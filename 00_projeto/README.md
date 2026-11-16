# CitizenTech — GS2026.2

**Integrantes (nome completo+RM):**
- Guilherme Orugian — RM572882
- Lucas Henrique — RM571901
- Rodrigo Bettio — RM573725

Prazo de todas as entregas: **19/11/2026 às23h55** (Portal do Aluno).

## Comece por aqui

- [Estado atual e próxima sessão](<../docs/estado.md>) — checkpoint operacional, restrições e pendências.
- [Plano aprovado](<../docs/plano_desenvolvimento.md>) — decisões D01–D25, contratos, fatias e mínimos das9 disciplinas.
- [Proposta e terminologia](<../docs/proposta_transicao_carreira.md>) — visão e limites; contém também contexto histórico, não um status de implementação.
- [Revisão adversarial](<../docs/revisao_adversarial_plano.md>) — achados R01–R30.

## Problema, público e proposta

Profissionais já graduados e experientes encontram informações fragmentadas ao comparar transições de carreira. CitizenTech pretende organizar experiência, distinguir competências declaradas e demonstradas, comparar até três caminhos e orientar preparação com fontes e limites explícitos. Não é seleção de candidatos, promessa de recolocação ou previsão individual de contratação.

O recorte atual do MVP é **Dados/BI, Monitoramento/IoT e Processos/Melhoria Contínua**. O corte R29 não aprovou rubricas nem eliminou o material dos outros destinos. Estatística mantém seis grupos ocupacionais por decisão científica expressa. ODS4 e10 são principais; não há impacto social comprovado apenas por implementar software.

## Implementação não é entrega concluída

**Implementado e verificado na etapa de15/16 de novembro:** API local de leituras, outbox/idempotência, autenticação/consentimentos com Oracle real, ingestão/features Caged, modelos ML/RNA e análise municipal real. Última regressão integrada ML/RNA/Estatística:227testes; API208testes com Oracle na etapaS5. Esses números não são uma única suíte nem uma nova execução nesta atualização documental.

**Ainda faltam:** servir os modelos com metadados/model cards, jornada de currículo/PII/LLM/comparação/plano/avaliação, firmware e Cloud reais, telas funcionais e E2E, notebooks/slides e pacotes acadêmicos finais. O frontend atual é um esqueleto; o app ainda não funciona ponta a ponta.

- [Evidência real ML/RNA](<../05_ML/evidencias/20261115_modelos_mvp_aceite.pdf>) — PDF preliminar,3páginas.
- [Evidência real Estatística](<../08_Estatistica/evidencias/20261115_d11_aceite.pdf>) — PDF preliminar,3páginas.
- [Aceite da S5](<../02_Cybersecurity/evidencias/20261115_s5_aceite_integracao.md>).

## Arquitetura e contrato único

Código executável próprio fica em `app/`: FastAPI, React/Astryx, ML/RNA em CPU, dados em Oracle/Mongo e integração prevista com Lambda/RDS. A cadeia de sensores/CTP possui API e outbox locais; a ligação real com firmware e nuvem ainda é pendente. Os sensores são instrumento didático de avaliação de competência, não dados de mercado de trabalho.

O contrato HTTP é o do plano§3 e dos [schemas da API](<../app/api/src/citizentech/leituras/esquemas.py>), não um JSON de exemplo mantido em paralelo neste README. Os limiares têm fonte única em [limiares.json](<../app/config/limiares.json>); não duplicá-los nas cópias do professor. Novo evento responde201, reenvio idêntico200 e conflito409; risco e estado do firmware são conceitos diferentes.

## Dependências humanas e segurança

Revisão das três rubricas, acessos de infraestrutura, Data Modeler, ideia efetiva da live, vídeos e envio no Portal continuam pendentes. Não inventar o conteúdo da live nem resultados de uso por participantes.

**Holdout fechado, nenhum modelo promovido.** Segredos não pertencem ao chat/relatórios; não apagar dados nem liberar envio da outbox antiga à nuvem. APIs pagas, recursos AWS, limpeza de dados e push exigem autorização conforme o estado e o CLAUDE. Documentos-modelo do professor são referências e não devem ser editados como implementação própria.
