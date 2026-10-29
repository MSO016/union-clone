from app.utils.adb_manager import ADBManager
import os
import platform
import subprocess
import logging
from pathlib import Path
import xml.etree.ElementTree as ET
class FastbootManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.fastboot_path = None
        try:
            from app.utils.path_manager import PathManager
            self.platform_tools_dir = PathManager.get_platform_tools_dir()
        except Exception:
            self.platform_tools_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'app', 'database', 'platform-tools')
        if platform.system() == 'Windows':
            self.startupinfo = subprocess.STARTUPINFO()
            self.startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.creation_flags = subprocess.CREATE_NO_WINDOW
            return
        self.startupinfo = None
        self.creation_flags = 0
    def find_fastboot_path(self):
        local_fastboot = os.path.join(self.platform_tools_dir, 'fastboot.exe' if platform.system() == 'Windows' else 'fastboot')
        if os.path.exists(local_fastboot):
            self.logger.debug(f'Fastboot encontrado em desenvolvimento: {local_fastboot}')
            return local_fastboot
        if platform.system() == 'Windows':
            installation_paths = ['C:\\Program Files (x86)\\Technicians Union - Smartphone Solutions\\platform-tools', 'C:\\Program Files\\Technicians Union - Smartphone Solutions\\platform-tools']
            for install_path in installation_paths:
                fastboot_path = os.path.join(install_path, 'fastboot.exe')
                if os.path.exists(fastboot_path):
                    self.logger.debug(f'Fastboot encontrado em instala├º├úo: {fastboot_path}')
                    return fastboot_path
        if platform.system() == 'Windows':
            paths = os.environ.get('PATH', '').split(os.pathsep)
            for path in paths:
                fastboot_path = os.path.join(path, 'fastboot.exe')
                if os.path.exists(fastboot_path):
                    self.logger.debug(f'Fastboot encontrado no PATH: {fastboot_path}')
                    return fastboot_path
        else:
            try:
                found_path = subprocess.check_output(['which', 'fastboot']).decode().strip()
                if found_path:
                    self.logger.debug(f'Fastboot encontrado via which: {found_path}')
                    return found_path
            except:
                pass
        self.logger.error('Fastboot n├úo encontrado em nenhum local')
    def check_fastboot_device(self):
        try:
            devices = self.execute_command('devices')
            return any((not line.startswith('List') for line in devices.split('\n') if not line.strip()))
        except Exception as e:
            self.logger.error(f'Erro ao verificar dispositivo fastboot: {str(e)}')
            return False
    def execute_command(self, command, timeout=30):
        if not self.fastboot_path:
            self.fastboot_path = self.find_fastboot_path()
            if not self.fastboot_path:
                raise Exception('Fastboot n├úo encontrado. Verifique se est├í instalado corretamente.')
        if isinstance(command, str):
            command_parts = command.split()
        else:
            command_parts = command
        cmd_list = [self.fastboot_path] + command_parts
        if ' ' in self.fastboot_path:
            cmd_str_log = f'"{self.fastboot_path}" {' '.join(command_parts)}'
        else:
            cmd_str_log = ' '.join(cmd_list)
        self.logger.debug(f'Executando comando Fastboot: {cmd_str_log}')
        return '\n'.join(valid_lines)
class AndroidTools:
    def __init__(self, adb_manager=None):
        self.adb = adb_manager or ADBManager()
        self.fastboot = FastbootManager()
        self.unlock_url = 'https://en-us.support.motorola.com/app/standalone/bootloader/unlock-your-device-c'
    def check_device_info(self):
        try:
            print('[DEBUG] Verificando dispositivo fastboot')
            if not self.adb.check_fastboot_device():
                return 'ÔØî Dispositivo n├úo est├í em modo fastboot'
        except Exception as e:
            print(f'[DEBUG] Erro geral: {str(e)}')
            return f'ÔØî Erro ao obter informa├º├Áes: {str(e)}'
        try:
            devices = self.adb.execute_fastboot_command('devices')
            print(f'[DEBUG] Dispositivos conectados: {devices}')
            if not devices or not devices.strip():
                return 'ÔØî Nenhum dispositivo detectado em modo fastboot'
            basic_vars = ['product', 'sku', 'carrier_sku', 'variant', 'serialno', 'imei', 'meid', 'cpu', 'emmc', 'ram', 'battid', 'securestate', 'secure', 'unlocked', 'frp-state', 'version-bootloader', 'version-baseband', 'kernel.version[0]', 'kernel.version[1]', 'current-slot', 'slot-count', 'running-slot', 'slot-suffixes', 'slot-successful:_a', 'slot-successful:_b', 'slot-bootable:_a', 'slot-bootable:_b', 'ro.carrier', 'carrier', 'cid', 'channelid', 'max-download-size', 'max-sparse-size', 'current-time', 'pcb-part-no', 'partition-type:boot', 'partition-size:boot', 'partition-type:system', 'partition-size:system', 'partition-type:userdata', 'partition-size:userdata']
            info = []
            device_info = {}
            print('[DEBUG] Tentando obter informa├º├Áes b├ísicas')
            for var in basic_vars:
                pass
            try:
                cmd = f'getvar {var}'
                result = self.adb.execute_fastboot_command(cmd)
                print(f'[DEBUG] {cmd} -> {result}')
                if result:
                    if 'FAILED' not in result:
                        for line in result.split('\n'):
                            if '(bootloader) ' in line:
                                value = line.split('(bootloader) ')[1].strip()
                                if value and value not in ('0', 'failed', 'n/a', 'null', ''):
                                    device_info[var] = value
            except Exception as e:
                print(f'[DEBUG] Erro ao obter {var}: {str(e)}')
        except Exception as e:
            print(f'[DEBUG] Erro ao verificar dispositivo: {str(e)}')
            try:
                return f'ÔØî Erro ao verificar dispositivo: {str(e)}'
            except Exception as e:
                print(f'[DEBUG] Erro geral: {str(e)}')
                return f'ÔØî Erro ao obter informa├º├Áes: {str(e)}'
        if 'imei' not in device_info:
            try:
                imei_result = self.adb.execute_fastboot_command('oem get_imei')
                if imei_result and 'unknown command' not in imei_result.lower():
                    device_info['imei'] = imei_result.split('\n')[0].strip()
            except Exception as e:
                print(f'[DEBUG] Erro ao obter IMEI alternativo: {str(e)}')
        if 'frp-state' not in device_info:
            try:
                frp_result = self.adb.execute_fastboot_command('oem get_frp_state')
                if frp_result and 'unknown command' not in frp_result.lower():
                    device_info['frp-state'] = frp_result.split('\n')[0].strip()
            except Exception as e:
                print(f'[DEBUG] Erro ao obter FRP alternativo: {str(e)}')
        if len(device_info) < 5:
            print('[DEBUG] Poucas informa├º├Áes obtidas, tentando fastboot getvar all')
            try:
                result = self.adb.execute_fastboot_command('getvar all')
                print(f'[DEBUG] getvar all -> {result}')
                if result and 'unknown command' not in result.lower():
                    for line in result.split('\n'):
                        if '(bootloader) ' in line:
                            line = line.split('(bootloader) ')[1].strip()
                            if ': ' in line:
                                key, value = line.split(': ', 1)
                                key = key.strip()
                                value = value.strip()
                                if key in device_info:
                                    continue
                                if not value:
                                    continue
                                if value not in ('0', 'failed', 'n/a', 'null', ''):
                                    device_info[key] = value
                                    print(f'[DEBUG] Adicionado do getvar all: {key} = {value}')
            except Exception as e:
                print(f'[DEBUG] Erro ao executar getvar all: {str(e)}')
        if len(device_info) < 3:
            print('[DEBUG] Tentando comandos espec├¡ficos Motorola')
            moto_commands = ['oem device-info', 'oem get_versions', 'oem get-bootinfo', 'oem get-build-info', 'oem config getprop']
            for cmd in moto_commands:
                try:
                    result = self.adb.execute_fastboot_command(cmd)
                    print(f'[DEBUG] {cmd} -> {result}')
                    if result and 'unknown command' not in result.lower():
                        info.append(f'Ô£à Informa├º├Áes do dispositivo:\n{result}')
                        break
                except Exception as e:
                    print(f'[DEBUG] Erro ao executar {cmd}: {str(e)}')
                    continue
        if device_info:
            info = []
            info.append('­ƒô▒ === INFORMA├ç├òES DO DISPOSITIVO ===')
            device_keys = ['sku', 'carrier_sku', 'product', 'serialno', 'imei', 'meid']
            for key in device_keys:
                if key not in device_info:
                    continue
                try:
                    if key == 'sku':
                        info.append(f'Ô£à Modelo: {device_info[key]}')
                    else:
                        info.append(f'Ô£à {key.upper()}: {device_info[key]}')
                    if not any((k in device_info for k in ('cpu', 'emmc', 'ram', 'battid'))):
                        break
                    info.append('\n­ƒöº === HARDWARE ===')
                    hw_keys = ['cpu', 'emmc', 'ram', 'battid']
                    for key in hw_keys:
                        if key in device_info:
                            info.append(f'Ô£à {key.upper()}: {device_info[key]}')
                    if not any((k in device_info for k in ('securestate', 'frp-state', 'unlocked'))):
                        break
                    info.append('\n­ƒöÆ === SEGURAN├çA ===')
                    sec_keys = ['securestate', 'frp-state', 'unlocked']
                    for key in sec_keys:
                        if key in device_info:
                            info.append(f'Ô£à {key.replace('-', ' ').title()}: {device_info[key]}')
                    if not any((k in device_info for k in ('current-slot', 'slot-count', 'running-slot'))):
                        break
                    info.append('\n­ƒöä === SLOTS A/B ===')
                    slot_keys = ['current-slot', 'slot-count', 'running-slot', 'slot-suffixes']
                    for key in slot_keys:
                        if key in device_info:
                            info.append(f'Ô£à {key.replace('-', ' ').title()}: {device_info[key]}')
                    slot_status_keys = ['slot-successful:_a', 'slot-successful:_b', 'slot-bootable:_a', 'slot-bootable:_b']
                    for key in slot_status_keys:
                        if key in device_info:
                            info.append(f'Ô£à {key.replace(':', ' ').replace('-', ' ').title()}: {device_info[key]}')
                    if not any((k in device_info for k in ('ro.carrier', 'carrier', 'cid', 'channelid'))):
                        break
                    info.append('\n­ƒôí === OPERADORA/REGI├âO ===')
                    carrier_keys = ['ro.carrier', 'carrier', 'cid', 'channelid']
                    for key in carrier_keys:
                        if key in device_info:
                            info.append(f'Ô£à {key.replace('.', ' ').replace('-', ' ').title()}: {device_info[key]}')
                    if not any((k in device_info for k in ('version-bootloader', 'version-baseband', 'kernel.version[0]'))):
                        break
                    info.append('\n­ƒôï === VERS├òES ===')
                    version_keys = ['version-bootloader', 'version-baseband', 'kernel.version[0]', 'kernel.version[1]']
                    for key in version_keys:
                        if key not in device_info:
                            continue
                        if 'kernel' in key:
                            info.append(f'Ô£à Kernel: {device_info[key]}')
                        else:
                            info.append(f'Ô£à {key.replace('-', ' ').title()}: {device_info[key]}')
                except Exception as e:
                    print(f'[DEBUG] Erro ao verificar dispositivo: {str(e)}')
                    try:
                        return f'ÔØî Erro ao verificar dispositivo: {str(e)}'
                    except Exception as e:
                        print(f'[DEBUG] Erro geral: {str(e)}')
                        return f'ÔØî Erro ao obter informa├º├Áes: {str(e)}'
        if not info:
            return 'ÔØî N├úo foi poss├¡vel obter informa├º├Áes do dispositivo. Verifique se ├® um dispositivo Motorola.'
        return '\n'.join(info)
    def fix_comm_server(self):
        try:
            print('[DEBUG] Verificando dispositivo fastboot')
            if not self.adb.check_fastboot_device():
                return 'ÔØî Dispositivo n├úo est├í em modo fastboot'
            command_variants = [['oem fb_mode_set', '-w', 'oem fb_mode_clear', 'reboot'], ['fb_mode_set', '-w', 'fb_mode_clear', 'reboot'], ['oem fb-mode-set', '-w', 'oem fb-mode-clear', 'reboot'], ['oem fbmodeset', '-w', 'oem fbmodeclear', 'reboot']]
            for commands in command_variants:
                print(f'[DEBUG] Tentando conjunto de comandos: {commands}')
                success = True
                for cmd in commands:
                    pass
            try:
                print(f'[DEBUG] Executando comando: {cmd}')
                result = self.adb.execute_fastboot_command(cmd)
                print(f'[DEBUG] Resultado: {result}')
                if 'unknown command' in result.lower():
                    success = False
            except Exception as e:
                print(f'[DEBUG] Erro ao executar {cmd}: {str(e)}')
                if 'unknown command' in str(e).lower():
                    success = False
        except Exception as e:
            print(f'[DEBUG] Erro geral: {str(e)}')
            return f'ÔØî Erro ao aplicar corre├º├úo: {str(e)}'
        try:
            return 'ÔØî Nenhum conjunto de comandos funcionou. Verifique se o dispositivo suporta esta opera├º├úo.'
        except Exception as e:
            print(f'[DEBUG] Erro geral: {str(e)}')
            return f'ÔØî Erro ao aplicar corre├º├úo: {str(e)}'
    def get_unlock_data(self):
        try:
            print('[DEBUG] Verificando dispositivo fastboot')
            if not self.adb.check_fastboot_device():
                return 'ÔØî Dispositivo n├úo est├í em modo fastboot'
            print('[DEBUG] Obtendo dados de desbloqueio')
            unlock_commands = ['oem get_unlock_data', 'oem get-unlock-data', 'oem unlock-data', 'oem unlock data', 'oem unlock_data', 'oem unlockdata', 'flashing get_unlock_data', 'flashing unlock_data']
            unlock_data = []
            success = False
            for cmd in unlock_commands:
                pass
            try:
                print(f'[DEBUG] Tentando comando: {cmd}')
                result = self.adb.execute_fastboot_command(cmd)
                print(f'[DEBUG] Resultado: {result}')
                if result:
                    if 'unknown command' not in result.lower():
                        current_data = []
                        for line in result.split('\n'):
                            if '(bootloader) ' in line:
                                line = line.split('(bootloader) ')[1]
                            elif 'INFO' in line:
                                line = line[line.find('INFO'):]
                            line = line.strip()
                            if not line or line.lower() in ('0', 'failed', 'n/a', 'null'):
                                continue
                            if any((x in line.upper() for x in ('INFO', '0A4', '303', '8A6', '1A3'))):
                                current_data.append(line)
                        if current_data:
                            unlock_data = current_data
                            success = True
            except Exception as e:
                print(f'[DEBUG] Erro ao tentar {cmd}: {str(e)}')
            else:
                if success and unlock_data:
                    formatted_data = []
                    for line in unlock_data:
                        if not line.startswith('INFO'):
                            line = f'INFO{line}'
                        formatted_data.append(line)
                    return 'Ô£à Dados de desbloqueio:\n' + '\n'.join(formatted_data)
                print('[DEBUG] Nenhum comando funcionou')
        except Exception as e:
            print(f'[DEBUG] Erro geral: {str(e)}')
            return f'ÔØî Erro ao obter dados de desbloqueio: {str(e)}'
        return 'ÔØî N├úo foi poss├¡vel obter os dados de desbloqueio. Verifique se:\n1. O dispositivo est├í em modo fastboot\n2. O bootloader permite desbloqueio\n3. Os drivers Motorola est├úo instalados\n4. O dispositivo est├í conectado corretamente\n5. Consulte https://motorola-global-portal.custhelp.com/app/standalone/bootloader/unlock-your-device-a para mais informa├º├Áes'
    def unlock_bootloader(self, unlock_code):
        try:
            print('[DEBUG] Verificando dispositivo fastboot')
            if not self.adb.check_fastboot_device():
                return 'ÔØî Dispositivo n├úo est├í em modo fastboot'
            if not unlock_code:
                return 'ÔØî C├│digo de desbloqueio n├úo fornecido'
            print('[DEBUG] Executando comando de desbloqueio')
        except Exception as e:
            print(f'[DEBUG] Erro geral: {str(e)}')
            return f'ÔØî Erro ao desbloquear bootloader: {str(e)}'
        try:
            result = self.adb.execute_fastboot_command(f'oem unlock {unlock_code}')
            print(f'[DEBUG] Resultado bruto: {result}')
            if not result or result.strip() == '':
                print('[DEBUG] Nenhuma resposta do comando de desbloqueio')
                return 'ÔØî Erro ao desbloquear bootloader'
            if any((x in result.lower() for x in ('success', 'unlocked', 'okay', 'done'))):
                return 'Ô£à Bootloader desbloqueado com sucesso!'
        except Exception as e:
            print(f'[DEBUG] Erro ao desbloquear: {str(e)}')
            try:
                return f'ÔØî Erro ao desbloquear bootloader: {str(e)}'
            except Exception as e:
                print(f'[DEBUG] Erro geral: {str(e)}')
                return f'ÔØî Erro ao desbloquear bootloader: {str(e)}'
        return 'ÔØî Falha ao desbloquear bootloader. Verifique o c├│digo fornecido.'
    def _detect_xml_type(self, xml_file):
        try:
            filename = os.path.basename(xml_file).lower()
            if 'servicefile' in filename:
                return ('service', False)
            if 'flashfile' in filename:
                return ('flash', True)
            tree = ET.parse(xml_file)
            root = tree.getroot()
            if root.findall('.//filename') or root.findall('.//erase'):
                return ('flash', True)
            if root.findall('.//step'):
                return ('droid', True)
        except Exception as e:
            print(f'[DEBUG] Erro ao detectar tipo de XML: {str(e)}')
        return ('unknown', True)
    def flash_stock_rom(self, xml_file, force_type=None):
        try:
            print('[DEBUG] ===== INICIANDO FLASH MOTOROLA UNIVERSAL =====')
            if not self.adb.check_fastboot_device():
                return 'ÔØî Dispositivo n├úo est├í em modo fastboot'
            if not xml_file or not os.path.exists(xml_file):
                return 'ÔØî Arquivo XML n├úo encontrado'
            if not xml_file.lower().endswith(('.xml', '.XML')):
                return 'ÔØî Arquivo deve ser um XML v├ílido'
            firmware_folder = self._detect_firmware_folder(xml_file)
            if not firmware_folder:
                return 'ÔØî Pasta de firmware n├úo encontrada'
            print(f'[DEBUG] Pasta de firmware: {firmware_folder}')
            device_type = self._detect_device_type()
            print(f'[DEBUG] Tipo de dispositivo: {device_type}')
            xml_type, will_erase = self._detect_xml_type(xml_file) if not force_type else (force_type, force_type == 'flash')
            print(f'[DEBUG] Tipo de XML: {xml_type} (Apagar├í dados: {'Sim' if will_erase else 'N├úo'})')
            if will_erase:
                print('[AVISO] Este processo apagar├í todos os dados do dispositivo!')
            commands = self._process_xml_to_commands(xml_file, firmware_folder, device_type, xml_type)
            if not commands:
                return 'ÔØî Nenhum comando v├ílido encontrado no XML'
            print(f'[DEBUG] {len(commands)} comandos gerados')
            success_count = 0
            error_count = 0
            for i, cmd in enumerate(commands):
                pass
            try:
                print(f'[DEBUG] [{i + 1}/{len(commands)}] Executando: {cmd}')
                result = self.adb.execute_fastboot_command(cmd, timeout=60)
                print(f'[DEBUG] Ô£à Sucesso: {result}')
                success_count += 1
            except Exception as e:
                error_msg = str(e)
                print(f'[DEBUG] ÔØî Erro: {error_msg}')
                error_count += 1
                if self._is_critical_error(cmd, error_msg):
                    pass
        except Exception as e:
            print(f'[DEBUG] Erro geral: {str(e)}')
            return f'ÔØî Erro ao fazer flash: {str(e)}'
        try:
            try:
                print('[DEBUG] Finalizando processo...')
                self.adb.execute_fastboot_command('oem fb_mode_clear', timeout=10)
                self.adb.execute_fastboot_command('reboot', timeout=10)
            except:
                pass
        except Exception as e:
            print(f'[DEBUG] Erro geral: {str(e)}')
            return f'ÔØî Erro ao fazer flash: {str(e)}'
        if error_count == 0:
            return f'Ô£à Flash conclu├¡do com sucesso! Todos os {success_count} comandos executados.{' (Dados preservados)' if not will_erase else ''}\nO dispositivo est├í reiniciando.'
        try:
            if success_count > error_count:
                return f'ÔÜá´©Å Flash parcialmente conclu├¡do: {success_count} sucessos, {error_count} erros. Dispositivo pode estar funcional.'
        except Exception as e:
            print(f'[DEBUG] Erro geral: {str(e)}')
            return f'ÔØî Erro ao fazer flash: {str(e)}'
        return f'ÔØî Flash falhado: {error_count} erros vs {success_count} sucessos.'
    def _detect_firmware_folder(self, xml_file):
        try:
            xml_dir = os.path.dirname(os.path.abspath(xml_file))
            xml_name = os.path.basename(xml_file)
            xml_name_no_ext = os.path.splitext(xml_name)[0]
            print(f'[DEBUG] Detectando pasta de firmware para: {xml_name}')
        except Exception as e:
            print(f'[DEBUG] Erro ao detectar pasta de firmware: {str(e)}')
        try:
            firmware_files = [f for f in os.listdir(xml_dir) if f.endswith(('.img', '.bin', '.mbn'))]
            if len(firmware_files) > 3:
                print(f'[DEBUG] {len(firmware_files)} arquivos de firmware encontrados na pasta do XML')
                return xml_dir
            potential_subdir = os.path.join(xml_dir, xml_name_no_ext)
            if os.path.exists(potential_subdir):
                firmware_files = [f for f in os.listdir(potential_subdir) if f.endswith(('.img', '.bin', '.mbn'))]
                if len(firmware_files) > 3:
                    print(f'[DEBUG] {len(firmware_files)} arquivos de firmware encontrados na subpasta: {xml_name_no_ext}')
                    return potential_subdir
        except Exception as e:
            print(f'[DEBUG] Erro ao detectar pasta de firmware: {str(e)}')
        parent_dir = os.path.dirname(xml_dir)
        if parent_dir != xml_dir:
            pass
        for item in os.listdir(xml_dir):
            item_path = os.path.join(xml_dir, item)
            if os.path.isdir(item_path):
                try:
                    firmware_files = [f for f in os.listdir(parent_dir) if f.endswith(('.img', '.bin', '.mbn'))]
                    if len(firmware_files) > 3:
                        print(f'[DEBUG] {len(firmware_files)} arquivos de firmware encontrados na pasta pai')
                        return parent_dir
                except Exception as e:
                    print(f'[DEBUG] Erro ao detectar pasta de firmware: {str(e)}')
                    try:
                        try:
                            pass
                        except:
                            pass
                    except Exception as e:
                        print(f'[DEBUG] Erro ao detectar pasta de firmware: {str(e)}')
                try:
                    try:
                        firmware_files = [f for f in os.listdir(item_path) if f.endswith(('.img', '.bin', '.mbn'))]
                        if len(firmware_files) > 3:
                            print(f'[DEBUG] {len(firmware_files)} arquivos de firmware encontrados em subpasta: {item}')
                            return item_path
                    except:
                        pass
                except Exception as e:
                    print(f'[DEBUG] Erro ao detectar pasta de firmware: {str(e)}')
        print('[DEBUG] ÔØî Nenhuma pasta de firmware encontrada')
    def _detect_device_type(self):
        try:
            slot_info = self.adb.execute_fastboot_command('getvar current-slot', timeout=5)
            if slot_info:
                if 'a' in slot_info.lower() or 'b' in slot_info.lower():
                    print('[DEBUG] Dispositivo A/B detectado')
                    return 'ab'
        except:
            pass
        try:
            try:
                slot_count = self.adb.execute_fastboot_command('getvar slot-count', timeout=5)
                if slot_count and '2' in slot_count:
                    print('[DEBUG] Dispositivo A/B detectado via slot-count')
                    return 'ab'
            except:
                pass
        except Exception as e:
            print(f'[DEBUG] Erro ao detectar tipo de dispositivo: {str(e)}')
            return 'traditional'
        try:
            print('[DEBUG] Dispositivo tradicional detectado')
        except Exception as e:
            print(f'[DEBUG] Erro ao detectar tipo de dispositivo: {str(e)}')
        return 'traditional'
    def _process_xml_to_commands(self, xml_file, firmware_folder, device_type, xml_type):
        try:
            commands = []
            tree = ET.parse(xml_file)
            root = tree.getroot()
            commands.append('getvar max-sparse-size')
            commands.append('oem fb_mode_set')
            if root.findall('.//step'):
                print('[DEBUG] Processando XML no formato <step>')
                for step in root.findall('.//step'):
                    operation = step.get('operation', '')
                    partition = step.get('partition', '')
                    filename = step.get('filename', '')
                    var = step.get('var', '')
                    if operation == 'flash' and partition and filename:
                        file_path = os.path.join(firmware_folder, filename)
                        if os.path.exists(file_path):
                            if device_type == 'ab' and self._needs_slot_suffix(partition):
                                current_slot = self._get_current_slot()
                                target_slot = 'b' if current_slot == 'a' else 'a'
                                cmd = f'flash --slot={target_slot} {partition} "{file_path}"'
                            else:
                                cmd = f'flash {partition} "{file_path}"'
                            commands.append(cmd)
                            continue
                        print(f'[DEBUG] ÔÜá´©Å Arquivo n├úo encontrado: {filename}')
                        continue
                    if operation == 'erase' and partition:
                        commands.append(f'erase {partition}')
                        continue
                    if operation == 'getvar' and var:
                        commands.append(f'getvar {var}')
                        continue
                    if operation != 'oem':
                        continue
                    if not var:
                        continue
                    commands.append(f'oem {var}')
                    continue
                return commands
            print('[DEBUG] Processando XML no formato antigo')
            for node in root.findall('.//filename'):
                partition = node.get('partition', '')
                filename = node.get('filename', '')
                if not partition:
                    continue
                if filename:
                    file_path = os.path.join(firmware_folder, filename)
                    if os.path.exists(file_path):
                        commands.append(f'flash {partition} "{file_path}"')
            if xml_type == 'flash':
                for node in root.findall('.//erase'):
                    partition = node.get('partition', '')
                    if partition:
                        commands.append(f'erase {partition}')
            commands.append('oem fb_mode_clear')
            commands.append('reboot')
            return commands
        except Exception as e:
            print(f'[DEBUG] Erro ao processar XML: {str(e)}')
            return []
    def _needs_slot_suffix(self, partition):
        ab_partitions = ['boot', 'system', 'vendor', 'dtbo', 'vbmeta', 'modem', 'bluetooth']
        return partition.lower() in ab_partitions
    def _get_current_slot(self):
        try:
            result = self.adb.execute_fastboot_command('getvar current-slot', timeout=5)
            if 'a' in result.lower():
                return 'a'
            if 'b' in result.lower():
                return 'b'
        except:
            pass
        return 'a'
    def _is_critical_error(self, command, error_msg):
        error_lower = error_msg.lower()
        critical_errors = ['no devices', 'device not found', 'write to device failed', 'remote: not allowed', 'remote: oem unlock is required', 'remote: device is locked']
        for critical in critical_errors:
            if critical in error_lower:
                return True
        if 'flash' in command.lower():
            critical_partitions = ['bootloader', 'boot', 'recovery']
            for partition in critical_partitions:
                if partition in command.lower():
                    return True
        return False
    def fix_mdm(self):
        try:
            if not self.adb.check_device():
                return 'ÔØî Dispositivo n├úo est├í em modo ADB'
            packages = ['com.motorola.mdmservice', 'com.motorola.android.settings.moto_secure', 'com.motorola.android.provisioning', 'com.motorola.paks', 'com.motorola.ccc.devicemanagement', 'com.motorola.android.provider.settings']
            results = []
            for package in packages:
                pass
            try:
                self.adb._run_adb_command([self.adb.adb_path, 'shell', 'pm', 'uninstall', '-k', '--user', '0', package])
                results.append(f'Ô£à Removido: {package}')
            except:
                results.append(f'ÔÜá´©Å Falha ao remover: {package}')
        except Exception as e:
            return f'ÔØî Erro ao remover MDM: {str(e)}'
        try:
            try:
                self.adb.finalize_adb_operation()
            except:
                pass
        except Exception as e:
            return f'ÔØî Erro ao remover MDM: {str(e)}'
        return '\n'.join(results)
    def check_bootloader_status(self):
        try:
            print('[DEBUG] Verificando status do bootloader')
            if not self.adb.check_fastboot_device():
                return 'ÔØî Dispositivo n├úo est├í em modo fastboot'
        except Exception as e:
            print(f'[DEBUG] Erro geral: {str(e)}')
            return 'ÔØî Erro ao verificar bootloader'
        try:
            result = self.adb.execute_fastboot_command('oem get-bootinfo')
            print(f'[DEBUG] Resultado bruto: {result}')
            if not result or result.strip() == '':
                print('[DEBUG] Nenhuma resposta do comando get-bootinfo')
                return 'ÔØî Erro ao verificar bootloader'
            for line in result.split('\n'):
                if '(bootloader) ' in line:
                    info = line.split('(bootloader) ')[1].strip()
                elif ': ' in line:
                    info = line.split(': ')[1].strip()
                else:
                    info = line.strip()
                if info and 'unlocked' in info.lower():
                    return 'Ô£à Bootloader Desbloqueado'
                if not info:
                    continue
                if 'locked' in info.lower():
                    return '­ƒöÆ Bootloader Bloqueado'
        except Exception as e:
            print(f'[DEBUG] Erro ao verificar bootloader: {str(e)}')
            try:
                return 'ÔØî Erro ao verificar bootloader'
            except Exception as e:
                print(f'[DEBUG] Erro geral: {str(e)}')
                return 'ÔØî Erro ao verificar bootloader'
        try:
            return 'ÔÜá´©Å Status do bootloader n├úo identificado'
        except Exception as e:
            print(f'[DEBUG] Erro ao verificar bootloader: {str(e)}')
            try:
                return 'ÔØî Erro ao verificar bootloader'
            except Exception as e:
                print(f'[DEBUG] Erro geral: {str(e)}')
                return 'ÔØî Erro ao verificar bootloader'
    def check_dm_verity(self):
        try:
            result = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'getprop ro.boot.veritymode']).strip()
            try:
                self.adb.finalize_adb_operation()
            except:
                pass
            else:
                if result == 'enforcing':
                    return '­ƒöÆ DM-Verity Ativo'
                if result == 'disabled':
                    pass
        except:
            return 'ÔØî Erro ao verificar DM-Verity'
        return 'ÔÜá´©Å Status Desconhecido'
    def disable_dm_verity(self):
        try:
            print('[DEBUG] Verificando dispositivo fastboot')
            if not self.adb.check_fastboot_device():
                return 'ÔØî Dispositivo n├úo est├í em modo fastboot'
            commands = ['--disable-verity', '--disable-verification', 'reboot']
            print('[DEBUG] Aplicando comandos DM-Verity')
            for cmd in commands:
                pass
            try:
                print(f'[DEBUG] Executando comando: {cmd}')
                self.adb.execute_fastboot_command(cmd)
                print(f'[DEBUG] Comando {cmd} executado com sucesso')
            except Exception as e:
                print(f'[DEBUG] Erro ao executar {cmd}: {str(e)}')
                try:
                    return f'ÔØî Erro ao desativar DM-Verity: falha no comando {cmd}'
                except Exception as e:
                    print(f'[DEBUG] Erro geral: {str(e)}')
                    return f'ÔØî Erro ao desativar DM-Verity: {str(e)}'
        except Exception as e:
            print(f'[DEBUG] Erro geral: {str(e)}')
            return f'ÔØî Erro ao desativar DM-Verity: {str(e)}'
        return 'Ô£à DM-Verity desativado com sucesso'
    def check_xiaomi_account(self):
        try:
            result = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'settings get secure user_name']).strip()
            try:
                self.adb.finalize_adb_operation()
            except:
                pass
            else:
                if result and result != 'null':
                    pass
        except:
            return 'ÔØî Erro ao verificar conta'
        return 'Ô£à Sem conta Mi'
