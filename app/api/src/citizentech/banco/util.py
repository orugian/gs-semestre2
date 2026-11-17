"""Utilidades compartilhadas de persistencia e formatacao para repositorios."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta, timezone
from typing import Any

# Fuso horario de Sao Paulo (UTC-3)
SAO_PAULO = timezone(timedelta(hours=-3))


def iso_utc(dt: Any) -> str | None:
    """Garante formatacao UTC ISO-8601 com sufixo 'Z'."""
    if dt is None:
        return None
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        else:
            dt = dt.astimezone(UTC)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return str(dt)


def agora_iso() -> str:
    """Retorna o instante atual em UTC ISO-8601 com 'Z'."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def deserializar_json(valor: Any) -> Any:
    """Converte valor do banco (objeto nativo, LOB ou str) em objeto Python."""
    if isinstance(valor, (dict, list)):
        return valor
    if hasattr(valor, "read"):
        valor = valor.read()
    if isinstance(valor, (bytes, bytearray)):
        valor = valor.decode("utf-8")
    if isinstance(valor, str):
        return json.loads(valor)
    return valor
