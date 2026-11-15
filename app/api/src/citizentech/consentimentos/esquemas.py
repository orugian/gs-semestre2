"""Esquemas de validacao e resposta para consentimentos LGPD."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

FINALIDADES_VALIDAS = ("perfil", "curriculo_llm", "laboratorio_nuvem")
TipoFinalidade = Literal["perfil", "curriculo_llm", "laboratorio_nuvem"]


class CriarConsentimentoRequisicao(BaseModel):
    """Payload para concessao de consentimento."""

    model_config = ConfigDict(extra="forbid")

    finalidade: str

    @field_validator("finalidade")
    @classmethod
    def validar_finalidade(cls, v: str) -> str:
        if v not in FINALIDADES_VALIDAS:
            raise ValueError(
                f"Finalidade invalida. Deve ser uma de: {', '.join(FINALIDADES_VALIDAS)}."
            )
        return v


class ConsentimentoResposta(BaseModel):
    """Dados de um consentimento."""

    id: str
    finalidade: str
    versao_termo: str
    concedido_em: str
    revogado_em: str | None = None


class ListarConsentimentosResposta(BaseModel):
    """Lista de consentimentos do usuario logado."""

    itens: list[ConsentimentoResposta]
