"""Testes da rota de comparação de destinos (/me/comparacoes)."""

import json
import logging
import uuid
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

try:
    from test_mercado import criar_snapshot_sintetico
except ImportError:
    from tests.test_mercado import criar_snapshot_sintetico

from citizentech.competencias.catalogo import carregar_catalogo_competencias
from citizentech.competencias.repositorio import (
    atualizar_competencia,
    salvar_candidatas_extracao,
)
from citizentech.main import app

TERMOS_PROIBIDOS_TEXTO = [
    "vaga",
    "probabilidade de",
    "vale a pena",
]


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


def _verificar_ausencia_chaves_proibidas(obj: Any) -> None:
    proibidas = {"score", "nota", "ranking", "pontuacao", "percentual", "aderencia"}
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert k.lower() not in proibidas, f"Chave proibida encontrada: {k}"
            _verificar_ausencia_chaves_proibidas(v)
    elif isinstance(obj, list):
        for item in obj:
            _verificar_ausencia_chaves_proibidas(item)


def _verificar_ausencia_termos_texto(obj: Any) -> None:
    if isinstance(obj, dict):
        for v in obj.values():
            _verificar_ausencia_termos_texto(v)
    elif isinstance(obj, list):
        for item in obj:
            _verificar_ausencia_termos_texto(item)
    elif isinstance(obj, str):
        texto_lower = obj.lower()
        for termo in TERMOS_PROIBIDOS_TEXTO:
            assert termo not in texto_lower, f"Termo proibido '{termo}' encontrado no texto: {obj}"


@pytest.mark.oracle
@pytest.mark.mongo
def test_comparacao_sem_score_preserva_obrigatorio_e_ordem():
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "comp_red")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}

    # Conceder consentimentos 'perfil' e 'curriculo_llm'
    resp = cliente.post(
        "/me/consentimentos",
        json={"finalidade": "perfil"},
        headers=headers_csrf,
    )
    assert resp.status_code == 201
    resp = cliente.post(
        "/me/consentimentos",
        json={"finalidade": "curriculo_llm"},
        headers=headers_csrf,
    )
    assert resp.status_code == 201

    catalogo = carregar_catalogo_competencias()
    curriculo_id = uuid.uuid4().hex
    extracao_id = uuid.uuid4().hex

    # Requisitos de analista_processos:
    # 9e84a506-df06-4be3-874a-fa01293e3dd5: "processos empresariais" (obrigatorio)
    # 6a7792a9-888a-46ad-afc9-2c0d94c8fde6: "criar modelos de processos empresariais" (obrigatorio)
    esco_confirmado = "9e84a506-df06-4be3-874a-fa01293e3dd5"
    esco_pendente = "6a7792a9-888a-46ad-afc9-2c0d94c8fde6"

    candidatas = [
        {"esco_id": esco_confirmado, "trecho_origem": "Mapeamento e processos empresariais"},
        {"esco_id": esco_pendente, "trecho_origem": "Criacao de modelos de processos"},
    ]
    salvas = salvar_candidatas_extracao(
        usuario_id=usuario["id"],
        curriculo_id=curriculo_id,
        extracao_id=extracao_id,
        candidatas=candidatas,
        catalogo=catalogo,
    )
    assert len(salvas) == 2

    # Confirma apenas a primeira competencia
    comp_conf = salvas[0]
    atualizada = atualizar_competencia(
        comp_id=comp_conf["id"],
        usuario_id=usuario["id"],
        acao="confirmar",
        trecho_origem=None,
        catalogo=catalogo,
    )
    assert atualizada is not None
    assert atualizada["revisao"] == "confirmada"

    # Faz POST /me/comparacoes
    payload = {
        "destinos": ["analista_processos", "analista_dados_bi"],
        "uf": "SP",
    }
    resp_comp = cliente.post("/me/comparacoes", json=payload, headers=headers_csrf)
    assert resp_comp.status_code == 201, (
        f"Esperado 201, recebido {resp_comp.status_code}: {resp_comp.text}"
    )
    corpo = resp_comp.json()

    # Ordem dos destinos igual à do corpo
    destinos_retornados = [d["destino_id"] for d in corpo["destinos"]]
    assert destinos_retornados == ["analista_processos", "analista_dados_bi"]

    # Verifica requisitos de analista_processos
    dest_proc = corpo["destinos"][0]
    itens_proc = dest_proc["dimensoes"]["requisitos"]["itens"]
    itens_por_esco = {it["esco_id"]: it for it in itens_proc}

    # Requisito confirmado deve aparecer como 'declarada'
    assert itens_por_esco[esco_confirmado]["estado"] == "declarada"
    # Requisito pendente deve aparecer como 'desconhecida' (T07)
    assert itens_por_esco[esco_pendente]["estado"] == "desconhecida"

    # Todo requisito obrigatório não demonstrado aparece em obrigatorios_nao_atendidos
    obrigatorios_nao_atendidos = dest_proc["dimensoes"]["obrigatorios_nao_atendidos"]
    obrig_ids = {it["id_local"] for it in obrigatorios_nao_atendidos}
    for it in itens_proc:
        if it["obrigatorio"] and it["estado"] != "demonstrada":
            assert it["id_local"] in obrig_ids

    # Varredura recursiva de chaves não encontra score/nota/etc
    _verificar_ausencia_chaves_proibidas(corpo)
    # Varredura recursiva de termos proibidos de mercado/produto
    _verificar_ausencia_termos_texto(corpo)

    # GET /me/comparacoes/{id} devolve o mesmo corpo
    comp_id = corpo["comparacao_id"]
    resp_get = cliente.get(f"/me/comparacoes/{comp_id}")
    assert resp_get.status_code == 200
    assert resp_get.json() == corpo


@pytest.mark.oracle
def test_comparacao_validacoes_400_e_seguranca():
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "comp_val")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}

    # Sem consentimento 'perfil' -> 403
    resp_sem_perfil = cliente.post(
        "/me/comparacoes",
        json={"destinos": ["analista_dados_bi"], "uf": "SP"},
        headers=headers_csrf,
    )
    assert resp_sem_perfil.status_code == 403
    assert resp_sem_perfil.json()["erro"] == "Consentimento necessario"

    # Concede 'perfil'
    cliente.post("/me/consentimentos", json={"finalidade": "perfil"}, headers=headers_csrf)

    # 0 destinos -> 400
    resp = cliente.post("/me/comparacoes", json={"destinos": []}, headers=headers_csrf)
    assert resp.status_code == 400
    assert "erro" in resp.json()

    # 4 destinos -> 400
    resp = cliente.post(
        "/me/comparacoes",
        json={"destinos": ["d1", "d2", "d3", "d4"]},
        headers=headers_csrf,
    )
    assert resp.status_code == 400

    # destinos repetidos -> 400
    resp = cliente.post(
        "/me/comparacoes",
        json={"destinos": ["analista_dados_bi", "analista_dados_bi"]},
        headers=headers_csrf,
    )
    assert resp.status_code == 400

    # destino inexistente -> 400
    resp = cliente.post(
        "/me/comparacoes",
        json={"destinos": ["destino_inexistente"]},
        headers=headers_csrf,
    )
    assert resp.status_code == 400

    # uf invalida no corpo -> 400
    resp = cliente.post(
        "/me/comparacoes",
        json={"destinos": ["analista_dados_bi"], "uf": "INVALIDA"},
        headers=headers_csrf,
    )
    assert resp.status_code == 400

    # sem CSRF -> 403
    resp = cliente.post(
        "/me/comparacoes",
        json={"destinos": ["analista_dados_bi"]},
    )
    assert resp.status_code == 403

    # sem cookie -> 401
    cliente_anon = TestClient(app, base_url="https://testserver")
    resp = cliente_anon.post(
        "/me/comparacoes",
        json={"destinos": ["analista_dados_bi"]},
        headers={"X-CSRF-Token": "x"},
    )
    assert resp.status_code == 401


@pytest.mark.oracle
def test_comparacao_isolamento_outro_usuario_e_inexistente():
    cliente1 = TestClient(app, base_url="https://testserver")
    u1 = _criar_usuario_e_sessao(cliente1, "comp_u1")
    h1 = {"X-CSRF-Token": u1["csrf_token"]}
    cliente1.post("/me/consentimentos", json={"finalidade": "perfil"}, headers=h1)

    resp_c1 = cliente1.post(
        "/me/comparacoes",
        json={"destinos": ["analista_dados_bi"]},
        headers=h1,
    )
    assert resp_c1.status_code == 201
    comp_id = resp_c1.json()["comparacao_id"]

    # u2 tenta acessar comparacao de u1 -> 404 (T14)
    cliente2 = TestClient(app, base_url="https://testserver")
    _criar_usuario_e_sessao(cliente2, "comp_u2")
    resp_u2 = cliente2.get(f"/me/comparacoes/{comp_id}")
    assert resp_u2.status_code == 404

    # id inexistente -> 404
    resp_inexistente = cliente1.get(f"/me/comparacoes/{uuid.uuid4().hex}")
    assert resp_inexistente.status_code == 404


@pytest.mark.oracle
def test_comparacao_rejeita_destino_nao_aprovado_no_catalogo(tmp_path: Path, monkeypatch):
    cat_dir = tmp_path / "catalogo"
    destinos_dir = cat_dir / "destinos"
    destinos_dir.mkdir(parents=True)

    escopo = {
        "versao": "1.0.0",
        "decisao": "R29",
        "destinos": ["dest_pendente"],
    }
    (cat_dir / "escopo_mvp.json").write_text(json.dumps(escopo), encoding="utf-8")

    yaml_pendente = """
schema_version: "1.0"
destino_id: "dest_pendente"
nome: "Destino Pendente"
revisao_humana:
  status: "pendente"
populacao:
  descricao: "Descricao."
requisitos:
  - id_local: "req_1"
    esco_id: "esco-1"
    titulo_oficial: "Titulo 1"
    obrigatorio_proposto: true
"""
    (destinos_dir / "dest_pendente.yaml").write_text(yaml_pendente, encoding="utf-8")
    monkeypatch.setenv("CITIZENTECH_CATALOGO", str(cat_dir))

    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "comp_pend")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}
    cliente.post("/me/consentimentos", json={"finalidade": "perfil"}, headers=headers_csrf)

    resp = cliente.post(
        "/me/comparacoes",
        json={"destinos": ["dest_pendente"]},
        headers=headers_csrf,
    )
    assert resp.status_code == 400
    assert resp.json()["erro"] == "Requisicao invalida"


@pytest.mark.oracle
def test_comparacao_mercado_e_preferencias(tmp_path: Path, monkeypatch):
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "comp_merc")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}
    cliente.post("/me/consentimentos", json={"finalidade": "perfil"}, headers=headers_csrf)

    # 1. Sem UF no corpo e sem intencao -> mercado com motivo "uf_nao_informada"
    resp = cliente.post(
        "/me/comparacoes",
        json={"destinos": ["analista_dados_bi"]},
        headers=headers_csrf,
    )
    assert resp.status_code == 201
    mercado_d = resp.json()["destinos"][0]["dimensoes"]["mercado"]
    assert mercado_d["disponivel"] is False
    assert mercado_d["motivo"] == "uf_nao_informada"
    # Sem intencao -> conflitos e observacoes vazios
    pref_d = resp.json()["destinos"][0]["dimensoes"]["preferencias"]
    assert pref_d["conflitos"] == []
    assert pref_d["observacoes"] == []

    # 2. Registra intenção com UF="RJ" e horas_semana=2 (< 4 gera conflito)
    intencao_payload = {
        "atividades_desejadas": ["analise"],
        "motivos": ["motivo"],
        "horas_semana": 2,
        "orcamento_mensal_brl": 100.0,
        "uf": "RJ",
    }
    cliente.put("/me/intencao", json=intencao_payload, headers=headers_csrf)

    # 3. Snapshot indisponível -> continua 201 com motivo "snapshot_indisponivel"
    monkeypatch.delenv("CITIZENTECH_MERCADO_SNAPSHOT", raising=False)
    resp = cliente.post(
        "/me/comparacoes",
        json={"destinos": ["analista_dados_bi"]},
        headers=headers_csrf,
    )
    assert resp.status_code == 201
    mercado_d = resp.json()["destinos"][0]["dimensoes"]["mercado"]
    assert mercado_d["disponivel"] is False
    assert mercado_d["motivo"] == "snapshot_indisponivel"
    # Com horas_semana=2 -> conflito gerado
    pref_d = resp.json()["destinos"][0]["dimensoes"]["preferencias"]
    assert len(pref_d["conflitos"]) > 0

    # 4. Com snapshot sintético válido
    dir_snap = tmp_path / "snap"
    criar_snapshot_sintetico(dir_snap)
    monkeypatch.setenv("CITIZENTECH_MERCADO_SNAPSHOT", str(dir_snap))

    # Testando com UF="SP" informada no corpo
    resp = cliente.post(
        "/me/comparacoes",
        json={"destinos": ["analista_dados_bi"], "uf": "SP"},
        headers=headers_csrf,
    )
    assert resp.status_code == 201
    mercado_d = resp.json()["destinos"][0]["dimensoes"]["mercado"]
    assert mercado_d["disponivel"] is True
    assert mercado_d["natureza"] == "observado"
    assert "Novo Caged" in mercado_d["fonte"]
    assert mercado_d["unidade"] == "admissões por mês"
    assert mercado_d["uf"] == "SP"
    # No snapshot padrão, o último observado válido para analista_dados_bi/SP é 20.0 em 202501
    assert mercado_d["ultimo_observado"]["competencia"] == "202501"
    assert mercado_d["ultimo_observado"]["valor"] == 20.0


@pytest.mark.oracle
def test_comparacao_nao_vaza_dados_em_log(caplog):
    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "comp_log")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}
    cliente.post("/me/consentimentos", json={"finalidade": "perfil"}, headers=headers_csrf)

    catalogo = carregar_catalogo_competencias()
    trecho_secreto = "TRECHO_SENSIVEL_DE_PROCESSO_XPTO_98765"
    candidatas = [
        {
            "esco_id": "9e84a506-df06-4be3-874a-fa01293e3dd5",
            "trecho_origem": trecho_secreto,
        }
    ]
    salvar_candidatas_extracao(
        usuario_id=usuario["id"],
        curriculo_id=uuid.uuid4().hex,
        extracao_id=uuid.uuid4().hex,
        candidatas=candidatas,
        catalogo=catalogo,
    )

    with caplog.at_level(logging.DEBUG):
        resp = cliente.post(
            "/me/comparacoes",
            json={"destinos": ["analista_processos"]},
            headers=headers_csrf,
        )
        assert resp.status_code == 201

    assert trecho_secreto not in caplog.text


@pytest.mark.oracle
@pytest.mark.mongo
def test_comparacao_apos_exercicio_demonstrada():
    """Valida integracao S13 com comparacao: tentativa demonstrada."""
    from citizentech.llm.cliente import ClienteLLM, RespostaLLM, obter_cliente_llm

    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "comp_ex_dem")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}

    cliente.post("/me/consentimentos", json={"finalidade": "perfil"}, headers=headers_csrf)
    cliente.post("/me/consentimentos", json={"finalidade": "curriculo_llm"}, headers=headers_csrf)

    class FakeLLMSucesso(ClienteLLM):
        def gerar_json(self, mensagens, schema, nome_schema, validar=None):
            dados = {
                "criterios": [
                    {
                        "id": "crit_redesenho_fluxo",
                        "nivel": 2,
                        "justificativa": "ok",
                        "trecho_resposta": "fluxo to-be validado",
                    },
                    {
                        "id": "crit_gestao_riscos",
                        "nivel": 2,
                        "justificativa": "ok",
                        "trecho_resposta": "fluxo to-be validado",
                    },
                    {
                        "id": "crit_indicadores_kpis",
                        "nivel": 2,
                        "justificativa": "ok",
                        "trecho_resposta": "fluxo to-be validado",
                    },
                ]
            }
            if validar:
                validar(dados)
            return RespostaLLM(dados=dados, modelo="fake", tentativas=1, uso=None)

    app.dependency_overrides[obter_cliente_llm] = lambda: FakeLLMSucesso()

    try:
        token = uuid.uuid4().hex[:8]
        payload_ex = {
            "destino_id": "analista_processos",
            "exercicio_id": "ex_analista_processos_01",
            "respostas_objetivas": {"q1": "C", "q2": "D", "q3": "A", "q4": "B"},
            "resposta_aberta": f"Proposta com fluxo TO-BE validado {token} para comparacao.",
        }
        r_tentativa = cliente.post("/me/tentativas", json=payload_ex, headers=headers_csrf)
        assert r_tentativa.status_code == 201
        assert r_tentativa.json()["resultado"] == "demonstrada"

        # Executa comparacao
        r_comp = cliente.post(
            "/me/comparacoes",
            json={"destinos": ["analista_processos"]},
            headers=headers_csrf,
        )
        assert r_comp.status_code == 201
        dados_comp = r_comp.json()

        dest = dados_comp["destinos"][0]
        reqs_map = {r["id_local"]: r for r in dest["dimensoes"]["requisitos"]["itens"]}

        # Requisitos avaliados no exercicio devem estar 'demonstrada'
        for req_id in [
            "processos_empresariais",
            "criar_modelos_processos_empresariais",
            "analisar_processos_empresariais",
        ]:
            assert reqs_map[req_id]["estado"] == "demonstrada"
            assert reqs_map[req_id]["motivo"] is None
        # Requisitos que o exercício NÃO avalia continuam sem informação (RV-S13-06)
        for req_id in ["analisar_dados", "garantia_qualidade_dados"]:
            assert reqs_map[req_id]["estado"] == "desconhecida"
            assert reqs_map[req_id]["motivo"] == "sem_informacao_suficiente"
    finally:
        app.dependency_overrides.pop(obter_cliente_llm, None)


@pytest.mark.oracle
@pytest.mark.mongo
def test_comparacao_apos_exercicio_insuficiente():
    """Valida integracao S13: tentativa insuficiente classifica requisitos como lacuna."""
    from citizentech.llm.cliente import ClienteLLM, RespostaLLM, obter_cliente_llm

    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "comp_ex_insuf")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}

    cliente.post("/me/consentimentos", json={"finalidade": "perfil"}, headers=headers_csrf)
    cliente.post("/me/consentimentos", json={"finalidade": "curriculo_llm"}, headers=headers_csrf)

    class FakeLLMZero(ClienteLLM):
        def gerar_json(self, mensagens, schema, nome_schema, validar=None):
            dados = {
                "criterios": [
                    {
                        "id": "crit_redesenho_fluxo",
                        "nivel": 0,
                        "justificativa": "ruim",
                        "trecho_resposta": "",
                    },
                    {
                        "id": "crit_gestao_riscos",
                        "nivel": 0,
                        "justificativa": "ruim",
                        "trecho_resposta": "",
                    },
                    {
                        "id": "crit_indicadores_kpis",
                        "nivel": 0,
                        "justificativa": "ruim",
                        "trecho_resposta": "",
                    },
                ]
            }
            if validar:
                validar(dados)
            return RespostaLLM(dados=dados, modelo="fake", tentativas=1, uso=None)

    app.dependency_overrides[obter_cliente_llm] = lambda: FakeLLMZero()

    try:
        token = uuid.uuid4().hex[:8]
        payload_ex = {
            "destino_id": "analista_processos",
            "exercicio_id": "ex_analista_processos_01",
            "respostas_objetivas": {"q1": "A", "q2": "A", "q3": "B", "q4": "C"},  # 0 acertos
            "resposta_aberta": f"Resposta insuficiente {token} para teste de lacuna.",
        }
        r_tentativa = cliente.post("/me/tentativas", json=payload_ex, headers=headers_csrf)
        assert r_tentativa.status_code == 201
        assert r_tentativa.json()["resultado"] == "insuficiente"

        # Executa comparacao
        r_comp = cliente.post(
            "/me/comparacoes",
            json={"destinos": ["analista_processos"]},
            headers=headers_csrf,
        )
        assert r_comp.status_code == 201
        dados_comp = r_comp.json()

        dest = dados_comp["destinos"][0]
        reqs_map = {r["id_local"]: r for r in dest["dimensoes"]["requisitos"]["itens"]}

        for req_id in [
            "processos_empresariais",
            "criar_modelos_processos_empresariais",
            "analisar_processos_empresariais",
        ]:
            assert reqs_map[req_id]["estado"] == "lacuna"
            assert reqs_map[req_id]["motivo"] == "exercicio_abaixo_do_minimo"
    finally:
        app.dependency_overrides.pop(obter_cliente_llm, None)


@pytest.mark.oracle
@pytest.mark.mongo
def test_comparacao_apos_exercicio_parcial():
    """Valida integracao S13: tentativa parcial classifica requisitos como desconhecida."""
    from citizentech.llm.cliente import ClienteLLM, ErroLLM, obter_cliente_llm

    cliente = TestClient(app, base_url="https://testserver")
    usuario = _criar_usuario_e_sessao(cliente, "comp_ex_parc")
    headers_csrf = {"X-CSRF-Token": usuario["csrf_token"]}

    cliente.post("/me/consentimentos", json={"finalidade": "perfil"}, headers=headers_csrf)
    cliente.post("/me/consentimentos", json={"finalidade": "curriculo_llm"}, headers=headers_csrf)

    class FakeLLMFalha(ClienteLLM):
        def gerar_json(self, mensagens, schema, nome_schema, validar=None):
            raise ErroLLM("Indisponibilidade simulada")

    app.dependency_overrides[obter_cliente_llm] = lambda: FakeLLMFalha()

    try:
        token = uuid.uuid4().hex[:8]
        payload_ex = {
            "destino_id": "analista_processos",
            "exercicio_id": "ex_analista_processos_01",
            "respostas_objetivas": {"q1": "C", "q2": "D", "q3": "A", "q4": "B"},
            "resposta_aberta": f"Resposta valida {token} mas LLM caira para parcial.",
        }
        r_tentativa = cliente.post("/me/tentativas", json=payload_ex, headers=headers_csrf)
        assert r_tentativa.status_code == 201
        assert r_tentativa.json()["resultado"] == "parcial"

        # Executa comparacao
        r_comp = cliente.post(
            "/me/comparacoes",
            json={"destinos": ["analista_processos"]},
            headers=headers_csrf,
        )
        assert r_comp.status_code == 201
        dados_comp = r_comp.json()

        dest = dados_comp["destinos"][0]
        reqs_map = {r["id_local"]: r for r in dest["dimensoes"]["requisitos"]["itens"]}

        for req_id in [
            "processos_empresariais",
            "criar_modelos_processos_empresariais",
            "analisar_processos_empresariais",
        ]:
            assert reqs_map[req_id]["estado"] == "desconhecida"
            assert reqs_map[req_id]["motivo"] == "avaliacao_parcial_llm_indisponivel"
    finally:
        app.dependency_overrides.pop(obter_cliente_llm, None)
