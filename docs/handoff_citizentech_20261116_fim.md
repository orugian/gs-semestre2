# Handoff CitizenTech — fim da sessão de 16/11/2026 (~21h30, UTC−3)

> Ler junto com `docs/estado.md` §0. Prazo de entrega: **19/11/2026 às 23h55** (~3,1 dias a partir deste handoff). Caminhos relativos à raiz do repositório; `../` = `C:\Users\orugi\Documents\Projetos\FIAP\GS`.

## 1. Ponto de parada

- **`main` = commit deste handoff**, enviado a `gs-semestre2` (gitleaks limpo no intervalo). `origin` não recebe push.
- **Produto:** todas as fatias S0–S15d estão integradas. A jornada completa existe na web (conta, consentimentos, currículo redigido, competências, intenção, comparação de até 3 destinos, plano, exercício diagnóstico, laboratório) e foi exercitada no Edge com a persona demo e a LLM real.
- **Testes em `main` rodados pelo orquestrador nesta sessão:** `app/api` 397 passed · `app/web` 61 passed · `app/tools` 43 passed · `test_firmware.py` 9 passed. `app/cloud` 115 e `app/ml` 274 são de sessões anteriores (nada mudou nesses pacotes).
- **Em aberto:** S15-e2e (Playwright + axe) terminou às 19h31 com saída 0, **sem commit**, e encontrou defeitos de acessibilidade (§3.1). Nenhum processo ficou de pé: a API de teste da porta 8000 foi encerrada e o `agy` da S15-e2e saiu.

## 2. O que foi feito nesta sessão (com evidência)

| Item | Evidência |
|---|---|
| S15b, S11b, S15c, S13, S12, S14, S15d integrados | `git log`; contratos e relatórios em `../.kaiser/{contratos,reports}/` |
| Persona demo (`marina.demo@citizentech.exemplo`, `persona_demo='S'`) | `app/tools/criar_persona_demo.py`; credenciais só em `../.dados/demo/persona_demo.json` |
| Cloud README (inclui arquivos da raiz e `codigo/`) | `06_Cloud/README.md` |
| Cyber relatório 12 págs. | `02_Cybersecurity/relatorio.{md,pdf}`; demo `evidencias/20261116_demo_protecoes.txt` |
| CTP documento 8 págs. (execução via `pip` testada em venv limpo) | `04_CTP_Python/documento.{md,pdf}` |
| Data Science relatório 7 págs.; DDL 001–007 aplicado; consultas executadas | `03_DataScience/relatorio.{md,pdf}`, `evidencias/20261116_consultas_{oracle,mongo}.txt` |
| AICSS relatório 8 págs. com evidência da lógica do firmware no computador | `01_AICSS/relatorio.{md,pdf}`, `evidencias/20261116_logica_firmware_host.txt` (10 casos, 16 leituras, 0 falhas), `evidencias/20261116_compat_servidor_modelo.txt` |
| UML | `docs/uml/uml_citizentech.md`, `docs/uml/img/` |
| Roteiros de vídeo: Cyber, Cloud, AIC, ML, RNA | `02_Cybersecurity/video.md`, `06_Cloud/video.md`, `09_AIC/video.md`, `05_ML/video.md`, `07_RedesNeurais/video.md` |
| Empacotador com cópias de código nas pastas de entrega | `app/tools/empacotar_entregas.py`; `--verificar` OK às 19h25 |

## 3. Pendências do agente (fazer já, nesta ordem)

### 3.1 Aceitar S15-e2e (worktree `../GS-wt/S15-e2e`, branch `fatia/S15-e2e`)
- Arquivos não commitados: `app/web/e2e/{jornada.spec.ts,acessibilidade.spec.ts,apoio.ts}`, `app/web/playwright.config.ts`, `app/web/package.json`, `app/web/pnpm-lock.yaml`. Relatório do agente: `../.kaiser/reports/S15-e2e.md`.
- Subir a API de teste (`../.kaiser/ferramentas/subir_api_teste.ps1`, porta 8000) e rodar **você mesmo** `pnpm exec playwright test` no worktree.
- Rodar o teste da persona (ficou `skip`): `E2E_PERSONA_EMAIL`/`E2E_PERSONA_SENHA` lidos de `../.dados/demo/persona_demo.json` sem imprimir, contra a API do app (`subir_api_teste.ps1 -App -ComLLM`).
- **Defeitos encontrados** (o agente não alterou `src/`):
  1. axe **critical** `aria-valid-attr-value` nas 7 telas da aba "Minha transição": `<Tab value="jornada">` tem `aria-controls="painel-jornada"`, mas não existe elemento com esse `id` (`app/web/src/App.tsx` linha 69; `AreaJornada.tsx`).
  2. Diálogo "Discordo" da tela de exercício sem nome acessível (`TelaExercicio.tsx`).
  3. Aviso React "Cannot update a component (`AreaJornada`) while rendering `TelaPlano`" (`TelaPlano.tsx`).
  4. O axe não cobriu as telas **Competências** e **Laboratório**: incluir.
- Correção: fatia pequena `S15e-a11y` (agy, RED = o próprio teste axe falhando), ou correção direta se for de 1–2 linhas, sempre com o RED reproduzido. Depois: commit, `merge --no-ff`, regressão web, `git worktree remove`, `git branch -d`, push.

### 3.2 Corrigir inconsistências nos documentos
- `02_Cybersecurity/relatorio.md` linha 17: diz que intenção, comparação e telas "estão em desenvolvimento"; já estão integradas. Linha 21: descreve o Comprehend como funcionando; na AWS real ele dá **AccessDenied** e a leitura fica `analise_status=indisponivel` (ver `06_Cloud/README.md` §4). Corrigir e regerar o PDF (`--max-paginas 15`).
- `00_projeto/README.md` linhas 26–28 ("Ainda faltam… o app ainda não funciona ponta a ponta"): desatualizado.
- `docs/estado.md` §1 e §4 descrevem o estado das 15h–17h; §0 prevalece. Ao atualizar, enxugar.

### 3.3 Firmware e AICSS
- Compilar o `sketch.ino` para ESP32 com `arduino-cli` (pedir aprovação para instalar o `arduino-cli` e o core `esp32`). Nunca foi compilado para a placa.
- Rodar no Wokwi. Pela CLI, precisa de `WOKWI_CLI_TOKEN` fornecido pelo usuário em `app/.env`; senão, o usuário roda pela extensão do VS Code (§4). Depois, preencher `01_AICSS/relatorio.md` §5.2 com as capturas e regerar o PDF.
- Limitação declarada no relatório: falha de **um** sensor não gera alerta local. Mudar isso é decisão de comportamento: perguntar antes.

### 3.4 Fechamento
- **Revisão de conformidade nº 2** (`../.kaiser/ferramentas/revisar_conformidade.ps1`). A nº 1 está em `../.kaiser/reports/REV-conformidade-1.md`; desde então AICSS, DS, ML e RNA foram resolvidos no texto (§2 deste handoff).
- Quando o usuário confirmar nomes e RMs: preencher todos os `[HUMANO — preencher]` (lista em REV-conformidade-1 §4.1) e regerar os PDFs (`app/tools/md_para_pdf.py`; Cyber com `--max-paginas 15`; slides de ML e relatório de Estatística pelo empacotador).
- Empacotador final: `python app/tools/empacotar_entregas.py --dados ..\.dados`, depois `--verificar --dados ..\.dados`.
- Atualizar `docs/estado.md`, gitleaks, commit, push e relatório de fim de turno.

### 3.5 Não verificado ou adiado (registrar se não der tempo)
- Revisão independente da S10 (não obrigatória). Bundle web de 737 kB.
- `app/cloud` e `app/ml` não foram rerodados nesta sessão.
- Os arquivos Flask do professor na raiz de `04_CTP_Python/` (`app.py`, `armazenamento.py`, `processamento.py`, `testes.py`) continuam lá; o documento de CTP diz que não fazem parte da solução. Remover só se o usuário decidir.

## 4. Pendências humanas

- **Nomes e RMs:** confirmar a lista do grupo; o agente preenche e regera os PDFs.
- **Wokwi:** rodar os 3 cenários (25/25, 38/12, 48/5) pela extensão do VS Code com a API local, ou fornecer `WOKWI_CLI_TOKEN`. Salvar `01_AICSS/evidencias/wokwi_{normal,atencao,critico}.png` e o trecho do Serial Monitor.
- **Cloud:** refazer os prints 1 e 2 do CloudWatch (`LEITURA DESCARTADA` + `CHAVE INVALIDA`; `ALERTA CIDADAO` + `GRAVADO NO RDS`) e capturar o terminal do simulador e a consulta no RDS, em `06_Cloud/evidencias/`. Learner Lab ativo e SG 5432 aberto até o fim da correção.
- **Data Modeler:** modelo lógico e relacional a partir do DDL do Oracle (`app/db/ddl/001–007`), imagens em `03_DataScience/`.
- **Vídeos:** AIC (≤ 7 min, rosto, obrigatório para pontuar), RNA, ML (≤ 5), Cyber (≤ 5), Cloud (≤ 5); links nos `video.md`. Ideias da live (04/11) para o vídeo de AIC.
- **Prints originais com e-mail:** `06_Cloud/evidencias/{function-url,banco-rds,security-group}.png` (fora do Git; cópias em `../.dados/cloud/privado/`) podem ser apagados.
- **Portal (19/11 até 23h55):** Estatística com 3 arquivos soltos (`.pdf`, `.py`, `.csv`), sem zip.

## 5. Arquivos e ferramentas relevantes

- Estado vivo: `docs/estado.md` · regras: `CLAUDE.md` (§5 ritual, §7 subagentes, §14.3 ambiente) · plano: `docs/plano_desenvolvimento.md`.
- Ferramentas do orquestrador em `../.kaiser/ferramentas/`: `lancar_agy.ps1 -S <fatia> [-T 45m] [-ComBancos]` (log `../.kaiser/tmp/lancar_<fatia>.log`, relatório `../.kaiser/reports/<fatia>.md`), `subir_api_teste.ps1 [-App] [-ComLLM] [-Porta]`, `env_teste.ps1`, `env_app.ps1`, `gasto_openrouter.py`, `revisar_conformidade.ps1`.
- Disparo em segundo plano: `Start-Process powershell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File <ps1> ...' -WindowStyle Hidden -PassThru` (o `run_in_background` do harness não funciona).
- Smoke no Edge: `../.kaiser/tmp/smoke/` (playwright-core, `channel:'msedge'`): `smoke_s15b.mjs`, `smoke_jornada.mjs`, `smoke_persona.mjs`, `smoke_plano.mjs`.
- Ferramentas em `app/tools/`: `md_para_pdf.py`, `empacotar_entregas.py`, `demo_protecoes.py`, `demo_leituras_ctp.py`, `demo_firmware_aicss.py`, `criar_persona_demo.py`, `aplicar_ddl.py`, `carregar_catalogo_oracle.py`, `executar_consultas_oracle.py`, `renderizar_mermaid.py`.
- gitleaks: `& "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Gitleaks.Gitleaks_Microsoft.Winget.Source_8wekyb3d8bbwe\gitleaks.exe" git --staged --redact --no-banner`; antes do push, `--log-opts="gs-semestre2/main..main"`. **Conferir `$LASTEXITCODE` antes de commitar.**
- Armadilhas do PowerShell 5.1: `[Console]::OutputEncoding=[Text.Encoding]::UTF8` antes de capturar Python; `Tee-Object` não tem `-Encoding` (usar `[IO.File]::WriteAllText` com UTF-8 sem BOM); `>` grava UTF-16; `-like` trata a crase como escape; buscas recursivas em `../` estouram o tempo por causa de `node_modules`.

## 6. Guardrails (inalterados)

Holdout 2026 fechado; não retunar com 2025; nenhum modelo promovido; não reiniciar fatias integradas; não apagar dados; nunca imprimir valores do `app/.env`; push só para `gs-semestre2` com gitleaks antes; OpenRouter ≤ US$ 7 (gasto US$ 0,01848); Adzuna 7/12; AWS só com o Learner Lab ativo. Worktrees `../GS-wt/S5-auth` e `../GS-wt/S5-red` são de outra frente: não limpar.
