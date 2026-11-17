# Vídeo — Cloud (máx. 5 min)

**Link (YouTube não listado):** [HUMANO — preencher]
**Conteúdo exigido:** o simulador enviando dados, o log recebendo e o banco gravando.

## Preparação (antes de gravar)
1. **Learner Lab ativo** (iniciar o laboratório; conferir `GET <Function URL>/health` com `"banco":"ok"`).
2. Terminal em `app\cloud` com `uv sync` feito e as variáveis `FUNCTION_URL` (sem barra final) e `DEVICE_KEY` definidas **fora da tela** (nunca digitar a chave gravando).
3. Abas abertas: CloudWatch → Log groups → `/aws/lambda/CP-2` (Live tail ou o stream mais recente); um cliente SQL ou CloudShell conectado ao RDS `cp1-cloud`, banco `citizentech`. Console com o cabeçalho da conta (ID, e-mail/RM) **fora do enquadramento** antes de gravar, e a aba de variáveis de ambiente da Lambda **não** deve aparecer sem tarja.
4. `06_Cloud/README.md` aberto para a abertura.

## Roteiro com tempos

| Tempo | Fala (resumo) | Tela |
|---|---|---|
| 0:00–0:30 | Cenário: bancada de monitoramento para profissionais em transição para IoT industrial; métricas temperatura (°C) e distância (cm); limiares normal/atenção/crítico do `limiares.json`. ODS 4 e 10. | README §1–§2 |
| 0:30–1:00 | Arquitetura: simulador → Function URL → Lambda → CloudWatch + Comprehend → RDS. Camada de IA: Comprehend escolhido; na conta do Learner Lab ele responde AccessDenied, e a ingestão continua (fallback). | README §3–§4 |
| 1:00–1:40 | `curl.exe "$env:FUNCTION_URL/health"` → `banco: ok`. Cenário normal sem chave: `uv run python -m citizentech_cloud.simulador --cenario normal --leituras 2`. | Terminal |
| 1:40–2:40 | Cenário de risco com chave: `uv run python -m citizentech_cloud.simulador --cenario evolucao --leituras 6 --com-chave`. Mostrar 30→50 °C passando de normal para atenção e crítico, com `alerta=True` nos críticos. | Terminal |
| 2:40–3:40 | CloudWatch: `PAYLOAD RECEBIDO`, `DISPOSITIVO=… GPS=…`, `CLASSIFICACAO risco=…`, `WARNING ALERTA CIDADAO`, `WARNING Falha na analise de sentimento via Comprehend` seguida de `GRAVADO NO RDS id=…`. | CloudWatch |
| 3:40–4:20 | Leitura inválida (sem `valor`) → 400 e `WARNING LEITURA DESCARTADA` no log; chave errada → 401. | Terminal + CloudWatch |
| 4:20–4:50 | Banco: `SELECT id, dispositivo_id, metrica, valor, nivel_risco, alerta, autenticado, analise_status, criado_em FROM ocorrencias ORDER BY id DESC LIMIT 10;` e `GET /ocorrencias?limite=5`. | SQL / terminal |
| 4:50–5:00 | Fechamento: limitações (RDS público como exceção acadêmica, IA sem resultado na conta). Nomes e RMs. | README §9 |

## Cuidados
- Não afirmar que o sentimento funcionou: na conta ele fica `indisponivel`.
- Se o lab expirar durante a gravação, reiniciar e repetir a partir de 1:00.
