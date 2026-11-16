"""Amostra pontual Adzuna (D05a) exibida em GET /mercado/{destino}, separada do Caged (T17)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from test_mercado import criar_snapshot_sintetico

from citizentech.main import app


def _criar_adzuna(diretorio: Path, adulterar: bool = False) -> Path:
    diretorio.mkdir(parents=True)
    resumo = {
        "schema_version": "1.0",
        "fonte": "Adzuna API (anúncios agregados de terceiros)",
        "atribuicao": "Jobs by Adzuna (https://www.adzuna.com.br)",
        "natureza": "amostra_pontual",
        "unidade": "anúncios publicados que correspondem ao termo de busca",
        "populacao": "Anúncios indexados pela Adzuna no Brasil no dia da coleta.",
        "coletado_em": "2026-11-16T13:30:00Z",
        "itens": [
            {"destino": "analista_dados_bi", "territorio": "SP", "termo_busca": "analista de dados",
             "status_http": 200, "contagem_anuncios": 274, "coletado_em": "2026-11-16T13:30:00Z"},
            {"destino": "analista_dados_bi", "territorio": "BR", "termo_busca": "analista de dados",
             "status_http": 200, "contagem_anuncios": 1036, "coletado_em": "2026-11-16T13:30:01Z"},
            {"destino": "analista_processos", "territorio": "SP", "termo_busca": "processos",
             "status_http": 500, "contagem_anuncios": None, "coletado_em": "2026-11-16T13:30:02Z"},
        ],
    }
    bruto = json.dumps(resumo, ensure_ascii=False).encode("utf-8")
    (diretorio / "resumo_adzuna.json").write_bytes(bruto)
    sha = "0" * 64 if adulterar else hashlib.sha256(bruto).hexdigest()
    (diretorio / "manifesto.json").write_text(
        json.dumps({"schema_version": "1.0", "arquivo": "resumo_adzuna.json", "sha256": sha}),
        encoding="utf-8",
    )
    return diretorio


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "CITIZENTECH_MERCADO_SNAPSHOT", str(criar_snapshot_sintetico(tmp_path / "snap"))
    )
    return TestClient(app)


def test_amostra_adzuna_disponivel_mostra_contagens_com_atribuicao_e_data(
    cliente, tmp_path, monkeypatch
):
    monkeypatch.setenv("CITIZENTECH_ADZUNA_SNAPSHOT", str(_criar_adzuna(tmp_path / "adz")))

    amostra = cliente.get("/mercado/analista_dados_bi?uf=SP").json()["amostra_adzuna"]

    assert amostra["disponivel"] is True
    assert amostra["natureza"] == "amostra_pontual"
    assert amostra["atribuicao"].startswith("Jobs by Adzuna")
    assert amostra["coletado_em"] == "2026-11-16T13:30:00Z"
    assert amostra["unidade"] and amostra["fonte"] and amostra["populacao"]
    assert [(i["territorio"], i["contagem_anuncios"]) for i in amostra["itens"]] == [
        ("SP", 274),
        ("BR", 1036),
    ]
    assert "16/11/2026" in amostra["motivo"]


def test_item_com_falha_na_coleta_aparece_como_ausente_nunca_zero(cliente, tmp_path, monkeypatch):
    monkeypatch.setenv("CITIZENTECH_ADZUNA_SNAPSHOT", str(_criar_adzuna(tmp_path / "adz")))

    amostra = cliente.get("/mercado/analista_processos?uf=SP").json()["amostra_adzuna"]

    assert amostra["disponivel"] is True
    assert amostra["itens"] == [
        {"territorio": "SP", "termo_busca": "processos", "contagem_anuncios": None}
    ]


def test_amostra_adulterada_fica_indisponivel_sem_derrubar_o_mercado(
    cliente, tmp_path, monkeypatch
):
    monkeypatch.setenv(
        "CITIZENTECH_ADZUNA_SNAPSHOT", str(_criar_adzuna(tmp_path / "adz", adulterar=True))
    )

    resposta = cliente.get("/mercado/analista_dados_bi?uf=SP")

    assert resposta.status_code == 200
    amostra = resposta.json()["amostra_adzuna"]
    assert amostra["disponivel"] is False
    assert amostra["itens"] == []
    assert str(tmp_path) not in json.dumps(amostra)


def test_sem_snapshot_configurado_continua_indisponivel(cliente, monkeypatch):
    monkeypatch.delenv("CITIZENTECH_ADZUNA_SNAPSHOT", raising=False)

    amostra = cliente.get("/mercado/analista_dados_bi?uf=SP").json()["amostra_adzuna"]

    assert amostra["disponivel"] is False
    assert amostra["natureza"] == "amostra_pontual"
