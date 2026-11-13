"""Tratamento padronizado de erros da API CitizenTech.

Garante que erros retornem no formato {"erro": ..., "detalhes": ...},
sem nunca expor HTTP 422 nem vazar dados sensiveis ou payloads brutos.
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErroValidacaoLeitura(ValueError):
    """Erro de validacao nas regras de negocio de leitura de telemetria."""

    def __init__(self, detalhes: str) -> None:
        super().__init__(detalhes)
        self.detalhes = detalhes


class ErroArmazenamento(RuntimeError):
    """Erro irrecuperavel na gravacao ou leitura duravel do CSV."""

    def __init__(self, detalhes: str) -> None:
        super().__init__(detalhes)
        self.detalhes = detalhes


def registrar_manipuladores_de_erro(app: FastAPI) -> None:
    """Registra manipuladores de erro globais para assegurar o contrato de respostas."""

    @app.exception_handler(RequestValidationError)
    async def manipulador_validacao_pydantic(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "erro": "Requisicao invalida",
                "detalhes": (
                    "Os dados enviados nao atendem ao esquema esperado ou estao malformados."
                ),
            },
        )

    @app.exception_handler(ErroValidacaoLeitura)
    async def manipulador_validacao_leitura(
        request: Request,
        exc: ErroValidacaoLeitura,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "erro": "Requisicao invalida",
                "detalhes": exc.detalhes,
            },
        )

    @app.exception_handler(ErroArmazenamento)
    async def manipulador_armazenamento(
        request: Request,
        exc: ErroArmazenamento,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "erro": "Servico indisponivel",
                "detalhes": exc.detalhes,
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def manipulador_http_exception(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        if isinstance(exc.detail, dict) and "erro" in exc.detail:
            conteudo = exc.detail
        else:
            conteudo = {
                "erro": "Erro na requisicao",
                "detalhes": str(exc.detail),
            }
        return JSONResponse(
            status_code=exc.status_code,
            content=conteudo,
        )
