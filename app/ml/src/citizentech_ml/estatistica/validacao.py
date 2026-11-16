"""Validação de bases municipais para análises estatísticas."""

from __future__ import annotations

import numpy as np
import pandas as pd

COLUNAS_OBRIGATORIAS: list[str] = [
    "municipio",
    "uf",
    "admissoes_2024",
    "admissoes_2025",
    "salario_medio_2024",
    "percentual_superior_2024",
]


def _contem_booleano(serie: pd.Series) -> bool:
    """Detecta se uma série é do tipo bool ou contém valores booleanos."""
    if pd.api.types.is_bool_dtype(serie):
        return True
    return any(isinstance(v, (bool, np.bool_)) for v in serie)


def validar_base_municipal(df: pd.DataFrame) -> pd.DataFrame:
    """Valida integridade, chaves e regras de negócio da base municipal consolidada."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("A entrada deve ser um pandas DataFrame.")
    if len(df) == 0:
        raise ValueError("A base municipal está vazia.")

    faltantes = [col for col in COLUNAS_OBRIGATORIAS if col not in df.columns]
    if faltantes:
        raise ValueError(f"Colunas obrigatórias ausentes na base municipal: {faltantes}.")

    df_out = df.copy()

    # Validação de identificador municipal nulo, vazio ou somente espaços
    if _contem_booleano(df_out["municipio"]):
        raise ValueError("Identificador municipal nulo ou vazio não é permitido.")
    if df_out["municipio"].isna().any():
        raise ValueError("Identificador municipal nulo ou vazio não é permitido.")
    mun_str = df_out["municipio"].astype(str).str.strip()
    if (mun_str == "").any() or mun_str.str.lower().isin(["none", "nan", "null"]).any():
        raise ValueError("Identificador municipal nulo ou vazio não é permitido.")

    # Validação de duplicata de chave municipal
    if df_out["municipio"].duplicated().any():
        dups = df_out.loc[df_out["municipio"].duplicated(), "municipio"].unique().tolist()
        raise ValueError(f"Municípios duplicados encontrados na base: {dups}")

    # Validação de UF35 (Estado de São Paulo)
    if df_out["uf"].isna().any():
        raise ValueError("A coluna 'uf' contém dados ausentes (NaN / None).")
    ufs_str = df_out["uf"].astype(str).str.strip().str.upper()
    ufs_invalidas = ufs_str[~ufs_str.isin(["SP", "35"])]
    if len(ufs_invalidas) > 0:
        raise ValueError(
            f"Apenas registros do estado de São Paulo (UF='SP' ou 35) são permitidos. "
            f"Encontrados: {ufs_invalidas.unique().tolist()}"
        )

    # Colunas numéricas a inspecionar
    cols_numericas = [
        "admissoes_2024",
        "admissoes_2025",
        "salario_medio_2024",
        "percentual_superior_2024",
    ]
    tem_total_municipal = "total_municipal_2024" in df_out.columns
    if tem_total_municipal:
        cols_numericas.append("total_municipal_2024")

    # Rejeição estrita de booleanos e dados ausentes
    for col in cols_numericas:
        if _contem_booleano(df_out[col]):
            raise ValueError(f"A coluna '{col}' não pode conter valores booleanos (True/False).")
        if df_out[col].isna().any():
            raise ValueError(f"A coluna '{col}' contém dados ausentes (NaN / None).")

    # Conversão e validação numérica estrita
    for col in cols_numericas:
        s_num = pd.to_numeric(df_out[col], errors="coerce")
        if s_num.isna().any() or np.isinf(s_num).any():
            raise ValueError(f"Coluna numérica '{col}' contém valores não finitos ou inválidos.")
        df_out[col] = s_num

    # Regras para contagens de eventos (admissões devem ser inteiros >= 0)
    for col_contagem in ["admissoes_2024", "admissoes_2025"]:
        if (df_out[col_contagem] < 0).any():
            raise ValueError(f"{col_contagem} não pode conter valores negativos.")
        if (df_out[col_contagem] % 1 != 0).any():
            raise ValueError(
                f"A coluna '{col_contagem}' deve conter contagens de eventos "
                "inteiras (não fracionárias)."
            )
        df_out[col_contagem] = df_out[col_contagem].astype(int)

    # Regras para variáveis contínuas (salário e percentual)
    if (df_out["salario_medio_2024"] <= 0).any():
        raise ValueError("salario_medio_2024 deve ser estritamente positivo (> 0).")
    df_out["salario_medio_2024"] = df_out["salario_medio_2024"].astype(float)

    if (
        (df_out["percentual_superior_2024"] < 0.0) | (df_out["percentual_superior_2024"] > 100.0)
    ).any():
        raise ValueError("percentual_superior_2024 deve estar contido no intervalo [0, 100].")
    df_out["percentual_superior_2024"] = df_out["percentual_superior_2024"].astype(float)

    # Suporte a total municipal opcional fornecido por compatibilidade
    if tem_total_municipal:
        s_tot = df_out["total_municipal_2024"]
        if (s_tot <= 0).any():
            raise ValueError("total_municipal_2024 deve ser estritamente positivo (> 0).")
        if (s_tot % 1 != 0).any():
            raise ValueError(
                "A coluna 'total_municipal_2024' deve conter contagens inteiras (não fracionárias)."
            )
        if (s_tot < df_out["admissoes_2024"]).any():
            raise ValueError(
                "total_municipal_2024 não pode ser inferior a admissoes_2024 "
                "(denominador municipal indevido)."
            )
        df_out["total_municipal_2024"] = s_tot.astype(int)
        df_out["participacao_2024"] = (
            100.0 * df_out["admissoes_2024"] / df_out["total_municipal_2024"]
        )

    # Alvo binário D11/R07 (admissoes_2025 > admissoes_2024)
    df_out["crescimento"] = (df_out["admissoes_2025"] > df_out["admissoes_2024"]).astype(int)

    return df_out
