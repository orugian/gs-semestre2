"""Carregamento e validação da lista de ocupações elegíveis."""

import hashlib
import json
from pathlib import Path

from citizentech_ml.ingestao.modelos import Ocupacoes


def carregar_ocupacoes(caminho: str | Path) -> Ocupacoes:
    """Lê e valida o arquivo JSON de ocupações.

    Regras:
    - O arquivo precisa conter 'destinos' com pelo menos um destino.
    - Cada código CBO deve ter exatamente 6 dígitos numéricos.
    - Conjuntos disjuntos: nenhum código pode aparecer em mais de um destino ou na reserva.
    - Retorna a estrutura Ocupacoes com codigos_ingestao e hash estável.
    """
    caminho_path = Path(caminho)
    if not caminho_path.exists():
        raise FileNotFoundError(f"Arquivo de ocupações não encontrado: {caminho_path}")

    conteudo_bytes = caminho_path.read_bytes()
    hash_sha256 = hashlib.sha256(conteudo_bytes).hexdigest()

    dados = json.loads(conteudo_bytes.decode("utf-8"))

    versao = dados.get("versao", "desconhecida")
    destinos = dados.get("destinos")
    if not isinstance(destinos, dict) or len(destinos) == 0:
        raise ValueError("O arquivo de ocupações deve conter ao menos um destino em 'destinos'.")

    codigos_vistos: dict[str, str] = {}
    todos_cbo_destinos: set[str] = set()

    for destino_id, info in destinos.items():
        if not isinstance(info, dict):
            raise ValueError(f"Destino '{destino_id}' deve ser um objeto JSON.")
        cbos = info.get("cbo6", [])
        if not isinstance(cbos, list) or len(cbos) == 0:
            raise ValueError(f"Destino '{destino_id}' não possui lista 'cbo6' válida.")

        for cbo in cbos:
            if not isinstance(cbo, str) or len(cbo) != 6 or not cbo.isdigit():
                raise ValueError(
                    f"Código CBO inválido: '{cbo}'. Deve conter exatamente 6 dígitos numéricos."
                )
            if cbo in codigos_vistos:
                origem_previa = codigos_vistos[cbo]
                raise ValueError(
                    f"Código CBO duplicado: '{cbo}' já definido em '{origem_previa}' "
                    f"e repetido em '{destino_id}'."
                )
            codigos_vistos[cbo] = destino_id
            todos_cbo_destinos.add(cbo)

    cbo6_reserva_raw = dados.get("cbo6_reserva", [])
    if not isinstance(cbo6_reserva_raw, list):
        raise ValueError("'cbo6_reserva' deve ser uma lista.")

    cbo6_reserva: list[str] = []
    for cbo in cbo6_reserva_raw:
        if not isinstance(cbo, str) or len(cbo) != 6 or not cbo.isdigit():
            raise ValueError(
                f"Código CBO inválido na reserva: '{cbo}'. "
                "Deve conter exatamente 6 dígitos numéricos."
            )
        if cbo in codigos_vistos:
            origem_previa = codigos_vistos[cbo]
            raise ValueError(
                f"Código CBO da reserva duplicado: '{cbo}' já definido em '{origem_previa}'."
            )
        codigos_vistos[cbo] = "cbo6_reserva"
        cbo6_reserva.append(cbo)

    codigos_ingestao = todos_cbo_destinos | set(cbo6_reserva)

    return Ocupacoes(
        versao=versao,
        destinos=destinos,
        cbo6_reserva=cbo6_reserva,
        codigos_ingestao=codigos_ingestao,
        hash=hash_sha256,
    )
