"""Esquemas de dados e validacao rigorosa de leituras de telemetria CTP."""

import math
import re
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from citizentech.erros import ErroValidacaoLeitura
from citizentech.limiares import (
    MetricaDesconhecida,
    ValorInvalido,
    carregar_limiares,
    classificar_risco,
)

_ID_REGEX = re.compile(r"^[\w\-.:]{1,64}$")


def _validar_identificador(
    valor: Any,
    nome_campo: str,
    obrigatorio: bool = False,
) -> str:
    if valor is None or valor == "":
        if obrigatorio:
            raise ErroValidacaoLeitura(f"Campo obrigatorio '{nome_campo}' ausente.")
        return ""
    if isinstance(valor, bool) or not isinstance(valor, str):
        raise ErroValidacaoLeitura(f"Campo '{nome_campo}' deve ser uma string.")
    if "\r" in valor or "\n" in valor or "\x00" in valor:
        raise ErroValidacaoLeitura(f"Campo '{nome_campo}' contem caracteres de controle invalidos.")
    if not _ID_REGEX.match(valor):
        raise ErroValidacaoLeitura(
            f"Campo '{nome_campo}' contem caracteres invalidos ou tamanho acima de 64 caracteres."
        )
    return valor


def _parsear_data_iso(data_str: Any) -> str:
    if data_str is None or data_str == "":
        return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    if isinstance(data_str, bool) or not isinstance(data_str, str):
        raise ErroValidacaoLeitura("Campo 'medido_em' deve ser uma string ISO-8601.")

    try:
        normalizada = data_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalizada)
    except Exception as err:
        raise ErroValidacaoLeitura(
            "Formato de 'medido_em' invalido. Esperado timestamp ISO-8601 com timezone."
        ) from err

    if dt.tzinfo is None:
        raise ErroValidacaoLeitura(
            "Campo 'medido_em' deve conter informacao de fuso horario (timezone)."
        )

    try:
        dt_utc = dt.astimezone(UTC)
    except (ValueError, OverflowError) as err:
        raise ErroValidacaoLeitura("Data fora da faixa UTC suportada.") from err
    return dt_utc.isoformat(timespec="seconds").replace("+00:00", "Z")


def validar_e_processar_payload(dados: dict[str, Any]) -> dict[str, Any]:
    """Valida estritamente o payload bruto recebido, recalculando o risco e normalizando campos."""
    if not isinstance(dados, dict):
        raise ErroValidacaoLeitura("Corpo da requisicao deve ser um objeto JSON.")

    # 1. Campos minimos obrigatorios
    for campo in ("dispositivo_id", "metrica", "valor"):
        if campo not in dados:
            raise ErroValidacaoLeitura(f"Campo obrigatorio ausente: '{campo}'.")

    dispositivo_id = _validar_identificador(
        dados["dispositivo_id"],
        "dispositivo_id",
        obrigatorio=True,
    )

    # 2. Validacao estrita de valor (sem coercoes Pydantic/int(bool))
    valor = dados["valor"]
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ErroValidacaoLeitura(
            "Campo 'valor' invalido. Esperado numero (int ou float), rejeitados bool e string."
        )

    try:
        if not math.isfinite(valor):
            raise ErroValidacaoLeitura("Valor numerico nao pode ser NaN ou Infinito.")
    except OverflowError as err:
        raise ErroValidacaoLeitura("Valor numerico fora da faixa suportada.") from err

    # 3. Metrica e limiares compartilhados
    metrica = dados["metrica"]
    if isinstance(metrica, bool) or not isinstance(metrica, str):
        raise ErroValidacaoLeitura("Campo 'metrica' deve ser uma string.")

    limiares = carregar_limiares()
    catalogo = limiares.get("metricas", {})
    if metrica not in catalogo:
        conhecidas = ", ".join(sorted(catalogo.keys()))
        raise ErroValidacaoLeitura(
            f"Metrica desconhecida. Metricas conhecidas: {conhecidas}."
        )

    config_metrica = catalogo[metrica]

    # Regra de falha de sensor fisico (-127 para temperatura_c especificamente)
    if metrica == "temperatura_c" and valor == -127.0:
        raise ErroValidacaoLeitura(
            "Leitura de sensor invalida (-127 C indica falha de hardware ou sensor desconectado)."
        )

    # Validacao contra limiares (ex: valor minimo de distancia_cm)
    try:
        risco = classificar_risco(metrica, valor, limiares=limiares)
    except MetricaDesconhecida as err:
        raise ErroValidacaoLeitura("Metrica desconhecida.") from err
    except ValorInvalido as err:
        raise ErroValidacaoLeitura("Valor fora da faixa permitida para a metrica.") from err

    # 4. Unidade (inferida ou validada)
    unidade_esperada = config_metrica.get("unidade")
    if "unidade" in dados:
        unidade = dados["unidade"]
        if unidade is not None and unidade != "":
            invalida = (
                isinstance(unidade, bool)
                or not isinstance(unidade, str)
                or unidade != unidade_esperada
            )
            if invalida:
                raise ErroValidacaoLeitura(
                    f"Unidade incompativel para metrica '{metrica}'. "
                    f"Esperada: '{unidade_esperada}'."
                )
        else:
            unidade = unidade_esperada
    else:
        unidade = unidade_esperada

    # 5. Envelope opcional documentado e validacoes de tipo
    if "schema_version" in dados:
        sv = dados["schema_version"]
        if isinstance(sv, bool) or not isinstance(sv, str) or sv != "1.0":
            raise ErroValidacaoLeitura("Campo 'schema_version' incompativel. Esperado '1.0'.")

    if "relato" in dados:
        relato_val = dados["relato"]
        if relato_val is not None:
            if isinstance(relato_val, bool) or not isinstance(relato_val, str):
                raise ErroValidacaoLeitura("Campo 'relato' deve ser uma string.")
            if len(relato_val) > 280:
                raise ErroValidacaoLeitura("Campo 'relato' excede o limite de 280 caracteres.")

    if "status" in dados:
        st_val = dados["status"]
        if isinstance(st_val, bool) or not isinstance(st_val, str):
            raise ErroValidacaoLeitura("Campo 'status' deve ser uma string.")
        if st_val.strip().upper() not in {"OK", "ALERTA", "ERRO"}:
            raise ErroValidacaoLeitura("Campo 'status' desconhecido.")
        if st_val.strip().upper() == "ERRO":
            raise ErroValidacaoLeitura(
                "Medida com status de erro do dispositivo nao e valida para registro."
            )

    if "evento_id" in dados:
        ev_raw = dados["evento_id"]
        if isinstance(ev_raw, bool) or not isinstance(ev_raw, str):
            raise ErroValidacaoLeitura("Campo 'evento_id' deve ser uma string.")
        evento_id = _validar_identificador(ev_raw, "evento_id", obrigatorio=True)
    else:
        evento_id = f"evt-{uuid4().hex}"

    if "ciclo_id" in dados:
        c_raw = dados["ciclo_id"]
        if isinstance(c_raw, bool) or not isinstance(c_raw, str):
            raise ErroValidacaoLeitura("Campo 'ciclo_id' deve ser uma string.")
        ciclo_id = _validar_identificador(c_raw, "ciclo_id")
    else:
        ciclo_id = ""

    if "sessao_laboratorio_id" in dados:
        s_raw = dados["sessao_laboratorio_id"]
        if isinstance(s_raw, bool) or not isinstance(s_raw, str):
            raise ErroValidacaoLeitura("Campo 'sessao_laboratorio_id' deve ser uma string.")
        sessao_id = _validar_identificador(s_raw, "sessao_laboratorio_id")
    else:
        sessao_id = ""

    if "tipo_dispositivo" in dados:
        t_raw = dados["tipo_dispositivo"]
        if isinstance(t_raw, bool) or not isinstance(t_raw, str):
            raise ErroValidacaoLeitura("Campo 'tipo_dispositivo' deve ser uma string.")
        tipo_disp = _validar_identificador(t_raw, "tipo_dispositivo", obrigatorio=True)
    else:
        tipo_disp = "esp32"

    medido_em_informado = (
        "medido_em" in dados
        and dados["medido_em"] is not None
        and dados["medido_em"] != ""
    )
    medido_em = _parsear_data_iso(dados.get("medido_em"))
    criado_em = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Alerta coerente com os limiares (atencao ou critico)
    alerta = risco in ("atencao", "critico")

    return {
        "evento_id": evento_id,
        "dispositivo_id": dispositivo_id,
        "sessao_laboratorio_id": sessao_id,
        "ciclo_id": ciclo_id,
        "tipo_dispositivo": tipo_disp,
        "metrica": metrica,
        "unidade": unidade,
        "valor": float(valor),
        "risco": risco,
        "alerta": alerta,
        "estado": "pendente_nuvem",
        "medido_em": medido_em,
        "criado_em": criado_em,
        "medido_em_informado": medido_em_informado,
    }

