"""Modulo de redacao de PII (dados pessoais) em curriculos e experiencias."""

import re

# Marcadores padronizados
MARCADOR_NOME = "[NOME]"
MARCADOR_EMAIL = "[EMAIL]"
MARCADOR_TELEFONE = "[TELEFONE]"
MARCADOR_CPF = "[CPF]"
MARCADOR_CEP = "[CEP]"
MARCADOR_ENDERECO = "[ENDERECO]"
MARCADOR_URL = "[URL]"

# URLs e perfis
PADRAO_URL = re.compile(
    r"\b(?:https?://|www\.)[^\s<>'\"\)]+|\b(?:linkedin\.com|github\.com)/[^\s<>'\"\)]+",
    re.IGNORECASE | re.MULTILINE,
)

# E-mail
PADRAO_EMAIL = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

# CPF: formatado (000.000.000-00) ou 11 digitos isolados
PADRAO_CPF_FORMATADO = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
PADRAO_CPF_DIGITOS = re.compile(r"(?<!\d)\d{11}(?!\d)")

# Telefone BR:
# Com ou sem +55, DDD com ou sem zero/parenteses, celular (9 digitos) ou fixo (8 digitos)
# Exige (?<!\d) a esquerda quando sem +55 e (?!\d) a direita para evitar match parcial
PADRAO_TELEFONE_DDD = re.compile(
    r"(?:(?:\+55\s*)|(?<!\d))(?:\(0?[1-9]{2}\)|0?[1-9]{2})\s*[-.]?\s*"
    r"(?:9\s*\d{4}[-.\s]?\d{4}|[2-5]\d{3}[-.\s]?\d{4})(?!\d)"
)
# Telefone sem DDD precedido por rotulo explicito
PADRAO_TELEFONE_ROTULO = re.compile(
    r"\b(?:tel(?:efone)?|cel(?:ular)?|whatsapp|whats|fone|contato)\s*[:.]?\s*"
    r"(?:9\s*\d{4}[-.\s]?\d{4}|[2-5]\d{3}[-.\s]?\d{4})(?!\d)",
    re.IGNORECASE,
)

# CEP: 00000-000 ou 00000000 precedido de CEP
PADRAO_CEP_FORMATADO = re.compile(r"\b\d{5}-\d{3}\b")
PADRAO_CEP_ROTULO = re.compile(
    r"\bcep\s*[:.]?\s*(\d{8}|\d{5}-\d{3})\b",
    re.IGNORECASE,
)

# Endereco: iniciado por Rua, R., Avenida, Av., etc. seguido de logradouro e numero
# Nao usa IGNORECASE no tipo de logradouro (exige maiuscula; abreviacoes R. e Av. exigem ponto)
PADRAO_ENDERECO = re.compile(
    r"(?:\b(?:Rua|Avenida|Alameda|Travessa|Rodovia|Estrada|Praça|Praca)\b|\bR\.|\bAv\.)"
    r"[^\S\r\n]+[A-Za-zÀ-ÿ0-9.'-]+(?:[^\S\r\n]+[A-Za-zÀ-ÿ0-9.'-]+)*?"
    r"(?:\s*,\s*|\s+)(?:(?i:n[º°o]?\.?|número|numero|km)\s*)?\d+[A-Za-z]?"
    r"(?:(?:\s*,\s*|\s+)(?i:apto|ap|bloco|bl|casa|sala|cj|andar)\.?\s*\d+[A-Za-z]?)?"
    r"(?!\w)"
)

# Linha com rotulo "Nome: ..."
PADRAO_NOME_ROTULO = re.compile(
    r"^\s*Nome\s*:\s*[^\n]+$",
    re.IGNORECASE | re.MULTILINE,
)

TERMOS_PROFISSIONAIS_SECAO = {
    "analista",
    "desenvolvedor",
    "desenvolvedora",
    "engenheiro",
    "engenheira",
    "gerente",
    "coordenador",
    "coordenadora",
    "coordenação",
    "coordenacao",
    "consultor",
    "consultora",
    "arquiteto",
    "arquiteta",
    "especialista",
    "técnico",
    "técnica",
    "tecnico",
    "tecnica",
    "professor",
    "professora",
    "cientista",
    "assistente",
    "diretor",
    "diretora",
    "supervisor",
    "supervisora",
    "perfil",
    "objetivo",
    "resumo",
    "formação",
    "formacao",
    "experiência",
    "experiencia",
    "competências",
    "competencias",
    "habilidades",
    "idiomas",
    "contato",
    "dados",
    "informações",
    "informacoes",
    "currículo",
    "curriculo",
    "curriculum",
}

TITULOS_NAO_NOME = {
    "curriculum vitae",
    "currículo vitae",
    "curriculo vitae",
    "curriculum",
    "currículo",
    "curriculo",
    "resumo profissional",
    "experiência profissional",
    "experiencia profissional",
    "informações pessoais",
    "dados pessoais",
}


def _tratar_url(match: re.Match) -> str:
    val = match.group(0)
    trailing = ""
    while val and val[-1] in ".,;:!?)":
        trailing = val[-1] + trailing
        val = val[:-1]
    return f"{MARCADOR_URL}{trailing}"


def redigir_pii(texto: str) -> tuple[str, dict[str, int]]:
    """Substitui dados pessoais (PII) por marcadores e retorna as contagens.

    Funcao pura e idempotente.
    """
    contagens = {
        "nome": 0,
        "email": 0,
        "telefone": 0,
        "cpf": 0,
        "cep": 0,
        "endereco": 0,
        "url": 0,
    }

    if not texto:
        return texto, contagens

    resultado = texto

    # 1. Nome explicito por rotulo ("Nome: ...")
    def _sub_nome_rotulo(match: re.Match) -> str:
        contagens["nome"] += 1
        return MARCADOR_NOME

    resultado, n_rotulos = PADRAO_NOME_ROTULO.subn(_sub_nome_rotulo, resultado)

    # 2. Heuristica de cabecalho (avalia TODAS as 3 primeiras linhas nao vazias sem break)
    linhas = resultado.splitlines(keepends=True)
    indices_nao_vazios = [
        i for i, linha in enumerate(linhas) if linha.strip()
    ]

    for idx in indices_nao_vazios[:3]:
        linha_pura = linhas[idx].strip()
        if MARCADOR_NOME in linha_pura:
            continue
        if (
            len(linha_pura) <= 80
            and not any(ch.isdigit() for ch in linha_pura)
            and "@" not in linha_pura
            and "[" not in linha_pura
            and "]" not in linha_pura
        ):
            palavras = linha_pura.split()
            if 2 <= len(palavras) <= 6:
                primeira_palavra = palavras[0].lower().rstrip(":,.-")
                if primeira_palavra in TERMOS_PROFISSIONAIS_SECAO:
                    continue
                if any(
                    linha_pura.lower().startswith(termo)
                    for termo in TERMOS_PROFISSIONAIS_SECAO
                ):
                    continue
                if linha_pura.lower() in TITULOS_NAO_NOME:
                    continue
                # Permite palavras com letras/acentos/hifens e iniciais com ponto (ex: A.)
                if all(
                    re.fullmatch(r"[A-Za-zÀ-ÿ]+(?:[-'][A-Za-zÀ-ÿ]+)*|[A-Za-zÀ-ÿ]\.", p)
                    for p in palavras
                ):
                    terminacao = "\n" if linhas[idx].endswith("\n") else ""
                    linhas[idx] = f"{MARCADOR_NOME}{terminacao}"
                    contagens["nome"] += 1

        resultado = "".join(linhas)

    # 3. URLs
    def _sub_url(match: re.Match) -> str:
        contagens["url"] += 1
        return _tratar_url(match)

    resultado = PADRAO_URL.sub(_sub_url, resultado)

    # 4. E-mails
    def _sub_email(match: re.Match) -> str:
        contagens["email"] += 1
        return MARCADOR_EMAIL

    resultado = PADRAO_EMAIL.sub(_sub_email, resultado)

    # 5. Endereco (antes de CEP e telefone)
    def _sub_endereco(match: re.Match) -> str:
        contagens["endereco"] += 1
        return MARCADOR_ENDERECO

    resultado = PADRAO_ENDERECO.sub(_sub_endereco, resultado)

    # 6. CEP (rotulo ou formatado)
    def _sub_cep(match: re.Match) -> str:
        contagens["cep"] += 1
        return MARCADOR_CEP

    resultado = PADRAO_CEP_ROTULO.sub(_sub_cep, resultado)
    resultado = PADRAO_CEP_FORMATADO.sub(_sub_cep, resultado)

    # 7. CPF (formatado ou 11 digitos isolados) - avaliado antes de telefone
    def _sub_cpf(match: re.Match) -> str:
        contagens["cpf"] += 1
        return MARCADOR_CPF

    resultado = PADRAO_CPF_FORMATADO.sub(_sub_cpf, resultado)
    resultado = PADRAO_CPF_DIGITOS.sub(_sub_cpf, resultado)

    # 8. Telefone BR
    def _sub_telefone(match: re.Match) -> str:
        contagens["telefone"] += 1
        return MARCADOR_TELEFONE

    resultado = PADRAO_TELEFONE_ROTULO.sub(_sub_telefone, resultado)
    resultado = PADRAO_TELEFONE_DDD.sub(_sub_telefone, resultado)

    return resultado, contagens
