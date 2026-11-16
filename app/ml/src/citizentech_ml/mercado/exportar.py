"""Exportador de snapshot de mercado integrando modelos clássicos e RNA."""

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

from citizentech_ml.baselines import prever_baselines
from citizentech_ml.features.densidade import calcular_densidade_treino


def normalizar_resumo_cv(
    resumo: dict[str, Any] | None,
    folds: list[dict[str, Any]] | None = None,
) -> dict[str, float | None]:
    """Normaliza chaves de métricas CV com mae_medio, mae_desvio, wape_medio, etc.

    Aceita a convenção `_media` ou `_medio`. Se `mase_medio` faltar e houver `folds` com
    `mase`, calcula média e desvio amostral (ddof=1; None se < 2 folds válidos).
    Valores indefinidos retornam None, nunca 0.
    """
    res = resumo if isinstance(resumo, dict) else {}

    def _obter(chave_medio: str, chave_media: str) -> float | None:
        val = res.get(chave_medio)
        if val is None:
            val = res.get(chave_media)
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    mae_medio = _obter("mae_medio", "mae_media")
    mae_desvio = _obter("mae_desvio", "mae_desvio")
    wape_medio = _obter("wape_medio", "wape_media")
    wape_desvio = _obter("wape_desvio", "wape_desvio")
    mase_medio = _obter("mase_medio", "mase_media")
    mase_desvio = _obter("mase_desvio", "mase_desvio")

    lista_folds = folds if folds is not None else res.get("folds")
    if mase_medio is None and isinstance(lista_folds, list):
        mases = [
            float(f["mase"])
            for f in lista_folds
            if isinstance(f, dict) and f.get("mase") is not None
        ]
        if mases:
            mase_medio = float(np.mean(mases))
            mase_desvio = float(np.std(mases, ddof=1)) if len(mases) >= 2 else None

    return {
        "mae_medio": mae_medio,
        "mae_desvio": mae_desvio,
        "wape_medio": wape_medio,
        "wape_desvio": wape_desvio,
        "mase_medio": mase_medio,
        "mase_desvio": mase_desvio,
    }


def _sanitizar_nan(obj: Any) -> Any:
    """Substitui recursivamente NaN e infinitos por None para serialização JSON estrita."""
    if isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: _sanitizar_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitizar_nan(v) for v in obj]
    return obj


def exportar_snapshot_mercado(
    painel_path: str | Path,
    dir_classicos: str | Path,
    dir_rna: str | Path,
    dir_saida: str | Path,
    escopo_path: str | Path | None = None,
) -> dict[str, Any]:
    """Exporta snapshot de mercado e manifesto validando integridade estrita."""
    # 1. Regra 1: dir_saida já existente gera FileExistsError imediatamente
    p_saida = Path(dir_saida)
    if p_saida.exists():
        raise FileExistsError(
            f"Diretório de saída '{p_saida}' já existente. Sobrescrita é proibida para "
            f"preservar a integridade dos artefatos."
        )

    # 2. Regra 2: Integridade sem desserializar modelos (apenas hashes e JSON/parquet)
    p_painel = Path(painel_path)
    if not p_painel.exists():
        raise FileNotFoundError(f"Painel de entrada não encontrado: {p_painel}")

    sha256_painel_calc = hashlib.sha256(p_painel.read_bytes()).hexdigest()

    # Leitura e verificação de integridade dos Clássicos
    p_dir_classicos = Path(dir_classicos)
    p_man_cl = p_dir_classicos / "manifesto.json"
    if not p_man_cl.exists():
        raise FileNotFoundError(f"Manifesto dos clássicos não encontrado em: {p_man_cl}")

    try:
        man_cl = json.loads(p_man_cl.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Manifesto dos clássicos malformado: {exc}") from exc

    arquivos_cl = man_cl.get("arquivos")
    if not isinstance(arquivos_cl, dict):
        raise ValueError("Manifesto dos clássicos: campo 'arquivos' ausente ou inválido.")

    for arq_obrigatorio in ["metricas.json", "previsoes.parquet"]:
        if arq_obrigatorio not in arquivos_cl:
            raise ValueError(
                f"Hash obrigatório '{arq_obrigatorio}' ausente no manifesto clássicos."
            )
        caminho_arq = p_dir_classicos / arq_obrigatorio
        if not caminho_arq.exists():
            raise FileNotFoundError(
                f"Arquivo obrigatório '{arq_obrigatorio}' ausente em clássicos."
            )
        hash_calc = hashlib.sha256(caminho_arq.read_bytes()).hexdigest()
        hash_esp = str(arquivos_cl[arq_obrigatorio])
        if hash_calc.lower() != hash_esp.lower():
            raise ValueError(
                f"Hash SHA-256 de '{arq_obrigatorio}' divergiu do manifesto clássicos: "
                f"esperado={hash_esp}, calculado={hash_calc}"
            )

    sha_painel_cl = man_cl.get("sha256_painel", "")
    if sha_painel_cl.lower() != sha256_painel_calc.lower():
        raise ValueError(
            f"sha256_painel clássicos ({sha_painel_cl}) diverge do painel ({sha256_painel_calc})."
        )

    metricas_cl = json.loads((p_dir_classicos / "metricas.json").read_text(encoding="utf-8"))
    sha_painel_met_cl = metricas_cl.get("sha256_painel")
    if sha_painel_met_cl and sha_painel_met_cl.lower() != sha256_painel_calc.lower():
        raise ValueError(
            f"sha256_painel métricas clássicos ({sha_painel_met_cl}) diverge do painel "
            f"({sha256_painel_calc})."
        )

    # Leitura e verificação de integridade da RNA
    p_dir_rna = Path(dir_rna)
    p_met_rna = p_dir_rna / "metricas.json"
    if not p_met_rna.exists():
        raise FileNotFoundError(f"Métricas/manifesto da RNA não encontrado em: {p_met_rna}")

    try:
        metricas_rna = json.loads(p_met_rna.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Métricas da RNA malformadas: {exc}") from exc

    sha_artefatos_rna = metricas_rna.get("sha256_artefatos")
    if not isinstance(sha_artefatos_rna, dict):
        raise ValueError("RNA: campo 'sha256_artefatos' ausente ou inválido em metricas.json.")

    if "previsoes.parquet" not in sha_artefatos_rna:
        raise ValueError("RNA: hash de 'previsoes.parquet' ausente em sha256_artefatos.")

    p_prev_rna = p_dir_rna / "previsoes.parquet"
    if not p_prev_rna.exists():
        raise FileNotFoundError(f"Arquivo 'previsoes.parquet' ausente em {p_dir_rna}")

    hash_prev_rna_calc = hashlib.sha256(p_prev_rna.read_bytes()).hexdigest()
    hash_prev_rna_esp = str(sha_artefatos_rna["previsoes.parquet"])
    if hash_prev_rna_calc.lower() != hash_prev_rna_esp.lower():
        raise ValueError(
            f"Hash SHA-256 de 'previsoes.parquet' divergiu na RNA: "
            f"esperado={hash_prev_rna_esp}, calculado={hash_prev_rna_calc}"
        )

    sha_painel_rna = metricas_rna.get("sha256_painel", "")
    if sha_painel_rna.lower() != sha256_painel_calc.lower():
        raise ValueError(
            f"sha256_painel da RNA ({sha_painel_rna}) diverge do painel ({sha256_painel_calc})."
        )

    # Coerência de hash_recorte entre clássicos e RNA
    recorte_cl = man_cl.get("recorte") if isinstance(man_cl.get("recorte"), dict) else {}
    hash_recorte_cl = (
        recorte_cl.get("hash_recorte")
        or man_cl.get("hash_recorte")
        or metricas_cl.get("hash_recorte")
    )
    recorte_rna = (
        metricas_rna.get("recorte") if isinstance(metricas_rna.get("recorte"), dict) else {}
    )
    hash_recorte_rna = recorte_rna.get("hash_recorte") or metricas_rna.get("hash_recorte")

    if not hash_recorte_cl or not hash_recorte_rna or hash_recorte_cl != hash_recorte_rna:
        raise ValueError(
            f"hash_recorte diverge entre clássicos ({hash_recorte_cl}) e RNA ({hash_recorte_rna})."
        )

    # 3. Regra 3: Validação de competências e filtro de escopo MVP
    df_painel = pd.read_parquet(p_painel)
    comps = df_painel["competencia"].astype(str).unique()
    if any(c >= "202601" for c in comps):
        raise ValueError(
            "Painel de desenvolvimento contém competências >= 202601. Holdout final 2026 "
            "está estritamente reservado."
        )

    if escopo_path:
        escopo = json.loads(Path(escopo_path).read_text(encoding="utf-8"))
    else:
        from citizentech_ml.recorte import carregar_escopo_mvp

        escopo = carregar_escopo_mvp()

    destinos_mvp = sorted(escopo.get("destinos", []))
    df_painel = df_painel[df_painel["destino"].isin(destinos_mvp)].copy()

    # 4. Regra 4: Densidade no treino 202101-202409 e conferência com clássicos
    df_treino = df_painel[
        df_painel["competencia"].between("202101", "202409") & df_painel["alvo"].notna()
    ].copy()
    rel_densidade = calcular_densidade_treino(
        df_treino, limite_minimo=10.0, limite_competencia_treino="202409"
    )

    series_elegiveis_calculadas = set(
        zip(
            rel_densidade[rel_densidade["elegivel"]]["destino"].astype(str),
            rel_densidade[rel_densidade["elegivel"]]["uf"].astype(str),
            strict=False,
        )
    )

    df_prev_cl = pd.read_parquet(p_dir_classicos / "previsoes.parquet")
    if "particao" in df_prev_cl.columns:
        df_prev_cl_val = df_prev_cl[df_prev_cl["particao"] == "validacao"].copy()
    else:
        df_prev_cl_val = df_prev_cl.copy()

    series_classicos_val = set(
        zip(
            df_prev_cl_val["destino"].astype(str),
            df_prev_cl_val["uf"].astype(str),
            strict=False,
        )
    )

    if series_classicos_val != series_elegiveis_calculadas:
        raise ValueError(
            f"Conjunto de séries elegíveis calculado ({len(series_elegiveis_calculadas)}) "
            f"diverge das séries de validação dos clássicos ({len(series_classicos_val)})."
        )

    # 5. Regra 5: Previsões de validação e verificação de chaves idênticas
    if "particao" in df_painel.columns:
        df_val_raw = df_painel[df_painel["particao"] == "validacao"].copy()
    else:
        df_val_raw = df_painel[df_painel["competencia"].between("202501", "202509")].copy()

    masc_eleg = df_val_raw.apply(
        lambda r: (str(r["destino"]), str(r["uf"])) in series_elegiveis_calculadas, axis=1
    )
    df_val_eleg = df_val_raw[masc_eleg].copy()

    df_val_baselines = df_val_eleg[
        df_val_eleg["alvo"].notna()
        & df_val_eleg["admissoes_soma_3m"].notna()
        & df_val_eleg["admissoes_sazonal_ano_anterior"].notna()
    ].copy()
    df_val_baselines = prever_baselines(df_val_baselines)

    chaves_baselines = set(
        zip(
            df_val_baselines["competencia"].astype(str),
            df_val_baselines["destino"].astype(str),
            df_val_baselines["uf"].astype(str),
            strict=False,
        )
    )

    modelos_classicos = ["ridge", "random_forest", "hist_gradient_boosting"]
    prev_classicos_dict: dict[str, pd.DataFrame] = {}
    for mod in modelos_classicos:
        sub_mod = df_prev_cl_val[df_prev_cl_val["modelo"] == mod].copy()
        chaves_mod = set(
            zip(
                sub_mod["competencia"].astype(str),
                sub_mod["destino"].astype(str),
                sub_mod["uf"].astype(str),
                strict=False,
            )
        )
        if chaves_mod != chaves_baselines:
            raise ValueError(
                f"Chaves de validação do modelo clássico '{mod}' divergem dos baselines."
            )
        prev_classicos_dict[mod] = sub_mod

    melhor_cfg_rna = metricas_rna.get("melhor_config", {})
    nome_cfg_rna = (
        melhor_cfg_rna.get("nome", "A")
        if isinstance(melhor_cfg_rna, dict)
        else str(melhor_cfg_rna)
    )
    mod_rna_nome = f"MLP_{nome_cfg_rna}_global_validacao"
    df_prev_rna = pd.read_parquet(p_dir_rna / "previsoes.parquet")
    sub_rna = df_prev_rna[df_prev_rna["modelo"] == mod_rna_nome].copy()
    chaves_rna = set(
        zip(
            sub_rna["competencia"].astype(str),
            sub_rna["destino"].astype(str),
            sub_rna["uf"].astype(str),
            strict=False,
        )
    )
    if chaves_rna != chaves_baselines:
        raise ValueError(
            f"Chaves de validação da RNA ({mod_rna_nome}) divergem dos baselines."
        )

    # Recomputação do MAE global de validação dos baselines
    mae_recomp_pers = float(
        np.mean(np.abs(df_val_baselines["previsao_persistencia"] - df_val_baselines["alvo"]))
    )
    mae_esp_pers = float(metricas_cl["validacao_externa"]["baselines"]["persistencia"]["mae"])
    if abs(mae_recomp_pers - mae_esp_pers) > 1e-6:
        raise ValueError(
            f"MAE global recomputado do baseline persistência ({mae_recomp_pers}) "
            f"diverge do manifesto ({mae_esp_pers})."
        )

    mae_recomp_saz = float(
        np.mean(np.abs(df_val_baselines["previsao_sazonal"] - df_val_baselines["alvo"]))
    )
    mae_esp_saz = float(metricas_cl["validacao_externa"]["baselines"]["sazonal"]["mae"])
    if abs(mae_recomp_saz - mae_esp_saz) > 1e-6:
        raise ValueError(
            f"MAE global recomputado do baseline sazonal ({mae_recomp_saz}) "
            f"diverge do manifesto ({mae_esp_saz})."
        )

    # 7. Regra 7: Escolha dinâmica do baseline com menor MAE de validação
    modelo_exibido = "persistencia" if mae_esp_pers < mae_esp_saz else "sazonal"

    # Mapeamento para busca rápida de métricas por série
    def _construir_mapa_metricas_series(
        tabela: list[dict[str, Any]],
    ) -> dict[tuple[str, str], dict[str, Any]]:
        return {(str(item["destino"]), str(item["uf"])): item for item in tabela}

    mapas_metricas_series: dict[str, dict[tuple[str, str], dict[str, Any]]] = {
        "persistencia": _construir_mapa_metricas_series(
            metricas_cl["validacao_externa"]["baselines"]["persistencia"]["tabela_series"]
        ),
        "sazonal": _construir_mapa_metricas_series(
            metricas_cl["validacao_externa"]["baselines"]["sazonal"]["tabela_series"]
        ),
        "ridge": _construir_mapa_metricas_series(
            metricas_cl["validacao_externa"]["modelos"]["ridge"]["tabela_series"]
        ),
        "random_forest": _construir_mapa_metricas_series(
            metricas_cl["validacao_externa"]["modelos"]["random_forest"]["tabela_series"]
        ),
        "hist_gradient_boosting": _construir_mapa_metricas_series(
            metricas_cl["validacao_externa"]["modelos"]["hist_gradient_boosting"]["tabela_series"]
        ),
        "mlp": _construir_mapa_metricas_series(
            metricas_rna["validacao_externa"]["tabela_series"]
        ),
    }

    # 8. Montagem das séries
    mapa_densidade = {
        (str(r["destino"]), str(r["uf"])): r for _, r in rel_densidade.iterrows()
    }
    todas_series_dest_uf = sorted(
        df_painel[["destino", "uf"]].drop_duplicates().to_records(index=False).tolist(),
        key=lambda x: (x[0], x[1]),
    )

    lista_series_saida: list[dict[str, Any]] = []
    for d, u in todas_series_dest_uf:
        d_str = str(d)
        u_str = str(u)
        info_dens = mapa_densidade.get((d_str, u_str))
        elegivel = bool(info_dens["elegivel"]) if info_dens is not None else False
        motivo_dens = str(info_dens["motivo"]) if info_dens is not None else "sem_dados_treino"
        media_alvo = (
            float(info_dens["media_alvo_treino"])
            if info_dens is not None and pd.notna(info_dens["media_alvo_treino"])
            else None
        )

        df_serie = df_painel[
            (df_painel["destino"] == d_str) & (df_painel["uf"] == u_str)
        ].sort_values("competencia")

        observado_lista: list[dict[str, Any]] = []
        for _, row_obs in df_serie.iterrows():
            adm = float(row_obs["admissoes"]) if pd.notna(row_obs.get("admissoes")) else None
            adm_tot = (
                float(row_obs["admissoes_total"])
                if pd.notna(row_obs.get("admissoes_total"))
                else None
            )
            desl = (
                float(row_obs["desligamentos"])
                if pd.notna(row_obs.get("desligamentos"))
                else None
            )
            observado_lista.append({
                "competencia": str(row_obs["competencia"]),
                "admissoes": adm,
                "admissoes_total": adm_tot,
                "desligamentos": desl,
            })

        previsoes_validacao_dict: dict[str, list[dict[str, Any]]] = {}
        metricas_validacao_dict: dict[str, dict[str, Any]] = {}

        if elegivel:
            # Baselines
            sub_b = df_val_baselines[
                (df_val_baselines["destino"] == d_str) & (df_val_baselines["uf"] == u_str)
            ].sort_values("competencia")
            previsoes_validacao_dict["persistencia"] = [
                {
                    "competencia": str(r["competencia"]),
                    "previsao": float(r["previsao_persistencia"]),
                    "alvo": float(r["alvo"]),
                }
                for _, r in sub_b.iterrows()
            ]
            previsoes_validacao_dict["sazonal"] = [
                {
                    "competencia": str(r["competencia"]),
                    "previsao": float(r["previsao_sazonal"]),
                    "alvo": float(r["alvo"]),
                }
                for _, r in sub_b.iterrows()
            ]

            # Clássicos
            for mod in modelos_classicos:
                sub_cl_m = prev_classicos_dict[mod][
                    (prev_classicos_dict[mod]["destino"] == d_str)
                    & (prev_classicos_dict[mod]["uf"] == u_str)
                ].sort_values("competencia")
                previsoes_validacao_dict[mod] = [
                    {
                        "competencia": str(r["competencia"]),
                        "previsao": float(r["previsao"]),
                        "alvo": float(r["alvo"]),
                    }
                    for _, r in sub_cl_m.iterrows()
                ]

            # MLP
            sub_rna_s = sub_rna[
                (sub_rna["destino"] == d_str) & (sub_rna["uf"] == u_str)
            ].sort_values("competencia")
            previsoes_validacao_dict["mlp"] = [
                {
                    "competencia": str(r["competencia"]),
                    "previsao": float(r["previsao"]),
                    "alvo": float(r["alvo"]),
                }
                for _, r in sub_rna_s.iterrows()
            ]

            # Métricas por série para cada modelo
            for id_mod, mapa_m in mapas_metricas_series.items():
                met_item = mapa_m.get((d_str, u_str))
                if met_item:
                    metricas_validacao_dict[id_mod] = {
                        "n": int(met_item["n"]),
                        "mae": (
                            float(met_item["mae"]) if met_item.get("mae") is not None else None
                        ),
                        "rmse": (
                            float(met_item["rmse"]) if met_item.get("rmse") is not None else None
                        ),
                        "wape": (
                            float(met_item["wape"]) if met_item.get("wape") is not None else None
                        ),
                        "mase": (
                            float(met_item["mase"]) if met_item.get("mase") is not None else None
                        ),
                    }

        lista_series_saida.append({
            "destino": d_str,
            "uf": u_str,
            "elegivel": elegivel,
            "motivo_densidade": motivo_dens,
            "media_alvo_treino": media_alvo,
            "observado": observado_lista,
            "previsoes_validacao": previsoes_validacao_dict,
            "metricas_validacao": metricas_validacao_dict,
        })

    # 9. Contexto regional
    regioes_nome = {
        "1": "Norte",
        "2": "Nordeste",
        "3": "Sudeste",
        "4": "Sul",
        "5": "Centro-Oeste",
    }
    todas_competencias = sorted(df_painel["competencia"].astype(str).unique().tolist())
    contexto_regional_lista: list[dict[str, Any]] = []

    for d in destinos_mvp:
        df_d = df_painel[df_painel["destino"] == d]
        ufs_presentes = sorted(df_d["uf"].astype(str).unique().tolist())

        # Agrupa UFs por região
        ufs_por_regiao: dict[str, list[str]] = {}
        for u in ufs_presentes:
            cod_reg = u[0] if u else ""
            nome_reg = regioes_nome.get(cod_reg, f"Regiao_{cod_reg}")
            ufs_por_regiao.setdefault(nome_reg, []).append(u)

        for nome_reg, ufs_reg in sorted(ufs_por_regiao.items()):
            ufs_reg_sorted = sorted(ufs_reg)
            observado_reg: list[dict[str, Any]] = []

            for comp in todas_competencias:
                sub_comp = df_d[
                    (df_d["competencia"] == comp) & (df_d["uf"].isin(ufs_reg_sorted))
                ]
                # Se alguma UF da região tiver admissões ausente no mês, valor é null
                if len(sub_comp) == len(ufs_reg_sorted) and sub_comp["admissoes"].notna().all():
                    soma_adm = float(sub_comp["admissoes"].sum())
                else:
                    soma_adm = None

                observado_reg.append({
                    "competencia": comp,
                    "admissoes": soma_adm,
                })

            contexto_regional_lista.append({
                "destino": d,
                "regiao": nome_reg,
                "ufs": ufs_reg_sorted,
                "observado": observado_reg,
            })

    # 10. Modelos e model cards (6 modelos na ordem estrita)
    config_modelos = [
        ("persistencia", "Persistência 3M", "baseline", "classicos"),
        ("sazonal", "Sazonal Ano Anterior", "baseline", "classicos"),
        ("ridge", "Ridge Regression", "classico", "classicos"),
        ("random_forest", "Random Forest", "classico", "classicos"),
        ("hist_gradient_boosting", "Hist Gradient Boosting", "classico", "classicos"),
        ("mlp", "Rede Neural MLP", "rna", "rna"),
    ]

    lista_modelos_saida: list[dict[str, Any]] = []
    for mod_id, mod_nome, mod_tipo, _arq_origem in config_modelos:
        # Metadados de validação global
        if mod_id in ["persistencia", "sazonal"]:
            met_glob = metricas_cl["validacao_externa"]["baselines"][mod_id]
            norm_cv = normalizar_resumo_cv(
                metricas_cl["baselines"][mod_id].get("cv_resumo"),
                folds=metricas_cl["baselines"][mod_id].get("folds"),
            )
            hiperparams = (
                {"regra": "admissoes_soma_3m"}
                if mod_id == "persistencia"
                else {"regra": "admissoes_sazonal_ano_anterior"}
            )
            selecao_txt = "Baseline determinístico sem hiperparâmetros"
            versao_art = p_dir_classicos.name
            data_tr = man_cl.get("data_utc", "2026-11-16T00:00:00Z")
            seeds_val = man_cl.get("seed", 42)
            versoes_val = man_cl.get("versoes", {})
            sha_arts = man_cl.get("arquivos", {})
        elif mod_id in ["ridge", "random_forest", "hist_gradient_boosting"]:
            met_glob = metricas_cl["validacao_externa"]["modelos"][mod_id]
            norm_cv = normalizar_resumo_cv(metricas_cl.get("resumo_cv", {}).get(mod_id))
            hiperparams = (
                metricas_cl.get("hiperparametros_e_cv", {})
                .get(mod_id, {})
                .get("melhores_parametros", {})
            )
            selecao_txt = (
                "Melhor configuração por CV 3 folds no treino (métrica de seleção, otimista)"
            )
            versao_art = p_dir_classicos.name
            data_tr = man_cl.get("data_utc", "2026-11-16T00:00:00Z")
            seeds_val = man_cl.get("seed", 42)
            versoes_val = man_cl.get("versoes", {})
            sha_arts = man_cl.get("arquivos", {})
        else:
            met_glob = metricas_rna["validacao_externa"]
            detalhes_cfg = metricas_rna.get("configs_detalhes", {}).get(nome_cfg_rna, {})
            norm_cv = normalizar_resumo_cv(detalhes_cfg)
            hiperparams = (
                metricas_rna.get("melhor_config", {}).get("params", {})
                if isinstance(metricas_rna.get("melhor_config"), dict)
                else {}
            )
            selecao_txt = (
                "CV 3 folds no treino (RV-RNA-03: métrica de seleção, otimista)"
            )
            versao_art = p_dir_rna.name
            data_tr = metricas_rna.get("data_utc", "2026-11-16T00:00:00Z")
            seeds_val = metricas_rna.get("seeds", 42)
            versoes_val = metricas_rna.get("versoes", {})
            sha_arts = metricas_rna.get("sha256_artefatos", {})

        model_card = {
            "_id": f"{mod_id}:{versao_art}",
            "modelo": mod_id,
            "versao_artefato": versao_art,
            "tipo": mod_tipo,
            "data_treino_utc": data_tr,
            "periodo_treino": ["202101", "202409"],
            "periodo_validacao": ["202501", "202509"],
            "populacao": (
                "Admissões formais com ensino superior completo ou mais "
                "nas ocupações CBO curadas de cada destino"
            ),
            "sha256_painel": sha256_painel_calc,
            "hash_recorte": hash_recorte_cl,
            "hiperparametros": hiperparams,
            "seed": seeds_val,
            "versoes": versoes_val,
            "sha256_artefatos": sha_arts,
            "selecao": selecao_txt,
            "limites": metricas_cl.get(
                "limites", ["Séries com média de treino < 10 são excluídas"]
            ),
            "status_promocao": "nao_decidida",
        }

        lista_modelos_saida.append({
            "id": mod_id,
            "nome": mod_nome,
            "tipo": mod_tipo,
            "promovido": False,
            "exibido_ao_usuario": (mod_id == modelo_exibido),
            "metricas_validacao_global": {
                "n": int(met_glob["n"]),
                "mae": float(met_glob["mae"]) if met_glob.get("mae") is not None else None,
                "rmse": float(met_glob["rmse"]) if met_glob.get("rmse") is not None else None,
                "wape": float(met_glob["wape"]) if met_glob.get("wape") is not None else None,
                "mase": float(met_glob["mase"]) if met_glob.get("mase") is not None else None,
            },
            "metricas_cv_treino": norm_cv,
            "model_card": model_card,
        })

    data_geracao = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    snapshot: dict[str, Any] = {
        "schema_version": "1.0",
        "gerado_em": data_geracao,
        "metadados_fonte": {
            "fonte": "Novo Caged — microdados públicos do MTE (PDET)",
            "populacao": (
                "Admissões formais com ensino superior completo ou mais "
                "nas ocupações CBO curadas de cada destino"
            ),
            "recorte": {
                "decisao": "R29",
                "hash_recorte": hash_recorte_cl,
                "sha256_escopo": escopo.get("sha256_escopo", ""),
            },
            "sha256_painel": sha256_painel_calc,
            "competencia_min": min(todas_competencias),
            "competencia_max": max(todas_competencias),
        },
        "densidade": {
            "limite_minimo": 10.0,
            "periodo_treino": ["202101", "202409"],
        },
        "promocao": {
            "criterio": (
                "D10a congelado: promoção de modelo exige avaliação no holdout final fechado "
                "e MAE de validação >=5% abaixo do melhor baseline com estabilidade entre folds."
            ),
            "status": "nao_decidida",
            "modelo_exibido": modelo_exibido,
            "motivo": (
                "Holdout 2026 permanece fechado nesta fatia. Nenhum modelo promovido; "
                f"número exibido ao usuário é o baseline de menor MAE ({modelo_exibido})."
            ),
        },
        "series": lista_series_saida,
        "contexto_regional": contexto_regional_lista,
        "modelos": lista_modelos_saida,
    }

    # Sanitização defensiva contra NaNs para compliance estrito com allow_nan=False
    snapshot_sanitizado = _sanitizar_nan(snapshot)

    # 11. Gravação com integridade
    p_saida.mkdir(parents=True, exist_ok=False)

    p_snap_json = p_saida / "snapshot_mercado.json"
    texto_snap = json.dumps(snapshot_sanitizado, indent=2, ensure_ascii=False, allow_nan=False)
    p_snap_json.write_text(texto_snap + "\n", encoding="utf-8")

    sha256_snap = hashlib.sha256(p_snap_json.read_bytes()).hexdigest()
    manifesto_saida = {
        "schema_version": "1.0",
        "arquivo": "snapshot_mercado.json",
        "sha256": sha256_snap,
        "gerado_em": data_geracao,
    }
    p_man_json = p_saida / "manifesto.json"
    p_man_json.write_text(
        json.dumps(manifesto_saida, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return snapshot_sanitizado



def criar_parser() -> argparse.ArgumentParser:
    """Cria analisador CLI para exportação do snapshot."""
    parser = argparse.ArgumentParser(
        description="Exportador de snapshot de mercado (ML) para API CitizenTech."
    )
    parser.add_argument(
        "--painel", required=True, help="Caminho do Parquet do painel de desenvolvimento."
    )
    parser.add_argument(
        "--classicos", required=True, help="Diretório dos artefatos dos modelos clássicos."
    )
    parser.add_argument(
        "--rna", required=True, help="Diretório dos artefatos do modelo RNA."
    )
    parser.add_argument(
        "--saida", required=True, help="Novo diretório de saída para o snapshot."
    )
    parser.add_argument(
        "--escopo", default=None, help="Caminho opcional do arquivo de escopo MVP."
    )
    return parser


def main() -> None:
    """Ponto de entrada CLI."""
    parser = criar_parser()
    args = parser.parse_args()
    try:
        exportar_snapshot_mercado(
            painel_path=args.painel,
            dir_classicos=args.classicos,
            dir_rna=args.rna,
            dir_saida=args.saida,
            escopo_path=args.escopo,
        )
    except Exception as exc:
        print(f"Erro na exportação de mercado: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
