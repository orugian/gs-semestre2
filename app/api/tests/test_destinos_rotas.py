"""Testes da rota pública de catálogo de destinos (/destinos)."""

import json
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from citizentech.main import app

CHAVES_PROIBIDAS_CATALOGO = {
    "exercicio",
    "politica_avaliacao_proposta",
    "checklist_revisao",
    "gabarito",
    "resposta_esperada",
    "rubrica",
}

TERMOS_PROIBIDOS_TEXTO = [
    "vaga",
    "probabilidade de",
    "vale a pena",
]


def _verificar_ausencia_chaves(obj: Any) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            k_lower = k.lower()
            for proibida in CHAVES_PROIBIDAS_CATALOGO:
                assert proibida not in k_lower, f"Chave proibida encontrada: {k}"
            _verificar_ausencia_chaves(v)
    elif isinstance(obj, list):
        for item in obj:
            _verificar_ausencia_chaves(item)


def _verificar_ausencia_termos_texto(obj: Any) -> None:
    if isinstance(obj, dict):
        for v in obj.values():
            _verificar_ausencia_termos_texto(v)
    elif isinstance(obj, list):
        for item in obj:
            _verificar_ausencia_termos_texto(item)
    elif isinstance(obj, str):
        texto_lower = obj.lower()
        for termo in TERMOS_PROIBIDOS_TEXTO:
            assert termo not in texto_lower, f"Termo proibido '{termo}' encontrado no texto: {obj}"


def test_get_destinos_sucesso_whitelist_e_ordem():
    cliente = TestClient(app, base_url="https://testserver")
    resp = cliente.get("/destinos")
    assert resp.status_code == 200
    dados = resp.json()

    assert "itens" in dados
    itens = dados["itens"]
    assert len(itens) == 3

    # Ordem de escopo_mvp.json
    ids = [d["destino_id"] for d in itens]
    assert ids == [
        "analista_dados_bi",
        "analista_monitoramento_iot",
        "analista_processos",
    ]

    for d in itens:
        # Whitelist exata de chaves no destino
        assert set(d.keys()) == {"destino_id", "nome", "descricao", "requisitos"}
        assert isinstance(d["destino_id"], str)
        assert isinstance(d["nome"], str)
        assert d["descricao"] is None or isinstance(d["descricao"], str)
        assert isinstance(d["requisitos"], list)
        assert len(d["requisitos"]) > 0

        for req in d["requisitos"]:
            # Whitelist exata de chaves no requisito
            assert set(req.keys()) == {"id_local", "esco_id", "titulo", "obrigatorio"}
            assert isinstance(req["id_local"], str)
            assert isinstance(req["esco_id"], str)
            assert isinstance(req["titulo"], str)
            assert isinstance(req["obrigatorio"], bool)

    # Varredura recursiva de chaves proibidas
    _verificar_ausencia_chaves(dados)
    # Varredura recursiva de strings proibidas
    _verificar_ausencia_termos_texto(dados)


def test_get_destinos_ignora_destino_nao_aprovado(tmp_path: Path, monkeypatch):
    cat_dir = tmp_path / "catalogo"
    destinos_dir = cat_dir / "destinos"
    destinos_dir.mkdir(parents=True)

    escopo = {
        "versao": "1.0.0",
        "decisao": "R29",
        "destinos": ["dest_aprovado", "dest_pendente"],
    }
    (cat_dir / "escopo_mvp.json").write_text(json.dumps(escopo), encoding="utf-8")

    yaml_aprovado = """
schema_version: "1.0"
destino_id: "dest_aprovado"
nome: "Destino Aprovado"
revisao_humana:
  status: "aprovado"
populacao:
  descricao: "Descricao aprovada."
requisitos:
  - id_local: "req_1"
    esco_id: "esco-1"
    titulo_oficial: "Titulo 1"
    obrigatorio_proposto: true
"""
    yaml_pendente = """
schema_version: "1.0"
destino_id: "dest_pendente"
nome: "Destino Pendente"
revisao_humana:
  status: "pendente"
populacao:
  descricao: "Descricao pendente."
requisitos:
  - id_local: "req_2"
    esco_id: "esco-2"
    titulo_oficial: "Titulo 2"
    obrigatorio_proposto: false
"""
    (destinos_dir / "dest_aprovado.yaml").write_text(yaml_aprovado, encoding="utf-8")
    (destinos_dir / "dest_pendente.yaml").write_text(yaml_pendente, encoding="utf-8")

    monkeypatch.setenv("CITIZENTECH_CATALOGO", str(cat_dir))

    cliente = TestClient(app, base_url="https://testserver")
    resp = cliente.get("/destinos")
    assert resp.status_code == 200
    dados = resp.json()

    ids = [d["destino_id"] for d in dados["itens"]]
    assert ids == ["dest_aprovado"]
    assert "dest_pendente" not in ids
