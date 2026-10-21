# Desenvolvimento de Soluções IoT com LoRa e LoRaWAN
# ======= Nível 5 - Gerência ============
# Extrai RSSI, SNR, PSR, GPS e estatísticas separadamente por End Device.

import math
import os
import re
import struct
import time
import pandas as pd

# Diretórios de Parâmetros e Dados Processados (Nível 4)[cite: 5]
dir_nivel4 = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "../3_N4_Armazenamento/Parametros/",
)
arquivo_gw_gps = os.path.join(dir_nivel4, "gateway_gps.txt")
arquivo_csv_end_devices = os.path.join(dir_nivel4, "end_devices_net_par.csv")
arquivo_parametros_propagacao = os.path.join(dir_nivel4, "parametros_propagacao.txt")

pasta_dados_processados = os.path.join(
    "..", "3_N4_Armazenamento", "Dados_Processados"
)

os.makedirs(pasta_dados_processados, exist_ok=True)

RADIO_CONFIG_LUT = [
    (7, 125000, 5), (7, 125000, 6), (7, 125000, 7), (7, 125000, 8),
    (7, 250000, 5), (7, 250000, 6), (7, 250000, 7), (7, 250000, 8),
    (7, 500000, 5), (7, 500000, 6), (7, 500000, 7), (7, 500000, 8),
    (8, 125000, 5), (8, 125000, 6), (8, 125000, 7), (8, 125000, 8),
    (8, 250000, 5), (8, 250000, 6), (8, 250000, 7), (8, 250000, 8),
    (8, 500000, 5), (8, 500000, 6), (8, 500000, 7), (8, 500000, 8),
    (9, 125000, 5), (9, 125000, 6), (9, 125000, 7), (9, 125000, 8),
    (9, 250000, 5), (9, 250000, 6), (9, 250000, 7), (9, 250000, 8),
    (9, 500000, 5), (9, 500000, 6), (9, 500000, 7), (9, 500000, 8),
    (10, 125000, 5), (10, 125000, 6), (10, 125000, 7), (10, 125000, 8),
    (10, 250000, 5), (10, 250000, 6), (10, 250000, 7), (10, 250000, 8),
    (10, 500000, 5), (10, 500000, 6), (10, 500000, 7), (10, 500000, 8),
    (11, 125000, 5), (11, 125000, 6), (11, 125000, 7), (11, 125000, 8),
    (11, 250000, 5), (11, 250000, 6), (11, 250000, 7), (11, 250000, 8),
    (11, 500000, 5), (11, 500000, 6), (11, 500000, 7), (11, 500000, 8),
    (12, 125000, 5), (12, 125000, 6), (12, 125000, 7), (12, 125000, 8),
    (12, 250000, 5), (12, 250000, 6), (12, 250000, 7), (12, 250000, 8),
    (12, 500000, 5), (12, 500000, 6), (12, 500000, 7), (12, 500000, 8),
]

TAMANHO_PACOTE = 30

def ler_end_devices():
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
    if not end_devices:
        end_devices = [1]
    return sorted(list(set(end_devices)))

def ler_gateway_gps():
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
        except Exception as e:
            print(f"Erro ao ler arquivo de parâmetros do Gateway: {e}")
    return gw_lat, gw_lon, gw_alt

def ler_parametros_propagacao():
    nrssi_med = 10
    nsnr_med = 10
    if os.path.exists(arquivo_parametros_propagacao):
        try:
            with open(arquivo_parametros_propagacao, "r") as f:
                conteudo = f.read()
            for linha in conteudo.splitlines():
                if "=" in linha and not linha.strip().startswith("#"):
                    chave, val = linha.split("=", 1)
                    chave = chave.strip().upper()
                    if chave == "NRSSI_MED":
                        nrssi_med = int(float(val.strip()))
                    elif chave == "NSNR_MED":
                        nsnr_med = int(float(val.strip()))
        except Exception as e:
            print(f"Erro ao ler parametros_propagacao.txt: {e}")
    return nrssi_med, nsnr_med

def calcula_toa_taxa_canal(spreading_factor, bandwidth_khz, coding_rate, tamanho_pacote=TAMANHO_PACOTE, n_preambulo=8, header_impl=False, crc_on=True, low_dr_opt=None):
    bandwidth_hz = bandwidth_khz * 1000
    tempo_simbolo = (2**spreading_factor) / bandwidth_hz
    tempo_preambulo = (n_preambulo + 4.25) * tempo_simbolo
    if low_dr_opt is None:
        low_dr_opt = 1 if tempo_simbolo > 0.016 else 0
    valor_cr = coding_rate
    ih = 1 if header_impl else 0
    crc = 1 if crc_on else 0
    de = 1 if low_dr_opt else 0
    n_pacote = (8 * tamanho_pacote - 4 * spreading_factor + 28 + 16 * crc - 20 * ih) / (4 * (spreading_factor - 2 * de))
    n_payload_simbolo = 8 + max(math.ceil(n_pacote) * (valor_cr + 4), 0)
    toa_s = tempo_preambulo + (n_payload_simbolo * tempo_simbolo)
    cr = 4 / (4 + valor_cr)
    taxa_teorica = spreading_factor * (bandwidth_hz / (2**spreading_factor)) * cr
    return toa_s * 1000, round(taxa_teorica, 3)

def calcula_taxa_canal(spreading_factor, bandwidth_khz, coding_rate, psr_percentual):
    _, taxa_teorica = calcula_toa_taxa_canal(spreading_factor, bandwidth_khz, coding_rate)
    return taxa_teorica, round((taxa_teorica * psr_percentual) / 100, 3)

def calcula_distancia_enlace(lat1, lon1, alt1, lat2, lon2, alt2):
    if None in (lat1, lon1, alt1, lat2, lon2, alt2):
        return None
    R = 6371000.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(math.sqrt((R * c)**2 + (alt2 - alt1)**2), 2)

PASTA_ARMAZENAMENTO = os.path.join("..", "3_N4_Armazenamento")
pasta_dados_brutos = os.path.join(PASTA_ARMAZENAMENTO, "Dados_Brutos")

while True:
    try:
        GW_LAT, GW_LON, GW_ALT = ler_gateway_gps()        
        lista_end_devices = ler_end_devices()
        NRSSI_MED, NSNR_MED = ler_parametros_propagacao()

        arquivo_entrada = ""
        if os.path.exists(pasta_dados_brutos):
            arquivos = sorted([os.path.join(pasta_dados_brutos, n) for n in os.listdir(pasta_dados_brutos) if n.endswith(".txt")])
            if arquivos:
                arquivo_entrada = arquivos[-1]

        if not arquivo_entrada:
            time.sleep(1)
            continue

        try:
            with open(arquivo_entrada, "r") as arquivo:
                linhas = arquivo.readlines()
        except (FileNotFoundError, PermissionError):
            time.sleep(1)
            continue

        dados_dev = {
            dev_id: {
                "rssi_down": [], "rssi_up": [], "snr_down": [], "snr_up": [],
                "psr": [], "taxa_teorica": [], "taxa_calculada": [], "gps_registros": [],
                "total_pacotes": 0, "pacotes_recebidos": 0, "pacotes_perdidos": 0,
            }
            for dev_id in lista_end_devices
        }

        for i in range(1, len(linhas)):
            partes = linhas[i].split(",")
            try:
                dev_id = int(partes[10])
                UL_B8 = int(partes[30])
                UL_B19 = int(partes[41])
            except (IndexError, ValueError):
                continue

            if dev_id not in dados_dev:
                dados_dev[dev_id] = {
                    "rssi_down": [], "rssi_up": [], "snr_down": [], "snr_up": [],
                    "psr": [], "taxa_teorica": [], "taxa_calculada": [], "gps_registros": [],
                    "total_pacotes": 0, "pacotes_recebidos": 0, "pacotes_perdidos": 0,
                }

            dados_dev[dev_id]["total_pacotes"] += 1

            pacote_recebido = 0
            for j in range(15):
                if ((int(partes[25 + j]) != 9) and (UL_B8 == 0) and (UL_B19 == 1)):
                    pacote_recebido = 1
                    break
            
            if pacote_recebido == 1:
                dados_dev[dev_id]["pacotes_recebidos"] += 1

                UL_B0 = int(partes[22])
                RSSI_DL = -10.5 if UL_B0 == 127 else ((UL_B0 / 2) - 74 if 0 <= UL_B0 < 127 else ((UL_B0 - 256) / 2) - 74)
                SNR_DL = round(((int(partes[23]) / 4) - 30), 2)

                UL_B2 = int(partes[24])
                RSSI_UL = -10.5 if UL_B2 == 127 else ((UL_B2 / 2) - 74 if 0 <= UL_B2 < 127 else ((UL_B2 - 256) / 2) - 74)
                SNR_UL = round(((int(partes[25]) / 4) - 30), 2)

                dados_dev[dev_id]["rssi_down"].append(RSSI_DL)
                dados_dev[dev_id]["rssi_up"].append(RSSI_UL)
                dados_dev[dev_id]["snr_down"].append(SNR_DL)
                dados_dev[dev_id]["snr_up"].append(SNR_UL)

                try:
                    lat_raw = ((int(partes[42]) << 24) | (int(partes[43]) << 16) | (int(partes[44]) << 8) | int(partes[45]))
                    if lat_raw & 0x80000000: lat_raw -= 0x100000000
                    latitude = lat_raw / 1e6

                    lon_raw = ((int(partes[46]) << 24) | (int(partes[47]) << 16) | (int(partes[48]) << 8) | int(partes[49]))
                    if lon_raw & 0x80000000: lon_raw -= 0x100000000
                    longitude = lon_raw / 1e6

                    alt_raw = ((int(partes[50]) << 8) | int(partes[51]))
                    if alt_raw & 0x8000: alt_raw -= 0x10000
                    altitude = float(alt_raw)

                    distancia_3d = calcula_distancia_enlace(GW_LAT, GW_LON, GW_ALT, latitude, longitude, altitude)
                    dados_dev[dev_id]["gps_registros"].append((latitude, longitude, altitude, distancia_3d))
                except (IndexError, ValueError):
                    pass
            else:
                dados_dev[dev_id]["pacotes_perdidos"] += 1

            PSR = (dados_dev[dev_id]["pacotes_recebidos"] / dados_dev[dev_id]["total_pacotes"]) * 100
            dados_dev[dev_id]["psr"].append(PSR)

            try:
                lut_index = int(partes[2])
                if 0 <= lut_index < len(RADIO_CONFIG_LUT):
                    sf_p, bw_hzp, cr_denp = RADIO_CONFIG_LUT[lut_index]
                    TAXA_TEORICA, TAXA_CALCULADA = calcula_taxa_canal(sf_p, bw_hzp // 1000, cr_denp - 4, PSR)
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
            arquivo_gps_dev = os.path.join(pasta_dados_processados, f"{dev_id}_gps.tmp")

            with open(arquivo_gps_dev, "w") as f_gps:
                for lat, lon, alt, dist in info["gps_registros"]:
                    print(f"{lat:.6f} {lon:.6f} {alt:.1f} {dist}", file=f_gps)

            mm_rssi_down, mm_rssi_up, mm_snr_down, mm_snr_up = [], [], [], []
            diff_rssi_down, diff_rssi_up, diff_snr_down, diff_snr_up = [], [], [], []
            std_rssi_down, std_rssi_up, std_snr_down, std_snr_up = [], [], [], []

            for idx in range(len(info["rssi_down"])):
                # Média Móvel RSSI (Conversão dBm -> mW -> Média -> dBm)
                if idx + 1 >= NRSSI_MED:
                    w_r_dl_dbm = info["rssi_down"][idx - NRSSI_MED + 1 : idx + 1]
                    w_r_up_dbm = info["rssi_up"][idx - NRSSI_MED + 1 : idx + 1]
                    
                    mw_dl = [10.0 ** (v / 10.0) for v in w_r_dl_dbm]
                    mean_mw_dl = sum(mw_dl) / NRSSI_MED
                    m_r_dl = 10.0 * math.log10(mean_mw_dl) if mean_mw_dl > 0 else None

                    mw_up = [10.0 ** (v / 10.0) for v in w_r_up_dbm]
                    mean_mw_up = sum(mw_up) / NRSSI_MED
                    m_r_up = 10.0 * math.log10(mean_mw_up) if mean_mw_up > 0 else None

                    # Desvio Padrão Convencional RSSI
                    mean_dl_dbm = sum(w_r_dl_dbm) / NRSSI_MED
                    var_dl = sum((x - mean_dl_dbm)**2 for x in w_r_dl_dbm) / (NRSSI_MED - 1) if NRSSI_MED > 1 else 0.0
                    std_r_dl = math.sqrt(max(0.0, var_dl))

                    mean_up_dbm = sum(w_r_up_dbm) / NRSSI_MED
                    var_up = sum((x - mean_up_dbm)**2 for x in w_r_up_dbm) / (NRSSI_MED - 1) if NRSSI_MED > 1 else 0.0
                    std_r_up = math.sqrt(max(0.0, var_up))
                else:
                    m_r_dl, m_r_up = None, None
                    std_r_dl, std_r_up = None, None

                # Média Móvel SNR (Sem conversão linear)
                if idx + 1 >= NSNR_MED:
                    w_s_dl = info["snr_down"][idx - NSNR_MED + 1 : idx + 1]
                    m_s_dl = sum(w_s_dl) / NSNR_MED
                    var_s_dl = sum((x - m_s_dl)**2 for x in w_s_dl) / (NSNR_MED - 1) if NSNR_MED > 1 else 0.0
                    std_s_dl = math.sqrt(max(0.0, var_s_dl))

                    w_s_up = info["snr_up"][idx - NSNR_MED + 1 : idx + 1]
                    m_s_up = sum(w_s_up) / NSNR_MED
                    var_s_up = sum((x - m_s_up)**2 for x in w_s_up) / (NSNR_MED - 1) if NSNR_MED > 1 else 0.0
                    std_s_up = math.sqrt(max(0.0, var_s_up))
                else:
                    m_s_dl, m_s_up = None, None
                    std_s_dl, std_s_up = None, None

                mm_rssi_down.append(m_r_dl)
                mm_rssi_up.append(m_r_up)
                mm_snr_down.append(m_s_dl)
                mm_snr_up.append(m_s_up)

                std_rssi_down.append(std_r_dl)
                std_rssi_up.append(std_r_up)
                std_snr_down.append(std_s_dl)
                std_snr_up.append(std_s_up)

                diff_rssi_down.append(info["rssi_down"][idx] - m_r_dl if m_r_dl is not None else None)
                diff_rssi_up.append(info["rssi_up"][idx] - m_r_up if m_r_up is not None else None)
                diff_snr_down.append(info["snr_down"][idx] - m_s_dl if m_s_dl is not None else None)
                diff_snr_up.append(info["snr_up"][idx] - m_s_up if m_s_up is not None else None)

            # Grava no _rssi.tmp com as 20 colunas correspondentes[cite: 5]
            with open(arquivo_rssi, "w") as f_rssi:
                for idx in range(len(info["rssi_down"])):
                    def fmt(val):
                        return f"{val:.2f}" if val is not None else "None"

                    print(
                        f"{info['rssi_down'][idx]} {info['rssi_up'][idx]} {info['snr_down'][idx]} {info['snr_up'][idx]} "
                        f"{fmt(mm_rssi_down[idx])} {fmt(mm_rssi_up[idx])} {fmt(mm_snr_down[idx])} {fmt(mm_snr_up[idx])} "
                        f"{fmt(diff_rssi_down[idx])} {fmt(diff_rssi_up[idx])} {fmt(diff_snr_down[idx])} {fmt(diff_snr_up[idx])} "
                        f"{fmt(mm_rssi_down[idx])} {fmt(mm_rssi_up[idx])} {fmt(std_rssi_down[idx])} {fmt(std_rssi_up[idx])} "
                        f"{fmt(mm_snr_down[idx])} {fmt(mm_snr_up[idx])} {fmt(std_snr_down[idx])} {fmt(std_snr_up[idx])}",
                        file=f_rssi,
                    )

            with open(arquivo_psr, "w") as f_psr:
                for val in info["psr"]: print(val, file=f_psr)

            with open(arquivo_taxa, "w") as f_taxa:
                for idx in range(len(info["taxa_teorica"])):
                    print(info["taxa_teorica"][idx], info["taxa_calculada"][idx], file=f_taxa)

            with open(arquivo_stats, "w") as f_stats:
                print(min(info["rssi_down"]), max(info["rssi_down"]), min(info["rssi_up"]), max(info["rssi_up"]),
                      min(info["snr_down"]), max(info["snr_down"]), min(info["snr_up"]), max(info["snr_up"]),
                      info["pacotes_perdidos"], file=f_stats)

            # Impressão dinâmica em tela dos cálculos executados por End Device[cite: 5]
            ult_mm_r_dl = mm_rssi_down[-1] if mm_rssi_down and mm_rssi_down[-1] is not None else 0.0
            ult_mm_r_up = mm_rssi_up[-1] if mm_rssi_up and mm_rssi_up[-1] is not None else 0.0
            ult_std_r_dl = std_rssi_down[-1] if std_rssi_down and std_rssi_down[-1] is not None else 0.0
            ult_std_r_up = std_rssi_up[-1] if std_rssi_up and std_rssi_up[-1] is not None else 0.0
            ult_mm_s_dl = mm_snr_down[-1] if mm_snr_down and mm_snr_down[-1] is not None else 0.0
            ult_mm_s_up = mm_snr_up[-1] if mm_snr_up and mm_snr_up[-1] is not None else 0.0
            ult_std_s_dl = std_snr_down[-1] if std_snr_down and std_snr_down[-1] is not None else 0.0
            ult_std_s_up = std_snr_up[-1] if std_snr_up and std_snr_up[-1] is not None else 0.0

            print(
                f"[N5] Sensor ID = {dev_id} | Pkts = {info['total_pacotes']} | Rec = {info['pacotes_recebidos']} "
                f"| RSSI DL MM: {ult_mm_r_dl:.2f} (DP: {ult_std_r_dl:.2f}) | RSSI UL MM: {ult_mm_r_up:.2f} (DP: {ult_std_r_up:.2f}) "
                f"| SNR DL MM: {ult_mm_s_dl:.2f} (DP: {ult_std_s_dl:.2f}) | SNR UL MM: {ult_mm_s_up:.2f} (DP: {ult_std_s_up:.2f}) "
                f"| PSR = {info['psr'][-1] if info['psr'] else 0:.2f}%"
            )

        time.sleep(1)
    except KeyboardInterrupt:
        break



