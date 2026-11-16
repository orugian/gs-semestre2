"""Executa as consultas de evidência de app/db/consultas/evidencias_oracle.sql e grava a saída.

Cada consulta começa com um comentário "-- Cn. título" e termina em ";". A saída é uma tabela
em texto por consulta, com data/hora da execução e o usuário do schema omitido.

Uso (a partir de app/tools, com ORACLE_DSN/USER/PASSWORD no ambiente):
    uv run --with oracledb python executar_consultas_oracle.py --saida <arquivo.txt>
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

ARQUIVO = Path(__file__).resolve().parents[1] / "db" / "consultas" / "evidencias_oracle.sql"


def consultas(texto: str) -> list[tuple[str, str]]:
    saida = []
    for bloco in texto.split(";"):
        m = re.search(r"^--\s*(C\d+\..*)$", bloco, flags=re.M)
        linhas = [linha for linha in bloco.splitlines() if not linha.strip().startswith("--")]
        sql = "\n".join(linhas).strip()
        if m and sql:
            saida.append((m.group(1).strip(), sql))
    return saida


def tabela(colunas: list[str], linhas: list[tuple]) -> str:
    texto = [[("" if v is None else str(v)) for v in linha] for linha in linhas]
    larguras = [max([len(c)] + [len(t[i]) for t in texto]) for i, c in enumerate(colunas)]
    sep = "-+-".join("-" * w for w in larguras)
    out = [" | ".join(c.ljust(w) for c, w in zip(colunas, larguras, strict=True)), sep]
    out += [" | ".join(v.ljust(w) for v, w in zip(t, larguras, strict=True)) for t in texto]
    out.append(f"({len(linhas)} linha{'s' if len(linhas) != 1 else ''})")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--saida", required=True)
    args = ap.parse_args(argv)
    import oracledb

    partes = [
        "# Consultas de evidência — Oracle local (Docker Free 23ai, DDL 19c), schema do app",
        f"# Executado em {datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')} por "
        "app/tools/executar_consultas_oracle.py; usuário e senha do schema omitidos.",
        "",
    ]
    with oracledb.connect(
        user=os.environ["ORACLE_USER"],
        password=os.environ["ORACLE_PASSWORD"],
        dsn=os.environ["ORACLE_DSN"],
    ) as conexao:
        cursor = conexao.cursor()
        for titulo, sql in consultas(ARQUIVO.read_text(encoding="utf-8")):
            cursor.execute(sql)
            colunas = [d[0].lower() for d in cursor.description]
            linhas = cursor.fetchall()
            partes += [f"== {titulo}", sql, "", tabela(colunas, linhas), ""]
    Path(args.saida).write_text("\n".join(partes), encoding="utf-8")
    print(f"{len([p for p in partes if p.startswith('== ')])} consultas gravadas em {args.saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
