# Plano de desenvolvimento — Transição de carreira orientada por evidências

**CitizenTech · FIAP GS 2026.2 · Plano v1.1 · 12/11/2026**
**v1.1:** incorpora a [revisão adversarial](revisao_adversarial_plano.md) (achados R01–R30); as linhas alteradas citam o ID do achado.
**Origem:** nivelamento Grill Me sobre [proposta_transicao_carreira.md](proposta_transicao_carreira.md) (seções 1–17).
**Prazo:** 19/11/2026, 23h55 (Portal do Aluno). **Estado:** aguardando aprovação final do usuário para iniciar a Fase 1.

> Este plano substitui as "recomendações" da proposta onde houver conflito. Itens marcados **[HUMANO]** não podem ser delegados a agentes.

---

## 1. Decisões fechadas no nivelamento

| # | Tema | Decisão |
|---|---|---|
| D01 | Público | **Amplo:** profissionais graduados e experientes em transição. O laboratório IoT é a **trilha prática opcional** do destino técnico, não um produto paralelo. **Risco aceito pelo usuário (R12):** a coerência dos sensores com o público amplo é o ponto mais fraco em AICSS/CTP/Cloud. O relatório de AICSS deve justificar explicitamente que os sensores servem à **avaliação prática da competência de monitoramento** do profissional em transição, e não a um fenômeno urbano. |
| D02 | Catálogo | **6 destinos curados:** (1) Analista de Dados/BI; (2) Analista de Monitoramento/IoT Industrial (com laboratório); (3) Analista de Processos/Melhoria Contínua; (4) Gerente de Projetos/Produto; (5) Analista de Suporte/Infraestrutura de TI; (6) Desenvolvedor de Sistemas. **Corte se faltar tempo: 3 destinos (1, 2, 3).** |
| D03 | Saída da 1ª sessão | Perfil → competências confirmadas → comparação de até 3 destinos → **escolha de 1** → plano inicial com checkpoints → 1 exercício diagnóstico. A reavaliação versionada fica como evolução futura. |
| D04 | Mercado (ML/RNA) | Novo Caged **jan/2020–set/2026** (verificado no FTP do MTE em 12/11). Unidade: **destino × UF (27) × mês**. Série principal: **admissões com superior completo ou mais**; a série total fica como contexto. Alvo: `y(g,t)=A(t+1)+A(t+2)+A(t+3)`. O app mostra SP por padrão, com UF selecionável. |
| D04a | Unidade ocupacional (**confirmada, R04**) | Cada destino é um **conjunto de ocupações CBO de 6 dígitos, disjunto dos demais**, para não contar a mesma população em vários destinos (a família 2124 é comum a vários destinos de TI). **Regra de densidade pré-registrada (R03):** uma série destino × UF só entra no treino e na avaliação se a média do alvo no treino for **≥ 10 admissões por trimestre**. Abaixo disso, o app **se abstém** naquela UF (T06) e mostra o agregado regional como contexto. |
| D04b | Revisões do Caged (**R02**) | **Features em *t*:** só registros com `competênciadec ≤ t` (o que já tinha sido declarado em *t*). **Alvo:** contagem consolidada MOV+FOR−EXC por `competênciamov`. Medir no histórico a fração de FOR por defasagem; se passar de 2% nos meses finais do teste, cortar esses meses ou declarar o viés, **antes** de abrir o teste. |
| D05 | Requisitos | Curadoria manual de **CBO + ESCO pt**, versionada (`app/catalogo/destinos/*.yaml`), com origem, data e revisor. Sem embeddings no MVP. |
| D05a | Adzuna | **Snapshot único em cache:** no máximo 12 chamadas (6 destinos × {SP, BR}), JSON bruto guardado com data e hash. Exibido como "amostra pontual Adzuna de DD/MM/2026", com atribuição. Não entra no treino. Nenhuma chamada ao vivo por usuário. As outras 13 chamadas ficam de reserva para smoke test e vídeo. |
| D06 | Exercício diagnóstico | Por destino, **3–5 questões objetivas** (correção determinística) + **1 resposta aberta** avaliada pela LLM por critério de rubrica (JSON validado: critério, nota 0–2, trecho justificador). **Nota final = 50% objetiva + 50% LLM.** Para "demonstrada (básico)", as duas partes precisam atingir o mínimo. Botões **"refazer"** e **"discordo"** (registra a flag; atende o art. 20 da LGPD e o T08). Se a LLM falhar, o resultado fica **"parcial"**, só com a objetiva. A rubrica é revisada pelo grupo. |
| D06a | LLM | **OpenRouter** com o modelo padrão `deepseek/deepseek-v4.1-flash-1017` e `response_format=json_schema`. Se o JSON vier inválido depois de 1 retry, cai para o **fallback `xiaomi/mimo-v2.6-flash`** (structured outputs nativo; configurável por env). Fica atrás de um adaptador `LLMClient`, e os testes usam um fake na fronteira. |
| D07 | Comparação | A LLM extrai competências **para uma lista fechada de IDs ESCO do catálogo**, cada uma com o trecho de origem → o usuário confirma, edita ou rejeita → regras determinísticas classificam cada requisito como `demonstrada`, `declarada`, `desconhecida` ou `lacuna`. **Dimensões separadas, sem score único.** |
| D07a | Currículo | Upload de **PDF/DOCX ≤ 2 MB** ou texto colado. Extração local (pypdf/python-docx), sem OCR. **Redação de PII** (e-mail, telefone, CPF, CEP/endereço, URLs de perfil) antes da LLM. **O original não é persistido**: só o texto redigido + hash vai para o MongoDB, com consentimento por finalidade. O conteúdo é tratado como dado não confiável (T15). |
| D08 | Bancos | **Oracle:** Docker `gvenzl/oracle-free` para o app e os testes; a execução no **Oracle FIAP** gera as evidências da entrega (DDL + consultas). **MongoDB:** Atlas M0. |
| D09 | AWS | **AWS Academy Learner Lab** (us-east-1, LabRole). RDS PostgreSQL "publicly accessible" como **exceção acadêmica documentada**: SG 5432 aberto nas janelas de teste e gravação e, **a partir da entrega (19/11), aberto continuamente até o fim da correção** para o avaliador conseguir testar (R14). Restringir ao IP `/32` **não funciona**, porque a Lambda fora de VPC sai por IPs dinâmicos. Controles: `rds.force_ssl=1`, `sslmode=verify-full` com o CA bundle, usuário `app_ingest` com INSERT/SELECT apenas, banco só com dados didáticos. O desenho de produção (Lambda em VPC + RDS Proxy) fica descrito no relatório de Cyber. |
| D09a | Function URL (**R13**) | `AuthType NONE` + header **`X-Device-Key` opcional**: **sem a chave**, o POST é aceito e gravado com `autenticado=false` (o log marca "não autenticado"), sujeito a **limite por `dispositivo_id`/minuto** verificado no RDS → 429. **Chave inválida → 401**. A FastAPI/outbox e o ESP32 sempre enviam a chave. Assim o simulador oficial do professor funciona. Reserved concurrency baixa, **se a conta permitir** (R24); senão, vale o limite da conta, documentado. Evidência em Cyber: 401 com chave errada, 429 por excesso e a flag `autenticado`. |
| D10 | Divisão temporal (**corrigido, R01**) | Por mês de referência *t*: **treino *t* ≤ set/2024 · validação *t* jan–set/2025 · teste *t* jan–jun/2026** (rótulos até set/2026). As lacunas out–dez/2024 e out–dez/2025 são o **embargo**: nenhuma linha cujo alvo atravesse a fronteira. Dentro do tuning, cada fold também expurga as últimas 3 linhas antes da validação. O modelo servido no app é **retreinado com todos os *t* rotulados (≤ jun/2026) depois do teste**, e isso é declarado. Tuning com origem móvel **dentro do treino**. Holdout aberto **uma única vez**. A exclusão de 2020 pode ser decidida na EDA, desde que antes de abrir a validação. |
| D10a | Promoção ao app | O modelo é promovido **para o número mostrado ao usuário** só se o **MAE de validação ficar ≥ 5% abaixo do melhor baseline** e o desvio do WAPE entre folds for menor que o ganho. Se nenhum passar, o app exibe o baseline. A RNA concorre nas mesmas condições. **Critério congelado neste documento.** **Integração garantida (R06):** todos os modelos (baseline, Ridge, RF, HGB e MLP) são servidos pela API (`GET /mercado/{destino}/modelos?uf=`) e aparecem no **painel técnico** com métricas lado a lado. Assim a RNA fica integrada à solução sem ser promovida artificialmente. |
| D10b | Stack ML/RNA | scikit-learn: baselines (persistência trimestral e sazonal), **Ridge**, **RandomForest**, **HistGradientBoosting**; tuning com RandomizedSearchCV + splitter temporal. RNA: **PyTorch CPU MLP**, com ≥ 2 configurações, dropout, early stopping e curvas. Escolha justificada por eficiência: wheel CPU leve no Windows, seeds determinísticas e inferência servida pelo próprio FastAPI. |
| D11 | Estatística | Base transversal: **municípios de SP × 2025**, agregada a partir do mesmo Caged (6 destinos). Variáveis: admissões, desligamentos, salário médio de admissão, % superior+, crescimento vs 2024. **Logística (R07):** alvo `admissões_2025 > admissões_2024`; explicativas **medidas em 2024 e sem relação com o cálculo do alvo**: **salário médio de admissão e % superior+**. **Emenda aprovada pelo usuário em15/11, antes da análise real:** retirar participação dos destinos no total municipal, cujo denominador não existe na ingestão filtrada. Manter as duas explicativas mínimas do enunciado, sem fabricar denominador; seis destinos científicos preservados. Isso evita a regressão tautológica. **Normalidade (R08):** assumida porque o enunciado manda, com histograma, QQ e Shapiro como diagnóstico e análise em `log(1+x)` como complemento, sem substituir os itens. A população é definida **antes** da análise (municípios com ≥ 10 admissões no recorte). Amostras com seed fixa declarada. **Python (scipy/statsmodels)**. Os parâmetros exatos do enunciado (n=20/α=6%; n=25/α=9%) são mantidos. |
| D12 | Autenticação do app | E-mail + senha (**argon2**), **JWT em cookie httpOnly + `Secure` + `SameSite=Lax` + token CSRF double-submit** (`X-CSRF-Token`) em métodos mutáveis (R20), autorização por proprietário em `/me/*`, **rate limit** (login 5/min; rotas LLM com quota), resposta **429**. Personas demo pré-criadas e sinalizadas. |
| D12a | Execução | **Local via `docker compose`** (web, api, oracle-free). O **worker da outbox roda dentro do processo da API** (tarefa de fundo) e o SQLite fica em **volume nomeado**, nunca em bind mount do Windows (R25). Mongo no Atlas (região `sa-east-1` se o M0 permitir, R19), Lambda e RDS na AWS. **Modo CTP isolado (R16):** `leituras` roda sozinho (`uvicorn` + CSV, sem Oracle/Mongo) com um comando, para o avaliador de CTP. |
| D13 | Laboratório IoT | O app cria uma **sessão de laboratório com código** → ESP32 Wokwi ou simulador envia os 3 cenários para `FastAPI POST /leituras` → CSV + outbox → worker → Lambda/RDS. A pessoa classifica as leituras (objetiva) e escreve o **relato ≤ 280 caracteres** (aberta, LLM). O relato passa pela redação de PII e é enviado à Lambda para análise de sentimento. A tela avisa que o relato vai para a nuvem e mostra o estado de sincronização. O simulador que fala direto com a Function URL continua existindo como evidência separada do Cloud. |
| D14 | Execução multiagente | **Orquestrador: esta sessão.** Implementadores: **`agy` + `gemini-3.8-flash-high`** com `--dangerously-skip-permissions`, **restrito à allowlist de comandos da §6.2**, **isolado em `git worktree` próprio, com ambiente sem segredos** (§6.3, R22), snapshot de git antes e depois e escopo de escrita exclusivo. Prompt sempre **via stdin** (aspas no argumento `-p` quebram o PowerShell 5.1; falha verificada na revisão). Revisor independente: outra chamada `agy` em `--mode plan`, sem participação na autoria. |
| D14a | Equipe | Nomes, RMs, papéis, gravações e ideia da live ficam como **[HUMANO] TODO**. |
| D14b | Gestão | **GitHub Projects** (repositório `insonia999/GS2_26`) com issues por fatia; UML em **Mermaid** versionada no repo. **Pré-requisito [HUMANO] (R28):** `gh auth refresh -s project,read:project` (o token atual não tem esse escopo). Até lá, só issues. |
| D16 | Corte e cronograma | Ordem de corte: (a) 6→3 destinos; (b) DOCX (fica PDF + texto); (c) Adzuna; (d) cenários 2026–2031 viram texto estático com fontes; (e) "discordo" vira só "refazer". **Mínimos acadêmicos nunca saem.** |
| D16a | Frontend | **React 19 + TypeScript + Vite**, componentes **Astryx** (`@astryxdesign/core`, versão fixada por ser beta, tema + CLI), **Tailwind só para layout**. Skill **impeccable** para direção visual, copy e auditoria. Testes: Vitest + Playwright + axe. **Plano B**, se o Astryx falhar no build do D1: Radix + Tailwind. |
| D16b | Segredos | `.env` fora do git + `.env.example` versionado. Nenhum agente lê ou imprime `.env`. **gitleaks** antes de cada commit. |
| D17 | ODS | **ODS 4 (meta 4.4) e ODS 10** como principais (ambos destacados pela FIAP); **ODS 8 (8.5/8.6)** como secundário. |
| D19 | Entregáveis | **Relatórios em Markdown** e **evidências visuais em HTML** (páginas estáticas com prints, saídas e tabelas). **Pipeline de formato desde o D1 (R10):** `md → html → pdf` com **Edge headless** (`msedge --headless --print-to-pdf`; não há pandoc nem LibreOffice na máquina), rodado a cada rascunho, com **contagem automática de páginas** (falha acima de 15 no Cyber). Os formatos exigidos pelo Portal são gerados por esse pipeline: Estatística `.pdf` + `.py` + `.csv`; Cyber PDF ≤ 15 páginas; ML slides em PDF. |
| D21 | Exercícios (**R23**) | Avaliação LLM com `temperature=0` e cache por hash da resposta. **No máximo 3 tentativas por exercício a cada 24 h**, todas registradas. |
| D22 | LGPD/LLM (**R18, R19**) | Antes de enviar o texto à LLM, o usuário vê o **texto redigido, pode editar e confirma o envio**. Heurística adicional remove o cabeçalho (nome). OpenRouter com `provider.data_collection="deny"`. O consentimento cita o operador (OpenRouter/DeepSeek) e a transferência internacional. A redação de PII é declarada como **parcial** no relatório de Cyber. |
| D23 | Sentimento (**R17**) | O sentimento HF do relato é **só o tom do relatório de incidente** (metadado da ocorrência). **Nunca** entra na nota de competência. Declarado no README de Cloud. |
| D24 | Firmware (**R21**) | A chave do dispositivo é **exclusiva da demo**, rotacionável, só vale para `POST /leituras` e tem rate limit próprio. Projeto Wokwi privado. O túnel ngrok é aberto **apenas durante a demonstração**. |
| D25 | Oracle (**R27**) | DDL no **dialeto 19c** (sem `BOOLEAN`, sem `IF [NOT] EXISTS`, sem domínios), para rodar igual no Docker 23ai e no Oracle FIAP. **Data Modeler (R11): obrigatório [HUMANO] no D4** (cerca de 30 min: importar o DDL, gerar os modelos lógico e relacional, exportar imagem/PDF). |
| D20 | Repositório | Monorepo em `info-gs-diciplinas/`: código em `app/`, entregas nas pastas `0X_*`, que referenciam o código. Limiares em **um único `app/config/limiares.json`**, consumido pela API, pela Lambda (copiado no empacotamento) e pelo firmware (header gerado). |

### 1.1 Registro de execução — 15/11/2026

- **D11/R07 — pré-registro municipal aprovado pelo usuário antes da análise real:** SP, seis destinos e todas as escolaridades; população de municípios com ≥10 admissões no recorte em2024. Snapshot de2024 até202412 e de2025 até202512; não abrir arquivos2026. Usar o campo oficial `salário` (salário mensal declarado), não `valor_salario_fixo`; ausentes/não positivos/infinito excluídos somente do denominador/média salarial, sem corte de outliers. Percentual superior declarado sobre todas as admissões, desconhecidos contabilizados separadamente. Modelos com salário/percentual usam casos completos e explicitam perdas, sem alterar população/seed após ver resultado. Logística: split municipal80/20 estratificado, seed44, limiar0,5; matriz/acurácia no teste, conformeR07, não apenas in-sample. TestesZ sobre admissões2025, amostras sem reposição com seeds42/43, n20/α6%unilateralmenor e n25/α9%unilateralmaior; σpopulacional(ddof0). Dicionário oficial local verificado por SHA-256 `0490f7ef84fd05db2d89cf22f56d8cf7262ceb14c9d7db1cca2bae422e6423ce`: `salário` mensal; unidade é da parte fixa; grau80=Pós-Graduação completa. Nenhuma base real municipal foi analisada antes deste registro.

- **D11 — emenda aprovada explicitamente pelo usuário na retomada:** usar salário médio de admissão2024 e percentual com superior2024 como as duas explicativas da logística; retirar participação dos destinos no total municipal. O Parquet preserva apenas CBOs selecionados e não fornece esse denominador. Aprovação registrada antes da análise municipal real, sem alterar alvo2025>2024, população científica de seis destinos,n/α literais,normalidadeassumida ou sementes. Implementação adaptada/testada/revista e integrada; base real de229municípios gerada somente de72fontes2024/25, Z/OLS/logísticaestratificada e diagnósticos executados/conferidos. Logística183treino/46teste,seed44,limiar0,5,acurácia54,3478%; resultados fracos preservados, sem ajustar parâmetros por desempenho. Evidênciapreliminar: [D11 real](<08_Estatistica/evidencias/20261115_d11_aceite.md>). Pacote portátilPDF/PY/CSVfinal ainda pendente.

- **D10 — escolha aprovada pelo usuário antes de avaliar a validação:** treinar com origens **202101–202409** (45 meses), mantendo os dados de 2020 apenas como histórico para os lags das origens de 2021. Excluir as 12 origens de 2020; não imputar suas features ausentes para incluí-las no treino. Os limites de validação/teste, embargo, densidade e promoção permanecem congelados. A aprovação **não é evidência de execução**. Na retomada, baselines executados com `--escopo-mvp --inicio-treino 202101 --validacao`: 55 séries elegíveis no treino, 495 linhas de validação; MAE persistência35,45 e sazonal33,60. Conferência independente de n/MAE/RMSE/WAPE nos3folds e validação sem divergências. Código integrado no merge `d807e10`, regressãoML110passed. Etapa posterior desta retomada: clássicos e RNA implementados/revistos/integrados, regressão conjuntaML/RNA/Estatística227passed. Treinos reais com os parâmetros fixados e conferência independente de n/MAE/RMSE/WAPE, alvos por chave e artefatos reabertos; MAEval Ridge34,25765,RF35,63387,HGB39,73936,MLP-A31,65446(5,77896%abaixo do sazonal). Nenhum parâmetro ajustado por2025, nenhuma promoção/serving ou avaliação final; holdout não aberto. Evidência adicional: [modelos reais](<05_ML/evidencias/20261115_modelos_mvp_aceite.md>). Evidência: [execução MVP](<05_ML/evidencias/20261115_baselines_mvp.md>); justificativa da escolha e EDA original em [estado](<docs/estado.md>) e [EDA do treino](<05_ML/evidencias/20261113-eda-treino.md>).
- **D02/D16/R29 — corte automático acionado:** às 18h50 de 15/11, os seis YAMLs continuavam com revisão humana pendente, sem aprovação registrada na sessão. Escopo do MVP reduzido aos destinos **(1) Dados/BI, (2) Monitoramento/IoT e (3) Processos/Melhoria Contínua**, conforme a ordem já aprovada. O corte não aprova rubricas nem autoriza apagar os outros rascunhos/dados. Recorte técnico aplicado ao pipelineML na retomada: manifesto canônico R29, projeção nova do painel e CLI explícito; originais de seis destinos/evidências de13/11 preservados. Próximas rotas de catálogo/mercado e a UI deverão consumir esse manifesto (ainda não integradas). D11/Estatística continua com sua população científica de seis destinos, sem emenda silenciosa.

---

## 2. Arquitetura alvo

```text
                     ┌──────────── app/ml (offline) ────────────┐
FTP MTE Novo Caged ─►│ ingestão streaming → agregados → features │─► artefatos versionados
Adzuna (≤12 calls) ─►│ snapshot cache                            │   (modelo, métricas, hash)
CBO/ESCO (curadoria)►│ catálogo YAML                              │
                     └───────────────────────────────────────────┘
                                         │ carrega artefatos próprios (sem upload)
Pessoa ─► web (React/Astryx) ─► api (FastAPI) ──┬─► Oracle (docker): relacional mestre
                                    │           ├─► MongoDB Atlas: currículo redigido, extrações,
                                    │           │   avaliações LLM, fontes, snapshots, model cards
                                    │           └─► OpenRouter (adaptador LLM)
ESP32 Wokwi / simulador ─► POST /leituras ─► CSV durável + outbox (SQLite, volume nomeado)
       LED/buzzer local                              │ worker na API, retry + evento_id
                                                     ▼
                              Lambda Function URL (X-Device-Key opc.) ─► HF sentimento (urllib)
                                         │ CloudWatch                ▼
                                         └──────────► RDS PostgreSQL `ocorrencias`
```

**Outbox (forma concreta):** SQLite `outbox.db` em **volume nomeado do Docker** (R25), escrito só pelo processo da API (o worker é uma tarefa de fundo do mesmo processo), com uma tabela `pendencias(evento_id PK, payload, tentativas, estado, ultimo_erro, atualizado_em)`. O worker usa backoff exponencial e trata as respostas da Lambda assim: 200/201 = ack; 409 = conflito sinalizado; 5xx/timeout = retry. O CSV é escrito por **um único processo** (a API) com lock de arquivo e append atômico por linha.

**Estrutura de pastas:**

```text
info-gs-diciplinas/
  app/
    config/limiares.json            # fonte única dos limiares
    catalogo/destinos/*.yaml        # 6 destinos: CBO6, ESCO, requisitos, exercício, rubrica
    api/                            # FastAPI (pyproject próprio)
      src/citizentech/{auth,perfil,curriculo,pii,catalogo,comparacao,mercado,
                       avaliacao,plano,laboratorio,outbox,llm,seguranca,persistencia}
      tests/{unit,api,integracao,contrato}
    ml/                             # ingestão Caged, features, treino, avaliação, export
    tools/                          # md→html→pdf (Edge headless), contagem de páginas
      notebooks/                    # fontes dos notebooks 05_ML e 07_RedesNeurais
    web/                            # React 19 + TS + Vite + Astryx
    iot/{firmware,simulador}        # sketch.ino + diagram.json Wokwi + gerador de header
    cloud/{lambda,sql,simulador}
    db/{oracle,mongo}               # DDL, seeds, consultas de evidência
    docker-compose.yml  .env.example
  01_AICSS … 09_AIC/                # relatórios .md + evidencias/*.html + cópias finais
  docs/                             # proposta, este plano, UML (Mermaid), ADRs curtos
```

---

## 3. Contratos (fechados para TDD)

### 3.1 Telemetria (AICSS → CTP → Cloud)

O contrato da proposta (§10.1) continua valendo. Métricas e limiares em `limiares.json`:

| Métrica | Unidade | normal | atenção | crítico | Direção |
|---|---|---|---|---|---|
| `temperatura_c` | C | < 35 | 35 ≤ v < 45 | ≥ 45 | maior = pior |
| `distancia_cm` | cm | > 15 | 8 < v ≤ 15 | ≤ 8 (v ≥ 0) | menor = pior |

Cenários: **25 °C/25 cm** (normal) · **38 °C/12 cm** (atenção) · **48 °C/5 cm** (crítico). Firmware: `OK` = normal e `ALERTA` = atenção/crítico. Atuadores: normal = desligado; atenção = LED; crítico = LED + buzzer. Falha de sensor (DS18B20 = −127 / HC-SR04 sem eco) gera `status:"ERRO"` e **não envia valor fabricado**.

### 3.2 API FastAPI (app)

| Rota | Auth | Resumo |
|---|---|---|
| `POST /auth/registrar` · `POST /auth/login` · `POST /auth/logout` · `GET /me` | — / cookie | argon2, JWT httpOnly, 429 no login |
| `POST /me/consentimentos` · `GET /me/consentimentos` · `DELETE /me/consentimentos/{id}` | cookie | finalidades: `perfil`, `curriculo_llm`, `laboratorio_nuvem`. Listagem do dono e revogação (404 se não existe ou é de outra pessoa): extensão aprovada pelo usuário em 13/11/2026 (D2), para tornar o T14 testável na S5. |
| `PUT /me/intencao` | cookie | atividades desejadas, motivos, h/semana, orçamento, UF |
| `POST /me/experiencias` (texto) · `POST /me/curriculo` (multipart ≤ 2 MB) | cookie | redação de PII → Mongo (texto + hash) |
| `POST /me/competencias/extrair` → candidatas · `PATCH /me/competencias/{id}` | cookie + quota LLM | confirmar, editar ou rejeitar; o estado nasce `declarada` |
| `GET /destinos` · `GET /destinos/{id}` | público | catálogo curado com fonte e data |
| `GET /mercado/{destino}?uf=SP` | público | observado + previsto + Adzuna + metadados (fonte, população, unidade, referência temporal, natureza) |
| `POST /me/comparacoes` `{destinos:[≤3]}` | cookie | dimensões separadas + explicação LLM fundamentada |
| `POST /me/caminho` → `GET /me/plano` · `PATCH /me/plano/checkpoints/{id}` | cookie | plano por regras (grafo de pré-requisitos) |
| `GET /destinos/{id}/exercicio` · `POST /me/tentativas` · `POST /me/tentativas/{id}/discordo` | cookie | sem gabarito no GET; nota 50/50; fallback "parcial" |
| `POST /me/laboratorio/sessoes` → código | cookie | vincula as leituras ao usuário |
| `POST /leituras` | `X-Device-Key` | 201 novo / 200 reenvio idêntico / 409 mesmo `evento_id` com conteúdo diferente / 400 / 401 / 429 / 503; CSV + outbox; estado `pendente_nuvem`. Extensão idempotente local aprovada pelo usuário em 13/11/2026 (D2). |
| `GET /leituras?sessao=&page=` · `GET /leituras/indicadores` | chave de dispositivo **ou** cookie do dono (R16) | histórico + total de alertas + média/máx./mín. por métrica |
| `GET /mercado/{destino}/modelos?uf=` | público (painel técnico) | previsões e métricas de todos os modelos, incluindo a RNA (R06) |
| `POST /me/curriculo/confirmar-envio` | cookie | o usuário revisa o texto redigido antes da LLM (R18) |

**Erros:** o handler global converte o 422 de validação em **400** com corpo `{erro, detalhes}`. Rejeita JSON malformado, NaN/Inf, bool como número, métrica desconhecida e payload acima de 8 KB.

### 3.3 Lambda (Cloud)

`GET /health` · `POST /ocorrencias` (400 para campo ausente, **sem chave → aceito com `autenticado=false`**, 401 para chave inválida, 429 acima do limite por dispositivo/minuto, **201 para registro novo**, **200 com o ID existente** para duplicata idêntica de `evento_id`, 409 para mesmo `evento_id` com conteúdo diferente) · `GET /ocorrencias?limite=`. Risco calculado localmente pelos limiares; sentimento HF por `urllib`, com timeout de ~8 s e resultado `indisponivel` em caso de falha, sem interromper a ingestão. Logs: payload bruto, dados interpretados, classificação e ID; `WARNING` para inválido ou crítico.

### 3.4 Persistência

**Oracle (relacional mestre):** `usuario`, `consentimento`, `intencao`, `experiencia`, `competencia_esco`, `competencia_usuario` (estado, origem, data), `ocupacao_cbo`, `destino`, `destino_ocupacao`, `requisito_destino`, `comparacao`, `comparacao_destino`, `caminho_escolhido`, `plano`, `checkpoint`, `exercicio`, `tentativa`, `sessao_laboratorio`, `mercado_mensal` (destino × UF × mês: admissões, desligamentos, total e superior+), `previsao_mercado` (modelo, versão, *t*, horizonte, valor). PK/FK/CHECK e consultas de evidência (JOIN, agregação, subconsulta, ranking).

**MongoDB:** `curriculos_redigidos`, `extracoes_llm`, `avaliacoes_llm`, `explicacoes`, `fontes` (procedência §5.3), `snapshots_adzuna`, `model_cards`. Ligação por IDs estáveis.

**RDS:** `ocorrencias` + `evento_id UNIQUE` + `autenticado BOOLEAN` (PostgreSQL suporta).

---

## 4. Catálogo de comportamentos TDD (ordem de execução)

Cada linha é uma fatia **RED → GREEN → REFACTOR**, testada pela interface pública. Os IDs T01–T17 vêm da proposta, e os T18+ são novos.

| Fatia | Comportamentos | Camada |
|---|---|---|
| S0 Esqueleto | Compose sobe; `GET /health` da API; pytest/vitest verdes vazios; `limiares.json` carregado | infra |
| S1 Limiares | Os 3 cenários classificam igual na API e na Lambda (tabela compartilhada de casos); fronteiras 35/45/8/15 | domínio |
| S2 Leituras CTP | **T09**, **T10**, 401 sem chave, 503 se o CSV falhar, indicador; **roda isolado sem Oracle** (R16) | API |
| S3 Outbox | **T12**, **T13** (fake Lambda), estado `pendente_nuvem` → `sincronizado` | worker |
| S4 Lambda | 400 / sem chave → `autenticado=false` / 401 chave inválida / 429 / 201 / 200-duplicata / 409, **T11** (HF fora), logs WARNING; contrato contra Postgres em Docker; **o simulador oficial do professor (sem header) recebe 201** | cloud |
| S5 Auth | registrar/login, cookie, **T14** (A não lê B → 404), **T16** (429; sem segredo em erro), **CSRF: mutação sem `X-CSRF-Token` → 403** (R20) | API |
| S6 Ingestão Caged | **T01**, **T02** (duplicatas MOV/FOR/EXC), **T03** (ausente ≠ zero), procedência com hash; **atributos sensíveis (idade, sexo, raça/cor, deficiência) descartados na ingestão** (R05) | ml |
| S7 Features/split | **T04** (embargo: nenhuma linha de treino com alvo além da fronteira), **T05** (alterar o futuro não muda as features do passado), **T18**: um FOR declarado depois de *t* não altera as features em *t* (R02); **T19**: série abaixo do limiar de densidade é excluída (R03) | ml |
| S8 Mercado API | **T06** (série insuficiente → abstém), **T17** (metadados obrigatórios na resposta) | API |
| S9 Currículo/PII | PII redigida antes da LLM; **nada chega à LLM sem a confirmação do usuário** (R18); arquivo > 2 MB → 400; original não persistido; **T15** | API |
| S10 Extração | Só IDs da lista fechada; item sem trecho de origem é descartado; **T07** | API |
| S11 Comparação | Obrigatório não atendido nunca some em média; desconhecido ≠ lacuna; ≤ 3 destinos | domínio |
| S12 Plano | Lacunas → atividades ordenadas por pré-requisito; checkpoints | domínio |
| S13 Avaliação | 50/50; LLM fora → "parcial"; GET sem gabarito; "discordo" registra; **T08**; 4ª tentativa em 24 h → 429 (R23) | API |
| S14 Laboratório | Sessão + código; leituras da sessão; relato ≤ 280 com PII redigida segue pela outbox | API |
| S15 Web | Jornada E2E Playwright (persona demo) + axe sem violações sérias | web |

**Regras:** fake do LLM e da Lambda na fronteira; Oracle e Postgres reais em Docker nos testes de integração; nenhum teste exige uma métrica de modelo específica.

---

## 5. Cronograma

| Dia | Data | Frente A (orquestrador + agy) | Frente B (agy) | Gate de saída |
|---|---|---|---|---|
| **D1** | Qui 12 – Sex 13 | Aprovação deste plano; Docker ativo + smoke do `oracle-free` (R26); S0, S1; `.env.example`; Astryx smoke build; **pipeline md→pdf (Edge) + contador de páginas** (R10); issues | **Ingestão Caged** (S6) em streaming: baixar → filtrar CBO6 → **salvar linhas filtradas em Parquet** (R05) → apagar o bruto; abortar se o disco livre ficar abaixo de 4 GB; confirmar os códigos CBO6 dos 6 destinos; snapshot Adzuna | Parquet real em `app/data/`; códigos CBO confirmados; build web OK; PDF de teste gerado |
| **D2** | Sáb 14 | S2, S3, S5; **rascunho por agente** do catálogo YAML dos 6 destinos (ESCO, questões, rubricas) (R29) | S7 + EDA + medição da defasagem FOR (R02) + baselines; **congelar** split e promoção (já fixados aqui) | Leituras ponta a ponta local; baselines medidos |
| **D3** | Dom 15 | S9, S10, S11; **[HUMANO] revisão das rubricas (~2 h); sem revisão até 18h → corte automático para 3 destinos** (R29) | ML (Ridge/RF/HGB + tuning) + RNA (MLP, ≥ 2 configs); Estatística (base municipal + script) | Validação comparada; promoção decidida; teste aberto 1x |
| **D4** | Seg 16 | S4 Lambda + deploy Learner Lab + RDS (SG por janela) + HF; firmware Wokwi DS18B20/HC-SR04/LED/buzzer | S8, S12, S13; Oracle DDL 19c + Mongo; **[HUMANO] Data Modeler (~30 min)** (R11) | 4 prints de Cloud; **[HUMANO] vídeo Cloud** (R15) |
| **D5** | Ter 17 | S14 + integração outbox → Lambda real; gravar a **demonstração dos 3 cenários AICSS/CTP** como evidência | S15 frontend (impeccable + Astryx), todas as telas; **[HUMANO] vídeos ML e RNA** | Jornada completa em uma persona |
| **D6** | Qua 18 | Revisão independente (agy plan) + correções; segurança demonstrada; Oracle FIAP (evidências); **[HUMANO] vídeos Cyber e AIC** | Relatórios .md + evidências .html → PDFs finais (9 disciplinas); UML Mermaid; notebooks finais | Checklist §17 da proposta; PDFs dentro do limite de páginas |
| **D7** | Qui 19 | **[HUMANO]** conferência de checklist, links e formatos; entrega no Portal até 23h55; **abrir o SG do RDS para o período de correção** (D09) | Margem de correção | Entregue |

**Leitura do cronograma em16/11:** esta tabela é o alvo original, não prova de execução. O gate D3 de abrir teste **não autoriza** abrir holdout: a instrução humana vigente mantém2026 fechado. Consulte estado.md para o checkpoint real e não repita S0/S5/treinos concluídos.

**Paralelismo:** no máximo 2 agentes `agy` simultâneos, com caminhos de escrita disjuntos e **um worktree cada**. A Frente B do D1 (dados) é o caminho crítico do ML/RNA/Estatística.

**Orçamento do orquestrador (R30):** testes completos em toda fatia. Leitura integral do diff só nas fatias com revisor independente (S3, S4, S5, S7, S9, S13); nas demais, por amostragem.

---

## 6. Execução multiagente

### 6.1 Papéis

- **Orquestrador (esta sessão):** contratos, este plano, issues, aceite de cada fatia (lê o diff, reexecuta os testes, tenta um contraexemplo), integração e testes de integração.
- **Implementadores `agy`:** uma fatia por chamada, com escopo de escrita exclusivo.
- **Revisor independente `agy --mode plan`:** obrigatório para S3/S4 (resiliência e nuvem), S5/S9 (segurança/PII), S7 (vazamento temporal) e S13 (avaliação/LLM).

### 6.2 Allowlist de comandos (regra explícita do contrato de cada delegação)

Por estar em uso o `--dangerously-skip-permissions`, todo prompt **lista literalmente** o que é permitido. Qualquer comando fora da lista é proibido, e o agente deve parar e reportar.

| Permitido | Restrição |
|---|---|
| Ler arquivos do repo | **Nunca** `.env*` (exceto `.env.example`), `~/.aws`, `~/.ssh` |
| Criar/editar arquivos | **Somente** nos caminhos de escrita declarados no contrato |
| `uv run pytest …`, `uv run ruff …`, `uv run python <script em app/>` | Dentro do componente; nunca Python/pip globais |
| `uv sync`, `uv add …`, `pnpm install`, `pnpm add …` | Só dentro de `app/*`, respeitando os locks; sem `-g` |
| `pnpm run test\|build\|lint\|typecheck`, `pnpm exec playwright test` | Só em `app/web` |
| Conexão aos serviços locais de teste | O orquestrador os mantém; **docker é proibido ao implementador** |
| `git status`, `git diff`, `git log` | **Proibido:** commit, push, reset, checkout, clean, rebase, stash |
| Rede | Só registries de pacotes, FTP do MTE (agente de dados) e docs públicas |
| **Proibido sempre** | `aws`, chamadas reais a OpenRouter/Adzuna/HF, apagar arquivos fora do escopo, alterar `settings.json`/credenciais, desativar testes, `--no-verify` |

**Procedimento operacional atualizado em16/11:** prevalece a allowlist literal de CLAUDE§7.3, que deve ser colada no contrato. Exemplos antigos com pip/Python globais ou docker pelo agente não são autorização. Antes e depois de cada chamada, o orquestrador registra os snapshots e compara o escopo. **Commits são feitos só pelo orquestrador**, depois do aceite e do gitleaks.

### 6.3 Invocação padrão (isolamento R22)

```powershell
# Executar a partir de REPO; gate de dependências e contrato já concluídos.
$R = 'C:\Users\orugi\Documents\Projetos\FIAP\GS'; $S = 'S8-mercado'
git -C "$R\info-gs-diciplinas" worktree add "$R\GS-wt\$S" -b "fatia/$S"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git -C "$R\GS-wt\$S" rev-parse HEAD > "$R\.kaiser\snapshots\$S-base.txt"
'AWS_*','OPENROUTER_*','HF_*','MONGODB_*','ADZUNA_*','DEVICE_KEY*','DB_*','ORACLE_*','JWT_*' |
  ForEach-Object { Get-ChildItem "env:$_" -ErrorAction SilentlyContinue } |
  ForEach-Object { Remove-Item "env:$($_.Name)" }
$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'
# Real .dados só quando o contrato autorizar expressamente a leitura.
$env:CITIZENTECH_DADOS="$R\.kaiser\tmp\dados-nao-reais"
$env:CITIZENTECH_TMP="$R\.kaiser\tmp"
Push-Location "$R\GS-wt\$S"
Get-Content -Raw -Encoding utf8 "$R\.kaiser\contratos\$S.md" |
  agy --model gemini-3.8-flash-high --dangerously-skip-permissions --print-timeout 45m 2>&1 |
  Out-File -Encoding utf8 "$R\.kaiser\reports\$S.md"
$resultado=$LASTEXITCODE
Pop-Location
git -C "$R\GS-wt\$S" status --porcelain --untracked-files=all > "$R\.kaiser\snapshots\$S-depois.txt"
exit $resultado
```

Revisão independente: nova chamada, `--mode plan --print-timeout 20m`, **sem** `--dangerously-skip-permissions`, sem relatório autoral. Nunca usar timeout0s. O próprio orquestrador mantém os serviços de teste e registra o ID do job em estado.md; no máximo2agy simultâneos.

Cada contrato segue o modelo da proposta (§14 "Contrato obrigatório por delegação"), acrescido da allowlist da §6.2. Os jobs rodam em background com ID registrado e timeout operacional de 45 min; a falha é reportada e a fatia replanejada, sem repetição indefinida.

---

## 7. Dados — tarefas concretas do D1

1. **Caged:** `ftp://ftp.mtps.gov.br/pdet/microdados/NOVO CAGED/{AAAA}/{AAAAMM}/CAGED{MOV,FOR,EXC}{AAAAMM}.7z`, cerca de 81 competências (MOV ≈ 35–50 MB compactado cada). Pipeline em streaming (`py7zr` + leitura em chunks): filtrar pelas CBO6 dos destinos → agregar por competência × UF × CBO × escolaridade × tipo de movimentação (+ salário para a Estatística) → apagar o bruto. MOV + FOR são somados por **competência da movimentação**, e EXC é subtraído. A regra fica documentada e testada (T02). Registrar procedência (URL, data, hash, layout `Layout Não-identificado Novo Caged Movimentação.xlsx`).
2. **CBO/ESCO:** confirmar os códigos de 6 dígitos de cada destino na tabela oficial da CBO; mapear 8–15 competências ESCO pt por destino, com requisito obrigatório ou desejável.
3. **Adzuna:** script idempotente com contador local de chamadas, que aborta acima de 12. Os resultados são guardados em `app/data/adzuna/AAAAMMDD/`. As condições de uso e a atribuição são registradas em `fontes`.

---

## 8. Mapa de entregas por disciplina

| Disciplina | O que sai do app/ | Artefato de entrega |
|---|---|---|
| 01 AICSS | `app/iot/firmware` (Wokwi), 3 cenários, LED/buzzer, POST para a API | `relatorio.md` + `evidencias/*.html` (Serial, JSON, CSV) |
| 02 Cyber | Auth/autorização, CSRF, rate limit 429, X-Device-Key 401 + flag `autenticado`, PII com confirmação, gitleaks, exceção RDS, isolamento de agentes | relatório .md (≤ 15 páginas no PDF) + vídeo ≤ 5 min [HUMANO] |
| 03 Data Science | `app/db/oracle`, `app/db/mongo`, consultas | DDL 19c + **modelo lógico e relacional no Data Modeler [HUMANO, obrigatório]** + evidências da execução no Oracle FIAP + justificativa da divisão Oracle/Mongo |
| 04 CTP | `POST/GET /leituras`, CSV, indicador, 3 cenários; **modo isolado** | `documento.md` + evidências .html + testes (o enunciado local não pede vídeo) |
| 05 ML | `app/ml` (baselines, Ridge/RF/HGB, tuning, importância) | `notebook.ipynb` + slides (.md → PDF) + vídeo ≤ 5 min [HUMANO] |
| 06 Cloud | `app/cloud` (Lambda, SQL, simulador direto) | README + 4 imagens + Function URL + endpoint + vídeo ≤ 5 min [HUMANO] |
| 07 RNA | MLP PyTorch, curvas, configs, demo com dados não vistos; servida em `/mercado/{d}/modelos` | `notebook.ipynb` + **vídeo obrigatório (1 ponto)** [HUMANO] |
| 08 Estatística | Base municipal SP 2025 (CSV/XLSX), `analise.py` autônomo | **`.pdf` + `.py` + `.csv`** enviados diretamente (−2 pontos se o formato estiver errado) |
| 09 AIC | Jornada completa + UML Mermaid + Kanban GitHub Projects + ODS 4/10(/8) | vídeo ≤ 7 min, rosto, sem música, nomes/RMs [HUMANO] |

---

## 9. Riscos do plano e mitigação

| Risco | Mitigação / gatilho |
|---|---|
| Séries CBO6 superior+ esparsas | Regra de densidade pré-registrada (D04a); abstenção por UF; registrar a cobertura efetiva |
| Disco insuficiente para o Caged | Streaming com exclusão do bruto; abortar se o espaço livre ficar abaixo de 4 GB (o Oracle Docker também ocupa disco) |
| Astryx beta quebra o build | Smoke test no D1; plano B Radix + Tailwind sem retrabalho de lógica |
| `agy` falha ou sai do escopo | Snapshot antes e depois; reverter só os arquivos da fatia; replanejar ou executar pelo orquestrador |
| Sessão de 4h do Learner Lab | Scripts de deploy idempotentes; gravar a evidência Cloud cedo (D4). **Não verificado:** se o RDS e a Function URL respondem fora das sessões e depois do fim do lab; confirmar no D4 e, se não responderem, avisar o professor no README |
| Reserved concurrency recusada pela conta | Usar o limite da conta + rate limit por dispositivo no RDS (R24) |
| Revisão humana das rubricas não acontece | Corte automático para 3 destinos no D3, às 18h (R29) |
| OpenRouter/modelo indisponível | Fallback por env; avaliação "parcial" e explicação omitida, com aviso |
| Oracle FIAP inacessível | As evidências de execução vêm do Docker Oracle Free, com a limitação declarada |
| Holdout "espiado" | Teste aberto só pelo script `avaliar_teste.py`, que grava hash e data da execução única |

---

## 10. Pendências [HUMANO] (não bloqueiam a Fase 1)

- [x] Nomes completos e RMs: Guilherme Orugian (RM572882), Lucas Henrique (RM571901), Rodrigo Bettio (RM573725).
- [ ] Ideia efetivamente extraída da live de 04/11 (para AIC).
- [ ] Quem grava cada vídeo e quem entrega cada disciplina no Portal.
- [ ] Preencher o `.env`: `OPENROUTER_API_KEY`, `ADZUNA_APP_ID/KEY`, `HF_TOKEN`, `MONGODB_URI`, `DEVICE_KEY`, credenciais do RDS.
- [ ] Revisar as rubricas dos **3 destinos mantidos após R29** (registrar revisor/mínimos). O gate original D3 às18h expirou; os seis rascunhos foram preservados, não aprovados.
- [ ] **Data Modeler** no D4 (obrigatório, R11); confirmar o campo de envio do vídeo de RNA.
- [ ] `gh auth refresh -s project,read:project` (R28).
- [x] **Tamanho do grupo:** trio, compatível com a Estatística (R09).
- [x] Primeiro smoke Docker executado no D1 (R26). Isso não garante serviços ativos hoje: o orquestrador deve reconferir quando a fatia precisar de banco.
- [ ] (Opcional) Comunicar ao professor de Cloud a exceção de rede do RDS.

---

## 11. Próximo passo

**Checkpoint16/11:** a fase inicial, S5 e experimentosML/RNA/D11 já estão integrados; não reiniciar S0/S1 nem retunar com2025. Próxima fatia recomendada: **S8 Mercado API/model cards/R06**, após ler§3 e conferir acessos/interfaces. Em paralelo sem sobreposição, finalizar notebooks/entregáveis científicos. S9–S11, Cloud/firmware e S12–S15 ainda precisam ser executados conforme dependências e gates humanos. [Estado atual](<docs/estado.md>) é a entrada operacional; holdout permanece fechado e não há autorização de push.
