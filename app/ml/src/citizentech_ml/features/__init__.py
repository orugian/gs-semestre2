"""Módulo de extração de features e alvos temporais do Novo Caged."""

from __future__ import annotations

from citizentech_ml.features.agregador import (
    DESTINOS_PADRAO,
    UFS_BRASIL,
    agregar_meses_as_of,
    concatenar_pre_agregados,
    extrair_mapa_cbo,
    pre_agregar_microdados,
)
from citizentech_ml.features.cobertura_regras import (
    obter_mapa_cobertura,
    validar_cobertura_sem_conflitos,
    verificar_mes_coberto,
    verificar_observacao_completa_as_of,
)
from citizentech_ml.features.datas import (
    deslocar_mes,
    diferenca_meses,
    gerar_intervalo_meses,
    int_para_mes,
    mes_para_int,
    validar_competencia,
)
from citizentech_ml.features.densidade import (
    calcular_densidade_treino,
    filtrar_series_elegiveis,
    obter_series_elegiveis,
)
from citizentech_ml.features.disponibilidade import (
    filtrar_disponiveis_as_of,
    validar_e_calcular_disponibilidade,
)
from citizentech_ml.features.extracao import (
    COLUNA_ALVO,
    COLUNAS_FEATURES,
    COLUNAS_IDENTIFICADORES,
    construir_painel_features,
)

__all__ = [
    "COLUNA_ALVO",
    "COLUNAS_FEATURES",
    "COLUNAS_IDENTIFICADORES",
    "DESTINOS_PADRAO",
    "UFS_BRASIL",
    "agregar_meses_as_of",
    "calcular_densidade_treino",
    "concatenar_pre_agregados",
    "construir_painel_features",
    "deslocar_mes",
    "diferenca_meses",
    "extrair_mapa_cbo",
    "filtrar_disponiveis_as_of",
    "filtrar_series_elegiveis",
    "gerar_intervalo_meses",
    "int_para_mes",
    "mes_para_int",
    "obter_mapa_cobertura",
    "obter_series_elegiveis",
    "pre_agregar_microdados",
    "validar_cobertura_sem_conflitos",
    "validar_competencia",
    "validar_e_calcular_disponibilidade",
    "verificar_mes_coberto",
    "verificar_observacao_completa_as_of",
]
