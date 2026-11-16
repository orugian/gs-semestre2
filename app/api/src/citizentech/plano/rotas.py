"""Rotas da API para caminho escolhido e plano inicial com checkpoints (/me/*)."""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from citizentech.auth.dependencias import exigir_csrf, obter_usuario_logado
from citizentech.consentimentos.repositorio import listar_consentimentos
from citizentech.plano.esquemas import (
    AtualizarCheckpointRequisicao,
    CaminhoRequisicao,
    CaminhoResposta,
    CheckpointItem,
)
from citizentech.plano.servico import (
    atualizar_checkpoint_usuario,
    gerar_e_salvar_caminho,
    obter_caminho_ativo_usuario,
)

logger = logging.getLogger("citizentech.plano")

router = APIRouter(prefix="/me", tags=["plano"])


def _verificar_consentimento_ativo(usuario_id: str, finalidade: str) -> bool:
    """Verifica se o usuario possui consentimento ativo para a finalidade."""
    consentimentos = listar_consentimentos(usuario_id)
    return any(
        c.get("finalidade") == finalidade and c.get("revogado_em") is None
        for c in consentimentos
    )


@router.post(
    "/caminho",
    response_model=CaminhoResposta,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(exigir_csrf)],
)
def escolher_caminho(
    payload: CaminhoRequisicao,
    usuario: Annotated[dict, Depends(obter_usuario_logado)],
) -> Any:
    """Escolhe 1 destino e gera o plano inicial com checkpoints determinísticos."""
    usuario_id = usuario["id"]

    if not _verificar_consentimento_ativo(usuario_id, "perfil"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "erro": "Consentimento necessario",
                "detalhes": "Consentimento para a finalidade 'perfil' ausente ou revogado.",
            },
        )

    return gerar_e_salvar_caminho(
        usuario_id=usuario_id,
        destino_id=payload.destino_id,
        comparacao_id=payload.comparacao_id,
    )


@router.get(
    "/plano",
    response_model=CaminhoResposta,
    status_code=status.HTTP_200_OK,
)
def obter_plano_ativo(
    usuario: Annotated[dict, Depends(obter_usuario_logado)],
) -> Any:
    """Recupera o plano ativo e os status atuais dos checkpoints do usuário."""
    usuario_id = usuario["id"]
    return obter_caminho_ativo_usuario(usuario_id)


@router.patch(
    "/plano/checkpoints/{checkpoint_id}",
    response_model=CheckpointItem,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(exigir_csrf)],
)
def atualizar_checkpoint(
    checkpoint_id: str,
    payload: AtualizarCheckpointRequisicao,
    usuario: Annotated[dict, Depends(obter_usuario_logado)],
) -> Any:
    """Atualiza o status de um checkpoint. A rota NÃO altera nenhuma competência."""
    usuario_id = usuario["id"]
    return atualizar_checkpoint_usuario(
        checkpoint_id=checkpoint_id,
        novo_status=payload.status,
        usuario_id=usuario_id,
    )
