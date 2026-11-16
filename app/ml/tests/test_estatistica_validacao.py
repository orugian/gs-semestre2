"""Testes de validação de dados para análises estatísticas municipais."""

import pandas as pd
import pytest

from citizentech_ml.estatistica.validacao import validar_base_municipal


def test_validar_base_municipal_gera_participacao_e_alvo_preserva_input():
    df_raw = pd.DataFrame(
        {
            "municipio": ["Campinas", "Santos"],
            "uf": ["SP", "SP"],
            "admissoes_2024": [100, 50],
            "admissoes_2025": [120, 40],
            "salario_medio_2024": [3500.0, 2800.0],
            "percentual_superior_2024": [25.0, 18.0],
            "total_municipal_2024": [1000, 500],
        }
    )
    df_copia_original = df_raw.copy()

    df_validado = validar_base_municipal(df_raw)

    # Imutabilidade do input
    pd.testing.assert_frame_equal(df_raw, df_copia_original)

    # Colunas adicionadas
    assert "participacao_2024" in df_validado.columns
    assert "crescimento" in df_validado.columns
    assert df_validado["participacao_2024"].tolist() == [10.0, 10.0]
    assert df_validado["crescimento"].tolist() == [1, 0]


def test_validar_base_municipal_aceita_ausencia_de_total_municipal():
    """Valida que base sem total_municipal_2024 é aceita sem denominador sintético."""
    df = pd.DataFrame(
        {
            "municipio": ["Campinas"],
            "uf": ["SP"],
            "admissoes_2024": [100],
            "admissoes_2025": [120],
            "salario_medio_2024": [3500.0],
            "percentual_superior_2024": [25.0],
        }
    )
    df_val = validar_base_municipal(df)
    assert "crescimento" in df_val.columns
    assert df_val["crescimento"].tolist() == [1]
    assert "total_municipal_2024" not in df_val.columns
    assert "participacao_2024" not in df_val.columns


def test_validar_base_municipal_rejeita_duplicatas_de_municipio():
    df = pd.DataFrame(
        {
            "municipio": ["Campinas", "Campinas"],
            "uf": ["SP", "SP"],
            "admissoes_2024": [100, 100],
            "admissoes_2025": [120, 120],
            "salario_medio_2024": [3500.0, 3500.0],
            "percentual_superior_2024": [25.0, 25.0],
            "total_municipal_2024": [1000, 1000],
        }
    )
    with pytest.raises(ValueError, match="duplicados"):
        validar_base_municipal(df)


def test_validar_base_municipal_rejeita_uf_fora_de_sp():
    df = pd.DataFrame(
        {
            "municipio": ["Niterói"],
            "uf": ["RJ"],
            "admissoes_2024": [100],
            "admissoes_2025": [120],
            "salario_medio_2024": [3500.0],
            "percentual_superior_2024": [25.0],
            "total_municipal_2024": [1000],
        }
    )
    with pytest.raises(ValueError, match="São Paulo"):
        validar_base_municipal(df)


def test_validar_base_municipal_rejeita_total_menor_que_admissoes():
    df = pd.DataFrame(
        {
            "municipio": ["Campinas"],
            "uf": ["SP"],
            "admissoes_2024": [100],
            "admissoes_2025": [120],
            "salario_medio_2024": [3500.0],
            "percentual_superior_2024": [25.0],
            "total_municipal_2024": [50],  # Menor que 100
        }
    )
    with pytest.raises(ValueError, match="denominador municipal indevido"):
        validar_base_municipal(df)


def test_validar_base_municipal_rejeita_valores_invalidos():
    base_padrao = {
        "municipio": ["Campinas"],
        "uf": ["SP"],
        "admissoes_2024": [100],
        "admissoes_2025": [120],
        "salario_medio_2024": [3500.0],
        "percentual_superior_2024": [25.0],
        "total_municipal_2024": [1000],
    }

    # Salário <= 0
    df_sal = pd.DataFrame({**base_padrao, "salario_medio_2024": [0.0]})
    with pytest.raises(ValueError, match="salario_medio_2024 deve ser estritamente positivo"):
        validar_base_municipal(df_sal)

    # Percentual > 100
    df_perc = pd.DataFrame({**base_padrao, "percentual_superior_2024": [105.0]})
    with pytest.raises(ValueError, match="percentual_superior_2024"):
        validar_base_municipal(df_perc)

    # NaN em coluna obrigatória
    df_nan = pd.DataFrame({**base_padrao, "admissoes_2024": [None]})
    with pytest.raises(ValueError, match="dados ausentes"):
        validar_base_municipal(df_nan)


def test_validar_base_municipal_nao_filtra_populacao_pequena():
    # Não filtrar população < 10 silenciosamente
    df = pd.DataFrame(
        {
            "municipio": ["Pequena Cidade"],
            "uf": ["SP"],
            "admissoes_2024": [2],
            "admissoes_2025": [3],
            "salario_medio_2024": [2000.0],
            "percentual_superior_2024": [5.0],
            "total_municipal_2024": [5],
        }
    )
    df_val = validar_base_municipal(df)
    assert len(df_val) == 1


def test_validar_base_municipal_rejeita_identificador_municipal_nulo_ou_vazio():
    base_padrao = {
        "uf": ["SP"],
        "admissoes_2024": [100],
        "admissoes_2025": [120],
        "salario_medio_2024": [3500.0],
        "percentual_superior_2024": [25.0],
    }

    # String vazia
    with pytest.raises(ValueError, match="Identificador municipal nulo ou vazio"):
        validar_base_municipal(pd.DataFrame({**base_padrao, "municipio": [""]}))

    # Espaços em branco
    with pytest.raises(ValueError, match="Identificador municipal nulo ou vazio"):
        validar_base_municipal(pd.DataFrame({**base_padrao, "municipio": ["   "]}))

    # None / NaN
    with pytest.raises(ValueError, match="Identificador municipal nulo ou vazio"):
        validar_base_municipal(pd.DataFrame({**base_padrao, "municipio": [None]}))


def test_validar_base_municipal_rejeita_booleanos():
    base_padrao = {
        "municipio": ["Campinas"],
        "uf": ["SP"],
        "admissoes_2024": [100],
        "admissoes_2025": [120],
        "salario_medio_2024": [3500.0],
        "percentual_superior_2024": [25.0],
    }

    # Bool em admissoes_2024 (não pode converter True em 1)
    with pytest.raises(ValueError, match="não pode conter valores booleanos"):
        validar_base_municipal(pd.DataFrame({**base_padrao, "admissoes_2024": [True]}))

    # Bool em admissoes_2025
    with pytest.raises(ValueError, match="não pode conter valores booleanos"):
        validar_base_municipal(pd.DataFrame({**base_padrao, "admissoes_2025": [False]}))

    # Bool em salario_medio_2024
    with pytest.raises(ValueError, match="não pode conter valores booleanos"):
        validar_base_municipal(pd.DataFrame({**base_padrao, "salario_medio_2024": [True]}))

    # Bool em percentual_superior_2024
    with pytest.raises(ValueError, match="não pode conter valores booleanos"):
        validar_base_municipal(pd.DataFrame({**base_padrao, "percentual_superior_2024": [True]}))

    # Bool em total_municipal_2024
    with pytest.raises(ValueError, match="não pode conter valores booleanos"):
        validar_base_municipal(pd.DataFrame({**base_padrao, "total_municipal_2024": [True]}))


def test_validar_base_municipal_rejeita_admissoes_fracionarias():
    base_padrao = {
        "municipio": ["Campinas"],
        "uf": ["SP"],
        "admissoes_2024": [100],
        "admissoes_2025": [120],
        "salario_medio_2024": [3500.0],
        "percentual_superior_2024": [25.0],
    }

    # Admissão 2024 fracionária
    with pytest.raises(ValueError, match="contagens.*inteiras"):
        validar_base_municipal(pd.DataFrame({**base_padrao, "admissoes_2024": [100.5]}))

    # Admissão 2025 fracionária
    with pytest.raises(ValueError, match="contagens.*inteiras"):
        validar_base_municipal(pd.DataFrame({**base_padrao, "admissoes_2025": [120.3]}))

    # Total municipal fracionário
    with pytest.raises(ValueError, match="total_municipal_2024.*contagens inteiras"):
        validar_base_municipal(pd.DataFrame({**base_padrao, "total_municipal_2024": [1000.7]}))


def test_validar_base_municipal_aceita_salario_fracionario_e_percentual_decimal():
    # Salários são contínuos (podem ser fracionários); percentuais admitem casas decimais
    df = pd.DataFrame(
        {
            "municipio": ["Campinas", "Santos"],
            "uf": ["SP", "SP"],
            "admissoes_2024": [100, 50],
            "admissoes_2025": [120, 60],
            "salario_medio_2024": [3542.87, 2891.43],
            "percentual_superior_2024": [25.75, 18.25],
        }
    )
    df_val = validar_base_municipal(df)
    assert df_val["salario_medio_2024"].tolist() == pytest.approx([3542.87, 2891.43])
    assert df_val["percentual_superior_2024"].tolist() == pytest.approx([25.75, 18.25])
    assert df_val["crescimento"].tolist() == [1, 1]


def test_validar_base_municipal_rejeita_contagens_negativas():
    base_padrao = {
        "municipio": ["Campinas"],
        "uf": ["SP"],
        "salario_medio_2024": [3500.0],
        "percentual_superior_2024": [25.0],
    }
    with pytest.raises(ValueError, match="admissoes_2024 não pode conter valores negativos"):
        df_neg_24 = pd.DataFrame({**base_padrao, "admissoes_2024": [-5], "admissoes_2025": [10]})
        validar_base_municipal(df_neg_24)

    with pytest.raises(ValueError, match="admissoes_2025 não pode conter valores negativos"):
        df_neg_25 = pd.DataFrame({**base_padrao, "admissoes_2024": [10], "admissoes_2025": [-2]})
        validar_base_municipal(df_neg_25)
