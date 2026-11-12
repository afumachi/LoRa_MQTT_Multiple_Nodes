
//=======================================================================
// 1 - Bibliotecas
//=======================================================================

// Bibliotecas comuns para os Hardwares ESP32 e NodeMCU

#include <SPI.h>  // A SPI é usada para conectar o Módulo de Processamento ao RFM95
#include <LoRa.h> // Biblioteca do Módulo de Rádio LoRa RFM95W

//=======================================================================
// 2 - Mapeamento dos Pinos
//=======================================================================

#if defined(PKLORA_ESP32)
  // ============= Pinagem na placa da PK-LoRa da ligação do RFM95 com o ESP32
  #define SCK_PIN   5
  #define MISO_PIN  19
  #define MOSI_PIN  27
  #define NSS_PIN   18
  #define RST_PIN   14
  #define DIO0_PIN  26
  #define DIO1_PIN  35
  #define DIO2_PIN  34

  // ============= CAMADA DE APLICAÇÃO
  // ESP32 I/Os - DIAGRAMA DE PINOS ENTRADAS E SAÍDAS
  // Pinos de Saída Digitais (Opcional, mas útil para debug no Gateway)
  #define LED_VERMELHO_PIN  15
  #define LED_VERDE_PIN     4



#elif defined(AAFLORA_ESP32)

  // ============= Pinagem na placa da AAF-LoRa da ligação do RFM95 com o ESP32
  #define SCK_PIN   18
  #define MISO_PIN  19
  #define MOSI_PIN  23
  #define NSS_PIN   5
  #define RST_PIN   14
  #define DIO0_PIN  26
  #define DIO1_PIN  35
  #define DIO2_PIN  34

  // Pinos dos LEDs
  #define LED_VERMELHO_PIN  15    // PINO 15
  #define LED_VERDE_PIN     4    // PINO 4

  #define LDR_PIN 36

#else
  #error "Por favor, definir a placa de hardware  (PKLORA_ESP32 ou AAFLORA_ESP32) no topo deste código!"
#endif

  // adicionar um conjunto de variáveis PKT_UL e PKT_DL para deixar os pacotes independentes

  // --- Physical Layer ---
#define RSSI_DOWNLINK 0
#define LQI_DOWNLINK  1
#define RSSI_UPLINK   2
#define LQI_UPLINK    3

  // --- MAC Layer ---
#define MAC_COUNTER_MSB 4 
#define MAC_COUNTER_LSB 5
#define MAC3_TEMPO 6
#define MAC4_COMANDO 7

  // --- Network Layer ---
#define  RECEIVER_ID     8
#define  NET2            9
#define  TRANSMITTER_ID  10
#define  NET4            11

  // --- Transport Layer ---
#define DL_COUNTER_MSB 12
#define DL_COUNTER_LSB 13
#define UL_COUNTER_MSB 14
#define UL_COUNTER_LSB 15


/*

enum bytes_do_pacote{

  // adicionar um conjunto de variáveis PKT_UL e PKT_DL para deixar os pacotes independentes

  // --- Physical Layer ---
  RSSI_DOWNLINK   = 0,
  LQI_DOWNLINK    = 1,
  RSSI_UPLINK     = 2,
  LQI_UPLINK      = 3,

  // --- MAC Layer ---
  MAC_COUNTER_MSB = 4, 
  MAC_COUNTER_LSB = 5,
  MAC3 = 6,
  MAC4 = 7,

  // --- Network Layer ---
  RECEIVER_ID     = 8,
  NET2            = 9,
  TRANSMITTER_ID  = 10,
  NET4            = 11,

  // --- Transport Layer ---
  DL_COUNTER_MSB = 12,
  DL_COUNTER_LSB = 13,
  UL_COUNTER_MSB = 14,
  UL_COUNTER_LSB = 15,

  // --- Application Layer ---
  APP1 = 16,  // Tipo de sensor - no caso da PK-LoRa é um LDR
  APP2 = 17,  // Valor inteiro da luminosidade da conta de divisão por 256
  APP3 = 18,  // Valor de resto da conta de divisão por 256
  APP4 = 19,
  APP5 = 20,
  APP6 = 21,
  APP7 = 22,
  APP8 = 23,
  APP9 = 24,
  APP10 = 25,
  APP11 = 26,
  APP12 = 27,
  APP13 = 28, 
  APP14 = 29,
  APP15 = 30,
  APP16 = 31,
  APP17 = 32,
  APP18 = 33,
  APP19 = 34,
  APP20 = 35,
  APP21 = 36,
  APP22 = 37,
  APP23 = 38,
  APP24 = 39,
  APP25 = 40,
  APP26 = 41,
  APP27 = 42,
  APP28 = 43,
  APP29 = 44,
  APP30 = 45,
  APP31 = 46,
  APP32 = 47,
  APP33 = 48,
  APP34 = 49,
  APP35 = 50,
  APP36 = 51,
};

*/
