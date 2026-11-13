"""Testes de integracao e contrato das rotas de telemetria CTP (S2)."""

import concurrent.futures

from fastapi.testclient import TestClient

from citizentech.main import app


def test_red_prioritario_post_e_get_persistente_apos_recriar_aplicacao(monkeypatch, tmp_path):
    caminho_csv = tmp_path / "runtime" / "leituras.csv"
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(caminho_csv))
    monkeypatch.setenv("DEVICE_KEY", "chave-secreta-demo")

    cliente = TestClient(app)

    payload = {
        "evento_id": "demo-ciclo-001-temperatura",
        "ciclo_id": "demo-ciclo-001",
        "sessao_laboratorio_id": "sessao-demo",
        "dispositivo_id": "esp32-lab-01",
        "tipo_dispositivo": "esp32",
        "metrica": "temperatura_c",
        "unidade": "C",
        "valor": 38.0,
        "medido_em": "2026-11-12T14:00:00Z",
        "relato": "Cenario didatico: aumento de temperatura.",
    }

    resposta_post = cliente.post(
        "/leituras",
        json=payload,
        headers={"X-Device-Key": "chave-secreta-demo"},
    )

    assert resposta_post.status_code == 201
    dados_post = resposta_post.json()
    assert dados_post["evento_id"] == "demo-ciclo-001-temperatura"
    assert dados_post["risco"] == "atencao"
    assert dados_post["alerta"] is True
    assert dados_post["estado"] == "pendente_nuvem"

    novo_cliente = TestClient(app)

    resposta_get = novo_cliente.get(
        "/leituras",
        headers={"X-Device-Key": "chave-secreta-demo"},
    )
    assert resposta_get.status_code == 200
    dados_get = resposta_get.json()
    assert dados_get["total"] == 1
    assert dados_get["itens"][0]["evento_id"] == "demo-ciclo-001-temperatura"
    assert dados_get["itens"][0]["valor"] == 38.0
    assert dados_get["itens"][0]["risco"] == "atencao"

    resposta_indicadores = novo_cliente.get(
        "/leituras/indicadores?metrica=temperatura_c",
        headers={"X-Device-Key": "chave-secreta-demo"},
    )
    assert resposta_indicadores.status_code == 200
    dados_ind = resposta_indicadores.json()
    assert dados_ind["contagem"] == 1
    assert dados_ind["total_alertas"] == 1
    assert dados_ind["media"] == 38.0
    assert dados_ind["maximo"] == 38.0
    assert dados_ind["minimo"] == 38.0


def test_cenarios_demonstracao_e_fronteiras_ignoram_status_declarado(monkeypatch, tmp_path):
    caminho_csv = tmp_path / "runtime" / "leituras.csv"
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(caminho_csv))
    monkeypatch.setenv("DEVICE_KEY", "chave-secreta-demo")

    cliente = TestClient(app)

    casos = [
        # Cenarios normais
        # O cliente declara ALERTA (vocabulario do firmware: OK/ALERTA/ERRO), mas a leitura e normal
        ("temperatura_c", 25.0, "normal", False, "ALERTA"),
        ("distancia_cm", 25.0, "normal", False, "ALERTA"),
        # Fronteiras e cenarios de atencao
        ("temperatura_c", 35.0, "atencao", True, "OK"),
        ("temperatura_c", 38.0, "atencao", True, "OK"),
        ("distancia_cm", 15.0, "atencao", True, "OK"),
        ("distancia_cm", 12.0, "atencao", True, "OK"),
        # Fronteiras e cenarios criticos
        ("temperatura_c", 45.0, "critico", True, "OK"),
        ("temperatura_c", 48.0, "critico", True, "OK"),
        ("distancia_cm", 8.0, "critico", True, "OK"),
        ("distancia_cm", 5.0, "critico", True, "OK"),
    ]

    for idx, (metrica, valor, risco_esp, alerta_esp, status_falso) in enumerate(casos):
        payload = {
            "dispositivo_id": f"disp-{idx}",
            "metrica": metrica,
            "valor": valor,
            "status": status_falso,
        }
        resp = cliente.post(
            "/leituras",
            json=payload,
            headers={"X-Device-Key": "chave-secreta-demo"},
        )
        assert resp.status_code == 201
        corpo = resp.json()
        assert corpo["risco"] == risco_esp, (
            f"Falhou para {metrica}={valor}: esperado {risco_esp}, obteve {corpo['risco']}"
        )
        assert corpo["alerta"] is alerta_esp


def test_validacao_rejeita_entradas_invalidas_com_400_e_sem_poluir_historico(monkeypatch, tmp_path):
    caminho_csv = tmp_path / "runtime" / "leituras.csv"
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(caminho_csv))
    monkeypatch.setenv("DEVICE_KEY", "chave-secreta-demo")

    cliente = TestClient(app)

    payloads_invalidos = [
        # Campos obrigatorios ausentes
        {"metrica": "temperatura_c", "valor": 25.0},
        {"dispositivo_id": "esp32-01", "valor": 25.0},
        {"dispositivo_id": "esp32-01", "metrica": "temperatura_c"},
        # Valor booleano
        {"dispositivo_id": "esp32-01", "metrica": "temperatura_c", "valor": True},
        {"dispositivo_id": "esp32-01", "metrica": "temperatura_c", "valor": False},
        # Valor string numerica
        {"dispositivo_id": "esp32-01", "metrica": "temperatura_c", "valor": "38.0"},
        # Metrica desconhecida
        {"dispositivo_id": "esp32-01", "metrica": "pressao_hpa", "valor": 1013.0},
        # Unidade incompativel
        {"dispositivo_id": "esp32-01", "metrica": "temperatura_c", "valor": 25.0, "unidade": "F"},
        {"dispositivo_id": "esp32-01", "metrica": "distancia_cm", "valor": 25.0, "unidade": "m"},
        # Falha de sensor fisico (-127 em temperatura)
        {"dispositivo_id": "esp32-01", "metrica": "temperatura_c", "valor": -127.0},
        # Status de erro do cliente
        {"dispositivo_id": "esp32-01", "metrica": "temperatura_c", "valor": 25.0, "status": "ERRO"},
        # Schema version incompativel
        {
            "dispositivo_id": "esp32-01",
            "metrica": "temperatura_c",
            "valor": 25.0,
            "schema_version": "2.0",
        },
        # Tipos invalidos em campos opcionais
        {
            "dispositivo_id": "esp32-01",
            "metrica": "temperatura_c",
            "valor": 25.0,
            "evento_id": False,
        },
        {
            "dispositivo_id": "esp32-01",
            "metrica": "temperatura_c",
            "valor": 25.0,
            "tipo_dispositivo": False,
        },
        {
            "dispositivo_id": "esp32-01",
            "metrica": "temperatura_c",
            "valor": 25.0,
            "relato": {"objeto": True},
        },
        {
            "dispositivo_id": "esp32-01",
            "metrica": "temperatura_c",
            "valor": 25.0,
            "relato": "A" * 281,
        },
        # Distancia negativa (abaixo do valor_minimo 0.0)
        {"dispositivo_id": "esp32-01", "metrica": "distancia_cm", "valor": -1.0},
        # Caracteres de controle / newline em identificadores (injecao em CSV)
        {"dispositivo_id": "esp32\nmalicioso", "metrica": "temperatura_c", "valor": 25.0},
        {
            "dispositivo_id": "esp32",
            "evento_id": "evt\r\nq",
            "metrica": "temperatura_c",
            "valor": 25.0,
        },
        # Timestamp medido_em sem timezone
        {
            "dispositivo_id": "esp32",
            "metrica": "temperatura_c",
            "valor": 25.0,
            "medido_em": "2026-11-12T14:00:00",
        },
    ]

    for p in payloads_invalidos:
        resp = cliente.post("/leituras", json=p, headers={"X-Device-Key": "chave-secreta-demo"})
        assert resp.status_code == 400, f"Esperado 400, obteve {resp.status_code} para payload: {p}"
        corpo = resp.json()
        assert "erro" in corpo
        assert "detalhes" in corpo

    # Requisicao com JSON malformado
    resp_malformado = cliente.post(
        "/leituras",
        content="{\"chave_invalida\": ",
        headers={"Content-Type": "application/json", "X-Device-Key": "chave-secreta-demo"},
    )
    assert resp_malformado.status_code == 400
    assert "erro" in resp_malformado.json()

    # Requisicao com corpo > 8192 bytes
    padding = "A" * 9000
    corpo_grande = (
        f'{{"dispositivo_id": "esp32-01", "metrica": "temperatura_c", '
        f'"valor": 25.0, "padding": "{padding}"}}'
    )
    resp_grande = cliente.post(
        "/leituras",
        content=corpo_grande,
        headers={"Content-Type": "application/json", "X-Device-Key": "chave-secreta-demo"},
    )
    assert resp_grande.status_code == 400
    assert "8KB" in resp_grande.json()["detalhes"]

    # Requisicao com valor NaN / Inf (enviado em JSON bruto)
    for valor_especial in ("NaN", "Infinity", "-Infinity"):
        payload_especial = (
            f'{{"dispositivo_id": "esp32-01", "metrica": "temperatura_c", '
            f'"valor": {valor_especial}}}'
        )
        resp_esp = cliente.post(
            "/leituras",
            content=payload_especial,
            headers={"Content-Type": "application/json", "X-Device-Key": "chave-secreta-demo"},
        )
        assert resp_esp.status_code == 400

    # Nenhum dos invalidos deve constar no GET ou indicadores
    resp_get = cliente.get("/leituras", headers={"X-Device-Key": "chave-secreta-demo"})
    assert resp_get.status_code == 200
    assert resp_get.json()["total"] == 0

    resp_ind = cliente.get("/leituras/indicadores", headers={"X-Device-Key": "chave-secreta-demo"})
    assert resp_ind.status_code == 200
    ind_data = resp_ind.json()
    assert ind_data["metricas"]["temperatura_c"]["contagem"] == 0
    assert ind_data["metricas"]["temperatura_c"]["media"] is None


def test_autenticacao_chave_dispositivo_fail_closed_e_sem_vazamento(monkeypatch, tmp_path):
    caminho_csv = tmp_path / "runtime" / "leituras.csv"
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(caminho_csv))
    monkeypatch.setenv("DEVICE_KEY", "chave-secreta-12345")

    cliente = TestClient(app)
    payload_valido = {"dispositivo_id": "esp32-01", "metrica": "temperatura_c", "valor": 25.0}

    rotas = [
        ("POST", "/leituras", payload_valido),
        ("GET", "/leituras", None),
        ("GET", "/leituras/indicadores", None),
    ]

    for metodo, rota, payload in rotas:
        # 1. Sem chave de autenticacao
        if metodo == "POST":
            r_sem_chave = cliente.post(rota, json=payload)
        else:
            r_sem_chave = cliente.get(rota)
        assert r_sem_chave.status_code == 401
        assert "chave-secreta-12345" not in r_sem_chave.text

        # 2. Chave incorreta
        headers_errados = {"X-Device-Key": "chave-errada-qualquer"}
        if metodo == "POST":
            r_errada = cliente.post(rota, json=payload, headers=headers_errados)
        else:
            r_errada = cliente.get(rota, headers=headers_errados)
        assert r_errada.status_code == 401
        assert "chave-secreta-12345" not in r_errada.text
        assert "chave-errada-qualquer" not in r_errada.text

    # 3. Authorization: Bearer nao e aceito (somente X-Device-Key)
    resp_bearer = cliente.post(
        "/leituras",
        json=payload_valido,
        headers={"Authorization": "Bearer chave-secreta-12345"},
    )
    assert resp_bearer.status_code == 401
    assert "chave-secreta-12345" not in resp_bearer.text

    # 4. Servidor sem configuracao de DEVICE_KEY (fail-closed, nao pode liberar acesso)
    monkeypatch.delenv("DEVICE_KEY", raising=False)
    resp_sem_config = cliente.get("/leituras", headers={"X-Device-Key": "chave-secreta-12345"})
    assert resp_sem_config.status_code == 401
    assert "chave-secreta-12345" not in resp_sem_config.text


def test_falhas_de_armazenamento_csv_retornam_503(monkeypatch, tmp_path):
    monkeypatch.setenv("DEVICE_KEY", "chave-secreta-demo")
    cliente = TestClient(app)

    # 1. Caminho apontando para um diretorio existente em vez de arquivo (conflito)
    pasta_conflito = tmp_path / "diretorio_conflito"
    pasta_conflito.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(pasta_conflito))

    payload = {"dispositivo_id": "esp32-01", "metrica": "temperatura_c", "valor": 25.0}

    # Falha na gravacao -> 503
    r_post_falha = cliente.post(
        "/leituras",
        json=payload,
        headers={"X-Device-Key": "chave-secreta-demo"},
    )
    assert r_post_falha.status_code == 503
    assert r_post_falha.json()["erro"] == "Servico indisponivel"

    # Falha na leitura -> 503 (nunca fabrica historico vazio)
    r_get_falha = cliente.get("/leituras", headers={"X-Device-Key": "chave-secreta-demo"})
    assert r_get_falha.status_code == 503
    assert r_get_falha.json()["erro"] == "Servico indisponivel"

    # 2. Arquivo CSV com conteudo corrompido (cabecalho invalido ou faltando colunas obrigatorias)
    arquivo_corrompido = tmp_path / "corrompido.csv"
    arquivo_corrompido.write_text("coluna_errada1,coluna_errada2\n123,456\n", encoding="utf-8")
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(arquivo_corrompido))

    r_get_corrompido = cliente.get("/leituras", headers={"X-Device-Key": "chave-secreta-demo"})
    assert r_get_corrompido.status_code == 503
    assert r_get_corrompido.json()["erro"] == "Servico indisponivel"

    r_ind_corrompido = cliente.get(
        "/leituras/indicadores",
        headers={"X-Device-Key": "chave-secreta-demo"},
    )
    assert r_ind_corrompido.status_code == 503
    assert r_ind_corrompido.json()["erro"] == "Servico indisponivel"


def test_concorrencia_escrita_csv_sem_perda_nem_corrupcao(monkeypatch, tmp_path):
    caminho_csv = tmp_path / "runtime" / "leituras_concorrentes.csv"
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(caminho_csv))
    monkeypatch.setenv("DEVICE_KEY", "chave-secreta-demo")
    monkeypatch.setenv("CITIZENTECH_RATE_LIMIT_POR_MINUTO", "200")

    cliente = TestClient(app)
    total_requisicoes = 30
    workers = 6

    def enviar_leitura(indice: int) -> int:
        payload = {
            "evento_id": f"evt-conc-{indice}",
            "dispositivo_id": f"disp-{indice % 5}",
            "metrica": "temperatura_c",
            "valor": 20.0 + (indice % 10),
        }
        resp = cliente.post(
            "/leituras",
            json=payload,
            headers={"X-Device-Key": "chave-secreta-demo"},
        )
        return resp.status_code

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        status_codes = list(executor.map(enviar_leitura, range(total_requisicoes)))

    assert all(code == 201 for code in status_codes)

    # Verifica linhas e unicidade de cabecalho no arquivo CSV
    linhas = caminho_csv.read_text(encoding="utf-8").strip().splitlines()
    assert len(linhas) == total_requisicoes + 1
    assert linhas[0].startswith("evento_id,dispositivo_id")
    assert sum(1 for linha in linhas if linha.startswith("evento_id,dispositivo_id")) == 1

    # Nova leitura por outro cliente confirma todos os 30 registros
    novo_cliente = TestClient(app)
    resp_get = novo_cliente.get(
        "/leituras?page_size=50",
        headers={"X-Device-Key": "chave-secreta-demo"},
    )
    assert resp_get.status_code == 200
    assert resp_get.json()["total"] == total_requisicoes


def test_paginacao_e_filtros_de_sessao_e_indicadores_estatisticos(monkeypatch, tmp_path):
    caminho_csv = tmp_path / "runtime" / "leituras_filtros.csv"
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(caminho_csv))
    monkeypatch.setenv("DEVICE_KEY", "chave-secreta-demo")

    cliente = TestClient(app)

    # Invalida paginacao -> 400
    for params in [
        "?page=0",
        "?page=-1",
        "?page_size=0",
        "?page_size=-5",
        "?page_size=101",
        "?page=abc",
    ]:
        resp_inv = cliente.get(f"/leituras{params}", headers={"X-Device-Key": "chave-secreta-demo"})
        assert resp_inv.status_code == 400
        assert "erro" in resp_inv.json()

    dados_sessao_1 = [
        {
            "dispositivo_id": "d1",
            "sessao_laboratorio_id": "sessao-1",
            "metrica": "temperatura_c",
            "valor": 25.0,
        },
        {
            "dispositivo_id": "d1",
            "sessao_laboratorio_id": "sessao-1",
            "metrica": "temperatura_c",
            "valor": 38.0,
        },
        {
            "dispositivo_id": "d1",
            "sessao_laboratorio_id": "sessao-1",
            "metrica": "temperatura_c",
            "valor": 48.0,
        },
    ]
    dados_sessao_2 = [
        {
            "dispositivo_id": "d2",
            "sessao_laboratorio_id": "sessao-2",
            "metrica": "distancia_cm",
            "valor": 25.0,
        },
    ]

    for p in dados_sessao_1 + dados_sessao_2:
        r = cliente.post("/leituras", json=p, headers={"X-Device-Key": "chave-secreta-demo"})
        assert r.status_code == 201

    # Filtro de sessao no GET /leituras
    r_get_s1 = cliente.get(
        "/leituras?sessao=sessao-1",
        headers={"X-Device-Key": "chave-secreta-demo"},
    )
    assert r_get_s1.status_code == 200
    assert r_get_s1.json()["total"] == 3

    r_get_s2 = cliente.get(
        "/leituras?sessao=sessao-2",
        headers={"X-Device-Key": "chave-secreta-demo"},
    )
    assert r_get_s2.status_code == 200
    assert r_get_s2.json()["total"] == 1

    # Indicadores da sessao 1 para temperatura_c
    r_ind_s1 = cliente.get(
        "/leituras/indicadores?sessao=sessao-1&metrica=temperatura_c",
        headers={"X-Device-Key": "chave-secreta-demo"},
    )
    assert r_ind_s1.status_code == 200
    d_ind_s1 = r_ind_s1.json()
    assert d_ind_s1["contagem"] == 3
    assert d_ind_s1["total_alertas"] == 2  # atencao (38) + critico (48)
    assert d_ind_s1["minimo"] == 25.0
    assert d_ind_s1["maximo"] == 48.0
    assert d_ind_s1["media"] == round((25.0 + 38.0 + 48.0) / 3, 2)

    # Indicadores para sessao inexistente ou vazia: contagem 0 e estatisticas null
    r_ind_vazio = cliente.get(
        "/leituras/indicadores?sessao=sessao-fantasma&metrica=temperatura_c",
        headers={"X-Device-Key": "chave-secreta-demo"},
    )
    assert r_ind_vazio.status_code == 200
    d_ind_vazio = r_ind_vazio.json()
    assert d_ind_vazio["contagem"] == 0
    assert d_ind_vazio["total_alertas"] == 0
    assert d_ind_vazio["media"] is None
    assert d_ind_vazio["maximo"] is None
    assert d_ind_vazio["minimo"] is None


def test_rate_limit_por_dispositivo_com_relogio_injetavel(monkeypatch, tmp_path):
    from citizentech.leituras.limitador import obter_limitador

    caminho_csv = tmp_path / "runtime" / "leituras_rate.csv"
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(caminho_csv))
    monkeypatch.setenv("DEVICE_KEY", "chave-secreta-demo")

    limitador = obter_limitador()
    limitador.limpar()
    limitador.definir_teto(2)

    tempo_simulado = 1000.0
    limitador.definir_relogio(lambda: tempo_simulado)

    cliente = TestClient(app)

    # Dispositivo A faz 2 requisicoes (atinge o teto)
    p_a = {"dispositivo_id": "esp32-alpha", "metrica": "temperatura_c", "valor": 25.0}
    r1 = cliente.post("/leituras", json=p_a, headers={"X-Device-Key": "chave-secreta-demo"})
    assert r1.status_code == 201
    r2 = cliente.post("/leituras", json=p_a, headers={"X-Device-Key": "chave-secreta-demo"})
    assert r2.status_code == 201

    # 3a requisicao do Dispositivo A deve ser bloqueada com 429
    r3 = cliente.post("/leituras", json=p_a, headers={"X-Device-Key": "chave-secreta-demo"})
    assert r3.status_code == 429
    assert r3.json()["erro"] == "Muitas requisicoes"

    # Dispositivo B nao foi bloqueado indevidamente
    p_b = {"dispositivo_id": "esp32-beta", "metrica": "temperatura_c", "valor": 25.0}
    rb = cliente.post("/leituras", json=p_b, headers={"X-Device-Key": "chave-secreta-demo"})
    assert rb.status_code == 201

    # Avanca o relogio em 61 segundos (expira janela de 1 minuto)
    tempo_simulado = 1061.0
    r_recuperado = cliente.post(
        "/leituras",
        json=p_a,
        headers={"X-Device-Key": "chave-secreta-demo"},
    )
    assert r_recuperado.status_code == 201

    # Restaura o limitador
    limitador.limpar()
    limitador.definir_teto(None)
    import time

    limitador.definir_relogio(time.time)


def test_stream_sem_content_length_aborta_ao_exceder_sem_consumir_resto(monkeypatch, tmp_path):
    import asyncio

    caminho_csv = tmp_path / "runtime" / "leituras_stream.csv"
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(caminho_csv))
    monkeypatch.setenv("DEVICE_KEY", "chave-secreta-demo")

    chamadas_receive = 0

    async def executar_teste_asgi():
        nonlocal chamadas_receive
        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "POST",
            "path": "/leituras",
            "raw_path": b"/leituras",
            "query_string": b"",
            "headers": [
                (b"host", b"testserver"),
                (b"x-device-key", b"chave-secreta-demo"),
                (b"content-type", b"application/json"),
            ],
        }

        async def receive():
            nonlocal chamadas_receive
            chamadas_receive += 1
            if chamadas_receive == 1:
                return {"type": "http.request", "body": b"A" * 5000, "more_body": True}
            if chamadas_receive == 2:
                # 5000 + 5000 = 10000 bytes > 8192 bytes (limite de 8KB)
                return {"type": "http.request", "body": b"A" * 5000, "more_body": True}
            # Terceiro chunk que JAMAIS deve ser consumido pelo servidor
            return {"type": "http.request", "body": b"A" * 5000, "more_body": False}

        mensagens_resposta = []

        async def send(msg):
            mensagens_resposta.append(msg)

        await app(scope, receive, send)
        return mensagens_resposta

    mensagens = asyncio.run(executar_teste_asgi())
    status_msg = [m for m in mensagens if m["type"] == "http.response.start"][0]
    corpo_msg = [m for m in mensagens if m["type"] == "http.response.body"][0]

    assert status_msg["status"] == 400
    assert b"8KB" in corpo_msg["body"]
    # Garante que abortou no segundo chunk e nao consumiu o resto do stream
    assert chamadas_receive == 2


def test_falha_fsync_faz_rollback_sem_perder_dados_preexistentes(monkeypatch, tmp_path):
    import os

    caminho_csv = tmp_path / "runtime" / "leituras_fsync.csv"
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(caminho_csv))
    monkeypatch.setenv("DEVICE_KEY", "chave-secreta-demo")

    cliente = TestClient(app)

    # 1. Salva um registro valido inicial com sucesso
    p1 = {"dispositivo_id": "esp32-01", "metrica": "temperatura_c", "valor": 25.0}
    r1 = cliente.post("/leituras", json=p1, headers={"X-Device-Key": "chave-secreta-demo"})
    assert r1.status_code == 201
    tamanho_antes = caminho_csv.stat().st_size

    # 2. Injeta falha localizada exclusivamente no os.fsync durante o proximo post
    fsync_original = os.fsync

    def fsync_falho(fd):
        raise OSError("Falha simulada de disco no fsync")

    monkeypatch.setattr(os, "fsync", fsync_falho)

    p2 = {"dispositivo_id": "esp32-02", "metrica": "temperatura_c", "valor": 38.0}
    r2 = cliente.post("/leituras", json=p2, headers={"X-Device-Key": "chave-secreta-demo"})
    assert r2.status_code == 503
    assert r2.json()["erro"] == "Servico indisponivel"

    # Restaura fsync especificamente mantendo as demais variaveis de ambiente
    monkeypatch.setattr(os, "fsync", fsync_original)

    # O arquivo deve ter exatamente o mesmo tamanho e manter o registro preexistente
    assert caminho_csv.stat().st_size == tamanho_antes
    r_get = cliente.get("/leituras", headers={"X-Device-Key": "chave-secreta-demo"})
    assert r_get.status_code == 200
    assert r_get.json()["total"] == 1
    assert r_get.json()["itens"][0]["dispositivo_id"] == "esp32-01"


def test_csv_com_fixtures_corrompidas_retorna_503_na_api_publica(monkeypatch, tmp_path):
    caminho_csv = tmp_path / "runtime" / "leituras_corruptas.csv"
    caminho_csv.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(caminho_csv))
    monkeypatch.setenv("DEVICE_KEY", "chave-secreta-demo")

    cliente = TestClient(app)
    cabecalho_ok = (
        "evento_id,dispositivo_id,sessao_laboratorio_id,ciclo_id,tipo_dispositivo,"
        "metrica,unidade,valor,risco,alerta,estado,medido_em,criado_em\n"
    )

    ts_ok = "2026-11-12T14:00:00Z"

    def _linha(
        val: str,
        met: str = "temperatura_c",
        risco: str = "normal",
        alerta: str = "False",
        dt1: str = ts_ok,
        dt2: str = ts_ok,
        extra: str = "",
    ) -> str:
        sufixo = f",{extra}\n" if extra else "\n"
        corpo = f"e1,d1,s1,c1,esp32,{met},C,{val},{risco},{alerta},pendente_nuvem"
        return f"{corpo},{dt1},{dt2}{sufixo}"

    cenarios_corrompidos = [
        # NaN em valor
        cabecalho_ok + _linha("NaN"),
        # Inf em valor
        cabecalho_ok + _linha("Infinity"),
        # Metrica desconhecida
        cabecalho_ok + _linha("25.0", met="metrica_fantasma"),
        # Risco incoerente com o valor (25.0 C deveria ser normal, mas esta marcado como critico)
        cabecalho_ok + _linha("25.0", risco="critico", alerta="True"),
        # Alerta incoerente com o risco
        cabecalho_ok + _linha("25.0", risco="normal", alerta="True"),
        # Timestamp invalido
        cabecalho_ok + _linha("25.0", dt1="data_invalida"),
        # Colunas extras
        cabecalho_ok.strip() + ",coluna_extra\n" + _linha("25.0", extra="extra"),
        # Linha final truncada (sem quebra de linha)
        cabecalho_ok + _linha("25.0").rstrip("\r\n"),
    ]

    for csv_invalido in cenarios_corrompidos:
        caminho_csv.write_text(csv_invalido, encoding="utf-8")
        conteudo_original = caminho_csv.read_text(encoding="utf-8")

        # GET /leituras deve retornar 503 sem serializar NaN nem 500
        r_get = cliente.get("/leituras", headers={"X-Device-Key": "chave-secreta-demo"})
        assert r_get.status_code == 503
        assert r_get.json()["erro"] == "Servico indisponivel"

        # POST /leituras deve retornar 503 e NAO modificar os bytes
        r_post = cliente.post(
            "/leituras",
            json={"dispositivo_id": "d1", "metrica": "temperatura_c", "valor": 25.0},
            headers={"X-Device-Key": "chave-secreta-demo"},
        )
        assert r_post.status_code == 503
        assert r_post.json()["erro"] == "Servico indisponivel"
        assert caminho_csv.read_text(encoding="utf-8") == conteudo_original


def test_indicadores_com_valores_extremos_calcula_media_estavel_sem_overflow(monkeypatch, tmp_path):
    caminho_csv = tmp_path / "runtime" / "leituras_extremos.csv"
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(caminho_csv))
    monkeypatch.setenv("DEVICE_KEY", "chave-secreta-demo")

    cliente = TestClient(app)

    # Dois valores finitos muito proximos de 1e308 (soma convencional resultaria em inf)
    p1 = {"dispositivo_id": "esp32-01", "metrica": "temperatura_c", "valor": 1e308}
    p2 = {"dispositivo_id": "esp32-02", "metrica": "temperatura_c", "valor": 1e308}

    r1 = cliente.post("/leituras", json=p1, headers={"X-Device-Key": "chave-secreta-demo"})
    assert r1.status_code == 201

    r2 = cliente.post("/leituras", json=p2, headers={"X-Device-Key": "chave-secreta-demo"})
    assert r2.status_code == 201

    r_ind = cliente.get(
        "/leituras/indicadores?metrica=temperatura_c",
        headers={"X-Device-Key": "chave-secreta-demo"},
    )
    assert r_ind.status_code == 200
    dados = r_ind.json()
    assert dados["contagem"] == 2
    assert dados["media"] == 1e308
    assert dados["maximo"] == 1e308
    assert dados["minimo"] == 1e308

