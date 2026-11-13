# Estado do desenvolvimento

> Arquivo vivo, mantido pelo orquestrador (CLAUDE.md §5). É o primeiro arquivo lido em cada sessão: seja curto e factual.

**Atualizado em:** 12/11/2026, 21h50 · **Dias até o prazo (19/11 23h55):** 7 · **Fase:** D1 em andamento (S0 e S1 integradas; S6 com código integrado e download completo aguardando aprovação)

## Concluído

- Documentação de base: proposta, plano v1.1 (D01–D25), revisões adversariais (R01–R30) e `CLAUDE.md`.
- **S0 — esqueleto (12/11), em `main`.** Evidência executada pelo orquestrador:
  - `.gitattributes` (LF; `.ps1` em CRLF; binários), `core.longpaths=true`, `.gitignore` ampliado (§15.3).
  - `uv` por componente (`app/api`, `app/ml`, `app/cloud`, `app/tools`), Python 3.11, `uv.lock` versionado.
  - `app/docker-compose.yml`, profile `teste`: `up -d --wait` → 3 serviços *healthy*; Oracle 26ai Free (usuário `CITIZENTECH` no `FREEPDB1`), Postgres 17.11 na 5433, Mongo 8.0.38 na 27018; portas respondendo no host.
  - `app/config/limiares.json` e `GET /health` (RED por `NotImplementedError`, depois verde pelo `TestClient`).
  - `app/tools/md_para_pdf.py`: 5 testes com Edge real; `plano_desenvolvimento.md` → PDF de 14 páginas; `--max-paginas 2` → saída 1.
  - `app/web`: React 19.3 + Vite 8 + Tailwind 4 + Astryx 0.7.14. `pnpm run test` → 1 passou; `pnpm run build` → ok; renderização conferida por captura de tela no Edge. **Plano B (Radix) não acionado.**
- **S1 — limiares compartilhados (12/11), em `main`.** Implementada pelo `agy` (job pwsh-135), aceita depois de: testes reexecutados (api 48, cloud 50), busca por limiar fixo no código (nenhum), 15 contraexemplos fora da tabela. Um defeito achado no aceite (inteiro gigante gerava `OverflowError`) foi corrigido pelo orquestrador com teste antes. Os 3 cenários classificam igual na API e na Lambda.
- **S6 — ingestão do Novo Caged, código em `main` (12/11).** Duas rodadas de `agy` (jobs pwsh-134 e pwsh-183) e ajustes do orquestrador. `uv run pytest` em `app/ml` → 23 passaram.
  - Smoke real de 202609 (em temporário): MOV 4 307 569 linhas lidas e 93 175 gravadas; FOR 1 540; EXC 59; 40 s. Conferência independente: 46 378 admissões e 800 células CBO × UF de superior+ idênticas à sondagem feita pelo orquestrador antes do agente.
  - Nenhuma coluna sensível no Parquet (28 colunas; idade, sexo, raça/cor e deficiência nunca são lidas).
  - Achados do aceite da rodada 1, todos corrigidos na rodada 2 com teste antes: falha de rede na listagem virava `ausente_na_fonte`; a retomada ignorava a troca da lista de ocupações; um registro `ingerido` podia ser rebaixado; um arquivo corrompido derrubava o período; gravações não atômicas; a CLI só imprimia no fim.
  - Ajustes do orquestrador: exceção própria para o aborto por disco; o hash da lista de ocupações passou a depender só do conjunto de códigos (aprovar a lista ou mover um código da reserva para um destino não força novo download).

## Em andamento

- Nenhum job ativo, nenhum worktree. Serviços de teste do compose **parados** (`stop`; volumes preservados).
- **S6 — download completo (81 competências): NÃO executado.** Depende da aprovação da lista de ocupações abaixo. `.dados\caged\` ainda não existe.

## Lista de ocupações CBO — PROVISÓRIA, aguardando aprovação do usuário

Evidência completa em `GS\.kaiser\reports\S6-sonda-cbo\` (contagens por CBO × UF de 202609, histórico de 6 meses de janeiro, scripts e a lista em JSON). Contagens abaixo: admissões com superior completo ou mais, Brasil, só o arquivo MOV de set/2026.

| Destino | CBO de 6 dígitos recomendados | Sup+ no mês | UFs com ≥ 4 no mês |
|---|---|---|---|
| 1 Dados/BI | 211205, 211210, 211215, 211220, 142330, 261215 | 3 034 | 22 |
| 2 Monitoramento/IoT | 212415, 202110, 202120, 202105, 202115, 300105, 313410 | 366 | 14 |
| 3 Processos | 214905, 214910, 214925, 214930, 391210, 391105 | 1 595 | 22 |
| 4 Projetos/Produto | 142520, 142605 | 676 | 12 |
| 5 Suporte/Infra | 212420, 212410, 212310, 212315, 317210 | 2 955 | 24 |
| 6 Desenvolvimento | 212405, 317110, 317105, 317120, 212205, 212215, 212425, 212430 | 5 925 | 24 |

Reserva (baixada junto, sem destino atribuído): 211110, 142335, 214355, 300110, 313415, 391220, 313405, 391125, 391205, 252105, 142315, 142705, 142510, 142535, 212305, 212320, 313220, 317205, 142530, 142505, 212210, 203105.

Pontos que o usuário precisa decidir ou conhecer:

- **Destino 1 depende de 142330 (Analista de negócios): 2 769 das 3 034.** Sem ele sobram 265 por mês e 11 UFs. O código fica na família 1423 (gerentes de comercialização, marketing e comunicação).
- **Destino 4 tem só 2 códigos.** "Gerente de produtos" aparece como sinônimo de 142315 (Gerente de marketing), que está na reserva: incluí-lo leva a 1 219 e 17 UFs, mas mistura gerentes de marketing.
- **Destino 3 não tem código próprio de "analista de processos".** Os códigos são aproximações. 252105 (Administrador, 3 907) ficou na reserva por ser genérico demais.
- **Destino 2 é esparso** (366 no país): a abstenção por UF (D04a) vai ser frequente.
- **Quebras de série:** 211220 (Cientista de dados) só aparece a partir de 2024; 212425 e 212430 a partir de 2022.
- **Fontes:** títulos do layout oficial do Caged (MTE). O site oficial da CBO exige reCAPTCHA; sinônimos e o título de 211220 vêm de espelho público (fonte secundária). As duas fontes divergem sobre 253120, que não está na lista.
- "UFs com ≥ 4 no mês" é só uma aproximação, com um único mês, da regra de densidade de D04a (≥ 10 por trimestre na média do treino).

## Bloqueios e pendências [HUMANO]

- [ ] **Aprovar a lista de ocupações** (bloqueia o download completo do Caged, caminho crítico).
- [ ] **Disco: 5,6 GB livres, abaixo do aviso de 6 GB.** A queda de cerca de 5 GB durante a sessão não foi explicada (detalhe em CLAUDE.md §14.3). A ingestão aborta abaixo de 4 GB. Liberar espaço antes do download e antes do PyTorch (D3).
- [ ] `MONGODB_URI` completa e IP liberado no Atlas.
- [ ] Senha correta do Oracle FIAP.
- [ ] Sessão do Learner Lab e porta 5432 do RDS antes do D4.
- [ ] Caminho da IA de sentimento (créditos HF ou Comprehend).
- [ ] AWS CLI (instalar ou usar o console).
- [ ] Push para o GitHub: `main` está 19 commits à frente de `origin/main`; nada foi enviado.
- [ ] `gh auth refresh -s project,read:project`; ideia da live (AIC); quem grava cada vídeo.

## Validação das credenciais (12/11, sem expor valores)

| Serviço | Resultado | Ação |
|---|---|---|
| OpenRouter | ok: chave ativa (limite US$ 7); `deepseek-v4.1-flash-1017` devolveu JSON válido via json_schema | — |
| Adzuna | ok: 200 (1 de 25 chamadas usada como smoke, registrada no contador) | snapshot só na S6, com o contador |
| Hugging Face | token válido, mas a inferência do modelo do enunciado retorna **402 (sem créditos)** | **decidir:** comprar créditos HF ou usar o caminho B (Amazon Comprehend, `pt`) |
| Lambda (reaproveitada) | 200, mas é `cp2-hello-world`, que responde 'Hello World' em toda rota | subir o código de ingestão na S4 |
| RDS (reaproveitado) | **TCP 5432 com timeout** a partir do IP público desta máquina | abrir o Learner Lab, liberar o SG (D09), criar `app_ingest` |
| Oracle FIAP | **ORA-01017** | corrigir `ORACLE_FIAP_PASSWORD` |
| Mongo Atlas | **`MONGODB_URI` contém só o nome de usuário** | preencher a URI completa e liberar o IP |

## Decisões tomadas fora do plano

- **Equipe (12/11):** Guilherme Orugian (RM572882), Lucas Henrique (RM571901), Rodrigo Bettio (RM573725).
- **LLM fallback (D06a):** `xiaomi/mimo-v2.6-flash`.
- **AWS reaproveitada (12/11):** Lambda `cp2-hello-world` e RDS `cp1-cloud`, com alteração autorizada pelo usuário.
- **S0 feita pelo orquestrador, não pelo `agy` (12/11).** É andaime e configuração (compose, uv, gitignore, smokes), em passos pequenos e verificados um a um. A regra de D14 (implementação via `agy`) foi seguida na S1 e na S6.
- **Escolhas locais da S0:** pacote da API chama-se `citizentech`; `app/tools` é projeto uv sem pacote; `@stylexjs/stylex` fixado em 0.19.1, porque a 0.19.2 tinha menos de um dia e o pnpm a recusa (a política não foi afrouxada); o `postinstall` do Astryx fica desativado; `GS22026_enunciadosOG.txt` (material do professor) mantém os bytes originais via `-text`.
- **S6:** o Parquet guarda uma linha por movimentação filtrada, um arquivo por tipo e competência, em `.dados\caged\parquet\`, com `procedencia.json` ao lado. O plano cita `app/data/`; vale o mapa do CLAUDE.md §15.1 (`.dados`, fora do git).
- **S6:** a ingestão baixa a união dos códigos dos destinos com a reserva (56 códigos). Assim a atribuição de códigos a destinos pode ser ajustada até o congelamento da S7 sem novo download.

## Não verificado

- `GET /health` num servidor `uvicorn` real (só pelo `TestClient`; a tentativa de subir o servidor falhou por erro da ferramenta de shell, sem processo órfão).
- Títulos oficiais da CBO no site do MTE (reCAPTCHA).
- Competências 202003 a 202005: quais dos arquivos MOV/FOR/EXC existem.
- Tempo e tamanho do download completo: estimativa por um único mês (cerca de 40 s e 1,5 MB por competência; perto de 55 min e 125 MB no total).

## Próximo passo exato

1. Com a lista aprovada: gravar a versão aprovada em `app/catalogo/ocupacoes_cbo.json` (commit), conferir o disco (≥ 6 GB) e rodar, em background, em `app/ml`:
   `uv run python -m citizentech_ml.ingestao --ocupacoes ..\catalogo\ocupacoes_cbo.json --inicio 202001 --fim 202609` com `$env:CITIZENTECH_DADOS` definido. Depois, `cobertura()` e conferência de 202609 contra a sondagem.
2. Snapshot da Adzuna (script com contador, máximo de 12 chamadas), só com o ok do usuário.
3. D2: S2 (leituras CTP), S3 (outbox) e S5 (auth) na frente A; S7 (features e split) na frente B, assim que o Parquet existir.
