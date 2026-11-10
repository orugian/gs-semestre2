#!/usr/bin/env python3
"""
CitizenTech - Sprint 4
Simulador de dispositivo de campo (ESP32 ou drone) enviando leituras
para a Function URL da Lambda.

Nao precisa de hardware: o script faz o mesmo POST que o ESP32 faria.
Usa apenas a biblioteca padrao do Python.

Uso:
    export FUNCTION_URL="https://xxxx.lambda-url.us-east-1.on.aws"

    # 10 leituras normais de um sensor de nivel de rio
    python3 simulador_dispositivo.py

    # cenario de enchente: o valor sobe a cada leitura ate virar critico
    python3 simulador_dispositivo.py --cenario enchente --leituras 8

    # drone sobrevoando area de queimada, com relato de texto
    python3 simulador_dispositivo.py --tipo drone --cenario queimada

    # uma leitura unica, para o print da entrega
    python3 simulador_dispositivo.py --leituras 1
"""

import argparse
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

CENARIOS = {
    "normal": {
        "metrica": "nivel_rio_cm",
        "inicio": 80.0,
        "passo": 3.0,
        "ruido": 5.0,
        "relatos": [
            "Rio esta no nivel de sempre, tudo tranquilo por aqui",
            "Passei na ponte agora, sem novidade",
        ],
    },
    "enchente": {
        "metrica": "nivel_rio_cm",
        "inicio": 120.0,
        "passo": 36.0,
        "ruido": 8.0,
        "relatos": [
            "A agua subiu muito rapido, ja cobriu a calcada",
            "Moradores da rua de baixo estao tirando os moveis",
            "Nao da mais para passar de carro, esta alagado",
        ],
    },
    "queimada": {
        "metrica": "fumaca_ppm",
        "inicio": 180.0,
        "passo": 95.0,
        "ruido": 25.0,
        "relatos": [
            "Muita fumaca vindo do lado da plantacao",
            "O ar esta irrespiravel, criancas tossindo na escola",
        ],
    },
    "seca": {
        "metrica": "umidade_solo_pct",
        "inicio": 38.0,
        "passo": -6.0,
        "ruido": 2.0,
        "relatos": [
            "Plantacao comecando a murchar, nao chove ha semanas",
            "Terra totalmente rachada no talhao 3",
        ],
    },
}

# Pontos monitorados (regiao de Sao Jose dos Campos / Vale do Paraiba)
PONTOS = [
    ("esp32-ponte-sul-01", -23.1896, -45.8841),
    ("esp32-corrego-leste-02", -23.2237, -45.9009),
    ("drone-vale-01", -23.1791, -45.8872),
    ("esp32-sitio-norte-07", -23.1302, -45.9530),
]


def enviar(url, payload, tempo_limite=30):
    corpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url.rstrip("/") + "/ocorrencias",
        data=corpo,
        headers={"Content-Type": "application/json",
                 "User-Agent": "CitizenTech-Simulador/1.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=tempo_limite) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as erro:
        return erro.code, erro.read().decode("utf-8", "replace")
    except Exception as erro:
        return None, str(erro)


def main():
    p = argparse.ArgumentParser(description="Simulador de ESP32/drone - CitizenTech")
    p.add_argument("--url", default=os.environ.get("FUNCTION_URL"),
                   help="Function URL da Lambda (ou variavel FUNCTION_URL)")
    p.add_argument("--cenario", default="normal", choices=list(CENARIOS),
                   help="comportamento da serie de leituras")
    p.add_argument("--tipo", default="esp32", choices=["esp32", "drone", "app"],
                   help="tipo de dispositivo que aparece no log")
    p.add_argument("--leituras", type=int, default=10, help="quantas leituras enviar")
    p.add_argument("--intervalo", type=float, default=2.0,
                   help="segundos entre as leituras")
    p.add_argument("--sem-relato", action="store_true",
                   help="envia so telemetria, sem texto para a IA classificar")
    args = p.parse_args()

    if not args.url:
        print("Defina a Function URL: export FUNCTION_URL=https://....on.aws")
        sys.exit(1)

    cen = CENARIOS[args.cenario]
    candidatos = [pt for pt in PONTOS if pt[0].startswith(args.tipo)] or PONTOS
    dispositivo, lat, lon = random.choice(candidatos)
    valor = cen["inicio"]

    print(f"Dispositivo .....: {dispositivo} ({args.tipo})")
    print(f"Posicao .........: {lat}, {lon}")
    print(f"Cenario .........: {args.cenario} / metrica {cen['metrica']}")
    print(f"Destino .........: {args.url.rstrip('/')}/ocorrencias")
    print("-" * 72)

    for i in range(1, args.leituras + 1):
        leitura = round(max(0.0, valor + random.uniform(-cen["ruido"], cen["ruido"])), 1)
        payload = {
            "dispositivo_id": dispositivo,
            "tipo_dispositivo": args.tipo,
            "latitude": round(lat + random.uniform(-0.0015, 0.0015), 6),
            "longitude": round(lon + random.uniform(-0.0015, 0.0015), 6),
            "metrica": cen["metrica"],
            "valor": leitura,
            "medido_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        # O relato e o texto que o modelo de IA vai classificar.
        if not args.sem_relato and (i == 1 or i == args.leituras or random.random() < 0.4):
            payload["relato"] = random.choice(cen["relatos"])

        status, resposta = enviar(args.url, payload)
        print(f"[{i:02d}/{args.leituras}] POST {cen['metrica']}={leitura} -> HTTP {status}")
        if isinstance(resposta, dict):
            print(f"         id={resposta.get('id')} "
                  f"risco={resposta.get('nivel_risco')} "
                  f"sentimento={resposta.get('sentimento')} "
                  f"confianca={resposta.get('confianca')}"
                  + ("  << ALERTA" if resposta.get("alerta") else ""))
        else:
            print(f"         resposta: {resposta}")

        valor += cen["passo"]
        if i < args.leituras:
            time.sleep(args.intervalo)

    print("-" * 72)
    print("Fim do envio. Abra o CloudWatch Logs da funcao para ver as linhas")
    print("PAYLOAD RECEBIDO / DISPOSITIVO / CLASSIFICACAO / GRAVADO NO RDS.")


if __name__ == "__main__":
    main()
