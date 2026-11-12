"""Aplicacao FastAPI. Na S0 existe apenas o health check."""

from fastapi import FastAPI

from citizentech.limiares import carregar_limiares

app = FastAPI(title="CitizenTech API", version="0.1.0")


@app.get("/health")
def health() -> dict:
    limiares = carregar_limiares()
    return {
        "status": "ok",
        "limiares": {
            "schema_version": limiares["schema_version"],
            "metricas": sorted(limiares["metricas"]),
        },
    }
