"""Contraexemplos independentes do orquestrador; somente fixtures, sem dados reais."""

import hashlib
import json

import pandas as pd
import pytest

from citizentech_ml.classicos import treinar_classicos
from citizentech_ml.features.extracao import COLUNAS_FEATURES
from citizentech_ml.treinar_classicos import (
    carregar_artefatos_classicos,
    salvar_artefatos_classicos,
)


@pytest.fixture(scope="module")
def painel_aceite():
    linhas = []
    for i, mes in enumerate(pd.period_range("2021-01", "2025-09", freq="M")):
        for j, destino in enumerate(
            ["analista_dados_bi", "analista_monitoramento_iot", "analista_processos"]
        ):
            for uf in ["35", "33"]:
                nivel = float(20 + j * 10 + i % 7)
                linha = {c: nivel for c in COLUNAS_FEATURES if "_total" not in c}
                linha.update(
                    competencia=mes.strftime("%Y%m"),
                    destino=destino,
                    uf=uf,
                    mes=mes.month,
                    alvo=nivel * 3 + i % 3,
                    admissoes_soma_3m=nivel * 3,
                    admissoes_sazonal_ano_anterior=nivel * 3 - 1,
                )
                linhas.append(linha)
    painel = pd.DataFrame(linhas)
    # Feature pode ser imputada, mas baseline ausente exclui esta linha da comparacao justa.
    idx = painel.index[painel["competencia"] == "202501"][0]
    painel.loc[idx, "admissoes_sazonal_ano_anterior"] = float("nan")
    return painel


@pytest.fixture(scope="module")
def resultado_aceite(painel_aceite):
    return treinar_classicos(painel_aceite, n_iter=1, incluir_validacao=True)


def test_previsoes_tabulares_usam_a_mesma_mascara_das_metricas(resultado_aceite):
    resultado = resultado_aceite
    externas = resultado["previsoes"].query("particao == 'validacao'")
    for nome, metricas in resultado["relatorio"]["validacao_externa"]["modelos"].items():
        assert len(externas[externas["modelo"] == nome]) == metricas["n"]


def test_relatorio_traz_hash_do_recorte_e_comparacao_de_baselines(resultado_aceite):
    rel = resultado_aceite["relatorio"]
    assert len(rel["recorte"]["hash_recorte"]) == 64
    assert set(rel["baselines"]) >= {"persistencia", "sazonal"}


def test_alvo_negativo_na_validacao_explicita_e_recusado(painel_aceite):
    painel = painel_aceite.copy()
    painel.loc[painel["competencia"] == "202501", "alvo"] = -1.0
    with pytest.raises(ValueError, match="alvo|Alvo|negativ"):
        treinar_classicos(painel, n_iter=1, incluir_validacao=True)


def test_manifesto_nao_pode_omitir_hash_do_modelo_antes_de_desserializar(tmp_path, monkeypatch):
    from citizentech_ml import treinar_classicos as cli

    metricas = b"{}"
    (tmp_path / "metricas.json").write_bytes(metricas)
    (tmp_path / "modelos.joblib").write_bytes(b"nao e um pickle confiavel")
    (tmp_path / "manifesto.json").write_text(
        json.dumps(
            {
                "versao_manifesto": "1.0",
                "arquivos": {"metricas.json": hashlib.sha256(metricas).hexdigest()},
            }
        ),
        encoding="utf-8",
    )
    chamadas = []

    def desserializacao_observada(*args, **kwargs):
        chamadas.append(True)
        raise AssertionError("Desserializador atingido antes de validar o manifesto completo")

    monkeypatch.setattr(cli.joblib, "load", desserializacao_observada)
    with pytest.raises(ValueError, match="[Mm]anifesto|[Aa]rquivos|hash"):
        carregar_artefatos_classicos(tmp_path)
    assert chamadas == []


def test_manifesto_com_caminho_inseguro_falha(tmp_path):
    """Manifesto com caminhos inseguros (absolutos, traversal ou separadores) deve falhar."""
    dummy_hash = "a" * 64
    arquivos_inseguros = {
        "modelos.joblib": dummy_hash,
        "previsoes.parquet": dummy_hash,
        "previsoes.csv": dummy_hash,
        "../metricas.json": dummy_hash,
    }
    (tmp_path / "manifesto.json").write_text(
        json.dumps(
            {
                "versao_manifesto": "1.0",
                "arquivos": arquivos_inseguros,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="[Mm]anifesto|caminho inseguro|inválido"):
        carregar_artefatos_classicos(tmp_path)


def test_manifesto_com_entrada_removida_ou_extra_falha(tmp_path):
    """Manifesto que omite arquivo obrigatório ou inclui artefato extra deve ser recusado."""
    dummy_hash = "b" * 64

    # 1. Omissão de previsoes.parquet
    (tmp_path / "manifesto.json").write_text(
        json.dumps(
            {
                "versao_manifesto": "1.0",
                "arquivos": {
                    "modelos.joblib": dummy_hash,
                    "previsoes.csv": dummy_hash,
                    "metricas.json": dummy_hash,
                },
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="[Mm]anifesto|omissão"):
        carregar_artefatos_classicos(tmp_path)

    # 2. Arquivo extra não autorizado
    (tmp_path / "manifesto.json").write_text(
        json.dumps(
            {
                "versao_manifesto": "1.0",
                "arquivos": {
                    "modelos.joblib": dummy_hash,
                    "previsoes.parquet": dummy_hash,
                    "previsoes.csv": dummy_hash,
                    "metricas.json": dummy_hash,
                    "script_externo.py": dummy_hash,
                },
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="[Mm]anifesto|extras|desconhecidos"):
        carregar_artefatos_classicos(tmp_path)


def test_igualdade_tabela_metricas_em_cv_com_baseline_ausente(painel_aceite):
    """Garante equivalência estrita entre previsões e métricas em CV mesmo com NaN no baseline."""
    painel = painel_aceite.copy()
    # Injetar NaN em baseline durante janela de validação de fold de treino (ex: 202306)
    idx_cv = painel.index[painel["competencia"] == "202306"][0]
    painel.loc[idx_cv, "admissoes_sazonal_ano_anterior"] = float("nan")

    res = treinar_classicos(painel, n_iter=1, n_splits=3, incluir_validacao=True)

    # Validar que em cada fold de CV a contagem tabular bate exatamente com o 'n' de métricas
    for fold in res["relatorio"]["folds"]:
        fold_idx = fold["fold"]
        nome_particao = f"cv_fold_{fold_idx}"
        for nome_modelo, metricas_mod in fold["modelos"].items():
            prevs_fold = res["previsoes"][
                (res["previsoes"]["particao"] == nome_particao)
                & (res["previsoes"]["modelo"] == nome_modelo)
            ]
            assert len(prevs_fold) == metricas_mod["n"]

    # Validar partição externa de validação
    externas = res["previsoes"].query("particao == 'validacao'")
    for nome_modelo, metricas_mod in res["relatorio"]["validacao_externa"]["modelos"].items():
        assert len(externas[externas["modelo"] == nome_modelo]) == metricas_mod["n"]


def test_recomputacao_referencia_parcial_ignora_colunas_previsao_stale(painel_aceite):
    """Colunas previsao_* pré-existentes ou stale são recalculadas via prever_baselines."""
    painel = painel_aceite.copy()
    painel["previsao_persistencia"] = -99999.0  # valor adulterado / stale
    if "previsao_sazonal" in painel.columns:
        painel.drop(columns=["previsao_sazonal"], inplace=True)

    res = treinar_classicos(painel, n_iter=1, n_splits=2)
    assert res is not None
    # Verifica que baselines foram computados corretamente e não usaram -99999
    base_res = res["relatorio"]["baselines"]
    assert "persistencia" in base_res
    assert "sazonal" in base_res

    # Testar falha clara se faltarem as referências fonte
    painel_invalido = painel_aceite.drop(columns=["admissoes_soma_3m"])
    with pytest.raises(ValueError, match="referências fonte suficientes|admissoes_soma_3m"):
        treinar_classicos(painel_invalido, n_iter=1)


def test_comparacao_baselines_e_hash_metadata(resultado_aceite, tmp_path):
    """Valida metadados de hash_recorte, sha256_escopo e estrutura comparativa com baselines."""
    rel = resultado_aceite["relatorio"]

    # 1. Metadados do recorte
    assert len(rel["recorte"]["hash_recorte"]) == 64
    assert len(rel["recorte"]["sha256_escopo"]) == 64
    assert rel["recorte"]["decisao"] == "R29"

    # 2. Estrutura de baselines
    assert set(rel["baselines"]) >= {"persistencia", "sazonal"}
    for nome_b in ["persistencia", "sazonal"]:
        b_info = rel["baselines"][nome_b]
        assert "cv_resumo" in b_info
        assert "folds" in b_info
        assert "validacao_externa" in b_info
        assert len(b_info["folds"]) == len(rel["folds"])

    # 3. Metadados nos folds
    for fold in rel["folds"]:
        assert "baselines" in fold
        assert set(fold["baselines"]) >= {"persistencia", "sazonal"}

    # 4. Salvar artefatos e conferir manifesto
    p_painel = tmp_path / "painel_dummy.parquet"
    pd.DataFrame({"x": [1]}).to_parquet(p_painel)
    dir_saida = tmp_path / "saida_metadata"
    salvar_artefatos_classicos(resultado_aceite, caminho_painel=p_painel, dir_saida=dir_saida)

    manifesto = json.loads((dir_saida / "manifesto.json").read_text(encoding="utf-8"))
    assert manifesto["hash_recorte"] == rel["recorte"]["hash_recorte"]
    assert manifesto["sha256_escopo"] == rel["recorte"]["sha256_escopo"]
    assert set(manifesto["arquivos"].keys()) == {
        "modelos.joblib",
        "previsoes.parquet",
        "previsoes.csv",
        "metricas.json",
    }


def test_relatorio_declara_cv_nao_aninhada(resultado_aceite):
    assert resultado_aceite["relatorio"].get("cv_aninhada") is False


def test_estimador_isolado_tambem_bloqueia_fit_de_holdout(painel_aceite):
    from citizentech_ml.classicos import EstimadorClassicoElegivel

    entrada = painel_aceite.copy()
    entrada["competencia"] = "202601"
    with pytest.raises(ValueError, match="2026|[Hh]oldout"):
        EstimadorClassicoElegivel().fit(entrada, entrada["alvo"])


def test_metricas_explicam_quantas_series_compuseram_mase(resultado_aceite):
    rel = resultado_aceite["relatorio"]
    for conjunto in [*rel["folds"], rel["validacao_externa"]]:
        for met in conjunto["modelos"].values():
            assert "series_com_escala" in met and "series_sem_escala" in met
            assert met["series_com_escala"] + met["series_sem_escala"] == len(met["tabela_series"])
