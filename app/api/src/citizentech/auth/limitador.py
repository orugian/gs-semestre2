"""Limitador de taxa em memoria para tentativas de login (D12, T16)."""

import threading
import time
from collections.abc import Callable

from fastapi import HTTPException, status


class LimitadorLogin:
    """Controlador de taxa de login com relogio injetavel e armazenamento em memoria."""

    def __init__(
        self,
        limite: int = 5,
        janela_segundos: int = 60,
        time_provider: Callable[[], float] = time.time,
    ) -> None:
        self.limite = limite
        self.janela_segundos = janela_segundos
        self.time_provider = time_provider
        self._historico: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def _purgar_expirados_bloqueado(self, agora: float) -> None:
        """Purga globalmente entradas com timestamps mais antigos que a janela.

        Deve ser chamado com self._lock adquirido.
        """
        limite_passado = agora - self.janela_segundos
        chaves_remover: list[str] = []
        for chave, tentativas in self._historico.items():
            validas = [t for t in tentativas if t > limite_passado]
            if not validas:
                chaves_remover.append(chave)
            else:
                self._historico[chave] = validas
        for chave in chaves_remover:
            del self._historico[chave]

    def purgar_expirados(self, agora: float | None = None) -> None:
        """Purga globalmente entradas expiradas (util para testes e manutencao)."""
        if agora is None:
            agora = self.time_provider()
        with self._lock:
            self._purgar_expirados_bloqueado(agora)

    def total_chaves_em_memoria(self) -> int:
        """Retorna a contagem atual de chaves rastreadas em memoria."""
        with self._lock:
            return len(self._historico)

    def verificar_e_registrar(self, chaves: list[str]) -> None:
        """Verifica atomicamente se alguma das chaves atingiu o limite.

        Se alguma excedeu, levanta HTTP 429 com cabecalho Retry-After.
        Se nenhuma excedeu, registra a tentativa em todas as chaves.
        """
        agora = self.time_provider()
        with self._lock:
            # Purga global de entradas expiradas para nao reter dados alem da janela
            self._purgar_expirados_bloqueado(agora)

            maior_retry_after = 0
            bloqueado = False

            for chave in chaves:
                lista = self._historico.get(chave, [])
                if len(lista) >= self.limite:
                    bloqueado = True
                    mais_antiga = lista[0]
                    espera = max(1, int(mais_antiga + self.janela_segundos - agora + 0.999))
                    if espera > maior_retry_after:
                        maior_retry_after = espera

            if bloqueado:
                # Nao cria nem registra chaves novas se a requisicao estiver bloqueada
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "erro": "Muitas requisicoes",
                        "detalhes": (
                            "Limite de tentativas de login excedido. "
                            "Tente novamente mais tarde."
                        ),
                    },
                    headers={"Retry-After": str(maior_retry_after)},
                )

            # Nao bloqueado: registra tentativa em todas as chaves fornecidas
            for chave in chaves:
                if chave not in self._historico:
                    self._historico[chave] = []
                self._historico[chave].append(agora)

    def resetar(self) -> None:
        """Limpa o historico em memoria (util para testes)."""
        with self._lock:
            self._historico.clear()


# Instancia padrao singleton para a aplicacao
limitador_login = LimitadorLogin()
