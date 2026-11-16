"""Rotas da API de mercado e painel técnico R06."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from citizentech.mercado.adzuna import montar_amostra_adzuna
from citizentech.mercado.esquemas import (
    AbstencaoSecao,
    ContextoRegionalSecao,
    CriterioPromocao,
    ModeloPainelTecnico,
    ObservadoSecao,
    ObservadoSerieItem,
    PrevistoSecao,
    PrevistoSerieItem,
    ReferenciaTemporal,
    RespostaMercado,
    RespostaModelos,
)
from citizentech.mercado.snapshot import (
    REGIAO_POR_DIGITO,
    UF_PARA_IBGE,
    carregar_escopo_mvp,
    carregar_snapshot_mercado,
)

router = APIRouter(prefix="/mercado", tags=["mercado"])


def _validar_uf(uf: str) -> tuple[str, str]:
    """Valida e normaliza sigla da UF, retornando (sigla, codigo_ibge)."""
    uf_limpa = uf.strip().upper()
    if uf_limpa not in UF_PARA_IBGE:
        raise HTTPException(
            status_code=400,
            detail={
                "erro": "Requisicao invalida",
                "detalhes": (
                    f"UF '{uf}' invalida. Esperada sigla de duas letras de um estado brasileiro."
                ),
            },
        )
    return uf_limpa, UF_PARA_IBGE[uf_limpa]


def _validar_destino(destino: str) -> None:
    """Valida se o destino pertence ao catálogo do escopo MVP (R29)."""
    escopo = carregar_escopo_mvp()
    destinos_validos = escopo.get("destinos", [])
    if destino not in destinos_validos:
        raise HTTPException(
            status_code=404,
            detail={
                "erro": "Nao encontrado",
                "detalhes": (
                    f"Destino '{destino}' nao encontrado no catalogo do escopo MVP (R29)."
                ),
            },
        )


@router.get("/{destino}", response_model=RespostaMercado)
def obter_mercado(destino: str, uf: str = "SP") -> RespostaMercado:
    """Retorna dados de mercado observado e previsto para um destino e UF."""
    uf_sigla, uf_codigo = _validar_uf(uf)
    _validar_destino(destino)

    snapshot = carregar_snapshot_mercado()

    serie_alvo = next(
        (
            s
            for s in snapshot.get("series", [])
            if s.get("destino") == destino and str(s.get("uf")) == uf_codigo
        ),
        None,
    )

    elegivel = bool(serie_alvo.get("elegivel")) if serie_alvo else False
    motivo_densidade = (
        str(serie_alvo.get("motivo_densidade", "sem_dados_treino"))
        if serie_alvo
        else "sem_dados_treino"
    )
    media_alvo = (
        float(serie_alvo["media_alvo_treino"])
        if serie_alvo and serie_alvo.get("media_alvo_treino") is not None
        else None
    )

    # Série observada local
    observado_bruto = serie_alvo.get("observado", []) if serie_alvo else []
    serie_obs = [
        ObservadoSerieItem(
            competencia=str(r["competencia"]),
            valor=(
                float(r["admissoes"])
                if r.get("admissoes") is not None
                else None
            ),
        )
        for r in observado_bruto
    ]

    if serie_obs:
        ref_temp_obs = ReferenciaTemporal(
            inicio=serie_obs[0].competencia,
            fim=serie_obs[-1].competencia,
        )
    else:
        ref_temp_obs = ReferenciaTemporal(
            inicio=str(snapshot.get("metadados_fonte", {}).get("competencia_min", "202001")),
            fim=str(snapshot.get("metadados_fonte", {}).get("competencia_max", "202509")),
        )

    observado_secao = ObservadoSecao(
        natureza="observado",
        fonte="Novo Caged — microdados públicos do MTE (PDET)",
        populacao=(
            "Admissões formais com ensino superior completo ou mais "
            "nas ocupações CBO curadas de cada destino"
        ),
        unidade="admissões por mês",
        referencia_temporal=ref_temp_obs,
        serie=serie_obs,
    )

    previsto_secao: PrevistoSecao | None = None
    abstencao_secao: AbstencaoSecao | None = None

    if elegivel and serie_alvo:
        promocao = snapshot.get("promocao", {})
        modelo_exibido = str(promocao.get("modelo_exibido", "sazonal"))
        status_promocao = str(promocao.get("status", "nao_decidida"))

        previsoes_modelo = serie_alvo.get("previsoes_validacao", {}).get(modelo_exibido, [])
        serie_prev = [
            PrevistoSerieItem(
                competencia_origem=str(r["competencia"]),
                previsao=float(r["previsao"]),
                realizado=float(r["alvo"]),
            )
            for r in previsoes_modelo
        ]

        if serie_prev:
            ref_temp_prev = ReferenciaTemporal(
                inicio=serie_prev[0].competencia_origem,
                fim=serie_prev[-1].competencia_origem,
            )
        else:
            ref_temp_prev = ReferenciaTemporal(inicio="202501", fim="202509")

        previsto_secao = PrevistoSecao(
            natureza="previsto_retrospectivo",
            fonte="Estimativa retrospectiva baseada em modelos validados no Novo Caged",
            populacao=(
                "Admissões formais com ensino superior completo ou mais "
                "nas ocupações CBO curadas de cada destino"
            ),
            unidade="admissões somadas nos 3 meses seguintes à competência de origem",
            referencia_temporal=ref_temp_prev,
            modelo_exibido=modelo_exibido,
            status_promocao=status_promocao,
            serie=serie_prev,
        )
    else:
        # Abstenção explícita com contexto regional observado (D04a/T06)
        regiao_nome = REGIAO_POR_DIGITO.get(uf_codigo[0], "Regional")
        ctx_reg_raw = next(
            (
                r
                for r in snapshot.get("contexto_regional", [])
                if r.get("destino") == destino and r.get("regiao") == regiao_nome
            ),
            None,
        )

        if ctx_reg_raw and "observado" in ctx_reg_raw:
            serie_reg = [
                ObservadoSerieItem(
                    competencia=str(r["competencia"]),
                    valor=(
                        float(r["admissoes"])
                        if r.get("admissoes") is not None
                        else None
                    ),
                )
                for r in ctx_reg_raw["observado"]
            ]
            ref_temp_reg = (
                ReferenciaTemporal(
                    inicio=serie_reg[0].competencia,
                    fim=serie_reg[-1].competencia,
                )
                if serie_reg
                else ReferenciaTemporal(inicio="202001", fim="202509")
            )
        else:
            serie_reg = []
            ref_temp_reg = ReferenciaTemporal(inicio="202001", fim="202509")

        abstencao_secao = AbstencaoSecao(
            motivo=motivo_densidade,
            media_alvo_treino=media_alvo,
            limite_minimo=10.0,
            contexto_regional=ContextoRegionalSecao(
                natureza="observado",
                fonte="Novo Caged — microdados públicos do MTE (PDET)",
                populacao="Admissões formais agregadas na macrorregião geográfica",
                unidade="admissões por mês",
                referencia_temporal=ref_temp_reg,
                regiao=regiao_nome,
                serie=serie_reg,
            ),
        )

    amostra_adzuna = montar_amostra_adzuna(destino)

    avisos = [
        (
            "Números medem admissões formais estimadas no grupo e território registradas no "
            "Novo Caged (PDET), sem constituir oportunidade aberta ou chance individual."
        ),
        (
            "Previsões disponíveis são retrospectivas (competências de 2025); 2026 está reservado "
            "à avaliação final no holdout fechado."
        ),
        (
            "Nenhum modelo de aprendizado foi promovido para substituir o baseline de referência "
            "(status de promoção: não decidida)."
        ),
    ]

    return RespostaMercado(
        destino=destino,
        uf=uf_sigla,
        uf_codigo=uf_codigo,
        observado=observado_secao,
        previsto=previsto_secao,
        abstencao=abstencao_secao,
        amostra_adzuna=amostra_adzuna,
        avisos=avisos,
    )


@router.get("/{destino}/modelos", response_model=RespostaModelos)
def obter_modelos(destino: str, uf: str = "SP") -> RespostaModelos:
    """Retorna painel técnico comparativo de todos os 6 modelos (R06)."""
    uf_sigla, uf_codigo = _validar_uf(uf)
    _validar_destino(destino)

    snapshot = carregar_snapshot_mercado()

    serie_alvo = next(
        (
            s
            for s in snapshot.get("series", [])
            if s.get("destino") == destino and str(s.get("uf")) == uf_codigo
        ),
        None,
    )

    elegivel = bool(serie_alvo.get("elegivel")) if serie_alvo else False
    motivo_densidade = (
        str(serie_alvo.get("motivo_densidade", "sem_dados_treino"))
        if serie_alvo
        else "sem_dados_treino"
    )

    prom_raw = snapshot.get("promocao", {})
    criterio_promocao = CriterioPromocao(
        criterio=str(prom_raw.get("criterio", "D10a congelado")),
        status=str(prom_raw.get("status", "nao_decidida")),
        modelo_exibido=str(prom_raw.get("modelo_exibido", "sazonal")),
    )

    modelos_saida: list[ModeloPainelTecnico] = []
    for m in snapshot.get("modelos", []):
        id_mod = str(m.get("id"))
        if elegivel and serie_alvo:
            met_serie = serie_alvo.get("metricas_validacao", {}).get(id_mod)
            prevs = serie_alvo.get("previsoes_validacao", {}).get(id_mod, [])
        else:
            met_serie = None
            prevs = []

        modelos_saida.append(
            ModeloPainelTecnico(
                id=id_mod,
                nome=str(m.get("nome")),
                tipo=str(m.get("tipo")),
                promovido=False,
                exibido_ao_usuario=bool(m.get("exibido_ao_usuario")),
                metricas_validacao_global=m.get("metricas_validacao_global", {}),
                metricas_cv_treino=m.get("metricas_cv_treino", {}),
                metricas_serie=met_serie,
                previsoes_validacao=prevs,
                model_card=m.get("model_card", {}),
            )
        )

    avisos = [
        "CV no treino não é aninhado: métrica de seleção, otimista",
        "hash garante integridade local, não autenticidade",
        (
            "Avaliação final no holdout 2026 permanece fechada nesta fatia; "
            "nenhum modelo foi promovido."
        ),
    ]

    return RespostaModelos(
        destino=destino,
        uf=uf_sigla,
        uf_codigo=uf_codigo,
        elegivel=elegivel,
        motivo_densidade=motivo_densidade,
        criterio_promocao=criterio_promocao,
        modelos=modelos_saida,
        avisos=avisos,
    )
