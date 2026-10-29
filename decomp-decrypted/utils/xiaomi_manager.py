from app.utils.adb_manager import ADBManager
import time
from datetime import datetime
import logging
import os
import platform
import subprocess
logger = logging.getLogger(__name__)
class XiaomiManager:
    def __init__(self, adb_manager=None):
        self.adb = adb_manager or ADBManager()
        self.logger = logging.getLogger(__name__)
        self.logger.debug(f'XiaomiManager inicializado (ADB: {'OK' if self.adb.adb_path else 'N/A'})')
        self.cache = {}
        self.cache_time = {}
        self.cache_ttl = 60
    def _get_cached_or_run(self, cache_key, function, *args, **kwargs):
        current_time = time.time()
        if cache_key in self.cache and current_time - self.cache_time.get(cache_key, 0) < self.cache_ttl:
            return self.cache[cache_key]
        try:
            result = function(*args, **kwargs)
            self.cache[cache_key] = result
            self.cache_time[cache_key] = current_time
            return result
        except Exception as e:
            self.logger.error(f'Erro ao executar {function.__name__}: {str(e)}')
            if cache_key in self.cache:
                self.logger.info(f'Retornando valor em cache para {cache_key}')
                return self.cache[cache_key]
            raise
    def clear_cache(self):
        self.cache.clear()
        self.cache_time.clear()
    def get_device_info(self):
        try:
            return self._get_cached_or_run('device_info', self._fetch_device_info)
        except Exception as e:
            self.logger.error(f'Erro ao obter informa├º├Áes do dispositivo: {str(e)}')
            return {'error': str(e)}
    def _fetch_device_info(self):
        self.logger.info('Coletando informa├º├Áes do dispositivo Xiaomi...')
        info = {}
        try:
            bat_info = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'dumpsys battery'])
            for line in bat_info.split('\n'):
                if 'level:' in line:
                    info['battery'] = line.split('level:')[1].strip()
                elif 'status:' in line:
                    status = line.split('status:')[1].strip()
                    if status == '2':
                        info['charging'] = 'Carregando'
                    elif status == '5':
                        info['charging'] = 'Completo'
                    else:
                        info['charging'] = 'Descarregando'
        except Exception as e:
            self.logger.warning(f'Erro ao obter informa├º├Áes da bateria: {str(e)}')
        try:
            info['miui_version'] = self.get_miui_version()
        except Exception as e:
            self.logger.warning(f'Erro ao obter vers├úo MIUI: {str(e)}')
            info['miui_version'] = 'Vers├úo Desconhecida'
        try:
            try:
                if self.is_bootloader_unlocked():
                    info['security'] = 'Bootloader Desbloqueado'
                else:
                    info['security'] = 'Bootloader Bloqueado'
            except Exception as e:
                self.logger.warning(f'Erro ao verificar status do bootloader: {str(e)}')
                info['security'] = 'Status Desconhecido'
        except Exception as e:
            self.logger.error(f'Erro ao coletar informa├º├Áes: {str(e)}')
            raise
        self.logger.info(f'Informa├º├Áes coletadas: {info}')
        return info
    def is_xiaomi_device(self):
        try:
            return self._get_cached_or_run('is_xiaomi', self._check_xiaomi_device)
        except Exception as e:
            self.logger.warning(f'Erro ao verificar dispositivo Xiaomi: {str(e)}')
            return False
    def _check_xiaomi_device(self):
        self.logger.info('Verificando se ├® dispositivo Xiaomi...')
        properties = ['ro.product.brand', 'ro.product.manufacturer', 'ro.product.vendor.brand']
        for prop in properties:
            try:
                if not self.adb.check_device():
                    self.logger.warning('Nenhum dispositivo conectado')
                    return False
            except Exception as e:
                self.logger.debug(f'Erro ao verificar propriedade {prop}: {str(e)}')
                continue
            try:
                value = self.adb._run_adb_command([self.adb.adb_path, 'shell', f'getprop {prop}']).strip().lower()
                self.logger.debug(f'Propriedade {prop}: {value}')
                if value in ('xiaomi', 'redmi', 'poco'):
                    self.logger.info(f'Dispositivo Xiaomi identificado via {prop}')
                    return True
            except Exception as e:
                self.logger.debug(f'Erro ao verificar propriedade {prop}: {str(e)}')
                continue
        self.logger.warning('Dispositivo n├úo ├® Xiaomi')
        return False
    def get_miui_version(self):
        try:
            cache_key = 'miui_version'
            if cache_key in self.cache and time.time() - self.cache_time.get(cache_key, 0) < self.cache_ttl:
                return self.cache[cache_key]
            result = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'getprop ro.miui.ui.version.name']).strip()
            if not result or result == '':
                result = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'getprop ro.build.version.incremental']).strip()
                hyperos_check = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'getprop ro.mi.os.version.name']).strip()
                if hyperos_check and 'HyperOS' in hyperos_check:
                    result = hyperos_check
            self.cache[cache_key] = result
            self.cache_time[cache_key] = time.time()
            return result
        except Exception as e:
            self.logger.error(f'Erro ao obter vers├úo MIUI: {str(e)}')
            return 'Vers├úo Desconhecida'
    def get_battery_level(self):
        try:
            if not self.adb.adb_path:
                return '--'
            result = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'dumpsys battery'])
            for line in result.split('\n'):
                if 'level:' in line:
                    level = line.split(':', 1)[1].strip()
                    return level
            return '--'
        except Exception as e:
            self.logger.error(f'Erro ao obter n├¡vel de bateria: {str(e)}')
            return '--'
    def check_bootloader_status(self):
        try:
            if not self.adb.adb_path:
                return 'ÔÜá´©Å ADB n├úo encontrado, n├úo foi poss├¡vel verificar status do bootloader'
            result = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'getprop ro.bootloader.unlock']).strip()
            if result == '1':
                return 'Ô£à Bootloader j├í est├í desbloqueado'
        except Exception as e:
            self.logger.error(f'Erro ao verificar status do bootloader: {str(e)}')
            return 'ÔÜá´©Å N├úo foi poss├¡vel verificar status do bootloader'
        return '­ƒöÆ Bootloader est├í bloqueado'
    def is_bootloader_unlocked(self):
        try:
            if not self.adb.adb_path:
                return False
            status = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'getprop ro.bootloader.unlock']).strip()
            return status == '1'
        except Exception as e:
            self.logger.error(f'Erro ao verificar status do bootloader: {str(e)}')
            return False
    def prepare_for_unlock(self):
        try:
            if not self.adb.adb_path:
                return 'ÔØî ADB n├úo encontrado, imposs├¡vel preparar para desbloqueio'
            if not self.is_xiaomi_device():
                return 'ÔÜá´©Å Dispositivo n├úo ├® Xiaomi. Opera├º├úo de unlock n├úo suportada.'
            dev_commands = ['settings put global development_settings_enabled 1', 'settings put global adb_enabled 1', 'settings put global usb_debugging_enabled 1']
            mi_commands = ['setprop persist.sys.usb.config diag,adb', 'setprop sys.usb.config diag,adb', 'setprop persist.sys.usb.diag 1']
            all_commands = dev_commands + mi_commands
            for cmd in all_commands:
                self.adb._run_adb_command([self.adb.adb_path, 'shell', cmd])
            account_result = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'getprop ro.miui.has_cust_partition']).strip()
            message = 'Ô£à Dispositivo preparado para desbloqueio do bootloader. '
            if account_result != '1':
                message += 'ÔÜá´©Å Adicione sua conta Mi nas configura├º├Áes e aguarde 7 dias.'
            print('Dispositivo preparado para unlock')
            return message
        except Exception as e:
            print(f'Erro ao preparar para unlock: {e}')
            self.logger.error(f'Erro ao preparar dispositivo para unlock: {str(e)}')
            return f'ÔØî Erro ao preparar dispositivo para desbloqueio: {str(e)}'
    def get_unlock_token(self):
        try:
            if not self.adb.adb_path:
                return 'ÔØî ADB n├úo encontrado, imposs├¡vel obter token de unlock'
            result = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'cat /data/miui/unlock_token'])
            print('Token de unlock obtido com sucesso')
            return f'Ô£à Token obtido: {result[:20]}...'
        except Exception as e:
            print(f'Erro ao obter token: {e}')
            self.logger.error(f'Erro ao obter token de unlock: {str(e)}')
            return 'ÔØî Erro ao obter token de unlock'
    def apply_advanced_tweaks(self):
        try:
            if not self.adb.adb_path:
                return 'ÔØî ADB n├úo encontrado, imposs├¡vel aplicar tweaks avan├ºados'
            touch_commands = ['settings put global debug.choreographer.skipwarning 1', 'settings put global debug.egl.hw 1', 'settings put global debug.sf.latch_unsignaled 1', 'settings put global persist.service.lgospd.enable 0']
            network_commands = ['settings put global cast_sender_enabled 0', 'settings put global tether_dun_required 0', 'settings put global tether_offload_disabled 0', 'settings put global wifi_scan_throttle_enabled 0', 'settings put global netstats_enabled 0']
            general_commands = ['settings put global development_settings_enabled 1', 'settings put global require_password_to_decrypt 0', 'settings put global device_provisioned 1']
            all_commands = touch_commands + network_commands + general_commands
            for cmd in all_commands:
                self.adb._run_adb_command([self.adb.adb_path, 'shell', cmd])
            print('Tweaks avan├ºados aplicados')
            return 'Ô£à Tweaks avan├ºados aplicados com sucesso'
        except Exception as e:
            print(f'Erro ao aplicar tweaks avan├ºados: {e}')
            self.logger.error(f'Erro ao aplicar tweaks avan├ºados: {str(e)}')
            return f'ÔØî Erro ao aplicar tweaks avan├ºados: {str(e)}'
    def flash_custom_recovery(self, recovery_img):
        try:
            if not self.adb.adb_path or not self.adb.fastboot_path:
                return 'ÔØî ADB ou Fastboot n├úo encontrados, imposs├¡vel flashear recovery'
            if not self.adb.check_fastboot_device():
                self.adb._run_adb_command([self.adb.adb_path, 'reboot', 'bootloader'])
                time.sleep(5)
            if not os.path.exists(recovery_img):
                return f'ÔØî Arquivo de recovery n├úo encontrado: {recovery_img}'
            result = self.adb._run_fastboot_command([self.adb.fastboot_path, 'flash', 'recovery', recovery_img])
            print(f'Recovery flasheada: {recovery_img}')
            return 'Ô£à Recovery customizada instalada com sucesso'
        except Exception as e:
            print(f'Erro ao flashear recovery: {e}')
            self.logger.error(f'Erro ao flashear recovery: {str(e)}')
            return f'ÔØî Erro ao flashear recovery: {str(e)}'
    def manage_system_apps(self, action, package_name):
        try:
            if not self.adb.adb_path:
                return f'ÔØî ADB n├úo encontrado, imposs├¡vel {action} {package_name}'
            cmd = 'disable' if action == 'disable' else 'enable'
            self.adb._run_adb_command([self.adb.adb_path, 'shell', f'pm {cmd} {package_name}'])
            print(f'App {package_name} {action}d')
            return f'Ô£à {package_name} {action}d com sucesso'
        except Exception as e:
            print(f'Erro ao {action} {package_name}: {e}')
            self.logger.error(f'Erro ao {action} app {package_name}: {str(e)}')
            return f'ÔØî Erro ao {action} {package_name}'
    def clear_app_data(self, package_name):
        try:
            if not self.adb.adb_path:
                return f'ÔØî ADB n├úo encontrado, imposs├¡vel limpar dados de {package_name}'
            self.adb._run_adb_command([self.adb.adb_path, 'shell', f'pm clear {package_name}'])
            print(f'Dados do app {package_name} limpos')
            return f'Ô£à Dados de {package_name} limpos com sucesso'
        except Exception as e:
            print(f'Erro ao limpar dados: {e}')
            self.logger.error(f'Erro ao limpar dados do app {package_name}: {str(e)}')
            return 'ÔØî Erro ao limpar dados do app'
    def disable_miui_ads(self):
        try:
            if not self.adb.adb_path:
                return 'ÔØî ADB n├úo encontrado, imposs├¡vel desativar an├║ncios'
            commands = ['settings put global msa_enable 0', 'settings put global personalized_ad_enabled 0', 'settings put global analytics_enabled 0', 'settings put global ad_enable_gdpr 0', 'pm disable com.miui.systemAdSolution', 'pm disable com.miui.analytics', 'pm disable com.xiaomi.mipicks']
            for cmd in commands:
                self.adb._run_adb_command([self.adb.adb_path, 'shell', cmd])
            print('An├║ncios MIUI desativados')
            return 'Ô£à An├║ncios MIUI/HyperOS desativados com sucesso'
        except Exception as e:
            print(f'Erro ao desativar an├║ncios: {e}')
            self.logger.error(f'Erro ao desativar an├║ncios MIUI: {str(e)}')
            return f'ÔØî Erro ao desativar an├║ncios: {str(e)}'
    def enable_third_party_themes(self):
        try:
            if not self.adb.adb_path:
                return 'ÔØî ADB n├úo encontrado, imposs├¡vel ativar temas de terceiros'
            commands = ['settings put system force_fsg_nav_bar 1', 'settings put global policy_control immersive.full=*', 'settings put secure theme_customization \'{ "android.theme.customization.theme_style": "-1" }\'', 'settings put secure force_allow_theme_apk 1']
            for cmd in commands:
                self.adb._run_adb_command([self.adb.adb_path, 'shell', cmd])
            print('Temas de terceiros ativados')
            return 'Ô£à Temas de terceiros ativados com sucesso'
        except Exception as e:
            print(f'Erro ao ativar temas de terceiros: {e}')
            self.logger.error(f'Erro ao ativar temas de terceiros: {str(e)}')
            return f'ÔØî Erro ao ativar temas de terceiros: {str(e)}'
    def disable_miui_optimization(self):
        try:
            if not self.adb.adb_path:
                return 'ÔØî ADB n├úo encontrado, imposs├¡vel desativar otimiza├º├Áes MIUI'
            commands = ['settings put global miui_optimization 0', 'settings put global miui.performance_mode 1', 'settings put global persist.sys.miui_optimization 0', 'setprop persist.miui.dexopt.first_use false']
            for cmd in commands:
                self.adb._run_adb_command([self.adb.adb_path, 'shell', cmd])
            print('Otimiza├º├Áes MIUI desativadas')
            return 'Ô£à Otimiza├º├Áes MIUI desativadas com sucesso'
        except Exception as e:
            print(f'Erro ao desativar otimiza├º├Áes MIUI: {e}')
            self.logger.error(f'Erro ao desativar otimiza├º├Áes MIUI: {str(e)}')
            return f'ÔØî Erro ao desativar otimiza├º├Áes MIUI: {str(e)}'
    def grant_security_permissions(self):
        try:
            permissions = ['android.permission.WRITE_SECURE_SETTINGS', 'android.permission.WRITE_SETTINGS', 'android.permission.MODIFY_PHONE_STATE']
            for perm in permissions:
                self.adb._run_adb_command([self.adb.adb_path, 'shell', f'pm grant com.miui.securitycenter {perm}'])
            return 'Ô£à Permiss├Áes concedidas ao app de seguran├ºa'
        except Exception as e:
            return f'ÔØî Erro ao conceder permiss├Áes: {str(e)}'
    def disable_battery_optimization(self, package_name):
        try:
            commands = [f'dumpsys deviceidle whitelist +{package_name}', f'settings put global app_standby_enabled 0 {package_name}']
            for cmd in commands:
                self.adb._run_adb_command([self.adb.adb_path, 'shell', cmd])
            return f'Ô£à Otimiza├º├úo de bateria desativada para {package_name}'
        except Exception as e:
            return f'ÔØî Erro ao desativar otimiza├º├úo de bateria: {str(e)}'
    def get_battery_info(self):
        try:
            battery_info = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'dumpsys battery'], capture_output=True)
            info = {}
            for line in battery_info.split('\n'):
                if 'level:' in line:
                    info['level'] = line.split('level:')[1].strip()
                elif 'status:' in line:
                    status = line.split('status:')[1].strip()
                    if status == '2':
                        info['status'] = 'Carregando'
                    elif status == '5':
                        info['status'] = 'Completo'
                    else:
                        info['status'] = 'Descarregando'
                elif 'temperature:' in line:
                    temp = float(line.split('temperature:')[1].strip()) / 10
                    info['temperature'] = f'{temp}┬░C'
            if 'level' in info:
                return info['level']
            return '--'
        except Exception as e:
            logger.error(f'Erro ao obter informa├º├Áes da bateria: {str(e)}')
            return '--'
    def bypass_anti_rollback(self):
        try:
            if not self.adb.adb_path:
                return 'ÔØî ADB n├úo encontrado, imposs├¡vel ignorar prote├º├úo anti-rollback'
            commands = ['setprop ro.anti.rollback 0', 'setprop ro.boot.flash.locked 0']
            for cmd in commands:
                self.adb._run_adb_command([self.adb.adb_path, 'shell', cmd])
            anti_rollback = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'getprop ro.boot.anti_version']).strip()
            if anti_rollback:
                message = f'ÔÜá´©Å Prote├º├úo anti-rollback detectada (vers├úo {anti_rollback}). Bypass pode n├úo funcionar.'
            else:
                message = 'Ô£à Prote├º├úo anti-rollback ignorada com sucesso'
            print(message)
            return message
        except Exception as e:
            print(f'Erro ao ignorar prote├º├úo anti-rollback: {e}')
            self.logger.error(f'Erro ao ignorar prote├º├úo anti-rollback: {str(e)}')
            return f'ÔØî Erro ao ignorar prote├º├úo anti-rollback: {str(e)}'
    def enable_camera2api(self):
        try:
            if not self.adb.adb_path:
                return 'ÔØî ADB n├úo encontrado, imposs├¡vel ativar Camera2 API'
            commands = ['setprop persist.camera.HAL3.enabled 1', 'setprop persist.vendor.camera.HAL3.enabled 1', 'setprop persist.camera.eis.enable 1']
            for cmd in commands:
                self.adb._run_adb_command([self.adb.adb_path, 'shell', cmd])
            print('Camera2 API ativada')
            return 'Ô£à Camera2 API ativada com sucesso'
        except Exception as e:
            print(f'Erro ao ativar Camera2 API: {e}')
            self.logger.error(f'Erro ao ativar Camera2 API: {str(e)}')
            return f'ÔØî Erro ao ativar Camera2 API: {str(e)}'
    def disable_dm_verity(self):
        try:
            self.logger.info('Iniciando processo de desativa├º├úo do DM-Verity')
            if not self.adb.fastboot_path:
                self.logger.info('Procurando Fastboot...')
                self.adb.fastboot_path = self.adb.find_fastboot_path()
            if not self.adb.fastboot_path:
                self.logger.error('Fastboot n├úo encontrado')
                return 'ÔØî Fastboot n├úo encontrado, imposs├¡vel desativar DM-Verity\n­ƒÆí Verifique se est├í instalado em C:\\platform-tools'
            self.logger.info(f'Fastboot encontrado: {self.adb.fastboot_path}')
        except Exception as e:
            self.logger.error(f'Erro ao corrigir DM-Verity: {str(e)}')
            return f'ÔØî Erro ao corrigir DM-Verity: {str(e)}'
        try:
            si = None
            cf = 0
            if platform.system() == 'Windows':
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                si.wShowWindow = subprocess.SW_HIDE
                cf = subprocess.CREATE_NO_WINDOW
            result = subprocess.run([self.adb.fastboot_path, 'devices'], capture_output=True, text=True, check=False, startupinfo=si, creationflags=cf, cwd=os.path.dirname(self.adb.fastboot_path))
            self.logger.debug(f'Sa├¡da do fastboot devices: {result.stdout}')
            if not result.stdout.strip():
                self.logger.error('Nenhum dispositivo fastboot detectado')
                return 'ÔØî Nenhum dispositivo em modo fastboot detectado'
            device_id = result.stdout.strip().split()[0]
            self.logger.info(f'Dispositivo fastboot detectado: {device_id}')
            commands = [[self.adb.fastboot_path, 'oem', 'cdms', 'fix'], [self.adb.fastboot_path, '--disable-verity'], [self.adb.fastboot_path, '--disable-verification'], [self.adb.fastboot_path, 'reboot']]
            for cmd in commands:
                self.logger.debug(f'Executando comando: {' '.join(cmd)}')
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=30, startupinfo=si, creationflags=cf, cwd=os.path.dirname(self.adb.fastboot_path))
                self.logger.debug(f'Sa├¡da: {result.stdout} {result.stderr}')
                if result.returncode != 0:
                    self.logger.warning(f'Comando {cmd[0]} falhou, tentando pr├│ximo comando')
            except Exception as e:
                self.logger.error(f'Erro ao verificar dispositivo fastboot: {str(e)}')
                try:
                    try:
                        return f'ÔØî Erro ao verificar dispositivo fastboot: {str(e)}'
                    except subprocess.TimeoutExpired:
                        self.logger.error(f'Timeout ao executar {cmd[0]}')
                    except Exception as e:
                        self.logger.error(f'Erro ao executar {cmd[0]}: {str(e)}')
                except Exception as e:
                    self.logger.error(f'Erro ao corrigir DM-Verity: {str(e)}')
                    return f'ÔØî Erro ao corrigir DM-Verity: {str(e)}'
        except Exception as e:
            self.logger.error(f'Erro ao verificar dispositivo fastboot: {str(e)}')
            try:
                return f'ÔØî Erro ao verificar dispositivo fastboot: {str(e)}'
            except Exception as e:
                self.logger.error(f'Erro ao corrigir DM-Verity: {str(e)}')
                return f'ÔØî Erro ao corrigir DM-Verity: {str(e)}'
        return 'Ô£à DM-Verity corrigido com sucesso. Dispositivo reiniciando...'
    def check_anti_rollback(self):
        try:
            arb = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'getprop ro.boot.anti_version']).strip()
            if arb:
                return f'Ôä╣´©Å Vers├úo Anti-rollback: {arb}'
        except Exception as e:
            return 'ÔÜá´©Å Erro ao verificar Anti-rollback'
        return 'Ôä╣´©Å Anti-rollback n├úo detectado'
    def get_fastboot_device_info(self):
        info = {}
        try:
            basic_vars = ['product', 'variant', 'serialno', 'secure', 'unlocked', 'anti', 'version-bootloader', 'version-baseband', 'current-slot', 'slot-count', 'max-download-size', 'partition-type:userdata', 'partition-size:userdata']
            for var in basic_vars:
                pass
            try:
                result = self.adb.execute_fastboot_command(f'getvar {var}', timeout=5)
                if result:
                    if 'FAILED' not in result:
                        for line in result.split('\n'):
                            if '(bootloader) ' in line:
                                value = line.split('(bootloader) ')[1].strip()
                                if value:
                                    info[var] = value
            except Exception:
                pass
        except Exception as e:
            self.logger.error(f'Erro ao obter info fastboot: {e}')
            return info
        if len(info) < 3:
            try:
                try:
                    result = self.adb.execute_fastboot_command('getvar all', timeout=10)
                    if result:
                        for line in result.split('\n'):
                            line = line.strip()
                            if '(bootloader) ' in line:
                                line = line.split('(bootloader) ')[1].strip()
                            if ': ' not in line:
                                continue
                            if 'finished' not in line.lower():
                                key, value = line.split(': ', 1)
                                key = key.strip().lower()
                                value = value.strip()
                                if not key:
                                    continue
                                if not value:
                                    continue
                                if key not in info:
                                    info[key] = value
                except Exception:
                    return info
            except Exception as e:
                self.logger.error(f'Erro ao obter info fastboot: {e}')
            return info
        return info
    def is_fastboot_connected(self):
        try:
            return self.adb.check_fastboot_device()
        except Exception:
            return False
    def check_bootloader_lock_status(self):
        try:
            if self.adb.is_device_connected():
                locked = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'getprop ro.boot.flash.locked']).strip()
                verified = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'getprop ro.boot.verifiedbootstate']).strip()
                result_lines = ['­ƒöÆ Status Bootloader (ADB):']
                if locked == '1':
                    result_lines.append('  Bootloader: BLOQUEADO')
                elif locked == '0':
                    result_lines.append('  Bootloader: DESBLOQUEADO')
                else:
                    result_lines.append('  Bootloader: Status indispon├¡vel')
                if verified:
                    states = {'green': 'Verificado (Seguro)', 'yellow': 'Parcialmente verificado', 'orange': 'Bootloader desbloqueado', 'red': 'Falha na verifica├º├úo'}
                    state_text = states.get(verified, verified)
                    result_lines.append(f'  Verified Boot: {state_text}')
                return '\n'.join(result_lines)
        except Exception:
            pass
        try:
            if self.is_fastboot_connected():
                result_lines = ['­ƒöÆ Status Bootloader (Fastboot):']
                for var, label in (('unlocked', 'Unlocked'), ('secure', 'Secure Boot')):
                    pass
            try:
                result = self.adb.execute_fastboot_command(f'getvar {var}', timeout=5)
                if result:
                    if 'FAILED' not in result:
                        value = ''
                        for line in result.split('\n'):
                            if '(bootloader) ' in line:
                                value = line.split('(bootloader) ')[1].strip()
                                break
                            if ': ' not in line:
                                continue
                            if not 'finished' not in line.lower():
                                continue
                            parts = line.split(': ', 1)
                            if not len(parts) == 2:
                                continue
                            value = parts[1].strip()
                            break
                        if value:
                            if var == 'unlocked':
                                status = 'DESBLOQUEADO' if value == 'yes' else 'BLOQUEADO'
                                result_lines.append(f'  Bootloader: {status}')
            except Exception:
                pass
        except Exception:
            pass
        return 'ÔÜá´©Å Nenhum dispositivo detectado para verificar bootloader'
    def get_device_identifiers(self):
        try:
            if self.adb.is_device_connected():
                props = {'Serial': 'ro.serialno', 'Codename': 'ro.product.device', 'Hardware': 'ro.hardware', 'Baseband': 'gsm.version.baseband', 'Plataforma': 'ro.board.platform', 'Seguran├ºa': 'ro.build.version.security_patch', 'Build': 'ro.build.display.id'}
                result_lines = ['­ƒôï Identifica├º├úo do Dispositivo (ADB):', '']
                for label, prop in props.items():
                    pass
            try:
                value = self.adb._run_adb_command([self.adb.adb_path, 'shell', f'getprop {prop}']).strip()
                if value:
                    result_lines.append(f'  {label}: {value}')
            except Exception:
                pass
            else:
                if len(result_lines) > 2:
                    pass
        except Exception:
            pass
        try:
            if self.is_fastboot_connected():
                fb_vars = {'Produto': 'product', 'Serial': 'serialno', 'Variante': 'variant', 'Bootloader': 'version-bootloader', 'Baseband': 'version-baseband', 'Unlocked': 'unlocked', 'Anti-rollback': 'anti', 'Secure': 'secure', 'Slot Atual': 'current-slot', 'Slots': 'slot-count'}
                result_lines = ['­ƒôï Identifica├º├úo do Dispositivo (Fastboot):', '']
                for label, var in fb_vars.items():
                    pass
            try:
                result = self.adb.execute_fastboot_command(f'getvar {var}', timeout=5)
                if result:
                    if 'FAILED' not in result:
                        value = ''
                        for line in result.split('\n'):
                            if '(bootloader) ' in line:
                                value = line.split('(bootloader) ')[1].strip()
                                break
                            if ': ' not in line:
                                continue
                            if not 'finished' not in line.lower():
                                continue
                            parts = line.split(': ', 1)
                            if not len(parts) == 2:
                                continue
                            value = parts[1].strip()
                            break
                        if value:
                            result_lines.append(f'  {label}: {value}')
            except Exception:
                pass
            else:
                if len(result_lines) > 2:
                    pass
        except Exception:
            pass
        return 'Ôä╣´©Å Nenhum dispositivo detectado (ADB ou Fastboot)'
    def remove_micloud(self):
        try:
            if self.is_fastboot_connected():
                return 'ÔØî Dispositivo em modo Fastboot.\nPara remover MiCloud, o aparelho precisa estar ligado com depuracao USB ativa.'
            commands = ['pm uninstall -k --user 0 com.xiaomi.finddevice', 'pm uninstall -k --user 0 com.miui.cloudservice', 'pm uninstall -k --user 0 com.xiaomi.account', 'pm clear com.xiaomi.finddevice', 'pm clear com.miui.cloudservice', "settings put global device_name ''", "settings put global user_name ''"]
            for cmd in commands:
                self.adb._run_adb_command([self.adb.adb_path, 'shell', cmd])
            return 'Ô£à MiCloud removido com sucesso'
        except Exception as e:
            self.logger.error(f'remove_micloud falhou: {e}')
            return 'ÔØî Nao foi possivel remover MiCloud. Verifique a conexao e tente novamente.'
    def remove_mi_account(self):
        try:
            adb_commands = ['pm uninstall -k --user 0 com.android.updater', 'pm uninstall -k --user 0 com.xiaomi.account', 'pm uninstall -k --user 0 com.xiaomi.finddevice', 'pm uninstall -k --user 0 com.miui.cloudservice', 'pm uninstall -k --user 0 com.miui.cloudbackup', 'pm clear com.xiaomi.account', 'pm clear com.xiaomi.finddevice', "settings put global device_name ''", "settings put global user_name ''"]
            for cmd in adb_commands:
                pass
            try:
                self.adb._run_adb_command([self.adb.adb_path, 'shell', cmd])
            except:
                pass
            else:
                if not self.adb.check_fastboot_device():
                    return 'Ô£à Conta Mi removida via ADB'
                fastboot_commands = [['erase', 'frp'], ['erase', 'persistent'], ['erase', 'config'], ['oem', 'unlock-go'], ['reboot']]
                for cmd in fastboot_commands:
                    self.adb._run_fastboot_command([self.adb.fastboot_path, *cmd])
        except Exception as e:
            return f'ÔØî Erro ao remover conta Mi: {str(e)}'
        return 'Ô£à Conta Mi removida com sucesso (ADB + Fastboot)'
    def reboot_to_recovery(self):
        try:
            if not self.adb.adb_path:
                return 'ÔØî ADB n├úo encontrado, imposs├¡vel reiniciar para recovery'
            self.adb._run_adb_command([self.adb.adb_path, 'reboot', 'recovery'])
            return 'Ô£à Dispositivo reiniciando para recovery'
        except Exception as e:
            self.logger.error(f'Erro ao reiniciar para recovery: {str(e)}')
            return f'ÔØî Erro ao reiniciar para recovery: {str(e)}'
    def reboot_to_fastboot(self):
        try:
            if not self.adb.adb_path:
                return 'ÔØî ADB n├úo encontrado, imposs├¡vel reiniciar para fastboot'
            self.adb._run_adb_command([self.adb.adb_path, 'reboot', 'bootloader'])
            return 'Ô£à Dispositivo reiniciando para fastboot'
        except Exception as e:
            self.logger.error(f'Erro ao reiniciar para fastboot: {str(e)}')
            return f'ÔØî Erro ao reiniciar para fastboot: {str(e)}'
    def reboot_to_edl(self):
        try:
            if not self.adb.adb_path:
                return 'ÔØî ADB n├úo encontrado, imposs├¡vel reiniciar para EDL'
            self.adb._run_adb_command([self.adb.adb_path, 'reboot', 'edl'])
            return 'Ô£à Dispositivo reiniciando para modo EDL'
        except Exception as e:
            self.logger.error(f'Erro ao reiniciar para EDL: {str(e)}')
            return f'ÔØî Erro ao reiniciar para EDL: {str(e)}'
    def unlock_mi_account(self):
        try:
            if not self.adb.adb_path:
                return 'ÔØî ADB n├úo encontrado, imposs├¡vel remover conta Mi'
            account_status = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'getprop ro.secureboot.lockstate']).strip()
            if account_status != 'locked':
                return 'Ô£à Dispositivo n├úo possui bloqueio de conta Mi'
            commands = ['pm clear com.xiaomi.finddevice', 'pm disable com.xiaomi.finddevice', 'settings put secure find_device_enabled 0', 'setprop persist.sys.mi_account_removed 1']
            for cmd in commands:
                self.adb._run_adb_command([self.adb.adb_path, 'shell', cmd])
            print('Conta Mi removida')
            return 'Ô£à Prote├º├úo de conta Mi removida. Reinicie o dispositivo.'
        except Exception as e:
            print(f'Erro ao remover conta Mi: {e}')
            self.logger.error(f'Erro ao remover conta Mi: {str(e)}')
            return f'ÔØî Erro ao remover conta Mi: {str(e)}'
