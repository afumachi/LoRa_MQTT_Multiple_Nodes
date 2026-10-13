// PWA Aplicativo de acesso

/*
  MoT LoRa Site Survey Versão Zero | WissTek IoT
  Última versão: Branquinho / Felipe / Anderson
  Hardware: PKLoRa ESP32
*/

//=======================================================================
// 1 - Escolha do Módulo - ESP32 ou NodeMCU
//=======================================================================

// Remova o comentário da linha referente ao módulo que você está utilizando e comente a outro

#define PKLORA_ESP32 // #define PKLORA_ESP32
//#define AFLORA_ESP32 // #define AFLORA_ESP32 fabricação própria
//#define PKLORA_NODEMCU // #define PKLORA_NODEMCU

//=======================================================================
// 2 - Biblioteca - chama o arquivo Biblioteca.h
//=======================================================================

#include "Bibliotecas.h"  // Arquivo contendo declaração de bibliotecas e variáveis

// =====================================================================
// 3 - Configurações Broker MQTT
// =====================================================================
// Configurações do Broker Mosquitto (Usando o broker público oficial)
const char* MQTT_BROKER = "test.mosquitto.org";

// Configurações do Broker HiveMQ (Usando o broker público oficial)
//const char* MQTT_BROKER   = "broker.hivemq.com";

// Configurações do Broker Smart TpM (Usando o broker público Smart TpM)
//const char* MQTT_BROKER   = "www.tpm.dev.br";

const int   MQTT_PORT     = 1883;

//const char* TOPIC_DL      = "mot_lora_mqtt_FEE23/gateway/downlink";
//const char* TOPIC_UL      = "mot_lora_mqtt_FEE23/gateway/uplink";

const char* TOPIC_DL      = "mot_aaf_194104/gateway/downlink";  // Python → ESP32
const char* TOPIC_UL      = "mot_aaf_194104/gateway/uplink";    // ESP32  → Python
String CLIENT_ID ;         // ID único no broker

// QoS usado nos dois sentidos (DL e UL). QoS1 = "at least once"
// MQTT confirma o recebimento (PUBACK) e a biblioteca retransmite se necessário.

#if defined(PKLORA_ESP32) || defined(AFLORA_ESP32)

  const int MQTT_QOS = 1;

#elif defined(PKLORA_NODEMCU)  
  
  // desabilita QoS com NodeMCU devido a exigência de processamento
  const int MQTT_QOS = 0; 

#endif

// --- Objeto MQTT ---
MQTTClient mqttClient(256);   // buffer de 256 bytes (read/write)

//=======================================================================
// 4 - Configuração de Setup de Rádio LoRa
//=======================================================================

// ============= CAMADA FÍSICA
// Parâmetros do LoRa
#define FREQUENCY_IN_HZ       903E6    // LoRa Frequency
#define txPower               2       // TX power in dBm, defaults to 17
#define spreadingFactor       7       // ranges from 6-12,default 7
#define signalBandwidth       500E3    // signal bandwidth in Hz
#define codingRateDenominator 5        // denominator of the coding rate

// Habilita ou disabilita o uso CRC, por padrão o CRC não é usado.
//#define loraCRC

//=======================================================================
// 5 - Configuração de Redes Wi-Fi
//=======================================================================

// Cofiguração das redes Wi-Fi 2.4GHz disponíveis
void conectar_wifi_multi() {
  wifiMulti.addAP("COLETTI_ADV_CRIS", "45384609");
  // Cadastre quantas redes você quiser (SSID, Senha)
	wifiMulti.addAP("COLETTI_ext", "1145384609");
	wifiMulti.addAP("2.4G COLETTI", "1145384609");

  wifiMulti.addAP("MJCA_FUNDOS", "21092429MJC@");





	wifiMulti.addAP("aafwifi", "aaf12345678");
	wifiMulti.addAP("CHACARA BBC", "Ailton1960#");
	wifiMulti.addAP("Claro-EB66", "54b80a7deb66");
  
}

// uffer e flag para o pacote DL recebido via MQTT
volatile bool mqtt_dl_disponivel = false;
byte          mqtt_dl_payload[TAMANHO_PACOTE];




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
// 6 - Setup de inicialização 
//=======================================================================

// Inicializa as camadas
void setup() {
  //================= INICIALIZA SERIAL E MÓDULO RF95

  Serial.begin(115200);
  // Aguarda para estabilização da Serial
  delay(20);

  // declara Leds como saídas digital do ESP32
  pinMode(LED_VERMELHO_PIN, OUTPUT);
  pinMode(LED_VERDE_PIN, OUTPUT);
  digitalWrite(LED_VERMELHO_PIN, LOW);
  digitalWrite(LED_VERDE_PIN,    LOW);

  conectar_wifi_multi();

  // O wifiMulti.run() tenta conectar a uma das redes cadastradas
  // Ele retorna WL_CONNECTED quando consegue se conectar com sucesso
  while (wifiMulti.run() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("Wi-Fi conectado com sucesso!");
  Serial.print("Conectado na rede: ");
  Serial.println(WiFi.SSID());
  Serial.print("Endereço IP: ");
  Serial.println(WiFi.localIP());

  CLIENT_ID = "esp32_gateway+lora_" + String(WiFi.macAddress());
  CLIENT_ID.replace(":", "");

  // ---------- Inicia MQTT ----------
  mqttClient.begin(MQTT_BROKER, MQTT_PORT, wifiClient);
  mqttClient.onMessageAdvanced(mqtt_callback);
  conectar_mqtt();

  #if defined(PKLORA_ESP32) || defined(AFLORA_ESP32)
    // --- Inicialização da Comunicação SPI entre o ESP32 e o Módulo LoRa RFM95 ---
    SPI.begin(SCK_PIN, MISO_PIN, MOSI_PIN, NSS_PIN);
    delay(20);
    LoRa.setSPI(SPI);
    delay(20);
  #endif

  // --- Inicialização da Comunicação LoRa em 915Mhz---
  LoRa.setPins(NSS_PIN, RST_PIN, DIO0_PIN);
  if (!LoRa.begin(FREQUENCY_IN_HZ)) {
    Serial.println("[Nó Sensor] Falha ao iniciar LoRa. Verifique conexões.");
    while (true); // Trava se o LoRa falhar
  }

  delay(1000);
  //  --- Atua Led vermelho  --- 
  digitalWrite(LED_VERMELHO_PIN, LOW); // LIGA LED VERMELHO - INDIFERENTE PARA O BOOT

  //  --- Atua Led verde  --- 
  digitalWrite(LED_VERDE_PIN, LOW);  // DESLIGA O LED VERDE - DEVE SER LOW DURANTE BOOT

  // Aguarda 1 segundo para estabilização
  delay(1000);

  //  --- Pisca Led verde  --- Sucesso ao Iniciar 
  digitalWrite(LED_VERMELHO_PIN, HIGH);  // DESLIGA O LED VERDE - DEVE SER LOW DURANTE BOOT
  digitalWrite(LED_VERDE_PIN, HIGH);  // 
  delay(2000);
  digitalWrite(LED_VERMELHO_PIN, LOW); 
  digitalWrite(LED_VERDE_PIN, LOW);  //

  #ifdef loraCRC   // Habilitação do CRC do chip lora  (Configurado em bibliotecas.h)
    LoRa.enableCrc();
  #endif

} // FIM DO SETUP


//=======================================================================
//                     4 - Loop de repetição
//=======================================================================
// A função loop irá executar repetidamente
void loop() {

  // Mantém conexões ativas
  // No loop, você pode monitorar a conexão.
  // Se a rede cair, o wifiMulti.run() tenta reconectar automaticamente à melhor rede disponível.
  if (wifiMulti.run() != WL_CONNECTED) {
    Serial.println("Conexão perdida! Tentando reconectar...");
    delay(1000);
  }

  // Liga um LED a cada 500 [ms]
  unsigned long tempo_led_ms = 1000UL;
  

  if (millis() - millis_mqtt_controle >= tempo_led_ms) {        

    st_led_vermelho = 1;
    // Zera contagem do tempo de controle MQTT para tempo de ESP32 rodando
    millis_mqtt_controle = millis(); 

  }
  else {
    st_led_vermelho = 0;
  }


  if (!mqttClient.connected()) {
    conectar_mqtt();
  }

  else{
    if (st_led_vermelho == 1){
      //digitalWrite(LED_VERMELHO_PIN, LOW);
      //digitalWrite(LED_VERDE_PIN, LOW);
    }
    else{
      //digitalWrite(LED_VERMELHO_PIN, HIGH);
      //digitalWrite(LED_VERDE_PIN, HIGH);
    }

  }

  mqttClient.loop();   // processa envio/recebimento e handshakes de QoS1/2

  // Verifica se chegou pacote DL via MQTT e o envia pelo rádio LoRa
  Phy_mqtt_receive_DL();

  // Verifica se chegou pacote UL via rádio LoRa e o publica no broker
  Phy_radio_receive_UL();
  
  unsigned long tempo_standby_ul_ms = 2UL * time_out_lora_ul; // 2 min. sem Pacotes UL sobe para MAX  

  if (millis() - millis_standby_controle >= tempo_standby_ul_ms) {
    Serial.println("TEMPO SEM RECEBER PACOTES UL - Time-Out");
    Serial.println("Voltando a Configuração LoRa MDC");

    millis_standby_controle = millis();
    //reset_gateway_para_setup_inicial(); // Timeout atingido → volta ao SETUP
  }  


  // Imprime Radio Config a cada 10 [s]
  unsigned long tempo_loop_ms = 20000UL;  

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




}
