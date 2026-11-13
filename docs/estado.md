# Estado do desenvolvimento

> Arquivo vivo, mantido pelo orquestrador (CLAUDE.md §5). É o primeiro arquivo lido em cada sessão: seja curto e factual.

**Atualizado em:** 13/11/2026, 11h15 · **Dias até o prazo (19/11 23h55):** 6,5 · **Fase:** D1 concluído com sucesso (S0, S1 e S6 integradas e validadas de ponta a ponta)

## Concluído

- Documentação de base: proposta, plano v1.1 (D01–D25), revisões adversariais (R01–R30) e `CLAUDE.md`.
- **S0 — esqueleto (12/11), em `main`.** Evidência executada pelo orquestrador:
  - `.gitattributes`, `core.longpaths=true`, `.gitignore` ampliado (§15.3); `uv` por componente (`app/api`, `app/ml`, `app/cloud`, `app/tools`), Python 3.11.
  - `app/docker-compose.yml`, profile `teste`: 3 serviços *healthy* (Oracle 26ai Free no `FREEPDB1`, Postgres 17.11 na 5433, Mongo 8.0.38 na 27018), login testado nos três.
  - `app/config/limiares.json` e `GET /health` (RED → GREEN pelo `TestClient`).
  - `app/tools/md_para_pdf.py`: 5 testes com Edge real; plano → PDF de 14 páginas; `--max-paginas 2` → saída 1.
  - `app/web`: React 19.3 + Vite 8 + Tailwind 4 + Astryx 0.7.14; teste, build e captura de tela ok. **Plano B (Radix) não acionado.**
- **S1 — limiares compartilhados (12/11), em `main`.** Via `agy`. Os 3 cenários classificam igual na API e na Lambda; tabela compartilhada em `app/config/casos_limiares.json`.
- **S6 — ingestão do Novo Caged: concluída e validada (13/11), em `main`.**
  - Código implementado via `agy` (2 rodadas) e refinado pelo orquestrador.
  - Lista de ocupações CBO aprovada pelo usuário versionada em `app/catalogo/ocupacoes_cbo.json` (6 destinos, 34 códigos; 22 de reserva).
  - **Download e processamento completo (202001–202609):** 243 arquivos verificados, 239 ingeridos, 4 ausentes na fonte legítimos (FOR e EXC de 202001, EXC de 202002 e EXC de 202003), 0 falhas, 0 pendentes.
  - 239 arquivos Parquet gerados em `.dados\caged\parquet\` totalizando 107,32 MB.
  - `caged\bruto\` 100% limpo e vazio.
  - **Conferência independente:** contagem de admissões no MOV em 7 competências amostrais (202001, 202101, 202201, 202301, 202401, 202501 e 202609) 100% idêntica às sondagens prévias independentes.
  - Nenhuma coluna sensível preservada nos Parquets (estrita adesão ao R05).
- **Push (13/11):** `main` enviado para `https://github.com/orugian/gs-semestre2` (remoto `gs-semestre2`). Gitleaks limpo em todo o histórico.
- Regressão em `main` (13/11): `uv run pytest` → api 48, cloud 50, ml 25, tools 5 (todos passando). Web: 1 teste (vitest).

## Em andamento

- **D2 iniciado em 13/11 às 11h08 (antecipado em relação ao cronograma de 14/11).** Ritual: `Get-Date`, `git status --short` limpo, `git worktree list` só main `e81fc3c`, disco 15,6 GB; nenhum gatilho de corte acionado.
- **S7 devolvida para correção (rodada 2):** implementação `pwsh-223` terminou/saída0, testes autorais executados pelo orquestrador (`pwsh-230`) →40 verdes e lint limpo, mas aceite independente →10 falhas (cobertura incompleta/revisões pendentes, coerções inválidas, catálogo sobreposto, fold vazio). Novo job `pwsh-232` ativo; worktree `GS-wt/S7-features`, branch `fatia/S7-features`; contratos/relatórios `.kaiser/{contratos,reports}/S7-features[-r2].md`; evidência `.kaiser/reports/S7-aceite-adversarial-red.txt`. RED inicial do autor foi NotImplementedError, não asserção: não aceito como prova de TDD; novos RED por asserção executados e reprodução T18 independente pendente. Holdout fechado; revisão independente ainda pendente.
- **Bancos de teste iniciados nesta sessão:** job `pwsh-221` concluído/saída 0; `docker compose -f app/docker-compose.yml --profile teste up -d --wait` → Oracle, Postgres e Mongo healthy; volumes preservados.
- Processo `agy.exe` PID 25872 (09h54) encerrado após autorização explícita do usuário nesta sessão (ocioso). Verificação de identidade incluiu nome, pai e horário; a primeira tentativa não o encerrou por diferença de fração de segundo na comparação.
- **S2 devolvida para correção (rodada 2):** job `pwsh-228` concluído/saída0; regressão do orquestrador `pwsh-234` →58 testes verdes e lint limpo. Aceite independente executado →6 falhas: POST201 sobre CSV corrompido, reflexão de conteúdo privado em 4 erros, Bearer não previsto aceito. Novo job `pwsh-236` ativo; worktree `GS-wt/S2-leituras`, branch `fatia/S2-leituras`; contratos/relatórios `.kaiser/{contratos,reports}/S2-leituras[-r2].md`, evidência `.kaiser/reports/S2-aceite-adversarial-red.txt`. Escopo disjunto de S7; 2 agy ativos.
- **S5 — acesso local aprovado pelo usuário:** criado schema exclusivo `CT_S5_TESTE` no Oracle Docker `FREEPDB1` com credencial didática (não de produção), quota50M e somente CREATE SESSION/TABLE/SEQUENCE; comando SQL*Plus via autenticação OS do container → usuário OPEN. Nenhum usuário anterior, FIAP ou nuvem alterado. Credencial de fixture será fornecida só na execução de teste, não copiada de .env.
- **Regressão inicial executada nesta sessão:** job `pwsh-225` saída0; `uv run pytest -q` + `uv run ruff check .` em api (48), ml (25), cloud (50), tools (5): todos verdes. Aviso de depreciação Starlette/httpx na API, sem falha.
- **RED T18 reproduzido pelo orquestrador:** worktree temporário destacado `GS-wt/S7-red` em main `e81fc3c`, teste copiado sem alterações (SHA256 `37d976e2bbcf61cea5ad5965f2a19525c344cb71a192a919bcfb3381d520faa2`) + interface mínima retornando painel vazio; `uv run pytest ...::test_t18_for_tardio_nao_altera_features_anteriores -q` → AssertionError `0 == 1` na quantidade esperada da série (não ImportError/NotImplementedError). Evidência `.kaiser/reports/S7-red-reproduzido.txt`. Não é prova retroativa do RED autoral; é reprodução independente. Worktree descartável, ainda presente.
- **Catálogo:** pesquisa ESCO oficial somente leitura delegada a subagente nativo `eb51d8d4-c3e4-4cbb-b0aa-2c805edf4da5`; nenhuma implementação delegada a agente nativo. Aguardar URIs/títulos verificados para contrato agy do rascunho YAML.
- Próximos trabalhos independentes: preparar requisitos S3/S5/catálogo; aceitar resultados S7/S2 quando concluírem. Nenhum push autorizado nesta sessão.

## Bloqueios e pendências [HUMANO]

- [ ] **Repositório público:** `orugian/gs-semestre2` está **público** e contém nomes e RMs da equipe, e-mails nos metadados dos commits e o material do professor (`docs\material_por_cadeira\`, PDFs dos enunciados). Confirmar que é isso mesmo ou tornar privado.
- [ ] **Qual é o remoto oficial?** `origin` continua `insonia999/GS2_26` (D14b) e não recebeu push. Decidir se `gs-semestre2` substitui o `origin` ou se os dois recebem push.
- [ ] `MONGODB_URI` completa e IP liberado no Atlas.
- [ ] Senha correta do Oracle FIAP.
- [ ] Sessão do Learner Lab e porta 5432 do RDS antes do D4.
- [ ] Caminho da IA de sentimento (créditos HF ou Comprehend).
- [ ] AWS CLI (instalar ou usar o console).
- [ ] Ok para o snapshot da Adzuna (até 12 chamadas, com contador).
- [ ] Revisão humana das rubricas até **D3 (15/11) às 18h**, senão corte automático para 3 destinos (R29).
- [ ] `gh auth refresh -s project,read:project`; ideia da live (AIC); quem grava cada vídeo.

**Disco:** 15,59 GB livres em 13/11 às 11h15.

## Validação das credenciais (12/11, sem expor valores)

| Serviço | Resultado | Ação |
|---|---|---|
| OpenRouter | ok (limite US$ 7); JSON válido via json_schema | — |
| Adzuna | ok (1 de 25 chamadas usada como smoke) | snapshot com o contador, depois do ok |
| Hugging Face | token válido, inferência retorna **402 (sem créditos)** | decidir: créditos HF ou Comprehend |
| Lambda (reaproveitada) | 200, mas ainda é `cp2-hello-world` | subir o código na S4 |
| RDS (reaproveitado) | **TCP 5432 com timeout** | Learner Lab, SG (D09), usuário `app_ingest` |
| Oracle FIAP | **ORA-01017** | corrigir `ORACLE_FIAP_PASSWORD` |
| Mongo Atlas | **`MONGODB_URI` só com o usuário** | URI completa e IP liberado |

## Decisões tomadas fora do plano

- **Equipe (12/11):** Guilherme Orugian (RM572882), Lucas Henrique (RM571901), Rodrigo Bettio (RM573725).
- **LLM fallback (D06a):** `xiaomi/mimo-v2.6-flash`.
- **AWS reaproveitada (12/11):** Lambda `cp2-hello-world` e RDS `cp1-cloud`, com alteração autorizada.
- **S0 feita pelo orquestrador, não pelo `agy`:** andaime e configuração, em passos pequenos. D14 foi seguido na S1 e na S6.
- **Escolhas locais da S0:** pacote da API chama-se `citizentech`; `app/tools` é projeto uv sem pacote; `@stylexjs/stylex` fixado em 0.19.1 (a 0.19.2 tinha menos de um dia e o pnpm a recusa); `postinstall` do Astryx desativado; `GS22026_enunciadosOG.txt` mantém os bytes originais (`-text`).
- **S6:** Parquet com uma linha por movimentação filtrada, um arquivo por tipo e competência, em `.dados\caged\parquet\` (o plano cita `app/data/`; vale o mapa do CLAUDE.md §15.1).
- **S6:** a ingestão baixa a união dos destinos com a reserva (56 códigos); o hash da lista depende só do conjunto de códigos. A atribuição de códigos a destinos pode mudar até o congelamento da S7 sem novo download.
- **Ocupações (13/11), decisões do usuário:** manter 142330 no destino 1; manter 142315 na reserva (destino 4 fica com 2 códigos); 252105 na reserva; aceitar a esparsidade do destino 2 e as quebras de série de 211220, 212425 e 212430.

## Não verificado

- `GET /health` num servidor `uvicorn` real (só pelo `TestClient`).
- Títulos oficiais da CBO no site do MTE (reCAPTCHA); o título de 211220 vem de fonte secundária.

## Próximo passo exato

1. **D2, frente B (caminho crítico):** contrato e `agy` da **S7** (features e split: T04, T05, T18, T19; **revisão independente obrigatória**) + EDA + medição da defasagem do FOR (R02) + baselines.
2. **D2, frente A:** S2 (leituras CTP, modo isolado), depois S3 (outbox) e S5 (auth), estas duas com revisão independente. Subir os serviços de teste antes das fatias que usam banco. Rascunho por agente do catálogo YAML dos 6 destinos (ESCO, questões, rubricas).
3. **Snapshot da Adzuna:** script com contador (máximo 12 chamadas), disparado assim que aprovado pelo usuário.
