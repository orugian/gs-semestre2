"""Repositorio Oracle (19c) para caminhos escolhidos, planos e checkpoints."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from citizentech.banco.conexao import ErroBancoIndisponivel, obter_conexao
from citizentech.plano.dominio import AVISO_PLANO, EXPLICACAO_REGRA_V1, REGRA_PLANO_V1

logger = logging.getLogger("citizentech.plano")


def _formatar_iso_utc(dt: Any) -> str:
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        else:
            dt = dt.astimezone(UTC)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return str(dt)


def _deserializar_json(valor: Any) -> Any:
    """Converte valor do banco (objeto nativo, LOB ou str) em objeto Python."""
    if isinstance(valor, (dict, list)):
        return valor
    if hasattr(valor, "read"):
        valor = valor.read()
    if isinstance(valor, (bytes, bytearray)):
        valor = valor.decode("utf-8")
    if isinstance(valor, str):
        return json.loads(valor)
    return valor


def verificar_comparacao_usuario(
    comparacao_id: str,
    usuario_id: str,
    destino_id: str,
) -> tuple[bool, str | None]:
    """Verifica se a comparacao existe, pertence ao usuario e contem o destino.

    Retorna (valido, erro_tipo):
    - Se comparacao nao existe ou eh de outro usuario: (False, "404")
    - Se comparacao pertence ao usuario mas nao contem o destino: (False, "400")
    - Se tudo valido: (True, None)
    """
    import oracledb

    sql_comp = "SELECT usuario_id FROM comparacao WHERE id = :id"
    sql_dest = (
        "SELECT 1 FROM comparacao_destino WHERE comparacao_id = :comp_id AND destino_id = :dest_id"
    )

    try:
        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(sql_comp, {"id": comparacao_id})
                row = cursor.fetchone()
                if not row or row[0] != usuario_id:
                    return False, "404"

                cursor.execute(sql_dest, {"comp_id": comparacao_id, "dest_id": destino_id})
                if not cursor.fetchone():
                    return False, "400"

        return True, None
    except oracledb.Error as err:
        raise ErroBancoIndisponivel() from err


def salvar_caminho_e_plano(
    usuario_id: str,
    destino_id: str,
    destino_nome: str,
    comparacao_id: str | None,
    versao_catalogo: str,
    plano_dict: dict[str, Any],
    itens_classificados: list[dict[str, Any]],
) -> dict[str, Any]:
    """Persiste caminho escolhido, plano e checkpoints em transacao atomica no Oracle."""
    import oracledb

    caminho_id = uuid.uuid4().hex
    plano_id = uuid.uuid4().hex
    agora = datetime.now(UTC)
    agora_iso = _formatar_iso_utc(agora)

    # Prepara base_json para rastreabilidade T08 SEM trechos de origem
    base_limpa: list[dict[str, Any]] = []
    for it in itens_classificados:
        copia = dict(it)
        copia.pop("trecho_origem", None)
        base_limpa.append(copia)
    base_json_str = json.dumps(base_limpa, ensure_ascii=False)

    obs_json_str = json.dumps(plano_dict.get("observacoes", []), ensure_ascii=False)

    sql_substituir = """
    UPDATE caminho_escolhido
    SET status = 'substituido'
    WHERE usuario_id = :usuario_id AND status = 'ativo'
    """

    sql_caminho = """
    INSERT INTO caminho_escolhido (
        id, usuario_id, destino_id, comparacao_id, versao_catalogo, status, criado_em
    ) VALUES (
        :id, :usuario_id, :destino_id, :comparacao_id, :versao_catalogo, 'ativo', :criado_em
    )
    """

    sql_plano = """
    INSERT INTO plano (
        id, caminho_id, regra, base_json, observacoes_json, gerado_em
    ) VALUES (
        :id, :caminho_id, :regra, :base_json, :observacoes_json, :gerado_em
    )
    """

    sql_checkpoint = """
    INSERT INTO checkpoint (
        id, plano_id, ordem, tipo, titulo, descricao, criterio_conclusao,
        requisito_id_local, estado_origem, motivo_origem, obrigatorio,
        exercicio_id, status, atualizado_em
    ) VALUES (
        :id, :plano_id, :ordem, :tipo, :titulo, :descricao, :criterio_conclusao,
        :requisito_id_local, :estado_origem, :motivo_origem, :obrigatorio,
        :exercicio_id, :status, :atualizado_em
    )
    """

    checkpoints_retorno: list[dict[str, Any]] = []

    try:
        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                # 1. Substitui caminho ativo anterior
                cursor.execute(sql_substituir, {"usuario_id": usuario_id})

                # 2. Insere novo caminho_escolhido
                cursor.execute(
                    sql_caminho,
                    {
                        "id": caminho_id,
                        "usuario_id": usuario_id,
                        "destino_id": destino_id,
                        "comparacao_id": comparacao_id,
                        "versao_catalogo": versao_catalogo,
                        "criado_em": agora,
                    },
                )

                # 3. Insere plano
                cursor.execute(
                    sql_plano,
                    {
                        "id": plano_id,
                        "caminho_id": caminho_id,
                        "regra": plano_dict.get("regra", REGRA_PLANO_V1),
                        "base_json": base_json_str,
                        "observacoes_json": obs_json_str,
                        "gerado_em": agora,
                    },
                )

                # 4. Insere checkpoints
                for cp in plano_dict.get("checkpoints", []):
                    cp_id = uuid.uuid4().hex
                    obrigatorio_char = "S" if cp.get("obrigatorio") else "N"
                    cursor.execute(
                        sql_checkpoint,
                        {
                            "id": cp_id,
                            "plano_id": plano_id,
                            "ordem": cp["ordem"],
                            "tipo": cp["tipo"],
                            "titulo": cp["titulo"],
                            "descricao": cp.get("descricao"),
                            "criterio_conclusao": cp.get("criterio_conclusao"),
                            "requisito_id_local": cp.get("requisito_id_local"),
                            "estado_origem": cp.get("estado_origem"),
                            "motivo_origem": cp.get("motivo_origem"),
                            "obrigatorio": obrigatorio_char,
                            "exercicio_id": cp.get("exercicio_id"),
                            "status": "pendente",
                            "atualizado_em": agora,
                        },
                    )

                    cp_ret = dict(cp)
                    cp_ret["id"] = cp_id
                    cp_ret["status"] = "pendente"
                    cp_ret["atualizado_em"] = agora_iso
                    checkpoints_retorno.append(cp_ret)

            conexao.commit()
    except oracledb.Error as err:
        raise ErroBancoIndisponivel() from err

    return {
        "caminho_id": caminho_id,
        "destino_id": destino_id,
        "comparacao_id": comparacao_id,
        "criado_em": agora_iso,
        "plano": {
            "plano_id": plano_id,
            "gerado_em": agora_iso,
            "destino_id": destino_id,
            "nome": destino_nome,
            "versao_catalogo": versao_catalogo,
            "regra": plano_dict.get("regra", REGRA_PLANO_V1),
            "explicacao_regra": plano_dict.get("explicacao_regra", EXPLICACAO_REGRA_V1),
            "ja_demonstrados": plano_dict.get("ja_demonstrados", []),
            "checkpoints": checkpoints_retorno,
            "observacoes": plano_dict.get("observacoes", []),
            "aviso": plano_dict.get("aviso", AVISO_PLANO),
        },
    }


def buscar_caminho_ativo(
    usuario_id: str,
    catalogo_destinos: dict[str, Any],
) -> dict[str, Any] | None:
    """Busca o caminho ativo do usuario e monta o plano com status atual dos checkpoints."""
    import oracledb

    sql_caminho = """
    SELECT id, destino_id, comparacao_id, versao_catalogo, criado_em
    FROM caminho_escolhido
    WHERE usuario_id = :usuario_id AND status = 'ativo'
    """

    sql_plano = """
    SELECT id, regra, base_json, observacoes_json, gerado_em
    FROM plano
    WHERE caminho_id = :caminho_id
    """

    sql_checkpoints = """
    SELECT id, ordem, tipo, titulo, descricao, criterio_conclusao,
           requisito_id_local, estado_origem, motivo_origem, obrigatorio,
           exercicio_id, status, atualizado_em
    FROM checkpoint
    WHERE plano_id = :plano_id
    ORDER BY ordem ASC
    """

    try:
        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(sql_caminho, {"usuario_id": usuario_id})
                row_cam = cursor.fetchone()
                if not row_cam:
                    return None

                caminho_id = str(row_cam[0])
                destino_id = str(row_cam[1])
                comparacao_id = str(row_cam[2]) if row_cam[2] is not None else None
                versao_catalogo = str(row_cam[3]) if row_cam[3] is not None else ""
                criado_em = _formatar_iso_utc(row_cam[4])

                cursor.execute(sql_plano, {"caminho_id": caminho_id})
                row_plano = cursor.fetchone()
                if not row_plano:
                    return None

                plano_id = str(row_plano[0])
                regra = str(row_plano[1])
                base_dados = _deserializar_json(row_plano[2])
                observacoes = _deserializar_json(row_plano[3])
                if not isinstance(observacoes, list):
                    observacoes = []
                gerado_em = _formatar_iso_utc(row_plano[4])

                # Identifica ja_demonstrados a partir da base_json
                ja_demonstrados: list[str] = []
                if isinstance(base_dados, list):
                    for it in base_dados:
                        if isinstance(it, dict) and it.get("estado") == "demonstrada":
                            ja_demonstrados.append(str(it.get("id_local")))

                # Busca checkpoints
                cursor.execute(sql_checkpoints, {"plano_id": plano_id})
                checkpoints: list[dict[str, Any]] = []
                for row_cp in cursor.fetchall():
                    checkpoints.append(
                        {
                            "id": str(row_cp[0]),
                            "ordem": int(row_cp[1]),
                            "tipo": str(row_cp[2]),
                            "titulo": str(row_cp[3]),
                            "descricao": str(row_cp[4]) if row_cp[4] is not None else None,
                            "criterio_conclusao": str(row_cp[5]) if row_cp[5] is not None else None,
                            "requisito_id_local": str(row_cp[6]) if row_cp[6] is not None else None,
                            "estado_origem": str(row_cp[7]) if row_cp[7] is not None else None,
                            "motivo_origem": str(row_cp[8]) if row_cp[8] is not None else None,
                            "obrigatorio": row_cp[9] == "S",
                            "exercicio_id": str(row_cp[10]) if row_cp[10] is not None else None,
                            "status": str(row_cp[11]),
                            "atualizado_em": _formatar_iso_utc(row_cp[12]),
                        }
                    )

                destino_info = catalogo_destinos.get(destino_id, {})
                destino_nome = destino_info.get("nome", destino_id)

                return {
                    "caminho_id": caminho_id,
                    "destino_id": destino_id,
                    "comparacao_id": comparacao_id,
                    "criado_em": criado_em,
                    "plano": {
                        "plano_id": plano_id,
                        "gerado_em": gerado_em,
                        "destino_id": destino_id,
                        "nome": destino_nome,
                        "versao_catalogo": versao_catalogo,
                        "regra": regra,
                        "explicacao_regra": EXPLICACAO_REGRA_V1,
                        "ja_demonstrados": ja_demonstrados,
                        "checkpoints": checkpoints,
                        "observacoes": observacoes,
                        "aviso": AVISO_PLANO,
                    },
                }
    except oracledb.Error as err:
        raise ErroBancoIndisponivel() from err


def obter_checkpoint_para_atualizacao(
    checkpoint_id: str,
    usuario_id: str,
) -> dict[str, Any] | None:
    """Verifica existencia e pertencimento do checkpoint a plano ativo do usuario."""
    import oracledb

    sql = """
    SELECT cp.id, cp.tipo, cp.status, c.usuario_id, c.status
    FROM checkpoint cp
    JOIN plano p ON cp.plano_id = p.id
    JOIN caminho_escolhido c ON p.caminho_id = c.id
    WHERE cp.id = :checkpoint_id
    """

    try:
        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(sql, {"checkpoint_id": checkpoint_id})
                row = cursor.fetchone()
                if not row:
                    return None

                dono_id = str(row[3])
                caminho_status = str(row[4])

                if dono_id != usuario_id or caminho_status != "ativo":
                    return None

                return {
                    "id": str(row[0]),
                    "tipo": str(row[1]),
                    "status": str(row[2]),
                }
    except oracledb.Error as err:
        raise ErroBancoIndisponivel() from err


def atualizar_status_checkpoint(checkpoint_id: str, novo_status: str) -> dict[str, Any]:
    """Atualiza o status de um checkpoint e retorna o registro completo atualizado."""
    import oracledb

    agora = datetime.now(UTC)
    agora_iso = _formatar_iso_utc(agora)

    sql_update = """
    UPDATE checkpoint
    SET status = :status, atualizado_em = :atualizado_em
    WHERE id = :id
    """

    sql_select = """
    SELECT id, ordem, tipo, titulo, descricao, criterio_conclusao,
           requisito_id_local, estado_origem, motivo_origem, obrigatorio,
           exercicio_id, status, atualizado_em
    FROM checkpoint
    WHERE id = :id
    """

    try:
        with obter_conexao() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(
                    sql_update,
                    {"status": novo_status, "atualizado_em": agora, "id": checkpoint_id},
                )
                cursor.execute(sql_select, {"id": checkpoint_id})
                row = cursor.fetchone()
                if not row:
                    raise ErroBancoIndisponivel()
            conexao.commit()

            return {
                "id": str(row[0]),
                "ordem": int(row[1]),
                "tipo": str(row[2]),
                "titulo": str(row[3]),
                "descricao": str(row[4]) if row[4] is not None else None,
                "criterio_conclusao": str(row[5]) if row[5] is not None else None,
                "requisito_id_local": str(row[6]) if row[6] is not None else None,
                "estado_origem": str(row[7]) if row[7] is not None else None,
                "motivo_origem": str(row[8]) if row[8] is not None else None,
                "obrigatorio": row[9] == "S",
                "exercicio_id": str(row[10]) if row[10] is not None else None,
                "status": str(row[11]),
                "atualizado_em": agora_iso,
            }
    except oracledb.Error as err:
        raise ErroBancoIndisponivel() from err
