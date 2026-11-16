"""Testes de modelos clássicos e validação cruzada temporal (S7-classicos)."""

from __future__ import annotations

import pandas as pd
import pytest

from citizentech_ml.classicos import (
    treinar_classicos,
)
from citizentech_ml.features.datas import gerar_intervalo_meses
from citizentech_ml.features.extracao import COLUNAS_FEATURES


def _criar_painel_mvp_sintetico(
    inicio: str = "202101",
    fim: str = "202409",
    destinos: tuple[str, ...] = (
        "analista_dados_bi",
        "analista_monitoramento_iot",
        "analista_processos",
    ),
    ufs: tuple[str, ...] = ("35", "33"),
    alvo_base: float = 25.0,
    incluir_baselines: bool = True,
) -> pd.DataFrame:
    """Gera painel sintético no formato exato do MVP R29 para testes rápidos."""
    meses = gerar_intervalo_meses(inicio, fim)
    linhas = []
    colunas_num = [c for c in COLUNAS_FEATURES if "_total" not in c and c != "mes"]

    for m in meses:
        mes_num = int(m[-2:])
        for dest in destinos:
            for uf in ufs:
                linha = {
                    "competencia": m,
                    "destino": dest,
                    "uf": uf,
                    "mes": mes_num,
                    "alvo": float(alvo_base),
                }
                for c in colunas_num:
                    linha[c] = float(alvo_base)
                if incluir_baselines:
                    linha["admissoes_soma_3m"] = float(alvo_base)
                    linha["admissoes_sazonal_ano_anterior"] = float(alvo_base)
                    linha["previsao_persistencia"] = float(alvo_base)
                    linha["previsao_sazonal"] = float(alvo_base)
                linhas.append(linha)

    return pd.DataFrame(linhas)


def test_prioritario_red_treinar_classicos_retorna_tres_modelos_e_previsoes() -> None:
    """Teste prioritário RED: esqueleto retorna coleção vazia e falha por asserção."""
    painel = _criar_painel_mvp_sintetico()
    resultado = treinar_classicos(painel, seed=42, n_iter=1, n_splits=3)

    assert "estimadores" in resultado, "Deveria conter chave 'estimadores'"
    assert set(resultado["estimadores"].keys()) == {
        "ridge",
        "random_forest",
        "hist_gradient_boosting",
    }, "Deveria conter exatamente 3 estimadores clássicos"

    assert "previsoes" in resultado, "Deveria conter chave 'previsoes'"
    df_prev = resultado["previsoes"]
    assert isinstance(df_prev, pd.DataFrame)
    colunas_esperadas = {"competencia", "destino", "uf", "modelo", "alvo", "previsao"}
    assert colunas_esperadas.issubset(df_prev.columns)

    assert "relatorio" in resultado, "Deveria conter chave 'relatorio'"
    relatorio = resultado["relatorio"]
    assert "folds" in relatorio
    assert len(relatorio["folds"]) == 3
    for fold in relatorio["folds"]:
        assert fold["meses_embargo"] == 3


def test_mutar_valores_2025_nao_altera_treino() -> None:
    """Mutar valores de 2025 não altera tuning, coeficientes nem densidade do treino."""
    painel_original = _criar_painel_mvp_sintetico(inicio="202101", fim="202509")

    # Painel com 2025 mutado com alvos e features extremas
    painel_mutado = painel_original.copy()
    mascara_2025 = painel_mutado["competencia"] >= "202501"
    painel_mutado.loc[mascara_2025, "alvo"] = 9999.0
    painel_mutado.loc[mascara_2025, "admissoes"] = 8888.0

    res_orig = treinar_classicos(
        painel_original, seed=42, n_iter=1, n_splits=2, incluir_validacao=False
    )
    res_mut = treinar_classicos(
        painel_mutado, seed=42, n_iter=1, n_splits=2, incluir_validacao=False
    )

    # Coeficientes do Ridge devem ser estritamente idênticos
    coef_orig = res_orig["relatorio"]["coeficientes_ridge"]
    coef_mut = res_mut["relatorio"]["coeficientes_ridge"]
    assert coef_orig == coef_mut

    # Melhores parâmetros de busca devem ser idênticos
    params_orig = res_orig["relatorio"]["hiperparametros_e_cv"]["ridge"]["melhores_parametros"]
    params_mut = res_mut["relatorio"]["hiperparametros_e_cv"]["ridge"]["melhores_parametros"]
    assert params_orig == params_mut

    # Densidade de treino deve ser idêntica
    assert (
        res_orig["relatorio"]["densidade"]["series_elegiveis_treino_global"]
        == res_mut["relatorio"]["densidade"]["series_elegiveis_treino_global"]
    )


def test_dados_2020_presentes_nao_entram_no_fit() -> None:
    """Origens de 2020 presentes no painel não entram no fit (treino estrito >= 202101)."""
    painel_com_2020 = _criar_painel_mvp_sintetico(inicio="202001", fim="202409")

    res = treinar_classicos(painel_com_2020, seed=42, n_iter=1, n_splits=2)
    periodo_treino = res["relatorio"]["periodo_treino"]

    assert periodo_treino["inicio"] >= "202101"
    assert periodo_treino["fim"] <= "202409"

    for fold in res["relatorio"]["folds"]:
        assert all(m >= "202101" for m in fold["meses_treino"])


def test_serie_elegivel_so_no_fim_do_treino_nao_entra_em_fold_antigo() -> None:
    """Série com densidade insuficiente no início não pode entrar em folds anteriores (D04a)."""
    painel = _criar_painel_mvp_sintetico(inicio="202101", fim="202409", alvo_base=25.0)

    # Série específica (analista_dados_bi, 33) tem alvo 1.0 até 202312 (<10), e 50.0 em 2024 (>=10)
    mascara_serie = (painel["destino"] == "analista_dados_bi") & (painel["uf"] == "33")
    mascara_antiga = mascara_serie & (painel["competencia"] <= "202306")
    painel.loc[mascara_antiga, "alvo"] = 1.0
    mascara_recente = mascara_serie & (painel["competencia"] > "202306")
    painel.loc[mascara_recente, "alvo"] = 80.0

    res = treinar_classicos(painel, seed=42, n_iter=1, n_splits=3)
    folds = res["relatorio"]["folds"]

    # No primeiro fold (mais antigo), o treino é curto e a série tem média 1.0 (< 10) -> excluída
    fold_0 = folds[0]
    fold_0_excluidas = fold_0["series_excluidas_densidade"]
    assert fold_0_excluidas >= 1, "A série com média 1.0 no início deveria ser excluída no fold 0"


def test_qualquer_competencia_2026_falha() -> None:
    """Competência >= 202601 deve falhar imediatamente (D10 / holdout congelado)."""
    painel = _criar_painel_mvp_sintetico(inicio="202101", fim="202409")
    linha_2026 = painel.iloc[0:1].copy()
    linha_2026["competencia"] = "202601"
    painel_com_2026 = pd.concat([painel, linha_2026], ignore_index=True)

    with pytest.raises(ValueError, match="holdout 2026"):
        treinar_classicos(painel_com_2026, seed=42, n_iter=1)


def test_input_permanece_inalterado() -> None:
    """O DataFrame de entrada não deve sofrer mutação."""
    painel = _criar_painel_mvp_sintetico()
    copia_esperada = painel.copy(deep=True)

    treinar_classicos(painel, seed=42, n_iter=1, n_splits=2)

    pd.testing.assert_frame_equal(painel, copia_esperada)


def test_reprodutibilidade_mesma_seed_mesmas_previsoes() -> None:
    """Execuções repetidas com a mesma seed produzem previsões rigorosamente idênticas."""
    painel = _criar_painel_mvp_sintetico()

    res1 = treinar_classicos(painel, seed=42, n_iter=1, n_splits=2)
    res2 = treinar_classicos(painel, seed=42, n_iter=1, n_splits=2)

    pd.testing.assert_frame_equal(res1["previsoes"], res2["previsoes"])
    assert (
        res1["relatorio"]["hiperparametros_e_cv"]
        == res2["relatorio"]["hiperparametros_e_cv"]
    )


def test_alvos_invalidos_negativos_ou_inf_geram_erro() -> None:
    """Alvos negativos ou infinitos no treino geram erro explícito."""
    painel_neg = _criar_painel_mvp_sintetico()
    painel_neg.loc[0, "alvo"] = -5.0

    with pytest.raises(ValueError, match="valores não finitos ou negativos"):
        treinar_classicos(painel_neg, seed=42, n_iter=1)

    painel_inf = _criar_painel_mvp_sintetico()
    painel_inf.loc[0, "alvo"] = float("inf")

    with pytest.raises(ValueError, match="valores não finitos ou negativos"):
        treinar_classicos(painel_inf, seed=42, n_iter=1)


def test_hgb_early_stopping_desabilitado_e_rf_paralelismo_limitado() -> None:
    """HGB tem early_stopping=False e RF respeita limite de paralelismo (<=6)."""
    painel = _criar_painel_mvp_sintetico()
    res = treinar_classicos(painel, seed=42, n_iter=1, n_splits=2)

    hgb_estimator = res["estimadores"]["hist_gradient_boosting"]
    hgb_reg = hgb_estimator.pipeline_.named_steps["regressor"]
    assert hgb_reg.early_stopping is False

    rf_estimator = res["estimadores"]["random_forest"]
    rf_reg = rf_estimator.pipeline_.named_steps["regressor"]
    assert rf_reg.n_jobs <= 6


def test_previsoes_negativas_preservadas_brutas_e_contabilizadas() -> None:
    """Previsões brutas são preservadas e contagem de negativas é registrada."""
    painel = _criar_painel_mvp_sintetico()
    res = treinar_classicos(painel, seed=42, n_iter=1, n_splits=2)

    contagem_neg = res["relatorio"]["exclusoes_e_avisos"]["previsoes_negativas"]
    assert "ridge" in contagem_neg
    assert "random_forest" in contagem_neg
    assert "hist_gradient_boosting" in contagem_neg
    assert all(isinstance(v, int) for v in contagem_neg.values())


def test_validacao_externa_incluida_somente_quando_solicitada() -> None:
    """Partição 2025 só é avaliada com incluir_validacao=True."""
    painel = _criar_painel_mvp_sintetico(inicio="202101", fim="202509")

    # 1. Sem validação
    res_sem = treinar_classicos(painel, seed=42, n_iter=1, n_splits=2, incluir_validacao=False)
    assert res_sem["relatorio"]["validacao_externa"] is None
    assert not (res_sem["previsoes"]["particao"] == "validacao").any()

    # 2. Com validação
    res_com = treinar_classicos(painel, seed=42, n_iter=1, n_splits=2, incluir_validacao=True)
    assert res_com["relatorio"]["validacao_externa"] is not None
    assert (res_com["previsoes"]["particao"] == "validacao").any()
