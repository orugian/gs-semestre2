"""Script para empacotar a funcao Lambda de ingestao em um arquivo .zip para deploy na AWS."""

import argparse
import hashlib
import importlib.metadata as md
import re
import sys
import zipfile
from pathlib import Path


def coletar_dependencias_recursivas(pacote_raiz: str = "pg8000") -> set[str]:
    """Descobre recursivamente todas as dependencias de um pacote."""
    visitados = set()
    fila = [pacote_raiz]

    while fila:
        pkg = fila.pop(0)
        if pkg.lower() in visitados:
            continue
        visitados.add(pkg.lower())

        try:
            reqs = md.requires(pkg) or []
        except md.PackageNotFoundError:
            continue

        for req in reqs:
            if "extra ==" in req:
                continue
            m = re.match(r"^([A-Za-z0-9_\-\.]+)", req.strip())
            if m:
                dep_nome = m.group(1).strip()
                if dep_nome.lower() not in visitados:
                    try:
                        md.version(dep_nome)
                        fila.append(dep_nome)
                    except md.PackageNotFoundError:
                        pass

    return visitados


def empacotar(saida_dir: Path, ca_path: Path | None = None) -> Path:
    """Gera o arquivo funcao_lambda.zip contendo handler, modulos e dependencias puras Python."""
    saida_dir.mkdir(parents=True, exist_ok=True)
    zip_path = saida_dir / "funcao_lambda.zip"

    raiz_cloud = Path(__file__).resolve().parent
    src_cloud = raiz_cloud / "src" / "citizentech_cloud"

    # Verificar limiares de origem (app/config/limiares.json)
    limiares_origem = raiz_cloud.parent / "config" / "limiares.json"
    if not limiares_origem.is_file():
        limiares_origem = src_cloud / "limiares.json"
    if not limiares_origem.is_file():
        raise FileNotFoundError(f"Arquivo limiares.json nao encontrado em {limiares_origem}")

    # Verificar dependencias e presenca de binarios
    deps = coletar_dependencias_recursivas("pg8000")
    arquivos_deps: list[tuple[Path, str]] = []

    for dep in deps:
        try:
            files = md.files(dep) or []
        except md.PackageNotFoundError:
            continue

        for f in files:
            nome_str = str(f)
            # Checagem estrita de binarios compilados
            if nome_str.lower().endswith((".pyd", ".so", ".dll")):
                sys.stderr.write(
                    f"Erro: Dependencia '{dep}' contem arquivo binario nativo: {nome_str}\n"
                )
                sys.exit(2)

            # Ignora dist-info metadata de teste/installer se quiser
            # Para execucao, precisamos dos pacotes/modulos python e arquivos de dados
            caminho_real = Path(f.locate())
            if caminho_real.is_file() and "__pycache__" not in nome_str:
                arquivos_deps.append((caminho_real, nome_str))

    # Criar arquivo ZIP
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        # 1. lambda_function.py na RAIZ do zip
        handler_src = src_cloud / "lambda_function.py"
        zipf.write(handler_src, arcname="lambda_function.py")

        # 2. Pacote citizentech_cloud/
        modulos = ["__init__.py", "risco.py", "sentimento.py", "banco.py", "lambda_function.py"]
        for mod in modulos:
            mod_path = src_cloud / mod
            if mod_path.is_file():
                zipf.write(mod_path, arcname=f"citizentech_cloud/{mod}")

        # Copia de limiares.json dentro de citizentech_cloud/ (D20)
        zipf.write(limiares_origem, arcname="citizentech_cloud/limiares.json")

        # 3. Certificado CA se fornecido
        if ca_path and ca_path.is_file():
            # Nome fixo: banco.py procura citizentech_cloud/global-bundle.pem (D09 verify-full)
            zipf.write(ca_path, arcname="citizentech_cloud/global-bundle.pem")

        # 4. Dependencias pure-python
        for caminho_real, arcname in arquivos_deps:
            # Evita sobrescrever se ja inserido
            try:
                zipf.getinfo(arcname)
            except KeyError:
                zipf.write(caminho_real, arcname=arcname)

    return zip_path


def calcular_sha256(caminho: Path) -> str:
    hasher = hashlib.sha256()
    with open(caminho, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Empacotador da AWS Lambda CitizenTech")
    parser.add_argument("--saida", required=True, help="Diretorio de saida do pacote .zip")
    parser.add_argument(
        "--ca", default=None, help="Caminho do arquivo global-bundle.pem (opcional)"
    )

    args = parser.parse_args(argv)
    saida_dir = Path(args.saida)
    ca_path = Path(args.ca) if args.ca else None

    if ca_path and not ca_path.is_file():
        sys.stderr.write(f"Erro: Arquivo CA especificado nao existe: {ca_path}\n")
        return 1

    try:
        zip_path = empacotar(saida_dir, ca_path)
    except SystemExit:
        raise
    except Exception as e:
        sys.stderr.write(f"Erro ao empacotar: {e}\n")
        return 1

    # Imprime lista de arquivos e hash SHA-256
    sha256 = calcular_sha256(zip_path)
    print("=== Arquivos no pacote funcao_lambda.zip ===")
    with zipfile.ZipFile(zip_path, "r") as z:
        for info in z.infolist():
            print(f" - {info.filename} ({info.file_size} bytes)")

    print(f"\nPacote gerado com sucesso: {zip_path}")
    print(f"SHA-256: {sha256}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
