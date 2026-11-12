"""Pipeline de entrega md -> html -> pdf com Edge headless e contagem de paginas (D19, R10).

Uso (a partir de app/tools):
    uv run python md_para_pdf.py <arquivo.md> [--saida <pasta>] [--max-paginas N] [--titulo T]

Codigos de saida: 0 = ok; 1 = PDF acima do limite de paginas; 2 = erro de entrada ou do Edge.
Quebra de pagina manual no Markdown: <div class="quebra-pagina"></div>
"""

import argparse
import html as html_lib
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown
from pypdf import PdfReader

QUEBRA_PAGINA = '<div class="quebra-pagina"></div>'

CAMINHOS_EDGE = (
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
)

CSS = """
@page { size: A4; margin: 20mm 18mm; }
body { font-family: "Segoe UI", Arial, sans-serif; font-size: 11pt; line-height: 1.45;
       color: #1a1a1a; }
h1 { font-size: 20pt; margin: 0 0 12pt; }
h2 { font-size: 15pt; margin: 18pt 0 8pt; }
h3 { font-size: 12pt; margin: 14pt 0 6pt; }
h1, h2, h3 { break-after: avoid; }
table { border-collapse: collapse; width: 100%; margin: 8pt 0; font-size: 10pt; }
th, td { border: 1px solid #999; padding: 4pt 6pt; text-align: left; vertical-align: top; }
th { background: #eee; }
tr, img, pre { break-inside: avoid; }
pre { background: #f4f4f4; padding: 8pt; font-size: 9pt; white-space: pre-wrap;
      word-break: break-word; }
code { font-family: Consolas, "Courier New", monospace; }
img { max-width: 100%; }
.quebra-pagina { break-after: page; }
"""


def converter_md_para_html(texto_md: str, titulo: str = "Documento") -> str:
    corpo = markdown.markdown(texto_md, extensions=["tables", "fenced_code", "sane_lists"])
    return (
        '<!doctype html>\n<html lang="pt-BR">\n<head>\n<meta charset="utf-8">\n'
        f"<title>{html_lib.escape(titulo)}</title>\n<style>{CSS}</style>\n</head>\n"
        f"<body>\n{corpo}\n</body>\n</html>\n"
    )


def localizar_edge() -> Path:
    candidatos = [os.environ.get("CITIZENTECH_EDGE"), *CAMINHOS_EDGE]
    for candidato in candidatos:
        if candidato and Path(candidato).is_file():
            return Path(candidato)
    raise FileNotFoundError("msedge.exe não encontrado (defina CITIZENTECH_EDGE)")


def gerar_pdf(caminho_html: Path, caminho_pdf: Path, timeout_s: int = 120) -> None:
    """Imprime o HTML em PDF com o Edge headless, sem cabecalho nem rodape do navegador."""
    caminho_html = Path(caminho_html).resolve()
    caminho_pdf = Path(caminho_pdf).resolve()
    caminho_pdf.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(prefix="edge-pdf-", ignore_cleanup_errors=True) as perfil:
        comando = [
            str(localizar_edge()),
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--disable-extensions",
            f"--user-data-dir={perfil}",
            "--no-pdf-header-footer",
            f"--print-to-pdf={caminho_pdf}",
            caminho_html.as_uri(),
        ]
        resultado = subprocess.run(comando, capture_output=True, timeout=timeout_s, check=False)
    if not caminho_pdf.is_file() or caminho_pdf.stat().st_size == 0:
        raise RuntimeError(f"o Edge não gerou o PDF (código {resultado.returncode})")


def contar_paginas(caminho_pdf: Path) -> int:
    return len(PdfReader(str(caminho_pdf)).pages)


def main(argumentos: list[str] | None = None) -> int:
    analisador = argparse.ArgumentParser(description="Converte Markdown em HTML e PDF (Edge).")
    analisador.add_argument("origem", type=Path, help="arquivo .md de origem")
    analisador.add_argument("--saida", type=Path, help="pasta de saída (padrão: a do .md)")
    analisador.add_argument("--max-paginas", type=int, help="falha se o PDF passar deste limite")
    analisador.add_argument("--titulo", help="título do documento (padrão: nome do arquivo)")
    opcoes = analisador.parse_args(argumentos)

    origem: Path = opcoes.origem
    if not origem.is_file():
        print(f"ERRO: arquivo não encontrado: {origem}", file=sys.stderr)
        return 2
    saida: Path = opcoes.saida or origem.parent
    saida.mkdir(parents=True, exist_ok=True)
    caminho_html = saida / f"{origem.stem}.html"
    caminho_pdf = saida / f"{origem.stem}.pdf"

    texto_md = origem.read_text(encoding="utf-8")
    caminho_html.write_text(
        converter_md_para_html(texto_md, titulo=opcoes.titulo or origem.stem), encoding="utf-8"
    )
    try:
        gerar_pdf(caminho_html, caminho_pdf)
    except (FileNotFoundError, RuntimeError, subprocess.TimeoutExpired) as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        return 2

    paginas = contar_paginas(caminho_pdf)
    print(f"{caminho_pdf} | {paginas} páginas")
    if opcoes.max_paginas is not None and paginas > opcoes.max_paginas:
        print(
            f"ERRO: o PDF tem {paginas} páginas, acima do limite de {opcoes.max_paginas}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
