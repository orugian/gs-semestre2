"""Repositorio de persistencia de avaliacoes e tentativas (Oracle + MongoDB)."""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from pymongo.errors import PyMongoError

from citizentech.avaliacao.catalogo import (
    carregar_dados_destino,
    obter_requisitos_avaliados_destino,
)
from citizentech.banco.conexao import ErroBancoIndisponivel, obter_conexao
from citizentech.curriculo.repositorio import obter_cliente_mongo

logger = logging.getLogger("citizentech.avaliacao")


def _formatar_iso_utc(dt: Any) -> str | None:
    if dt is None:
        return None
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        else:
            dt = dt.astimezone(UTC)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return str(dt)


def contar_tentativas_24h(usuario_id: str, exercicio_id: str) -> int:
    """Conta tentativas do usuario para o exercicio nas ultimas 24 horas."""
    sql = """
    SELECT COUNT(*) FROM tentativa
    WHERE usuario_id = :usuario_id
      AND exercicio_id = :exercicio_id
      AND criado_em >= :limite_24h
    """
    limite = datetime.now(UTC) - timedelta(hours=24)
    try:
        import oracledb

        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(
                    sql,
                    {
                        "usuario_id": usuario_id,
                        "exercicio_id": exercicio_id,
                        "limite_24h": limite,
                    },
                )
                linha = cursor.fetchone()
                return int(linha[0]) if linha else 0
    except oracledb.Error as err:
        raise ErroBancoIndisponivel() from err


def salvar_tentativa_oracle(dados: dict[str, Any]) -> None:
    """Persiste a tentativa no Oracle 19c."""
    sql = """
    INSERT INTO tentativa (
        id, usuario_id, destino_id, exercicio_id, exercicio_versao,
        respostas_objetivas_json, acertos, total_objetivas, nota_objetiva,
        status_aberta, nota_llm, nota_final, resultado,
        avaliacao_id, sha256_resposta, discordo_em, discordo_motivo, criado_em
    ) VALUES (
        :id, :usuario_id, :destino_id, :exercicio_id, :exercicio_versao,
        :respostas_objetivas_json, :acertos, :total_objetivas, :nota_objetiva,
        :status_aberta, :nota_llm, :nota_final, :resultado,
        :avaliacao_id, :sha256_resposta, NULL, NULL, :criado_em
    )
    """
    try:
        import oracledb

        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                # Sem isto o driver liga datetime como DATE e perde as frações de segundo,
                # o que empata tentativas feitas no mesmo segundo (ordem de "ultima").
                cursor.setinputsizes(criado_em=oracledb.DB_TYPE_TIMESTAMP_TZ)
                cursor.execute(sql, dados)
    except oracledb.Error as err:
        raise ErroBancoIndisponivel() from err


def _obter_colecao_mongo(nome_colecao: str) -> Any:
    db_nome = os.environ.get("MONGODB_DB")
    cliente = obter_cliente_mongo()
    return cliente[db_nome][nome_colecao]


def salvar_resposta_aberta_mongo(
    tentativa_id: str,
    usuario_id: str,
    sha256: str,
    texto_redigido: str,
    criado_em: str,
) -> None:
    """Salva a resposta aberta redigida na colecao respostas_abertas do MongoDB."""
    doc = {
        "_id": tentativa_id,
        "usuario_id": usuario_id,
        "sha256": sha256,
        "texto_redigido": texto_redigido,
        "criado_em": criado_em,
    }
    try:
        colecao = _obter_colecao_mongo("respostas_abertas")
        colecao.insert_one(doc)
    except (PyMongoError, Exception) as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "erro": "Servico indisponivel",
                "detalhes": "Falha ao gravar resposta aberta no banco de dados.",
            },
        ) from err


def buscar_avaliacao_cache_mongo(chave_sha256: str) -> dict[str, Any] | None:
    """Busca avaliacao de resposta aberta em cache pelo SHA-256 (R23)."""
    try:
        colecao = _obter_colecao_mongo("avaliacoes_llm")
        return colecao.find_one({"_id": chave_sha256})
    except (PyMongoError, Exception) as err:
        logger.warning("Falha ao consultar cache Mongo de avaliacoes: %s", type(err).__name__)
        return None


def salvar_avaliacao_cache_mongo(
    chave_sha256: str,
    exercicio_id: str,
    versao: str,
    modelo: str,
    criterios: list[dict[str, Any]],
    criado_em: str,
) -> None:
    """Grava avaliacao com sucesso no cache Mongo (avaliacoes parciais nunca entram)."""
    doc = {
        "_id": chave_sha256,
        "exercicio_id": exercicio_id,
        "versao": versao,
        "modelo": modelo,
        "criterios": criterios,
        "criado_em": criado_em,
    }
    try:
        colecao = _obter_colecao_mongo("avaliacoes_llm")
        colecao.replace_one({"_id": chave_sha256}, doc, upsert=True)
    except (PyMongoError, Exception) as err:
        logger.warning("Falha ao gravar cache Mongo de avaliacoes: %s", type(err).__name__)


def registrar_discordo_oracle(
    tentativa_id: str,
    usuario_id: str,
    motivo_redigido: str,
) -> tuple[str, str]:
    """Registra contestacao de avaliacao pelo usuario (T08, LGPD art. 20)."""
    sql_consulta = """
    SELECT id, usuario_id, discordo_em
    FROM tentativa
    WHERE id = :id
    """
    sql_update = """
    UPDATE tentativa
    SET discordo_em = :discordo_em,
        discordo_motivo = :discordo_motivo
    WHERE id = :id AND usuario_id = :usuario_id AND discordo_em IS NULL
    """
    try:
        import oracledb

        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(sql_consulta, {"id": tentativa_id})
                linha = cursor.fetchone()
                if not linha or str(linha[1]) != usuario_id:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail={
                            "erro": "Nao encontrado",
                            "detalhes": "Tentativa nao encontrada ou nao pertence ao usuario.",
                        },
                    )

                if linha[2] is not None:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail={
                            "erro": "Conflito",
                            "detalhes": "Contestacao ja registrada para esta tentativa.",
                        },
                    )

                agora = datetime.now(UTC)
                cursor.execute(
                    sql_update,
                    {
                        "id": tentativa_id,
                        "usuario_id": usuario_id,
                        "discordo_em": agora,
                        "discordo_motivo": motivo_redigido,
                    },
                )
                if cursor.rowcount == 0:
                    # Outra requisicao registrou a contestacao entre o SELECT e o UPDATE
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail={
                            "erro": "Conflito",
                            "detalhes": "Esta tentativa ja possui contestacao registrada.",
                        },
                    )
                return _formatar_iso_utc(agora) or "", motivo_redigido
    except oracledb.Error as err:
        raise ErroBancoIndisponivel() from err


def listar_tentativas_usuario(
    usuario_id: str,
    destino_id: str | None = None,
) -> dict[str, Any]:
    """Lista historico de tentativas do usuario com identificacao da ultima e da melhor."""
    sql = """
    SELECT id, destino_id, exercicio_id, exercicio_versao,
           acertos, total_objetivas, nota_objetiva,
           status_aberta, nota_llm, nota_final, resultado,
           discordo_em, criado_em
    FROM tentativa
    WHERE usuario_id = :usuario_id
    """
    params: dict[str, Any] = {"usuario_id": usuario_id}
    if destino_id:
        sql += " AND destino_id = :destino_id"
        params["destino_id"] = destino_id
    sql += " ORDER BY criado_em ASC, id ASC"

    try:
        import oracledb

        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(sql, params)
                linhas = cursor.fetchall()
    except oracledb.Error as err:
        raise ErroBancoIndisponivel() from err

    itens = []
    for idx, r in enumerate(linhas):
        tid = str(r[0])
        did = str(r[1])
        eid = str(r[2])
        versao = str(r[3])
        nota_obj = float(r[6])
        status_ab = str(r[7])
        nota_llm_val = float(r[8]) if r[8] is not None else None
        nota_fin_val = float(r[9]) if r[9] is not None else None
        res_val = str(r[10])
        disc_em = _formatar_iso_utc(r[11])
        criad_em = _formatar_iso_utc(r[12]) or ""

        itens.append(
            {
                "tentativa_id": tid,
                "destino_id": did,
                "exercicio_id": eid,
                "exercicio_versao": versao,
                "criado_em": criad_em,
                "nota_objetiva": round(nota_obj, 2),
                "status_aberta": status_ab,
                "nota_llm": round(nota_llm_val, 2) if nota_llm_val is not None else None,
                "nota_final": round(nota_fin_val, 2) if nota_fin_val is not None else None,
                "resultado": res_val,
                "discordo_em": disc_em,
                "_raw_nota_final": nota_fin_val,
                "_raw_criado_em": r[12],
                "_raw_nota_obj": nota_obj,
                "_idx": idx,
            }
        )

    if not itens:
        return {"itens": [], "ultima": None, "melhor": None}

    # Ultima: mais recente por criado_em (empate pelo indice de insercao)
    ultima_tentativa = max(itens, key=lambda x: (x["_raw_criado_em"], x["_idx"]))
    ultima_id = ultima_tentativa["tentativa_id"]

    # Melhor: maior nota_final; empate e mais recente; parciais so contam se nao houver avaliada
    avaliadas = [
        it
        for it in itens
        if it["status_aberta"] == "avaliada" and it["_raw_nota_final"] is not None
    ]
    if avaliadas:
        melhor_item = max(
            avaliadas,
            key=lambda x: (x["_raw_nota_final"], x["_raw_criado_em"], x["_idx"]),
        )
        melhor_id = melhor_item["tentativa_id"]
    else:
        # Se so houver tentativas parciais
        melhor_item = max(
            itens,
            key=lambda x: (x["_raw_nota_obj"], x["_raw_criado_em"], x["_idx"]),
        )
        melhor_id = melhor_item["tentativa_id"]

    # Remove campos internos
    for it in itens:
        it.pop("_raw_nota_final", None)
        it.pop("_raw_criado_em", None)
        it.pop("_raw_nota_obj", None)
        it.pop("_idx", None)

    return {
        "itens": itens,
        "ultima": ultima_id,
        "melhor": melhor_id,
    }


def resultados_exercicio_para_comparacao(usuario_id: str) -> list[dict[str, Any]]:
    """Retorna resultados da tentativa mais recente de cada exercicio para comparacao (S11b/S13)."""
    sql = """
    SELECT destino_id, exercicio_id, resultado, criado_em
    FROM tentativa
    WHERE usuario_id = :usuario_id
    ORDER BY criado_em DESC, id DESC
    """
    try:
        import oracledb

        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(sql, {"usuario_id": usuario_id})
                linhas = cursor.fetchall()
    except oracledb.Error as err:
        raise ErroBancoIndisponivel() from err

    # Seleciona tentativa mais recente de cada exercicio_id
    exercicios_vistos: set[str] = set()
    resultados: list[dict[str, Any]] = []

    for r in linhas:
        destino_id = str(r[0])
        exercicio_id = str(r[1])
        resultado = str(r[2])

        if exercicio_id in exercicios_vistos:
            continue
        exercicios_vistos.add(exercicio_id)

        dados_destino = carregar_dados_destino(destino_id)
        if not dados_destino:
            continue

        reqs = obter_requisitos_avaliados_destino(dados_destino)
        esco_ids = [item["esco_id"] for item in reqs if item.get("esco_id")]
        if esco_ids:
            resultados.append(
                {
                    "esco_ids_avaliados": esco_ids,
                    "resultado": resultado,
                }
            )

    return resultados
