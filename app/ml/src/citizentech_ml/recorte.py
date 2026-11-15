"""Módulo de recorte do escopo MVP (R29) para o painel de desenvolvimento."""

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

from citizentech_ml.features.agregador import DESTINOS_PADRAO
from citizentech_ml.features.datas import validar_competencia

DESTINOS_CANONICOS_SEIS: tuple[str, ...] = tuple(DESTINOS_PADRAO)

DESTINOS_MVP_PADRAO: tuple[str, ...] = (
    "analista_dados_bi",
    "analista_monitoramento_iot",
    "analista_processos",
)


def obter_caminho_catalogo_padrao() -> Path:
    """Retorna o caminho padrão para o arquivo do escopo MVP.

    Busca em app/catalogo/escopo_mvp.json garantindo resolução consistente.
    """
    p3 = Path(__file__).resolve().parents[3] / "catalogo" / "escopo_mvp.json"
    if p3.exists():
        return p3
    p4 = Path(__file__).resolve().parents[4] / "app" / "catalogo" / "escopo_mvp.json"
    if p4.exists():
        return p4
    return p3


def validar_escopo_mvp(
    dados: Any, sha256_escopo: str | None = None
) -> dict[str, Any]:
    """Valida o conteúdo do escopo MVP R29 com checagens estritas de metadados e IDs.

    Garante que qualquer via pública (seja por arquivo ou dicionário direto) passe
    pela mesma validação de integridade.
    """
    if not isinstance(dados, dict):
        raise ValueError("Conteúdo do escopo deve ser um dicionário/objeto JSON.")

    versao = dados.get("versao")
    if not isinstance(versao, str) or not versao.strip():
        raise ValueError("Campo 'versao' obrigatório ausente ou inválido no escopo.")

    decisao = dados.get("decisao")
    if decisao != "R29":
        raise ValueError(f"Decisão deve ser 'R29', recebido: {decisao!r}")

    destinos = dados.get("destinos")
    if not isinstance(destinos, list) or not all(isinstance(d, str) for d in destinos):
        raise ValueError("Campo 'destinos' deve ser uma lista de strings.")

    if len(destinos) != len(set(destinos)):
        raise ValueError("Destinos duplicados detectados no escopo.")

    if set(destinos) != set(DESTINOS_MVP_PADRAO):
        raise ValueError(
            f"Conjunto de destinos inválido: esperado {set(DESTINOS_MVP_PADRAO)}, "
            f"recebido {set(destinos)}"
        )

    status_rubricas = dados.get("status_rubricas")
    if status_rubricas != "revisao_humana_pendente":
        raise ValueError(
            "Campo 'status_rubricas' deve ser 'revisao_humana_pendente', "
            f"recebido: {status_rubricas!r}"
        )

    # Rejeição estrita de qualquer chave de métrica
    chaves_proibidas = {
        "metricas",
        "estatistica",
        "estatisticas",
        "metrics",
        "mae",
        "rmse",
        "wape",
        "mase",
    }
    presentes_proibidas = chaves_proibidas.intersection(dados.keys())
    if presentes_proibidas:
        raise ValueError(f"Métricas proibidas presentes no escopo: {sorted(presentes_proibidas)}")

    # Hash determinístico do recorte
    hash_recorte = hashlib.sha256(",".join(sorted(destinos)).encode("utf-8")).hexdigest()
    if sha256_escopo is None:
        payload = json.dumps(
            {
                "versao": versao,
                "decisao": decisao,
                "destinos": sorted(destinos),
                "status_rubricas": status_rubricas,
            },
            sort_keys=True,
        ).encode("utf-8")
        sha256_escopo = hashlib.sha256(payload).hexdigest()

    return {
        "versao": versao,
        "decisao": decisao,
        "destinos": list(destinos),
        "status_rubricas": status_rubricas,
        "hash_recorte": hash_recorte,
        "sha256_escopo": sha256_escopo,
    }


def carregar_escopo_mvp(caminho: str | Path | None = None) -> dict[str, Any]:
    """Carrega e valida o escopo MVP aprovado na decisão R29.

    Retorna dicionário validado com IDs únicos, conjunto aprovado
    e hash determinístico do recorte.
    """
    if caminho is None:
        caminho_arquivo = obter_caminho_catalogo_padrao()
    else:
        caminho_arquivo = Path(caminho)

    if not caminho_arquivo.exists():
        raise FileNotFoundError(f"Arquivo de escopo não encontrado: {caminho_arquivo}")

    with caminho_arquivo.open("r", encoding="utf-8") as f:
        dados = json.load(f)

    sha256_escopo = hashlib.sha256(caminho_arquivo.read_bytes()).hexdigest()
    return validar_escopo_mvp(dados, sha256_escopo=sha256_escopo)


def recortar_painel_mvp(
    painel: pd.DataFrame,
    escopo: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Recorta o painel de desenvolvimento para o escopo MVP R29.

    Preserva todas as colunas e origens históricas 2020. Mantém input intacto.
    Rejeita competências fora de 202001-202509, destinos desconhecidos,
    duplicações na chave (competencia, destino, uf) e ausência de qualquer
    um dos 3 destinos do MVP. Rejeita projeção vazia.
    """
    if not isinstance(painel, pd.DataFrame):
        raise TypeError("O painel de entrada deve ser um pandas DataFrame.")

    if painel.empty:
        raise ValueError("Operação rejeitada: painel vazio.")

    colunas_obrigatorias = {"competencia", "destino", "uf"}
    colunas_faltantes = colunas_obrigatorias - set(painel.columns)
    if colunas_faltantes:
        raise ValueError(f"Colunas obrigatórias ausentes no painel: {sorted(colunas_faltantes)}")

    # 1. Validação de chaves duplicadas
    if painel.duplicated(subset=["competencia", "destino", "uf"]).any():
        raise ValueError("Chaves duplicadas (competencia, destino, uf) encontradas no painel.")

    # 2. Validação estrita de competências (permitido: 202001 a 202509)
    comps = painel["competencia"].astype(str)
    for c in comps.unique():
        c_val = validar_competencia(c)
        if c_val < "202001" or c_val > "202509":
            raise ValueError(
                f"Competência '{c}' fora do intervalo permitido 202001-202509 "
                f"(origem 202510-202512 é embargo e >= 202601 é teste inacessível)."
            )

    # 3. Validação de destinos contra os 6 canônicos
    destinos_presentes = set(painel["destino"].unique())
    destinos_desconhecidos = destinos_presentes - set(DESTINOS_CANONICOS_SEIS)
    if destinos_desconhecidos:
        raise ValueError(
            f"Destinos desconhecidos encontrados no painel: {sorted(destinos_desconhecidos)}"
        )

    # 4. Obtenção e validação do escopo (mesma regra estrita para arquivo ou dicionário direto)
    if escopo is None:
        escopo_validado = carregar_escopo_mvp()
    else:
        escopo_validado = validar_escopo_mvp(escopo)

    destinos_mvp = set(escopo_validado["destinos"])

    # 5. Validação de presença obrigatória dos 3 destinos
    destinos_faltantes = destinos_mvp - destinos_presentes
    if destinos_faltantes:
        raise ValueError(
            "Destinos obrigatórios do MVP ausentes no painel de entrada: "
            f"{sorted(destinos_faltantes)}"
        )

    # 6. Recorte sem alteração do input
    df_recortado = painel[painel["destino"].isin(destinos_mvp)].copy()

    # 7. Proibição de projeção vazia
    if df_recortado.empty:
        raise ValueError("Operação rejeitada: recorte resultou em painel vazio.")

    return df_recortado

    return df_recortado


def executar_recorte_cli(
    caminho_painel: str | Path,
    caminho_saida: str | Path,
    caminho_escopo: str | Path | None = None,
) -> tuple[Path, Path]:
    """Executa o recorte via CLI com validação antecipada e manifesto determinístico."""
    p_saida = Path(caminho_saida)
    if p_saida.exists():
        raise FileExistsError(
            f"Arquivo de saída já existente: '{p_saida}'. "
            "Sobrescrita é proibida para preservar integridade histórica."
        )

    p_manifesto = p_saida.with_suffix(".json")
    if p_manifesto.exists():
        raise FileExistsError(
            f"Manifesto de saída já existente: '{p_manifesto}'. "
            "Sobrescrita é proibida."
        )

    p_painel = Path(caminho_painel)
    if not p_painel.exists():
        raise FileNotFoundError(f"Painel de entrada não encontrado: '{p_painel}'")

    bytes_input = p_painel.read_bytes()
    sha256_input = hashlib.sha256(bytes_input).hexdigest()

    escopo = carregar_escopo_mvp(caminho_escopo)

    df_in = pd.read_parquet(p_painel)
    df_out = recortar_painel_mvp(df_in, escopo=escopo)

    # Contagem de linhas por partição temporal
    comps_out = df_out["competencia"].astype(str)
    linhas_particao = {
        "historico_2020": int((comps_out < "202101").sum()),
        "treino_202101_202409": int(((comps_out >= "202101") & (comps_out <= "202409")).sum()),
        "embargo_202410_202412": int(((comps_out >= "202410") & (comps_out <= "202412")).sum()),
        "validacao_202501_202509": int(((comps_out >= "202501") & (comps_out <= "202509")).sum()),
        "total": len(df_out),
    }

    intervalo_origens = {
        "inicio": str(comps_out.min()),
        "fim": str(comps_out.max()),
    }

    # Gravação do Parquet de saída
    p_saida.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_parquet(p_saida, index=False)
    sha256_output = hashlib.sha256(p_saida.read_bytes()).hexdigest()

    data_utc = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    manifesto = {
        "decisao": escopo["decisao"],
        "destinos": escopo["destinos"],
        "sha256_input": sha256_input,
        "sha256_output": sha256_output,
        "sha256_escopo": escopo["sha256_escopo"],
        "hash_recorte": escopo["hash_recorte"],
        "intervalo_origens": intervalo_origens,
        "inicio_treino": "202101",
        "linhas_por_particao": linhas_particao,
        "data_utc": data_utc,
        "versoes": {
            "pandas": str(pd.__version__),
            "numpy": str(np.__version__),
            "pyarrow": str(pa.__version__),
        },
    }

    p_manifesto.write_text(
        json.dumps(manifesto, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return p_saida, p_manifesto


def main() -> None:
    """Ponto de entrada da CLI para recorte do painel MVP."""
    parser = argparse.ArgumentParser(
        description="Recorte do painel de desenvolvimento para o escopo MVP R29."
    )
    parser.add_argument("--painel", required=True, help="Caminho do Parquet de desenvolvimento.")
    parser.add_argument("--saida", required=True, help="Caminho do arquivo Parquet de saída.")
    parser.add_argument(
        "--escopo",
        default=None,
        help="Caminho opcional para o JSON de escopo MVP (padrão: app/catalogo/escopo_mvp.json).",
    )

    args = parser.parse_args()

    try:
        p_saida, p_manifesto = executar_recorte_cli(
            caminho_painel=args.painel,
            caminho_saida=args.saida,
            caminho_escopo=args.escopo,
        )
        print("=== Recorte MVP R29 Concluído ===")
        print(f"Parquet gravado em: {p_saida}")
        print(f"Manifesto gravado em: {p_manifesto}")
    except Exception as exc:
        print(f"Erro no recorte do painel MVP: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
