"""Carregamento e filtragem do catálogo de destinos (R29)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import yaml

_PADRAO_CATALOGO = Path(__file__).resolve().parents[4] / "catalogo"


def _obter_diretorio_catalogo() -> Path:
    caminho_env = os.environ.get("CITIZENTECH_CATALOGO")
    return Path(caminho_env) if caminho_env else _PADRAO_CATALOGO


def carregar_destinos_aprovados_brutos() -> list[dict[str, Any]]:
    """Carrega destinos aprovados com campos necessários para o domínio de comparação."""
    catalogo_dir = _obter_diretorio_catalogo()
    arquivo_escopo = catalogo_dir / "escopo_mvp.json"
    if not arquivo_escopo.is_file():
        return []

    conteudo_escopo = json.loads(arquivo_escopo.read_text(encoding="utf-8"))
    destinos_escopo = conteudo_escopo.get("destinos", [])

    destinos_dir = catalogo_dir / "destinos"
    destinos_aprovados: list[dict[str, Any]] = []

    for destino_id in destinos_escopo:
        arquivo_yaml = destinos_dir / f"{destino_id}.yaml"
        if not arquivo_yaml.is_file():
            arquivo_yaml = destinos_dir / f"{destino_id}.yml"
            if not arquivo_yaml.is_file():
                continue

        dados = yaml.safe_load(arquivo_yaml.read_text(encoding="utf-8"))
        if not isinstance(dados, dict):
            continue

        revisao = dados.get("revisao_humana") or {}
        if revisao.get("status") != "aprovado":
            continue

        destinos_aprovados.append(dados)

    return destinos_aprovados


def carregar_destinos_publicos() -> list[dict[str, Any]]:
    """Retorna destinos aprovados no contrato público com whitelist estrita."""
    destinos_brutos = carregar_destinos_aprovados_brutos()
    itens: list[dict[str, Any]] = []

    for dados in destinos_brutos:
        destino_id = dados.get("destino_id", "")
        nome = dados.get("nome", "")

        populacao = dados.get("populacao") or {}
        descricao = populacao.get("descricao") if isinstance(populacao, dict) else None

        requisitos_saida: list[dict[str, Any]] = []
        for req in dados.get("requisitos") or []:
            if not isinstance(req, dict):
                continue
            id_local = req.get("id_local", "")
            esco_id = req.get("esco_id", "")
            titulo = req.get("titulo_oficial") or req.get("titulo", "")
            obrigatorio = (
                req.get("obrigatorio_proposto")
                if "obrigatorio_proposto" in req
                else req.get("obrigatorio", False)
            )
            requisitos_saida.append({
                "id_local": str(id_local),
                "esco_id": str(esco_id),
                "titulo": str(titulo),
                "obrigatorio": bool(obrigatorio),
            })

        itens.append({
            "destino_id": str(destino_id),
            "nome": str(nome),
            "descricao": descricao,
            "requisitos": requisitos_saida,
        })

    return itens
