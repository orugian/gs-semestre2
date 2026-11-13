"""Interfaces e clientes de rede para obtenção dos microdados do Novo Caged."""

import re
import subprocess
from pathlib import Path
from typing import Protocol


class Baixador(Protocol):
    """Protocolo da fronteira de rede para listagem e download de microdados."""

    def listar_arquivos(self, competencia: str) -> list[str]:
        """Lista os arquivos disponíveis para a competência AAAAMM."""
        ...

    def baixar_arquivo(self, tipo: str, competencia: str, destino: Path) -> Path:
        """Baixa o arquivo para o destino local."""
        ...


class BaixadorCurl:
    """Implementação real de download via curl.exe usando subprocess."""

    def __init__(self, url_base: str = "ftp://ftp.mtps.gov.br/pdet/microdados/NOVO%20CAGED/"):
        self.url_base = url_base.rstrip("/") + "/"

    def listar_arquivos(self, competencia: str) -> list[str]:
        """Lista os arquivos disponíveis no diretório remoto da competência AAAAMM."""
        ano = competencia[:4]
        url = f"{self.url_base}{ano}/{competencia}/"
        cmd = ["curl.exe", "-s", "--max-time", "40", "--list-only", url]

        resultado = subprocess.run(
            cmd,
            shell=False,
            capture_output=True,
            text=True,
            check=False,
        )
        if resultado.returncode != 0:
            raise RuntimeError(
                f"Falha ao listar arquivos de {competencia} (código {resultado.returncode}): "
                f"{resultado.stderr.strip()}"
            )

        arquivos: list[str] = []
        padrao = re.compile(rf"^CAGED(MOV|FOR|EXC){competencia}\.7z$", re.IGNORECASE)
        for linha in resultado.stdout.splitlines():
            nome = linha.strip()
            if padrao.match(nome):
                arquivos.append(nome)
        return arquivos

    def baixar_arquivo(self, tipo: str, competencia: str, destino: Path) -> Path:
        """Baixa um arquivo .7z do FTP usando curl.exe."""
        ano = competencia[:4]
        nome_arquivo = f"CAGED{tipo.upper()}{competencia}.7z"
        url = f"{self.url_base}{ano}/{competencia}/{nome_arquivo}"

        destino.parent.mkdir(parents=True, exist_ok=True)
        cmd = ["curl.exe", "-s", "--max-time", "900", "-o", str(destino), url]

        resultado = subprocess.run(
            cmd,
            shell=False,
            capture_output=True,
            text=True,
            check=False,
        )

        if resultado.returncode != 0:
            if destino.exists():
                destino.unlink()
            raise RuntimeError(
                f"Falha de download do arquivo '{nome_arquivo}' (código {resultado.returncode}): "
                f"{resultado.stderr.strip()}"
            )

        if not destino.exists() or destino.stat().st_size == 0:
            if destino.exists():
                destino.unlink()
            raise RuntimeError(f"Download de '{nome_arquivo}' produziu arquivo vazio ou ausente.")

        return destino
