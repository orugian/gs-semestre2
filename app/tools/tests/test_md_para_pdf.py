"""Pipeline md -> html -> pdf: conversao, PDF real pelo Edge e limite de paginas."""

from md_para_pdf import QUEBRA_PAGINA, contar_paginas, converter_md_para_html, main

MD_TRES_PAGINAS = f"""# Relatório de teste

Página um, com acentuação: ção, é, ã.

| Métrica | Valor |
|---|---|
| temperatura_c | 38,0 |

{QUEBRA_PAGINA}

## Página dois

```python
print("bloco de código")
```

{QUEBRA_PAGINA}

## Página três
"""


def test_markdown_vira_html_utf8_com_tabela_e_codigo():
    html = converter_md_para_html(MD_TRES_PAGINAS, titulo="Relatório de teste")

    assert '<meta charset="utf-8">' in html
    assert "<title>Relatório de teste</title>" in html
    assert "<table>" in html and "<td>38,0</td>" in html
    assert "<pre>" in html and "bloco de código" in html
    assert "acentuação: ção, é, ã" in html


def test_pdf_gerado_pelo_edge_tem_as_paginas_contadas(tmp_path):
    origem = tmp_path / "relatorio.md"
    origem.write_text(MD_TRES_PAGINAS, encoding="utf-8")

    codigo = main([str(origem), "--saida", str(tmp_path)])

    assert codigo == 0
    assert (tmp_path / "relatorio.html").is_file()
    assert contar_paginas(tmp_path / "relatorio.pdf") == 3


def test_limite_de_paginas_excedido_retorna_erro(tmp_path, capsys):
    origem = tmp_path / "relatorio.md"
    origem.write_text(MD_TRES_PAGINAS, encoding="utf-8")

    codigo = main([str(origem), "--saida", str(tmp_path), "--max-paginas", "2"])

    assert codigo == 1
    assert "3 páginas" in capsys.readouterr().err


def test_limite_de_paginas_respeitado_retorna_zero(tmp_path):
    origem = tmp_path / "relatorio.md"
    origem.write_text(MD_TRES_PAGINAS, encoding="utf-8")

    assert main([str(origem), "--saida", str(tmp_path), "--max-paginas", "3"]) == 0


def test_arquivo_de_origem_inexistente_retorna_erro(tmp_path, capsys):
    codigo = main([str(tmp_path / "nao_existe.md"), "--saida", str(tmp_path)])

    assert codigo == 2
    assert "não encontrado" in capsys.readouterr().err
