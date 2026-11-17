"""Servico de curriculo e porta de saida para a LLM."""

from typing import Any

from citizentech.consentimentos.dependencias import validar_consentimento
from citizentech.curriculo.repositorio import (
    RepositorioCurriculos,
    obter_repositorio_curriculos,
)
from citizentech.erros import ConsentimentoAusente, NaoEncontrado


class CurriculoNaoLiberado(ConsentimentoAusente):
    """Lancada quando o curriculo nao esta liberado para envio a LLM."""

    def __init__(self, detalhes: str, erro: str = "Acesso negado") -> None:
        super().__init__(detalhes=detalhes, erro=erro)


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
    try:
        validar_consentimento(
            usuario_id,
            "curriculo_llm",
            mensagem_detalhe="Consentimento 'curriculo_llm' ausente ou revogado para o usuario.",
            erro="Acesso negado",
        )
    except ConsentimentoAusente as exc:
        raise CurriculoNaoLiberado(exc.detalhes, erro="Acesso negado") from exc

    # 2. Busca documento pertencente ao usuario (T14)
    doc = repositorio.buscar_por_id(curriculo_id=curriculo_id, usuario_id=usuario_id)
    if not doc:
        raise NaoEncontrado("Curriculo nao encontrado ou nao pertence ao usuario.")

    # 3. Verifica se esta confirmado
    if doc.get("status") != "confirmado":
        raise CurriculoNaoLiberado(
            "Curriculo ainda nao foi confirmado pelo usuario.", erro="Acesso negado"
        )

    return doc["texto_redigido"]
