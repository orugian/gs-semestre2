"""Testes de integracao do fluxo de autenticacao e sessao (S5)."""

import uuid

import pytest
from fastapi.testclient import TestClient

from citizentech.main import app


@pytest.mark.oracle
def test_ciclo_completo_registro_login_me():
    cliente = TestClient(app, base_url="https://testserver")
    email = f"usuario_{uuid.uuid4().hex[:8]}@example.test"
    senha = "SenhaForte123!@"

    # 1. Registrar conta -> 201
    resp_reg = cliente.post("/auth/registrar", json={"email": email, "senha": senha})
    assert resp_reg.status_code == 201
    dados_reg = resp_reg.json()
    assert "id" in dados_reg
    assert dados_reg["email"] == email.lower()
    assert "criado_em" in dados_reg

    # 2. Login -> 200 + cookies de sessao e csrf
    resp_login = cliente.post("/auth/login", json={"email": email, "senha": senha})
    assert resp_login.status_code == 200
    dados_login = resp_login.json()
    assert dados_login["id"] == dados_reg["id"]
    assert dados_login["email"] == email.lower()

    # Verifica atributos do cookie de sessao no Set-Cookie
    cookies_headers = resp_login.headers.get_list("set-cookie")
    cookie_sessao_raw = next((c for c in cookies_headers if "sessao=" in c), None)
    assert cookie_sessao_raw is not None, "Cookie de sessao ausente no Set-Cookie"
    assert "httponly" in cookie_sessao_raw.lower()
    assert "secure" in cookie_sessao_raw.lower()
    assert "samesite=lax" in cookie_sessao_raw.lower()

    # 3. GET /me com cookie -> 200 com mesmo id e email
    resp_me = cliente.get("/me")
    assert resp_me.status_code == 200
    dados_me = resp_me.json()
    assert dados_me["id"] == dados_reg["id"]
    assert dados_me["email"] == email.lower()
    assert "criado_em" in dados_me
    assert dados_me["persona_demo"] == "N"

    # 4. GET /me sem cookie -> 401
    cliente_anonimo = TestClient(app, base_url="https://testserver")
    resp_sem_cookie = cliente_anonimo.get("/me")
    assert resp_sem_cookie.status_code == 401


@pytest.mark.oracle
def test_logout_invalida_sessao_no_servidor_e_apaga_cookies():
    """Logout real: usuario.sessao_versao e incrementada; cookie antigo -> 401."""
    cliente = TestClient(app, base_url="https://testserver")
    email = f"usuario_logout_{uuid.uuid4().hex[:8]}@example.test"
    senha = "SenhaForte123!@"

    cliente.post("/auth/registrar", json={"email": email, "senha": senha})
    resp_login = cliente.post("/auth/login", json={"email": email, "senha": senha})
    assert resp_login.status_code == 200

    cookie_sessao_salvo = cliente.cookies.get("sessao")
    csrf_token = cliente.cookies.get("csrf_token")
    assert cookie_sessao_salvo is not None
    assert csrf_token is not None

    # Logout sem CSRF -> 403
    resp_sem_csrf = cliente.post("/auth/logout")
    assert resp_sem_csrf.status_code == 403

    # Logout com CSRF correto -> 204
    resp_logout = cliente.post("/auth/logout", headers={"X-CSRF-Token": csrf_token})
    assert resp_logout.status_code == 204

    # Confere que Set-Cookie de remocao foi enviado
    cookies_headers = resp_logout.headers.get_list("set-cookie")
    assert any(
        "sessao=" in c and ("max-age=0" in c.lower() or "expires=" in c.lower())
        for c in cookies_headers
    )

    # Cliente que copiou o cookie antes do logout tenta acessar GET /me -> 401
    cliente_forjador = TestClient(app, base_url="https://testserver")
    cliente_forjador.cookies.set("sessao", cookie_sessao_salvo)
    resp_pos_logout = cliente_forjador.get("/me")
    assert resp_pos_logout.status_code == 401
    assert "logout" in resp_pos_logout.json()["detalhes"].lower()


@pytest.mark.oracle
def test_login_credenciais_invalidas_mesmo_caminho_e_mensagem():
    """Login com e-mail inexistente e senha incorreta possuem mensagens idênticas."""
    cliente = TestClient(app, base_url="https://testserver")
    email_cadastrado = f"usuario_cred_{uuid.uuid4().hex[:8]}@example.test"
    senha_correta = "SenhaForte123!@"

    cliente.post("/auth/registrar", json={"email": email_cadastrado, "senha": senha_correta})

    # 1. E-mail existente com senha errada -> 401
    resp_senha_errada = cliente.post(
        "/auth/login",
        json={"email": email_cadastrado, "senha": "SenhaErrada123!@"},
    )
    assert resp_senha_errada.status_code == 401
    corpo_esperado = resp_senha_errada.json()
    assert corpo_esperado["erro"] == "Nao autenticado"
    assert corpo_esperado["detalhes"] == "Credenciais invalidas."

    # 2. E-mail inexistente -> 401 com resposta identica
    resp_email_inexistente = cliente.post(
        "/auth/login",
        json={
            "email": f"inexistente_{uuid.uuid4().hex[:8]}@example.test",
            "senha": "SenhaQualquer123!@",
        },
    )
    assert resp_email_inexistente.status_code == 401
    assert resp_email_inexistente.json() == corpo_esperado
