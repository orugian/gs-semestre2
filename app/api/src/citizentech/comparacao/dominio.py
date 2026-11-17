"""Domínio puro de comparação de destinos de transição (sem score único).

Decisões D07, R29, T07:
- Classificação determinística em dimensões separadas.
- Não existe score único, nota, ranking ou percentual de aderência.
- Requisitos obrigatórios não atendidos nunca desaparecem numa média.
"""

from typing import Any

from citizentech.catalogo import normalizar_requisito

ESTADOS_VALIDOS_COMPETENCIA = frozenset({"declarada", "rejeitada", "nao_possuo"})
RESULTADOS_VALIDOS_EXERCICIO = frozenset({"demonstrada", "insuficiente", "parcial"})

ESTADO_DEMONSTRADA = "demonstrada"
ESTADO_DECLARADA = "declarada"
ESTADO_DESCONHECIDA = "desconhecida"
ESTADO_LACUNA = "lacuna"

MOTIVO_EXERCICIO_ABAIXO = "exercicio_abaixo_do_minimo"
MOTIVO_AUSENCIA_INFORMADA = "ausencia_informada_pelo_usuario"
MOTIVO_SEM_INFORMACAO = "sem_informacao_suficiente"
MOTIVO_PARCIAL = "avaliacao_parcial_llm_indisponivel"

AVISO_ENTRADA_CONFLITANTE = "entrada_conflitante"

AVISO_GERAL = "Sem nota única: cada dimensão é apresentada separadamente e a decisão é sua."


def _validar_competencias_e_exercicios(
    competencias: list[dict[str, Any]],
    resultados_exercicio: Any,
) -> None:
    for comp in competencias:
        estado = comp.get("estado")
        if estado not in ESTADOS_VALIDOS_COMPETENCIA:
            raise ValueError(f"Estado de competência inválido na entrada: '{estado}'")

    for ex in resultados_exercicio:
        resultado = ex.get("resultado")
        if resultado not in RESULTADOS_VALIDOS_EXERCICIO:
            raise ValueError(f"Resultado de exercício inválido na entrada: '{resultado}'")


def classificar_requisitos(
    requisitos: list[dict[str, Any]],
    competencias: list[dict[str, Any]],
    resultados_exercicio: Any,
) -> list[dict[str, Any]]:
    """Classifica deterministamente cada requisito do catálogo.

    Precedência:
    1. Exercício com resultado 'demonstrada' -> demonstrada.
    2. Exercício com resultado 'insuficiente' -> lacuna (exercicio_abaixo_do_minimo).
    3. Competência com estado 'nao_possuo' -> lacuna (ausencia_informada_pelo_usuario).
    4. Competência com estado 'declarada' -> declarada (origem repassada).
    5. Caso contrário -> desconhecida (sem_informacao_suficiente ou avaliacao_parcial).
    """
    _validar_competencias_e_exercicios(competencias, resultados_exercicio)

    # Agrupa competências por esco_id preservando itens
    comps_por_esco: dict[str, list[dict[str, Any]]] = {}
    for comp in competencias:
        eid = comp.get("esco_id")
        if eid:
            comps_por_esco.setdefault(eid, []).append(comp)

    # Agrupa exercícios por esco_id
    exs_por_esco: dict[str, list[dict[str, Any]]] = {}
    for ex in resultados_exercicio:
        eids = ex.get("esco_ids_avaliados")
        if eids is None and "esco_id" in ex:
            eids = [ex["esco_id"]]
        if eids:
            for eid in eids:
                exs_por_esco.setdefault(eid, []).append(ex)

    itens_classificados: list[dict[str, Any]] = []

    for req in requisitos:
        req_norm = normalizar_requisito(req)
        id_local = req_norm["id_local"]
        esco_id = req_norm["esco_id"]
        titulo = req_norm["titulo"]
        obrigatorio = req_norm["obrigatorio"]

        comps = comps_por_esco.get(esco_id, [])
        exs = exs_por_esco.get(esco_id, [])

        estados_comp = {c.get("estado") for c in comps}
        resultados_ex = {e.get("resultado") for e in exs}

        # Detecção de conflito na entrada
        tem_conflito = False
        if len(estados_comp) > 1:
            tem_conflito = True
        if "demonstrada" in resultados_ex and "insuficiente" in resultados_ex:
            tem_conflito = True
        if "demonstrada" in resultados_ex and (
            "nao_possuo" in estados_comp or "rejeitada" in estados_comp
        ):
            tem_conflito = True
        if "insuficiente" in resultados_ex and "declarada" in estados_comp:
            tem_conflito = True

        avisos: list[str] = [AVISO_ENTRADA_CONFLITANTE] if tem_conflito else []

        # Aplicação determinística da precedência
        estado: str
        motivo: str | None = None
        origem: str | None = None
        trecho_origem: str | None = None

        if "demonstrada" in resultados_ex:
            estado = ESTADO_DEMONSTRADA
            motivo = None
        elif "insuficiente" in resultados_ex:
            estado = ESTADO_LACUNA
            motivo = MOTIVO_EXERCICIO_ABAIXO
        elif "nao_possuo" in estados_comp:
            estado = ESTADO_LACUNA
            motivo = MOTIVO_AUSENCIA_INFORMADA
        elif "declarada" in estados_comp:
            estado = ESTADO_DECLARADA
            motivo = None
            comp_declarada = next(c for c in comps if c.get("estado") == "declarada")
            origem = comp_declarada.get("origem")
            trecho_origem = comp_declarada.get("trecho_origem")
        else:
            estado = ESTADO_DESCONHECIDA
            if "parcial" in resultados_ex:
                motivo = MOTIVO_PARCIAL
            else:
                motivo = MOTIVO_SEM_INFORMACAO

        itens_classificados.append({
            "id_local": id_local,
            "esco_id": esco_id,
            "titulo": str(titulo),
            "obrigatorio": bool(obrigatorio),
            "estado": estado,
            "motivo": motivo,
            "origem": origem,
            "trecho_origem": trecho_origem,
            "avisos": avisos,
        })

    return itens_classificados


def comparar_destinos(
    destinos: list[dict[str, Any]],
    competencias: list[dict[str, Any]],
    resultados_exercicio: Any = (),
    preferencias: dict[str, Any] | None = None,
    mercado: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compara até 3 destinos de transição sem score único.

    Validações:
    - 0 ou > 3 destinos -> ValueError
    - destino_id repetido -> ValueError
    - status_revisao != 'aprovado' -> ValueError
    """
    total_destinos = len(destinos) if destinos else 0
    if not destinos or total_destinos > 3:
        raise ValueError(
            f"Quantidade de destinos inválida ({total_destinos}). Deve ser entre 1 e 3."
        )

    ids = [d.get("destino_id") for d in destinos]
    if any(not i for i in ids):
        raise ValueError("Destino com identificador 'destino_id' inválido ou ausente.")
    if len(ids) != len(set(ids)):
        raise ValueError("Destinos repetidos não são permitidos na comparação.")

    for d in destinos:
        status = d.get("status_revisao")
        if not status and isinstance(d.get("revisao_humana"), dict):
            status = d["revisao_humana"].get("status")
        if status != "aprovado":
            raise ValueError(
                f"Destino '{d.get('destino_id')}' possui status de revisão '{status}'. "
                "Apenas destinos com status 'aprovado' podem ser comparados."
            )

    destinos_saida: list[dict[str, Any]] = []

    conflitos_pref: list[str] = []
    observacoes_pref: list[str] = []
    if preferencias:
        horas = preferencias.get("horas_semana")
        if horas is not None and horas < 4:
            conflitos_pref.append(
                "Disponibilidade semanal abaixo de 4 h torna o plano de preparação muito longo."
            )

    for d in destinos:
        requisitos = d.get("requisitos", [])
        itens = classificar_requisitos(requisitos, competencias, resultados_exercicio)

        contagem = {
            ESTADO_DEMONSTRADA: sum(1 for it in itens if it["estado"] == ESTADO_DEMONSTRADA),
            ESTADO_DECLARADA: sum(1 for it in itens if it["estado"] == ESTADO_DECLARADA),
            ESTADO_DESCONHECIDA: sum(1 for it in itens if it["estado"] == ESTADO_DESCONHECIDA),
            ESTADO_LACUNA: sum(1 for it in itens if it["estado"] == ESTADO_LACUNA),
        }

        obrigatorios_nao_atendidos = [
            {
                "id_local": it["id_local"],
                "titulo": it["titulo"],
                "estado": it["estado"],
            }
            for it in itens
            if it["obrigatorio"] and it["estado"] != ESTADO_DEMONSTRADA
        ]

        if obrigatorios_nao_atendidos:
            situacao_obrigatorios = "ha_obrigatorios_nao_demonstrados"
        else:
            situacao_obrigatorios = "todos_demonstrados"

        declarados_ids = [it["id_local"] for it in itens if it["estado"] == ESTADO_DECLARADA]
        demonstrados_ids = [it["id_local"] for it in itens if it["estado"] == ESTADO_DEMONSTRADA]

        did = d["destino_id"]
        if mercado and did in mercado and mercado[did] is not None:
            mercado_destino = mercado[did]
        else:
            mercado_destino = {"disponivel": False, "natureza": "indisponivel"}

        destinos_saida.append({
            "destino_id": did,
            "nome": d.get("nome", ""),
            "dimensoes": {
                "requisitos": {
                    "itens": itens,
                    "contagem": contagem,
                },
                "obrigatorios_nao_atendidos": obrigatorios_nao_atendidos,
                "aproveitamento_experiencia": {
                    "declarados": declarados_ids,
                    "demonstrados": demonstrados_ids,
                },
                "mercado": mercado_destino,
                "preferencias": {
                    "conflitos": list(conflitos_pref),
                    "observacoes": list(observacoes_pref),
                },
            },
            "situacao_obrigatorios": situacao_obrigatorios,
        })

    return {
        "destinos": destinos_saida,
        "aviso": AVISO_GERAL,
    }
