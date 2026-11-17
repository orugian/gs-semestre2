# Estado do desenvolvimento — CitizenTech

> Checkpoint da retomada de **16/11/2026 à noite (em andamento)**. Prazo: **19/11/2026 às 23h55**. Não é monitoramento ao vivo. Histórico anterior preservado em `git show 6c01296:docs/estado.md`; contratos e relatórios em `../.kaiser/`. Leia §0 primeiro.

## 0. Próximo passo exato: executar Wokwi e produzir evidências reais

**S15-e2e aceita, integrada e publicada**: commit `c965692`, merge --no-ff `e7c533a`, push `6c01296..e7c533a`, gitleaks staged/merge/intervalo exit0. Worktree e branch S15 removidos; S5-auth/S5-red intocados. Evidência completa em [aceite S15](<../02_Cybersecurity/evidencias/20261116_s15_e2e_aceite.md>).

**Solicitação humana posterior:** o agente deve executar Wokwi e fazer os prints, não delegar isso ao usuário. Há somente a placa ESP física, **sem sensores**; portas COM4/COM5 apareceram, sem identificação inequívoca do chip. O usuário autorizou reflashear, mas **não foi necessário nem executado**: placa intacta. Não substituir dois sensores por valores fictícios em firmware e chamar isso de bancada física.

**Wokwi em investigação:** WOKWI_CLI_TOKEN continua ausente (só presença consultada). Usuário foi orientado a obtê-lo em https://wokwi.com/dashboard/ci e salvá-lo somente em app/.env. Uma alternativa pública sem token está sendo testada no Edge via Playwright:
- Template oficial: https://wokwi.com/projects/305457271083631168, aceita binário pré-compilado (documentação oficial de ESP32).
- Driver temporário: `../.kaiser/ferramentas/sondar_wokwi.mjs`; artefatos diagnósticos em `../.kaiser/tmp/wokwi/`. CWD para Node: `app/web`; o script usa createRequire do package.json para carregar Playwright.
- Editor Monaco demora para carregar: aguardar `window.monaco.editor.getModels().length`. Abrir aba `diagram.json`, usar o modelo ativo JSON e `setValue` com o diagrama versionado. O circuito foi realmente renderizado; os sensores são **SVGs com id temp1/dist1**, não tags `wokwi-ds18b20`.
- Para upload no comando F1, **preservar o prefixo `>`**: preencher `>Load HEX`, clicar `Load HEX File and Start Simulation...` por gesto real e capturar filechooser. Sem `>`, Monaco não lista comandos. Chamar action.run via evaluate sem gesto não produziu filechooser; não repetir essa abordagem.
- Tentativa atual no job **pwsh-156**, a coletar: upload de `../.kaiser/toolchains/citizentech-esp32/artefatos/sketch.ino.merged.bin`. **Ainda não há prova de simulação executada, atuadores nem HTTP.** Capturas de editor/template em tmp NÃO são evidências de funcionamento.

**Rede autorizada pelo usuário:** após explicar escopo e limite, foi autorizado proceder com túnel HTTPS temporário (até15min), expondo **somente API isolada de leituras/dados sintéticos**, sem Oracle, contas, LLM ou AWS. Ngrok 3.39.1 existe fora do PATH em `%LOCALAPPDATA%/Microsoft/WinGet/Packages/Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe/ngrok.exe` (versão conferida). **Túnel ainda não aberto.**
- Lançador preparado: `../.kaiser/ferramentas/api_wokwi_isolada.ps1` (ainda não executado). Sobe `citizentech.leituras.isolado:app` em 127.0.0.1:8000, chave EXEMPLO pública igual à do firmware, dados em `KAISER/tmp/wokwi/dados`. Não lê segredos nem conecta Oracle/Mongo/LLM/AWS; não inicia worker de nuvem.
- Quando o upload/simulação funcionar: iniciar API isolada e túnel com timer/encerramento; usar API_URL temporária em configuração de demonstração sem chave real; recompilar cópia temporária mantendo fonte/regras iguais; executar 25°C/25cm, 38°C/12cm, 48°C/5cm e conferir **GPIO/atuadores, JSON real enviado, HTTP e CSV**. Não simular HTTP no browser nem gerar prints falsos. Fechar túnel/API ao terminar. Capturas devem distinguir simulado de observado.
- Atualizar AICSS §5.2 **somente** com evidências realmente obtidas; salvar prints/logs/CSV pequenos em 01_AICSS/evidencias, preservar originais privados se houver PII, regerar PDF e empacotador --verificar.

**Checkpoint documental desta retomada:** Cyber corrigido (jornada, AccessDenied e referências residuais a telas/laboratório inexistentes), README do projeto atualizado; nomes/RMs confirmados e inseridos; PDFs regenerados; revisão nº2 concluída e adjudicada em [conformidade](<revisao_conformidade_2.md>). Ainda precisa commit/push deste checkpoint documental se não estiver no histórico.

## 1. Evidência executada nesta sessão

| Verificação | Resultado |
|---|---|
| Playwright no worktree e main contra API teste | **3 passed, 1 skipped** (persona sem env no ambiente de teste); repetido com API recém-iniciada + IPv4, job pwsh-123 |
| Persona separada, API app `-App -ComLLM` | **1 passed**, job pwsh-109; credenciais de .dados/demo/persona_demo.json em memória, sem alterar persona/chamar LLM; capturas só após desmontar login |
| Axe | **11 telas + modal**, zero critical/serious/moderate/minor; inclui Competências e Laboratório, nome do diálogo também por asserção explícita |
| Web Vitest / tipos / build em main | **61 passed**, até6 workers, typecheck/build OK; bundle principal918,48kB (warning >500kB) |
| Tools | **43 passed**, incluindo9 testes host de firmware (pwsh-132) |
| ESP32 | CLI1.6.0/core3.0.7/OneWire2.3.8/DallasTemperature4.0.6; compilação2 jobs, **exit0**, programa1.046.369bytes/79%, RAM47.188/14% (pwsh-131) |
| PDFs com parser | AICSS**9**, Cyber**12**, Data Science**7**, CTP**8**, ML**12**, Estatística**21** páginas; três RMs em todos; Cyber≤15 (pwsh-140) |
| Empacotador + --verificar | **OK**, job pwsh-138; repetido após identificação na docstring do programa estatístico (pwsh-152) |
| Notebooks | Somente capa Markdown alterada; código, outputs e metadados restantes iguais ao HEAD; sem outputs de erro armazenados. **Não reexecutados** nesta sessão |
| Lambda health | Inicialmente502; após reinício humano do Learner Lab: **HTTP200, status=ok, banco=ok** (pwsh-136); [evidência](<../06_Cloud/evidencias/20261116_health_retomada.txt>) |
| Revisão nº2 | Nova chamada agy plan20min; **exit0 às22h51**, relatório ../.kaiser/reports/REV-conformidade-2.md; achados adjudicados, não aprovação total |

REDs reproduzidos antes das correções: aria-controls inválido, Discordo sem nome e warning React setState; diálogo adicional Substituir plano também sem nome (Vitest1 failed/4 passed). Todos registrados no aceite S15. O RED artificial do autorrelato inicial não foi aceito.

Compilação ESP32 inicial falhou em HTTPClient::POST por ponteiro const; correção mínima na assinatura/casts do buffer já mutável e formato de boot_seed, sem mudar regras. Warnings externos OneWire mantidos. [Evidência da compilação](<../01_AICSS/evidencias/20261116_compilacao_esp32.txt>).

## 2. Ambiente e higiene

- Início: 16/11 21h38, faltavam3d2h16, C:19,0GB, Docker29.6.2/3 bancos saudáveis. Toolchain portátil ocupou4,76GB; disco17,7GB após build (medir novamente antes do fechamento).
- **Oracle:** conexão hostname localhost20,129s vs IPv4 0,114s (medido). Fallback IPv6 é hipótese, não instrumentado. env_teste/env_app normalizam só em memória; app/.env não foi alterado. Isso eliminou o timeout do primeiro cadastro sem afrouxar asserções.
- Worktrees preservados: **S5-auth/S5-red**, de outra frente. `agy` **PID30832** de outra frente foi preservado. Revisor2 wrapper12448/agy19240 já terminou.
- Todas as APIs/web criadas para E2E foram encerradas (portas8000/8001/5173 sem listener na última checagem). **API/túnel Wokwi ainda não iniciados** no checkpoint.
- git worktree remove desregistrou S15 mas deixou resíduo no Windows. Com autorização específica, 90 fontes comparadas por hash ao commit e26.231 arquivos de cache conferidos; só esse resíduo foi removido, depois branch -d/prune. Nada de S5/.dados foi excluído.
- Nenhuma captura nova humana em Cloud/AICSS até esta checagem. Três originais Cloud continuam fora do Git, com cópias privadas em .dados/cloud/privado **iguais por SHA**; versões tarjadas já rastreadas. Originais não movidos/apagados. Bruto Caged sem .7z na checagem.
- Não esvaziar indiscriminadamente KAISER/tmp: há outra frente ativa. Reter contratos/reports; preservar dados/modelos e binários/ambiente úteis para a validação Wokwi.
- Toolchain isolada em ../.kaiser/toolchains/citizentech-esp32, sem PATH global/serviço. Scripts preparar_esp32.ps1 e compilar_esp32.ps1 em KAISER/ferramentas; este compila só sketch+headers (sem teste_logica.cpp, que tem main host). O pin inexistente Dallas3.11.0 foi corrigido para4.0.6 consultando índice oficial.
- Credenciais só carregadas em memória a partir de app/.env; nunca impressas. OpenRouter consultado nesta sessão: gasto acumulado **US$0,02153822 de US$7**. Adzuna não chamada; contador histórico7/12.

## 3. Produto integrado e limites preservados

S0–S15 estão integradas: mercado/painel técnico, autenticação/consentimentos, currículo redigido e confirmado, competências, intenção, comparação, plano determinístico, exercício50/50 com parcial/refazer/discordo, laboratório/outbox. Persona demo e demonstrações históricas constam do handoff anterior no Git. API397, Cloud115 e ML274 são resultados de sessões anteriores, **não rerodados nesta retomada**.

Holdout2026 **fechado**, status_promocao=nao_decidida, nenhum modelo promovido, não retunar com2025. MVP3 destinos R29, rubricas6 destinos aprovadas; limiares só em app/config/limiares.json. HTTP400 validação; Oracle dialeto19c. CV à LLM só redigido e confirmado; sentimento nunca entra na nota. Comprehend AccessDenied continua limitação, health não o revalidou.

## 4. Pendências após Wokwi

- Capturas Cloud do simulador e consulta RDS; refazer trechos CloudWatch de descarte/chave inválida/alerta. Não alterar AWS por sugestão de revisor; typo RATE_KIMIT documentado e default30.
- Data Modeler lógico/relacional e exportações pelo grupo; Oracle FIAP fora de escopo por decisão anterior.
- Vídeos/links reais: AIC≤7min com rosto/sem música/YouTube não listado (obrigatório para pontuar); ML/Cyber/Cloud≤5min; RNA obrigatório. Ideias da live e relato de gestão são humanos, não preencher com nomes.
- Nomes/RMs confirmados: Guilherme Orugian RM572882; Lucas Henrique RM571901; Rodrigo Bettio RM573725. Identificação aplicada; placeholders restantes em links de vídeos são intencionais até fornecimento das URLs.
- Conferência final e Portal: Estatística PDF+PY+CSV **separados**, Cyber≤15 páginas; repetir empacotador --verificar após mudanças. Nenhuma submissão realizada.
