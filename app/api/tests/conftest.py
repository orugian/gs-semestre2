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

    # Mesmas regras de app/tools/aplicar_ddl.py: todos os DDL 00N_*.sql em ordem, idempotente.
    ddl_dir = Path(__file__).resolve().parents[2] / "db" / "ddl"
    arquivos = sorted(ddl_dir.glob("[0-9][0-9][0-9]_*.sql"))
    if not arquivos:
        raise FileNotFoundError(f"Nenhum DDL encontrado em {ddl_dir}")
    ja_existe = ("ORA-00955", "ORA-01408", "ORA-02260", "ORA-02275")

    with oracledb.connect(user=user, password=password, dsn=dsn) as conexao:
        with conexao.cursor() as cursor:
            for arquivo in arquivos:
                for bloco in arquivo.read_text(encoding="utf-8").split(";"):
                    linhas = [
                        linha for linha in bloco.splitlines() if not linha.strip().startswith("--")
                    ]
                    sql = "\n".join(linhas).strip()
                    if not sql:
                        continue
                    try:
                        cursor.execute(sql)
                    except oracledb.DatabaseError as err:
                        if any(codigo in str(err) for codigo in ja_existe):
                            continue
                        raise
        conexao.commit()
