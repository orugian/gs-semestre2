"""Aceite independente municipal, apenas fixtures e metadados de arquivos temporarios."""

import os

import pandas as pd
import pytest

from citizentech_ml.estatistica.base_municipal import (
    SEIS_DESTINOS_OFICIAIS,
    agregar_base_municipal,
    planejar_fontes_municipais,
)


def test_alias_hardlink_para_sentinela_2026_e_rejeitado_antes_de_io(tmp_path):
    sentinela = tmp_path / "CAGEDMOV202601.parquet"
    sentinela.write_bytes(b"fixture sintetica, nao e dado do holdout")
    alvo = tmp_path / "CAGEDMOV202401.parquet"
    for ano in (2024, 2025):
        for mes in range(1, 13):
            for tipo in ("MOV", "FOR", "EXC"):
                p = tmp_path / f"CAGED{tipo}{ano}{mes:02d}.parquet"
                if p != alvo:
                    p.write_bytes(b"fixture")
    os.link(sentinela, alvo)
    with pytest.raises(ValueError, match="[Aa]lias|[Ll]ink|[Dd]uplicad"):
        planejar_fontes_municipais(tmp_path)


def test_media_salarial_e_percentual_usam_contribuicoes_assinadas_e_snapshot():
    mapa = {
        "destinos": {
            nome: {"cbo6": [str(100001 + i)]}
            for i, nome in enumerate(sorted(SEIS_DESTINOS_OFICIAIS))
        }
    }
    cbo = next(iter(mapa["destinos"].values()))["cbo6"][0]

    def linha(ano, tipo="MOV", salario=1000.0, grau=9, arquivo=None):
        comp = f"{ano}01"
        arq = arquivo or comp
        return {
            "municipio": "355030",
            "uf": "35",
            "cbo2002_ocupacao": cbo,
            "saldo_movimentacao": 1,
            "grau_instrucao": grau,
            "salario": salario,
            "arquivo_tipo": tipo,
            "competencia_mov": comp,
            "competencia_dec": arq,
            "competencia_arquivo": arq,
            "competencia_exc": arq if tipo == "EXC" else None,
        }

    dados = [linha(2024) for _ in range(8)]
    dados += [linha(2024, salario=2000.0, grau=7) for _ in range(4)]
    dados += [linha(2024, tipo="EXC"), linha(2024, tipo="FOR", salario=float("nan"), grau=99)]
    # Esta retificacao posterior nao pode revisar o snapshot de2024.
    dados += [linha(2024, tipo="FOR", salario=9999.0, grau=80, arquivo="202501")]
    dados += [linha(2025, salario=100.0, grau=7)]
    base, _ = agregar_base_municipal(pd.DataFrame(dados), mapa)
    r = base.set_index("municipio").loc["355030"]
    assert r["admissoes_2024"] == 12
    assert r["n_salarios_validos_2024"] == 11
    assert r["n_salarios_invalidos_2024"] == 1
    assert r["salario_medio_2024"] == pytest.approx(15000 / 11)
    assert r["percentual_superior_2024"] == pytest.approx(100 * 7 / 12)
    assert r["escolaridade_desconhecida_2024"] == 1
    assert r["admissoes_2025"] == 1
    assert r["crescimento"] == 0


@pytest.mark.parametrize(
    "campo,valor", [("arquivo_tipo", "FOR"), ("competencia_arquivo", "202402")]
)
def test_metadados_internos_divergentes_do_nome_da_fonte_sao_recusados(tmp_path, campo, valor):
    from citizentech_ml.estatistica.base_municipal import carregar_base_municipal

    for ano in (2024, 2025):
        for mes in range(1, 13):
            for tipo in ("MOV", "FOR", "EXC"):
                (tmp_path / f"CAGED{tipo}{ano}{mes:02d}.parquet").write_bytes(b"fixture")
    mapa = {
        "destinos": {
            nome: {"cbo6": [str(100001 + i)]}
            for i, nome in enumerate(sorted(SEIS_DESTINOS_OFICIAIS))
        }
    }
    linha = {
        "municipio": "355030",
        "uf": "35",
        "cbo2002_ocupacao": "100001",
        "saldo_movimentacao": 1,
        "grau_instrucao": 9,
        "salario": 1000.0,
        "arquivo_tipo": "MOV",
        "competencia_mov": "202401",
        "competencia_dec": "202401",
        "competencia_arquivo": "202401",
        "competencia_exc": None,
    }
    linha[campo] = valor
    with pytest.raises(ValueError, match="[Ff]onte|[Dd]iverg|competencia_arquivo|arquivo_tipo"):
        carregar_base_municipal(tmp_path, mapa, leitor=lambda p: pd.DataFrame([linha]))
