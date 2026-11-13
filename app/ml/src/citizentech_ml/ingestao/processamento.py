"""Processamento, filtragem e conversão de microdados do Novo Caged para Parquet."""

import unicodedata
from pathlib import Path

import pandas as pd

COLUNAS_ESQUEMA_PARQUET = [
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

MAPA_COLUNAS_ORIGEM = {
    "competenciamov": "competencia_mov",
    "regiao": "regiao",
    "uf": "uf",
    "municipio": "municipio",
    "secao": "secao",
    "subclasse": "subclasse",
    "saldomovimentacao": "saldo_movimentacao",
    "cbo2002ocupacao": "cbo2002_ocupacao",
    "categoria": "categoria",
    "graudeinstrucao": "grau_instrucao",
    "horascontratuais": "horas_contratuais",
    "tipoempregador": "tipo_empregador",
    "tipoestabelecimento": "tipo_estabelecimento",
    "tipomovimentacao": "tipo_movimentacao",
    "indtrabintermitente": "ind_trab_intermitente",
    "indtrabparcial": "ind_trab_parcial",
    "salario": "salario",
    "tamestabjan": "tam_estab_jan",
    "indicadoraprendiz": "indicador_aprendiz",
    "origemdainformacao": "origem_informacao",
    "competenciadec": "competencia_dec",
    "indicadordeforadoprazo": "indicador_fora_prazo",
    "unidadesalariocodigo": "unidade_salario_codigo",
    "valorsalariofixo": "valor_salario_fixo",
    "competenciaexc": "competencia_exc",
    "indicadordeexclusao": "indicador_exclusao",
}

COLUNAS_OBRIGATORIAS_BASE = {
    "competenciamov",
    "regiao",
    "uf",
    "municipio",
    "secao",
    "subclasse",
    "saldomovimentacao",
    "cbo2002ocupacao",
    "categoria",
    "graudeinstrucao",
    "horascontratuais",
    "tipoempregador",
    "tipoestabelecimento",
    "tipomovimentacao",
    "indtrabintermitente",
    "indtrabparcial",
    "salario",
    "tamestabjan",
    "indicadoraprendiz",
    "origemdainformacao",
    "competenciadec",
    "indicadordeforadoprazo",
    "unidadesalariocodigo",
    "valorsalariofixo",
}

COLUNAS_OBRIGATORIAS_EXC = COLUNAS_OBRIGATORIAS_BASE | {
    "competenciaexc",
    "indicadordeexclusao",
}

COLUNAS_SENSIVEIS_NORMALIZADAS = {
    "idade",
    "sexo",
    "racacor",
    "tipodedeficiencia",
}


def normalizar_identificador(texto: str) -> str:
    """Remove acentuação, espaços e formata em minúsculas."""
    nfkd = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in nfkd if not unicodedata.combining(c))
    return sem_acento.lower().replace(" ", "").replace("_", "").replace("-", "").strip()


def analisar_cabecalho(
    linha_cabecalho: str, tipo: str
) -> tuple[dict[str, str], list[str], list[str]]:
    """Analisa o cabeçalho original do arquivo .txt.

    Retorna:
    - mapa_renomear: dict[coluna_original, nome_parquet]
    - descartadas_sensiveis: list[str] com os nomes originais sensíveis encontrados
    - ignoradas: list[str] com nomes de colunas desconhecidas
    """
    colunas_originais = [
        c.strip().strip("\ufeff") for c in linha_cabecalho.split(";") if c.strip()
    ]
    mapa_normalizado: dict[str, str] = {
        normalizar_identificador(c): c for c in colunas_originais
    }

    obrigatorias = COLUNAS_OBRIGATORIAS_EXC if tipo.upper() == "EXC" else COLUNAS_OBRIGATORIAS_BASE

    for col_obrig in obrigatorias:
        if col_obrig not in mapa_normalizado:
            raise ValueError(f"Coluna obrigatória ausente no cabeçalho: '{col_obrig}'")

    mapa_renomear: dict[str, str] = {}
    descartadas_sensiveis: list[str] = []
    ignoradas: list[str] = []

    for col_orig in colunas_originais:
        norm = normalizar_identificador(col_orig)
        if norm in COLUNAS_SENSIVEIS_NORMALIZADAS:
            descartadas_sensiveis.append(col_orig)
        elif norm in MAPA_COLUNAS_ORIGEM:
            mapa_renomear[col_orig] = MAPA_COLUNAS_ORIGEM[norm]
        else:
            ignoradas.append(col_orig)

    return mapa_renomear, descartadas_sensiveis, ignoradas


def processar_txt_para_parquet(
    caminho_txt: Path,
    caminho_parquet: Path,
    tipo: str,
    competencia: str,
    cbos_permitidos: set[str],
    chunksize: int = 100_000,
) -> tuple[int, int, list[str], list[str]]:
    """Lê o arquivo .txt em chunks, aplica lista de permissão e grava em Parquet.

    Retorna:
    (linhas_lidas, linhas_gravadas, descartadas_sensiveis, ignoradas)
    """
    with caminho_txt.open("r", encoding="utf-8") as f:
        linha_cabecalho = f.readline()

    if not linha_cabecalho.strip():
        raise ValueError("Arquivo .txt está vazio ou sem cabeçalho.")

    mapa_renomear, descartadas_sensiveis, ignoradas = analisar_cabecalho(linha_cabecalho, tipo)
    colunas_permitidas = list(mapa_renomear.keys())

    linhas_lidas = 0
    chunks_filtrados: list[pd.DataFrame] = []

    # Leitura em blocos utilizando somente colunas permitidas (minimização e usecols)
    for chunk in pd.read_csv(
        caminho_txt,
        sep=";",
        encoding="utf-8",
        dtype=str,
        usecols=colunas_permitidas,
        chunksize=chunksize,
        na_filter=False,
    ):
        linhas_lidas += len(chunk)
        chunk = chunk.rename(columns=mapa_renomear)

        # Filtro estrito pelas ocupações CBO dos destinos e reserva
        chunk_filtrado = chunk[chunk["cbo2002_ocupacao"].isin(cbos_permitidos)]
        if not chunk_filtrado.empty:
            chunks_filtrados.append(chunk_filtrado.copy())

    if chunks_filtrados:
        df = pd.concat(chunks_filtrados, ignore_index=True)
    else:
        df = pd.DataFrame(columns=[mapa_renomear[c] for c in colunas_permitidas])

    # Inserção de colunas exclusivas ou metadados
    if tipo.upper() == "EXC":
        df["competencia_exc"] = df["competencia_exc"].astype("string")
        df["indicador_exclusao"] = pd.to_numeric(df["indicador_exclusao"], errors="coerce").astype(
            "Int16"
        )
    else:
        df["competencia_exc"] = pd.Series(None, index=df.index, dtype="string")
        df["indicador_exclusao"] = pd.Series(pd.NA, index=df.index, dtype="Int16")

    df["arquivo_tipo"] = tipo.upper()
    df["competencia_arquivo"] = str(competencia)

    # Conversão de tipos estrita
    df["saldo_movimentacao"] = pd.to_numeric(df["saldo_movimentacao"], errors="coerce").astype(
        "int8"
    )

    colunas_string = [
        "competencia_mov",
        "regiao",
        "uf",
        "municipio",
        "secao",
        "subclasse",
        "cbo2002_ocupacao",
        "competencia_dec",
        "competencia_exc",
        "arquivo_tipo",
        "competencia_arquivo",
    ]
    for col in colunas_string:
        df[col] = df[col].astype("string")

    colunas_int16 = [
        "categoria",
        "grau_instrucao",
        "tipo_empregador",
        "tipo_estabelecimento",
        "tipo_movimentacao",
        "ind_trab_intermitente",
        "ind_trab_parcial",
        "indicador_aprendiz",
        "tam_estab_jan",
        "origem_informacao",
        "unidade_salario_codigo",
        "indicador_fora_prazo",
        "indicador_exclusao",
    ]
    for col in colunas_int16:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int16")

    # Tratamento de decimais com vírgula e nulos para salários e horas
    colunas_float = ["horas_contratuais", "salario", "valor_salario_fixo"]
    for col in colunas_float:
        serie_limpa = df[col].astype(str).str.strip().str.replace(",", ".")
        serie_limpa = serie_limpa.replace({"": None, "nan": None, "None": None, "<NA>": None})
        df[col] = pd.to_numeric(serie_limpa, errors="coerce").astype("float64")

    # Reordenação exata segundo o esquema
    df = df[COLUNAS_ESQUEMA_PARQUET]

    caminho_parquet.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(caminho_parquet, index=False, engine="pyarrow")
    linhas_gravadas = len(df)

    return linhas_lidas, linhas_gravadas, descartadas_sensiveis, ignoradas
