//================ RECEBE O PACOTE DE DL DA CAMADA DE REDE ========
void Transp_radio_receive_DL() { 

  contadorDL = contadorDL + 1;


  // 1. Verifica se um novo pacote chegou (substitua pela sua função de leitura)
    
    // Extrai os dados conforme a sua lógica

    medidasLSS = (((int(PacoteDL[14])) * 256) + (PacoteDL[15]));

    pacotesRecebidos++;
    
    // Atualiza o relógio para o momento exato da chegada
    ultimoRecebimento = millis(); 
    
    atualizarPER();

  App_radio_receive_DL();

}


//================ ENVIA O PACOTE DE UL À CAMADA DE REDE ========
void Transp_radio_send_UL() { 


  // neste ponto pode ser implementado um controle relacionado ao recebimento não sequencial de pacotes de DL
  
  atualizarPER();

  contadorUL = contadorUL + 1;  // Incrementa o contador de pacote de UL

  PacoteUL[LSS_COUNTER_MSB] = contador_perda_DL/256; //PacoteDL[DL_COUNTER_MSB];
  PacoteUL[LSS_COUNTER_LSB] = contador_perda_DL%256; //PacoteDL[DL_COUNTER_LSB];

  PacoteUL[UL_COUNTER_MSB] = contadorUL/256; // = (contadorUL >> 8) & 0xFF; 
  PacoteUL[UL_COUNTER_LSB] = contadorUL%256; // = contadorUL & 0xFF;

    if ((contadorUL >= medidasLSS) or (per > 10)){ // era >= aaf 09/11
      contadorUL = 0;
      medidasLSS = 0;
      confirma_novo_radio_sensor = 5;
      primeiro_setup = 1;
    }

  #if defined(OLED_INTEGRADO)

    display.setTextSize(1);
    //display.setCursor(0, 35);
    display.print("Pkt_UL : ");
    display.setTextSize(1);
    display.println(contadorUL, 1); 

  #endif
  
  Net_radio_send_UL();

}

void atualizarPER() {
  unsigned long totalPacotes = pacotesRecebidos + pacotesPerdidos;
  
  if (totalPacotes > 0) {
    per = ((float)pacotesPerdidos / (float)totalPacotes) * 100.0;
  }

  Serial.print("Recebidos: "); Serial.print(pacotesRecebidos);
  Serial.print(" | Perdidos: "); Serial.print(pacotesPerdidos);
  Serial.print(" | PER: "); Serial.print(per, 2); Serial.println("%");
}
