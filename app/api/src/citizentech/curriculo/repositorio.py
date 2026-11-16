"""Repositorio de persistencia de curriculos redigidos no MongoDB."""

import os
import threading
from typing import Any, Protocol

import pymongo
from fastapi import HTTPException, status
from pymongo.errors import PyMongoError

CAMPOS_PERMITIDOS = {
    "_id",
    "usuario_id",
    "origem",
    "status",
    "texto_redigido",
    "sha256_texto_redigido",
    "redacoes",
    "criado_em",
    "confirmado_em",
}

_cliente_mongo_lock = threading.Lock()
_cliente_mongo: pymongo.MongoClient | None = None


def obter_cliente_mongo() -> pymongo.MongoClient:
    """Retorna cliente MongoDB singleton sob demanda com lock thread-safe."""
    global _cliente_mongo
    if _cliente_mongo is not None:
        return _cliente_mongo

    with _cliente_mongo_lock:
        if _cliente_mongo is not None:
            return _cliente_mongo

        uri = os.environ.get("MONGODB_URI")
        db_nome = os.environ.get("MONGODB_DB")
        if not (uri and db_nome):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "erro": "Servico indisponivel",
                    "detalhes": "Configuracao do banco de dados MongoDB ausente.",
                },
            )

        try:
            cliente = pymongo.MongoClient(
                uri,
                serverSelectionTimeoutMS=2000,
                connectTimeoutMS=2000,
                socketTimeoutMS=2000,
            )
            cliente.admin.command("ping")
            _cliente_mongo = cliente
            return _cliente_mongo
        except (PyMongoError, Exception) as err:
            # Apos falha de conexao, o proximo uso tenta de novo (nao cachear cliente quebrado)
            _cliente_mongo = None
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "erro": "Servico indisponivel",
                    "detalhes": "Falha na comunicacao com o banco de dados.",
                },
            ) from err


def fechar_cliente_mongo() -> None:
    """Encerra a instancia singleton do MongoClient."""
    global _cliente_mongo
    with _cliente_mongo_lock:
        if _cliente_mongo is not None:
            try:
                _cliente_mongo.close()
            except Exception:
                pass
            _cliente_mongo = None


class RepositorioCurriculos(Protocol):
    """Protocolo do repositorio de curriculos."""

    def salvar(self, documento: dict[str, Any]) -> dict[str, Any]: ...

    def buscar_por_id(
        self, curriculo_id: str, usuario_id: str | None = None
    ) -> dict[str, Any] | None: ...

    def confirmar(
        self,
        curriculo_id: str,
        usuario_id: str,
        texto_redigido: str,
        sha256_texto_redigido: str,
        redacoes: dict[str, int],
        confirmado_em: str,
    ) -> dict[str, Any] | None: ...


class RepositorioCurriculosMongo:
    """Implementacao de persistencia no MongoDB com conexao sob demanda singleton."""

    def _obter_colecao(self) -> Any:
        db_nome = os.environ.get("MONGODB_DB")
        cliente = obter_cliente_mongo()
        return cliente[db_nome]["curriculos_redigidos"]

    def salvar(self, documento: dict[str, Any]) -> dict[str, Any]:
        doc_filtrado = {
            k: v for k, v in documento.items() if k in CAMPOS_PERMITIDOS
        }
        colecao = self._obter_colecao()
        try:
            colecao.insert_one(doc_filtrado)
        except (PyMongoError, Exception) as err:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "erro": "Servico indisponivel",
                    "detalhes": "Falha ao gravar no banco de dados.",
                },
            ) from err

        resposta = dict(doc_filtrado)
        resposta["id"] = resposta.pop("_id")
        return resposta

    def buscar_por_id(
        self, curriculo_id: str, usuario_id: str | None = None
    ) -> dict[str, Any] | None:
        filtro: dict[str, Any] = {"_id": curriculo_id}
        if usuario_id is not None:
            filtro["usuario_id"] = usuario_id

        colecao = self._obter_colecao()
        try:
            doc = colecao.find_one(filtro)
        except (PyMongoError, Exception) as err:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "erro": "Servico indisponivel",
                    "detalhes": "Falha ao consultar banco de dados.",
                },
            ) from err

        if not doc:
            return None

        resposta = dict(doc)
        resposta["id"] = resposta.pop("_id")
        return resposta

    def confirmar(
        self,
        curriculo_id: str,
        usuario_id: str,
        texto_redigido: str,
        sha256_texto_redigido: str,
        redacoes: dict[str, int],
        confirmado_em: str,
    ) -> dict[str, Any] | None:
        colecao = self._obter_colecao()
        filtro = {"_id": curriculo_id, "usuario_id": usuario_id}

        try:
            doc_atual = colecao.find_one(filtro)
            if not doc_atual:
                return None

            # Idempotencia: se ja confirmado, mantem o estado original
            if doc_atual.get("status") == "confirmado":
                resposta = dict(doc_atual)
                resposta["id"] = resposta.pop("_id")
                return resposta

            atualizacao = {
                "$set": {
                    "status": "confirmado",
                    "texto_redigido": texto_redigido,
                    "sha256_texto_redigido": sha256_texto_redigido,
                    "redacoes": redacoes,
                    "confirmado_em": confirmado_em,
                }
            }
            doc_atualizado = colecao.find_one_and_update(
                filtro,
                atualizacao,
                return_document=pymongo.ReturnDocument.AFTER,
            )
        except (PyMongoError, Exception) as err:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "erro": "Servico indisponivel",
                    "detalhes": "Falha ao atualizar no banco de dados.",
                },
            ) from err

        if not doc_atualizado:
            return None

        resposta = dict(doc_atualizado)
        resposta["id"] = resposta.pop("_id")
        return resposta


class RepositorioCurriculosEmMemoria:
    """Implementacao em memoria para testes unitarios isolados."""

    def __init__(self) -> None:
        self._documentos: dict[str, dict[str, Any]] = {}

    def salvar(self, documento: dict[str, Any]) -> dict[str, Any]:
        doc_filtrado = {
            k: v for k, v in documento.items() if k in CAMPOS_PERMITIDOS
        }
        cid = doc_filtrado["_id"]
        self._documentos[cid] = dict(doc_filtrado)
        resposta = dict(doc_filtrado)
        resposta["id"] = resposta.pop("_id")
        return resposta

    def buscar_por_id(
        self, curriculo_id: str, usuario_id: str | None = None
    ) -> dict[str, Any] | None:
        doc = self._documentos.get(curriculo_id)
        if not doc:
            return None
        if usuario_id is not None and doc.get("usuario_id") != usuario_id:
            return None
        resposta = dict(doc)
        resposta["id"] = resposta.pop("_id")
        return resposta

    def confirmar(
        self,
        curriculo_id: str,
        usuario_id: str,
        texto_redigido: str,
        sha256_texto_redigido: str,
        redacoes: dict[str, int],
        confirmado_em: str,
    ) -> dict[str, Any] | None:
        doc = self._documentos.get(curriculo_id)
        if not doc or doc.get("usuario_id") != usuario_id:
            return None
        if doc.get("status") == "confirmado":
            resposta = dict(doc)
            resposta["id"] = resposta.pop("_id")
            return resposta

        doc["status"] = "confirmado"
        doc["texto_redigido"] = texto_redigido
        doc["sha256_texto_redigido"] = sha256_texto_redigido
        doc["redacoes"] = redacoes
        doc["confirmado_em"] = confirmado_em

        resposta = dict(doc)
        resposta["id"] = resposta.pop("_id")
        return resposta


def obter_repositorio_curriculos() -> RepositorioCurriculos:
    """Dependencia FastAPI para obter o repositorio de curriculos."""
    return RepositorioCurriculosMongo()
