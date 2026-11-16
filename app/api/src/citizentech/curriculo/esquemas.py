"""Esquemas Pydantic para curriculo e experiencias."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

AVISO_REDACAO_PADRAO = (
    "A redação automática é parcial: revise o texto e remova qualquer "
    "dado pessoal restante antes de confirmar."
)


class RedacoesContagem(BaseModel):
    """Contagens de redacoes realizadas por categoria de PII."""

    nome: int = 0
    email: int = 0
    telefone: int = 0
    cpf: int = 0
    cep: int = 0
    endereco: int = 0
    url: int = 0


class CriarExperienciasRequisicao(BaseModel):
    """Requisicao para criacao de experiencias a partir de texto."""

    model_config = ConfigDict(extra="forbid")

    texto: str = Field(..., description="Texto com as experiencias profissionais")

    @field_validator("texto")
    @classmethod
    def validar_texto(cls, valor: str) -> str:
        valor_limpo = valor.strip()
        if not valor_limpo or len(valor_limpo) > 20000:
            raise ValueError(
                "O texto deve conter entre 1 e 20.000 caracteres apos remocao de espacos."
            )
        return valor


class ConfirmarEnvioRequisicao(BaseModel):
    """Requisicao para confirmacao de envio do curriculo redigido."""

    model_config = ConfigDict(extra="forbid")

    curriculo_id: str = Field(..., min_length=1, description="Identificador do curriculo")
    texto_revisado: str | None = Field(
        None, description="Texto opcional revisado pelo usuario"
    )

    @field_validator("texto_revisado")
    @classmethod
    def validar_texto_revisado(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        valor_limpo = valor.strip()
        if not valor_limpo or len(valor_limpo) > 20000:
            raise ValueError(
                "O texto revisado deve conter entre 1 e 20.000 caracteres apos remocao de espacos."
            )
        return valor


class CurriculoResposta(BaseModel):
    """Resposta padronizada de curriculo e experiencias."""

    id: str
    origem: Literal["texto", "pdf", "docx"]
    status: Literal["aguardando_confirmacao", "confirmado"]
    texto_redigido: str
    sha256_texto_redigido: str
    redacoes: RedacoesContagem
    aviso_redacao: str = AVISO_REDACAO_PADRAO
    criado_em: str
    confirmado_em: str | None = None
