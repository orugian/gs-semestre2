"""Aplicacao FastAPI em modo isolado CTP (sem Oracle e sem Mongo)."""

from fastapi import FastAPI

from citizentech.erros import registrar_manipuladores_de_erro
from citizentech.leituras.rotas import router as leituras_router

app = FastAPI(title="CitizenTech API (Modo Isolado CTP)", version="0.1.0")
registrar_manipuladores_de_erro(app)
app.include_router(leituras_router)
