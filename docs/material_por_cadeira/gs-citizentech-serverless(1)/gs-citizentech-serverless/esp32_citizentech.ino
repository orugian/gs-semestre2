/*
 * Global Solution - CitizenTech
 * Dispositivo de campo real (ESP32) enviando leituras para a Function URL da Lambda.
 *
 * Use este sketch se o grupo tiver a placa fisica. Quem nao tiver roda o
 * simulador em Python (simulador_dispositivo.py) - a Lambda nao sabe a
 * diferenca: recebe o mesmo JSON nos dois casos.
 *
 * Ligacao do exemplo: sensor ultrassonico HC-SR04 medindo o nivel de um
 * corrego (TRIG no GPIO 5, ECHO no GPIO 18). Troque a funcao lerSensor()
 * pelo sensor do seu cenario (MQ-2 para fumaca, DHT22 para temperatura,
 * higrometro para umidade do solo).
 *
 * Bibliotecas: WiFi.h e HTTPClient.h (ja vem no core ESP32)
 */

#include <WiFi.h>
#include <HTTPClient.h>

// ---------------------------------------------------------- configuracao
const char* WIFI_SSID     = "SUA_REDE";
const char* WIFI_SENHA    = "SUA_SENHA";

// Function URL da Lambda + rota de ingestao
const char* ENDPOINT      = "https://XXXXXXXX.lambda-url.us-east-1.on.aws/ocorrencias";

const char* DISPOSITIVO   = "esp32-ponte-sul-01";
const char* TIPO          = "esp32";
const char* METRICA       = "nivel_rio_cm";
const float LATITUDE      = -23.189600;
const float LONGITUDE     = -45.884100;

const int   PINO_TRIG     = 5;
const int   PINO_ECHO     = 18;
const int   ALTURA_SENSOR = 400;   // cm do sensor ate o fundo do corrego
const long  INTERVALO_MS  = 60000; // uma leitura por minuto

// ---------------------------------------------------------------- setup
void setup() {
  Serial.begin(115200);
  pinMode(PINO_TRIG, OUTPUT);
  pinMode(PINO_ECHO, INPUT);

  WiFi.begin(WIFI_SSID, WIFI_SENHA);
  Serial.print("Conectando ao WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("Conectado. IP: ");
  Serial.println(WiFi.localIP());
}

// ------------------------------------------------------------- sensor
float lerSensor() {
  digitalWrite(PINO_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PINO_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PINO_TRIG, LOW);

  long duracao = pulseIn(PINO_ECHO, HIGH, 30000);
  if (duracao == 0) return -1.0;             // sem eco: leitura invalida

  float distancia = duracao * 0.0343 / 2.0;  // cm do sensor ate a agua
  float nivel = ALTURA_SENSOR - distancia;   // altura da coluna de agua
  if (nivel < 0) nivel = 0;
  return nivel;
}

// ------------------------------------------------------------- envio
void enviar(float valor) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Sem WiFi, leitura descartada");
    return;
  }

  // Monta o mesmo JSON que o simulador em Python envia
  String corpo = "{";
  corpo += "\"dispositivo_id\":\"" + String(DISPOSITIVO) + "\",";
  corpo += "\"tipo_dispositivo\":\"" + String(TIPO) + "\",";
  corpo += "\"latitude\":" + String(LATITUDE, 6) + ",";
  corpo += "\"longitude\":" + String(LONGITUDE, 6) + ",";
  corpo += "\"metrica\":\"" + String(METRICA) + "\",";
  corpo += "\"valor\":" + String(valor, 1);
  corpo += "}";

  HTTPClient http;
  http.begin(ENDPOINT);
  http.addHeader("Content-Type", "application/json");

  int status = http.POST(corpo);
  Serial.print("POST -> HTTP ");
  Serial.println(status);
  if (status > 0) {
    Serial.println(http.getString());   // resposta com nivel_risco e id do banco
  }
  http.end();
}

// -------------------------------------------------------------- loop
void loop() {
  float valor = lerSensor();
  if (valor >= 0) {
    Serial.print(METRICA);
    Serial.print(" = ");
    Serial.println(valor);
    enviar(valor);
  } else {
    Serial.println("Leitura invalida do sensor");
  }
  delay(INTERVALO_MS);
}
