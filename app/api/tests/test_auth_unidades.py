"""Testes unitarios puros das regras de autenticacao, senha, JWT, CSRF e limitador (sem banco)."""

import hashlib
import time

import jwt
import pytest
from fastapi import HTTPException

from citizentech.auth.csrf import gerar_token_csrf, validar_token_csrf
from citizentech.auth.esquemas import normalizar_e_validar_email
from citizentech.auth.limitador import LimitadorLogin
from citizentech.auth.senhas import (
    executar_verificacao_ficticia,
    gerar_hash_senha,
    validar_politica_senha,
    verificar_senha,
)
from citizentech.auth.tokens import (
    criar_token_sessao,
    decodificar_token_sessao,
    obter_jwt_secret,
)
from citizentech.erros import ErroSegurancaIndisponivel


# ---------------------------------------------------------------------------
# 1. Politica e Hash de Senhas
# ---------------------------------------------------------------------------
def test_senha_valida_passa_na_politica():
    validar_politica_senha("SenhaForte123!@")
    validar_politica_senha("a" * 10)
    validar_politica_senha("a" * 128)


def test_senha_curta_rejeitada_com_400():
    with pytest.raises(HTTPException) as exc_info:
        validar_politica_senha("curta9ch")
    assert exc_info.value.status_code == 400
    assert "10 e 128" in exc_info.value.detail["detalhes"]


def test_senha_longa_rejeitada_com_400():
    with pytest.raises(HTTPException) as exc_info:
        validar_politica_senha("a" * 129)
    assert exc_info.value.status_code == 400
    assert "10 e 128" in exc_info.value.detail["detalhes"]


def test_senha_acima_de_1024_bytes_rejeitada_antes_do_hash():
    senha_enorme = "a" * 1025
    with pytest.raises(HTTPException) as exc_info:
        validar_politica_senha(senha_enorme)
    assert exc_info.value.status_code == 400
    assert "limite maximo" in exc_info.value.detail["detalhes"]


def test_geracao_e_verificacao_argon2():
    senha = "MinhaSenhaSuperSegura123!"
    hash_senha = gerar_hash_senha(senha)
    assert hash_senha.startswith("$argon2id$")
    assert verificar_senha(hash_senha, senha) is True
    assert verificar_senha(hash_senha, "SenhaErradaTotal123") is False


def test_verificacao_ficticia_executa_sem_erros():
    executar_verificacao_ficticia("qualquer_senha")


# ---------------------------------------------------------------------------
# 2. Normalizacao e Validacao de E-mail
# ---------------------------------------------------------------------------
def test_normalizacao_email():
    email_bruto = "  Usuario.Teste@Dominio.COM  "
    assert normalizar_e_validar_email(email_bruto) == "usuario.teste@dominio.com"


def test_email_invalido_sem_arroba():
    with pytest.raises(ValueError) as exc_info:
        normalizar_e_validar_email("usuario-sem-arroba.com")
    assert "invalido" in str(exc_info.value)
    assert "usuario-sem-arroba.com" not in str(exc_info.value)


def test_email_invalido_sem_dominio():
    with pytest.raises(ValueError) as exc_info:
        normalizar_e_validar_email("usuario@dominio")
    assert "invalido" in str(exc_info.value)


def test_email_excede_254_caracteres():
    email_longo = "a" * 245 + "@example.test"  # > 254 chars
    with pytest.raises(ValueError) as exc_info:
        normalizar_e_validar_email(email_longo)
    assert "254" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 3. JWT e Segredos (Fail-Closed)
# ---------------------------------------------------------------------------
def test_jwt_secret_ausente_ou_curto_lanca_503(monkeypatch):
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(ErroSegurancaIndisponivel):
        obter_jwt_secret()

    monkeypatch.setenv("JWT_SECRET", "x" * 31)
    with pytest.raises(ErroSegurancaIndisponivel):
        obter_jwt_secret()


def test_ciclo_jwt_com_claims_obrigatorios():
    relogio_falso = 1700000000.0
    csrf_token = "meu-csrf-secreto"
    token = criar_token_sessao(
        usuario_id="user123",
        sessao_versao=1,
        csrf_token=csrf_token,
        expira_minutos=30,
        time_provider=lambda: relogio_falso,
    )

    claims = decodificar_token_sessao(token, time_provider=lambda: relogio_falso)
    assert claims["sub"] == "user123"
    assert claims["ver"] == 1
    assert claims["iat"] == int(relogio_falso)
    assert claims["exp"] == int(relogio_falso + 1800)
    assert claims["csrf"] == hashlib.sha256(csrf_token.encode("utf-8")).hexdigest()


def test_jwt_expirado_rejeitado_com_401():
    tempo_inicial = 1700000000.0
    token = criar_token_sessao(
        usuario_id="user123",
        sessao_versao=1,
        csrf_token="csrf123",
        expira_minutos=10,
        time_provider=lambda: tempo_inicial,
    )

    # Avanca o relogio para alem da expiracao (10 min + 1s = 601s)
    tempo_futuro = tempo_inicial + 601
    with pytest.raises(HTTPException) as exc_info:
        decodificar_token_sessao(token, time_provider=lambda: tempo_futuro)
    assert exc_info.value.status_code == 401
    assert "expirada" in exc_info.value.detail["detalhes"].lower()


def test_jwt_com_alg_none_rejeitado():
    # Cria token forjando alg: none
    header = {"alg": "none", "typ": "JWT"}
    payload = {
        "sub": "user123",
        "ver": 1,
        "exp": int(time.time()) + 3600,
        "csrf": "abc",
    }
    token_none = jwt.encode(payload, key="", algorithm="none", headers=header)

    with pytest.raises(HTTPException) as exc_info:
        decodificar_token_sessao(token_none)
    assert exc_info.value.status_code == 401


def test_jwt_assinado_com_outro_segredo_rejeitado():
    segredo_falso = "outro-segredo-com-mais-de-32-caracteres-invalido!"
    payload = {
        "sub": "user123",
        "ver": 1,
        "exp": int(time.time()) + 3600,
        "csrf": "abc",
    }
    token_adulterado = jwt.encode(payload, segredo_falso, algorithm="HS256")

    with pytest.raises(HTTPException) as exc_info:
        decodificar_token_sessao(token_adulterado)
    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# 4. Token CSRF Double-Submit
# ---------------------------------------------------------------------------
def test_validacao_csrf_sucesso():
    token = gerar_token_csrf()
    hash_esperado = hashlib.sha256(token.encode("utf-8")).hexdigest()
    # Nao lanca excecao
    validar_token_csrf(token, hash_esperado)


def test_validacao_csrf_ausente_ou_vazio_lanca_403():
    with pytest.raises(HTTPException) as exc_info:
        validar_token_csrf(None, "hash_qualquer")
    assert exc_info.value.status_code == 403

    with pytest.raises(HTTPException) as exc_info:
        validar_token_csrf("   ", "hash_qualquer")
    assert exc_info.value.status_code == 403


def test_validacao_csrf_token_divergente_lanca_403():
    token_a = gerar_token_csrf()
    token_b = gerar_token_csrf()
    hash_a = hashlib.sha256(token_a.encode("utf-8")).hexdigest()

    with pytest.raises(HTTPException) as exc_info:
        validar_token_csrf(token_b, hash_a)
    assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# 5. Limitador de Taxa com Relogio Injetavel
# ---------------------------------------------------------------------------
def test_limitador_bloqueia_na_sexta_tentativa_e_libera_apos_janela():
    tempo_atual = 1000.0

    def obter_tempo():
        return tempo_atual

    limitador = LimitadorLogin(limite=5, janela_segundos=60, time_provider=obter_tempo)
    chaves = ["email:alvo@example.test", "ip:192.168.1.1"]

    # 5 tentativas permitidas
    for _ in range(5):
        limitador.verificar_e_registrar(chaves)

    # 6ª tentativa bloqueada com 429 e Retry-After
    with pytest.raises(HTTPException) as exc_info:
        limitador.verificar_e_registrar(chaves)
    assert exc_info.value.status_code == 429
    assert exc_info.value.headers["Retry-After"] == "60"

    # Avanca 30 segundos: continua bloqueado com Retry-After de 30s
    tempo_atual = 1030.0
    with pytest.raises(HTTPException) as exc_info:
        limitador.verificar_e_registrar(chaves)
    assert exc_info.value.status_code == 429
    assert exc_info.value.headers["Retry-After"] == "30"

    # Avanca mais 31 segundos (total 61s): janela expirou, deve liberar
    tempo_atual = 1061.0
    limitador.verificar_e_registrar(chaves)  # Sucesso, sem excecao
