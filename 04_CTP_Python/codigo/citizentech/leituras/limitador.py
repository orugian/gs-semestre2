"""Limitador de taxa (rate limiter) por dispositivo com relogio injetavel."""

import os
import threading
import time
from collections import defaultdict
from collections.abc import Callable


class LimitadorTaxa:
    def __init__(
        self,
        teto_por_minuto: int | None = None,
        relogio: Callable[[], float] | None = None,
    ) -> None:
        self._teto_padrao = teto_por_minuto
        self._relogio = relogio or time.time
        self._historico: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def _obter_teto(self) -> int:
        if self._teto_padrao is not None:
            return self._teto_padrao
        env_val = os.environ.get("CITIZENTECH_RATE_LIMIT_POR_MINUTO")
        if env_val:
            try:
                return int(env_val)
            except ValueError:
                pass
        return 60

    def definir_relogio(self, relogio: Callable[[], float]) -> None:
        with self._lock:
            self._relogio = relogio

    def definir_teto(self, teto: int | None) -> None:
        with self._lock:
            self._teto_padrao = teto

    def limpar(self) -> None:
        with self._lock:
            self._historico.clear()

    def requisicao_permitida(self, dispositivo_id: str) -> bool:
        teto = self._obter_teto()
        agora = self._relogio()
        janela = agora - 60.0

        with self._lock:
            timestamps = self._historico[dispositivo_id]
            # Remove requisicoes anteriores a janela de 1 minuto
            validados = [ts for ts in timestamps if ts > janela]
            if len(validados) >= teto:
                self._historico[dispositivo_id] = validados
                return False
            validados.append(agora)
            self._historico[dispositivo_id] = validados
            return True


_LIMITADOR_PADRAO = LimitadorTaxa()


def obter_limitador() -> LimitadorTaxa:
    return _LIMITADOR_PADRAO
