"""Adaptadores de analise de sentimento para relatos cidadaos."""

import json
import logging
import os
import urllib.error
import urllib.request

logger = logging.getLogger("citizentech_cloud.sentimento")


def criar_cliente_comprehend():
    """Fabrica de cliente boto3 Comprehend com timeouts estritos."""
    import boto3
    from botocore.config import Config

    regiao = os.environ.get("AWS_REGION", "us-east-1")
    # Timeout curto: a falha da IA nunca pode estourar o timeout da Lambda (30 s).
    config = Config(connect_timeout=3, read_timeout=5, retries={"max_attempts": 1})
    return boto3.client("comprehend", region_name=regiao, config=config)


def analisar_relato(
    texto: str | None,
    provedor: str | None = None,
    cliente=None,
) -> dict:
    """Analisa o tom do relato por IA.

    Retorna sempre um dicionario com as chaves:
    - sentimento: str | None ('positive', 'negative', 'neutral', 'mixed')
    - confianca: float | None (arredondada a 4 casas decimais)
    - analise_status: str ('ok', 'sem_relato', 'desligado', 'indisponivel')
    - provedor: str
    """
    if provedor is None:
        provedor = os.environ.get("SENTIMENTO_PROVEDOR", "comprehend")

    if not texto or not texto.strip():
        return {
            "sentimento": None,
            "confianca": None,
            "analise_status": "sem_relato",
            "provedor": provedor,
        }

    texto_limpo = texto.strip()

    if provedor == "desligado":
        return {
            "sentimento": None,
            "confianca": None,
            "analise_status": "desligado",
            "provedor": "desligado",
        }

    if provedor == "comprehend":
        try:
            if cliente is None:
                cliente = criar_cliente_comprehend()

            # Comprehend limita a 5000 bytes UTF-8; usamos 4500 para margem de seguranca
            texto_truncado = texto_limpo.encode("utf-8")[:4500].decode("utf-8", errors="ignore")
            resp = cliente.detect_sentiment(Text=texto_truncado, LanguageCode="pt")

            rotulo = resp["Sentiment"].lower()
            chave_score = resp["Sentiment"].capitalize()
            score = float(resp["SentimentScore"][chave_score])
            confianca = round(score, 4)

            return {
                "sentimento": rotulo,
                "confianca": confianca,
                "analise_status": "ok",
                "provedor": "comprehend",
            }
        except Exception as e:
            logger.warning(
                "Falha na analise de sentimento via Comprehend: %s",
                type(e).__name__,
            )
            return {
                "sentimento": None,
                "confianca": None,
                "analise_status": "indisponivel",
                "provedor": "comprehend",
            }

    if provedor == "hf":
        try:
            url = os.environ.get("HF_API_URL", "https://router.huggingface.co/hf-inference/models")
            modelo = os.environ.get("HF_MODEL", "cardiffnlp/twitter-xlm-roberta-base-sentiment")
            endpoint = f"{url.rstrip('/')}/{modelo.strip('/')}" if modelo else url
            token = os.environ.get("HF_TOKEN", "")

            req_headers = {"Content-Type": "application/json"}
            if token:
                req_headers["Authorization"] = f"Bearer {token}"

            corpo = json.dumps({"inputs": texto_limpo}).encode("utf-8")
            req = urllib.request.Request(endpoint, data=corpo, headers=req_headers, method="POST")

            with urllib.request.urlopen(req, timeout=8) as response:
                dados = json.loads(response.read().decode("utf-8"))

            eh_lista_de_listas = isinstance(dados, list) and dados and isinstance(dados[0], list)
            itens = dados[0] if eh_lista_de_listas else dados
            if not isinstance(itens, list) or not itens:
                raise ValueError("Resposta inesperada da API Hugging Face")

            melhor = max(itens, key=lambda x: x.get("score", 0.0))
            rotulo = str(melhor["label"]).lower()
            confianca = round(float(melhor["score"]), 4)

            return {
                "sentimento": rotulo,
                "confianca": confianca,
                "analise_status": "ok",
                "provedor": "hf",
            }
        except Exception as e:
            logger.warning(
                "Falha na analise de sentimento via HF: %s",
                type(e).__name__,
            )
            return {
                "sentimento": None,
                "confianca": None,
                "analise_status": "indisponivel",
                "provedor": "hf",
            }

    logger.warning("Provedor de sentimento desconhecido: %s", provedor)
    return {
        "sentimento": None,
        "confianca": None,
        "analise_status": "indisponivel",
        "provedor": provedor,
    }
