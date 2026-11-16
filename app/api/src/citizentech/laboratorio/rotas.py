"""Rotas para sessao de laboratorio (/me/laboratorio)."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from citizentech.auth.dependencias import exigir_csrf, obter_usuario_logado
from citizentech.consentimentos.repositorio import listar_consentimentos
from citizentech.laboratorio.esquemas import (
    CriarSessaoResposta,
    RegistrarRelatoRequisicao,
    RegistrarRelatoResposta,
    SessaoLaboratorioResposta,
)
from citizentech.laboratorio.repositorio import (
    buscar_sessao_ativa_usuario,
    buscar_sessao_por_id_e_usuario,
)
from citizentech.laboratorio.servico import (
    abrir_nova_sessao,
    compor_detalhes_sessao,
    registrar_relato_sessao,
)

router = APIRouter(prefix="/me/laboratorio", tags=["laboratorio"])


def _verificar_consentimento_laboratorio_nuvem(usuario_id: str) -> None:
    consentimentos = listar_consentimentos(usuario_id)
    tem_consentimento = any(
        c.get("finalidade") == "laboratorio_nuvem" and c.get("revogado_em") is None
        for c in consentimentos
    )
    if not tem_consentimento:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "erro": "Consentimento necessario",
                "detalhes": "Consentimento 'laboratorio_nuvem' ausente ou revogado para o usuario.",
            },
        )


@router.post(
    "/sessoes",
    response_model=CriarSessaoResposta,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(exigir_csrf)],
)
def criar_sessao(
    usuario: Annotated[dict, Depends(obter_usuario_logado)],
) -> Any:
    _verificar_consentimento_laboratorio_nuvem(usuario["id"])
    return abrir_nova_sessao(usuario["id"])


@router.get(
    "/sessoes/atual",
    response_model=SessaoLaboratorioResposta,
    status_code=status.HTTP_200_OK,
)
def obter_sessao_atual(
    usuario: Annotated[dict, Depends(obter_usuario_logado)],
) -> Any:
    sessao = buscar_sessao_ativa_usuario(usuario["id"])
    if not sessao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "erro": "Nao encontrado",
                "detalhes": "Nenhuma sessao de laboratorio ativa encontrada.",
            },
        )
    return compor_detalhes_sessao(sessao)


@router.get(
    "/sessoes/{sessao_id}",
    response_model=SessaoLaboratorioResposta,
    status_code=status.HTTP_200_OK,
)
def obter_sessao_por_id(
    sessao_id: str,
    usuario: Annotated[dict, Depends(obter_usuario_logado)],
) -> Any:
    sessao = buscar_sessao_por_id_e_usuario(sessao_id, usuario["id"])
    if not sessao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "erro": "Nao encontrado",
                "detalhes": "Sessao de laboratorio nao encontrada.",
            },
        )
    return compor_detalhes_sessao(sessao)


@router.post(
    "/sessoes/{sessao_id}/relato",
    response_model=RegistrarRelatoResposta,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(exigir_csrf)],
)
def registrar_relato(
    sessao_id: str,
    payload: RegistrarRelatoRequisicao,
    usuario: Annotated[dict, Depends(obter_usuario_logado)],
) -> Any:
    _verificar_consentimento_laboratorio_nuvem(usuario["id"])
    return registrar_relato_sessao(
        sessao_id=sessao_id,
        usuario_id=usuario["id"],
        relato_bruto=payload.relato,
    )
