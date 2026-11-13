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
