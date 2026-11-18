# Handoff CitizenTech — fechamento técnico, 17/11/2026

O nome deste arquivo foi mantido para preservar os links. O [estado](estado.md) registra os comandos e resultados. Prazo acadêmico: **19/11/2026 às 23h55 (Brasília)**. Entrega no Portal e vídeos não estão concluídos.

## Onde retomar

Começar pelo [README de reprodução](../README.md) e conferir `git status`, `git worktree list` e `git ls-remote gs-semestre2 refs/heads/main`. A interface NOUS, o foco por teclado e a tabela do painel já estão integrados (`48be785`, `a14ebef`, `d8700ab`); o código anterior a esses commits não é a interface a gravar. Use também o preparo de QA integrado em `8dbe4f7`: o ambiente usa o schema local de teste e uma outbox nova, não a persona do app. O runner foi validado com `-SemML`, e o Playwright com a API do checkout atual (6 passaram; persona fora desta rodada). Não usar `origin` como destino de publicação.

| Item da fila | Situação e próximo passo |
|---|---|
| P01 · Ambiente | Não interferir nos worktrees `S5-auth`/`S5-red`, no agente da outra frente nem nos volumes compartilhados. |
| P03 · Cloud | As quatro categorias de imagem foram obtidas. O alerta CloudWatch de **16/11** é o **id 8**; o terminal e SELECT de **17/11** mostram os **ids 12–19**. Usar o [inventário](../06_Cloud/README.md) e o [registro da rodada](../06_Cloud/evidencias/20261117_rodada_function_url.txt). Não é necessário repetir a rodada para comprovar o que já está registrado. |
| P04 · Data Modeler | Concluído pelo agente: [projeto nativo e exportações](../03_DataScience/evidencias/20261117_datamodeler/). Não refazer nem pedir a modelagem ao grupo. |
| P05 · QA | [Teste de foco](../app/web/e2e/foco_visivel.spec.ts), [teste da tabela](../app/web/e2e/painel_tabela.spec.ts) e [limites da sondagem](../02_Cybersecurity/evidencias/20261117_qa_teclado_foco.md). Não alegar certificação WCAG, teste de leitor de tela nem cobertura de toda combinação de navegador e dispositivo. |
| P06 · Ciência | Os notebooks entregues são cópias idênticas às fontes, com saídas salvas. Para a demonstração, usar essas saídas e o [aceite de validação retrospectiva](../05_ML/evidencias/20261115_modelos_mvp_aceite.md), sem treino, retuning, promoção ou abertura de 2026. |
| P07 · Pacote | Depois de incorporar **material novo**, gerar/conferir com os [comandos do empacotador](../README.md#gerar-e-conferir-as-entregas). Conferir Cyber ≤15 páginas. Preservar originais; entregar apenas versões revistas e tarjadas, nunca toda a pasta de trabalho indiscriminadamente. |
| P02 · Vídeos (última etapa de produção) | Grupo grava com o [kit de gravação](../gravacao/README.md) (scripts de preparo para qualquer computador + roteiros AIC, ML, RNA, Cyber e Cloud). Cada `video.md` guarda só o link. Só preencher os links depois de testar duração e acesso sem login. |
| P08 · Portal | Grupo envia seguindo o `LEIA-ME.md` de cada pasta `0X_*`. Estatística: PDF, PY e CSV **separados**. Guardar a confirmação do Portal. |

## Limites para a gravação

- **Wokwi → API isolada → CSV** e **simulador de software → Lambda → RDS** são demonstrações distintas. Não soltar os eventos antigos, chamar o sensor virtual de bancada física nem atribuir sentimento válido ao Comprehend. Ver [aceite Wokwi](../01_AICSS/evidencias/20261117_wokwi_aceite.md).
- Se a gravação Cloud exigir operação ao vivo, conferir health naquela data e reconfirmar as autorizações pertinentes antes de gasto ou mudança AWS. Não alterar SG, IAM ou recursos para obter um print.
- Segredos ficam em memória; não exibir terminais com credenciais, variáveis ou dados de conta. Não pedir URLs antes da gravação e não inventar links, métricas ou relatos.

**Skills sugeridas para a retomada:** `handoff` para checkpoint; `impeccable` somente se houver nova QA visual; `wordcraft` se for preciso regerar/inspecionar documentos (respeitar o pipeline D19).
