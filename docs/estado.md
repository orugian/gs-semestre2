# Estado do desenvolvimento

> Arquivo vivo, mantido pelo orquestrador (CLAUDE.md §5). É o primeiro arquivo lido em cada sessão: seja curto e factual.

**Atualizado em:** 15/11/2026, 20h36 (UTC−3) · **Dias até o prazo (19/11 23h55):** 4,14 · **Fase:** retomada ativa; S5 devolvida para correções do aceite, RED independente reproduzido; R29 técnico em implementação e modelos ML/RNA/Estatística pendentes. Caminho crítico atrasado > meio dia, usuário avisado.

**Ponto corrente:** `main` em `112042d` antes do registro da retomada; worktrees `../GS-wt/S5-auth` (base `04c7f94`, implementação não commitada preservada), `../GS-wt/S7-recorte` (base `112042d`, implementação parcial) e `../GS-wt/S5-red` (descartável, main + esqueleto do RED). Dois `agy` de retomada ativos, listados abaixo; objetivo automático ativo. Handoff anterior: `%TEMP%\handoff_citizentech_20261115.md`.

**Escopo vigente (D02/D16/R29):** prazo de 15/11 às 18h ultrapassado, sem revisão humana registrada nos YAMLs nem nesta conversa. Acionado o corte automático para **Dados/BI, Monitoramento/IoT e Processos**. Os seis rascunhos e o painel de seis destinos estão preservados; a aplicação do recorte no produto/execuções futuras ainda está pendente. Não equivale à aprovação das três rubricas.

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

- **S3 — outbox durável e `POST /leituras` idempotente, em `main` (merge `04c7f94`).** `agy` em 2 rodadas + ajustes do orquestrador.
  - Evidência: em `app/api`, `uv run pytest -q -rs` → 109 passed, 0 pulados; ruff limpo (em `main`, depois do merge).
  - **Sensibilidade do teste reproduzida por mutação**, com o worker neutralizado: `'pendente_nuvem' == 'sincronizado'` falha por asserção (`.kaiser/reports/S3-red-reproduzido.txt`). Isso **não** é reprodução literal de testes novos sobre base + esqueleto (§7.5), nem prova retroativa da sequência autoral TDD. Diff lido na íntegra.
  - Aceite adversarial (11 contraexemplos): 3 falharam na rodada 1 — reenvio sem `medido_em` virava 409 quando o relógio avançava (o caso T13 real; o teste do autor passava por cair no mesmo segundo); órfão do CSV reenviado respondia 200 sem entrar na fila; chave do dispositivo saía por `http://` para host externo. Corrigidos na rodada 2, junto com `synchronous=FULL`, mensagens 503 sem texto de exceção, `.dockerignore`, uv 0.11.6 e usuário não-root na imagem.
  - **Revisão independente** (`agy --mode plan`, `.kaiser/reports/S3-outbox-rev.md`, sobre o commit `09e2f0d`), adjudicação: **RV-S3-01 aceito** (ack sem `id` remoto marcava `sincronizado`; agora exige `evento_id` igual e `id` não vazio); **RV-S3-02 aceito** (CSV com caminho explícito e outbox em outra pasta; a outbox agora acompanha o CSV); **RV-S3-03 aceito** (backoff contava do início do lote; agora do momento da falha); **RV-S3-04 aceito** (modo isolado não reconciliava órfãos ao subir; ganhou `lifespan` sem worker); **RV-S3-05 aceito em parte** (413 e 422 viram `erro_permanente`; 404/405 continuam na fila porque indicam URL mal configurada, corrigível); **RV-S3-06/07/08 aceitos como limitação**, documentados no README (processo único obrigatório, sem keep-alive, contexto de build em `app/`). Cada correção com RED por asserção (`.kaiser/reports/S3-revisao-red.txt`). As correções pós-revisão (commit `1f837ef`) **não passaram por nova revisão independente**.
  - **Imagem Docker construída e exercitada pelo orquestrador:** `docker build -f app\api\Dockerfile app` → 376 MB; contêiner com volume nomeado temporário: `/health` 200, POST novo 201, reenvio 2 s depois 200 com o mesmo `medido_em`, conteúdo diferente 409, processo como usuário `citizentech`, CSV + `outbox.db` no volume, estado preservado depois de `docker restart`; contêiner e volume temporários removidos. A imagem `citizentech-api:s3` ficou no Docker.
  - **Achado do orquestrador:** os testes da rodada 1 gravaram um `outbox.db` com 77 eventos de teste em `.dados\runtime\` (o `agy` roda com `CITIZENTECH_DADOS` real). Adicionada a fixture autouse `ambiente_isolado` em `app/api/tests/conftest.py`; verificado com diretório-sentinela que a suíte não cria mais nada fora de `tmp`. **O arquivo antigo continua lá** (apagar exige aprovação; ver pendências).
- **S7b — painel de desenvolvimento, EDA do treino e baselines, em `main` (merge `464fa4c`).** `agy` em 2 rodadas + ajustes do orquestrador. Sem revisão independente (não é fatia de risco na lista do plano).
  - Evidência: em `app/ml`, `uv run pytest -q` → 86 passed; ruff limpo (em `main`).
  - **Executado nos dados reais a partir de `main`:** `python -m citizentech_ml.painel` → `.dados\caged\painel\painel_desenvolvimento.parquet` (11 178 linhas: treino 9 234, embargo 486, validação 1 458; sha256 `8e653b00…b4eb9e`, idêntico entre execuções). **Conferência independente direto dos Parquets:** alvo consolidado da origem 202312 e admissões as-of de 202403 com 0 divergências em 162 séries; `n`, MAE e WAPE dos 3 folds iguais ao recálculo à parte.
  - **Baselines, só treino (validação e teste NÃO avaliados):** 3 folds de origem móvel (avaliação em 202401–03, 202404–06, 202407–09; 113/114/114 séries elegíveis de 162). Persistência trimestral: MAE médio 52,17 (desvio 9,63), WAPE 13,71%. Sazonal: MAE 65,45 (desvio 13,98), WAPE 17,09%. O sazonal vence só no fold de jan–mar/2024 (49,63 contra 63,08).
  - **EDA do treino** (`05_ML/evidencias/20261113-eda-treino.md` + 2 PNG): 115 de 162 séries passam na densidade (D04a) e cobrem 99,61% das admissões do treino; IoT tem 14 UFs elegíveis e Projetos/Produto 13; índice sazonal do agregado: pico em agosto (1,11), vale em dezembro (0,82); 45 origens de treino com todas as features (202101–202409); defasagem de declaração e FOR abaixo de 2% a partir de 2021 (2020: 2,48% de FOR na série principal).
  - Devolvido na rodada 1: MAE 0,0 fabricado quando n = 0; fração de exclusões subestimada; rótulos e formatação. Corrigido pelo orquestrador depois da rodada 2: a tabela da série total comparava o consolidado com o as-of da série principal (mostrava 75–90% de diferença; o correto é 0,5–3%).
  - Evidências versionadas em `05_ML/evidencias/20261113-*` (EDA, PNGs, `baselines-treino.json` e `.txt` com comandos e conferência).

## Retomada — sessão iniciada em 15/11 às 19h01 (continuação às 20h13)

**Foto corrente às20h31:**
- S5 commitada em `fatia/S5-auth`, `1e409a5`, após aceite próprio: suite completaOracle **204 passed,0skip,101,57s**, rufflimpo. RED independente já reproduzido e rascunhoadversarial corrigido. **Revisão independente agy em execução `pwsh-26`**; patch3pontos e contrato `../.kaiser/contratos/S5-auth-rev.md`, sem relatórioautoral. Não integrada ainda.
- **Runner Oracle `pwsh-18` continua ativo**, aguardando sinais sem segredo em `../.kaiser/tmp/S5-oracle-canal-651E903F48/`: novo schema autorizado `CT_S5_TESTE_651E903F48`, senha apenasemmemória. Para repetir worktree criar `worktree-<id>.signal`; após merge criar `main-<id>.signal`; terminar com `encerrar-<id>.signal`. Timeout30min após últimaespera; não matar/encerrar antes da regressão se ainda útil. Nenhuma exclusão de schema/dados autorizada.
- S7-recorte revisada pelo agy `pwsh-21` (coletado saída0), contrato `../.kaiser/contratos/S7-recorte-rev.md`, sobre `ac8230f`. Adjudicação: **RV-R29-01 aceito/corrigido** (return duplicado); **02 aceito como limitação operacional**, documentado (rejeição2026 pós-leitura NÃO é barreiraI/O; usar somente painelDEVsegregado); **03 aceito/corrigido** (baselines agora recusa sobrescrita); **04 aceito/corrigido** (modo catalogo_parcial quando menosde6destinos). RED próprio2failed, GREEN/regressão própria `pwsh-28` **110passed/rufflimpo**. Correções <30linhasfonte commitadas `b45b092` após gitleaks, não receberam segunda revisão. Recorte ainda não integrado. Limitação histórica: RED inicial da projeção não preservado; REDs das validações/CLI e manifestos registrados.
- PainelDEV identificado sem reconstruir microdados: sha256 `8e653b0047ceed204d25bf7c0d9d28c8d7944bd4e75c7f65bf4ea09651b4eb9e`, metadadosorigens202001–202509,11178linhas. Nenhum arquivo de holdout lido. Pronto para projeção/validação após mergeR29.
- Gitleaks no commitS5 identificou falso positivo na string de teste JWTcurto (não era credencial). Fixture passou a `"x" * 31`, reforçando teste do limite32; teste próprio1passed e nova varreduralimpa. Não foi criadaexceção nem enfraquecidodetector.
- `main` em `4f6e87e` antes deste novo registro, sem push; evidência parcialS5 versionada em `02_Cybersecurity/evidencias/20261115_s5_aceite_parcial.txt`. ContratosClássicos/Estatísticapreparados,NÃOiniciados. Nenhum modelo realnovo/holdoutaberto.

- Após interrupção externa, `job_list` vazio e `job_output` dos antigos `pwsh-16`/`pwsh-23` retornou unknown job. Nenhum `agy` ativo confirmado. Relatório recorte parcial (aguardava tarefa filha), relatório S5-r2 vazio; mudanças preservadas. Não atribuir saída0 nem conclusão a esses jobs perdidos.
- **Retentativas únicas em execução nesta continuação:** recorte `pwsh-5`, S5-r2 `pwsh-6`, contratos/relatórios com sufixo `-retomada`. Orientados a comandos síncronos, sem tarefas filhas pendentes. Dois slots agy ocupados, escopos disjuntos. Objetivo rearmado revisão2.
- Às20h13 Docker daemon indisponível (named pipe ausente), não é falha da aplicação. **Usuário autorizou nesta continuação criar novo schema local exclusivo de teste**, senha gerada somente em memória, sem mudar CT_S5_TESTE nem apagar dados. `pwsh-10` coletado: Docker Desktop iniciado, Oracle iniciado; smoke OSDBA `select status from v$instance` →OPEN, healthy. Runner de infraestrutura preparado em `../.kaiser/tmp/S5-oracle-sessao-20261115.ps1` (ainda não executado), mantém conexão em memória para worktree e futura regressão main via sinais sem segredo. Disco24,8GB.
- `pwsh-5` de retomada concluído/coletado saída0; relatório recorte disponível. Aceite próprio `pwsh-13` →109 passed/rufflimpo. Achado próprio: manifesto sem --escopo-mvp listava6destinos mesmo em arquivo com2; RED por asserção executado e correção local de poucas linhas aplicada; regressão pós-correção `pwsh-16` desta continuação em execução. Recorte ainda não commitado/integrado.
- Contratos seguintes preparados, **NÃO iniciados**: `../.kaiser/contratos/S7-classicos.md` (Ridge/RF/HGB, tuningtemporal e densidadeporfold) e `../.kaiser/contratos/S7-estatistica.md` (funções inferenciais/regressões somentefixtures). Dependem das dependências commitadas do recorte. Nenhum modelo real treinado nesta sessão; Estatística real aguarda resolver denominador municipal e congelar população/ano antes de análise.

### Histórico da primeira etapa — jobs antigos superados

- Ritual executado: `main` limpo em `112042d`, worktree S5 preservado, nenhum `agy` herdado; Docker 29.6.2/Oracle healthy; disco 25,3 GB, prazo 4,20 dias.
- O objetivo antigo não foi localizado por `get_goal` (retornou null); continuidade recriada como `goal-b26c0ecc-56d3-46a1-9ddc-bb5fb7873872`, ativo, com as restrições do usuário.
- **S7-recorte via agy em execução: job `pwsh-16`**, worktree `../GS-wt/S7-recorte`, contrato `../.kaiser/contratos/S7-recorte.md`. Escopo: manifesto R29, projeção do painel de desenvolvimento, baselines explícitos202101 e dependências sklearn/scipy/statsmodels. Somente fixtures; sem acesso a `.dados`, sem torch nesta fatia.
- **Gate Oracle S5:** variáveis de conexão não herdadas, fixture segura ainda indisponível; não ler `.env` nem mudar credenciais. Usuário pediu explicação e recebeu; testes Oracle atuais ainda não executados.
- **S5 aceite nesta retomada:** rascunho corrigido e copiado para `tests/test_s5_aceite.py` (limite por e-mail sem login de preparação; JWT adulterado a partir de token válido). `pwsh-20` coletado: 7 passed,16 deselected nos casos sem Oracle; ruff limpo. RED original reproduzido independentemente sobre `main` + rota501 em worktree `../GS-wt/S5-red`: `pwsh-19` saída1 por **assert501==201**, evidência `../.kaiser/reports/S5-red-independente-20261115.txt`.
- **Falhas novas confirmadas:** `tests/test_s5_validacao_sem_banco.py`, `pwsh-21` coletado →6 failed,5 passed (aceita ausênciaiat/jti; exp malformado causaTypeError; senha5000 no login responde503 antes de validação400). Não são testes Oracle nem avaliação do holdout. **Devolvido ao agy, rodada2 `pwsh-23` em execução**, contrato `../.kaiser/contratos/S5-auth-r2.md`, mesmo worktree preservado. Adendo autoriza substituir a prova de isolamento por subprocesso novo (sem remover drivers de sys.modules), config fail-closed e limpeza de entradas expiradas do limitador, sem apagar dados. Máximo2 agy respeitado com `pwsh-16`.
- Exploração somente leitura identificou riscos para confirmar: carregador do painel abre Parquets antes de filtrar2026 (não reconstruir painel real); D11 ainda seis destinos e denominador municipal total não disponível no parquet filtrado. Manter população D11 até decisão explícita; nunca substituir denominador por total do recorte. O catálogo contém estatística2026 em texto legado, vista incidentalmente pelo explorador, não usada nem reproduzida; nenhum arquivo de holdout foi aberto.

## Foto histórica do handoff às 18h50 — superada pela retomada acima

- **S5 — auth e consentimentos: implementação concluída pelo `agy`, aceite incompleto.** `pwsh-324` terminou com saída 0; não está rodando. Worktree `../GS-wt/S5-auth`, branch `fatia/S5-auth`, base `04c7f94`; código e testes novos **não commitados**, nenhum merge. Contrato `../.kaiser/contratos/S5-auth.md`, relatório `../.kaiser/reports/S5-auth.md`; snapshots de base e escopo em `../.kaiser/snapshots/S5-auth-{base,depois}.txt`.
  - **Executado pelo orquestrador em 15/11 (`pwsh-6`, já coletado):** em `app/api` do worktree, `uv run pytest -q -rs -p no:warnings` com Oracle de teste configurado → saída 0, nenhum skip listado, ~99 s; sequência de 143 testes verdes compatível com a contagem do autorrelato. `uv run ruff check . -q` → saída 0. Sem variáveis Oracle → saída 0, **12 testes pulados** por banco não configurado; isso não substitui integração real. Evidência consolidada em `../.kaiser/reports/S5-aceite-orquestrador-20261115.md`.
  - **RED:** autorrelato mostra `501 == 201` em `test_ciclo_completo_registro_login_me`; reprodução independente exigida por §7.5 **não executada**. A leitura integral do diff e a revisão independente `agy --mode plan` também não foram concluídas.
  - **Contraexemplos apenas redigidos, NÃO executados:** `../.kaiser/tmp/test_s5_aceite.py`, preservado também em `../.kaiser/snapshots/S5-test_s5_aceite-rascunho.py`. Ainda não copiado para os testes do worktree. Revisar o próprio rascunho antes de usá-lo: o caso de limite por e-mail já consome uma tentativa ao criar a conta; os JWTs forjados omitem `jti`, podendo falhar por claim ausente em vez do motivo alegado. Nenhum desses casos é falha reproduzida.
  - **Pontos de atenção lidos, sem correção/reprodução:** login não aplica o limite de senha antes da verificação Argon2; fixture `_proteger_modo_isolado` remove drivers de `sys.modules`, enfraquecendo a prova de isolamento (preferir processo novo); revisar limites/configuração de expiração, crescimento do limitador e autorização/CSRF. Não mudar o contrato público por inferência.
- **Serviços verificados às 18h50:** Docker 29.6.2 ativo; só Oracle `healthy` (1521, PDB `FREEPDB1`), Postgres e Mongo não aparecem como ativos. Schema dedicado `CT_S5_TESTE`, fixture local já autorizada, segredo não reproduzido nos documentos. Não alterar credenciais/permissões para retomar.
- **Jobs/higiene:** `pwsh-2` e `pwsh-6` concluídos/coletados; nenhum processo `agy` encontrado. Preservar o worktree S5 e os temporários relevantes ao aceite. Brutos Caged vazios. Nenhum arquivo de implementação alterado durante o fechamento documental.
## Bloqueios e pendências [HUMANO]

- [ ] **Repositório público:** `orugian/gs-semestre2` está **público** e contém nomes e RMs da equipe, e-mails nos metadados dos commits e o material do professor (`docs\material_por_cadeira\`, PDFs dos enunciados). Confirmar que é isso mesmo ou tornar privado.
- [ ] **Qual é o remoto oficial?** `origin` continua `insonia999/GS2_26` (D14b) e não recebeu push. Decidir se `gs-semestre2` substitui o `origin` ou se os dois recebem push.
- [ ] `MONGODB_URI` completa e IP liberado no Atlas.
- [ ] Senha correta do Oracle FIAP.
- [ ] Sessão do Learner Lab e porta 5432 do RDS antes do D4.
- [ ] Caminho da IA de sentimento (créditos HF ou Comprehend).
- [ ] AWS CLI (instalar ou usar o console).
- [ ] Ok para o snapshot da Adzuna (até 12 chamadas, com contador).
- [x] **D10, aprovado pelo usuário em 15/11:** treino com origens desde **202101**, preservando 2020 apenas como histórico de lags (45 origens até 202409, sem imputar 2020 para incluí-lo no treino). EDA: CV 0,251 e FOR 2,48% em 2020, além de ausência de lag de 12 meses. **Execução dos baselines e modelos com essa escolha ainda pendente**; split, embargo, densidade e promoção inalterados.
- [ ] **Apagar `.dados\runtime\outbox.db*`?** São 77 eventos de teste gravados por engano (ver S3). Enquanto existirem, subir a API com `CITIZENTECH_DADOS` real e `FUNCTION_URL` configurada enviaria esses eventos à Lambda.
- [ ] **Revisão humana das três rubricas mantidas após o corte R29:** Dados/BI, Monitoramento/IoT e Processos. Às 18h50 de 15/11, os seis YAMLs ainda eram rascunhos com revisor e mínimos nulos; nenhuma revisão humana foi registrada. Roteiro em `app/catalogo/README.md` §4. Os demais rascunhos estão preservados, não aprovados.
- [ ] `gh auth refresh -s project,read:project`; ideia da live (AIC); quem grava cada vídeo.

**Disco:** 25,3 GB livres em 15/11 às 18h50; a recuperação desde os 8,6 GB de 13/11 ocorreu fora do trabalho aqui registrado, causa não verificada. **Abaixo de 6 GB, avisar; abaixo de 4 GB, parar.**

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
- S2/S3: POST vindo do Wokwi/ESP32 real; worker contra a Lambda e o RDS reais (só fake na fronteira); `docker compose --profile app up` com o `app/.env` real (o smoke usou `docker run` com chave descartável).
- S7b: baselines com `--inicio-treino 202101` e métricas de validação ainda não executados; decisão do usuário já registrada. **Não fazer EDA da validação nem abrir o holdout.** Resultados de 13/11 descrevem os seis destinos e a configuração anterior; não relabelar como resultado do recorte novo.
- Catálogo: correção técnica de enunciados, gabaritos e rubricas (depende da revisão humana); versão da ESCO.
- Regressão web (`pnpm run test`) nesta sessão: não executada (nenhuma mudança em `app/web`).
## Próximo passo exato

1. **Revisões em execução:** coletar `pwsh-21` (R29) e `pwsh-26` (S5), adjudicar cada achado com execução própria. `pwsh-18` é o runner Oracle aguardando sinal, não confundir com agy. Objetivo está ativo; após eventual nova interrupção, só rearmar com pedido humano de continuidade.
2. **S5:** após adjudicar a revisão independente, corrigir achados bloqueadores com RED/GREEN, commitar com gitleaks, integrar `--no-ff` e sinalizar regressão em main ao runner Oracle ainda ativo. Não substituir integração real por skips/fakes. Preservar trabalho/schema/dados; não remover worktree enquanto não integrado. Registrar limites e eventual necessidade de nova revisão das correções.
3. **Caminho crítico ML/RNA/Estatística:** integrar recorte após revisão/regressão; somente então criar worktrees dos contratosClássicos/Estatística, máximo2agy. Aplicar recorte ao painel de DESENVOLVIMENTO existente em saídaNOVA, sem reconstruir microdados. Baselines com `--escopo-mvp --inicio-treino 202101 --validacao`; registrar população/hashes e preservar evidências anteriores. RNA vem em seguida com PyTorchCPU/≥2configs. Estatística real continua com seisdestinosD11 e denominador municipalpendente; fixtures não são entrega acadêmica. Não fazer EDA2025 nem abrir holdout.
4. **Cronograma restante:** consultar o plano §5 literalmente: D3 prevê **S9/S10/S11**, ML (Ridge/RF/HGB + tuning), RNA (MLP ≥ 2 configs) e Estatística; D4 prevê **S4**, firmware e **S8/S12/S13**. Priorizar o caminho crítico atrasado e dependências, não apresentar todas essas fatias como iniciadas. Não abrir holdout nesta retomada antes de concluir critérios e candidatos.
5. **Dependências humanas:** revisão das três rubricas, credenciais/infra e vídeos; apagar o outbox contaminado e snapshot Adzuna só com aprovação específica.
6. **Push:** não autorizado neste fechamento. Antes do commit documental, `main` tinha 19 commits a mais que a referência local `gs-semestre2/main`; referência não consultada remotamente. Não houve push nesta sessão.
