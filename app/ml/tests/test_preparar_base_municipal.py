"""Testes unitários e de integração para a CLI preparar_base."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from citizentech_ml.estatistica.base_municipal import (
    COLUNAS_MINIMAS,
    MESES_CANONICOS,
    TIPOS_CANONICOS,
)
from citizentech_ml.estatistica.preparar_base import main, preparar_base

MAPA_MINIMO = {
    "destinos": {
        "analista_dados_bi": {"cbo6": ["211205"]},
        "analista_monitoramento_iot": {"cbo6": ["211210"]},
        "analista_processos": {"cbo6": ["212405"]},
        "gerente_projetos_produto": {"cbo6": ["142105"]},
        "analista_suporte_infra": {"cbo6": ["212420"]},
        "desenvolvedor_sistemas": {"cbo6": ["212410"]},
    }
}


def _criar_fixture_parquets(dir_parquets: Path) -> None:
    """Cria os 72 arquivos Parquet para teste do CLI."""
    for comp in MESES_CANONICOS:
        for tipo in TIPOS_CANONICOS:
            linhas = []
            if comp == "202401" and tipo == "MOV":
                for _ in range(12):
                    linhas.append({
                        "municipio": "355030", "uf": "35", "cbo2002_ocupacao": "211205",
                        "saldo_movimentacao": 1, "grau_instrucao": 9, "salario": 5000.0,
                        "arquivo_tipo": "MOV", "competencia_mov": "202401",
                        "competencia_dec": "202401", "competencia_exc": None,
                        "competencia_arquivo": "202401",
                    })
            elif comp == "202501" and tipo == "MOV":
                for _ in range(15):
                    linhas.append({
                        "municipio": "355030", "uf": "35", "cbo2002_ocupacao": "211205",
                        "saldo_movimentacao": 1, "grau_instrucao": 9, "salario": 6000.0,
                        "arquivo_tipo": "MOV", "competencia_mov": "202501",
                        "competencia_dec": "202501", "competencia_exc": None,
                        "competencia_arquivo": "202501",
                    })
            df = pd.DataFrame(linhas, columns=COLUNAS_MINIMAS)
            df.to_parquet(dir_parquets / f"CAGED{tipo}{comp}.parquet", index=False)


def test_cli_help(capsys):
    """CLI deve responder a --help com parâmetros obrigatórios."""
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "--parquets" in captured.out
    assert "--mapa" in captured.out
    assert "--saida" in captured.out


def test_preparar_base_recusa_sobrescrever_diretorio_existente(tmp_path: Path):
    """Não sobrescrever diretório existente; validar antes de criar saída."""
    dir_saida = tmp_path / "saida_existente"
    dir_saida.mkdir()

    arq_mapa = tmp_path / "mapa.json"
    arq_mapa.write_text(json.dumps(MAPA_MINIMO), encoding="utf-8")

    with pytest.raises(FileExistsError, match="já existe"):
        preparar_base(tmp_path, arq_mapa, dir_saida)


def test_preparar_base_valida_existencia_parquets_e_mapa(tmp_path: Path):
    """Valida que entradas inexistentes geram FileNotFoundError antes de criar saída."""
    dir_saida = tmp_path / "saida_nova"
    arq_mapa = tmp_path / "mapa.json"
    arq_mapa.write_text(json.dumps(MAPA_MINIMO), encoding="utf-8")

    # Parquets não existe
    with pytest.raises(FileNotFoundError, match="parquets"):
        preparar_base(tmp_path / "inexistente", arq_mapa, dir_saida)
    assert not dir_saida.exists()

    # Mapa não existe
    dir_parquets = tmp_path / "parquets"
    dir_parquets.mkdir()
    with pytest.raises(FileNotFoundError, match="mapa"):
        preparar_base(dir_parquets, tmp_path / "mapa_inexistente.json", dir_saida)
    assert not dir_saida.exists()


def test_preparar_base_cli_executa_e_gera_csv_e_manifesto(tmp_path: Path):
    """Execução completa do CLI gerando CSV sem BOM e manifesto com hashes."""
    dir_parquets = tmp_path / "parquets"
    dir_parquets.mkdir()
    _criar_fixture_parquets(dir_parquets)

    arq_mapa = tmp_path / "mapa.json"
    arq_mapa.write_text(json.dumps(MAPA_MINIMO), encoding="utf-8")

    dir_saida = tmp_path / "saida_nova"

    # Executa via CLI
    codigo = main([
        "--parquets", str(dir_parquets),
        "--mapa", str(arq_mapa),
        "--saida", str(dir_saida),
    ])
    assert codigo == 0

    # Verifica CSV
    arq_csv = dir_saida / "base_municipal.csv"
    assert arq_csv.exists()
    conteudo_bytes = arq_csv.read_bytes()
    # UTF-8 sem BOM (BOM seria b'\xef\xbb\xbf')
    assert not conteudo_bytes.startswith(b"\xef\xbb\xbf")

    df_lido = pd.read_csv(arq_csv, dtype={"municipio": str, "uf": str})
    assert len(df_lido) == 1
    assert df_lido.iloc[0]["municipio"] == "355030"
    assert df_lido.iloc[0]["admissoes_2024"] == 12
    assert df_lido.iloc[0]["admissoes_2025"] == 15

    # Verifica Manifesto JSON
    arq_manifesto = dir_saida / "manifesto.json"
    assert arq_manifesto.exists()
    manifesto_bytes = arq_manifesto.read_bytes()
    assert not manifesto_bytes.startswith(b"\xef\xbb\xbf")

    manifesto = json.loads(manifesto_bytes.decode("utf-8"))
    assert "hashes" in manifesto
    assert "mapa_sha256" in manifesto["hashes"]
    assert "csv_sha256" in manifesto["hashes"]
    assert "fontes_sha256" in manifesto["hashes"]
    assert len(manifesto["hashes"]["fontes_sha256"]) == 72
    assert manifesto["timestamp_utc"].endswith("Z")
    assert "relatorio" in manifesto
