"""Verificação da cobertura da ingestão no período de referência."""

from pathlib import Path

import pandas as pd

from citizentech_ml.ingestao.ingestor import _gerar_intervalo_competencias
from citizentech_ml.ingestao.manifesto import carregar_manifesto, obter_registro


def cobertura(dir_dados: str | Path, inicio: str, fim: str) -> pd.DataFrame:
    """Retorna a situação de cada competência e tipo no intervalo informado.

    Possíveis situações:
    - ingerido: arquivo processado e gravado em Parquet
    - ausente_na_fonte: verificado no FTP e não existente
    - falha: download ou processamento falhou
    - pendente: ainda não processado ou ausente do manifesto
    """
    dir_dados_path = Path(dir_dados)
    manifesto_path = dir_dados_path / "caged" / "procedencia.json"
    manifesto = carregar_manifesto(manifesto_path)

    competencias = _gerar_intervalo_competencias(inicio, fim)
    tipos = ["MOV", "FOR", "EXC"]

    linhas: list[dict[str, str]] = []
    for comp in competencias:
        for t in tipos:
            reg = obter_registro(manifesto, t, comp)
            situacao = reg.situacao if reg is not None else "pendente"
            linhas.append(
                {
                    "competencia": comp,
                    "tipo": t,
                    "situacao": situacao,
                }
            )

    df = pd.DataFrame(linhas)
    df["competencia"] = df["competencia"].astype("string")
    df["tipo"] = df["tipo"].astype("string")
    df["situacao"] = df["situacao"].astype("string")
    return df
