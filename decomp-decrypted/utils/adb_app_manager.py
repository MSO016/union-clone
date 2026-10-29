import subprocess
import re
import logging
import os
from typing import (List, Dict, Optional, Tuple)
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
logger = logging.getLogger(__name__)
class AndroidVersion(Enum):
    ANDROID_9 = (28, 'Android 9 (Pie)')
    ANDROID_10 = (29, 'Android 10')
    ANDROID_11 = (30, 'Android 11')
    ANDROID_12 = (31, 'Android 12')
    ANDROID_13 = (33, 'Android 13')
    ANDROID_14 = (34, 'Android 14')
    UNKNOWN = (0, 'Vers├úo Desconhecida')
class AppType(Enum):
    ALL = 'all'
    SYSTEM = 'system'
    USER = 'user'
    DISABLED = 'disabled'
    ENABLED = 'enabled'
@dataclass
class AppInfo:
    package_name: str
    app_name: str = ''
    version: str = ''
    is_system: bool = False
    is_enabled: bool = True
    is_suspended: bool = False
    install_location: str = ''
    size_info: Dict[str, str] = None
    permissions: List[str] = None
    def __post_init__(self):
        if self.size_info is None:
            self.size_info = {}
        if self.permissions is None:
            self.permissions = []
class ADBAppManager:
    def __init__(self, adb_manager):
        self.adb_manager = adb_manager
        self.logger = logging.getLogger(__name__)
        self.android_version = None
        self.device_serial = None
        self._apps_cache = {}
        self._cache_timestamp = None
        self._cache_timeout = 30
    def _execute_adb_command(self, command: List[str], timeout: int=30) -> str:
        try:
            if not self.adb_manager.adb_path:
                raise Exception('ADB n├úo est├í dispon├¡vel')
            if not os.path.isfile(self.adb_manager.adb_path):
                raise Exception('ADB n├úo encontrado. Verifique a instala├º├úo.')
            full_command = [self.adb_manager.adb_path] + command
            self.logger.debug(f'Executando comando: {' '.join(full_command)}')
            import platform
            if platform.system() == 'Windows':
                result = subprocess.run(full_command, capture_output=True, text=True, encoding='utf-8', errors='ignore', startupinfo=self.adb_manager.startupinfo, creationflags=self.adb_manager.creation_flags, timeout=timeout, check=False)
            else:
                result = subprocess.run(full_command, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=timeout, check=False)
            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else 'Erro desconhecido'
                raise Exception(f'Comando ADB falhou: {error_msg}')
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            raise Exception(f'Timeout na execu├º├úo do comando ADB ({timeout}s)')
        except Exception as e:
            self.logger.error(f'Erro ao executar comando ADB: {str(e)}')
            raise
    def _get_android_version(self) -> AndroidVersion:
        try:
            if self.android_version is not None:
                return self.android_version
            sdk_version = self._execute_adb_command(['shell', 'getprop', 'ro.build.version.sdk'])
            sdk_int = int(sdk_version.strip())
            version_map = {28: AndroidVersion.ANDROID_9, 29: AndroidVersion.ANDROID_10, 30: AndroidVersion.ANDROID_11, 31: AndroidVersion.ANDROID_12, 32: AndroidVersion.ANDROID_12, 33: AndroidVersion.ANDROID_13, 34: AndroidVersion.ANDROID_14}
            self.android_version = version_map.get(sdk_int, AndroidVersion.UNKNOWN)
            self.logger.info(f'Android detectado: {self.android_version.value[1]} (SDK {sdk_int})')
        except Exception as e:
            self.logger.error(f'Erro ao detectar vers├úo do Android: {str(e)}')
            self.android_version = AndroidVersion.UNKNOWN
        return self.android_version
    def list_packages(self, app_type: AppType=AppType.ALL, include_details: bool=False) -> List[AppInfo]:
        try:
            cache_key = f'{app_type.value}_{include_details}'
            if self._is_cache_valid(cache_key):
                return self._apps_cache[cache_key]
            self.logger.info(f'Listando pacotes: {app_type.value}')
            command = ['shell', 'pm', 'list', 'packages']
            if app_type == AppType.SYSTEM:
                command.append('-s')
            elif app_type == AppType.USER:
                command.append('-3')
            elif app_type == AppType.DISABLED:
                command.append('-d')
            elif app_type == AppType.ENABLED:
                command.append('-e')
            output = self._execute_adb_command(command)
            apps = []
            for line in output.split('\n'):
                line = line.strip()
                if line.startswith('package:'):
                    package_name = line.replace('package:', '')
                    app_info = AppInfo(package_name=package_name, is_system=app_type == AppType.SYSTEM)
                    if include_details:
                        pass
            try:
                self._get_app_status(app_info)
                self._get_app_extra_details(app_info)
            except Exception as e:
                self.logger.debug(f'Erro ao obter detalhes de {package_name}: {str(e)}')
            else:
                apps.append(app_info)
                self._apps_cache[cache_key] = apps
                self._cache_timestamp = datetime.now()
                self.logger.info(f'Encontrados {len(apps)} pacotes')
        except Exception as e:
            self.logger.error(f'Erro ao listar pacotes: {str(e)}')
            raise
        return apps
    def list_mdm_packages(self, include_details: bool=False) -> List[AppInfo]:
        try:
            self.logger.info('Detectando aplicativos MDM...')
            mdm_patterns = ['com.payjoy.access', 'com.payjoy.permission', 'paks', 'paksnotification', 'payjoyaccess', 'sysdll', 'motoframeworkresoverlaypayjoy', 'paksoverlayusc', 'paksoverlaytce', 'configupdater', 'carrierconfig', 'carrierdefaultapp', 'com.android.managedprovisioning', 'com.android.deviceowner', 'com.samsung.android.mdm', 'com.samsung.android.knox', 'com.airwatch', 'com.mobileiron', 'com.microsoft.intune', 'com.citrix.xenmobile', 'com.maas360', 'com.soti.mobicontrol', 'com.good.gd', 'com.vmware.boxer', 'com.blackberry.dynamics', 'com.checkpoint.pointsec', 'com.zenprise', 'com.absolute.android.securezone', 'com.lookout.enterprise', 'com.symantec.mobilesecurity.sep', 'com.kaspersky.ksm', 'com.f5.edge.client', 'com.citrix.receiver.nfuse', 'com.parallels.ras.client', 'com.teamviewer.quicksupport', 'com.logmein.rescue', 'com.bomgar.android.enterprise', 'com.amtel.android.mdm', 'com.miradore.android.mdm', 'com.hexnode.android.mdm', 'com.scalefusion.android.mdm', 'com.42gears.suremdm', 'com.manageengine.mdm', 'com.sophos.mobilecontrol', 'com.spiceworks.android.mdm', 'com.comodo.mdm', 'com.trend.imss.android.mdm', 'com.eset.mdm', 'com.avast.android.mdm', 'com.avg.android.mdm', 'com.bitdefender.mdm', 'com.norton.mdm', 'com.mcafee.mdm', 'com.paloaltonetworks.globalprotect']
            all_apps = self.list_packages(AppType.ALL, include_details)
            mdm_apps = []
            for app in all_apps:
                package_lower = app.package_name.lower()
                is_mdm = any((pattern.lower() in package_lower for pattern in mdm_patterns))
                mdm_keywords = ['mdm', 'device', 'management', 'enterprise', 'security', 'knox', 'admin', 'policy', 'compliance', 'remote', 'control', 'monitor', 'tracking', 'location', 'geofence', 'kiosk', 'lockdown', 'provision']
                if not is_mdm:
                    is_mdm = any((keyword in package_lower for keyword in mdm_keywords))
                if not is_mdm:
                    continue
                if app.app_name:
                    app.app_name = f'[MDM] {app.app_name}'
                else:
                    app.app_name = '[MDM] App'
                mdm_apps.append(app)
            self.logger.info(f'Detectados {len(mdm_apps)} aplicativos MDM')
            return mdm_apps
        except Exception as e:
            self.logger.error(f'Erro ao detectar aplicativos MDM: {e}')
            return []
    def _get_app_status(self, app_info: AppInfo) -> None:
        try:
            output = self._execute_adb_command(['shell', 'dumpsys', 'package', app_info.package_name], timeout=5)
            app_info.is_enabled = True
            app_info.is_suspended = False
            for line in output.split('\n'):
                line_lower = line.strip().lower()
                if 'suspended=' in line_lower:
                    if 'suspended=true' in line_lower:
                        app_info.is_suspended = True
                        app_info.is_enabled = False
                elif 'hidden=' in line_lower:
                    if 'hidden=true' in line_lower:
                        app_info.is_suspended = True
                        app_info.is_enabled = False
                else:
                    if 'enabled=' not in line_lower:
                        continue
                    if 'enabled=0' in line_lower or 'enabled=2' in line_lower:
                        app_info.is_enabled = False
                    elif 'enabled=1' in line_lower:
                        app_info.is_enabled = True
            return
        except Exception as e:
            self.logger.debug(f'Erro ao obter status de {app_info.package_name}: {str(e)}')
    def _get_app_extra_details(self, app_info: AppInfo) -> None:
        try:
            output = self._execute_adb_command(['shell', 'dumpsys', 'package', app_info.package_name])
            for line in output.split('\n'):
                line = line.strip()
                if line.startswith('versionName='):
                    app_info.version = line.split('=', 1)[1]
                elif line.startswith('applicationInfo='):
                    app_info.is_system = 'system' in line.lower()
        except Exception as e:
            self.logger.warning(f'Erro ao obter detalhes extras de {app_info.package_name}: {str(e)}')
        try:
            try:
                label_output = self._execute_adb_command(['shell', 'pm', 'list', 'packages', '-3', '-f', app_info.package_name])
                if label_output:
                    app_info.app_name = self._extract_app_name(label_output)
                    return
            except Exception:
                app_info.app_name = app_info.package_name
        except Exception as e:
            self.logger.warning(f'Erro ao obter detalhes extras de {app_info.package_name}: {str(e)}')
    def _get_app_details(self, app_info: AppInfo) -> None:
        self._get_app_status(app_info)
        self._get_app_extra_details(app_info)
    def _extract_app_name(self, pm_output: str) -> str:
        lines = pm_output.split('\n')
        for line in lines:
            if 'package:' in line:
                parts = line.split('=')
                if len(parts) > 1:
                    apk_path = parts[1].strip()
                    apk_name = apk_path.split('/')[-1]
                    return apk_name.replace('.apk', '')
        return ''
    def force_stop_app(self, package_name: str) -> bool:
        try:
            self.logger.info(f'For├ºando parada do app: {package_name}')
            if not self._package_exists(package_name):
                raise Exception(f'Pacote {package_name} n├úo encontrado')
            self._execute_adb_command(['shell', 'am', 'force-stop', package_name])
            self.logger.info(f'App {package_name} parado com sucesso')
            return True
        except Exception as e:
            self.logger.error(f'Erro ao parar app {package_name}: {str(e)}')
            return False
    def clear_app_cache(self, package_name: str) -> Tuple[bool, str]:
        try:
            self.logger.info(f'Limpando cache do app: {package_name}')
            if not self._package_exists(package_name):
                return False, f'Pacote {package_name} n├úo encontrado'
            android_version = self._get_android_version()
            if android_version in (AndroidVersion.ANDROID_13, AndroidVersion.ANDROID_14):
                return self._clear_cache_only(package_name)
            return self._clear_cache_legacy(package_name)
        except Exception as e:
            error_msg = f'Erro ao limpar cache de {package_name}: {str(e)}'
            self.logger.error(error_msg)
            return False, error_msg
    def _clear_cache_only(self, package_name: str) -> Tuple[bool, str]:
        try:
            output = self._execute_adb_command(['shell', 'pm', 'clear', '--cache-only', package_name])
            if 'Success' in output:
                msg = f'Cache do {package_name} limpo com sucesso'
                self.logger.info(msg)
                return True, msg
            msg = f'Falha ao limpar cache: {output}'
            self.logger.warning(msg)
            return False, msg
        except Exception as e:
            self.logger.warning(f'Comando --cache-only falhou: {str(e)}')
            return self._clear_cache_legacy(package_name)
    def _clear_cache_legacy(self, package_name: str) -> Tuple[bool, str]:
        warning_msg = f'ATEN├ç├âO: No Android {self.android_version.value[1]}, n├úo ├® poss├¡vel limpar apenas o cache via ADB sem root.\n\nOp├º├Áes dispon├¡veis:\n1. Limpar TODOS os dados do app (cache + dados do usu├írio)\n2. Abrir configura├º├Áes do app para limpeza manual\n3. Cancelar opera├º├úo\n\nPara {package_name}, recomendamos abrir as configura├º├Áes manualmente.'
        return False, warning_msg
    def clear_all_data(self, package_name: str) -> Tuple[bool, str]:
        try:
            self.logger.warning(f'Limpando TODOS os dados do app: {package_name}')
            if not self._package_exists(package_name):
                return False, f'Pacote {package_name} n├úo encontrado'
            output = self._execute_adb_command(['shell', 'pm', 'clear', package_name])
            if 'Success' in output:
                msg = f'Todos os dados do {package_name} foram limpos com sucesso'
                self.logger.info(msg)
                return True, msg
            msg = f'Falha ao limpar dados: {output}'
            self.logger.warning(msg)
            return False, msg
        except Exception as e:
            error_msg = f'Erro ao limpar dados de {package_name}: {str(e)}'
            self.logger.error(error_msg)
            return False, error_msg
    def open_app_settings(self, package_name: str) -> bool:
        try:
            self.logger.info(f'Abrindo configura├º├Áes do app: {package_name}')
            if not self._package_exists(package_name):
                raise Exception(f'Pacote {package_name} n├úo encontrado')
            self._execute_adb_command(['shell', 'am', 'start', '-a', 'android.settings.APPLICATION_DETAILS_SETTINGS', '-d', f'package:{package_name}'])
            self.logger.info(f'Configura├º├Áes abertas para {package_name}')
            return True
        except Exception as e:
            self.logger.error(f'Erro ao abrir configura├º├Áes de {package_name}: {str(e)}')
            return False
    def batch_force_stop(self, package_names: List[str]) -> Dict[str, bool]:
        results = {}
        for package_name in package_names:
            results[package_name] = self.force_stop_app(package_name)
        return results
    def batch_clear_cache(self, package_names: List[str]) -> Dict[str, Tuple[bool, str]]:
        results = {}
        for package_name in package_names:
            results[package_name] = self.clear_app_cache(package_name)
        return results
    def search_packages(self, query: str, app_type: AppType=AppType.ALL) -> List[AppInfo]:
        try:
            all_apps = self.list_packages(app_type)
            filtered_apps = []
            query_lower = query.lower()
            for app in all_apps:
                if query_lower in app.package_name.lower() or query_lower in app.app_name.lower():
                    filtered_apps.append(app)
            return filtered_apps
        except Exception as e:
            self.logger.error(f'Erro ao pesquisar pacotes: {str(e)}')
            return []
    def get_app_info(self, package_name: str) -> Optional[AppInfo]:
        try:
            if not self._package_exists(package_name):
                return
            app_info = AppInfo(package_name=package_name)
            self._get_app_details(app_info)
            return app_info
        except Exception as e:
            self.logger.error(f'Erro ao obter informa├º├Áes de {package_name}: {str(e)}')
    def _package_exists(self, package_name: str) -> bool:
        try:
            output = self._execute_adb_command(['shell', 'pm', 'list', 'packages', package_name])
            return f'package:{package_name}' in output
        except Exception:
            return False
    def _is_cache_valid(self, cache_key: str) -> bool:
        if cache_key not in self._apps_cache or self._cache_timestamp is None:
            return False
        time_diff = (datetime.now() - self._cache_timestamp).total_seconds()
        return time_diff < self._cache_timeout
    def clear_cache(self) -> None:
        self._apps_cache.clear()
        self._cache_timestamp = None
        self.logger.info('Cache do gerenciador limpo')
    def get_summary(self) -> Dict[str, int]:
        try:
            all_apps = self.list_packages(AppType.ALL)
            system_apps = self.list_packages(AppType.SYSTEM)
            user_apps = self.list_packages(AppType.USER)
            return {'total': len(all_apps), 'system': len(system_apps), 'user': len(user_apps), 'android_version': self._get_android_version().value[0]}
        except Exception as e:
            self.logger.error(f'Erro ao obter resumo: {str(e)}')
            return {'total': 0, 'system': 0, 'user': 0, 'android_version': 0}
    def uninstall_app(self, package_name: str) -> bool:
        try:
            self.logger.info(f'Desinstalando aplicativo: {package_name}')
            if not self._package_exists(package_name):
                raise Exception(f'Pacote {package_name} n├úo encontrado')
            output = self._execute_adb_command(['shell', 'pm', 'uninstall', '--user', '0', package_name])
            if 'Success' in output:
                msg = f'Aplicativo {package_name} desinstalado com sucesso'
                self.logger.info(msg)
                self.clear_cache()
                return True
            msg = f'Falha ao desinstalar: {output}'
            self.logger.warning(msg)
            return False
        except Exception as e:
            error_msg = f'Erro ao desinstalar {package_name}: {str(e)}'
            self.logger.error(error_msg)
            return False
    def freeze_app(self, package_name: str) -> Tuple[bool, str]:
        try:
            self.logger.info(f'Congelando aplicativo: {package_name}')
            if not self._package_exists(package_name):
                return False, f'Pacote {package_name} n├úo encontrado'
            android_version = self._get_android_version()
            if android_version == AndroidVersion.UNKNOWN:
                return (False, 'N├úo foi poss├¡vel detectar a vers├úo do Android')
            output = self._execute_adb_command(['shell', 'pm', 'suspend', package_name])
            if 'Error' not in output and 'Failed' not in output:
                msg = f'Aplicativo {package_name} congelado com sucesso'
                self.logger.info(msg)
                self.clear_cache()
                return True, msg
            self.logger.warning('Falha ao congelar %s: %s', package_name, output)
            return False, f'Nao foi possivel congelar o aplicativo {package_name}'
        except Exception as e:
            self.logger.error('Erro ao congelar %s: %s', package_name, e)
            return False, f'Nao foi possivel congelar o aplicativo {package_name}'
    def unfreeze_app(self, package_name: str) -> Tuple[bool, str]:
        try:
            self.logger.info(f'Descongelando aplicativo: {package_name}')
            if not self._package_exists(package_name):
                return False, f'Pacote {package_name} n├úo encontrado'
            output = self._execute_adb_command(['shell', 'pm', 'unsuspend', package_name])
            if 'Error' not in output and 'Failed' not in output:
                msg = f'Aplicativo {package_name} descongelado com sucesso'
                self.logger.info(msg)
                self.clear_cache()
                return True, msg
            self.logger.warning('Falha ao descongelar %s: %s', package_name, output)
            return False, f'Nao foi possivel descongelar o aplicativo {package_name}'
        except Exception as e:
            self.logger.error('Erro ao descongelar %s: %s', package_name, e)
            return False, f'Nao foi possivel descongelar o aplicativo {package_name}'
    def enable_app(self, package_name: str) -> Tuple[bool, str]:
        try:
            self.logger.info(f'Habilitando aplicativo: {package_name}')
            if not self._package_exists(package_name):
                return False, f'Pacote {package_name} n├úo encontrado'
            output = self._execute_adb_command(['shell', 'pm', 'enable', '--user', '0', package_name])
            if 'enabled' in output.lower() or 'success' in output.lower():
                msg = f'Aplicativo {package_name} habilitado com sucesso'
                self.logger.info(msg)
                self.clear_cache()
                return True, msg
            self.logger.warning('Falha ao habilitar %s: %s', package_name, output)
            return False, f'Nao foi possivel habilitar o aplicativo {package_name}'
        except Exception as e:
            self.logger.error('Erro ao habilitar %s: %s', package_name, e)
            return False, f'Nao foi possivel habilitar o aplicativo {package_name}'
    def disable_app(self, package_name: str) -> Tuple[bool, str]:
        try:
            self.logger.info(f'Desabilitando aplicativo: {package_name}')
            if not self._package_exists(package_name):
                return False, f'Pacote {package_name} n├úo encontrado'
            output = self._execute_adb_command(['shell', 'pm', 'disable-user', '--user', '0', package_name])
            if 'disabled' in output.lower() or 'success' in output.lower():
                msg = f'Aplicativo {package_name} desabilitado com sucesso'
                self.logger.info(msg)
                self.clear_cache()
                return True, msg
            self.logger.warning('Falha ao desabilitar %s: %s', package_name, output)
            return False, f'Nao foi possivel desabilitar o aplicativo {package_name}'
        except Exception as e:
            self.logger.error('Erro ao desabilitar %s: %s', package_name, e)
            return False, f'Nao foi possivel desabilitar o aplicativo {package_name}'
    def _is_browser_app(self, package_name: str) -> bool:
        browser_patterns = ['chrome', 'firefox', 'browser', 'internet', 'opera', 'edge', 'vivaldi', 'brave', 'samsung', 'webview', 'mi.globalbrowser', 'ucturbo', 'dolphin', 'maxthon', 'com.android.chrome', 'com.android.browser', 'org.mozilla.firefox', 'com.sec.android.app.sbrowser', 'com.opera.browser', 'com.opera.mini.native', 'com.UCMobile.intl', 'com.chrome.beta', 'com.chrome.dev']
        package_lower = package_name.lower()
        return any((pattern in package_lower for pattern in browser_patterns))
    def smart_clear_app_cache(self, package_name: str) -> Tuple[bool, str, Dict]:
        try:
            self.logger.info(f'Iniciando limpeza inteligente para: {package_name}')
            if not self._package_exists(package_name):
                return False, f'Aplicativo {package_name} n├úo encontrado no dispositivo', {'type': 'error', 'user_action': False, 'technical_details': f'Pacote {package_name} n├úo existe'}
            is_browser = self._is_browser_app(package_name)
            android_version = self._get_android_version()
            if is_browser:
                return self._handle_browser_cache_smart(package_name, android_version)
            return self._handle_regular_app_cache_smart(package_name, android_version)
        except Exception as e:
            error_msg = f'Erro inesperado ao tentar limpar cache de {package_name}'
            self.logger.error(f'{error_msg}: {str(e)}')
            return False, error_msg, {'type': 'error', 'user_action': False, 'technical_details': str(e)}
    def _handle_browser_cache_smart(self, package_name: str, android_version) -> Tuple[bool, str, Dict]:
        browser_name = self._get_browser_friendly_name(package_name)
        try:
            self._execute_adb_command(['shell', 'am', 'force-stop', package_name])
            self.logger.info(f'Navegador {package_name} parado com sucesso')
        except Exception:
            pass
        if android_version.value[0] >= 28:
            try:
                output = self._execute_adb_command(['shell', 'pm', 'clear', '--cache-only', package_name], timeout=45)
                if 'Success' in output:
                    return True, f'Cache do {browser_name} processado', {'type': 'browser_partial_success', 'user_action': True, 'message': f" Comando de limpeza executado para {browser_name}\n\n´©Å IMPORTANTE: Navegadores usam cache protegido.\nPara limpeza completa, recomendamos:\nÔÇó Abrir {browser_name} > Menu > Configura├º├Áes\nÔÇó Procurar 'Limpar dados de navega├º├úo'\nÔÇó Selecionar cache e cookies\n\n Isso garante limpeza completa e segura!", 'browser_name': browser_name, 'manual_cleanup_recommended': True}
            except Exception:
                pass
        try:
            trim_success = self._try_smart_trim_caches()
            if trim_success:
                return True, 'Otimiza├º├úo do sistema executada', {'type': 'browser_system_optimization', 'user_action': True, 'message': f' Sistema otimizado para {browser_name}\n\n´©Å LIMITA├ç├âO T├ëCNICA: Navegadores protegem seu cache\npor seguran├ºa do Android.\n\n O que fizemos:\nÔÇó Parou o {browser_name}\nÔÇó Otimizou cache geral do sistema\nÔÇó Liberou mem├│ria dispon├¡vel\n\n Para limpeza completa do navegador:\nÔÇó Abrir {browser_name}\nÔÇó Menu > Configura├º├Áes > Limpar dados\n\n Isso ├® normal e seguro!', 'browser_name': browser_name, 'manual_cleanup_recommended': True}
        except Exception:
            pass
        return False, f'Limpeza limitada para {browser_name}', {'type': 'browser_limitation', 'user_action': True, 'message': f' {browser_name} usa cache protegido\n\n´©Å EXPLICA├ç├âO T├ëCNICA:\nNavegadores modernos protegem seus dados por\nseguran├ºa. O ADB n├úo consegue limpar diretamente.\n\n SOLU├ç├òES DISPON├ìVEIS:\n\n1´©ÅÔâú MANUAL (Recomendado):\nÔÇó Abrir {browser_name}\nÔÇó Menu > Configura├º├Áes > Limpar dados\n\n2´©ÅÔâú RADICAL (Perde senhas):\nÔÇó Limpar TODOS os dados do app\nÔÇó ´©Å Remove senhas e configura├º├Áes\n\n Para t├®cnicos: Isso ├® comportamento normal\ne esperado em Android moderno!', 'browser_name': browser_name, 'manual_cleanup_recommended': True, 'radical_option_available': True}
    def _handle_regular_app_cache_smart(self, package_name: str, android_version) -> Tuple[bool, str, Dict]:
        app_name = self._get_app_friendly_name(package_name)
        if android_version.value[0] >= 28:
            try:
                output = self._execute_adb_command(['shell', 'pm', 'clear', '--cache-only', package_name], timeout=30)
                if 'Success' in output:
                    return True, f'Cache de {app_name} limpo com sucesso', {'type': 'regular_app_success', 'user_action': False, 'message': f' Cache do {app_name} foi limpo!\n\n Opera├º├úo realizada:\nÔÇó Cache tempor├írio removido\nÔÇó Dados do usu├írio preservados\nÔÇó App pode iniciar mais r├ípido\n\n Economia de espa├ºo realizada com sucesso!', 'app_name': app_name}
            except Exception:
                pass
        return self._clear_cache_legacy_smart(package_name, app_name, android_version)
    def _clear_cache_legacy_smart(self, package_name: str, app_name: str, android_version) -> Tuple[bool, str, Dict]:
        return False, f'Limpeza de cache limitada para {app_name}', {'type': 'legacy_limitation', 'user_action': True, 'message': f'´©Å LIMITA├ç├âO DO ANDROID {android_version.value[1]}\n\n Seu dispositivo n├úo suporta limpeza\nde cache via ADB sem root.\n\n OP├ç├òES DISPON├ìVEIS:\n\n1´©ÅÔâú MANUAL:\nÔÇó Configura├º├Áes > Apps > {app_name}\nÔÇó Armazenamento > Limpar Cache\n\n2´©ÅÔâú LIMPAR TUDO:\nÔÇó Remove TODOS os dados do app\nÔÇó ´©Å Perde configura├º├Áes e logins\n\n Isso ├® normal em Android mais antigo!', 'app_name': app_name, 'manual_cleanup_available': True, 'full_clear_available': True}
    def _try_smart_trim_caches(self) -> bool:
        try:
            cache_sizes = ['256M', '512M', '1G']
            for size in cache_sizes:
                try:
                    try:
                        output = self._execute_adb_command(['shell', 'pm', 'trim-caches', size], timeout=60)
                        if 'Error' not in output and 'Failed' not in output:
                            self.logger.info(f'Trim caches executado: {size}')
                            return True
                    except Exception:
                        continue
                except Exception as e:
                    self.logger.warning(f'Erro no trim caches: {str(e)}')
                    return False
        except Exception as e:
            self.logger.warning(f'Erro no trim caches: {str(e)}')
        return False
    def _get_browser_friendly_name(self, package_name: str) -> str:
        browser_names = {'com.android.chrome': 'Google Chrome', 'com.chrome.beta': 'Chrome Beta', 'com.chrome.dev': 'Chrome Dev', 'org.mozilla.firefox': 'Mozilla Firefox', 'com.sec.android.app.sbrowser': 'Samsung Internet', 'com.opera.browser': 'Opera', 'com.opera.mini.native': 'Opera Mini', 'com.UCMobile.intl': 'UC Browser', 'com.android.browser': 'Navegador Android', 'com.mi.globalbrowser': 'Mi Browser'}
        return browser_names.get(package_name, 'Navegador')
    def _get_app_friendly_name(self, package_name: str) -> str:
        try:
            parts = package_name.split('.')
            if len(parts) > 0:
                return parts[-1].title()
            return package_name
        except:
            return package_name
    def list_removed_packages(self) -> List[str]:
        try:
            self.logger.info('Listando pacotes removidos do usuario principal')
            output_all = self._execute_adb_command(['shell', 'pm', 'list', 'packages', '-u'], timeout=30)
            output_installed = self._execute_adb_command(['shell', 'pm', 'list', 'packages'], timeout=30)
            all_pkgs = set()
            for line in output_all.split('\n'):
                line = line.strip()
                if line.startswith('package:'):
                    all_pkgs.add(line.replace('package:', ''))
            installed_pkgs = set()
            for line in output_installed.split('\n'):
                line = line.strip()
                if line.startswith('package:'):
                    installed_pkgs.add(line.replace('package:', ''))
            removed = sorted(all_pkgs - installed_pkgs)
            self.logger.info('Pacotes removidos encontrados: %d', len(removed))
            return removed
        except Exception as e:
            self.logger.error('Erro ao listar pacotes removidos: %s', e)
            return []
    def list_disabled_packages(self) -> List[str]:
        try:
            self.logger.info('Listando pacotes desabilitados')
            output = self._execute_adb_command(['shell', 'pm', 'list', 'packages', '-d'], timeout=30)
            packages = []
            for line in output.split('\n'):
                line = line.strip()
                if line.startswith('package:'):
                    packages.append(line.replace('package:', ''))
            self.logger.info('Pacotes desabilitados encontrados: %d', len(packages))
            return sorted(packages)
        except Exception as e:
            self.logger.error('Erro ao listar pacotes desabilitados: %s', e)
            return []
    def install_existing_package(self, package_name: str) -> Tuple[bool, str]:
        try:
            self.logger.info('Reinstalando pacote existente: %s', package_name)
            try:
                output = self._execute_adb_command(['shell', 'cmd', 'package', 'install-existing', '--user', '0', package_name], timeout=30)
            except Exception:
                self.logger.warning('Comando principal falhou, tentando alternativa')
                output = self._execute_adb_command(['shell', 'pm', 'install-existing', '--user', '0', package_name], timeout=30)
            else:
                if 'installed' in output.lower() or package_name in output.lower():
                    pass
        except Exception as e:
            self.logger.error('Erro ao reinstalar pacote %s: %s', package_name, e)
            return (False, 'Ocorreu um erro ao tentar restaurar. Verifique a conexao e tente novamente.')
        try:
            self.logger.warning('Resposta inesperada ao reinstalar: %s', output)
        except Exception as e:
            self.logger.error('Erro ao reinstalar pacote %s: %s', package_name, e)
            return (False, 'Ocorreu um erro ao tentar restaurar. Verifique a conexao e tente novamente.')
        return (False, 'Nao foi possivel restaurar o aplicativo. Tente reiniciar o dispositivo.')
    def install_apk_from_file(self, apk_path: str) -> Tuple[bool, str]:
        try:
            self.logger.info('Instalando APK: %s', apk_path)
            if not apk_path or not os.path.isfile(apk_path):
                return (False, 'Arquivo nao encontrado. Verifique o caminho e tente novamente.')
            if not apk_path.lower().endswith('.apk'):
                return (False, 'O arquivo selecionado nao e um aplicativo valido.')
            if os.path.getsize(apk_path) == 0:
                return (False, 'O arquivo selecionado esta vazio.')
            output = self._execute_adb_command(['install', '-r', apk_path], timeout=120)
            if 'success' in output.lower():
                self.clear_cache()
                self.logger.info('APK instalado com sucesso: %s', apk_path)
                return (True, 'Aplicativo instalado com sucesso!')
            self.logger.warning('Falha ao instalar APK: %s', output)
            return (False, 'Nao foi possivel instalar o aplicativo. Verifique se o arquivo e compativel com o dispositivo.')
        except Exception as e:
            self.logger.error('Erro ao instalar APK %s: %s', apk_path, e)
            return (False, 'Ocorreu um erro durante a instalacao. Verifique a conexao e tente novamente.')
