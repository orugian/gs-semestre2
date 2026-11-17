"""Demonstração executável das proteções da API CitizenTech (evidência de Cybersecurity).

Roda contra uma API local já de pé (sem nuvem, sem LLM real) e imprime cada requisição com
o status HTTP obtido e o esperado. Não imprime senhas, cookies nem tokens: as senhas são
geradas aleatoriamente em memória e os e-mails são contas de demonstração descartáveis.

Uso (a partir de app/tools):
    uv run python demo_protecoes.py --base http://127.0.0.1:8000
Saída 0 se todos os resultados baterem com o esperado; 1 caso contrário.
"""

from __future__ import annotations

import argparse
import secrets
import sys
from datetime import UTC, datetime

from _comum import Sessao, requisitar


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", default="http://127.0.0.1:8000")
    base = ap.parse_args(argv).base.rstrip("/")
    falhas = 0

    def verificar(n: str, descricao: str, obtido: int, esperado: int, extra: str = "") -> None:
        nonlocal falhas
        ok = obtido == esperado
        falhas += 0 if ok else 1
        print(
            f"[{n}] {descricao}: HTTP {obtido} (esperado {esperado}) {'OK' if ok else 'FALHOU'}"
            + (f"\n      {extra}" if extra else "")
        )

    agora = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"=== Demonstração de proteções CitizenTech — {agora} — API {base} ===")
    sufixo = secrets.token_hex(4)
    email_a, email_b = f"demo-cyber-a-{sufixo}@exemplo.test", f"demo-cyber-b-{sufixo}@exemplo.test"
    senha_a, senha_b = secrets.token_urlsafe(18), secrets.token_urlsafe(18)
    a, b = Sessao(), Sessao()

    s, c, _ = requisitar(base, "POST", "/auth/registrar", {"email": email_a, "senha": "curta123"})
    verificar(
        "1", "Política de senha: cadastro com senha de 8 caracteres", s, 400, f"resposta: {c}"
    )

    s, c, _ = requisitar(base, "POST", "/auth/registrar", {"email": email_a, "senha": senha_a})
    verificar("2", "Cadastro com senha forte (hash Argon2id no Oracle)", s, 201)
    requisitar(base, "POST", "/auth/registrar", {"email": email_b, "senha": senha_b})

    s, _, sc = requisitar(
        base, "POST", "/auth/login", {"email": email_a, "senha": senha_a}, sessao=a
    )
    atributos = [
        linha.split("=", 1)[0] + ": " + "; ".join(p.strip() for p in linha.split(";")[1:])
        for linha in sc
    ]
    verificar("3", "Login (cookies emitidos; valores omitidos)", s, 200, " | ".join(atributos))
    requisitar(base, "POST", "/auth/login", {"email": email_b, "senha": senha_b}, sessao=b)

    s, c, _ = requisitar(base, "GET", "/me")
    verificar("4", "Acesso a /me sem cookie de sessão", s, 401, f"resposta: {c}")

    adulterada = Sessao()
    adulterada.cookies = dict(a.cookies)
    token = adulterada.cookies["sessao"]
    adulterada.cookies["sessao"] = token[:-2] + ("AA" if token[-2:] != "AA" else "BB")
    s, c, _ = requisitar(base, "GET", "/me", sessao=adulterada)
    verificar("5", "Token de sessão com assinatura adulterada", s, 401, f"resposta: {c}")

    s, c, _ = requisitar(base, "POST", "/me/consentimentos", {"finalidade": "perfil"}, sessao=a)
    verificar("6", "POST autenticado SEM cabeçalho X-CSRF-Token", s, 403, f"resposta: {c}")
    s, _, _ = requisitar(
        base, "POST", "/me/consentimentos", {"finalidade": "perfil"}, sessao=a, csrf=True
    )
    verificar("7", "Mesmo POST com X-CSRF-Token (double-submit)", s, 201)

    texto = (
        "Analista de processos. Contato: maria.teste@exemplo.test, telefone (11) 98765-4321, "
        "CPF 123.456.789-09. Mapeei fluxos em BPMN e reduzi o tempo de ciclo."
    )
    s, c, _ = requisitar(base, "POST", "/me/experiencias", {"texto": texto}, sessao=a, csrf=True)
    redigido = (c or {}).get("texto_redigido", "") if isinstance(c, dict) else ""
    contagens = (
        {k: v for k, v in ((c or {}).get("redacoes") or {}).items() if v}
        if isinstance(c, dict)
        else {}
    )
    sem_pii = all(x not in redigido for x in ("maria.teste@", "98765-4321", "123.456.789-09"))
    verificar(
        "8",
        "Minimização: texto com dados pessoais FICTÍCIOS é redigido antes de gravar",
        s,
        201,
        f"texto gravado: {redigido!r}\n      redações: {contagens}"
        f" · PII ausente do texto gravado: {sem_pii}",
    )
    falhas += 0 if sem_pii else 1
    curriculo_id = (c or {}).get("id") if isinstance(c, dict) else None

    s, c, _ = requisitar(base, "GET", f"/me/curriculo/{curriculo_id}", sessao=b)
    verificar("9", "Usuário B tenta ler o currículo do usuário A (IDOR)", s, 404, f"resposta: {c}")
    s, _, _ = requisitar(base, "GET", f"/me/curriculo/{curriculo_id}", sessao=a)
    verificar("10", "Dono lê o próprio currículo", s, 200)

    s, _, _ = requisitar(
        base, "POST", "/me/consentimentos", {"finalidade": "curriculo_llm"}, sessao=a, csrf=True
    )
    verificar("11a", "Consentimento 'curriculo_llm' concedido (texto ainda NÃO confirmado)", s, 201)
    s, c, _ = requisitar(
        base,
        "POST",
        "/me/competencias/extrair",
        {"curriculo_id": curriculo_id},
        sessao=a,
        csrf=True,
    )
    verificar(
        "11b",
        "Envio à IA antes de o usuário confirmar o texto redigido (D22)",
        s,
        403,
        f"resposta: {c}",
    )

    s, c, _ = requisitar(
        base,
        "POST",
        "/leituras",
        {"dispositivo_id": "lab-iot-bancada-01", "metrica": "temperatura_c", "valor": 25.0},
    )
    verificar("12", "Leitura de sensor sem X-Device-Key", s, 401, f"resposta: {c}")
    s, c, _ = requisitar(
        base,
        "POST",
        "/leituras",
        {"dispositivo_id": "lab-iot-bancada-01", "metrica": "temperatura_c", "valor": 25.0},
        cabecalhos={"X-Device-Key": secrets.token_hex(16)},
    )
    verificar("13", "Leitura de sensor com chave errada", s, 401, f"resposta: {c}")

    antiga = Sessao()
    antiga.cookies = dict(a.cookies)
    s, _, _ = requisitar(base, "POST", "/auth/logout", sessao=a, csrf=True)
    verificar("14", "Logout", s, 204)
    s, c, _ = requisitar(base, "GET", "/me", sessao=antiga)
    verificar("15", "Reuso do cookie antigo após logout", s, 401, f"resposta: {c}")

    email_c = f"demo-cyber-c-{sufixo}@exemplo.test"
    obtidos = []
    for _ in range(8):
        s, c, _ = requisitar(
            base, "POST", "/auth/login", {"email": email_c, "senha": secrets.token_urlsafe(12)}
        )
        obtidos.append(s)
        if s == 429:
            break
    verificar(
        "16",
        "Força bruta: logins errados em sequência até o bloqueio",
        obtidos[-1],
        429,
        f"sequência de status: {obtidos} · resposta final: {c}\n      o limite é de 5 tentativas"
        " por minuto por e-mail E por IP; os 2 logins anteriores deste IP também contam",
    )
    print(f"      e-mails de demonstração (contas descartáveis): {email_a}, {email_b}")

    print(f"=== Resultado: falhas={falhas} (0 = todas as verificações bateram com o esperado) ===")
    return 0 if falhas == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
