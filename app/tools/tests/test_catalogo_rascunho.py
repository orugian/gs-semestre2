"""Testes de validação dos rascunhos de destinos do catálogo (Contrato D2).

Garante que os 6 destinos em formato YAML seguem fielmente as decisões D02, D05, D06,
D07, D21, D23 e R29, respeitando o catálogo de ocupações CBO aprovado e os 29 conceitos
da fonte oficial ESCO consultados em 13/11/2026.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

import pytest
import yaml

APP_DIR = Path(__file__).resolve().parents[2]
CATALOGO_DIR = APP_DIR / "catalogo"
DESTINOS_DIR = CATALOGO_DIR / "destinos"
FONTES_DIR = CATALOGO_DIR / "fontes"
CONFIG_DIR = APP_DIR / "config"

DESTINOS_ESPERADOS = [
    "analista_dados_bi",
    "analista_monitoramento_iot",
    "analista_processos",
    "gerente_projetos_produto",
    "analista_suporte_infra",
    "desenvolvedor_sistemas",
]


@pytest.fixture(scope="module")
def ocupacoes_cbo() -> dict[str, Any]:
    cbo_path = CATALOGO_DIR / "ocupacoes_cbo.json"
    with open(cbo_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def fonte_esco() -> list[dict[str, Any]]:
    esco_path = FONTES_DIR / "esco_20261113.json"
    with open(esco_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def esco_por_uri(fonte_esco: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["uri"]: item for item in fonte_esco}


@pytest.fixture(scope="module")
def destinos_carregados() -> dict[str, dict[str, Any]]:
    """Carrega os 6 arquivos de destinos garantindo falha por AssertionError se ausentes."""
    faltantes = [
        did for did in DESTINOS_ESPERADOS if not (DESTINOS_DIR / f"{did}.yaml").is_file()
    ]
    assert not faltantes, f"Arquivos de destino ausentes no catálogo: {faltantes}"

    resultado = {}
    for did in DESTINOS_ESPERADOS:
        yaml_path = DESTINOS_DIR / f"{did}.yaml"
        with open(yaml_path, encoding="utf-8") as f:
            conteudo = yaml.safe_load(f)
            assert isinstance(conteudo, dict), f"{did}.yaml não é um dicionário YAML válido"
            resultado[did] = conteudo
    return resultado


def test_conjunto_exato_seis_arquivos_destinos_existem():
    """Garante que existem exatamente os 6 arquivos de destinos esperados (RED prioritário)."""
    arquivos_existentes = [
        DESTINOS_DIR / f"{did}.yaml"
        for did in DESTINOS_ESPERADOS
        if (DESTINOS_DIR / f"{did}.yaml").is_file()
    ]
    assert len(arquivos_existentes) == 6, (
        f"Esperado exatamente 6 arquivos de destinos, encontrados {len(arquivos_existentes)}: "
        f"{[p.name for p in arquivos_existentes]}"
    )
    if DESTINOS_DIR.exists():
        todos_yamls = list(DESTINOS_DIR.glob("*.yaml"))
        assert len(todos_yamls) == 6, (
            f"Diretório de destinos contém arquivos extras não previstos: "
            f"{[p.name for p in todos_yamls if p.stem not in DESTINOS_ESPERADOS]}"
        )


def test_metadados_e_cbo_iguais_ao_catalogo(
    destinos_carregados: dict[str, dict[str, Any]], ocupacoes_cbo: dict[str, Any]
):
    """Verifica correspondência estrita com app/catalogo/ocupacoes_cbo.json."""
    cbo_destinos = ocupacoes_cbo["destinos"]
    assert set(destinos_carregados.keys()) == set(cbo_destinos.keys())

    for did, data in destinos_carregados.items():
        assert data.get("schema_version") == "1.0"
        assert data.get("destino_id") == did
        assert data.get("nome") == cbo_destinos[did]["nome"]
        assert data.get("cbo6") == cbo_destinos[did]["cbo6"]
        assert data.get("status") == "rascunho"
        assert data.get("curadoria_natureza") == "inferida_pendente_revisao"


def test_nenhuma_cbo_repetida_entre_destinos_e_reserva(
    destinos_carregados: dict[str, dict[str, Any]], ocupacoes_cbo: dict[str, Any]
):
    """Garante que não há sobreposição de CBOs entre destinos nem com a reserva."""
    cbo_reserva = set(ocupacoes_cbo.get("cbo6_reserva", []))
    cbos_vistas: dict[str, str] = {}

    for did, data in destinos_carregados.items():
        cbos = data.get("cbo6", [])
        assert len(cbos) > 0, f"Destino {did} possui lista cbo6 vazia"
        assert len(cbos) == len(set(cbos)), f"Destino {did} possui códigos cbo duplicados"

        for cbo in cbos:
            assert cbo not in cbo_reserva, (
                f"CBO {cbo} do destino {did} colide com a reserva do catálogo"
            )
            assert cbo not in cbos_vistas, (
                f"CBO {cbo} está presente em mais de um destino: {cbos_vistas[cbo]} e {did}"
            )
            cbos_vistas[cbo] = did


def test_oito_requisitos_esco_coincidem_com_fonte(
    destinos_carregados: dict[str, dict[str, Any]],
    esco_por_uri: dict[str, dict[str, Any]],
):
    """Garante que cada destino possui exatamente 8 requisitos derivados da fonte ESCO oficial."""
    for did, data in destinos_carregados.items():
        requisitos = data.get("requisitos", [])
        assert len(requisitos) == 8, (
            f"Destino {did} deve conter exatamente 8 requisitos, encontrou {len(requisitos)}"
        )

        ids_locais = set()
        uris_vistas = set()

        for req in requisitos:
            id_local = req.get("id_local")
            assert id_local and id_local.islower() and " " not in id_local, (
                f"id_local inválido em {did}: {id_local}"
            )
            assert id_local not in ids_locais, f"id_local duplicado em {did}: {id_local}"
            ids_locais.add(id_local)

            esco_uri = req.get("esco_uri")
            assert esco_uri in esco_por_uri, f"URI ESCO desconhecida em {did}: {esco_uri}"
            assert esco_uri not in uris_vistas, f"URI ESCO duplicada em {did}: {esco_uri}"
            uris_vistas.add(esco_uri)

            esco_item = esco_por_uri[esco_uri]
            assert req.get("titulo_oficial") == esco_item["titulo"]
            assert req.get("esco_id") == esco_item["id"]

            tipo_esco_esperado = esco_item["tipo"][0]["title"]
            assert req.get("tipo_esco") == tipo_esco_esperado, (
                f"Tipo ESCO divergente em {did} ({id_local}): "
                f"esperado '{tipo_esco_esperado}', obtido '{req.get('tipo_esco')}'"
            )

            assert isinstance(req.get("obrigatorio_proposto"), bool)
            assert bool(req.get("descricao_contextual_proposta"))
            assert bool(req.get("evidencia_esperada"))


def test_conhecimento_nao_marcado_como_habilidade_pratica(
    destinos_carregados: dict[str, dict[str, Any]],
    esco_por_uri: dict[str, dict[str, Any]],
):
    """Garante que conceitos do tipo 'conhecimento' são tratados como tal, não habilidade."""
    for did, data in destinos_carregados.items():
        for req in data.get("requisitos", []):
            esco_uri = req["esco_uri"]
            item_fonte = esco_por_uri[esco_uri]
            tipo_oficial = item_fonte["tipo"][0]["title"]

            if tipo_oficial == "conhecimento":
                assert req.get("tipo_esco") == "conhecimento"
                evidencia = req.get("evidencia_esperada", "").lower()
                assert not any(
                    termo in evidencia
                    for termo in ["certificação profissional", "certificacao profissional"]
                ), f"Evidência de conhecimento em {did} promete certificação profissional"


def test_questoes_objetivas_gabaritos_e_requisitos(
    destinos_carregados: dict[str, dict[str, Any]],
):
    """Valida que cada destino tem 3–5 questões objetivas com alternativas e gabarito válido."""
    for did, data in destinos_carregados.items():
        exercicio = data.get("exercicio", {})
        assert exercicio.get("id")
        assert exercicio.get("cenario")

        reqs_validos = {r["id_local"] for r in data.get("requisitos", [])}
        questoes = exercicio.get("questoes_objetivas", [])
        assert 3 <= len(questoes) <= 5, (
            f"Destino {did} deve ter entre 3 e 5 objetivas, tem {len(questoes)}"
        )

        q_ids = set()
        for q in questoes:
            qid = q.get("id")
            assert qid and qid not in q_ids, f"ID de questão repetido ou nulo em {did}: {qid}"
            q_ids.add(qid)

            assert bool(q.get("enunciado")), f"Enunciado ausente na questão {qid} de {did}"
            alternativas = q.get("alternativas")
            assert isinstance(alternativas, dict) and set(alternativas.keys()) == {
                "A",
                "B",
                "C",
                "D",
            }, f"Alternativas da questão {qid} em {did} devem ser dicionário com chaves A, B, C, D"

            gabarito = q.get("gabarito")
            assert gabarito in {"A", "B", "C", "D"}, (
                f"Gabarito inválido ({gabarito}) na questão {qid} de {did}"
            )
            assert bool(q.get("justificativa")), f"Justificativa ausente em {qid} de {did}"

            reqs_avaliados = q.get("requisitos_avaliados", [])
            assert len(reqs_avaliados) > 0, f"Questão {qid} de {did} sem requisitos_avaliados"
            for r_id in reqs_avaliados:
                assert r_id in reqs_validos, (
                    f"Requisito avaliado {r_id} na questão {qid} não consta nos requisitos de {did}"
                )


def test_questao_aberta_rubrica_ancoras_e_sem_sentimento(
    destinos_carregados: dict[str, dict[str, Any]],
):
    """Valida 1 questão aberta com 3–4 critérios na rubrica (âncoras 0, 1, 2) e sem sentimento."""
    palavras_vedadas_sentimento = ["humor", "simpatia", "sentimento", "personalidade"]

    for did, data in destinos_carregados.items():
        exercicio = data.get("exercicio", {})
        reqs_validos = {r["id_local"] for r in data.get("requisitos", [])}

        aberta = exercicio.get("questao_aberta")
        assert isinstance(aberta, dict), f"Destino {did} deve conter exatamente 1 questao_aberta"
        assert bool(aberta.get("enunciado")), f"Enunciado da questão aberta ausente em {did}"

        rubrica = aberta.get("rubrica", [])
        assert 3 <= len(rubrica) <= 4, (
            f"Destino {did} deve ter 3 a 4 critérios de rubrica, tem {len(rubrica)}"
        )

        crit_ids = set()
        for crit in rubrica:
            cid = crit.get("id")
            assert cid and cid not in crit_ids, f"ID de critério duplicado em {did}: {cid}"
            crit_ids.add(cid)

            desc = crit.get("descricao", "")
            assert bool(desc), f"Critério {cid} de {did} sem descrição"

            for palavra in palavras_vedadas_sentimento:
                assert palavra not in desc.lower(), (
                    f"Critério {cid} de {did} contém menção vedada a sentimento/personalidade (D23)"
                )

            ancoras = crit.get("ancoras", {})
            assert isinstance(ancoras, dict)
            assert 0 in ancoras and 1 in ancoras and 2 in ancoras, (
                f"Critério {cid} de {did} deve conter âncoras para notas 0, 1 e 2"
            )

            reqs_crit = crit.get("requisitos_avaliados", [])
            assert len(reqs_crit) > 0, f"Critério {cid} de {did} sem requisitos_avaliados"
            for r_id in reqs_crit:
                assert r_id in reqs_validos, (
                    f"Requisito {r_id} no critério {cid} não existe em {did}"
                )


def test_politica_avaliacao_proposta_e_pendencia_humana(
    destinos_carregados: dict[str, dict[str, Any]],
):
    """Garante pesos 50/50, mínimos nulos para decisão humana e conformidade D21/D23."""
    for did, data in destinos_carregados.items():
        pol = data.get("politica_avaliacao_proposta", {})
        pesos = pol.get("pesos", {})

        p_obj = pesos.get("objetiva")
        p_llm = pesos.get("llm")
        assert math.isclose(p_obj, 0.5), f"Peso da objetiva deve ser 0.5 em {did}"
        assert math.isclose(p_llm, 0.5), f"Peso da LLM deve ser 0.5 em {did}"
        assert math.isfinite(p_obj) and math.isfinite(p_llm)

        # R29: mínimos de aprovação são nulos no rascunho (pendência da decisão humana em D3)
        assert pol.get("minimo_objetiva") is None, (
            f"minimo_objetiva deve ser nulo no rascunho {did}"
        )
        assert pol.get("minimo_llm") is None, f"minimo_llm deve ser nulo no rascunho {did}"

        # D21: no máximo 3 tentativas a cada 24 horas
        tentativas = pol.get("politica_tentativas", {})
        assert tentativas.get("max_tentativas_24h") == 3

        # Revisão humana explicitamente pendente
        rev = data.get("revisao_humana", {})
        assert rev.get("status") == "pendente"
        assert rev.get("revisor") is None
        assert rev.get("revisado_em") is None
        assert "15/11/2026 às 18h (America/Sao_Paulo)" in rev.get("observacoes", "")

        # Checklist de revisão presente e pendente
        chk = data.get("checklist_revisao", {})
        assert isinstance(chk, dict) and len(chk) >= 5
        for item_nome, item_status in chk.items():
            assert item_status == "pendente", (
                f"Checklist {item_nome} em {did} não pode ser aprovado previamente"
            )


def test_iot_cenario_alinhado_com_limiares_versionados(
    destinos_carregados: dict[str, dict[str, Any]],
):
    """Garante que o destino IoT utiliza exatamente os limiares de app/config/limiares.json."""
    limiares_path = CONFIG_DIR / "limiares.json"
    with open(limiares_path, encoding="utf-8") as f:
        limiares = json.load(f)

    temp_atencao = limiares["metricas"]["temperatura_c"]["atencao"]
    temp_critico = limiares["metricas"]["temperatura_c"]["critico"]
    dist_atencao = limiares["metricas"]["distancia_cm"]["atencao"]
    dist_critico = limiares["metricas"]["distancia_cm"]["critico"]

    iot = destinos_carregados["analista_monitoramento_iot"]
    cenario_txt = iot["exercicio"]["cenario"]

    assert str(temp_atencao) in cenario_txt or f"{int(temp_atencao)}" in cenario_txt
    assert str(temp_critico) in cenario_txt or f"{int(temp_critico)}" in cenario_txt
    assert str(dist_atencao) in cenario_txt or f"{int(dist_atencao)}" in cenario_txt
    assert str(dist_critico) in cenario_txt or f"{int(dist_critico)}" in cenario_txt


def test_readme_catalogo_existe():
    """Garante que app/catalogo/README.md existe e aborda o processo de revisão humana D3."""
    readme_path = CATALOGO_DIR / "README.md"
    assert readme_path.is_file(), "app/catalogo/README.md não encontrado"
    conteudo = readme_path.read_text(encoding="utf-8")
    assert len(conteudo) > 100
    assert "D3" in conteudo
    assert "revisão" in conteudo.lower()
    assert "rascunho" in conteudo.lower()
    assert "banca/grupo" not in conteudo, "README não deve conter menção a 'banca/grupo'"
    assert "o carregador do catálogo deve recusar" in conteudo, (
        "README deve especificar 'o carregador do catálogo deve recusar' como requisito futuro"
    )


def test_diversidade_gabaritos_por_destino(
    destinos_carregados: dict[str, dict[str, Any]],
):
    """Garante pelo menos 3 letras distintas por destino quando há 4 ou mais questões."""
    for did, data in destinos_carregados.items():
        questoes = data.get("exercicio", {}).get("questoes_objetivas", [])
        if len(questoes) >= 4:
            gabaritos = {q.get("gabarito") for q in questoes}
            assert len(gabaritos) >= 3, (
                f"Destino {did} com pouca diversidade ({gabaritos}): esperado >= 3 letras"
            )


def test_distribuicao_global_letras_gabarito(
    destinos_carregados: dict[str, dict[str, Any]],
):
    """Garante que nos 6 destinos cada letra A, B, C, D é gabarito pelo menos 3 vezes."""
    contagem: dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0}
    for data in destinos_carregados.values():
        for q in data.get("exercicio", {}).get("questoes_objetivas", []):
            gab = q.get("gabarito")
            if gab in contagem:
                contagem[gab] += 1
    for letra, qtd in contagem.items():
        assert qtd >= 3, (
            f"Letra {letra} aparece apenas {qtd} vezes como gabarito (mínimo esperado: 3)"
        )


def test_tamanho_e_distincao_alternativas(
    destinos_carregados: dict[str, dict[str, Any]],
):
    """Garante len(correta) <= 1.3 * max(len outras) e alternativas com textos distintos."""
    for did, data in destinos_carregados.items():
        questoes = data.get("exercicio", {}).get("questoes_objetivas", [])
        for q in questoes:
            qid = q.get("id")
            alternativas = q.get("alternativas", {})
            textos = list(alternativas.values())
            assert len(textos) == 4, f"Questão {qid} de {did} não possui 4 alternativas"
            assert len(set(textos)) == 4, (
                f"Questão {qid} de {did} possui alternativas com textos duplicados"
            )

            gabarito = q.get("gabarito")
            correta = alternativas.get(gabarito, "")
            outras = [texto for k, texto in alternativas.items() if k != gabarito]
            max_outras = max(len(t) for t in outras)
            limite = 1.3 * max_outras
            assert len(correta) <= limite, (
                f"Questão {qid} de {did}: tamanho da correta ({len(correta)}) "
                f"excede 1.3 * max(outras) ({limite:.1f}, max_outras={max_outras})"
            )


def test_requisitos_nao_avaliados(
    destinos_carregados: dict[str, dict[str, Any]],
):
    """Garante que requisitos_nao_avaliados bate com o calculado e não inclui obrigatórios."""
    for did, data in destinos_carregados.items():
        exercicio = data.get("exercicio", {})
        assert "requisitos_nao_avaliados" in exercicio, (
            f"Chave 'requisitos_nao_avaliados' não encontrada em exercicio de {did}"
        )
        declarados = exercicio.get("requisitos_nao_avaliados")
        assert isinstance(declarados, list), (
            f"'requisitos_nao_avaliados' em {did} deve ser uma lista"
        )

        todos_reqs = {r["id_local"] for r in data.get("requisitos", [])}
        reqs_obrigatorios = {
            r["id_local"]
            for r in data.get("requisitos", [])
            if r.get("obrigatorio_proposto") is True
        }

        avaliados_questoes = {
            r_id
            for q in exercicio.get("questoes_objetivas", [])
            for r_id in q.get("requisitos_avaliados", [])
        }
        avaliados_rubrica = {
            r_id
            for crit in exercicio.get("questao_aberta", {}).get("rubrica", [])
            for r_id in crit.get("requisitos_avaliados", [])
        }
        avaliados_total = avaliados_questoes | avaliados_rubrica
        calculado_nao_avaliados = todos_reqs - avaliados_total

        assert set(declarados) == calculado_nao_avaliados, (
            f"Divergência em 'requisitos_nao_avaliados' de {did}: "
            f"declarado {set(declarados)} vs calculado {calculado_nao_avaliados}"
        )

        for req_id in declarados:
            assert req_id not in reqs_obrigatorios, (
                f"Requisito obrigatório '{req_id}' consta como não avaliado em {did}"
            )


def test_nenhuma_justificativa_contem_referencia_a_letra(
    destinos_carregados: dict[str, dict[str, Any]],
):
    """Garante que nenhuma justificativa contém referência explícita a letra de alternativa."""
    padrao = re.compile(r"\b(?:alternativa|opção|opcao|letra)\s+[A-Da-d]\b", re.IGNORECASE)
    for did, data in destinos_carregados.items():
        questoes = data.get("exercicio", {}).get("questoes_objetivas", [])
        for q in questoes:
            qid = q.get("id")
            justificativa = q.get("justificativa", "")
            matches = padrao.findall(justificativa)
            assert not matches, (
                f"Justificativa da questão {qid} em {did} contém referência a letra: {matches}"
            )

