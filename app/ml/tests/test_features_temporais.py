"""Testes de features temporais do Novo Caged (T18, T05, cobertura, etc.)."""

from pathlib import Path

import pandas as pd
import pytest

from citizentech_ml.features import construir_painel_features
from citizentech_ml.ingestao.ocupacoes import carregar_ocupacoes

CAMINHO_CATALOGO = Path(__file__).resolve().parents[2] / "catalogo" / "ocupacoes_cbo.json"


def test_t18_for_tardio_nao_altera_features_anteriores():
    """T18: com admissão MOV em 202401, mais FOR com competencia_mov=202401

    e competencia_dec/arquivo=202404, a feature de 202402 deve ser idêntica
    antes/depois do FOR, enquanto a de 202404 deve incorporá-lo.
    """
    ocupacoes = carregar_ocupacoes(CAMINHO_CATALOGO)

    # Cobertura sintética com MOV, FOR, EXC ingeridos para 202401 até 202404
    cobertura_registros = []
    for comp in ["202401", "202402", "202403", "202404"]:
        for tipo in ["MOV", "FOR", "EXC"]:
            cobertura_registros.append(
                {"competencia": comp, "tipo": tipo, "situacao": "ingerido"}
            )
    df_cobertura = pd.DataFrame(cobertura_registros)

    # 1. Registro MOV regular em 202401
    reg_mov_202401 = {
        "competencia_mov": "202401",
        "competencia_dec": "202401",
        "competencia_arquivo": "202401",
        "competencia_exc": None,
        "arquivo_tipo": "MOV",
        "saldo_movimentacao": 1,
        "cbo2002_ocupacao": "211205",  # analista_dados_bi
        "uf": "35",  # SP
        "grau_instrucao": 9,  # Superior completo
    }

    # 2. Registro FOR tardio declarando admissão de 202401 somente em 202404
    reg_for_tardio = {
        "competencia_mov": "202401",
        "competencia_dec": "202404",
        "competencia_arquivo": "202404",
        "competencia_exc": None,
        "arquivo_tipo": "FOR",
        "saldo_movimentacao": 1,
        "cbo2002_ocupacao": "211205",
        "uf": "35",
        "grau_instrucao": 9,
    }

    # Cenário A: apenas MOV disponível
    df_dados_antes = pd.DataFrame([reg_mov_202401])
    painel_antes = construir_painel_features(
        dados=df_dados_antes,
        cobertura=df_cobertura,
        ocupacoes=ocupacoes,
        competencias=["202402", "202404"],
    )

    # Filtrar para a série de teste (analista_dados_bi em SP)
    serie_antes_202402 = painel_antes[
        (painel_antes["destino"] == "analista_dados_bi")
        & (painel_antes["uf"] == "35")
        & (painel_antes["competencia"] == "202402")
    ]
    serie_antes_202404 = painel_antes[
        (painel_antes["destino"] == "analista_dados_bi")
        & (painel_antes["uf"] == "35")
        & (painel_antes["competencia"] == "202404")
    ]

    assert len(serie_antes_202402) == 1
    assert len(serie_antes_202404) == 1
    # Antes do FOR: lag_1 em 202402 enxerga 1 admissão; lag_3 em 202404 enxerga 1 admissão
    assert serie_antes_202402["admissoes_lag_1"].iloc[0] == 1.0
    assert serie_antes_202404["admissoes_lag_3"].iloc[0] == 1.0

    # Cenário B: MOV + FOR tardio (publicado em 202404)
    df_dados_depois = pd.DataFrame([reg_mov_202401, reg_for_tardio])
    painel_depois = construir_painel_features(
        dados=df_dados_depois,
        cobertura=df_cobertura,
        ocupacoes=ocupacoes,
        competencias=["202402", "202404"],
    )

    serie_depois_202402 = painel_depois[
        (painel_depois["destino"] == "analista_dados_bi")
        & (painel_depois["uf"] == "35")
        & (painel_depois["competencia"] == "202402")
    ]
    serie_depois_202404 = painel_depois[
        (painel_depois["destino"] == "analista_dados_bi")
        & (painel_depois["uf"] == "35")
        & (painel_depois["competencia"] == "202404")
    ]

    # Em 202402, o FOR de 202404 AINDA NÃO EXISTIA: a feature deve ser IDÊNTICA a antes (1.0)
    assert serie_depois_202402["admissoes_lag_1"].iloc[0] == 1.0
    assert (
        serie_depois_202402["admissoes_lag_1"].iloc[0]
        == serie_antes_202402["admissoes_lag_1"].iloc[0]
    )

    # Em 202404, o FOR já foi publicado: lag_3 deve incorporar a admissão tardia (1 + 1 = 2.0)
    assert serie_depois_202404["admissoes_lag_3"].iloc[0] == 2.0


def test_t05_alterar_mov_futuro_e_exc_tardia_mantem_passado():
    """T05: Alterar MOV futuro e EXC tardia mantém o passado inalterado.

    EXC só afeta as features a partir da data de disponibilidade conservadora.
    """
    ocupacoes = carregar_ocupacoes(CAMINHO_CATALOGO)

    meses = [
        "202303", "202304", "202305", "202306", "202307", "202308", "202309",
        "202310", "202311", "202312", "202401", "202402",
        "202403", "202404", "202405", "202406",
    ]
    cobertura_registros = []
    for m in meses:
        for t in ["MOV", "FOR", "EXC"]:
            cobertura_registros.append({"competencia": m, "tipo": t, "situacao": "ingerido"})
    df_cobertura = pd.DataFrame(cobertura_registros)

    # 1. Admissão original em 202305
    reg_mov_202305 = {
        "competencia_mov": "202305",
        "competencia_dec": "202305",
        "competencia_arquivo": "202305",
        "competencia_exc": None,
        "arquivo_tipo": "MOV",
        "saldo_movimentacao": 1,
        "cbo2002_ocupacao": "211205",
        "uf": "35",
        "grau_instrucao": 9,
    }

    # Estado Inicial
    painel_inicial = construir_painel_features(
        dados=pd.DataFrame([reg_mov_202305]),
        cobertura=df_cobertura,
        ocupacoes=ocupacoes,
        competencias=["202306", "202401", "202402"],
    )

    def obter_admissoes_lag(painel, comp, lag_col):
        s = painel[
            (painel["destino"] == "analista_dados_bi")
            & (painel["uf"] == "35")
            & (painel["competencia"] == comp)
        ]
        assert len(s) == 1
        return s[lag_col].iloc[0]

    # Em 202306, lag 1 aponta para 202305 -> 1.0
    assert obter_admissoes_lag(painel_inicial, "202306", "admissoes_lag_1") == 1.0
    # Em 202402, lag 9 aponta para 202305 (deslocamento -9 meses)
    # 202402 - 9 meses = 202305. Como não havia exclusão ainda, enxerga 1.0
    assert obter_admissoes_lag(painel_inicial, "202402", "admissoes_sazonal_ano_anterior") == 1.0

    # 2. Adiciona:
    #   - EXC tardia: anula admissão de 202305, mas só publicada em 202402 (exc e arquivo 202402)
    #   - MOV futuro: admissão ocorrida em 202405
    reg_exc_tardia = {
        "competencia_mov": "202305",
        "competencia_dec": "202305",
        "competencia_exc": "202402",
        "competencia_arquivo": "202402",
        "arquivo_tipo": "EXC",
        "saldo_movimentacao": 1,
        "cbo2002_ocupacao": "211205",
        "uf": "35",
        "grau_instrucao": 9,
    }
    reg_mov_futuro = {
        "competencia_mov": "202405",
        "competencia_dec": "202405",
        "competencia_arquivo": "202405",
        "competencia_exc": None,
        "arquivo_tipo": "MOV",
        "saldo_movimentacao": 1,
        "cbo2002_ocupacao": "211205",
        "uf": "35",
        "grau_instrucao": 9,
    }

    painel_com_modificacoes = construir_painel_features(
        dados=pd.DataFrame([reg_mov_202305, reg_exc_tardia, reg_mov_futuro]),
        cobertura=df_cobertura,
        ocupacoes=ocupacoes,
        competencias=["202306", "202401", "202402", "202406"],
    )

    # Verificação 1: O passado em 202306 e 202401 NÃO MUDA! (Valores concretos iguais a 1.0)
    assert obter_admissoes_lag(painel_com_modificacoes, "202306", "admissoes_lag_1") == 1.0
    # Verificação 2: Em 202401, a exclusão ainda não é conhecida
    # Verificação 3: Em 202402, a exclusão de 202305 torna-se conhecida,
    # então admissoes_sazonal_ano_anterior (que inclui 202305) vira 0.0!
    assert (
        obter_admissoes_lag(painel_com_modificacoes, "202402", "admissoes_sazonal_ano_anterior")
        == 0.0
    )
    # Verificação 4: O MOV futuro de 202405 só é conhecido no futuro (202406 enxerga lag 1 = 1.0)
    assert obter_admissoes_lag(painel_com_modificacoes, "202406", "admissoes_lag_1") == 1.0


def test_cobertura_ausencia_nao_vira_zero_e_jan2020_legitimo():
    """T03 e Cobertura: ausência de fonte ou falha não vira zero (permanece NaN).

    - MOV falha/pendente -> NaN
    - Série coberta sem movimentação -> 0.0
    - Jan/2020 legitimamente sem FOR/EXC (ausente_na_fonte) é considerada coberta
    - Janelas incompletas permanecem NaN
    """
    ocupacoes = carregar_ocupacoes(CAMINHO_CATALOGO)

    cobertura_registros = [
        # Jan 2020: legitimamente apenas MOV (FOR/EXC ausente_na_fonte)
        {"competencia": "202001", "tipo": "MOV", "situacao": "ingerido"},
        {"competencia": "202001", "tipo": "FOR", "situacao": "ausente_na_fonte"},
        {"competencia": "202001", "tipo": "EXC", "situacao": "ausente_na_fonte"},
        # Fev 2020: coberto normal
        {"competencia": "202002", "tipo": "MOV", "situacao": "ingerido"},
        {"competencia": "202002", "tipo": "FOR", "situacao": "ingerido"},
        {"competencia": "202002", "tipo": "EXC", "situacao": "ingerido"},
        # Mar 2020: MOV pendente (NÃO coberto)
        {"competencia": "202003", "tipo": "MOV", "situacao": "pendente"},
        {"competencia": "202003", "tipo": "FOR", "situacao": "ingerido"},
        {"competencia": "202003", "tipo": "EXC", "situacao": "ingerido"},
    ]
    df_cobertura = pd.DataFrame(cobertura_registros)

    # Nenhum dado de movimentação fornecido
    df_dados = pd.DataFrame(
        columns=[
            "competencia_mov",
            "competencia_dec",
            "competencia_arquivo",
            "arquivo_tipo",
            "saldo_movimentacao",
            "cbo2002_ocupacao",
            "uf",
            "grau_instrucao",
        ]
    )

    painel = construir_painel_features(
        dados=df_dados,
        cobertura=df_cobertura,
        ocupacoes=ocupacoes,
        competencias=["202001", "202002", "202003"],
    )

    # 1. 202001 é coberto: série sem movimentação deve ser 0.0 (não NaN)
    s_202001 = painel[
        (painel["competencia"] == "202001")
        & (painel["destino"] == "analista_dados_bi")
        & (painel["uf"] == "35")
    ]
    assert s_202001["admissoes"].iloc[0] == 0.0
    # Mas janelas passadas incompletas (lag_1 de 202001 = 201912) NÃO existem -> NaN (não 0.0!)
    assert pd.isna(s_202001["admissoes_lag_1"].iloc[0])
    assert pd.isna(s_202001["admissoes_soma_3m"].iloc[0])

    # 2. 202003 tem MOV pendente: NÃO coberto -> valores devem ser NaN (NUNCA zero!)
    s_202003 = painel[
        (painel["competencia"] == "202003")
        & (painel["destino"] == "analista_dados_bi")
        & (painel["uf"] == "35")
    ]
    assert pd.isna(s_202003["admissoes"].iloc[0])
    assert pd.isna(s_202003["desligamentos"].iloc[0])


def test_rejeita_contagens_negativas_explicitamente():
    """Gera ValueError explícito em contagens negativas (não clipar silenciosamente)."""
    ocupacoes = carregar_ocupacoes(CAMINHO_CATALOGO)

    df_cobertura = pd.DataFrame([
        {"competencia": "202401", "tipo": "MOV", "situacao": "ingerido"},
        {"competencia": "202401", "tipo": "FOR", "situacao": "ingerido"},
        {"competencia": "202401", "tipo": "EXC", "situacao": "ingerido"},
    ])

    # 2 exclusões sem nenhuma admissão correspondente -> contagem de admissão ficaria -2
    df_dados = pd.DataFrame([
        {
            "competencia_mov": "202401",
            "competencia_dec": "202401",
            "competencia_exc": "202401",
            "competencia_arquivo": "202401",
            "arquivo_tipo": "EXC",
            "saldo_movimentacao": 1,
            "cbo2002_ocupacao": "211205",
            "uf": "35",
            "grau_instrucao": 9,
        },
        {
            "competencia_mov": "202401",
            "competencia_dec": "202401",
            "competencia_exc": "202401",
            "competencia_arquivo": "202401",
            "arquivo_tipo": "EXC",
            "saldo_movimentacao": 1,
            "cbo2002_ocupacao": "211205",
            "uf": "35",
            "grau_instrucao": 9,
        },
    ])

    with pytest.raises(ValueError, match="Contagem negativa inconsistente"):
        construir_painel_features(
            dados=df_dados,
            cobertura=df_cobertura,
            ocupacoes=ocupacoes,
            competencias=["202401"],
        )


def test_cbo_reserva_e_cbo_fora_sao_descartados():
    """CBOs na reserva ou fora do catálogo não devem aparecer em nenhum destino."""
    ocupacoes = carregar_ocupacoes(CAMINHO_CATALOGO)

    df_cobertura = pd.DataFrame([
        {"competencia": "202401", "tipo": "MOV", "situacao": "ingerido"},
        {"competencia": "202401", "tipo": "FOR", "situacao": "ingerido"},
        {"competencia": "202401", "tipo": "EXC", "situacao": "ingerido"},
    ])

    # 142315 está na cbo6_reserva (não em gerente_projetos_produto nem analista_dados_bi)
    # 999999 não existe em lugar nenhum
    df_dados = pd.DataFrame([
        {
            "competencia_mov": "202401",
            "competencia_dec": "202401",
            "competencia_arquivo": "202401",
            "arquivo_tipo": "MOV",
            "saldo_movimentacao": 1,
            "cbo2002_ocupacao": "142315",  # Reserva
            "uf": "35",
            "grau_instrucao": 9,
        },
        {
            "competencia_mov": "202401",
            "competencia_dec": "202401",
            "competencia_arquivo": "202401",
            "arquivo_tipo": "MOV",
            "saldo_movimentacao": 1,
            "cbo2002_ocupacao": "999999",  # Não catalogado
            "uf": "35",
            "grau_instrucao": 9,
        },
    ])

    painel = construir_painel_features(
        dados=df_dados,
        cobertura=df_cobertura,
        ocupacoes=ocupacoes,
        competencias=["202401"],
    )

    # Todas as séries em 202401 devem ter 0 admissões (os CBOs foram ignorados)
    assert (painel["admissoes"] == 0.0).all()


def test_campos_temporais_invalidos_geram_erro():
    """Validações de campos temporais não devem aceitar nulos, vazios ou formatos inválidos."""
    ocupacoes = carregar_ocupacoes(CAMINHO_CATALOGO)

    df_cobertura = pd.DataFrame([
        {"competencia": "202401", "tipo": "MOV", "situacao": "ingerido"}
    ])

    df_dados_invalido = pd.DataFrame([
        {
            "competencia_mov": "202413",  # Mês 13 inválido
            "competencia_dec": "202401",
            "competencia_arquivo": "202401",
            "arquivo_tipo": "MOV",
            "saldo_movimentacao": 1,
            "cbo2002_ocupacao": "211205",
            "uf": "35",
            "grau_instrucao": 9,
        }
    ])

    with pytest.raises(ValueError, match="Mês inválido"):
        construir_painel_features(
            dados=df_dados_invalido,
            cobertura=df_cobertura,
            ocupacoes=ocupacoes,
            competencias=["202401"],
        )


def test_duplicatas_legitimas_preservadas():
    """Não assumir unicidade de linhas para deduplicar registros legítimos idênticos."""
    ocupacoes = carregar_ocupacoes(CAMINHO_CATALOGO)

    df_cobertura = pd.DataFrame([
        {"competencia": "202401", "tipo": "MOV", "situacao": "ingerido"},
        {"competencia": "202401", "tipo": "FOR", "situacao": "ingerido"},
        {"competencia": "202401", "tipo": "EXC", "situacao": "ingerido"},
    ])

    reg_identico = {
        "competencia_mov": "202401",
        "competencia_dec": "202401",
        "competencia_arquivo": "202401",
        "arquivo_tipo": "MOV",
        "saldo_movimentacao": 1,
        "cbo2002_ocupacao": "211205",
        "uf": "35",
        "grau_instrucao": 9,
    }

    # Três registros idênticos para a mesma pessoa/ocupação/mês
    df_dados = pd.DataFrame([reg_identico, reg_identico, reg_identico])

    painel = construir_painel_features(
        dados=df_dados,
        cobertura=df_cobertura,
        ocupacoes=ocupacoes,
        competencias=["202401"],
    )

    s = painel[
        (painel["competencia"] == "202401")
        & (painel["destino"] == "analista_dados_bi")
        & (painel["uf"] == "35")
    ]
    # Devem ser exatamente 3 admissões, nunca deduplicadas para 1!
    assert s["admissoes"].iloc[0] == 3.0


def test_calculo_alvo_trimestral_manual_e_janela_incompleta():
    """Alvo y(g,t) = A(t+1) + A(t+2) + A(t+3) calculado manualmente.

    Se t+3 estiver ausente ou não coberto, o alvo vira NaN (não zero).
    """
    ocupacoes = carregar_ocupacoes(CAMINHO_CATALOGO)

    # Cobertura de 202401 até 202404
    cobertura_registros = []
    for m in ["202401", "202402", "202403", "202404"]:
        for t in ["MOV", "FOR", "EXC"]:
            cobertura_registros.append({"competencia": m, "tipo": t, "situacao": "ingerido"})
    df_cobertura = pd.DataFrame(cobertura_registros)

    # Admissões em t+1 (202402: 5), t+2 (202403: 7), t+3 (202404: 10)
    def criar_mov(comp, n):
        return [
            {
                "competencia_mov": comp,
                "competencia_dec": comp,
                "competencia_arquivo": comp,
                "arquivo_tipo": "MOV",
                "saldo_movimentacao": 1,
                "cbo2002_ocupacao": "211205",
                "uf": "35",
                "grau_instrucao": 9,
            }
            for _ in range(n)
        ]

    dados = criar_mov("202402", 5) + criar_mov("202403", 7) + criar_mov("202404", 10)
    df_dados = pd.DataFrame(dados)

    painel = construir_painel_features(
        dados=df_dados,
        cobertura=df_cobertura,
        ocupacoes=ocupacoes,
        competencias=["202401", "202402"],
    )

    s_202401 = painel[
        (painel["competencia"] == "202401")
        & (painel["destino"] == "analista_dados_bi")
        & (painel["uf"] == "35")
    ]
    # Alvo para 202401: A(202402) + A(202403) + A(202404) = 5 + 7 + 10 = 22.0
    assert s_202401["alvo"].iloc[0] == 22.0

    # Para 202402, t+3 seria 202405, que NÃO está coberto
    s_202402 = painel[
        (painel["competencia"] == "202402")
        & (painel["destino"] == "analista_dados_bi")
        & (painel["uf"] == "35")
    ]
    # Janela incompleta: alvo deve ser NaN, NUNCA preenchido com zero ou soma parcial
    assert pd.isna(s_202402["alvo"].iloc[0])


def test_serie_total_contexto_separa_superior_completo():
    """A série principal usa superior+; a série total abrange todos os graus."""
    ocupacoes = carregar_ocupacoes(CAMINHO_CATALOGO)

    df_cobertura = pd.DataFrame([
        {"competencia": "202401", "tipo": "MOV", "situacao": "ingerido"},
        {"competencia": "202401", "tipo": "FOR", "situacao": "ingerido"},
        {"competencia": "202401", "tipo": "EXC", "situacao": "ingerido"},
    ])

    # 1 admissão com superior (grau 9) e 2 admissões com ensino médio (grau 7)
    df_dados = pd.DataFrame([
        {
            "competencia_mov": "202401",
            "competencia_dec": "202401",
            "competencia_arquivo": "202401",
            "arquivo_tipo": "MOV",
            "saldo_movimentacao": 1,
            "cbo2002_ocupacao": "211205",
            "uf": "35",
            "grau_instrucao": 9,  # Superior completo
        },
        {
            "competencia_mov": "202401",
            "competencia_dec": "202401",
            "competencia_arquivo": "202401",
            "arquivo_tipo": "MOV",
            "saldo_movimentacao": 1,
            "cbo2002_ocupacao": "211205",
            "uf": "35",
            "grau_instrucao": 7,  # Médio completo (não entra na principal)
        },
        {
            "competencia_mov": "202401",
            "competencia_dec": "202401",
            "competencia_arquivo": "202401",
            "arquivo_tipo": "MOV",
            "saldo_movimentacao": 1,
            "cbo2002_ocupacao": "211205",
            "uf": "35",
            "grau_instrucao": 7,
        },
    ])

    painel = construir_painel_features(
        dados=df_dados,
        cobertura=df_cobertura,
        ocupacoes=ocupacoes,
        competencias=["202401"],
    )

    s = painel[
        (painel["competencia"] == "202401")
        & (painel["destino"] == "analista_dados_bi")
        & (painel["uf"] == "35")
    ]
    # Principal (superior+): 1
    assert s["admissoes"].iloc[0] == 1.0
    # Total (contexto): 1 + 2 = 3
    assert s["admissoes_total"].iloc[0] == 3.0


def test_todas_27_ufs_e_6_destinos_presentes_na_grade():
    """Cada competência coberta deve produzir exatamente 6 destinos x 27 UFs = 162 séries."""
    ocupacoes = carregar_ocupacoes(CAMINHO_CATALOGO)

    df_cobertura = pd.DataFrame([
        {"competencia": "202401", "tipo": "MOV", "situacao": "ingerido"},
        {"competencia": "202401", "tipo": "FOR", "situacao": "ingerido"},
        {"competencia": "202401", "tipo": "EXC", "situacao": "ingerido"},
    ])

    df_dados = pd.DataFrame(
        columns=[
            "competencia_mov",
            "competencia_dec",
            "competencia_arquivo",
            "arquivo_tipo",
            "saldo_movimentacao",
            "cbo2002_ocupacao",
            "uf",
            "grau_instrucao",
        ]
    )

    painel = construir_painel_features(
        dados=df_dados,
        cobertura=df_cobertura,
        ocupacoes=ocupacoes,
        competencias=["202401"],
    )

    assert len(painel) == 6 * 27
    assert set(painel["destino"].unique()) == {
        "analista_dados_bi",
        "analista_monitoramento_iot",
        "analista_processos",
        "gerente_projetos_produto",
        "analista_suporte_infra",
        "desenvolvedor_sistemas",
    }
    assert len(painel["uf"].unique()) == 27


def test_revisao_exc_pendente_produz_nan():
    """Revisão EXC pendente no intervalo m..t produz NaN para a contagem retrospectiva."""
    cobertura_dados = []
    for m in ["202401", "202402", "202403"]:
        for t in ["MOV", "FOR", "EXC"]:
            sit = "pendente" if (m == "202403" and t == "EXC") else "ingerido"
            cobertura_dados.append({"competencia": m, "tipo": t, "situacao": sit})
    c = pd.DataFrame(cobertura_dados)

    linha_sint = {
        "competencia_mov": "202401",
        "competencia_dec": "202401",
        "competencia_arquivo": "202401",
        "arquivo_tipo": "MOV",
        "saldo_movimentacao": 1,
        "cbo2002_ocupacao": "211205",
        "uf": "35",
        "grau_instrucao": 9,
    }

    painel = construir_painel_features(
        dados=pd.DataFrame([linha_sint]),
        cobertura=c,
        competencias=["202403"],
        ufs=["35"],
        calcular_alvo=False,
    )
    # Em 202403, lag 2 aponta para 202401. Como 202403 tem EXC pendente, lag 2 deve ser NaN
    s = painel[painel["destino"] == "analista_dados_bi"]
    assert pd.isna(s["admissoes_lag_2"].iloc[0])


def test_falha_futura_nao_contamina_origem_antiga():
    """Falha em competência futura (> t) não contamina a origem passada (<= t)."""
    cobertura_dados = []
    for m in ["202401", "202402", "202403", "202404"]:
        for t in ["MOV", "FOR", "EXC"]:
            # Falha drástica no futuro em 202404
            sit = "falha" if m == "202404" else "ingerido"
            cobertura_dados.append({"competencia": m, "tipo": t, "situacao": sit})
    c = pd.DataFrame(cobertura_dados)

    linha_sint = {
        "competencia_mov": "202401",
        "competencia_dec": "202401",
        "competencia_arquivo": "202401",
        "arquivo_tipo": "MOV",
        "saldo_movimentacao": 1,
        "cbo2002_ocupacao": "211205",
        "uf": "35",
        "grau_instrucao": 9,
    }

    painel = construir_painel_features(
        dados=pd.DataFrame([linha_sint]),
        cobertura=c,
        competencias=["202401"],
        ufs=["35"],
        calcular_alvo=False,
    )
    s = painel[painel["destino"] == "analista_dados_bi"]
    # Em 202401, a observação está 100% íntegra (falha futura em 202404 não afeta t=202401)
    assert s["admissoes"].iloc[0] == 1.0


def test_cobertura_duplicada_conflitante_gera_erro():
    """Duplicação com status conflitante no manifesto de cobertura gera ValueError."""
    c = pd.DataFrame([
        {"competencia": "202401", "tipo": "MOV", "situacao": "ingerido"},
        {"competencia": "202401", "tipo": "MOV", "situacao": "falha"},  # Conflito!
        {"competencia": "202401", "tipo": "FOR", "situacao": "ingerido"},
        {"competencia": "202401", "tipo": "EXC", "situacao": "ingerido"},
    ])
    with pytest.raises(ValueError, match="Conflito de situações de cobertura"):
        construir_painel_features(
            dados=pd.DataFrame(),
            cobertura=c,
            competencias=["202401"],
            ufs=["35"],
        )


def test_catalogo_reserva_sobrepondo_destino_gera_erro():
    """Reserva CBO6 que sobrepõe ocupação de destino gera ValueError."""
    catalogo = {
        "destinos": {"analista_dados_bi": {"cbo6": ["211205"]}},
        "cbo6_reserva": ["211205"],  # Sobreposição proibida
    }
    c = pd.DataFrame([
        {"competencia": "202401", "tipo": "MOV", "situacao": "ingerido"},
        {"competencia": "202401", "tipo": "FOR", "situacao": "ingerido"},
        {"competencia": "202401", "tipo": "EXC", "situacao": "ingerido"},
    ])
    with pytest.raises(ValueError, match="sobrepõe o destino"):
        construir_painel_features(
            dados=pd.DataFrame(),
            cobertura=c,
            ocupacoes=catalogo,
            competencias=["202401"],
            ufs=["35"],
        )


def test_equivalencia_bruto_vs_pre_agregado():
    """Valida que pré-agregar chunks e construir painel produz resultado idêntico a dados brutos."""
    from citizentech_ml.features import (
        concatenar_pre_agregados,
        pre_agregar_microdados,
    )

    c = pd.DataFrame([
        {"competencia": m, "tipo": t, "situacao": "ingerido"}
        for m in ["202401", "202402", "202403"]
        for t in ["MOV", "FOR", "EXC"]
    ])

    linhas_chunk1 = [
        {
            "competencia_mov": "202401",
            "competencia_dec": "202401",
            "competencia_arquivo": "202401",
            "arquivo_tipo": "MOV",
            "saldo_movimentacao": 1,
            "cbo2002_ocupacao": "211205",
            "uf": "35",
            "grau_instrucao": 9,
        },
        {
            "competencia_mov": "202401",
            "competencia_dec": "202401",
            "competencia_arquivo": "202401",
            "arquivo_tipo": "MOV",
            "saldo_movimentacao": -1,
            "cbo2002_ocupacao": "211205",
            "uf": "35",
            "grau_instrucao": 9,
        },
    ]

    linhas_chunk2 = [
        {
            "competencia_mov": "202402",
            "competencia_dec": "202402",
            "competencia_arquivo": "202402",
            "arquivo_tipo": "MOV",
            "saldo_movimentacao": 1,
            "cbo2002_ocupacao": "211205",
            "uf": "35",
            "grau_instrucao": 9,
        },
    ]

    df_bruto = pd.DataFrame(linhas_chunk1 + linhas_chunk2)

    # 1. Painel gerado diretamente a partir dos dados brutos
    painel_bruto = construir_painel_features(
        dados=df_bruto,
        cobertura=c,
        competencias=["202402"],
        ufs=["35"],
        calcular_alvo=False,
    )

    # 2. Painel gerado a partir de chunks pré-agregados
    pre1 = pre_agregar_microdados(pd.DataFrame(linhas_chunk1))
    pre2 = pre_agregar_microdados(pd.DataFrame(linhas_chunk2))
    pre_consolidado = concatenar_pre_agregados([pre1, pre2])

    painel_pre = construir_painel_features(
        dados=pre_consolidado,
        cobertura=c,
        competencias=["202402"],
        ufs=["35"],
        calcular_alvo=False,
    )

    pd.testing.assert_frame_equal(painel_bruto, painel_pre)


def test_bloqueio_origens_teste_por_padrao():
    """Competências de teste (>= 202601) são bloqueadas por padrão para proteger o holdout."""
    c = pd.DataFrame([
        {"competencia": "202601", "tipo": "MOV", "situacao": "ingerido"},
        {"competencia": "202601", "tipo": "FOR", "situacao": "ingerido"},
        {"competencia": "202601", "tipo": "EXC", "situacao": "ingerido"},
    ])
    # Sem permitir_teste=True deve levantar ValueError
    with pytest.raises(ValueError, match="Competência de teste '202601' bloqueada por padrão"):
        construir_painel_features(
            dados=pd.DataFrame(),
            cobertura=c,
            competencias=["202601"],
            ufs=["35"],
            permitir_teste=False,
        )

    # Com permitir_teste=True é permitido para testes sintéticos
    painel_sint = construir_painel_features(
        dados=pd.DataFrame(),
        cobertura=c,
        competencias=["202601"],
        ufs=["35"],
        calcular_alvo=False,
        permitir_teste=True,
    )
    assert not painel_sint.empty
    assert (painel_sint["competencia"] == "202601").all()



