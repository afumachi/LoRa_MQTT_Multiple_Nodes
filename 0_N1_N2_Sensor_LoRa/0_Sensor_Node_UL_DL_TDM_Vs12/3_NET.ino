// ====== FUNÇÃO RECEBE PACOTE DA CAMADA DE REDE
void Net_radio_receive_DL() {

  if(PacoteDL[8] == ID_sensor) {  // Só passa para a camada superior se for o destino final do pacote

    primeiro_downlink = 1;

        if (!controle_ativo) {
          // Primeira vez que recebe o comando 4: inicia a contagem
          millis_inicio_controle = millis();
          controle_ativo         = true;

          Serial.println("[CONTROLE] Contagem iniciada. Tempo limite: ");

        } else {
          // Pacote com comando chegou novamente enquanto contagem ativa:
          // Reinicia a contagem com o novo tempo recebido
          millis_inicio_controle = millis();
          millis_standby_controle = millis();

          Serial.println("[CONTROLE] Contagem reiniciada. Novo tempo limite: ");

        }

        if (controle_ativo) {
          Serial.println("[CONTROLE != 0] Contagem cancelada.");
          controle_ativo = false;
          millis_inicio_controle = 0;
        }



    Transp_radio_receive_DL();
  }
}

// ====== ENVIA PACOTE CAMADA REDE
void Net_radio_send_UL() {

  PacoteUL[RECEIVER_ID]    = ID_gateway; //PacoteDL[TRANSMITTER_ID];   // Destino do pacote de UL
  PacoteUL[TRANSMITTER_ID] = ID_sensor;                                // Emissor do pacote UL

  Mac_radio_send_UL();
}