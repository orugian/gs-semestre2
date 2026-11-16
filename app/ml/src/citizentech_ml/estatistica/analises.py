"""Funções de análise estatística inferencial e modelos de regressão."""

from __future__ import annotations

import warnings
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split
from statsmodels.tools.sm_exceptions import (
    ConvergenceWarning,
    PerfectSeparationError,
    PerfectSeparationWarning,
)

from citizentech_ml.estatistica.validacao import validar_base_municipal


def probabilidades_normais(populacao: Any) -> dict[str, Any]:
    """Calcula probabilidades sob a premissa de distribuição Normal dos registros."""
    arr = np.asarray(populacao, dtype=float).ravel()
    if len(arr) < 2:
        raise ValueError("A população precisa ter pelo menos 2 observações.")
    if not np.all(np.isfinite(arr)):
        raise ValueError("A população contém valores ausentes (NaN) ou infinitos.")

    sigma = float(np.std(arr, ddof=0))
    if sigma <= 0.0 or np.isclose(sigma, 0.0):
        raise ValueError("A população é constante (desvio padrão populacional zero).")

    mu = float(np.mean(arr))
    mediana = float(np.median(arr))

    p_menor_media = float(stats.norm.cdf(mu, loc=mu, scale=sigma))
    p_maior_mediana = float(stats.norm.sf(mediana, loc=mu, scale=sigma))

    if np.isclose(p_maior_mediana, 0.5):
        classif_mediana = "equiprovavel"
    elif p_maior_mediana > 0.5:
        classif_mediana = "provavel"
    else:
        classif_mediana = "pouco_provavel"

    interpretacao = (
        f"Sob premissa de Normalidade (mu={mu:.4f}, sigma_ddof0={sigma:.4f}): "
        f"P(X < media) = {p_menor_media:.4f} (equiprovável); "
        f"P(X > mediana) = {p_maior_mediana:.4f} ({classif_mediana})."
    )

    return {
        "media": mu,
        "mediana": mediana,
        "sigma_populacional": sigma,
        "probabilidade_menor_media": p_menor_media,
        "probabilidade_maior_mediana": p_maior_mediana,
        "classificacao_menor_media": "equiprovavel",
        "classificacao_maior_mediana": classif_mediana,
        "interpretacao": interpretacao,
    }


def testes_medias_enunciado(
    populacao: Any,
    seeds: tuple[int, int] = (42, 43),
) -> dict[str, Any]:
    """Testes unilaterais de médias (n=20 alpha=0.06 menor; n=25 alpha=0.09 maior)."""
    arr = np.asarray(populacao, dtype=float).ravel()
    if len(arr) < 25:
        raise ValueError(
            "A população precisa ter pelo menos 25 observações para os testes de médias."
        )
    if not np.all(np.isfinite(arr)):
        raise ValueError("A população contém valores ausentes (NaN) ou infinitos.")

    sigma_ref = float(np.std(arr, ddof=0))
    if sigma_ref <= 0.0 or np.isclose(sigma_ref, 0.0):
        raise ValueError("A população é constante (desvio padrão populacional zero).")
    mu_ref = float(np.mean(arr))

    # Amostra 1: teste unilateral à esquerda (menor), n=20, alpha=0.06
    seed_menor = int(seeds[0])
    rng_menor = np.random.default_rng(seed_menor)
    idx_menor = rng_menor.choice(len(arr), size=20, replace=False)
    amostra_menor = arr[idx_menor]
    media_menor = float(np.mean(amostra_menor))
    erro_padrao_menor = sigma_ref / np.sqrt(20)
    z_menor = float((media_menor - mu_ref) / erro_padrao_menor)
    alpha_menor = 0.06
    p_valor_menor = float(stats.norm.cdf(z_menor))
    z_crit_menor = float(stats.norm.ppf(alpha_menor))
    rejeita_menor = bool(z_menor < z_crit_menor)
    decisao_menor = (
        "Rejeita H0 ao nível de significância de 6% (evidência estatística de média menor)"
        if rejeita_menor
        else "Não rejeita H0 ao nível de significância de 6% (sem evidência de média menor)"
    )

    # Amostra 2: teste unilateral à direita (maior), n=25, alpha=0.09
    seed_maior = int(seeds[1])
    rng_maior = np.random.default_rng(seed_maior)
    idx_maior = rng_maior.choice(len(arr), size=25, replace=False)
    amostra_maior = arr[idx_maior]
    media_maior = float(np.mean(amostra_maior))
    erro_padrao_maior = sigma_ref / np.sqrt(25)
    z_maior = float((media_maior - mu_ref) / erro_padrao_maior)
    alpha_maior = 0.09
    p_valor_maior = float(stats.norm.sf(z_maior))
    z_crit_maior = float(stats.norm.ppf(1.0 - alpha_maior))
    rejeita_maior = bool(z_maior > z_crit_maior)
    decisao_maior = (
        "Rejeita H0 ao nível de significância de 9% (evidência estatística de média maior)"
        if rejeita_maior
        else "Não rejeita H0 ao nível de significância de 9% (sem evidência de média maior)"
    )

    return {
        "mu_ref": mu_ref,
        "sigma_ref": sigma_ref,
        "seeds": (seed_menor, seed_maior),
        "teste_menor": {
            "tipo": "unilateral_menor",
            "seed": seed_menor,
            "n": 20,
            "indices_amostrais": idx_menor.tolist(),
            "media_amostral": media_menor,
            "mu_ref": mu_ref,
            "sigma_ref": sigma_ref,
            "estatistica_z": z_menor,
            "p_valor": p_valor_menor,
            "alpha": alpha_menor,
            "z_critico": z_crit_menor,
            "regiao_critica": f"z < {z_crit_menor:.4f}",
            "rejeita_h0": rejeita_menor,
            "decisao": decisao_menor,
        },
        "teste_maior": {
            "tipo": "unilateral_maior",
            "seed": seed_maior,
            "n": 25,
            "indices_amostrais": idx_maior.tolist(),
            "media_amostral": media_maior,
            "mu_ref": mu_ref,
            "sigma_ref": sigma_ref,
            "estatistica_z": z_maior,
            "p_valor": p_valor_maior,
            "alpha": alpha_maior,
            "z_critico": z_crit_maior,
            "regiao_critica": f"z > {z_crit_maior:.4f}",
            "rejeita_h0": rejeita_maior,
            "decisao": decisao_maior,
        },
    }


testes_medias_enunciado.__test__ = False  # Evita captura indevida pelo coletor do pytest


def ajustar_ols_simples(
    X: Any,
    y: Any,
    ponto_previsao: Any = None,
) -> dict[str, Any]:
    """Ajusta modelo de regressão linear simples (OLS) com intercepto via statsmodels."""
    if isinstance(X, pd.DataFrame):
        if X.shape[1] != 1:
            raise ValueError("X para OLS simples deve conter exatamente uma coluna.")
        x_name = str(X.columns[0])
        x_vals = np.asarray(X.iloc[:, 0], dtype=float).ravel()
    elif isinstance(X, pd.Series):
        x_name = str(X.name) if X.name is not None else "x"
        x_vals = np.asarray(X, dtype=float).ravel()
    else:
        x_name = "x"
        x_vals = np.asarray(X, dtype=float).ravel()

    if isinstance(y, (pd.Series, pd.DataFrame)):
        y_name = str(y.name) if getattr(y, "name", None) is not None else "y"
        if isinstance(y, pd.DataFrame):
            if y.shape[1] != 1:
                raise ValueError("y deve ser unidimensional.")
            y_name = str(y.columns[0])
            y_vals = np.asarray(y.iloc[:, 0], dtype=float).ravel()
        else:
            y_vals = np.asarray(y, dtype=float).ravel()
    else:
        y_name = "y"
        y_vals = np.asarray(y, dtype=float).ravel()

    if len(x_vals) != len(y_vals):
        raise ValueError("X e y devem ter o mesmo comprimento.")
    if len(x_vals) < 3:
        raise ValueError("Amostra insuficiente para OLS simples (mínimo de 3 observações).")
    if not np.all(np.isfinite(x_vals)) or not np.all(np.isfinite(y_vals)):
        raise ValueError("Entradas contêm valores ausentes (NaN) ou infinitos.")

    var_x = float(np.var(x_vals, ddof=0))
    var_y = float(np.var(y_vals, ddof=0))
    if var_x <= 0.0 or np.isclose(var_x, 0.0):
        raise ValueError("X possui variância zero (constante / singularidade).")
    if var_y <= 0.0 or np.isclose(var_y, 0.0):
        raise ValueError("y possui variância zero (constante).")

    # Covariância e correlação de Pearson
    cov_mat = np.cov(x_vals, y_vals, ddof=1)
    corr_mat = np.corrcoef(x_vals, y_vals)
    cov_xy = float(cov_mat[0, 1])
    pearson_r = float(corr_mat[0, 1])

    # Ajuste OLS statsmodels com intercepto
    df_x = pd.DataFrame({x_name: x_vals})
    x_com_const = sm.add_constant(df_x, has_constant="add")
    modelo = sm.OLS(y_vals, x_com_const).fit()

    intercepto = float(modelo.params["const"])
    coef_angular = float(modelo.params[x_name])
    r2 = float(modelo.rsquared)
    r2_adj = float(modelo.rsquared_adj)
    f_stat = float(modelo.fvalue)
    f_p = float(modelo.f_pvalue)

    sinal = "+" if coef_angular >= 0 else "-"
    equacao = f"{y_name} = {intercepto:.4f} {sinal} {abs(coef_angular):.4f} * {x_name}"

    previsao = None
    if ponto_previsao is not None:
        if isinstance(ponto_previsao, dict):
            val_ponto = float(ponto_previsao.get(x_name, next(iter(ponto_previsao.values()))))
        elif isinstance(ponto_previsao, (pd.Series, pd.DataFrame)):
            val_ponto = float(ponto_previsao.iloc[0])
        else:
            val_ponto = float(ponto_previsao)
        previsao = float(intercepto + coef_angular * val_ponto)

    return {
        "tipo": "ols_simples",
        "variavel_x": x_name,
        "variavel_y": y_name,
        "coeficientes": {
            "const": intercepto,
            x_name: coef_angular,
        },
        "intercepto": intercepto,
        "coeficiente_angular": coef_angular,
        "equacao": equacao,
        "r2": r2,
        "r2_ajustado": r2_adj,
        "estatistica_f": f_stat,
        "p_f": f_p,
        "covariancia": cov_xy,
        "correlacao_pearson": pearson_r,
        "matriz_covariancia": cov_mat.tolist(),
        "matriz_correlacao": corr_mat.tolist(),
        "ponto_previsao": ponto_previsao,
        "previsao": previsao,
        "n_observacoes": len(x_vals),
    }


def ajustar_ols_multipla(
    X: Any,
    y: Any,
    ponto_previsao: Any = None,
) -> dict[str, Any]:
    """Ajusta modelo de regressão linear múltipla (OLS) com intercepto via statsmodels."""
    if isinstance(X, pd.DataFrame):
        df_x = X.copy()
    else:
        arr_x = np.asarray(X, dtype=float)
        if arr_x.ndim != 2:
            raise ValueError(
                "X para OLS múltipla deve ser bidimensional com pelo menos 2 preditores."
            )
        df_x = pd.DataFrame(arr_x, columns=[f"x{i + 1}" for i in range(arr_x.shape[1])])

    k = df_x.shape[1]
    if k < 2:
        raise ValueError("OLS múltipla requer pelo menos 2 variáveis explicativas.")

    if isinstance(y, (pd.Series, pd.DataFrame)):
        y_name = str(y.name) if getattr(y, "name", None) is not None else "y"
        if isinstance(y, pd.DataFrame):
            if y.shape[1] != 1:
                raise ValueError("y deve ser unidimensional.")
            y_name = str(y.columns[0])
            y_vals = np.asarray(y.iloc[:, 0], dtype=float).ravel()
        else:
            y_vals = np.asarray(y, dtype=float).ravel()
    else:
        y_name = "y"
        y_vals = np.asarray(y, dtype=float).ravel()

    if len(df_x) != len(y_vals):
        raise ValueError("X e y devem ter o mesmo comprimento.")
    if len(df_x) <= k + 1:
        raise ValueError(
            f"Amostra insuficiente para OLS múltipla (requer n > k + 1 = {k + 2} observações)."
        )
    if not np.all(np.isfinite(df_x.to_numpy())) or not np.all(np.isfinite(y_vals)):
        raise ValueError("Entradas contêm valores ausentes (NaN) ou infinitos.")

    for col in df_x.columns:
        var_col = float(np.var(df_x[col], ddof=0))
        if var_col <= 0.0 or np.isclose(var_col, 0.0):
            raise ValueError(f"A variável '{col}' possui variância zero.")
    var_y = float(np.var(y_vals, ddof=0))
    if var_y <= 0.0 or np.isclose(var_y, 0.0):
        raise ValueError("y possui variância zero.")

    x_com_const = sm.add_constant(df_x, has_constant="add")
    rank = int(np.linalg.matrix_rank(x_com_const.to_numpy()))
    if rank < k + 1:
        raise ValueError("Colinearidade perfeita ou matriz de desenho com rank insuficiente.")

    # Matrizes de covariância e correlação de Pearson de todo o conjunto [X, y]
    df_conjunto = df_x.copy()
    df_conjunto[y_name] = y_vals
    mat_cov = df_conjunto.cov(ddof=1).to_dict()
    mat_corr = df_conjunto.corr().to_dict()

    modelo = sm.OLS(y_vals, x_com_const).fit()
    coeficientes = {str(col): float(val) for col, val in modelo.params.items()}
    intercepto = float(modelo.params["const"])
    r2 = float(modelo.rsquared)
    r2_adj = float(modelo.rsquared_adj)
    f_stat = float(modelo.fvalue)
    f_p = float(modelo.f_pvalue)

    termos = [f"{intercepto:.4f}"]
    for col in df_x.columns:
        c_val = float(modelo.params[col])
        sinal = "+" if c_val >= 0 else "-"
        termos.append(f"{sinal} {abs(c_val):.4f} * {col}")
    equacao = f"{y_name} = " + " ".join(termos)

    previsao = None
    if ponto_previsao is not None:
        if isinstance(ponto_previsao, dict):
            ausentes = [c for c in df_x.columns if c not in ponto_previsao]
            if ausentes:
                raise ValueError(f"Ponto de previsão ausente para as variáveis: {ausentes}")
            ponto_vals = [1.0] + [float(ponto_previsao[c]) for c in df_x.columns]
        elif isinstance(ponto_previsao, pd.DataFrame):
            ponto_vals = [1.0] + [float(ponto_previsao[c].iloc[0]) for c in df_x.columns]
        elif isinstance(ponto_previsao, pd.Series):
            ponto_vals = [1.0] + [float(ponto_previsao[c]) for c in df_x.columns]
        else:
            arr_pt = np.asarray(ponto_previsao, dtype=float).ravel()
            if len(arr_pt) != k:
                raise ValueError(f"Ponto de previsão deve conter {k} valores correspondentes a X.")
            ponto_vals = [1.0] + [float(v) for v in arr_pt]
        previsao = float(modelo.predict(ponto_vals)[0])

    return {
        "tipo": "ols_multipla",
        "variaveis_x": list(df_x.columns),
        "variavel_y": y_name,
        "coeficientes": coeficientes,
        "intercepto": intercepto,
        "equacao": equacao,
        "r2": r2,
        "r2_ajustado": r2_adj,
        "estatistica_f": f_stat,
        "p_f": f_p,
        "matriz_covariancia": mat_cov,
        "matriz_correlacao": mat_corr,
        "ponto_previsao": ponto_previsao,
        "previsao": previsao,
        "n_observacoes": len(df_x),
    }


def ajustar_logistica_municipal(
    base: pd.DataFrame,
    ponto_previsao: Any = None,
    seed: int = 44,
) -> dict[str, Any]:
    """Ajusta modelo de regressão logística binária municipal via statsmodels Logit."""
    if not isinstance(base, pd.DataFrame):
        raise TypeError("base deve ser um pandas DataFrame.")

    # Validação e geração estrita das colunas de negócio sem vazamento
    df_validado = validar_base_municipal(base)

    # Emenda D11 aprovada: logística usa SOMENTE salario_medio_2024 e percentual_superior_2024
    colunas_x = ["salario_medio_2024", "percentual_superior_2024"]
    X = df_validado[colunas_x].copy()
    y = df_validado["crescimento"].to_numpy().astype(int)

    if len(X) < 4:
        raise ValueError(
            "Amostra insuficiente para regressão logística municipal (mínimo de 4 observações)."
        )

    classes_unicas = np.unique(y)
    if len(classes_unicas) < 2:
        raise ValueError(
            f"Regressão logística requer ambas as classes (0 e 1). "
            f"Encontrada classe única: {classes_unicas.tolist()}."
        )

    for col in colunas_x:
        var_col = float(np.var(X[col], ddof=0))
        if var_col <= 0.0 or np.isclose(var_col, 0.0):
            raise ValueError(f"A variável explicativa '{col}' possui variância zero.")

    x_const = sm.add_constant(X, has_constant="add")
    rank = int(np.linalg.matrix_rank(x_const.to_numpy()))
    if rank < 3:
        raise ValueError("Matriz explicativa possui rank insuficiente ou colinearidade perfeita.")

    idx_tr, idx_te = train_test_split(
        np.arange(len(X)),
        test_size=0.2,
        random_state=seed,
        stratify=y,
    )
    x_tr, y_tr = x_const.iloc[idx_tr], y[idx_tr]
    if len(y_tr) <= 3 or np.linalg.matrix_rank(x_tr) < 3:
        raise ValueError("Treino estratificado insuficiente ou com rank insuficiente.")
    if len(np.unique(y_tr)) < 2 or len(np.unique(y[idx_te])) < 2:
        raise ValueError("Ambas as classes devem estar presentes no treino e teste estratificados.")
    logit_mod = sm.Logit(y_tr, x_tr)
    with warnings.catch_warnings(record=True) as warn_list:
        warnings.simplefilter("always")
        try:
            resultado_logit = logit_mod.fit(disp=False)
        except (PerfectSeparationError, np.linalg.LinAlgError) as erro:
            raise ValueError(
                f"Falha no ajuste logístico devido a separação perfeita ou singularidade: {erro}"
            ) from erro

    for w in warn_list:
        if issubclass(w.category, (PerfectSeparationWarning, ConvergenceWarning)):
            msg_w = str(w.message)
            raise ValueError(
                f"Detecção de separação perfeita ou não convergência no modelo logístico: {msg_w}"
            )

    convergiu = bool(getattr(resultado_logit, "mle_retvals", {}).get("converged", True))
    if not convergiu:
        raise ValueError(
            "O modelo logístico não convergiu (possível quase-separação ou má especificação)."
        )

    params = resultado_logit.params
    if not np.all(np.isfinite(params)):
        raise ValueError("Coeficientes do modelo logístico não finitos (infinito ou NaN).")
    if np.any(np.abs(params) > 1e4):
        raise ValueError(
            "Detecção de separação perfeita ou coeficientes extremos no modelo logístico."
        )

    # Matriz de confusão e acurácia NO AJUSTE (in-sample)
    probabilidades_treino = np.asarray(resultado_logit.predict(x_tr), dtype=float)
    classes_preditas = (probabilidades_treino >= 0.5).astype(int)

    cm = confusion_matrix(y_tr, classes_preditas, labels=[0, 1])
    acuracia = float(accuracy_score(y_tr, classes_preditas))
    classes_teste = (resultado_logit.predict(x_const.iloc[idx_te]) >= 0.5).astype(int)
    avaliacao_teste = {
        "tipo": "teste_estratificado",
        "seed": seed,
        "fracao_teste": 0.2,
        "municipios_treino": df_validado.iloc[idx_tr]["municipio"].tolist(),
        "municipios_teste": df_validado.iloc[idx_te]["municipio"].tolist(),
        "matriz_confusao": confusion_matrix(y[idx_te], classes_teste, labels=[0, 1]).tolist(),
        "acuracia": float(accuracy_score(y[idx_te], classes_teste)),
    }

    matriz_confusao = {
        "rotulo": "Matriz de confusão no ajuste (in-sample, descritiva)",
        "ordem_classes": [0, 1],
        "matriz": cm.tolist(),
        "verdadeiros_negativos": int(cm[0, 0]),
        "falsos_positivos": int(cm[0, 1]),
        "falsos_negativos": int(cm[1, 0]),
        "verdadeiros_positivos": int(cm[1, 1]),
    }

    coeficientes = {str(col): float(val) for col, val in params.items()}
    beta_const = float(params["const"])
    beta_sal = float(params["salario_medio_2024"])
    beta_sup = float(params["percentual_superior_2024"])

    sinal_sal = "+" if beta_sal >= 0 else "-"
    sinal_sup = "+" if beta_sup >= 0 else "-"
    equacao = (
        f"logit(p) = {beta_const:.4f} {sinal_sal} {abs(beta_sal):.4f} * salario_medio_2024 "
        f"{sinal_sup} {abs(beta_sup):.4f} * percentual_superior_2024"
    )

    previsao_ponto = None
    if ponto_previsao is not None:
        if isinstance(ponto_previsao, dict):
            ausentes = [c for c in colunas_x if c not in ponto_previsao]
            if ausentes:
                raise ValueError(
                    f"Ponto de previsão ausente para variáveis explicativas: {ausentes}"
                )
            ponto_vals = [
                1.0,
                float(ponto_previsao["salario_medio_2024"]),
                float(ponto_previsao["percentual_superior_2024"]),
            ]
        elif isinstance(ponto_previsao, pd.DataFrame):
            ausentes = [c for c in colunas_x if c not in ponto_previsao.columns]
            if ausentes:
                raise ValueError(
                    f"Ponto de previsão ausente para variáveis explicativas: {ausentes}"
                )
            ponto_vals = [
                1.0,
                float(ponto_previsao["salario_medio_2024"].iloc[0]),
                float(ponto_previsao["percentual_superior_2024"].iloc[0]),
            ]
        elif isinstance(ponto_previsao, pd.Series):
            ausentes = [c for c in colunas_x if c not in ponto_previsao.index]
            if ausentes:
                raise ValueError(
                    f"Ponto de previsão ausente para variáveis explicativas: {ausentes}"
                )
            ponto_vals = [
                1.0,
                float(ponto_previsao["salario_medio_2024"]),
                float(ponto_previsao["percentual_superior_2024"]),
            ]
        else:
            arr_p = np.asarray(ponto_previsao, dtype=float).ravel()
            if len(arr_p) != 2:
                raise ValueError(
                    "Ponto de previsão deve conter 2 valores para as variáveis explicativas."
                )
            ponto_vals = [1.0, float(arr_p[0]), float(arr_p[1])]

        prob_ponto = float(resultado_logit.predict(ponto_vals)[0])
        classe_ponto = int(prob_ponto >= 0.5)
        previsao_ponto = {
            "probabilidade": prob_ponto,
            "classe": classe_ponto,
            "limiar": 0.5,
        }

    return {
        "tipo": "logistica_binaria_municipal",
        "variaveis_x": colunas_x,
        "variavel_y": "crescimento",
        "coeficientes": coeficientes,
        "equacao": equacao,
        "matriz_confusao_no_ajuste": matriz_confusao,
        "acuracia_no_ajuste": acuracia,
        "avaliacao_teste": avaliacao_teste,
        "limiar_classificacao": 0.5,
        "previsao_ponto": previsao_ponto,
        "nota_validacao": (
            "Ajuste somente nos 80% de treino; avaliacao_teste usa os 20% estratificados "
            f"(R07, seed{seed}). Métricas no ajuste são diagnóstico separado, "
            "não evidência de teste."
        ),
        "n_observacoes": len(X),
    }
