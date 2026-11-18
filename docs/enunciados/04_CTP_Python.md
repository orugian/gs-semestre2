# Computational Thinking with Python

> Disciplina (nome oficial): **Computational Thinking with Python**  
> Entrega no Portal do Aluno até **19/11/2026 às 23h55**. Fonte completa: `docs/GS2_2026_enunciados.md` e `docs/material_por_cadeira/`.

## Resumo do desafio

Desenvolver em Python uma solução funcional relacionada ao problema CitizenTech escolhido pelo grupo, utilizando estruturas de dados, funções e modularização. A aplicação deverá coletar ou processar dados relevantes ao público definido, apresentar resultados úteis e demonstrar seu funcionamento com casos de teste.

## Contextualização do problema

**Como transformar os dados coletados por dispositivos e sensores em informações úteis para o cidadão?**

No desafio CitizenTech, sensores e dispositivos podem observar situações reais, mas seus dados precisam ser recebidos, validados, processados e disponibilizados. A contribuição de Computational Thinking with Python será desenvolver uma **API REST integrada à solução de AICSS**, considerando o mesmo problema, público e contexto das demais disciplinas. A aplicação deverá permitir que as medições sejam consultadas e utilizadas por outros componentes do projeto.

## Objetivo

Construir e demonstrar um fluxo funcional:

```
ESP32 com sensores → JSON → API REST Python → processamento → CSV → consulta GET
```

A API deve receber leituras do dispositivo (ou de uma simulação compatível), aplicar regras de classificação e registrar um histórico para apoiar análises e outras disciplinas.

## Solução tecnológica

O projeto deverá:
- Desenvolver uma API REST com **Flask ou FastAPI**, incluindo um endpoint **POST** para receber leituras em JSON e validar os campos necessários.
- Processar as informações usando funções, estruturas condicionais, repetições e coleções; classificar as leituras conforme regras relacionadas ao problema CitizenTech.
- Registrar as leituras em **CSV**, com data/hora, valores e classificação; implementar um endpoint **GET** para consultar os registros armazenados.
- Implementar ao menos **um indicador calculado** (como média, total de alertas ou valor máximo) e demonstrar **três cenários de teste** com requisições, respostas e registros.

É aceita a integração com ESP32 físico ou simulado (Wokwi), assim como requisições HTTP simuladas, desde que a API funcione e o JSON seja compatível com AICSS. Interface gráfica, banco de dados e modelo de IA não são obrigatórios. Identifique limitações.

## Informações sobre a entrega

- Capa com título, nomes e RMs.
- Problema, público beneficiado e contribuição da API.
- Arquitetura e origem dos dados; contrato JSON.
- Código Python e instruções de execução.
- Testes dos endpoints, três cenários e histórico CSV.
- Indicador calculado, limitações e relação com um ODS.

## Critérios de avaliação

| Critério | Pontos |
|---|---:|
| Problema e contribuição CitizenTech | 1 |
| API REST e endpoints funcionais | 2 |
| Recebimento e processamento do JSON | 2 |
| Persistência CSV e consulta GET | 2 |
| Lógica, funções e indicador calculado | 2 |
| Testes e demonstração de integração | 1 |
| **Total** | **10** |
