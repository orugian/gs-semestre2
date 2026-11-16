"""Testes para o programa portátil de análise estatística municipal."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from citizentech_ml.estatistica import (
    ajustar_logistica_municipal,
    ajustar_ols_multipla,
    ajustar_ols_simples,
    probabilidades_normais,
    testes_medias_enunciado,
)
from citizentech_ml.estatistica.analise_portatil import (
    FIGURAS_PADRAO,
    executar_analise,
)


@pytest.fixture
def caminho_base_sintetica_40(tmp_path: Path) -> Path:
    """Gera uma base sintética de 40 municípios (rotulada como sintética) em tmp_path."""
    rng = np.random.default_rng(20261116)
    n = 40
    salario = 2500.0 + rng.uniform(500.0, 5000.0, size=n)
    percentual = rng.uniform(15.0, 85.0, size=n)

    crescimento = np.zeros(n, dtype=int)
    crescimento[:20] = 0
    crescimento[20:] = 1
    rng.shuffle(crescimento)

    admissoes_2024 = rng.integers(20, 200, size=n)
    admissoes_2025 = np.zeros(n, dtype=int)
    for i in range(n):
        if crescimento[i] == 1:
            admissoes_2025[i] = admissoes_2024[i] + int(rng.integers(1, 50))
        else:
            admissoes_2025[i] = max(0, admissoes_2024[i] - int(rng.integers(1, 15)))

    df = pd.DataFrame(
        {
            "municipio": [f"35{i:04d}" for i in range(n)],
            "uf": "35",
            "admissoes_2024": admissoes_2024,
            "admissoes_2025": admissoes_2025,
            "salario_medio_2024": salario,
            "percentual_superior_2024": percentual,
            "crescimento": crescimento,
        }
    )
    caminho = tmp_path / "base_sintetica_40_municipios.csv"
    df.to_csv(caminho, index=False, encoding="utf-8")
    return caminho


def test_programa_portatil_reproduz_resultados_da_biblioteca_em_fixture(
    caminho_base_sintetica_40: Path,
) -> None:
    """RED -> GREEN: Valida que analise_portatil reproduz os resultados de citizentech_ml."""
    df = pd.read_csv(caminho_base_sintetica_40, encoding="utf-8")

    # Executa análise portátil
    res_portatil = executar_analise(caminho_base_sintetica_40)

    # Resultados esperados via biblioteca interna
    esp_q02 = probabilidades_normais(df["admissoes_2025"])
    esp_q03 = testes_medias_enunciado(df["admissoes_2025"], seeds=(42, 43))

    mediana_sal = float(df["salario_medio_2024"].median())
    mediana_sup = float(df["percentual_superior_2024"].median())

    esp_q04 = ajustar_ols_simples(
        df[["salario_medio_2024"]],
        df["admissoes_2025"],
        ponto_previsao=mediana_sal,
    )
    esp_q05 = ajustar_ols_multipla(
        df[["salario_medio_2024", "percentual_superior_2024"]],
        df["admissoes_2025"],
        ponto_previsao={
            "salario_medio_2024": mediana_sal,
            "percentual_superior_2024": mediana_sup,
        },
    )
    esp_q06 = ajustar_logistica_municipal(
        df,
        ponto_previsao={
            "salario_medio_2024": mediana_sal,
            "percentual_superior_2024": mediana_sup,
        },
        seed=44,
    )

    # Asserções Q02
    assert res_portatil["q02"] is not None
    q02 = res_portatil["q02"]
    assert q02["media"] == pytest.approx(esp_q02["media"], rel=1e-9)
    assert q02["mediana"] == pytest.approx(esp_q02["mediana"], rel=1e-9)
    assert q02["sigma_populacional"] == pytest.approx(esp_q02["sigma_populacional"], rel=1e-9)
    assert q02["probabilidade_menor_media"] == pytest.approx(
        esp_q02["probabilidade_menor_media"], rel=1e-9
    )
    assert q02["probabilidade_maior_mediana"] == pytest.approx(
        esp_q02["probabilidade_maior_mediana"], rel=1e-9
    )
    assert q02["classificacao_menor_media"] == esp_q02["classificacao_menor_media"]
    assert q02["classificacao_maior_mediana"] == esp_q02["classificacao_maior_mediana"]

    # Asserções Q03
    assert res_portatil["q03"] is not None
    q03 = res_portatil["q03"]
    assert q03["mu_ref"] == pytest.approx(esp_q03["mu_ref"], rel=1e-9)
    assert q03["sigma_ref"] == pytest.approx(esp_q03["sigma_ref"], rel=1e-9)
    for teste_key in ["teste_menor", "teste_maior"]:
        assert q03[teste_key]["media_amostral"] == pytest.approx(
            esp_q03[teste_key]["media_amostral"], rel=1e-9
        )
        assert q03[teste_key]["estatistica_z"] == pytest.approx(
            esp_q03[teste_key]["estatistica_z"], rel=1e-9
        )
        assert q03[teste_key]["p_valor"] == pytest.approx(
            esp_q03[teste_key]["p_valor"], rel=1e-9
        )
        assert q03[teste_key]["rejeita_h0"] == esp_q03[teste_key]["rejeita_h0"]

    # Asserções Q04
    assert res_portatil["q04"] is not None
    q04 = res_portatil["q04"]
    assert q04["intercepto"] == pytest.approx(esp_q04["intercepto"], rel=1e-9)
    assert q04["coeficiente_angular"] == pytest.approx(esp_q04["coeficiente_angular"], rel=1e-9)
    assert q04["r2"] == pytest.approx(esp_q04["r2"], rel=1e-9)
    assert q04["estatistica_f"] == pytest.approx(esp_q04["estatistica_f"], rel=1e-9)
    assert q04["p_f"] == pytest.approx(esp_q04["p_f"], rel=1e-9)
    assert q04["covariancia"] == pytest.approx(esp_q04["covariancia"], rel=1e-9)
    assert q04["correlacao_pearson"] == pytest.approx(esp_q04["correlacao_pearson"], rel=1e-9)
    assert q04["previsao"] == pytest.approx(esp_q04["previsao"], rel=1e-9)

    # Asserções Q05
    assert res_portatil["q05"] is not None
    q05 = res_portatil["q05"]
    assert q05["intercepto"] == pytest.approx(esp_q05["intercepto"], rel=1e-9)
    for col in ["salario_medio_2024", "percentual_superior_2024"]:
        assert q05["coeficientes"][col] == pytest.approx(esp_q05["coeficientes"][col], rel=1e-9)
    assert q05["r2"] == pytest.approx(esp_q05["r2"], rel=1e-9)
    assert q05["estatistica_f"] == pytest.approx(esp_q05["estatistica_f"], rel=1e-9)
    assert q05["p_f"] == pytest.approx(esp_q05["p_f"], rel=1e-9)
    assert q05["previsao"] == pytest.approx(esp_q05["previsao"], rel=1e-9)

    # Asserções Q06
    assert res_portatil["q06"] is not None
    q06 = res_portatil["q06"]
    for col in ["const", "salario_medio_2024", "percentual_superior_2024"]:
        assert q06["coeficientes"][col] == pytest.approx(esp_q06["coeficientes"][col], rel=1e-9)
    assert (
        q06["avaliacao_teste"]["matriz_confusao"]
        == esp_q06["avaliacao_teste"]["matriz_confusao"]
    )
    assert q06["avaliacao_teste"]["acuracia"] == pytest.approx(
        esp_q06["avaliacao_teste"]["acuracia"], rel=1e-9
    )
    assert q06["previsao_ponto"]["probabilidade"] == pytest.approx(
        esp_q06["previsao_ponto"]["probabilidade"], rel=1e-9
    )
    assert q06["previsao_ponto"]["classe"] == esp_q06["previsao_ponto"]["classe"]


def test_analise_portatil_nao_importa_citizentech_ml_via_ast() -> None:
    """Garante que analise_portatil é totalmente autônomo e não importa citizentech_ml."""
    caminho_script = (
        Path(__file__).resolve().parent.parent
        / "src"
        / "citizentech_ml"
        / "estatistica"
        / "analise_portatil.py"
    )
    conteudo = caminho_script.read_text(encoding="utf-8")
    tree = ast.parse(conteudo, filename=str(caminho_script))

    modulos_importados = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modulos_importados.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modulos_importados.append(node.module)

    for mod in modulos_importados:
        assert not mod.startswith("citizentech_ml"), (
            f"O script portátil não pode importar 'citizentech_ml'. Encontrado: {mod}"
        )


def test_execucao_como_script_subprocess_grava_figuras_e_json(
    caminho_base_sintetica_40: Path,
    tmp_path: Path,
) -> None:
    """Executa o script via subprocess com sys.executable e valida retorno 0, 8 figuras e JSON."""
    caminho_script = (
        Path(__file__).resolve().parent.parent
        / "src"
        / "citizentech_ml"
        / "estatistica"
        / "analise_portatil.py"
    )
    pasta_figuras = tmp_path / "minhas_figuras"
    arquivo_json = tmp_path / "saida_teste.json"

    cmd = [
        sys.executable,
        str(caminho_script),
        str(caminho_base_sintetica_40),
        "--figuras",
        str(pasta_figuras),
        "--json",
        str(arquivo_json),
    ]

    resultado = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert resultado.returncode == 0, f"Script falhou com saída de erro:\n{resultado.stderr}"
    assert "RELATÓRIO ESTATÍSTICO MUNICIPAL" in resultado.stdout
    assert "QUESTÃO 02" in resultado.stdout
    assert "QUESTÃO 06" in resultado.stdout
    assert "PONTOS EXTREMOS" in resultado.stdout

    # Valida presença das 8 figuras geradas
    for nome_fig in FIGURAS_PADRAO:
        caminho_fig = pasta_figuras / nome_fig
        assert caminho_fig.is_file(), f"Figura obrigatória não gerada: {nome_fig}"
        assert caminho_fig.stat().st_size > 1000, f"Figura gerada corrompida/vazia: {nome_fig}"

    # Valida arquivo JSON
    assert arquivo_json.is_file(), "Arquivo JSON não foi gravado."
    conteudo_json = arquivo_json.read_text(encoding="utf-8")
    dados = json.loads(conteudo_json)
    for chave in [
        "base",
        "q02",
        "q03",
        "q04",
        "q05",
        "q06",
        "diagnostico",
        "figuras",
        "limites",
        "pontos_extremos_salario",
    ]:
        assert chave in dados, f"Chave ausente no JSON: {chave}"
    assert len(dados["figuras"]) == 8


def test_coluna_obrigatoria_ausente_gera_erro_e_saida_nao_zero(
    caminho_base_sintetica_40: Path,
    tmp_path: Path,
) -> None:
    """Valida erro claro quando uma coluna obrigatória estiver ausente."""
    caminho_script = (
        Path(__file__).resolve().parent.parent
        / "src"
        / "citizentech_ml"
        / "estatistica"
        / "analise_portatil.py"
    )
    df = pd.read_csv(caminho_base_sintetica_40, encoding="utf-8")
    df_invalido = df.drop(columns=["salario_medio_2024"])
    caminho_invalido = tmp_path / "base_sem_salario.csv"
    df_invalido.to_csv(caminho_invalido, index=False, encoding="utf-8")

    # Chamada direta via Python
    with pytest.raises(ValueError, match="Colunas obrigatórias ausentes.*salario_medio_2024"):
        executar_analise(caminho_invalido)

    # Chamada via subprocess
    res = subprocess.run(
        [sys.executable, str(caminho_script), str(caminho_invalido)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert res.returncode != 0
    assert "Colunas obrigatórias ausentes" in res.stderr


def test_nan_em_variavel_usada_gera_erro(
    caminho_base_sintetica_40: Path,
    tmp_path: Path,
) -> None:
    """Valida erro claro ao conter valor NaN em coluna usada."""
    df = pd.read_csv(caminho_base_sintetica_40, encoding="utf-8")
    df.loc[3, "percentual_superior_2024"] = np.nan
    caminho_nan = tmp_path / "base_com_nan.csv"
    df.to_csv(caminho_nan, index=False, encoding="utf-8")

    with pytest.raises(ValueError, match="percentual_superior_2024.*valores ausentes"):
        executar_analise(caminho_nan)


def test_crescimento_divergente_do_recalculado_gera_erro(
    caminho_base_sintetica_40: Path,
    tmp_path: Path,
) -> None:
    """Valida erro se o alvo 'crescimento' divergir de (admissoes_2025 > admissoes_2024)."""
    df = pd.read_csv(caminho_base_sintetica_40, encoding="utf-8")
    # Inverte o valor do crescimento na primeira linha
    df.loc[0, "crescimento"] = 1 - df.loc[0, "crescimento"]
    caminho_divergente = tmp_path / "base_crescimento_divergente.csv"
    df.to_csv(caminho_divergente, index=False, encoding="utf-8")

    with pytest.raises(ValueError, match="Divergência detectada entre a coluna 'crescimento'"):
        executar_analise(caminho_divergente)


def test_entrada_nao_e_alterada(caminho_base_sintetica_40: Path) -> None:
    """Garante que a execução da análise não altera o arquivo de entrada."""
    conteudo_antes = caminho_base_sintetica_40.read_bytes()
    executar_analise(caminho_base_sintetica_40)
    conteudo_depois = caminho_base_sintetica_40.read_bytes()
    assert conteudo_antes == conteudo_depois


def test_json_sem_nan(caminho_base_sintetica_40: Path) -> None:
    """Garante que o resultado seja serializável em JSON estrito sem NaN ou Infinity."""
    res = executar_analise(caminho_base_sintetica_40)
    texto_json = json.dumps(res, allow_nan=False)
    assert "NaN" not in texto_json
    assert "Infinity" not in texto_json


def test_pontos_extremos_salario_bloco_descritivo_em_fixture_sintetica(
    caminho_base_sintetica_40: Path,
) -> None:
    """Valida o bloco descritivo pontos_extremos_salario com os 3 maiores salários."""
    df = pd.read_csv(caminho_base_sintetica_40, encoding="utf-8")
    mediana_sal = float(df["salario_medio_2024"].median())
    top3_esperados = (
        df.sort_values(by="salario_medio_2024", ascending=False)
        .head(3)[["municipio", "admissoes_2024", "salario_medio_2024"]]
        .to_dict(orient="records")
    )

    res = executar_analise(caminho_base_sintetica_40)

    assert "pontos_extremos_salario" in res
    bloco = res["pontos_extremos_salario"]
    assert bloco["mediana_salario_medio_2024"] == pytest.approx(mediana_sal, rel=1e-9)
    assert len(bloco["municipios"]) == 3

    for obt, esp in zip(bloco["municipios"], top3_esperados, strict=True):
        assert str(obt["municipio"]) == str(esp["municipio"])
        assert obt["admissoes_2024"] == int(esp["admissoes_2024"])
        assert obt["salario_medio_2024"] == pytest.approx(
            float(esp["salario_medio_2024"]), rel=1e-9
        )
        assert "n_salarios_validos_2024" in obt
        assert obt["razao_para_mediana"] == pytest.approx(
            float(esp["salario_medio_2024"]) / mediana_sal, rel=1e-9
        )

