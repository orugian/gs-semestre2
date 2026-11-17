"""Ganchos opcionais da gravação de leituras.

O modo isolado (CTP) não tem banco nem laboratório: não registra gancho e o relato nunca é anexado.
A aplicação completa (`citizentech.main`) registra o gancho do laboratório, que anexa o relato
redigido da sessão ativa à primeira leitura gravada.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class GanchoRelato:
    buscar_pendente: Callable[[str], str | None]
    marcar_enviado: Callable[[str, str], bool]


_gancho: GanchoRelato | None = None


def registrar_gancho_relato(gancho: GanchoRelato | None) -> None:
    global _gancho
    _gancho = gancho


def gancho_relato() -> GanchoRelato | None:
    return _gancho
