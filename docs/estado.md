# Estado do desenvolvimento

> Arquivo vivo, mantido pelo orquestrador (CLAUDE.md §5). É o primeiro arquivo lido em cada sessão: seja curto e factual.

**Atualizado em:** 12/11/2026 · **Dias até o prazo (19/11 23h55):** 7 · **Fase:** pré-D1

## Concluído

- Proposta consolidada: `docs/proposta_transicao_carreira.md`.
- Nivelamento Grill Me → plano v1.1: `docs/plano_desenvolvimento.md` (D01–D25).
- Revisão adversarial (2 revisores `agy` + orquestrador): `docs/revisao_adversarial_plano.md` (R01–R30). Decisões do usuário sobre R04, R12 e R13/R14 registradas.
- `CLAUDE.md` do orquestrador criado, com ambiente (§14) e organização/descartáveis (§15). Revisado adversarialmente (2 revisores `agy` + verificação empírica): `docs/revisao_adversarial_claude_md.md` (17 achados adjudicados).
- Estrutura fora do git criada: `GS\.kaiser\{contratos,reports,snapshots,tmp}`.
- Docker Desktop ativo (29.6.2). gitleaks 8.30.1 instalado (autorizado pelo usuário em 12/11).
- Commit inicial dos documentos em `main` (ver `git log`).

## Em andamento

- Nada. Nenhum job ativo, nenhum worktree.

## Bloqueios e pendências [HUMANO]

- [ ] Aprovar o plano v1.1 e o CLAUDE.md.
- [ ] `gh auth refresh -s project,read:project`.
- [ ] Preencher em `app/.env` as variáveis marcadas [USUÁRIO]: OPENROUTER_API_KEY, ADZUNA_APP_ID/KEY, HF_TOKEN, MONGODB_URI, ORACLE_FIAP_*, e depois do deploy FUNCTION_URL/DB_HOST/DB_PASSWORD. As [GERADO] já estão preenchidas.
- [ ] Ideia da live (AIC) e quem grava cada vídeo.
- [ ] Decidir sobre a AWS CLI (instalar ou fazer o deploy pelo console).

**Disco livre em 12/11:** 10,1 GB.

## Validação das credenciais (12/11, sem expor valores)

| Serviço | Resultado | Ação |
|---|---|---|
| OpenRouter | ok: chave ativa (limite US$ 7); `deepseek-v4.1-flash-1017` devolveu JSON válido via json_schema | — |
| Adzuna | ok: 200 (1 de 25 chamadas usada como smoke, registrada no contador) | snapshot só na S6/D1 |
| Hugging Face | token válido, mas a inferência do modelo do enunciado retorna **402 (sem créditos)** | **decidir:** comprar créditos HF ou usar o caminho B (Amazon Comprehend, `pt`), previsto no enunciado de Cloud |
| Lambda (reaproveitada) | 200, mas é `cp2-hello-world`, que responde 'Hello World' em toda rota | subir o código de ingestão na S4 (alteração autorizada pelo usuário) |
| RDS (reaproveitado) | **TCP 5432 com timeout** a partir do IP público desta máquina; DNS público ok | abrir a sessão do Learner Lab e confirmar que o RDS está *available*; liberar o SG (D09); criar `app_ingest` |
| Oracle FIAP | **ORA-01017** (usuário/senha recusados) | corrigir `ORACLE_FIAP_PASSWORD` (e confirmar o serviço `ORCL`); não bloqueia o D1 |
| Mongo Atlas | **`MONGODB_URI` contém só o nome de usuário**; `CONECTION_STRING` é um comando `mongosh` sem senha | preencher `MONGODB_URI=mongodb+srv://<usuario>:<senha>@cluster0.uwow7nl.mongodb.net/?appName=...` e liberar o IP no Network Access |

Variáveis extras no `.env` (`CONECTION_STRING`, `PROJECT_ID`) são ignoradas pelo app.

## Decisões tomadas fora do plano

- **Equipe (12/11):** Guilherme Orugian (RM572882), Lucas Henrique (RM571901), Rodrigo Bettio (RM573725). Trio, dentro do limite da Estatística (resolve R09). Registrado em `00_projeto/README.md`; usar em todas as capas.
- **LLM fallback (D06a):** `xiaomi/mimo-v2.6-flash`, escolha do usuário em 12/11, substituindo o `openai/gpt-4o-mini`. structured_outputs verificado; chamada real com json_schema devolveu JSON válido, sem raciocínio, 18 tokens; US$ 0,14/0,28 por milhão de tokens.
- **AWS reaproveitada (12/11):** por restrição da conta AWS Academy, o grupo reutiliza a Lambda `cp2-hello-world` e o RDS `cp1-cloud` já existentes. O usuário **autorizou quaisquer alterações** neles (código da Lambda, tabelas, usuários e SG), usando as credenciais do `.env`. Continuam valendo os controles D09/D09a.
- **`app/.env` criado (12/11)** a partir de `app/.env.example`, com os segredos locais gerados aleatoriamente (Oracle, Postgres/Mongo de teste, JWT, DEVICE_KEY). O `.gitignore` protege `.env*`, exceto `.env.example`.

## Próximo passo exato

1. Executar S0 (esqueleto `app/`, `.gitignore`/`.env.example`, smoke do compose + oracle-free, smoke do Astryx, pipeline md→pdf) em paralelo com o agente de dados (ingestão do Caged, S6).
