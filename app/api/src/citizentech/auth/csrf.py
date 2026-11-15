"""Geracao e validacao double-submit de tokens anti-CSRF (R20)."""

import hashlib
import hmac
import secrets

from fastapi import HTTPException, status


def gerar_token_csrf() -> str:
    """Gera um token CSRF seguro e imprevisivel."""
    return secrets.token_urlsafe(32)


def validar_token_csrf(token_header: str | None, hash_esperado: str) -> None:
    """Valida o token CSRF recebido no cabecalho contra o hash registrado no JWT.

    Usa comparacao em tempo constante (hmac.compare_digest).
    """
    if not token_header or not token_header.strip():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "erro": "Acesso proibido",
                "detalhes": "Token CSRF invalido ou ausente.",
            },
        )

    hash_recebido = hashlib.sha256(token_header.strip().encode("utf-8")).hexdigest()
    if not hmac.compare_digest(hash_recebido, hash_esperado):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "erro": "Acesso proibido",
                "detalhes": "Token CSRF invalido ou ausente.",
            },
        )
