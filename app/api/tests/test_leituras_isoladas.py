"""Testes da aplicacao em modo isolado CTP (sem Oracle e sem Mongo).

Valida que `citizentech.leituras.isolado:app` funciona de forma totalmente autocontida
apenas com FastAPI e CSV duravel, sem importar drivers externos de banco ou rede externa.
"""

import sys

from fastapi.testclient import TestClient

from citizentech.leituras.isolado import app as app_isolado


def test_modo_isolado_nao_importa_oracle_nem_mongo():
    import subprocess

    codigo = (
        "import sys\n"
        "from citizentech.leituras.isolado import app\n"
        "proibidos = ['oracledb', 'cx_Oracle', 'pymongo', 'motor']\n"
        "importados = [m for m in proibidos if m in sys.modules]\n"
        "if importados:\n"
        "    sys.stderr.write(f'Modulos proibidos importados: {importados}')\n"
        "    sys.exit(1)\n"
        "sys.stdout.write('LIMPO')\n"
        "sys.exit(0)\n"
    )
    resultado = subprocess.run(
        [sys.executable, "-c", codigo],
        capture_output=True,
        text=True,
        check=False,
    )
    assert resultado.returncode == 0, (
        f"Modo isolado importou modulos proibidos no processo limpo. "
        f"Stderr: {resultado.stderr} Stdout: {resultado.stdout}"
    )
    for modulo in ["oracledb", "cx_Oracle", "pymongo", "motor"]:
        assert modulo not in resultado.stderr
    assert resultado.stdout.strip() == "LIMPO"


def test_modo_isolado_executa_ciclo_completo_ctp(monkeypatch, tmp_path):
    caminho_csv = tmp_path / "runtime" / "leituras_isoladas.csv"
    monkeypatch.setenv("CITIZENTECH_LEITURAS_CSV", str(caminho_csv))
    monkeypatch.setenv("DEVICE_KEY", "chave-isolada-demo")

    cliente = TestClient(app_isolado)

    # 1. Rejeita sem chave
    resp_sem_chave = cliente.get("/leituras")
    assert resp_sem_chave.status_code == 401

    # 2. Rejeita payload invalido com 400
    resp_invalido = cliente.post(
        "/leituras",
        json={"dispositivo_id": "esp32-iso", "metrica": "temperatura_c", "valor": "invalido"},
        headers={"X-Device-Key": "chave-isolada-demo"},
    )
    assert resp_invalido.status_code == 400

    # 3. Posta leitura valida com chave
    payload = {
        "dispositivo_id": "esp32-iso",
        "metrica": "distancia_cm",
        "valor": 12.0,
        "sessao_laboratorio_id": "sessao-ctp",
    }
    resp_post = cliente.post(
        "/leituras",
        json=payload,
        headers={"X-Device-Key": "chave-isolada-demo"},
    )
    assert resp_post.status_code == 201
    corpo_post = resp_post.json()
    assert corpo_post["risco"] == "atencao"
    assert corpo_post["alerta"] is True
    assert corpo_post["estado"] == "pendente_nuvem"

    # 4. Consulta historico no modo isolado
    resp_get = cliente.get("/leituras", headers={"X-Device-Key": "chave-isolada-demo"})
    assert resp_get.status_code == 200
    dados_get = resp_get.json()
    assert dados_get["total"] == 1
    assert dados_get["itens"][0]["dispositivo_id"] == "esp32-iso"

    # 5. Consulta indicadores no modo isolado
    resp_ind = cliente.get(
        "/leituras/indicadores?metrica=distancia_cm",
        headers={"X-Device-Key": "chave-isolada-demo"},
    )
    assert resp_ind.status_code == 200
    dados_ind = resp_ind.json()
    assert dados_ind["contagem"] == 1
    assert dados_ind["total_alertas"] == 1
    assert dados_ind["media"] == 12.0
