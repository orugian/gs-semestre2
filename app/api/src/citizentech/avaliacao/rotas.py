"""Rotas de avaliacao e exercicio diagnostico (S13)."""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from citizentech.auth.dependencias import exigir_csrf, obter_usuario_logado
from citizentech.avaliacao.catalogo import (
    carregar_dados_destino,
    formatar_exercicio_publico,
    obter_requisitos_avaliados_destino,
)
from citizentech.avaliacao.correcao import (
    calcular_nota_aberta_llm,
    calcular_nota_final,
    corrigir_questoes_objetivas,
    determinar_resultado,
)
from citizentech.avaliacao.esquemas import (
    CriarTentativaRequisicao,
    DiscordoResposta,
    ListarTentativasResposta,
    RegistrarDiscordoRequisicao,
    TentativaResposta,
)
from citizentech.avaliacao.llm_rubrica import (
    construir_mensagens_avaliacao,
    gerar_schema_rubrica,
    sanitizar_delimitadores,
    validar_saida_rubrica,
)
from citizentech.avaliacao.repositorio import (
    buscar_avaliacao_cache_mongo,
    contar_tentativas_24h,
    listar_tentativas_usuario,
    registrar_discordo_oracle,
    salvar_avaliacao_cache_mongo,
    salvar_resposta_aberta_mongo,
    salvar_tentativa_oracle,
)
from citizentech.consentimentos.repositorio import listar_consentimentos
from citizentech.curriculo.redacao import redigir_pii
from citizentech.llm.cliente import ClienteLLM, ErroLLM, obter_cliente_llm

logger = logging.getLogger("citizentech.avaliacao")

router = APIRouter(tags=["avaliacao"])

AVISO_DIAGNOSTICO = (
    "Resultado diagnóstico de nível básico. "
    "Você pode refazer (até 3 vezes em 24 horas) ou registrar que discorda."
)


def _verificar_consentimento_curriculo_llm(usuario_id: str) -> None:
    """Valida consentimento ativo curriculo_llm exigido antes de enviar texto a LLM (D22)."""
    consentimentos = listar_consentimentos(usuario_id)
    tem_consentimento = any(
        c.get("finalidade") == "curriculo_llm" and c.get("revogado_em") is None
        for c in consentimentos
    )
    if not tem_consentimento:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "erro": "Consentimento necessario",
                "detalhes": "Consentimento 'curriculo_llm' ausente ou revogado para o usuario.",
            },
        )


@router.get("/destinos/{destino_id}/exercicio")
def obter_exercicio_destino(
    destino_id: str,
    usuario: Annotated[dict, Depends(obter_usuario_logado)],
) -> dict[str, Any]:
    """Retorna o caderno de exercicio diagnostico do destino aprovado (whitelist estrita)."""
    dados_destino = carregar_dados_destino(destino_id)
    if not dados_destino:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "erro": "Nao encontrado",
                "detalhes": f"Destino '{destino_id}' nao encontrado ou nao aprovado no catalogo.",
            },
        )

    exercicio = dados_destino["exercicio"]
    politica = dados_destino["politica"]
    total_24h = contar_tentativas_24h(usuario["id"], exercicio["id"])
    tentativas_restantes = max(0, politica["max_tentativas_24h"] - total_24h)

    return formatar_exercicio_publico(dados_destino, tentativas_restantes)


@router.post(
    "/me/tentativas",
    response_model=TentativaResposta,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(exigir_csrf)],
)
def submeter_tentativa(
    payload: CriarTentativaRequisicao,
    usuario: Annotated[dict, Depends(obter_usuario_logado)],
    cliente_llm: Annotated[ClienteLLM, Depends(obter_cliente_llm)],
) -> dict[str, Any]:
    """Submete tentativa do exercicio diagnostico com correcao 50/50 e validacao rigorosa."""
    usuario_id = usuario["id"]

    # 1. Verifica consentimento ativo curriculo_llm antes de qualquer processamento (D22)
    _verificar_consentimento_curriculo_llm(usuario_id)

    # 2. Carrega e valida o destino homologado
    dados_destino = carregar_dados_destino(payload.destino_id)
    if not dados_destino:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "erro": "Nao encontrado",
                "detalhes": f"Destino '{payload.destino_id}' nao encontrado ou nao aprovado.",
            },
        )

    exercicio = dados_destino["exercicio"]
    politica = dados_destino["politica"]

    if payload.exercicio_id != exercicio["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "erro": "Requisicao invalida",
                "detalhes": "exercicio_id informado nao corresponde ao exercicio do destino.",
            },
        )

    # 3. Valida questoes objetivas: todas respondidas e nenhuma extra
    questoes_yaml = exercicio.get("questoes_objetivas") or []
    ids_questoes_yaml = {str(q["id"]) for q in questoes_yaml}
    ids_respostas = set(payload.respostas_objetivas.keys())
    if ids_respostas != ids_questoes_yaml:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "erro": "Requisicao invalida",
                "detalhes": "Respostas objetivas devem conter todas as questoes e nenhuma a mais.",
            },
        )

    for q in questoes_yaml:
        qid = str(q["id"])
        resp_val = payload.respostas_objetivas[qid]
        alternativas_validas = set(q.get("alternativas", {}).keys())
        if resp_val not in alternativas_validas:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "erro": "Requisicao invalida",
                    "detalhes": f"Alternativa '{resp_val}' invalida para a questao '{qid}'.",
                },
            )

    # 4. Valida resposta aberta: 20 a 4000 caracteres apos strip
    resp_aberta_strip = payload.resposta_aberta.strip()
    if len(resp_aberta_strip) < 20 or len(resp_aberta_strip) > 4000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "erro": "Requisicao invalida",
                "detalhes": "A resposta aberta deve conter entre 20 e 4000 caracteres.",
            },
        )

    # 5. Verifica limite de taxa de 24h ANTES de qualquer chamada a LLM e sem gravar (D21)
    max_tentativas = politica["max_tentativas_24h"]
    total_24h = contar_tentativas_24h(usuario_id, exercicio["id"])
    if total_24h >= max_tentativas:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "erro": "Limite de taxa excedido",
                "detalhes": (
                    f"Limite de {max_tentativas} tentativas em 24h atingido para este exercicio."
                ),
            },
        )

    # 6. Minimizacao de PII na resposta aberta (D22)
    texto_redigido, _ = redigir_pii(resp_aberta_strip)

    # 7. Normalizacao de espacos e geracao de chaves de cache (R23)
    texto_normalizado = " ".join(texto_redigido.strip().split())
    versao = str(exercicio["versao"])
    chave_cache = hashlib.sha256(
        f"{exercicio['id']}|{versao}|{texto_normalizado}".encode()
    ).hexdigest()
    sha256_resposta = hashlib.sha256(texto_normalizado.encode("utf-8")).hexdigest()

    # 8. Verificacao de cache Mongo
    doc_cache = buscar_avaliacao_cache_mongo(chave_cache)
    em_cache = False
    status_aberta = "avaliada"
    modelo_usado: str | None = None
    criterios_llm: list[dict[str, Any]] = []

    if doc_cache:
        em_cache = True
        status_aberta = "avaliada"
        modelo_usado = doc_cache.get("modelo")
        criterios_llm = doc_cache.get("criterios", [])
    else:
        qa = exercicio.get("questao_aberta") or {}
        rubrica = qa.get("rubrica") or []
        criterios_ids = [str(c["id"]) for c in rubrica]
        # A validação usa exatamente o texto que vai à LLM (sem delimitadores)
        texto_para_llm = sanitizar_delimitadores(texto_redigido)

        mensagens = construir_mensagens_avaliacao(
            cenario=exercicio.get("cenario", ""),
            enunciado_qa=qa.get("enunciado", ""),
            rubrica=rubrica,
            resposta_redigida=texto_para_llm,
        )
        schema = gerar_schema_rubrica(criterios_ids)

        try:
            resposta_llm = cliente_llm.gerar_json(
                mensagens=mensagens,
                schema=schema,
                nome_schema="avaliacao_rubrica",
                validar=lambda d: validar_saida_rubrica(d, criterios_ids, texto_para_llm),
            )
            status_aberta = "avaliada"
            modelo_usado = resposta_llm.modelo
            criterios_llm = resposta_llm.dados.get("criterios", [])

            # Grava no cache apenas se for bem-sucedida (R23)
            agora_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            salvar_avaliacao_cache_mongo(
                chave_sha256=chave_cache,
                exercicio_id=exercicio["id"],
                versao=versao,
                modelo=modelo_usado,
                criterios=criterios_llm,
                criado_em=agora_iso,
            )
        except ErroLLM:
            status_aberta = "parcial"
            modelo_usado = None
            criterios_llm = []

    # 9. Correcao deterministica da parte objetiva
    res_obj = corrigir_questoes_objetivas(questoes_yaml, payload.respostas_objetivas)

    # 10. Calculo da nota aberta e nota final 50/50
    nota_llm: float | None = None
    nota_final: float | None = None
    if status_aberta == "avaliada":
        qa = exercicio.get("questao_aberta") or {}
        rubrica = qa.get("rubrica") or []
        nota_llm = calcular_nota_aberta_llm(criterios_llm, len(rubrica))
        nota_final = calcular_nota_final(
            nota_objetiva=res_obj["nota"],
            nota_llm=nota_llm,
            peso_objetiva=politica["pesos"]["objetiva"],
            peso_llm=politica["pesos"]["llm"],
        )

    # 11. Determinacao do resultado (ambas as partes precisam atingir o minimo)
    resultado = determinar_resultado(
        nota_objetiva=res_obj["nota"],
        nota_llm=nota_llm,
        status_aberta=status_aberta,
        minimo_objetiva=politica["minimo_objetiva"],
        minimo_llm=politica["minimo_llm"],
    )

    # 12. Gravacao da tentativa no Oracle e resposta aberta no Mongo
    tentativa_id = uuid.uuid4().hex
    agora = datetime.now(UTC)
    agora_iso = agora.strftime("%Y-%m-%dT%H:%M:%SZ")
    avaliacao_id = chave_cache if status_aberta == "avaliada" else None

    salvar_resposta_aberta_mongo(
        tentativa_id=tentativa_id,
        usuario_id=usuario_id,
        sha256=sha256_resposta,
        texto_redigido=texto_redigido,
        criado_em=agora_iso,
    )

    salvar_tentativa_oracle(
        {
            "id": tentativa_id,
            "usuario_id": usuario_id,
            "destino_id": payload.destino_id,
            "exercicio_id": exercicio["id"],
            "exercicio_versao": versao,
            "respostas_objetivas_json": json.dumps(payload.respostas_objetivas),
            "acertos": res_obj["acertos"],
            "total_objetivas": res_obj["total"],
            "nota_objetiva": round(res_obj["nota"], 4),
            "status_aberta": status_aberta,
            "nota_llm": round(nota_llm, 4) if nota_llm is not None else None,
            "nota_final": round(nota_final, 4) if nota_final is not None else None,
            "resultado": resultado,
            "avaliacao_id": avaliacao_id,
            "sha256_resposta": sha256_resposta,
            "criado_em": agora,
        }
    )

    logger.info(
        "Tentativa registrada id=%s destino=%s resultado=%s status_aberta=%s",
        tentativa_id,
        payload.destino_id,
        resultado,
        status_aberta,
    )

    # 13. Montagem da resposta final
    tentativas_restantes_24h = max(0, max_tentativas - (total_24h + 1))
    reqs_avaliados = obter_requisitos_avaliados_destino(dados_destino)

    return {
        "tentativa_id": tentativa_id,
        "destino_id": payload.destino_id,
        "exercicio_id": exercicio["id"],
        "exercicio_versao": versao,
        "criado_em": agora_iso,
        "objetiva": {
            "acertos": res_obj["acertos"],
            "total": res_obj["total"],
            "nota": round(res_obj["nota"], 2),
            "questoes": res_obj["questoes"],
        },
        "aberta": {
            "status": status_aberta,
            "nota": round(nota_llm, 2) if nota_llm is not None else None,
            "modelo": modelo_usado,
            "em_cache": em_cache,
            "criterios": criterios_llm,
        },
        "nota_final": round(nota_final, 2) if nota_final is not None else None,
        "resultado": resultado,
        "requisitos_avaliados": reqs_avaliados,
        "tentativas_restantes_24h": tentativas_restantes_24h,
        "aviso": AVISO_DIAGNOSTICO,
    }


@router.post(
    "/me/tentativas/{tentativa_id}/discordo",
    response_model=DiscordoResposta,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(exigir_csrf)],
)
def registrar_discordo(
    tentativa_id: str,
    payload: RegistrarDiscordoRequisicao,
    usuario: Annotated[dict, Depends(obter_usuario_logado)],
) -> dict[str, Any]:
    """Registra contestacao de avaliacao pelo usuario (T08, LGPD art. 20)."""
    usuario_id = usuario["id"]
    motivo_strip = payload.motivo.strip()
    if len(motivo_strip) < 10 or len(motivo_strip) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "erro": "Requisicao invalida",
                "detalhes": "O motivo da contestacao deve conter entre 10 e 1000 caracteres.",
            },
        )

    motivo_redigido, _ = redigir_pii(motivo_strip)
    discordo_em, motivo_salvo = registrar_discordo_oracle(
        tentativa_id=tentativa_id,
        usuario_id=usuario_id,
        motivo_redigido=motivo_redigido,
    )

    logger.info("Contestacao registrada tentativa_id=%s usuario_id=%s", tentativa_id, usuario_id)

    return {
        "tentativa_id": tentativa_id,
        "discordo_em": discordo_em,
        "motivo": motivo_salvo,
        "status_contestacao": "registrada",
    }


@router.get(
    "/me/tentativas",
    response_model=ListarTentativasResposta,
    status_code=status.HTTP_200_OK,
)
def listar_tentativas(
    usuario: Annotated[dict, Depends(obter_usuario_logado)],
    destino_id: str | None = Query(None),
) -> dict[str, Any]:
    """Lista tentativas do usuario com resumo e identificacao da ultima e melhor."""
    return listar_tentativas_usuario(usuario["id"], destino_id)
