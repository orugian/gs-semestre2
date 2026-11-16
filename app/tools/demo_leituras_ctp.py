"""Demonstração executável do fluxo CTP: JSON do dispositivo -> POST /leituras -> CSV -> GET.

Envia os três cenários de `app/config/limiares.json` (normal, atenção, crítico) para a API de
leituras, mais casos de erro e de reenvio, e consulta o histórico e os indicadores. A chave do
dispositivo vem da variável de ambiente DEVICE_KEY e nunca é impressa.

Uso (a partir de app/tools, com a API de pé):
    uv run python demo_leituras_ctp.py --base http://127.0.0.1:8001
Saída 0 se todos os status baterem com o esperado.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from datetime import UTC, datetime
from pathlib import Path

LIMIARES = Path(__file__).resolve().parents[1] / "config" / "limiares.json"


def requisitar(base: str, metodo: str, caminho: str, corpo=None, chave: str | None = None):
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    cab = {"Content-Type": "application/json"} if dados is not None else {}
    if chave:
        cab["X-Device-Key"] = chave
    req = urllib.request.Request(base + caminho, data=dados, headers=cab, method=metodo)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode("utf-8") or "null")
    except urllib.error.HTTPError as e:
        texto = e.read().decode("utf-8")
        try:
            return e.code, json.loads(texto)
        except json.JSONDecodeError:
            return e.code, texto


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", default="http://127.0.0.1:8001")
    base = ap.parse_args(argv).base.rstrip("/")
    chave = os.environ.get("DEVICE_KEY")
    if not chave:
        print("DEVICE_KEY ausente no ambiente", file=sys.stderr)
        return 2

    cenarios = json.loads(LIMIARES.read_text(encoding="utf-8"))["cenarios_demonstracao"]
    falhas = 0

    def mostrar(rotulo: str, enviado, status: int, esperado: int, resposta) -> None:
        nonlocal falhas
        ok = status == esperado
        falhas += 0 if ok else 1
        print(f"\n[{rotulo}] HTTP {status} (esperado {esperado}) {'OK' if ok else 'FALHOU'}")
        if enviado is not None:
            print(f"  enviado : {json.dumps(enviado, ensure_ascii=False)}")
        print(f"  resposta: {json.dumps(resposta, ensure_ascii=False)}")

    agora = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"=== Demonstração CTP — {agora} — API {base} ===")
    sessao = f"demo-ctp-{uuid.uuid4().hex[:8]}"
    primeiro = None
    for cen in cenarios:
        for metrica, unidade in (("temperatura_c", "C"), ("distancia_cm", "cm")):
            payload = {
                "evento_id": str(uuid.uuid4()),
                "dispositivo_id": "esp32-bancada-01",
                "tipo_dispositivo": "esp32",
                "sessao_laboratorio_id": sessao,
                "metrica": metrica,
                "valor": cen[metrica],
                "unidade": unidade,
                "status": "OK" if cen["nome"] == "normal" else "ALERTA",
                "medido_em": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            primeiro = primeiro or payload
            s, r = requisitar(base, "POST", "/leituras", payload, chave)
            esperado_risco = cen["classe_esperada"]
            mostrar(f"cenário {cen['nome']} · {metrica}", payload, s, 201, r)
            if isinstance(r, dict) and r.get("risco") != esperado_risco:
                falhas += 1
                print(f"  RISCO DIVERGENTE: esperado {esperado_risco}")

    s, r = requisitar(base, "POST", "/leituras", primeiro, chave)
    mostrar("reenvio idêntico (mesmo evento_id)", None, s, 200, r)
    alterado = dict(primeiro, valor=99.0)
    s, r = requisitar(base, "POST", "/leituras", alterado, chave)
    mostrar("mesmo evento_id com valor diferente", None, s, 409, r)
    invalido = {"dispositivo_id": "esp32-bancada-01", "metrica": "temperatura_c"}
    s, r = requisitar(base, "POST", "/leituras", invalido, chave)
    mostrar("leitura sem 'valor'", invalido, s, 400, r)
    falha_sensor = {"dispositivo_id": "esp32-bancada-01", "metrica": "temperatura_c", "valor": -127}
    s, r = requisitar(base, "POST", "/leituras", falha_sensor, chave)
    mostrar("DS18B20 desconectado (-127 °C)", falha_sensor, s, 400, r)
    s, r = requisitar(base, "POST", "/leituras", primeiro)
    mostrar("sem X-Device-Key", None, s, 401, r)

    s, r = requisitar(base, "GET", f"/leituras?sessao={sessao}&page_size=20", chave=chave)
    resumo = {
        "total": r.get("total") if isinstance(r, dict) else None,
        "itens": [
            {k: i[k] for k in ("metrica", "valor", "risco", "alerta", "estado")}
            for i in (r.get("itens", []) if isinstance(r, dict) else [])
        ],
    }
    mostrar("GET /leituras da sessão (histórico do CSV)", None, s, 200, resumo)
    s, r = requisitar(base, "GET", f"/leituras/indicadores?sessao={sessao}", chave=chave)
    mostrar("GET /leituras/indicadores da sessão", None, s, 200, r)
    s, r = requisitar(base, "GET", f"/leituras/indicadores?sessao={sessao}&metrica=temperatura_c",
                      chave=chave)
    mostrar("GET /leituras/indicadores?metrica=temperatura_c", None, s, 200, r)

    print(f"\n=== sessão {sessao} · falhas={falhas} ===")
    return 0 if falhas == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
