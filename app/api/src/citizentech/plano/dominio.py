"""Dominio puro de geracao de plano inicial deterministico por regras.

Decisoes D03, T07, T08:
- Regras deterministicas sobre o catalogo existente, sem conteudo novo e sem LLM.
- Concluir checkpoint nao torna competencia demonstrada (somente exercicio).
- Ordem simples: obrigatorios de conhecimento, outros obrigatorios,
  opcionais conhecimento, outros opcionais.
- Sem estimativas de horas, semanas, prazos, score, nota ou ranking.
"""

from __future__ import annotations

import unicodedata
from typing import Any

REGRA_PLANO_V1 = "ordem_por_obrigatoriedade_e_tipo_v1"
EXPLICACAO_REGRA_V1 = (
    "Ordem definida por regras simples: requisitos obrigatórios de conhecimento primeiro, "
    "seguidos dos demais obrigatórios, opcionais de conhecimento e demais opcionais. "
    "Cada requisito não demonstrado gera etapas de estudo e prática ou demonstração, "
    "concluindo com o exercício diagnóstico."
)
AVISO_PLANO = (
    "Plano inicial gerado por regras simples a partir do catálogo revisado; "
    "concluir uma etapa não torna a competência demonstrada: isso só acontece pelo exercício."
)
OBS_HORAS_BAIXAS = "Disponibilidade semanal abaixo de 4 h: o plano tende a se estender."


def _normalizar_tipo(tipo: str | None) -> str:
    if not tipo:
        return ""
    nf = unicodedata.normalize("NFKD", str(tipo)).encode("ascii", "ignore").decode("ascii")
    return nf.strip().lower()


def gerar_plano(
    destino: dict[str, Any],
    itens_classificados: list[dict[str, Any]],
    preferencias: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Gera deterministamente o plano inicial de transicao e checkpoints.

    Entradas:
    - destino: dict do YAML aprovado (destino_id, nome, versao, requisitos, exercicio).
    - itens_classificados: lista retornada por comparacao.dominio.classificar_requisitos.
    - preferencias: dados de intencao do usuario (opcional).
    """
    requisitos_catalogo = destino.get("requisitos") or []
    req_map: dict[str, dict[str, Any]] = {
        str(r.get("id_local")): r for r in requisitos_catalogo if r.get("id_local") is not None
    }

    classif_map: dict[str, dict[str, Any]] = {
        str(it.get("id_local")): it for it in itens_classificados if it.get("id_local") is not None
    }

    ja_demonstrados: list[str] = []
    g1_obrig_conh: list[str] = []
    g2_obrig_outros: list[str] = []
    g3_opc_conh: list[str] = []
    g4_opc_outros: list[str] = []

    # Processa na ordem exata do catalogo
    for req in requisitos_catalogo:
        id_local = str(req.get("id_local"))
        it = classif_map.get(id_local)
        if not it:
            continue

        estado = it.get("estado")
        if estado == "demonstrada":
            ja_demonstrados.append(id_local)
            continue

        obrigatorio = bool(it.get("obrigatorio"))
        tipo_normalizado = _normalizar_tipo(req.get("tipo_esco"))
        eh_conhecimento = tipo_normalizado == "conhecimento"

        if obrigatorio and eh_conhecimento:
            g1_obrig_conh.append(id_local)
        elif obrigatorio and not eh_conhecimento:
            g2_obrig_outros.append(id_local)
        elif not obrigatorio and eh_conhecimento:
            g3_opc_conh.append(id_local)
        else:
            g4_opc_outros.append(id_local)

    requisitos_ordenados = g1_obrig_conh + g2_obrig_outros + g3_opc_conh + g4_opc_outros

    checkpoints: list[dict[str, Any]] = []
    ordem_atual = 1

    for id_local in requisitos_ordenados:
        req = req_map.get(id_local, {})
        it = classif_map.get(id_local, {})

        estado = it.get("estado")
        motivo = it.get("motivo")
        obrigatorio = bool(it.get("obrigatorio"))
        titulo = str(req.get("titulo_oficial") or it.get("titulo") or id_local)
        desc_proposta = req.get("descricao_contextual_proposta")
        evidencia = req.get("evidencia_esperada")

        if estado in ("lacuna", "desconhecida"):
            # Checkpoint 1: estudar
            checkpoints.append(
                {
                    "ordem": ordem_atual,
                    "tipo": "estudar",
                    "titulo": f"Estudar: {titulo}",
                    "descricao": str(desc_proposta) if desc_proposta else None,
                    "criterio_conclusao": None,
                    "requisito_id_local": id_local,
                    "estado_origem": estado,
                    "motivo_origem": motivo,
                    "obrigatorio": obrigatorio,
                    "exercicio_id": None,
                }
            )
            ordem_atual += 1

            # Checkpoint 2: praticar
            checkpoints.append(
                {
                    "ordem": ordem_atual,
                    "tipo": "praticar",
                    "titulo": f"Praticar: {titulo}",
                    "descricao": None,
                    "criterio_conclusao": str(evidencia) if evidencia else None,
                    "requisito_id_local": id_local,
                    "estado_origem": estado,
                    "motivo_origem": motivo,
                    "obrigatorio": obrigatorio,
                    "exercicio_id": None,
                }
            )
            ordem_atual += 1

        elif estado == "declarada":
            # Checkpoint: demonstrar
            checkpoints.append(
                {
                    "ordem": ordem_atual,
                    "tipo": "demonstrar",
                    "titulo": f"Demonstrar: {titulo}",
                    "descricao": (
                        "Experiência prévia declarada. A demonstração formal "
                        "ocorre por meio do exercício diagnóstico prático."
                    ),
                    "criterio_conclusao": str(evidencia) if evidencia else None,
                    "requisito_id_local": id_local,
                    "estado_origem": estado,
                    "motivo_origem": motivo,
                    "obrigatorio": obrigatorio,
                    "exercicio_id": None,
                }
            )
            ordem_atual += 1

    # Checkpoint opcional de laboratorio guiado por dados
    if bool(destino.get("tem_laboratorio")):
        checkpoints.append(
            {
                "ordem": ordem_atual,
                "tipo": "laboratorio",
                "titulo": "Sessão prática no laboratório de monitoramento (opcional)",
                "descricao": "Atividade prática complementar em ambiente simulado de laboratório.",
                "criterio_conclusao": None,
                "requisito_id_local": None,
                "estado_origem": None,
                "motivo_origem": None,
                "obrigatorio": False,
                "exercicio_id": None,
            }
        )
        ordem_atual += 1

    # Checkpoint final de exercicio (sempre presente)
    exercicio_info = destino.get("exercicio") or {}
    exercicio_id = exercicio_info.get("id") if isinstance(exercicio_info, dict) else None

    checkpoints.append(
        {
            "ordem": ordem_atual,
            "tipo": "exercicio",
            "titulo": "Fazer o exercício diagnóstico do destino",
            "descricao": (
                "Avaliação prática e diagnóstica para demonstração das competências do destino."
            ),
            "criterio_conclusao": None,
            "requisito_id_local": None,
            "estado_origem": None,
            "motivo_origem": None,
            "obrigatorio": True,
            "exercicio_id": exercicio_id,
        }
    )

    observacoes: list[str] = []
    if preferencias and isinstance(preferencias, dict):
        horas = preferencias.get("horas_semana")
        if horas is not None and horas < 4:
            observacoes.append(OBS_HORAS_BAIXAS)

    return {
        "destino_id": destino.get("destino_id", ""),
        "nome": destino.get("nome", ""),
        "versao_catalogo": destino.get("versao", ""),
        "regra": REGRA_PLANO_V1,
        "explicacao_regra": EXPLICACAO_REGRA_V1,
        "ja_demonstrados": ja_demonstrados,
        "checkpoints": checkpoints,
        "observacoes": observacoes,
        "aviso": AVISO_PLANO,
    }
