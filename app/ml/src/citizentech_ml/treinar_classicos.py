"""CLI e gerenciamento de artefatos dos modelos clássicos (S7-classicos).

Implementa persistência auditável com manifesto de integridade e loader seguro.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn

from citizentech_ml.classicos import treinar_classicos

ARTEFATOS_OBRIGATORIOS: set[str] = {
    "modelos.joblib",
    "previsoes.parquet",
    "previsoes.csv",
    "metricas.json",
}


def _converter_para_serializavel(obj: Any) -> Any:
    """Converte tipos numpy, conjuntos e caminhos para tipos nativos serializáveis em JSON."""
    if isinstance(obj, dict):
        return {str(k): _converter_para_serializavel(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_converter_para_serializavel(v) for v in obj]
    if isinstance(obj, set):
        return sorted([_converter_para_serializavel(v) for v in obj])
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return _converter_para_serializavel(obj.tolist())
    if isinstance(obj, Path):
        return str(obj)
    return obj


def salvar_artefatos_classicos(
    resultado: Any,
    caminho_painel: str | Path,
    dir_saida: str | Path,
    seed: int = 42,
    n_iter: int = 6,
) -> Path:
    """Grava estimadores, previsões, relatório e manifesto com verificação SHA256 estrita."""
    dir_s = Path(dir_saida)
    if dir_s.exists():
        raise FileExistsError(f"Diretório de saída já existente: {dir_s}")

    dir_s.mkdir(parents=True, exist_ok=False)

    p_painel = Path(caminho_painel)
    sha256_painel = (
        hashlib.sha256(p_painel.read_bytes()).hexdigest() if p_painel.exists() else None
    )

    # 1. Salvar modelos joblib
    p_modelos = dir_s / "modelos.joblib"
    joblib.dump(resultado["estimadores"], p_modelos)
    hash_modelos = hashlib.sha256(p_modelos.read_bytes()).hexdigest()

    # 2. Salvar previsões Parquet e CSV
    df_previsoes: pd.DataFrame = resultado["previsoes"]
    p_prev_parquet = dir_s / "previsoes.parquet"
    p_prev_csv = dir_s / "previsoes.csv"
    df_previsoes.to_parquet(p_prev_parquet, index=False)
    df_previsoes.to_csv(p_prev_csv, index=False, encoding="utf-8")
    hash_prev_parquet = hashlib.sha256(p_prev_parquet.read_bytes()).hexdigest()
    hash_prev_csv = hashlib.sha256(p_prev_csv.read_bytes()).hexdigest()

    # 3. Salvar métricas JSON serializáveis
    p_metricas = dir_s / "metricas.json"
    relatorio_serializavel = _converter_para_serializavel(resultado["relatorio"])
    conteudo_metricas = json.dumps(relatorio_serializavel, indent=2, ensure_ascii=False) + "\n"
    p_metricas.write_text(conteudo_metricas, encoding="utf-8")
    hash_metricas = hashlib.sha256(p_metricas.read_bytes()).hexdigest()

    # 4. Gravar manifesto com hashes de todos os artefatos gerados
    data_utc = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    hash_recorte = relatorio_serializavel.get("recorte", {}).get("hash_recorte")
    sha256_escopo = relatorio_serializavel.get("recorte", {}).get("sha256_escopo")

    manifesto = {
        "versao_manifesto": "1.0",
        "sha256_painel": sha256_painel,
        "caminho_painel": str(p_painel.resolve()) if p_painel.exists() else str(p_painel),
        "data_utc": data_utc,
        "seed": seed,
        "n_iter": n_iter,
        "hash_recorte": hash_recorte,
        "sha256_escopo": sha256_escopo,
        "recorte": relatorio_serializavel.get("recorte", {}),
        "versoes": {
            "python": sys.version,
            "sklearn": sklearn.__version__,
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "joblib": joblib.__version__,
            "plataforma": platform.platform(),
        },
        "arquivos": {
            "modelos.joblib": hash_modelos,
            "previsoes.parquet": hash_prev_parquet,
            "previsoes.csv": hash_prev_csv,
            "metricas.json": hash_metricas,
        },
    }

    p_manifesto = dir_s / "manifesto.json"
    p_manifesto.write_text(
        json.dumps(manifesto, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return dir_s


def carregar_artefatos_classicos(diretorio: str | Path) -> dict[str, Any]:
    """Carrega artefatos verificando rigorosamente os hashes antes da desserialização.

    Aviso de segurança (Integridade vs Autenticidade):
    Este loader valida exclusivamente a integridade local (detecção de corrupção ou
    adulteração acidental) de artefatos próprios gravados em diretório confiável.
    Ele NÃO confere autenticidade criptográfica nem protege contra um adversário
    que possa substituir o arquivo de manifesto juntamente com os artefatos.
    A desserialização de modelos via joblib/pickle pode executar código Python arbitrário;
    portanto, NUNCA utilize este loader em artefatos provenientes de fontes não confiáveis.
    """
    dir_p = Path(diretorio)
    if not dir_p.exists() or not dir_p.is_dir():
        raise FileNotFoundError(f"Diretório não encontrado: {dir_p}")

    p_manifesto = dir_p / "manifesto.json"
    if not p_manifesto.exists():
        raise FileNotFoundError(
            f"Manifesto não encontrado em '{p_manifesto}'. "
            "Recusando desserialização de artefatos sem manifesto de integridade."
        )

    with p_manifesto.open("r", encoding="utf-8") as f:
        try:
            manifesto = json.load(f)
        except json.JSONDecodeError as err:
            raise ValueError(f"Manifesto JSON inválido ou corrompido: {err}") from err

    if not isinstance(manifesto, dict):
        raise ValueError("Manifesto inválido: JSON de nível superior deve ser um objeto.")

    versao = manifesto.get("versao_manifesto")
    if versao != "1.0":
        raise ValueError(f"Manifesto com versão desconhecida ou ausente: {versao!r}")

    arquivos_declarados = manifesto.get("arquivos")
    if not isinstance(arquivos_declarados, dict):
        raise ValueError("Manifesto inválido: campo 'arquivos' ausente ou inválido.")

    chaves_declaradas = set(arquivos_declarados.keys())
    faltantes = ARTEFATOS_OBRIGATORIOS - chaves_declaradas
    if faltantes:
        raise ValueError(
            f"Manifesto inválido: omissão de artefatos obrigatórios: {sorted(faltantes)}"
        )

    extras = chaves_declaradas - ARTEFATOS_OBRIGATORIOS
    if extras:
        raise ValueError(
            f"Manifesto inválido: artefatos extras ou desconhecidos no manifesto: {sorted(extras)}"
        )

    # Validação estrita de cada entrada no manifesto
    for nome_arq, hash_esperado in arquivos_declarados.items():
        if not isinstance(nome_arq, str) or not nome_arq.strip():
            raise ValueError(f"Manifesto contém nome de arquivo inválido: {nome_arq!r}")

        p_nome = Path(nome_arq)
        if (
            p_nome.is_absolute()
            or ".." in nome_arq
            or "/" in nome_arq
            or "\\" in nome_arq
            or p_nome.name != nome_arq
        ):
            raise ValueError(f"Manifesto contém caminho inseguro ou inválido: {nome_arq!r}")

        if (
            not isinstance(hash_esperado, str)
            or len(hash_esperado) != 64
            or not all(c in "0123456789abcdefABCDEF" for c in hash_esperado)
        ):
            raise ValueError(
                f"Manifesto contém hash SHA-256 inválido para '{nome_arq}': {hash_esperado!r}"
            )

    # Verificação estrita de hash ANTES de qualquer leitura/desserialização
    for nome_arq in sorted(ARTEFATOS_OBRIGATORIOS):
        hash_esperado = arquivos_declarados[nome_arq]
        caminho_arq = dir_p / nome_arq
        if not caminho_arq.exists() or not caminho_arq.is_file():
            raise FileNotFoundError(
                f"Artefato obrigatório '{nome_arq}' ausente no disco: {caminho_arq}"
            )
        hash_calculado = hashlib.sha256(caminho_arq.read_bytes()).hexdigest()
        if hash_calculado.lower() != hash_esperado.lower():
            raise ValueError(
                f"Falha de integridade: hash do arquivo '{nome_arq}' ({hash_calculado}) "
                f"diverge do esperado no manifesto ({hash_esperado}). "
                "Desserialização rejeitada por risco de adulteração."
            )

    # Carregar com segurança após validação completa de integridade
    modelos = joblib.load(dir_p / "modelos.joblib")
    previsoes = pd.read_parquet(dir_p / "previsoes.parquet")
    with (dir_p / "metricas.json").open("r", encoding="utf-8") as f:
        relatorio = json.load(f)

    return {
        "manifesto": manifesto,
        "estimadores": modelos,
        "modelos": modelos,
        "previsoes": previsoes,
        "relatorio": relatorio,
    }


def main() -> None:
    """Ponto de entrada da CLI para treinar_classicos."""
    parser = argparse.ArgumentParser(
        description="Treinamento e validação de modelos clássicos com busca temporal."
    )
    parser.add_argument(
        "--painel",
        required=True,
        help="Caminho do arquivo Parquet do painel de desenvolvimento.",
    )
    parser.add_argument(
        "--saida",
        required=True,
        help="Caminho do diretório de saída (não pode existir previamente).",
    )
    parser.add_argument(
        "--validacao",
        action="store_true",
        help="Inclui avaliação na partição de validação (202501-202509).",
    )
    parser.add_argument(
        "--n-iter",
        type=int,
        default=6,
        help="Número de iterações no RandomizedSearchCV (default 6).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Semente fixa para reproduzibilidade (default 42).",
    )
    parser.add_argument(
        "--n-splits",
        type=int,
        default=3,
        help="Número de folds temporais com embargo (default 3).",
    )

    args = parser.parse_args()

    caminho_saida = Path(args.saida)
    if caminho_saida.exists():
        raise FileExistsError(
            f"Diretório de saída já existente: '{caminho_saida}'. "
            "A CLI recusa sobrescrever diretórios para garantir imutabilidade dos artefatos."
        )

    p_painel = Path(args.painel)
    if not p_painel.exists():
        raise FileNotFoundError(f"Arquivo do painel não encontrado: {p_painel}")

    df_painel = pd.read_parquet(p_painel)

    resultado = treinar_classicos(
        painel=df_painel,
        seed=args.seed,
        n_iter=args.n_iter,
        incluir_validacao=args.validacao,
        n_splits=args.n_splits,
    )

    salvar_artefatos_classicos(
        resultado=resultado,
        caminho_painel=args.painel,
        dir_saida=caminho_saida,
        seed=args.seed,
        n_iter=args.n_iter,
    )

    print(f"Treinamento clássico concluído com sucesso. Artefatos gravados em: {caminho_saida}")


if __name__ == "__main__":
    main()
