# CitizenTech — Modelagem e implementação dos dados (Oracle + MongoDB)

**Disciplina:** Cognitive Data Science · **Global Solution 2026.2**

**Integrantes (nome completo + RM):**

- Guilherme Orugian — RM572882
- Lucas Henrique — RM571901
- Rodrigo Bettio — RM573725

> Tudo o que aparece como resultado neste relatório foi **executado** em 16/11/2026 no Oracle local (Docker, imagem Oracle Free 23ai, DDL escrito no dialeto 19c) e no MongoDB Atlas do projeto. As saídas completas estão em `evidencias/`. O Oracle da FIAP ficou fora do escopo por decisão do grupo (credencial recusada com ORA-01017); o mesmo DDL roda nele sem mudança porque usa só recursos do 19c.

## 1. Contexto: que dados a solução trata

A CitizenTech ajuda profissionais graduados e experientes em transição de carreira a comparar destinos com base em evidências. Os dados se dividem em quatro grupos:

| Grupo | Exemplos | Onde fica |
|---|---|---|
| Conta, consentimento e decisões da pessoa | usuário, consentimentos por finalidade, intenção, competências revisadas, comparações, plano e checkpoints, tentativas do exercício, sessão de laboratório | **Oracle** |
| Catálogo curado | destinos, ocupações CBO, competências ESCO, requisitos de cada destino | YAML versionados (fonte) → **Oracle** (projeção relacional para consulta) |
| Textos e documentos de formato variável | texto **redigido** do currículo, metadados das extrações por IA, avaliações da IA em cache, respostas abertas redigidas, *model cards* dos modelos de mercado | **MongoDB** |
| Leituras de sensores e mercado | leituras da bancada (CSV + outbox), série de admissões do Novo Caged | CSV/SQLite locais e snapshot versionado com hash (fora do escopo deste relatório) |

## 2. Modelagem relacional (Oracle)

**Arquivos:** `app/db/ddl/001_usuario_consentimento.sql` a `007_catalogo.sql` (cópia consolidada em `03_DataScience/oracle.sql`). São **16 tabelas** com chaves primárias, estrangeiras (com `ON DELETE CASCADE` a partir de `usuario`, exceto em `consentimento`, ver §5), `CHECK` de domínio (estados, finalidades, faixas numéricas), `UNIQUE` e índices de acesso.

**Diagrama entidade-relacionamento:** `docs/uml/img/06_6_modelo_de_dados_relacional_oracle_ddl_001007.png` (gerado do mesmo DDL). **DER do Oracle Data Modeler:** [AGENTE — execução pendente: importar o DDL no Modeler real, gerar modelos lógico/relacional, salvar projeto nativo e exportar imagens. Responsabilidade transferida pelo usuário em17/11/2026; não confundir Mermaid com essa execução].

Principais decisões de modelagem:
- **Dialeto 19c:** sem `BOOLEAN` (flags em `CHAR(1)` com `CHECK IN ('S','N')`), sem `IF NOT EXISTS`, sem tipo `JSON` nativo. Documentos que precisam ficar junto da linha (ex.: o resultado de cada destino numa comparação) vão em `CLOB`/`VARCHAR2` com `CHECK (coluna IS JSON)`, consultáveis com `JSON_VALUE`.
- **Rastreabilidade:** cada comparação guarda o resultado completo por destino, na ordem escolhida (`comparacao_destino.ordem`); o plano guarda a base de estados usada (`plano.base_json`); a tentativa guarda a versão do exercício e o hash da resposta.
- **Minimização:** o texto do currículo e as respostas abertas **não** ficam no Oracle (só no MongoDB, já redigidos); o Oracle guarda o hash.
- **Catálogo disjunto:** `destino_ocupacao` tem `UNIQUE (cbo6)`, garantindo que uma ocupação CBO pertença a um só destino (a mesma população não é contada duas vezes no mercado).

| Tabela | Papel | Chaves e restrições principais |
|---|---|---|
| `usuario` | conta (e-mail, hash Argon2id, versão da sessão, `persona_demo`) | PK `id`, UNIQUE `email`, CHECK `persona_demo IN ('S','N')` |
| `consentimento` | finalidade, versão do termo, concessão e revogação | FK `usuario`, CHECK finalidade ∈ {perfil, curriculo_llm, laboratorio_nuvem} |
| `competencia_usuario` | competência sugerida/declarada e a revisão da pessoa | FK `usuario`, CHECK revisão ∈ {pendente, confirmada, rejeitada, nao_possuo} |
| `intencao` | atividades, motivos (JSON), horas/semana, orçamento, UF | PK = FK `usuario` (1:1), CHECK horas 1–80 |
| `comparacao` / `comparacao_destino` | comparação de até 3 destinos e o resultado de cada um | PK composta (`comparacao_id`, `ordem`), CHECK ordem 1–3, UNIQUE destino por comparação |
| `caminho_escolhido` / `plano` / `checkpoint` | destino escolhido, plano gerado e etapas | `plano.caminho_id` UNIQUE (1:1), CHECK tipo e status |
| `tentativa` | exercício diagnóstico: notas objetiva e da IA, resultado, contestação | FK `usuario`, CHECK resultado ∈ {demonstrada, insuficiente, parcial} |
| `sessao_laboratorio` | sessão com código, validade e relato redigido | UNIQUE `codigo`, CHECK status |
| `destino`, `ocupacao_cbo`, `destino_ocupacao`, `competencia_esco`, `requisito_destino` | catálogo curado | PKs naturais, FKs entre catálogo, UNIQUE `cbo6` |

<div class="quebra-pagina"></div>

## 3. Consultas no Oracle — evidências de execução

**Arquivo:** `app/db/consultas/evidencias_oracle.sql` (9 consultas). **Execução:** `app/tools/executar_consultas_oracle.py`, saída completa em `evidencias/20261116_consultas_oracle.txt` (21:58 UTC). Os dados de usuário são da **persona de demonstração** (Marina, fictícia, marcada `persona_demo = 'S'`), criada pelo script `app/tools/criar_persona_demo.py` pela API real, com a IA real sugerindo as competências e avaliando o exercício.

| # | Técnica | Pergunta respondida | Resultado executado (resumo) |
|---|---|---|---|
| C1 | JOIN de 3 tabelas + `LISTAGG` | Quais ocupações CBO compõem cada destino? | 6 destinos; Monitoramento/IoT com 7 ocupações, Dados/BI e Processos com 6 cada (os três do MVP marcados `S`) |
| C2 | JOIN + agregação condicional | Quantos requisitos obrigatórios e opcionais cada destino tem? | IoT: 6 obrigatórios, 2 opcionais, 3 de conhecimento |
| C3 | `GROUP BY` + `HAVING` | Quais competências ESCO aparecem em mais de um destino? | 13 competências; "identificar os requisitos dos clientes" em 4 destinos |
| C4 | JOIN de 4 tabelas + `LEFT JOIN` | Como a persona revisou as sugestões da IA e onde elas contam? | "sensores" e "protocolos de comunicação de TIC" confirmadas; "resolver problemas de sistemas de TIC" rejeitada; "efetuar análise de riscos" marcada como "não possuo" |
| C5 | Subconsulta `NOT EXISTS` | Que obrigatórios a persona ainda não confirmou em cada destino do MVP? | 16 pares destino × requisito (4 no destino IoT) |
| C6 | Função analítica `RANK() OVER (PARTITION BY …)` | Qual a melhor tentativa de cada exercício? | 1 tentativa: objetiva 0,75, IA 1,0, final 0,875, **demonstrada** |
| C7 | `JSON_VALUE` sobre `CLOB IS JSON` | O que cada comparação salva mostrou por destino? | antes do exercício IoT tinha 2 declaradas e 6 desconhecidas; depois, `todos_demonstrados`; último mês observado (202509, SP): IoT 121, Processos 645, Dados/BI 1994 admissões |
| C8 | JOIN de 4 tabelas + agregação | Como está o progresso do plano ativo por tipo de etapa? | 16 checkpoints; 1 `demonstrar` concluído |
| C9 | Agregação | Consentimentos ativos por finalidade (LGPD) | perfil, curriculo_llm e laboratorio_nuvem: 1 ativo cada |

Trecho real da saída (C6):

```
exercicio_id                     | criado_em                  | nota_objetiva | nota_llm | nota_final | resultado   | posicao_melhor
ex_analista_monitoramento_iot_01 | 2026-11-16 21:57:29.996023 | 0.75          | 1.0      | 0.875      | demonstrada | 1
```

Os números de mercado em C7 são **admissões formais observadas** no Novo Caged (ensino superior completo ou mais, nas ocupações do destino, SP), repassadas do snapshot versionado; não são oportunidades abertas nem chance individual.

<div class="quebra-pagina"></div>

## 4. Documentos e consultas no MongoDB — evidências de execução

**Arquivo:** `app/db/mongo/evidencias_mongo.js` (cópia em `03_DataScience/mongodb.js`), executado com `mongosh --file` contra o Atlas do projeto. Saída completa em `evidencias/20261116_consultas_mongo.txt`. Nenhuma consulta devolve o texto do currículo nem da resposta: só metadados.

| Coleção | Documentos (16/11) | Conteúdo | Por que é documento |
|---|---|---|---|
| `curriculos_redigidos` | 1 | texto **já redigido**, hash SHA-256, contagem de redações por tipo, status de confirmação | texto longo e livre; a contagem de redações varia por categoria |
| `extracoes_llm` | 1 | modelo usado, tentativas, uso de tokens, candidatas e descartes por motivo (sem a resposta bruta) | metadados de chamadas à IA com estrutura que muda por modelo |
| `avaliacoes_llm` | 1 | cache da avaliação por critério da rubrica (chave = hash da resposta) | lista aninhada de critérios; leitura por chave |
| `respostas_abertas` | 1 | resposta aberta redigida da tentativa | texto livre ligado ao id da tentativa no Oracle |
| `model_cards` | 6 | procedência dos modelos de mercado: período de treino e validação, seed, versões das bibliotecas, hashes dos artefatos, status de promoção | documento técnico aninhado, diferente para modelo clássico e rede neural |

| # | Consulta | Resultado executado |
|---|---|---|
| M1 | documentos por coleção | 5 coleções; `model_cards` com 6 documentos |
| M2 | `aggregate` em `curriculos_redigidos` por origem e status | 1 currículo de texto confirmado, 1 e-mail e 1 telefone redigidos |
| M3 | `aggregate` em `extracoes_llm` por modelo | `deepseek/deepseek-v4.1-flash-1017`: 1 extração, 4 candidatas, 0 descartes |
| M4 | `find` com projeção em `model_cards` | 6 modelos (persistência, sazonal, ridge, random forest, gradient boosting, MLP), treino 202101–202409, validação 202501–202509, seed 42, `status_promocao = nao_decidida` |
| M5 | `$unwind` + `$group` em `avaliacoes_llm` | nível médio 2 nos 3 critérios da rubrica do exercício IoT |
| M6 | `aggregate` em `respostas_abertas` por usuário | 1 resposta da persona |
| M7 | índices por coleção | só `_id` (as buscas são por chave) |

## 5. Por que Oracle e MongoDB, e como os dois se ligam

- **Oracle para o que precisa de integridade e de perguntas cruzadas:** conta, consentimento (prova de LGPD), estados de competência, comparações, plano e tentativas têm regras de domínio (`CHECK`), relações obrigatórias (`FK`) e consultas que cruzam o catálogo com as decisões da pessoa (C4, C5, C8). Apagar a conta remove em cascata competências, intenção, comparações, plano, tentativas e sessões de laboratório. O consentimento **não** tem cascata, de propósito: o registro de que o consentimento existiu e foi revogado precisa ser preservado (prova perante a LGPD), então a conta só pode ser apagada depois de tratar esses registros.
- **MongoDB para texto livre e documentos de formato variável:** currículo redigido, respostas abertas e saídas de IA mudam de forma conforme o modelo e o conteúdo; guardar isso em colunas fixas obrigaria a esquemas frágeis. Os *model cards* são documentos técnicos aninhados que se leem inteiros.
- **Ligação por identificadores estáveis:** `curriculo_id` (Mongo) está em `competencia_usuario.curriculo_id`; `tentativa.avaliacao_id` é a chave do documento em `avaliacoes_llm`; `respostas_abertas._id` é o `tentativa.id`.
- **Minimização como regra de distribuição:** dado pessoal em texto livre só existe redigido e só no MongoDB; o Oracle guarda hash e estados. Nenhum log contém esses textos (verificado na demonstração de Cyber).

## 6. Limitações

- Oracle local em Docker, não o Oracle da FIAP (credencial recusada); o DDL é 19c e roda igual.
- Os dados de usuário são de **uma persona de demonstração** fictícia; as contagens descrevem o ambiente de demonstração, não um uso real.
- O MongoDB ainda não tem índices além de `_id` nem TTL para os textos redigidos (proposto: TTL e índice por `usuario_id`).
- A exclusão de conta não remove automaticamente os documentos do MongoDB (proposto).
- Modelos lógico/relacional e exportações do Data Modeler ainda pendentes de execução pelo **agente**, por decisão do usuário em17/11; nenhum artefato real dessa ferramenta é alegado como concluído.
