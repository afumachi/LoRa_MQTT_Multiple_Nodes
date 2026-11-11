// ====== FUNÇÃO RECEBE PACOTE DA CAMADA DE REDE
void Net_radio_receive_DL() {
  if(PacoteDL[RECEIVER_ID] == ID_sensor) {  // Só passa para a camada superior se for o destino final do pacote
    //Serial.println("Pacote DL é para este Nó Sensor");

    Transp_radio_receive_DL();
  }
}

// ====== ENVIA PACOTE CAMADA REDE
void Net_radio_send_UL() {

  PacoteUL[RECEIVER_ID]    = ID_gateway; //PacoteDL[TRANSMITTER_ID];   // Destino do pacote de UL
  PacoteUL[TRANSMITTER_ID] = ID_sensor;                                // Emissor do pacote UL

  Mac_radio_send_UL();
}