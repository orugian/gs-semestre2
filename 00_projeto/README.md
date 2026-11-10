# CitizenTech — GS 2026.2
**Integrantes (nome completo + RM):**
- TODO

Prazo de todas as entregas: **19/11/2026 às 23h55** (Portal do Aluno).

## Problema real
TODO
## Público/cidadão beneficiado (condições de acesso)
TODO
## Contexto (cidade, campo ou comunidade)
TODO
## Solução e inovação
TODO
## ODS relacionados e como contribuem
TODO
## Ideias da live (04/11) que inspiraram a proposta
TODO
## Arquitetura integrada
TODO
## Contrato JSON único (AICSS → CTP → Cloud)
Um POST por leitura de sensor. É o mesmo formato que a Lambda do professor (`06_Cloud`) já aceita.

```json
{
  "dispositivo_id": "esp32-01",
  "tipo_dispositivo": "esp32",
  "latitude": -23.5505,
  "longitude": -46.6333,
  "metrica": "TODO_nome_da_metrica",
  "valor": 42.0,
  "status": "OK",
  "medido_em": "2026-11-10T12:00:00Z",
  "relato": "texto opcional do cidadão"
}
```
- Obrigatórios: `dispositivo_id`, `metrica`, `valor`. Os demais são opcionais.
- `status` (`OK`/`ALERTA`) é calculado no ESP32 (AICSS).
- O risco na nuvem/API é `normal` / `atencao` / `critico` (CTP e Cloud).
- Os limiares de cada métrica precisam ser os mesmos em `01_AICSS/firmware/sketch.ino`, `04_CTP_Python/processamento.py` e `06_Cloud/lambda_function.py`.
## Acessibilidade, segurança, proteção de dados, sustentabilidade, condições reais de uso
TODO
