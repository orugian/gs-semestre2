"""Gerador do header C++ de limiares a partir de app/config/limiares.json (D20)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _comum import sha256_arquivo as calcular_sha256


def renderizar_header(conteudo_json: dict, sha256_origem: str) -> str:
    """Gera o texto em C++ do header de limiares."""
    metricas = conteudo_json.get("metricas", {})
    temp = metricas.get("temperatura_c", {})
    dist = metricas.get("distancia_cm", {})

    # Limiares só existem em app/config/limiares.json: chave ausente falha em vez de usar padrão.
    temp_atencao = float(temp["atencao"])
    temp_critico = float(temp["critico"])
    dist_atencao = float(dist["atencao"])
    dist_critico = float(dist["critico"])
    dist_minimo = float(dist.get("valor_minimo", 0.0))

    linhas = [
        "#ifndef LIMIARES_H",
        "#define LIMIARES_H",
        "",
        "// ARQUIVO GERADO AUTOMATICAMENTE A PARTIR DE app/config/limiares.json",
        "// NAO EDITAR ESTE ARQUIVO MANUALMENTE (D20).",
        f"// SHA-256 de origem: {sha256_origem}",
        "",
        f'#define LIMIARES_JSON_SHA256 "{sha256_origem}"',
        "",
        f"#define LIMIAR_TEMPERATURA_ATENCAO {temp_atencao:.1f}f",
        f"#define LIMIAR_TEMPERATURA_CRITICO {temp_critico:.1f}f",
        f"#define LIMIAR_DISTANCIA_ATENCAO {dist_atencao:.1f}f",
        f"#define LIMIAR_DISTANCIA_CRITICO {dist_critico:.1f}f",
        f"#define LIMIAR_DISTANCIA_MINIMO {dist_minimo:.1f}f",
        "",
        "#endif // LIMIARES_H",
        "",
    ]
    return "\n".join(linhas)


def gerar_conteudo_esperado(json_path: Path) -> tuple[str, str]:
    """Retorna (conteudo_header, sha256_origem) para o arquivo JSON especificado."""
    sha256_origem = calcular_sha256(json_path)
    with json_path.open("r", encoding="utf-8") as f:
        dados = json.load(f)
    conteudo = renderizar_header(dados, sha256_origem)
    return conteudo, sha256_origem


def verificar_header(json_path: Path, header_path: Path) -> bool:
    """Retorna True se o header em disco for identico ao gerado a partir do JSON."""
    if not header_path.is_file():
        return False
    esperado, _ = gerar_conteudo_esperado(json_path)
    conteudo_atual = header_path.read_text(encoding="utf-8")
    return conteudo_atual == esperado


def escrever_header(json_path: Path, header_path: Path) -> None:
    """Gera e grava o header no caminho de destino."""
    conteudo, _ = gerar_conteudo_esperado(json_path)
    header_path.parent.mkdir(parents=True, exist_ok=True)
    header_path.write_text(conteudo, encoding="utf-8", newline="\n")


def resolver_caminhos_padrao() -> tuple[Path, Path]:
    """Resolve caminhos padrão a partir da raiz do repositório."""
    tools_dir = Path(__file__).resolve().parent
    repo_root = tools_dir.parent.parent
    json_path = repo_root / "app" / "config" / "limiares.json"
    header_path = repo_root / "app" / "iot" / "firmware" / "limiares.h"
    return json_path, header_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Gera ou verifica o header C++ de limiares (limiares.h)."
    )
    parser.add_argument(
        "--verificar",
        action="store_true",
        help="Verifica se o header existente corresponde exatamente ao JSON de origem.",
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=None,
        help="Caminho do limiares.json (padrao: app/config/limiares.json)",
    )
    parser.add_argument(
        "--header",
        type=Path,
        default=None,
        help="Caminho do limiares.h (padrao: app/iot/firmware/limiares.h)",
    )

    args = parser.parse_args(argv)

    json_padrao, header_padrao = resolver_caminhos_padrao()
    json_path = args.json or json_padrao
    header_path = args.header or header_padrao

    if not json_path.is_file():
        sys.stderr.write(f"Erro: arquivo JSON nao encontrado: {json_path}\n")
        return 1

    if args.verificar:
        if not verificar_header(json_path, header_path):
            sys.stderr.write(
                f"Erro: header {header_path} diverge de {json_path} ou nao existe.\n"
            )
            return 1
        return 0

    escrever_header(json_path, header_path)
    print(f"Header gerado com sucesso em {header_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
