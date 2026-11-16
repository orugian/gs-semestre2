"""Aplicacao FastAPI em modo isolado CTP (sem Oracle e sem Mongo).

Nao inicia o worker da outbox (nao ha nuvem neste modo), mas reconcilia no startup os
eventos que ficaram no CSV sem entrada na outbox depois de uma queda.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from citizentech.erros import registrar_manipuladores_de_erro
from citizentech.leituras.rotas import router as leituras_router
from citizentech.outbox.banco import reconciliar_com_csv

logger = logging.getLogger("citizentech.leituras.isolado")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    try:
        reconciliar_com_csv()
    except Exception as err:
        logger.warning("Falha na reconciliacao de startup: %s", type(err).__name__)
    yield


app = FastAPI(title="CitizenTech API (Modo Isolado CTP)", version="0.1.0", lifespan=lifespan)
registrar_manipuladores_de_erro(app)
app.include_router(leituras_router)