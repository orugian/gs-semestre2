# CitizenTech — FIAP Global Solution 2026.2

Aplicação web que ajuda profissionais graduados e experientes a comparar caminhos de transição de carreira com evidências do mercado formal (Novo Caged), separando o que é **observado**, **previsto**, **simulado** e **trabalho futuro**.

Integrantes: Guilherme Orugian (RM572882) · Lucas Henrique (RM571901) · Rodrigo Bettio (RM573725).

**Vai gravar um vídeo?** Comece por [gravacao/README.md](gravacao/README.md): um script prepara o computador e outro abre a aplicação. **Vai enviar no Portal?** Cada pasta `0X_*` tem um `LEIA-ME.md` com os arquivos exatos a anexar.

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
| `app/dados_publicos` | Snapshot público de mercado (Novo Caged agregado, com SHA-256) usado pelas telas Mercado e Painel técnico |
| `app/tools` | Empacotador de entregas, gerador de PDF, demos e scripts de teste |
| `gravacao` | Kit para gravar os vídeos: scripts de preparo, roteiros por disciplina e quadro de gestão |
| `01_AICSS` … `09_AIC` | Entregáveis por disciplina (`LEIA-ME.md` diz o que enviar): relatórios (`.md` + PDF), evidências e cópias **geradas** do código |
| `docs` | Plano, proposta, estado vivo, enunciados (`docs/enunciados/`), UML; `docs/historico/` guarda o que não é mais operacional |

As cópias de código dentro de `0X_*` são geradas por `app/tools/empacotar_entregas.py` — edite sempre a origem em `app/` e rode o empacotador.

## Pré-requisitos

Windows 11 + PowerShell 5.1 (os comandos abaixo), ou equivalente.

| Ferramenta | Versão usada | Para |
|---|---|---|
| [uv](https://docs.astral.sh/uv/) | 0.11 (instala o Python 3.11 sozinho) | todos os componentes Python |
| Node.js + pnpm | Node 24, pnpm 11 | `app/web` |
| Docker Desktop | 29 | bancos de teste (Oracle Free, PostgreSQL, MongoDB) |
| Microsoft Edge | qualquer recente | geração de PDF e testes Playwright |
| g++ no PATH | — | necessário para a suíte completa de `tools` (compilação do firmware no host); dispensável para iniciar o site |

Dados grandes (parquets do Caged, snapshots, artefatos de modelo) ficam **fora do repositório**, na pasta indicada por `CITIZENTECH_DADOS`.

## Configurar

```powershell
if (-not (Test-Path app\.env)) { Copy-Item app\.env.example app\.env }
# Preencha as senhas locais em app/.env antes de subir os bancos. Não sobrescreva um ambiente existente.
docker compose -f app\docker-compose.yml --profile teste up -d --wait
```

O compose cria o Oracle com o usuário do app (`ORACLE_USER`). Os testes da API usam um schema separado cujo nome começa com `CT_` e contém `TESTE` (trava de segurança dos testes). Crie-o uma vez:

```powershell
docker exec -it citizentech-oracle-1 bash -c 'sqlplus -L -s system/"$ORACLE_PASSWORD"@localhost:1521/FREEPDB1'
```

No SQL*Plus do **container local**, execute as linhas abaixo uma a uma. Informe no prompt oculto a senha de `ORACLE_TESTE_PASSWORD` que você escolheu em `app/.env`; não a coloque no comando nem na gravação. Se já existir um schema de teste preparado, não recrie o usuário.

```sql
SET VERIFY OFF
ACCEPT senha_teste CHAR PROMPT 'Senha do schema de teste: ' HIDE
CREATE USER CT_TESTE_S9 IDENTIFIED BY "&senha_teste" QUOTA UNLIMITED ON USERS;
UNDEFINE senha_teste
GRANT CREATE SESSION, CREATE TABLE, CREATE SEQUENCE TO CT_TESTE_S9;
EXIT;
```

## Testar

```powershell
# Na raiz: API, Cloud, ferramentas e web; não executa a suíte científica.
powershell -NoProfile -File app\tools\testar_tudo.ps1 -SemML

# Ou um componente (cada exemplo começa na raiz):
. .\app\tools\ambiente_teste.ps1
Push-Location app\api; uv sync --frozen; uv run --frozen pytest -rs; Pop-Location
Push-Location app\web; pnpm install --frozen-lockfile; pnpm run test; pnpm run build; Pop-Location
```

O runner requer os três bancos de teste. Em execuções individuais, confira os *skips* no resumo: teste pulado não comprova integração. Sem `-SemML`, o runner inclui os testes unitários de `ml` (não os notebooks). `-ComE2E` exige também a API de teste na porta 8000, o snapshot de Mercado e a porta 5173 livre para o Playwright. O caso da persona tem configuração própria; não forneça credenciais reais ao runner de teste.

## Rodar a aplicação

Abra **dois terminais na raiz**. No primeiro, use o schema de testes (não a persona existente). O auxiliar configura chaves efêmeras e caminhos de runtime novos; não use o diretório da outbox antiga.

```powershell
. .\app\tools\ambiente_teste.ps1
cd app\api
uv sync --frozen
# Somente no primeiro preparo do schema de TESTE recém-criado: lista os DDL 001–007.
uv run --frozen python ..\tools\aplicar_ddl.py
# Confira a lista e o schema CT_TESTE_S9; então aplique nele (não no banco do app).
uv run --frozen python ..\tools\aplicar_ddl.py --confirmar
uv run --frozen uvicorn citizentech.main:app --host 127.0.0.1 --port 8000
```

No segundo terminal:

```powershell
cd app\web
pnpm install --frozen-lockfile
pnpm run dev     # http://localhost:5173; encerrar com Ctrl+C antes do Playwright
```

As telas **Mercado** e **Painel técnico** usam o snapshot público versionado em `app/dados_publicos/mercado/` (validado por SHA-256). Para usar outro snapshot gerado por `app/ml`, aponte `CITIZENTECH_MERCADO_SNAPSHOT` para a pasta dele.

## Gerar e conferir as entregas

```powershell
$env:CITIZENTECH_DADOS = 'C:\caminho\para\.dados'
cd app\tools; uv run python empacotar_entregas.py; uv run python empacotar_entregas.py --verificar
```

Regras do projeto, decisões (D01–D25) e estado: [CLAUDE.md](CLAUDE.md), [plano](docs/plano_desenvolvimento.md), [estado](docs/estado.md).
