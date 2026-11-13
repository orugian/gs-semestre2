# CitizenTech API — Telemetria CTP e Modo Isolado (S2)

Módulo de recepção, validação, classificação e persistência de telemetria didática de monitoramento IoT (sensores de temperatura e distância/nível), operando de forma autônoma sem dependência de bancos de dados relacionais ou documentais.

---

## 1. Execução em Modo Isolado CTP

O modo isolado permite executar a API sem Oracle, sem MongoDB e sem acesso a rede externa, utilizando armazenamento durável em arquivo CSV com locking de arquivo (`portalocker`) e sincronização física em disco (`fsync`):

```powershell
# No diretorio app/api
uv run uvicorn citizentech.leituras.isolado:app --port 8000
```

> **Aviso de concorrência e processo:** Esta fase foi projetada para execução com um único processo worker do Uvicorn (`--workers 1`), assegurando consistência na escrita do CSV com lock de filesystem/memória e sincronização física em disco (`fsync`). O lock previne condições de corrida entre threads e processos no mesmo arquivo.

---

## 2. Variáveis de Ambiente

Configure as variáveis de ambiente necessárias (nomes sem segredos ou credenciais reais):

- `DEVICE_KEY`: Chave secreta exclusiva do dispositivo IoT (demo). Obrigatória; a API opera em modo *fail-closed* (sem chave configurada ou com chave incorreta, retorna HTTP 401). A validação usa comparação resistente a timing (`secrets.compare_digest`).
- `CITIZENTECH_DADOS`: Caminho raiz para armazenamento de dados fora do repositório git. O arquivo CSV de runtime será salvo em `$env:CITIZENTECH_DADOS\runtime\leituras.csv`.
- `CITIZENTECH_LEITURAS_CSV` *(opcional)*: Caminho direto e explícito para o arquivo CSV de telemetria (utilizado primordialmente em testes automatizados).
- `CITIZENTECH_RATE_LIMIT_POR_MINUTO` *(opcional)*: Teto de requisições permitidas por minuto para cada `dispositivo_id` (padrão: 60 requisições/min).
- `CITIZENTECH_LIMIARES` *(opcional)*: Caminho para a fonte única de limiares (`limiares.json`). Por padrão, aponta para `app/config/limiares.json`.

---

## 3. Exemplos de Requisições — Cenários Sintéticos

A autenticação é realizada **exclusivamente** via header `X-Device-Key: <DEVICE_KEY>` (cabeçalhos de autorização como Bearer tokens não são aceitos nesta fatia).

### Cenário 1: Normal (Temperatura 25.0 °C / Distância 25.0 cm)
```powershell
curl.exe -X POST "http://localhost:8000/leituras" `
  -H "Content-Type: application/json" `
  -H "X-Device-Key: $env:DEVICE_KEY" `
  -d '{"dispositivo_id": "esp32-lab-01", "metrica": "temperatura_c", "valor": 25.0}'
```
*Resposta esperada:* HTTP 201 com `"risco": "normal"`, `"alerta": false`, `"estado": "pendente_nuvem"`.

### Cenário 2: Atenção (Temperatura 38.0 °C / Distância 12.0 cm)
```powershell
curl.exe -X POST "http://localhost:8000/leituras" `
  -H "Content-Type: application/json" `
  -H "X-Device-Key: $env:DEVICE_KEY" `
  -d '{"dispositivo_id": "esp32-lab-01", "metrica": "temperatura_c", "valor": 38.0, "status": "OK"}'
```
*Resposta esperada:* HTTP 201 com `"risco": "atencao"`, `"alerta": true`. Note que o status `"OK"` declarado pelo cliente é ignorado, prevalecendo o recálculo do servidor. O campo `status` é opcional e aceita apenas o vocabulário do firmware (`OK`, `ALERTA`, `ERRO`); outro valor responde 400, e `ERRO` também responde 400 porque não há medida válida a registrar.

### Cenário 3: Crítico (Temperatura 48.0 °C / Distância 5.0 cm)
```powershell
curl.exe -X POST "http://localhost:8000/leituras" `
  -H "Content-Type: application/json" `
  -H "X-Device-Key: $env:DEVICE_KEY" `
  -d '{"dispositivo_id": "esp32-lab-01", "metrica": "distancia_cm", "valor": 5.0}'
```
*Resposta esperada:* HTTP 201 com `"risco": "critico"`, `"alerta": true`.

### Consulta de Histórico Paginado
```powershell
curl.exe -X GET "http://localhost:8000/leituras?page=1&page_size=20&sessao=sessao-demo" `
  -H "X-Device-Key: $env:DEVICE_KEY"
```

### Consulta de Indicadores Estatísticos
```powershell
curl.exe -X GET "http://localhost:8000/leituras/indicadores?metrica=temperatura_c" `
  -H "X-Device-Key: $env:DEVICE_KEY"
```

---

## 4. Arquitetura e Decisões de Implementação

- **Isolamento de Banco de Dados:** O módulo isolado (`citizentech.leituras.isolado:app`) e o módulo principal (`citizentech.main:app`) compartilham as mesmas rotas e regras de negócio sem importar nem exigir Oracle ou MongoDB.
- **Lock de Filesystem e Durabilidade:** Escrita atômica em CSV sob lock exclusivo de arquivo (`portalocker`) e lock de thread. Antes do append, a integridade do arquivo existente (cabeçalho exato, tipos válidos, valores coerentes com classificações de risco e final sem truncamento) é integralmente verificada. Caso o arquivo esteja corrompido, a API retorna HTTP 503 sem alterar os bytes do arquivo em disco.
- **Tolerância a Falhas e Rollback:** Se o append ou o `os.fsync()` falhar, o arquivo é truncado de volta ao tamanho original para preservar os registros preexistentes intactos, retornando HTTP 503 ao cliente.
- **Consumo Protegido de Stream:** O corpo da requisição é lido progressivamente via `request.stream()` com teto de 8192 bytes (8KB). Requisições sem `Content-Length` que excedam o limite são imediatamente abortadas com HTTP 400 sem consumir o restante do payload.
- **Fail-Closed e Sem Vazamento de Dados:** Sem `DEVICE_KEY` configurada ou com chave incorreta, retorna HTTP 401. Erros de validação nunca refletem conteúdos de payload enviados pelo cliente, parâmetros de consulta arbitrários, caminhos internos ou chaves de segredo.
- **Cálculo Numérico Estável:** O cálculo de média nos indicadores utiliza algoritmo incremental estável, prevenindo estouro para infinito (`Inf`) ao somar valores finitos de grande magnitude e respondendo com erro controlado em caso de overflow.
- **Tratamento de Sentinela de Hardware:** A temperatura de `-127.0 °C` (código de desconexão/erro físico do sensor Dallas DS18B20) é estritamente rejeitada como falha de hardware com HTTP 400, sem impor faixas físicas arbitrárias não contratadas.

---

## 5. Limitações Conhecidas e Escopo Futuro

1. **Sincronização com Nuvem (S3):** O atributo `"estado": "pendente_nuvem"` indica que os dados foram persistidos apenas localmente. O worker outbox assíncrono para reconciliação com a nuvem AWS será implementado na fatia S3.
2. **Autenticação de Usuários e Sessões (S5 / S14):** Nesta fatia S2, a autenticação restringe-se à chave de dispositivo (`DEVICE_KEY`). Não há cookies de sessão, login de usuários ou emissão de JWT implementados nesta etapa.
3. **Campo Relato:** O campo opcional `relato` presente no envelope da telemetria é previsto para apoio didático na S14; nesta fase ele tem tamanho validado (<= 280 caracteres), é descartado e não é persistido nem repassado a modelos de linguagem, prevenindo injeções de prompt.
