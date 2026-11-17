"""Testes unitarios do servico e repositorio de curriculo."""

import uuid

import pytest

from citizentech.curriculo.repositorio import (
    RepositorioCurriculosEmMemoria,
    RepositorioCurriculosMongo,
)
from citizentech.curriculo.servico import CurriculoNaoLiberado, texto_liberado_para_llm
from citizentech.erros import ServicoIndisponivel


def test_repositorio_em_memoria_ciclo_completo():
    repo = RepositorioCurriculosEmMemoria()
    cid = uuid.uuid4().hex
    uid = uuid.uuid4().hex

    doc = {
        "_id": cid,
        "usuario_id": uid,
        "origem": "texto",
        "status": "aguardando_confirmacao",
        "texto_redigido": "Texto sem PII",
        "sha256_texto_redigido": "hash123",
        "redacoes": {"nome": 0, "email": 0},
        "criado_em": "2026-11-16T12:00:00Z",
        "confirmado_em": None,
    }

    # Salva
    salvo = repo.salvar(doc)
    assert salvo["id"] == cid
    assert salvo["status"] == "aguardando_confirmacao"

    # Busca
    buscado = repo.buscar_por_id(cid, usuario_id=uid)
    assert buscado is not None
    assert buscado["id"] == cid

    # T14: outro usuario nao encontra
    assert repo.buscar_por_id(cid, usuario_id="outro_user") is None

    # Confirma
    confirmado = repo.confirmar(
        curriculo_id=cid,
        usuario_id=uid,
        texto_redigido="Texto revisado",
        sha256_texto_redigido="hash456",
        redacoes={"nome": 0, "email": 0},
        confirmado_em="2026-11-16T12:05:00Z",
    )
    assert confirmado is not None
    assert confirmado["status"] == "confirmado"
    assert confirmado["texto_redigido"] == "Texto revisado"
    assert confirmado["confirmado_em"] == "2026-11-16T12:05:00Z"

    # Idempotencia de confirmacao
    reconfirmado = repo.confirmar(
        curriculo_id=cid,
        usuario_id=uid,
        texto_redigido="Tentativa de sobreescrita",
        sha256_texto_redigido="hash789",
        redacoes={"nome": 0, "email": 0},
        confirmado_em="2026-11-16T12:10:00Z",
    )
    assert reconfirmado["texto_redigido"] == "Texto revisado"
    assert reconfirmado["confirmado_em"] == "2026-11-16T12:05:00Z"


def test_texto_liberado_para_llm_falha_se_curriculo_nao_confirmado(monkeypatch):
    repo = RepositorioCurriculosEmMemoria()
    cid = uuid.uuid4().hex
    uid = uuid.uuid4().hex

    repo.salvar({
        "_id": cid,
        "usuario_id": uid,
        "origem": "texto",
        "status": "aguardando_confirmacao",
        "texto_redigido": "Texto redigido",
        "sha256_texto_redigido": "abc",
        "redacoes": {},
        "criado_em": "2026-11-16T12:00:00Z",
        "confirmado_em": None,
    })

    # Simula consentimento curriculo_llm ativo
    monkeypatch.setattr(
        "citizentech.consentimentos.dependencias.listar_consentimentos",
        lambda u: [{"finalidade": "curriculo_llm", "revogado_em": None}],
    )

    with pytest.raises(CurriculoNaoLiberado) as exc:
        texto_liberado_para_llm(uid, cid, repositorio=repo)
    assert "ainda nao foi confirmado" in exc.value.detalhes


def test_texto_liberado_para_llm_falha_se_consentimento_revogado(monkeypatch):
    repo = RepositorioCurriculosEmMemoria()
    cid = uuid.uuid4().hex
    uid = uuid.uuid4().hex

    repo.salvar({
        "_id": cid,
        "usuario_id": uid,
        "origem": "texto",
        "status": "confirmado",
        "texto_redigido": "Texto liberado",
        "sha256_texto_redigido": "abc",
        "redacoes": {},
        "criado_em": "2026-11-16T12:00:00Z",
        "confirmado_em": "2026-11-16T12:05:00Z",
    })

    # Consentimento curriculo_llm revogado
    monkeypatch.setattr(
        "citizentech.consentimentos.dependencias.listar_consentimentos",
        lambda u: [{"finalidade": "curriculo_llm", "revogado_em": "2026-11-16T12:10:00Z"}],
    )

    with pytest.raises(CurriculoNaoLiberado) as exc:
        texto_liberado_para_llm(uid, cid, repositorio=repo)
    assert "ausente ou revogado" in exc.value.detalhes


def test_texto_liberado_para_llm_sucesso_quando_confirmado_e_consentido(monkeypatch):
    repo = RepositorioCurriculosEmMemoria()
    cid = uuid.uuid4().hex
    uid = uuid.uuid4().hex

    repo.salvar({
        "_id": cid,
        "usuario_id": uid,
        "origem": "texto",
        "status": "confirmado",
        "texto_redigido": "Texto aprovado e redigido",
        "sha256_texto_redigido": "abc",
        "redacoes": {},
        "criado_em": "2026-11-16T12:00:00Z",
        "confirmado_em": "2026-11-16T12:05:00Z",
    })

    monkeypatch.setattr(
        "citizentech.consentimentos.dependencias.listar_consentimentos",
        lambda u: [{"finalidade": "curriculo_llm", "revogado_em": None}],
    )

    resultado = texto_liberado_para_llm(uid, cid, repositorio=repo)
    assert resultado == "Texto aprovado e redigido"


def test_mongo_indisponivel_retorna_503_sem_vazar_uri(monkeypatch):
    # Aponta para porta fechada com timeout minimo
    uri_invalida = "mongodb://127.0.0.1:59999"
    monkeypatch.setenv("MONGODB_URI", uri_invalida)
    monkeypatch.setenv("MONGODB_DB", "citizentech_teste_s9")

    repo = RepositorioCurriculosMongo()

    with pytest.raises(ServicoIndisponivel) as exc:
        repo.buscar_por_id("qualquer_id")

    detalhes = str(exc.value.detalhes)
    assert uri_invalida not in detalhes
    assert "mongodb://" not in detalhes
    assert "59999" not in detalhes
