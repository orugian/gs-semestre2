"""Leitura da fonte unica de limiares (app/config/limiares.json, D20).

O caminho vem de CITIZENTECH_LIMIARES; sem a variavel, usa o arquivo versionado do repositorio.
A classificacao de risco e implementada na fatia S1.
"""

import json
import math
import os
from pathlib import Path

_PADRAO = Path(__file__).resolve().parents[3] / "config" / "limiares.json"


class MetricaDesconhecida(ValueError):
    """Lancada quando a metrica nao consta no catalogo de limiares."""


class ValorInvalido(ValueError):
    """Lancada quando o valor recebido e invalido (tipo incorreto, bool, NaN, inf, < minimo)."""


def caminho_limiares() -> Path:
    return Path(os.environ.get("CITIZENTECH_LIMIARES") or _PADRAO)


def carregar_limiares() -> dict:
    with open(caminho_limiares(), encoding="utf-8") as arquivo:
        return json.load(arquivo)


def classificar_risco(metrica: str, valor: float, limiares: dict | None = None) -> str:
    """Classifica o risco de uma leitura conforme limiares compartilhados."""
    if limiares is None:
        limiares = carregar_limiares()

    metricas = limiares.get("metricas") if isinstance(limiares, dict) else None
    if not isinstance(metrica, str) or not metricas or metrica not in metricas:
        conhecidas = ", ".join(sorted(metricas.keys())) if metricas else ""
        raise MetricaDesconhecida(
            f"Metrica '{metrica}' desconhecida. Metricas conhecidas: {conhecidas}."
        )

    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValorInvalido(
            f"Valor '{valor}' invalido para metrica '{metrica}'. Esperado int ou float."
        )

    try:
        nao_finito = not math.isfinite(valor)
    except OverflowError:  # inteiro grande demais para float
        nao_finito = True
    if nao_finito:
        raise ValorInvalido(
            f"Valor '{valor}' invalido para metrica '{metrica}'. "
            "Nao sao permitidos NaN ou Infinito."
        )

    config_metrica = metricas[metrica]
    valor_minimo = config_metrica.get("valor_minimo")
    if valor_minimo is not None and valor < valor_minimo:
        raise ValorInvalido(
            f"Valor {valor} abaixo do valor minimo permitido "
            f"({valor_minimo}) para metrica '{metrica}'."
        )

    direcao = config_metrica.get("direcao")
    limiar_critico = config_metrica["critico"]
    limiar_atencao = config_metrica["atencao"]

    if direcao == "maior_pior":
        if valor >= limiar_critico:
            return "critico"
        if valor >= limiar_atencao:
            return "atencao"
        return "normal"
    elif direcao == "menor_pior":
        if valor <= limiar_critico:
            return "critico"
        if valor <= limiar_atencao:
            return "atencao"
        return "normal"

    raise ValueError(f"Direcao desconhecida '{direcao}' para metrica '{metrica}'.")
