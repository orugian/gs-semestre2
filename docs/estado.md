# Estado do desenvolvimento — CitizenTech

> **Checkpoint17/11/2026, madrugada.** Prazo19/11/2026 às23h55. Não é monitoramento ao vivo. Este estado e o [handoff](<handoff_citizentech_20261116_fim.md>) prevalecem sobre os checkpoints anteriores; o Git mantém o histórico.

## 0. Retomada concluída; próximo passo depende das entregas humanas

**Wokwi efetivamente executado pelo agente:**3cenários,6HTTP201,6linhas CSV, LED0/1/1 e PWM**1.000Hz** só no crítico. [Aceite com prints/Serial/VCD/limites](<../01_AICSS/evidencias/20261117_wokwi_aceite.md>), [CSV original](<../01_AICSS/evidencias/20261117_wokwi_leituras.csv>), [manifesto/hashes](<../01_AICSS/evidencias/20261117_wokwi_manifesto.json>). **Sensores/atuadores simulados**, não bancada física. A placa ESP sem sensores do usuário permaneceu intacta, sem reflash.

- Ajustes25°C/25cm,38°C/12cm,48°C/5cm; medições reais da simulação **25,00/25,11**, **38,00/12,07**, **48,00/4,96**. Valores não injetados no firmware: OneWire/DallasTemperature e TRIG/ECHO/pulseIn realmente executados.
- Edge/Playwright sobre template oficial, carregando o binário local pelo comando **Upload Firmware and Start Simulation…**. Sessão efêmera anônima, sem salvar/publicar projeto ou usar conta pessoal. Token de CI não foi necessário; não presumir que está disponível.
- API exclusiva `citizentech.leituras.isolado:app`, dados novos, chave **pública de exemplo**, nenhum segredo real. GET autenticado200; GET/POST sem chave401. Worker da nuvem desligado: os6eventos ficaram **pendente_nuvem**, portanto **não é Wokwi→Lambda/RDS**.
- Ngrok apresentou falha TLS (-1), com DNS/TCP funcionando no PCAP; CPUmax também falhou. Critérios não enfraquecidos. Cloudflare Quick Tunnel HTTPS/CPU padrão passou os mesmos testes, mudando só o destino de demo. Causa exata do encerramento no servidor ngrok **não verificada**, hipótese de CPU como solução rejeitada. Nenhuma mudança em regras, firmware, limiares ou diagrama do produto nesta etapa.
- GPIO extraído de VCD real do analisador passivo nos pinos2/15/4/18: normal LED0/buzzer0; atenção LED1/buzzer0; crítico LED1,200 subidas em200ms, mediana1.000Hz. Nenhuma gravação acústica.
- Seis PNG inspecionados, sem dados pessoais/conta/token/chave real: **nenhuma tarja necessária**. Vinte e dois originais de dados/imagens copiados, não movidos, também para .dados/iot/privado/20261117_wokwi, comparados por SHA. Originais Cloud anteriores intocados.
- Túneis próprios ngrok/Cloudflare e API do ensaio **encerrados**. Última checagem03h42: portas8000/4040/20241 sem listener, C:**17,1GB** livres. Não relançar para “manter demo viva”; só abrir novo túnel temporário com escopo isolado.

**Documentos/pacote:** AICSS§5.2 e limites atualizados com os três prints; PDF**10p**. Firmware README e projeto/Cloud distinguem Wokwi→CSV da execução AWS anterior. Revisão nº2 adjudicada e RC2-04 fechado com prova. Empacotador gerar+`--verificar` **OK**; tools**43passed** após a atualização. PDFs:10/12/7/8/12/21p; três RMs em todos, Cyber≤15. Parser confirmou três imagens2200×1400 no PDF AICSS (p7/7/8) e as medidas no texto.

**Publicação:** S15 em `e7c533a`; docs/compilação/revisão2 em `f10ffd2`; boot Wokwi em `409e975`, todos publicados em gs-semestre2. O lote final de Wokwi/documentos está no commit que contém este estado; confirmar hash/remote pelo Git, sem repetir o aceite. Gitleaks staged e do intervalo são obrigatórios antes de commit/push; somente remoto gs-semestre2.

**Próximo passo exato:** grupo produzir os artefatos do §4 (Cloud/Data Modeler/vídeos/live); então o agente confere arquivos realmente fornecidos, preserva originais por cópia privada, redige dados pessoais, atualiza documentos/PDFs, repete empacotador --verificar e publica. Não substituir captura Cloud por PNG de terminal local nem por este Wokwi isolado. Não declarar entrega acadêmica concluída antes desses gates e do Portal.

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
- Worktrees **S5-auth b94b0de/S5-red112042d** e `agy` PID30832 de outra frente foram preservados. Docker compartilhado não foi derrubado nem volumes apagados. S15 worktree/branch removidos após merge; resíduo Windows só removido com aprovação específica e hashes conferidos.
- Último disco medido: **17,1GB**. Arduino portátil isolado4,76GB em ../.kaiser/toolchains/citizentech-esp32, sem PATH global/serviço. Cloudflared portátil2026.11.0 ocupa55,4MB nessa mesma raiz de ferramentas; digest oficial conferido, sem login/autoupdate/serviço instalado. Remoção após o projeto exige confirmação, sem tocar dados.
- Trilha fora do Git em ../.kaiser/ferramentas/ (validar_wokwi.mjs, verificar_gpio_wokwi.mjs, compilar_wokwi_demo.ps1, lançadores de API/túneis); diagnósticos em ../.kaiser/tmp/wokwi e reports/wokwi_20261117_red. Retidos para auditoria/reprodução; não limpar tmp global com outra frente ativa, nem apagar originais/evidências para “higiene”.
- **Oracle:** localhost20,129s vs127.0.0.1 em0,114s. IPv6 é hipótese não instrumentada. env_teste/env_app normalizam somente em memória, sem alterar app/.env; evitou timeout de cadastro sem relaxar asserção.
- Segredos de app só em memória a partir de app/.env; não imprimidos/copied para agentes/worktrees. Persona só quando teste exige. Wokwi usou exclusivamente placeholder público e dados sintéticos.
- OpenRouter nesta sessão: **US$0,02153822 de US$7**; Wokwi não o chamou. Adzuna não chamada nesta retomada, contador histórico7/12. Comprehend AccessDenied e HF402 permanecem limitações, sem sentimento válido medido.
- Três originais Cloud anteriores continuam ignorados, com cópias privadas iguais por SHA em .dados/cloud/privado; versões tarjadas rastreadas. Nenhuma nova captura humana Cloud. Caged bruto sem .7z na última checagem; parquets/snapshots/modelos preservados.

## 3. Produto e ciência protegidos

S0–S15 integradas: mercado/painel técnico, autenticação/consentimentos, currículo redigido e confirmado, competências, intenção/comparação, plano determinístico, exercício50/50 com parcial/refazer/discordo e laboratório/outbox. API397/Cloud115/ML274 são resultados de sessões anteriores, **não rerodados nesta retomada**.

Holdout2026 **fechado**, status_promocao=nao_decidida, nenhum modelo promovido; não retunar2025. MVP3destinos R29; rubricas6destinos aprovadas, limiares só em app/config/limiares.json. Validação HTTP400, Oracle dialeto19c. CV à LLM só redigido e confirmado; sentimento nunca entra na nota. Não reabrir fatias integradas nem S5 da outra frente.

## 4. Pendências humanas e limites reais

1. **Cloud:** capturas do simulador e consulta RDS; refazer CloudWatch de descarte/chave inválida/alerta; vídeo≤5min. Não alterar AWS por sugestão de revisor; typo RATE_KIMIT documentado e default30. Health verificado não garante Lab continuamente disponível.
2. **Data Modeler:** modelos lógico/relacional e exportações pelo grupo. Oracle FIAP fora do escopo por decisão anterior; não alegar execução nele nem chamar Mermaid de Data Modeler.
3. **Vídeos/URLs:** AIC≤7min com rosto/sem música/YouTube não listado e nomes/RMs (obrigatório para pontuar); ML/Cyber/Cloud≤5min; RNA obrigatório. Ideias efetivas da live e relato de gestão também humanos.
4. Identidades confirmadas e aplicadas: Guilherme Orugian RM572882; Lucas Henrique RM571901; Rodrigo Bettio RM573725. Placeholders em URLs de vídeos permanecem até receber links reais.
5. Conferência e **Portal**: Estatística PDF+PY+CSV separados, sem ZIP; Cyber≤15p. Nenhuma submissão realizada. Texto de operador/transferência internacional em consentimentos, proteção de sensor único, buffer offline do ESP e TLS/CA de produção permanecem limitações, não foram escondidos.
