# Revisão adversarial — CLAUDE.md do orquestrador

**Data:** 12/11/2026 · **Objeto:** [CLAUDE.md](../CLAUDE.md) (versão com §14 Ambiente e §15 Organização)

**Revisores independentes** (`agy --mode plan`, somente leitura, sem participar da autoria):
- A — engenharia de prompt e comportamento do agente: `.kaiser/reports/REV-CLAUDE-A-prompt.md`
- B — executabilidade operacional (Windows / PS 5.1 / worktrees / disco): `.kaiser/reports/REV-CLAUDE-B-operacional.md`

**Verificação empírica do orquestrador:** cada achado com afirmação factual foi testado na máquina antes da adjudicação.

| Fato testado | Resultado |
|---|---|
| `2>&1` em executável nativo no PS 5.1 | O stderr vira `ErrorRecord`, mas o `$LASTEXITCODE` é preservado |
| `git worktree remove` com `.venv` ignorado | Remove normalmente |
| `agy --print-timeout 2m` | Funciona |
| `agy --mode plan` sem `--dangerously-skip-permissions` | Lê arquivos (comprovado pelos próprios revisores, que leram os documentos) |
| Imagem `gvenzl/oracle-free:23-slim` | 0,79 GB comprimida |
| gitleaks | 8.30.1 disponível via winget |
| Nova regex da varredura de transição | Detectou 4 de 4 segredos de teste, com 0 falsos positivos nos documentos do repositório |

## Adjudicação

| # | Origem | Sev. | Achado | Decisão | Correção aplicada |
|---|---|---|---|---|---|
| 1 | A1, B2 | Bloq. | Deadlock: "gitleaks antes de todo commit", mas o gitleaks não existe e o 1º passo é um commit | **Aceito** | §3.4 + **varredura de transição** testada (§14.2) até a S0; comando de instalação via winget |
| 2 | A2, B3 | Bloq. | O snippet era síncrono e usava `--print-timeout 0s`, sem timeout real | **Aceito** | §7.2: execução numa chamada de shell em background e `--print-timeout 45m` (implementação) / `20m` (revisão); `0s` proibido |
| 3 | A3 | Bloq. | O revisor `--mode plan` sem a flag não conseguiria ler o diff | **Aceito em parte** | A premissa "aborta" é falsa (os revisores leram arquivos), mas é verdade que ele não executa `git diff`. §7.2/§7.6: o orquestrador grava o patch em `.kaiser\tmp\` e o revisor o lê. A flag de bypass **não** foi adotada em revisões |
| 4 | A5, B3 | Alto | A limpeza de variáveis de ambiente apagaria as credenciais do orquestrador | **Aceito em parte** | Fato verificado: cada chamada de shell do harness é um processo novo, então o risco real era só ambiguidade. O snippet agora declara isso explicitamente. `Start-Job` não foi adotado, porque o job do harness já isola |
| 5 | A6 | Alto | O snapshot "antes" (repositório principal) era comparado com o "depois" (worktree) | **Aceito** | `-base` = `rev-parse HEAD` do worktree; `-depois` = status com `--untracked-files=all`; o aceite usa `diff <base>` |
| 6 | A4 | Alto | §4 ("sem âncora → pergunte") contradizia §8, com risco de paralisia | **Aceito** | §4: só pergunta quando a escolha afeta negócio, contrato, arquitetura, dados/ML ou conformidade; escolhas locais são autônomas |
| 7 | A7, B5 | Alto | A allowlist impedia apagar os `.7z` (estouro de disco), criar pastas e instalar o Playwright | **Aceito** | §7.3: exclusão só em TMP e em `caged\bruto` (S6), `New-Item`, `playwright install chromium`. A extração do `.7z` é feita por Python (`uv run`), já coberto |
| 8 | B4 | Alto | Worktree sem `.venv`/`node_modules`/`.env`; conflito de compose entre worktrees | **Aceito com outra correção** | §7.2: bootstrap pelo próprio subagente (`uv sync`/`pnpm install`). **Não** copiar `.env` (os testes usam fakes). §7.3/§14.1/§14.2: o subagente não usa `docker`; os serviços de teste sobem uma vez pelo orquestrador, com volumes nomeados |
| 9 | B1 | Bloq. → **Médio** | "Oracle em Docker inviável em 10 GB" (o revisor estimou 8,2 GB) | **Rejeitado como bloqueador** | Medido: `23-slim` tem 0,79 GB comprimida (estimativa de 2–3 GB extraída). A troca por mock/SQLite foi rejeitada, porque violaria "Oracle real nos testes" e o D08. §14.2 ganhou o orçamento de disco detalhado, a imagem slim, o PyTorch CPU e o procedimento de limpeza com aprovação |
| 10 | A8 | Médio | O RED falharia por ImportError em módulo novo | **Aceito** | §7.4: esqueleto de interface primeiro; §7.5: o RED vale só por asserção |
| 11 | A9 | Médio | "> 45 min" no contrato (o LLM não mede tempo); faltavam convenções de nomes | **Aceito** | A cláusula foi removida do contrato (o timeout é do `agy`); linha de convenções adicionada ao template |
| 12 | A10 | Médio | Citações confusas: D6 (dia) vs D06 (decisão); D25 citada para todas as entregas humanas | **Aceito** | §2: convenção de IDs (`D01–D25` = decisões, `D1–D7` = dias); §12 cita D14a, D25 e plano §10; §15.1 diz "no dia D6" |
| 13 | B7 | Médio | §15.1 ("cópias geradas, nunca editar") contradizia §7.1 ("agy rascunha relatórios") | **Aceito** | §15.1: separação entre (a) autorais editáveis em `0X_*` e (b) cópias geradas; notebooks importam `app\ml` |
| 14 | B6 | Médio | `git worktree remove` falharia com `.venv`/locks; sugestão de `--force` + `Remove-Item` | **Aceito em parte** | Verificado: ignorados **não** bloqueiam. §15.4: encerrar processos antes (locks do Windows), `--force` só em descarte decidido, `worktree prune`. O `Remove-Item -Force` sugerido foi **rejeitado** por conflitar com o protocolo de exclusão |
| 15 | A11 | Baixo | Custo de contexto: hardware, lista de competências, árvore e tabela duplicadas | **Aceito em parte** | Hardware reduzido aos fatos que mudam decisões (threads, RAM, disco). As competências e a árvore mais a tabela foram **mantidas**: a persona foi pedida pelo usuário, e a árvore (onde) e a tabela (ciclo de vida) respondem a perguntas diferentes |
| 16 | — (orquestrador) | Médio | A primeira regex da varredura dava 35 falsos positivos nos próprios documentos | **Corrigido** | A regex agora exige atribuição com valor ou formatos de chave conhecidos; testada (4/4 detectados, 0 falsos positivos) |
| 17 | — (orquestrador) | Baixo | A cerca de código da varredura ficou colada a texto (render quebrado) | **Corrigido** | Formatação validada: 10 cercas no início de linha, nenhuma no meio de linha |

## Não verificado

- O comportamento do `agy` com `--dangerously-skip-permissions` ao executar `uv sync` dentro de um worktree. Será verificado no primeiro disparo (S1), com o snapshot como rede de segurança.
- O tamanho real da imagem do Oracle extraída no WSL2 e o crescimento do VHDX. Será medido no smoke da S0 (`docker system df`).
- Se o harness de desenvolvimento das próximas sessões continuará usando o PowerShell 5.1. A §14.3 deve ser atualizada se mudar.
