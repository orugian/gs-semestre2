# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Produto: profissionais graduados e experientes comparando caminhos de transição de carreira. Não é seleção de candidatos por empregadores.

Artefato solicitado em16/11/2026: caderno visual interno para o responsável e a equipe entenderem o projeto e retomarem o desenvolvimento. Público/formato offline e responsivo confirmados por pergunta estruturada nesta sessão.

## Product Purpose

CitizenTech organiza experiência e evidências, distingue competências declaradas/demonstradas e pretende apoiar comparação e preparação para transição. A documentação visual explica implementação, arquitetura, lacunas e próximos gates; não demonstra uma jornada já concluída.

A autoridade de produto continua em [plano aprovado](<docs/plano_desenvolvimento.md>), [proposta](<docs/proposta_transicao_carreira.md>) e [CLAUDE.md](<CLAUDE.md>). Este registro não altera D01–D25.

## Operating Context

Projeto acadêmico FIAP GS2026.2, nove disciplinas, prazo19/11/2026às23h55. Estado operacional em [estado.md](<docs/estado.md>). Pessoas também precisam produzir vídeos, Data Modeler e submissões no Portal.

## Capabilities and Constraints

- API local, outbox, autenticação/consentimentos, ingestão/features e experimentos científicos estão implementados nos limites do estado.
- Interface atual é esqueleto; serving/model cards e jornada profissional/LLM/Cloud/firmware/E2E não estão concluídos.
- MVP de produto: três destinos R29. Estatística: seis destinos/todas as escolaridades. Não misturar coortes.
- Holdout2026 fechado; nenhum modelo promovido. Ganho de validação não garante emprego nem promoção automática.
- Panorama: um HTML estático autossuficiente com CSS local, sem rede, dependências novas, dados ao vivo ou autenticação. Não alterar `app/web` para produzi-lo.
- Não expor dados cadastrais da equipe, segredos, currículo ou eventos pessoais no documento visual.

## Evidence on Hand

Fontes reais do panorama: [checkpoint](<docs/estado.md>), [evidência ML/RNA](<05_ML/evidencias/20261115_modelos_mvp_aceite.md>) e [evidência D11](<08_Estatistica/evidencias/20261115_d11_aceite.md>). Resultados são retrospectivos e não demonstram aplicação integrada em produção. Nenhum testemunho de usuários ou impacto social foi medido.

## Product Principles

1. Distinguir observado, previsto, simulado e futuro.
2. Mostrar fonte, população, unidade e referência temporal.
3. Não converter experiência declarada em competência demonstrada nem criar score único.
4. Não fabricar dados/evidências ou esconder resultados fracos.
5. Documentação não deve parecer funcionalidade entregue quando é trabalho futuro.

## Accessibility & Inclusion

Leitura em português, desktop e mobile web; navegação por teclado, foco visível, contraste e sem dependência exclusiva de cor. Documento deve funcionar offline e permitir impressão. Linguagem direta, sem jargão desnecessário ou promessa de recolocação.
