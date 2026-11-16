"""Servico de curriculo e porta de saida para a LLM."""

from typing import Any

from citizentech.consentimentos.repositorio import listar_consentimentos
from citizentech.curriculo.repositorio import (
    RepositorioCurriculos,
    obter_repositorio_curriculos,
)


class CurriculoNaoLiberado(Exception):
    """Lancada quando o curriculo nao esta liberado para envio a LLM."""

    def __init__(self, detalhes: str) -> None:
        super().__init__(detalhes)
        self.detalhes = detalhes


def texto_liberado_para_llm(
    usuario_id: str,
    curriculo_id: str,
    repositorio: RepositorioCurriculos | Any = None,
) -> str:
    """Devolve o texto redigido somente se confirmado e com consentimento ativo.

    Esta e a UNICA funcao pela qual o texto podera chegar a LLM na fatia S10.
    """
    if repositorio is None:
        repositorio = obter_repositorio_curriculos()

    # 1. Verifica se o consentimento curriculo_llm esta ativo (nao revogado)
    consentimentos = listar_consentimentos(usuario_id)
    curriculo_llm_ativo = any(
        c.get("finalidade") == "curriculo_llm" and c.get("revogado_em") is None
        for c in consentimentos
    )
    if not curriculo_llm_ativo:
        raise CurriculoNaoLiberado(
            "Consentimento 'curriculo_llm' ausente ou revogado para o usuario."
        )

    # 2. Busca documento pertencente ao usuario (T14)
    doc = repositorio.buscar_por_id(curriculo_id=curriculo_id, usuario_id=usuario_id)
    if not doc:
        raise CurriculoNaoLiberado(
            "Curriculo nao encontrado ou nao pertence ao usuario."
        )

    # 3. Verifica se esta confirmado
    if doc.get("status") != "confirmado":
        raise CurriculoNaoLiberado(
            "Curriculo ainda nao foi confirmado pelo usuario."
        )

    return doc["texto_redigido"]
