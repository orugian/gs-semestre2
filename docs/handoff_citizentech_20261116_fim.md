# Handoff CitizenTech — encerramento em 17/11/2026

> Arquivo canônico mantido com o nome original para não quebrar as referências. **Checagem de encerramento: 17/11, 08h51 (UTC−3)**. Prazo: **19/11/2026, 23h55**; faltavam 2 dias e 15 horas. Implementação aceita não significa entrega acadêmica concluída.

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
| Capturas AWS que faltam e limites reais | [Cloud §8–§9](<../06_Cloud/README.md#L148-L177>) |
| Data Modeler | [Data Science §2](<../03_DataScience/relatorio.md#L24-L31>), [SQL consolidado](<../03_DataScience/oracle.sql>) |
| Roteiros e locais dos links de vídeo | [AIC](<../09_AIC/video.md>), [ML](<../05_ML/video.md>), [Cyber](<../02_Cybersecurity/video.md>), [Cloud](<../06_Cloud/video.md>), [RNA](<../07_RedesNeurais/video.md>) |
| Gerar/conferir entregas | [Empacotador](<../app/tools/empacotar_entregas.py>), [conversor PDF](<../app/tools/md_para_pdf.py>), [manifesto do pacote](<entregas_manifesto.json>) |

Não tratar “pendente” em **evidência histórica datada** como estado atual: alguns snapshots antecedem integrações já concluídas. Não reescrever esses registros para apagar a história.

## 3. Ordem de trabalho da próxima sessão

| ID / prioridade | Responsável | Ação e critério para fechar |
|---|---|---|
| P01 — início | Agente | Executar ritual do CLAUDE: data/prazo/disco, Git/remotos/worktrees/processos e serviços necessários. Ler estado/handoff antes de agir. Ver quais arquivos humanos novos realmente chegaram. Nenhuma implementação nova neste encerramento. |
| P02 — crítica, em paralelo | Humano + agente | **Vídeos e live:** preparar demonstração e auxiliar tecnicamente; grupo grava/publica e fornece URLs. AIC é obrigatório para pontuar, RNA também exige vídeo. Validar duração/acesso e inserir links nos cinco roteiros; nunca fabricar vídeo, fala da live ou relato de gestão. |
| P03 — crítica, em paralelo | Humano + agente | **Cloud:** humano inicia Learner Lab e captura console autenticado; agente revalida health em execução nova e orienta os cenários. Completar imagens listadas abaixo. Texto antigo não substitui print e Wokwi local não comprova AWS. Não mudar IAM/SG/Lambda/RDS nem gastar quota sem autorização aplicável. |
| P04 — alta, em paralelo | Humano + agente | **Data Modeler:** grupo importa DDL 001–007/dialeto19c, gera modelos lógico e relacional, exporta imagens e salva o projeto nativo. Agente confere entidades/chaves/relações e incorpora evidências no relatório/PDF. Mermaid não equivale à execução no Modeler. |
| P05 — alta | Agente; humano se ferramenta não permitir | **QA final ainda incompleta:** revisar visualmente os PDFs (paginações/legibilidade/figuras), testar teclado/foco e acessibilidade manual pertinente, conferir URLs em sessão anônima. Contagem de páginas/RMs/imagens e axe já foram feitos; não chamá-los de auditoria visual ou certificação WCAG completa. Registrar o que não puder executar. |
| P06 — condicionada | Agente, com autorização quando necessária | **Reprodutibilidade/ciência:** conferir procedência das saídas e execuções anteriores dos notebooks. Não houve reexecução integral de ML/RNA/Estatística nesta retomada. Não executar notebook em massa nem script final se isso retreinar, retunar 2025 ou abrir 2026. Se a exigência literal de reexecução conflitar com esse gate, parar e pedir decisão; não improvisar. |
| P07 — fechamento técnico | Agente | Após incorporar arquivos: corrigir só documentos afetados, regenerar PDFs/cópias pelo pipeline e rodar empacotador `--verificar`. Regressão direcionada se houver alteração; executar API/Cloud/ML completos se forem necessários para um novo aceite, sem afirmar que os resultados históricos foram repetidos. Gitleaks staged/intervalo antes de commit/push. |
| P08 — entrega | Humano | Conferir pacotes/links e submeter no Portal até o prazo; guardar confirmação. Estatística em PDF+PY+CSV separados, **sem ZIP**; Cyber≤15 páginas. Nenhuma submissão foi feita pelo agente. |

### P03 — imagens Cloud, sem ambiguidade

- Variáveis Lambda: já há imagem tarjada; conferir se continua válida, sem expor valores secretos.
- **Falta:** simulador enviando leituras e resposta da Function URL em execução real.
- **Falta/refazer:** CloudWatch com chegada/classificação/gravação e os casos de descarte/chave inválida/alerta crítico.
- **Falta:** consulta RDS mostrando ocorrências realmente gravadas.
- Captura do console AWS é humana (D14a). O agente pode executar/validar simulador e consultas autorizadas e tentar capturas locais reais; se não conseguir, orientar a captura humana. **Não gerar imagem de saída histórica e chamá-la de print ao vivo.**
- Salvar arquivos novos em `06_Cloud/evidencias/`, datados, sem sobrescrever os antigos. Antes de versionar, o agente copia originais com dados pessoais para `.dados/cloud/privado`, preserva SHA, produz derivadas tarjadas e confere os bytes staged. Nunca mover/apagar originais ou registrar segredos.

### P02 — vídeos e conteúdo humano

- **AIC:** até 7 min, YouTube não listado, rosto visível, sem música, nomes/RMs na abertura ou fechamento. Grupo fornece 1–2 ideias reais da live e uma dificuldade real de gestão.
- **ML, Cyber, Cloud:** até 5 min cada. **RNA:** vídeo funcional obrigatório; conferir o enunciado, sem inventar limite que ele não fixa.
- Identidades já confirmadas/aplicadas: não pedir os nomes novamente; o grupo ainda precisa mostrá-los na gravação.
- Preparação de AIC foi corrigida: a persona existente usa **`-App`**, não o schema padrão de testes. Ver [roteiro, preparação](<../09_AIC/video.md#L6-L10>). Só usar `-ComLLM` com autorização válida; plano/resultado em cache não justifica chamada paga desnecessária. Manter a outbox antiga isolada.

## 4. Não feito/verificado — não transformar automaticamente em nova implementação

- **Wokwi→AWS, bancada física e áudio acústico:** não medidos. Wokwi→API CTP isolada→CSV está aceito; os seis eventos ficaram pendente_nuvem e não devem ser liberados retrospectivamente. Não comprar sensores nem repetir hardware sem necessidade/decisão.
- **Cloud agora:** disponibilidade atual não foi chamada de novo neste encerramento. Último health real ok foi após reinício humano em16/11; o Lab pode ter expirado.
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
Priorize QA final e incorporação de imagens Cloud, Data Modeler e vídeos/links reais. Se faltarem materiais humanos, avance nas verificações executáveis e peça apenas os insumos ausentes. Confirme Lab/health antes de nova demonstração AWS.
Não reabra fatias integradas, retune 2025, promova modelos, abra holdout2026, toque S5 da outra frente ou apague dados. Não libere a outbox antiga. Não apresente Wokwi→CSV como Wokwi→AWS.
Siga D14 para implementação e preserve segredos em memória. Reconfirme autorizações aplicáveis antes de gasto pago ou alteração AWS. Commit/push somente com autorização válida, gitleaks staged/intervalo e para gs-semestre2, nunca origin.
Após mudanças, atualize documentos/PDFs, rode empacotador --verificar e a regressão pertinente, registre o que não conseguiu verificar e deixe novo estado/handoff.
```

## 7. Skills sugeridas

`handoff` para novo checkpoint; `wordcraft` para documentos, respeitando o pipeline Edge/D19; `managing-python-dependencies` antes de Python; `diagnose`/`tdd` apenas se surgir falha real; `impeccable` para QA de UI/a11y; `agent-reach` para documentação externa; `ml-best-practices`/`notebook-guidance` antes de qualquer trabalho científico; `accidental-data-loss-prevention` antes de exclusões. Implementação via agy conforme D14; aceite, segredos e integração são do orquestrador.
