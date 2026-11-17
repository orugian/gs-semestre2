"""Carregamento e filtragem do catalogo de destinos (R29)."""

from __future__ import annotations

from typing import Any

from citizentech.catalogo import (
    carregar_destinos_aprovados,
    normalizar_requisito,
)
from citizentech.catalogo import (
    diretorio_catalogo as _obter_diretorio_catalogo,
)

# Mantem compatibilidade com importadores legados
carregar_destinos_aprovados_brutos = carregar_destinos_aprovados
diretorio_catalogo = _obter_diretorio_catalogo

__all__ = [
    "carregar_destinos_aprovados_brutos",
    "carregar_destinos_publicos",
    "diretorio_catalogo",
]


def carregar_destinos_publicos() -> list[dict[str, Any]]:
    """Retorna destinos aprovados no contrato publico com whitelist estrita."""
    destinos_brutos = carregar_destinos_aprovados()
    itens: list[dict[str, Any]] = []

    for dados in destinos_brutos:
        destino_id = dados.get("destino_id", "")
        nome = dados.get("nome", "")

        populacao = dados.get("populacao") or {}
        descricao = populacao.get("descricao") if isinstance(populacao, dict) else None

        requisitos_saida = [
            normalizar_requisito(req)
            for req in (dados.get("requisitos") or [])
            if isinstance(req, dict)
        ]

        itens.append({
            "destino_id": str(destino_id),
            "nome": str(nome),
            "descricao": descricao,
            "requisitos": requisitos_saida,
        })

    return itens
