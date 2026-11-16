"""Testes unitarios e de contrato do modulo outbox (Plano §2, T12, T13, S3)."""

from datetime import UTC, datetime

import httpx

from citizentech.erros import ErroArmazenamento
from citizentech.outbox.banco import (
    atualizar_status_pendencia,
    inicializar_banco,
    obter_mapa_estados,
    obter_pendencia,
    salvar_pendencia,
)
from citizentech.outbox.canonicalizacao import (
    comparar_payloads_identicos,
)
from citizentech.outbox.cliente import ClienteLambda
from citizentech.outbox.worker import (
    calcular_proxima_tentativa,
    processar_pendencias_uma_vez,
)


def test_canonicalizacao_campos_estaveis_e_reaproveitamento_medido_em():
    existente = {
        "evento_id": "evt-001",
        "dispositivo_id": "esp32-01",
        "metrica": "temperatura_c",
        "unidade": "C",
        "valor": 38.0,
        "sessao_laboratorio_id": "sessao-1",
        "ciclo_id": "ciclo-1",
        "tipo_dispositivo": "esp32",
        "medido_em": "2026-11-13T12:00:00Z",
        "criado_em": "2026-11-13T12:00:01Z",
    }

    # 1. Payload identico
    novo_identico = dict(existente)
    novo_identico["criado_em"] = "2026-11-13T12:05:00Z"  # Horario diferente de retry ignorado
    assert comparar_payloads_identicos(existente, novo_identico) is True

    # 2. medido_em omitido no retry reaproveita o existente
    novo_sem_medido = dict(existente)
    del novo_sem_medido["medido_em"]
    assert comparar_payloads_identicos(existente, novo_sem_medido) is True

    # 3. medido_em com fuso horario equivalente UTC
    novo_tz_equivalente = dict(existente)
    novo_tz_equivalente["medido_em"] = "2026-11-13T09:00:00-03:00"
    assert comparar_payloads_identicos(existente, novo_tz_equivalente) is True

    # 4. medido_em diferente -> nao identico
    novo_medido_divergente = dict(existente)
    novo_medido_divergente["medido_em"] = "2026-11-13T13:00:00Z"
    assert comparar_payloads_identicos(existente, novo_medido_divergente) is False

    # 5. valor diferente -> nao identico
    novo_valor_dif = dict(existente)
    novo_valor_dif["valor"] = 38.5
    assert comparar_payloads_identicos(existente, novo_valor_dif) is False

    # 6. metrica diferente -> nao identico
    novo_metrica_dif = dict(existente)
    novo_metrica_dif["metrica"] = "distancia_cm"
    assert comparar_payloads_identicos(existente, novo_metrica_dif) is False

    # 7. dispositivo_id diferente -> nao identico
    novo_disp_dif = dict(existente)
    novo_disp_dif["dispositivo_id"] = "esp32-99"
    assert comparar_payloads_identicos(existente, novo_disp_dif) is False


def test_banco_sqlite_crud_e_idempotencia(tmp_path):
    caminho_db = tmp_path / "outbox_teste.db"
    inicializar_banco(caminho_db)

    registro = {
        "evento_id": "evt-teste-1",
        "dispositivo_id": "esp32-01",
        "metrica": "temperatura_c",
        "unidade": "C",
        "valor": 25.0,
        "risco": "normal",
        "alerta": False,
        "estado": "pendente_nuvem",
        "medido_em": "2026-11-13T10:00:00Z",
        "criado_em": "2026-11-13T10:00:00Z",
    }

    # Salva pendencia
    salvar_pendencia(registro, caminho_db)
    pendencia = obter_pendencia("evt-teste-1", caminho_db)
    assert pendencia is not None
    assert pendencia["evento_id"] == "evt-teste-1"
    assert pendencia["estado"] == "pendente_nuvem"
    assert pendencia["tentativas"] == 0

    # Chamada idempotente de salvar_pendencia nao duplica nem sobrescreve
    salvar_pendencia(registro, caminho_db)
    mapa = obter_mapa_estados(caminho_db)
    assert len(mapa) == 1
    assert mapa["evt-teste-1"] == "pendente_nuvem"

    # Atualiza status para sincronizado
    atualizar_status_pendencia(
        evento_id="evt-teste-1",
        estado="sincronizado",
        tentativas=1,
        proxima_tentativa_em="2026-11-13T10:01:00Z",
        ultimo_erro=None,
        caminho=caminho_db,
    )
    atualizado = obter_pendencia("evt-teste-1", caminho_db)
    assert atualizado["estado"] == "sincronizado"
    assert atualizado["tentativas"] == 1


def test_banco_sqlite_falha_diretorio_lanca_erro_armazenamento(tmp_path):
    diretorio = tmp_path / "pasta_invalida"
    diretorio.mkdir()

    import pytest

    with pytest.raises(ErroArmazenamento):
        salvar_pendencia({"evento_id": "x"}, caminho=diretorio)


def test_cliente_lambda_validacao_estrita_envelope():
    registro = {
        "evento_id": "evt-env-1",
        "dispositivo_id": "esp32-01",
        "metrica": "temperatura_c",
        "unidade": "C",
        "valor": 30.0,
        "risco": "normal",
        "alerta": False,
        "medido_em": "2026-11-13T10:00:00Z",
    }

    # 1. 200 com HTML (nao e JSON) -> ENVELOPE_INVALIDO
    t_html = httpx.MockTransport(
        lambda req: httpx.Response(200, text="<html><body>OK</body></html>")
    )
    c_html = ClienteLambda(
        url="https://fake.example.test",
        chave_dispositivo="key",
        transport=t_html,
    )
    res_html = c_html.enviar_leitura(registro)
    assert res_html.sucesso is False
    assert res_html.codigo_erro == "ENVELOPE_INVALIDO"

    # 2. 200 com JSON sem evento_id coerente -> ENVELOPE_INVALIDO
    t_mismatched = httpx.MockTransport(
        lambda req: httpx.Response(200, json={"evento_id": "outro-id", "id": "123"})
    )
    c_mismatched = ClienteLambda(
        url="https://fake.example.test", chave_dispositivo="key", transport=t_mismatched
    )
    res_mismatched = c_mismatched.enviar_leitura(registro)
    assert res_mismatched.sucesso is False
    assert res_mismatched.codigo_erro == "ENVELOPE_INVALIDO"

    # 3. 200 com envelope valido -> Sucesso sincronizado
    t_ok = httpx.MockTransport(
        lambda req: httpx.Response(200, json={"evento_id": "evt-env-1", "id": "rec-1"})
    )
    c_ok = ClienteLambda(
        url="https://fake.example.test",
        chave_dispositivo="key",
        transport=t_ok,
    )
    res_ok = c_ok.enviar_leitura(registro)
    assert res_ok.sucesso is True
    assert res_ok.estado_final == "sincronizado"


def test_cliente_lambda_tratamento_respostas_de_erro():
    registro = {
        "evento_id": "evt-err-1",
        "dispositivo_id": "esp32-01",
        "metrica": "temperatura_c",
        "unidade": "C",
        "valor": 30.0,
        "risco": "normal",
        "alerta": False,
        "medido_em": "2026-11-13T10:00:00Z",
    }

    casos = [
        (409, {"erro": "Conflito"}, "conflito", "CONFLITO_409"),
        (400, {"erro": "Bad Request"}, "erro_permanente", "ERRO_CLIENTE_4XX"),
        (401, {"erro": "Unauthorized"}, "erro_permanente", "ERRO_CLIENTE_4XX"),
        (403, {"erro": "Forbidden"}, "erro_permanente", "ERRO_CLIENTE_4XX"),
        (413, {"erro": "Payload Too Large"}, "erro_permanente", "ERRO_CLIENTE_4XX"),
        (422, {"erro": "Unprocessable"}, "erro_permanente", "ERRO_CLIENTE_4XX"),
        # URL mal configurada pode ser corrigida: continua na fila
        (404, {"erro": "Not Found"}, "pendente_nuvem", "ERRO_REMOTO_INDEFINIDO"),
        (429, {"erro": "Too Many Requests"}, "pendente_nuvem", "RATE_LIMIT_429"),
        (500, {"erro": "Internal Error"}, "pendente_nuvem", "ERRO_SERVIDOR_5XX"),
        (503, {"erro": "Service Unavailable"}, "pendente_nuvem", "ERRO_SERVIDOR_5XX"),
    ]

    for status_code, corpo, estado_esp, cod_erro_esp in casos:
        transport = httpx.MockTransport(
            lambda req, sc=status_code, b=corpo: httpx.Response(sc, json=b)
        )
        cliente = ClienteLambda(
            url="https://fake.example.test",
            chave_dispositivo="key",
            transport=transport,
        )
        res = cliente.enviar_leitura(registro)
        assert res.sucesso is False
        assert res.estado_final == estado_esp
        assert res.codigo_erro == cod_erro_esp


def test_cliente_lambda_timeout_e_conexao_recusada():
    registro = {
        "evento_id": "evt-timeout-1",
        "dispositivo_id": "esp32-01",
        "metrica": "temperatura_c",
        "unidade": "C",
        "valor": 30.0,
        "risco": "normal",
        "alerta": False,
        "medido_em": "2026-11-13T10:00:00Z",
    }

    def handler_timeout(req):
        raise httpx.TimeoutException("Timeout simulado")

    c_timeout = ClienteLambda(
        url="https://fake.example.test",
        chave_dispositivo="key",
        transport=httpx.MockTransport(handler_timeout),
    )
    res_to = c_timeout.enviar_leitura(registro)
    assert res_to.codigo_erro == "TIMEOUT"
    assert res_to.estado_final == "pendente_nuvem"

    def handler_conn(req):
        raise httpx.ConnectError("Conexao recusada")

    c_conn = ClienteLambda(
        url="https://fake.example.test",
        chave_dispositivo="key",
        transport=httpx.MockTransport(handler_conn),
    )
    res_conn = c_conn.enviar_leitura(registro)
    assert res_conn.codigo_erro == "CONEXAO_RECUSADA"
    assert res_conn.estado_final == "pendente_nuvem"


def test_cliente_lambda_seguranca_header_e_minimizacao():
    requisicao_capturada: list[httpx.Request] = []

    def handler(req: httpx.Request) -> httpx.Response:
        requisicao_capturada.append(req)
        return httpx.Response(201, json={"evento_id": "evt-sec-1", "id": "rec-1"})

    cliente = ClienteLambda(
        url="https://fake.example.test/nuvem",
        chave_dispositivo="chave-secreta-xyz",
        transport=httpx.MockTransport(handler),
    )

    registro_com_relato = {
        "evento_id": "evt-sec-1",
        "dispositivo_id": "esp32-01",
        "metrica": "temperatura_c",
        "unidade": "C",
        "valor": 25.0,
        "risco": "normal",
        "alerta": False,
        "medido_em": "2026-11-13T10:00:00Z",
        "relato": "Dado sensivel do usuario que NAO deve ir a nuvem",
        "pii": "email@example.com",
    }

    res = cliente.enviar_leitura(registro_com_relato)
    assert res.sucesso is True

    assert len(requisicao_capturada) == 1
    req = requisicao_capturada[0]

    # Verifica headers de seguranca
    assert req.headers.get("X-Device-Key") == "chave-secreta-xyz"
    assert "Authorization" not in req.headers

    # Minimizacao: nao contem relato nem pii
    import json
    corpo = json.loads(req.content.decode("utf-8"))
    assert "relato" not in corpo
    assert "pii" not in corpo
    assert "chave-secreta-xyz" not in req.content.decode("utf-8")


def test_cliente_lambda_omite_identificadores_opcionais_vazios():
    """A Lambda recusa sessao_laboratorio_id/ciclo_id vazios (1–64 caracteres): não enviar ""."""
    import json

    corpos: list[dict] = []

    def handler(req: httpx.Request) -> httpx.Response:
        corpos.append(json.loads(req.content.decode("utf-8")))
        return httpx.Response(201, json={"evento_id": "evt-vazio-1", "id": 1})

    cliente = ClienteLambda(
        url="https://fake.example.test/nuvem",
        chave_dispositivo="chave-demo",
        transport=httpx.MockTransport(handler),
    )
    registro = {
        "evento_id": "evt-vazio-1",
        "dispositivo_id": "esp32-01",
        "sessao_laboratorio_id": "",
        "ciclo_id": "",
        "metrica": "temperatura_c",
        "unidade": "C",
        "valor": 25.0,
        "risco": "normal",
        "alerta": False,
        "medido_em": "2026-11-13T10:00:00Z",
    }
    assert cliente.enviar_leitura(registro).sucesso is True
    assert "sessao_laboratorio_id" not in corpos[0]
    assert "ciclo_id" not in corpos[0]

    registro_com_sessao = dict(registro, evento_id="evt-vazio-2", sessao_laboratorio_id="LAB-1")
    cliente.enviar_leitura(registro_com_sessao)
    assert corpos[1]["sessao_laboratorio_id"] == "LAB-1"


def test_backoff_exponencial_limitado():
    agora = datetime(2026, 11, 13, 12, 0, 0, tzinfo=UTC)

    # tentativas=1 -> 1s
    p1 = calcular_proxima_tentativa(agora, tentativas=1, base_segundos=1.0, max_segundos=60.0)
    assert p1 == "2026-11-13T12:00:01Z"

    # tentativas=2 -> 2s
    p2 = calcular_proxima_tentativa(agora, tentativas=2, base_segundos=1.0, max_segundos=60.0)
    assert p2 == "2026-11-13T12:00:02Z"

    # tentativas=3 -> 4s
    p3 = calcular_proxima_tentativa(agora, tentativas=3, base_segundos=1.0, max_segundos=60.0)
    assert p3 == "2026-11-13T12:00:04Z"

    # tentativas=7 -> 64s limitado a 60s
    p7 = calcular_proxima_tentativa(agora, tentativas=7, base_segundos=1.0, max_segundos=60.0)
    assert p7 == "2026-11-13T12:01:00Z"


def test_worker_fila_vazia_retorna_zero_sem_queimar_cpu(tmp_path):
    caminho_db = tmp_path / "outbox_vazia.db"
    inicializar_banco(caminho_db)

    processados = processar_pendencias_uma_vez(caminho_db=caminho_db)
    assert processados == 0


def test_operational_error_com_caminho_nao_vaza_na_resposta_503(monkeypatch, tmp_path):
    import sqlite3

    from fastapi.testclient import TestClient

    from citizentech.leituras import repositorio
    from citizentech.main import app

    csv = tmp_path / "rt" / "leituras.csv"
    db = tmp_path / "rt" / "outbox.db"
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(csv))
    monkeypatch.setenv("CITIZENTECH_OUTBOX_DB", str(db))
    monkeypatch.setenv("DEVICE_KEY", "chave-teste-sec")

    caminho_secreto = "C:\\pasta_secreta\\dados_confidenciais\\outbox.db"

    def erro_com_caminho(*args, **kwargs):
        raise sqlite3.OperationalError(f"unable to open database file at {caminho_secreto}")

    monkeypatch.setattr(repositorio, "salvar_pendencia", erro_com_caminho)

    cliente = TestClient(app, raise_server_exceptions=False)
    resp = cliente.post(
        "/leituras",
        json={
            "evento_id": "evt-leak-test",
            "dispositivo_id": "esp32-01",
            "metrica": "temperatura_c",
            "valor": 25.0,
        },
        headers={"X-Device-Key": "chave-teste-sec"},
    )
    assert resp.status_code == 503
    corpo = resp.text
    assert "pasta_secreta" not in corpo
    assert "dados_confidenciais" not in corpo
    assert "unable to open" not in corpo
    assert "OperationalError" in corpo


def test_reconciliacao_startup_falha_loga_warning_com_caplog(monkeypatch, caplog):
    import logging

    from fastapi.testclient import TestClient

    from citizentech import main

    def falha_reconciliacao():
        raise RuntimeError("falha simulada na reconciliacao")

    monkeypatch.setattr(main, "reconciliar_com_csv", falha_reconciliacao)

    with caplog.at_level(logging.WARNING, logger="citizentech.main"):
        with TestClient(main.app):
            pass

    avisos = [
        r
        for r in caplog.records
        if r.levelname == "WARNING" and "Falha na reconciliacao de startup" in r.message
    ]
    assert len(avisos) == 1
    assert "RuntimeError" in avisos[0].message
    assert "falha simulada" not in avisos[0].message
