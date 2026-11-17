"""Renderiza os blocos ```mermaid de um Markdown em PNG com o Edge headless.

Cada bloco vira `<saida>/<nn>_<slug-do-título>.png`. Usa mermaid.js do jsDelivr (precisa de rede)
e `--virtual-time-budget` para o Edge esperar o desenho antes da captura.

Uso (a partir de app/tools):
    uv run python renderizar_mermaid.py <arquivo.md> --saida <pasta>
Atenção: um erro de sintaxe vira uma imagem de "Syntax error"; confira as imagens geradas.
"""

from __future__ import annotations

import argparse
import html
import re
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

from _comum import localizar_edge

MODELO = """<!doctype html><html><head><meta charset="utf-8">
<style>body{{margin:0;padding:24px;background:#fff;font-family:Segoe UI,Arial}}</style>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
</head><body><pre class="mermaid">{codigo}</pre>
<script>mermaid.initialize({{startOnLoad:true, theme:"neutral", securityLevel:"strict"}});</script>
</body></html>"""


def slug(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", t.lower()).strip("_")[:50]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("arquivo")
    ap.add_argument("--saida", required=True)
    ap.add_argument("--largura", type=int, default=1600)
    ap.add_argument("--altura", type=int, default=1200)
    args = ap.parse_args(argv)
    texto = Path(args.arquivo).read_text(encoding="utf-8")
    saida = Path(args.saida).resolve()
    saida.mkdir(parents=True, exist_ok=True)

    titulo = "diagrama"
    n = 0
    with tempfile.TemporaryDirectory() as tmp:
        for linha_bloco in re.finditer(
            r"^## ([^\n]+)$|```mermaid\n(.*?)```", texto, flags=re.M | re.S
        ):
            if linha_bloco.group(1):
                titulo = linha_bloco.group(1)
                continue
            n += 1
            pagina = Path(tmp) / f"d{n}.html"
            pagina.write_text(
                MODELO.format(codigo=html.escape(linha_bloco.group(2))), encoding="utf-8"
            )
            png = saida / f"{n:02d}_{slug(titulo)}.png"
            r = subprocess.run(
                [
                    str(localizar_edge()),
                    "--headless=new",
                    "--disable-gpu",
                    "--hide-scrollbars",
                    f"--window-size={args.largura},{args.altura}",
                    "--virtual-time-budget=8000",
                    f"--screenshot={png}",
                    pagina.as_uri(),
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            ok = png.is_file() and png.stat().st_size > 5000
            tamanho = png.stat().st_size if png.is_file() else 0
            print(f"{png.name}: {'ok' if ok else 'FALHOU'} ({tamanho} bytes)")
            if not ok:
                print(r.stderr[-500:], file=sys.stderr)
                return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
