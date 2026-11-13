"""Testes da classificacao de risco e leitura de limiares na API (S1)."""

import json
from pathlib import Path

import pytest

from citizentech.limiares import (
    MetricaDesconhecida,
    ValorInvalido,
    classificar_risco,
)

_CAMINHO_CASOS = Path(__file__).resolve().parents[2] / "config" / "casos_limiares.json"

with open(_CAMINHO_CASOS, encoding="utf-8") as _f:
    _DADOS_CASOS = json.load(_f)

_CASOS_VALIDOS = _DADOS_CASOS["casos_validos"]
_CASOS_INVALIDOS = _DADOS_CASOS["casos_invalidos"]

_MAPA_ERROS = {
    "metrica_desconhecida": MetricaDesconhecida,
    "valor_invalido": ValorInvalido,
}


def _converter_valor(valor_bruto):
    if isinstance(valor_bruto, dict) and "especial" in valor_bruto:
        return float(valor_bruto["especial"])
    return valor_bruto


@pytest.mark.parametrize(
    ("metrica", "valor", "classe_esperada"),
    [
        (caso["metrica"], caso["valor"], caso["classe"])
        for caso in _CASOS_VALIDOS
    ],
)
def test_casos_validos_da_tabela_compartilhada(metrica, valor, classe_esperada):
    assert classificar_risco(metrica, valor) == classe_esperada


@pytest.mark.parametrize(
    ("metrica", "valor_bruto", "tipo_erro"),
    [
        (caso["metrica"], caso["valor"], caso["erro"])
        for caso in _CASOS_INVALIDOS
    ],
)
def test_casos_invalidos_da_tabela_compartilhada(metrica, valor_bruto, tipo_erro):
    valor = _converter_valor(valor_bruto)
    excecao_esperada = _MAPA_ERROS[tipo_erro]
    with pytest.raises(excecao_esperada):
        classificar_risco(metrica, valor)


def test_limiares_alterados_mudam_a_classificacao():
    limiares_customizados = {
        "metricas": {
            "temperatura_c": {
                "unidade": "C",
                "direcao": "maior_pior",
                "atencao": 30.0,
                "critico": 45.0,
            }
        }
    }
    # Com atencao alterada para 30.0, o valor 32 vira atencao (no original seria normal)
    assert classificar_risco("temperatura_c", 32.0, limiares=limiares_customizados) == "atencao"


def test_metrica_desconhecida_cita_as_metricas_conhecidas():
    with pytest.raises(MetricaDesconhecida) as excinfo:
        classificar_risco("pressao_hpa", 1013.25)
    mensagem = str(excinfo.value)
    assert "pressao_hpa" in mensagem
    assert "temperatura_c" in mensagem

def test_inteiro_gigante_e_valor_invalido():
    with pytest.raises(ValorInvalido):
        classificar_risco("temperatura_c", 10**400)
