/*
  MoT LoRa Site Survey Versão Configura Rádio | WissTek IoT
  Última versão: Branquinho / Anderson
  Hardware: PKLoRa ESP32 ou PKLoRa NodeMCU
  Nó Sensor - 
*/

//=======================================================================
// 1 - Escolha do Módulo - ESP32 ou NodeMCU
//=======================================================================

// Remova o comentário da linha referente ao módulo que você está utilizando e comente a outro

//#define PKLORA_ESP32 // HARDWARE COM ESP32
#define AAFLORA_ESP32 // HARDWARE COM ESP12E - NODEMCU

//=======================================================================
// 2 - Biblioteca - chama o arquivo Biblioteca.h
//=======================================================================

#include "Bibliotecas.h"  // Arquivo contendo declaração de bibliotecas e variáveis


//=======================================================================
// 3 - Configuração de Setup de Rádio LoRa
//=======================================================================

// ============= CAMADA FÍSICA
// Parâmetros do LoRa
#define FREQUENCY_IN_HZ       903E6    // LoRa Frequency
#define txPower               20       // TX power in dBm, defaults to 17
#define spreadingFactor       12       // ranges from 6-12,default 7
#define signalBandwidth       500E3    // signal bandwidth in Hz
#define codingRateDenominator 5        // denominator of the coding rate

#define TAMANHO_PACOTE 30

// ============== CAMADA MAC

byte PacoteDL[TAMANHO_PACOTE];
byte PacoteUL[TAMANHO_PACOTE];

// ============= CAMADA DE REDE
// Identificação do sensor e tamanho de pacote
int ID_sensor = 9; // Variável de iIdentificação do sensor que está no pacote de DL byte 8
int ID_gateway = 0;    // Variável com o ID_gateway que estará no pacote de DL byte 10

//=======================================================================
// 4 - Setup de inicialização
//=======================================================================
// Inicializa as camadas
void setup() {

  Serial.begin(115200);
  delay(200);
  Serial.println("--- Iniciando Nó Sensor LoRa ---");

  // --- Inicialização de I/O ---
  pinMode(LED_VERMELHO_PIN, OUTPUT);
  pinMode(LED_VERDE_PIN, OUTPUT);

  // Garante que os LEDs iniciem desligados
  digitalWrite(LED_VERMELHO_PIN, LOW);
  digitalWrite(LED_VERDE_PIN, LOW);

  #if defined(PKLORA_ESP32)
    digitalWrite(LED_AMARELO_PIN, LOW);

  #endif

    // --- Inicialização Módulo RF95 (LoRa) ---
  #if defined(PKLORA_ESP32)
    // 1. Remapeia e inicializa o barramento SPI com os pinos do seu Kit
    SPI.begin(SCK_PIN, MISO_PIN, MOSI_PIN, NSS_PIN);
  #endif
  
  // 2. Informa à biblioteca LoRa os pinos de controle
  LoRa.setPins(NSS_PIN, RST_PIN, DIO0_PIN);

  if (!LoRa.begin(FREQUENCY_IN_HZ)) {
    Serial.println("Erro ao iniciar módulo RFM95");
  }

  LoRa.setTxPower(txPower);
  LoRa.setSpreadingFactor(spreadingFactor);
  LoRa.setSignalBandwidth(signalBandwidth);
  LoRa.setCodingRate4(codingRateDenominator);
 
  Serial.println("LoRa Inicializado com Sucesso!");

  randomSeed(analogRead(34)); 
  
  // Pisca o LED Verde para indicar inicialização bem-sucedida
  digitalWrite(LED_VERMELHO_PIN, HIGH);
  delay(1000);
  digitalWrite(LED_VERMELHO_PIN, LOW);



} // FIM DO SETUP

//=======================================================================
//  5 - Loop de repetição
//=======================================================================
// A função loop irá executar repetidamente
void loop() {
    
  Phy_radio_send_UL();

  // Gera um número aleatório entre 100 e 1000
  // O valor máximo no random() é exclusivo, por isso usamos 1001
  int tempoAleatorio = random(100, 1001); 
  
  // Aplica o delay gerado
  delay(tempoAleatorio); 


}

