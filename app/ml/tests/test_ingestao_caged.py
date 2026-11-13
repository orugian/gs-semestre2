"""Conjunto completo de testes do módulo de ingestão do Novo Caged (Contrato S6)."""

import hashlib
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd
import py7zr
import pytest

from citizentech_ml.ingestao import (
    Fonte,
    Ocupacoes,
    carregar_ocupacoes,
    cobertura,
    consolidar_mensal,
    ingerir_arquivo,
    ingerir_periodo,
)
from citizentech_ml.ingestao.__main__ import main as cli_main

CABECALHO_MOV = (
    "competênciamov;região;uf;município;seção;subclasse;saldomovimentação;"
    "cbo2002ocupação;categoria;graudeinstrução;idade;horascontratuais;raçacor;sexo;"
    "tipoempregador;tipoestabelecimento;tipomovimentação;tipodedeficiência;"
    "indtrabintermitente;indtrabparcial;salário;tamestabjan;indicadoraprendiz;"
    "origemdainformação;competênciadec;indicadordeforadoprazo;unidadesaláriocódigo;valorsaláriofixo"
)

CABECALHO_EXC = (
    "competênciamov;região;uf;município;seção;subclasse;saldomovimentação;"
    "cbo2002ocupação;categoria;graudeinstrução;idade;horascontratuais;raçacor;sexo;"
    "tipoempregador;tipoestabelecimento;tipomovimentação;tipodedeficiência;"
    "indtrabintermitente;indtrabparcial;salário;tamestabjan;indicadoraprendiz;"
    "origemdainformação;competênciadec;competênciaexc;indicadordeexclusão;"
    "indicadordeforadoprazo;unidadesaláriocódigo;valorsaláriofixo"
)

ESQUEMA_COLUNAS_ESPERADO = [
    "competencia_mov",
    "regiao",
    "uf",
    "municipio",
    "secao",
    "subclasse",
    "saldo_movimentacao",
    "cbo2002_ocupacao",
    "categoria",
    "grau_instrucao",
    "horas_contratuais",
    "tipo_empregador",
    "tipo_estabelecimento",
    "tipo_movimentacao",
    "ind_trab_intermitente",
    "ind_trab_parcial",
    "indicador_aprendiz",
    "salario",
    "valor_salario_fixo",
    "tam_estab_jan",
    "origem_informacao",
    "unidade_salario_codigo",
    "competencia_dec",
    "indicador_fora_prazo",
    "competencia_exc",
    "indicador_exclusao",
    "arquivo_tipo",
    "competencia_arquivo",
]


def criar_7z_em_bytes(nome_txt: str, conteudo_txt: str) -> bytes:
    """Cria um arquivo .7z em memória contendo o arquivo .txt com o conteúdo fornecido."""
    buffer = io.BytesIO()
    with py7zr.SevenZipFile(buffer, mode="w") as z:
        z.writestr(conteudo_txt.encode("utf-8"), nome_txt)
    return buffer.getvalue()


class BaixadorFalso:
    """Baixador em memória para testes sem acesso à rede."""

    def __init__(
        self,
        arquivos: dict[tuple[str, str], bytes] | None = None,
        listar_map: dict[str, list[str]] | None = None,
        falhas: set[tuple[str, str]] | None = None,
    ):
        self.arquivos = arquivos or {}
        self.listar_map = listar_map or {}
        self.falhas = falhas or set()
        self.chamadas_download: list[tuple[str, str]] = []
        self.chamadas_listar: list[str] = []

    def listar_arquivos(self, competencia: str) -> list[str]:
        self.chamadas_listar.append(competencia)
        if competencia in self.listar_map:
            return self.listar_map[competencia]
        return [f"CAGED{t}{c}.7z" for (t, c) in self.arquivos.keys() if c == competencia]

    def baixar_arquivo(self, tipo: str, competencia: str, destino: Path) -> Path:
        self.chamadas_download.append((tipo, competencia))
        if (tipo, competencia) in self.falhas:
            raise RuntimeError(f"Simulacao de falha de rede ao baixar CAGED{tipo}{competencia}.7z")
        conteudo = self.arquivos.get((tipo, competencia))
        if conteudo is None:
            raise FileNotFoundError(f"Arquivo CAGED{tipo}{competencia}.7z nao encontrado no mock")
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(conteudo)
        return destino


def _obter_ocupacoes_teste(cbos: list[str]) -> Ocupacoes:
    """Helper para instanciar objeto Ocupacoes para testes."""
    return Ocupacoes(
        versao="teste-v1",
        destinos={"dev": {"nome": "Desenvolvedor", "cbo6": cbos}},
        cbo6_reserva=[],
        codigos_ingestao=set(cbos),
        hash="hash-teste-sha256",
    )


# ---------------------------------------------------------------------------
# Teste prioritário (RED -> GREEN)
# ---------------------------------------------------------------------------
def test_ingestao_grava_so_ocupacoes_da_lista_sem_atributos_sensiveis(tmp_path: Path):
    """Teste prioritário: ingestão filtra CBOs, descarta sensíveis e limpa bruto."""
    cbo_elegivel = "212405"
    cbo_ignorado = "999999"

    linha1 = (
        f"202609;3;33;330455;P;8513900;1;{cbo_elegivel};101;9;35;40,00;1;1;"
        "0;1;97;0;0;0;5000,00;99;0;1;202609;0;5;5000,00"
    )
    linha2 = (
        f"202609;3;33;330455;P;8513900;1;{cbo_ignorado};101;7;45;44,00;2;2;"
        "0;1;97;0;0;0;3000,00;99;0;1;202609;0;5;3000,00"
    )
    linha3 = (
        f"202609;3;35;355030;P;8513900;-1;{cbo_elegivel};101;10;28;40,00;3;1;"
        "0;1;40;0;0;0;6000,00;99;0;1;202609;0;5;6000,00"
    )

    conteudo_csv = f"{CABECALHO_MOV}\r\n{linha1}\r\n{linha2}\r\n{linha3}\r\n"
    bytes_7z = criar_7z_em_bytes("CAGEDMOV202609.txt", conteudo_csv)
    sha256_esperado = hashlib.sha256(bytes_7z).hexdigest()

    baixador = BaixadorFalso(arquivos={("MOV", "202609"): bytes_7z})
    ocupacoes = _obter_ocupacoes_teste([cbo_elegivel])
    fonte = Fonte()

    registro = ingerir_arquivo(
        tipo="MOV",
        competencia="202609",
        ocupacoes=ocupacoes,
        dir_dados=tmp_path,
        baixador=baixador,
        fonte=fonte,
    )

    # 1. Parquet existe e contém somente linhas com CBOs da lista, na quantidade exata (2 linhas)
    caminho_parquet = tmp_path / "caged" / "parquet" / "CAGEDMOV202609.parquet"
    assert caminho_parquet.exists()
    df = pd.read_parquet(caminho_parquet)
    assert len(df) == 2
    assert set(df["cbo2002_ocupacao"]) == {cbo_elegivel}

    # 2. As colunas do Parquet são exatamente as do esquema; nenhuma contém atributo sensível
    assert list(df.columns) == ESQUEMA_COLUNAS_ESPERADO
    for col in df.columns:
        tokens = col.lower().split("_")
        assert "idade" not in tokens
        assert "sexo" not in tokens
        assert "raca" not in tokens
        assert "cor" not in tokens
        assert not any("defici" in t for t in tokens)

    # 3. caged/bruto/ está vazio
    bruto_dir = tmp_path / "caged" / "bruto"
    assert bruto_dir.exists()
    assert len(list(bruto_dir.iterdir())) == 0

    # 4. Procedência confere
    assert registro.situacao == "ingerido"
    assert registro.sha256_7z == sha256_esperado
    assert registro.bytes_7z == len(bytes_7z)
    assert registro.linhas_lidas == 3
    assert registro.linhas_gravadas == 2


# ---------------------------------------------------------------------------
# 1. R05 ponta a ponta: valores sensíveis nunca vazam em manifesto nem CLI
# ---------------------------------------------------------------------------
def test_r05_ponta_a_ponta_valores_sensiveis_nunca_aparecem_em_manifesto_ou_cli(
    tmp_path: Path, monkeypatch, capsys
):
    """R05: valores sentinela de colunas sensíveis não vazam em arquivos nem logs."""
    cbo = "212405"
    idade_sentinela = "777"
    raca_sentinela = "888"
    sexo_sentinela = "999"
    defici_sentinela = "555"

    linha = (
        f"202609;3;33;330455;P;8513900;1;{cbo};101;9;"
        f"{idade_sentinela};40,00;{raca_sentinela};{sexo_sentinela};"
        f"0;1;97;{defici_sentinela};0;0;5000,00;99;0;1;202609;0;5;5000,00"
    )
    conteudo_csv = f"{CABECALHO_MOV}\r\n{linha}\r\n"
    bytes_7z = criar_7z_em_bytes("CAGEDMOV202609.txt", conteudo_csv)

    json_ocupacoes = tmp_path / "ocupacoes.json"
    json_ocupacoes.write_text(
        json.dumps(
            {
                "versao": "teste-v1",
                "destinos": {"dev": {"nome": "Desenvolvedor", "cbo6": [cbo]}},
                "cbo6_reserva": [],
            }
        ),
        encoding="utf-8",
    )

    baixador = BaixadorFalso(
        arquivos={("MOV", "202609"): bytes_7z},
        listar_map={"202609": ["CAGEDMOV202609.7z"]},
    )
    monkeypatch.setattr(
        "citizentech_ml.ingestao.ingestor.BaixadorCurl", lambda *args, **kwargs: baixador
    )

    dir_dados = tmp_path / "dados"
    args = [
        "--ocupacoes",
        str(json_ocupacoes),
        "--inicio",
        "202609",
        "--fim",
        "202609",
        "--dados",
        str(dir_dados),
    ]

    ret = cli_main(args)
    assert ret == 0

    stdout = capsys.readouterr().out
    manifesto_txt = (dir_dados / "caged" / "procedencia.json").read_text(encoding="utf-8")

    for sentinela in [idade_sentinela, raca_sentinela, sexo_sentinela, defici_sentinela]:
        assert sentinela not in stdout
        assert sentinela not in manifesto_txt


# ---------------------------------------------------------------------------
# 2. EXC: colunas competencia_exc e indicador_exclusao
# ---------------------------------------------------------------------------
def test_exc_com_competencia_exc_e_indicador_exclusao_preenchidos_e_nulos_no_mov(tmp_path: Path):
    """EXC popula competencia_exc e indicador_exclusao; MOV mantém nulos."""
    cbo = "212405"

    linha_exc = (
        f"202003;3;33;330455;F;4292802;1;{cbo};101;9;X;44,00;X;X;0;1;20;X;0;0;2000,00;99;0;1;"
        "202003;202609;1;0;5;2000,00"
    )
    bytes_exc = criar_7z_em_bytes("CAGEDEXC202609.txt", f"{CABECALHO_EXC}\r\n{linha_exc}\r\n")

    linha_mov = (
        f"202609;3;33;330455;P;8513900;1;{cbo};101;9;X;40,00;X;X;0;1;97;X;0;0;2500,00;99;0;1;"
        "202609;0;5;2500,00"
    )
    bytes_mov = criar_7z_em_bytes("CAGEDMOV202609.txt", f"{CABECALHO_MOV}\r\n{linha_mov}\r\n")

    baixador = BaixadorFalso(
        arquivos={
            ("EXC", "202609"): bytes_exc,
            ("MOV", "202609"): bytes_mov,
        }
    )
    ocupacoes = _obter_ocupacoes_teste([cbo])

    ingerir_arquivo("EXC", "202609", ocupacoes, tmp_path, baixador=baixador)
    ingerir_arquivo("MOV", "202609", ocupacoes, tmp_path, baixador=baixador)

    df_exc = pd.read_parquet(tmp_path / "caged" / "parquet" / "CAGEDEXC202609.parquet")
    assert df_exc["competencia_exc"].iloc[0] == "202609"
    assert df_exc["indicador_exclusao"].iloc[0] == 1

    df_mov = pd.read_parquet(tmp_path / "caged" / "parquet" / "CAGEDMOV202609.parquet")
    assert pd.isna(df_mov["competencia_exc"].iloc[0])
    assert pd.isna(df_mov["indicador_exclusao"].iloc[0])


# ---------------------------------------------------------------------------
# 3. T03 - Salário: vazio ou texto inválido vira nulo, nunca 0; vírgula decimal
# ---------------------------------------------------------------------------
def test_t03_salario_vazio_ou_invalido_vira_nulo_e_decimal_com_virgula_convertido(tmp_path: Path):
    """T03: salários vazios ou não numéricos viram NaN; '1621,00' vira 1621.0."""
    cbo = "212405"
    linha_valido = (
        f"202609;3;33;330455;P;8513900;1;{cbo};101;9;30;40,00;1;1;0;1;97;0;0;0;"
        "1621,00;99;0;1;202609;0;5;1621,00"
    )
    linha_vazio = (
        f"202609;3;33;330455;P;8513900;1;{cbo};101;9;30;40,00;1;1;0;1;97;0;0;0;"
        ";99;0;1;202609;0;5;"
    )
    linha_invalido = (
        f"202609;3;33;330455;P;8513900;1;{cbo};101;9;30;40,00;1;1;0;1;97;0;0;0;"
        "TEXTO_INVALIDO;99;0;1;202609;0;5;ABC"
    )

    conteudo = f"{CABECALHO_MOV}\r\n{linha_valido}\r\n{linha_vazio}\r\n{linha_invalido}\r\n"
    bytes_7z = criar_7z_em_bytes("CAGEDMOV202609.txt", conteudo)
    baixador = BaixadorFalso(arquivos={("MOV", "202609"): bytes_7z})
    ocupacoes = _obter_ocupacoes_teste([cbo])

    ingerir_arquivo("MOV", "202609", ocupacoes, tmp_path, baixador=baixador)

    df = pd.read_parquet(tmp_path / "caged" / "parquet" / "CAGEDMOV202609.parquet")
    assert df["salario"].iloc[0] == 1621.0
    assert df["valor_salario_fixo"].iloc[0] == 1621.0

    assert np.isnan(df["salario"].iloc[1])
    assert np.isnan(df["valor_salario_fixo"].iloc[1])

    assert np.isnan(df["salario"].iloc[2])
    assert np.isnan(df["valor_salario_fixo"].iloc[2])


# ---------------------------------------------------------------------------
# 4. T03 - Período ausente na fonte registrado e sem linhas falsas na consolidação
# ---------------------------------------------------------------------------
def test_t03_periodo_ausente_na_fonte_registrado_e_sem_linhas_falsas_na_consolidacao(
    tmp_path: Path,
):
    """T03: arquivos não existentes na fonte viram ausente_na_fonte sem gerar linhas com zero."""
    cbo = "212405"
    linha_mov = (
        f"202001;3;33;330455;P;8513900;1;{cbo};101;9;30;40,00;1;1;0;1;97;0;0;0;"
        "3000,00;99;0;1;202001;0;5;3000,00"
    )
    bytes_mov = criar_7z_em_bytes("CAGEDMOV202001.txt", f"{CABECALHO_MOV}\r\n{linha_mov}\r\n")

    # 202001 tem apenas MOV; FOR e EXC estão ausentes no FTP
    baixador = BaixadorFalso(
        arquivos={("MOV", "202001"): bytes_mov},
        listar_map={"202001": ["CAGEDMOV202001.7z"]},
    )
    ocupacoes = _obter_ocupacoes_teste([cbo])

    resumo = ingerir_periodo("202001", "202001", ocupacoes, tmp_path, baixador=baixador)
    assert resumo.total_ingeridos == 1
    assert resumo.total_ausentes == 2

    df_cob = cobertura(tmp_path, "202001", "202001")
    mov_cob = df_cob[df_cob["tipo"] == "MOV"]["situacao"].iloc[0]
    for_cob = df_cob[df_cob["tipo"] == "FOR"]["situacao"].iloc[0]
    exc_cob = df_cob[df_cob["tipo"] == "EXC"]["situacao"].iloc[0]

    assert mov_cob == "ingerido"
    assert for_cob == "ausente_na_fonte"
    assert exc_cob == "ausente_na_fonte"

    # Na consolidação, apenas o registro real de 202001 existe, sem linhas inventadas
    df_cons = consolidar_mensal(tmp_path / "caged" / "parquet")
    assert len(df_cons) == 1
    assert df_cons["competencia_mov"].iloc[0] == "202001"
    assert df_cons["admissoes"].iloc[0] == 1


# ---------------------------------------------------------------------------
# 5. T02 - Consolidação MOV + FOR - EXC com duplicatas preservadas
# ---------------------------------------------------------------------------
def test_t02_consolidacao_mov_for_exc_com_linhas_duplicadas(tmp_path: Path):
    """T02: consolidação calcula MOV+FOR-EXC e não usa drop_duplicates em linhas idênticas."""
    cbo = "212405"
    uf = "33"

    # MOV 202003: 2 admissões idênticas e 1 desligamento
    linha_adm = (
        f"202003;3;{uf};330455;P;8513900;1;{cbo};101;9;30;40,00;1;1;0;1;97;0;0;0;"
        "2500,00;99;0;1;202003;0;5;2500,00"
    )
    linha_des = (
        f"202003;3;{uf};330455;P;8513900;-1;{cbo};101;9;30;40,00;1;1;0;1;40;0;0;0;"
        "2500,00;99;0;1;202003;0;5;2500,00"
    )
    conteudo_mov = f"{CABECALHO_MOV}\r\n{linha_adm}\r\n{linha_adm}\r\n{linha_des}\r\n"
    bytes_mov = criar_7z_em_bytes("CAGEDMOV202003.txt", conteudo_mov)

    # FOR 202005: 1 admissão com competencia_mov=202003
    linha_for = (
        f"202003;3;{uf};330455;P;8513900;1;{cbo};101;9;30;40,00;1;1;0;1;97;0;0;0;"
        "2500,00;99;0;1;202005;1;5;2500,00"
    )
    conteudo_for = f"{CABECALHO_MOV}\r\n{linha_for}\r\n"
    bytes_for = criar_7z_em_bytes("CAGEDFOR202005.txt", conteudo_for)

    # EXC 202006: exclusão de 1 admissão de 202003
    linha_exc = (
        f"202003;3;{uf};330455;P;8513900;1;{cbo};101;9;30;40,00;1;1;0;1;97;0;0;0;"
        "2500,00;99;0;1;202003;202006;1;0;5;2500,00"
    )
    conteudo_exc = f"{CABECALHO_EXC}\r\n{linha_exc}\r\n"
    bytes_exc = criar_7z_em_bytes("CAGEDEXC202006.txt", conteudo_exc)

    baixador = BaixadorFalso(
        arquivos={
            ("MOV", "202003"): bytes_mov,
            ("FOR", "202005"): bytes_for,
            ("EXC", "202006"): bytes_exc,
        }
    )
    ocupacoes = _obter_ocupacoes_teste([cbo])

    ingerir_arquivo("MOV", "202003", ocupacoes, tmp_path, baixador=baixador)
    ingerir_arquivo("FOR", "202005", ocupacoes, tmp_path, baixador=baixador)
    ingerir_arquivo("EXC", "202006", ocupacoes, tmp_path, baixador=baixador)

    df_cons = consolidar_mensal(tmp_path / "caged" / "parquet")
    assert len(df_cons) == 1
    linha_res = df_cons.iloc[0]

    assert linha_res["competencia_mov"] == "202003"
    assert linha_res["uf"] == uf
    assert linha_res["cbo2002_ocupacao"] == cbo
    assert bool(linha_res["superior"]) is True
    # (2 MOV + 1 FOR) - 1 EXC = 2 admissões
    assert linha_res["admissoes"] == 2
    # (1 MOV + 0 FOR) - 0 EXC = 1 desligamento
    assert linha_res["desligamentos"] == 1


# ---------------------------------------------------------------------------
# 6. T02 - Reingestão não infla com retomada
# ---------------------------------------------------------------------------
def test_t02_reingestao_nao_infla_com_retomada(tmp_path: Path):
    """T02: reexecução pula arquivos já ingeridos sem refazer download nem inflar registros."""
    cbo = "212405"
    linha = (
        f"202609;3;33;330455;P;8513900;1;{cbo};101;9;30;40,00;1;1;0;1;97;0;0;0;"
        "2000,00;99;0;1;202609;0;5;2000,00"
    )
    bytes_mov = criar_7z_em_bytes("CAGEDMOV202609.txt", f"{CABECALHO_MOV}\r\n{linha}\r\n")

    baixador = BaixadorFalso(
        arquivos={("MOV", "202609"): bytes_mov},
        listar_map={"202609": ["CAGEDMOV202609.7z"]},
    )
    ocupacoes = _obter_ocupacoes_teste([cbo])

    # 1ª execução
    resumo1 = ingerir_periodo("202609", "202609", ocupacoes, tmp_path, baixador=baixador)
    assert resumo1.total_ingeridos == 1
    assert len(baixador.chamadas_download) == 1

    manifesto_txt1 = (tmp_path / "caged" / "procedencia.json").read_text(encoding="utf-8")
    registros1 = json.loads(manifesto_txt1)
    assert len(registros1) == 3  # MOV, FOR (ausente), EXC (ausente)

    # 2ª execução
    resumo2 = ingerir_periodo("202609", "202609", ocupacoes, tmp_path, baixador=baixador)
    assert resumo2.total_ingeridos == 1
    # Nenhuma nova chamada de download foi feita
    assert len(baixador.chamadas_download) == 1

    manifesto_txt2 = (tmp_path / "caged" / "procedencia.json").read_text(encoding="utf-8")
    registros2 = json.loads(manifesto_txt2)
    assert len(registros2) == 3


# ---------------------------------------------------------------------------
# 7. T02 - Republicação com hash diferente sinaliza conflito se reprocessar
# ---------------------------------------------------------------------------
def test_t02_republicacao_com_hash_diferente_sinaliza_conflito_se_reprocessar(tmp_path: Path):
    """T02: arquivo republicado com outro hash registra conflito se reprocessar=True."""
    cbo = "212405"
    linha_v1 = (
        f"202609;3;33;330455;P;8513900;1;{cbo};101;9;30;40,00;1;1;0;1;97;0;0;0;"
        "2000,00;99;0;1;202609;0;5;2000,00"
    )
    bytes_v1 = criar_7z_em_bytes("CAGEDMOV202609.txt", f"{CABECALHO_MOV}\r\n{linha_v1}\r\n")

    baixador = BaixadorFalso(arquivos={("MOV", "202609"): bytes_v1})
    ocupacoes = _obter_ocupacoes_teste([cbo])

    reg1 = ingerir_arquivo("MOV", "202609", ocupacoes, tmp_path, baixador=baixador)
    hash_v1 = reg1.sha256_7z

    # Republicação do MTE com novos dados
    linha_v2 = (
        f"202609;3;33;330455;P;8513900;1;{cbo};101;9;30;40,00;1;1;0;1;97;0;0;0;"
        "3500,00;99;0;1;202609;0;5;3500,00"
    )
    bytes_v2 = criar_7z_em_bytes("CAGEDMOV202609.txt", f"{CABECALHO_MOV}\r\n{linha_v2}\r\n")
    baixador.arquivos[("MOV", "202609")] = bytes_v2

    # Sem reprocessar: ignora alteração remota
    reg_ignorado = ingerir_arquivo(
        "MOV", "202609", ocupacoes, tmp_path, baixador=baixador, reprocessar=False
    )
    assert reg_ignorado.sha256_7z == hash_v1
    assert reg_ignorado.conflito is None

    # Com reprocessar: detecta conflito e atualiza Parquet
    reg_reprocessado = ingerir_arquivo(
        "MOV", "202609", ocupacoes, tmp_path, baixador=baixador, reprocessar=True
    )
    assert reg_reprocessado.sha256_7z != hash_v1
    assert reg_reprocessado.conflito is not None
    assert reg_reprocessado.conflito["sha256_anterior"] == hash_v1
    assert reg_reprocessado.conflito["sha256_novo"] == reg_reprocessado.sha256_7z


# ---------------------------------------------------------------------------
# 8. T01 - Fonte sem autorização de treino não é promovida
# ---------------------------------------------------------------------------
def test_t01_fonte_sem_autorizacao_treino_nao_promovida(tmp_path: Path):
    """T01: fonte com treino_autorizado=False aborta promoção e registra motivo."""
    cbo = "212405"
    baixador = BaixadorFalso()
    ocupacoes = _obter_ocupacoes_teste([cbo])
    fonte_bloqueada = Fonte(
        treino_autorizado=False,
        base_autorizacao="Termos de uso proíbem treinamento em modelos comerciais.",
    )

    resumo = ingerir_periodo(
        "202609", "202609", ocupacoes, tmp_path, baixador=baixador, fonte=fonte_bloqueada
    )

    assert resumo.sucesso is False
    assert resumo.total_nao_promovidas == 3
    assert len(baixador.chamadas_download) == 0

    parquet_dir = tmp_path / "caged" / "parquet"
    assert not list(parquet_dir.glob("*.parquet"))

    manifesto_txt = (tmp_path / "caged" / "procedencia.json").read_text(encoding="utf-8")
    for reg in json.loads(manifesto_txt):
        assert reg["situacao"] == "nao_promovida"
        assert reg["erro"] == fonte_bloqueada.base_autorizacao


# ---------------------------------------------------------------------------
# 9. Disco: espaço insuficiente (< 4 GB) aborta antes do download
# ---------------------------------------------------------------------------
def test_disco_espaco_insuficiente_aborta_antes_do_download(tmp_path: Path):
    """Disco: espaço livre abaixo de 4 GB aborta imediatamente sem download."""
    cbo = "212405"
    linha = (
        f"202609;3;33;330455;P;8513900;1;{cbo};101;9;30;40,00;1;1;0;1;97;0;0;0;"
        "2000,00;99;0;1;202609;0;5;2000,00"
    )
    bytes_mov = criar_7z_em_bytes("CAGEDMOV202609.txt", f"{CABECALHO_MOV}\r\n{linha}\r\n")
    baixador = BaixadorFalso(arquivos={("MOV", "202609"): bytes_mov})
    ocupacoes = _obter_ocupacoes_teste([cbo])

    with pytest.raises(RuntimeError, match="4 GB"):
        ingerir_periodo(
            "202609",
            "202609",
            ocupacoes,
            tmp_path,
            baixador=baixador,
            espaco_livre_gb=lambda _: 3.9,
        )

    # Nenhuma chamada de download realizada
    assert len(baixador.chamadas_download) == 0


# ---------------------------------------------------------------------------
# 10. Falha de download: registra falha, limpa bruto e continua período
# ---------------------------------------------------------------------------
def test_falha_de_download_registra_falha_apaga_bruto_e_continua_periodo(tmp_path: Path):
    """Falha de download não vira ausente_na_fonte, limpa bruto e permite outros arquivos."""
    cbo = "212405"
    linha_mov = (
        f"202609;3;33;330455;P;8513900;1;{cbo};101;9;30;40,00;1;1;0;1;97;0;0;0;"
        "2000,00;99;0;1;202609;0;5;2000,00"
    )
    bytes_mov = criar_7z_em_bytes("CAGEDMOV202609.txt", f"{CABECALHO_MOV}\r\n{linha_mov}\r\n")

    linha_exc = (
        f"202609;3;33;330455;P;8513900;1;{cbo};101;9;30;40,00;1;1;0;1;97;0;0;0;"
        "2000,00;99;0;1;202609;202609;1;0;5;2000,00"
    )
    bytes_exc = criar_7z_em_bytes("CAGEDEXC202609.txt", f"{CABECALHO_EXC}\r\n{linha_exc}\r\n")

    baixador = BaixadorFalso(
        arquivos={
            ("MOV", "202609"): bytes_mov,
            ("EXC", "202609"): bytes_exc,
        },
        listar_map={"202609": ["CAGEDMOV202609.7z", "CAGEDFOR202609.7z", "CAGEDEXC202609.7z"]},
        falhas={("FOR", "202609")},  # FOR simula falha de conexão
    )
    ocupacoes = _obter_ocupacoes_teste([cbo])

    resumo = ingerir_periodo("202609", "202609", ocupacoes, tmp_path, baixador=baixador)

    assert resumo.sucesso is False
    assert resumo.total_falhas == 1
    assert resumo.total_ingeridos == 2

    # Verifica o registro da falha no manifesto
    manifesto_txt = (tmp_path / "caged" / "procedencia.json").read_text(encoding="utf-8")
    regs = {r["tipo"]: r for r in json.loads(manifesto_txt)}
    assert regs["FOR"]["situacao"] == "falha"
    assert "Simulacao de falha de rede" in regs["FOR"]["erro"]

    # Bruto deve permanecer rigorosamente vazio
    bruto_dir = tmp_path / "caged" / "bruto"
    assert len(list(bruto_dir.iterdir())) == 0


# ---------------------------------------------------------------------------
# 11. Cabeçalho inesperado: ausência de coluna obrigatória falha nomeando coluna
# ---------------------------------------------------------------------------
def test_cabecalho_inesperado_sem_coluna_obrigatoria_falha_com_nome_da_coluna(tmp_path: Path):
    """Arquivo sem coluna obrigatória (ex: competênciadec) falha explicitamente."""
    cbo = "212405"
    # Cabeçalho sem competênciadec
    cabecalho_invalido = CABECALHO_MOV.replace("competênciadec;", "")
    linha = (
        f"202609;3;33;330455;P;8513900;1;{cbo};101;9;30;40,00;1;1;0;1;97;0;0;0;"
        "2000,00;99;0;1;0;5;2000,00"
    )
    bytes_7z = criar_7z_em_bytes("CAGEDMOV202609.txt", f"{cabecalho_invalido}\r\n{linha}\r\n")

    baixador = BaixadorFalso(arquivos={("MOV", "202609"): bytes_7z})
    ocupacoes = _obter_ocupacoes_teste([cbo])

    with pytest.raises(ValueError, match="competenciadec"):
        ingerir_arquivo("MOV", "202609", ocupacoes, tmp_path, baixador=baixador)

    # Nenhum Parquet gravado
    parquet_dir = tmp_path / "caged" / "parquet"
    assert not list(parquet_dir.glob("*.parquet"))


# ---------------------------------------------------------------------------
# 12. Lista de ocupações inválida: duplicatas ou código não numérico de 6 dígitos
# ---------------------------------------------------------------------------
def test_lista_ocupacoes_invalida_lanca_value_error(tmp_path: Path):
    """carregar_ocupacoes valida tamanho de 6 dígitos e disjunção de conjuntos."""
    # 1. Código com 5 dígitos
    json_5dig = tmp_path / "ocupacoes_5dig.json"
    json_5dig.write_text(
        json.dumps(
            {
                "versao": "v1",
                "destinos": {"d1": {"nome": "D1", "cbo6": ["12345"]}},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="6 dígitos"):
        carregar_ocupacoes(json_5dig)

    # 2. Código duplicado entre dois destinos
    json_duplicado = tmp_path / "ocupacoes_dup.json"
    json_duplicado.write_text(
        json.dumps(
            {
                "versao": "v1",
                "destinos": {
                    "d1": {"nome": "D1", "cbo6": ["123456"]},
                    "d2": {"nome": "D2", "cbo6": ["123456"]},
                },
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicado"):
        carregar_ocupacoes(json_duplicado)

    # 3. Código duplicado entre destino e reserva
    json_dup_reserva = tmp_path / "ocupacoes_reserva.json"
    json_dup_reserva.write_text(
        json.dumps(
            {
                "versao": "v1",
                "destinos": {"d1": {"nome": "D1", "cbo6": ["123456"]}},
                "cbo6_reserva": ["123456"],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicado"):
        carregar_ocupacoes(json_dup_reserva)


# ---------------------------------------------------------------------------
# 13. Coluna nova desconhecida vai para colunas_ignoradas e não para Parquet
# ---------------------------------------------------------------------------
def test_coluna_nova_desconhecida_no_cabecalho_vai_para_colunas_ignoradas(tmp_path: Path):
    """Colunas desconhecidas inseridas pelo MTE no futuro são ignoradas e auditadas."""
    cbo = "212405"
    cabecalho_com_extra = f"{CABECALHO_MOV};coluna_futura_mte"
    linha = (
        f"202609;3;33;330455;P;8513900;1;{cbo};101;9;30;40,00;1;1;0;1;97;0;0;0;"
        "2000,00;99;0;1;202609;0;5;2000,00;valor_extra"
    )
    bytes_7z = criar_7z_em_bytes("CAGEDMOV202609.txt", f"{cabecalho_com_extra}\r\n{linha}\r\n")

    baixador = BaixadorFalso(arquivos={("MOV", "202609"): bytes_7z})
    ocupacoes = _obter_ocupacoes_teste([cbo])

    reg = ingerir_arquivo("MOV", "202609", ocupacoes, tmp_path, baixador=baixador)

    assert "coluna_futura_mte" in reg.colunas_ignoradas

    df = pd.read_parquet(tmp_path / "caged" / "parquet" / "CAGEDMOV202609.parquet")
    assert "coluna_futura_mte" not in df.columns
    assert list(df.columns) == ESQUEMA_COLUNAS_ESPERADO


# ---------------------------------------------------------------------------
# 14. A1: BaixadorCurl lança RuntimeError em erro de curl e ingerir_periodo trata
# ---------------------------------------------------------------------------
def test_baixador_curl_lanca_erro_quando_o_curl_falha(monkeypatch):
    """A1: BaixadorCurl.listar_arquivos lança RuntimeError quando curl.exe retorna != 0."""
    import subprocess

    from citizentech_ml.ingestao.baixador import BaixadorCurl

    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=6,
            stdout="",
            stderr="curl: (6) Could not resolve host: host-inexistente.invalid",
        )

    monkeypatch.setattr(subprocess, "run", mock_run)
    baixador = BaixadorCurl(url_base="ftp://host-inexistente.invalid/pdet/")

    with pytest.raises(RuntimeError, match="código 6"):
        baixador.listar_arquivos("202609")


def test_falha_na_listagem_registra_falha_e_nunca_ausente_na_fonte(tmp_path: Path):
    """A1: falha na listagem de uma competência registra 'falha' e continua para a próxima."""
    cbo = "212405"
    linha = (
        f"202609;3;33;330455;P;8513900;1;{cbo};101;9;30;40,00;1;1;0;1;97;0;0;0;"
        "2000,00;99;0;1;202609;0;5;2000,00"
    )
    bytes_mov = criar_7z_em_bytes("CAGEDMOV202609.txt", f"{CABECALHO_MOV}\r\n{linha}\r\n")

    class BaixadorComFalhaListagem(BaixadorFalso):
        def listar_arquivos(self, competencia: str) -> list[str]:
            self.chamadas_listar.append(competencia)
            if competencia == "202608":
                raise RuntimeError("Falha de rede ao conectar no FTP (código 6)")
            return super().listar_arquivos(competencia)

    baixador = BaixadorComFalhaListagem(
        arquivos={("MOV", "202609"): bytes_mov},
        listar_map={"202609": ["CAGEDMOV202609.7z"]},
    )
    ocupacoes = _obter_ocupacoes_teste([cbo])

    resumo = ingerir_periodo("202608", "202609", ocupacoes, tmp_path, baixador=baixador)

    assert resumo.sucesso is False
    assert resumo.total_falhas == 3  # MOV, FOR, EXC de 202608
    assert resumo.total_ingeridos == 1  # MOV de 202609
    assert resumo.total_ausentes == 2  # FOR, EXC de 202609

    manifesto_txt = (tmp_path / "caged" / "procedencia.json").read_text(encoding="utf-8")
    regs = json.loads(manifesto_txt)
    regs_202608 = [r for r in regs if r["competencia_arquivo"] == "202608"]
    assert len(regs_202608) == 3
    for r in regs_202608:
        assert r["situacao"] == "falha"
        assert r["erro"].startswith("Falha ao listar")
        assert "ausente_na_fonte" != r["situacao"]


# ---------------------------------------------------------------------------
# 15. A2: Troca da lista de ocupações reprocessa o arquivo
# ---------------------------------------------------------------------------
def test_troca_da_lista_de_ocupacoes_reprocessa_o_arquivo(tmp_path: Path):
    """A2: reexecução com hash de ocupações diferente rebaixa, reprocessa e atualiza Parquet."""
    cbo_a = "212405"
    cbo_b = "212410"

    linha_a = (
        f"202609;3;33;330455;P;8513900;1;{cbo_a};101;9;30;40,00;1;1;0;1;97;0;0;0;"
        "2000,00;99;0;1;202609;0;5;2000,00"
    )
    linha_b = (
        f"202609;3;33;330455;P;8513900;1;{cbo_b};101;9;30;40,00;1;1;0;1;97;0;0;0;"
        "3000,00;99;0;1;202609;0;5;3000,00"
    )
    conteudo_csv = f"{CABECALHO_MOV}\r\n{linha_a}\r\n{linha_b}\r\n"
    bytes_mov = criar_7z_em_bytes("CAGEDMOV202609.txt", conteudo_csv)

    baixador = BaixadorFalso(
        arquivos={("MOV", "202609"): bytes_mov},
        listar_map={"202609": ["CAGEDMOV202609.7z"]},
    )

    ocupacoes_a = Ocupacoes(
        versao="v_a",
        destinos={"dev": {"nome": "Dev", "cbo6": [cbo_a]}},
        cbo6_reserva=[],
        codigos_ingestao={cbo_a},
        hash="hash_lista_A",
    )
    ocupacoes_b = Ocupacoes(
        versao="v_b",
        destinos={"dev": {"nome": "Dev", "cbo6": [cbo_a, cbo_b]}},
        cbo6_reserva=[],
        codigos_ingestao={cbo_a, cbo_b},
        hash="hash_lista_B",
    )

    # 1ª execução com lista A
    resumo_a = ingerir_periodo("202609", "202609", ocupacoes_a, tmp_path, baixador=baixador)
    assert resumo_a.total_ingeridos == 1
    assert len(baixador.chamadas_download) == 1

    df_parquet_a = pd.read_parquet(tmp_path / "caged" / "parquet" / "CAGEDMOV202609.parquet")
    assert len(df_parquet_a) == 1
    assert set(df_parquet_a["cbo2002_ocupacao"]) == {cbo_a}

    manifesto_a = json.loads((tmp_path / "caged" / "procedencia.json").read_text(encoding="utf-8"))
    reg_mov_a = next(r for r in manifesto_a if r["tipo"] == "MOV")
    assert reg_mov_a["hash_ocupacoes"] == "hash_lista_A"
    assert reg_mov_a.get("hash_ocupacoes_anterior") is None

    # 2ª execução com lista B (sem reprocessar=True)
    resumo_b = ingerir_periodo("202609", "202609", ocupacoes_b, tmp_path, baixador=baixador)
    assert resumo_b.total_ingeridos == 1
    # Houve novo download porque a lista mudou
    assert len(baixador.chamadas_download) == 2

    # Parquet foi substituído e agora contém os 2 CBOs
    df_parquet_b = pd.read_parquet(tmp_path / "caged" / "parquet" / "CAGEDMOV202609.parquet")
    assert len(df_parquet_b) == 2
    assert set(df_parquet_b["cbo2002_ocupacao"]) == {cbo_a, cbo_b}

    manifesto_b = json.loads((tmp_path / "caged" / "procedencia.json").read_text(encoding="utf-8"))
    reg_mov_b = next(r for r in manifesto_b if r["tipo"] == "MOV")
    assert reg_mov_b["hash_ocupacoes"] == "hash_lista_B"
    assert reg_mov_b["hash_ocupacoes_anterior"] == "hash_lista_A"


# ---------------------------------------------------------------------------
# 16. A3: Retomada não consulta a fonte nem rebaixa registro ingerido
# ---------------------------------------------------------------------------
def test_retomada_nao_consulta_a_fonte_nem_rebaixa_registro_ingerido(tmp_path: Path):
    """A3: competência com todos os tipos ingeridos faz 0 chamadas de listagem e download."""
    cbo = "212405"
    linha_mov = (
        f"202609;3;33;330455;P;8513900;1;{cbo};101;9;30;40,00;1;1;0;1;97;0;0;0;"
        "2000,00;99;0;1;202609;0;5;2000,00"
    )
    linha_for = (
        f"202609;3;33;330455;P;8513900;1;{cbo};101;9;30;40,00;1;1;0;1;97;0;0;0;"
        "2000,00;99;0;1;202609;1;5;2000,00"
    )
    linha_exc = (
        f"202609;3;33;330455;P;8513900;1;{cbo};101;9;30;40,00;1;1;0;1;97;0;0;0;"
        "2000,00;99;0;1;202609;202609;1;0;5;2000,00"
    )

    bytes_mov = criar_7z_em_bytes("CAGEDMOV202609.txt", f"{CABECALHO_MOV}\r\n{linha_mov}\r\n")
    bytes_for = criar_7z_em_bytes("CAGEDFOR202609.txt", f"{CABECALHO_MOV}\r\n{linha_for}\r\n")
    bytes_exc = criar_7z_em_bytes("CAGEDEXC202609.txt", f"{CABECALHO_EXC}\r\n{linha_exc}\r\n")

    baixador1 = BaixadorFalso(
        arquivos={
            ("MOV", "202609"): bytes_mov,
            ("FOR", "202609"): bytes_for,
            ("EXC", "202609"): bytes_exc,
        },
        listar_map={"202609": ["CAGEDMOV202609.7z", "CAGEDFOR202609.7z", "CAGEDEXC202609.7z"]},
    )
    ocupacoes = _obter_ocupacoes_teste([cbo])

    # 1ª execução completa
    resumo1 = ingerir_periodo("202609", "202609", ocupacoes, tmp_path, baixador=baixador1)
    assert resumo1.total_ingeridos == 3
    assert len(baixador1.chamadas_download) == 3

    # 2ª execução com baixador cuja listagem devolve lista vazia []
    baixador2 = BaixadorFalso(listar_map={"202609": []})
    resumo2 = ingerir_periodo("202609", "202609", ocupacoes, tmp_path, baixador=baixador2)

    # Nenhuma chamada de listagem e nenhuma chamada de download
    assert len(baixador2.chamadas_listar) == 0
    assert len(baixador2.chamadas_download) == 0
    assert resumo2.total_ingeridos == 3

    # Manifesto continua com os 3 registros como 'ingerido' (não foram sobrescritos)
    manifesto_txt = (tmp_path / "caged" / "procedencia.json").read_text(encoding="utf-8")
    regs = json.loads(manifesto_txt)
    assert len(regs) == 3
    for r in regs:
        assert r["situacao"] == "ingerido"

    # Caso B: reprocessar=True mas arquivo sumiu da listagem remota ->
    # não sobrescreve registro ingerido, mantém no manifesto e sinaliza falha no resumo
    baixador3 = BaixadorFalso(listar_map={"202609": []})
    resumo3 = ingerir_periodo(
        "202609", "202609", ocupacoes, tmp_path, baixador=baixador3, reprocessar=True
    )
    assert resumo3.sucesso is False
    assert resumo3.total_falhas == 3

    manifesto_txt3 = (tmp_path / "caged" / "procedencia.json").read_text(encoding="utf-8")
    regs3 = json.loads(manifesto_txt3)
    for r in regs3:
        assert r["situacao"] == "ingerido"


# ---------------------------------------------------------------------------
# 17. A4: Arquivo corrompido vira falha no período e a execução continua
# ---------------------------------------------------------------------------
def test_arquivo_corrompido_vira_falha_e_o_periodo_continua(tmp_path: Path):
    """A4: arquivo corrompido em uma competência vira falha e competência seguinte é processada."""
    cbo = "212405"
    bytes_corrompidos = b"BYTES_CORROMPIDOS_QUE_NAO_SAO_7Z"

    linha = (
        f"202609;3;33;330455;P;8513900;1;{cbo};101;9;30;40,00;1;1;0;1;97;0;0;0;"
        "2000,00;99;0;1;202609;0;5;2000,00"
    )
    bytes_bom = criar_7z_em_bytes("CAGEDMOV202609.txt", f"{CABECALHO_MOV}\r\n{linha}\r\n")

    baixador = BaixadorFalso(
        arquivos={
            ("MOV", "202608"): bytes_corrompidos,
            ("MOV", "202609"): bytes_bom,
        },
        listar_map={
            "202608": ["CAGEDMOV202608.7z"],
            "202609": ["CAGEDMOV202609.7z"],
        },
    )
    ocupacoes = _obter_ocupacoes_teste([cbo])

    resumo = ingerir_periodo("202608", "202609", ocupacoes, tmp_path, baixador=baixador)

    assert resumo.sucesso is False
    assert resumo.total_falhas >= 1
    assert resumo.total_ingeridos >= 1

    # Parquet de 202608 não deve existir em disco
    parquet_202608 = tmp_path / "caged" / "parquet" / "CAGEDMOV202608.parquet"
    assert not parquet_202608.exists()

    # Parquet de 202609 deve existir e estar correto
    parquet_202609 = tmp_path / "caged" / "parquet" / "CAGEDMOV202609.parquet"
    assert parquet_202609.exists()
    df_202609 = pd.read_parquet(parquet_202609)
    assert len(df_202609) == 1

    # Bruto deve permanecer rigorosamente vazio
    bruto_dir = tmp_path / "caged" / "bruto"
    assert len(list(bruto_dir.iterdir())) == 0

    # Manifesto registra 'falha' em 202608 com tipo e mensagem da exceção
    manifesto_txt = (tmp_path / "caged" / "procedencia.json").read_text(encoding="utf-8")
    regs = json.loads(manifesto_txt)
    reg_202608_mov = next(
        r for r in regs if r["competencia_arquivo"] == "202608" and r["tipo"] == "MOV"
    )
    assert reg_202608_mov["situacao"] == "falha"
    assert "Bad7zFile" in reg_202608_mov["erro"] or "Error" in reg_202608_mov["erro"]
    assert reg_202608_mov["linhas_lidas"] == 0
    assert reg_202608_mov["linhas_gravadas"] == 0


# ---------------------------------------------------------------------------
# 18. A5: Gravação atômica de Parquet preserva arquivo anterior e limpa .tmp
# ---------------------------------------------------------------------------
def test_falha_ao_gravar_parquet_preserva_o_parquet_anterior(tmp_path: Path, monkeypatch):
    """A5: falha ao gravar Parquet preserva o Parquet anterior intacto e não deixa .tmp."""
    cbo = "212405"
    linha = (
        f"202609;3;33;330455;P;8513900;1;{cbo};101;9;30;40,00;1;1;0;1;97;0;0;0;"
        "2000,00;99;0;1;202609;0;5;2000,00"
    )
    bytes_mov = criar_7z_em_bytes("CAGEDMOV202609.txt", f"{CABECALHO_MOV}\r\n{linha}\r\n")
    baixador = BaixadorFalso(
        arquivos={("MOV", "202609"): bytes_mov},
        listar_map={"202609": ["CAGEDMOV202609.7z"]},
    )
    ocupacoes = _obter_ocupacoes_teste([cbo])

    # 1. Ingestão inicial bem-sucedida
    reg1 = ingerir_arquivo("MOV", "202609", ocupacoes, tmp_path, baixador=baixador)
    assert reg1.situacao == "ingerido"
    caminho_parquet = tmp_path / "caged" / "parquet" / "CAGEDMOV202609.parquet"
    assert caminho_parquet.exists()
    df_anterior = pd.read_parquet(caminho_parquet)
    assert len(df_anterior) == 1

    # 2. Mock de to_parquet que escreve dados corrompidos e lança erro
    def mock_to_parquet_falho(self, path, *args, **kwargs):
        Path(path).write_bytes(b"DADOS_CORROMPIDOS_TRUNCADOS")
        raise OSError("Falha simulada durante escrita em disco")

    monkeypatch.setattr(pd.DataFrame, "to_parquet", mock_to_parquet_falho)

    # 3. Reprocessamento que falha
    with pytest.raises(OSError, match="Falha simulada"):
        ingerir_arquivo(
            "MOV", "202609", ocupacoes, tmp_path, baixador=baixador, reprocessar=True
        )

    # 4. Parquet anterior deve permanecer legível e idêntico
    assert caminho_parquet.exists()
    df_preservado = pd.read_parquet(caminho_parquet)
    pd.testing.assert_frame_equal(df_anterior, df_preservado)

    # 5. Nenhum arquivo .tmp na pasta parquet
    tmps = list((tmp_path / "caged" / "parquet").glob("*.tmp"))
    assert tmps == []


# ---------------------------------------------------------------------------
# 19. A6: CLI e ingerir_periodo registram/imprimem cada arquivo assim que processa
# ---------------------------------------------------------------------------
def test_cli_imprime_cada_arquivo_assim_que_processa(tmp_path: Path, monkeypatch, capsys):
    """A6: ao_registrar entrega o 1º arquivo antes do download do 2º; CLI imprime ao vivo."""
    cbo = "212405"
    linha = (
        f"202609;3;33;330455;P;8513900;1;{cbo};101;9;30;40,00;1;1;0;1;97;0;0;0;"
        "2000,00;99;0;1;202609;0;5;2000,00"
    )
    bytes_mov = criar_7z_em_bytes("CAGEDMOV202609.txt", f"{CABECALHO_MOV}\r\n{linha}\r\n")
    bytes_for = criar_7z_em_bytes("CAGEDFOR202609.txt", f"{CABECALHO_MOV}\r\n{linha}\r\n")

    eventos: list[tuple[str, str, str]] = []

    class BaixadorInstrumentado(BaixadorFalso):
        def baixar_arquivo(self, tipo: str, competencia: str, destino: Path) -> Path:
            eventos.append(("download", tipo, competencia))
            return super().baixar_arquivo(tipo, competencia, destino)

    baixador = BaixadorInstrumentado(
        arquivos={
            ("MOV", "202609"): bytes_mov,
            ("FOR", "202609"): bytes_for,
        },
        listar_map={"202609": ["CAGEDMOV202609.7z", "CAGEDFOR202609.7z"]},
    )
    ocupacoes = _obter_ocupacoes_teste([cbo])

    def callback_registro(reg):
        eventos.append(("registro", reg.tipo, reg.competencia_arquivo))

    ingerir_periodo(
        "202609",
        "202609",
        ocupacoes,
        tmp_path,
        baixador=baixador,
        ao_registrar=callback_registro,
    )

    # O registro do primeiro arquivo (MOV) deve ser entregue antes do download do segundo (FOR)
    idx_reg_mov = eventos.index(("registro", "MOV", "202609"))
    idx_down_for = eventos.index(("download", "FOR", "202609"))
    assert idx_reg_mov < idx_down_for

    # Validação da CLI: em aborto, linhas já processadas foram impressas no stdout
    json_ocupacoes = tmp_path / "ocupacoes.json"
    json_ocupacoes.write_text(
        json.dumps(
            {
                "versao": "teste-v1",
                "destinos": {"dev": {"nome": "Dev", "cbo6": [cbo]}},
                "cbo6_reserva": [],
            }
        ),
        encoding="utf-8",
    )

    baixador_aborto = BaixadorFalso(
        arquivos={("MOV", "202608"): bytes_mov},
        listar_map={"202608": ["CAGEDMOV202608.7z"]},
    )
    monkeypatch.setattr(
        "citizentech_ml.ingestao.ingestor.BaixadorCurl", lambda *args, **kwargs: baixador_aborto
    )

    chamadas_disco = 0

    def mock_disco(dir_dados, fn):
        nonlocal chamadas_disco
        chamadas_disco += 1
        if chamadas_disco > 1:
            raise RuntimeError("Espaço livre em disco (2.0 GB) abaixo do limite de 4 GB exigido.")
        return 10.0

    monkeypatch.setattr("citizentech_ml.ingestao.ingestor._verificar_espaco_disco", mock_disco)

    dir_dados_aborto = tmp_path / "dados_aborto"
    args = [
        "--ocupacoes",
        str(json_ocupacoes),
        "--inicio",
        "202608",
        "--fim",
        "202609",
        "--dados",
        str(dir_dados_aborto),
    ]

    ret = cli_main(args)
    assert ret == 1
    stdout_aborto = capsys.readouterr().out
    # A linha do MOV de 202608 já processado antes do aborto deve estar impressa no stdout
    assert "MOV 202608 | lidas:" in stdout_aborto

