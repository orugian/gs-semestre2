"""Módulo de avaliação e geração de previsões dos baselines."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from citizentech_ml.features.datas import validar_competencia
from citizentech_ml.features.densidade import (
    calcular_densidade_treino,
    filtrar_series_elegiveis,
    obter_series_elegiveis,
)
from citizentech_ml.metricas import mae, mase, resumir_erros
from citizentech_ml.recorte import (
    carregar_escopo_mvp,
    recortar_painel_mvp,
)
from citizentech_ml.split import SplitOrigemMovel


def prever_baselines(painel: pd.DataFrame) -> pd.DataFrame:
    """Gera previsões dos baselines persistência e sazonal sem preencher NaN."""
    if "admissoes_soma_3m" not in painel.columns:
        raise ValueError("Coluna obrigatória 'admissoes_soma_3m' ausente no painel.")
    if "admissoes_sazonal_ano_anterior" not in painel.columns:
        raise ValueError("Coluna obrigatória 'admissoes_sazonal_ano_anterior' ausente no painel.")

    df_res = painel.copy()
    df_res["previsao_persistencia"] = df_res["admissoes_soma_3m"]
    df_res["previsao_sazonal"] = df_res["admissoes_sazonal_ano_anterior"]
    return df_res



def _avaliar_conjunto_baselines(
    df_treino_base: pd.DataFrame,
    df_val_base: pd.DataFrame,
    limite_densidade: float = 10.0,
) -> dict[str, Any]:
    """Avalia baselines em um conjunto treino/avaliação sob as regras D04a e D10b."""
    # 1. Densidade no treino do conjunto
    rel_densidade = calcular_densidade_treino(
        df_treino_base,
        limite_minimo=limite_densidade,
        limite_competencia_treino=None,
    )
    series_elegiveis = obter_series_elegiveis(rel_densidade)
    total_series = len(rel_densidade)
    series_excluidas = total_series - len(series_elegiveis)

    # 2. Filtrar janela de avaliação para as séries elegíveis
    df_val_elegivel = filtrar_series_elegiveis(df_val_base, series_elegiveis)

    # Contagem de linhas elegíveis fora por ausência de dados
    fora_alvo = int(df_val_elegivel["alvo"].isna().sum()) if not df_val_elegivel.empty else 0
    fora_pers = (
        int(df_val_elegivel["previsao_persistencia"].isna().sum())
        if not df_val_elegivel.empty
        else 0
    )
    fora_saz = (
        int(df_val_elegivel["previsao_sazonal"].isna().sum())
        if not df_val_elegivel.empty
        else 0
    )

    # 3. Comparação justa: alvo e ambas as previsões presentes
    if df_val_elegivel.empty:
        df_eval = df_val_elegivel.iloc[0:0].copy()
    else:
        mascara_justa = (
            df_val_elegivel["alvo"].notna()
            & df_val_elegivel["previsao_persistencia"].notna()
            & df_val_elegivel["previsao_sazonal"].notna()
        )
        df_eval = df_val_elegivel[mascara_justa].copy()

    # 4. Cálculo de escala MASE no treino por série (MAE do sazonal)
    mapa_escalas: dict[tuple[str, str], float | None] = {}
    for s in series_elegiveis:
        df_tr_s = df_treino_base[
            (df_treino_base["destino"] == s[0]) & (df_treino_base["uf"] == s[1])
        ]
        val_tr = df_tr_s[df_tr_s["alvo"].notna() & df_tr_s["previsao_sazonal"].notna()]
        if len(val_tr) > 0:
            e_s = mae(val_tr["alvo"], val_tr["previsao_sazonal"])
            mapa_escalas[s] = e_s if e_s > 0.0 else None
        else:
            mapa_escalas[s] = None

    # 5. Avaliação métrica de cada baseline
    baselines_dict: dict[str, Any] = {}
    for nome_b, col_b in [
        ("persistencia", "previsao_persistencia"),
        ("sazonal", "previsao_sazonal"),
    ]:
        if df_eval.empty:
            baselines_dict[nome_b] = {
                "n": 0,
                "mae": None,
                "rmse": None,
                "wape": None,
                "macro_mae": None,
                "mase": None,
                "series_com_escala": 0,
                "series_sem_escala": len(series_elegiveis),
                "tabela_series": [],
            }
            continue

        res_b = resumir_erros(
            df_eval,
            col_real="alvo",
            col_prev=col_b,
            chaves_serie=["destino", "uf"],
        )

        mases_validos: list[float] = []
        for reg in res_b["tabela_series"]:
            chave_s = (str(reg["destino"]), str(reg["uf"]))
            esc = mapa_escalas.get(chave_s)
            val_mase_s = mase([reg["mae"]], [0.0], esc) if esc is not None else None
            reg["mase"] = val_mase_s
            if val_mase_s is not None:
                mases_validos.append(val_mase_s)

        series_com_escala = len(mases_validos)
        series_sem_esc = len(series_elegiveis) - series_com_escala
        mase_agregado = float(np.mean(mases_validos)) if mases_validos else None

        baselines_dict[nome_b] = {
            "n": res_b["n"],
            "mae": res_b["mae"],
            "rmse": res_b["rmse"],
            "wape": res_b["wape"],
            "macro_mae": res_b["macro_mae"],
            "mase": mase_agregado,
            "series_com_escala": series_com_escala,
            "series_sem_escala": series_sem_esc,
            "tabela_series": res_b["tabela_series"],
        }


    return {
        "series_elegiveis": len(series_elegiveis),
        "series_excluidas_densidade": series_excluidas,
        "linhas_descartadas": {
            "alvo_ausente": fora_alvo,
            "persistencia_ausente": fora_pers,
            "sazonal_ausente": fora_saz,
        },
        "baselines": baselines_dict,
    }


def avaliar_baselines(
    painel: pd.DataFrame,
    inicio_treino: str | None = None,
    incluir_validacao: bool = False,
    n_splits: int = 3,
    limite_densidade: float = 10.0,
) -> dict[str, Any]:
    """Avalia baselines via origem móvel no treino e opcionalmente na validação."""
    if "competencia" not in painel.columns:
        raise ValueError("Coluna 'competencia' ausente no painel.")

    # 1. Proteção de holdout e teste: nunca avaliar competências >= 202601
    comps_presentes = painel["competencia"].astype(str).unique()
    for c in comps_presentes:
        if validar_competencia(c) >= "202601":
            raise ValueError(
                f"Competência de teste '{c}' presente: esta fatia não permite "
                f"competências de teste (>= 202601)."
            )

    df_base = painel.copy()
    if "previsao_persistencia" not in df_base.columns or "previsao_sazonal" not in df_base.columns:
        df_base = prever_baselines(df_base)

    inicio_val: str | None = None
    if inicio_treino is not None:
        inicio_val = validar_competencia(inicio_treino)
        df_base = df_base[df_base["competencia"] >= inicio_val].copy()

    # Treino global congelado D10 <= 202409
    df_treino_global = df_base[df_base["competencia"] <= "202409"].copy()

    # 2. Backtesting com origem móvel dentro do treino
    splitter = SplitOrigemMovel(n_splits=n_splits, limite_treino_maximo="202409")
    folds: list[dict[str, Any]] = []

    for fold_idx, (idx_tr, idx_vl) in enumerate(splitter.split(df_treino_global)):
        f_tr = df_treino_global.iloc[idx_tr]
        f_vl = df_treino_global.iloc[idx_vl]

        eval_fold = _avaliar_conjunto_baselines(
            df_treino_base=f_tr,
            df_val_base=f_vl,
            limite_densidade=limite_densidade,
        )
        eval_fold["fold"] = fold_idx
        eval_fold["meses_treino"] = sorted(f_tr["competencia"].unique())
        eval_fold["meses_validacao"] = sorted(f_vl["competencia"].unique())
        folds.append(eval_fold)

    # 3. Resumo entre folds (média e desvio padrão amostral ddof=1)
    resumo_folds: dict[str, Any] = {}
    for nome_b in ["persistencia", "sazonal"]:
        maes = [
            float(f["baselines"][nome_b]["mae"])
            for f in folds
            if f["baselines"][nome_b]["mae"] is not None
        ]
        wapes = [
            float(f["baselines"][nome_b]["wape"])
            for f in folds
            if f["baselines"][nome_b]["wape"] is not None
        ]

        folds_validos = len(maes)
        if folds_validos == 0:
            mae_media = None
            mae_desvio = None
        else:
            mae_media = float(np.mean(maes))
            mae_desvio = float(np.std(maes, ddof=1)) if folds_validos > 1 else None

        if len(wapes) == 0:
            wape_media = None
            wape_desvio = None
        else:
            wape_media = float(np.mean(wapes))
            wape_desvio = float(np.std(wapes, ddof=1)) if len(wapes) > 1 else None

        resumo_folds[nome_b] = {
            "folds_validos": folds_validos,
            "mae_media": mae_media,
            "mae_desvio": mae_desvio,
            "wape_media": wape_media,
            "wape_desvio": wape_desvio,
        }


    # 4. Avaliação na partição de validação (somente com incluir_validacao=True)
    validacao_dict: dict[str, Any] | None = None
    if incluir_validacao:
        df_val_global = df_base[
            (df_base["competencia"] >= "202501") & (df_base["competencia"] <= "202509")
        ].copy()
        validacao_dict = _avaliar_conjunto_baselines(
            df_treino_base=df_treino_global,
            df_val_base=df_val_global,
            limite_densidade=limite_densidade,
        )

    return {
        "inicio_treino": inicio_val,
        "n_splits": n_splits,
        "limite_densidade": limite_densidade,
        "folds": folds,
        "resumo_folds": resumo_folds,
        "validacao": validacao_dict,
    }


def salvar_relatorio_baselines(
    relatorio: dict[str, Any],
    caminho_painel: str | Path,
    dir_saida: str | Path,
    info_escopo: dict[str, Any] | None = None,
) -> Path:
    """Salva o baselines.json com parâmetros, sha256 do painel, escopo e data UTC."""
    dir_s = Path(dir_saida)
    dir_s.mkdir(parents=True, exist_ok=True)
    caminho_json = dir_s / "baselines.json"

    sha256_painel: str | None = None
    p_painel = Path(caminho_painel)
    if p_painel.exists():
        sha256_painel = hashlib.sha256(p_painel.read_bytes()).hexdigest()

    data_utc = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    escopo_dict = info_escopo or {
        "modo": "nao_informado",
        "destinos": None,
    }

    conteudo = {
        "sha256_painel": sha256_painel,
        "caminho_painel": str(p_painel),
        "data_utc": data_utc,
        "escopo": escopo_dict,
        "avaliacao": relatorio,
    }

    caminho_json.write_text(
        json.dumps(conteudo, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return caminho_json


def main() -> None:
    """Ponto de entrada CLI para avaliação dos baselines."""
    parser = argparse.ArgumentParser(description="Avaliação de baselines no painel do Novo Caged.")
    parser.add_argument("--painel", required=True, help="Caminho do Parquet do painel.")
    parser.add_argument("--saida", required=True, help="Diretório de saída para baselines.json.")
    parser.add_argument(
        "--inicio-treino", default=None, help="Competência inicial de treino (ex: 202101)."
    )
    parser.add_argument(
        "--validacao", action="store_true", help="Inclui partição de validação (202501-202509)."
    )
    parser.add_argument(
        "--n-splits", type=int, default=3, help="Número de folds na origem móvel."
    )
    parser.add_argument(
        "--limite-densidade",
        type=float,
        default=10.0,
        help="Média mínima de admissões no treino (D04a).",
    )
    parser.add_argument(
        "--escopo-mvp",
        action="store_true",
        help="Projeta o painel para o escopo MVP R29 antes da avaliação dos baselines.",
    )

    args = parser.parse_args()

    try:
        df_painel = pd.read_parquet(args.painel)

        if args.escopo_mvp:
            escopo = carregar_escopo_mvp()
            df_painel = recortar_painel_mvp(df_painel, escopo=escopo)
            inicio_treino = args.inicio_treino or "202101"
            info_escopo: dict[str, Any] = {
                "modo": "mvp_r29",
                "destinos": escopo["destinos"],
                "hash_recorte": escopo["hash_recorte"],
                "sha256_escopo": escopo["sha256_escopo"],
                "inicio_treino": inicio_treino,
            }
        else:
            inicio_treino = args.inicio_treino
            info_escopo = {
                "modo": "catalogo_completo",
                "destinos": sorted(df_painel["destino"].astype(str).unique().tolist()),
            }

        relatorio = avaliar_baselines(
            painel=df_painel,
            inicio_treino=inicio_treino,
            incluir_validacao=args.validacao,
            n_splits=args.n_splits,
            limite_densidade=args.limite_densidade,
        )
        caminho_json = salvar_relatorio_baselines(
            relatorio=relatorio,
            caminho_painel=args.painel,
            dir_saida=args.saida,
            info_escopo=info_escopo,
        )
        print("=== Avaliação dos Baselines (Origem Móvel) ===")
        resumo = relatorio["resumo_folds"]
        print(f"Folds avaliados: {len(relatorio['folds'])}")

        def _fmt(val: float | None, sufixo: str = "") -> str:
            if val is None:
                return "N/D"
            return f"{val:.2f}{sufixo}"

        def _fmt_pct(val: float | None) -> str:
            if val is None:
                return "N/D"
            return f"{val * 100.0:.2f}%"

        for nome, chave in [("Persistência", "persistencia"), ("Sazonal", "sazonal")]:
            r = resumo[chave]
            mae_m = _fmt(r["mae_media"])
            mae_d = _fmt(r["mae_desvio"])
            wape_m = _fmt_pct(r["wape_media"])
            wape_d = _fmt_pct(r["wape_desvio"])
            f_val = r.get("folds_validos", len(relatorio["folds"]))
            print(
                f"{nome:<12} | Folds válidos: {f_val} | "
                f"MAE médio: {mae_m:>7} (± {mae_d:>6}) | "
                f"WAPE médio: {wape_m:>7} (± {wape_d:>6})"
            )
        if relatorio["validacao"]:
            val_b = relatorio["validacao"]["baselines"]
            print("--- Partição de Validação (202501-202509) ---")
            for nome, chave in [("Persistência", "persistencia"), ("Sazonal", "sazonal")]:
                vb = val_b[chave]
                mae_v = _fmt(vb["mae"])
                wape_v = _fmt_pct(vb["wape"])
                print(f"{nome:<12} | MAE: {mae_v:>7} | WAPE: {wape_v:>7}")
        print(f"Relatório gravado em: {caminho_json}")

    except Exception as exc:
        print(f"Erro na avaliação dos baselines: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
