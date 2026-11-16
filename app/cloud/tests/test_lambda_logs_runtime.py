"""Logs INFO visíveis no runtime da Lambda e diagnóstico seguro de falha de conexão."""

import logging

import pg8000.dbapi
import pytest

from citizentech_cloud import banco


def test_logger_do_pacote_emite_info_mesmo_com_raiz_em_warning(monkeypatch):
    """O runtime Python da AWS deixa o logger raiz em WARNING; o enunciado exige INFO."""
    import importlib

    import citizentech_cloud.lambda_function as modulo

    raiz = logging.getLogger()
    nivel_original = raiz.level
    raiz.setLevel(logging.WARNING)
    try:
        importlib.reload(modulo)
        assert logging.getLogger("citizentech_cloud").getEffectiveLevel() <= logging.INFO
        assert modulo.logger.isEnabledFor(logging.INFO)
    finally:
        raiz.setLevel(nivel_original)


def test_falha_de_conexao_loga_sqlstate_sem_segredo(monkeypatch, caplog):
    def conectar_falho(**kwargs):
        raise pg8000.dbapi.DatabaseError(
            {"S": "FATAL", "C": "28P01", "M": "password authentication failed for user x"}
        )

    monkeypatch.setattr(pg8000.dbapi, "connect", conectar_falho)
    monkeypatch.setenv("DB_SSLMODE", "disable")
    monkeypatch.setenv("DB_PASSWORD", "senha-que-nao-pode-aparecer")
    with caplog.at_level(logging.ERROR), pytest.raises(banco.BancoIndisponivelError):
        banco.obter_conexao()
    assert "DatabaseError" in caplog.text
    assert "28P01" in caplog.text
    assert "senha-que-nao-pode-aparecer" not in caplog.text
    assert "password authentication failed" not in caplog.text
