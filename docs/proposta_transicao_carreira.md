# Transição profissional orientada por evidências — proposta e preparação do desenvolvimento

**CitizenTech · FIAP GS 2026.2 · Versão 0.1 · 12/11/2026**

**Atualização 12/11/2026:** o nivelamento Grill Me foi concluído. As decisões e o plano TDD estão em [plano_desenvolvimento.md](plano_desenvolvimento.md), que prevalece sobre as recomendações deste documento em caso de conflito (ex.: público amplo com laboratório IoT opcional; 6 destinos; nota 50/50 no exercício; ODS 4 e 10 principais).

**Contexto histórico da versão0.1:** este texto nasceu como proposta para nivelamento. A etapa Grill Me e a aprovação do plano já ocorreram; **não reiniciar o nivelamento na próxima sessão**. Para retomar o desenvolvimento, ler primeiro [estado.md](<estado.md>) e depois as decisões/contratos necessários do plano aprovado. As seções históricas desta proposta não são um checklist de execução atual.

**Prazo acadêmico registrado nos enunciados:** 19/11/2026, às 23h55. O cronograma disponível é curto; não há promessa de concluir todas as funcionalidades comerciais até essa data.

**Legenda:** **Definido** = solicitado pelo usuário ou exigido no enunciado; **Proposto** = recomendação a validar; **Pendente** = decisão, acesso ou evidência ainda necessária; **Futuro** = fora do MVP recomendado. Nenhuma métrica de modelo, previsão de mercado, economia ou receita deste produto foi demonstrada nesta etapa. Os códigos preexistentes não foram executados nem certificados por esta consolidação.

## 1. Visão, cidadão e problema

**Proposta:** aplicação web que ajuda profissionais já graduados e com experiência a comparar caminhos de transição, reconhecer competências aproveitáveis, identificar lacunas, planejar a preparação e interpretar sinais do mercado de trabalho.

**Problema principal:** tomar decisões de transição com informações fragmentadas, recomendações genéricas de cursos e dificuldade de distinguir experiência transferível, competência demonstrada e demanda efetiva do mercado.

**Pergunta central:** “Qual caminho atende aos meus objetivos e restrições, aproveita minha experiência e apresenta evidências suficientes para justificar o investimento de preparação?”

- **Público definido pelo usuário:** profissionais graduados e experientes em transição. Não é plataforma para escolher a primeira graduação nem ferramenta de seleção de candidatos por empregadores.
- **Recorte proposto para o MVP:** um domínio de origem, três destinos próximos e um território inicial, preferencialmente SP. Ocupações, setor e território exatos serão fechados no nivelamento; a opção de prática industrial da seção 8 depende de aprovação explícita.
- **Condições de acesso:** uso pelo navegador, interface em português, compatibilidade móvel, navegação por teclado, baixo volume de dados, ausência de câmera obrigatória e possibilidade de preencher experiência sem upload de currículo.
- **ODS propostos:** ODS 4, especialmente desenvolvimento de competências para trabalho; ODS 8, trabalho decente e transição profissional; ODS 10, acesso à orientação e transparência. São contribuições pretendidas, não impacto comprovado.
- **Beneficiário:** profissional. **Comprador candidato:** o próprio profissional ou consultoria de carreira/recolocação que ofereça o serviço ao participante. B2B2C é hipótese comercial, não contrato existente.

**Valor a demonstrar:** melhorar a clareza da decisão, reduzir recomendações sem fundamento, evitar formação redundante e explicitar alternativas e limitações. Não garantir recolocação, aumento salarial ou preservação de senioridade.

## 2. Limites do produto e terminologia

| Termo | Significado adotado | O que não significa |
|---|---|---|
| Competência demonstrada | Evidência revisada segundo critérios explícitos | Certificação profissional automática |
| Competência declarada | Informação fornecida pela pessoa | Habilidade comprovada |
| Competência transferível candidata | Conhecimento com possível uso no destino | Transferência assegurada entre contextos |
| Lacuna | Requisito cuja ausência foi identificada | Tudo que não apareceu no currículo |
| Desconhecido | Informação insuficiente para avaliar | Inaptidão |
| Cobertura de requisitos | Relação explicável entre requisitos avaliados e evidências | Probabilidade de contratação |
| Preparação | Plano e domínio de tarefas delimitadas | Direito a exercer profissão regulamentada |
| Admissões formais | Entradas registradas na população coberta pela fonte | Anúncios, postos líquidos criados ou todas as oportunidades |
| Cenário de longo prazo | Resultado condicionado a premissas e fontes | Previsão garantida de uma profissão |

**Regra de produto:** a decisão permanece com o usuário. O sistema não deve responder “essa profissão vale/não vale a pena” como verdade universal. Apresentará alinhamento com objetivos, esforço, evidência de mercado, incerteza e conflitos. Será permitido concluir **“não há dados suficientes”**, **“mantenha esta alternativa em observação”** ou **“considere evoluir na função atual”**.

Uma experiência de emprego anterior não deve ser convertida automaticamente em competência. Ausência de portfólio não pode eliminar quem trabalhou com informação confidencial: oferecer exercícios acessíveis e exemplos anonimizados que a pessoa tenha autorização para compartilhar.

## 3. Jornada e entregas da aplicação web

1. **Definir intenção:** atividades desejadas, motivos da mudança, disponibilidade de estudo, orçamento e restrições voluntárias. Evitar coletar idade, raça, saúde ou fotografia para ordenar caminhos.
2. **Organizar experiência:** relato ou currículo autorizado; extração assistida e confirmação pelo usuário. Cada competência mantém origem, data e estado de evidência.
3. **Comparar até três caminhos:** tarefas do destino, aproveitamento da experiência, requisitos, barreiras regulatórias, panorama de mercado e conflitos com preferências.
4. **Avaliar uma competência relevante:** exercício com critérios definidos, resultado observável e revisão. LLM pode apoiar feedback, mas não ser autoridade incontestável.
5. **Construir plano:** lacunas priorizadas, pré-requisitos, atividades, estimativa de carga e checkpoints. Cursos são meios possíveis, não a finalidade do produto.
6. **Reavaliar:** incorporar nova evidência, revisar o plano e registrar por que a recomendação mudou.

**Telas propostas:** entrada/perfil; comparação de caminhos; detalhe do mercado e das fontes; competências/evidências; plano/checkpoints; laboratório prático apenas se aprovado; painel técnico restrito para saúde dos dados e execução dos modelos.

**Exemplo de saída, sem números inventados:** “O caminho A aproveita sua experiência em processos, mas a competência SQL permanece não avaliada. O indicador de admissões cobre a família ocupacional, não exatamente o título comercial. Antes de adquirir uma formação extensa, execute a atividade diagnóstica e compare os requisitos dos caminhos A e B.”

### Escopo mínimo e exclusões

**MVP proposto:** comparação explicável, um panorama real de mercado, baseline e modelos próprios avaliados, plano inicial por regras, uma avaliação prática, fontes datadas, APIs/persistência e evidências acadêmicas. Integração IoT depende da seção 8.

**Fora do MVP:** todas as profissões, previsão individual de contratação, salário futuro garantido, prazo de aptidão aprendido sem histórico, candidaturas automáticas, mensagens a recrutadores, testes psicológicos, inferência por rosto/voz, contratação de cursos e pagamentos. Agentes de desenvolvimento não precisam existir dentro da aplicação final.

## 4. Mercado existente e hipótese de diferenciação

A pesquisa documental confirmou sobreposição com [Google Career Dreamer](https://grow.google/career-dreamer/), [LinkedIn Career Explorer](https://linkedin.github.io/career-explorer/), [LinkedIn Next Role Explorer](https://www.linkedin.com/help/learning/answer/a6231389), [Gloat](https://resources.gloat.com/actionable-career-pathing/) e, no Brasil, [TCD Career Engine](https://hotmart.com/pt-br/marketplace/produtos/tcd-career-engine/F101057508E). Os fornecedores anunciam exploração de caminhos, lacunas, planos e/ou apoio à preparação. Suas eficácias não foram auditadas.

**Diferenciação candidata:** aproveitar experiência de domínio, distinguir declaração de evidência, comparar alternativas sob restrições pessoais e apresentar sinais brasileiros de mercado com procedência e incerteza. Não alegar ineditismo ou exclusividade dessa combinação sem comparação prática.

**Modelo comercial a testar:** pacote de diagnóstico e reavaliação; alternativamente, cobrança por participante para consultorias. Não há preço próprio validado. Como referência adjacente, a [Teal](https://www.tealhq.com/pricing) anuncia US$ 29 por 30 dias; isso não demonstra disposição a pagar no Brasil nem equivalência funcional.

**Validação futura:** comparar clareza/utilidade com orientação genérica, registrar correções feitas pelos participantes, testar disposição a pagar e medir tempo de trabalho do consultor. Custos incluem especialistas, atualização/licença de dados, infraestrutura, inferência, suporte e aquisição. Evitar monetização que incentive recomendar cursos desnecessários; qualquer afiliação deve ser visível.

## 5. Dados reais, aquisição e Browser Stealth

### 5.1 Fontes e prontidão

| Fonte | Uso proposto | Disponibilidade e limite verificados |
|---|---|---|
| [Guia Brasileiro de Ocupações, CBO e QBQ](https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/acoes-e-programas/programas-projetos-acoes-obras-e-atividades/estatisticas-trabalho/guia-brasileiro-de-ocupacoes) | Tarefas, conhecimentos, habilidades e referência de ocupações | Portal e documentação consultados; extração/mapeamento ainda não implementados |
| [RAIS e Novo Caged](https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/acoes-e-programas/programas-projetos-acoes-obras-e-atividades/estatisticas-trabalho/microdados-rais-e-caged) | Estoque formal, fluxos, remuneração e território, conforme cada base | MTE disponibiliza microdados não identificados; arquivos, schemas, revisões e recorte ainda precisam ser inspecionados e processados |
| [ESCO](https://esco.ec.europa.eu/en/use-esco/download) | Taxonomia de competências/ocupações, inclusive em português | Download/API documentados; condições e versão precisam acompanhar a ingestão |
| [O*NET](https://www.onetcenter.org/database.html) | Tarefas e competências como referência complementar | Base 31.0 com licença CC BY 4.0, sujeita às exceções documentadas; retrata os EUA, não o Brasil |
| [Adzuna API](https://developer.adzuna.com/overview) | Anúncios e indicadores licenciados | Exige app_id/app_key; país, quota, licença, cobertura e histórico necessário não foram testados |
| [Greenhouse Job Board API](https://docs.greenhouse.io/job-board) | Anúncios de organizações selecionadas | GETs documentados como públicos; autorização de reutilização/treinamento e amostra brasileira precisam ser verificadas; não fornece automaticamente histórico representativo |
| Participantes e especialistas | Evidências de competências, correções e progresso | Ainda não coletados; participação informada, finalidade e governança necessárias |

**Separar os conjuntos:** mercado real; taxonomias; perfis consentidos; exercícios; telemetria didática. Telemetria simulada não é evidência de mercado e não substitui a base real obrigatória de Estatística. Fixtures sintéticas são permitidas para testar software, claramente identificadas.

### 5.2 Política de coleta

**Decisão proposta:** Browser Stealth não será dependência do MVP nem mecanismo para contornar restrições. Automação de navegador pode servir para renderização/testes e coleta expressamente permitida; a necessidade técnica de renderizar JavaScript não cria autorização de reutilização.

O [LinkedIn informa](https://www.linkedin.com/help/linkedin/answer/a1341387/prohibited-software-and-extensions) que proíbe scraping e automações não autorizadas, inclusive contornar controles e limites. O [User Agreement](https://www.linkedin.com/legal/user-agreement) se aplica a membros e visitantes. Portanto:

- Não usar contas falsas, contorno de CAPTCHA, rotação de identidades para evitar bloqueios, credenciais compartilhadas ou scraping autenticado não autorizado.
- Usar LinkedIn somente por acesso oficialmente autorizado/licenciado ou referências permitidas. Um agregador intermediário não elimina restrições da origem.
- Priorizar dados públicos com condições claras, APIs oficiais, feeds acordados e textos fornecidos com direito de uso.
- Registrar separadamente permissão para **acessar, armazenar, treinar e redistribuir**. API pública e robots.txt não equivalem a licença irrestrita para todas essas finalidades.
- Respeitar quotas, paginação, cache e limites. Em 401/403, suspender e revisar autorização; em 429, seguir o prazo informado, sem evasão.
- Não coletar perfis individuais, contatos de recrutadores, dados de candidatura ou atributos sensíveis para o modelo de mercado.
- Se não houver fonte de anúncios aprovada, demonstrar o módulo de mercado com dados oficiais reais, sem inventar vagas ou fingir cobertura de plataformas privadas.

### 5.3 Qualidade e procedência

Cada fonte terá URL, responsável, licença/termos e data da consulta, finalidade permitida, intervalo coberto, data de publicação, data de coleta, versão, hash e transformações. Retenção do conteúdo integral depende da licença; pode-se guardar apenas metadados e derivados autorizados.

Deduplicar anúncios e republicações por identificadores e similaridade; não interpretar ausência em uma coleta como contratação. Distinguir data publicada, atualizada e primeira observação. Salário ausente não vira zero; manter moeda, periodicidade, regime e cobertura. Distribuição salarial observada não é oferta pessoal futura.

**Título comercial ≠ CBO ≠ ESCO ≠ O*NET.** Usar correspondências revisadas, potencialmente muitos-para-muitos, com confiança, origem e granularidade. Não somar a mesma população várias vezes. Se o título for mais específico que a base, mostrar o grupo ocupacional efetivamente medido.

Um snapshot atual não permite reconstruir cinco anos de anúncios. Na Adzuna, a documentação de [histórico](https://developer.adzuna.com/docs/historical) demonstra médias salariais; não presumir disponibilidade de histórico completo de anúncios e competências.

## 6. Inteligência de mercado e modelos ML/DL

### 6.1 Perguntas mensuráveis

O módulo apoiará a pergunta “vale investir neste caminho?” por componentes, não por um veredito opaco:

- Volume e evolução de admissões/desligamentos formais no recorte;
- Estoque de vínculos e remuneração observada, quando comparáveis e disponíveis;
- Requisitos e diversidade de anunciantes, se houver amostra autorizada;
- Concentração, sazonalidade, volatilidade e estabilidade da cobertura;
- Compatibilidade com preferências e evidências do profissional.

**Não classificar “fogo de palha” como alvo supervisionado sem definição e rótulos independentes.** No MVP, apresentar sinais que sustentam ou enfraquecem a hipótese de crescimento persistente. Uma alta isolada pode ser sazonalidade, rotatividade, mudança de coleta ou choque econômico. Nem admissões elevadas nem saldo positivo garantem bons empregos.

### 6.2 Experimento principal proposto

**Unidade:** família/grupo CBO × UF × mês, limitada ao recorte escolhido. Expandir séries para treino compartilhado somente com justificativa; não alegar generalização a grupos não testados.

**Base candidata:** Novo Caged desde 2020 até a última competência publicada e processada. Não concatenar automaticamente Caged antigo e Novo Caged; documentar mudanças metodológicas, revisões e efeitos da pandemia. A extensão e densidade reais ainda precisam ser verificadas.

**Alvo de regressão:** soma de admissões formais dos três meses seguintes ao mês de referência disponível:

`y(g,t) = A(g,t+1) + A(g,t+2) + A(g,t+3)`

O painel deve dizer “admissões formais estimadas no grupo e território”, nunca “vagas disponíveis” ou “probabilidade de conseguir emprego”. Mostrar desligamentos/saldo histórico junto ao volume para não confundir reposição com expansão. Saldo futuro é uma alternativa de experimento, não um alvo adicional obrigatório nesta versão.

**Público vs. população medida:** o dado agregado não prova demanda exclusiva por graduados experientes. Examinar um recorte por escolaridade se disponível e suficientemente denso; não usar idade como proxy de senioridade. Enquanto isso, rotular o indicador como contexto geral da ocupação. O sistema deve conseguir abster-se de detalhes locais quando a agregação não os sustenta.

**Features candidatas, disponíveis na origem:** admissões/desligamentos passados, lags, somas/médias móveis deslocadas, mês do ano, grupo ocupacional e território. Sem preços, vínculos ou informações publicados apenas depois da data simulada. Não usar variável contemporânea que contenha o próprio alvo futuro.

**ML — desenho proposto para cumprir a disciplina:** baseline de persistência trimestral e referência sazonal quando houver histórico; comparar **Regressão Linear e Random Forest** como os dois algoritmos inicialmente propostos. O enunciado exige dois algoritmos adequados, não especificamente esse par. Tuning em pelo menos um modelo com validação temporal. LightGBM/XGBoost são alternativas, não dependências obrigatórias.

**RNA — implementação obrigatória, arquitetura proposta:** MLP compacta sobre as mesmas features defasadas, preferencialmente com treino compartilhado quando defensável. Usar TensorFlow/Keras ou PyTorch, escolher um; documentar camadas, neurônios, ativação, loss, épocas, batch size, learning rate, seed e ambiente. Comparar pelo menos duas configurações, curvas treino/validação e regularização/early stopping quando apropriados. RNN/GRU é evolução, não requisito autoimposto.

Os notebooks devem explicar os resultados após as células de análise e encerrar com síntese crítica. Fixar dependências em ambiente isolado e registrar versões/seeds. Como o alvo é uma contagem, definir tratamento de previsões negativas na validação e avaliar o pipeline inteiro; não corrigir apenas o número exibido para esconder comportamento inválido.

**Métricas:** MAE e RMSE em admissões; erro por série e macroagregado, além de erro agregado ponderado; MASE se denominador válido. Evitar MAPE como única métrica em séries com zeros. Relatar resíduos, estabilidade temporal, custo/latência e importância de features sem interpretação causal.

Uma RNA que perde para o baseline continua sendo um experimento acadêmico válido se criticamente analisado. Não promovê-la ao produto por ser “DL”. Modelo simples pode ser a escolha final.

### 6.3 Validação e prevenção de vazamento

1. Auditar schema, faltantes, densidade, revisões e cobertura antes de fixar o recorte.
2. Definir calendário de treino, validação e teste por datas comuns a todas as séries, não divisão aleatória de linhas.
3. Usar backtesting com origem móvel. Remover/embargar exemplos cujo intervalo do alvo atravesse a fronteira da validação/teste. Os três meses finais sem rótulo observado não viram zeros.
4. Ajustar imputação, escala, seleção de features e codificações apenas no treino de cada fold; aplicar as transformações já ajustadas à validação/teste.
5. Escolher hiperparâmetros e modelo sem consultar o teste final. Não retreinar usando o teste e continuar chamando-o de não visto.
6. Registrar data de referência, publicação e revisão. Sem snapshots históricos, declarar avaliação retrospectiva com a versão disponível, não backtest perfeitamente point-in-time. Uma defasagem fixa, sozinha, não garante ausência de revisões.
7. Quantificar incerteza apenas se houver método e calibração suficientes, com cobertura avaliada fora do treino. Sem isso, mostrar estimativa experimental sem faixa probabilística inventada.
8. Separar população repetida/ocupações correlacionadas; milhares de linhas de painel não equivalem a milhares de meses independentes. Incerteza de métricas deve respeitar blocos temporais.
9. Congelar critérios de promoção antes do holdout: melhoria e estabilidade em validação, limites por recorte e orçamento de erro a definir em Grill Me. Resultado inconclusivo mantém baseline ou histórico descritivo; não adulterar teste para promover modelo.

**Condição de parada:** se a base não sustentar o alvo, reduzir granularidade/horizonte com justificativa anterior ao teste ou apresentar limitação explícita. Não criar séries fictícias para “provar” viabilidade real.

### 6.4 Horizonte de cinco anos

Horizonte pretendido nesta versão: aproximadamente **2026–2031**. O MVP terá previsão curta avaliada, inicialmente trimestral, e cenários de longo prazo separados. Previsões de 6–12 meses só entram se forem treinadas e avaliadas para esses horizontes.

O [WEF 2025](https://www.weforum.org/stories/2025/01/future-of-jobs-report-2025-jobs-of-the-future-and-the-skills-you-need-to-get-them/) relata expectativa dos empregadores pesquisados de mudança em 39% das competências essenciais até 2030. A [OIT 2025](https://www.ilo.org/publications/generative-ai-and-jobs-2025-update) estima alguma exposição à IA generativa para um em quatro trabalhadores no mundo e distingue transformação de tarefas de eliminação de empregos. Não são previsões locais de contratação nem cobrem automaticamente 2031.

Para cada caminho: cenário de continuidade, aceleração de adoção tecnológica e desaceleração; premissas, tarefas afetadas, fontes, data e sinais que exigiriam revisão. Não atribuir probabilidades inventadas, somar números de geografias diferentes ou extrapolar 60 meses de forma mecânica e apresentá-los como certeza.

## 7. IA do perfil, plano e explicação

| Componente | Abordagem inicial | Limite e avaliação |
|---|---|---|
| Extração de competências | LLM com saída estruturada + taxonomia + revisão do usuário | Cada item aponta trecho de origem; medir precisão/cobertura contra anotação humana, não autoavaliação da mesma LLM |
| Busca de caminhos | Embeddings multilíngues, regras de elegibilidade e requisitos | Similaridade textual não equivale a domínio; sem score de contratação |
| Comparação | Dimensões separadas e prioridades explícitas do usuário | Não esconder requisitos obrigatórios em uma média; permitir desconhecidos e discordância |
| Plano | Grafo de pré-requisitos + tarefas e estimativas revisadas | Carga de curso não é tempo comprovado de aprendizagem |
| Reavaliação | Critérios objetivos e revisão humana em tarefas abertas | Evidência mede apenas o que a tarefa permite observar |
| Explicação | LLM com recuperação de fontes e resultados estruturados | Não calcula números de mercado livremente nem inventa referências |

**Prazo:** separar carga planejada, domínio demonstrado e tempo até emprego. No MVP, a estimativa é um planejamento revisável. Modelos de tempo até competência exigem dados longitudinais futuros, incluindo interrupções e participantes ainda em andamento; não treinar só com concluintes.

**LLM na aplicação:** receber dados mínimos, explicar resultados e preparar tarefas. Não comprar cursos, enviar candidaturas, compartilhar currículo, mudar perfil ou agir externamente sem aprovação. Documentos externos são dados não confiáveis, nunca instruções para ferramentas. Não executar código produzido em currículo/anúncio.

## 8. IoT: bloqueio de aderência e alternativa para nivelamento

**Pendente crítico:** uma plataforma generalista de carreira não precisa naturalmente de dois sensores e um atuador. Não declarar a aderência a AICSS resolvida colocando sensores ambientais decorativos ou inferindo aptidão por biometria.

**Alternativa proposta, ainda não aprovada:** recortar o piloto para graduados com experiência em operações/engenharia que avaliam transição para funções de análise operacional e monitoramento de equipamentos. A aplicação incluiria uma prática de instrumentação e interpretação de incidentes. O laboratório é parte da preparação desse mesmo público, não um segundo produto com beneficiários diferentes.

### Bancada didática candidata

- ESP32 físico ou Wokwi;
- Sensor de temperatura DS18B20;
- Sensor ultrassônico de distância, representando distância ao material/superfície de um reservatório didático;
- LED/buzzer para alertar o participante no local;
- Um JSON por leitura, conforme contrato existente do projeto; correlação por sessão de laboratório e ciclo de aquisição;
- Critérios do exercício: interpretar medidas, reconhecer limiares, justificar resposta e produzir uma análise. Sensor mede fenômeno, não inteligência, personalidade, empregabilidade ou prontidão global.

**Limiares exclusivamente didáticos propostos:** temperatura: normal abaixo de 35 °C, atenção de 35 até abaixo de 45 °C, crítico a partir de 45 °C; distância: normal acima de 15 cm, atenção acima de 8 até 15 cm, crítico até 8 cm. Distância física válida deve ser não negativa. Os valores não representam limites de segurança industrial; confirmar cenário e adequação antes de implementar. Nenhum aquecimento ou operação perigosa é necessário na demonstração.

**Três cenários mínimos:** 25 °C/25 cm (normal), 38 °C/12 cm (atenção), 48 °C/5 cm (crítico). Por sensor: `OK` para normal, `ALERTA` para atenção/crítico; LED/buzzer deve distinguir os cenários. Falha de sensor é estado de erro separado, não valor normal nem zero fabricado.

**Ligação com carreira:** exercício previsto na trilha aprovada → evidência do que o participante executou/explicou → revisão de uma competência específica. Telemetria isolada não comprova aprendizado; ausência de acesso físico não pode ser barreira, daí a opção simulada.

**Gate:** usuário deve aceitar o recorte e a justificativa acadêmica precisa ser validada com a disciplina. Se rejeitado, reformular contexto ou tema integrado. A execução do circuito não resolve, por si só, a pertinência. ML de mercado e telemetria não devem ser unidos artificialmente em uma única tabela de treinamento.

## 9. Arquitetura proposta

```text
Fontes reais autorizadas -> ingestão/qualidade -> dataset versionado
                                              -> treino ML/RNA offline
                                              -> artefatos + métricas

Pessoa -> aplicação web -> FastAPI -> perfil, caminhos, plano, inferência
                              |      Oracle: dados relacionais mestres
                              |      MongoDB: documentos/evidências/fontes
                              |      índice vetorial derivado, se necessário
                              |
ESP32/Wokwi -> POST leituras --+-> CSV durável + indicador + histórico GET
          alerta local        +-> outbox persistente -> AWS Lambda Function URL
                                                        | limiares locais
                                                        | HF/Comprehend isolado
                                                        | CloudWatch
                                                        v
                                                  RDS PostgreSQL
                                                  GET /ocorrencias
```

**Frontend:** React + TypeScript, proposto; escolher hospedagem depois de orçamento/acesso. O resultado é uma aplicação própria do projeto, não alteração da GUI usada para conversar com o agente.

**Backend:** FastAPI, validação com Pydantic e módulos de domínio. ML/RNA em bibliotecas próprias para inferência; LLM por adaptador substituível. Embeddings e busca vetorial somente se justificarem o custo; não adicionar outra infraestrutura sem necessidade.

**Implantação acadêmica:** web/API podem ser demonstradas localmente; o componente Cloud exige execução real em AWS, salvo autorização formal da disciplina. Não criar recursos pagos, contas ou permissões nesta etapa.

**Persistência e responsabilidade:**

- **Oracle:** usuário pseudonimizado, consentimentos/finalidades, experiência, competência, evidência referenciada, ocupação, correspondência de taxonomias, caminho, plano e checkpoint. Demonstrar PK/FK, integridade e consultas úteis.
- **MongoDB:** documentos de fontes e avaliações permitidos, extrações estruturadas e histórico de explicações; ligar por IDs estáveis, não replicar sem necessidade o perfil inteiro.
- **RDS PostgreSQL:** tabela `ocorrencias`, responsável pela telemetria aceita na nuvem. PostgreSQL não substitui a entrega de Oracle/MongoDB.
- **CSV:** histórico obrigatório de CTP; não é banco de currículos. Um processo escritor/controle de concorrência e recuperação de arquivo precisam ser testados.
- **Outbox:** registro persistente de envio/ack, com reenvio e idempotência. A forma concreta será fechada no planejamento; memória volátil não basta.
- **Artefatos de ML:** dataset/transformações/modelo/métricas versionados; somente artefatos próprios e confiáveis são carregados. Não carregar pickle enviado por usuário.

Não requerer transação distribuída entre três bancos. Cada dado tem uma fonte de verdade. Relacionar documentos e telemetria por referências; manter o MVP modular, não uma coleção de microsserviços.

### 9.1 Risco de implantação a resolver

O enunciado Cloud determina **Lambda fora de VPC**. A comunicação direta com RDS nessa configuração exige um caminho de rede acessível e regras compatíveis; a saída padrão da Lambda não oferece IP fixo por função.

**Não resolver silenciosamente liberando PostgreSQL para `0.0.0.0/0`.** Validar a base acadêmica existente, conectividade, TLS com verificação, credenciais de menor privilégio, limites de conexões e controles compensatórios. Se não houver desenho aceitável, solicitar orientação/exceção formal; produção normalmente requer outro desenho de rede. Não afirmar que API autenticada protege a porta do banco.

Esse gate e as credenciais/cotas de Oracle, MongoDB e AWS devem ser resolvidos antes de prometer a entrega completa. Senhas, tokens e números de contas não entram neste documento.

## 10. Contratos de API e eventos propostos

### 10.1 Telemetria única entre AICSS, CTP e Cloud

Preservar o padrão de um POST por sensor já descrito no [contrato-base do projeto](<C:/Users/orugi/Documents/Projetos/FIAP/GS/info-gs-diciplinas/00_projeto/README.md#L21-L40>). Exemplo didático, não leitura real:

```json
{
  "schema_version": "1.0",
  "evento_id": "demo-ciclo-001-temperatura",
  "ciclo_id": "demo-ciclo-001",
  "sessao_laboratorio_id": "sessao-demo",
  "dispositivo_id": "esp32-lab-01",
  "tipo_dispositivo": "esp32",
  "metrica": "temperatura_c",
  "unidade": "C",
  "valor": 38.0,
  "status": "ALERTA",
  "medido_em": "2026-11-12T14:00:00Z",
  "relato": "Cenario didatico: aumento de temperatura."
}
```

Os três campos obrigatórios do enunciado Cloud são `dispositivo_id`, `metrica`, `valor`; as extensões são propostas compatíveis. Coordenadas são opcionais/nulas quando não necessárias. Nenhuma localização residencial precisa ser coletada. Na demonstração, um POST análogo usa `distancia_cm`.

O servidor recalcula risco por limiar; não confia no `status` do cliente. A mesma configuração versionada deve ser aplicada em firmware, API e Lambda. Identificadores de ciclo permitem associar sensores sem obrigar envelope de lote incompatível com o material existente.

| Interface | Comportamento esperado |
|---|---|
| FastAPI `POST /leituras` | Valida e persiste CSV; retorna 201 com ID local e estado de sincronização; 400 para payload inválido; 503 se não conseguir persistir |
| FastAPI `GET /leituras` | Histórico paginado e autorizado, com classificação e indicador: total de alertas/média por métrica |
| Lambda `GET /health` | Saúde da função sem expor segredos; distinguir checks adicionais de dependências quando implementados |
| Lambda `POST /ocorrencias` | 400 se campos obrigatórios faltarem; 201 após registro novo no RDS, com ID, risco e indicador de alerta |
| Lambda `GET /ocorrencias` | Registros persistidos, acesso autorizado e paginação |
| APIs de perfil/caminhos/plano | Contratos ainda a fechar em Grill Me; não gerar testes contra assinaturas inventadas |

Na Lambda, `evento_id` identifica reenvios: proposta de 200 com o ID existente para duplicata idêntica, sem nova linha; 409 se a mesma chave tiver conteúdo diferente. Requisições acadêmicas sem essa extensão continuam atendendo o mínimo dos três campos, mas não oferecem deduplicação confiável entre tentativas. Confirmar contratos antes dos testes.

FastAPI usa 422 por padrão em alguns erros: o contrato proposto de 400 exige tratamento explícito e teste, especialmente na Lambda onde 400 é obrigatório. Rejeitar JSON malformado, valores não finitos, booleano no lugar de número, métrica/unidade desconhecida e payload excessivo. Erro não pode desaparecer silenciosamente.

Falha na nuvem não apaga o CSV; resposta local não pode dizer “salvo no RDS” enquanto estiver pendente. Falha de sentimento não impede classificação por limiar e persistência. Falha do próprio banco não deve retornar 201.

## 11. Rastreabilidade das nove disciplinas

**Legenda de estado atual:** “proposto” não significa implementado. Aderência depende de evidências de execução. Este Markdown não substitui os arquivos finais exigidos por disciplina.

| Disciplina e fonte | Requisito que deve aparecer na entrega | Aplicação nesta proposta / evidência futura |
|---|---|---|
| [01 AICSS](<C:/Users/orugi/Documents/Projetos/FIAP/GS/info-gs-diciplinas/01_AICSS/ENUNCIADO.md>) | ESP32, ≥2 sensores relevantes, ≥1 atuador, status por sensor, alerta local, JSON/Python/CSV, ≥3 comportamentos | Bancada da seção 8; firmware/diagrama, JSON e registros nos três cenários. **Pertinência pendente** |
| [02 Cybersecurity](<C:/Users/orugi/Documents/Projetos/FIAP/GS/info-gs-diciplinas/02_Cybersecurity/ENUNCIADO.md>) | Superfície de ataque, ≥5 riscos, controles, ≥1 proteção funcional, LGPD e engenharia social | Seção 12; demonstrar autorização e/ou rate limiting. PDF ≤15 páginas e vídeo ≤5 min |
| [03 Data Science](<C:/Users/orugi/Documents/Projetos/FIAP/GS/info-gs-diciplinas/03_DataScience/ENUNCIADO.md>) | Modelagem, tabelas relacionadas, documentos, consultas executadas e justificativa Oracle/MongoDB | Modelador indicado na disciplina, DDL/scripts e evidências de relações e consultas. Não trocar Oracle por RDS |
| [04 CTP Python](<C:/Users/orugi/Documents/Projetos/FIAP/GS/info-gs-diciplinas/04_CTP_Python/ENUNCIADO.md>) | Flask/FastAPI, POST validado, funções/condicionais/repetições/coleções, CSV, GET, indicador e 3 cenários | API de leituras e classificação, histórico e testes ponta a ponta; documentar contrato e execução |
| [05 ML](<C:/Users/orugi/Documents/Projetos/FIAP/GS/info-gs-diciplinas/05_ML/ENUNCIADO.md>) | Dataset/EDA, preprocessing sem vazamento, baseline + ≥2 algoritmos, tuning ≥1, métricas e importância | Experimento da seção 6; notebook, slides PPT/PDF e vídeo ≤5 min; previsões fora do treino |
| [06 Cloud](<C:/Users/orugi/Documents/Projetos/FIAP/GS/info-gs-diciplinas/06_Cloud/ENUNCIADO.md>) | Lambda Function URL fora de VPC, RDS PostgreSQL, rotas, logs, limiares, IA por API resiliente e simulador | Seção 11.2; execução na AWS, quatro imagens e vídeo ≤5 min. **Rede/conta/acesso pendentes** |
| [07 RNA/DL](<C:/Users/orugi/Documents/Projetos/FIAP/GS/info-gs-diciplinas/07_RedesNeurais/ENUNCIADO.md>) | Dataset pertinente, rede própria, treinamento, curvas, refinamento/configurações e avaliação inédita | MLP da seção 6; notebook, parâmetros, métricas, limitações e demonstração funcional em vídeo. Não há duração específica registrada nesse enunciado |
| [08 Estatística](<C:/Users/orugi/Documents/Projetos/FIAP/GS/info-gs-diciplinas/08_Estatistica/ENUNCIADO.md>) | Dados reais, probabilidades, testes de média específicos, regressões simples/múltipla/logística e interpretação | Seção 11.1; base CSV/XLSX, código .py/.r e relatório PDF enviados diretamente, não somente links |
| [09 AI Challenge](<C:/Users/orugi/Documents/Projetos/FIAP/GS/info-gs-diciplinas/09_AIC/ENUNCIADO.md>) | Mesmo problema/público/contexto, execução integrada, UML, Kanban, ODS, acessibilidade e inspiração da live | Vídeo ≤7 min, YouTube não listado, rosto do narrador, sem música, nomes/RMs na abertura ou fechamento; distinguir implementado de futuro |

**Complementos de entrega:** nomes completos e RMs nas identificações/capas exigidas; validar os formatos e campos do Portal. Não presumir que um único vídeo substitua todos os vídeos por disciplina. Em Data Science, o enunciado local é resumido: confirmar detalhes de formato/modelador com o material da aula, sem inventar número mínimo de tabelas. Em RNA, confirmar campo de envio do vídeo. Para AIC, o grupo deve fornecer a ideia efetivamente extraída da live; não fabricar participação ou inspiração.

### 11.1 Plano específico de Estatística — sem perder os parâmetros do enunciado

Usar um recorte **real** documentado. O painel de mercado pode sustentar análises, mas observações temporais não são independentes. Se for necessário um recorte transversal para inferência, defini-lo explicitamente e preservar o mesmo problema; não fabricar dados normalmente distribuídos.

- **Questão 02:** sob a hipótese Normal solicitada, escolher variável numérica e calcular `P(X < média)` e `P(X > mediana amostral)`, classificando os eventos. A primeira vale 0,5 quando a média define o centro do modelo Normal; a segunda não é automaticamente 0,5 se a mediana amostral diferir desse centro. Mostrar parâmetros, unidades, diagnóstico de distribuição e limites da hipótese didática.
- **Questão 03a:** teste unilateral inferior para média, **n = 20**, **α = 6%**, desvio de referência igual ao desvio populacional dos dados conforme o enunciado.
- **Questão 03b:** teste unilateral superior, **n = 25**, **α = 9%**, mesma exigência de referência. Identificar a população finita do recorte e o método de seleção; não procurar repetidamente amostras até obter significância. Se for exigida a direção da média no exercício, declarar seleção condicionada e seu limite inferencial. Não substituir esses alfas por 5% sem autorização.
- **Questão 04:** duas variáveis quantitativas, dispersão com eixos, covariância/Pearson e gráfico de correlação, reta/equação de regressão simples, R², teste F e uma previsão.
- **Questão 05:** pelo menos três variáveis quantitativas, dispersões, matrizes de covariância/correlação e gráfico, equação de regressão múltipla, R², teste F e previsão com ≥2 explicativas.
- **Questão 06:** regressão logística binária com ≥2 explicativas quantitativas, equação, matriz de confusão, acurácia e classificação. Alvo candidato: admissões no trimestre futuro maiores que no trimestre precedente, calculado somente onde o futuro já foi observado; não “profissão boa/ruim”.
- **Questão 07/08:** interpretar todos os resultados, entregar base CSV/XLSX, código .py/.r e relatório PDF diretamente no Portal, conforme o enunciado.

Variáveis candidatas para regressões: alvo trimestral futuro e volumes passados de admissões/desligamentos; decisões finais dependem da EDA e da adequação dos pressupostos. Mostrar heterocedasticidade, dependência, baixa amostra e transformações, se presentes. Correções robustas podem complementar a atividade, não substituir silenciosamente seus itens. Testes F/Pearson não demonstram causalidade nem validam previsão individual de carreira.

### 11.2 Plano específico de Cloud

- Tabela `ocorrencias`: dispositivo, tipo, coordenadas quando fornecidas, métrica, valor, relato, resultado de análise, risco e data/hora; acrescentar ID de evento e restrição de unicidade quando aplicável.
- Rotas e respostas da seção 10, com risco `normal`, `atencao`, `critico`, calculado localmente na função por limiares, sem depender da API de IA.
- CloudWatch: payload bruto, interpretação, classificação e ID; `WARNING` para inválido/crítico. Usar apenas dados didáticos controlados e sem PII para a demonstração. Em produção, logs brutos de texto livre exigem outra política; sanitizar/limitar e validar eventual ajuste com a disciplina. Hash sozinho não substitui o payload bruto pedido no enunciado.
- IA: Hugging Face com modelo indicado `cardiffnlp/twitter-xlm-roberta-base-sentiment`, `HF_TOKEN` em variável de ambiente e endpoint `https://router.huggingface.co/hf-inference/models/{modelo}`; usar apenas `urllib` na chamada, sem adicionar biblioteca ao pacote, devolver rótulo de maior pontuação e confiança. Alternativa: Comprehend com idioma `pt` e permissão IAM pertinente, conforme o enunciado. Confirmar disponibilidade/permissões antes. Seguir timeout de 30 s da função no caminho HF e reservar tempo para persistência.
- Simulador específico de Cloud: enviar a sequência diretamente à Function URL, imprimindo request/response em cada envio e evoluindo de normal a crítico. O fluxo integrado via FastAPI/outbox é adicional e não elimina essa evidência. Configurar autenticação autorizada também para o simulador; não expor uma API de escrita sem controle apenas para facilitar a gravação do vídeo.
- Sentimento se refere apenas ao relato da ocorrência/experiência didática, nunca à empregabilidade, competência ou saúde mental. É componente acadêmico separado da previsão de mercado.
- Timeout/erro do provedor resulta em sentimento indisponível e ingestão preservada. Para evidenciar integração, demonstrar ao menos uma resposta real bem-sucedida do caminho escolhido e uma falha tratada; mock não prova serviço externo integrado.
- Entregar Function URL funcional, endpoint RDS sem senha, SQL, função, simulador/firmware, README e vídeo ≤5 min.
- **Quatro imagens:** variável de ambiente cadastrada com valor secreto oculto; simulador enviando; logs com chegada/classificação; consulta com registros no RDS. Não usar screenshots para expor tokens.

## 12. Segurança, privacidade e acessibilidade

As classificações abaixo são preliminares, não auditoria de um sistema implementado.

| Risco | Impacto / probabilidade preliminar | Controle e demonstração planejados |
|---|---|---|
| Acesso ao perfil/evidência de outra pessoa | Alto / médio | Autenticação e autorização por proprietário; teste cruzado devolve 403/404 sem vazamento |
| Credencial ou currículo em logs/repositório | Alto / médio | Dados mínimos, segredos em ambiente, varredura e redaction; demo Cloud sem PII |
| SQL injection/XSS em currículo/anúncio | Alto / médio | Consultas parametrizadas, sanitização na apresentação, validação e CSP quando aplicável |
| Abuso de API/inferência e custos | Médio-alto / médio | Rate limiting, quotas, limite de upload, timeout e orçamento; demonstrar 429 |
| Prompt injection em fontes externas | Alto / médio | Separar dados/instruções, ferramentas restritas, saída validada; conteúdo não aciona comandos |
| Envenenamento ou troca de dataset/modelo | Alto / médio | Procedência, hashes, revisão de ingestão e artefatos aprovados; não desserializar upload arbitrário |
| Replay/falsificação de dispositivo | Médio / médio | Identidade autorizada, chave fora do repositório, idempotência e sequência/ciclo |
| Exposição do RDS | Alto / médio | Gate de rede, TLS verificado, menor privilégio, limites de conexão e revisão antes do deploy |
| Phishing prometendo emprego/curso obrigatório | Alto / médio | Avisos, canais oficiais, domínio verificável; nenhuma compra/candidatura automática |
| Perda/divergência entre histórico local e nuvem | Médio / médio | Outbox durável, estado explícito, idempotência, backup e teste de recuperação |

**LGPD:** inventariar currículo, formação, histórico, preferências e evidências; definir finalidade/base legal por operação. Não usar consentimento como autorização genérica para tudo. Informar terceiros/modelos externos, retenção, exclusão e direitos de correção/revisão. Dados sensíveis incidentais devem ser minimizados; não inferir atributos protegidos para recomendar ou impedir caminhos. Perfil não é enviado ao patrocinador/empregador sem autorização apropriada.

Acesso público à web não exige perfil real no protótipo: usar personas de demonstração sinalizadas, mantendo **dados de mercado reais**. Fixtures e personas não serão apresentadas como participantes ou evidências comerciais.

**Acessibilidade:** teclado, foco visível, rótulos, contraste, texto alternativo e estados não comunicados só por cor; linguagem simples para incerteza; sem câmera/áudio obrigatório. Requisitos regulamentados e acomodações são tratados explicitamente, sem inferir incapacidade.

## 13. Preparação para TDD — executar somente após nivelamento

**Definido:** testes antecedem a implementação de cada comportamento. **Não significa escrever todos os testes imagináveis antes de qualquer código.** Aplicar fatias verticais: **RED → GREEN → REFACTOR**, uma capacidade observável por ciclo.

1. Aprovar interfaces e comportamentos prioritários com o usuário.
2. Escrever um teste de comportamento pela interface pública; confirmar falha pelo motivo esperado.
3. Implementar o mínimo para passar; executar o teste e a regressão relevante.
4. Refatorar com testes verdes, preservando o comportamento.
5. Registrar evidências e revisão adversarial; só então iniciar a próxima fatia.

### Catálogo inicial de comportamentos, não testes já escritos

| ID | Dado / quando | Resultado esperado |
|---|---|---|
| T01 | Fonte sem autorização de treinamento | Ingestão para treino não é promovida; motivo registrado |
| T02 | Dois registros do mesmo anúncio/evento | Deduplicação sem inflar contagens; conflito de conteúdo sinalizado |
| T03 | Falta período de coleta ou salário | Não converter ausência em zero ou falso declínio |
| T04 | Alvo atravessa corte temporal | Pipeline impede uso no treino daquele fold |
| T05 | Registros futuros são alterados | Features de uma origem anterior permanecem iguais |
| T06 | Série insuficiente/mapeamento ocupacional ambíguo | Resposta informa limitação; não fabrica previsão específica |
| T07 | Usuário não declarou uma habilidade | Estado desconhecido, não incapaz |
| T08 | Recomendação muda após evidência | Motivo e versão são rastreáveis; usuário pode corrigir |
| T09 | POST válido em três níveis didáticos | CSV/histórico/indicador e alerta coerentes com limiares |
| T10 | Payload inválido/não finito/campo ausente | 400; nenhum registro apresentado como válido |
| T11 | Serviço de sentimento indisponível | Risco e persistência continuam; sentimento indisponível explícito |
| T12 | Banco Cloud falha ou internet cai | Sem 201 falso na nuvem; cópia local e pendência preservadas |
| T13 | Reenvio após perda de resposta | Um registro lógico no RDS, mesmo ID recuperado |
| T14 | Usuário A tenta ler dados de B | Acesso negado sem exposição |
| T15 | Documento manda ignorar regras/executar comando | Texto tratado como dado; nenhuma ação externa |
| T16 | Token exposto em erro ou orçamento excedido | Sem segredo na resposta/log; requisição limitada |
| T17 | Previsão/explicação exibida | Fonte, população, unidade, referência temporal e natureza observado/previsto/cenário visíveis |

**Ferramentas propostas:** pytest para domínio/API/integração, cliente de teste HTTP e testes de UI/E2E com Playwright quando iniciada a implementação. Mockar provedores externos na fronteira para determinismo; não mockar toda a lógica para obter verde. Testes de contrato e smoke autorizados verificam integrações reais, sem coletar sites privados no CI.

**Software ≠ ciência:** testes validam contratos, integridade, ausência de vazamento e comportamento; avaliação fora da amostra valida utilidade preditiva. Não escrever teste que exige “90% de acurácia” arbitrária nem adaptar o holdout até passar. LLM deve ser testada por schema, fundamentação, limites e conjunto revisado; não exigir texto literalmente idêntico.

Na suíte comportamental, conferir persistência pelas APIs públicas; para entregas de bancos, incluir separadamente consultas SQL/documentais como evidências acadêmicas. Não confundir essa inspeção com testes acoplados a métodos privados.

## 14. Orquestração multiagente de desenvolvimento

**Definido:** um LLM de maior capacidade atua como orquestrador; subagentes de menor custo executam tarefas delimitadas; cada subagente realiza autorrevisão adversarial antes de entregar; o orquestrador revisa e decide integrar.

**Não confundir:** essa é a organização do desenvolvimento. A aplicação não precisa executar uma rede de agentes para cada usuário. Mais agentes não substituem contratos, testes nem revisão humana de decisões de domínio.

### Papéis propostos

- **Orquestrador:** fecha requisitos, define dependências/interfaces, distribui escopo, resolve conflitos, revisa riscos e executa/verifica testes de integração.
- **Dados/ML:** fontes, qualidade, features, baselines, backtests e documentação de modelos.
- **Backend/persistência:** APIs, autorização, Oracle/MongoDB, CSV/outbox e integração dos modelos.
- **Frontend:** jornada, acessibilidade e explicações sem falsa precisão.
- **IoT/Cloud:** contrato comum, sensores/atuador, Lambda/RDS e resiliência, somente após os gates.
- **Revisor independente:** revisa mudanças de maior risco sem participar de sua autoria; não substituído pela autorrevisão do implementador.

Papéis podem ser executados em sequência pelo mesmo pool; não pressupõem seis agentes simultâneos. Começar com no máximo duas tarefas independentes e aumentar apenas se integração e custo justificarem. Não deixar dois agentes editarem os mesmos arquivos em paralelo.

### Contrato obrigatório por delegação

```text
Objetivo e benefício ao usuário:
Requisitos e decisões aprovadas que se aplicam:
Escopo permitido e caminhos exclusivos de escrita:
Arquivos/interfaces de entrada já verificados:
Comportamento público e teste prioritário (RED):
Critério de aceitação e comandos de validação:
Dependências, limites de tempo/custo e condição de parada:
Ações proibidas: alterar segredos/permissões; coletar fonte sem autorização;
  enfraquecer testes; remover trabalho alheio; publicar/gastar sem autorização.
Formato de retorno:
  1. O que mudou e arquivos/linhas.
  2. Evidência RED e GREEN, comandos e resultados reais.
  3. Autorrevisão adversarial: contraexemplos, falhas/segurança,
     pressupostos, vazamento, incompatibilidade acadêmica.
  4. Problemas corrigidos e riscos ainda abertos.
  5. O que NÃO foi testado/implementado e dependências faltantes.
```

**Checklist adversarial mínimo do subagente:** dado ausente/adversarial; erro externo; acesso indevido; duplicação/reenvio; vazamento temporal; efeito de refatoração nos testes; resultado que contradiz a recomendação; diferença entre mock e execução real. Não basta escrever “revisado e aprovado”.

**Aceite do orquestrador:** ler o diff e os arquivos afetados, verificar evidências, executar testes quando possível, confirmar que o teste falhou antes da correção por motivo pertinente, tentar um contraexemplo, revisar licença/privacidade e integração, então aceitar ou devolver. Se não executou um teste, declarar isso. Não aceitar autorrelato de sucesso como prova.

### Execução local e segurança operacional

A referência existente é [SUBAGENT-INSTRUCTIONS.md](<C:/Users/orugi/Documents/Projetos/FIAP/GS/SUBAGENT-INSTRUCTIONS.md>): subagentes via **Antigravity CLI (`agy`)**, modelo registrado `gemini-3.8-flash-high`. Revalidar disponibilidade/capacidade antes de executar; a seleção do orquestrador e o orçamento serão definidos no nivelamento.

Auditorias usam modo somente leitura/`plan`; implementação só após aprovação do plano e com escopo de escrita delimitado. Não ativar `--dangerously-skip-permissions`, alterar configurações de autenticação ou ampliar permissões por conveniência. Prompts devem incluir restrições; a possibilidade técnica de uma ferramenta não concede autorização.

Registrar IDs de jobs, coletar resultados, estabelecer timeout operacional e encerrar trabalho que perdeu utilidade. Tarefas independentes podem iniciar juntas; dependentes esperam contrato e integração. Não iniciar orquestração em massa só porque há vários módulos. Para falhas de ferramenta/permissão, reportar e replanejar, não fingir saída nem repetir indefinidamente.

## 15. Sequência de implementação a planejar na próxima sessão

| Fase | Resultado verificável | Dependência / corte |
|---|---|---|
| 0 — Grill Me | Público, domínio, destinos, IoT, dados, orçamento e critérios decididos | Não iniciar código com os gates centrais abertos |
| 1 — Contratos e primeira fatia TDD | Uma jornada mínima por API e UI com fonte real identificada | Interface e primeiro comportamento aprovados |
| 2 — Dados e baseline | Recorte real reproduzível, EDA, divisão temporal e baseline | Arquivos reais/schema/permissões verificados |
| 3 — ML, RNA e Estatística | Comparações, tuning, curvas, relatório e exemplos não vistos | Sem resultados simulados passando por medição real |
| 4 — IoT, Python e Cloud | Três cenários, CSV/GET, Lambda/RDS, logs e IA resiliente | Pertinência e acesso/rede aprovados; contratos da fase 1 |
| 5 — Integração, segurança e UX | Caminho ponta a ponta, controle funcionando e falhas demonstradas | Revisão independente antes de considerar pronto |
| 6 — Entregas | Notebooks/scripts/relatórios, UML, Kanban e vídeos por disciplina | Checklist de formato, nomes/RMs, evidências e links |

Após contratos, módulos independentes podem ser delegados em paralelo. Priorizar uma fatia executável sobre funcionalidades extras. Se faltar tempo, cortar scraping, RNN, agentes em runtime, previsão de aptidão e abrangência nacional; **não cortar requisito obrigatório e continuar declarando conformidade**. Não existe cronograma garantido antes de conhecer acessos, equipe e dados.

## 16. Roteiro da próxima sessão — Grill Me

A entrevista ocorrerá **uma pergunta por vez**, com resposta recomendada e resolução das dependências. Não iniciar agora nem exigir que o usuário responda todo este roteiro de uma vez. Questões respondíveis pelo repositório devem ser investigadas, não devolvidas ao usuário.

1. **Qual recorte une carreira e prática pertinente a sensores?** Recomendação: testar a opção industrial da seção 8; se não fizer sentido ao produto, não forçá-la.
2. **Qual domínio de origem e quais três destinos?** Recomendação: escolher pela disponibilidade de especialista, correspondência ocupacional e dados, não pela profissão mais citada em notícias.
3. **Qual decisão o usuário toma ao fim da primeira sessão?** Recomendação: selecionar um caminho para experimentar, não receber promessa de emprego.
4. **Qual população/geografia e alvo o mercado realmente mede?** Recomendação: começar agregado e rotulado corretamente; admitir diferença entre profissionais graduados e população formal total.
5. **Quais fontes já estão acessíveis e podem ser usadas para treino?** Recomendação: dados oficiais primeiro; anúncios somente com condições verificadas.
6. **Como a competência será demonstrada e quem revisa os critérios?** Recomendação: uma tarefa delimitada e revisável, sem currículo como única verdade.
7. **Quais comportamentos públicos e gates estatísticos serão aprovados?** Recomendação: priorizar integridade, abstenção e baseline; fixar antes do teste final.
8. **Quais acessos/custos de bancos e AWS estão disponíveis?** Recomendação: resolver conectividade acadêmica sem exposição ampla automática.
9. **Quem implementa e quem revisa cada fatia?** Recomendação: orquestrador responsável, filhos econômicos delimitados e revisão independente nos componentes de maior risco.
10. **Qual corte é viável até 19/11?** Recomendação: comprovar o núcleo e todos os mínimos acadêmicos, marcando evoluções futuras honestamente.

**Ao concluir:** atualizar decisões neste documento, aprovar o plano TDD e só então gerar testes/código. Esta versão não é aprovação tácita de stack, sensores, modelos, custos ou coleta em plataformas privadas.

## 17. Critérios de conclusão e auditoria desta proposta

### Para o futuro protótipo

- [ ] Problema, público e contexto únicos; pertinência IoT aceita.
- [ ] Fontes reais e condições de uso verificadas; dataset reproduzível e sem histórico inventado.
- [ ] ML baseline + dois algoritmos + tuning; RNA própria com comparação e teste não visto.
- [ ] Estatística real com todos os parâmetros e formatos do enunciado.
- [ ] Interface distingue observado, previsto, cenário e hipótese de planejamento.
- [ ] CSV/Python, Oracle/MongoDB e RDS executados e evidenciados.
- [ ] Três cenários IoT, alertas locais e limiares coerentes; erro/reenvio tolerados.
- [ ] Sentimento Cloud real e fallback demonstrados, sem uso para aptidão.
- [ ] Proteção de segurança funcionando; nenhum segredo exposto; LGPD e acessibilidade documentadas.
- [ ] Testes e revisões independentes registrados; limites não ocultados.
- [ ] UML/Kanban, inspiração real da live, identificações e entregas nos formatos corretos.

### Revisões realizadas nesta consolidação

Os nove enunciados locais foram lidos, incluindo os parâmetros específicos de Estatística e Cloud. Duas revisões independentes do desenho foram solicitadas via `agy`, em modo de planejamento e sem ferramentas de acesso a dados. **Foram revisões textuais da proposta, não auditorias de código nem validação empírica.**

**Incorporado:** revisão temporal do Caged, risco de granularidade incompatível, admissões versus rotatividade, pouca história para DL, idempotência/outbox, pertinência IoT ainda aberta e conflito de rede/privacidade no ambiente acadêmico.

**Não incorporado sem crítica:** substituir α=6%/9% por 5% (contraria a atividade); usar idade como proxy de senioridade; trocar o contrato obrigatório de telemetria por envelope incompatível; trocar níveis de risco do enunciado; substituir payload bruto exigido apenas por hash; afirmar reprovação acadêmica automática ou que TLS resolve exposição de rede. Uma observação do revisor sobre “menos de 60 meses desde 2020” não foi aceita: em novembro de 2026 a contagem potencial é maior, embora a quantidade efetivamente utilizável ainda dependa dos arquivos disponíveis.

**Conclusão:** a proposta tem um núcleo digital viável para investigação e desenvolvimento incremental. A entrega integral da GS continua condicionada ao recorte IoT, ao acesso/qualidade dos dados e à implantação acadêmica. O documento está pronto para a rodada de nivelamento; não declara o produto implementado ou validado.
