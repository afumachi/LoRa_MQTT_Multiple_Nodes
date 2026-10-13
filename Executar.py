import subprocess
import os
import time

# Define a lista de scripts com suas respectivas pastas
scripts = [
    {
        "pasta": "2_N2_N3_Python",
        "arquivo": "N2_N3_MQTT_ToA_TDM_Vs12.py",
        "titulo": "N2_N3 - MQTT & LoRa"
    },
    {
        "pasta": "4_N5_Processamento",
        "arquivo": "N5_Gerencia_GPS_TDM_Lut_Vs5.py",
        "titulo": "N5 - Processamento & GPS"
    },
    {
        "pasta": "5_N6_Exibição",
        "arquivo": "N6_Gerencia_RSSI_SNR_GPS_TDM_Vs15.py",
        "titulo": "N6 - Interface Gráfica"
    }
]

processos = []

print("=== INICIANDO SISTEMA LORA EM JANELAS SEPARADAS ===")

for item in scripts:
    pasta = item["pasta"]
    arquivo = item["arquivo"]
    titulo = item["titulo"]
    
    if os.path.exists(os.path.join(pasta, arquivo)):
        print(f"[Orquestrador] Abrindo terminal para: {arquivo}")
        
        # No Windows, 'start cmd /k' abre um novo prompt de comando dedicado com um título próprio
        # Mantemos o 'cwd=pasta' para preservar os caminhos relativos internos de cada script.
        comando = f'start "{titulo}" cmd /k python {arquivo}'
        
        p = subprocess.Popen(comando, shell=True, cwd=pasta)
        processos.append(p)
        time.sleep(0.5)
    else:
        print(f"[Erro] Arquivo não encontrado: {pasta}\\{arquivo}")

print("\nTodos os terminais foram disparados com sucesso!")
