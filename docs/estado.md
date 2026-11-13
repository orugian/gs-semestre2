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

## Em andamento

- **S3 — outbox:** job `pwsh-281` (`agy`, 45 min, disparado às 12h17), worktree `GS-wt/S3-outbox`, branch `fatia/S3-outbox` (base `de3a55e`). Contrato `.kaiser/contratos/S3-outbox.md`, relatório `.kaiser/reports/S3-outbox.md`. Falta: aceite, reprodução do RED (fatia de risco), revisão independente, merge.
- **Serviços de teste de pé** (Oracle, Postgres, Mongo *healthy* desde 11h10). Nenhuma fatia integrada os usou ainda; parar com `stop` se a S5 não começar nesta sessão.
- **S5 — preparada, não iniciada:** schema `CT_S5_TESTE` criado no Oracle Docker (`FREEPDB1`) com aprovação do usuário: credencial didática de fixture, quota de 50 MB, só `CREATE SESSION/TABLE/SEQUENCE`. Contrato ainda não escrito. Depende da S3 integrada (as duas mexem em `main.py` e `erros.py`).
- **EDA + baselines:** não iniciados. Contrato a escrever (`app/ml`, escopo disjunto da S3).
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
- **Catálogo:** 29 conceitos ESCO consultados na API oficial em 13/11 (versão da ESCO não fixada na consulta); a associação conceito → destino é curadoria inferida, não vínculo oficial.

## Não verificado

- Títulos oficiais da CBO no site do MTE (reCAPTCHA); o título de 211220 vem de fonte secundária.
- S2: POST vindo do Wokwi/ESP32 real; execução com mais de um processo `uvicorn`.
- S7: painel completo sobre os dados reais (só a pré-agregação foi executada: 55 s); desempenho de `construir_painel_features` nas ~69 origens.
- Catálogo: correção técnica de enunciados, gabaritos e rubricas (depende da revisão humana); versão da ESCO.
- Regressão web (`pnpm run test`) nesta sessão: não executada (nenhuma mudança em `app/web`).

## Próximo passo exato

1. **S3:** coletar `pwsh-281`; aceite (§7.5) com reprodução do RED; commit em `fatia/S3-outbox`; revisão independente (`agy --mode plan`, patch em `.kaiser\tmp\S3-diff.patch`); merge.
2. **EDA + baselines (caminho crítico):** escrever o contrato e disparar o `agy` em paralelo com a S3 (escopo `app/ml` + `05_ML`). Entradas já medidas: defasagem de FOR abaixo de 2%; **UF `99` (2 264 linhas, 0,03%) faz `pre_agregar_microdados` lançar erro**: o carregador real descarta essas linhas e reporta a contagem (consequência de D04, que fixa 27 UFs; escolha do orquestrador, informada ao usuário). Decidir na EDA a exclusão de 2020 (D10) antes de olhar a validação.
3. **S5 (auth):** contrato depois da S3 integrada; Oracle Docker com o schema `CT_S5_TESTE`.
4. **Snapshot da Adzuna:** script com contador (máximo 12 chamadas), só depois do ok do usuário.
5. **Push:** `main` está 12 commits à frente (contando este registro) de `gs-semestre2/main`; não houve push nesta sessão (falta o ok).