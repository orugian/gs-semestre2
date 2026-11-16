#ifndef LOGICA_H
#define LOGICA_H

#include "limiares.h"
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>

enum class Classe { NORMAL, ATENCAO, CRITICO, ERRO };

// Classifica a temperatura em graus Celsius conforme limiares.h
inline Classe classificar_temperatura(float c) {
    if (std::isnan(c) || std::isinf(c) || std::fabs(c - (-127.0f)) < 0.01f) {
        return Classe::ERRO;
    }
    if (c >= LIMIAR_TEMPERATURA_CRITICO) {
        return Classe::CRITICO;
    }
    if (c >= LIMIAR_TEMPERATURA_ATENCAO) {
        return Classe::ATENCAO;
    }
    return Classe::NORMAL;
}

// Classifica a distancia em centimetros conforme limiares.h
inline Classe classificar_distancia(float cm) {
    if (std::isnan(cm) || std::isinf(cm) || cm < LIMIAR_DISTANCIA_MINIMO) {
        return Classe::ERRO;
    }
    if (cm <= LIMIAR_DISTANCIA_CRITICO) {
        return Classe::CRITICO;
    }
    if (cm <= LIMIAR_DISTANCIA_ATENCAO) {
        return Classe::ATENCAO;
    }
    return Classe::NORMAL;
}

// Converte a classe para o formato de status do firmware (OK | ALERTA | ERRO)
inline const char* status_firmware(Classe c) {
    switch (c) {
        case Classe::NORMAL:
            return "OK";
        case Classe::ATENCAO:
        case Classe::CRITICO:
            return "ALERTA";
        case Classe::ERRO:
        default:
            return "ERRO";
    }
}

struct Atuadores {
    bool led;
    bool buzzer;
    bool piscar_falha;
};

// Decide acionamento com base na pior classe entre os sensores validos
inline Atuadores decidir_atuadores(Classe temp, Classe dist) {
    if (temp == Classe::ERRO && dist == Classe::ERRO) {
        return {false, false, true};
    }

    bool tem_critico = (temp == Classe::CRITICO || dist == Classe::CRITICO);
    bool tem_atencao = (temp == Classe::ATENCAO || dist == Classe::ATENCAO);

    if (tem_critico) {
        return {true, true, false};
    }
    if (tem_atencao) {
        return {true, false, false};
    }
    return {false, false, false};
}

// Converte duracao do pulso de eco (us) para distancia (cm); 0 us vira NAN
inline float distancia_de_eco_us(unsigned long duracao_us) {
    if (duracao_us == 0) {
        return NAN;
    }
    return static_cast<float>(duracao_us) * 0.0343f / 2.0f;
}

// Escapa caracteres especiais para JSON em buffer estatico sem heap
inline bool escapar_para_json(const char* src, char* dst, size_t dst_tam) {
    if (!dst || dst_tam == 0) return false;
    if (!src) {
        dst[0] = '\0';
        return true;
    }
    size_t j = 0;
    for (size_t i = 0; src[i] != '\0'; ++i) {
        char c = src[i];
        if (c == '"' || c == '\\') {
            if (j + 2 >= dst_tam) return false;
            dst[j++] = '\\';
            dst[j++] = c;
        } else if (c == '\n') {
            if (j + 2 >= dst_tam) return false;
            dst[j++] = '\\';
            dst[j++] = 'n';
        } else if (c == '\r') {
            if (j + 2 >= dst_tam) return false;
            dst[j++] = '\\';
            dst[j++] = 'r';
        } else if (c == '\t') {
            if (j + 2 >= dst_tam) return false;
            dst[j++] = '\\';
            dst[j++] = 't';
        } else {
            if (j + 1 >= dst_tam) return false;
            dst[j++] = c;
        }
    }
    if (j >= dst_tam) return false;
    dst[j] = '\0';
    return true;
}

// Monta o payload JSON estrito da telemetria CTP. Retorna bytes ou -1 se falhar
inline int montar_json(char* buf, size_t tam, const char* evento_id, const char* dispositivo_id,
                       const char* sessao, const char* ciclo_id, const char* metrica,
                       const char* unidade, float valor, const char* status) {
    if (!buf || tam == 0) {
        return -1;
    }
    if (std::isnan(valor) || std::isinf(valor)) {
        return -1;
    }

    char esc_ev[80];
    char esc_disp[80];
    char esc_sess[80];
    char esc_ciclo[80];
    char esc_metr[40];
    char esc_unid[20];
    char esc_stat[20];

    if (!escapar_para_json(evento_id, esc_ev, sizeof(esc_ev))) return -1;
    if (!escapar_para_json(dispositivo_id, esc_disp, sizeof(esc_disp))) return -1;
    if (!escapar_para_json(sessao, esc_sess, sizeof(esc_sess))) return -1;
    if (!escapar_para_json(ciclo_id, esc_ciclo, sizeof(esc_ciclo))) return -1;
    if (!escapar_para_json(metrica, esc_metr, sizeof(esc_metr))) return -1;
    if (!escapar_para_json(unidade, esc_unid, sizeof(esc_unid))) return -1;
    if (!escapar_para_json(status, esc_stat, sizeof(esc_stat))) return -1;

    if (std::fabs(valor) < 0.0001f) {
        valor = 0.0f;
    }

    int n = 0;
    if (sessao && sessao[0] != '\0') {
        n = std::snprintf(
            buf, tam,
            "{\"schema_version\":\"1.0\",\"evento_id\":\"%s\",\"dispositivo_id\":\"%s\",\"tipo_dispositivo\":\"esp32\",\"sessao_laboratorio_id\":\"%s\",\"ciclo_id\":\"%s\",\"metrica\":\"%s\",\"unidade\":\"%s\",\"valor\":%.2f,\"status\":\"%s\"}",
            esc_ev, esc_disp, esc_sess, esc_ciclo, esc_metr, esc_unid, valor, esc_stat
        );
    } else {
        n = std::snprintf(
            buf, tam,
            "{\"schema_version\":\"1.0\",\"evento_id\":\"%s\",\"dispositivo_id\":\"%s\",\"tipo_dispositivo\":\"esp32\",\"ciclo_id\":\"%s\",\"metrica\":\"%s\",\"unidade\":\"%s\",\"valor\":%.2f,\"status\":\"%s\"}",
            esc_ev, esc_disp, esc_ciclo, esc_metr, esc_unid, valor, esc_stat
        );
    }

    if (n < 0 || static_cast<size_t>(n) >= tam) {
        return -1;
    }
    return n;
}

#endif // LOGICA_H
