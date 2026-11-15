"""Geracao, assinatura e validacao de tokens JWT de sessao."""

import hashlib
import math
import os
import time
import uuid
from collections.abc import Callable
from typing import Any

import jwt
from fastapi import HTTPException, status

from citizentech.erros import ErroSegurancaIndisponivel


def obter_jwt_secret() -> str:
    """Recupera e valida o segredo de assinatura JWT.

    Fail-closed: se ausente ou com menos de 32 caracteres, lanca excecao para
    retorno 503, sem nunca adotar valor padrao.
    """
    secret = os.environ.get("JWT_SECRET")
    if not secret or len(secret) < 32:
        raise ErroSegurancaIndisponivel(
            "Configuracao de seguranca ausente ou invalida "
            "(JWT_SECRET deve ter ao menos 32 caracteres)."
        )
    return secret


def obter_expiracao_minutos() -> int:
    """Obtem o tempo de expiracao do token em minutos (padrao 60).

    Fail-closed: se invalido, <= 0 ou excede limites representaveis, lanca
    ErroSegurancaIndisponivel para retorno 503. Padrao 60 apenas quando ausente.
    """
    raw = os.environ.get("JWT_EXPIRA_MINUTOS")
    if raw is None or raw.strip() == "":
        return 60

    try:
        val = int(raw.strip())
    except (ValueError, TypeError) as err:
        raise ErroSegurancaIndisponivel(
            "Configuracao de seguranca invalida (JWT_EXPIRA_MINUTOS deve ser inteiro positivo)."
        ) from err

    if val <= 0:
        raise ErroSegurancaIndisponivel(
            "Configuracao de seguranca invalida (JWT_EXPIRA_MINUTOS deve ser maior que zero)."
        )

    # Evita overflow em timestamp e representacao de tempo (limite do ano 9999 UTC)
    # 253402300799 eh 9999-12-31T23:59:59Z
    if val > (253402300799 // 60):
        raise ErroSegurancaIndisponivel(
            "Configuracao de seguranca invalida (JWT_EXPIRA_MINUTOS excede o limite representavel)."
        )

    return val


def criar_token_sessao(
    usuario_id: str,
    sessao_versao: int,
    csrf_token: str,
    expira_minutos: int | None = None,
    time_provider: Callable[[], float] = time.time,
) -> str:
    """Gera um JWT HS256 contendo os claims de sessao e o hash do token CSRF."""
    secret = obter_jwt_secret()
    if expira_minutos is None:
        expira_minutos = obter_expiracao_minutos()

    agora = int(time_provider())
    expira_em = agora + (expira_minutos * 60)
    csrf_hash = hashlib.sha256(csrf_token.encode("utf-8")).hexdigest()

    claims = {
        "sub": usuario_id,
        "iat": agora,
        "exp": expira_em,
        "jti": uuid.uuid4().hex,
        "ver": sessao_versao,
        "csrf": csrf_hash,
    }

    return jwt.encode(claims, secret, algorithm="HS256")


def decodificar_token_sessao(
    token: str,
    time_provider: Callable[[], float] = time.time,
) -> dict[str, Any]:
    """Decodifica e valida o token JWT.

    Aceita SOMENTE HS256. Rejeita tokens com alg: none, expirados, adulterados,
    assinados com outro segredo ou com claims/tipos invalidos.
    """
    secret = obter_jwt_secret()

    try:
        # Decodifica estritamente com HS256
        claims = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"verify_exp": False},  # validamos com o time_provider injetavel
        )
    except jwt.InvalidTokenError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "erro": "Nao autenticado",
                "detalhes": "Sessao invalida ou expirada.",
            },
        ) from err

    # Validacao de presenca de todos os claims obrigatorios (sub, iat, exp, jti, ver, csrf)
    claims_obrigatorios = ("sub", "iat", "exp", "jti", "ver", "csrf")
    for claim in claims_obrigatorios:
        if claim not in claims or claims[claim] is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "erro": "Nao autenticado",
                    "detalhes": f"Claim obrigatorio '{claim}' ausente.",
                },
            )

    # Validacao estrita dos tipos basicos dos claims
    sub = claims["sub"]
    if not isinstance(sub, str) or not sub.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "erro": "Nao autenticado",
                "detalhes": "Claim 'sub' invalido.",
            },
        )

    jti = claims["jti"]
    if not isinstance(jti, str) or not jti.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "erro": "Nao autenticado",
                "detalhes": "Claim 'jti' invalido.",
            },
        )

    csrf = claims["csrf"]
    if not isinstance(csrf, str) or not csrf.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "erro": "Nao autenticado",
                "detalhes": "Claim 'csrf' invalido.",
            },
        )

    ver = claims["ver"]
    if not isinstance(ver, int) or isinstance(ver, bool):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "erro": "Nao autenticado",
                "detalhes": "Claim 'ver' invalido.",
            },
        )

    iat = claims["iat"]
    if (
        not isinstance(iat, (int, float))
        or isinstance(iat, bool)
        or not math.isfinite(iat)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "erro": "Nao autenticado",
                "detalhes": "Claim 'iat' invalido.",
            },
        )

    exp = claims["exp"]
    if (
        not isinstance(exp, (int, float))
        or isinstance(exp, bool)
        or not math.isfinite(exp)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "erro": "Nao autenticado",
                "detalhes": "Claim 'exp' invalido.",
            },
        )

    # Validacao manual de expiracao compativel com relogio injetado
    agora = int(time_provider())
    if agora >= exp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "erro": "Nao autenticado",
                "detalhes": "Sessao expirada.",
            },
        )

    return claims
