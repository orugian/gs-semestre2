"""Contraexemplos independentes RNA; somente fixtures e artefatos temporarios."""

import json

import numpy as np
import pandas as pd
import pytest

from citizentech_ml.rede_neural import carregar_modelo_rna, treinar_rna

DESTINOS = [
    "analista_dados_bi",
    "analista_monitoramento_iot",
    "analista_processos",
    "gerente_projetos_produto",
    "analista_suporte_infra",
    "desenvolvedor_sistemas",
]


@pytest.fixture(scope="module")
def painel_rna_aceite():
    linhas = []
    for i, mes in enumerate(pd.period_range("2021-01", "2024-09", freq="M")):
        for j, destino in enumerate(DESTINOS):
            v = float(20 + j * 2 + i % 5)
            linhas.append(
                {
                    "competencia": mes.strftime("%Y%m"),
                    "destino": destino,
                    "uf": "35",
                    "mes": mes.month,
                    "admissoes": v,
                    "desligamentos": v / 2,
                    "admissoes_soma_3m": 3 * v,
                    "admissoes_sazonal_ano_anterior": 3 * v - 1,
                    "alvo": 3 * v + i % 2,
                }
            )
    return pd.DataFrame(linhas)


@pytest.fixture(scope="module")
def resultado_rna_aceite(painel_rna_aceite):
    return treinar_rna(painel_rna_aceite, max_epochs=2, patience=1, n_splits=1)


def test_api_rna_aplica_r29_e_nao_treina_destinos_fora_do_mvp(resultado_rna_aceite):
    assert set(resultado_rna_aceite["previsoes"]["destino"]) == set(DESTINOS[:3])


def test_api_rna_registra_recorte_e_comparacao_baseline(resultado_rna_aceite):
    rel = resultado_rna_aceite["relatorio"]
    assert "recorte" in rel
    assert len(rel["recorte"]["hash_recorte"]) == 64
    assert set(rel["baselines"]) >= {"persistencia", "sazonal"}


def test_api_rna_recusa_origem_fora_do_painel_desenvolvimento(painel_rna_aceite):
    extra = painel_rna_aceite.iloc[:1].copy()
    extra["competencia"] = "202510"
    entrada = pd.concat([painel_rna_aceite, extra], ignore_index=True)
    with pytest.raises(ValueError, match="202509|intervalo|desenvolvimento"):
        treinar_rna(entrada, max_epochs=2, patience=1, n_splits=1)


def test_feature_infinita_nao_pode_gerar_modelo_silenciosamente(painel_rna_aceite):
    entrada = painel_rna_aceite.copy()
    entrada["admissoes"] = np.inf
    # O contrato exige recusa, nao uma mensagem especifica de implementacao.
    with pytest.raises(ValueError):
        treinar_rna(entrada, max_epochs=2, patience=1, n_splits=1)


def test_loader_rna_exige_hashes_antes_de_carregar(tmp_path, monkeypatch, resultado_rna_aceite):
    from citizentech_ml import rede_neural

    (tmp_path / "checkpoint_rna.pt").write_bytes(b"arquivo na fronteira de desserializacao")
    (tmp_path / "preprocessador.json").write_text(
        json.dumps(resultado_rna_aceite["preprocessador"].to_dict()), encoding="utf-8"
    )
    (tmp_path / "metricas.json").write_text(
        json.dumps({"sha256_artefatos": {}, "melhor_config": {}}), encoding="utf-8"
    )
    chamadas = []

    def carga_observada(*args, **kwargs):
        chamadas.append(True)
        raise AssertionError("torch.load atingido sem hashes obrigatorios")

    monkeypatch.setattr(rede_neural.torch, "load", carga_observada)
    with pytest.raises(ValueError, match="[Hh]ash|[Mm]anifesto"):
        carregar_modelo_rna(tmp_path)
    assert chamadas == []


def test_valores_2025_nao_controlam_ajuste_quando_validacao_desligada(
    painel_rna_aceite, resultado_rna_aceite
):
    futuro = painel_rna_aceite.iloc[:1].copy()
    futuro["competencia"] = "202501"
    futuro["alvo"] = np.inf
    futuro["admissoes"] = np.inf
    entrada = pd.concat([painel_rna_aceite, futuro], ignore_index=True)
    resultado = treinar_rna(entrada, max_epochs=2, patience=1, n_splits=1)
    pd.testing.assert_frame_equal(resultado["previsoes"], resultado_rna_aceite["previsoes"])


def test_valores_de_destino_descartado_nao_controlam_fit_mvp(
    painel_rna_aceite, resultado_rna_aceite
):
    entrada = painel_rna_aceite.copy()
    entrada.loc[entrada["destino"] == "desenvolvedor_sistemas", "admissoes"] = np.inf
    resultado = treinar_rna(entrada, max_epochs=2, patience=1, n_splits=1)
    pd.testing.assert_frame_equal(resultado["previsoes"], resultado_rna_aceite["previsoes"])
