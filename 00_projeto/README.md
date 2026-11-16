# CitizenTech — GS2026.2

**Integrantes (nome completo+RM):**
- Guilherme Orugian — RM572882
- Lucas Henrique — RM571901
- Rodrigo Bettio — RM573725

Prazo de todas as entregas: **19/11/2026 às23h55** (Portal do Aluno).

## Comece por aqui

- [Estado atual e próxima sessão](<../docs/estado.md>) — checkpoint operacional, restrições e pendências.
- [Panorama visual offline](<../docs/panorama_projeto.html>) — arquitetura, resultados,9disciplinas e próximos gates; documento, não app.
- [Plano aprovado](<../docs/plano_desenvolvimento.md>) — decisões D01–D25, contratos, fatias e mínimos das9 disciplinas.
- [Proposta e terminologia](<../docs/proposta_transicao_carreira.md>) — visão e limites; contém também contexto histórico, não um status de implementação.
- [Revisão adversarial](<../docs/revisao_adversarial_plano.md>) — achados R01–R30.

## Problema, público e proposta

Profissionais já graduados e experientes encontram informações fragmentadas ao comparar transições de carreira. CitizenTech pretende organizar experiência, distinguir competências declaradas e demonstradas, comparar até três caminhos e orientar preparação com fontes e limites explícitos. Não é seleção de candidatos, promessa de recolocação ou previsão individual de contratação.

O recorte atual do MVP é **Dados/BI, Monitoramento/IoT e Processos/Melhoria Contínua**. As rubricas dos seis destinos foram revisadas e aprovadas pelo grupo em 16/11 (mínimos 0,5/0,5); como isso ocorreu após o prazo D3, o recorte R29 de três destinos no MVP permanece, sem eliminar o material dos outros. Estatística mantém seis grupos ocupacionais por decisão científica expressa. ODS4 e10 são principais; não há impacto social comprovado apenas por implementar software.

## Implementação não é entrega concluída

**Implementado e verificado até 16/11:** API local de leituras, outbox/idempotência, autenticação/consentimentos (Oracle real na etapa S5), ingestão/features Caged, modelos ML/RNA, análise municipal real, **API de mercado** (`/mercado/{destino}` com abstenção e metadados; `/mercado/{destino}/modelos` com os 6 modelos, nenhum promovido), **tela web de Mercado e Painel técnico**, **programa estatístico portátil com relatório** e **notebooks ML/RNA executados com slides**. Regressão em 16/11: ML 266, API 221 com Oracle local, Cloud 50, Tools 20, Web 17 + build.

**Ainda faltam:** jornada de currículo/PII/LLM/comparação/plano/avaliação/laboratório, firmware e Cloud reais, login na web, E2E, empacotamento das entregas e PDFs finais, relatórios de Cyber/CTP/Data Science/AICSS/Cloud. O app ainda não funciona ponta a ponta.

- [Estado detalhado](<../docs/estado.md>) — o que foi verificado, como demonstrar o mercado e pendências.
- [Evidência real ML/RNA](<../05_ML/evidencias/20261115_modelos_mvp_aceite.md>) · [notebook ML](<../app/ml/notebooks/ml_mercado.ipynb>) · [notebook RNA](<../app/ml/notebooks/rna_mercado.ipynb>) · [slides ML](<../05_ML/slides.md>).
- [Relatório estatístico](<../08_Estatistica/relatorio.md>) — rascunho final; PDF ainda não empacotado.
- [Aceite da S5](<../02_Cybersecurity/evidencias/20261115_s5_aceite_integracao.md>).

## Arquitetura e contrato único

Código executável próprio fica em `app/`: FastAPI, React/Astryx, ML/RNA em CPU, dados em Oracle/Mongo e integração prevista com Lambda/RDS. A cadeia de sensores/CTP possui API e outbox locais; a ligação real com firmware e nuvem ainda é pendente. Os sensores são instrumento didático de avaliação de competência, não dados de mercado de trabalho.

O contrato HTTP é o do plano§3 e dos [schemas da API](<../app/api/src/citizentech/leituras/esquemas.py>), não um JSON de exemplo mantido em paralelo neste README. Os limiares têm fonte única em [limiares.json](<../app/config/limiares.json>); não duplicá-los nas cópias do professor. Novo evento responde201, reenvio idêntico200 e conflito409; risco e estado do firmware são conceitos diferentes.

## Dependências humanas e segurança

Decisões de 16/11: rubricas aprovadas, Atlas acessível, AWS Learner Lab ativo e evidências de banco relacional **somente no Oracle local** (Oracle FIAP fora de escopo). Continuam pendentes: Data Modeler, prints do console AWS (sob instrução do agente), ideia efetiva da live, vídeos e envio no Portal. Não inventar o conteúdo da live nem resultados de uso por participantes.

**Holdout fechado, nenhum modelo promovido.** Segredos não pertencem ao chat/relatórios; não apagar dados nem liberar envio da outbox antiga à nuvem. APIs pagas, recursos AWS, limpeza de dados e push exigem autorização conforme o estado e o CLAUDE. Documentos-modelo do professor são referências e não devem ser editados como implementação própria.
