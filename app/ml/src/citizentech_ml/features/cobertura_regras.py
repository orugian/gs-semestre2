"""Regras de validação de cobertura do Novo Caged para evitar falsos zeros."""

from __future__ import annotations

import pandas as pd

from citizentech_ml.features.datas import (
    gerar_intervalo_meses,
    mes_para_int,
    validar_competencia,
)

SITUACOES_VALIDAS_REVISAO: set[str] = {"ingerido", "ausente_na_fonte"}


def validar_cobertura_sem_conflitos(df_cobertura: pd.DataFrame) -> None:
    """Verifica se existem duplicatas conflitantes no DataFrame de cobertura.

    Gera ValueError se para a mesma competência e tipo houver situações divergentes.
    """
    if df_cobertura.empty:
        return

    colunas = {"competencia", "tipo", "situacao"}
    if not colunas.issubset(df_cobertura.columns):
        raise ValueError(
            f"DataFrame de cobertura deve conter as colunas: {sorted(colunas)}"
        )

    # Agrupa por competência e tipo normalizados
    df_temp = pd.DataFrame({
        "competencia": df_cobertura["competencia"].astype(str).str.strip(),
        "tipo": df_cobertura["tipo"].astype(str).str.strip().str.upper(),
        "situacao": df_cobertura["situacao"].astype(str).str.strip().str.lower(),
    })

    duplicatas = (
        df_temp.groupby(["competencia", "tipo"])["situacao"]
        .nunique()
        .reset_index()
    )
    conflitos = duplicatas[duplicatas["situacao"] > 1]
    if not conflitos.empty:
        primeiro = conflitos.iloc[0]
        raise ValueError(
            f"Conflito de situações de cobertura detectado para a competência "
            f"'{primeiro['competencia']}' e tipo '{primeiro['tipo']}'."
        )


def _obter_mapa_situacoes(df_cobertura: pd.DataFrame) -> dict[tuple[str, str], str]:
    """Retorna mapa {(competencia, tipo): situacao} normalizado."""
    validar_cobertura_sem_conflitos(df_cobertura)
    mapa: dict[tuple[str, str], str] = {}
    for _, row in df_cobertura.iterrows():
        comp_val = validar_competencia(str(row["competencia"]))
        tipo_val = str(row["tipo"]).strip().upper()
        sit_val = str(row["situacao"]).strip().lower()
        mapa[(comp_val, tipo_val)] = sit_val
    return mapa


def verificar_mes_coberto(df_cobertura: pd.DataFrame, mes: str) -> bool:
    """Verifica se um determinado mês possui observação inicial completa na fonte.

    Regras estritas (D04b / Aceite S7):
    - MOV deve estar explicitamente presente e ter situacao == 'ingerido'.
    - FOR deve estar explicitamente presente e ter situacao in {'ingerido', 'ausente_na_fonte'}.
    - EXC deve estar explicitamente presente e ter situacao in {'ingerido', 'ausente_na_fonte'}.
    - Se qualquer um dos três tipos estiver ausente do manifesto ou possuir outra situação
      (ex: 'nao_promovida', 'falha', 'pendente', 'desconhecida'), o mês NÃO é coberto.
    """
    mes_val = validar_competencia(mes)
    mapa = _obter_mapa_situacoes(df_cobertura)

    # 1. MOV deve ser 'ingerido'
    if mapa.get((mes_val, "MOV")) != "ingerido":
        return False

    # 2. FOR e EXC devem estar explicitamente presentes e válidos
    for tipo_extra in ["FOR", "EXC"]:
        sit = mapa.get((mes_val, tipo_extra))
        if sit not in SITUACOES_VALIDAS_REVISAO:
            return False

    return True


def verificar_observacao_completa_as_of(
    df_cobertura: pd.DataFrame,
    mes_mov: str,
    as_of: str,
) -> bool:
    """Valida se a contagem do mês de movimento m é completamente conhecida no momento as-of t.

    Regras estritas (D04b / R02 / T05 / T18 / Aceite S7):
    - Para contagem em mês m e origem t, validar:
      1. MOV m deve ser 'ingerido'.
      2. Revisões FOR e EXC em TODO o intervalo m..t devem estar completas
         (situacao in {'ingerido', 'ausente_na_fonte'}).
    - Lacuna antes de m NÃO afeta m.
    - Falhas ou pendências no futuro > t NÃO alteram o passado (não afetam t).
    """
    m_val = validar_competencia(mes_mov)
    t_val = validar_competencia(as_of)

    if mes_para_int(m_val) > mes_para_int(t_val):
        return False

    mapa = _obter_mapa_situacoes(df_cobertura)

    # MOV do próprio mês de movimento m deve ser 'ingerido'
    if mapa.get((m_val, "MOV")) != "ingerido":
        return False

    # Revisões FOR e EXC de todo o intervalo m..t devem estar completas
    intervalo = gerar_intervalo_meses(m_val, t_val)
    for k in intervalo:
        for tipo in ["FOR", "EXC"]:
            sit = mapa.get((k, tipo))
            if sit not in SITUACOES_VALIDAS_REVISAO:
                return False

    return True


def obter_mapa_cobertura(df_cobertura: pd.DataFrame, meses: list[str]) -> dict[str, bool]:
    """Retorna mapa {mes: booleano} indicando se cada mês possui observação inicial completa."""
    return {m: verificar_mes_coberto(df_cobertura, m) for m in meses}

