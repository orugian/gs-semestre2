"""Rotas para gestao de consentimentos do usuario logado (/me/consentimentos)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from citizentech.auth.dependencias import exigir_csrf, obter_usuario_logado
from citizentech.consentimentos.esquemas import (
    ConsentimentoResposta,
    CriarConsentimentoRequisicao,
    ListarConsentimentosResposta,
)
from citizentech.consentimentos.repositorio import (
    criar_consentimento,
    listar_consentimentos,
    revogar_consentimento,
)

router = APIRouter(prefix="/me/consentimentos", tags=["consentimentos"])


@router.post(
    "",
    response_model=ConsentimentoResposta,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(exigir_csrf)],
)
def conceder(
    payload: CriarConsentimentoRequisicao,
    usuario: Annotated[dict, Depends(obter_usuario_logado)],
) -> dict:
    """Concede um novo consentimento para o usuario logado (exige CSRF)."""
    return criar_consentimento(
        usuario_id=usuario["id"],
        finalidade=payload.finalidade,
    )


@router.get(
    "",
    response_model=ListarConsentimentosResposta,
    status_code=status.HTTP_200_OK,
)
def listar(
    usuario: Annotated[dict, Depends(obter_usuario_logado)],
) -> dict:
    """Lista todos os consentimentos pertencentes ao usuario logado (sem exigencia de CSRF)."""
    itens = listar_consentimentos(usuario_id=usuario["id"])
    return {"itens": itens}


@router.delete(
    "/{consentimento_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(exigir_csrf)],
)
def revogar(
    consentimento_id: str,
    usuario: Annotated[dict, Depends(obter_usuario_logado)],
) -> Response:
    """Revoga o consentimento especificado.

    T14: Se o consentimento pertencer a outro usuario ou nao existir, retorna 404
    sem expor a existencia previa do registro.
    """
    sucesso = revogar_consentimento(
        usuario_id=usuario["id"],
        consentimento_id=consentimento_id,
    )

    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "erro": "Nao encontrado",
                "detalhes": "Consentimento nao encontrado.",
            },
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
