// Harness de host para a evidencia de AICSS: roda a MESMA logica do firmware (logica.h)
// para uma leitura de temperatura e distancia e imprime, em uma linha JSON, a classificacao,
// a decisao dos atuadores e os payloads que o sketch.ino enviaria.
//
// Uso: demo_cenarios <ciclo_id> <temp_c> <dist_cm|sem_eco> [sessao]
// Compilado e chamado por app/tools/demo_firmware_aicss.py.
#include <cstdio>
#include <cstdlib>
#include <cstring>

#include "logica.h"

static const char* DISPOSITIVO_ID = "esp32-lab-01";

static void imprimir_payload(const char* rotulo, Classe classe, const char* ciclo, const char* sessao,
                             const char* metrica, const char* unidade, float valor) {
    if (classe == Classe::ERRO) {
        std::printf("\"%s\":null", rotulo);  // o sketch.ino nao envia leitura com ERRO
        return;
    }
    char evento_id[64];
    std::snprintf(evento_id, sizeof(evento_id), "%s-%s-%s", DISPOSITIVO_ID, ciclo, metrica);
    char json[512];
    int n = montar_json(json, sizeof(json), evento_id, DISPOSITIVO_ID, sessao, ciclo, metrica, unidade,
                        valor, status_firmware(classe));
    if (n < 0) {
        std::printf("\"%s\":\"FALHA_MONTAR_JSON\"", rotulo);
        return;
    }
    std::printf("\"%s\":%s", rotulo, json);
}

static const char* nome_classe(Classe c) {
    switch (c) {
        case Classe::NORMAL: return "normal";
        case Classe::ATENCAO: return "atencao";
        case Classe::CRITICO: return "critico";
        default: return "erro";
    }
}

int main(int argc, char** argv) {
    if (argc < 4) {
        std::fprintf(stderr, "uso: demo_cenarios <ciclo_id> <temp_c> <dist_cm|sem_eco> [sessao]\n");
        return 2;
    }
    const char* ciclo = argv[1];
    float temp = static_cast<float>(std::atof(argv[2]));
    // "sem_eco" reproduz o timeout do pulseIn (0 us), que o firmware converte em NAN
    float dist = std::strcmp(argv[3], "sem_eco") == 0 ? distancia_de_eco_us(0)
                                                       : static_cast<float>(std::atof(argv[3]));
    const char* sessao = argc >= 5 ? argv[4] : "";

    Classe ct = classificar_temperatura(temp);
    Classe cd = classificar_distancia(dist);
    Atuadores a = decidir_atuadores(ct, cd);

    std::printf("{\"classe_temperatura\":\"%s\",\"status_temperatura\":\"%s\",", nome_classe(ct),
                status_firmware(ct));
    std::printf("\"classe_distancia\":\"%s\",\"status_distancia\":\"%s\",", nome_classe(cd),
                status_firmware(cd));
    std::printf("\"led\":%s,\"buzzer\":%s,\"piscar_falha\":%s,", a.led ? "true" : "false",
                a.buzzer ? "true" : "false", a.piscar_falha ? "true" : "false");
    imprimir_payload("json_temperatura", ct, ciclo, sessao, "temperatura_c", "C", temp);
    std::printf(",");
    imprimir_payload("json_distancia", cd, ciclo, sessao, "distancia_cm", "cm", dist);
    std::printf("}\n");
    return 0;
}
