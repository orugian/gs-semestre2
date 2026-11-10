"""Teste local da Lambda sem AWS: finge o driver do Postgres e a Hugging Face.
Serve para gerar o exemplo de log identico ao que aparece no CloudWatch.
"""
import json, logging, os, sys, types

# --- driver falso do Postgres ------------------------------------------
class _Cursor:
    _seq = 100
    def execute(self, sql, params=None):
        self._sql, self._params = sql, params
    def fetchone(self):
        _Cursor._seq += 1
        return (_Cursor._seq, "2026-11-05 19:58:12.441+00")
    def fetchall(self):
        return []

class _Conn:
    def cursor(self): return _Cursor()
    def commit(self): pass
    def close(self): pass

fake = types.ModuleType("pg8000")
fake.connect = lambda **kw: _Conn()
sys.modules["pg8000"] = fake

os.environ.update(DB_HOST="rds.local", DB_NAME="citizentech",
                  DB_USER="postgres", DB_PASSWORD="x", HF_TOKEN="hf_fake")

logging.basicConfig(level=logging.INFO,
                    format="%(levelname)s\t%(message)s", stream=sys.stdout)

import lambda_function as fn

# --- Hugging Face falsa (resposta real do modelo de sentimento) -------
def analisar_fake(texto):
    if not texto:
        return None, None
    negativas = ("subiu", "alagado", "fumaca", "irrespiravel", "murchar", "rachada", "tossindo")
    if any(p in texto.lower() for p in negativas):
        return "negative", 0.9471
    return "neutral", 0.8123
fn.analisar_relato = analisar_fake

def evento(metodo, caminho, corpo=None):
    return {"rawPath": caminho,
            "requestContext": {"http": {"method": metodo}},
            "body": json.dumps(corpo, ensure_ascii=False) if corpo else None}

casos = [
    ("GET", "/health", None),
    ("POST", "/ocorrencias", {
        "dispositivo_id": "esp32-ponte-sul-01", "tipo_dispositivo": "esp32",
        "latitude": -23.189612, "longitude": -45.884073,
        "metrica": "nivel_rio_cm", "valor": 118.4,
        "medido_em": "2026-11-05T19:58:10+00:00"}),
    ("POST", "/ocorrencias", {
        "dispositivo_id": "esp32-ponte-sul-01", "tipo_dispositivo": "esp32",
        "latitude": -23.189588, "longitude": -45.884120,
        "metrica": "nivel_rio_cm", "valor": 268.9,
        "relato": "A agua subiu muito rapido, ja cobriu a calcada",
        "medido_em": "2026-11-05T20:04:10+00:00"}),
    ("POST", "/ocorrencias", {
        "dispositivo_id": "drone-vale-01", "tipo_dispositivo": "drone",
        "metrica": "fumaca_ppm", "valor": 640.0,
        "relato": "O ar esta irrespiravel, criancas tossindo na escola"}),
    ("POST", "/ocorrencias", {"dispositivo_id": "esp32-sitio-norte-07"}),
]

for metodo, caminho, corpo in casos:
    print(f"\n===== {metodo} {caminho} =====")
    r = fn.lambda_handler(evento(metodo, caminho, corpo), None)
    print(f"RESPOSTA {r['statusCode']} {r['body']}")
