"""Testes unitários puros do domínio de geração de plano (TDD)."""

from typing import Any

from citizentech.plano.dominio import gerar_plano

CHAVES_PROIBIDAS = {"horas", "semanas", "prazo", "duracao", "score", "nota"}
TERMOS_PROIBIDOS = ["vaga", "probabilidade", "vale a pena", "nota", "score", "ranking"]


def _verificar_ausencia_chaves_proibidas(obj: Any) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert k.lower() not in CHAVES_PROIBIDAS, f"Chave proibida encontrada: {k}"
            _verificar_ausencia_chaves_proibidas(v)
    elif isinstance(obj, list):
        for item in obj:
            _verificar_ausencia_chaves_proibidas(item)


def _verificar_ausencia_termos_proibidos(obj: Any) -> None:
    if isinstance(obj, dict):
        for v in obj.values():
            _verificar_ausencia_termos_proibidos(v)
    elif isinstance(obj, list):
        for item in obj:
            _verificar_ausencia_termos_proibidos(item)
    elif isinstance(obj, str):
        texto_lower = obj.lower()
        for termo in TERMOS_PROIBIDOS:
            assert termo not in texto_lower, f"Termo proibido '{termo}' encontrado no texto: {obj}"


def test_ordem_obrigatorio_conhecimento_primeiro_e_exercicio_no_fim():
    destino = {
        "destino_id": "destino_sintetico",
        "nome": "Destino Sintético de Teste",
        "versao": "1.0.0",
        "requisitos": [
            {
                "id_local": "req1_opc_comp",
                "esco_id": "esco-1",
                "titulo_oficial": "Competência Opcional",
                "tipo_esco": "competência",
                "obrigatorio_proposto": False,
                "descricao_contextual_proposta": "Estudo de competência opcional",
                "evidencia_esperada": "Prática de competência opcional",
            },
            {
                "id_local": "req2_obrig_comp",
                "esco_id": "esco-2",
                "titulo_oficial": "Competência Obrigatória",
                "tipo_esco": "competência",
                "obrigatorio_proposto": True,
                "descricao_contextual_proposta": "Estudo de competência obrigatória",
                "evidencia_esperada": "Prática de competência obrigatória",
            },
            {
                "id_local": "req3_obrig_conh",
                "esco_id": "esco-3",
                "titulo_oficial": "Conhecimento Obrigatório",
                "tipo_esco": "conhecimento",
                "obrigatorio_proposto": True,
                "descricao_contextual_proposta": "Estudo de conhecimento obrigatório",
                "evidencia_esperada": "Prática de conhecimento obrigatório",
            },
            {
                "id_local": "req4_opc_conh",
                "esco_id": "esco-4",
                "titulo_oficial": "Conhecimento Opcional",
                "tipo_esco": "conhecimento",
                "obrigatorio_proposto": False,
                "descricao_contextual_proposta": "Estudo de conhecimento opcional",
                "evidencia_esperada": "Demonstração de conhecimento opcional",
            },
            {
                "id_local": "req5_obrig_conh_dem",
                "esco_id": "esco-5",
                "titulo_oficial": "Conhecimento Demonstrado",
                "tipo_esco": "conhecimento",
                "obrigatorio_proposto": True,
                "descricao_contextual_proposta": "Estudo de conhecimento demonstrado",
                "evidencia_esperada": "Evidência já demonstrada",
            },
        ],
        "exercicio": {
            "id": "ex_sintetico_01",
            "versao": "1.0.0",
        },
    }

    itens_classificados = [
        {
            "id_local": "req1_opc_comp",
            "esco_id": "esco-1",
            "titulo": "Competência Opcional",
            "obrigatorio": False,
            "estado": "desconhecida",
            "motivo": "sem_informacao_suficiente",
            "origem": None,
            "trecho_origem": None,
            "avisos": [],
        },
        {
            "id_local": "req2_obrig_comp",
            "esco_id": "esco-2",
            "titulo": "Competência Obrigatória",
            "obrigatorio": True,
            "estado": "lacuna",
            "motivo": "ausencia_informada_pelo_usuario",
            "origem": None,
            "trecho_origem": None,
            "avisos": [],
        },
        {
            "id_local": "req3_obrig_conh",
            "esco_id": "esco-3",
            "titulo": "Conhecimento Obrigatório",
            "obrigatorio": True,
            "estado": "desconhecida",
            "motivo": "sem_informacao_suficiente",
            "origem": None,
            "trecho_origem": None,
            "avisos": [],
        },
        {
            "id_local": "req4_opc_conh",
            "esco_id": "esco-4",
            "titulo": "Conhecimento Opcional",
            "obrigatorio": False,
            "estado": "declarada",
            "motivo": None,
            "origem": "extracao_llm",
            "trecho_origem": "Trecho de teste",
            "avisos": [],
        },
        {
            "id_local": "req5_obrig_conh_dem",
            "esco_id": "esco-5",
            "titulo": "Conhecimento Demonstrado",
            "obrigatorio": True,
            "estado": "demonstrada",
            "motivo": None,
            "origem": None,
            "trecho_origem": None,
            "avisos": [],
        },
    ]

    plano = gerar_plano(destino, itens_classificados, preferencias=None)

    # 1. Requisito demonstrada vai para ja_demonstrados
    assert plano["ja_demonstrados"] == ["req5_obrig_conh_dem"]

    # 2. Ordem dos checkpoints
    cps = plano["checkpoints"]
    assert len(cps) == 8, f"Esperado 8 checkpoints, obtido {len(cps)}"

    # Checkpoint 1 & 2: obrigatório conhecimento (req3_obrig_conh)
    assert cps[0]["ordem"] == 1
    assert cps[0]["tipo"] == "estudar"
    assert cps[0]["requisito_id_local"] == "req3_obrig_conh"

    assert cps[1]["ordem"] == 2
    assert cps[1]["tipo"] == "praticar"
    assert cps[1]["requisito_id_local"] == "req3_obrig_conh"

    # Checkpoint 3 & 4: obrigatório competência (req2_obrig_comp)
    assert cps[2]["ordem"] == 3
    assert cps[2]["tipo"] == "estudar"
    assert cps[2]["requisito_id_local"] == "req2_obrig_comp"

    assert cps[3]["ordem"] == 4
    assert cps[3]["tipo"] == "praticar"
    assert cps[3]["requisito_id_local"] == "req2_obrig_comp"

    # Checkpoint 5: opcional conhecimento declarada (req4_opc_conh)
    assert cps[4]["ordem"] == 5
    assert cps[4]["tipo"] == "demonstrar"
    assert cps[4]["requisito_id_local"] == "req4_opc_conh"

    # Checkpoint 6 & 7: opcional competência desconhecida (req1_opc_comp)
    assert cps[5]["ordem"] == 6
    assert cps[5]["tipo"] == "estudar"
    assert cps[5]["requisito_id_local"] == "req1_opc_comp"

    assert cps[6]["ordem"] == 7
    assert cps[6]["tipo"] == "praticar"
    assert cps[6]["requisito_id_local"] == "req1_opc_comp"

    # Checkpoint 8: exercício diagnóstico no fim
    assert cps[7]["ordem"] == 8
    assert cps[7]["tipo"] == "exercicio"
    assert cps[7]["exercicio_id"] == "ex_sintetico_01"

    # 3. Verificação de chaves e termos proibidos
    _verificar_ausencia_chaves_proibidas(plano)
    _verificar_ausencia_termos_proibidos(plano)


def test_declarada_gera_so_demonstrar_e_lacuna_repassa_motivo():
    destino = {
        "destino_id": "destino_teste",
        "nome": "Destino Teste",
        "versao": "1.0",
        "requisitos": [
            {
                "id_local": "req_dec",
                "esco_id": "esco-dec",
                "titulo_oficial": "Habilidade Declarada",
                "tipo_esco": "competência",
                "obrigatorio_proposto": True,
                "descricao_contextual_proposta": "Contexto dec",
                "evidencia_esperada": "Evidencia dec",
            },
            {
                "id_local": "req_lac",
                "esco_id": "esco-lac",
                "titulo_oficial": "Habilidade Lacuna",
                "tipo_esco": "competência",
                "obrigatorio_proposto": True,
                "descricao_contextual_proposta": "Contexto lac",
                "evidencia_esperada": "Evidencia lac",
            },
        ],
        "exercicio": {"id": "ex_01", "versao": "1.0"},
    }

    itens_classificados = [
        {
            "id_local": "req_dec",
            "esco_id": "esco-dec",
            "titulo": "Habilidade Declarada",
            "obrigatorio": True,
            "estado": "declarada",
            "motivo": None,
            "origem": "extracao_llm",
            "trecho_origem": "Trecho declarada",
            "avisos": [],
        },
        {
            "id_local": "req_lac",
            "esco_id": "esco-lac",
            "titulo": "Habilidade Lacuna",
            "obrigatorio": True,
            "estado": "lacuna",
            "motivo": "ausencia_informada_pelo_usuario",
            "origem": None,
            "trecho_origem": None,
            "avisos": [],
        },
    ]

    plano = gerar_plano(destino, itens_classificados)
    cps = plano["checkpoints"]

    # req_dec -> demonstrar; req_lac -> estudar + praticar; exercicio -> 1 cp (total 4)
    assert len(cps) == 4

    # req_dec (declarada): só demonstrar
    cp_dec = next(c for c in cps if c["requisito_id_local"] == "req_dec")
    assert cp_dec["tipo"] == "demonstrar"
    assert cp_dec["criterio_conclusao"] == "Evidencia dec"
    assert cp_dec["estado_origem"] == "declarada"

    # req_lac (lacuna com ausencia_informada_pelo_usuario): estudar e praticar com motivo repassado
    cps_lac = [c for c in cps if c["requisito_id_local"] == "req_lac"]
    assert len(cps_lac) == 2
    assert cps_lac[0]["tipo"] == "estudar"
    assert cps_lac[0]["motivo_origem"] == "ausencia_informada_pelo_usuario"
    assert cps_lac[1]["tipo"] == "praticar"
    assert cps_lac[1]["motivo_origem"] == "ausencia_informada_pelo_usuario"
    assert cps_lac[1]["criterio_conclusao"] == "Evidencia lac"


def test_tudo_demonstrado_gera_apenas_exercicio():
    destino = {
        "destino_id": "destino_total",
        "nome": "Destino Totalmente Atendido",
        "versao": "1.0",
        "requisitos": [
            {
                "id_local": "req_1",
                "esco_id": "esco-1",
                "titulo_oficial": "Req 1",
                "tipo_esco": "conhecimento",
                "obrigatorio_proposto": True,
                "descricao_contextual_proposta": "Contexto 1",
                "evidencia_esperada": "Evidencia 1",
            },
            {
                "id_local": "req_2",
                "esco_id": "esco-2",
                "titulo_oficial": "Req 2",
                "tipo_esco": "competência",
                "obrigatorio_proposto": False,
                "descricao_contextual_proposta": "Contexto 2",
                "evidencia_esperada": "Evidencia 2",
            },
        ],
        "exercicio": {"id": "ex_total", "versao": "1.0"},
    }

    itens_classificados = [
        {
            "id_local": "req_1",
            "esco_id": "esco-1",
            "titulo": "Req 1",
            "obrigatorio": True,
            "estado": "demonstrada",
            "motivo": None,
            "origem": None,
            "trecho_origem": None,
            "avisos": [],
        },
        {
            "id_local": "req_2",
            "esco_id": "esco-2",
            "titulo": "Req 2",
            "obrigatorio": False,
            "estado": "demonstrada",
            "motivo": None,
            "origem": None,
            "trecho_origem": None,
            "avisos": [],
        },
    ]

    plano = gerar_plano(destino, itens_classificados)
    assert set(plano["ja_demonstrados"]) == {"req_1", "req_2"}
    assert len(plano["checkpoints"]) == 1
    cp_final = plano["checkpoints"][0]
    assert cp_final["ordem"] == 1
    assert cp_final["tipo"] == "exercicio"
    assert cp_final["exercicio_id"] == "ex_total"


def test_laboratorio_apenas_em_analista_monitoramento_iot():
    destino_iot = {
        "destino_id": "analista_monitoramento_iot",
        "nome": "Analista de Monitoramento IoT",
        "versao": "1.0",
        "tem_laboratorio": True,
        "requisitos": [
            {
                "id_local": "sensores",
                "esco_id": "esco-sens",
                "titulo_oficial": "Sensores",
                "tipo_esco": "conhecimento",
                "obrigatorio_proposto": True,
                "descricao_contextual_proposta": "Estudo sensores",
                "evidencia_esperada": "Evidencia sensores",
            }
        ],
        "exercicio": {"id": "ex_iot", "versao": "1.0"},
    }

    itens_iot = [
        {
            "id_local": "sensores",
            "esco_id": "esco-sens",
            "titulo": "Sensores",
            "obrigatorio": True,
            "estado": "desconhecida",
            "motivo": "sem_informacao_suficiente",
            "origem": None,
            "trecho_origem": None,
            "avisos": [],
        }
    ]

    plano_iot = gerar_plano(destino_iot, itens_iot)
    tipos_iot = [cp["tipo"] for cp in plano_iot["checkpoints"]]
    assert "laboratorio" in tipos_iot
    # O laboratorio deve ser opcional e vir imediatamente antes do exercicio
    idx_lab = tipos_iot.index("laboratorio")
    assert idx_lab == len(tipos_iot) - 2
    assert plano_iot["checkpoints"][idx_lab]["obrigatorio"] is False
    assert tipos_iot[-1] == "exercicio"

    # Outro destino nao pode ter laboratorio
    destino_proc = dict(destino_iot, destino_id="analista_processos", tem_laboratorio=False)
    plano_proc = gerar_plano(destino_proc, itens_iot)
    tipos_proc = [cp["tipo"] for cp in plano_proc["checkpoints"]]
    assert "laboratorio" not in tipos_proc


def test_preferencias_horas_semana_observacoes():
    destino = {
        "destino_id": "analista_processos",
        "nome": "Analista de Processos",
        "versao": "1.0",
        "requisitos": [],
        "exercicio": {"id": "ex_01", "versao": "1.0"},
    }

    # horas_semana < 4 gera observacao
    plano_poucas_horas = gerar_plano(destino, [], preferencias={"horas_semana": 2})
    assert len(plano_poucas_horas["observacoes"]) == 1
    assert "Disponibilidade semanal abaixo de 4 h" in plano_poucas_horas["observacoes"][0]

    # horas_semana >= 4 nao gera observacao
    plano_horas_ok = gerar_plano(destino, [], preferencias={"horas_semana": 10})
    assert plano_horas_ok["observacoes"] == []

    # sem preferencias nao gera observacao
    plano_sem_pref = gerar_plano(destino, [], preferencias=None)
    assert plano_sem_pref["observacoes"] == []

