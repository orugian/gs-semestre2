"""Aceite independente S2, fixtures sinteticas e armazenamento temporario."""
import pytest
from fastapi.testclient import TestClient

from citizentech.main import app


@pytest.fixture
def contexto(monkeypatch, tmp_path):
    caminho = tmp_path / "leituras.csv"
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(caminho))
    monkeypatch.setenv("DEVICE_KEY", "fixture-local")
    cliente = TestClient(app, raise_server_exceptions=False)
    return cliente, caminho, {"X-Device-Key": "fixture-local"}

def test_csv_corrompido_nao_confirma_novo_registro(contexto):
    client, path, headers = contexto
    path.write_text("cabecalho_invalido\n", encoding="utf-8")
    r = client.post("/leituras", headers=headers,
                    json={"dispositivo_id": "aceite", "metrica": "temperatura_c", "valor": 38})
    assert r.status_code == 503

@pytest.mark.parametrize("campo", ["valor", "metrica", "unidade", "medido_em"])
def test_entrada_invalida_nao_reflete_dado_privado(contexto, campo):
    client, _, headers = contexto
    payload = {"dispositivo_id": "aceite", "metrica": "temperatura_c", "valor": 38}
    payload[campo] = "pessoa-privada@example.test"
    r = client.post("/leituras", headers=headers, json=payload)
    assert r.status_code == 400
    assert "pessoa-privada" not in r.text

def test_bearer_nao_substitui_header_de_dispositivo(contexto):
    client, _, _ = contexto
    r = client.get("/leituras", headers={"Authorization": "Bearer fixture-local"})
    assert r.status_code == 401


@pytest.mark.parametrize("extra", [
    {"tipo_dispositivo": ""}, {"status": "inventado"},
    {"medido_em": "9999-12-31T23:59:59-03:00"},
    {"medido_em": "0001-01-01T00:00:00+03:00"},
])
def test_envelope_invalido_nao_corrompe_historico(contexto, extra):
    client, _, headers = contexto
    payload = {"dispositivo_id": "extra", "metrica": "temperatura_c", "valor": 38}
    r = client.post("/leituras", headers=headers, json=payload | extra)
    assert r.status_code == 400
    assert client.get("/leituras", headers=headers).json()["total"] == 0


def test_so_sentinela_exata_representa_falha_sensor(contexto):
    client, _, headers = contexto
    payload = {"dispositivo_id": "sentinela", "metrica": "temperatura_c", "valor": -126.999999}
    assert client.post("/leituras", headers=headers, json=payload).status_code == 201
    assert client.get("/leituras", headers=headers).status_code == 200
