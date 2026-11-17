"""Aplica os DDL de app/db/ddl (001, 002, ...) em ordem no schema Oracle indicado pelo ambiente.

Lê ORACLE_DSN, ORACLE_USER e ORACLE_PASSWORD do ambiente (nunca imprime valores). É idempotente:
objetos que já existem (ORA-00955, ORA-01408, ORA-02260, ORA-02275) são ignorados.

Uso (a partir de app/tools, com as variáveis definidas):
    uv run --with oracledb python aplicar_ddl.py --confirmar
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _comum import blocos_sql, conectar_oracle

DDL_DIR = Path(__file__).resolve().parents[1] / "db" / "ddl"
JA_EXISTE = ("ORA-00955", "ORA-01408", "ORA-02260", "ORA-02275")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--confirmar", action="store_true", help="executa de fato (sem ele, só lista)")
    args = ap.parse_args(argv)

    arquivos = sorted(DDL_DIR.glob("[0-9][0-9][0-9]_*.sql"))
    print("DDL encontrados:", [a.name for a in arquivos])
    if not args.confirmar:
        print("Nada executado (use --confirmar).")
        return 0

    import oracledb

    criados, ignorados = 0, 0
    try:
        conexao = conectar_oracle()
    except RuntimeError as err:
        print(str(err), file=sys.stderr)
        return 2

    with conexao:
        with conexao.cursor() as cursor:
            for arquivo in arquivos:
                for sql in blocos_sql(arquivo.read_text(encoding="utf-8")):
                    try:
                        cursor.execute(sql)
                        criados += 1
                    except oracledb.DatabaseError as err:
                        if any(codigo in str(err) for codigo in JA_EXISTE):
                            ignorados += 1
                            continue
                        print(
                            f"Erro em {arquivo.name}: {str(err).splitlines()[0]}", file=sys.stderr
                        )
                        return 1
            conexao.commit()
            cursor.execute("SELECT table_name FROM user_tables ORDER BY table_name")
            tabelas = [linha[0] for linha in cursor]
    print(f"Comandos executados: {criados} · já existentes: {ignorados}")
    print("Tabelas no schema:", tabelas)
    return 0


if __name__ == "__main__":
    sys.exit(main())
