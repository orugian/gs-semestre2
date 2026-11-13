"""Agregação as-of e construção de grade regular de destinos x 27 UFs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from citizentech_ml.features.cobertura_regras import (
    verificar_observacao_completa_as_of,
)
from citizentech_ml.features.disponibilidade import (
    filtrar_disponiveis_as_of,
    validar_e_calcular_disponibilidade,
)
from citizentech_ml.ingestao.consolidacao import GRAUS_SUPERIOR_OU_MAIS
from citizentech_ml.ingestao.ocupacoes import carregar_ocupacoes

UFS_BRASIL: list[str] = [
    "11", "12", "13", "14", "15", "16", "17",
    "21", "22", "23", "24", "25", "26", "27", "28", "29",
    "31", "32", "33", "35",
    "41", "42", "43",
    "50", "51", "52", "53",
]

DESTINOS_PADRAO: list[str] = [
    "analista_dados_bi",
    "analista_monitoramento_iot",
    "analista_processos",
    "gerente_projetos_produto",
    "analista_suporte_infra",
    "desenvolvedor_sistemas",
]

CAMINHO_CATALOGO_PADRAO = (
    Path(__file__).resolve().parents[4] / "catalogo" / "ocupacoes_cbo.json"
)


def _validar_cbo_codigo(cbo: Any) -> str:
    """Valida código CBO como string estrita de 6 dígitos numéricos."""
    if cbo is None or isinstance(cbo, bool):
        raise ValueError(f"CBO inválido: {cbo!r}")
    cbo_str = str(cbo).strip()
    if len(cbo_str) != 6 or not cbo_str.isdigit():
        raise ValueError(f"CBO deve conter exatamente 6 dígitos numéricos, recebido: {cbo!r}")
    return cbo_str


def extrair_mapa_cbo(ocupacoes: Any = None) -> tuple[dict[str, str], list[str]]:
    """Extrai mapa de CBO6 -> destino e lista de destinos a partir do catálogo/objeto Ocupacoes.

    Regras (D04a / Aceite S7):
    - Cada destino é conjunto disjunto de CBOs de 6 dígitos.
    - Se qualquer CBO for repetido entre destinos diferentes, gera ValueError explícito.
    - Reserva CBO6 deve ser disjunta de todos os destinos; se sobrepuser, gera ValueError.
    - A reserva CBO6 é explicitamente excluída do mapa retornado.
    """
    if ocupacoes is None:
        if CAMINHO_CATALOGO_PADRAO.exists():
            ocupacoes = carregar_ocupacoes(CAMINHO_CATALOGO_PADRAO)
        else:
            raise ValueError(
                "Objeto de ocupações não fornecido e catálogo padrão não encontrado."
            )

    destinos_dict = getattr(ocupacoes, "destinos", None)
    reserva_lista = getattr(ocupacoes, "cbo6_reserva", None)

    if destinos_dict is None and isinstance(ocupacoes, dict):
        destinos_dict = ocupacoes.get("destinos", {})
    if reserva_lista is None and isinstance(ocupacoes, dict):
        reserva_lista = ocupacoes.get("cbo6_reserva", [])

    if not isinstance(destinos_dict, dict) or not destinos_dict:
        raise ValueError("Estrutura de ocupações inválida: nenhum destino encontrado.")

    mapa: dict[str, str] = {}
    destinos_ordenados = sorted(destinos_dict.keys())

    for destino_id, info in destinos_dict.items():
        cbos = info.get("cbo6", []) if isinstance(info, dict) else []
        for cbo in cbos:
            cbo_str = _validar_cbo_codigo(cbo)
            if cbo_str in mapa:
                antigo = mapa[cbo_str]
                if antigo != destino_id:
                    raise ValueError(
                        f"CBO {cbo_str} atribuído a múltiplos destinos: "
                        f"'{antigo}' e '{destino_id}'."
                    )
            mapa[cbo_str] = str(destino_id)

    # Validar que a reserva é disjunta dos destinos oficiais
    if reserva_lista:
        for cbo_res in reserva_lista:
            cbo_res_str = _validar_cbo_codigo(cbo_res)
            if cbo_res_str in mapa:
                raise ValueError(
                    f"CBO de reserva {cbo_res_str} sobrepõe o destino '{mapa[cbo_res_str]}'."
                )

    return mapa, destinos_ordenados


def _validar_saldo_movimentacao(serie: pd.Series) -> None:
    """Valida que todos os saldos de movimentação são estritamente 1 ou -1."""
    for v in serie.unique():
        if v is None or pd.isna(v):
            raise ValueError("Coluna 'saldo_movimentacao' contém valores nulos/ausentes.")
        if isinstance(v, bool) or type(v) is bool:
            raise ValueError(f"Coluna 'saldo_movimentacao' não aceita booleanos: {v!r}")
        if isinstance(v, (int, np.integer)):
            if v not in (1, -1):
                raise ValueError(f"saldo_movimentacao deve ser 1 ou -1, recebido: {v!r}")
        elif isinstance(v, (float, np.floating)):
            if not np.isfinite(v) or v not in (1.0, -1.0):
                raise ValueError(f"saldo_movimentacao float inválido (esperado 1 ou -1): {v!r}")
        elif isinstance(v, str):
            s = v.strip()
            if s not in ("1", "-1", "1.0", "-1.0"):
                raise ValueError(f"saldo_movimentacao string inválida: {v!r}")
        else:
            raise ValueError(f"Tipo não suportado em 'saldo_movimentacao': {type(v).__name__}")


def _validar_ufs(serie: pd.Series) -> None:
    """Valida códigos de UF segundo o padrão IBGE."""
    ufs_validas = set(UFS_BRASIL)
    for v in serie.unique():
        if v is None or pd.isna(v):
            raise ValueError("Coluna 'uf' contém valores nulos/ausentes.")
        if isinstance(v, bool):
            raise ValueError(f"Coluna 'uf' não aceita booleanos: {v!r}")
        s = str(v).strip()
        if s not in ufs_validas:
            raise ValueError(f"Código de UF IBGE inválido: {v!r}")


def _validar_grau_instrucao(serie: pd.Series) -> None:
    """Valida que grau de instrução não é nulo, bool ou valor não finito."""
    for v in serie.unique():
        if v is None or pd.isna(v):
            raise ValueError("Coluna 'grau_instrucao' contém valores nulos/ausentes.")
        if isinstance(v, bool) or type(v) is bool:
            raise ValueError(f"Coluna 'grau_instrucao' não aceita booleanos: {v!r}")
        if isinstance(v, (float, np.floating)):
            if not np.isfinite(v) or not float(v).is_integer():
                raise ValueError(f"Coluna 'grau_instrucao' contém float inválido: {v!r}")
        elif isinstance(v, str):
            s = v.strip()
            if not s.isdigit():
                raise ValueError(f"Coluna 'grau_instrucao' contém string inválida: {v!r}")
        elif isinstance(v, (int, np.integer)):
            pass
        else:
            raise ValueError(f"Tipo inválido para 'grau_instrucao': {type(v).__name__}")


def pre_agregar_microdados(
    df: pd.DataFrame,
    ocupacoes: Any = None,
) -> pd.DataFrame:
    """Valida, calcula disponibilidade e pré-agrega microdados por destino/UF/superior/mês/disp.

    Regras (D04b / R02 / Aceite S7):
    - Validação estrita sem coerção silenciosa (rejeita nulos, tipos inválidos, saldos != +-1).
    - Não deduplica linhas (registros idênticos são preservados).
    - Exclui CBOs que não pertençam aos destinos oficiais (inclusive reserva).
    """
    if df.empty:
        return pd.DataFrame(
            columns=[
                "destino",
                "uf",
                "superior",
                "competencia_mov",
                "competencia_disp",
                "delta_adm",
                "delta_des",
            ]
        )

    # 1. Validação temporal e cálculo de disponibilidade
    df_disp = validar_e_calcular_disponibilidade(df)

    # 2. Validação estrita de integridade dos dados (sem coerção silenciosa)
    _validar_saldo_movimentacao(df_disp["saldo_movimentacao"])
    _validar_ufs(df_disp["uf"])
    _validar_grau_instrucao(df_disp["grau_instrucao"])

    cbo_mapa, _ = extrair_mapa_cbo(ocupacoes)

    df_filtrado = df_disp.copy()
    df_filtrado["cbo2002_ocupacao"] = df_filtrado["cbo2002_ocupacao"].astype(str).str.strip()
    df_filtrado["destino"] = df_filtrado["cbo2002_ocupacao"].map(cbo_mapa)

    # Filtrar apenas ocupações pertencentes a algum destino oficial (reserva é descartada)
    df_filtrado = df_filtrado[df_filtrado["destino"].notna()].copy()
    if df_filtrado.empty:
        return pd.DataFrame(
            columns=[
                "destino",
                "uf",
                "superior",
                "competencia_mov",
                "competencia_disp",
                "delta_adm",
                "delta_des",
            ]
        )

    df_filtrado["uf"] = df_filtrado["uf"].astype(str).str.strip()
    grau_int = df_filtrado["grau_instrucao"].astype(float).astype(int)
    df_filtrado["superior"] = grau_int.isin(GRAUS_SUPERIOR_OU_MAIS)

    sinal = df_filtrado["arquivo_tipo"].map({"MOV": 1, "FOR": 1, "EXC": -1})
    saldo = df_filtrado["saldo_movimentacao"].astype(float).astype(int)

    df_filtrado["delta_adm"] = ((saldo == 1).astype(int) * sinal)
    df_filtrado["delta_des"] = ((saldo == -1).astype(int) * sinal)

    agrupado = (
        df_filtrado.groupby(
            ["destino", "uf", "superior", "competencia_mov", "competencia_disp"],
            as_index=False,
            dropna=False,
        )[["delta_adm", "delta_des"]]
        .sum()
    )
    return agrupado


def concatenar_pre_agregados(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """Concatena e consolida múltiplos DataFrames pré-agregados por destino/uf/superior/mes/disp.

    Permite processamento eficiente de arquivos Parquet ou lotes de microdados sem expandir memória.
    """
    validos = [d for d in dfs if not d.empty]
    colunas = [
        "destino", "uf", "superior", "competencia_mov", "competencia_disp",
        "delta_adm", "delta_des"
    ]
    if not validos:
        return pd.DataFrame(columns=colunas)

    concatenado = pd.concat(validos, ignore_index=True)
    agrupado = (
        concatenado.groupby(
            ["destino", "uf", "superior", "competencia_mov", "competencia_disp"],
            as_index=False,
            dropna=False,
        )[["delta_adm", "delta_des"]]
        .sum()
    )
    return agrupado


def agregar_meses_as_of(
    df_pre_agregado: pd.DataFrame,
    cobertura: pd.DataFrame,
    as_of: str,
    meses_historico: list[str],
    destinos: list[str],
    ufs: list[str] | None = None,
) -> dict[str, dict[str, pd.DataFrame]]:
    """Agrega contagens mensais como conhecidas no momento as-of para uma lista de meses históricos.

    Retorna:
    {
       mes: {
          "principal": DataFrame (destino x UF, colunas: admissoes, desligamentos),
          "total": DataFrame (destino x UF, colunas: admissoes_total, desligamentos_total)
       }
    }
    Se o mês de movimento não estiver completamente observado em as-of (MOV em mes e
    revisões FOR/EXC em todo intervalo mes..as_of), os valores são NaN.
    Se o mês estiver coberto, séries sem movimentação têm valor 0.0.
    Se contagens resultantes forem negativas, gera ValueError explícito.
    """
    ufs = ufs or UFS_BRASIL
    df_visivel = filtrar_disponiveis_as_of(df_pre_agregado, as_of)

    grade_base = (
        pd.MultiIndex.from_product([destinos, ufs], names=["destino", "uf"])
        .to_frame()
        .reset_index(drop=True)
    )

    resultado: dict[str, dict[str, pd.DataFrame]] = {}

    for mes in meses_historico:
        esta_coberto = verificar_observacao_completa_as_of(
            cobertura, mes_mov=mes, as_of=as_of
        )

        if not esta_coberto:
            # Não completamente observado as-of -> NaN para todas as séries
            df_nan_princ = grade_base.copy()
            df_nan_princ["admissoes"] = float("nan")
            df_nan_princ["desligamentos"] = float("nan")

            df_nan_tot = grade_base.copy()
            df_nan_tot["admissoes_total"] = float("nan")
            df_nan_tot["desligamentos_total"] = float("nan")

            resultado[mes] = {"principal": df_nan_princ, "total": df_nan_tot}
            continue

        # Mês coberto: extrair movimentações visíveis até as-of
        sub_mes = (
            df_visivel[df_visivel["competencia_mov"] == mes]
            if not df_visivel.empty
            else pd.DataFrame()
        )

        if sub_mes.empty:
            df_princ = grade_base.copy()
            df_princ["admissoes"] = 0.0
            df_princ["desligamentos"] = 0.0

            df_tot = grade_base.copy()
            df_tot["admissoes_total"] = 0.0
            df_tot["desligamentos_total"] = 0.0

            resultado[mes] = {"principal": df_princ, "total": df_tot}
            continue

        # 1. Série Principal (superior completo ou mais)
        sub_sup = sub_mes[sub_mes["superior"]]
        if not sub_sup.empty:
            sub_princ = sub_sup.groupby(
                ["destino", "uf"], as_index=False
            )[["delta_adm", "delta_des"]].sum()
            sub_princ = sub_princ.rename(
                columns={"delta_adm": "admissoes", "delta_des": "desligamentos"}
            )
            df_princ = pd.merge(grade_base, sub_princ, on=["destino", "uf"], how="left")
            df_princ["admissoes"] = df_princ["admissoes"].fillna(0.0).astype(float)
            df_princ["desligamentos"] = df_princ["desligamentos"].fillna(0.0).astype(float)
        else:
            df_princ = grade_base.copy()
            df_princ["admissoes"] = 0.0
            df_princ["desligamentos"] = 0.0

        # 2. Série Total (contexto, todos os graus)
        sub_tot = sub_mes.groupby(
            ["destino", "uf"], as_index=False
        )[["delta_adm", "delta_des"]].sum()
        sub_tot = sub_tot.rename(
            columns={"delta_adm": "admissoes_total", "delta_des": "desligamentos_total"}
        )

        df_tot = pd.merge(grade_base, sub_tot, on=["destino", "uf"], how="left")
        df_tot["admissoes_total"] = df_tot["admissoes_total"].fillna(0.0).astype(float)
        df_tot["desligamentos_total"] = df_tot["desligamentos_total"].fillna(0.0).astype(float)

        # Verificação rigorosa contra contagens negativas (não clipar silenciosamente)
        if (df_princ["admissoes"] < 0).any() or (df_princ["desligamentos"] < 0).any():
            raise ValueError(
                f"Contagem negativa inconsistente na série principal no mês {mes} as-of {as_of}."
            )
        if (df_tot["admissoes_total"] < 0).any() or (df_tot["desligamentos_total"] < 0).any():
            raise ValueError(
                f"Contagem negativa inconsistente na série total no mês {mes} as-of {as_of}."
            )

        resultado[mes] = {"principal": df_princ, "total": df_tot}

    return resultado

