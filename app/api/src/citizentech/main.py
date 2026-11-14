"""Aplicacao FastAPI integrada com outbox e worker em segundo plano (S3)."""

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from citizentech.erros import registrar_manipuladores_de_erro
from citizentech.leituras.rotas import router as leituras_router
from citizentech.limiares import carregar_limiares
from citizentech.outbox.banco import reconciliar_com_csv
from citizentech.outbox.worker import GerenciadorWorkerOutbox

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

    # 3. Shutdown: encerra o worker de forma limpa
    if gerenciador:
        await gerenciador.parar()


def criar_app() -> FastAPI:
    aplicacao = FastAPI(title="CitizenTech API", version="0.1.0", lifespan=lifespan)
    registrar_manipuladores_de_erro(aplicacao)
    aplicacao.include_router(leituras_router)

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
