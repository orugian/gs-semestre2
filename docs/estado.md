# Estado do desenvolvimento

> Arquivo vivo, mantido pelo orquestrador (CLAUDE.md §5). É o primeiro arquivo lido em cada sessão: seja curto e factual.

**Atualizado em:** 13/11/2026, 10h20 · **Dias até o prazo (19/11 23h55):** 6,5 · **Fase:** fim do D1 (S0 e S1 integradas; S6 com código integrado, lista de ocupações aprovada e download completo em execução)

## Concluído

- Documentação de base: proposta, plano v1.1 (D01–D25), revisões adversariais (R01–R30) e `CLAUDE.md`.
- **S0 — esqueleto (12/11), em `main`.** Evidência executada pelo orquestrador:
  - `.gitattributes`, `core.longpaths=true`, `.gitignore` ampliado (§15.3); `uv` por componente (`app/api`, `app/ml`, `app/cloud`, `app/tools`), Python 3.11.
  - `app/docker-compose.yml`, profile `teste`: 3 serviços *healthy* (Oracle 26ai Free no `FREEPDB1`, Postgres 17.11 na 5433, Mongo 8.0.38 na 27018), login testado nos três.
  - `app/config/limiares.json` e `GET /health` (RED → GREEN pelo `TestClient`).
  - `app/tools/md_para_pdf.py`: 5 testes com Edge real; plano → PDF de 14 páginas; `--max-paginas 2` → saída 1.
  - `app/web`: React 19.3 + Vite 8 + Tailwind 4 + Astryx 0.7.14; teste, build e captura de tela ok. **Plano B (Radix) não acionado.**
- **S1 — limiares compartilhados (12/11), em `main`.** Via `agy`. Os 3 cenários classificam igual na API e na Lambda; tabela compartilhada em `app/config/casos_limiares.json`.
- **S6 — ingestão do Novo Caged: código em `main` (12/11).** Via `agy`, 2 rodadas, mais ajustes do orquestrador. Smoke real de 202609 conferido contra contagem independente (46 378 admissões; 800 células CBO × UF idênticas). Nenhuma coluna sensível no Parquet.
- **Lista de ocupações CBO aprovada pelo usuário (13/11)**, sem alterações, seguindo as recomendações do orquestrador nos pontos fracos. Versionada em `app/catalogo/ocupacoes_cbo.json` (6 destinos, 34 códigos; 22 de reserva; título e fonte de cada título; limitações declaradas no próprio arquivo). Evidência da escolha: `GS\.kaiser\reports\S6-sonda-cbo\`.
- **Push (13/11):** `main` enviado para `https://github.com/orugian/gs-semestre2` (remoto `gs-semestre2`), a pedido do usuário. Antes do envio: gitleaks em todo o histórico → sem vazamentos; nenhum `.env`, chave ou dado rastreado.
- Regressão em `main` (13/11): `uv run pytest` → api 48, cloud 50, ml 25, tools 5. Web: 1 teste (vitest, executado em 12/11).

## Em andamento

- **S6 — download completo (202001–202609), job `pwsh-204` do harness, iniciado em 13/11 às 10h14.**
  - Destino: `GS\.dados\caged\parquet\` + `GS\.dados\caged\procedencia.json`. Log: `GS\.kaiser\reports\S6-download-completo.log` (UTF-16; ler com `Get-Content -Encoding Unicode`).
  - Ritmo medido no início: 4 competências em 1,6 min (previsão de cerca de 35 min no total).
  - **Se a sessão terminar antes, o job pode morrer junto. A retomada é segura:** arquivos já ingeridos são pulados sem rede. Basta repetir o comando do "Próximo passo".
  - **A conferência do resultado ainda não foi feita** (ver "Próximo passo", item 1).
- Nenhum worktree, nenhum `agy`. Serviços de teste do compose **parados** (`stop`; volumes preservados).

## Bloqueios e pendências [HUMANO]

- [ ] **Repositório público:** `orugian/gs-semestre2` está **público** e agora contém nomes e RMs da equipe, e-mails nos metadados dos commits e o material do professor (`docs\material_por_cadeira\`, PDFs dos enunciados). Confirmar que é isso mesmo ou tornar privado.
- [ ] **Qual é o remoto oficial?** `origin` continua `insonia999/GS2_26` (D14b) e não recebeu push. Decidir se `gs-semestre2` substitui o `origin` ou se os dois recebem push.
- [ ] `MONGODB_URI` completa e IP liberado no Atlas.
- [ ] Senha correta do Oracle FIAP.
- [ ] Sessão do Learner Lab e porta 5432 do RDS antes do D4.
- [ ] Caminho da IA de sentimento (créditos HF ou Comprehend).
- [ ] AWS CLI (instalar ou usar o console).
- [ ] Ok para o snapshot da Adzuna (até 12 chamadas, com contador).
- [ ] Revisão humana das rubricas até **D3 (15/11) às 18h**, senão corte automático para 3 destinos (R29).
- [ ] `gh auth refresh -s project,read:project`; ideia da live (AIC); quem grava cada vídeo.

**Disco:** 16,0 GB livres em 13/11 às 10h (eram 5,6 GB em 12/11 às 21h40; a recuperação aconteceu fora da sessão e a causa da queda continua sem explicação, ver CLAUDE.md §14.3).

## Validação das credenciais (12/11, sem expor valores)

| Serviço | Resultado | Ação |
|---|---|---|
| OpenRouter | ok (limite US$ 7); JSON válido via json_schema | — |
| Adzuna | ok (1 de 25 chamadas usada como smoke) | snapshot com o contador, depois do ok |
| Hugging Face | token válido, inferência retorna **402 (sem créditos)** | decidir: créditos HF ou Comprehend |
| Lambda (reaproveitada) | 200, mas ainda é `cp2-hello-world` | subir o código na S4 |
| RDS (reaproveitado) | **TCP 5432 com timeout** | Learner Lab, SG (D09), usuário `app_ingest` |
| Oracle FIAP | **ORA-01017** | corrigir `ORACLE_FIAP_PASSWORD` |
| Mongo Atlas | **`MONGODB_URI` só com o usuário** | URI completa e IP liberado |

## Decisões tomadas fora do plano

- **Equipe (12/11):** Guilherme Orugian (RM572882), Lucas Henrique (RM571901), Rodrigo Bettio (RM573725).
- **LLM fallback (D06a):** `xiaomi/mimo-v2.6-flash`.
- **AWS reaproveitada (12/11):** Lambda `cp2-hello-world` e RDS `cp1-cloud`, com alteração autorizada.
- **S0 feita pelo orquestrador, não pelo `agy`:** andaime e configuração, em passos pequenos. D14 foi seguido na S1 e na S6.
- **Escolhas locais da S0:** pacote da API chama-se `citizentech`; `app/tools` é projeto uv sem pacote; `@stylexjs/stylex` fixado em 0.19.1 (a 0.19.2 tinha menos de um dia e o pnpm a recusa); `postinstall` do Astryx desativado; `GS22026_enunciadosOG.txt` mantém os bytes originais (`-text`).
- **S6:** Parquet com uma linha por movimentação filtrada, um arquivo por tipo e competência, em `.dados\caged\parquet\` (o plano cita `app/data/`; vale o mapa do CLAUDE.md §15.1).
- **S6:** a ingestão baixa a união dos destinos com a reserva (56 códigos); o hash da lista depende só do conjunto de códigos. A atribuição de códigos a destinos pode mudar até o congelamento da S7 sem novo download.
- **Ocupações (13/11), decisões do usuário:** manter 142330 no destino 1; manter 142315 na reserva (destino 4 fica com 2 códigos); 252105 na reserva; aceitar a esparsidade do destino 2 e as quebras de série de 211220, 212425 e 212430.

## Não verificado

- Resultado do download completo (cobertura, contagens, tamanho final).
- `GET /health` num servidor `uvicorn` real (só pelo `TestClient`).
- Títulos oficiais da CBO no site do MTE (reCAPTCHA); o título de 211220 vem de fonte secundária.

## Próximo passo exato

1. **Fechar a S6.** Em `app\ml`, com `$env:CITIZENTECH_DADOS = 'C:\Users\orugi\Documents\Projetos\FIAP\GS\.dados'` e `$env:PYTHONUTF8 = '1'`:
   - se o log não terminar com `Resumo da ingestao`, repetir `uv run python -m citizentech_ml.ingestao --ocupacoes ..\catalogo\ocupacoes_cbo.json --inicio 202001 --fim 202609` (retoma de onde parou);
   - conferir `cobertura(dados, "202001", "202609")`: nenhuma `falha` nem `pendente`; cada `ausente_na_fonte` confirmado por listagem do FTP (já confirmados em 12/11: FOR e EXC de 202001, EXC de 202002);
   - conferir as admissões do MOV de 202001, 202101, 202201, 202301, 202401, 202501 e 202609 contra as contagens independentes em `GS\.kaiser\reports\S6-sonda-cbo\` (`sonda_historico_cbo.csv` e `sonda_adm_202609_cbo_uf.csv`, por CBO);
   - confirmar `caged\bruto\` vazio, medir o tamanho do Parquet e registrar aqui.
2. **D2, frente B (caminho crítico):** contrato e `agy` da **S7** (features e split: T04, T05, T18, T19; revisão independente obrigatória) + EDA + medição da defasagem do FOR (R02) + baselines.
3. **D2, frente A:** S2 (leituras CTP, modo isolado), depois S3 (outbox) e S5 (auth), estas duas com revisão independente. Subir os serviços de teste antes das fatias que usam banco. Rascunho por agente do catálogo YAML dos 6 destinos (ESCO, questões, rubricas).
4. Snapshot da Adzuna, só com o ok do usuário.
