"""Esquemas Pydantic para rotas de avaliacao e tentativas (S13)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CriarTentativaRequisicao(BaseModel):
    model_config = ConfigDict(extra="forbid")

    destino_id: str
    exercicio_id: str
    respostas_objetivas: dict[str, str]
    resposta_aberta: str = Field(..., min_length=20, max_length=4000)


class RegistrarDiscordoRequisicao(BaseModel):
    model_config = ConfigDict(extra="forbid")

    motivo: str = Field(..., min_length=10, max_length=1000)


class QuestaoObjetivaCorrecao(BaseModel):
    id: str
    resposta: str
    correta: bool
    gabarito: str
    justificativa: str


class ResumoObjetivaResposta(BaseModel):
    acertos: int
    total: int
    nota: float
    questoes: list[QuestaoObjetivaCorrecao]


class CriterioAvaliadoResposta(BaseModel):
    id: str
    nivel: int
    justificativa: str
    trecho_resposta: str


class ResumoAbertaResposta(BaseModel):
    status: str
    nota: float | None
    modelo: str | None
    em_cache: bool
    criterios: list[CriterioAvaliadoResposta]


class RequisitoAvaliadoItem(BaseModel):
    id_local: str
    esco_id: str


class TentativaResposta(BaseModel):
    tentativa_id: str
    destino_id: str
    exercicio_id: str
    exercicio_versao: str
    criado_em: str
    objetiva: ResumoObjetivaResposta
    aberta: ResumoAbertaResposta
    nota_final: float | None
    resultado: str
    requisitos_avaliados: list[RequisitoAvaliadoItem]
    tentativas_restantes_24h: int
    aviso: str


class DiscordoResposta(BaseModel):
    tentativa_id: str
    discordo_em: str
    motivo: str
    status_contestacao: str = "registrada"


class ItemResumoTentativa(BaseModel):
    tentativa_id: str
    destino_id: str
    exercicio_id: str
    exercicio_versao: str
    criado_em: str
    nota_objetiva: float
    status_aberta: str
    nota_llm: float | None = None
    nota_final: float | None = None
    resultado: str
    discordo_em: str | None = None


class ListarTentativasResposta(BaseModel):
    itens: list[ItemResumoTentativa]
    ultima: str | None
    melhor: str | None
