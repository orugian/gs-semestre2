"""Aceite independente S3 (orquestrador): CSV e SQLite reais em tmp_path, fake so na Lambda."""
import json
import sqlite3
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from fastapi.testclient import TestClient

from citizentech.leituras import repositorio
from citizentech.main import app
from citizentech.outbox.banco import obter_pendencia
from citizentech.outbox.cliente import ClienteLambda
from citizentech.outbox.worker import processar_pendencias_uma_vez

K = {"X-Device-Key": "fixture-local"}
BASE = {
    "evento_id": "evt-aceite-1",
    "dispositivo_id": "esp32-a",
    "metrica": "temperatura_c",
    "valor": 38.0,
}
CABECALHO = (
    "evento_id,dispositivo_id,sessao_laboratorio_id,ciclo_id,tipo_dispositivo,"
    "metrica,unidade,valor,risco,alerta,estado,medido_em,criado_em\n"
)


@pytest.fixture
def ctx(monkeypatch, tmp_path):
    csv = tmp_path / "rt" / "leituras.csv"
    db = tmp_path / "rt" / "outbox.db"
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(csv))
    monkeypatch.setenv("CITIZENTECH_OUTBOX_DB", str(db))
    monkeypatch.setenv("DEVICE_KEY", "fixture-local")
    monkeypatch.setenv("CITIZENTECH_RATE_LIMIT_POR_MINUTO", "500")
    return TestClient(app, raise_server_exceptions=False), csv, db


def _lambda(handler):
    return ClienteLambda(
        url="https://lambda.example.test/ocorrencias",
        chave_dispositivo="fixture-local",
        transport=httpx.MockTransport(handler),
    )


def _aceita(request: httpx.Request) -> httpx.Response:
    corpo = json.loads(request.content)
    return httpx.Response(201, json={"evento_id": corpo["evento_id"], "id": "n-1"})


def test_reenvio_sem_medido_em_apos_o_relogio_avancar_e_identico(ctx, monkeypatch):
    cliente, _, _ = ctx

    class Relogio(datetime):
        agora = datetime(2026, 11, 13, 12, 0, 0, tzinfo=UTC)

        @classmethod
        def now(cls, tz=None):
            return cls.agora

    monkeypatch.setattr("citizentech.leituras.esquemas.datetime", Relogio)
    r1 = cliente.post("/leituras", json=BASE, headers=K)
    assert r1.status_code == 201
    Relogio.agora += timedelta(seconds=5)
    r2 = cliente.post("/leituras", json=BASE, headers=K)
    assert r2.status_code == 200
    assert r2.json()["medido_em"] == r1.json()["medido_em"]


def test_medido_em_equivalente_em_outro_fuso_e_identico(ctx):
    cliente, _, _ = ctx
    r1 = cliente.post("/leituras", json=BASE | {"medido_em": "2026-11-13T12:00:00Z"}, headers=K)
    r2 = cliente.post(
        "/leituras", json=BASE | {"medido_em": "2026-11-13T09:00:00-03:00"}, headers=K
    )
    assert (r1.status_code, r2.status_code) == (201, 200)


def test_falha_do_sqlite_apos_append_desfaz_csv_e_preserva_anteriores(ctx, monkeypatch):
    cliente, csv, _ = ctx
    assert cliente.post("/leituras", json=BASE, headers=K).status_code == 201
    antes = csv.read_bytes()
    original = repositorio.salvar_pendencia
    falhar = {"ligado": True}

    def instavel(registro, caminho=None):
        if falhar["ligado"]:
            raise sqlite3.OperationalError("disk I/O error em C:\\interno\\outbox.db")
        return original(registro, caminho)

    monkeypatch.setattr(repositorio, "salvar_pendencia", instavel)
    novo = BASE | {"evento_id": "evt-aceite-2"}
    r = cliente.post("/leituras", json=novo, headers=K)
    assert r.status_code == 503
    assert "interno" not in r.text and "outbox.db" not in r.text
    assert csv.read_bytes() == antes
    assert cliente.get("/leituras", headers=K).json()["total"] == 1
    falhar["ligado"] = False
    assert cliente.post("/leituras", json=novo, headers=K).status_code == 201


def test_outbox_corrompida_responde_503_sem_tocar_no_csv(ctx):
    cliente, csv, db = ctx
    assert cliente.post("/leituras", json=BASE, headers=K).status_code == 201
    antes = csv.read_bytes()
    for sufixo in ("", "-wal", "-shm"):
        alvo = db.with_name(db.name + sufixo)
        if alvo.exists():
            alvo.unlink()
    db.write_bytes(b"isto nao e um banco sqlite" * 50)
    r = cliente.post("/leituras", json=BASE | {"evento_id": "evt-aceite-3"}, headers=K)
    assert r.status_code == 503
    assert str(db.parent) not in r.text
    assert csv.read_bytes() == antes


def test_relato_nao_e_persistido_nem_enviado_a_nuvem(ctx):
    cliente, csv, db = ctx
    recebidos = []

    def handler(request):
        recebidos.append(request.content)
        return _aceita(request)

    r = cliente.post("/leituras", json=BASE | {"relato": "texto-pessoal-zq"}, headers=K)
    assert r.status_code == 201
    processar_pendencias_uma_vez(cliente=_lambda(handler))
    assert len(recebidos) == 1 and b"relato" not in recebidos[0]
    for arquivo in csv.parent.iterdir():
        assert b"texto-pessoal-zq" not in arquivo.read_bytes(), arquivo.name


def test_ack_com_evento_de_outro_registro_nao_sincroniza(ctx):
    cliente, _, db = ctx
    cliente.post("/leituras", json=BASE, headers=K)
    processar_pendencias_uma_vez(
        cliente=_lambda(lambda req: httpx.Response(200, json={"evento_id": "outro", "id": "x"}))
    )
    assert obter_pendencia("evt-aceite-1", db)["estado"] == "pendente_nuvem"


def test_redirecionamento_nao_e_seguido_nem_vira_sucesso(ctx):
    cliente, _, db = ctx
    cliente.post("/leituras", json=BASE, headers=K)
    hosts = []

    def handler(request):
        hosts.append(request.url.host)
        return httpx.Response(307, headers={"Location": "https://externo.example.test/x"})

    processar_pendencias_uma_vez(cliente=_lambda(handler))
    assert hosts == ["lambda.example.test"]
    assert obter_pendencia("evt-aceite-1", db)["estado"] == "pendente_nuvem"


def test_backoff_respeita_agendamento_e_tem_teto(ctx):
    cliente, _, db = ctx
    cliente.post("/leituras", json=BASE, headers=K)
    chamadas = []
    agora = datetime(2030, 1, 1, tzinfo=UTC)

    def handler(request):
        chamadas.append(1)
        return httpx.Response(503)

    def relogio() -> datetime:
        return agora

    lam = _lambda(handler)
    processar_pendencias_uma_vez(cliente=lam, relogio=relogio)
    processar_pendencias_uma_vez(cliente=lam, relogio=relogio)
    assert len(chamadas) == 1
    for _ in range(12):
        agora += timedelta(seconds=61)
        processar_pendencias_uma_vez(cliente=lam, relogio=relogio)
    assert len(chamadas) == 13
    proxima = datetime.fromisoformat(
        obter_pendencia("evt-aceite-1", db)["proxima_tentativa_em"].replace("Z", "+00:00")
    )
    assert timedelta(0) < proxima - agora <= timedelta(seconds=60)


def test_reenvio_apos_sincronizar_devolve_estado_atual_sem_reenviar(ctx):
    cliente, _, db = ctx
    cliente.post("/leituras", json=BASE, headers=K)
    chamadas = []

    def handler(request):
        chamadas.append(1)
        return _aceita(request)

    lam = _lambda(handler)
    processar_pendencias_uma_vez(cliente=lam)
    r = cliente.post("/leituras", json=BASE, headers=K)
    assert r.status_code == 200 and r.json()["estado"] == "sincronizado"
    processar_pendencias_uma_vez(cliente=lam)
    assert len(chamadas) == 1


def test_reenvio_de_orfao_do_csv_entra_na_fila(ctx):
    cliente, csv, db = ctx
    csv.parent.mkdir(parents=True, exist_ok=True)
    csv.write_text(
        CABECALHO
        + "evt-aceite-1,esp32-a,,,esp32,temperatura_c,C,38.0,atencao,True,"
        "pendente_nuvem,2026-11-13T12:00:00Z,2026-11-13T12:00:00Z\n",
        encoding="utf-8",
    )
    r = cliente.post("/leituras", json=BASE | {"medido_em": "2026-11-13T12:00:00Z"}, headers=K)
    assert r.status_code == 200
    assert cliente.post("/leituras", json=BASE | {"valor": 40.0}, headers=K).status_code == 409
    assert obter_pendencia("evt-aceite-1", db) is not None


def test_url_http_externa_nao_recebe_a_chave(ctx):
    cliente, _, db = ctx
    cliente.post("/leituras", json=BASE, headers=K)
    vistos = []

    def handler(request):
        vistos.append(request.headers.get("X-Device-Key"))
        return _aceita(request)

    inseguro = ClienteLambda(
        url="http://externo.example.test/ocorrencias",
        chave_dispositivo="fixture-local",
        transport=httpx.MockTransport(handler),
    )
    processar_pendencias_uma_vez(cliente=inseguro)
    assert vistos == []
    assert obter_pendencia("evt-aceite-1", db)["estado"] != "sincronizado"
