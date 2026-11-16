"""Testes unitários e de integração para base municipal e leitor seguro."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from citizentech_ml.estatistica.base_municipal import (
    carregar_base_municipal,
    planejar_fontes_municipais,
)

MAPA_MINIMO = {
    "destinos": {
        "analista_dados_bi": {"cbo6": ["211205"]},
        "analista_monitoramento_iot": {"cbo6": ["211210"]},
        "analista_processos": {"cbo6": ["212405"]},
        "gerente_projetos_produto": {"cbo6": ["142105"]},
        "analista_suporte_infra": {"cbo6": ["212420"]},
        "desenvolvedor_sistemas": {"cbo6": ["212410"]},
    }
}


def _criar_72_fontes_dummy(diretorio: Path, incluir_2026: bool = True) -> list[Path]:
    """Cria arquivos dummy para os 72 meses/tipos canônicos e sentinela 2026."""
    caminhos = []
    meses = [f"{ano}{mes:02d}" for ano in (2024, 2025) for mes in range(1, 13)]
    tipos = ["MOV", "FOR", "EXC"]
    for comp in meses:
        for tipo in tipos:
            p = diretorio / f"CAGED{tipo}{comp}.parquet"
            p.write_bytes(b"DUMMY_PARQUET")
            caminhos.append(p)

    if incluir_2026:
        sentinela = diretorio / "CAGEDMOV202601.parquet"
        sentinela.write_bytes(b"PROIBIDO_2026")
        sentinela_extra = diretorio / "CAGEDFOR202602.parquet"
        sentinela_extra.write_bytes(b"PROIBIDO_2026")

    return caminhos


def test_tracerbullet_planejador_e_leitor_seguro_ignoram_2026(tmp_path: Path):
    """Tracer bullet: 72 fontes canônicas com sentinela 2026 nunca tocado."""
    fontes_esperadas = _criar_72_fontes_dummy(tmp_path, incluir_2026=True)

    # 1. Planejador deve retornar exatamente 72 caminhos e ignorar arquivos 2026
    planejados = planejar_fontes_municipais(tmp_path)
    assert len(planejados) == 72
    assert all("2026" not in p.name for p in planejados)
    assert [p.name for p in planejados] == [p.name for p in fontes_esperadas]

    # 2. Leitor spy: se qualquer arquivo 2026 for tocado, explode imediatamente
    chamadas: list[Path] = []

    def leitor_spy(caminho: Path) -> pd.DataFrame:
        if "2026" in caminho.name:
            raise RuntimeError(f"VIOLAÇÃO CRÍTICA: Arquivo 2026 tocado pelo leitor: {caminho}")
        chamadas.append(caminho)
        # Retorna DataFrame vazio compatível
        return pd.DataFrame(
            columns=[
                "municipio",
                "uf",
                "cbo2002_ocupacao",
                "saldo_movimentacao",
                "grau_instrucao",
                "salario",
                "arquivo_tipo",
                "competencia_mov",
                "competencia_dec",
                "competencia_exc",
                "competencia_arquivo",
            ]
        )

    base, relatorio = carregar_base_municipal(tmp_path, MAPA_MINIMO, leitor=leitor_spy)
    assert len(chamadas) == 72
    assert all("2026" not in p.name for p in chamadas)
    assert isinstance(base, pd.DataFrame)
    assert isinstance(relatorio, dict)


def test_planejador_falta_de_arquivo_gera_erro_de_cobertura(tmp_path: Path):
    """Falta de qualquer um dos 72 arquivos esperados gera erro claro de cobertura."""
    fontes = _criar_72_fontes_dummy(tmp_path, incluir_2026=False)
    # Remove um arquivo (ex: CAGEDEXC202512.parquet)
    fontes[-1].unlink()

    with pytest.raises((FileNotFoundError, ValueError), match="cobertura|ausente"):
        planejar_fontes_municipais(tmp_path)


def test_validar_mapa_destinos_exige_seis_disjuntos():
    """Validação estrita do mapa: 6 destinos obrigatórios e disjuntos."""
    from citizentech_ml.estatistica.base_municipal import validar_mapa_destinos

    # Mapa válido
    mapa_cbo = validar_mapa_destinos(MAPA_MINIMO)
    assert len(mapa_cbo) == 6
    assert mapa_cbo["211205"] == "analista_dados_bi"

    # Faltando um dos seis destinos
    incompleto = {
        "destinos": {
            k: v for k, v in MAPA_MINIMO["destinos"].items() if k != "desenvolvedor_sistemas"
        }
    }
    with pytest.raises(ValueError, match="exatamente 6 destinos|desenvolvedor_sistemas"):
        validar_mapa_destinos(incompleto)

    # CBO repetido entre destinos diferentes
    sobreposto = {
        "destinos": {
            **MAPA_MINIMO["destinos"],
            "desenvolvedor_sistemas": {"cbo6": ["211205"]},  # mesmo do analista_dados_bi
        }
    }
    with pytest.raises(ValueError, match="múltiplos|sobrep|disjunt"):
        validar_mapa_destinos(sobreposto)


def test_dois_municipios_seis_destinos_mov_for_exc_e_salario_ponderado():
    """Fixture com 2 municípios, 6 destinos, MOV+FOR-EXC, linhas idênticas e médias."""
    from citizentech_ml.estatistica.base_municipal import agregar_base_municipal

    cbos = ["211205", "211210", "212405", "142105", "212420", "212410"]

    linhas = []

    # Município 1: 355030 (SP capital)
    # 2024: 12 admissões legítimas (2 por destino), incluindo 2 linhas idênticas
    for cbo in cbos:
        linhas.append({
            "municipio": "355030", "uf": "35", "cbo2002_ocupacao": cbo,
            "saldo_movimentacao": 1, "grau_instrucao": 9, "salario": 5000.0,
            "arquivo_tipo": "MOV", "competencia_mov": "202401", "competencia_dec": "202401",
            "competencia_exc": None, "competencia_arquivo": "202401",
        })
        linhas.append({
            "municipio": "355030", "uf": "35", "cbo2002_ocupacao": cbo,
            "saldo_movimentacao": 1, "grau_instrucao": 9, "salario": 5000.0,
            "arquivo_tipo": "MOV", "competencia_mov": "202401", "competencia_dec": "202401",
            "competencia_exc": None, "competencia_arquivo": "202401",
        })

    # Adiciona 1 FOR de admissão (salário 8000) e 1 EXC cancelando-o exatamente
    linhas.append({
        "municipio": "355030", "uf": "35", "cbo2002_ocupacao": "211205",
        "saldo_movimentacao": 1, "grau_instrucao": 80, "salario": 8000.0,
        "arquivo_tipo": "FOR", "competencia_mov": "202402", "competencia_dec": "202403",
        "competencia_exc": None, "competencia_arquivo": "202403",
    })
    linhas.append({
        "municipio": "355030", "uf": "35", "cbo2002_ocupacao": "211205",
        "saldo_movimentacao": 1, "grau_instrucao": 80, "salario": 8000.0,
        "arquivo_tipo": "EXC", "competencia_mov": "202402", "competencia_dec": "202404",
        "competencia_exc": "202404", "competencia_arquivo": "202404",
    })

    # 1 desligamento legítimo em 2024
    linhas.append({
        "municipio": "355030", "uf": "35", "cbo2002_ocupacao": "211205",
        "saldo_movimentacao": -1, "grau_instrucao": 9, "salario": 5000.0,
        "arquivo_tipo": "MOV", "competencia_mov": "202405", "competencia_dec": "202405",
        "competencia_exc": None, "competencia_arquivo": "202405",
    })

    # 2025 para 355030: 15 admissões (crescimento positivo: 15 > 12)
    for _ in range(15):
        linhas.append({
            "municipio": "355030", "uf": "35", "cbo2002_ocupacao": "212410",
            "saldo_movimentacao": 1, "grau_instrucao": 10, "salario": 6000.0,
            "arquivo_tipo": "MOV", "competencia_mov": "202506", "competencia_dec": "202506",
            "competencia_exc": None, "competencia_arquivo": "202506",
        })

    # Município 2: 350950 (Campinas) - 10 admissões em 2024, 0 em 2025 (zero estrutural)
    for _ in range(10):
        linhas.append({
            "municipio": "350950", "uf": "35", "cbo2002_ocupacao": "211205",
            "saldo_movimentacao": 1, "grau_instrucao": 7, "salario": 4000.0,
            "arquivo_tipo": "MOV", "competencia_mov": "202407", "competencia_dec": "202407",
            "competencia_exc": None, "competencia_arquivo": "202407",
        })

    # Município 3: 351000 - 9 admissões em 2024 (<10) -> excluído da população
    for _ in range(9):
        linhas.append({
            "municipio": "351000", "uf": "35", "cbo2002_ocupacao": "211205",
            "saldo_movimentacao": 1, "grau_instrucao": 9, "salario": 3000.0,
            "arquivo_tipo": "MOV", "competencia_mov": "202401", "competencia_dec": "202401",
            "competencia_exc": None, "competencia_arquivo": "202401",
        })
    for _ in range(30):
        linhas.append({
            "municipio": "351000", "uf": "35", "cbo2002_ocupacao": "211205",
            "saldo_movimentacao": 1, "grau_instrucao": 9, "salario": 3000.0,
            "arquivo_tipo": "MOV", "competencia_mov": "202501", "competencia_dec": "202501",
            "competencia_exc": None, "competencia_arquivo": "202501",
        })

    df_micro = pd.DataFrame(linhas)
    base, rel = agregar_base_municipal(df_micro, MAPA_MINIMO)

    # 1. Município 351000 deve ser excluído (< 10 em 2024)
    assert "351000" not in base["municipio"].tolist()
    assert rel["n_populacao_final"] == 2
    assert rel["n_excluidos_menos_10"] == 1

    # 2. Ordem estável por município
    assert base["municipio"].tolist() == ["350950", "355030"]

    # 3. Métricas de 355030
    sp_row = base.loc[base["municipio"] == "355030"].iloc[0]
    assert sp_row["admissoes_2024"] == 12
    assert sp_row["desligamentos_2024"] == 1
    assert sp_row["admissoes_2025"] == 15
    assert sp_row["salario_medio_2024"] == pytest.approx(5000.0)
    assert sp_row["salario_medio_2025"] == pytest.approx(6000.0)
    assert sp_row["percentual_superior_2024"] == pytest.approx(100.0)
    assert sp_row["crescimento"] == 1
    assert sp_row["crescimento_percentual"] == pytest.approx(100.0 * (15 / 12 - 1.0))

    # 4. Métricas de 350950 (Campinas) - Zero estrutural em 2025
    camp_row = base.loc[base["municipio"] == "350950"].iloc[0]
    assert camp_row["admissoes_2024"] == 10
    assert camp_row["admissoes_2025"] == 0
    assert camp_row["desligamentos_2025"] == 0
    assert pd.isna(camp_row["salario_medio_2025"])
    assert pd.isna(camp_row["percentual_superior_2025"])
    assert camp_row["percentual_superior_2024"] == pytest.approx(0.0)
    assert camp_row["crescimento"] == 0
    assert camp_row["crescimento_percentual"] == pytest.approx(-100.0)


def test_for_exc_2025_com_movimento_2024_nao_altera_2024():
    """Declaração/disponibilidade em 2025 de movimento de 2024 é ignorada pelo snapshot 2024."""
    from citizentech_ml.estatistica.base_municipal import agregar_base_municipal

    # 10 admissões em 2024 (disponíveis em 202401)
    linhas = [
        {
            "municipio": "355030", "uf": "35", "cbo2002_ocupacao": "211205",
            "saldo_movimentacao": 1, "grau_instrucao": 9, "salario": 4000.0,
            "arquivo_tipo": "MOV", "competencia_mov": "202401", "competencia_dec": "202401",
            "competencia_exc": None, "competencia_arquivo": "202401",
        }
        for _ in range(10)
    ]
    # Revisão em 2025 (disponibilidade 202503) de um movimento de 202401
    linhas.append({
        "municipio": "355030", "uf": "35", "cbo2002_ocupacao": "211205",
        "saldo_movimentacao": 1, "grau_instrucao": 9, "salario": 9999.0,
        "arquivo_tipo": "FOR", "competencia_mov": "202401", "competencia_dec": "202503",
        "competencia_exc": None, "competencia_arquivo": "202503",
    })

    df = pd.DataFrame(linhas)
    base, rel = agregar_base_municipal(df, MAPA_MINIMO)
    row = base.iloc[0]
    assert row["admissoes_2024"] == 10
    assert row["salario_medio_2024"] == pytest.approx(4000.0)
    assert rel["contadores"]["linhas_ignoradas_disponibilidade_snapshot"] == 1


def test_superior_graus_e_desconhecidos_a_parte():
    """Superior inclui 9, 10, 11, 80; 99 e nulos contados à parte; códigos estranhos falham."""
    from citizentech_ml.estatistica.base_municipal import agregar_base_municipal

    # 10 admissões em 2024 com graus variados:
    # 4 superior: 9, 10, 11, 80
    # 3 não-superior conhecidos: 1, 6, 8
    # 3 desconhecidos: 99, None, np.nan
    graus = [9, 10, 11, 80, 1, 6, 8, 99, None, np.nan]
    linhas = [
        {
            "municipio": "355030", "uf": "35", "cbo2002_ocupacao": "211205",
            "saldo_movimentacao": 1, "grau_instrucao": g, "salario": 3000.0,
            "arquivo_tipo": "MOV", "competencia_mov": "202401", "competencia_dec": "202401",
            "competencia_exc": None, "competencia_arquivo": "202401",
        }
        for g in graus
    ]

    base, _ = agregar_base_municipal(pd.DataFrame(linhas), MAPA_MINIMO)
    row = base.iloc[0]
    assert row["admissoes_2024"] == 10
    assert row["admissoes_superior_2024"] == 4
    assert row["escolaridade_desconhecida_2024"] == 3
    # Denominador do % superior é o total (todas escolaridades: 10)
    assert row["percentual_superior_2024"] == pytest.approx(40.0)

    # Grau inválido: código 12 (não previsto)
    linhas_inv = [linhas[0].copy() | {"grau_instrucao": 12}]
    with pytest.raises(ValueError, match="não previsto"):
        agregar_base_municipal(pd.DataFrame(linhas_inv), MAPA_MINIMO)

    # Grau booleano inválido
    linhas_bool = [linhas[0].copy() | {"grau_instrucao": True}]
    with pytest.raises((TypeError, ValueError), match="booleano"):
        agregar_base_municipal(pd.DataFrame(linhas_bool), MAPA_MINIMO)


def test_nan_salarial_mantem_admissao_e_outliers_preservados():
    """Valores inválidos de salário mantêm admissões; outliers válidos são preservados."""
    from citizentech_ml.estatistica.base_municipal import agregar_base_municipal

    linhas = []
    # 9 admissões com salário 5000
    for _ in range(9):
        linhas.append({
            "municipio": "355030", "uf": "35", "cbo2002_ocupacao": "211205",
            "saldo_movimentacao": 1, "grau_instrucao": 9, "salario": 5000.0,
            "arquivo_tipo": "MOV", "competencia_mov": "202401", "competencia_dec": "202401",
            "competencia_exc": None, "competencia_arquivo": "202401",
        })
    # 1 admissão com salário NaN (inválido)
    linhas.append({
        "municipio": "355030", "uf": "35", "cbo2002_ocupacao": "211205",
        "saldo_movimentacao": 1, "grau_instrucao": 9, "salario": np.nan,
        "arquivo_tipo": "MOV", "competencia_mov": "202401", "competencia_dec": "202401",
        "competencia_exc": None, "competencia_arquivo": "202401",
    })
    # 1 admissão com salário <= 0 (inválido)
    linhas.append({
        "municipio": "355030", "uf": "35", "cbo2002_ocupacao": "211205",
        "saldo_movimentacao": 1, "grau_instrucao": 9, "salario": 0.0,
        "arquivo_tipo": "MOV", "competencia_mov": "202401", "competencia_dec": "202401",
        "competencia_exc": None, "competencia_arquivo": "202401",
    })
    # 1 admissão com salário outlier de 150.000 (válido, não deve ser cortado)
    linhas.append({
        "municipio": "355030", "uf": "35", "cbo2002_ocupacao": "211205",
        "saldo_movimentacao": 1, "grau_instrucao": 9, "salario": 150000.0,
        "arquivo_tipo": "MOV", "competencia_mov": "202401", "competencia_dec": "202401",
        "competencia_exc": None, "competencia_arquivo": "202401",
    })

    base, _ = agregar_base_municipal(pd.DataFrame(linhas), MAPA_MINIMO)
    row = base.iloc[0]
    # Total de admissões: 9 + 1 + 1 + 1 = 12
    assert row["admissoes_2024"] == 12
    assert row["n_salarios_validos_2024"] == 10
    assert row["n_salarios_invalidos_2024"] == 2
    # Média com outlier preservado: (9*5000 + 150000) / 10 = 195000 / 10 = 19500.0
    assert row["salario_medio_2024"] == pytest.approx(19500.0)


def test_contagem_negativa_ou_subgrupo_acima_do_total_rejeitado():
    """Validações de consistência: sem clip, erro claro em contagem negativa ou subgrupo > total."""
    from citizentech_ml.estatistica.base_municipal import agregar_base_municipal

    # EXC maior que MOV produz contagem negativa de admissões
    linhas = [
        {
            "municipio": "355030", "uf": "35", "cbo2002_ocupacao": "211205",
            "saldo_movimentacao": 1, "grau_instrucao": 9, "salario": 3000.0,
            "arquivo_tipo": "MOV", "competencia_mov": "202401", "competencia_dec": "202401",
            "competencia_exc": None, "competencia_arquivo": "202401",
        },
        {
            "municipio": "355030", "uf": "35", "cbo2002_ocupacao": "211205",
            "saldo_movimentacao": 1, "grau_instrucao": 9, "salario": 3000.0,
            "arquivo_tipo": "EXC", "competencia_mov": "202401", "competencia_dec": "202401",
            "competencia_exc": "202401", "competencia_arquivo": "202401",
        },
        {
            "municipio": "355030", "uf": "35", "cbo2002_ocupacao": "211205",
            "saldo_movimentacao": 1, "grau_instrucao": 9, "salario": 3000.0,
            "arquivo_tipo": "EXC", "competencia_mov": "202401", "competencia_dec": "202401",
            "competencia_exc": "202401", "competencia_arquivo": "202401",
        },
    ]
    with pytest.raises(ValueError, match="[Cc]ontagem negativa"):
        agregar_base_municipal(pd.DataFrame(linhas), MAPA_MINIMO)


def test_microdados_input_inalterado():
    """Verifica pureza da função: DataFrame de entrada não é modificado in-place."""
    from citizentech_ml.estatistica.base_municipal import agregar_base_municipal

    df = pd.DataFrame([
        {
            "municipio": "355030", "uf": "35", "cbo2002_ocupacao": "211205",
            "saldo_movimentacao": 1, "grau_instrucao": 9, "salario": 5000.0,
            "arquivo_tipo": "MOV", "competencia_mov": "202401", "competencia_dec": "202401",
            "competencia_exc": None, "competencia_arquivo": "202401",
        }
        for _ in range(10)
    ])
    df_clone = df.copy(deep=True)
    _, _ = agregar_base_municipal(df, MAPA_MINIMO)
    pd.testing.assert_frame_equal(df, df_clone)


def test_competencia_2026_rejeitada_no_microdado():
    """Declaração/arquivo/movimento 2026 não é autorizado a entrar no input."""
    from citizentech_ml.estatistica.base_municipal import agregar_base_municipal

    linha_2026 = {
        "municipio": "355030", "uf": "35", "cbo2002_ocupacao": "211205",
        "saldo_movimentacao": 1, "grau_instrucao": 9, "salario": 5000.0,
        "arquivo_tipo": "MOV", "competencia_mov": "202601", "competencia_dec": "202601",
        "competencia_exc": None, "competencia_arquivo": "202601",
    }
    with pytest.raises(ValueError, match="2026 não autorizado"):
        agregar_base_municipal(pd.DataFrame([linha_2026]), MAPA_MINIMO)


def test_municipio_sp_invalido_rejeitado():
    """Município em SP deve ser código de 6 dígitos numéricos com prefixo 35."""
    from citizentech_ml.estatistica.base_municipal import agregar_base_municipal

    # Código com 7 dígitos (ex: IBGE 7)
    linha_ibge7 = {
        "municipio": "3550308", "uf": "35", "cbo2002_ocupacao": "211205",
        "saldo_movimentacao": 1, "grau_instrucao": 9, "salario": 5000.0,
        "arquivo_tipo": "MOV", "competencia_mov": "202401", "competencia_dec": "202401",
        "competencia_exc": None, "competencia_arquivo": "202401",
    }
    with pytest.raises(ValueError, match="prefixo 35"):
        agregar_base_municipal(pd.DataFrame([linha_ibge7]), MAPA_MINIMO)

    # Código sem prefixo 35
    linha_outro_prefixo = linha_ibge7.copy()
    linha_outro_prefixo["municipio"] = "330455"
    with pytest.raises(ValueError, match="prefixo 35"):
        agregar_base_municipal(pd.DataFrame([linha_outro_prefixo]), MAPA_MINIMO)


def test_integracao_parquet_real_72_fontes_e_hashes(tmp_path: Path):
    """Integração fim a fim com 72 arquivos Parquet reais gravados em disco."""
    from citizentech_ml.estatistica.base_municipal import (
        COLUNAS_MINIMAS,
        MESES_CANONICOS,
        TIPOS_CANONICOS,
        carregar_base_municipal,
    )

    # 1. Cria os 72 arquivos Parquet reais
    for comp in MESES_CANONICOS:
        for tipo in TIPOS_CANONICOS:
            linhas = []
            # No primeiro mês de 2024 (202401 MOV), coloca 10 admissões para 355030
            if comp == "202401" and tipo == "MOV":
                for _ in range(10):
                    linhas.append({
                        "municipio": "355030", "uf": "35", "cbo2002_ocupacao": "211205",
                        "saldo_movimentacao": 1, "grau_instrucao": 9, "salario": 5000.0,
                        "arquivo_tipo": "MOV", "competencia_mov": "202401",
                        "competencia_dec": "202401", "competencia_exc": None,
                        "competencia_arquivo": "202401",
                    })
            # No primeiro mês de 2025 (202501 MOV), coloca 12 admissões para 355030
            elif comp == "202501" and tipo == "MOV":
                for _ in range(12):
                    linhas.append({
                        "municipio": "355030", "uf": "35", "cbo2002_ocupacao": "211205",
                        "saldo_movimentacao": 1, "grau_instrucao": 9, "salario": 5500.0,
                        "arquivo_tipo": "MOV", "competencia_mov": "202501",
                        "competencia_dec": "202501", "competencia_exc": None,
                        "competencia_arquivo": "202501",
                    })

            df_arq = pd.DataFrame(linhas, columns=COLUNAS_MINIMAS)
            p = tmp_path / f"CAGED{tipo}{comp}.parquet"
            df_arq.to_parquet(p, index=False)

    # Sentinela 2026 no diretório (não deve ser tocado nem listado)
    (tmp_path / "CAGEDMOV202601.parquet").write_bytes(b"SENTINELA_2026")

    base, relatorio = carregar_base_municipal(tmp_path, MAPA_MINIMO)

    assert len(base) == 1
    row = base.iloc[0]
    assert row["municipio"] == "355030"
    assert row["admissoes_2024"] == 10
    assert row["admissoes_2025"] == 12
    assert row["salario_medio_2024"] == pytest.approx(5000.0)
    assert row["salario_medio_2025"] == pytest.approx(5500.0)
    assert row["crescimento"] == 1
    assert row["crescimento_percentual"] == pytest.approx(20.0)

    # Verifica hashes e procedência
    assert len(relatorio["hashes_fontes"]) == 72
    assert all("2026" not in f for f in relatorio["hashes_fontes"])
    assert all(len(h) == 64 for h in relatorio["hashes_fontes"].values())
    assert relatorio["timestamp_utc"].endswith("Z")
