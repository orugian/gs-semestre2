"""Repositorio de persistencia CSV em modo isolado CTP.

Garante lock de filesystem e memoria, escrita atomica por linha, fsync antes de confirmar,
validacao estrita de integridade contra corrupcao (HTTP 503) e recuperacao conservadora
sem perda de dados preexistentes.
"""

import csv
import math
import os
import re
import threading
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

import portalocker

from citizentech.erros import ErroArmazenamento
from citizentech.limiares import carregar_limiares, classificar_risco

_MEM_LOCK = threading.RLock()
_ID_REGEX = re.compile(r"^[\w\-.:]{1,64}$")

COLUNAS = [
    "evento_id",
    "dispositivo_id",
    "sessao_laboratorio_id",
    "ciclo_id",
    "tipo_dispositivo",
    "metrica",
    "unidade",
    "valor",
    "risco",
    "alerta",
    "estado",
    "medido_em",
    "criado_em",
]


def obter_caminho_csv() -> Path:
    caminho_direto = os.environ.get("CITIZENTECH_LEITURAS_CSV")
    if caminho_direto:
        return Path(caminho_direto)

    diretorio_dados = os.environ.get("CITIZENTECH_DADOS")
    if diretorio_dados:
        return Path(diretorio_dados) / "runtime" / "leituras.csv"

    raise ErroArmazenamento(
        "Destino de dados nao configurado (CITIZENTECH_DADOS ou CITIZENTECH_LEITURAS_CSV)."
    )


@contextmanager
def _obter_lock_exclusivo(caminho: Path) -> Generator[None, None, None]:
    if caminho.is_dir():
        raise ErroArmazenamento("Destino de armazenamento invalido: caminho aponta para diretorio.")

    try:
        caminho.parent.mkdir(parents=True, exist_ok=True)
    except Exception as err:
        raise ErroArmazenamento("Falha ao inicializar diretorio de armazenamento.") from err

    lock_file = caminho.parent / f".{caminho.name}.lock"
    with _MEM_LOCK:
        try:
            with portalocker.Lock(lock_file, timeout=10):
                yield
        except ErroArmazenamento:
            raise
        except Exception as err:
            raise ErroArmazenamento("Falha de bloqueio de arquivo no armazenamento.") from err


def _validar_iso_com_tz(data_str: str) -> None:
    if not isinstance(data_str, str) or not data_str:
        raise ValueError("Data ausente ou tipo incorreto.")
    normalizada = data_str.replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalizada)
    if dt.tzinfo is None:
        raise ValueError("Data sem timezone.")


def _validar_e_carregar_arquivo(caminho: Path) -> list[dict[str, Any]]:
    """Valida a integridade completa do arquivo CSV.

    Rejeita cabecalhos incompletos/fora de ordem, colunas extras/faltantes,
    linhas truncadas, NaN/Inf, metricas desconhecidas, classificacoes inconsistentes
    e datas invalidas.
    """
    if not caminho.exists() or caminho.stat().st_size == 0:
        return []

    try:
        with open(caminho, newline="", encoding="utf-8") as f:
            conteudo = f.read()
    except Exception as err:
        raise ErroArmazenamento("Arquivo CSV corrompido: falha de leitura ou encoding.") from err

    if not conteudo.endswith(("\n", "\r\n")):
        raise ErroArmazenamento("Arquivo CSV corrompido: linha final truncada.")

    try:
        limiares = carregar_limiares()
        catalogo = limiares.get("metricas", {})
    except Exception as err:
        raise ErroArmazenamento("Falha ao carregar limiares para validacao do CSV.") from err

    linhas = list(csv.reader(conteudo.splitlines()))
    if not linhas:
        return []

    cabecalho = linhas[0]
    if cabecalho != COLUNAS:
        raise ErroArmazenamento(
            "Arquivo CSV corrompido: cabecalho invalido, incompleto ou fora de ordem."
        )

    registros: list[dict[str, Any]] = []
    for num_linha, linha in enumerate(linhas[1:], start=2):
        if len(linha) != len(COLUNAS):
            raise ErroArmazenamento(
                f"Arquivo CSV corrompido: quantidade incorreta de colunas na linha {num_linha}."
            )

        row = dict(zip(COLUNAS, linha, strict=True))

        # Validacao de identificadores e campos de texto
        if not row["evento_id"] or not _ID_REGEX.match(row["evento_id"]):
            raise ErroArmazenamento("Arquivo CSV corrompido: evento_id invalido.")
        if not row["dispositivo_id"] or not _ID_REGEX.match(row["dispositivo_id"]):
            raise ErroArmazenamento("Arquivo CSV corrompido: dispositivo_id invalido.")
        if row["ciclo_id"] and not _ID_REGEX.match(row["ciclo_id"]):
            raise ErroArmazenamento("Arquivo CSV corrompido: ciclo_id invalido.")
        if row["sessao_laboratorio_id"] and not _ID_REGEX.match(row["sessao_laboratorio_id"]):
            raise ErroArmazenamento("Arquivo CSV corrompido: sessao_laboratorio_id invalido.")
        if not row["tipo_dispositivo"] or not _ID_REGEX.match(row["tipo_dispositivo"]):
            raise ErroArmazenamento("Arquivo CSV corrompido: tipo_dispositivo invalido.")

        metrica = row["metrica"]
        if metrica not in catalogo:
            raise ErroArmazenamento("Arquivo CSV corrompido: metrica desconhecida.")

        unidade_esperada = catalogo[metrica]["unidade"]
        if row["unidade"] != unidade_esperada:
            raise ErroArmazenamento("Arquivo CSV corrompido: unidade incompativel.")

        # Validacao de valor
        try:
            valor_num = float(row["valor"])
        except ValueError as err:
            raise ErroArmazenamento("Arquivo CSV corrompido: valor nao numerico.") from err

        if not math.isfinite(valor_num):
            raise ErroArmazenamento("Arquivo CSV corrompido: valor NaN ou Infinito.")

        if metrica == "temperatura_c" and valor_num == -127.0:
            raise ErroArmazenamento("Arquivo CSV corrompido: leitura com falha de sensor (-127).")

        valor_min = catalogo[metrica].get("valor_minimo")
        if valor_min is not None and valor_num < valor_min:
            raise ErroArmazenamento("Arquivo CSV corrompido: valor abaixo do minimo permitido.")

        # Classificacao consistente
        try:
            risco_calculado = classificar_risco(metrica, valor_num, limiares=limiares)
        except Exception as err:
            raise ErroArmazenamento("Arquivo CSV corrompido: erro ao classificar risco.") from err

        if row["risco"] != risco_calculado:
            raise ErroArmazenamento(
                "Arquivo CSV corrompido: classificacao de risco incoerente com o valor."
            )

        alerta_esperado = risco_calculado in ("atencao", "critico")
        if row["alerta"] not in ("True", "False", "true", "false", "1", "0"):
            raise ErroArmazenamento("Arquivo CSV corrompido: campo alerta invalido.")
        alerta_bool = row["alerta"].lower() in ("true", "1")
        if alerta_bool != alerta_esperado:
            raise ErroArmazenamento(
                "Arquivo CSV corrompido: status de alerta incoerente com o risco."
            )

        if row["estado"] != "pendente_nuvem":
            raise ErroArmazenamento("Arquivo CSV corrompido: estado invalido.")

        try:
            _validar_iso_com_tz(row["medido_em"])
            _validar_iso_com_tz(row["criado_em"])
        except Exception as err:
            raise ErroArmazenamento("Arquivo CSV corrompido: timestamp ISO invalido.") from err

        registros.append({
            "evento_id": row["evento_id"],
            "dispositivo_id": row["dispositivo_id"],
            "sessao_laboratorio_id": row["sessao_laboratorio_id"],
            "ciclo_id": row["ciclo_id"],
            "tipo_dispositivo": row["tipo_dispositivo"],
            "metrica": metrica,
            "unidade": row["unidade"],
            "valor": valor_num,
            "risco": row["risco"],
            "alerta": alerta_bool,
            "estado": row["estado"],
            "medido_em": row["medido_em"],
            "criado_em": row["criado_em"],
        })

    return registros


def salvar_leitura(registro: dict[str, Any], caminho: Path | None = None) -> None:
    """Grava o registro no CSV com append atomico, validacao previa e fsync."""
    if caminho is None:
        caminho = obter_caminho_csv()

    with _obter_lock_exclusivo(caminho):
        # 1. Valida se arquivo existente esta integro. Se corrompido, 503 sem alterar bytes.
        if caminho.exists() and caminho.stat().st_size > 0:
            _validar_e_carregar_arquivo(caminho)

        tamanho_original = caminho.stat().st_size if caminho.exists() else 0
        arquivo_novo = tamanho_original == 0

        try:
            with open(caminho, mode="a", newline="", encoding="utf-8") as arquivo:
                escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS)
                if arquivo_novo:
                    escritor.writeheader()
                escritor.writerow({col: registro.get(col, "") for col in COLUNAS})
                arquivo.flush()
                os.fsync(arquivo.fileno())
        except Exception as err:
            # Recuperacao conservadora: se falhar o append/fsync,
            # restaura estado anterior sem apagar preexistente
            try:
                if arquivo_novo:
                    if caminho.exists():
                        caminho.unlink(missing_ok=True)
                else:
                    with open(caminho, mode="r+b") as f_rollback:
                        f_rollback.seek(tamanho_original)
                        f_rollback.truncate()
                        f_rollback.flush()
                        os.fsync(f_rollback.fileno())
            except Exception:
                pass
            raise ErroArmazenamento(
                f"Falha na gravacao duravel do arquivo CSV: {type(err).__name__}"
            ) from err


def ler_todas_leituras(caminho: Path | None = None) -> list[dict[str, Any]]:
    """Le todos os registros do arquivo CSV, validando cabecalho e integridade estrita."""
    if caminho is None:
        caminho = obter_caminho_csv()

    with _obter_lock_exclusivo(caminho):
        return _validar_e_carregar_arquivo(caminho)
