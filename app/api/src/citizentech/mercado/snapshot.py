"""Carregamento e validação de integridade do snapshot de mercado."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from citizentech.catalogo import carregar_escopo_mvp
from citizentech.erros import ServicoIndisponivel

__all__ = [
    "DIRETORIO_PADRAO_SNAPSHOT",
    "REGIAO_POR_DIGITO",
    "UF_PARA_IBGE",
    "carregar_escopo_mvp",
    "carregar_snapshot_mercado",
]

# Diretório padrão do snapshot público de mercado versionado no repositório
DIRETORIO_PADRAO_SNAPSHOT: Path = (
    Path(__file__).resolve().parents[4] / "dados_publicos" / "mercado" / "20261116_r29_aceite"
)

# Mapeamento oficial de UFs para códigos IBGE de 2 dígitos
UF_PARA_IBGE: dict[str, str] = {
    "AC": "12",
    "AL": "27",
    "AP": "16",
    "AM": "13",
    "BA": "29",
    "CE": "23",
    "DF": "53",
    "ES": "32",
    "GO": "52",
    "MA": "21",
    "MT": "51",
    "MS": "50",
    "MG": "31",
    "PA": "15",
    "PB": "25",
    "PR": "41",
    "PE": "26",
    "PI": "22",
    "RJ": "33",
    "RN": "24",
    "RS": "43",
    "RO": "11",
    "RR": "14",
    "SC": "42",
    "SP": "35",
    "SE": "28",
    "TO": "17",
}

# Região geográfica pelo primeiro dígito do código IBGE
REGIAO_POR_DIGITO: dict[str, str] = {
    "1": "Norte",
    "2": "Nordeste",
    "3": "Sudeste",
    "4": "Sul",
    "5": "Centro-Oeste",
}

_cache_snapshot: dict[str, Any] | None = None
_cache_info: tuple[str, float, int] | None = None


def carregar_snapshot_mercado() -> dict[str, Any]:
    """Carrega snapshot e manifesto validando integridade SHA-256 e schema_version."""
    caminho_var = os.environ.get("CITIZENTECH_MERCADO_SNAPSHOT")
    if caminho_var and caminho_var.strip():
        p_dir = Path(caminho_var)
    else:
        p_dir = Path(DIRETORIO_PADRAO_SNAPSHOT)

    p_man = p_dir / "manifesto.json"
    p_snap = p_dir / "snapshot_mercado.json"

    if not p_man.exists() or not p_snap.exists():
        raise ServicoIndisponivel(
            "Arquivos de manifesto ou snapshot de mercado nao encontrados."
        )

    try:
        stat_snap = p_snap.stat()
        info_atual = (str(p_snap), stat_snap.st_mtime, stat_snap.st_size)
    except Exception as exc:
        raise ServicoIndisponivel(
            "Falha ao inspecionar atributos do snapshot de mercado."
        ) from exc

    global _cache_snapshot, _cache_info
    if _cache_snapshot is not None and _cache_info == info_atual:
        return _cache_snapshot

    try:
        conteudo_man = p_man.read_text(encoding="utf-8")
        man = json.loads(conteudo_man)
    except Exception as exc:
        raise ServicoIndisponivel(
            "Manifesto de mercado malformado ou ilegivel."
        ) from exc

    if not isinstance(man, dict) or man.get("schema_version") != "1.0":
        raise ServicoIndisponivel(
            "Versao de esquema do snapshot de mercado incompativel."
        )

    sha_esperado = man.get("sha256")
    if not sha_esperado:
        raise ServicoIndisponivel("Hash SHA-256 ausente no manifesto de mercado.")

    try:
        bytes_snap = p_snap.read_bytes()
    except Exception as exc:
        raise ServicoIndisponivel(
            "Falha ao ler dados brutos do snapshot de mercado."
        ) from exc

    sha_calculado = hashlib.sha256(bytes_snap).hexdigest()
    if sha_calculado.lower() != str(sha_esperado).lower():
        raise ServicoIndisponivel("Integridade do snapshot de mercado violada.")

    try:
        snapshot = json.loads(bytes_snap.decode("utf-8"))
    except Exception as exc:
        raise ServicoIndisponivel(
            "Conteudo JSON do snapshot de mercado corrompido."
        ) from exc

    _cache_snapshot = snapshot
    _cache_info = info_atual
    return snapshot
