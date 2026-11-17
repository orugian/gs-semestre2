"""Serviço de montagem de entradas para comparação e resumo de mercado."""

from __future__ import annotations

import logging
from typing import Any

from citizentech.avaliacao.repositorio import resultados_exercicio_para_comparacao
from citizentech.catalogo import carregar_destinos_aprovados
from citizentech.comparacao.dominio import comparar_destinos
from citizentech.competencias.repositorio import competencias_para_comparacao
from citizentech.intencao.repositorio import buscar_intencao
from citizentech.mercado.snapshot import UF_PARA_IBGE, carregar_snapshot_mercado

logger = logging.getLogger("citizentech.comparacao")


def resumo_mercado_para_comparacao(destino_id: str, uf: str | None) -> dict[str, Any]:
    """Retorna o resumo de mercado observado para o destino e UF (T17 / regra de produto)."""
    if uf is None:
        return {
            "disponivel": False,
            "natureza": "indisponivel",
            "motivo": "uf_nao_informada",
        }

    uf_sigla = uf.strip().upper()
    uf_codigo = UF_PARA_IBGE.get(uf_sigla)
    if not uf_codigo:
        return {
            "disponivel": False,
            "natureza": "indisponivel",
            "motivo": "sem_serie_para_uf",
            "uf": uf,
        }

    try:
        snapshot = carregar_snapshot_mercado()
    except Exception:
        return {
            "disponivel": False,
            "natureza": "indisponivel",
            "motivo": "snapshot_indisponivel",
        }

    serie_alvo = next(
        (
            s
            for s in snapshot.get("series", [])
            if s.get("destino") == destino_id and str(s.get("uf")) == uf_codigo
        ),
        None,
    )

    if not serie_alvo:
        return {
            "disponivel": False,
            "natureza": "indisponivel",
            "motivo": "sem_serie_para_uf",
            "uf": uf,
        }

    observado_bruto = serie_alvo.get("observado", [])
    if not observado_bruto:
        return {
            "disponivel": False,
            "natureza": "indisponivel",
            "motivo": "sem_serie_para_uf",
            "uf": uf,
        }

    observados_validos = [r for r in observado_bruto if r.get("admissoes") is not None]
    if not observados_validos:
        return {
            "disponivel": False,
            "natureza": "indisponivel",
            "motivo": "sem_serie_para_uf",
            "uf": uf,
        }

    ref_temp = f"{observado_bruto[0]['competencia']}–{observado_bruto[-1]['competencia']}"
    ultimo = observados_validos[-1]
    ultimo_valor = ultimo["admissoes"]
    elegivel = bool(serie_alvo.get("elegivel", False))

    valor_texto = (
        f"{ultimo_valor:.0f}"
        if float(ultimo_valor).is_integer()
        else f"{float(ultimo_valor):.1f}".replace(".", ",")
    )
    resumo_texto = (
        f"Último mês observado ({ultimo['competencia']}): {valor_texto} "
        "admissões formais estimadas no grupo e território (Novo Caged)."
    )

    return {
        "disponivel": True,
        "natureza": "observado",
        "fonte": "Novo Caged — microdados públicos do MTE (PDET)",
        "populacao": (
            "Admissões formais com ensino superior completo ou mais "
            "nas ocupações CBO curadas de cada destino"
        ),
        "unidade": "admissões por mês",
        "uf": uf,
        "referencia_temporal": ref_temp,
        "ultimo_observado": {
            "competencia": str(ultimo["competencia"]),
            "valor": ultimo_valor,
        },
        "elegivel_previsao": elegivel,
        "resumo": resumo_texto,
        "detalhe_url": f"/mercado/{destino_id}?uf={uf}",
    }


def executar_comparacao(
    usuario_id: str,
    destinos_solicitados: list[str],
    uf_solicitada: str | None,
) -> tuple[dict[str, Any], str | None]:
    """Prepara entradas, chama comparar_destinos e retorna (resultado_dominio, uf_efetiva)."""
    # 1. Carrega destinos aprovados do catálogo
    destinos_brutos = carregar_destinos_aprovados()
    mapa_destinos = {d.get("destino_id"): d for d in destinos_brutos}

    destinos_entrada: list[dict[str, Any]] = []
    for did in destinos_solicitados:
        if did not in mapa_destinos:
            raise ValueError(
                f"Destino '{did}' não encontrado ou não aprovado no catálogo fechado."
            )
        dados = mapa_destinos[did]
        requisitos_formatados = []
        for req in dados.get("requisitos") or []:
            if not isinstance(req, dict):
                continue
            requisitos_formatados.append({
                "id_local": str(req.get("id_local", "")),
                "esco_id": str(req.get("esco_id", "")),
                "titulo_oficial": str(req.get("titulo_oficial") or req.get("titulo", "")),
                "obrigatorio_proposto": bool(
                    req.get("obrigatorio_proposto")
                    if "obrigatorio_proposto" in req
                    else req.get("obrigatorio", False)
                ),
            })
        destinos_entrada.append({
            "destino_id": did,
            "nome": dados.get("nome", ""),
            "status_revisao": "aprovado",
            "requisitos": requisitos_formatados,
        })

    # 2. Competências do usuário
    competencias = competencias_para_comparacao(usuario_id)

    # 3. Intenção e resolução de UF efetiva
    intencao = buscar_intencao(usuario_id)
    if uf_solicitada:
        uf_efetiva = uf_solicitada.strip().upper()
    elif intencao and intencao.get("uf"):
        uf_efetiva = intencao["uf"]
    else:
        uf_efetiva = None

    preferencias: dict[str, Any] | None = None
    if intencao:
        preferencias = {
            "horas_semana": intencao["horas_semana"],
            "uf": intencao["uf"],
            "atividades_desejadas": intencao["atividades_desejadas"],
        }

    # 4. Mercado por destino
    mercado: dict[str, Any] = {}
    for did in destinos_solicitados:
        mercado[did] = resumo_mercado_para_comparacao(did, uf_efetiva)

    # 5. Executa domínio
    resultados_exercicio = resultados_exercicio_para_comparacao(usuario_id)
    resultado_dominio = comparar_destinos(
        destinos=destinos_entrada,
        competencias=competencias,
        resultados_exercicio=resultados_exercicio,
        preferencias=preferencias,
        mercado=mercado,
    )

    return resultado_dominio, uf_efetiva
