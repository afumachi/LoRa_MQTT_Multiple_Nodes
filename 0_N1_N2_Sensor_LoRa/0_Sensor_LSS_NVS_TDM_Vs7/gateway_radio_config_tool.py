#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FERRAMENTA DE CONFIGURAÇÃO LoRa PARA GATEWAY
Calcula índices de configuração para enviar nos PacoteDL

Uso:
    python3 gateway_radio_config_tool.py
    
Ou importar como módulo:
    from gateway_radio_config_tool import RadioConfigCalculator
"""

class RadioConfigCalculator:
    """
    Calculador de índice de configuração LoRa
    Mapeia SF, BW, CR → Índice (0-71)
    """
    
    # Constantes
    SF_MIN = 7
    SF_MAX = 12
    BW_VALUES = {125000: 0, 250000: 1, 500000: 2}
    CR_MIN = 5
    CR_MAX = 8
    MAX_INDEX = 71
    
    # Configurações pré-definidas
    PRESETS = {
        'long_range': {'sf': 12, 'bw': 125000, 'cr': 8, 'description': 'Máxima distância (SF12/BW125/CR8)'},
        'long_range_default': {'sf': 12, 'bw': 125000, 'cr': 5, 'description': 'Long Range Padrão (SF12/BW125/CR5)'},
        'balanced': {'sf': 10, 'bw': 250000, 'cr': 7, 'description': 'Balanceado (SF10/BW250/CR7)'},
        'high_speed': {'sf': 7, 'bw': 500000, 'cr': 5, 'description': 'Alta velocidade (SF7/BW500/CR5)'},
        'max_robustness': {'sf': 12, 'bw': 500000, 'cr': 8, 'description': 'Máxima robustez (SF12/BW500/CR8)'},
    }
    
    @staticmethod
    def calculate_index(sf, bw, cr):
        """
        Calcula índice da tabela LUT
        
        Fórmula: índice = (SF-7)*12 + (BW_idx)*4 + (CR-5)
        
        Args:
            sf (int): Spreading Factor (7-12)
            bw (int): Bandwidth em Hz (125000, 250000, 500000)
            cr (int): Coding Rate Denominator (5, 6, 7, 8)
            
        Returns:
            int: Índice (0-71) ou -1 se inválido
        """
        # Validação
        if not RadioConfigCalculator._validate(sf, bw, cr):
            return -1
        
        bw_idx = RadioConfigCalculator.BW_VALUES[bw]
        index = (sf - 7) * 12 + bw_idx * 4 + (cr - 5)
        
        return index
    
    @staticmethod
    def decode_index(index):
        """
        Decodifica um índice para seus parâmetros constituintes
        
        Args:
            index (int): Índice (0-71)
            
        Returns:
            dict: {'sf': int, 'bw': int, 'cr': int} ou None se inválido
        """
        if index < 0 or index > 71:
            return None
        
        sf = 7 + (index // 12)
        bw_idx = (index % 12) // 4
        cr = 5 + (index % 4)
        
        # Converte bw_idx para valor real
        bw_lookup = {0: 125000, 1: 250000, 2: 500000}
        bw = bw_lookup[bw_idx]
        
        return {'sf': sf, 'bw': bw, 'cr': cr}
    
    @staticmethod
    def _validate(sf, bw, cr):
        """Valida parâmetros"""
        if not (RadioConfigCalculator.SF_MIN <= sf <= RadioConfigCalculator.SF_MAX):
            print(f"❌ SF inválido: {sf} (deve ser {RadioConfigCalculator.SF_MIN}-{RadioConfigCalculator.SF_MAX})")
            return False
        
        if bw not in RadioConfigCalculator.BW_VALUES:
            print(f"❌ BW inválido: {bw} Hz (deve ser 125000, 250000 ou 500000)")
            return False
        
        if not (RadioConfigCalculator.CR_MIN <= cr <= RadioConfigCalculator.CR_MAX):
            print(f"❌ CR inválido: {cr} (deve ser {RadioConfigCalculator.CR_MIN}-{RadioConfigCalculator.CR_MAX})")
            return False
        
        return True
    
    @staticmethod
    def get_preset(preset_name):
        """
        Retorna um preset de configuração
        
        Args:
            preset_name (str): Nome do preset
            
        Returns:
            dict: {'sf': int, 'bw': int, 'cr': int, 'index': int, 'description': str}
        """
        if preset_name not in RadioConfigCalculator.PRESETS:
            print(f"❌ Preset '{preset_name}' não encontrado")
            print(f"Presets disponíveis: {', '.join(RadioConfigCalculator.PRESETS.keys())}")
            return None
        
        preset = RadioConfigCalculator.PRESETS[preset_name].copy()
        preset['index'] = RadioConfigCalculator.calculate_index(
            preset['sf'], preset['bw'], preset['cr']
        )
        return preset
    
    @staticmethod
    def print_all_configs():
        """Imprime tabela completa de todas as 72 configurações"""
        print("\n" + "="*80)
        print(" "*20 + "TABELA COMPLETA DE CONFIGURAÇÕES LoRa (72)")
        print("="*80)
        
        for i in range(72):
            config = RadioConfigCalculator.decode_index(i)
            if config:
                bw_khz = config['bw'] / 1000
                print(f"  Idx {i:2d} | SF {config['sf']:2d} | BW {bw_khz:6.0f} kHz | CR 4/{config['cr']}")
            
            # Quebra de linha visual a cada SF (12 índices)
            if (i + 1) % 12 == 0 and i < 71:
                print("  " + "-"*60)
        
        print("="*80 + "\n")
    
    @staticmethod
    def print_presets():
        """Imprime todos os presets disponíveis"""
        print("\n" + "="*80)
        print(" "*20 + "PRESETS DE CONFIGURAÇÃO DISPONÍVEIS")
        print("="*80)
        
        for name, config in RadioConfigCalculator.PRESETS.items():
            index = RadioConfigCalculator.calculate_index(
                config['sf'], config['bw'], config['cr']
            )
            bw_khz = config['bw'] / 1000
            print(f"\n  {name.upper()}")
            print(f"    Descrição: {config['description']}")
            print(f"    SF: {config['sf']}, BW: {bw_khz:.0f} kHz, CR: 4/{config['cr']}")
            print(f"    ➜ Índice para PacoteDL[0]: {index}")
        
        print("\n" + "="*80 + "\n")


class LoRaPacketBuilder:
    """
    Construtor de pacotes LoRa para enviar aos nós sensores
    """
    
    def __init__(self):
        self.packet = [0] * 20  # PacoteDL tem 20 bytes
    
    def set_radio_config_index(self, index):
        """
        Define o índice de configuração LoRa
        
        Args:
            index (int): 0-71
        """
        if index < 0 or index > 71:
            print(f"❌ Índice inválido: {index}")
            return False
        
        self.packet[0] = index
        config = RadioConfigCalculator.decode_index(index)
        print(f"✓ Configuração de rádio definida: Idx {index} (SF{config['sf']}/BW{config['bw']//1000}kHz/CR4/{config['cr']})")
        return True
    
    def set_tx_power(self, power):
        """
        Define a potência de transmissão
        
        Args:
            power (int): 1-17 dBm
        """
        if power < 1 or power > 17:
            print(f"❌ TX Power inválido: {power} (deve ser 1-17 dBm)")
            return False
        
        self.packet[3] = power
        print(f"✓ TX Power definido: {power} dBm")
        return True
    
    def set_command(self, cmd):
        """
        Define o comando MAC (PacoteDL[7])
        
        Args:
            cmd (int): 0-5 (máquina de estado MAC)
        """
        if cmd < 0 or cmd > 5:
            print(f"❌ Comando inválido: {cmd} (deve ser 0-5)")
            return False
        
        self.packet[7] = cmd
        commands = {
            0: "Sem comando",
            1: "Iniciar reconfiguração",
            2: "Confirmar reconfiguração (não usar)",
            3: "Testar enlace",
            4: "Iniciar Site Survey",
            5: "Último pacote Site Survey"
        }
        print(f"✓ Comando definido: {cmd} ({commands.get(cmd, 'Desconhecido')})")
        return True
    
    def get_packet(self):
        """Retorna o pacote como bytes"""
        return bytes(self.packet)
    
    def get_packet_hex(self):
        """Retorna o pacote em formato hexadecimal"""
        return ' '.join(f'{b:02X}' for b in self.packet)
    
    def print_packet(self):
        """Imprime o pacote de forma legível"""
        print("\n" + "="*80)
        print(" "*30 + "PACOTE DL (20 BYTES)")
        print("="*80)
        print("\nBytes de configuração:")
        
        config = RadioConfigCalculator.decode_index(self.packet[0])
        print(f"  [0] Índice de Config: {self.packet[0]:3d} → SF{config['sf']}/BW{config['bw']//1000}kHz/CR4/{config['cr']}")
        print(f"  [1-2] Reservados: {self.packet[1]:3d} {self.packet[2]:3d}")
        print(f"  [3] TX Power: {self.packet[3]:3d} dBm")
        print(f"  [4-6] Reservados: {self.packet[4]:3d} {self.packet[5]:3d} {self.packet[6]:3d}")
        print(f"  [7] Comando MAC: {self.packet[7]:3d}")
        
        print("\nBytes restantes (8-19):")
        for i in range(8, 20):
            print(f"  [{i:2d}] Valor: {self.packet[i]:3d}")
        
        print("\nFormato Hexadecimal (para envio):")
        print(f"  {self.get_packet_hex()}")
        print("="*80 + "\n")


def interactive_menu():
    """Menu interativo para usar a ferramenta"""
    
    while True:
        print("\n" + "="*80)
        print(" "*20 + "FERRAMENTA DE CONFIGURAÇÃO LoRa (GATEWAY)")
        print("="*80)
        print("\n[1] Calcular índice a partir de parâmetros (SF, BW, CR)")
        print("[2] Decodificar índice para parâmetros")
        print("[3] Ver presets disponíveis")
        print("[4] Ver tabela completa de 72 configurações")
        print("[5] Construir pacote PacoteDL personalizado")
        print("[6] Sair\n")
        
        choice = input("Escolha uma opção (1-6): ").strip()
        
        if choice == '1':
            print("\nCalcular Índice de Configuração")
            print("-" * 40)
            try:
                sf = int(input("  Spreading Factor (7-12): "))
                bw = int(input("  Bandwidth (125000, 250000, 500000): "))
                cr = int(input("  Coding Rate (5, 6, 7, 8): "))
                
                index = RadioConfigCalculator.calculate_index(sf, bw, cr)
                if index >= 0:
                    print(f"\n✓ Índice calculado: {index}")
                    print(f"  Use PacoteDL[0] = {index} no seu pacote")
            except ValueError:
                print("❌ Entrada inválida")
        
        elif choice == '2':
            print("\nDecodificar Índice")
            print("-" * 40)
            try:
                index = int(input("  Índice (0-71): "))
                config = RadioConfigCalculator.decode_index(index)
                
                if config:
                    print(f"\n✓ Índice {index} decodificado:")
                    print(f"  Spreading Factor: {config['sf']}")
                    print(f"  Bandwidth: {config['bw']} Hz ({config['bw']/1000:.0f} kHz)")
                    print(f"  Coding Rate: 4/{config['cr']}")
            except ValueError:
                print("❌ Entrada inválida")
        
        elif choice == '3':
            RadioConfigCalculator.print_presets()
        
        elif choice == '4':
            RadioConfigCalculator.print_all_configs()
        
        elif choice == '5':
            print("\nConstruir Pacote PacoteDL")
            print("-" * 40)
            
            builder = LoRaPacketBuilder()
            
            print("\nOpções:")
            print("  [A] Usar preset")
            print("  [B] Configuração customizada")
            
            sub_choice = input("\nEscolha (A/B): ").strip().upper()
            
            if sub_choice == 'A':
                print("\nPresets disponíveis:")
                for name in RadioConfigCalculator.PRESETS.keys():
                    print(f"  - {name}")
                
                preset_name = input("\nEscolha o preset: ").strip().lower()
                preset = RadioConfigCalculator.get_preset(preset_name)
                
                if preset:
                    builder.set_radio_config_index(preset['index'])
            
            elif sub_choice == 'B':
                try:
                    sf = int(input("  Spreading Factor (7-12): "))
                    bw = int(input("  Bandwidth (125000, 250000, 500000): "))
                    cr = int(input("  Coding Rate (5, 6, 7, 8): "))
                    
                    index = RadioConfigCalculator.calculate_index(sf, bw, cr)
                    if index >= 0:
                        builder.set_radio_config_index(index)
                except ValueError:
                    print("❌ Entrada inválida")
            
            # Solicita potência e comando
            try:
                power = int(input("\nTX Power (1-17 dBm): "))
                builder.set_tx_power(power)
                
                cmd = int(input("Comando MAC (0-5): "))
                builder.set_command(cmd)
            except ValueError:
                print("❌ Entrada inválida")
            
            builder.print_packet()
        
        elif choice == '6':
            print("Saindo...\n")
            break
        
        else:
            print("❌ Opção inválida")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Modo linha de comando
        if sys.argv[1] == '--table':
            RadioConfigCalculator.print_all_configs()
        elif sys.argv[1] == '--presets':
            RadioConfigCalculator.print_presets()
        elif sys.argv[1] == '--calculate':
            if len(sys.argv) == 5:
                try:
                    sf = int(sys.argv[2])
                    bw = int(sys.argv[3])
                    cr = int(sys.argv[4])
                    index = RadioConfigCalculator.calculate_index(sf, bw, cr)
                    print(f"Índice: {index}")
                except:
                    print("Uso: python3 gateway_radio_config_tool.py --calculate SF BW CR")
            else:
                print("Uso: python3 gateway_radio_config_tool.py --calculate SF BW CR")
        else:
            print("Opções: --table, --presets, --calculate SF BW CR")
    else:
        # Modo interativo
        interactive_menu()

