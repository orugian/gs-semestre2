"""Testes para o servidor local que emula a AWS Lambda Function URL."""

import json
import threading
import urllib.request

import pytest

from citizentech_cloud.servidor_local import criar_servidor


@pytest.fixture
def servidor_emulador():
    servidor = criar_servidor(porta=0, host="127.0.0.1")
    porta = servidor.server_address[1]
    thread = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{porta}"
    yield base_url
    servidor.shutdown()
    servidor.server_close()


@pytest.mark.postgres
def test_servidor_local_responde_health(servidor_emulador):
    url = f"{servidor_emulador}/health"
    with urllib.request.urlopen(url, timeout=5) as resp:
        assert resp.status == 200
        dados = json.loads(resp.read().decode("utf-8"))
        assert dados["status"] == "ok"
        assert dados["banco"] in ("ok", "indisponivel")


@pytest.mark.postgres
def test_servidor_local_responde_post_ocorrencias(servidor_emulador):
    url = f"{servidor_emulador}/ocorrencias"
    payload = {
        "dispositivo_id": "teste-servidor-local",
        "metrica": "temperatura_c",
        "valor": 25.0,
    }
    corpo = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=corpo,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        assert resp.status == 201
        dados = json.loads(resp.read().decode("utf-8"))
        assert dados["id"] is not None
        assert dados["dispositivo_id"] == "teste-servidor-local"
