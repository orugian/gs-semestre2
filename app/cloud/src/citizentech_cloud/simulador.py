"""Simulador de dispositivo IoT para o cenario de laboratorio de monitoramento.

Compativel com o protocolo oficial do professor e com a outbox da API.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import UTC, datetime

from citizentech_cloud.risco import carregar_limiares


def enviar(
    url: str,
    payload: dict,
    chave: str | None = None,
    timeout: int = 30,
) -> tuple[int, dict]:
    """Envia uma leitura para a Function URL da Lambda ou servidor local."""
    corpo = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if chave:
        headers["X-Device-Key"] = chave

    req = urllib.request.Request(url, data=corpo, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            resposta_texto = resp.read().decode("utf-8")
            try:
                dados_resp = json.loads(resposta_texto)
            except Exception:
                dados_resp = {"texto": resposta_texto}
            return status, dados_resp
    except urllib.error.HTTPError as err:
        try:
            dados_erro = json.loads(err.read().decode("utf-8"))
        except Exception:
            dados_erro = {"erro": err.reason}
        return err.code, dados_erro


def gerar_leituras(
    cenario: str,
    total_leituras: int = 5,
    sem_relato: bool = False,
) -> list[dict]:
    """Gera lista de payloads para o cenario selecionado."""
    limiares = carregar_limiares()
    cenarios_map = {
        c["nome"]: c
        for c in limiares.get("cenarios_demonstracao", [])
    }

    leituras = []
    temp_evolucao = 30.0

    for i in range(total_leituras):
        evento_id = str(uuid.uuid4())
        agora = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        if cenario == "evolucao":
            metrica = "temperatura_c"
            valor = round(temp_evolucao, 2)
            temp_evolucao += 4.0  # Cruza de 30 para 34, 38 (atencao), 42, 46 (critico)
            unidade = "C"
            relato_texto = f"Monitoramento em bancada - temperatura em evolucao ({valor} C)"
        elif cenario in cenarios_map:
            dados_cen = cenarios_map[cenario]
            # Alterna entre temperatura e distancia
            if i % 2 == 0:
                metrica = "temperatura_c"
                valor = float(dados_cen["temperatura_c"])
                unidade = "C"
            else:
                metrica = "distancia_cm"
                valor = float(dados_cen["distancia_cm"])
                unidade = "cm"
            relato_texto = f"Monitoramento estavel bancada ({cenario}: {metrica}={valor})"
        else:
            metrica = "temperatura_c"
            valor = 25.0
            unidade = "C"
            relato_texto = f"Leitura padrao {cenario}"

        payload = {
            "evento_id": evento_id,
            "dispositivo_id": "lab-iot-bancada-01",
            "tipo_dispositivo": "sensor_bancada",
            "latitude": -23.5505,
            "longitude": -46.6333,
            "metrica": metrica,
            "valor": valor,
            "unidade": unidade,
            "medido_em": agora,
        }
        if not sem_relato:
            payload["relato"] = relato_texto

        leituras.append(payload)

    return leituras


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Simulador de leituras IoT CitizenTech")
    parser.add_argument(
        "--url",
        default=os.environ.get("FUNCTION_URL", "http://localhost:8099/ocorrencias"),
        help="URL de ingestao da Function URL ou emulador local",
    )
    parser.add_argument(
        "--cenario",
        choices=["normal", "atencao", "critico", "evolucao"],
        default="evolucao",
        help="Cenario de teste para injetar leituras",
    )
    parser.add_argument(
        "--leituras",
        type=int,
        default=5,
        help="Quantidade de medicoes a enviar",
    )
    parser.add_argument(
        "--intervalo",
        type=float,
        default=1.0,
        help="Intervalo em segundos entre envios",
    )
    parser.add_argument(
        "--com-chave",
        action="store_true",
        help="Envia X-Device-Key lida da variavel de ambiente DEVICE_KEY",
    )
    parser.add_argument(
        "--sem-relato",
        action="store_true",
        help="Omite o campo 'relato' do payload",
    )

    args = parser.parse_args(argv)

    chave = os.environ.get("DEVICE_KEY") if args.com_chave else None
    if args.com_chave and not chave:
        sys.stderr.write(
            "Aviso: --com-chave especificado, mas DEVICE_KEY nao esta definida no ambiente.\n"
        )

    # A Function URL vem sem caminho (como no simulador do professor): a rota e /ocorrencias.
    destino = args.url.rstrip("/")
    if not destino.endswith("/ocorrencias"):
        destino += "/ocorrencias"

    leituras = gerar_leituras(args.cenario, args.leituras, args.sem_relato)
    print(
        f"=== Simulador: cenario={args.cenario}, envios={len(leituras)}, url={destino} ==="
    )

    falhas = 0
    for i, payload in enumerate(leituras, start=1):
        status, resp = enviar(destino, payload, chave=chave)
        resp_id = resp.get("id")
        risco = resp.get("nivel_risco", "N/A")
        sentimento = resp.get("sentimento", "N/A")
        alerta = resp.get("alerta", False)

        if status >= 400:
            falhas += 1
            erro = resp.get("erro", "N/A")
            detalhes = resp.get("detalhes", "")
            msg_erro = f"erro={erro}"
            if detalhes:
                msg_erro += f" | detalhes={detalhes}"
            print(
                f"[{i}/{len(leituras)}] {payload['metrica']}={payload['valor']} -> "
                f"HTTP {status} | {msg_erro}"
            )
        else:
            print(
                f"[{i}/{len(leituras)}] {payload['metrica']}={payload['valor']} -> "
                f"HTTP {status} | ID={resp_id} | risco={risco} | "
                f"sentimento={sentimento} | alerta={alerta}"
            )

        if i < len(leituras) and args.intervalo > 0:
            time.sleep(args.intervalo)

    if falhas:
        print(f"=== Simulacao concluida com {falhas} envio(s) recusado(s) ===")
        return 1
    print("=== Simulacao concluida com sucesso ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
