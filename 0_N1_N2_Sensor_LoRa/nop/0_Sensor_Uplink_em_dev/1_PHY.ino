
//================ ENVIA O PACOTE UL ========
void Phy_radio_send_UL() {

  for (int i = 0; i < TAMANHO_PACOTE; i++) {
    PacoteUL[i] = 0;    
  }
  

  // Pisca o LED de transmissão de pacote UL
  digitalWrite(LED_VERMELHO_PIN, HIGH); // Início da Transmissão

  PacoteUL[0] = 20;
  PacoteUL[1] = 159;
  PacoteUL[2] = 0;
  PacoteUL[3] = 160;
  PacoteUL[4] = 0;
  PacoteUL[5] = 254;
  PacoteUL[6] = 0;
  PacoteUL[7] = 6;
  PacoteUL[8] = 0;
  PacoteUL[9] = 9;
  PacoteUL[10] = 9;
  PacoteUL[11] = 99;
  PacoteUL[12] = 87;
  PacoteUL[13] = 54;
  PacoteUL[14] = 100;
  PacoteUL[15] = 254;
  PacoteUL[16] = 1;
  PacoteUL[17] = 0;
  PacoteUL[18] = 155;
  PacoteUL[19] = 254;
  PacoteUL[20] = 0;
  PacoteUL[21] = 254;
  PacoteUL[22] = 254;
  PacoteUL[23] = 0;
  PacoteUL[24] = 254;
  PacoteUL[25] = 0;
  PacoteUL[26] = 254;
  PacoteUL[27] = 254;
  PacoteUL[28] = 0;
  PacoteUL[29] = 254;

  LoRa.beginPacket();                 // Inicia o envio do pacote ao rádio
  
  for (int i = 0; i < TAMANHO_PACOTE; i++) {
    LoRa.write(PacoteUL[i]);          // Envia byte a byte as informações para o Rádio
  }
  LoRa.endPacket();                   // Finaliza o envio do pacote

  digitalWrite(LED_VERMELHO_PIN, LOW); // Fim da Transmissão

}
