"""Testes de integracao do Outbox duravel e reenvio idempotente (S3)."""

import concurrent.futures
import json
from datetime import UTC, datetime, timedelta

import httpx
from fastapi.testclient import TestClient

from citizentech.main import app, criar_app
from citizentech.outbox.banco import (
    obter_mapa_estados,
    obter_pendencia,
    reconciliar_com_csv,
)
from citizentech.outbox.cliente import ClienteLambda
from citizentech.outbox.worker import processar_pendencias_uma_vez


def test_red_prioritario_resiliencia_e_sincronizacao_outbox(monkeypatch, tmp_path):
    """Teste prioritario RED:

    1. POST leitura valido -> 201 local pendente;
    2. Fronteira fake Lambda falha por timeout/503;
    3. Apos processamento explicito de UMA iteracao e recriacao da aplicacao apontando
       ao mesmo runtime, GET ainda retorna leitura pendente e mesmo evento_id;
    4. Quando fake volta e aceita 201, GET passa a sincronizado.
    """
    caminho_csv = tmp_path / "runtime" / "leituras.csv"
    caminho_db = tmp_path / "runtime" / "outbox.db"
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(caminho_csv))
    monkeypatch.setenv("CITIZENTECH_OUTBOX_DB", str(caminho_db))
    monkeypatch.setenv("DEVICE_KEY", "chave-secreta-s3")
    monkeypatch.setenv("FUNCTION_URL", "https://fake.example.test/telemetria")

    deve_falhar = True
    registros_recebidos = []

    def fake_lambda_handler(request: httpx.Request) -> httpx.Response:
        corpo = json.loads(request.content.decode("utf-8"))
        registros_recebidos.append(corpo)
        if deve_falhar:
            return httpx.Response(503, json={"erro": "Nuvem temporariamente indisponivel"})
        return httpx.Response(
            201,
            json={"evento_id": corpo["evento_id"], "id": f"nuvem-{corpo['evento_id']}"},
        )

    transport = httpx.MockTransport(fake_lambda_handler)
    cliente_lambda = ClienteLambda(
        url="https://fake.example.test/telemetria",
        chave_dispositivo="chave-secreta-s3",
        transport=transport,
    )

    tempo_simulado = datetime.now(UTC)

    def relogio() -> datetime:
        return tempo_simulado

    # 1. POST leitura valido -> 201 local pendente
    cliente = TestClient(app)
    payload = {
        "evento_id": "evt-s3-demo-001",
        "ciclo_id": "ciclo-s3",
        "sessao_laboratorio_id": "sessao-s3",
        "dispositivo_id": "esp32-s3-01",
        "tipo_dispositivo": "esp32",
        "metrica": "temperatura_c",
        "unidade": "C",
        "valor": 38.0,
        "medido_em": "2026-11-13T12:00:00Z",
    }
    resp_post = cliente.post(
        "/leituras",
        json=payload,
        headers={"X-Device-Key": "chave-secreta-s3"},
    )
    assert resp_post.status_code == 201
    dados_post = resp_post.json()
    assert dados_post["evento_id"] == "evt-s3-demo-001"
    assert dados_post["estado"] == "pendente_nuvem"

    # 2. Fake Lambda falha por 503; executa UMA iteracao
    processar_pendencias_uma_vez(cliente=cliente_lambda, relogio=relogio)

    # 3. Recriacao da aplicacao apontando para o mesmo runtime
    novo_cliente = TestClient(app)
    resp_get1 = novo_cliente.get(
        "/leituras",
        headers={"X-Device-Key": "chave-secreta-s3"},
    )
    assert resp_get1.status_code == 200
    dados_get1 = resp_get1.json()
    assert dados_get1["total"] == 1
    assert dados_get1["itens"][0]["evento_id"] == "evt-s3-demo-001"
    assert dados_get1["itens"][0]["estado"] == "pendente_nuvem"

    # 4. Fake volta e aceita 201; avanca relogio injetavel e executa UMA iteracao
    deve_falhar = False
    tempo_simulado += timedelta(seconds=2)
    processar_pendencias_uma_vez(cliente=cliente_lambda, relogio=relogio)

    resp_get2 = novo_cliente.get(
        "/leituras",
        headers={"X-Device-Key": "chave-secreta-s3"},
    )
    assert resp_get2.status_code == 200
    dados_get2 = resp_get2.json()
    assert dados_get2["itens"][0]["estado"] == "sincronizado"


def test_reenvio_identico_retorna_200_com_mesmo_evento_id(monkeypatch, tmp_path):
    caminho_csv = tmp_path / "runtime" / "leituras.csv"
    caminho_db = tmp_path / "runtime" / "outbox.db"
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(caminho_csv))
    monkeypatch.setenv("CITIZENTECH_OUTBOX_DB", str(caminho_db))
    monkeypatch.setenv("DEVICE_KEY", "chave-secreta-demo")

    cliente = TestClient(app)

    payload = {
        "evento_id": "evt-reenvio-001",
        "ciclo_id": "ciclo-1",
        "sessao_laboratorio_id": "sessao-1",
        "dispositivo_id": "esp32-01",
        "tipo_dispositivo": "esp32",
        "metrica": "temperatura_c",
        "unidade": "C",
        "valor": 38.0,
    }

    # 1. Primeiro envio -> 201 Created
    r1 = cliente.post("/leituras", json=payload, headers={"X-Device-Key": "chave-secreta-demo"})
    assert r1.status_code == 201
    dados1 = r1.json()
    assert dados1["evento_id"] == "evt-reenvio-001"
    medido_em_original = dados1["medido_em"]
    assert medido_em_original != ""

    # 2. Reenvio identico (omitindo medido_em novamente) -> 200 OK reaproveita medido_em
    r2 = cliente.post("/leituras", json=payload, headers={"X-Device-Key": "chave-secreta-demo"})
    assert r2.status_code == 200
    dados2 = r2.json()
    assert dados2["evento_id"] == "evt-reenvio-001"
    assert dados2["medido_em"] == medido_em_original
    # Reenvio local nao significa sincronizacao remota (continua pendente_nuvem)
    assert dados2["estado"] == "pendente_nuvem"

    # 3. Reenvio identico explicitando o medido_em original -> 200 OK
    payload_com_medido = dict(payload)
    payload_com_medido["medido_em"] = medido_em_original
    r3 = cliente.post(
        "/leituras",
        json=payload_com_medido,
        headers={"X-Device-Key": "chave-secreta-demo"},
    )
    assert r3.status_code == 200
    assert r3.json()["evento_id"] == "evt-reenvio-001"

    # Confirma que o CSV contem exatamente 1 linha de dados
    linhas = caminho_csv.read_text(encoding="utf-8").strip().splitlines()
    assert len(linhas) == 2  # cabecalho + 1 registro


def test_reenvio_com_conteudo_divergente_retorna_409_conflito(monkeypatch, tmp_path):
    caminho_csv = tmp_path / "runtime" / "leituras.csv"
    caminho_db = tmp_path / "runtime" / "outbox.db"
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(caminho_csv))
    monkeypatch.setenv("CITIZENTECH_OUTBOX_DB", str(caminho_db))
    monkeypatch.setenv("DEVICE_KEY", "chave-secreta-demo")

    cliente = TestClient(app)

    payload_base = {
        "evento_id": "evt-conflito-base",
        "ciclo_id": "ciclo-orig",
        "sessao_laboratorio_id": "sessao-orig",
        "dispositivo_id": "esp32-orig",
        "tipo_dispositivo": "esp32",
        "metrica": "temperatura_c",
        "valor": 25.0,
        "medido_em": "2026-11-13T10:00:00Z",
    }

    r_orig = cliente.post(
        "/leituras",
        json=payload_base,
        headers={"X-Device-Key": "chave-secreta-demo"},
    )
    assert r_orig.status_code == 201

    variacoes_conflitantes = [
        {"valor": 38.0},  # Valor divergente
        {"metrica": "distancia_cm"},  # Metrica divergente
        {"dispositivo_id": "esp32-outro"},  # Dispositivo divergente
        {"sessao_laboratorio_id": "sessao-outra"},  # Sessao divergente
        {"ciclo_id": "ciclo-outro"},  # Ciclo divergente
        {"tipo_dispositivo": "sensor_banco"},  # Tipo disp divergente
        {"medido_em": "2026-11-13T11:00:00Z"},  # Timestamp divergente
    ]

    for variacao in variacoes_conflitantes:
        payload_alt = dict(payload_base)
        payload_alt.update(variacao)
        r_conf = cliente.post(
            "/leituras",
            json=payload_alt,
            headers={"X-Device-Key": "chave-secreta-demo"},
        )
        assert r_conf.status_code == 409, f"Deveria falhar com 409 para {variacao}"
        assert r_conf.json()["erro"] == "Conflito"

    # Confirma que os dados originais no CSV e no GET permaneceram intactos
    r_get = cliente.get("/leituras", headers={"X-Device-Key": "chave-secreta-demo"})
    assert r_get.status_code == 200
    dados_get = r_get.json()
    assert dados_get["total"] == 1
    assert dados_get["itens"][0]["valor"] == 25.0
    assert dados_get["itens"][0]["dispositivo_id"] == "esp32-orig"


def test_concorrencia_reenvios_mesmo_evento_id(monkeypatch, tmp_path):
    caminho_csv = tmp_path / "runtime" / "leituras_conc.csv"
    caminho_db = tmp_path / "runtime" / "outbox_conc.db"
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(caminho_csv))
    monkeypatch.setenv("CITIZENTECH_OUTBOX_DB", str(caminho_db))
    monkeypatch.setenv("DEVICE_KEY", "chave-secreta-demo")
    monkeypatch.setenv("CITIZENTECH_RATE_LIMIT_POR_MINUTO", "500")

    cliente = TestClient(app)
    workers = 6

    payload = {
        "evento_id": "evt-concorrente-unico",
        "dispositivo_id": "esp32-conc",
        "metrica": "temperatura_c",
        "valor": 38.0,
        "medido_em": "2026-11-13T12:00:00Z",
    }

    def enviar(_: int) -> int:
        resp = cliente.post(
            "/leituras",
            json=payload,
            headers={"X-Device-Key": "chave-secreta-demo"},
        )
        return resp.status_code

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        codigos = list(executor.map(enviar, range(workers)))

    # Exatamente 1 requisicao deve obter 201 e as outras 5 devem obter 200
    assert codigos.count(201) == 1
    assert codigos.count(200) == 5

    # CSV e outbox contem estritamente 1 registro
    linhas = caminho_csv.read_text(encoding="utf-8").strip().splitlines()
    assert len(linhas) == 2  # cabecalho + 1 registro
    assert len(obter_mapa_estados(caminho_db)) == 1


def test_simulacao_perda_de_resposta_apos_aceite_na_lambda(monkeypatch, tmp_path):
    """T13: perda de resposta DEPOIS que a Lambda aceitou o evento.

    Na proxima tentativa, manda o mesmo payload/evento_id. A fake Lambda reconhece
    a idempotencia, retorna 200 com mesmo ID e conta apenas um registro logico.
    """
    caminho_csv = tmp_path / "runtime" / "leituras.csv"
    caminho_db = tmp_path / "runtime" / "outbox.db"
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(caminho_csv))
    monkeypatch.setenv("CITIZENTECH_OUTBOX_DB", str(caminho_db))
    monkeypatch.setenv("DEVICE_KEY", "chave-secreta-s3")
    monkeypatch.setenv("FUNCTION_URL", "https://fake.example.test/telemetria")

    banco_remoto_lambda: dict[str, dict] = {}
    tentativa = 0

    def fake_lambda_handler(request: httpx.Request) -> httpx.Response:
        nonlocal tentativa
        tentativa += 1
        corpo = json.loads(request.content.decode("utf-8"))
        ev_id = corpo["evento_id"]

        # Registra logicamente no banco da nuvem
        if ev_id not in banco_remoto_lambda:
            banco_remoto_lambda[ev_id] = corpo

        if tentativa == 1:
            # Simula queda de conexao/timeout DEPOIS de o registro ter sido gravado na nuvem
            raise httpx.TimeoutException("Queda de conexao durante envio da resposta HTTP")

        # Tentativa 2: reenviou com o mesmo evento_id -> retorna 200 OK idempotente
        return httpx.Response(200, json={"evento_id": ev_id, "id": f"nuvem-{ev_id}"})

    transport = httpx.MockTransport(fake_lambda_handler)
    cliente_lambda = ClienteLambda(
        url="https://fake.example.test/telemetria",
        chave_dispositivo="chave-secreta-s3",
        transport=transport,
    )

    tempo_simulado = datetime.now(UTC)

    def relogio() -> datetime:
        return tempo_simulado

    cliente = TestClient(app)
    p = {
        "evento_id": "evt-perda-resposta-001",
        "dispositivo_id": "esp32-01",
        "metrica": "temperatura_c",
        "valor": 38.0,
    }
    r_post = cliente.post("/leituras", json=p, headers={"X-Device-Key": "chave-secreta-s3"})
    assert r_post.status_code == 201

    # 1a tentativa: falha por timeout (mas a Lambda gravou)
    processar_pendencias_uma_vez(cliente=cliente_lambda, relogio=relogio)
    p_atual = obter_pendencia("evt-perda-resposta-001", caminho_db)
    assert p_atual["estado"] == "pendente_nuvem"
    assert p_atual["ultimo_erro"] == "TIMEOUT"

    # 2a tentativa: avanca relogio e reenvia
    tempo_simulado += timedelta(seconds=2)
    processar_pendencias_uma_vez(cliente=cliente_lambda, relogio=relogio)

    p_final = obter_pendencia("evt-perda-resposta-001", caminho_db)
    assert p_final["estado"] == "sincronizado"
    assert p_final["ultimo_erro"] is None

    # Verifica que a Lambda contem exatamente 1 registro logico para o evento
    assert len(banco_remoto_lambda) == 1
    assert "evt-perda-resposta-001" in banco_remoto_lambda


def test_reconciliacao_csv_para_outbox_recupera_orfaos_apos_crash(monkeypatch, tmp_path):
    """Simula crash ocorrido apos append/fsync no CSV mas antes do commit no SQLite."""
    caminho_csv = tmp_path / "runtime" / "leituras.csv"
    caminho_db = tmp_path / "runtime" / "outbox.db"
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(caminho_csv))
    monkeypatch.setenv("CITIZENTECH_OUTBOX_DB", str(caminho_db))
    monkeypatch.setenv("DEVICE_KEY", "chave-secreta-demo")

    caminho_csv.parent.mkdir(parents=True, exist_ok=True)
    cabecalho = (
        "evento_id,dispositivo_id,sessao_laboratorio_id,ciclo_id,tipo_dispositivo,"
        "metrica,unidade,valor,risco,alerta,estado,medido_em,criado_em\n"
    )
    linha_orfao = (
        "evt-orfao-1,esp32-01,s1,c1,esp32,temperatura_c,C,38.0,atencao,True,"
        "pendente_nuvem,2026-11-13T12:00:00Z,2026-11-13T12:00:00Z\n"
    )
    caminho_csv.write_text(cabecalho + linha_orfao, encoding="utf-8")

    # Inicialmente o SQLite esta vazio
    assert obter_pendencia("evt-orfao-1", caminho_db) is None

    # Executa reconciliacao de startup
    qtd = reconciliar_com_csv(caminho_csv=caminho_csv, caminho_db=caminho_db)
    assert qtd == 1

    pendencia = obter_pendencia("evt-orfao-1", caminho_db)
    assert pendencia is not None
    assert pendencia["evento_id"] == "evt-orfao-1"
    assert pendencia["estado"] == "pendente_nuvem"

    # Segunda reconciliacao nao duplica nem reverte
    qtd2 = reconciliar_com_csv(caminho_csv=caminho_csv, caminho_db=caminho_db)
    assert qtd2 == 0


def test_falha_sqlite_retorna_503_sem_enviar_a_nuvem(monkeypatch, tmp_path):
    caminho_csv = tmp_path / "runtime" / "leituras.csv"
    # Configura outbox_db apontando para um diretorio existente (falha no SQLite)
    pasta_db_invalida = tmp_path / "runtime" / "outbox.db"
    pasta_db_invalida.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(caminho_csv))
    monkeypatch.setenv("CITIZENTECH_OUTBOX_DB", str(pasta_db_invalida))
    monkeypatch.setenv("DEVICE_KEY", "chave-secreta-demo")

    cliente = TestClient(app)
    p = {
        "evento_id": "evt-falha-sqlite",
        "dispositivo_id": "esp32-01",
        "metrica": "temperatura_c",
        "valor": 25.0,
    }
    resp = cliente.post("/leituras", json=p, headers={"X-Device-Key": "chave-secreta-demo"})
    assert resp.status_code == 503
    assert resp.json()["erro"] == "Servico indisponivel"


def test_nuvem_retorna_409_conflito_marca_sem_loop_infinito(monkeypatch, tmp_path):
    caminho_csv = tmp_path / "runtime" / "leituras.csv"
    caminho_db = tmp_path / "runtime" / "outbox.db"
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(caminho_csv))
    monkeypatch.setenv("CITIZENTECH_OUTBOX_DB", str(caminho_db))
    monkeypatch.setenv("DEVICE_KEY", "chave-secreta-demo")

    chamadas = 0

    def handler_409(req: httpx.Request) -> httpx.Response:
        nonlocal chamadas
        chamadas += 1
        return httpx.Response(409, json={"erro": "Conflito na nuvem"})

    cliente_lambda = ClienteLambda(
        url="https://fake.example.test",
        chave_dispositivo="key",
        transport=httpx.MockTransport(handler_409),
    )

    cliente = TestClient(app)
    p = {
        "evento_id": "evt-conflito-nuvem",
        "dispositivo_id": "esp32-01",
        "metrica": "temperatura_c",
        "valor": 38.0,
    }
    r = cliente.post("/leituras", json=p, headers={"X-Device-Key": "chave-secreta-demo"})
    assert r.status_code == 201

    # Primeira iteracao: recebe 409
    processar_pendencias_uma_vez(cliente=cliente_lambda)
    assert chamadas == 1
    pend = obter_pendencia("evt-conflito-nuvem", caminho_db)
    assert pend["estado"] == "conflito"
    assert pend["ultimo_erro"] == "CONFLITO_409"

    # Segunda iteracao: NAO deve tentar novamente (nao ha loop infinito)
    processar_pendencias_uma_vez(cliente=cliente_lambda)
    assert chamadas == 1

    # GET /leituras reflete estado "conflito"
    r_get = cliente.get("/leituras", headers={"X-Device-Key": "chave-secreta-demo"})
    assert r_get.status_code == 200
    assert r_get.json()["itens"][0]["estado"] == "conflito"


def test_nuvem_retorna_401_marca_erro_permanente(monkeypatch, tmp_path):
    caminho_csv = tmp_path / "runtime" / "leituras.csv"
    caminho_db = tmp_path / "runtime" / "outbox.db"
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(caminho_csv))
    monkeypatch.setenv("CITIZENTECH_OUTBOX_DB", str(caminho_db))
    monkeypatch.setenv("DEVICE_KEY", "chave-secreta-demo")

    chamadas = 0

    def handler_401(req: httpx.Request) -> httpx.Response:
        nonlocal chamadas
        chamadas += 1
        return httpx.Response(401, json={"erro": "Nao autorizado"})

    cliente_lambda = ClienteLambda(
        url="https://fake.example.test",
        chave_dispositivo="key",
        transport=httpx.MockTransport(handler_401),
    )

    cliente = TestClient(app)
    p = {
        "evento_id": "evt-auth-nuvem",
        "dispositivo_id": "esp32-01",
        "metrica": "temperatura_c",
        "valor": 38.0,
    }
    cliente.post("/leituras", json=p, headers={"X-Device-Key": "chave-secreta-demo"})

    processar_pendencias_uma_vez(cliente=cliente_lambda)
    assert chamadas == 1
    pend = obter_pendencia("evt-auth-nuvem", caminho_db)
    assert pend["estado"] == "erro_permanente"
    assert pend["ultimo_erro"] == "ERRO_CLIENTE_4XX"

    # Nao tenta novamente
    processar_pendencias_uma_vez(cliente=cliente_lambda)
    assert chamadas == 1

    r_get = cliente.get("/leituras", headers={"X-Device-Key": "chave-secreta-demo"})
    assert r_get.status_code == 200
    assert r_get.json()["itens"][0]["estado"] == "erro_permanente"


def test_lifespan_inicia_e_para_limpamente(monkeypatch, tmp_path):
    caminho_csv = tmp_path / "runtime" / "leituras.csv"
    caminho_db = tmp_path / "runtime" / "outbox.db"
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(caminho_csv))
    monkeypatch.setenv("CITIZENTECH_OUTBOX_DB", str(caminho_db))
    monkeypatch.setenv("DEVICE_KEY", "chave-secreta-demo")
    monkeypatch.setenv("FUNCTION_URL", "https://fake.example.test/telemetria")

    app_com_lifespan = criar_app()
    with TestClient(app_com_lifespan) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
