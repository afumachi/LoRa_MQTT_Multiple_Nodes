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

#define AFLORA_ESP32 // HARDWARE COM ESP32
//#define PKLORA_NODEMCU // HARDWARE COM ESP12E - NODEMCU

// Caso tenha sensor GPS integrado ao Módulo
#define SEM_GPS // MoT 20 Bytes
//#define GPS_INTEGRADO // MoT 30 Bytes

//=======================================================================
// 2 - Biblioteca - chama o arquivo Biblioteca.h
//=======================================================================

#include "Bibliotecas.h"  // Arquivo contendo declaração de bibliotecas e variáveis

/*
// Máquina de Estado_DL:
// 10 => Estado Inicial Sem Enlace - Sem Recepção de DL - Sem request UL (standy-by)
// confirma_novo_radio_base = 10; // AAF 17-09 inicio do Estado_DL == 10

// 1 => Mudança de Rádio request UL

// 3 => Teste de Enlace request UL

// 4 => LSS request UL

// 5 => LSS último Pacote request UL
// após send UL, confirma_novo_radio_base = 10;

*/

//=======================================================================
// 3 - Configuração de Setup de Rádio LoRa
//=======================================================================

// ============= CAMADA FÍSICA
// Parâmetros do LoRa
#define FREQUENCY_IN_HZ       903E6    // LoRa Frequency
#define txPower                  14       // TX power in dBm, defaults to 17
#define spreadingFactorSetup       12       // ranges from 6-12,default 7
#define signalBandwidthSetup       125E3    // signal bandwidth in Hz
#define codingRateDenominatorSetup 8        // denominator of the coding rate

#define TAMANHO_PACOTE 20

// Habilita ou disabilita o uso CRC, por padrão o CRC não é usado.
//#define loraCRC

// Váriáveis utilizadas no código
int RSSI_dBm_DL; // Variável com a potência rádio recebida (RSSI) em dBm
int RSSI_DL;     // Variável de mapeamento da RSSI em um valor de 0 a 255 para colocar no pacote

float SNR_DL_bruto;   // Variável com a relação sinal ruído
uint8_t SNR_DL;           // Variável inteira para enviar a SNR, que será convertida para a SNR original no Python

// ============== CAMADA MAC

byte PacoteDL[TAMANHO_PACOTE];
byte PacoteUL[TAMANHO_PACOTE];

// ============= CAMADA DE REDE
// Identificação do sensor e tamanho de pacote
int ID_sensor = 3; // Variável de iIdentificação do sensor que está no pacote de DL byte 8
int ID_gateway = 0;    // Variável com o ID_gateway que estará no pacote de DL byte 10

// ============== CAMADA DE TRANSPORTE
int contador_pkt_DL = 0; // Variável para o contador de pacotes de DL
int contador_pkt_UL = 0; // Variável para o contador de pacotes de UL
uint16_t contadorUL = 0;
uint16_t contadorDL = 0;
uint16_t contadorSS = 0;

int luminosidade; // Variável que vai receber o valor da luminosidade entre 0 e 4095 - ADC 12 bits
uint8_t feedback_led_amarelo = 0;


// Variáveis de controle de tempo
unsigned long tempoAnterior = 0;   // Armazena o último momento em que o LED mudou de estado
const long intervalo = 100;        // Intervalo de tempo desejado (100 milissegundos)

// Variável para armazenar o estado atual do LED
int estadoLed = LOW;

// 1. Criamos uma estrutura para expor o ponteiro de função privada em tempo de compilação
template<typename Tag, typename Tag::type M>
struct ObtorPrivado {
  friend typename Tag::type pegar_metodo(Tag) { return M; }
};

struct LoRaReadRegTag {
  typedef uint8_t (LoRaClass::*type)(uint8_t);
  friend type pegar_metodo(LoRaReadRegTag);
};

// Força a instanciação do ponteiro para a função privada burlando o acesso
template struct ObtorPrivado<LoRaReadRegTag, &LoRaClass::readRegister>;

// 2. Esta é a função que você chamará no seu código
uint8_t lerRegistradorLoRa(uint8_t endereco) {
  auto metodo_privado = pegar_metodo(LoRaReadRegTag());
  return (LoRa.*metodo_privado)(endereco);
}

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
  
  #if defined(PKLORA_ESP32)
    pinMode(BOTAO_PIN, INPUT); 
    pinMode(LED_AMARELO_PIN, OUTPUT);
    // Configuração ADC para o LDR
    analogReadResolution(12);
    analogSetAttenuation(ADC_11db);
  #endif

  // Garante que os LEDs iniciem desligados
  digitalWrite(LED_VERMELHO_PIN, LOW);
  digitalWrite(LED_VERDE_PIN, LOW);

  #if defined(PKLORA_ESP32)
    digitalWrite(LED_AMARELO_PIN, LOW);

  #endif


  #if defined(GPS_INTEGRADO)
    // GPS Serial: Baud 9600, Pins: RX=16, TX=17
    SerialGPS.begin(9600, SERIAL_8N1, 16, 17);

    // Initialize I2C with your specific pins (SDA = 21, SCL = 22)
    Wire.begin(21, 22);
    delay(100);

    // Initialize OLED display
    if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { // 0x3C is common I2C address
      Serial.println(F("SSD1306 allocation failed"));
      for(;;); 
    }
    
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    delay(100);

  #endif


    // --- Inicialização Módulo RF95 (LoRa) ---
  #if defined(AFLORA_ESP32)
    // 1. Remapeia e inicializa o barramento SPI com os pinos do seu Kit
    SPI.begin(SCK_PIN, MISO_PIN, MOSI_PIN, NSS_PIN);
  #endif
  
  // 2. Informa à biblioteca LoRa os pinos de controle
  LoRa.setPins(NSS_PIN, RST_PIN, DIO0_PIN);

  if (!LoRa.begin(FREQUENCY_IN_HZ)) {
    Serial.println("Erro ao iniciar módulo RFM95");
  }

// CONFIGURAÇÕES DE RÁDIO LORA NA CAMADA FÍSICA - 1_PHY.ino
/*
  LoRa.setTxPower(txPower);
  LoRa.setSpreadingFactor(spreadingFactor);
  LoRa.setSignalBandwidth(signalBandwidth);
  LoRa.setCodingRate4(codingRateDenominator);

*/
 
  Serial.println("LoRa Inicializado com Sucesso!");

  #if defined(GPS_INTEGRADO)
    // Limpa o Display
    display.clearDisplay();
      
    // Escreve o Título Display
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.println("PKLoRa Site Survey");
    display.drawLine(0, 12, 128, 12, SSD1306_WHITE);    

    // Escreve valor do LDR
    display.setTextSize(1);
    display.setCursor(0, 17);
    display.println("PKLoRa Inicializado");
    display.println("");  
    display.setTextSize(2);
    display.println("SUCESSO!"); 

    // Escreve o buffer na tela Oled
    display.display();
  #endif


  #ifdef loraCRC   // Habilitação do CRC do chip lora  (Configurado em bibliotecas.h)
    LoRa.enableCrc();
  #endif

    // DEBUG: Imprimir slots de NVS
    radioConfigManager.debugPrintSlots();
    
    // DEBUG: Imprimir configuração atual
    RadioConfig config = radioConfigManager.getConfig();
    Serial.printf("[DEBUG] Config atual: SF=%d, BW=%ld Hz, CR=4/%d\n",
                  config.spreadingFactor, config.signalBandwidth, config.codingRateDenominator);

  // Pisca o LED Verde para indicar inicialização bem-sucedida
  digitalWrite(LED_VERDE_PIN, HIGH);
  delay(2000);
  digitalWrite(LED_VERDE_PIN, LOW);

} // FIM DO SETUP

//=======================================================================
//  5 - Loop de repetição
//=======================================================================
// A função loop irá executar repetidamente
void loop() {
    
  // --- Controle de timeout do Comando 4 ---
  // Executado a cada iteração do loop, independente de novo pacote chegar
  if (controle_ativo) {
    unsigned long tempo_limite_ms = (unsigned long)tempo_radio * 100UL * 1000UL; // 10x o valor recebido em MAC3_TEMPO

    if (millis() - millis_inicio_controle >= tempo_limite_ms) {
      //reset_para_setup_inicial(); // Timeout atingido → volta ao SETUP
    }
    millis_inicio_controle = millis();
  }


  unsigned long tempo_standby_ms = 10UL * time_out_lora_dl; // 10 min. sem Pacotes DL sobe para MAX  

  if ((millis() - millis_standby_controle >= tempo_standby_ms)) {
    Serial.println("TEMPO SEM RECEBER PACOTES - Time-Out");
    Serial.println("Voltando a Configuração LoRa MDC");
    millis_standby_controle = millis();
    //reset_para_setup_inicial(); // Timeout atingido → volta ao SETUP
  }     


  #if defined(GPS_INTEGRADO)
    // Lê os caracteres do GPS a cada 200 [ms]
    unsigned long tempo_sensores_ms = 200UL; // 200 ms

    if (millis() - millis_gps_controle >= tempo_sensores_ms) {        
      updateGPS(); // Atualiza / Lê GPS
      //Serial.println("FUNÇÃO UPDATE GPS");  
      // Zera contagem do tempo de controle GPS para tempo de ESP32 rodando
      millis_gps_controle = millis(); 
    }
  #endif

  Phy_radio_receive_DL(); // Função que recebe os pacotes pelo rádio

/*
  unsigned long tempo_pacoteDL_ms = (unsigned long)tempo_radio * 1UL * 1500UL; // 1,5x o valor recebido em MAC3_TEMPO


  if ((confirma_novo_radio_base != 10) & ((millis() - millis_contador_DL) >= tempo_pacoteDL_ms)) {
    millis_contador_DL = millis();
    Perda_DL = 1;
    Transp_radio_receive_DL();
  }

*/

  // Imprime Radio Config a cada 10 [s]
  unsigned long tempo_loop_ms = 10000UL;  

  if (millis() - millis_radio_control >= tempo_loop_ms) {        

    // 1. Lê diretamente a memória do chip usando a função bypass
    uint8_t regModemConfig1 = lerRegistradorLoRa(0x1D); // Controla Bandwidth e Coding Rate
    uint8_t regModemConfig2 = lerRegistradorLoRa(0x1E); // Controla Spreading Factor

    // 2. Processamento matemático dos bits (Máscaras de bits para o chip SX127x)
    int sfAtual = regModemConfig2 >> 4; 
    int crAtual = ((regModemConfig1 & 0x0E) >> 1) + 4; // Extrai o Coding Rate (Retorna 5 para 4/5, 6 para 4/6...)

    // 3. Extração do Bandwidth (Bits 7-4 do reg 0x1D)
    uint8_t bwCodigo = regModemConfig1 >> 4;
    float bwRealkHz = 0;
    switch (bwCodigo) {
      case 0: bwRealkHz = 7.8;   break;
      case 1: bwRealkHz = 10.4;  break;
      case 2: bwRealkHz = 15.6;  break;
      case 3: bwRealkHz = 20.8;  break;
      case 4: bwRealkHz = 31.25; break;
      case 5: bwRealkHz = 41.7;  break;
      case 6: bwRealkHz = 62.5;  break;
      case 7: bwRealkHz = 125.0; break;
      case 8: bwRealkHz = 250.0; break;
      case 9: bwRealkHz = 500.0; break;
    }

    // 4. Impressão limpa no Serial Monitor
    Serial.println(F("\n====== DADOS DO REGISTRADOR EM TEMPO REAL ======"));
    Serial.print(F("Spreading Factor (SF): ")); Serial.println(sfAtual);
    Serial.print(F("Bandwidth (BW):        ")); Serial.print(bwRealkHz); Serial.println(F(" kHz"));
    Serial.print(F("Coding Rate (CR):      4/")); Serial.println(crAtual);
    Serial.println(F("================================================"));

  // Zera contagem do tempo de controle MQTT para tempo de ESP32 rodando
  millis_radio_control = millis(); 

  }


  // Obtém o tempo atual desde que o ESP32 foi ligado
  unsigned long tempoAtual = millis();

  // Verifica se a diferença entre o tempo atual e o último registro é maior ou igual ao intervalo
  if (tempoAtual - tempoAnterior >= intervalo) {
    // Salva o momento atual como o último momento modificado
    tempoAnterior = tempoAtual;

    // Inverte o estado do LED (se estava ligado, desliga; se estava desligado, liga)
    if (estadoLed == LOW) {
      estadoLed = HIGH;
    } else {
      estadoLed = LOW;
    }

    // Aplica o novo estado ao pino do LED
    digitalWrite(LED_VERMELHO_PIN, estadoLed);
  }

}

