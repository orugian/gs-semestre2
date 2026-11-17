"""Regras de canonicalizacao idempotente para telemetria (D2, S3)."""

import math
from typing import Any

from citizentech.leituras.esquemas import parsear_data_iso


def normalizar_para_comparacao(dados: dict[str, Any]) -> dict[str, Any]:
    """Extrai campos estaveis de negocio para verificacao de idempotencia."""
    valor_float = float(dados["valor"])
    ciclo = dados.get("ciclo_id") or ""
    sessao = dados.get("sessao_laboratorio_id") or ""
    tipo_disp = dados.get("tipo_dispositivo") or "esp32"
    unidade = dados.get("unidade") or ""
    metrica = dados.get("metrica") or ""
    dispositivo_id = dados.get("dispositivo_id") or ""
    evento_id = dados.get("evento_id") or ""

    return {
        "evento_id": evento_id,
        "dispositivo_id": dispositivo_id,
        "metrica": metrica,
        "unidade": unidade,
        "valor": valor_float,
        "sessao_laboratorio_id": sessao,
        "ciclo_id": ciclo,
        "tipo_dispositivo": tipo_disp,
    }


def comparar_payloads_identicos(existente: dict[str, Any], novo: dict[str, Any]) -> bool:
    """Verifica se o novo payload e identico ao existente segundo as regras estaveis.

    - Campos estaveis: evento_id, dispositivo_id, metrica, unidade, valor, sessao, ciclo, tipo_disp.
    - medido_em: se omitido no payload novo, reaproveita o existente (considera compativel).
      Se fornecido explicitamente, deve coincidir com o medido_em original apos normalizacao UTC.
    """
    existente_norm = normalizar_para_comparacao(existente)
    novo_norm = normalizar_para_comparacao(novo)

    # 1. Checa identificadores e metrica
    campos_estaveis = (
        "evento_id",
        "dispositivo_id",
        "metrica",
        "sessao_laboratorio_id",
        "ciclo_id",
        "tipo_dispositivo",
    )
    for campo in campos_estaveis:
        if existente_norm[campo] != novo_norm[campo]:
            return False

    # 2. Checa unidade se fornecida no novo
    if novo_norm["unidade"] and existente_norm["unidade"]:
        if novo_norm["unidade"] != existente_norm["unidade"]:
            return False

    # 3. Checa valor numerico
    if not math.isclose(existente_norm["valor"], novo_norm["valor"], rel_tol=1e-9, abs_tol=1e-9):
        return False

    # 4. Checa medido_em
    if "medido_em_informado" in novo:
        informou_medido_em = bool(novo["medido_em_informado"])
    else:
        informou_medido_em = "medido_em" in novo and novo["medido_em"] not in (None, "")

    if informou_medido_em:
        medido_novo = novo.get("medido_em")
        medido_existente = existente.get("medido_em")
        try:
            iso_novo = parsear_data_iso(medido_novo)
            iso_existente = parsear_data_iso(medido_existente)
            if iso_novo != iso_existente:
                return False
        except Exception:
            return False

    return True
