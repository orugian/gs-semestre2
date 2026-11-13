"""Módulo de ingestão do Novo Caged."""

from citizentech_ml.ingestao.baixador import Baixador, BaixadorCurl
from citizentech_ml.ingestao.cobertura import cobertura
from citizentech_ml.ingestao.consolidacao import consolidar_mensal
from citizentech_ml.ingestao.ingestor import ingerir_arquivo, ingerir_periodo
from citizentech_ml.ingestao.modelos import (
    Fonte,
    Ocupacoes,
    RegistroProcedencia,
    ResumoIngestao,
)
from citizentech_ml.ingestao.ocupacoes import carregar_ocupacoes

__all__ = [
    "Baixador",
    "BaixadorCurl",
    "Fonte",
    "Ocupacoes",
    "RegistroProcedencia",
    "ResumoIngestao",
    "carregar_ocupacoes",
    "cobertura",
    "consolidar_mensal",
    "ingerir_arquivo",
    "ingerir_periodo",
]
