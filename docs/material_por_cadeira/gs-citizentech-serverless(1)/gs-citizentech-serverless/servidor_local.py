"""Sobe a Lambda num servidor HTTP local para testar o simulador de ponta a ponta."""
import json, logging, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
import teste_local as t   # reaproveita os stubs de banco e IA
fn = t.fn

class H(BaseHTTPRequestHandler):
    def _run(self, metodo):
        n = int(self.headers.get("Content-Length") or 0)
        corpo = self.rfile.read(n).decode() if n else None
        ev = {"rawPath": self.path, "requestContext": {"http": {"method": metodo}}, "body": corpo}
        r = fn.lambda_handler(ev, None)
        b = r["body"].encode()
        self.send_response(r["statusCode"])
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)
    def do_POST(self): self._run("POST")
    def do_GET(self): self._run("GET")
    def log_message(self, *a): pass

HTTPServer(("127.0.0.1", 8099), H).serve_forever()
