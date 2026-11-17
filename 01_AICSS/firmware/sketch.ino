/*
 * CitizenTech GS 2026.2 - Firmware ESP32 para Wokwi
 * Monitoramento de Laboratorio (Temperatura e Distancia)
 *
 * Arquitetura estrita de responsabilidade:
 * - sketch.ino: exclusivamente I/O (sensores fisicos, rede WiFi, HTTP, atuadores, Serial).
 * - logica.h: regras de negocio puras, classificacao e atuacao.
 * - limiares.h: limiares sincronizados com app/config/limiares.json (D20).
 * - segredos.h: credenciais e chaves do dispositivo (D24).
 */

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <OneWire.h>
#include <DallasTemperature.h>

#include "limiares.h"
#include "logica.h"

#if __has_include("segredos.h")
#include "segredos.h"
#else
#include "segredos.exemplo.h"
#endif

// ------------------------------------------------------------- Mapeamento de Pinos
#define PINO_ONEWIRE 4
#define PINO_TRIG 5
#define PINO_ECHO 18
#define PINO_LED 2
#define PINO_BUZZER 15

// ------------------------------------------------------------- Configuracoes Gerais
static const char* DISPOSITIVO_ID = "esp32-lab-01";
static const unsigned long INTERVALO_MS = 5000;
static const unsigned long TIMEOUT_PULSE_US = 30000; // ~5 metros

// ------------------------------------------------------------- Objetos Globais
static OneWire oneWire(PINO_ONEWIRE);
static DallasTemperature ds18b20(&oneWire);

static uint32_t boot_seed = 0;
static unsigned long contador_ciclo = 0;

// ------------------------------------------------------------- Leitura de Sensores
float ler_temperatura() {
    ds18b20.requestTemperatures();
    float temp = ds18b20.getTempCByIndex(0);
    return temp;
}

float ler_distancia() {
    digitalWrite(PINO_TRIG, LOW);
    delayMicroseconds(2);
    digitalWrite(PINO_TRIG, HIGH);
    delayMicroseconds(10);
    digitalWrite(PINO_TRIG, LOW);

    unsigned long duracao_us = pulseIn(PINO_ECHO, HIGH, TIMEOUT_PULSE_US);
    return distancia_de_eco_us(duracao_us);
}

// ------------------------------------------------------------- Controle de Atuadores
void acionar_atuadores(const Atuadores& atuadores) {
    if (atuadores.piscar_falha) {
        noTone(PINO_BUZZER);
        // Padrao de piscar diferenciado indicando falha geral de sensores
        for (int i = 0; i < 3; i++) {
            digitalWrite(PINO_LED, HIGH);
            delay(100);
            digitalWrite(PINO_LED, LOW);
            delay(100);
        }
    } else {
        digitalWrite(PINO_LED, atuadores.led ? HIGH : LOW);
        if (atuadores.buzzer) {
            tone(PINO_BUZZER, 1000);
        } else {
            noTone(PINO_BUZZER);
        }
    }
}

// ------------------------------------------------------------- Comunicacao HTTP
bool enviar_leitura(char* json, const char* evento_id) {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.printf("[WiFi] Desconectado. Leitura %s nao enviada.\n", evento_id);
        return false;
    }

    HTTPClient http;
    http.begin(API_URL);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-Device-Key", DEVICE_KEY);

    int codigo = http.POST(reinterpret_cast<uint8_t*>(json), strlen(json));
    Serial.printf("[HTTP] POST %s -> status %d\n", evento_id, codigo);

    bool sucesso = (codigo == 200 || codigo == 201);
    bool deve_tentar_reenvio = (!sucesso && (codigo < 0 || codigo == 429 || (codigo >= 500 && codigo < 600)));

    if (deve_tentar_reenvio) {
        Serial.printf("[HTTP] Tentando 1 reenvio idempotente para %s apos falha (%d)...\n", evento_id, codigo);
        delay(500);
        codigo = http.POST(reinterpret_cast<uint8_t*>(json), strlen(json));
        Serial.printf("[HTTP Reenvio] POST %s -> status %d\n", evento_id, codigo);
        sucesso = (codigo == 200 || codigo == 201);
        if (!sucesso) {
            Serial.printf("[HTTP] Falha definitiva no reenvio de %s (status %d). Desistindo.\n", evento_id, codigo);
        }
    } else if (!sucesso) {
        Serial.printf("[HTTP] Falha nao reenviavel (%d) para %s.\n", codigo, evento_id);
    }

    http.end();
    return sucesso;
}

// ------------------------------------------------------------- Setup
void setup() {
    Serial.begin(115200);
    pinMode(PINO_LED, OUTPUT);
    pinMode(PINO_BUZZER, OUTPUT);
    pinMode(PINO_TRIG, OUTPUT);
    pinMode(PINO_ECHO, INPUT);

    digitalWrite(PINO_TRIG, LOW);
    digitalWrite(PINO_LED, LOW);
    noTone(PINO_BUZZER);

    ds18b20.begin();
    boot_seed = esp_random();

    Serial.println("\n[ESP32] Inicializando monitoramento do laboratorio...");
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    Serial.print("[WiFi] Conectando");
    for (int i = 0; i < 40 && WiFi.status() != WL_CONNECTED; i++) {
        delay(250);
        Serial.print(".");
    }
    Serial.println(WiFi.status() == WL_CONNECTED ? " conectado!" : " sem WiFi (modo local)");
}

// ------------------------------------------------------------- Loop Principal
void loop() {
    contador_ciclo++;
    char ciclo_id[32];
    snprintf(ciclo_id, sizeof(ciclo_id), "c-%08lx-%lu", static_cast<unsigned long>(boot_seed), contador_ciclo);

    // 1. Leituras dos sensores
    float temp_c = ler_temperatura();
    Classe classe_temp = classificar_temperatura(temp_c);
    const char* st_temp = status_firmware(classe_temp);

    float dist_cm = ler_distancia();
    Classe classe_dist = classificar_distancia(dist_cm);
    const char* st_dist = status_firmware(classe_dist);

    Serial.printf("[Ciclo %s] Temp: %.2f C [%s] | Dist: %.2f cm [%s]\n",
                  ciclo_id, temp_c, st_temp, dist_cm, st_dist);

    // 2. Decisao e atuacao local
    Atuadores atuadores = decidir_atuadores(classe_temp, classe_dist);
    acionar_atuadores(atuadores);

    // 3. Envio de telemetria individual (ignora falhas/ERRO conforme contrato)
    if (classe_temp != Classe::ERRO) {
        char evento_id_temp[64];
        snprintf(evento_id_temp, sizeof(evento_id_temp), "%s-%s-temperatura_c", DISPOSITIVO_ID, ciclo_id);

        char json_temp[512];
        int bytes = montar_json(
            json_temp, sizeof(json_temp),
            evento_id_temp, DISPOSITIVO_ID, SESSAO_LABORATORIO,
            ciclo_id, "temperatura_c", "C", temp_c, st_temp
        );

        if (bytes > 0) {
            enviar_leitura(json_temp, evento_id_temp);
        }
    } else {
        Serial.println("[Serial] Temperatura com leitura invalida/desconectada (ERRO). Nao enviada a API.");
    }

    if (classe_dist != Classe::ERRO) {
        char evento_id_dist[64];
        snprintf(evento_id_dist, sizeof(evento_id_dist), "%s-%s-distancia_cm", DISPOSITIVO_ID, ciclo_id);

        char json_dist[512];
        int bytes = montar_json(
            json_dist, sizeof(json_dist),
            evento_id_dist, DISPOSITIVO_ID, SESSAO_LABORATORIO,
            ciclo_id, "distancia_cm", "cm", dist_cm, st_dist
        );

        if (bytes > 0) {
            enviar_leitura(json_dist, evento_id_dist);
        }
    } else {
        Serial.println("[Serial] Distancia com leitura invalida/sem eco (ERRO). Nao enviada a API.");
    }

    delay(INTERVALO_MS);
}
