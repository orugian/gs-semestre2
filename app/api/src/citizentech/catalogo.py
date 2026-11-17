"""Modulo centralizado de catalogo de destinos e competencias (S17).

Centraliza a descoberta, resolucao de caminhos, carregamento de YAMLs homologados
e normalizacao de requisitos com precedencia unica.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import yaml

from citizentech.erros import ServicoIndisponivel

_PADRAO_CATALOGO = Path(__file__).resolve().parents[3] / "catalogo"


def diretorio_catalogo() -> Path:
    """Retorna o diretorio do catalogo (respeita CITIZENTECH_CATALOGO ou fallback)."""
    caminho_env = os.environ.get("CITIZENTECH_CATALOGO")
    return Path(caminho_env) if caminho_env else _PADRAO_CATALOGO


def caminho_escopo_mvp() -> Path:
    """Retorna o caminho para escopo_mvp.json (respeita CITIZENTECH_ESCOPO_MVP)."""
    caminho_env = os.environ.get("CITIZENTECH_ESCOPO_MVP")
    if caminho_env:
        return Path(caminho_env)
    return diretorio_catalogo() / "escopo_mvp.json"


def carregar_escopo_mvp() -> dict[str, Any]:
    """Carrega o arquivo escopo_mvp.json com validacao de existencia."""
    caminho = caminho_escopo_mvp()
    if not caminho.is_file():
        raise ServicoIndisponivel(
            detalhes="Catalogo de escopo MVP nao encontrado.",
            erro="Servico indisponivel",
        )
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ServicoIndisponivel(
            detalhes="Falha ao carregar arquivo de escopo MVP.",
            erro="Servico indisponivel",
        ) from exc


def _carregar_yaml_se_aprovado(destinos_dir: Path, destino_id: str) -> dict[str, Any] | None:
    arquivo_yaml = destinos_dir / f"{destino_id}.yaml"
    if not arquivo_yaml.is_file():
        arquivo_yaml = destinos_dir / f"{destino_id}.yml"
        if not arquivo_yaml.is_file():
            return None

    try:
        dados = yaml.safe_load(arquivo_yaml.read_text(encoding="utf-8"))
    except Exception:
        return None

    if not isinstance(dados, dict):
        return None

    revisao = dados.get("revisao_humana") or {}
    if revisao.get("status") != "aprovado":
        return None

    return dados


def carregar_destinos_aprovados() -> list[dict[str, Any]]:
    """Carrega destinos aprovados do catalogo (escopo_mvp.json + YAML aprovados, .yaml/.yml)."""
    try:
        conteudo_escopo = carregar_escopo_mvp()
    except (ServicoIndisponivel, Exception):
        return []

    destinos_escopo = conteudo_escopo.get("destinos", [])
    catalogo_dir = diretorio_catalogo()
    destinos_dir = catalogo_dir / "destinos"
    destinos_aprovados: list[dict[str, Any]] = []

    for destino_id in destinos_escopo:
        dados = _carregar_yaml_se_aprovado(destinos_dir, destino_id)
        if dados is not None:
            destinos_aprovados.append(dados)

    return destinos_aprovados


def carregar_destino_aprovado(destino_id: str) -> dict[str, Any] | None:
    """Carrega um destino aprovado especifico se presente no escopo e com status aprovado."""
    try:
        conteudo_escopo = carregar_escopo_mvp()
    except (ServicoIndisponivel, Exception):
        return None

    destinos_escopo = conteudo_escopo.get("destinos", [])
    if destino_id not in destinos_escopo:
        return None

    catalogo_dir = diretorio_catalogo()
    destinos_dir = catalogo_dir / "destinos"
    return _carregar_yaml_se_aprovado(destinos_dir, destino_id)


def normalizar_requisito(req: dict[str, Any]) -> dict[str, Any]:
    """Normaliza requisito com UMA precedencia: obrigatorio_proposto se presente, senao
    obrigatorio.
    """
    id_local = req.get("id_local", "")
    esco_id = req.get("esco_id", "")
    titulo = req.get("titulo_oficial") or req.get("titulo", "")
    obrigatorio = (
        req.get("obrigatorio_proposto")
        if "obrigatorio_proposto" in req
        else req.get("obrigatorio", False)
    )
    return {
        "id_local": str(id_local) if id_local is not None else "",
        "esco_id": str(esco_id) if esco_id is not None else "",
        "titulo": str(titulo),
        "obrigatorio": bool(obrigatorio),
    }
