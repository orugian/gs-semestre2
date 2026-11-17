"""Testes de contrato de erros da API CitizenTech.

Rede de seguranca (S17): fixa status HTTP e corpo byte a byte de respostas
de erro representativas que serao refatoradas:
- 403 consentimento ausente (intencao, comparacao, plano, curriculo, avaliacao, laboratorio)
- 404 recurso inexistente (curriculo, plano, tentativa)
- 409 conflito de evento
- 503 banco indisponivel
"""

import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient

from citizentech.banco import conexao
from citizentech.main import app


def _criar_usuario_e_sessao(cliente: TestClient, sufixo: str) -> dict[str, Any]:
    email = f"user_contrato_{sufixo}_{uuid.uuid4().hex[:6]}@example.test"
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


# ============================================================================
# 1. 403 Consentimento Ausente
# ============================================================================


@pytest.mark.oracle
def test_contrato_403_consentimento_ausente_intencao():
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "intencao")
    headers = {"X-CSRF-Token": usuario["csrf_token"]}

    payload = {
        "atividades_desejadas": ["analise de dados"],
        "motivos": ["Transicao para tech"],
        "horas_semana": 10,
        "orcamento_mensal_brl": 200.0,
        "uf": "SP",
    }
    resp = cliente.put("/me/intencao", json=payload, headers=headers)
    assert resp.status_code == 403
    assert resp.json() == {
        "erro": "Consentimento necessario",
        "detalhes": "Consentimento para a finalidade 'perfil' ausente ou revogado.",
    }


@pytest.mark.oracle
def test_contrato_403_consentimento_ausente_comparacao():
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "comparacao")
    headers = {"X-CSRF-Token": usuario["csrf_token"]}

    payload = {
        "destinos": ["analista_dados_jr"],
    }
    resp = cliente.post("/me/comparacoes", json=payload, headers=headers)
    assert resp.status_code == 403
    assert resp.json() == {
        "erro": "Consentimento necessario",
        "detalhes": "Consentimento para a finalidade 'perfil' ausente ou revogado.",
    }


@pytest.mark.oracle
def test_contrato_403_consentimento_ausente_plano():
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "plano")
    headers = {"X-CSRF-Token": usuario["csrf_token"]}

    payload = {
        "destino_id": "analista_monitoramento_iot",
    }
    resp = cliente.post("/me/caminho", json=payload, headers=headers)
    assert resp.status_code == 403
    assert resp.json() == {
        "erro": "Consentimento necessario",
        "detalhes": "Consentimento para a finalidade 'perfil' ausente ou revogado.",
    }


@pytest.mark.oracle
def test_contrato_403_consentimento_ausente_curriculo():
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "curriculo")
    headers = {"X-CSRF-Token": usuario["csrf_token"]}

    payload = {
        "texto": "Experiencia em Python e desenvolvimento de software.",
    }
    resp = cliente.post("/me/experiencias", json=payload, headers=headers)
    assert resp.status_code == 403
    assert resp.json() == {
        "erro": "Consentimento necessario",
        "detalhes": "Consentimento para a finalidade 'perfil' ausente ou revogado.",
    }


@pytest.mark.oracle
def test_contrato_403_consentimento_ausente_avaliacao():
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "avaliacao")
    headers = {"X-CSRF-Token": usuario["csrf_token"]}

    payload = {
        "destino_id": "analista_processos",
        "exercicio_id": "ex_analista_processos_01",
        "respostas_objetivas": {"q1": "C", "q2": "D", "q3": "A", "q4": "B"},
        "resposta_aberta": "Proposta de solucao completa com mais de 20 caracteres.",
    }
    resp = cliente.post("/me/tentativas", json=payload, headers=headers)
    assert resp.status_code == 403
    assert resp.json() == {
        "erro": "Consentimento necessario",
        "detalhes": "Consentimento 'curriculo_llm' ausente ou revogado para o usuario.",
    }


@pytest.mark.oracle
def test_contrato_403_consentimento_ausente_laboratorio():
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "laboratorio")
    headers = {"X-CSRF-Token": usuario["csrf_token"]}

    resp = cliente.post("/me/laboratorio/sessoes", json={}, headers=headers)
    assert resp.status_code == 403
    assert resp.json() == {
        "erro": "Consentimento necessario",
        "detalhes": "Consentimento 'laboratorio_nuvem' ausente ou revogado para o usuario.",
    }


# ============================================================================
# 2. 404 Recurso Inexistente
# ============================================================================


@pytest.mark.oracle
def test_contrato_404_recurso_inexistente_curriculo():
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "curriculo404")
    headers = {"X-CSRF-Token": usuario["csrf_token"]}

    # Dar consentimento 'perfil'
    cliente.post(
        "/me/consentimentos",
        json={"finalidade": "perfil"},
        headers=headers,
    )

    resp = cliente.get("/me/curriculo/000000000000000000000000")
    assert resp.status_code == 404
    assert resp.json() == {
        "erro": "Recurso nao encontrado",
        "detalhes": "Curriculo nao encontrado.",
    }


@pytest.mark.oracle
def test_contrato_404_recurso_inexistente_plano():
    cliente = TestClient(app, base_url="https://testserver")
    _criar_usuario_e_sessao(cliente, "plano404")

    resp = cliente.get("/me/plano")
    assert resp.status_code == 404
    assert resp.json() == {
        "erro": "Nao encontrado",
        "detalhes": "Nenhum plano ativo encontrado para o usuario.",
    }


@pytest.mark.oracle
def test_contrato_404_recurso_inexistente_tentativa():
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "tentativa404")
    headers = {"X-CSRF-Token": usuario["csrf_token"]}

    resp = cliente.post(
        "/me/tentativas/00000000-0000-0000-0000-000000000000/discordo",
        json={"motivo": "Contestacao valida para tentativa inexistente."},
        headers=headers,
    )
    assert resp.status_code == 404
    assert resp.json() == {
        "erro": "Nao encontrado",
        "detalhes": "Tentativa nao encontrada ou nao pertence ao usuario.",
    }


# ============================================================================
# 3. 409 Conflito de Evento
# ============================================================================


def test_contrato_409_conflito_evento(tmp_path, monkeypatch):
    caminho_csv = tmp_path / "runtime" / "leituras.csv"
    caminho_db = tmp_path / "runtime" / "outbox.db"
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(caminho_csv))
    monkeypatch.setenv("CITIZENTECH_OUTBOX_DB", str(caminho_db))
    monkeypatch.setenv("DEVICE_KEY", "chave-secreta-demo")

    cliente = TestClient(app)

    payload_base = {
        "evento_id": "evt-contrato-409",
        "dispositivo_id": "esp32-01",
        "metrica": "temperatura_c",
        "valor": 25.0,
        "medido_em": "2026-11-13T10:00:00Z",
    }
    headers = {"X-Device-Key": "chave-secreta-demo"}

    r_orig = cliente.post("/leituras", json=payload_base, headers=headers)
    assert r_orig.status_code == 201

    payload_conflito = dict(payload_base)
    payload_conflito["valor"] = 38.0
    r_conf = cliente.post("/leituras", json=payload_conflito, headers=headers)
    assert r_conf.status_code == 409
    assert r_conf.json() == {
        "erro": "Conflito",
        "detalhes": "Mesmo evento_id com conteudo divergente.",
    }


# ============================================================================
# 4. 503 Banco Indisponivel
# ============================================================================


def test_contrato_503_banco_indisponivel(monkeypatch):
    import oracledb

    def falha_conexao():
        raise oracledb.DatabaseError("ORA-12541: Cannot connect")

    monkeypatch.setattr(conexao, "obter_pool", falha_conexao)
    cliente = TestClient(app, base_url="https://testserver")

    resp = cliente.post(
        "/auth/login",
        json={"email": "teste503@example.test", "senha": "SenhaForte123!@"},
    )
    assert resp.status_code == 503
    assert resp.json() == {
        "erro": "Servico indisponivel",
        "detalhes": "Falha na comunicacao com o banco de dados.",
    }
