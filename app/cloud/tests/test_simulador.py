"""Testes unitarios e de integracao local para o simulador de dispositivos IoT."""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from citizentech_cloud import simulador


class DummyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        tamanho = int(self.headers.get("Content-Length", 0))
        corpo = self.rfile.read(tamanho).decode("utf-8")
        dados = json.loads(corpo)

        chave_recebida = self.headers.get("X-Device-Key")
        resp = {
            "id": 999,
            "evento_id": dados.get("evento_id"),
            "dispositivo_id": dados.get("dispositivo_id"),
            "nivel_risco": "normal",
            "alerta": False,
            "sentimento": "neutral",
            "chave_presente": bool(chave_recebida),
        }
        corpo_resp = json.dumps(resp).encode("utf-8")
        self.send_response(201)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(corpo_resp)

    def log_message(self, format, *args):
        pass  # Silenciar logs do server de teste


@pytest.fixture
def servidor_http_dummy():
    servidor = HTTPServer(("127.0.0.1", 0), DummyHandler)
    porta = servidor.server_address[1]
    thread = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{porta}/ocorrencias"
    servidor.shutdown()
    servidor.server_close()


def test_gerar_leituras_cenarios():
    for cen in ["normal", "atencao", "critico"]:
        leituras = simulador.gerar_leituras(cenario=cen, total_leituras=2, sem_relato=False)
        assert len(leituras) == 2
        assert "evento_id" in leituras[0]
        assert "relato" in leituras[0]

    # Teste sem relato
    leituras_sem = simulador.gerar_leituras(cenario="normal", total_leituras=1, sem_relato=True)
    assert "relato" not in leituras_sem[0]

    # Teste evolucao (temperatura cresce)
    leituras_evo = simulador.gerar_leituras(cenario="evolucao", total_leituras=5)
    assert len(leituras_evo) == 5
    temps = [leitura["valor"] for leitura in leituras_evo]
    assert temps == sorted(temps)
    assert temps[-1] >= 45.0  # Cruzou para critico


def test_enviar_e_simulador_cli_sem_vazar_chave(servidor_http_dummy, monkeypatch, capsys):
    chave_secreta = "super-chave-secreta-xyz"
    monkeypatch.setenv("DEVICE_KEY", chave_secreta)

    # 1. Teste da funcao enviar diretamente
    status, corpo = simulador.enviar(
        servidor_http_dummy,
        {"dispositivo_id": "teste-sim", "metrica": "temperatura_c", "valor": 25.0},
        chave=chave_secreta,
    )
    assert status == 201
    assert corpo["id"] == 999
    assert corpo["chave_presente"] is True

    # 2. Teste do loop principal CLI
    codigo = simulador.main([
        "--url", servidor_http_dummy,
        "--cenario", "normal",
        "--leituras", "3",
        "--intervalo", "0",
        "--com-chave",
    ])
    assert codigo == 0

    captured = capsys.readouterr()
    assert "HTTP 201 | ID=999" in captured.out
    # Seguranca: A chave NUNCA deve ser impressa em stdout ou stderr
    assert chave_secreta not in captured.out
    assert chave_secreta not in captured.err


def test_simulador_default_cenario_evolucao(servidor_http_dummy, capsys):
    """Quando --cenario nao e passado, o padrao deve ser 'evolucao'."""
    codigo = simulador.main([
        "--url", servidor_http_dummy,
        "--leituras", "1",
        "--intervalo", "0",
    ])
    assert codigo == 0
    captured = capsys.readouterr()
    assert "cenario=evolucao" in captured.out


class DummyHandlerErro400(BaseHTTPRequestHandler):
    def do_POST(self):
        corpo_resp = json.dumps({
            "erro": "Valor invalido",
            "detalhes": "temperatura fora da faixa permitida",
        }).encode("utf-8")
        self.send_response(400)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(corpo_resp)

    def log_message(self, format, *args):
        pass


@pytest.fixture
def servidor_http_erro400():
    servidor = HTTPServer(("127.0.0.1", 0), DummyHandlerErro400)
    porta = servidor.server_address[1]
    thread = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{porta}/ocorrencias"
    servidor.shutdown()
    servidor.server_close()


def test_simulador_imprime_erro_quando_status_maior_ou_igual_400(servidor_http_erro400, capsys):
    """Quando status >= 400, o simulador deve imprimir erro e detalhes da resposta."""
    simulador.main([
        "--url", servidor_http_erro400,
        "--leituras", "1",
        "--intervalo", "0",
    ])
    captured = capsys.readouterr()
    assert "HTTP 400" in captured.out
    assert "Valor invalido" in captured.out
    assert "temperatura fora da faixa permitida" in captured.out


class HandlerRotas(BaseHTTPRequestHandler):
    caminhos: list[str] = []

    def do_POST(self):
        HandlerRotas.caminhos.append(self.path)
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if self.path.rstrip("/") == "/ocorrencias":
            codigo, corpo = 201, {"id": 1, "nivel_risco": "normal", "alerta": False}
        else:
            codigo, corpo = 404, {"erro": "Nao encontrado", "detalhes": "rota"}
        dados = json.dumps(corpo).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(dados)

    def log_message(self, format, *args):
        pass


@pytest.fixture
def servidor_rotas():
    HandlerRotas.caminhos = []
    servidor = HTTPServer(("127.0.0.1", 0), HandlerRotas)
    thread = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{servidor.server_address[1]}"
    servidor.shutdown()
    servidor.server_close()


@pytest.mark.parametrize("sufixo", ["", "/", "/ocorrencias", "/ocorrencias/"])
def test_url_base_da_function_url_recebe_rota_ocorrencias(servidor_rotas, sufixo, capsys):
    """A Function URL vem sem caminho (como no simulador do professor): anexar /ocorrencias."""
    codigo = simulador.main(
        ["--url", servidor_rotas + sufixo, "--cenario", "normal", "--leituras", "1",
         "--intervalo", "0"]
    )
    assert HandlerRotas.caminhos == ["/ocorrencias"]
    assert codigo == 0
    assert "HTTP 201" in capsys.readouterr().out


def test_simulador_retorna_1_e_nao_diz_sucesso_quando_ha_erro(servidor_http_erro400, capsys):
    codigo = simulador.main(
        ["--url", servidor_http_erro400, "--cenario", "normal", "--leituras", "1",
         "--intervalo", "0"]
    )
    saida = capsys.readouterr().out
    assert codigo == 1
    assert "concluida com sucesso" not in saida
