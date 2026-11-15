"""Aceite independente S5 (orquestrador): Oracle real no schema de teste, sem mocks de banco."""

import time
import uuid

import jwt
import pytest
from fastapi.testclient import TestClient

from citizentech.auth import senhas
from citizentech.main import app

SENHA = "Senha-de-fixture-123"
SEGREDO = "segredo-de-teste-super-seguro-com-mais-de-32-caracteres-para-jwt"


def _cliente(ip: str = "testclient") -> TestClient:
    return TestClient(
        app, base_url="https://testserver", client=(ip, 50000), raise_server_exceptions=False
    )


def _email() -> str:
    return f"aceite_{uuid.uuid4().hex[:12]}@example.test"


def _conta(cliente: TestClient | None = None) -> tuple[TestClient, str, str]:
    """Registra, entra e devolve (cliente com cookies, email, token csrf)."""
    cliente = cliente or _cliente()
    email = _email()
    assert cliente.post("/auth/registrar", json={"email": email, "senha": SENHA}).status_code == 201
    r = cliente.post("/auth/login", json={"email": email, "senha": SENHA})
    assert r.status_code == 200
    return cliente, email, cliente.cookies.get("csrf_token")


class _ContadorHasher:
    def __init__(self, real):
        self._real = real
        self.verificacoes = 0

    def verify(self, *args, **kwargs):
        self.verificacoes += 1
        return self._real.verify(*args, **kwargs)

    def __getattr__(self, nome):
        return getattr(self._real, nome)


@pytest.mark.oracle
def test_csrf_de_outra_sessao_do_mesmo_usuario_e_recusado():
    a, email, csrf_a = _conta()
    b = _cliente()
    assert b.post("/auth/login", json={"email": email, "senha": SENHA}).status_code == 200
    csrf_b = b.cookies.get("csrf_token")
    assert csrf_a != csrf_b
    corpo = {"finalidade": "perfil"}
    assert (
        a.post("/me/consentimentos", json=corpo, headers={"X-CSRF-Token": csrf_b}).status_code
        == 403
    )
    assert (
        a.post("/me/consentimentos", json=corpo, headers={"X-CSRF-Token": csrf_a}).status_code
        == 201
    )


@pytest.mark.oracle
def test_cookie_csrf_trocado_pelo_atacante_nao_vale():
    a, _, _ = _conta()
    a.cookies.set("csrf_token", "valor-do-atacante")
    r = a.post(
        "/me/consentimentos",
        json={"finalidade": "perfil"},
        headers={"X-CSRF-Token": "valor-do-atacante"},
    )
    assert r.status_code == 403


@pytest.mark.oracle
def test_sessao_encerrada_nao_muta_nem_le():
    a, _, csrf = _conta()
    copia = _cliente()
    copia.cookies.set("sessao", a.cookies.get("sessao"))
    assert a.post("/auth/logout", headers={"X-CSRF-Token": csrf}).status_code == 204
    assert copia.get("/me").status_code == 401
    r = copia.post(
        "/me/consentimentos", json={"finalidade": "perfil"}, headers={"X-CSRF-Token": csrf}
    )
    assert r.status_code == 401


@pytest.mark.oracle
def test_logout_expira_os_dois_cookies_com_atributos_de_seguranca():
    a, _, csrf = _conta()
    r = a.post("/auth/logout", headers={"X-CSRF-Token": csrf})
    cookies = r.headers.get_list("set-cookie")
    for nome in ("sessao=", "csrf_token="):
        linha = next(c for c in cookies if c.startswith(nome))
        assert "Max-Age=0" in linha and "Secure" in linha and "SameSite=lax" in linha


@pytest.mark.parametrize(
    "claims,algoritmo,segredo",
    [
        ({"ver": 0, "csrf": "x", "exp": 4102444800}, "HS512", SEGREDO),
        (
            {"ver": 0, "csrf": "x", "exp": 4102444800},
            "HS256",
            "outro-segredo-com-mais-de-32-caracteres-aqui",
        ),
        ({"ver": 0, "csrf": "x"}, "HS256", SEGREDO),
        ({"ver": 99, "csrf": "x", "exp": 4102444800}, "HS256", SEGREDO),
        ({"ver": 0, "csrf": "x", "exp": 1}, "HS256", SEGREDO),
    ],
)
@pytest.mark.oracle
def test_token_forjado_ou_incoerente_e_recusado(claims, algoritmo, segredo):
    a, _, _ = _conta()
    # Partir de uma sessao realmente aceita isola a propriedade alterada.
    assert a.get("/me").status_code == 200
    base = jwt.decode(a.cookies.get("sessao"), SEGREDO, algorithms=["HS256"])
    assert {"sub", "iat", "exp", "jti", "ver", "csrf"} <= set(base)
    if "exp" not in claims:
        base.pop("exp")
    # Preservar csrf e versao, exceto quando a versao e o defeito sob teste.
    alteracoes = {k: v for k, v in claims.items() if k != "csrf"}
    token = jwt.encode({**base, **alteracoes}, segredo, algoritmo)
    forjado = _cliente()
    forjado.cookies.set("sessao", token)
    assert forjado.get("/me").status_code == 401


@pytest.mark.oracle
def test_me_devolve_somente_os_campos_do_contrato():
    a, email, _ = _conta()
    corpo = a.get("/me").json()
    assert set(corpo) == {"id", "email", "criado_em", "persona_demo"}
    assert corpo["email"] == email and corpo["persona_demo"] == "N"
    assert corpo["criado_em"].endswith("Z")


@pytest.mark.oracle
def test_login_inexistente_e_senha_errada_sao_indistinguiveis(monkeypatch):
    _, email, _ = _conta()
    contador = _ContadorHasher(senhas._hasher)
    monkeypatch.setattr(senhas, "_hasher", contador)
    errada = _cliente("10.0.0.1").post(
        "/auth/login", json={"email": email, "senha": "Outra-senha-12345"}
    )
    apos_errada = contador.verificacoes
    inexistente = _cliente("10.0.0.2").post(
        "/auth/login", json={"email": _email(), "senha": "Outra-senha-12345"}
    )
    assert errada.status_code == inexistente.status_code == 401
    assert errada.json() == inexistente.json()
    assert "set-cookie" not in errada.headers and "set-cookie" not in inexistente.headers
    assert apos_errada == 1 and contador.verificacoes == 2


@pytest.mark.oracle
def test_senha_gigante_no_login_e_recusada_sem_calcular_hash(monkeypatch):
    _, email, _ = _conta()
    contador = _ContadorHasher(senhas._hasher)
    monkeypatch.setattr(senhas, "_hasher", contador)
    r = _cliente("10.0.0.3").post("/auth/login", json={"email": email, "senha": "x" * 5000})
    assert r.status_code == 400
    assert contador.verificacoes == 0


@pytest.mark.oracle
def test_limite_por_email_vale_mesmo_trocando_de_endereco():
    email = _email()
    # Registro nao faz login: nenhuma das cinco tentativas foi consumida no preparo.
    assert (
        _cliente().post("/auth/registrar", json={"email": email, "senha": SENHA}).status_code == 201
    )
    for i in range(5):
        r = _cliente(f"10.1.0.{i}").post(
            "/auth/login", json={"email": email, "senha": "errada-12345"}
        )
        assert r.status_code == 401
    variacao = f"  {email.upper()} "
    r = _cliente("10.1.0.99").post("/auth/login", json={"email": variacao, "senha": SENHA})
    assert r.status_code == 429
    assert int(r.headers["retry-after"]) >= 1
    assert "set-cookie" not in r.headers


@pytest.mark.oracle
def test_limite_por_endereco_ignora_x_forwarded_for():
    cliente = _cliente("10.2.0.1")
    for i in range(5):
        r = cliente.post(
            "/auth/login",
            json={"email": _email(), "senha": "errada-12345"},
            headers={"X-Forwarded-For": f"203.0.113.{i}"},
        )
        assert r.status_code == 401
    r = cliente.post(
        "/auth/login",
        json={"email": _email(), "senha": "errada-12345"},
        headers={"X-Forwarded-For": "203.0.113.200"},
    )
    assert r.status_code == 429


@pytest.mark.oracle
def test_t14_outro_usuario_nao_ve_nem_revoga_e_resposta_nao_denuncia():
    a, _, csrf_a = _conta()
    b, _, csrf_b = _conta()
    criado = a.post(
        "/me/consentimentos", json={"finalidade": "curriculo_llm"}, headers={"X-CSRF-Token": csrf_a}
    )
    assert criado.status_code == 201
    cid = criado.json()["id"]
    alheio = b.delete(f"/me/consentimentos/{cid}", headers={"X-CSRF-Token": csrf_b})
    inexistente = b.delete(
        f"/me/consentimentos/{uuid.uuid4().hex}", headers={"X-CSRF-Token": csrf_b}
    )
    injecao = b.delete(
        "/me/consentimentos/1%27%20OR%20%271%27%3D%271", headers={"X-CSRF-Token": csrf_b}
    )
    assert alheio.status_code == inexistente.status_code == injecao.status_code == 404
    assert alheio.json() == inexistente.json() == injecao.json()
    assert b.get("/me/consentimentos").json()["itens"] == []
    itens_a = a.get("/me/consentimentos").json()["itens"]
    assert [i["id"] for i in itens_a] == [cid] and itens_a[0]["revogado_em"] is None


@pytest.mark.oracle
def test_revogacao_e_idempotente_e_preserva_a_data():
    a, _, csrf = _conta()
    cid = a.post(
        "/me/consentimentos", json={"finalidade": "perfil"}, headers={"X-CSRF-Token": csrf}
    ).json()["id"]
    assert a.delete(f"/me/consentimentos/{cid}", headers={"X-CSRF-Token": csrf}).status_code == 204
    primeira = a.get("/me/consentimentos").json()["itens"][0]["revogado_em"]
    assert primeira and primeira.endswith("Z")
    time.sleep(1.1)
    assert a.delete(f"/me/consentimentos/{cid}", headers={"X-CSRF-Token": csrf}).status_code == 204
    assert a.get("/me/consentimentos").json()["itens"][0]["revogado_em"] == primeira


@pytest.mark.parametrize(
    "rota,corpo",
    [
        ("/auth/registrar", {"email": "pessoa-zq@", "senha": "segredo-zq-123456"}),
        ("/auth/registrar", {"email": "pessoa-zq@example.test", "senha": "zq"}),
        (
            "/auth/registrar",
            {"email": "pessoa-zq@example.test", "senha": "segredo-zq-123456", "x": 1},
        ),
        ("/auth/login", {"email": 12345, "senha": "segredo-zq-123456"}),
        ("/auth/login", ["pessoa-zq@example.test", "segredo-zq-123456"]),
    ],
)
def test_validacao_responde_400_sem_repetir_o_que_recebeu(rota, corpo):
    r = _cliente().post(rota, json=corpo)
    assert r.status_code == 400
    assert set(r.json()) == {"erro", "detalhes"}
    assert "zq" not in r.text and "12345" not in r.text


def test_banco_fora_do_ar_responde_503_sem_detalhe_interno(monkeypatch):
    import oracledb

    from citizentech.banco import conexao

    def falha():
        raise oracledb.DatabaseError("ORA-12541: sem listener em host-interno-zq:1521")

    monkeypatch.setattr(conexao, "obter_pool", falha)
    cliente = _cliente()
    for rota, corpo in (
        ("/auth/login", {"email": _email(), "senha": SENHA}),
        ("/auth/registrar", {"email": _email(), "senha": SENHA}),
    ):
        r = cliente.post(rota, json=corpo)
        assert r.status_code == 503
        assert "ORA-" not in r.text and "host-interno-zq" not in r.text
    assert cliente.get("/health").status_code == 200


def test_mutacao_sem_sessao_e_401_mesmo_com_cabecalho_csrf():
    r = _cliente().post(
        "/me/consentimentos", json={"finalidade": "perfil"}, headers={"X-CSRF-Token": "x"}
    )
    assert r.status_code == 401
