"""Catalogo fechado de competencias ESCO para destinos homologados."""

from __future__ import annotations

import json
import os
from pathlib import Path

import yaml

_PADRAO_CATALOGO = Path(__file__).resolve().parents[4] / "catalogo"


def carregar_catalogo_competencias() -> dict[str, str]:
    """Carrega o catalogo fechado de competencias (esco_id -> titulo_oficial).

    Regra R29 / revisao: Le escopo_mvp.json e carrega apenas os destinos cujo
    revisao_humana.status == 'aprovado'. Nao usa status_rubricas de escopo_mvp.json.
    """
    caminho_env = os.environ.get("CITIZENTECH_CATALOGO")
    catalogo_dir = Path(caminho_env) if caminho_env else _PADRAO_CATALOGO

    arquivo_escopo = catalogo_dir / "escopo_mvp.json"
    if not arquivo_escopo.is_file():
        return {}

    conteudo_escopo = json.loads(arquivo_escopo.read_text(encoding="utf-8"))
    destinos = conteudo_escopo.get("destinos", [])

    catalogo: dict[str, str] = {}
    destinos_dir = catalogo_dir / "destinos"

    for destino_id in destinos:
        arquivo_yaml = destinos_dir / f"{destino_id}.yaml"
        if not arquivo_yaml.is_file():
            arquivo_yaml = destinos_dir / f"{destino_id}.yml"
            if not arquivo_yaml.is_file():
                continue

        dados_destino = yaml.safe_load(arquivo_yaml.read_text(encoding="utf-8"))
        if not isinstance(dados_destino, dict):
            continue

        revisao_humana = dados_destino.get("revisao_humana") or {}
        if revisao_humana.get("status") != "aprovado":
            continue

        requisitos = dados_destino.get("requisitos") or []
        for req in requisitos:
            if not isinstance(req, dict):
                continue
            esco_id = req.get("esco_id")
            titulo = req.get("titulo_oficial") or req.get("titulo") or ""
            if esco_id:
                catalogo[esco_id] = titulo

    return catalogo
