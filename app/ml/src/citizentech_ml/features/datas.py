"""Manipulação e validação estrita de competências mensais (YYYYMM)."""

from __future__ import annotations


def validar_competencia(comp: str) -> str:
    """Valida se uma competência possui formato YYYYMM rigoroso (ano 1900..2100, mês 01..12).

    Gera ValueError explícito caso seja inválida, nula ou fora dos limites.
    """
    if not isinstance(comp, str):
        raise ValueError(f"Competência deve ser string, recebido {type(comp)}: {comp!r}")
    comp_limpa = comp.strip()
    if len(comp_limpa) != 6 or not comp_limpa.isdigit():
        raise ValueError(
            f"Competência inválida: {comp!r}. Deve conter exatamente 6 dígitos numéricos (YYYYMM)."
        )
    ano = int(comp_limpa[:4])
    mes = int(comp_limpa[4:])
    if not (1900 <= ano <= 2100):
        raise ValueError(f"Ano fora dos limites razoáveis (1900..2100): {ano} em {comp!r}")
    if not (1 <= mes <= 12):
        raise ValueError(f"Mês inválido (deve ser 01..12): {mes} em {comp!r}")
    return comp_limpa


def mes_para_int(comp: str) -> int:
    """Converte competência YYYYMM para índice numérico contínuo de meses."""
    comp_val = validar_competencia(comp)
    ano = int(comp_val[:4])
    mes = int(comp_val[4:])
    return ano * 12 + (mes - 1)


def int_para_mes(idx: int) -> str:
    """Converte índice numérico contínuo de meses para YYYYMM."""
    ano = idx // 12
    mes = (idx % 12) + 1
    return f"{ano:04d}{mes:02d}"


def deslocar_mes(comp: str, n_meses: int) -> str:
    """Desloca competência YYYYMM por n meses (positivo para futuro, negativo para passado)."""
    idx = mes_para_int(comp) + n_meses
    return int_para_mes(idx)


def diferenca_meses(comp1: str, comp2: str) -> int:
    """Retorna a diferença em meses entre comp1 e comp2 (comp2 - comp1)."""
    return mes_para_int(comp2) - mes_para_int(comp1)


def gerar_intervalo_meses(inicio: str, fim: str) -> list[str]:
    """Gera lista sequencial de competências de inicio até fim (inclusive)."""
    idx_inicio = mes_para_int(inicio)
    idx_fim = mes_para_int(fim)
    if idx_inicio > idx_fim:
        raise ValueError(f"Competência inicial {inicio} posterior à final {fim}")
    return [int_para_mes(i) for i in range(idx_inicio, idx_fim + 1)]
