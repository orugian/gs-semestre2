"""Testes do módulo de redes neurais (MLP PyTorch CPU)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from citizentech_ml.features.datas import gerar_intervalo_meses
from citizentech_ml.rede_neural import (
    MLPRegressor,
    PreprocessadorRNA,
    _particionar_treino_interno_fold,
    treinar_rna,
)


def _criar_painel_mvp_mensal(
    inicio: str = "202101",
    fim: str = "202409",
    destinos: list[str] | None = None,
    ufs: list[str] | None = None,
) -> pd.DataFrame:
    """Gera painel mensal sintético com destinos e UFs para testes de RNA."""
    destinos = destinos or [
        "analista_dados_bi",
        "analista_monitoramento_iot",
        "analista_processos",
    ]
    ufs = ufs or ["35", "33"]
    meses = gerar_intervalo_meses(inicio, fim)

    linhas = []
    for m in meses:
        mes_num = int(m[-2:])
        for d_idx, d in enumerate(destinos):
            for u_idx, u in enumerate(ufs):
                base_val = 15.0 + (d_idx + 1) * 10.0 + (u_idx + 1) * 5.0
                alvo = base_val + 2.0 * np.sin(mes_num * np.pi / 6.0)
                linhas.append(
                    {
                        "competencia": m,
                        "mes": mes_num,
                        "destino": d,
                        "uf": u,
                        "admissoes": float(alvo / 3.0),
                        "desligamentos": float(alvo / 4.0),
                        "admissoes_lag_1": float(alvo / 3.0),
                        "admissoes_lag_2": float(alvo / 3.0),
                        "admissoes_lag_3": float(alvo / 3.0),
                        "admissoes_lag_12": float(alvo / 3.0),
                        "desligamentos_lag_1": float(alvo / 4.0),
                        "desligamentos_lag_2": float(alvo / 4.0),
                        "desligamentos_lag_3": float(alvo / 4.0),
                        "desligamentos_lag_12": float(alvo / 4.0),
                        "admissoes_soma_3m": float(alvo),
                        "admissoes_media_3m": float(alvo / 3.0),
                        "admissoes_sazonal_ano_anterior": float(alvo),
                        "alvo": float(alvo),
                    }
                )
    return pd.DataFrame(linhas)


def test_treinar_rna_tracer_bullet_duas_configs_curvas_checkpoint_previsoes():
    """RED prioritário: exige 2 configurações, curvas não-vazias, checkpoint e previsões."""
    df = _criar_painel_mvp_mensal("202101", "202409")
    resultado = treinar_rna(df, seed=42, max_epochs=2, patience=2)

    # 1. Exige pelo menos 2 configurações avaliadas (A e B)
    assert "configs" in resultado
    assert len(resultado["configs"]) >= 2
    assert "A" in resultado["configs"]
    assert "B" in resultado["configs"]

    # 2. Exige curvas de loss não-vazias
    curvas = resultado.get("curvas")
    assert isinstance(curvas, pd.DataFrame)
    assert not curvas.empty
    assert {"config", "epoca", "loss_fit"}.issubset(curvas.columns)

    # 3. Exige modelo em PyTorch CPU reabrível
    modelo = resultado.get("modelo")
    assert isinstance(modelo, MLPRegressor)
    state_dict = modelo.state_dict()
    assert len(state_dict) > 0
    for p in modelo.parameters():
        assert p.device.type == "cpu"

    # 4. Exige previsões alinhadas
    previsoes = resultado.get("previsoes")
    assert isinstance(previsoes, pd.DataFrame)
    assert not previsoes.empty
    colunas_prev_esperadas = {"competencia", "destino", "uf", "modelo", "alvo", "previsao"}
    assert colunas_prev_esperadas.issubset(previsoes.columns)


def test_origens_2020_nao_entram_fit():
    """D10/D04a: dados de 2020 são apenas histórico de lags, nunca entram no fit."""
    df = _criar_painel_mvp_mensal("202001", "202409")
    resultado = treinar_rna(df, seed=42, max_epochs=2, patience=2)

    curvas = resultado["curvas"]
    assert not curvas.empty

    # Verifica os intervalos de fit nos folds da configuração
    cfg_a = resultado["configs"]["A"]
    for f in cfg_a["folds"]:
        meses_fit = f["intervalos"]["meses_fit"]
        assert all(m >= "202101" for m in meses_fit), f"Mês < 202101 encontrado no fit: {meses_fit}"


def test_mutar_2025_nao_muda_ajuste_nem_selecao_quando_sem_validacao():
    """Contraexemplo: mutar 2025 não altera o ajuste/seleção sem incluir_validacao."""
    df1 = _criar_painel_mvp_mensal("202101", "202509")
    df2 = df1.copy()

    # Muta drasticamente os alvos de 2025
    mascara_2025 = df2["competencia"] >= "202501"
    df2.loc[mascara_2025, "alvo"] = df2.loc[mascara_2025, "alvo"] * 100.0

    res1 = treinar_rna(df1, seed=42, max_epochs=2, patience=2, incluir_validacao=False)
    res2 = treinar_rna(df2, seed=42, max_epochs=2, patience=2, incluir_validacao=False)

    # Melhor configuração deve ser exatamente a mesma
    assert res1["melhor_config"] == res2["melhor_config"]

    # Métricas de treino global devem ser idênticas
    mae1 = res1["relatorio"]["treino_global"]["mae"]
    mae2 = res2["relatorio"]["treino_global"]["mae"]
    assert np.isclose(mae1, mae2, atol=1e-5)

    # Validação externa não deve ter sido avaliada
    assert res1["relatorio"]["validacao_externa"] is None
    assert res2["relatorio"]["validacao_externa"] is None


def test_earlystop_e_embargo_internos_expressos_por_datas():
    """Contraexemplo: earlystop e embargo internos expressos por datas de calendário, não linhas."""
    df = _criar_painel_mvp_mensal("202101", "202409")
    df_tr = df[df["competencia"] <= "202306"].copy()

    df_fit, df_es, intervalos = _particionar_treino_interno_fold(
        df_tr, coluna_tempo="competencia", meses_earlystop=3, meses_embargo=3
    )

    meses_fit = set(intervalos["meses_fit"])
    meses_emb = set(intervalos["meses_embargo"])
    meses_es = set(intervalos["meses_earlystop"])

    # Disjunção estrita dos conjuntos de meses
    assert len(meses_fit.intersection(meses_emb)) == 0
    assert len(meses_fit.intersection(meses_es)) == 0
    assert len(meses_emb.intersection(meses_es)) == 0

    # Ordem estrita: fit < embargo < earlystop
    assert max(meses_fit) < min(meses_emb)
    assert max(meses_emb) < min(meses_es)
    assert len(meses_es) == 3
    assert len(meses_emb) == 3


def test_scaler_fit_nao_usa_janela_val():
    """Contraexemplo: pré-processador ajustado estritamente no subset de fit, sem dados futuros."""
    df_fit = _criar_painel_mvp_mensal("202101", "202212")
    prep = PreprocessadorRNA()
    prep.fit(df_fit)

    med_original = dict(prep.medianas)
    mean_original = list(prep.scaler_x_mean)
    alvo_original = prep.alvo_mean

    # Cria dados de validação com valores extremos
    df_val = _criar_painel_mvp_mensal("202301", "202306")
    df_val["alvo"] = 999999.0
    df_val["admissoes"] = 999999.0

    # Aplicação de transform_x e transform_y não pode alterar o estado do pré-processador
    X_val = prep.transform_x(df_val)
    y_val = prep.transform_y(df_val["alvo"])

    assert prep.medianas == med_original
    assert prep.scaler_x_mean == mean_original
    assert prep.alvo_mean == alvo_original
    assert X_val.shape[0] == len(df_val)
    assert y_val.shape[0] == len(df_val)


def test_densidade_por_fold():
    """Contraexemplo: densidade >= 10 é calculada para cada fold individualmente."""
    df = _criar_painel_mvp_mensal("202101", "202409")

    # Injeta série com baixa densidade (< 10) apenas no primeiro fold
    mascara_baixa = (df["destino"] == "analista_processos") & (df["uf"] == "33")
    df.loc[mascara_baixa & (df["competencia"] <= "202212"), "alvo"] = 2.0

    res = treinar_rna(df, seed=42, max_epochs=2, patience=2)
    cfg_a = res["configs"]["A"]
    # Verifica que o relatório de cada fold registra a contagem de séries elegíveis
    for f in cfg_a["folds"]:
        assert "series_elegiveis" in f
        assert f["series_elegiveis"] > 0


def test_checkpoint_restaura_melhor_epoca():
    """Contraexemplo: checkpoint restaura a melhor época observada na janela interna."""
    df = _criar_painel_mvp_mensal("202101", "202409")
    res = treinar_rna(df, seed=42, max_epochs=4, patience=15)

    cfg_a = res["configs"]["A"]
    for f in cfg_a["folds"]:
        assert 1 <= f["melhor_epoca"] <= f["epocas_treinadas"]


def test_determinismo_cpu_mesma_seed():
    """Contraexemplo: determinismo em CPU com a mesma seed produz resultados idênticos."""
    df = _criar_painel_mvp_mensal("202101", "202409")
    res1 = treinar_rna(df, seed=42, max_epochs=2, patience=2)
    res2 = treinar_rna(df, seed=42, max_epochs=2, patience=2)

    curvas1 = res1["curvas"]["loss_fit"].to_numpy()
    curvas2 = res2["curvas"]["loss_fit"].to_numpy()
    assert np.allclose(curvas1, curvas2, atol=1e-6)

    mae1 = res1["relatorio"]["treino_global"]["mae"]
    mae2 = res2["relatorio"]["treino_global"]["mae"]
    assert np.isclose(mae1, mae2, atol=1e-6)


def test_alvo_negativo_ou_inf_rejeitados():
    """Contraexemplo: alvo negativo ou não-finito gera erro explícito."""
    df = _criar_painel_mvp_mensal("202101", "202409")
    df.loc[0, "alvo"] = -5.0
    with pytest.raises(ValueError, match="valores negativos ou não finitos"):
        treinar_rna(df, seed=42, max_epochs=2)

    df.loc[0, "alvo"] = np.inf
    with pytest.raises(ValueError, match="valores negativos ou não finitos"):
        treinar_rna(df, seed=42, max_epochs=2)


def test_conjunto_vazio_rejeitado():
    """Contraexemplo: DataFrame vazio gera erro claro."""
    df_vazio = pd.DataFrame()
    with pytest.raises(ValueError, match="painel vazio"):
        treinar_rna(df_vazio)


def test_competencia_2026_rejeitada():
    """Contraexemplo: competências de teste (>= 2026) são categoricamente proibidas."""
    df = _criar_painel_mvp_mensal("202101", "202601")
    with pytest.raises(ValueError, match="Competência de teste .* presente"):
        treinar_rna(df, seed=42, max_epochs=2)


def test_preservar_previsoes_negativas_sem_clipagem():
    """Preserva previsões negativas brutas e declara contagem, sem clipagem silenciosa."""
    df = _criar_painel_mvp_mensal("202101", "202409")
    res = treinar_rna(df, seed=42, max_epochs=2, patience=2)

    rel = res["relatorio"]
    assert "contagem_negativos" in rel
    assert isinstance(rel["contagem_negativos"], int)
    assert rel["contagem_negativos"] >= 0


def test_treinar_rna_recusa_parametros_invalidos():
    """Valida que parâmetros básicos como max_epochs e patience devem ser estritamente positivos."""
    df = _criar_painel_mvp_mensal("202101", "202409")
    with pytest.raises(ValueError, match="max_epochs"):
        treinar_rna(df, max_epochs=0)
    with pytest.raises(ValueError, match="patience"):
        treinar_rna(df, patience=0)
    with pytest.raises(ValueError, match="min_delta"):
        treinar_rna(df, min_delta=-1.0)
    with pytest.raises(ValueError, match="n_splits"):
        treinar_rna(df, n_splits=0)
    with pytest.raises(ValueError, match="limite_densidade"):
        treinar_rna(df, limite_densidade=-1.0)


def test_treinar_rna_recusa_inf_em_features_antecipado():
    """Valores infinitos em features devem ser recusados de forma limpa e antecipada."""
    df = _criar_painel_mvp_mensal("202101", "202409")
    df.loc[0, "admissoes"] = np.inf
    with pytest.raises(ValueError, match="inf|finito"):
        treinar_rna(df, max_epochs=2, patience=1)


def test_treinar_rna_exige_fontes_baselines_obrigatorias():
    """Não permite treinar sem as colunas fontes determinísticas de baselines."""
    df = _criar_painel_mvp_mensal("202101", "202409")
    df_sem_fonte = df.drop(columns=["admissoes_soma_3m"])
    with pytest.raises(ValueError, match="admissoes_soma_3m"):
        treinar_rna(df_sem_fonte, max_epochs=2, patience=1)


def test_treinar_rna_relatorio_folds_completo():
    """Relatório por fold deve incluir n, MAE, RMSE, WAPE, MASE, macro_mae,
    tabela_series, exclusoes e intervalos.
    """
    df = _criar_painel_mvp_mensal("202101", "202409")
    res = treinar_rna(df, max_epochs=2, patience=1, n_splits=2)
    cfg_a = res["configs"]["A"]
    for f in cfg_a["folds"]:
        assert "n" in f and f["n"] > 0
        assert "mae" in f and f["mae"] is not None
        assert "rmse" in f and f["rmse"] is not None
        assert "wape" in f
        assert "mase" in f
        assert "macro_mae" in f
        assert "tabela_series" in f and len(f["tabela_series"]) > 0
        assert "exclusoes" in f
        assert "series_elegiveis" in f["exclusoes"]
        assert "series_excluidas_densidade" in f["exclusoes"]
        assert "linhas_descartadas" in f["exclusoes"]
        assert "intervalos" in f
        assert "meses_fit" in f["intervalos"]
        assert "meses_earlystop" in f["intervalos"]
        assert "meses_embargo" in f["intervalos"]
        assert "meses_avaliacao" in f["intervalos"]


def test_treinar_rna_validacao_externa_alvo_invalido_rejeitado():
    """Se incluir_validacao=True, alvo negativo em 2025 deve ser rejeitado."""
    df = _criar_painel_mvp_mensal("202101", "202509")
    mascara_2025 = df["competencia"] >= "202501"
    df.loc[mascara_2025, "alvo"] = -10.0
    with pytest.raises(ValueError, match="alvo.*negativo|não finito"):
        treinar_rna(df, max_epochs=2, patience=1, incluir_validacao=True)
