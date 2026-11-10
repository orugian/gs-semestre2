"""
CitizenTech - Sprint 4
API Serverless de ingestao de ocorrencias urbanas/rurais.

A mesma funcao Lambda da Sprint 3 passa a:
  1. receber dados enviados por dispositivos de campo (ESP32 / drone / app do cidadao);
  2. registrar no CloudWatch tudo o que chega (o "log das informacoes chegando");
  3. classificar o nivel de risco da leitura;
  4. classificar o relato em texto com um modelo de IA (Hugging Face, opcional);
  5. gravar o resultado no RDS PostgreSQL.

Rotas (Function URL):
  GET  /health       -> status da funcao e do banco
  POST /ocorrencias  -> recebe a leitura do dispositivo, classifica e grava
  GET  /ocorrencias  -> lista as ultimas ocorrencias gravadas
  GET  /locais       -> rota de consulta da Sprint 3 (mantida)

Variaveis de ambiente:
  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD   (RDS da Sprint 3)
  HF_TOKEN      token gratuito do tipo Read da Hugging Face (opcional)
  HF_MODEL      default: cardiffnlp/twitter-xlm-roberta-base-sentiment
  HF_API_URL    default: https://router.huggingface.co/hf-inference/models
"""

import json
import logging
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone

# Driver do PostgreSQL: o mesmo que ja foi empacotado na Sprint 3.
# pg8000 e Python puro (pip install pg8000 -t .) e nao exige compilacao.
# Se a sua Sprint 3 usa psycopg2, troque apenas esta linha por:
#   import psycopg2 as driver     e use dbname= no lugar de database=
import pg8000 as driver

logger = logging.getLogger()
logger.setLevel(logging.INFO)

HF_MODEL = os.environ.get("HF_MODEL", "cardiffnlp/twitter-xlm-roberta-base-sentiment")
HF_API_URL = os.environ.get("HF_API_URL", "https://router.huggingface.co/hf-inference/models")
HF_TOKEN = os.environ.get("HF_TOKEN")

# Limiares por metrica: valor acima de "critico" dispara alerta ao cidadao.
LIMIARES = {
    "nivel_rio_cm": {"atencao": 150.0, "critico": 250.0},
    "chuva_mm_h": {"atencao": 20.0, "critico": 50.0},
    "fumaca_ppm": {"atencao": 300.0, "critico": 600.0},
    "temperatura_c": {"atencao": 35.0, "critico": 40.0},
    "umidade_solo_pct": {"atencao": 20.0, "critico": 10.0},  # quanto MENOR, pior
}

INVERTIDAS = {"umidade_solo_pct"}


# ---------------------------------------------------------------- banco
def conectar():
    return driver.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", 5432)),
        database=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )


def gravar_ocorrencia(dados):
    sql = """
        INSERT INTO ocorrencias
            (dispositivo_id, tipo_dispositivo, latitude, longitude,
             metrica, valor, relato, sentimento, confianca, nivel_risco, medido_em)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, criado_em
    """
    conn = conectar()
    try:
        cur = conn.cursor()
        cur.execute(sql, (
            dados["dispositivo_id"], dados["tipo_dispositivo"],
            dados["latitude"], dados["longitude"],
            dados["metrica"], dados["valor"], dados["relato"],
            dados["sentimento"], dados["confianca"],
            dados["nivel_risco"], dados["medido_em"],
        ))
        novo_id, criado_em = cur.fetchone()
        conn.commit()
        return novo_id, criado_em
    finally:
        conn.close()


def listar_ocorrencias(limite=20):
    conn = conectar()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, dispositivo_id, tipo_dispositivo, metrica, valor,
                   nivel_risco, sentimento, confianca, relato, criado_em
              FROM ocorrencias
             ORDER BY id DESC
             LIMIT %s
        """, (limite,))
        colunas = ["id", "dispositivo_id", "tipo_dispositivo", "metrica", "valor",
                   "nivel_risco", "sentimento", "confianca", "relato", "criado_em"]
        return [dict(zip(colunas, linha)) for linha in cur.fetchall()]
    finally:
        conn.close()


# ------------------------------------------------------- classificacoes
def classificar_risco(metrica, valor):
    """Regra de limiar: nao depende de rede nem de token. Sempre executa."""
    faixa = LIMIARES.get(metrica)
    if faixa is None or valor is None:
        return "desconhecido"
    if metrica in INVERTIDAS:
        if valor <= faixa["critico"]:
            return "critico"
        if valor <= faixa["atencao"]:
            return "atencao"
        return "normal"
    if valor >= faixa["critico"]:
        return "critico"
    if valor >= faixa["atencao"]:
        return "atencao"
    return "normal"


def analisar_relato(texto):
    """
    Caminho A - Hugging Face.
    Manda o relato do cidadao para o modelo de sentimento e devolve
    (rotulo, confianca). Usa apenas urllib: nenhuma biblioteca nova no pacote.
    """
    if not texto or not HF_TOKEN:
        return None, None

    url = f"{HF_API_URL}/{HF_MODEL}"
    corpo = json.dumps({"inputs": texto}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=corpo,
        headers={
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            saida = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as erro:
        logger.warning("Hugging Face respondeu %s: %s", erro.code, erro.read()[:200])
        return None, None
    except Exception as erro:  # timeout, DNS, etc.
        logger.warning("Falha ao chamar a Hugging Face: %s", erro)
        return None, None

    # A resposta vem como [[{"label": "...", "score": 0.97}, ...]]
    lista = saida[0] if saida and isinstance(saida[0], list) else saida
    melhor = max(lista, key=lambda item: item["score"])
    return melhor["label"], round(float(melhor["score"]), 4)


# --------------------------------------------------------------- rotas
def rota_ingestao(evento):
    bruto = evento.get("body") or "{}"
    logger.info("PAYLOAD RECEBIDO: %s", bruto)

    try:
        payload = json.loads(bruto)
    except json.JSONDecodeError:
        return resposta(400, {"erro": "corpo nao e um JSON valido"})

    obrigatorios = ["dispositivo_id", "metrica", "valor"]
    faltando = [c for c in obrigatorios if payload.get(c) is None]
    if faltando:
        logger.warning("LEITURA DESCARTADA - campos ausentes: %s", faltando)
        return resposta(400, {"erro": "campos obrigatorios ausentes", "campos": faltando})

    dados = {
        "dispositivo_id": payload["dispositivo_id"],
        "tipo_dispositivo": payload.get("tipo_dispositivo", "desconhecido"),
        "latitude": payload.get("latitude"),
        "longitude": payload.get("longitude"),
        "metrica": payload["metrica"],
        "valor": float(payload["valor"]),
        "relato": payload.get("relato"),
        "medido_em": payload.get("medido_em") or datetime.now(timezone.utc).isoformat(),
    }

    logger.info(
        "DISPOSITIVO=%s TIPO=%s GPS=(%s, %s) %s=%s",
        dados["dispositivo_id"], dados["tipo_dispositivo"],
        dados["latitude"], dados["longitude"],
        dados["metrica"], dados["valor"],
    )

    dados["nivel_risco"] = classificar_risco(dados["metrica"], dados["valor"])
    dados["sentimento"], dados["confianca"] = analisar_relato(dados["relato"])

    logger.info(
        "CLASSIFICACAO risco=%s sentimento=%s confianca=%s",
        dados["nivel_risco"], dados["sentimento"], dados["confianca"],
    )
    if dados["nivel_risco"] == "critico":
        logger.warning(
            "ALERTA CIDADAO: %s em %s atingiu %s (%s)",
            dados["metrica"], dados["dispositivo_id"],
            dados["valor"], dados["nivel_risco"],
        )

    novo_id, criado_em = gravar_ocorrencia(dados)
    logger.info("GRAVADO NO RDS id=%s em %s", novo_id, criado_em)

    return resposta(201, {
        "id": novo_id,
        "dispositivo_id": dados["dispositivo_id"],
        "metrica": dados["metrica"],
        "valor": dados["valor"],
        "nivel_risco": dados["nivel_risco"],
        "sentimento": dados["sentimento"],
        "confianca": dados["confianca"],
        "alerta": dados["nivel_risco"] == "critico",
    })


def resposta(status, corpo):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(corpo, default=str, ensure_ascii=False),
    }


def lambda_handler(evento, contexto):
    metodo = (evento.get("requestContext", {})
                    .get("http", {})
                    .get("method", "GET")).upper()
    caminho = evento.get("rawPath", "/")

    logger.info("REQUISICAO %s %s", metodo, caminho)

    try:
        if caminho == "/health":
            return resposta(200, {"status": "ok", "modelo": HF_MODEL,
                                  "ia_ativa": bool(HF_TOKEN)})

        if caminho == "/ocorrencias" and metodo == "POST":
            return rota_ingestao(evento)

        if caminho == "/ocorrencias" and metodo == "GET":
            return resposta(200, {"ocorrencias": listar_ocorrencias()})

        return resposta(404, {"erro": "rota nao encontrada", "caminho": caminho})

    except Exception as erro:
        logger.exception("ERRO NAO TRATADO")
        return resposta(500, {"erro": str(erro)})
