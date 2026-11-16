"""Testes unitarios para banco.py: configuracao SSL e hash canonico."""

import logging
import ssl

import pytest

from citizentech_cloud.banco import (
    BancoIndisponivelError,
    calcular_hash_conteudo,
    montar_config_conexao,
)


def test_montar_config_conexao_fail_closed_sem_ca(monkeypatch, caplog):
    """Quando DB_SSLMODE != disable e nenhum bundle CA e fornecido, falha fechado (503)."""
    monkeypatch.setenv("DB_SSLMODE", "verify-full")
    monkeypatch.delenv("DB_SSLROOTCERT", raising=False)

    with caplog.at_level(logging.ERROR), pytest.raises(BancoIndisponivelError):
        montar_config_conexao()

    assert "bundle CA ausente" in caplog.text


CERT_VALIDO_PEM = """-----BEGIN CERTIFICATE-----
MIIFgzCCA2ugAwIBAgIPXZONMGc2yAYdGsdUhGkHMA0GCSqGSIb3DQEBCwUAMDsx
CzAJBgNVBAYTAkVTMREwDwYDVQQKDAhGTk1ULVJDTTEZMBcGA1UECwwQQUMgUkFJ
WiBGTk1ULVJDTTAeFw0wODEwMjkxNTU5NTZaFw0zMDAxMDEwMDAwMDBaMDsxCzAJ
BgNVBAYTAkVTMREwDwYDVQQKDAhGTk1ULVJDTTEZMBcGA1UECwwQQUMgUkFJWiBG
Tk1ULVJDTTCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoCggIBALpxgHpMhm5/
yBNtwMZ9HACXjywMI7sQmkCpGreHiPibVmr75nuOi5KOpyVdWRHbNi63URcfqQgf
BBckWKo3Shjf5TnUV/3XwSyRAZHiItQDwFj8d0fsjz50Q7qsNI1NOHZnjrDIbzAz
WHFctPVrbtQBULgTfmxKo0nRIBnuvMApGGWn3v7v3QqQIecaZ5JCEJhfTzC8PhxF
tBDXaEAUwED653cXeuYLj2VbPNmaUtu1vZ5Gzz3rkQUCwJaydkxNEJY7kvqcfw+Z
374jNUUeAlz+taibmSXaXvMiwzn15Cou08YfxGyqxRxqAQVKL9LFwag0Jl1mpdIC
IfkYtwb1TplvqKtMUejPUBjFd8g5CSxJkjKZqLsXF3mwWsXmo8RZZUc1g16p6DUL
mbvkzSDGm0oGObVo/CK67lWMK07q87Hj/LaZmtVC+nFNCM+HHmpxffnTtOmlcYF7
wk5HlqX2doWjKI/pgG6BU6VtX7hI+cL5NqYuSf+4lsKMB7ObiFj86xsc3i1w4peS
MKGJ47xVqCfWS+2QrYv6YyVZLag13cqXM7zlzced0ezvXg5KkAYmY6252TUtB7p2
ZSysV4999AeU14ECll2jB0nVetBX+RvnU0Z1qrB5QstocQjpYL05ac70r8NWQMet
UqIJ5G+GR4of6ygnXYMgrwTJbFaai0b1AgMBAAGjgYMwgYAwDwYDVR0TAQH/BAUw
AwEB/zAOBgNVHQ8BAf8EBAMCAQYwHQYDVR0OBBYEFPd9xf3E6Jobd2Sn9R2gzL+H
YJptMD4GA1UdIAQ3MDUwMwYEVR0gADArMCkGCCsGAQUFBwIBFh1odHRwOi8vd3d3
LmNlcnQuZm5tdC5lcy9kcGNzLzANBgkqhkiG9w0BAQsFAAOCAgEAB5BK3/MjTvDD
nFFlm5wioooMhfNzKWtN/gHiqQxjAb8EZ6WdmF/9ARP67Jpi6Yb+tmLSbkyU+8B1
RXxlDPiyN8+sD8+Nb/kZ94/sHvJwnvDKuO+3/3Y3dlv2bojzr2IyIpMNOmqOFGYM
LVN0V2Ue1bLdI4E7pWYjJ2cJj+F3qkPNZVEI7VFY/uY5+ctHhKQV8Xa7pO6kO8Rf
77IzlhEYt8llvhjho6Tc+hj507wTmzl6NLrTQfv6MooqtyuGC2mDOL7Nii4LcK2N
JpLuHvUBKwrZ1pebbuCoGRw6IYsMHkCtA+fdZn71uSANA+iW+YJF1DngoABd15jm
fZ5nc8OaKveri6E6FO80vFIOiZiaBECEHX5FaZNXzuvO+FB8TxxuBEOb+dY7Ixjp
6o7RTUaN8Tvkasq6+yO3m/qZASlaWFot4/nUbQ4mrcFuNLwy+AwF+mWj2zs3gyLp
1txyM/1d8iC9djwj2ij3+RvrWWTV3F9yfiD8zYm1kGdNYno/Tq0dwzn+evQoFt9B
9kiABdcPUXmsEKvU7ANm5mqwujGSQkBqvjrTcuFqN1W8rB2Vt2lh8kORdOag0wok
RqEIr9baRRmW1FMdW4R58MD3R++Lj8UGrp1MYp3/RgT408m2ECVAdf4WqslKYIYv
uu8wd+RU4riEmViAqhOLUTpPSPaLtrM=
-----END CERTIFICATE-----
"""


def test_montar_config_conexao_verify_full(tmp_path, monkeypatch):
    ca_file = tmp_path / "global-bundle.pem"
    ca_file.write_text(CERT_VALIDO_PEM, encoding="utf-8")

    monkeypatch.setenv("DB_SSLMODE", "verify-full")
    monkeypatch.setenv("DB_SSLROOTCERT", str(ca_file))
    monkeypatch.setenv("DB_HOST", "rds-postgres.citizentech.com")
    monkeypatch.setenv("DB_PORT", "5432")

    config = montar_config_conexao()
    assert config["host"] == "rds-postgres.citizentech.com"
    assert config["port"] == 5432
    assert isinstance(config["ssl_context"], ssl.SSLContext)
    assert config["ssl_context"].check_hostname is True


def test_montar_config_conexao_disable(monkeypatch):
    monkeypatch.setenv("DB_SSLMODE", "disable")
    config = montar_config_conexao()
    assert config["ssl_context"] is None


def test_hash_conteudo_canonico_independe_da_ordem_de_chaves():
    dados1 = {
        "dispositivo_id": "disp-01",
        "metrica": "temperatura_c",
        "unidade": "C",
        "valor": 25.0,
        "sessao_laboratorio_id": "sessao-1",
        "ciclo_id": "ciclo-1",
        "tipo_dispositivo": "sensor_bancada",
        "medido_em": "2026-11-16T12:00:00Z",
    }
    # Mesmos dados em ordem reversa
    dados2 = {k: dados1[k] for k in reversed(list(dados1.keys()))}

    h1 = calcular_hash_conteudo(dados1)
    h2 = calcular_hash_conteudo(dados2)
    assert h1 == h2

    # Dados com valor diferente geram hash diferente
    dados3 = dict(dados1)
    dados3["valor"] = 26.0
    h3 = calcular_hash_conteudo(dados3)
    assert h1 != h3


def test_eh_erro_unique_violation_estrutura_pg8000():
    """Valida deteccao de erro 23505 tanto com dicionario nativo do pg8000 quanto com string."""
    import pg8000.dbapi

    from citizentech_cloud.banco import eh_erro_unique_violation

    # Formato real do pg8000 (dict em args[0])
    erro_dict = pg8000.dbapi.DatabaseError({
        "S": "ERROR",
        "V": "ERROR",
        "C": "23505",
        "M": 'duplicate key value violates unique constraint "ocorrencias_evento_id_key"',
    })
    assert eh_erro_unique_violation(erro_dict) is True

    # Formato string/fallback
    erro_str = pg8000.dbapi.DatabaseError("Erro 23505: chave duplicada")
    assert eh_erro_unique_violation(erro_str) is True

    # Outro erro SQL (ex: 42P01 table does not exist)
    erro_outro = pg8000.dbapi.DatabaseError({"C": "42P01", "M": "relation does not exist"})
    assert eh_erro_unique_violation(erro_outro) is False
