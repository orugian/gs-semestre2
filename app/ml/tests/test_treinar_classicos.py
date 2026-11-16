"""Testes da CLI e persistência de artefatos com manifesto (S7-classicos)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from citizentech_ml.classicos import treinar_classicos
from citizentech_ml.features.datas import gerar_intervalo_meses
from citizentech_ml.features.extracao import COLUNAS_FEATURES
from citizentech_ml.treinar_classicos import (
    carregar_artefatos_classicos,
    salvar_artefatos_classicos,
)


def _criar_painel_mvp_arquivo(
    caminho_parquet: Path,
    inicio: str = "202101",
    fim: str = "202409",
) -> Path:
    """Gera um arquivo Parquet sintético no padrão do MVP para testes de CLI e persistência."""
    meses = gerar_intervalo_meses(inicio, fim)
    destinos = ("analista_dados_bi", "analista_monitoramento_iot", "analista_processos")
    ufs = ("35", "33")
    colunas_num = [c for c in COLUNAS_FEATURES if "_total" not in c and c != "mes"]

    linhas = []
    for m in meses:
        mes_num = int(m[-2:])
        for dest in destinos:
            for uf in ufs:
                linha = {
                    "competencia": m,
                    "destino": dest,
                    "uf": uf,
                    "mes": mes_num,
                    "alvo": 30.0,
                    "admissoes_soma_3m": 30.0,
                    "admissoes_sazonal_ano_anterior": 30.0,
                    "previsao_persistencia": 30.0,
                    "previsao_sazonal": 30.0,
                }
                for c in colunas_num:
                    linha[c] = 30.0
                linhas.append(linha)

    df = pd.DataFrame(linhas)
    df.to_parquet(caminho_parquet, index=False)
    return caminho_parquet


def test_salvar_e_carregar_artefatos_classicos(tmp_path: Path) -> None:
    """Grava artefatos com manifesto e recarrega verificando hash."""
    p_painel = _criar_painel_mvp_arquivo(tmp_path / "painel.parquet")
    df_painel = pd.read_parquet(p_painel)

    resultado = treinar_classicos(df_painel, seed=42, n_iter=1, n_splits=2)
    dir_saida = tmp_path / "artefatos_classicos"

    salvar_artefatos_classicos(
        resultado=resultado,
        caminho_painel=p_painel,
        dir_saida=dir_saida,
        seed=42,
        n_iter=1,
    )

    # Verificar existência de arquivos
    assert (dir_saida / "modelos.joblib").exists()
    assert (dir_saida / "previsoes.parquet").exists()
    assert (dir_saida / "previsoes.csv").exists()
    assert (dir_saida / "metricas.json").exists()
    assert (dir_saida / "manifesto.json").exists()

    # Verificar manifesto
    manifesto_texto = (dir_saida / "manifesto.json").read_text(encoding="utf-8")
    manifesto = json.loads(manifesto_texto)
    assert manifesto["data_utc"].endswith("Z")
    assert manifesto["sha256_painel"] is not None
    assert "modelos.joblib" in manifesto["arquivos"]

    # Carregar via loader público seguro
    carregado = carregar_artefatos_classicos(dir_saida)
    assert "estimadores" in carregado
    assert set(carregado["estimadores"].keys()) == {
        "ridge",
        "random_forest",
        "hist_gradient_boosting",
    }
    assert isinstance(carregado["previsoes"], pd.DataFrame)
    assert "folds" in carregado["relatorio"]


def test_recusa_desserializacao_sem_manifesto(tmp_path: Path) -> None:
    """Recusa carregamento se o manifesto estiver ausente."""
    p_painel = _criar_painel_mvp_arquivo(tmp_path / "painel.parquet")
    df_painel = pd.read_parquet(p_painel)
    resultado = treinar_classicos(df_painel, seed=42, n_iter=1, n_splits=2)
    dir_saida = tmp_path / "artefatos_sem_manifesto"

    salvar_artefatos_classicos(resultado, p_painel, dir_saida)

    # Deletar manifesto
    (dir_saida / "manifesto.json").unlink()

    with pytest.raises(FileNotFoundError, match="Manifesto não encontrado"):
        carregar_artefatos_classicos(dir_saida)


def test_recusa_desserializacao_se_arquivo_alterado(tmp_path: Path) -> None:
    """Detecta alteração no arquivo e recusa desserialização por falha de integridade."""
    p_painel = _criar_painel_mvp_arquivo(tmp_path / "painel.parquet")
    df_painel = pd.read_parquet(p_painel)
    resultado = treinar_classicos(df_painel, seed=42, n_iter=1, n_splits=2)
    dir_saida = tmp_path / "artefatos_alterados"

    salvar_artefatos_classicos(resultado, p_painel, dir_saida)

    # Adulterar o modelos.joblib
    p_modelos = dir_saida / "modelos.joblib"
    bytes_originais = p_modelos.read_bytes()
    p_modelos.write_bytes(bytes_originais + b"bytes_corruptos")

    with pytest.raises(ValueError, match="Falha de integridade: hash do arquivo"):
        carregar_artefatos_classicos(dir_saida)


def test_cli_executa_e_grava_artefatos(tmp_path: Path) -> None:
    """Executa a CLI via subprocess e valida que os artefatos são gerados corretamente."""
    p_painel = _criar_painel_mvp_arquivo(tmp_path / "painel_cli.parquet")
    dir_saida = tmp_path / "saida_cli"

    cmd = [
        sys.executable,
        "-m",
        "citizentech_ml.treinar_classicos",
        "--painel",
        str(p_painel),
        "--saida",
        str(dir_saida),
        "--seed",
        "42",
        "--n-iter",
        "1",
        "--n-splits",
        "2",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode == 0, f"CLI falhou: {proc.stderr}"
    assert dir_saida.exists()
    assert (dir_saida / "manifesto.json").exists()

    # Loader valida integridade
    carregado = carregar_artefatos_classicos(dir_saida)
    assert set(carregado["estimadores"].keys()) == {
        "ridge",
        "random_forest",
        "hist_gradient_boosting",
    }


def test_cli_recusa_diretorio_existente(tmp_path: Path) -> None:
    """CLI recusa executar se o diretório de saída já existir (sem sobrescrever)."""
    p_painel = _criar_painel_mvp_arquivo(tmp_path / "painel_cli.parquet")
    dir_saida = tmp_path / "saida_existente"
    dir_saida.mkdir()
    arquivo_sentinela = dir_saida / "arquivo.txt"
    arquivo_sentinela.write_text("nao_alterar", encoding="utf-8")

    cmd = [
        sys.executable,
        "-m",
        "citizentech_ml.treinar_classicos",
        "--painel",
        str(p_painel),
        "--saida",
        str(dir_saida),
        "--n-iter",
        "1",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode != 0
    assert "Diretório de saída já existente" in proc.stderr
    assert arquivo_sentinela.read_text(encoding="utf-8") == "nao_alterar"


def test_cli_recusa_dados_2026(tmp_path: Path) -> None:
    """CLI recusa painel com competência >= 202601."""
    p_painel = _criar_painel_mvp_arquivo(tmp_path / "painel_2026.parquet")
    df = pd.read_parquet(p_painel)
    linha_2026 = df.iloc[0:1].copy()
    linha_2026["competencia"] = "202601"
    pd.concat([df, linha_2026], ignore_index=True).to_parquet(p_painel, index=False)

    dir_saida = tmp_path / "saida_invalida"

    cmd = [
        sys.executable,
        "-m",
        "citizentech_ml.treinar_classicos",
        "--painel",
        str(p_painel),
        "--saida",
        str(dir_saida),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode != 0
    assert "holdout 2026" in proc.stderr


def test_cli_suporta_flag_validacao(tmp_path: Path) -> None:
    """CLI com flag --validacao inclui métricas da partição 2025."""
    p_painel = _criar_painel_mvp_arquivo(
        tmp_path / "painel_val.parquet", inicio="202101", fim="202509"
    )
    dir_saida = tmp_path / "saida_val"

    cmd = [
        sys.executable,
        "-m",
        "citizentech_ml.treinar_classicos",
        "--painel",
        str(p_painel),
        "--saida",
        str(dir_saida),
        "--validacao",
        "--n-iter",
        "1",
        "--n-splits",
        "2",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode == 0, f"CLI falhou: {proc.stderr}"

    carregado = carregar_artefatos_classicos(dir_saida)
    assert carregado["relatorio"]["validacao_externa"] is not None
    assert (carregado["previsoes"]["particao"] == "validacao").any()
