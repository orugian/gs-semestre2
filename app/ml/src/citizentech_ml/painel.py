"""Módulo de construção, carregamento e persistência do painel de desenvolvimento."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from citizentech_ml.features.agregador import (
    CAMINHO_CATALOGO_PADRAO,
    UFS_BRASIL,
    concatenar_pre_agregados,
    pre_agregar_microdados,
)
from citizentech_ml.features.datas import gerar_intervalo_meses, validar_competencia
from citizentech_ml.features.extracao import construir_painel_features
from citizentech_ml.ingestao.cobertura import cobertura
from citizentech_ml.ingestao.manifesto import carregar_manifesto
from citizentech_ml.ingestao.ocupacoes import carregar_ocupacoes

COLUNAS_PRE_AGREGADO: list[str] = [
    "destino",
    "uf",
    "superior",
    "competencia_mov",
    "competencia_disp",
    "delta_adm",
    "delta_des",
]

COLUNAS_LEITURA: list[str] = [
    "competencia_mov",
    "competencia_dec",
    "competencia_exc",
    "competencia_arquivo",
    "arquivo_tipo",
    "saldo_movimentacao",
    "cbo2002_ocupacao",
    "uf",
    "grau_instrucao",
]


def carregar_pre_agregado(
    dir_parquet: str | Path,
    ocupacoes: Any = None,
    limite_competencia_mov: str = "202512",
    permitir_teste: bool = False,
    por_tipo: bool = False,
) -> tuple[pd.DataFrame, dict[str, Any]]:

    """Carrega microdados particionados em Parquet, pré-agregando arquivo por arquivo."""
    dir_p = Path(dir_parquet)
    if not dir_p.exists() or not dir_p.is_dir():
        raise FileNotFoundError(f"Diretório de parquets não encontrado: {dir_p}")

    arquivos = sorted(dir_p.glob("*.parquet"))
    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo Parquet encontrado em: {dir_p}")

    limite_val = validar_competencia(limite_competencia_mov)
    if limite_val > "202512" and not permitir_teste:
        raise ValueError(
            f"limite_competencia_mov '{limite_val}' > 202512 exige permitir_teste=True."
        )

    ufs_validas = set(UFS_BRASIL)
    linhas_uf_invalida: dict[str, int] = {}
    total_linhas_lidas = 0
    linhas_apos_limite = 0
    lista_pre: list[pd.DataFrame] = []

    for arq in arquivos:
        schema_names = pq.ParquetFile(arq).schema.names
        cols = [c for c in COLUNAS_LEITURA if c in schema_names]
        df_lido = pd.read_parquet(arq, columns=cols)
        total_linhas_lidas += len(df_lido)

        if df_lido.empty:
            continue

        # 1. Descartar UFs inválidas contando por código
        uf_series = df_lido["uf"].astype(str).str.strip()
        mascara_uf_invalida = ~uf_series.isin(ufs_validas)
        if mascara_uf_invalida.any():
            contagens = uf_series[mascara_uf_invalida].value_counts()
            for uf_cod, qtd in contagens.items():
                uf_cod_str = str(uf_cod)
                linhas_uf_invalida[uf_cod_str] = linhas_uf_invalida.get(uf_cod_str, 0) + int(qtd)
            df_lido = df_lido[~mascara_uf_invalida].copy()

        if df_lido.empty:
            continue

        # 2. Descartar competências após o limite
        comp_mov = df_lido["competencia_mov"].astype(str).str.strip()
        mascara_apos_limite = comp_mov > limite_val
        if mascara_apos_limite.any():
            linhas_apos_limite += int(mascara_apos_limite.sum())
            df_lido = df_lido[~mascara_apos_limite].copy()

        if df_lido.empty:
            continue

        df_pre = pre_agregar_microdados(df_lido, ocupacoes=ocupacoes)
        if not df_pre.empty:
            if por_tipo:
                tipo = str(df_lido["arquivo_tipo"].iloc[0]).strip().upper()
                df_pre = df_pre.copy()
                df_pre["arquivo_tipo"] = tipo
            lista_pre.append(df_pre)

    if por_tipo:
        if not lista_pre:
            cols = [
                "destino",
                "uf",
                "superior",
                "competencia_mov",
                "competencia_disp",
                "arquivo_tipo",
                "delta_adm",
                "delta_des",
            ]
            pre_agregado = pd.DataFrame(columns=cols)
        else:
            df_concat = pd.concat(lista_pre, ignore_index=True)
            cols_grupo = [
                "destino",
                "uf",
                "superior",
                "competencia_mov",
                "competencia_disp",
                "arquivo_tipo",
            ]
            pre_agregado = (
                df_concat.groupby(cols_grupo, as_index=False)[["delta_adm", "delta_des"]]
                .sum()
                .sort_values(cols_grupo)
                .reset_index(drop=True)
            )
    else:
        pre_agregado = concatenar_pre_agregados(lista_pre)

    relatorio: dict[str, Any] = {
        "arquivos_lidos": len(arquivos),
        "linhas_lidas": total_linhas_lidas,
        "linhas_uf_invalida": dict(sorted(linhas_uf_invalida.items())),
        "linhas_apos_limite": int(linhas_apos_limite),
        "linhas_pre_agregadas": len(pre_agregado),
        "limite_usado": limite_val,
    }
    return pre_agregado, relatorio


def atribuir_particao(competencia: str) -> str:
    """Classifica competência em partição congelada (D10)."""
    comp = validar_competencia(competencia)
    if comp <= "202409":
        return "treino"
    if "202410" <= comp <= "202412":
        return "embargo"
    if "202501" <= comp <= "202509":
        return "validacao"
    raise ValueError(f"Competência '{comp}' fora do intervalo de desenvolvimento (máximo 202509).")


def construir_painel_desenvolvimento(
    dir_dados: str | Path,
    caminho_ocupacoes: str | Path | None = None,
    inicio: str = "202001",
    fim: str = "202509",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Constrói o painel de desenvolvimento destino x UF x mês com partição."""
    inicio_val = validar_competencia(inicio)
    fim_val = validar_competencia(fim)
    if fim_val > "202509":
        raise ValueError(
            f"fim '{fim_val}' não pode ser posterior a 202509 (holdout e embargo protegidos)."
        )
    if inicio_val > fim_val:
        raise ValueError(f"inicio '{inicio_val}' posterior a fim '{fim_val}'.")

    dir_dados_path = Path(dir_dados)
    manifesto_path = dir_dados_path / "caged" / "procedencia.json"
    manifesto = carregar_manifesto(manifesto_path)
    if manifesto:
        comps = [r.competencia_arquivo for r in manifesto if r.competencia_arquivo]
        fim_cobertura = max(comps) if comps else fim_val
        if fim_cobertura < fim_val:
            fim_cobertura = fim_val
    else:
        fim_cobertura = fim_val

    df_cob = cobertura(dir_dados_path, inicio_val, fim_cobertura)

    ocupacoes = None
    if caminho_ocupacoes is not None:
        ocupacoes = carregar_ocupacoes(caminho_ocupacoes)

    dir_parquet = dir_dados_path / "caged" / "parquet"
    pre_agregado, relatorio_carga = carregar_pre_agregado(
        dir_parquet, ocupacoes=ocupacoes, limite_competencia_mov="202512"
    )

    intervalo_comps = gerar_intervalo_meses(inicio_val, fim_val)
    painel = construir_painel_features(
        dados=pre_agregado,
        cobertura=df_cob,
        ocupacoes=ocupacoes,
        competencias=intervalo_comps,
        permitir_teste=False,
    )

    painel["particao"] = painel["competencia"].astype(str).map(atribuir_particao).astype("string")

    relatorio = dict(relatorio_carga)
    relatorio.update(
        {
            "inicio": inicio_val,
            "fim": fim_val,
            "linhas_painel": len(painel),
            "particoes": {str(k): int(v) for k, v in painel["particao"].value_counts().items()},
        }
    )
    return painel, relatorio


def salvar_painel(
    painel: pd.DataFrame,
    relatorio: dict[str, Any],
    dir_saida: str | Path,
    caminho_ocupacoes: str | Path | None = None,
) -> tuple[Path, Path]:
    """Persiste o painel em Parquet e os metadados em JSON UTF-8 sem BOM."""
    dir_s = Path(dir_saida)
    dir_s.mkdir(parents=True, exist_ok=True)

    caminho_parquet = dir_s / "painel_desenvolvimento.parquet"
    caminho_json = dir_s / "painel_desenvolvimento.json"

    painel.to_parquet(caminho_parquet, index=False)
    sha256_parquet = hashlib.sha256(caminho_parquet.read_bytes()).hexdigest()

    sha256_ocupacoes: str | None = None
    if caminho_ocupacoes is not None and Path(caminho_ocupacoes).exists():
        sha256_ocupacoes = hashlib.sha256(Path(caminho_ocupacoes).read_bytes()).hexdigest()
    elif CAMINHO_CATALOGO_PADRAO.exists():
        sha256_ocupacoes = hashlib.sha256(CAMINHO_CATALOGO_PADRAO.read_bytes()).hexdigest()

    data_utc = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    info_json = {
        "relatorio": relatorio,
        "sha256_parquet": sha256_parquet,
        "sha256_ocupacoes": sha256_ocupacoes,
        "data_utc": data_utc,
        "versoes": {
            "pandas": str(pd.__version__),
            "numpy": str(np.__version__),
            "pyarrow": str(pa.__version__),
        },
    }

    caminho_json.write_text(
        json.dumps(info_json, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return caminho_parquet, caminho_json


def main() -> None:
    """Ponto de entrada CLI para montagem do painel de desenvolvimento."""
    parser = argparse.ArgumentParser(
        description="Construção e salvamento do painel de desenvolvimento do Novo Caged."
    )
    parser.add_argument("--dados", required=True, help="Diretório base de dados (contém caged/).")
    parser.add_argument("--saida", required=True, help="Diretório de saída para salvar o painel.")
    parser.add_argument("--ocupacoes", default=None, help="Caminho alternativo para catálogo CBO.")
    parser.add_argument("--inicio", default="202001", help="Competência inicial (padrão 202001).")
    parser.add_argument("--fim", default="202509", help="Competência final (padrão 202509).")

    args = parser.parse_args()

    try:
        painel, relatorio = construir_painel_desenvolvimento(
            dir_dados=args.dados,
            caminho_ocupacoes=args.ocupacoes,
            inicio=args.inicio,
            fim=args.fim,
        )
        caminho_parquet, caminho_json = salvar_painel(
            painel=painel,
            relatorio=relatorio,
            dir_saida=args.saida,
            caminho_ocupacoes=args.ocupacoes,
        )
        print("=== Relatório de Construção do Painel ===")
        print(json.dumps(relatorio, indent=2, ensure_ascii=False))
        print(f"Painel gravado com sucesso em: {caminho_parquet}")
        print(f"Metadados gravados em: {caminho_json}")
    except Exception as exc:
        print(f"Erro na construção do painel: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
