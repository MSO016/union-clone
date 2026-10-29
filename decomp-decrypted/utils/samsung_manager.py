import serial
import serial.tools.list_ports
import time
import logging
import re
import threading
import os
import platform
import subprocess
from typing import (Optional, List, Dict, Tuple)
logger = logging.getLogger(__name__)
class SamsungManager:
    def __init__(self, adb_manager=None):
        self.adb_manager = adb_manager
        self.serial_port = None
        self.is_connected = False
        self.current_port = None
        self.current_baudrate = None
        self.first_unlock = False
        self._lock = threading.Lock()
        self.baudrates = [115200, 9600, 38400]
        self.command_timeout = 3
    def find_samsung_ports(self) -> List[Dict]:
        samsung_ports = []
        try:
            import serial.tools.list_ports
            ports = []
            try:
                ports = list(serial.tools.list_ports.comports())
            except Exception as e:
                logger.warning(f'Erro ao listar portas COM: {str(e)}')
                try:
                    return []
                except Exception as e:
                    logger.error(f'Erro geral ao buscar portas: {str(e)}')
                    return samsung_ports
            else:
                for port in ports:
                    pass
        except Exception as e:
            logger.error(f'Erro geral ao buscar portas: {str(e)}')
        return samsung_ports
    def auto_detect_baudrate(self, port: str) -> Optional[int]:
        logger.info(f'Detectando configura├º├úo para {port}...')
        try:
            test_serial = serial.Serial(port=port, baudrate=115200, timeout=1, write_timeout=1, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
            test_serial.close()
            logger.debug(f'Usando configura├º├úo padr├úo 115200 para {port}')
        except:
            try:
                test_serial = serial.Serial(port=port, baudrate=9600, timeout=1, write_timeout=1, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
                test_serial.close()
                logger.debug(f'Usando configura├º├úo alternativa 9600 para {port}')
            except:
                logger.warning('N├úo foi poss├¡vel detectar configura├º├úo automaticamente')
                return
            return 9600
        return 115200
    def connect_serial(self, port: str, baudrate: int=None) -> bool:
        with self._lock:
            try:
                if self.serial_port and self.serial_port.is_open:
                    self.serial_port.close()
                if not baudrate:
                    baudrate = self.auto_detect_baudrate(port)
                    if not baudrate:
                        return False
            except Exception as e:
                logger.error(f'Erro ao conectar: {str(e)}')
                self.is_connected = False
                return False
            try:
                self.serial_port = serial.Serial(port=port, baudrate=baudrate, timeout=self.command_timeout, write_timeout=self.command_timeout, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
                self.current_port = port
                self.current_baudrate = baudrate
                self.is_connected = True
                logger.info(f'Conectado ├á porta {port} @ {baudrate} baud')
            except Exception as e:
                logger.error(f'Erro ao conectar: {str(e)}')
                self.is_connected = False
                return False
        return True
    def disconnect_serial(self):
        with self._lock:
            try:
                if self.serial_port and self.serial_port.is_open:
                    self.serial_port.close()
                self.is_connected = False
                self.current_port = None
                self.current_baudrate = None
                self.first_unlock = False
                logger.info('Desconectado da porta serial')
                return
            except Exception as e:
                logger.error(f'Erro ao desconectar: {str(e)}')
    def ensure_modem_unlocked(self):
        if not self.first_unlock:
            if self.is_connected:
                self._unlock_samsung_modem()
    def send_at_command(self, command: str, wait_time: float=1.5) -> Tuple[bool, str]:
        if not self.is_connected or not self.serial_port:
            return (False, 'N├úo conectado')
        with self._lock:
            try:
                if self.serial_port.in_waiting:
                    self.serial_port.read(self.serial_port.in_waiting)
                cmd_bytes = f'{command}\r\n'.encode('utf-8')
                self.serial_port.write(cmd_bytes)
                time.sleep(wait_time)
                response = ''
                attempts = 0
                while attempts < 15:
                    if self.serial_port.in_waiting:
                        data = self.serial_port.read(self.serial_port.in_waiting)
                        response += data.decode('utf-8', errors='ignore')
                        time.sleep(0.1)
                    else:
                        attempts += 1
                        time.sleep(0.1)
                if response.strip():
                    return True, response.strip()
            except Exception as e:
                logger.error(f'Erro ao enviar comando: {str(e)}')
                return False, str(e)
        return (False, 'Sem resposta')
    def _unlock_samsung_modem(self):
        try:
            self.first_unlock = True
            success, response = self.send_at_command('AT+SWATD=0')
            if success and 'OK' in response:
                logger.info('Modem Samsung pronto para comunica├º├úo')
                return
            logger.debug('Tentando m├®todo alternativo de comunica├º├úo')
            commands = ['AT+SWATD=0', 'AT+ACTIVATE=0,0,0']
            for cmd in commands:
                self.send_at_command(cmd, 0.3)
            logger.info('Comunica├º├úo estabelecida com modem Samsung')
            return
        except Exception as e:
            logger.error(f'Erro ao estabelecer comunica├º├úo: {str(e)}')
            self.first_unlock = False
    def get_device_info(self, progress_callback=None) -> Optional[Dict]:
        if not self.is_connected:
            return
        info = {}
        total_commands = 10
        current = 0
        def update_progress(msg):
            nonlocal current
            current += 1
            if progress_callback:
                progress_callback(f'[{current}/{total_commands}] {msg}')
        update_progress('Obtendo informa├º├Áes do dispositivo...')
        success, response = self.send_at_command('AT+DEVCONINFO', 3.0)
        if success and '+DEVCONINFO:' in response:
            logger.debug(f'Resposta DEVCONINFO completa: {response}')
            parsed_info = self._parse_devconinfo(response)
            info.update(parsed_info)
            if 'serialno' in parsed_info:
                logger.debug(f'Serial obtido do DEVCONINFO parse: {parsed_info['serialno']}')
        commands = [('AT+GMM', 'model', 'Modelo'), ('AT+GMR', 'revision', 'Revis├úo'), ('AT+CGSN', 'imei', 'IMEI'), ('AT+GSN', 'serialno', 'Serial'), ('AT^GETPORTMODE', 'portmode', 'Modo Porta'), ('AT+CGMR', 'build', 'Build'), ('AT+CIMI', 'imsi', 'IMSI')]
        additional_system_commands = [('AT+VERSNAME=3,2,3', 'android_version', 'Vers├úo do Sistema')]
        for cmd, key, desc in commands:
            if key in info and info[key] and info[key] not in ('NONE', 'UNKNOWN', 'N├úo dispon├¡vel', 'N/A', None):
                logger.debug(f"[DEBUG] Pulando {cmd} porque j├í temos {key} = '{info[key]}'")
                continue
            update_progress(f'Obtendo {desc}...')
            success, response = self.send_at_command(cmd, 1.0)
            if not success:
                continue
            if response:
                cleaned = self._clean_at_response(response, cmd)
                if cleaned and 'ERROR' not in cleaned:
                    info[key] = cleaned
                elif 'CME Error' in response:
                    info[key] = 'N├úo dispon├¡vel'
        for cmd, key, desc in additional_system_commands:
            if key not in info:
                update_progress(f'Obtendo {desc}...')
                success, response = self.send_at_command(cmd, 2.0)
                if not success:
                    continue
                if response:
                    parsed_version = self._parse_system_version_response(response)
                    if parsed_version:
                        info[key] = parsed_version
                        logger.debug('Vers├úo do sistema obtida com sucesso')
                    else:
                        info[key] = 'N├úo dispon├¡vel'
        if 'imei' not in info or info.get('imei') == 'N├úo dispon├¡vel':
            update_progress('Tentando m├®todo alternativo para IMEI...')
            success, response = self.send_at_command('AT+DEVCONINFO', 3.0)
            if success and 'IMEI(' in response:
                import re
                imei_match = re.search('IMEI\\(([^)]+)\\)', response)
                if imei_match and imei_match.group(1):
                    imei_value = imei_match.group(1)
                    if 'CME Error' not in imei_value:
                        info['imei'] = imei_value
        if not info.get('baseband') or info.get('baseband') == 'N├úo dispon├¡vel':
            update_progress('Tentando obter informa├º├úo de baseband...')
            success, response = self.send_at_command('AT+CGMM', 1.0)
            if success and response:
                cleaned = self._clean_at_response(response, 'AT+CGMM')
                if cleaned and 'ERROR' not in cleaned:
                    info['baseband'] = cleaned
        serial_atual = info.get('serialno')
        if serial_atual is None or serial_atual in ('NONE', 'N├úo dispon├¡vel', 'N/A'):
            update_progress('Tentando obter n├║mero serial...')
            success, response = self.send_at_command('AT+GSN', 2.0)
            if success and response:
                cleaned = self._clean_at_response(response, 'AT+GSN')
                if cleaned and 'ERROR' not in cleaned and cleaned not in ('NONE', '') and cleaned != serial_atual:
                    info['serialno'] = cleaned
                    logger.debug(f'Serial obtido via AT+GSN: {cleaned}')
                else:
                    success, response = self.send_at_command('AT+EGMR=0,7', 1.0)
                    if success and response:
                        cleaned = self._clean_at_response(response, 'AT+EGMR=0,7')
                        if cleaned and 'ERROR' not in cleaned and cleaned != '':
                            info['serialno'] = cleaned
                            logger.debug(f'Serial obtido via AT+EGMR: {cleaned}')
                        else:
                            info['serialno'] = 'Protegido pelo dispositivo'
        else:
            logger.debug(f'Serial j├í obtido via DEVCONINFO: {serial_atual}')
        for key in list(info.keys()):
            if info[key] and ('CME Error' in str(info[key]) or '+CME' in str(info[key])):
                info[key] = 'N├úo dispon├¡vel'
        if 'serialno' in info:
            logger.debug(f'Serial final retornado: {info['serialno']}')
        if info:
            return info
    def _clean_at_response(self, response: str, command: str) -> str:
        lines = response.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line == command:
                continue
            if line == 'OK':
                continue
            if line.startswith('AT'):
                continue
            if line.startswith('+CME'):
                continue
            cleaned_lines.append(line)
        if cleaned_lines:
            return '\n'.join(cleaned_lines)
        return ''
    def _parse_devconinfo(self, raw_response: str) -> Dict:
        parsed = {}
        try:
            if '+DEVCONINFO:' in raw_response:
                content = raw_response.split('+DEVCONINFO:', 1)[1]
                content = content.replace('#OK#', '').replace('\nOK', '')
                content = content.strip()
                field_map = {'MN': 'model', 'BASE': 'baseband', 'VER': 'android', 'HIDVER': 'hidden_version', 'MNC': 'mnc', 'MCC': 'mcc', 'PRD': 'product_code', 'AID': 'aid', 'CC': 'country_code', 'OMCCODE': 'csc', 'SN': 'serialno', 'IMEI': 'imei', 'UN': 'unique_number', 'PN': 'phone_number', 'CON': 'connection_type', 'LOCK': 'lock_status', 'LIMIT': 'limit_status', 'SDP': 'sdp_status', 'HVID': 'hardware_version', 'SALES': 'sales_code', 'MCPS': 'mcps'}
                pattern = '(\\w+)\\(([^)]*)\\)'
                matches = re.findall(pattern, content)
                for field, value in matches:
                    if field not in field_map:
                        continue
                    if value not in ('UNKNOWN', 'NONE'):
                        if value is None:
                            if field in ('BASE', 'SN'):
                                parsed[field_map[field]] = None
                            else:
                                parsed[field_map[field]] = 'N├úo dispon├¡vel'
                        elif value == '' and field not in ('MNC', 'MCC', 'AID', 'OMCCODE', 'PN'):
                            parsed[field_map[field]] = 'N├úo dispon├¡vel'
                        else:
                            parsed[field_map[field]] = value if value else 'N/A'
                            if field != 'SN':
                                continue
                            if not value:
                                continue
                            if value not in ('UNKNOWN', 'NONE'):
                                logger.debug(f'Serial encontrado no DEVCONINFO: {value}')
                if parsed.get('baseband') is None and parsed.get('android'):
                    android_parts = parsed['android'].split('/')
                    if len(android_parts) >= 4:
                        parsed['baseband'] = android_parts[0]
        except Exception as e:
            logger.error(f'Erro ao analisar DEVCONINFO: {str(e)}')
        return parsed
    def _parse_system_version_response(self, raw_response: str) -> Optional[str]:
        try:
            if '+VERSNAME:' in raw_response:
                import re
                match = re.search('\\+VERSNAME:3,(\\d+)', raw_response)
                if match:
                    version_number = match.group(1)
                    version_map = {'9': 'Android 9 (API 28)', '10': 'Android 10 (API 29)', '11': 'Android 11 (API 30)', '12': 'Android 12 (API 31)', '13': 'Android 13 (API 33)', '14': 'Android 14 (API 34)', '15': 'Android 15 (API 35)'}
                    friendly_name = version_map.get(version_number, f'Android {version_number}')
                    logger.debug(f'Vers├úo do sistema detectada: {friendly_name}')
                    return friendly_name
        except Exception as e:
            logger.debug(f'Erro ao analisar vers├úo do sistema: {str(e)}')
    def frp_unlock_pre_2022(self) -> Tuple[bool, str]:
        if not self.is_connected:
            return (False, 'Dispositivo n├úo conectado')
        logger.info('Iniciando FRP Unlock Pre-2022...')
        commands = ['AT+SWATD=0', 'AT+DUMPCTRL=1,0', 'AT+DEBUGLVC=0,5', 'AT+SWATD=1', 'AT+ACTIVATE=0,0,0', 'AT+SWATD=0', 'AT+DEBUGLVC=0,5', 'AT+BANDLOCK=0', 'AT+SVCIFPGM=1,3']
        success_count = 0
        for cmd in commands:
            success, response = self.send_at_command(cmd, 0.5)
            if success and ('OK' in response or len(response) > 0):
                success_count += 1
        if success_count > len(commands) / 2:
            return (True, 'Ô£à FRP Unlock Pre-2022 executado com sucesso!\nReinicie o dispositivo e complete a configura├º├úo.')
        return (False, 'ÔØî FRP Unlock falhou. Verifique se o dispositivo ├® compat├¡vel.')
    def frp_unlock_2022(self) -> Tuple[bool, str]:
        if not self.is_connected:
            return (False, 'Dispositivo n├úo conectado')
        logger.info('Iniciando FRP Unlock 2022 H├¡brido...')
        union_commands = ['AT+SWATD=0', 'AT+DEBUGLVC=0,5', 'AT+DUMPCTRL=1,0', 'AT+BANDLOCK=0', 'AT+SWATD=1', 'AT+DEBUGLVC=0,5', 'AT+SWATD=0', 'AT+SVCIFPGM=1,3', 'AT+ACTIVATE=0,0,0']
        nphonekit_commands = ['AT+KSTRINGB=0,3', 'AT+DUMPCTRL=1,0']
        union_success = 0
        for cmd in union_commands:
            success, response = self.send_at_command(cmd, 0.5)
            if success and ('OK' in response or len(response) > 0):
                union_success += 1
        nphonekit_success = 0
        for cmd in nphonekit_commands:
            try:
                success, response = self.send_at_command(cmd, 0.3)
                if success:
                    if 'OK' in response or len(response) > 0:
                        nphonekit_success += 1
                        logger.debug(f'Comando h├¡brido 2022 {cmd}: sucesso')
                    else:
                        continue
            except Exception:
                logger.debug(f'Comando h├¡brido 2022 {cmd}: falhou silenciosamente')
                continue
        if union_success > len(union_commands) / 2:
            bonus_msg = f' (H├¡bridos: +{nphonekit_success})' if nphonekit_success > 0 else ''
            return True, f'Ô£à FRP Unlock 2022 H├¡brido executado com sucesso!{bonus_msg}\nReinicie o dispositivo e complete a configura├º├úo.'
        return (False, 'ÔØî FRP Unlock falhou. Verifique a vers├úo do patch de seguran├ºa.')
    def frp_unlock_2024(self) -> Tuple[bool, str]:
        if not self.is_connected:
            return (False, 'Dispositivo n├úo conectado')
        logger.info('Iniciando FRP Unlock 2024 H├¡brido...')
        union_commands = ['AT+SWATD=0', 'AT+ACTIVATE=0,0,0', 'AT+DEBUGLVC=0,5', 'AT+KSTRINGB=0,3', 'AT+DUMPCTRL=1,0', 'AT+BANDLOCK=0', 'AT+SVCIFPGM=1,3']
        nphonekit_commands = ['AT+VERSNAME=3.2.3', 'AT+REACTIVE=1,0,0', 'AT+PRECONFIG=2,VZW', 'AT+PRECONFIG=1,0']
        union_success = 0
        for cmd in union_commands:
            success, response = self.send_at_command(cmd, 0.5)
            if success and ('OK' in response or len(response) > 0):
                union_success += 1
        nphonekit_success = 0
        for cmd in nphonekit_commands:
            try:
                success, response = self.send_at_command(cmd, 0.3)
                if success:
                    if 'OK' in response or len(response) > 0:
                        nphonekit_success += 1
                        logger.debug(f'Comando h├¡brido {cmd}: sucesso')
                    else:
                        continue
            except Exception as e:
                logger.debug(f'Comando h├¡brido {cmd}: falhou silenciosamente')
                continue
        total_success = union_success + nphonekit_success * 0.1
        success_threshold = len(union_commands) * 0.6
        if union_success >= success_threshold:
            bonus_msg = f' (Comandos h├¡bridos: +{nphonekit_success})' if nphonekit_success > 0 else ''
            return True, f'Ô£à FRP Unlock 2024 H├¡brido executado com sucesso!{bonus_msg}\nReinicie o dispositivo e complete a configura├º├úo.'
        return (False, 'ÔØî FRP Unlock falhou. Este m├®todo pode n├úo ser compat├¡vel com seu dispositivo.')
    def open_wifitest_menu(self) -> bool:
        if not self.is_connected:
            return False
        success, response = self.send_at_command('AT+WIFITEST=9,9,9,1', 1.0)
        if success:
            logger.info('Menu WIFITEST aberto')
            return True
        logger.error('Falha ao abrir menu WIFITEST')
        return False
    def reboot_device(self, mode: str='normal') -> bool:
        if not self.is_connected:
            return False
        if mode == 'normal':
            success, _ = self.send_at_command('AT+CFUN=1,1', 0.5)
            return True
        if mode == 'download':
            success, response = self.send_at_command('AT+SUDDLMOD=0,0', 1.0)
            if success or not self.is_connected:
                return True
            success2, _ = self.send_at_command('AT+CFUN=1,1', 0.5)
            return True
        return False
    def check_imei(self) -> Optional[str]:
        if not self.is_connected:
            return
        commands = ['AT+CGSN', 'AT+GSN', 'AT+DEVCONINFO']
        for cmd in commands:
            success, response = self.send_at_command(cmd)
            if success:
                imei_pattern = '\\b\\d{15}\\b'
                match = re.search(imei_pattern, response)
                if match:
                    return match.group()
    def remove_bloatware(self, progress_callback=None):
        if not self.adb_manager:
            return {'success': [], 'failed': [], 'not_found': []}
        bloatware_packages = ['com.samsung.android.bixby.agent', 'com.samsung.android.bixby.service', 'com.samsung.android.bixby.wakeup', 'com.samsung.android.app.spage', 'com.samsung.android.game.gamehome', 'com.samsung.android.game.gametools', 'com.samsung.android.ardrawing', 'com.samsung.android.aremoji', 'com.samsung.android.app.tips', 'com.samsung.android.wellbeing', 'com.samsung.android.da.daagent', 'com.samsung.android.service.livedrawing', 'com.samsung.android.app.social', 'com.facebook.katana', 'com.facebook.services', 'com.facebook.system', 'com.facebook.appmanager', 'com.microsoft.skydrive', 'com.microsoft.office.excel', 'com.microsoft.office.word', 'com.microsoft.office.powerpoint', 'com.google.android.apps.tachyon', 'com.google.android.videos', 'com.google.android.music', 'com.google.android.apps.magazines', 'com.claro.sync', 'com.claro.video', 'com.vivo.app.vivosync', 'com.tim.meutim', 'com.oi.services']
        results = {'success': [], 'failed': [], 'not_found': []}
        total = len(bloatware_packages)
        for i, package in enumerate(bloatware_packages):
            if progress_callback:
                progress_callback(i + 1, total, package)
            try:
                check_cmd = f'shell pm list packages {package}'
                check_result = None
                if self.adb_manager and hasattr(self.adb_manager, 'execute_adb_command'):
                    pass
                try:
                    check_result = self.adb_manager.execute_adb_command(check_cmd, timeout=5)
                except Exception:
                    try:
                        si = None
                        cf = 0
                        if platform.system() == 'Windows':
                            si = subprocess.STARTUPINFO()
                            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                            si.wShowWindow = subprocess.SW_HIDE
                            cf = subprocess.CREATE_NO_WINDOW
                        check_process = subprocess.run(['adb'] + check_cmd.split(), shell=False, capture_output=True, text=True, timeout=5, startupinfo=si, creationflags=cf)
                        check_result = check_process.stdout
                    except Exception:
                        check_result = None
            except Exception as e:
                logger.error(f'Erro ao processar pacote: {str(e)}')
                results['failed'].append(package)
            if check_result and package in str(check_result):
                remove_cmd = f'shell pm uninstall -k --user 0 {package}'
                remove_result = None
                if self.adb_manager and hasattr(self.adb_manager, 'execute_adb_command'):
                    try:
                        remove_result = self.adb_manager.execute_adb_command(remove_cmd, timeout=10)
                    except Exception:
                        try:
                            si = None
                            cf = 0
                            if platform.system() == 'Windows':
                                si = subprocess.STARTUPINFO()
                                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                                si.wShowWindow = subprocess.SW_HIDE
                                cf = subprocess.CREATE_NO_WINDOW
                            remove_process = subprocess.run(['adb'] + remove_cmd.split(), shell=False, capture_output=True, text=True, timeout=10, startupinfo=si, creationflags=cf)
                            remove_result = remove_process.stdout
                        except Exception:
                            remove_result = None
                else:
                    try:
                        try:
                            si = None
                            cf = 0
                            if platform.system() == 'Windows':
                                si = subprocess.STARTUPINFO()
                                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                                si.wShowWindow = subprocess.SW_HIDE
                                cf = subprocess.CREATE_NO_WINDOW
                            remove_process = subprocess.run(['adb'] + remove_cmd.split(), shell=False, capture_output=True, text=True, timeout=10, startupinfo=si, creationflags=cf)
                            remove_result = remove_process.stdout
                        except Exception:
                            remove_result = None
                    except Exception as e:
                        logger.error(f'Erro ao processar pacote: {str(e)}')
                        results['failed'].append(package)
                if remove_result:
                    remove_str = str(remove_result).lower()
                    if 'success' in remove_str or 'failure' not in remove_str and 'error' not in remove_str:
                        results['success'].append(package)
                        logger.debug(f'Pacote removido: {package}')
                        continue
                    try:
                        results['failed'].append(package)
                        logger.debug(f'Falha ao remover: {package}')
                    except Exception as e:
                        logger.error(f'Erro ao processar pacote: {str(e)}')
                        results['failed'].append(package)
                    continue
                try:
                    results['failed'].append(package)
                except Exception as e:
                    logger.error(f'Erro ao processar pacote: {str(e)}')
                    results['failed'].append(package)
                continue
            try:
                results['not_found'].append(package)
            except Exception as e:
                logger.error(f'Erro ao processar pacote: {str(e)}')
                results['failed'].append(package)
            continue
        return results
    def factory_reset_device(self) -> Tuple[bool, str]:
        if not self.is_connected:
            return (False, 'Dispositivo n├úo conectado ├á porta serial')
        logger.warning('INICIANDO FACTORY RESET - OPERA├ç├âO IRREVERS├ìVEL!')
        try:
            success, response = self.send_at_command('AT+FACTORST=0,0', 3.0)
            if success:
                response_upper = response.upper()
                if 'OK' in response_upper:
                    if any((pattern in response_upper for pattern in ('FACTORST', 'FACTORY', 'RESET'))):
                        logger.info('Factory reset executado com sucesso - Resposta confirmada')
                        return (True, 'FACTORY RESET EXECUTADO COM SUCESSO!\n\nO dispositivo deve reiniciar automaticamente e iniciar o processo de formata├º├úo.\nTODOS OS DADOS FORAM APAGADOS - Esta opera├º├úo n├úo pode ser desfeita.\n\nAguarde o dispositivo completar o processo de reset e reinicializa├º├úo.')
                    logger.info('Comando factory reset enviado - Aguardando efeito')
                    return (True, 'COMANDOS FACTORY RESET ENVIADOS\n\nOs comandos foram aceitos pelo dispositivo\nAguarde alguns segundos - o dispositivo deve reiniciar automaticamente\nSe o reset foi iniciado, TODOS OS DADOS SER├âO APAGADOS\n\nMonitore a tela do dispositivo para confirmar o processo.')
                logger.error(f'Factory reset falhou - Resposta inesperada: {response}')
                return False, f'FACTORY RESET FALHOU\n\nResposta do dispositivo: {response[:100]}...\nPoss├¡veis causas:\n  ÔÇó Dispositivo n├úo suporta este comando\n  ÔÇó Firmware bloqueou a opera├º├úo\n  ÔÇó Dispositivo em estado protegido\n\nTente outros m├®todos de factory reset se necess├írio.'
            logger.error('Falha na comunica├º├úo durante factory reset')
            return (False, 'FALHA NA COMUNICA├ç├âO\n\nN├úo foi poss├¡vel enviar os comandos para o dispositivo\nVerifique:\n  ÔÇó Conex├úo serial est├ível\n  ÔÇó Dispositivo respondendo corretamente\n  ÔÇó Cabo USB conectado corretamente\n\nTente reconectar e executar novamente.')
        except Exception as e:
            logger.error(f'Erro durante factory reset: {str(e)}')
            return False, f'ERRO DURANTE FACTORY RESET: {str(e)}'
    def test_at_commands(self) -> Dict[str, str]:
        if not self.is_connected:
            return {'Status': 'N├úo conectado'}
        test_commands = {'Teste de comunica├º├úo': 'AT', 'Informa├º├Áes do modem': 'ATI', 'Fabricante do dispositivo': 'AT+GMI', 'Modelo do dispositivo': 'AT+GMM', 'N├║mero de s├®rie': 'AT+CGSN', 'Status do dispositivo': 'AT+FUS?'}
        results = {}
        for desc, cmd in test_commands.items():
            success, response = self.send_at_command(cmd)
            if success:
                lines = response.split('\n')
                clean_response = []
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    if line == cmd:
                        continue
                    if line == 'OK':
                        continue
                    if line.startswith('AT'):
                        continue
                    clean_response.append(line)
                results[desc] = ' '.join(clean_response) if clean_response else 'OK'
            else:
                results[desc] = 'Sem resposta'
        return results
