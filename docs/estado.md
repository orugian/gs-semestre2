# Estado do desenvolvimento — CitizenTech

> Primeiro arquivo da próxima sessão. Snapshot documental de **16/11/2026 ~17h05 (UTC−3)**, não monitoramento ao vivo. Prazo **19/11/2026 às 23h55** (~3,3 dias). Histórico detalhado: `git show 18e7a14:docs/estado.md` (até 16/11 16h), `git show 27a06a4:docs/estado.md`, `git show d2ddec4:docs/estado.md`; trilha de agentes em `../.kaiser/{contratos,reports}/`.

## 0. Sessão de 16/11 noite (camada mais recente; prevalece sobre §1–§4 onde conflitar)

**Integrado em `main` e enviado a `gs-semestre2` (`2a0049e`, gitleaks limpo no intervalo):**
- **S15b telas web** (`47a9d4c`): aba "Minha transição" com Entrar/Criar conta, Consentimentos, Currículo (colar/enviar → texto redigido editável → confirmar → só então "Sugerir competências") e Competências (confirmar/rejeitar/não possuo). Correções do orquestrador: editar depois de confirmar esconde "Sugerir" até reconfirmar (RED reproduzido: `expected <button> to be null`), textos sem prometer ocultação total, Astryx em pt-BR (`InternationalizationProvider`). `pnpm run test` 40 passed, build ok. **Smoke real no Edge** (playwright-core em `../.kaiser/tmp/smoke/smoke_s15b.mjs`, cookies Secure em localhost funcionam): registrar 201 → login 200 → 2 consentimentos 201 → experiências 201 sem e-mail/telefone → confirmar 200 → extrair 503 (API sem chave LLM; mensagem correta) → logout 204. **Tela de competências não vista no navegador** (precisa da LLM real).
- **S11b rotas** (`b6fa38d`): `PUT/GET /me/intencao`, `GET /destinos` (whitelist, sem exercício), `POST /me/comparacoes` (≤3, sem score, mercado repassado do snapshot), `GET /me/comparacoes/{id}`; DDL `app/db/ddl/003_intencao_comparacao.sql`. `app/api` **342 passed, 0 skip**, ruff limpo (rodado pelo orquestrador no worktree e em `main`). Contraexemplos na API real (porta 8002): fora do escopo/4 destinos/UF inválida/campo extra → 400; sem `perfil` → 403; outro usuário → 404; GET = POST; `ultimo_observado` SP = `/mercado` (processos 645,0; dados/BI 1994,0 em 202509). Gitleaks pegou falso positivo (`texto_secreto` em teste) **depois** do commit local por erro do orquestrador (encadeou o commit); corrigido renomeando e refazendo o merge local antes do push (`reset --keep` em histórico não enviado).
- **06_Cloud/README.md** completo com evidências reais; prints novos tarjados `20261116_function_url.png`, `20261116_rds_conectividade.png`, `20261116_rds_security_group.png` (originais copiados para `../.dados/cloud/privado/20261116_*_original.png`, SHA conferido; os 3 originais com e-mail seguem em `06_Cloud/evidencias/` excluídos via `.git/info/exclude` — o usuário pode apagá-los). Console mostra a variável `RATE_KIMIT_POR_MINUTO` (erro de digitação; efeito nulo, padrão 30).
- **02_Cybersecurity/relatorio.md + .pdf (11 páginas)** com demonstração executada `app/tools/demo_protecoes.py` → `evidencias/20261116_demo_protecoes.txt` (16 verificações, 0 falhas; Argon2id m=65536,t=3,p=4 conferido no Oracle; PII fictícia 0 vezes no log).
- **04_CTP_Python/documento.md + .pdf (8 páginas)** com `app/tools/demo_leituras_ctp.py` → `evidencias/20261116_demo_ctp.txt` e `20261116_historico_leituras.csv` (3 cenários normal/atenção/crítico, 200 reenvio, 409, 400, 401; indicadores temp média 37,0 e dist 14,0); 108 testes de leituras/outbox passaram.

**Em andamento (processos destacados, ver `../.kaiser/tmp/lancar_<fatia>.log`):**
- **S13-avaliacao** (agy PID 11120, 17h00, worktree `../GS-wt/S13-avaliacao`, contrato `../.kaiser/contratos/S13-avaliacao.md`, DDL reservado `004_avaliacao.sql`; integra `resultados_exercicio_para_comparacao` em `comparacao/servico.py`). Fatia de risco: no aceite, **reproduzir RED** em worktree temporário e **revisão independente** `agy --mode plan`.
- **S15c-comparacao** (agy PID 29064, 17h02, worktree `../GS-wt/S15c-comparacao`): telas de Intenção e Comparação; etapas passam a 5. Aceite: testes + smoke Edge com `smoke_s15b.mjs` estendido.
- API de teste do orquestrador ainda de pé na porta 8000 (código de `main` antes da S11b; wrapper PID 26924). Reiniciar com `subir_api_teste.ps1` para smokes novos.

**Bloqueio / decisão pendente do usuário:** S12 (plano) precisa de fonte para "atividades por pré-requisito": o catálogo não tem grafo de pré-requisitos nem atividades. Pergunta enviada ao usuário em 16/11 ~17h05.

**Decisões locais desta sessão:** consentimento `curriculo_llm` também cobre o envio da resposta aberta do exercício à LLM (S13), com redação de PII antes; comparação sem UF e sem intenção devolve mercado `uf_nao_informada`; DDL numerado por fatia (003 S11b, 004 S13, 005 livre para S12/S14).

**Fatos de ambiente novos** (também em CLAUDE §14.3): `run_in_background` do harness não executa — usar `Start-Process` com `../.kaiser/ferramentas/lancar_agy.ps1`; `env_teste.ps1`; `subir_api_teste.ps1`; capturar saída Python com `[Console]::OutputEncoding=UTF8`.

**Próximo passo exato:** aceitar S15c e S13 (com RED reproduzido e revisão independente) → S12 conforme a resposta do usuário → S14 laboratório → S15 E2E (Playwright com Edge `channel: 'msedge'` + axe, persona demo) → Data Science (DDL 001–004 + consultas no Oracle local + coleções Mongo) → firmware Wokwi + AICSS → roteiros → revisão de conformidade → empacotador (incluir cópias de `app/cloud` em `06_Cloud/codigo/` e de leituras em `04_CTP_Python/codigo/`) e PDFs.

## 1. Ponto de parada

**`main` = este commit documental sobre `d9a544b`, enviado a `gs-semestre2` (gitleaks limpo no intervalo).** `origin` (insonia999) não recebe push.

**Regressão em `main` executada pelo orquestrador às ~15h55:** `app/api` **329 passed, 0 skip** (Oracle `CT_TESTE_S9` + Mongo local) · `app/cloud` **115 passed** (Postgres 5433) · `app/tools` **41 passed** · `app/web` **18 passed** · ruff limpo em api/cloud/tools. `app/ml` 274 passed (16/11 manhã, não rerodado à tarde: nada de ML mudou desde então).

| Bloco | Situação | Evidência / limite |
|---|---|---|
| S0–S3, S5, S6, S7, S8, E05, E08, S15a | integrados (sessões anteriores) | ver git e `05_ML/`, `08_Estatistica/` |
| **E09 empacotador** | integrado | `05_ML/notebook.ipynb`, `07_RedesNeurais/notebook.ipynb`, `08_Estatistica/{analise.py,base_municipal.csv,requirements.txt,relatorio.pdf}`, `05_ML/slides.pdf` são cópias geradas; `docs/entregas_manifesto.json`. PDFs ainda com `[HUMANO — preencher]`. **Reexecutar no fim** (`uv run python empacotar_entregas.py --dados ..\..\..\.dados`, depois `--verificar`). |
| **S8b model cards + Adzuna** | integrado | Atlas `model_cards` 6 docs; Adzuna `../.dados/adzuna/20261116/` (6 chamadas, contador **7/12**); `/mercado` mostra "amostra pontual Adzuna de 16/11/2026" com `CITIZENTECH_ADZUNA_SNAPSHOT`. |
| **S9 currículo/PII** | integrado (backend) | RED reproduzido; revisão independente 9 achados (8 corrigidos, 1 risco documentado). `POST /me/experiencias`, `POST /me/curriculo`, `GET /me/curriculo/{id}`, `POST /me/curriculo/confirmar-envio`. **Sem tela.** |
| **S10 extração LLM** | integrado (backend) | `POST /me/competencias/extrair`, `GET /me/competencias`, `PATCH /me/competencias/{id}`; DDL `app/db/ddl/002_competencias.sql`. Smoke real OpenRouter ok (modelo padrão, 7 candidatas). **Sem tela.** Revisão independente não feita (não obrigatória). |
| **S11 comparação** | **só domínio** | `citizentech.comparacao.dominio.comparar_destinos`; integração com S10 via `competencias_para_comparacao`. **Falta rota `POST /me/comparacoes` e tela.** |
| **S4 Lambda/RDS** | **integrado e verificado na AWS real** | Evidências `06_Cloud/evidencias/`: `20261116_e2e_function_url.txt`, `20261116_consulta_rds.txt`, `20261116_cloudwatch_3.png`, `20261116_lambda_variaveis_ambiente.png` (segredos tarjados). **Faltam prints CloudWatch 1 e 2** (perdidos por erro do orquestrador ao mover; ver §6). Sentimento: Comprehend **AccessDenied** na LabRole → `analise_status=indisponivel` (fallback exigido funcionando). |
| **E01 firmware Wokwi** | integrado (código) | `app/iot/firmware/` (lógica testada no host com g++; `limiares.h` gerado). **Não compilado para ESP32, não simulado no Wokwi.** |
| S12 plano · S13 avaliação · S14 laboratório | **não iniciados** | contratos a escrever |
| Telas web: login, intenção, currículo, competências, comparação, plano, exercício, laboratório | **não iniciadas** | só existem Mercado + Painel técnico |
| S15 jornada E2E (Playwright + axe) | não iniciada | |
| Relatórios: Cyber, CTP, Data Science, AICSS, Cloud README, AIC, roteiros de vídeo | **não iniciados** (modelos com TODO) | ver §4 |

## 2. Resultados científicos (inalterados; não misturar coortes)

**ML/RNA (R29):** 3 destinos × UF, superior+; validação 202501–202509; MAE persistência 35,45253 · sazonal 33,59596 · Ridge 34,25765 · RF 35,63387 · HGB 39,73936 · MLP A 31,65446. **Nenhum modelo promovido**; holdout 2026 fechado. [Evidência](<../05_ML/evidencias/20261115_modelos_mvp_aceite.md>).
**D11:** Z p 0,324 e 0,659 (não rejeitam H0); OLS R² 3,6×10⁻⁷ e 0,0215; logística 54,35%. [Relatório](<../08_Estatistica/relatorio.md>).

## 3. Ativos e operação

- Dados: painel MVP `../.dados/caged/painel/r29_20261115_2041/`, artefatos `../.dados/artefatos/{classicos,rna}/20261115_r29_aceite/`, snapshot mercado `../.dados/mercado/20261116_r29_aceite/` (SHA `9c093f93…`), base D11 `../.dados/estatistica/20261115_d11_aceite/`, Adzuna `../.dados/adzuna/20261116/`, Cloud `../.dados/cloud/` (zip da Lambda `funcao_lambda_20261116.zip` SHA `f1828467…e954`, `rds-global-bundle.pem`, `segredo_app_ingest.txt`, `privado/` com prints originais **com segredos — nunca versionar**).
- **Não** subir a API com `FUNCTION_URL` + `CITIZENTECH_DADOS` real (`../.dados/runtime/outbox.db*` tem 77 eventos antigos; preservar).
- Docker: Oracle, Mongo e Postgres de teste **de pé** (volumes preservados). Caiu uma vez em 16/11; reiniciar com `Start-Process 'C:\Program Files\Docker\Docker\Docker Desktop.exe'` e `docker compose -f app\docker-compose.yml --profile teste up -d --wait`.
- Credenciais: só em `app/.env`, ler por script que não imprime valores. Para testes Oracle exportar `ORACLE_USER/PASSWORD` = `ORACLE_TESTE_*`; Mongo de teste `mongodb://citizentech_teste:<MONGO_TESTE_PASSWORD>@localhost:27018/?authSource=admin` com `MONGODB_DB` contendo `teste`.
- AWS (Learner Lab): Lambda `CP-2` (log group `/aws/lambda/CP-2`), RDS instância `cp1-cloud`, banco `citizentech`, usuário `app_ingest`, SG 5432 aberto (D09, manter até a correção). Se o lab expirar, `/health` mostra banco indisponível → pedir ao usuário para reiniciar o lab.
- Gastos: OpenRouter **US$ 0,0168 de 7** (consultar `GET https://openrouter.ai/api/v1/key`); Adzuna **7/12**.
- Worktrees preservados de outra frente: `../GS-wt/S5-auth`, `../GS-wt/S5-red` (este com alterações locais — não limpar). Processo `agy` PID 30832 (09h23) é da frente do panorama — não encerrar.
- Disco: 22,0 GB livres (15h49).

## 4. Próxima sessão — tarefas em ordem

**Caminho crítico (produto ponta a ponta):**
1. **S11b rotas** `PUT /me/intencao` + `POST /me/comparacoes` `{destinos:[≤3]}` (cookie+CSRF; usa catálogo aprovado + `competencias_para_comparacao` + mercado do snapshot como repasse; persistência Oracle `comparacao`/`comparacao_destino` em `003_*.sql`). Explicação LLM fundamentada é opcional e só se houver tempo (D07; nunca calcula números).
2. **S15b telas web** (agy, `app/web`, usar skill `impeccable`): login/registro, consentimentos, intenção, currículo (upload/colar → revisão do texto redigido → confirmar), competências (confirmar/rejeitar/não possuo), comparação de até 3 destinos por dimensões. Smoke real no Edge com API local.
3. **S12 plano** (domínio + rota): lacunas → atividades por pré-requisito + checkpoints.
4. **S13 avaliação** (fatia de risco: RED reproduzido + revisão independente): `GET /destinos/{id}/exercicio` sem gabarito, `POST /me/tentativas` 50/50, LLM fora → "parcial", "discordo", 4ª tentativa em 24 h → 429, `temperature=0`, cache por hash (D06, D21, R23, T08).
5. **S14 laboratório**: `POST /me/laboratorio/sessoes` → código; leituras da sessão; relato ≤280 redigido segue pela outbox.
6. **S15 E2E**: Playwright + axe com persona demo sinalizada.

**Entregas acadêmicas (paralelo, escopos disjuntos):**
7. `06_Cloud/README.md` (cenário: monitoramento de bancada de laboratório; limiares de `limiares.json`; caminho de IA B Comprehend com AccessDenied documentado + HF 402; ODS; passo a passo; Function URL e endpoint sem senha) — evidências já existem.
8. `02_Cybersecurity/relatorio.md` → PDF ≤15 págs. (S5 auth/CSRF/429, S9 PII parcial (D22, R18), S10 injeção T15, S4 D09a chave opcional/401/429/idempotência, SG aberto como exceção D09, LGPD do relato no CloudWatch, desenho de produção).
9. `03_DataScience/relatorio.md` + `oracle.sql`/`mongodb.js` (cópias de `app/db`): DDL 001+002(+003), consultas de evidência (JOIN, agregação, subconsulta, ranking) **executadas no Oracle local**, coleções Mongo reais (`curriculos_redigidos`, `extracoes_llm`, `model_cards`). Oracle FIAP fora de escopo (declarar).
10. `04_CTP_Python/documento.md` (leituras/CSV/outbox/idempotência; modo isolado R16) e cópias de código pelo empacotador.
11. `01_AICSS/relatorio.md` (sensores como instrumento de avaliação prática; 3 cenários; o que é simulado) — depende de rodar o firmware no Wokwi.
12. Firmware: rodar no Wokwi (VS Code + extensão, `host.wokwi.internal:8000`) contra a API local com `DEVICE_KEY` da demo; gravar evidências dos 3 cenários.
13. Roteiros `*/video.md`, `09_AIC` (relatório/roteiro), revisão geral de conformidade acadêmica (agy `--mode plan`) antes do D7, empacotador final + PDFs.

**Não verificado / dívidas registradas:** axe nunca rodado; bundle web 737 kB; revisão independente de S10 não feita; Comprehend negado (limitação de conta); prints CloudWatch 1–2 a refazer; `escopo_mvp.json` com `status_rubricas` desatualizado de propósito (não alterar; S10 lê o status de cada YAML).

## 5. Guardrails

Holdout 2026 fechado; não retunar com 2025; não promover modelo; não reiniciar fatias integradas; não apagar dados; não ler/imprimir valores do `.env`; push só para `gs-semestre2` com gitleaks antes; OpenRouter ≤ US$ 7; Adzuna ≤ 12 (restam 5); AWS só com Learner Lab ativo; mínimos acadêmicos nunca cortados (D16).

## 6. Pendências humanas

- **Refazer 2 prints do CloudWatch** (os arquivos `cloudwatch-1.png` e `cloudwatch-2.png` foram sobrescritos por erro do orquestrador ao mover para a pasta privada): stream de 18:38 UTC mostrando `WARNING LEITURA DESCARTADA` + `CHAVE INVALIDA` (print 1) e `ALERTA CIDADAO` + `GRAVADO NO RDS` (print 2). Salvar em `06_Cloud/evidencias/` — o orquestrador tarja o e-mail e versiona.
- Prints ainda não feitos: **Function URL** (Auth type NONE) e **RDS → Connectivity & security** (endpoint, publicly accessible, regra 5432).
- Manter o SG 5432 aberto até o fim da correção (D09) e reiniciar o Learner Lab se expirar.
- Wokwi: abrir o projeto `app/iot/firmware` no VS Code com a extensão Wokwi (licença gratuita) quando o agente pedir; ESP32 físico só se o agente avisar.
- Data Modeler (D25) sobre o DDL do Oracle local; nomes/RMs nos `[HUMANO — preencher]`; vídeos (ML ≤5, RNA, Cyber ≤5, Cloud ≤5, AIC ≤7 com rosto); ideia da live; envio no Portal (Estatística: `.pdf` + `.py` + `.csv`).

## 7. Decisões locais válidas

- Limiares só em [limiares.json](<../app/config/limiares.json>); HTTP 400 para validação; DDL Oracle 19c; domínio pt-BR sem acento.
- `status_promocao="nao_decidida"`; app exibe o baseline de menor MAE de validação.
- Sentimento (D23): Comprehend por padrão, HF alternativo; falha → `indisponivel`; nunca entra em nota.
- OpenRouter: `max_tokens=6000` + `reasoning.max_tokens=2000`, `temperature=0`, `data_collection=deny`, `require_parameters=true`; `content` vazio = falha → retry → fallback.
- Lista fechada ESCO = união dos requisitos dos YAMLs com `revisao_humana.status == "aprovado"` dos destinos de `escopo_mvp.json`.
- Trecho de evidência só com marcadores de redação é descartado.
- Simulador Cloud anexa `/ocorrencias` à Function URL; Lambda força logs INFO e loga `sqlstate` em falha de conexão.
- PDF sem LaTeX; componentes web sem cores fixas `text-neutral-*`; Tailwind só para layout.
- Sem score único; PII só vai à LLM redigida e confirmada.
