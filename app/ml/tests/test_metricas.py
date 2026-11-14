"""Testes das funções de métricas de avaliação puras e agregações."""

import math

import numpy as np
import pandas as pd
import pytest

from citizentech_ml.metricas import (
    mae,
    mase,
    resumir_erros,
    rmse,
    wape,
)


def test_metricas_valores_exatos_vetores_pequenos() -> None:
    """Calcula valores manuais exatos para vetores conhecidos."""
    y = np.array([10.0, 20.0, 30.0])
    yhat = np.array([12.0, 18.0, 33.0])

    # Erros abs: 2, 2, 3 -> soma = 7 -> mae = 7/3
    val_mae = mae(y, yhat)
    assert math.isclose(val_mae, 7.0 / 3.0, rel_tol=1e-9)

    # Erros quad: 4, 4, 9 -> soma = 17 -> rmse = sqrt(17/3)
    val_rmse = rmse(y, yhat)
    assert math.isclose(val_rmse, math.sqrt(17.0 / 3.0), rel_tol=1e-9)

    # Soma y = 60 -> wape = 7/60
    val_wape = wape(y, yhat)
    assert val_wape is not None
    assert math.isclose(val_wape, 7.0 / 60.0, rel_tol=1e-9)

    # MASE com escala válida = 2.0 -> (7/3) / 2 = 7/6
    val_mase = mase(y, yhat, erro_escala=2.0)
    assert val_mase is not None
    assert math.isclose(val_mase, 7.0 / 6.0, rel_tol=1e-9)


def test_wape_denominador_zero() -> None:
    """WAPE com soma real igual a zero retorna None, nunca inf ou 0."""
    y = np.array([0.0, 0.0, 0.0])
    yhat = np.array([1.0, 2.0, 3.0])
    assert wape(y, yhat) is None


def test_mase_escala_invalida_ou_ausente() -> None:
    """MASE com escala <= 0 ou None retorna None."""
    y = np.array([10.0, 20.0])
    yhat = np.array([12.0, 22.0])

    assert mase(y, yhat, erro_escala=0.0) is None
    assert mase(y, yhat, erro_escala=-1.5) is None
    assert mase(y, yhat, erro_escala=None) is None
    assert mase(y, yhat, erro_escala=float("nan")) is None


def test_validacoes_entradas_invalidas() -> None:
    """Verifica rejeição com ValueError para vazios, tamanhos distintos e NaN/inf."""
    # Vazio
    with pytest.raises(ValueError, match="vazio"):
        mae(np.array([]), np.array([]))

    # Tamanhos distintos
    with pytest.raises(ValueError, match="tamanhos diferentes"):
        rmse(np.array([1.0, 2.0]), np.array([1.0]))

    # NaN
    with pytest.raises(ValueError, match="não finitos ou NaN"):
        wape(np.array([1.0, float("nan")]), np.array([1.0, 2.0]))

    # Inf
    with pytest.raises(ValueError, match="não finitos ou NaN"):
        mae(np.array([1.0, 2.0]), np.array([1.0, float("inf")]))


def test_resumir_erros() -> None:
    """Valida agregação global e macro-MAE por série em DataFrame."""
    df = pd.DataFrame(
        {
            "destino": ["d1", "d1", "d2", "d2"],
            "uf": ["SP", "SP", "RJ", "RJ"],
            "real": [10.0, 20.0, 100.0, 200.0],
            "prev": [12.0, 18.0, 110.0, 190.0],
        }
    )

    resumo = resumir_erros(df, col_real="real", col_prev="prev", chaves_serie=["destino", "uf"])

    assert resumo["n"] == 4
    # Erros abs: d1: 2, 2 (mae = 2.0); d2: 10, 10 (mae = 10.0)
    # Global MAE: (2 + 2 + 10 + 10) / 4 = 24 / 4 = 6.0
    assert math.isclose(resumo["mae"], 6.0, rel_tol=1e-9)

    # Macro MAE: média de (2.0 e 10.0) = 6.0
    assert math.isclose(resumo["macro_mae"], 6.0, rel_tol=1e-9)

    # WAPE global: 24 / (30 + 300) = 24 / 330 = 0.07272727...
    assert math.isclose(resumo["wape"], 24.0 / 330.0, rel_tol=1e-9)

    # Erro com NaN em df
    df_nan = df.copy()
    df_nan.loc[0, "real"] = float("nan")
    with pytest.raises(ValueError, match="contêm NaN"):
        resumir_erros(df_nan, "real", "prev", ["destino", "uf"])
