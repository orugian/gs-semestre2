"""Testes das rotas de avaliacao e exercicio diagnostico (S13)."""

import logging
import os
import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient

from citizentech.curriculo.repositorio import obter_cliente_mongo
from citizentech.llm.cliente import ClienteLLM, ErroLLM, RespostaLLM, obter_cliente_llm
from citizentech.main import app


def _criar_usuario_e_sessao(cliente: TestClient, sufixo: str) -> dict[str, Any]:
    email = f"user_{sufixo}_{uuid.uuid4().hex[:6]}@example.test"
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


def _varrer_chaves_recursivo(dado: Any, chaves_proibidas: set[str]) -> list[str]:
    encontradas = []
    if isinstance(dado, dict):
        for k, v in dado.items():
            if k in chaves_proibidas:
                encontradas.append(k)
            encontradas.extend(_varrer_chaves_recursivo(v, chaves_proibidas))
    elif isinstance(dado, list):
        for item in dado:
            encontradas.extend(_varrer_chaves_recursivo(item, chaves_proibidas))
    return encontradas


@pytest.mark.oracle
def test_get_exercicio_nao_vaza_gabarito():
    """Valida que GET /destinos/{id}/exercicio nao vaza gabarito, justificativa ou requisitos."""
    cliente = TestClient(app, base_url="https://testserver")
    _criar_usuario_e_sessao(cliente, "s13_get")

    resp = cliente.get("/destinos/analista_processos/exercicio")
    assert resp.status_code == 200
    dados = resp.json()

    chaves_proibidas = {"gabarito", "justificativa", "requisitos_avaliados"}
    vazadas = _varrer_chaves_recursivo(dados, chaves_proibidas)
    assert vazadas == [], f"Chaves proibidas encontradas na resposta: {vazadas}"

    assert dados["destino_id"] == "analista_processos"
    assert "exercicio_id" in dados
    assert "versao" in dados
    assert "cenario" in dados

    questoes = dados["questoes_objetivas"]
    assert len(questoes) == 4
    for q in questoes:
        assert "id" in q
        assert "enunciado" in q
        assert "alternativas" in q
        assert "gabarito" not in q
        assert "justificativa" not in q
        assert "requisitos_avaliados" not in q

    aberta = dados["questao_aberta"]
    assert "id" in aberta
    assert "enunciado" in aberta
    criterios = aberta["criterios"]
    assert len(criterios) == 3
    for c in criterios:
        assert "id" in c
        assert "descricao" in c
        assert "ancoras" in c
        assert set(c["ancoras"].keys()) == {"0", "1", "2"}

    assert "politica" in dados
    assert "tentativas_restantes_24h" in dados


@pytest.mark.oracle
def test_get_exercicio_destino_inexistente_retorna_404():
    """Valida 404 para destino nao cadastrado ou nao aprovado."""
    cliente = TestClient(app, base_url="https://testserver")
    _criar_usuario_e_sessao(cliente, "s13_404")

    resp = cliente.get("/destinos/destino_inventado_xyz/exercicio")
    assert resp.status_code == 404
    assert "erro" in resp.json()


def test_get_exercicio_sem_cookie_retorna_401():
    """Valida 401 ao chamar GET /destinos/{id}/exercicio sem autenticacao."""
    cliente = TestClient(app, base_url="https://testserver")
    resp = cliente.get("/destinos/analista_processos/exercicio")
    assert resp.status_code == 401


@pytest.mark.oracle
@pytest.mark.mongo
def test_llm_fora_resulta_parcial_e_objetiva_preservada():
    """Valida que falha na LLM produz resultado parcial preservando a correcao objetiva."""
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "s13_llm_fora")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}

    cliente.post(
        "/me/consentimentos",
        json={"finalidade": "curriculo_llm"},
        headers=headers_csrf,
    )

    class FakeClienteLLMFalha(ClienteLLM):
        def gerar_json(self, mensagens, schema, nome_schema, validar=None):
            raise ErroLLM("Simulacao de LLM indisponivel")

    app.dependency_overrides[obter_cliente_llm] = lambda: FakeClienteLLMFalha()

    try:
        token = uuid.uuid4().hex[:8]
        payload = {
            "destino_id": "analista_processos",
            "exercicio_id": "ex_analista_processos_01",
            "respostas_objetivas": {"q1": "C", "q2": "D", "q3": "A", "q4": "B"},
            "resposta_aberta": (
                f"Minha proposta TO-BE {token} define fluxo claro de triagem e expedicao. "
                "Mitigamos o risco operacional com contingencia manual e leitor reserva. "
                "Adotamos os KPIs Lead Time de Expedicao e OTIF com meta de 98%."
            ),
        }

        resp = cliente.post("/me/tentativas", json=payload, headers=headers_csrf)
        assert resp.status_code == 201
        corpo = resp.json()

        assert corpo["objetiva"]["acertos"] == 4
        assert corpo["objetiva"]["total"] == 4
        assert corpo["objetiva"]["nota"] == 1.0
        assert corpo["aberta"]["status"] == "parcial"
        assert corpo["aberta"]["nota"] is None
        assert corpo["nota_final"] is None
        assert corpo["resultado"] == "parcial"
        assert len(corpo["requisitos_avaliados"]) > 0
    finally:
        app.dependency_overrides.pop(obter_cliente_llm, None)


@pytest.mark.oracle
@pytest.mark.mongo
def test_avaliacao_sucesso_completo_demonstrada():
    """Valida fluxo de avaliacao bem-sucedida com resultado demonstrada (50/50)."""
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "s13_sucesso")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}

    cliente.post(
        "/me/consentimentos",
        json={"finalidade": "curriculo_llm"},
        headers=headers_csrf,
    )

    esquema_recebido = {}

    class FakeClienteLLMSucesso(ClienteLLM):
        def gerar_json(self, mensagens, schema, nome_schema, validar=None):
            nonlocal esquema_recebido
            esquema_recebido = schema
            dados = {
                "criterios": [
                    {
                        "id": "crit_redesenho_fluxo",
                        "nivel": 2,
                        "justificativa": "Excelente fluxo TO-BE com raias bem definidas.",
                        "trecho_resposta": "define fluxo claro de triagem",
                    },
                    {
                        "id": "crit_gestao_riscos",
                        "nivel": 2,
                        "justificativa": "Salvaguardas operacionais muito bem delimitadas.",
                        "trecho_resposta": "mitigamos o risco operacional com contingencia manual",
                    },
                    {
                        "id": "crit_indicadores_kpis",
                        "nivel": 2,
                        "justificativa": "KPIs claros e acionaveis com metas percentuais.",
                        "trecho_resposta": "adotamos os kpis lead time de expedicao e otif",
                    },
                ]
            }
            if validar:
                validar(dados)
            return RespostaLLM(
                dados=dados,
                modelo="fake-eval-model",
                tentativas=1,
                uso={"total_tokens": 150},
            )

    app.dependency_overrides[obter_cliente_llm] = lambda: FakeClienteLLMSucesso()

    try:
        token = uuid.uuid4().hex[:8]
        payload = {
            "destino_id": "analista_processos",
            "exercicio_id": "ex_analista_processos_01",
            "respostas_objetivas": {"q1": "C", "q2": "D", "q3": "A", "q4": "B"},
            "resposta_aberta": (
                f"Minha proposta TO-BE {token} define fluxo claro de triagem e expedicao. "
                "Mitigamos o risco operacional com contingencia manual e leitor reserva. "
                "Adotamos os KPIs Lead Time de Expedicao e OTIF com meta de 98%."
            ),
        }

        resp = cliente.post("/me/tentativas", json=payload, headers=headers_csrf)
        assert resp.status_code == 201
        corpo = resp.json()

        assert corpo["objetiva"]["nota"] == 1.0
        assert corpo["aberta"]["status"] == "avaliada"
        assert corpo["aberta"]["nota"] == 1.0
        assert corpo["aberta"]["em_cache"] is False
        assert corpo["aberta"]["modelo"] == "fake-eval-model"
        assert corpo["nota_final"] == 1.0
        assert corpo["resultado"] == "demonstrada"

        # Verifica que o schema continha o enum dos IDs de rubrica
        criterios_enum = esquema_recebido["properties"]["criterios"]["items"]["properties"]["id"][
            "enum"
        ]
        assert set(criterios_enum) == {
            "crit_redesenho_fluxo",
            "crit_gestao_riscos",
            "crit_indicadores_kpis",
        }
    finally:
        app.dependency_overrides.pop(obter_cliente_llm, None)


@pytest.mark.oracle
@pytest.mark.mongo
def test_cache_por_hash_espacos_colapsados():
    """Valida R23: mesma resposta aberta com espacos diferentes reutiliza cache na 2a tentativa."""
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "s13_cache")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}

    cliente.post(
        "/me/consentimentos",
        json={"finalidade": "curriculo_llm"},
        headers=headers_csrf,
    )

    chamadas_llm = 0

    class FakeClienteContador(ClienteLLM):
        def gerar_json(self, mensagens, schema, nome_schema, validar=None):
            nonlocal chamadas_llm
            chamadas_llm += 1
            dados = {
                "criterios": [
                    {
                        "id": "crit_redesenho_fluxo",
                        "nivel": 1,
                        "justificativa": "Fluxo regular.",
                        "trecho_resposta": "operacional com novas raias",
                    },
                    {
                        "id": "crit_gestao_riscos",
                        "nivel": 1,
                        "justificativa": "Riscos medianos.",
                        "trecho_resposta": "analise dos principais riscos",
                    },
                    {
                        "id": "crit_indicadores_kpis",
                        "nivel": 1,
                        "justificativa": "KPIs basicos.",
                        "trecho_resposta": "indicadores de tempo de ciclo",
                    },
                ]
            }
            if validar:
                validar(dados)
            return RespostaLLM(dados=dados, modelo="fake-model", tentativas=1, uso=None)

    app.dependency_overrides[obter_cliente_llm] = lambda: FakeClienteContador()

    try:
        token = uuid.uuid4().hex[:8]
        # 1a tentativa: texto base
        texto_base = (
            f"Proposta estruturada {token} de fluxo operacional com novas raias. "
            "Realizamos analise dos principais riscos operacionais de transicao. "
            "Acompanhamos indicadores de tempo de ciclo."
        )
        payload1 = {
            "destino_id": "analista_processos",
            "exercicio_id": "ex_analista_processos_01",
            "respostas_objetivas": {"q1": "C", "q2": "D", "q3": "A", "q4": "B"},
            "resposta_aberta": texto_base,
        }
        resp1 = cliente.post("/me/tentativas", json=payload1, headers=headers_csrf)
        assert resp1.status_code == 201
        assert resp1.json()["aberta"]["em_cache"] is False
        assert chamadas_llm == 1

        # 2a tentativa: mesmo texto com quebras e multiplos espacos
        texto_espacado = (
            f"   Proposta   estruturada   {token}   de fluxo   operacional com novas raias. \n\n"
            "Realizamos  analise  dos principais   riscos operacionais de transicao. \n"
            "Acompanhamos    indicadores   de tempo   de ciclo.   "
        )
        payload2 = {
            "destino_id": "analista_processos",
            "exercicio_id": "ex_analista_processos_01",
            "respostas_objetivas": {"q1": "C", "q2": "D", "q3": "A", "q4": "B"},
            "resposta_aberta": texto_espacado,
        }
        resp2 = cliente.post("/me/tentativas", json=payload2, headers=headers_csrf)
        assert resp2.status_code == 201
        assert resp2.json()["aberta"]["em_cache"] is True
        assert chamadas_llm == 1  # Fake NAO foi chamado de novo!
    finally:
        app.dependency_overrides.pop(obter_cliente_llm, None)


@pytest.mark.oracle
@pytest.mark.mongo
def test_tentativa_parcial_nao_entra_no_cache():
    """Valida que avaliacao com falha da LLM (parcial) nao entra no cache."""
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "s13_nocache_parcial")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}

    cliente.post(
        "/me/consentimentos",
        json={"finalidade": "curriculo_llm"},
        headers=headers_csrf,
    )

    deve_falhar = True

    class FakeClienteAlternado(ClienteLLM):
        def gerar_json(self, mensagens, schema, nome_schema, validar=None):
            if deve_falhar:
                raise ErroLLM("Falha temporaria")
            dados = {
                "criterios": [
                    {
                        "id": "crit_redesenho_fluxo",
                        "nivel": 2,
                        "justificativa": "ok",
                        "trecho_resposta": "para testar parcial sem cache",
                    },
                    {
                        "id": "crit_gestao_riscos",
                        "nivel": 2,
                        "justificativa": "ok",
                        "trecho_resposta": "para testar parcial sem cache",
                    },
                    {
                        "id": "crit_indicadores_kpis",
                        "nivel": 2,
                        "justificativa": "ok",
                        "trecho_resposta": "para testar parcial sem cache",
                    },
                ]
            }
            if validar:
                validar(dados)
            return RespostaLLM(dados=dados, modelo="fake-model", tentativas=1, uso=None)

    app.dependency_overrides[obter_cliente_llm] = lambda: FakeClienteAlternado()

    try:
        token = uuid.uuid4().hex[:8]
        texto = f"Texto unico {token} para testar parcial sem cache no banco de dados."
        payload = {
            "destino_id": "analista_processos",
            "exercicio_id": "ex_analista_processos_01",
            "respostas_objetivas": {"q1": "C", "q2": "D", "q3": "A", "q4": "B"},
            "resposta_aberta": texto,
        }

        # 1a tentativa: falha
        resp1 = cliente.post("/me/tentativas", json=payload, headers=headers_csrf)
        assert resp1.status_code == 201
        assert resp1.json()["aberta"]["status"] == "parcial"

        # 2a tentativa: servico restabelecido -> chama LLM com sucesso (nao veio do cache)
        deve_falhar = False
        resp2 = cliente.post("/me/tentativas", json=payload, headers=headers_csrf)
        assert resp2.status_code == 201
        assert resp2.json()["aberta"]["status"] == "avaliada"
        assert resp2.json()["aberta"]["em_cache"] is False
    finally:
        app.dependency_overrides.pop(obter_cliente_llm, None)


@pytest.mark.oracle
@pytest.mark.mongo
def test_limite_tentativas_24h_quarta_retorna_429():
    """Valida D21: maximo 3 tentativas em 24h por exercicio; a 4a e 429 sem chamar LLM."""
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "s13_limite")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}

    cliente.post(
        "/me/consentimentos",
        json={"finalidade": "curriculo_llm"},
        headers=headers_csrf,
    )

    chamadas_llm = 0

    class FakeClienteSimples(ClienteLLM):
        def gerar_json(self, mensagens, schema, nome_schema, validar=None):
            nonlocal chamadas_llm
            chamadas_llm += 1
            dados = {
                "criterios": [
                    {
                        "id": "crit_redesenho_fluxo",
                        "nivel": 1,
                        "justificativa": "ok",
                        "trecho_resposta": "resposta para teste de limite",
                    },
                    {
                        "id": "crit_gestao_riscos",
                        "nivel": 1,
                        "justificativa": "ok",
                        "trecho_resposta": "resposta para teste de limite",
                    },
                    {
                        "id": "crit_indicadores_kpis",
                        "nivel": 1,
                        "justificativa": "ok",
                        "trecho_resposta": "resposta para teste de limite",
                    },
                ]
            }
            if validar:
                try:
                    validar(dados)
                except ValueError as err:
                    raise ErroLLM(str(err)) from err
            return RespostaLLM(dados=dados, modelo="fake", tentativas=1, uso=None)

    app.dependency_overrides[obter_cliente_llm] = lambda: FakeClienteSimples()

    try:
        token = uuid.uuid4().hex[:8]
        payload = {
            "destino_id": "analista_processos",
            "exercicio_id": "ex_analista_processos_01",
            "respostas_objetivas": {"q1": "C", "q2": "D", "q3": "A", "q4": "B"},
            "resposta_aberta": f"Resposta para teste de limite {token} com texto unico.",
        }

        # 1a, 2a e 3a tentativa devem responder 201
        for i in range(3):
            payload["resposta_aberta"] = (
                f"Resposta para teste de limite {token} com texto unico {i}."
            )
            r = cliente.post("/me/tentativas", json=payload, headers=headers_csrf)
            assert r.status_code == 201
            assert r.json()["tentativas_restantes_24h"] == (2 - i)

        assert chamadas_llm == 3

        # 4a tentativa: 429 Too Many Requests
        payload["resposta_aberta"] = f"Tentativa quatro {token} que deve ser barrada imediatamente."
        r4 = cliente.post("/me/tentativas", json=payload, headers=headers_csrf)
        assert r4.status_code == 429
        assert "Limite" in r4.json()["erro"]
        assert chamadas_llm == 3  # Fake LLM NAO foi chamado!

        # Tentativa em OUTRO destino/exercicio nao e bloqueada
        payload_outro = {
            "destino_id": "analista_dados_bi",
            "exercicio_id": "ex_analista_dados_bi_01",
            "respostas_objetivas": {"q1": "A", "q2": "B", "q3": "C", "q4": "D"},
            "resposta_aberta": (
                "Estruturacao de pipeline com camadas bronze e silver, "
                "garantindo qualidade com testes de chaves nulas e SLA de ingestao."
            ),
        }
        r_outro = cliente.post("/me/tentativas", json=payload_outro, headers=headers_csrf)
        # Fake vai falhar na validacao porque a rubrica de analista_dados_bi
        # tem outros criterios, gerando resposta parcial 201
        assert r_outro.status_code == 201
    finally:
        app.dependency_overrides.pop(obter_cliente_llm, None)


@pytest.mark.oracle
@pytest.mark.mongo
def test_pii_redigido_antes_de_ir_a_llm_e_antes_de_gravar_mongo():
    """Valida D22: dados pessoais (PII) sao redigidos antes do prompt e da gravacao."""
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "s13_pii")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}

    cliente.post(
        "/me/consentimentos",
        json={"finalidade": "curriculo_llm"},
        headers=headers_csrf,
    )

    prompt_recebido = ""

    class FakeClientePII(ClienteLLM):
        def gerar_json(self, mensagens, schema, nome_schema, validar=None):
            nonlocal prompt_recebido
            prompt_recebido = mensagens[1]["content"]
            dados = {
                "criterios": [
                    {
                        "id": "crit_redesenho_fluxo",
                        "nivel": 1,
                        "justificativa": "ok",
                        "trecho_resposta": "proposta estruturada de fluxo to-be",
                    },
                    {
                        "id": "crit_gestao_riscos",
                        "nivel": 1,
                        "justificativa": "ok",
                        "trecho_resposta": "proposta estruturada de fluxo to-be",
                    },
                    {
                        "id": "crit_indicadores_kpis",
                        "nivel": 1,
                        "justificativa": "ok",
                        "trecho_resposta": "proposta estruturada de fluxo to-be",
                    },
                ]
            }
            if validar:
                try:
                    validar(dados)
                except ValueError as err:
                    raise ErroLLM(str(err)) from err
            return RespostaLLM(dados=dados, modelo="fake", tentativas=1, uso=None)

    app.dependency_overrides[obter_cliente_llm] = lambda: FakeClientePII()

    email_pii = "joao.silva@hospitalteste.org"
    telefone_pii = "(11) 98765-4321"

    try:
        token = uuid.uuid4().hex[:8]
        payload = {
            "destino_id": "analista_processos",
            "exercicio_id": "ex_analista_processos_01",
            "respostas_objetivas": {"q1": "C", "q2": "D", "q3": "A", "q4": "B"},
            "resposta_aberta": (
                f"Contato para duvidas: {email_pii} ou cel {telefone_pii} {token}. "
                "Proposta estruturada de fluxo TO-BE com contingencia e KPIs."
            ),
        }

        resp = cliente.post("/me/tentativas", json=payload, headers=headers_csrf)
        assert resp.status_code == 201
        tentativa_id = resp.json()["tentativa_id"]

        # Prompt enviado a LLM nao contem o e-mail nem telefone
        assert email_pii not in prompt_recebido
        assert telefone_pii not in prompt_recebido
        assert "[EMAIL]" in prompt_recebido
        assert "[TELEFONE]" in prompt_recebido

        # Mongo respostas_abertas nao contem o e-mail nem telefone
        mongo = obter_cliente_mongo()
        db_nome = os.environ.get("MONGODB_DB")
        doc = mongo[db_nome]["respostas_abertas"].find_one({"_id": tentativa_id})
        assert doc is not None
        assert email_pii not in doc["texto_redigido"]
        assert telefone_pii not in doc["texto_redigido"]
        assert "[EMAIL]" in doc["texto_redigido"]
    finally:
        app.dependency_overrides.pop(obter_cliente_llm, None)


@pytest.mark.oracle
def test_sem_consentimento_curriculo_llm_retorna_403():
    """Valida que ausencia de consentimento curriculo_llm resulta em 403 sem chamar LLM."""
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "s13_sem_consent")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}

    payload = {
        "destino_id": "analista_processos",
        "exercicio_id": "ex_analista_processos_01",
        "respostas_objetivas": {"q1": "C", "q2": "D", "q3": "A", "q4": "B"},
        "resposta_aberta": "Proposta de solucao completa com mais de 20 caracteres.",
    }

    resp = cliente.post("/me/tentativas", json=payload, headers=headers_csrf)
    assert resp.status_code == 403
    assert "curriculo_llm" in resp.json()["detalhes"]


def test_sem_cookie_401_e_sem_csrf_403():
    """Valida seguranca de cookie e token CSRF nas rotas /me/tentativas."""
    cliente = TestClient(app, base_url="https://testserver")

    # Sem cookie
    resp1 = cliente.post("/me/tentativas", json={})
    assert resp1.status_code == 401

    # Com cookie mas sem CSRF
    _criar_usuario_e_sessao(cliente, "s13_csrf")
    resp2 = cliente.post("/me/tentativas", json={})  # Sem header X-CSRF-Token
    assert resp2.status_code == 403


@pytest.mark.oracle
def test_validacoes_entrada_400():
    """Valida todas as regras de esquema e negocio que devem responder 400."""
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "s13_val")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}

    cliente.post(
        "/me/consentimentos",
        json={"finalidade": "curriculo_llm"},
        headers=headers_csrf,
    )

    base_payload = {
        "destino_id": "analista_processos",
        "exercicio_id": "ex_analista_processos_01",
        "respostas_objetivas": {"q1": "C", "q2": "D", "q3": "A", "q4": "B"},
        "resposta_aberta": "Resposta valida com tamanho suficiente para passar no schema.",
    }

    # 1. Alternativa invalida
    p1 = dict(base_payload)
    p1["respostas_objetivas"] = {"q1": "Z", "q2": "D", "q3": "A", "q4": "B"}
    assert cliente.post("/me/tentativas", json=p1, headers=headers_csrf).status_code == 400

    # 2. Questao faltando
    p2 = dict(base_payload)
    p2["respostas_objetivas"] = {"q1": "C", "q2": "D", "q3": "A"}
    assert cliente.post("/me/tentativas", json=p2, headers=headers_csrf).status_code == 400

    # 3. Questao extra
    p3 = dict(base_payload)
    p3["respostas_objetivas"] = {"q1": "C", "q2": "D", "q3": "A", "q4": "B", "q_extra": "A"}
    assert cliente.post("/me/tentativas", json=p3, headers=headers_csrf).status_code == 400

    # 4. exercicio_id divergente
    p4 = dict(base_payload)
    p4["exercicio_id"] = "ex_divergente_00"
    assert cliente.post("/me/tentativas", json=p4, headers=headers_csrf).status_code == 400

    # 5. Resposta aberta com 19 caracteres
    p5 = dict(base_payload)
    p5["resposta_aberta"] = "1234567890123456789"  # 19 chars
    assert cliente.post("/me/tentativas", json=p5, headers=headers_csrf).status_code == 400

    # 6. Resposta aberta com 4001 caracteres
    p6 = dict(base_payload)
    p6["resposta_aberta"] = "A" * 4001
    assert cliente.post("/me/tentativas", json=p6, headers=headers_csrf).status_code == 400


@pytest.mark.oracle
@pytest.mark.mongo
def test_discordo_fluxo_completo():
    """Valida registro de contestacao (T08, LGPD art. 20), redacao PII, 409 e 404."""
    cliente = TestClient(app, base_url="https://testserver")
    usuario1 = _criar_usuario_e_sessao(cliente, "s13_disc1")
    headers_csrf1 = {"X-CSRF-Token": usuario1["csrf_token"]}

    cliente.post(
        "/me/consentimentos",
        json={"finalidade": "curriculo_llm"},
        headers=headers_csrf1,
    )

    class FakeLLM(ClienteLLM):
        def gerar_json(self, mensagens, schema, nome_schema, validar=None):
            raise ErroLLM("Falha proposital para teste")

    app.dependency_overrides[obter_cliente_llm] = lambda: FakeLLM()

    try:
        # Cria tentativa
        payload = {
            "destino_id": "analista_processos",
            "exercicio_id": "ex_analista_processos_01",
            "respostas_objetivas": {"q1": "C", "q2": "D", "q3": "A", "q4": "B"},
            "resposta_aberta": "Proposta de solucao com texto suficiente para teste de discordo.",
        }
        r_tentativa = cliente.post("/me/tentativas", json=payload, headers=headers_csrf1)
        assert r_tentativa.status_code == 201
        tentativa_id = r_tentativa.json()["tentativa_id"]

        # Motivo muito curto (<10) -> 400
        r_curto = cliente.post(
            f"/me/tentativas/{tentativa_id}/discordo",
            json={"motivo": "Curto"},
            headers=headers_csrf1,
        )
        assert r_curto.status_code == 400

        # Motivo muito longo (>1000) -> 400
        r_longo = cliente.post(
            f"/me/tentativas/{tentativa_id}/discordo",
            json={"motivo": "X" * 1001},
            headers=headers_csrf1,
        )
        assert r_longo.status_code == 400

        # Outro usuario tentando contestar tentativa de usuario1 -> 404 (T14)
        cliente2 = TestClient(app, base_url="https://testserver")
        usuario2 = _criar_usuario_e_sessao(cliente2, "s13_disc2")
        headers_csrf2 = {"X-CSRF-Token": usuario2["csrf_token"]}
        r_outro = cliente2.post(
            f"/me/tentativas/{tentativa_id}/discordo",
            json={"motivo": "Nao concordo com a correcao feita."},
            headers=headers_csrf2,
        )
        assert r_outro.status_code == 404

        # Registra com sucesso contendo e-mail que deve ser redigido
        motivo_com_email = (
            "Discordo pois enviei a solucao detalhada para coordenador@empresa.com em anexo."
        )
        r_disc = cliente.post(
            f"/me/tentativas/{tentativa_id}/discordo",
            json={"motivo": motivo_com_email},
            headers=headers_csrf1,
        )
        assert r_disc.status_code == 200
        corpo_disc = r_disc.json()
        assert corpo_disc["tentativa_id"] == tentativa_id
        assert corpo_disc["status_contestacao"] == "registrada"
        assert corpo_disc["discordo_em"] is not None
        assert "coordenador@empresa.com" not in corpo_disc["motivo"]
        assert "[EMAIL]" in corpo_disc["motivo"]

        # Segunda contestacao para a mesma tentativa -> 409 Conflict
        r_dup = cliente.post(
            f"/me/tentativas/{tentativa_id}/discordo",
            json={"motivo": "Segunda tentativa de contestacao."},
            headers=headers_csrf1,
        )
        assert r_dup.status_code == 409
        # Nota e resultado inalterados depois da contestação (RV-S13-07)
        r_lista = cliente.get("/me/tentativas?destino_id=analista_processos")
        assert r_lista.status_code == 200
        item = next(i for i in r_lista.json()["itens"] if i["tentativa_id"] == tentativa_id)
        corpo_t = r_tentativa.json()
        assert item["resultado"] == corpo_t["resultado"]
        assert item["nota_final"] == corpo_t["nota_final"]
    finally:
        app.dependency_overrides.pop(obter_cliente_llm, None)


@pytest.mark.oracle
@pytest.mark.mongo
def test_listar_tentativas_ultima_e_melhor_com_tres_tentativas():
    """Valida GET /me/tentativas com calculo correto de ultima e melhor entre tres tentativas."""
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "s13_listar")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}

    cliente.post(
        "/me/consentimentos",
        json={"finalidade": "curriculo_llm"},
        headers=headers_csrf,
    )

    nota_llm_simulada = 0

    class FakeLLMVar(ClienteLLM):
        def gerar_json(self, mensagens, schema, nome_schema, validar=None):
            dados = {
                "criterios": [
                    {
                        "id": "crit_redesenho_fluxo",
                        "nivel": nota_llm_simulada,
                        "justificativa": "ok",
                        "trecho_resposta": "resposta de listagem",
                    },
                    {
                        "id": "crit_gestao_riscos",
                        "nivel": nota_llm_simulada,
                        "justificativa": "ok",
                        "trecho_resposta": "resposta de listagem",
                    },
                    {
                        "id": "crit_indicadores_kpis",
                        "nivel": nota_llm_simulada,
                        "justificativa": "ok",
                        "trecho_resposta": "resposta de listagem",
                    },
                ]
            }
            if validar:
                try:
                    validar(dados)
                except ValueError as err:
                    raise ErroLLM(str(err)) from err
            return RespostaLLM(dados=dados, modelo="fake", tentativas=1, uso=None)

    app.dependency_overrides[obter_cliente_llm] = lambda: FakeLLMVar()

    try:
        # Tentativa 1: obj 1.0, llm 0 (nivel 0) -> nota_final 0.50
        nota_llm_simulada = 0
        p1 = {
            "destino_id": "analista_processos",
            "exercicio_id": "ex_analista_processos_01",
            "respostas_objetivas": {"q1": "C", "q2": "D", "q3": "A", "q4": "B"},
            "resposta_aberta": "Resposta de listagem tentativa numero 1.",
        }
        cliente.post("/me/tentativas", json=p1, headers=headers_csrf)

        # Tentativa 2: obj 1.0, llm 1.0 (nivel 2) -> nota_final 1.00 (MELHOR)
        nota_llm_simulada = 2
        p2 = {
            "destino_id": "analista_processos",
            "exercicio_id": "ex_analista_processos_01",
            "respostas_objetivas": {"q1": "C", "q2": "D", "q3": "A", "q4": "B"},
            "resposta_aberta": "Resposta de listagem tentativa numero 2 com texto diferente.",
        }
        r2 = cliente.post("/me/tentativas", json=p2, headers=headers_csrf)
        id2 = r2.json()["tentativa_id"]

        # Tentativa 3: obj 0.5 (2 corretas), llm 0.5 (nivel 1) -> nota_final 0.50 (ULTIMA)
        nota_llm_simulada = 1
        p3 = {
            "destino_id": "analista_processos",
            "exercicio_id": "ex_analista_processos_01",
            "respostas_objetivas": {"q1": "C", "q2": "D", "q3": "B", "q4": "A"},
            "resposta_aberta": "Resposta de listagem tentativa numero 3 com texto diferente.",
        }
        r3 = cliente.post("/me/tentativas", json=p3, headers=headers_csrf)
        id3 = r3.json()["tentativa_id"]

        # Consulta lista
        resp_lista = cliente.get("/me/tentativas?destino_id=analista_processos")
        assert resp_lista.status_code == 200
        corpo = resp_lista.json()

        assert corpo["ultima"] == id3
        assert corpo["melhor"] == id2
        assert len(corpo["itens"]) == 3

        # Resumo de cada tentativa nao vaza a resposta aberta
        for item in corpo["itens"]:
            assert "resposta_aberta" not in item
            assert "texto_redigido" not in item
    finally:
        app.dependency_overrides.pop(obter_cliente_llm, None)


@pytest.mark.oracle
@pytest.mark.mongo
def test_nenhuma_linha_de_log_contem_resposta_motivo_ou_trechos(caplog):
    """Valida seguranca de logging: caplog DEBUG nao contem texto da resposta nem motivo."""
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "s13_logsec")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}

    cliente.post(
        "/me/consentimentos",
        json={"finalidade": "curriculo_llm"},
        headers=headers_csrf,
    )

    segredo_resposta = "SEGREDO_RESPOSTA_ABERTA_MUITO_CONFIDENCIAL_123"
    segredo_motivo = "SEGREDO_MOTIVO_DISCORDO_MUITO_CONFIDENCIAL_456"

    class FakeLLM(ClienteLLM):
        def gerar_json(self, mensagens, schema, nome_schema, validar=None):
            dados = {
                "criterios": [
                    {
                        "id": "crit_redesenho_fluxo",
                        "nivel": 1,
                        "justificativa": "ok",
                        "trecho_resposta": segredo_resposta,
                    },
                    {
                        "id": "crit_gestao_riscos",
                        "nivel": 1,
                        "justificativa": "ok",
                        "trecho_resposta": segredo_resposta,
                    },
                    {
                        "id": "crit_indicadores_kpis",
                        "nivel": 1,
                        "justificativa": "ok",
                        "trecho_resposta": segredo_resposta,
                    },
                ]
            }
            if validar:
                try:
                    validar(dados)
                except ValueError as err:
                    raise ErroLLM(str(err)) from err
            return RespostaLLM(dados=dados, modelo="fake", tentativas=1, uso=None)

    app.dependency_overrides[obter_cliente_llm] = lambda: FakeLLM()

    try:
        with caplog.at_level(logging.DEBUG):
            payload = {
                "destino_id": "analista_processos",
                "exercicio_id": "ex_analista_processos_01",
                "respostas_objetivas": {"q1": "C", "q2": "D", "q3": "A", "q4": "B"},
                "resposta_aberta": (
                    f"Proposta contendo {segredo_resposta} para analise de conformidade."
                ),
            }
            r_tentativa = cliente.post("/me/tentativas", json=payload, headers=headers_csrf)
            assert r_tentativa.status_code == 201
            tentativa_id = r_tentativa.json()["tentativa_id"]

            r_disc = cliente.post(
                f"/me/tentativas/{tentativa_id}/discordo",
                json={"motivo": f"Contestacao com {segredo_motivo} registrado."},
                headers=headers_csrf,
            )
            assert r_disc.status_code == 200

        # Varre registros de log da aplicacao em DEBUG
        registros_app = [r for r in caplog.records if r.name.startswith("citizentech")]
        assert len(registros_app) > 0
        for record in registros_app:
            mensagem = record.getMessage()
            assert segredo_resposta not in mensagem, f"Vazamento no log: {mensagem}"
            assert segredo_motivo not in mensagem, f"Vazamento no log: {mensagem}"
    finally:
        app.dependency_overrides.pop(obter_cliente_llm, None)


def _fake_rubrica(criterios_por_id):
    class _Fake(ClienteLLM):
        def gerar_json(self, mensagens, schema, nome_schema, validar=None):
            dados = {"criterios": criterios_por_id}
            if validar:
                try:
                    validar(dados)
                except ValueError as exc:
                    raise ErroLLM(str(exc)) from exc
            return RespostaLLM(dados=dados, modelo="fake-rev", tentativas=1, uso=None)

    return _Fake()


@pytest.mark.oracle
@pytest.mark.mongo
def test_trecho_que_cruza_delimitador_removido_e_aceito():
    """RV-S13-02: a validação usa o mesmo texto (sem delimitadores) que foi à LLM."""
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "s13_rv02")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}
    cliente.post("/me/consentimentos", json={"finalidade": "curriculo_llm"}, headers=headers_csrf)
    token = uuid.uuid4().hex[:8]
    criterios = [
        {
            "id": "crit_redesenho_fluxo",
            "nivel": 2,
            "justificativa": "ok",
            "trecho_resposta": "fluxo to-be com triagem rapida",
        },
        {"id": "crit_gestao_riscos", "nivel": 0, "justificativa": "ausente", "trecho_resposta": ""},
        {
            "id": "crit_indicadores_kpis",
            "nivel": 0,
            "justificativa": "ausente",
            "trecho_resposta": "",
        },
    ]
    app.dependency_overrides[obter_cliente_llm] = lambda: _fake_rubrica(criterios)
    try:
        payload = {
            "destino_id": "analista_processos",
            "exercicio_id": "ex_analista_processos_01",
            "respostas_objetivas": {"q1": "C", "q2": "D", "q3": "A", "q4": "B"},
            "resposta_aberta": (
                f"Proposta {token}: fluxo TO-BE <<<RESPOSTA com triagem rapida e expedicao."
            ),
        }
        resp = cliente.post("/me/tentativas", json=payload, headers=headers_csrf)
        assert resp.status_code == 201
        assert resp.json()["aberta"]["status"] == "avaliada"
    finally:
        app.dependency_overrides.pop(obter_cliente_llm, None)


@pytest.mark.oracle
@pytest.mark.mongo
def test_falha_ao_gravar_resposta_nao_consome_tentativa(monkeypatch):
    """RV-S13-04: se a gravação da resposta falhar, a tentativa não fica registrada no Oracle."""
    from fastapi import HTTPException

    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "s13_rv04")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}
    cliente.post("/me/consentimentos", json={"finalidade": "curriculo_llm"}, headers=headers_csrf)

    def _falha(**_kwargs):
        raise HTTPException(
            status_code=503, detail={"erro": "Servico indisponivel", "detalhes": "x"}
        )

    monkeypatch.setattr("citizentech.avaliacao.rotas.salvar_resposta_aberta_mongo", _falha)
    app.dependency_overrides[obter_cliente_llm] = lambda: _fake_rubrica([])
    try:
        payload = {
            "destino_id": "analista_processos",
            "exercicio_id": "ex_analista_processos_01",
            "respostas_objetivas": {"q1": "C", "q2": "D", "q3": "A", "q4": "B"},
            "resposta_aberta": f"Resposta qualquer {uuid.uuid4().hex} com tamanho suficiente.",
        }
        resp = cliente.post("/me/tentativas", json=payload, headers=headers_csrf)
        assert resp.status_code == 503
        r_lista = cliente.get("/me/tentativas?destino_id=analista_processos")
        assert r_lista.status_code == 200
        assert r_lista.json()["itens"] == []
    finally:
        app.dependency_overrides.pop(obter_cliente_llm, None)
