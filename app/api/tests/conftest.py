"""Isolamento dos testes: nenhum teste le ou grava no diretorio real de dados nem chama a nuvem."""

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