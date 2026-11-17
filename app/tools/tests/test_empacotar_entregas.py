"""Testes de unidade e integração do empacotador de entregas."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from empacotar_entregas import ItemEntrega, empacotar, itens_padrao, main

PNG_1X1 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06"
    b"\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf"
    b"\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"
)


def calcular_sha256(conteudo: bytes) -> str:
    return hashlib.sha256(conteudo).hexdigest()


def montar_arvore_base(tmp_path: Path):
    raiz = tmp_path / "repo"
    dados = tmp_path / "dados"

    fonte_analise = raiz / "app/ml/src/citizentech_ml/estatistica/analise_portatil.py"
    fonte_ml_nb = raiz / "app/ml/notebooks/ml_mercado.ipynb"
    fonte_rna_nb = raiz / "app/ml/notebooks/rna_mercado.ipynb"
    fonte_csv = dados / "estatistica/20261115_d11_aceite/base_municipal.csv"

    conteudo_analise = b"# Script analise portatil real\nprint('analise')\n"
    conteudo_ml = b'{"cells": [{"cell_type": "code", "source": ["# ML"]}], "nbformat": 4}\n'
    conteudo_rna = b'{"cells": [{"cell_type": "code", "source": ["# RNA"]}], "nbformat": 4}\n'
    conteudo_csv = b"municipio_ibge,taxa_formalizacao\n3550308,0.75\n"

    for caminho, bytes_conteudo in [
        (fonte_analise, conteudo_analise),
        (fonte_ml_nb, conteudo_ml),
        (fonte_rna_nb, conteudo_rna),
        (fonte_csv, conteudo_csv),
    ]:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_bytes(bytes_conteudo)

    dest_analise = raiz / "08_Estatistica/analise.py"
    dest_csv = raiz / "08_Estatistica/base_municipal.csv"
    dest_req = raiz / "08_Estatistica/requirements.txt"
    dest_ml_nb = raiz / "05_ML/notebook.ipynb"
    dest_rna_nb = raiz / "07_RedesNeurais/notebook.ipynb"
    (raiz / "docs").mkdir(parents=True, exist_ok=True)

    for dest in [dest_analise, dest_csv, dest_req, dest_ml_nb, dest_rna_nb]:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("TODO: modelo do professor a ser substituido\n", encoding="utf-8")

    sha_csv = calcular_sha256(conteudo_csv)
    itens = itens_padrao(sha_csv=sha_csv)

    return raiz, dados, itens, {
        "analise": (dest_analise, conteudo_analise, fonte_analise),
        "csv": (dest_csv, conteudo_csv, fonte_csv),
        "req": dest_req,
        "ml_nb": (dest_ml_nb, conteudo_ml, fonte_ml_nb),
        "rna_nb": (dest_rna_nb, conteudo_rna, fonte_rna_nb),
    }


def test_gera_copias_identicas_e_verificar_passa(tmp_path: Path):
    raiz, dados, itens, dests = montar_arvore_base(tmp_path)

    codigo_gerar = main(
        ["--raiz", str(raiz), "--dados", str(dados), "--sem-pdf"],
        itens=itens,
    )
    assert codigo_gerar == 0

    assert dests["analise"][0].read_bytes() == dests["analise"][1]
    assert dests["csv"][0].read_bytes() == dests["csv"][1]
    assert dests["ml_nb"][0].read_bytes() == dests["ml_nb"][1]
    assert dests["rna_nb"][0].read_bytes() == dests["rna_nb"][1]

    linhas_req = dests["req"].read_text(encoding="utf-8").strip().splitlines()
    assert linhas_req == [
        "pandas",
        "numpy",
        "scipy",
        "statsmodels",
        "matplotlib",
        "scikit-learn",
        "openpyxl",
    ]

    manifesto_path = raiz / "docs/entregas_manifesto.json"
    assert manifesto_path.is_file()
    manifesto = json.loads(manifesto_path.read_text(encoding="utf-8"))
    assert "gerado_em" in manifesto
    assert manifesto["gerado_em"].endswith("Z")

    itens_manifesto = {item["destino"]: item for item in manifesto["itens"]}
    assert itens_manifesto["08_Estatistica/analise.py"]["sha256"] == calcular_sha256(
        dests["analise"][1]
    )
    assert itens_manifesto["08_Estatistica/base_municipal.csv"]["sha256"] == calcular_sha256(
        dests["csv"][1]
    )
    assert itens_manifesto["05_ML/notebook.ipynb"]["sha256"] == calcular_sha256(
        dests["ml_nb"][1]
    )
    assert itens_manifesto["07_RedesNeurais/notebook.ipynb"]["sha256"] == calcular_sha256(
        dests["rna_nb"][1]
    )
    assert itens_manifesto["08_Estatistica/analise.py"]["estado"] == "atualizado"

    codigo_verificar = main(
        ["--raiz", str(raiz), "--dados", str(dados), "--verificar", "--sem-pdf"],
        itens=itens,
    )
    assert codigo_verificar == 0


def test_csv_com_hash_divergente_retorna_2_e_nao_altera_destinos(tmp_path: Path, capsys):
    raiz, dados, _, dests = montar_arvore_base(tmp_path)

    # Cria itens com SHA diferente do arquivo real
    sha_falso = "a" * 64
    itens = itens_padrao(sha_csv=sha_falso)

    codigo = main(
        ["--raiz", str(raiz), "--dados", str(dados), "--sem-pdf"],
        itens=itens,
    )
    assert codigo == 2
    assert "SHA-256 divergente" in capsys.readouterr().err

    # Nenhum destino alterado: continuam com "TODO"
    for chave in ["analise", "csv", "ml_nb", "rna_nb"]:
        conteudo = dests[chave][0].read_text(encoding="utf-8")
        assert "TODO: modelo do professor" in conteudo

    assert not (raiz / "docs/entregas_manifesto.json").exists()


def test_origem_ausente_retorna_2_e_nada_alterado(tmp_path: Path, capsys):
    raiz, dados, itens, dests = montar_arvore_base(tmp_path)

    # Remove fonte do script de análise
    dests["analise"][2].unlink()

    codigo = main(
        ["--raiz", str(raiz), "--dados", str(dados), "--sem-pdf"],
        itens=itens,
    )
    assert codigo == 2
    assert "arquivo de origem não encontrado" in capsys.readouterr().err

    # Nenhum destino alterado
    for chave in ["csv", "ml_nb", "rna_nb"]:
        conteudo = dests[chave][0].read_text(encoding="utf-8")
        assert "TODO: modelo do professor" in conteudo

    assert not (raiz / "docs/entregas_manifesto.json").exists()


def test_segunda_execucao_reporta_inalterado_e_preserva_mtimes(tmp_path: Path):
    raiz, dados, itens, dests = montar_arvore_base(tmp_path)

    # 1ª execução
    assert main(["--raiz", str(raiz), "--dados", str(dados), "--sem-pdf"], itens=itens) == 0

    destinos = [
        dests["analise"][0],
        dests["csv"][0],
        dests["req"],
        dests["ml_nb"][0],
        dests["rna_nb"][0],
    ]
    mtimes_1 = {d: d.stat().st_mtime_ns for d in destinos}

    # Pausa para garantir que mtime mudaria se houvesse reescrita
    time.sleep(0.05)

    # 2ª execução
    assert main(["--raiz", str(raiz), "--dados", str(dados), "--sem-pdf"], itens=itens) == 0

    mtimes_2 = {d: d.stat().st_mtime_ns for d in destinos}
    assert mtimes_1 == mtimes_2

    manifesto = json.loads((raiz / "docs/entregas_manifesto.json").read_text(encoding="utf-8"))
    for item in manifesto["itens"]:
        assert item["estado"] == "inalterado"


def test_origem_alterada_verificar_falha_e_nova_geracao_atualiza(tmp_path: Path, capsys):
    raiz, dados, itens, dests = montar_arvore_base(tmp_path)

    assert main(["--raiz", str(raiz), "--dados", str(dados), "--sem-pdf"], itens=itens) == 0
    assert (
        main(
            ["--raiz", str(raiz), "--dados", str(dados), "--verificar", "--sem-pdf"],
            itens=itens,
        )
        == 0
    )

    # Modifica a origem de análise
    novo_conteudo = b"# Novo codigo da analise atualizado\n"
    dests["analise"][2].write_bytes(novo_conteudo)

    # --verificar deve falhar (código 1) citando o destino
    codigo_verificar = main(
        ["--raiz", str(raiz), "--dados", str(dados), "--verificar", "--sem-pdf"],
        itens=itens,
    )
    assert codigo_verificar == 1
    err = capsys.readouterr().err
    assert "08_Estatistica/analise.py" in err

    # Nova geração deve marcar como "atualizado"
    codigo_gerar = main(
        ["--raiz", str(raiz), "--dados", str(dados), "--sem-pdf"],
        itens=itens,
    )
    assert codigo_gerar == 0
    assert dests["analise"][0].read_bytes() == novo_conteudo

    manifesto = json.loads((raiz / "docs/entregas_manifesto.json").read_text(encoding="utf-8"))
    itens_map = {item["destino"]: item for item in manifesto["itens"]}
    assert itens_map["08_Estatistica/analise.py"]["estado"] == "atualizado"


def test_verificar_nao_escreve_nada(tmp_path: Path):
    raiz, dados, itens, _ = montar_arvore_base(tmp_path)

    assert main(["--raiz", str(raiz), "--dados", str(dados), "--sem-pdf"], itens=itens) == 0

    arquivos_antes = {
        p: (p.stat().st_mtime_ns, p.stat().st_size)
        for p in raiz.rglob("*")
        if p.is_file()
    }

    assert (
        main(
            ["--raiz", str(raiz), "--dados", str(dados), "--verificar", "--sem-pdf"],
            itens=itens,
        )
        == 0
    )

    arquivos_depois = {
        p: (p.stat().st_mtime_ns, p.stat().st_size)
        for p in raiz.rglob("*")
        if p.is_file()
    }

    assert arquivos_antes == arquivos_depois


def test_pdf_real_com_imagens_relativas(tmp_path: Path):
    raiz = tmp_path / "repo"
    pasta_estatistica = raiz / "08_Estatistica"
    pasta_figuras = pasta_estatistica / "evidencias/figuras"
    pasta_figuras.mkdir(parents=True, exist_ok=True)

    (pasta_figuras / "grafico1.png").write_bytes(PNG_1X1)
    (pasta_figuras / "grafico2.png").write_bytes(PNG_1X1)

    md_conteudo = """# Relatório de Estatística

Relatório analítico de validação.

![Gráfico 1](evidencias/figuras/grafico1.png)

![Gráfico 2](evidencias/figuras/grafico2.png)
"""
    md_path = pasta_estatistica / "relatorio.md"
    md_path.write_text(md_conteudo, encoding="utf-8")

    item_pdf = ItemEntrega(
        tipo="pdf",
        origem="08_Estatistica/relatorio.md",
        destino="08_Estatistica/relatorio.pdf",
    )

    codigo = empacotar(raiz=raiz, itens=[item_pdf])
    assert codigo == 0

    pdf_path = pasta_estatistica / "relatorio.pdf"
    html_path = pasta_estatistica / "relatorio.html"

    assert pdf_path.is_file()
    assert html_path.is_file()

    html_texto = html_path.read_text(encoding="utf-8")
    assert 'src="evidencias/figuras/grafico1.png"' in html_texto
    assert 'src="evidencias/figuras/grafico2.png"' in html_texto

    manifesto = json.loads((raiz / "docs/entregas_manifesto.json").read_text(encoding="utf-8"))
    assert len(manifesto["itens"]) == 1
    item_manifesto = manifesto["itens"][0]
    assert item_manifesto["destino"] == "08_Estatistica/relatorio.pdf"
    assert item_manifesto["paginas"] is not None
    assert item_manifesto["paginas"] >= 1
    assert item_manifesto["estado"] == "criado"

    # Segunda execução sem alterações no md -> PDF deve ser inalterado
    mtime_pdf_antes = pdf_path.stat().st_mtime_ns
    time.sleep(0.05)
    assert empacotar(raiz=raiz, itens=[item_pdf]) == 0
    assert pdf_path.stat().st_mtime_ns == mtime_pdf_antes

    manifesto_2 = json.loads((raiz / "docs/entregas_manifesto.json").read_text(encoding="utf-8"))
    assert manifesto_2["itens"][0]["estado"] == "inalterado"


def test_imagem_referenciada_ausente_retorna_2(tmp_path: Path, capsys):
    raiz = tmp_path / "repo"
    pasta_estatistica = raiz / "08_Estatistica"
    pasta_estatistica.mkdir(parents=True, exist_ok=True)

    md_path = pasta_estatistica / "relatorio.md"
    md_path.write_text(
        "# Relatório\n\n![Foto](evidencias/figuras/nao_existe.png)\n",
        encoding="utf-8",
    )

    item_pdf = ItemEntrega(
        tipo="pdf",
        origem="08_Estatistica/relatorio.md",
        destino="08_Estatistica/relatorio.pdf",
    )

    codigo = empacotar(raiz=raiz, itens=[item_pdf])
    assert codigo == 2
    err = capsys.readouterr().err
    assert "evidencias/figuras/nao_existe.png" in err
    assert not (pasta_estatistica / "relatorio.pdf").exists()


def test_pdf_max_paginas_excedido_retorna_1(tmp_path: Path, capsys):
    raiz = tmp_path / "repo"
    pasta_ml = raiz / "05_ML"
    pasta_ml.mkdir(parents=True, exist_ok=True)

    md_path = pasta_ml / "slides.md"
    md_path.write_text(
        "# Slide 1\n"
        '<div class="quebra-pagina"></div>\n'
        "# Slide 2\n"
        '<div class="quebra-pagina"></div>\n'
        "# Slide 3\n",
        encoding="utf-8",
    )

    item_pdf = ItemEntrega(
        tipo="pdf",
        origem="05_ML/slides.md",
        destino="05_ML/slides.pdf",
        max_paginas=2,
    )

    codigo = empacotar(raiz=raiz, itens=[item_pdf])
    assert codigo == 1

    err = capsys.readouterr().err
    assert "acima do limite de 2" in err

    pdf_path = pasta_ml / "slides.pdf"
    assert pdf_path.is_file()

    manifesto = json.loads((raiz / "docs/entregas_manifesto.json").read_text(encoding="utf-8"))
    assert manifesto["itens"][0]["paginas"] == 3


def test_todos_os_relatorios_pdf_das_disciplinas_sao_cobertos():
    """Todo relatório entregue em PDF tem item no empacotador; senão --verificar não o vê."""
    pdfs = {i.destino: i for i in itens_padrao() if i.tipo == "pdf"}
    esperados = {
        "01_AICSS/relatorio.pdf",
        "02_Cybersecurity/relatorio.pdf",
        "03_DataScience/relatorio.pdf",
        "04_CTP_Python/documento.pdf",
        "05_ML/slides.pdf",
        "08_Estatistica/relatorio.pdf",
    }
    assert esperados <= set(pdfs)
    assert pdfs["02_Cybersecurity/relatorio.pdf"].max_paginas == 15
    assert all(item.titulo for item in pdfs.values())


def test_requirements_de_ml_e_rna_instalam_o_que_os_notebooks_importam():
    """Os notebooks importam torch e citizentech_ml; o requirements gerado precisa refletir isso."""
    gerados = {i.destino: i for i in itens_padrao() if i.tipo == "texto_gerado"}
    for destino in ("05_ML/requirements.txt", "07_RedesNeurais/requirements.txt"):
        conteudo = gerados[destino].conteudo or ""
        assert "tensorflow" not in conteudo
        assert "torch==" in conteudo
        assert "citizentech_ml" in conteudo


def test_pdf_usa_titulo_do_item(tmp_path: Path):
    raiz = tmp_path / "repo"
    (raiz / "05_ML").mkdir(parents=True)
    (raiz / "05_ML/slides.md").write_text("# Slide\n", encoding="utf-8")
    item = ItemEntrega(
        tipo="pdf",
        origem="05_ML/slides.md",
        destino="05_ML/slides.pdf",
        titulo="CitizenTech - Slides",
    )
    assert empacotar(raiz=raiz, itens=[item]) == 0
    html = (raiz / "05_ML/slides.html").read_text(encoding="utf-8")
    assert "<title>CitizenTech - Slides</title>" in html


def test_dados_ausente_sem_env_retorna_2(tmp_path: Path, monkeypatch, capsys):
    raiz = tmp_path / "repo"
    raiz.mkdir(parents=True, exist_ok=True)
    monkeypatch.delenv("CITIZENTECH_DADOS", raising=False)

    codigo = main(["--raiz", str(raiz)])
    assert codigo == 2
    err = capsys.readouterr().err
    assert "CITIZENTECH_DADOS" in err


def test_nunca_escreve_fora_do_escopo(tmp_path: Path):
    raiz, dados, itens, _ = montar_arvore_base(tmp_path)

    # Cria diretórios adicionais e arquivos de controle
    (raiz / "01_AICSS").mkdir(parents=True, exist_ok=True)
    arquivo_controle_1 = raiz / "01_AICSS/controle.txt"
    arquivo_controle_1.write_text("nao mexa\n", encoding="utf-8")

    (raiz / "outro_modulo").mkdir(parents=True, exist_ok=True)
    arquivo_controle_2 = raiz / "outro_modulo/controle.txt"
    arquivo_controle_2.write_text("intocado\n", encoding="utf-8")

    arquivos_antes = {p.relative_to(raiz).as_posix() for p in raiz.rglob("*") if p.is_file()}

    assert main(["--raiz", str(raiz), "--dados", str(dados), "--sem-pdf"], itens=itens) == 0

    arquivos_depois = {p.relative_to(raiz).as_posix() for p in raiz.rglob("*") if p.is_file()}
    arquivos_modificados_ou_criados = arquivos_depois - arquivos_antes

    # Todos os arquivos novos/modificados devem estar estritamente
    # em 0X_* ou docs/entregas_manifesto.json
    for caminho in arquivos_modificados_ou_criados:
        valido = caminho == "docs/entregas_manifesto.json" or any(
            caminho.startswith(f"0{n}_") for n in range(10)
        )
        assert valido, f"Arquivo criado fora do escopo permitido: {caminho}"

    # Arquivos de controle permanecem intactos
    assert arquivo_controle_1.read_text(encoding="utf-8") == "nao mexa\n"
    assert arquivo_controle_2.read_text(encoding="utf-8") == "intocado\n"


def test_requirements_txt_estatistica_gerado_exatamente_7_linhas(tmp_path: Path):
    raiz = tmp_path / "repo"
    (raiz / "docs").mkdir(parents=True, exist_ok=True)

    item_req = ItemEntrega(
        tipo="texto_gerado",
        origem="(declarado)",
        destino="08_Estatistica/requirements.txt",
        conteudo="\n".join([
            "pandas",
            "numpy",
            "scipy",
            "statsmodels",
            "matplotlib",
            "scikit-learn",
            "openpyxl",
        ])
        + "\n",
    )

    assert empacotar(raiz=raiz, itens=[item_req]) == 0

    req_file = raiz / "08_Estatistica/requirements.txt"
    assert req_file.is_file()
    linhas = req_file.read_text(encoding="utf-8").splitlines()
    assert linhas == [
        "pandas",
        "numpy",
        "scipy",
        "statsmodels",
        "matplotlib",
        "scikit-learn",
        "openpyxl",
    ]


def test_concatenacao_junta_fontes_em_ordem_e_verificar_detecta_mudanca(tmp_path: Path):
    raiz = tmp_path / "repo"
    (raiz / "docs").mkdir(parents=True)
    a = raiz / "app/db/ddl/001_a.sql"
    b = raiz / "app/db/consultas/b.sql"
    for caminho, texto in ((a, "CREATE TABLE a (x NUMBER);\n"), (b, "SELECT 1 FROM dual;\n")):
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(texto, encoding="utf-8")
    item = ItemEntrega(
        tipo="concatenacao",
        origem="app/db/ddl/001_a.sql;app/db/consultas/b.sql",
        destino="03_DataScience/oracle.sql",
        conteudo="-- cabeçalho gerado",
    )

    assert main(["--raiz", str(raiz), "--sem-pdf"], itens=[item]) == 0
    texto = (raiz / "03_DataScience/oracle.sql").read_text(encoding="utf-8")
    assert texto.startswith("-- cabeçalho gerado")
    assert texto.index("CREATE TABLE a") < texto.index("SELECT 1 FROM dual")
    assert "-- Origem: app/db/ddl/001_a.sql" in texto
    assert main(["--raiz", str(raiz), "--sem-pdf", "--verificar"], itens=[item]) == 0

    b.write_text("SELECT 2 FROM dual;\n", encoding="utf-8")
    assert main(["--raiz", str(raiz), "--sem-pdf", "--verificar"], itens=[item]) == 1


def test_itens_codigo_apontam_para_fontes_existentes():
    from empacotar_entregas import itens_codigo

    raiz = Path(__file__).resolve().parents[3]
    for item in itens_codigo():
        if item.tipo not in ("copia", "concatenacao"):
            continue
        for origem in item.origem.split(";"):
            assert (raiz / origem).is_file(), origem
