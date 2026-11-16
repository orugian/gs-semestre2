"""Leitor seguro e agregação da base municipal anual (2024-2025)."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

COLUNAS_MINIMAS: list[str] = [
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

MESES_CANONICOS: list[str] = [f"{ano}{mes:02d}" for ano in (2024, 2025) for mes in range(1, 13)]
TIPOS_CANONICOS: list[str] = ["MOV", "FOR", "EXC"]

SEIS_DESTINOS_OFICIAIS: set[str] = {
    "analista_dados_bi",
    "analista_monitoramento_iot",
    "analista_processos",
    "gerente_projetos_produto",
    "analista_suporte_infra",
    "desenvolvedor_sistemas",
}

GRAUS_SUPERIOR: set[int] = {9, 10, 11, 80}
GRAUS_VALIDOS: set[int] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 80, 99}


def _calcular_sha256(caminho: Path) -> str:
    """Calcula hash SHA256 de um arquivo."""
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def validar_mapa_destinos(mapa: dict[str, Any]) -> dict[str, str]:
    """Valida o mapa sintético/oficial de ocupações e extrai CBO6 -> destino.

    Regras:
    - Obrigatório, exatamente os 6 destinos oficiais sem abrir catálogo externo.
    - Conjuntos não-vazios e disjuntos de CBO6 (string de 6 dígitos).
    - Reserva CBO6 opcional deve ser disjunta de todos os destinos.
    """
    if not isinstance(mapa, dict):
        raise TypeError("Mapa de destinos deve ser um dicionário.")

    destinos_dict = mapa.get("destinos")
    if not isinstance(destinos_dict, dict):
        raise ValueError("Mapa deve conter a chave 'destinos' com um dicionário.")

    chaves_destinos = set(destinos_dict.keys())
    if chaves_destinos != SEIS_DESTINOS_OFICIAIS:
        faltantes = SEIS_DESTINOS_OFICIAIS - chaves_destinos
        extras = chaves_destinos - SEIS_DESTINOS_OFICIAIS
        raise ValueError(
            f"Mapa deve conter exatamente 6 destinos oficiais. "
            f"Faltantes: {sorted(faltantes)}, Extras: {sorted(extras)}"
        )

    mapa_cbo: dict[str, str] = {}
    for dest_id, info in destinos_dict.items():
        if not isinstance(info, dict) or "cbo6" not in info:
            raise ValueError(f"Destino '{dest_id}' deve conter a chave 'cbo6'.")
        cbos = info["cbo6"]
        if not isinstance(cbos, list) or len(cbos) == 0:
            raise ValueError(f"Destino '{dest_id}' possui lista 'cbo6' vazia ou inválida.")

        for cbo in cbos:
            if isinstance(cbo, bool) or cbo is None:
                raise ValueError(f"CBO inválido no destino '{dest_id}': {cbo!r}")
            cbo_str = str(cbo).strip()
            if len(cbo_str) != 6 or not cbo_str.isdigit():
                raise ValueError(
                    f"CBO deve conter 6 dígitos numéricos: {cbo!r} no destino '{dest_id}'"
                )
            if cbo_str in mapa_cbo:
                raise ValueError(
                    f"CBO {cbo_str} atribuído a múltiplos destinos: "
                    f"'{mapa_cbo[cbo_str]}' e '{dest_id}'"
                )
            mapa_cbo[cbo_str] = dest_id

    # Reserva opcional
    reserva = mapa.get("cbo6_reserva", [])
    if reserva:
        for cbo_res in reserva:
            cbo_res_str = str(cbo_res).strip()
            if cbo_res_str in mapa_cbo:
                raise ValueError(
                    f"CBO de reserva {cbo_res_str} sobrepõe o destino '{mapa_cbo[cbo_res_str]}'"
                )

    return mapa_cbo


def planejar_fontes_municipais(dir_parquet: str | Path) -> list[Path]:
    """Planeja e valida os 72 caminhos canônicos 202401-202512 x MOV/FOR/EXC."""
    dir_path = Path(dir_parquet).resolve()
    if not dir_path.exists() or not dir_path.is_dir():
        raise FileNotFoundError(f"Diretório de parquets não encontrado: {dir_parquet}")

    caminhos: list[Path] = []
    nomes_vistos: set[str] = set()

    for comp in MESES_CANONICOS:
        for tipo in TIPOS_CANONICOS:
            nome_esperado = f"CAGED{tipo}{comp}.parquet"
            if nome_esperado in nomes_vistos:
                raise ValueError(f"Fonte duplicada detectada: {nome_esperado}")
            nomes_vistos.add(nome_esperado)

            caminho_esperado = dir_path / nome_esperado

            if ".." in caminho_esperado.parts:
                raise ValueError(f"Caminho com escape não permitido: {caminho_esperado}")
            if caminho_esperado.is_symlink():
                raise ValueError(f"Symlinks e aliases são proibidos: {caminho_esperado}")
            if not caminho_esperado.exists() or not caminho_esperado.is_file():
                raise FileNotFoundError(
                    f"Erro de cobertura: arquivo canônico ausente: {nome_esperado}"
                )
            if caminho_esperado.stat().st_nlink > 1:
                raise ValueError(f"Hardlinks e aliases sao proibidos: {nome_esperado}")
            if caminho_esperado.resolve().parent != dir_path:
                raise ValueError(f"Desvio de raiz proibido para o arquivo: {nome_esperado}")

            caminhos.append(caminho_esperado)

    if len(caminhos) != 72:
        raise ValueError(f"Cobertura incompleta: esperados 72 arquivos, obtidos {len(caminhos)}")

    return caminhos


def _validar_competencia_str(comp: Any, nome_campo: str) -> str:
    """Valida formato YYYYMM rigoroso e proíbe anos >= 2026."""
    if isinstance(comp, bool) or comp is None:
        raise ValueError(f"Campo '{nome_campo}' nulo ou booleano inválido: {comp!r}")
    s = str(comp).strip()
    if len(s) != 6 or not s.isdigit():
        raise ValueError(f"Campo '{nome_campo}' deve ter 6 dígitos YYYYMM: {comp!r}")
    ano = int(s[:4])
    mes = int(s[4:])
    if not (1 <= mes <= 12):
        raise ValueError(f"Mês inválido no campo '{nome_campo}': {s}")
    if ano >= 2026:
        raise ValueError(f"Arquivo/declaração de 2026 não autorizado no campo '{nome_campo}': {s}")
    return s


def _validar_grau_instrucao_val(val: Any) -> int | None:
    """Valida grau de instrução. Retorna int válido ou None (se nulo/desconhecido)."""
    if val is None or pd.isna(val):
        return None
    if isinstance(val, (bool, np.bool_)):
        raise TypeError(f"grau_instrucao não aceita valores booleanos: {val!r}")
    if isinstance(val, (float, np.floating)):
        if not np.isfinite(val) or not float(val).is_integer():
            raise ValueError(f"grau_instrucao float não inteiro inválido: {val!r}")
        val_int = int(val)
    elif isinstance(val, (int, np.integer)):
        val_int = int(val)
    elif isinstance(val, str):
        s = val.strip()
        if not s.isdigit():
            raise ValueError(f"grau_instrucao string não numérica: {val!r}")
        val_int = int(s)
    else:
        raise TypeError(f"Tipo inválido para grau_instrucao: {type(val).__name__}")

    if val_int not in GRAUS_VALIDOS:
        raise ValueError(f"Código de grau_instrucao não previsto: {val_int}")
    return val_int


def _validar_saldo_movimentacao_val(val: Any) -> int:
    """Valida saldo de movimentação (+1 ou -1)."""
    if val is None or pd.isna(val):
        raise ValueError("saldo_movimentacao não pode ser nulo.")
    if isinstance(val, (bool, np.bool_)):
        raise TypeError(f"saldo_movimentacao não aceita valores booleanos: {val!r}")
    if isinstance(val, (int, np.integer)):
        v_int = int(val)
    elif isinstance(val, (float, np.floating)):
        if not np.isfinite(val) or not float(val).is_integer():
            raise ValueError(f"saldo_movimentacao inválido: {val!r}")
        v_int = int(val)
    elif isinstance(val, str):
        s = val.strip()
        if s in ("1", "+1", "1.0"):
            v_int = 1
        elif s in ("-1", "-1.0"):
            v_int = -1
        else:
            raise ValueError(f"saldo_movimentacao string inválida: {val!r}")
    else:
        raise TypeError(f"Tipo inválido para saldo_movimentacao: {type(val).__name__}")

    if v_int not in (1, -1):
        raise ValueError(f"saldo_movimentacao deve ser estritamente 1 ou -1, recebido: {v_int}")
    return v_int


def agregar_base_municipal(
    microdados: pd.DataFrame,
    mapa: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Agrega microdados puros para a base municipal anual (SP, 6 destinos).

    Função pura sem I/O:
    - Validação de chaves, competências, tipos, SP e destinos.
    - Snapshots anuais separados: 2024 até 202412, 2025 até 202512.
    - Suficientes estatísticas assinadas: MOV/FOR (+1), EXC (-1).
    - População final: municípios com admissoes_2024 >= 10.
    """
    mapa_cbo = validar_mapa_destinos(mapa)

    if not isinstance(microdados, pd.DataFrame):
        raise TypeError("microdados deve ser um DataFrame pandas.")

    faltantes = [c for c in COLUNAS_MINIMAS if c not in microdados.columns]
    if faltantes:
        raise ValueError(f"Colunas mínimas ausentes nos microdados: {faltantes}")

    # Contadores de qualidade / exclusão
    contadores = {
        "linhas_totais_input": len(microdados),
        "linhas_excluidas_fora_sp": 0,
        "linhas_excluidas_fora_destinos": 0,
        "linhas_ignoradas_movimento_outro_ano": 0,
        "linhas_ignoradas_disponibilidade_snapshot": 0,
        "linhas_elegiveis_2024": 0,
        "linhas_elegiveis_2025": 0,
    }

    colunas_ordenadas = [
        "municipio",
        "uf",
        "admissoes_2024",
        "admissoes_2025",
        "desligamentos_2024",
        "desligamentos_2025",
        "admissoes_superior_2024",
        "admissoes_superior_2025",
        "escolaridade_desconhecida_2024",
        "escolaridade_desconhecida_2025",
        "salario_medio_2024",
        "salario_medio_2025",
        "percentual_superior_2024",
        "percentual_superior_2025",
        "n_salarios_validos_2024",
        "n_salarios_validos_2025",
        "n_salarios_invalidos_2024",
        "n_salarios_invalidos_2025",
        "crescimento",
        "crescimento_percentual",
    ]

    if microdados.empty:
        df_vazio = pd.DataFrame(columns=colunas_ordenadas)
        relatorio_vazio = {
            "timestamp_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "n_antes_populacao": 0,
            "n_populacao_final": 0,
            "n_excluidos_menos_10": 0,
            "contadores": contadores,
        }
        return df_vazio, relatorio_vazio

    # Estruturas para suficientes estatísticas por (município, ano)
    stats: dict[str, dict[str, dict[str, float | int]]] = {}
    municipios_observados_sp: set[str] = set()

    for idx, row in microdados.iterrows():
        # 1. Tipo de arquivo e saldo
        tipo_arq = str(row["arquivo_tipo"]).strip().upper()
        if tipo_arq not in {"MOV", "FOR", "EXC"}:
            raise ValueError(f"arquivo_tipo inválido na linha {idx}: {tipo_arq!r}")

        saldo = _validar_saldo_movimentacao_val(row["saldo_movimentacao"])
        grau = _validar_grau_instrucao_val(row["grau_instrucao"])

        # 2. Competências e Disponibilidade
        comp_mov = _validar_competencia_str(row["competencia_mov"], "competencia_mov")
        comp_dec = _validar_competencia_str(row["competencia_dec"], "competencia_dec")
        comp_arq = _validar_competencia_str(row["competencia_arquivo"], "competencia_arquivo")

        val_exc = row.get("competencia_exc")
        val_exc_vazio = (
            val_exc is None or pd.isna(val_exc) or str(val_exc).strip() in ("", "None", "nan")
        )
        if tipo_arq == "EXC":
            if val_exc_vazio:
                raise ValueError(
                    f"Registro EXC na linha {idx} sem competencia_exc válida: {val_exc!r}"
                )
            comp_exc = _validar_competencia_str(val_exc, "competencia_exc")
            comp_disp = max(comp_dec, comp_exc, comp_arq)
        else:
            if not val_exc_vazio:
                _validar_competencia_str(val_exc, "competencia_exc")
            comp_disp = max(comp_dec, comp_arq)

        # 3. Filtro de ano de movimento e disponibilidade do snapshot
        ano_mov = comp_mov[:4]
        if ano_mov not in ("2024", "2025"):
            contadores["linhas_ignoradas_movimento_outro_ano"] += 1
            continue

        if ano_mov == "2024" and comp_disp > "202412":
            contadores["linhas_ignoradas_disponibilidade_snapshot"] += 1
            continue
        if ano_mov == "2025" and comp_disp > "202512":
            contadores["linhas_ignoradas_disponibilidade_snapshot"] += 1
            continue

        # 4. Filtro geográfico (Apenas UF35 / SP)
        uf_raw = row["uf"]
        if isinstance(uf_raw, bool) or uf_raw is None or pd.isna(uf_raw):
            contadores["linhas_excluidas_fora_sp"] += 1
            continue
        uf_str = str(uf_raw).strip()
        if uf_str not in ("35", "SP"):
            contadores["linhas_excluidas_fora_sp"] += 1
            continue

        # Município de SP deve ser código de 6 dígitos prefixo 35
        mun_raw = row["municipio"]
        if isinstance(mun_raw, bool) or mun_raw is None or pd.isna(mun_raw):
            raise ValueError(f"Código municipal nulo ou inválido em SP na linha {idx}: {mun_raw!r}")
        mun_str = str(mun_raw).strip()
        if len(mun_str) != 6 or not mun_str.isdigit() or not mun_str.startswith("35"):
            raise ValueError(
                f"Município de SP deve conter 6 dígitos numéricos com prefixo 35: {mun_raw!r}"
            )

        municipios_observados_sp.add(mun_str)

        # 5. Filtro de CBO (seis destinos)
        cbo_raw = row["cbo2002_ocupacao"]
        if isinstance(cbo_raw, bool) or cbo_raw is None or pd.isna(cbo_raw):
            contadores["linhas_excluidas_fora_destinos"] += 1
            continue
        cbo_str = str(cbo_raw).strip()
        if cbo_str not in mapa_cbo:
            contadores["linhas_excluidas_fora_destinos"] += 1
            continue

        # Registra elegibilidade
        if ano_mov == "2024":
            contadores["linhas_elegiveis_2024"] += 1
        else:
            contadores["linhas_elegiveis_2025"] += 1

        # 6. Agregação com sinal documental (MOV/FOR=+1, EXC=-1)
        sinal = 1 if tipo_arq in ("MOV", "FOR") else -1

        if mun_str not in stats:
            stats[mun_str] = {
                "2024": {
                    "admissoes": 0,
                    "desligamentos": 0,
                    "superior": 0,
                    "desconhecida": 0,
                    "soma_salario": 0.0,
                    "n_validos": 0,
                    "n_invalidos": 0,
                },
                "2025": {
                    "admissoes": 0,
                    "desligamentos": 0,
                    "superior": 0,
                    "desconhecida": 0,
                    "soma_salario": 0.0,
                    "n_validos": 0,
                    "n_invalidos": 0,
                },
            }

        s_ano = stats[mun_str][ano_mov]

        if saldo == 1:
            s_ano["admissoes"] += sinal
            if grau in GRAUS_SUPERIOR:
                s_ano["superior"] += sinal
            elif grau is None or grau == 99:
                s_ano["desconhecida"] += sinal

            # Salário mensal declarado
            salario_raw = row.get("salario")
            eh_valido = False
            salario_valido_tipo = (
                salario_raw is not None
                and not isinstance(salario_raw, bool)
                and not pd.isna(salario_raw)
            )
            if salario_valido_tipo:
                try:
                    sal_f = float(salario_raw)
                    if np.isfinite(sal_f) and sal_f > 0:
                        eh_valido = True
                except (ValueError, TypeError):
                    eh_valido = False

            if eh_valido:
                s_ano["soma_salario"] += sinal * sal_f
                s_ano["n_validos"] += sinal
            else:
                s_ano["n_invalidos"] += sinal

        elif saldo == -1:
            s_ano["desligamentos"] += sinal

    # 7. Validação estrita das estatísticas consolidadas por município x ano
    for mun, st_anos in stats.items():
        for ano in ("2024", "2025"):
            d = st_anos[ano]
            adm = d["admissoes"]
            des = d["desligamentos"]
            sup = d["superior"]
            desc = d["desconhecida"]
            soma_s = d["soma_salario"]
            nv = d["n_validos"]
            ni = d["n_invalidos"]

            if adm < 0:
                raise ValueError(f"Contagem negativa de admissões em {mun}/{ano}: {adm}")
            if des < 0:
                raise ValueError(f"Contagem negativa de desligamentos em {mun}/{ano}: {des}")
            if sup < 0:
                raise ValueError(f"Contagem negativa de admissões superior em {mun}/{ano}: {sup}")
            if desc < 0:
                raise ValueError(
                    f"Contagem negativa de escolaridade desconhecida em {mun}/{ano}: {desc}"
                )
            if round(soma_s, 4) < 0:
                raise ValueError(f"Soma salarial líquida negativa em {mun}/{ano}: {soma_s}")
            if nv < 0:
                raise ValueError(f"n salarial válido negativo em {mun}/{ano}: {nv}")
            if ni < 0:
                raise ValueError(f"n salarial inválido negativo em {mun}/{ano}: {ni}")

            if sup > adm:
                raise ValueError(
                    f"Admissões superior ({sup}) acima do total ({adm}) em {mun}/{ano}"
                )
            if desc > adm:
                raise ValueError(
                    f"Escolaridade desconhecida ({desc}) acima do total ({adm}) em {mun}/{ano}"
                )
            if sup + desc > adm:
                raise ValueError(
                    f"Soma de superior e desconhecida ({sup + desc}) excede total ({adm}) "
                    f"em {mun}/{ano}"
                )
            if nv > adm or ni > adm:
                raise ValueError(f"Contagens salariais excedem admissões em {mun}/{ano}")
            if nv + ni != adm:
                raise ValueError(
                    f"Soma n_validos ({nv}) + n_invalidos ({ni}) != admissoes ({adm}) "
                    f"em {mun}/{ano}"
                )

    # 8. População D11 congelada: municípios com admissoes_2024 >= 10
    todos_municipios = sorted(municipios_observados_sp)
    populacao_municipios = [
        m for m in todos_municipios if stats.get(m, {}).get("2024", {}).get("admissoes", 0) >= 10
    ]

    linhas_base: list[dict[str, Any]] = []
    for mun in populacao_municipios:
        s24 = stats[mun]["2024"]
        s25 = stats.get(mun, {}).get(
            "2025",
            {
                "admissoes": 0,
                "desligamentos": 0,
                "superior": 0,
                "desconhecida": 0,
                "soma_salario": 0.0,
                "n_validos": 0,
                "n_invalidos": 0,
            },
        )

        adm24 = int(s24["admissoes"])
        adm25 = int(s25["admissoes"])
        des24 = int(s24["desligamentos"])
        des25 = int(s25["desligamentos"])
        sup24 = int(s24["superior"])
        sup25 = int(s25["superior"])
        desc24 = int(s24["desconhecida"])
        desc25 = int(s25["desconhecida"])
        nv24 = int(s24["n_validos"])
        nv25 = int(s25["n_validos"])
        ni24 = int(s24["n_invalidos"])
        ni25 = int(s25["n_invalidos"])

        # Salário médio: soma / n_validos; se n_validos == 0, NaN
        sal_med24 = (float(s24["soma_salario"]) / nv24) if nv24 > 0 else np.nan
        sal_med25 = (float(s25["soma_salario"]) / nv25) if nv25 > 0 else np.nan

        # Percentual superior: 100 * superior / admissoes; se adm == 0, NaN
        pct_sup24 = (100.0 * sup24 / adm24) if adm24 > 0 else np.nan
        pct_sup25 = (100.0 * sup25 / adm25) if adm25 > 0 else np.nan

        crescimento = 1 if adm25 > adm24 else 0
        cresc_pct = 100.0 * (adm25 / adm24 - 1.0)

        linhas_base.append(
            {
                "municipio": mun,
                "uf": "35",
                "admissoes_2024": adm24,
                "admissoes_2025": adm25,
                "desligamentos_2024": des24,
                "desligamentos_2025": des25,
                "admissoes_superior_2024": sup24,
                "admissoes_superior_2025": sup25,
                "escolaridade_desconhecida_2024": desc24,
                "escolaridade_desconhecida_2025": desc25,
                "salario_medio_2024": sal_med24,
                "salario_medio_2025": sal_med25,
                "percentual_superior_2024": pct_sup24,
                "percentual_superior_2025": pct_sup25,
                "n_salarios_validos_2024": nv24,
                "n_salarios_validos_2025": nv25,
                "n_salarios_invalidos_2024": ni24,
                "n_salarios_invalidos_2025": ni25,
                "crescimento": crescimento,
                "crescimento_percentual": cresc_pct,
            }
        )

    if linhas_base:
        base_df = pd.DataFrame(linhas_base)[colunas_ordenadas]
    else:
        base_df = pd.DataFrame(columns=colunas_ordenadas)

    relatorio = {
        "timestamp_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "n_antes_populacao": len(todos_municipios),
        "n_populacao_final": len(populacao_municipios),
        "n_excluidos_menos_10": len(todos_municipios) - len(populacao_municipios),
        "contadores": contadores,
        "politicas": {
            "convencao_disponibilidade": "mensal por competencia",
            "limite_disponibilidade_2024": "202412",
            "limite_disponibilidade_2025": "202512 (maturacao limitada, sem arquivos 2026)",
            "populacao_criterio": "admissoes_2024 >= 10 nos seis destinos em SP",
            "salario": (
                "salario mensal declarado nominal sem correcao inflacionaria ou corte de outliers"
            ),
            "superior_graus": sorted(GRAUS_SUPERIOR),
            "escolaridade_desconhecida_graus": [99, None],
        },
    }

    return base_df, relatorio


def carregar_base_municipal(
    dir_parquet: str | Path,
    mapa: dict[str, Any],
    leitor: Callable[[Path], pd.DataFrame] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Carrega os 72 arquivos canônicos e constrói a base municipal."""
    fontes = planejar_fontes_municipais(dir_parquet)

    if leitor is None:

        def leitor_default(p: Path) -> pd.DataFrame:
            return pd.read_parquet(p, columns=COLUNAS_MINIMAS)

        executar_leitura = leitor_default
    else:
        executar_leitura = leitor

    hashes_fontes: dict[str, str] = {}
    dfs: list[pd.DataFrame] = []

    for p in fontes:
        hashes_fontes[p.name] = _calcular_sha256(p)
        df_parte = executar_leitura(p)
        if df_parte is not None and not df_parte.empty:
            for campo, esperado in (
                ("arquivo_tipo", p.stem[5:8]),
                ("competencia_arquivo", p.stem[8:]),
            ):
                if campo not in df_parte:
                    raise ValueError(f"Fonte {p.name} sem campo {campo}.")
                valores = df_parte[campo].astype("string").str.strip().str.upper()
                if valores.ne(esperado).fillna(True).any():
                    raise ValueError(f"Fonte {p.name} com {campo} divergente do nome canonico.")
            dfs.append(df_parte)

    if dfs:
        microdados = pd.concat(dfs, ignore_index=True)
    else:
        microdados = pd.DataFrame(columns=COLUNAS_MINIMAS)

    base_df, relatorio = agregar_base_municipal(microdados, mapa)
    relatorio["fontes_planejadas"] = [str(p) for p in fontes]
    relatorio["hashes_fontes"] = hashes_fontes

    return base_df, relatorio
