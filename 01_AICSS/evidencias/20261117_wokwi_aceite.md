# Aceite executado — ESP32 no Wokwi até o CSV

**17/11/2026, 03h33–03h35 (UTC−3). Natureza: simulação efetivamente executada, não bancada física.** Placa do usuário permaneceu intacta. Sem OpenRouter, AWS, Oracle, Mongo ou holdout.

## Comandos e resultados reais

No componente web, `node ..\..\..\.kaiser\ferramentas\validar_wokwi.mjs` (Playwright/Edge, template oficial https://wokwi.com/projects/305457271083631168). Firmware compilado localmente e carregado pelo comando **Upload Firmware and Start Simulation…**, não pelo botão de compilar do site. Texto do editor mostra a fonte efetivamente compilada. Sessão anônima efêmera; nenhum projeto público foi criado/salvo ou compartilhado, nem uma conta autenticada foi usada.

```text
Build demo Wokwi exit=0
Sketch uses 1046385 bytes (79%); Global variables 47188 bytes (14%)
GREEN normal HTTP201, 2 metricas gravadas, risco normal tempo simulado 00:17.249
GREEN atencao HTTP201, 2 metricas gravadas, risco atencao tempo simulado 00:16.633
GREEN critico HTTP201, 2 metricas gravadas, risco critico tempo simulado 00:17.367
WOKWI_COMPLETO 3 cenarios; CSV total 6
```

O ajuste virtual é a entrada do sensor, não um valor injetado no firmware. O DS18B20 foi lido por OneWire/DallasTemperature e o HC-SR04 por TRIG/ECHO/pulseIn. Fontes, limiares e atuadores não foram alterados para aprovar o teste. Foram três inicializações independentes, com sensores pré-configurados e boot/ciclo próprios.

| Cenário | Ajuste °C/cm | Medido pelo firmware °C/cm | Risco recalculado na API | GPIO2 / GPIO15 |
|---|---|---|---|---|
| Normal | 25 / 25 | **25,00 / 25,11** | normal / normal | LED0; buzzer0, sem PWM |
| Atenção | 38 / 12 | **38,00 / 12,07** | atencao / atencao | LED1; buzzer0, sem PWM |
| Crítico | 48 / 5 | **48,00 / 4,96** | critico / critico | LED1; **PWM1.000Hz**, 200 subidas nos últimos200ms |

**GPIO não inferido só da figura:** `node ..\..\..\.kaiser\ferramentas\verificar_gpio_wokwi.mjs` leu os três VCD baixados do analisador lógico do próprio Wokwi, timescale1ns. Normal17,833428s, atenção17,150623s, crítico17,984056s de captura. GPIO2 confirmado0/1/1; GPIO15 sem pulsos nos dois primeiros e frequência mediana1.000Hz no último. O nível final0 de GPIO15 no crítico é uma fase do PWM, não buzzer inativo. Áudio acústico e bancada física não foram medidos.

## Evidências preservadas

- Circuito/Serial originais: [normal](<20261117_wokwi_normal_wokwi.png>), [atenção](<20261117_wokwi_atencao_wokwi.png>), [crítico](<20261117_wokwi_critico_wokwi.png>).
- GET real da API lendo seu CSV: [2 registros](<20261117_wokwi_normal_servidor.png>), [4 registros](<20261117_wokwi_atencao_servidor.png>), [6 registros](<20261117_wokwi_critico_servidor.png>).
- Serial: [normal](<20261117_wokwi_normal_serial.txt>), [atenção](<20261117_wokwi_atencao_serial.txt>), [crítico](<20261117_wokwi_critico_serial.txt>).
- Capturas GPIO brutas: [normal](<20261117_wokwi_normal.vcd>), [atenção](<20261117_wokwi_atencao.vcd>), [crítico](<20261117_wokwi_critico.vcd>); [verificação numérica](<20261117_wokwi_gpio.json>).
- [CSV original com6linhas](<20261117_wokwi_leituras.csv>), [JSON do histórico consultado](<20261117_wokwi_historico_api.json>) e [IDs por cenário](<20261117_wokwi_resumo.json>). O JSON é resposta real de GET/persistência, **não** transcrição inventada do corpo de POST capturado na rede.
- Diagramas usados, com analisador adicional passivo nos GPIO2/15/4/18: [normal](<20261117_wokwi_normal_diagram.json>), [atenção](<20261117_wokwi_atencao_diagram.json>), [crítico](<20261117_wokwi_critico_diagram.json>). Não alteram regras nem os sensores do circuito original.

Todas as seis imagens foram inspecionadas: não há conta pessoal, senha, token ou chave real, portanto **nenhuma tarja artificial foi necessária**. Vinte e dois arquivos foram copiados (não movidos) para evidências versionáveis e para `.dados/iot/privado/20261117_wokwi`; SHA comparado entre origem e cópias. CSV também preservado. Os originais Cloud anteriores não foram alterados.

## Transporte, RED e limites

1. API exclusiva do ensaio: `citizentech.leituras.isolado:app`, base vazia, chave pública **de exemplo** e dados sintéticos. GET autenticado200; GET/POST sem chave401. Nenhuma credencial real do app foi compilada, enviada ou carregada nessa API.
2. Ngrok respondeu200 ao host, mas no Wokwi os POST retornaram **-1**, sem atingir a API; teste de CSV falhou por asserção. PCAP real mostrou DNS respondido e TCP aberto, encerramento TLS pelo servidor antes de a troca de chaves terminar. `cpuFrequency=max` também falhou: hipótese de frequência como solução **rejeitada**; não alteramos o diagrama do projeto.
3. Contraste de destino: túnel HTTPS anônimo Cloudflare, cliente portátil2026.11.0, SHA oficial `d5c1d82031da6253dcdcff64c944cd0fe063016edeb2e4fd088075fc9bd52d0a`. Mesma lógica/bibliotecas/CPU padrão, só API_URL de demonstração diferente: **seis201 e seis registros**. Causa precisa da política/timeout TLS do ngrok não foi medida no servidor; não alegamos tê-la provado. Não houve rebaixamento para HTTP público nem enfraquecimento dos critérios.
4. Gateway público Wokwi monitora tráfego, conforme [documentação](https://docs.wokwi.com/guides/esp32-wifi). Por isso somente chave fictícia, leituras virtuais e API isolada foram usados. O protótipo não valida CA/pinning do servidor no overload TLS atual de HTTPClient; HTTPS observado **não certifica segurança de produção**. Demonstração com chave real deve seguir o projeto privado/rotação/escopo de D24, não copiar a configuração deste ensaio.
5. API gravou os eventos como `pendente_nuvem`: modo isolado **não executa worker de outbox**. Não houve Wokwi→Lambda/RDS nesta execução. As demonstrações AWS anteriores vieram de simulador por software; não misturar evidências.
6. Todos os túneis foram encerrados (o primeiro ngrok por timer15min, o segundo e Cloudflare deliberadamente antes do limite). API própria também encerrada; portas8000/4040/20241 sem listeners na checagem final. Serviços e worktrees da outra frente foram preservados.

Fonte do projeto/firmware e hashes dos artefatos estão no manifesto desta execução. Reprodução: seguir o README do firmware, iniciar nova API isolada e novo túnel temporário; URLs antigas não são permanentes nem evidência de serviço ao vivo.
