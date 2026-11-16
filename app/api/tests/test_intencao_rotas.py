"""Testes da rota de intenção de transição profissional (/me/intencao)."""

import logging
import uuid

import pytest
from fastapi.testclient import TestClient

from citizentech.main import app


def _criar_usuario_e_sessao(cliente: TestClient, sufixo: str) -> dict:
    email = f"user_{sufixo}_{uuid.uuid4().hex[:6]}@example.test"
    senha = "SenhaForte123!@"

    resp_reg = cliente.post("/auth/registrar", json={"email": email, "senha": senha})
    assert resp_reg.status_code == 201
    dados_reg = resp_reg.json()

    resp_login = cliente.post("/auth/login", json={"email": email, "senha": senha})
    assert resp_login.status_code == 200
    csrf_token = cliente.cookies.get("csrf_token")
    assert csrf_token is not None

    return {
        "id": dados_reg["id"],
        "email": email,
        "csrf_token": csrf_token,
    }


@pytest.mark.oracle
def test_put_intencao_redige_motivo_e_exige_perfil():
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "intencao_red")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}

    payload = {
        "atividades_desejadas": ["analise de dados", "criacao de dashboards"],
        "motivos": [
            "Transicao de carreira para tech, contato: joao.silva@empresa.com para detalhes"
        ],
        "horas_semana": 10,
        "orcamento_mensal_brl": 250.0,
        "uf": "SP",
    }

    # 1. Sem consentimento 'perfil' -> 403 e GET -> 404
    resp_put_sem_consent = cliente.put("/me/intencao", json=payload, headers=headers_csrf)
    assert resp_put_sem_consent.status_code == 403
    assert resp_put_sem_consent.json()["erro"] == "Consentimento necessario"

    resp_get_sem_intencao = cliente.get("/me/intencao")
    assert resp_get_sem_intencao.status_code == 404

    # 2. Com consentimento 'perfil' -> 200 e motivo redigido (sem email)
    resp_consent = cliente.post(
        "/me/consentimentos",
        json={"finalidade": "perfil"},
        headers=headers_csrf,
    )
    assert resp_consent.status_code == 201

    resp_put = cliente.put("/me/intencao", json=payload, headers=headers_csrf)
    assert resp_put.status_code == 200
    dados_put = resp_put.json()

    assert "joao.silva@empresa.com" not in dados_put["motivos"][0]
    assert "[EMAIL]" in dados_put["motivos"][0]
    assert dados_put["horas_semana"] == 10
    assert dados_put["orcamento_mensal_brl"] == 250.0
    assert dados_put["uf"] == "SP"
    assert "atualizado_em" in dados_put

    # 3. GET devolve o mesmo corpo
    resp_get = cliente.get("/me/intencao")
    assert resp_get.status_code == 200
    assert resp_get.json() == dados_put


@pytest.mark.oracle
def test_put_intencao_upsert():
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "int_upsert")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}

    cliente.post("/me/consentimentos", json={"finalidade": "perfil"}, headers=headers_csrf)

    payload1 = {
        "atividades_desejadas": ["analise"],
        "motivos": ["motivo inicial"],
        "horas_semana": 15,
        "orcamento_mensal_brl": 100.0,
        "uf": "RJ",
    }
    resp1 = cliente.put("/me/intencao", json=payload1, headers=headers_csrf)
    assert resp1.status_code == 200
    assert resp1.json()["horas_semana"] == 15
    assert resp1.json()["uf"] == "RJ"

    payload2 = {
        "atividades_desejadas": ["engenharia"],
        "motivos": ["segundo motivo"],
        "horas_semana": 20,
        "orcamento_mensal_brl": 500.0,
        "uf": "MG",
    }
    resp2 = cliente.put("/me/intencao", json=payload2, headers=headers_csrf)
    assert resp2.status_code == 200
    assert resp2.json()["horas_semana"] == 20
    assert resp2.json()["uf"] == "MG"

    resp_get = cliente.get("/me/intencao")
    assert resp_get.status_code == 200
    assert resp_get.json()["horas_semana"] == 20
    assert resp_get.json()["uf"] == "MG"
    assert resp_get.json()["atividades_desejadas"] == ["engenharia"]


@pytest.mark.oracle
def test_put_intencao_validacoes_400():
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "int_val")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}
    cliente.post("/me/consentimentos", json={"finalidade": "perfil"}, headers=headers_csrf)

    base = {
        "atividades_desejadas": ["atividade valida"],
        "motivos": ["motivo valido"],
        "horas_semana": 10,
        "orcamento_mensal_brl": 200.0,
        "uf": "SP",
    }

    # horas_semana == 0
    p = dict(base, horas_semana=0)
    assert cliente.put("/me/intencao", json=p, headers=headers_csrf).status_code == 400

    # horas_semana == 81
    p = dict(base, horas_semana=81)
    assert cliente.put("/me/intencao", json=p, headers=headers_csrf).status_code == 400

    # uf invalida
    p = dict(base, uf="XX")
    assert cliente.put("/me/intencao", json=p, headers=headers_csrf).status_code == 400

    # 11 atividades
    p = dict(base, atividades_desejadas=[f"ativ {i}" for i in range(11)])
    assert cliente.put("/me/intencao", json=p, headers=headers_csrf).status_code == 400

    # atividade com 121 caracteres
    p = dict(base, atividades_desejadas=["a" * 121])
    assert cliente.put("/me/intencao", json=p, headers=headers_csrf).status_code == 400

    # atividade vazia após strip
    p = dict(base, atividades_desejadas=["   "])
    assert cliente.put("/me/intencao", json=p, headers=headers_csrf).status_code == 400

    # motivo de 301 caracteres
    p = dict(base, motivos=["m" * 301])
    assert cliente.put("/me/intencao", json=p, headers=headers_csrf).status_code == 400

    # motivo vazio após strip
    p = dict(base, motivos=["   "])
    assert cliente.put("/me/intencao", json=p, headers=headers_csrf).status_code == 400

    # 6 motivos
    p = dict(base, motivos=[f"motivo {i}" for i in range(6)])
    assert cliente.put("/me/intencao", json=p, headers=headers_csrf).status_code == 400

    # orcamento negativo
    p = dict(base, orcamento_mensal_brl=-1.0)
    assert cliente.put("/me/intencao", json=p, headers=headers_csrf).status_code == 400

    # orcamento acima de 100000
    p = dict(base, orcamento_mensal_brl=100001.0)
    assert cliente.put("/me/intencao", json=p, headers=headers_csrf).status_code == 400

    # campo extra
    p = dict(base, campo_extra="nao permitido")
    assert cliente.put("/me/intencao", json=p, headers=headers_csrf).status_code == 400


@pytest.mark.oracle
def test_intencao_seguranca_cookie_e_csrf():
    cliente = TestClient(app, base_url="https://testserver")
    _criar_usuario_e_sessao(cliente, "int_sec")

    payload = {
        "atividades_desejadas": ["analise"],
        "motivos": ["motivo"],
        "horas_semana": 10,
        "orcamento_mensal_brl": 0.0,
        "uf": "SP",
    }

    # PUT sem CSRF -> 403
    resp_sem_csrf = cliente.put("/me/intencao", json=payload)
    assert resp_sem_csrf.status_code == 403

    # Cliente anonimo (sem cookie)
    cliente_anon = TestClient(app, base_url="https://testserver")
    resp_put_anon = cliente_anon.put("/me/intencao", json=payload, headers={"X-CSRF-Token": "x"})
    assert resp_put_anon.status_code == 401

    resp_get_anon = cliente_anon.get("/me/intencao")
    assert resp_get_anon.status_code == 401


@pytest.mark.oracle
def test_intencao_nao_grava_motivo_em_log(caplog):
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "int_log")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}
    cliente.post("/me/consentimentos", json={"finalidade": "perfil"}, headers=headers_csrf)

    marcador_motivo = "MOTIVO-MARCADOR-PARA-LOG-12345"
    payload = {
        "atividades_desejadas": ["atividade"],
        "motivos": [f"Estou buscando transicao: {marcador_motivo}"],
        "horas_semana": 10,
        "orcamento_mensal_brl": None,
        "uf": "SP",
    }

    with caplog.at_level(logging.DEBUG):
        resp = cliente.put("/me/intencao", json=payload, headers=headers_csrf)
        assert resp.status_code == 200

    assert marcador_motivo not in caplog.text
