"""GS 2026.2 - AICSS - Servidor Python que recebe o JSON do ESP32, exibe e grava em CSV.

Uso:  python servidor.py            (escuta em http://0.0.0.0:8000/leituras)
Só usa a biblioteca padrão. O JSON segue o contrato de 00_projeto/README.md.
"""
import csv
import json
import os
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.stdout.reconfigure(encoding="utf-8")  # acentos no terminal do Windows

PORTA = 8000
ARQUIVO_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leituras.csv")
CAMPOS = ["recebido_em", "dispositivo_id", "tipo_dispositivo", "latitude", "longitude",
          "metrica", "valor", "status", "medido_em"]
OBRIGATORIOS = ["dispositivo_id", "metrica", "valor"]


def gravar_csv(leitura):
    novo = not os.path.exists(ARQUIVO_CSV)
    with open(ARQUIVO_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS, extrasaction="ignore")
        if novo:
            w.writeheader()
        w.writerow(leitura)


class Handler(BaseHTTPRequestHandler):
    def _responder(self, codigo, corpo):
        dados = json.dumps(corpo, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def do_POST(self):
        if self.path != "/leituras":
            return self._responder(404, {"erro": "rota inexistente"})
        try:
            tamanho = int(self.headers.get("Content-Length", 0))
            leitura = json.loads(self.rfile.read(tamanho) or b"{}")
        except json.JSONDecodeError:
            return self._responder(400, {"erro": "JSON inválido"})
        faltando = [c for c in OBRIGATORIOS if leitura.get(c) is None]
        if faltando:
            print(f"[DESCARTADA] campos ausentes {faltando}: {leitura}")
            return self._responder(400, {"erro": "campos obrigatórios ausentes", "campos": faltando})

        leitura["recebido_em"] = datetime.now().isoformat(timespec="seconds")
        gravar_csv(leitura)
        print(f"[{leitura['recebido_em']}] {leitura['dispositivo_id']} "
              f"{leitura['metrica']}={leitura['valor']} status={leitura.get('status', '-')}")
        self._responder(201, {"ok": True, "leitura": leitura})

    def do_GET(self):
        if self.path != "/leituras":
            return self._responder(404, {"erro": "rota inexistente"})
        if not os.path.exists(ARQUIVO_CSV):
            return self._responder(200, [])
        with open(ARQUIVO_CSV, encoding="utf-8") as f:
            self._responder(200, list(csv.DictReader(f)))

    def log_message(self, *args):  # silencia o log padrão do http.server
        pass


if __name__ == "__main__":
    print(f"Servidor AICSS em http://0.0.0.0:{PORTA}/leituras  ->  {ARQUIVO_CSV}")
    HTTPServer(("0.0.0.0", PORTA), Handler).serve_forever()
