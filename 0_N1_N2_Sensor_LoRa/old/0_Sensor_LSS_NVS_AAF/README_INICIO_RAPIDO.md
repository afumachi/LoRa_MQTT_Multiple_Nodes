# 🚀 SISTEMA OTIMIZADO DE CONFIGURAÇÃO LoRa - INÍCIO RÁPIDO

## 📦 O QUE FOI CRIADO

Uma solução completa para economizar bytes e memoria no firmware do nó sensor LoRa, implementando:

- ✅ **Tabela LUT** com 72 combinações de parâmetros LoRa indexadas
- ✅ **Persistência em NVS** com wear leveling (100 slots rotativos)
- ✅ **Compatibilidade total** com lógica MAC existente
- ✅ **Scripts Python** para gateway calcular índices
- ✅ **Funções auxiliares** para debug e teste

---

## 📁 ARQUIVOS ENTREGUES

### 1. **RadioConfigOptimized.h** ⭐ (Principal)
Classe `RadioConfigNVS` que implementa:
- Tabela LUT comprimida em PROGMEM
- Persistência em NVS com 100 slots
- Carregamento automático na inicialização
- Debug com impressão de slots

**Usar quando:** Quiser máxima flexibilidade e funcionalidades

### 2. **RadioConfigLUT_Corrigido.h**
Tabela LUT corrigida com 72 combinações únicas:
- SF: 7-12 (6 valores)
- BW: 125kHz, 250kHz, 500kHz (3 valores)  
- CR: 4/5, 4/6, 4/7, 4/8 (4 valores)

**Usar quando:** Quiser consultar a tabela ou usá-la separadamente

### 3. **RadioConfigUtils.h**
Utilitários e funções auxiliares:
- `calculateRadioIndex()` - Calcula índice de SF/BW/CR
- `decodeRadioIndex()` - Inverte: índice → SF/BW/CR
- `getRadioConfigText()` - Descrição textual de configuração
- `suggestRadioConfigBySignalQuality()` - Sugestão automática baseada em RSSI/SNR
- Histórico de alterações

**Usar quando:** Precisar utilidades para trabalhar com índices

### 4. **gateway_radio_config_tool.py**
Ferramenta Python para o gateway (interativa):
- Menu para calcular índices
- Decodificar índices
- Visualizar tabela completa
- Montar pacotes PacoteDL personalizados

**Usar quando:** For enviar comandos do gateway para os nós

### 5. **GUIA_INTEGRACAO.md** 📖 (Essencial)
Guia passo-a-passo completo:
- Como adicionar headers ao projeto
- Modificações necessárias em cada arquivo .ino
- Fluxo de funcionamento
- Wear leveling explicado
- Checklist de implementação

**Leia primeiro!** Antes de começar a integração

### 6. **OTIMIZACOES_PROPOSTAS.md**
Análise de otimizações adicionais:
- 4 opções de compressão mais agressiva
- Comparação de economia de espaço
- Análise de casos de uso
- Roadmap de implementação

**Usar quando:** Quiser otimizações além da solução base

---

## ⚡ INÍCIO RÁPIDO (5 MINUTOS)

### Passo 1: Copie os arquivos
```bash
# Copie para a pasta do projeto Arduino
cp RadioConfigOptimized.h        ~/Arduino/seu_projeto/
cp RadioConfigLUT_Corrigido.h    ~/Arduino/seu_projeto/
cp RadioConfigUtils.h            ~/Arduino/seu_projeto/
```

### Passo 2: Modifique Bibliotecas.h
Adicione no final:
```cpp
#include "RadioConfigLUT_Corrigido.h"
#include "RadioConfigOptimized.h"
#include "RadioConfigUtils.h"
```

### Passo 3: Modifique 1_PHY.ino (linhas 4-22)
Substitua:
```cpp
if (primeiro_setup == 1){
    //Serial.println("Primeiro SETUP");
    LoRa.sleep();
    loadRadioConfigFromNVS();  // ← ADICIONE ESTA LINHA
    LoRa.idle();
    // ... resto
}
```

### Passo 4: Modifique 1_PHY.ino (linhas 54-70)
Substitua blocos de leitura de SF/BW/CR por:
```cpp
uint8_t radio_config_index = PacoteDL[0];
if (radio_config_index > 71) radio_config_index = 60;
valor_novo_potencia_radio = PacoteDL[3];
```

### Passo 5: Modifique 1_PHY.ino (linhas 193-195)
Substitua `AplicarConfiguracoesRadio()` por:
```cpp
if (confirma_novo_radio == 1){
    applyRadioConfigByIndex(radio_config_index);
    confirma_novo_radio_sensor = 0;
    confirma_novo_radio_base = 10;
    confirma_novo_radio = 0;
    recebe_comando_nova_radio = 0;
}
```

### Passo 6: Compile e teste ✅
```
Esperado: Serial mostra "[NVS] Primeira inicialização - SF=12"
```

---

## 🎯 FLUXO VISUAL

```
INICIALIZAÇÃO DO NÓ SENSOR
│
├─ Serial inicializa
│  └─ primeiro_setup = 1
│     └─ loadRadioConfigFromNVS()
│        ├─ ¿NVS vazio? (Primeira vez)
│        │  ├─ SIM: Carrega índice 60 (SF12/BW125/CR5)
│        │  └─ Salva no slot 0
│        └─ ¿NVS com dados?
│           └─ Carrega índice anterior

RECEBIMENTO DE PacoteDL DO GATEWAY
│
├─ Phy_radio_receive_DL()
│  ├─ Lê PacoteDL[0] = índice (0-71)
│  └─ Lê PacoteDL[7] = comando MAC (0-5)
│
└─ Mac_radio_receive_DL()  ← Lógica existente (sem mudanças)

ENVIO DE PacoteUL
│
├─ Mac_radio_send_UL()  ← Lógica existente (sem mudanças)
│  └─ confirma_novo_radio = 1?
│
└─ Phy_radio_send_UL()
   ├─ Envia PacoteUL
   └─ applyRadioConfigByIndex(índice)
      ├─ Aplica SF, BW, CR no RFM95
      └─ Salva índice em NVS (wear leveling)
         └─ Próximo reboot carregará esta config
```

---

## 📊 COMPARAÇÃO ANTES VS DEPOIS

### Antes
- PacoteDL[0] = SF (7-12)
- PacoteDL[1] = BW (1, 2 ou 3)
- PacoteDL[2] = CR (5, 6, 7 ou 8)
- PacoteDL[3] = Potência
- **Total: 4 bytes de config**
- ❌ Sem persistência
- ❌ Muitas variáveis redundantes

### Depois
- PacoteDL[0] = Índice (0-71)
- PacoteDL[1] = **Livre** 🎉
- PacoteDL[2] = **Livre** 🎉
- PacoteDL[3] = Potência
- **Total: 2 bytes obrigatórios + 2 livres**
- ✅ Persistência automática
- ✅ 2 bytes adicionais liberados

---

## 🔧 TESTES RECOMENDADOS

### Teste 1: Primeira Inicialização
```
Resultado esperado: Serial mostra
[NVS] Primeira inicialização - Carregando SF=12
[RADIO SETUP] Carregando índice 60 - SF:12, BW:125000 Hz, CR:4/5
```

### Teste 2: Reconfiguração
```cpp
// No seu script Python:
python3 gateway_radio_config_tool.py
[1] Calcular índice
SF: 9
BW: 250000
CR: 7
→ Resultado: Índice 28
→ Envie PacoteDL[0] = 28
```

Resultado esperado no nó:
```
[RX] Índice de configuração recebido: 28
[RADIO] Aplicando configuração - SF:9, BW:250000 Hz, CR:4/7
[NVS] Nova configuração persistida: Índice 28
```

### Teste 3: Reinicialização
```
Desconecte/reconecte o nó

Resultado esperado no serial:
[NVS] Configuração carregada: Índice 28 do slot 0
[RADIO SETUP] Carregando índice 28 - SF:9, BW:250000 Hz, CR:4/7
```

### Teste 4: Wear Leveling
```
Envie 100 alterações consecutivas de configuração

Resultado esperado:
Slots 0-99 serão preenchidos sequencialmente
[NVS] Índice 45 escrito no slot 47
[NVS] Índice 12 escrito no slot 48
...
[NVS] Índice 60 escrito no slot 0 (volta para o início)
```

---

## 🐛 TROUBLESHOOTING

### Erro: "RadioConfigOptimized.h not found"
```cpp
// Verifique:
// 1. O arquivo está na mesma pasta do .ino?
// 2. O caminho está correto no #include?
#include "RadioConfigOptimized.h"  ✅ Correto
#include <RadioConfigOptimized.h>  ❌ Errado (angle brackets)
```

### Erro: "Preferences.h not found"
```cpp
// Preferences é nativa do ESP32, mas:
// 1. Verifique se Arduino IDE tem suporte ESP32
// 2. Selecione "ESP32 Dev Module" em Tools → Board
// 3. Reinicie Arduino IDE
```

### NVS está corrompido
```cpp
// Solução: Reset completo
void setup() {
    // radioConfigManager.reset();  // ← Descomente UMA VEZ
}
// Depois comente novamente para não resetar todo reboot
```

### PacoteDL não está recebendo índice
```cpp
// Verifique:
// 1. Gateway está enviando índice em PacoteDL[0]?
// 2. Valor está entre 0-71?
// 3. Camada MAC está processando corretamente?

// Debug: Adicione em Phy_radio_receive_DL()
Serial.printf("DEBUG PacoteDL[0] recebido: %d\n", PacoteDL[0]);
```

---

## 📱 USANDO O SCRIPT PYTHON

### Instalação
```bash
# Não requer instalação (Python 3 puro)
python3 gateway_radio_config_tool.py

# Ou crie um alias
alias radio_config="python3 gateway_radio_config_tool.py"
radio_config
```

### Exemplos de Uso

**Calcular índice:**
```bash
python3 gateway_radio_config_tool.py --calculate 10 250000 7
→ Índice: 28
```

**Ver tabela:**
```bash
python3 gateway_radio_config_tool.py --table
```

**Ver presets:**
```bash
python3 gateway_radio_config_tool.py --presets
```

---

## 🎓 PRINCIPAIS APRENDIZADOS

### 1. Tabela LUT (Look-Up Table)
- Economiza bytes eliminando parâmetros redundantes
- Usa PROGMEM (Flash) em vez de RAM
- Permite adicionar configurações complicadas de forma simples

### 2. Persistência em NVS
- Salva última configuração automaticamente
- Não precisa de EEPROM externo
- Wear leveling protege contra desgaste

### 3. Máquina de Estado MAC
- Permanece 100% intacta e funcional
- Abstração permite mudanças transparentes na PHY
- Compatibilidade total com código existente

### 4. Otimizações Propostas
- 4 níveis de compressão disponíveis
- Escolha baseada em caso de uso específico
- Trade-off entre flexibilidade vs economia

---

## 📞 SUPORTE

### Problemas de Compilação?
1. Verifique includes
2. Verifique Arduino IDE versão (1.8.19+)
3. Verifique board selecionado (ESP32 Dev Module)

### Problemas de Execução?
1. Ative modo DEBUG: `radioConfigManager.debugPrintSlots();`
2. Verifique serial a 115200 baud
3. Teste com índices simples (0, 60, 71)

### Problemas de NVS?
1. `radioConfigManager.reset();` (uma vez)
2. Limpie NVS via Arduino IDE: Tools → Erase All Flash

---

## ✨ PRÓXIMOS PASSOS

- [ ] Copia arquivos para projeto
- [ ] Modifica Bibliotecas.h (adiciona includes)
- [ ] Modifica 1_PHY.ino (5 pequenas mudanças)
- [ ] Compila e testa
- [ ] Valida com múltiplos nós
- [ ] Implementa otimizações adicionais (opcional)

---

## 📚 DOCUMENTAÇÃO COMPLETA

Para detalhes completos, veja:

| Arquivo | Conteúdo |
|---------|----------|
| GUIA_INTEGRACAO.md | Passo-a-passo completo de integração |
| OTIMIZACOES_PROPOSTAS.md | 4 opções de otimização mais agressiva |
| RadioConfigOptimized.h | Código principal (classe + NVS) |
| RadioConfigUtils.h | Funções auxiliares e debug |
| gateway_radio_config_tool.py | Script interativo para gateway |

---

## 🎉 PRONTO PARA COMEÇAR!

```
1. Leia GUIA_INTEGRACAO.md
2. Copie os 3 arquivos .h
3. Faça as 5 modificações em 1_PHY.ino
4. Compile e teste
5. Aproveite 2 bytes adicionais! 🚀
```

**Tempo estimado de integração: 2-3 horas**

---

*Documento gerado para Fumachi - Pesquisador UNICAMP IoT/LoRa*

