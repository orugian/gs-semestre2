"""Servico de aplicacao para o plano de transicao."""

from __future__ import annotations

import logging
from typing import Any

from citizentech.avaliacao.repositorio import resultados_exercicio_para_comparacao
from citizentech.catalogo import carregar_destino_aprovado, carregar_destinos_aprovados
from citizentech.comparacao.dominio import classificar_requisitos
from citizentech.competencias.repositorio import competencias_para_comparacao
from citizentech.erros import Conflito, NaoEncontrado, RequisicaoInvalida
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
                raise NaoEncontrado("Comparacao informada nao encontrada para o usuario.")
            raise RequisicaoInvalida(
                detalhes="Destino informado nao faz parte da comparacao indicada.",
                erro="Destino invalido",
            )

    # 2. Carrega destino aprovado e valida destino_id
    destino = carregar_destino_aprovado(destino_id)
    if not destino:
        raise RequisicaoInvalida(
            detalhes="Destino fora do escopo ou nao aprovado.",
            erro="Destino invalido",
        )

    # 3. Coleta competencias confirmadas, exercicios e intencao
    competencias = competencias_para_comparacao(usuario_id)
    resultados_ex = resultados_exercicio_para_comparacao(usuario_id)
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
    destinos_aprovados = carregar_destinos_aprovados()
    catalogo_map = {d.get("destino_id"): d for d in destinos_aprovados if d.get("destino_id")}

    caminho = buscar_caminho_ativo(usuario_id, catalogo_map)
    if not caminho:
        raise NaoEncontrado("Nenhum plano ativo encontrado para o usuario.")
    return caminho


def atualizar_checkpoint_usuario(
    checkpoint_id: str,
    novo_status: str,
    usuario_id: str,
) -> dict[str, Any]:
    """Atualiza o status de um checkpoint especifico do usuario."""
    cp_info = obter_checkpoint_para_atualizacao(checkpoint_id, usuario_id)
    if not cp_info:
        raise NaoEncontrado("Checkpoint nao encontrado ou de plano inativo/outro usuario.")

    if cp_info.get("tipo") == "exercicio":
        raise Conflito("O status do exercicio vem da avaliacao.")

    atualizado = atualizar_status_checkpoint(checkpoint_id, novo_status)
    logger.debug(
        "Checkpoint atualizado: id=%s novo_status=%s",
        checkpoint_id,
        novo_status,
    )
    return atualizado
