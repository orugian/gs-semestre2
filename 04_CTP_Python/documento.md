# Computational Thinking with Python — Entrega
**Integrantes (nome completo + RM):**
- TODO

## Problema, público beneficiado e contribuição da API
TODO
## Arquitetura e origem dos dados
TODO
## Contrato JSON
Ver `00_projeto/README.md` (é o mesmo JSON enviado pelo ESP32 do AICSS). Exemplo do cenário: TODO
## Instruções de execução
```bash
pip install -r requirements.txt
python app.py          # API em http://127.0.0.1:8000
python testes.py       # em outro terminal: 3 cenários + histórico + indicadores
```
Rotas: `POST /leituras`, `GET /leituras` (filtros `dispositivo_id`, `metrica`, `classificacao`), `GET /indicadores`. O histórico fica em `historico.csv`.
## Testes dos endpoints: 3 cenários (requisições, respostas) e histórico CSV
TODO
## Indicador calculado
TODO
## Limitações
TODO
## ODS
TODO
