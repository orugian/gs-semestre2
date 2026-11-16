"""Testes para funções estatísticas inferenciais e regressões."""

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from citizentech_ml.estatistica.analises import (
    ajustar_logistica_municipal,
    ajustar_ols_multipla,
    ajustar_ols_simples,
    probabilidades_normais,
    testes_medias_enunciado,
)


def test_probabilidades_normais_populacao_assimetrica_normal_assumida():
    """Valida cálculo de P(X < media)=0.5 e P(X > mediana) sob Normal assumida com sigma ddof=0."""
    populacao = [10.0, 11.0, 12.0, 13.0, 24.0]
    mu = float(np.mean(populacao))
    mediana = float(np.median(populacao))
    sigma_ddof0 = float(np.std(populacao, ddof=0))
    p_esperado_maior_mediana = float(stats.norm.sf(mediana, loc=mu, scale=sigma_ddof0))

    resultado = probabilidades_normais(populacao)

    assert resultado["probabilidade_menor_media"] == pytest.approx(0.5)
    assert resultado["probabilidade_maior_mediana"] == pytest.approx(p_esperado_maior_mediana)
    assert resultado["classificacao_menor_media"] == "equiprovavel"
    assert resultado["classificacao_maior_mediana"] == "provavel"


def test_probabilidades_normais_rejeita_n_menor_que_dois():
    with pytest.raises(ValueError, match="pelo menos 2 observações"):
        probabilidades_normais([42.0])


def test_probabilidades_normais_rejeita_populacao_constante():
    with pytest.raises(ValueError, match="constante"):
        probabilidades_normais([5.0, 5.0, 5.0, 5.0])


def test_probabilidades_normais_rejeita_nan_ou_infinito():
    with pytest.raises(ValueError, match="ausentes.*infinitos"):
        probabilidades_normais([1.0, 2.0, np.nan, 4.0])
    with pytest.raises(ValueError, match="ausentes.*infinitos"):
        probabilidades_normais([1.0, 2.0, np.inf, 4.0])


def test_probabilidades_normais_classificacao_pouco_provavel():
    populacao = [5.0, 18.0, 19.0, 20.0, 21.0]
    resultado = probabilidades_normais(populacao)
    assert resultado["probabilidade_maior_mediana"] < 0.5
    assert resultado["classificacao_maior_mediana"] == "pouco_provavel"


def test_testes_medias_enunciado_calculo_z_e_rejeicao():
    rng = np.random.default_rng(12345)
    populacao = rng.normal(loc=100.0, scale=15.0, size=35)
    mu_ref = float(np.mean(populacao))
    sigma_ref = float(np.std(populacao, ddof=0))

    res = testes_medias_enunciado(populacao, seeds=(42, 43))

    assert "teste_menor" in res
    assert "teste_maior" in res

    # Teste menor: n=20, alpha=0.06
    tm = res["teste_menor"]
    assert tm["n"] == 20
    assert tm["alpha"] == 0.06
    assert len(tm["indices_amostrais"]) == 20
    assert len(set(tm["indices_amostrais"])) == 20  # sem reposição
    assert tm["mu_ref"] == pytest.approx(mu_ref)
    assert tm["sigma_ref"] == pytest.approx(sigma_ref)
    z_indep_1 = (tm["media_amostral"] - mu_ref) / (sigma_ref / np.sqrt(20))
    p_indep_1 = float(stats.norm.cdf(z_indep_1))
    z_crit_1 = float(stats.norm.ppf(0.06))
    assert tm["estatistica_z"] == pytest.approx(z_indep_1)
    assert tm["p_valor"] == pytest.approx(p_indep_1)
    assert tm["z_critico"] == pytest.approx(z_crit_1)
    assert tm["rejeita_h0"] == (z_indep_1 < z_crit_1)

    # Teste maior: n=25, alpha=0.09
    tM = res["teste_maior"]
    assert tM["n"] == 25
    assert tM["alpha"] == 0.09
    assert len(tM["indices_amostrais"]) == 25
    assert len(set(tM["indices_amostrais"])) == 25  # sem reposição
    assert tM["mu_ref"] == pytest.approx(mu_ref)
    assert tM["sigma_ref"] == pytest.approx(sigma_ref)
    z_indep_2 = (tM["media_amostral"] - mu_ref) / (sigma_ref / np.sqrt(25))
    p_indep_2 = float(stats.norm.sf(z_indep_2))
    z_crit_2 = float(stats.norm.ppf(1.0 - 0.09))
    assert tM["estatistica_z"] == pytest.approx(z_indep_2)
    assert tM["p_valor"] == pytest.approx(p_indep_2)
    assert tM["z_critico"] == pytest.approx(z_crit_2)
    assert tM["rejeita_h0"] == (z_indep_2 > z_crit_2)


def test_testes_medias_enunciado_rejeita_populacao_insuficiente():
    with pytest.raises(ValueError, match="pelo menos 25 observações"):
        testes_medias_enunciado(list(range(24)))


def test_testes_medias_enunciado_rejeita_constante_e_nan():
    with pytest.raises(ValueError, match="constante"):
        testes_medias_enunciado([10.0] * 30)

    with pytest.raises(ValueError, match="ausentes.*infinitos"):
        pop = [1.0] * 29 + [np.nan]
        testes_medias_enunciado(pop)


def test_ajustar_ols_simples_coeficientes_conhecidos_e_previsao():
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    y = 3.0 + 2.5 * x
    res = ajustar_ols_simples(x, y, ponto_previsao=10.0)

    assert res["intercepto"] == pytest.approx(3.0)
    assert res["coeficiente_angular"] == pytest.approx(2.5)
    assert res["r2"] == pytest.approx(1.0)
    assert res["correlacao_pearson"] == pytest.approx(1.0)
    assert res["previsao"] == pytest.approx(28.0)


def test_ajustar_ols_simples_rejeita_entradas_invalidas():
    # Amostra insuficiente
    with pytest.raises(ValueError, match="mínimo de 3"):
        ajustar_ols_simples([1.0, 2.0], [3.0, 4.0])

    # Comprimentos divergentes
    with pytest.raises(ValueError, match="mesmo comprimento"):
        ajustar_ols_simples([1.0, 2.0, 3.0], [4.0, 5.0])

    # Variância zero de X
    with pytest.raises(ValueError, match="X possui variância zero"):
        ajustar_ols_simples([2.0, 2.0, 2.0], [1.0, 2.0, 3.0])

    # Variância zero de y
    with pytest.raises(ValueError, match="y possui variância zero"):
        ajustar_ols_simples([1.0, 2.0, 3.0], [5.0, 5.0, 5.0])

    # NaN / Inf
    with pytest.raises(ValueError, match="ausentes.*infinitos"):
        ajustar_ols_simples([1.0, np.nan, 3.0], [1.0, 2.0, 3.0])


def test_ajustar_ols_multipla_coeficientes_conhecidos_e_previsao():
    x1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
    x2 = np.array([3.0, 1.0, 4.0, 2.0, 6.0, 5.0, 8.0, 7.0])
    x3 = np.array([0.5, 1.5, 0.2, 2.1, 1.8, 3.0, 2.5, 4.0])
    # y = 10.0 + 2.0*x1 - 1.5*x2 + 0.5*x3
    y = 10.0 + 2.0 * x1 - 1.5 * x2 + 0.5 * x3

    df_x = pd.DataFrame({"x1": x1, "x2": x2, "x3": x3})
    ponto = {"x1": 2.0, "x2": 3.0, "x3": 1.0}
    # y_esperado = 10 + 2*(2) - 1.5*(3) + 0.5*(1) = 10 + 4 - 4.5 + 0.5 = 10.0

    res = ajustar_ols_multipla(df_x, y, ponto_previsao=ponto)

    assert res["coeficientes"]["const"] == pytest.approx(10.0)
    assert res["coeficientes"]["x1"] == pytest.approx(2.0)
    assert res["coeficientes"]["x2"] == pytest.approx(-1.5)
    assert res["coeficientes"]["x3"] == pytest.approx(0.5)
    assert res["r2"] == pytest.approx(1.0)
    assert res["previsao"] == pytest.approx(10.0)
    assert "matriz_covariancia" in res
    assert "matriz_correlacao" in res


def test_ajustar_ols_multipla_rejeita_colinearidade_e_invalidos():
    # Colinearidade perfeita
    x1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    x2 = 2.0 * x1
    y = np.array([2.0, 4.0, 5.0, 8.0, 10.0, 12.0])
    df_colin = pd.DataFrame({"x1": x1, "x2": x2})
    with pytest.raises(ValueError, match="Colinearidade perfeita|rank insuficiente"):
        ajustar_ols_multipla(df_colin, y)

    # Menos de 2 variáveis explicativas
    df_1col = pd.DataFrame({"x1": x1})
    with pytest.raises(ValueError, match="pelo menos 2 variáveis explicativas"):
        ajustar_ols_multipla(df_1col, y)

    # Amostra insuficiente (k=2, k+1=3, n=3 <= 3)
    with pytest.raises(ValueError, match="Amostra insuficiente"):
        ajustar_ols_multipla(df_colin.iloc[:3], y[:3])

    # Variância zero em coluna
    df_var0 = pd.DataFrame({"x1": x1, "x2": [5.0] * len(x1)})
    with pytest.raises(ValueError, match="variância zero"):
        ajustar_ols_multipla(df_var0, y)


def test_ajustar_logistica_municipal_ajuste_e_previsao():
    rng = np.random.default_rng(44)
    n = 40
    salario = rng.normal(3000.0, 500.0, size=n).round(2)
    superior = rng.uniform(10.0, 40.0, size=n).round(2)
    total_mun = rng.integers(5000, 20000, size=n)
    adm_2024 = rng.integers(100, 1000, size=n)
    # Admissões 2025 para gerar ambas as classes sem separação perfeita
    ruido = rng.integers(-50, 50, size=n)
    adm_2025 = np.clip(adm_2024 + ruido, a_min=10, a_max=None)

    df_base = pd.DataFrame(
        {
            "municipio": [f"Mun_{i}" for i in range(n)],
            "uf": ["SP"] * n,
            "admissoes_2024": adm_2024,
            "admissoes_2025": adm_2025,
            "salario_medio_2024": salario,
            "percentual_superior_2024": superior,
            "total_municipal_2024": total_mun,
        }
    )

    ponto = {
        "salario_medio_2024": 3200.0,
        "percentual_superior_2024": 22.0,
    }

    res = ajustar_logistica_municipal(df_base, ponto_previsao=ponto, seed=44)

    assert "acuracia_no_ajuste" in res
    assert 0.0 <= res["acuracia_no_ajuste"] <= 1.0
    assert res["matriz_confusao_no_ajuste"]["ordem_classes"] == [0, 1]
    assert "previsao_ponto" in res
    assert 0.0 <= res["previsao_ponto"]["probabilidade"] <= 1.0
    assert res["previsao_ponto"]["classe"] in (0, 1)
    assert res["variaveis_x"] == ["salario_medio_2024", "percentual_superior_2024"]
    assert "participacao_2024" not in res["variaveis_x"]
    assert "logit(p) =" in res["equacao"]
    assert "salario_medio_2024" in res["equacao"]
    assert "percentual_superior_2024" in res["equacao"]
    assert "participacao_2024" not in res["equacao"]


def test_ajustar_logistica_municipal_rejeita_classe_unica():
    # Todos com admissoes_2025 > admissoes_2024 -> classe unica = 1
    df = pd.DataFrame(
        {
            "municipio": [f"Mun_{i}" for i in range(10)],
            "uf": ["SP"] * 10,
            "admissoes_2024": [100] * 10,
            "admissoes_2025": [200] * 10,
            "salario_medio_2024": [3000.0 + i * 100 for i in range(10)],
            "percentual_superior_2024": [10.0 + i * 2 for i in range(10)],
            "total_municipal_2024": [5000 + i * 100 for i in range(10)],
        }
    )
    with pytest.raises(ValueError, match="classe única"):
        ajustar_logistica_municipal(df)


def test_ajustar_logistica_municipal_rejeita_separacao_perfeita():
    # Separação perfeita gerada por uma feature linearmente extrema
    # Ex: salário < 3000 -> classe 0; salário >= 3000 -> classe 1 com grande gap
    salario = [1000.0, 1100.0, 1200.0, 1300.0, 50000.0, 51000.0, 52000.0, 53000.0]
    adm_24 = [100, 100, 100, 100, 200, 200, 200, 200]
    adm_25 = [50, 50, 50, 50, 400, 400, 400, 400]
    df = pd.DataFrame(
        {
            "municipio": [f"Mun_{i}" for i in range(8)],
            "uf": ["SP"] * 8,
            "admissoes_2024": adm_24,
            "admissoes_2025": adm_25,
            "salario_medio_2024": salario,
            "percentual_superior_2024": [10.0, 11.0, 12.0, 13.0, 30.0, 31.0, 32.0, 33.0],
            "total_municipal_2024": [1000] * 8,
        }
    )
    with pytest.raises(ValueError, match="separação perfeita|quase-separação"):
        ajustar_logistica_municipal(df)


def test_ajustar_logistica_municipal_ignora_colunas_extras_e_preserva_input():
    rng = np.random.default_rng(77)
    n = 30
    salario = rng.normal(3000.0, 500.0, size=n).round(2)
    superior = rng.uniform(10.0, 40.0, size=n).round(2)
    total_mun = rng.integers(5000, 20000, size=n)
    adm_2024 = rng.integers(100, 1000, size=n)
    ruido = rng.integers(-40, 40, size=n)
    adm_2025 = np.clip(adm_2024 + ruido, a_min=10, a_max=None)

    df_base = pd.DataFrame(
        {
            "municipio": [f"Mun_{i}" for i in range(n)],
            "uf": ["SP"] * n,
            "admissoes_2024": adm_2024,
            "admissoes_2025": adm_2025,
            "salario_medio_2024": salario,
            "percentual_superior_2024": superior,
            "total_municipal_2024": total_mun,
            "coluna_futura_vazamento_2026": rng.normal(size=n),
            "outra_coluna_aleatoria": [f"texto_{i}" for i in range(n)],
        }
    )
    df_copia = df_base.copy()

    res = ajustar_logistica_municipal(df_base)

    # Imutabilidade do input
    pd.testing.assert_frame_equal(df_base, df_copia)

    # Apenas as 2 colunas fixadas pela Emenda D11 entraram no modelo
    assert res["variaveis_x"] == [
        "salario_medio_2024",
        "percentual_superior_2024",
    ]
    assert set(res["coeficientes"].keys()) == {
        "const",
        "salario_medio_2024",
        "percentual_superior_2024",
    }


def test_ajustar_logistica_municipal_sem_total_municipal_duas_explicativas():
    """RED: base válida SEM total_municipal_2024 é aceita e logística usa somente 2 explicativas."""
    rng = np.random.default_rng(44)
    n = 30
    salario = rng.normal(3000.0, 500.0, size=n).round(2)
    superior = rng.uniform(10.0, 40.0, size=n).round(2)
    adm_2024 = rng.integers(100, 1000, size=n)
    ruido = rng.integers(-40, 40, size=n)
    adm_2025 = np.clip(adm_2024 + ruido, a_min=10, a_max=None)

    df_base = pd.DataFrame(
        {
            "municipio": [f"Mun_{i}" for i in range(n)],
            "uf": ["SP"] * n,
            "admissoes_2024": adm_2024,
            "admissoes_2025": adm_2025,
            "salario_medio_2024": salario,
            "percentual_superior_2024": superior,
        }
    )
    ponto = {"salario_medio_2024": 3200.0, "percentual_superior_2024": 25.0}

    res = ajustar_logistica_municipal(df_base, ponto_previsao=ponto, seed=44)

    assert res["variaveis_x"] == ["salario_medio_2024", "percentual_superior_2024"]
    assert "participacao_2024" not in res["variaveis_x"]
    assert set(res["coeficientes"].keys()) == {
        "const",
        "salario_medio_2024",
        "percentual_superior_2024",
    }
    assert res["previsao_ponto"] is not None
    assert 0.0 <= res["previsao_ponto"]["probabilidade"] <= 1.0


def test_ajustar_logistica_municipal_ponto_previsao_formatos_e_validacoes():
    rng = np.random.default_rng(44)
    n = 30
    salario = rng.normal(3000.0, 500.0, size=n).round(2)
    superior = rng.uniform(10.0, 40.0, size=n).round(2)
    adm_2024 = rng.integers(100, 1000, size=n)
    ruido = rng.integers(-40, 40, size=n)
    adm_2025 = np.clip(adm_2024 + ruido, a_min=10, a_max=None)

    df_base = pd.DataFrame(
        {
            "municipio": [f"Mun_{i}" for i in range(n)],
            "uf": ["SP"] * n,
            "admissoes_2024": adm_2024,
            "admissoes_2025": adm_2025,
            "salario_medio_2024": salario,
            "percentual_superior_2024": superior,
        }
    )

    # 1. Ponto como lista / array de 2 elementos
    res_arr = ajustar_logistica_municipal(df_base, ponto_previsao=[3200.0, 25.0])
    assert res_arr["previsao_ponto"] is not None
    assert 0.0 <= res_arr["previsao_ponto"]["probabilidade"] <= 1.0

    # 2. Ponto como array de 3 elementos (critério antigo de 3X deve falhar)
    with pytest.raises(ValueError, match="Ponto de previsão deve conter 2 valores"):
        ajustar_logistica_municipal(df_base, ponto_previsao=[3200.0, 25.0, 5.0])

    # 3. Ponto como dict com variável faltante
    with pytest.raises(ValueError, match="Ponto de previsão ausente para variáveis explicativas"):
        ajustar_logistica_municipal(df_base, ponto_previsao={"salario_medio_2024": 3200.0})

    # 4. Ponto como DataFrame (1 linha, 2 colunas)
    df_ponto = pd.DataFrame({"salario_medio_2024": [3200.0], "percentual_superior_2024": [25.0]})
    res_df = ajustar_logistica_municipal(df_base, ponto_previsao=df_ponto)
    assert res_df["previsao_ponto"]["probabilidade"] == pytest.approx(
        res_arr["previsao_ponto"]["probabilidade"]
    )

    # 5. Ponto como Series
    s_ponto = pd.Series({"salario_medio_2024": 3200.0, "percentual_superior_2024": 25.0})
    res_s = ajustar_logistica_municipal(df_base, ponto_previsao=s_ponto)
    assert res_s["previsao_ponto"]["probabilidade"] == pytest.approx(
        res_arr["previsao_ponto"]["probabilidade"]
    )


def test_ajustar_logistica_municipal_rejeita_rank_insuficiente_2x():
    # 2 explicativas perfeitamente colineares: rank(const, X1, X2) = 2 < 3
    salario = [2000.0, 2500.0, 3000.0, 3500.0, 4000.0, 4500.0]
    percentual_colinear = [0.01 * s for s in salario]
    df = pd.DataFrame(
        {
            "municipio": [f"Mun_{i}" for i in range(6)],
            "uf": ["SP"] * 6,
            "admissoes_2024": [100, 150, 200, 250, 300, 350],
            "admissoes_2025": [120, 140, 210, 240, 310, 340],
            "salario_medio_2024": salario,
            "percentual_superior_2024": percentual_colinear,
        }
    )
    with pytest.raises(ValueError, match="rank insuficiente ou colinearidade perfeita"):
        ajustar_logistica_municipal(df)


def test_ajustar_logistica_municipal_nao_inclui_em_x_alvo_crescimento_participacao_ou_2025():
    rng = np.random.default_rng(99)
    n = 25
    salario = rng.normal(3000.0, 400.0, size=n).round(2)
    superior = rng.uniform(15.0, 35.0, size=n).round(2)
    adm_2024 = rng.integers(100, 800, size=n)
    adm_2025 = rng.integers(100, 800, size=n)
    tot_mun = adm_2024 * 10

    df = pd.DataFrame(
        {
            "municipio": [f"Mun_{i}" for i in range(n)],
            "uf": ["SP"] * n,
            "admissoes_2024": adm_2024,
            "admissoes_2025": adm_2025,
            "salario_medio_2024": salario,
            "percentual_superior_2024": superior,
            "total_municipal_2024": tot_mun,
            "participacao_2024": (100.0 * adm_2024 / tot_mun),
            "crescimento": (adm_2025 > adm_2024).astype(int),
            "saldo_2025": adm_2025 - adm_2024,
        }
    )

    res = ajustar_logistica_municipal(df)

    assert res["variaveis_x"] == ["salario_medio_2024", "percentual_superior_2024"]
    assert set(res["coeficientes"].keys()) == {
        "const",
        "salario_medio_2024",
        "percentual_superior_2024",
    }
    cols_proibidas = [
        "admissoes_2025",
        "crescimento",
        "participacao_2024",
        "total_municipal_2024",
        "saldo_2025",
    ]
    for col_proibida in cols_proibidas:
        assert col_proibida not in res["variaveis_x"]
        assert col_proibida not in res["coeficientes"]
        assert col_proibida not in res["equacao"]
