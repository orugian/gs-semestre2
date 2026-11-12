"""Leitura da fonte unica de limiares (app/config/limiares.json, D20).

O caminho vem de CITIZENTECH_LIMIARES; sem a variavel, usa o arquivo versionado do repositorio.
A classificacao de risco e implementada na fatia S1.
"""

import json
import os
from pathlib import Path

_PADRAO = Path(__file__).resolve().parents[3] / "config" / "limiares.json"


def caminho_limiares() -> Path:
    return Path(os.environ.get("CITIZENTECH_LIMIARES") or _PADRAO)


def carregar_limiares() -> dict:
    with open(caminho_limiares(), encoding="utf-8") as arquivo:
        return json.load(arquivo)
