"""Modulo de extracao de texto de documentos PDF e DOCX."""

import io
import zipfile
from typing import Literal

import docx
import pypdf
from fastapi import HTTPException, status

LIMITE_CARACTERES_TEXTO = 50000
LIMITE_DESCOMPRESSAO_DOCX_BYTES = 20 * 1024 * 1024  # 20 MB
LIMITE_PAGINAS_PDF = 50


def detectar_tipo_arquivo(conteudo: bytes) -> Literal["pdf", "docx"]:
    """Detecta o formato do arquivo exclusivamente pelo conteudo (magic bytes/estrutura)."""
    if conteudo.startswith(b"%PDF-"):
        return "pdf"

    if conteudo.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(io.BytesIO(conteudo)) as zf:
                if "word/document.xml" in zf.namelist():
                    return "docx"
        except Exception:
            pass

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "erro": "Arquivo invalido",
            "detalhes": "Formato de arquivo nao suportado. Aceita somente PDF ou DOCX.",
        },
    )


def extrair_texto_pdf(conteudo: bytes) -> str:
    """Extrai texto de arquivo PDF via pypdf sem OCR."""
    try:
        leitor = pypdf.PdfReader(io.BytesIO(conteudo))
        if leitor.is_encrypted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "erro": "Arquivo criptografado",
                    "detalhes": "O arquivo PDF esta protegido por senha ou criptografia.",
                },
            )

        if len(leitor.pages) > LIMITE_PAGINAS_PDF:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "erro": "Arquivo muito extenso",
                    "detalhes": f"PDF excede o limite de {LIMITE_PAGINAS_PDF} paginas.",
                },
            )

        total_caracteres = 0
        paginas_texto: list[str] = []
        for pagina in leitor.pages:
            texto_pag = pagina.extract_text()
            if texto_pag:
                total_caracteres += len(texto_pag)
                if total_caracteres > LIMITE_CARACTERES_TEXTO:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "erro": "Texto muito longo",
                            "detalhes": "Texto extraido excede o limite de 50.000 caracteres.",
                        },
                    )
                paginas_texto.append(texto_pag)
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "erro": "Arquivo corrompido",
                "detalhes": "Nao foi possivel ler o arquivo PDF informado.",
            },
        ) from err

    texto = "\n\n".join(paginas_texto).strip()
    if not texto:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "erro": "Sem texto extraivel",
                "detalhes": "sem texto extraível; OCR não é suportado",
            },
        )

    return texto


def extrair_texto_docx(conteudo: bytes) -> str:
    """Extrai texto de arquivo DOCX via python-docx com protecao anti-ZIP-bomb."""
    # 1. Protecao anti-ZIP-bomb
    try:
        with zipfile.ZipFile(io.BytesIO(conteudo)) as zf:
            total_descomprimido = sum(info.file_size for info in zf.infolist())
            if total_descomprimido > LIMITE_DESCOMPRESSAO_DOCX_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "erro": "Arquivo excessivamente grande",
                        "detalhes": "Tamanho descomprimido excede o limite de seguranca de 20 MB.",
                    },
                )
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "erro": "Arquivo invalido",
                "detalhes": "Estrutura ZIP do DOCX invalida ou corrompida.",
            },
        ) from err

    # 2. Leitura via python-docx
    try:
        doc = docx.Document(io.BytesIO(conteudo))
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "erro": "Arquivo corrompido",
                "detalhes": "Nao foi possivel processar o documento DOCX.",
            },
        ) from err

    partes: list[str] = []
    for p in doc.paragraphs:
        if p.text:
            partes.append(p.text)

    for tabela in doc.tables:
        for linha in tabela.rows:
            celulas = [cel.text.strip() for cel in linha.cells if cel.text.strip()]
            if celulas:
                partes.append(" | ".join(celulas))

    texto = "\n".join(partes).strip()
    if not texto:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "erro": "Sem texto extraivel",
                "detalhes": "sem texto extraível; OCR não é suportado",
            },
        )

    if len(texto) > LIMITE_CARACTERES_TEXTO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "erro": "Texto muito longo",
                "detalhes": "Texto extraido excede o limite de 50.000 caracteres.",
            },
        )

    return texto
