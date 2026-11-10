"""GS 2026.2 - CTP - Persistência do histórico de leituras em CSV."""
import csv
import os

ARQUIVO_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historico.csv")
CAMPOS = ["data_hora", "dispositivo_id", "tipo_dispositivo", "latitude", "longitude",
          "metrica", "valor", "status_dispositivo", "classificacao"]


def salvar(registro):
    novo = not os.path.exists(ARQUIVO_CSV)
    with open(ARQUIVO_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS, extrasaction="ignore")
        if novo:
            w.writeheader()
        w.writerow(registro)


def listar(filtros=None):
    """Lê o CSV e aplica filtros simples por igualdade (ex.: {"metrica": "x"})."""
    if not os.path.exists(ARQUIVO_CSV):
        return []
    with open(ARQUIVO_CSV, encoding="utf-8") as f:
        registros = list(csv.DictReader(f))
    for campo, valor in (filtros or {}).items():
        registros = [r for r in registros if r.get(campo) == valor]
    return registros
