"""Seleção de séries temporais por densidade de admissões no treino (D04a / T19)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from citizentech_ml.features.datas import validar_competencia


def calcular_densidade_treino(
    df_treino: pd.DataFrame,
    limite_minimo: float = 10.0,
    coluna_alvo: str = "alvo",
    coluna_tempo: str = "competencia",
    limite_competencia_treino: str | None = "202409",
) -> pd.DataFrame:
    """Calcula a média do alvo trimestral exclusivamente no conjunto de treino.

    Regras (D04a / T19):
    - Usa APENAS dados de treino; nunca consulta validação ou teste.
    - O chamador é responsável por fornecer exclusivamente o conjunto de treino
      do fold correspondente (ou do treino global D10 <= 202409).
    - Se a coluna temporal estiver presente e contiver competências posteriores
      a `limite_competencia_treino`, gera ValueError explícito para evitar vazamento acidental.
    - Rejeita alvos com valores negativos ou não finitos (inf, -inf).
    - Limite 10.0 é inclusive (média >= 10.0 é elegível).
    - Retorna relatório estruturado com:
      destino, uf, media_alvo_treino, elegivel, motivo.
    - Motivos: 'aprovado', 'densidade_insuficiente', 'sem_dados_treino'.
    """
    if df_treino.empty:
        return pd.DataFrame(
            columns=["destino", "uf", "media_alvo_treino", "elegivel", "motivo"]
        ).astype({
            "destino": "string",
            "uf": "string",
            "media_alvo_treino": "float64",
            "elegivel": "bool",
            "motivo": "string",
        })

    colunas_necessarias = ["destino", "uf", coluna_alvo]
    for col in colunas_necessarias:
        if col not in df_treino.columns:
            raise ValueError(f"Coluna obrigatória '{col}' ausente no DataFrame de treino.")

    # Validar que alvos não contêm valores negativos nem infinitos
    valores_alvo = df_treino[coluna_alvo].dropna().to_numpy()
    if len(valores_alvo) > 0:
        if not np.isfinite(valores_alvo).all() or (valores_alvo < 0).any():
            raise ValueError(
                f"Coluna de alvo '{coluna_alvo}' contém valores não finitos ou negativos."
            )

    # Validar que dados não contêm competências de validação/teste se a coluna existir
    if limite_competencia_treino is not None and coluna_tempo in df_treino.columns:
        corte_val = validar_competencia(limite_competencia_treino)
        comps = df_treino[coluna_tempo].dropna().astype(str).unique()
        for c in comps:
            if validar_competencia(c) > corte_val:
                raise ValueError(
                    f"DataFrame contém competência '{c}' posterior ao limite de treino "
                    f"'{corte_val}'. A densidade deve ser calculada estritamente no treino."
                )

    agrupado = (
        df_treino.groupby(["destino", "uf"], as_index=False, dropna=False)[coluna_alvo]
        .mean()
        .rename(columns={coluna_alvo: "media_alvo_treino"})
    )

    elegivel_lista: list[bool] = []
    motivo_lista: list[str] = []

    for _, row in agrupado.iterrows():
        media = row["media_alvo_treino"]
        if pd.isna(media):
            elegivel_lista.append(False)
            motivo_lista.append("sem_dados_treino")
        elif media >= limite_minimo:
            elegivel_lista.append(True)
            motivo_lista.append("aprovado")
        else:
            elegivel_lista.append(False)
            motivo_lista.append("densidade_insuficiente")

    agrupado["elegivel"] = pd.Series(elegivel_lista, index=agrupado.index, dtype="bool")
    agrupado["motivo"] = pd.Series(motivo_lista, index=agrupado.index, dtype="string")
    agrupado["destino"] = agrupado["destino"].astype("string")
    agrupado["uf"] = agrupado["uf"].astype("string")
    agrupado["media_alvo_treino"] = agrupado["media_alvo_treino"].astype("float64")

    return agrupado



def obter_series_elegiveis(relatorio_densidade: pd.DataFrame) -> set[tuple[str, str]]:
    """Extrai o conjunto de tuplas (destino, uf) elegíveis a partir do relatório."""
    if relatorio_densidade.empty:
        return set()
    aprovados = relatorio_densidade[relatorio_densidade["elegivel"]]
    return set(zip(aprovados["destino"], aprovados["uf"], strict=False))


def filtrar_series_elegiveis(
    df: pd.DataFrame,
    series_elegiveis: set[tuple[str, str]],
) -> pd.DataFrame:
    """Filtra qualquer painel mantendo apenas as séries (destino, uf) elegíveis."""
    if df.empty or not series_elegiveis:
        return df.iloc[0:0].copy()

    pares = list(zip(df["destino"], df["uf"], strict=False))
    mascara = [p in series_elegiveis for p in pares]
    return df[mascara].copy()
