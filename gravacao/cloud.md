# Roteiro de gravação — Cloud (até 5 min)

**Exigido pelo enunciado:** o **simulador enviando dados**, o **log recebendo** e o **banco gravando**.

Há dois caminhos. **Use o A se tiver o Learner Lab ativo**; senão, o **B** (funciona em qualquer computador). Nos dois, a parte da AWS real aparece pelas capturas já salvas.

## Caminho A — com o Learner Lab (AWS real)

Quem tem acesso ao Lab (Guilherme):
1. Inicie o laboratório. Confira: `curl.exe "<Function URL>/health"` → `"banco":"ok"`. A URL está em `06_Cloud/README.md`.
2. Em `app\cloud`, defina **fora da gravação** `FUNCTION_URL` (sem barra final) e `DEVICE_KEY`. Nunca digite a chave gravando.
3. Abra o CloudWatch → Log groups → `/aws/lambda/CP-2` (Live tail). **Tire o cabeçalho da conta (ID, e-mail) do enquadramento.**
4. Grave seguindo a tabela abaixo, trocando a URL local pela `$env:FUNCTION_URL`:
   - `uv run --frozen python -m citizentech_cloud.simulador --cenario normal --leituras 2`
   - `uv run --frozen python -m citizentech_cloud.simulador --cenario evolucao --leituras 6 --com-chave`
   - consulta ao RDS como em `06_Cloud/README.md` §7.

## Caminho B — sem AWS (emulador local)

1. Na raiz: `powershell -NoProfile -ExecutionPolicy Bypass -File gravacao\cloud_local.ps1`.
   - Abre uma janela **"log da Lambda local"** (o mesmo código da Lambda, rodando na sua máquina) e, no terminal, roda o simulador, os testes negativos e a consulta ao banco, **pausando** (ENTER) para você narrar.
2. Deixe lado a lado: o terminal e a janela do log.
3. Tenha abertas as capturas reais: `06_Cloud\evidencias\20261117_simulador_function_url.png`, `20261116_cloudwatch_critico.png`, `20261116_cloudwatch_descarte.png`, `20261116_cloudwatch_chave_invalida.png`, `20261117_negativos_e_rds_ocorrencias.png`.

**No vídeo, diga claramente:** "esta parte ao vivo é o emulador local com o mesmo código da Lambda; a execução na AWS está nestas capturas".

## Gravação

| Tempo | O que dizer | Tela |
|---|---|---|
| 0:00–0:30 | Cenário: bancada de monitoramento para quem está migrando para IoT industrial. Mede temperatura (°C) e distância (cm) e classifica em normal, atenção e crítico, com limites num arquivo único (`limiares.json`). ODS 4 e 10. | `06_Cloud/README.md` §1–2 |
| 0:30–1:00 | Arquitetura: simulador → Function URL → Lambda → CloudWatch + Comprehend → RDS PostgreSQL. A IA escolhida foi o Comprehend; a conta do Learner Lab **nega** o acesso, então a ingestão continua sem sentimento. | README §3–4 |
| 1:00–1:40 | Health → `banco: ok`. Cenário normal sem chave: 201 com `autenticado=false`. | Terminal |
| 1:40–2:40 | Evolução 30 → 50 °C com chave: normal → atenção (38) → crítico (46, 50) com `alerta=True`. | Terminal |
| 2:40–3:40 | Log: `CLASSIFICACAO risco=…`, `WARNING ALERTA CIDADAO` nos críticos, `GRAVADO NO RDS id=…`. Mostre também a captura real do CloudWatch (id 8, 46 °C, 16/11). | Log + captura |
| 3:40–4:20 | Leitura sem `valor` → 400 e `LEITURA DESCARTADA` no log; chave errada → 401 e `CHAVE INVALIDA`. | Terminal + log |
| 4:20–4:50 | Banco: `SELECT … FROM ocorrencias ORDER BY id DESC LIMIT 10` e `GET /ocorrencias?limite=5`. Mostre a captura real do RDS (ids 12–19, 17/11). | Terminal + captura |
| 4:50–5:00 | Limitações: RDS público como exceção acadêmica; sentimento indisponível na conta. Nomes e RMs. | README §9 |

## Não diga
"O sentimento funcionou" (fica `indisponivel`/`desligado`). Não apresente o emulador como se fosse a AWS. Não diga que o ESP32 do Wokwi enviou à AWS: ele enviou à API local e ao CSV.

## Checklist
- [ ] até 5 min · [ ] simulador, log e banco aparecem · [ ] caminho (AWS real ou emulador) dito em voz alta · [ ] sem chave/senha/conta na tela · [ ] nomes e RMs · [ ] link testado
