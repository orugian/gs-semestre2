"""Testes do módulo de baselines e avaliação com origem móvel."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from citizentech_ml.baselines import avaliar_baselines, prever_baselines
from citizentech_ml.features.datas import gerar_intervalo_meses


def _criar_painel_sintetico() -> pd.DataFrame:
    """Cria painel sintético com 4 séries de 202101 a 202509 (57 meses).

    Séries:
    1. (d1, SP): Constante (alvo=30, persistencia=30, sazonal=30). Persistência com MAE 0.
    2. (d2, RJ): Sazonalidade anual (alvo oscila 20/40 por mês; sazonal acerta, persistência erra).
    3. (d1, RJ): Média do alvo = 5.0 (densidade insuficiente < 10.0; excluída).
    4. (d2, SP): Média do alvo = 50.0 (elegível).
    """
    meses = gerar_intervalo_meses("202101", "202509")
    linhas = []

    for m in meses:
        mes_num = int(m[-2:])
        # (d1, SP) - constante
        linhas.append(
            {
                "competencia": m,
                "destino": "d1",
                "uf": "35",
                "alvo": 30.0,
                "admissoes_soma_3m": 30.0,
                "admissoes_sazonal_ano_anterior": 30.0,
            }
        )
        # (d2, RJ) - sazonal (período 12)
        padrao_sazonal = 20.0 if mes_num % 2 == 0 else 40.0
        linhas.append(
            {
                "competencia": m,
                "destino": "d2",
                "uf": "33",
                "alvo": padrao_sazonal,
                "admissoes_soma_3m": 30.0,  # persistência erra por 10
                "admissoes_sazonal_ano_anterior": padrao_sazonal,  # sazonal acerta exatamente
            }
        )
        # (d1, RJ) - baixa densidade (< 10)
        linhas.append(
            {
                "competencia": m,
                "destino": "d1",
                "uf": "33",
                "alvo": 5.0,
                "admissoes_soma_3m": 5.0,
                "admissoes_sazonal_ano_anterior": 5.0,
            }
        )
        # (d2, SP) - elegível com pequenos desvios
        linhas.append(
            {
                "competencia": m,
                "destino": "d2",
                "uf": "35",
                "alvo": 50.0,
                "admissoes_soma_3m": 52.0,
                "admissoes_sazonal_ano_anterior": 48.0,
            }
        )

    df = pd.DataFrame(linhas)
    return prever_baselines(df)


def test_prever_baselines_colunas() -> None:
    """Verifica se prever_baselines anexa colunas e valida campos obrigatórios."""
    df = pd.DataFrame(
        {
            "admissoes_soma_3m": [10.0, float("nan")],
            "admissoes_sazonal_ano_anterior": [float("nan"), 20.0],
        }
    )
    df_prev = prever_baselines(df)
    assert "previsao_persistencia" in df_prev.columns
    assert "previsao_sazonal" in df_prev.columns
    assert np.isnan(df_prev.loc[1, "previsao_persistencia"])
    assert np.isnan(df_prev.loc[0, "previsao_sazonal"])

    # Item 2: Erro se colunas obrigatórias não existirem
    with pytest.raises(ValueError, match="admissoes_soma_3m"):
        prever_baselines(pd.DataFrame({"admissoes_sazonal_ano_anterior": [10.0]}))
    with pytest.raises(ValueError, match="admissoes_sazonal_ano_anterior"):
        prever_baselines(pd.DataFrame({"admissoes_soma_3m": [10.0]}))



def test_avaliar_baselines_comparacao_justa_e_densidade() -> None:
    """Verifica densidade D04a, mesma quantidade n para baselines e acurácias esperadas."""
    df_painel = _criar_painel_sintetico()
    res = avaliar_baselines(df_painel, n_splits=3, limite_densidade=10.0)

    assert "folds" in res
    assert len(res["folds"]) == 3

    for fold in res["folds"]:
        # (d1, RJ) com média 5 deve ter sido excluída
        assert fold["series_excluidas_densidade"] == 1
        assert fold["series_elegiveis"] == 3

        base_pers = fold["baselines"]["persistencia"]
        base_saz = fold["baselines"]["sazonal"]

        # Comparação justa: mesmo n em ambos os baselines
        assert base_pers["n"] == base_saz["n"]
        assert base_pers["n"] > 0

    # Resumo entre folds
    resumo = res["resumo_folds"]
    assert "persistencia" in resumo
    assert "sazonal" in resumo
    assert resumo["persistencia"]["mae_media"] is not None
    assert resumo["persistencia"]["mae_desvio"] is not None


def test_avaliar_baselines_isolamento_validacao() -> None:
    """Valor absurdo na validação não altera nada com incluir_validacao=False."""
    df_painel = _criar_painel_sintetico()

    res_limpo = avaliar_baselines(df_painel, incluir_validacao=False)

    # Injeta valor absurdo na validação (202505)
    df_adulterado = df_painel.copy()
    mascara_val = df_adulterado["competencia"] == "202505"
    df_adulterado.loc[mascara_val, "alvo"] = 9999999.0
    # Mantém a previsão original para gerar erro absurdo


    res_com_adulteracao = avaliar_baselines(df_adulterado, incluir_validacao=False)

    # Nenhuma métrica dos folds pode ser alterada
    assert res_limpo["resumo_folds"] == res_com_adulteracao["resumo_folds"]
    for f1, f2 in zip(res_limpo["folds"], res_com_adulteracao["folds"], strict=True):
        assert f1["baselines"] == f2["baselines"]

    # Com incluir_validacao=True, o bloco de validação reflete a alteração
    res_val_limpo = avaliar_baselines(df_painel, incluir_validacao=True)
    res_val_adulterado = avaliar_baselines(df_adulterado, incluir_validacao=True)

    assert res_val_limpo["validacao"] is not None
    assert res_val_adulterado["validacao"] is not None
    assert (
        res_val_adulterado["validacao"]["baselines"]["persistencia"]["mae"]
        > res_val_limpo["validacao"]["baselines"]["persistencia"]["mae"]
    )


def test_avaliar_baselines_inicio_treino_e_bloqueio_teste() -> None:
    """Valida descarte de origens anteriores a inicio_treino e bloqueio >= 202601."""
    df_painel = _criar_painel_sintetico()

    # inicio_treino registrado
    res = avaliar_baselines(df_painel, inicio_treino="202201")
    assert res["inicio_treino"] == "202201"

    # Presença de competência de teste deve falhar
    df_com_teste = df_painel.copy()
    nova_linha = df_painel.iloc[0:1].copy()
    nova_linha["competencia"] = "202601"
    df_com_teste = pd.concat([df_com_teste, nova_linha], ignore_index=True)

    with pytest.raises(ValueError, match="não permite competências de teste"):
        avaliar_baselines(df_com_teste)


def test_avaliar_baselines_n_zero_retorna_none() -> None:
    """Item 1: Quando n == 0, métricas devem ser None e não 0.0 fabricado."""
    df_painel = _criar_painel_sintetico()
    # Força alvo ausente em todo o período de validação dos folds
    df_sem_alvo = df_painel.copy()
    df_sem_alvo["alvo"] = float("nan")

    res = avaliar_baselines(df_sem_alvo, n_splits=3)
    for fold in res["folds"]:
        for nome_b in ["persistencia", "sazonal"]:
            b = fold["baselines"][nome_b]
            assert b["n"] == 0
            assert b["mae"] is None
            assert b["rmse"] is None
            assert b["wape"] is None
            assert b["macro_mae"] is None
            assert b["mase"] is None

    resumo = res["resumo_folds"]
    for nome_b in ["persistencia", "sazonal"]:
        assert resumo[nome_b]["folds_validos"] == 0
        assert resumo[nome_b]["mae_media"] is None
        assert resumo[nome_b]["mae_desvio"] is None
        assert resumo[nome_b]["wape_media"] is None
        assert resumo[nome_b]["wape_desvio"] is None


def test_avaliar_baselines_mase_com_escala_parcial() -> None:
    """Item 3: MASE agregado é a média das séries com escala válida e não vira None por 1 série."""
    df_painel = _criar_painel_sintetico()
    res = avaliar_baselines(df_painel, n_splits=3)
    for fold in res["folds"]:
        b_saz = fold["baselines"]["sazonal"]
        assert "series_com_escala" in b_saz
        assert "series_sem_escala" in b_saz
        # Se houver séries com escala, mase agregado deve ser float (não None)
        if b_saz["series_com_escala"] > 0:
            assert b_saz["mase"] is not None
            assert isinstance(b_saz["mase"], float)




def test_cli_baselines(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida execução da CLI dos baselines e persistência do JSON."""
    import sys

    from citizentech_ml.baselines import main

    df_painel = _criar_painel_sintetico()
    caminho_parquet = tmp_path / "painel.parquet"
    df_painel.to_parquet(caminho_parquet, index=False)
    dir_saida = tmp_path / "saida_baselines"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "baselines",
            "--painel",
            str(caminho_parquet),
            "--saida",
            str(dir_saida),
            "--validacao",
        ],
    )
    main()

    caminho_json = dir_saida / "baselines.json"
    assert caminho_json.exists()
    conteudo = json.loads(caminho_json.read_text(encoding="utf-8"))
    assert "sha256_painel" in conteudo
    assert "data_utc" in conteudo
    assert conteudo["data_utc"].endswith("Z")
    assert "avaliacao" in conteudo
    assert conteudo["avaliacao"]["validacao"] is not None


def test_cli_baselines_escopo_mvp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida flag --escopo-mvp: projeta para MVP R29, início treino 202101 e manifesto."""
    import sys

    from citizentech_ml.baselines import main
    from citizentech_ml.recorte import DESTINOS_MVP_PADRAO

    # Painel sintético contendo os 6 destinos canônicos
    todos_destinos = [
        "analista_dados_bi",
        "analista_monitoramento_iot",
        "analista_processos",
        "gerente_projetos_produto",
        "analista_suporte_infra",
        "desenvolvedor_sistemas",
    ]
    meses = gerar_intervalo_meses("202012", "202409")
    linhas = []
    for d in todos_destinos:
        for m in meses:
            linhas.append(
                {
                    "competencia": m,
                    "destino": d,
                    "uf": "35",
                    "alvo": 30.0,
                    "admissoes_soma_3m": 30.0,
                    "admissoes_sazonal_ano_anterior": 30.0,
                }
            )
    df = prever_baselines(pd.DataFrame(linhas))
    p_painel = tmp_path / "painel_completo.parquet"
    df.to_parquet(p_painel, index=False)
    dir_saida = tmp_path / "saida_mvp"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "baselines",
            "--painel",
            str(p_painel),
            "--saida",
            str(dir_saida),
            "--escopo-mvp",
        ],
    )
    main()

    p_json = dir_saida / "baselines.json"
    assert p_json.exists()
    conteudo = json.loads(p_json.read_text(encoding="utf-8"))

    # Verifica registro explícito do escopo MVP
    assert "escopo" in conteudo
    esc = conteudo["escopo"]
    assert esc["modo"] == "mvp_r29"
    assert sorted(esc["destinos"]) == sorted(DESTINOS_MVP_PADRAO)
    assert "hash_recorte" in esc
    assert "sha256_escopo" in esc
    assert esc["inicio_treino"] == "202101"

    # Avaliação deve ter inicio_treino explícito 202101 (dados 2020 apenas histórico)
    aval = conteudo["avaliacao"]
    assert aval["inicio_treino"] == "202101"
    # Folds e densidade calculados estritamente sobre treino >= 202101 e destinos MVP
    assert len(aval["folds"]) == 3
    for fold in aval["folds"]:
        assert all(m >= "202101" for m in fold["meses_treino"])


def test_cli_baselines_rotulo_catalogo_completo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sem flag --escopo-mvp, mantém compatibilidade e rotula como catalogo_completo."""
    import sys

    from citizentech_ml.baselines import main

    df_painel = _criar_painel_sintetico()
    p_painel = tmp_path / "painel.parquet"
    df_painel.to_parquet(p_painel, index=False)
    dir_saida = tmp_path / "saida_completo"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "baselines",
            "--painel",
            str(p_painel),
            "--saida",
            str(dir_saida),
        ],
    )
    main()

    p_json = dir_saida / "baselines.json"
    assert p_json.exists()
    conteudo = json.loads(p_json.read_text(encoding="utf-8"))
    assert "escopo" in conteudo
    assert conteudo["escopo"]["modo"] == "catalogo_completo"
    # O modo sem recorte nao prova que seis destinos estejam presentes no arquivo.
    assert conteudo["escopo"]["destinos"] == ["d1", "d2"]

