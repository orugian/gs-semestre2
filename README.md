# CitizenTech — FIAP Global Solution 2026.2

Aplicação web que ajuda profissionais graduados e experientes a comparar caminhos de transição de carreira com evidências do mercado formal (Novo Caged), separando o que é **observado**, **previsto**, **simulado** e **trabalho futuro**.

Integrantes: Guilherme Orugian (RM572882) · Lucas Henrique (RM571901) · Rodrigo Bettio (RM573725).

## Onde está cada coisa

| Pasta | Conteúdo |
|---|---|
| `app/api` | API FastAPI (conta, consentimentos, currículo redigido, competências, comparação, plano, exercício, laboratório, leituras IoT + outbox) |
| `app/web` | Interface React 19 + TypeScript + Vite (Astryx), testes Vitest e Playwright/axe |
| `app/ml` | Ingestão do Novo Caged, features, modelos clássicos, rede neural (PyTorch CPU) e estatística |
| `app/cloud` | Lambda + simulador do dispositivo (AWS Learner Lab, RDS PostgreSQL) |
| `app/iot` | Firmware ESP32 (Wokwi), com lógica testável no computador |
| `app/db` | DDL Oracle (dialeto 19c) e consultas de evidência; scripts MongoDB |
| `app/catalogo`, `app/config` | Catálogo curado dos 6 destinos (YAML) e fonte única de limiares (`limiares.json`) |
| `app/tools` | Empacotador de entregas, gerador de PDF, demos e scripts de teste |
| `01_AICSS` … `09_AIC` | Entregáveis por disciplina: relatórios (`.md` + PDF), evidências e cópias **geradas** do código |
| `docs` | Plano, proposta, estado vivo, enunciados, UML; `docs/historico/` guarda o que não é mais operacional |

As cópias de código dentro de `0X_*` são geradas por `app/tools/empacotar_entregas.py` — edite sempre a origem em `app/` e rode o empacotador.

## Pré-requisitos

Windows 11 + PowerShell 5.1 (os comandos abaixo), ou equivalente.

| Ferramenta | Versão usada | Para |
|---|---|---|
| [uv](https://docs.astral.sh/uv/) | 0.11 (instala o Python 3.11 sozinho) | todos os componentes Python |
| Node.js + pnpm | Node 24, pnpm 11 | `app/web` |
| Docker Desktop | 29 | bancos de teste (Oracle Free, PostgreSQL, MongoDB) |
| Microsoft Edge | qualquer recente | geração de PDF e testes Playwright |
| g++ (opcional) | — | teste da lógica do firmware no computador (`app/tools/tests/test_firmware.py`) |

Dados grandes (parquets do Caged, snapshots, artefatos de modelo) ficam **fora do repositório**, na pasta indicada por `CITIZENTECH_DADOS`.

## Configurar

```powershell
Copy-Item app\.env.example app\.env      # preencha: [GERADO] = qualquer segredo aleatório local
docker compose -f app\docker-compose.yml --profile teste up -d --wait
```

O compose cria o Oracle com o usuário do app (`ORACLE_USER`). Os testes da API usam um schema separado cujo nome começa com `CT_` e contém `TESTE` (trava de segurança dos testes). Crie-o uma vez:

```powershell
"CREATE USER CT_TESTE_S9 IDENTIFIED BY ""<ORACLE_TESTE_PASSWORD>"" QUOTA UNLIMITED ON USERS;`nGRANT CREATE SESSION, CREATE TABLE, CREATE SEQUENCE TO CT_TESTE_S9;" |
  docker exec -i citizentech-oracle-1 bash -c 'sqlplus -s system/"$ORACLE_PASSWORD"@localhost:1521/FREEPDB1'
```

## Testar

```powershell
# tudo de uma vez (carrega as variáveis de teste de app/.env sem exibi-las)
powershell -NoProfile -ExecutionPolicy Bypass -File app\tools\testar_tudo.ps1          # -SemML para pular o ML; -ComE2E para Playwright

# ou um componente
. .\app\tools\ambiente_teste.ps1
cd app\api; uv sync; uv run pytest          # idem em app\cloud, app\tools, app\ml
cd app\web; pnpm install; pnpm run test; pnpm run build
```

Testes que dependem de banco são **pulados** (não falham) se as variáveis de teste não existirem; o resumo do pytest mostra quantos.

## Rodar a aplicação

```powershell
. .\app\tools\ambiente_teste.ps1
cd app\api; uv run uvicorn citizentech.main:app --host 127.0.0.1 --port 8000     # GET /health
cd app\web; pnpm run dev                                                         # http://localhost:5173
```

A tela **Mercado** precisa de `CITIZENTECH_MERCADO_SNAPSHOT` (snapshot gerado por `app/ml`); sem ele, a API responde 503 e a interface mostra o erro.

## Gerar e conferir as entregas

```powershell
$env:CITIZENTECH_DADOS = 'C:\caminho\para\.dados'
cd app\tools; uv run python empacotar_entregas.py; uv run python empacotar_entregas.py --verificar
```

Regras do projeto, decisões (D01–D25) e estado: [CLAUDE.md](CLAUDE.md), [plano](docs/plano_desenvolvimento.md), [estado](docs/estado.md).
