"""Cria a persona de demonstração e percorre a jornada pela API real (com a LLM real).

A persona é fictícia ("Marina, técnica de manutenção industrial em transição para monitoramento
IoT"), fica marcada com persona_demo='S' no Oracle e usa só dados inventados. A senha é gerada
aqui e gravada **fora do repositório** em <dados>/demo/persona_demo.json (nunca impressa).

Passos: cadastro → marcação de persona → consentimentos → intenção → currículo (texto) →
confirmação → extração de competências (LLM) → revisão (confirmar/rejeitar/não possuo) →
comparação de 3 destinos → escolha do destino IoT → plano → 1 checkpoint concluído →
exercício diagnóstico (LLM) → sessão de laboratório com relato.

Uso (a partir de app/tools, com a API de pé e ORACLE_* do mesmo schema da API no ambiente):
    uv run --with oracledb python criar_persona_demo.py --base http://127.0.0.1:8003 --dados <DADOS>
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

EMAIL = "marina.demo@citizentech.exemplo"
CURRICULO = (
    "Marina Fictícia — Técnica em manutenção industrial\n"
    "Contato: marina.ficticia@exemplo.test · (11) 90000-1234\n\n"
    "Experiência (10 anos) em indústria de autopeças. Faço a manutenção preventiva de prensas e "
    "esteiras e acompanho sensores de temperatura e de presença instalados nas células. Configuro "
    "alarmes no supervisório e trato falhas de comunicação entre CLP e o painel. Registro as "
    "medições em planilhas e monto relatórios semanais de paradas. Conheço o protocolo Modbus e "
    "estudei MQTT em um curso livre. Participei da análise de riscos de uma nova linha de solda."
)
RESPOSTA_ABERTA = (
    "Hipóteses: (1) borda — GPIO do LED e do buzzer danificada ou atuador sem alimentação; sensor "
    "travado repetindo leitura; (2) firmware — laço principal travado ou condição de acionamento "
    "comparando com limiar errado; (3) rede — broker MQTT retendo mensagem antiga (retain) ou "
    "perda de conexão sem reconexão, por isso o painel mostra o último status normal. "
    "Isolamento: medir tensão na GPIO e acionar os atuadores por comando local; injetar uma "
    "leitura de teste acima de 45 °C e conferir no monitor serial a decisão do firmware; "
    "acompanhar o tópico no broker e conferir horário da última mensagem. "
    "Prevenção: heartbeat a cada 10 s com alerta de dispositivo offline quando passar de 30 s, "
    "watchdog de hardware que reinicia o nó travado e um circuito de parada independente "
    "(fail-safe) que desliga a esteira se a distância ficar abaixo de 8 cm."
)


class Cliente:
    def __init__(self, base: str) -> None:
        self.base = base.rstrip("/")
        self.cookies: dict[str, str] = {}
        self.log: list[str] = []

    def req(
        self, metodo: str, caminho: str, corpo=None, esperado: tuple[int, ...] = (200, 201, 204)
    ):
        dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
        cab = {"Content-Type": "application/json"} if dados is not None else {}
        if self.cookies:
            cab["Cookie"] = "; ".join(f"{k}={v}" for k, v in self.cookies.items())
            if metodo != "GET" and "csrf_token" in self.cookies:
                cab["X-CSRF-Token"] = self.cookies["csrf_token"]
        r = urllib.request.Request(self.base + caminho, data=dados, headers=cab, method=metodo)
        try:
            with urllib.request.urlopen(r, timeout=240) as x:
                status, texto, sc = (
                    x.status,
                    x.read().decode("utf-8"),
                    x.headers.get_all("Set-Cookie") or [],
                )
        except urllib.error.HTTPError as e:
            status, texto, sc = (
                e.code,
                e.read().decode("utf-8"),
                e.headers.get_all("Set-Cookie") or [],
            )
        for linha in sc:
            nome, _, resto = linha.partition("=")
            self.cookies[nome.strip()] = resto.split(";", 1)[0]
        self.log.append(f"{metodo} {caminho.split('?')[0]} -> {status}")
        if status not in esperado:
            raise RuntimeError(f"{metodo} {caminho} devolveu {status}: {texto[:300]}")
        return json.loads(texto) if texto else None


def marcar_persona(usuario_id: str) -> None:
    import oracledb

    with oracledb.connect(
        user=os.environ["ORACLE_USER"],
        password=os.environ["ORACLE_PASSWORD"],
        dsn=os.environ["ORACLE_DSN"],
    ) as c:
        c.cursor().execute("UPDATE usuario SET persona_demo = 'S' WHERE id = :id", id=usuario_id)
        c.commit()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", default="http://127.0.0.1:8003")
    ap.add_argument("--dados", required=True)
    args = ap.parse_args(argv)
    arq = Path(args.dados) / "demo" / "persona_demo.json"
    api = Cliente(args.base)

    if arq.exists():
        cred = json.loads(arq.read_text(encoding="utf-8"))
    else:
        cred = {"email": EMAIL, "senha": secrets.token_urlsafe(16)}
        u = api.req("POST", "/auth/registrar", cred)
        cred["usuario_id"] = u["id"]
        cred["criado_em"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        arq.parent.mkdir(parents=True, exist_ok=True)
        arq.write_text(json.dumps(cred, ensure_ascii=False, indent=2), encoding="utf-8")
        marcar_persona(u["id"])
    api.req("POST", "/auth/login", {"email": cred["email"], "senha": cred["senha"]})
    me = api.req("GET", "/me")
    print(f"persona: {me['email']} · persona_demo={me['persona_demo']}")

    ativos = {
        c["finalidade"]
        for c in api.req("GET", "/me/consentimentos")["itens"]
        if c["revogado_em"] is None
    }
    for finalidade in ("perfil", "curriculo_llm", "laboratorio_nuvem"):
        if finalidade not in ativos:
            api.req("POST", "/me/consentimentos", {"finalidade": finalidade})
    api.req(
        "PUT",
        "/me/intencao",
        {
            "atividades_desejadas": [
                "Monitorar sensores de linhas de produção",
                "Montar painéis de alarmes",
            ],
            "motivos": [
                "Quero sair da manutenção corretiva e trabalhar com dados de monitoramento"
            ],
            "horas_semana": 8,
            "orcamento_mensal_brl": 200.0,
            "uf": "SP",
        },
    )

    cv = api.req("POST", "/me/experiencias", {"texto": CURRICULO})
    print(f"currículo redigido: redações={ {k: v for k, v in cv['redacoes'].items() if v} }")
    api.req(
        "POST", "/me/curriculo/confirmar-envio", {"curriculo_id": cv["id"], "texto_revisado": None}
    )
    ext = api.req("POST", "/me/competencias/extrair", {"curriculo_id": cv["id"]})
    cand = ext["candidatas"]
    print(
        f"extração: modelo={ext['modelo']} · candidatas={len(cand)}"
        f" · descartadas={ext['descartadas']}"
    )
    for i, c in enumerate(cand):
        # Revisão humana simulada: a última sugestão a persona diz que não possui e a penúltima
        # ela rejeita (não corresponde ao que faz); as demais ela confirma.
        acao = "confirmar"
        if len(cand) >= 3 and i == len(cand) - 1:
            acao = "nao_possuo"
        elif len(cand) >= 3 and i == len(cand) - 2:
            acao = "rejeitar"
        api.req("PATCH", f"/me/competencias/{c['id']}", {"acao": acao})
        print(f"  {c['titulo']}: {acao}")
    comp = api.req(
        "POST",
        "/me/comparacoes",
        {
            "destinos": ["analista_monitoramento_iot", "analista_processos", "analista_dados_bi"],
            "uf": "SP",
        },
    )
    for d in comp["destinos"]:
        print(
            f"comparação {d['destino_id']}: {d['dimensoes']['requisitos']['contagem']} · "
            f"obrigatórios não atendidos={len(d['dimensoes']['obrigatorios_nao_atendidos'])}"
        )
    cam = api.req(
        "POST",
        "/me/caminho",
        {"destino_id": "analista_monitoramento_iot", "comparacao_id": comp["comparacao_id"]},
    )
    plano = cam["plano"]
    primeiro = next(c for c in plano["checkpoints"] if c["tipo"] in ("estudar", "demonstrar"))
    api.req("PATCH", f"/me/plano/checkpoints/{primeiro['id']}", {"status": "concluido"})
    print(
        f"plano: {len(plano['checkpoints'])} checkpoints"
        f" · já demonstrados={plano['ja_demonstrados']}"
    )

    ex = api.req("GET", "/destinos/analista_monitoramento_iot/exercicio")
    respostas = {"q1": "B", "q2": "C", "q3": "A", "q4": "A"}  # uma errada de propósito (q3)
    t = api.req(
        "POST",
        "/me/tentativas",
        {
            "destino_id": "analista_monitoramento_iot",
            "exercicio_id": ex["exercicio_id"],
            "respostas_objetivas": respostas,
            "resposta_aberta": RESPOSTA_ABERTA,
        },
    )
    print(
        f"exercício: objetiva={t['objetiva']['acertos']}/{t['objetiva']['total']}"
        f" · aberta={t['aberta']['status']} "
        f"nota={t['aberta']['nota']} · final={t['nota_final']} · resultado={t['resultado']}"
    )

    s = api.req("POST", "/me/laboratorio/sessoes")
    api.req(
        "POST",
        f"/me/laboratorio/sessoes/{s['id']}/relato",
        {
            "relato": (
                "Temperatura do motor subiu rápido depois de 10 min de operação; buzzer acionou."
            )
        },
    )
    print(f"laboratório: código {s['codigo']} até {s['expira_em']}")
    comp2 = api.req(
        "POST", "/me/comparacoes", {"destinos": ["analista_monitoramento_iot"], "uf": "SP"}
    )
    d = comp2["destinos"][0]
    print(f"comparação após o exercício: {d['dimensoes']['requisitos']['contagem']}")
    print("chamadas:", " | ".join(api.log))
    print(f"credenciais da persona gravadas em {arq} (fora do repositório)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
