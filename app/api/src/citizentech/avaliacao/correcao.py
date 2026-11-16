"""Funcoes puras de correcao de exercicio diagnostico (S13)."""

from __future__ import annotations

from typing import Any


def corrigir_questoes_objetivas(
    questoes: list[dict[str, Any]],
    respostas_usuario: dict[str, str],
) -> dict[str, Any]:
    """Corrige deterministicamente questoes objetivas contra o gabarito.

    Retorna acertos, total, nota exata e detalhe por questao com justificativa.
    """
    acertos = 0
    questoes_corrigidas: list[dict[str, Any]] = []

    for q in questoes:
        qid = str(q["id"])
        gabarito = str(q.get("gabarito", "")).strip().upper()
        resposta = str(respostas_usuario.get(qid, "")).strip().upper()
        correta = (resposta == gabarito) if (resposta and gabarito) else False
        if correta:
            acertos += 1

        questoes_corrigidas.append(
            {
                "id": qid,
                "resposta": resposta,
                "correta": correta,
                "gabarito": gabarito,
                "justificativa": str(q.get("justificativa", "")),
            }
        )

    total = len(questoes)
    nota = (acertos / total) if total > 0 else 0.0

    return {
        "acertos": acertos,
        "total": total,
        "nota": nota,
        "questoes": questoes_corrigidas,
    }


def calcular_nota_aberta_llm(
    criterios_avaliados: list[dict[str, Any]],
    total_criterios_rubrica: int,
) -> float:
    """Calcula a nota da dissertativa: soma dos niveis / (2 * total de criterios)."""
    if total_criterios_rubrica <= 0:
        return 0.0
    soma_niveis = sum(int(c.get("nivel", 0)) for c in criterios_avaliados)
    return soma_niveis / (2.0 * total_criterios_rubrica)


def calcular_nota_final(
    nota_objetiva: float,
    nota_llm: float | None,
    peso_objetiva: float = 0.5,
    peso_llm: float = 0.5,
) -> float | None:
    """Composicao ponderada 50/50 da nota final.

    Retorna None se a dissertativa for parcial / nao avaliada.
    """
    if nota_llm is None:
        return None
    return (peso_objetiva * nota_objetiva) + (peso_llm * nota_llm)


def determinar_resultado(
    nota_objetiva: float,
    nota_llm: float | None,
    status_aberta: str,
    minimo_objetiva: float = 0.5,
    minimo_llm: float = 0.5,
) -> str:
    """Determina o resultado da avaliacao (D06).

    - 'parcial' se a dissertativa for parcial ou nota_llm ausente.
    - 'demonstrada' se e somente se AMBAS as partes atingirem seus minimos.
    - 'insuficiente' caso contrario (nunca demonstrada apenas pela media).
    """
    if status_aberta == "parcial" or nota_llm is None:
        return "parcial"

    # Comparacao com os valores exatos de minimo
    if (nota_objetiva >= minimo_objetiva) and (nota_llm >= minimo_llm):
        return "demonstrada"

    return "insuficiente"
