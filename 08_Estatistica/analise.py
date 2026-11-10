"""GS 2026.2 - Estatística com R e Python - questões 02 a 06.

Uso:  python analise.py                (usa ARQUIVO abaixo)
      python analise.py dados/base.csv (ou .xlsx)
Os gráficos são salvos em figuras/ para o relatório (questão 07).
A base deve ser REAL (não são aceitos dados fictícios) e precisa ser entregue em .csv ou .xlsx.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix

# ================================================================ CONFIGURAÇÃO (TODO)
ARQUIVO = "dados/base.csv"
SEPARADOR = ","
VAR_NORMAL = "TODO_coluna"            # Q02 e Q03: variável numérica
Q4_X, Q4_Y = "TODO_x", "TODO_y"       # Q04: explicativa e resposta
Q4_X_PREVISAO = 0.0                   # Q04f: valor de X para a previsão
Q5_Y = "TODO_y"                       # Q05: resposta
Q5_X = ["TODO_x1", "TODO_x2"]         # Q05: >= 2 explicativas (total >= 3 variáveis)
Q5_NOVO = {"TODO_x1": 0.0, "TODO_x2": 0.0}
Q6_ALVO = "TODO_alvo_binario"         # Q06: coluna 0/1 (ou criar a partir de um limiar)
Q6_X = ["TODO_x1", "TODO_x2"]         # Q06: >= 2 explicativas
Q6_NOVO = {"TODO_x1": 0.0, "TODO_x2": 0.0}
SEMENTE = 42
# =====================================================================================

sys.stdout.reconfigure(encoding="utf-8")  # acentos no terminal do Windows
PASTA_FIG =os.path.join(os.path.dirname(os.path.abspath(__file__)), "figuras")
os.makedirs(PASTA_FIG, exist_ok=True)


def titulo(txt):
    print("\n" + "=" * 80 + f"\n{txt}\n" + "=" * 80)


def salvar(nome):
    plt.tight_layout()
    plt.savefig(os.path.join(PASTA_FIG, nome), dpi=120)
    plt.close()


def classificar_evento(p):
    if p == 0:
        return "evento impossível"
    if p == 1:
        return "evento certo"
    if np.isclose(p, 0.5):
        return "evento equiprovável (50%)"
    return "evento provável (p > 0,5)" if p > 0.5 else "evento pouco provável (p < 0,5)"


def carregar(caminho):
    if caminho.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(caminho)
    return pd.read_csv(caminho, sep=SEPARADOR)


def regressao_ols(X, y):
    """Mínimos quadrados com R², F e p-valor do Teste F."""
    X1 = np.column_stack([np.ones(len(X)), X])
    beta, *_ = np.linalg.lstsq(X1, y, rcond=None)
    y_hat = X1 @ beta
    sqr, sqt = np.sum((y_hat - y.mean()) ** 2), np.sum((y - y.mean()) ** 2)
    k, n = X.shape[1], len(y)
    r2 = sqr / sqt
    f = (sqr / k) / (np.sum((y - y_hat) ** 2) / (n - k - 1))
    p_f = stats.f.sf(f, k, n - k - 1)
    return beta, r2, f, p_f


def interpretar_modelo(r2, p_f):
    print(f"R² = {r2:.4f} -> o modelo explica {r2 * 100:.2f}% da variação da variável resposta.")
    print(f"Teste F: p-valor = {p_f:.4g} -> "
          + ("modelo significativo (p < 0,05)." if p_f < 0.05 else "modelo NÃO significativo (p >= 0,05)."))


def heatmap(corr, nome, tit):
    fig, ax = plt.subplots(figsize=(1.2 * len(corr) + 3, 1.2 * len(corr) + 2))
    im = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr)), corr.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(corr)), corr.columns)
    for i in range(len(corr)):
        for j in range(len(corr)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center")
    fig.colorbar(im)
    ax.set_title(tit)
    salvar(nome)


def q02(df):
    titulo("02) Distribuição Normal")
    x = df[VAR_NORMAL].dropna()
    media, dp, mediana = x.mean(), x.std(), x.median()
    print(f"{VAR_NORMAL}: média={media:.4f}, mediana={mediana:.4f}, desvio padrão={dp:.4f}")
    pa = stats.norm.cdf(media, media, dp)
    pb = stats.norm.sf(mediana, media, dp)
    print(f"a) P(X < média)   = {pa:.4f} -> {classificar_evento(pa)}")
    print(f"b) P(X > mediana) = {pb:.4f} -> {classificar_evento(pb)}")


def teste_z(x, n, alfa, cauda):
    """Média de referência = média populacional; sigma = desvio padrão populacional dos dados."""
    mu0, sigma = x.mean(), x.std(ddof=0)
    amostra = x.sample(n=n, random_state=SEMENTE)
    media_amostral = amostra.mean()
    z = (media_amostral - mu0) / (sigma / np.sqrt(n))
    if cauda == "esquerda":
        z_crit, p = stats.norm.ppf(alfa), stats.norm.cdf(z)
        h1, rejeita = f"μ < {mu0:.4f}", z < z_crit
    else:
        z_crit, p = stats.norm.ppf(1 - alfa), stats.norm.sf(z)
        h1, rejeita = f"μ > {mu0:.4f}", z > z_crit
    print(f"H0: μ = {mu0:.4f} | H1: {h1} | α={alfa:.0%} | n={n} | σ={sigma:.4f}")
    print(f"média amostral={media_amostral:.4f} | z={z:.4f} | z crítico={z_crit:.4f} | p-valor={p:.4f}")
    print("Decisão: " + ("rejeita H0." if rejeita else "não rejeita H0."))


def q03(df):
    titulo("03) Teste de hipótese para a média")
    x = df[VAR_NORMAL].dropna()
    print("a) média amostral MENOR que a populacional:")
    teste_z(x, n=20, alfa=0.06, cauda="esquerda")
    print("\nb) média amostral MAIOR que a populacional:")
    teste_z(x, n=25, alfa=0.09, cauda="direita")


def q04(df):
    titulo("04) Análise bivariada")
    d = df[[Q4_X, Q4_Y]].dropna()
    x, y = d[Q4_X].to_numpy(float), d[Q4_Y].to_numpy(float)
    beta, r2, f, p_f = regressao_ols(x.reshape(-1, 1), y)

    plt.scatter(x, y, alpha=0.6)
    plt.title(f"Dispersão: {Q4_Y} x {Q4_X}")
    plt.xlabel(Q4_X)
    plt.ylabel(Q4_Y)
    salvar("q04a_dispersao.png")
    print("a) Gráfico de dispersão: figuras/q04a_dispersao.png")

    r, p_r = stats.pearsonr(x, y)
    print(f"b) Covariância = {np.cov(x, y)[0, 1]:.4f} | Pearson r = {r:.4f} (p={p_r:.4g})")
    heatmap(d.corr(), "q04c_correlacao.png", "Correlação de Pearson")
    print("c) Gráfico de correlação: figuras/q04c_correlacao.png")

    xs = np.linspace(x.min(), x.max(), 100)
    plt.scatter(x, y, alpha=0.6)
    plt.plot(xs, beta[0] + beta[1] * xs, color="red")
    plt.title(f"Regressão linear simples: {Q4_Y} x {Q4_X}")
    plt.xlabel(Q4_X)
    plt.ylabel(Q4_Y)
    salvar("q04d_regressao.png")
    print(f"d) Equação: {Q4_Y} = {beta[0]:.4f} + {beta[1]:.4f} * {Q4_X}  (figuras/q04d_regressao.png)")
    print(f"e) R²={r2:.4f} | F={f:.4f}")
    interpretar_modelo(r2, p_f)
    print(f"f) Previsão para {Q4_X}={Q4_X_PREVISAO}: {Q4_Y} = {beta[0] + beta[1] * Q4_X_PREVISAO:.4f}")


def q05(df):
    titulo("05) Análise multivariada - Regressão linear múltipla")
    cols = Q5_X + [Q5_Y]
    d = df[cols].dropna()
    pd.plotting.scatter_matrix(d, figsize=(10, 10), diagonal="hist")
    plt.suptitle("Matriz de dispersão")
    salvar("q05a_dispersao.png")
    print("a) Gráfico de dispersão: figuras/q05a_dispersao.png")
    print("b) Matriz de covariância:\n", d.cov().round(4))
    print("   Matriz de correlação de Pearson:\n", d.corr().round(4))
    heatmap(d.corr(), "q05c_correlacao.png", "Correlação de Pearson")
    print("c) Gráfico de correlação: figuras/q05c_correlacao.png")
    beta, r2, f, p_f = regressao_ols(d[Q5_X].to_numpy(float), d[Q5_Y].to_numpy(float))
    termos = " ".join(f"{b:+.4f} * {c}" for b, c in zip(beta[1:], Q5_X))
    print(f"d) Equação: {Q5_Y} = {beta[0]:.4f} {termos}")
    print(f"e) R²={r2:.4f} | F={f:.4f}")
    interpretar_modelo(r2, p_f)
    prev = beta[0] + sum(b * Q5_NOVO[c] for b, c in zip(beta[1:], Q5_X))
    print(f"f) Previsão para {Q5_NOVO}: {Q5_Y} = {prev:.4f}")


def q06(df):
    titulo("06) Análise multivariada - Regressão logística binária")
    d = df[Q6_X + [Q6_ALVO]].dropna()
    X, y = d[Q6_X].to_numpy(float), d[Q6_ALVO].astype(int).to_numpy()
    modelo = LogisticRegression(penalty=None, max_iter=1000).fit(X, y)
    termos = " ".join(f"{b:+.4f} * {c}" for b, c in zip(modelo.coef_[0], Q6_X))
    print(f"a) logit(p) = ln(p / (1 - p)) = {modelo.intercept_[0]:.4f} {termos}")
    print(f"   p = 1 / (1 + e^-({modelo.intercept_[0]:.4f} {termos}))")
    y_pred = modelo.predict(X)
    print("b) Matriz de confusão (linhas = real 0/1, colunas = previsto 0/1):")
    print(confusion_matrix(y, y_pred))
    print(f"   Acurácia = {accuracy_score(y, y_pred):.4f}")
    novo = np.array([[Q6_NOVO[c] for c in Q6_X]])
    p = modelo.predict_proba(novo)[0, 1]
    print(f"c) Classificação para {Q6_NOVO}: P(classe 1) = {p:.4f} -> classe {int(p >= 0.5)}")


if __name__ == "__main__":
    df = carregar(sys.argv[1] if len(sys.argv) > 1 else ARQUIVO)
    print(f"Base: {df.shape[0]} registros x {df.shape[1]} colunas")
    print(df.describe().T)
    q02(df)
    q03(df)
    q04(df)
    q05(df)
    q06(df)
