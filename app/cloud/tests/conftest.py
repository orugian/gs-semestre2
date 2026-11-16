"""Configuracoes e fixtures de teste para citizentech_cloud."""

import os
from pathlib import Path

import pg8000.dbapi
import pytest


@pytest.fixture(autouse=True)
def verificar_ambiente_postgres(request, monkeypatch):
    """Verifica e mapeia as variaveis PG_TESTE_* para testes com marcador postgres."""
    marker = request.node.get_closest_marker("postgres")
    if marker is None:
        return

    vars_requeridas = [
        "PG_TESTE_HOST",
        "PG_TESTE_PORT",
        "PG_TESTE_DB",
        "PG_TESTE_USER",
        "PG_TESTE_PASSWORD",
    ]
    faltantes = [v for v in vars_requeridas if not os.environ.get(v)]
    if faltantes:
        pytest.skip(f"Variaveis de teste Postgres faltantes: {faltantes}")

    banco = os.environ["PG_TESTE_DB"]
    if "teste" not in banco.lower():
        pytest.fail(f"Seguranca: PG_TESTE_DB ('{banco}') nao contem 'teste'. Abortando.")

    # Mapeia PG_TESTE_* -> DB_*
    monkeypatch.setenv("DB_HOST", os.environ["PG_TESTE_HOST"])
    monkeypatch.setenv("DB_PORT", os.environ["PG_TESTE_PORT"])
    monkeypatch.setenv("DB_NAME", os.environ["PG_TESTE_DB"])
    monkeypatch.setenv("DB_USER", os.environ["PG_TESTE_USER"])
    monkeypatch.setenv("DB_PASSWORD", os.environ["PG_TESTE_PASSWORD"])
    monkeypatch.setenv("DB_SSLMODE", "disable")


@pytest.fixture(autouse=True)
def preparar_banco_postgres(request):
    """Aplica o DDL de ocorrencias e limpa registros de teste antes e depois."""
    marker = request.node.get_closest_marker("postgres")
    if marker is None:
        yield
        return

    host = os.environ.get("PG_TESTE_HOST", "localhost")
    if host == "localhost":
        host = "127.0.0.1"
    port = int(os.environ.get("PG_TESTE_PORT", "5433"))
    database = os.environ.get("PG_TESTE_DB", "citizentech_teste")
    user = os.environ.get("PG_TESTE_USER", "citizentech_teste")
    password = os.environ.get("PG_TESTE_PASSWORD", "")

    # Aplicar DDL
    caminho_sql = Path(__file__).resolve().parents[1] / "sql" / "ocorrencias.sql"
    if caminho_sql.is_file():
        conteudo = caminho_sql.read_text(encoding="utf-8")
        if "-- FIM_DDL" in conteudo:
            ddl = conteudo.split("-- FIM_DDL")[0]
        else:
            ddl = conteudo

        conn = pg8000.dbapi.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database=database,
        )
        try:
            cur = conn.cursor()
            for bloco in ddl.split(";"):
                # Remove linhas de comentarios do bloco
                linhas = [
                    linha
                    for linha in bloco.splitlines()
                    if not linha.strip().startswith("--")
                ]
                stmt = "\n".join(linhas).strip()
                if stmt:
                    cur.execute(stmt)
            conn.commit()
            # Limpar antes do teste
            cur.execute("DELETE FROM ocorrencias WHERE dispositivo_id LIKE 'teste-%'")
            conn.commit()
        finally:
            conn.close()

    yield

    # Limpar apos o teste
    conn = pg8000.dbapi.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database=database,
    )
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM ocorrencias WHERE dispositivo_id LIKE 'teste-%'")
        conn.commit()
    finally:
        conn.close()
