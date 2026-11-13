"""Testes da classificacao de risco e leitura de limiares na nuvem/Lambda (S1)."""

import ast
import json
import sys
from pathlib import Path

import pytest

import citizentech_cloud.risco
from citizentech_cloud.risco import (
    MetricaDesconhecida,
    ValorInvalido,
    carregar_limiares,
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


def test_carrega_limiares_do_caminho_da_variavel_de_ambiente(tmp_path, monkeypatch):
    arquivo_customizado = tmp_path / "limiares_teste.json"
    conteudo_esperado = {
        "schema_version": "1.0",
        "metricas": {
            "teste": {
                "atencao": 10.0,
                "critico": 20.0,
            }
        },
    }
    with open(arquivo_customizado, "w", encoding="utf-8") as f:
        json.dump(conteudo_esperado, f)

    monkeypatch.setenv("CITIZENTECH_LIMIARES", str(arquivo_customizado))
    resultado = carregar_limiares()
    assert resultado == conteudo_esperado


def test_modulo_usa_apenas_biblioteca_padrao():
    caminho_arquivo = Path(citizentech_cloud.risco.__file__).resolve()
    with open(caminho_arquivo, encoding="utf-8") as f:
        arvore = ast.parse(f.read(), filename=str(caminho_arquivo))

    modulos_importados = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            for alias in no.names:
                modulos_importados.add(alias.name.split(".")[0])
        elif isinstance(no, ast.ImportFrom):
            if no.module:
                modulos_importados.add(no.module.split(".")[0])

    stdlib = sys.stdlib_module_names | set(sys.builtin_module_names)
    for modulo in modulos_importados:
        assert modulo in stdlib, f"Modulo '{modulo}' nao pertence a biblioteca padrao"

def test_inteiro_gigante_e_valor_invalido():
    with pytest.raises(ValorInvalido):
        classificar_risco("temperatura_c", 10**400)
