"""Persistência de intenção de transição no Oracle (19c)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from citizentech.banco.conexao import ErroBancoIndisponivel, obter_conexao
from citizentech.banco.util import deserializar_json, iso_utc


def salvar_intencao(
    usuario_id: str,
    atividades_desejadas: list[str],
    motivos: list[str],
    horas_semana: int,
    orcamento_mensal_brl: float | None,
    uf: str,
) -> dict[str, Any]:
    """Salva ou atualiza a intenção do usuário (upsert)."""
    import oracledb

    agora = datetime.now(UTC)
    atividades_json = json.dumps(atividades_desejadas, ensure_ascii=False)
    motivos_json = json.dumps(motivos, ensure_ascii=False)

    sql = """
    MERGE INTO intencao target
    USING (SELECT :usuario_id AS usuario_id FROM dual) src
    ON (target.usuario_id = src.usuario_id)
    WHEN MATCHED THEN
        UPDATE SET
            atividades_json = :atividades_json,
            motivos_json = :motivos_json,
            horas_semana = :horas_semana,
            orcamento_mensal_brl = :orcamento_mensal_brl,
            uf = :uf,
            atualizado_em = :atualizado_em
    WHEN NOT MATCHED THEN
        INSERT (
            usuario_id, atividades_json, motivos_json, horas_semana,
            orcamento_mensal_brl, uf, atualizado_em
        ) VALUES (
            :usuario_id, :atividades_json, :motivos_json, :horas_semana,
            :orcamento_mensal_brl, :uf, :atualizado_em
        )
    """

    try:
        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(
                    sql,
                    {
                        "usuario_id": usuario_id,
                        "atividades_json": atividades_json,
                        "motivos_json": motivos_json,
                        "horas_semana": horas_semana,
                        "orcamento_mensal_brl": orcamento_mensal_brl,
                        "uf": uf,
                        "atualizado_em": agora,
                    },
                )
            conexao.commit()
    except oracledb.Error as err:
        raise ErroBancoIndisponivel() from err

    return {
        "atividades_desejadas": atividades_desejadas,
        "motivos": motivos,
        "horas_semana": horas_semana,
        "orcamento_mensal_brl": orcamento_mensal_brl,
        "uf": uf,
        "atualizado_em": iso_utc(agora),
    }


def buscar_intencao(usuario_id: str) -> dict[str, Any] | None:
    """Busca a intenção registrada do usuário."""
    import oracledb

    sql = """
    SELECT atividades_json, motivos_json, horas_semana, orcamento_mensal_brl, uf, atualizado_em
    FROM intencao
    WHERE usuario_id = :usuario_id
    """

    try:
        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(sql, {"usuario_id": usuario_id})
                row = cursor.fetchone()
                if not row:
                    return None

                atividades = deserializar_json(row[0])
                motivos = deserializar_json(row[1])
                horas_semana = int(row[2])
                orcamento = float(row[3]) if row[3] is not None else None
                uf = str(row[4]).strip()
                atualizado_em = iso_utc(row[5])

                return {
                    "atividades_desejadas": atividades,
                    "motivos": motivos,
                    "horas_semana": horas_semana,
                    "orcamento_mensal_brl": orcamento,
                    "uf": uf,
                    "atualizado_em": atualizado_em,
                }
    except oracledb.Error as err:
        raise ErroBancoIndisponivel() from err
