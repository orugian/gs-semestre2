"""Vínculos entre a Lambda e a API local que o código não mostra (só testes; a Lambda não muda).

A API (app/api) reenvia leituras pela outbox; a Lambda deduplica pelo hash do conteúdo. Se um
reenvio idêntico gerasse hash diferente, a nuvem gravaria duplicatas ou responderia 409.
"""

from __future__ import annotations

import copy

from citizentech_cloud.banco import calcular_hash_conteudo

# Mesmo formato montado por app/api/src/citizentech/outbox/cliente.py (enviar_leitura).
PAYLOAD_OUTBOX = {
    "evento_id": "esp32-lab-01-c1-temperatura_c",
    "dispositivo_id": "esp32-lab-01",
    "tipo_dispositivo": "esp32",
    "metrica": "temperatura_c",
    "unidade": "C",
    "valor": 38.0,
    "risco": "atencao",
    "alerta": True,
    "medido_em": "2026-11-17T13:10:00Z",
    "criado_em": "2026-11-17T13:10:01Z",
    "sessao_laboratorio_id": "LAB-ABC123",
    "ciclo_id": "c1",
}


def test_reenvio_identico_da_outbox_gera_o_mesmo_hash():
    reenvio = copy.deepcopy(PAYLOAD_OUTBOX)
    reenvio["criado_em"] = "2026-11-17T13:15:00Z"  # o reenvio muda só o instante de criação
    assert calcular_hash_conteudo(PAYLOAD_OUTBOX) == calcular_hash_conteudo(reenvio)


def test_valor_int_e_float_equivalentes_tem_o_mesmo_hash():
    como_int = dict(PAYLOAD_OUTBOX, valor=38)
    assert calcular_hash_conteudo(PAYLOAD_OUTBOX) == calcular_hash_conteudo(como_int)


def test_conteudo_diferente_muda_o_hash():
    alterado = dict(PAYLOAD_OUTBOX, valor=38.5)
    assert calcular_hash_conteudo(PAYLOAD_OUTBOX) != calcular_hash_conteudo(alterado)

