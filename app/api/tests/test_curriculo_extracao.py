"""Testes unitarios do modulo de extracao de texto (PDF/DOCX)."""

import io
import zipfile

import docx
import pypdf
import pytest
from fastapi import HTTPException

from citizentech.curriculo.extracao import (
    detectar_tipo_arquivo,
    extrair_texto_docx,
    extrair_texto_pdf,
)


def _criar_pdf_minimo(texto: str) -> bytes:
    """Gera bytes de um PDF 1.4 minimo valido com texto legivel pelo pypdf."""
    stream_txt = f"BT\n/F1 12 Tf\n50 700 Td\n({texto}) Tj\nET\n".encode("latin-1")
    tamanho_stream = len(stream_txt)

    corpo = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        + f"4 0 obj\n<< /Length {tamanho_stream} >>\nstream\n".encode("latin-1")
        + stream_txt
        + b"endstream\nendobj\n"
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    )
    xref_offset = len(corpo)
    offsets = [0]
    for obj_num in range(1, 6):
        offsets.append(corpo.find(f"{obj_num} 0 obj\n".encode("latin-1")))

    xref = b"xref\n0 6\n0000000000 65535 f \n"
    for off in offsets[1:]:
        xref += f"{off:010d} 00000 n \n".encode("latin-1")

    trailer = (
        f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode(
            "latin-1"
        )
    )
    return corpo + xref + trailer


def _criar_docx_valido(
    paragrafos: list[str], linhas_tabela: list[list[str]] | None = None
) -> bytes:
    doc = docx.Document()
    for p in paragrafos:
        doc.add_paragraph(p)
    if linhas_tabela:
        tabela = doc.add_table(rows=len(linhas_tabela), cols=len(linhas_tabela[0]))
        for i, linha in enumerate(linhas_tabela):
            for j, celula in enumerate(linha):
                tabela.cell(i, j).text = celula
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_detectar_tipo_arquivo_pdf_e_docx():
    pdf_bytes = _criar_pdf_minimo("Teste")
    assert detectar_tipo_arquivo(pdf_bytes) == "pdf"

    docx_bytes = _criar_docx_valido(["Texto DOCX"])
    assert detectar_tipo_arquivo(docx_bytes) == "docx"


def test_detectar_tipo_arquivo_rejeita_txt_e_binario_aleatorio():
    txt_bytes = b"Este e um arquivo texto puro."
    with pytest.raises(HTTPException) as exc1:
        detectar_tipo_arquivo(txt_bytes)
    assert exc1.value.status_code == 400

    zip_nao_docx = io.BytesIO()
    with zipfile.ZipFile(zip_nao_docx, "w") as zf:
        zf.writestr("arquivo.txt", "conteudo")
    with pytest.raises(HTTPException) as exc2:
        detectar_tipo_arquivo(zip_nao_docx.getvalue())
    assert exc2.value.status_code == 400


def test_extrair_texto_pdf_valido():
    pdf_bytes = _criar_pdf_minimo("Experiencia com Python e Docker")
    texto = extrair_texto_pdf(pdf_bytes)
    assert "Experiencia com Python e Docker" in texto


def test_extrair_texto_pdf_sem_texto_lanca_400():
    # PDF em branco sem stream de texto
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=100, height=100)
    buf = io.BytesIO()
    writer.write(buf)

    with pytest.raises(HTTPException) as exc:
        extrair_texto_pdf(buf.getvalue())
    assert exc.value.status_code == 400
    assert "sem texto extraível; OCR não é suportado" in exc.value.detail["detalhes"]


def test_extrair_texto_pdf_criptografado_lanca_400():
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.encrypt("senha_segredo")
    buf = io.BytesIO()
    writer.write(buf)

    with pytest.raises(HTTPException) as exc:
        extrair_texto_pdf(buf.getvalue())
    assert exc.value.status_code == 400
    assert "protegido por senha ou criptografia" in exc.value.detail["detalhes"]


def test_extrair_texto_pdf_corrompido_lanca_400():
    bytes_corrompidos = b"%PDF-1.4 conteudo corrompido e invalido"
    with pytest.raises(HTTPException) as exc:
        extrair_texto_pdf(bytes_corrompidos)
    assert exc.value.status_code == 400


def test_extrair_texto_pdf_arvore_pages_quebrada_lanca_400():
    # Item 6: PDF de cabecalho valido e arvore /Pages quebrada (Kids nao iteravel)
    corpo = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids 99 /Count 1 >>\nendobj\n"
    )
    xref_offset = len(corpo)
    trailer = f"trailer\n<< /Size 3 /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode(
        "latin-1"
    )
    corpo += trailer
    with pytest.raises(HTTPException) as exc:
        extrair_texto_pdf(corpo)
    assert exc.value.status_code == 400


def test_extrair_texto_pdf_limite_50000_acumulado_por_pagina(monkeypatch):
    # Item 7: Contagem acumulada por página; ultrapassou 50 000 caracteres -> 400 imediatamente
    class FakePage:
        def __init__(self, chars: int):
            self.chars = chars
            self.extraido = False

        def extract_text(self):
            self.extraido = True
            return "X" * self.chars

    p1 = FakePage(30000)
    p2 = FakePage(30000)
    p3 = FakePage(10)

    class FakeReader:
        def __init__(self, stream):
            self.is_encrypted = False
            self.pages = [p1, p2, p3]

    monkeypatch.setattr(pypdf, "PdfReader", FakeReader)

    with pytest.raises(HTTPException) as exc:
        extrair_texto_pdf(b"%PDF-1.4 fake")

    assert exc.value.status_code == 400
    assert "50.000 caracteres" in exc.value.detail["detalhes"]
    # Interrompe imediatamente: p3 nao pode ter sido extraido
    assert p1.extraido is True
    assert p2.extraido is True
    assert p3.extraido is False, "Pagina 3 nao deveria ter sido processada apos estourar o limite"




def test_extrair_texto_docx_valido_com_paragrafos_e_tabelas():
    docx_bytes = _criar_docx_valido(
        paragrafos=["Desenvolvedor Backend", "Habilidades em cloud"],
        linhas_tabela=[["Empresa A", "2020-2022"], ["Empresa B", "2022-2024"]],
    )
    texto = extrair_texto_docx(docx_bytes)
    assert "Desenvolvedor Backend" in texto
    assert "Habilidades em cloud" in texto
    assert "Empresa A | 2020-2022" in texto
    assert "Empresa B | 2022-2024" in texto


def test_extrair_texto_docx_anti_zip_bomb_lanca_400():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Escreve 21 MB de zeros que comprimem para poucos KB
        zf.writestr("word/document.xml", b"0" * (21 * 1024 * 1024))

    with pytest.raises(HTTPException) as exc:
        extrair_texto_docx(buf.getvalue())
    assert exc.value.status_code == 400
    assert "20 MB" in exc.value.detail["detalhes"]


def test_extrair_texto_docx_sem_texto_lanca_400():
    docx_vazio = _criar_docx_valido(paragrafos=[])
    with pytest.raises(HTTPException) as exc:
        extrair_texto_docx(docx_vazio)
    assert exc.value.status_code == 400
    assert "sem texto extraível; OCR não é suportado" in exc.value.detail["detalhes"]


def test_extrair_texto_acima_de_50000_caracteres_lanca_400():
    texto_gigante = "A" * 50001
    docx_bytes = _criar_docx_valido(paragrafos=[texto_gigante])
    with pytest.raises(HTTPException) as exc:
        extrair_texto_docx(docx_bytes)
    assert exc.value.status_code == 400
    assert "50.000 caracteres" in exc.value.detail["detalhes"]
