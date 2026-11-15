"""Repositorio de persistencia de usuarios no banco Oracle."""

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status

from citizentech.banco.conexao import ErroBancoIndisponivel, obter_conexao


def _formatar_iso_utc(dt: Any) -> str:
    """Garante formatacao UTC ISO-8601 com 'Z'."""
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        else:
            dt = dt.astimezone(UTC)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return str(dt)


def criar_usuario(email: str, senha_hash: str) -> dict[str, Any]:
    """Cria um novo usuario no banco Oracle garantindo unicidade pela constraint.

    Se houver violacao de unicidade (ORA-00001), lanca HTTP 409 Conflito.
    """
    usuario_id = uuid.uuid4().hex
    criado_em = datetime.now(UTC)

    sql = """
    INSERT INTO usuario (
        id, email, senha_hash, sessao_versao, persona_demo, criado_em
    ) VALUES (
        :id, :email, :senha_hash, :sessao_versao, :persona_demo, :criado_em
    )
    """

    try:
        import oracledb

        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(
                    sql,
                    {
                        "id": usuario_id,
                        "email": email,
                        "senha_hash": senha_hash,
                        "sessao_versao": 0,
                        "persona_demo": "N",
                        "criado_em": criado_em,
                    },
                )
    except oracledb.IntegrityError as err:
        if "ORA-00001" in str(err) or getattr(err, "code", None) == 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "erro": "Conflito",
                    "detalhes": "E-mail ja cadastrado.",
                },
            ) from err
        raise ErroBancoIndisponivel() from err
    except oracledb.DatabaseError as err:
        if "ORA-00001" in str(err) or getattr(err, "code", None) == 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "erro": "Conflito",
                    "detalhes": "E-mail ja cadastrado.",
                },
            ) from err
        raise ErroBancoIndisponivel() from err
    except Exception as err:
        if isinstance(err, HTTPException):
            raise
        raise ErroBancoIndisponivel() from err

    return {
        "id": usuario_id,
        "email": email,
        "criado_em": _formatar_iso_utc(criado_em),
    }


def buscar_por_email(email: str) -> dict[str, Any] | None:
    """Busca usuario por e-mail utilizando bind variable."""
    sql = """
    SELECT id, email, senha_hash, sessao_versao, persona_demo, criado_em
    FROM usuario
    WHERE email = :email
    """
    try:
        import oracledb

        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(sql, {"email": email})
                linha = cursor.fetchone()
                if not linha:
                    return None
                return {
                    "id": linha[0],
                    "email": linha[1],
                    "senha_hash": linha[2],
                    "sessao_versao": int(linha[3]),
                    "persona_demo": str(linha[4]).strip(),
                    "criado_em": _formatar_iso_utc(linha[5]),
                }
    except oracledb.Error as err:
        raise ErroBancoIndisponivel() from err
    except Exception as err:
        if isinstance(err, (HTTPException, ErroBancoIndisponivel)):
            raise
        raise ErroBancoIndisponivel() from err


def buscar_por_id(usuario_id: str) -> dict[str, Any] | None:
    """Busca usuario por id utilizando bind variable."""
    sql = """
    SELECT id, email, senha_hash, sessao_versao, persona_demo, criado_em
    FROM usuario
    WHERE id = :id
    """
    try:
        import oracledb

        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(sql, {"id": usuario_id})
                linha = cursor.fetchone()
                if not linha:
                    return None
                return {
                    "id": linha[0],
                    "email": linha[1],
                    "senha_hash": linha[2],
                    "sessao_versao": int(linha[3]),
                    "persona_demo": str(linha[4]).strip(),
                    "criado_em": _formatar_iso_utc(linha[5]),
                }
    except oracledb.Error as err:
        raise ErroBancoIndisponivel() from err
    except Exception as err:
        if isinstance(err, (HTTPException, ErroBancoIndisponivel)):
            raise
        raise ErroBancoIndisponivel() from err


def incrementar_sessao_versao(usuario_id: str) -> None:
    """Incrementa a versao de sessao do usuario para invalidar tokens ativos no logout."""
    sql = """
    UPDATE usuario
    SET sessao_versao = sessao_versao + 1
    WHERE id = :id
    """
    try:
        import oracledb

        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(sql, {"id": usuario_id})
    except oracledb.Error as err:
        raise ErroBancoIndisponivel() from err
    except Exception as err:
        if isinstance(err, (HTTPException, ErroBancoIndisponivel)):
            raise
        raise ErroBancoIndisponivel() from err
