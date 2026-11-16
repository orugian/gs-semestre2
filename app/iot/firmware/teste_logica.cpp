#include "logica.h"
#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>

static int total_falhas = 0;

#define TEST_ASSERT(cond, msg) \
    do { \
        if (!(cond)) { \
            std::printf("  [FALHA] Linha %d: %s\n", __LINE__, msg); \
            total_falhas++; \
        } \
    } while (0)

void testar_cenarios_prioritarios() {
    std::printf("=== Teste Prioritario: 3 Cenarios de Demonstracao ===\n");

    // Cenario 1: Normal (25 C, 25 cm)
    Classe t1 = classificar_temperatura(25.0f);
    Classe d1 = classificar_distancia(25.0f);
    Atuadores a1 = decidir_atuadores(t1, d1);
    TEST_ASSERT(t1 == Classe::NORMAL, "Cenario 1: Temperatura 25 C deve ser NORMAL");
    TEST_ASSERT(d1 == Classe::NORMAL, "Cenario 1: Distancia 25 cm deve ser NORMAL");
    TEST_ASSERT(!a1.led && !a1.buzzer && !a1.piscar_falha, "Cenario 1: Atuadores desligados");

    // Cenario 2: Atencao (38 C, 12 cm)
    Classe t2 = classificar_temperatura(38.0f);
    Classe d2 = classificar_distancia(12.0f);
    Atuadores a2 = decidir_atuadores(t2, d2);
    TEST_ASSERT(t2 == Classe::ATENCAO, "Cenario 2: Temperatura 38 C deve ser ATENCAO");
    TEST_ASSERT(d2 == Classe::ATENCAO, "Cenario 2: Distancia 12 cm deve ser ATENCAO");
    TEST_ASSERT(a2.led && !a2.buzzer && !a2.piscar_falha, "Cenario 2: LED aceso sem buzzer");

    // Cenario 3: Critico (48 C, 5 cm)
    Classe t3 = classificar_temperatura(48.0f);
    Classe d3 = classificar_distancia(5.0f);
    Atuadores a3 = decidir_atuadores(t3, d3);
    TEST_ASSERT(t3 == Classe::CRITICO, "Cenario 3: Temperatura 48 C deve ser CRITICO");
    TEST_ASSERT(d3 == Classe::CRITICO, "Cenario 3: Distancia 5 cm deve ser CRITICO");
    TEST_ASSERT(a3.led && a3.buzzer && !a3.piscar_falha, "Cenario 3: LED aceso e buzzer ligado");
}

void testar_fronteiras_e_falhas() {
    std::printf("=== Teste de Fronteiras e Falhas ===\n");

    // Temperatura: normal < 35, atencao 35 <= v < 45, critico >= 45
    TEST_ASSERT(classificar_temperatura(34.99f) == Classe::NORMAL, "Temp 34.99 -> NORMAL");
    TEST_ASSERT(classificar_temperatura(35.0f) == Classe::ATENCAO, "Temp 35.0 -> ATENCAO");
    TEST_ASSERT(classificar_temperatura(44.99f) == Classe::ATENCAO, "Temp 44.99 -> ATENCAO");
    TEST_ASSERT(classificar_temperatura(45.0f) == Classe::CRITICO, "Temp 45.0 -> CRITICO");
    TEST_ASSERT(classificar_temperatura(60.0f) == Classe::CRITICO, "Temp 60.0 -> CRITICO");
    TEST_ASSERT(classificar_temperatura(-127.0f) == Classe::ERRO, "Temp -127.0 -> ERRO");
    TEST_ASSERT(classificar_temperatura(NAN) == Classe::ERRO, "Temp NAN -> ERRO");

    // Distancia: normal > 15, atencao 8 < v <= 15, critico 0 <= v <= 8, <0 ou NAN -> ERRO
    TEST_ASSERT(classificar_distancia(15.01f) == Classe::NORMAL, "Dist 15.01 -> NORMAL");
    TEST_ASSERT(classificar_distancia(15.0f) == Classe::ATENCAO, "Dist 15.0 -> ATENCAO");
    TEST_ASSERT(classificar_distancia(8.01f) == Classe::ATENCAO, "Dist 8.01 -> ATENCAO");
    TEST_ASSERT(classificar_distancia(8.0f) == Classe::CRITICO, "Dist 8.0 -> CRITICO");
    TEST_ASSERT(classificar_distancia(0.0f) == Classe::CRITICO, "Dist 0.0 -> CRITICO");
    TEST_ASSERT(classificar_distancia(-1.0f) == Classe::ERRO, "Dist -1.0 -> ERRO");
    TEST_ASSERT(classificar_distancia(NAN) == Classe::ERRO, "Dist NAN -> ERRO");

    // status_firmware
    TEST_ASSERT(std::strcmp(status_firmware(Classe::NORMAL), "OK") == 0, "status NORMAL -> OK");
    TEST_ASSERT(std::strcmp(status_firmware(Classe::ATENCAO), "ALERTA") == 0, "status ATENCAO -> ALERTA");
    TEST_ASSERT(std::strcmp(status_firmware(Classe::CRITICO), "ALERTA") == 0, "status CRITICO -> ALERTA");
    TEST_ASSERT(std::strcmp(status_firmware(Classe::ERRO), "ERRO") == 0, "status ERRO -> ERRO");

    // Decisao de atuadores com falhas
    Atuadores norm_err = decidir_atuadores(Classe::NORMAL, Classe::ERRO);
    TEST_ASSERT(!norm_err.led && !norm_err.buzzer && !norm_err.piscar_falha, "Temp NORMAL + Dist ERRO -> Atuadores da temp (desligados)");

    Atuadores aten_err = decidir_atuadores(Classe::ERRO, Classe::ATENCAO);
    TEST_ASSERT(aten_err.led && !aten_err.buzzer && !aten_err.piscar_falha, "Temp ERRO + Dist ATENCAO -> LED aceso");

    Atuadores crit_err = decidir_atuadores(Classe::CRITICO, Classe::ERRO);
    TEST_ASSERT(crit_err.led && crit_err.buzzer && !crit_err.piscar_falha, "Temp CRITICO + Dist ERRO -> LED + Buzzer");

    Atuadores ambos_err = decidir_atuadores(Classe::ERRO, Classe::ERRO);
    TEST_ASSERT(!ambos_err.led && !ambos_err.buzzer && ambos_err.piscar_falha, "Ambos ERRO -> piscar_falha");
}

void testar_eco_e_json() {
    std::printf("=== Teste de Eco Ultrassonico e JSON ===\n");

    // Eco us -> cm
    float d = distancia_de_eco_us(1458);
    TEST_ASSERT(std::fabs(d - 25.0f) < 0.1f, "1458 us deve resultar em aprox 25 cm");
    float d_zero = distancia_de_eco_us(0);
    TEST_ASSERT(std::isnan(d_zero), "0 us deve retornar NAN");

    // Montar JSON
    char buf[512];
    int n = montar_json(buf, sizeof(buf), "esp32-boot-1-temperatura_c", "esp32-lab-01", "", "ciclo-01", "temperatura_c", "C", 38.0f, "ALERTA");
    TEST_ASSERT(n > 0, "montar_json deve retornar bytes escritos");
    TEST_ASSERT(std::strstr(buf, "\"schema_version\":\"1.0\"") != nullptr, "JSON deve conter schema_version 1.0");
    TEST_ASSERT(std::strstr(buf, "\"valor\":38.00") != nullptr, "JSON deve conter valor com 2 casas");
    TEST_ASSERT(std::strstr(buf, "sessao_laboratorio_id") == nullptr, "Sessao vazia deve ser omitida");

    // Com sessao
    n = montar_json(buf, sizeof(buf), "id-02", "esp32-lab-01", "sessao-123", "c1", "distancia_cm", "cm", 12.34f, "ALERTA");
    TEST_ASSERT(n > 0, "montar_json com sessao valido");
    TEST_ASSERT(std::strstr(buf, "\"sessao_laboratorio_id\":\"sessao-123\"") != nullptr, "Sessao deve estar presente");

    // Buffer pequeno
    char buf_pequeno[10];
    int n_err = montar_json(buf_pequeno, sizeof(buf_pequeno), "id", "dev", "", "c", "m", "u", 1.0f, "OK");
    TEST_ASSERT(n_err == -1, "Buffer pequeno deve retornar -1");

    // NaN / Inf
    n_err = montar_json(buf, sizeof(buf), "id", "dev", "", "c", "m", "u", NAN, "OK");
    TEST_ASSERT(n_err == -1, "Valor NaN deve retornar -1");
}

int main() {
    testar_cenarios_prioritarios();
    testar_fronteiras_e_falhas();
    testar_eco_e_json();

    if (total_falhas > 0) {
        std::printf("\nRESULTADO: %d teste(s) FALHARAM!\n", total_falhas);
        return 1;
    }
    std::printf("\nRESULTADO: Todos os testes passaram com sucesso!\n");
    return 0;
}
