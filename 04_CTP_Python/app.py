"""GS 2026.2 - CTP - API REST (Flask) integrada ao dispositivo do AICSS.

Fluxo: ESP32 -> JSON -> POST /leituras -> validação/classificação -> CSV -> GET

Rotas:
  POST /leituras      recebe uma leitura (contrato JSON de 00_projeto/README.md)
  GET  /leituras      lista o histórico (filtros: ?dispositivo_id=  ?metrica=  ?classificacao=)
  GET  /indicadores   indicadores calculados sobre o histórico

Executar:  pip install -r requirements.txt  &&  python app.py
"""
from datetime import datetime

from flask import Flask, jsonify, request

import armazenamento
import processamento

app = Flask(__name__)
app.json.ensure_ascii = False


@app.post("/leituras")
def receber_leitura():
    dados = request.get_json(silent=True)
    erros = processamento.validar_leitura(dados)
    if erros:
        return jsonify({"erros": erros}), 400

    valor = float(dados["valor"])
    registro = {
        "data_hora": datetime.now().isoformat(timespec="seconds"),
        "dispositivo_id": dados["dispositivo_id"],
        "tipo_dispositivo": dados.get("tipo_dispositivo", ""),
        "latitude": dados.get("latitude", ""),
        "longitude": dados.get("longitude", ""),
        "metrica": dados["metrica"],
        "valor": valor,
        "status_dispositivo": dados.get("status", ""),
        "classificacao": processamento.classificar(dados["metrica"], valor),
    }
    armazenamento.salvar(registro)
    return jsonify(registro), 201


@app.get("/leituras")
def consultar_leituras():
    filtros = {k: v for k, v in request.args.items()
               if k in ("dispositivo_id", "metrica", "classificacao")}
    return jsonify(armazenamento.listar(filtros))


@app.get("/indicadores")
def indicadores():
    return jsonify(processamento.calcular_indicadores(armazenamento.listar()))


if __name__ == "__main__":
    # Porta 8000 = mesma URL que o firmware do AICSS usa.
    app.run(host="0.0.0.0", port=8000, debug=True)
