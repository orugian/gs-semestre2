"""Aceite independente S7: dados exclusivamente sinteticos."""
import pandas as pd
import pytest

from citizentech_ml.features import construir_painel_features
from citizentech_ml.split import SplitOrigemMovel


def cobertura():
    return pd.DataFrame([
        {"competencia": m, "tipo": t, "situacao": "ingerido"}
        for m in ["202401", "202402", "202403", "202404"]
        for t in ["MOV", "FOR", "EXC"]
    ])


def linha():
    return dict(competencia_mov="202401", competencia_dec="202401",
                competencia_arquivo="202401", arquivo_tipo="MOV", saldo_movimentacao=1,
                cbo2002_ocupacao="211205", uf="35", grau_instrucao=9)


@pytest.mark.parametrize("situacao", [None, "nao_promovida", "desconhecida"])
def test_cobertura_for_incompleta_nao_produz_contagem(situacao):
    c = cobertura()
    mascara = (c.competencia == "202401") & (c.tipo == "FOR")
    if situacao is None:
        c = c[~mascara]
    else:
        c.loc[mascara, "situacao"] = situacao
    p = construir_painel_features(pd.DataFrame([linha()]), c,
                                 competencias=["202401"], ufs=["35"], calcular_alvo=False)
    assert pd.isna(p.loc[p.destino == "analista_dados_bi", "admissoes"].iloc[0])


def test_revisao_pendente_posterior_nao_produz_passado_completo():
    c = cobertura()
    c.loc[(c.competencia == "202404") & (c.tipo == "FOR"), "situacao"] = "pendente"
    p = construir_painel_features(pd.DataFrame([linha()]), c,
                                 competencias=["202404"], ufs=["35"], calcular_alvo=False)
    assert pd.isna(p.loc[p.destino == "analista_dados_bi", "admissoes_lag_3"].iloc[0])


@pytest.mark.parametrize("campo,valor", [("saldo_movimentacao", None),
                                       ("saldo_movimentacao", 1.9),
                                       ("uf", "99"), ("grau_instrucao", None)])
def test_dado_invalido_nao_vira_zero_ou_outra_populacao(campo, valor):
    r = linha()
    r[campo] = valor
    with pytest.raises(ValueError):
        construir_painel_features(pd.DataFrame([r]), cobertura(),
                                 competencias=["202401"], ufs=["35"], calcular_alvo=False)


def test_catalogo_sobreposto_nao_atribui_silenciosamente():
    catalogo = {"destinos": {"a": {"cbo6": ["211205"]}, "b": {"cbo6": ["211205"]}}}
    with pytest.raises(ValueError):
        construir_painel_features(pd.DataFrame([linha()]), cobertura(), ocupacoes=catalogo,
                                 competencias=["202401"], ufs=["35"], calcular_alvo=False)


def test_fold_vazio_nao_e_devolvido():
    meses = [f"2023{m:02d}" for m in range(1, 13)] + ["202401", "202409"]
    splitter = SplitOrigemMovel(n_splits=2, tamanho_minimo_treino_meses=3)
    try:
        folds = list(splitter.split(pd.DataFrame({"competencia": meses})))
    except ValueError:
        return
    assert all(len(treino) and len(validacao) for treino, validacao in folds)


def test_competencia_com_espacos_aceita_nao_perde_movimentacao():
    r = linha()
    r["competencia_mov"] = " 202401 "
    p = construir_painel_features(pd.DataFrame([r]), cobertura(),
                                 competencias=["202401"], ufs=["35"], calcular_alvo=False)
    assert p.loc[p.destino == "analista_dados_bi", "admissoes"].iloc[0] == 1.0


def test_pendencia_futura_no_manifesto_nao_anula_alvo_historico():
    """RV-S7-01: linha pendente em mes futuro do manifesto nao pode anular alvo ja observado."""
    c = pd.concat(
        [cobertura(), pd.DataFrame([
            {"competencia": "202501", "tipo": "FOR", "situacao": "pendente"},
        ])],
        ignore_index=True,
    )
    dados = [
        linha() | {"competencia_mov": m, "competencia_dec": m, "competencia_arquivo": m}
        for m in ["202402", "202403", "202404"]
    ]
    p = construir_painel_features(pd.DataFrame(dados), c, competencias=["202401"], ufs=["35"])
    assert p.loc[p.destino == "analista_dados_bi", "alvo"].iloc[0] == 3.0


def test_competencias_do_manifesto_sao_validadas_quando_omitidas():
    """RV-S7-02: competencias vindas da cobertura passam pela mesma validacao das explicitas."""
    c = cobertura()
    c["competencia"] = " " + c["competencia"] + " "
    p = construir_painel_features(pd.DataFrame([linha()]), c, ufs=["35"], calcular_alvo=False)
    assert set(p["mes"]) == {1, 2, 3, 4}
    assert set(p["competencia"]) == {"202401", "202402", "202403", "202404"}


def test_pre_agregado_nao_silencia_catalogo_sobreposto():
    from citizentech_ml.features import pre_agregar_microdados

    pre = pre_agregar_microdados(pd.DataFrame([linha()]))
    catalogo = {"destinos": {"a": {"cbo6": ["211205"]}, "b": {"cbo6": ["211205"]}}}
    with pytest.raises(ValueError, match="múltiplos destinos"):
        construir_painel_features(pre, cobertura(), ocupacoes=catalogo,
                                 competencias=["202401"], calcular_alvo=False)
