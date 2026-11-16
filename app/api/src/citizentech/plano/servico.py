"""Servico de aplicacao para o plano de transicao."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException, status

from citizentech.comparacao.dominio import classificar_requisitos
from citizentech.competencias.repositorio import competencias_para_comparacao
from citizentech.destinos.catalogo import carregar_destinos_aprovados_brutos
from citizentech.intencao.repositorio import buscar_intencao
from citizentech.plano.dominio import gerar_plano
from citizentech.plano.repositorio import (
    atualizar_status_checkpoint,
    buscar_caminho_ativo,
    obter_checkpoint_para_atualizacao,
    salvar_caminho_e_plano,
    verificar_comparacao_usuario,
)

logger = logging.getLogger("citizentech.plano")


def _resultados_exercicio(usuario_id: str) -> list[dict[str, Any]]:
    """Devolve os resultados de exercicios diagnósticos para o usuario.

    Por enquanto retorna lista vazia; ligado à avaliacao na integracao.
    """
    return []


def gerar_e_salvar_caminho(
    usuario_id: str,
    destino_id: str,
    comparacao_id: str | None,
) -> dict[str, Any]:
    """Valida entradas, monta o plano deterministico e persiste no banco."""
    # 1. Validacao de comparacao_id se informado
    if comparacao_id:
        valido, erro_tipo = verificar_comparacao_usuario(comparacao_id, usuario_id, destino_id)
        if not valido:
            if erro_tipo == "404":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "erro": "Nao encontrado",
                        "detalhes": "Comparacao informada nao encontrada para o usuario.",
                    },
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "erro": "Destino invalido",
                    "detalhes": "Destino informado nao faz parte da comparacao indicada.",
                },
            )

    # 2. Carrega destinos aprovados e valida destino_id
    destinos_aprovados = carregar_destinos_aprovados_brutos()
    destino = next((d for d in destinos_aprovados if d.get("destino_id") == destino_id), None)
    if not destino:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "erro": "Destino invalido",
                "detalhes": "Destino fora do escopo ou nao aprovado.",
            },
        )

    # 3. Coleta competencias confirmadas, exercicios e intencao
    competencias = competencias_para_comparacao(usuario_id)
    resultados_ex = _resultados_exercicio(usuario_id)
    preferencias = buscar_intencao(usuario_id)

    # 4. Classifica requisitos
    requisitos_catalogo = destino.get("requisitos") or []
    itens_classificados = classificar_requisitos(requisitos_catalogo, competencias, resultados_ex)

    # 5. Gera plano deterministico
    plano_dict = gerar_plano(destino, itens_classificados, preferencias)

    # 6. Persiste caminho, plano e checkpoints
    versao_catalogo = str(destino.get("versao", ""))
    destino_nome = str(destino.get("nome", destino_id))
    caminho = salvar_caminho_e_plano(
        usuario_id=usuario_id,
        destino_id=destino_id,
        destino_nome=destino_nome,
        comparacao_id=comparacao_id,
        versao_catalogo=versao_catalogo,
        plano_dict=plano_dict,
        itens_classificados=itens_classificados,
    )

    logger.debug(
        "Caminho criado com sucesso: caminho_id=%s destino_id=%s",
        caminho["caminho_id"],
        destino_id,
    )
    return caminho


def obter_caminho_ativo_usuario(usuario_id: str) -> dict[str, Any]:
    """Recupera o caminho ativo do usuario com status atuais dos checkpoints."""
    destinos_aprovados = carregar_destinos_aprovados_brutos()
    catalogo_map = {d.get("destino_id"): d for d in destinos_aprovados if d.get("destino_id")}

    caminho = buscar_caminho_ativo(usuario_id, catalogo_map)
    if not caminho:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "erro": "Nao encontrado",
                "detalhes": "Nenhum plano ativo encontrado para o usuario.",
            },
        )
    return caminho


def atualizar_checkpoint_usuario(
    checkpoint_id: str,
    novo_status: str,
    usuario_id: str,
) -> dict[str, Any]:
    """Atualiza o status de um checkpoint especifico do usuario."""
    cp_info = obter_checkpoint_para_atualizacao(checkpoint_id, usuario_id)
    if not cp_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "erro": "Nao encontrado",
                "detalhes": "Checkpoint nao encontrado ou de plano inativo/outro usuario.",
            },
        )

    if cp_info.get("tipo") == "exercicio":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "erro": "Conflito",
                "detalhes": "O status do exercicio vem da avaliacao.",
            },
        )

    atualizado = atualizar_status_checkpoint(checkpoint_id, novo_status)
    logger.debug(
        "Checkpoint atualizado: id=%s novo_status=%s",
        checkpoint_id,
        novo_status,
    )
    return atualizado
