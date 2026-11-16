"""Testes das rotas públicas de mercado e painel técnico R06."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from citizentech.main import app


def criar_snapshot_sintetico(diretorio: Path, dados_custom: dict[str, Any] | None = None) -> Path:
    """Helper de teste que cria snapshot_mercado.json e manifesto.json válidos."""
    diretorio.mkdir(parents=True, exist_ok=True)
    snapshot = dados_custom or {
        "schema_version": "1.0",
        "gerado_em": "2026-11-16T00:00:00Z",
        "metadados_fonte": {
            "fonte": "Novo Caged — microdados públicos do MTE (PDET)",
            "populacao": (
                "Admissões formais com ensino superior completo ou mais "
                "nas ocupações CBO curadas de cada destino"
            ),
            "recorte": {
                "decisao": "R29",
                "hash_recorte": "recorte_hash_123",
                "sha256_escopo": "escopo_hash_123",
            },
            "sha256_painel": "painel_hash_123",
            "competencia_min": "202001",
            "competencia_max": "202509",
        },
        "densidade": {
            "limite_minimo": 10.0,
            "periodo_treino": ["202101", "202409"],
        },
        "promocao": {
            "criterio": "D10a congelado",
            "status": "nao_decidida",
            "modelo_exibido": "sazonal",
            "motivo": "Holdout permanece fechado",
        },
        "series": [
            {
                "destino": "analista_dados_bi",
                "uf": "35",
                "elegivel": True,
                "motivo_densidade": "aprovado",
                "media_alvo_treino": 123.4,
                "observado": [
                    {
                        "competencia": "202001",
                        "admissoes": None,  # Mês ausente
                        "admissoes_total": 30.0,
                        "desligamentos": 10.0,
                    },
                    {
                        "competencia": "202501",
                        "admissoes": 20.0,
                        "admissoes_total": 40.0,
                        "desligamentos": 15.0,
                    },
                ],
                "previsoes_validacao": {
                    "persistencia": [
                        {"competencia": "202501", "previsao": 45.0, "alvo": 50.0}
                    ],
                    "sazonal": [
                        {"competencia": "202501", "previsao": 48.0, "alvo": 50.0}
                    ],
                    "ridge": [
                        {"competencia": "202501", "previsao": 47.0, "alvo": 50.0}
                    ],
                    "random_forest": [
                        {"competencia": "202501", "previsao": 46.0, "alvo": 50.0}
                    ],
                    "hist_gradient_boosting": [
                        {"competencia": "202501", "previsao": 46.5, "alvo": 50.0}
                    ],
                    "mlp": [
                        {"competencia": "202501", "previsao": 49.0, "alvo": 50.0}
                    ],
                },
                "metricas_validacao": {
                    "persistencia": {"n": 9, "mae": 5.0, "rmse": 6.0, "wape": 0.1, "mase": 1.2},
                    "sazonal": {"n": 9, "mae": 2.0, "rmse": 3.0, "wape": 0.05, "mase": 0.8},
                    "ridge": {"n": 9, "mae": 3.0, "rmse": 4.0, "wape": 0.07, "mase": 0.9},
                    "random_forest": {
                        "n": 9, "mae": 4.0, "rmse": 5.0, "wape": 0.08, "mase": 1.0
                    },
                    "hist_gradient_boosting": {
                        "n": 9, "mae": 3.5, "rmse": 4.5, "wape": 0.075, "mase": 0.95
                    },
                    "mlp": {"n": 9, "mae": 2.5, "rmse": 3.5, "wape": 0.06, "mase": 0.85},
                },
            },
            {
                "destino": "analista_dados_bi",
                "uf": "31",
                "elegivel": False,
                "motivo_densidade": "densidade_insuficiente",
                "media_alvo_treino": 4.5,
                "observado": [
                    {
                        "competencia": "202001",
                        "admissoes": 2.0,
                        "admissoes_total": 5.0,
                        "desligamentos": 1.0,
                    },
                    {
                        "competencia": "202501",
                        "admissoes": 3.0,
                        "admissoes_total": 6.0,
                        "desligamentos": 2.0,
                    },
                ],
                "previsoes_validacao": {},
                "metricas_validacao": {},
            },
        ],
        "contexto_regional": [
            {
                "destino": "analista_dados_bi",
                "regiao": "Sudeste",
                "ufs": ["31", "32", "33", "35"],
                "observado": [
                    {"competencia": "202001", "admissoes": 150.0},
                    {"competencia": "202501", "admissoes": 200.0},
                ],
            }
        ],
        "modelos": [
            {
                "id": "persistencia",
                "nome": "Persistência 3M",
                "tipo": "baseline",
                "promovido": False,
                "exibido_ao_usuario": False,
                "metricas_validacao_global": {
                    "n": 495, "mae": 5.0, "rmse": 6.0, "wape": 0.1, "mase": 1.2
                },
                "metricas_cv_treino": {
                    "mae_medio": 5.0,
                    "mae_desvio": 0.2,
                    "wape_medio": 0.1,
                    "wape_desvio": 0.01,
                    "mase_medio": 1.2,
                    "mase_desvio": 0.05,
                },
                "model_card": {
                    "_id": "persistencia:1.0",
                    "modelo": "persistencia",
                    "versao_artefato": "classicos",
                    "tipo": "baseline",
                    "data_treino_utc": "2026-11-16T00:00:00Z",
                    "periodo_treino": ["202101", "202409"],
                    "periodo_validacao": ["202501", "202509"],
                    "populacao": "Admissões com superior+",
                    "sha256_painel": "painel_hash_123",
                    "hash_recorte": "recorte_hash_123",
                    "hiperparametros": {"regra": "admissoes_soma_3m"},
                    "seed": 42,
                    "versoes": {},
                    "sha256_artefatos": {},
                    "selecao": "Baseline determinístico",
                    "limites": [],
                    "status_promocao": "nao_decidida",
                },
            },
            {
                "id": "sazonal",
                "nome": "Sazonal Ano Anterior",
                "tipo": "baseline",
                "promovido": False,
                "exibido_ao_usuario": True,
                "metricas_validacao_global": {
                    "n": 495, "mae": 2.0, "rmse": 3.0, "wape": 0.05, "mase": 0.8
                },
                "metricas_cv_treino": {
                    "mae_medio": 2.0,
                    "mae_desvio": 0.1,
                    "wape_medio": 0.05,
                    "wape_desvio": 0.005,
                    "mase_medio": 0.8,
                    "mase_desvio": 0.03,
                },
                "model_card": {
                    "_id": "sazonal:1.0",
                    "modelo": "sazonal",
                    "versao_artefato": "classicos",
                    "tipo": "baseline",
                    "data_treino_utc": "2026-11-16T00:00:00Z",
                    "periodo_treino": ["202101", "202409"],
                    "periodo_validacao": ["202501", "202509"],
                    "populacao": "Admissões com superior+",
                    "sha256_painel": "painel_hash_123",
                    "hash_recorte": "recorte_hash_123",
                    "hiperparametros": {"regra": "admissoes_sazonal_ano_anterior"},
                    "seed": 42,
                    "versoes": {},
                    "sha256_artefatos": {},
                    "selecao": "Baseline determinístico",
                    "limites": [],
                    "status_promocao": "nao_decidida",
                },
            },
            {
                "id": "ridge",
                "nome": "Ridge Regression",
                "tipo": "classico",
                "promovido": False,
                "exibido_ao_usuario": False,
                "metricas_validacao_global": {
                    "n": 495, "mae": 3.0, "rmse": 4.0, "wape": 0.07, "mase": 0.9
                },
                "metricas_cv_treino": {
                    "mae_medio": 3.0,
                    "mae_desvio": 0.15,
                    "wape_medio": 0.07,
                    "wape_desvio": 0.008,
                    "mase_medio": 0.9,
                    "mase_desvio": 0.04,
                },
                "model_card": {
                    "_id": "ridge:1.0",
                    "modelo": "ridge",
                    "versao_artefato": "classicos",
                    "tipo": "classico",
                    "data_treino_utc": "2026-11-16T00:00:00Z",
                    "periodo_treino": ["202101", "202409"],
                    "periodo_validacao": ["202501", "202509"],
                    "populacao": "Admissões com superior+",
                    "sha256_painel": "painel_hash_123",
                    "hash_recorte": "recorte_hash_123",
                    "hiperparametros": {},
                    "seed": 42,
                    "versoes": {},
                    "sha256_artefatos": {},
                    "selecao": "CV 3 folds",
                    "limites": [],
                    "status_promocao": "nao_decidida",
                },
            },
            {
                "id": "random_forest",
                "nome": "Random Forest",
                "tipo": "classico",
                "promovido": False,
                "exibido_ao_usuario": False,
                "metricas_validacao_global": {
                    "n": 495, "mae": 4.0, "rmse": 5.0, "wape": 0.08, "mase": 1.0
                },
                "metricas_cv_treino": {
                    "mae_medio": 4.0,
                    "mae_desvio": 0.2,
                    "wape_medio": 0.08,
                    "wape_desvio": 0.01,
                    "mase_medio": 1.0,
                    "mase_desvio": 0.05,
                },
                "model_card": {
                    "_id": "random_forest:1.0",
                    "modelo": "random_forest",
                    "versao_artefato": "classicos",
                    "tipo": "classico",
                    "data_treino_utc": "2026-11-16T00:00:00Z",
                    "periodo_treino": ["202101", "202409"],
                    "periodo_validacao": ["202501", "202509"],
                    "populacao": "Admissões com superior+",
                    "sha256_painel": "painel_hash_123",
                    "hash_recorte": "recorte_hash_123",
                    "hiperparametros": {},
                    "seed": 42,
                    "versoes": {},
                    "sha256_artefatos": {},
                    "selecao": "CV 3 folds",
                    "limites": [],
                    "status_promocao": "nao_decidida",
                },
            },
            {
                "id": "hist_gradient_boosting",
                "nome": "Hist Gradient Boosting",
                "tipo": "classico",
                "promovido": False,
                "exibido_ao_usuario": False,
                "metricas_validacao_global": {
                    "n": 495, "mae": 3.5, "rmse": 4.5, "wape": 0.075, "mase": 0.95
                },
                "metricas_cv_treino": {
                    "mae_medio": 3.5,
                    "mae_desvio": 0.18,
                    "wape_medio": 0.075,
                    "wape_desvio": 0.009,
                    "mase_medio": 0.95,
                    "mase_desvio": 0.045,
                },
                "model_card": {
                    "_id": "hist_gradient_boosting:1.0",
                    "modelo": "hist_gradient_boosting",
                    "versao_artefato": "classicos",
                    "tipo": "classico",
                    "data_treino_utc": "2026-11-16T00:00:00Z",
                    "periodo_treino": ["202101", "202409"],
                    "periodo_validacao": ["202501", "202509"],
                    "populacao": "Admissões com superior+",
                    "sha256_painel": "painel_hash_123",
                    "hash_recorte": "recorte_hash_123",
                    "hiperparametros": {},
                    "seed": 42,
                    "versoes": {},
                    "sha256_artefatos": {},
                    "selecao": "CV 3 folds",
                    "limites": [],
                    "status_promocao": "nao_decidida",
                },
            },
            {
                "id": "mlp",
                "nome": "Rede Neural MLP",
                "tipo": "rna",
                "promovido": False,
                "exibido_ao_usuario": False,
                "metricas_validacao_global": {
                    "n": 495, "mae": 2.5, "rmse": 3.5, "wape": 0.06, "mase": 0.85
                },
                "metricas_cv_treino": {
                    "mae_medio": 2.5,
                    "mae_desvio": 0.12,
                    "wape_medio": 0.06,
                    "wape_desvio": 0.007,
                    "mase_medio": 0.85,
                    "mase_desvio": 0.04,
                },
                "model_card": {
                    "_id": "mlp:1.0",
                    "modelo": "mlp",
                    "versao_artefato": "rna",
                    "tipo": "rna",
                    "data_treino_utc": "2026-11-16T00:00:00Z",
                    "periodo_treino": ["202101", "202409"],
                    "periodo_validacao": ["202501", "202509"],
                    "populacao": "Admissões com superior+",
                    "sha256_painel": "painel_hash_123",
                    "hash_recorte": "recorte_hash_123",
                    "hiperparametros": {},
                    "seed": 42,
                    "versoes": {},
                    "sha256_artefatos": {},
                    "selecao": "CV 3 folds",
                    "limites": [],
                    "status_promocao": "nao_decidida",
                },
            },
        ],
    }

    caminho_snap = diretorio / "snapshot_mercado.json"
    conteudo_bytes = json.dumps(snapshot, ensure_ascii=False, indent=2).encode("utf-8")
    caminho_snap.write_bytes(conteudo_bytes)

    sha256_snap = hashlib.sha256(conteudo_bytes).hexdigest()
    manifesto = {
        "schema_version": "1.0",
        "arquivo": "snapshot_mercado.json",
        "sha256": sha256_snap,
        "gerado_em": "2026-11-16T00:00:00Z",
    }
    caminho_man = diretorio / "manifesto.json"
    caminho_man.write_bytes(json.dumps(manifesto, ensure_ascii=False, indent=2).encode("utf-8"))

    return diretorio


def test_mercado_serie_elegivel_retorna_observado_e_previsto_com_metadados_t17(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """RED prioritário: série elegível retorna observado e previsto com metadados T17."""
    dir_snap = criar_snapshot_sintetico(tmp_path / "mercado_snap")
    monkeypatch.setenv("CITIZENTECH_MERCADO_SNAPSHOT", str(dir_snap))

    cliente = TestClient(app)
    resposta = cliente.get("/mercado/analista_dados_bi?uf=SP")

    assert resposta.status_code == 200
    dados = resposta.json()

    assert "observado" in dados and isinstance(dados["observado"], dict)
    assert "previsto" in dados and isinstance(dados["previsto"], dict)

    for secao in [dados["observado"], dados["previsto"]]:
        for campo in ["natureza", "fonte", "populacao", "unidade", "referencia_temporal"]:
            assert campo in secao
            assert secao[campo] is not None
            assert secao[campo] != ""

    assert dados["previsto"]["natureza"] == "previsto_retrospectivo"
    assert dados["previsto"]["status_promocao"] == "nao_decidida"
    assert dados["abstencao"] is None
    assert dados["amostra_adzuna"]["disponivel"] is False


def test_mercado_serie_nao_elegivel_retorna_abstencao_com_contexto_regional_t06(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """T06: série não elegível retorna abstenção com contexto regional observado."""
    dir_snap = criar_snapshot_sintetico(tmp_path / "mercado_snap_t06")
    monkeypatch.setenv("CITIZENTECH_MERCADO_SNAPSHOT", str(dir_snap))

    cliente = TestClient(app)
    resposta = cliente.get("/mercado/analista_dados_bi?uf=MG")

    assert resposta.status_code == 200
    dados = resposta.json()

    assert dados["previsto"] is None
    assert dados["abstencao"] is not None
    abst = dados["abstencao"]
    assert abst["motivo"] == "densidade_insuficiente"
    assert abst["media_alvo_treino"] == 4.5
    assert abst["limite_minimo"] == 10.0

    ctx_reg = abst["contexto_regional"]
    assert ctx_reg["natureza"] == "observado"
    assert ctx_reg["regiao"] == "Sudeste"
    assert isinstance(ctx_reg["serie"], list)
    assert len(ctx_reg["serie"]) > 0

    assert dados["observado"] is not None


def test_mercado_destino_desconhecido_ou_fora_do_mvp_retorna_404(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Destino desconhecido ou fora do escopo MVP gera HTTP 404."""
    dir_snap = criar_snapshot_sintetico(tmp_path / "mercado_snap_404")
    monkeypatch.setenv("CITIZENTECH_MERCADO_SNAPSHOT", str(dir_snap))

    cliente = TestClient(app)

    # 1. Destino fora do escopo MVP (R29)
    resp1 = cliente.get("/mercado/desenvolvedor_sistemas?uf=SP")
    assert resp1.status_code == 404
    d1 = resp1.json()
    assert "erro" in d1 and "detalhes" in d1

    # 2. Destino inexistente
    resp2 = cliente.get("/mercado/profissao_fantasma?uf=SP")
    assert resp2.status_code == 404
    d2 = resp2.json()
    assert "erro" in d2 and "detalhes" in d2


def test_mercado_uf_invalida_retorna_400(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """UF inválida retorna HTTP 400 com erro padronizado."""
    dir_snap = criar_snapshot_sintetico(tmp_path / "mercado_snap_400")
    monkeypatch.setenv("CITIZENTECH_MERCADO_SNAPSHOT", str(dir_snap))

    cliente = TestClient(app)
    resposta = cliente.get("/mercado/analista_dados_bi?uf=XX")
    assert resposta.status_code == 400
    dados = resposta.json()
    assert "erro" in dados and "detalhes" in dados


def test_mercado_uf_case_insensitive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """UF em minúsculas (sp) é aceita normalmente."""
    dir_snap = criar_snapshot_sintetico(tmp_path / "mercado_snap_uf_case")
    monkeypatch.setenv("CITIZENTECH_MERCADO_SNAPSHOT", str(dir_snap))

    cliente = TestClient(app)
    resposta = cliente.get("/mercado/analista_dados_bi?uf=sp")
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["uf"] == "SP"
    assert dados["uf_codigo"] == "35"


def test_mercado_variavel_ambiente_ausente_retorna_503(
    monkeypatch: pytest.MonkeyPatch
):
    """Sem variável de ambiente CITIZENTECH_MERCADO_SNAPSHOT retorna HTTP 503."""
    monkeypatch.delenv("CITIZENTECH_MERCADO_SNAPSHOT", raising=False)

    cliente = TestClient(app)
    resposta = cliente.get("/mercado/analista_dados_bi?uf=SP")
    assert resposta.status_code == 503
    dados = resposta.json()
    assert dados["erro"] == "Servico indisponivel"
    assert "detalhes" in dados
    assert "C:" not in dados["detalhes"]
    assert "/" not in dados["detalhes"]


def test_mercado_hash_adulterado_retorna_503_sem_vazar_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Snapshot adulterado (hash divergente) gera HTTP 503 sem caminho de disco nem stack."""
    dir_snap = criar_snapshot_sintetico(tmp_path / "mercado_snap_tamper")
    # Altera 1 byte de snapshot_mercado.json
    p_snap = dir_snap / "snapshot_mercado.json"
    p_snap.write_bytes(p_snap.read_bytes() + b"X")

    monkeypatch.setenv("CITIZENTECH_MERCADO_SNAPSHOT", str(dir_snap))

    cliente = TestClient(app)
    resposta = cliente.get("/mercado/analista_dados_bi?uf=SP")
    assert resposta.status_code == 503
    dados = resposta.json()
    assert dados["erro"] == "Servico indisponivel"
    assert str(dir_snap) not in dados["detalhes"]
    assert "Traceback" not in dados["detalhes"]


def test_mercado_schema_version_invalido_retorna_503_sem_vazar_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Manifesto com schema_version '9.9' gera HTTP 503 sem vazar caminhos."""
    dir_snap = criar_snapshot_sintetico(tmp_path / "mercado_snap_schema")
    p_man = dir_snap / "manifesto.json"
    man = json.loads(p_man.read_text(encoding="utf-8"))
    man["schema_version"] = "9.9"
    p_man.write_text(json.dumps(man), encoding="utf-8")

    monkeypatch.setenv("CITIZENTECH_MERCADO_SNAPSHOT", str(dir_snap))

    cliente = TestClient(app)
    resposta = cliente.get("/mercado/analista_dados_bi?uf=SP")
    assert resposta.status_code == 503
    dados = resposta.json()
    assert dados["erro"] == "Servico indisponivel"
    assert str(dir_snap) not in dados["detalhes"]


def test_mercado_modelos_retorna_6_modelos_na_ordem_com_um_exibido_e_mlp_rna(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Painel técnico R06: 6 modelos na ordem estrita, um exibido, todos promovido=false."""
    dir_snap = criar_snapshot_sintetico(tmp_path / "mercado_snap_mod")
    monkeypatch.setenv("CITIZENTECH_MERCADO_SNAPSHOT", str(dir_snap))

    cliente = TestClient(app)
    resposta = cliente.get("/mercado/analista_dados_bi/modelos?uf=SP")

    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["elegivel"] is True
    assert dados["motivo_densidade"] == "aprovado"

    modelos = dados["modelos"]
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
    assert exibidos[0]["id"] == dados["criterio_promocao"]["modelo_exibido"]
    assert all(not m["promovido"] for m in modelos)

    mod_mlp = next(m for m in modelos if m["id"] == "mlp")
    assert mod_mlp["tipo"] == "rna"
    assert "metricas_cv_treino" in mod_mlp
    assert len(mod_mlp["previsoes_validacao"]) > 0
    assert mod_mlp["metricas_serie"] is not None


def test_mercado_modelos_serie_nao_elegivel_retorna_metricas_null_e_previsoes_vazias(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Painel técnico para série não elegível retorna metricas_serie null e previsões vazias."""
    dir_snap = criar_snapshot_sintetico(tmp_path / "mercado_snap_mod_nao_eleg")
    monkeypatch.setenv("CITIZENTECH_MERCADO_SNAPSHOT", str(dir_snap))

    cliente = TestClient(app)
    resposta = cliente.get("/mercado/analista_dados_bi/modelos?uf=MG")

    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["elegivel"] is False

    for m in dados["modelos"]:
        assert m["metricas_serie"] is None
        assert m["previsoes_validacao"] == []


def test_mercado_mes_ausente_retorna_null_na_serie(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Mês ausente na série observada retorna valor null e nunca zero fabricado."""
    dir_snap = criar_snapshot_sintetico(tmp_path / "mercado_snap_null")
    monkeypatch.setenv("CITIZENTECH_MERCADO_SNAPSHOT", str(dir_snap))

    cliente = TestClient(app)
    resposta = cliente.get("/mercado/analista_dados_bi?uf=SP")

    assert resposta.status_code == 200
    dados = resposta.json()
    serie_obs = dados["observado"]["serie"]
    obs_202001 = next(item for item in serie_obs if item["competencia"] == "202001")
    assert obs_202001["valor"] is None


def test_mercado_respostas_respeitam_regra_linguagem_produto(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Regra de produto: proibido 'vaga' e 'probabilidade de contrata' nas respostas."""
    dir_snap = criar_snapshot_sintetico(tmp_path / "mercado_snap_ling")
    monkeypatch.setenv("CITIZENTECH_MERCADO_SNAPSHOT", str(dir_snap))

    cliente = TestClient(app)

    r1 = cliente.get("/mercado/analista_dados_bi?uf=SP")
    assert r1.status_code == 200
    t1 = r1.text.lower()
    assert "vaga" not in t1
    assert "probabilidade de contrata" not in t1
    assert "probabilidade de emprego" not in t1
    assert "vale a pena" not in t1

    r2 = cliente.get("/mercado/analista_dados_bi/modelos?uf=SP")
    assert r2.status_code == 200
    t2 = r2.text.lower()
    assert "vaga" not in t2
    assert "probabilidade de contrata" not in t2
    assert "probabilidade de emprego" not in t2
    assert "vale a pena" not in t2


def test_health_continua_ok():
    """Verifica que /health continua respondendo normalmente."""
    cliente = TestClient(app)
    resp = cliente.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
