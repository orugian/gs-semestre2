"""Modulo de gestao de consentimentos (LGPD) da API CitizenTech."""

from citizentech.consentimentos.dependencias import exigir_consentimento, validar_consentimento

__all__ = ["exigir_consentimento", "validar_consentimento"]
