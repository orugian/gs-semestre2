"""Esquemas de dados para intenção de transição profissional."""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from citizentech.mercado.snapshot import UF_PARA_IBGE


class IntencaoRequisicao(BaseModel):
    model_config = ConfigDict(extra="forbid")

    atividades_desejadas: list[str] = Field(default_factory=list)
    motivos: list[str] = Field(default_factory=list)
    horas_semana: int = Field(..., ge=1, le=80)
    orcamento_mensal_brl: float | None = Field(default=None, ge=0.0, le=100000.0)
    uf: str

    @field_validator("atividades_desejadas")
    @classmethod
    def validar_atividades(cls, valores: list[str]) -> list[str]:
        if len(valores) > 10:
            raise ValueError("No máximo 10 atividades desejadas são permitidas.")
        itens_limpos: list[str] = []
        for item in valores:
            item_strip = item.strip()
            if not (1 <= len(item_strip) <= 120):
                raise ValueError(
                    "Cada atividade desejada deve ter entre 1 e 120 caracteres após strip."
                )
            itens_limpos.append(item_strip)
        return itens_limpos

    @field_validator("motivos")
    @classmethod
    def validar_motivos(cls, valores: list[str]) -> list[str]:
        if len(valores) > 5:
            raise ValueError("No máximo 5 motivos são permitidos.")
        itens_limpos: list[str] = []
        for item in valores:
            item_strip = item.strip()
            if not (1 <= len(item_strip) <= 300):
                raise ValueError(
                    "Cada motivo deve ter entre 1 e 300 caracteres após remoção de espaços."
                )
            itens_limpos.append(item_strip)
        return itens_limpos

    @field_validator("uf")
    @classmethod
    def validar_uf(cls, valor: str) -> str:
        uf_limpa = valor.strip().upper()
        if uf_limpa not in UF_PARA_IBGE:
            raise ValueError(f"UF '{valor}' inválida. Esperada sigla de estado brasileiro.")
        return uf_limpa


class IntencaoResposta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    atividades_desejadas: list[str]
    motivos: list[str]
    horas_semana: int
    orcamento_mensal_brl: float | None
    uf: str
    atualizado_em: str
