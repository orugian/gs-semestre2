"""Repositorio Oracle para sessao de laboratorio (S14)."""

import logging
from datetime import UTC, datetime
from typing import Any

from citizentech.banco.conexao import ErroBancoIndisponivel, obter_conexao

logger = logging.getLogger("citizentech.laboratorio.repositorio")


class ConflitoCodigoSessao(Exception):
    """Excecao para colisao de codigo unico de sessao."""


def _formatar_iso_utc(dt: Any) -> str | None:
    """Garante formatacao UTC ISO-8601 com 'Z'."""
    if dt is None:
        return None
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        else:
            dt = dt.astimezone(UTC)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return str(dt)


def _garantir_datetime_utc(dt: Any) -> datetime:
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
    parsed = datetime.fromisoformat(str(dt).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def criar_sessao_oracle(
    sessao_id: str,
    usuario_id: str,
    codigo: str,
    criado_em: datetime,
    expira_em: datetime,
) -> dict[str, Any]:
    """Cria nova sessao ativa encerrando sessao ativa anterior do mesmo usuario."""
    import oracledb

    try:
        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                # 1. Encerra qualquer sessao ativa anterior do usuario
                sql_encerrar = """
                UPDATE sessao_laboratorio
                SET status = 'encerrada'
                WHERE usuario_id = :usuario_id AND status = 'ativa'
                """
                cursor.execute(sql_encerrar, {"usuario_id": usuario_id})

                # 2. Insere a nova sessao ativa
                sql_inserir = """
                INSERT INTO sessao_laboratorio (
                    id, usuario_id, codigo, status, criado_em, expira_em,
                    relato_redigido, relato_status, relato_evento_id
                ) VALUES (
                    :id, :usuario_id, :codigo, 'ativa', :criado_em, :expira_em,
                    NULL, 'nenhum', NULL
                )
                """
                cursor.setinputsizes(
                    criado_em=oracledb.DB_TYPE_TIMESTAMP_TZ,
                    expira_em=oracledb.DB_TYPE_TIMESTAMP_TZ,
                )
                try:
                    cursor.execute(
                        sql_inserir,
                        {
                            "id": sessao_id,
                            "usuario_id": usuario_id,
                            "codigo": codigo,
                            "criado_em": criado_em,
                            "expira_em": expira_em,
                        },
                    )
                except oracledb.DatabaseError as err:
                    if "ORA-00001" in str(err):
                        raise ConflitoCodigoSessao(f"Codigo {codigo} ja existe.") from err
                    raise
    except ConflitoCodigoSessao:
        raise
    except oracledb.Error as err:
        raise ErroBancoIndisponivel() from err
    except Exception as err:
        if isinstance(err, ErroBancoIndisponivel):
            raise
        raise ErroBancoIndisponivel() from err

    return {
        "id": sessao_id,
        "usuario_id": usuario_id,
        "codigo": codigo,
        "status": "ativa",
        "criado_em": _formatar_iso_utc(criado_em),
        "expira_em": _formatar_iso_utc(expira_em),
        "criado_em_dt": criado_em,
        "expira_em_dt": expira_em,
        "relato_redigido": None,
        "relato_status": "nenhum",
        "relato_evento_id": None,
    }


def buscar_sessao_ativa_usuario(usuario_id: str) -> dict[str, Any] | None:
    """Busca a sessao ativa e nao expirada mais recente do usuario."""
    import oracledb

    sql = """
    SELECT id, usuario_id, codigo, status, criado_em, expira_em,
           relato_redigido, relato_status, relato_evento_id
    FROM sessao_laboratorio
    WHERE usuario_id = :usuario_id AND status = 'ativa' AND expira_em > :agora
    ORDER BY criado_em DESC
    FETCH FIRST 1 ROWS ONLY
    """
    agora = datetime.now(UTC)

    try:
        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                cursor.setinputsizes(agora=oracledb.DB_TYPE_TIMESTAMP_TZ)
                cursor.execute(sql, {"usuario_id": usuario_id, "agora": agora})
                linha = cursor.fetchone()
                if not linha:
                    return None
                return {
                    "id": linha[0],
                    "usuario_id": linha[1],
                    "codigo": linha[2],
                    "status": linha[3],
                    "criado_em": _formatar_iso_utc(linha[4]),
                    "expira_em": _formatar_iso_utc(linha[5]),
                    "criado_em_dt": _garantir_datetime_utc(linha[4]),
                    "expira_em_dt": _garantir_datetime_utc(linha[5]),
                    "relato_redigido": linha[6],
                    "relato_status": linha[7],
                    "relato_evento_id": linha[8],
                }
    except oracledb.Error as err:
        raise ErroBancoIndisponivel() from err
    except Exception as err:
        if isinstance(err, ErroBancoIndisponivel):
            raise
        raise ErroBancoIndisponivel() from err


def buscar_sessao_por_id_e_usuario(sessao_id: str, usuario_id: str) -> dict[str, Any] | None:
    """Busca sessao por id pertencente ao usuario (T14)."""
    import oracledb

    sql = """
    SELECT id, usuario_id, codigo, status, criado_em, expira_em,
           relato_redigido, relato_status, relato_evento_id
    FROM sessao_laboratorio
    WHERE id = :id AND usuario_id = :usuario_id
    """

    try:
        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(sql, {"id": sessao_id, "usuario_id": usuario_id})
                linha = cursor.fetchone()
                if not linha:
                    return None
                return {
                    "id": linha[0],
                    "usuario_id": linha[1],
                    "codigo": linha[2],
                    "status": linha[3],
                    "criado_em": _formatar_iso_utc(linha[4]),
                    "expira_em": _formatar_iso_utc(linha[5]),
                    "criado_em_dt": _garantir_datetime_utc(linha[4]),
                    "expira_em_dt": _garantir_datetime_utc(linha[5]),
                    "relato_redigido": linha[6],
                    "relato_status": linha[7],
                    "relato_evento_id": linha[8],
                }
    except oracledb.Error as err:
        raise ErroBancoIndisponivel() from err
    except Exception as err:
        if isinstance(err, ErroBancoIndisponivel):
            raise
        raise ErroBancoIndisponivel() from err


def salvar_relato_pendente(
    sessao_id: str,
    usuario_id: str,
    texto_redigido: str,
) -> tuple[str, str]:
    """Atualiza relato na sessao. Retorna (status_sessao, relato_status).

    Lanca KeyError se sessao nao encontrada para o usuario.
    """
    import oracledb

    sql_consulta = """
    SELECT status, expira_em, relato_status
    FROM sessao_laboratorio
    WHERE id = :id AND usuario_id = :usuario_id
    """

    sql_update = """
    UPDATE sessao_laboratorio
    SET relato_redigido = :texto_redigido, relato_status = 'pendente'
    WHERE id = :id AND usuario_id = :usuario_id
    """

    try:
        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(sql_consulta, {"id": sessao_id, "usuario_id": usuario_id})
                linha = cursor.fetchone()
                if not linha:
                    raise KeyError("Sessao nao encontrada.")

                status_atual = linha[0]
                expira_em = _garantir_datetime_utc(linha[1])
                relato_status_atual = linha[2]

                agora = datetime.now(UTC)
                expirada = expira_em <= agora
                if status_atual == "encerrada" or expirada:
                    return ("encerrada_ou_expirada", relato_status_atual)

                if relato_status_atual == "enviado":
                    return ("ativa", "enviado")

                cursor.execute(
                    sql_update,
                    {
                        "texto_redigido": texto_redigido,
                        "id": sessao_id,
                        "usuario_id": usuario_id,
                    },
                )
                return ("ativa", "pendente")
    except KeyError:
        raise
    except oracledb.Error as err:
        raise ErroBancoIndisponivel() from err
    except Exception as err:
        if isinstance(err, (KeyError, ErroBancoIndisponivel)):
            raise
        raise ErroBancoIndisponivel() from err


def buscar_relato_pendente_sessao_ativa(codigo: str) -> str | None:
    """Busca texto do relato pendente se a sessao estiver ativa e nao expirada.

    Falha silenciosamente retornando None em caso de indisponibilidade ou ausencia do banco.
    """
    try:
        import oracledb
        agora = datetime.now(UTC)
        sql = """
        SELECT relato_redigido
        FROM sessao_laboratorio
        WHERE codigo = :codigo
          AND status = 'ativa'
          AND expira_em > :agora
          AND relato_status = 'pendente'
          AND relato_redigido IS NOT NULL
        """
        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                cursor.setinputsizes(agora=oracledb.DB_TYPE_TIMESTAMP_TZ)
                cursor.execute(sql, {"codigo": codigo, "agora": agora})
                linha = cursor.fetchone()
                if linha and linha[0]:
                    return str(linha[0])
                return None
    except Exception as err:
        logger.debug("Falha ao consultar relato de sessao ativa: %s", type(err).__name__)
        return None


def marcar_relato_enviado(codigo: str, evento_id: str) -> bool:
    """Marca o relato da sessao como enviado associando ao evento_id da leitura.

    Falha silenciosamente retornando False em caso de erro.
    """
    try:
        sql = """
        UPDATE sessao_laboratorio
        SET relato_status = 'enviado', relato_evento_id = :evento_id
        WHERE codigo = :codigo AND relato_status = 'pendente'
        """
        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(sql, {"codigo": codigo, "evento_id": evento_id})
                return cursor.rowcount > 0
    except Exception as err:
        logger.debug("Falha ao marcar relato como enviado: %s", type(err).__name__)
        return False
