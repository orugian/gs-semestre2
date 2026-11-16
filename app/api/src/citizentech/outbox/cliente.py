"""Cliente HTTP para despacho seguro a fronteira Lambda (T12, T13, D24)."""

import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx


@dataclass(frozen=True)
class ResultadoEnvio:
    sucesso: bool
    estado_final: str
    codigo_erro: str | None = None
    status_code: int | None = None


class ClienteLambda:
    """Cliente HTTP com timeout rigoroso, redirect desabilitado e validacao de envelope."""

    def __init__(
        self,
        url: str | None = None,
        chave_dispositivo: str | None = None,
        timeout: float = 5.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.url = url or os.environ.get("FUNCTION_URL", "")
        self.chave_dispositivo = chave_dispositivo or os.environ.get("DEVICE_KEY", "")
        self.timeout = timeout
        self.transport = transport

    def enviar_leitura(self, registro: dict[str, Any]) -> ResultadoEnvio:
        if not self.url or not self.chave_dispositivo:
            return ResultadoEnvio(
                sucesso=False,
                estado_final="pendente_nuvem",
                codigo_erro="CONFIGURACAO_AUSENTE",
            )

        parsed = urlparse(self.url)
        scheme = parsed.scheme.lower()
        hostname = (parsed.hostname or "").lower()

        valida = scheme == "https" or (
            scheme == "http" and hostname in ("localhost", "127.0.0.1")
        )
        if not valida:
            return ResultadoEnvio(
                sucesso=False,
                estado_final="erro_permanente",
                codigo_erro="URL_INSEGURA",
            )

        # Minimizacao de dados (D13/D22): estritamente telemetria sem relato nem PII
        payload_nuvem = {
            "evento_id": registro["evento_id"],
            "dispositivo_id": registro["dispositivo_id"],
            "tipo_dispositivo": registro.get("tipo_dispositivo") or "esp32",
            "metrica": registro["metrica"],
            "unidade": registro["unidade"],
            "valor": float(registro["valor"]),
            "risco": registro["risco"],
            "alerta": bool(registro["alerta"]),
            "medido_em": registro["medido_em"],
            "criado_em": registro.get("criado_em", registro["medido_em"]),
        }
        # A Lambda exige 1–64 caracteres quando o campo vem; vazio é omitido, não enviado como "".
        for campo in ("sessao_laboratorio_id", "ciclo_id"):
            if registro.get(campo):
                payload_nuvem[campo] = registro[campo]

        if registro.get("relato_redigido"):
            payload_nuvem["relato"] = str(registro["relato_redigido"])[:280]

        headers = {
            "Content-Type": "application/json",
            "X-Device-Key": self.chave_dispositivo,
        }

        try:
            with httpx.Client(
                timeout=self.timeout,
                follow_redirects=False,
                transport=self.transport,
            ) as client:
                resp = client.post(self.url, json=payload_nuvem, headers=headers)
        except httpx.TimeoutException:
            return ResultadoEnvio(
                sucesso=False,
                estado_final="pendente_nuvem",
                codigo_erro="TIMEOUT",
            )
        except (httpx.ConnectError, httpx.NetworkError):
            return ResultadoEnvio(
                sucesso=False,
                estado_final="pendente_nuvem",
                codigo_erro="CONEXAO_RECUSADA",
            )
        except Exception:
            return ResultadoEnvio(
                sucesso=False,
                estado_final="pendente_nuvem",
                codigo_erro="ERRO_DESCONHECIDO",
            )

        status_code = resp.status_code

        # 1. Sucesso (200 ou 201) com validacao estrita do envelope acordado
        if status_code in (200, 201):
            try:
                corpo = resp.json()
            except Exception:
                # 200 com HTML ou texto arbitrario nao pode ser ack silencioso
                return ResultadoEnvio(
                    sucesso=False,
                    estado_final="pendente_nuvem",
                    codigo_erro="ENVELOPE_INVALIDO",
                    status_code=status_code,
                )

            id_remoto = corpo.get("id") if isinstance(corpo, dict) else None
            ack_valido = (
                isinstance(corpo, dict)
                and corpo.get("evento_id") == registro["evento_id"]
                and isinstance(id_remoto, (str, int))
                and not isinstance(id_remoto, bool)
                and str(id_remoto).strip() != ""
            )
            if not ack_valido:
                return ResultadoEnvio(
                    sucesso=False,
                    estado_final="pendente_nuvem",
                    codigo_erro="ENVELOPE_INVALIDO",
                    status_code=status_code,
                )

            return ResultadoEnvio(
                sucesso=True,
                estado_final="sincronizado",
                codigo_erro=None,
                status_code=status_code,
            )

        # 2. Conflito permanente na nuvem (409)
        if status_code == 409:
            return ResultadoEnvio(
                sucesso=False,
                estado_final="conflito",
                codigo_erro="CONFLITO_409",
                status_code=status_code,
            )

        # 3. Erros permanentes: payload rejeitado (400, 413, 422) ou credencial recusada (401, 403).
        # 404/405 ficam como transitorios: indicam URL mal configurada, que pode ser corrigida.
        if status_code in (400, 401, 403, 413, 422):
            return ResultadoEnvio(
                sucesso=False,
                estado_final="erro_permanente",
                codigo_erro="ERRO_CLIENTE_4XX",
                status_code=status_code,
            )

        # 4. Rate limit (429) -> retry com backoff
        if status_code == 429:
            return ResultadoEnvio(
                sucesso=False,
                estado_final="pendente_nuvem",
                codigo_erro="RATE_LIMIT_429",
                status_code=status_code,
            )

        # 5. Erro interno do servidor ou gateway (5xx) -> retry com backoff
        if 500 <= status_code < 600:
            return ResultadoEnvio(
                sucesso=False,
                estado_final="pendente_nuvem",
                codigo_erro="ERRO_SERVIDOR_5XX",
                status_code=status_code,
            )

        # Outros status inesperados
        return ResultadoEnvio(
            sucesso=False,
            estado_final="pendente_nuvem",
            codigo_erro="ERRO_REMOTO_INDEFINIDO",
            status_code=status_code,
        )
