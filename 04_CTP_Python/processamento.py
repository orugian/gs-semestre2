"""GS 2026.2 - CTP - Regras de negócio: validação, classificação e indicadores.

Módulo sem Flask, para poder ser testado e reaproveitado por outras disciplinas.
"""

# TODO: trocar pelas métricas e limiares da ideia (iguais aos do AICSS e do Cloud).
# invertido=True -> quanto MENOR o valor, pior (ex.: umidade do solo).
LIMIARES = {
    "TODO_metrica_1": {"atencao": 50.0, "critico": 70.0, "invertido": False},
    "TODO_metrica_2": {"atencao": 40.0, "critico": 30.0, "invertido": True},
}

CAMPOS_OBRIGATORIOS = ("dispositivo_id", "metrica", "valor")
NIVEIS = ("normal", "atencao", "critico")


def validar_leitura(dados):
    """Retorna a lista de erros encontrados (lista vazia = leitura válida)."""
    if not isinstance(dados, dict):
        return ["o corpo deve ser um objeto JSON"]
    erros = [f"campo obrigatório ausente: {c}" for c in CAMPOS_OBRIGATORIOS
             if dados.get(c) in (None, "")]
    if dados.get("valor") is not None:
        try:
            float(dados["valor"])
        except (TypeError, ValueError):
            erros.append("valor deve ser numérico")
    if dados.get("metrica") and dados["metrica"] not in LIMIARES:
        erros.append(f"métrica desconhecida: {dados['metrica']} (use: {', '.join(LIMIARES)})")
    return erros


def classificar(metrica, valor):
    """Compara o valor com os limiares da métrica: normal | atencao | critico."""
    faixa = LIMIARES[metrica]
    if faixa["invertido"]:
        if valor <= faixa["critico"]:
            return "critico"
        return "atencao" if valor <= faixa["atencao"] else "normal"
    if valor >= faixa["critico"]:
        return "critico"
    return "atencao" if valor >= faixa["atencao"] else "normal"


def calcular_indicadores(registros):
    """Indicadores sobre o histórico: total, alertas e média/máximo/mínimo por métrica."""
    por_metrica = {}
    for r in registros:
        por_metrica.setdefault(r["metrica"], []).append(float(r["valor"]))
    return {
        "total_leituras": len(registros),
        "total_alertas": sum(1 for r in registros if r["classificacao"] == "critico"),
        "por_classificacao": {n: sum(1 for r in registros if r["classificacao"] == n) for n in NIVEIS},
        "por_metrica": {
            m: {"quantidade": len(v), "media": round(sum(v) / len(v), 2),
                "maximo": max(v), "minimo": min(v)}
            for m, v in por_metrica.items()
        },
    }
