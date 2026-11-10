# Cloud — Ingestão serverless (AWS Lambda + RDS + IA)
**Integrantes (nome completo + RM):**
- TODO

## Cenário CitizenTech (problema, cidadão beneficiado, métrica medida)
TODO
## Limiares adotados (normal / atencao / critico)
TODO
## Caminho de IA usado (A Hugging Face / B Comprehend) e porquê
TODO
## ODS (ex.: 3, 10, 11) e como contribui
TODO
## Passo a passo para reproduzir
**Local, sem AWS (2 terminais):** copiar `servidor_local.py` e `teste_local.py` de `docs/material_por_cadeira/gs-citizentech-serverless(1)/gs-citizentech-serverless/` e rodar:
1. `python servidor_local.py`
2. `FUNCTION_URL=http://127.0.0.1:8099 python simulador_dispositivo.py --cenario TODO --leituras 5 --intervalo 1`

**AWS:**
1. `psql -h <RDS> -U postgres -d citizentech -f tabela_ocorrencias.sql`
2. `pip install pg8000 -t pacote/ && cp lambda_function.py pacote/ && cd pacote && zip -r ../funcao.zip . && cd ..`
3. `aws lambda update-function-code --function-name challenge-api --zip-file fileb://funcao.zip`
4. Variáveis de ambiente: `DB_HOST DB_PORT DB_NAME DB_USER DB_PASSWORD HF_TOKEN`. Timeout de 30 s. Função **fora de VPC**.
5. `FUNCTION_URL=https://xxxx.lambda-url.us-east-1.on.aws python simulador_dispositivo.py --cenario TODO` (rodar um cenário normal e um de risco)
## Function URL
TODO
## Endpoint do RDS (sem senha)
TODO
## Evidências (pasta evidencias/): variável de ambiente; simulador enviando; CloudWatch Logs; consulta no banco
TODO
