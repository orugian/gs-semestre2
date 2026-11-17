"""Rotas da API de comparação de destinos (/me/comparacoes)."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from citizentech.auth.dependencias import exigir_csrf, obter_usuario_logado
from citizentech.comparacao.esquemas import ComparacaoResposta, CriarComparacaoRequisicao
from citizentech.comparacao.repositorio import buscar_comparacao, salvar_comparacao
from citizentech.comparacao.servico import executar_comparacao
from citizentech.consentimentos.dependencias import exigir_consentimento

logger = logging.getLogger("citizentech.comparacao")

router = APIRouter(prefix="/me", tags=["comparacao"])


@router.post(
    "/comparacoes",
    response_model=ComparacaoResposta,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(exigir_csrf)],
)
def criar_comparacao(
    payload: CriarComparacaoRequisicao,
    usuario: Annotated[dict, Depends(exigir_consentimento("perfil"))],
) -> dict[str, Any]:
    """Cria uma nova comparação de até 3 destinos (sem score único)."""
    usuario_id = usuario["id"]

    try:
        resultado_dominio, uf_efetiva = executar_comparacao(
            usuario_id=usuario_id,
            destinos_solicitados=payload.destinos,
            uf_solicitada=payload.uf,
        )
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "erro": "Requisicao invalida",
                "detalhes": str(err),
            },
        ) from err

    comparacao_id = uuid.uuid4().hex
    agora = datetime.now(UTC)
    criado_em = agora.strftime("%Y-%m-%dT%H:%M:%SZ")

    salvar_comparacao(
        comparacao_id=comparacao_id,
        usuario_id=usuario_id,
        uf=uf_efetiva,
        aviso=resultado_dominio["aviso"],
        criado_em=agora,
        destinos=resultado_dominio["destinos"],
    )

    logger.debug("Comparacao criada id=%s usuario_id=%s", comparacao_id, usuario_id)

    return {
        "comparacao_id": comparacao_id,
        "criado_em": criado_em,
        "uf": uf_efetiva,
        "destinos": resultado_dominio["destinos"],
        "aviso": resultado_dominio["aviso"],
    }


@router.get(
    "/comparacoes/{comparacao_id}",
    response_model=ComparacaoResposta,
    status_code=status.HTTP_200_OK,
)
def obter_comparacao(
    comparacao_id: str,
    usuario: Annotated[dict, Depends(obter_usuario_logado)],
) -> dict[str, Any]:
    """Recupera uma comparação salva pelo id."""
    usuario_id = usuario["id"]

    comparacao = buscar_comparacao(
        comparacao_id=comparacao_id,
        usuario_id=usuario_id,
    )
    if comparacao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "erro": "Nao encontrado",
                "detalhes": "Comparacao nao encontrada ou nao pertence ao usuario.",
            },
        )

    return comparacao
