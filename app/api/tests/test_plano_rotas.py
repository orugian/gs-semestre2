"""Testes de integracao das rotas de caminho e plano (/me/*) com Oracle e MongoDB."""

import logging
import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient

from citizentech.banco.conexao import obter_conexao
from citizentech.competencias.catalogo import carregar_catalogo_competencias
from citizentech.competencias.repositorio import (
    atualizar_competencia,
    salvar_candidatas_extracao,
)
from citizentech.main import app

TERMOS_PROIBIDOS_TEXTO = [
    "vaga",
    "probabilidade de",
    "vale a pena",
]


def _criar_usuario_e_sessao(cliente: TestClient, sufixo: str) -> dict:
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


def _verificar_ausencia_chaves_proibidas(obj: Any) -> None:
    proibidas = {"horas", "semanas", "prazo", "duracao", "score", "nota"}
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert k.lower() not in proibidas, f"Chave proibida encontrada: {k}"
            _verificar_ausencia_chaves_proibidas(v)
    elif isinstance(obj, list):
        for item in obj:
            _verificar_ausencia_chaves_proibidas(item)


def _verificar_ausencia_termos_texto(obj: Any) -> None:
    if isinstance(obj, dict):
        for v in obj.values():
            _verificar_ausencia_termos_texto(v)
    elif isinstance(obj, list):
        for item in obj:
            _verificar_ausencia_termos_texto(item)
    elif isinstance(obj, str):
        texto_lower = obj.lower()
        for termo in TERMOS_PROIBIDOS_TEXTO:
            assert termo not in texto_lower, f"Termo proibido '{termo}' encontrado no texto: {obj}"


@pytest.mark.oracle
@pytest.mark.mongo
def test_concluir_checkpoint_nao_demonstra_competencia():
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "plano_red")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}

    # Conceder consentimento 'perfil'
    resp = cliente.post(
        "/me/consentimentos",
        json={"finalidade": "perfil"},
        headers=headers_csrf,
    )
    assert resp.status_code == 201

    # 1. POST /me/caminho -> 201
    resp_cam = cliente.post(
        "/me/caminho",
        json={"destino_id": "analista_processos"},
        headers=headers_csrf,
    )
    assert resp_cam.status_code == 201
    dados_cam = resp_cam.json()

    checkpoints = dados_cam["plano"]["checkpoints"]
    assert len(checkpoints) > 0

    # Localizar checkpoint do tipo 'estudar'
    cp_estudar = next(cp for cp in checkpoints if cp["tipo"] == "estudar")
    cp_exercicio = next(cp for cp in checkpoints if cp["tipo"] == "exercicio")

    # 2. PATCH de um checkpoint estudar para 'concluido' -> 200
    resp_patch = cliente.patch(
        f"/me/plano/checkpoints/{cp_estudar['id']}",
        json={"status": "concluido"},
        headers=headers_csrf,
    )
    assert resp_patch.status_code == 200
    assert resp_patch.json()["status"] == "concluido"

    # 3. POST /me/comparacoes {"destinos":["analista_processos"]} -> continua sem demonstrada
    resp_comp = cliente.post(
        "/me/comparacoes",
        json={"destinos": ["analista_processos"]},
        headers=headers_csrf,
    )
    assert resp_comp.status_code == 201
    dados_comp = resp_comp.json()
    dest = dados_comp["destinos"][0]
    contagem = dest["dimensoes"]["requisitos"]["contagem"]
    assert contagem["demonstrada"] == 0, (
        "Concluir checkpoint não pode tornar competência demonstrada"
    )

    # 4. PATCH do checkpoint exercicio -> 409
    resp_patch_ex = cliente.patch(
        f"/me/plano/checkpoints/{cp_exercicio['id']}",
        json={"status": "concluido"},
        headers=headers_csrf,
    )
    assert resp_patch_ex.status_code == 409


@pytest.mark.oracle
@pytest.mark.mongo
def test_novo_caminho_substitui_anterior_e_get_plano_e_patch_antigo_404():
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "plano_subs")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}

    # Conceder consentimento 'perfil'
    resp_cons = cliente.post(
        "/me/consentimentos",
        json={"finalidade": "perfil"},
        headers=headers_csrf,
    )
    assert resp_cons.status_code == 201

    # 1. Cria caminho 1
    resp1 = cliente.post(
        "/me/caminho",
        json={"destino_id": "analista_processos"},
        headers=headers_csrf,
    )
    assert resp1.status_code == 201
    dados1 = resp1.json()
    cp_antigo_id = dados1["plano"]["checkpoints"][0]["id"]

    # 2. Cria caminho 2
    resp2 = cliente.post(
        "/me/caminho",
        json={"destino_id": "analista_dados_bi"},
        headers=headers_csrf,
    )
    assert resp2.status_code == 201
    dados2 = resp2.json()
    assert dados2["destino_id"] == "analista_dados_bi"
    assert dados2["caminho_id"] != dados1["caminho_id"]

    # 3. GET /me/plano retorna o caminho ativo (o segundo)
    resp_get = cliente.get("/me/plano")
    assert resp_get.status_code == 200
    dados_get = resp_get.json()
    assert dados_get["destino_id"] == "analista_dados_bi"
    assert dados_get["caminho_id"] == dados2["caminho_id"]

    # 4. PATCH no checkpoint do plano antigo vira 404
    resp_patch_antigo = cliente.patch(
        f"/me/plano/checkpoints/{cp_antigo_id}",
        json={"status": "concluido"},
        headers=headers_csrf,
    )
    assert resp_patch_antigo.status_code == 404


@pytest.mark.oracle
@pytest.mark.mongo
def test_comparacao_id_validacoes():
    cliente_a = TestClient(app, base_url="https://testserver")
    usuario_a = _criar_usuario_e_sessao(cliente_a, "usr_a")
    headers_a = {"X-CSRF-Token": usuario_a["csrf_token"]}

    cliente_b = TestClient(app, base_url="https://testserver")
    usuario_b = _criar_usuario_e_sessao(cliente_b, "usr_b")
    headers_b = {"X-CSRF-Token": usuario_b["csrf_token"]}

    for c, h in [(cliente_a, headers_a), (cliente_b, headers_b)]:
        r = c.post("/me/consentimentos", json={"finalidade": "perfil"}, headers=h)
        assert r.status_code == 201

    # Usuario A cria comparacao com analista_processos
    resp_comp_a = cliente_a.post(
        "/me/comparacoes",
        json={"destinos": ["analista_processos"]},
        headers=headers_a,
    )
    assert resp_comp_a.status_code == 201
    comp_a_id = resp_comp_a.json()["comparacao_id"]

    # Usuario B tenta usar comparacao de A -> 404
    resp_b_com_a = cliente_b.post(
        "/me/caminho",
        json={"destino_id": "analista_processos", "comparacao_id": comp_a_id},
        headers=headers_b,
    )
    assert resp_b_com_a.status_code == 404

    # Comparacao inexistente -> 404
    resp_inex = cliente_a.post(
        "/me/caminho",
        json={"destino_id": "analista_processos", "comparacao_id": "comp_inexistente_123"},
        headers=headers_a,
    )
    assert resp_inex.status_code == 404

    # Usuario A cria comparacao somente com analista_dados_bi
    resp_comp_dev = cliente_a.post(
        "/me/comparacoes",
        json={"destinos": ["analista_dados_bi"]},
        headers=headers_a,
    )
    assert resp_comp_dev.status_code == 201
    comp_dev_id = resp_comp_dev.json()["comparacao_id"]

    # Tentativa de escolher analista_processos passando comparacao sem analista_processos -> 400
    resp_dest_fora = cliente_a.post(
        "/me/caminho",
        json={"destino_id": "analista_processos", "comparacao_id": comp_dev_id},
        headers=headers_a,
    )
    assert resp_dest_fora.status_code == 400

    # Usuario A escolhe com comparacao valida que contem o destino -> 201
    resp_ok = cliente_a.post(
        "/me/caminho",
        json={"destino_id": "analista_processos", "comparacao_id": comp_a_id},
        headers=headers_a,
    )
    assert resp_ok.status_code == 201
    assert resp_ok.json()["comparacao_id"] == comp_a_id


@pytest.mark.oracle
@pytest.mark.mongo
def test_destino_fora_do_escopo_ou_invalido():
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "escopo")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}

    resp = cliente.post(
        "/me/consentimentos",
        json={"finalidade": "perfil"},
        headers=headers_csrf,
    )
    assert resp.status_code == 201

    resp_invalido = cliente.post(
        "/me/caminho",
        json={"destino_id": "astronauta_espacial"},
        headers=headers_csrf,
    )
    assert resp_invalido.status_code == 400


@pytest.mark.oracle
@pytest.mark.mongo
def test_seguranca_cookie_csrf_consentimento():
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "seguranca")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}

    # 1. Sem consentimento perfil -> 403
    resp_sem_perfil = cliente.post(
        "/me/caminho",
        json={"destino_id": "analista_processos"},
        headers=headers_csrf,
    )
    assert resp_sem_perfil.status_code == 403

    # Conceder consentimento perfil
    resp_cons = cliente.post(
        "/me/consentimentos",
        json={"finalidade": "perfil"},
        headers=headers_csrf,
    )
    assert resp_cons.status_code == 201

    # 2. GET /me/plano sem plano criado -> 404
    resp_sem_plano = cliente.get("/me/plano")
    assert resp_sem_plano.status_code == 404

    # 3. Sem cookie de sessao -> 401
    cliente_deslogado = TestClient(app, base_url="https://testserver")
    payload_destino = {"destino_id": "analista_processos"}
    resp_sem_cookie1 = cliente_deslogado.post("/me/caminho", json=payload_destino)
    assert resp_sem_cookie1.status_code == 401
    assert cliente_deslogado.get("/me/plano").status_code == 401
    resp_sem_cookie2 = cliente_deslogado.patch(
        "/me/plano/checkpoints/123",
        json={"status": "concluido"},
    )
    assert resp_sem_cookie2.status_code == 401

    # 4. Sem CSRF -> 403
    resp_sem_csrf1 = cliente.post("/me/caminho", json=payload_destino)
    assert resp_sem_csrf1.status_code == 403
    resp_sem_csrf2 = cliente.patch("/me/plano/checkpoints/123", json={"status": "concluido"})
    assert resp_sem_csrf2.status_code == 403


@pytest.mark.oracle
@pytest.mark.mongo
def test_patch_checkpoint_erros_validacao_e_outro_usuario():
    cliente_a = TestClient(app, base_url="https://testserver")
    usuario_a = _criar_usuario_e_sessao(cliente_a, "patch_a")
    headers_a = {"X-CSRF-Token": usuario_a["csrf_token"]}

    cliente_b = TestClient(app, base_url="https://testserver")
    usuario_b = _criar_usuario_e_sessao(cliente_b, "patch_b")
    headers_b = {"X-CSRF-Token": usuario_b["csrf_token"]}

    for c, h in [(cliente_a, headers_a), (cliente_b, headers_b)]:
        r = c.post("/me/consentimentos", json={"finalidade": "perfil"}, headers=h)
        assert r.status_code == 201

    resp_cam = cliente_a.post(
        "/me/caminho",
        json={"destino_id": "analista_processos"},
        headers=headers_a,
    )
    assert resp_cam.status_code == 201
    cp_a_id = resp_cam.json()["plano"]["checkpoints"][0]["id"]

    # Usuario B tenta alterar checkpoint de A -> 404
    resp_b_patch = cliente_b.patch(
        f"/me/plano/checkpoints/{cp_a_id}",
        json={"status": "concluido"},
        headers=headers_b,
    )
    assert resp_b_patch.status_code == 404

    # Status invalido -> 400
    resp_invalido = cliente_a.patch(
        f"/me/plano/checkpoints/{cp_a_id}",
        json={"status": "status_nao_permitido"},
        headers=headers_a,
    )
    assert resp_invalido.status_code == 400

    # Checkpoint inexistente -> 404
    resp_inex = cliente_a.patch(
        "/me/plano/checkpoints/id_inexistente",
        json={"status": "concluido"},
        headers=headers_a,
    )
    assert resp_inex.status_code == 404


@pytest.mark.oracle
@pytest.mark.mongo
def test_base_json_sem_trecho_origem_e_logs_sem_trechos(caplog):
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "trecho_sec")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}

    # Conceder consentimento perfil
    resp_cons = cliente.post(
        "/me/consentimentos",
        json={"finalidade": "perfil"},
        headers=headers_csrf,
    )
    assert resp_cons.status_code == 201

    # Cria competencia declarada com trecho de origem confidencial
    trecho_confidencial = "TRECHO_SENSIVEL_SIGILOSO_123456789"
    catalogo = carregar_catalogo_competencias()
    curriculo_id = uuid.uuid4().hex
    extracao_id = uuid.uuid4().hex

    # esco_id de analista_processos: processos_empresariais
    esco_id = "9e84a506-df06-4be3-874a-fa01293e3dd5"
    candidatas = [{"esco_id": esco_id, "trecho_origem": trecho_confidencial}]
    salvos = salvar_candidatas_extracao(
        usuario["id"], curriculo_id, extracao_id, candidatas, catalogo
    )
    atualizar_competencia(
        salvos[0]["id"], usuario["id"], "confirmar", trecho_confidencial, catalogo
    )

    with caplog.at_level(logging.DEBUG):
        resp_cam = cliente.post(
            "/me/caminho",
            json={"destino_id": "analista_processos"},
            headers=headers_csrf,
        )
        assert resp_cam.status_code == 201
        caminho_id = resp_cam.json()["caminho_id"]

    # 1. Verifica no banco Oracle que base_json nao contem trecho_origem
    with obter_conexao() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT base_json FROM plano WHERE caminho_id = :cid", {"cid": caminho_id})
            row = cur.fetchone()
            assert row is not None
            base_json_val = row[0]
            if hasattr(base_json_val, "read"):
                base_json_val = base_json_val.read()
            assert trecho_confidencial not in str(base_json_val)
            assert "trecho_origem" not in str(base_json_val)

    # 2. Verifica que nenhuma linha de log contem o trecho confidencial
    assert trecho_confidencial not in caplog.text


@pytest.mark.oracle
@pytest.mark.mongo
def test_plano_usa_exercicio_demonstrado_da_avaliacao():
    """Integração S12×S13: requisitos demonstrados pelo exercício não geram passos de estudo."""
    from citizentech.llm.cliente import ClienteLLM, RespostaLLM, obter_cliente_llm

    class _FakeNota2(ClienteLLM):
        def gerar_json(self, mensagens, schema, nome_schema, validar=None):
            ids = schema["properties"]["criterios"]["items"]["properties"]["id"]["enum"]
            dados = {
                "criterios": [
                    {"id": i, "nivel": 2, "justificativa": "ok", "trecho_resposta": "fluxo to-be"}
                    for i in ids
                ]
            }
            if validar:
                validar(dados)
            return RespostaLLM(dados=dados, modelo="fake", tentativas=1, uso=None)

    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "s12_s13")
    h = {"X-CSRF-Token": usuario["csrf_token"]}
    cliente.post("/me/consentimentos", json={"finalidade": "perfil"}, headers=h)
    cliente.post("/me/consentimentos", json={"finalidade": "curriculo_llm"}, headers=h)
    app.dependency_overrides[obter_cliente_llm] = lambda: _FakeNota2()
    try:
        r = cliente.post(
            "/me/tentativas",
            headers=h,
            json={
                "destino_id": "analista_processos",
                "exercicio_id": "ex_analista_processos_01",
                "respostas_objetivas": {"q1": "C", "q2": "D", "q3": "A", "q4": "B"},
                "resposta_aberta": (
                    f"Proposta {uuid.uuid4().hex[:6]} com fluxo TO-BE e pontos de checagem."
                ),
            },
        )
        assert r.status_code == 201
        assert r.json()["resultado"] == "demonstrada"
    finally:
        app.dependency_overrides.pop(obter_cliente_llm, None)

    resp = cliente.post("/me/caminho", json={"destino_id": "analista_processos"}, headers=h)
    assert resp.status_code == 201
    plano = resp.json()["plano"]
    assert "processos_empresariais" in plano["ja_demonstrados"]
    ids_com_passo = {c["requisito_id_local"] for c in plano["checkpoints"]}
    assert "processos_empresariais" not in ids_com_passo
    # Requisito que o exercício não avalia continua gerando passos
    assert "analisar_dados" in ids_com_passo
