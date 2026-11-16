"""Isolamento dos testes: nenhum teste le ou grava no diretorio real de dados nem chama a nuvem."""

import os
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def ambiente_isolado(monkeypatch, tmp_path_factory):
    """Aponta os dados para uma pasta temporaria e remove configuracao herdada do processo.

    Cada teste define o que precisa com monkeypatch.setenv; o que ele nao definir cai na pasta
    temporaria, nunca em CITIZENTECH_DADOS real (onde um outbox.db de teste poderia depois ser
    enviado a Lambda verdadeira).
    """
    monkeypatch.setenv("CITIZENTECH_DADOS", str(tmp_path_factory.mktemp("dados_isolados")))
    for variavel in (
        "CITIZENTECH_LEITURAS_CSV",
        "CITIZENTECH_OUTBOX_DB",
        "CITIZENTECH_RATE_LIMIT_POR_MINUTO",
        "FUNCTION_URL",
        "DEVICE_KEY",
    ):
        monkeypatch.delenv(variavel, raising=False)


@pytest.fixture(autouse=True)
def configurar_jwt_secret_padrao(monkeypatch):
    """Configura segredo JWT padrao de 32+ caracteres para testes de autenticacao."""
    monkeypatch.setenv(
        "JWT_SECRET",
        "segredo-de-teste-super-seguro-com-mais-de-32-caracteres-para-jwt",
    )


@pytest.fixture(autouse=True)
def resetar_limitador_entre_testes():
    """Garante que o limitador de taxa de login em memoria seja resetado a cada teste."""
    from citizentech.auth.limitador import limitador_login

    limitador_login.resetar()


def pytest_runtest_setup(item):
    """Verifica se teste marcado com oracle ou mongo possui credenciais configuradas."""
    if "oracle" in item.keywords:
        dsn = os.environ.get("ORACLE_DSN")
        user = os.environ.get("ORACLE_USER")
        password = os.environ.get("ORACLE_PASSWORD")
        if not (dsn and user and password):
            pytest.skip("Oracle de teste não configurado")
        if not (user.startswith("CT_") and "TESTE" in user.upper()):
            pytest.fail(
                "Usuario Oracle inseguro para testes: deve comecar com CT_ e conter TESTE."
            )

    if "mongo" in item.keywords:
        uri = os.environ.get("MONGODB_URI")
        db = os.environ.get("MONGODB_DB")
        if not (uri and db):
            pytest.skip("Mongo de teste não configurado")
        if "teste" not in db.lower():
            pytest.fail(
                "Banco MongoDB inseguro para testes: nome deve conter 'teste'."
            )


@pytest.fixture(scope="session", autouse=True)
def aplicar_ddl_oracle_teste():
    """Aplica o DDL de usuario e consentimento no schema de teste se configurado."""
    dsn = os.environ.get("ORACLE_DSN")
    user = os.environ.get("ORACLE_USER")
    password = os.environ.get("ORACLE_PASSWORD")
    if not (dsn and user and password):
        return

    if not (user.startswith("CT_") and "TESTE" in user.upper()):
        pytest.fail(
            "Usuario Oracle inseguro para testes: deve comecar com CT_ e conter TESTE."
        )

    try:
        import oracledb
    except ImportError:
        return

    caminho_ddl_001 = (
        Path(__file__).resolve().parents[2] / "db" / "ddl" / "001_usuario_consentimento.sql"
    )
    caminho_ddl_002 = (
        Path(__file__).resolve().parents[2] / "db" / "ddl" / "002_competencias.sql"
    )
    caminho_ddl_003 = (
        Path(__file__).resolve().parents[2] / "db" / "ddl" / "003_intencao_comparacao.sql"
    )
    caminho_ddl_005 = (
        Path(__file__).resolve().parents[2] / "db" / "ddl" / "005_plano.sql"
    )
    if not caminho_ddl_001.is_file():
        raise FileNotFoundError(f"Arquivo DDL nao encontrado: {caminho_ddl_001}")
    if not caminho_ddl_002.is_file():
        raise FileNotFoundError(f"Arquivo DDL nao encontrado: {caminho_ddl_002}")
    if not caminho_ddl_003.is_file():
        raise FileNotFoundError(f"Arquivo DDL nao encontrado: {caminho_ddl_003}")
    if not caminho_ddl_005.is_file():
        raise FileNotFoundError(f"Arquivo DDL nao encontrado: {caminho_ddl_005}")

    with oracledb.connect(user=user, password=password, dsn=dsn) as conexao:
        with conexao.cursor() as cursor:
            try:
                cursor.execute("SELECT 1 FROM usuario WHERE ROWNUM = 1")
                cursor.execute("SELECT 1 FROM consentimento WHERE ROWNUM = 1")
                cursor.execute("SELECT 1 FROM competencia_usuario WHERE ROWNUM = 1")
                cursor.execute("SELECT 1 FROM intencao WHERE ROWNUM = 1")
                cursor.execute("SELECT 1 FROM comparacao WHERE ROWNUM = 1")
                cursor.execute("SELECT 1 FROM comparacao_destino WHERE ROWNUM = 1")
                cursor.execute("SELECT 1 FROM caminho_escolhido WHERE ROWNUM = 1")
                cursor.execute("SELECT 1 FROM plano WHERE ROWNUM = 1")
                cursor.execute("SELECT 1 FROM checkpoint WHERE ROWNUM = 1")
                return
            except oracledb.DatabaseError:
                pass

            for caminho_ddl in (
                caminho_ddl_001,
                caminho_ddl_002,
                caminho_ddl_003,
                caminho_ddl_005,
            ):
                conteudo = caminho_ddl.read_text(encoding="utf-8")
                for bloco in conteudo.split(";"):
                    linhas = [
                        linha
                        for linha in bloco.splitlines()
                        if not linha.strip().startswith("--")
                    ]
                    sql = "\n".join(linhas).strip()
                    if not sql:
                        continue
                    try:
                        cursor.execute(sql)
                    except oracledb.DatabaseError as err:
                        msg = str(err)
                        # ORA-00955: name is already used by an existing object
                        # ORA-01408: such column list already indexed
                        if "ORA-00955" in msg or "ORA-01408" in msg:
                            continue
                        raise
        conexao.commit()
