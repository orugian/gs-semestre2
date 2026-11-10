# Global Solution 2026.2 — CitizenTech
## Enunciados consolidados por disciplina

> Documento consolidado a partir de `GS2 2026.txt`. O conteúdo dos enunciados foi mantido; apenas a formatação foi padronizada e trechos duplicados foram removidos.

### Sumário

1. [Redes Neurais](#1-redes-neurais)
2. [Estatística com R e Python](#2-estatística-com-r-e-python)
3. [AI Challenge (AIC)](#3-ai-challenge-aic)
4. [AI Computer Systems e Sensors (AICSS)](#4-ai-computer-systems-e-sensors-aicss)
5. [Cybersecurity](#5-cybersecurity)
6. [Machine Learning](#6-machine-learning)
7. [Computational Thinking with Python](#7-computational-thinking-with-python)
8. [Cloud Computing](#8-cloud-computing)
9. [Data Science](#9-data-science)

---

## 1. Redes Neurais

### Resumo do desafio

Nesta disciplina, o desafio é desenvolver e avaliar uma **Rede Neural Artificial** capaz de resolver uma tarefa relacionada ao problema escolhido pelo grupo. O modelo deverá processar dados, identificar padrões, realizar classificações ou previsões e gerar resultados que possam contribuir para a solução CitizenTech proposta.

O objetivo não é apenas treinar uma rede neural, mas demonstrar que o modelo funciona, avaliar seu desempenho e justificar as decisões tomadas durante seu desenvolvimento.

### Etapas obrigatórias

**1. Definir o problema e a aplicação**
- Apresentar brevemente o problema CitizenTech escolhido pelo grupo.
- Identificar o público impactado e o contexto de aplicação.
- Explicar como a rede neural poderá contribuir para a solução.
- Definir claramente quais serão os dados de entrada e os resultados esperados (saída do modelo).

**2. Selecionar e compreender o dataset**
- Escolher uma base de dados relacionada ao problema.
- Informar a fonte dos dados e descrever suas principais características.
- Justificar por que a base é adequada para a tarefa proposta.
- Apresentar exemplos dos dados utilizados.

**3. Preparar os dados**
- Realizar o tratamento e a preparação dos dados.
- Aplicar as transformações necessárias para o treinamento.
- Dividir os dados em conjuntos de treinamento e teste, utilizando validação quando aplicável.
- Explicar as principais decisões tomadas nessa etapa.

**4. Implementar a rede neural**
- Implementar uma arquitetura adequada à tarefa, utilizando os conceitos estudados na disciplina.
- Escolher entre arquiteturas como MLP, CNN ou RNN, conforme a natureza dos dados e do problema.
- Justificar a arquitetura escolhida e apresentar sua estrutura.
- Explicar brevemente como a rede processa os dados e produz os resultados.

**5. Treinar o modelo**
- Realizar o treinamento da rede neural.
- Definir e apresentar os principais parâmetros utilizados, como número de épocas, batch size e learning rate.
- Registrar os resultados do treinamento, incluindo gráficos de evolução da função de perda e outras métricas pertinentes.

**6. Refinar e otimizar o modelo**

Analisar os resultados do treinamento, identificar possíveis problemas e aplicar estratégias para melhorar o desempenho e a capacidade de generalização do modelo.
- Investigar problemas como overfitting, underfitting, ruído nos dados ou baixa capacidade de generalização.
- Explorar técnicas de otimização de hiperparâmetros, como ajuste de learning rate, número de camadas, número de neurônios e batch size.
- Aplicar técnicas de regularização, como dropout e early stopping, quando apropriado.
- Comparar diferentes configurações ou estratégias e apresentar evidências dos resultados obtidos.
- Justificar as alterações realizadas e explicar se elas contribuíram para melhorar o modelo.

**7. Avaliar os resultados**
- Avaliar o modelo utilizando métricas adequadas à tarefa, como accuracy, precision, recall, F1-score ou RMSE, conforme aplicável.
- Apresentar e interpretar os resultados obtidos.
- Discutir os pontos fortes, as limitações e os possíveis erros do modelo.
- Explicar se o desempenho alcançado é adequado ao problema proposto.

**8. Demonstrar a aplicação**
- Apresentar uma demonstração funcional do modelo utilizando exemplos de dados que não tenham sido utilizados diretamente no treinamento.
- Mostrar as entradas fornecidas e os resultados produzidos pela rede neural.
- Explicar como o modelo poderia ser integrado à solução CitizenTech do grupo.
- Caso a integração completa não seja possível, apresentar uma simulação funcional e identificar claramente o que ainda precisaria ser desenvolvido.

### Sugestões de datasets

Os grupos podem utilizar bases de dados relacionadas ao problema escolhido. Algumas sugestões:

| Dataset | Possível aplicação |
|---|---|
| PlantVillage | Identificação de doenças em plantas por imagens |
| Human Activity Recognition | Reconhecimento de atividades humanas por sensores |
| Air Quality | Análise e previsão de indicadores de qualidade do ar |
| ESC-50 | Classificação de sons ambientais |
| Appliances Energy Prediction | Análise e previsão de consumo de energia |
| CIFAR-10 | Classificação de imagens |

Outras bases podem ser utilizadas, desde que tenham relação com o problema proposto.

Repositórios recomendados: Kaggle, UCI Machine Learning Repository e TensorFlow Datasets.

### Entregáveis

O grupo deverá entregar:

1. **Notebook Jupyter ou Google Colab** com o desenvolvimento completo do projeto, incluindo:
   - Carregamento e preparação dos dados;
   - Implementação da arquitetura da rede neural;
   - Treinamento do modelo;
   - Otimização e refinamento;
   - Avaliação dos resultados;
   - Demonstração da aplicação.
2. **Identificação da base de dados:** fonte, descrição e justificativa da escolha.
3. **Evidências do desenvolvimento:** gráficos, métricas, comparações entre configurações e resultados obtidos.
4. **Demonstração funcional:** exemplos de entradas e saídas do modelo e sua contribuição para a solução CitizenTech.
5. **Documentação:** explicação das decisões técnicas, resultados, limitações e possibilidades de evolução.

### Critérios de avaliação — 10 pontos

| Critério | Pontuação |
|---|---:|
| Definição do problema e escolha justificada do dataset | 1,0 |
| Preparação e tratamento dos dados | 1,0 |
| Implementação e justificativa da arquitetura da rede neural | 2,0 |
| Treinamento e registro dos resultados | 1,5 |
| Refinamento, otimização de hiperparâmetros e regularização, com comparação de resultados | 1,5 |
| Avaliação, interpretação das métricas e análise das limitações | 1,0 |
| Demonstração funcional da aplicação em vídeo | 1,0 |
| Integração e contribuição para a solução CitizenTech | 1,0 |
| **Total** | **10,0** |

### Orientações gerais

- O projeto deve utilizar o mesmo problema, público e contexto definidos pelo grupo para a Global Solution, mantendo a integração entre as disciplinas.
- A rede neural deve ter uma função clara dentro da solução proposta.
- Não é obrigatório desenvolver um dispositivo físico. Simulações são permitidas, desde que apresentem evidências verificáveis de funcionamento.
- Funcionalidades que não forem implementadas devem ser identificadas como possibilidades de evolução futura.
- Considerar aspectos de acessibilidade, segurança, proteção de dados, sustentabilidade e condições reais de utilização.

**Identificação:** a entrega deve conter uma capa com o nome completo e RM de todos os integrantes.

---

## 2. Estatística com R e Python

### Tema

O desafio CitizenTech convida nossos alunos a olhar para problemas reais das cidades, do campo e das comunidades e desenvolver soluções tecnológicas capazes de melhorar concretamente a vida das pessoas. Estamos falando de mobilidade, acessibilidade, sustentabilidade, segurança, infraestrutura, conectividade, inclusão e tantas outras necessidades do nosso cotidiano.

### Objetivo

Cada grupo deverá escolher um problema real, investigar quem é afetado e em quais condições de acesso, justificar as tecnologias escolhidas, demonstrar o funcionamento da proposta (por implementação ou simulação com evidências de execução) e apresentar evidências de validação, relacionando o projeto aos ODS pertinentes.

### Briefing

A avaliação contemplará a aplicação de técnicas de inferência estatística, regressão e classificação a dados reais relacionados ao desafio CitizenTech, utilizando R ou Python para desenvolver modelos preditivos que apoiem a tomada de decisão e a criação de soluções tecnológicas inteligentes e sustentáveis.

### Regras gerais

- Colocar o nome completo e o número de matrícula de todos os integrantes;
- Não envie links, poste todos os entregáveis diretamente no Portal, nos formatos exigidos;
- Serão descontados **2,0 pontos** em caso de cadastro ou entrega inadequados no sistema;
- Após o prazo de entrega, o sistema não aceitará envios posteriores;
- O(s) arquivo(s) enviado(s) será(ão) o(s) avaliado(s), não sendo permitida substituição após o prazo;
- Será descontado **1,0 ponto** por item ausente e/ou não atendido na avaliação.

### Orientações para o desenvolvimento da avaliação

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

### Resumo da pontuação

| Questão | Conteúdo | Pontos |
|---|---|---:|
| 02 | Probabilidade (Distribuição Normal) | 1,0 |
| 03 | Teste de hipótese para a média | 1,0 |
| 04 | Análise bivariada / Regressão Linear Simples | 2,0 |
| 05 | Análise multivariada / Regressão Linear Múltipla | 2,0 |
| 06 | Análise multivariada / Regressão Logística Binária | 2,0 |
| 07 | Relatório estatístico | 2,0 |

---

## 3. AI Challenge (AIC)

### Resumo do desafio

Apresentação do vídeo do projeto integrador CitizenTech, com a união de todas as disciplinas. No vídeo (pitch), os alunos devem apresentar o problema e o público atendido, explicar como o grupo pensou na solução e como ela foi construída, mostrar a gestão das entregas (Kanban/métodos ágeis) e a documentação da arquitetura em UML, e relacionar o projeto aos ODS pertinentes.

### 1) Contexto

A Global Solution 2026.2 propõe o desenvolvimento de um protótipo CitizenTech com dados e inteligência artificial, voltado à melhoria da vida de um público definido, nas cidades, no campo ou nas comunidades.

Ao longo do projeto, seu grupo trabalhou em um mesmo problema, público e contexto, mobilizando conhecimentos de diferentes disciplinas para construir uma solução integrada.

Agora é o momento de apresentar essa trajetória: como o grupo compreendeu o problema, pensou na solução, construiu o protótipo e organizou suas entregas até chegar ao resultado final.

As ideias e reflexões compartilhadas pelos convidados na live de lançamento da Global Solution devem servir de inspiração para o desenvolvimento da solução. Elas também serão consideradas na classificação das melhores propostas.

### 2) Objetivo

Produzir um vídeo de **até 7 minutos** que apresente o projeto integrador, demonstrando o funcionamento da solução e explicando como os conhecimentos das disciplinas e a gestão das entregas contribuíram para sua construção. **Essa entrega é obrigatória para pontuar na disciplina de AIC.**

### 3) O que deve ser apresentado no vídeo

**3.1) Problema, público e proposta de solução** — Apresentem:
- O problema real escolhido e o contexto em que ele acontece.
- O público afetado e suas condições de acesso e uso da solução.
- A solução proposta e como ela busca melhorar a vida desse público.
- Os Objetivos de Desenvolvimento Sustentável (ODS) relacionados ao projeto.
- As ideias ou reflexões apresentadas pelos convidados da live de lançamento que inspiraram ou orientaram a proposta.

**3.2) Construção e integração do projeto**

Expliquem como o grupo pensou e construiu a solução, relacionando as contribuições das disciplinas ao resultado apresentado.

Abordem os componentes efetivamente utilizados no projeto, como programação em Python, dados e armazenamento, análise estatística, machine learning, redes neurais, sensores e sistemas embarcados, nuvem, segurança da informação e proteção de dados.

Mostrem também como a arquitetura e os modelos UML ajudaram a planejar ou compreender a solução. Não basta listar as disciplinas: expliquem como seus conhecimentos e componentes se conectam.

**3.3) Demonstração do funcionamento**

Apresentem o protótipo em funcionamento, por meio de implementação ou simulação, com evidências de execução. Durante a demonstração:
- Mostrem códigos e/ou hardware em funcionamento, conforme os componentes utilizados pelo grupo.
- Expliquem como os dados são utilizados pela solução e qual é o papel da inteligência artificial.
- Apresentem evidências de validação e os resultados observados.
- Identifiquem claramente as funcionalidades que ainda são propostas como evoluções futuras.

Funcionalidades apenas planejadas não substituem a demonstração do que foi desenvolvido.

### 4) Gestão das entregas e resultado final

Expliquem como o grupo organizou o trabalho ao longo do projeto. Apresentem, por exemplo:
- Como as atividades foram planejadas e distribuídas.
- Como o grupo acompanhou o andamento das entregas e tratou dificuldades.
- De que forma essa organização contribuiu para integrar as disciplinas e alcançar o resultado final.

Finalizem comentando como a solução considerou acessibilidade, segurança, proteção de dados, sustentabilidade e condições reais de uso.

### Requisitos do vídeo

- Ter duração máxima de 7 minutos.
- Ser publicado no YouTube com a opção de visibilidade **Não listado**.
- Mostrar o rosto da pessoa que estiver narrando.
- Não conter música de fundo.
- Evidenciar códigos e/ou hardware em funcionamento.
- Apresentar, na primeira ou na última tela, os nomes e as matrículas de todos os integrantes, de forma bem visível.

Antes da entrega, verifiquem se o link está correto e se o vídeo pode ser acessado por quem o receber.

### 5) Entrega

Apenas um integrante do grupo deve realizar a entrega, enviando o link do vídeo no local indicado pelo professor.

### 6) Critérios de avaliação

| Critério | Pontuação |
|---|---:|
| Clareza na apresentação do problema, do público, da solução e dos ODS relacionados | 1,5 |
| Explicação da construção do projeto e da integração entre as disciplinas | 2,5 |
| Demonstração do funcionamento, uso de dados e IA, e apresentação das evidências de validação | 3,0 |
| Explicação da gestão das entregas e de sua contribuição para o resultado final | 1,5 |
| Atendimento aos requisitos do vídeo e identificação dos integrantes | 1,5 |
| **Total** | **10,0** |

### 7) Classificação das melhores soluções

A classificação das melhores soluções terá como referência as ideias e reflexões apresentadas pelos convidados na live de lançamento da Global Solution. Por isso, assistam à live e expliquem no vídeo como essas contribuições inspiraram ou orientaram as escolhas do grupo.

---

## 4. AI Computer Systems e Sensors (AICSS)

### Resumo do desafio

Criar um dispositivo IoT usando ESP32 (Wokwi ou físico) com pelo menos 2 sensores e 1 atuador, que coleta os dados, classifica cada sensor com um status e emite o alerta no local. Enviar as leituras em JSON a um servidor externo, que exibe e grava os dados. Demonstrar pelo menos 3 comportamentos diferentes. A solução deve justificar como os sensores escolhidos servem ao problema do cidadão atendido e deve trazer uma inovação.

### Contextualização

**Como um dispositivo com sensores pode perceber um problema antes que ele afete alguém?**

A vida cotidiana está repleta de fenômenos observáveis. Os dados existem, mas precisam ser capturados, medidos e analisados. Durante a jornada da disciplina realizou-se a coleta de medições dos sensores, tratamento dessas medições, notificações (em texto e em atuadores), transmissão de dados, entre outros recursos. Por isso, a contribuição de AICSS para o Desafio CitizenTech visa dar apoio às pessoas nas cidades, no campo ou nas comunidades usando dispositivos e sensores. Nesta GS, deve-se desenvolver o dispositivo que coleta os dados da solução CitizenTech, com o mesmo problema, o mesmo público e o mesmo contexto das demais disciplinas.

### Objetivo

Construir e demonstrar um fluxo funcional:

```
Fenômeno observado → ESP32 com sensores → alerta local → JSON → servidor Python
```

O dispositivo deve alertar o cidadão no próprio local e enviar os dados para a solução integrada. No servidor eles poderão ser usados pela IA desenvolvida nas outras disciplinas.

### Solução tecnológica

O projeto deverá:
- Usar um ESP32, simulado (Wokwi) ou físico, com **pelo menos 2 sensores** relevantes ao problema e **pelo menos 1 atuador** (LED, buzzer, entre outros).
- Coletar os dados, controlar limiares, organizar a leitura e classificar cada sensor com um status (ex.: OK / ALERTA).
- Enviar as leituras em JSON a um servidor Python, que exibe e grava os dados em CSV.
- Demonstrar **pelo menos 3 comportamentos diferentes**, mostrando a reação do atuador, o JSON transmitido e o registro no servidor.

São aceitos protótipos físicos ou simulados, com evidências da execução. Identifique o que foi implementado ou simulado e explique as limitações.

### Informações sobre a entrega

- Capa com título, nomes e RMs.
- Problema, público beneficiado e evidência de sua relevância.
- Arquitetura da solução e origem dos dados.
- Evidências de funcionamento, resultados dos testes com diferentes entradas e limitações identificadas.
- Código desenvolvido.
- Relação com pelo menos um ODS.

### Critérios de avaliação

| Critério | Pontos |
|---|---:|
| Problema e contribuição CitizenTech | 1 |
| Coleta e decisão com dados IoT | 3 |
| Transmissão de dados usando JSON | 3 |
| Justificativa dos sensores utilizados e alinhamento com a solução adotada | 2 |
| Inovação apresentada | 1 |
| **Total** | **10** |

---

## 5. Cybersecurity

### Resumo do desafio

Analisar os riscos de segurança cibernética da solução CitizenTech e implementar mecanismos de proteção compatíveis com o projeto. O grupo deverá identificar ameaças e vulnerabilidades, propor controles de segurança e demonstrar ao menos uma proteção aplicada ao protótipo, considerando também privacidade e LGPD.

### Tema: Protótipo CitizenTech com Dados e IA para um Público Definido

As equipes deverão desenvolver uma solução CitizenTech baseada em dados e inteligência artificial para atender uma necessidade real de um público específico.

Exemplos de público:
- Agricultores familiares
- Pessoas idosas
- Comunidades em áreas de risco
- Escolas públicas
- Moradores de áreas rurais
- Pessoas com deficiência
- Agentes de saúde
- Cooperativas
- Pequenos empreendedores

Cada equipe deverá escolher **apenas um público-alvo e um problema principal**.

### Desafio da disciplina de Cybersecurity

A equipe deverá atuar como uma **consultoria de segurança** responsável por avaliar os riscos do protótipo CitizenTech desenvolvido. O objetivo é identificar vulnerabilidades, ameaças e controles de segurança adequados ao contexto da solução.

O trabalho deverá demonstrar como a cibersegurança contribui para a proteção:
- dos usuários;
- dos dados;
- dos modelos de IA;
- da infraestrutura;
- da privacidade;
- da conformidade com a LGPD.

### Requisitos técnicos

**1. Descrição da solução CitizenTech** — Apresentar:
- problema escolhido;
- público-alvo;
- uso de IA;
- dados utilizados;
- arquitetura simplificada.

Exemplo: `Usuário | Aplicação | Banco de Dados | Modelo de IA`

**2. Mapeamento de Superfície de Ataque** — Identificar pelo menos:

| Componente | Exemplos |
|---|---|
| Usuários | Acesso indevido, Senha fraca |
| Aplicação | SQL Injection, XSS, Falha de autenticação |
| API | Abuso de requisições |
| Banco de Dados | Vazamento, Exposição indevida |
| Modelo de IA | Manipulação de dados, Model poisoning |

**3. Matriz de Riscos** — Apresentar **no mínimo 5 riscos**. Exemplo:

| Risco | Impacto | Probabilidade |
|---|---|---|
| Roubo de credenciais | Alto | Médio |
| Vazamento de dados | Alto | Alto |
| Ataque à API | Médio | Alto |
| Engenharia Social | Alto | Médio |
| Alteração do modelo de IA | Alto | Baixo |

**4. Controles de Segurança** — Propor controles para os riscos identificados. Exemplos:

| Controle | Exemplos |
|---|---|
| Autenticação | MFA, Política de senhas |
| Firewall/WAF | Proteção da aplicação |
| Backup | Recuperação de incidentes |
| Criptografia | Dados em trânsito, Dados em repouso |
| Monitoramento | Logs, Alertas |

**5. Demonstração Obrigatória** — O grupo deverá implementar **pelo menos UMA proteção funcionando**. Exemplos aceitos:
- Opção 1: Proxy com bloqueio de categorias.
- Opção 2: Firewall/UFW bloqueando acesso.
- Opção 3: Rate Limiting.
- Opção 4: Validação de login.
- Opção 5: Registro de logs.
- Opção 6: Criptografia de dados.
- Opção 7: Hash de integridade.
- Opção 8: Controle de acesso baseado em perfil.

**Não basta propor. É necessário demonstrar com evidências.**

**6. LGPD** — Responder:
- Quais dados pessoais são tratados?
- Quais dados sensíveis podem existir?
- Quais proteções serão aplicadas?
- Como o usuário será informado?

**7. Engenharia Social** — Apresentar:

| Item | Exemplos |
|---|---|
| Cenário de ataque | Phishing, WhatsApp falso, E-mail falso |
| Contramedidas | Treinamento, Conscientização, MFA |

### Entregáveis

**PDF (máximo: 15 páginas)**, contendo:
- Solução CitizenTech
- Arquitetura
- Riscos
- Controles
- LGPD
- Demonstração

**Vídeo Pitch (máximo: 5 minutos)**, contendo:
- problema;
- solução;
- riscos;
- proteção implementada.

### Critérios de avaliação

| Critério | Pontos |
|---|---:|
| Identificação de ameaças e vulnerabilidades | 2 |
| Qualidade da análise de riscos | 2 |
| Implementação de proteção funcional | 3 |
| Privacidade e LGPD | 1 |
| Justificativa técnica das escolhas | 1 |
| Apresentação/Pitch | 1 |
| **Total** | **10** |

---

## 6. Machine Learning

*(FIAP | Global Solution 2026.2 | Machine Learning & Modelling)*

### Resumo do desafio

Desenvolver um modelo de Machine Learning de classificação ou regressão aplicado ao problema CitizenTech escolhido, utilizando dados reais ou simulados. Realizar análise exploratória, pré-processamento, treinamento de algoritmos estudados na disciplina e avaliação dos resultados por meio de métricas adequadas, demonstrando sua aplicação prática ao público definido.

### Descrição

Desenvolver e comparar modelos de Machine Learning de classificação ou regressão para resolver um problema real da solução CitizenTech do grupo. Utilizar dados estruturados, justificar a escolha dos algoritmos e demonstrar como as previsões podem beneficiar o público definido, considerando as condições reais de uso.

Os grupos deverão utilizar algoritmos estudados na disciplina, como **Regressão Linear, Regressão Logística, KNN, Árvore de Decisão, Random Forest, LightGBM, XGBoost ou CatBoost**. Não é necessário utilizar todos, mas é **obrigatória a comparação entre diferentes modelos e a justificativa da escolha final**.

### Datasets e aplicações sugeridas

Pesquisar bases públicas pertinentes ao problema, por exemplo em Kaggle, IBGE, DataSUS, INEP, dados.gov.br ou portais públicos municipais e estaduais. Dados simulados são permitidos, desde que as premissas e limitações sejam documentadas.

- **Saúde:** classificação de risco ou previsão de demanda por atendimentos.
- **Educação:** identificação de risco de evasão ou previsão de desempenho escolar.
- **Mobilidade:** previsão de demanda de transporte ou risco de acidentes.
- **Meio ambiente e cidades:** previsão de qualidade do ar, enchentes ou eventos extremos.
- **Agricultura e comunidades:** previsão de produtividade ou classificação de vulnerabilidade.

### Entregáveis

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

### Critérios de avaliação

| Critério | Peso |
|---|---:|
| Entendimento do problema, escolha dos algoritmos (com justificativa) e implementação | 3,0 |
| Pré-processamento e uso correto de normalização / padronização | 2,0 |
| Interpretação das métricas, tuning e análise de generalização | 2,0 |
| Organização e clareza técnica | 1,5 |
| Aplicação ao contexto CitizenTech e benefício ao público definido | 1,0 |
| Apresentação e vídeo | 0,5 |
| **Total** | **10,0** |

### Observações

O modelo deve estar associado ao mesmo problema e público da solução integradora. Serão avaliadas a consistência metodológica, a interpretação dos resultados e as evidências de funcionamento, não apenas métricas elevadas. Funcionalidades não implementadas devem ser identificadas como evoluções futuras.

---

## 7. Computational Thinking with Python

### Resumo do desafio

Desenvolver em Python uma solução funcional relacionada ao problema CitizenTech escolhido pelo grupo, utilizando estruturas de dados, funções e modularização. A aplicação deverá coletar ou processar dados relevantes ao público definido, apresentar resultados úteis e demonstrar seu funcionamento com casos de teste.

### Contextualização do problema

**Como transformar os dados coletados por dispositivos e sensores em informações úteis para o cidadão?**

No desafio CitizenTech, sensores e dispositivos podem observar situações reais, mas seus dados precisam ser recebidos, validados, processados e disponibilizados. A contribuição de Computational Thinking with Python será desenvolver uma **API REST integrada à solução de AICSS**, considerando o mesmo problema, público e contexto das demais disciplinas. A aplicação deverá permitir que as medições sejam consultadas e utilizadas por outros componentes do projeto.

### Objetivo

Construir e demonstrar um fluxo funcional:

```
ESP32 com sensores → JSON → API REST Python → processamento → CSV → consulta GET
```

A API deve receber leituras do dispositivo (ou de uma simulação compatível), aplicar regras de classificação e registrar um histórico para apoiar análises e outras disciplinas.

### Solução tecnológica

O projeto deverá:
- Desenvolver uma API REST com **Flask ou FastAPI**, incluindo um endpoint **POST** para receber leituras em JSON e validar os campos necessários.
- Processar as informações usando funções, estruturas condicionais, repetições e coleções; classificar as leituras conforme regras relacionadas ao problema CitizenTech.
- Registrar as leituras em **CSV**, com data/hora, valores e classificação; implementar um endpoint **GET** para consultar os registros armazenados.
- Implementar ao menos **um indicador calculado** (como média, total de alertas ou valor máximo) e demonstrar **três cenários de teste** com requisições, respostas e registros.

É aceita a integração com ESP32 físico ou simulado (Wokwi), assim como requisições HTTP simuladas, desde que a API funcione e o JSON seja compatível com AICSS. Interface gráfica, banco de dados e modelo de IA não são obrigatórios. Identifique limitações.

### Informações sobre a entrega

- Capa com título, nomes e RMs.
- Problema, público beneficiado e contribuição da API.
- Arquitetura e origem dos dados; contrato JSON.
- Código Python e instruções de execução.
- Testes dos endpoints, três cenários e histórico CSV.
- Indicador calculado, limitações e relação com um ODS.

### Critérios de avaliação

| Critério | Pontos |
|---|---:|
| Problema e contribuição CitizenTech | 1 |
| API REST e endpoints funcionais | 2 |
| Recebimento e processamento do JSON | 2 |
| Persistência CSV e consulta GET | 2 |
| Lógica, funções e indicador calculado | 2 |
| Testes e demonstração de integração | 1 |
| **Total** | **10** |

---

## 8. Cloud Computing

### Resumo do desafio

Será avaliada a implementação de uma solução completa serverless na nuvem (AWS) para ingestão de dados da CitizenTech, incluindo monitoramento e geração de notificações.

**Título:** Global Solution — CitizenTech · Ingestão Serverless de Dados de Campo: AWS Lambda + RDS + IA

### Cenário

A tecnologia já faz parte do dia a dia das pessoas, mas problemas antigos continuam de pé: enchentes que pegam o bairro de surpresa, queimadas que chegam antes do aviso, estiagem que compromete a safra do pequeno produtor, serviços públicos que só descobrem o problema depois que ele aconteceu. A Global Solution deste semestre pede soluções CitizenTech: tecnologia criada a partir das necessidades reais das pessoas, da grande cidade à comunidade mais remota, com o cidadão no centro da inovação.

Nesta entrega você constrói a espinha dorsal de uma CitizenTech: a camada de nuvem que recebe os dados do mundo real e os transforma em informação útil. Sensores em uma ponte, um drone sobrevoando a lavoura e o celular de um morador do bairro passam a enviar leituras para a mesma API serverless, que registra, classifica e persiste tudo o que chega — pronto para alimentar um painel, um alerta ou uma decisão do poder público.

A ideia central é entender que "IA e nuvem" quase nunca começam treinando modelo. Começam com dado chegando, dado registrado e dado confiável; o modelo pronto, consumido por API, entra depois para dar sentido a esse dado.

### Desafio

Publique uma API serverless na AWS que receba as leituras de um dispositivo de campo (ESP32, drone ou aplicativo do cidadão), mostre no log tudo o que chegou, classifique o nível de risco da leitura e grave o resultado em um banco PostgreSQL gerenciado.

Como nem todo grupo terá hardware disponível, o dispositivo pode ser simulado por software: um script que envia o mesmo JSON que o ESP32 enviaria. A API não distingue um do outro — e é justamente essa indiferença entre o sensor real e o simulador que faz o projeto testável.

### O que você vai exercitar

- Expor uma função Lambda pela Function URL e tratar rotas e método HTTP (GET e POST).
- Ler o corpo de uma requisição vinda de um dispositivo e validar os campos obrigatórios.
- Registrar a telemetria no CloudWatch Logs de forma legível, incluindo o descarte de leituras inválidas.
- Persistir o dado no RDS PostgreSQL a partir de uma função serverless.
- Consumir um modelo de IA pronto por API (Hugging Face) ou um serviço gerenciado (Amazon Comprehend), guardando o token em variável de ambiente e sem segredo no código.
- Simular o comportamento de um dispositivo IoT para validar a ponta a ponta sem depender de hardware.

### Pré-requisitos

Conta AWS com permissão para criar função Lambda e instância RDS PostgreSQL. A função **não deve ser criada dentro de uma VPC**, para que tenha saída para a internet sem configuração adicional. Se você já publicou a função `challenge-api` com Function URL e banco acessível nas atividades anteriores, reaproveite essa base: aqui ela ganha a rota de ingestão.

### Arquitetura

```
ESP32 / drone / app do cidadão          (dispositivo real ou simulador)
            |  HTTPS POST  {dispositivo, gps, métrica, valor, relato}
            v
     AWS Lambda (Function URL)          rota POST /ocorrencias
            |-- log  -> CloudWatch Logs (payload, dispositivo, classificação)
            |-- IA   -> Hugging Face ou Amazon Comprehend (classifica o relato)
            v
     Amazon RDS PostgreSQL              tabela ocorrencias
            |
            v
     Painel / alerta ao cidadão         (consumo via GET /ocorrencias)
```

### Requisitos obrigatórios

1. **Defina o cenário CitizenTech do grupo.** Escolha o problema, quem é o cidadão beneficiado, qual métrica o dispositivo mede e qual o limiar que caracteriza risco. Exemplos: nível de córrego em centímetros, concentração de fumaça em ppm, umidade do solo em porcentagem, temperatura ambiente. O cenário escolhido deve aparecer no README.
2. **Crie a tabela `ocorrencias` no RDS PostgreSQL**, com identificação do dispositivo, tipo, coordenadas, métrica, valor, relato em texto, resultado da análise, nível de risco e data/hora. O script de criação vai na entrega.
3. **Crie a rota `POST /ocorrencias` na Lambda.** Ela deve ler o JSON do corpo, validar os campos obrigatórios (`dispositivo_id`, `metrica`, `valor`), devolver `400` quando faltar campo e `201` com o registro criado quando der certo. Mantenha `GET /health` e acrescente `GET /ocorrencias` para listar o que já foi gravado.
4. **Registre no log tudo o que chega.** A função precisa gravar no CloudWatch, em linhas separadas e legíveis: o payload bruto recebido, os dados interpretados (dispositivo, tipo, GPS, métrica e valor), o resultado da classificação e o `id` gerado na gravação. Leituras inválidas e valores em nível crítico devem sair como `WARNING`.
5. **Classifique o nível de risco da leitura** comparando o valor com os limiares do seu cenário, devolvendo `normal`, `atencao` ou `critico`. Essa classificação é local, não depende de rede e deve funcionar sempre.
6. **Grave o resultado no banco** e devolva na resposta o `id` do registro, o nível de risco e se a leitura dispara alerta ao cidadão.
7. **Construa o simulador do dispositivo.** Um script que assuma a identidade de um ESP32 ou de um drone e envie uma sequência de leituras para a Function URL, com valores evoluindo ao longo do tempo até cruzar o limiar crítico. O simulador deve imprimir, a cada envio, o que mandou e o que a API respondeu. Quem tiver a placa física pode entregar o firmware no lugar do script — o JSON enviado é o mesmo.
8. **Teste de ponta a ponta.** Rode o simulador em um cenário normal e em um cenário de risco, e comprove no CloudWatch que as leituras chegaram e no banco que foram gravadas.

### Camada de IA

Além do limiar numérico, a API deve classificar o relato em texto que acompanha a ocorrência — o que o morador escreveu ao registrar o problema. Escolha um caminho e justifique a escolha na entrega:

- **Caminho A — Hugging Face (recomendado).** Gere um token gratuito do tipo Read, cadastre-o na Lambda como variável de ambiente `HF_TOKEN` e envie o texto ao modelo `cardiffnlp/twitter-xlm-roberta-base-sentiment`, devolvendo o rótulo de maior pontuação com a confiança. A chamada usa apenas `urllib`: nenhuma biblioteca nova entra no pacote. Mantenha o timeout da função em 30 segundos.
  > **Atenção:** o endpoint correto hoje é `https://router.huggingface.co/hf-inference/models/{modelo}` — o antigo `api-inference.huggingface.co` foi desativado e responde erro 410.
- **Caminho B — Amazon Comprehend.** Quem tiver permissão de IAM pode anexar a política `ComprehendReadOnly` à role da Lambda e trocar apenas a função de análise pela detecção de sentimento do Comprehend, com idioma `pt`. O restante da API não muda.

Em qualquer caminho, **a falha do modelo não pode derrubar a ingestão**: se o serviço de IA não responder, a leitura ainda precisa ser classificada por limiar, gravada no banco e registrada no log.

### Entregáveis

- Function URL da Lambda em funcionamento.
- Endpoint do RDS PostgreSQL (sem a senha).
- Script de criação da tabela `ocorrencias`.
- Arquivo final da função Lambda e o código do simulador (ou o firmware do ESP32).
- Quatro evidências em imagem:
  1. a variável de ambiente cadastrada;
  2. o simulador enviando as leituras;
  3. o trecho do CloudWatch Logs com o payload chegando e a classificação;
  4. a consulta no banco com as ocorrências gravadas.
- README com o cenário CitizenTech escolhido, o cidadão beneficiado, os limiares adotados, o caminho de IA usado e o porquê, e o passo a passo para reproduzir a solução.
- Vídeo de até 5 minutos demonstrando o simulador enviando dados, o log recebendo e o banco gravando.

### Critérios de avaliação

| Critério | Peso |
|---|---:|
| Ingestão funcionando: POST recebendo, validando e respondendo corretamente | 25% |
| Observabilidade: log claro do que chega, do que é classificado e do que é descartado | 20% |
| Persistência: modelo de dados coerente e gravação consistente no RDS | 20% |
| Camada de IA integrada com token protegido e falha tratada sem derrubar a ingestão | 15% |
| Simulador do dispositivo e teste de ponta a ponta | 10% |
| Aderência ao CitizenTech: problema real, cidadão identificado, ODS justificado | 10% |

### Conexão com os ODS

Identifique no README a quais Objetivos de Desenvolvimento Sustentável a solução se conecta e de que forma contribui. Os mais diretos neste desafio são o **ODS 3 — Saúde e bem-estar**, o **ODS 10 — Redução das desigualdades** e o **ODS 11 — Cidades e comunidades sustentáveis**, já que levar monitoramento e alerta a lugares onde a infraestrutura é limitada é exatamente o tipo de desigualdade que a tecnologia pode reduzir.

---

## 9. Data Science

### Resumo do desafio

Será avaliada a modelagem e implementação dos dados da solução CitizenTech, utilizando **MySQL/Oracle Data Modeler, Oracle SQL Developer / DbDesigner** e bases **NoSQL (MongoDB, Neo4j, Redis, Cassandra)**. A entrega deverá demonstrar tabelas relacionadas, documentos e consultas em funcionamento, com evidências de execução e justificativa da distribuição dos dados entre Oracle e MongoDB.
