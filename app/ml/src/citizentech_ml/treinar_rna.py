"""Ponto de entrada CLI para treino e avaliação de redes neurais (MLP PyTorch CPU)."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import torch

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from citizentech_ml.recorte import carregar_escopo_mvp, recortar_painel_mvp
from citizentech_ml.rede_neural import CONFIGS_PADRAO, treinar_rna


def criar_parser() -> argparse.ArgumentParser:
    """Cria o analisador de argumentos da CLI."""
    parser = argparse.ArgumentParser(
        description="Treino e avaliação de MLP PyTorch CPU para o Novo Caged."
    )
    parser.add_argument(
        "--painel", required=True, help="Caminho do Parquet do painel de desenvolvimento."
    )
    parser.add_argument(
        "--saida", required=True, help="Diretório de saída para os artefatos gerados."
    )
    parser.add_argument(
        "--validacao",
        action="store_true",
        help="Inclui partição de validação externa (202501-202509).",
    )
    parser.add_argument(
        "--max-epochs", type=int, default=200, help="Número máximo de épocas por modelo."
    )
    parser.add_argument(
        "--patience", type=int, default=15, help="Paciência para early stopping."
    )
    parser.add_argument(
        "--min-delta", type=float, default=1e-5, help="Melhoria mínima no early stopping."
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Seed determinística para CPU."
    )
    parser.add_argument(
        "--limite-densidade", type=float, default=10.0, help="Média mínima de admissões no treino."
    )
    parser.add_argument(
        "--escopo-mvp",
        action="store_true",
        help="Projeta o painel para o escopo MVP R29 antes do treino.",
    )
    parser.add_argument(
        "--n-splits", type=int, default=3, help="Número de folds na origem móvel."
    )
    return parser


def _gerar_grafico_curvas(df_curvas: pd.DataFrame, caminho_png: Path) -> str:
    """Gera gráfico PNG claro das curvas de loss por configuração e época."""
    fig, ax = plt.subplots(figsize=(10, 6))

    configs_unicas = df_curvas["config"].unique()
    cores = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

    for idx, cfg in enumerate(configs_unicas):
        cor = cores[idx % len(cores)]
        sub = df_curvas[df_curvas["config"] == cfg]

        # Agrupa por época para exibir a média entre folds
        agrupado = sub.groupby("epoca")[["loss_fit", "loss_val_interna"]].mean().reset_index()

        ax.plot(
            agrupado["epoca"],
            agrupado["loss_fit"],
            label=f"Config {cfg} - Treino",
            color=cor,
            linestyle="-",
            linewidth=2,
        )
        if "loss_val_interna" in agrupado.columns and agrupado["loss_val_interna"].notna().any():
            ax.plot(
                agrupado["epoca"],
                agrupado["loss_val_interna"],
                label=f"Config {cfg} - Val Interna",
                color=cor,
                linestyle="--",
                linewidth=1.5,
            )

    ax.set_title("Curvas de Aprendizado MLP PyTorch CPU (MSE sobre y Padronizado)", fontsize=13)
    ax.set_xlabel("Época", fontsize=11)
    ax.set_ylabel("Loss MSE (y Padronizado)", fontsize=11)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right", fontsize=9)

    fig.tight_layout()
    fig.savefig(caminho_png, dpi=150)
    plt.close(fig)

    return hashlib.sha256(caminho_png.read_bytes()).hexdigest()


def executar_treino_rna_cli(
    caminho_painel: str | Path,
    dir_saida: str | Path,
    incluir_validacao: bool = False,
    max_epochs: int = 200,
    patience: int = 15,
    min_delta: float = 1e-5,
    seed: int = 42,
    limite_densidade: float = 10.0,
    escopo_mvp: bool = False,
    n_splits: int = 3,
) -> tuple[Path, Path]:
    """Executa o pipeline completo de treinamento, avaliação e persistência auditável."""
    p_saida = Path(dir_saida)
    if p_saida.exists():
        raise FileExistsError(
            f"Diretório de saída '{p_saida}' já existente. Sobrescrita é proibida para "
            f"preservar a integridade histórica dos experimentos."
        )

    p_painel = Path(caminho_painel)
    if not p_painel.exists():
        raise FileNotFoundError(f"Painel de entrada não encontrado: '{p_painel}'")

    bytes_painel = p_painel.read_bytes()
    sha256_painel = hashlib.sha256(bytes_painel).hexdigest()

    df_painel = pd.read_parquet(p_painel)

    escopo = carregar_escopo_mvp()
    df_painel = recortar_painel_mvp(df_painel, escopo=escopo)
    info_escopo = {
        "modo": "mvp_r29",
        "destinos": sorted(escopo["destinos"]),
        "ufs": sorted(df_painel["uf"].astype(str).unique().tolist()),
        "hash_recorte": escopo["hash_recorte"],
        "sha256_escopo": escopo["sha256_escopo"],
        "flag_escopo_mvp_cli": escopo_mvp,
        "versao": escopo.get("versao", "1.0.0"),
        "decisao": escopo.get("decisao", "R29"),
    }

    # Execução do treino de RNA com CV por origem móvel
    resultado = treinar_rna(
        painel=df_painel,
        seed=seed,
        max_epochs=max_epochs,
        patience=patience,
        min_delta=min_delta,
        incluir_validacao=incluir_validacao,
        n_splits=n_splits,
        limite_densidade=limite_densidade,
        configs=CONFIGS_PADRAO,
        coluna_alvo="alvo",
        coluna_tempo="competencia",
    )

    # Criação do diretório de saída
    p_saida.mkdir(parents=True, exist_ok=False)

    # 1. Salvar checkpoint do modelo global
    caminho_pt = p_saida / "checkpoint_rna.pt"
    torch.save(resultado["modelo"].state_dict(), caminho_pt)
    sha256_pt = hashlib.sha256(caminho_pt.read_bytes()).hexdigest()

    # 2. Salvar pré-processador
    caminho_prep = p_saida / "preprocessador.json"
    caminho_prep.write_text(
        json.dumps(resultado["preprocessador"].to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    sha256_prep = hashlib.sha256(caminho_prep.read_bytes()).hexdigest()

    # 3. Salvar previsões em Parquet e CSV
    caminho_prev_pq = p_saida / "previsoes.parquet"
    caminho_prev_csv = p_saida / "previsoes.csv"
    resultado["previsoes"].to_parquet(caminho_prev_pq, index=False)
    resultado["previsoes"].to_csv(caminho_prev_csv, index=False, encoding="utf-8")
    sha256_prev_pq = hashlib.sha256(caminho_prev_pq.read_bytes()).hexdigest()
    sha256_prev_csv = hashlib.sha256(caminho_prev_csv.read_bytes()).hexdigest()

    # 4. Salvar curvas em CSV
    caminho_curvas_csv = p_saida / "curvas.csv"
    resultado["curvas"].to_csv(caminho_curvas_csv, index=False, encoding="utf-8")
    sha256_curvas_csv = hashlib.sha256(caminho_curvas_csv.read_bytes()).hexdigest()

    # 5. Salvar gráfico de curvas em PNG
    caminho_curvas_png = p_saida / "curvas.png"
    sha256_curvas_png = _gerar_grafico_curvas(resultado["curvas"], caminho_curvas_png)

    data_utc = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Comparação direta de métricas com baselines no CV
    rel_baselines = resultado["relatorio"]["baselines"]
    melhor_nome = resultado["melhor_config"]
    melhor_cfg_info = resultado["configs"][melhor_nome]

    comparacao_cv = {
        "MLP": {
            "nome": melhor_nome,
            "mae_medio": melhor_cfg_info["mae_medio"],
            "mae_desvio": melhor_cfg_info["mae_desvio"],
            "wape_medio": melhor_cfg_info["wape_medio"],
            "wape_desvio": melhor_cfg_info["wape_desvio"],
            "mase_medio": melhor_cfg_info.get("mase_medio"),
            "mase_desvio": melhor_cfg_info.get("mase_desvio"),
        },
        "persistencia": rel_baselines.get("persistencia"),
        "sazonal": rel_baselines.get("sazonal"),
    }

    comparacao_val = None
    if incluir_validacao:
        comparacao_val = {
            "MLP": resultado["relatorio"]["validacao_externa"],
            "persistencia": rel_baselines.get("persistencia", {}).get("validacao"),
            "sazonal": rel_baselines.get("sazonal", {}).get("validacao"),
        }

    # Montagem do manifesto e métricas JSON
    manifesto = {
        "sha256_painel": sha256_painel,
        "caminho_painel": str(p_painel),
        "data_utc": data_utc,
        "recorte": info_escopo,
        "versoes": {
            "torch": str(torch.__version__),
            "numpy": str(np.__version__),
            "pandas": str(pd.__version__),
        },
        "seeds": seed,
        "params": {
            "max_epochs": max_epochs,
            "patience": patience,
            "min_delta": min_delta,
            "n_splits": n_splits,
            "limite_densidade": limite_densidade,
            "configs": CONFIGS_PADRAO,
        },
        "feature_list": {
            "colunas_categoricas": resultado["preprocessador"].colunas_categoricas,
            "colunas_numericas": resultado["preprocessador"].colunas_numericas_efetivas,
            "dimensao_entrada": resultado["preprocessador"].dimensao_entrada,
        },
        "intervalos": {
            "treino_inicio": "202101",
            "treino_fim": "202409",
            "validacao_inicio": "202501" if incluir_validacao else None,
            "validacao_fim": "202509" if incluir_validacao else None,
            "meses_earlystop_interno": 3,
            "meses_embargo_interno": 3,
        },
        "cv_ranking": resultado["relatorio"]["ranking_configs"],
        "melhor_config": resultado["relatorio"]["melhor_config"],
        "configs_detalhes": resultado["configs"],
        "treino_global": resultado["relatorio"]["treino_global"],
        "validacao_externa": resultado["relatorio"]["validacao_externa"],
        "contagem_negativos": resultado["relatorio"]["contagem_negativos"],
        "min_previsao_negativa": resultado["relatorio"]["min_previsao_negativa"],
        "comparacao_baseline": {
            "cv_treino": comparacao_cv,
            "validacao_externa": comparacao_val,
        },
        "tempo_total_segundos": resultado["relatorio"]["tempo_total_segundos"],
        "sha256_artefatos": {
            "checkpoint_rna.pt": sha256_pt,
            "preprocessador.json": sha256_prep,
            "previsoes.parquet": sha256_prev_pq,
            "previsoes.csv": sha256_prev_csv,
            "curvas.csv": sha256_curvas_csv,
            "curvas.png": sha256_curvas_png,
        },
    }

    caminho_metricas = p_saida / "metricas.json"
    caminho_metricas.write_text(
        json.dumps(manifesto, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return caminho_metricas, caminho_pt


def main() -> None:
    """Ponto de entrada de execução da CLI."""
    parser = criar_parser()
    args = parser.parse_args()

    try:
        p_metricas, p_pt = executar_treino_rna_cli(
            caminho_painel=args.painel,
            dir_saida=args.saida,
            incluir_validacao=args.validacao,
            max_epochs=args.max_epochs,
            patience=args.patience,
            min_delta=args.min_delta,
            seed=args.seed,
            limite_densidade=args.limite_densidade,
            escopo_mvp=args.escopo_mvp,
            n_splits=args.n_splits,
        )
        print("=== Treinamento de RNA Concluído com Sucesso ===")
        print(f"Métricas e Manifesto: {p_metricas}")
        print(f"Checkpoint PyTorch CPU: {p_pt}")
    except Exception as exc:
        print(f"Erro no treinamento de RNA: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
