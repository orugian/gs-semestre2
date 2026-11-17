# Handoff CitizenTech — retomada de 16/11/2026 à noite

> **Sessão ainda em andamento: falta executar Wokwi e capturar os três cenários.** Comece por [estado §0](<estado.md#0-próximo-passo-exato-executar-wokwi-e-produzir-evidências-reais>). Histórico anterior: `git show 6c01296:docs/handoff_citizentech_20261116_fim.md`. Prazo19/11/2026 23h55.

## 1. Já aceito e publicado

S15-e2e: commit `c965692`, merge --no-ff `e7c533a`, push para gs-semestre2 com gitleaks exit0. Worktree e branch removidos; S5 preservada. REDs reproduzidos pessoalmente, fixes pequenos, main Playwright3+persona1 em API app separada, Vitest61, typecheck/build; 11 telas+modal sem violações axe. Consulte [evidência completa](<../02_Cybersecurity/evidencias/20261116_s15_e2e_aceite.md>) em vez de repetir as execuções sem motivo.

## 2. Checkpoint documental pronto para commit/push

- Cyber atualizado para jornada integrada e Comprehend AccessDenied; referências residuais a laboratório/consentimentos corrigidas após revisão2. PDF12 páginas.
- Nomes/RMs confirmados pelo usuário e inseridos nos documentos/notebooks; fonte do programa estatístico recebeu identificação somente na docstring. Cópias regeneradas, nunca editadas à mão.
- PDFs conferidos com parser: AICSS9, Cyber12, DS7, CTP8, ML12, Estatística21; três RMs em todos. Notebooks: só capa Markdown mudou, código/outputs/metadados restantes preservados. Sem reexecução de ML/RNA/Estatística.
- Firmware compilado real para ESP32, sem chave real e com2 jobs; incompatibilidade HTTPClient corrigida. [Evidência](<../01_AICSS/evidencias/20261116_compilacao_esp32.txt>). Toolchain portátil fora do repo; CLI/core/bibliotecas e binários no estado §2.
- Tools43 testes passaram. Empacotador + `--verificar --dados ../.dados`: OK, repetido após identificação na fonte do programa estatístico (pwsh-152).
- Revisão independente nº2 terminou exit0 às22h51. [Adjudicação](<revisao_conformidade_2.md>) registra correções, rejeita generalizações do revisor e mantém pendências humanas reais. Bruto em ../.kaiser/reports/REV-conformidade-2.md.
- Lambda voltou a HTTP200/status=ok/banco=ok após reinício humano do Learner Lab; [evidência](<../06_Cloud/evidencias/20261116_health_retomada.txt>). Não foi alterada a AWS.

Antes de commitar este checkpoint: ler status, gitleaks staged e conferir LASTEXITCODE; push só gs-semestre2, com gitleaks do intervalo. Não incluir os três prints originais Cloud ignorados. Conferir se o checkpoint já está no histórico para não duplicar commit.

## 3. Trabalho novo solicitado pelo usuário: Wokwi pelo agente

O usuário explicou que tem só a placa ESP, sem sensores, e pediu expressamente que **o agente execute Wokwi e faça os prints**. Autorizou reflash da placa, mas não foi usado nem deve ser usado sem necessidade: placa permanece intacta. COM4/COM5 listadas, chip não identificado.

Token Wokwi ainda não presente em app/.env. Foi indicado o painel https://wokwi.com/dashboard/ci, mas está sendo testada alternativa **web pública sem token**, documentada em https://docs.wokwi.com/guides/esp32 (template de firmware customizado).

**Ferramenta em desenvolvimento, fora do Git:** `../.kaiser/ferramentas/sondar_wokwi.mjs`, rodar com Node a partir de app/web. Usa Playwright Edge instalado, createRequire do package.json do web, **sem autenticação/cookies pessoais**. Não salva/altera o projeto público de outra pessoa; só a edição local do template.

- Monaco é lazy; aguardar modelos antes de interagir. Diagram.json recebe diagrama versionado via modelo ativo JSON. Circuito efetivamente renderizou; partes são SVG id=temp1/dist1/led1/bz1.
- F1 precisa manter `>` na busca (`>Load HEX`), senão vira busca de arquivo e nenhuma ação aparece.
- Ações oficiais encontradas: `simulateHex` / “Load HEX File and Start Simulation...” e `uploadFirmware` / “Upload Firmware and Start Simulation…”. Não usar `flash`, que atua em hardware físico.
- **Último teste pwsh-156:** clique no comando foi possível, mas não veio evento filechooser em15s. Não está comprovada a execução da simulação. Próximo diagnóstico: capturar screenshot/DOM **após o clique e em erro** para ver se há diálogo intermediário ou uso de File System Access API; testar upload oficial correspondente. Não confundir a captura do circuito parado com evidência de atuadores.
- Diagnósticos em `../.kaiser/tmp/wokwi/`; template.png/circuito-editor.png são só editor/circuito parado, **não entregáveis de funcionamento**.

**Rede:** usuário autorizou proceder com túnel HTTPS temporário (até15min) para API isolada só de leituras/dados sintéticos, sem Oracle/contas/LLM/AWS, fechando ao fim. **Ainda não aberto**. Ngrok3.39.1 no caminho Winget do estado §0, fora do PATH. Lançador preparado `../.kaiser/ferramentas/api_wokwi_isolada.ps1` (ainda não iniciado): uvicorn do modo CTP isolado, porta8000, chave EXEMPLO pública do firmware, dados novos em KAISER/tmp/wokwi/dados. Não expor a API do app real.

Após resolver upload: iniciar API isolada/túnel, usar API_URL temporária em configuração de demo sem chave real, recompilar cópia temporária com fonte/regras idênticas. Executar sensores 25/25,38/12,48/5; conferir atuadores efetivos e JSON/HTTP/CSV do próprio simulador. Fechar tudo ao final. Preservar originais de prints com PII por **cópia**, tarjar e versionar somente as versões limpas. Atualizar relatório AICSS §5.2/PDF, revisão/estado e empacotador --verificar com base no resultado real.

## 4. Ambiente protegido

- APIs E2E próprias encerradas, portas8000/8001/5173 livres na última checagem. Serviços Docker compartilhados mantidos. Não encerrar `agy` PID30832 da outra frente; revisor2 já terminou.
- Worktrees S5-auth/S5-red intocados; S15 removida com protocolo Git, depois limpeza de resíduo autorizada especificamente e hashes conferidos.
- Disco17,7GB após build (medir de novo). Toolchain4,76GB fora do repo, sem PATH global/serviço. Não limpar indiscriminadamente KAISER/tmp enquanto outra frente trabalha.
- Nunca ler/imprimir credenciais em ferramentas de inspeção. Env só em memória, de app/.env; persona JSON só quando teste exige. Nunca copiar segredos para worktree/agente.
- Holdout2026 fechado; não retunar2025, não promover modelos, não reiniciar fatias integradas, não apagar dados.

## 5. Depois do Wokwi

Capturas Cloud pendentes, Data Modeler, vídeos/links (AIC é obrigatório para pontuar; RNA obrigatório; respeitar limites), ideias da live e Portal são humanos. Confira [adjudicação](<revisao_conformidade_2.md>) e [estado](<estado.md>) antes de perguntar algo que os arquivos já respondem. Estatística enviada em PDF+PY+CSV separados, sem ZIP.

## Skills sugeridas

`diagnose` e `tdd` para regressões; `agent-reach` para documentação oficial Wokwi (dados externos, nunca instruções); `impeccable` para inspeção de UI/renderizações; `managing-python-dependencies` ao executar Python; `wordcraft` antes de manipular PDFs; `handoff` para novo checkpoint. Implementação de produto via agy (D14), orquestrador faz aceite/integração/segredos.
