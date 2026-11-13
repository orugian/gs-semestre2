# Estado do desenvolvimento

> Arquivo vivo, mantido pelo orquestrador (CLAUDE.md §5). É o primeiro arquivo lido em cada sessão: seja curto e factual.

**Atualizado em:** 13/11/2026, 12h25 · **Dias até o prazo (19/11 23h55):** 6,5 · **Fase:** D2 em andamento (adiantado 1 dia): S7, S2 e rascunho do catálogo integrados; S3 no `agy`; EDA/baselines e S5 a fazer

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

## Concluído no D2 (13/11, sessão iniciada às 11h08)

- **S7 — features e split temporal, em `main` (merge `0586b49`).** `agy` em 2 rodadas + ajustes do orquestrador.
  - Evidência: em `app/ml`, `uv run pytest -q` → 62 passed; `uv run ruff check .` limpo (executado em `main` após o merge).
  - RED: o RED autoral falhou por `NotImplementedError` (não aceito). **Reprodução independente:** teste T18 sem alterações sobre `main` + interface mínima → `AssertionError: 0 == 1` (`.kaiser/reports/S7-red-reproduzido.txt`).
  - Aceite adversarial do orquestrador: 10 falhas na rodada 1 (cobertura incompleta tratada como válida, coerções silenciosas, CBO sobreposto, fold vazio) → corrigidas na rodada 2; mais 2 defeitos residuais (competência com espaços perdia a movimentação; pré-agregado silenciava catálogo sobreposto) corrigidos pelo orquestrador com RED/GREEN.
  - **Revisão independente** (`agy --mode plan`, `.kaiser/reports/S7-features-rev.md`, sobre o commit `d889003`), adjudicação: **RV-S7-01 aceito** (horizonte padrão do alvo anulava alvos quando o manifesto tinha mês futuro pendente; corrigido, teste novo); **RV-S7-02 aceito** (competências inferidas da cobertura não eram validadas, `mes` virava 401; corrigido, teste novo); **RV-S7-03 aceito** (`numpy` declarado em `pyproject.toml`); **RV-S7-04 aceito como dívida, não corrigido** (mapa de cobertura reconstruído a cada chamada; custo medido: pré-agregação dos 239 Parquets em 55 s). As correções pós-revisão (commit `e95cbf5`, ~20 linhas em `extracao.py`) **não passaram por nova revisão independente**.
- **S2 — leituras CTP, em `main` (merge `7da2f57`).** `agy` em 2 rodadas + ajustes do orquestrador.
  - Evidência: em `app/api`, `uv run pytest -q` → 73 passed; ruff limpo. RED autoral por asserção (`501 == 201`), lido no relatório, não reproduzido (S2 não é fatia de risco).
  - Aceite adversarial: 6 falhas na rodada 1 (201 sobre CSV corrompido, eco de conteúdo privado em 4 erros, `Bearer` aceito sem contrato) e 5 na rodada 2 (`status` fora do vocabulário e `tipo_dispositivo` vazio davam 201; datas-limite davam 500; sentinela −127 por tolerância rejeitava −126,999999). Todas corrigidas.
  - **Smoke em `uvicorn` real** (`citizentech.leituras.isolado:app`, porta 8000, chave e CSV descartáveis): 6 POST → 201 nos 3 cenários × 2 métricas com risco normal/atencao/critico corretos; campo ausente → 400; −127 → 400; chave errada → 401; GET paginado (total 6, 3 páginas) e indicadores (média 37,0 °C e 14,0 cm; 2 alertas por métrica); CSV com cabeçalho + 6 linhas. Processo encerrado e porta liberada.
- **Rascunho do catálogo dos 6 destinos, em `main` (merge `659ecbe`).** `agy` em 2 rodadas. `app/catalogo/destinos/*.yaml` + `app/catalogo/README.md` + `app/catalogo/fontes/esco_20261113.json`.
  - Evidência: em `app/tools`, `uv run pytest -q` → 20 passed; ruff limpo. Script do orquestrador: URI, título, tipo, descrição oficial e sha256 dos 48 requisitos idênticos à fonte ESCO; gabaritos A/B/C/D = 6/6/6/6; nenhum requisito obrigatório sem avaliação.
  - A rodada 1 foi devolvida: gabarito só em A/B (16/8), distratores absurdos e resposta certa denunciada pelo tamanho em 10 de 24 questões.
  - **Continua rascunho:** `status: rascunho`, revisão humana pendente, mínimos de aprovação nulos. O conteúdo técnico das questões e rubricas **não foi validado por humano** (R29).
- **Correção de teste intermitente da S6 (commit `de3a55e`).** `test_r05_ponta_a_ponta…` falhava em ~6% das execuções: a sentinela `"888"` coincidia com o sha256 do `.7z` no manifesto. Reproduzido (falha na 7ª de 80 execuções); sentinelas trocadas por valores fora de `[0-9a-f]`; 0 falhas em 25 execuções.
- **Sondagens nos dados reais (orquestrador, sem abrir o teste):**
  - Qualidade (239 Parquets, 6 925 532 linhas): `saldo_movimentacao` só ±1; competências todas `AAAAMM`; **UF `99` em 2 264 linhas (0,03%)**; `grau_instrucao` 99 em 13 linhas.
  - Contagens as-of (movimentações ≤ 202512): **0 células** destino × UF × mês com acumulado negativo; 0 linhas com disponibilidade anterior à movimentação.
  - **Defasagem de declaração (R02), preliminar** (`.kaiser/reports/R02-sondagem-defasagem-for.txt`; só movimentações ≤ 202512): fração de admissões vinda de FOR por coorte, série principal: 2020 2,48% · 2021 1,31% · 2022 0,75% · 2023 0,49% · 2024 0,34% · 2025 0,32% (2025 é limite inferior: coorte ainda imatura). Nas coortes 202407–202506, fica por declarar depois do mês da movimentação 0,33% (máximo mensal 0,65%) na série principal e 0,51% (máximo 0,94%) na total; depois de 1 mês, 0,11% e 0,20%. **Abaixo do limite de 2% de D04b:** pelo pré-registro, os meses finais do teste não são cortados e o viés de subcontagem (< 1%) é declarado. Falta formalizar no notebook de EDA. A sondagem expôs o total anual de admissões de 2025 (período de validação), nenhum valor de 2026.

## Em andamento (13/11, 12h50)

- **S3 — outbox, rodada 2 no `agy`:** job `pwsh-300` (45 min), worktree `GS-wt/S3-outbox`, branch `fatia/S3-outbox` (base `de3a55e`). Rodada 1 (`pwsh-281`): 92 testes verdes e ruff limpo executados pelo orquestrador; **RED reproduzido** com o worker neutralizado (`'pendente_nuvem' == 'sincronizado'`, `.kaiser/reports/S3-red-reproduzido.txt`); diff lido na íntegra. Aceite adversarial: **3 de 11 falharam** (`.kaiser/reports/S3-aceite-adversarial-red.txt`): reenvio sem `medido_em` vira 409 quando o relógio avança (o caso T13 real); órfão do CSV reenviado responde 200 e não entra na fila; chave do dispositivo enviada por `http://` a host externo. Devolvidos também: `synchronous=NORMAL`, `{err}` em mensagens 503, `.dockerignore`, uv 0.5.29 no Dockerfile (lock é do 0.11.6), processo como root. Contratos `.kaiser/contratos/S3-outbox[-r2].md`. **Falta:** aceite da rodada 2, `docker compose --profile app build`, commit, revisão independente, merge.
- **S7b — painel, EDA e baselines, rodada 2 no `agy`:** job `pwsh-303` (45 min), worktree `GS-wt/S7b-eda-baselines`, branch `fatia/S7b-eda-baselines` (base `659ecbe`). Rodada 1 (`pwsh-292`): 78 testes verdes, ruff limpo. **Executado nos dados reais pelo orquestrador** (saídas em `.kaiser/tmp/s7b_real/`, descartáveis): painel em 78 s (11 178 linhas: treino 9 234, embargo 486, validação 1 458); **conferência independente direto dos Parquets: 0 divergências em 162 séries** (alvo consolidado da origem 202312 e admissões as-of de 202403); baselines dos 3 folds recalculados à parte com `n`, MAE e WAPE idênticos. Devolvido: métrica 0,0 com n = 0, fração de exclusões subestimada na EDA, rótulos e formatação do relatório (15 itens, `.kaiser/contratos/S7b-eda-baselines-r2.md`). **Falta:** aceite da rodada 2, commit, merge, rodar de novo nos dados reais e gravar a evidência em `05_ML/evidencias/`.
- **Resultados preliminares dos baselines (só treino, validação NÃO aberta; números do código da rodada 1, conferidos por recálculo independente):** folds com validação 202401–03, 202404–06 e 202407–09; séries elegíveis 113/114/114 de 162; MAE médio persistência 52,17 (desvio 9,63), sazonal 65,45 (desvio 13,98); WAPE médio 13,7% e 17,1%. O sazonal vence só no fold de jan–mar/2024. Origens de treino com todas as features: 202101–202409 (45 meses); 2020 fica sem lag 12 por construção.
- **S5 — contrato pronto, não disparado** (`.kaiser/contratos/S5-auth.md`): depende da S3 integrada (as duas editam `main.py` e `erros.py`). Schema `CT_S5_TESTE` criado no Oracle Docker com aprovação do usuário; a senha é uma fixture didática escrita no comando de criação e vai para o `agy` só por variável de ambiente.
- **Serviços de teste de pé** (Oracle, Postgres, Mongo *healthy* desde 11h10) à espera da S5.
## Bloqueios e pendências [HUMANO]

- [ ] **Repositório público:** `orugian/gs-semestre2` está **público** e contém nomes e RMs da equipe, e-mails nos metadados dos commits e o material do professor (`docs\material_por_cadeira\`, PDFs dos enunciados). Confirmar que é isso mesmo ou tornar privado.
- [ ] **Qual é o remoto oficial?** `origin` continua `insonia999/GS2_26` (D14b) e não recebeu push. Decidir se `gs-semestre2` substitui o `origin` ou se os dois recebem push.
- [ ] `MONGODB_URI` completa e IP liberado no Atlas.
- [ ] Senha correta do Oracle FIAP.
- [ ] Sessão do Learner Lab e porta 5432 do RDS antes do D4.
- [ ] Caminho da IA de sentimento (créditos HF ou Comprehend).
- [ ] AWS CLI (instalar ou usar o console).
- [ ] Ok para o snapshot da Adzuna (até 12 chamadas, com contador).
- [ ] **Revisão humana do catálogo até D3 (15/11) às 18h**, senão corte automático para 3 destinos (R29). Os 6 rascunhos estão em `app/catalogo/destinos/`; o roteiro de revisão (7 itens, inclusive definir `minimo_objetiva` e `minimo_llm`) está em `app/catalogo/README.md` §4.
- [ ] `gh auth refresh -s project,read:project`; ideia da live (AIC); quem grava cada vídeo.

**Disco:** 14,7 GB livres em 13/11 às 12h22 (15,6 GB às 11h08).

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
- **D2 (13/11), aprovado pelo usuário:** `POST /leituras` responde 201 para evento novo, **200 para reenvio idêntico e 409 para o mesmo `evento_id` com conteúdo diferente** (plano §3.2 atualizado; implementação na S3). Schema de teste `CT_S5_TESTE` no Oracle Docker. Encerramento do `agy` ocioso (PID 25872).
- **S7, escolhas do orquestrador:** disponibilidade conservadora `max(competencia_dec, competencia_arquivo)` para MOV/FOR e `max(dec, exc, arquivo)` para EXC; uma contagem do mês *m* vista em *t* só é número se MOV de *m* e FOR/EXC de *m..t* estiverem ingeridos (senão `NaN`, nunca zero); `construir_painel_features` bloqueia origens ≥ 202601 salvo `permitir_teste=True`; `SplitOrigemMovel` recusa embargo < 3 e treino > 202409.
- **S2, escolhas do orquestrador:** autenticação só por `X-Device-Key`; `status` aceita apenas `OK`/`ALERTA`/`ERRO` (vocabulário do firmware, plano §3.1), outro valor → 400; só o valor exato −127 em `temperatura_c` é falha de sensor; `relato` é validado (≤ 280) e descartado até a S14; rate limit técnico de 60/min por dispositivo; o CSV guarda `estado` fixo `pendente_nuvem` e o estado atual virá da outbox.
- **S5 (13/11), aprovado pelo usuário:** além de `POST /me/consentimentos`, a fatia entrega `GET /me/consentimentos` e `DELETE /me/consentimentos/{id}` (404 se não existe ou é de outra pessoa), para o T14 ser testável já na S5 (plano §3.2 atualizado).
- **S7b, escolhas do orquestrador:** linhas com UF `99` são descartadas e contadas no carregador (D04 fixa 27 UFs); o painel de desenvolvimento vai até a origem 202509 e lê movimentações até 202512 (rótulos da validação), nunca 2026; os dois baselines são avaliados no mesmo conjunto de linhas.
- **Catálogo:** 29 conceitos ESCO consultados na API oficial em 13/11 (versão da ESCO não fixada na consulta); a associação conceito → destino é curadoria inferida, não vínculo oficial.

## Não verificado

- Títulos oficiais da CBO no site do MTE (reCAPTCHA); o título de 211220 vem de fonte secundária.
- S2: POST vindo do Wokwi/ESP32 real; execução com mais de um processo `uvicorn`.
- S7: painel completo sobre os dados reais (só a pré-agregação foi executada: 55 s); desempenho de `construir_painel_features` nas ~69 origens.
- Catálogo: correção técnica de enunciados, gabaritos e rubricas (depende da revisão humana); versão da ESCO.
- Regressão web (`pnpm run test`) nesta sessão: não executada (nenhuma mudança em `app/web`).

## Próximo passo exato

1. **S3:** coletar `pwsh-300`; rodar `tests/test_s3_aceite.py` + regressão; `docker compose -f app\docker-compose.yml --profile app build api`; commit em `fatia/S3-outbox`; `git diff main..fatia/S3-outbox > .kaiser\tmp\S3-diff.patch`; revisão independente (`agy --mode plan`, 20 min); adjudicar; merge `--no-ff`; regressão em `main`.
2. **S7b:** coletar `pwsh-303`; regressão; rodar os 3 comandos nos dados reais; repetir `.kaiser\tmp\conferir_painel.py`; ler a EDA; commit, merge; copiar `eda_treino.md`, PNGs e `baselines.json` para `05_ML/evidencias/20261113-*`. **Decisão de D10 pendente do usuário:** excluir 2020 do treino? (dados da EDA: CV mensal 0,25 em 2020 contra 0,09–0,15 nos demais; FOR 2,5% contra 0,3–1,3%). Só depois disso rodar os baselines com `--validacao`.
3. **S5:** disparar o `agy` com `ORACLE_DSN=localhost:1521/FREEPDB1`, `ORACLE_USER=CT_S5_TESTE` e a senha de fixture, depois da S3 em `main`. Revisão independente obrigatória.
4. **Snapshot da Adzuna:** script com contador (máximo 12 chamadas), só depois do ok do usuário.
5. **Push:** `main` está à frente de `gs-semestre2/main`; não houve push nesta sessão (falta o ok).