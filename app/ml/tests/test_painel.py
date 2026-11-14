"""Testes do módulo de painel de desenvolvimento."""

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from citizentech_ml.ingestao.manifesto import salvar_manifesto
from citizentech_ml.ingestao.modelos import RegistroProcedencia
from citizentech_ml.painel import (
    carregar_pre_agregado,
    construir_painel_desenvolvimento,
    salvar_painel,
)


def test_carregar_pre_agregado_filtragem_uf_e_limite_mov(tmp_path: Path) -> None:
    """Valida descarte e contagem de UFs inválidas e competências após limite."""
    dir_parquet = tmp_path / "parquet"
    dir_parquet.mkdir(parents=True, exist_ok=True)

    df_mov = pd.DataFrame(
        {
            "competencia_mov": ["202401", "202401", "202401"],
            "competencia_dec": ["202401", "202401", "202401"],
            "competencia_arquivo": ["202401", "202401", "202401"],
            "arquivo_tipo": ["MOV", "MOV", "MOV"],
            "saldo_movimentacao": [1, 1, 1],
            "cbo2002_ocupacao": ["211205", "211205", "211205"],
            "uf": ["35", "35", "99"],
            "grau_instrucao": [9, 9, 9],
        }
    )
    df_mov.to_parquet(dir_parquet / "CAGEDMOV202401.parquet", index=False)

    df_for = pd.DataFrame(
        {
            "competencia_mov": ["202401", "202402", "202601"],
            "competencia_dec": ["202403", "202403", "202403"],
            "competencia_arquivo": ["202403", "202403", "202403"],
            "arquivo_tipo": ["FOR", "FOR", "FOR"],
            "saldo_movimentacao": [1, 1, 1],
            "cbo2002_ocupacao": ["211205", "211205", "211205"],
            "uf": ["35", "35", "35"],
            "grau_instrucao": [9, 9, 9],
        }
    )
    df_for.to_parquet(dir_parquet / "CAGEDFOR202403.parquet", index=False)

    pre_agregado, relatorio = carregar_pre_agregado(dir_parquet)

    assert relatorio["linhas_uf_invalida"] == {"99": 1}
    assert relatorio["linhas_apos_limite"] == 1
    assert pre_agregado["delta_adm"].sum() == 4


def test_carregar_pre_agregado_por_tipo_e_equivalencia(tmp_path: Path) -> None:
    """Item 5: Valida carregar_pre_agregado com por_tipo=True e equivalência com modo padrão."""
    dir_parquet = tmp_path / "parquet_equiv"
    dir_parquet.mkdir(parents=True, exist_ok=True)

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

    pre_padrao, rel_padrao = carregar_pre_agregado(dir_parquet, por_tipo=False)
    pre_tipo, rel_tipo = carregar_pre_agregado(dir_parquet, por_tipo=True)

    assert "arquivo_tipo" in pre_tipo.columns
    assert "arquivo_tipo" not in pre_padrao.columns

    # No modo por_tipo, MOV e EXC ficam separados
    mov_rows = pre_tipo[pre_tipo["arquivo_tipo"] == "MOV"]
    exc_rows = pre_tipo[pre_tipo["arquivo_tipo"] == "EXC"]
    assert mov_rows["delta_adm"].sum() == 10
    assert exc_rows["delta_adm"].sum() == -2

    # Teste de equivalência: consolidar pre_tipo sem arquivo_tipo dá exatamente pre_padrao
    cols_grupo = ["destino", "uf", "superior", "competencia_mov", "competencia_disp"]
    reconsolidado = (
        pre_tipo.groupby(cols_grupo, as_index=False)[["delta_adm", "delta_des"]]
        .sum()
        .sort_values(cols_grupo)
        .reset_index(drop=True)
    )
    padrao_ordenado = pre_padrao.sort_values(cols_grupo).reset_index(drop=True)
    pd.testing.assert_frame_equal(reconsolidado, padrao_ordenado)



def test_carregar_pre_agregado_erros_limite_e_diretorio(tmp_path: Path) -> None:
    """Verifica FileNotFoundError para diretório vazio/inexistente e ValueError para limite."""
    # Diretório inexistente
    with pytest.raises(FileNotFoundError, match="Diretório de parquets não encontrado"):
        carregar_pre_agregado(tmp_path / "nao_existe")

    # Diretório vazio
    dir_vazio = tmp_path / "vazio"
    dir_vazio.mkdir()
    with pytest.raises(FileNotFoundError, match="Nenhum arquivo Parquet encontrado"):
        carregar_pre_agregado(dir_vazio)

    # Limite > 202512 sem permitir_teste
    dir_com_arquivo = tmp_path / "com_arquivo"
    dir_com_arquivo.mkdir()
    pd.DataFrame({"a": [1]}).to_parquet(dir_com_arquivo / "teste.parquet")
    with pytest.raises(ValueError, match="exige permitir_teste=True"):
        carregar_pre_agregado(dir_com_arquivo, limite_competencia_mov="202606")


def test_construir_painel_desenvolvimento_e_salvar(tmp_path: Path) -> None:
    """Testa construção do painel de desenvolvimento com partições e salvamento."""
    dir_dados = tmp_path / "dados"
    dir_parquet = dir_dados / "caged" / "parquet"
    dir_parquet.mkdir(parents=True, exist_ok=True)

    # 1. Criar manifesto de procedência sintético para cobertura
    manifesto_path = dir_dados / "caged" / "procedencia.json"
    registros = [
        RegistroProcedencia(
            fonte="novo_caged",
            url="http://teste",
            arquivo=f"CAGEDMOV{m}.7z",
            tipo="MOV",
            competencia_arquivo=m,
            situacao="ingerido",
            linhas_gravadas=10,
        )
        for m in ["202409", "202410", "202411", "202412", "202501"]
    ]
    salvar_manifesto(manifesto_path, registros)

    # 2. Criar parquets sintéticos
    for m in ["202409", "202410", "202411", "202412", "202501"]:
        df = pd.DataFrame(
            {
                "competencia_mov": [m],
                "competencia_dec": [m],
                "competencia_arquivo": [m],
                "arquivo_tipo": ["MOV"],
                "saldo_movimentacao": [1],
                "cbo2002_ocupacao": ["211205"],
                "uf": ["35"],
                "grau_instrucao": [9],
            }
        )
        df.to_parquet(dir_parquet / f"CAGEDMOV{m}.parquet", index=False)

    # Fim > 202509 deve falhar
    with pytest.raises(ValueError, match="não pode ser posterior a 202509"):
        construir_painel_desenvolvimento(dir_dados, inicio="202409", fim="202601")

    # Construir painel de 202409 a 202501
    painel, relatorio = construir_painel_desenvolvimento(
        dir_dados, inicio="202409", fim="202501"
    )

    # Nenhuma competência >= 202510
    assert (painel["competencia"] >= "202510").sum() == 0

    # Partições corretas
    particoes_comp = (
        painel[["competencia", "particao"]].drop_duplicates().set_index("competencia")["particao"]
    )
    assert particoes_comp.get("202409") == "treino"
    assert particoes_comp.get("202410") == "embargo"
    assert particoes_comp.get("202411") == "embargo"
    assert particoes_comp.get("202412") == "embargo"
    assert particoes_comp.get("202501") == "validacao"

    # Salvar painel
    dir_saida = tmp_path / "saida"
    salvar_painel(painel, relatorio, dir_saida)

    caminho_parquet = dir_saida / "painel_desenvolvimento.parquet"
    caminho_json = dir_saida / "painel_desenvolvimento.json"

    assert caminho_parquet.exists()
    assert caminho_json.exists()

    bytes_json = caminho_json.read_bytes()
    # Verifica ausência de BOM (UTF-8 puro não começa com 0xEF 0xBB 0xBF)
    assert not bytes_json.startswith(b"\xef\xbb\xbf")

    conteudo_json = json.loads(bytes_json.decode("utf-8"))
    sha_esperado = hashlib.sha256(caminho_parquet.read_bytes()).hexdigest()
    assert conteudo_json["sha256_parquet"] == sha_esperado
    assert "data_utc" in conteudo_json
    assert conteudo_json["data_utc"].endswith("Z")
    assert "versoes" in conteudo_json


def test_cli_painel(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida execução da CLI do painel e tratamento de erro."""
    import sys

    from citizentech_ml.painel import main

    dir_dados = tmp_path / "dados_cli"
    dir_parquet = dir_dados / "caged" / "parquet"
    dir_parquet.mkdir(parents=True, exist_ok=True)
    manifesto_path = dir_dados / "caged" / "procedencia.json"
    salvar_manifesto(
        manifesto_path,
        [
            RegistroProcedencia(
                fonte="novo_caged",
                url="http://teste",
                arquivo="CAGEDMOV202409.7z",
                tipo="MOV",
                competencia_arquivo="202409",
                situacao="ingerido",
                linhas_gravadas=1,
            )
        ],
    )
    df = pd.DataFrame(
        {
            "competencia_mov": ["202409"],
            "competencia_dec": ["202409"],
            "competencia_arquivo": ["202409"],
            "arquivo_tipo": ["MOV"],
            "saldo_movimentacao": [1],
            "cbo2002_ocupacao": ["211205"],
            "uf": ["35"],
            "grau_instrucao": [9],
        }
    )
    df.to_parquet(dir_parquet / "CAGEDMOV202409.parquet", index=False)
    dir_saida = tmp_path / "saida_cli"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "painel",
            "--dados",
            str(dir_dados),
            "--saida",
            str(dir_saida),
            "--inicio",
            "202409",
            "--fim",
            "202409",
        ],
    )
    main()
    assert (dir_saida / "painel_desenvolvimento.parquet").exists()

    # Erro (diretório inexistente) deve invocar sys.exit(1)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "painel",
            "--dados",
            str(tmp_path / "nao_existe"),
            "--saida",
            str(dir_saida),
        ],
    )
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1

