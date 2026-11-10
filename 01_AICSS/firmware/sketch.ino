/*
 * GS 2026.2 - AICSS - Dispositivo CitizenTech (ESP32)
 * Fluxo: fenômeno -> sensores -> status por sensor (OK/ALERTA) -> alerta local
 *        (LED + buzzer) -> JSON -> servidor Python (01_AICSS/servidor/servidor.py)
 *
 * Os 2 sensores do diagram.json são potenciômetros que simulam qualquer
 * sensor analógico. Troque lerSensor() e a tabela SENSORES pelos sensores
 * reais da ideia (DHT22, HC-SR04, MQ-2, LDR, umidade do solo...).
 * JSON: mesmo contrato de 00_projeto/README.md (aceito também por CTP e Cloud).
 */
#include <WiFi.h>
#include <HTTPClient.h>

// ------------------------------------------------------------- configuração
const char* WIFI_SSID  = "Wokwi-GUEST";   // rede do simulador Wokwi
const char* WIFI_SENHA = "";
// Wokwi (VS Code) acessa o PC por host.wokwi.internal. No Wokwi web é preciso
// expor o servidor na internet (ex.: ngrok). Na placa física, use o IP do PC.
const char* SERVIDOR_URL = "http://host.wokwi.internal:8000/leituras";

const char* DISPOSITIVO_ID = "esp32-01";       // TODO
const float LATITUDE  = 0.0;                   // TODO
const float LONGITUDE = 0.0;                   // TODO
const long  INTERVALO_MS = 5000;

const int PINO_LED    = 2;
const int PINO_BUZZER = 4;

struct Sensor {
  const char* metrica;   // nome da métrica no JSON (TODO)
  int pino;
  float minimo, maximo;  // escala da leitura (TODO)
  float limite;          // limiar de ALERTA (TODO)
  bool invertido;        // true = alerta quando o valor fica ABAIXO do limite
};

Sensor SENSORES[] = {
  {"TODO_metrica_1", 34, 0, 100, 70, false},
  {"TODO_metrica_2", 35, 0, 100, 30, true},
};
const int N_SENSORES = sizeof(SENSORES) / sizeof(SENSORES[0]);

// ---------------------------------------------------------------- funções
float lerSensor(const Sensor& s) {
  int bruto = analogRead(s.pino);  // 0..4095
  return s.minimo + (s.maximo - s.minimo) * bruto / 4095.0;
}

const char* classificar(const Sensor& s, float valor) {
  bool alerta = s.invertido ? (valor < s.limite) : (valor > s.limite);
  return alerta ? "ALERTA" : "OK";
}

void alertaLocal(int qtdAlertas) {
  // Nenhum alerta: tudo desligado | 1 alerta: LED | 2+ alertas: LED + buzzer
  digitalWrite(PINO_LED, qtdAlertas > 0 ? HIGH : LOW);
  if (qtdAlertas > 1) tone(PINO_BUZZER, 1000); else noTone(PINO_BUZZER);
}

String montarJson(const Sensor& s, float valor, const char* status) {
  String j = "{";
  j += "\"dispositivo_id\":\"" + String(DISPOSITIVO_ID) + "\",";
  j += "\"tipo_dispositivo\":\"esp32\",";
  j += "\"latitude\":" + String(LATITUDE, 6) + ",";
  j += "\"longitude\":" + String(LONGITUDE, 6) + ",";
  j += "\"metrica\":\"" + String(s.metrica) + "\",";
  j += "\"valor\":" + String(valor, 2) + ",";
  j += "\"status\":\"" + String(status) + "\"";
  j += "}";
  return j;
}

void enviar(const String& json) {
  Serial.println("JSON -> " + json);
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Sem WiFi: leitura não enviada");
    return;
  }
  HTTPClient http;
  http.begin(SERVIDOR_URL);
  http.addHeader("Content-Type", "application/json");
  int codigo = http.POST(json);
  Serial.printf("HTTP %d %s\n", codigo, codigo > 0 ? http.getString().c_str() : "");
  http.end();
}

// ------------------------------------------------------------ setup / loop
void setup() {
  Serial.begin(115200);
  pinMode(PINO_LED, OUTPUT);
  pinMode(PINO_BUZZER, OUTPUT);
  WiFi.begin(WIFI_SSID, WIFI_SENHA);
  Serial.print("Conectando ao WiFi");
  for (int i = 0; i < 40 && WiFi.status() != WL_CONNECTED; i++) {
    delay(250);
    Serial.print(".");
  }
  Serial.println(WiFi.status() == WL_CONNECTED ? " conectado" : " sem WiFi (modo local)");
}

void loop() {
  int alertas = 0;
  for (int i = 0; i < N_SENSORES; i++) {
    float valor = lerSensor(SENSORES[i]);
    const char* status = classificar(SENSORES[i], valor);
    if (strcmp(status, "ALERTA") == 0) alertas++;
    Serial.printf("%s = %.2f [%s]\n", SENSORES[i].metrica, valor, status);
    enviar(montarJson(SENSORES[i], valor, status));
  }
  alertaLocal(alertas);
  delay(INTERVALO_MS);
}
