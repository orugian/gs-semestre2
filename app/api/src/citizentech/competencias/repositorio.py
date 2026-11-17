"""Persistencia de competencias no Oracle e registro de extracoes no MongoDB."""

from __future__ import annotations

import logging
import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from citizentech.banco.conexao import ErroBancoIndisponivel, obter_conexao
from citizentech.banco.util import iso_utc
from citizentech.curriculo.redacao import redigir_pii
from citizentech.curriculo.repositorio import obter_cliente_mongo

logger = logging.getLogger("citizentech.competencias")


def contar_extracoes_24h(usuario_id: str) -> int:
    """Conta quantas extracoes foram realizadas pelo usuario nas ultimas 24 horas no Mongo."""
    cliente_mongo = obter_cliente_mongo()
    db_nome = os.environ.get("MONGODB_DB")
    if not db_nome:
        return 0

    limite_dt = datetime.now(UTC) - timedelta(hours=24)
    limite_iso = limite_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    colecao = cliente_mongo[db_nome]["extracoes_llm"]
    return int(
        colecao.count_documents(
            {
                "usuario_id": usuario_id,
                "criado_em": {"$gte": limite_iso},
            }
        )
    )


def registrar_extracao_mongo(
    usuario_id: str,
    curriculo_id: str,
    sha256_texto_redigido: str,
    modelo: str,
    tentativas: int,
    uso: dict[str, Any] | None,
    contagem_candidatas: int,
    descartadas: dict[str, int],
) -> str:
    """Registra metadados da execucao da LLM no MongoDB (sem texto e sem resposta bruta)."""
    extracao_id = uuid.uuid4().hex
    criado_em = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    documento = {
        "_id": extracao_id,
        "usuario_id": usuario_id,
        "curriculo_id": curriculo_id,
        "sha256_texto_redigido": sha256_texto_redigido,
        "modelo": modelo,
        "tentativas": tentativas,
        "uso": uso,
        "contagem_candidatas": contagem_candidatas,
        "descartadas": descartadas,
        "criado_em": criado_em,
    }

    cliente_mongo = obter_cliente_mongo()
    db_nome = os.environ.get("MONGODB_DB")
    if db_nome:
        cliente_mongo[db_nome]["extracoes_llm"].insert_one(documento)

    return extracao_id


def salvar_candidatas_extracao(
    usuario_id: str,
    curriculo_id: str,
    extracao_id: str,
    candidatas: list[dict[str, Any]],
    catalogo: dict[str, str],
) -> list[dict[str, Any]]:
    """Persiste candidatas no Oracle.

    Substitui pendentes do mesmo curriculo sem tocar confirmadas/rejeitadas.
    """
    agora = datetime.now(UTC)

    sql_delete = """
    DELETE FROM competencia_usuario
    WHERE usuario_id = :usuario_id
      AND curriculo_id = :curriculo_id
      AND revisao = 'pendente'
    """

    sql_insert = """
    INSERT INTO competencia_usuario (
        id, usuario_id, esco_id, trecho_origem, origem,
        estado_evidencia, revisao, curriculo_id, extracao_id,
        criado_em, atualizado_em
    ) VALUES (
        :id, :usuario_id, :esco_id, :trecho_origem, 'extracao_llm',
        'declarada', 'pendente', :curriculo_id, :extracao_id,
        :criado_em, :atualizado_em
    )
    """

    import oracledb

    itens_salvos: list[dict[str, Any]] = []

    try:
        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(
                    sql_delete,
                    {"usuario_id": usuario_id, "curriculo_id": curriculo_id},
                )

                for cand in candidatas:
                    comp_id = uuid.uuid4().hex
                    esco_id = cand["esco_id"]
                    trecho = cand["trecho_origem"]

                    cursor.execute(
                        sql_insert,
                        {
                            "id": comp_id,
                            "usuario_id": usuario_id,
                            "esco_id": esco_id,
                            "trecho_origem": trecho,
                            "curriculo_id": curriculo_id,
                            "extracao_id": extracao_id,
                            "criado_em": agora,
                            "atualizado_em": agora,
                        },
                    )

                    itens_salvos.append(
                        {
                            "id": comp_id,
                            "esco_id": esco_id,
                            "titulo": catalogo.get(esco_id, ""),
                            "trecho_origem": trecho,
                            "origem": "extracao_llm",
                            "estado_evidencia": "declarada",
                            "revisao": "pendente",
                            "curriculo_id": curriculo_id,
                            "extracao_id": extracao_id,
                            "criado_em": iso_utc(agora),
                            "atualizado_em": iso_utc(agora),
                        }
                    )
            conexao.commit()
    except oracledb.Error as err:
        raise ErroBancoIndisponivel() from err

    return itens_salvos


def listar_competencias_usuario(
    usuario_id: str,
    catalogo: dict[str, str],
) -> list[dict[str, Any]]:
    """Lista todas as competencias do usuario registradas no Oracle."""
    sql = """
    SELECT id, esco_id, trecho_origem, origem, estado_evidencia,
           revisao, curriculo_id, extracao_id, criado_em, atualizado_em
    FROM competencia_usuario
    WHERE usuario_id = :usuario_id
    ORDER BY criado_em ASC, id ASC
    """

    import oracledb

    itens: list[dict[str, Any]] = []
    try:
        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(sql, {"usuario_id": usuario_id})
                for row in cursor.fetchall():
                    esco_id = row[1]
                    itens.append(
                        {
                            "id": row[0],
                            "esco_id": esco_id,
                            "titulo": catalogo.get(esco_id, ""),
                            "trecho_origem": row[2],
                            "origem": row[3],
                            "estado_evidencia": row[4],
                            "revisao": row[5],
                            "curriculo_id": row[6],
                            "extracao_id": row[7],
                            "criado_em": iso_utc(row[8]),
                            "atualizado_em": iso_utc(row[9]),
                        }
                    )
    except oracledb.Error as err:
        raise ErroBancoIndisponivel() from err

    return itens


def atualizar_competencia(
    comp_id: str,
    usuario_id: str,
    acao: str,
    trecho_origem: str | None,
    catalogo: dict[str, str],
) -> dict[str, Any] | None:
    """Atualiza o estado de revisao e opcionalmente o trecho_origem da competencia."""
    mapa_acao = {
        "confirmar": "confirmada",
        "rejeitar": "rejeitada",
        "nao_possuo": "nao_possuo",
    }
    nova_revisao = mapa_acao.get(acao)
    if not nova_revisao:
        raise ValueError(f"Acao de revisao invalida: {acao}")

    agora = datetime.now(UTC)

    import oracledb

    try:
        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                if trecho_origem is not None:
                    texto_redigido, _ = redigir_pii(trecho_origem)
                    trecho_final = texto_redigido[:500]
                    sql = """
                    UPDATE competencia_usuario
                    SET revisao = :revisao,
                        trecho_origem = :trecho_origem,
                        atualizado_em = :atualizado_em
                    WHERE id = :id AND usuario_id = :usuario_id
                    """
                    cursor.execute(
                        sql,
                        {
                            "revisao": nova_revisao,
                            "trecho_origem": trecho_final,
                            "atualizado_em": agora,
                            "id": comp_id,
                            "usuario_id": usuario_id,
                        },
                    )
                else:
                    sql = """
                    UPDATE competencia_usuario
                    SET revisao = :revisao,
                        atualizado_em = :atualizado_em
                    WHERE id = :id AND usuario_id = :usuario_id
                    """
                    cursor.execute(
                        sql,
                        {
                            "revisao": nova_revisao,
                            "atualizado_em": agora,
                            "id": comp_id,
                            "usuario_id": usuario_id,
                        },
                    )

                if cursor.rowcount == 0:
                    return None

                cursor.execute(
                    """
                    SELECT id, esco_id, trecho_origem, origem, estado_evidencia,
                           revisao, curriculo_id, extracao_id, criado_em, atualizado_em
                    FROM competencia_usuario
                    WHERE id = :id AND usuario_id = :usuario_id
                    """,
                    {"id": comp_id, "usuario_id": usuario_id},
                )
                row = cursor.fetchone()
                if not row:
                    return None

                esco_id = row[1]
                resultado = {
                    "id": row[0],
                    "esco_id": esco_id,
                    "titulo": catalogo.get(esco_id, ""),
                    "trecho_origem": row[2],
                    "origem": row[3],
                    "estado_evidencia": row[4],
                    "revisao": row[5],
                    "curriculo_id": row[6],
                    "extracao_id": row[7],
                    "criado_em": iso_utc(row[8]),
                    "atualizado_em": iso_utc(row[9]),
                }
            conexao.commit()
            return resultado
    except oracledb.Error as err:
        raise ErroBancoIndisponivel() from err


def competencias_para_comparacao(usuario_id: str) -> list[dict[str, Any]]:
    """Funcao de dominio publica para S11: devolve competencias para comparacao excluindo pendentes.

    Retorna lista com {"esco_id", "estado", "origem", "trecho_origem"}, onde
    estado = "declarada" (confirmada), "rejeitada" ou "nao_possuo".
    """
    sql = """
    SELECT esco_id, revisao, origem, trecho_origem
    FROM competencia_usuario
    WHERE usuario_id = :usuario_id
      AND revisao IN ('confirmada', 'rejeitada', 'nao_possuo')
    ORDER BY criado_em ASC, id ASC
    """

    import oracledb

    itens: list[dict[str, Any]] = []
    try:
        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(sql, {"usuario_id": usuario_id})
                for row in cursor.fetchall():
                    revisao = row[1]
                    estado = "declarada" if revisao == "confirmada" else revisao
                    itens.append(
                        {
                            "esco_id": row[0],
                            "estado": estado,
                            "origem": row[2],
                            "trecho_origem": row[3],
                        }
                    )
    except oracledb.Error as err:
        raise ErroBancoIndisponivel() from err

    return itens
