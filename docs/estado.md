# Estado do desenvolvimento — CitizenTech

> Primeiro arquivo da próxima sessão. Snapshot documental, não monitoramento em tempo real. Histórico detalhado de aceites/adjudicações: `git show d2ddec4:docs/estado.md` e trilha retida em `../.kaiser/reports/`.

**Checkpoint funcional:** `main` em `d2ddec4`, conferido em16/11/2026 às00h30 (UTC−3), sem mudanças pendentes naquele instante. Prazo: **19/11/2026 às23h55** —3,98 dias na conferência. A aplicação **ainda não está integrada ponta a ponta**. Esta atualização é documental; não houve nova execução das suítes nesta tarefa de handoff.

## Tarefa documental em andamento nesta sessão

Handoff e prompt de retomada já entregues ao usuário. Documentação reorganizada em `1c9f75a`; PRODUCT.md e DESIGN.md, de escopo documental, em `7fd8769`. Usuário confirmou caderno interno offline/responsivo, não apresentação comercial nem alteração da interface do app. **Autoria do HTML:** primeira chamada `pwsh-152` concluída/coletada;6testes estáticos próprios passaram, mas leitura/render encontrou falsos feitos(firmware/PII/Cloud), rótulos científicos incorretos, fronteira do holdout mal descrita e diagrama mobile ilegível. Em correção na segunda/última rodada: **job `pwsh-168`**, agy, mesmo worktree `../GS-wt/DOC-panorama`, branch `fatia/DOC-panorama`, escrita exclusiva `docs/panorama_projeto.html`. BrowserR1 `pwsh-166` coletado: Edge real, foco/contraste sem achados, porém mobile solicitou390/360 e layout expandiu528; verificador fortalecido, nenhum aceite declarado. RED próprio: arquivo ausente→AssertionError,1failed;6testes estáticos em `.kaiser/tmp/test_panorama_documental.py`. Auditoria independente somente leitura confirmou links/estado inicial/quota antigos; corrigidos conforme CLAUDE e57links locais próprios verificados sem quebrados. Aguardar R2, repetir render/aceite e integrar. Há somente este job próprio ativo; processo agy de origem não confirmada foi preservado, sem exceder2.

## 1. Ponto de parada

- S0–S3, S5, ingestão S6, features/split S7 e experimentos ML/RNA/D11 estão integrados em `main`, com as limitações abaixo.
- Última regressão integrada ML/RNA/Estatística: **227passed e ruff limpo**, execução15/16 de novembro (`pwsh-114`). API: **208passed,0skip com Oracle real**, na etapa S5. Não somar esses números como se fossem uma única execução.
- ML/RNA foram treinados e avaliados em dados reais segregados; artefatos reabertos e previsões/métricas conferidas independentemente. **Nenhum modelo foi promovido.**
- D11 foi executada em229 municípios de SP; análises e diagnósticos reais conferidos. PDFs de evidência ML/RNA e Estatística:3 páginas cada, **preliminares**, não pacotes acadêmicos finais.
- **Holdout2026 fechado.** Não retunar com os resultados já vistos de2025. Nenhum push nesta retomada, nenhum segredo lido e nenhum dado/schema/volume apagado.
- Frontend atual: somente esqueleto Astryx; confirmado por leitura de [App.tsx](<../app/web/src/App.tsx>). A API principal só inclui leituras, autenticação, consentimentos e saúde; [main.py](<../app/api/src/citizentech/main.py>) ainda não inclui Mercado/LLM/jornada profissional.

## 2. O que está verificado

| Frente | Implementado / evidência | Limite que permanece |
|---|---|---|
| Base técnica | uv por componente, React/Astryx, limiares compartilhados, Docker de teste e geração PDF Edge | Smoke da base não significa jornada funcional |
| CTP / leituras | POST/GET, validações400/401/429, indicadores, CSV e smoke HTTP local | ESP32/Wokwi real ainda não demonstrado |
| Outbox S3 | SQLite durável, idempotência201/200/409, reconciliação, retry; imagem Docker exercitada | Lambda/RDS reais não integrados; processo único |
| Auth S5 | JWT/cookie, CSRF, Argon2id, consentimentos por proprietário; Oracle real208passed | UI de login ausente; limitações de rate limit por processo/logout/enumeração documentadas |
| Caged S6 |239 Parquets de243 fontes verificadas,4 ausências legítimas; descarte de atributos sensíveis | Ingestão histórica incluiu2026; isso **não** autoriza reabrir esses arquivos agora |
| Features / ML | As-of, embargo, densidade por fold, baselines, Ridge/RF/HGB e MLP CPU com duas configurações | Serving, promoção, model cards MongoDB, notebooks/slides e avaliação final pendentes |
| Estatística D11 |229 municípios, Z/OLS/Logit, teste municipal estratificado, histogramas/QQ/Shapiro/log1p | Script portátil, dispersões/resíduos e pacote PDF/PY/CSV final pendentes |
| Catálogo | Seis rascunhos e fontes ESCO preservados | Nenhuma das três rubricas do MVP foi aprovada por humano |
| Cloud / IoT / IA | Regras locais de risco e infraestrutura-base | S4, firmware próprio e S9–S15/jornada ainda pendentes |

Outras regressões registradas na etapa anterior: Cloud50passed; Tools20passed; Web1teste, typecheck/build. Não foram reexecutadas neste pedido documental.

## 3. Recortes e resultados — não misturar coortes

**Produto R29:** três destinos: Dados/BI, Monitoramento/IoT e Processos/Melhoria Contínua. O corte não aprova rubricas e não apaga os outros três rascunhos. Rotas futuras e UI devem consumir [escopo_mvp.json](<../app/catalogo/escopo_mvp.json>).

**ML/RNA:** superior/pós, três destinos×UF. Histórico2020 apenas para lags; fit202101–202409; validação202501–202509. Embargo, densidade e promoção D10/D04a/D10a inalterados. Validação:55 séries elegíveis de81;495 linhas.

| Modelo | MAE de validação |
|---|---:|
| Persistência |35,45253|
| Sazonal |33,59596|
| Ridge |34,25765|
| Random Forest |35,63387|
| HistGradientBoosting |39,73936|
| MLP A |31,65446|

MLP A foi escolhida no **CV do treino**, refit55 épocas. Ganho de MAE5,77896% vs sazonal; **não é promoção automática nem superioridade estatística demonstrada**. Os clássicos não superaram o sazonal. [Evidência ML/RNA](<../05_ML/evidencias/20261115_modelos_mvp_aceite.md>) e [recálculo JSON](<../05_ML/evidencias/20261115_modelos_mvp_aceite.json>).

**D11:** seis destinos e **todas as escolaridades**, SP, população com≥10 admissões2024; snapshots202412/202512, sem revisões2026. Duas explicativas autorizadas: salário mensal declarado2024 e %superior2024; participação municipal removida por aprovação humana. Pré-registro integral no plano§1.1.

-229 municípios,229 casos completos, nenhum município removido para melhorar ajuste. Dicionário:645 municípios+359999=Sp-Ignorado; a base não contém a categoria ignorada.
- Z: n20/α6%,seed42,p0,324213; n25/α9%,seed43,p0,659389; ambos não rejeitamH0. Normal **assumida** nos itens obrigatórios, não comprovada; Shapiro original p9,69×10⁻³² e log1p p8,01×10⁻⁸.
- OLS: R² simples3,626×10⁻⁷; múltipla0,021458 — resultados fracos preservados.
- Logística:183 treino/46 teste,80/20 estratificado,seed44,limiar0,5; matriz[[8,14],[7,17]],acurácia54,3478%. Teste municipal não é o holdout temporal de ML.
- [Evidência D11](<../08_Estatistica/evidencias/20261115_d11_aceite.md>) e [JSON real](<../08_Estatistica/evidencias/20261115_d11_aceite.json>).

## 4. Ativos e proteção operacional

Raízes externas: `GS=..`, `.dados=../.dados`, `.kaiser=../.kaiser`, worktrees=`../GS-wt`.

- DEV seis destinos: `../.dados/caged/painel/painel_desenvolvimento.parquet`, SHA `8e653b0047ceed204d25bf7c0d9d28c8d7944bd4e75c7f65bf4ea09651b4eb9e`.
- DEV MVP: `../.dados/caged/painel/r29_20261115_2041/painel_mvp.parquet`, SHA `33a898980916c841c325fb9e37b643484ee1d6f8b7017a19f52208de02e922c5`.
- Modelos próprios: `../.dados/artefatos/classicos/20261115_r29_aceite/` e `../.dados/artefatos/rna/20261115_r29_aceite/`, com manifestos/hashes. Hash é integridade local, não autenticidade contra atacante que controla manifesto.
- D11: `../.dados/estatistica/20261115_d11_aceite/base_municipal.csv` e manifesto; SHA CSV `5dbc73acfb01012a7aa0fa45ef457a7226639a8b48bda85b0389972f99a9a7ee`.
- D11 usa somente72 nomes canônicos2024/25, com gate antes de read/hash/footer, bloqueio de symlink/hardlink e vínculo nome×metadados. Perfil real:2.216.198 linhas R05/36,37MB comprimidos, não100M linhas nacionais. Iterrows é dívida de performance, não razão para mudar população.
- **Não reconstruir DEV com o loader legado no diretório misto de Parquets:** ele pode abrir2026 antes de filtrar. Proteção em memória não é barreira de I/O.
- **Não subir worker com dados reais e FUNCTION_URL:** `../.dados/runtime/outbox.db*` contém77 eventos antigos de teste. Arquivo preservado; remoção exige aprovação específica.
- Oracle local foi parado, volumes preservados. Schema S5 autorizado foi criado sem tocar o anterior; senha gerada apenas em memória foi esquecida ao encerrar runner. Não tentar recuperá-la nem alegar sessão/credencial ativa. Nova necessidade de credencial/schema exige o gate humano adequado.

## 5. Git, processos e auditoria

- Commits de integração: S5 `c391eac`; R29 `d807e10`; Estatística `df28804`; clássicos `7d1d4db`; RNA `a3a6866`; base municipal `1a47a1a`; último checkpoint de evidências `d2ddec4`.
- Worktrees S7 limpos/integrados e branches locais já removidos; fonte retida emmain. **Preservar original S5** `../GS-wt/S5-auth` em `b94b0de`, limpo; `../GS-wt/S5-red` em `112042d` mantido para reprodução.
- Jobs antigos até123 encerrados/coletados; são histórico, não tarefas a aguardar. Na conferência documental00h30 apareceu um processo `agy` PID16884, criado15/11às23h22, **origem não confirmada**. Não há vínculo de repo/worktree nos argumentos; isso não comprova seu cwd. Não foi cancelado. Reconferir antes de delegar; máximo2agy.
- Contratos, relatórios e snapshots de revisão em `.kaiser` foram mantidos. Adjudicações completas continuam no histórico d2ddec4 do estado; não reabrir fatias concluídas sem defeito concreto.
- Gitleaks bloqueou falsos positivos em fixture JWT e chave estatística; corrigidos sem allowlist/skip e sem alterar métricas. Toda entrega documental será novamente varrida antes do commit.
- Disco conferido:24,3GiB em16/11às00h30; avisar<6GiB, abortar ingestão<4GiB. Nenhuma limpeza de dados autorizada.

## 5a. Em andamento — sessão de implementação 16/11 (paralela à tarefa documental acima)

- **S8 integrada** em `main` (`a49682f`; fatia `2772689`): exportador `citizentech_ml.mercado.exportar` (snapshot JSON derivado dos artefatos, só hash+JSON/parquet, sem desserializar modelos) + API `GET /mercado/{destino}?uf=` (T06/T17) e `/mercado/{destino}/modelos` (R06, 6 modelos, nenhum promovido; exibido = baseline de menor MAE de validação = sazonal) + RV-RNA-01/02. Evidência desta sessão: testes S8 api13/ml37 passed; regressão em main **api193 passed (28 oracle deselecionados), ml241 passed, ruff limpo** (`pwsh-213`); export real DEV → conferência independente `.kaiser/tmp/conferir_snapshot_s8.py` ok (55 elegíveis/26 abstenções, MAE dos 6 bate com a evidência 15/11 e com recálculo direto); smoke HTTP via TestClient no snapshot real: SP 200 com metadados, AC 200 abstenção+contexto Norte, 404 fora do MVP, 400 `uf=XX`, `uf=sp` ok, nenhum termo proibido/NaN; artefato RNA real recarrega com a nova validação. RED do agente por asserção (501, AttributeError→ValueError, chave ausente) — não reproduzido pelo orquestrador (S8 fora da lista de fatias de risco). Revisão independente não obrigatória para S8.
  - Snapshot oficial: `../.dados/mercado/20261116_r29_aceite/` (SHA `snapshot_mercado.json` `9c093f93091fbda4bb4bdc796cd9eee9823da4005dfa22616950dba8d37540a3`), conferido pelo script independente. Para servir: `CITIZENTECH_MERCADO_SNAPSHOT` apontando para esse diretório. Model cards não estão no Mongo (Atlas sem senha em 12/11; gate humano). UI do painel técnico ainda não existe.
- **E08 integrada** em `main` (`181ba51`; fatia `04d1fa9`): programa portátil `app/ml/src/citizentech_ml/estatistica/analise_portatil.py` (sem importar `citizentech_ml`; fonte do `analise.py` de entrega), 8 figuras em `08_Estatistica/evidencias/figuras/`, JSON `20261116_analise_portatil.json` e `08_Estatistica/relatorio.md` reescrito. Evidência desta sessão: reexecução no CSV real → 16 checagens contra o JSON D11 de 15/11 sem divergência e JSON idêntico ao commitado; 9 testes; regressão ML em main **250 passed**, ruff limpo. Rodada 2 corrigiu LaTeX cru no PDF (o gerador não renderiza `$...$`), discutiu pontos extremos de salário (352885: 19 adm., R$527.726,85, 136,56× a mediana; 351210: R$86.712,01) mantidos por pré-registro, sem análise de sensibilidade (trabalho futuro), e vírgula decimal nas figuras. Orquestrador removeu 2 frases sem evidência. PDF de teste: 21 páginas, renderização conferida por screenshot. **PDF final:** gerar pelo empacotador com o `.md` e as figuras na mesma pasta relativa (gerar o PDF dentro de `evidencias/` quebra os caminhos das imagens). Pendentes humanos: nomes/RMs.
- `pwsh-222`: agy S15a-painel-mercado em `../GS-wt/S15a-painel-mercado` (base `ad42db6`): tela web de mercado + aba painel técnico R06 consumindo `/mercado` (Astryx, testes Vitest com fetch falso). Contrato `../.kaiser/contratos/S15a-painel-mercado.md`.
- `pwsh-215`: agy E05-notebooks em `../GS-wt/E05-notebooks` (base `a49682f`): notebooks ML e RNA em `app/ml/notebooks/` importando `citizentech_ml`, sem retreino, leitura só do painel DEV e artefatos; slides `05_ML/slides.md`.
- agy PID16884: pai é powershell interativo do Windows Terminal (15/11 23h22) — outra sessão (tarefa documental DOC-panorama acima); não é job desta sessão; preservado.
- Decisão local: `status_promocao="nao_decidida"` porque D10a depende da avaliação final com holdout fechado; o app exibe o baseline de menor MAE de validação, rotulado `previsto_retrospectivo`.

## 6. Próxima sessão — ordem recomendada

1. Ritual de [CLAUDE.md](<../CLAUDE.md>): data/prazo, este estado, git/worktrees/processos; Docker só quando a fatia exigir. Não ler segredos nem iniciar outra ingestão/treino.
2. **S8 Mercado API/model cards/R06:** ler plano§3 e§4, conferir gates Mongo/Oracle/artefatos e fechar o contrato público. Corrigir dívidas RV-RNA-01/02: `_medio`/`_media`, resumo MASE de referências, validação de `melhor_config`. Usar só artefatos próprios/raiz confiável; planejar pinning externo. **Não promover pela única condição de ganho de MAE.**
3. Em paralelo, frente documental/científica sem sobreposição: notebooks ML/RNA importando app/ml, execução completa, slides e análise crítica; finalizar Estatística com dispersões/Pearson/resíduos e programa portátil. Empacotar código/CSV/PDF por ferramentas, sem editar modelos do professor.
4. Reavaliar cronograma: S9(currículo/PII),S10(extração),S11(comparação) do D3 ainda faltam; S4/Cloud e firmware precisam de gates humanos. S12–S15 e jornadaE2E não estão iniciadas. Não declarar todas essas frentes em execução.
5. Sem abrir o holdout, mudar split/densidade/promoção ou retunar com2025. Qualquer nova decisão científica/de produto segue aprovação humana; mínimos acadêmicos nunca são cortados.

## 7. Pendências humanas / restrições

- Revisar as **três** rubricas mantidas; [roteiro do catálogo](<../app/catalogo/README.md>)§4. Seis YAMLs ainda são rascunhos, mínimos/revisor não aprovados.
- Configurar acessos pelo ambiente, nunca enviar segredos ao chat: Atlas/URI/IP; Oracle FIAP; Learner Lab/RDS; opção HF(créditos) ou Comprehend; AWS CLI ou console. Status conhecidos são de12/11, **não revalidados** agora.
- Adzuna: snapshot só após aprovação, teto do projeto12 chamadas/contador — disponibilidade da conta não aumenta esse teto.
- Definir responsáveis pelos vídeos, ideia real da live, Data Modeler e Portal. Formatos/limites no plano§8; PDFs preliminares não equivalem a submissão final.
- Decidir remoto oficial e exposição pública de nomes/RMs/material do professor. Push do dia13 é histórico; **não autoriza novo push**. Autorizações de AWS/credenciais precisam respeitar o escopo vigente.
- Não apagar dados/outbox/schemas/volumes, não ler arquivos de segredos e não chamar APIs pagas sem autorização.

## 8. Decisões locais que continuam válidas

- Limiares de produto só em [limiares.json](<../app/config/limiares.json>); validaçãoHTTP400; OracleDDL19c; domínio em português sem acento.
- CTP: X-Device-Key, estadosOK/ALERTA/ERRO, sentinela exata−127; POST201novo/200idêntico/409conflito. Risco normal/atencao/critico é distinto do estado do firmware.
- As-of: MOV/FOR=max(dec,arquivo);EXC=max(dec,exc,arquivo). Ausência de cobertura não vira zero. Parquets conservam linhas legítimas repetidas; não deduplicar arbitrariamente.
- Ingestão usa56CBOs(34dosdestinos+22reserva), sem atributos sensíveis; CBOs/fontes/curadoria preservados. Para D11 usar snapshot mínimo de mapa em `.kaiser/snapshots/D11_mapa_cbo_seis.json`, sem carregar catálogo completo por padrão.
- Catálogo ESCO é curadoria inferida, não vínculo oficial; versão da ESCO ainda precisa ser fixada. Alegações de títulos CBO por fontes secundárias continuam limitadas.
- Nenhum score único, probabilidade individual de contratação ou competência automaticamente demonstrada por experiência. PII só chega à LLM redigida e após confirmação explícita; sentimento não entra na nota.
