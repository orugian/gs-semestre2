"""Catalogo fechado de competencias ESCO para destinos homologados."""

from __future__ import annotations

from citizentech.catalogo import carregar_destinos_aprovados


def carregar_catalogo_competencias() -> dict[str, str]:
    """Carrega o catalogo fechado de competencias (esco_id -> titulo_oficial).

    Regra R29 / revisao: Le escopo_mvp.json e carrega apenas os destinos cujo
    revisao_humana.status == 'aprovado'. Nao usa status_rubricas de escopo_mvp.json.
    """
    destinos = carregar_destinos_aprovados()
    catalogo: dict[str, str] = {}

    for dados_destino in destinos:
        requisitos = dados_destino.get("requisitos") or []
        for req in requisitos:
            if not isinstance(req, dict):
                continue
            esco_id = req.get("esco_id")
            titulo = req.get("titulo_oficial") or req.get("titulo") or ""
            if esco_id:
                catalogo[esco_id] = titulo

    return catalogo
