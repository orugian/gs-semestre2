"""Snapshot único Adzuna (D05a): no máximo 12 chamadas no contador do projeto.

O contador é incrementado e gravado ANTES de cada chamada (uma chamada que falha também
conta). O JSON bruto de cada resposta é guardado com SHA-256; as credenciais nunca são
gravadas (nem na URL, nem no corpo). O resultado é exibido como "amostra pontual", com
atribuição, e não entra no treino.

Uso real (somente o orquestrador, com autorização de quota):
    uv run python -m citizentech_ml.mercado.adzuna --saida <DADOS>/adzuna/AAAAMMDD
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

URL_BASE = "https://api.adzuna.com/v1/api/jobs/br/search/1"
ATRIBUICAO = "Jobs by Adzuna (https://www.adzuna.com.br)"
TERRITORIOS = {"SP": "São Paulo", "BR": None}


class LimiteChamadasExcedido(RuntimeError):
    """A coleta ultrapassaria o teto de chamadas do contador D05a."""


@dataclass(frozen=True)
class ConsultaAdzuna:
    destino: str
    territorio: str  # "SP" ou "BR"
    termo: str


def _agora() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ler_contador(caminho: Path) -> dict[str, Any]:
    if not caminho.exists():
        return {"total": 0, "registro": []}
    estado = json.loads(caminho.read_text(encoding="utf-8"))
    if not isinstance(estado.get("total"), int) or estado["total"] < 0:
        raise ValueError("Contador Adzuna malformado.")
    estado.setdefault("registro", [])
    return estado


def _gravar_json(caminho: Path, obj: Any) -> bytes:
    bruto = json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8")
    temporario = caminho.with_suffix(caminho.suffix + ".tmp")
    temporario.write_bytes(bruto)
    os.replace(temporario, caminho)
    return bruto


def _montar_url(consulta: ConsultaAdzuna, app_id: str, app_key: str) -> str:
    if consulta.territorio not in TERRITORIOS:
        raise ValueError(f"Território não suportado: {consulta.territorio}")
    parametros = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": "20",
        "what": consulta.termo,
        "content-type": "application/json",
    }
    onde = TERRITORIOS[consulta.territorio]
    if onde:
        parametros["where"] = onde
    return f"{URL_BASE}?{urllib.parse.urlencode(parametros)}"


def http_urllib(url: str, timeout_s: float = 20.0) -> tuple[int, bytes]:
    """Cliente HTTP real (urllib). Erros de rede viram status 0, sem vazar a URL."""
    try:
        with urllib.request.urlopen(url, timeout=timeout_s) as resposta:  # noqa: S310
            return resposta.status, resposta.read()
    except urllib.error.HTTPError as erro:
        return erro.code, erro.read()
    except (urllib.error.URLError, TimeoutError):
        return 0, b""


def coletar_snapshot_adzuna(
    consultas: Sequence[ConsultaAdzuna],
    dir_saida: str | Path,
    caminho_contador: str | Path,
    *,
    http: Callable[[str], tuple[int, bytes]],
    credenciais: tuple[str, str],
    maximo: int = 12,
) -> dict[str, Any]:
    """Executa as consultas respeitando o teto e grava brutos, resumo e manifesto."""
    dir_saida = Path(dir_saida)
    caminho_contador = Path(caminho_contador)
    app_id, app_key = credenciais
    if not app_id or not app_key:
        raise ValueError("Credenciais Adzuna ausentes.")
    if dir_saida.exists():
        raise FileExistsError(f"Snapshot já existe: {dir_saida.name}")

    estado = _ler_contador(caminho_contador)
    if estado["total"] + len(consultas) > maximo:
        raise LimiteChamadasExcedido(
            f"{estado['total']} chamadas já usadas + {len(consultas)} solicitadas > teto {maximo}."
        )

    dir_saida.mkdir(parents=True)
    itens: list[dict[str, Any]] = []
    for indice, consulta in enumerate(consultas, start=1):
        url = _montar_url(consulta, app_id, app_key)
        estado["total"] += 1
        registro = {
            "quando": _agora(),
            "finalidade": "snapshot D05a",
            "destino": consulta.destino,
            "territorio": consulta.territorio,
            "status": None,
        }
        estado["registro"].append(registro)
        _gravar_json(caminho_contador, estado)  # reserva a chamada antes de fazê-la

        status, corpo = http(url)
        registro["status"] = status
        _gravar_json(caminho_contador, estado)

        for segredo in (app_key, app_id):
            corpo = corpo.replace(segredo.encode("utf-8"), b"[CREDENCIAL]")
        nome_bruto = f"{indice:02d}_{consulta.destino}_{consulta.territorio}.json"
        (dir_saida / nome_bruto).write_bytes(corpo)

        contagem = None
        media = None
        if status == 200:
            try:
                dados = json.loads(corpo.decode("utf-8"))
                contagem = int(dados["count"]) if "count" in dados else None
                media = float(dados["mean"]) if dados.get("mean") is not None else None
            except (ValueError, TypeError, KeyError):
                contagem = None
        itens.append(
            {
                "destino": consulta.destino,
                "territorio": consulta.territorio,
                "termo_busca": consulta.termo,
                "status_http": status,
                "contagem_anuncios": contagem,
                "media_salarial_anunciada": media,
                "coletado_em": registro["quando"],
                "arquivo_bruto": nome_bruto,
                "sha256_bruto": hashlib.sha256(corpo).hexdigest(),
            }
        )

    resumo = {
        "schema_version": "1.0",
        "fonte": "Adzuna API (anúncios agregados de terceiros)",
        "atribuicao": ATRIBUICAO,
        "natureza": "amostra_pontual",
        "unidade": "anúncios publicados que correspondem ao termo de busca",
        "populacao": (
            "Anúncios indexados pela Adzuna no Brasil no dia da coleta; não é medida "
            "oficial de mercado, não entra no treino e não indica chance individual."
        ),
        "coletado_em": itens[0]["coletado_em"] if itens else _agora(),
        "itens": itens,
    }
    bruto_resumo = _gravar_json(dir_saida / "resumo_adzuna.json", resumo)
    _gravar_json(
        dir_saida / "manifesto.json",
        {
            "schema_version": "1.0",
            "arquivo": "resumo_adzuna.json",
            "sha256": hashlib.sha256(bruto_resumo).hexdigest(),
            "gerado_em": _agora(),
        },
    )
    return resumo


def _consultas_do_escopo(caminho_termos: Path) -> list[ConsultaAdzuna]:
    termos = json.loads(caminho_termos.read_text(encoding="utf-8"))
    return [
        ConsultaAdzuna(destino=destino, territorio=territorio, termo=termo)
        for destino, termo in termos.items()
        for territorio in ("SP", "BR")
    ]


def main(argv: list[str] | None = None) -> int:
    analisador = argparse.ArgumentParser(description="Coleta o snapshot único Adzuna (D05a).")
    analisador.add_argument("--saida", type=Path, required=True)
    analisador.add_argument("--termos", type=Path, required=True, help="JSON {destino: termo}")
    analisador.add_argument("--contador", type=Path, required=True)
    analisador.add_argument("--maximo", type=int, default=12)
    opcoes = analisador.parse_args(argv)
    credenciais = (os.environ.get("ADZUNA_APP_ID", ""), os.environ.get("ADZUNA_APP_KEY", ""))
    resumo = coletar_snapshot_adzuna(
        _consultas_do_escopo(opcoes.termos),
        opcoes.saida,
        opcoes.contador,
        http=http_urllib,
        credenciais=credenciais,
        maximo=opcoes.maximo,
    )
    for item in resumo["itens"]:
        print(
            f"{item['destino']} {item['territorio']} status={item['status_http']} "
            f"anuncios={item['contagem_anuncios']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
