"""A lista de ocupações aprovada pelo usuário é versionada e válida para a ingestão."""

import json
from pathlib import Path

from citizentech_ml.ingestao import carregar_ocupacoes

CAMINHO = Path(__file__).resolve().parents[2] / "catalogo" / "ocupacoes_cbo.json"


def test_catalogo_aprovado_carrega_com_seis_destinos_disjuntos():
    assert CAMINHO.is_file(), f"catálogo ausente: {CAMINHO}"

    ocupacoes = carregar_ocupacoes(CAMINHO)
    bruto = json.loads(CAMINHO.read_text(encoding="utf-8"))

    assert bruto["situacao"] == "aprovada"
    assert len(ocupacoes.destinos) == 6
    codigos_dos_destinos = [c for d in ocupacoes.destinos.values() for c in d["cbo6"]]
    assert len(codigos_dos_destinos) == len(set(codigos_dos_destinos))
    assert ocupacoes.codigos_ingestao == set(codigos_dos_destinos) | set(ocupacoes.cbo6_reserva)


def test_todo_codigo_do_catalogo_tem_titulo_e_fonte_do_titulo():
    assert CAMINHO.is_file(), f"catálogo ausente: {CAMINHO}"

    ocupacoes = carregar_ocupacoes(CAMINHO)
    titulos = json.loads(CAMINHO.read_text(encoding="utf-8"))["ocupacoes"]

    assert set(titulos) == ocupacoes.codigos_ingestao
    for codigo, dados in titulos.items():
        assert dados["titulo"].strip(), codigo
        assert dados["fonte_titulo"] in {"layout_novo_caged", "espelho_secundario"}, codigo