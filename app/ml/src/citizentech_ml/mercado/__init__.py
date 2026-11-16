"""Módulo de exportação de snapshot de mercado e métricas técnicas."""

from typing import Any

__all__ = ["exportar_snapshot_mercado", "normalizar_resumo_cv"]


def __getattr__(name: str) -> Any:
    if name in __all__:
        import citizentech_ml.mercado.exportar as exp

        return getattr(exp, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

