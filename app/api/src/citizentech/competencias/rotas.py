"""Rotas de extracao e revisao de competencias (/me/competencias)."""

from __future__ import annotations

import hashlib
import logging
import os
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from citizentech.auth.dependencias import exigir_csrf, obter_usuario_logado
from citizentech.competencias.catalogo import carregar_catalogo_competencias
from citizentech.competencias.esquemas import (
    AtualizarCompetenciaRequisicao,
    ExtrairCompetenciasRequisicao,
)
from citizentech.competencias.extracao import (
    construir_mensagens_extracao,
    gerar_schema_extracao,
    validar_saida_llm,
)
from citizentech.competencias.repositorio import (
    atualizar_competencia,
    contar_extracoes_24h,
    listar_competencias_usuario,
    registrar_extracao_mongo,
    salvar_candidatas_extracao,
)
from citizentech.curriculo.servico import CurriculoNaoLiberado, texto_liberado_para_llm
from citizentech.erros import NaoEncontrado
from citizentech.llm.cliente import ClienteLLM, ErroLLM, obter_cliente_llm

logger = logging.getLogger("citizentech.competencias")

router = APIRouter(prefix="/me/competencias", tags=["competencias"])

AVISO_EXTRACAO = (
    "Sugestões automáticas: confirme apenas o que você realmente faz. "
    "Declarar não é o mesmo que demonstrar."
)


@router.post(
    "/extrair",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(exigir_csrf)],
)
def extrair_competencias(
    payload: ExtrairCompetenciasRequisicao,
    usuario: Annotated[dict, Depends(obter_usuario_logado)],
    cliente_llm: Annotated[ClienteLLM, Depends(obter_cliente_llm)],
) -> dict[str, Any]:
    """Extrai competencias do curriculo atraves de LLM contra catalogo fechado."""
    usuario_id = usuario["id"]

    # 1. Verifica quota de 24h
    limite_quota = int(os.environ.get("CITIZENTECH_QUOTA_EXTRACAO_24H", "5"))
    total_24h = contar_extracoes_24h(usuario_id)
    if total_24h >= limite_quota:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "erro": "Limite de taxa excedido",
                "detalhes": f"Limite de {limite_quota} extracoes em 24h atingido.",
            },
        )

    # 2. Obtem texto liberado para LLM (D22)
    try:
        texto_redigido = texto_liberado_para_llm(usuario_id, payload.curriculo_id)
    except NaoEncontrado as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "erro": "Nao encontrado",
                "detalhes": exc.detalhes,
            },
        ) from exc
    except CurriculoNaoLiberado as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"erro": "Acesso negado", "detalhes": exc.detalhes},
        ) from exc

    # 3. Carrega catalogo fechado homologado
    catalogo = carregar_catalogo_competencias()
    lista_fechada = set(catalogo.keys())

    # 4. Constroi mensagens e schema para a LLM
    mensagens = construir_mensagens_extracao(texto_redigido, catalogo)
    schema = gerar_schema_extracao(lista_fechada)

    def _validar_raiz(dados: dict[str, Any]) -> None:
        if (
            not isinstance(dados, dict)
            or "competencias" not in dados
            or not isinstance(dados["competencias"], list)
        ):
            raise ValueError("Estrutura JSON raiz invalida retornado pela LLM.")

    # 5. Executa geracao estruturada pela LLM com retry/fallback
    try:
        resposta_llm = cliente_llm.gerar_json(
            mensagens=mensagens,
            schema=schema,
            nome_schema="extracao_competencias",
            validar=_validar_raiz,
        )
    except ErroLLM as exc:
        logger.warning("Falha na chamada LLM para extracao: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "erro": "Servico indisponivel",
                "detalhes": "Nao foi possivel obter resposta da LLM no momento.",
            },
        ) from exc

    # 6. Validacao deterministica local
    candidatas_validadas, descartadas = validar_saida_llm(
        resposta_llm.dados, lista_fechada, texto_redigido
    )

    # 7. Registra metadados no Mongo (sem texto e sem resposta bruta)
    sha256_texto = hashlib.sha256(texto_redigido.encode("utf-8")).hexdigest()
    extracao_id = registrar_extracao_mongo(
        usuario_id=usuario_id,
        curriculo_id=payload.curriculo_id,
        sha256_texto_redigido=sha256_texto,
        modelo=resposta_llm.modelo,
        tentativas=resposta_llm.tentativas,
        uso=resposta_llm.uso,
        contagem_candidatas=len(candidatas_validadas),
        descartadas=descartadas,
    )

    # 8. Persiste candidatas no Oracle (substitui pendentes do mesmo curriculo)
    candidatas_salvas = salvar_candidatas_extracao(
        usuario_id=usuario_id,
        curriculo_id=payload.curriculo_id,
        extracao_id=extracao_id,
        candidatas=candidatas_validadas,
        catalogo=catalogo,
    )

    logger.info(
        "Extracao concluida usuario_id=%s extracao_id=%s candidatas=%d modelo=%s",
        usuario_id,
        extracao_id,
        len(candidatas_salvas),
        resposta_llm.modelo,
    )

    return {
        "extracao_id": extracao_id,
        "modelo": resposta_llm.modelo,
        "candidatas": candidatas_salvas,
        "descartadas": descartadas,
        "aviso": AVISO_EXTRACAO,
    }


@router.get("")
def listar_competencias(
    usuario: Annotated[dict, Depends(obter_usuario_logado)],
) -> dict[str, Any]:
    """Lista as competencias do usuario logado."""
    catalogo = carregar_catalogo_competencias()
    itens = listar_competencias_usuario(usuario["id"], catalogo)
    return {"itens": itens}


@router.patch(
    "/{id}",
    dependencies=[Depends(exigir_csrf)],
)
def atualizar_competencia_rota(
    id: str,
    payload: AtualizarCompetenciaRequisicao,
    usuario: Annotated[dict, Depends(obter_usuario_logado)],
) -> dict[str, Any]:
    """Atualiza o estado de revisao de uma competencia do usuario."""
    catalogo = carregar_catalogo_competencias()
    atualizada = atualizar_competencia(
        comp_id=id,
        usuario_id=usuario["id"],
        acao=payload.acao,
        trecho_origem=payload.trecho_origem,
        catalogo=catalogo,
    )

    if atualizada is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "erro": "Nao encontrado",
                "detalhes": "Competencia nao encontrada ou nao pertence ao usuario.",
            },
        )

    return atualizada
