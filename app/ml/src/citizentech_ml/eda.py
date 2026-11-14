"""Módulo de Análise Exploratória de Dados (EDA) exclusiva do conjunto de treino."""

from __future__ import annotations

import argparse
import hashlib
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from citizentech_ml.features.datas import diferenca_meses
from citizentech_ml.features.densidade import calcular_densidade_treino
from citizentech_ml.features.extracao import COLUNAS_FEATURES
from citizentech_ml.painel import carregar_pre_agregado

RODAPE_TABELA = (
    "*Fonte: Novo Caged, MTE/PDET | População: admissões formais, "
    "ocupações CBO do destino | Natureza: observado*"
)


def formatar_pt_br(
    valor: float | int | None,
    casas: int = 0,
    percentual: bool = False,
) -> str:
    """Formata números no padrão pt-BR (milhar com ponto, decimal com vírgula)."""
    if valor is None:
        return "N/D"
    if isinstance(valor, float) and (np.isnan(valor) or not np.isfinite(valor)):
        return "N/D"

    if percentual:
        texto = f"{float(valor):,.{casas}f}"
        texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{texto}%"

    if casas == 0:
        return f"{int(round(float(valor))):,}".replace(",", ".")

    texto = f"{float(valor):,.{casas}f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return texto


def formatar_ufs_invalidas(ufs_dict: dict[str, int] | None) -> str:
    """Formata contagem de UFs inválidas de forma legível em pt-BR."""
    if not ufs_dict:
        return "Nenhuma"
    itens = [f"UF {uf}: {formatar_pt_br(qtd, casas=0)}" for uf, qtd in sorted(ufs_dict.items())]
    return ", ".join(itens)


def _secao_qualidade(
    df_treino: pd.DataFrame,
    relatorio_carga: dict[str, Any] | None,
    linhas_painel_ignoradas: int,
) -> tuple[str, str]:
    """Gera tabela e texto da Seção 1: Qualidade e cobertura."""
    linhas_lidas = relatorio_carga.get("linhas_lidas", 0) if relatorio_carga else 0
    ufs_inv = relatorio_carga.get("linhas_uf_invalida", {}) if relatorio_carga else {}
    linhas_apos = relatorio_carga.get("linhas_apos_limite", 0) if relatorio_carga else 0

    total_registros_treino = len(df_treino)
    meses_cobertos = sorted(df_treino["competencia"].unique()) if not df_treino.empty else []
    alvo_ausente = int(df_treino["alvo"].isna().sum()) if "alvo" in df_treino.columns else 0

    prop_zeros = 0.0
    if "admissoes" in df_treino.columns and total_registros_treino > 0:
        prop_zeros = float((df_treino["admissoes"] == 0).sum() / total_registros_treino) * 100.0

    # Item 13: Análise de cobertura completa de features e ausentes por feature
    cols_feat_presentes = [c for c in COLUNAS_FEATURES if c in df_treino.columns]
    if cols_feat_presentes and not df_treino.empty:
        mascara_todas = df_treino[cols_feat_presentes].notna().all(axis=1)
        origens_todas = sorted(df_treino.loc[mascara_todas, "competencia"].unique())
        n_origens_todas = len(origens_todas)
        faixa_todas = f"{origens_todas[0]} a {origens_todas[-1]}" if origens_todas else "Nenhuma"
    else:
        n_origens_todas = 0
        faixa_todas = "N/D"

    linhas_indicadores = [
        "| Indicador | Valor |",
        "|---|---|",
        f"| Linhas brutas lidas nos arquivos Parquet | {formatar_pt_br(linhas_lidas)} |",
        f"| Linhas descartadas com código de UF inválido | {formatar_ufs_invalidas(ufs_inv)} |",
        f"| Linhas descartadas por competência posterior | {formatar_pt_br(linhas_apos)} |",
        f"| Linhas do painel no treino (t ≤ 202409) | {formatar_pt_br(total_registros_treino)} |",
        f"| Linhas posteriores ignoradas na montagem da EDA | "
        f"{formatar_pt_br(linhas_painel_ignoradas)} |",
        f"| Total de origens mensais de treino analisadas | "
        f"{formatar_pt_br(len(meses_cobertos))} |",
        f"| Origens de treino com todas as features | "
        f"{formatar_pt_br(n_origens_todas)} ({faixa_todas}) |",
        f"| Registros com alvo consolidado ausente | {formatar_pt_br(alvo_ausente)} |",
        f"| Proporção de células com zero nas admissões | "
        f"{formatar_pt_br(prop_zeros, casas=2, percentual=True)} |",
    ]

    tabela = (
        "\n".join(linhas_indicadores)
        + f"\n\n{RODAPE_TABELA} | Unidade: contagens e percentuais | Período: 202001–202409\n"
    )

    if cols_feat_presentes and not df_treino.empty:
        tabela += "\n### Ausência de Dados por Coluna de Feature (Treino)\n\n"
        tabela += (
            "| Coluna de Feature | Linhas Ausentes | Proporção Ausente (%) |\n|---|---|---|\n"
        )
        for col_f in cols_feat_presentes:
            qtd_aus = int(df_treino[col_f].isna().sum())
            pct_aus = (
                (qtd_aus / total_registros_treino * 100.0) if total_registros_treino > 0 else 0.0
            )
            tabela += (
                f"| {col_f} | {formatar_pt_br(qtd_aus)} | "
                f"{formatar_pt_br(pct_aus, casas=2, percentual=True)} |\n"
            )
        tabela += f"\n{RODAPE_TABELA} | Unidade: contagens e percentuais | Período: 202001–202409\n"

    prop_z_fmt = formatar_pt_br(prop_zeros, casas=2, percentual=True)
    tot_reg_fmt = formatar_pt_br(total_registros_treino)
    n_orig_fmt = formatar_pt_br(n_origens_todas)
    frase = (
        f"No período de treino estrito (202001 a 202409), foram analisadas {len(meses_cobertos)} "
        f"origens temporais com {tot_reg_fmt} registros, sendo que {n_orig_fmt} origens possuem "
        f"todas as features presentes ({faixa_todas}) e a taxa global de zeros foi de {prop_z_fmt}."
    )
    return tabela, frase


def _secao_densidade(df_treino: pd.DataFrame) -> tuple[str, str]:
    """Gera tabela e texto da Seção 2: Densidade (D04a) com cobertura efetiva."""
    if df_treino.empty or "alvo" not in df_treino.columns:
        return "Nenhum dado disponível para cálculo de densidade.", "Dados ausentes."

    rel_densidade = calcular_densidade_treino(
        df_treino,
        limite_minimo=10.0,
        limite_competencia_treino="202409",
    )

    destinos = sorted(rel_densidade["destino"].unique())
    cabecalho_dens = (
        "| Destino | UFs Elegíveis (Média ≥ 10) | "
        "Cobertura de Admissões (%) | UFs Excluídas (< 10 ou sem dados) |"
    )
    linhas_md = [
        cabecalho_dens,
        "|---|---|---|---|",
    ]

    total_elegiveis = 0
    total_series = len(rel_densidade)
    total_adm_global = (
        float(df_treino["admissoes"].sum()) if "admissoes" in df_treino.columns else 0.0
    )
    total_adm_eleg_global = 0.0

    for d in destinos:
        sub_rel = rel_densidade[rel_densidade["destino"] == d]
        elegiveis = sub_rel[sub_rel["elegivel"]]
        excluidas = sub_rel[~sub_rel["elegivel"]]

        total_elegiveis += len(elegiveis)
        ufs_eleg_set = set(elegiveis["uf"].unique())

        sub_df = df_treino[df_treino["destino"] == d]
        tot_d = float(sub_df["admissoes"].sum()) if "admissoes" in sub_df.columns else 0.0
        tot_d_eleg = (
            float(sub_df[sub_df["uf"].isin(ufs_eleg_set)]["admissoes"].sum())
            if "admissoes" in sub_df.columns
            else 0.0
        )
        total_adm_eleg_global += tot_d_eleg

        cob_pct = (tot_d_eleg / tot_d * 100.0) if tot_d > 0.0 else 100.0

        if not excluidas.empty:
            ufs_exc_str = ", ".join(sorted(excluidas["uf"].unique()))
        else:
            ufs_exc_str = "Nenhuma"

        cob_str = formatar_pt_br(cob_pct, casas=2, percentual=True)
        linhas_md.append(f"| {d} | {len(elegiveis)} / 27 | {cob_str} | {ufs_exc_str} |")

    tabela = (
        "\n".join(linhas_md)
        + f"\n\n{RODAPE_TABELA} | Unidade: UFs e percentual | Período: 202001–202409\n"
    )
    cob_global_pct = (
        (total_adm_eleg_global / total_adm_global * 100.0) if total_adm_global > 0.0 else 100.0
    )
    cob_glob_str = formatar_pt_br(cob_global_pct, casas=2, percentual=True)
    frase = (
        f"Do total de {total_series} séries destino × UF analisadas no treino, {total_elegiveis} "
        f"atenderam ao critério de densidade mínima de 10 admissões/tri (D04a) e "
        f"{total_series - total_elegiveis} foram excluídas, atingindo cobertura de {cob_glob_str} "
        "das admissões observadas no treino."
    )
    return tabela, frase


def _secao_nivel_tendencia(
    df_treino: pd.DataFrame,
    df_pre_treino: pd.DataFrame,
    dir_saida: Path,
) -> tuple[str, str]:
    """Gera gráfico com subplots e tabela da Seção 3: Nível e tendência."""
    png_path = dir_saida / "nivel_tendencia.png"
    if df_treino.empty or "competencia" not in df_treino.columns:
        return "Dados insuficientes.", "Dados ausentes."

    agrupado = df_treino.groupby(["competencia", "destino"], as_index=False)[
        ["admissoes", "admissoes_total"]
    ].sum()

    meses = sorted(agrupado["competencia"].unique())
    destinos = sorted(agrupado["destino"].unique())

    # Item 11: Dois subplots no mesmo PNG (Série Principal e Série Total)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

    for d in destinos:
        sub = agrupado[agrupado["destino"] == d].set_index("competencia")
        valores_sup = [sub.loc[m, "admissoes"] if m in sub.index else 0.0 for m in meses]
        valores_tot = [sub.loc[m, "admissoes_total"] if m in sub.index else 0.0 for m in meses]
        ax1.plot(range(len(meses)), valores_sup, label=d)
        ax2.plot(range(len(meses)), valores_tot, label=d)

    ax1.set_title("Série Principal: Admissões com Nível Superior Completo ou Mais (Treino)")
    ax1.set_ylabel("Admissões declaradas até o próprio mês")
    ax1.grid(True, linestyle="--", alpha=0.6)
    ax1.legend(bbox_to_anchor=(1.02, 1), loc="upper left")

    ax2.set_title("Série de Contexto: Admissões Totais em Todos os Graus de Instrução (Treino)")
    ax2.set_xlabel("Origens Temporais")
    ax2.set_ylabel("Admissões declaradas até o próprio mês")
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend(bbox_to_anchor=(1.02, 1), loc="upper left")

    passo = max(1, len(meses) // 8)
    ax2.set_xticks(range(0, len(meses), passo))
    ax2.set_xticklabels([meses[i] for i in range(0, len(meses), passo)], rotation=45)

    plt.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)

    # Item 8: Visão consolidada (MOV+FOR-EXC) comparada com a visão as-of
    df_pre_limite = df_pre_treino[df_pre_treino["competencia_mov"] <= "202409"].copy()

    cabecalho_nivel = (
        "| Destino | Consolidado (Superior) | Média Mensal (Superior) | "
        "Dif. vs As-Of (Superior) | Consolidado (Total) | Média Mensal (Total) | "
        "Dif. vs As-Of (Total) |"
    )
    linhas_tab = [
        cabecalho_nivel,
        "|---|---|---|---|---|---|---|",
    ]

    contagens = df_treino.groupby("destino")["competencia"].nunique().to_dict()
    maior_dest = ""
    maior_vol_cons = -1.0

    for d in destinos:
        n_m = contagens.get(d, 1)

        # Consolidado superior
        sub_pre_sup = df_pre_limite[
            (df_pre_limite["destino"] == d) & (df_pre_limite["superior"])
        ]
        tot_cons_sup = float(sub_pre_sup["delta_adm"].sum()) if not sub_pre_sup.empty else 0.0
        med_cons_sup = tot_cons_sup / n_m if n_m > 0 else 0.0

        # As-of superior
        tot_asof_sup = float(df_treino[df_treino["destino"] == d]["admissoes"].sum())
        dif_sup = (
            ((tot_cons_sup - tot_asof_sup) / tot_asof_sup * 100.0) if tot_asof_sup > 0 else 0.0
        )

        # Consolidado total
        sub_pre_tot = df_pre_limite[df_pre_limite["destino"] == d]
        tot_cons_tot = float(sub_pre_tot["delta_adm"].sum()) if not sub_pre_tot.empty else 0.0
        med_cons_tot = tot_cons_tot / n_m if n_m > 0 else 0.0

        # As-of total
        tot_asof_tot = float(df_treino[df_treino["destino"] == d]["admissoes_total"].sum())
        dif_tot = (
            ((tot_cons_tot - tot_asof_tot) / tot_asof_tot * 100.0) if tot_asof_tot > 0 else 0.0
        )

        if tot_cons_sup > maior_vol_cons:
            maior_vol_cons = tot_cons_sup
            maior_dest = d

        sup_cons_fmt = formatar_pt_br(tot_cons_sup)
        sup_med_fmt = formatar_pt_br(med_cons_sup, casas=1)
        sup_dif_fmt = formatar_pt_br(dif_sup, casas=2, percentual=True)
        tot_cons_fmt = formatar_pt_br(tot_cons_tot)
        tot_med_fmt = formatar_pt_br(med_cons_tot, casas=1)
        tot_dif_fmt = formatar_pt_br(dif_tot, casas=2, percentual=True)

        linhas_tab.append(
            f"| {d} | {sup_cons_fmt} | {sup_med_fmt} | {sup_dif_fmt} | "
            f"{tot_cons_fmt} | {tot_med_fmt} | {tot_dif_fmt} |"
        )

    tabela = (
        "![Nível e Tendência](nivel_tendencia.png)\n\n"
        + "\n".join(linhas_tab)
        + f"\n\n{RODAPE_TABELA} | Unidade: admissões formais consolidadas e percentual "
        "| Período: 202001–202409\n"
    )
    frase = (
        f"O destino com maior volume consolidado com nível superior no treino "
        f"foi '{maior_dest}', totalizando {formatar_pt_br(maior_vol_cons)} admissões observadas."
    )
    return tabela, frase


def _secao_sazonalidade(df_treino: pd.DataFrame, dir_saida: Path) -> tuple[str, str]:
    """Gera gráfico e tabela da Seção 4: Índice sazonal calculado em anos completos."""
    png_path = dir_saida / "sazonalidade.png"
    if df_treino.empty or "competencia" not in df_treino.columns:
        return "Dados insuficientes.", "Dados ausentes."

    df_tr = df_treino.copy()
    df_tr["ano"] = df_tr["competencia"].astype(str).str[:4]
    df_tr["mes_num"] = df_tr["competencia"].astype(str).str[4:].astype(int)

    # Item 10: Selecionar apenas anos completos presentes no treino (12 meses)
    anos_completos = []
    for a in sorted(df_tr["ano"].unique()):
        if df_tr[df_tr["ano"] == a]["mes_num"].nunique() == 12:
            anos_completos.append(a)

    if not anos_completos:
        anos_completos = sorted(df_tr["ano"].unique())

    df_comp = df_tr[df_tr["ano"].isin(anos_completos)].copy()
    destinos = sorted(df_comp["destino"].unique())

    # Cálculo do índice sazonal (1.00 = média anual)
    indices_por_destino: dict[str, dict[int, float]] = {}
    for d in destinos:
        sub_d = df_comp[df_comp["destino"] == d]
        indices_mes: dict[int, list[float]] = {m: [] for m in range(1, 13)}
        for a in anos_completos:
            sub_da = sub_d[sub_d["ano"] == a]
            tot_ano = float(sub_da["admissoes"].sum())
            med_ano = tot_ano / 12.0 if tot_ano > 0 else 0.0
            for m in range(1, 13):
                adm_m = float(sub_da[sub_da["mes_num"] == m]["admissoes"].sum())
                idx = (adm_m / med_ano) if med_ano > 0 else 1.0
                indices_mes[m].append(idx)
        indices_por_destino[d] = {
            m: float(np.mean(indices_mes[m])) if indices_mes[m] else 1.0 for m in range(1, 13)
        }

    # Índice sazonal do Agregado
    indices_agg_mes: dict[int, list[float]] = {m: [] for m in range(1, 13)}
    for a in anos_completos:
        sub_a = df_comp[df_comp["ano"] == a]
        tot_ano_agg = float(sub_a["admissoes"].sum())
        med_ano_agg = tot_ano_agg / 12.0 if tot_ano_agg > 0 else 0.0
        for m in range(1, 13):
            adm_m_agg = float(sub_a[sub_a["mes_num"] == m]["admissoes"].sum())
            idx_agg = (adm_m_agg / med_ano_agg) if med_ano_agg > 0 else 1.0
            indices_agg_mes[m].append(idx_agg)

    indices_agregado = {
        m: float(np.mean(indices_agg_mes[m])) if indices_agg_mes[m] else 1.0 for m in range(1, 13)
    }

    fig, ax = plt.subplots(figsize=(11, 5))
    for d in destinos:
        valores = [indices_por_destino[d][m] for m in range(1, 13)]
        ax.plot(range(1, 13), valores, marker="o", label=d, alpha=0.7)

    ax.plot(
        range(1, 13),
        [indices_agregado[m] for m in range(1, 13)],
        color="black",
        linewidth=2.5,
        linestyle="--",
        label="Agregado (Média)",
    )
    ax.axhline(1.0, color="gray", linestyle=":", alpha=0.8, label="Média do ano (1,00)")

    ax.set_title("Índice Sazonal Médio de Admissões por Mês do Ano (Anos Completos)")
    ax.set_xlabel("Mês do Ano (1 a 12)")
    ax.set_ylabel("Índice Sazonal (1,00 = Média do Ano)")
    ax.set_xticks(range(1, 13))
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)

    linhas_tab = [
        "| Destino | Jan | Fev | Mar | Abr | Mai | Jun | Jul | Ago | Set | Out | Nov | Dez |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for d in destinos:
        cols = [formatar_pt_br(indices_por_destino[d][m], casas=2) for m in range(1, 13)]
        linhas_tab.append(f"| {d} | " + " | ".join(cols) + " |")

    cols_agg = [formatar_pt_br(indices_agregado[m], casas=2) for m in range(1, 13)]
    linhas_tab.append("| **Agregado** | " + " | ".join(cols_agg) + " |")

    mes_maior = max(indices_agregado, key=lambda m: indices_agregado[m])
    mes_menor = min(indices_agregado, key=lambda m: indices_agregado[m])
    idx_max = indices_agregado[mes_maior]
    idx_min = indices_agregado[mes_menor]

    anos_str = ", ".join(anos_completos)
    idx_max_str = formatar_pt_br(idx_max, casas=2)
    idx_min_str = formatar_pt_br(idx_min, casas=2)
    tabela = (
        "![Índice Sazonal](sazonalidade.png)\n\n"
        + "\n".join(linhas_tab)
        + f"\n\n{RODAPE_TABELA} | Unidade: índice sazonal (1,00 = média anual) | "
        f"Anos completos considerados: {anos_str}\n"
    )
    frase = (
        f"Com base exclusivamente nos anos completos do treino ({anos_str}), o padrão sazonal do "
        f"agregado atingiu o maior índice no mês {mes_maior} ({idx_max_str}) "
        f"e o menor índice no mês {mes_menor} ({idx_min_str})."
    )
    return tabela, frase


def _secao_2020_comparativo(
    df_treino: pd.DataFrame, df_pre_treino: pd.DataFrame
) -> tuple[str, str]:
    """Gera tabelas e texto da Seção 5: 2020 x demais anos para ambas as séries."""
    if df_treino.empty:
        return "Dados insuficientes.", "Dados ausentes."

    df_tr = df_treino.copy()
    df_tr["ano"] = df_tr["competencia"].astype(str).str[:4]
    anos = sorted(df_tr["ano"].unique())

    df_pre = df_pre_treino[df_pre_treino["competencia_mov"] <= "202409"].copy()
    df_pre["ano_mov"] = df_pre["competencia_mov"].astype(str).str[:4]

    tem_tipo = "arquivo_tipo" in df_pre.columns

    def _resumir_serie(superior_filtro: bool | None) -> list[str]:
        cabecalho_2020 = (
            "| Ano | Meses no Treino | Admissões Consolidadas | Média Mensal | "
            "CV Mensal | Dif. vs As-Of (%) | Fração FOR (%) | Declaradas após o Mês (%) |"
        )
        linhas = [
            cabecalho_2020,
            "|---|---|---|---|---|---|---|---|",
        ]
        for a in anos:
            sub_tr = df_tr[df_tr["ano"] == a]
            col_asof = "admissoes" if superior_filtro is True else "admissoes_total"
            asof_ano = float(sub_tr[col_asof].sum())

            sub_pre = df_pre[df_pre["ano_mov"] == a]
            if superior_filtro is True:
                sub_pre = sub_pre[sub_pre["superior"]]
            elif superior_filtro is False:
                sub_pre = sub_pre[~sub_pre["superior"]]

            meses_no_treino = sub_tr["competencia"].nunique()

            mensal_cons = sub_pre.groupby("competencia_mov")["delta_adm"].sum()
            tot_cons = float(mensal_cons.sum())
            med_mensal = tot_cons / meses_no_treino if meses_no_treino > 0 else 0.0

            cv = (
                (float(mensal_cons.std(ddof=1)) / float(mensal_cons.mean()))
                if len(mensal_cons) > 1 and float(mensal_cons.mean()) > 0
                else 0.0
            )

            dif_asof = ((tot_cons - asof_ano) / asof_ano * 100.0) if asof_ano > 0 else 0.0

            if tem_tipo:
                sub_mov = sub_pre[sub_pre["arquivo_tipo"] == "MOV"]
                sub_for = sub_pre[sub_pre["arquivo_tipo"] == "FOR"]
                adm_mov = float(sub_mov.loc[sub_mov["delta_adm"] > 0, "delta_adm"].sum())
                adm_for = float(sub_for.loc[sub_for["delta_adm"] > 0, "delta_adm"].sum())
                tot_bruto = adm_mov + adm_for
                frac_for = (adm_for / tot_bruto * 100.0) if tot_bruto > 0 else 0.0
            else:
                adm_pos = float(sub_pre.loc[sub_pre["delta_adm"] > 0, "delta_adm"].sum())
                sub_for = sub_pre[sub_pre["competencia_disp"] > sub_pre["competencia_mov"]]
                adm_for = float(sub_for.loc[sub_for["delta_adm"] > 0, "delta_adm"].sum())
                tot_bruto = adm_pos
                frac_for = (adm_for / adm_pos * 100.0) if adm_pos > 0 else 0.0

            sub_pos = sub_pre[sub_pre["delta_adm"] > 0]
            sub_pos_tardia = sub_pos[sub_pos["competencia_disp"] > sub_pos["competencia_mov"]]
            adm_tardia = float(sub_pos_tardia["delta_adm"].sum())
            frac_tardia = (adm_tardia / tot_bruto * 100.0) if tot_bruto > 0 else 0.0

            c_tot = formatar_pt_br(tot_cons)
            c_med = formatar_pt_br(med_mensal, casas=1)
            c_cv = formatar_pt_br(cv, casas=3)
            c_dif = formatar_pt_br(dif_asof, casas=2, percentual=True)
            c_for = formatar_pt_br(frac_for, casas=2, percentual=True)
            c_tar = formatar_pt_br(frac_tardia, casas=2, percentual=True)

            linhas.append(
                f"| {a} | {meses_no_treino} | {c_tot} | {c_med} | {c_cv} | "
                f"{c_dif} | {c_for} | {c_tar} |"
            )
        return linhas

    tabela_sup = _resumir_serie(superior_filtro=True)
    tabela_tot = _resumir_serie(superior_filtro=None)

    sub_pre_2020 = df_pre[(df_pre["ano_mov"] == "2020") & (df_pre["superior"])]
    m_cons_2020 = sub_pre_2020.groupby("competencia_mov")["delta_adm"].sum()
    cv_2020 = (
        (float(m_cons_2020.std(ddof=1)) / float(m_cons_2020.mean()))
        if len(m_cons_2020) > 1 and float(m_cons_2020.mean()) > 0
        else 0.0
    )
    med_2020 = float(m_cons_2020.mean()) if not m_cons_2020.empty else 0.0
    meses_2020 = int(m_cons_2020.shape[0])

    rodape_comp = (
        f"{RODAPE_TABELA} | Unidade: contagens, razões e percentuais | Período: 202001–202409\n"
    )
    tabela = (
        "### Série Principal: Nível Superior Completo ou Mais\n\n"
        + "\n".join(tabela_sup)
        + f"\n\n{rodape_comp}\n"
        + "### Série de Contexto: Total de Ocupações (Todos os Graus de Instrução)\n\n"
        + "\n".join(tabela_tot)
        + f"\n\n{rodape_comp}"
    )

    cv_2020_fmt = formatar_pt_br(cv_2020, casas=3)
    med_2020_fmt = formatar_pt_br(med_2020, casas=1)
    if meses_2020 == 0:
        frase = "Não há movimentações de 2020 no treino recebido para a série principal."
    else:
        frase = (
            f"O ano de 2020 apresentou coeficiente de variação mensal de {cv_2020_fmt} "
            f"e média mensal consolidada de {med_2020_fmt} admissões na série principal "
            f"({meses_2020} meses com movimentação no treino)."
        )
    return tabela, frase


def _secao_defasagem(df_pre_treino: pd.DataFrame) -> tuple[str, str]:
    """Gera tabelas e texto da Seção 6: Defasagem de declaração (R02) por série."""
    if df_pre_treino.empty:
        return "Dados insuficientes.", "Dados ausentes."

    df_pre = df_pre_treino.copy()
    df_pre["ano_mov"] = df_pre["competencia_mov"].astype(str).str[:4]
    anos = sorted(df_pre["ano_mov"].unique())

    tem_tipo = "arquivo_tipo" in df_pre.columns

    def _resumir_defasagem_serie(
        superior_filtro: bool | None,
    ) -> tuple[list[str], list[float], list[float], list[float]]:
        cabecalho_def = (
            "| Ano Movimentação | Até 0m (%) | Até 1m (%) | Até 2m (%) | "
            "Até 3m (%) | Até 6m (%) | Até 12m (%) | Fração Exclusões (%) |"
        )
        linhas = [
            cabecalho_def,
            "|---|---|---|---|---|---|---|---|",
        ]
        c0_list: list[float] = []
        c3_list: list[float] = []
        exc_list: list[float] = []

        for a in anos:
            sub = df_pre[df_pre["ano_mov"] == a].copy()
            if superior_filtro is True:
                sub = sub[sub["superior"]]
            elif superior_filtro is False:
                sub = sub[~sub["superior"]]

            if sub.empty:
                linhas.append(f"| {a} | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% |")
                continue

            sub["defasagem"] = [
                diferenca_meses(str(m), str(d))
                for m, d in zip(sub["competencia_mov"], sub["competencia_disp"], strict=False)
            ]

            if tem_tipo:
                sub_mov_for = sub[sub["arquivo_tipo"].isin(["MOV", "FOR"])]
                sub_pos = sub_mov_for[sub_mov_for["delta_adm"] > 0]
                tot_bruto = float(sub_pos["delta_adm"].sum())

                sub_exc = sub[sub["arquivo_tipo"] == "EXC"]
                tot_exc = abs(float(sub_exc["delta_adm"].sum()))
            else:
                sub_pos = sub[sub["delta_adm"] > 0]
                tot_bruto = float(sub_pos["delta_adm"].sum())
                sub_neg = sub[sub["delta_adm"] < 0]
                tot_exc = abs(float(sub_neg["delta_adm"].sum()))

            if tot_bruto == 0.0:
                linhas.append(f"| {a} | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% |")
                continue

            c0 = (
                float(sub_pos.loc[sub_pos["defasagem"] <= 0, "delta_adm"].sum()) / tot_bruto * 100.0
            )
            c1 = (
                float(sub_pos.loc[sub_pos["defasagem"] <= 1, "delta_adm"].sum()) / tot_bruto * 100.0
            )
            c2 = (
                float(sub_pos.loc[sub_pos["defasagem"] <= 2, "delta_adm"].sum()) / tot_bruto * 100.0
            )
            c3 = (
                float(sub_pos.loc[sub_pos["defasagem"] <= 3, "delta_adm"].sum()) / tot_bruto * 100.0
            )
            c6 = (
                float(sub_pos.loc[sub_pos["defasagem"] <= 6, "delta_adm"].sum()) / tot_bruto * 100.0
            )
            c12 = (
                float(sub_pos.loc[sub_pos["defasagem"] <= 12, "delta_adm"].sum())
                / tot_bruto
                * 100.0
            )
            f_exc = tot_exc / tot_bruto * 100.0

            c0_list.append(c0)
            c3_list.append(c3)
            exc_list.append(f_exc)

            fmt_0 = formatar_pt_br(c0, casas=1, percentual=True)
            fmt_1 = formatar_pt_br(c1, casas=1, percentual=True)
            fmt_2 = formatar_pt_br(c2, casas=1, percentual=True)
            fmt_3 = formatar_pt_br(c3, casas=1, percentual=True)
            fmt_6 = formatar_pt_br(c6, casas=1, percentual=True)
            fmt_12 = formatar_pt_br(c12, casas=1, percentual=True)
            fmt_exc = formatar_pt_br(f_exc, casas=2, percentual=True)

            linhas.append(
                f"| {a} | {fmt_0} | {fmt_1} | {fmt_2} | {fmt_3} | "
                f"{fmt_6} | {fmt_12} | {fmt_exc} |"
            )

        return linhas, c0_list, c3_list, exc_list

    linhas_sup, c0_sup, c3_sup, exc_sup = _resumir_defasagem_serie(superior_filtro=True)
    linhas_tot, _, _, _ = _resumir_defasagem_serie(superior_filtro=None)

    med_0_sup = float(np.mean(c0_sup)) if c0_sup else 0.0
    med_3_sup = float(np.mean(c3_sup)) if c3_sup else 0.0
    med_exc_sup = float(np.mean(exc_sup)) if exc_sup else 0.0

    rodape_def = (
        f"{RODAPE_TABELA} | Unidade: percentual acumulado (%) | Período: 202001–202412\n"
    )
    tabela = (
        "### Série Principal: Nível Superior Completo ou Mais\n\n"
        + "\n".join(linhas_sup)
        + f"\n\n{rodape_def}\n"
        + "### Série de Contexto: Total de Ocupações (Todos os Graus de Instrução)\n\n"
        + "\n".join(linhas_tot)
        + f"\n\n{rodape_def}"
    )

    med_0_fmt = formatar_pt_br(med_0_sup, casas=1, percentual=True)
    med_3_fmt = formatar_pt_br(med_3_sup, casas=1, percentual=True)
    med_exc_fmt = formatar_pt_br(med_exc_sup, casas=2, percentual=True)
    frase = (
        f"Na série principal, em média, {med_0_fmt} das admissões foram declaradas "
        f"no próprio mês (até 0 meses), atingindo {med_3_fmt} em até 3 meses, "
        f"com fração média de exclusões de {med_exc_fmt}."
    )
    return tabela, frase


def _secao_distribuicao_alvo(df_treino: pd.DataFrame) -> tuple[str, str]:
    """Gera tabela e texto da Seção 7: Distribuição do alvo com formatação pt-BR."""
    if df_treino.empty or "alvo" not in df_treino.columns:
        return "Dados insuficientes.", "Dados ausentes."

    destinos = sorted(df_treino["destino"].unique())
    linhas_tab = [
        "| Destino | N | Zeros (%) | Média | Desvio | Q10 | Q25 | Mediana (Q50) | Q75 | Q90 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]

    total_validos = 0
    total_zeros = 0

    for d in destinos:
        sub = df_treino[df_treino["destino"] == d]["alvo"].dropna().to_numpy(dtype=float)
        n = len(sub)
        if n == 0:
            linhas_tab.append(f"| {d} | 0 | 0,0% | 0,0 | 0,0 | 0,0 | 0,0 | 0,0 | 0,0 | 0,0 |")
            continue

        zeros = int((sub == 0.0).sum())
        total_validos += n
        total_zeros += zeros

        p_zeros = (zeros / n) * 100.0
        media = float(np.mean(sub))
        desvio = float(np.std(sub, ddof=1)) if n > 1 else 0.0
        q10, q25, q50, q75, q90 = np.quantile(sub, [0.10, 0.25, 0.50, 0.75, 0.90])

        p_z = formatar_pt_br(p_zeros, casas=1, percentual=True)
        m_val = formatar_pt_br(media, casas=1)
        s_val = formatar_pt_br(desvio, casas=1)
        q10_s = formatar_pt_br(q10, casas=1)
        q25_s = formatar_pt_br(q25, casas=1)
        q50_s = formatar_pt_br(q50, casas=1)
        q75_s = formatar_pt_br(q75, casas=1)
        q90_s = formatar_pt_br(q90, casas=1)

        linhas_tab.append(
            f"| {d} | {formatar_pt_br(n)} | {p_z} | {m_val} | {s_val} | "
            f"{q10_s} | {q25_s} | {q50_s} | {q75_s} | {q90_s} |"
        )

    prop_zeros_global = (total_zeros / total_validos * 100.0) if total_validos > 0 else 0.0
    tabela = (
        "\n".join(linhas_tab)
        + f"\n\n{RODAPE_TABELA} | Unidade: admissões formais observadas no grupo e "
        "território (soma dos 3 meses seguintes) | Período: 202001–202409\n"
    )
    z_glob_fmt = formatar_pt_br(prop_zeros_global, casas=2, percentual=True)
    frase = (
        f"A distribuição do alvo trimestral consolidado apresenta proporção global de zeros de "
        f"{z_glob_fmt} para o conjunto de séries de treino avaliadas."
    )
    return tabela, frase


def gerar_eda_treino(
    painel: pd.DataFrame,
    pre_agregado: pd.DataFrame,
    dir_saida: str | Path,
    relatorio_carga: dict[str, Any] | None = None,
    sha256_painel: str | None = None,
) -> Path:
    """Gera relatório de EDA exclusivo do treino em Markdown e gráficos PNG."""
    dir_s = Path(dir_saida)
    dir_s.mkdir(parents=True, exist_ok=True)

    # 1. Isolamento estrito do treino (t <= 202409)
    if "particao" in painel.columns:
        df_treino = painel[painel["particao"] == "treino"].copy()
    else:
        df_treino = painel[painel["competencia"] <= "202409"].copy()
    linhas_painel_ignoradas = len(painel) - len(df_treino)

    # Para defasagem, somente movimentações até 202412
    mascara_pre = pre_agregado["competencia_mov"] <= "202412"
    df_pre_treino = pre_agregado[mascara_pre].copy()
    linhas_pre_ignoradas = int((~mascara_pre).sum())

    # Construção das 7 seções
    tab1, frase1 = _secao_qualidade(df_treino, relatorio_carga, linhas_painel_ignoradas)
    tab2, frase2 = _secao_densidade(df_treino)
    tab3, frase3 = _secao_nivel_tendencia(df_treino, df_pre_treino, dir_s)
    tab4, frase4 = _secao_sazonalidade(df_treino, dir_s)
    tab5, frase5 = _secao_2020_comparativo(df_treino, df_pre_treino)
    tab6, frase6 = _secao_defasagem(df_pre_treino)
    tab7, frase7 = _secao_distribuicao_alvo(df_treino)

    # Item 15: Metadados no cabeçalho
    data_utc = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    sha_str = sha256_painel if sha256_painel else "Não informado"
    msg_metodologica = (
        "Dados observados do Novo Caged; nenhum número deste relatório vem de validação ou teste."
    )

    p_ign_fmt = formatar_pt_br(linhas_painel_ignoradas)
    pre_ign_fmt = formatar_pt_br(linhas_pre_ignoradas)

    conteudo_md = f"""# Análise Exploratória de Dados (EDA) — Conjunto de Treino

- **Data de geração (UTC):** {data_utc}
- **SHA-256 do Painel:** {sha_str}
- **Nota metodológica:** {msg_metodologica}

Relatório descritivo automatizado sobre o conjunto de treino do Novo Caged (202001 a 202409).
Registros posteriores (embargo e validação) foram estritamente isolados e ignorados:
- Linhas de painel desconsideradas: {p_ign_fmt}
- Linhas pré-agregadas desconsideradas (> 202412): {pre_ign_fmt}

---

## 1. Qualidade e cobertura

{tab1}

> **Fato observado:** {frase1}

---

## 2. Densidade (D04a)

{tab2}

> **Fato observado:** {frase2}

---

## 3. Nível e tendência

{tab3}

> **Fato observado:** {frase3}

---

## 4. Sazonalidade

{tab4}

> **Fato observado:** {frase4}

---

## 5. 2020 × demais anos

{tab5}

> **Fato observado:** {frase5}

---

## 6. Defasagem de declaração (R02)

{tab6}

> **Fato observado:** {frase6}

---

## 7. Distribuição do alvo

{tab7}

> **Fato observado:** {frase7}
"""

    caminho_md = dir_s / "eda_treino.md"
    caminho_md.write_text(conteudo_md, encoding="utf-8")
    return caminho_md


def main() -> None:
    """Ponto de entrada CLI para geração da EDA do treino."""
    parser = argparse.ArgumentParser(description="Geração de EDA do treino do Novo Caged.")
    parser.add_argument("--painel", required=True, help="Caminho do Parquet do painel.")
    parser.add_argument("--dados", required=True, help="Diretório de dados (contém caged/).")
    parser.add_argument(
        "--saida", required=True, help="Diretório de saída para eda_treino.md e PNGs."
    )

    args = parser.parse_args()

    try:
        p_painel = Path(args.painel)
        df_painel = pd.read_parquet(p_painel)
        sha256_painel = (
            hashlib.sha256(p_painel.read_bytes()).hexdigest() if p_painel.exists() else None
        )

        dir_parquet = Path(args.dados) / "caged" / "parquet"
        # Item 5: EDA carrega pre_agregado com por_tipo=True
        df_pre, rel_carga = carregar_pre_agregado(
            dir_parquet, limite_competencia_mov="202512", por_tipo=True
        )

        caminho_md = gerar_eda_treino(
            painel=df_painel,
            pre_agregado=df_pre,
            dir_saida=args.saida,
            relatorio_carga=rel_carga,
            sha256_painel=sha256_painel,
        )
        print(f"EDA gerada com sucesso em: {caminho_md}")
    except Exception as exc:
        print(f"Erro na geração da EDA: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
