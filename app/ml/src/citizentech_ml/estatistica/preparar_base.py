"""CLI para preparação e congelamento da base municipal anual (2024-2025)."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from citizentech_ml.estatistica.base_municipal import carregar_base_municipal


def _calcular_sha256_arquivo(caminho: Path) -> str:
    """Calcula hash SHA256 de um arquivo."""
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def preparar_base(
    caminho_parquets: str | Path,
    caminho_mapa: str | Path,
    caminho_saida: str | Path,
) -> dict[str, Any]:
    """Executa a preparação e exportação da base municipal.

    Regras:
    - Valida existência de parquets e mapa antes de qualquer operação.
    - Não sobrescreve diretório de saída existente (FileExistsError).
    - Gera CSV UTF-8 sem BOM e manifesto JSON com hashes e procedência.
    """
    p_saida = Path(caminho_saida).resolve()
    if p_saida.exists():
        raise FileExistsError(
            f"Diretório de saída já existe e não pode ser sobrescrito: {caminho_saida}"
        )

    p_mapa = Path(caminho_mapa).resolve()
    if not p_mapa.exists() or not p_mapa.is_file():
        raise FileNotFoundError(f"Arquivo de mapa não encontrado: {caminho_mapa}")

    p_parquets = Path(caminho_parquets).resolve()
    if not p_parquets.exists() or not p_parquets.is_dir():
        raise FileNotFoundError(f"Diretório de parquets não encontrado: {caminho_parquets}")

    # Lê mapa JSON
    with open(p_mapa, encoding="utf-8") as f:
        mapa_dict = json.load(f)
    mapa_sha256 = _calcular_sha256_arquivo(p_mapa)

    # Carrega e agrega base municipal
    base_df, relatorio = carregar_base_municipal(p_parquets, mapa_dict)

    # Cria diretório de saída exclusivamente após validações
    p_saida.mkdir(parents=True, exist_ok=False)

    # Exporta CSV UTF-8 sem BOM
    arq_csv = p_saida / "base_municipal.csv"
    base_df.to_csv(arq_csv, index=False, encoding="utf-8")
    csv_sha256 = _calcular_sha256_arquivo(arq_csv)

    # Monta manifesto JSON
    timestamp_utc = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    manifesto = {
        "timestamp_utc": timestamp_utc,
        "hashes": {
            "mapa_sha256": mapa_sha256,
            "csv_sha256": csv_sha256,
            "fontes_sha256": relatorio.get("hashes_fontes", {}),
        },
        "fontes_72": relatorio.get("fontes_planejadas", []),
        "relatorio": relatorio,
    }

    # Grava manifesto JSON UTF-8 sem BOM
    arq_manifesto = p_saida / "manifesto.json"
    with open(arq_manifesto, "w", encoding="utf-8") as f:
        json.dump(manifesto, f, indent=2, ensure_ascii=False)

    return manifesto


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada da CLI preparar_base."""
    parser = argparse.ArgumentParser(
        description="Prepara a base municipal anual (2024-2025) a partir dos parquets CAGED."
    )
    parser.add_argument(
        "--parquets",
        required=True,
        type=Path,
        help="Diretório contendo os 72 arquivos Parquet oficiais.",
    )
    parser.add_argument(
        "--mapa",
        required=True,
        type=Path,
        help="Arquivo JSON com o mapa mínimo de 6 destinos científicos.",
    )
    parser.add_argument(
        "--saida",
        required=True,
        type=Path,
        help="Novo diretório para gravação da base municipal e do manifesto.",
    )

    args = parser.parse_args(argv)
    preparar_base(args.parquets, args.mapa, args.saida)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
