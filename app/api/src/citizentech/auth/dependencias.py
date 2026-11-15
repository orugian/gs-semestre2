"""Dependencias do FastAPI para extracao de sessao autenticada e validacao CSRF."""

from typing import Any

from fastapi import HTTPException, Request, status

from citizentech.auth.csrf import validar_token_csrf
from citizentech.auth.repositorio import buscar_por_id
from citizentech.auth.tokens import decodificar_token_sessao


def obter_usuario_logado(request: Request) -> dict[str, Any]:
    """Extrai e valida o usuario logado a partir do cookie de sessao JWT."""
    token = request.cookies.get("sessao")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "erro": "Nao autenticado",
                "detalhes": "Cookie de sessao ausente.",
            },
        )

    claims = decodificar_token_sessao(token)
    usuario_id = claims["sub"]
    usuario = buscar_por_id(usuario_id)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "erro": "Nao autenticado",
                "detalhes": "Usuario nao encontrado.",
            },
        )

    # Logout real: verifica se a versao do token corresponde a versao atual no banco
    if usuario["sessao_versao"] != claims["ver"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "erro": "Nao autenticado",
                "detalhes": "Sessao encerrada previamente (logout realizado).",
            },
        )

    # Armazena os claims no objeto usuario para uso pelas dependencias seguintes
    usuario["_claims"] = claims
    return usuario


def exigir_csrf(request: Request) -> None:
    """Valida o token CSRF double-submit em metodos mutaveis autenticados por cookie."""
    token = request.cookies.get("sessao")
    if not token:
        # Se nao ha cookie de sessao, a rota respondera 401 pela autenticacao
        return

    claims = decodificar_token_sessao(token)
    token_csrf = request.headers.get("x-csrf-token")
    validar_token_csrf(token_csrf, claims["csrf"])
