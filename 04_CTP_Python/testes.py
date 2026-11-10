"""GS 2026.2 - CTP - Três cenários de teste com requisição, resposta e registro.

Com a API rodando (python app.py), em outro terminal:  python testes.py
Usa só a biblioteca padrão. URL configurável: API_URL=http://... python testes.py
"""
import json
import os
import sys
import urllib.error
import urllib.request

from processamento import LIMIARES

sys.stdout.reconfigure(encoding="utf-8")  # acentos no terminal do Windows

API = os.environ.get("API_URL", "http://127.0.0.1:8000")


def chamar(metodo, rota, corpo=None):
    dados = json.dumps(corpo).encode() if corpo is not None else None
    req = urllib.request.Request(API + rota, data=dados, method=metodo,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def cenario(titulo, corpo, status_esperado):
    print(f"\n=== {titulo}")
    print("Requisição:", json.dumps(corpo, ensure_ascii=False))
    status, resposta = chamar("POST", "/leituras", corpo)
    print(f"Resposta HTTP {status}:", json.dumps(resposta, ensure_ascii=False))
    print("OK" if status == status_esperado else f"FALHOU (esperado {status_esperado})")


if __name__ == "__main__":
    metrica, faixa = next(iter(LIMIARES.items()))
    a, c = faixa["atencao"], faixa["critico"]
    normal = a + 10 if faixa["invertido"] else a - 10
    critico = c - 5 if faixa["invertido"] else c + 5
    base = {"dispositivo_id": "teste-01", "tipo_dispositivo": "esp32", "metrica": metrica}

    cenario("Cenário 1 - leitura normal", {**base, "valor": normal}, 201)
    cenario("Cenário 2 - leitura crítica (alerta)", {**base, "valor": critico}, 201)
    cenario("Cenário 3 - leitura inválida (sem 'valor')", base, 400)

    print("\n=== Histórico gravado (GET /leituras?dispositivo_id=teste-01)")
    print(json.dumps(chamar("GET", "/leituras?dispositivo_id=teste-01")[1], indent=2, ensure_ascii=False))
    print("\n=== Indicadores (GET /indicadores)")
    print(json.dumps(chamar("GET", "/indicadores")[1], indent=2, ensure_ascii=False))
