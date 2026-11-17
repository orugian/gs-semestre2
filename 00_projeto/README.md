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

**Integrado até 16/11:** API de leituras/outbox/idempotência, mercado e painel técnico; jornada web com conta, consentimentos, intenção, currículo redigido e confirmado, revisão de competências, comparação de até três destinos, plano, exercício diagnóstico e laboratório. A persona de demonstração foi exercitada no Edge. Lambda e RDS foram executados na AWS real; Comprehend retornou **AccessDenied**, com sentimento `indisponivel`. Notebooks ML/RNA, slides, programa estatístico portátil, relatórios acadêmicos e cópias de código foram gerados; nenhum modelo promovido e holdout 2026 fechado. Comandos e resultados de cada aceite estão no [estado operacional](<../docs/estado.md>).

**Aceites desta retomada:** E2E/acessibilidade integrada em `e7c533a` (11 telas + modal sem violações axe; 3 E2E contra API teste e persona separada contra API app). Firmware compilado e **executado no Wokwi em17/11**:3cenários,6HTTP201/6registros CSV; GPIO confirma LED0/1/1 e PWM1.000Hz só no crítico. [Capturas e aceite Wokwi](<../01_AICSS/evidencias/20261117_wokwi_aceite.md>). Revisão nº2 adjudicada, sem aprovação acadêmica total. **Fechamento pendente:** Data Modeler, capturas Cloud, vídeos e Portal; repetir o empacotador após qualquer alteração. Identificação do grupo foi confirmada pelo usuário e aplicada aos documentos; os seis PDFs foram regenerados e conferidos, e o empacotador passou em `--verificar`. Revisão independente nº 2 e adjudicação estão em [conformidade](<../docs/revisao_conformidade_2.md>), sem aprovação total enquanto faltam as evidências e entregas humanas. O código integrado e as evidências históricas não equivalem à entrega acadêmica concluída. Na retomada de 16/11 à noite, o health respondeu HTTP 502; após o reinício humano do Learner Lab, voltou a HTTP 200 com `status=ok`, `banco=ok` (evidência de health em Cloud).

- [Estado detalhado](<../docs/estado.md>) — o que foi verificado, como demonstrar o mercado e pendências.
- [Handoff de encerramento de 17/11](<../docs/handoff_citizentech_20261116_fim.md>) — base funcional `f96b13e`, fila P01–P08, responsabilidades humanas e verificações ainda não feitas. Priorizar entrega acadêmica; não repetir S15/Wokwi nem reabrir fatias integradas.
- [Evidência real ML/RNA](<../05_ML/evidencias/20261115_modelos_mvp_aceite.md>) · [notebook ML](<../app/ml/notebooks/ml_mercado.ipynb>) · [notebook RNA](<../app/ml/notebooks/rna_mercado.ipynb>) · [slides ML](<../05_ML/slides.md>).
- [Relatório estatístico](<../08_Estatistica/relatorio.md>) e [PDF gerado](<../08_Estatistica/relatorio.pdf>) — conferir identificação e versão final no empacotamento.
- [Aceite da S5](<../02_Cybersecurity/evidencias/20261115_s5_aceite_integracao.md>).

## Arquitetura e contrato único

Código executável próprio fica em `app/`: FastAPI, React/Astryx, ML/RNA em CPU, dados em Oracle/Mongo e integração implementada com Lambda/RDS. A API e a outbox locais foram exercitadas até a AWS real com simulador por software. Separadamente, o ESP32 virtual foi executado no Wokwi até a API CTP isolada/CSV, com sensores e atuadores medidos; esse lote **não** foi enviado à AWS. Os sensores são instrumento didático de avaliação de competência, não dados de mercado de trabalho.

O contrato HTTP é o do plano§3 e dos [schemas da API](<../app/api/src/citizentech/leituras/esquemas.py>), não um JSON de exemplo mantido em paralelo neste README. Os limiares têm fonte única em [limiares.json](<../app/config/limiares.json>); não duplicá-los nas cópias do professor. Novo evento responde201, reenvio idêntico200 e conflito409; risco e estado do firmware são conceitos diferentes.

## Dependências humanas e segurança

Decisões de 16/11: rubricas aprovadas, Atlas acessível e evidências de banco relacional **somente no Oracle local** (Oracle FIAP fora de escopo). AWS depende da disponibilidade do Learner Lab; o health precisa retornar `banco=ok` antes de nova demonstração. Em17/11 o usuário determinou **Data Modeler pelo agente** e informou o **Learner Lab reativado** (novo health ainda pendente). Continuam humanos: prints do console autenticado AWS sob orientação do agente, ideia efetiva da live, vídeos e Portal. [Guia exato de capturas](<../docs/historico/guia_capturas_learner_lab.md>). Não inventar o conteúdo da live nem resultados de uso por participantes.

**Holdout fechado, nenhum modelo promovido.** Segredos não pertencem ao chat/relatórios; não apagar dados nem liberar envio da outbox antiga à nuvem. APIs pagas, recursos AWS, limpeza de dados e push exigem autorização conforme o estado e o CLAUDE. Documentos-modelo do professor são referências e não devem ser editados como implementação própria.
