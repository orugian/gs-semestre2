"""S0: a API responde ao health check e carrega a fonte unica de limiares."""

from fastapi.testclient import TestClient

from citizentech.main import app


def test_health_responde_ok_com_limiares_carregados():
    resposta = TestClient(app).get("/health")

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "ok"
    assert corpo["limiares"]["schema_version"] == "1.0"
    assert corpo["limiares"]["metricas"] == ["distancia_cm", "temperatura_c"]
