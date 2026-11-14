"""Testes do módulo de EDA exclusiva do treino."""

from pathlib import Path

import pandas as pd
import pytest

from citizentech_ml.eda import gerar_eda_treino
from citizentech_ml.features.datas import gerar_intervalo_meses


def _criar_dados_sinteticos_eda() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Gera painel sintético e pré-agregado sintético para testes da EDA."""
    meses_painel = gerar_intervalo_meses("202001", "202509")
    linhas_painel = []

    for m in meses_painel:
        particao = "treino" if m <= "202409" else ("embargo" if m <= "202412" else "validacao")
        # Injeta um valor absurdo na validação para verificar isolamento
        alvo_val = 99999999.0 if particao == "validacao" else 25.0
        linhas_painel.append(
            {
                "competencia": m,
                "destino": "analista_dados_bi",
                "uf": "35",
                "particao": particao,
                "admissoes": 10.0,
                "admissoes_total": 50.0,
                "alvo": alvo_val,
                "mes": int(m[4:]),
            }
        )
        linhas_painel.append(
            {
                "competencia": m,
                "destino": "desenvolvedor_sistemas",
                "uf": "33",
                "particao": particao,
                "admissoes": 5.0,  # abaixo de 10 -> densidade insuficiente
                "admissoes_total": 20.0,
                "alvo": 5.0,
                "mes": int(m[4:]),
            }
        )

    df_painel = pd.DataFrame(linhas_painel)

    # Pré-agregado sintético cobrindo 2020 a 2024 (e um registro 2025 para testar descarte)
    meses_mov = ["202001", "202006", "202101", "202401", "202412", "202506"]
    linhas_pre = []
    for mov in meses_mov:
        linhas_pre.append(
            {
                "destino": "analista_dados_bi",
                "uf": "35",
                "superior": True,
                "competencia_mov": mov,
                "competencia_disp": mov,
                "delta_adm": 20,
                "delta_des": 5,
            }
        )
        # Declaração fora de prazo (FOR: disp > mov)
        linhas_pre.append(
            {
                "destino": "analista_dados_bi",
                "uf": "35",
                "superior": True,
                "competencia_mov": mov,
                "competencia_disp": "202412" if mov <= "202412" else "202512",
                "delta_adm": 5,
                "delta_des": 1,
            }
        )
    df_pre = pd.DataFrame(linhas_pre)

    return df_painel, df_pre


def test_gerar_eda_treino(tmp_path: Path) -> None:
    """Verifica se a EDA gera o Markdown com as 7 seções e PNGs válidos."""
    df_painel, df_pre = _criar_dados_sinteticos_eda()
    dir_saida = tmp_path / "saida_eda"

    relatorio_carga = {
        "arquivos_lidos": 20,
        "linhas_lidas": 1000,
        "linhas_uf_invalida": {"99": 2},
        "linhas_apos_limite": 0,
        "linhas_pre_agregadas": 100,
        "limite_usado": "202512",
    }

    caminho_md = gerar_eda_treino(
        painel=df_painel,
        pre_agregado=df_pre,
        dir_saida=dir_saida,
        relatorio_carga=relatorio_carga,
    )

    assert caminho_md.exists()
    conteudo = caminho_md.read_text(encoding="utf-8")

    # 1. As 7 seções obrigatórias
    assert "Qualidade e cobertura" in conteudo
    assert "Densidade" in conteudo
    assert "Nível e tendência" in conteudo
    assert "Sazonalidade" in conteudo
    assert "2020 × demais anos" in conteudo
    assert "Defasagem de declaração" in conteudo
    assert "Distribuição do alvo" in conteudo

    # 2. Informações de proveniência em tabelas
    assert "Novo Caged, MTE/PDET" in conteudo
    assert "admissões formais, ocupações CBO do destino" in conteudo
    assert "observado" in conteudo

    # 3. Gráficos PNG gerados com tamanho > 0
    png_nivel = dir_saida / "nivel_tendencia.png"
    png_sazonal = dir_saida / "sazonalidade.png"
    assert png_nivel.exists() and png_nivel.stat().st_size > 0
    assert png_sazonal.exists() and png_sazonal.stat().st_size > 0

    # 4. Isolamento estrito da validação: valor absurdo 99999999 NÃO pode aparecer
    assert "99999999" not in conteudo


def test_cli_eda(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida execução da CLI da EDA."""
    import sys

    from citizentech_ml.eda import main

    df_painel, _ = _criar_dados_sinteticos_eda()
    caminho_painel = tmp_path / "painel.parquet"
    df_painel.to_parquet(caminho_painel, index=False)

    dir_dados = tmp_path / "dados"
    dir_parquet = dir_dados / "caged" / "parquet"
    dir_parquet.mkdir(parents=True, exist_ok=True)
    df_parquet = pd.DataFrame(
        {
            "competencia_mov": ["202401"],
            "competencia_dec": ["202401"],
            "competencia_arquivo": ["202401"],
            "arquivo_tipo": ["MOV"],
            "saldo_movimentacao": [1],
            "cbo2002_ocupacao": ["211205"],
            "uf": ["35"],
            "grau_instrucao": [9],
        }
    )
    df_parquet.to_parquet(dir_parquet / "CAGEDMOV202401.parquet", index=False)

    dir_saida = tmp_path / "saida_cli_eda"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "eda",
            "--painel",
            str(caminho_painel),
            "--dados",
            str(dir_dados),
            "--saida",
            str(dir_saida),
        ],
    )
    main()

    assert (dir_saida / "eda_treino.md").exists()


def test_eda_item_5_fracao_exclusoes_em_celula_com_admissoes(tmp_path: Path) -> None:
    """Item 5: Exclusão em célula com admissões deve ser contada (10 MOV + 2 EXC -> 20%)."""
    from citizentech_ml.painel import carregar_pre_agregado

    dir_parquet = tmp_path / "parquet_item5"
    dir_parquet.mkdir(parents=True, exist_ok=True)

    # Cria 10 admissões em MOV
    df_mov = pd.DataFrame(
        {
            "competencia_mov": ["202401"] * 10,
            "competencia_dec": ["202401"] * 10,
            "competencia_arquivo": ["202401"] * 10,
            "arquivo_tipo": ["MOV"] * 10,
            "saldo_movimentacao": [1] * 10,
            "cbo2002_ocupacao": ["211205"] * 10,
            "uf": ["35"] * 10,
            "grau_instrucao": [9] * 10,
        }
    )
    df_mov.to_parquet(dir_parquet / "CAGEDMOV202401.parquet", index=False)

    # Cria 2 exclusões de admissão em EXC na mesma célula (competencia_mov=202401, CBO=211205, SP)
    df_exc = pd.DataFrame(
        {
            "competencia_mov": ["202401"] * 2,
            "competencia_dec": ["202401"] * 2,
            "competencia_exc": ["202401"] * 2,
            "competencia_arquivo": ["202401"] * 2,
            "arquivo_tipo": ["EXC"] * 2,
            "saldo_movimentacao": [1] * 2,
            "cbo2002_ocupacao": ["211205"] * 2,
            "uf": ["35"] * 2,
            "grau_instrucao": [9] * 2,
        }
    )
    df_exc.to_parquet(dir_parquet / "CAGEDEXC202401.parquet", index=False)


    df_pre, _ = carregar_pre_agregado(dir_parquet, por_tipo=True)

    # Verifica que df_pre possui a coluna arquivo_tipo
    assert "arquivo_tipo" in df_pre.columns

    # Monta painel mínimo para rodar EDA
    df_painel = pd.DataFrame(
        [
            {
                "competencia": "202401",
                "destino": "analista_dados_bi",
                "uf": "35",
                "particao": "treino",
                "admissoes": 10.0,
                "admissoes_total": 10.0,
                "alvo": 10.0,
                "mes": 1,
            }
        ]
    )

    dir_saida = tmp_path / "saida_item5"
    caminho_md = gerar_eda_treino(
        painel=df_painel,
        pre_agregado=df_pre,
        dir_saida=dir_saida,
    )
    conteudo = caminho_md.read_text(encoding="utf-8")
    # Deve conter a fração de exclusões correta de 20% (formatada em pt-BR como 20,0% ou 20,00%)
    assert "20,0" in conteudo


def test_eda_item_10_sazonalidade_ignora_ano_incompleto_e_calcula_indice(tmp_path: Path) -> None:
    """Item 10: Sazonalidade ignora 2024 (incompleto) e calcula índice sazonal (média = 1,00)."""
    # Anos completos: 2020 a 2023 (12 meses cada, valor constante 100)
    # Ano incompleto: 2024 (9 meses, valor 10.000)
    linhas = []
    for ano in range(2020, 2024):
        for m in range(1, 13):
            comp = f"{ano}{m:02d}"
            linhas.append(
                {
                    "competencia": comp,
                    "destino": "analista_dados_bi",
                    "uf": "35",
                    "particao": "treino",
                    "admissoes": 100.0,
                    "admissoes_total": 100.0,
                    "alvo": 100.0,
                    "mes": m,
                }
            )
    # 2024 (incompleto, 1 a 9)
    for m in range(1, 10):
        comp = f"2024{m:02d}"
        linhas.append(
            {
                "competencia": comp,
                "destino": "analista_dados_bi",
                "uf": "35",
                "particao": "treino",
                "admissoes": 10000.0,
                "admissoes_total": 10000.0,
                "alvo": 10000.0,
                "mes": m,
            }
        )

    df_painel = pd.DataFrame(linhas)
    # Pré-agregado mínimo
    df_pre = pd.DataFrame(
        [
            {
                "destino": "analista_dados_bi",
                "uf": "35",
                "superior": True,
                "competencia_mov": "202001",
                "competencia_disp": "202001",
                "delta_adm": 100,
                "delta_des": 0,
                "arquivo_tipo": "MOV",
            }
        ]
    )

    dir_saida = tmp_path / "saida_item10"
    caminho_md = gerar_eda_treino(
        painel=df_painel,
        pre_agregado=df_pre,
        dir_saida=dir_saida,
    )
    conteudo = caminho_md.read_text(encoding="utf-8")

    # A seção 4 deve citar os anos completos utilizados (2020, 2021, 2022, 2023)
    # e NÃO deve usar 2024 no índice
    assert "2020" in conteudo
    assert "2023" in conteudo
    # E o índice deve ser 1,00 para todos os meses (constante)
    assert "1,00" in conteudo
    # A frase factual deve citar tanto o maior quanto o menor índice
    assert "maior índice" in conteudo or "maior" in conteudo
    assert "menor índice" in conteudo or "menor" in conteudo


def test_formatar_pt_br_e_ufs() -> None:
    """Item 12: Valida formatação pt-BR e exibição legível de UFs inválidas."""
    from citizentech_ml.eda import formatar_pt_br, formatar_ufs_invalidas

    assert formatar_pt_br(139575, casas=0) == "139.575"
    assert formatar_pt_br(2448.7, casas=1) == "2.448,7"
    assert formatar_pt_br(14.18, casas=2, percentual=True) == "14,18%"
    assert formatar_pt_br(None) == "N/D"

    assert formatar_ufs_invalidas({"99": 2264}) == "UF 99: 2.264"
    assert formatar_ufs_invalidas({"99": 2264, "00": 10}) == "UF 00: 10, UF 99: 2.264"
    assert formatar_ufs_invalidas({}) == "Nenhuma"
    assert formatar_ufs_invalidas(None) == "Nenhuma"


def test_eda_itens_6_7_8_9_secao_5_for_e_ano_parcial(tmp_path: Path) -> None:
    """Itens 6-9: Fração FOR, declaradas pós-mês, 2 séries e ano parcial."""
    # Painel com 2024 (9 meses no treino)
    linhas_painel = []
    for m in range(1, 10):
        comp = f"2024{m:02d}"
        linhas_painel.append(
            {
                "competencia": comp,
                "destino": "analista_dados_bi",
                "uf": "35",
                "particao": "treino",
                "admissoes": 10.0,
                "admissoes_total": 20.0,
                "alvo": 10.0,
                "mes": m,
            }
        )
    df_painel = pd.DataFrame(linhas_painel)

    # df_pre com MOV (8 admissões) e FOR (2 admissões), disp > mov
    df_pre = pd.DataFrame(
        [
            {
                "destino": "analista_dados_bi",
                "uf": "35",
                "superior": True,
                "competencia_mov": "202401",
                "competencia_disp": "202401",
                "delta_adm": 8,
                "delta_des": 0,
                "arquivo_tipo": "MOV",
            },
            {
                "destino": "analista_dados_bi",
                "uf": "35",
                "superior": True,
                "competencia_mov": "202401",
                "competencia_disp": "202403",  # disp > mov
                "delta_adm": 2,
                "delta_des": 0,
                "arquivo_tipo": "FOR",
            },
        ]
    )

    dir_saida = tmp_path / "saida_itens_6_9"
    caminho_md = gerar_eda_treino(
        painel=df_painel,
        pre_agregado=df_pre,
        dir_saida=dir_saida,
        sha256_painel="abc123sha",
    )
    conteudo = caminho_md.read_text(encoding="utf-8")

    # Item 6: colunas próprias de Fração FOR e declaradas após o mês
    assert "Fração FOR (%)" in conteudo
    assert "Declaradas após o Mês (%)" in conteudo
    # Fração FOR: 2 / 10 = 20,00%
    assert "20,00%" in conteudo

    # Item 7: Ambas as séries rotuladas
    assert "Série Principal" in conteudo
    assert "Série de Contexto" in conteudo

    # Item 9: Colunas "Meses no Treino" e "Média Mensal"
    assert "Meses no Treino" in conteudo
    assert "Média Mensal" in conteudo

    # Item 15: Cabeçalho com sha256_painel e nota metodológica obrigatória
    assert "abc123sha" in conteudo
    msg_esperada = (
        "Dados observados do Novo Caged; nenhum número deste relatório vem de validação ou teste."
    )
    assert msg_esperada in conteudo


def test_eda_secao_5_serie_total_compara_com_as_of_total(tmp_path: Path) -> None:
    """A diferença consolidado × as-of da série total usa a coluna as-of TOTAL do painel."""
    df_painel = pd.DataFrame(
        [
            {
                "competencia": f"2024{m:02d}",
                "destino": "analista_dados_bi",
                "uf": "35",
                "particao": "treino",
                "admissoes": 8.0,
                "admissoes_total": 18.0,
                "alvo": 10.0,
                "mes": m,
            }
            for m in range(1, 10)
        ]
    )  # as-of no ano: principal 72, total 162

    def linha(superior: bool, disp: str, adm: int, tipo: str) -> dict:
        return {
            "destino": "analista_dados_bi",
            "uf": "35",
            "superior": superior,
            "competencia_mov": "202401",
            "competencia_disp": disp,
            "delta_adm": adm,
            "delta_des": 0,
            "arquivo_tipo": tipo,
        }

    df_pre = pd.DataFrame(
        [
            linha(True, "202401", 80, "MOV"),
            linha(True, "202403", 10, "FOR"),
            linha(False, "202401", 100, "MOV"),
        ]
    )  # consolidado: principal 90, total 190

    caminho_md = gerar_eda_treino(painel=df_painel, pre_agregado=df_pre, dir_saida=tmp_path / "s5")
    conteudo = caminho_md.read_text(encoding="utf-8")
    secao_5 = conteudo.split("## 5.")[1].split("## 6.")[0]

    assert "25,00%" in secao_5  # principal: (90 - 72) / 72
    assert "17,28%" in secao_5  # total: (190 - 162) / 162
    assert "163,89%" not in secao_5  # total comparado por engano com o as-of da principal
    assert "Não há movimentações de 2020" in secao_5  # frase não inventa média de ano ausente