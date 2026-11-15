# CitizenTech API — Telemetria CTP e Outbox Durável (S2 + S3)

Módulo de recepção, validação, classificação de risco, persistência durável local e reenvio idempotente de telemetria IoT (sensores de temperatura e distância/nível), operando de forma resiliente com persistência dupla em CSV e SQLite Outbox.

---

## 1. Execução

### Modo Integrado (com Outbox e Worker em Segundo Plano)
O modo principal executa a API com ciclo de vida completo (*lifespan*), inicializando a reconciliação de inicialização entre CSV e SQLite e, se `FUNCTION_URL` estiver configurada, disparando o worker assíncrono interno de despacho para a nuvem:

```powershell
# No diretorio app/api
uv run uvicorn citizentech.main:app --port 8000
```

### Modo Isolado CTP (Autocontido, Sem Nuvem)
O modo isolado permite executar a API sem nenhuma dependência de rede externa, bancos relacionais ou documentais, utilizando exclusivamente o runtime durável local:

```powershell
# No diretorio app/api
uv run uvicorn citizentech.leituras.isolado:app --port 8000
```

> **Aviso de concorrência e processo:** Esta fase foi projetada para execução com um único processo worker do Uvicorn (`--workers 1`), assegurando consistência na escrita do CSV com lock de filesystem/memória (`portalocker`) e transações seguras em SQLite com modo WAL (`busy_timeout=5000`, `synchronous=FULL`).

---

## 2. Vocabulário de Status e Validação

O payload de telemetria aceita opcionalmente o campo `status` reportado pelo hardware:
- **`OK`**: Dispositivo operando em condições normais.
- **`ALERTA`**: Dispositivo sinaliza condição operacional que requer atenção.
- **`ERRO`**: Dispositivo em estado de falha de hardware ou sensor; a API rejeita com **HTTP 400 Bad Request** ("Medida com status de erro do dispositivo nao e valida para registro.").

A classificação final de `risco` (`normal`, `atencao`, `critico`) e a flag `alerta` são sempre recalculadas deterministicamente pela API a partir dos limiares centralizados (`limiares.json`), nunca confiando cegamente no status declarado pelo cliente.

---

## 3. Máquina de Estados da Outbox

A fila de pendências (`pendencias`) gerencia a durabilidade e o ciclo de vida de cada evento de telemetria através da seguinte máquina de estados (`pendente_nuvem` → `sincronizado` | `conflito` | `erro_permanente`):

```
                  ┌──────────────────────────────────────────────┐
                  │ POST /leituras (201 Created)                 │
                  │ CSV fsync OK + SQLite pendencias OK          │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                             ┌───────────────────────┐
            ┌───────────────►│    pendente_nuvem     │◄──────────────┐
            │                └───────────┬───────────┘               │
            │                            │                           │
            │ Retry com                  │ Despacho HTTP             │ Retry com
            │ Backoff Exponencial        │ para FUNCTION_URL         │ Backoff Exponencial
            │ (5xx, Timeout, 429)        │                           │ (Perda de resposta /
            │                            │                           │  Envelope inválido)
            ├────────────────────────────┴───────────────────────────┤
            │                                                        │
            ▼                                                        ▼
┌───────────────────────┐                                ┌───────────────────────┐
│     sincronizado      │                                │       conflito        │
├───────────────────────┤                                ├───────────────────────┤
│ Nuvem responde 200/201│                                │ Nuvem responde 409    │
│ com envelope válido   │                                │ (sem loop infinito)   │
│ {evento_id, id}       │                                └───────────────────────┘
└───────────────────────┘                                            │
                                                                     ▼
                                                         ┌───────────────────────┐
                                                         │   erro_permanente     │
                                                         ├───────────────────────┤
                                                         │ Nuvem responde        │
                                                         │ 400, 401, 403, 413 ou │
                                                         │ 422, ou URL insegura  │
                                                         └───────────────────────┘
```

- **`pendente_nuvem`:** Estado inicial após persistência local. Aguarda envio ou reenvio agendado.
- **`sincronizado`:** Evento confirmado pela nuvem (código HTTP 200 ou 201 com envelope JSON contendo o `evento_id` correspondente **e** um `id` remoto não vazio; sem o `id` não há prova de persistência e o evento continua pendente).
- **`conflito`:** Nuvem retornou HTTP 409 (identificador reutilizado com dados incompatíveis). Sinalizado explicitamente; não repete indefinidamente.
- **`erro_permanente`:** Nuvem retornou erro de cliente/autenticação (HTTP 400, 401, 403, 413, 422) ou a URL de destino é insegura. HTTP 404 e 405 **não** são permanentes: indicam `FUNCTION_URL` mal configurada, que pode ser corrigida, e o evento continua na fila. Interrompe tentativas automáticas.

### Tabela de Códigos de `ultimo_erro`

| Código de Erro | Origem / Causa | Estado Resultante | Política de Reenvio |
|---|---|---|---|
| `CONFIGURACAO_AUSENTE` | `FUNCTION_URL` ou `DEVICE_KEY` não configuradas | `pendente_nuvem` | Aguarda configuração no ambiente |
| `URL_INSEGURA` | URL não usa `https://` (exceto `localhost`/`127.0.0.1`) | `erro_permanente` | Não repete (evita tráfego em texto claro) |
| `TIMEOUT` | Timeout na comunicação HTTP com a Lambda | `pendente_nuvem` | Retry com backoff exponencial (máx 60s) |
| `CONEXAO_RECUSADA` | Falha de conexão de rede ou porta inacessível | `pendente_nuvem` | Retry com backoff exponencial (máx 60s) |
| `RATE_LIMIT_429` | Nuvem respondeu HTTP 429 Too Many Requests | `pendente_nuvem` | Retry com backoff exponencial (máx 60s) |
| `ERRO_SERVIDOR_5XX` | Nuvem respondeu HTTP 500, 502, 503 ou 504 | `pendente_nuvem` | Retry com backoff exponencial (máx 60s) |
| `ENVELOPE_INVALIDO` | Resposta 200/201 sem JSON, com `evento_id` divergente ou sem `id` remoto | `pendente_nuvem` | Retry com backoff exponencial (máx 60s) |
| `CONFLITO_409` | Nuvem respondeu HTTP 409 Conflict | `conflito` | Não repete (requer intervenção/análise) |
| `ERRO_CLIENTE_4XX` | Nuvem respondeu HTTP 400, 401, 403, 413 ou 422 | `erro_permanente` | Não repete (credenciais/payload inválido) |
| `ERRO_DESCONHECIDO` | Exceção imprevista durante despacho HTTP | `pendente_nuvem` | Retry com backoff exponencial (máx 60s) |
| `ERRO_REMOTO_INDEFINIDO` | Outra resposta HTTP (inclui 3xx, 404 e 405) | `pendente_nuvem` | Retry com backoff exponencial (máx 60s) |

---

## 4. Protocolo de Falha, Idempotência e Reconciliação

### Ordem das Gravações e Transação Durável
Dois sistemas de armazenamento distintos (CSV em disco e SQLite outbox) não possuem transação distribuída atômica de dois fases nativa. O protocolo implementa durabilidade e recuperação nos seguintes passos:
1. **Lock Exclusivo:** Cada escrita adquire bloqueio de memória (`threading.RLock`) e de filesystem (`portalocker`), garantindo serialização estrita mesmo sob concorrência intensa (até 6 requisições simultâneas).
2. **Checagem de Idempotência:**
   - Se o `evento_id` já existir e possuir os mesmos campos estáveis (`dispositivo_id`, `metrica`, `unidade`, `valor`, `sessao_laboratorio_id`, `ciclo_id`, `tipo_dispositivo`), responde **HTTP 200 OK** com os dados originais (reaproveitando o `medido_em` original se omitido no reenvio).
   - Se o `evento_id` existir mas contiver dados divergentes, rejeita imediatamente com **HTTP 409 Conflict** sem sobrescrever dados.
3. **Escrita Atômica no CSV:** Grava a nova linha e executa `os.fsync()`. Se ocorrer falha de disco, restaura o arquivo ao tamanho original via truncamento conservador e retorna **HTTP 503**.
4. **Commit na Outbox SQLite:** Insere o registro na tabela `pendencias` com `estado='pendente_nuvem'`. Se o SQLite falhar, desfaz a escrita no CSV via truncamento seguro e retorna **HTTP 503**.
5. **Confirmação:** Confirma **HTTP 201 Created** apenas após ambos estarem duravelmente gravados.

### Janelas de Crash e Protocolos de Recuperação
- **Crash entre CSV fsync e SQLite commit:** O evento está seguro no CSV, mas ausente do SQLite.
  - **Reconciliação no Startup:** Na inicialização da aplicação, `reconciliar_com_csv()` varre o CSV e insere todos os registros órfãos na outbox como `pendente_nuvem`. Vale para a aplicação integrada e para o modo isolado (que reconcilia, mas não inicia o worker).
  - **Cura no Reenvio:** Se o dispositivo reenviar a requisição antes do reinício do servidor, a API detecta que o evento existe no CSV mas não no SQLite, insere a pendência na outbox (idempotente) antes de responder **HTTP 200 OK** (se a inserção falhar, retorna **HTTP 503**).
- **Perda de resposta após aceite na nuvem (T13):** Se a Lambda aceitar o evento mas a conexão cair antes da API receber a confirmação, o worker registrará `TIMEOUT`. Na próxima iteração (após backoff), reenvia exatamente o mesmo `evento_id` e payload estável. A Lambda detecta a idempotência, retorna HTTP 200 com o envelope acordado e mantém apenas um registro lógico. A outbox atualiza para `sincronizado`.
- **Composição na Leitura:** O CSV em disco permanece como histórico imutável com `estado="pendente_nuvem"`. O endpoint `GET /leituras` compõe dinamicamente o estado atual consultando o mapa de estados da outbox SQLite, sem reescrever o arquivo CSV.

### Regra HTTPS para Despacho Remoto
O `ClienteLambda` exige estritamente URLs com esquema `https://`. Apenas `http://localhost` e `http://127.0.0.1` (emulador local na porta 8099) são aceitos com HTTP plano. Qualquer outra URL externa em HTTP plano é recusada imediatamente, nenhum pedido sai da aplicação, e o evento é marcado como `erro_permanente` com código `URL_INSEGURA`, evitando envio da chave do dispositivo (`X-Device-Key`) em texto claro.

---

## 5. Variáveis de Ambiente

Configure as variáveis de ambiente necessárias (nomes sem segredos ou credenciais reais):

- `DEVICE_KEY`: Chave secreta de autenticação compartilhada com o dispositivo IoT e a fronteira Lambda. Obrigatória; a API opera em modo *fail-closed* (sem chave ou com chave incorreta, retorna HTTP 401 via `secrets.compare_digest`).
- `FUNCTION_URL` *(opcional)*: URL de invocação da Lambda na nuvem para despacho da telemetria pelo worker outbox (deve usar `https://`, exceto localhost/127.0.0.1).
- `CITIZENTECH_DADOS`: Caminho raiz para armazenamento de dados fora do repositório git. O runtime salvará `$env:CITIZENTECH_DADOS\runtime\leituras.csv` e `$env:CITIZENTECH_DADOS\runtime\outbox.db`.
- `CITIZENTECH_OUTBOX_DB` *(opcional)*: Caminho direto e explícito para o banco SQLite outbox (usado em testes automatizados).
- `CITIZENTECH_LEITURAS_CSV` *(opcional)*: Caminho direto e explícito para o arquivo CSV de telemetria (usado em testes automatizados).
- `CITIZENTECH_RATE_LIMIT_POR_MINUTO` *(opcional)*: Teto de requisições por minuto para cada `dispositivo_id` (padrão: 60 requisições/min).
- `CITIZENTECH_LIMIARES` *(opcional)*: Caminho para a fonte única de limiares (`limiares.json`). Padrão: `app/config/limiares.json`.

---

## 6. Exemplos de Requisições — Cenários e Contrato HTTP

A autenticação é realizada **exclusivamente** via header `X-Device-Key: <DEVICE_KEY>` (cabeçalhos `Authorization: Bearer` são estritamente rejeitados com HTTP 401).

### Envio de Leitura Nova (HTTP 201 Created)
```powershell
curl.exe -X POST "http://localhost:8000/leituras" `
  -H "Content-Type: application/json" `
  -H "X-Device-Key: $env:DEVICE_KEY" `
  -d '{"evento_id": "evt-demo-01", "dispositivo_id": "esp32-lab-01", "metrica": "temperatura_c", "valor": 38.0}'
```
*Resposta esperada (HTTP 201):*
```json
{
  "evento_id": "evt-demo-01",
  "dispositivo_id": "esp32-lab-01",
  "metrica": "temperatura_c",
  "unidade": "C",
  "valor": 38.0,
  "risco": "atencao",
  "alerta": true,
  "estado": "pendente_nuvem",
  "medido_em": "2026-11-13T12:00:00Z"
}
```

### Reenvio Idêntico do Mesmo Evento (HTTP 200 OK)
```powershell
curl.exe -X POST "http://localhost:8000/leituras" `
  -H "Content-Type: application/json" `
  -H "X-Device-Key: $env:DEVICE_KEY" `
  -d '{"evento_id": "evt-demo-01", "dispositivo_id": "esp32-lab-01", "metrica": "temperatura_c", "valor": 38.0}'
```
*Resposta esperada (HTTP 200):* Mesmo corpo retornado originalmente, sem duplicar registros no CSV nem na outbox. O status 200 local confirma o aceite idempotente e **o 200 de reenvio não significa sincronização com a nuvem**.

### Reenvio Conflitante com Conteúdo Divergente (HTTP 409 Conflict)
```powershell
curl.exe -X POST "http://localhost:8000/leituras" `
  -H "Content-Type: application/json" `
  -H "X-Device-Key: $env:DEVICE_KEY" `
  -d '{"evento_id": "evt-demo-01", "dispositivo_id": "esp32-lab-01", "metrica": "temperatura_c", "valor": 45.0}'
```
*Resposta esperada (HTTP 409):*
```json
{
  "erro": "Conflito",
  "detalhes": "Mesmo evento_id com conteudo divergente."
}
```

### Consulta de Histórico com Composição de Estado
```powershell
curl.exe -X GET "http://localhost:8000/leituras?page=1&page_size=20" `
  -H "X-Device-Key: $env:DEVICE_KEY"
```
*Resposta esperada (HTTP 200):* Itens paginados onde `"estado"` reflete a situação em tempo real (`"sincronizado"`, `"pendente_nuvem"`, `"conflito"` ou `"erro_permanente"`).

---

## 7. Limitações Conhecidas

1. **Fronteira Fake Lambda:** Os testes automatizados da fatia S3 utilizam transporte simulado em memória (`httpx.MockTransport`) na fronteira da Lambda. Isso valida o contrato HTTP, segurança de headers, redirects desabilitados e envelopes de resposta sem realizar chamadas de rede externas, mas **fake da Lambda não prova AWS/RDS** (escopo das fatias S4 e S12).
2. **Tentativas e Backoff:** As pendências em falha transitória realizam **tentativas sem teto (backoff máximo de 60 s)** até que a nuvem restabeleça comunicação ou retorne código definitivo (`409`, `400`, `401`, `403`, `413`, `422`). O intervalo de espera conta a partir do momento da falha de cada item.
3. **Modo Isolado e SQLite:** **O modo isolado passa a gravar também `outbox.db` (SQLite da biblioteca padrão) ao lado do CSV**, mantendo o estado de durabilidade e idempotência local unificado. O banco fica sempre na mesma pasta do CSV (ou em `CITIZENTECH_OUTBOX_DB`, se definida).
4. **Worker Monoprocesso:** O worker em segundo plano é executado como uma tarefa assíncrona dentro do mesmo processo da API FastAPI (*single process*). Não há dependência de Celery, Redis ou filas distribuídas externas. Se o processo da API for finalizado, as pendências permanecem íntegras no SQLite e serão retomadas no próximo startup. A fila não reserva linhas: com mais de um processo (`--workers 2`), o mesmo evento seria enviado em duplicidade (a idempotência da Lambda evitaria o registro duplicado, mas o uso é **não suportado**). Cada envio abre uma conexão HTTP nova, sem reaproveitamento.
5. **Minimização de Dados (D13/D22):** O cliente outbox despacha estritamente os campos normalizados de telemetria, omitindo categoricamente o campo didático `relato` e eventuais dados de consentimento/PII, que serão tratados na fatia S14 após anonimização e validação de consentimento.
6. **Imagem Docker:** o contexto de build é a pasta `app/` (o Dockerfile copia `api/` e `config/`): use `docker compose -f app\docker-compose.yml --profile app build api` ou `docker build -f app\api\Dockerfile app`. A imagem roda como usuário não-root com um único worker e grava CSV e outbox no volume nomeado `api_runtime`.

---

## 8. Autenticação e Sessão (S5)

Proteção funcional de autenticação, sessão segura, prevenção a CSRF e autorização por proprietário (Cybersecurity D12, T14, T16, R20).

### Rotas de Autenticação e Consentimento

| Rota | Método | Autenticação / CSRF | Sucesso | Erros |
|---|---|---|---|---|
| `/auth/registrar` | `POST` | Pública (sem sessão) | `201 Created` `{id, email, criado_em}` | `400` payload/política inválida, `409` e-mail já cadastrado |
| `/auth/login` | `POST` | Pública (sem sessão) | `200 OK` `{id, email}` + cookies `sessao` e `csrf_token` | `401` credenciais inválidas, `429` rate limit excedido, `400` payload inválido |
| `/auth/logout` | `POST` | Cookie `sessao` + `X-CSRF-Token` | `204 No Content` (invalida todas as sessões do usuário no servidor via incremento de `sessao_versao` e remove cookies) | `401` não autenticado, `403` CSRF inválido ou ausente |
| `/me` | `GET` | Cookie `sessao` | `200 OK` `{id, email, criado_em, persona_demo}` | `401` não autenticado |
| `/me/consentimentos` | `POST` | Cookie `sessao` + `X-CSRF-Token` | `201 Created` `{id, finalidade, versao_termo, concedido_em, revogado_em: null}` | `400` finalidade desconhecida, `401`, `403` |
| `/me/consentimentos` | `GET` | Cookie `sessao` (sem CSRF) | `200 OK` `{itens: [...]}` (apenas do proprietário) | `401` |
| `/me/consentimentos/{id}` | `DELETE` | Cookie `sessao` + `X-CSRF-Token` | `204 No Content` (marca `revogado_em`) | `401`, `403`, `404` se inexistente ou de outro usuário (T14) |

### Cookies e Proteção de Sessão
- **Cookie de Sessão (`sessao`):** JWT assinado com HS256 emitido com atributos `HttpOnly; Secure; SameSite=Lax; Path=/` e `Max-Age` configurado conforme expiração (padrão 60 minutos). O atributo `HttpOnly` impede a leitura direta do cookie via JavaScript (`document.cookie`), dificultando o roubo de tokens por scripts maliciosos, mas **não previne XSS em geral** (ataques XSS ainda podem disparar requisições autenticadas no contexto do navegador ou manipular o DOM; a segurança plena exige sanitização rigorosa e Content Security Policy). O token JWT nunca é retornado no corpo da resposta nem em outros cabeçalhos.
- **Cookie de CSRF (`csrf_token`):** Token aleatório emitido com `Secure; SameSite=Lax; Path=/` (sem `HttpOnly`), permitindo leitura pelo frontend para envio no cabeçalho `X-CSRF-Token`.

### Proteção Anti-CSRF (R20)
- Em requisições autenticadas mutáveis (`POST`, `PUT`, `PATCH`, `DELETE`), o servidor exige o cabeçalho `X-CSRF-Token`.
- O servidor calcula o hash SHA-256 do token do cabeçalho e compara com o claim `csrf` contido no JWT de sessão utilizando `hmac.compare_digest` (tempo constante).
- Se o cabeçalho estiver ausente, vazio, divergente ou pertencer a outra sessão, a requisição é rejeitada com **HTTP 403 Forbidden**.
- As rotas públicas (`/auth/registrar`, `/auth/login`) e as rotas seguras de leitura (`GET`) não exigem token CSRF.

### Limite de Taxa no Login (D12, T16)
- No máximo 5 tentativas de login por minuto por e-mail normalizado e, separadamente, por endereço IP de origem (`request.client.host`).
- Conta tentativas com sucesso e falha. A 6ª tentativa retorna **HTTP 429 Too Many Requests** com cabeçalho `Retry-After: <segundos>`.
- O limite por e-mail aplica-se igualmente a e-mails inexistentes e cadastrados, prevenindo enumeração de contas por exaustão ou temporização.

### Variáveis de Ambiente
- `ORACLE_DSN`: String de conexão / DSN com o banco Oracle (ex: `localhost:1521/FREEPDB1`).
- `ORACLE_USER`: Usuário do schema Oracle.
- `ORACLE_PASSWORD`: Senha do usuário Oracle.
- `JWT_SECRET`: Segredo de no mínimo 32 caracteres para assinatura do JWT (fail-closed: se ausente ou curto, rotas de auth respondem `503 Service Unavailable`).
- `JWT_EXPIRA_MINUTOS`: Duração da sessão em minutos (padrão `60`).

### Como Aplicar o DDL no Oracle
O script DDL em dialeto Oracle 19c está em `app/db/ddl/001_usuario_consentimento.sql`:
```powershell
# Executavel via SQL*Plus ou SQL Developer no schema desejado:
# Recomenda-se autenticacao interativa (solicitando a senha em prompt seguro) para evitar o vazamento de credenciais na lista de processos do sistema operacional:
sqlplus "$env:ORACLE_USER@$env:ORACLE_DSN" @app/db/ddl/001_usuario_consentimento.sql
```
Nos testes automatizados, a fixture de sessão do pytest aplica o DDL automaticamente no schema exclusivo de teste (`CT_*TESTE*`).

### Limitações Conhecidas
1. **Rate Limit em Memória e Monoprocesso:** O controle de tentativas de login é mantido em memória dentro do processo da API. Em arquiteturas com múltiplos nós ou múltiplos workers, cada processo terá seu próprio contador, sendo necessário Redis/Key-Value distribuído para coordenação global.
2. **Sem MFA / 2FA:** A autenticação atual implementa fator único (e-mail + senha Argon2id).
3. **Sem Recuperação de Senha:** Não há fluxo de envio de e-mail com token temporário para redefinição de senha esquecida.
4. **Enumeração Residual por 409 no Cadastro:** O endpoint `/auth/registrar` retorna `409 Conflict` quando um e-mail já existe no banco (para consistência e prevenção de contas zumbis), o que revela a existência da conta no momento da tentativa de registro.
5. **Invalidação Global de Sessões no Logout e JWT sem Rotação:** O token de sessão não utiliza mecanismo de refresh tokens rotativos. O endpoint de logout incrementa a coluna global `sessao_versao` do usuário no banco de dados, o que invalida **todas as sessões ativas do usuário em todos os dispositivos simultaneamente**, e não apenas a sessão do dispositivo local.
