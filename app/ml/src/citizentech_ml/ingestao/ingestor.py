"""Ingestão e processamento de arquivos do Novo Caged."""

import hashlib
import shutil
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import py7zr

from citizentech_ml.ingestao.baixador import Baixador, BaixadorCurl
from citizentech_ml.ingestao.manifesto import (
    carregar_manifesto,
    obter_registro,
    upsert_registro,
)
from citizentech_ml.ingestao.modelos import (
    Fonte,
    Ocupacoes,
    RegistroProcedencia,
    ResumoIngestao,
)
from citizentech_ml.ingestao.processamento import processar_txt_para_parquet

TRANSFORMACOES_PADRAO = [
    "Filtro por lista de CBOs dos destinos e reserva",
    "Descarte preventivo de atributos sensíveis na leitura via usecols",
    "Conversao para formato Parquet com esquema tipado",
]


class EspacoInsuficiente(RuntimeError):
    """Espaco livre abaixo do limite: a ingestao inteira aborta (nao e falha de um arquivo)."""


def _limpar_diretorio(diretorio: Path) -> None:
    """Remove todo o conteúdo de um diretório mantendo o diretório vazio."""
    if not diretorio.exists():
        diretorio.mkdir(parents=True, exist_ok=True)
        return
    for item in diretorio.iterdir():
        if item.is_file() or item.is_symlink():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)


def _gerar_intervalo_competencias(inicio: str, fim: str) -> list[str]:
    """Gera lista de competências AAAAMM entre inicio e fim inclusive."""
    ano_inicio, mes_inicio = int(inicio[:4]), int(inicio[4:])
    ano_fim, mes_fim = int(fim[:4]), int(fim[4:])

    resultado: list[str] = []
    ano, mes = ano_inicio, mes_inicio
    while (ano < ano_fim) or (ano == ano_fim and mes <= mes_fim):
        resultado.append(f"{ano:04d}{mes:02d}")
        mes += 1
        if mes > 12:
            mes = 1
            ano += 1
    return resultado


def _verificar_espaco_disco(
    dir_dados: Path, espaco_livre_gb: Callable[[Path], float] | None
) -> float:
    """Verifica espaço livre em GB e aborta se < 4.0 GB."""
    if espaco_livre_gb is not None:
        livre = espaco_livre_gb(dir_dados)
    else:
        uso = shutil.disk_usage(dir_dados)
        livre = uso.free / (1024**3)

    if livre < 4.0:
        raise EspacoInsuficiente(
            f"Espaço livre em disco ({livre:.2f} GB) abaixo do limite de 4 GB exigido. "
            "Ingestão abortada."
        )
    return livre


def ingerir_arquivo(
    tipo: str,
    competencia: str,
    ocupacoes: Ocupacoes,
    dir_dados: str | Path,
    baixador: Baixador | None = None,
    fonte: Fonte | None = None,
    reprocessar: bool = False,
) -> RegistroProcedencia:
    """Processa um único arquivo de movimentações do Novo Caged."""
    dir_dados_path = Path(dir_dados)
    caged_dir = dir_dados_path / "caged"
    bruto_dir = caged_dir / "bruto"
    parquet_dir = caged_dir / "parquet"
    manifesto_path = caged_dir / "procedencia.json"

    bruto_dir.mkdir(parents=True, exist_ok=True)
    parquet_dir.mkdir(parents=True, exist_ok=True)

    if fonte is None:
        fonte = Fonte()

    tipo_upper = tipo.upper()
    nome_7z = f"CAGED{tipo_upper}{competencia}.7z"
    caminho_7z = bruto_dir / nome_7z
    caminho_parquet = parquet_dir / f"CAGED{tipo_upper}{competencia}.parquet"
    ano = competencia[:4]
    url_arquivo = f"{fonte.url_base.rstrip('/')}/{ano}/{competencia}/{nome_7z}"

    # Retomada se já ingerido e Parquet presente com mesmo hash de ocupações
    manifesto = carregar_manifesto(manifesto_path)
    registro_previo = obter_registro(manifesto, tipo_upper, competencia)
    mesmo_hash = (
        registro_previo is not None
        and registro_previo.hash_ocupacoes == ocupacoes.hash
    )
    if (
        not reprocessar
        and mesmo_hash
        and registro_previo.situacao == "ingerido"
        and caminho_parquet.exists()
    ):
        return registro_previo

    if baixador is None:
        baixador = BaixadorCurl(url_base=fonte.url_base)

    try:
        # 1. Download
        try:
            baixador.baixar_arquivo(tipo_upper, competencia, caminho_7z)
        except Exception as exc_down:
            registro_falha = RegistroProcedencia(
                fonte=fonte.id,
                url=url_arquivo,
                arquivo=nome_7z,
                tipo=tipo_upper,
                competencia_arquivo=competencia,
                situacao="falha",
                hash_ocupacoes=ocupacoes.hash,
                versao_ocupacoes=ocupacoes.versao,
                erro=f"Falha de download: {exc_down}",
                transformacoes=TRANSFORMACOES_PADRAO,
            )
            upsert_registro(manifesto_path, registro_falha)
            return registro_falha

        bytes_7z_raw = caminho_7z.read_bytes()
        sha256_7z = hashlib.sha256(bytes_7z_raw).hexdigest()
        tamanho_7z = len(bytes_7z_raw)

        conflito = None
        if registro_previo is not None and registro_previo.sha256_7z:
            if registro_previo.sha256_7z != sha256_7z:
                conflito = {
                    "sha256_anterior": registro_previo.sha256_7z,
                    "sha256_novo": sha256_7z,
                    "detectado_em": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                }

        # 2. Extração
        subpasta_extrair = bruto_dir / f"extraido_{tipo_upper}_{competencia}"
        subpasta_extrair.mkdir(parents=True, exist_ok=True)
        with py7zr.SevenZipFile(caminho_7z, mode="r") as z:
            z.extractall(path=subpasta_extrair)

        txts = list(subpasta_extrair.glob("*.txt"))
        if not txts:
            raise FileNotFoundError(f"Nenhum arquivo .txt encontrado após extração de {nome_7z}")
        caminho_txt = txts[0]

        # 3. Processamento para Parquet
        lidas, gravadas, descartadas, ignoradas = processar_txt_para_parquet(
            caminho_txt=caminho_txt,
            caminho_parquet=caminho_parquet,
            tipo=tipo_upper,
            competencia=competencia,
            cbos_permitidos=ocupacoes.codigos_ingestao,
        )

        hash_ocupacoes_anterior = (
            registro_previo.hash_ocupacoes
            if (registro_previo is not None and registro_previo.hash_ocupacoes != ocupacoes.hash)
            else None
        )

        registro = RegistroProcedencia(
            fonte=fonte.id,
            url=url_arquivo,
            arquivo=nome_7z,
            tipo=tipo_upper,
            competencia_arquivo=competencia,
            situacao="ingerido",
            sha256_7z=sha256_7z,
            bytes_7z=tamanho_7z,
            coletado_em=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            linhas_lidas=lidas,
            linhas_gravadas=gravadas,
            colunas_descartadas_sensiveis=descartadas,
            colunas_ignoradas=ignoradas,
            hash_ocupacoes=ocupacoes.hash,
            hash_ocupacoes_anterior=hash_ocupacoes_anterior,
            versao_ocupacoes=ocupacoes.versao,
            transformacoes=TRANSFORMACOES_PADRAO,
            conflito=conflito,
        )
        upsert_registro(manifesto_path, registro)
        return registro

    finally:
        # Garante limpeza completa de bruto após cada arquivo
        _limpar_diretorio(bruto_dir)


def ingerir_periodo(
    inicio: str,
    fim: str,
    ocupacoes: Ocupacoes,
    dir_dados: str | Path,
    baixador: Baixador | None = None,
    fonte: Fonte | None = None,
    espaco_livre_gb: Callable[[Path], float] | None = None,
    reprocessar: bool = False,
    ao_registrar: Callable[[RegistroProcedencia], None] | None = None,
) -> ResumoIngestao:
    """Percorre as competências entre inicio e fim realizando a ingestão."""
    dir_dados_path = Path(dir_dados)
    caged_dir = dir_dados_path / "caged"
    parquet_dir = caged_dir / "parquet"
    manifesto_path = caged_dir / "procedencia.json"
    caged_dir.mkdir(parents=True, exist_ok=True)
    parquet_dir.mkdir(parents=True, exist_ok=True)

    if fonte is None:
        fonte = Fonte()

    resumo = ResumoIngestao()
    competencias = _gerar_intervalo_competencias(inicio, fim)
    tipos = ["MOV", "FOR", "EXC"]

    # Comportamento T01: se treino não autorizado, não promove
    if not fonte.treino_autorizado:
        resumo.sucesso = False
        resumo.erro = fonte.base_autorizacao
        for comp in competencias:
            for t in tipos:
                nome_7z = f"CAGED{t}{comp}.7z"
                ano = comp[:4]
                url_arq = f"{fonte.url_base.rstrip('/')}/{ano}/{comp}/{nome_7z}"
                reg = RegistroProcedencia(
                    fonte=fonte.id,
                    url=url_arq,
                    arquivo=nome_7z,
                    tipo=t,
                    competencia_arquivo=comp,
                    situacao="nao_promovida",
                    erro=fonte.base_autorizacao,
                    hash_ocupacoes=ocupacoes.hash,
                    versao_ocupacoes=ocupacoes.versao,
                    transformacoes=TRANSFORMACOES_PADRAO,
                )
                upsert_registro(manifesto_path, reg)
                resumo.registros.append(reg)
                resumo.total_processados += 1
                resumo.total_nao_promovidas += 1
                if ao_registrar is not None:
                    ao_registrar(reg)
        return resumo

    if baixador is None:
        baixador = BaixadorCurl(url_base=fonte.url_base)

    for comp in competencias:
        manifesto = carregar_manifesto(manifesto_path)

        tipos_a_processar: list[str] = []
        for t in tipos:
            caminho_parquet = parquet_dir / f"CAGED{t}{comp}.parquet"
            reg_previo = obter_registro(manifesto, t, comp)
            ja_ingerido = (
                not reprocessar
                and reg_previo is not None
                and reg_previo.situacao == "ingerido"
                and reg_previo.hash_ocupacoes == ocupacoes.hash
                and caminho_parquet.exists()
            )
            if ja_ingerido and reg_previo is not None:
                resumo.registros.append(reg_previo)
                resumo.total_processados += 1
                resumo.total_ingeridos += 1
                resumo.total_linhas_lidas += reg_previo.linhas_lidas
                resumo.total_linhas_gravadas += reg_previo.linhas_gravadas
                if ao_registrar is not None:
                    ao_registrar(reg_previo)
            else:
                tipos_a_processar.append(t)

        if not tipos_a_processar:
            continue

        # Disco: aborta antes de qualquer download se < 4 GB
        _verificar_espaco_disco(dir_dados_path, espaco_livre_gb)

        try:
            arquivos_na_fonte = [a.upper() for a in baixador.listar_arquivos(comp)]
        except Exception as exc_list:
            resumo.sucesso = False
            for t in tipos_a_processar:
                ano = comp[:4]
                nome_7z = f"CAGED{t}{comp}.7z"
                url_arq = f"{fonte.url_base.rstrip('/')}/{ano}/{comp}/{nome_7z}"
                reg_falha = RegistroProcedencia(
                    fonte=fonte.id,
                    url=url_arq,
                    arquivo=nome_7z,
                    tipo=t,
                    competencia_arquivo=comp,
                    situacao="falha",
                    erro=f"Falha ao listar: {exc_list}",
                    hash_ocupacoes=ocupacoes.hash,
                    versao_ocupacoes=ocupacoes.versao,
                    transformacoes=TRANSFORMACOES_PADRAO,
                )
                upsert_registro(manifesto_path, reg_falha)
                resumo.registros.append(reg_falha)
                resumo.total_processados += 1
                resumo.total_falhas += 1
                if ao_registrar is not None:
                    ao_registrar(reg_falha)
            continue

        for t in tipos_a_processar:
            resumo.total_processados += 1
            nome_esperado = f"CAGED{t}{comp}.7z".upper()
            caminho_parquet = parquet_dir / f"CAGED{t}{comp}.parquet"
            reg_previo = obter_registro(manifesto, t, comp)

            # Se o arquivo não existir na fonte remota
            if nome_esperado not in arquivos_na_fonte:
                parquet_existe = caminho_parquet.exists()
                era_ingerido = (
                    reg_previo is not None
                    and reg_previo.situacao == "ingerido"
                    and parquet_existe
                )
                if era_ingerido and reg_previo is not None:
                    # Um registro ingerido cujo Parquet existe nunca é sobrescrito
                    resumo.registros.append(reg_previo)
                    resumo.total_falhas += 1
                    resumo.sucesso = False
                    if ao_registrar is not None:
                        ao_registrar(reg_previo)
                    continue

                ano = comp[:4]
                url_arq = f"{fonte.url_base.rstrip('/')}/{ano}/{comp}/CAGED{t}{comp}.7z"
                reg_ausente = RegistroProcedencia(
                    fonte=fonte.id,
                    url=url_arq,
                    arquivo=f"CAGED{t}{comp}.7z",
                    tipo=t,
                    competencia_arquivo=comp,
                    situacao="ausente_na_fonte",
                    hash_ocupacoes=ocupacoes.hash,
                    versao_ocupacoes=ocupacoes.versao,
                    transformacoes=TRANSFORMACOES_PADRAO,
                )
                upsert_registro(manifesto_path, reg_ausente)
                resumo.registros.append(reg_ausente)
                resumo.total_ausentes += 1
                if ao_registrar is not None:
                    ao_registrar(reg_ausente)
                continue

            # Processa o arquivo
            try:
                reg = ingerir_arquivo(
                    tipo=t,
                    competencia=comp,
                    ocupacoes=ocupacoes,
                    dir_dados=dir_dados_path,
                    baixador=baixador,
                    fonte=fonte,
                    reprocessar=reprocessar,
                )
            except EspacoInsuficiente:
                raise
            except Exception as exc_proc:
                if caminho_parquet.exists():
                    caminho_parquet.unlink()
                bruto_dir = caged_dir / "bruto"
                _limpar_diretorio(bruto_dir)

                ano = comp[:4]
                url_arq = f"{fonte.url_base.rstrip('/')}/{ano}/{comp}/CAGED{t}{comp}.7z"
                reg = RegistroProcedencia(
                    fonte=fonte.id,
                    url=url_arq,
                    arquivo=f"CAGED{t}{comp}.7z",
                    tipo=t,
                    competencia_arquivo=comp,
                    situacao="falha",
                    hash_ocupacoes=ocupacoes.hash,
                    versao_ocupacoes=ocupacoes.versao,
                    transformacoes=TRANSFORMACOES_PADRAO,
                    erro=f"{type(exc_proc).__name__}: {exc_proc}",
                )
                upsert_registro(manifesto_path, reg)

            resumo.registros.append(reg)
            if ao_registrar is not None:
                ao_registrar(reg)

            if reg.situacao == "ingerido":
                resumo.total_ingeridos += 1
                resumo.total_linhas_lidas += reg.linhas_lidas
                resumo.total_linhas_gravadas += reg.linhas_gravadas
            elif reg.situacao == "falha":
                resumo.total_falhas += 1
                resumo.sucesso = False

    return resumo
