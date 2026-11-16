"""Modulo de extracao e gestao de competencias declaradas pelo usuario."""

from citizentech.competencias.catalogo import carregar_catalogo_competencias
from citizentech.competencias.repositorio import competencias_para_comparacao

__all__ = ["carregar_catalogo_competencias", "competencias_para_comparacao"]
