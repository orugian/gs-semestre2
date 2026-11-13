"""Testes de divisão temporal, embargos e seleção por densidade (T04, T19, D10, D04a)."""

import numpy as np
import pandas as pd
import pytest

from citizentech_ml.features.datas import gerar_intervalo_meses
from citizentech_ml.features.densidade import (
    calcular_densidade_treino,
    filtrar_series_elegiveis,
    obter_series_elegiveis,
)
from citizentech_ml.split import (
    SplitOrigemMovel,
    obter_split_calendario,
)


def test_t04_split_calendario_padrao_e_embargo():
    """T04 / D10: Treino termina em 202409, embargo 202410..202412, validação 202501..202509.

    Teste sintético 202601..202606 não é retornado por padrão pelas APIs de desenvolvimento.
    """
    meses_completos = gerar_intervalo_meses("202001", "202606")
    df = pd.DataFrame({"competencia": meses_completos})

    # Padrão: desenvolvimento (apenas treino e validação)
    df_treino, df_val = obter_split_calendario(df, incluir_teste=False)

    # 1. Limites do Treino
    assert df_treino["competencia"].min() == "202001"
    assert df_treino["competencia"].max() == "202409"

    # 2. Embargo 1: 202410, 202411, 202412 NÃO estão em treino nem em validação
    meses_embargo_1 = {"202410", "202411", "202412"}
    assert set(df_treino["competencia"]).isdisjoint(meses_embargo_1)
    assert set(df_val["competencia"]).isdisjoint(meses_embargo_1)

    # 3. Limites da Validação
    assert df_val["competencia"].min() == "202501"
    assert df_val["competencia"].max() == "202509"

    # 4. Nenhum dado de teste ou embargo 2 vaza na validação
    assert (df_val["competencia"] <= "202509").all()

    # 5. Solicitação explícita do split com teste sintético
    df_treino_3, df_val_3, df_teste = obter_split_calendario(df, incluir_teste=True)
    assert len(df_treino_3) == len(df_treino)
    assert len(df_val_3) == len(df_val)

    # 6. Embargo 2: 202510, 202511, 202512 não estão em teste nem validação
    meses_embargo_2 = {"202510", "202511", "202512"}
    assert set(df_val_3["competencia"]).isdisjoint(meses_embargo_2)
    assert set(df_teste["competencia"]).isdisjoint(meses_embargo_2)

    assert df_teste["competencia"].min() == "202601"
    assert df_teste["competencia"].max() == "202606"


def test_t04_folds_origem_movel_multi_uf_desordenado_e_meses_faltantes():
    """T04: Folds multi-UF com datas desordenadas/ausentes respeitam embargo de 3 meses reais

    e nunca incluem origens fora do treino (<= 202409).
    """
    # Cria painel sintético com 2 destinos e 3 UFs, de 202101 a 202409
    meses = gerar_intervalo_meses("202101", "202409")
    # Simula meses faltantes no painel: remove 202305 e 202306
    meses_com_falha = [m for m in meses if m not in {"202305", "202306"}]

    linhas = []
    for m in meses_com_falha:
        for dest in ["analista_dados_bi", "desenvolvedor_sistemas"]:
            for uf in ["35", "33", "31"]:
                linhas.append({"competencia": m, "destino": dest, "uf": uf})

    df = pd.DataFrame(linhas)

    # Embaralhar completamente a ordem das linhas
    np.random.seed(42)
    df_embaralhado = df.sample(frac=1.0, random_state=42).reset_index(drop=True)

    splitter = SplitOrigemMovel(
        n_splits=3,
        tamanho_validacao_meses=3,
        meses_embargo=3,
        tamanho_minimo_treino_meses=12,
        coluna_tempo="competencia",
        limite_treino_maximo="202409",
    )

    splits = list(splitter.split(df_embaralhado))
    assert len(splits) == 3

    for fold_idx, (idx_treino, idx_val) in enumerate(splits):
        treino_fold = df_embaralhado.iloc[idx_treino]
        val_fold = df_embaralhado.iloc[idx_val]

        # 1. Nenhum índice sobreposto
        assert len(set(idx_treino).intersection(set(idx_val))) == 0

        # 2. Treino e validação não podem estar vazios
        assert not treino_fold.empty
        assert not val_fold.empty

        max_treino = treino_fold["competencia"].max()
        min_val = val_fold["competencia"].min()
        max_val = val_fold["competencia"].max()

        # 3. Origem não ultrapassa o limite máximo de treino (202409)
        assert max_val <= "202409"
        assert max_treino <= "202409"

        # 4. Embargo de pelo menos 3 meses reais de calendário entre max_treino e min_val
        # Ex: se min_val for 202407, os meses 202406, 202405, 202404 são embargo.
        # Logo, max_treino DEVE ser <= 202403!
        ano_val, mes_val = int(min_val[:4]), int(min_val[4:])
        val_idx_int = ano_val * 12 + (mes_val - 1)

        ano_tr, mes_tr = int(max_treino[:4]), int(max_treino[4:])
        tr_idx_int = ano_tr * 12 + (mes_tr - 1)

        diferenca_meses_calendario = val_idx_int - tr_idx_int
        # A diferença em meses inteiros deve ser > 3 (ou seja, pelo menos 4 meses de intervalo)
        assert diferenca_meses_calendario >= 4, (
            f"Fold {fold_idx}: Embargo violado! max_treino={max_treino}, min_val={min_val}, "
            f"diferença={diferenca_meses_calendario} meses"
        )


def test_t19_densidade_limite_10_inclusive_e_isolamento_treino():
    """T19: Médias 9.99 (excluída) e 10.0 (elegível inclusive).

    Outlier enorme na validação não altera a seleção do treino.
    """
    # Série 1: analista_dados_bi em SP tem média 9.99 no treino
    # Série 2: desenvolvedor_sistemas em SP tem média 10.0 no treino (inclusive!)
    # Série 3: analista_monitoramento_iot em SP tem média 5.0 no treino
    dados_treino = [
        # Série 1: média (9.98 + 10.0) / 2 = 9.99
        {"destino": "analista_dados_bi", "uf": "35", "alvo": 9.98, "competencia": "202401"},
        {"destino": "analista_dados_bi", "uf": "35", "alvo": 10.0, "competencia": "202402"},
        # Série 2: média (10.0 + 10.0) / 2 = 10.0
        {"destino": "desenvolvedor_sistemas", "uf": "35", "alvo": 10.0, "competencia": "202401"},
        {"destino": "desenvolvedor_sistemas", "uf": "35", "alvo": 10.0, "competencia": "202402"},
        # Série 3: média 5.0
        {"destino": "analista_monitoramento_iot", "uf": "35", "alvo": 5.0, "competencia": "202401"},
        {"destino": "analista_monitoramento_iot", "uf": "35", "alvo": 5.0, "competencia": "202402"},
    ]
    df_treino = pd.DataFrame(dados_treino)

    relatorio = calcular_densidade_treino(df_treino, limite_minimo=10.0, coluna_alvo="alvo")
    series_ok = obter_series_elegiveis(relatorio)

    # 1. Limite 10.0 inclusive
    assert ("desenvolvedor_sistemas", "35") in series_ok
    # 2. 9.99 é rejeitado
    assert ("analista_dados_bi", "35") not in series_ok
    assert ("analista_monitoramento_iot", "35") not in series_ok

    # Motivos
    r_dev = relatorio[relatorio["destino"] == "desenvolvedor_sistemas"].iloc[0]
    assert bool(r_dev["elegivel"]) is True
    assert r_dev["motivo"] == "aprovado"

    r_bi = relatorio[relatorio["destino"] == "analista_dados_bi"].iloc[0]
    assert bool(r_bi["elegivel"]) is False
    assert r_bi["motivo"] == "densidade_insuficiente"

    # 3. Outlier enorme na validação NÃO altera seleção do treino
    dados_val = [
        # Outlier gigante de 1.000.000 na validação para a série de BI
        {"destino": "analista_dados_bi", "uf": "35", "alvo": 1_000_000.0, "competencia": "202501"},
    ]
    df_val = pd.DataFrame(dados_val)

    # Se a seleção consultar somente o treino, BI continua excluída
    relatorio_apenas_treino = calcular_densidade_treino(
        df_treino, limite_minimo=10.0, coluna_alvo="alvo"
    )
    series_treino = obter_series_elegiveis(relatorio_apenas_treino)
    assert ("analista_dados_bi", "35") not in series_treino

    # Aplicação do filtro na validação usando as séries elegíveis do treino
    df_val_filtrado = filtrar_series_elegiveis(df_val, series_treino)
    # A série de BI (mesmo com 1M no alvo de validação) foi expurgada da avaliação!
    assert df_val_filtrado.empty


def test_t19_por_fold_recalcula_elegibilidade_sem_vazar_treino_completo():
    """Por fold, a densidade é recalculada exclusivamente no treino daquele fold."""
    # Série que tem média baixa nos primeiros anos, mas cresce no final do treino
    dados = [
        # Fold 1 treino: média = 4.0 (< 10)
        {"destino": "analista_dados_bi", "uf": "35", "alvo": 4.0, "competencia": "202201"},
        {"destino": "analista_dados_bi", "uf": "35", "alvo": 4.0, "competencia": "202202"},
        # Fold 2 treino adicional: alvos altos elevam a média total
        {"destino": "analista_dados_bi", "uf": "35", "alvo": 30.0, "competencia": "202401"},
        {"destino": "analista_dados_bi", "uf": "35", "alvo": 30.0, "competencia": "202402"},
    ]
    df = pd.DataFrame(dados)

    # No slice do Fold 1 (apenas 2022)
    df_fold1_tr = df[df["competencia"] <= "202202"]
    rel_fold1 = calcular_densidade_treino(df_fold1_tr, limite_minimo=10.0)
    assert ("analista_dados_bi", "35") not in obter_series_elegiveis(rel_fold1)

    # No slice do Fold 2 (2022 + 2024)
    rel_fold2 = calcular_densidade_treino(df, limite_minimo=10.0)
    # Média total = (4 + 4 + 30 + 30)/4 = 17.0 >= 10.0
    assert ("analista_dados_bi", "35") in obter_series_elegiveis(rel_fold2)


def test_splitter_origem_movel_get_n_splits_e_erros():
    """Valida get_n_splits e levantamento de erro quando dados forem insuficientes."""
    splitter = SplitOrigemMovel(n_splits=3, tamanho_validacao_meses=3, meses_embargo=3)
    assert splitter.get_n_splits() == 3

    # Dataset com apenas 5 meses: impossível gerar 3 folds com embargo de 3 meses e treino min 12
    df_pequeno = pd.DataFrame({"competencia": ["202401", "202402", "202403", "202404", "202405"]})
    with pytest.raises(ValueError, match="Dados insuficientes para gerar 3 splits"):
        list(splitter.split(df_pequeno))


def test_split_origem_movel_regras_congeladas_d10():
    """Valida que SplitOrigemMovel bloqueia embargo < 3 e limite_treino_maximo > 202409."""
    # 1. Rejeita embargo < 3
    with pytest.raises(ValueError, match="meses_embargo deve ser >= 3"):
        SplitOrigemMovel(meses_embargo=2)

    # 2. Rejeita limite de treino posterior a 202409
    with pytest.raises(ValueError, match="não pode ser posterior a 202409"):
        SplitOrigemMovel(limite_treino_maximo="202501")

    # 3. Rejeita tipos não inteiros (float e bool)
    with pytest.raises(TypeError):
        SplitOrigemMovel(n_splits=3.0)  # float

    with pytest.raises(TypeError):
        SplitOrigemMovel(n_splits=True)  # bool


def test_densidade_treino_validacao_estrita_alvo_e_corte():
    """calcular_densidade_treino rejeita alvos não finitos/negativos e dados pós-treino."""
    # 1. Alvo negativo
    df_neg = pd.DataFrame([
        {"destino": "analista_dados_bi", "uf": "35", "alvo": -5.0},
    ])
    with pytest.raises(ValueError, match="não finitos ou negativos"):
        calcular_densidade_treino(df_neg)

    # 2. Alvo infinito
    df_inf = pd.DataFrame([
        {"destino": "analista_dados_bi", "uf": "35", "alvo": float("inf")},
    ])
    with pytest.raises(ValueError, match="não finitos ou negativos"):
        calcular_densidade_treino(df_inf)

    # 3. Competência de validação (202501) passada acidentalmente
    df_vazamento = pd.DataFrame([
        {"destino": "analista_dados_bi", "uf": "35", "alvo": 15.0, "competencia": "202501"},
    ])
    with pytest.raises(ValueError, match="posterior ao limite de treino"):
        calcular_densidade_treino(df_vazamento, limite_competencia_treino="202409")


