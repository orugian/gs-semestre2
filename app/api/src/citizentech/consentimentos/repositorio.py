"""Repositorio de persistencia de consentimentos no Oracle."""

import uuid
from datetime import UTC, datetime
from typing import Any

from citizentech.banco.conexao import ErroBancoIndisponivel, obter_conexao
from citizentech.banco.util import iso_utc


def criar_consentimento(
    usuario_id: str,
    finalidade: str,
    versao_termo: str = "v1.0",
) -> dict[str, Any]:
    """Registra uma concessao de consentimento para o usuario."""
    consentimento_id = uuid.uuid4().hex
    concedido_em = datetime.now(UTC)

    sql = """
    INSERT INTO consentimento (
        id, usuario_id, finalidade, versao_termo, concedido_em, revogado_em
    ) VALUES (
        :id, :usuario_id, :finalidade, :versao_termo, :concedido_em, NULL
    )
    """

    try:
        import oracledb

        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(
                    sql,
                    {
                        "id": consentimento_id,
                        "usuario_id": usuario_id,
                        "finalidade": finalidade,
                        "versao_termo": versao_termo,
                        "concedido_em": concedido_em,
                    },
                )
    except oracledb.Error as err:
        raise ErroBancoIndisponivel() from err
    except Exception as err:
        if isinstance(err, ErroBancoIndisponivel):
            raise
        raise ErroBancoIndisponivel() from err

    return {
        "id": consentimento_id,
        "finalidade": finalidade,
        "versao_termo": versao_termo,
        "concedido_em": iso_utc(concedido_em),
        "revogado_em": None,
    }


def listar_consentimentos(usuario_id: str) -> list[dict[str, Any]]:
    """Lista todos os consentimentos pertencentes exclusivamente ao usuario informado."""
    sql = """
    SELECT id, finalidade, versao_termo, concedido_em, revogado_em
    FROM consentimento
    WHERE usuario_id = :usuario_id
    ORDER BY concedido_em DESC
    """

    try:
        import oracledb

        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(sql, {"usuario_id": usuario_id})
                linhas = cursor.fetchall()
                itens = []
                for linha in linhas:
                    itens.append(
                        {
                            "id": linha[0],
                            "finalidade": linha[1],
                            "versao_termo": linha[2],
                            "concedido_em": iso_utc(linha[3]),
                            "revogado_em": iso_utc(linha[4]),
                        }
                    )
                return itens
    except oracledb.Error as err:
        raise ErroBancoIndisponivel() from err
    except Exception as err:
        if isinstance(err, ErroBancoIndisponivel):
            raise
        raise ErroBancoIndisponivel() from err


def revogar_consentimento(usuario_id: str, consentimento_id: str) -> bool:
    """Revoga o consentimento caso pertença ao usuario informado (T14).

    Filtra por usuario_id diretamente na SQL.
    Retorna True se encontrado e revogado (ou ja revogado).
    Retorna False se o recurso nao existir ou pertencer a outro usuario.
    """
    sql_consulta = """
    SELECT id, revogado_em
    FROM consentimento
    WHERE id = :id AND usuario_id = :usuario_id
    """

    sql_update = """
    UPDATE consentimento
    SET revogado_em = :agora
    WHERE id = :id AND usuario_id = :usuario_id
    """

    try:
        import oracledb

        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(
                    sql_consulta,
                    {"id": consentimento_id, "usuario_id": usuario_id},
                )
                linha = cursor.fetchone()
                if not linha:
                    return False

                revogado_em = linha[1]
                if revogado_em is None:
                    cursor.execute(
                        sql_update,
                        {
                            "id": consentimento_id,
                            "usuario_id": usuario_id,
                            "agora": datetime.now(UTC),
                        },
                    )
                return True
    except oracledb.Error as err:
        raise ErroBancoIndisponivel() from err
    except Exception as err:
        if isinstance(err, ErroBancoIndisponivel):
            raise
        raise ErroBancoIndisponivel() from err


def buscar_consentimento_global(consentimento_id: str) -> dict[str, Any] | None:
    """Busca consentimento independente de dono (util apenas para verificacao em testes)."""
    sql = """
    SELECT id, usuario_id, finalidade, versao_termo, concedido_em, revogado_em
    FROM consentimento
    WHERE id = :id
    """
    try:
        import oracledb

        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(sql, {"id": consentimento_id})
                linha = cursor.fetchone()
                if not linha:
                    return None
                return {
                    "id": linha[0],
                    "usuario_id": linha[1],
                    "finalidade": linha[2],
                    "versao_termo": linha[3],
                    "concedido_em": iso_utc(linha[4]),
                    "revogado_em": iso_utc(linha[5]),
                }
    except oracledb.Error as err:
        raise ErroBancoIndisponivel() from err
    except Exception as err:
        if isinstance(err, ErroBancoIndisponivel):
            raise
        raise ErroBancoIndisponivel() from err
