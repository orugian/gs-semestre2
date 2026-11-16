"""Testes unitarios da funcao pura de redacao de PII (redacao.py)."""


from citizentech.curriculo.redacao import redigir_pii


def test_texto_sem_pii_permanece_identico():
    texto = (
        "Desenvolvedor de software com sólida experiência em arquitetura de microsserviços.\n"
        "Competências: Python, FastAPI, Docker, SQL, Git, Linux.\n"
        "Participou de migração de monólito para arquitetura orientada a eventos."
    )
    resultado, contagens = redigir_pii(texto)
    assert resultado == texto
    for categoria, qtd in contagens.items():
        assert qtd == 0, f"Categoria {categoria} deveria ser 0"


def test_redacao_email():
    texto = "Contato pelo e-mail joao.silva_dev@empresa.com.br ou joao@teste.org."
    resultado, contagens = redigir_pii(texto)
    assert "[EMAIL]" in resultado
    assert "joao.silva_dev@empresa.com.br" not in resultado
    assert "joao@teste.org" not in resultado
    assert contagens["email"] == 2


def test_redacao_telefone_formatos_diversos():
    casos = [
        "(11) 98765-4321",
        "+55 (11) 98765-4321",
        "+55 11 98765-4321",
        "11 98765-4321",
        "(11) 987654321",
        "(11) 3456-7890",
        "11 3456-7890",
        "(21) 2233-4455",
        "Telefone: 98765-4321",
        "Celular: 91234-5678",
    ]
    for telefone in casos:
        texto = f"Meu contato e {telefone} para ligacoes."
        resultado, contagens = redigir_pii(texto)
        assert "[TELEFONE]" in resultado, f"Falhou para telefone: {telefone}"
        assert contagens["telefone"] >= 1, f"Contagem zero para: {telefone}"


def test_redacao_cpf_formatado_e_11_digitos():
    texto_formatado = "Meu CPF e 123.456.789-00 registrado."
    resultado, contagens = redigir_pii(texto_formatado)
    assert "[CPF]" in resultado
    assert "123.456.789-00" not in resultado
    assert contagens["cpf"] == 1

    texto_digitos = "Documento: 98765432100 para conferencia."
    resultado2, contagens2 = redigir_pii(texto_digitos)
    assert "[CPF]" in resultado2
    assert "98765432100" not in resultado2
    assert contagens2["cpf"] == 1


def test_redacao_cep():
    texto = "Residente no CEP 01310-100 ou CEP 01310100."
    resultado, contagens = redigir_pii(texto)
    assert "[CEP]" in resultado
    assert "01310-100" not in resultado
    assert "01310100" not in resultado
    assert contagens["cep"] == 2


def test_redacao_endereco():
    casos = [
        "Moro na Rua das Flores, 123.",
        "Trabalho na R. Augusta, 1000, Consolação.",
        "Escritorio na Avenida Paulista, 1578.",
        "Localizado na Av. Brigadeiro Faria Lima, 3000, Itaim Bibi.",
        "Residencia na Alameda Santos, 50.",
        "Próximo à Praça da Sé, 1.",
        "Rodovia dos Imigrantes, km 20.",
        "Estrada do Campo Limpo, 500.",
    ]
    for endereco in casos:
        resultado, contagens = redigir_pii(endereco)
        assert "[ENDERECO]" in resultado, f"Falhou para endereco: {endereco}"
        assert contagens["endereco"] >= 1, f"Contagem zero para: {endereco}"


def test_redacao_urls_e_perfis():
    texto = (
        "Veja meu portfolio em https://meusite.com.br/projetos e no www.github.com/usuario.\n"
        "Perfis: linkedin.com/in/usuario-dev e github.com/usuario-dev."
    )
    resultado, contagens = redigir_pii(texto)
    assert "[URL]" in resultado
    assert "https://meusite.com.br" not in resultado
    assert "linkedin.com/in/usuario-dev" not in resultado
    assert "github.com/usuario-dev" not in resultado
    assert contagens["url"] == 4


def test_redacao_nome_cabecalho_primeiras_3_linhas():
    texto = (
        "Carlos Alberto da Silva\n"
        "Engenheiro de Software Sênior\n"
        "São Paulo - SP\n"
        "Experiência com desenvolvimento backend desde 2018."
    )
    resultado, contagens = redigir_pii(texto)
    linhas = resultado.splitlines()
    assert linhas[0] == "[NOME]"
    assert "Carlos Alberto da Silva" not in resultado
    assert "Engenheiro de Software Sênior" in resultado
    assert contagens["nome"] == 1


def test_redacao_nome_com_rotulo_em_qualquer_posicao():
    texto = (
        "Resumo de Qualificações\n"
        "Nome: Maria das Dores Souza\n"
        "Atuação na área de dados."
    )
    resultado, contagens = redigir_pii(texto)
    assert "[NOME]" in resultado
    assert "Maria das Dores Souza" not in resultado
    assert contagens["nome"] == 1


def test_nao_destroi_conteudo_profissional():
    texto = (
        "Atuação como desenvolvedor pleno no período de 2019–2023.\n"
        "Início em 03/2020 e término em 11/2022.\n"
        "Ano de formação: 2018.\n"
        "Aumento de 99.9% no throughput e redução de 40% na latência.\n"
        "Orçamento gerenciado de R$ 150.000,00 anuais.\n"
        "Tecnologias: REST API, SQL, AWS, CI/CD, JWT."
    )
    resultado, contagens = redigir_pii(texto)

    # Datas, anos e intervalos preservados
    assert "2019–2023" in resultado
    assert "03/2020" in resultado
    assert "11/2022" in resultado
    assert "2018" in resultado

    # Percentuais, valores e siglas preservados
    assert "99.9%" in resultado
    assert "40%" in resultado
    assert "R$ 150.000,00" in resultado
    assert "REST API, SQL, AWS, CI/CD, JWT" in resultado

    # Nenhuma redacao indevida
    assert contagens["telefone"] == 0
    assert contagens["cpf"] == 0
    assert contagens["nome"] == 0


def test_ano_isolado_e_intervalo_anos_nao_sao_telefone_nem_cpf():
    texto = "Projetos realizados entre 2019-2023 e no ano 2024."
    resultado, contagens = redigir_pii(texto)
    assert "2019-2023" in resultado
    assert "2024" in resultado
    assert contagens["telefone"] == 0
    assert contagens["cpf"] == 0


def test_idempotencia_da_redacao():
    texto = (
        "Ana Paula de Oliveira\n"
        "Email: ana.oliveira@example.test\n"
        "Telefone: (11) 97654-3210\n"
        "CPF: 111.222.333-44\n"
        "Endereço: Rua dos Pinheiros, 500, Pinheiros\n"
        "CEP: 05422-000\n"
        "GitHub: github.com/ana-oliveira\n"
        "Período: 2019-2023. Desempenho: 100%."
    )
    primeiro_passo, contagens1 = redigir_pii(texto)
    segundo_passo, contagens2 = redigir_pii(primeiro_passo)

    # O texto redigido deve ser estritamente identico
    assert primeiro_passo == segundo_passo

    # Na segunda aplicacao, nenhuma redacao nova deve ocorrer
    for cat, qtd in contagens2.items():
        assert qtd == 0, f"Segunda passagem gerou contagem em {cat}: {qtd}"


def test_endereco_falsos_positivos_e_sem_consumir_texto_livre():
    # Item 1: "Python, R e SQL, 3 anos" e "Domínio de R e Julia, 3 projetos" inalterados
    t1 = "Python, R e SQL, 3 anos"
    res1, c1 = redigir_pii(t1)
    assert res1 == t1
    assert c1["endereco"] == 0

    t2 = "Domínio de R e Julia, 3 projetos"
    res2, c2 = redigir_pii(t2)
    assert res2 == t2
    assert c2["endereco"] == 0

    # Item 1: Complemento nao consome texto livre
    t3 = "Rua Augusta, 1000 e trabalho como dev há 10 anos"
    res3, c3 = redigir_pii(t3)
    assert res3 == "[ENDERECO] e trabalho como dev há 10 anos"
    assert c3["endereco"] == 1


def test_endereco_sem_virgula_e_complementos_imovel():
    # Item 2: Endereco sem virgula
    casos_validos = [
        ("Rua Augusta 1000", "[ENDERECO]"),
        ("Avenida Paulista 1578", "[ENDERECO]"),
        ("Rua Vergueiro nº 123", "[ENDERECO]"),
        ("Av. Brasil, 500, apto 12", "[ENDERECO]"),
    ]
    for entrada, esperado in casos_validos:
        res, c = redigir_pii(entrada)
        assert res == esperado, f"Falhou para entrada: {entrada}"
        assert c["endereco"] == 1

    # Sem numero pode ficar inalterado
    t_sem_num = "Projetos em Av. Paulista? Não."
    res_sn, c_sn = redigir_pii(t_sem_num)
    assert res_sn == t_sem_num
    assert c_sn["endereco"] == 0


def test_cabecalho_nome_e_cargos_primeiras_3_linhas():
    # Item 3: Cargo na 1a linha nao vira [NOME], nome real na 3a linha vira [NOME]
    t1 = "Analista de Dados\nCoordenação de Projetos\nMaria Silva"
    res1, c1 = redigir_pii(t1)
    assert res1 == "Analista de Dados\nCoordenação de Projetos\n[NOME]"
    assert c1["nome"] == 1

    # Linha única de cargo fica inalterada
    t2 = "Engenheiro Civil Sênior"
    res2, c2 = redigir_pii(t2)
    assert res2 == t2
    assert c2["nome"] == 0

    # Nome na 1a linha e cargo na 2a linha
    t3 = "Maria Silva\nAnalista de Dados"
    res3, c3 = redigir_pii(t3)
    assert res3 == "[NOME]\nAnalista de Dados"
    assert c3["nome"] == 1

    # Iniciais com ponto permitidas
    t4 = "Carlos A. da Silva"
    res4, c4 = redigir_pii(t4)
    assert res4 == "[NOME]"
    assert c4["nome"] == 1


def test_telefone_ddd_com_zero_e_evita_match_parcial():
    # Item 4: Aceitar DDD com zero
    t_zero1 = "Contato: (011) 98765-4321 urgente"
    res_z1, c_z1 = redigir_pii(t_zero1)
    assert "[TELEFONE]" in res_z1
    assert "(011) 98765-4321" not in res_z1
    assert c_z1["telefone"] == 1

    t_zero2 = "Ligue para 011 98765-4321 hoje"
    res_z2, c_z2 = redigir_pii(t_zero2)
    assert "[TELEFONE]" in res_z2
    assert "011 98765-4321" not in res_z2
    assert c_z2["telefone"] == 1

    # Item 4: 11 dígitos isolados vira [CPF] inteiro, nunca match parcial de telefone
    t_cpf11 = "Processei 12345678901 registros"
    res_cpf11, c_cpf11 = redigir_pii(t_cpf11)
    assert res_cpf11 == "Processei [CPF] registros"
    assert c_cpf11["telefone"] == 0
    assert c_cpf11["cpf"] == 1

    # Item 4: 14 dígitos fica inalterado
    t_14dig = "Total de 10011987654321 transações"
    res_14, c_14 = redigir_pii(t_14dig)
    assert res_14 == t_14dig
    assert c_14["telefone"] == 0
    assert c_14["cpf"] == 0



