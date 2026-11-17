# Registro de decisões — reorganização do código (untangle), 17/11/2026

Pedido do usuário: repositório organizado, fácil de entender e de replicar. Escopo aprovado: **web, tools, cloud (só testes/organização, nunca o código implantado da Lambda) e api**. `app/ml` congelado (holdout, model cards e notebooks dependem dele). Comportamento público não muda; corpos de erro `{erro, detalhes}` e status HTTP ficam idênticos.

Diagnóstico completo (IDs H/N/S/X): relatório somente leitura de 17/11. Cada correção abaixo vem acima dos problemas que resolve.

## Feito

- **Entregas declaradas num lugar só** — o empacotador passa a cobrir os 6 relatórios PDF (com título e limite de 15 p em Cyber) e gera os `requirements.txt` de ML/RNA a partir do `uv.lock`.
  - PDFs de AICSS, Cyber, Data Science e CTP fora do manifesto: `--verificar` não os via.
  - `05_ML/requirements.txt` e `07_RedesNeurais/requirements.txt` do esqueleto (tensorflow, sem `citizentech_ml`) não instalavam o que os notebooks importam.
- **Replicação documentada e executável** — `README.md` na raiz, `app/tools/ambiente_teste.ps1`, `app/tools/testar_tudo.ps1`, `.env.example` completo e portável.
  - Variáveis `PG_TESTE_*`, `ORACLE_TESTE_*` e o schema `CT_TESTE_*` só existiam em scripts fora do repositório.
  - `.env.example` com caminhos absolutos da máquina e variáveis mortas (`APP_ENV`, `CITIZENTECH_TMP`, `ADZUNA_MAX_CHAMADAS`, `ORACLE_FIAP_*`); 14 variáveis lidas pelo código sem documentação.
- **Documentos fora de uso saem da superfície** — `docs/historico/` e `docs/panorama/`; `.gitignore` cobre originais com PII e estado da ferramenta de design.

## Em execução / próximo

- **Web: cliente HTTP único + domínio compartilhado + componentes menores** (C1, C2, C10 parte web, C11 web, C12) — depois do redesign visual S16, para não haver dois agentes nos mesmos arquivos.
- **API: um módulo de catálogo, utilidades de banco, serviço de leituras, erros de domínio, laço de retentativas da LLM** (C5, C7, C8, C9, C15, C11 api) — fatia S17.
- **Tools: `_comum.py`** (C13) e **testes de paridade com a Lambda** (C14) — fatia S17.

## Decidido não fazer (com motivo)

- Alterar `app/cloud/src` (Lambda implantada e evidenciada): só testes de paridade (C14).
- Ler limites de validação da API no web em tempo de execução (C3 completo): exigiria rota nova; fica um teste de contrato que falha se os números divergirem.
- Polling do laboratório com backoff (X3) e aviso de sessão expirada (C11): decisões de produto, ficam como estão; o aviso morto é removido.
