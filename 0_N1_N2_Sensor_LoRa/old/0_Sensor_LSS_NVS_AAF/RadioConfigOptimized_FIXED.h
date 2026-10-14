//=======================================================================
// RADIO CONFIGURATION LOOKUP TABLE - OTIMIZADO COM NVS E WEAR LEVELING
// VERSÃO CORRIGIDA - sem redefinições, compatível com ESP32
//=======================================================================

#ifndef RADIO_CONFIG_OPTIMIZED_H
#define RADIO_CONFIG_OPTIMIZED_H

#include <Preferences.h>  // Biblioteca NVS (Non-Volatile Storage)

// ========== ESTRUTURA DE DADOS COMPRIMIDA ==========
// Cada configuração de rádio ocupa apenas 3 bytes em vez de 12 bytes
struct RadioConfig {
    uint8_t spreadingFactor;      // 7-12 (6 valores)
    uint32_t signalBandwidth;     // 125000, 250000, 500000 (3 valores)
    uint8_t codingRateDenominator; // 5, 6, 7, 8 (4 valores)
};

// ========== TABELA LUT - 72 COMBINAÇÕES INDEXADAS ==========
// Organização: Índice 0-71 mapeia direto para SF+BW+CR
// Reduz de 12 bytes para apenas 1 byte (índice) no PacoteDL[0]
const RadioConfig RADIO_CONFIG_LUT[72] PROGMEM = {

    // ===== SF=7 (Índices 0-11) =====
    // BW=125kHz (Índices 0-3): CR 5,6,7,8
    {7, 125000, 5}, {7, 125000, 6}, {7, 125000, 7}, {7, 125000, 8},
    // BW=250kHz (Índices 4-7): CR 5,6,7,8
    {7, 250000, 5}, {7, 250000, 6}, {7, 250000, 7}, {7, 250000, 8},
    // BW=500kHz (Índices 8-11): CR 5,6,7,8
    {7, 500000, 5}, {7, 500000, 6}, {7, 500000, 7}, {7, 500000, 8},
 
    // ===== SF=8 (Índices 12-23) =====
    // BW=125kHz (Índices 12-15): CR 5,6,7,8
    {8, 125000, 5}, {8, 125000, 6}, {8, 125000, 7}, {8, 125000, 8},
    // BW=250kHz (Índices 16-19): CR 5,6,7,8
    {8, 250000, 5}, {8, 250000, 6}, {8, 250000, 7}, {8, 250000, 8},
    // BW=500kHz (Índices 20-23): CR 5,6,7,8
    {8, 500000, 5}, {8, 500000, 6}, {8, 500000, 7}, {8, 500000, 8},
 
    // ===== SF=9 (Índices 24-35) =====
    // BW=125kHz (Índices 24-27): CR 5,6,7,8
    {9, 125000, 5}, {9, 125000, 6}, {9, 125000, 7}, {9, 125000, 8},
    // BW=250kHz (Índices 28-31): CR 5,6,7,8
    {9, 250000, 5}, {9, 250000, 6}, {9, 250000, 7}, {9, 250000, 8},
    // BW=500kHz (Índices 32-35): CR 5,6,7,8
    {9, 500000, 5}, {9, 500000, 6}, {9, 500000, 7}, {9, 500000, 8},
 
    // ===== SF=10 (Índices 36-47) =====
    // BW=125kHz (Índices 36-39): CR 5,6,7,8
    {10, 125000, 5}, {10, 125000, 6}, {10, 125000, 7}, {10, 125000, 8},
    // BW=250kHz (Índices 40-43): CR 5,6,7,8
    {10, 250000, 5}, {10, 250000, 6}, {10, 250000, 7}, {10, 250000, 8},
    // BW=500kHz (Índices 44-47): CR 5,6,7,8
    {10, 500000, 5}, {10, 500000, 6}, {10, 500000, 7}, {10, 500000, 8},
 
    // ===== SF=11 (Índices 48-59) =====
    // BW=125kHz (Índices 48-51): CR 5,6,7,8
    {11, 125000, 5}, {11, 125000, 6}, {11, 125000, 7}, {11, 125000, 8},
    // BW=250kHz (Índices 52-55): CR 5,6,7,8
    {11, 250000, 5}, {11, 250000, 6}, {11, 250000, 7}, {11, 250000, 8},
    // BW=500kHz (Índices 56-59): CR 5,6,7,8
    {11, 500000, 5}, {11, 500000, 6}, {11, 500000, 7}, {11, 500000, 8},
 
    // ===== SF=12 (Índices 60-71) - MÁXIMA DISTÂNCIA =====
    // BW=125kHz (Índices 60-63): CR 5,6,7,8
    {12, 125000, 5}, {12, 125000, 6}, {12, 125000, 7}, {12, 125000, 8},
    // BW=250kHz (Índices 64-67): CR 5,6,7,8
    {12, 250000, 5}, {12, 250000, 6}, {12, 250000, 7}, {12, 250000, 8},
    // BW=500kHz (Índices 68-71): CR 5,6,7,8
    {12, 500000, 5}, {12, 500000, 6}, {12, 500000, 7}, {12, 500000, 8},

};

// ========== CONFIGURAÇÕES DE NVS COM WEAR LEVELING ==========
class RadioConfigNVS {
    
private:
    Preferences nvs;
    static constexpr uint8_t NVS_SLOTS = 100;           // 100 slots rotativos
    static constexpr uint8_t NVS_MAX_INDEX = 71;        // Máximo índice válido (72 configs)
    static constexpr uint8_t DEFAULT_INDEX = 63;        // Índice padrão: SF=12, BW=125kHz, CR=4/8
    static constexpr const char* NVS_NAMESPACE = "RadioConfig";
    static constexpr const char* NVS_COUNTER_KEY = "slot_counter";
    
    uint8_t current_slot;                           // Slot atual (0-99)
    uint8_t current_index;                          // Índice de configuração atual (0-71)

public:
    RadioConfigNVS() : current_slot(0), current_index(DEFAULT_INDEX) {}

    // ========== INICIALIZAÇÃO ==========
    void begin() {
        nvs.begin(NVS_NAMESPACE, false);  // false = modo read/write
        
        // Verifica se é primeira vez (não há counter no NVS)
        if (!nvs.isKey(NVS_COUNTER_KEY)) {
            Serial.println("[NVS] Primeira inicialização - Carregando configuração padrão (SF=12)");
            writeIndex(DEFAULT_INDEX);  // Salva índice padrão no slot 0
            current_index = DEFAULT_INDEX;
        } else {
            loadLatestIndex();           // Carrega último índice salvo
        }
    }

    // ========== ESCRITA COM WEAR LEVELING ==========
    void writeIndex(uint8_t index) {
        if (index > NVS_MAX_INDEX) {
            Serial.printf("[NVS] Erro: Índice %d inválido (máximo: %d)\n", index, NVS_MAX_INDEX);
            return;
        }

        // Incrementa contador de slot (wear leveling)
        uint16_t slot_counter = nvs.getUShort(NVS_COUNTER_KEY, 0);
        current_slot = (slot_counter % NVS_SLOTS);

        // Monta chave dinâmica: "index_slot_0", "index_slot_1", etc
        char key[16];
        snprintf(key, sizeof(key), "index_slot_%d", current_slot);

        // Escreve índice no NVS
        nvs.putUChar(key, index);
        nvs.putUShort(NVS_COUNTER_KEY, slot_counter + 1);  // Incrementa para próximo slot
        // CORRIGIDO: Preferences não tem commit(), apenas end()
        nvs.end();
        nvs.begin(NVS_NAMESPACE, false);  // Reabre para leitura

        current_index = index;
        Serial.printf("[NVS] Índice %d escrito no slot %d\n", index, current_slot);
    }

    // ========== LEITURA COM WEAR LEVELING ==========
    void loadLatestIndex() {
        uint16_t slot_counter = nvs.getUShort(NVS_COUNTER_KEY, 0);
        
        // O slot mais recente é o anterior ao contador atual
        for (int i = 0; i < NVS_SLOTS; i++) {
            int slot_to_check = (slot_counter - 1 - i) % NVS_SLOTS;
            if (slot_to_check < 0) slot_to_check += NVS_SLOTS;

            char key[16];
            snprintf(key, sizeof(key), "index_slot_%d", slot_to_check);

            if (nvs.isKey(key)) {
                uint8_t index = nvs.getUChar(key, DEFAULT_INDEX);
                if (index <= NVS_MAX_INDEX) {
                    current_index = index;
                    current_slot = slot_to_check;
                    Serial.printf("[NVS] Configuração carregada: Índice %d do slot %d\n", 
                                  current_index, slot_to_check);
                    return;
                }
            }
        }

        // Fallback: nenhum índice válido encontrado
        current_index = DEFAULT_INDEX;
        Serial.println("[NVS] Nenhuma configuração válida encontrada - Usando padrão");
    }

    // ========== GETTER DO ÍNDICE ATUAL ==========
    uint8_t getIndex() {
        return current_index;
    }

    // ========== GETTER DA CONFIGURAÇÃO ==========
    RadioConfig getConfig(uint8_t index = 255) {
        if (index == 255) index = current_index;  // Usa índice atual se não especificado
        
        if (index > NVS_MAX_INDEX) {
            Serial.printf("[NVS] Índice %d inválido - Retornando padrão\n", index);
            index = DEFAULT_INDEX;
        }

        RadioConfig config;
        memcpy_P(&config, &RADIO_CONFIG_LUT[index], sizeof(RadioConfig));
        return config;
    }

    // ========== DEBUG: Listar todos os slots ==========
    void debugPrintSlots() {
        Serial.println("\n[NVS DEBUG] Conteúdo dos slots:");
        for (uint8_t i = 0; i < NVS_SLOTS; i++) {
            char key[16];
            snprintf(key, sizeof(key), "index_slot_%d", i);
            if (nvs.isKey(key)) {
                uint8_t index = nvs.getUChar(key);
                Serial.printf("  Slot %2d: Índice %2d\n", i, index);
            }
        }
        Serial.printf("  Contador: %d\n", nvs.getUShort(NVS_COUNTER_KEY, 0));
        Serial.println();
    }

    // ========== RESET COMPLETO ==========
    void reset() {
        nvs.clear();
        current_index = DEFAULT_INDEX;
        current_slot = 0;
        writeIndex(DEFAULT_INDEX);
        Serial.println("[NVS] Configurações resetadas para padrão");
    }
};

//=======================================================================
// VARIÁVEIS GLOBAIS
//=======================================================================
RadioConfigNVS radioConfigManager;  // Instância global

//=======================================================================
// FUNÇÕES DE INTEGRAÇÃO COM O FIRMWARE EXISTENTE
//=======================================================================

/**
 * Função para aplicar configuração pelo índice
 * Deve ser chamada em Phy_radio_send_UL() após PacoteUL ser enviado
 */
void applyRadioConfigByIndex(uint8_t index) {
    
    RadioConfig config = radioConfigManager.getConfig(index);
    
    Serial.printf("[RADIO] Aplicando configuração - SF:%d, BW:%ld Hz, CR:4/%d\n",
                  config.spreadingFactor, config.signalBandwidth, config.codingRateDenominator);
    
    LoRa.sleep();  // Coloca em sleep para garantir a mudança de parâmetros
    LoRa.setSpreadingFactor(config.spreadingFactor);
    LoRa.setSignalBandwidth(config.signalBandwidth);
    LoRa.setCodingRate4(config.codingRateDenominator);
    LoRa.idle();   // Retorna ao modo standby/recepção
    
    // Salva na NVS apenas se foi alterado
    if (radioConfigManager.getIndex() != index) {
        radioConfigManager.writeIndex(index);
        Serial.printf("[NVS] Nova configuração persistida: Índice %d\n", index);
    }
}

/**
 * Função para carregar configuração na inicialização
 * Deve ser chamada em setup() ou no primeiro ciclo de Phy_radio_receive_DL()
 */
void loadRadioConfigFromNVS() {
    radioConfigManager.begin();  // Inicializa NVS
    
    uint8_t index = radioConfigManager.getIndex();
    RadioConfig config = radioConfigManager.getConfig(index);
    
    Serial.printf("[RADIO SETUP] Carregando índice %d - SF:%d, BW:%ld Hz, CR:4/%d\n",
                  index, config.spreadingFactor, config.signalBandwidth, config.codingRateDenominator);
    
    LoRa.sleep();
    LoRa.setSpreadingFactor(config.spreadingFactor);
    LoRa.setSignalBandwidth(config.signalBandwidth);
    LoRa.setCodingRate4(config.codingRateDenominator);
    LoRa.idle();
}

/**
 * Retorna descrição textual da configuração
 */
const char* getRadioConfigDescription(uint8_t index) {
    static char buffer[64];
    if (index > 71) return "ÍNDICE INVÁLIDO";
    
    RadioConfig config = radioConfigManager.getConfig(index);
    snprintf(buffer, sizeof(buffer), "SF%d | BW%ld kHz | CR4/%d",
             config.spreadingFactor,
             config.signalBandwidth / 1000,
             config.codingRateDenominator);
    return buffer;
}

#endif // RADIO_CONFIG_OPTIMIZED_H

