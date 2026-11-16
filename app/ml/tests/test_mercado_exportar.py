"""Testes do exportador de mercado (ML) e normalização de métricas."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from citizentech_ml.mercado.exportar import (
    exportar_snapshot_mercado,
    normalizar_resumo_cv,
)


def test_normalizar_resumo_cv_com_convencao_media_e_folds():
    """Verifica aceitação de _media e cálculo de mase a partir de folds."""
    resumo_antigo = {
        "folds_validos": 3,
        "mae_media": 10.5,
        "mae_desvio": 1.2,
        "wape_media": 0.15,
        "wape_desvio": 0.02,
    }
    folds = [
        {"mase": 1.0},
        {"mase": 1.2},
        {"mase": 1.4},
    ]

    norm = normalizar_resumo_cv(resumo_antigo, folds=folds)

    assert norm["mae_medio"] == 10.5
    assert norm["mae_desvio"] == 1.2
    assert norm["wape_medio"] == 0.15
    assert norm["wape_desvio"] == 0.02
    assert norm["mase_medio"] == pytest.approx(1.2)
    assert norm["mase_desvio"] == pytest.approx(0.2)


def test_normalizar_resumo_cv_com_convencao_medio():
    """Verifica aceitação de _medio quando presente diretamente."""
    resumo_medio = {
        "mae_medio": 5.0,
        "mae_desvio": 0.5,
        "wape_medio": 0.08,
        "wape_desvio": 0.01,
        "mase_medio": 0.9,
        "mase_desvio": 0.04,
    }
    norm = normalizar_resumo_cv(resumo_medio)
    assert norm == resumo_medio


def test_normalizar_resumo_cv_indefinidos_retornam_none():
    """Valores indefinidos ou folds insuficientes (<2) geram None e nunca zero."""
    resumo_vazio = {}
    folds_um = [{"mase": 0.8}]
    norm = normalizar_resumo_cv(resumo_vazio, folds=folds_um)

    assert norm["mae_medio"] is None
    assert norm["mae_desvio"] is None
    assert norm["wape_medio"] is None
    assert norm["wape_desvio"] is None
    assert norm["mase_medio"] == 0.8
    assert norm["mase_desvio"] is None


def _criar_artefatos_sinteticos(
    tmp_path: Path,
    persistencia_vence: bool = False,
    competencia_2026: bool = False,
    adulterar_parquet: bool = False,
    painel_divergente: bool = False,
    recorte_divergente: bool = False,
    chaves_divergentes: bool = False,
    elegiveis_divergentes: bool = False,
    incluir_nan_observado: bool = False,
    omitir_uf_regional: bool = False,
) -> tuple[Path, Path, Path, Path]:
    """Helper que monta ambiente com painel, clássicos e RNA com integridade estrita."""
    dir_base = tmp_path / "ambiente"
    dir_base.mkdir(parents=True, exist_ok=True)

    # 1. Escopo MVP
    hash_recorte_val = "recorte_hash_123"
    escopo = {
        "versao": "1.0.0",
        "decisao": "R29",
        "destinos": [
            "analista_dados_bi",
            "analista_monitoramento_iot",
            "analista_processos",
        ],
        "hash_recorte": hash_recorte_val,
        "sha256_escopo": "escopo_hash_123",
    }
    p_escopo = dir_base / "escopo_mvp.json"
    p_escopo.write_text(json.dumps(escopo, indent=2), encoding="utf-8")

    destinos = escopo["destinos"]
    ufs = ["35", "31"]

    meses_treino = [
        f"{ano}{mes:02d}"
        for ano in range(2021, 2025)
        for mes in range(1, 13)
        if not (ano == 2024 and mes > 9)
    ]
    meses_val = [f"2025{mes:02d}" for mes in range(1, 10)]
    meses_todos = ["202001", "202002"] + meses_treino + meses_val
    if competencia_2026:
        meses_todos.append("202601")

    linhas_painel = []
    for m in meses_todos:
        part = (
            "validacao"
            if m.startswith("2025")
            else ("treino" if m >= "202101" else "historico")
        )
        for d in destinos:
            for u in ufs:
                nivel = 50.0 if u == "35" else 4.0
                alvo_val = nivel + (1.0 if d == "analista_dados_bi" else 2.0)

                if persistencia_vence:
                    soma_3m = alvo_val
                    sazonal = alvo_val + 10.0
                else:
                    soma_3m = alvo_val + 10.0
                    sazonal = alvo_val

                adm = alvo_val / 3.0
                if (
                    incluir_nan_observado
                    and m == "202001"
                    and u == "35"
                    and d == "analista_dados_bi"
                ):
                    adm = np.nan
                if (
                    omitir_uf_regional
                    and m == "202002"
                    and u == "31"
                    and d == "analista_dados_bi"
                ):
                    adm = np.nan

                linhas_painel.append({
                    "competencia": m,
                    "mes": int(m[-2:]),
                    "destino": d,
                    "uf": u,
                    "admissoes": adm,
                    "desligamentos": 5.0,
                    "admissoes_total": 20.0,
                    "desligamentos_total": 10.0,
                    "admissoes_soma_3m": soma_3m,
                    "admissoes_sazonal_ano_anterior": sazonal,
                    "alvo": alvo_val,
                    "particao": part,
                })

    df_painel = pd.DataFrame(linhas_painel)
    p_painel = dir_base / "painel.parquet"
    df_painel.to_parquet(p_painel, index=False)
    sha_painel = hashlib.sha256(p_painel.read_bytes()).hexdigest()

    series_elegiveis = [(d, "35") for d in destinos]
    if elegiveis_divergentes:
        series_classicos = series_elegiveis + [("analista_dados_bi", "31")]
    else:
        series_classicos = series_elegiveis

    dir_classicos = dir_base / "classicos"
    dir_classicos.mkdir(parents=True, exist_ok=True)

    linhas_prev_classicos = []
    modelos_classicos = ["ridge", "random_forest", "hist_gradient_boosting"]
    for m in meses_val:
        for d, u in series_classicos:
            alvo_real = 50.0 + (1.0 if d == "analista_dados_bi" else 2.0)
            for mod in modelos_classicos:
                linhas_prev_classicos.append({
                    "competencia": m,
                    "destino": d,
                    "uf": u,
                    "modelo": mod,
                    "alvo": alvo_real,
                    "previsao": alvo_real + 1.0,
                    "particao": "validacao",
                })

    if chaves_divergentes:
        linhas_prev_classicos = [
            r
            for r in linhas_prev_classicos
            if not (
                r["modelo"] == "ridge"
                and r["competencia"] == "202501"
                and r["destino"] == "analista_dados_bi"
            )
        ]

    df_prev_cl = pd.DataFrame(linhas_prev_classicos)
    p_prev_cl = dir_classicos / "previsoes.parquet"
    df_prev_cl.to_parquet(p_prev_cl, index=False)
    sha_prev_cl = hashlib.sha256(p_prev_cl.read_bytes()).hexdigest()

    mae_pers = 0.0 if persistencia_vence else 10.0
    mae_saz = 10.0 if persistencia_vence else 0.0

    tabela_series_cl = [
        {"destino": d, "uf": u, "n": 9, "mae": 1.0, "rmse": 1.0, "wape": 0.02, "mase": 0.5}
        for d, u in series_elegiveis
    ]
    tabela_series_pers = [
        {
            "destino": d,
            "uf": u,
            "n": 9,
            "mae": mae_pers,
            "rmse": mae_pers,
            "wape": 0.02,
            "mase": 0.5,
        }
        for d, u in series_elegiveis
    ]
    tabela_series_saz = [
        {
            "destino": d,
            "uf": u,
            "n": 9,
            "mae": mae_saz,
            "rmse": mae_saz,
            "wape": 0.02,
            "mase": 0.5,
        }
        for d, u in series_elegiveis
    ]

    metricas_cl = {
        "data_utc": "2026-11-16T00:00:00Z",
        "sha256_painel": "outro_sha" if painel_divergente else sha_painel,
        "hash_recorte": "outro_recorte" if recorte_divergente else hash_recorte_val,
        "populacao": "Admissões com superior+",
        "limites": ["limite1"],
        "baselines": {
            "persistencia": {
                "cv_resumo": {
                    "folds_validos": 3,
                    "mae_media": 5.0,
                    "mae_desvio": 0.2,
                    "wape_media": 0.1,
                    "wape_desvio": 0.01,
                },
                "folds": [{"mase": 1.0}, {"mase": 1.2}, {"mase": 1.4}],
            },
            "sazonal": {
                "cv_resumo": {
                    "folds_validos": 3,
                    "mae_media": 4.0,
                    "mae_desvio": 0.15,
                    "wape_media": 0.08,
                    "wape_desvio": 0.005,
                },
                "folds": [{"mase": 0.9}, {"mase": 1.0}, {"mase": 1.1}],
            },
        },
        "resumo_cv": {
            "ridge": {
                "mae_media": 3.0,
                "mae_desvio": 0.1,
                "rmse_media": 4.0,
                "rmse_desvio": 0.1,
                "wape_media": 0.06,
                "wape_desvio": 0.005,
                "mase_media": 0.8,
                "mase_desvio": 0.02,
            },
            "random_forest": {
                "mae_media": 3.5,
                "mae_desvio": 0.12,
                "rmse_media": 4.5,
                "rmse_desvio": 0.12,
                "wape_media": 0.07,
                "wape_desvio": 0.006,
                "mase_media": 0.85,
                "mase_desvio": 0.03,
            },
            "hist_gradient_boosting": {
                "mae_media": 3.2,
                "mae_desvio": 0.11,
                "rmse_media": 4.2,
                "rmse_desvio": 0.11,
                "wape_media": 0.065,
                "wape_desvio": 0.005,
                "mase_media": 0.82,
                "mase_desvio": 0.025,
            },
        },
        "validacao_externa": {
            "periodo": ["202501", "202509"],
            "series_elegiveis": len(series_elegiveis),
            "baselines": {
                "persistencia": {
                    "n": len(series_elegiveis) * 9,
                    "mae": mae_pers,
                    "rmse": mae_pers,
                    "wape": 0.02,
                    "mase": 0.5,
                    "tabela_series": tabela_series_pers,
                },
                "sazonal": {
                    "n": len(series_elegiveis) * 9,
                    "mae": mae_saz,
                    "rmse": mae_saz,
                    "wape": 0.02,
                    "mase": 0.5,
                    "tabela_series": tabela_series_saz,
                },
            },
            "modelos": {
                "ridge": {
                    "n": len(series_elegiveis) * 9,
                    "mae": 1.0,
                    "rmse": 1.0,
                    "wape": 0.02,
                    "mase": 0.5,
                    "tabela_series": tabela_series_cl,
                },
                "random_forest": {
                    "n": len(series_elegiveis) * 9,
                    "mae": 1.0,
                    "rmse": 1.0,
                    "wape": 0.02,
                    "mase": 0.5,
                    "tabela_series": tabela_series_cl,
                },
                "hist_gradient_boosting": {
                    "n": len(series_elegiveis) * 9,
                    "mae": 1.0,
                    "rmse": 1.0,
                    "wape": 0.02,
                    "mase": 0.5,
                    "tabela_series": tabela_series_cl,
                },
            },
        },
        "hiperparametros_e_cv": {
            "ridge": {"melhores_parametros": {"alpha": 1.0}},
            "random_forest": {"melhores_parametros": {"n_estimators": 100}},
            "hist_gradient_boosting": {"melhores_parametros": {"max_iter": 100}},
        },
    }
    p_metricas_cl = dir_classicos / "metricas.json"
    p_metricas_cl.write_text(json.dumps(metricas_cl, indent=2), encoding="utf-8")
    sha_metricas_cl = hashlib.sha256(p_metricas_cl.read_bytes()).hexdigest()

    manifesto_cl = {
        "versao_manifesto": "1.0",
        "sha256_painel": "outro_sha" if painel_divergente else sha_painel,
        "caminho_painel": str(p_painel),
        "data_utc": "2026-11-16T00:00:00Z",
        "seed": 42,
        "n_iter": 10,
        "hash_recorte": hash_recorte_val,
        "sha256_escopo": "escopo_hash_123",
        "recorte": {
            "decisao": "R29",
            "versao": "1.0.0",
            "destinos": destinos,
            "ufs": ufs,
            "hash_recorte": hash_recorte_val,
        },
        "versoes": {"scikit-learn": "1.4.0"},
        "arquivos": {
            "modelos.joblib": (
                "dummy_sha_joblib_123456789012345678901234567890123456789012345678901234"
            ),
            "previsoes.parquet": (
                sha_prev_cl
                if not adulterar_parquet
                else "sha_falso_123456789012345678901234567890123456789012345678901234"
            ),
            "metricas.json": sha_metricas_cl,
        },
    }
    p_man_cl = dir_classicos / "manifesto.json"
    p_man_cl.write_text(json.dumps(manifesto_cl, indent=2), encoding="utf-8")

    dir_rna = dir_base / "rna"
    dir_rna.mkdir(parents=True, exist_ok=True)

    linhas_prev_rna = []
    for m in meses_val:
        for d, u in series_elegiveis:
            alvo_real = 50.0 + (1.0 if d == "analista_dados_bi" else 2.0)
            linhas_prev_rna.append({
                "competencia": m,
                "destino": d,
                "uf": u,
                "modelo": "MLP_A_global_validacao",
                "alvo": alvo_real,
                "previsao": alvo_real + 0.5,
            })
    df_prev_rna = pd.DataFrame(linhas_prev_rna)
    p_prev_rna = dir_rna / "previsoes.parquet"
    df_prev_rna.to_parquet(p_prev_rna, index=False)
    sha_prev_rna = hashlib.sha256(p_prev_rna.read_bytes()).hexdigest()

    tabela_series_rna = [
        {"destino": d, "uf": u, "n": 9, "mae": 0.5, "rmse": 0.5, "wape": 0.01, "mase": 0.3}
        for d, u in series_elegiveis
    ]

    metricas_rna = {
        "sha256_painel": sha_painel,
        "data_utc": "2026-11-16T00:00:00Z",
        "recorte": {"hash_recorte": hash_recorte_val, "sha256_escopo": "escopo_hash_123"},
        "versoes": {"torch": "2.2.0"},
        "seeds": 42,
        "params": {},
        "feature_list": {},
        "intervalos": {"treino_inicio": "202101", "treino_fim": "202409"},
        "cv_ranking": ["A", "B"],
        "melhor_config": {
            "nome": "A",
            "params": {
                "hidden_layers": [64, 32],
                "dropout": 0.1,
                "lr": 0.001,
                "batch_size": 128,
                "nome": "A",
            },
            "num_epochs_refit": 10,
        },
        "configs_detalhes": {
            "A": {
                "mae_medio": 2.5,
                "mae_desvio": 0.1,
                "wape_medio": 0.05,
                "wape_desvio": 0.005,
                "mase_medio": 0.7,
                "mase_desvio": 0.02,
            },
            "B": {
                "mae_medio": 3.0,
                "mae_desvio": 0.15,
                "wape_medio": 0.06,
                "wape_desvio": 0.006,
                "mase_medio": 0.8,
                "mase_desvio": 0.03,
            },
        },
        "validacao_externa": {
            "n": len(series_elegiveis) * 9,
            "mae": 0.5,
            "rmse": 0.5,
            "wape": 0.01,
            "mase": 0.3,
            "tabela_series": tabela_series_rna,
        },
        "sha256_artefatos": {
            "checkpoint_rna.pt": (
                "dummy_sha_pt_123456789012345678901234567890123456789012345678901234"
            ),
            "preprocessador.json": (
                "dummy_sha_prep_123456789012345678901234567890123456789012345678901234"
            ),
            "previsoes.parquet": sha_prev_rna,
        },
    }
    p_metricas_rna = dir_rna / "metricas.json"
    p_metricas_rna.write_text(json.dumps(metricas_rna, indent=2), encoding="utf-8")

    return p_painel, dir_classicos, dir_rna, p_escopo


def test_exportar_snapshot_sucesso_e_schema(tmp_path: Path):
    """Verifica exportação bem sucedida de snapshot com todos os campos e 6 modelos."""
    p_painel, dir_classicos, dir_rna, p_escopo = _criar_artefatos_sinteticos(tmp_path)
    dir_saida = tmp_path / "saida_snapshot"

    snap = exportar_snapshot_mercado(
        painel_path=p_painel,
        dir_classicos=dir_classicos,
        dir_rna=dir_rna,
        dir_saida=dir_saida,
        escopo_path=p_escopo,
    )

    p_snap_json = dir_saida / "snapshot_mercado.json"
    p_man_json = dir_saida / "manifesto.json"
    assert p_snap_json.exists()
    assert p_man_json.exists()

    with p_man_json.open("r", encoding="utf-8") as f:
        man = json.load(f)
    assert man["schema_version"] == "1.0"
    assert man["arquivo"] == "snapshot_mercado.json"
    assert man["sha256"] == hashlib.sha256(p_snap_json.read_bytes()).hexdigest()

    assert snap["schema_version"] == "1.0"
    assert "gerado_em" in snap and snap["gerado_em"].endswith("Z")
    assert snap["promocao"]["status"] == "nao_decidida"
    assert snap["promocao"]["modelo_exibido"] == "sazonal"

    modelos = snap["modelos"]
    assert len(modelos) == 6
    ids = [m["id"] for m in modelos]
    assert ids == [
        "persistencia",
        "sazonal",
        "ridge",
        "random_forest",
        "hist_gradient_boosting",
        "mlp",
    ]

    exibidos = [m for m in modelos if m["exibido_ao_usuario"]]
    assert len(exibidos) == 1
    assert exibidos[0]["id"] == "sazonal"
    assert all(not m["promovido"] for m in modelos)

    assert len(snap["series"]) > 0
    series_31 = [s for s in snap["series"] if s["uf"] == "31"]
    assert len(series_31) > 0
    assert not series_31[0]["elegivel"]
    assert series_31[0]["previsoes_validacao"] == {}
    assert series_31[0]["metricas_validacao"] == {}

    assert len(snap["contexto_regional"]) > 0


def test_exportar_snapshot_modelo_exibido_persistencia(tmp_path: Path):
    """Verifica que quando persistência tem menor MAE, ela é o modelo exibido."""
    p_painel, dir_classicos, dir_rna, p_escopo = _criar_artefatos_sinteticos(
        tmp_path, persistencia_vence=True
    )
    dir_saida = tmp_path / "saida_pers"

    snap = exportar_snapshot_mercado(
        painel_path=p_painel,
        dir_classicos=dir_classicos,
        dir_rna=dir_rna,
        dir_saida=dir_saida,
        escopo_path=p_escopo,
    )
    assert snap["promocao"]["modelo_exibido"] == "persistencia"
    exibidos = [m for m in snap["modelos"] if m["exibido_ao_usuario"]]
    assert len(exibidos) == 1
    assert exibidos[0]["id"] == "persistencia"


def test_exportar_snapshot_dir_saida_existente_recusa(tmp_path: Path):
    """dir_saida já existente gera FileExistsError e nada é alterado."""
    p_painel, dir_classicos, dir_rna, p_escopo = _criar_artefatos_sinteticos(tmp_path)
    dir_saida = tmp_path / "saida_ocupada"
    dir_saida.mkdir(parents=True, exist_ok=True)
    canary = dir_saida / "canary.txt"
    canary.write_text("intacto", encoding="utf-8")

    with pytest.raises(FileExistsError):
        exportar_snapshot_mercado(
            painel_path=p_painel,
            dir_classicos=dir_classicos,
            dir_rna=dir_rna,
            dir_saida=dir_saida,
            escopo_path=p_escopo,
        )

    assert canary.read_text(encoding="utf-8") == "intacto"


def test_exportar_snapshot_adulteracao_hash_previsoes_recusa(tmp_path: Path):
    """Hash adulterado de previsoes.parquet gera ValueError."""
    p_painel, dir_classicos, dir_rna, p_escopo = _criar_artefatos_sinteticos(
        tmp_path, adulterar_parquet=True
    )
    dir_saida = tmp_path / "saida_corrompida"

    with pytest.raises(ValueError, match="[Hh]ash|diverg"):
        exportar_snapshot_mercado(
            painel_path=p_painel,
            dir_classicos=dir_classicos,
            dir_rna=dir_rna,
            dir_saida=dir_saida,
            escopo_path=p_escopo,
        )


def test_exportar_snapshot_painel_divergente_recusa(tmp_path: Path):
    """sha256_painel divergente gera ValueError."""
    p_painel, dir_classicos, dir_rna, p_escopo = _criar_artefatos_sinteticos(
        tmp_path, painel_divergente=True
    )
    dir_saida = tmp_path / "saida_diverg_painel"

    with pytest.raises(ValueError, match="[Pp]ainel|sha256|diverg"):
        exportar_snapshot_mercado(
            painel_path=p_painel,
            dir_classicos=dir_classicos,
            dir_rna=dir_rna,
            dir_saida=dir_saida,
            escopo_path=p_escopo,
        )


def test_exportar_snapshot_competencia_2026_recusa(tmp_path: Path):
    """Competência >= 202601 gera ValueError antes de gerar saída."""
    p_painel, dir_classicos, dir_rna, p_escopo = _criar_artefatos_sinteticos(
        tmp_path, competencia_2026=True
    )
    dir_saida = tmp_path / "saida_2026"

    with pytest.raises(ValueError, match="2026|holdout"):
        exportar_snapshot_mercado(
            painel_path=p_painel,
            dir_classicos=dir_classicos,
            dir_rna=dir_rna,
            dir_saida=dir_saida,
            escopo_path=p_escopo,
        )
    assert not dir_saida.exists()


def test_exportar_snapshot_chaves_divergentes_recusa(tmp_path: Path):
    """Chaves de validação divergentes entre modelos geram ValueError."""
    p_painel, dir_classicos, dir_rna, p_escopo = _criar_artefatos_sinteticos(
        tmp_path, chaves_divergentes=True
    )
    dir_saida = tmp_path / "saida_chaves_diverg"

    with pytest.raises(ValueError, match="[Cc]haves|diverg"):
        exportar_snapshot_mercado(
            painel_path=p_painel,
            dir_classicos=dir_classicos,
            dir_rna=dir_rna,
            dir_saida=dir_saida,
            escopo_path=p_escopo,
        )


def test_exportar_snapshot_elegiveis_divergentes_recusa(tmp_path: Path):
    """Séries elegíveis calculadas divergentes das validações dos clássicos geram ValueError."""
    p_painel, dir_classicos, dir_rna, p_escopo = _criar_artefatos_sinteticos(
        tmp_path, elegiveis_divergentes=True
    )
    dir_saida = tmp_path / "saida_eleg_diverg"

    with pytest.raises(ValueError, match="[Ee]leg|diverg"):
        exportar_snapshot_mercado(
            painel_path=p_painel,
            dir_classicos=dir_classicos,
            dir_rna=dir_rna,
            dir_saida=dir_saida,
            escopo_path=p_escopo,
        )


def test_exportar_snapshot_nan_observado_e_regional_ausente(tmp_path: Path):
    """NaN observado vira null (sem token 'NaN') e mês com UF ausente no regional vira null."""
    p_painel, dir_classicos, dir_rna, p_escopo = _criar_artefatos_sinteticos(
        tmp_path, incluir_nan_observado=True, omitir_uf_regional=True
    )
    dir_saida = tmp_path / "saida_nan"

    snap = exportar_snapshot_mercado(
        painel_path=p_painel,
        dir_classicos=dir_classicos,
        dir_rna=dir_rna,
        dir_saida=dir_saida,
        escopo_path=p_escopo,
    )

    conteudo_texto = (dir_saida / "snapshot_mercado.json").read_text(encoding="utf-8")
    assert "NaN" not in conteudo_texto
    assert "null" in conteudo_texto

    serie_bi_35 = next(
        s for s in snap["series"] if s["destino"] == "analista_dados_bi" and s["uf"] == "35"
    )
    obs_202001 = next(o for o in serie_bi_35["observado"] if o["competencia"] == "202001")
    assert obs_202001["admissoes"] is None

    reg_bi_sudeste = next(
        r for r in snap["contexto_regional"] if r["destino"] == "analista_dados_bi"
    )
    obs_reg_202002 = next(o for o in reg_bi_sudeste["observado"] if o["competencia"] == "202002")
    assert obs_reg_202002["admissoes"] is None
