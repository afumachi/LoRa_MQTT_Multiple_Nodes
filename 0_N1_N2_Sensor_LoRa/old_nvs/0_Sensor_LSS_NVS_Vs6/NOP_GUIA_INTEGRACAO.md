# GUIA DE INTEGRAÇÃO - CONFIGURAÇÃO OTIMIZADA LORA COM NVS

## 📋 RESUMO DA IMPLEMENTAÇÃO

Esta solução otimiza o firmware do nó sensor LoRa economizando bytes e memória através de:

1. **Tabela LUT (Look-Up Table)**: 72 combinações indexadas (0-71)
2. **NVS com Wear Leveling**: 100 slots rotativos para persistência
3. **Economia de Bytes**: PacoteDL[0] agora recebe apenas 1 byte (índice) em vez de 3 bytes separados
4. **Carregamento Automático**: Na primeira inicialização e reinicialização
5. **Compatibilidade Total**: Mantém lógica MAC existente intacta

---

## 🔧 PASSO 1: Adicionar o Header ao Projeto

1. Copie os arquivos para a pasta do projeto Arduino:
   - `RadioConfigOptimized.h` → mesma pasta do sketch principal
   - `RadioConfigLUT_Corrigido.h` → mesma pasta do sketch principal

2. No arquivo `Bibliotecas.h`, ADICIONE no final:

```cpp
#include "RadioConfigLUT_Corrigido.h"  // Tabela LUT das 72 configurações

// ============================================================
// NVS E GERENCIADOR DE CONFIGURAÇÃO DE RÁDIO
// ============================================================
#include "RadioConfigOptimized.h"       // Classe de persistência e aplicação
```

---

## 📝 PASSO 2: Modificar 1_PHY.ino

### A) Adicione a inicialização de NVS no primeiro_setup:

**ANTES (linhas 4-22):**
```cpp
if (primeiro_setup == 1){
    //Serial.println("Primeiro SETUP");
    LoRa.sleep();
    LoRa.setTxPower(txPower);
    LoRa.setSpreadingFactor(spreadingFactor);
    LoRa.setSignalBandwidth(signalBandwidth);
    LoRa.setCodingRate4(codingRateDenominator);
    LoRa.idle();
    // ... resto do código
}
```

**DEPOIS:**
```cpp
if (primeiro_setup == 1){
    //Serial.println("Primeiro SETUP");
    LoRa.sleep();
    
    // NOVO: Carrega configuração persistida ou padrão
    loadRadioConfigFromNVS();
    
    // Se não quiser usar NVS, descomente as linhas abaixo (fallback manual):
    // LoRa.setTxPower(txPower);
    // LoRa.setSpreadingFactor(spreadingFactor);
    // LoRa.setSignalBandwidth(signalBandwidth);
    // LoRa.setCodingRate4(codingRateDenominator);
    
    LoRa.idle(); // Retorna ao modo standby-recepção
    
    // ... resto do código
}
```

### B) Receba o índice no PacoteDL (SUBSTITUA as linhas 54-70):

**ANTES:**
```cpp
// ADICIONADO Variáveis de recebimento do valores de rádio LoRa
valor_novo_spreadingfactor = PacoteDL[0]; // Byte DL[0] valor de rádio LoRa de Spreading Spectrum
valor_novo_bandwidth = PacoteDL[1]; // Byte DL[1] valor de rádio LoRa de Bandwidth

// Configura Valor de Bandwidth de acordo com o valor recebido no Byte[1]
if (valor_novo_bandwidth == 3){
    valor_novo_bandwidth = 500E3;
}
else if (valor_novo_bandwidth == 2){
    valor_novo_bandwidth = 250E3;
}
else if (valor_novo_bandwidth == 1){
    valor_novo_bandwidth = 125E3;
}

valor_novo_codingrate = PacoteDL[2]; // Byte DL[2] valor de rádio LoRa de CodingRate
valor_novo_potencia_radio = PacoteDL[3]; // Byte DL[3] valor de rádio LoRa de Potência de Rádio LoRa
```

**DEPOIS:**
```cpp
// NOVO: Recebe índice de configuração (0-71) em PacoteDL[0]
uint8_t radio_config_index = PacoteDL[0];

// Valida índice
if (radio_config_index <= 71) {
    // Armazena índice para usar após envio UL
    Serial.printf("[RX] Índice de configuração recebido: %d\n", radio_config_index);
} else {
    Serial.printf("[RX] Índice INVÁLIDO recebido: %d (máximo: 71)\n", radio_config_index);
    radio_config_index = 60;  // Fallback para configuração padrão
}

// PacoteDL[3] continua sendo TX Power (sem alteração)
valor_novo_potencia_radio = PacoteDL[3];

// Variáveis antigas são mantidas para compatibilidade (opcional remover)
valor_novo_spreadingfactor = 0;  // Não usado mais
valor_novo_bandwidth = 0;         // Não usado mais
valor_novo_codingrate = 0;        // Não usado mais
```

### C) Aplicar configuração após envio UL (linhas 192-195):

**ANTES:**
```cpp
if (confirma_novo_radio == 1){
    AplicarConfiguracoesRadio();
}
```

**DEPOIS:**
```cpp
if (confirma_novo_radio == 1){
    // NOVO: Aplica configuração pelo índice em vez de parâmetros separados
    applyRadioConfigByIndex(radio_config_index);
    
    // Limpa flags da máquina de estado
    confirma_novo_radio_sensor = 0;
    confirma_novo_radio_base = 10;
    confirma_novo_radio = 0;
    recebe_comando_nova_radio = 0;
    primeiro_setup = 0;
    
    Serial.printf("[RADIO] Configuração %d aplicada e persistida\n", radio_config_index);
}
```

### D) Remova as funções antigas (opcional):

Pode remover ou comentar:
- `AplicarConfiguracoesRadio()` (linha 250)
- `RetornaConfiguracoesRadioMAX()` (linha 226)

---

## 📝 PASSO 3: Modificar 2_MAC.ino (MANTER IDÊNTICO)

**NENHUMA alteração necessária!** A lógica MAC permanece 100% intacta:

```cpp
// ===== PERMANECE IGUAL =====
// Quando PacoteDL[7] == 1, executa:
if ((recebe_comando_nova_radio == 1)){
    confirma_novo_radio_sensor = 2;
    // ... resto do código
}

// Mac_radio_send_UL() também permanece igual
// A máquina de estado MAC funciona normalmente
```

---

## 📝 PASSO 4: Modificar Bibliotecas.h

**REMOVA (linhas 43-53):**
```cpp
// # Configuração Atual Rádio LoRa
int valor_atual_spreadingfactor = 12;
int valor_atual_bandwidth = 125E3;
int valor_atual_codingrate = 8;
int valor_atual_potencia_radio = 20;

// # Configuração Nova Rádio LoRa
int valor_novo_spreadingfactor = 12;
int valor_novo_bandwidth = 125E3;
int valor_novo_codingrate = 8;
int valor_novo_potencia_radio = 20;
// ... resto das linhas removidas
```

**ADICIONE NO LUGAR:**
```cpp
// ============================================================
// CONFIGURAÇÕES LoRa OTIMIZADAS COM LUT
// ============================================================
uint8_t radio_config_index = 60;        // Índice da configuração (0-71)
                                         // 60 = SF12, BW125kHz, CR4/5 (default)
uint8_t valor_novo_potencia_radio = 20; // TX Power: 1-17 dBm (continua em byte 3)

// Variáveis mantidas para compatibilidade com MAC (podem ser removidas depois):
int valor_atual_spreadingfactor = 12;
int valor_atual_bandwidth = 125E3;
int valor_atual_codingrate = 8;
int valor_atual_potencia_radio = 20;
```

---

## 🎯 FLUXO DE FUNCIONAMENTO

```
INICIALIZAÇÃO
    ↓
[primeiro_setup == 1] ativa
    ↓
loadRadioConfigFromNVS()
    ├─ Verifica NVS (existe índice salvo?)
    │  ├─ SIM → Carrega índice anterior
    │  └─ NÃO → Carrega índice padrão (60: SF12/BW125/CR5)
    ├─ Aplica configuração no RFM95
    └─ primeiro_setup = 0

RECEPÇÃO DE PacoteDL
    ├─ PacoteDL[0] = índice (0-71)
    ├─ PacoteDL[7] = comando (0-5)
    └─ PacoteDL[3] = TX Power

ENVIO DE PacoteUL
    ├─ MAC executa lógica (sem alterações)
    └─ Se confirma_novo_radio == 1:
        └─ applyRadioConfigByIndex(índice)
            ├─ Aplica SF, BW, CR no RFM95
            ├─ Salva índice em NVS (wear leveling)
            └─ Próxima inicialização carregará esta config
```

---

## 💾 ECONOMIA DE MEMÓRIA

### Antes (Implementação Antiga):
- PacoteDL[0] = Spreading Factor (1 byte)
- PacoteDL[1] = Bandwidth (1 byte)
- PacoteDL[2] = Coding Rate (1 byte)
- PacoteDL[3] = TX Power (1 byte)
- **Total: 4 bytes**

### Depois (Implementação Nova):
- PacoteDL[0] = Índice de Configuração (1 byte)
- PacoteDL[1] = Livre para uso
- PacoteDL[2] = Livre para uso
- PacoteDL[3] = TX Power (1 byte)
- **Total: 2 bytes obrigatórios + 2 bytes livres**

**Economia: 2 bytes por pacote + Tabela LUT em PROGMEM (não consome RAM)**

### RAM Ocupada:
- Tabela LUT (PROGMEM, não RAM): ~288 bytes
- Classe RadioConfigNVS: ~12 bytes RAM
- **Total: ~12 bytes de RAM adicional**

---

## 🔄 WEAR LEVELING (100 SLOTS)

O NVS usa 100 slots rotativos para prolongar vida útil da EEPROM:

```
Slot 0  → Escrita 1
Slot 1  → Escrita 2
...
Slot 99 → Escrita 100
Slot 0  → Escrita 101 (rota novamente)
```

Com aproximadamente 10.000 ciclos de escrita por slot:
- **100 slots × 10.000 ciclos = 1.000.000 de alterações de configuração**

---

## 🐛 DEBUG E TESTES

### Ativar logs detalhados:

No arquivo principal, após inicializar Serial:

```cpp
void setup() {
    Serial.begin(115200);
    delay(200);
    
    // ... resto do setup ...
    
    // DEBUG: Imprimir slots de NVS
    radioConfigManager.debugPrintSlots();
    
    // DEBUG: Imprimir configuração atual
    RadioConfig config = radioConfigManager.getConfig();
    Serial.printf("[DEBUG] Config atual: SF=%d, BW=%ld Hz, CR=4/%d\n",
                  config.spreadingFactor, config.signalBandwidth, config.codingRateDenominator);
}
```

### Testar diferentes índices:

```cpp
// No loop() ou em função de teste:
void testRadioConfig() {
    for (uint8_t i = 0; i < 72; i += 12) {  // Testa a cada SF
        Serial.printf("Testando índice %d: %s\n", i, getRadioConfigDescription(i));
        applyRadioConfigByIndex(i);
        delay(1000);
    }
}
```

---

## 🔧 PROPOSTA DE OTIMIZAÇÕES ADICIONAIS

### Opção 1: Reduzir Tabela LUT para 48 combinações
Se não precisar de CR4/5 e CR4/6, pode reduzir para:
- SF: 6 valores (7-12)
- BW: 3 valores (125, 250, 500)
- CR: 2 valores (7, 8)
- **Total: 6 × 3 × 2 = 36 combinações** ou mesmo eliminar a escolha de BW e deixar apenas 4/8.

### Opção 2: Comprimir Índice em 6 bits
Se usar apenas 48-63 configurações, pode comprimir em 6 bits dentro de um byte:

```cpp
struct CompactPacketDL {
    uint8_t radio_index : 6;      // Bits 0-5: índice (0-63)
    uint8_t reserved : 2;         // Bits 6-7: reservado
    uint8_t tx_power;
    // ... resto dos bytes
};
```

**Economia: Liberta até 2 bits adicionais**

### Opção 3: Predefinir Perfis de Uso

Em vez de 72 combinações genéricas, definir apenas perfis úteis:

```cpp
enum RadioProfile {
    PROFILE_LONG_RANGE = 0,   // SF12/BW125/CR8
    PROFILE_BALANCED = 1,     // SF10/BW250/CR7
    PROFILE_HIGH_SPEED = 2,   // SF7/BW500/CR5
    PROFILE_CUSTOM = 3,       // Aceita parâmetros individuais
};
```

**Economia: PacoteDL[0] recebe apenas 2 bits (4 perfis)**

---

## ✅ CHECKLIST DE IMPLEMENTAÇÃO

- [ ] Copiar `RadioConfigOptimized.h` para a pasta do projeto
- [ ] Copiar `RadioConfigLUT_Corrigido.h` para a pasta do projeto
- [ ] Adicionar includes em `Bibliotecas.h`
- [ ] Modificar `1_PHY.ino` - Inicialização NVS
- [ ] Modificar `1_PHY.ino` - Recepção de índice
- [ ] Modificar `1_PHY.ino` - Aplicação de configuração
- [ ] Modificar `Bibliotecas.h` - Remover variáveis antigas
- [ ] Compilar e testar na primeira vez (deveria carregar SF12 padrão)
- [ ] Testar recebimento de PacoteDL com diferentes índices
- [ ] Testar persistência (reboot e verificar se mantém configuração)
- [ ] Ativar modo debug e verificar logs de NVS
- [ ] Testar wear leveling (enviar muitas reconfiguções)

---

## 📞 SUPORTE

Em caso de erros de compilação:
1. Verificar se a biblioteca `Preferences.h` está disponível (nativa do ESP32)
2. Verificar Arduino IDE versão (recomendado 1.8.19+)
3. Verificar se board "ESP32 Dev Module" está selecionado

