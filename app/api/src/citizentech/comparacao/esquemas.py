"""Esquemas de dados para comparação de destinos."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from citizentech.mercado.snapshot import UF_PARA_IBGE


class CriarComparacaoRequisicao(BaseModel):
    model_config = ConfigDict(extra="forbid")

    destinos: list[str] = Field(...)
    uf: str | None = None

    @field_validator("destinos")
    @classmethod
    def validar_destinos(cls, valores: list[str]) -> list[str]:
        if not valores or len(valores) > 3:
            raise ValueError(
                f"Quantidade de destinos inválida ({len(valores) if valores else 0}). "
                "Deve ser entre 1 e 3."
            )
        itens_limpos = [d.strip() for d in valores]
        if any(not d for d in itens_limpos):
            raise ValueError("Identificador de destino inválido ou vazio.")
        if len(itens_limpos) != len(set(itens_limpos)):
            raise ValueError("Destinos repetidos não são permitidos na comparação.")
        return itens_limpos

    @field_validator("uf")
    @classmethod
    def validar_uf(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        uf_limpa = valor.strip().upper()
        if uf_limpa not in UF_PARA_IBGE:
            raise ValueError(f"UF '{valor}' inválida. Esperada sigla de estado brasileiro.")
        return uf_limpa


class ComparacaoResposta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    comparacao_id: str
    criado_em: str
    uf: str | None
    destinos: list[dict[str, Any]]
    aviso: str
