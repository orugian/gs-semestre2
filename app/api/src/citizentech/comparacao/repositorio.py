"""Persistência de comparações e destinos no Oracle (19c)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from citizentech.banco.conexao import ErroBancoIndisponivel, obter_conexao


def _formatar_iso_utc(dt: Any) -> str:
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        else:
            dt = dt.astimezone(UTC)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return str(dt)


def _deserializar_json(valor: Any) -> Any:
    """Converte valor do banco (objeto nativo, LOB ou str) em objeto Python."""
    if isinstance(valor, (dict, list)):
        return valor
    if hasattr(valor, "read"):
        valor = valor.read()
    if isinstance(valor, (bytes, bytearray)):
        valor = valor.decode("utf-8")
    if isinstance(valor, str):
        return json.loads(valor)
    return valor


def salvar_comparacao(
    comparacao_id: str,
    usuario_id: str,
    uf: str | None,
    aviso: str,
    criado_em: datetime,
    destinos: list[dict[str, Any]],
) -> None:
    """Persiste a comparação e os destinos no Oracle em transação atômica."""
    import oracledb

    sql_comparacao = """
    INSERT INTO comparacao (id, usuario_id, uf, aviso, criado_em)
    VALUES (:id, :usuario_id, :uf, :aviso, :criado_em)
    """

    sql_destino = """
    INSERT INTO comparacao_destino (
        comparacao_id, ordem, destino_id, situacao_obrigatorios, resultado_json
    ) VALUES (
        :comparacao_id, :ordem, :destino_id, :situacao_obrigatorios, :resultado_json
    )
    """

    try:
        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(
                    sql_comparacao,
                    {
                        "id": comparacao_id,
                        "usuario_id": usuario_id,
                        "uf": uf,
                        "aviso": aviso,
                        "criado_em": criado_em,
                    },
                )

                for ordem, d in enumerate(destinos, start=1):
                    resultado_json = json.dumps(d, ensure_ascii=False)
                    cursor.execute(
                        sql_destino,
                        {
                            "comparacao_id": comparacao_id,
                            "ordem": ordem,
                            "destino_id": d["destino_id"],
                            "situacao_obrigatorios": d["situacao_obrigatorios"],
                            "resultado_json": resultado_json,
                        },
                    )
            conexao.commit()
    except oracledb.Error as err:
        raise ErroBancoIndisponivel() from err


def buscar_comparacao(
    comparacao_id: str,
    usuario_id: str,
) -> dict[str, Any] | None:
    """Recupera comparação e seus destinos ordenados por ordem de exibição."""
    import oracledb

    sql_comp = """
    SELECT id, uf, aviso, criado_em
    FROM comparacao
    WHERE id = :id AND usuario_id = :usuario_id
    """

    sql_dest = """
    SELECT ordem, destino_id, situacao_obrigatorios, resultado_json
    FROM comparacao_destino
    WHERE comparacao_id = :comparacao_id
    ORDER BY ordem ASC
    """

    try:
        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(sql_comp, {"id": comparacao_id, "usuario_id": usuario_id})
                row_comp = cursor.fetchone()
                if not row_comp:
                    return None

                cid = str(row_comp[0])
                uf = str(row_comp[1]).strip() if row_comp[1] is not None else None
                aviso = str(row_comp[2])
                criado_em = _formatar_iso_utc(row_comp[3])

                cursor.execute(sql_dest, {"comparacao_id": comparacao_id})
                destinos: list[dict[str, Any]] = []
                for row_d in cursor.fetchall():
                    item_json = _deserializar_json(row_d[3])
                    destinos.append(item_json)

                return {
                    "comparacao_id": cid,
                    "criado_em": criado_em,
                    "uf": uf,
                    "destinos": destinos,
                    "aviso": aviso,
                }
    except oracledb.Error as err:
        raise ErroBancoIndisponivel() from err
