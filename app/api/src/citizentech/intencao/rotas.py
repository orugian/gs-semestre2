"""Rotas da API de intenção de transição profissional (/me/intencao)."""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from citizentech.auth.dependencias import exigir_csrf, obter_usuario_logado
from citizentech.consentimentos.repositorio import listar_consentimentos
from citizentech.curriculo.redacao import redigir_pii
from citizentech.intencao.esquemas import IntencaoRequisicao, IntencaoResposta
from citizentech.intencao.repositorio import buscar_intencao, salvar_intencao

logger = logging.getLogger("citizentech.intencao")

router = APIRouter(prefix="/me", tags=["intencao"])


def _verificar_consentimento_ativo(usuario_id: str, finalidade: str) -> bool:
    """Verifica se o usuário possui consentimento ativo (não revogado) para a finalidade."""
    consentimentos = listar_consentimentos(usuario_id)
    return any(
        c.get("finalidade") == finalidade and c.get("revogado_em") is None
        for c in consentimentos
    )


@router.put(
    "/intencao",
    response_model=IntencaoResposta,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(exigir_csrf)],
)
def registrar_intencao(
    payload: IntencaoRequisicao,
    usuario: Annotated[dict, Depends(obter_usuario_logado)],
) -> dict[str, Any]:
    """Registra ou atualiza a intenção de transição profissional do usuário."""
    usuario_id = usuario["id"]

    if not _verificar_consentimento_ativo(usuario_id, "perfil"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "erro": "Consentimento necessario",
                "detalhes": "Consentimento para a finalidade 'perfil' ausente ou revogado.",
            },
        )

    # Redige cada motivo antes de gravar (minimização de PII)
    motivos_redigidos: list[str] = []
    for motivo in payload.motivos:
        texto_redigido, _ = redigir_pii(motivo)
        motivos_redigidos.append(texto_redigido)

    resultado = salvar_intencao(
        usuario_id=usuario_id,
        atividades_desejadas=payload.atividades_desejadas,
        motivos=motivos_redigidos,
        horas_semana=payload.horas_semana,
        orcamento_mensal_brl=payload.orcamento_mensal_brl,
        uf=payload.uf,
    )

    logger.debug("Intencao atualizada para usuario_id=%s uf=%s", usuario_id, payload.uf)
    return resultado


@router.get(
    "/intencao",
    response_model=IntencaoResposta,
    status_code=status.HTTP_200_OK,
)
def obter_intencao(
    usuario: Annotated[dict, Depends(obter_usuario_logado)],
) -> dict[str, Any]:
    """Recupera a intenção de transição profissional registrada pelo usuário."""
    usuario_id = usuario["id"]

    intencao = buscar_intencao(usuario_id)
    if intencao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "erro": "Nao encontrado",
                "detalhes": "Intencao de transicao nao encontrada para o usuario.",
            },
        )

    return intencao
