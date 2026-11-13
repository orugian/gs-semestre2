"""CLI para execução da ingestão do Novo Caged."""

import argparse
import os
import sys
from pathlib import Path

from citizentech_ml.ingestao.ingestor import ingerir_periodo
from citizentech_ml.ingestao.ocupacoes import carregar_ocupacoes


def construir_parser() -> argparse.ArgumentParser:
    """Constrói o parser de argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="Ingestão de microdados do Novo Caged em formato Parquet."
    )
    parser.add_argument(
        "--ocupacoes",
        required=True,
        help="Caminho para o JSON com a lista de CBOs elegíveis.",
    )
    parser.add_argument(
        "--inicio",
        required=True,
        help="Competência inicial no formato AAAAMM (ex: 202001).",
    )
    parser.add_argument(
        "--fim",
        required=True,
        help="Competência final no formato AAAAMM (ex: 202609).",
    )
    parser.add_argument(
        "--dados",
        default=None,
        help="Diretório de dados (se omitido, utiliza $env:CITIZENTECH_DADOS).",
    )
    parser.add_argument(
        "--reprocessar",
        action="store_true",
        help="Força reprocessamento de arquivos já ingeridos.",
    )
    return parser


def main(args: list[str] | None = None) -> int:
    """Ponto de entrada da CLI."""
    parser = construir_parser()
    parsed = parser.parse_args(args)

    dir_dados_str = parsed.dados or os.environ.get("CITIZENTECH_DADOS")
    if not dir_dados_str:
        print(
            "Erro: Diretório de dados não informado via --dados e "
            "$env:CITIZENTECH_DADOS não está definido.",
            file=sys.stderr,
        )
        return 1

    caminho_dados = Path(dir_dados_str)
    caminho_ocupacoes = Path(parsed.ocupacoes)

    try:
        ocupacoes = carregar_ocupacoes(caminho_ocupacoes)
    except Exception as exc:
        print(f"Erro ao carregar ocupações: {exc}", file=sys.stderr)
        return 1

    print(f"Iniciando ingestao Novo Caged ({parsed.inicio} ate {parsed.fim})...")
    print(f"Ocupacoes: versao={ocupacoes.versao}, hash={ocupacoes.hash[:10]}...")
    print(f"Diretorio de destino: {caminho_dados}")
    print("-" * 75)

    try:
        resumo = ingerir_periodo(
            inicio=parsed.inicio,
            fim=parsed.fim,
            ocupacoes=ocupacoes,
            dir_dados=caminho_dados,
            reprocessar=parsed.reprocessar,
        )
    except Exception as exc:
        print(f"Falha/aborto durante ingestao: {exc}", file=sys.stderr)
        return 1

    for reg in resumo.registros:
        print(
            f"{reg.tipo:<3} {reg.competencia_arquivo:<6} | "
            f"lidas: {reg.linhas_lidas:<8} | "
            f"gravadas: {reg.linhas_gravadas:<8} | "
            f"situacao: {reg.situacao}"
        )

    print("-" * 75)
    print(
        f"Resumo da ingestao: {resumo.total_processados} arquivos verificados, "
        f"{resumo.total_ingeridos} ingeridos, "
        f"{resumo.total_ausentes} ausentes na fonte, "
        f"{resumo.total_falhas} falhas."
    )

    if not resumo.sucesso or resumo.total_falhas > 0:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
