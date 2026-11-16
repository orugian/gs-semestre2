"""Publicação idempotente dos model cards do snapshot de mercado no MongoDB."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path

import pytest

from citizentech_ml.mercado.model_cards import publicar_model_cards


def _card(modelo: str) -> dict:
    return {
        "_id": f"{modelo}:v_teste",
        "modelo": modelo,
        "versao_artefato": "v_teste",
        "status_promocao": "nao_decidida",
        "limites": ["teste"],
    }


def _gravar_snapshot(diretorio: Path, modelos: list[str], adulterar: bool = False) -> Path:
    diretorio.mkdir(parents=True)
    snapshot = {
        "schema_version": "1.0",
        "gerado_em": "2026-11-16T05:08:30Z",
        "modelos": [{"id": m, "model_card": _card(m)} for m in modelos],
    }
    bruto = json.dumps(snapshot, ensure_ascii=False).encode("utf-8")
    (diretorio / "snapshot_mercado.json").write_bytes(bruto)
    sha = hashlib.sha256(bruto).hexdigest()
    if adulterar:
        sha = "0" * 64
    (diretorio / "manifesto.json").write_text(
        json.dumps({"schema_version": "1.0", "arquivo": "snapshot_mercado.json", "sha256": sha}),
        encoding="utf-8",
    )
    return diretorio


class ColecaoFalsa:
    """Coleção em memória com a mesma semântica de update_one(upsert) usada pelo publicador."""

    def __init__(self) -> None:
        self.docs: dict[str, dict] = {}

    def update_one(self, filtro, atualizacao, upsert=False):
        _id = filtro["_id"]
        doc = self.docs.get(_id)
        if doc is None:
            assert upsert
            doc = {"_id": _id, **atualizacao.get("$setOnInsert", {})}
        doc.update(atualizacao["$set"])
        self.docs[_id] = doc


def test_publica_um_card_por_modelo_com_hash_do_snapshot(tmp_path):
    modelos = ["persistencia", "sazonal", "ridge", "random_forest", "hist_gradient_boosting", "mlp"]
    diretorio = _gravar_snapshot(tmp_path / "snap", modelos)
    colecao = ColecaoFalsa()

    resumo = publicar_model_cards(diretorio, colecao)

    assert sorted(colecao.docs) == sorted(f"{m}:v_teste" for m in modelos)
    sha = hashlib.sha256((diretorio / "snapshot_mercado.json").read_bytes()).hexdigest()
    for doc in colecao.docs.values():
        assert doc["sha256_snapshot_mercado"] == sha
        assert doc["status_promocao"] == "nao_decidida"
        assert doc["publicado_em"].endswith("Z")
    assert resumo["publicados"] == 6


def test_reexecucao_nao_duplica_e_preserva_data_de_publicacao(tmp_path):
    diretorio = _gravar_snapshot(tmp_path / "snap", ["sazonal", "mlp"])
    colecao = ColecaoFalsa()
    publicar_model_cards(diretorio, colecao)
    primeira = {k: v["publicado_em"] for k, v in colecao.docs.items()}

    publicar_model_cards(diretorio, colecao)

    assert len(colecao.docs) == 2
    assert {k: v["publicado_em"] for k, v in colecao.docs.items()} == primeira


def test_snapshot_adulterado_nao_publica_nada(tmp_path):
    diretorio = _gravar_snapshot(tmp_path / "snap", ["sazonal"], adulterar=True)
    colecao = ColecaoFalsa()

    with pytest.raises(ValueError, match="SHA-256"):
        publicar_model_cards(diretorio, colecao)
    assert colecao.docs == {}


def test_card_sem_id_ou_promovido_e_recusado(tmp_path):
    diretorio = tmp_path / "snap"
    diretorio.mkdir()
    card = _card("mlp")
    card["status_promocao"] = "promovido"
    bruto = json.dumps({"modelos": [{"id": "mlp", "model_card": card}]}).encode("utf-8")
    (diretorio / "snapshot_mercado.json").write_bytes(bruto)
    (diretorio / "manifesto.json").write_text(
        json.dumps({"sha256": hashlib.sha256(bruto).hexdigest()}), encoding="utf-8"
    )
    colecao = ColecaoFalsa()

    with pytest.raises(ValueError, match="promo"):
        publicar_model_cards(diretorio, colecao)
    assert colecao.docs == {}


@pytest.mark.skipif(
    not (os.environ.get("MONGODB_URI") and "teste" in os.environ.get("MONGODB_DB", "")),
    reason="Mongo de teste não configurado",
)
def test_publicacao_real_no_mongo_de_teste_e_idempotente(tmp_path):
    from pymongo import MongoClient

    diretorio = _gravar_snapshot(tmp_path / "snap", ["sazonal", "mlp"])
    cliente = MongoClient(os.environ["MONGODB_URI"], serverSelectionTimeoutMS=3000)
    colecao = cliente[os.environ["MONGODB_DB"]][f"model_cards_teste_{uuid.uuid4().hex[:8]}"]
    try:
        publicar_model_cards(diretorio, colecao)
        publicar_model_cards(diretorio, colecao)
        docs = list(colecao.find({}))
        assert sorted(d["_id"] for d in docs) == ["mlp:v_teste", "sazonal:v_teste"]
    finally:
        colecao.drop()
        cliente.close()
