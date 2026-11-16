"""Regras de negocio para gestao de sessoes de laboratorio (S14)."""

import secrets
import uuid
from datetime import UTC, datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status

from citizentech.curriculo.redacao import redigir_pii
from citizentech.laboratorio.repositorio import (
    ConflitoCodigoSessao,
    criar_sessao_oracle,
    salvar_relato_pendente,
)
from citizentech.leituras.repositorio import ler_todas_leituras
from citizentech.leituras.rotas import calcular_indicadores
from citizentech.limiares import carregar_limiares
from citizentech.outbox.banco import obter_mapa_estados

ALFABETO_CODIGO = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_SAO_PAULO = timezone(timedelta(hours=-3))


def gerar_codigo() -> str:
    """Gera codigo curto LAB-XXXXXX sobre o alfabeto sem ambiguidades."""
    return "LAB-" + "".join(secrets.choice(ALFABETO_CODIGO) for _ in range(6))


def formatar_instrucoes(codigo: str, expira_em: datetime) -> str:
    """Gera texto explicativo em pt-BR com timestamp local de America/Sao_Paulo."""
    if expira_em.tzinfo is None:
        expira_em = expira_em.replace(tzinfo=UTC)
    expira_sp = expira_em.astimezone(_SAO_PAULO).strftime("%d/%m/%Y %H:%M:%S")
    return (
        f"Configure o dispositivo da bancada com sessao_laboratorio_id = {codigo}. "
        f"As leituras enviadas com esse código até {expira_sp} aparecem nesta sessão."
    )


def abrir_nova_sessao(usuario_id: str) -> dict[str, Any]:
    """Abre uma nova sessao de laboratorio valida por 4 horas."""
    sessao_id = uuid.uuid4().hex
    criado_em = datetime.now(UTC)
    expira_em = criado_em + timedelta(hours=4)

    sessao: dict[str, Any] | None = None
    for _ in range(5):
        codigo = gerar_codigo()
        try:
            sessao = criar_sessao_oracle(
                sessao_id=sessao_id,
                usuario_id=usuario_id,
                codigo=codigo,
                criado_em=criado_em,
                expira_em=expira_em,
            )
            break
        except ConflitoCodigoSessao:
            continue

    if sessao is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "erro": "Erro interno",
                "detalhes": "Nao foi possivel gerar um codigo unico de sessao.",
            },
        )

    instrucoes = formatar_instrucoes(sessao["codigo"], expira_em)
    return {
        "id": sessao["id"],
        "codigo": sessao["codigo"],
        "status": "ativa",
        "criado_em": sessao["criado_em"],
        "expira_em": sessao["expira_em"],
        "instrucoes": instrucoes,
    }


def compor_detalhes_sessao(sessao: dict[str, Any]) -> dict[str, Any]:
    """Compoe leituras do CSV e indicadores para retorno do contrato."""
    agora = datetime.now(UTC)
    expira_em_dt = sessao["expira_em_dt"]
    status_calculado = sessao["status"]
    if status_calculado == "ativa" and expira_em_dt <= agora:
        status_calculado = "expirada"

    instrucoes = formatar_instrucoes(sessao["codigo"], expira_em_dt)

    # 1. Carrega leituras do CSV filtrando pela sessao
    todos = ler_todas_leituras()
    mapa_estados = obter_mapa_estados()
    if mapa_estados:
        for r in todos:
            if r["evento_id"] in mapa_estados:
                r["estado"] = mapa_estados[r["evento_id"]]

    codigo = sessao["codigo"]
    leituras_sessao = [r for r in todos if r.get("sessao_laboratorio_id") == codigo]

    # 2. Calcula indicadores por metrica conhecida
    limiares = carregar_limiares()
    catalogo = limiares.get("metricas", {})
    indicadores = {}
    for m in sorted(catalogo.keys()):
        leituras_m = [r for r in leituras_sessao if r.get("metrica") == m]
        indicadores[m] = calcular_indicadores(leituras_m)

    return {
        "id": sessao["id"],
        "codigo": sessao["codigo"],
        "status": status_calculado,
        "criado_em": sessao["criado_em"],
        "expira_em": sessao["expira_em"],
        "instrucoes": instrucoes,
        "relato": {
            "texto_redigido": sessao.get("relato_redigido"),
            "status": sessao.get("relato_status") or "nenhum",
        },
        "leituras": leituras_sessao,
        "indicadores": indicadores,
    }


def registrar_relato_sessao(
    sessao_id: str,
    usuario_id: str,
    relato_bruto: str,
) -> dict[str, Any]:
    """Valida, redige e registra relato na sessao."""
    relato_strip = relato_bruto.strip()
    if len(relato_strip) < 1 or len(relato_strip) > 280:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "erro": "Requisicao invalida",
                "detalhes": "O relato deve conter entre 1 e 280 caracteres.",
            },
        )

    texto_redigido, _ = redigir_pii(relato_strip)

    try:
        status_sessao, status_relato = salvar_relato_pendente(
            sessao_id=sessao_id,
            usuario_id=usuario_id,
            texto_redigido=texto_redigido,
        )
    except KeyError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "erro": "Nao encontrado",
                "detalhes": "Sessao de laboratorio nao encontrada.",
            },
        ) from err

    if status_sessao == "encerrada_ou_expirada":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "erro": "Conflito",
                "detalhes": "Sessao encerrada ou expirada.",
            },
        )

    if status_relato == "enviado":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "erro": "Conflito",
                "detalhes": "Relato ja foi enviado para a nuvem.",
            },
        )

    return {
        "texto_redigido": texto_redigido,
        "status": "pendente",
    }
