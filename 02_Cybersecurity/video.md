# Vídeo pitch — Cybersecurity (máx. 5 min)

**Link (YouTube não listado):** [HUMANO — preencher]
**Conteúdo exigido:** problema · solução · riscos · proteção implementada.

## Preparação (antes de gravar)
1. Docker com Oracle e Mongo de teste de pé: `docker compose -f app\docker-compose.yml --profile teste up -d --wait`.
2. API local contra os bancos de teste (segredos gerados em memória): `powershell -File ..\.kaiser\ferramentas\subir_api_teste.ps1` (ou `cd app\api; uv run uvicorn citizentech.main:app --port 8000` com as variáveis de teste).
3. Terminal com fonte grande em `app\tools`. Navegador com `02_Cybersecurity/relatorio.pdf` aberto nas páginas da matriz de riscos e da LGPD.
4. **Não mostrar** `app\.env`, o console da AWS sem tarja nem nenhum e-mail real.

## Roteiro com tempos

| Tempo | Fala (resumo) | Tela |
|---|---|---|
| 0:00–0:30 | Problema: profissionais em transição de carreira decidem com pouca evidência e entregam currículo e documentos para muitos sites. Nossa solução compara destinos sem nota única e trata o currículo com IA. | Aba "Minha transição" do app |
| 0:30–1:10 | Solução e arquitetura: web → API → Oracle e MongoDB → modelo de linguagem só com texto redigido e confirmado → laboratório IoT → Lambda e RDS. | Diagrama da §1 do relatório |
| 1:10–2:10 | Riscos: matriz com 10 riscos; os três residuais altos são vazamento de dado do currículo, RDS público e Function URL sem autenticação obrigatória, e engenharia social com falso recrutador. Explicar por que o RDS está público (Lambda fora de VPC) e que é exceção acadêmica. | Matriz de riscos (§3) |
| 2:10–4:10 | **Demonstração ao vivo:** rodar `uv run python demo_protecoes.py --base http://127.0.0.1:8000`. Comentar em voz alta: senha curta 400; cookie HttpOnly e Secure; token adulterado 401; POST sem CSRF 403; CPF, e-mail e telefone fictícios redigidos; usuário B não lê o currículo de A (404); IA bloqueada antes da confirmação (403); logout invalida a sessão; força bruta vira 429. Terminar mostrando `falhas=0`. | Terminal |
| 4:10–4:40 | LGPD: consentimento por finalidade e revogável, minimização (original do currículo não é guardado), a pessoa vê e edita o texto antes da IA, `data_collection=deny`. | §6 do relatório |
| 4:40–5:00 | Fechamento: o que fica para produção (MFA, RDS privado, WAF, exclusão de conta). Nomes e RMs. | Slide final ou tela do relatório |

## Frases que NÃO usar
"100% seguro", "inviolável", "LGPD garantida", "sem riscos". Diga "reduz", "mitiga", "risco residual".
