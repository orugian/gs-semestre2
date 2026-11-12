# Revisão adversarial — Plano de desenvolvimento v1.0

**Data:** 12/11/2026 · **Objeto:** [plano_desenvolvimento.md](plano_desenvolvimento.md)
**Fontes da revisão:**
1. Verificação do orquestrador contra o repositório e o ambiente: layout e Leia-me do Novo Caged no FTP do MTE, API de modelos do OpenRouter, npm do Astryx, documentação de concorrência da AWS Lambda, ferramentas instaladas, `gh` e Docker.
2. Revisor independente A, conformidade acadêmica: [REV-A-academico.md](../../.kaiser/reports/REV-A-academico.md).
3. Revisor independente B, viabilidade técnica, metodologia e segurança: [REV-B-tecnico.md](../../.kaiser/reports/REV-B-tecnico.md).

Os achados dos revisores foram **adjudicados**: aceitos, aceitos parcialmente ou rejeitados, sempre com motivo. Nenhum achado foi aceito apenas porque o revisor o afirmou.

---

## 1. Achados aceitos

Severidade: **B** = bloqueador · **A** = alto · **M** = médio · **Bx** = baixo.

### Metodologia ML / dados

| ID | Sev | Achado | Evidência | Correção |
|---|---|---|---|---|
| R01 | **A** | **O split anunciado contradiz o embargo.** Com treino até *t* = dez/2024, o alvo do último treino cobre jan–mar/2025, que se sobrepõe à janela dos alvos da validação, que começa em jan/2025. O mesmo acontece entre a validação (dez/2025) e o teste (jan/2026). | D04 + D10 (REV-B #1, aceito) | Expurgar no treino toda linha cujo alvo atravesse a fronteira. Ficam: **treino *t* ≤ set/2024 · validação *t* jan–set/2025 · teste *t* jan–jun/2026**. O modelo final do app é retreinado com tudo o que tem rótulo, até *t* = jun/2026, **depois** do teste, e isso é declarado. |
| R02 | **A** | **Revisões do Caged quebram o "point-in-time" (T05).** Pelo Leia-me oficial, os arquivos FOR trazem movimentações declaradas fora do prazo com a competência da *declaração*, e EXC traz cancelamentos retroativos. Se as features em *t* usarem MOV+FOR−EXC consolidados, elas incluem declarações feitas depois de *t*. Além disso, os alvos dos meses mais recentes (jul–set/2026) ainda vão receber FOR, ficam subcontados e enviesam o teste. | Leia-me do FTP do MTE; layout com `competênciamov`, `competênciadec` e `competênciaexc` | **Features:** só registros com `competênciadec ≤ t`. **Alvo:** contagem consolidada por `competênciamov`. Medir no histórico a fração de FOR por defasagem. Se ela passar de 2% nos últimos meses do teste, cortar esses meses ou declarar o viés. Tudo isso decidido **antes** de abrir o teste. |
| R03 | **M** | **Esparsidade das séries destino × UF × superior+.** Em UFs pequenas (AC, AP, RR) as séries de destinos como IoT/automação tendem a ser quase só zeros. O plano tinha um fallback, mas sem regra numérica. | D04a (REV-B #7, aceito parcialmente) | Regra pré-registrada: uma série entra no treino e na avaliação só se a **média do alvo no treino for ≥ 10 admissões por trimestre**. Abaixo disso, o app **se abstém** naquela UF (T06) e exibe o agregado regional como contexto. A sugestão do revisor de usar a família CBO de 4 dígitos foi **rejeitada** porque recria a dupla contagem; ver R04. |
| R04 | **M** | **A mudança de família CBO para CBO6 não foi aprovada pelo usuário.** A resposta à Q4 foi "família CBO × 27 UFs", e o plano mudou isso sozinho em D04a. | D04 vs D04a | Confirmar com o usuário (pergunta 4). Vários destinos de TI caem na família 2124, então usar família conta a mesma população em mais de um destino. |
| R05 | **M** | **Só uma passada de download.** O Estatística precisa de município e salário, e o ML precisa de UF, escolaridade e competências. Se o D1 baixar só os agregados do ML, será preciso baixar o Caged de novo (cerca de 81 arquivos e 3,6 GB). | §7 | Guardar as **linhas filtradas**, apenas das CBO6 dos 6 destinos, em Parquet com todas as colunas não sensíveis: competências, UF, município, CBO, grau de instrução, tipo de movimentação, salário, horas, saldo e indicadores de aprendiz/intermitente. **Excluir** idade, sexo, raça/cor e deficiência na própria ingestão (minimização). |
| R06 | **M** | **O critério de promoção pode tirar a RNA e o ML do app**, e a RNA vale 1 ponto em "integração". | D10a (REV-B #2, aceito parcialmente) | **Manter** o critério de promoção para o número mostrado ao usuário. Os modelos não promovidos continuam servidos pela API e aparecem no **painel técnico**, que já está previsto na proposta §3, com métricas lado a lado (`GET /mercado/{d}/modelos`). A correção do revisor ("expor sempre a RNA ao usuário") foi **rejeitada** por desonestidade científica. |

### Estatística

| ID | Sev | Achado | Correção |
|---|---|---|---|
| R07 | **A** | **A logística é tautológica.** `crescimento > 0` é definido a partir das admissões de 2025 contra 2024. Usar admissões/desligamentos de 2025 como explicativas praticamente reconstrói o alvo. | Explicativas **sem relação com o cálculo do alvo**: salário médio de admissão, % de superior+ e participação dos destinos no emprego formal municipal, todos medidos em **2024**. Alvo: crescimento entre 2024 e 2025. Matriz de confusão em amostra de teste estratificada. |
| R08 | **M** | Contagens e salários municipais são muito assimétricos. Assumir a Normal sem diagnóstico enfraquece as questões 02 e 03. | O enunciado **manda** assumir a Normal, então ela é mantida. Mostrar histograma, Shapiro/QQ e uma análise com `log(1+x)` como **complemento**, sem substituir os itens (REV-B #3, aceito parcialmente). |
| R09 | **M** | **O enunciado de Estatística aceita grupos "individual, em dupla ou em trio".** Se o grupo tiver mais de 3 pessoas, há conflito de entrega. | **[HUMANO]** Confirmar o tamanho do grupo e como fazer a entrega de Estatística. |

### Conformidade acadêmica

| ID | Sev | Achado | Correção |
|---|---|---|---|
| R10 | **A** | **Formatos.** Estatística exige `.pdf` + `.py` + `.csv/.xlsx`, com desconto de 2,0 pontos por entrega inadequada. Cyber exige PDF de até 15 páginas. ML exige slides PPT ou PDF. D19 deixava a conversão para o D6, e **não há pandoc nem LibreOffice** na máquina. | Pipeline **md → html → pdf** com **Edge headless** (`msedge --headless --print-to-pdf`, Edge confirmado instalado), criado já no D1 e usado em cada rascunho, com **contagem automática de páginas** (falha acima de 15 no Cyber). Slides de ML em HTML e depois PDF. O HTML de evidências continua, como pedido. |
| R11 | **A** | **Data Science cita ferramenta de modelagem** ("MySQL/Oracle Data Modeler, Oracle SQL Developer / DbDesigner"). O plano tratava isso como "se exigido". | Tarefa **[HUMANO] obrigatória no D4, de cerca de 30 min**: importar o DDL no SQL Developer Data Modeler, gerar os modelos lógico e relacional e exportar imagem/PDF. Os agentes não operam GUI. |
| R12 | **A** | **Pertinência dos sensores com público amplo** (AICSS: 2 pontos para "justificativa dos sensores"; Cloud: "o que o morador escreveu ao registrar o problema"). O lab opcional de um único destino é o elo mais fraco da coerência "mesmo problema, público e contexto". Esse risco já tinha sido sinalizado no nivelamento. | Reabrir a decisão (pergunta 1). Proposta: o app continua amplo, mas **a persona do piloto e as narrativas de AICSS, CTP e Cloud** passam a ser o profissional de operações/manutenção em transição para monitoramento. O relato vira um "relatório de incidente de campo". |
| R13 | **A** | **O avaliador pode receber 401.** O simulador oficial ([simulador_dispositivo.py](../06_Cloud/simulador_dispositivo.py)) não envia `X-Device-Key`. Se o professor fizer um POST com só os 3 campos obrigatórios, a resposta é 401 e o critério de ingestão (25%) cai. | Decisão do usuário (pergunta 2). |
| R14 | **A** | **Disponibilidade da Function URL depois da entrega.** Com o SG do RDS aberto "só nas janelas", qualquer teste do professor fora delas falha no banco. A sugestão do revisor B de restringir ao IP `/32` do desenvolvedor **não funciona**, porque a Lambda fora de VPC sai por IPs dinâmicos da AWS; o revisor A apontou isso corretamente. | Decisão do usuário (pergunta 2). A disponibilidade no Learner Lab entre sessões **não foi verificada**: ver §3. |
| R15 | **M** | Todos os vídeos estavam no D7: cinco gravações com rosto, mais upload e checagem de links. | Distribuir: **Cloud no D4** (e a gravação dos 3 cenários AICSS/CTP como evidência no D5; os enunciados locais dessas duas não pedem vídeo), **ML e RNA no D5**, **Cyber e AIC no D6**. O D7 fica só para checklist e Portal (REV-B #6, aceito). |
| R16 | **M** | O professor de CTP pode querer rodar a API isoladamente ("Interface gráfica, banco de dados e IA não são obrigatórios"), mas a API integrada depende de Docker e Oracle. Além disso, `GET /leituras` exigia login. | O módulo `leituras` deve rodar **sozinho** (`uvicorn` + CSV, sem Oracle) com um comando, e a app integrada importa o mesmo módulo. Com a chave de dispositivo, `GET /leituras` aceita a chave **ou** o cookie do dono. |
| R17 | **Bx** | O sentimento do relato de incidente é avaliado por um modelo treinado em tweets. | Sentimento = **tom do relatório de incidente** (urgência), guardado como metadado da ocorrência. **Nunca** entra na nota de competência. Isso fica declarado no README de Cloud (REV-A contraexemplo 4, aceito). |

### Segurança / LGPD

| ID | Sev | Achado | Correção |
|---|---|---|---|
| R18 | **A** | **A redação de PII por regex não remove o nome da pessoa**, que é o dado pessoal mais evidente de um currículo e costuma estar na primeira linha. | Antes da LLM, a tela mostra o **texto redigido para revisão e edição** pelo usuário, que confirma o envio. Acrescentar heurística para remover o cabeçalho (primeiras linhas com nome). Para Cyber, declarar que a redação é parcial. |
| R19 | **A** | **Transferência internacional e retenção (LGPD art. 33).** O OpenRouter e o provedor do DeepSeek recebem texto de currículo; o Atlas pode estar fora do Brasil. | Configurar no OpenRouter `provider.data_collection: "deny"` e, se disponível, roteamento sem retenção. Consentimento específico citando operador e país. Criar o Atlas em São Paulo (`sa-east-1`) se o M0 permitir; senão, declarar a região. |
| R20 | **A** | **CSRF.** JWT em cookie httpOnly sem SameSite nem token protege mal as rotas mutáveis `/me/*`. | `SameSite=Lax` + `Secure` + **token CSRF double-submit** (header `X-CSRF-Token`) em POST/PUT/PATCH/DELETE. Teste incluído na S5 (REV-B #5, aceito). |
| R21 | **M** | **A chave do dispositivo fica exposta no firmware.** No Wokwi web o código-fonte é visível. Para alcançar a API local é preciso um túnel (ngrok, que está instalado), o que expõe a FastAPI à internet. | A chave de dispositivo é **específica da demo**, rotacionável, só vale para `POST /leituras` e tem rate limit próprio. Projeto Wokwi privado. O túnel é aberto apenas durante a demonstração. Firmware com `WiFiClientSecure` (limitação de verificação de CA documentada). |
| R22 | **A** | **`--dangerously-skip-permissions` com allowlist apenas textual** não impede o agente de executar comandos fora da lista nem de ler segredos do ambiente (REV-B #4, aceito parcialmente). | Isolar sem Docker, que nem sempre está ativo: (1) **um `git worktree` por fatia** em `..\GS-wt\<fatia>`, então um dano fica confinado e é descartável; (2) agy lançado com **ambiente limpo**, sem `AWS_*`, `OPENROUTER_*`, `HF_*` ou `MONGODB_*`; (3) `.env` real **fora** do diretório do worktree; (4) diff do worktree comparado com o escopo declarado antes de qualquer merge. O container sugerido pelo revisor fica como opção se Docker estiver estável. |
| R23 | **M** | **"Refazer" permite repetir até passar.** A nota LLM é não determinística, então quem refaz várias vezes acaba atingindo o mínimo. | `temperature=0`, cache da nota por hash da resposta, **no máximo 3 tentativas por exercício a cada 24 h** e todas as tentativas registradas (com a última e a melhor visíveis). |
| R24 | **M** | **Reserved concurrency pode ser impossível no Learner Lab.** A AWS só permite reservar até "unreserved account concurrency − 100", e contas acadêmicas costumam ter limite baixo. | Tentar. Se falhar, usar o próprio limite da conta como teto e documentar. No banco, um **limite por `dispositivo_id`/minuto**, verificado no RDS antes do INSERT. |

### Arquitetura / operação

| ID | Sev | Achado | Correção |
|---|---|---|---|
| R25 | **M** | **SQLite com WAL compartilhado entre containers em bind mount do Windows** tem locking pouco confiável. | O worker da outbox roda **no mesmo processo da API** (tarefa de fundo) e o SQLite fica em um **volume nomeado** do Docker, nunca em bind mount. |
| R26 | **M** | **Docker Desktop estava parado** na verificação, e o Oracle Free consome alguns GB de disco, que competem com os ~12 GB livres e a ingestão do Caged. | O D1 começa com o Docker ativo e um teste de fumaça do `oracle-free`. Gate de disco: a ingestão aborta se o espaço livre ficar abaixo de 4 GB. |
| R27 | **M** | **DDL Oracle 23ai vs Oracle FIAP**, possivelmente 19c. | DDL restrito ao **dialeto 19c**: sem `BOOLEAN`, sem `IF [NOT] EXISTS`, sem domínios SQL (REV-B #8, aceito). |
| R28 | **M** | **O token do `gh` não tem o escopo `project`**, então o GitHub Projects não funciona. | **[HUMANO]** `gh auth refresh -s project,read:project` (interativo). Até lá, as issues vão para o repositório. |
| R29 | **M** | **Gargalo humano na curadoria.** Seis destinos × (8–15 competências ESCO + 3–5 questões + rubrica) são produzidos por LLM, mas o plano exige revisão do grupo, e isso não tinha tempo alocado. | Agentes geram os rascunhos no D2. Revisão **[HUMANO] no D3, cerca de 2 h**. Se a revisão não acontecer, o corte (a) de 6 para 3 destinos entra automaticamente no D3, às 18h. |
| R30 | **Bx** | O orçamento de tokens do orquestrador não estava previsto: aceitar 15 fatias com leitura de diff e reexecução de testes é caro. | Aceite em lote: testes completos sempre e leitura integral do diff apenas nas fatias marcadas para revisão independente (S3, S4, S5, S7, S9, S13). Nas demais, leitura por amostragem. |

---

## 2. Achados rejeitados

| Origem | Achado | Motivo da rejeição |
|---|---|---|
| REV-B #5b | Restringir o SG do RDS ao IP `/32` do desenvolvedor | Incompatível com Lambda fora de VPC, que tem IP de saída dinâmico. Testes falhariam com timeout. |
| REV-B #7 | Consolidar na família CBO de 4 dígitos | Recria a dupla contagem entre destinos de TI. A esparsidade é tratada por R03. |
| REV-B #8b | Risco de ERESOLVE do Astryx com React 19 | Verificado no npm: `@astryxdesign/core@0.7.14` declara peer `react >=19` e `@stylexjs/stylex ^0.19`. O risco que resta é ser beta e mudar com frequência (publicado hoje), e isso já é coberto por versão fixada + plano B. |
| REV-B #9 | Simulador da Cloud acoplado à web | O plano (D13) já mantém o simulador direto para a Function URL como evidência separada. |
| REV-B contraexemplo 2 | Suspensão da conta por scan na porta 5432 | Não há evidência dessa política. O risco real de exposição já está em R14 e R22. |
| REV-A #1b | Abrir 0.0.0.0/0 sem restrição de tempo | Não foi aceito como padrão. Vai como alternativa na pergunta 2. |
| REV-A #5 | Vídeo de RNA ausente do plano | Já estava no D7 do plano. Fica só a redistribuição de R15. |

---

## 3. Fatos verificados e não verificados

**Verificados (12/11/2026):** competências do Novo Caged de 202001 a 202609 no FTP; o layout tem `competênciamov`, `competênciadec`, `competênciaexc`, `graudeinstrução` (inclui "Superior Completo", "Mestrado" e "Doutorado"), `município`, `salário` e `saldomovimentação`; `deepseek/deepseek-v4.1-flash-1017` existe no OpenRouter com `response_format` e `structured_outputs`; o Astryx 0.7.14 tem as peer deps citadas; o Edge está instalado (pandoc e LibreOffice não); o ngrok está instalado (arduino-cli e PlatformIO não); a máquina tem 31,8 GB de RAM; o repositório `insonia999/GS2_26` é privado; o token do `gh` não tem escopo `project`; o Docker daemon estava parado.

**Não verificados:** comportamento do RDS e da Function URL entre sessões do Learner Lab e depois do fim do lab; limite de concorrência Lambda da conta acadêmica; disponibilidade do M0 em `sa-east-1`; versão do Oracle FIAP; termos de cache/armazenamento da Adzuna para o snapshot; velocidade do FTP do MTE; tamanho do grupo.

---

## 4. Decisões do usuário sobre os achados abertos (12/11/2026)

1. **R12 (coerência IoT):** **manter** o laboratório como trilha opcional, com público amplo. Risco aceito e registrado em D01. Mitigação: o relatório de AICSS justifica os sensores como instrumento de avaliação prática da competência de monitoramento.
2. **R13/R14 (Lambda para o avaliador):** **chave opcional** (sem chave → aceito com `autenticado=false` + rate limit; chave inválida → 401) e **RDS aberto de 19/11 até o fim da correção**, com TLS obrigatório e usuário de menor privilégio. Aplicado em D09 e D09a.
3. **R04 (unidade ocupacional):** **CBO6 disjunto confirmado**, com abstenção nas séries abaixo de 10 admissões por trimestre. Aplicado em D04a.

Todos os demais achados aceitos foram aplicados ao [plano v1.1](plano_desenvolvimento.md).
