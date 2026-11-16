"""Testes do adaptador ClienteLLM com mocks de transporte."""

import json
import logging
from typing import Any

import httpx
import pytest

from citizentech.llm.cliente import ClienteLLM, ErroLLM


def test_content_nulo_faz_retry_e_cai_no_fallback():
    """Testa se content: null aciona retry no modelo padrao e cai no fallback."""
    chamadas: list[httpx.Request] = []
    modelo_padrao = "deepseek/deepseek-v4.1-flash-1017"
    modelo_fallback = "xiaomi/mimo-v2.6-flash"

    def handler(request: httpx.Request) -> httpx.Response:
        chamadas.append(request)
        payload = json.loads(request.content.decode("utf-8"))
        model = payload.get("model")

        if model == modelo_padrao:
            corpo = {
                "id": "gen-1",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": None,
                        }
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 20},
            }
            return httpx.Response(200, json=corpo)
        elif model == modelo_fallback:
            corpo = {
                "id": "gen-2",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": json.dumps({"competencias": []}),
                        }
                    }
                ],
                "usage": {"prompt_tokens": 12, "completion_tokens": 25},
            }
            return httpx.Response(200, json=corpo)
        return httpx.Response(400, json={"error": "modelo desconhecido"})

    transport = httpx.MockTransport(handler)
    cliente = ClienteLLM(
        api_key="sk-or-v1-teste",
        base_url="https://openrouter.ai/api/v1",
        modelo=modelo_padrao,
        modelo_fallback=modelo_fallback,
        transport=transport,
    )

    schema = {
        "type": "object",
        "properties": {"competencias": {"type": "array"}},
    }
    resposta = cliente.gerar_json(
        mensagens=[{"role": "user", "content": "teste"}],
        schema=schema,
        nome_schema="extracao_competencias",
    )

    assert resposta.modelo == modelo_fallback
    assert resposta.tentativas == 3

    for req in chamadas:
        corpo_enviado = json.loads(req.content.decode("utf-8"))
        assert corpo_enviado["response_format"]["type"] == "json_schema"
        assert corpo_enviado["provider"]["data_collection"] == "deny"
        assert corpo_enviado["provider"]["require_parameters"] is True
        # 16/11: com 2000 o raciocinio esgota o orcamento (finish=length, content vazio)
        assert corpo_enviado["max_tokens"] >= 6000
        assert corpo_enviado["reasoning"]["max_tokens"] <= corpo_enviado["max_tokens"] // 2
        assert corpo_enviado["temperature"] == 0


def test_um_retry_no_mesmo_modelo_para_json_invalido():
    """Valida 1 retry no mesmo modelo quando o JSON for invalido, tendo sucesso na tentativa 2."""
    tentativa = 0
    modelo_padrao = "deepseek/deepseek-v4.1-flash-1017"

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal tentativa
        tentativa += 1
        if tentativa == 1:
            corpo = {
                "choices": [{"message": {"role": "assistant", "content": "json-quebrado {{"}}],
                "usage": {"total_tokens": 15},
            }
        else:
            corpo = {
                "choices": [{"message": {"role": "assistant", "content": '{"competencias": []}'}}],
                "usage": {"total_tokens": 20},
            }
        return httpx.Response(200, json=corpo)

    cliente = ClienteLLM(
        api_key="sk-or-v1-teste",
        modelo=modelo_padrao,
        modelo_fallback="xiaomi/mimo-v2.6-flash",
        transport=httpx.MockTransport(handler),
    )

    resposta = cliente.gerar_json(
        mensagens=[{"role": "user", "content": "ola"}],
        schema={"type": "object"},
        nome_schema="teste",
    )
    assert resposta.modelo == modelo_padrao
    assert resposta.tentativas == 2
    assert resposta.dados == {"competencias": []}


def test_status_401_vai_direto_ao_fallback():
    """401/402/403 do provedor nao fazem retry no mesmo modelo e vao direto ao fallback."""
    chamadas: list[str] = []
    modelo_padrao = "deepseek/deepseek-v4.1-flash-1017"
    modelo_fallback = "xiaomi/mimo-v2.6-flash"

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode("utf-8"))
        chamadas.append(payload["model"])
        if payload["model"] == modelo_padrao:
            return httpx.Response(401, json={"error": "unauthorized"})
        return httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": '{"ok": true}'}}]},
        )

    cliente = ClienteLLM(
        api_key="sk-or-v1-teste",
        modelo=modelo_padrao,
        modelo_fallback=modelo_fallback,
        transport=httpx.MockTransport(handler),
    )

    resposta = cliente.gerar_json(
        mensagens=[{"role": "user", "content": "ola"}],
        schema={"type": "object"},
        nome_schema="teste",
    )
    assert resposta.modelo == modelo_fallback
    assert resposta.tentativas == 2
    assert chamadas == [modelo_padrao, modelo_fallback]


def test_status_402_ou_403_vai_direto_ao_fallback():
    """402 Payment Required e 403 Forbidden vao direto ao fallback."""
    chamadas: list[str] = []
    modelo_padrao = "deepseek/deepseek-v4.1-flash-1017"
    modelo_fallback = "xiaomi/mimo-v2.6-flash"

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode("utf-8"))
        chamadas.append(payload["model"])
        if payload["model"] == modelo_padrao:
            return httpx.Response(402, json={"error": "payment required"})
        return httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": '{"ok": true}'}}]},
        )

    cliente = ClienteLLM(
        api_key="sk-or-v1-teste",
        modelo=modelo_padrao,
        modelo_fallback=modelo_fallback,
        transport=httpx.MockTransport(handler),
    )

    resposta = cliente.gerar_json(
        mensagens=[{"role": "user", "content": "ola"}],
        schema={"type": "object"},
        nome_schema="teste",
    )
    assert resposta.modelo == modelo_fallback
    assert resposta.tentativas == 2
    assert chamadas == [modelo_padrao, modelo_fallback]


def test_fallback_tambem_falha_lanca_erro_llm():
    """Quando o fallback tambem falha, lanca ErroLLM."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "server error"})

    cliente = ClienteLLM(
        api_key="sk-or-v1-teste",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(ErroLLM) as exc:
        cliente.gerar_json(
            mensagens=[{"role": "user", "content": "ola"}],
            schema={"type": "object"},
            nome_schema="teste",
        )
    assert "falha" in str(exc.value).lower() or "llm" in str(exc.value).lower()


def test_sem_chave_lanca_erro_llm_sem_rede(monkeypatch):
    """Sem chave de API configurada, lanca ErroLLM('configuracao ausente') sem chamar rede."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    foi_chamado = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal foi_chamado
        foi_chamado = True
        return httpx.Response(200, json={})

    cliente = ClienteLLM(api_key=None, transport=httpx.MockTransport(handler))

    with pytest.raises(ErroLLM) as exc:
        cliente.gerar_json(
            mensagens=[{"role": "user", "content": "ola"}],
            schema={"type": "object"},
            nome_schema="teste",
        )
    assert "configuracao ausente" in str(exc.value).lower()
    assert foi_chamado is False


def test_validar_lancando_value_error_conta_como_falha():
    """Se a funcao validar() lancar ValueError, conta como falha e aciona retry/fallback."""
    chamadas = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal chamadas
        chamadas += 1
        return httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": '{"num": 1}'}}]},
        )

    def validador(dados: dict[str, Any]) -> None:
        if chamadas < 2:
            raise ValueError("dado sem campo obrigatorio")

    cliente = ClienteLLM(
        api_key="sk-or-v1-teste",
        transport=httpx.MockTransport(handler),
    )

    resposta = cliente.gerar_json(
        mensagens=[{"role": "user", "content": "ola"}],
        schema={"type": "object"},
        nome_schema="teste",
        validar=validador,
    )
    assert resposta.tentativas == 2


def test_fences_markdown_json_aceitos():
    """Valida que blocos ```json ... ``` retornados pela LLM sao aceitos e parseados."""
    def handler(request: httpx.Request) -> httpx.Response:
        conteudo = "```json\n{\"resultado\": \"sucesso\"}\n```"
        return httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": conteudo}}]},
        )

    cliente = ClienteLLM(
        api_key="sk-or-v1-teste",
        transport=httpx.MockTransport(handler),
    )

    resposta = cliente.gerar_json(
        mensagens=[{"role": "user", "content": "ola"}],
        schema={"type": "object"},
        nome_schema="teste",
    )
    assert resposta.dados == {"resultado": "sucesso"}


def test_chave_e_conteudo_nunca_aparecem_em_log(caplog):
    """Garante que a chave de API e o conteudo enviado/recebido nunca aparecem em logs."""
    chave_secreta = "sk-or-v1-segredo-super-sigiloso-12345"
    texto_usuario = "Meu texto de curriculo totalmente confidencial"
    resposta_conteudo = "Resposta contendo segredo confidencial"

    def handler(request: httpx.Request) -> httpx.Response:
        corpo = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": json.dumps({"res": resposta_conteudo}),
                    }
                }
            ]
        }
        return httpx.Response(200, json=corpo)

    cliente = ClienteLLM(
        api_key=chave_secreta,
        transport=httpx.MockTransport(handler),
    )

    with caplog.at_level(logging.DEBUG):
        resposta = cliente.gerar_json(
            mensagens=[{"role": "user", "content": texto_usuario}],
            schema={"type": "object"},
            nome_schema="teste",
        )

    assert resposta.dados == {"res": resposta_conteudo}
    logs_texto = caplog.text
    assert chave_secreta not in logs_texto
    assert texto_usuario not in logs_texto
    assert resposta_conteudo not in logs_texto


def test_timeout_aciona_retry():
    """Timeout de rede e tratado como falha e aciona retry/fallback."""
    chamadas = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal chamadas
        chamadas += 1
        if chamadas == 1:
            raise httpx.ReadTimeout("Timeout de leitura")
        return httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": '{"ok": true}'}}]},
        )

    cliente = ClienteLLM(
        api_key="sk-or-v1-teste",
        transport=httpx.MockTransport(handler),
    )

    resposta = cliente.gerar_json(
        mensagens=[{"role": "user", "content": "ola"}],
        schema={"type": "object"},
        nome_schema="teste",
    )
    assert resposta.tentativas == 2
    assert resposta.dados == {"ok": True}
