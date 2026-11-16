"""Modelos Pydantic para requisicoes e respostas da API de plano."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class CaminhoRequisicao(BaseModel):
    model_config = ConfigDict(extra="forbid")

    destino_id: str
    comparacao_id: str | None = None


class CheckpointItem(BaseModel):
    id: str | None = None
    ordem: int
    tipo: Literal["estudar", "praticar", "demonstrar", "laboratorio", "exercicio"]
    titulo: str
    descricao: str | None = None
    criterio_conclusao: str | None = None
    requisito_id_local: str | None = None
    estado_origem: str | None = None
    motivo_origem: str | None = None
    obrigatorio: bool
    exercicio_id: str | None = None
    status: Literal["pendente", "em_andamento", "concluido"] = "pendente"
    atualizado_em: str | None = None


class PlanoDetalhado(BaseModel):
    plano_id: str
    gerado_em: str
    destino_id: str
    nome: str
    versao_catalogo: str
    regra: str
    explicacao_regra: str
    ja_demonstrados: list[str]
    checkpoints: list[CheckpointItem]
    observacoes: list[str]
    aviso: str


class CaminhoResposta(BaseModel):
    caminho_id: str
    destino_id: str
    comparacao_id: str | None = None
    criado_em: str
    plano: PlanoDetalhado


class AtualizarCheckpointRequisicao(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["pendente", "em_andamento", "concluido"]
