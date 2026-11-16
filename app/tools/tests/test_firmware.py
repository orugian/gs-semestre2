"""Testes automatizados do firmware ESP32, logica e gerador de limiares (E01-firmware)."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from gerar_limiares_h import (
    calcular_sha256,
    escrever_header,
    gerar_conteudo_esperado,
    verificar_header,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
FIRMWARE_DIR = REPO_ROOT / "app" / "iot" / "firmware"
CONFIG_DIR = REPO_ROOT / "app" / "config"
LIMIARES_JSON_PATH = CONFIG_DIR / "limiares.json"
LIMIARES_H_PATH = FIRMWARE_DIR / "limiares.h"
SKETCH_PATH = FIRMWARE_DIR / "sketch.ino"
DIAGRAM_PATH = FIRMWARE_DIR / "diagram.json"
TESTE_LOGICA_PATH = FIRMWARE_DIR / "teste_logica.cpp"


# ==============================================================================
# (a) Testes do Gerador de Limiares
# ==============================================================================
def test_gerador_limiares_conteudo_padrao():
    """Confere que o conteudo gerado contem as macros e o hash SHA-256 do JSON."""
    conteudo, sha256 = gerar_conteudo_esperado(LIMIARES_JSON_PATH)

    assert "LIMIAR_TEMPERATURA_ATENCAO 35.0f" in conteudo
    assert "LIMIAR_TEMPERATURA_CRITICO 45.0f" in conteudo
    assert "LIMIAR_DISTANCIA_ATENCAO 15.0f" in conteudo
    assert "LIMIAR_DISTANCIA_CRITICO 8.0f" in conteudo
    assert "LIMIAR_DISTANCIA_MINIMO 0.0f" in conteudo
    assert f'#define LIMIARES_JSON_SHA256 "{sha256}"' in conteudo
    assert sha256 == calcular_sha256(LIMIARES_JSON_PATH)


def test_gerador_limiares_com_fixture_alterada(tmp_path: Path):
    """Gera header a partir de um JSON alterado e verifica diferenca."""
    dados_mock = {
        "metricas": {
            "temperatura_c": {"atencao": 30.5, "critico": 40.0},
            "distancia_cm": {"atencao": 20.0, "critico": 10.0, "valor_minimo": 0.0},
        }
    }
    mock_json = tmp_path / "mock_limiares.json"
    mock_json.write_text(json.dumps(dados_mock), encoding="utf-8")

    mock_header = tmp_path / "limiares.h"
    escrever_header(mock_json, mock_header)

    conteudo = mock_header.read_text(encoding="utf-8")
    assert "LIMIAR_TEMPERATURA_ATENCAO 30.5f" in conteudo
    assert "LIMIAR_TEMPERATURA_CRITICO 40.0f" in conteudo
    assert "LIMIAR_DISTANCIA_ATENCAO 20.0f" in conteudo
    assert "LIMIAR_DISTANCIA_CRITICO 10.0f" in conteudo
    assert verificar_header(mock_json, mock_header) is True

    # Se alterar o JSON sem atualizar o header, verificar deve retornar False
    dados_mock["metricas"]["temperatura_c"]["atencao"] = 99.0
    mock_json.write_text(json.dumps(dados_mock), encoding="utf-8")
    assert verificar_header(mock_json, mock_header) is False


def test_gerador_cli_verificar():
    """Executa a CLI do gerador com --verificar via subprocess e confere retorno 0."""
    res = subprocess.run(
        ["uv", "run", "python", "gerar_limiares_h.py", "--verificar"],
        cwd=REPO_ROOT / "app" / "tools",
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"CLI --verificar falhou: {res.stderr}"


# ==============================================================================
# (b) Compilação e Execução de teste_logica.cpp no Host com g++
# ==============================================================================
def test_compilacao_e_execucao_teste_logica(tmp_path: Path):
    """Compila teste_logica.cpp com g++ -std=c++17 -Wall -Wextra -Werror e executa."""
    gpp = shutil.which("g++")
    if not gpp:
        pytest.fail("Compilador g++ nao encontrado no PATH do sistema. Obrigatorio para testes.")

    binario = tmp_path / "teste_logica.exe"
    cmd_compilar = [
        gpp,
        "-std=c++17",
        "-Wall",
        "-Wextra",
        "-Werror",
        f"-I{FIRMWARE_DIR}",
        str(TESTE_LOGICA_PATH),
        "-o",
        str(binario),
    ]

    res_compilacao = subprocess.run(cmd_compilar, capture_output=True, text=True)
    assert res_compilacao.returncode == 0, (
        f"Falha na compilacao com g++:\n{res_compilacao.stderr}"
    )

    res_execucao = subprocess.run([str(binario)], capture_output=True, text=True)
    assert res_execucao.returncode == 0, (
        f"Binario teste_logica falhou com codigo {res_execucao.returncode}:\n"
        f"{res_execucao.stdout}\n{res_execucao.stderr}"
    )


# ==============================================================================
# (c) Verificação de Sincronia de limiares.h
# ==============================================================================
def test_limiares_h_sincronizado():
    """Garante que o arquivo limiares.h no repositorio esta rigorosamente em dia."""
    assert LIMIARES_H_PATH.is_file(), "limiares.h nao existe em app/iot/firmware"
    assert verificar_header(LIMIARES_JSON_PATH, LIMIARES_H_PATH) is True, (
        "limiares.h diverge de app/config/limiares.json. "
        "Execute 'uv run python gerar_limiares_h.py'."
    )


# ==============================================================================
# (d) Validação do diagram.json e Pinos do Sketch
# ==============================================================================
def test_diagram_json_e_pinos_sketch():
    """Valida que diagram.json e JSON valido, contem as 5 partes e mapeia os pinos do sketch."""
    assert DIAGRAM_PATH.is_file(), "diagram.json nao existe em app/iot/firmware"
    dados_diagram = json.loads(DIAGRAM_PATH.read_text(encoding="utf-8"))

    partes = {p["type"] for p in dados_diagram.get("parts", [])}
    partes_obrigatorias = {
        "board-esp32-devkit-c-v4",
        "wokwi-ds18b20",
        "wokwi-hc-sr04",
        "wokwi-led",
        "wokwi-buzzer",
    }
    assert partes_obrigatorias.issubset(partes), (
        f"Partes ausentes no diagram.json: {partes_obrigatorias - partes}"
    )

    # Extrai #define PINO_* do sketch.ino
    assert SKETCH_PATH.is_file(), "sketch.ino nao existe em app/iot/firmware"
    conteudo_sketch = SKETCH_PATH.read_text(encoding="utf-8")

    pinos = dict(re.findall(r"#define\s+(PINO_\w+)\s+(\d+)", conteudo_sketch))
    assert "PINO_ONEWIRE" in pinos, "PINO_ONEWIRE ausente no sketch"
    assert "PINO_TRIG" in pinos, "PINO_TRIG ausente no sketch"
    assert "PINO_ECHO" in pinos, "PINO_ECHO ausente no sketch"
    assert "PINO_LED" in pinos, "PINO_LED ausente no sketch"
    assert "PINO_BUZZER" in pinos, "PINO_BUZZER ausente no sketch"

    # Confere conexoes no diagram.json
    conexoes = dados_diagram.get("connections", [])
    conexoes_str = " ".join(f"{c[0]}->{c[1]}" for c in conexoes)

    pino_onewire = pinos["PINO_ONEWIRE"]
    pino_trig = pinos["PINO_TRIG"]
    pino_echo = pinos["PINO_ECHO"]
    pino_led = pinos["PINO_LED"]
    pino_buzzer = pinos["PINO_BUZZER"]

    assert f"esp:{pino_onewire}" in conexoes_str, f"Pino OneWire GPIO {pino_onewire} desconectado"
    assert f"esp:{pino_trig}" in conexoes_str, f"Pino Trig GPIO {pino_trig} desconectado"
    assert f"esp:{pino_echo}" in conexoes_str, f"Pino Echo GPIO {pino_echo} desconectado"
    assert f"esp:{pino_led}" in conexoes_str, f"Pino LED GPIO {pino_led} desconectado"
    assert f"esp:{pino_buzzer}" in conexoes_str, f"Pino Buzzer GPIO {pino_buzzer} desconectado"


# ==============================================================================
# (e) Segurança e Ausência de Chaves Reais (D24)
# ==============================================================================
def test_segredos_e_gitignore():
    """Garante que segredos.h esta ignorado e nenhum arquivo versionado contem chave real."""
    gitignore_path = REPO_ROOT / ".gitignore"
    assert gitignore_path.is_file()
    linhas_gitignore = gitignore_path.read_text(encoding="utf-8").splitlines()
    assert any("app/iot/firmware/segredos.h" in linha for linha in linhas_gitignore), (
        "app/iot/firmware/segredos.h deve constar no .gitignore"
    )

    segredos_exemplo = FIRMWARE_DIR / "segredos.exemplo.h"
    assert segredos_exemplo.is_file()
    conteudo_exemplo = segredos_exemplo.read_text(encoding="utf-8")
    assert 'DEVICE_KEY "troque-pela-chave-da-demo"' in conteudo_exemplo

    # Varre arquivos do firmware em busca de segredos ou chaves reais
    for arquivo in FIRMWARE_DIR.iterdir():
        if arquivo.name == "segredos.h":
            continue  # segredos.h e local e ignorado
        conteudo = arquivo.read_text(encoding="utf-8", errors="ignore")
        # Procura definicoes literais de DEVICE_KEY
        matches = re.findall(r'#define\s+DEVICE_KEY\s+"([^"]+)"', conteudo)
        for chave in matches:
            assert chave == "troque-pela-chave-da-demo", (
                f"Chave real encontrada no arquivo {arquivo.name}: '{chave}'. "
                f"Apenas o placeholder 'troque-pela-chave-da-demo' e permitido."
            )


# ==============================================================================
# (f) Pré-Mortem: Ausência de Limiares Duplicados no Sketch e Sem Eco HC-SR04
# ==============================================================================
def test_pre_mortem_limiares_nao_duplicados_no_sketch():
    """Garante que o sketch nao duplica limiares de temperatura ou distancia à mão (D20)."""
    conteudo_sketch = SKETCH_PATH.read_text(encoding="utf-8")
    linhas = conteudo_sketch.splitlines()

    for linha in linhas:
        linha_strip = linha.strip()
        # Ignora definicoes de pinos, delays, timeouts ou comentarios
        if (
            linha_strip.startswith("//")
            or linha_strip.startswith("/*")
            or linha_strip.startswith("*")
            or linha_strip.startswith("#define PINO_")
            or "TIMEOUT_" in linha_strip
            or "delay" in linha_strip
        ):
            continue

        # Nao deve haver comparacoes com literais de limiares (35, 45, 8, 15)
        for num in ("35", "45", "8", "15"):
            # Procura comparadores relacionais < 35, >= 45, etc.
            padrao = rf"[<>!=]=?\s*{num}(\.0+)?f?\b"
            assert not re.search(padrao, linha_strip), (
                f"Possivel limiar duplicado no sketch ({num}): '{linha_strip}'. "
                f"Utilize exclusivamente as funcoes de logica.h!"
            )


def test_pre_mortem_validacao_json_gerado(tmp_path: Path):
    """Compila um mini programa no host que chama montar_json e valida com json.loads."""
    gpp = shutil.which("g++")
    if not gpp:
        pytest.fail("g++ nao encontrado")

    codigo_teste = f"""#include "{FIRMWARE_DIR.as_posix()}/logica.h"
#include <cstdio>

int main() {{
    char buf[512];
    int n = montar_json(
        buf, sizeof(buf),
        "esp32-c1-temperatura_c",
        "esp32-lab-01",
        "sessao-demo",
        "c1",
        "temperatura_c",
        "C",
        38.00f,
        "ALERTA"
    );
    if (n < 0) return 1;
    std::printf("%s\\n", buf);
    return 0;
}}
"""
    cpp_file = tmp_path / "gera_json.cpp"
    cpp_file.write_text(codigo_teste, encoding="utf-8")
    binario = tmp_path / "gera_json.exe"

    res_comp = subprocess.run(
        [gpp, "-std=c++17", str(cpp_file), "-o", str(binario)],
        capture_output=True,
        text=True,
    )
    if res_comp.returncode != 0:
        # Quando montar_json ainda nao esta implementado (RED), pula ou falha
        pytest.fail(f"Compilacao do teste JSON falhou: {res_comp.stderr}")

    res_exec = subprocess.run([str(binario)], capture_output=True, text=True)
    assert res_exec.returncode == 0, f"Execucao falhou: {res_exec.stderr}"

    # Valida com o parser padrao do Python
    dados = json.loads(res_exec.stdout.strip())
    assert dados["schema_version"] == "1.0"
    assert dados["dispositivo_id"] == "esp32-lab-01"
    assert dados["tipo_dispositivo"] == "esp32"
    assert dados["sessao_laboratorio_id"] == "sessao-demo"
    assert dados["metrica"] == "temperatura_c"
    assert dados["unidade"] == "C"
    assert dados["valor"] == 38.0
    assert dados["status"] == "ALERTA"
