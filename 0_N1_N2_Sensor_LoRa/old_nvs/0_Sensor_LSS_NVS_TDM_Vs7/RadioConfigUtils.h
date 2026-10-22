
//=======================================================================
// UTILITÁRIOS E FUNÇÕES AUXILIARES PARA CONFIGURAÇÃO LoRa
// Calculadoras de índice, conversão de parâmetros, debug
//=======================================================================

/* aaf
#ifndef RADIO_CONFIG_UTILS_H
#define RADIO_CONFIG_UTILS_H
*/

// ========== CALCULADOR DE ÍNDICE ==========
/* aaf
 * Calcula o índice da tabela LUT a partir dos parâmetros LoRa individuais
 * 
 * Fórmula: índice = (SF-7)*12 + (BW_idx)*4 + (CR-5)
 * Onde: BW_idx = 0(125kHz), 1(250kHz), 2(500kHz)
 *       SF = 7-12, CR = 5-8
 * 
 * @param sf Spreading Factor (7-12)
 * @param bw Bandwidth em Hz (125000, 250000, 500000)
 * @param cr Coding Rate Denominator (5, 6, 7, 8)
 * @return Índice (0-71) ou 255 se parâmetros inválidos
 */

/* aaf 
uint8_t calculateRadioIndex(uint8_t sf, uint32_t bw, uint8_t cr) {
    // Validação de Spreading Factor (7-12)
    if (sf < 7 || sf > 12) {
        Serial.printf("[ERROR] SF inválido: %d (deve ser 7-12)\n", sf);
        return 255;
    }

    // Validação e cálculo de Bandwidth
    uint8_t bw_idx;
    if (bw == 125000) {
        bw_idx = 0;
    } else if (bw == 250000) {
        bw_idx = 1;
    } else if (bw == 500000) {
        bw_idx = 2;
    } else {
        Serial.printf("[ERROR] BW inválido: %ld Hz (deve ser 125000, 250000 ou 500000)\n", bw);
        return 255;
    }

    // Validação de Coding Rate (5-8)
    if (cr < 5 || cr > 8) {
        Serial.printf("[ERROR] CR inválido: %d (deve ser 5-8)\n", cr);
        return 255;
    }

    // Cálculo do índice
    uint8_t index = (sf - 7) * 12 + bw_idx * 4 + (cr - 5);
    
    if (index > 71) {
        Serial.printf("[ERROR] Índice calculado fora do intervalo: %d\n", index);
        return 255;
    }
    
    return index;
}
*/
// ========== DECODIFICADOR DE ÍNDICE ==========
/*
 * Decodifica um índice para seus parâmetros constituintes
 * 
 * @param index Índice (0-71)
 * @param sf Pointer para armazenar Spreading Factor
 * @param bw Pointer para armazenar Bandwidth
 * @param cr Pointer para armazenar Coding Rate Denominator
 * @return true se decodificação bem-sucedida, false se índice inválido
 */

/* aaf
bool decodeRadioIndex(uint8_t index, uint8_t* sf, uint32_t* bw, uint8_t* cr) {
    if (index > 71) {
        Serial.printf("[ERROR] Índice inválido: %d (máximo: 71)\n", index);
        return false;
    }

    // Decodifica usando a fórmula inversa
    *sf = 7 + (index / 12);           // Spreading Factor (7-12)
    uint8_t bw_idx = (index % 12) / 4; // Bandwidth index (0, 1, 2)
    *cr = 5 + (index % 4);             // Coding Rate Denominator (5-8)

    // Converte bandwidth index para valor real
    switch (bw_idx) {
        case 0: *bw = 125000; break;
        case 1: *bw = 250000; break;
        case 2: *bw = 500000; break;
        default: return false;
    }

    return true;
}
*/
// ========== TABELA DE REFERÊNCIA RÁPIDA ==========
/**
 * Retorna uma descrição textual da configuração para um índice
 * Útil para debug e logging
 * 
 * @param index Índice (0-71)
 * @return Pointer para string estática com descrição
 */
 /* aaf
const char* getRadioConfigText(uint8_t index) {
    static char buffer[96];
    
    if (index > 71) {
        snprintf(buffer, sizeof(buffer), "ERRO: Índice %d inválido", index);
        return buffer;
    }

    uint8_t sf;
    uint32_t bw;
    uint8_t cr;
    
    if (!decodeRadioIndex(index, &sf, &bw, &cr)) {
        return "ERRO: Falha ao decodificar";
    }

    snprintf(buffer, sizeof(buffer), 
             "Idx %2d | SF %2d | BW %6ld kHz | CR 4/%d",
             index, sf, bw / 1000, cr);
    
    return buffer;
}
*/
// ========== TABELA AUXILIAR - ÍNDICES PRÉ-CALCULADOS ==========
/**
 * Índices pré-calculados para configurações comuns
 * Evita cálculos em runtime
 */
 /* aaf
struct CommonRadioConfigs {
    static constexpr uint8_t LONG_RANGE_125_8 = 63;   // SF12, BW125k, CR4/8
    static constexpr uint8_t LONG_RANGE_125_5 = 60;   // SF12, BW125k, CR4/5 (DEFAULT)
    static constexpr uint8_t BALANCED = 37;           // SF10, BW250k, CR4/7
    static constexpr uint8_t HIGH_SPEED = 2;          // SF7, BW500k, CR4/7
    static constexpr uint8_t MAX_RANGE = 71;          // SF12, BW500k, CR4/8
};
*/
// ========== VALIDADOR DE CONFIGURAÇÃO ==========
/**
 * Valida se uma configuração é válida e recomendada
 * 
 * @param index Índice a validar
 * @return true se válido, false caso contrário
 */
 /* aaf
bool isValidRadioIndex(uint8_t index) {
    return (index <= 71);
}
*/
// ========== FUNÇÃO DE DEBUG COMPLETA ==========
/**
 * Imprime tabela completa de configurações disponíveis (use apenas para debug)
 * Recomendado: comentar após testes
 */
 /* aaf
void printAllRadioConfigs() {
    Serial.println("\n========== TABELA COMPLETA DE CONFIGURAÇÕES LORA (72) ==========");
    
    for (uint8_t i = 0; i < 72; i++) {
        uint8_t sf;
        uint32_t bw;
        uint8_t cr;
        
        if (decodeRadioIndex(i, &sf, &bw, &cr)) {
            Serial.printf("%s\n", getRadioConfigText(i));
            
            // Quebra de linha a cada SF (a cada 12 índices)
            if ((i + 1) % 12 == 0) {
                Serial.println("---");
            }
        }
    }
    Serial.println("==============================================================\n");
}
*/
// ========== MONITOR DE ALTERAÇÕES ==========
/**
 * Estrutura para rastrear histórico de alterações de configuração
 * Útil para debug e diagnóstico
 */
 /* aaf
struct RadioConfigHistory {
    static constexpr uint8_t MAX_HISTORY = 20;
    
    struct HistoryEntry {
        uint8_t index;
        uint32_t timestamp;
    };
    
    HistoryEntry history[MAX_HISTORY];
    uint8_t history_count;
    
    RadioConfigHistory() : history_count(0) {}
    
    void recordChange(uint8_t index) {
        if (history_count < MAX_HISTORY) {
            history[history_count].index = index;
            history[history_count].timestamp = millis();
            history_count++;
        } else {
            // Desloca histórico (FIFO)
            for (int i = 0; i < MAX_HISTORY - 1; i++) {
                history[i] = history[i + 1];
            }
            history[MAX_HISTORY - 1].index = index;
            history[MAX_HISTORY - 1].timestamp = millis();
        }
    }
    
    void printHistory() {
        Serial.println("\n========== HISTÓRICO DE ALTERAÇÕES ==========");
        for (uint8_t i = 0; i < history_count; i++) {
            Serial.printf("  %d. Índice %2d - T=%lu ms - %s\n",
                         i + 1, 
                         history[i].index,
                         history[i].timestamp,
                         getRadioConfigText(history[i].index));
        }
        Serial.println("==========================================\n");
    }
    
    void clear() {
        history_count = 0;
    }
};
*/
// ========== VALIDADOR DE QUALIDADE DE LINK ==========
/**
 * Sugere uma configuração ótima baseada em RSSI e SNR
 * Usa heurística simples: pior sinal = maior SF
 */
 /* aaf
uint8_t suggestRadioConfigBySignalQuality(int16_t rssi, int8_t snr) {
    // RSSI: -30 (excelente) a -120 (péssimo)
    // SNR: 10 (excelente) a -20 (péssimo)
    
    uint8_t suggested_sf;
    uint32_t suggested_bw;
    uint8_t suggested_cr;
    
    // Baseado em RSSI (prioridade principal)
    if (rssi > -80) {
        suggested_sf = 7;     // Sinal forte: SF mínimo
        suggested_bw = 500000;
        suggested_cr = 5;
    } else if (rssi > -90) {
        suggested_sf = 9;     // Sinal médio
        suggested_bw = 250000;
        suggested_cr = 6;
    } else if (rssi > -100) {
        suggested_sf = 10;    // Sinal fraco
        suggested_bw = 250000;
        suggested_cr = 7;
    } else {
        suggested_sf = 12;    // Sinal muito fraco
        suggested_bw = 125000;
        suggested_cr = 8;     // Máxima robustez
    }
    
    return calculateRadioIndex(suggested_sf, suggested_bw, suggested_cr);
}
*/
// ========== COMPARADOR DE CONFIGURAÇÕES ==========
/**
 * Compara dois índices e retorna a diferença em termos de robustez
 * Número positivo: primeira config é mais robusta
 * Número negativo: segunda config é mais robusta
 */
/* aaf
int8_t compareRobustness(uint8_t index1, uint8_t index2) {
    if (index1 > 71 || index2 > 71) return 0;
    
    // SF tem maior peso (8x), depois CR (1x), BW não muda robustez (mesma throughput)
    int8_t sf_diff = ((index1 / 12) - (index2 / 12)) * 8;
    int8_t cr_diff = ((index1 % 4) - (index2 % 4)) * 1;
    
    return sf_diff + cr_diff;
}

#endif // RADIO_CONFIG_UTILS_H

*/