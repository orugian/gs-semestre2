"""Módulo de métricas de avaliação de modelos e baselines."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _validar_arrays(y: Any, yhat: Any) -> tuple[np.ndarray, np.ndarray]:
    """Converte e valida estritamente arrays de real e previsto."""
    arr_y = np.asarray(y, dtype=float).ravel()
    arr_yhat = np.asarray(yhat, dtype=float).ravel()

    if len(arr_y) == 0 or len(arr_yhat) == 0:
        raise ValueError("Array de entrada vazio.")

    if len(arr_y) != len(arr_yhat):
        raise ValueError(
            f"Entradas com tamanhos diferentes: len(y)={len(arr_y)} != len(yhat)={len(arr_yhat)}."
        )

    if not np.isfinite(arr_y).all() or not np.isfinite(arr_yhat).all():
        raise ValueError("Entradas contêm valores não finitos ou NaN.")

    return arr_y, arr_yhat


def mae(y: Any, yhat: Any) -> float:
    """Erro absoluto médio ponderado por linha."""
    arr_y, arr_yhat = _validar_arrays(y, yhat)
    return float(np.mean(np.abs(arr_y - arr_yhat)))


def rmse(y: Any, yhat: Any) -> float:
    """Raiz do erro quadrático médio."""
    arr_y, arr_yhat = _validar_arrays(y, yhat)
    return float(np.sqrt(np.mean((arr_y - arr_yhat) ** 2)))


def wape(y: Any, yhat: Any) -> float | None:
    """Weighted Absolute Percentage Error (soma dos erros abs / soma do real).

    Retorna None se a soma dos valores reais for zero (nunca 0 nem inf).
    """
    arr_y, arr_yhat = _validar_arrays(y, yhat)
    soma_real = float(np.sum(arr_y))
    if soma_real == 0.0:
        return None
    soma_erros = float(np.sum(np.abs(arr_y - arr_yhat)))
    return soma_erros / soma_real


def mase(y: Any, yhat: Any, erro_escala: float | None) -> float | None:
    """Mean Absolute Scaled Error relativo à escala do erro ingênuo/sazonal.

    Retorna None se a escala for <= 0, None ou NaN.
    """
    arr_y, arr_yhat = _validar_arrays(y, yhat)
    if erro_escala is None or np.isnan(erro_escala) or erro_escala <= 0.0:
        return None
    val_mae = float(np.mean(np.abs(arr_y - arr_yhat)))
    return val_mae / float(erro_escala)


def resumir_erros(
    df: pd.DataFrame,
    col_real: str,
    col_prev: str,
    chaves_serie: list[str],
) -> dict[str, Any]:
    """Resumo de erros com métricas globais e desagregadas por série."""
    if df.empty:
        raise ValueError("DataFrame vazio fornecido para resumir_erros.")

    for col in [col_real, col_prev]:
        if col not in df.columns:
            raise ValueError(f"Coluna obrigatória '{col}' ausente no DataFrame.")
        if df[col].isna().any():
            raise ValueError(f"Coluna '{col}' contêm NaN.")

    for k in chaves_serie:
        if k not in df.columns:
            raise ValueError(f"Chave de série '{k}' ausente no DataFrame.")

    y = df[col_real].to_numpy(dtype=float)
    yhat = df[col_prev].to_numpy(dtype=float)

    if not np.isfinite(y).all() or not np.isfinite(yhat).all():
        raise ValueError("Colunas contêm valores não finitos ou NaN.")

    val_n = len(df)
    val_mae = mae(y, yhat)
    val_rmse = rmse(y, yhat)
    val_wape = wape(y, yhat)

    tabela: list[dict[str, Any]] = []
    maes_series: list[float] = []

    agrupado = df.groupby(chaves_serie, as_index=False, dropna=False)
    for _, grupo in agrupado:
        y_g = grupo[col_real].to_numpy(dtype=float)
        yhat_g = grupo[col_prev].to_numpy(dtype=float)
        m_g = mae(y_g, yhat_g)
        r_g = rmse(y_g, yhat_g)
        w_g = wape(y_g, yhat_g)
        maes_series.append(m_g)

        reg_serie = {str(k): grupo[k].iloc[0] for k in chaves_serie}
        reg_serie.update(
            {
                "n": len(grupo),
                "mae": m_g,
                "rmse": r_g,
                "wape": w_g,
            }
        )
        tabela.append(reg_serie)

    val_macro_mae = float(np.mean(maes_series)) if maes_series else 0.0

    return {
        "n": val_n,
        "mae": val_mae,
        "rmse": val_rmse,
        "wape": val_wape,
        "macro_mae": val_macro_mae,
        "tabela_series": tabela,
    }
