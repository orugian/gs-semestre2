"""Rotas do catálogo público de destinos (/destinos)."""

from typing import Any

from fastapi import APIRouter, status

from citizentech.destinos.catalogo import carregar_destinos_publicos

router = APIRouter(tags=["destinos"])


@router.get("/destinos", status_code=status.HTTP_200_OK)
def listar_destinos() -> dict[str, Any]:
    """Retorna a lista de destinos aprovados no catálogo MVP (R29)."""
    return {"itens": carregar_destinos_publicos()}
