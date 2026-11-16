"""Aceite independente R07: avaliacao municipal fora do ajuste, sem tocar2026."""

import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm
from sklearn.model_selection import train_test_split

from citizentech_ml.estatistica import ajustar_logistica_municipal


def test_r07_logistica_avalia_teste_estratificado_sem_sobreposicao():
    rng = np.random.default_rng(123)
    f1, f2 = rng.normal(size=(2, 200))
    prob = 1 / (1 + np.exp(-(0.3 * f1 + 0.2 * f2)))
    y = rng.binomial(1, prob)
    base = pd.DataFrame(
        {
            "municipio": [str(350000 + i) for i in range(200)],
            "uf": "35",
            "admissoes_2024": 50,
            "admissoes_2025": 50 + 2 * y - 1,
            "salario_medio_2024": 3000 + 500 * f1,
            "percentual_superior_2024": 50 + 10 * f2,
        }
    )
    res = ajustar_logistica_municipal(base, seed=44)
    assert "avaliacao_teste" in res, "R07 exige teste estratificado, nao somente in-sample"
    av = res["avaliacao_teste"]
    tr, te = train_test_split(np.arange(200), test_size=0.2, random_state=44, stratify=y)
    assert av["municipios_treino"] == base.iloc[tr]["municipio"].tolist()
    assert av["municipios_teste"] == base.iloc[te]["municipio"].tolist()
    assert set(av["municipios_treino"]).isdisjoint(av["municipios_teste"])
    assert np.asarray(av["matriz_confusao"]).sum() == 40
    assert 0 <= av["acuracia"] <= 1
    x = sm.add_constant(base[["salario_medio_2024", "percentual_superior_2024"]])
    independente = sm.Logit(y[tr], x.iloc[tr]).fit(disp=False)
    for nome, coef in independente.params.items():
        assert res["coeficientes"][nome] == pytest.approx(coef)
    classes = (independente.predict(x.iloc[te]) >= 0.5).astype(int).to_numpy()
    assert av["acuracia"] == pytest.approx(np.mean(classes == y[te]))
