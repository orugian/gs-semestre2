"""Testes do domínio puro de comparação de destinos (S11)."""

import copy
import json
from typing import Any

import pytest

from citizentech.comparacao.dominio import (
    classificar_requisitos,
    comparar_destinos,
)

CHAVES_PROIBIDAS = {
    "score",
    "nota",
    "ranking",
    "pontuacao",
    "percentual_aderencia",
    "aderencia",
}

TEXTOS_PROIBIDOS = [
    "vaga",
    "vagas",
    "probabilidade de emprego",
    "probabilidade de contratacao",
    "probabilidade de contratação",
    "probabilidade de",
    "vale a pena",
]


def _verificar_chaves_proibidas(objeto: Any) -> None:
    if isinstance(objeto, dict):
        for k, v in objeto.items():
            k_lower = str(k).lower()
            for proibida in CHAVES_PROIBIDAS:
                assert proibida not in k_lower, f"Chave proibida encontrada: {k}"
            _verificar_chaves_proibidas(v)
    elif isinstance(objeto, list):
        for item in objeto:
            _verificar_chaves_proibidas(item)


def _verificar_textos_proibidos(objeto: Any) -> None:
    if isinstance(objeto, str):
        texto_lower = objeto.lower()
        for proibido in TEXTOS_PROIBIDOS:
            assert (
                proibido not in texto_lower
            ), f"Texto proibido encontrado: '{proibido}' em '{objeto}'"
    elif isinstance(objeto, dict):
        for k, v in objeto.items():
            _verificar_textos_proibidos(k)
            _verificar_textos_proibidos(v)
    elif isinstance(objeto, list):
        for item in objeto:
            _verificar_textos_proibidos(item)


def test_obrigatorio_nao_atendido_nunca_some() -> None:
    """Destino com 5 requisitos, 4 demonstrados e 1 obrigatório sem informação:

    deve listar o obrigatório em obrigatorios_nao_atendidos com estado desconhecida,
    situacao_obrigatorios == 'ha_obrigatorios_nao_demonstrados' e nenhuma chave proibida.
    """
    requisitos = [
        {
            "id_local": "req-1",
            "esco_id": "esco-1",
            "titulo_oficial": "Req 1",
            "obrigatorio_proposto": True,
        },
        {
            "id_local": "req-2",
            "esco_id": "esco-2",
            "titulo_oficial": "Req 2",
            "obrigatorio_proposto": True,
        },
        {
            "id_local": "req-3",
            "esco_id": "esco-3",
            "titulo_oficial": "Req 3",
            "obrigatorio_proposto": False,
        },
        {
            "id_local": "req-4",
            "esco_id": "esco-4",
            "titulo_oficial": "Req 4",
            "obrigatorio_proposto": False,
        },
        {
            "id_local": "req-5",
            "esco_id": "esco-5",
            "titulo_oficial": "Req 5",
            "obrigatorio_proposto": True,
        },
    ]

    destinos = [
        {
            "destino_id": "dest-1",
            "nome": "Desenvolvedor Backend",
            "status_revisao": "aprovado",
            "requisitos": requisitos,
        }
    ]

    # 4 demonstrados por exercício: esco-1, esco-2, esco-3, esco-4.
    # esco-5 é obrigatório e não tem informação.
    resultados_exercicio = [
        {"esco_ids_avaliados": ["esco-1"], "resultado": "demonstrada"},
        {"esco_ids_avaliados": ["esco-2"], "resultado": "demonstrada"},
        {"esco_ids_avaliados": ["esco-3"], "resultado": "demonstrada"},
        {"esco_ids_avaliados": ["esco-4"], "resultado": "demonstrada"},
    ]
    competencias: list[dict[str, Any]] = []

    res = comparar_destinos(destinos, competencias, resultados_exercicio)

    assert "destinos" in res
    assert len(res["destinos"]) == 1
    d0 = res["destinos"][0]
    assert d0["destino_id"] == "dest-1"
    assert d0["situacao_obrigatorios"] == "ha_obrigatorios_nao_demonstrados"

    nao_atendidos = d0["dimensoes"]["obrigatorios_nao_atendidos"]
    assert len(nao_atendidos) == 1
    assert nao_atendidos[0]["id_local"] == "req-5"
    assert nao_atendidos[0]["titulo"] == "Req 5"
    assert nao_atendidos[0]["estado"] == "desconhecida"

    _verificar_chaves_proibidas(res)
    _verificar_textos_proibidos(res)


def test_nao_declarado_e_desconhecida_nao_lacuna() -> None:
    """T07: usuário não declarou uma habilidade -> estado desconhecida, nunca lacuna."""
    requisitos = [
        {
            "id_local": "req-1",
            "esco_id": "esco-x",
            "titulo_oficial": "Python",
            "obrigatorio_proposto": True,
        }
    ]
    competencias: list[dict[str, Any]] = []
    resultados_exercicio: list[dict[str, Any]] = []

    itens = classificar_requisitos(requisitos, competencias, resultados_exercicio)
    assert len(itens) == 1
    item = itens[0]
    assert item["estado"] == "desconhecida"
    assert item["motivo"] == "sem_informacao_suficiente"
    assert item["estado"] != "lacuna"


def test_regras_precedencia_1_a_5_e_casos_particulares() -> None:
    """Valida as regras de precedência determinísticas de 1 a 5."""
    requisitos = [
        {
            "id_local": "r1",
            "esco_id": "esco-demo",
            "titulo_oficial": "Habilidade 1",
            "obrigatorio_proposto": True,
        },
        {
            "id_local": "r2",
            "esco_id": "esco-insuf",
            "titulo_oficial": "Habilidade 2",
            "obrigatorio_proposto": True,
        },
        {
            "id_local": "r3",
            "esco_id": "esco-nao-possuo",
            "titulo_oficial": "Habilidade 3",
            "obrigatorio_proposto": False,
        },
        {
            "id_local": "r4",
            "esco_id": "esco-decl",
            "titulo_oficial": "Habilidade 4",
            "obrigatorio_proposto": False,
        },
        {
            "id_local": "r5",
            "esco_id": "esco-rej",
            "titulo_oficial": "Habilidade 5",
            "obrigatorio_proposto": False,
        },
        {
            "id_local": "r6",
            "esco_id": "esco-vazio",
            "titulo_oficial": "Habilidade 6",
            "obrigatorio_proposto": False,
        },
        {
            "id_local": "r7",
            "esco_id": "esco-parcial",
            "titulo_oficial": "Habilidade 7",
            "obrigatorio_proposto": False,
        },
    ]

    competencias = [
        {"esco_id": "esco-nao-possuo", "estado": "nao_possuo"},
        {
            "esco_id": "esco-decl",
            "estado": "declarada",
            "origem": "curriculo_pdf",
            "trecho_origem": "Experiência de 3 anos",
        },
        {"esco_id": "esco-rej", "estado": "rejeitada"},
    ]

    resultados_exercicio = [
        {"esco_ids_avaliados": ["esco-demo"], "resultado": "demonstrada"},
        {"esco_ids_avaliados": ["esco-insuf"], "resultado": "insuficiente"},
        {"esco_ids_avaliados": ["esco-parcial"], "resultado": "parcial"},
    ]

    itens = classificar_requisitos(requisitos, competencias, resultados_exercicio)
    itens_map = {it["esco_id"]: it for it in itens}

    # 1. demonstrada
    assert itens_map["esco-demo"]["estado"] == "demonstrada"
    assert itens_map["esco-demo"]["motivo"] is None

    # 2. insuficiente -> lacuna (exercicio_abaixo_do_minimo)
    assert itens_map["esco-insuf"]["estado"] == "lacuna"
    assert itens_map["esco-insuf"]["motivo"] == "exercicio_abaixo_do_minimo"

    # 3. nao_possuo -> lacuna (ausencia_informada_pelo_usuario)
    assert itens_map["esco-nao-possuo"]["estado"] == "lacuna"
    assert itens_map["esco-nao-possuo"]["motivo"] == "ausencia_informada_pelo_usuario"

    # 4. declarada -> declarada (com repasse de origem e trecho_origem)
    assert itens_map["esco-decl"]["estado"] == "declarada"
    assert itens_map["esco-decl"]["origem"] == "curriculo_pdf"
    assert itens_map["esco-decl"]["trecho_origem"] == "Experiência de 3 anos"
    assert itens_map["esco-decl"]["motivo"] is None

    # 5a. rejeitada -> desconhecida (sem_informacao_suficiente)
    assert itens_map["esco-rej"]["estado"] == "desconhecida"
    assert itens_map["esco-rej"]["motivo"] == "sem_informacao_suficiente"

    # 5b. total ausência -> desconhecida (sem_informacao_suficiente)
    assert itens_map["esco-vazio"]["estado"] == "desconhecida"
    assert itens_map["esco-vazio"]["motivo"] == "sem_informacao_suficiente"

    # 5c. exercício parcial -> desconhecida (avaliacao_parcial_llm_indisponivel)
    assert itens_map["esco-parcial"]["estado"] == "desconhecida"
    assert itens_map["esco-parcial"]["motivo"] == "avaliacao_parcial_llm_indisponivel"


def test_conflito_declarada_e_nao_possuo_lacuna_com_aviso() -> None:
    """Conflito declarada + nao_possuo -> lacuna com aviso 'entrada_conflitante'."""
    requisitos = [
        {
            "id_local": "r-conf",
            "esco_id": "esco-conf",
            "titulo_oficial": "SQL",
            "obrigatorio_proposto": True,
        }
    ]
    competencias = [
        {"esco_id": "esco-conf", "estado": "declarada", "origem": "auto"},
        {"esco_id": "esco-conf", "estado": "nao_possuo"},
    ]
    resultados_exercicio: list[dict[str, Any]] = []

    itens = classificar_requisitos(requisitos, competencias, resultados_exercicio)
    assert len(itens) == 1
    it = itens[0]
    assert it["estado"] == "lacuna"
    assert it["motivo"] == "ausencia_informada_pelo_usuario"
    assert "entrada_conflitante" in it["avisos"]


def test_conflitos_adicionais_exercicio_e_declaracao() -> None:
    """Verifica precedência e avisos quando há contradições entre exercício e declaração."""
    requisitos = [
        {"id_local": "r1", "esco_id": "esco-1", "titulo_oficial": "Git"},
        {"id_local": "r2", "esco_id": "esco-2", "titulo_oficial": "Docker"},
        {"id_local": "r3", "esco_id": "esco-3", "titulo_oficial": "Linux"},
    ]

    competencias = [
        {"esco_id": "esco-1", "estado": "nao_possuo"},
        {"esco_id": "esco-2", "estado": "declarada", "origem": "curriculo"},
        {"esco_id": "esco-3", "estado": "declarada", "origem": "curriculo"},
    ]
    resultados = [
        {"esco_ids_avaliados": ["esco-1"], "resultado": "demonstrada"},
        {"esco_ids_avaliados": ["esco-2"], "resultado": "insuficiente"},
        {"esco_ids_avaliados": ["esco-3"], "resultado": "demonstrada"},
    ]

    itens = classificar_requisitos(requisitos, competencias, resultados)
    imap = {it["esco_id"]: it for it in itens}

    assert imap["esco-1"]["estado"] == "demonstrada"
    assert "entrada_conflitante" in imap["esco-1"]["avisos"]

    assert imap["esco-2"]["estado"] == "lacuna"
    assert imap["esco-2"]["motivo"] == "exercicio_abaixo_do_minimo"
    assert "entrada_conflitante" in imap["esco-2"]["avisos"]

    assert imap["esco-3"]["estado"] == "demonstrada"
    assert imap["esco-3"]["avisos"] == []


def test_estado_invalido_dispara_value_error() -> None:
    """Estado desconhecido na entrada de competências ou resultados dispara ValueError."""
    requisitos = [{"id_local": "r1", "esco_id": "esco-1", "titulo_oficial": "T"}]

    with pytest.raises(ValueError, match="Estado de competência inválido"):
        classificar_requisitos(requisitos, [{"esco_id": "esco-1", "estado": "inventado"}], [])

    with pytest.raises(ValueError, match="Resultado de exercício inválido"):
        classificar_requisitos(
            requisitos,
            [],
            [{"esco_ids_avaliados": ["esco-1"], "resultado": "magico"}],
        )


def test_validacao_destinos_quantidade_duplicados_e_status() -> None:
    """Validações de 0, > 3 destinos, duplicados e status_revisao != 'aprovado'."""
    req = [{"id_local": "r1", "esco_id": "e1", "titulo_oficial": "T"}]
    d_valido = {
        "destino_id": "d1",
        "nome": "D1",
        "status_revisao": "aprovado",
        "requisitos": req,
    }

    # 0 destinos
    with pytest.raises(ValueError, match="Quantidade de destinos inválida"):
        comparar_destinos([], [])

    # 4 destinos
    d2 = {"destino_id": "d2", "nome": "D2", "status_revisao": "aprovado", "requisitos": req}
    d3 = {"destino_id": "d3", "nome": "D3", "status_revisao": "aprovado", "requisitos": req}
    d4 = {"destino_id": "d4", "nome": "D4", "status_revisao": "aprovado", "requisitos": req}
    with pytest.raises(ValueError, match="Quantidade de destinos inválida"):
        comparar_destinos([d_valido, d2, d3, d4], [])

    # Destinos repetidos
    d_rep = {
        "destino_id": "d1",
        "nome": "D1 repetido",
        "status_revisao": "aprovado",
        "requisitos": req,
    }
    with pytest.raises(ValueError, match="Destinos repetidos"):
        comparar_destinos([d_valido, d_rep], [])

    # Status não aprovado
    d_pendente = {
        "destino_id": "dp",
        "nome": "DP",
        "status_revisao": "pendente",
        "requisitos": req,
    }
    with pytest.raises(ValueError, match="status de revisão"):
        comparar_destinos([d_pendente], [])

    # Status em revisao_humana não aprovado
    d_rev_pendente = {
        "destino_id": "drp",
        "nome": "DRP",
        "revisao_humana": {"status": "rejeitado"},
        "requisitos": req,
    }
    with pytest.raises(ValueError, match="status de revisão"):
        comparar_destinos([d_rev_pendente], [])

    # Status em revisao_humana aprovado funciona
    d_rev_ok = {
        "destino_id": "dro",
        "nome": "DRO",
        "revisao_humana": {"status": "aprovado"},
        "requisitos": req,
    }
    res = comparar_destinos([d_rev_ok], [])
    assert len(res["destinos"]) == 1


def test_ordem_destinos_preservada_e_independencia() -> None:
    """A ordem dos destinos na saída é exatamente a mesma da entrada e competências não vazam."""
    d3 = {
        "destino_id": "dest-3",
        "nome": "Terceiro",
        "status_revisao": "aprovado",
        "requisitos": [{"id_local": "r3", "esco_id": "esco-3", "titulo_oficial": "Skill 3"}],
    }
    d1 = {
        "destino_id": "dest-1",
        "nome": "Primeiro",
        "status_revisao": "aprovado",
        "requisitos": [{"id_local": "r1", "esco_id": "esco-1", "titulo_oficial": "Skill 1"}],
    }
    d2 = {
        "destino_id": "dest-2",
        "nome": "Segundo",
        "status_revisao": "aprovado",
        "requisitos": [{"id_local": "r2", "esco_id": "esco-2", "titulo_oficial": "Skill 2"}],
    }

    competencias = [{"esco_id": "esco-3", "estado": "declarada", "origem": "auto"}]
    exercicios = [{"esco_ids_avaliados": ["esco-1"], "resultado": "demonstrada"}]

    res = comparar_destinos([d3, d1, d2], competencias, exercicios)

    # Ordem preservada
    ordem_saida = [d["destino_id"] for d in res["destinos"]]
    assert ordem_saida == ["dest-3", "dest-1", "dest-2"]

    # Independência dos destinos
    d3_itens = res["destinos"][0]["dimensoes"]["requisitos"]["itens"]
    assert d3_itens[0]["estado"] == "declarada"

    d1_itens = res["destinos"][1]["dimensoes"]["requisitos"]["itens"]
    assert d1_itens[0]["estado"] == "demonstrada"

    d2_itens = res["destinos"][2]["dimensoes"]["requisitos"]["itens"]
    assert d2_itens[0]["estado"] == "desconhecida"


def test_competencia_fora_do_catalogo_e_ignorada() -> None:
    """esco_id do usuário que não pertence ao destino é ignorado e não cria requisito."""
    destinos = [
        {
            "destino_id": "d1",
            "nome": "D1",
            "status_revisao": "aprovado",
            "requisitos": [{"id_local": "r1", "esco_id": "esco-alvo", "titulo_oficial": "Alvo"}],
        }
    ]
    competencias = [
        {"esco_id": "esco-alien-1", "estado": "declarada", "origem": "cv"},
        {"esco_id": "esco-alien-2", "estado": "nao_possuo"},
    ]
    exercicios = [{"esco_ids_avaliados": ["esco-alien-3"], "resultado": "demonstrada"}]

    res = comparar_destinos(destinos, competencias, exercicios)
    itens = res["destinos"][0]["dimensoes"]["requisitos"]["itens"]
    assert len(itens) == 1
    assert itens[0]["esco_id"] == "esco-alvo"
    assert itens[0]["estado"] == "desconhecida"


@pytest.mark.parametrize(
    ("n_demo", "n_decl", "n_lac", "n_desc"),
    [
        (0, 0, 0, 5),
        (2, 1, 1, 1),
        (5, 0, 0, 0),
        (0, 3, 2, 0),
        (1, 1, 1, 1),
    ],
)
def test_propriedades_contagens_e_aproveitamento(
    n_demo: int,
    n_decl: int,
    n_lac: int,
    n_desc: int,
) -> None:
    """Propriedade: a soma das contagens é estritamente igual ao número de requisitos."""
    requisitos: list[dict[str, Any]] = []
    competencias: list[dict[str, Any]] = []
    exercicios: list[dict[str, Any]] = []

    idx = 0
    for _ in range(n_demo):
        idx += 1
        eid = f"esco-{idx}"
        requisitos.append(
            {"id_local": f"req-{idx}", "esco_id": eid, "titulo": f"T{idx}", "obrigatorio": True}
        )
        exercicios.append({"esco_ids_avaliados": [eid], "resultado": "demonstrada"})

    for _ in range(n_decl):
        idx += 1
        eid = f"esco-{idx}"
        requisitos.append(
            {"id_local": f"req-{idx}", "esco_id": eid, "titulo": f"T{idx}", "obrigatorio": False}
        )
        competencias.append({"esco_id": eid, "estado": "declarada", "origem": "cv"})

    for _ in range(n_lac):
        idx += 1
        eid = f"esco-{idx}"
        requisitos.append(
            {"id_local": f"req-{idx}", "esco_id": eid, "titulo": f"T{idx}", "obrigatorio": True}
        )
        competencias.append({"esco_id": eid, "estado": "nao_possuo"})

    for _ in range(n_desc):
        idx += 1
        eid = f"esco-{idx}"
        requisitos.append(
            {"id_local": f"req-{idx}", "esco_id": eid, "titulo": f"T{idx}", "obrigatorio": False}
        )

    destinos = [
        {
            "destino_id": "d-prop",
            "nome": "Prop",
            "status_revisao": "aprovado",
            "requisitos": requisitos,
        }
    ]

    res = comparar_destinos(destinos, competencias, exercicios)
    d0 = res["destinos"][0]
    dim = d0["dimensoes"]
    cont = dim["requisitos"]["contagem"]

    assert cont["demonstrada"] == n_demo
    assert cont["declarada"] == n_decl
    assert cont["lacuna"] == n_lac
    assert cont["desconhecida"] == n_desc
    assert sum(cont.values()) == len(requisitos)

    assert len(dim["aproveitamento_experiencia"]["demonstrados"]) == n_demo
    assert len(dim["aproveitamento_experiencia"]["declarados"]) == n_decl


def test_mercado_repassado_ou_indisponivel() -> None:
    """Mercado é apenas repassado sem cálculo; ausente vira disponível: False, indisponível."""
    d1 = {"destino_id": "d1", "nome": "D1", "status_revisao": "aprovado", "requisitos": []}
    d2 = {"destino_id": "d2", "nome": "D2", "status_revisao": "aprovado", "requisitos": []}

    mercado_input = {
        "d1": {
            "disponivel": True,
            "natureza": "estavel",
            "resumo": "Panorama setorial com crescimento moderado",
            "referencia_temporal": "2026-T3",
        }
    }

    # Passando mercado onde d1 está presente e d2 está ausente
    res = comparar_destinos([d1, d2], [], mercado=mercado_input)
    assert res["destinos"][0]["dimensoes"]["mercado"] == mercado_input["d1"]
    assert res["destinos"][1]["dimensoes"]["mercado"] == {
        "disponivel": False,
        "natureza": "indisponivel",
    }

    # Passando mercado=None
    res_none = comparar_destinos([d1], [], mercado=None)
    assert res_none["destinos"][0]["dimensoes"]["mercado"] == {
        "disponivel": False,
        "natureza": "indisponivel",
    }


def test_preferencias_conflito_horas_semana() -> None:
    """Preferências: horas_semana < 4 gera conflito; sem preferências gera listas vazias."""
    d = {"destino_id": "d1", "nome": "D1", "status_revisao": "aprovado", "requisitos": []}

    # Sem preferências
    res_sem = comparar_destinos([d], [], preferencias=None)
    assert res_sem["destinos"][0]["dimensoes"]["preferencias"]["conflitos"] == []
    assert res_sem["destinos"][0]["dimensoes"]["preferencias"]["observacoes"] == []

    # Horas < 4
    res_baixa = comparar_destinos([d], [], preferencias={"horas_semana": 2, "uf": "SP"})
    conflitos = res_baixa["destinos"][0]["dimensoes"]["preferencias"]["conflitos"]
    assert len(conflitos) == 1
    assert "Disponibilidade semanal abaixo de 4 h" in conflitos[0]

    # Horas >= 4
    res_ok = comparar_destinos([d], [], preferencias={"horas_semana": 10, "uf": "SP"})
    assert res_ok["destinos"][0]["dimensoes"]["preferencias"]["conflitos"] == []


def test_situacao_obrigatorios_todos_demonstrados() -> None:
    """Quando todos os obrigatórios forem demonstrados: 'todos_demonstrados'."""
    requisitos = [
        {
            "id_local": "r1",
            "esco_id": "e1",
            "titulo_oficial": "Req 1",
            "obrigatorio_proposto": True,
        },
        {
            "id_local": "r2",
            "esco_id": "e2",
            "titulo_oficial": "Req 2",
            "obrigatorio_proposto": False,
        },
    ]
    exercicios = [
        {"esco_ids_avaliados": ["e1"], "resultado": "demonstrada"},
    ]
    destinos = [
        {"destino_id": "d1", "nome": "D1", "status_revisao": "aprovado", "requisitos": requisitos}
    ]

    res = comparar_destinos(destinos, [], exercicios)
    d0 = res["destinos"][0]
    assert d0["situacao_obrigatorios"] == "todos_demonstrados"
    assert d0["dimensoes"]["obrigatorios_nao_atendidos"] == []


def test_mutacao_entradas_preservacao_imutabilidade() -> None:
    """Garante que classificar_requisitos e comparar_destinos não alteram os objetos de entrada."""
    requisitos = [
        {"id_local": "r1", "esco_id": "e1", "titulo_oficial": "Req 1", "obrigatorio_proposto": True}
    ]
    competencias = [
        {"esco_id": "e1", "estado": "declarada", "origem": "teste"}
    ]
    exercicios = [
        {"esco_ids_avaliados": ["e1"], "resultado": "demonstrada"}
    ]
    destinos = [
        {"destino_id": "d1", "nome": "D1", "status_revisao": "aprovado", "requisitos": requisitos}
    ]
    preferencias = {"horas_semana": 3, "uf": "RJ"}
    mercado = {"d1": {"disponivel": True, "natureza": "estavel"}}

    destinos_clone = copy.deepcopy(destinos)
    competencias_clone = copy.deepcopy(competencias)
    exercicios_clone = copy.deepcopy(exercicios)
    preferencias_clone = copy.deepcopy(preferencias)
    mercado_clone = copy.deepcopy(mercado)

    classificar_requisitos(requisitos, competencias, exercicios)
    assert requisitos == destinos_clone[0]["requisitos"]
    assert competencias == competencias_clone
    assert exercicios == exercicios_clone

    comparar_destinos(destinos, competencias, exercicios, preferencias, mercado)
    assert destinos == destinos_clone
    assert competencias == competencias_clone
    assert exercicios == exercicios_clone
    assert preferencias == preferencias_clone
    assert mercado == mercado_clone


def test_saida_serializavel_json_e_sem_termos_proibidos() -> None:
    """Saída completa deve ser 100% serializável por json.dumps e respeitar restrições léxicas."""
    requisitos = [
        {
            "id_local": "r1",
            "esco_id": "e1",
            "titulo_oficial": "Python",
            "obrigatorio_proposto": True,
        },
        {
            "id_local": "r2",
            "esco_id": "e2",
            "titulo_oficial": "Java",
            "obrigatorio_proposto": False,
        },
    ]
    destinos = [
        {
            "destino_id": "d1",
            "nome": "Backend",
            "status_revisao": "aprovado",
            "requisitos": requisitos,
        }
    ]
    competencias = [{"esco_id": "e2", "estado": "declarada", "origem": "cv"}]
    exercicios = [{"esco_ids_avaliados": ["e1"], "resultado": "demonstrada"}]
    preferencias = {"horas_semana": 2, "uf": "SP"}
    mercado = {
        "d1": {
            "disponivel": True,
            "natureza": "expansao",
            "resumo": "Em alta",
            "referencia_temporal": "2026",
        }
    }

    res = comparar_destinos(destinos, competencias, exercicios, preferencias, mercado)

    # Serialização JSON sem erro
    serializado = json.dumps(res, ensure_ascii=False)
    assert isinstance(serializado, str)

    # Varredura léxica recursiva
    _verificar_chaves_proibidas(res)
    _verificar_textos_proibidos(res)

    # Validação do aviso padrão
    assert (
        res["aviso"]
        == "Sem nota única: cada dimensão é apresentada separadamente e a decisão é sua."
    )
