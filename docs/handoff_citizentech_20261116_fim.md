# Handoff CitizenTech — encerramento em 17/11/2026

> Arquivo canônico mantido com o nome original para não quebrar as referências. **Checagem de encerramento: 17/11, 08h51 (UTC−3)**. Prazo: **19/11/2026, 23h55**; faltavam 2 dias e 15 horas. Implementação aceita não significa entrega acadêmica concluída.

**Atualização expressa do usuário em17/11, após o encerramento:** **Data Modeler será executado pelo agente, não pelo usuário** (D25/CLAUDE§12 atualizados). O usuário também informou que **reativou o Learner Lab para a próxima sessão**; health ainda não revalidado pelo agente. Essas instruções substituem a atribuição humana anterior somente para Data Modeler.

## 0. Atualização de 17/11, ~10h45 — o que mudou na fila

- **P03 Cloud — imagens concluídas.** Health 200; rodada nova 13:09–13:13Z (ids 12–19, 400, 401); prints SIM e DB capturados pelo agente; CW-C/D/K do usuário (rodada de 16/11) tarjados e incorporados. Pendente só o **vídeo Cloud** (humano). Opcional: print CloudWatch da janela 13:09:50Z–13:13:00Z.
- **P04 Data Modeler — concluído pelo agente.** Ver [estado §00](<estado.md>) e [`03_DataScience/evidencias/20261117_datamodeler/`](<../03_DataScience/evidencias/20261117_datamodeler/>).
- **P05 QA — parcial.** PDFs inspecionados por folha de contato; CTP corrigido (Wokwi já executado → CSV). Teclado em 4 telas; achado de foco fraco em Mercado/login **aguarda decisão** (corrigir reabre CSS integrado).
- **P02 vídeos/links — nada recebido.** Próximo passo depende do grupo: gravar/publicar e enviar as 5 URLs (AIC obrigatório; RNA obrigatório).
- P06–P08 inalterados.

## 1. Ponto de parada

**Base funcional publicada: `f96b13e` em `main` e `gs-semestre2/main`.** Working tree limpa e zero commits pendentes nesse remoto antes desta atualização documental. O upstream mostrado por `git status` ainda é `origin/main`; seu atraso é esperado. **Não resetar/rebasear para origin**, nem enviar para esse remoto por engano. O commit que contém esta versão do handoff é somente de encerramento/documentação.

S15 foi integrada e aceita; o agente também concluiu os três cenários do Wokwi, de sensores virtuais até a API isolada/CSV, com GPIO medido. PDF AICSS atualizado. **Não repetir o aceite de S15, a busca de token ou o diagnóstico do upload Wokwi.** Resumo numérico e limites no [estado §0–§3](<estado.md>); comandos, RED/GREEN e arquivos brutos nos aceites abaixo.

## 2. Mapa mínimo de arquivos

| Assunto | Fonte para retomar |
|---|---|
| Regras e operação | [CLAUDE](<../CLAUDE.md>), depois [estado §0](<estado.md>) |
| Critérios acadêmicos e decisões | [Plano](<plano_desenvolvimento.md>) e enunciado da disciplina em trabalho; [conformidade nº2](<revisao_conformidade_2.md>) |
| S15, a11y, persona, testes e limitações | [Aceite S15](<../02_Cybersecurity/evidencias/20261116_s15_e2e_aceite.md>) |
| Firmware/Wokwi, prints, Serial, VCD, CSV e hashes | [Aceite Wokwi](<../01_AICSS/evidencias/20261117_wokwi_aceite.md>), [manifesto](<../01_AICSS/evidencias/20261117_wokwi_manifesto.json>), [relatório](<../01_AICSS/relatorio.md>) |
| Capturas AWS que faltam, passos exatos e limites reais | [Guia de capturas Learner Lab](<guia_capturas_learner_lab.md>) e [inventário Cloud §8–§9](<../06_Cloud/README.md>) |
| Data Modeler | [Data Science §2](<../03_DataScience/relatorio.md#L24-L31>), [SQL consolidado](<../03_DataScience/oracle.sql>) |
| Roteiros e locais dos links de vídeo | [AIC](<../09_AIC/video.md>), [ML](<../05_ML/video.md>), [Cyber](<../02_Cybersecurity/video.md>), [Cloud](<../06_Cloud/video.md>), [RNA](<../07_RedesNeurais/video.md>) |
| Gerar/conferir entregas | [Empacotador](<../app/tools/empacotar_entregas.py>), [conversor PDF](<../app/tools/md_para_pdf.py>), [manifesto do pacote](<entregas_manifesto.json>) |

Não tratar “pendente” em **evidência histórica datada** como estado atual: alguns snapshots antecedem integrações já concluídas. Não reescrever esses registros para apagar a história.

## 3. Ordem de trabalho da próxima sessão

| ID / prioridade | Responsável | Ação e critério para fechar |
|---|---|---|
| P01 — início | Agente | Executar ritual do CLAUDE: data/prazo/disco, Git/remotos/worktrees/processos e serviços necessários. Ler estado/handoff antes de agir. Ver quais arquivos humanos novos realmente chegaram. Nenhuma implementação nova neste encerramento. |
| P02 — crítica, em paralelo | Humano + agente | **Vídeos e live:** preparar demonstração e auxiliar tecnicamente; grupo grava/publica e fornece URLs. AIC é obrigatório para pontuar, RNA também exige vídeo. Validar duração/acesso e inserir links nos cinco roteiros; nunca fabricar vídeo, fala da live ou relato de gestão. |
| P03 — crítica, em paralelo | Humano + agente | **Cloud:** usuário informou Lab já reativado; agente deve validar health antes de pedir novo reinício, executar a rodada autorizada e informar horários/IDs para captura. Humano captura console autenticado conforme o guia; agente prepara simulador/SQL e tenta as capturas locais reais. Sem confundir saída histórica/Wokwi local com AWS; não alterar recursos/permissões nem gastar quota sem autorização aplicável. |
| P04 — alta, em paralelo | **AGENTE** | **Data Modeler:** determinação direta do usuário17/11. Verificar ferramenta/automação suportada; conduzir importação dos DDL001–007/19c no Modeler real, gerar modelos lógico/relacional, salvar projeto nativo e exportar imagem/PDF. Conferir as16tabelas/chaves/relações e atualizar Data Science/PDF. Se faltar ferramenta/licença/acesso, pedir só a habilitação necessária, não transferir a modelagem ao usuário. Autoria delegada conforme D14 quando aplicável; aceite pelo orquestrador. Mermaid/arquivo sintético não provam execução. |
| P05 — alta | Agente; humano se ferramenta não permitir | **QA final ainda incompleta:** revisar visualmente os PDFs (paginações/legibilidade/figuras), testar teclado/foco e acessibilidade manual pertinente, conferir URLs em sessão anônima. Contagem de páginas/RMs/imagens e axe já foram feitos; não chamá-los de auditoria visual ou certificação WCAG completa. Registrar o que não puder executar. |
| P06 — condicionada | Agente, com autorização quando necessária | **Reprodutibilidade/ciência:** conferir procedência das saídas e execuções anteriores dos notebooks. Não houve reexecução integral de ML/RNA/Estatística nesta retomada. Não executar notebook em massa nem script final se isso retreinar, retunar 2025 ou abrir 2026. Se a exigência literal de reexecução conflitar com esse gate, parar e pedir decisão; não improvisar. |
| P07 — fechamento técnico | Agente | Após incorporar arquivos: corrigir só documentos afetados, regenerar PDFs/cópias pelo pipeline e rodar empacotador `--verificar`. Regressão direcionada se houver alteração; executar API/Cloud/ML completos se forem necessários para um novo aceite, sem afirmar que os resultados históricos foram repetidos. Gitleaks staged/intervalo antes de commit/push. |
| P08 — entrega | Humano | Conferir pacotes/links e submeter no Portal até o prazo; guardar confirmação. Estatística em PDF+PY+CSV separados, **sem ZIP**; Cyber≤15 páginas. Nenhuma submissão foi feita pelo agente. |

### P03 — imagens Cloud, sem ambiguidade

Seguir o [guia exato de capturas](<guia_capturas_learner_lab.md>):
- **Dentro da AWS:** CloudWatch `/aws/lambda/CP-2`, região us-east-1: **CW-C** crítico (CLASSIFICACAO+ALERTA CIDADAO+GRAVADO NO RDS), **CW-D** WARNING de LEITURA DESCARTADA e **CW-K** WARNING de CHAVE INVALIDA. Agente envia testes e fornece a janela/IDs; não capturar logs antigos como novos.
- **Fora do console AWS:** **SIM**, terminal real do simulador com201; **DB**, SELECT+resultado RDS correlacionados aos eventos. Agente prepara e tenta capturas; humano ajuda só se não for possível. A página de infraestrutura RDS não mostra as linhas do banco.
- Variáveis Lambda e CloudWatch geral já têm imagem. Reaproveitar se válidas/legíveis; não exigir nova exposição de segredos. Captura de console autenticado permanece humana, Data Modeler não.
- Originais com PII: copiar para privado antes de tarjar, sem mover/apagar; nunca capturar segredos. Não renderizar logs históricos como supostos prints ao vivo. Inventário/nomes/consulta SQL e cuidados estão no guia.

### P02 — vídeos e conteúdo humano

- **AIC:** até 7 min, YouTube não listado, rosto visível, sem música, nomes/RMs na abertura ou fechamento. Grupo fornece 1–2 ideias reais da live e uma dificuldade real de gestão.
- **ML, Cyber, Cloud:** até 5 min cada. **RNA:** vídeo funcional obrigatório; conferir o enunciado, sem inventar limite que ele não fixa.
- Identidades já confirmadas/aplicadas: não pedir os nomes novamente; o grupo ainda precisa mostrá-los na gravação.
- Preparação de AIC foi corrigida: a persona existente usa **`-App`**, não o schema padrão de testes. Ver [roteiro, preparação](<../09_AIC/video.md#L6-L10>). Só usar `-ComLLM` com autorização válida; plano/resultado em cache não justifica chamada paga desnecessária. Manter a outbox antiga isolada.

## 4. Não feito/verificado — não transformar automaticamente em nova implementação

- **Wokwi→AWS, bancada física e áudio acústico:** não medidos. Wokwi→API CTP isolada→CSV está aceito; os seis eventos ficaram pendente_nuvem e não devem ser liberados retrospectivamente. Não comprar sensores nem repetir hardware sem necessidade/decisão.
- **Cloud agora:** usuário informou nova ativação do Lab em17/11, após o encerramento. Nenhuma nova chamada de health foi feita nesta atualização documental; validar na retomada, sem assumir disponibilidade contínua nem pedir reinício por padrão.
- **Comprehend AccessDenied / HF402:** não houve resultado válido de sentimento. Não comprar créditos ou alterar permissões para maquiar essa limitação.
- **API397/Cloud115/ML274:** resultados de etapas anteriores; não foram rerodados nesta retomada. Tools43, web61/3E2E+persona separada e Wokwi têm evidências próprias no estado/aceites.
- **Limitações declaradas:** texto de operador/transferência internacional em consentimentos, backup/restauração não verificados, falha isolada de sensor sem alerta local, buffer offline do ESP e validação CA/pinning não concluídos. Confrontar impacto com enunciados; se precisar de implementação nova, apresentar escopo/decisão ao usuário, **não reabrir fatias por iniciativa própria**.
- **Holdout2026 fechado e nenhum modelo promovido:** é gate protegido, não uma tarefa automática da próxima sessão. Sem retuning em2025.

## 5. Ambiente efetivamente deixado

Às08h51: main limpa em `f96b13e`, remoto gs-semestre2 sincronizado; **16,3GB livres**. Sem listeners8000/8001/5173/4040/20241 da demo. **Às09h05, agy30832 foi confirmado ativo**, iniciado16/11 09h23, pai31520: é da outra frente, não encerrar. Reidentificar processos ao retomar, nunca agir só pelo PID antigo. Worktrees **S5-auth b94b0de** e **S5-red112042d** continuam preservados e não pertencem a este encerramento.

Docker: Oracle, Mongo e PostgreSQL de teste saudáveis, compartilhados, mantidos; nenhum volume apagado. Brutos Caged `.7z`: zero. Não limpar tmp global; orquestração/diagnósticos e ferramentas portáteis retidos para auditoria/reprodução. Credenciais só por carregamento em memória dos arquivos autorizados; nunca colar no chat, ler em ferramenta de inspeção ou copiar para agente/worktree. A autorização de flash da placa não foi usada e não é motivo para reflashear no próximo atendimento.

## 6. Prompt de gatilho para a próxima sessão

```text
Retome CitizenTech na raiz info-gs-diciplinas, a partir do HEAD publicado (base funcional f96b13e, seguida pelo encerramento documental).
Leia CLAUDE.md, docs/estado.md §0 e docs/handoff_citizentech_20261116_fim.md. Siga a fila P01–P08; não repita S15 nem o aceite Wokwi.
Execute Data Modeler pelo agente, conforme determinação17/11 (D25/CLAUDE§12); não o delegue ao usuário. O usuário já reativou o Learner Lab: confirme health na retomada, execute a rodada autorizada e oriente os prints exatos de docs/guia_capturas_learner_lab.md. Priorize também QA final e incorporação de vídeos/links reais; peça só os insumos/habilitações realmente ausentes.
Não reabra fatias integradas, retune 2025, promova modelos, abra holdout2026, toque S5 da outra frente ou apague dados. Não libere a outbox antiga. Não apresente Wokwi→CSV como Wokwi→AWS.
Siga D14 para implementação e preserve segredos em memória. Reconfirme autorizações aplicáveis antes de gasto pago ou alteração AWS. Commit/push somente com autorização válida, gitleaks staged/intervalo e para gs-semestre2, nunca origin.
Após mudanças, atualize documentos/PDFs, rode empacotador --verificar e a regressão pertinente, registre o que não conseguiu verificar e deixe novo estado/handoff.
```

## 7. Skills sugeridas

`handoff` para novo checkpoint; `wordcraft` para documentos, respeitando o pipeline Edge/D19; `managing-python-dependencies` antes de Python; `diagnose`/`tdd` apenas se surgir falha real; `impeccable` para QA de UI/a11y; `agent-reach` para documentação externa; `ml-best-practices`/`notebook-guidance` antes de qualquer trabalho científico; `accidental-data-loss-prevention` antes de exclusões. Implementação via agy conforme D14; aceite, segredos e integração são do orquestrador.
