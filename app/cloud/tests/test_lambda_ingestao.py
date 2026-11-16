"""Testes prioritarios da Lambda de ingestao de ocorrencias."""

import json
import os

import pg8000.dbapi
import pytest

from citizentech_cloud.lambda_function import lambda_handler


def _consultar_banco(query: str, params: tuple = ()):
    host = os.environ.get("DB_HOST", "127.0.0.1")
    if host == "localhost":
        host = "127.0.0.1"
    conn = pg8000.dbapi.connect(
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=host,
        port=int(os.environ["DB_PORT"]),
        database=os.environ["DB_NAME"],
    )
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        return cur.fetchall()
    finally:
        conn.close()


@pytest.mark.postgres
def test_post_sem_chave_do_simulador_oficial_grava_201_nao_autenticado():
    """Simulador do professor envia medicao sem header e sem evento_id.

    Deve gravar com 201 e autenticado=False.
    """
    payload = {
        "dispositivo_id": "teste-sim-prof-01",
        "tipo_dispositivo": "sensor_estacao",
        "latitude": -23.5505,
        "longitude": -46.6333,
        "metrica": "nivel_rio_cm",
        "valor": 268.9,
        "medido_em": "2026-11-16T12:00:00Z",
        "relato": "Nivel da agua subindo proximo a ponte.",
    }
    evento = {
        "requestContext": {"http": {"method": "POST", "path": "/ocorrencias"}},
        "headers": {},
        "body": json.dumps(payload),
    }

    resposta = lambda_handler(evento)

    assert resposta["statusCode"] == 201
    corpo = json.loads(resposta["body"])
    assert corpo["autenticado"] is False
    assert corpo["nivel_risco"] == "desconhecido"
    assert corpo["alerta"] is False
    assert corpo["id"] is not None

    # Verificar presenca no banco
    linhas = _consultar_banco(
        "SELECT id, autenticado, nivel_risco FROM ocorrencias WHERE id = %s",
        (corpo["id"],),
    )
    assert len(linhas) == 1
    assert linhas[0][1] is False
    assert linhas[0][2] == "desconhecido"


@pytest.mark.postgres
def test_ia_fora_nao_derruba_ingestao(monkeypatch, caplog):
    """Quando o servico de IA falha, a ingestao continua com 201.

    Sentimento=None, analise_status='indisponivel', log WARNING e persistido no banco.
    """
    monkeypatch.setenv("SENTIMENTO_PROVEDOR", "comprehend")
    from citizentech_cloud import sentimento

    class ClienteComprehendFalho:
        def detect_sentiment(self, **kwargs):
            raise RuntimeError("Falha de conexao com o servico de IA")

    # Injetar fabrica de cliente Comprehend pelo caminho real
    monkeypatch.setattr(
        sentimento,
        "criar_cliente_comprehend",
        lambda: ClienteComprehendFalho(),
        raising=False,
    )

    payload = {
        "dispositivo_id": "teste-ia-fora-01",
        "tipo_dispositivo": "sensor_bancada",
        "metrica": "temperatura_c",
        "valor": 25.0,
        "relato": "Tudo normal na bancada de testes.",
    }
    evento = {
        "requestContext": {"http": {"method": "POST", "path": "/ocorrencias"}},
        "headers": {},
        "body": json.dumps(payload),
    }

    import logging
    with caplog.at_level(logging.WARNING):
        resposta = lambda_handler(evento)

    assert resposta["statusCode"] == 201
    corpo = json.loads(resposta["body"])
    assert corpo["sentimento"] is None
    assert corpo["analise_status"] == "indisponivel"
    assert "Falha na analise de sentimento" in caplog.text
    assert "RuntimeError" in caplog.text

    # Verificar linha gravada no Postgres com analise_status='indisponivel'
    linhas = _consultar_banco(
        "SELECT id, analise_status, sentimento FROM ocorrencias WHERE id = %s",
        (corpo["id"],),
    )
    assert len(linhas) == 1
    assert linhas[0][1] == "indisponivel"
    assert linhas[0][2] is None


@pytest.mark.postgres
def test_duplicata_identica_200_e_conteudo_diferente_409(monkeypatch):
    """Reenvio de evento_id identico retorna 200 com duplicata=true.

    Evento_id com conteudo alterado retorna 409.
    """
    monkeypatch.setenv("DEVICE_KEY", "chave-secreta-lab")

    payload1 = {
        "evento_id": "teste-evt-dup-12345",
        "dispositivo_id": "teste-disp-dup-01",
        "tipo_dispositivo": "sensor_bancada",
        "metrica": "temperatura_c",
        "valor": 25.0,
        "unidade": "C",
        "sessao_laboratorio_id": "sessao-1",
        "ciclo_id": "ciclo-1",
        "medido_em": "2026-11-16T12:00:00Z",
    }
    evento1 = {
        "requestContext": {"http": {"method": "POST", "path": "/ocorrencias"}},
        "headers": {"x-device-key": "chave-secreta-lab"},
        "body": json.dumps(payload1),
    }

    # Primeiro envio -> 201
    resp1 = lambda_handler(evento1)
    assert resp1["statusCode"] == 201
    corpo1 = json.loads(resp1["body"])
    primeiro_id = corpo1["id"]

    # Reenvio identico -> 200 com duplicata=true e mesmo id
    resp2 = lambda_handler(evento1)
    assert resp2["statusCode"] == 200
    corpo2 = json.loads(resp2["body"])
    assert corpo2["id"] == primeiro_id
    assert corpo2.get("duplicata") is True

    # Reenvio com mesmo evento_id mas valor diferente -> 409
    payload_diferente = dict(payload1)
    payload_diferente["valor"] = 48.0
    evento_conflito = {
        "requestContext": {"http": {"method": "POST", "path": "/ocorrencias"}},
        "headers": {"x-device-key": "chave-secreta-lab"},
        "body": json.dumps(payload_diferente),
    }
    resp3 = lambda_handler(evento_conflito)
    assert resp3["statusCode"] == 409
    corpo3 = json.loads(resp3["body"])
    assert "erro" in corpo3


@pytest.mark.postgres
def test_colisao_concorrente_evento_id_identico_200_e_diferente_409():
    """Provoca o caminho real de UniqueViolation (23505) do Postgres com threads concorrentes.

    Duas threads concorrentes com o mesmo evento_id:
    - Com conteudo identico -> uma recebe 201 e a outra 200 (duplicata=True)
    - Com conteudo diferente -> uma recebe 201 e a outra 409 (conflito)
    """
    import concurrent.futures

    # 1. Caso: Conteudo identico -> uma 201, a outra 200 duplicata
    payload_identico = {
        "evento_id": "teste-evt-race-dup-real",
        "dispositivo_id": "teste-disp-dup-real",
        "tipo_dispositivo": "sensor_bancada",
        "metrica": "temperatura_c",
        "valor": 25.0,
    }

    evento_dup = {
        "requestContext": {"http": {"method": "POST", "path": "/ocorrencias"}},
        "headers": {},
        "body": json.dumps(payload_identico),
    }

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(lambda_handler, evento_dup)
        f2 = executor.submit(lambda_handler, evento_dup)
        r1 = f1.result()
        r2 = f2.result()

    status_identico = sorted([r1["statusCode"], r2["statusCode"]])
    assert status_identico == [200, 201], f"Esperado [200, 201], obtido {status_identico}"
    corpos_identico = [json.loads(r1["body"]), json.loads(r2["body"])]
    resp_200 = next(c for c in corpos_identico if c.get("duplicata") is True)
    resp_201 = next(c for c in corpos_identico if not c.get("duplicata"))
    assert resp_200["id"] == resp_201["id"]

    # 2. Caso: Conteudo diferente -> uma 201, a outra 409 conflito
    payload_dif_1 = {
        "evento_id": "teste-evt-race-conf-real",
        "dispositivo_id": "teste-disp-conf-real",
        "tipo_dispositivo": "sensor_bancada",
        "metrica": "temperatura_c",
        "valor": 25.0,
    }
    payload_dif_2 = dict(payload_dif_1)
    payload_dif_2["valor"] = 35.0

    evento_dif_1 = {
        "requestContext": {"http": {"method": "POST", "path": "/ocorrencias"}},
        "headers": {},
        "body": json.dumps(payload_dif_1),
    }
    evento_dif_2 = {
        "requestContext": {"http": {"method": "POST", "path": "/ocorrencias"}},
        "headers": {},
        "body": json.dumps(payload_dif_2),
    }

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(lambda_handler, evento_dif_1)
        f2 = executor.submit(lambda_handler, evento_dif_2)
        r1 = f1.result()
        r2 = f2.result()

    status_diferente = sorted([r1["statusCode"], r2["statusCode"]])
    assert status_diferente == [201, 409], f"Esperado [201, 409], obtido {status_diferente}"
