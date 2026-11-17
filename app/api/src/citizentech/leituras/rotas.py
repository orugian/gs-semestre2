"""Rotas de telemetria CTP."""

import json
import logging
import math
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse

from citizentech.erros import ConflitoEvento
from citizentech.leituras.esquemas import validar_e_processar_payload
from citizentech.leituras.ganchos import gancho_relato
from citizentech.leituras.limitador import obter_limitador
from citizentech.leituras.repositorio import salvar_leitura_duravel
from citizentech.leituras.seguranca import verificar_chave_dispositivo
from citizentech.leituras.servico import (
    calcular_indicadores,
    listar_leituras_com_estado,
)
from citizentech.limiares import carregar_limiares

logger = logging.getLogger(__name__)

router = APIRouter()

LIMITE_PAYLOAD_BYTES = 8192


async def _ler_corpo_com_limite(request: Request, limite: int = LIMITE_PAYLOAD_BYTES) -> bytes:
    tamanho_header = request.headers.get("content-length")
    if tamanho_header:
        try:
            if int(tamanho_header) > limite:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "erro": "Requisicao invalida",
                        "detalhes": "Tamanho da requisicao excede o limite de 8KB.",
                    },
                )
        except ValueError:
            pass

    pedacos: list[bytes] = []
    total = 0
    async for pedaco in request.stream():
        total += len(pedaco)
        if total > limite:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "erro": "Requisicao invalida",
                    "detalhes": "Tamanho da requisicao excede o limite de 8KB.",
                },
            )
        pedacos.append(pedaco)
    return b"".join(pedacos)


@router.post("/leituras", status_code=status.HTTP_201_CREATED)
async def criar_leitura(
    request: Request,
    _chave: str = Depends(verificar_chave_dispositivo),
) -> JSONResponse:
    # 1. Validacao de tamanho consumindo stream sob demanda (com ou sem Content-Length)
    corpo_bytes = await _ler_corpo_com_limite(request, LIMITE_PAYLOAD_BYTES)

    # 2. Rejeita JSON malformado
    try:
        dados_brutos = json.loads(corpo_bytes.decode("utf-8"))
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "erro": "Requisicao invalida",
                "detalhes": "JSON malformado ou encoding invalido.",
            },
        ) from err

    # 3. Validacao das regras de negocio e computacao de risco
    registro = validar_e_processar_payload(dados_brutos)

    # 4. Rate limit por dispositivo
    limitador = obter_limitador()
    if not limitador.requisicao_permitida(registro["dispositivo_id"]):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "erro": "Muitas requisicoes",
                "detalhes": "Limite de requisicoes excedido para o dispositivo.",
            },
        )

    # 4.1. Sessao de laboratorio com relato pendente: anexa o relato redigido (so na app completa)
    sessao_cod = registro.get("sessao_laboratorio_id")
    gancho = gancho_relato()
    relato_para_anexar: str | None = None
    if sessao_cod and gancho:
        try:
            relato_para_anexar = gancho.buscar_pendente(sessao_cod)
            if relato_para_anexar:
                registro["relato_redigido"] = relato_para_anexar
        except Exception as exc:
            logger.warning("Falha ao buscar relato pendente para sessao: %s", type(exc).__name__)

    # 5. Persistencia duravel em CSV e Outbox SQLite
    try:
        resultado, reg_final = salvar_leitura_duravel(registro)
    except ConflitoEvento as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "erro": "Conflito",
                "detalhes": str(err),
            },
        ) from err

    # 5.1. Se leitura foi gravada como nova (criado) e havia relato anexado,
    # marca relato como enviado no banco de dados
    if resultado == "criado" and relato_para_anexar and sessao_cod and gancho:
        try:
            gancho.marcar_enviado(sessao_cod, reg_final["evento_id"])
        except Exception as exc:
            logger.warning("Falha ao marcar relato como enviado: %s", type(exc).__name__)

    codigo_status = (
        status.HTTP_201_CREATED if resultado == "criado" else status.HTTP_200_OK
    )

    # 6. Resposta conforme contrato (201 novo, 200 reenvio identico)
    return JSONResponse(
        status_code=codigo_status,
        content={
            "evento_id": reg_final["evento_id"],
            "dispositivo_id": reg_final["dispositivo_id"],
            "metrica": reg_final["metrica"],
            "unidade": reg_final["unidade"],
            "valor": reg_final["valor"],
            "risco": reg_final["risco"],
            "alerta": reg_final["alerta"],
            "estado": reg_final["estado"],
            "medido_em": reg_final["medido_em"],
        },
    )


@router.get("/leituras")
def listar_leituras(
    sessao: str | None = Query(None, alias="sessao"),
    page: int = Query(1, alias="page"),
    page_size: int = Query(20, alias="page_size"),
    _chave: str = Depends(verificar_chave_dispositivo),
) -> dict[str, Any]:
    if page < 1 or page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "erro": "Requisicao invalida",
                "detalhes": (
                    "Parametros de paginacao invalidos (page >= 1, 1 <= page_size <= 100)."
                ),
            },
        )

    todos = listar_leituras_com_estado(sessao=sessao)

    total = len(todos)
    inicio = (page - 1) * page_size
    fim = inicio + page_size
    itens = todos[inicio:fim]
    total_paginas = math.ceil(total / page_size) if total > 0 else 0

    return {
        "itens": itens,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_paginas": total_paginas,
    }


@router.get("/leituras/indicadores")
def obter_indicadores(
    sessao: str | None = Query(None, alias="sessao"),
    metrica: str | None = Query(None, alias="metrica"),
    _chave: str = Depends(verificar_chave_dispositivo),
) -> dict[str, Any]:
    limiares = carregar_limiares()
    catalogo = limiares.get("metricas", {})

    if metrica is not None and metrica != "":
        if metrica not in catalogo:
            conhecidas = ", ".join(sorted(catalogo.keys()))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "erro": "Requisicao invalida",
                    "detalhes": (
                        f"Metrica desconhecida. Metricas conhecidas: {conhecidas}."
                    ),
                },
            )

    todos = listar_leituras_com_estado(sessao=sessao)

    if metrica is not None and metrica != "":
        filtradas = [r for r in todos if r["metrica"] == metrica]
        stats = calcular_indicadores(filtradas)
        return {
            "sessao": sessao,
            "metrica": metrica,
            **stats,
        }

    resultado_metricas: dict[str, Any] = {}
    for m in sorted(catalogo.keys()):
        filtradas = [r for r in todos if r["metrica"] == m]
        resultado_metricas[m] = calcular_indicadores(filtradas)

    return {
        "sessao": sessao,
        "metricas": resultado_metricas,
    }
