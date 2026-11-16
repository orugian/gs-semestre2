"""Snapshot único Adzuna (D05a): teto de chamadas por contador, JSON bruto com hash, resumo."""

from __future__ import annotations

import hashlib
import json

import pytest

from citizentech_ml.mercado.adzuna import (
    ConsultaAdzuna,
    LimiteChamadasExcedido,
    coletar_snapshot_adzuna,
)

CONSULTAS = [
    ConsultaAdzuna(destino="analista_dados_bi", territorio="SP", termo="analista de dados"),
    ConsultaAdzuna(destino="analista_dados_bi", territorio="BR", termo="analista de dados"),
]


class HttpFalso:
    def __init__(self, status: int = 200, contagem: int = 321) -> None:
        self.status = status
        self.contagem = contagem
        self.urls: list[str] = []

    def __call__(self, url: str) -> tuple[int, bytes]:
        self.urls.append(url)
        corpo = {"count": self.contagem, "mean": 5000.5, "results": [{"title": "Analista"}]}
        return self.status, json.dumps(corpo).encode("utf-8")


def _contador(tmp_path, total: int):
    caminho = tmp_path / "contador_chamadas.json"
    caminho.write_text(json.dumps({"total": total, "registro": []}), encoding="utf-8")
    return caminho


def test_coleta_grava_brutos_com_hash_resumo_e_incrementa_contador(tmp_path):
    contador = _contador(tmp_path, 1)
    http = HttpFalso()

    resumo = coletar_snapshot_adzuna(
        CONSULTAS, tmp_path / "20261116", contador, http=http,
        credenciais=("id-falso", "chave-falsa"), maximo=12,
    )

    estado = json.loads(contador.read_text(encoding="utf-8"))
    assert estado["total"] == 3
    assert len(estado["registro"]) == 2
    assert all("chave-falsa" not in json.dumps(r) for r in estado["registro"])
    assert len(http.urls) == 2
    itens = resumo["itens"]
    assert [(i["destino"], i["territorio"], i["contagem_anuncios"]) for i in itens] == [
        ("analista_dados_bi", "SP", 321),
        ("analista_dados_bi", "BR", 321),
    ]
    for item in itens:
        bruto = (tmp_path / "20261116" / item["arquivo_bruto"]).read_bytes()
        assert hashlib.sha256(bruto).hexdigest() == item["sha256_bruto"]
        assert b"chave-falsa" not in bruto
    assert resumo["natureza"] == "amostra_pontual"
    assert resumo["atribuicao"].startswith("Jobs by Adzuna")
    manifesto = json.loads((tmp_path / "20261116" / "manifesto.json").read_text("utf-8"))
    bruto_resumo = (tmp_path / "20261116" / "resumo_adzuna.json").read_bytes()
    assert manifesto["sha256"] == hashlib.sha256(bruto_resumo).hexdigest()
    texto_resumo = bruto_resumo.decode("utf-8").lower()
    assert "chave-falsa" not in texto_resumo and "vaga" not in texto_resumo


def test_teto_do_contador_impede_qualquer_chamada(tmp_path):
    contador = _contador(tmp_path, 11)
    http = HttpFalso()

    with pytest.raises(LimiteChamadasExcedido):
        coletar_snapshot_adzuna(
            CONSULTAS, tmp_path / "20261116", contador, http=http,
            credenciais=("id", "chave"), maximo=12,
        )

    assert http.urls == []
    assert json.loads(contador.read_text(encoding="utf-8"))["total"] == 11
    assert not (tmp_path / "20261116").exists()


def test_diretorio_existente_nao_e_sobrescrito_nem_gasta_chamada(tmp_path):
    contador = _contador(tmp_path, 1)
    (tmp_path / "20261116").mkdir()
    http = HttpFalso()

    with pytest.raises(FileExistsError):
        coletar_snapshot_adzuna(
            CONSULTAS, tmp_path / "20261116", contador, http=http,
            credenciais=("id", "chave"), maximo=12,
        )
    assert http.urls == []


def test_erro_http_conta_a_chamada_e_vira_item_indisponivel(tmp_path):
    contador = _contador(tmp_path, 1)
    http = HttpFalso(status=500)

    resumo = coletar_snapshot_adzuna(
        CONSULTAS, tmp_path / "20261116", contador, http=http,
        credenciais=("id", "chave"), maximo=12,
    )

    assert json.loads(contador.read_text(encoding="utf-8"))["total"] == 3
    assert all(i["contagem_anuncios"] is None for i in resumo["itens"])
    assert all(i["status_http"] == 500 for i in resumo["itens"])
