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


class ConflitoEvento(ValueError):
    """Conflito de evento_id com payload divergente."""

    def __init__(self, detalhes: str) -> None:
        super().__init__(detalhes)
        self.detalhes = detalhes


class Conflito(Exception):
    """Conflito de estado ou concorrencia de recursos."""

    def __init__(self, detalhes: str, erro: str = "Conflito") -> None:
        super().__init__(detalhes)
        self.detalhes = detalhes
        self.erro = erro


class RequisicaoInvalida(Exception):
    """Requisicao invalida por regra de negocio do dominio."""

    def __init__(self, detalhes: str, erro: str = "Requisicao invalida") -> None:
        super().__init__(detalhes)
        self.detalhes = detalhes
        self.erro = erro


class ErroInterno(Exception):
    """Erro interno no servidor."""

    def __init__(
        self,
        detalhes: str = "Erro interno no servidor.",
        erro: str = "Erro interno",
    ) -> None:
        super().__init__(detalhes)
        self.detalhes = detalhes
        self.erro = erro


class ErroBancoIndisponivel(RuntimeError):
    """Erro de conexao ou indisponibilidade do banco Oracle."""

    def __init__(
        self, detalhes: str = "Falha na comunicacao com o banco de dados."
    ) -> None:
        super().__init__(detalhes)
        self.detalhes = detalhes


class ErroSegurancaIndisponivel(RuntimeError):
    """Erro de configuracao de seguranca (ex: JWT_SECRET ausente ou curto)."""

    def __init__(
        self, detalhes: str = "Configuracao de seguranca ausente ou invalida."
    ) -> None:
        super().__init__(detalhes)
        self.detalhes = detalhes


class NaoEncontrado(Exception):
    """Recurso nao encontrado no dominio."""

    def __init__(
        self,
        detalhes: str = "Recurso nao encontrado.",
        erro: str = "Nao encontrado",
    ) -> None:
        super().__init__(detalhes)
        self.detalhes = detalhes
        self.erro = erro


class ConsentimentoAusente(Exception):
    """Consentimento obrigatorio ausente ou revogado para a operacao."""

    def __init__(
        self,
        detalhes: str,
        erro: str = "Consentimento necessario",
    ) -> None:
        super().__init__(detalhes)
        self.detalhes = detalhes
        self.erro = erro


class LimiteExcedido(Exception):
    """Limite de taxa ou cota excedido."""

    def __init__(
        self,
        detalhes: str,
        erro: str = "Limite de taxa excedido",
    ) -> None:
        super().__init__(detalhes)
        self.detalhes = detalhes
        self.erro = erro


class ServicoIndisponivel(RuntimeError):
    """Servico externo ou recurso necessario indisponivel."""

    def __init__(
        self,
        detalhes: str = "Servico indisponivel no momento.",
        erro: str = "Servico indisponivel",
    ) -> None:
        super().__init__(detalhes)
        self.detalhes = detalhes
        self.erro = erro


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

    @app.exception_handler(RequisicaoInvalida)
    async def manipulador_requisicao_invalida(
        request: Request,
        exc: RequisicaoInvalida,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "erro": exc.erro,
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

    @app.exception_handler(ConflitoEvento)
    async def manipulador_conflito_evento(
        request: Request,
        exc: ConflitoEvento,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "erro": "Conflito",
                "detalhes": exc.detalhes,
            },
        )

    @app.exception_handler(Conflito)
    async def manipulador_conflito(
        request: Request,
        exc: Conflito,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "erro": exc.erro,
                "detalhes": exc.detalhes,
            },
        )

    @app.exception_handler(ErroBancoIndisponivel)
    async def manipulador_banco(
        request: Request,
        exc: ErroBancoIndisponivel,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "erro": "Servico indisponivel",
                "detalhes": exc.detalhes,
            },
        )

    @app.exception_handler(ErroSegurancaIndisponivel)
    async def manipulador_seguranca(
        request: Request,
        exc: ErroSegurancaIndisponivel,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "erro": "Servico indisponivel",
                "detalhes": exc.detalhes,
            },
        )

    @app.exception_handler(NaoEncontrado)
    async def manipulador_nao_encontrado(
        request: Request,
        exc: NaoEncontrado,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "erro": exc.erro,
                "detalhes": exc.detalhes,
            },
        )

    @app.exception_handler(ConsentimentoAusente)
    async def manipulador_consentimento(
        request: Request,
        exc: ConsentimentoAusente,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "erro": exc.erro,
                "detalhes": exc.detalhes,
            },
        )

    @app.exception_handler(LimiteExcedido)
    async def manipulador_limite(
        request: Request,
        exc: LimiteExcedido,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "erro": exc.erro,
                "detalhes": exc.detalhes,
            },
        )

    @app.exception_handler(ServicoIndisponivel)
    async def manipulador_servico_indisponivel(
        request: Request,
        exc: ServicoIndisponivel,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "erro": exc.erro,
                "detalhes": exc.detalhes,
            },
        )

    @app.exception_handler(ErroInterno)
    async def manipulador_erro_interno(
        request: Request,
        exc: ErroInterno,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "erro": exc.erro,
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
            headers=exc.headers,
        )
