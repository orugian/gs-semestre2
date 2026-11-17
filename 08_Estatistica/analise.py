"""Programa portátil para análise estatística municipal (Q02 a Q06 e diagnósticos).

Integrantes: Guilherme Orugian — RM572882;
Lucas Henrique — RM571901; Rodrigo Bettio — RM573725.

Uso:
    python analise.py [CAMINHO_CSV] [--figuras DIR] [--json ARQ]

Executa de forma autônoma sem dependência do pacote citizentech_ml.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split

COLUNAS_OBRIGATORIAS = [
    "municipio",
    "uf",
    "admissoes_2024",
    "admissoes_2025",
    "salario_medio_2024",
    "percentual_superior_2024",
]

FIGURAS_PADRAO = [
    "q04_dispersao_reta.png",
    "q04_correlacao.png",
    "q05_dispersao_matriz.png",
    "q05_correlacao.png",
    "q06_matriz_confusao.png",
    "diag_normalidade.png",
    "diag_residuos_simples.png",
    "diag_residuos_multipla.png",
]

LIMITES_METODOLOGICOS = [
    "Normalidade assumida pelo enunciado, nao comprovada empiricamente.",
    "Testes Z usam sigma da populacao de referencia e SE=sigma/sqrt(n), sem correcao finita.",
    "Sem arquivos2026/revisoes2026; criterio e sementes nao alterados por resultado.",
    "Ponto previsto e cenario de medianas dos atributos, nao municipio observado.",
]


def calcular_sha256(caminho: Path) -> str:
    """Calcula o hash SHA-256 do arquivo informado."""
    hasher = hashlib.sha256()
    with open(caminho, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def _contem_booleano(serie: pd.Series) -> bool:
    """Detecta se uma série é booleana ou contém instâncias booleanas."""
    if pd.api.types.is_bool_dtype(serie):
        return True
    return any(isinstance(v, (bool, np.bool_)) for v in serie)


def carregar_e_validar_base(caminho_arquivo: str | Path) -> tuple[pd.DataFrame, str]:
    """Carrega e valida os dados de entrada (.csv ou .xlsx)."""
    caminho = Path(caminho_arquivo)
    if not caminho.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    sha256_arquivo = calcular_sha256(caminho)

    if caminho.suffix.lower() in [".xlsx", ".xls"]:
        try:
            df = pd.read_excel(caminho)
        except ImportError as err:
            raise RuntimeError(
                "Leitura de arquivos Excel (.xlsx/.xls) requer o pacote 'openpyxl' instalado."
            ) from err
    else:
        df = pd.read_csv(caminho, encoding="utf-8")

    if not isinstance(df, pd.DataFrame):
        raise TypeError("A entrada carregada deve ser um DataFrame.")
    if len(df) == 0:
        raise ValueError("A base municipal está vazia.")

    faltantes = [col for col in COLUNAS_OBRIGATORIAS if col not in df.columns]
    if faltantes:
        raise ValueError(f"Colunas obrigatórias ausentes na base municipal: {faltantes}")

    df_out = df.copy()

    # Identificador municipal
    if _contem_booleano(df_out["municipio"]):
        raise ValueError("Identificador municipal nulo ou inválido (booleano detectado).")
    if df_out["municipio"].isna().any():
        raise ValueError("Identificador municipal contém valores nulos (NaN / None).")
    mun_str = df_out["municipio"].astype(str).str.strip()
    if (mun_str == "").any() or mun_str.str.lower().isin(["none", "nan", "null"]).any():
        raise ValueError("Identificador municipal nulo ou vazio não é permitido.")
    df_out["municipio"] = mun_str

    if df_out["municipio"].duplicated().any():
        dups = df_out.loc[df_out["municipio"].duplicated(), "municipio"].unique().tolist()
        raise ValueError(f"Municípios duplicados encontrados na base: {dups}")

    # UF (Estado de São Paulo: SP ou 35)
    if df_out["uf"].isna().any():
        raise ValueError("A coluna 'uf' contém dados ausentes (NaN / None).")
    ufs_str = df_out["uf"].astype(str).str.strip().str.upper()
    ufs_invalidas = ufs_str[~ufs_str.isin(["SP", "35"])]
    if len(ufs_invalidas) > 0:
        raise ValueError(
            f"Apenas registros do estado de São Paulo (UF='SP' ou 35) são permitidos. "
            f"Encontrados: {ufs_invalidas.unique().tolist()}"
        )
    df_out["uf"] = ufs_str

    # Checagem de tipos e dados ausentes nas numéricas
    cols_num = [
        "admissoes_2024",
        "admissoes_2025",
        "salario_medio_2024",
        "percentual_superior_2024",
    ]
    for col in cols_num:
        if _contem_booleano(df_out[col]):
            raise ValueError(f"A coluna '{col}' não pode conter valores booleanos.")
        if df_out[col].isna().any():
            raise ValueError(f"A coluna '{col}' contém valores ausentes (NaN / None).")
        s_num = pd.to_numeric(df_out[col], errors="coerce")
        if s_num.isna().any() or np.isinf(s_num).any():
            raise ValueError(f"Coluna numérica '{col}' contém valores não finitos ou inválidos.")
        df_out[col] = s_num

    # Contagens inteiras não negativas
    for col_c in ["admissoes_2024", "admissoes_2025"]:
        if (df_out[col_c] < 0).any():
            raise ValueError(f"Coluna '{col_c}' não pode conter valores negativos.")
        if (df_out[col_c] % 1 != 0).any():
            raise ValueError(f"Coluna '{col_c}' deve conter contagens inteiras.")
        df_out[col_c] = df_out[col_c].astype(int)

    # Salário estritamente positivo
    if (df_out["salario_medio_2024"] <= 0).any():
        raise ValueError("salario_medio_2024 deve ser estritamente positivo (> 0).")
    df_out["salario_medio_2024"] = df_out["salario_medio_2024"].astype(float)

    # Percentual superior em [0, 100]
    p_sup = df_out["percentual_superior_2024"]
    if ((p_sup < 0.0) | (p_sup > 100.0)).any():
        raise ValueError("percentual_superior_2024 deve estar contido no intervalo [0, 100].")
    df_out["percentual_superior_2024"] = p_sup.astype(float)

    # Alvo crescimento: recalcular e conferir
    recalc_crescimento = (df_out["admissoes_2025"] > df_out["admissoes_2024"]).astype(int)
    if "crescimento" in df_out.columns:
        if (df_out["crescimento"].astype(int) != recalc_crescimento).any():
            raise ValueError(
                "Divergência detectada entre a coluna 'crescimento' "
                "e o recálculo (admissoes_2025 > admissoes_2024)."
            )
    df_out["crescimento"] = recalc_crescimento

    return df_out, sha256_arquivo


def calcular_q02(serie_admissoes: pd.Series) -> dict[str, Any]:
    """Q02: Distribuição Normal assumida para admissoes_2025."""
    arr = serie_admissoes.to_numpy(dtype=float).ravel()
    if len(arr) < 2:
        raise ValueError("A população precisa ter pelo menos 2 observações.")
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


def calcular_q03(
    serie_admissoes: pd.Series,
    seeds: tuple[int, int] = (42, 43),
) -> dict[str, Any]:
    """Q03: Testes de hipótese unilaterais para a média (Z menor e Z maior)."""
    arr = serie_admissoes.to_numpy(dtype=float).ravel()
    if len(arr) < 25:
        raise ValueError(
            "A população precisa ter pelo menos 25 observações para os testes de médias."
        )
    sigma_ref = float(np.std(arr, ddof=0))
    if sigma_ref <= 0.0 or np.isclose(sigma_ref, 0.0):
        raise ValueError("A população é constante (desvio padrão populacional zero).")
    mu_ref = float(np.mean(arr))

    # Teste menor: seed 42, n=20, alpha=0.06
    seed_menor = int(seeds[0])
    rng_menor = np.random.default_rng(seed_menor)
    idx_menor = rng_menor.choice(len(arr), size=20, replace=False)
    amostra_menor = arr[idx_menor]
    media_menor = float(np.mean(amostra_menor))
    se_menor = sigma_ref / np.sqrt(20)
    z_menor = float((media_menor - mu_ref) / se_menor)
    alpha_menor = 0.06
    p_menor = float(stats.norm.cdf(z_menor))
    z_crit_menor = float(stats.norm.ppf(alpha_menor))
    rejeita_menor = bool(z_menor < z_crit_menor)
    decisao_menor = (
        "Rejeita H0 ao nível de significância de 6% (evidência estatística de média menor)"
        if rejeita_menor
        else "Não rejeita H0 ao nível de significância de 6% (sem evidência de média menor)"
    )

    # Teste maior: seed 43, n=25, alpha=0.09
    seed_maior = int(seeds[1])
    rng_maior = np.random.default_rng(seed_maior)
    idx_maior = rng_maior.choice(len(arr), size=25, replace=False)
    amostra_maior = arr[idx_maior]
    media_maior = float(np.mean(amostra_maior))
    se_maior = sigma_ref / np.sqrt(25)
    z_maior = float((media_maior - mu_ref) / se_maior)
    alpha_maior = 0.09
    p_maior = float(stats.norm.sf(z_maior))
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
        "seeds": [seed_menor, seed_maior],
        "teste_menor": {
            "tipo": "unilateral_menor",
            "seed": seed_menor,
            "n": 20,
            "indices_amostrais": idx_menor.tolist(),
            "media_amostral": media_menor,
            "mu_ref": mu_ref,
            "sigma_ref": sigma_ref,
            "estatistica_z": z_menor,
            "p_valor": p_menor,
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
            "p_valor": p_maior,
            "alpha": alpha_maior,
            "z_critico": z_crit_maior,
            "regiao_critica": f"z > {z_crit_maior:.4f}",
            "rejeita_h0": rejeita_maior,
            "decisao": decisao_maior,
        },
    }


def calcular_q04(df: pd.DataFrame) -> tuple[dict[str, Any], Any]:
    """Q04: Análise bivariada (salario_medio_2024 x admissoes_2025)."""
    x_vals = df["salario_medio_2024"].to_numpy(dtype=float).ravel()
    y_vals = df["admissoes_2025"].to_numpy(dtype=float).ravel()

    cov_mat = np.cov(x_vals, y_vals, ddof=1)
    corr_mat = np.corrcoef(x_vals, y_vals)
    cov_xy = float(cov_mat[0, 1])
    pearson_r = float(corr_mat[0, 1])

    df_x = pd.DataFrame({"salario_medio_2024": x_vals})
    x_const = sm.add_constant(df_x, has_constant="add")
    modelo = sm.OLS(y_vals, x_const).fit()

    intercepto = float(modelo.params["const"])
    coef_angular = float(modelo.params["salario_medio_2024"])
    r2 = float(modelo.rsquared)
    r2_adj = float(modelo.rsquared_adj)
    f_stat = float(modelo.fvalue)
    f_p = float(modelo.f_pvalue)

    sinal = "+" if coef_angular >= 0 else "-"
    equacao = (
        f"admissoes_2025 = {intercepto:.4f} {sinal} {abs(coef_angular):.4f} * salario_medio_2024"
    )

    ponto_previsao = float(np.median(x_vals))
    previsao = float(intercepto + coef_angular * ponto_previsao)

    res = {
        "tipo": "ols_simples",
        "variavel_x": "salario_medio_2024",
        "variavel_y": "admissoes_2025",
        "coeficientes": {
            "const": intercepto,
            "salario_medio_2024": coef_angular,
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
    return res, modelo


def calcular_q05(df: pd.DataFrame) -> tuple[dict[str, Any], Any]:
    """Q05: Análise multivariada (OLS múltipla com salário e % superior)."""
    cols_x = ["salario_medio_2024", "percentual_superior_2024"]
    df_x = df[cols_x].copy()
    y_vals = df["admissoes_2025"].to_numpy(dtype=float).ravel()

    df_conjunto = df[cols_x + ["admissoes_2025"]].copy()
    mat_cov = df_conjunto.cov(ddof=1).to_dict()
    mat_corr = df_conjunto.corr().to_dict()

    x_const = sm.add_constant(df_x, has_constant="add")
    modelo = sm.OLS(y_vals, x_const).fit()

    coeficientes = {str(col): float(val) for col, val in modelo.params.items()}
    intercepto = float(modelo.params["const"])
    r2 = float(modelo.rsquared)
    r2_adj = float(modelo.rsquared_adj)
    f_stat = float(modelo.fvalue)
    f_p = float(modelo.f_pvalue)

    termos = [f"{intercepto:.4f}"]
    for col in cols_x:
        c_val = float(modelo.params[col])
        sinal = "+" if c_val >= 0 else "-"
        termos.append(f"{sinal} {abs(c_val):.4f} * {col}")
    equacao = "admissoes_2025 = " + " ".join(termos)

    ponto_previsao = {
        "salario_medio_2024": float(df["salario_medio_2024"].median()),
        "percentual_superior_2024": float(df["percentual_superior_2024"].median()),
    }
    ponto_vals = [
        1.0,
        ponto_previsao["salario_medio_2024"],
        ponto_previsao["percentual_superior_2024"],
    ]
    previsao = float(modelo.predict(ponto_vals)[0])

    res = {
        "tipo": "ols_multipla",
        "variaveis_x": cols_x,
        "variavel_y": "admissoes_2025",
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
        "n_observacoes": len(df),
    }
    return res, modelo


def calcular_q06(df: pd.DataFrame, seed: int = 44) -> tuple[dict[str, Any], Any]:
    """Q06: Regressão logística binária municipal estratificada."""
    cols_x = ["salario_medio_2024", "percentual_superior_2024"]
    X = df[cols_x].copy()
    y = df["crescimento"].to_numpy().astype(int)

    idx_tr, idx_te = train_test_split(
        np.arange(len(X)),
        test_size=0.2,
        random_state=seed,
        stratify=y,
    )

    x_const = sm.add_constant(X, has_constant="add")
    x_tr, y_tr = x_const.iloc[idx_tr], y[idx_tr]
    x_te, y_te = x_const.iloc[idx_te], y[idx_te]

    logit_mod = sm.Logit(y_tr, x_tr)
    resultado_logit = logit_mod.fit(disp=False)

    params = resultado_logit.params
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

    # In-sample (no ajuste, descritiva)
    prob_tr = np.asarray(resultado_logit.predict(x_tr), dtype=float)
    pred_tr = (prob_tr >= 0.5).astype(int)
    cm_tr = confusion_matrix(y_tr, pred_tr, labels=[0, 1])
    acc_tr = float(accuracy_score(y_tr, pred_tr))

    # Out-of-sample (no teste)
    prob_te = np.asarray(resultado_logit.predict(x_te), dtype=float)
    pred_te = (prob_te >= 0.5).astype(int)
    cm_te = confusion_matrix(y_te, pred_te, labels=[0, 1])
    acc_te = float(accuracy_score(y_te, pred_te))

    # Ponto de previsão = medianas
    ponto_previsao = {
        "salario_medio_2024": float(df["salario_medio_2024"].median()),
        "percentual_superior_2024": float(df["percentual_superior_2024"].median()),
    }
    ponto_vals = [
        1.0,
        ponto_previsao["salario_medio_2024"],
        ponto_previsao["percentual_superior_2024"],
    ]
    prob_ponto = float(resultado_logit.predict(ponto_vals)[0])
    classe_ponto = int(prob_ponto >= 0.5)

    res = {
        "tipo": "logistica_binaria_municipal",
        "variaveis_x": cols_x,
        "variavel_y": "crescimento",
        "coeficientes": coeficientes,
        "equacao": equacao,
        "matriz_confusao_no_ajuste": {
            "rotulo": "Matriz de confusão no ajuste (in-sample, descritiva)",
            "ordem_classes": [0, 1],
            "matriz": cm_tr.tolist(),
            "verdadeiros_negativos": int(cm_tr[0, 0]),
            "falsos_positivos": int(cm_tr[0, 1]),
            "falsos_negativos": int(cm_tr[1, 0]),
            "verdadeiros_positivos": int(cm_tr[1, 1]),
        },
        "acuracia_no_ajuste": acc_tr,
        "avaliacao_teste": {
            "tipo": "teste_estratificado",
            "seed": seed,
            "fracao_teste": 0.2,
            "municipios_treino": df.iloc[idx_tr]["municipio"].tolist(),
            "municipios_teste": df.iloc[idx_te]["municipio"].tolist(),
            "matriz_confusao": cm_te.tolist(),
            "acuracia": acc_te,
        },
        "limiar_classificacao": 0.5,
        "previsao_ponto": {
            "probabilidade": prob_ponto,
            "classe": classe_ponto,
            "limiar": 0.5,
        },
        "nota_validacao": (
            "Ajuste somente nos 80% de treino; avaliacao_teste usa os 20% estratificados "
            f"(R07, seed{seed}). Métricas no ajuste são diagnóstico separado, "
            "não evidência de teste."
        ),
        "n_observacoes": len(df),
    }
    return res, resultado_logit


def calcular_diagnostico(serie_admissoes: pd.Series) -> dict[str, Any]:
    """Diagnóstico complementar de normalidade (Shapiro-Wilk original e log1p)."""
    arr = serie_admissoes.to_numpy(dtype=float).ravel()
    w_orig, p_orig = stats.shapiro(arr)
    w_log, p_log = stats.shapiro(np.log1p(arr))

    return {
        "n": len(arr),
        "teste": "Shapiro-Wilk",
        "natureza": "diagnostico complementar; Normal assumida mantida nos itens obrigatorios",
        "original": {
            "estatistica_w": float(w_orig),
            "p_valor": float(p_orig),
        },
        "log1p": {
            "estatistica_w": float(w_log),
            "p_valor": float(p_log),
        },
    }


def calcular_pontos_extremos_salario(df: pd.DataFrame) -> dict[str, Any]:
    """Calcula bloco descritivo com os 3 maiores salários médios de 2024 e razão para a mediana."""
    mediana = float(df["salario_medio_2024"].median())
    df_sorted = df.sort_values(by="salario_medio_2024", ascending=False).head(3)

    tem_validos = "n_salarios_validos_2024" in df.columns
    municipios = []
    for _, row in df_sorted.iterrows():
        sal = float(row["salario_medio_2024"])
        adm24 = int(row["admissoes_2024"])
        n_val = int(row["n_salarios_validos_2024"]) if tem_validos else adm24
        razao = float(sal / mediana) if mediana > 0 else 0.0
        municipios.append(
            {
                "municipio": str(row["municipio"]),
                "admissoes_2024": adm24,
                "salario_medio_2024": sal,
                "n_salarios_validos_2024": n_val,
                "razao_para_mediana": razao,
            }
        )

    return {
        "mediana_salario_medio_2024": mediana,
        "municipios": municipios,
        "top_3": municipios,
        "observacao": (
            "Decisão pré-registrada D11: pontos mantidos em todos os cálculos "
            "sem corte pós-observação. Hipótese de erro de declaração/escala "
            "do campo salário no Caged não verificada."
        ),
    }


def _formatar_ptbr(
    val: float,
    casas: int = 4,
    cientifico: bool = False,
    potencia_limite: float = 1e-3,
    separador_milhar: bool = False,
) -> str:
    """Formata número no padrão brasileiro com vírgula decimal e notação científica limpa."""
    if cientifico or (0 < abs(val) < potencia_limite):
        texto = f"{val:.{casas}e}"
        partes = texto.split("e")
        mantissa = partes[0].replace(".", ",")
        exp = int(partes[1])
        mapa_exp = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
        return f"{mantissa}×10{str(exp).translate(mapa_exp)}"
    if separador_milhar:
        texto = f"{val:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return texto
    texto = f"{val:.{casas}f}"
    return texto.replace(".", ",")


def gerar_todas_figuras(
    df: pd.DataFrame,
    res_q04: dict[str, Any],
    modelo_q04: Any,
    res_q05: dict[str, Any],
    modelo_q05: Any,
    res_q06: dict[str, Any],
    diag: dict[str, Any],
    dir_figuras: Path,
) -> list[str]:
    """Gera as 8 figuras exigidas em formato PNG com dpi >= 120."""
    dir_figuras.mkdir(parents=True, exist_ok=True)
    figuras_salvas = []

    # 1. q04_dispersao_reta.png (painel original + painel auxiliar log)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    x_q04 = df["salario_medio_2024"].to_numpy(dtype=float)
    y_q04 = df["admissoes_2025"].to_numpy(dtype=float)

    # Painel 1: escala original com reta OLS
    ax1.scatter(
        x_q04,
        y_q04,
        alpha=0.6,
        color="#1f77b4",
        edgecolors="none",
        label="Municípios de SP",
    )
    xs = np.linspace(x_q04.min(), x_q04.max(), 200)
    ys = res_q04["intercepto"] + res_q04["coeficiente_angular"] * xs
    ax1.plot(xs, ys, color="#d62728", lw=2, label="Reta OLS")
    ax1.set_title(
        "Regressão Linear Simples: Admissões 2025 x Salário Médio 2024 (Q04)",
        fontsize=10,
    )
    ax1.set_xlabel("Salário Médio de Admissão em 2024 (R$)", fontsize=9)
    ax1.set_ylabel("Admissões Formais em 2025 (contagem)", fontsize=9)

    eq_ptbr = (
        f"admissoes_2025 = {_formatar_ptbr(res_q04['intercepto'], 4)} + "
        f"{_formatar_ptbr(res_q04['coeficiente_angular'], 4)} * salario_medio_2024"
    )
    r2_ptbr = _formatar_ptbr(res_q04["r2"], 4, cientifico=True)
    f_ptbr = _formatar_ptbr(res_q04["estatistica_f"], 4, cientifico=True)
    pf_ptbr = _formatar_ptbr(res_q04["p_f"], 4)
    pt_ptbr = _formatar_ptbr(res_q04["ponto_previsao"], 2, separador_milhar=True)
    prev_ptbr = _formatar_ptbr(res_q04["previsao"], 2)

    texto_box = (
        f"Equação: {eq_ptbr}\n"
        f"R² = {r2_ptbr} | F = {f_ptbr} (p={pf_ptbr})\n"
        f"Previsão na mediana (R$ {pt_ptbr}): {prev_ptbr}"
    )
    ax1.text(
        0.05,
        0.95,
        texto_box,
        transform=ax1.transAxes,
        verticalalignment="top",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.9, edgecolor="gray"),
        fontsize=8,
    )
    ax1.legend(loc="upper right")
    ax1.grid(True, linestyle="--", alpha=0.5)

    # Painel 2: visualização auxiliar com eixo X em escala log
    ax2.scatter(
        x_q04,
        y_q04,
        alpha=0.6,
        color="#1f77b4",
        edgecolors="none",
        label="Municípios de SP",
    )
    xs_log = np.geomspace(max(float(x_q04.min()), 1.0), float(x_q04.max()), 200)
    ys_log = res_q04["intercepto"] + res_q04["coeficiente_angular"] * xs_log
    ax2.plot(xs_log, ys_log, color="#d62728", lw=2, label="Reta OLS (escala original)")
    ax2.set_xscale("log")
    ax2.set_title(
        "Visualização auxiliar — eixo X em escala log (os cálculos usam a escala original)",
        fontsize=10,
    )
    ax2.set_xlabel("Salário Médio de Admissão em 2024 (R$, escala log)", fontsize=9)
    ax2.set_ylabel("Admissões Formais em 2025 (contagem)", fontsize=9)
    ax2.legend(loc="upper right")
    ax2.grid(True, linestyle="--", alpha=0.5, which="both")

    idx_top2 = np.argsort(x_q04)[-2:]
    for idx_p in idx_top2:
        xp = float(x_q04[idx_p])
        yp = float(y_q04[idx_p])
        mun_p = str(df.iloc[idx_p]["municipio"])
        val_sal_str = _formatar_ptbr(xp, 2, separador_milhar=True)
        ax2.annotate(
            f"{mun_p}: R$ {val_sal_str}",
            xy=(xp, yp),
            xytext=(xp * 0.5, max(yp * 1.5, yp + 20)),
            arrowprops=dict(arrowstyle="->", color="#333333", lw=0.8),
            fontsize=8,
            ha="center",
        )

    plt.tight_layout()
    nome_f1 = "q04_dispersao_reta.png"
    plt.savefig(dir_figuras / nome_f1, dpi=120)
    plt.close()
    figuras_salvas.append(nome_f1)

    # 2. q04_correlacao.png
    fig, ax = plt.subplots(figsize=(6, 5))
    mat_corr_q04 = np.array(res_q04["matriz_correlacao"])
    cax = ax.imshow(mat_corr_q04, cmap="coolwarm", vmin=-1, vmax=1)
    labels_q04 = ["Salário 2024", "Admissões 2025"]
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(labels_q04, rotation=15, ha="right")
    ax.set_yticklabels(labels_q04)
    for i in range(2):
        for j in range(2):
            val = mat_corr_q04[i, j]
            cor_txt = "black" if abs(val) < 0.6 else "white"
            val_txt = _formatar_ptbr(val, 4)
            ax.text(j, i, val_txt, ha="center", va="center", color=cor_txt, fontsize=11)
    fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04)
    ax.set_title("Matriz de Correlação Linear de Pearson (Q04)", fontsize=11)
    plt.tight_layout()
    nome_f2 = "q04_correlacao.png"
    plt.savefig(dir_figuras / nome_f2, dpi=120)
    plt.close()
    figuras_salvas.append(nome_f2)

    # 3. q05_dispersao_matriz.png
    cols_mat = ["salario_medio_2024", "percentual_superior_2024", "admissoes_2025"]
    df_mat = df[cols_mat].rename(
        columns={
            "salario_medio_2024": "Salário (R$)",
            "percentual_superior_2024": "% Superior (%)",
            "admissoes_2025": "Admissões 2025",
        }
    )
    axes = pd.plotting.scatter_matrix(
        df_mat,
        figsize=(9, 9),
        diagonal="hist",
        color="#1f77b4",
        alpha=0.6,
    )
    plt.suptitle("Matriz de Dispersão das Variáveis Quantitativas (Q05)", fontsize=13, y=0.98)
    for ax_row in axes:
        for ax_item in ax_row:
            ax_item.xaxis.label.set_fontsize(9)
            ax_item.yaxis.label.set_fontsize(9)
    plt.tight_layout()
    nome_f3 = "q05_dispersao_matriz.png"
    plt.savefig(dir_figuras / nome_f3, dpi=120)
    plt.close()
    figuras_salvas.append(nome_f3)

    # 4. q05_correlacao.png
    fig, ax = plt.subplots(figsize=(7, 6))
    cols_q05 = ["salario_medio_2024", "percentual_superior_2024", "admissoes_2025"]
    mat_corr_q05 = df[cols_q05].corr().to_numpy()
    cax = ax.imshow(mat_corr_q05, cmap="coolwarm", vmin=-1, vmax=1)
    labels_q05 = ["Salário 2024", "% Superior 2024", "Admissões 2025"]
    ax.set_xticks([0, 1, 2])
    ax.set_yticks([0, 1, 2])
    ax.set_xticklabels(labels_q05, rotation=20, ha="right")
    ax.set_yticklabels(labels_q05)
    for i in range(3):
        for j in range(3):
            val = mat_corr_q05[i, j]
            cor_txt = "black" if abs(val) < 0.6 else "white"
            val_txt = _formatar_ptbr(val, 4)
            ax.text(j, i, val_txt, ha="center", va="center", color=cor_txt, fontsize=10)
    fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04)
    ax.set_title("Matriz de Correlação Linear de Pearson (Q05)", fontsize=11)
    plt.tight_layout()
    nome_f4 = "q05_correlacao.png"
    plt.savefig(dir_figuras / nome_f4, dpi=120)
    plt.close()
    figuras_salvas.append(nome_f4)

    # 5. q06_matriz_confusao.png (Conjunto de Teste)
    fig, ax = plt.subplots(figsize=(6, 5))
    cm_te = np.array(res_q06["avaliacao_teste"]["matriz_confusao"])
    cax = ax.imshow(cm_te, cmap="Blues", vmin=0, vmax=max(cm_te.max() + 2, 1))
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(["0 (Não Cresce)", "1 (Cresce)"])
    ax.set_yticklabels(["0 (Não Cresce)", "1 (Cresce)"])
    ax.set_xlabel("Classe Predita", fontsize=10)
    ax.set_ylabel("Classe Real (Observada)", fontsize=10)
    rotulos_celulas = [
        [f"VN\n{cm_te[0, 0]}", f"FP\n{cm_te[0, 1]}"],
        [f"FN\n{cm_te[1, 0]}", f"VP\n{cm_te[1, 1]}"],
    ]
    for i in range(2):
        for j in range(2):
            cor_c = "black" if cm_te[i, j] < cm_te.max() / 2 else "white"
            ax.text(
                j,
                i,
                rotulos_celulas[i][j],
                ha="center",
                va="center",
                color=cor_c,
                fontsize=12,
                fontweight="bold",
            )
    fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04)
    acc_val = res_q06["avaliacao_teste"]["acuracia"]
    acc_ptbr = f"{acc_val * 100:.2f}%".replace(".", ",")
    ax.set_title(
        f"Matriz de Confusão no Teste (Q06)\nAcurácia = {acc_ptbr} (n=46)",
        fontsize=11,
    )
    plt.tight_layout()
    nome_f5 = "q06_matriz_confusao.png"
    plt.savefig(dir_figuras / nome_f5, dpi=120)
    plt.close()
    figuras_salvas.append(nome_f5)

    # 6. diag_normalidade.png
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 8))
    admissoes = df["admissoes_2025"].to_numpy(dtype=float)
    log_adm = np.log1p(admissoes)

    w_orig = diag["original"]["estatistica_w"]
    p_orig = diag["original"]["p_valor"]
    w_orig_ptbr = _formatar_ptbr(w_orig, 4)
    p_orig_ptbr = _formatar_ptbr(p_orig, 2, cientifico=True)
    ax1.hist(admissoes, bins=30, color="#1f77b4", edgecolor="black", alpha=0.7)
    ax1.set_title(
        f"Admissões 2025 Original\nShapiro-Wilk W = {w_orig_ptbr} (p = {p_orig_ptbr})",
        fontsize=10,
    )
    ax1.set_xlabel("Admissões 2025", fontsize=9)
    ax1.set_ylabel("Frequência", fontsize=9)

    stats.probplot(admissoes, dist="norm", plot=ax2)
    ax2.set_title("Q-Q Plot: Admissões 2025 Original", fontsize=10)
    ax2.set_xlabel("Quantis Teóricos da Normal", fontsize=9)
    ax2.set_ylabel("Quantis Amostrais", fontsize=9)

    w_log = diag["log1p"]["estatistica_w"]
    p_log = diag["log1p"]["p_valor"]
    w_log_ptbr = _formatar_ptbr(w_log, 4)
    p_log_ptbr = _formatar_ptbr(p_log, 2, cientifico=True)
    ax3.hist(log_adm, bins=30, color="#2ca02c", edgecolor="black", alpha=0.7)
    ax3.set_title(
        f"Admissões 2025 em log(1 + x)\nShapiro-Wilk W = {w_log_ptbr} (p = {p_log_ptbr})",
        fontsize=10,
    )
    ax3.set_xlabel("log(1 + Admissões 2025)", fontsize=9)
    ax3.set_ylabel("Frequência", fontsize=9)

    stats.probplot(log_adm, dist="norm", plot=ax4)
    ax4.set_title("Q-Q Plot: log(1 + Admissões 2025)", fontsize=10)
    ax4.set_xlabel("Quantis Teóricos da Normal", fontsize=9)
    ax4.set_ylabel("Quantis Amostrais", fontsize=9)

    plt.suptitle(
        "Diagnóstico Complementar de Normalidade da Variável Admissões 2025",
        fontsize=12,
        y=0.99,
    )
    plt.tight_layout()
    nome_f6 = "diag_normalidade.png"
    plt.savefig(dir_figuras / nome_f6, dpi=120)
    plt.close()
    figuras_salvas.append(nome_f6)

    # 7. diag_residuos_simples.png
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5))
    residuos_s = modelo_q04.resid
    ajustados_s = modelo_q04.fittedvalues
    ax1.scatter(ajustados_s, residuos_s, alpha=0.6, color="#1f77b4")
    ax1.axhline(0, color="red", linestyle="--", lw=1.5)
    ax1.set_title("Resíduos x Valores Ajustados (OLS Simples)", fontsize=10)
    ax1.set_xlabel("Valores Ajustados (Fitted Values)", fontsize=9)
    ax1.set_ylabel("Resíduos Amostrais", fontsize=9)
    ax1.grid(True, linestyle="--", alpha=0.5)

    stats.probplot(residuos_s, dist="norm", plot=ax2)
    ax2.set_title("Q-Q Plot dos Resíduos (OLS Simples)", fontsize=10)
    ax2.set_xlabel("Quantis Teóricos da Normal", fontsize=9)
    ax2.set_ylabel("Quantis dos Resíduos", fontsize=9)
    ax2.grid(True, linestyle="--", alpha=0.5)

    plt.suptitle("Diagnóstico de Resíduos: Regressão Linear Simples (Q04)", fontsize=12, y=0.98)
    plt.tight_layout()
    nome_f7 = "diag_residuos_simples.png"
    plt.savefig(dir_figuras / nome_f7, dpi=120)
    plt.close()
    figuras_salvas.append(nome_f7)

    # 8. diag_residuos_multipla.png
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5))
    residuos_m = modelo_q05.resid
    ajustados_m = modelo_q05.fittedvalues
    ax1.scatter(ajustados_m, residuos_m, alpha=0.6, color="#2ca02c")
    ax1.axhline(0, color="red", linestyle="--", lw=1.5)
    ax1.set_title("Resíduos x Valores Ajustados (OLS Múltipla)", fontsize=10)
    ax1.set_xlabel("Valores Ajustados (Fitted Values)", fontsize=9)
    ax1.set_ylabel("Resíduos Amostrais", fontsize=9)
    ax1.grid(True, linestyle="--", alpha=0.5)

    stats.probplot(residuos_m, dist="norm", plot=ax2)
    ax2.set_title("Q-Q Plot dos Resíduos (OLS Múltipla)", fontsize=10)
    ax2.set_xlabel("Quantis Teóricos da Normal", fontsize=9)
    ax2.set_ylabel("Quantis dos Resíduos", fontsize=9)
    ax2.grid(True, linestyle="--", alpha=0.5)

    plt.suptitle("Diagnóstico de Resíduos: Regressão Linear Múltipla (Q05)", fontsize=12, y=0.98)
    plt.tight_layout()
    nome_f8 = "diag_residuos_multipla.png"
    plt.savefig(dir_figuras / nome_f8, dpi=120)
    plt.close()
    figuras_salvas.append(nome_f8)

    return figuras_salvas


def executar_analise(
    caminho_csv: str | Path,
    dir_figuras: str | Path | None = None,
) -> dict[str, Any]:
    """Executa a análise estatística portátil completa a partir de um arquivo CSV ou Excel."""
    df, sha256_csv = carregar_e_validar_base(caminho_csv)

    q02 = calcular_q02(df["admissoes_2025"])
    q03 = calcular_q03(df["admissoes_2025"], seeds=(42, 43))
    q04, mod_q04 = calcular_q04(df)
    q05, mod_q05 = calcular_q05(df)
    q06, mod_q06 = calcular_q06(df, seed=44)
    diagnostico = calcular_diagnostico(df["admissoes_2025"])
    pontos_extremos = calcular_pontos_extremos_salario(df)

    if dir_figuras is not None:
        figuras_geradas = gerar_todas_figuras(
            df=df,
            res_q04=q04,
            modelo_q04=mod_q04,
            res_q05=q05,
            modelo_q05=mod_q05,
            res_q06=q06,
            diag=diagnostico,
            dir_figuras=Path(dir_figuras),
        )
    else:
        figuras_geradas = list(FIGURAS_PADRAO)

    return {
        "base": {
            "n": len(df),
            "sha256": sha256_csv,
            "colunas_usadas": [
                "municipio",
                "uf",
                "admissoes_2024",
                "admissoes_2025",
                "salario_medio_2024",
                "percentual_superior_2024",
                "crescimento",
            ],
        },
        "q02": q02,
        "q03": q03,
        "q04": q04,
        "q05": q05,
        "q06": q06,
        "diagnostico": diagnostico,
        "pontos_extremos_salario": pontos_extremos,
        "figuras": figuras_geradas,
        "limites": list(LIMITES_METODOLOGICOS),
    }


def imprimir_relatorio_terminal(res: dict[str, Any]) -> None:
    """Imprime no terminal o relatório resumido das questões 02 a 06 e diagnósticos."""
    print("=" * 80)
    print("RELATÓRIO ESTATÍSTICO MUNICIPAL — CITIZENTECH (D11)")
    print(f"Base: n = {res['base']['n']} municípios | SHA-256 = {res['base']['sha256'][:16]}...")
    print("=" * 80)

    # Q02
    q02 = res["q02"]
    print("\n[QUESTÃO 02] Distribuição Normal Assumida (Variável: admissoes_2025)")
    print(f"  Média populacional (mu):           {q02['media']:.4f}")
    print(f"  Mediana populacional:             {q02['mediana']:.4f}")
    print(f"  Desvio padrão populacional (ddof=0): {q02['sigma_populacional']:.4f}")
    p_menor = q02["probabilidade_menor_media"]
    p_maior = q02["probabilidade_maior_mediana"]
    c_menor = q02["classificacao_menor_media"]
    c_maior = q02["classificacao_maior_mediana"]
    print(f"  a) P(X < média):                   {p_menor:.4f} -> {c_menor}")
    print(f"  b) P(X > mediana):                 {p_maior:.4f} -> {c_maior}")
    print(f"  Interpretação: {q02['interpretacao']}")

    # Q03
    q03 = res["q03"]
    tm, tM = q03["teste_menor"], q03["teste_maior"]
    print("\n[QUESTÃO 03] Teste de Hipótese para a Média (Teste Z, sem correção finita)")
    print(f"  Ref. populacional: mu_ref = {q03['mu_ref']:.4f} | sigma_ref = {q03['sigma_ref']:.4f}")
    print(
        f"  a) Unilateral à Esquerda (n={tm['n']}, alpha={tm['alpha']:.0%}, seed={tm['seed']}):"
    )
    print(
        f"     x_bar = {tm['media_amostral']:.4f} | z = {tm['estatistica_z']:.4f} "
        f"| z_crit = {tm['z_critico']:.4f} | p-valor = {tm['p_valor']:.4f}"
    )
    print(f"     Decisão: {tm['decisao']}")
    print(f"  b) Unilateral à Direita (n={tM['n']}, alpha={tM['alpha']:.0%}, seed={tM['seed']}):")
    print(
        f"     x_bar = {tM['media_amostral']:.4f} | z = {tM['estatistica_z']:.4f} "
        f"| z_crit = {tM['z_critico']:.4f} | p-valor = {tM['p_valor']:.4f}"
    )
    print(f"     Decisão: {tM['decisao']}")

    # Q04
    q04 = res["q04"]
    print("\n[QUESTÃO 04] Análise Bivariada (Regressão Linear Simples OLS)")
    print(f"  Covariância amostral (ddof=1):     {q04['covariancia']:.4f}")
    print(f"  Correlação de Pearson (r):         {q04['correlacao_pearson']:.6f}")
    print(f"  Equação OLS:                       {q04['equacao']}")
    print(
        f"  Adequação do Modelo:               R² = {q04['r2']:.6e} "
        f"| F = {q04['estatistica_f']:.6e} (p-valor = {q04['p_f']:.4f})"
    )
    print(
        f"  Previsão no ponto (X = R$ {q04['ponto_previsao']:.2f}): "
        f"Admissões previstas = {q04['previsao']:.4f}"
    )

    # Q05
    q05 = res["q05"]
    print("\n[QUESTÃO 05] Análise Multivariada (Regressão Linear Múltipla OLS)")
    print(f"  Equação OLS Múltipla:              {q05['equacao']}")
    print(
        f"  Adequação do Modelo:               R² = {q05['r2']:.4f} "
        f"| F = {q05['estatistica_f']:.4f} (p-valor = {q05['p_f']:.4f})"
    )
    pt5 = q05["ponto_previsao"]
    print(
        f"  Previsão no ponto (Salário={pt5['salario_medio_2024']:.2f}, "
        f"%Sup={pt5['percentual_superior_2024']:.2f}%):"
    )
    print(f"     Admissões previstas = {q05['previsao']:.4f}")

    # Q06
    q06 = res["q06"]
    av_te = q06["avaliacao_teste"]
    print("\n[QUESTÃO 06] Regressão Logística Binária Municipal (Statsmodels Logit)")
    print(f"  Equação logit:                     {q06['equacao']}")
    print(f"  Avaliação no Ajuste (in-sample):   Acurácia = {q06['acuracia_no_ajuste']:.2%}")
    print(f"  Avaliação no Teste (estratificado): Acurácia = {av_te['acuracia']:.2%}")
    print(f"     Matriz de Confusão no Teste:    {av_te['matriz_confusao']}")
    pt6 = q06["previsao_ponto"]
    print(
        f"  Classificação no ponto de medianas: Probabilidade = {pt6['probabilidade']:.4f} "
        f"-> Classe Predita = {pt6['classe']}"
    )

    # Diagnóstico
    diag = res["diagnostico"]
    w_o = diag["original"]["estatistica_w"]
    p_o = diag["original"]["p_valor"]
    w_l = diag["log1p"]["estatistica_w"]
    p_l = diag["log1p"]["p_valor"]
    print("\n[DIAGNÓSTICO COMPLEMENTAR] Teste de Shapiro-Wilk (admissoes_2025)")
    print(f"  Original: W = {w_o:.6f} | p-valor = {p_o:.2e} -> Não normal (p < 0.05)")
    print(f"  log1p:    W = {w_l:.6f} | p-valor = {p_l:.2e} -> Não normal (p < 0.05)")

    # Pontos extremos de salário
    if "pontos_extremos_salario" in res:
        pts = res["pontos_extremos_salario"]
        med = pts["mediana_salario_medio_2024"]
        print(
            "\n[PONTOS EXTREMOS DE SALÁRIO] Top 3 maiores 'salario_medio_2024' (pré-registro D11)"
        )
        print(f"  Mediana populacional de salário médio 2024: R$ {med:.2f}")
        for item in pts["municipios"]:
            print(
                f"  - Município {item['municipio']}: R$ {item['salario_medio_2024']:.2f} "
                f"({item['razao_para_mediana']:.2f}x a mediana) | "
                f"Admissões 2024: {item['admissoes_2024']} | "
                f"Salários válidos 2024: {item['n_salarios_validos_2024']}"
            )
        print("  Nota: Todos os pontos foram mantidos nos cálculos conforme pré-registro D11.")
    print("=" * 80)


def main() -> None:
    """Ponto de entrada de linha de comando."""
    parser = argparse.ArgumentParser(description="Análise estatística municipal portátil")
    parser.add_argument(
        "caminho_csv",
        nargs="?",
        default=str(Path(__file__).parent / "base_municipal.csv"),
        help="Caminho para o CSV ou Excel (padrão: base_municipal.csv ao lado do script)",
    )
    parser.add_argument(
        "--figuras",
        default=str(Path(__file__).parent / "figuras"),
        help="Diretório para salvar as figuras geradas (padrão: figuras/ ao lado do script)",
    )
    parser.add_argument(
        "--json",
        default=None,
        help="Caminho para salvar o resultado em formato JSON",
    )
    args = parser.parse_args()

    caminho_csv = Path(args.caminho_csv)
    dir_figuras = Path(args.figuras) if args.figuras else None

    resultado = executar_analise(caminho_csv, dir_figuras=dir_figuras)
    imprimir_relatorio_terminal(resultado)

    if args.json:
        caminho_json = Path(args.json)
        caminho_json.parent.mkdir(parents=True, exist_ok=True)
        with open(caminho_json, "w", encoding="utf-8") as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2, allow_nan=False)
        print(f"\nResultado salvo em JSON: {caminho_json}")


if __name__ == "__main__":
    main()
