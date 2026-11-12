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

## Decisões tomadas fora do plano

- **Equipe (12/11):** Guilherme Orugian (RM572882), Lucas Henrique (RM571901), Rodrigo Bettio (RM573725). Trio, dentro do limite da Estatística (resolve R09). Registrado em `00_projeto/README.md`; usar em todas as capas.
- **LLM fallback (D06a):** `openai/gpt-4o-mini` (structured_outputs verificado no OpenRouter em 12/11).
- **`app/.env` criado (12/11)** a partir de `app/.env.example`, com os segredos locais gerados aleatoriamente (Oracle, Postgres/Mongo de teste, JWT, DEVICE_KEY). O `.gitignore` protege `.env*`, exceto `.env.example`.

## Próximo passo exato

1. Executar S0 (esqueleto `app/`, `.gitignore`/`.env.example`, smoke do compose + oracle-free, smoke do Astryx, pipeline md→pdf) em paralelo com o agente de dados (ingestão do Caged, S6).
