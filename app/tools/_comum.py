"""Funcoes e utilidades comuns para os scripts em app/tools."""

from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

CAMINHOS_EDGE = (
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
)


class Sessao:
    """Guarda os cookies da sessao e cabecalho CSRF para requisicoes HTTP."""

    def __init__(self, cookies: dict[str, str] | None = None) -> None:
        self.cookies: dict[str, str] = dict(cookies or {})

    def cabecalho(self) -> str:
        return "; ".join(f"{k}={v}" for k, v in self.cookies.items())

    def atualizar_cookies(self, set_cookies: list[str]) -> None:
        for linha in set_cookies:
            nome, _, resto = linha.partition("=")
            self.cookies[nome.strip()] = resto.split(";", 1)[0]


def requisitar(
    base: str,
    metodo: str,
    caminho: str,
    corpo: Any = None,
    sessao: Sessao | None = None,
    csrf: bool = False,
    chave: str | None = None,
    cabecalhos: dict[str, str] | None = None,
    timeout: int = 30,
) -> tuple[int, Any, list[str]]:
    """Executa requisicao HTTP com suporte a cookies/sessao, CSRF e X-Device-Key."""
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    h: dict[str, str] = {"Content-Type": "application/json"} if dados is not None else {}
    if sessao and sessao.cookies:
        h["Cookie"] = sessao.cabecalho()
    # CSRF só quando pedido: a demo de proteções envia requisições sem o token de propósito.
    if csrf and sessao and "csrf_token" in sessao.cookies:
        h["X-CSRF-Token"] = sessao.cookies["csrf_token"]
    if chave:
        h["X-Device-Key"] = chave
    if cabecalhos:
        h.update(cabecalhos)

    req = urllib.request.Request(base + caminho, data=dados, headers=h, method=metodo)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            status, texto, set_cookies = (
                r.status,
                r.read().decode("utf-8"),
                r.headers.get_all("Set-Cookie") or [],
            )
    except urllib.error.HTTPError as e:
        status, texto, set_cookies = (
            e.code,
            e.read().decode("utf-8"),
            e.headers.get_all("Set-Cookie") or [],
        )

    if sessao is not None:
        sessao.atualizar_cookies(set_cookies)

    try:
        corpo_resp = json.loads(texto) if texto else None
    except json.JSONDecodeError:
        corpo_resp = texto

    return status, corpo_resp, set_cookies


def conectar_oracle():
    """Conexao oracledb a partir de ORACLE_USER, ORACLE_PASSWORD e ORACLE_DSN."""
    import oracledb

    user = os.environ.get("ORACLE_USER")
    password = os.environ.get("ORACLE_PASSWORD")
    dsn = os.environ.get("ORACLE_DSN")
    if not (user and password and dsn):
        raise RuntimeError("Variaveis ORACLE_USER, ORACLE_PASSWORD e ORACLE_DSN obrigatorias.")
    return oracledb.connect(user=user, password=password, dsn=dsn)


def blocos_sql(texto: str) -> list[str]:
    """Divide o arquivo SQL por ';' e remove linhas de comentario."""
    saida = []
    for bloco in texto.split(";"):
        linhas = [linha for linha in bloco.splitlines() if not linha.strip().startswith("--")]
        sql = "\n".join(linhas).strip()
        if sql:
            saida.append(sql)
    return saida


def sha256_arquivo(caminho: Path | str) -> str:
    """Calcula o hash SHA-256 de um arquivo."""
    hasher = hashlib.sha256()
    with Path(caminho).open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def localizar_edge() -> Path:
    """Localiza o executavel msedge.exe no sistema."""
    candidatos = [os.environ.get("CITIZENTECH_EDGE"), *CAMINHOS_EDGE]
    for candidato in candidatos:
        if candidato and Path(candidato).is_file():
            return Path(candidato)
    raise FileNotFoundError("msedge.exe nao encontrado (defina CITIZENTECH_EDGE)")
