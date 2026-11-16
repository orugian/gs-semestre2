"""Worker em segundo plano para despacho da outbox (Plano §2, D12a/R25)."""

import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from citizentech.outbox.banco import (
    atualizar_status_pendencia,
    listar_pendencias_para_envio,
)
from citizentech.outbox.cliente import ClienteLambda

logger = logging.getLogger("citizentech.outbox")


def calcular_proxima_tentativa(
    agora: datetime,
    tentativas: int,
    base_segundos: float = 1.0,
    max_segundos: float = 60.0,
) -> str:
    """Calcula backoff exponencial limitado para retries."""
    fator = 2 ** max(0, tentativas - 1)
    intervalo = min(max_segundos, base_segundos * fator)
    proxima = agora + timedelta(seconds=intervalo)
    return proxima.strftime("%Y-%m-%dT%H:%M:%SZ")


def processar_pendencias_uma_vez(
    limite: int = 50,
    cliente: ClienteLambda | None = None,
    relogio: Callable[[], datetime] | None = None,
    caminho_db: Path | None = None,
    base_backoff_segundos: float = 1.0,
    max_backoff_segundos: float = 60.0,
) -> int:
    """Processa uma iteracao de pendencias da outbox com cliente e relogio injetaveis."""
    if relogio is None:
        relogio = lambda: datetime.now(UTC)  # noqa: E731
    agora_dt = relogio()
    agora_iso = agora_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    if cliente is None:
        cliente = ClienteLambda()

    itens = listar_pendencias_para_envio(limite=limite, agora=agora_iso, caminho=caminho_db)
    processados = 0

    for item in itens:
        evento_id = item["evento_id"]
        payload = item["payload"]
        tentativas = item["tentativas"] + 1

        resultado = cliente.enviar_leitura(payload)

        if resultado.sucesso:
            atualizar_status_pendencia(
                evento_id=evento_id,
                estado="sincronizado",
                tentativas=tentativas,
                proxima_tentativa_em=agora_iso,
                ultimo_erro=None,
                caminho=caminho_db,
            )
        elif resultado.estado_final == "conflito":
            atualizar_status_pendencia(
                evento_id=evento_id,
                estado="conflito",
                tentativas=tentativas,
                proxima_tentativa_em=agora_iso,
                ultimo_erro=resultado.codigo_erro,
                caminho=caminho_db,
            )
        elif resultado.estado_final == "erro_permanente":
            atualizar_status_pendencia(
                evento_id=evento_id,
                estado="erro_permanente",
                tentativas=tentativas,
                proxima_tentativa_em=agora_iso,
                ultimo_erro=resultado.codigo_erro,
                caminho=caminho_db,
            )
        else:
            # Erro transitorio (5xx, timeout, conexao recusada, rate limit, envelope invalido)
            proxima_iso = calcular_proxima_tentativa(
                agora=relogio(),
                tentativas=tentativas,
                base_segundos=base_backoff_segundos,
                max_segundos=max_backoff_segundos,
            )
            atualizar_status_pendencia(
                evento_id=evento_id,
                estado="pendente_nuvem",
                tentativas=tentativas,
                proxima_tentativa_em=proxima_iso,
                ultimo_erro=resultado.codigo_erro,
                caminho=caminho_db,
            )

        processados += 1

    return processados


class GerenciadorWorkerOutbox:
    """Controla o ciclo de vida do worker assincrono dentro do processo da API."""

    def __init__(
        self,
        intervalo_pesquisa: float = 2.0,
        cliente: ClienteLambda | None = None,
        caminho_db: Path | None = None,
    ) -> None:
        self.intervalo_pesquisa = intervalo_pesquisa
        self.cliente = cliente
        self.caminho_db = caminho_db
        self._tarefa: asyncio.Task[Any] | None = None
        self._parar_evento = asyncio.Event()

    async def _loop_execucao(self) -> None:
        loop = asyncio.get_running_loop()
        while not self._parar_evento.is_set():
            try:
                await loop.run_in_executor(
                    None,
                    processar_pendencias_uma_vez,
                    50,
                    self.cliente,
                    None,
                    self.caminho_db,
                )
            except Exception as err:
                logger.warning("Falha nao fatal na iteracao da outbox: %s", type(err).__name__)

            try:
                await asyncio.wait_for(self._parar_evento.wait(), timeout=self.intervalo_pesquisa)
            except TimeoutError:
                pass

    def iniciar(self) -> None:
        if self._tarefa is None or self._tarefa.done():
            self._parar_evento.clear()
            self._tarefa = asyncio.create_task(self._loop_execucao())

    async def parar(self) -> None:
        self._parar_evento.set()
        if self._tarefa and not self._tarefa.done():
            self._tarefa.cancel()
            try:
                await self._tarefa
            except asyncio.CancelledError:
                pass
            self._tarefa = None
