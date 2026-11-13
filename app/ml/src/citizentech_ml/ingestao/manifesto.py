"""Gerenciamento do manifesto de procedência em procedencia.json."""

import json
import os
from pathlib import Path

from citizentech_ml.ingestao.modelos import RegistroProcedencia


def carregar_manifesto(caminho_json: Path) -> list[RegistroProcedencia]:
    """Carrega os registros de procedência existentes."""
    if not caminho_json.exists():
        return []
    conteudo = caminho_json.read_text(encoding="utf-8")
    if not conteudo.strip():
        return []
    dados = json.loads(conteudo)
    if not isinstance(dados, list):
        return []
    return [RegistroProcedencia.from_dict(item) for item in dados]


def salvar_manifesto(caminho_json: Path, registros: list[RegistroProcedencia]) -> None:
    """Salva a lista de registros de procedência em formato JSON UTF-8 sem BOM."""
    caminho_json.parent.mkdir(parents=True, exist_ok=True)
    dados = [r.to_dict() for r in registros]
    caminho_tmp = caminho_json.with_name(f"{caminho_json.name}.tmp")
    try:
        caminho_tmp.write_text(
            json.dumps(dados, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        os.replace(caminho_tmp, caminho_json)
    except Exception:
        if caminho_tmp.exists():
            caminho_tmp.unlink()
        raise


def obter_registro(
    registros: list[RegistroProcedencia], tipo: str, competencia: str
) -> RegistroProcedencia | None:
    """Busca um registro pela combinação (tipo, competencia_arquivo)."""
    for reg in registros:
        if reg.tipo.upper() == tipo.upper() and reg.competencia_arquivo == competencia:
            return reg
    return None


def upsert_registro(
    caminho_json: Path, registro: RegistroProcedencia
) -> list[RegistroProcedencia]:
    """Atualiza ou insere o registro no manifesto e persiste no disco."""
    registros = carregar_manifesto(caminho_json)
    substituido = False
    for i, reg in enumerate(registros):
        if (
            reg.tipo.upper() == registro.tipo.upper()
            and reg.competencia_arquivo == registro.competencia_arquivo
        ):
            registros[i] = registro
            substituido = True
            break
    if not substituido:
        registros.append(registro)
    salvar_manifesto(caminho_json, registros)
    return registros
