"""Gerenciamento de conexao sob demanda com banco Oracle (19c/23ai).

Importacao do oracledb sob demanda para nao quebrar execucao em modo isolado.
"""

import os
import threading
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from citizentech.erros import ErroBancoIndisponivel

_pool_lock = threading.Lock()
_pool: Any = None


def obter_pool() -> Any:
    """Retorna o pool de conexoes Oracle sob demanda."""
    global _pool
    if _pool is not None:
        return _pool

    with _pool_lock:
        if _pool is not None:
            return _pool

        dsn = os.environ.get("ORACLE_DSN")
        user = os.environ.get("ORACLE_USER")
        password = os.environ.get("ORACLE_PASSWORD")

        if not (dsn and user and password):
            raise ErroBancoIndisponivel("Configuracao do banco Oracle ausente.")

        try:
            import oracledb

            _pool = oracledb.create_pool(
                user=user,
                password=password,
                dsn=dsn,
                min=1,
                max=4,
                increment=1,
            )
            return _pool
        except Exception as err:
            raise ErroBancoIndisponivel("Nao foi possivel conectar ao banco de dados.") from err


@contextmanager
def obter_conexao() -> Generator[Any, None, None]:
    """Adquire uma conexao do pool, gerencia transacao e devolve ao pool."""
    pool = obter_pool()
    try:
        import oracledb
    except ImportError as err:
        raise ErroBancoIndisponivel("Driver oracledb nao instalado.") from err

    try:
        conexao = pool.acquire()
    except oracledb.Error as err:
        raise ErroBancoIndisponivel("Falha ao obter conexao com o banco de dados.") from err

    try:
        yield conexao
        conexao.commit()
    except Exception:
        try:
            conexao.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            pool.release(conexao)
        except Exception:
            pass


def fechar_pool() -> None:
    """Encerra o pool de conexoes se estiver aberto."""
    global _pool
    with _pool_lock:
        if _pool is not None:
            try:
                _pool.close()
            except Exception:
                pass
            _pool = None
