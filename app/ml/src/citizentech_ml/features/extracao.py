"""Extração de features temporais as-of e cálculo de alvos consolidados."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from citizentech_ml.features.agregador import (
    UFS_BRASIL,
    agregar_meses_as_of,
    extrair_mapa_cbo,
    pre_agregar_microdados,
)
from citizentech_ml.features.datas import (
    deslocar_mes,
    validar_competencia,
)

COLUNAS_IDENTIFICADORES: list[str] = ["competencia", "destino", "uf"]

COLUNAS_FEATURES: list[str] = [
    "mes",
    "admissoes",
    "desligamentos",
    "admissoes_lag_1",
    "admissoes_lag_2",
    "admissoes_lag_3",
    "admissoes_lag_12",
    "desligamentos_lag_1",
    "desligamentos_lag_2",
    "desligamentos_lag_3",
    "desligamentos_lag_12",
    "admissoes_soma_3m",
    "admissoes_media_3m",
    "admissoes_sazonal_ano_anterior",
    "admissoes_total",
    "desligamentos_total",
    "admissoes_total_lag_1",
    "admissoes_total_lag_2",
    "admissoes_total_lag_3",
    "admissoes_total_lag_12",
    "desligamentos_total_lag_1",
    "desligamentos_total_lag_2",
    "desligamentos_total_lag_3",
    "desligamentos_total_lag_12",
    "admissoes_total_soma_3m",
    "admissoes_total_media_3m",
    "admissoes_total_sazonal_ano_anterior",
]

COLUNA_ALVO: str = "alvo"


def construir_painel_features(
    dados: pd.DataFrame,
    cobertura: pd.DataFrame,
    ocupacoes: Any = None,
    competencias: list[str] | None = None,
    ufs: list[str] | None = None,
    calcular_alvo: bool = True,
    horizonte_consolidacao: str | None = None,
    permitir_teste: bool = False,
) -> pd.DataFrame:
    """Constrói o painel de features as-of para cada competência solicitada.

    Aceita tanto microdados brutos quanto DataFrame já pré-agregado por
    `pre_agregar_microdados` ou `concatenar_pre_agregados`.

    Para cada competência t:
    - Agrega apenas informações disponíveis até t (competencia_disp <= t e competencia_mov <= t).
    - Valida observação completa: MOV em m e revisões FOR/EXC em todo intervalo m..t.
    - Extrai features retrospectivas em t (admissões/desligamentos, lags 1, 2, 3, 12,
      soma/média 3m, sazonal ano anterior).
    - Não preenche janelas incompletas com zero (permanecem NaN).
    - Se calcular_alvo=True, anexa a coluna 'alvo' consolidado y(g,t) = A(t+1) + A(t+2) + A(t+3).
    - Protege o holdout congelado (D10): competências >= 202601 são bloqueadas por padrão,
      exigindo `permitir_teste=True` para cenários sintéticos de teste.
    """
    ufs = ufs or UFS_BRASIL

    # Identificar se a entrada já é pré-agregada ou se são microdados brutos
    colunas_pre = {
        "destino", "uf", "superior", "competencia_mov", "competencia_disp",
        "delta_adm", "delta_des"
    }
    if colunas_pre.issubset(dados.columns):
        df_pre = dados.copy()
        _, destinos = extrair_mapa_cbo(ocupacoes)
    else:
        df_pre = pre_agregar_microdados(dados, ocupacoes=ocupacoes)
        _, destinos = extrair_mapa_cbo(ocupacoes)

    if competencias is None:
        # As competências inferidas passam pela mesma validação das explícitas (RV-S7-02).
        if "competencia" in cobertura.columns and not cobertura.empty:
            origem_comp = cobertura["competencia"]
        elif not df_pre.empty:
            origem_comp = df_pre["competencia_mov"]
        else:
            origem_comp = pd.Series(dtype="string")
        todas_comp = sorted({validar_competencia(str(c)) for c in origem_comp.dropna()})

        if not permitir_teste:
            # Em modo desenvolvimento padrão, nunca calcula origens de teste (>= 202601)
            competencias = [c for c in todas_comp if c <= "202509"]
        else:
            competencias = todas_comp
    else:
        competencias = [validar_competencia(c) for c in competencias]
        if not permitir_teste:
            for c in competencias:
                if c >= "202601":
                    raise ValueError(
                        f"Competência de teste '{c}' bloqueada por padrão em desenvolvimento "
                        f"para proteger o holdout congelado (D10). "
                        f"Para testes sintéticos, use permitir_teste=True."
                    )

    # Para alvos consolidados (se solicitado), calculamos a agregação consolidada de todos os dados
    dados_consolidados_mes: dict[str, pd.DataFrame] = {}
    if calcular_alvo and competencias:
        if horizonte_consolidacao is not None:
            t_max_disp = validar_competencia(horizonte_consolidacao)
        elif not cobertura.empty and "competencia" in cobertura.columns:
            # Horizonte padrão = última competência com algum arquivo ingerido (RV-S7-01).
            # Linhas apenas pendentes/falhas DEPOIS dela não existem como informação e não
            # podem anular alvos já observados; lacunas ANTES dela continuam produzindo NaN.
            ingeridas = cobertura.loc[
                cobertura["situacao"].astype(str).str.strip().str.lower() == "ingerido",
                "competencia",
            ]
            base_horizonte = ingeridas if not ingeridas.empty else cobertura["competencia"]
            t_max_disp = max(validar_competencia(str(c)) for c in base_horizonte.dropna())
        elif not df_pre.empty and df_pre["competencia_disp"].notna().any():
            t_max_disp = str(df_pre["competencia_disp"].max())
        else:
            t_max_disp = "999912"

        todos_meses_alvo: set[str] = set()
        for t in competencias:
            todos_meses_alvo.add(deslocar_mes(t, 1))
            todos_meses_alvo.add(deslocar_mes(t, 2))
            todos_meses_alvo.add(deslocar_mes(t, 3))

        mapa_alvos = agregar_meses_as_of(
            df_pre_agregado=df_pre,
            cobertura=cobertura,
            as_of=str(t_max_disp),
            meses_historico=sorted(todos_meses_alvo),
            destinos=destinos,
            ufs=ufs,
        )
        for m, d in mapa_alvos.items():
            dados_consolidados_mes[m] = d["principal"]

    painel_partes: list[pd.DataFrame] = []

    for t in competencias:
        # Meses passados necessários para as features de t:
        # t, t-1, t-2, t-3, t-9, t-10, t-11, t-12
        meses_necessarios = [
            t,
            deslocar_mes(t, -1),
            deslocar_mes(t, -2),
            deslocar_mes(t, -3),
            deslocar_mes(t, -9),
            deslocar_mes(t, -10),
            deslocar_mes(t, -11),
            deslocar_mes(t, -12),
        ]

        agregados_t = agregar_meses_as_of(
            df_pre_agregado=df_pre,
            cobertura=cobertura,
            as_of=t,
            meses_historico=meses_necessarios,
            destinos=destinos,
            ufs=ufs,
        )

        p_t = agregados_t[t]["principal"]
        tot_t = agregados_t[t]["total"]

        df_t = (
            pd.MultiIndex.from_product([destinos, ufs], names=["destino", "uf"])
            .to_frame()
            .reset_index(drop=True)
        )
        df_t["competencia"] = t
        df_t["mes"] = int(t[4:])

        # Valores em t
        df_t["admissoes"] = p_t["admissoes"]
        df_t["desligamentos"] = p_t["desligamentos"]
        df_t["admissoes_total"] = tot_t["admissoes_total"]
        df_t["desligamentos_total"] = tot_t["desligamentos_total"]

        # Lags da série principal
        p_lag1 = agregados_t[deslocar_mes(t, -1)]["principal"]
        p_lag2 = agregados_t[deslocar_mes(t, -2)]["principal"]
        p_lag3 = agregados_t[deslocar_mes(t, -3)]["principal"]
        p_lag12 = agregados_t[deslocar_mes(t, -12)]["principal"]

        df_t["admissoes_lag_1"] = p_lag1["admissoes"]
        df_t["admissoes_lag_2"] = p_lag2["admissoes"]
        df_t["admissoes_lag_3"] = p_lag3["admissoes"]
        df_t["admissoes_lag_12"] = p_lag12["admissoes"]

        df_t["desligamentos_lag_1"] = p_lag1["desligamentos"]
        df_t["desligamentos_lag_2"] = p_lag2["desligamentos"]
        df_t["desligamentos_lag_3"] = p_lag3["desligamentos"]
        df_t["desligamentos_lag_12"] = p_lag12["desligamentos"]

        # Soma e média dos últimos 3 meses (t, t-1, t-2)
        mats_adm_3m = np.column_stack([
            df_t["admissoes"].to_numpy(),
            df_t["admissoes_lag_1"].to_numpy(),
            df_t["admissoes_lag_2"].to_numpy(),
        ])
        tem_nan_adm = np.isnan(mats_adm_3m).any(axis=1)
        df_t["admissoes_soma_3m"] = np.where(
            tem_nan_adm, np.nan, np.sum(mats_adm_3m, axis=1)
        )
        df_t["admissoes_media_3m"] = np.where(
            tem_nan_adm, np.nan, np.mean(mats_adm_3m, axis=1)
        )

        # Referência sazonal do ano anterior: A(t-11) + A(t-10) + A(t-9)
        p_lag9 = agregados_t[deslocar_mes(t, -9)]["principal"]
        p_lag10 = agregados_t[deslocar_mes(t, -10)]["principal"]
        p_lag11 = agregados_t[deslocar_mes(t, -11)]["principal"]

        mats_saz = np.column_stack([
            p_lag11["admissoes"].to_numpy(),
            p_lag10["admissoes"].to_numpy(),
            p_lag9["admissoes"].to_numpy(),
        ])
        tem_nan_saz = np.isnan(mats_saz).any(axis=1)
        df_t["admissoes_sazonal_ano_anterior"] = np.where(
            tem_nan_saz, np.nan, np.sum(mats_saz, axis=1)
        )

        # Lags da série total (contexto)
        tot_lag1 = agregados_t[deslocar_mes(t, -1)]["total"]
        tot_lag2 = agregados_t[deslocar_mes(t, -2)]["total"]
        tot_lag3 = agregados_t[deslocar_mes(t, -3)]["total"]
        tot_lag12 = agregados_t[deslocar_mes(t, -12)]["total"]

        df_t["admissoes_total_lag_1"] = tot_lag1["admissoes_total"]
        df_t["admissoes_total_lag_2"] = tot_lag2["admissoes_total"]
        df_t["admissoes_total_lag_3"] = tot_lag3["admissoes_total"]
        df_t["admissoes_total_lag_12"] = tot_lag12["admissoes_total"]

        df_t["desligamentos_total_lag_1"] = tot_lag1["desligamentos_total"]
        df_t["desligamentos_total_lag_2"] = tot_lag2["desligamentos_total"]
        df_t["desligamentos_total_lag_3"] = tot_lag3["desligamentos_total"]
        df_t["desligamentos_total_lag_12"] = tot_lag12["desligamentos_total"]

        mats_tot_3m = np.column_stack([
            df_t["admissoes_total"].to_numpy(),
            df_t["admissoes_total_lag_1"].to_numpy(),
            df_t["admissoes_total_lag_2"].to_numpy(),
        ])
        tem_nan_tot = np.isnan(mats_tot_3m).any(axis=1)
        df_t["admissoes_total_soma_3m"] = np.where(
            tem_nan_tot, np.nan, np.sum(mats_tot_3m, axis=1)
        )
        df_t["admissoes_total_media_3m"] = np.where(
            tem_nan_tot, np.nan, np.mean(mats_tot_3m, axis=1)
        )

        tot_lag9 = agregados_t[deslocar_mes(t, -9)]["total"]
        tot_lag10 = agregados_t[deslocar_mes(t, -10)]["total"]
        tot_lag11 = agregados_t[deslocar_mes(t, -11)]["total"]

        mats_tot_saz = np.column_stack([
            tot_lag11["admissoes_total"].to_numpy(),
            tot_lag10["admissoes_total"].to_numpy(),
            tot_lag9["admissoes_total"].to_numpy(),
        ])
        tem_nan_tot_saz = np.isnan(mats_tot_saz).any(axis=1)
        df_t["admissoes_total_sazonal_ano_anterior"] = np.where(
            tem_nan_tot_saz, np.nan, np.sum(mats_tot_saz, axis=1)
        )

        # Cálculo do alvo y(g,t) = A(t+1) + A(t+2) + A(t+3)
        if calcular_alvo:
            m1 = deslocar_mes(t, 1)
            m2 = deslocar_mes(t, 2)
            m3 = deslocar_mes(t, 3)

            p_m1 = dados_consolidados_mes.get(m1)
            p_m2 = dados_consolidados_mes.get(m2)
            p_m3 = dados_consolidados_mes.get(m3)

            if p_m1 is not None and p_m2 is not None and p_m3 is not None:
                alvo_mats = np.column_stack([
                    p_m1["admissoes"].to_numpy(),
                    p_m2["admissoes"].to_numpy(),
                    p_m3["admissoes"].to_numpy(),
                ])
                tem_nan_alvo = np.isnan(alvo_mats).any(axis=1)
                df_t["alvo"] = np.where(tem_nan_alvo, np.nan, np.sum(alvo_mats, axis=1))
            else:
                df_t["alvo"] = np.nan

        painel_partes.append(df_t)

    if not painel_partes:
        todas_colunas = COLUNAS_IDENTIFICADORES + COLUNAS_FEATURES
        if calcular_alvo:
            todas_colunas.append(COLUNA_ALVO)
        return pd.DataFrame(columns=todas_colunas)

    resultado = pd.concat(painel_partes, ignore_index=True)
    resultado["competencia"] = resultado["competencia"].astype("string")
    resultado["destino"] = resultado["destino"].astype("string")
    resultado["uf"] = resultado["uf"].astype("string")

    return resultado

