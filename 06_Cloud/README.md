# Cloud — Ingestão serverless de leituras de campo (AWS Lambda + RDS PostgreSQL + IA)

**Disciplina:** Plataformas de Serviços Cognitivos · **Global Solution 2026.2 — CitizenTech**

**Integrantes (nome completo + RM):**
- [HUMANO — preencher]

> Este README descreve o que foi **implementado e executado na AWS real** (Learner Lab, us-east-1) em 16/11/2026, o que é **simulado** (o dispositivo de campo é um script, como o enunciado permite) e o que **não funcionou** por limitação de conta (a camada de IA, ver §4). Cada número citado vem das evidências em `evidencias/`.

## 1. Cenário CitizenTech

**Problema.** Quem está migrando de carreira para monitoramento industrial e IoT precisa praticar a leitura de sensores, o ajuste de limiares e a reação a alarmes. Laboratório físico com instrumentação é caro e raro fora dos grandes centros, e quem trabalha durante o dia não consegue frequentar uma bancada presencial.

**Cidadão beneficiado.** O profissional graduado e experiente em transição de carreira, usuário da plataforma CitizenTech, que faz a trilha prática opcional do destino "Analista de Monitoramento/IoT Industrial". O laboratório é uma **bancada de monitoramento** com um ESP32 (ou o simulador) medindo temperatura e distância. A nuvem recebe as leituras, registra tudo, classifica o risco e guarda o histórico que a pessoa usa para demonstrar a competência de monitoramento.

**Métricas medidas pelo dispositivo.**
- `temperatura_c`: temperatura da bancada em °C (sensor DS18B20 no firmware);
- `distancia_cm`: distância de aproximação em cm (sensor HC-SR04 no firmware), usada como "zona de segurança" da bancada.

**Dispositivo.** Neste módulo o dispositivo é o **simulador por software** `citizentech_cloud.simulador`, que assume a identidade `lab-iot-bancada-01` (`tipo_dispositivo = sensor_bancada`) e envia o mesmo JSON que o firmware envia. O firmware do ESP32 existe em `app/iot/firmware/`, mas **não foi usado** nas evidências deste README.

## 2. Limiares adotados

Os limiares ficam num único arquivo, `app/config/limiares.json`, que é copiado para dentro do pacote da Lambda no empacotamento (`citizentech_cloud/limiares.json`) e também gera o cabeçalho do firmware. A classificação é local, não usa rede e sempre funciona.

| Métrica | Direção | `normal` | `atencao` | `critico` |
|---|---|---|---|---|
| `temperatura_c` (°C) | quanto maior, pior | v < 35 | 35 ≤ v < 45 | v ≥ 45 |
| `distancia_cm` (cm) | quanto menor, pior | v > 15 | 8 < v ≤ 15 | 0 ≤ v ≤ 8 |

- Valor `critico` → `alerta = true` na resposta e linha `WARNING ALERTA CIDADAO` no CloudWatch.
- Métrica sem limiar cadastrado (por exemplo, `nivel_rio_cm` do simulador oficial do professor) é **aceita e gravada** com `nivel_risco = desconhecido`, sem alerta. Distância negativa é descartada com 400.

## 3. Arquitetura e comportamento da API

```
Simulador (lab-iot-bancada-01)  ou  ESP32 (firmware)  ou  API CitizenTech (outbox)
        |  HTTPS POST /ocorrencias  {dispositivo_id, metrica, valor, gps, relato, evento_id}
        v
AWS Lambda "CP-2" (Function URL, fora de VPC, Python, timeout 30 s)
        |-- CloudWatch Logs  /aws/lambda/CP-2  (payload, dados interpretados, classificação, id)
        |-- Amazon Comprehend (sentimento do relato, idioma pt) -> falha tratada (ver §4)
        v
Amazon RDS PostgreSQL "cp1-cloud", banco "citizentech", tabela "ocorrencias" (usuário app_ingest)
        |
        v
GET /ocorrencias  (painel / alerta)
```

| Rota | Comportamento |
|---|---|
| `GET /health` | `200 {"status":"ok","banco":"ok"|"indisponivel","ia_provedor":"comprehend"}` |
| `POST /ocorrencias` | valida `dispositivo_id`, `metrica`, `valor` (obrigatórios), tipos, faixas (`valor` finito em [−1e6, 1e6], latitude, longitude), `relato` ≤ 280 caracteres, corpo ≤ 8 KB. Campo ausente ou inválido → **400**. Sucesso → **201** com `id`, `nivel_risco`, `alerta`, `sentimento`, `confianca`, `analise_status`. |
| `GET /ocorrencias?limite=N` | lista as últimas N (1–100, padrão 20) ocorrências gravadas. |

Proteções adicionais:
- **Chave do dispositivo opcional (`X-Device-Key`).** Sem a chave, a leitura é aceita e gravada com `autenticado = false`, para que o simulador oficial do professor funcione. Chave errada → **401** e `WARNING CHAVE INVALIDA`. O simulador e a API CitizenTech enviam a chave.
- **Limite por dispositivo:** 30 leituras por minuto por `dispositivo_id`, contadas no RDS → **429**.
- **Idempotência:** `evento_id` repetido com o mesmo conteúdo → **200** com `"duplicata": true` (não grava de novo); mesmo `evento_id` com conteúdo diferente → **409**.
- Banco fora do ar → **503**, sem derrubar a função.

**Linhas de log** (todas em `/aws/lambda/CP-2`): `REQUISICAO <método> <rota>` · `PAYLOAD RECEBIDO: <json bruto>` · `DISPOSITIVO=… TIPO=… GPS=(lat, lon) <métrica>=<valor> AUTENTICADO=…` · `CLASSIFICACAO risco=… sentimento=… confianca=… analise=…` · `GRAVADO NO RDS id=…`. Saem como **WARNING**: `LEITURA DESCARTADA - <motivo>`, `CHAVE INVALIDA`, `ALERTA CIDADAO` (nível crítico), `LIMITE EXCEDIDO` e a falha da IA.

## 4. Camada de IA: caminho escolhido e o que aconteceu

**Caminho B — Amazon Comprehend** (`detect_sentiment`, `LanguageCode="pt"`), selecionado pela variável `SENTIMENTO_PROVEDOR=comprehend`. O código também implementa o **caminho A** (Hugging Face, modelo `cardiffnlp/twitter-xlm-roberta-base-sentiment` no endpoint `router.huggingface.co/hf-inference`, só com `urllib`, token em `HF_TOKEN`), ativado com `SENTIMENTO_PROVEDOR=hf`.

**Por que o caminho B.** Em 12/11/2026 o token Hugging Face do grupo era válido, mas a inferência respondia **HTTP 402** (conta sem créditos). O Comprehend não exige token: a autorização vem da role da Lambda, então nenhum segredo de IA fica no código nem em variável de ambiente.

**Resultado real na AWS.** A role do Learner Lab (`LabRole`) **não tem permissão** para o Comprehend: a chamada falha com `ClientError` (AccessDenied, verificado em 16/11/2026). O grupo não anexou a política `ComprehendReadOnly`: o Learner Lab trabalha com a `LabRole` pronta e a alteração de IAM não foi tentada. Por isso **nenhuma leitura gravada tem sentimento**: todas aparecem com `analise_status = indisponivel` (ou `sem_relato` quando não há relato). **Não apresentamos nenhum rótulo de sentimento como resultado medido.**

**A falha da IA não derruba a ingestão** (requisito do enunciado), e isso está evidenciado: no print do CloudWatch a linha `WARNING Falha na analise de sentimento via Comprehend: ClientError` é seguida de `CLASSIFICACAO risco=normal … analise=indisponivel` e de `GRAVADO NO RDS id=2`. O cliente do Comprehend tem timeout de 3 s de conexão e 5 s de leitura, com uma tentativa, para nunca estourar os 30 s da função.

**Uso do sentimento no produto.** O sentimento mede só o tom do relato da ocorrência. Ele é um metadado do registro e **nunca entra em nota ou avaliação de competência** da pessoa (decisão D23 do projeto).

**Para ver o sentimento funcionando** numa conta com permissão: anexar `ComprehendReadOnly` à role da Lambda (nada no código muda), ou cadastrar `HF_TOKEN` de uma conta com créditos e trocar `SENTIMENTO_PROVEDOR` para `hf`. Isso **não foi executado** pelo grupo.

## 5. ODS

- **ODS 4 — Educação de qualidade (meta 4.4):** a bancada remota dá prática de monitoramento a adultos em requalificação profissional, que dificilmente teriam acesso a laboratório físico.
- **ODS 10 — Redução das desigualdades:** a prática deixa de depender de morar perto de um laboratório ou de ter horário livre durante o dia; basta o simulador (ou um ESP32 barato) e a API.
- **ODS 8 — Trabalho decente (8.5/8.6), secundário:** a evidência prática apoia a transição para ocupações técnicas formais.
- **ODS 3 — Saúde e bem-estar (relação indireta):** o próprio exercício trata de segurança de bancada; a classificação `critico` com alerta treina a reação a temperatura alta e aproximação perigosa.

## 6. Entregáveis

| Item | Onde |
|---|---|
| **Function URL** | `https://olzbq42krrvnxabsypfszez6qa0aehbm.lambda-url.us-east-1.on.aws/` (Auth type NONE; rotas `/health` e `/ocorrencias`) |
| **Endpoint do RDS** (sem senha) | `cp1-cloud.cdbgtc0abxoh.us-east-1.rds.amazonaws.com:5432`, banco `citizentech`, TLS `verify-full` |
| Script da tabela `ocorrencias` | `tabela_ocorrencias.sql` (cópia de `app/cloud/sql/ocorrencias.sql`) |
| Handler da Lambda e simulador na raiz do módulo | `lambda_function.py` (cópia do handler final) e `simulador_dispositivo.py` (cópia de `simulador.py`). Os dois importam o pacote `citizentech_cloud` de `codigo/`; para rodar o simulador a partir de `06_Cloud/`: `$env:PYTHONPATH='codigo'; python simulador_dispositivo.py --cenario normal --leituras 2` (com `FUNCTION_URL` definido, como em §7.2). O handler depende do driver `pg8000`, que vai dentro do zip da função (§7.2) |
| Código final da Lambda e do simulador | `codigo/` (cópia gerada de `app/cloud/src/citizentech_cloud/`: `lambda_function.py`, `risco.py`, `sentimento.py`, `banco.py`, `simulador.py`, `servidor_local.py`, `limiares.json`) |
| Testes automatizados | `app/cloud/tests/` (115 testes; rodam contra PostgreSQL local em Docker) |
| Evidências | `evidencias/` (§8) |
| Vídeo (≤ 5 min) | [HUMANO — link] |

> As cópias em `06_Cloud/codigo/`, `lambda_function.py`, `simulador_dispositivo.py` e `tabela_ocorrencias.sql` são geradas pelo empacotador do projeto (`app/tools/empacotar_entregas.py`) a partir de `app/cloud/` e substituem os modelos do enunciado. A fonte é `app/cloud/`.

**Disponibilidade para a correção.** O Learner Lab desliga os recursos ao fim de cada sessão. Se a Function URL ou o `/health` não responderem (ou mostrarem `"banco":"indisponivel"`), o laboratório expirou e o grupo precisa reiniciá-lo. O grupo mantém o laboratório ativo nas janelas de correção.

## 7. Passo a passo para reproduzir

Pré-requisitos: Python 3.11 e [uv](https://docs.astral.sh/uv/). Os comandos partem de `app/cloud/`. Use PowerShell ou bash; os exemplos estão em PowerShell.

### 7.1 Local, sem AWS (emulador da Function URL + PostgreSQL em Docker)

```powershell
# na raiz do repositório: sobe o PostgreSQL de teste (porta 5433)
docker compose -f app\docker-compose.yml --profile teste up -d --wait postgres

cd app\cloud
uv sync
$env:DB_HOST='localhost'; $env:DB_PORT='5433'; $env:DB_NAME='citizentech_teste'
$env:DB_USER='citizentech_teste'; $env:DB_PASSWORD='<senha do .env local>'; $env:DB_SSLMODE='disable'
$env:SENTIMENTO_PROVEDOR='desligado'
# aplica a tabela (a parte do app_ingest depois de FIM_DDL é opcional no local)
# psql ... -f sql\ocorrencias.sql
uv run python -m citizentech_cloud.servidor_local --porta 8099      # terminal 1
uv run python -m citizentech_cloud.simulador --url http://127.0.0.1:8099 --cenario normal --leituras 4 --intervalo 1     # terminal 2
uv run python -m citizentech_cloud.simulador --url http://127.0.0.1:8099 --cenario evolucao --leituras 6 --intervalo 1
uv run pytest -q                                                     # 115 testes
```

### 7.2 AWS (Learner Lab)

1. **RDS PostgreSQL** (público como exceção acadêmica; SG com 5432 aberto durante a correção, porque a Lambda fora de VPC sai por IPs dinâmicos). Criar o banco `citizentech` e aplicar o script com o usuário master, criando o usuário de menor privilégio `app_ingest` (só `INSERT` e `SELECT`):
   ```bash
   psql "host=<endpoint> dbname=citizentech user=postgres sslmode=verify-full sslrootcert=global-bundle.pem" \
        -v senha_app_ingest='<senha forte>' -f sql/ocorrencias.sql
   ```
2. **Pacote da função:** `uv run python empacotar_lambda.py --saida <pasta> --ca <caminho>/global-bundle.pem` gera `funcao_lambda.zip` (handler na raiz, pacote `citizentech_cloud/`, `limiares.json`, certificado da AWS e o driver `pg8000`, só Python puro) e imprime o SHA-256.
3. **Lambda** (console): runtime Python 3.11+, **fora de VPC**, timeout **30 s**, handler `lambda_function.lambda_handler`, enviar o zip. Criar a **Function URL** com Auth type NONE.
4. **Variáveis de ambiente:** `DB_HOST`, `DB_PORT=5432`, `DB_NAME=citizentech`, `DB_USER=app_ingest`, `DB_PASSWORD`, `DB_SSLMODE=verify-full`, `DEVICE_KEY` (chave do dispositivo), `SENTIMENTO_PROVEDOR=comprehend` (ou `hf` com `HF_TOKEN`). Opcional: `RATE_LIMIT_POR_MINUTO` (padrão 30). Nenhum segredo fica no código.
5. **Teste ponta a ponta:**
   ```powershell
   $env:FUNCTION_URL='https://<id>.lambda-url.us-east-1.on.aws'
   uv run python -m citizentech_cloud.simulador --cenario normal --leituras 2
   $env:DEVICE_KEY='<chave>'; uv run python -m citizentech_cloud.simulador --cenario evolucao --leituras 6 --com-chave
   curl.exe "$env:FUNCTION_URL/ocorrencias?limite=5"
   ```
   Conferir no CloudWatch (`/aws/lambda/CP-2`) e no RDS (consultas no fim de `sql/ocorrencias.sql`).

## 8. Evidências (`evidencias/`)

Execução de 16/11/2026, 15h37–15h38 (UTC−3), contra a Function URL real.

| # exigido | Evidência | Arquivo | Situação |
|---|---|---|---|
| 1 | Variáveis de ambiente cadastradas na Lambda (valores secretos tarjados) | `20261116_lambda_variaveis_ambiente.png` | ok |
| 2 | Simulador enviando as leituras e a resposta da API | `20261116_e2e_function_url.txt` (saída do terminal) | texto ok; **print do terminal pendente** [HUMANO] |
| 3 | CloudWatch com payload chegando, classificação e gravação | `20261116_cloudwatch_3.png` | ok; prints do descarte/chave inválida e do alerta crítico **a refazer** [HUMANO] |
| 4 | Consulta no banco com as ocorrências gravadas | `20261116_consulta_rds.txt` (psql, TLS verify-full) | texto ok; **print pendente** [HUMANO] |
| extra | Function URL da Lambda `CP-2` no console | `20261116_function_url.png` | ok (usuário do console tarjado) |
| extra | RDS `cp1-cloud`: endpoint, porta 5432, *publicly accessible* = Yes, security group `default` | `20261116_rds_conectividade.png` | ok (usuário tarjado) |
| extra | Regras do security group: entrada CIDR `0.0.0.0/0` (exceção acadêmica, §9) | `20261116_rds_security_group.png` | ok (usuário tarjado) |

O que as evidências mostram (valores copiados das saídas):
- `GET /health` → 200 `{"status": "ok", "banco": "ok", "ia_provedor": "comprehend"}`.
- **Cenário normal** sem chave: 2 leituras (25,0 °C e 25,0 cm) → 201, `risco=normal`, `alerta=False`, gravadas como `autenticado=false` (ids 2 e 3).
- **Cenário de risco** com chave: 6 leituras de 30 a 50 °C → 30 e 34 `normal`, 38 e 42 `atencao`, 46 e 50 `critico` com `alerta=True` (ids 4–9).
- Payload do simulador oficial do professor (`nivel_rio_cm` = 268,9) → 201 com `nivel_risco=desconhecido` (id 10).
- Leitura sem `metrica`/`valor` → 400; chave inválida → 401; `evento_id` repetido igual → 200 `duplicata: true`; repetido diferente → 409.
- No RDS: 10 linhas (ids 2–11), 2 críticas (ids 8 e 9, 46 e 50 °C); resumo `lab-iot-bancada-01`: 9 leituras, média 33,56, pico 50, 2 críticas, 2 não autenticadas.

## 9. Limitações declaradas

- **IA sem resultado na conta do Learner Lab:** Comprehend negado (AccessDenied) e Hugging Face com 402. O fallback funciona; o sentimento em si **não foi observado**.
- **RDS público e SG 5432 aberto** para a Lambda fora de VPC e para a correção. Em produção: Lambda em VPC com RDS privado e RDS Proxy, ou Data API, e segredo no AWS Secrets Manager.
- **Function URL sem autenticação obrigatória** (a chave é opcional para aceitar o simulador do professor). Leituras sem chave ficam marcadas `autenticado=false` e sujeitas ao limite por dispositivo.
- **Variável do limite:** no print das variáveis o nome aparece como `RATE_KIMIT_POR_MINUTO` (erro de digitação no console). O código lê `RATE_LIMIT_POR_MINUTO` e, sem ela, usa o padrão 30, que é o mesmo valor; o comportamento não muda.
- O relato de texto livre (≤ 280 caracteres) vai para o log e para o banco. O simulador envia relatos sem dados pessoais. A redação do relato antes de sair da plataforma faz parte da sessão de laboratório do app, que **ainda está em desenvolvimento**.
- O dispositivo das evidências é o **simulador**. O firmware do ESP32 tem a lógica testada no computador, mas **ainda não foi executado no Wokwi nem contra a Lambda**.
