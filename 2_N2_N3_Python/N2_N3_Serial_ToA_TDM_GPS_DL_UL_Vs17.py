
'''

# Framework Serial para Multiplos Nó-Sensores

'''
# ===== Bibliotecas =====
import serial
import time
import math
import struct
from time import localtime, strftime
import os
import random
import pandas as pd
import threading


# ========== Criação de Variáveis GLOBAIS =========================
global rssi_DL, rssi_UL, contador_UL, contador_DL, ultimo_pacote_DL, ultimo_pacote_UL, air_quality_indicator
global valor_inicial_spreadingfactor, valor_inicial_bandwidth, valor_inicial_codingrate, valor_inicial_potencia_radio
global valor_atual_spreadingfactor, valor_atual_bandwidth, valor_atual_codingrate, valor_atual_potencia_radio
global valor_anterior_spreadingfactor, valor_anterior_bandwidth, valor_anterior_codingrate, valor_anterior_potencia_radio
global valor_novo_spreadingfactor, valor_novo_bandwidth, valor_novo_codingrate, valor_novo_potencia_radio
global taxa_canal_teorica, taxa_canal_calculada, bitrate, perda_geral, st_cmd_led_amarelo
global medida_atual, numero_de_medidas, condicao_start, tempo_entre_medidas, perda_total, enlace_testado
global recebe_valor_spreadingfactor, recebe_valor_bandwidth, recebe_valor_codingrate, recebe_valor_potencia_radio
global comanda_mudar_radio, contador_pacote_DL, LSS_status, psr_geral, contador_reconfigura, confirma_mudar_radio
global psrDL_geral, contador_perda_DL, ID_gateway, ID_sensor, Pacote_DL, pacote_recebido, estado_mqtt, radio_configurado
global estado_lss, toa_entre_medidas, indice_dispositivo_atual, quantidade_de_medidas
global sf_csv, bw_csv, cr_csv, pw_csv, sf_csv_new, bw_csv_new, cr_csv_new
global comando, medidas, tempo, arquivo_log_dados, num_medidas
global Contador_pkt_DL, num_medidas_total, tempo_entre_pacotes, valor_tempo
global Pacote_UL, primeiro_pacote_recebido, total_end_devices, ultimo_pacote, Tempo_gasto
global Comando_LED_amarelo, St_LED_amarelo, Tempo_inicial_RX, Tempo_limite_RX, time_out



# ===== Arquivo Log globais =====
lock_arquivo_log = threading.Lock()

# ===== Variáveis globais =====
#TAMANHO_PACOTE = 20
TAMANHO_PACOTE_DL = 20
TAMANHO_PACOTE_UL = 30

# 
indice_dispositivo_atual = 0

# definições de teste: configurações importantes para a bateria de testes extraídas do arquivo de parâmetros
numero_de_medidas = 0
quantidade_de_medidas = 0
rota = [] # neste momento é um enlace ponto a ponto, que futuramente poderá ser usada para roteamento
enlace_testado = 0
radio_configurado = 0
estado_lss = 0
perda_PK_RX = 0

# Variáveis de Controle
comando = 0
medidas = 100
medida_atual = 0
num_medidas = 0
tempo = 2.0
condicao_start = 0
arquivo_log_dados = 0

# ================ Camada MAC
tempo_entre_pacotes = 0.2
pacote_recebido = 0
primeiro_pacote_recebido = 0
Tempo_inicial_RX = 0
Tempo_limite_RX = 0
time_out = 5
Tempo_gasto = 0
# ================ Camada Transporte
Contador_pkt_DL = 0
num_medidas_total = 0

#Camada Física

sf_csv = 12
bw_csv = 125
cr_csv = 8
sf_csv_new = 12
bw_csv_new = 125
cr_csv_new = 8
pw_csv = 20

# Camada MAC
valor_tempo = 5
tempo_entre_medidas = 5
toa_entre_medidas = 5

# Adição variáveis de controle do ciclo de modif. configuração rádio LoRa
inicia_lora_site_survey = 0
comanda_mudar_radio = 0 # Comando de Downlink de mudança de configuração de rádio LoRa
confirma_mudar_radio = 0 # Recebe Uplink da Confirmação da mudança de rádio
ultimo_pacote = 0

# Camada Transporte
ID_gateway = 0
ID_sensor = 1

# Aplicação
Comando_LED_amarelo = 0

# Cria os pacotes de DL e UL
Pacote_DL = [0]*TAMANHO_PACOTE_DL
Pacote_UL = [0]*TAMANHO_PACOTE_UL

# Caminho da Pasta de armazenamento (Caminho Relativo)
PASTA_ARMAZENAMENTO = os.path.join("..", "3_N4_Armazenamento")
dir_nivel4 = os.path.join(os.path.dirname(__file__), '../3_N4_Armazenamento/Parametros/')

# Caminhos dos arquivos de armazenamento e leitura de parametros
caminho_parametros = os.path.join(PASTA_ARMAZENAMENTO, "Parametros")
caminho_dados = os.path.join(PASTA_ARMAZENAMENTO, "Dados_Brutos")

# os.makedirs com exist_ok=True substitui o 'if not os.path.exists' e cria toda a estrutura de uma vez
os.makedirs(caminho_dados, exist_ok=True)
os.makedirs(caminho_parametros, exist_ok=True)
caminho_led = os.path.join(caminho_parametros, "cmd_led_amarelo.txt")

# Definindo o caminho do arquivo CSV com base no diretório nivel4
caminho_csv_end_devices = os.path.join(dir_nivel4, 'end_devices_net_par.csv')

# Declaração da variável inteira
total_end_devices: int = 0

#Atualiza arquivo de Parâmetros
#pasta_parametros = os.path.join(dir_nivel4, 'PARAMETROS_SERIAL.txt')

caminho_txt_parametros = os.path.join(dir_nivel4, "PARAMETROS_SERIAL.txt")

arquivo_cmd_lora = 'cmd_lora.txt'
caminho_cmd_lora = os.path.join(caminho_parametros, arquivo_cmd_lora)
parametros_cmd = open(caminho_cmd_lora, 'w')
parametros_cmd.write("0\n0\n") 
parametros_cmd.close()

# Conteúdo de 2 linhas para escrever
linhas_conteudo = [
    "linha1: parametros_radio_01\n",
    "linha2: parametros_radio_02\n"
]

Cabecalho = 'Time stamp,Contador,DL_B0,DL_B1,DL_B2,DL_B3,DL_B4,DL_B5,DL_B6,DL_B7,DL_B8,DL_B9,DL_B10,DL_B11,DL_B12,DL_B13,DL_B14,DL_B15,DL_B16,DL_B17,DL_B18,DL_B19,UL_B0,UL_B1,UL_B2,UL_B3,UL_B4,UL_B5,UL_B6,UL_B7,UL_B8,UL_B9,UL_B10,UL_B11,UL_B12,UL_B13,UL_B14,UL_B15,UL_B16,UL_B17,UL_B18,UL_B19'

# ======================================================================================

# Garante que os pacotes de DL e UL estão com valor 0
for i in range(TAMANHO_PACOTE_DL):
   Pacote_DL[i] = 0
for i in range(TAMANHO_PACOTE_UL):
   Pacote_UL[i] = 0

# =======================================================

# Criação do arquivo de CMD LED AMARELO
CMD_LED_FILE = os.path.join(dir_nivel4, 'cmd_led_amarelo.txt')
if not os.path.exists(CMD_LED_FILE):
    with open(CMD_LED_FILE, "w") as f:
        f.write("0")


def ler_cmd_led_amarelo():
    try:
        with open(CMD_LED_FILE, "r") as f:
            val = f.read().strip()
            return int(val) if val in ("0", "1") else 0
    except Exception as e:
        print(f"[AVISO] Não foi possível ler {CMD_LED_FILE}: {e}. Usando LED=0.")
        return 0


def ler_parametros_arquivo():
   if not os.path.exists(caminho_txt_parametros):
      return None
   try:
      with open(caminho_txt_parametros, "r") as f:
         linhas = [linha.strip() for linha in f.readlines()]
         if len(linhas) >= 4:
            comando = int(linhas[0])
            medidas = int(linhas[1])
            tempo = float(linhas[2].replace(",", "."))
            n_serial = str(linhas[3])
            return comando, medidas, tempo, n_serial
   except Exception:
      pass
   return None

def calculo_toa_radio_lora(n_preambulo=8, header_impl=False, crc_on=True, low_dr_opt=None):
    global toa_entre_medidas, valor_atual_bandwidth, valor_atual_spreadingfactor, valor_atual_codingrate, TAMANHO_PACOTE_UL
    global sf_csv, bw_csv, cr_csv, valor_tempo

    valor_atual_spreadingfactor = sf_csv
    valor_atual_bandwidth = bw_csv
    valor_atual_codingrate = cr_csv
    
    # 1. Parâmetros de tempo dos símbolos LoRa
    BANDWIDTH_Hz = valor_atual_bandwidth * 1000 #calcula Bandwidth em Hz
    tempo_simbolo = (2**valor_atual_spreadingfactor) / BANDWIDTH_Hz #calcula o tempo de símbolos de acordo com Spreading Factor e Bandwidth
    
    # 2. Tempo do Preâmbulo
    tempo_preambulo = (n_preambulo + 4.25) * tempo_simbolo
    
    # 3. Determinação automática do Low Data Rate Optimization
    # Obrigatório quando a duração do símbolo > 16ms
    if low_dr_opt is None:
        low_dr_opt = 1 if tempo_simbolo > 0.016 else 0 # Variável DE == 1 If ((SF >= 11) & (BW == 125kHz))
        
    # 4. Cálculo do número de símbolos do Payload (n_payload)
    # valor_CR = int(valor_codingrate.split('/')[1]) - 4 # 4/5 -> 1, 4/8 -> 4
    if (valor_atual_codingrate == 5):
        valor_CR = 1
    elif (valor_atual_codingrate == 6):
        valor_CR = 2
    elif (valor_atual_codingrate == 7):
        valor_CR = 3
    elif (valor_atual_codingrate == 8):
        valor_CR = 4
    
    IH = 1 if header_impl else 0
    CRC = 1 if crc_on else 0
    DE = 1 if low_dr_opt else 0
    
    n_pacote = (8 * TAMANHO_PACOTE_UL - 4 * valor_atual_spreadingfactor + 28 + 16 * CRC - 20 * IH) / (4 * (valor_atual_spreadingfactor - 2 * DE))
    n_payload_simbolo = 8 + max(math.ceil(n_pacote) * (valor_CR + 4), 0)
    
    tempo_pacote_toa = n_payload_simbolo * tempo_simbolo
    
    # Retorna ToA em ms e bitrate em bps
    ToA_ms = (tempo_preambulo + tempo_pacote_toa) * 1000

    # bitrate = (SF*((BW*1000)/(2^SF))*(4/(4+CR)))/1000
    bitrate = (valor_atual_spreadingfactor*((BANDWIDTH_Hz)/(2**valor_atual_spreadingfactor))*(4/(4+valor_CR)))

    # calcula valor do tempo da comunicação MQTT + entre o Envio do Pacote via LoRa de Downlink + Uplink + Tempo Processamento ESP32 + MQTT
    valor_tempo = ((2*ToA_ms))/1000 #
    toa_entre_medidas = max(math.ceil(valor_tempo), 0) #arredonda em segundos o tempo entre medidas
    # Imprime tempos para Debug
    #print("### Time On Air (ToA [ms]): ", ToA_ms)
    #print('### Valor Tempo Entre Medidas: ', toa_entre_medidas, 'Calculado' , valor_tempo)
    return toa_entre_medidas


# =============================================================================
# TABELA LUT DE 72 COMBINAÇÕES INDEXADAS (EQUIVALENTE AO FIRMWARE DO ESP32)
# =============================================================================
RADIO_CONFIG_LUT = [
    # ===== SF=7 (Índices 0-11) =====
    (7, 125000, 5), (7, 125000, 6), (7, 125000, 7), (7, 125000, 8),
    (7, 250000, 5), (7, 250000, 6), (7, 250000, 7), (7, 250000, 8),
    (7, 500000, 5), (7, 500000, 6), (7, 500000, 7), (7, 500000, 8),
    
    # ===== SF=8 (Índices 12-23) =====
    (8, 125000, 5), (8, 125000, 6), (8, 125000, 7), (8, 125000, 8),
    (8, 250000, 5), (8, 250000, 6), (8, 250000, 7), (8, 250000, 8),
    (8, 500000, 5), (8, 500000, 6), (8, 500000, 7), (8, 500000, 8),
    
    # ===== SF=9 (Índices 24-35) =====
    (9, 125000, 5), (9, 125000, 6), (9, 125000, 7), (9, 125000, 8),
    (9, 250000, 5), (9, 250000, 6), (9, 250000, 7), (9, 250000, 8),
    (9, 500000, 5), (9, 500000, 6), (9, 500000, 7), (9, 500000, 8),
    
    # ===== SF=10 (Índices 36-47) =====
    (10, 125000, 5), (10, 125000, 6), (10, 125000, 7), (10, 125000, 8),
    (10, 250000, 5), (10, 250000, 6), (10, 250000, 7), (10, 250000, 8),
    (10, 500000, 5), (10, 500000, 6), (10, 500000, 7), (10, 500000, 8),
    
    # ===== SF=11 (Índices 48-59) =====
    (11, 125000, 5), (11, 125000, 6), (11, 125000, 7), (11, 125000, 8),
    (11, 250000, 5), (11, 250000, 6), (11, 250000, 7), (11, 250000, 8),
    (11, 500000, 5), (11, 500000, 6), (11, 500000, 7), (11, 500000, 8),
    
    # ===== SF=12 (Índices 60-71) =====
    (12, 125000, 5), (12, 125000, 6), (12, 125000, 7), (12, 125000, 8),
    (12, 250000, 5), (12, 250000, 6), (12, 250000, 7), (12, 250000, 8),
    (12, 500000, 5), (12, 500000, 6), (12, 500000, 7), (12, 500000, 8),
]

# Variável para rastrear a linha atual no CSV
linha_dispositivo_atual = 0

#========== DOWNLINK ================
def downlink():
   global rssi_DL, rssi_UL, contador_UL, contador_DL, ultimo_pacote_DL, ultimo_pacote_UL
   global comanda_mudar_radio, estado_lss, total_end_devices, ultimo_pacote
   global indice_dispositivo_atual, quantidade_de_medidas, time_out
   global sf_csv, bw_csv, cr_csv, pw_csv, linha_dispositivo_atual
   global sf_csv_new, bw_csv_new, cr_csv_new
   global Contador_pkt_DL, num_medidas_total, primeiro_pacote_recebido
   global ID_sensor, ID_gateway, Pacote_DL, Pacote_UL, medida_atual, num_medidas
   
   sf_csv = 12
   bw_csv = 125
   cr_csv = 8
   
   sf_csv_new = 12
   bw_csv_new = 125
   cr_csv_new = 8
   
   pw_csv = 20

   try:

       # Leitura das configurações e do endereço do nó sensor a partir do CSV
       if os.path.exists(caminho_csv_end_devices):
           try:
               df_devices = pd.read_csv(caminho_csv_end_devices)
               
               if not df_devices.empty:
                   if indice_dispositivo_atual >= len(df_devices):
                       print("[LSS] Todos os nós do arquivo CSV já foram percorridos. Reiniciando lista no primeiro nó...")
                       indice_dispositivo_atual = 0
                   
                   # Guarda o índice da linha atual para atualizar no uplink
                   linha_dispositivo_atual = indice_dispositivo_atual
                   dispositivo = df_devices.iloc[indice_dispositivo_atual]

                   # Obtém o endereço de rede do sensor
                   endereco_hex_ou_str = str(dispositivo['endereco_rede']).strip()
                   if endereco_hex_ou_str.startswith("0x") or endereco_hex_ou_str.startswith("0X"):
                       ID_sensor = int(endereco_hex_ou_str, 16)
                   else:
                       ID_sensor = int(endereco_hex_ou_str)

                   # Obtém os parâmetros de rádio configurados com final _new
                   sf_csv = int(dispositivo['spreading_factor'])
                   bw_csv = int(dispositivo['bandwidth'])
                   cr_csv = int(dispositivo['coding_rate'])
                   pw_csv = int(dispositivo['potencia_tx_new'])

                   sf_csv_new = int(dispositivo['spreading_factor_new'])
                   bw_csv_new = int(dispositivo['bandwidth_new'])
                   cr_csv_new = int(dispositivo['coding_rate_new'])
                   
                   # Lê o comando_radio da mesma linha do CSV
                   comanda_mudar_radio = int(dispositivo['comando_radio'])
                   
                   print(f"[LSS] Enviando Pacote DL para o Nó Sensor [{indice_dispositivo_atual + 1}/{len(df_devices)}]: "
                         f"Endereço 0x{ID_sensor:02X} ({ID_sensor}) | SF: {sf_csv} | BW: {bw_csv} | CR: {cr_csv} | Pot_Tx: {pw_csv} | Cmd: {comanda_mudar_radio}")
                   
                   indice_dispositivo_atual += 1
               else:
                   print("[AVISO] O arquivo end_devices_net_par.csv está vazio. Mantendo valores padrões.")
           except Exception as e:
               print(f"[ERRO] Falha ao ler parâmetros do nó em {caminho_csv_end_devices}: {e}")
       else:
           print(f"[AVISO] Arquivo {caminho_csv_end_devices} não encontrado. Mantendo valores padrões.")

       # Limpa o pacote para garantir que não tem lixo
       for i in range(TAMANHO_PACOTE_DL):
           Pacote_DL[i] = 0

       # Converte Bandwidth de KHz para Hz para consulta na tabela LUT
       bw_hz = bw_csv * 1000
       bw_hz_new = bw_csv_new * 1000
       
       # Busca o índice correspondente na tabela LUT de 72 combinações
       lut_index = 0
       lut_index_new = 0

       for idx, config in enumerate(RADIO_CONFIG_LUT):
           if config == (sf_csv, bw_hz, cr_csv):
               lut_index = idx
               break
       
       for idx_new, config in enumerate(RADIO_CONFIG_LUT):
           if config == (sf_csv_new, bw_hz_new, cr_csv_new):
               lut_index_new = idx_new
               break

       calculo_toa_radio_lora() # chama função cálculo ToA

       # Alocação nos Bytes do Pacote_DL conforme solicitado
       Pacote_DL[0] = lut_index       # Índice da tabela LUT (0-71) no Byte 0
       Pacote_DL[1] = lut_index_new   # Índice novo da tabela LUT (0-71) no Byte 0
       Pacote_DL[2] = 0
       Pacote_DL[3] = pw_csv          # Potência de transmissão

       # Camada MAC
       Pacote_DL[4] = ultimo_pacote
       Pacote_DL[5] = 0
       Pacote_DL[6] = int(10 * time_out) # multiplica por 10 para eliminar uma casa decimal
       Pacote_DL[7] = comanda_mudar_radio
       estado_lss = comanda_mudar_radio
       #print("### DOWNLINK ### MÁQUINA ESTADO LORA: ", comanda_mudar_radio)

       # Camada de Rede
       Pacote_DL[8] = ID_sensor & 0xFF
       Pacote_DL[10] = ID_gateway

       # Camada de Transporte
       Pacote_DL[12] = int(medida_atual / 256)
       Pacote_DL[13] = int(medida_atual % 256)
       Pacote_DL[14] = int(num_medidas_total / 256)  # MSB
       Pacote_DL[15] = int(num_medidas_total % 256)  # LSB   

       # Camada de Aplicação
       Comando_LED_amarelo = ler_cmd_led_amarelo()
       Pacote_DL[16] = Comando_LED_amarelo

       # Atualiza arquivo de comando de estado do LoRa
       with open(caminho_cmd_lora, 'r') as f:
           linhas = f.readlines()

       linhas[0] = f"{estado_lss}\n"

       with open(caminho_cmd_lora, 'w') as f:
           f.writelines(linhas)

       ser.reset_input_buffer()
       for Bytes_DL in range(TAMANHO_PACOTE_DL):
           ser.write(chr(Pacote_DL[Bytes_DL]).encode('latin1'))
       ser.flush()
       #print(bytes(Pacote_DL).hex(" ")) #Imprime Pacote_DL para Debug
       time.sleep(0.05)
       
   except (serial.SerialException, OSError) as e:
       raise ConnectionError(f"Gateway desconectado na escrita: {e}")


#========== UPLINK ==================
def uplink():
   global perda_geral, rssi_DL, rssi_UL, contador_UL, ultimo_pacote_DL, quantidade_de_medidas
   global luminosidade, confirma_mudar_radio, snr_UL, snr_DL, st_cmd_led_amarelo
   global perda_total, contador_pacote_DL, contador_DL, medida_atual, numero_de_medidas
   global temperatura, umidade, latitude, longitude, altitude, contador_perda_DL
   global linha_dispositivo_atual


   global Pacote_UL, Pacote_DL, pacote_recebido, primeiro_pacote_recebido, tempo_entre_pacotes
   global Tempo_inicial_RX, Tempo_limite_RX, St_LED_amarelo, TAMANHO_PACOTE_UL

   # ======== COLETA UPLINK VIA SERIAL ========
   Pacote_UL = b''
   
   try:
      Pacote_UL = Pacote_UL + ser.read(TAMANHO_PACOTE_UL - len(Pacote_UL))

      if len(Pacote_UL) == TAMANHO_PACOTE_UL:   
         print('Pacote = ', medida_atual, ' | Pacote UL recebido')
         #print(Pacote_UL.hex(" ")) #Imprime Pacote_UL para Debug
         pacote_recebido = 1
         # Camada MAC
         confirma_mudar_radio = Pacote_UL[7]

         with open(caminho_cmd_lora, 'r') as f:
             linhas2 = f.readlines()

         linhas2[1] = f"{confirma_mudar_radio}\n"

         with open(caminho_cmd_lora, 'w') as f:
             f.writelines(linhas2)
         
         # Atualiza o arquivo CSV com confirma_mudar_radio e altera parâmetros se confirma_mudar_radio == 3
         if os.path.exists(caminho_csv_end_devices):
             try:
                 df_devices = pd.read_csv(caminho_csv_end_devices)
                 if 'linha_dispositivo_atual' in globals() and linha_dispositivo_atual < len(df_devices):
                     # Escreve confirma_mudar_radio na coluna comando_radio_st
                     df_devices.loc[linha_dispositivo_atual, 'comando_radio_st'] = confirma_mudar_radio
                     
                     # Caso confirma_mudar_radio == 3: atualiza comando_radio e copia os parâmetros _new para os parâmetros atuais
                     if confirma_mudar_radio == 3:
                         df_devices.loc[linha_dispositivo_atual, 'comando_radio'] = 4
                         df_devices.loc[linha_dispositivo_atual, 'spreading_factor'] = df_devices.loc[linha_dispositivo_atual, 'spreading_factor_new']
                         df_devices.loc[linha_dispositivo_atual, 'bandwidth'] = df_devices.loc[linha_dispositivo_atual, 'bandwidth_new']
                         df_devices.loc[linha_dispositivo_atual, 'coding_rate'] = df_devices.loc[linha_dispositivo_atual, 'coding_rate_new']
                         df_devices.loc[linha_dispositivo_atual, 'potencia_tx'] = df_devices.loc[linha_dispositivo_atual, 'potencia_tx_new']
                         print(f"[LSS] Rádio do Nó 0x{int(df_devices.loc[linha_dispositivo_atual, 'endereco_rede']):02X} reconfigurado com sucesso no CSV!")
                         time.sleep(1)
                         
                     df_devices.to_csv(caminho_csv_end_devices, index=False)
             except Exception as e:
                 print(f"[ERRO] Falha ao atualizar CSV no uplink: {e}")

      else: 
         pacote_recebido = 0

   except (serial.SerialException, OSError) as e:
       raise ConnectionError(f"Gateway desconectado na leitura: {e}")         


print("\n========== Aguardando Configuração Inicial via Painel (PARAMETROS.txt) ==========")

config = None
while config is None:
   config = ler_parametros_arquivo()
   if config is None:
      time.sleep(1)

_, num_medidas_total, tempo_entre_pacotes, n_serial = config
n_serial1 = int(n_serial) - 1

print(f"[Config] Porta COM: {n_serial} | Tempo entre pacotes: {tempo_entre_pacotes}s | Medidas: {num_medidas_total}")

ser = serial.Serial("COM"+str(n_serial), 115200, timeout=0.5, parity=serial.PARITY_NONE)

ser.setDTR(False)
ser.setRTS(False)
time.sleep(0.1)
ser.setDTR(True)
ser.setRTS(True)
time.sleep(1.5)

ser.reset_input_buffer()
ser.reset_output_buffer()

Comando_LED_amarelo = 0  
Contador_pkt_DL = 0
perda_PK_RX     = 0
ID_sensor = 1
ID_gateway = 0

print("\n========== Gateway LoRa - Comunicação Local (Controlado por Painel) ==========")

try:
    j = 1
    Log_dados = None
    filename1 = None
    estado_anterior = 0
    rodada_concluida = False

    while True:

       try:

          config_atual = ler_parametros_arquivo()
          if config_atual:
              comando, num_medidas_total, tempo_entre_pacotes, _ = config_atual
          else:
              comando = 0

          if comando == 1 and rodada_concluida:
              rodada_concluida = False
              estado_anterior = 0

          if comando == 0:
              if Log_dados and not Log_dados.closed:
                  Log_dados.close()
                  print(f'[LSS] Teste FINALIZADO Pelo Operador. Arquivo de log salvo e fechado com sucesso.')
                  print('Pacotes enviados = ', quantidade_de_medidas, ' Pacotes perdidos da rede = ', perda_PK_RX)
                  print('Tempo Entre Pacotes = ', Tempo_gasto)

                  # Escreve 0 automaticamente na primeira linha do PARAMETROS_SERIAL.txt para parar o teste
                  try:
                     if config_atual:
                        _, m_v, t_v, s_v = config_atual
                        with open(caminho_txt_parametros, "w") as pf:
                           pf.write("0\n")
                           pf.write(f"{m_v}\n")
                           pf.write(f"{t_v}\n")
                           pf.write(f"{s_v}\n")
                  except Exception as e:
                      print(f"[Erro] Falha ao atualizar PARAMETROS_SERIAL.txt para 0: {e}")
                  
              Log_dados = None
              rodada_concluida = False
              time.sleep(0.05)
              j = 1
              Contador_pkt_DL = 0
              perda_PK_RX = 0
              estado_anterior = 0
              primeiro_pacote_recebido = 0
              quantidade_de_medidas = 0
              medida_atual = 0
              ultimo_pacote = 0
              comanda_mudar_radio = 0 
              condicao_start = 0
              num_medidas_total = 0
              time.sleep(0.2)           
              continue

          if comando == 2:
              if estado_anterior != 2 and not rodada_concluida:
                  print('[LoRa] Teste PAUSADO pelo operador.')
                  estado_anterior = 2
              time.sleep(0.1)
              continue

          if comando == 1 and not rodada_concluida:
              if Log_dados is None or Log_dados.closed:
                 filename1 = strftime(os.path.join(caminho_dados, "Rodada_Teste_%Y_%m_%d_%H-%M-%S.txt"))
                 Log_dados = open(filename1, 'w')
                 print("Novo arquivo de log criado: %s" % filename1)
                 print(Cabecalho, file=Log_dados)
                 j = 1
                 perda_PK_RX = 0

              if estado_anterior != 1:
                 print('[LoRa] Teste INICIADO / RETOMADO.')
                 estado_anterior = 1

              # AAF 23-09-2026
              if os.path.exists(caminho_csv_end_devices):
                  try:
                     df_devices = pd.read_csv(caminho_csv_end_devices)
                     # O número de end devices cadastrados corresponde à quantidade de linhas no DataFrame
                     total_end_devices = len(df_devices)
                     #print(f"Total de end devices cadastrados: {total_end_devices}")
                  except Exception as e:
                     print(f"Erro ao ler o arquivo End Devices CSV: {e}")
                     total_end_devices = 0
              else:
                  print(f"Arquivo {caminho_csv_end_devices} não foi encontrado.")
                  total_end_devices = 0

              quantidade_de_medidas = num_medidas_total * total_end_devices # AAF 23-09-2026
              
              if (medida_atual == 0):
                  
                 radio_configurado = 1
                 inicia_lora_site_survey = 1
                 comanda_mudar_radio = 4
                 confirma_mudar_radio = 0
                 LSS_status = 1
                 print("################## LSS - Iniciando Medições LoRa #################")
                 # Gera o nome do arquivo com o novo caminho
                 filename1 = strftime(os.path.join(caminho_dados, "Rodada_Teste_%Y_%m_%d_%H-%M-%S.txt"))
       
                 Log_dados = open(filename1, 'w')
                 print("Arquivo de log: %s" % filename1)
                 Cabecalho = 'Time stamp,Contador,DL_B0,DL_B1,DL_B2,DL_B3,DL_B4,DL_B5,DL_B6,DL_B7,DL_B8,DL_B9,DL_B10,DL_B11,DL_B12,DL_B13,DL_B14,DL_B15,DL_B16,DL_B17,DL_B18,DL_B19,DL_B20,DL_B21,DL_B22,DL_B23,DL_B24,DL_B25,DL_B26,DL_B27,DL_B28,DL_B29,UL_B0,UL_B1,UL_B2,UL_B3,UL_B4,UL_B5,UL_B6,UL_B7,UL_B8,UL_B9,UL_B10,UL_B11,UL_B12,UL_B13,UL_B14,UL_B15,UL_B16,UL_B17,UL_B18,UL_B19,UL_B20,UL_B21,UL_B22,UL_B23,UL_B24,UL_B25,UL_B26,UL_B27,UL_B28,UL_B29'
                 print(Cabecalho,file=Log_dados)
                 time.sleep(1)
                 calculo_toa_radio_lora() # chama função cálculo ToA (Time On Air)
              else:
                 comanda_mudar_radio = 4 
                 confirma_mudar_radio = 0
                 LSS_status = 1
                 
              
              if (medida_atual < quantidade_de_medidas):
                  
                  LSS_status = 1
                                   
                  medida_atual = medida_atual + 1

                  if ((medida_atual) > (quantidade_de_medidas - total_end_devices)): # AAF 23-09-2026
                      ultimo_pacote = 1
                  else:
                      ultimo_pacote = 0

                  # (if) Tempo Gasto Para debug do try:
                  Tempo_gasto = 0
                  if (Tempo_gasto == 0):
                  #try:
                        Tempo_inicio_pacote = time.time()

                        # ================ Envio de pacote de DL
                        downlink()
                                              
                        time_out = (valor_tempo + tempo_entre_pacotes) #toa_entre_medidas
                        time.sleep(time_out)
                        # print('time-out total : ', time_out) # imprime para debug

                        pacote_recebido = 0
                        # ================ Recebimento de pacote de UL
                        uplink()

                        if (pacote_recebido == 1):
                            
                            Dados_DL = ''
                            Dados_UL = ''
                            
                            # Monta a string dos bytes de Downlink (tamanho 20)
                            for i in range(TAMANHO_PACOTE_DL):
                               if i == 0:
                                  Dados_DL = str(Pacote_DL[i])
                               else:
                                  Dados_DL = Dados_DL + ', ' + str(Pacote_DL[i])
                                  
                            # Monta a string dos bytes de Uplink (tamanho 30)
                            for i in range(TAMANHO_PACOTE_UL):
                               if i == 0:
                                  Dados_UL = str(Pacote_UL[i])
                               else:
                                  Dados_UL = Dados_UL + ', ' + str(Pacote_UL[i])

                            Tempo = time.asctime()
                            print(Tempo + ', ' + str(medida_atual) + ', Downlink: ' + Dados_DL + ' Uplink: ' + Dados_UL)
                            
                            # Grava Pacotes com a trava de segurança
                            with lock_arquivo_log:
                                Dados_log = Tempo + ',' + str(medida_atual) + ',' + Dados_DL + ',' + Dados_UL
                                print(Dados_log, file=Log_dados)
                                Log_dados.flush()

                        elif(pacote_recebido == 0):

                           perda_PK_RX += 1
                           print('Cont = ', medida_atual, ' PERDEU PACOTE ')
                           print('Pacotes perdidos = ', perda_PK_RX)
                           
                           Dados_DL = ''
                           Dados_UL = ''
                           
                           # Monta o Downlink normal mesmo perdendo o pacote
                           for i in range(TAMANHO_PACOTE_DL):
                                if i == 0:
                                    Dados_DL = str(Pacote_DL[i])
                                else:
                                    Dados_DL = Dados_DL + ', ' + str(Pacote_DL[i])
                                    
                           # Preenche o Uplink perdido com '9' para todos os 30 índices
                           for i in range(TAMANHO_PACOTE_UL):
                                if i == 0:
                                    Dados_UL = '9'
                                else:
                                    Dados_UL = Dados_UL + ', 9'

                           Tempo = time.asctime()
                           print(Tempo + ', ' + str(medida_atual) + ', Downlink: ' + Dados_DL + ' Uplink: ' + Dados_UL)

                           # Grava Pacotes com a trava de segurança
                           with lock_arquivo_log:
                                Dados_log = Tempo + ',' + str(medida_atual) + ',' + Dados_DL + ',' + Dados_UL
                                print(Dados_log, file=Log_dados)
                                Log_dados.flush()
                                
                        Tempo_gasto = time.time() - Tempo_inicio_pacote
                   
                  #except:
                     #Log_dados.close()
                     #print('[LoRa] Fim da Execução')
                 
              else:
                 print('Pacotes enviados = ', quantidade_de_medidas, ' Pacotes perdidos da rede = ', perda_PK_RX)
                 print('Tempo Entre Pacotes = ', Tempo_gasto)
                 if Log_dados and not Log_dados.closed:
                     Log_dados.close()
                     print('[LSS] Arquivo de log salvo e fechado com sucesso.')
                 Log_dados = None
                 primeiro_pacote_recebido = 0
                 perda_PK_RX = 0
                 medida_atual = 0
                 ultimo_pacote = 0
                 comanda_mudar_radio = 0 
                 # Escreve 0 automaticamente na primeira linha do PARAMETROS_SERIAL.txt para parar o teste
                 try:
                     if config_atual:
                        _, m_v, t_v, s_v = config_atual
                        with open(caminho_txt_parametros, "w") as pf:
                           pf.write("0\n")
                           pf.write(f"{m_v}\n")
                           pf.write(f"{t_v}\n")
                           pf.write(f"{s_v}\n")
                 except Exception as e:
                     print(f"[Erro] Falha ao atualizar PARAMETROS_SERIAL.txt para 0: {e}")

                 rodada_concluida = True
                 condicao_start = 0
                 num_medidas_total = 0
                 time.sleep(1)
                 continue                 
          
       except (serial.SerialException, OSError, ConnectionError) as e:
          print("\n[Aviso] Conexão Serial com o Gateway perdida! Aguardando reconexão física do cabo...")
            
          # Fecha a porta anterior com segurança se houver alguma referência aberta
          try:
              ser.close()
          except:
              pass

           # Loop contínuo de tentativa de reconexão até o usuário plugá-lo de volta
          while True:
              try:
                  time.sleep(3) # Tenta a cada 3 segundos
                  ser = serial.Serial("COM" + str(n_serial), 115200, timeout=0.5, parity=serial.PARITY_NONE)
                  ser.setDTR(False)
                  ser.setRTS(False)
                  time.sleep(0.1)
                  ser.setDTR(True)
                  ser.setRTS(True)
                  time.sleep(1.5)
                  ser.reset_input_buffer()
                  ser.reset_output_buffer()
                  print("\n[Sucesso] Gateway reconectado! Retomando o teste...")
                  break # Sai do loop de reconexão e volta ao loop principal do teste
              except (serial.SerialException, FileNotFoundError):
                  # Enquanto o cabo estiver desligado, exibe pontos na tela sem quebrar o script
                  print(".", end="", flush=True)
              except Exception as ex:
                  # Outros erros inesperados durante a tentativa
                  print(f"\n[Erro inesperado na reconexão: {ex}]. Tentando novamente...")
      
# Interrompe a aplicação N2_N3 e a conexão com MQTT
except KeyboardInterrupt:
   print("\n[Ctrl + C] Interrompido pelo usuário.")
   try:
      if 'Log_dados' in locals() and Log_dados and not Log_dados.closed:
         Log_dados.close()
   except:
      pass
   print('[LoRa] Interrompido pelo usuário')
   # Escreve 0 automaticamente na primeira linha do PARAMETROS_SERIAL.txt para parar o teste
   try:
      if config_atual:
         _, m_v, t_v, s_v = config_atual
         with open(caminho_txt_parametros, "w") as pf:
            pf.write("0\n")
            pf.write(f"{m_v}\n")
            pf.write(f"{t_v}\n")
            pf.write(f"{s_v}\n")
   except Exception as e:
      print(f"[Erro] Falha ao atualizar PARAMETROS_SERIAL.txt para 0: {e}")
   rodada_concluida = True
   time.sleep(1)
   
finally:
   try:
      ser.close()
      print("[Serial] Porta serial fechada.")
   except:
      pass
