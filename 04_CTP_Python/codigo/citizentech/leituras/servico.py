"""Servico de leituras de telemetria CTP.

Centraliza regras de listagem com estado da outbox e calculo de indicadores.
"""

import math
from typing import Any

from citizentech.erros import RequisicaoInvalida
from citizentech.leituras.repositorio import ler_todas_leituras
from citizentech.outbox.banco import obter_mapa_estados


def listar_leituras_com_estado(sessao: str | None = None) -> list[dict[str, Any]]:
    """Mescla leituras do CSV com o estado da outbox SQLite e filtra opcionalmente por sessao."""
    todos = ler_todas_leituras()
    mapa_estados = obter_mapa_estados()
    if mapa_estados:
        for r in todos:
            if r.get("evento_id") in mapa_estados:
                r["estado"] = mapa_estados[r["evento_id"]]

    if sessao is not None and sessao != "":
        todos = [r for r in todos if r.get("sessao_laboratorio_id") == sessao]

    return todos


def calcular_indicadores(leituras: list[dict[str, Any]]) -> dict[str, Any]:
    """Calcula indicadores estatisticos sobre uma lista de leituras."""
    contagem = len(leituras)
    if contagem == 0:
        return {
            "contagem": 0,
            "total_alertas": 0,
            "media": None,
            "maximo": None,
            "minimo": None,
        }
    valores = [r["valor"] for r in leituras]
    total_alertas = sum(1 for r in leituras if r.get("alerta") is True)

    # Media estavel (evita overflow de soma intermediaria com valores extremos)
    media = 0.0
    for i, v in enumerate(valores, start=1):
        media += (v - media) / i

    val_max = max(valores)
    val_min = min(valores)

    if not math.isfinite(media) or not math.isfinite(val_max) or not math.isfinite(val_min):
        raise RequisicaoInvalida(
            detalhes="Overflow numerico no calculo de estatisticas dos valores.",
            erro="Erro no calculo de indicadores",
        )

    try:
        media_arredondada = round(media, 2)
        max_arredondado = round(val_max, 2)
        min_arredondado = round(val_min, 2)
    except OverflowError:
        media_arredondada = media
        max_arredondado = val_max
        min_arredondado = val_min

    return {
        "contagem": contagem,
        "total_alertas": total_alertas,
        "media": media_arredondada,
        "maximo": max_arredondado,
        "minimo": min_arredondado,
    }
