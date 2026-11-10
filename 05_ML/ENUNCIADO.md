# Machine Learning

> Disciplina (nome oficial): **Machine Learning and Modelling**  
> Entrega no Portal do Aluno até **19/11/2026 às 23h55**. Fonte completa: `docs/GS2_2026_enunciados.md` e `docs/material_por_cadeira/`.

*(FIAP | Global Solution 2026.2 | Machine Learning & Modelling)*

## Resumo do desafio

Desenvolver um modelo de Machine Learning de classificação ou regressão aplicado ao problema CitizenTech escolhido, utilizando dados reais ou simulados. Realizar análise exploratória, pré-processamento, treinamento de algoritmos estudados na disciplina e avaliação dos resultados por meio de métricas adequadas, demonstrando sua aplicação prática ao público definido.

## Descrição

Desenvolver e comparar modelos de Machine Learning de classificação ou regressão para resolver um problema real da solução CitizenTech do grupo. Utilizar dados estruturados, justificar a escolha dos algoritmos e demonstrar como as previsões podem beneficiar o público definido, considerando as condições reais de uso.

Os grupos deverão utilizar algoritmos estudados na disciplina, como **Regressão Linear, Regressão Logística, KNN, Árvore de Decisão, Random Forest, LightGBM, XGBoost ou CatBoost**. Não é necessário utilizar todos, mas é **obrigatória a comparação entre diferentes modelos e a justificativa da escolha final**.

## Datasets e aplicações sugeridas

Pesquisar bases públicas pertinentes ao problema, por exemplo em Kaggle, IBGE, DataSUS, INEP, dados.gov.br ou portais públicos municipais e estaduais. Dados simulados são permitidos, desde que as premissas e limitações sejam documentadas.

- **Saúde:** classificação de risco ou previsão de demanda por atendimentos.
- **Educação:** identificação de risco de evasão ou previsão de desempenho escolar.
- **Mobilidade:** previsão de demanda de transporte ou risco de acidentes.
- **Meio ambiente e cidades:** previsão de qualidade do ar, enchentes ou eventos extremos.
- **Agricultura e comunidades:** previsão de produtividade ou classificação de vulnerabilidade.

## Entregáveis

**1. Notebook Jupyter (.ipynb)**
- **Entendimento e EDA:** descrever problema, público, fonte e variáveis; apresentar estatísticas, gráficos e análise de qualidade dos dados.
- **Pré-processamento:** tratar valores ausentes, realizar engenharia de atributos quando pertinente, separar treino/teste e aplicar normalização ou padronização quando necessária, evitando data leakage.
- **Modelagem:** treinar e comparar pelo menos dois algoritmos adequados ao problema, incluindo justificativas e um baseline.
- **Otimização:** realizar tuning de hiperparâmetros em pelo menos um modelo com GridSearchCV, RandomizedSearchCV ou método equivalente, usando validação apropriada.
- **Avaliação:** comparar métricas de classificação ou regressão, analisar overfitting/underfitting e justificar a escolha do modelo final.
- **Interpretação:** apresentar e interpretar feature importance ou método equivalente de importância das variáveis quando aplicável.
- **Aplicação:** demonstrar previsões em exemplos ou simulações e explicar o benefício e as limitações para o público definido.

**2. Slides (PPT ou PDF)**

Apresentar problema e público, motivação, base de dados, arquitetura simplificada, modelos comparados, tuning, métricas, importância das variáveis, modelo final, demonstração da aplicação e relação com os ODS pertinentes.

**3. Vídeo pitch (até 5 minutos)**

Explicar o problema, as decisões de modelagem, os resultados e a aplicação prática. Incluir demonstração do notebook ou das previsões. Enviar link de YouTube não listado ou Google Drive com acesso habilitado.

## Critérios de avaliação

| Critério | Peso |
|---|---:|
| Entendimento do problema, escolha dos algoritmos (com justificativa) e implementação | 3,0 |
| Pré-processamento e uso correto de normalização / padronização | 2,0 |
| Interpretação das métricas, tuning e análise de generalização | 2,0 |
| Organização e clareza técnica | 1,5 |
| Aplicação ao contexto CitizenTech e benefício ao público definido | 1,0 |
| Apresentação e vídeo | 0,5 |
| **Total** | **10,0** |

## Observações

O modelo deve estar associado ao mesmo problema e público da solução integradora. Serão avaliadas a consistência metodológica, a interpretação dos resultados e as evidências de funcionamento, não apenas métricas elevadas. Funcionalidades não implementadas devem ser identificadas como evoluções futuras.
