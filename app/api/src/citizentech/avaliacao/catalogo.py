"""Carregamento e formatacao de exercicios e politicas de avaliacao do catalogo (S13)."""

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


def carregar_dados_destino(destino_id: str) -> dict[str, Any] | None:
    """Carrega dados brutos do destino aprovado validando escopo_mvp e revisao humana."""
    catalogo_dir = _obter_diretorio_catalogo()
    arquivo_escopo = catalogo_dir / "escopo_mvp.json"
    if not arquivo_escopo.is_file():
        return None

    conteudo_escopo = json.loads(arquivo_escopo.read_text(encoding="utf-8"))
    destinos_escopo = conteudo_escopo.get("destinos", [])
    if destino_id not in destinos_escopo:
        return None

    destinos_dir = catalogo_dir / "destinos"
    arquivo_yaml = destinos_dir / f"{destino_id}.yaml"
    if not arquivo_yaml.is_file():
        arquivo_yaml = destinos_dir / f"{destino_id}.yml"
        if not arquivo_yaml.is_file():
            return None

    dados = yaml.safe_load(arquivo_yaml.read_text(encoding="utf-8"))
    if not isinstance(dados, dict):
        return None

    revisao = dados.get("revisao_humana") or {}
    if revisao.get("status") != "aprovado":
        return None

    exercicio = dados.get("exercicio")
    politica_raw = dados.get("politica_avaliacao_proposta")
    if not exercicio or not politica_raw:
        return None

    # Mapeamento id_local -> esco_id a partir dos requisitos do YAML
    mapa_id_local_para_esco: dict[str, str] = {}
    for req in dados.get("requisitos") or []:
        if isinstance(req, dict) and req.get("id_local") and req.get("esco_id"):
            mapa_id_local_para_esco[str(req["id_local"])] = str(req["esco_id"])

    # Extrai politica com defaults seguros lidos do YAML
    pesos = politica_raw.get("pesos") or {}
    politica_tentativas = politica_raw.get("politica_tentativas") or {}
    fallback_llm = politica_raw.get("fallback_llm") or {}

    politica = {
        "pesos": {
            "objetiva": float(pesos.get("objetiva", 0.5)),
            "llm": float(pesos.get("llm", 0.5)),
        },
        "minimo_objetiva": float(politica_raw.get("minimo_objetiva", 0.5)),
        "minimo_llm": float(politica_raw.get("minimo_llm", 0.5)),
        "max_tentativas_24h": int(politica_tentativas.get("max_tentativas_24h", 3)),
        "fallback_llm": {
            "comportamento": str(fallback_llm.get("comportamento", "parcial")),
        },
    }

    return {
        "destino_id": destino_id,
        "dados_brutos": dados,
        "exercicio": exercicio,
        "politica": politica,
        "mapa_id_local_para_esco": mapa_id_local_para_esco,
    }


def obter_requisitos_avaliados_destino(dados_destino: dict[str, Any]) -> list[dict[str, str]]:
    """Retorna lista de requisitos avaliados no exercicio mapeados com id_local e esco_id."""
    exercicio = dados_destino["exercicio"]
    mapa = dados_destino["mapa_id_local_para_esco"]
    vistos = set()
    resultado: list[dict[str, str]] = []

    # Questoes objetivas
    for q in exercicio.get("questoes_objetivas") or []:
        for id_local in q.get("requisitos_avaliados") or []:
            if id_local in mapa and id_local not in vistos:
                vistos.add(id_local)
                resultado.append({"id_local": id_local, "esco_id": mapa[id_local]})

    # Questao aberta
    qa = exercicio.get("questao_aberta") or {}
    for id_local in qa.get("requisitos_avaliados") or []:
        if id_local in mapa and id_local not in vistos:
            vistos.add(id_local)
            resultado.append({"id_local": id_local, "esco_id": mapa[id_local]})

    return resultado


def formatar_exercicio_publico(
    dados_destino: dict[str, Any],
    tentativas_restantes_24h: int,
) -> dict[str, Any]:
    """Retorna contrato publico do exercicio com whitelist estrita.
    Nao inclui gabaritos nem justificativas.
    """
    exercicio = dados_destino["exercicio"]
    politica = dados_destino["politica"]

    questoes_publicas = []
    for q in exercicio.get("questoes_objetivas") or []:
        questoes_publicas.append(
            {
                "id": str(q["id"]),
                "enunciado": str(q["enunciado"]),
                "alternativas": {str(k): str(v) for k, v in q.get("alternativas", {}).items()},
            }
        )

    qa = exercicio.get("questao_aberta") or {}
    criterios_publicos = []
    for c in qa.get("rubrica") or []:
        ancoras_formatadas = {str(k): str(v) for k, v in c.get("ancoras", {}).items()}
        criterios_publicos.append(
            {
                "id": str(c["id"]),
                "descricao": str(c.get("descricao", "")),
                "ancoras": ancoras_formatadas,
            }
        )

    return {
        "destino_id": dados_destino["destino_id"],
        "exercicio_id": str(exercicio["id"]),
        "versao": str(exercicio["versao"]),
        "cenario": str(exercicio.get("cenario", "")),
        "questoes_objetivas": questoes_publicas,
        "questao_aberta": {
            "id": str(qa.get("id", "qa1")),
            "enunciado": str(qa.get("enunciado", "")),
            "criterios": criterios_publicos,
        },
        "politica": {
            "pesos": politica["pesos"],
            "minimo_objetiva": politica["minimo_objetiva"],
            "minimo_llm": politica["minimo_llm"],
            "max_tentativas_24h": politica["max_tentativas_24h"],
        },
        "tentativas_restantes_24h": tentativas_restantes_24h,
    }
