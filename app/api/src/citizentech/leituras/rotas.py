"""Rotas de telemetria CTP."""

import json
import math
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse

from citizentech.erros import ConflitoEvento
from citizentech.leituras.esquemas import validar_e_processar_payload
from citizentech.leituras.limitador import obter_limitador
from citizentech.leituras.repositorio import (
    ler_todas_leituras,
    salvar_leitura_duravel,
)
from citizentech.leituras.seguranca import verificar_chave_dispositivo
from citizentech.limiares import carregar_limiares
from citizentech.outbox.banco import obter_mapa_estados

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

    # 4.1. Gancho de sessao de laboratorio: se sessao_laboratorio_id preenchido e existir
    # sessao ativa nao expirada com relato pendente, anexa relato redigido
    sessao_cod = registro.get("sessao_laboratorio_id")
    relato_para_anexar: str | None = None
    if sessao_cod:
        try:
            from citizentech.laboratorio.repositorio import buscar_relato_pendente_sessao_ativa

            relato_para_anexar = buscar_relato_pendente_sessao_ativa(sessao_cod)
            if relato_para_anexar:
                registro["relato_redigido"] = relato_para_anexar
        except Exception:
            pass

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
    if resultado == "criado" and relato_para_anexar and sessao_cod:
        try:
            from citizentech.laboratorio.repositorio import marcar_relato_enviado

            marcar_relato_enviado(sessao_cod, reg_final["evento_id"])
        except Exception:
            pass

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

    todos = ler_todas_leituras()
    mapa_estados = obter_mapa_estados()
    if mapa_estados:
        for r in todos:
            if r["evento_id"] in mapa_estados:
                r["estado"] = mapa_estados[r["evento_id"]]

    if sessao is not None and sessao != "":
        todos = [r for r in todos if r["sessao_laboratorio_id"] == sessao]

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


def calcular_indicadores(leituras: list[dict[str, Any]]) -> dict[str, Any]:
    """Calcula indicadores estatisticos sobre uma lista de leituras."""
    contagem = len(leituras)
    if contagem == 0:
        return {
            "contagem": 0,
            "total_alertas": 0,
            "media": None,
            "maximo": None,
            "minimo": None,
        }
    valores = [r["valor"] for r in leituras]
    total_alertas = sum(1 for r in leituras if r.get("alerta") is True)

    # Media estavel (evita overflow de soma intermediaria com valores extremos)
    media = 0.0
    for i, v in enumerate(valores, start=1):
        media += (v - media) / i

    val_max = max(valores)
    val_min = min(valores)

    if not math.isfinite(media) or not math.isfinite(val_max) or not math.isfinite(val_min):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "erro": "Erro no calculo de indicadores",
                "detalhes": "Overflow numerico no calculo de estatisticas dos valores.",
            },
        )

    try:
        media_arredondada = round(media, 2)
        max_arredondado = round(val_max, 2)
        min_arredondado = round(val_min, 2)
    except OverflowError:
        media_arredondada = media
        max_arredondado = val_max
        min_arredondado = val_min

    return {
        "contagem": contagem,
        "total_alertas": total_alertas,
        "media": media_arredondada,
        "maximo": max_arredondado,
        "minimo": min_arredondado,
    }


def _calcular_estatisticas(leituras: list[dict[str, Any]]) -> dict[str, Any]:
    return calcular_indicadores(leituras)


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

    todos = ler_todas_leituras()
    if sessao is not None and sessao != "":
        todos = [r for r in todos if r["sessao_laboratorio_id"] == sessao]

    if metrica is not None and metrica != "":
        filtradas = [r for r in todos if r["metrica"] == metrica]
        stats = _calcular_estatisticas(filtradas)
        return {
            "sessao": sessao,
            "metrica": metrica,
            **stats,
        }

    resultado_metricas: dict[str, Any] = {}
    for m in sorted(catalogo.keys()):
        filtradas = [r for r in todos if r["metrica"] == m]
        resultado_metricas[m] = _calcular_estatisticas(filtradas)

    return {
        "sessao": sessao,
        "metricas": resultado_metricas,
    }
