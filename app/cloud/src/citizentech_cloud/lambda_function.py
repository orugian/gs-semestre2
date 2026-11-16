"""Handler principal da funcao Lambda de ingestao de ocorrencias (Function URL)."""

import base64
import hmac
import json
import logging
import math
import os
import urllib.parse
from datetime import datetime

from citizentech_cloud import banco, risco, sentimento

logger = logging.getLogger("citizentech_cloud.lambda_function")


def _resposta(status: int, corpo: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(corpo, ensure_ascii=False),
    }


def lambda_handler(evento: dict, contexto=None) -> dict:
    """Handler da AWS Lambda Function URL."""
    # 1. Determina rota e metodo HTTP
    http_ctx = (evento.get("requestContext") or {}).get("http") or {}
    rota = evento.get("rawPath") or http_ctx.get("path") or evento.get("path") or ""
    metodo = (http_ctx.get("method") or evento.get("httpMethod") or "GET").upper()

    logger.info("REQUISICAO %s %s", metodo, rota)

    # Normalizacao de barra final (/ocorrencias/ == /ocorrencias, /health/ == /health)
    rota_normalizada = rota.rstrip("/") if rota != "/" else "/"

    # 2. Rota de Health Check
    if rota_normalizada == "/health":
        if metodo != "GET":
            return _resposta(
                405, {"erro": "Metodo nao permitido", "detalhes": "Apenas GET em /health"}
            )
        banco_status = "ok" if banco.testar_conexao() else "indisponivel"
        ia_provedor = os.environ.get("SENTIMENTO_PROVEDOR", "comprehend")
        return _resposta(200, {
            "status": "ok",
            "banco": banco_status,
            "ia_provedor": ia_provedor,
        })

    # 3. Rota de Ocorrencias
    if rota_normalizada == "/ocorrencias":
        if metodo == "GET":
            return _tratar_get_ocorrencias(evento)
        if metodo == "POST":
            return _tratar_post_ocorrencias(evento)
        return _resposta(405, {
            "erro": "Metodo nao permitido",
            "detalhes": "Apenas GET e POST em /ocorrencias",
        })

    return _resposta(404, {"erro": "Nao encontrado", "detalhes": f"Rota '{rota}' inexistente"})


def _tratar_get_ocorrencias(evento: dict) -> dict:
    """Processa GET /ocorrencias?limite=N."""
    params = evento.get("queryStringParameters") or {}
    limite_str = params.get("limite")

    if not limite_str and "rawQueryString" in evento:
        qs = urllib.parse.parse_qs(evento["rawQueryString"])
        limite_str = qs.get("limite", [None])[0]

    limite = 20
    if limite_str is not None:
        try:
            limite = int(limite_str)
            if limite < 1 or limite > 100:
                return _resposta(400, {
                    "erro": "Parametro invalido",
                    "detalhes": "limite deve ser um inteiro entre 1 e 100",
                })
        except (ValueError, TypeError):
            return _resposta(400, {
                "erro": "Parametro invalido",
                "detalhes": "limite deve ser um inteiro entre 1 e 100",
            })

    try:
        itens = banco.listar_ocorrencias(limite=limite)
        return _resposta(200, {"ocorrencias": itens})
    except Exception as e:
        logger.error("Erro ao listar ocorrencias: %s", type(e).__name__)
        return _resposta(503, {
            "erro": "Banco indisponivel",
            "detalhes": "Falha ao consultar ocorrencias no banco",
        })


def _tratar_post_ocorrencias(evento: dict) -> dict:
    """Processa POST /ocorrencias."""
    # Obter e decodificar corpo bruto
    corpo_bruto = evento.get("body")
    if evento.get("isBase64Encoded") and corpo_bruto:
        try:
            corpo_bruto = base64.b64decode(corpo_bruto).decode("utf-8")
        except Exception:
            logger.warning("LEITURA DESCARTADA - erro na decodificacao base64")
            return _resposta(
                400, {"erro": "Corpo invalido", "detalhes": "Falha ao decodificar base64"}
            )

    if corpo_bruto is None:
        corpo_str = ""
    elif isinstance(corpo_bruto, str):
        corpo_str = corpo_bruto
    else:
        corpo_str = json.dumps(corpo_bruto)

    logger.info("PAYLOAD RECEBIDO: %s", corpo_str[:2000])

    # Limite maximo de 8 KB
    if len(corpo_str.encode("utf-8")) > 8192:
        logger.warning("LEITURA DESCARTADA - payload excede 8 KB")
        return _resposta(400, {"erro": "Payload muito grande", "detalhes": "Corpo excede 8 KB"})

    # Parse JSON
    try:
        dados = json.loads(corpo_str)
    except Exception as e:
        logger.warning("LEITURA DESCARTADA - JSON malformado")
        return _resposta(400, {"erro": "JSON malformado", "detalhes": str(e)})

    if not isinstance(dados, dict):
        logger.warning("LEITURA DESCARTADA - corpo deve ser um objeto JSON")
        return _resposta(400, {"erro": "Corpo invalido", "detalhes": "Esperado objeto JSON"})

    # Validacao de campos obrigatorios
    for campo in ("dispositivo_id", "metrica", "valor"):
        if campo not in dados or dados[campo] is None:
            logger.warning("LEITURA DESCARTADA - campo obrigatorio ausente: %s", campo)
            return _resposta(400, {
                "erro": "Campo obrigatorio ausente",
                "detalhes": f"Campo '{campo}' e obrigatorio e nao pode ser nulo",
            })

    disp_id = dados["dispositivo_id"]
    if not isinstance(disp_id, str) or not (1 <= len(disp_id) <= 64):
        logger.warning("LEITURA DESCARTADA - dispositivo_id deve ter entre 1 e 64 caracteres")
        return _resposta(400, {
            "erro": "dispositivo_id invalido",
            "detalhes": "dispositivo_id deve ser string com 1 a 64 caracteres",
        })

    # Validacao de valor
    valor = dados["valor"]
    if isinstance(valor, bool):
        logger.warning("LEITURA DESCARTADA - valor nao pode ser booleano")
        return _resposta(400, {"erro": "Valor invalido", "detalhes": "valor nao pode ser booleano"})

    if not isinstance(valor, (int, float)):
        logger.warning("LEITURA DESCARTADA - valor deve ser numerico")
        return _resposta(400, {"erro": "Valor invalido", "detalhes": "valor deve ser int ou float"})

    try:
        valor_float = float(valor)
        if not math.isfinite(valor_float) or valor_float < -1e6 or valor_float > 1e6:
            logger.warning("LEITURA DESCARTADA - valor fora da faixa [-1e6, 1e6] ou nao-finito")
            return _resposta(400, {
                "erro": "Valor invalido",
                "detalhes": "valor deve estar entre -1e6 e 1e6 e ser finito",
            })
    except (ValueError, OverflowError):
        logger.warning("LEITURA DESCARTADA - valor numerico invalido")
        return _resposta(400, {"erro": "Valor invalido", "detalhes": "valor numerico invalido"})

    # Validacao de coordenadas
    lat = dados.get("latitude")
    if lat is not None:
        lat_invalida = (
            isinstance(lat, bool)
            or not isinstance(lat, (int, float))
            or not (-90.0 <= float(lat) <= 90.0)
        )
        if lat_invalida:
            logger.warning("LEITURA DESCARTADA - latitude fora de [-90, 90]")
            return _resposta(
                400,
                {"erro": "Latitude invalida", "detalhes": "latitude deve estar entre -90 e 90"},
            )
        lat = float(lat)

    lon = dados.get("longitude")
    if lon is not None:
        lon_invalida = (
            isinstance(lon, bool)
            or not isinstance(lon, (int, float))
            or not (-180.0 <= float(lon) <= 180.0)
        )
        if lon_invalida:
            logger.warning("LEITURA DESCARTADA - longitude fora de [-180, 180]")
            return _resposta(
                400,
                {"erro": "Longitude invalida", "detalhes": "longitude deve estar entre -180 e 180"},
            )
        lon = float(lon)

    # Validacao de relato
    relato = dados.get("relato")
    if relato is not None:
        if not isinstance(relato, str) or len(relato) > 280:
            logger.warning("LEITURA DESCARTADA - relato deve ser string de ate 280 caracteres")
            return _resposta(400, {
                "erro": "Relato invalido",
                "detalhes": "relato deve ser string com no maximo 280 caracteres",
            })

    # Validacao de evento_id
    evento_id = dados.get("evento_id")
    if evento_id is not None:
        if not isinstance(evento_id, str) or not (1 <= len(evento_id) <= 64):
            logger.warning("LEITURA DESCARTADA - evento_id deve ser string de 1 a 64 caracteres")
            return _resposta(400, {
                "erro": "evento_id invalido",
                "detalhes": "evento_id deve ser string com 1 a 64 caracteres",
            })

    # Campos textuais: tipo e tamanho (evita 201 com lixo e 503 por erro do banco)
    for campo, maximo, obrigatorio in (
        ("metrica", 64, True),
        ("tipo_dispositivo", 32, False),
        ("unidade", 16, False),
        ("sessao_laboratorio_id", 64, False),
        ("ciclo_id", 64, False),
    ):
        texto = dados.get(campo)
        if texto is None and not obrigatorio:
            continue
        if not isinstance(texto, str) or not (1 <= len(texto) <= maximo):
            logger.warning("LEITURA DESCARTADA - %s invalido", campo)
            return _resposta(400, {
                "erro": f"{campo} invalido",
                "detalhes": f"{campo} deve ser string com 1 a {maximo} caracteres",
            })

    medido_em = dados.get("medido_em")
    if medido_em is not None:
        try:
            if not isinstance(medido_em, str):
                raise ValueError
            instante = datetime.fromisoformat(medido_em.replace("Z", "+00:00"))
            if instante.tzinfo is None:
                raise ValueError
        except ValueError:
            logger.warning("LEITURA DESCARTADA - medido_em invalido")
            return _resposta(400, {
                "erro": "medido_em invalido",
                "detalhes": "medido_em deve ser data ISO-8601 com fuso horario",
            })

    # Autenticacao via header X-Device-Key (D09a)
    headers = {k.lower(): v for k, v in (evento.get("headers") or {}).items()}
    chave_enviada = headers.get("x-device-key")
    chave_esperada = os.environ.get("DEVICE_KEY")

    if chave_enviada is None:
        autenticado = False
        logger.info("DISPOSITIVO=%s nao autenticado", disp_id)
    else:
        if not chave_esperada or not hmac.compare_digest(chave_enviada, chave_esperada):
            logger.warning("CHAVE INVALIDA dispositivo=%s", disp_id)
            return _resposta(401, {
                "erro": "Nao autorizado",
                "detalhes": "Chave de dispositivo invalida",
            })
        autenticado = True

    # Classificacao de risco
    metrica = dados["metrica"]
    try:
        nivel_risco = risco.classificar_risco(metrica, valor_float)
    except risco.ValorInvalido as e:
        logger.warning("LEITURA DESCARTADA - %s", str(e))
        return _resposta(400, {"erro": "Valor invalido", "detalhes": str(e)})
    except (risco.MetricaDesconhecida, Exception):
        logger.warning("metrica sem limiar: %s", metrica)
        nivel_risco = "desconhecido"

    alerta = (nivel_risco == "critico")

    # Registro de divergencia se outbox enviou risco
    risco_enviado = dados.get("risco")
    if risco_enviado and risco_enviado != nivel_risco:
        logger.info(
            "Risco recebido ('%s') diverge do calculado localmente ('%s')",
            risco_enviado,
            nivel_risco,
        )

    tipo_disp = dados.get("tipo_dispositivo") or "desconhecido"
    logger.info(
        "DISPOSITIVO=%s TIPO=%s GPS=(%s, %s) %s=%s AUTENTICADO=%s",
        disp_id,
        tipo_disp,
        lat,
        lon,
        metrica,
        valor_float,
        "true" if autenticado else "false",
    )

    # Analise de sentimento do relato
    ia_res = sentimento.analisar_relato(relato)
    sentimento_rotulo = ia_res.get("sentimento")
    confianca = ia_res.get("confianca")
    analise_status = ia_res.get("analise_status")

    logger.info(
        "CLASSIFICACAO risco=%s sentimento=%s confianca=%s analise=%s",
        nivel_risco,
        sentimento_rotulo,
        confianca,
        analise_status,
    )

    if alerta:
        logger.warning(
            "ALERTA CIDADAO: dispositivo %s em nivel critico (%s=%s)",
            disp_id,
            metrica,
            valor_float,
        )

    # Persistencia no RDS PostgreSQL
    dados_banco = {
        "dispositivo_id": disp_id,
        "tipo_dispositivo": tipo_disp,
        "latitude": lat,
        "longitude": lon,
        "metrica": metrica,
        "valor": valor_float,
        "relato": relato,
        "sentimento": sentimento_rotulo,
        "confianca": confianca,
        "nivel_risco": nivel_risco,
        "medido_em": dados.get("medido_em"),
        "evento_id": evento_id,
        "autenticado": autenticado,
        "unidade": dados.get("unidade"),
        "sessao_laboratorio_id": dados.get("sessao_laboratorio_id"),
        "ciclo_id": dados.get("ciclo_id"),
        "alerta": alerta,
        "analise_status": analise_status,
    }

    try:
        resultado = banco.inserir_ocorrencia(dados_banco)
    except banco.LimiteExcedidoError:
        logger.warning("LIMITE EXCEDIDO dispositivo=%s", disp_id)
        return _resposta(429, {
            "erro": "Limite excedido",
            "detalhes": "Maximo de requisicoes por minuto excedido",
        })
    except banco.ConflitoEventoError:
        return _resposta(409, {
            "erro": "Conflito de evento",
            "detalhes": "evento_id ja registrado com conteudo diferente",
        })
    except banco.BancoIndisponivelError:
        return _resposta(503, {
            "erro": "Banco indisponivel",
            "detalhes": "Falha ao registrar ocorrencia no banco",
        })

    id_gravado = resultado["id"]
    logger.info("GRAVADO NO RDS id=%s", id_gravado)

    corpo_resposta = {
        "id": id_gravado,
        "evento_id": evento_id,
        "dispositivo_id": disp_id,
        "metrica": metrica,
        "valor": valor_float,
        "nivel_risco": nivel_risco,
        "alerta": alerta,
        "autenticado": autenticado,
        "sentimento": sentimento_rotulo,
        "confianca": confianca,
        "analise_status": analise_status,
    }

    if resultado.get("duplicata"):
        corpo_resposta["duplicata"] = True
        return _resposta(200, corpo_resposta)

    return _resposta(201, corpo_resposta)
