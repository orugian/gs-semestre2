"""Publicação idempotente dos model cards do snapshot de mercado no MongoDB (plano §3.4).

Fonte única: `snapshot_mercado.json` já verificado pelo SHA-256 do manifesto. Upsert por
`_id` (modelo:versão); `publicado_em` só é gravado na primeira publicação. Nenhum card
promovido é aceito enquanto o holdout estiver fechado (D10a).

Uso real (orquestrador): uv run python -m citizentech_ml.mercado.model_cards --snapshot <dir>
(lê MONGODB_URI e MONGODB_DB do ambiente; nunca imprime a URI).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

COLECAO_PADRAO = "model_cards"


def _carregar_cards(dir_snapshot: Path) -> tuple[list[dict[str, Any]], str]:
    manifesto = json.loads((dir_snapshot / "manifesto.json").read_text(encoding="utf-8"))
    bruto = (dir_snapshot / "snapshot_mercado.json").read_bytes()
    sha = hashlib.sha256(bruto).hexdigest()
    if str(manifesto.get("sha256", "")).lower() != sha:
        raise ValueError("SHA-256 do snapshot de mercado diverge do manifesto.")
    snapshot = json.loads(bruto.decode("utf-8"))
    cards = []
    for modelo in snapshot.get("modelos", []):
        card = modelo.get("model_card")
        if not isinstance(card, dict) or not card.get("_id"):
            raise ValueError(f"Model card ausente ou sem _id para {modelo.get('id')}.")
        if card.get("status_promocao") != "nao_decidida" or modelo.get("promovido"):
            raise ValueError(f"Card {card['_id']} indica promoção; holdout fechado (D10a).")
        cards.append(card)
    if not cards:
        raise ValueError("Snapshot sem model cards.")
    return cards, sha


def publicar_model_cards(dir_snapshot: str | Path, colecao: Any) -> dict[str, Any]:
    """Valida todos os cards antes de gravar qualquer um; depois faz upsert idempotente."""
    cards, sha = _carregar_cards(Path(dir_snapshot))
    agora = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    for card in cards:
        campos = {k: v for k, v in card.items() if k != "_id"}
        campos["sha256_snapshot_mercado"] = sha
        colecao.update_one(
            {"_id": card["_id"]},
            {"$set": campos, "$setOnInsert": {"publicado_em": agora}},
            upsert=True,
        )
    return {"publicados": len(cards), "ids": [c["_id"] for c in cards], "sha256_snapshot": sha}


def main(argv: list[str] | None = None) -> int:
    analisador = argparse.ArgumentParser(description="Publica model cards no MongoDB.")
    analisador.add_argument("--snapshot", type=Path, required=True)
    analisador.add_argument("--colecao", default=COLECAO_PADRAO)
    opcoes = analisador.parse_args(argv)
    uri, banco = os.environ.get("MONGODB_URI"), os.environ.get("MONGODB_DB")
    if not uri or not banco:
        print("ERRO: MONGODB_URI/MONGODB_DB ausentes.")
        return 2
    from pymongo import MongoClient

    cliente = MongoClient(uri, serverSelectionTimeoutMS=8000)
    try:
        colecao = cliente[banco][opcoes.colecao]
        resumo = publicar_model_cards(opcoes.snapshot, colecao)
        total = colecao.count_documents({"sha256_snapshot_mercado": resumo["sha256_snapshot"]})
    finally:
        cliente.close()
    print(f"publicados={resumo['publicados']} na colecao={opcoes.colecao} documentos={total}")
    print("ids=" + ",".join(resumo["ids"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
