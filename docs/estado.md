# Estado do desenvolvimento — CitizenTech

> **Fechamento técnico em 17/11/2026, após 18h (UTC−3).** Prazo: **19/11/2026 às 23h55**. Este estado e o [handoff](<handoff_citizentech_20261116_fim.md>) prevalecem sobre checkpoints anteriores; o Git mantém o histórico.

## 000. Tarde de 17/11 — redesign NOUS e reorganização (pedido do usuário)

Pedido: UI moderna no DS NOUS + matriz de pixels three.js, foco visível (aprovado), higiene/organização do repositório (untangle em web/tools/cloud-testes/api; `app/ml` congelado). Vídeos ficam para o fim, com tudo revisado. Decisões e motivos em [decisoes_untangle.md](<decisoes_untangle.md>).

- **Fechamento de QA (`8dbe4f7`):** `powershell -NoProfile -File app\tools\testar_tudo.ps1 -SemML` retornou 0 em API, Cloud, tools, typecheck, Vitest (68) e build. Os 17 testes do preparo local passaram em PowerShell, incluindo falta de instalação e recusa de banco externo. No checkout integrado, `pnpm exec playwright test` com a API local isolada → 6 passaram, 1 skip (persona não configurada); axe não reportou violações nas 11 telas e no modal exercitados. `empacotar_entregas.py --verificar` OK, SHA-256 dos **53 destinos** igual ao manifesto; nenhum relatório-fonte PDF mudou neste fechamento. O guia para schema vazio foi conferido em modo de listagem (DDL 001–007); não foi realizada uma instalação do zero em outro computador. A revisão de documentação terminou; a varredura estrutural final adicional foi interrompida sem parecer, não é certificação de ausência de dívida técnica. Worktrees de entrega removidos; S5 preservada. Próximo passo: vídeos reais e, depois dos links conferidos, Portal.
- **Marcos anteriores da integração:**
  - `2282afb` README de replicação na raiz, `app/tools/ambiente_teste.ps1` + `testar_tudo.ps1`, `.env.example` completo, empacotador cobrindo os 6 PDFs, requirements ML/RNA do `uv.lock`, docs históricos em `docs/historico`/`docs/panorama`.
  - **S16 (`48be785`)** redesign NOUS: RED `foco_visivel` reproduzido em main (Selector Destino/E-mail sem indicador) → GREEN; vitest 65, build (three.js em chunk separado 528 kB), playwright 5+1 skip persona, axe 0 serious/critical em 11 telas + modal. O orquestrador corrigiu a matriz (câmera/culling: não renderizava), fez pixels quadrados e reverteu mudanças de comportamento não contratadas em `TelaComparacao`.
  - **S17 (`fde8f6e`)** untangle API/tools: contratos de erro (11 testes) iguais antes/depois; api 408, tools 47, cloud 118. agy estourou 60 min; orquestrador corrigiu `NameError` real em `executar_consultas_oracle.py` (pego pelo ruff), concluiu `_comum`/demos/conftest DDL 001–007/teste de hash com a Lambda (Lambda intacta) e reexecutou as demos (proteções 16/16, CTP e firmware falhas=0).
  - `f82301d` cópia CTP autocontida (gancho de relato), entregas regeneradas, `--verificar` OK; cópia entregue rodada isolada com o `requirements.txt` → demo CTP falhas=0.
- **S18 integrada** (`a14ebef`), incluindo cliente HTTP comum, rótulos, listas e estado do plano; `d8700ab` corrigiu o corte da linha da MLP no painel. Na integração: 68 Vitest, 6 E2E passaram e 1 caso da persona foi pulado. Não repetir S15 para obter nova evidência do mesmo aceite.
- **Revalidação no HEAD `d8700ab`:** `typecheck`, 68 Vitest e build OK; os 3 casos de foco e tabela passaram em Edge contra uma API recém-iniciada nesse HEAD, runtime separado e sem nuvem. No build, a 390 px, o canvas de 33×12 mudou nas duas comparações de quadros com movimento normal e em nenhuma com `prefers-reduced-motion: reduce`; sem overflow horizontal na tela Entrar. O aviso de tamanho de chunks no build continua. Esse teste não envolveu uma pessoa usando leitor de tela.
- Não feito por decisão: `app/cloud/src` (Lambda implantada) intocado; polling do laboratório sem backoff e aviso de sessão expirada ficam como estão.

## 00. Sessão de 17/11 manhã — Cloud e Data Modeler concluídos

- **Lab:** `GET /health` 200 `banco=ok` às 13:03:31Z (verificado). Rodada nova 13:09:57–13:12:43Z: simulador normal (ids 12–13) e evolução 30→50 °C (ids 14–19, 46/50 crítico `alerta=True`); sem `metrica` → 400; chave inválida → 401. SELECT no RDS (app_ingest, verify-full) → 17 linhas de `lab-iot-bancada-01`. Nenhum recurso AWS alterado. [Registro](<../06_Cloud/evidencias/20261117_rodada_function_url.txt>).
- **Prints Cloud — as 4 categorias cobertas:** SIM `20261117_simulador_function_url.png` e DB `20261117_negativos_e_rds_ocorrencias.png` capturados pelo agente (janela do console via PrintWindow, sem segredo visível); CW-C/CW-D/CW-K fornecidos pelo usuário às 09h56–09h58, **são da rodada de 16/11 (18:38Z)**, renomeados `20261116_cloudwatch_{critico,descarte,chave_invalida}.png`, e-mail tarjado; originais copiados (SHA igual) para `.dados/cloud/privado` e excluídos do Git via `.git/info/exclude`. **Logs CloudWatch da rodada de 17/11 não têm imagem** (opcional).
- **Data Modeler executado pelo agente (D25/CLAUDE §12):** SQL Developer Data Modeler 24.3.1.351.0831 oficial (zip SHA-256 conferido com a página da Oracle), portátil em `../.kaiser/toolchains/datamodeler` (~0,9 GB, sem PATH/serviço, perfil isolado `userdir`). Automação da GUI por pyautogui + PrintWindow. Import do `oracle.sql`: 32 instruções, 23 importadas, **0 falhas**, 9 não reconhecidas (= os 9 SELECT C1–C9). Relacional **16 tabelas/15 FKs** (nomes idênticos ao DDL); lógico por *Engineer to Logical Model*: **16 entidades/15 relações**. Site usado: Oracle 21c (o 24.3 não lista 19c). Projeto `.dmd`, PDF/PNG/SVG de ambos os diagramas, log e 3 telas em [`03_DataScience/evidencias/20261117_datamodeler/`](<../03_DataScience/evidencias/20261117_datamodeler/>). Relatório DS §2/§6 atualizado; PDF **9p**, RMs ok.
- **QA:** folhas de contato de todos os PDFs inspecionadas (AICSS10, Cyber12, DS9, CTP8, ML12, Est21; nenhuma página vazia). CTP §2/§7 dizia "Wokwi ainda não executado" — corrigido com o aceite Wokwi (sem dizer Wokwi→AWS); PDF CTP 8p. Teclado/foco: [QA](<../02_Cybersecurity/evidencias/20261117_qa_teclado_foco.md>) — fluxo por teclado ok; achado de foco pouco visível nos seletores de Mercado e nos campos de login (WCAG 2.4.7) — **corrigido à tarde na S16, com aprovação do usuário** (ver §000).
- **Regressão:** tools **43 passed**; cloud **115 passed** ×4 com `PG_TESTE_*` em memória (sem elas, 33 skips/3 erros de ambiente); 1 falha intermitente observada 2× em `test_simulador.py` (ConnectionAbortedError WinError 10053 no servidor HTTP local do teste), não reproduzida em 10 rodadas seguintes — *flaky* de ambiente, não alterado. Empacotador `--verificar` **OK**. API/ML/web não rerodados (sem mudança de código).
- **Vídeos/links:** nenhum recebido; os 5 `video.md` seguem com `[HUMANO — preencher]`.

## 0. Fechamento funcional aceito; pendente o fechamento acadêmico (registro de 17/11 08h51)

**Nova orientação do usuário em17/11, após o encerramento:** **Data Modeler é tarefa do AGENTE**, não do grupo; D25/CLAUDE§12 e handoff foram atualizados. O usuário informou **Learner Lab reativado para a próxima sessão**; isso ainda não foi confirmado por novo health. Próximo agente: iniciar validação Cloud e execução agêntica do Modeler, sem pedir ao usuário que faça a modelagem. [Capturas exatas que faltam](<historico/guia_capturas_learner_lab.md>).

**Verificação desta atualização documental:** guia de capturas confrontado com enunciado/logs/schema do projeto; PDF Data Science regenerado, **7p**, três RMs conferidos; empacotador **--verificar OK**. Data Modeler continua pendente de execução e nenhuma nova chamada AWS foi feita agora.

**Wokwi efetivamente executado pelo agente:**3cenários,6HTTP201,6linhas CSV, LED0/1/1 e PWM**1.000Hz** só no crítico. [Aceite com prints/Serial/VCD/limites](<../01_AICSS/evidencias/20261117_wokwi_aceite.md>), [CSV original](<../01_AICSS/evidencias/20261117_wokwi_leituras.csv>), [manifesto/hashes](<../01_AICSS/evidencias/20261117_wokwi_manifesto.json>). **Sensores/atuadores simulados**, não bancada física. A placa ESP sem sensores do usuário permaneceu intacta, sem reflash.

- Ajustes25°C/25cm,38°C/12cm,48°C/5cm; medições reais da simulação **25,00/25,11**, **38,00/12,07**, **48,00/4,96**. Valores não injetados no firmware: OneWire/DallasTemperature e TRIG/ECHO/pulseIn realmente executados.
- Edge/Playwright sobre template oficial, carregando o binário local pelo comando **Upload Firmware and Start Simulation…**. Sessão efêmera anônima, sem salvar/publicar projeto ou usar conta pessoal. Token de CI não foi necessário; não presumir que está disponível.
- API exclusiva `citizentech.leituras.isolado:app`, dados novos, chave **pública de exemplo**, nenhum segredo real. GET autenticado200; GET/POST sem chave401. Worker da nuvem desligado: os6eventos ficaram **pendente_nuvem**, portanto **não é Wokwi→Lambda/RDS**.
- Ngrok apresentou falha TLS (-1), com DNS/TCP funcionando no PCAP; CPUmax também falhou. Critérios não enfraquecidos. Cloudflare Quick Tunnel HTTPS/CPU padrão passou os mesmos testes, mudando só o destino de demo. Causa exata do encerramento no servidor ngrok **não verificada**, hipótese de CPU como solução rejeitada. Nenhuma mudança em regras, firmware, limiares ou diagrama do produto nesta etapa.
- GPIO extraído de VCD real do analisador passivo nos pinos2/15/4/18: normal LED0/buzzer0; atenção LED1/buzzer0; crítico LED1,200 subidas em200ms, mediana1.000Hz. Nenhuma gravação acústica.
- Seis PNG inspecionados, sem dados pessoais/conta/token/chave real: **nenhuma tarja necessária**. Vinte e dois originais de dados/imagens copiados, não movidos, também para .dados/iot/privado/20261117_wokwi, comparados por SHA. Originais Cloud anteriores intocados.
- Túneis próprios ngrok/Cloudflare e API do ensaio **encerrados**. Nova checagem08h51: portas8000/8001/5173/4040/20241 sem listener; C:**16,3GB** livres. Às09h05 foi confirmado o agy30832 da outra frente, iniciado16/11 09h23, preservado. Não relançar para “manter demo viva”; só abrir novo serviço/túnel quando necessário ao trabalho autorizado.

**Documentos/pacote:** AICSS§5.2 e limites atualizados com os três prints; PDF**10p**. Firmware README e projeto/Cloud distinguem Wokwi→CSV da execução AWS anterior. Revisão nº2 adjudicada e RC2-04 fechado com prova. Empacotador gerar+`--verificar` **OK**; tools**43passed** após a atualização. PDFs:10/12/7/8/12/21p; três RMs em todos, Cyber≤15. Parser confirmou três imagens2200×1400 no PDF AICSS (p7/7/8) e as medidas no texto.

**Publicação funcional confirmada:** `f96b13e` em main e gs-semestre2/main, working tree limpa e zero commits não enviados antes deste encerramento documental. Histórico: S15 `e7c533a`, docs/revisão2 `f10ffd2`, boot Wokwi `409e975`. O upstream origin/main continua antigo: não resetar/rebasear nem publicar nesse remoto por confusão. Gitleaks staged/intervalo antes de cada commit/push; somente gs-semestre2.

**Próximo passo exato:** seguir P01–P08 do [handoff](<handoff_citizentech_20261116_fim.md>). Agente faz inventário, **Data Modeler** e QA final; conduz testes Cloud e orienta as capturas autenticadas, enquanto o grupo prepara vídeos/live em paralelo. Incorpora apenas arquivos realmente obtidos, copia originais privados antes de tarjar e repete PDFs/empacotador. Não é necessário esperar parado pelos humanos, nem repetir S15/Wokwi. Não substituir captura AWS por saída histórica/local e não declarar entrega acadêmica concluída antes do Portal.

## 1. Evidências já aceitas nesta retomada

| Verificação | Resultado executado |
|---|---|
| S15-e2e | Commit `c965692`, merge --no-ff `e7c533a`, main regredido e push; [aceite detalhado](<../02_Cybersecurity/evidencias/20261116_s15_e2e_aceite.md>) |
| Playwright em main / API teste recém-iniciada | **3passed,1skipped**; skip é só persona sem env de app nesse ambiente (pwsh-123) |
| Persona separada contra API app `-App -ComLLM` | **1passed** (pwsh-109); credenciais só em memória, nenhuma alteração da persona/chamada LLM; prints após desmontar login |
| Acessibilidade | **11telas+modal**, zero violações axe nas severidades medidas; nome de diálogo também por asserção, sem alegar certificação WCAG completa |
| Web Vitest/tipos/build | **61passed**, até6workers; typecheck/build OK; bundle918,48kB mantém warning>500kB |
| Tools | **43passed**, incluindo9testes host de firmware; repetido após Wokwi no pwsh-194 |
| Compilação inicial ESP32 | CLI1.6.0/core3.0.7/OneWire2.3.8/Dallas4.0.6,2jobs, exit0; programa1.046.369bytes/79%, RAM47.188/14% (pwsh-131) |
| Build da demo Wokwi | Mesmas fontes/bibliotecas, header só de exemplo/URL;1.046.385bytes/79%, mesma RAM; fonte comparada por SHA ao repo |
| Wokwi completo | **3GREEN,6HTTP201,6CSV** no pwsh-189; GPIO verificado separadamente pelo parser VCD, exit0 |
| PDFs finais | **AICSS10, Cyber12, DS7, CTP8, ML12, Estatística21**; três RMs e imagens AICSS conferidos com parser |
| Notebooks | Só capa Markdown alterada; código/outputs/metadados restantes iguais ao HEAD anterior; sem outputs de erro armazenados. **Não reexecutados** |
| Lambda health | Inicialmente502; pós-reinício humano do Lab: **HTTP200/status=ok/banco=ok** (pwsh-136), [evidência](<../06_Cloud/evidencias/20261116_health_retomada.txt>) |
| Revisão nº2 | Nova chamada agy plan20min, exit0 em16/11 22h51; [adjudicação atualizada](<revisao_conformidade_2.md>) |

REDs web reais reproduzidos antes das correções: aria-controls inválido, Discordo sem nome e warning setState; Substituir plano também falhou por nome. Corrigidos, regressão executada, nenhum teste enfraquecido. Compilação ESP32 inicial revelou assinatura mutável HTTPClient::POST; fix mínimo preservou bytes/reenvio. Warnings OneWire mantidos.

## 2. Ambiente e higiene

- **Sem job próprio útil em andamento.** Ensaios e browsers terminaram. API Wokwi wrapper2888/servidor20584; ngrok29628/14548; Cloudflare35500 foram encerrados. Primeiro túnel por timer15min, demais deliberadamente antes do limite. Jobs170/175/178/180/187/189/194 coletados; falhas diagnósticas preservadas, não interpretadas como GREEN.
- Worktrees **S5-auth b94b0de/S5-red112042d** permanecem preservados. **Agy30832 confirmado ativo às09h05**, iniciado16/11 09h23, pertence à outra frente: não encerrar nem interferir. Sempre reidentificar processos numa sessão nova, nunca matar só pelo PID de um handoff. Docker Oracle/Mongo/Postgres **saudáveis** na checagem de encerramento, compartilhados e mantidos; nenhum volume apagado. S15 worktree/branch já removidos após merge e limpeza específica autorizada.
- Último disco medido: **16,3GB**. Arduino portátil isolado4,76GB em ../.kaiser/toolchains/citizentech-esp32, sem PATH global/serviço. Cloudflared portátil2026.11.0 ocupa55,4MB nessa mesma raiz de ferramentas; digest oficial conferido, sem login/autoupdate/serviço instalado. Remoção após o projeto exige confirmação, sem tocar dados.
- Trilha fora do Git em ../.kaiser/ferramentas/ (validar_wokwi.mjs, verificar_gpio_wokwi.mjs, compilar_wokwi_demo.ps1, lançadores de API/túneis); diagnósticos em ../.kaiser/tmp/wokwi e reports/wokwi_20261117_red. Retidos para auditoria/reprodução; não limpar tmp global com outra frente ativa, nem apagar originais/evidências para “higiene”.
- **Oracle:** localhost20,129s vs127.0.0.1 em0,114s. IPv6 é hipótese não instrumentada. env_teste/env_app normalizam somente em memória, sem alterar app/.env; evitou timeout de cadastro sem relaxar asserção.
- Segredos de app só em memória a partir de app/.env; não impressos ou copiados para agentes/worktrees. Persona só quando teste exige. Wokwi usou exclusivamente placeholder público e dados sintéticos.
- Última consulta OpenRouter: **US$0,02153822 de US$7**, em etapa anterior; não é leitura ao vivo da conta. Wokwi e o encerramento não o chamaram. Adzuna não chamada nesta retomada, contador histórico7/12. Comprehend AccessDenied e HF402 permanecem limitações, sem sentimento válido medido.
- Três originais Cloud anteriores continuam ignorados, com cópias privadas iguais por SHA em .dados/cloud/privado; versões tarjadas rastreadas. Nenhuma nova captura humana Cloud. Caged bruto sem .7z na última checagem; parquets/snapshots/modelos preservados.

## 3. Produto e ciência protegidos

S0–S15 integradas: mercado/painel técnico, autenticação/consentimentos, currículo redigido e confirmado, competências, intenção/comparação, plano determinístico, exercício50/50 com parcial/refazer/discordo e laboratório/outbox. API397/Cloud115/ML274 são resultados de sessões anteriores, **não rerodados nesta retomada**.

Holdout2026 **fechado**, status_promocao=nao_decidida, nenhum modelo promovido; não retunar2025. MVP3destinos R29; rubricas6destinos aprovadas, limiares só em app/config/limiares.json. Validação HTTP400, Oracle dialeto19c. CV à LLM só redigido e confirmado; sentimento nunca entra na nota. Não reabrir fatias integradas nem S5 da outra frente.

## 4. Pendências humanas e limites reais

Fila, responsáveis e critérios detalhados no [handoff P01–P08](<handoff_citizentech_20261116_fim.md>). As tarefas abaixo **não estão concluídas**.

1. **Cloud:** imagens das 4 categorias **concluídas em 17/11** (ver §00). Falta só o vídeo ≤5 min (humano). Não alterar recursos; typo RATE_KIMIT e default 30 já documentados.
2. **Data Modeler:** **concluído pelo agente em 17/11** (ver §00). Oracle FIAP continua fora do escopo.
3. **Vídeos/URLs:** AIC≤7min com rosto/sem música/YouTube não listado e nomes/RMs (obrigatório para pontuar); ML/Cyber/Cloud≤5min; RNA obrigatório. Ideias efetivas da live e relato de gestão também humanos.
4. Identidades confirmadas e aplicadas: Guilherme Orugian RM572882; Lucas Henrique RM571901; Rodrigo Bettio RM573725. Placeholders em URLs de vídeos permanecem até receber links reais.
5. Conferência e **Portal**: Estatística PDF+PY+CSV separados, sem ZIP; Cyber≤15p. Nenhuma submissão realizada. Texto de operador/transferência internacional em consentimentos, backup/restauração não verificados, proteção de sensor único, buffer offline do ESP e TLS/CA de produção permanecem limitações; não implementar correções fora do escopo sem decisão.

### 4.1 Verificações que o próximo agente ainda deve conduzir

- [x] Inventariar arquivos humanos novos (17/11: 3 prints CloudWatch; nenhum vídeo/link).
- [x] Revalidar health do Lab (200 às 13:03Z).
- [x] Executar Data Modeler pelo agente e incorporar ao relatório/PDF.
- [x] Revisar visualmente PDFs por folha de contato (resolução baixa; legibilidade fina de tabelas não conferida página a página). [ ] Testar links reais quando fornecidos.
- [x] QA de teclado/foco parcial (4 telas); correção aprovada e integrada na S16; regressão de Mercado/login verde.
- [x] Procedência das cópias finais de ML/RNA conferida **sem executar células**: SHA-256 igual ao da respectiva fonte, 15/15 e 7/7 células de código com contador, 16 e 9 saídas salvas, nenhuma saída de erro. Última alteração das cópias: `f10ffd2`. Não é uma reexecução científica em máquina limpa.
- [ ] Após incorporar materiais, regenerar cópias/PDFs, executar empacotador --verificar, regressão pertinente e gitleaks; publicar apenas mudanças intencionais.

**Preparação da próxima gravação:** roteiros atualizados em 17/11 à tarde. AIC usa `-App` (persona existente) e **sem `-ComLLM`** por padrão; chamada paga só com autorização reconfirmada. ML e RNA seguem o README (API local + snapshot de Mercado, sem login). O modo sem `-App` usa o schema de teste e não a persona existente. Não liberar a outbox antiga. Bancada física, áudio acústico e Wokwi→AWS seguem não verificados, não são compras/implementações automaticamente autorizadas.
