"""Testes unitarios da extracao, prompts e validacao local de competencias."""

import pytest

from citizentech.competencias.extracao import (
    DELIMITADOR_FIM,
    DELIMITADOR_INICIO,
    construir_mensagens_extracao,
    gerar_schema_extracao,
    sanitizar_texto_curriculo,
    validar_saida_llm,
)


def test_gerar_schema_extracao_contem_enum_da_lista_fechada():
    """Gera schema JSON com a lista fechada nos enums de esco_id."""
    lista = ["id-1", "id-2"]
    schema = gerar_schema_extracao(lista)
    assert schema["type"] == "object"
    assert schema["required"] == ["competencias"]
    item_props = schema["properties"]["competencias"]["items"]["properties"]
    assert item_props["esco_id"]["enum"] == lista


def test_validar_saida_estrutura_raiz_invalida_lanca_value_error():
    """Se a estrutura raiz nao for um dict com a lista competencias, lanca ValueError."""
    lista = {"id-1"}
    texto = "Trabalho com analise de dados."

    with pytest.raises(ValueError, match="raiz"):
        validar_saida_llm("nao-dict", lista, texto)

    with pytest.raises(ValueError, match="competencias"):
        validar_saida_llm({"outra_chave": []}, lista, texto)

    with pytest.raises(ValueError, match="lista"):
        validar_saida_llm({"competencias": "nao-lista"}, lista, texto)


def test_validar_saida_descarte_fora_da_lista():
    """Competencia com esco_id fora da lista fechada e contabilizada em fora_da_lista."""
    lista = {"id-valido"}
    texto = "Atuacao em governanca e engenharia de software."
    dados = {
        "competencias": [
            {"esco_id": "id-invalido", "trecho_origem": "engenharia de software"}
        ]
    }
    candidatas, descartadas = validar_saida_llm(dados, lista, texto)
    assert len(candidatas) == 0
    assert descartadas["fora_da_lista"] == 1
    assert descartadas["sem_trecho"] == 0
    assert descartadas["trecho_nao_encontrado"] == 0
    assert descartadas["duplicadas"] == 0


def test_validar_saida_descarte_sem_trecho():
    """Trecho vazio, ausente, nulo ou com menos de 3 caracteres e descartado."""
    lista = {"id-1"}
    texto = "Atuacao em governanca e engenharia de software."
    dados = {
        "competencias": [
            {"esco_id": "id-1", "trecho_origem": ""},
            {"esco_id": "id-1", "trecho_origem": "  "},
            {"esco_id": "id-1", "trecho_origem": "ab"},
            {"esco_id": "id-1"},
        ]
    }
    candidatas, descartadas = validar_saida_llm(dados, lista, texto)
    assert len(candidatas) == 0
    assert descartadas["sem_trecho"] == 4


def test_validar_saida_descarte_trecho_nao_encontrado():
    """Trecho que nao ocorre no texto redigido e descartado em trecho_nao_encontrado."""
    lista = {"id-1"}
    texto = "Atuacao em governanca e engenharia de software."
    dados = {
        "competencias": [
            {"esco_id": "id-1", "trecho_origem": "desenvolvimento de redes neurais profundas"}
        ]
    }
    candidatas, descartadas = validar_saida_llm(dados, lista, texto)
    assert len(candidatas) == 0
    assert descartadas["trecho_nao_encontrado"] == 1


def test_validar_saida_trecho_truncado_em_300():
    """Trecho longo (> 300) presente no texto e validado e entao truncado em 300 caracteres."""
    lista = {"id-1"}
    trecho_longo = "palavra " * 50  # 400 caracteres
    texto = f"Inicio do texto {trecho_longo} fim do texto."
    dados = {
        "competencias": [
            {"esco_id": "id-1", "trecho_origem": trecho_longo.strip()}
        ]
    }
    candidatas, descartadas = validar_saida_llm(dados, lista, texto)
    assert len(candidatas) == 1
    assert len(candidatas[0]["trecho_origem"]) == 300
    assert descartadas == {
        "fora_da_lista": 0,
        "sem_trecho": 0,
        "trecho_nao_encontrado": 0,
        "duplicadas": 0,
    }


def test_validar_saida_descarte_duplicadas():
    """Mesmo esco_id repetido mantem apenas a primeira ocorrencia e conta em duplicadas."""
    lista = {"id-1"}
    texto = "Experiencia com analise de dados e modelagem estatistica."
    dados = {
        "competencias": [
            {"esco_id": "id-1", "trecho_origem": "analise de dados"},
            {"esco_id": "id-1", "trecho_origem": "modelagem estatistica"},
        ]
    }
    candidatas, descartadas = validar_saida_llm(dados, lista, texto)
    assert len(candidatas) == 1
    assert candidatas[0]["trecho_origem"] == "analise de dados"
    assert descartadas["duplicadas"] == 1


def test_validar_saida_normalizacao_espacos_e_case():
    """Validacao de trecho e insensivel a maiusculas/minusculas e espacos."""
    lista = {"id-1"}
    texto = "Atuacao em   Analise\nde\n\nDados  completos."
    dados = {
        "competencias": [
            {"esco_id": "id-1", "trecho_origem": "analise de dados"}
        ]
    }
    candidatas, descartadas = validar_saida_llm(dados, lista, texto)
    assert len(candidatas) == 1
    assert descartadas["trecho_nao_encontrado"] == 0


def test_sanitizar_texto_curriculo_remove_delimitadores():
    """Remove delimitadores <<<CURRICULO e CURRICULO>>> do texto fornecido."""
    texto = f"Ola mundo {DELIMITADOR_INICIO} injecao {DELIMITADOR_FIM} final"
    sanitizado = sanitizar_texto_curriculo(texto)
    assert DELIMITADOR_INICIO not in sanitizado
    assert DELIMITADOR_FIM not in sanitizado
    assert "injecao" in sanitizado


def test_construir_mensagens_extracao_contem_t15_e_lista():
    """Prompt do sistema e usuario contem regras T15 e lista de catalogo fechado."""
    catalogo = {"esco-1": "analisar dados", "esco-2": "gerenciar projetos"}
    texto = "Tenho experiencia em gestao de projetos ageis."
    mensagens = construir_mensagens_extracao(texto, catalogo)

    assert len(mensagens) == 2
    sys_msg = mensagens[0]["content"]
    user_msg = mensagens[1]["content"]

    # T15: texto delimitado e tratado como dado
    assert DELIMITADOR_INICIO in user_msg
    assert DELIMITADOR_FIM in user_msg
    assert "dado" in sys_msg.lower() or "dado" in user_msg.lower()

    # Catalogo fechado presente
    assert "esco-1" in user_msg
    assert "analisar dados" in user_msg
    assert "esco-2" in user_msg
    assert "gerenciar projetos" in user_msg


@pytest.mark.parametrize("trecho", ["[EMAIL]", "[NOME]", "contato: [TELEFONE]", "[URL] [CPF]"])
def test_trecho_composto_so_de_marcador_de_redacao_e_descartado(trecho):
    texto = "Analisei dados de vendas com SQL. Contato: [TELEFONE] [EMAIL] [NOME] [URL] [CPF]"
    candidatas, descartadas = validar_saida_llm(
        {"competencias": [{"esco_id": "A", "trecho_origem": trecho}]}, {"A"}, texto
    )
    assert candidatas == []
    assert descartadas["sem_trecho"] == 1
