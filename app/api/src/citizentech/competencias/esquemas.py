"""Esquemas Pydantic para rotas de competencias."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ExtrairCompetenciasRequisicao(BaseModel):
    """Requisicao para extracao de competencias."""

    model_config = ConfigDict(extra="forbid")
    curriculo_id: str = Field(..., min_length=1)


class AtualizarCompetenciaRequisicao(BaseModel):
    """Requisicao para confirmacao/rejeicao de competencia."""

    model_config = ConfigDict(extra="forbid")
    acao: Literal["confirmar", "rejeitar", "nao_possuo"]
    trecho_origem: str | None = Field(None, max_length=500)
