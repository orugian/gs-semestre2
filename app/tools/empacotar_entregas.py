"""Empacotador de entregas das pastas 0X_* e gerador de PDFs.

Uso (a partir de app/tools):
    uv run python empacotar_entregas.py [--raiz <REPO>] [--dados <DADOS>] [--verificar] [--sem-pdf]

Códigos de saída:
    0 = sucesso
    1 = verificação falhou (cópia ausente/desatualizada) ou PDF excedeu max_paginas
    2 = erro de validação (origem ausente, hash divergente, imagem ausente, dados ausente)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from md_para_pdf import contar_paginas, converter_md_para_html, gerar_pdf

REQUISITOS_ESTATISTICA = [
    "pandas",
    "numpy",
    "scipy",
    "statsmodels",
    "matplotlib",
    "scikit-learn",
    "openpyxl",
]
CONTEUDO_REQUISITOS_ESTATISTICA = "\n".join(REQUISITOS_ESTATISTICA) + "\n"
SHA256_BASE_MUNICIPAL = "5dbc73acfb01012a7aa0fa45ef457a7226639a8b48bda85b0389972f99a9a7ee"


@dataclass(frozen=True)
class ItemEntrega:
    tipo: str  # "copia", "copia_dados", "pdf", "texto_gerado"
    origem: str
    destino: str
    sha256_esperado: str | None = None
    max_paginas: int | None = None
    conteudo: str | None = None


def itens_padrao(sha_csv: str = SHA256_BASE_MUNICIPAL) -> list[ItemEntrega]:
    return [
        ItemEntrega(
            tipo="copia",
            origem="app/ml/src/citizentech_ml/estatistica/analise_portatil.py",
            destino="08_Estatistica/analise.py",
        ),
        ItemEntrega(
            tipo="copia_dados",
            origem="estatistica/20261115_d11_aceite/base_municipal.csv",
            destino="08_Estatistica/base_municipal.csv",
            sha256_esperado=sha_csv,
        ),
        ItemEntrega(
            tipo="copia",
            origem="app/ml/notebooks/ml_mercado.ipynb",
            destino="05_ML/notebook.ipynb",
        ),
        ItemEntrega(
            tipo="copia",
            origem="app/ml/notebooks/rna_mercado.ipynb",
            destino="07_RedesNeurais/notebook.ipynb",
        ),
        ItemEntrega(
            tipo="pdf",
            origem="08_Estatistica/relatorio.md",
            destino="08_Estatistica/relatorio.pdf",
        ),
        ItemEntrega(
            tipo="pdf",
            origem="05_ML/slides.md",
            destino="05_ML/slides.pdf",
        ),
        ItemEntrega(
            tipo="texto_gerado",
            origem="(declarado)",
            destino="08_Estatistica/requirements.txt",
            conteudo=CONTEUDO_REQUISITOS_ESTATISTICA,
        ),
    ]


def calcular_sha256(caminho: Path) -> str:
    hasher = hashlib.sha256()
    with open(caminho, "rb") as f:
        while pedaco := f.read(65536):
            hasher.update(pedaco)
    return hasher.hexdigest()


def extrair_imagens_relativas(texto_md: str) -> list[str]:
    padrao = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
    imagens = []
    for match in padrao.findall(texto_md):
        bruto = match.strip()
        token = bruto.split()[0]
        limpo = token.strip("<>\"'")
        if limpo.startswith(("http://", "https://", "data:", "file://")):
            continue
        if limpo:
            imagens.append(limpo)
    return imagens


def gravar_atomico(caminho: Path, dados: bytes) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=caminho.parent,
        delete=False,
        prefix=f".{caminho.name}.",
        suffix=".tmp",
    ) as temp_file:
        temp_file.write(dados)
        temp_file.flush()
        temp_path = Path(temp_file.name)
    try:
        os.replace(temp_path, caminho)
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)


def gravar_se_diferente(caminho: Path, novos_bytes: bytes) -> str:
    if caminho.is_file():
        atuais = caminho.read_bytes()
        if atuais == novos_bytes:
            return "inalterado"
        gravar_atomico(caminho, novos_bytes)
        return "atualizado"
    gravar_atomico(caminho, novos_bytes)
    return "criado"


def validar_origens(raiz: Path, dados: Path | None, itens: list[ItemEntrega]) -> int:
    precisa_dados = any(i.tipo == "copia_dados" for i in itens)
    if precisa_dados and dados is None:
        print(
            "ERRO: diretório de dados não informado (defina CITIZENTECH_DADOS ou use --dados)",
            file=sys.stderr,
        )
        return 2

    for item in itens:
        if item.tipo == "copia":
            orig = raiz / item.origem
            if not orig.is_file():
                print(f"ERRO: arquivo de origem não encontrado: {orig}", file=sys.stderr)
                return 2
            if item.sha256_esperado:
                sha = calcular_sha256(orig)
                if sha != item.sha256_esperado:
                    print(
                        f"ERRO: SHA-256 divergente em {orig}: "
                        f"esperado {item.sha256_esperado}, obtido {sha}",
                        file=sys.stderr,
                    )
                    return 2
        elif item.tipo == "copia_dados":
            assert dados is not None
            orig = dados / item.origem
            if not orig.is_file():
                print(f"ERRO: arquivo de dados não encontrado: {orig}", file=sys.stderr)
                return 2
            if item.sha256_esperado:
                sha = calcular_sha256(orig)
                if sha != item.sha256_esperado:
                    print(
                        f"ERRO: SHA-256 divergente em {orig}: "
                        f"esperado {item.sha256_esperado}, obtido {sha}",
                        file=sys.stderr,
                    )
                    return 2
        elif item.tipo == "pdf":
            orig = raiz / item.origem
            if not orig.is_file():
                print(f"ERRO: arquivo markdown não encontrado: {orig}", file=sys.stderr)
                return 2
            texto_md = orig.read_text(encoding="utf-8")
            imagens = extrair_imagens_relativas(texto_md)
            for img_rel in imagens:
                img_path = (orig.parent / img_rel).resolve()
                if not img_path.is_file():
                    print(
                        f"ERRO: imagem referenciada não encontrada: {img_rel} (em {item.origem})",
                        file=sys.stderr,
                    )
                    return 2
        elif item.tipo == "texto_gerado":
            pass
        else:
            print(f"ERRO: tipo de entrega desconhecido: {item.tipo}", file=sys.stderr)
            return 2

    return 0


def imprimir_tabela(itens_manifesto: list[dict]) -> None:
    print(f"{'Destino':<45} {'Estado':<12} {'Páginas':<8}")
    print("-" * 67)
    for item in itens_manifesto:
        paginas_str = str(item["paginas"]) if item["paginas"] is not None else "-"
        print(f"{item['destino']:<45} {item['estado']:<12} {paginas_str:<8}")


def empacotar(
    raiz: Path,
    dados: Path | None = None,
    itens: list[ItemEntrega] | None = None,
    sem_pdf: bool = False,
) -> int:
    if itens is None:
        itens = itens_padrao()

    itens_ativos = [i for i in itens if not (sem_pdf and i.tipo == "pdf")]

    codigo_validacao = validar_origens(raiz, dados, itens_ativos)
    if codigo_validacao != 0:
        return codigo_validacao

    itens_manifesto: list[dict] = []
    max_paginas_excedido = False

    for item in itens_ativos:
        dest = raiz / item.destino
        dest.parent.mkdir(parents=True, exist_ok=True)

        if item.tipo == "copia":
            orig = raiz / item.origem
            conteudo_bytes = orig.read_bytes()
            estado = gravar_se_diferente(dest, conteudo_bytes)
            sha = hashlib.sha256(conteudo_bytes).hexdigest()
            itens_manifesto.append(
                {
                    "destino": Path(item.destino).as_posix(),
                    "origem": Path(item.origem).as_posix(),
                    "sha256": sha,
                    "paginas": None,
                    "estado": estado,
                }
            )

        elif item.tipo == "copia_dados":
            assert dados is not None
            orig = dados / item.origem
            conteudo_bytes = orig.read_bytes()
            estado = gravar_se_diferente(dest, conteudo_bytes)
            sha = hashlib.sha256(conteudo_bytes).hexdigest()
            origem_posix = Path(item.origem).as_posix()
            itens_manifesto.append(
                {
                    "destino": Path(item.destino).as_posix(),
                    "origem": f"DADOS/{origem_posix}",
                    "sha256": sha,
                    "paginas": None,
                    "estado": estado,
                }
            )

        elif item.tipo == "texto_gerado":
            conteudo_str = item.conteudo or ""
            conteudo_bytes = conteudo_str.encode("utf-8")
            estado = gravar_se_diferente(dest, conteudo_bytes)
            sha = hashlib.sha256(conteudo_bytes).hexdigest()
            itens_manifesto.append(
                {
                    "destino": Path(item.destino).as_posix(),
                    "origem": item.origem or "(declarado)",
                    "sha256": sha,
                    "paginas": None,
                    "estado": estado,
                }
            )

        elif item.tipo == "pdf":
            orig = raiz / item.origem
            dest_html = orig.with_suffix(".html")
            dest_pdf = dest

            pdf_existia = dest_pdf.is_file()
            up_to_date = False
            if pdf_existia and dest_html.is_file():
                mtime_pdf = dest_pdf.stat().st_mtime
                mtime_md = orig.stat().st_mtime
                texto_md = orig.read_text(encoding="utf-8")
                imagens = extrair_imagens_relativas(texto_md)
                mtimes_dep = [mtime_md] + [
                    (orig.parent / img).resolve().stat().st_mtime for img in imagens
                ]
                if mtime_pdf >= max(mtimes_dep):
                    up_to_date = True

            if up_to_date:
                estado = "inalterado"
            else:
                estado = "atualizado" if pdf_existia else "criado"
                texto_md = orig.read_text(encoding="utf-8")
                html_conteudo = converter_md_para_html(texto_md, titulo=orig.stem)
                dest_html.write_text(html_conteudo, encoding="utf-8")
                try:
                    gerar_pdf(dest_html, dest_pdf)
                except (FileNotFoundError, RuntimeError, subprocess.TimeoutExpired) as erro:
                    print(f"ERRO: PDF de {item.origem} não gerado: {erro}", file=sys.stderr)
                    return 2

            paginas = contar_paginas(dest_pdf)
            if item.max_paginas is not None and paginas > item.max_paginas:
                print(
                    f"AVISO: {item.destino} tem {paginas} páginas, "
                    f"acima do limite de {item.max_paginas}",
                    file=sys.stderr,
                )
                max_paginas_excedido = True

            sha = calcular_sha256(dest_pdf)
            itens_manifesto.append(
                {
                    "destino": Path(item.destino).as_posix(),
                    "origem": Path(item.origem).as_posix(),
                    "sha256": sha,
                    "paginas": paginas,
                    "estado": estado,
                }
            )

    itens_manifesto.sort(key=lambda x: x["destino"])
    manifesto_caminho = raiz / "docs/entregas_manifesto.json"
    agora_utc = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    dados_manifesto = {
        "gerado_em": agora_utc,
        "itens": itens_manifesto,
    }
    conteudo_manifesto = json.dumps(dados_manifesto, indent=2, ensure_ascii=False) + "\n"
    gravar_atomico(manifesto_caminho, conteudo_manifesto.encode("utf-8"))

    imprimir_tabela(itens_manifesto)

    if max_paginas_excedido:
        return 1
    return 0


def verificar(
    raiz: Path,
    dados: Path | None = None,
    itens: list[ItemEntrega] | None = None,
    sem_pdf: bool = False,
) -> int:
    if itens is None:
        itens = itens_padrao()

    itens_ativos = [i for i in itens if not (sem_pdf and i.tipo == "pdf")]

    precisa_dados = any(i.tipo == "copia_dados" for i in itens_ativos)
    if precisa_dados and dados is None:
        print(
            "ERRO: diretório de dados não informado (defina CITIZENTECH_DADOS ou use --dados)",
            file=sys.stderr,
        )
        return 2

    falhas: list[str] = []

    for item in itens_ativos:
        dest = raiz / item.destino
        if not dest.is_file():
            falhas.append(f"{item.destino}: arquivo de destino ausente")
            continue

        if item.tipo == "copia":
            orig = raiz / item.origem
            if not orig.is_file():
                falhas.append(f"{item.destino}: origem ausente ({item.origem})")
            elif dest.read_bytes() != orig.read_bytes():
                falhas.append(f"{item.destino}: conteúdo divergente da origem ({item.origem})")

        elif item.tipo == "copia_dados":
            assert dados is not None
            orig = dados / item.origem
            if not orig.is_file():
                falhas.append(f"{item.destino}: origem em dados ausente ({item.origem})")
            else:
                if dest.read_bytes() != orig.read_bytes():
                    falhas.append(
                        f"{item.destino}: conteúdo divergente da base em dados ({item.origem})"
                    )
                if item.sha256_esperado:
                    sha_dest = calcular_sha256(dest)
                    if sha_dest != item.sha256_esperado:
                        falhas.append(
                            f"{item.destino}: SHA-256 {sha_dest} diverge do esperado "
                            f"{item.sha256_esperado}"
                        )

        elif item.tipo == "texto_gerado":
            esperado = (item.conteudo or "").encode("utf-8")
            if dest.read_bytes() != esperado:
                falhas.append(f"{item.destino}: conteúdo divergente do texto gerado esperado")

        elif item.tipo == "pdf":
            orig = raiz / item.origem
            if not orig.is_file():
                falhas.append(f"{item.destino}: Markdown de origem ausente ({item.origem})")
            elif dest.stat().st_mtime < orig.stat().st_mtime:
                falhas.append(f"{item.destino}: PDF desatualizado em relação a {item.origem}")

    if falhas:
        print("ERRO: Verificação de entregas encontrou inconformidades:", file=sys.stderr)
        for falha in falhas:
            print(f"  - {falha}", file=sys.stderr)
        return 1

    print("OK: Todas as entregas estão atualizadas e íntegras.")
    return 0


def main(argumentos: list[str] | None = None, itens: list[ItemEntrega] | None = None) -> int:
    analisador = argparse.ArgumentParser(
        description="Empacotador de entregas das pastas 0X_* e gerador de PDFs."
    )
    padrao_raiz = Path(__file__).resolve().parents[2]
    analisador.add_argument(
        "--raiz",
        type=Path,
        default=padrao_raiz,
        help="Raiz do repositório (padrão: dois níveis acima do script)",
    )
    analisador.add_argument(
        "--dados",
        type=Path,
        default=None,
        help="Diretório de dados grandes (padrão: $env:CITIZENTECH_DADOS)",
    )
    analisador.add_argument(
        "--verificar",
        action="store_true",
        help="Apenas verifica se as cópias e PDFs estão atualizados",
    )
    analisador.add_argument(
        "--sem-pdf",
        action="store_true",
        help="Pula a geração e verificação de PDFs",
    )
    opcoes = analisador.parse_args(argumentos)

    raiz = opcoes.raiz.resolve()
    dados = opcoes.dados
    if dados is None:
        env_dados = os.environ.get("CITIZENTECH_DADOS")
        if env_dados:
            dados = Path(env_dados)
    if dados is not None:
        dados = dados.resolve()

    if itens is None:
        itens = itens_padrao()

    if opcoes.verificar:
        return verificar(raiz=raiz, dados=dados, itens=itens, sem_pdf=opcoes.sem_pdf)
    return empacotar(raiz=raiz, dados=dados, itens=itens, sem_pdf=opcoes.sem_pdf)


if __name__ == "__main__":
    sys.exit(main())
