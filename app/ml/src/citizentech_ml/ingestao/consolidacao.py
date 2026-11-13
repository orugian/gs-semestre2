"""Consolidação mensal de admissões e desligamentos por CBO e UF."""

from pathlib import Path

import pandas as pd

GRAUS_SUPERIOR_OU_MAIS = {9, 10, 11, 80}

COLUNAS_CONSOLIDACAO = [
    "competencia_mov",
    "uf",
    "cbo2002_ocupacao",
    "superior",
    "admissoes",
    "desligamentos",
]


def consolidar_mensal(dir_parquet: str | Path) -> pd.DataFrame:
    """Consolida as contagens mensais MOV+FOR-EXC a partir dos arquivos Parquet.

    Unidade de agregação: competencia_mov x uf x cbo2002_ocupacao x superior.
    - admissoes = saldo 1 em MOV e FOR menos saldo 1 em EXC.
    - desligamentos = saldo -1 em MOV e FOR menos saldo -1 em EXC.
    - Combinações sem movimentação real não são preenchidas com zero (ausência não é zero).
    """
    dir_parquet_path = Path(dir_parquet)
    if not dir_parquet_path.exists():
        return pd.DataFrame(columns=COLUNAS_CONSOLIDACAO).astype(
            {
                "competencia_mov": "string",
                "uf": "string",
                "cbo2002_ocupacao": "string",
                "superior": "bool",
                "admissoes": "int64",
                "desligamentos": "int64",
            }
        )

    arquivos_parquet = list(dir_parquet_path.glob("*.parquet"))
    if not arquivos_parquet:
        return pd.DataFrame(columns=COLUNAS_CONSOLIDACAO).astype(
            {
                "competencia_mov": "string",
                "uf": "string",
                "cbo2002_ocupacao": "string",
                "superior": "bool",
                "admissoes": "int64",
                "desligamentos": "int64",
            }
        )

    dfs: list[pd.DataFrame] = []
    colunas_ler = [
        "competencia_mov",
        "uf",
        "cbo2002_ocupacao",
        "grau_instrucao",
        "saldo_movimentacao",
        "arquivo_tipo",
    ]

    for p in arquivos_parquet:
        df_p = pd.read_parquet(p, columns=colunas_ler)
        if not df_p.empty:
            dfs.append(df_p)

    if not dfs:
        return pd.DataFrame(columns=COLUNAS_CONSOLIDACAO).astype(
            {
                "competencia_mov": "string",
                "uf": "string",
                "cbo2002_ocupacao": "string",
                "superior": "bool",
                "admissoes": "int64",
                "desligamentos": "int64",
            }
        )

    df_total = pd.concat(dfs, ignore_index=True)

    # Identificação de nível superior completo ou mais
    df_total["superior"] = df_total["grau_instrucao"].isin(GRAUS_SUPERIOR_OU_MAIS)

    # Identificação do impacto na contagem (MOV/FOR soma, EXC subtrai)
    eh_exc = df_total["arquivo_tipo"] == "EXC"
    sinal = eh_exc.map({True: -1, False: 1})

    df_total["delta_adm"] = ((df_total["saldo_movimentacao"] == 1).astype(int) * sinal)
    df_total["delta_des"] = ((df_total["saldo_movimentacao"] == -1).astype(int) * sinal)

    agrupado = (
        df_total.groupby(
            ["competencia_mov", "uf", "cbo2002_ocupacao", "superior"],
            as_index=False,
            dropna=False,
        )[["delta_adm", "delta_des"]]
        .sum()
    )

    agrupado = agrupado.rename(
        columns={"delta_adm": "admissoes", "delta_des": "desligamentos"}
    )

    agrupado["competencia_mov"] = agrupado["competencia_mov"].astype("string")
    agrupado["uf"] = agrupado["uf"].astype("string")
    agrupado["cbo2002_ocupacao"] = agrupado["cbo2002_ocupacao"].astype("string")
    agrupado["superior"] = agrupado["superior"].astype("bool")
    agrupado["admissoes"] = agrupado["admissoes"].astype("int64")
    agrupado["desligamentos"] = agrupado["desligamentos"].astype("int64")

    return agrupado[COLUNAS_CONSOLIDACAO]
