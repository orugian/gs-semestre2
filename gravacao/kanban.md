# Quadro de gestão — CitizenTech (GS 2026.2)

> **Como foi feito este quadro:** o grupo organizou o trabalho em **fatias** (S0, S1…), cada uma com um teste escrito antes do código, revisão e integração no ramo principal. As datas abaixo são as **datas reais de integração** registradas no Git (`git log --merges`). O quadro foi **montado a partir desse histórico** para a apresentação; não houve um quadro Trello/Projects mantido em paralelo. Diga isso no vídeo, se mostrar este arquivo.

## Concluído

| Data | Fatia | Entrega | Disciplinas |
|---|---|---|---|
| 12/11 | S0 | Esqueleto: API com `/health`, bancos de teste em Docker, web inicial, gerador de PDF | todas |
| 12/11 | S1 | Limiares únicos (`limiares.json`): API e Lambda classificam igual | AICSS, CTP, Cloud |
| 12/11 | S6 | Ingestão do Novo Caged em Parquet, com procedência e sem atributos sensíveis | ML, RNA |
| 13/11 | S2 | API de leituras: POST, CSV, GET e indicadores; roda isolada | CTP |
| 13/11 | S7 | Features retrospectivas e divisão temporal com embargo (sem vazamento) | ML, RNA |
| 13/11 | — | Catálogo dos 6 destinos (rascunho para revisão do grupo) | AIC |
| 13/11 | S3 | Outbox durável: reenvio sem duplicar leituras | CTP, Cloud |
| 13/11 | S7b | EDA do treino e baselines | ML |
| 15/11 | S5 | Contas, login seguro, CSRF, limite de tentativas, consentimentos | Cyber |
| 15/11 | S7 | Estatística inferencial; modelos clássicos; rede neural (2 configurações) | Estatística, ML, RNA |
| 16/11 | S8 | Mercado na API (snapshot com hash) e painel técnico | ML, RNA, AIC |
| 16/11 | E05, E08 | Notebooks ML/RNA, slides, programa de Estatística | ML, RNA, Estatística |
| 16/11 | S9 | Currículo com dados pessoais redigidos e confirmação antes da IA | Cyber, Data Science |
| 16/11 | S10, S11 | Extração de competências (IA) e comparação de destinos sem nota única | AIC |
| 16/11 | S4 | Lambda de ingestão + RDS na AWS (Learner Lab) | Cloud |
| 16/11 | E01 | Firmware ESP32 (Wokwi) | AICSS |
| 16/11 | S12, S13, S14 | Plano, exercício diagnóstico (50% objetiva, 50% IA), laboratório | AIC |
| 16/11 | S15 | Telas da jornada + testes ponta a ponta e acessibilidade (axe) | AIC, Cyber |
| 17/11 | — | Data Modeler (modelos lógico e relacional), capturas AWS, Wokwi executado | Data Science, Cloud, AICSS |
| 17/11 | S16 | Redesenho visual e foco visível por teclado | AIC |
| 17/11 | S17, S18 | Organização do código (API, ferramentas, web) | todas |

## Em andamento / a fazer

| Item | Responsável |
|---|---|
| Gravar vídeos (AIC, ML, RNA, Cyber, Cloud) | grupo |
| Revisar e enviar arquivos no Portal até 19/11 23h55 | grupo |

## Cortes e decisões de escopo (gestão)

- **6 → 3 destinos no ML e no app:** a revisão das rubricas atrasou; o corte previsto no plano entrou automaticamente. As rubricas dos 6 foram aprovadas depois, mas o MVP ficou com 3.
- **Holdout 2026 fechado:** nenhum modelo foi promovido; o app mostra o baseline sazonal.
- **Sentimento na nuvem:** a conta do Learner Lab nega o Comprehend; a ingestão continua sem ele (limitação declarada).
