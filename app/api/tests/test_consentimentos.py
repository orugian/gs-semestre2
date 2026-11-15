"""Testes de consentimentos e autorizacao por proprietario (T14, R20)."""

import uuid

import pytest
from fastapi.testclient import TestClient

from citizentech.consentimentos.repositorio import buscar_consentimento_global
from citizentech.main import app


def criar_usuario_e_sessao(cliente: TestClient, sufixo: str) -> dict:
    """Funcao auxiliar para criar conta e logar retornando cookies e token CSRF."""
    email = f"usuario_{sufixo}_{uuid.uuid4().hex[:6]}@example.test"
    senha = "SenhaForte123!@"

    # 1. Registrar
    resp_reg = cliente.post("/auth/registrar", json={"email": email, "senha": senha})
    assert resp_reg.status_code == 201
    dados_reg = resp_reg.json()

    # 2. Login
    resp_login = cliente.post("/auth/login", json={"email": email, "senha": senha})
    assert resp_login.status_code == 200
    csrf_token = cliente.cookies.get("csrf_token")
    assert csrf_token is not None

    return {
        "id": dados_reg["id"],
        "email": email,
        "csrf_token": csrf_token,
    }


@pytest.mark.oracle
def test_consentimentos_fluxo_completo_concessao_listagem_revogacao():
    cliente = TestClient(app, base_url="https://testserver")
    usuario = criar_usuario_e_sessao(cliente, "fluxo")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}

    # 1. Rejeita concessao sem autenticacao
    cliente_anonimo = TestClient(app, base_url="https://testserver")
    resp_sem_auth = cliente_anonimo.post(
        "/me/consentimentos",
        json={"finalidade": "perfil"},
        headers={"X-CSRF-Token": "qualquer"},
    )
    assert resp_sem_auth.status_code == 401

    # 2. Rejeita concessao autenticada sem CSRF (R20)
    resp_sem_csrf = cliente.post("/me/consentimentos", json={"finalidade": "perfil"})
    assert resp_sem_csrf.status_code == 403

    # 3. Rejeita finalidade desconhecida com 400
    resp_invalido = cliente.post(
        "/me/consentimentos",
        json={"finalidade": "marketing_externo"},
        headers=headers_csrf,
    )
    assert resp_invalido.status_code == 400

    # 4. Concede consentimentos validos com CSRF -> 201
    resp_c1 = cliente.post(
        "/me/consentimentos",
        json={"finalidade": "perfil"},
        headers=headers_csrf,
    )
    assert resp_c1.status_code == 201
    c1 = resp_c1.json()
    assert "id" in c1
    assert c1["finalidade"] == "perfil"
    assert c1["versao_termo"] == "v1.0"
    assert "concedido_em" in c1
    assert c1["revogado_em"] is None

    resp_c2 = cliente.post(
        "/me/consentimentos",
        json={"finalidade": "laboratorio_nuvem"},
        headers=headers_csrf,
    )
    assert resp_c2.status_code == 201
    c2 = resp_c2.json()

    # 5. Lista consentimentos (GET nao exige CSRF) -> 200
    resp_list = cliente.get("/me/consentimentos")
    assert resp_list.status_code == 200
    itens = resp_list.json()["itens"]
    ids_listados = [item["id"] for item in itens]
    assert c1["id"] in ids_listados
    assert c2["id"] in ids_listados

    # 6. Revoga c1 -> 204
    resp_revoga = cliente.delete(f"/me/consentimentos/{c1['id']}", headers=headers_csrf)
    assert resp_revoga.status_code == 204

    # 7. Repetir revogacao -> 204 (idempotente)
    resp_revoga_repetida = cliente.delete(
        f"/me/consentimentos/{c1['id']}",
        headers=headers_csrf,
    )
    assert resp_revoga_repetida.status_code == 204

    # 8. Lista novamente e confere que c1 possui revogado_em preenchido
    resp_list_apos = cliente.get("/me/consentimentos")
    itens_apos = resp_list_apos.json()["itens"]
    item_c1 = next(it for it in itens_apos if it["id"] == c1["id"])
    assert item_c1["revogado_em"] is not None


@pytest.mark.oracle
def test_t14_autorizacao_por_proprietario_sem_vazamento_de_existencia():
    """T14: Usuario B tenta revogar ou ler dado de A -> 404 identico a id inexistente.

    O consentimento de A permanece ativo e nao e listado para B.
    """
    cliente_a = TestClient(app, base_url="https://testserver")
    usuario_a = criar_usuario_e_sessao(cliente_a, "t14_a")
    headers_a = {"X-CSRF-Token": usuario_a["csrf_token"]}

    cliente_b = TestClient(app, base_url="https://testserver")
    usuario_b = criar_usuario_e_sessao(cliente_b, "t14_b")
    headers_b = {"X-CSRF-Token": usuario_b["csrf_token"]}

    # A cria consentimento
    resp_c_a = cliente_a.post(
        "/me/consentimentos",
        json={"finalidade": "curriculo_llm"},
        headers=headers_a,
    )
    assert resp_c_a.status_code == 201
    id_consentimento_a = resp_c_a.json()["id"]

    # B tenta deletar id inexistente para capturar a resposta padrao
    id_inexistente = uuid.uuid4().hex
    resp_b_inexistente = cliente_b.delete(
        f"/me/consentimentos/{id_inexistente}",
        headers=headers_b,
    )
    assert resp_b_inexistente.status_code == 404
    corpo_inexistente = resp_b_inexistente.json()

    # B tenta deletar o consentimento de A
    resp_b_ataca_a = cliente_b.delete(
        f"/me/consentimentos/{id_consentimento_a}",
        headers=headers_b,
    )
    # Deve retornar 404 com EXATAMENTE o mesmo corpo para nao vazar existencia
    assert resp_b_ataca_a.status_code == 404
    assert resp_b_ataca_a.json() == corpo_inexistente

    # O consentimento de A deve continuar ATIVO no banco (revogado_em e None)
    dado_a_no_banco = buscar_consentimento_global(id_consentimento_a)
    assert dado_a_no_banco is not None
    assert dado_a_no_banco["revogado_em"] is None

    # GET /me/consentimentos de B nao lista o consentimento de A
    resp_list_b = cliente_b.get("/me/consentimentos")
    ids_b = [it["id"] for it in resp_list_b.json()["itens"]]
    assert id_consentimento_a not in ids_b


@pytest.mark.oracle
def test_r20_csrf_com_token_de_outra_sessao_rejeitado_com_403():
    """R20: Usar cookie de sessao de A com o token CSRF de B -> 403."""
    cliente_a = TestClient(app, base_url="https://testserver")
    criar_usuario_e_sessao(cliente_a, "r20_a")

    cliente_b = TestClient(app, base_url="https://testserver")
    usuario_b = criar_usuario_e_sessao(cliente_b, "r20_b")

    # A tenta mutacao usando o X-CSRF-Token de B
    resp_forjada = cliente_a.post(
        "/me/consentimentos",
        json={"finalidade": "perfil"},
        headers={"X-CSRF-Token": usuario_b["csrf_token"]},
    )
    assert resp_forjada.status_code == 403
    assert "CSRF" in resp_forjada.json()["detalhes"]

    # A tenta logout usando o X-CSRF-Token de B
    resp_logout_forjado = cliente_a.post(
        "/auth/logout",
        headers={"X-CSRF-Token": usuario_b["csrf_token"]},
    )
    assert resp_logout_forjado.status_code == 403
