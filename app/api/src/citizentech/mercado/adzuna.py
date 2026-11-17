"""Leitura da amostra pontual Adzuna (D05a) com verificação de SHA-256.

A amostra é opcional: se ausente, adulterada ou ilegível, o mercado continua respondendo e
a amostra aparece como indisponível (sem expor caminhos).
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from citizentech.banco.util import SAO_PAULO
from citizentech.mercado.esquemas import AmostraAdzuna, ItemAmostraAdzuna

_INDISPONIVEL = "Snapshot Adzuna não coletado nesta versão (D05a)."
_INVALIDO = "Snapshot Adzuna indisponível: falha na verificação de integridade."


def _carregar_resumo() -> tuple[dict | None, str]:
    caminho = os.environ.get("CITIZENTECH_ADZUNA_SNAPSHOT")
    if not caminho:
        return None, _INDISPONIVEL
    try:
        diretorio = Path(caminho)
        manifesto = json.loads((diretorio / "manifesto.json").read_text(encoding="utf-8"))
        bruto = (diretorio / "resumo_adzuna.json").read_bytes()
        if hashlib.sha256(bruto).hexdigest() != str(manifesto.get("sha256", "")).lower():
            return None, _INVALIDO
        resumo = json.loads(bruto.decode("utf-8"))
        if resumo.get("natureza") != "amostra_pontual":
            return None, _INVALIDO
        return resumo, ""
    except (OSError, ValueError):
        return None, _INVALIDO


def _data_local(iso_utc: str) -> str:
    instante = datetime.strptime(iso_utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    return instante.astimezone(SAO_PAULO).strftime("%d/%m/%Y")


def montar_amostra_adzuna(destino: str) -> AmostraAdzuna:
    resumo, motivo = _carregar_resumo()
    if resumo is None:
        return AmostraAdzuna(disponivel=False, natureza="amostra_pontual", motivo=motivo)
    itens = [
        ItemAmostraAdzuna(
            territorio=item["territorio"],
            termo_busca=item["termo_busca"],
            contagem_anuncios=item.get("contagem_anuncios")
            if item.get("status_http") == 200
            else None,
        )
        for item in resumo.get("itens", [])
        if item.get("destino") == destino
    ]
    coletado_em = resumo["coletado_em"]
    return AmostraAdzuna(
        disponivel=True,
        natureza="amostra_pontual",
        motivo=(
            f"Amostra pontual Adzuna de {_data_local(coletado_em)}: contagem de anúncios "
            "indexados no dia da coleta; não é série oficial, não entra no treino e não "
            "indica chance individual."
        ),
        fonte=resumo.get("fonte"),
        atribuicao=resumo.get("atribuicao"),
        unidade=resumo.get("unidade"),
        populacao=resumo.get("populacao"),
        coletado_em=coletado_em,
        itens=itens,
    )
