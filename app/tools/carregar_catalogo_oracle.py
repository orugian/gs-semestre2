"""Carrega a projeção relacional do catálogo (DDL 007) a partir dos YAML e do JSON de ocupações.

A fonte de verdade continua em app/catalogo. Esta carga substitui por completo o conteúdo das
cinco tabelas de catálogo (destino, ocupacao_cbo, destino_ocupacao, competencia_esco,
requisito_destino), numa única transação. Não toca em nenhuma tabela de dados de usuário.

Uso (a partir de app/tools, com ORACLE_DSN/USER/PASSWORD no ambiente):
    uv run --with oracledb --with pyyaml python carregar_catalogo_oracle.py --confirmar
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import yaml

CATALOGO = Path(__file__).resolve().parents[1] / "catalogo"


def montar_linhas() -> dict[str, list[tuple]]:
    escopo = json.loads((CATALOGO / "escopo_mvp.json").read_text(encoding="utf-8"))["destinos"]
    ocupacoes = json.loads((CATALOGO / "ocupacoes_cbo.json").read_text(encoding="utf-8"))
    linhas: dict[str, list[tuple]] = {
        k: []
        for k in (
            "destino",
            "ocupacao_cbo",
            "destino_ocupacao",
            "competencia_esco",
            "requisito_destino",
        )
    }
    for cbo6, dados in ocupacoes["ocupacoes"].items():
        linhas["ocupacao_cbo"].append((cbo6, dados["titulo"], dados.get("fonte_titulo")))
    esco: dict[str, tuple] = {}
    for arquivo in sorted((CATALOGO / "destinos").glob("*.yaml")):
        d = yaml.safe_load(arquivo.read_text(encoding="utf-8"))
        rev = d.get("revisao_humana") or {}
        status = (
            rev.get("status")
            if rev.get("status") in ("aprovado", "pendente", "rascunho")
            else "pendente"
        )
        revisado = datetime.fromisoformat(rev["revisado_em"]) if rev.get("revisado_em") else None
        descricao = ((d.get("populacao") or {}).get("descricao") or "")[:1000] or None
        linhas["destino"].append(
            (
                d["destino_id"],
                d["nome"],
                d.get("versao"),
                status,
                revisado,
                "S" if d["destino_id"] in escopo else "N",
                descricao,
            )
        )
        for cbo6 in d.get("cbo6") or []:
            linhas["destino_ocupacao"].append((d["destino_id"], str(cbo6)))
        for ordem, r in enumerate(d.get("requisitos") or [], start=1):
            esco.setdefault(
                r["esco_id"],
                (
                    r["esco_id"],
                    r.get("titulo_oficial") or r["id_local"],
                    r.get("tipo_esco"),
                    r.get("esco_uri"),
                ),
            )
            linhas["requisito_destino"].append(
                (
                    d["destino_id"],
                    r["id_local"],
                    r["esco_id"],
                    "S" if r.get("obrigatorio_proposto") else "N",
                    ordem,
                )
            )
    linhas["competencia_esco"] = list(esco.values())
    return linhas


INSERTS = {
    "ocupacao_cbo": "INSERT INTO ocupacao_cbo (cbo6, titulo, fonte_titulo) VALUES (:1, :2, :3)",
    "destino": (
        "INSERT INTO destino (id, nome, versao, status_revisao, revisado_em, no_escopo_mvp, "
        "descricao) VALUES (:1, :2, :3, :4, :5, :6, :7)"
    ),
    "destino_ocupacao": "INSERT INTO destino_ocupacao (destino_id, cbo6) VALUES (:1, :2)",
    "competencia_esco": (
        "INSERT INTO competencia_esco (esco_id, titulo, tipo, uri) VALUES (:1, :2, :3, :4)"
    ),
    "requisito_destino": (
        "INSERT INTO requisito_destino (destino_id, id_local, esco_id, obrigatorio, "
        "ordem) VALUES (:1, :2, :3, :4, :5)"
    ),
}
ORDEM_APAGAR = [
    "requisito_destino",
    "destino_ocupacao",
    "destino",
    "competencia_esco",
    "ocupacao_cbo",
]
ORDEM_INSERIR = [
    "ocupacao_cbo",
    "destino",
    "destino_ocupacao",
    "competencia_esco",
    "requisito_destino",
]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--confirmar", action="store_true")
    args = ap.parse_args(argv)
    linhas = montar_linhas()
    print("Linhas por tabela:", {k: len(v) for k, v in linhas.items()})
    if not args.confirmar:
        print("Nada gravado (use --confirmar).")
        return 0
    import oracledb

    with oracledb.connect(
        user=os.environ["ORACLE_USER"],
        password=os.environ["ORACLE_PASSWORD"],
        dsn=os.environ["ORACLE_DSN"],
    ) as conexao:
        with conexao.cursor() as cursor:
            for tabela in ORDEM_APAGAR:
                cursor.execute(f"DELETE FROM {tabela}")  # nomes fixos do próprio script
            for tabela in ORDEM_INSERIR:
                if linhas[tabela]:
                    cursor.executemany(INSERTS[tabela], linhas[tabela])
        conexao.commit()
    print("Catálogo carregado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
