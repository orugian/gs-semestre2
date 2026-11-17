# Firmware ESP32 — Monitoramento de Laboratório CitizenTech

Firmware para ESP32 em C++ (Arduino Core) com lógica desacoplada e testada no host via `g++`.
O dispositivo monitora condições ambientais de laboratório através de dois sensores:
- **Temperatura**: Sensor digital Dallas DS18B20 (barramento 1-Wire no GPIO 4, pull-up 4,7 kΩ para 3V3).
- **Distância**: Sensor ultrassônico HC-SR04 (TRIG no GPIO 5, ECHO no GPIO 18).
- **Atuadores**: LED vermelho (GPIO 2, resistor 220 Ω) e Buzzer piezoelétrico (GPIO 15).

---

## 1. Como Gerar e Validar o Header de Limiares (`limiares.h`)

Os limiares de risco são centralizados em `app/config/limiares.json` (D20). O firmware **nunca** deve conter limiares duplicados em código.

Para gerar ou atualizar o header:
```powershell
cd app\tools
uv run python gerar_limiares_h.py
```

Para verificar se o header versionado está sincronizado com o JSON (retorna 0 se idêntico, 1 se divergir):
```powershell
cd app\tools
uv run python gerar_limiares_h.py --verificar
```

---

## 2. Configuração de Credenciais (`segredos.h`)

Para manter a segurança das chaves de API e isolamento de credenciais (D24):
1. Copie o modelo de exemplo para `segredos.h`:
   ```powershell
   Copy-Item app\iot\firmware\segredos.exemplo.h app\iot\firmware\segredos.h
   ```
2. Abra `app/iot/firmware/segredos.h` e defina sua chave (`DEVICE_KEY`) e URL da API:
   ```cpp
   #define WIFI_SSID "Wokwi-GUEST"
   #define WIFI_PASSWORD ""
   #define DEVICE_KEY "troque-pela-chave-da-demo"
   #define API_URL "http://host.wokwi.internal:8000/leituras"
   #define SESSAO_LABORATORIO ""
   ```
3. O arquivo `segredos.h` está incluído no `.gitignore` e **nunca** deve ser versionado no Git.

---

## 2.1 Compilação ESP32 verificada em 16/11/2026

Toolchain usada: Arduino CLI **1.6.0**, core **esp32:esp32 3.0.7**, **OneWire 2.3.8** e **DallasTemperature 4.0.6**; placa `esp32:esp32:esp32`. A instalação local autorizada está isolada em `../.kaiser/toolchains/citizentech-esp32/` (fora do repositório, sem PATH global ou serviço residente); dados, downloads, bibliotecas e cache ficam sob essa mesma raiz. Ocupação medida: **4,76 GB** antes dos artefatos; compilação limitada a **2 jobs**. Remoção após o projeto depende de confirmação do responsável, sem tocar `.dados`.

A pasta compilada deve se chamar `sketch` e conter somente `sketch.ino`, `logica.h`, `limiares.h` e `segredos.exemplo.h`. **Não inclua `teste_logica.cpp`**, que é teste do computador e tem outro `main`. Para compilar não são necessárias credenciais: o exemplo versionado basta; ele **não autentica uma demonstração real**.

Comandos usados (a partir da raiz do repositório; CLI/core/bibliotecas já instalados):

```powershell
$tc = '..\.kaiser\toolchains\citizentech-esp32'
$sketch = '..\.kaiser\tmp\esp32\sketch'
New-Item -ItemType Directory -Force $sketch | Out-Null
'sketch.ino','logica.h','limiares.h','segredos.exemplo.h' | ForEach-Object {
  Copy-Item -LiteralPath "app\iot\firmware\$_" -Destination "$sketch\$_"
}
& "$tc\bin\arduino-cli.exe" --config-file "$tc\arduino-cli.yaml" compile --fqbn esp32:esp32:esp32 --jobs 2 --warnings all --output-dir "$tc\artefatos" $sketch
if ($LASTEXITCODE -ne 0) { throw 'Compilacao ESP32 falhou' }
```

Resultado: **1.046.369 bytes de programa (79%)**, **47.188 bytes de variáveis globais (14%)**, exit 0. A primeira compilação expôs incompatibilidade real com a assinatura mutável de `HTTPClient::POST`; corrigida usando os buffers JSON mutáveis que o sketch já possui, sem remover qualificadores por `const_cast`. Também corrigido o formato de impressão de `boot_seed`. Permanecem warnings da biblioteca externa OneWire 2.3.8; não foram silenciados. Evidência em `01_AICSS/evidencias/20261116_compilacao_esp32.txt`.

**Compilar não é simular:** LED, buzzer, sensores e Wi-Fi/HTTP no Wokwi continuam não verificados sem capturas/Serial Monitor da execução.

## 3. Execução no Simulador Wokwi

### Opção A: Extensão Wokwi no VS Code (Recomendado)
1. Instale a extensão oficial do Wokwi no VS Code.
2. Inicie a API localmente na porta 8000 (`uv run uvicorn citizentech.main:app --port 8000`).
3. Abra a pasta `app/iot/firmware` no VS Code.
4. Pressione `F1` e selecione **Wokwi: Start Simulator** (ou abra `diagram.json`).
5. A URL da API configurada como `http://host.wokwi.internal:8000/leituras` permite comunicação direta entre o simulador e o host.

### Opção B: Wokwi Web (Simulador no Navegador)
1. Quando rodando no navegador, o simulador Wokwi não possui rota local direta para `localhost`.
2. Inicie um túnel HTTPS temporário via ngrok durante a demonstração (D24):
   ```powershell
   ngrok http 8000
   ```
3. Atualize o `API_URL` em `segredos.h` com a URL pública gerada (ex.: `https://xxxx.ngrok-free.app/leituras`).
4. Finalizada a demonstração, encerre o processo do ngrok para revogar o acesso externo.

---

## 4. Testando os 3 Cenários de Demonstração no Simulador

No simulador Wokwi em execução, clique no sensor para alterar o valor simulado:

| Cenário | Temperatura (DS18B20) | Distância (HC-SR04) | Status ESP32 | Atuadores Acionados |
| :--- | :--- | :--- | :--- | :--- |
| **Normal** | `25.0 °C` (clique no DS18B20 e ajuste o slider para 25) | `25.0 cm` (clique no HC-SR04 e ajuste para 25 cm) | `OK` / `OK` | LED apagado, Buzzer desligado |
| **Atenção** | `38.0 °C` (ajuste slider para 38 °C) | `12.0 cm` (ajuste slider para 12 cm) | `ALERTA` / `ALERTA` | **LED aceso**, Buzzer desligado |
| **Crítico** | `48.0 °C` (ajuste slider para 48 °C) | `5.0 cm` (ajuste slider para 5 cm) | `ALERTA` / `ALERTA` | **LED aceso**, **Buzzer acionado** |

### Simulação de Falha de Sensores
- Se o sensor DS18B20 for desconectado ou retornar `-127 °C`, ou se o HC-SR04 sofrer timeout de eco (`0 us` / sem eco):
  - A leitura correspondente é classificada como `ERRO`.
  - Leituras com status `ERRO` **não são enviadas** para a API (evitando poluição do banco e rejeição HTTP 400).
  - A informação de erro é exibida no Serial Monitor.
  - Caso **ambos** os sensores falhem simultaneamente, o firmware ativa o padrão especial `piscar_falha` no LED vermelho.

---

## 5. Simulado × Físico

| Componente / Recurso | Ambiente Wokwi (Simulado) | Ambiente Físico (Bancada) |
| :--- | :--- | :--- |
| **Microcontrolador** | ESP32 DevKit v1/v4 simulado no navegador | ESP32 NodeMCU / DevKit C v4 real conectado via USB |
| **WiFi** | Rede virtual `Wokwi-GUEST` (sem senha) | Rede WiFi local de 2.4 GHz (SSID e senha reais) |
| **Sensor DS18B20** | Componente virtual `wokwi-ds18b20` com controle deslizante | Sensor DS18B20 físico à prova d'água com resistor pull-up de 4,7 kΩ |
| **Sensor HC-SR04** | Componente virtual `wokwi-hc-sr04` com controle deslizante | Sensor ultrassônico HC-SR04 com divisor resistivo ou alimentação compatível |
| **Buzzer** | Simulação de áudio WebAudio pelo navegador | Buzzer piezoelétrico físico com transistor/resistor limitador |
| **Comunicação API** | Roteada por `host.wokwi.internal` ou túnel ngrok | Roteada pelo IP local da máquina na rede LAN (ex.: `http://192.168.1.50:8000`) |

---

## 6. Testes Automatizados no Host

A lógica de decisão, classificação e geração de payload JSON é 100% C++ puro em `logica.h` e é compilada e testada no computador host com `g++`:

```powershell
# Executa todos os testes no host
cd app\tools
uv run pytest tests/test_firmware.py -v
```
