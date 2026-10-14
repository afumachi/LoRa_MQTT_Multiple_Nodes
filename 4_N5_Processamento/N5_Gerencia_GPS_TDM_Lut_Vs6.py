# FEE247 - Desenvolvimento de Soluções IoT com LoRa e LoRaWAN
# ======= Nível 5 - Gerência ============
# Extrai RSSI, SNR, PSR, GPS e estatísticas separadamente por End Device.

# FEE247 - Desenvolvimento de Soluções IoT com LoRa e LoRaWAN
# ======= Nível 5 - Gerência ============
# Extrai RSSI, SNR, PSR, GPS e estatísticas separadamente por End Device.

import math
import os
import re
import struct
import time
import pandas as pd

# Diretórios de Parâmetros e Dados Processados (Nível 4)
dir_nivel4 = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "../3_N4_Armazenamento/Parametros/",
)
arquivo_gw_gps = os.path.join(dir_nivel4, "gateway_gps.txt")
arquivo_csv_end_devices = os.path.join(dir_nivel4, "end_devices_net_par.csv")

# Caminho da pasta de destino dos dados processados
pasta_dados_processados = os.path.join(
    "..", "3_N4_Armazenamento", "Dados_Processados"
)

# Garante que a pasta de destino existe
os.makedirs(pasta_dados_processados, exist_ok=True)

# =============================================================================
# TABELA LUT DE 72 COMBINAÇÕES INDEXADAS (EQUIVALENTE AO FIRMWARE DO ESP32 E N2/N3)
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

TAMANHO_PACOTE = 30

def ler_end_devices():
    """Lê a lista de endereços de rede dos End Devices cadastrados no CSV."""
    end_devices = []
    if os.path.exists(arquivo_csv_end_devices):
        try:
            df_devices = pd.read_csv(arquivo_csv_end_devices)
            if "endereco_rede" in df_devices.columns:
                for val in df_devices["endereco_rede"]:
                    val_str = str(val).strip()
                    if val_str.startswith("0x") or val_str.startswith("0X"):
                        end_devices.append(int(val_str, 16))
                    else:
                        end_devices.append(int(val_str))
        except Exception as e:
            print(f"[ERRO] Falha ao ler {arquivo_csv_end_devices}: {e}")
    
    # Caso o arquivo não exista ou esteja vazio, assume lista padrão com ID 1
    if not end_devices:
        end_devices = [1]
    return sorted(list(set(end_devices)))


def ler_gateway_gps():
    """Lê as coordenadas do Gateway a partir do arquivo gateway_gps.txt."""
    gw_lat, gw_lon, gw_alt = -23.005380, -46.835336, 770.0

    if os.path.exists(arquivo_gw_gps):
        try:
            with open(arquivo_gw_gps, "r") as f:
                conteudo = f.read()

            valores_dict = {}
            for linha in conteudo.splitlines():
                if "=" in linha and not linha.strip().startswith("#"):
                    chave, val = linha.split("=", 1)
                    try:
                        valores_dict[chave.strip().upper()] = float(val.strip())
                    except ValueError:
                        pass

            if "GW_LAT" in valores_dict and "GW_LON" in valores_dict:
                gw_lat = valores_dict["GW_LAT"]
                gw_lon = valores_dict["GW_LON"]
                gw_alt = valores_dict.get("GW_ALT", gw_alt)
                return gw_lat, gw_lon, gw_alt

            floats = [
                float(x) for x in re.findall(r"[-+]?\d*\.\d+|\d+", conteudo)
            ]
            if len(floats) >= 3:
                gw_lat, gw_lon, gw_alt = floats[0], floats[1], floats[2]
            elif len(floats) == 2:
                gw_lat, gw_lon = floats[0], floats[1]

        except Exception as e:
            print(f"Erro ao ler arquivo de parâmetros do Gateway: {e}")

    return gw_lat, gw_lon, gw_alt


def calcula_toa_taxa_canal(
    spreading_factor,
    bandwidth_khz,
    coding_rate,
    tamanho_pacote=TAMANHO_PACOTE,
    n_preambulo=8,
    header_impl=False,
    crc_on=True,
    low_dr_opt=None,
):
    bandwidth_hz = bandwidth_khz * 1000
    tempo_simbolo = (2**spreading_factor) / bandwidth_hz

    tempo_preambulo = (n_preambulo + 4.25) * tempo_simbolo

    if low_dr_opt is None:
        low_dr_opt = 1 if tempo_simbolo > 0.016 else 0

    valor_cr = coding_rate

    ih = 1 if header_impl else 0
    crc = 1 if crc_on else 0
    de = 1 if low_dr_opt else 0

    n_pacote = (
        8 * tamanho_pacote - 4 * spreading_factor + 28 + 16 * crc - 20 * ih
    ) / (4 * (spreading_factor - 2 * de))
    n_payload_simbolo = 8 + max(math.ceil(n_pacote) * (valor_cr + 4), 0)

    tempo_pacote_toa = n_payload_simbolo * tempo_simbolo
    toa_s = tempo_preambulo + tempo_pacote_toa
    toa_ms = toa_s * 1000

    cr = 4 / (4 + valor_cr)
    taxa_teorica = (
        spreading_factor * (bandwidth_hz / (2**spreading_factor)) * cr
    )

    return toa_ms, round(taxa_teorica, 3)


def calcula_taxa_canal(
    spreading_factor, bandwidth_khz, coding_rate, psr_percentual
):
    _, taxa_teorica = calcula_toa_taxa_canal(
        spreading_factor, bandwidth_khz, coding_rate
    )
    taxa_calculada = round((taxa_teorica * psr_percentual) / 100, 3)
    return taxa_teorica, taxa_calculada


def calcula_distancia_enlace(lat1, lon1, alt1, lat2, lon2, alt2):
    """Calcula a distância 3D em metros entre duas coordenadas geográficas."""
    if None in (lat1, lon1, alt1, lat2, lon2, alt2):
        return None

    R = 6371000.0  # Raio médio da Terra em metros
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    dist_2d = R * c

    dalt = alt2 - alt1
    dist_3d = math.sqrt(dist_2d**2 + dalt**2)

    return round(dist_3d, 2)


# Pasta de dados brutos
PASTA_ARMAZENAMENTO = os.path.join("..", "3_N4_Armazenamento")
pasta_dados_brutos = os.path.join(PASTA_ARMAZENAMENTO, "Dados_Brutos")

while True:
    try:
        # Lê dinamicamente os parâmetros do Gateway e End Devices cadastrados
        GW_LAT, GW_LON, GW_ALT = ler_gateway_gps()        
        lista_end_devices = ler_end_devices()

        arquivo_entrada = ""
        if os.path.exists(pasta_dados_brutos):
            arquivos = os.listdir(pasta_dados_brutos)
            arquivos.sort()
            for nome in arquivos:
                if nome.endswith(".txt"):
                    arquivo_entrada = os.path.join(pasta_dados_brutos, nome)

        if not arquivo_entrada:
            time.sleep(1)
            continue

        try:
            with open(arquivo_entrada, "r") as arquivo:
                linhas = arquivo.readlines()
        except (FileNotFoundError, PermissionError):
            time.sleep(1)
            continue

        # Inicializa dicionários organizados por ID do End Device
        dados_dev = {
            dev_id: {

                
                "rssi_down": [],
                "rssi_up": [],
                "snr_down": [],
                "snr_up": [],
                "psr": [],
                "taxa_teorica": [],
                "taxa_calculada": [],
                "total_pacotes": 0,
                "pacotes_recebidos": 0,
                "pacotes_perdidos": 0,
                
            }
            for dev_id in lista_end_devices
        }

        for i in range(1, len(linhas)):
            partes = linhas[i].split(",")
            
            # Endereço do End Device está em DL_B8 -> partes[10]
            dev_id = int(partes[10]) #if len(partes) > 52 else int(partes[10])

            # Se o dispositivo não estiver no dicionário, inclui dinamicamente
            if dev_id not in dados_dev:
                dados_dev[dev_id] = {
                    "rssi_down": [],
                    "rssi_up": [],
                    "snr_down": [],
                    "snr_up": [],
                    "psr": [],
                    "taxa_teorica": [],
                    "taxa_calculada": [],
                    "total_pacotes": 0,
                    "pacotes_recebidos": 0,
                    "pacotes_perdidos": 0,
                }

            dados_dev[dev_id]["total_pacotes"] += 1

            pacote_recebido = 0
            try:
                UL_B8 = int(partes[30]) # Endereço do Gateway
                UL_B19 = int(partes[41]) # Tipo PKLoRa
            except (IndexError, ValueError):
                # Se a linha estiver corrompida ou incompleta, ignora esta linha e passa para a próxima
                continue
            for j in range(15):
                if (int(partes[23 + j]) != 9): # and (UL_B8 == 0) and (UL_B19 == 1)):
                    pacote_recebido = 1
                    break
            
            if (pacote_recebido == 1):
                dados_dev[dev_id]["pacotes_recebidos"] += 1

                # RSSI / SNR Downlink e Uplink
                UL_B0 = int(partes[22])

                if UL_B0 == 127:
                    RSSI_DL = -10.5
                
                # Condição 2: Intervalo entre -10.5 e -74 dBm
                # Na ida: byte = (rssi + 74) * 2. Na volta: rssi = (byte / 2) - 74
                # Esta faixa gera bytes de 0 (para -74 dBm) até 126 (para -11 dBm)
                elif 0 <= UL_B0 < 127:
                    RSSI_DL = (UL_B0 / 2) - 74
                
                # Condição 3: Intervalo abaixo de -74 dBm (até -138 dBm)
                # Na ida: byte = ((rssi + 74) * 2) + 256. Na volta: rssi = ((byte - 256) / 2) - 74
                # Esta faixa gera bytes de 128 (para -138 dBm) até 255 (ponto logo abaixo de -74 dBm)
                elif 128 <= UL_B0 <= 255:
                    RSSI_DL = ((UL_B0 - 256) / 2) - 74
    
                '''
                RSSI_DL = (
                    ((UL_B0 - 256) / 2.0) - 74
                    if UL_B0 > 128
                    else (UL_B0 / 2.0) - 74
                )
                '''

                UL_B1 = int(partes[23])
                SNR_DL = round(((UL_B1 / 4) - 30), 2)


                UL_B2 = int(partes[24])

                if UL_B2 == 127:
                    RSSI_UL = -10.5
                
                # Condição 2: Intervalo entre -10.5 e -74 dBm
                # Na ida: byte = (rssi + 74) * 2. Na volta: rssi = (byte / 2) - 74
                # Esta faixa gera bytes de 0 (para -74 dBm) até 126 (para -11 dBm)
                elif 0 <= UL_B2 < 127:
                    RSSI_UL = (UL_B2 / 2) - 74
                
                # Condição 3: Intervalo abaixo de -74 dBm (até -138 dBm)
                # Na ida: byte = ((rssi + 74) * 2) + 256. Na volta: rssi = ((byte - 256) / 2) - 74
                # Esta faixa gera bytes de 128 (para -138 dBm) até 255 (ponto logo abaixo de -74 dBm)
                elif 128 <= UL_B2 <= 255:
                    RSSI_UL = ((UL_B2 - 256) / 2) - 74
    
                '''
                UL_B2 = int(partes[24])
                RSSI_UL = (
                    ((UL_B2 - 256) / 2.0) - 74
                    if UL_B2 > 128
                    else (UL_B2 / 2.0) - 74
                )
                '''

                UL_B3 = int(partes[25])
                SNR_UL = round(((UL_B3 / 4) - 30), 2)

                dados_dev[dev_id]["rssi_down"].append(RSSI_DL)
                dados_dev[dev_id]["rssi_up"].append(RSSI_UL)
                dados_dev[dev_id]["snr_down"].append(SNR_DL)
                dados_dev[dev_id]["snr_up"].append(SNR_UL)

            else:
                dados_dev[dev_id]["pacotes_perdidos"] += 1

            # PSR do dispositivo
            PSR = (
                dados_dev[dev_id]["pacotes_recebidos"]
                / dados_dev[dev_id]["total_pacotes"]
            ) * 100
            dados_dev[dev_id]["psr"].append(PSR)

            # Cálculo de Taxa com base na Tabela LUT pelo Pacote Byte 0 (partes[2])
            try:
                lut_index = int(partes[2])
                if 0 <= lut_index < len(RADIO_CONFIG_LUT):
                    sf_pacote, bw_hz_pacote, cr_den_pacote = RADIO_CONFIG_LUT[lut_index]
                    bw_pacote_khz = bw_hz_pacote // 1000
                    cr_pacote = cr_den_pacote - 4  # 5,6,7,8 -> 1,2,3,4

                    TAXA_TEORICA, TAXA_CALCULADA = calcula_taxa_canal(
                        sf_pacote, bw_pacote_khz, cr_pacote, PSR
                    )
                else:
                    TAXA_TEORICA, TAXA_CALCULADA = None, None
            except (ValueError, ZeroDivisionError, IndexError):
                TAXA_TEORICA, TAXA_CALCULADA = None, None

            dados_dev[dev_id]["taxa_teorica"].append(TAXA_TEORICA)
            dados_dev[dev_id]["taxa_calculada"].append(TAXA_CALCULADA)

        # Gravação dos arquivos .tmp específicos para cada End Device
        for dev_id, info in dados_dev.items():
            if info["total_pacotes"] == 0:
                continue

            arquivo_rssi = os.path.join(pasta_dados_processados, f"{dev_id}_rssi.tmp")
            arquivo_psr = os.path.join(pasta_dados_processados, f"{dev_id}_psr.tmp")
            arquivo_stats = os.path.join(pasta_dados_processados, f"{dev_id}_stats.tmp")
            arquivo_taxa = os.path.join(pasta_dados_processados, f"{dev_id}_taxa_dados.tmp")

            rssi_down_min = min(info["rssi_down"]) if info["rssi_down"] else None
            rssi_down_max = max(info["rssi_down"]) if info["rssi_down"] else None
            rssi_up_min = min(info["rssi_up"]) if info["rssi_up"] else None
            rssi_up_max = max(info["rssi_up"]) if info["rssi_up"] else None
            snr_down_min = min(info["snr_down"]) if info["snr_down"] else None
            snr_down_max = max(info["snr_down"]) if info["snr_down"] else None
            snr_up_min = min(info["snr_up"]) if info["snr_up"] else None
            snr_up_max = max(info["snr_up"]) if info["snr_up"] else None

            # Grava RSSI / SNR
            with open(arquivo_rssi, "w") as f_rssi:
                for idx in range(len(info["rssi_down"])):
                    print(
                        info["rssi_down"][idx],
                        info["rssi_up"][idx],
                        info["snr_down"][idx],
                        info["snr_up"][idx],
                        file=f_rssi,
                    )

            # Grava PSR
            with open(arquivo_psr, "w") as f_psr:
                for val in info["psr"]:
                    print(val, file=f_psr)

            # Grava Taxa de Dados
            with open(arquivo_taxa, "w") as f_taxa:
                for idx in range(len(info["taxa_teorica"])):
                    print(
                        info["taxa_teorica"][idx],
                        info["taxa_calculada"][idx],
                        file=f_taxa,
                    )

            # Grava Estatísticas
            with open(arquivo_stats, "w") as f_stats:
                print(
                    rssi_down_min,
                    rssi_down_max,
                    rssi_up_min,
                    rssi_up_max,
                    snr_down_min,
                    snr_down_max,
                    snr_up_min,
                    snr_up_max,
                    info["pacotes_perdidos"],
                    file=f_stats,
                )

            print(
                f"[N5] Sensor ID = {dev_id} | Pacotes = {info['total_pacotes']} "
                f"| Recebidos = {info['pacotes_recebidos']} | Perdidos = {info['pacotes_perdidos']} "
                f"| PSR = {info['psr'][-1] if info['psr'] else 0:.2f}%"
            )

        time.sleep(1)

    except KeyboardInterrupt:
        print("\n[Ctrl + C] Interrompido pelo usuário.")
        break
    
#===========================================================
