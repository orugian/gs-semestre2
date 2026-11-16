# Estado do desenvolvimento — CitizenTech

> Primeiro arquivo da próxima sessão. Snapshot documental, não monitoramento em tempo real. Histórico detalhado de aceites anteriores: `git show d2ddec4:docs/estado.md` (até 15/11) e `git show 5d311e7:docs/estado.md` (sessão de 16/11 madrugada); trilha completa em `../.kaiser/reports/` e `../.kaiser/contratos/`.

**Checkpoint funcional:** `main` em `5d311e7` + este commit documental, conferido em **16/11/2026 às 09h15 (UTC−3)**, árvore limpa. Prazo **19/11/2026 às 23h55** — **3,6 dias**. Nenhum push nesta sessão (`main` está 82+ commits à frente de `origin`). A aplicação **ainda não funciona ponta a ponta**: existe mercado (API + tela + painel técnico), autenticação e leituras CTP; faltam currículo/PII, extração, comparação, plano, avaliação, laboratório, nuvem, firmware e jornada E2E.

## 1. Ponto de parada

| Fatia | Situação | Commit de integração |
|---|---|---|
| S0–S3 base, limiares, leituras CTP, outbox | integradas (sessões anteriores) | — |
| S5 autenticação/consentimentos | integrada; Oracle real 208 passed na época | `c391eac` |
| S6 ingestão Caged, S7 features/split, ML/RNA/D11 | integradas; nenhum modelo promovido | `1a47a1a`, `a3a6866` |
| **S8 mercado API + snapshot + painel R06** | **integrada 16/11** | `a49682f` |
| **E08 Estatística portátil + relatório** | **integrada 16/11** | `181ba51` |
| **S15a tela web Mercado + Painel técnico** | **integrada 16/11** | `6662ff3` |
| **E05 notebooks ML/RNA + slides ML** | **integrada 16/11** | `13cb0a2` |
| S9 currículo/PII · S10 extração · S11 comparação · S12 plano · S13 avaliação · S14 laboratório | **não iniciadas** | — |
| S4 Lambda/RDS · firmware Wokwi | **não iniciadas** (dependem de gates humanos) | — |
| S15 final (jornada E2E Playwright + axe) | não iniciada | — |
| Empacotador de entregas + PDFs finais | não iniciado | — |

**Regressão executada em `main` em 16/11 (madrugada, após o último merge):** `app/ml` 266 passed + ruff limpo; `app/api` 193 passed com `-m "not oracle"` (28 testes Oracle **não executados** — Oracle parado); `app/web` 17 passed + typecheck + build. Cloud (50) e Tools (20) **não reexecutados** desde 15/11.

## 2. O que está verificado (e o limite de cada item)

| Frente | Evidência | Limite |
|---|---|---|
| Mercado S8 | Snapshot real exportado e conferido por script independente (`../.kaiser/tmp/conferir_snapshot_s8.py`): 55 séries com estimativa, 26 abstenções; MAE dos 6 modelos igual à evidência de 15/11. HTTP real: SP 200 com metadados T17, AC 200 abstenção + contexto Norte, 404 fora do MVP, 400 `uf=XX`. | Model cards só dentro do snapshot, **não no MongoDB** (Atlas sem senha). RED do agente não reproduzido pelo orquestrador. |
| Tela S15a | Render real no Edge (API local + `vite preview`), 1280 px e 390 px, SP/AC/painel técnico. | Sem axe/Playwright. Bundle 737 kB. Não está numa jornada (sem login/currículo). |
| Estatística E08 | Programa portátil reproduz exatamente o JSON D11 de 15/11 (16 checagens); 8 figuras; relatório sem LaTeX; PDF de teste 21 págs. | PDF final, cópia `analise.py`/CSV nas pastas de entrega e nomes/RMs pendentes. |
| Notebooks E05 | Reexecutados pelo orquestrador (saída 0); números das tabelas = artefatos; slides com números amarrados por teste; RNA confere 495 linhas por chave. | Cópia para `05_ML/notebook.ipynb`/`07_RedesNeurais/notebook.ipynb` pendente (empacotador); PDF dos slides pendente; vídeos humanos. |
| Auth S5 | Oracle real na época (208 passed). | UI de login ausente. |
| CTP/outbox | API, CSV, idempotência. | ESP32/Wokwi e Lambda/RDS reais não integrados. |
| Catálogo | 6 YAMLs rascunho; MVP com 3 destinos (R29). | **Nenhuma rubrica revisada por humano.** |

## 3. Resultados científicos (não misturar coortes)

**ML/RNA (produto, R29):** 3 destinos × UF, superior+; fit 202101–202409, validação 202501–202509; 55/81 séries elegíveis, 495 linhas. MAE validação: persistência 35,45253 · sazonal 33,59596 · Ridge 34,25765 · RF 35,63387 · HGB 39,73936 · MLP A 31,65446 (−5,78% vs sazonal). **Nenhum modelo promovido**: D10a exige também estabilidade do WAPE e a decisão final depende do holdout 2026, fechado. App exibe o sazonal rotulado "estimativa retrospectiva (2025)". [Evidência](<../05_ML/evidencias/20261115_modelos_mvp_aceite.md>).

**D11 (Estatística):** 6 destinos, todas as escolaridades, 229 municípios SP. Z: p 0,324 (n20/α6%) e 0,659 (n25/α9%), não rejeitam H0. OLS R² 3,6×10⁻⁷ e 0,0215. Logística teste 54,35% ([[8,14],[7,17]]). Dois salários médios extremos (352885 R$ 527.726,85; 351210 R$ 86.712,01) mantidos por pré-registro, sem análise de sensibilidade. [Relatório](<../08_Estatistica/relatorio.md>), [JSON](<../08_Estatistica/evidencias/20261116_analise_portatil.json>).

## 4. Ativos e proteção operacional

Raízes externas: `GS=..`, `.dados=../.dados`, `.kaiser=../.kaiser`, worktrees=`../GS-wt`.

- Painel DEV MVP `../.dados/caged/painel/r29_20261115_2041/painel_mvp.parquet` (SHA `33a89898…c22c5`); DEV 6 destinos `../.dados/caged/painel/painel_desenvolvimento.parquet` (SHA `8e653b00…4eb9e`).
- Artefatos `../.dados/artefatos/{classicos,rna}/20261115_r29_aceite/` (manifestos com hash = integridade local, não autenticidade).
- **Snapshot de mercado** `../.dados/mercado/20261116_r29_aceite/` (SHA `snapshot_mercado.json` `9c093f93091fbda4bb4bdc796cd9eee9823da4005dfa22616950dba8d37540a3`). Servir com `CITIZENTECH_MERCADO_SNAPSHOT` apontando para esse diretório.
- Base D11 `../.dados/estatistica/20261115_d11_aceite/base_municipal.csv` (SHA `5dbc73ac…a7ee`).
- **Não** reconstruir painel com o loader legado sobre `caged/parquet` (diretório misto com 2026). **Não** subir a API com `FUNCTION_URL` e `CITIZENTECH_DADOS` real: `../.dados/runtime/outbox.db*` tem 77 eventos antigos de teste (preservar; remoção só com aprovação).
- Docker: os 3 containers estão parados (Oracle saiu às ~09h08 por terceiros); volumes preservados. Credencial temporária do schema S5 foi esquecida; nova credencial = gate humano.

## 5. Git, processos e worktrees (conferido 09h15)

- Worktrees preservados: `../GS-wt/S5-auth` (`b94b0de`) e `../GS-wt/S5-red` (`112042d`). **DOC-panorama integrado em `c6ee6e1` e worktree/branch limpos removidos às09h44**; não há mais autoria pendente desse HTML.
- Processo `agy` PID 16884 (pai: powershell do Windows Terminal, 15/11 23h22) = sessão documental do panorama. Não é desta linha de trabalho. Conta para o limite de 2 agy simultâneos.
- Nenhum job/servidor desta sessão ativo; portas 8000/5173 livres.
- Disco: 23,5 GB livres.

### Encerramento documental —16/11 às09h44

[Panorama visual offline](<panorama_projeto.html>) publicado, reconciliado com as integraçõesS8/E05/E08/S15a da outra frente. Snapshotfuncional09h15, não monitoramento vivo. Próxima implementação continua**S9 após gates**; nada de reiniciarS8 ou refazer os notebooks. [Aceite/evidências](<../09_AIC/evidencias/20261116_panorama_aceite.md>): RED de ausência porAssertionError;8checagens próprias emmain passed; Edge real no arquivo publicado em1440/768/390/360,sem expansão horizontal do corpo,teclado/hover verificados,zero recursos remotos,contraste de texto computado mínimo6,917:1. Revisão independente leu toda superfície+6capturas;P2 de rubricas tardias corrigido e resolução confirmada. Não é auditoriaaxe integral nem regressão do app.

Jobs próprios152/168/290(autoria/reconciliação),166/174/179/277/292/293/300(browser) concluídos/coletados,sem job próprio restante; falhas de primeira rodada registradas,não omitidas. Não se matou oPID16884 nem se deduziu origem além do registro anterior. Nenhuma alteração emapp/ por esta linha documental,nenhum holdout/segredo acessado,push ou dado apagado. Disco24,1GB às09h43. Temporários globais de outras sessões não foram esvaziados para evitar perda concorrente; provas finais estão versionadas.

[Handoff atual no temporário do sistema](<C:/Users/orugi/AppData/Local/Temp/handoff_citizentech_20261116_0915.md>),com prompt atualizado no chat; substitui o inicial que ainda apontavaS8. [PRODUCT](<../PRODUCT.md>)/[DESIGN](<../DESIGN.md>) tratam o caderno, não uma nova identidade para o appAstryx.

## 6. Próxima sessão — tarefas em ordem

**A. Verificações que ficaram pendentes (fazer primeiro, baratas):**
1. Subir serviços de teste (`docker compose -f app\docker-compose.yml --profile teste up -d --wait`) e rodar a suíte API **com Oracle** (`uv run pytest -q` em `app/api`) — os 28 testes `oracle` não rodaram após S8. Se a credencial do schema de teste não funcionar, registrar e pedir ao usuário; não recuperar senha.
2. Reexecutar `app/cloud` e `app/tools` (`uv run pytest`, `uv run ruff check .`).
3. Rodar **axe** sobre a tela de mercado (Playwright + `@axe-core/playwright` exige `pnpm add -D`, permitido dentro de `app/web`) — pode entrar como primeiro teste E2E da S15.

**B. Caminho crítico do produto (atrasado ≥1 dia):**
4. **S9 currículo/PII** (fatia de risco: RED reproduzido pelo orquestrador + revisão independente `agy --mode plan`): `POST /me/experiencias`, `POST /me/curriculo` (PDF/DOCX ≤2 MB, pypdf/python-docx), redação de PII, `POST /me/curriculo/confirmar-envio`; nada vai à LLM sem confirmação (D07a, D22, R18, T15). Persistência do texto redigido: Mongo de teste local (27018) nos testes; Atlas real só com credencial.
5. **S10 extração** (LLM com fake na fronteira; lista fechada de IDs ESCO; T07). OpenRouter real só com autorização (quota US$ 7).
6. **S11 comparação** (domínio puro; obrigatório não atendido não some; `desconhecida`≠`lacuna`; ≤3 destinos).
7. S12 plano → S13 avaliação (risco) → S14 laboratório → telas web correspondentes → **S15 jornada E2E** com persona demo.

**C. Entregas acadêmicas (paralelo, sem sobreposição de arquivos):**
8. **Empacotador** `app/tools/empacotar_entregas.py` (D6 do plano): copia `analise_portatil.py`→`08_Estatistica/analise.py`, `base_municipal.csv`→`08_Estatistica/`, notebooks→`05_ML/notebook.ipynb` e `07_RedesNeurais/notebook.ipynb`, gera PDFs (relatório Estatística, slides ML) com figuras em caminhos relativos corretos, contagem de páginas. Hoje esses alvos ainda são os **modelos do professor com TODO**.
9. Relatórios ainda vazios/TODO: `02_Cybersecurity/relatorio.md` (≤15 págs. PDF; S5 tem evidência), `04_CTP_Python/documento.md`, `03_DataScience/relatorio.md` (+ DDL/Mongo), `01_AICSS/relatorio.md`, `06_Cloud/README.md`, roteiros `*/video.md`. Escrever só o que está implementado; o restante rotulado como planejado.
10. Model cards no MongoDB: implementar gravação contra Mongo de teste; Atlas quando houver credencial.

**D. Guardrails:** holdout 2026 fechado; não retunar com 2025; não promover modelo; não ler `.env*`; não push sem ok; APIs pagas/AWS só com autorização; mínimos acadêmicos nunca cortados (D16).

## 7. Pendências humanas

- **Revisar as 3 rubricas** do MVP ([roteiro](<../app/catalogo/README.md>) §4) — bloqueia qualidade de S10/S13.
- Credenciais no `app/.env` (nunca no chat): senha do `MONGODB_URI` Atlas + liberar IP; Oracle FIAP (ORA-01017 em 12/11); Learner Lab ativo (Lambda/RDS); HF sem créditos (402) — decidir créditos ou alternativa.
- Autorizar: uso do OpenRouter nos smoke tests reais; snapshot Adzuna (≤12 chamadas) ou manter "indisponível"; push e para qual remoto.
- Data Modeler (D25), ideia da live, vídeos (ML ≤5 min, RNA obrigatório, Cyber ≤5, Cloud ≤5, AIC ≤7 com rosto), envio no Portal, prints do console AWS.

## 8. Decisões locais válidas

- Limiares só em [limiares.json](<../app/config/limiares.json>); validação HTTP 400; DDL Oracle 19c; domínio em pt-BR sem acento.
- `status_promocao="nao_decidida"` enquanto o holdout estiver fechado; app exibe o baseline de menor MAE de validação.
- Snapshot de mercado é derivado dos artefatos sem desserializar modelos (só hash + JSON/parquet); a API verifica o SHA do snapshot antes de servir.
- Notebooks de entrega têm fonte em `app/ml/notebooks/`; programa estatístico em `app/ml/src/citizentech_ml/estatistica/analise_portatil.py`. Pastas `0X_*` recebem cópias pelo empacotador.
- O gerador de PDF (`app/tools/md_para_pdf.py`) **não renderiza LaTeX**: documentos de entrega usam Unicode.
- Componentes web: não usar cores fixas `text-neutral-*` (tema escuro do Astryx); Tailwind só para layout.
- Nenhum score único, nenhuma probabilidade individual de contratação; PII só vai à LLM redigida e confirmada; sentimento não entra na nota.
