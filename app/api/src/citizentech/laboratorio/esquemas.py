"""Esquemas Pydantic para o modulo de laboratorio."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class RelatoInfo(BaseModel):
    texto_redigido: str | None = None
    status: Literal["nenhum", "pendente", "enviado"] = "nenhum"


class CriarSessaoResposta(BaseModel):
    id: str
    codigo: str
    status: Literal["ativa"] = "ativa"
    criado_em: str
    expira_em: str
    instrucoes: str


class SessaoLaboratorioResposta(BaseModel):
    id: str
    codigo: str
    status: Literal["ativa", "encerrada", "expirada"]
    criado_em: str
    expira_em: str
    instrucoes: str
    relato: RelatoInfo
    leituras: list[dict[str, Any]] = Field(default_factory=list)
    indicadores: dict[str, Any] = Field(default_factory=dict)


class RegistrarRelatoRequisicao(BaseModel):
    relato: str


class RegistrarRelatoResposta(BaseModel):
    texto_redigido: str
    status: Literal["pendente"] = "pendente"
