"""Aplicacao FastAPI integrada com outbox e worker em segundo plano (S3)."""

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from citizentech.auth.rotas import router as auth_router
from citizentech.avaliacao.rotas import router as avaliacao_router
from citizentech.comparacao.rotas import router as comparacao_router
from citizentech.competencias.rotas import router as competencias_router
from citizentech.consentimentos.rotas import router as consentimentos_router
from citizentech.curriculo.rotas import router as curriculo_router
from citizentech.destinos.rotas import router as destinos_router
from citizentech.erros import registrar_manipuladores_de_erro
from citizentech.intencao.rotas import router as intencao_router
from citizentech.leituras.rotas import router as leituras_router
from citizentech.limiares import carregar_limiares
from citizentech.mercado.rotas import router as mercado_router
from citizentech.outbox.banco import reconciliar_com_csv
from citizentech.outbox.worker import GerenciadorWorkerOutbox
from citizentech.plano.rotas import router as plano_router

logger = logging.getLogger("citizentech.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # 1. Startup: reconcilia eventos orfaos do CSV com a outbox SQLite
    try:
        reconciliar_com_csv()
    except Exception as err:
        logger.warning("Falha na reconciliacao de startup: %s", type(err).__name__)

    # 2. Inicia worker em segundo plano apenas se FUNCTION_URL estiver configurada
    gerenciador: GerenciadorWorkerOutbox | None = None
    if os.environ.get("FUNCTION_URL"):
        gerenciador = GerenciadorWorkerOutbox()
        gerenciador.iniciar()

    yield

    # 3. Shutdown: encerra o worker de forma limpa e fecha cliente MongoDB
    if gerenciador:
        await gerenciador.parar()

    try:
        from citizentech.curriculo.repositorio import fechar_cliente_mongo

        fechar_cliente_mongo()
    except Exception:
        pass


def criar_app() -> FastAPI:
    aplicacao = FastAPI(title="CitizenTech API", version="0.1.0", lifespan=lifespan)
    registrar_manipuladores_de_erro(aplicacao)
    aplicacao.include_router(leituras_router)
    aplicacao.include_router(auth_router)
    aplicacao.include_router(consentimentos_router)
    aplicacao.include_router(mercado_router)
    aplicacao.include_router(curriculo_router)
    aplicacao.include_router(competencias_router)
    aplicacao.include_router(intencao_router)
    aplicacao.include_router(destinos_router)
    aplicacao.include_router(comparacao_router)
    aplicacao.include_router(plano_router)
    aplicacao.include_router(avaliacao_router)

    @aplicacao.get("/health")
    def health() -> dict:
        limiares = carregar_limiares()
        return {
            "status": "ok",
            "limiares": {
                "schema_version": limiares["schema_version"],
                "metricas": sorted(limiares["metricas"]),
            },
        }

    return aplicacao


app = criar_app()
