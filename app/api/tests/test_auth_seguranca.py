"""Testes de seguranca, rate limit, injecao, fail-closed e privacidade (S5)."""

import concurrent.futures
import uuid

import pytest
from fastapi.testclient import TestClient

from citizentech.auth.limitador import limitador_login
from citizentech.banco.conexao import fechar_pool
from citizentech.main import app


# ---------------------------------------------------------------------------
# 1. Rate Limit de Login (D12, T16)
# ---------------------------------------------------------------------------
@pytest.mark.oracle
def test_rate_limit_login_5_por_minuto_com_relogio_injetado(monkeypatch):
    tempo_simulado = 5000.0
    monkeypatch.setattr(limitador_login, "time_provider", lambda: tempo_simulado)
    limitador_login.resetar()

    cliente = TestClient(app, base_url="https://testserver")
    email = f"rate_limit_{uuid.uuid4().hex[:8]}@example.test"
    senha_correta = "SenhaForte123!@"
    cliente.post("/auth/registrar", json={"email": email, "senha": senha_correta})

    # 1 a 5 tentativas com senha errada -> 401
    for _ in range(5):
        resp = cliente.post("/auth/login", json={"email": email, "senha": "SenhaIncorreta123!"})
        assert resp.status_code == 401

    # 6ª tentativa -> 429 Too Many Requests com Retry-After
    resp_6 = cliente.post("/auth/login", json={"email": email, "senha": "SenhaIncorreta123!"})
    assert resp_6.status_code == 429
    assert resp_6.headers.get("Retry-After") == "60"
    assert resp_6.json()["erro"] == "Muitas requisicoes"

    # Tentativa com senha correta tambem bloqueada na 6ª tentativa -> 429
    resp_correta_bloqueada = cliente.post(
        "/auth/login", json={"email": email, "senha": senha_correta}
    )
    assert resp_correta_bloqueada.status_code == 429

    # Avanca o relogio em 61 segundos -> libera login
    tempo_simulado = 5061.0
    resp_liberada = cliente.post(
        "/auth/login", json={"email": email, "senha": senha_correta}
    )
    assert resp_liberada.status_code == 200

    limitador_login.resetar()


@pytest.mark.oracle
def test_rate_limit_email_inexistente_nao_revela_existencia(monkeypatch):
    tempo_simulado = 10000.0
    monkeypatch.setattr(limitador_login, "time_provider", lambda: tempo_simulado)
    limitador_login.resetar()

    cliente = TestClient(app, base_url="https://testserver")
    email_inexistente = f"fantasma_{uuid.uuid4().hex[:8]}@example.test"

    for _ in range(5):
        resp = cliente.post(
            "/auth/login", json={"email": email_inexistente, "senha": "Qualquer123!@"}
        )
        assert resp.status_code == 401

    resp_bloqueado = cliente.post(
        "/auth/login", json={"email": email_inexistente, "senha": "Qualquer123!@"}
    )
    assert resp_bloqueado.status_code == 429
    assert resp_bloqueado.headers.get("Retry-After") == "60"

    limitador_login.resetar()


# ---------------------------------------------------------------------------
# 2. Cadastro Duplicado e Concorrencia
# ---------------------------------------------------------------------------
@pytest.mark.oracle
def test_cadastro_duplicado_mesmo_com_maiusculas_ou_espacos():
    cliente = TestClient(app, base_url="https://testserver")
    email_base = f"duplicado_{uuid.uuid4().hex[:8]}@example.test"
    senha = "SenhaForte123!@"

    # 1. Primeiro cadastro -> 201
    resp1 = cliente.post("/auth/registrar", json={"email": email_base, "senha": senha})
    assert resp1.status_code == 201

    # 2. Segundo cadastro identico -> 409
    resp2 = cliente.post("/auth/registrar", json={"email": email_base, "senha": senha})
    assert resp2.status_code == 409
    assert resp2.json()["erro"] == "Conflito"

    # 3. Terceiro cadastro variando maiusculas e espacos -> 409
    email_variado = f"  {email_base.upper()}  "
    resp3 = cliente.post("/auth/registrar", json={"email": email_variado, "senha": senha})
    assert resp3.status_code == 409


@pytest.mark.oracle
def test_concorrencia_dois_cadastros_simultaneos_gera_um_201_e_um_409():
    email = f"concorrente_{uuid.uuid4().hex[:8]}@example.test"
    senha = "SenhaForte123!@"

    cliente1 = TestClient(app, base_url="https://testserver")
    cliente2 = TestClient(app, base_url="https://testserver")

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        payload = {"email": email, "senha": senha}
        f1 = executor.submit(cliente1.post, "/auth/registrar", json=payload)
        f2 = executor.submit(cliente2.post, "/auth/registrar", json=payload)
        r1 = f1.result()
        r2 = f2.result()

    status_codes = sorted([r1.status_code, r2.status_code])
    assert status_codes == [201, 409], f"Esperava [201, 409], obteve {status_codes}"


# ---------------------------------------------------------------------------
# 3. Validacoes de Entrada (HTTP 400 sem vazar dados)
# ---------------------------------------------------------------------------
def test_validacoes_retornam_400_e_nao_ecoam_dados():
    cliente = TestClient(app, base_url="https://testserver")

    # E-mail sem @
    r = cliente.post("/auth/registrar", json={"email": "sem-arroba", "senha": "SenhaForte123!@"})
    assert r.status_code == 400
    assert "sem-arroba" not in r.text

    # Senha curta
    r = cliente.post("/auth/registrar", json={"email": "valido@example.test", "senha": "curta"})
    assert r.status_code == 400
    assert "curta" not in r.text

    # Senha de 2000 caracteres (> 1024 bytes)
    senha_longa = "s" * 2000
    r = cliente.post("/auth/registrar", json={"email": "valido@example.test", "senha": senha_longa})
    assert r.status_code == 400
    assert senha_longa not in r.text

    # Corpo que nao e objeto JSON
    r = cliente.post(
        "/auth/registrar",
        content="['item1', 'item2']",
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 400

    # E-mail numerico
    r = cliente.post("/auth/registrar", json={"email": 123456, "senha": "SenhaForte123!@"})
    assert r.status_code == 400

    # JSON malformado
    r = cliente.post(
        "/auth/registrar",
        content="{email: 'invalido'",
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# 4. Fail-Closed com JWT_SECRET Ausente ou Curto
# ---------------------------------------------------------------------------
def test_jwt_secret_ausente_responde_503_fail_closed(monkeypatch):
    monkeypatch.delenv("JWT_SECRET", raising=False)
    cliente = TestClient(app, base_url="https://testserver")

    resp_login = cliente.post(
        "/auth/login",
        json={"email": "teste@example.test", "senha": "SenhaForte123!@"},
    )
    assert resp_login.status_code == 503
    assert resp_login.json()["erro"] == "Servico indisponivel"


# ---------------------------------------------------------------------------
# 5. Invariante de Privacidade e Ausencia de Segredos em Log e Respostas (T16)
# ---------------------------------------------------------------------------
@pytest.mark.oracle
def test_nenhum_segredo_aparece_em_resposta_ou_log(caplog):
    cliente = TestClient(app, base_url="https://testserver")
    email_privado = f"segredo_privacidade_{uuid.uuid4().hex[:8]}@example.test"
    senha_secreta = "MinhaSuperSenhaSecreta123!@"

    # Executa operacoes que geram respostas e logs
    cliente.post("/auth/registrar", json={"email": email_privado, "senha": senha_secreta})
    resp_login = cliente.post("/auth/login", json={"email": email_privado, "senha": senha_secreta})
    assert resp_login.status_code == 200

    # Forca erro 401
    resp_erro = cliente.post(
        "/auth/login", json={"email": email_privado, "senha": "SenhaErrada!@#123"}
    )
    assert resp_erro.status_code == 401

    # Inspeciona todas as mensagens capturadas no log
    logs_texto = " ".join(record.getMessage() for record in caplog.records)

    # Nunca pode conter a senha nem o e-mail em plain text
    assert senha_secreta not in logs_texto
    assert "SenhaErrada!@#123" not in logs_texto
    assert email_privado not in logs_texto

    # Respostas de erro nunca ecoam senhas ou e-mails
    assert senha_secreta not in resp_erro.text
    assert "SenhaErrada!@#123" not in resp_erro.text
    assert email_privado not in resp_erro.text


# ---------------------------------------------------------------------------
# 6. SQL Injection com Bind Variables
# ---------------------------------------------------------------------------
@pytest.mark.oracle
def test_prevencao_sql_injection():
    cliente = TestClient(app, base_url="https://testserver")

    # Injeção no e-mail durante o login
    email_sql_inj = "x' OR '1'='1"
    resp_inj = cliente.post(
        "/auth/login",
        json={"email": email_sql_inj, "senha": "SenhaForte123!@"},
    )
    # Rejeitado por validacao de formato ou 401, nunca executa SQL arbitraria
    assert resp_inj.status_code in (400, 401)

    # Injeção no consentimento_id
    id_sql_inj = "1 OR 1=1"
    resp_inj_consent = cliente.delete(
        f"/me/consentimentos/{id_sql_inj}",
        headers={"X-CSRF-Token": "token-falso"},
    )
    # Sem autenticação válida -> 401
    assert resp_inj_consent.status_code == 401


# ---------------------------------------------------------------------------
# 7. Disponibilidade Parcial: Banco Indisponivel vs Health Check
# ---------------------------------------------------------------------------
def test_banco_indisponivel_devolve_503_sem_vazar_ora_e_health_continua_200(monkeypatch):
    fechar_pool()
    monkeypatch.setenv("ORACLE_DSN", "localhost:9999/INEXISTENTE_DB")
    cliente = TestClient(app, base_url="https://testserver")

    # Rota que precisa do banco devolve 503 generico
    resp_login = cliente.post(
        "/auth/login",
        json={"email": "usuario@example.test", "senha": "SenhaForte123!@"},
    )
    assert resp_login.status_code == 503
    assert "ORA-" not in resp_login.text
    assert "9999" not in resp_login.text
    assert resp_login.json()["erro"] == "Servico indisponivel"

    # Rota /health continua retornando 200
    resp_health = cliente.get("/health")
    assert resp_health.status_code == 200
    assert resp_health.json()["status"] == "ok"

    fechar_pool()
