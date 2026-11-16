"""Esquemas Pydantic para as respostas das rotas de mercado."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ReferenciaTemporal(BaseModel):
    """Intervalo de competências coberto pela seção."""

    inicio: str
    fim: str


class ObservadoSerieItem(BaseModel):
    """Ponto de dado observado no tempo."""

    competencia: str
    valor: float | None = None


class PrevistoSerieItem(BaseModel):
    """Ponto de dado previsto e realizado no tempo."""

    competencia_origem: str
    previsao: float
    realizado: float


class ObservadoSecao(BaseModel):
    """Metadados e série histórica observada (T17)."""

    natureza: str
    fonte: str
    populacao: str
    unidade: str
    referencia_temporal: ReferenciaTemporal
    serie: list[ObservadoSerieItem]


class PrevistoSecao(BaseModel):
    """Metadados e série de previsão retrospectiva (T17)."""

    natureza: str
    fonte: str
    populacao: str
    unidade: str
    referencia_temporal: ReferenciaTemporal
    modelo_exibido: str
    status_promocao: str
    serie: list[PrevistoSerieItem]


class ContextoRegionalSecao(BaseModel):
    """Metadados e série agregada observada da macrorregião (D04a/T06)."""

    natureza: str
    fonte: str
    populacao: str
    unidade: str
    referencia_temporal: ReferenciaTemporal
    regiao: str
    serie: list[ObservadoSerieItem]


class AbstencaoSecao(BaseModel):
    """Abstenção explícita para séries com densidade insuficiente (D04a/T06)."""

    motivo: str
    media_alvo_treino: float | None
    limite_minimo: float
    contexto_regional: ContextoRegionalSecao


class AmostraAdzuna(BaseModel):
    """Situação da coleta Adzuna na versão atual (D05a)."""

    disponivel: bool
    natureza: str
    motivo: str


class RespostaMercado(BaseModel):
    """Resposta principal da rota pública GET /mercado/{destino}."""

    destino: str
    uf: str
    uf_codigo: str
    observado: ObservadoSecao
    previsto: PrevistoSecao | None = None
    abstencao: AbstencaoSecao | None = None
    amostra_adzuna: AmostraAdzuna
    avisos: list[str]


class CriterioPromocao(BaseModel):
    """Critério e status de promoção técnica dos modelos."""

    criterio: str
    status: str
    modelo_exibido: str


class ModeloPainelTecnico(BaseModel):
    """Visão técnica comparativa de um modelo no painel R06."""

    id: str
    nome: str
    tipo: str
    promovido: bool
    exibido_ao_usuario: bool
    metricas_validacao_global: dict[str, Any]
    metricas_cv_treino: dict[str, Any]
    metricas_serie: dict[str, Any] | None = None
    previsoes_validacao: list[dict[str, Any]]
    model_card: dict[str, Any]


class RespostaModelos(BaseModel):
    """Resposta do painel técnico comparativo GET /mercado/{destino}/modelos (R06)."""

    destino: str
    uf: str
    uf_codigo: str
    elegivel: bool
    motivo_densidade: str
    criterio_promocao: CriterioPromocao
    modelos: list[ModeloPainelTecnico]
    avisos: list[str]
