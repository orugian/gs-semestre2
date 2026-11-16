"""Adaptador de cliente para provedores LLM (OpenRouter)."""

import json
import logging
import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger("citizentech.llm")


class ErroLLM(RuntimeError):
    """Excecao lancada quando ha falha de comunicacao ou configuracao com a LLM."""


@dataclass(frozen=True)
class RespostaLLM:
    """Resposta estruturada da LLM apos parse e validacao."""

    dados: dict[str, Any]
    modelo: str
    tentativas: int
    uso: dict[str, Any] | None


class ClienteLLM:
    """Cliente para geracao estruturada de JSON com retry e fallback."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        modelo: str | None = None,
        modelo_fallback: str | None = None,
        timeout: float = 60.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.base_url = (
            base_url
            or os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        ).rstrip("/")
        self.modelo = modelo or os.environ.get(
            "OPENROUTER_MODEL", "deepseek/deepseek-v4.1-flash-1017"
        )
        self.modelo_fallback = modelo_fallback or os.environ.get(
            "OPENROUTER_MODEL_FALLBACK", "xiaomi/mimo-v2.6-flash"
        )
        self.data_collection = os.environ.get("OPENROUTER_DATA_COLLECTION", "deny")
        self.timeout = timeout
        self.transport = transport

    def _executar_requisicao(
        self,
        cliente_http: httpx.Client,
        modelo_atual: str,
        mensagens: list[dict[str, Any]],
        schema: dict[str, Any],
        nome_schema: str,
        tentativa_num: int,
        validar: Callable[[dict[str, Any]], None] | None,
    ) -> tuple[bool, int | None, dict[str, Any] | None, dict[str, Any] | None]:
        """Executa uma tentativa isolada contra o modelo especificado."""
        t0 = time.monotonic()
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://citizentech.local",
            "X-Title": "CitizenTech",
            "Content-Type": "application/json",
        }
        payload = {
            "model": modelo_atual,
            "messages": mensagens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": nome_schema,
                    "strict": True,
                    "schema": schema,
                },
            },
            # Modelo padrao raciocina antes de responder; com 2000 tokens o raciocinio
            # esgotava o orcamento (finish_reason=length, content vazio; verificado 16/11).
            "max_tokens": 6000,
            "reasoning": {"max_tokens": 2000},
            "temperature": 0,
            "provider": {
                "require_parameters": True,
                "data_collection": self.data_collection,
            },
            "usage": {"include": True},
        }

        try:
            resp = cliente_http.post(url, headers=headers, json=payload)
            duracao = time.monotonic() - t0
            status_code = resp.status_code
            logger.info(
                "Chamada LLM modelo=%s status=%d tentativa=%d duracao=%.2fs",
                modelo_atual,
                status_code,
                tentativa_num,
                duracao,
            )

            if status_code != 200:
                return False, status_code, None, None

            corpo_json = resp.json()
            choices = corpo_json.get("choices") or []
            if not choices:
                return False, status_code, None, None

            content = choices[0].get("message", {}).get("content")
            if content is None or not str(content).strip():
                return False, status_code, None, None

            conteudo_str = str(content).strip()
            if conteudo_str.startswith("```json"):
                conteudo_str = conteudo_str[7:].strip()
            elif conteudo_str.startswith("```"):
                conteudo_str = conteudo_str[3:].strip()
            if conteudo_str.endswith("```"):
                conteudo_str = conteudo_str[:-3].strip()

            dados = json.loads(conteudo_str)
            if validar is not None:
                validar(dados)

            return True, status_code, dados, corpo_json.get("usage")
        except Exception as err:
            duracao = time.monotonic() - t0
            logger.warning(
                "Falha na tentativa LLM modelo=%s tentativa=%d duracao=%.2fs erro=%s",
                modelo_atual,
                tentativa_num,
                duracao,
                type(err).__name__,
            )
            return False, None, None, None

    def gerar_json(
        self,
        mensagens: list[dict[str, Any]],
        schema: dict[str, Any],
        nome_schema: str,
        validar: Callable[[dict[str, Any]], None] | None = None,
    ) -> RespostaLLM:
        """Gera resposta JSON com retry no modelo padrao e fallback."""
        if not self.api_key:
            raise ErroLLM("configuracao ausente: chave OPENROUTER_API_KEY nao informada.")

        total_tentativas = 0
        with httpx.Client(timeout=self.timeout, transport=self.transport) as cliente_http:
            # 1. Tentativa inicial no modelo padrao
            total_tentativas += 1
            sucesso, status_code, dados, uso = self._executar_requisicao(
                cliente_http,
                self.modelo,
                mensagens,
                schema,
                nome_schema,
                total_tentativas,
                validar,
            )
            if sucesso and dados is not None:
                return RespostaLLM(
                    dados=dados,
                    modelo=self.modelo,
                    tentativas=total_tentativas,
                    uso=uso,
                )

            # Se for 401, 402 ou 403, nao faz retry no mesmo modelo: vai direto ao fallback
            deve_tentar_novamente_padrao = status_code not in (401, 402, 403)

            if deve_tentar_novamente_padrao:
                # 2. Retry no modelo padrao
                total_tentativas += 1
                sucesso, status_code, dados, uso = self._executar_requisicao(
                    cliente_http,
                    self.modelo,
                    mensagens,
                    schema,
                    nome_schema,
                    total_tentativas,
                    validar,
                )
                if sucesso and dados is not None:
                    return RespostaLLM(
                        dados=dados,
                        modelo=self.modelo,
                        tentativas=total_tentativas,
                        uso=uso,
                    )

            # 3. Fallback (1 tentativa)
            total_tentativas += 1
            sucesso, status_code, dados, uso = self._executar_requisicao(
                cliente_http,
                self.modelo_fallback,
                mensagens,
                schema,
                nome_schema,
                total_tentativas,
                validar,
            )
            if sucesso and dados is not None:
                return RespostaLLM(
                    dados=dados,
                    modelo=self.modelo_fallback,
                    tentativas=total_tentativas,
                    uso=uso,
                )

        raise ErroLLM(
            f"Falha ao obter resposta estruturada da LLM apos {total_tentativas} tentativas."
        )


_cliente_padrao: ClienteLLM | None = None


def obter_cliente_llm() -> ClienteLLM:
    """Retorna o cliente LLM padrao para injecao de dependencias."""
    global _cliente_padrao
    if _cliente_padrao is None:
        _cliente_padrao = ClienteLLM()
    return _cliente_padrao
