"""Cálculo de disponibilidade conservadora as-of e validação temporal estrita."""

from __future__ import annotations

import pandas as pd

from citizentech_ml.features.datas import validar_competencia


def validar_e_calcular_disponibilidade(df: pd.DataFrame) -> pd.DataFrame:
    """Valida campos temporais e calcula a coluna de competência de disponibilidade as-of.

    Regras (D04b / R02 / T05 / T18):
    - Para EXC: t_disp = max(competencia_dec, competencia_exc, competencia_arquivo)
    - Para MOV e FOR: t_disp = max(competencia_dec, competencia_arquivo)
    - Campos ausentes, vazios ou em formato inválido geram ValueError explícito.
    - Tipos de arquivo válidos: MOV, FOR, EXC (case-insensitive e strip).
    - Vetorizado via mapeamento de combinações temporais únicas para alta performance.
    """
    if df.empty:
        df_res = df.copy()
        df_res["competencia_disp"] = pd.Series(dtype="string")
        return df_res

    colunas_obrigatorias = [
        "competencia_mov",
        "competencia_dec",
        "competencia_arquivo",
        "arquivo_tipo",
    ]
    for col in colunas_obrigatorias:
        if col not in df.columns:
            raise ValueError(f"Coluna obrigatória ausente no DataFrame: '{col}'")

    df_res = df.copy()
    if "competencia_exc" not in df_res.columns:
        df_res["competencia_exc"] = None

    # Normalizar arquivo_tipo para validação consistente
    df_res["arquivo_tipo"] = df_res["arquivo_tipo"].astype(str).str.strip().str.upper()
    for coluna in ("competencia_mov", "competencia_dec", "competencia_arquivo"):
        df_res[coluna] = df_res[coluna].astype(str).str.strip()

    colunas_chave = [
        "arquivo_tipo",
        "competencia_mov",
        "competencia_dec",
        "competencia_arquivo",
        "competencia_exc",
    ]

    # Extrair combinações únicas para validação rápida vetorizada
    df_unicos = df_res[colunas_chave].drop_duplicates()
    lookup_disp: dict[tuple[str, str, str, str, str], str] = {}

    for _, row in df_unicos.iterrows():
        tipo = str(row["arquivo_tipo"])
        if tipo not in {"MOV", "FOR", "EXC"}:
            raise ValueError(f"Tipo de arquivo desconhecido: {tipo!r}")

        # Validação estrita de cada competência
        validar_competencia(str(row["competencia_mov"]))
        comp_dec = validar_competencia(str(row["competencia_dec"]))
        comp_arq = validar_competencia(str(row["competencia_arquivo"]))

        val_exc = row["competencia_exc"]
        val_exc_str = "" if (pd.isna(val_exc) or val_exc is None) else str(val_exc).strip()
        if tipo == "EXC":
            if val_exc_str in {"", "None", "nan"}:
                raise ValueError(
                    f"Registro de EXC sem 'competencia_exc' válida: {val_exc!r}"
                )
            comp_exc = validar_competencia(val_exc_str)
            t_disp = max(comp_dec, comp_exc, comp_arq)
        else:
            t_disp = max(comp_dec, comp_arq)

        chave = (
            tipo,
            str(row["competencia_mov"]).strip(),
            str(row["competencia_dec"]).strip(),
            str(row["competencia_arquivo"]).strip(),
            val_exc_str,
        )
        lookup_disp[chave] = t_disp

    # Mapear de volta com vetorização rápida
    exc_series = df_res["competencia_exc"].apply(
        lambda v: "" if (pd.isna(v) or v is None) else str(v).strip()
    )
    chaves_serie = list(zip(
        df_res["arquivo_tipo"],
        df_res["competencia_mov"].astype(str).str.strip(),
        df_res["competencia_dec"].astype(str).str.strip(),
        df_res["competencia_arquivo"].astype(str).str.strip(),
        exc_series,
        strict=False,
    ))

    df_res["competencia_disp"] = pd.Series(
        [lookup_disp[c] for c in chaves_serie],
        index=df_res.index,
        dtype="string",
    )
    return df_res


def filtrar_disponiveis_as_of(df_com_disp: pd.DataFrame, t: str) -> pd.DataFrame:
    """Filtra apenas os registros conhecidos até o momento as-of t e com movimentação até t.

    Regra R02 / T05 / T18:
    - competencia_disp <= t
    - competencia_mov <= t
    """
    t_val = validar_competencia(t)
    mascara = (df_com_disp["competencia_disp"] <= t_val) & (
        df_com_disp["competencia_mov"] <= t_val
    )
    return df_com_disp[mascara].copy()

