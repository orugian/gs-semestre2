"""Contraexemplos públicos de segurança que não dependem de conexão Oracle."""

import hashlib
import time
import uuid

import jwt
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from citizentech.auth.limitador import LimitadorLogin, limitador_login
from citizentech.auth.tokens import decodificar_token_sessao, obter_expiracao_minutos
from citizentech.erros import ErroSegurancaIndisponivel
from citizentech.main import app

SEGREDO = "segredo-de-teste-super-seguro-com-mais-de-32-caracteres-para-jwt"


def _claims_validos():
    agora = int(time.time())
    return {
        "sub": uuid.uuid4().hex,
        "iat": agora,
        "exp": agora + 3600,
        "jti": uuid.uuid4().hex,
        "ver": 0,
        "csrf": hashlib.sha256(b"csrf-fixture").hexdigest(),
    }


@pytest.mark.parametrize("claim", ["sub", "iat", "exp", "jti", "ver", "csrf"])
def test_jwt_sem_claim_obrigatorio_e_recusado(claim):
    claims = _claims_validos()
    # Controle positivo: a única diferença do contraexemplo é o claim retirado.
    assert decodificar_token_sessao(jwt.encode(claims, SEGREDO, algorithm="HS256")) == claims
    claims.pop(claim)
    token = jwt.encode(claims, SEGREDO, algorithm="HS256")
    with pytest.raises(HTTPException) as erro:
        decodificar_token_sessao(token)
    assert erro.value.status_code == 401


@pytest.mark.parametrize("valor", ["amanha", {}, [], None])
def test_jwt_com_expiracao_de_tipo_invalido_e_401(valor):
    claims = _claims_validos()
    claims["exp"] = valor
    token = jwt.encode(claims, SEGREDO, algorithm="HS256")
    with pytest.raises(HTTPException) as erro:
        decodificar_token_sessao(token)
    assert erro.value.status_code == 401


def test_login_rejeita_senha_gigante_antes_de_depender_do_banco(monkeypatch):
    for nome in ("ORACLE_DSN", "ORACLE_USER", "ORACLE_PASSWORD"):
        monkeypatch.delenv(nome, raising=False)
    cliente = TestClient(app, base_url="https://testserver", raise_server_exceptions=False)
    resposta = cliente.post(
        "/auth/login", json={"email": "fixture@example.test", "senha": "x" * 5000}
    )
    assert resposta.status_code == 400
    assert set(resposta.json()) == {"erro", "detalhes"}
    assert "x" * 20 not in resposta.text


@pytest.mark.parametrize("segredo_invalido", [None, "", "curto", "segredo-com-menos-de-32-chars!"])
def test_registro_fail_closed_quando_jwt_secret_ausente_ou_curto(monkeypatch, segredo_invalido):
    if segredo_invalido is None:
        monkeypatch.delenv("JWT_SECRET", raising=False)
    else:
        monkeypatch.setenv("JWT_SECRET", segredo_invalido)
    for nome in ("ORACLE_DSN", "ORACLE_USER", "ORACLE_PASSWORD"):
        monkeypatch.delenv(nome, raising=False)
    cliente = TestClient(app, base_url="https://testserver", raise_server_exceptions=False)
    resposta = cliente.post(
        "/auth/registrar",
        json={"email": "teste@example.test", "senha": "SenhaForte123!"},
    )
    assert resposta.status_code == 503
    assert set(resposta.json()) == {"erro", "detalhes"}
    assert resposta.json()["erro"] == "Servico indisponivel"


@pytest.mark.parametrize("valor_invalido", ["invalido", "0", "-5", "-100", "99999999999999999999"])
def test_jwt_expira_minutos_invalido_ou_nao_positivo_retorna_503(monkeypatch, valor_invalido):
    monkeypatch.setenv("JWT_EXPIRA_MINUTOS", valor_invalido)
    with pytest.raises(ErroSegurancaIndisponivel):
        obter_expiracao_minutos()
    cliente = TestClient(app, base_url="https://testserver", raise_server_exceptions=False)
    resposta = cliente.post(
        "/auth/login",
        json={"email": "teste@example.test", "senha": "SenhaForte123!"},
    )
    assert resposta.status_code == 503
    assert set(resposta.json()) == {"erro", "detalhes"}
    assert resposta.json()["erro"] == "Servico indisponivel"
    assert "Configuracao de seguranca" in resposta.json()["detalhes"]


def test_jwt_expira_minutos_ausente_usa_padrao_60(monkeypatch):
    monkeypatch.delenv("JWT_EXPIRA_MINUTOS", raising=False)
    assert obter_expiracao_minutos() == 60


@pytest.mark.parametrize(
    ("claim", "valor_tipo_invalido"),
    [
        ("sub", ""),
        ("sub", 12345),
        ("jti", ""),
        ("jti", 12345),
        ("csrf", ""),
        ("csrf", 12345),
        ("ver", "0"),
        ("ver", True),
        ("iat", "1700000000"),
        ("iat", True),
        ("iat", float("nan")),
        ("iat", float("inf")),
        ("exp", True),
        ("exp", float("nan")),
        ("exp", float("inf")),
    ],
)
def test_jwt_com_claims_de_tipos_invalidos_rejeitados_com_401(claim, valor_tipo_invalido):
    claims = _claims_validos()
    claims[claim] = valor_tipo_invalido
    token = jwt.encode(claims, SEGREDO, algorithm="HS256")
    with pytest.raises(HTTPException) as erro:
        decodificar_token_sessao(token)
    assert erro.value.status_code == 401


def test_limitador_nao_guarda_email_de_requisicao_bloqueada_por_ip_e_expira_globalmente():
    tempo = [1000.0]
    lim = LimitadorLogin(limite=5, janela_segundos=60, time_provider=lambda: tempo[0])

    # 5 tentativas com o IP 10.0.0.1 e email A
    for _ in range(5):
        lim.verificar_e_registrar(["email:user_a@example.test", "ip:10.0.0.1"])

    assert lim.total_chaves_em_memoria() == 2

    # 6a tentativa: mesmo IP (bloqueado), mas fornecendo email B novo
    with pytest.raises(HTTPException) as exc_info:
        lim.verificar_e_registrar(["email:user_b_novo@example.test", "ip:10.0.0.1"])
    assert exc_info.value.status_code == 429

    # Prova de liberacao/nao-retencao: email B nao deve ser guardado em memoria
    assert "email:user_b_novo@example.test" not in lim._historico
    assert lim.total_chaves_em_memoria() == 2

    # Avanca o relogio para alem da janela de 60 segundos
    tempo[0] += 61.0

    # Purga global: entradas expiradas sao completamente removidas
    lim.purgar_expirados()
    assert lim.total_chaves_em_memoria() == 0


def test_limitador_comportamento_http_apos_expiracao(monkeypatch):
    tempo = [2000.0]
    monkeypatch.setattr(limitador_login, "time_provider", lambda: tempo[0])

    # Sem Oracle, login normal com credencial invalida retorna 503 se Oracle nao configurado,
    # porem queremos verificar a resposta de rate limit (429 vs 503/401).
    # 5 chamadas consom o limite
    for _ in range(5):
        limitador_login.verificar_e_registrar(["email:alvo@example.test", "ip:192.168.1.100"])

    # 6a chamada -> HTTP 429
    with pytest.raises(HTTPException) as exc_429:
        limitador_login.verificar_e_registrar(["email:alvo@example.test", "ip:192.168.1.100"])
    assert exc_429.value.status_code == 429
    assert exc_429.value.headers["Retry-After"] == "60"

    # Avanca o relogio em 61 segundos (apos a janela)
    tempo[0] += 61.0

    # Proxima chamada deve ter sucesso no limitador (sem 429) e limpar a memoria antiga
    limitador_login.verificar_e_registrar(["email:alvo@example.test", "ip:192.168.1.100"])
    # As chaves antigas expiraram e so a tentativa nova existe
    assert len(limitador_login._historico["email:alvo@example.test"]) == 1
    assert len(limitador_login._historico["ip:192.168.1.100"]) == 1
