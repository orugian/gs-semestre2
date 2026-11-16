"""Testes estáticos de entrega e integridade dos notebooks ML e RNA.

Estes testes inspecionam os notebooks sem executá-los e sem ler dados reais.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

NOTEBOOKS_DIR = Path(__file__).resolve().parent.parent / "notebooks"
ML_NOTEBOOK_PATH = NOTEBOOKS_DIR / "ml_mercado.ipynb"
RNA_NOTEBOOK_PATH = NOTEBOOKS_DIR / "rna_mercado.ipynb"

TERMOS_PROIBIDOS = [
    "vaga",
    "probabilidade de contrata",
    "probabilidade de emprego",
    "vale a pena",
]

PADROES_CODIGO_PROIBIDOS = [
    r"caged[\\/]parquet",
    r"joblib\.load\(",
    r"torch\.load\(",
    r"treinar_classicos\(",
    r"treinar_rna\(",
    r"\.fit\(",
]


def carregar_notebook(caminho: Path) -> dict:
    assert caminho.exists(), f"Notebook não encontrado: {caminho}"
    with open(caminho, encoding="utf-8") as f:
        nb = json.load(f)
    assert nb.get("nbformat") == 4, f"nbformat deve ser 4, obtido {nb.get('nbformat')}"
    return nb


@pytest.mark.parametrize("caminho", [ML_NOTEBOOK_PATH, RNA_NOTEBOOK_PATH])
def test_notebook_existe_e_nbformat4_valido(caminho: Path):
    nb = carregar_notebook(caminho)
    assert "cells" in nb
    assert len(nb["cells"]) > 0


@pytest.mark.parametrize("caminho", [ML_NOTEBOOK_PATH, RNA_NOTEBOOK_PATH])
def test_todas_celulas_codigo_possuem_execution_count_e_sem_erro(caminho: Path):
    nb = carregar_notebook(caminho)
    celulas_codigo = [c for c in nb["cells"] if c.get("cell_type") == "code"]
    assert len(celulas_codigo) > 0, f"Notebook {caminho.name} não contém células de código."

    for idx, c in enumerate(celulas_codigo):
        ec = c.get("execution_count")
        assert (
            isinstance(ec, int) and ec > 0
        ), f"Célula de código {idx} em {caminho.name} não foi executada (execution_count={ec})."

        for out in c.get("outputs", []):
            out_type = out.get("output_type")
            err_msg = (
                f"Célula de código {idx} em {caminho.name} contém erro: "
                f"{out.get('ename')}: {out.get('evalue')}"
            )
            assert out_type != "error", err_msg


@pytest.mark.parametrize("caminho", [ML_NOTEBOOK_PATH, RNA_NOTEBOOK_PATH])
def test_cada_celula_codigo_seguida_imediatamente_por_markdown(caminho: Path):
    nb = carregar_notebook(caminho)
    cells = nb["cells"]

    for idx, cell in enumerate(cells):
        if cell.get("cell_type") == "code":
            assert idx + 1 < len(
                cells
            ), f"Célula {idx} em {caminho.name} é de código e é a última célula do notebook."
            seguinte = cells[idx + 1]
            assert seguinte.get("cell_type") == "markdown", (
                f"Célula {idx} (código) em {caminho.name} deve ser seguida imediatamente "
                f"por célula markdown interpretativa. Próxima célula é {seguinte.get('cell_type')}."
            )


@pytest.mark.parametrize("caminho", [ML_NOTEBOOK_PATH, RNA_NOTEBOOK_PATH])
def test_regras_seguranca_codigo_e_reuso(caminho: Path):
    nb = carregar_notebook(caminho)

    todo_codigo = "\n".join(
        "".join(c.get("source", [])) for c in nb["cells"] if c.get("cell_type") == "code"
    )

    # Deve importar citizentech_ml
    assert (
        "citizentech_ml" in todo_codigo
    ), f"Notebook {caminho.name} deve importar o pacote citizentech_ml."

    # Não pode conter padrões proibidos
    for padrao in PADROES_CODIGO_PROIBIDOS:
        assert not re.search(
            padrao, todo_codigo
        ), f"Notebook {caminho.name} contém padrão de código proibido: {padrao}"

    # Não pode conter leitura direta de arquivo com competência 2026 (holdout fechado)
    for linha in todo_codigo.splitlines():
        tem_2026 = any(f"20260{m}" in linha for m in range(1, 10))
        tem_leitura = any(k in linha for k in ["read", "open"])
        if tem_2026 and tem_leitura:
            raise AssertionError(f"Leitura proibida de arquivo de competência 2026: {linha}")


@pytest.mark.parametrize("caminho", [ML_NOTEBOOK_PATH, RNA_NOTEBOOK_PATH])
def test_linguagem_proibida(caminho: Path):
    nb = carregar_notebook(caminho)

    todo_texto = "\n".join("".join(c.get("source", [])) for c in nb["cells"]).lower()

    for termo in TERMOS_PROIBIDOS:
        assert (
            termo not in todo_texto
        ), f"Notebook {caminho.name} contém termo proibido de linguagem: '{termo}'"


def test_secoes_obrigatorias_notebook_ml():
    nb = carregar_notebook(ML_NOTEBOOK_PATH)
    textos_md = "\n".join(
        "".join(c.get("source", [])) for c in nb["cells"] if c.get("cell_type") == "markdown"
    ).lower()

    secoes_esperadas = [
        "integrantes",
        "eda",
        "pré-processamento",
        "modelagem",
        "otimização",
        "avaliação",
        "interpretação",
        "aplicação",
    ]

    for sec in secoes_esperadas:
        assert (
            sec in textos_md
        ), f"Notebook ML não contém a seção obrigatória: '{sec}'"


def test_secoes_obrigatorias_notebook_rna():
    nb = carregar_notebook(RNA_NOTEBOOK_PATH)
    textos_md = "\n".join(
        "".join(c.get("source", [])) for c in nb["cells"] if c.get("cell_type") == "markdown"
    ).lower()

    secoes_esperadas = [
        "1. problema e aplicação",
        "2. dataset",
        "3. preparação",
        "4. arquitetura",
        "5. treinamento",
        "6. refinamento",
        "7. avaliação",
        "8. demonstração",
    ]

    for sec in secoes_esperadas:
        assert (
            sec in textos_md
        ), f"Notebook RNA não contém a seção obrigatória: '{sec}'"


@pytest.mark.parametrize("caminho", [ML_NOTEBOOK_PATH, RNA_NOTEBOOK_PATH])
def test_ultima_celula_e_markdown_de_sintese(caminho: Path):
    nb = carregar_notebook(caminho)
    ultima_celula = nb["cells"][-1]
    assert (
        ultima_celula.get("cell_type") == "markdown"
    ), f"A última célula de {caminho.name} deve ser markdown."
    texto_ultima = "".join(ultima_celula.get("source", [])).lower()
    assert any(
        palavra in texto_ultima for palavra in ["síntese", "conclusão", "considerações", "resumo"]
    ), f"A última célula de {caminho.name} deve conter texto de síntese."


def obter_repo_root() -> Path:
    p = Path(__file__).resolve()
    while p != p.parent:
        if (p / "05_ML").exists() and (p / "app").exists():
            return p
        p = p.parent
    raise RuntimeError("Raiz do repositório não encontrada")


SLIDES_PATH = obter_repo_root() / "05_ML" / "slides.md"


def test_slides_demonstracao_numeros_correspondem_a_saida_celula_ml():
    assert SLIDES_PATH.exists(), f"Arquivo de slides não encontrado: {SLIDES_PATH}"
    with open(SLIDES_PATH, encoding="utf-8") as f:
        slides_text = f.read()

    match_slide = re.search(
        r"# Demonstração da Aplicação Prática.*?(?=\n<div|\Z)",
        slides_text,
        re.DOTALL,
    )
    assert match_slide, "Slide 'Demonstração da Aplicação Prática' não encontrado em slides.md"
    slide_content = match_slide.group(0)

    nb = carregar_notebook(ML_NOTEBOOK_PATH)
    app_cells = [
        c
        for c in nb["cells"]
        if c.get("cell_type") == "code"
        and any("8. Aplicação" in line or "df_exemplos" in line for line in c.get("source", []))
    ]
    assert len(app_cells) == 1, (
        f"Esperado exatamente 1 célula de aplicação prática no notebook ML, "
        f"encontrado {len(app_cells)}"
    )
    app_cell = app_cells[0]

    output_text = ""
    for out in app_cell.get("outputs", []):
        if "text" in out:
            output_text += "".join(out["text"])
        elif "data" in out and "text/plain" in out["data"]:
            output_text += "".join(out["data"]["text/plain"])

    assert (
        output_text.strip()
    ), "A célula de aplicação do notebook ML não possui saídas de texto executadas."

    saida_floats = [float(x) for x in re.findall(r"\b\d+\.?\d*\b", output_text)]

    linhas_exemplos = [
        linha
        for linha in slide_content.splitlines()
        if any(
            k in linha
            for k in [
                "analista_dados_bi",
                "analista_monitoramento_iot",
                "analista_processos",
                "Dados/BI",
                "Monitoramento/IoT",
                "Processos",
            ]
        )
        and any(
            termo in linha.lower()
            for termo in [
                "realizado",
                "ridge",
                "sazonal",
                "baseline",
                "persistência",
                "rf",
                "mlp",
            ]
        )
    ]
    assert (
        len(linhas_exemplos) >= 3
    ), f"Esperado pelo menos 3 linhas de cenários na demonstração, obtido {len(linhas_exemplos)}"

    erros = []
    for linha in linhas_exemplos:
        nums_ptbr = re.findall(r"\b\d{1,3}(?:\.\d{3})+(?:,\d+)?\b|\b\d+(?:,\d+)?\b", linha)
        for n_str in nums_ptbr:
            val = float(n_str.replace(".", "").replace(",", "."))
            diffs = [abs(val - out_val) for out_val in saida_floats]
            min_diff = min(diffs) if diffs else float("inf")
            if min_diff > 1.0:
                erros.append(
                    f"Número '{n_str}' (valor {val}) na linha '{linha.strip()}' "
                    f"não encontrado na saída da célula de aplicação do ml_mercado.ipynb "
                    f"(menor diferença: {min_diff:.2f})"
                )

    assert not erros, (
        "Números no slide de demonstração divergem da saída da célula executada:\n"
        + "\n".join(erros)
    )


def test_slides_sem_latex_nem_cifrao_exceto_reais():
    assert SLIDES_PATH.exists(), f"Arquivo de slides não encontrado: {SLIDES_PATH}"
    with open(SLIDES_PATH, encoding="utf-8") as f:
        slides_text = f.read()

    assert "{,}" not in slides_text, "slides.md contém '{,}' do LaTeX. Utilize vírgula simples."
    assert r"\alpha" not in slides_text, "slides.md contém '\\alpha' do LaTeX. Utilize Unicode 'α'."
    assert r"\times" not in slides_text, "slides.md contém '\\times' do LaTeX. Utilize Unicode '×'."

    linhas_cifrao_invalido = []
    for num_linha, linha in enumerate(slides_text.splitlines(), start=1):
        cifroes_sem_r = re.findall(r"(?<!R)\$", linha)
        if cifroes_sem_r:
            linhas_cifrao_invalido.append(f"Linha {num_linha}: {linha.strip()}")

    assert not linhas_cifrao_invalido, (
        "slides.md contém '$' do LaTeX (permitido apenas 'R$'):\n"
        + "\n".join(linhas_cifrao_invalido)
    )

