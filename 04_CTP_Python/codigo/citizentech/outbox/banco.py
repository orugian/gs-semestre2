"""Persistencia SQLite para fila duravel da Outbox (Plano §2, D12a/R25)."""

import json
import os
import sqlite3
import threading
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from citizentech.erros import ErroArmazenamento

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS pendencias (
    evento_id TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    tentativas INTEGER NOT NULL DEFAULT 0,
    estado TEXT NOT NULL DEFAULT 'pendente_nuvem',
    ultimo_erro TEXT,
    atualizado_em TEXT NOT NULL,
    proxima_tentativa_em TEXT NOT NULL,
    criado_em TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pendencias_estado_proxima
    ON pendencias (estado, proxima_tentativa_em);
"""


def obter_caminho_outbox_db(caminho_csv: Path | None = None) -> Path:
    """Resolve o caminho do SQLite outbox.db.

    Ordem: CITIZENTECH_OUTBOX_DB; pasta do CSV recebido explicitamente; pasta de
    CITIZENTECH_LEITURAS_CSV; CITIZENTECH_DADOS/runtime. O banco fica sempre ao lado do CSV.
    """
    caminho_env = os.environ.get("CITIZENTECH_OUTBOX_DB")
    if caminho_env:
        return Path(caminho_env)

    if caminho_csv is not None:
        return Path(caminho_csv).parent / "outbox.db"

    caminho_csv = os.environ.get("CITIZENTECH_LEITURAS_CSV")
    if caminho_csv:
        return Path(caminho_csv).parent / "outbox.db"

    diretorio_dados = os.environ.get("CITIZENTECH_DADOS")
    if diretorio_dados:
        return Path(diretorio_dados) / "runtime" / "outbox.db"

    raise ErroArmazenamento("Destino de armazenamento outbox SQLite nao configurado.")


_BANCOS_INICIALIZADOS: set[str] = set()
_INIT_LOCK = threading.Lock()


def conectar_banco(caminho: Path | None = None) -> sqlite3.Connection:
    """Abre conexao isolada com SQLite em modo WAL e timeout estrito."""
    if caminho is None:
        caminho = obter_caminho_outbox_db()

    if caminho.is_dir():
        raise ErroArmazenamento("Destino de outbox invalido: caminho aponta para diretorio.")

    try:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(caminho), timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        conn.execute("PRAGMA synchronous = FULL;")
        return conn
    except ErroArmazenamento:
        raise
    except Exception as err:
        raise ErroArmazenamento(
            f"Falha ao conectar ao banco outbox SQLite: {type(err).__name__}"
        ) from err


@contextmanager
def transacao_banco(caminho: Path | None = None) -> Generator[sqlite3.Connection, None, None]:
    conn = conectar_banco(caminho)
    try:
        with conn:
            yield conn
    except ErroArmazenamento:
        raise
    except Exception as err:
        raise ErroArmazenamento(
            f"Falha na operacao SQLite do outbox: {type(err).__name__}"
        ) from err
    finally:
        conn.close()


def inicializar_banco(caminho: Path | None = None) -> None:
    """Cria tabelas e indices necessarios da outbox caso nao existam, apenas uma vez por caminho."""
    if caminho is None:
        caminho = obter_caminho_outbox_db()

    chave = str(caminho.resolve())
    if chave in _BANCOS_INICIALIZADOS and caminho.exists():
        return

    with _INIT_LOCK:
        if chave in _BANCOS_INICIALIZADOS and caminho.exists():
            return
        with transacao_banco(caminho) as conn:
            conn.executescript(SCHEMA_SQL)
        _BANCOS_INICIALIZADOS.add(chave)


def salvar_pendencia(registro: dict[str, Any], caminho: Path | None = None) -> None:
    """Insere ou atualiza um registro na fila da outbox."""
    inicializar_banco(caminho)
    agora = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    payload_json = json.dumps(registro, ensure_ascii=False)
    with transacao_banco(caminho) as conn:
        conn.execute(
            """
            INSERT INTO pendencias (
                evento_id, payload, tentativas, estado, ultimo_erro,
                atualizado_em, proxima_tentativa_em, criado_em
            ) VALUES (?, ?, 0, ?, NULL, ?, ?, ?)
            ON CONFLICT(evento_id) DO NOTHING
            """,
            (
                registro["evento_id"],
                payload_json,
                registro.get("estado", "pendente_nuvem"),
                agora,
                agora,
                registro.get("criado_em", agora),
            ),
        )


def obter_pendencia(evento_id: str, caminho: Path | None = None) -> dict[str, Any] | None:
    """Obtem um registro pendente da outbox pelo evento_id."""
    inicializar_banco(caminho)
    with transacao_banco(caminho) as conn:
        cursor = conn.execute(
            """
            SELECT evento_id, payload, tentativas, estado, ultimo_erro,
                   atualizado_em, proxima_tentativa_em, criado_em
            FROM pendencias WHERE evento_id = ?
            """,
            (evento_id,),
        )
        linha = cursor.fetchone()
        if not linha:
            return None
        payload = json.loads(linha["payload"])
        return {
            "evento_id": linha["evento_id"],
            "payload": payload,
            "tentativas": linha["tentativas"],
            "estado": linha["estado"],
            "ultimo_erro": linha["ultimo_erro"],
            "atualizado_em": linha["atualizado_em"],
            "proxima_tentativa_em": linha["proxima_tentativa_em"],
            "criado_em": linha["criado_em"],
        }


def obter_mapa_estados(caminho: Path | None = None) -> dict[str, str]:
    """Retorna dicionario evento_id -> estado para composicao rapida no GET /leituras."""
    if caminho is None:
        try:
            caminho = obter_caminho_outbox_db()
        except ErroArmazenamento:
            return {}

    if not caminho.exists():
        return {}

    with transacao_banco(caminho) as conn:
        cursor = conn.execute("SELECT evento_id, estado FROM pendencias")
        return {row["evento_id"]: row["estado"] for row in cursor.fetchall()}


def listar_pendencias_para_envio(
    limite: int = 50,
    agora: str | None = None,
    caminho: Path | None = None,
) -> list[dict[str, Any]]:
    """Lista eventos pendentes prontos para envio (estado pendente_nuvem e horario chegado)."""
    inicializar_banco(caminho)
    if agora is None:
        agora = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    with transacao_banco(caminho) as conn:
        cursor = conn.execute(
            """
            SELECT evento_id, payload, tentativas, estado, ultimo_erro,
                   atualizado_em, proxima_tentativa_em, criado_em
            FROM pendencias
            WHERE estado = 'pendente_nuvem' AND proxima_tentativa_em <= ?
            ORDER BY criado_em ASC
            LIMIT ?
            """,
            (agora, limite),
        )
        linhas = cursor.fetchall()
        resultados = []
        for linha in linhas:
            resultados.append({
                "evento_id": linha["evento_id"],
                "payload": json.loads(linha["payload"]),
                "tentativas": linha["tentativas"],
                "estado": linha["estado"],
                "ultimo_erro": linha["ultimo_erro"],
                "atualizado_em": linha["atualizado_em"],
                "proxima_tentativa_em": linha["proxima_tentativa_em"],
                "criado_em": linha["criado_em"],
            })
        return resultados


def atualizar_status_pendencia(
    evento_id: str,
    estado: str,
    tentativas: int,
    proxima_tentativa_em: str,
    ultimo_erro: str | None = None,
    caminho: Path | None = None,
) -> None:
    """Atualiza o resultado da tentativa de envio de uma pendencia."""
    agora = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    with transacao_banco(caminho) as conn:
        conn.execute(
            """
            UPDATE pendencias
            SET estado = ?, tentativas = ?, ultimo_erro = ?,
                atualizado_em = ?, proxima_tentativa_em = ?
            WHERE evento_id = ?
            """,
            (estado, tentativas, ultimo_erro, agora, proxima_tentativa_em, evento_id),
        )


def reconciliar_com_csv(caminho_csv: Path | None = None, caminho_db: Path | None = None) -> int:
    """Recupera pendencias orfas do CSV para a outbox idempotentemente no startup."""
    from citizentech.leituras.repositorio import ler_todas_leituras, obter_caminho_csv

    if caminho_csv is None:
        try:
            caminho_csv = obter_caminho_csv()
        except ErroArmazenamento:
            return 0

    if not caminho_csv.exists() or caminho_csv.stat().st_size == 0:
        return 0

    inicializar_banco(caminho_db)
    registros_csv = ler_todas_leituras(caminho_csv)
    if not registros_csv:
        return 0

    agora = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    reconciliados = 0

    with transacao_banco(caminho_db) as conn:
        for reg in registros_csv:
            cursor = conn.execute(
                "SELECT estado FROM pendencias WHERE evento_id = ?",
                (reg["evento_id"],),
            )
            existente = cursor.fetchone()
            if existente is None:
                payload_json = json.dumps(reg, ensure_ascii=False)
                conn.execute(
                    """
                    INSERT INTO pendencias (
                        evento_id, payload, tentativas, estado, ultimo_erro,
                        atualizado_em, proxima_tentativa_em, criado_em
                    ) VALUES (?, ?, 0, 'pendente_nuvem', NULL, ?, ?, ?)
                    """,
                    (reg["evento_id"], payload_json, agora, agora, reg["criado_em"]),
                )
                reconciliados += 1

    return reconciliados
