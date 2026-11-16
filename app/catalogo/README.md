# Catálogo de Destinos, Competências e Exercícios Práticos

Este diretório contém os rascunhos estruturados dos **seis destinos profissionais** do projeto CitizenTech, elaborados em conformidade com o Contrato D2 e as decisões de arquitetura e produto **D02, D05, D06, D07, D21, D23 e R29**.

> [!NOTE]
> **REVISÃO HUMANA CONCLUÍDA EM 16/11/2026 (10h05, UTC−3)**
> O grupo revisou e aprovou os seis destinos: `status: aprovado`, `revisao_humana.status: aprovado`, revisor "grupo", checklist integralmente aprovado e mínimos de aprovação **0,5 (objetiva) e 0,5 (LLM)**. A revisão ocorreu depois do prazo D3 (15/11 às 18h), por isso o corte R29 para **três destinos no MVP** continua valendo; os outros três seguem aprovados como conteúdo, fora do escopo do app. O texto abaixo descreve o processo de revisão a partir do rascunho original.

---

## 1. Destinos Curados (Decisão D02)

Foram mapeados os seis destinos canônicos do projeto, localizados em `app/catalogo/destinos/`:

1. **Analista de Dados/BI** (`analista_dados_bi.yaml`): Foco em SQL, qualidade de dados, visualização de dados, análise estatística e ETL.
2. **Analista de Monitoramento/IoT Industrial** (`analista_monitoramento_iot.yaml`): Foco em sensores, telemetria MQTT, observabilidade de sistemas e limiares industriais.
3. **Analista de Processos/Melhoria Contínua** (`analista_processos.yaml`): Foco em modelagem BPMN, análise de tempos/gargalos, metodologia Lean/Six Sigma e riscos operacionais.
4. **Gerente de Projetos/Produto** (`gerente_projetos_produto.yaml`): Foco em metodologias ágeis (Scrum/Kanban), priorização de produto, gestão de riscos e negociação com stakeholders.
5. **Analista de Suporte/Infraestrutura de TI** (`analista_suporte_infra.yaml`): Foco em administração de servidores, resolução de problemas de rede TCP/IP, sustentação a usuários e segurança.
6. **Desenvolvedor de Sistemas** (`desenvolvedor_sistemas.yaml`): Foco em arquitetura de software, testes automatizados (TDD/unitários), persistência SQL e tratamento de concorrência.

---

## 2. Fontes de Dados e Rastreabilidade (Decisões D05 e R29)

- **CBO (Classificação Brasileira de Ocupações):**
  - Arquivo base: `app/catalogo/ocupacoes_cbo.json` (aprovado em 13/11/2026).
  - Códigos de 6 dígitos rigorosamente preservados, garantindo que não haja sobreposição entre destinos nem com os códigos da reserva.
  - Limitações de esparsidade de séries e quebras históricas (ex: 211220 a partir de 2024; 212425 e 212430 a partir de 2022) preservadas nos metadados.
- **ESCO (European Skills, Competences, Qualifications and Occupations):**
  - Arquivo base: `app/catalogo/fontes/esco_20261113.json` (29 conceitos oficiais consultados em 13/11/2026).
  - SHA256 verificado: `08eff6c325155d8cfaef70c8d390ba67303f3ed17897cd4ce8857cbf40db5a7c`.
  - Títulos oficiais em português europeu preservados exatamente como constam na API da Comissão Europeia.
  - *Limitação da consulta:* A versão da taxonomia ESCO não estava fixada no endpoint da consulta (endpoint padrão `resource/skill` e `resource/concept`).
  - Natureza da curadoria: **Mapeamento contextual inferido pendente de validação humana** (`curadoria_natureza: inferida_pendente_revisao`). Não há alegação de associação oficial entre CBO e ESCO pela Comissão Europeia ou MTE.

---

## 3. Estrutura dos Exercícios Práticos e Avaliação (Decisões D06, D07, D21 e D23)

Cada destino contém um exercício didático e sintético composto por:
- **Cenário Didático:** Contexto prático e verossímil de negócio. Para o destino IoT, o cenário obedece estritamente aos limiares versionados em `app/config/limiares.json` (temperatura de atenção a 35 °C e crítica a 45 °C; distância de atenção a 15 cm e crítica a 8 cm; LED para atenção e LED+buzzer para crítico).
- **3 a 5 Questões Objetivas Determinísticas:** Questões de múltipla escolha (A, B, C, D) com gabarito único, justificativa objetiva fundamentada e amarração aos requisitos ESCO avaliados.
- **1 Questão Dissertativa Aberta com Rubrica Estruturada:** Pergunta aprofundada contextual acompanhada de 3 a 4 critérios de correção com âncoras claras para notas 0, 1 e 2.
- **Vedação a Sentimento e Subjetividade (D23):** Nenhum critério de correção avalia aspectos de simpatia, humor, personalidade ou estilo pessoal; a rubrica avalia exclusivamente conduta técnica, raciocínio lógico e resolução prática de problemas.
- **Política de Avaliação Proposta:**
  - Composição 50% objetiva + 50% dissertativa (LLM).
  - Necessidade de aprovação mínima em ambas as etapas para considerar a competência demonstrada no nível básico (D06 e D07).
  - Competência declarada ≠ demonstrada; lacuna de conhecimento ≠ desconhecida (D07).
  - Fallback parcial em caso de indisponibilidade da API de LLM.
  - Limite rigoroso de no máximo 3 tentativas a cada 24 horas (D21).
  - Direito a contestação e solicitação de revisão humana.

---

## 4. Roteiro para Revisão Humana D3 (15/11/2026 até 18:00)

O grupo deve realizar a revisão colaborativa dos arquivos YAML seguindo o checklist abaixo antes da aprovação final:

1. **Pertinência Ocupacional e Escopo:**
   - Avaliar se os 8 conceitos ESCO selecionados cobrem adequadamente a atuação cotidiana dos profissionais em cada ocupação CBO correspondente.
2. **Caráter Obrigatório dos Requisitos:**
   - Revisar os booleanos `obrigatorio_proposto` de cada competência/conhecimento, confirmando quais constituem o núcleo indispensável do cargo (requisito obrigatório não pode sumir em médias compensatórias, D07).
3. **Adequação dos Enunciados e Gabaritos:**
   - Validar a clareza técnica dos enunciados, a plausibilidade dos distratores e a exatidão dos gabaritos.
4. **Calibração das Rubricas e Âncoras 0/1/2:**
   - Verificar se as âncoras descritivas oferecem parâmetros inequívocos para a LLM e para corretores humanos, sem margem para avaliações subjetivas.
5. **Definição dos Mínimos de Aprovação:**
   - Estabelecer os valores definitivos para `minimo_objetiva` e `minimo_llm` (hoje nulos), definindo o ponto de corte para nível básico.
6. **Acessibilidade e Inclusão:**
   - Assegurar que os enunciados utilizem linguagem clara, direta e sem vieses excludentes.
7. **Homologação e Assinatura:**
   - Atualizar `revisao_humana.status` para `aprovado`, registrar a data em `revisado_em` e o identificador do membro responsável em `revisor`.

---

## 5. Travas de uso (histórico do rascunho — todas resolvidas em 16/11/2026)

As condições abaixo bloqueavam o uso enquanto os arquivos eram rascunho. Após a revisão humana, nenhuma delas se aplica; o carregador continua obrigado a verificá-las (fail-safe) caso um destino volte ao estado de rascunho.

1. `status: rascunho`: Indica que os dados não foram homologados formalmente.
2. `revisao_humana.status: pendente`: O fluxo de governança exige aprovação explícita do grupo até D3.
3. `revisao_humana.revisor: null` e `revisado_em: null`: Ausência de assinatura humana responsável.
4. `politica_avaliacao_proposta.minimo_objetiva: null` e `minimo_llm: null`: Sem as notas de corte aprovadas humanamente, o carregador do catálogo deve recusar o cálculo de proficiência por segurança (fail-safe).
