"""Evidência de AICSS no host: lógica do firmware -> JSON -> API Python -> CSV.

Compila `aicss/demo_cenarios.cpp` com a mesma `logica.h` e `limiares.h` do firmware
(`app/iot/firmware/`), roda os três cenários de `app/config/limiares.json`, casos de fronteira e
falhas de sensor, confere a decisão dos atuadores contra `limiares.json`, envia ao `POST /leituras`
exatamente o JSON que o `sketch.ino` montaria e lê de volta o histórico gravado em CSV.

Não substitui a execução no Wokwi: aqui não há ESP32, Wi-Fi, LED nem buzzer reais; o que roda é o
código C++ de decisão e de montagem do JSON. A chave do dispositivo vem de DEVICE_KEY e nunca é
impressa.

Uso (a partir de app/tools, com a API de leituras de pé):
    uv run python demo_firmware_aicss.py --base http://127.0.0.1:8001 [--csv <arquivo do CSV>]
Saída 0 se todas as conferências baterem.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path

from demo_leituras_ctp import requisitar

RAIZ_APP = Path(__file__).resolve().parents[1]
FIRMWARE = RAIZ_APP / "iot" / "firmware"
HARNESS = Path(__file__).resolve().parent / "aicss" / "demo_cenarios.cpp"
LIMIARES = RAIZ_APP / "config" / "limiares.json"

# (rótulo, temperatura °C, distância cm ou "sem_eco", classe de pior caso esperada ou "falha")
CASOS_EXTRAS = [
    ("fronteira 34,9 °C / 15,1 cm", "34.9", "15.1", "normal"),
    ("fronteira 35,0 °C / 15,0 cm", "35.0", "15.0", "atencao"),
    ("fronteira 45,0 °C / 8,0 cm", "45.0", "8.0", "critico"),
    ("misto: temperatura normal, distância crítica", "25.0", "6.0", "critico"),
    ("DS18B20 desconectado (-127 °C), distância normal", "-127", "25.0", "normal"),
    ("HC-SR04 sem eco, temperatura em atenção", "38.0", "sem_eco", "atencao"),
    ("os dois sensores em falha", "-127", "sem_eco", "falha"),
]


def compilar(destino: Path) -> Path:
    gpp = shutil.which("g++")
    if not gpp:
        raise SystemExit("g++ não encontrado no PATH")
    binario = destino / ("demo_cenarios.exe" if os.name == "nt" else "demo_cenarios")
    cmd = [gpp, "-std=c++17", "-Wall", "-Wextra", "-Werror", f"-I{FIRMWARE}", str(HARNESS), "-o",
           str(binario)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise SystemExit(f"falha ao compilar:\n{res.stderr}")
    return binario


def rodar(binario: Path, ciclo: str, temp: str, dist: str, sessao: str) -> dict:
    res = subprocess.run([str(binario), ciclo, temp, dist, sessao], capture_output=True, text=True,
                         check=True)
    return json.loads(res.stdout)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", default="http://127.0.0.1:8001")
    ap.add_argument("--csv", help="arquivo CSV da API, para imprimir as linhas desta sessão")
    args = ap.parse_args(argv)
    base = args.base.rstrip("/")
    chave = os.environ.get("DEVICE_KEY")
    if not chave:
        print("DEVICE_KEY ausente no ambiente", file=sys.stderr)
        return 2

    limiares = json.loads(LIMIARES.read_text(encoding="utf-8"))
    atuadores_esperados = limiares["atuadores"]
    casos = [(f"cenário {c['nome']}", str(c["temperatura_c"]), str(c["distancia_cm"]),
              c["classe_esperada"]) for c in limiares["cenarios_demonstracao"]] + CASOS_EXTRAS

    agora = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    sessao = f"demo-aicss-{uuid.uuid4().hex[:8]}"
    semente = secrets.token_hex(4)
    print(f"=== Evidência AICSS (lógica do firmware no host) — {agora} — API {base} ===")
    texto_header = (FIRMWARE / "limiares.h").read_text(encoding="utf-8")
    sha_header = texto_header.split("SHA-256 de origem: ")[1]
    print(f"firmware: {FIRMWARE.relative_to(RAIZ_APP.parent)} · limiares SHA-256 no header: "
          f"{sha_header[:12]}…")
    print(f"sessão: {sessao}")

    falhas = 0
    enviados: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        binario = compilar(Path(tmp))
        print("compilação g++ -std=c++17 -Wall -Wextra -Werror: OK")
        for n, (rotulo, temp, dist, esperado) in enumerate(casos, start=1):
            ciclo = f"c-{semente}-{n}"
            saida = rodar(binario, ciclo, temp, dist, sessao)
            if esperado == "falha":
                esperado_at = {"led": False, "buzzer": False, "piscar_falha": True}
            else:
                esperado_at = dict(atuadores_esperados[esperado], piscar_falha=False)
            obtido_at = {k: saida[k] for k in ("led", "buzzer", "piscar_falha")}
            ok_at = obtido_at == esperado_at
            falhas += 0 if ok_at else 1
            print(f"\n[{n}] {rotulo}: temperatura={temp} dist={dist}")
            print(f"  firmware : temperatura {saida['classe_temperatura']}"
                  f" ({saida['status_temperatura']})"
                  f" · distância {saida['classe_distancia']} ({saida['status_distancia']})")
            conferencia = "OK" if ok_at else "FALHOU " + str(esperado_at)
            print(f"  atuadores: LED={'aceso' if saida['led'] else 'apagado'}"
                  f" · buzzer={'ligado' if saida['buzzer'] else 'desligado'}"
                  f" · piscar_falha={'sim' if saida['piscar_falha'] else 'não'}"
                  f"  (esperado pelo limiares.json: {conferencia})")
            for campo, classe in (("json_temperatura", saida["classe_temperatura"]),
                                  ("json_distancia", saida["classe_distancia"])):
                payload = saida[campo]
                if payload is None:
                    print(f"  {campo}: não enviado (leitura com ERRO, como no sketch.ino)")
                    continue
                print(f"  JSON enviado : {json.dumps(payload, ensure_ascii=False)}")
                s, r = requisitar(base, "POST", "/leituras", payload, chave)
                ok = s == 201 and isinstance(r, dict) and r.get("risco") == classe
                falhas += 0 if ok else 1
                enviados.append(payload["evento_id"])
                print(f"  API          : HTTP {s} {json.dumps(r, ensure_ascii=False)}"
                      f"  ({'risco igual ao do firmware' if ok else 'DIVERGENTE'})")

    s, r = requisitar(base, "GET", f"/leituras?sessao={sessao}&page_size=50", chave=chave)
    itens = r.get("itens", []) if isinstance(r, dict) else []
    ok_get = s == 200 and sorted(i["evento_id"] for i in itens) == sorted(enviados)
    falhas += 0 if ok_get else 1
    print(f"\n[GET /leituras?sessao={sessao}] HTTP {s} · {len(itens)} leituras no histórico,"
          f" {len(enviados)} enviadas ({'OK' if ok_get else 'FALHOU'})")
    for i in itens:
        print(f"  {i['evento_id']}: {i['metrica']}={i['valor']}"
              f" risco={i['risco']} alerta={i['alerta']}")

    if args.csv:
        linhas = Path(args.csv).read_text(encoding="utf-8").splitlines()
        da_sessao = [linha for linha in linhas if sessao in linha]
        print(f"\n[CSV {Path(args.csv).name}] cabeçalho + {len(da_sessao)} linhas desta sessão:")
        print(f"  {linhas[0]}")
        for linha in da_sessao:
            print(f"  {linha}")

    print(f"\n=== sessão {sessao} · falhas={falhas} ===")
    return 0 if falhas == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
