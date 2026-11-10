# AI Computer Systems e Sensors (AICSS)

> Disciplina (nome oficial): **AI Computer Systems and Sensors**  
> Entrega no Portal do Aluno até **19/11/2026 às 23h55**. Fonte completa: `docs/GS2_2026_enunciados.md` e `docs/material_por_cadeira/`.

## Resumo do desafio

Criar um dispositivo IoT usando ESP32 (Wokwi ou físico) com pelo menos 2 sensores e 1 atuador, que coleta os dados, classifica cada sensor com um status e emite o alerta no local. Enviar as leituras em JSON a um servidor externo, que exibe e grava os dados. Demonstrar pelo menos 3 comportamentos diferentes. A solução deve justificar como os sensores escolhidos servem ao problema do cidadão atendido e deve trazer uma inovação.

## Contextualização

**Como um dispositivo com sensores pode perceber um problema antes que ele afete alguém?**

A vida cotidiana está repleta de fenômenos observáveis. Os dados existem, mas precisam ser capturados, medidos e analisados. Durante a jornada da disciplina realizou-se a coleta de medições dos sensores, tratamento dessas medições, notificações (em texto e em atuadores), transmissão de dados, entre outros recursos. Por isso, a contribuição de AICSS para o Desafio CitizenTech visa dar apoio às pessoas nas cidades, no campo ou nas comunidades usando dispositivos e sensores. Nesta GS, deve-se desenvolver o dispositivo que coleta os dados da solução CitizenTech, com o mesmo problema, o mesmo público e o mesmo contexto das demais disciplinas.

## Objetivo

Construir e demonstrar um fluxo funcional:

```
Fenômeno observado → ESP32 com sensores → alerta local → JSON → servidor Python
```

O dispositivo deve alertar o cidadão no próprio local e enviar os dados para a solução integrada. No servidor eles poderão ser usados pela IA desenvolvida nas outras disciplinas.

## Solução tecnológica

O projeto deverá:
- Usar um ESP32, simulado (Wokwi) ou físico, com **pelo menos 2 sensores** relevantes ao problema e **pelo menos 1 atuador** (LED, buzzer, entre outros).
- Coletar os dados, controlar limiares, organizar a leitura e classificar cada sensor com um status (ex.: OK / ALERTA).
- Enviar as leituras em JSON a um servidor Python, que exibe e grava os dados em CSV.
- Demonstrar **pelo menos 3 comportamentos diferentes**, mostrando a reação do atuador, o JSON transmitido e o registro no servidor.

São aceitos protótipos físicos ou simulados, com evidências da execução. Identifique o que foi implementado ou simulado e explique as limitações.

## Informações sobre a entrega

- Capa com título, nomes e RMs.
- Problema, público beneficiado e evidência de sua relevância.
- Arquitetura da solução e origem dos dados.
- Evidências de funcionamento, resultados dos testes com diferentes entradas e limitações identificadas.
- Código desenvolvido.
- Relação com pelo menos um ODS.

## Critérios de avaliação

| Critério | Pontos |
|---|---:|
| Problema e contribuição CitizenTech | 1 |
| Coleta e decisão com dados IoT | 3 |
| Transmissão de dados usando JSON | 3 |
| Justificativa dos sensores utilizados e alinhamento com a solução adotada | 2 |
| Inovação apresentada | 1 |
| **Total** | **10** |
