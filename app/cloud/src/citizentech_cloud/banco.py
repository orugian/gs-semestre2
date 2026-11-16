"""Modulo de conexao ao RDS PostgreSQL e operacoes da tabela ocorrencias."""

import hashlib
import json
import logging
import os
import ssl
from pathlib import Path

import pg8000.dbapi

logger = logging.getLogger("citizentech_cloud.banco")


class LimiteExcedidoError(Exception):
    """Lancada quando a taxa de requisicoes por dispositivo no minuto e excedida."""


class ConflitoEventoError(Exception):
    """Lancada quando um evento_id ja existe com conteudo diferente (HTTP 409)."""


class BancoIndisponivelError(Exception):
    """Lancada quando ha falha de conexao ou persistencia no banco (HTTP 503)."""


def eh_erro_unique_violation(e: Exception) -> bool:
    """Verifica se a excecao do banco e uma UniqueViolation (codigo 23505).

    Suporta o dicionario estruturado nativo do pg8000 ({'C': '23505', ...})
    e strings contendo o codigo de erro.
    """
    if not e.args:
        return False
    primeiro = e.args[0]
    if isinstance(primeiro, dict):
        return primeiro.get("C") == "23505"
    if isinstance(primeiro, str):
        return "23505" in primeiro
    return "23505" in str(e)


def calcular_hash_conteudo(dados: dict) -> str:
    """Calcula o SHA-256 do JSON canonico para deteccao de duplicata ou conflito."""
    canon = {
        "ciclo_id": dados.get("ciclo_id"),
        "dispositivo_id": dados.get("dispositivo_id"),
        "medido_em": dados.get("medido_em"),
        "metrica": dados.get("metrica"),
        "sessao_laboratorio_id": dados.get("sessao_laboratorio_id"),
        "tipo_dispositivo": dados.get("tipo_dispositivo"),
        "unidade": dados.get("unidade"),
        "valor": float(dados["valor"]),
    }
    canon_json = json.dumps(canon, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon_json.encode("utf-8")).hexdigest()


def montar_config_conexao() -> dict:
    """Monta os parametros de conexao com pg8000 respeitando D09/D09a."""
    user = os.environ.get("DB_USER", "postgres")
    password = os.environ.get("DB_PASSWORD", "")
    host = os.environ.get("DB_HOST", "localhost")
    port = int(os.environ.get("DB_PORT", "5432"))
    database = os.environ.get("DB_NAME", "citizentech")
    sslmode = os.environ.get("DB_SSLMODE", "verify-full")

    ssl_context = None
    if sslmode == "disable":
        ssl_context = None
    else:
        cafile = os.environ.get("DB_SSLROOTCERT")
        if not cafile:
            bundle_local = Path(__file__).resolve().parent / "global-bundle.pem"
            if bundle_local.is_file():
                cafile = str(bundle_local)
        if not cafile or not Path(cafile).is_file():
            logger.error("bundle CA ausente para SSL (DB_SSLMODE=%s)", sslmode)
            raise BancoIndisponivelError("bundle CA ausente para conexao segura com o banco")
        ssl_context = ssl.create_default_context(cafile=cafile)
        ssl_context.check_hostname = True

    return {
        "user": user,
        "password": password,
        "host": host,
        "port": port,
        "database": database,
        "ssl_context": ssl_context,
        "timeout": 10,
    }


def obter_conexao():
    """Abre uma conexao com o PostgreSQL."""
    config = montar_config_conexao()
    if config["host"] == "localhost":
        config["host"] = "127.0.0.1"
    try:
        return pg8000.dbapi.connect(**config)
    except Exception as e:
        # SQLSTATE (ex.: 28P01 senha, 3D000 banco inexistente) diagnostica sem expor segredo
        sqlstate = e.args[0].get("C") if e.args and isinstance(e.args[0], dict) else None
        logger.error(
            "Erro ao conectar ao banco de dados: %s sqlstate=%s", type(e).__name__, sqlstate
        )
        raise BancoIndisponivelError("Falha de conexao com o banco de dados") from e


def testar_conexao() -> bool:
    """Verifica se o banco responde (usado pelo /health)."""
    try:
        conn = obter_conexao()
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1")
            return True
        finally:
            conn.close()
    except Exception:
        return False


def verificar_rate_limit(conn, dispositivo_id: str, limite: int | None = None) -> None:
    """Verifica se o dispositivo excedeu o rate limit no RDS no ultimo minuto."""
    if limite is None:
        limite = int(os.environ.get("RATE_LIMIT_POR_MINUTO", "30"))

    cur = conn.cursor()
    sql_count = (
        "SELECT COUNT(*) FROM ocorrencias "
        "WHERE dispositivo_id = %s AND criado_em > NOW() - INTERVAL '1 minute'"
    )
    cur.execute(sql_count, (dispositivo_id,))
    row = cur.fetchone()
    total = row[0] if row else 0
    if total >= limite:
        raise LimiteExcedidoError(
            f"Limite de {limite} leituras/minuto excedido para dispositivo {dispositivo_id}"
        )


def inserir_ocorrencia(dados: dict) -> dict:
    """Insere ocorrencia tratando rate limit, idempotencia e conflitos.

    Retorna dict com {'id': ..., 'duplicata': True|False, 'novo': True|False}.
    """
    novo_hash = calcular_hash_conteudo(dados)
    evento_id = dados.get("evento_id")

    try:
        conn = obter_conexao()
    except Exception as e:
        raise BancoIndisponivelError("Banco de dados indisponivel") from e

    try:
        cur = conn.cursor()

        # 1. Se evento_id ja existe, verificar duplicata (200) ou conflito (409) antes do rate limit
        if evento_id:
            cur.execute(
                "SELECT id, hash_conteudo FROM ocorrencias WHERE evento_id = %s",
                (evento_id,),
            )
            row = cur.fetchone()
            if row:
                existente_id, existente_hash = row
                if existente_hash == novo_hash:
                    return {"id": existente_id, "duplicata": True, "novo": False}
                raise ConflitoEventoError("evento_id ja registrado com conteudo diferente")

        # 2. Lock transacional por dispositivo_id para evitar corrida no rate limit
        cur.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (dados["dispositivo_id"],))

        # 3. Checagem de rate limit no RDS
        verificar_rate_limit(conn, dados["dispositivo_id"])

        # 3. Insercao no banco
        sql_insert = """
            INSERT INTO ocorrencias (
                dispositivo_id, tipo_dispositivo, latitude, longitude,
                metrica, valor, relato, sentimento, confianca,
                nivel_risco, medido_em, evento_id, autenticado,
                unidade, sessao_laboratorio_id, ciclo_id, alerta,
                analise_status, hash_conteudo
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s
            ) RETURNING id
        """
        params = (
            dados["dispositivo_id"],
            dados.get("tipo_dispositivo") or "desconhecido",
            dados.get("latitude"),
            dados.get("longitude"),
            dados["metrica"],
            float(dados["valor"]),
            dados.get("relato"),
            dados.get("sentimento"),
            dados.get("confianca"),
            dados["nivel_risco"],
            dados.get("medido_em"),
            evento_id,
            bool(dados.get("autenticado", False)),
            dados.get("unidade"),
            dados.get("sessao_laboratorio_id"),
            dados.get("ciclo_id"),
            bool(dados.get("alerta", False)),
            dados.get("analise_status"),
            novo_hash,
        )

        try:
            cur.execute(sql_insert, params)
            novo_id = cur.fetchone()[0]
            conn.commit()
            return {"id": novo_id, "duplicata": False, "novo": True}
        except (pg8000.dbapi.DatabaseError, pg8000.exceptions.DatabaseError) as e:
            # Corrida de insercao: se erro for UniqueViolation (23505) em evento_id
            if eh_erro_unique_violation(e):
                conn.rollback()
                cur = conn.cursor()
                cur.execute(
                    "SELECT id, hash_conteudo FROM ocorrencias WHERE evento_id = %s",
                    (evento_id,),
                )
                row = cur.fetchone()
                if row:
                    existente_id, existente_hash = row
                    if existente_hash == novo_hash:
                        return {"id": existente_id, "duplicata": True, "novo": False}
                    msg_conflito = "evento_id ja registrado com conteudo diferente"
                    raise ConflitoEventoError(msg_conflito) from e
            conn.rollback()
            raise
    except (LimiteExcedidoError, ConflitoEventoError):
        raise
    except Exception as e:
        logger.error("Erro ao persistir ocorrencia no RDS: %s", type(e).__name__)
        raise BancoIndisponivelError("Falha ao gravar ocorrencia no RDS") from e
    finally:
        conn.close()


def listar_ocorrencias(limite: int = 20) -> list[dict]:
    """Lista as ultimas ocorrencias ordenadas por id DESC."""
    conn = obter_conexao()
    try:
        cur = conn.cursor()
        sql = """
            SELECT id, dispositivo_id, tipo_dispositivo, latitude, longitude,
                   metrica, valor, relato, sentimento, confianca,
                   nivel_risco, medido_em, criado_em, evento_id, autenticado,
                   unidade, sessao_laboratorio_id, ciclo_id, alerta, analise_status
            FROM ocorrencias
            ORDER BY id DESC
            LIMIT %s
        """
        cur.execute(sql, (limite,))
        colunas = [
            "id",
            "dispositivo_id",
            "tipo_dispositivo",
            "latitude",
            "longitude",
            "metrica",
            "valor",
            "relato",
            "sentimento",
            "confianca",
            "nivel_risco",
            "medido_em",
            "criado_em",
            "evento_id",
            "autenticado",
            "unidade",
            "sessao_laboratorio_id",
            "ciclo_id",
            "alerta",
            "analise_status",
        ]
        resultados = []
        for row in cur.fetchall():
            item = {}
            for col, val in zip(colunas, row, strict=False):
                if hasattr(val, "isoformat"):
                    item[col] = val.isoformat()
                elif hasattr(val, "__float__") and col == "confianca":
                    item[col] = float(val) if val is not None else None
                else:
                    item[col] = val
            resultados.append(item)
        return resultados
    finally:
        conn.close()
