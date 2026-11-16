"""Testes de validacao de entrada, codigos HTTP e regras de negocio da Lambda."""

import base64
import json
import logging

import pytest

from citizentech_cloud.lambda_function import lambda_handler


def _evento_post(payload=None, body_raw=None, headers=None, path="/ocorrencias", b64=False):
    if body_raw is None:
        body_raw = json.dumps(payload) if payload is not None else None
    return {
        "rawPath": path,
        "requestContext": {"http": {"method": "POST", "path": path}},
        "headers": headers or {},
        "body": body_raw,
        "isBase64Encoded": b64,
    }


@pytest.mark.postgres
def test_400_json_malformado(caplog):
    with caplog.at_level(logging.WARNING):
        resp = lambda_handler(_evento_post(body_raw="{json:invalido"))
    assert resp["statusCode"] == 400
    corpo = json.loads(resp["body"])
    assert "JSON malformado" in corpo["erro"]
    assert "LEITURA DESCARTADA" in caplog.text


@pytest.mark.postgres
def test_400_corpo_nao_objeto(caplog):
    with caplog.at_level(logging.WARNING):
        resp = lambda_handler(_evento_post(body_raw='"apenas uma string"'))
    assert resp["statusCode"] == 400
    assert "LEITURA DESCARTADA" in caplog.text

    resp_lista = lambda_handler(_evento_post(body_raw="[1, 2, 3]"))
    assert resp_lista["statusCode"] == 400


@pytest.mark.postgres
def test_400_corpo_maior_que_8kb(caplog):
    grande = {
        "dispositivo_id": "teste-disp",
        "metrica": "temperatura_c",
        "valor": 25.0,
        "extra": "x" * 9000,
    }
    with caplog.at_level(logging.WARNING):
        resp = lambda_handler(_evento_post(payload=grande))
    assert resp["statusCode"] == 400
    assert "LEITURA DESCARTADA" in caplog.text


@pytest.mark.postgres
def test_400_campos_obrigatorios_ausentes_ou_nulos():
    for campo in ["dispositivo_id", "metrica", "valor"]:
        base = {"dispositivo_id": "teste-disp", "metrica": "temperatura_c", "valor": 25.0}
        del base[campo]
        resp = lambda_handler(_evento_post(payload=base))
        assert resp["statusCode"] == 400

        base_nulo = {"dispositivo_id": "teste-disp", "metrica": "temperatura_c", "valor": 25.0}
        base_nulo[campo] = None
        resp_nulo = lambda_handler(_evento_post(payload=base_nulo))
        assert resp_nulo["statusCode"] == 400


@pytest.mark.postgres
def test_400_dispositivo_id_vazio_ou_maior_que_64():
    p_vazio = {"dispositivo_id": "", "metrica": "temperatura_c", "valor": 20.0}
    resp_vazio = lambda_handler(_evento_post(payload=p_vazio))
    assert resp_vazio["statusCode"] == 400

    p_longo = {"dispositivo_id": "d" * 65, "metrica": "temperatura_c", "valor": 20.0}
    resp_longo = lambda_handler(_evento_post(payload=p_longo))
    assert resp_longo["statusCode"] == 400


@pytest.mark.postgres
def test_400_valor_invalido_tipos_e_faixas():
    # Booleano
    p_bool = {"dispositivo_id": "teste-disp", "metrica": "temperatura_c", "valor": True}
    resp_bool = lambda_handler(_evento_post(payload=p_bool))
    assert resp_bool["statusCode"] == 400

    # String
    p_str = {"dispositivo_id": "teste-disp", "metrica": "temperatura_c", "valor": "25.0"}
    resp_str = lambda_handler(_evento_post(payload=p_str))
    assert resp_str["statusCode"] == 400

    # Fora de [-1e6, 1e6]
    p_alto = {"dispositivo_id": "teste-disp", "metrica": "temperatura_c", "valor": 2e6}
    resp_alto = lambda_handler(_evento_post(payload=p_alto))
    assert resp_alto["statusCode"] == 400

    p_baixo = {"dispositivo_id": "teste-disp", "metrica": "temperatura_c", "valor": -2e6}
    resp_baixo = lambda_handler(_evento_post(payload=p_baixo))
    assert resp_baixo["statusCode"] == 400

    # NaN literal no JSON
    raw_nan = '{"dispositivo_id": "teste-disp", "metrica": "temperatura_c", "valor": NaN}'
    resp_nan = lambda_handler(_evento_post(body_raw=raw_nan))
    assert resp_nan["statusCode"] == 400


@pytest.mark.postgres
def test_400_metrica_conhecida_com_valor_invalido_para_risco():
    # distancia_cm nao pode ser negativa conforme limiares.json
    payload = {"dispositivo_id": "teste-disp", "metrica": "distancia_cm", "valor": -5.0}
    resp = lambda_handler(_evento_post(payload=payload))
    assert resp["statusCode"] == 400
    corpo = json.loads(resp["body"])
    assert "Valor invalido" in corpo["erro"]


@pytest.mark.postgres
def test_400_latitude_longitude_invalidas():
    # Latitude fora de [-90, 90]
    p_lat = {
        "dispositivo_id": "teste-disp",
        "metrica": "temperatura_c",
        "valor": 25.0,
        "latitude": 91.0,
    }
    resp_lat = lambda_handler(_evento_post(payload=p_lat))
    assert resp_lat["statusCode"] == 400

    # Longitude fora de [-180, 180]
    p_lon = {
        "dispositivo_id": "teste-disp",
        "metrica": "temperatura_c",
        "valor": 25.0,
        "longitude": -185.0,
    }
    resp_lon = lambda_handler(_evento_post(payload=p_lon))
    assert resp_lon["statusCode"] == 400


@pytest.mark.postgres
def test_400_relato_longo():
    payload = {
        "dispositivo_id": "teste-disp",
        "metrica": "temperatura_c",
        "valor": 25.0,
        "relato": "a" * 281,
    }
    resp = lambda_handler(_evento_post(payload=payload))
    assert resp["statusCode"] == 400


@pytest.mark.postgres
def test_400_evento_id_invalido():
    # Nao string
    p_int = {
        "dispositivo_id": "teste-disp",
        "metrica": "temperatura_c",
        "valor": 25.0,
        "evento_id": 12345,
    }
    resp_int = lambda_handler(_evento_post(payload=p_int))
    assert resp_int["statusCode"] == 400

    # Mais de 64 caracteres
    p_longo = {
        "dispositivo_id": "teste-disp",
        "metrica": "temperatura_c",
        "valor": 25.0,
        "evento_id": "e" * 65,
    }
    resp_longo = lambda_handler(_evento_post(payload=p_longo))
    assert resp_longo["statusCode"] == 400


@pytest.mark.postgres
def test_body_base64_decodificado():
    payload = {"dispositivo_id": "teste-disp-b64", "metrica": "temperatura_c", "valor": 25.0}
    b64_str = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")
    resp = lambda_handler(_evento_post(body_raw=b64_str, b64=True))
    assert resp["statusCode"] == 201
    corpo = json.loads(resp["body"])
    assert corpo["dispositivo_id"] == "teste-disp-b64"


@pytest.mark.postgres
def test_404_rota_inexistente():
    evento = {
        "rawPath": "/rota_desconhecida",
        "requestContext": {"http": {"method": "GET", "path": "/rota_desconhecida"}},
    }
    resp = lambda_handler(evento)
    assert resp["statusCode"] == 404


@pytest.mark.postgres
def test_405_metodo_errado():
    evento = {
        "rawPath": "/ocorrencias",
        "requestContext": {"http": {"method": "DELETE", "path": "/ocorrencias"}},
    }
    resp = lambda_handler(evento)
    assert resp["statusCode"] == 405


@pytest.mark.postgres
def test_barra_final_equivale_a_rota_sem_barra():
    """Rotas /ocorrencias/ e /health/ com barra final equivalem as rotas sem barra."""
    # 1. GET /health/ deve responder 200 status: ok
    resp_health = lambda_handler({
        "rawPath": "/health/",
        "requestContext": {"http": {"method": "GET", "path": "/health/"}},
    })
    assert resp_health["statusCode"] == 200
    corpo_health = json.loads(resp_health["body"])
    assert corpo_health["status"] == "ok"

    # 2. GET /ocorrencias/ deve responder 200
    resp_get_ocorr = lambda_handler({
        "rawPath": "/ocorrencias/",
        "requestContext": {"http": {"method": "GET", "path": "/ocorrencias/"}},
    })
    assert resp_get_ocorr["statusCode"] == 200

    # 3. POST /ocorrencias/ deve processar normalmente (ex: 201)
    payload = {
        "dispositivo_id": "teste-disp-barra",
        "metrica": "temperatura_c",
        "valor": 25.0,
    }
    resp_post_ocorr = lambda_handler(_evento_post(payload=payload, path="/ocorrencias/"))
    assert resp_post_ocorr["statusCode"] == 201


@pytest.mark.postgres
def test_401_chave_errada_e_nao_aparece_no_log(monkeypatch, caplog):
    monkeypatch.setenv("DEVICE_KEY", "chave-secreta-correta")
    chave_invalida = "chave-invalida-super-secreta"

    payload = {"dispositivo_id": "teste-disp-401", "metrica": "temperatura_c", "valor": 25.0}
    evento = _evento_post(payload=payload, headers={"x-device-key": chave_invalida})

    with caplog.at_level(logging.WARNING):
        resp = lambda_handler(evento)

    assert resp["statusCode"] == 401
    assert "CHAVE INVALIDA" in caplog.text
    # Garantir que o valor da chave NUNCA vaza no log
    assert chave_invalida not in caplog.text
    assert "chave-secreta-correta" not in caplog.text


@pytest.mark.postgres
def test_429_rate_limit_excedido_no_banco(monkeypatch, caplog):
    monkeypatch.setenv("RATE_LIMIT_POR_MINUTO", "2")

    payload1 = {"dispositivo_id": "teste-disp-rate", "metrica": "temperatura_c", "valor": 25.0}
    payload2 = {"dispositivo_id": "teste-disp-outro", "metrica": "temperatura_c", "valor": 25.0}

    # Leitura 1 disp-rate -> 201
    assert lambda_handler(_evento_post(payload=payload1))["statusCode"] == 201
    # Leitura 2 disp-rate -> 201
    assert lambda_handler(_evento_post(payload=payload1))["statusCode"] == 201

    # Leitura 3 disp-rate -> 429
    with caplog.at_level(logging.WARNING):
        resp3 = lambda_handler(_evento_post(payload=payload1))
    assert resp3["statusCode"] == 429
    assert "LIMITE EXCEDIDO" in caplog.text

    # Outro dispositivo nao deve ser afetado -> 201
    assert lambda_handler(_evento_post(payload=payload2))["statusCode"] == 201


@pytest.mark.postgres
def test_idempotencia_antes_do_rate_limit(monkeypatch):
    """Reenvio de evento_id existente deve responder duplicata (200)

    mesmo apos o rate limit por minuto ter sido atingido.
    """
    monkeypatch.setenv("RATE_LIMIT_POR_MINUTO", "2")

    payload1 = {
        "evento_id": "teste-evt-idemp-01",
        "dispositivo_id": "teste-disp-idemp",
        "metrica": "temperatura_c",
        "valor": 25.0,
    }
    payload2 = {
        "evento_id": "teste-evt-idemp-02",
        "dispositivo_id": "teste-disp-idemp",
        "metrica": "temperatura_c",
        "valor": 26.0,
    }

    # 1. Enviar primeira leitura -> 201
    resp1 = lambda_handler(_evento_post(payload=payload1))
    assert resp1["statusCode"] == 201
    corpo1 = json.loads(resp1["body"])
    id_original = corpo1["id"]

    # 2. Enviar segunda leitura com evento_id diferente -> 201 (atinge o limite de 2/min)
    resp2 = lambda_handler(_evento_post(payload=payload2))
    assert resp2["statusCode"] == 201

    # 3. Reenviar a primeira leitura identica -> deve retornar 200 duplicata, NAO 429!
    resp3 = lambda_handler(_evento_post(payload=payload1))
    assert resp3["statusCode"] == 200
    corpo3 = json.loads(resp3["body"])
    assert corpo3["id"] == id_original
    assert corpo3.get("duplicata") is True


@pytest.mark.postgres
def test_corrida_rate_limit_concorrente(monkeypatch):
    """6 threads simultaneas do mesmo dispositivo com RATE_LIMIT_POR_MINUTO=3

    devem resultar em exatamente 3 respostas 201 e 3 respostas 429,
    sem ultrapassar a cota por concorrencia desprotegida.
    """
    import concurrent.futures

    monkeypatch.setenv("RATE_LIMIT_POR_MINUTO", "3")
    disp_id = "teste-disp-corrida-rate"

    respostas = []

    def enviar_leitura(indice):
        payload = {
            "dispositivo_id": disp_id,
            "metrica": "temperatura_c",
            "valor": 20.0 + indice,
        }
        return lambda_handler(_evento_post(payload=payload))

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futuros = [executor.submit(enviar_leitura, i) for i in range(6)]
        for f in concurrent.futures.as_completed(futuros):
            respostas.append(f.result())

    status_codes = [r["statusCode"] for r in respostas]
    qtd_201 = status_codes.count(201)
    qtd_429 = status_codes.count(429)

    assert len(respostas) == 6
    assert qtd_201 == 3, f"Esperado 3 respostas 201, obtido {qtd_201} (status: {status_codes})"
    assert qtd_429 == 3, f"Esperado 3 respostas 429, obtido {qtd_429} (status: {status_codes})"


@pytest.mark.postgres
def test_classificacao_temperatura_48_critico_alerta_cidadao(caplog):
    payload = {"dispositivo_id": "teste-disp-critico", "metrica": "temperatura_c", "valor": 48.0}
    with caplog.at_level(logging.WARNING):
        resp = lambda_handler(_evento_post(payload=payload))

    assert resp["statusCode"] == 201
    corpo = json.loads(resp["body"])
    assert corpo["nivel_risco"] == "critico"
    assert corpo["alerta"] is True
    assert "ALERTA CIDADAO" in caplog.text


@pytest.mark.postgres
def test_classificacao_distancia_12_atencao():
    payload = {"dispositivo_id": "teste-disp-atencao", "metrica": "distancia_cm", "valor": 12.0}
    resp = lambda_handler(_evento_post(payload=payload))
    assert resp["statusCode"] == 201
    corpo = json.loads(resp["body"])
    assert corpo["nivel_risco"] == "atencao"
    assert corpo["alerta"] is False


@pytest.mark.postgres
def test_payload_exato_outbox_api_com_chave(monkeypatch, caplog):
    monkeypatch.setenv("DEVICE_KEY", "chave-outbox-valida")

    # Contrato oficial da outbox da API
    payload_outbox = {
        "evento_id": "teste-outbox-evt-999",
        "dispositivo_id": "teste-outbox-disp",
        "sessao_laboratorio_id": "sessao-lab-01",
        "ciclo_id": "ciclo-01",
        "tipo_dispositivo": "sensor_bancada",
        "metrica": "temperatura_c",
        "unidade": "C",
        "valor": 38.0,
        "risco": "normal",  # Risco divergente proposital para verificar recalculacao
        "alerta": False,
        "medido_em": "2026-11-16T12:00:00Z",
        "criado_em": "2026-11-16T12:00:01Z",
    }
    evento = _evento_post(payload=payload_outbox, headers={"x-device-key": "chave-outbox-valida"})

    with caplog.at_level(logging.INFO):
        resp = lambda_handler(evento)

    assert resp["statusCode"] == 201
    corpo = json.loads(resp["body"])
    assert corpo["evento_id"] == "teste-outbox-evt-999"
    assert corpo["id"] is not None
    assert corpo["autenticado"] is True
    # Risco recalculado localmente para 38.0 deve ser atencao!
    assert corpo["nivel_risco"] == "atencao"
    assert "diverge" in caplog.text


@pytest.mark.postgres
def test_banco_indisponivel_retorna_503_sem_vazar_host(monkeypatch):
    monkeypatch.setenv("DB_PORT", "59999")  # Porta inexistente
    monkeypatch.setenv("DB_HOST", "host-secreto-banco")

    payload = {"dispositivo_id": "teste-disp-503", "metrica": "temperatura_c", "valor": 25.0}
    resp = lambda_handler(_evento_post(payload=payload))

    assert resp["statusCode"] == 503
    corpo = json.loads(resp["body"])
    assert "Banco indisponivel" in corpo["erro"]
    assert "host-secreto-banco" not in resp["body"]
    assert "59999" not in resp["body"]


@pytest.mark.postgres
def test_get_ocorrencias_limite():
    # Inserir 3 registros
    for i in range(3):
        p = {"dispositivo_id": f"teste-disp-get-{i}", "metrica": "temperatura_c", "valor": 20.0 + i}
        lambda_handler(_evento_post(payload=p))

    # GET com limite=2
    evento = {
        "rawPath": "/ocorrencias",
        "rawQueryString": "limite=2",
        "requestContext": {"http": {"method": "GET", "path": "/ocorrencias"}},
    }
    resp = lambda_handler(evento)
    assert resp["statusCode"] == 200
    corpo = json.loads(resp["body"])
    assert len(corpo["ocorrencias"]) == 2
    # Ordenado por id DESC
    assert corpo["ocorrencias"][0]["id"] > corpo["ocorrencias"][1]["id"]


@pytest.mark.postgres
def test_get_ocorrencias_limite_invalido():
    # limite = 0
    resp0 = lambda_handler({
        "rawPath": "/ocorrencias",
        "rawQueryString": "limite=0",
        "requestContext": {"http": {"method": "GET", "path": "/ocorrencias"}},
    })
    assert resp0["statusCode"] == 400

    # limite = abc
    resp_abc = lambda_handler({
        "rawPath": "/ocorrencias",
        "rawQueryString": "limite=abc",
        "requestContext": {"http": {"method": "GET", "path": "/ocorrencias"}},
    })
    assert resp_abc["statusCode"] == 400


@pytest.mark.postgres
def test_health_check_com_banco_ok_e_banco_fora(monkeypatch):
    # 1. Com banco ok
    resp_ok = lambda_handler({
        "rawPath": "/health",
        "requestContext": {"http": {"method": "GET", "path": "/health"}},
    })
    assert resp_ok["statusCode"] == 200
    corpo_ok = json.loads(resp_ok["body"])
    assert corpo_ok["status"] == "ok"
    assert corpo_ok["banco"] == "ok"

    # 2. Com banco fora
    monkeypatch.setenv("DB_PORT", "59999")
    resp_fora = lambda_handler({
        "rawPath": "/health",
        "requestContext": {"http": {"method": "GET", "path": "/health"}},
    })
    assert resp_fora["statusCode"] == 200
    corpo_fora = json.loads(resp_fora["body"])
    assert corpo_fora["status"] == "ok"
    assert corpo_fora["banco"] == "indisponivel"


@pytest.mark.postgres
@pytest.mark.parametrize(
    "extra",
    [
        {"metrica": {"a": 1}},
        {"metrica": ""},
        {"metrica": "m" * 65},
        {"tipo_dispositivo": 5},
        {"tipo_dispositivo": "t" * 33},
        {"medido_em": "ontem"},
        {"medido_em": 123},
        {"unidade": 5},
        {"sessao_laboratorio_id": "s" * 65},
    ],
)
def test_400_campos_texto_invalidos_nunca_viram_503_nem_201(extra, caplog):
    payload = {"dispositivo_id": "teste-texto", "metrica": "temperatura_c", "valor": 25.0}
    payload.update(extra)
    with caplog.at_level(logging.WARNING):
        resp = lambda_handler(_evento_post(payload=payload))
    assert resp["statusCode"] == 400
    assert "LEITURA DESCARTADA" in caplog.text


@pytest.mark.postgres
def test_medido_em_iso_com_fuso_e_aceito():
    payload = {
        "dispositivo_id": "teste-medido",
        "metrica": "temperatura_c",
        "valor": 25.0,
        "medido_em": "2026-11-16T14:00:00Z",
    }
    assert lambda_handler(_evento_post(payload=payload))["statusCode"] == 201
