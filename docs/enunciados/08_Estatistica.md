# Estatística com R e Python

> Disciplina (nome oficial): **Statistical Computing with R and Python**  
> Entrega no Portal do Aluno até **19/11/2026 às 23h55**. Fonte completa: `docs/GS2_2026_enunciados.md` e `docs/material_por_cadeira/`.

## Tema

O desafio CitizenTech convida nossos alunos a olhar para problemas reais das cidades, do campo e das comunidades e desenvolver soluções tecnológicas capazes de melhorar concretamente a vida das pessoas. Estamos falando de mobilidade, acessibilidade, sustentabilidade, segurança, infraestrutura, conectividade, inclusão e tantas outras necessidades do nosso cotidiano.

## Objetivo

Cada grupo deverá escolher um problema real, investigar quem é afetado e em quais condições de acesso, justificar as tecnologias escolhidas, demonstrar o funcionamento da proposta (por implementação ou simulação com evidências de execução) e apresentar evidências de validação, relacionando o projeto aos ODS pertinentes.

## Briefing

A avaliação contemplará a aplicação de técnicas de inferência estatística, regressão e classificação a dados reais relacionados ao desafio CitizenTech, utilizando R ou Python para desenvolver modelos preditivos que apoiem a tomada de decisão e a criação de soluções tecnológicas inteligentes e sustentáveis.

## Regras gerais

- Colocar o nome completo e o número de matrícula de todos os integrantes;
- Não envie links, poste todos os entregáveis diretamente no Portal, nos formatos exigidos;
- Serão descontados **2,0 pontos** em caso de cadastro ou entrega inadequados no sistema;
- Após o prazo de entrega, o sistema não aceitará envios posteriores;
- O(s) arquivo(s) enviado(s) será(ão) o(s) avaliado(s), não sendo permitida substituição após o prazo;
- Será descontado **1,0 ponto** por item ausente e/ou não atendido na avaliação.

## Orientações para o desenvolvimento da avaliação

Os alunos deverão se organizar individualmente, em dupla ou em trio para realizar a avaliação.

**01) Bases de dados** — Explore as bases de dados indicadas abaixo para fundamentar sua análise:
- IBGE: https://www.ibge.gov.br/
- Portal Brasileiro de Dados Abertos: https://dados.gov.br/home
- Google Data Search: datasetsearch.research.google.com
- Kaggle: https://www.kaggle.com/
- GitHub: https://github.com/awesomedata/awesome-public-datasets

> OBS: Outras bases de dados podem ser utilizadas, a base de dados poderá ser escolhida livremente pelo grupo, desde que seja adequada ao contexto e devidamente justificada, **não sendo aceitas bases geradas artificialmente ou com dados fictícios**.

**02) (1,0 ponto)** Assumindo que as variáveis numéricas escolhidas seguem uma Distribuição Normal de Probabilidade, escolher uma variável aleatória da base de dados e determinar:
- a) A probabilidade desta variável ser menor do que a média dos registros da variável. Na sequência classifique o evento quanto ao resultado probabilístico.
- b) A probabilidade desta variável ser maior que a mediana dos registros da variável. Na sequência classifique o evento quanto ao resultado probabilístico.

**03) (1,0 ponto)** Assumindo que as variáveis numéricas escolhidas seguem uma Distribuição Normal de Probabilidade, escolher uma variável aleatória da base de dados e realizar um teste de hipótese para a média utilizando como dados do problema:
- a) A média amostral é **menor** do que a média populacional de referência, a um nível de significância de **6%**, amostra de tamanho **20** e desvio padrão de referência igual ao desvio padrão populacional dos dados.
- b) A média amostral é **maior** do que a média populacional de referência, a um nível de significância de **9%**, amostra de tamanho **25** e desvio padrão de referência igual ao desvio padrão populacional dos dados.

**04) (2,0 pontos)** Faça uma **Análise Bivariada** entre 02 variáveis quantitativas contendo:
- a) O Gráfico de Dispersão, com título e nomes nos eixos x e y, e interprete o resultado.
- b) A Covariância e a Correlação Linear de Pearson, e interprete os resultados.
- c) O Gráfico de Correlação Linear de Pearson, e interprete o resultado.
- d) A reta da Regressão Linear Simples (no Gráfico de Dispersão), e a Equação da Regressão Linear Simples.
- e) A verificação da adequação do modelo (R² e Teste F), e interprete os resultados.
- f) Faça uma previsão.

**05) (2,0 pontos)** Faça uma **Análise Multivariada** entre, pelo menos, 03 variáveis quantitativas contendo:
- a) O Gráfico de Dispersão, e interprete os principais resultados.
- b) A Matriz de Covariância e a Matriz de Correlação Linear de Pearson, e interprete os principais resultados.
- c) O Gráfico de Correlação Linear de Pearson, e interprete os principais resultados.
- d) A Equação da Regressão Linear Múltipla.
- e) A verificação da adequação do modelo (R² e Teste F), e interprete os resultados.
- f) Faça uma previsão utilizando, pelo menos, 02 variáveis explicativas.

**06) (2,0 pontos)** Faça uma **Análise Multivariada** entre, pelo menos, 03 variáveis quantitativas contendo:
- a) A Equação da Regressão Logística Binária.
- b) A Matriz de Confusão e a Acurácia, interprete os resultados.
- c) Uma classificação utilizando, pelo menos, 02 variáveis explicativas.

**07) (2,0 pontos)** Elabore um **relatório estatístico**, contendo as tabelas, gráficos e medidas estatísticas obtidas, com suas respectivas interpretações, com o objetivo de extrair insights relevantes que auxiliem na resolução do problema‑tema desta avaliação. Assuma que este relatório será apresentado a uma empresa ou cliente que, além de utilizar as informações para apoiar a tomada de decisão, também avaliará seu desempenho e rigor como profissional da área técnica.

**08) Entrega** — Em seguida, apenas um representante de cada grupo deverá postar no Portal:
- a) O arquivo com a base de dados, obrigatoriamente em formato **.csv** (Comma-Separated Values) ou **.xlsx** (Excel);
- b) Os códigos desenvolvidos, obrigatoriamente em formato **.r** (R) ou **.py** (Python);
- c) O relatório estatístico, obrigatoriamente em formato **.pdf** (PDF).

> OBS: As entregas devem ser realizadas estritamente conforme as orientações e formatos definidos e trabalhados em aula pelo(a) respectivo(a) professor(a) da disciplina durante o semestre.

## Resumo da pontuação

| Questão | Conteúdo | Pontos |
|---|---|---:|
| 02 | Probabilidade (Distribuição Normal) | 1,0 |
| 03 | Teste de hipótese para a média | 1,0 |
| 04 | Análise bivariada / Regressão Linear Simples | 2,0 |
| 05 | Análise multivariada / Regressão Linear Múltipla | 2,0 |
| 06 | Análise multivariada / Regressão Logística Binária | 2,0 |
| 07 | Relatório estatístico | 2,0 |
