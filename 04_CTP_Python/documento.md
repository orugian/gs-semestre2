# CitizenTech — API REST de leituras do laboratório de monitoramento

**Disciplina:** Computational Thinking with Python · **Global Solution 2026.2**

**Integrantes (nome completo + RM):**
- [HUMANO — preencher]

<div class="quebra-pagina"></div>

## 1. Problema, público beneficiado e contribuição da API

**Problema.** Quem está migrando de carreira para monitoramento industrial e IoT precisa praticar a leitura de sensores e a reação a alarmes, mas laboratório com instrumentação é caro e raro fora dos grandes centros.

**Público beneficiado.** Profissionais graduados e experientes em transição de carreira que usam a plataforma CitizenTech e escolhem a trilha prática do destino "Analista de Monitoramento/IoT Industrial".

**Contribuição da API.** A API recebe as leituras de uma bancada de monitoramento (ESP32 com sensor de temperatura DS18B20 e sensor de distância HC-SR04, ou uma simulação com o mesmo JSON), valida cada leitura, classifica o risco com os mesmos limiares usados pelo firmware e pela nuvem, grava o histórico em CSV e devolve o histórico e indicadores calculados por `GET`. Esse histórico é a base para a pessoa demonstrar, com dados reais da própria sessão, a competência de monitoramento. A mesma API repassa cada leitura para a nuvem (disciplina de Cloud) sem perder dados quando a rede cai.

## 2. Arquitetura e origem dos dados

```
ESP32 (DS18B20 + HC-SR04)  ou  simulação HTTP com o mesmo JSON
        |  POST /leituras  (JSON, cabeçalho X-Device-Key)
        v
API REST FastAPI (Python 3.11)  ── módulo citizentech.leituras
        |-- valida campos e tipos          (esquemas.py)
        |-- classifica o risco             (limiares.py + app/config/limiares.json)
        |-- limita requisições por dispositivo (limitador.py)
        |-- grava no CSV (histórico)       (repositorio.py)
        |-- registra na outbox SQLite      (outbox/banco.py) ──> worker ──> AWS Lambda (Cloud)
        v
GET /leituras              histórico paginado, filtro por sessão
GET /leituras/indicadores  contagem, alertas, média, máximo e mínimo por métrica
```

**Origem dos dados.** As leituras vêm do dispositivo da bancada. Nas evidências deste documento, o dispositivo é **simulado por requisições HTTP** com o JSON exato do firmware (o enunciado aceita). O firmware do ESP32 está em `app/iot/firmware/` e envia o mesmo contrato; ele **ainda não foi executado no Wokwi** contra esta API.

**Modo isolado (para a correção desta disciplina).** A API completa do produto também tem contas, currículo e bancos Oracle e MongoDB. Para CTP existe o aplicativo `citizentech.leituras.isolado`, que sobe **só as rotas de leituras**, sem Oracle, sem MongoDB e sem nuvem. É esse modo que as evidências usam.

## 3. Contrato JSON

**Requisição `POST /leituras`** (cabeçalho obrigatório `X-Device-Key`):

```json
{
  "evento_id": "81499162-b7c3-42fe-97cc-a3a2b6264ae0",
  "dispositivo_id": "esp32-bancada-01",
  "tipo_dispositivo": "esp32",
  "sessao_laboratorio_id": "demo-ctp-bba8a9e3",
  "metrica": "temperatura_c",
  "valor": 25.0,
  "unidade": "C",
  "status": "OK",
  "medido_em": "2026-11-16T19:32:02Z"
}
```

| Campo | Regra |
|---|---|
| `dispositivo_id`, `metrica`, `valor` | **obrigatórios**; ausente → 400 |
| `metrica` | `temperatura_c` ou `distancia_cm` (as métricas de `limiares.json`); outra → 400 |
| `valor` | número (int ou float), finito; texto, booleano, NaN ou infinito → 400; `-127` em `temperatura_c` (código do DS18B20 desconectado) → 400; distância negativa → 400 |
| `unidade` | opcional; se vier, precisa ser `C` ou `cm` conforme a métrica |
| `status` | opcional: `OK` ou `ALERTA`; `ERRO` (falha do sensor) → 400 |
| `evento_id` | opcional; se ausente, a API gera um. Mesmo `evento_id` com o mesmo conteúdo → **200** (reenvio, não duplica); com conteúdo diferente → **409** |
| `medido_em` | opcional, ISO-8601; se ausente, usa o horário de recebimento (UTC) |
| `relato` | opcional, até 280 caracteres |
| corpo | até 8 KB |

**Resposta `201`:**
```json
{"evento_id": "...", "dispositivo_id": "esp32-bancada-01", "metrica": "temperatura_c", "unidade": "C",
 "valor": 25.0, "risco": "normal", "alerta": false, "estado": "pendente_nuvem", "medido_em": "2026-11-16T19:32:02Z"}
```

**Regras de classificação** (`app/config/limiares.json`, fonte única usada pela API, pela Lambda e pelo firmware):

| Métrica | `normal` | `atencao` | `critico` |
|---|---|---|---|
| `temperatura_c` (°C, quanto maior pior) | v < 35 | 35 ≤ v < 45 | v ≥ 45 |
| `distancia_cm` (cm, quanto menor pior) | v > 15 | 8 < v ≤ 15 | 0 ≤ v ≤ 8 |

`alerta = true` quando o risco é `atencao` ou `critico` (é o LED aceso na bancada). Na nuvem, o "alerta ao cidadão" é só o `critico` (buzzer).

**Erros:** sempre no formato `{"erro": "...", "detalhes": "..."}`. 400 validação · 401 chave ausente ou errada · 409 conflito de `evento_id` · 429 limite por dispositivo · 503 falha ao gravar.

## 4. Código Python e instruções de execução

**Onde está o código** (fonte em `app/api/src/citizentech/`; cópia gerada em `04_CTP_Python/codigo/` pelo empacotador da entrega):

| Arquivo | Responsabilidade |
|---|---|
| `leituras/isolado.py` | aplicativo FastAPI do modo isolado |
| `leituras/rotas.py` | endpoints `POST /leituras`, `GET /leituras`, `GET /leituras/indicadores`; leitura do corpo com limite de 8 KB; cálculo dos indicadores |
| `leituras/esquemas.py` | `validar_e_processar_payload`: validação campo a campo e normalização |
| `limiares.py` | `carregar_limiares` e `classificar_risco` (regras da tabela acima) |
| `leituras/repositorio.py` | gravação durável no CSV (trava de arquivo, escrita atômica por linha e `fsync` antes de confirmar) e leitura do histórico |
| `leituras/limitador.py` | limite de leituras por minuto por `dispositivo_id` |
| `leituras/seguranca.py` | conferência da `X-Device-Key` em tempo constante |
| `outbox/` | fila SQLite que repassa cada leitura à nuvem com nova tentativa e idempotência |

**Conceitos de pensamento computacional aplicados:** decomposição (validar → classificar → limitar → gravar → consultar, cada etapa numa função); estruturas condicionais (classificação por faixas, regras de erro); repetição (percurso do histórico para filtrar e calcular indicadores); coleções (`dict` para o registro e para o catálogo de limiares, `list` para o histórico, `set` para os status válidos); modularização (um módulo por responsabilidade) e abstração (os limiares ficam num arquivo de dados, não espalhados no código).

**Como executar** (Windows PowerShell; requer Python 3.11 e [uv](https://docs.astral.sh/uv/)):

```powershell
cd app\api
uv sync
$env:DEVICE_KEY = '<chave da bancada>'                 # obrigatória: sem ela a API recusa tudo
$env:CITIZENTECH_LEITURAS_CSV = "$PWD\leituras.csv"     # onde o histórico será gravado
$env:CITIZENTECH_OUTBOX_DB = "$PWD\outbox.db"
uv run uvicorn citizentech.leituras.isolado:app --port 8001
```

**Alternativa sem o repositório completo** (só a pasta da entrega, com `pip`): a cópia em `04_CTP_Python/codigo/` traz o pacote e o arquivo de limiares, e `04_CTP_Python/requirements.txt` lista as dependências.

```powershell
cd 04_CTP_Python
python -m pip install -r requirements.txt
cd codigo
$env:CITIZENTECH_LIMIARES = "$PWD\config\limiares.json"
$env:DEVICE_KEY = '<chave da bancada>'
$env:CITIZENTECH_LEITURAS_CSV = "$PWD\leituras.csv"
python -m uvicorn citizentech.leituras.isolado:app --port 8001
```

Os arquivos `app.py`, `armazenamento.py`, `processamento.py` e `testes.py` na raiz de `04_CTP_Python/` são o modelo em Flask fornecido no enunciado e **não fazem parte** da solução.

Em outro terminal, com a mesma `DEVICE_KEY` no ambiente:

```powershell
cd app\tools
uv run python demo_leituras_ctp.py --base http://127.0.0.1:8001     # 3 cenários + erros + GET
cd ..\api
uv run pytest tests/test_leituras.py tests/test_leituras_isoladas.py -q
```

Requisição manual: `curl.exe -X POST http://127.0.0.1:8001/leituras -H "Content-Type: application/json" -H "X-Device-Key: <chave>" -d '{"dispositivo_id":"esp32-bancada-01","metrica":"temperatura_c","valor":38}'`.

<div class="quebra-pagina"></div>

## 5. Testes dos endpoints: três cenários e histórico CSV

Execução de 16/11/2026 às 19:32 UTC (16:32 em Brasília), pelo script `app/tools/demo_leituras_ctp.py`, contra a API em modo isolado. Saída completa: `evidencias/20261116_demo_ctp.txt` (**0 falhas**). Os valores dos cenários vêm de `cenarios_demonstracao` em `limiares.json`.

| Cenário | Leitura enviada | HTTP | `risco` | `alerta` |
|---|---|---|---|---|
| 1 · normal | `temperatura_c` = 25,0 | 201 | normal | false |
| 1 · normal | `distancia_cm` = 25,0 | 201 | normal | false |
| 2 · atenção | `temperatura_c` = 38,0 | 201 | atencao | true |
| 2 · atenção | `distancia_cm` = 12,0 | 201 | atencao | true |
| 3 · crítico | `temperatura_c` = 48,0 | 201 | critico | true |
| 3 · crítico | `distancia_cm` = 5,0 | 201 | critico | true |

Casos de borda executados na mesma sessão:

| Caso | HTTP | Resposta |
|---|---|---|
| Reenvio idêntico (mesmo `evento_id`) | 200 | mesmo registro; o CSV não ganhou linha nova |
| Mesmo `evento_id` com `valor` diferente | 409 | "Mesmo evento_id com conteudo divergente." |
| Leitura sem `valor` | 400 | "Campo obrigatorio ausente: 'valor'." |
| DS18B20 desconectado (`-127`) | 400 | "Leitura de sensor invalida (-127 C indica falha de hardware ou sensor desconectado)." |
| Sem `X-Device-Key` | 401 | "Chave de dispositivo ausente ou invalida." |

**Consulta do histórico** `GET /leituras?sessao=demo-ctp-bba8a9e3` → 200 com `total: 6`, as seis leituras na ordem de chegada (o reenvio e as leituras recusadas não entraram).

**Histórico CSV gravado** (`evidencias/20261116_historico_leituras.csv`, cópia do arquivo gerado pela API):

```
evento_id,dispositivo_id,sessao_laboratorio_id,ciclo_id,tipo_dispositivo,metrica,unidade,valor,risco,alerta,estado,medido_em,criado_em
81499162-…,esp32-bancada-01,demo-ctp-bba8a9e3,,esp32,temperatura_c,C,25.0,normal,False,pendente_nuvem,2026-11-16T19:32:02Z,2026-11-16T19:32:02Z
59eb0366-…,esp32-bancada-01,demo-ctp-bba8a9e3,,esp32,distancia_cm,cm,25.0,normal,False,pendente_nuvem,2026-11-16T19:32:02Z,2026-11-16T19:32:02Z
9bc63598-…,esp32-bancada-01,demo-ctp-bba8a9e3,,esp32,temperatura_c,C,38.0,atencao,True,pendente_nuvem,2026-11-16T19:32:02Z,2026-11-16T19:32:02Z
e11b3559-…,esp32-bancada-01,demo-ctp-bba8a9e3,,esp32,distancia_cm,cm,12.0,atencao,True,pendente_nuvem,2026-11-16T19:32:02Z,2026-11-16T19:32:02Z
48425223-…,esp32-bancada-01,demo-ctp-bba8a9e3,,esp32,temperatura_c,C,48.0,critico,True,pendente_nuvem,2026-11-16T19:32:02Z,2026-11-16T19:32:02Z
ebb423a6-…,esp32-bancada-01,demo-ctp-bba8a9e3,,esp32,distancia_cm,cm,5.0,critico,True,pendente_nuvem,2026-11-16T19:32:03Z,2026-11-16T19:32:03Z
```

O `estado = pendente_nuvem` indica que a leitura está na outbox esperando envio à nuvem. No modo isolado não há nuvem configurada, então ela continua pendente; no produto completo o worker a envia à Lambda e o estado passa a `sincronizado`.

**Testes automatizados.** 108 testes de leituras, limiares, outbox e aceite das fatias de leitura passaram em 16/11/2026 (`uv run pytest tests/test_leituras.py tests/test_leituras_isoladas.py tests/test_s2_aceite.py tests/test_s3_aceite.py tests/test_outbox.py tests/test_outbox_integracao.py tests/test_limiares.py -q` → `108 passed`).

## 6. Indicador calculado

`GET /leituras/indicadores?sessao=<id>` calcula, **por métrica**, a contagem de leituras, o total de alertas, a média, o máximo e o mínimo. A média é calculada de forma incremental (`media += (v − media) / i`), o que evita estouro numérico com valores grandes. Resultado real da sessão de demonstração:

| Métrica | Contagem | Alertas | Média | Máximo | Mínimo |
|---|---|---|---|---|---|
| `temperatura_c` | 3 | 2 | 37,0 | 48,0 | 25,0 |
| `distancia_cm` | 3 | 2 | 14,0 | 25,0 | 5,0 |

Conferência manual: (25 + 38 + 48) / 3 = 37,0 °C e (25 + 12 + 5) / 3 = 14,0 cm; os alertas são as leituras de atenção e crítico (2 por métrica). Também é possível filtrar uma métrica: `?metrica=temperatura_c` devolveu o mesmo bloco de temperatura.

## 7. Limitações

- O dispositivo das evidências é **simulado por HTTP**; o firmware do ESP32 ainda não foi executado no Wokwi contra esta API.
- O CSV é adequado para um laboratório com poucos dispositivos; a leitura do histórico percorre o arquivo inteiro a cada `GET`. Para volume maior, um banco de dados.
- O limite de requisições por dispositivo fica em memória do processo: com várias instâncias da API, cada uma conta separado.
- A chave do dispositivo é única para a bancada de demonstração (não há uma chave por dispositivo).
- Os indicadores são descritivos da sessão; não há previsão nem detecção de tendência.

## 8. ODS

**ODS 4 — Educação de qualidade (meta 4.4):** a bancada remota com histórico e indicadores dá prática de monitoramento a adultos em requalificação profissional, que dificilmente teriam acesso a laboratório físico. **ODS 10 — Redução das desigualdades:** a prática não depende de morar perto de um laboratório; basta o simulador ou um ESP32 de baixo custo.
