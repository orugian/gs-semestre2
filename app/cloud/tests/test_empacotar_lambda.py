"""Testes unitarios para o empacotador da AWS Lambda (empacotar_lambda.py)."""

import importlib.metadata as md
import json
import sys
import zipfile
from pathlib import Path

import pytest

raiz_cloud = Path(__file__).resolve().parents[1]
if str(raiz_cloud) not in sys.path:
    sys.path.insert(0, str(raiz_cloud))

import empacotar_lambda  # noqa: E402


def test_empacotar_gera_zip_com_estrutura_correta(tmp_path):
    saida = tmp_path / "dist"
    ca_dummy = tmp_path / "rds-ca-baixado.pem"
    ca_dummy.write_text("dummy ca content", encoding="utf-8")

    zip_path = empacotar_lambda.empacotar(saida, ca_path=ca_dummy)
    assert zip_path.is_file()

    with zipfile.ZipFile(zip_path, "r") as z:
        nomes = set(z.namelist())

        # 1. lambda_function.py na raiz
        assert "lambda_function.py" in nomes

        # 2. Pacote citizentech_cloud e limiares.json
        assert "citizentech_cloud/__init__.py" in nomes
        assert "citizentech_cloud/risco.py" in nomes
        assert "citizentech_cloud/sentimento.py" in nomes
        assert "citizentech_cloud/banco.py" in nomes
        assert "citizentech_cloud/limiares.json" in nomes

        # 3. Certificado CA
        # banco.py procura o bundle ao lado do modulo (verify-full, D09)
        assert "citizentech_cloud/global-bundle.pem" in nomes

        # 4. Dependencia pg8000
        pg8000_presente = any("pg8000" in n for n in nomes)
        assert pg8000_presente is True

        # 5. Conferir conteudo de limiares.json identico a app/config/limiares.json
        conteudo_zip = json.loads(z.read("citizentech_cloud/limiares.json").decode("utf-8"))
        caminho_origem = Path(__file__).resolve().parents[2] / "config" / "limiares.json"
        conteudo_origem = json.loads(caminho_origem.read_text(encoding="utf-8"))
        assert conteudo_zip == conteudo_origem


def test_empacotar_aborta_com_codigo_2_se_houver_binario(tmp_path, monkeypatch):
    class FakePackageFile:
        def __init__(self, name):
            self.name = name

        def __str__(self):
            return self.name

        def locate(self):
            return tmp_path / self.name

    # Injetar retorno de md.files com arquivo binario nativo
    def fake_files(pkg):
        if pkg == "pg8000":
            return [FakePackageFile("modulo_nativo.pyd")]
        return []

    monkeypatch.setattr(md, "files", fake_files)

    with pytest.raises(SystemExit) as exc:
        empacotar_lambda.empacotar(tmp_path / "dist")
    assert exc.value.code == 2
