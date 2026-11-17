"""Rotas de curriculo e experiencias (/me).

Risco arquitetural documentado (parser multipart / upload):
- O parser multipart do Starlette (UploadFile/python-multipart) pode realizar spool
  de arquivos acima de 1 MB (limite padrao de SpooledTemporaryFile) em arquivo temporario
  do sistema operacional antes mesmo da execucao alcancar o corpo da rota.
- Requisicoes com corpo chunked transfer-encoding (sem cabecalho Content-Length)
  so tem seu limite de tamanho avaliado durante/apos o parse e consumo do stream.
- Mitigacao recomendada para o ambiente de producao:
  Configuracao de limite estrito de tamanho do corpo da requisicao (client_max_body_size
  ou request buffering limit no proxy reverso / API Gateway, e.g. Nginx, Traefik, AWS ALB).
"""

import hashlib
import logging
import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status

from citizentech.auth.dependencias import exigir_csrf, obter_usuario_logado
from citizentech.consentimentos.dependencias import exigir_consentimento
from citizentech.curriculo.esquemas import (
    ConfirmarEnvioRequisicao,
    CriarExperienciasRequisicao,
    CurriculoResposta,
)
from citizentech.curriculo.extracao import (
    detectar_tipo_arquivo,
    extrair_texto_docx,
    extrair_texto_pdf,
)
from citizentech.curriculo.redacao import redigir_pii
from citizentech.curriculo.repositorio import (
    RepositorioCurriculos,
    obter_repositorio_curriculos,
)

logger = logging.getLogger("citizentech.curriculo")

router = APIRouter(prefix="/me", tags=["curriculo"])

LIMITE_ARQUIVO_BYTES = 2 * 1024 * 1024  # 2.097.152 bytes (2 MB)
MARGEM_MULTIPART_BYTES = 64 * 1024  # 64 KB de margem para envelope multipart


@router.post(
    "/experiencias",
    response_model=CurriculoResposta,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(exigir_csrf)],
)
def criar_experiencias(
    payload: CriarExperienciasRequisicao,
    usuario: Annotated[dict, Depends(exigir_consentimento("perfil"))],
    repositorio: Annotated[
        RepositorioCurriculos, Depends(obter_repositorio_curriculos)
    ],
) -> dict:
    """Cria e redige experiencias profissionais a partir de texto colado."""
    # 1. Redacao de PII
    texto_redigido, redacoes = redigir_pii(payload.texto)
    sha256_texto = hashlib.sha256(texto_redigido.encode("utf-8")).hexdigest()
    criado_em = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    curriculo_id = uuid.uuid4().hex
    documento = {
        "_id": curriculo_id,
        "usuario_id": usuario["id"],
        "origem": "texto",
        "status": "aguardando_confirmacao",
        "texto_redigido": texto_redigido,
        "sha256_texto_redigido": sha256_texto,
        "redacoes": redacoes,
        "criado_em": criado_em,
        "confirmado_em": None,
    }

    resultado = repositorio.salvar(documento)
    logger.debug("Experiencias registradas: id=%s origem=texto", curriculo_id)
    return resultado


@router.post(
    "/curriculo",
    response_model=CurriculoResposta,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(exigir_csrf)],
)
async def upload_curriculo(
    request: Request,
    usuario: Annotated[dict, Depends(exigir_consentimento("perfil"))],
    repositorio: Annotated[
        RepositorioCurriculos, Depends(obter_repositorio_curriculos)
    ],
    arquivo: Annotated[UploadFile, File()],
) -> dict:
    """Recebe upload de curriculo (PDF ou DOCX), extrai e redige o texto."""
    # 1. Verificacao preventiva de Content-Length
    tamanho_header = request.headers.get("content-length")
    if tamanho_header:
        try:
            if int(tamanho_header) > LIMITE_ARQUIVO_BYTES + MARGEM_MULTIPART_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "erro": "Arquivo muito grande",
                        "detalhes": "Tamanho da requisicao excede o limite de 2 MB.",
                    },
                )
        except ValueError:
            pass

    # 3. Leitura com controle estrito de bytes
    conteudo = bytearray()
    try:
        while chunk := await arquivo.read(64 * 1024):
            conteudo.extend(chunk)
            if len(conteudo) > LIMITE_ARQUIVO_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "erro": "Arquivo muito grande",
                        "detalhes": "O arquivo enviado excede o limite maximo de 2 MB.",
                    },
                )
    finally:
        await arquivo.close()

    dados_arquivo = bytes(conteudo)

    # 4. Inspecao de formato pelo conteudo (nao por extensao nem content-type)
    origem = detectar_tipo_arquivo(dados_arquivo)

    # 5. Extracao de texto local (sem OCR)
    if origem == "pdf":
        texto_extraido = extrair_texto_pdf(dados_arquivo)
    else:
        texto_extraido = extrair_texto_docx(dados_arquivo)

    # 6. Redacao de PII
    texto_redigido, redacoes = redigir_pii(texto_extraido)
    sha256_texto = hashlib.sha256(texto_redigido.encode("utf-8")).hexdigest()
    criado_em = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    curriculo_id = uuid.uuid4().hex
    documento = {
        "_id": curriculo_id,
        "usuario_id": usuario["id"],
        "origem": origem,
        "status": "aguardando_confirmacao",
        "texto_redigido": texto_redigido,
        "sha256_texto_redigido": sha256_texto,
        "redacoes": redacoes,
        "criado_em": criado_em,
        "confirmado_em": None,
    }

    resultado = repositorio.salvar(documento)
    # Log estritamente seguro: nenhum dado pessoal, texto ou nome de arquivo
    logger.debug("Curriculo processado com sucesso: id=%s origem=%s", curriculo_id, origem)
    return resultado


@router.get(
    "/curriculo/{curriculo_id}",
    response_model=CurriculoResposta,
    status_code=status.HTTP_200_OK,
)
def obter_curriculo(
    curriculo_id: str,
    usuario: Annotated[dict, Depends(obter_usuario_logado)],
    repositorio: Annotated[
        RepositorioCurriculos, Depends(obter_repositorio_curriculos)
    ],
) -> dict:
    """Recupera o curriculo redigido pertencente exclusivamente ao usuario (T14)."""
    documento = repositorio.buscar_por_id(
        curriculo_id=curriculo_id, usuario_id=usuario["id"]
    )
    if not documento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "erro": "Recurso nao encontrado",
                "detalhes": "Curriculo nao encontrado.",
            },
        )
    return documento


@router.post(
    "/curriculo/confirmar-envio",
    response_model=CurriculoResposta,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(exigir_csrf)],
)
def confirmar_envio(
    payload: ConfirmarEnvioRequisicao,
    usuario: Annotated[dict, Depends(exigir_consentimento("curriculo_llm"))],
    repositorio: Annotated[
        RepositorioCurriculos, Depends(obter_repositorio_curriculos)
    ],
) -> dict:
    """Confirma o envio do curriculo redigido com consentimento curriculo_llm ativo."""
    # 1. Busca documento pertencente ao usuario (T14)
    documento_existente = repositorio.buscar_por_id(
        curriculo_id=payload.curriculo_id, usuario_id=usuario["id"]
    )
    if not documento_existente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "erro": "Recurso nao encontrado",
                "detalhes": "Curriculo nao encontrado.",
            },
        )

    # 3. Se houver texto revisado, passa novamente pela redacao de PII
    if payload.texto_revisado is not None:
        texto_final, redacoes = redigir_pii(payload.texto_revisado)
        sha256_final = hashlib.sha256(texto_final.encode("utf-8")).hexdigest()
    else:
        texto_final = documento_existente["texto_redigido"]
        redacoes = documento_existente["redacoes"]
        sha256_final = documento_existente["sha256_texto_redigido"]

    confirmado_em = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    resultado = repositorio.confirmar(
        curriculo_id=payload.curriculo_id,
        usuario_id=usuario["id"],
        texto_redigido=texto_final,
        sha256_texto_redigido=sha256_final,
        redacoes=redacoes,
        confirmado_em=confirmado_em,
    )
    if not resultado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "erro": "Recurso nao encontrado",
                "detalhes": "Curriculo nao encontrado.",
            },
        )

    logger.debug("Curriculo confirmado: id=%s", payload.curriculo_id)
    return resultado
