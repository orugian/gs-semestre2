"""Testes da interface CLI e persistência de modelos de RNA (MLP PyTorch CPU)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch

from citizentech_ml.features.datas import gerar_intervalo_meses
from citizentech_ml.rede_neural import MLPRegressor, PreprocessadorRNA, carregar_modelo_rna
from citizentech_ml.treinar_rna import criar_parser, executar_treino_rna_cli


def _criar_painel_mvp_arquivo(caminho: Path, inicio: str = "202101", fim: str = "202409") -> Path:
    """Gera painel MVP sintético gravado em Parquet com alvos e baselines."""
    destinos = [
        "analista_dados_bi",
        "analista_monitoramento_iot",
        "analista_processos",
    ]
    ufs = ["35", "33"]
    meses = gerar_intervalo_meses(inicio, fim)

    linhas = []
    for m in meses:
        mes_num = int(m[-2:])
        for d_idx, d in enumerate(destinos):
            for u_idx, u in enumerate(ufs):
                base_val = 15.0 + (d_idx + 1) * 10.0 + (u_idx + 1) * 5.0
                alvo = base_val + 2.0 * np.sin(mes_num * np.pi / 6.0)
                linhas.append(
                    {
                        "competencia": m,
                        "mes": mes_num,
                        "destino": d,
                        "uf": u,
                        "admissoes": float(alvo / 3.0),
                        "desligamentos": float(alvo / 4.0),
                        "admissoes_lag_1": float(alvo / 3.0),
                        "admissoes_lag_2": float(alvo / 3.0),
                        "admissoes_lag_3": float(alvo / 3.0),
                        "admissoes_lag_12": float(alvo / 3.0),
                        "desligamentos_lag_1": float(alvo / 4.0),
                        "desligamentos_lag_2": float(alvo / 4.0),
                        "desligamentos_lag_3": float(alvo / 4.0),
                        "desligamentos_lag_12": float(alvo / 4.0),
                        "admissoes_soma_3m": float(alvo),
                        "admissoes_media_3m": float(alvo / 3.0),
                        "admissoes_sazonal_ano_anterior": float(alvo),
                        "alvo": float(alvo),
                    }
                )
    df = pd.DataFrame(linhas)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(caminho, index=False)
    return caminho


def test_parser_argumentos():
    """Verifica que o analisador CLI possui todos os argumentos obrigatórios e opcionais."""
    parser = criar_parser()
    args = parser.parse_args(["--painel", "painel.parquet", "--saida", "dir_saida", "--validacao"])
    assert args.painel == "painel.parquet"
    assert args.saida == "dir_saida"
    assert args.validacao is True
    assert args.max_epochs == 200
    assert args.patience == 15
    assert args.seed == 42


def test_executar_treino_rna_gera_todos_artefatos(tmp_path: Path):
    """Verifica geração completa e auditável de todos os artefatos exigidos pelo contrato."""
    p_painel = _criar_painel_mvp_arquivo(tmp_path / "dados" / "painel.parquet")
    dir_saida = tmp_path / "saida_rna"

    p_metricas, p_checkpoint = executar_treino_rna_cli(
        caminho_painel=p_painel,
        dir_saida=dir_saida,
        max_epochs=2,
        patience=2,
        seed=42,
    )

    # 1. Verifica existência dos arquivos principais
    assert dir_saida.exists()
    assert (dir_saida / "metricas.json").exists()
    assert (dir_saida / "checkpoint_rna.pt").exists()
    assert (dir_saida / "preprocessador.json").exists()
    assert (dir_saida / "previsoes.parquet").exists()
    assert (dir_saida / "previsoes.csv").exists()
    assert (dir_saida / "curvas.csv").exists()
    assert (dir_saida / "curvas.png").exists()

    # 2. Inspeciona o conteúdo de metricas.json
    with (dir_saida / "metricas.json").open("r", encoding="utf-8") as f:
        meta = json.load(f)

    assert "sha256_painel" in meta
    assert "sha256_artefatos" in meta
    assert "checkpoint_rna.pt" in meta["sha256_artefatos"]
    assert "preprocessador.json" in meta["sha256_artefatos"]
    assert "versoes" in meta
    assert meta["versoes"]["torch"] == str(torch.__version__)
    assert "cv_ranking" in meta
    assert "melhor_config" in meta
    assert "comparacao_baseline" in meta


def test_saida_ja_existente_recusa_e_mantem_intacta(tmp_path: Path):
    """Contraexemplo: saída já existente gera FileExistsError e permanece intacta."""
    p_painel = _criar_painel_mvp_arquivo(tmp_path / "dados" / "painel.parquet")
    dir_saida = tmp_path / "saida_ocupada"
    dir_saida.mkdir(parents=True, exist_ok=True)
    canary = dir_saida / "canary.txt"
    canary.write_text("intacto", encoding="utf-8")

    with pytest.raises(FileExistsError):
        executar_treino_rna_cli(
            caminho_painel=p_painel,
            dir_saida=dir_saida,
            max_epochs=2,
        )

    assert canary.read_text(encoding="utf-8") == "intacto"


def test_painel_inexistente_gera_erro(tmp_path: Path):
    """Contraexemplo: painel inexistente gera FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        executar_treino_rna_cli(
            caminho_painel=tmp_path / "nao_existe.parquet",
            dir_saida=tmp_path / "saida_teste",
        )


def test_carregar_modelo_rna_sucesso_e_recusa_hash_alterado(tmp_path: Path):
    """Contraexemplo: loader valida hashes e recusa arquivos alterados ou corrompidos."""
    p_painel = _criar_painel_mvp_arquivo(tmp_path / "dados" / "painel.parquet")
    dir_saida = tmp_path / "saida_load"

    executar_treino_rna_cli(
        caminho_painel=p_painel,
        dir_saida=dir_saida,
        max_epochs=2,
        patience=2,
        seed=42,
    )

    # 1. Carregamento com integridade intacta funciona perfeitamente
    modelo, prep, meta = carregar_modelo_rna(dir_saida)
    assert isinstance(modelo, MLPRegressor)
    assert isinstance(prep, PreprocessadorRNA)
    assert meta["melhor_config"]["nome"] in ["A", "B"]

    # 2. Corrupção do checkpoint deve ser detectada e rejeitada
    caminho_pt = dir_saida / "checkpoint_rna.pt"
    bytes_originais_pt = caminho_pt.read_bytes()
    # Modifica um byte do checkpoint
    caminho_pt.write_bytes(bytes_originais_pt + b"corrupcao")

    with pytest.raises(ValueError, match="Hash SHA-256 do checkpoint divergiu"):
        carregar_modelo_rna(dir_saida)

    # Restaura checkpoint e corrompe o pré-processador
    caminho_pt.write_bytes(bytes_originais_pt)
    caminho_prep = dir_saida / "preprocessador.json"
    texto_original_prep = caminho_prep.read_text(encoding="utf-8")
    caminho_prep.write_text(texto_original_prep + " ", encoding="utf-8")

    with pytest.raises(ValueError, match="Hash SHA-256 do pré-processador divergiu"):
        carregar_modelo_rna(dir_saida)


def test_carregar_modelo_rna_recusa_manifesto_sem_hashes_obrigatorios(tmp_path: Path):
    """Contraexemplo: loader recusa manifesto sem hashes obrigatórios ou com hashes malformados."""
    p_painel = _criar_painel_mvp_arquivo(tmp_path / "dados" / "painel.parquet")
    dir_saida = tmp_path / "saida_sem_hashes"

    executar_treino_rna_cli(
        caminho_painel=p_painel,
        dir_saida=dir_saida,
        max_epochs=2,
        patience=2,
        seed=42,
    )

    caminho_meta = dir_saida / "metricas.json"
    with caminho_meta.open("r", encoding="utf-8") as f:
        meta = json.load(f)

    # 1. Esvazia sha256_artefatos
    meta["sha256_artefatos"] = {}
    caminho_meta.write_text(json.dumps(meta), encoding="utf-8")

    with pytest.raises(ValueError, match="[Hh]ash|[Mm]anifesto"):
        carregar_modelo_rna(dir_saida)

    # 2. Hash malformado (não-hexadecimal de 64 caracteres)
    meta["sha256_artefatos"] = {
        "checkpoint_rna.pt": "invalido",
        "preprocessador.json": "invalido",
    }
    caminho_meta.write_text(json.dumps(meta), encoding="utf-8")

    with pytest.raises(ValueError, match="[Hh]ash|[Mm]anifesto"):
        carregar_modelo_rna(dir_saida)
