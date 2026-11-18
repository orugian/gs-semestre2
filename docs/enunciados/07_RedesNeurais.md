# Redes Neurais

> Disciplina (nome oficial): **Redes Neurais Artificiais, Deep Learning e Algoritmos Genéticos**  
> Entrega no Portal do Aluno até **19/11/2026 às 23h55**. Fonte completa: `docs/GS2_2026_enunciados.md` e `docs/material_por_cadeira/`.
>
> **Resumo no PDF geral da GS:** Será avaliada a aplicação de modelos de redes neurais ao problema CitizenTech, por meio de tarefas como classificação, previsão, detecção de anomalias ou reconhecimento de padrões, conforme a proposta do grupo. A entrega deverá demonstrar a implementação ou simulação funcional, com métricas e testes, interpretando criticamente os resultados em relação ao problema, ao público atendido e aos benefícios esperados.

## Resumo do desafio

Nesta disciplina, o desafio é desenvolver e avaliar uma **Rede Neural Artificial** capaz de resolver uma tarefa relacionada ao problema escolhido pelo grupo. O modelo deverá processar dados, identificar padrões, realizar classificações ou previsões e gerar resultados que possam contribuir para a solução CitizenTech proposta.

O objetivo não é apenas treinar uma rede neural, mas demonstrar que o modelo funciona, avaliar seu desempenho e justificar as decisões tomadas durante seu desenvolvimento.

## Etapas obrigatórias

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

## Sugestões de datasets

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

## Entregáveis

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

## Critérios de avaliação — 10 pontos

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

## Orientações gerais

- O projeto deve utilizar o mesmo problema, público e contexto definidos pelo grupo para a Global Solution, mantendo a integração entre as disciplinas.
- A rede neural deve ter uma função clara dentro da solução proposta.
- Não é obrigatório desenvolver um dispositivo físico. Simulações são permitidas, desde que apresentem evidências verificáveis de funcionamento.
- Funcionalidades que não forem implementadas devem ser identificadas como possibilidades de evolução futura.
- Considerar aspectos de acessibilidade, segurança, proteção de dados, sustentabilidade e condições reais de utilização.

**Identificação:** a entrega deve conter uma capa com o nome completo e RM de todos os integrantes.
