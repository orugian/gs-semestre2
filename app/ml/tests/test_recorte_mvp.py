"""Testes do módulo de recorte do painel MVP (R29)."""

import json
from pathlib import Path

import pandas as pd
import pytest

from citizentech_ml.recorte import (
    DESTINOS_MVP_PADRAO,
    carregar_escopo_mvp,
    recortar_painel_mvp,
)


def _criar_painel_base() -> pd.DataFrame:
    """Retorna painel válido mínimo com os 6 destinos canônicos e origens 202012 e 202101."""
    todos_destinos = [
        "analista_dados_bi",
        "analista_monitoramento_iot",
        "analista_processos",
        "gerente_projetos_produto",
        "analista_suporte_infra",
        "desenvolvedor_sistemas",
    ]
    linhas = []
    for d in todos_destinos:
        for c in ["202012", "202101"]:
            linhas.append(
                {
                    "competencia": c,
                    "destino": d,
                    "uf": "35",
                    "admissoes": 10.0,
                    "admissoes_lag_1": 9.0,
                    "admissoes_lag_12": 8.0,
                    "admissoes_soma_3m": 30.0,
                    "admissoes_sazonal_ano_anterior": 25.0,
                    "alvo": 35.0,
                }
            )
    return pd.DataFrame(linhas)


def test_recortar_painel_mvp_seis_destinos_para_tres() -> None:
    """RED prioritário: painel com 6 destinos e origens 202012/202101 deve reter apenas 1/2/3.

    Input deve permanecer intacto e valores de lags preservados.
    """
    df_original = _criar_painel_base()
    df_clone = df_original.copy(deep=True)

    df_recortado = recortar_painel_mvp(df_original)

    # 1. Input deve permanecer intacto
    pd.testing.assert_frame_equal(df_original, df_clone)

    # 2. Saída deve conter apenas os 3 destinos aprovados no MVP R29
    destinos_retornados = sorted(df_recortado["destino"].unique())
    assert destinos_retornados == sorted(DESTINOS_MVP_PADRAO)

    # 3. Preservação de origens históricas 2020 e início do treino 202101 (2 meses * 3 destinos = 6)
    assert len(df_recortado) == 6
    assert set(df_recortado["competencia"].unique()) == {"202012", "202101"}

    # 4. Lags e demais colunas devem ser exatamente preservados
    for d in DESTINOS_MVP_PADRAO:
        sub_orig = df_original[
            (df_original["destino"] == d) & (df_original["competencia"] == "202012")
        ]
        sub_rec = df_recortado[
            (df_recortado["destino"] == d) & (df_recortado["competencia"] == "202012")
        ]
        assert sub_rec.iloc[0]["admissoes_lag_1"] == sub_orig.iloc[0]["admissoes_lag_1"] == 9.0
        assert sub_rec.iloc[0]["admissoes_lag_12"] == sub_orig.iloc[0]["admissoes_lag_12"] == 8.0


@pytest.mark.parametrize("comp_invalida", ["201912", "202510", "202512", "202601", "202606"])
def test_recortar_painel_mvp_rejeita_competencias_fora_intervalo(comp_invalida: str) -> None:
    """Rejeita estritamente competências fora do intervalo permitido 202001-202509."""
    df = _criar_painel_base()
    linha_extra = df.iloc[0:1].copy()
    linha_extra["competencia"] = comp_invalida
    df_com_extra = pd.concat([df, linha_extra], ignore_index=True)

    with pytest.raises(ValueError, match="fora do intervalo permitido 202001-202509"):
        recortar_painel_mvp(df_com_extra)


def test_recortar_painel_mvp_rejeita_destinos_desconhecidos() -> None:
    """Rejeita registros com destinos fora dos 6 canônicos conhecidos."""
    df = _criar_painel_base()
    linha_extra = df.iloc[0:1].copy()
    linha_extra["destino"] = "analista_desconhecido"
    df_com_extra = pd.concat([df, linha_extra], ignore_index=True)

    with pytest.raises(ValueError, match="Destinos desconhecidos encontrados"):
        recortar_painel_mvp(df_com_extra)


def test_recortar_painel_mvp_rejeita_duplicacao_chave() -> None:
    """Rejeita duplicata na chave (competencia, destino, uf)."""
    df = _criar_painel_base()
    linha_duplicada = df.iloc[0:1].copy()
    df_duplicado = pd.concat([df, linha_duplicada], ignore_index=True)

    with pytest.raises(ValueError, match="Chaves duplicadas"):
        recortar_painel_mvp(df_duplicado)


def test_recortar_painel_mvp_rejeita_ausencia_destinos_mvp() -> None:
    """Rejeita painel se qualquer um dos 3 destinos MVP estiver ausente."""
    df = _criar_painel_base()
    # Remove 'analista_processos'
    df_sem_processos = df[df["destino"] != "analista_processos"].copy()

    with pytest.raises(ValueError, match="Destinos obrigatórios do MVP ausentes"):
        recortar_painel_mvp(df_sem_processos)


def test_recortar_painel_mvp_rejeita_projecao_vazia() -> None:
    """Não aceita silenciosamente projeção vazia."""
    df_vazio = pd.DataFrame(columns=["competencia", "destino", "uf"])
    with pytest.raises(ValueError, match="painel vazio"):
        recortar_painel_mvp(df_vazio)


def test_carregar_escopo_mvp_padrao() -> None:
    """Verifica carregamento do arquivo oficial escopo_mvp.json."""
    escopo = carregar_escopo_mvp()
    assert escopo["decisao"] == "R29"
    assert escopo["status_rubricas"] == "revisao_humana_pendente"
    assert sorted(escopo["destinos"]) == sorted(DESTINOS_MVP_PADRAO)
    assert len(escopo["destinos"]) == 3
    assert "hash_recorte" in escopo
    assert "sha256_escopo" in escopo
    # Sem métricas
    assert "metricas" not in escopo
    assert "estatistica" not in escopo


def test_carregar_escopo_mvp_validacoes(tmp_path: Path) -> None:
    """Valida rejeição de escopos adulterados (destinos incorretos, duplicados, com métricas)."""
    # 1. Destino faltando
    arq1 = tmp_path / "escopo1.json"
    arq1.write_text(
        json.dumps({
            "versao": "1.0",
            "decisao": "R29",
            "destinos": ["analista_dados_bi", "analista_monitoramento_iot"],
            "status_rubricas": "revisao_humana_pendente",
        }),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Conjunto de destinos inválido"):
        carregar_escopo_mvp(arq1)

    # 2. Destinos com duplicatas
    arq2 = tmp_path / "escopo2.json"
    arq2.write_text(
        json.dumps({
            "versao": "1.0",
            "decisao": "R29",
            "destinos": [
                "analista_dados_bi",
                "analista_monitoramento_iot",
                "analista_processos",
                "analista_dados_bi",
            ],
            "status_rubricas": "revisao_humana_pendente",
        }),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicados"):
        carregar_escopo_mvp(arq2)

    # 3. Presença proibida de métricas
    arq3 = tmp_path / "escopo3.json"
    arq3.write_text(
        json.dumps({
            "versao": "1.0",
            "decisao": "R29",
            "destinos": list(DESTINOS_MVP_PADRAO),
            "status_rubricas": "revisao_humana_pendente",
            "metricas": {"mae": 10.5},
        }),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Métricas proibidas"):
        carregar_escopo_mvp(arq3)


def test_carregar_escopo_mvp_arquivo_inexistente(tmp_path: Path) -> None:
    """Verifica que carregar_escopo_mvp dispara FileNotFoundError se o arquivo não existir."""
    caminho_fake = tmp_path / "inexistente_escopo.json"
    with pytest.raises(FileNotFoundError, match="Arquivo de escopo não encontrado"):
        carregar_escopo_mvp(caminho_fake)


def test_recortar_painel_mvp_escopo_direto_rejeita_duplicatas() -> None:
    """Escopo passado diretamente não pode burlar validação aceitando duplicatas por set."""
    df = _criar_painel_base()
    escopo_com_duplicata = {
        "versao": "1.0.0",
        "decisao": "R29",
        "destinos": [
            "analista_dados_bi",
            "analista_monitoramento_iot",
            "analista_processos",
            "analista_dados_bi",
        ],
        "status_rubricas": "revisao_humana_pendente",
    }
    with pytest.raises(ValueError, match="duplicados"):
        recortar_painel_mvp(df, escopo=escopo_com_duplicata)


def test_recortar_painel_mvp_escopo_direto_valida_metadados_completos() -> None:
    """Escopo passado diretamente não pode burlar metadados (versao, decisao, status_rubricas)."""
    df = _criar_painel_base()

    # 1. Sem versão
    with pytest.raises(ValueError, match="versao"):
        recortar_painel_mvp(
            df,
            escopo={
                "decisao": "R29",
                "destinos": list(DESTINOS_MVP_PADRAO),
                "status_rubricas": "revisao_humana_pendente",
            },
        )

    # 2. Decisão incorreta
    with pytest.raises(ValueError, match="Decisão deve ser 'R29'"):
        recortar_painel_mvp(
            df,
            escopo={
                "versao": "1.0.0",
                "decisao": "R30",
                "destinos": list(DESTINOS_MVP_PADRAO),
                "status_rubricas": "revisao_humana_pendente",
            },
        )

    # 3. Status rubricas incorreto
    with pytest.raises(ValueError, match="status_rubricas"):
        recortar_painel_mvp(
            df,
            escopo={
                "versao": "1.0.0",
                "decisao": "R29",
                "destinos": list(DESTINOS_MVP_PADRAO),
                "status_rubricas": "homologado",
            },
        )


def test_recortar_painel_mvp_escopo_direto_rejeita_metricas() -> None:
    """Escopo passado diretamente não pode conter métricas proibidas."""
    df = _criar_painel_base()
    escopo_com_metrica = {
        "versao": "1.0.0",
        "decisao": "R29",
        "destinos": list(DESTINOS_MVP_PADRAO),
        "status_rubricas": "revisao_humana_pendente",
        "estatistica": {"valor": 42},
    }
    with pytest.raises(ValueError, match="Métricas proibidas"):
        recortar_painel_mvp(df, escopo=escopo_com_metrica)


def test_executar_recorte_cli_sucesso(tmp_path: Path) -> None:
    """Execução da CLI de recorte grava parquet e manifesto JSON com hashes e partições."""
    from citizentech_ml.recorte import executar_recorte_cli

    df = _criar_painel_base()
    p_painel = tmp_path / "painel_entrada.parquet"
    df.to_parquet(p_painel, index=False)

    p_saida = tmp_path / "saida_recorte" / "painel_mvp.parquet"
    p_out, p_man = executar_recorte_cli(caminho_painel=p_painel, caminho_saida=p_saida)

    assert p_out.exists()
    assert p_man.exists()

    # Validação do Parquet recortado
    df_rec = pd.read_parquet(p_out)
    assert sorted(df_rec["destino"].unique()) == sorted(DESTINOS_MVP_PADRAO)

    # Validação do Manifesto JSON
    manifesto = json.loads(p_man.read_text(encoding="utf-8"))
    assert manifesto["decisao"] == "R29"
    assert sorted(manifesto["destinos"]) == sorted(DESTINOS_MVP_PADRAO)
    assert manifesto["inicio_treino"] == "202101"
    assert "sha256_input" in manifesto
    assert "sha256_output" in manifesto
    assert "sha256_escopo" in manifesto
    assert "hash_recorte" in manifesto
    assert manifesto["linhas_por_particao"]["historico_2020"] == 3
    assert manifesto["linhas_por_particao"]["treino_202101_202409"] == 3
    assert manifesto["linhas_por_particao"]["total"] == 6
    assert manifesto["data_utc"].endswith("Z")
    assert "pandas" in manifesto["versoes"]
    assert "pyarrow" in manifesto["versoes"]


def test_executar_recorte_cli_impede_sobrescrita_parquet(tmp_path: Path) -> None:
    """Proteção estrita: saída já existente deve falhar com FileExistsError antes de gravar."""
    from citizentech_ml.recorte import executar_recorte_cli

    df = _criar_painel_base()
    p_painel = tmp_path / "painel_entrada.parquet"
    df.to_parquet(p_painel, index=False)

    p_saida = tmp_path / "ja_existe.parquet"
    p_saida.write_text("conteudo anterior", encoding="utf-8")

    with pytest.raises(FileExistsError, match="Arquivo de saída já existente"):
        executar_recorte_cli(caminho_painel=p_painel, caminho_saida=p_saida)


def test_executar_recorte_cli_impede_sobrescrita_manifesto(tmp_path: Path) -> None:
    """Proteção estrita: manifesto já existente deve falhar com FileExistsError antes de gravar."""
    from citizentech_ml.recorte import executar_recorte_cli

    df = _criar_painel_base()
    p_painel = tmp_path / "painel_entrada.parquet"
    df.to_parquet(p_painel, index=False)

    p_saida = tmp_path / "painel_novo.parquet"
    p_manifesto = p_saida.with_suffix(".json")
    p_manifesto.write_text("manifesto anterior", encoding="utf-8")

    with pytest.raises(FileExistsError, match="Manifesto de saída já existente"):
        executar_recorte_cli(caminho_painel=p_painel, caminho_saida=p_saida)


def test_executar_recorte_cli_painel_inexistente(tmp_path: Path) -> None:
    """Painel de entrada inexistente deve disparar FileNotFoundError."""
    from citizentech_ml.recorte import executar_recorte_cli

    p_painel_fake = tmp_path / "nao_existe.parquet"
    p_saida = tmp_path / "saida.parquet"
    with pytest.raises(FileNotFoundError, match="Painel de entrada não encontrado"):
        executar_recorte_cli(caminho_painel=p_painel_fake, caminho_saida=p_saida)


def test_main_cli_recorte(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifica ponto de entrada main() de recorte via python -m citizentech_ml.recorte."""
    import sys

    from citizentech_ml.recorte import main

    df = _criar_painel_base()
    p_painel = tmp_path / "in.parquet"
    df.to_parquet(p_painel, index=False)
    p_saida = tmp_path / "out" / "mvp.parquet"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "recorte",
            "--painel",
            str(p_painel),
            "--saida",
            str(p_saida),
        ],
    )
    main()

    assert p_saida.exists()
    assert p_saida.with_suffix(".json").exists()
