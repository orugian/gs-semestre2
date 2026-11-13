"""Seguranca e autenticacao por chave de dispositivo exclusiva (D24)."""

import os
import secrets

from fastapi import HTTPException, Request, status


def verificar_chave_dispositivo(request: Request) -> str:
    """Valida a chave do dispositivo. Operacao fail-closed: sem chave configurada, rejeita tudo."""
    chave_esperada = os.environ.get("DEVICE_KEY")
    if not chave_esperada or not chave_esperada.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "erro": "Nao autorizado",
                "detalhes": "Chave de dispositivo nao configurada no servidor.",
            },
        )

    chave_recebida = request.headers.get("X-Device-Key")
    if not chave_recebida:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "erro": "Nao autorizado",
                "detalhes": "Chave de dispositivo ausente ou invalida.",
            },
        )

    try:
        valido = secrets.compare_digest(chave_recebida, chave_esperada)
    except Exception:
        valido = False

    if not valido:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "erro": "Nao autorizado",
                "detalhes": "Chave de dispositivo ausente ou invalida.",
            },
        )

    return chave_recebida

