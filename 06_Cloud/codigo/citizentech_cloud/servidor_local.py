"""Servidor HTTP local para emular a AWS Lambda Function URL na porta 8099."""

import argparse
import json
import logging
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

from citizentech_cloud.lambda_function import lambda_handler

logger = logging.getLogger("citizentech_cloud.servidor_local")


class EmuladorLambdaHandler(BaseHTTPRequestHandler):
    """Handler HTTP que converte requisicoes no formato de evento da Lambda Function URL."""

    def do_GET(self):
        self._processar_requisicao()

    def do_POST(self):
        self._processar_requisicao()

    def do_PUT(self):
        self._processar_requisicao()

    def do_DELETE(self):
        self._processar_requisicao()

    def _processar_requisicao(self):
        partes_path = self.path.split("?", 1)
        raw_path = partes_path[0]
        raw_query = partes_path[1] if len(partes_path) > 1 else ""

        tamanho_corpo = int(self.headers.get("Content-Length", 0))
        corpo_bytes = self.rfile.read(tamanho_corpo) if tamanho_corpo > 0 else b""
        corpo_str = corpo_bytes.decode("utf-8") if corpo_bytes else None

        headers_dict = {k: v for k, v in self.headers.items()}

        evento = {
            "version": "2.0",
            "routeKey": "$default",
            "rawPath": raw_path,
            "rawQueryString": raw_query,
            "headers": headers_dict,
            "requestContext": {
                "http": {
                    "method": self.command,
                    "path": raw_path,
                    "protocol": self.protocol_version,
                    "sourceIp": self.client_address[0],
                }
            },
            "body": corpo_str,
            "isBase64Encoded": False,
        }

        try:
            resultado_lambda = lambda_handler(evento)
        except Exception as e:
            logger.exception("Erro interno no lambda_handler: %s", e)
            resultado_lambda = {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"erro": "Erro interno do servidor"}),
            }

        status = resultado_lambda.get("statusCode", 200)
        headers = resultado_lambda.get("headers", {})
        corpo = resultado_lambda.get("body", "")

        self.send_response(status)
        for h_nome, h_valor in headers.items():
            self.send_header(h_nome, h_valor)
        self.end_headers()

        if isinstance(corpo, str):
            self.wfile.write(corpo.encode("utf-8"))
        elif isinstance(corpo, bytes):
            self.wfile.write(corpo)

    def log_message(self, format, *args):
        # Redireciona logs do BaseHTTPRequestHandler para o logging padrao
        logger.debug(
            "%s - - [%s] %s",
            self.client_address[0],
            self.log_date_time_string(),
            format % args,
        )


def criar_servidor(porta: int = 8099, host: str = "127.0.0.1") -> HTTPServer:
    """Cria e retorna a instancia do HTTPServer para a Lambda local."""
    return HTTPServer((host, porta), EmuladorLambdaHandler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Emulador local da Lambda Function URL CitizenTech"
    )
    parser.add_argument("--porta", type=int, default=8099, help="Porta HTTP (padrao: 8099)")
    parser.add_argument("--host", default="127.0.0.1", help="Host HTTP (padrao: 127.0.0.1)")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    servidor = criar_servidor(porta=args.porta, host=args.host)
    print(f"Emulador Lambda ativo em http://{args.host}:{args.porta}")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando emulador...")
    finally:
        servidor.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
