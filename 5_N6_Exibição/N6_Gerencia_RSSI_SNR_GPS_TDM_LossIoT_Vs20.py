# Desenvolvimento de Soluções IoT com LoRa e LoRaWAN
# ======= Nível 6 - Gerência e Parâmetros LoRa ============
# Gráficos de RSSI, PSR, GPS, Atenuação IoT e Cadastro de End Devices

import time
import os
import glob
import re
import webbrowser
import tkinter.messagebox as tkMessageBox
import tkinter.filedialog as tkFileDialog
import tkinter.ttk as ttk
import tkinter
from tkinter import *
from tkinter import messagebox
from tkinter import END, messagebox
import matplotlib
matplotlib.use('TkAgg')
from matplotlib import style
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import math
import pandas as pd

style.use("ggplot")

# =============================================================================
# DIRETÓRIOS E CONSTANTES
# =============================================================================
dir_nivel4 = os.path.join(os.path.dirname(__file__), '../3_N4_Armazenamento/Parametros/')

arquivo_gw_gps = os.path.join(dir_nivel4, "gateway_gps.txt")
arquivo_parametros_propagacao = os.path.join(dir_nivel4, "parametros_propagacao.txt")

dir_dados = os.path.join(os.path.dirname(__file__), '../3_N4_Armazenamento/Dados_Processados/')
arquivo_gps_tmp = os.path.join(dir_dados, "gps.tmp")

# Caminho para o CSV de End Devices
arquivo_csv_end_devices = os.path.join(dir_nivel4, "end_devices_net_par.csv")

# Valores de fallback padrão - GPS
GW_LAT_DEFAULT = -23.005380
GW_LON_DEFAULT = -46.835336
GW_ALT_DEFAULT = 770.0

# =============================================================================
# REFRESH DAS TELAS E CONFIGURAÇÕES
# =============================================================================
REFRESH_MS = 500
MAX_PONTOS = 10000

cor_rssi_down = "#1f77b4"
cor_rssi_up = "#ff7f0e"
cor_snr_down = "#1f77b4"
cor_snr_up = "#ff7f0e"
cor_psr = "#2ca02c"
cor_taxa_teorica = "#9467bd"
cor_taxa_calculada = "#d62728"

# Atualiza arquivo de Parâmetros de Comando
pasta_parametros = os.path.join(dir_nivel4, 'PARAMETROS.txt')
os.makedirs(dir_nivel4, exist_ok=True)
with open(pasta_parametros, 'w') as parametros:
    parametros.write("0\n0\n12\n125\n8\n20\n8\n0\n0\n") 

estado_lss = "0"

def ler_end_devices():
    """Lê a lista de End Devices cadastrados no CSV para popular o Dropdown."""
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
            print(f"[ERRO] Falha ao ler CSV: {e}")
    
    if not end_devices:
        end_devices = [1]
    return sorted(list(set(end_devices)))

def get_tmp_path(nome_base):
    """Monta o caminho dinâmico do arquivo com o prefixo do End Device."""
    dev_id = end_device_selecionado.get()
    return os.path.join(dir_dados, f"{dev_id}_{nome_base}")


# =============================================================================
# FUNÇÕES DE LEITURA (GPS)
# =============================================================================
def ler_gateway_gps():
    gw_lat, gw_lon, gw_alt = GW_LAT_DEFAULT, GW_LON_DEFAULT, GW_ALT_DEFAULT
    if os.path.exists(arquivo_gw_gps):
        try:
            with open(arquivo_gw_gps, "r") as f:
                conteudo = f.read()
            floats = [float(x) for x in re.findall(r"[-+]?\d*\.\d+|\d+", conteudo)]
            if len(floats) >= 3:
                gw_lat, gw_lon, gw_alt = floats[0], floats[1], floats[2]
        except Exception: pass
    return gw_lat, gw_lon, gw_alt

def ler_ultimo_gps_por_id(dev_id):
    caminho_arquivo = os.path.join(dir_dados, f"{dev_id}_gps.tmp")
    if not os.path.exists(caminho_arquivo):
        return None
    try:
        with open(caminho_arquivo, "r") as f:
            linhas = [line.strip() for line in f if line.strip()]
            if not linhas:
                return None
            partes = linhas[-1].split()
            if len(partes) >= 4:
                return float(partes[3])
    except Exception:
        pass
    return None

def ler_ultimo_gps():
    caminho_arquivo = get_tmp_path("gps.tmp")
    if not os.path.exists(caminho_arquivo):
        return None
    try:
        with open(caminho_arquivo, "r") as f:
            linhas = [line.strip() for line in f if line.strip()]
            if not linhas:
                return None
            partes = linhas[-1].split()
            if len(partes) >= 4:
                return (float(partes[0]), float(partes[1]), float(partes[2]), float(partes[3]))
    except Exception:
        return None

def ler_parametros_propagacao_arquivo():
    p_tx, g_tx, g_rx, c, f_freq, lamb, s_rx, nrssi, nsnr = 17.0, 0.0, 0.0, 299792458.0, 903000000.0, 0.3319961, -136.0, 10, 10
    if os.path.exists(arquivo_parametros_propagacao):
        try:
            with open(arquivo_parametros_propagacao, "r") as f:
                for linha in f:
                    if "=" in linha and not linha.strip().startswith("#"):
                        k, v = linha.split("=", 1)
                        k, val = k.strip().upper(), float(v.strip())
                        if k == "P_TX": p_tx = val
                        elif k == "G_TX": g_tx = val
                        elif k == "G_RX": g_rx = val
                        elif k == "C": c = val
                        elif k == "F": f_freq = val
                        elif k == "LAMBDA": lamb = val
                        elif k == "S_RX": s_rx = val
                        elif k == "NRSSI_MED": nrssi = int(val)
                        elif k == "NSNR_MED": nsnr = int(val)
        except Exception: pass
    return p_tx, g_tx, g_rx, c, f_freq, lamb, s_rx, nrssi, nsnr

def salvar_parametros_propagacao_arquivo(nrssi_val, nsnr_val):
    p_tx, g_tx, g_rx, c, f_freq, lamb, s_rx, _, _ = ler_parametros_propagacao_arquivo()
    os.makedirs(dir_nivel4, exist_ok=True)
    try:
        with open(arquivo_parametros_propagacao, "w") as f:
            f.write(f"P_TX = {p_tx}\nG_TX = {g_tx}\nG_RX = {g_rx}\nC = {c}\nF = {f_freq}\nLAMBDA = {lamb}\nS_RX = {s_rx}\nNRSSI_MED = {int(nrssi_val)}\nNSNR_MED = {int(nsnr_val)}\n")
    except Exception: pass


# ===================== ATUALIZA GRÁFICOS (LORA) =====================
def atualizar_grafico(ax_rssi_dl, ax_rssi_dl_diff, ax_rssi_ul, ax_rssi_ul_diff, 
                      ax_snr_dl, ax_snr_dl_diff, ax_snr_ul, ax_snr_ul_diff, 
                      ax3, ax4, canvas_rssi, canvas_snr, canvas3, canvas4, 
                      raiz, label_down, label_up, label_snr_down, label_snr_up, 
                      label_psr, label_taxa_teorica, label_taxa_calculada):
    
    rssi_down, rssi_up, snr_down, snr_up = [], [], [], []
    mm_rssi_down, mm_rssi_up, mm_snr_down, mm_snr_up = [], [], [], []
    diff_rssi_down, diff_rssi_up, diff_snr_down, diff_snr_up = [], [], [], []
    mean_mm_r_dl, mean_mm_r_up, std_r_dl, std_r_up = [], [], [], []
    mean_mm_s_dl, mean_mm_s_up, std_s_dl, std_s_up = [], [], [], []
    psr, taxa_teorica, taxa_calculada = [], [], []

    try:
        with open(get_tmp_path("rssi.tmp"), 'r') as f:
            for linha in f:
                linha = linha.strip()
                if linha:
                    try:
                        p = linha.split()
                        rssi_down.append(float(p[0].replace(",", ".")))
                        rssi_up.append(float(p[1].replace(",", ".")))
                        snr_down.append(float(p[2].replace(",", ".")))
                        snr_up.append(float(p[3].replace(",", ".")))

                        def pv(idx):
                            return float(p[idx].replace(",", ".")) if len(p) > idx and p[idx] != "None" else None

                        mm_rssi_down.append(pv(4))
                        mm_rssi_up.append(pv(5))
                        mm_snr_down.append(pv(6))
                        mm_snr_up.append(pv(7))
                        diff_rssi_down.append(pv(8))
                        diff_rssi_up.append(pv(9))
                        diff_snr_down.append(pv(10))
                        diff_snr_up.append(pv(11))
                        mean_mm_r_dl.append(pv(12))
                        mean_mm_r_up.append(pv(13))
                        std_r_dl.append(pv(14))
                        std_r_up.append(pv(15))
                        mean_mm_s_dl.append(pv(16))
                        mean_mm_s_up.append(pv(17))
                        std_s_dl.append(pv(18))
                        std_s_up.append(pv(19))
                    except Exception: pass
    except FileNotFoundError: pass

    try:
        with open(get_tmp_path("psr.tmp"), 'r') as f:
            for linha in f:
                if linha.strip():
                    try: psr.append(float(linha.strip()))
                    except ValueError: pass
    except FileNotFoundError: pass

    try:
        with open(get_tmp_path("taxa_dados.tmp"), 'r') as f:
            for linha in f:
                if linha.strip():
                    try:
                        p = linha.strip().split()
                        if p[0] != "None" and p[1] != "None":
                            taxa_teorica.append(float(p[0].replace(",", ".")))
                            taxa_calculada.append(float(p[1].replace(",", ".")))
                    except Exception: pass
    except FileNotFoundError: pass

    curr_r_dl = f"RSSI DL: {rssi_down[-1]:.2f} dBm | Média MM: {f'{mean_mm_r_dl[-1]:.2f}' if mean_mm_r_dl and mean_mm_r_dl[-1] is not None else '--'} | DP: {f'{std_r_dl[-1]:.2f}' if std_r_dl and std_r_dl[-1] is not None else '--'}" if rssi_down else "RSSI DL atual: --"
    curr_r_up = f"RSSI UL: {rssi_up[-1]:.2f} dBm | Média MM: {f'{mean_mm_r_up[-1]:.2f}' if mean_mm_r_up and mean_mm_r_up[-1] is not None else '--'} | DP: {f'{std_r_up[-1]:.2f}' if std_r_up and std_r_up[-1] is not None else '--'}" if rssi_up else "RSSI UL atual: --"
    label_down.config(text=curr_r_dl)
    label_up.config(text=curr_r_up)

    curr_s_dl = f"SNR DL: {snr_down[-1]:.2f} dB | Média MM: {f'{mean_mm_s_dl[-1]:.2f}' if mean_mm_s_dl and mean_mm_s_dl[-1] is not None else '--'} | DP: {f'{std_s_dl[-1]:.2f}' if std_s_dl and std_s_dl[-1] is not None else '--'}" if snr_down else "SNR DL atual: --"
    curr_s_up = f"SNR UL: {snr_up[-1]:.2f} dB | Média MM: {f'{mean_mm_s_up[-1]:.2f}' if mean_mm_s_up and mean_mm_s_up[-1] is not None else '--'} | DP: {f'{std_s_up[-1]:.2f}' if std_s_up and std_s_up[-1] is not None else '--'}" if snr_up else "SNR UL atual: --"
    label_snr_down.config(text=curr_s_dl)
    label_snr_up.config(text=curr_s_up)

    label_psr.config(text=f"PSR atual: {round(psr[-1],2)} %" if psr else "PSR atual: --")
    label_taxa_teorica.config(text=f"Taxa Teórica atual: {round(taxa_teorica[-1],3)} bps" if taxa_teorica else "Taxa Teórica atual: --")
    label_taxa_calculada.config(text=f"Taxa Real atual: {round(taxa_calculada[-1],3)} bps" if taxa_calculada else "Taxa Real atual: --")

    ax_rssi_dl.clear(); ax_rssi_dl_diff.clear(); ax_rssi_ul.clear(); ax_rssi_ul_diff.clear()
    if rssi_down:
        x = range(len(rssi_down))
        ax_rssi_dl.plot(x, rssi_down, label="RSSI DL", color=cor_rssi_down, linewidth=1.2)
        if any(v is not None for v in mm_rssi_down): ax_rssi_dl.plot(x, mm_rssi_down, label="MM RSSI DL", linestyle="--", color="black")
        ax_rssi_dl.legend(loc='upper right', fontsize=7)
        ax_rssi_dl.set_title("RSSI Downlink & Média Móvel", fontsize=8)
        if any(v is not None for v in diff_rssi_down):
            ax_rssi_dl_diff.plot(x, diff_rssi_down, label="Dif RSSI DL", color="#d62728", linewidth=1.2)
            ax_rssi_dl_diff.axhline(0, color="gray", linestyle=":")
            ax_rssi_dl_diff.legend(loc='upper right', fontsize=7)
            ax_rssi_dl_diff.set_title("Diferença RSSI Downlink", fontsize=8)

    if rssi_up:
        x_up = range(len(rssi_up))
        ax_rssi_ul.plot(x_up, rssi_up, label="RSSI UL", color=cor_rssi_up, linewidth=1.2)
        if any(v is not None for v in mm_rssi_up): ax_rssi_ul.plot(x_up, mm_rssi_up, label="MM RSSI UL", linestyle="--", color="black")
        ax_rssi_ul.legend(loc='upper right', fontsize=7)
        ax_rssi_ul.set_title("RSSI Uplink & Média Móvel", fontsize=8)
        if any(v is not None for v in diff_rssi_up):
            ax_rssi_ul_diff.plot(x_up, diff_rssi_up, label="Dif RSSI UL", color="#9467bd", linewidth=1.2)
            ax_rssi_ul_diff.axhline(0, color="gray", linestyle=":")
            ax_rssi_ul_diff.legend(loc='upper right', fontsize=7)
            ax_rssi_ul_diff.set_title("Diferença RSSI Uplink", fontsize=8)

    ax_snr_dl.clear(); ax_snr_dl_diff.clear(); ax_snr_ul.clear(); ax_snr_ul_diff.clear()
    if snr_down:
        x_s = range(len(snr_down))
        ax_snr_dl.plot(x_s, snr_down, label="SNR DL", color=cor_snr_down, linewidth=1.2)
        if any(v is not None for v in mm_snr_down): ax_snr_dl.plot(x_s, mm_snr_down, label="MM SNR DL", linestyle="--", color="black")
        ax_snr_dl.legend(loc='upper right', fontsize=7)
        ax_snr_dl.set_title("SNR Downlink & Média Móvel", fontsize=8)
        if any(v is not None for v in diff_snr_down):
            ax_snr_dl_diff.plot(x_s, diff_snr_down, label="Dif SNR DL", color="#d62728", linewidth=1.2)
            ax_snr_dl_diff.axhline(0, color="gray", linestyle=":")
            ax_snr_dl_diff.legend(loc='upper right', fontsize=7)
            ax_snr_dl_diff.set_title("Diferença SNR Downlink", fontsize=8)

    if snr_up:
        x_su = range(len(snr_up))
        ax_snr_ul.plot(x_su, snr_up, label="SNR UL", color=cor_snr_up, linewidth=1.2)
        if any(v is not None for v in mm_snr_up): ax_snr_ul.plot(x_su, mm_snr_up, label="MM SNR UL", linestyle="--", color="black")
        ax_snr_ul.legend(loc='upper right', fontsize=7)
        ax_snr_ul.set_title("SNR Uplink & Média Móvel", fontsize=8)
        if any(v is not None for v in diff_snr_up):
            ax_snr_ul_diff.plot(x_su, diff_snr_up, label="Dif SNR UL", color="#9467bd", linewidth=1.2)
            ax_snr_ul_diff.axhline(0, color="gray", linestyle=":")
            ax_snr_ul_diff.legend(loc='upper right', fontsize=7)
            ax_snr_ul_diff.set_title("Diferença SNR Uplink", fontsize=8)

    ax3.clear(); ax4.clear()
    if psr: ax3.plot(psr, label="PSR (%)", color=cor_psr); ax3.legend(loc='upper right', fontsize=8)
    ax3.set_title("Packet Success Rate - PSR", fontsize=9)
    if taxa_teorica: ax4.plot(taxa_teorica, label="Taxa Teórica", color=cor_taxa_teorica)
    if taxa_calculada: ax4.plot(taxa_calculada, label="Taxa Real", color=cor_taxa_calculada)
    if taxa_teorica or taxa_calculada: ax4.legend(loc='upper right', fontsize=8)
    ax4.set_title("Taxa de Canal LoRa", fontsize=9)

    canvas_rssi.draw(); canvas_snr.draw(); canvas3.draw(); canvas4.draw()
    raiz.after(1000, atualizar_grafico, ax_rssi_dl, ax_rssi_dl_diff, ax_rssi_ul, ax_rssi_ul_diff, 
               ax_snr_dl, ax_snr_dl_diff, ax_snr_ul, ax_snr_ul_diff, ax3, ax4, 
               canvas_rssi, canvas_snr, canvas3, canvas4, raiz, 
               label_down, label_up, label_snr_down, label_snr_up, 
               label_psr, label_taxa_teorica, label_taxa_calculada)

def salvar(fig_rssi, fig_snr, fig_psr=None, fig_taxa=None):
    arquivo = tkFileDialog.asksaveasfilename(defaultextension=".png")
    if arquivo:
        fig_rssi.savefig(arquivo.replace(".png","_rssi.png"))
        fig_snr.savefig(arquivo.replace(".png","_snr.png"))
        if fig_psr: fig_psr.savefig(arquivo.replace(".png","_psr.png"))
        if fig_taxa: fig_taxa.savefig(arquivo.replace(".png","_taxa.png"))

# =============================================================================
# INTERFACE PRINCIPAL
# =============================================================================
raiz = Tk()
raiz.title("LoRa - GERÊNCIA DE REDE")
raiz.geometry("1350x980")
try: raiz.state('zoomed')
except Exception: pass

end_device_selecionado = StringVar(value="1")
notebook = ttk.Notebook(raiz)
notebook.pack(fill=BOTH, expand=True, padx=5, pady=5)

# =============================================================================
# ABA 1: Setup (Monitor de Pacotes LoRa) - RESTAURADA
# =============================================================================
aba_gerencia = Frame(notebook, bg="#F0F0F0")
notebook.add(aba_gerencia, text="  📡 Monitor de Pacotes LoRa ")

reg_parametrizacao = Frame(master=aba_gerencia, borderwidth=1, relief='sunken', bg="#F0F0F0")
reg_parametrizacao.place(x=10, y=10, width=300, height=310)

Label(reg_parametrizacao, font=("Arial", 14, "bold"), text="Configurações LoRa", padx=5, pady=5, bg="#F0F0F0").pack(side=TOP, anchor="n")

Label(reg_parametrizacao, text="End Device (Nó Sensor):", font=("Arial", 11, "bold"), bg="#F0F0F0").place(x=20, y=50)
lista_ids = [str(dev) for dev in ler_end_devices()]
combo_devices = ttk.Combobox(reg_parametrizacao, textvariable=end_device_selecionado, values=lista_ids, state="readonly", width=12, font=("Arial", 11))
combo_devices.place(x=20, y=80)
if lista_ids:
    combo_devices.current(0)

Label(reg_parametrizacao, text="Qtde. de Medidas", font=("Arial", 12), bg="#F0F0F0").place(x=20, y=120)
valor_intervalo = Entry(reg_parametrizacao, width=10, font=("Arial", 12))
valor_intervalo.place(x=20, y=150); valor_intervalo.insert(0, "100")

status_texto_ger = StringVar(); status_texto_ger.set("LoRa Site Survey - COMANDO PARADO")
label_status_ger = Label(reg_parametrizacao, textvariable=status_texto_ger, font=("Arial", 10, "bold"), fg="red", bg="#F0F0F0")
label_status_ger.place(x=15, y=250)

status_texto_ger2 = StringVar(); status_texto_ger2.set("LoRa Site Survey - ESTADO PARADO")
label_status_ger2 = Label(reg_parametrizacao, textvariable=status_texto_ger2, font=("Arial", 10, "bold"), fg="red", bg="#F0F0F0")
label_status_ger2.place(x=15, y=275)

def captura_num_medidas(): v = valor_intervalo.get(); return int(v) if v and int(v) > 0 else 10

def grava_comandos(condicao_start):
    with open(os.path.join(dir_nivel4, 'PARAMETROS.txt'), 'w') as s:
        s.write(f"{condicao_start}\n{captura_num_medidas()}\n12\n125\n8\n20\n8\n0\n")

btn_iniciar = Button(reg_parametrizacao, text="INICIAR", font=("Arial", 12, "bold"), width=10, command=lambda: grava_comandos(1))
btn_iniciar.place(x=25, y=200)
btn_parar = Button(reg_parametrizacao, text="PARAR", font=("Arial", 12, "bold"), width=10, command=lambda: grava_comandos(0))
btn_parar.place(x=155, y=200)

reg_estatisticas = Frame(master=aba_gerencia, borderwidth=1, relief='sunken', bg="#F0F0F0")
reg_estatisticas.place(x=10, y=330, width=300, relheight=1.0, height=400)

Label(reg_estatisticas, font=("Arial", 12, "bold"), text="RSSI / SNR / PSR (DL / UL)", bg="#F0F0F0").pack(side=TOP, anchor="n", pady=(6, 4))
texto_estatisticas = Text(reg_estatisticas, font=("Consolas", 9), bg="white", fg="black", wrap="none", relief="flat", state="disabled")
texto_estatisticas.pack(side=TOP, fill="both", expand=True, padx=6, pady=(0, 6))

def _ler_ultima_linha_valida(caminho):
    try:
        with open(caminho, 'r') as f: linhas = f.readlines()
    except FileNotFoundError: return None
    for linha in reversed(linhas):
        if linha.strip(): return linha.strip()
    return None

def ler_ultimo_valor_rssi_snr():
    linha = _ler_ultima_linha_valida(get_tmp_path("rssi.tmp"))
    if not linha: return None
    try:
        partes = linha.split()
        return (float(partes[0].replace(",", ".")), float(partes[1].replace(",", ".")), float(partes[2].replace(",", ".")), float(partes[3].replace(",", ".")))
    except (ValueError, IndexError): return None

def ler_ultimo_psr():
    linha = _ler_ultima_linha_valida(get_tmp_path("psr.tmp"))
    return float(linha) if linha else None

def ler_stats_min_max():
    try:
        with open(get_tmp_path("stats.tmp"), 'r') as f:
            linha = f.readline().strip()
    except FileNotFoundError:
        return None
    if not linha: return None
    def parse_float(val):
        if not val or val == "None": return None
        try: return float(val.replace(",", "."))
        except ValueError: return None
    return tuple(parse_float(c) for c in linha.split()[:8])

def _fmt(valor, unidade=""):
    return ("{:.2f}".format(valor) + (" " + unidade if unidade else "")) if valor is not None else "--"

def ler_ultima_taxa_calculada():
    linha = _ler_ultima_linha_valida(get_tmp_path("taxa_dados.tmp"))
    if not linha: return None
    try:
        partes = linha.split()
        if len(partes) >= 2:
            val_calc = partes[1].replace(",", ".")
            if val_calc != "None": return float(val_calc)
    except (ValueError, IndexError): pass
    return None

def atualizar_texto_estatisticas():
    dados_atual = ler_ultimo_valor_rssi_snr()
    psr_atual = ler_ultimo_psr()
    stats = ler_stats_min_max()
    taxa_calc_atual = ler_ultima_taxa_calculada()

    rssi_dl_at, rssi_ul_at, snr_dl_at, snr_ul_at = dados_atual if dados_atual else (None,)*4
    (rssi_dl_min, rssi_dl_max, rssi_ul_min, rssi_ul_max, snr_dl_min, snr_dl_max, snr_ul_min, snr_ul_max) = stats if stats else (None,)*8

    linhas_texto = [
        "=== RSSI (dBm) ===", "Downlink:", f"  atual {_fmt(rssi_dl_at):>10}", f"  min   {_fmt(rssi_dl_min):>10}   max {_fmt(rssi_dl_max):>10}",
        "Uplink:", f"  atual {_fmt(rssi_ul_at):>10}", f"  min   {_fmt(rssi_ul_min):>10}   max {_fmt(rssi_ul_max):>10}", "",
        "=== SNR (dB) ===", "Downlink:", f"  atual {_fmt(snr_dl_at):>10}", f"  min   {_fmt(snr_dl_min):>10}   max {_fmt(snr_dl_max):>10}",
        "Uplink:", f"  atual {_fmt(snr_ul_at):>10}", f"  min   {_fmt(snr_ul_min):>10}   max {_fmt(snr_ul_max):>10}", "",
        "=== PSR atual === " f"    {_fmt(psr_atual, '%'):>10}", "",
        "=== Taxa Real atual ===" f"  {_fmt(taxa_calc_atual, 'bps'):>10}"
    ]

    texto_estatisticas.config(state="normal")
    texto_estatisticas.delete("1.0", "end")
    texto_estatisticas.insert("1.0", "\n".join(linhas_texto))
    texto_estatisticas.config(state="disabled")

    path_param = os.path.join(dir_nivel4, 'cmd_lora.txt')
    if os.path.exists(path_param):
        try:
            with open(path_param, 'r') as f: linhas = [linha.strip() for linha in f.readlines()]
            cmd_lss = linhas[0] if len(linhas) > 0 else "0"
            estado_lss = linhas[1] if len(linhas) > 0 else "0"
            mensagens_cmd = {"0": ("TESTE PARADO", "red"), "1": ("CMD CONFIG RADIO", "blue"), "3": ("CMD TESTE ENLACE", "blue"), "4": ("LSS EM ANDAMENTO", "green"), "5": ("ENVIA ÚLTIMO PKT", "green"), "10": ("CMD GATEWAY MAX", "blue")}
            if cmd_lss in mensagens_cmd:
                status_texto_ger.set(f"LoRa Site Survey - {mensagens_cmd[cmd_lss][0]}")
                label_status_ger.config(fg=mensagens_cmd[cmd_lss][1])
            mensagens_est = {"0": ("ESTADO PARADO", "red"), "1": ("ERRO CONFIG RADIO", "blue"), "3": ("RADIO CONFIGURADO", "blue"), "4": ("TESTE ENLACE OK", "blue"), "5": ("ÚLTIMO PKT UL OK", "green"), "6": ("PACOTE UL RECEBIDO", "green"), "10": ("GATEWAY MAX OK", "blue")}
            if estado_lss in mensagens_est:
                status_texto_ger2.set(f"LoRa Site Survey - {mensagens_est[estado_lss][0]}")
                label_status_ger2.config(fg=mensagens_est[estado_lss][1])
        except Exception: pass
    raiz.after(REFRESH_MS, atualizar_texto_estatisticas)

atualizar_texto_estatisticas()

reg_amostragem = Frame(master=aba_gerencia, borderwidth=1, relief='sunken', bg="#F0F0F0")
reg_amostragem.place(x=320, y=10, relwidth=1.0, width=-330, relheight=1.0, height=-20)

frame_cabecalho_amostragem = Frame(reg_amostragem, bg="#F0F0F0")
frame_cabecalho_amostragem.pack(side=TOP, fill="x", padx=8, pady=(8, 4))
Label(frame_cabecalho_amostragem, font=("Arial", 14, "bold"), text="Amostragem de Pacotes DL/UL - Teste em Andamento", bg="#F0F0F0").pack(side=TOP, anchor="w")

label_arquivo_amostragem = Label(frame_cabecalho_amostragem, text="Arquivo: -- (aguardando início de teste) --", font=("Arial", 9), fg="gray30", bg="#F0F0F0")
label_arquivo_amostragem.pack(side=TOP, anchor="w", pady=(2, 0))
label_status_amostragem = Label(frame_cabecalho_amostragem, text="Medida: --", font=("Arial", 9, "bold"), fg="gray30", bg="#F0F0F0")
label_status_amostragem.pack(side=TOP, anchor="w")

frame_tabela_amostragem = Frame(reg_amostragem, bg="#F0F0F0")
frame_tabela_amostragem.pack(side=TOP, fill="both", expand=True, padx=8, pady=(4, 8))

colunas_amostragem = ("medida", "timestamp", "dl_bytes", "ul_bytes")
tabela_pacotes = ttk.Treeview(frame_tabela_amostragem, columns=colunas_amostragem, show="headings")
tabela_pacotes.heading("medida", text="Medida"); tabela_pacotes.heading("timestamp", text="Timestamp")
tabela_pacotes.heading("dl_bytes", text="Pacote Downlink (20 bytes)"); tabela_pacotes.heading("ul_bytes", text="Pacote Uplink (30 bytes)")
tabela_pacotes.column("medida", width=60, anchor="center", stretch=False); tabela_pacotes.column("timestamp", width=160, anchor="center", stretch=False)
tabela_pacotes.column("dl_bytes", width=300, anchor="w", stretch=True); tabela_pacotes.column("ul_bytes", width=420, anchor="w", stretch=True)

scroll_v_amostragem = ttk.Scrollbar(frame_tabela_amostragem, orient="vertical", command=tabela_pacotes.yview)
scroll_h_amostragem = ttk.Scrollbar(frame_tabela_amostragem, orient="horizontal", command=tabela_pacotes.xview)
tabela_pacotes.configure(yscrollcommand=scroll_v_amostragem.set, xscrollcommand=scroll_h_amostragem.set)

tabela_pacotes.grid(row=0, column=0, sticky="nsew"); scroll_v_amostragem.grid(row=0, column=1, sticky="ns")
scroll_h_amostragem.grid(row=1, column=0, sticky="ew")
frame_tabela_amostragem.rowconfigure(0, weight=1); frame_tabela_amostragem.columnconfigure(0, weight=1)

MAX_LINHAS_TABELA = 500
arquivo_atual_amostragem, posicao_leitura_amostragem, buffer_incompleto_amostragem = None, 0, ""

def localizar_arquivo_rodada_mais_recente():
    try:
        arquivos = glob.glob(os.path.join(os.path.dirname(__file__), "../3_N4_Armazenamento/Dados_Brutos/Rodada_Teste_*.txt"))
        if arquivos: return max(arquivos, key=os.path.getmtime)
    except Exception: pass
    return None

def atualizar_amostragem_pacotes():
    global arquivo_atual_amostragem, posicao_leitura_amostragem, buffer_incompleto_amostragem
    arquivo_mais_recente = localizar_arquivo_rodada_mais_recente()
    if arquivo_mais_recente != arquivo_atual_amostragem:
        for item in tabela_pacotes.get_children(): tabela_pacotes.delete(item)
        arquivo_atual_amostragem, posicao_leitura_amostragem, buffer_incompleto_amostragem = arquivo_mais_recente, 0, ""
        label_arquivo_amostragem.config(text=f"Arquivo: {os.path.basename(arquivo_mais_recente)}" if arquivo_mais_recente else "Arquivo: -- (aguardando início de teste) --")
        label_status_amostragem.config(text="Medida: --")

    if arquivo_atual_amostragem and os.path.exists(arquivo_atual_amostragem):
        try:
            with open(arquivo_atual_amostragem, 'r') as f:
                f.seek(posicao_leitura_amostragem)
                novo_conteudo = f.read()
                posicao_leitura_amostragem = f.tell()

            ultima_medida = None
            if novo_conteudo:
                buffer_incompleto_amostragem += novo_conteudo
                linhas = buffer_incompleto_amostragem.split("\n")
                buffer_incompleto_amostragem = linhas[-1]
                linhas_completas = linhas[:-1]

                for linha in linhas_completas:
                    linha = linha.strip()
                    if not linha or linha.startswith("Time stamp"): continue
                    campos = [c.strip() for c in linha.split(",")]
                    if len(campos) < 40: continue
                    tabela_pacotes.insert("", "end", values=(campos[1], campos[0], ", ".join(campos[2:22]), ", ".join(campos[22:52])))
                    ultima_medida = campos[1]

                filhos = tabela_pacotes.get_children()
                if len(filhos) > MAX_LINHAS_TABELA:
                    for item in filhos[:len(filhos) - MAX_LINHAS_TABELA]: tabela_pacotes.delete(item)
                if linhas_completas: tabela_pacotes.yview_moveto(1.0)
            if ultima_medida is not None:
                label_status_amostragem.config(text=f"Medida: {ultima_medida} de {captura_num_medidas()}")
        except Exception: pass
    raiz.after(REFRESH_MS, atualizar_amostragem_pacotes)

atualizar_amostragem_pacotes()


# =============================================================================
# ABA 2: RSSI
# =============================================================================
aba_gerencia_rssi = Frame(notebook, bg="#F0F0F0")
notebook.add(aba_gerencia_rssi, text="  📶 Gerência LoRa - RSSI  ")
frame_ctrl_rssi = Frame(aba_gerencia_rssi, bg="#F0F0F0")
frame_ctrl_rssi.pack(fill="x", padx=10, pady=(5,0))
Label(frame_ctrl_rssi, text="Janela Móvel RSSI (NRSSI_MED):", font=("Arial", 9, "bold"), bg="#F0F0F0").pack(side="left", padx=5)
entry_nrssi_med = Entry(frame_ctrl_rssi, width=6, font=("Arial", 10))
entry_nrssi_med.pack(side="left", padx=5)
_, _, _, _, _, _, _, nrssi_init, nsnr_init = ler_parametros_propagacao_arquivo()
entry_nrssi_med.insert(0, str(nrssi_init))
Button(frame_ctrl_rssi, text="💾 Salvar Janela RSSI", font=("Arial", 9), command=lambda: salvar_parametros_propagacao_arquivo(int(entry_nrssi_med.get()), nsnr_init)).pack(side="left", padx=5)

frame_labels_rssi = Frame(aba_gerencia_rssi, bg="#F0F0F0")
frame_labels_rssi.pack(fill="x", padx=10, pady=(5,2))
label_down = Label(frame_labels_rssi, text="RSSI DL atual: --", font=("Arial",9,"bold"), bg=cor_rssi_down, fg="white", relief="ridge", bd=3, pady=2)
label_down.pack(side="left", padx=5, fill="x", expand=True)
label_up = Label(frame_labels_rssi, text="RSSI UL atual: --", font=("Arial",9,"bold"), bg=cor_rssi_up, fg="white", relief="ridge", bd=3, pady=2)
label_up.pack(side="left", padx=5, fill="x", expand=True)
Button(frame_labels_rssi, text="Salvar Gráficos RSSI", command=lambda: salvar(fig_rssi, fig_snr)).pack(side="right", padx=5)

frame_rssi_sub = Frame(aba_gerencia_rssi)
frame_rssi_sub.pack(fill="both", expand=True, padx=10, pady=2)
fig_rssi = Figure(figsize=(10, 6))
ax_rssi_dl = fig_rssi.add_subplot(411)
ax_rssi_dl_diff = fig_rssi.add_subplot(412, sharex=ax_rssi_dl)
ax_rssi_ul = fig_rssi.add_subplot(413, sharex=ax_rssi_dl)
ax_rssi_ul_diff = fig_rssi.add_subplot(414, sharex=ax_rssi_dl)
fig_rssi.tight_layout()
canvas_rssi = FigureCanvasTkAgg(fig_rssi, master=frame_rssi_sub)
canvas_rssi.get_tk_widget().pack(fill="both", expand=True)

# =============================================================================
# ABA 3: SNR
# =============================================================================
aba_gerencia_snr = Frame(notebook, bg="#F0F0F0")
notebook.add(aba_gerencia_snr, text="  Gerência LoRa - SNR  ")
frame_ctrl_snr = Frame(aba_gerencia_snr, bg="#F0F0F0")
frame_ctrl_snr.pack(fill="x", padx=10, pady=(5,0))
Label(frame_ctrl_snr, text="Janela Móvel SNR (NSNR_MED):", font=("Arial", 9, "bold"), bg="#F0F0F0").pack(side="left", padx=5)
entry_nsnr_med = Entry(frame_ctrl_snr, width=6, font=("Arial", 10))
entry_nsnr_med.pack(side="left", padx=5)
entry_nsnr_med.insert(0, str(nsnr_init))
Button(frame_ctrl_snr, text="💾 Salvar Janela SNR", font=("Arial", 9), command=lambda: salvar_parametros_propagacao_arquivo(nrssi_init, int(entry_nsnr_med.get()))).pack(side="left", padx=5)

frame_labels_snr = Frame(aba_gerencia_snr, bg="#F0F0F0")
frame_labels_snr.pack(fill="x", padx=10, pady=(5,2))
label_snr_down = Label(frame_labels_snr, text="SNR DL atual: --", font=("Arial",9,"bold"), bg=cor_snr_down, fg="white", relief="ridge", bd=3, pady=2)
label_snr_down.pack(side="left", padx=5, fill="x", expand=True)
label_snr_up = Label(frame_labels_snr, text="SNR UL atual: --", font=("Arial",9,"bold"), bg=cor_snr_up, fg="white", relief="ridge", bd=3, pady=2)
label_snr_up.pack(side="left", padx=5, fill="x", expand=True)
Button(frame_labels_snr, text="Salvar Gráficos SNR", command=lambda: salvar(fig_rssi, fig_snr)).pack(side="right", padx=5)

frame_snr_sub = Frame(aba_gerencia_snr)
frame_snr_sub.pack(fill="both", expand=True, padx=10, pady=2)
fig_snr = Figure(figsize=(10, 6))
ax_snr_dl = fig_snr.add_subplot(411)
ax_snr_dl_diff = fig_snr.add_subplot(412, sharex=ax_snr_dl)
ax_snr_ul = fig_snr.add_subplot(413, sharex=ax_snr_dl)
ax_snr_ul_diff = fig_snr.add_subplot(414, sharex=ax_snr_dl)
fig_snr.tight_layout()
canvas_snr = FigureCanvasTkAgg(fig_snr, master=frame_snr_sub)
canvas_snr.get_tk_widget().pack(fill="both", expand=True)

# =============================================================================
# ABA 4: PSR - Data rate
# =============================================================================
aba_taxas = Frame(notebook, bg="#F0F0F0")
notebook.add(aba_taxas, text="  📊 PSR - Data rate  ")
frame_label_psr = Frame(aba_taxas)
frame_label_psr.pack(fill="x", padx=10, pady=(10,5))
label_psr = Label(frame_label_psr, text="PSR atual: --", font=("Arial",9,"bold"), bg=cor_psr, fg="white", relief="ridge", bd=3, width=15, pady=4)
label_psr.pack(side="left", padx=5)
Button(frame_label_psr, text="Salvar Gráficos", command=lambda: salvar(fig_rssi, fig_snr, fig3, fig4)).pack(side="right", pady=5)

frame_psr = Frame(aba_taxas); frame_psr.pack(fill="both", expand=True, padx=10, pady=5)
fig3 = Figure(figsize=(10,1.8)); ax3 = fig3.add_subplot(111)
canvas3 = FigureCanvasTkAgg(fig3, master=frame_psr)
canvas3.get_tk_widget().pack(fill="both", expand=True)

frame_labels_taxa = Frame(aba_taxas); frame_labels_taxa.pack(fill="x", padx=10, pady=(10,5))
label_taxa_teorica = Label(frame_labels_taxa, text="Taxa Teórica atual: --", font=("Arial",9,"bold"), bg=cor_taxa_teorica, fg="white", relief="ridge", bd=3, width=25, pady=4)
label_taxa_teorica.pack(side="left", padx=5)
label_taxa_calculada = Label(frame_labels_taxa, text="Taxa Real atual: --", font=("Arial",9,"bold"), bg=cor_taxa_calculada, fg="white", relief="ridge", bd=3, width=25, pady=4)
label_taxa_calculada.pack(side="left", padx=5)

frame_taxa = Frame(aba_taxas); frame_taxa.pack(fill="both", expand=True, padx=10, pady=5)
fig4 = Figure(figsize=(10,1.8)); ax4 = fig4.add_subplot(111)
canvas4 = FigureCanvasTkAgg(fig4, master=frame_taxa)
canvas4.get_tk_widget().pack(fill="both", expand=True)


# =============================================================================
# ABA 5: GPS, Distância & Atenuações do Ambiente Adicionais
# =============================================================================
class VisualizadorGPS:
    def __init__(self, notebook, raiz):
        self.root = raiz
        self.node_lat, self.node_lon, self.node_alt, self.distancia = None, None, None, None
        self.tab_gps = ttk.Frame(notebook)
        notebook.add(self.tab_gps, text="  📍 GPS, Distância & Atenuação  ")
        self.criar_widgets_tab_gps()
        self.carregar_dados_gateway_iniciais()
        self.atualizar_dados_loop()

    def criar_widgets_tab_gps(self):
        # Frame de Configurações Globais de Propagação (Frequência e dEL)
        frame_globais = ttk.LabelFrame(self.tab_gps, text=" Configurações Globais de Propagação ", padding=10)
        frame_globais.pack(fill="x", padx=15, pady=5)
        
        ttk.Label(frame_globais, text="Frequência de Operação [Hz]:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.entry_freq = ttk.Entry(frame_globais, width=15)
        self.entry_freq.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        self.entry_freq.insert(0, "903000000")

        ttk.Label(frame_globais, text="Distância de Referência (dEL) [m]:").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        self.entry_del = ttk.Entry(frame_globais, width=10)
        self.entry_del.grid(row=0, column=3, sticky="w", padx=5, pady=2)
        self.entry_del.insert(0, "1.0")

        # Frame de Atenuações do Ambiente - adicionais
        frame_amb = ttk.LabelFrame(self.tab_gps, text=" Atenuações do Ambiente - adicionais ", padding=10)
        frame_amb.pack(fill="x", padx=15, pady=5)

        self.atenuacoes_entries = {}
        defaults_amb = [
            ("Atenuação por paredes", "8"),
            ("Atenuação por lajes - andar", "10"),
            ("Atenuação armários - móveis", "4"),
            ("Atenuação por Vidro", "2"),
            ("Atenuação por máquina", "12"),
            ("Atenuação por altura Sensor", "1.5"),
            ("Outras Atenuações", "0")
        ]
        
        for idx, (label_txt, val_padrao) in enumerate(defaults_amb):
            row = idx // 2
            col = (idx % 2) * 3
            ttk.Label(frame_amb, text=f"{label_txt} [dB]:").grid(row=row, column=col, sticky="w", padx=5, pady=2)
            ent = ttk.Entry(frame_amb, width=8)
            ent.grid(row=row, column=col+1, sticky="w", padx=5, pady=2)
            ent.insert(0, val_padrao)
            self.atenuacoes_entries[label_txt] = ent

        # Frame Gateway
        frame_gw = ttk.LabelFrame(self.tab_gps, text=" Configuração do Gateway Fixo ", padding=10)
        frame_gw.pack(fill="x", padx=15, pady=5)
        grid_gw = ttk.Frame(frame_gw); grid_gw.pack(fill="x")
        
        ttk.Label(grid_gw, text="Latitude:").grid(row=0, column=0, sticky="w", pady=2)
        self.entry_gw_lat = ttk.Entry(grid_gw, width=22); self.entry_gw_lat.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(grid_gw, text="Longitude:").grid(row=1, column=0, sticky="w", pady=2)
        self.entry_gw_lon = ttk.Entry(grid_gw, width=22); self.entry_gw_lon.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(grid_gw, text="Altitude (m):").grid(row=2, column=0, sticky="w", pady=2)
        self.entry_gw_alt = ttk.Entry(grid_gw, width=22); self.entry_gw_alt.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        ttk.Button(frame_gw, text="💾 Salvar Gateway", command=self.salvar_gateway).pack(anchor="e", pady=(5, 0))

        frame_node = ttk.LabelFrame(self.tab_gps, text=" Nó Sensor (Calculado) ", padding=10)
        frame_node.pack(fill="x", padx=15, pady=5)
        self.lbl_node_lat = ttk.Label(frame_node, text="Latitude: --"); self.lbl_node_lat.pack(anchor="w")
        self.lbl_node_lon = ttk.Label(frame_node, text="Longitude: --"); self.lbl_node_lon.pack(anchor="w")
        self.lbl_node_alt = ttk.Label(frame_node, text="Altitude: --"); self.lbl_node_alt.pack(anchor="w")

        frame_dist = ttk.Frame(self.tab_gps, padding=5)
        frame_dist.pack(fill="x", padx=15, pady=2)
        self.lbl_distancia = ttk.Label(frame_dist, text="Distância de Enlace: --", font=("Arial", 11, "bold"), foreground="#0055A5")
        self.lbl_distancia.pack(anchor="center")

        frame_botoes = ttk.Frame(self.tab_gps, padding=5)
        frame_botoes.pack(fill="x", padx=15)
        ttk.Button(frame_botoes, text="🗺️ Abrir no Google Maps", command=self.abrir_maps).pack(side="left", expand=True, fill="x", padx=5)
        ttk.Button(frame_botoes, text="🔄 Recarregar Dados", command=self.recarregar_tudo).pack(side="right", expand=True, fill="x", padx=5)

    def carregar_dados_gateway_iniciais(self):
        gw_lat, gw_lon, gw_alt = ler_gateway_gps()
        self.entry_gw_lat.delete(0, END); self.entry_gw_lat.insert(0, f"{gw_lat:.6f}")
        self.entry_gw_lon.delete(0, END); self.entry_gw_lon.insert(0, f"{gw_lon:.6f}")
        self.entry_gw_alt.delete(0, END); self.entry_gw_alt.insert(0, f"{gw_alt:.1f}")

    def salvar_gateway(self):
        try:
            lat = float(self.entry_gw_lat.get().strip().replace(",", "."))
            lon = float(self.entry_gw_lon.get().strip().replace(",", "."))
            alt = float(self.entry_gw_alt.get().strip().replace(",", "."))
            os.makedirs(dir_nivel4, exist_ok=True)
            with open(arquivo_gw_gps, "w") as f:
                f.write(f"GW_LAT = {lat:.6f}\nGW_LON = {lon:.6f}\nGW_ALT = {alt:.1f}\n")
            messagebox.showinfo("Sucesso", f"Coordenadas do Gateway salvas em:\n{arquivo_gw_gps}")
        except ValueError:
            messagebox.showerror("Erro de Validação", "Insira valores numéricos válidos.")

    def atualizar_dados_loop(self):
        dados_node = ler_ultimo_gps()
        if dados_node:
            self.node_lat, self.node_lon, self.node_alt = dados_node[0:3]
            self.distancia = dados_node[3] if len(dados_node) > 3 else None
            self.lbl_node_lat.config(text=f"Latitude: {self.node_lat:.6f}°")
            self.lbl_node_lon.config(text=f"Longitude: {self.node_lon:.6f}°")
            self.lbl_node_alt.config(text=f"Altitude: {self.node_alt:.1f} m")
            self.lbl_distancia.config(text=f"Distância de Enlace: {self.distancia:.2f} m" if self.distancia is not None else "Distância de Enlace: N/A")
        self.root.after(2000, self.atualizar_dados_loop)

    def recarregar_tudo(self):
        self.carregar_dados_gateway_iniciais()

    def abrir_maps(self):
        try:
            gw_lat, gw_lon = float(self.entry_gw_lat.get().replace(",", ".")), float(self.entry_gw_lon.get().replace(",", "."))
            if self.node_lat is not None and self.node_lon is not None:
                webbrowser.open(f"https://www.google.com/maps/dir/?api=1&origin={gw_lat},{gw_lon}&destination={self.node_lat},{self.node_lon}")
        except ValueError: pass

app_gps = VisualizadorGPS(notebook, raiz)


# =============================================================================
# ABA 6: PARÂMETROS DE ATENUAÇÃO IoT
# =============================================================================
class TabAtuencaoIoT:
    def __init__(self, notebook, raiz):
        self.root = raiz
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="  📉 Parâmetros de Atenuação IoT  ")
        self.criar_widgets()

    def criar_widgets(self):
        frame_t1 = ttk.LabelFrame(self.tab, text=" Tabela 1: Parâmetros de Atenuação e Ambiente por End Device ", padding=5)
        frame_t1.pack(fill="both", expand=True, padx=10, pady=5)

        cols_t1 = ("sensor", "distancia", "beta", "paredes", "lages", "moveis", "janelas", "maquinas", "altura", "outras")
        self.tree_t1 = ttk.Treeview(frame_t1, columns=cols_t1, show="headings", height=5)
        
        headers_t1 = ["End Device", "Distância [m]", "Beta (n)", "Paredes [dB]", "Lajes [dB]", "Móveis [dB]", "Janelas [dB]", "Máquinas [dB]", "Altura NS [dB]", "Outras [dB]"]
        for col, h in zip(cols_t1, headers_t1):
            self.tree_t1.heading(col, text=h)
            self.tree_t1.column(col, anchor="center", width=95)
        
        self.tree_t1.pack(side="left", fill="both", expand=True)
        scroll_t1 = ttk.Scrollbar(frame_t1, orient="vertical", command=self.tree_t1.yview)
        self.tree_t1.configure(yscrollcommand=scroll_t1.set)
        scroll_t1.pack(side="right", fill="y")
        self.tree_t1.bind("<Double-1>", self.editar_celula_t1)

        # Botão para calcular loss utilizando os parâmetros da aba 5
        btn_calc = ttk.Button(self.tab, text="⚡ Calcular Loss IoT Total", command=self.calcular_atenuacoes)
        btn_calc.pack(pady=5)

        frame_t2 = ttk.LabelFrame(self.tab, text=" Tabela 2: Loss Espaço Livre, Log-Distance, Ambiente e Desempenho do Canal ", padding=5)
        frame_t2.pack(fill="both", expand=True, padx=10, pady=5)

        cols_t2 = ("sensor", "dist", "lel", "lpl", "latm", "ltot", "psr", "tx_teorica", "tx_real")
        self.tree_t2 = ttk.Treeview(frame_t2, columns=cols_t2, show="headings", height=5)
        headers_t2 = ["End Device", "Dist [m]", "LEL [dB]", "LPL [dB]", "Loss Amb [dB]", "Ltot [dB]", "PSR %", "Tx Teórica [bps]", "Tx Real [bps]"]
        for col, h in zip(cols_t2, headers_t2):
            self.tree_t2.heading(col, text=h)
            self.tree_t2.column(col, anchor="center", width=100)
        self.tree_t2.pack(side="left", fill="both", expand=True)
        scroll_t2 = ttk.Scrollbar(frame_t2, orient="vertical", command=self.tree_t2.yview)
        self.tree_t2.configure(yscrollcommand=scroll_t2.set)
        scroll_t2.pack(side="right", fill="y")

        frame_t3 = ttk.LabelFrame(self.tab, text=" Tabela 3: Orçamento de Enlace, Prx (Calculado vs Medido) e Ajuste Log-Distance ", padding=5)
        frame_t3.pack(fill="both", expand=True, padx=10, pady=5)

        cols_t3 = ("sensor", "dist", "ptx", "agw", "anode", "prx_max", "prx_min", "prx_med", "dp", "prx_calc", "ltot_calc", "ltot_med", "ajuste")
        self.tree_t3 = ttk.Treeview(frame_t3, columns=cols_t3, show="headings", height=5)
        headers_t3 = ["End Device", "Dist", "Ptx", "Ant GW", "Ant Node", "Prx MAX", "Prx MIN", "Prx MED", "DP", "Prx Calc", "Ltot Calc", "Ltot Med", "Ajuste Log-Dist"]
        for col, h in zip(cols_t3, headers_t3):
            self.tree_t3.heading(col, text=h)
            self.tree_t3.column(col, anchor="center", width=85)
        self.tree_t3.pack(side="left", fill="both", expand=True)
        scroll_t3 = ttk.Scrollbar(frame_t3, orient="vertical", command=self.tree_t3.yview)
        self.tree_t3.configure(yscrollcommand=scroll_t3.set)
        scroll_t3.pack(side="right", fill="y")
        self.tree_t3.bind("<Double-1>", self.editar_celula_t3)

        self.carregar_dados_tabela1()

    def carregar_dados_tabela1(self):
        for item in self.tree_t1.get_children(): self.tree_t1.delete(item)
        for item in self.tree_t2.get_children(): self.tree_t2.delete(item)
        for item in self.tree_t3.get_children(): self.tree_t3.delete(item)

        devices = ler_end_devices()
        for dev in devices:
            dist_gps = ler_ultimo_gps_por_id(dev)
            dist_val = f"{dist_gps:.2f}" if dist_gps is not None else "25.00"
            self.tree_t1.insert("", "end", values=(f"Sensor {dev}", dist_val, "3.0", "2.0", "0.0", "0.0", "1.0", "0.0", "1.5", "0.0"))
            self.tree_t2.insert("", "end", values=(f"Sensor {dev}", dist_val, "--", "--", "--", "--", "--", "--", "--"))
            self.tree_t3.insert("", "end", values=(f"Sensor {dev}", dist_val, "14.0", "0.0", "0.0", "--", "--", "--", "--", "--", "--", "--", "--"))

    def editar_celula_t1(self, event):
        item_id = self.tree_t1.identify_row(event.y)
        column = self.tree_t1.identify_column(event.x)
        if not item_id or not column: return
        col_idx = int(column.replace("#", "")) - 1
        val_atual = self.tree_t1.item(item_id, "values")[col_idx]
        
        top = Toplevel(self.root)
        top.title("Editar Parâmetro")
        top.geometry("250x120")
        ttk.Label(top, text="Novo Valor:").pack(pady=5)
        ent = ttk.Entry(top)
        ent.pack(pady=5); ent.insert(0, val_atual)

        def salvar():
            vals = list(self.tree_t1.item(item_id, "values"))
            vals[col_idx] = ent.get().strip()
            self.tree_t1.item(item_id, values=vals)
            top.destroy()

        ttk.Button(top, text="Salvar", command=salvar).pack(pady=5)

    def editar_celula_t3(self, event):
        item_id = self.tree_t3.identify_row(event.y)
        column = self.tree_t3.identify_column(event.x)
        if not item_id or not column: return
        col_idx = int(column.replace("#", "")) - 1
        if col_idx not in [2, 3, 4]:
            messagebox.showinfo("Aviso", "Apenas Potência Tx e Ganhos de Antena são editáveis nesta tabela.")
            return
        val_atual = self.tree_t3.item(item_id, "values")[col_idx]
        
        top = Toplevel(self.root)
        top.title("Editar Orçamento de Enlace")
        top.geometry("250x120")
        ttk.Label(top, text="Novo Valor:").pack(pady=5)
        ent = ttk.Entry(top)
        ent.pack(pady=5); ent.insert(0, val_atual)

        def salvar():
            vals = list(self.tree_t3.item(item_id, "values"))
            vals[col_idx] = ent.get().strip()
            self.tree_t3.item(item_id, values=vals)
            top.destroy()

        ttk.Button(top, text="Salvar", command=salvar).pack(pady=5)

    def calcular_atenuacoes(self):
        try:
            freq = float(app_gps.entry_freq.get().replace(",", "."))
            d_el = float(app_gps.entry_del.get().replace(",", "."))
            c = 299792458.0
            lamb = c / freq
        except ValueError:
            messagebox.showerror("Erro", "Frequência e Distância de Referência na Aba 5 devem ser numéricas.")
            return

        # Captura os coeficientes de atenuação definidos na Aba 5
        try:
            atn_paredes = float(app_gps.atenuacoes_entries["Atenuação por paredes"].get().replace(",", "."))
            atn_lajes = float(app_gps.atenuacoes_entries["Atenuação por lajes - andar"].get().replace(",", "."))
            atn_moveis = float(app_gps.atenuacoes_entries["Atenuação armários - móveis"].get().replace(",", "."))
            atn_vidro = float(app_gps.atenuacoes_entries["Atenuação por Vidro"].get().replace(",", "."))
            atn_maquina = float(app_gps.atenuacoes_entries["Atenuação por máquina"].get().replace(",", "."))
            atn_altura = float(app_gps.atenuacoes_entries["Atenuação por altura Sensor"].get().replace(",", "."))
            atn_outras = float(app_gps.atenuacoes_entries["Outras Atenuações"].get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Erro", "Os valores de atenuação na Aba 5 devem ser numéricos.")
            return

        for item_t1, item_t2, item_t3 in zip(self.tree_t1.get_children(), self.tree_t2.get_children(), self.tree_t3.get_children()):
            v1 = self.tree_t1.item(item_t1, "values")
            v3 = self.tree_t3.item(item_t3, "values")
            
            sensor_nome = v1[0]
            try:
                d = float(v1[1].replace(",", "."))
                beta = float(v1[2].replace(",", "."))
                n_paredes = float(v1[3].replace(",", "."))
                n_lages = float(v1[4].replace(",", "."))
                n_moveis = float(v1[5].replace(",", "."))
                n_janelas = float(v1[6].replace(",", "."))
                n_maquinas = float(v1[7].replace(",", "."))
                h_altura = float(v1[8].replace(",", "."))
                n_outras = float(v1[9].replace(",", "."))
            except ValueError:
                continue

            # Cálculo do Loss Ambiente com base na multiplicação solicitada
            lel = 20.0 * math.log10((4.0 * math.pi * d_el) / lamb) if d_el > 0 else 0.0
            lpl = 10.0 * beta * math.log10(d / d_el) if d > 0 and d_el > 0 else 0.0
            
            loss_amb = (atn_paredes * n_paredes) + \
                       (atn_lajes * n_lages) + \
                       (atn_moveis * n_moveis) + \
                       (atn_vidro * n_janelas) + \
                       (atn_maquina * n_maquinas) + \
                       (atn_altura * h_altura) + \
                       (atn_outras * n_outras)
                       
            ltot_calc = lel + lpl + loss_amb

            dev_id = re.findall(r'\d+', sensor_nome)
            dev_id_str = dev_id[0] if dev_id else "1"
            
            psr_val = "--"
            path_psr = os.path.join(dir_dados, f"{dev_id_str}_psr.tmp")
            if os.path.exists(path_psr):
                try:
                    with open(path_psr, "r") as f:
                        linhas = [l.strip() for l in f if l.strip()]
                        if linhas: psr_val = f"{float(linhas[-1]):.2f}"
                except Exception: pass

            tx_teorica_val, tx_real_val = "--", "--"
            path_taxa = os.path.join(dir_dados, f"{dev_id_str}_taxa_dados.tmp")
            if os.path.exists(path_taxa):
                try:
                    with open(path_taxa, "r") as f:
                        linhas = [l.strip() for l in f if l.strip()]
                        if linhas:
                            p_tx_a = linhas[-1].split()
                            if len(p_tx_a) >= 2:
                                tx_teorica_val = f"{float(p_tx_a[0]):.2f}"
                                tx_real_val = f"{float(p_tx_a[1]):.2f}"
                except Exception: pass

            prx_max, prx_min, prx_med, dp_val = "-59.00", "-61.50", "-62.34", "0.16"
            path_rssi = os.path.join(dir_dados, f"{dev_id_str}_rssi.tmp")
            rssi_ul_vals = []
            if os.path.exists(path_rssi):
                try:
                    with open(path_rssi, "r") as f:
                        for linha in f:
                            partes = linha.strip().split()
                            if len(partes) > 1:
                                try: rssi_ul_vals.append(float(partes[1].replace(",", ".")))
                                except ValueError: pass
                    if rssi_ul_vals:
                        prx_max = f"{max(rssi_ul_vals):.2f}"
                        prx_min = f"{min(rssi_ul_vals):.2f}"
                        media_ul = sum(rssi_ul_vals) / len(rssi_ul_vals)
                        prx_med = f"{media_ul:.2f}"
                        if len(rssi_ul_vals) > 1:
                            var = sum((x - media_ul)**2 for x in rssi_ul_vals) / (len(rssi_ul_vals) - 1)
                            dp_val = f"{math.sqrt(var):.3f}"
                except Exception: pass

            try:
                ptx = float(v3[2].replace(",", "."))
                agw = float(v3[3].replace(",", "."))
                anode = float(v3[4].replace(",", "."))
            except ValueError:
                ptx, agw, anode = 14.0, 0.0, 0.0

            prx_calc = ptx + agw + anode - ltot_calc
            ltot_med = ptx + agw + anode - float(prx_med)
            ajuste = ltot_med - ltot_calc

            self.tree_t2.item(item_t2, values=(sensor_nome, f"{d:.1f}", f"{lel:.2f}", f"{lpl:.2f}", f"{loss_amb:.2f}", f"{ltot_calc:.2f}", psr_val, tx_teorica_val, tx_real_val))
            self.tree_t3.item(item_t3, values=(sensor_nome, f"{d:.1f}", f"{ptx:.1f}", f"{agw:.1f}", f"{anode:.1f}", f"- {abs(float(prx_max)):.2f}", f"- {abs(float(prx_min)):.2f}", f"- {abs(float(prx_med)):.2f}", dp_val, f"- {abs(prx_calc):.2f}", f"{ltot_calc:.2f}", f"{ltot_med:.2f}", f"{ajuste:.2f}"))

        messagebox.showinfo("Sucesso", "Cálculos de Loss IoT Total e Orçamento de Enlace executados com sucesso com base nas atenuações da Aba 5!")

app_atenuacao = TabAtuencaoIoT(notebook, raiz)


# =============================================================================
# ABA 7: CADASTRO DE END DEVICES E PARÂMETROS DE RÁDIO - RESTAURADA
# =============================================================================
aba_end_devices = Frame(notebook, bg="#F0F0F0")
notebook.add(aba_end_devices, text="  💻 Nó Sensores (End Devices)  ")

ultima_modificacao_csv = 0

frame_tabela_ed = Frame(aba_end_devices, bg="#F0F0F0")
frame_tabela_ed.pack(side=LEFT, fill=BOTH, expand=True, padx=20, pady=20)

Label(frame_tabela_ed, text="End Devices Cadastrados no CSV", font=("Arial", 14, "bold"), bg="#F0F0F0").pack(pady=(0, 10))

colunas_ed = ("endereco_rede", "spreading_factor", "bandwidth", "coding_rate", "potencia_tx", "spreading_factor_new", "bandwidth_new", "coding_rate_new", "potencia_tx_new", "comando_radio", "comando_radio_st")
tabela_ed = ttk.Treeview(frame_tabela_ed, columns=colunas_ed, show="headings", height=20)

tabela_ed.heading("endereco_rede", text="ID da Rede")
tabela_ed.heading("spreading_factor", text="Spreading Factor")
tabela_ed.heading("bandwidth", text="Bandwidth KHz")
tabela_ed.heading("coding_rate", text="Coding Rate")
tabela_ed.heading("potencia_tx", text="Potência Tx")
tabela_ed.heading("spreading_factor_new", text="Config SF")
tabela_ed.heading("bandwidth_new", text="Config BW KHz")
tabela_ed.heading("coding_rate_new", text="Config CR")
tabela_ed.heading("potencia_tx_new", text="Config P TX")
tabela_ed.heading("comando_radio", text="Cmd LoRa")
tabela_ed.heading("comando_radio_st", text="St Cmd LoRa")

for col in colunas_ed:
    tabela_ed.column(col, anchor="center", width=60)

tabela_ed.pack(side=LEFT, fill=BOTH, expand=True)

scroll_ed = ttk.Scrollbar(frame_tabela_ed, orient="vertical", command=tabela_ed.yview)
tabela_ed.configure(yscrollcommand=scroll_ed.set)
scroll_ed.pack(side=RIGHT, fill=Y)

frame_controles_ed = Frame(aba_end_devices, bg="#F0F0F0", width=350)
frame_controles_ed.pack(side=RIGHT, fill=Y, padx=20, pady=20)

Label(frame_controles_ed, text="Gerenciar End Devices", font=("Arial", 14, "bold"), bg="#F0F0F0").pack(pady=(0, 10))

def criar_campo(texto):
    Label(frame_controles_ed, text=texto, bg="#F0F0F0", font=("Arial", 10, "bold")).pack(anchor="w", pady=(3, 0))
    entry = Entry(frame_controles_ed, font=("Arial", 11))
    entry.pack(fill=X, pady=(0, 3))
    return entry

entry_ed_id = criar_campo("Endereço de Rede (ID Nó Sensor): *")

def adicionar_ed():
    novo_id = entry_ed_id.get().strip()
    sf, bw, cr, ptx = 12, 125, 8, 20
    sf_new, bw_new, cr_new, ptx_new = 12, 125, 8, 20
    cmd_lora, st_cmd_lora = 4, 4

    if novo_id:
        tabela_ed.insert("", "end", values=(novo_id, sf, bw, cr, ptx, sf_new, bw_new, cr_new, ptx_new, cmd_lora, st_cmd_lora))
        entry_ed_id.delete(0, END)
        salvar_ed(silencioso=True)
    else:
        messagebox.showwarning("Aviso", "O Endereço de Rede (ID) é obrigatório.")

def excluir_ed():
    selecionados = tabela_ed.selection()
    if not selecionados:
        messagebox.showwarning("Aviso", "Selecione um End Device na tabela para excluir.")
        return
    for item in selecionados:
        tabela_ed.delete(item)
    salvar_ed(silencioso=True)

def salvar_ed(silencioso=False):
    global ultima_modificacao_csv
    dados_para_salvar = []
    
    for item in tabela_ed.get_children():
        valores = tabela_ed.item(item, 'values')
        dados_para_salvar.append({
            "endereco_rede": valores[0],
            "spreading_factor": valores[1],
            "bandwidth": valores[2],
            "coding_rate": valores[3],
            "potencia_tx": valores[4],
            "spreading_factor_new": valores[5],
            "bandwidth_new": valores[6],
            "coding_rate_new": valores[7],
            "potencia_tx_new": valores[8],
            "comando_radio": valores[9],
            "comando_radio_st": valores[10]
        })
    
    df_salvar = pd.DataFrame(dados_para_salvar, columns=colunas_ed)
    try:
        df_salvar.to_csv(arquivo_csv_end_devices, index=False)
        if os.path.exists(arquivo_csv_end_devices):
            ultima_modificacao_csv = os.path.getmtime(arquivo_csv_end_devices)

        if not silencioso:
            messagebox.showinfo("Sucesso", f"End Devices salvos com sucesso em:\n{arquivo_csv_end_devices}")
        
        lista_atualizada = [str(dev) for dev in ler_end_devices()]
        combo_devices['values'] = lista_atualizada
        if lista_atualizada and end_device_selecionado.get() not in lista_atualizada:
            combo_devices.current(0)
    except Exception as e:
        if not silencioso:
            messagebox.showerror("Erro", f"Erro ao salvar arquivo CSV: {e}")

Button(frame_controles_ed, text="➕ Adicionar à Lista", font=("Arial", 11), command=adicionar_ed).pack(fill=X, pady=3)
Button(frame_controles_ed, text="❌ Excluir Selecionado", font=("Arial", 11), command=excluir_ed).pack(fill=X, pady=3)

Label(frame_controles_ed, text="----------------------------------------", bg="#F0F0F0", fg="gray").pack(pady=5)
Button(frame_controles_ed, text="💾 Salvar Alterações no Arquivo", font=("Arial", 11, "bold"), bg="#4CAF50", fg="white", command=lambda: salvar_ed(silencioso=False)).pack(fill=X, pady=5)
Label(frame_controles_ed, text="----------------------------------------", bg="#F0F0F0", fg="gray").pack(pady=5)

Label(frame_controles_ed, text="Modificar os Parâmetros de Rádio LoRa", bg="#F0F0F0", fg="black", font=(None, 11, "bold")).pack(pady=5)

entry_ed_sf  = criar_campo("Spreading Factor [7 a 12] (SF):"); entry_ed_sf.insert(0, "12")
entry_ed_bw  = criar_campo("Bandwidth [125 | 250 | 500 KHz] (BW):"); entry_ed_bw.insert(0, "125")
entry_ed_cr  = criar_campo("Coding Rate [5 a 8] (CR):"); entry_ed_cr.insert(0, "8")
entry_ed_ptx = criar_campo("Potência TX [2 a 20 dBm]:"); entry_ed_ptx.insert(0, "14")

def modificar_radio_lora():
    selecionados = tabela_ed.selection()
    if not selecionados:
        messagebox.showwarning("Aviso", "Selecione um End Device na tabela para reconfigurar.")
        return

    sf_str = entry_ed_sf.get().strip()
    bw_str = entry_ed_bw.get().strip()
    cr_str = entry_ed_cr.get().strip()
    ptx_str = entry_ed_ptx.get().strip()

    if not (sf_str and bw_str and cr_str and ptx_str):
        messagebox.showwarning("Aviso", "Preencha todos os campos de parâmetro de Rádio.")
        return

    try:
        sf_val, bw_val, cr_val, ptx_val = int(sf_str), int(bw_str), int(cr_str), int(ptx_str)
        if not (7 <= sf_val <= 12):
            messagebox.showerror("Valor Invalido", "O Spreading Factor (SF) deve estar entre 7 e 12.")
            return
        if bw_val not in (125, 250, 500):
            messagebox.showerror("Valor Invalido", "O Bandwidth (BW) deve ser exatamente 125, 250 ou 500 KHz.")
            return
        if not (5 <= cr_val <= 8):
            messagebox.showerror("Valor Invalido", "O Coding Rate (CR) deve estar entre 5 e 8.")
            return
        if not (2 <= ptx_val <= 20):
            messagebox.showerror("Valor Invalido", "A Potência TX deve estar entre 2 e 20 dBm.")
            return
    except ValueError:
        messagebox.showerror("Erro de Formato", "Todos os campos de rádio devem conter valores numéricos inteiros.")
        return

    for item in selecionados:
        vals = list(tabela_ed.item(item, 'values'))
        vals[5], vals[6], vals[7], vals[8], vals[9] = str(sf_val), str(bw_val), str(cr_val), str(ptx_val), 1
        tabela_ed.item(item, values=tuple(vals))

    salvar_ed(silencioso=False)

btn_modificar_radio = Button(frame_controles_ed, text="📡 Modificar Rádio LoRa", font=("Arial", 11, "bold"), bg="#2196F3", fg="white", state="disabled", command=modificar_radio_lora)
btn_modificar_radio.pack(fill=X, pady=8)

def ao_selecionar_tabela(event):
    if tabela_ed.selection():
        btn_modificar_radio.config(state="normal")
    else:
        btn_modificar_radio.config(state="disabled")

tabela_ed.bind("<<TreeviewSelect>>", ao_selecionar_tabela)

def carregar_tabela_ed():
    global ultima_modificacao_csv
    selecionados = tabela_ed.selection()
    id_selecionado = tabela_ed.item(selecionados[0], 'values')[0] if selecionados else None

    for item in tabela_ed.get_children():
        tabela_ed.delete(item)
        
    if os.path.exists(arquivo_csv_end_devices):
        try:
            ultima_modificacao_csv = os.path.getmtime(arquivo_csv_end_devices)
            df_devices = pd.read_csv(arquivo_csv_end_devices)
            for col in colunas_ed:
                if col not in df_devices.columns: df_devices[col] = ""

            item_para_selecionar = None
            for _, row in df_devices.iterrows():
                novo_item = tabela_ed.insert("", "end", values=(
                    row["endereco_rede"], row["spreading_factor"], row["bandwidth"], row["coding_rate"], row["potencia_tx"],
                    row["spreading_factor_new"], row["bandwidth_new"], row["coding_rate_new"], row["potencia_tx_new"],
                    row["comando_radio"], row["comando_radio_st"]
                ))
                if id_selecionado is not None and str(row["endereco_rede"]) == str(id_selecionado):
                    item_para_selecionar = novo_item
            if item_para_selecionar:
                tabela_ed.selection_set(item_para_selecionar)
        except Exception as e:
            print(f"Erro ao carregar CSV na tabela: {e}")

def monitorar_atualizacao_csv():
    global ultima_modificacao_csv
    if os.path.exists(arquivo_csv_end_devices):
        try:
            mtime = os.path.getmtime(arquivo_csv_end_devices)
            if mtime > ultima_modificacao_csv:
                carregar_tabela_ed()
        except Exception:
            pass
    raiz.after(2000, monitorar_atualizacao_csv)

carregar_tabela_ed()
monitorar_atualizacao_csv()

# =============================================================================
# INICIALIZAÇÃO DE GRÁFICOS E CALLBACK DE FECHAMENTO
# =============================================================================
atualizar_grafico(ax_rssi_dl, ax_rssi_dl_diff, ax_rssi_ul, ax_rssi_ul_diff, 
                  ax_snr_dl, ax_snr_dl_diff, ax_snr_ul, ax_snr_ul_diff, ax3, ax4, 
                  canvas_rssi, canvas_snr, canvas3, canvas4, raiz, 
                  label_down, label_up, label_snr_down, label_snr_up, 
                  label_psr, label_taxa_teorica, label_taxa_calculada)

def callback():
    if tkMessageBox.askokcancel("Sair", "Tem certeza que deseja sair?"):
        grava_comandos(0)
        raiz.destroy()

raiz.protocol("WM_DELETE_WINDOW", callback)
raiz.mainloop()
