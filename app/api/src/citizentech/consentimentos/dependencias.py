"""Dependencias FastAPI e utilitarios de validacao de consentimento LGPD."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Any

from fastapi import Depends

from citizentech.auth.dependencias import obter_usuario_logado
from citizentech.consentimentos.repositorio import listar_consentimentos
from citizentech.erros import ConsentimentoAusente


def validar_consentimento(
    usuario_id: str,
    finalidade: str,
    mensagem_detalhe: str | None = None,
    erro: str = "Consentimento necessario",
) -> None:
    """Valida se ha consentimento ativo para a finalidade; lanca ConsentimentoAusente."""
    consentimentos = listar_consentimentos(usuario_id)
    tem_consentimento = any(
        c.get("finalidade") == finalidade and c.get("revogado_em") is None
        for c in consentimentos
    )
    if not tem_consentimento:
        detalhe = (
            mensagem_detalhe
            if mensagem_detalhe is not None
            else f"Consentimento para a finalidade '{finalidade}' ausente ou revogado."
        )
        raise ConsentimentoAusente(detalhes=detalhe, erro=erro)


def exigir_consentimento(
    finalidade: str,
    mensagem_detalhe: str | None = None,
    erro: str = "Consentimento necessario",
) -> Callable[..., dict[str, Any]]:
    """Cria uma dependencia FastAPI que exige consentimento ativo para a finalidade."""

    def _dependencia(
        usuario: Annotated[dict[str, Any], Depends(obter_usuario_logado)],
    ) -> dict[str, Any]:
        validar_consentimento(
            usuario_id=usuario["id"],
            finalidade=finalidade,
            mensagem_detalhe=mensagem_detalhe,
            erro=erro,
        )
        return usuario

    return _dependencia
