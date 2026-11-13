"""Modelos e estruturas de dados para a ingestão do Novo Caged."""

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Ocupacoes:
    """Conjunto de ocupações CBO elegíveis para a ingestão."""

    versao: str
    destinos: dict[str, dict[str, Any]]
    cbo6_reserva: list[str]
    codigos_ingestao: set[str]
    hash: str


@dataclass
class Fonte:
    """Descritor da fonte dos microdados."""

    id: str = "novo_caged"
    responsavel: str = "Ministério do Trabalho e Emprego — PDET"
    url_base: str = "ftp://ftp.mtps.gov.br/pdet/microdados/NOVO%20CAGED/"
    intervalo: str = "202001–202609"
    termos: str = "Termo de uso específico não localizado no FTP em 12/11/2026 (não verificado)"
    treino_autorizado: bool = True
    base_autorizacao: str = (
        "Microdados públicos não identificados divulgados pelo MTE/PDET; "
        "uso para treino decidido em D04 do plano"
    )


@dataclass
class RegistroProcedencia:
    """Registro de procedência auditável de um arquivo ingerido ou consultado."""

    fonte: str
    url: str
    arquivo: str
    tipo: str
    competencia_arquivo: str
    situacao: str  # "ingerido" | "ausente_na_fonte" | "falha" | "nao_promovida"
    sha256_7z: str | None = None
    bytes_7z: int | None = None
    coletado_em: str | None = None
    linhas_lidas: int = 0
    linhas_gravadas: int = 0
    colunas_descartadas_sensiveis: list[str] = field(default_factory=list)
    colunas_ignoradas: list[str] = field(default_factory=list)
    hash_ocupacoes: str | None = None
    hash_ocupacoes_anterior: str | None = None
    versao_ocupacoes: str | None = None
    layout_sha256: str = "0490f7ef84fd05db2d89cf22f56d8cf7262ceb14c9d7db1cca2bae422e6423ce"
    transformacoes: list[str] = field(default_factory=list)
    erro: str | None = None
    conflito: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Converte o registro para dicionário JSON-serializável."""
        return asdict(self)

    @classmethod
    def from_dict(cls, dados: dict[str, Any]) -> "RegistroProcedencia":
        """Instancia o registro a partir de dicionário."""
        return cls(**dados)


@dataclass
class ResumoIngestao:
    """Resumo consolidado da execução de ingestão de um período."""

    total_processados: int = 0
    total_ingeridos: int = 0
    total_ausentes: int = 0
    total_falhas: int = 0
    total_nao_promovidas: int = 0
    total_linhas_lidas: int = 0
    total_linhas_gravadas: int = 0
    registros: list[RegistroProcedencia] = field(default_factory=list)
    sucesso: bool = True
    erro: str | None = None
