"""Testes de integracao e contrato das rotas de laboratorio (S14)."""

import json
import logging
import re
import uuid
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from fastapi.testclient import TestClient

from citizentech.banco.conexao import obter_conexao
from citizentech.main import app
from citizentech.outbox.banco import obter_pendencia
from citizentech.outbox.cliente import ClienteLambda


def _criar_usuario_e_sessao(cliente: TestClient, sufixo: str) -> dict:
    email = f"lab_{sufixo}_{uuid.uuid4().hex[:6]}@example.test"
    senha = "SenhaForte123!@"
    resp_reg = cliente.post("/auth/registrar", json={"email": email, "senha": senha})
    assert resp_reg.status_code == 201
    dados_reg = resp_reg.json()

    resp_login = cliente.post("/auth/login", json={"email": email, "senha": senha})
    assert resp_login.status_code == 200
    csrf_token = cliente.cookies.get("csrf_token")
    assert csrf_token is not None

    return {
        "id": dados_reg["id"],
        "email": email,
        "csrf_token": csrf_token,
    }


def _conceder_consentimento(
    cliente: TestClient,
    csrf_token: str,
    finalidade: str = "laboratorio_nuvem",
) -> None:
    resp = cliente.post(
        "/me/consentimentos",
        json={"finalidade": finalidade},
        headers={"X-CSRF-Token": csrf_token},
    )
    assert resp.status_code == 201


@pytest.mark.oracle
@pytest.mark.mongo
def test_leituras_da_sessao_e_relato_redigido_seguem_para_a_outbox(monkeypatch, tmp_path):
    caminho_csv = tmp_path / "runtime" / "leituras.csv"
    caminho_db = tmp_path / "runtime" / "outbox.db"
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(caminho_csv))
    monkeypatch.setenv("CITIZENTECH_OUTBOX_DB", str(caminho_db))
    monkeypatch.setenv("DEVICE_KEY", "chave-lab-teste")

    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "s14_full")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}

    # Concede consentimento laboratorio_nuvem
    _conceder_consentimento(cliente, usuario["csrf_token"], "laboratorio_nuvem")

    # 1. Abre sessao de laboratorio -> 201 com codigo no formato
    resp_sessao = cliente.post("/me/laboratorio/sessoes", headers=headers_csrf)
    assert resp_sessao.status_code == 201
    dados_sessao = resp_sessao.json()
    sessao_id = dados_sessao["id"]
    codigo = dados_sessao["codigo"]
    assert re.match(r"^LAB-[ABCDEFGHJKMNPQRSTUVWXYZ23456789]{6}$", codigo)
    assert dados_sessao["status"] == "ativa"
    assert "instrucoes" in dados_sessao

    # 2. Registra relato -> 200, texto_redigido sem o e-mail
    texto_relato = "Sensor aqueceu rápido; me chame em ana.teste@exemplo.test"
    resp_relato = cliente.post(
        f"/me/laboratorio/sessoes/{sessao_id}/relato",
        json={"relato": texto_relato},
        headers=headers_csrf,
    )
    assert resp_relato.status_code == 200
    dados_relato = resp_relato.json()
    assert dados_relato["status"] == "pendente"
    texto_redigido = dados_relato["texto_redigido"]
    assert "ana.teste@exemplo.test" not in texto_redigido
    assert "[EMAIL]" in texto_redigido

    # 3. Envia 2 leituras por POST /leituras com sessao_laboratorio_id = codigo e 1 com outro codigo
    headers_device = {"X-Device-Key": "chave-lab-teste"}
    p1 = {
        "evento_id": "evt-s14-1",
        "dispositivo_id": "esp32-01",
        "sessao_laboratorio_id": codigo,
        "metrica": "temperatura_c",
        "valor": 38.0,
    }
    p2 = {
        "evento_id": "evt-s14-2",
        "dispositivo_id": "esp32-01",
        "sessao_laboratorio_id": codigo,
        "metrica": "distancia_cm",
        "valor": 20.0,
    }
    p3 = {
        "evento_id": "evt-s14-3",
        "dispositivo_id": "esp32-02",
        "sessao_laboratorio_id": "LAB-OUTRO9",
        "metrica": "temperatura_c",
        "valor": 25.0,
    }

    r1 = cliente.post("/leituras", json=p1, headers=headers_device)
    assert r1.status_code == 201

    r2 = cliente.post("/leituras", json=p2, headers=headers_device)
    assert r2.status_code == 201

    r3 = cliente.post("/leituras", json=p3, headers=headers_device)
    assert r3.status_code == 201

    # 4. GET /me/laboratorio/sessoes/{id} -> exatamente as 2 leituras da sessao,
    # indicadores corretos, relato 'enviado'
    resp_get = cliente.get(f"/me/laboratorio/sessoes/{sessao_id}")
    assert resp_get.status_code == 200
    dados_get = resp_get.json()
    assert dados_get["id"] == sessao_id
    assert dados_get["codigo"] == codigo
    assert dados_get["relato"]["status"] == "enviado"
    assert dados_get["relato"]["texto_redigido"] == texto_redigido

    leituras_sessao = dados_get["leituras"]
    assert len(leituras_sessao) == 2
    eventos_retornados = [item["evento_id"] for item in leituras_sessao]
    assert eventos_retornados == ["evt-s14-1", "evt-s14-2"]

    indicadores = dados_get["indicadores"]
    assert "temperatura_c" in indicadores
    assert indicadores["temperatura_c"]["contagem"] == 1
    assert indicadores["temperatura_c"]["media"] == 38.0
    assert "distancia_cm" in indicadores
    assert indicadores["distancia_cm"]["contagem"] == 1
    assert indicadores["distancia_cm"]["media"] == 20.0

    # 5. A pendencia da primeira leitura da sessao na outbox tem relato_redigido
    # igual ao texto redigido e a segunda nao tem
    pend1 = obter_pendencia("evt-s14-1", caminho_db)
    assert pend1 is not None
    assert pend1["payload"].get("relato_redigido") == texto_redigido

    pend2 = obter_pendencia("evt-s14-2", caminho_db)
    assert pend2 is not None
    relato_p2 = pend2["payload"].get("relato_redigido")
    assert "relato_redigido" not in pend2["payload"] or relato_p2 is None

    # 6. Com ClienteLambda + MockTransport, o corpo enviado da primeira leitura
    # tem relato redigido e nao contem o e-mail
    corpos_nuvem: list[dict] = []

    def handler_lambda(req: httpx.Request) -> httpx.Response:
        corpos_nuvem.append(json.loads(req.content.decode("utf-8")))
        return httpx.Response(201, json={"evento_id": "evt-s14-1", "id": "nuvem-1"})

    cliente_lambda = ClienteLambda(
        url="https://fake.example.test/telemetria",
        chave_dispositivo="chave-lab-teste",
        transport=httpx.MockTransport(handler_lambda),
    )
    res_envio = cliente_lambda.enviar_leitura(pend1["payload"])
    assert res_envio.sucesso is True
    assert len(corpos_nuvem) == 1
    corpo_1 = corpos_nuvem[0]
    assert corpo_1.get("relato") == texto_redigido
    assert "ana.teste@exemplo.test" not in json.dumps(corpo_1)


@pytest.mark.oracle
def test_sem_consentimento_laboratorio_nuvem_retorna_403(monkeypatch, tmp_path):
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "sem_consent")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}

    # Sem o consentimento laboratorio_nuvem -> 403 ao abrir sessao
    resp = cliente.post("/me/laboratorio/sessoes", headers=headers_csrf)
    assert resp.status_code == 403
    corpo = resp.json()
    assert "erro" in corpo
    assert "detalhes" in corpo

    # Tentativa de registrar relato em sessao ficticia sem consentimento -> 403
    resp_rel = cliente.post(
        "/me/laboratorio/sessoes/fake-id/relato",
        json={"relato": "Tentativa sem consentimento"},
        headers=headers_csrf,
    )
    assert resp_rel.status_code == 403


@pytest.mark.oracle
def test_abrir_segunda_sessao_encerra_primeira(monkeypatch, tmp_path):
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "troca_sessao")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}
    _conceder_consentimento(cliente, usuario["csrf_token"], "laboratorio_nuvem")

    # 1. Abre primeira sessao
    r1 = cliente.post("/me/laboratorio/sessoes", headers=headers_csrf)
    assert r1.status_code == 201
    s1_id = r1.json()["id"]

    # 2. Abre segunda sessao
    r2 = cliente.post("/me/laboratorio/sessoes", headers=headers_csrf)
    assert r2.status_code == 201
    s2_id = r2.json()["id"]
    assert s1_id != s2_id

    # 3. GET .../atual devolve a 2a sessao
    r_atual = cliente.get("/me/laboratorio/sessoes/atual")
    assert r_atual.status_code == 200
    assert r_atual.json()["id"] == s2_id
    assert r_atual.json()["status"] == "ativa"

    # 4. Primeira sessao esta encerrada
    r_s1 = cliente.get(f"/me/laboratorio/sessoes/{s1_id}")
    assert r_s1.status_code == 200
    assert r_s1.json()["status"] == "encerrada"

    # 5. Relato na 1a sessao -> 409 Conflito (sessao encerrada)
    r_rel = cliente.post(
        f"/me/laboratorio/sessoes/{s1_id}/relato",
        json={"relato": "Tentando relatar em sessao encerrada"},
        headers=headers_csrf,
    )
    assert r_rel.status_code == 409


@pytest.mark.oracle
def test_validacao_relato_tamanho_e_status_e_acesso_proprietario(monkeypatch, tmp_path):
    caminho_csv = tmp_path / "runtime" / "leituras.csv"
    caminho_db = tmp_path / "runtime" / "outbox.db"
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(caminho_csv))
    monkeypatch.setenv("CITIZENTECH_OUTBOX_DB", str(caminho_db))
    monkeypatch.setenv("DEVICE_KEY", "chave-lab-teste")

    cliente1 = TestClient(app, base_url="https://testserver")
    user1 = _criar_usuario_e_sessao(cliente1, "dono")
    csrf1 = {"X-CSRF-Token": user1["csrf_token"]}
    _conceder_consentimento(cliente1, user1["csrf_token"], "laboratorio_nuvem")

    r_sessao = cliente1.post("/me/laboratorio/sessoes", headers=csrf1)
    assert r_sessao.status_code == 201
    s_id = r_sessao.json()["id"]
    cod = r_sessao.json()["codigo"]

    # 1. Relato com 0 caracteres apos strip -> 400
    r_0 = cliente1.post(
        f"/me/laboratorio/sessoes/{s_id}/relato",
        json={"relato": "   "},
        headers=csrf1,
    )
    assert r_0.status_code == 400

    # 2. Relato com 281 caracteres -> 400
    r_281 = cliente1.post(
        f"/me/laboratorio/sessoes/{s_id}/relato",
        json={"relato": "A" * 281},
        headers=csrf1,
    )
    assert r_281.status_code == 400

    # 3. Outro usuario -> 404 no GET e no relato (T14)
    cliente2 = TestClient(app, base_url="https://testserver")
    user2 = _criar_usuario_e_sessao(cliente2, "intruso")
    csrf2 = {"X-CSRF-Token": user2["csrf_token"]}
    _conceder_consentimento(cliente2, user2["csrf_token"], "laboratorio_nuvem")

    r_get_outro = cliente2.get(f"/me/laboratorio/sessoes/{s_id}")
    assert r_get_outro.status_code == 404

    r_rel_outro = cliente2.post(
        f"/me/laboratorio/sessoes/{s_id}/relato",
        json={"relato": "Relato de outro usuario"},
        headers=csrf2,
    )
    assert r_rel_outro.status_code == 404

    # 4. Substituicao de relato pendente (o ultimo vale)
    t1 = "Aquecimento inicial observado na bancada: temperatura normal."
    r_p1 = cliente1.post(
        f"/me/laboratorio/sessoes/{s_id}/relato",
        json={"relato": t1},
        headers=csrf1,
    )
    assert r_p1.status_code == 200
    assert r_p1.json()["texto_redigido"] == t1

    t2 = "Aquecimento observado na bancada: temperatura aumentou 5 graus."
    r_p2 = cliente1.post(
        f"/me/laboratorio/sessoes/{s_id}/relato",
        json={"relato": t2},
        headers=csrf1,
    )
    assert r_p2.status_code == 200
    assert r_p2.json()["texto_redigido"] == t2

    # Envia leitura para marcar o relato como enviado
    r_leitura = cliente1.post(
        "/leituras",
        json={
            "evento_id": "evt-env-10",
            "dispositivo_id": "esp32-01",
            "sessao_laboratorio_id": cod,
            "metrica": "temperatura_c",
            "valor": 26.0,
        },
        headers={"X-Device-Key": "chave-lab-teste"},
    )
    assert r_leitura.status_code == 201

    # 5. Relato depois de enviado -> 409
    r_apos_envio = cliente1.post(
        f"/me/laboratorio/sessoes/{s_id}/relato",
        json={"relato": "Tentativa de enviar outro relato"},
        headers=csrf1,
    )
    assert r_apos_envio.status_code == 409


@pytest.mark.oracle
def test_leitura_com_codigo_expirado_aceita_sem_relato(monkeypatch, tmp_path):
    caminho_csv = tmp_path / "runtime" / "leituras.csv"
    caminho_db = tmp_path / "runtime" / "outbox.db"
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(caminho_csv))
    monkeypatch.setenv("CITIZENTECH_OUTBOX_DB", str(caminho_db))
    monkeypatch.setenv("DEVICE_KEY", "chave-lab-teste")

    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "expirada")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}
    _conceder_consentimento(cliente, usuario["csrf_token"], "laboratorio_nuvem")

    resp_s = cliente.post("/me/laboratorio/sessoes", headers=headers_csrf)
    assert resp_s.status_code == 201
    s_id = resp_s.json()["id"]
    cod = resp_s.json()["codigo"]

    # Registra relato
    r_rel = cliente.post(
        f"/me/laboratorio/sessoes/{s_id}/relato",
        json={"relato": "Relato de sessao que vai expirar"},
        headers=headers_csrf,
    )
    assert r_rel.status_code == 200

    # Manipula expira_em no banco de teste para o passado
    import oracledb
    with obter_conexao() as conn:
        with conn.cursor() as cur:
            cur.setinputsizes(passado=oracledb.DB_TYPE_TIMESTAMP_TZ)
            cur.execute(
                "UPDATE sessao_laboratorio SET expira_em = :passado WHERE id = :id",
                {"passado": datetime.now(UTC) - timedelta(hours=1), "id": s_id},
            )

    # 1. GET /me/laboratorio/sessoes/atual -> 404 (expirada nao e ativa)
    r_atual = cliente.get("/me/laboratorio/sessoes/atual")
    assert r_atual.status_code == 404

    # 2. GET /me/laboratorio/sessoes/{id} -> status 'expirada'
    r_get = cliente.get(f"/me/laboratorio/sessoes/{s_id}")
    assert r_get.status_code == 200
    assert r_get.json()["status"] == "expirada"

    # 3. Leitura com codigo de sessao expirada -> aceita pelo POST /leituras (201),
    # sem relato anexado
    r_post = cliente.post(
        "/leituras",
        json={
            "evento_id": "evt-exp-01",
            "dispositivo_id": "esp32-01",
            "sessao_laboratorio_id": cod,
            "metrica": "temperatura_c",
            "valor": 30.0,
        },
        headers={"X-Device-Key": "chave-lab-teste"},
    )
    assert r_post.status_code == 201

    pend = obter_pendencia("evt-exp-01", caminho_db)
    assert pend is not None
    relato_exp = pend["payload"].get("relato_redigido")
    assert "relato_redigido" not in pend["payload"] or relato_exp is None

    # O relato continua pendente no banco (nao foi enviado)
    r_get_depois = cliente.get(f"/me/laboratorio/sessoes/{s_id}")
    assert r_get_depois.json()["relato"]["status"] == "pendente"


def test_modo_isolado_sem_oracle_aceita_leitura_com_sessao(monkeypatch, tmp_path):
    from citizentech.leituras.isolado import app as app_isolado

    caminho_csv = tmp_path / "runtime" / "leituras_iso.csv"
    caminho_db = tmp_path / "runtime" / "outbox_iso.db"
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(caminho_csv))
    monkeypatch.setenv("CITIZENTECH_OUTBOX_DB", str(caminho_db))
    monkeypatch.setenv("DEVICE_KEY", "chave-isolado")

    # Remove Oracle do ambiente
    monkeypatch.delenv("ORACLE_DSN", raising=False)
    monkeypatch.delenv("ORACLE_USER", raising=False)
    monkeypatch.delenv("ORACLE_PASSWORD", raising=False)

    cliente_isolado = TestClient(app_isolado)
    resp = cliente_isolado.post(
        "/leituras",
        json={
            "evento_id": "evt-iso-1",
            "dispositivo_id": "esp32-iso",
            "sessao_laboratorio_id": "LAB-ISOL99",
            "metrica": "temperatura_c",
            "valor": 22.5,
        },
        headers={"X-Device-Key": "chave-isolado"},
    )
    assert resp.status_code == 201
    dados = resp.json()
    assert dados["evento_id"] == "evt-iso-1"


@pytest.mark.oracle
def test_codigo_unicidade_e_formato(monkeypatch, tmp_path):
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "100_sessoes")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}
    _conceder_consentimento(cliente, usuario["csrf_token"], "laboratorio_nuvem")

    codigos = set()
    padrao = re.compile(r"^LAB-[ABCDEFGHJKMNPQRSTUVWXYZ23456789]{6}$")

    for _ in range(100):
        resp = cliente.post("/me/laboratorio/sessoes", headers=headers_csrf)
        assert resp.status_code == 201
        codigo = resp.json()["codigo"]
        assert padrao.match(codigo)
        assert codigo not in codigos
        codigos.add(codigo)

    assert len(codigos) == 100


@pytest.mark.oracle
def test_nenhuma_linha_de_log_contem_o_relato(caplog, monkeypatch, tmp_path):
    caminho_csv = tmp_path / "runtime" / "leituras.csv"
    caminho_db = tmp_path / "runtime" / "outbox.db"
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(caminho_csv))
    monkeypatch.setenv("CITIZENTECH_OUTBOX_DB", str(caminho_db))
    monkeypatch.setenv("DEVICE_KEY", "chave-lab-teste")

    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "log_sec")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}
    _conceder_consentimento(cliente, usuario["csrf_token"], "laboratorio_nuvem")

    marcador_relato = "MARCADOR-DE-RELATO-PARA-LOG-987"

    with caplog.at_level(logging.DEBUG):
        resp_s = cliente.post("/me/laboratorio/sessoes", headers=headers_csrf)
        s_id = resp_s.json()["id"]
        cod = resp_s.json()["codigo"]

        cliente.post(
            f"/me/laboratorio/sessoes/{s_id}/relato",
            json={"relato": f"Temperatura subiu e {marcador_relato}"},
            headers=headers_csrf,
        )

        cliente.post(
            "/leituras",
            json={
                "evento_id": "evt-log-sec-1",
                "dispositivo_id": "esp32-01",
                "sessao_laboratorio_id": cod,
                "metrica": "temperatura_c",
                "valor": 28.0,
            },
            headers={"X-Device-Key": "chave-lab-teste"},
        )

        cliente.get(f"/me/laboratorio/sessoes/{s_id}")

    # Verifica todos os registros de log capturados
    for record in caplog.records:
        assert marcador_relato not in record.message
        assert marcador_relato not in str(record.args)
