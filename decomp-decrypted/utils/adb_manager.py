import subprocess
import os
import tempfile
from PyQt5.QtWidgets import (QMessageBox, QProgressDialog, QFileDialog)
from PyQt5.QtCore import Qt
import threading
from queue import Queue
import time
import re
import platform
import logging
import sys
from datetime import datetime
import atexit
from pathlib import Path
import stat
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
_DEVICES_LONG_LINE_RE = re.compile('^(\\S+)\\s+(\\S+)(?:\\s+(.*))?$')
def _parse_devices_long_output(raw):
    parsed = []
    if not raw:
        return parsed
    for linha in str(raw).splitlines():
        item = linha.strip()
        if not item:
            continue
        if item.startswith('List of') or item.startswith('*'):
            continue
        match = _DEVICES_LONG_LINE_RE.match(item)
        if not match:
            continue
        info = {'serial': match.group(1) or '', 'state': match.group(2) or '', 'usb': '', 'model': '', 'product': '', 'transport': ''}
        extras = match.group(3) or ''
        for token in extras.split():
            if token.startswith('usb:'):
                info['usb'] = token[4:]
            elif token.startswith('model:'):
                info['model'] = token[6:].replace('_', ' ')
            elif token.startswith('product:'):
                info['product'] = token[8:]
            elif token.startswith('transport_id:'):
                info['transport'] = token[13:]
        parsed.append(info)
        continue
    return parsed
class ADBManager:
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ADBManager, cls).__new__(cls)
            return cls._instance
    def __init__(self):
        with self._lock:
            if not self._initialized:
                self.logger = logging.getLogger(__name__)
                self.adb_path = None
                self.fastboot_path = None
                self.logcat_process = None
                self.log_capture_running = False
                self.log_buffer = []
                self.log_lock = threading.Lock()
                self.command_lock = threading.Lock()
                self.lock = threading.Lock()
                self.active_processes = []
                self._adb_blocked_by_windows = False
                self._block_error_shown = False
                self.startupinfo = None
                self.creation_flags = 0
                if os.name == 'nt':
                    self.startupinfo = subprocess.STARTUPINFO()
                    self.startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    self.startupinfo.wShowWindow = subprocess.SW_HIDE
                    self.creation_flags = subprocess.CREATE_NO_WINDOW
                self.log_queue = Queue()
                self.log_thread = None
                self.running = False
                self.adb_path = None
                self.fastboot_path = None
                atexit.register(self._cleanup_on_exit)
                self.selected_serial = None
                self.__class__._initialized = True
    def test_adb_functionality(self, adb_path):
        try:
            if platform.system() == 'Windows':
                result = subprocess.run([adb_path, 'version'], capture_output=True, timeout=5, text=True, startupinfo=self.startupinfo, creationflags=self.creation_flags)
            else:
                result = subprocess.run([adb_path, 'version'], capture_output=True, timeout=5, text=True)
            if result.returncode == 0 and 'Android Debug Bridge' in result.stdout:
                self.logger.info(f'ADB funcional - Vers├úo: {result.stdout.strip()}')
                self._adb_blocked_by_windows = False
                return True
            if result.returncode == 3221225477 or result.returncode == -1073741819:
                self._adb_blocked_by_windows = True
                self.logger.error(f'Ôøö ADB BLOQUEADO PELO WINDOWS (c├│digo {result.returncode})')
                return False
            self.logger.warning(f'ADB n├úo funcional - Return code: {result.returncode}')
            return False
        except subprocess.TimeoutExpired:
            self.logger.error(f'ADB timeout - Poss├¡vel travamento: {adb_path}')
            return False
        except FileNotFoundError:
            self.logger.error(f'ADB n├úo encontrado: {adb_path}')
            return False
        except Exception as e:
            self.logger.error(f'Erro ao testar ADB {adb_path}: {str(e)}')
            return False
    def _test_adb_responds(self, adb_path, timeout=3):
        try:
            if not os.path.isfile(adb_path):
                return False
            si = None
            cf = 0
            if platform.system() == 'Windows':
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                si.wShowWindow = subprocess.SW_HIDE
                cf = subprocess.CREATE_NO_WINDOW
            result = subprocess.run([adb_path, 'version'], capture_output=True, text=True, timeout=timeout, startupinfo=si, creationflags=cf)
            if result.returncode == 0 and 'Android Debug Bridge' in result.stdout:
                self._adb_blocked_by_windows = False
                return True
            if result.returncode == 3221225477 or result.returncode == -1073741819:
                self._adb_blocked_by_windows = True
                self.logger.error(f'Ôøö ADB BLOQUEADO PELO WINDOWS (c├│digo {result.returncode})')
                return False
            self.logger.warning(f'ADB retornou c├│digo {result.returncode}')
            return False
        except subprocess.TimeoutExpired:
            self.logger.warning(f'ÔÅ░ TIMEOUT: ADB em {adb_path} n├úo respondeu em {timeout}s - IGNORANDO')
            return False
        except OSError as e:
            if hasattr(e, 'winerror') and e.winerror == 3221225477:
                self.logger.error(f'ÔØî ERRO 0xc0000005: ADB em {adb_path} bloqueado por DEP!')
            return False
        except Exception as e:
            self.logger.debug(f'Erro ao testar ADB: {e}')
            return False
    def is_adb_blocked_by_windows(self):
        return getattr(self, '_adb_blocked_by_windows', False)
    def get_adb_blocked_message(self):
        return "O Windows bloqueou a ferramenta ADB.\n\nPara corrigir:\n1. Abra 'Seguran├ºa do Windows'\n2. V├í em 'Prote├º├úo contra v├¡rus e amea├ºas'\n3. Clique em 'Hist├│rico de prote├º├úo'\n4. Encontre 'adb.exe' e clique em 'Permitir'\n\nAp├│s liberar, reinicie o aplicativo."
    def _get_adb_version_number(self, adb_path):
        try:
            si = None
            cf = 0
            if platform.system() == 'Windows':
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                si.wShowWindow = subprocess.SW_HIDE
                cf = subprocess.CREATE_NO_WINDOW
            result = subprocess.run([adb_path, 'version'], capture_output=True, text=True, timeout=5, startupinfo=si, creationflags=cf)
            if result.returncode == 0:
                output = result.stdout
                match = re.search('Version\\s+(\\d+)\\.(\\d+)\\.(\\d+)', output)
                if match:
                    return int(match.group(1)), int(match.group(2)), int(match.group(3))
                match = re.search('version\\s+(\\d+)\\.(\\d+)\\.(\\d+)', output, re.IGNORECASE)
                if match:
                    return int(match.group(1)), int(match.group(2)), int(match.group(3))
                match = re.search('(\\d+)\\.(\\d+)\\.(\\d+)', output)
                if match:
                    return int(match.group(1)), int(match.group(2)), int(match.group(3))
        except Exception as e:
            self.logger.debug(f'Erro ao extrair vers├úo do ADB: {e}')
    def _is_adb_modern(self, adb_path):
        version = self._get_adb_version_number(adb_path)
        if not version:
            return False
        major, minor, patch = version
        if major >= 30:
            self.logger.info(f'Ô£à ADB vers├úo {major}.{minor}.{patch} - MODERNA')
            return True
        if major == 1 and minor == 0 and patch >= 40:
            self.logger.info(f'Ô£à ADB vers├úo {major}.{minor}.{patch} - ACEIT├üVEL')
            return True
        self.logger.warning(f'ÔÜá´©Å ADB vers├úo {major}.{minor}.{patch} - MUITO ANTIGA (m├¡nimo: 30.0.0 ou 1.0.40)')
        return False
    def _get_app_platform_tools_dir(self):
        try:
            from app.utils.path_manager import PathManager
            pm_dir = PathManager.get_platform_tools_dir()
            if pm_dir and os.path.isdir(pm_dir):
                return pm_dir
        except Exception:
            pass
        import sys
        is_frozen = getattr(sys, 'frozen', False)
        if is_frozen:
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        platform_tools_dir = os.path.join(base_dir, 'platform-tools')
        if not os.path.exists(platform_tools_dir):
            try:
                os.makedirs(platform_tools_dir, exist_ok=True)
            except Exception:
                platform_tools_dir = os.path.join(tempfile.gettempdir(), 'union_platform_tools')
                os.makedirs(platform_tools_dir, exist_ok=True)
            return platform_tools_dir
            return platform_tools_dir
        return platform_tools_dir
    def _download_adb_automatically(self):
        import zipfile
        import urllib.request
        import shutil
        self.logger.info('­ƒöä Iniciando download autom├ítico do ADB...')
        url = 'https://dl.google.com/android/repository/platform-tools-latest-windows.zip'
        platform_tools_dir = self._get_app_platform_tools_dir()
        adb_path = os.path.join(platform_tools_dir, 'adb.exe')
        if os.path.isfile(adb_path) and self._test_adb_responds(adb_path, timeout=3) and self._is_adb_modern(adb_path):
            self.logger.info(f'Ô£à ADB j├í existe e ├® moderno: {adb_path}')
            return adb_path
        try:
            temp_dir = tempfile.mkdtemp(prefix='union_adb_')
            zip_path = os.path.join(temp_dir, 'platform-tools.zip')
            self.logger.info(f'­ƒôÑ Baixando de {url}...')
            urllib.request.urlretrieve(url, zip_path)
            self.logger.info('­ƒôª Extraindo arquivos...')
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            extracted_dir = os.path.join(temp_dir, 'platform-tools')
            essential_files = ['adb.exe', 'AdbWinApi.dll', 'AdbWinUsbApi.dll', 'fastboot.exe']
            for file_name in essential_files:
                src = os.path.join(extracted_dir, file_name)
                dst = os.path.join(platform_tools_dir, file_name)
                if not os.path.isfile(src):
                    pass
                if os.path.isfile(dst):
                    os.remove(dst)
                shutil.copy2(src, dst)
                self.logger.info(f'  Ô£à {file_name} copiado')
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
            else:
                if os.path.isfile(adb_path):
                    if self._test_adb_responds(adb_path, timeout=3):
                        version = self._get_adb_version_number(adb_path)
                        if version:
                            self.logger.info(f'­ƒÄë ADB {version[0]}.{version[1]}.{version[2]} baixado e funcional!')
                        return adb_path
                    self.logger.error('ÔØî ADB baixado mas n├úo funciona')
                    return
                self.logger.error('ÔØî Falha ao extrair ADB')
        except Exception as e:
            self.logger.error(f'ÔØî Erro ao baixar ADB: {e}')
    def _ensure_adb_available(self):
        if self.adb_path and os.path.isfile(self.adb_path) and self._test_adb_responds(self.adb_path, timeout=3):
            if self._is_adb_modern(self.adb_path):
                return self.adb_path
            self.logger.warning('ÔÜá´©Å ADB atual ├® muito antigo - buscando alternativa...')
        app_adb = os.path.join(self._get_app_platform_tools_dir(), 'adb.exe')
        if os.path.isfile(app_adb) and self._test_adb_responds(app_adb, timeout=3) and self._is_adb_modern(app_adb):
            self.adb_path = app_adb
            return app_adb
        self.logger.info('­ƒöä Nenhum ADB moderno encontrado - iniciando download...')
        downloaded_adb = self._download_adb_automatically()
        if downloaded_adb:
            self.adb_path = downloaded_adb
            return downloaded_adb
    def test_fastboot_functionality(self, fastboot_path):
        try:
            if platform.system() == 'Windows':
                result = subprocess.run([fastboot_path, '--version'], capture_output=True, timeout=5, text=True, startupinfo=self.startupinfo, creationflags=self.creation_flags)
            else:
                result = subprocess.run([fastboot_path, '--version'], capture_output=True, timeout=5, text=True)
            if result.returncode == 0:
                if 'fastboot' in result.stdout.lower() or 'version' in result.stdout.lower():
                    self.logger.info(f'Fastboot funcional - Vers├úo: {result.stdout.strip()}')
                    return True
            self.logger.warning(f'Fastboot n├úo funcional - Return code: {result.returncode}')
            return False
        except subprocess.TimeoutExpired:
            self.logger.error(f'Fastboot timeout - Poss├¡vel travamento: {fastboot_path}')
            return False
        except FileNotFoundError:
            self.logger.error(f'Fastboot n├úo encontrado: {fastboot_path}')
            return False
        except Exception as e:
            self.logger.error(f'Erro ao testar Fastboot {fastboot_path}: {str(e)}')
            return False
    def diagnose_adb_issues(self):
        report = []
        report.append('­ƒöì === DIAGN├ôSTICO DETALHADO ADB/FASTBOOT ===')
        report.append(f'Sistema: {platform.system()} {platform.release()}')
        report.append(f'Arquitetura: {platform.architecture()}')
        report.append(f'Execut├ível congelado: {getattr(sys, 'frozen', False)}')
        is_frozen = getattr(sys, 'frozen', False)
        if is_frozen:
            base_dir = os.path.dirname(sys.executable)
            report.append(f'Diret├│rio base: {base_dir}')
            adb_name = 'adb.exe' if platform.system() == 'Windows' else 'adb'
            fastboot_name = 'fastboot.exe' if platform.system() == 'Windows' else 'fastboot'
            possible_adb_paths = [os.path.join(base_dir, 'platform-tools', adb_name), os.path.join(base_dir, '_internal', 'platform-tools', adb_name), os.path.join(base_dir, 'app', 'database', 'platform-tools', adb_name), os.path.join(base_dir, 'database', 'platform-tools', adb_name), os.path.join(base_dir, adb_name)]
            possible_fastboot_paths = [os.path.join(base_dir, 'platform-tools', fastboot_name), os.path.join(base_dir, '_internal', 'platform-tools', fastboot_name), os.path.join(base_dir, 'app', 'database', 'platform-tools', fastboot_name), os.path.join(base_dir, 'database', 'platform-tools', fastboot_name), os.path.join(base_dir, fastboot_name)]
            report.append('\n­ƒôü VERIFICA├ç├âO DE CAMINHOS ADB:')
            for i, path in enumerate(possible_adb_paths, 1):
                if os.path.exists(path):
                    if self.test_adb_functionality(path):
                        report.append(f'  {i}. Ô£à FUNCIONAL: {path}')
                    else:
                        report.append(f'  {i}. ÔÜá´©Å  ENCONTRADO MAS N├âO FUNCIONAL: {path}')
                else:
                    report.append(f'  {i}. ÔØî N├âO ENCONTRADO: {path}')
            report.append('\n­ƒôü VERIFICA├ç├âO DE CAMINHOS FASTBOOT:')
            for i, path in enumerate(possible_fastboot_paths, 1):
                if os.path.exists(path):
                    if self.test_fastboot_functionality(path):
                        report.append(f'  {i}. Ô£à FUNCIONAL: {path}')
                    else:
                        report.append(f'  {i}. ÔÜá´©Å  ENCONTRADO MAS N├âO FUNCIONAL: {path}')
                else:
                    report.append(f'  {i}. ÔØî N├âO ENCONTRADO: {path}')
            report.append('\n­ƒôé CONTE├ÜDO DOS DIRET├ôRIOS:')
            dirs_to_check = [os.path.join(base_dir, 'platform-tools'), os.path.join(base_dir, '_internal', 'platform-tools'), os.path.join(base_dir, 'app', 'database', 'platform-tools')]
            for dir_path in dirs_to_check:
                if os.path.exists(dir_path):
                    try:
                        contents = os.listdir(dir_path)
                        report.append(f'  ­ƒôü {dir_path}:')
                        for file in contents:
                            file_path = os.path.join(dir_path, file)
                            size = os.path.getsize(file_path) if os.path.isfile(file_path) else 'DIR'
                            report.append(f'    - {file} ({size} bytes)')
                    except Exception as e:
                        report.append(f'  ÔØî Erro ao listar {dir_path}: {e}')
                        continue
                else:
                    report.append(f'  ÔØî Diret├│rio n├úo existe: {dir_path}')
        report.append('\n­ƒöì VERIFICA├ç├âO NO PATH DO SISTEMA:')
        try:
            if platform.system() == 'Windows':
                result = subprocess.run(['where', 'adb'], capture_output=True, text=True, timeout=5)
            else:
                result = subprocess.run(['which', 'adb'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                system_adb = result.stdout.strip()
                report.append(f'  Ô£à ADB encontrado no PATH: {system_adb}')
            else:
                report.append('  ÔØî ADB n├úo encontrado no PATH do sistema')
        except Exception as e:
            report.append(f'  ÔÜá´©Å  Erro ao verificar PATH: {e}')
        report.append('\n­ƒÄ» STATUS ATUAL:')
        report.append(f'  ADB Path: {self.adb_path if self.adb_path else 'N├âO DEFINIDO'}')
        report.append(f'  Fastboot Path: {self.fastboot_path if self.fastboot_path else 'N├âO DEFINIDO'}')
        return '\n'.join(report)
    def find_binary_paths(self):
        try:
            is_frozen = getattr(sys, 'frozen', False)
            self.logger.info(f'Procurando bin├írios ADB e Fastboot (frozen={is_frozen})')
            self.adb_path = None
            self.fastboot_path = None
            self.adb_path = self.find_adb_path()
            self.logger.info(f'Caminho ADB encontrado: {self.adb_path}')
            self.fastboot_path = self.find_fastboot_path()
            self.logger.info(f'Caminho Fastboot encontrado: {self.fastboot_path}')
            if not self.adb_path:
                self.logger.error('ADB n├úo encontrado no sistema')
            else:
                self.logger.info(f'ADB encontrado: {self.adb_path}')
            if not self.fastboot_path:
                self.logger.error('Fastboot n├úo encontrado no sistema')
            else:
                self.logger.info(f'Fastboot encontrado: {self.fastboot_path}')
            return self.adb_path is not None and self.fastboot_path is not None
        except Exception as e:
            self.logger.error(f'Erro ao inicializar ADBManager: {str(e)}')
            return False
    def _resolve_protected_adb(self, adb_name):
        try:
            from app.utils.unlock_tools_manager import get_unlock_tools_manager
            _mgr = get_unlock_tools_manager()
            _candidate = os.path.join(_mgr.get_tools_dir(), adb_name)
            if os.path.isfile(_candidate):
                _dir = os.path.dirname(_candidate)
                _files = {f.lower() for f in os.listdir(_dir)} if os.path.isdir(_dir) else set()
                if 'adbwinapi.dll' in _files and 'adbwinusbapi.dll' in _files:
                    self.logger.info('ADB resolvido via recurso protegido')
                    return _candidate
        except ImportError:
            return
        except Exception:
            self.logger.debug('Recurso protegido indisponivel')
        if _mgr.zip_disponivel() and not _mgr.ja_extraido():
            _ok, _ = _mgr.extrair()
            if _ok and os.path.isfile(_candidate):
                self.logger.info('ADB obtido de recurso protegido')
                return _candidate
    def find_adb_path(self):
        self.logger.info('Procurando ADB...')
        import sys
        import os
        import platform
        import subprocess
        import stat
        adb_name = 'adb.exe' if platform.system() == 'Windows' else 'adb'
        _protected = self._resolve_protected_adb(adb_name)
        if _protected:
            return _protected
        is_frozen = getattr(sys, 'frozen', False)
        if is_frozen:
            base_dir = os.path.dirname(sys.executable)
            self.logger.info(f'Executando a partir de execut├ível congelado. Base dir: {base_dir}')
            app_adb_paths = [os.path.join(base_dir, 'platform-tools', adb_name), os.path.join(base_dir, '_internal', 'platform-tools', adb_name)]
            for path in app_adb_paths:
                if os.path.isfile(path):
                    self.logger.info(f'Ô£à PRIORIDADE 1: ADB do aplicativo encontrado: {path}')
                    return path
            if platform.system() == 'Windows':
                try:
                    si = subprocess.STARTUPINFO()
                    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    si.wShowWindow = subprocess.SW_HIDE
                    which_result = subprocess.run(['where', 'adb'], capture_output=True, text=True, check=False, timeout=5, startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
                    if which_result.returncode == 0:
                        paths_from_path = which_result.stdout.strip().split('\n')
                        for path in paths_from_path:
                            path = path.strip()
                            if not path:
                                continue
                            if '\\Windows\\' in path:
                                continue
                            if os.path.isfile(path):
                                self.logger.info(f'Ô£à PRIORIDADE 2: ADB do PATH encontrado: {path}')
                                return path
                except Exception as e:
                    self.logger.debug(f'Busca no PATH falhou: {e}')
            external_adb = os.path.join('C:\\', 'platform-tools', adb_name)
            if os.path.isfile(external_adb):
                self.logger.warning(f'ÔÜá´©Å PRIORIDADE 3: ADB externo encontrado: {external_adb}')
                return external_adb
            self.logger.info('­ƒöä Nenhum ADB moderno encontrado - iniciando download autom├ítico...')
            downloaded_adb = self._download_adb_automatically()
            if downloaded_adb and os.path.isfile(downloaded_adb):
                self.logger.info(f'­ƒÄë ADB baixado automaticamente: {downloaded_adb}')
                return downloaded_adb
            self.logger.error('ÔØî Nenhum ADB funcional encontrado!')
            self.logger.error('Tentamos:')
            self.logger.error(f'  1. ADB do aplicativo em {base_dir}\\platform-tools')
            self.logger.error('  2. ADB do PATH do Windows')
            self.logger.error('  3. ADB externo em C:\\platform-tools')
            self.logger.error('  4. Download autom├ítico do Google')
            platform_tools_dir = os.path.join(base_dir, 'platform-tools')
            if os.path.exists(platform_tools_dir):
                self.logger.info(f'Conte├║do de platform-tools: {os.listdir(platform_tools_dir)}')
                return
            return
        common_paths = []
        is_frozen = getattr(sys, 'frozen', False)
        base_path = sys._MEIPASS if is_frozen else os.path.dirname(os.path.abspath(__file__))
        if platform.system() == 'Windows':
            windows_platform_tools = os.path.join('C:\\', 'platform-tools', adb_name)
            if os.path.isfile(windows_platform_tools):
                self.logger.info(f'Ô£à ADB encontrado em C:\\platform-tools: {windows_platform_tools}')
                return windows_platform_tools
        if is_frozen:
            common_paths.extend([os.path.join(base_path, 'bin', 'platform-tools', adb_name), os.path.join(base_path, 'platform-tools', adb_name), os.path.join(base_path, 'tools', adb_name), os.path.join(base_path, 'adb', adb_name), os.path.join(base_path, adb_name)])
        if platform.system() == 'Windows':
            common_paths.extend([os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'resources', 'platform-tools', adb_name), os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'bin', 'platform-tools', adb_name), os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'platform-tools', adb_name), os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'resources', 'platform-tools', adb_name), os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'bin', 'platform-tools', adb_name), os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'platform-tools', adb_name), os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Android', 'Sdk', 'platform-tools', adb_name), os.path.join(os.environ.get('PROGRAMFILES', ''), 'Android', 'android-sdk', 'platform-tools', adb_name), os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Android', 'android-sdk', 'platform-tools', adb_name), os.path.join(os.environ.get('APPDATA', ''), 'Local', 'Android', 'Sdk', 'platform-tools', adb_name), os.path.join(os.environ.get('USERPROFILE', ''), 'AppData', 'Local', 'Android', 'Sdk', 'platform-tools', adb_name)])
            try:
                which_result = subprocess.run(['where', 'adb'], capture_output=True, text=True, check=False, startupinfo=self.startupinfo, creationflags=self.creation_flags)
                if which_result.returncode == 0:
                    paths_from_which = which_result.stdout.strip().split('\n')
                    common_paths.extend([p.strip() for p in paths_from_which if p.strip()])
                    self.logger.debug(f'ADB encontrado no PATH: {paths_from_which}')
            except Exception as e:
                self.logger.debug(f'Erro ao procurar ADB no PATH: {str(e)}')
        else:
            common_paths.extend([os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'resources', 'platform-tools', adb_name), os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'bin', 'platform-tools', adb_name), os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'platform-tools', adb_name), os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'resources', 'platform-tools', adb_name), os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'bin', 'platform-tools', adb_name), os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'platform-tools', adb_name), os.path.join(os.path.expanduser('~'), 'Android', 'Sdk', 'platform-tools', adb_name), os.path.join('/', 'usr', 'local', 'bin', adb_name), os.path.join('/', 'usr', 'bin', adb_name), os.path.join('/', 'opt', 'android-sdk', 'platform-tools', adb_name), os.path.join('/', 'opt', 'android-studio', 'sdk', 'platform-tools', adb_name)])
            try:
                which_result = subprocess.run(['which', 'adb'], capture_output=True, text=True, check=False)
                if which_result.returncode == 0:
                    path_from_which = which_result.stdout.strip()
                    if path_from_which:
                        common_paths.append(path_from_which)
                        self.logger.debug(f'ADB encontrado no PATH: {path_from_which}')
            except Exception as e:
                self.logger.debug(f'Erro ao procurar ADB no PATH: {str(e)}')
        for path in common_paths:
            if os.path.isfile(path):
                self.logger.info(f'Ô£à ADB encontrado em: {path}')
                return path
        self.logger.info('­ƒöä Nenhum ADB encontrado - tentando download autom├ítico...')
        downloaded_adb = self._download_adb_automatically()
        if downloaded_adb and os.path.isfile(downloaded_adb):
            self.logger.info(f'­ƒÄë ADB baixado automaticamente: {downloaded_adb}')
            return downloaded_adb
        self.logger.warning('ADB n├úo encontrado ou nenhum funcional')
    def find_fastboot_path(self):
        self.logger.info('Procurando fastboot...')
        fastboot_name = 'fastboot.exe' if platform.system() == 'Windows' else 'fastboot'
        is_frozen = getattr(sys, 'frozen', False)
        if is_frozen:
            base_dir = os.path.dirname(sys.executable)
            self.logger.info(f'Executando a partir de execut├ível congelado. Base dir: {base_dir}')
            if platform.system() == 'Windows':
                windows_platform_tools = os.path.join('C:\\', 'platform-tools', fastboot_name)
                if os.path.isfile(windows_platform_tools):
                    self.logger.info(f'Ô£à Fastboot encontrado em C:\\platform-tools: {windows_platform_tools}')
                    return windows_platform_tools
            possible_paths = [os.path.join(base_dir, 'platform-tools', fastboot_name), os.path.join(base_dir, '_internal', 'platform-tools', fastboot_name)]
            for path in possible_paths:
                if os.path.isfile(path):
                    self.logger.info(f'Ô£à Fastboot encontrado em: {path}')
                    return path
            self.logger.error('Fastboot n├úo encontrado nos caminhos esperados ap├│s compila├º├úo')
            self.logger.error(f'Caminhos verificados: {possible_paths}')
        else:
            if platform.system() == 'Windows':
                windows_platform_tools = os.path.join('C:\\', 'platform-tools', fastboot_name)
                if os.path.isfile(windows_platform_tools):
                    self.logger.info(f'Ô£à Fastboot encontrado em C:\\platform-tools: {windows_platform_tools}')
                    return windows_platform_tools
            database_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'database', 'platform-tools', fastboot_name)
            self.logger.debug(f'Procurando fastboot em: {database_path}')
            if os.path.isfile(database_path):
                self.logger.info(f'Ô£à Fastboot encontrado em: {database_path}')
                return database_path
        common_paths = []
        is_frozen = getattr(sys, 'frozen', False)
        base_path = sys._MEIPASS if is_frozen else os.path.dirname(os.path.abspath(__file__))
        if is_frozen:
            common_paths.extend([os.path.join(base_path, 'bin', 'platform-tools', fastboot_name), os.path.join(base_path, 'platform-tools', fastboot_name), os.path.join(base_path, 'tools', fastboot_name), os.path.join(base_path, 'fastboot', fastboot_name), os.path.join(base_path, fastboot_name)])
        if platform.system() == 'Windows':
            common_paths.extend([os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'resources', 'platform-tools', fastboot_name), os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'bin', 'platform-tools', fastboot_name), os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'platform-tools', fastboot_name), os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'resources', 'platform-tools', fastboot_name), os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'bin', 'platform-tools', fastboot_name), os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'platform-tools', fastboot_name), os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Android', 'Sdk', 'platform-tools', fastboot_name), os.path.join(os.environ.get('PROGRAMFILES', ''), 'Android', 'android-sdk', 'platform-tools', fastboot_name), os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Android', 'android-sdk', 'platform-tools', fastboot_name), os.path.join(os.environ.get('APPDATA', ''), 'Local', 'Android', 'Sdk', 'platform-tools', fastboot_name), os.path.join(os.environ.get('USERPROFILE', ''), 'AppData', 'Local', 'Android', 'Sdk', 'platform-tools', fastboot_name)])
            try:
                which_result = subprocess.run(['where', 'fastboot'], capture_output=True, text=True, check=False, startupinfo=self.startupinfo, creationflags=self.creation_flags)
                if which_result.returncode == 0:
                    paths_from_which = which_result.stdout.strip().split('\n')
                    common_paths.extend([p.strip() for p in paths_from_which if p.strip()])
                    self.logger.debug(f'Fastboot encontrado no PATH: {paths_from_which}')
            except Exception as e:
                self.logger.debug(f'Erro ao procurar Fastboot no PATH: {str(e)}')
        else:
            common_paths.extend([os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'resources', 'platform-tools', fastboot_name), os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'bin', 'platform-tools', fastboot_name), os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'platform-tools', fastboot_name), os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'resources', 'platform-tools', fastboot_name), os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'bin', 'platform-tools', fastboot_name), os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'platform-tools', fastboot_name), os.path.join(os.path.expanduser('~'), 'Android', 'Sdk', 'platform-tools', fastboot_name), os.path.join('/', 'usr', 'local', 'bin', fastboot_name), os.path.join('/', 'usr', 'bin', fastboot_name), os.path.join('/', 'opt', 'android-sdk', 'platform-tools', fastboot_name), os.path.join('/', 'opt', 'android-studio', 'sdk', 'platform-tools', fastboot_name)])
            try:
                if platform.system() == 'Windows':
                    which_result = subprocess.run(['where', 'fastboot'], capture_output=True, text=True, check=False, startupinfo=self.startupinfo, creationflags=self.creation_flags)
                else:
                    which_result = subprocess.run(['which', 'fastboot'], capture_output=True, text=True, check=False)
                if which_result.returncode == 0:
                    path_from_which = which_result.stdout.strip()
                    if path_from_which:
                        common_paths.append(path_from_which)
                        self.logger.debug(f'Fastboot encontrado no PATH: {path_from_which}')
            except Exception as e:
                self.logger.debug(f'Erro ao procurar Fastboot no PATH: {str(e)}')
        for path in common_paths:
            if os.path.isfile(path):
                self.logger.info(f'Fastboot encontrado em: {path}')
                if platform.system() != 'Windows':
                    try:
                        current_permissions = os.stat(path).st_mode
                        os.chmod(path, current_permissions | stat.S_IXUSR)
                    except Exception as e:
                        self.logger.warning(f'N├úo foi poss├¡vel definir permiss├úo de execu├º├úo para {path}: {str(e)}')
                    return path
                return path
        self.logger.warning('Fastboot n├úo encontrado')
    def execute_adb_command(self, command, timeout=30, shell=False, background=False):
        if not self.adb_path:
            self.adb_path = self.find_adb_path()
            if not self.adb_path:
                raise Exception('ADB n├úo encontrado. Verifique se o Android SDK est├í instalado corretamente.')
        if not os.path.isfile(self.adb_path):
            self.logger.error(f'ADB n├úo encontrado no caminho configurado: {os.path.basename(self.adb_path)}')
            raise Exception('ADB n├úo encontrado. Verifique se o arquivo est├í acess├¡vel ou reinstale o sistema.')
        if isinstance(command, str):
            command_parts = command.split()
        else:
            command_parts = command
        _GLOBAL_COMMANDS = {'connect', 'devices', 'version', 'disconnect', 'kill-server', 'start-server'}
        if self.selected_serial and command_parts and command_parts[0] not in _GLOBAL_COMMANDS:
            cmd_list = [self.adb_path, '-s', self.selected_serial] + command_parts
        else:
            cmd_list = [self.adb_path] + command_parts
        adb_name = os.path.basename(self.adb_path)
        cmd_str_log = f'{adb_name} {' '.join(command_parts)}'
        self.logger.debug(f'Executando comando ADB: {cmd_str_log}')
        try:
            if background:
                adb_dir = os.path.dirname(self.adb_path)
                if platform.system() == 'Windows':
                    process = subprocess.Popen(cmd_list, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=adb_dir, startupinfo=self.startupinfo, creationflags=self.creation_flags)
                else:
                    process = subprocess.Popen(cmd_list, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=adb_dir)
                with self.lock:
                    process.start_time = time.time()
                    self.active_processes.append(process)
                return process
            if platform.system() == 'Windows':
                process = subprocess.run(cmd_list, shell=False, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=timeout, cwd=os.path.dirname(self.adb_path), startupinfo=self.startupinfo, creationflags=self.creation_flags)
            else:
                process = subprocess.run(cmd_list, shell=False, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=timeout)
            if process.returncode != 0:
                error = process.stderr.strip() if process.stderr else ''
                self.logger.error(f'Erro ADB: {error}')
                if 'device unauthorized' in error or 'device offline' in error:
                    raise Exception('Dispositivo n├úo autorizado ou offline. Verifique a confirma├º├úo de depura├º├úo USB.')
                if 'device not found' in error or 'no devices/emulators found' in error:
                    raise Exception('Nenhum dispositivo conectado. Conecte um dispositivo Android.')
                raise Exception(f'Erro ao executar comando ADB: {error}')
            if process.stdout:
                return process.stdout.strip()
        except subprocess.TimeoutExpired:
            self.logger.error(f'Timeout ao executar comando ADB: {cmd_str_log}')
            raise Exception('Timeout ao executar comando ADB. O dispositivo pode estar ocupado ou n├úo respondendo.')
        except OSError as e:
            if hasattr(e, 'winerror'):
                if e.winerror == 3221225477:
                    pass
            self.logger.error(f'Erro de Access Violation (0xc0000005) ao executar ADB: {cmd_str_log}')
            raise Exception('Erro cr├¡tico ao executar ADB. Verifique se o arquivo n├úo est├í corrompido ou bloqueado por antiv├¡rus.')
            self.logger.error(f'Erro de sistema ao executar comando ADB: {str(e)}')
            raise Exception('Erro ao executar comando ADB. Verifique a conex├úo com o dispositivo.')
        except Exception as e:
            self.logger.error(f'Erro ao executar comando ADB: {str(e)}')
            raise
        return ''
    def execute_fastboot_command(self, command, timeout=30):
        if not self.fastboot_path:
            self.fastboot_path = self.find_fastboot_path()
            if not self.fastboot_path:
                raise Exception('Fastboot n├úo encontrado. Verifique se o Android SDK est├í instalado corretamente.')
        if not os.path.isfile(self.fastboot_path):
            self.logger.error(f'Fastboot n├úo encontrado no caminho configurado: {os.path.basename(self.fastboot_path)}')
            raise Exception('Fastboot n├úo encontrado. Verifique se o arquivo est├í acess├¡vel ou reinstale o sistema.')
        if isinstance(command, str):
            command_parts = command.split()
        else:
            command_parts = command
        cmd_list = [self.fastboot_path] + command_parts
        fastboot_name = os.path.basename(self.fastboot_path)
        cmd_str_log = f'{fastboot_name} {' '.join(command_parts)}'
        self.logger.debug(f'Executando comando Fastboot: {cmd_str_log}')
        try:
            fastboot_dir = os.path.dirname(self.fastboot_path)
            if platform.system() == 'Windows':
                process = subprocess.run(cmd_list, shell=False, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=timeout, cwd=fastboot_dir, startupinfo=self.startupinfo, creationflags=self.creation_flags)
            else:
                process = subprocess.run(cmd_list, shell=False, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=timeout, cwd=fastboot_dir)
            output = process.stdout.strip() if process.stdout else ''
            error = process.stderr.strip() if process.stderr else ''
            combined = output + '\n' + error if error else output
            is_getvar = len(command_parts) > 0 and command_parts[0] == 'getvar'
            if is_getvar:
                if error and not output:
                    if ':' in error or 'finished' in error.lower():
                        return error.strip()
                if output:
                    return output.strip()
                return ''
            if process.returncode != 0:
                if any((ignore in error.lower() for ignore in ('getvar variable not found', 'unknown variable'))):
                    return ''
                self.logger.error(f'Erro Fastboot: {error}')
                raise Exception(f'Erro ao executar comando Fastboot: {error}')
            return output
        except subprocess.TimeoutExpired:
            self.logger.error(f'Timeout ao executar comando Fastboot: {cmd_str_log}')
            raise Exception('Timeout ao executar comando Fastboot. O dispositivo pode estar ocupado ou n├úo respondendo.')
        except OSError as e:
            self.logger.error(f'Erro de sistema ao executar comando Fastboot: {str(e)}')
            raise Exception('Erro ao executar comando Fastboot. Verifique a conex├úo com o dispositivo.')
        except Exception as e:
            self.logger.error(f'Erro ao executar comando Fastboot: {str(e)}')
            raise
    def _run_fastboot_command(self, command_list, capture_output=True):
        if isinstance(command_list, list):
            if command_list[0] == self.fastboot_path:
                command_list = command_list[1:]
            command = ' '.join(command_list)
        else:
            command = command_list
        return self.execute_fastboot_command(command)
    def is_device_connected(self):
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                devices = self.execute_adb_command('devices', timeout=5)
                lines = devices.split('\n')
                self.logger.debug(f'Sa├¡da do ADB devices: {devices}')
                for line in lines:
                    line = line.strip()
                    if line.startswith('List of devices') or line.startswith('*'):
                        continue
                    if '\tdevice' in line or ' device' in line:
                        self.logger.debug(f'Dispositivo encontrado: {line}')
                        return True
                        return False
                        return False
            except Exception as e:
                error_msg = str(e).lower()
                self.logger.error(f'Erro ao verificar dispositivo (tentativa {attempt + 1}): {str(e)}')
                if attempt == 0:
                    if any((x in error_msg for x in ('timeout', 'protocol fault', 'connection reset', 'failed to check server'))):
                        self.logger.info('­ƒöä Reiniciando servidor ADB automaticamente...')
                        try:
                            self._restart_adb_server()
                            self.logger.info('Ô£à Servidor ADB reiniciado! Tentando novamente...')
                        except Exception as restart_error:
                            self.logger.error(f'Erro ao reiniciar servidor ADB: {str(restart_error)}')
                            e = None
                            del e
                            return False
                continue
    def _restart_adb_server(self):
        if not self.adb_path:
            self.adb_path = self.find_adb_path()
        if not self.adb_path:
            raise Exception('ADB n├úo encontrado')
        adb_dir = os.path.dirname(self.adb_path)
        try:
            subprocess.run([self.adb_path, 'kill-server'], capture_output=True, timeout=5, cwd=adb_dir, startupinfo=self.startupinfo, creationflags=self.creation_flags)
        except Exception:
            pass
        import time
        time.sleep(0.5)
        result = subprocess.run([self.adb_path, 'start-server'], capture_output=True, timeout=10, cwd=adb_dir, startupinfo=self.startupinfo, creationflags=self.creation_flags)
        if result.returncode != 0:
            stderr = result.stderr.decode('utf-8', errors='ignore') if result.stderr else ''
            raise Exception(f'Falha ao iniciar servidor ADB: {stderr}')
    def get_device_serial(self):
        try:
            devices = self.execute_adb_command('devices', timeout=5)
            lines = devices.split('\n')
        except Exception as e:
            self.logger.error(f'Erro ao obter serial do dispositivo: {str(e)}')
        try:
            connected_devices = [line.split('\t')[0] for line in lines if '\tdevice' in line]
            if not connected_devices:
                return
            return connected_devices[0]
        except Exception as e:
            self.logger.error(f'Erro ao obter serial do dispositivo: {str(e)}')
    def get_connected_devices(self):
        devices = []
        try:
            output = self.execute_adb_command('devices', timeout=5)
            for line in output.split('\n'):
                line = line.strip()
                if line:
                    if line.startswith('List of devices') or line.startswith('*'):
                        continue
                    if '\tdevice' in line:
                        serial = line.split('\t')[0].strip()
                        if serial:
                            model = self._get_device_model_by_serial(serial)
                            devices.append({'serial': serial, 'status': 'device', 'model': model})
        except Exception as e:
            self.logger.error(f'Erro ao listar dispositivos: {str(e)}')
        return devices
    def _get_device_model_by_serial(self, serial):
        try:
            if not self.adb_path:
                self.adb_path = self.find_adb_path()
            if not self.adb_path:
                return serial
            adb_dir = os.path.dirname(self.adb_path)
            if platform.system() == 'Windows':
                result = subprocess.run([self.adb_path, '-s', serial, 'shell', 'getprop', 'ro.product.model'], capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=5, cwd=adb_dir, startupinfo=self.startupinfo, creationflags=self.creation_flags)
            else:
                result = subprocess.run([self.adb_path, '-s', serial, 'shell', 'getprop', 'ro.product.model'], capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=5)
            model = result.stdout.strip()
            if model:
                return model
            return serial
        except Exception:
            return serial
    def set_selected_device(self, serial):
        self.selected_serial = serial
        if serial:
            self.logger.info(f'Dispositivo selecionado: {serial}')
            return
        self.logger.info('Sele├º├úo de dispositivo removida (modo autom├ítico)')
    def reboot_device(self, mode=None):
        command = 'reboot'
        if mode:
            command += f' {mode}'
        try:
            return self.execute_adb_command(command)
        except Exception as e:
            self.logger.error(f'Erro ao reiniciar dispositivo: {str(e)}')
            raise
    def cleanup_processes(self):
        with self.lock:
            current_time = time.time()
            recent_operations = []
            for process in self.active_processes:
                if process.poll() is not None:
                    continue
                if not hasattr(process, 'start_time'):
                    continue
                if current_time - process.start_time < 30:
                    recent_operations.append(process)
            if recent_operations:
                self.logger.warning(f'Cleanup adiado: {len(recent_operations)} opera├º├úo(├Áes) cr├¡tica(s) detectada(s)')
                return
            for process in self.active_processes:
                try:
                    if process.poll() is None:
                        process.terminate()
                        time.sleep(0.2)
                        if process.poll() is None:
                            process.kill()
                except Exception as e:
                    self.logger.error(f'Erro ao encerrar processo: {str(e)}')
                    continue
            self.active_processes.clear()
    def force_cleanup_processes(self):
        with self.lock:
            for process in self.active_processes:
                try:
                    if process.poll() is None:
                        process.terminate()
                        time.sleep(0.2)
                        if process.poll() is None:
                            process.kill()
                except Exception as e:
                    self.logger.error(f'Erro ao encerrar processo: {str(e)}')
                    continue
            self.active_processes.clear()
    def terminate_process(self, process):
        if not process:
            return
        with self.lock:
            try:
                if process in self.active_processes:
                    if process.poll() is None:
                        process.terminate()
                        time.sleep(0.2)
                        if process.poll() is None:
                            process.kill()
                    self.active_processes.remove(process)
                return
            except Exception as e:
                self.logger.error(f'Erro ao encerrar processo: {str(e)}')
    def kill_server(self):
        try:
            return self.execute_adb_command('kill-server')
        except Exception as e:
            self.logger.error(f'Erro ao matar servidor ADB: {str(e)}')
    def start_server(self):
        try:
            return self.execute_adb_command('start-server')
        except Exception as e:
            self.logger.error(f'Erro ao iniciar servidor ADB: {str(e)}')
    def restart_server(self):
        self.kill_server()
        time.sleep(1)
        return self.start_server()
    def _cleanup_on_exit(self):
        try:
            if platform.system() != 'Windows':
                return
            if self.adb_path and os.path.exists(self.adb_path):
                pass
            try:
                subprocess.run([self.adb_path, 'kill-server'], timeout=3, capture_output=True, startupinfo=self.startupinfo, creationflags=self.creation_flags)
            except:
                pass
            else:
                time.sleep(1)
        except:
            return
        try:
            subprocess.run(['taskkill', '/F', '/IM', 'adb.exe'], timeout=3, capture_output=True, startupinfo=self.startupinfo, creationflags=self.creation_flags)
        except:
            pass
        try:
            subprocess.run(['wmic', 'process', 'where', "name='adb.exe'", 'delete'], timeout=3, capture_output=True, startupinfo=self.startupinfo, creationflags=self.creation_flags)
        except:
            pass
        time.sleep(1)
    def finalize_adb_operation(self):
        if platform.system() != 'Windows':
            return
        try:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            subprocess.run(['taskkill', '/F', '/IM', 'adb.exe'], capture_output=True, timeout=3, startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
            return
        except:
            return
    def reset_adb_complete(self):
        try:
            self.logger.info('=== RESET COMPLETO DO ADB ===')
            if platform.system() == 'Windows':
                pass
            try:
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                si.wShowWindow = subprocess.SW_HIDE
                subprocess.run(['taskkill', '/F', '/IM', 'adb.exe'], capture_output=True, timeout=5, startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
                self.logger.info('Ô£à Processos ADB finalizados')
                time.sleep(1)
            except Exception as e:
                self.logger.debug(f'Kill ADB: {e}')
            else:
                self.force_cleanup_processes()
                self.adb_path = None
                self.fastboot_path = None
                self.adb_path = self.find_adb_path()
                self.fastboot_path = self.find_fastboot_path()
                if self.adb_path and os.path.isfile(self.adb_path):
                    pass
        except Exception as e:
            error_msg = f'ÔØî Erro ao resetar ADB: {str(e)}'
            self.logger.error(error_msg)
            return error_msg
        msg = 'Ô£à ADB resetado com sucesso!\n\n'
        if self.adb_path:
            msg += f'ADB: {self.adb_path}\n'
        else:
            msg += 'ÔÜá´©Å ADB n├úo encontrado no sistema\n'
        if self.fastboot_path:
            msg += f'Fastboot: {self.fastboot_path}'
            return msg
        try:
            msg += 'ÔÜá´©Å Fastboot n├úo encontrado'
        except Exception as e:
            error_msg = f'ÔØî Erro ao resetar ADB: {str(e)}'
            self.logger.error(error_msg)
            return error_msg
        return msg
    def get_device_states_detailed(self):
        try:
            out = self.execute_adb_command('devices -l', timeout=5) or ''
        except Exception as exc:
            self.logger.debug(f'states_detailed indisponivel: {exc}')
            return []
        return _parse_devices_long_output(out)
    def force_reconnect_offline(self):
        try:
            self.execute_adb_command('reconnect offline', timeout=5)
            return (True, "Solicitacao de autorizacao reenviada. Olhe a tela do aparelho e toque em 'Permitir'.")
        except Exception as exc:
            self.logger.debug(f'reconnect offline falhou: {exc}')
            return (False, 'Nao foi possivel reenviar a solicitacao agora. Tente reiniciar a conexao ADB.')
    def regenerate_adb_keys(self):
        try:
            home = os.path.expanduser('~')
            android_dir = os.path.join(home, '.android')
            removidos = 0
            for nome in ('adbkey', 'adbkey.pub'):
                alvo = os.path.join(android_dir, nome)
            try:
                if os.path.isfile(alvo):
                    os.remove(alvo)
                    removidos += 1
            except OSError as exc:
                self.logger.debug(f'falha ao remover {nome}: {exc}')
        except Exception as exc:
            self.logger.debug(f'regenerate_adb_keys falhou: {exc}')
            return (False, 'Nao foi possivel preparar a nova autorizacao. Reinicie o aplicativo e tente novamente.')
        try:
            self.reset_adb_complete()
        except Exception as exc:
            self.logger.debug(f'reset apos regen falhou: {exc}')
            try:
                return (False, 'Foi possivel preparar o aparelho, porem o servico nao reiniciou. Reinicie o aplicativo.')
            except Exception as exc:
                self.logger.debug(f'regenerate_adb_keys falhou: {exc}')
                return (False, 'Nao foi possivel preparar a nova autorizacao. Reinicie o aplicativo e tente novamente.')
        return (True, 'Chaves de autorizacao regeneradas com sucesso. Olhe o aparelho ÔÇö o pedido de permissao vai aparecer agora.')
    def aguardar_autorizacao(self, max_tentativas: int=8, intervalo: int=2, progress_cb=None) -> bool:
        try:
            if progress_cb:
                progress_cb('Dispositivo detectado ÔÇö forcando autorizacao...')
            for i in range(max_tentativas):
                pass
            try:
                self._restart_adb_server()
            except Exception:
                pass
            else:
                import time
                time.sleep(intervalo)
        except Exception:
            pass
        return False
    def __del__(self):
        self.cleanup_processes()
    def check_device(self):
        max_attempts = 2
        if not self.adb_path:
            self.adb_path = self.find_adb_path()
            if not self.adb_path:
                raise Exception('ADB n├úo encontrado. Verifique se est├í instalado em C:\\platform-tools ou no PATH do sistema.')
        if not os.path.isfile(self.adb_path):
            self.logger.error(f'ADB n├úo encontrado no caminho: {self.adb_path}')
            raise Exception('ADB n├úo encontrado. Verifique se o arquivo est├í acess├¡vel.')
        for attempt in range(max_attempts):
            try:
                result = subprocess.run([self.adb_path, 'devices'], cwd=os.path.dirname(self.adb_path), startupinfo=self.startupinfo, creationflags=self.creation_flags, capture_output=True, text=True, timeout=10)
                if result.returncode != 0:
                    error_msg = result.stderr.strip() if result.stderr else f'Exit code: {result.returncode}'
                    self.logger.error(f'Comando ADB falhou: {error_msg}')
                    if 'protocol fault' in error_msg and "couldn't read status" in error_msg or 'failed to check server version' in error_msg:
                        if attempt == 0:
                            self.logger.info('Detectado servidor ADB n├úo inicializado. Tentando inicializar...')
                            try:
                                try:
                                    start_result = subprocess.run([self.adb_path, 'start-server'], startupinfo=self.startupinfo, creationflags=self.creation_flags, capture_output=True, text=True, timeout=15)
                                    self.logger.info(f'Tentativa de inicializa├º├úo do servidor ADB: {start_result.returncode}')
                                    time.sleep(1)
                                except Exception as start_error:
                                    self.logger.warning(f'Falha ao inicializar servidor ADB: {start_error}')
                            except subprocess.TimeoutExpired:
                                if attempt == max_attempts - 1:
                                    self.logger.error("Timeout ao executar comando 'adb devices'")
                                    raise Exception('Timeout ao verificar dispositivos ADB')
                                self.logger.warning(f'Timeout na tentativa {attempt + 1}, tentando novamente...')
                            except Exception as e:
                                if attempt == max_attempts - 1:
                                    raise Exception(f'Erro ao verificar dispositivo: {str(e)}')
                                self.logger.warning(f'Erro na tentativa {attempt + 1}: {str(e)}')
                            continue
                        raise Exception(f'ADB n├úo est├í funcionando corretamente ap├│s inicializa├º├úo: {error_msg}')
                    raise Exception(f'ADB n├úo est├í funcionando corretamente: {error_msg}')
            except subprocess.TimeoutExpired:
                if attempt == max_attempts - 1:
                    self.logger.error("Timeout ao executar comando 'adb devices'")
                    raise Exception('Timeout ao verificar dispositivos ADB')
                self.logger.warning(f'Timeout na tentativa {attempt + 1}, tentando novamente...')
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise Exception(f'Erro ao verificar dispositivo: {str(e)}')
                self.logger.warning(f'Erro na tentativa {attempt + 1}: {str(e)}')
            devices_output = result.stdout.strip()
            lines = devices_output.split('\n')
            self.logger.debug(f'Sa├¡da do check_device: {devices_output}')
            for line in lines:
                line = line.strip()
                if line.startswith('List of devices') or line.startswith('*'):
                    continue
                if '\tdevice' in line or ' device' in line:
                    self.logger.debug(f'Dispositivo encontrado em check_device: {line}')
                    return True
            try:
                pass
            except subprocess.TimeoutExpired:
                if attempt == max_attempts - 1:
                    self.logger.error("Timeout ao executar comando 'adb devices'")
                    raise Exception('Timeout ao verificar dispositivos ADB')
                self.logger.warning(f'Timeout na tentativa {attempt + 1}, tentando novamente...')
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise Exception(f'Erro ao verificar dispositivo: {str(e)}')
                self.logger.warning(f'Erro na tentativa {attempt + 1}: {str(e)}')
            return False
    def get_battery_info(self):
        try:
            return self._run_adb_command([self.adb_path, 'shell', 'dumpsys', 'battery'])
        except Exception as e:
            raise Exception(f'Erro ao obter info da bateria: {str(e)}')
    def get_device_logs(self):
        try:
            if not self.adb_path or not os.path.isfile(self.adb_path):
                raise Exception('ADB n├úo encontrado. Verifique a instala├º├úo.')
            result = subprocess.run([self.adb_path, 'logcat', '-d'], startupinfo=self.startupinfo, creationflags=self.creation_flags, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else f'Exit code: {result.returncode}'
                raise Exception(f'Falha ao extrair logs: {error_msg}')
        except subprocess.TimeoutExpired:
            raise Exception('Timeout ao extrair logs do dispositivo')
        except Exception as e:
            raise Exception(f'Erro ao extrair logs: {str(e)}')
        return result.stdout
    def reset_battery_stats(self):
        try:
            self._run_adb_command([self.adb_path, 'shell', 'dumpsys', 'batterystats', '--reset'], capture_output=False)
            return 'Estat├¡sticas da bateria resetadas com sucesso'
        except Exception as e:
            raise Exception(f'Erro ao resetar bateria: {str(e)}')
    def parse_battery_info(self, info_str):
        info_dict = {}
        for line in info_str.split('\n'):
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                info_dict[key.strip()] = value.strip()
        return info_dict
    def check_wifi(self):
        try:
            return self._run_adb_command([self.adb_path, 'shell', 'dumpsys', 'wifi'])
        except Exception as e:
            raise Exception(f'Erro ao verificar WiFi: {str(e)}')
    def check_network(self):
        try:
            return self._run_adb_command([self.adb_path, 'shell', 'dumpsys', 'connectivity'])
        except Exception as e:
            raise Exception(f'Erro ao verificar rede: {str(e)}')
    def check_sensors(self):
        try:
            return self._run_adb_command([self.adb_path, 'shell', 'dumpsys', 'sensorservice'])
        except Exception as e:
            raise Exception(f'Erro ao verificar sensores: {str(e)}')
    def read_logs(self):
        while self.running and self.logcat_process:
            line = self.logcat_process.stdout.readline()
            if line:
                self.log_queue.put(line.strip())
            else:
                return
            return
    def start_logcat(self):
        try:
            if self.logcat_process:
                self.stop_logcat()
            self._run_adb_command([self.adb_path, 'logcat', '-c'], capture_output=False)
            self.logcat_process = subprocess.Popen([self.adb_path, 'logcat'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.path.dirname(self.adb_path), startupinfo=self.startupinfo, creationflags=self.creation_flags, universal_newlines=True, bufsize=1)
            self.running = True
            self.log_thread = threading.Thread(target=self.read_logs)
            self.log_thread.daemon = True
            self.log_thread.start()
            return True
        except Exception as e:
            self.running = False
            self.logcat_process = None
            raise Exception(f'Erro ao iniciar logcat: {str(e)}')
    def stop_logcat(self):
        self.running = False
        if self.logcat_process:
            self.logcat_process.terminate()
            self.logcat_process = None
    def parse_network_info(self, info_str):
        info_dict = {'network_providers': [], 'active_network': None, 'blocked_uids': [], 'network_status': {'wifi': {'state': 'Desconhecido', 'signal': None, 'ssid': None}, 'mobile': {'state': 'Desconhecido', 'type': None, 'signal': None}}, 'dns_servers': [], 'network_interfaces': []}
        current_section = None
        for line in info_str.split('\n'):
            line = line.strip()
            if 'NetworkProviders for:' in line:
                current_section = 'providers'
            elif 'Active default network:' in line:
                info_dict['active_network'] = line.split(':', 1)[1].strip()
            elif 'Status for known UIDs:' in line:
                current_section = 'uids'
            elif 'DNS servers:' in line:
                current_section = 'dns'
            elif 'Network Interfaces:' in line:
                current_section = 'interfaces'
            if current_section == 'providers' and ':' in line:
                provider = line.split(':', 1)[1].strip()
                if provider:
                    info_dict['network_providers'].append(provider)
                    continue
                continue
            if current_section == 'uids' and 'UID=' in line:
                uid = line.split('=')[1].split()[0]
                if 'blockedReasons=4' in line:
                    info_dict['blocked_uids'].append(uid)
                    continue
            elif 'WIFI' in line and 'CONNECTED' in line:
                info_dict['network_status']['wifi']['state'] = 'Conectado'
                if 'SignalStrength:' in line:
                    signal = line.split('SignalStrength:')[1].split()[0]
                    info_dict['network_status']['wifi']['signal'] = signal
                    continue
            else:
                if 'MOBILE' not in line:
                    continue
                if 'CONNECTED' not in line:
                    continue
                info_dict['network_status']['mobile']['state'] = 'Conectado'
                if 'type:' not in line:
                    continue
                net_type = line.split('type:')[1].split()[0]
                info_dict['network_status']['mobile']['type'] = net_type
                continue
        return info_dict
    def format_network_info(self, parsed_info):
        output = []
        output.append('=== Status da Rede ===')
        output.append(f'Rede Ativa: {parsed_info['active_network']}')
        wifi = parsed_info['network_status']['wifi']
        output.append('\n=== WiFi ===')
        output.append(f'Estado: {wifi['state']}')
        if wifi['signal']:
            output.append(f'For├ºa do Sinal: {wifi['signal']} dBm')
        if wifi['ssid']:
            output.append(f'Rede: {wifi['ssid']}')
        mobile = parsed_info['network_status']['mobile']
        output.append('\n=== Rede M├│vel ===')
        output.append(f'Estado: {mobile['state']}')
        if mobile['type']:
            output.append(f'Tipo: {mobile['type']}')
        if mobile['signal']:
            output.append(f'For├ºa do Sinal: {mobile['signal']}')
        output.append('\n=== Provedores de Rede ===')
        for provider in parsed_info['network_providers']:
            output.append(f'ÔÇó {provider}')
        if parsed_info['blocked_uids']:
            output.append('\n=== Aplicativos com Rede Bloqueada ===')
            for uid in parsed_info['blocked_uids']:
                output.append(f'ÔÇó UID {uid}')
        return '\n'.join(output)
    def clear_adb_cache(self):
        try:
            if not self.adb_path:
                self.logger.warning('Tentativa de limpar cache mas ADB n├úo encontrado')
                return False
        except Exception as e:
            self.logger.error(f'Erro no clear_adb_cache: {str(e)}')
            return False
        try:
            self.kill_server()
            time.sleep(1)
            self.start_server()
            self.logger.info('Cache do ADB limpo com sucesso')
        except Exception as e:
            self.logger.error(f'Erro ao limpar cache do ADB: {str(e)}')
            try:
                return False
            except Exception as e:
                self.logger.error(f'Erro no clear_adb_cache: {str(e)}')
                return False
        return True
    def _verify_adb_dlls(self, adb_executable):
        if platform.system() != 'Windows':
            return (True, '')
        adb_dir = os.path.dirname(adb_executable)
        required_dlls = ['AdbWinApi.dll', 'AdbWinUsbApi.dll']
        missing = []
        for dll in required_dlls:
            dll_path = os.path.join(adb_dir, dll)
            if os.path.isfile(dll_path):
                continue
            missing.append(dll)
        if missing:
            dlls_str = ', '.join(missing)
            logger.error(f'DLLs ausentes: {dlls_str}')
            return False, f'Arquivos necess├írios n├úo encontrados: {dlls_str}. Poss├¡vel causa: antiv├¡rus removeu os arquivos. Adicione a pasta do programa nas exclus├Áes do antiv├¡rus e reinstale.'
        return (True, '')
    def _run_adb_command(self, command_list, capture_output=True, timeout=30):
        if not command_list or not command_list[0]:
            raise Exception('Comando ADB inv├ílido: caminho do ADB n├úo especificado')
        _GLOBAL_CMDS = {'connect', 'devices', 'version', 'disconnect', 'kill-server', 'start-server'}
        if self.selected_serial and len(command_list) > 1 and command_list[1] not in _GLOBAL_CMDS and command_list[1] != '-s':
            command_list = [command_list[0], '-s', self.selected_serial] + command_list[1:]
        adb_executable = command_list[0]
        if not os.path.isfile(adb_executable):
            _recovered = self.find_adb_path()
            if _recovered and os.path.isfile(_recovered):
                self.adb_path = _recovered
                command_list[0] = _recovered
                adb_executable = _recovered
            else:
                raise Exception('ADB n├úo encontrado. Verifique a instala├º├úo.')
        dlls_ok, dlls_msg = self._verify_adb_dlls(adb_executable)
        if not dlls_ok:
            _recovered = self._resolve_protected_adb('adb.exe' if platform.system() == 'Windows' else 'adb')
            if _recovered:
                self.adb_path = _recovered
                command_list[0] = _recovered
                adb_executable = _recovered
                dlls_ok, dlls_msg = self._verify_adb_dlls(_recovered)
            if not dlls_ok:
                raise Exception(dlls_msg)
        adb_dir = os.path.dirname(adb_executable)
        with self.command_lock:
            try:
                if capture_output:
                    if platform.system() == 'Windows':
                        result = subprocess.run(command_list, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=timeout, cwd=adb_dir, startupinfo=self.startupinfo, creationflags=self.creation_flags)
                    else:
                        result = subprocess.run(command_list, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=timeout)
                    return result.stdout
            except subprocess.CalledProcessError as e:
                logger.error(f'Erro ao executar comando ADB: {str(e)}')
                raise
            except OSError as e:
                error_msg = str(e)
                if hasattr(e, 'winerror') and e.winerror == 3221225477:
                    logger.error('ERRO 0xc0000005 (ACCESS VIOLATION) ao executar ADB!')
                    logger.error(f'Caminho do ADB: {os.path.basename(adb_executable)}')
                    logger.error('Poss├¡veis causas: pasta oculta/sistema, DEP bloqueando')
                    raise Exception('Erro de acesso ao executar ADB (0xc0000005). Verifique se o ADB est├í em uma pasta acess├¡vel (ex: C:\\platform-tools) e n├úo em pastas ocultas ou de sistema.')
                if '0xc0000005' in error_msg or 'Access violation' in error_msg:
                    logger.error(f'ERRO 0xc0000005 detectado na mensagem: {error_msg}')
                    raise Exception('Erro de acesso ao executar ADB. Reinstale o platform-tools em C:\\platform-tools')
                logger.error(f'Erro de sistema ao executar ADB: {str(e)}')
                raise
            except subprocess.TimeoutExpired:
                logger.error(f'Timeout ao executar comando ADB ({timeout}s)')
                raise Exception('Timeout ao executar comando ADB. O dispositivo pode estar ocupado.')
            except Exception as e:
                logger.error(f'Erro inesperado: {str(e)}')
                raise
            try:
                if platform.system() == 'Windows':
                    subprocess.run(command_list, timeout=timeout, cwd=adb_dir, startupinfo=self.startupinfo, creationflags=self.creation_flags)
                else:
                    subprocess.run(command_list, timeout=timeout)
                return
            except subprocess.CalledProcessError as e:
                logger.error(f'Erro ao executar comando ADB: {str(e)}')
                raise
            except OSError as e:
                error_msg = str(e)
                if hasattr(e, 'winerror') and e.winerror == 3221225477:
                    logger.error('ERRO 0xc0000005 (ACCESS VIOLATION) ao executar ADB!')
                    logger.error(f'Caminho do ADB: {os.path.basename(adb_executable)}')
                    logger.error('Poss├¡veis causas: pasta oculta/sistema, DEP bloqueando')
                    raise Exception('Erro de acesso ao executar ADB (0xc0000005). Verifique se o ADB est├í em uma pasta acess├¡vel (ex: C:\\platform-tools) e n├úo em pastas ocultas ou de sistema.')
                if '0xc0000005' in error_msg or 'Access violation' in error_msg:
                    logger.error(f'ERRO 0xc0000005 detectado na mensagem: {error_msg}')
                    raise Exception('Erro de acesso ao executar ADB. Reinstale o platform-tools em C:\\platform-tools')
                logger.error(f'Erro de sistema ao executar ADB: {str(e)}')
                raise
            except subprocess.TimeoutExpired:
                logger.error(f'Timeout ao executar comando ADB ({timeout}s)')
                raise Exception('Timeout ao executar comando ADB. O dispositivo pode estar ocupado.')
            except Exception as e:
                logger.error(f'Erro inesperado: {str(e)}')
                raise
    def check_fastboot_device(self):
        max_attempts = 2
        if not self.fastboot_path:
            self.fastboot_path = self.find_fastboot_path()
            if not self.fastboot_path:
                raise Exception('Fastboot n├úo encontrado. Verifique se est├í instalado em C:\\platform-tools ou no PATH do sistema.')
        if not os.path.isfile(self.fastboot_path):
            self.logger.error(f'Fastboot n├úo encontrado no caminho: {self.fastboot_path}')
            raise Exception('Fastboot n├úo encontrado. Verifique se o arquivo est├í acess├¡vel.')
        for attempt in range(max_attempts):
            try:
                result = subprocess.run([self.fastboot_path, 'devices'], startupinfo=self.startupinfo, creationflags=self.creation_flags, capture_output=True, text=True, timeout=10)
                if result.returncode != 0:
                    error_msg = result.stderr.strip() if result.stderr else f'Exit code: {result.returncode}'
                    self.logger.error(f'Comando fastboot falhou: {error_msg}')
                    if 'protocol fault' in error_msg and "couldn't read status" in error_msg or 'failed to check server version' in error_msg:
                        if attempt == 0:
                            self.logger.info('Detectado poss├¡vel problema de inicializa├º├úo do fastboot. Tentando novamente...')
                            time.sleep(1)
                            continue
                        raise Exception(f'Fastboot n├úo est├í funcionando corretamente ap├│s nova tentativa: {error_msg}')
                    raise Exception(f'Fastboot n├úo est├í funcionando corretamente: {error_msg}')
            except subprocess.TimeoutExpired:
                if attempt == max_attempts - 1:
                    self.logger.error("Timeout ao executar comando 'fastboot devices'")
                    raise Exception('Timeout ao verificar dispositivos fastboot')
                self.logger.warning(f'Timeout na tentativa {attempt + 1} do fastboot, tentando novamente...')
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise Exception(f'Erro ao verificar dispositivo fastboot: {str(e)}')
                self.logger.warning(f'Erro na tentativa {attempt + 1} do fastboot: {str(e)}')
            devices = result.stdout.strip().split('\n')[0:]
            return len(devices) > 0 and 'fastboot' in ' '.join(devices).lower()
    def check_device_info(self):
        try:
            info = {}
            info['model'] = self._run_adb_command([self.adb_path, 'shell', 'getprop', 'ro.product.model']).strip()
            info['brand'] = self._run_adb_command([self.adb_path, 'shell', 'getprop', 'ro.product.brand']).strip()
            info['android'] = self._run_adb_command([self.adb_path, 'shell', 'getprop', 'ro.build.version.release']).strip()
            info['security'] = self._run_adb_command([self.adb_path, 'shell', 'getprop', 'ro.build.version.security_patch']).strip()
            info['imei'] = self._run_adb_command([self.adb_path, 'shell', "service call iphonesubinfo 1 | grep -o '[0-9a-f]\\{8\\} ' | tail -n+3 | while read a; do echo -n \\\\u${a:4:4}\\\\u${a:0:4}; done"]).strip()
            info['device'] = self._run_adb_command([self.adb_path, 'shell', 'getprop', 'ro.product.device']).strip()
            info['board'] = self._run_adb_command([self.adb_path, 'shell', 'getprop', 'ro.product.board']).strip()
            info['manufacturer'] = self._run_adb_command([self.adb_path, 'shell', 'getprop', 'ro.product.manufacturer']).strip()
            info['hardware'] = self._run_adb_command([self.adb_path, 'shell', 'getprop', 'ro.hardware']).strip()
            info['chipset'] = self._run_adb_command([self.adb_path, 'shell', 'getprop', 'ro.board.platform']).strip()
            info['build_id'] = self._run_adb_command([self.adb_path, 'shell', 'getprop', 'ro.build.id']).strip()
            info['build_type'] = self._run_adb_command([self.adb_path, 'shell', 'getprop', 'ro.build.type']).strip()
            info['build_fingerprint'] = self._run_adb_command([self.adb_path, 'shell', 'getprop', 'ro.build.fingerprint']).strip()
            info['baseband'] = self._run_adb_command([self.adb_path, 'shell', 'getprop', 'ro.build.expect.baseband']).strip()
            info['kernel'] = self._run_adb_command([self.adb_path, 'shell', 'uname -r']).strip()
            self._log_device_info(info)
            return info
        except Exception as e:
            logger.error(f'Erro ao obter informa├º├Áes do dispositivo: {str(e)}')
            raise Exception(f'Erro ao obter informa├º├Áes do dispositivo: {str(e)}')
    def _log_device_info(self, info):
        cores = {'azul': '\x1b[94m', 'verde': '\x1b[92m', 'roxo': '\x1b[95m', 'amarelo': '\x1b[93m', 'vermelho': '\x1b[91m', 'negrito': '\x1b[1m', 'fim': '\x1b[0m', 'sublinhado': '\x1b[4m'}
        print(f'\n{cores['negrito']}{cores['azul']}{'============================================================'}{cores['fim']}')
        print(f'{cores['negrito']}{cores['azul']}{'===================='} INFORMA├ç├òES DO DISPOSITIVO {'===================='}{cores['fim']}')
        print(f'{cores['negrito']}{cores['azul']}{'============================================================'}{cores['fim']}\n')
        print(f'{cores['negrito']}{cores['verde']}­ƒô▒ DISPOSITIVO:{cores['fim']} {cores['negrito']}{info.get('brand', 'N/A')} {info.get('model', 'N/A')}{cores['fim']}')
        print(f'{cores['negrito']}{cores['verde']}­ƒñû ANDROID:{cores['fim']} {cores['amarelo']}{info.get('android', 'N/A')}{cores['fim']} (Patch {info.get('security', 'N/A')})')
        if info.get('imei') and info.get('imei') != '\\x00\\x00':
            print(f'{cores['negrito']}{cores['verde']}­ƒô▓ IMEI:{cores['fim']} {info.get('imei', 'N/A')}')
        print(f'\n{cores['negrito']}{cores['roxo']}--- HARDWARE ---{cores['fim']}')
        print(f'{cores['negrito']}­ƒöº Chipset:{cores['fim']} {info.get('chipset', 'N/A')}')
        print(f'{cores['negrito']}­ƒºá Placa:{cores['fim']} {info.get('board', 'N/A')}')
        print(f'{cores['negrito']}ÔÜÖ´©Å Hardware:{cores['fim']} {info.get('hardware', 'N/A')}')
        print(f'{cores['negrito']}­ƒÅ¡ Fabricante:{cores['fim']} {info.get('manufacturer', 'N/A')}')
        print(f'{cores['negrito']}­ƒÆ╗ Kernel:{cores['fim']} {info.get('kernel', 'N/A')}')
        print(f'\n{cores['negrito']}{cores['roxo']}--- SISTEMA ---{cores['fim']}')
        print(f'{cores['negrito']}­ƒåö Build ID:{cores['fim']} {info.get('build_id', 'N/A')}')
        print(f'{cores['negrito']}­ƒôè Build Type:{cores['fim']} {info.get('build_type', 'N/A')}')
        build_fingerprint = info.get('build_fingerprint', 'N/A')
        print(f'{cores['negrito']}­ƒöæ Fingerprint:{cores['fim']} ', end='')
        if len(build_fingerprint) > 60:
            print(f'\n  {build_fingerprint}')
        else:
            print(build_fingerprint)
        if info.get('baseband'):
            print(f'{cores['negrito']}­ƒôí Baseband:{cores['fim']} {info.get('baseband', 'N/A')}')
        print(f'\n{cores['negrito']}{cores['azul']}{'============================================================'}{cores['fim']}')
        logger.info('==================================================')
        logger.info(f'=== Informa├º├Áes do Dispositivo {info.get('model', 'Desconhecido')} ===')
        logger.info('==================================================')
        logger.info(f'­ƒô▒ Modelo: {info.get('model', 'N/A')}')
        logger.info(f'­ƒÅ¡ Fabricante: {info.get('brand', 'N/A')} ({info.get('manufacturer', 'N/A')})')
        logger.info(f'­ƒñû Android: {info.get('android', 'N/A')}')
        logger.info(f'­ƒöÆ Patch de Seguran├ºa: {info.get('security', 'N/A')}')
        logger.info(f'­ƒô▒ IMEI: {info.get('imei', 'N/A')}')
        logger.info('--------------------------------------------------')
        logger.info('­ƒôï Especifica├º├Áes T├®cnicas:')
        logger.info(f'  ÔÇó Dispositivo: {info.get('device', 'N/A')}')
        logger.info(f'  ÔÇó Placa: {info.get('board', 'N/A')}')
        logger.info(f'  ÔÇó Hardware: {info.get('hardware', 'N/A')}')
        logger.info(f'  ÔÇó Chipset: {info.get('chipset', 'N/A')}')
        logger.info(f'  ÔÇó Kernel: {info.get('kernel', 'N/A')}')
        logger.info('--------------------------------------------------')
        logger.info('­ƒöº Informa├º├Áes de Build:')
        logger.info(f'  ÔÇó ID: {info.get('build_id', 'N/A')}')
        logger.info(f'  ÔÇó Tipo: {info.get('build_type', 'N/A')}')
        logger.info(f'  ÔÇó Baseband: {info.get('baseband', 'N/A')}')
        logger.info(f'  ÔÇó Fingerprint: {build_fingerprint}')
        logger.info('==================================================')
    def check_storage_info(self):
        try:
            return self._run_adb_command([self.adb_path, 'shell', 'df -h'])
        except Exception as e:
            raise Exception(f'Erro ao verificar armazenamento: {str(e)}')
    def check_cpu_info(self):
        try:
            return self._run_adb_command([self.adb_path, 'shell', 'cat /proc/cpuinfo'])
        except Exception as e:
            raise Exception(f'Erro ao verificar CPU: {str(e)}')
    def check_memory_info(self):
        try:
            return self._run_adb_command([self.adb_path, 'shell', 'cat /proc/meminfo'])
        except Exception as e:
            raise Exception(f'Erro ao verificar mem├│ria: {str(e)}')
    def test_touch_screen(self):
        try:
            return self._run_adb_command([self.adb_path, 'shell', 'getevent -l'])
        except Exception as e:
            raise Exception(f'Erro ao testar touch screen: {str(e)}')
    def test_buttons(self):
        try:
            return self._run_adb_command([self.adb_path, 'shell', 'getevent -l'])
        except Exception as e:
            raise Exception(f'Erro ao testar bot├Áes: {str(e)}')
    def check_charging_status(self):
        try:
            return self._run_adb_command([self.adb_path, 'shell', 'dumpsys battery'])
        except Exception as e:
            raise Exception(f'Erro ao verificar status de carregamento: {str(e)}')
    def check_display_info(self):
        try:
            return self._run_adb_command([self.adb_path, 'shell', 'dumpsys display'])
        except Exception as e:
            raise Exception(f'Erro ao verificar display: {str(e)}')
    def check_bootloader_status(self):
        try:
            if not self.check_fastboot_device():
                raise Exception('Nenhum dispositivo em modo fastboot detectado')
            return self._run_fastboot_command([self.fastboot_path, 'getvar', 'all'])
        except Exception as e:
            raise Exception(f'Erro ao verificar bootloader: {str(e)}')
    def check_partition_info(self):
        try:
            if not self.check_fastboot_device():
                raise Exception('Nenhum dispositivo em modo fastboot detectado')
            return self._run_fastboot_command([self.fastboot_path, 'getvar', 'partition-type:*'])
        except Exception as e:
            raise Exception(f'Erro ao verificar parti├º├Áes: {str(e)}')
    def check_partition_map(self):
        try:
            if not self.check_device():
                raise Exception('ÔØî Nenhum dispositivo Android detectado.\n\nVerifique:\nÔÇó O cabo USB est├í conectado\nÔÇó A depura├º├úo USB est├í ativada\nÔÇó O aparelho est├í ligado')
            path = self._run_adb_command([self.adb_path, 'shell', 'find /dev/block/platform -type d -name by-name 2>/dev/null']).strip()
            if not path:
                path = '/dev/block/by-name'
            result = self._run_adb_command([self.adb_path, 'shell', f'ls -la {path}'])
            if not result or not result.strip() or 'No such file' in result or 'not found' in result:
                raise Exception('ÔØî Este aparelho n├úo suporta a leitura do mapa de parti├º├Áes.\n\nPoss├¡veis motivos:\nÔÇó Modelo n├úo compat├¡vel com esta fun├º├úo\nÔÇó Aparelho com acesso restrito')
            return f'PATH:{path}\n{result}'
        except Exception as e:
            error_str = str(e)
            if error_str.startswith('ÔØî'):
                raise
            logger.error(f'Erro interno check_partition_map: {error_str}')
            raise Exception('ÔØî N├úo foi poss├¡vel obter o mapa de parti├º├Áes.\n\nTente reconectar o aparelho e tentar novamente.')
    def reboot_to_system(self):
        try:
            if self.check_device():
                self._run_adb_command([self.adb_path, 'reboot'])
                return 'Dispositivo reiniciando para o sistema via ADB'
            if self.check_fastboot_device():
                self._run_fastboot_command([self.fastboot_path, 'reboot'])
                return 'Dispositivo reiniciando para o sistema via Fastboot'
            raise Exception('ÔØî Nenhum dispositivo Android detectado!\n\nPara reiniciar o sistema, voc├¬ precisa:\nÔÇó Conectar um dispositivo Android via USB\nÔÇó Ativar a Depura├º├úo USB (para modo normal)\nÔÇó OU ter o dispositivo em modo Fastboot\nÔÇó Autorizar a conex├úo no dispositivo\nÔÇó Verificar se os drivers ADB/Fastboot est├úo instalados\n\n­ƒÆí Dica: V├í em Configura├º├Áes > Op├º├Áes do desenvolvedor > Depura├º├úo USB')
        except Exception as e:
            if 'Nenhum dispositivo Android detectado' in str(e):
                raise e
            raise Exception(f'Erro ao reiniciar: {str(e)}')
    def reboot_to_fastboot(self):
        try:
            if not self.check_device():
                raise Exception('ÔØî Nenhum dispositivo Android detectado!\n\nPara usar o Modo Fastboot, voc├¬ precisa:\nÔÇó Conectar um dispositivo Android via USB\nÔÇó Ativar a Depura├º├úo USB nas op├º├Áes de desenvolvedor\nÔÇó Autorizar a conex├úo no dispositivo\nÔÇó Verificar se os drivers ADB est├úo instalados\n\n­ƒÆí Dica: V├í em Configura├º├Áes > Op├º├Áes do desenvolvedor > Depura├º├úo USB')
            self._run_adb_command([self.adb_path, 'reboot', 'bootloader'])
            return 'Dispositivo reiniciando para fastboot'
        except Exception as e:
            if 'Nenhum dispositivo Android detectado' in str(e):
                raise e
            raise Exception(f'Erro ao reiniciar para fastboot: {str(e)}')
    def reboot_to_recovery(self):
        try:
            if not self.check_device():
                raise Exception('ÔØî Nenhum dispositivo Android detectado!\n\nPara usar o Modo Recovery, voc├¬ precisa:\nÔÇó Conectar um dispositivo Android via USB\nÔÇó Ativar a Depura├º├úo USB nas op├º├Áes de desenvolvedor\nÔÇó Autorizar a conex├úo no dispositivo\nÔÇó Verificar se os drivers ADB est├úo instalados\n\n­ƒÆí Dica: V├í em Configura├º├Áes > Op├º├Áes do desenvolvedor > Depura├º├úo USB')
            self._run_adb_command([self.adb_path, 'reboot', 'recovery'])
            return 'Dispositivo reiniciando para recovery'
        except Exception as e:
            if 'Nenhum dispositivo Android detectado' in str(e):
                raise e
            raise Exception(f'Erro ao reiniciar para recovery: {str(e)}')
    def test_usb_connection(self):
        try:
            return self._run_adb_command([self.adb_path, 'shell', 'dumpsys', 'usb'])
        except Exception as e:
            raise Exception(f'Erro ao testar conex├úo USB: {str(e)}')
    def check_thermal_info(self):
        try:
            return self._run_adb_command([self.adb_path, 'shell', 'dumpsys', 'thermalservice'])
        except Exception as e:
            raise Exception(f'Erro ao verificar informa├º├Áes t├®rmicas: {str(e)}')
    def check_system_events(self):
        try:
            if not self.check_device():
                return 'Nenhum dispositivo detectado'
            log_results = []
            found_logs = False
            log_results.append('======================================================================')
            log_results.append('­ƒô▒ RELAT├ôRIO DE DIAGN├ôSTICO DO SISTEMA'.center(70))
            log_results.append('======================================================================')
            log_results.append('\nEste relat├│rio analisa logs e eventos do sistema Android para identificar problemas.')
            log_results.append('Cada se├º├úo cont├®m explica├º├Áes detalhadas para ajudar na interpreta├º├úo dos resultados.')
            log_results.append('----------------------------------------------------------------------\n')
            error_descriptions = {'permission': 'Problemas de permiss├úo - O sistema negou acesso a um recurso', 'crash': 'Crash de aplicativo - Um aplicativo fechou inesperadamente', 'anr': 'ANR (App Not Responding) - Um aplicativo parou de responder', 'failed': 'Falha em opera├º├úo - Uma a├º├úo solicitada n├úo p├┤de ser conclu├¡da', 'exception': 'Exce├º├úo n├úo tratada - Erro de programa├º├úo n├úo capturado', 'out of memory': 'Mem├│ria insuficiente - O dispositivo est├í com pouca RAM dispon├¡vel', 'battery': 'Problema de bateria - H├í um problema com a carga ou estado da bateria', 'temperature': 'Problema de temperatura - O dispositivo est├í muito quente ou frio', 'deadlock': 'Deadlock - Processos travados esperando um pelo outro', 'watchdog': 'Watchdog timeout - Um processo demorou muito para responder', 'fatal': 'Erro fatal - Problema grave no sistema ou aplicativo', 'denied': 'Acesso negado - Uma opera├º├úo foi bloqueada por seguran├ºa'}
            try:
                result = self._run_adb_command([self.adb_path, 'shell', 'logcat -d -b system'])
                if result and len(result.strip()) > 10:
                    important_lines = []
                    error_count = 0
                    warning_count = 0
                    error_types = {}
                    for line in result.split('\n'):
                        if 'E/' not in line and 'error' not in line.lower():
                            if 'exception' in line.lower():
                                important_lines.append(line)
                                error_count += 1
                                for error_key, description in error_descriptions.items():
                                    if error_key not in line.lower():
                                        continue
                                    if error_key not in error_types:
                                        error_types[error_key] = {'count': 1, 'description': description}
                                    else:
                                        error_types[error_key]['count'] += 1
                            elif 'W/' in line or 'warning' in line.lower():
                                important_lines.append(line)
                                warning_count += 1
                    if len(important_lines) > 30:
                        important_lines = important_lines[:30]
                        important_lines.append('... (mais linhas omitidas) ...')
                    log_results.append('\n­ƒôè RESUMO DE LOGS DO SISTEMA')
                    log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                    log_results.append('Ôòæ ' + 'O que ├® isto?'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'Logs do sistema Android que mostram erros e avisos dos aplicativos'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'e componentes do sistema operacional.'.ljust(66) + ' Ôòæ')
                    log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                    log_results.append(f'ÔØî Erros encontrados: {error_count}')
                    log_results.append(f'ÔÜá´©Å Avisos encontrados: {warning_count}')
                    if error_types:
                        log_results.append('\n­ƒöì TIPOS DE ERROS DETECTADOS:')
                        log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                        for error_key, data in error_types.items():
                            log_results.append(f'Ôòæ ÔÇó {data['description']} ({data['count']} ocorr├¬ncias)'.ljust(69) + 'Ôòæ')
                        log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                    if important_lines:
                        log_results.append('\n­ƒöì EVENTOS IMPORTANTES DO SISTEMA')
                        log_results.append('----------------------------------------------------------------------')
                        log_results.append('­ƒæë O que significam estes logs?')
                        log_results.append('   E/ = Erro | W/ = Aviso | I/ = Informa├º├úo')
                        log_results.append('   Os c├│digos ap├│s a barra (/) indicam o componente que gerou o log.')
                        log_results.append('----------------------------------------------------------------------')
                        log_results.append('\n'.join(important_lines))
                    else:
                        log_results.append('\nÔ£à Nenhum evento cr├¡tico encontrado nos logs do sistema')
                        log_results.append('   Isto ├® um bom sinal! O sistema est├í funcionando normalmente.')
                    found_logs = True
            except Exception as e:
                log_results.append(f'\nÔÜá´©Å N├úo foi poss├¡vel ler logs do sistema: {str(e)}')
                log_results.append('   Por que isto acontece? O dispositivo pode ter restri├º├Áes de acesso')
                log_results.append('   aos logs ou a depura├º├úo USB pode estar com problemas.')
            else:
                kernel_issues_by_type = {}
        except Exception as e:
            return f'Erro ao verificar eventos do sistema:\n{str(e)}\n\nVerifique se:\n1. O dispositivo est├í respondendo\n2. A conex├úo USB est├í est├ível\n3. A depura├º├úo USB continua ativada'
        try:
            result = self._run_adb_command([self.adb_path, 'shell', 'dmesg'])
            if result and len(result.strip()) > 10:
                kernel_issues = []
                kernel_terms = {'error': 'Erro geral no kernel', 'fail': 'Falha em uma opera├º├úo', 'denied': 'Permiss├úo negada pelo sistema', 'cannot': 'Opera├º├úo imposs├¡vel', 'panic': 'Kernel Panic - erro muito grave', 'emerg': 'Emerg├¬ncia no sistema', 'alert': 'Alerta de funcionamento', 'critical': 'Problema cr├¡tico', 'oom_kill': 'Out of Memory Kill - Processo eliminado por falta de mem├│ria', 'segfault': 'Segmentation Fault - Acesso inv├ílido ├á mem├│ria', 'i/o error': 'Erro de entrada/sa├¡da', 'blocked for': 'Processo bloqueado por muito tempo'}
                for line in result.split('\n'):
                    lower_line = line.lower()
                    for term, description in kernel_terms.items():
                        if not term in lower_line:
                            continue
                        kernel_issues.append(line)
                        if term not in kernel_issues_by_type:
                            kernel_issues_by_type[term] = {'count': 1, 'description': description}
                        else:
                            kernel_issues_by_type[term]['count'] += 1
                        break
                if len(kernel_issues) > 20:
                    kernel_issues = kernel_issues[:20]
                    kernel_issues.append('... (mais linhas omitidas) ...')
                log_results.append('\n­ƒûÑ´©Å LOGS DO KERNEL (DMESG)')
                log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                log_results.append('Ôòæ ' + 'O que ├® isto?'.ljust(66) + ' Ôòæ')
                log_results.append('Ôòæ ' + 'Logs do n├║cleo do sistema (kernel) que mostram problemas de'.ljust(66) + ' Ôòæ')
                log_results.append('Ôòæ ' + 'hardware, permiss├Áes e acessos a recursos de baixo n├¡vel.'.ljust(66) + ' Ôòæ')
                log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                if kernel_issues_by_type:
                    log_results.append('\nÔÜá´©Å TIPOS DE PROBLEMAS NO KERNEL:')
                    log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                    for term, data in kernel_issues_by_type.items():
                        log_results.append(f'Ôòæ ÔÇó {data['description']} ({data['count']} ocorr├¬ncias)'.ljust(69) + 'Ôòæ')
                    log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                    log_results.append('\n­ƒæë O que isso significa para voc├¬?')
                    log_results.append('   Problemas no kernel podem causar travamentos, reinicializa├º├Áes')
                    log_results.append('   inesperadas ou funcionamento inst├ível do dispositivo.')
                if kernel_issues:
                    log_results.append('\nÔÜá´©Å Problemas identificados no kernel:')
                    log_results.append('----------------------------------------------------------------------')
                    log_results.append('\n'.join(kernel_issues))
                else:
                    log_results.append('\nÔ£à Nenhum problema cr├¡tico encontrado nos logs do kernel')
                    log_results.append('   Os componentes de baixo n├¡vel do sistema est├úo funcionando corretamente.')
                found_logs = True
        except Exception as e:
            log_results.append(f'\nÔÜá´©Å N├úo foi poss├¡vel ler logs do kernel: {str(e)}')
            log_results.append('   Por que isto acontece? Alguns dispositivos restringem o acesso')
            log_results.append('   aos logs do kernel por raz├Áes de seguran├ºa.')
        crash_count = 0
        anr_count = 0
        error_count = 0
        crash_apps = set()
        anr_apps = set()
        try:
            result = self._run_adb_command([self.adb_path, 'shell', 'dumpsys dropbox --print'])
            if result and len(result.strip()) > 10:
                crash_events = []
                anr_events = []
                other_events = []
                for line in result.split('\n'):
                    if 'CRASH' in line:
                        crash_events.append(line)
                        crash_count += 1
                        app_match = re.search('data_app_crash/([^/]+)', line)
                        if app_match:
                            crash_apps.add(app_match.group(1))
                    elif 'ANR' in line:
                        anr_events.append(line)
                        anr_count += 1
                        app_match = re.search('data_app_anr/([^/]+)', line)
                        if app_match:
                            anr_apps.add(app_match.group(1))
                    elif 'ERROR' in line or 'EXCEPTION' in line:
                        other_events.append(line)
                        error_count += 1
                log_results.append('\n­ƒô▒ EVENTOS DO SISTEMA (DROPBOX)')
                log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                log_results.append('Ôòæ ' + 'O que ├® isto?'.ljust(66) + ' Ôòæ')
                log_results.append('Ôòæ ' + 'Logs de eventos cr├¡ticos como crashes, aplicativos que n├úo'.ljust(66) + ' Ôòæ')
                log_results.append('Ôòæ ' + 'respondem (ANRs) e outros erros significativos do sistema.'.ljust(66) + ' Ôòæ')
                log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                if crash_events:
                    log_results.append('\n­ƒÆÑ CRASHES DETECTADOS:')
                    log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                    log_results.append('Ôòæ ' + 'O que s├úo crashes?'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'Crashes ocorrem quando um aplicativo para de funcionar'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'abruptamente devido a um erro grave no c├│digo.'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'Impacto: Perda de dados n├úo salvos e interrup├º├úo do uso.'.ljust(66) + ' Ôòæ')
                    log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                    log_results.append('\n'.join(crash_events[:10]))
                    if len(crash_events) > 10:
                        log_results.append(f'... (mais {len(crash_events) - 10} eventos omitidos) ...')
                if anr_events:
                    log_results.append('\nÔÅ▒´©Å ANRs (Application Not Responding):')
                    log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                    log_results.append('Ôòæ ' + 'O que s├úo ANRs?'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + "Ocorrem quando um aplicativo 'congela' e n├úo responde ├ás".ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'intera├º├Áes do usu├írio por mais de 5 segundos.'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'Impacto: Frustra├º├úo do usu├írio e perda de produtividade.'.ljust(66) + ' Ôòæ')
                    log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                    log_results.append('\n'.join(anr_events[:10]))
                    if len(anr_events) > 10:
                        log_results.append(f'... (mais {len(anr_events) - 10} eventos omitidos) ...')
                if other_events:
                    log_results.append('\nÔÜá´©Å OUTROS ERROS:')
                    log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                    log_results.append('Ôòæ ' + 'O que s├úo esses erros?'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'Problemas n├úo categorizados que afetam o funcionamento do'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'sistema ou aplicativos de forma irregular.'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'Impacto: Comportamentos inesperados ou falhas diversas.'.ljust(66) + ' Ôòæ')
                    log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                    log_results.append('\n'.join(other_events[:10]))
                    if len(other_events) > 10:
                        log_results.append(f'... (mais {len(other_events) - 10} eventos omitidos) ...')
                if not crash_events and not anr_events and not other_events:
                    log_results.append('Ô£à Nenhum evento cr├¡tico encontrado nos logs do sistema')
                    log_results.append('   Isto ├® um ├│timo sinal! Significa que o sistema est├í operando')
                    log_results.append('   corretamente sem falhas graves recentes.')
                found_logs = True
        except Exception as e:
            log_results.append(f'\nÔÜá´©Å N├úo foi poss├¡vel ler eventos do sistema: {str(e)}')
            log_results.append('   Por que isto acontece? O dispositivo pode ter restri├º├Áes de acesso')
            log_results.append('   aos logs do sistema ou problemas de comunica├º├úo.')
        battery_dict = {}
        try:
            battery_info = self._run_adb_command([self.adb_path, 'shell', 'dumpsys battery'])
            if battery_info:
                log_results.append('\n­ƒöï INFORMA├ç├òES DA BATERIA')
                log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                log_results.append('Ôòæ ' + 'O que ├® isto?'.ljust(66) + ' Ôòæ')
                log_results.append('Ôòæ ' + 'Dados t├®cnicos sobre o estado atual da bateria e como est├í'.ljust(66) + ' Ôòæ')
                log_results.append('Ôòæ ' + 'sendo utilizada pelo dispositivo.'.ljust(66) + ' Ôòæ')
                log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                for line in battery_info.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        battery_dict[key.strip()] = value.strip()
                if battery_dict:
                    power_source = 'AC' if battery_dict.get('AC powered') == 'true' else 'USB' if battery_dict.get('USB powered') == 'true' else 'Bateria'
                    health_map = {'1': 'Desconhecido', '2': 'Boa', '3': 'Superaquecida', '4': 'Danificada', '5': 'Sobretens├úo', '6': 'Falha', '7': 'Fria'}
                    health_code = battery_dict.get('health', '1')
                    health = health_map.get(health_code, 'Desconhecido')
                    log_results.append('')
                    log_results.append('ÔöîÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÉ')
                    log_results.append(f'Ôöé ­ƒöî Fonte de energia: {power_source.ljust(48)}Ôöé')
                    log_results.append('Ôöé  Ô×£ Indica se o dispositivo est├í usando energia da bateria   Ôöé')
                    log_results.append('Ôöé    ou est├í conectado ├á energia.                             Ôöé')
                    log_results.append('Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ')
                    log_results.append(f'Ôöé ­ƒôè N├¡vel: {battery_dict.get('level', 'N/A')}%'.ljust(67) + 'Ôöé')
                    log_results.append('Ôöé  Ô×£ A porcentagem atual de carga da bateria.                 Ôöé')
                    log_results.append('Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ')
                    log_results.append(f'Ôöé ÔØñ´©Å Sa├║de: {health} (C├│digo: {health_code})'.ljust(67) + 'Ôöé')
                    log_results.append('Ôöé  Ô×£ Condi├º├úo geral da bateria e sua capacidade de manter     Ôöé')
                    log_results.append('Ôöé    carga.                                                   Ôöé')
            try:
                temp = float(battery_dict.get('temperature', '0')) / 10
                log_results.append('Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ')
                log_results.append(f'Ôöé ­ƒîí´©Å Temperatura: {temp:.1f}┬░C'.ljust(67) + 'Ôöé')
                log_results.append('Ôöé  Ô×£ Temperatura atual da bateria. Valores acima de 40┬░C s├úo   Ôöé')
                log_results.append('Ôöé    preocupantes.                                             Ôöé')
            except:
                log_results.append('Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ')
                log_results.append(f'Ôöé ­ƒîí´©Å Temperatura: {battery_dict.get('temperature', 'N/A')}'.ljust(67) + 'Ôöé')
                log_results.append('Ôöé  Ô×£ Temperatura atual da bateria em unidades do sistema.      Ôöé')
            else:
                try:
                    try:
                        try:
                            try:
                                voltage = float(battery_dict.get('voltage', '0')) / 1000
                                log_results.append('Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ')
                                log_results.append(f'Ôöé ÔÜí Voltagem: {voltage:.2f}V'.ljust(67) + 'Ôöé')
                                log_results.append('Ôöé  Ô×£ Tens├úo atual da bateria. Valores abaixo do normal podem   Ôöé')
                                log_results.append('Ôöé    indicar problemas.                                        Ôöé')
                            except Exception as e:
                                log_results.append(f'\nÔÜá´©Å N├úo foi poss├¡vel ler informa├º├Áes da bateria: {str(e)}')
                                log_results.append('   Por que isto acontece? Pode haver restri├º├Áes de permiss├úo para')
                                log_results.append('   acessar as informa├º├Áes da bateria ou problemas de comunica├º├úo.')
                        except:
                            log_results.append('Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ')
                            log_results.append(f'Ôöé ÔÜí Voltagem: {battery_dict.get('voltage', 'N/A')}'.ljust(67) + 'Ôöé')
                            log_results.append('Ôöé  Ô×£ Tens├úo el├®trica atual fornecida pela bateria.             Ôöé')
                    except Exception as e:
                        log_results.append(f'\nÔÜá´©Å N├úo foi poss├¡vel ler informa├º├Áes da bateria: {str(e)}')
                        log_results.append('   Por que isto acontece? Pode haver restri├º├Áes de permiss├úo para')
                        log_results.append('   acessar as informa├º├Áes da bateria ou problemas de comunica├º├úo.')
                except Exception as e:
                    return f'Erro ao verificar eventos do sistema:\n{str(e)}\n\nVerifique se:\n1. O dispositivo est├í respondendo\n2. A conex├úo USB est├í est├ível\n3. A depura├º├úo USB continua ativada'
                log_results.append('Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ')
                log_results.append(f'Ôöé ­ƒö¼ Tecnologia: {battery_dict.get('technology', 'N/A')}'.ljust(67) + 'Ôöé')
                log_results.append('Ôöé  Ô×£ O tipo de qu├¡mica utilizada na bateria (Li-Ion, Li-Poly).    Ôöé')
                log_results.append('ÔööÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÿ')
                found_logs = True
        except Exception as e:
            return f'Erro ao verificar eventos do sistema:\n{str(e)}\n\nVerifique se:\n1. O dispositivo est├í respondendo\n2. A conex├úo USB est├í est├ível\n3. A depura├º├úo USB continua ativada'
        return '\n'.join(log_results)
    def panic_android(self, parent_window=None):
        if not self.check_device():
            return 'Nenhum dispositivo detectado. Conecte o dispositivo e tente novamente.'
        progress = QProgressDialog('Gerando Bugreport...', None, 0, 100, parent_window)
        progress.setWindowModality(Qt.WindowModal)
        progress.setAutoClose(True)
        progress.setValue(0)
        try:
            progress.setLabelText('Coletando informa├º├Áes do dispositivo...')
            device_info = self.check_device_info()
            progress.setValue(10)
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            default_filename = f'bugreport_{timestamp}.zip'
            save_path, _ = QFileDialog.getSaveFileName(parent_window, 'Salvar Bugreport', default_filename, 'Arquivos ZIP (*.zip)')
            if not save_path:
                return 'Opera├º├úo cancelada pelo usu├írio.'
            progress.setLabelText('Gerando bugreport completo...\nIsso pode levar alguns minutos.')
            progress.setValue(30)
            self._run_adb_command([self.adb_path, 'bugreport', save_path])
            progress.setValue(90)
            if os.path.exists(save_path):
                progress.setValue(100)
                return f'Bugreport gerado com sucesso!\n\nArquivo salvo em:\n{save_path}\n\nEste arquivo cont├®m informa├º├Áes detalhadas do sistema\nque podem ajudar no diagn├│stico de problemas.'
            raise Exception('Falha ao gerar o arquivo de bugreport')
        except Exception as e:
            return f'Erro durante a gera├º├úo do bugreport: {str(e)}'
    def filter_logcat(self, filter_type='all', keywords=None):
        try:
            buffer_arg = {'all': '', 'system': '-b system', 'main': '-b main', 'crash': '-b crash', 'radio': '-b radio', 'events': '-b events'}.get(filter_type, '')
            cmd = [self.adb_path, 'logcat', '-d']
            if buffer_arg:
                cmd.extend(buffer_arg.split())
            output = self._run_adb_command(cmd)
            if keywords:
                filtered_lines = []
                for line in output.split('\n'):
                    if any((keyword.lower() in line.lower() for keyword in keywords)):
                        filtered_lines.append(line)
                return '\n'.join(filtered_lines)
            return output
        except Exception as e:
            raise Exception(f'Erro ao filtrar logs: {str(e)}')
    def analyze_system_errors(self):
        try:
            system_logs = self.filter_logcat('system')
            crash_logs = self.filter_logcat('crash')
            error_patterns = {'ANR': 'ANR in (\\S+)', 'FATAL EXCEPTION': 'FATAL EXCEPTION: .*?(?=\\n)', 'System.err': 'System.err: .*?(?=\\n)', 'SIGSEGV': 'SIGSEGV.*?(?=\\n)', 'OutOfMemoryError': 'OutOfMemoryError.*?(?=\\n)'}
            results = {'anrs': [], 'crashes': [], 'system_errors': [], 'summary': {'total_anrs': 0, 'total_crashes': 0, 'total_errors': 0}}
            for line in system_logs.split('\n'):
                if 'ANR in' in line:
                    match = re.search(error_patterns['ANR'], line)
                    if match:
                        results['anrs'].append({'package': match.group(1), 'timestamp': line.split()[0:2], 'full_log': line})
                        results['summary']['total_anrs'] += 1
                if any((err in line for err in ('FATAL EXCEPTION', 'System.err', 'SIGSEGV'))):
                    results['system_errors'].append(line)
                    results['summary']['total_errors'] += 1
            for line in crash_logs.split('\n'):
                if any((pattern in line for pattern in error_patterns.values())):
                    results['crashes'].append(line)
                    results['summary']['total_crashes'] += 1
            return self.format_error_analysis(results)
        except Exception as e:
            raise Exception(f'Erro ao analisar erros do sistema: {str(e)}')
    def format_error_analysis(self, results):
        output = []
        output.append('=== An├ílise de Erros do Sistema ===')
        output.append('\nResumo:')
        output.append(f'ÔÇó Total de ANRs: {results['summary']['total_anrs']}')
        output.append(f'ÔÇó Total de Crashes: {results['summary']['total_crashes']}')
        output.append(f'ÔÇó Total de Erros de Sistema: {results['summary']['total_errors']}')
        if results['anrs']:
            output.append('\n=== ANRs (Application Not Responding) ===')
            for anr in results['anrs']:
                output.append(f'\nAplicativo: {anr['package']}')
                output.append(f'Timestamp: {' '.join(anr['timestamp'])}')
        if results['crashes']:
            output.append('\n=== Crashes ===')
            for crash in results['crashes'][:10]:
                output.append(f'\nÔÇó {crash}')
        if results['system_errors']:
            output.append('\n=== Erros de Sistema ===')
            for error in results['system_errors'][:10]:
                output.append(f'\nÔÇó {error}')
        if not any([results['anrs'], results['crashes'], results['system_errors']]):
            output.append('\nNenhum erro cr├¡tico encontrado nos logs analisados.')
        return '\n'.join(output)
    def unlock_bootloader(self, parent_window=None):
        warning = 'ATEN├ç├âO!\n\nO desbloqueio do bootloader ir├í:\n1. Apagar TODOS os dados do dispositivo\n2. Pode invalidar a garantia\n3. ├ë um processo irrevers├¡vel\n\nCertifique-se de:\n1. Ter feito backup de todos os dados\n2. O dispositivo estar com a bateria carregada\n3. Ter habilitado o desbloqueio OEM nas configura├º├Áes\n\nDeseja continuar?'
        reply = QMessageBox.warning(parent_window, 'Desbloquear Bootloader', warning, QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No:
            return 'Opera├º├úo cancelada pelo usu├írio.'
        progress = QProgressDialog('Desbloqueando bootloader...', None, 0, 100, parent_window)
        progress.setWindowModality(Qt.WindowModal)
        progress.setAutoClose(True)
        progress.setValue(0)
        try:
            progress.setLabelText('Verificando estado do dispositivo...')
            if not self.check_fastboot_device():
                return 'Dispositivo n├úo est├í em modo fastboot.\n1. Ative o modo desenvolvedor\n2. Habilite o desbloqueio OEM\n3. Reinicie em modo fastboot'
            progress.setValue(20)
            progress.setLabelText('Verificando status do bootloader...')
            bootloader_status = self._run_fastboot_command([self.fastboot_path, 'getvar', 'unlocked'])
            progress.setValue(40)
            if 'unlocked: yes' in bootloader_status.lower():
                return 'Bootloader j├í est├í desbloqueado!'
            progress.setLabelText('Executando comando de desbloqueio...')
            self._run_fastboot_command([self.fastboot_path, 'flashing', 'unlock'])
            progress.setValue(60)
            progress.setLabelText('Aguardando confirma├º├úo no dispositivo...\nUse as teclas de volume e power para confirmar')
            time.sleep(5)
            progress.setValue(80)
            progress.setLabelText('Verificando resultado...')
            bootloader_status = self._run_fastboot_command([self.fastboot_path, 'getvar', 'unlocked'])
            progress.setValue(100)
            if 'unlocked: yes' in bootloader_status.lower():
                return 'Bootloader desbloqueado com sucesso!\nO dispositivo ser├í reiniciado e todos os dados ser├úo apagados.'
        except Exception as e:
            return f'Erro ao desbloquear bootloader: {str(e)}'
        return 'N├úo foi poss├¡vel confirmar o desbloqueio.\nVerifique se:\n1. O desbloqueio foi confirmado no dispositivo\n2. O dispositivo suporta desbloqueio\n3. O desbloqueio OEM est├í habilitado'
    def fix_permissions(self):
        try:
            if not self.check_device():
                return 'Nenhum dispositivo detectado'
            permissions = ['android.permission.READ_EXTERNAL_STORAGE', 'android.permission.WRITE_EXTERNAL_STORAGE', 'android.permission.ACCESS_MEDIA_LOCATION', 'android.permission.MANAGE_EXTERNAL_STORAGE', 'android.permission.PACKAGE_USAGE_STATS', 'android.permission.SYSTEM_ALERT_WINDOW', 'android.permission.WRITE_SECURE_SETTINGS']
            results = []
            for perm in permissions:
                pass
            try:
                result = self._run_adb_command([self.adb_path, 'shell', 'pm', 'grant', 'com.android.systemui', perm])
                results.append(f'Permiss├úo {perm}: OK')
            except:
                results.append(f'Permiss├úo {perm}: Falhou')
            else:
                self._run_adb_command([self.adb_path, 'shell', 'pm', 'reset-permissions'])
                results.append('Reset geral de permiss├Áes: OK')
                self._run_adb_command([self.adb_path, 'shell', 'chmod -R 777 /data/local/tmp'])
                results.append('Permiss├Áes de arquivos tempor├írios: OK')
        except Exception as e:
            raise Exception(f'Erro ao corrigir permiss├Áes: {str(e)}')
        return '\n'.join(results)
    def _run_adb_command_with_progress(self, command):
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, cwd=os.path.dirname(self.adb_path) if self.adb_path else None, startupinfo=self.startupinfo, creationflags=self.creation_flags)
            return process
        except Exception as e:
            raise Exception(f'Erro ao executar comando: {str(e)}')
    def kill_process(self, package_name):
        try:
            if not self.check_device():
                return 'Nenhum dispositivo detectado'
            commands = [f'am force-stop {package_name}', f'killall {package_name}', f'kill $(pidof {package_name})']
            for cmd in commands:
                pass
            try:
                self._run_adb_command([self.adb_path, 'shell', cmd])
            except:
                pass
            else:
                ps_output = self._run_adb_command([self.adb_path, 'shell', 'ps | grep', package_name])
                if package_name in ps_output:
                    return f'N├úo foi poss├¡vel matar o processo {package_name}'
        except Exception as e:
            return f'Erro ao matar processo: {str(e)}'
        return f'Processo {package_name} finalizado com sucesso'
    def list_processes(self):
        try:
            if not self.check_device():
                return 'Nenhum dispositivo detectado'
            ps_output = self._run_adb_command([self.adb_path, 'shell', 'ps -A'])
            processes = []
            for line in ps_output.split('\n')[1:]:
                parts = line.split()
                if len(parts) >= 8:
                    processes.append({'pid': parts[1], 'user': parts[0], 'name': parts[-1], 'cpu': parts[2], 'mem': parts[3]})
            processes.sort(key=(lambda x: float(x['cpu'])), reverse=True)
            output = ['=== Processos em Execu├º├úo ===\n']
            output.append('PID\tCPU%\tMEM\tUSU├üRIO\tPROCESSO')
            output.append('--------------------------------------------------')
            for proc in processes[:20]:
                output.append(f'{proc['pid']}\t{proc['cpu']}%\t{proc['mem']}\t{proc['user']}\t{proc['name']}')
            return '\n'.join(output)
        except Exception as e:
            return f'Erro ao listar processos: {str(e)}'
    def start_log_capture(self, log_file=None):
        if self.logcat_process is not None:
            return 'Captura de logs j├í est├í em andamento'
        if not self.check_device():
            return 'Nenhum dispositivo detectado'
        try:
            if log_file is None:
                log_dir = os.path.join(tempfile.gettempdir(), 'adb_logs')
                os.makedirs(log_dir, exist_ok=True)
                log_file = os.path.join(log_dir, f'logcat_{time.strftime('%Y%m%d_%H%M%S')}.txt')
            self._run_adb_command([self.adb_path, 'logcat', '-c'])
            def capture_logs():
                with open(log_file, 'w', encoding='utf-8') as f:
                    process = subprocess.Popen([self.adb_path, 'logcat'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, cwd=os.path.dirname(self.adb_path), startupinfo=self.startupinfo, creationflags=self.creation_flags)
                    self.logcat_process = process
                    while self.running:
                        line = process.stdout.readline()
                        if line:
                            f.write(line)
                            f.flush()
                            self.log_queue.put(line)
                    process.terminate()
                    self.logcat_process = None
            self.running = True
            self.log_thread = threading.Thread(target=capture_logs)
            self.log_thread.daemon = True
            self.log_thread.start()
            return f'Captura de logs iniciada. Arquivo: {log_file}'
        except Exception as e:
            self.running = False
            self.logcat_process = None
            return f'Erro ao iniciar captura de logs: {str(e)}'
    def stop_log_capture(self):
        if self.logcat_process is None:
            return 'Nenhuma captura de logs em andamento'
        try:
            self.running = False
            if self.log_thread:
                self.log_thread.join(timeout=5)
            if self.logcat_process:
                self.logcat_process.terminate()
                self.logcat_process = None
            return 'Captura de logs finalizada'
        except Exception as e:
            return f'Erro ao parar captura de logs: {str(e)}'
    def get_latest_logs(self, max_lines=100):
        try:
            logs = []
            while not self.log_queue.empty():
                logs.append(self.log_queue.get_nowait())
            return ''.join(logs)
        except:
            return ''
    def get_device_info(self):
        device_info = {}
        try:
            if not self.is_device_connected():
                return 'Nenhum dispositivo conectado'
            model_output = self.execute_adb_command('shell getprop ro.product.model').strip()
            brand_output = self.execute_adb_command('shell getprop ro.product.brand').strip()
            if not model_output or not brand_output:
                return 'N├úo foi poss├¡vel obter informa├º├Áes b├ísicas do dispositivo'
            device_info['model'] = model_output
            device_info['brand'] = brand_output
            android_version = self.execute_adb_command('shell getprop ro.build.version.release').strip()
            device_info['android'] = android_version or 'Desconhecido'
            cpu_info = self.execute_adb_command('shell cat /proc/cpuinfo')
            cpu_model_match = re.search('Hardware\\s+:\\s+(.*)', cpu_info)
            if cpu_model_match:
                device_info['cpu'] = cpu_model_match.group(1).strip()
            else:
                device_info['cpu'] = 'Desconhecido'
            mem_info = self.execute_adb_command('shell cat /proc/meminfo')
            total_mem_match = re.search('MemTotal\\s+:\\s+(\\d+)', mem_info)
            if total_mem_match:
                total_mem_kb = int(total_mem_match.group(1))
                total_mem_mb = total_mem_kb / 1024
                device_info['memory'] = f'{total_mem_mb:.0f} MB'
            else:
                device_info['memory'] = 'Desconhecido'
            battery_info = self.execute_adb_command('shell dumpsys battery')
            battery_level_match = re.search('level: (\\d+)', battery_info)
            if battery_level_match:
                device_info['battery'] = f'{battery_level_match.group(1)}%'
                return device_info
            device_info['battery'] = 'Desconhecido'
            return device_info
        except Exception as e:
            self.logger.error(f'Erro ao obter informa├º├Áes do dispositivo: {str(e)}')
            return f'Erro ao obter informa├º├Áes do dispositivo: {str(e)}'
    def check_system_events(self):
        try:
            if not self.check_device():
                return 'Nenhum dispositivo detectado'
            log_results = []
            found_logs = False
            log_results.append('======================================================================')
            log_results.append('­ƒô▒ RELAT├ôRIO DE DIAGN├ôSTICO DO SISTEMA'.center(70))
            log_results.append('======================================================================')
            log_results.append('\nEste relat├│rio analisa logs e eventos do sistema Android para identificar problemas.')
            log_results.append('Cada se├º├úo cont├®m explica├º├Áes detalhadas para ajudar na interpreta├º├úo dos resultados.')
            log_results.append('----------------------------------------------------------------------\n')
            error_descriptions = {'permission': 'Problemas de permiss├úo - O sistema negou acesso a um recurso', 'crash': 'Crash de aplicativo - Um aplicativo fechou inesperadamente', 'anr': 'ANR (App Not Responding) - Um aplicativo parou de responder', 'failed': 'Falha em opera├º├úo - Uma a├º├úo solicitada n├úo p├┤de ser conclu├¡da', 'exception': 'Exce├º├úo n├úo tratada - Erro de programa├º├úo n├úo capturado', 'out of memory': 'Mem├│ria insuficiente - O dispositivo est├í com pouca RAM dispon├¡vel', 'battery': 'Problema de bateria - H├í um problema com a carga ou estado da bateria', 'temperature': 'Problema de temperatura - O dispositivo est├í muito quente ou frio', 'deadlock': 'Deadlock - Processos travados esperando um pelo outro', 'watchdog': 'Watchdog timeout - Um processo demorou muito para responder', 'fatal': 'Erro fatal - Problema grave no sistema ou aplicativo', 'denied': 'Acesso negado - Uma opera├º├úo foi bloqueada por seguran├ºa'}
            try:
                result = self._run_adb_command([self.adb_path, 'shell', 'logcat -d -b system'])
                if result and len(result.strip()) > 10:
                    important_lines = []
                    error_count = 0
                    warning_count = 0
                    error_types = {}
                    for line in result.split('\n'):
                        if 'E/' not in line and 'error' not in line.lower():
                            if 'exception' in line.lower():
                                important_lines.append(line)
                                error_count += 1
                                for error_key, description in error_descriptions.items():
                                    if error_key not in line.lower():
                                        continue
                                    if error_key not in error_types:
                                        error_types[error_key] = {'count': 1, 'description': description}
                                    else:
                                        error_types[error_key]['count'] += 1
                            elif 'W/' in line or 'warning' in line.lower():
                                important_lines.append(line)
                                warning_count += 1
                    if len(important_lines) > 30:
                        important_lines = important_lines[:30]
                        important_lines.append('... (mais linhas omitidas) ...')
                    log_results.append('\n­ƒôè RESUMO DE LOGS DO SISTEMA')
                    log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                    log_results.append('Ôòæ ' + 'O que ├® isto?'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'Logs do sistema Android que mostram erros e avisos dos aplicativos'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'e componentes do sistema operacional.'.ljust(66) + ' Ôòæ')
                    log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                    log_results.append(f'ÔØî Erros encontrados: {error_count}')
                    log_results.append(f'ÔÜá´©Å Avisos encontrados: {warning_count}')
                    if error_types:
                        log_results.append('\n­ƒöì TIPOS DE ERROS DETECTADOS:')
                        log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                        for error_key, data in error_types.items():
                            log_results.append(f'Ôòæ ÔÇó {data['description']} ({data['count']} ocorr├¬ncias)'.ljust(69) + 'Ôòæ')
                        log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                    if important_lines:
                        log_results.append('\n­ƒöì EVENTOS IMPORTANTES DO SISTEMA')
                        log_results.append('----------------------------------------------------------------------')
                        log_results.append('­ƒæë O que significam estes logs?')
                        log_results.append('   E/ = Erro | W/ = Aviso | I/ = Informa├º├úo')
                        log_results.append('   Os c├│digos ap├│s a barra (/) indicam o componente que gerou o log.')
                        log_results.append('----------------------------------------------------------------------')
                        log_results.append('\n'.join(important_lines))
                    else:
                        log_results.append('\nÔ£à Nenhum evento cr├¡tico encontrado nos logs do sistema')
                        log_results.append('   Isto ├® um bom sinal! O sistema est├í funcionando normalmente.')
                    found_logs = True
            except Exception as e:
                log_results.append(f'\nÔÜá´©Å N├úo foi poss├¡vel ler logs do sistema: {str(e)}')
                log_results.append('   Por que isto acontece? O dispositivo pode ter restri├º├Áes de acesso')
                log_results.append('   aos logs ou a depura├º├úo USB pode estar com problemas.')
            else:
                kernel_issues_by_type = {}
        except Exception as e:
            return f'Erro ao verificar eventos do sistema:\n{str(e)}\n\nVerifique se:\n1. O dispositivo est├í respondendo\n2. A conex├úo USB est├í est├ível\n3. A depura├º├úo USB continua ativada'
        try:
            result = self._run_adb_command([self.adb_path, 'shell', 'dmesg'])
            if result and len(result.strip()) > 10:
                kernel_issues = []
                kernel_terms = {'error': 'Erro geral no kernel', 'fail': 'Falha em uma opera├º├úo', 'denied': 'Permiss├úo negada pelo sistema', 'cannot': 'Opera├º├úo imposs├¡vel', 'panic': 'Kernel Panic - erro muito grave', 'emerg': 'Emerg├¬ncia no sistema', 'alert': 'Alerta de funcionamento', 'critical': 'Problema cr├¡tico', 'oom_kill': 'Out of Memory Kill - Processo eliminado por falta de mem├│ria', 'segfault': 'Segmentation Fault - Acesso inv├ílido ├á mem├│ria', 'i/o error': 'Erro de entrada/sa├¡da', 'blocked for': 'Processo bloqueado por muito tempo'}
                for line in result.split('\n'):
                    lower_line = line.lower()
                    for term, description in kernel_terms.items():
                        if not term in lower_line:
                            continue
                        kernel_issues.append(line)
                        if term not in kernel_issues_by_type:
                            kernel_issues_by_type[term] = {'count': 1, 'description': description}
                        else:
                            kernel_issues_by_type[term]['count'] += 1
                        break
                if len(kernel_issues) > 20:
                    kernel_issues = kernel_issues[:20]
                    kernel_issues.append('... (mais linhas omitidas) ...')
                log_results.append('\n­ƒûÑ´©Å LOGS DO KERNEL (DMESG)')
                log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                log_results.append('Ôòæ ' + 'O que ├® isto?'.ljust(66) + ' Ôòæ')
                log_results.append('Ôòæ ' + 'Logs do n├║cleo do sistema (kernel) que mostram problemas de'.ljust(66) + ' Ôòæ')
                log_results.append('Ôòæ ' + 'hardware, permiss├Áes e acessos a recursos de baixo n├¡vel.'.ljust(66) + ' Ôòæ')
                log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                if kernel_issues_by_type:
                    log_results.append('\nÔÜá´©Å TIPOS DE PROBLEMAS NO KERNEL:')
                    log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                    for term, data in kernel_issues_by_type.items():
                        log_results.append(f'Ôòæ ÔÇó {data['description']} ({data['count']} ocorr├¬ncias)'.ljust(69) + 'Ôòæ')
                    log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                    log_results.append('\n­ƒæë O que isso significa para voc├¬?')
                    log_results.append('   Problemas no kernel podem causar travamentos, reinicializa├º├Áes')
                    log_results.append('   inesperadas ou funcionamento inst├ível do dispositivo.')
                if kernel_issues:
                    log_results.append('\nÔÜá´©Å Problemas identificados no kernel:')
                    log_results.append('----------------------------------------------------------------------')
                    log_results.append('\n'.join(kernel_issues))
                else:
                    log_results.append('\nÔ£à Nenhum problema cr├¡tico encontrado nos logs do kernel')
                    log_results.append('   Os componentes de baixo n├¡vel do sistema est├úo funcionando corretamente.')
                found_logs = True
        except Exception as e:
            log_results.append(f'\nÔÜá´©Å N├úo foi poss├¡vel ler logs do kernel: {str(e)}')
            log_results.append('   Por que isto acontece? Alguns dispositivos restringem o acesso')
            log_results.append('   aos logs do kernel por raz├Áes de seguran├ºa.')
        crash_count = 0
        anr_count = 0
        error_count = 0
        crash_apps = set()
        anr_apps = set()
        try:
            result = self._run_adb_command([self.adb_path, 'shell', 'dumpsys dropbox --print'])
            if result and len(result.strip()) > 10:
                crash_events = []
                anr_events = []
                other_events = []
                for line in result.split('\n'):
                    if 'CRASH' in line:
                        crash_events.append(line)
                        crash_count += 1
                        app_match = re.search('data_app_crash/([^/]+)', line)
                        if app_match:
                            crash_apps.add(app_match.group(1))
                    elif 'ANR' in line:
                        anr_events.append(line)
                        anr_count += 1
                        app_match = re.search('data_app_anr/([^/]+)', line)
                        if app_match:
                            anr_apps.add(app_match.group(1))
                    elif 'ERROR' in line or 'EXCEPTION' in line:
                        other_events.append(line)
                        error_count += 1
                log_results.append('\n­ƒô▒ EVENTOS DO SISTEMA (DROPBOX)')
                log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                log_results.append('Ôòæ ' + 'O que ├® isto?'.ljust(66) + ' Ôòæ')
                log_results.append('Ôòæ ' + 'Logs de eventos cr├¡ticos como crashes, aplicativos que n├úo'.ljust(66) + ' Ôòæ')
                log_results.append('Ôòæ ' + 'respondem (ANRs) e outros erros significativos do sistema.'.ljust(66) + ' Ôòæ')
                log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                if crash_events:
                    log_results.append('\n­ƒÆÑ CRASHES DETECTADOS:')
                    log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                    log_results.append('Ôòæ ' + 'O que s├úo crashes?'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'Crashes ocorrem quando um aplicativo para de funcionar'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'abruptamente devido a um erro grave no c├│digo.'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'Impacto: Perda de dados n├úo salvos e interrup├º├úo do uso.'.ljust(66) + ' Ôòæ')
                    log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                    log_results.append('\n'.join(crash_events[:10]))
                    if len(crash_events) > 10:
                        log_results.append(f'... (mais {len(crash_events) - 10} eventos omitidos) ...')
                if anr_events:
                    log_results.append('\nÔÅ▒´©Å ANRs (Application Not Responding):')
                    log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                    log_results.append('Ôòæ ' + 'O que s├úo ANRs?'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + "Ocorrem quando um aplicativo 'congela' e n├úo responde ├ás".ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'intera├º├Áes do usu├írio por mais de 5 segundos.'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'Impacto: Frustra├º├úo do usu├írio e perda de produtividade.'.ljust(66) + ' Ôòæ')
                    log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                    log_results.append('\n'.join(anr_events[:10]))
                    if len(anr_events) > 10:
                        log_results.append(f'... (mais {len(anr_events) - 10} eventos omitidos) ...')
                if other_events:
                    log_results.append('\nÔÜá´©Å OUTROS ERROS:')
                    log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                    log_results.append('Ôòæ ' + 'O que s├úo esses erros?'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'Problemas n├úo categorizados que afetam o funcionamento do'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'sistema ou aplicativos de forma irregular.'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'Impacto: Comportamentos inesperados ou falhas diversas.'.ljust(66) + ' Ôòæ')
                    log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                    log_results.append('\n'.join(other_events[:10]))
                    if len(other_events) > 10:
                        log_results.append(f'... (mais {len(other_events) - 10} eventos omitidos) ...')
                if not crash_events and not anr_events and not other_events:
                    log_results.append('Ô£à Nenhum evento cr├¡tico encontrado nos logs do sistema')
                    log_results.append('   Isto ├® um ├│timo sinal! Significa que o sistema est├í operando')
                    log_results.append('   corretamente sem falhas graves recentes.')
                found_logs = True
        except Exception as e:
            log_results.append(f'\nÔÜá´©Å N├úo foi poss├¡vel ler eventos do sistema: {str(e)}')
            log_results.append('   Por que isto acontece? O dispositivo pode ter restri├º├Áes de acesso')
            log_results.append('   aos logs do sistema ou problemas de comunica├º├úo.')
        battery_dict = {}
        try:
            battery_info = self._run_adb_command([self.adb_path, 'shell', 'dumpsys battery'])
            if battery_info:
                log_results.append('\n­ƒöï INFORMA├ç├òES DA BATERIA')
                log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                log_results.append('Ôòæ ' + 'O que ├® isto?'.ljust(66) + ' Ôòæ')
                log_results.append('Ôòæ ' + 'Dados t├®cnicos sobre o estado atual da bateria e como est├í'.ljust(66) + ' Ôòæ')
                log_results.append('Ôòæ ' + 'sendo utilizada pelo dispositivo.'.ljust(66) + ' Ôòæ')
                log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                for line in battery_info.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        battery_dict[key.strip()] = value.strip()
                if battery_dict:
                    power_source = 'AC' if battery_dict.get('AC powered') == 'true' else 'USB' if battery_dict.get('USB powered') == 'true' else 'Bateria'
                    health_map = {'1': 'Desconhecido', '2': 'Boa', '3': 'Superaquecida', '4': 'Danificada', '5': 'Sobretens├úo', '6': 'Falha', '7': 'Fria'}
                    health_code = battery_dict.get('health', '1')
                    health = health_map.get(health_code, 'Desconhecido')
                    log_results.append('')
                    log_results.append('ÔöîÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÉ')
                    log_results.append(f'Ôöé ­ƒöî Fonte de energia: {power_source.ljust(48)}Ôöé')
                    log_results.append('Ôöé  Ô×£ Indica se o dispositivo est├í usando energia da bateria   Ôöé')
                    log_results.append('Ôöé    ou est├í conectado ├á energia.                             Ôöé')
                    log_results.append('Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ')
                    log_results.append(f'Ôöé ­ƒôè N├¡vel: {battery_dict.get('level', 'N/A')}%'.ljust(67) + 'Ôöé')
                    log_results.append('Ôöé  Ô×£ A porcentagem atual de carga da bateria.                 Ôöé')
                    log_results.append('Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ')
                    log_results.append(f'Ôöé ÔØñ´©Å Sa├║de: {health} (C├│digo: {health_code})'.ljust(67) + 'Ôöé')
                    log_results.append('Ôöé  Ô×£ Condi├º├úo geral da bateria e sua capacidade de manter     Ôöé')
                    log_results.append('Ôöé    carga.                                                   Ôöé')
            try:
                temp = float(battery_dict.get('temperature', '0')) / 10
                log_results.append('Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ')
                log_results.append(f'Ôöé ­ƒîí´©Å Temperatura: {temp:.1f}┬░C'.ljust(67) + 'Ôöé')
                log_results.append('Ôöé  Ô×£ Temperatura atual da bateria. Valores acima de 40┬░C s├úo   Ôöé')
                log_results.append('Ôöé    preocupantes.                                             Ôöé')
            except:
                log_results.append('Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ')
                log_results.append(f'Ôöé ­ƒîí´©Å Temperatura: {battery_dict.get('temperature', 'N/A')}'.ljust(67) + 'Ôöé')
                log_results.append('Ôöé  Ô×£ Temperatura atual da bateria em unidades do sistema.      Ôöé')
            else:
                try:
                    try:
                        try:
                            try:
                                voltage = float(battery_dict.get('voltage', '0')) / 1000
                                log_results.append('Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ')
                                log_results.append(f'Ôöé ÔÜí Voltagem: {voltage:.2f}V'.ljust(67) + 'Ôöé')
                                log_results.append('Ôöé  Ô×£ Tens├úo atual da bateria. Valores abaixo do normal podem   Ôöé')
                                log_results.append('Ôöé    indicar problemas.                                        Ôöé')
                            except Exception as e:
                                log_results.append(f'\nÔÜá´©Å N├úo foi poss├¡vel ler informa├º├Áes da bateria: {str(e)}')
                                log_results.append('   Por que isto acontece? Pode haver restri├º├Áes de permiss├úo para')
                                log_results.append('   acessar as informa├º├Áes da bateria ou problemas de comunica├º├úo.')
                        except:
                            log_results.append('Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ')
                            log_results.append(f'Ôöé ÔÜí Voltagem: {battery_dict.get('voltage', 'N/A')}'.ljust(67) + 'Ôöé')
                            log_results.append('Ôöé  Ô×£ Tens├úo el├®trica atual fornecida pela bateria.             Ôöé')
                    except Exception as e:
                        log_results.append(f'\nÔÜá´©Å N├úo foi poss├¡vel ler informa├º├Áes da bateria: {str(e)}')
                        log_results.append('   Por que isto acontece? Pode haver restri├º├Áes de permiss├úo para')
                        log_results.append('   acessar as informa├º├Áes da bateria ou problemas de comunica├º├úo.')
                except Exception as e:
                    return f'Erro ao verificar eventos do sistema:\n{str(e)}\n\nVerifique se:\n1. O dispositivo est├í respondendo\n2. A conex├úo USB est├í est├ível\n3. A depura├º├úo USB continua ativada'
                log_results.append('Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ')
                log_results.append(f'Ôöé ­ƒö¼ Tecnologia: {battery_dict.get('technology', 'N/A')}'.ljust(67) + 'Ôöé')
                log_results.append('Ôöé  Ô×£ O tipo de qu├¡mica utilizada na bateria (Li-Ion, Li-Poly).    Ôöé')
                log_results.append('ÔööÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÿ')
                found_logs = True
        except Exception as e:
            return f'Erro ao verificar eventos do sistema:\n{str(e)}\n\nVerifique se:\n1. O dispositivo est├í respondendo\n2. A conex├úo USB est├í est├ível\n3. A depura├º├úo USB continua ativada'
        return '\n'.join(log_results)
    def panic_android(self, parent_window=None):
        if not self.check_device():
            return 'Nenhum dispositivo detectado. Conecte o dispositivo e tente novamente.'
        progress = QProgressDialog('Gerando Bugreport...', None, 0, 100, parent_window)
        progress.setWindowModality(Qt.WindowModal)
        progress.setAutoClose(True)
        progress.setValue(0)
        try:
            progress.setLabelText('Coletando informa├º├Áes do dispositivo...')
            device_info = self.check_device_info()
            progress.setValue(10)
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            default_filename = f'bugreport_{timestamp}.zip'
            save_path, _ = QFileDialog.getSaveFileName(parent_window, 'Salvar Bugreport', default_filename, 'Arquivos ZIP (*.zip)')
            if not save_path:
                return 'Opera├º├úo cancelada pelo usu├írio.'
            progress.setLabelText('Gerando bugreport completo...\nIsso pode levar alguns minutos.')
            progress.setValue(30)
            self._run_adb_command([self.adb_path, 'bugreport', save_path])
            progress.setValue(90)
            if os.path.exists(save_path):
                progress.setValue(100)
                return f'Bugreport gerado com sucesso!\n\nArquivo salvo em:\n{save_path}\n\nEste arquivo cont├®m informa├º├Áes detalhadas do sistema\nque podem ajudar no diagn├│stico de problemas.'
            raise Exception('Falha ao gerar o arquivo de bugreport')
        except Exception as e:
            return f'Erro durante a gera├º├úo do bugreport: {str(e)}'
    def filter_logcat(self, filter_type='all', keywords=None):
        try:
            buffer_arg = {'all': '', 'system': '-b system', 'main': '-b main', 'crash': '-b crash', 'radio': '-b radio', 'events': '-b events'}.get(filter_type, '')
            cmd = [self.adb_path, 'logcat', '-d']
            if buffer_arg:
                cmd.extend(buffer_arg.split())
            output = self._run_adb_command(cmd)
            if keywords:
                filtered_lines = []
                for line in output.split('\n'):
                    if any((keyword.lower() in line.lower() for keyword in keywords)):
                        filtered_lines.append(line)
                return '\n'.join(filtered_lines)
            return output
        except Exception as e:
            raise Exception(f'Erro ao filtrar logs: {str(e)}')
    def analyze_system_errors(self):
        try:
            system_logs = self.filter_logcat('system')
            crash_logs = self.filter_logcat('crash')
            error_patterns = {'ANR': 'ANR in (\\S+)', 'FATAL EXCEPTION': 'FATAL EXCEPTION: .*?(?=\\n)', 'System.err': 'System.err: .*?(?=\\n)', 'SIGSEGV': 'SIGSEGV.*?(?=\\n)', 'OutOfMemoryError': 'OutOfMemoryError.*?(?=\\n)'}
            results = {'anrs': [], 'crashes': [], 'system_errors': [], 'summary': {'total_anrs': 0, 'total_crashes': 0, 'total_errors': 0}}
            for line in system_logs.split('\n'):
                if 'ANR in' in line:
                    match = re.search(error_patterns['ANR'], line)
                    if match:
                        results['anrs'].append({'package': match.group(1), 'timestamp': line.split()[0:2], 'full_log': line})
                        results['summary']['total_anrs'] += 1
                if any((err in line for err in ('FATAL EXCEPTION', 'System.err', 'SIGSEGV'))):
                    results['system_errors'].append(line)
                    results['summary']['total_errors'] += 1
            for line in crash_logs.split('\n'):
                if any((pattern in line for pattern in error_patterns.values())):
                    results['crashes'].append(line)
                    results['summary']['total_crashes'] += 1
            return self.format_error_analysis(results)
        except Exception as e:
            raise Exception(f'Erro ao analisar erros do sistema: {str(e)}')
    def format_error_analysis(self, results):
        output = []
        output.append('=== An├ílise de Erros do Sistema ===')
        output.append('\nResumo:')
        output.append(f'ÔÇó Total de ANRs: {results['summary']['total_anrs']}')
        output.append(f'ÔÇó Total de Crashes: {results['summary']['total_crashes']}')
        output.append(f'ÔÇó Total de Erros de Sistema: {results['summary']['total_errors']}')
        if results['anrs']:
            output.append('\n=== ANRs (Application Not Responding) ===')
            for anr in results['anrs']:
                output.append(f'\nAplicativo: {anr['package']}')
                output.append(f'Timestamp: {' '.join(anr['timestamp'])}')
        if results['crashes']:
            output.append('\n=== Crashes ===')
            for crash in results['crashes'][:10]:
                output.append(f'\nÔÇó {crash}')
        if results['system_errors']:
            output.append('\n=== Erros de Sistema ===')
            for error in results['system_errors'][:10]:
                output.append(f'\nÔÇó {error}')
        if not any([results['anrs'], results['crashes'], results['system_errors']]):
            output.append('\nNenhum erro cr├¡tico encontrado nos logs analisados.')
        return '\n'.join(output)
    def unlock_bootloader(self, parent_window=None):
        warning = 'ATEN├ç├âO!\n\nO desbloqueio do bootloader ir├í:\n1. Apagar TODOS os dados do dispositivo\n2. Pode invalidar a garantia\n3. ├ë um processo irrevers├¡vel\n\nCertifique-se de:\n1. Ter feito backup de todos os dados\n2. O dispositivo estar com a bateria carregada\n3. Ter habilitado o desbloqueio OEM nas configura├º├Áes\n\nDeseja continuar?'
        reply = QMessageBox.warning(parent_window, 'Desbloquear Bootloader', warning, QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No:
            return 'Opera├º├úo cancelada pelo usu├írio.'
        progress = QProgressDialog('Desbloqueando bootloader...', None, 0, 100, parent_window)
        progress.setWindowModality(Qt.WindowModal)
        progress.setAutoClose(True)
        progress.setValue(0)
        try:
            progress.setLabelText('Verificando estado do dispositivo...')
            if not self.check_fastboot_device():
                return 'Dispositivo n├úo est├í em modo fastboot.\n1. Ative o modo desenvolvedor\n2. Habilite o desbloqueio OEM\n3. Reinicie em modo fastboot'
            progress.setValue(20)
            progress.setLabelText('Verificando status do bootloader...')
            bootloader_status = self._run_fastboot_command([self.fastboot_path, 'getvar', 'unlocked'])
            progress.setValue(40)
            if 'unlocked: yes' in bootloader_status.lower():
                return 'Bootloader j├í est├í desbloqueado!'
            progress.setLabelText('Executando comando de desbloqueio...')
            self._run_fastboot_command([self.fastboot_path, 'flashing', 'unlock'])
            progress.setValue(60)
            progress.setLabelText('Aguardando confirma├º├úo no dispositivo...\nUse as teclas de volume e power para confirmar')
            time.sleep(5)
            progress.setValue(80)
            progress.setLabelText('Verificando resultado...')
            bootloader_status = self._run_fastboot_command([self.fastboot_path, 'getvar', 'unlocked'])
            progress.setValue(100)
            if 'unlocked: yes' in bootloader_status.lower():
                return 'Bootloader desbloqueado com sucesso!\nO dispositivo ser├í reiniciado e todos os dados ser├úo apagados.'
        except Exception as e:
            return f'Erro ao desbloquear bootloader: {str(e)}'
        return 'N├úo foi poss├¡vel confirmar o desbloqueio.\nVerifique se:\n1. O desbloqueio foi confirmado no dispositivo\n2. O dispositivo suporta desbloqueio\n3. O desbloqueio OEM est├í habilitado'
    def fix_permissions(self):
        try:
            if not self.check_device():
                return 'Nenhum dispositivo detectado'
            permissions = ['android.permission.READ_EXTERNAL_STORAGE', 'android.permission.WRITE_EXTERNAL_STORAGE', 'android.permission.ACCESS_MEDIA_LOCATION', 'android.permission.MANAGE_EXTERNAL_STORAGE', 'android.permission.PACKAGE_USAGE_STATS', 'android.permission.SYSTEM_ALERT_WINDOW', 'android.permission.WRITE_SECURE_SETTINGS']
            results = []
            for perm in permissions:
                pass
            try:
                result = self._run_adb_command([self.adb_path, 'shell', 'pm', 'grant', 'com.android.systemui', perm])
                results.append(f'Permiss├úo {perm}: OK')
            except:
                results.append(f'Permiss├úo {perm}: Falhou')
            else:
                self._run_adb_command([self.adb_path, 'shell', 'pm', 'reset-permissions'])
                results.append('Reset geral de permiss├Áes: OK')
                self._run_adb_command([self.adb_path, 'shell', 'chmod -R 777 /data/local/tmp'])
                results.append('Permiss├Áes de arquivos tempor├írios: OK')
        except Exception as e:
            raise Exception(f'Erro ao corrigir permiss├Áes: {str(e)}')
        return '\n'.join(results)
    def _run_adb_command_with_progress(self, command):
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, cwd=os.path.dirname(self.adb_path) if self.adb_path else None, startupinfo=self.startupinfo, creationflags=self.creation_flags)
            return process
        except Exception as e:
            raise Exception(f'Erro ao executar comando: {str(e)}')
    def kill_process(self, package_name):
        try:
            if not self.check_device():
                return 'Nenhum dispositivo detectado'
            commands = [f'am force-stop {package_name}', f'killall {package_name}', f'kill $(pidof {package_name})']
            for cmd in commands:
                pass
            try:
                self._run_adb_command([self.adb_path, 'shell', cmd])
            except:
                pass
            else:
                ps_output = self._run_adb_command([self.adb_path, 'shell', 'ps | grep', package_name])
                if package_name in ps_output:
                    return f'N├úo foi poss├¡vel matar o processo {package_name}'
        except Exception as e:
            return f'Erro ao matar processo: {str(e)}'
        return f'Processo {package_name} finalizado com sucesso'
    def list_processes(self):
        try:
            if not self.check_device():
                return 'Nenhum dispositivo detectado'
            ps_output = self._run_adb_command([self.adb_path, 'shell', 'ps -A'])
            processes = []
            for line in ps_output.split('\n')[1:]:
                parts = line.split()
                if len(parts) >= 8:
                    processes.append({'pid': parts[1], 'user': parts[0], 'name': parts[-1], 'cpu': parts[2], 'mem': parts[3]})
            processes.sort(key=(lambda x: float(x['cpu'])), reverse=True)
            output = ['=== Processos em Execu├º├úo ===\n']
            output.append('PID\tCPU%\tMEM\tUSU├üRIO\tPROCESSO')
            output.append('--------------------------------------------------')
            for proc in processes[:20]:
                output.append(f'{proc['pid']}\t{proc['cpu']}%\t{proc['mem']}\t{proc['user']}\t{proc['name']}')
            return '\n'.join(output)
        except Exception as e:
            return f'Erro ao listar processos: {str(e)}'
    def start_log_capture(self, log_file=None):
        if self.logcat_process is not None:
            return 'Captura de logs j├í est├í em andamento'
        if not self.check_device():
            return 'Nenhum dispositivo detectado'
        try:
            if log_file is None:
                log_dir = os.path.join(tempfile.gettempdir(), 'adb_logs')
                os.makedirs(log_dir, exist_ok=True)
                log_file = os.path.join(log_dir, f'logcat_{time.strftime('%Y%m%d_%H%M%S')}.txt')
            self._run_adb_command([self.adb_path, 'logcat', '-c'])
            def capture_logs():
                with open(log_file, 'w', encoding='utf-8') as f:
                    process = subprocess.Popen([self.adb_path, 'logcat'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, cwd=os.path.dirname(self.adb_path), startupinfo=self.startupinfo, creationflags=self.creation_flags)
                    self.logcat_process = process
                    while self.running:
                        line = process.stdout.readline()
                        if line:
                            f.write(line)
                            f.flush()
                            self.log_queue.put(line)
                    process.terminate()
                    self.logcat_process = None
            self.running = True
            self.log_thread = threading.Thread(target=capture_logs)
            self.log_thread.daemon = True
            self.log_thread.start()
            return f'Captura de logs iniciada. Arquivo: {log_file}'
        except Exception as e:
            self.running = False
            self.logcat_process = None
            return f'Erro ao iniciar captura de logs: {str(e)}'
    def stop_log_capture(self):
        if self.logcat_process is None:
            return 'Nenhuma captura de logs em andamento'
        try:
            self.running = False
            if self.log_thread:
                self.log_thread.join(timeout=5)
            if self.logcat_process:
                self.logcat_process.terminate()
                self.logcat_process = None
            return 'Captura de logs finalizada'
        except Exception as e:
            return f'Erro ao parar captura de logs: {str(e)}'
    def get_latest_logs(self, max_lines=100):
        try:
            logs = []
            while not self.log_queue.empty():
                logs.append(self.log_queue.get_nowait())
            return ''.join(logs)
        except:
            return ''
    def get_device_info(self):
        device_info = {}
        try:
            if not self.is_device_connected():
                return 'Nenhum dispositivo conectado'
            model_output = self.execute_adb_command('shell getprop ro.product.model').strip()
            brand_output = self.execute_adb_command('shell getprop ro.product.brand').strip()
            if not model_output or not brand_output:
                return 'N├úo foi poss├¡vel obter informa├º├Áes b├ísicas do dispositivo'
            device_info['model'] = model_output
            device_info['brand'] = brand_output
            android_version = self.execute_adb_command('shell getprop ro.build.version.release').strip()
            device_info['android'] = android_version or 'Desconhecido'
            cpu_info = self.execute_adb_command('shell cat /proc/cpuinfo')
            cpu_model_match = re.search('Hardware\\s+:\\s+(.*)', cpu_info)
            if cpu_model_match:
                device_info['cpu'] = cpu_model_match.group(1).strip()
            else:
                device_info['cpu'] = 'Desconhecido'
            mem_info = self.execute_adb_command('shell cat /proc/meminfo')
            total_mem_match = re.search('MemTotal\\s+:\\s+(\\d+)', mem_info)
            if total_mem_match:
                total_mem_kb = int(total_mem_match.group(1))
                total_mem_mb = total_mem_kb / 1024
                device_info['memory'] = f'{total_mem_mb:.0f} MB'
            else:
                device_info['memory'] = 'Desconhecido'
            battery_info = self.execute_adb_command('shell dumpsys battery')
            battery_level_match = re.search('level: (\\d+)', battery_info)
            if battery_level_match:
                device_info['battery'] = f'{battery_level_match.group(1)}%'
                return device_info
            device_info['battery'] = 'Desconhecido'
            return device_info
        except Exception as e:
            self.logger.error(f'Erro ao obter informa├º├Áes do dispositivo: {str(e)}')
            return f'Erro ao obter informa├º├Áes do dispositivo: {str(e)}'
    def check_system_events(self):
        try:
            if not self.check_device():
                return 'Nenhum dispositivo detectado'
            log_results = []
            found_logs = False
            log_results.append('======================================================================')
            log_results.append('­ƒô▒ RELAT├ôRIO DE DIAGN├ôSTICO DO SISTEMA'.center(70))
            log_results.append('======================================================================')
            log_results.append('\nEste relat├│rio analisa logs e eventos do sistema Android para identificar problemas.')
            log_results.append('Cada se├º├úo cont├®m explica├º├Áes detalhadas para ajudar na interpreta├º├úo dos resultados.')
            log_results.append('----------------------------------------------------------------------\n')
            error_descriptions = {'permission': 'Problemas de permiss├úo - O sistema negou acesso a um recurso', 'crash': 'Crash de aplicativo - Um aplicativo fechou inesperadamente', 'anr': 'ANR (App Not Responding) - Um aplicativo parou de responder', 'failed': 'Falha em opera├º├úo - Uma a├º├úo solicitada n├úo p├┤de ser conclu├¡da', 'exception': 'Exce├º├úo n├úo tratada - Erro de programa├º├úo n├úo capturado', 'out of memory': 'Mem├│ria insuficiente - O dispositivo est├í com pouca RAM dispon├¡vel', 'battery': 'Problema de bateria - H├í um problema com a carga ou estado da bateria', 'temperature': 'Problema de temperatura - O dispositivo est├í muito quente ou frio', 'deadlock': 'Deadlock - Processos travados esperando um pelo outro', 'watchdog': 'Watchdog timeout - Um processo demorou muito para responder', 'fatal': 'Erro fatal - Problema grave no sistema ou aplicativo', 'denied': 'Acesso negado - Uma opera├º├úo foi bloqueada por seguran├ºa'}
            try:
                result = self._run_adb_command([self.adb_path, 'shell', 'logcat -d -b system'])
                if result and len(result.strip()) > 10:
                    important_lines = []
                    error_count = 0
                    warning_count = 0
                    error_types = {}
                    for line in result.split('\n'):
                        if 'E/' not in line and 'error' not in line.lower():
                            if 'exception' in line.lower():
                                important_lines.append(line)
                                error_count += 1
                                for error_key, description in error_descriptions.items():
                                    if error_key not in line.lower():
                                        continue
                                    if error_key not in error_types:
                                        error_types[error_key] = {'count': 1, 'description': description}
                                    else:
                                        error_types[error_key]['count'] += 1
                            elif 'W/' in line or 'warning' in line.lower():
                                important_lines.append(line)
                                warning_count += 1
                    if len(important_lines) > 30:
                        important_lines = important_lines[:30]
                        important_lines.append('... (mais linhas omitidas) ...')
                    log_results.append('\n­ƒôè RESUMO DE LOGS DO SISTEMA')
                    log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                    log_results.append('Ôòæ ' + 'O que ├® isto?'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'Logs do sistema Android que mostram erros e avisos dos aplicativos'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'e componentes do sistema operacional.'.ljust(66) + ' Ôòæ')
                    log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                    log_results.append(f'ÔØî Erros encontrados: {error_count}')
                    log_results.append(f'ÔÜá´©Å Avisos encontrados: {warning_count}')
                    if error_types:
                        log_results.append('\n­ƒöì TIPOS DE ERROS DETECTADOS:')
                        log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                        for error_key, data in error_types.items():
                            log_results.append(f'Ôòæ ÔÇó {data['description']} ({data['count']} ocorr├¬ncias)'.ljust(69) + 'Ôòæ')
                        log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                    if important_lines:
                        log_results.append('\n­ƒöì EVENTOS IMPORTANTES DO SISTEMA')
                        log_results.append('----------------------------------------------------------------------')
                        log_results.append('­ƒæë O que significam estes logs?')
                        log_results.append('   E/ = Erro | W/ = Aviso | I/ = Informa├º├úo')
                        log_results.append('   Os c├│digos ap├│s a barra (/) indicam o componente que gerou o log.')
                        log_results.append('----------------------------------------------------------------------')
                        log_results.append('\n'.join(important_lines))
                    else:
                        log_results.append('\nÔ£à Nenhum evento cr├¡tico encontrado nos logs do sistema')
                        log_results.append('   Isto ├® um bom sinal! O sistema est├í funcionando normalmente.')
                    found_logs = True
            except Exception as e:
                log_results.append(f'\nÔÜá´©Å N├úo foi poss├¡vel ler logs do sistema: {str(e)}')
                log_results.append('   Por que isto acontece? O dispositivo pode ter restri├º├Áes de acesso')
                log_results.append('   aos logs ou a depura├º├úo USB pode estar com problemas.')
            else:
                kernel_issues_by_type = {}
        except Exception as e:
            return f'Erro ao verificar eventos do sistema:\n{str(e)}\n\nVerifique se:\n1. O dispositivo est├í respondendo\n2. A conex├úo USB est├í est├ível\n3. A depura├º├úo USB continua ativada'
        try:
            result = self._run_adb_command([self.adb_path, 'shell', 'dmesg'])
            if result and len(result.strip()) > 10:
                kernel_issues = []
                kernel_terms = {'error': 'Erro geral no kernel', 'fail': 'Falha em uma opera├º├úo', 'denied': 'Permiss├úo negada pelo sistema', 'cannot': 'Opera├º├úo imposs├¡vel', 'panic': 'Kernel Panic - erro muito grave', 'emerg': 'Emerg├¬ncia no sistema', 'alert': 'Alerta de funcionamento', 'critical': 'Problema cr├¡tico', 'oom_kill': 'Out of Memory Kill - Processo eliminado por falta de mem├│ria', 'segfault': 'Segmentation Fault - Acesso inv├ílido ├á mem├│ria', 'i/o error': 'Erro de entrada/sa├¡da', 'blocked for': 'Processo bloqueado por muito tempo'}
                for line in result.split('\n'):
                    lower_line = line.lower()
                    for term, description in kernel_terms.items():
                        if not term in lower_line:
                            continue
                        kernel_issues.append(line)
                        if term not in kernel_issues_by_type:
                            kernel_issues_by_type[term] = {'count': 1, 'description': description}
                        else:
                            kernel_issues_by_type[term]['count'] += 1
                        break
                if len(kernel_issues) > 20:
                    kernel_issues = kernel_issues[:20]
                    kernel_issues.append('... (mais linhas omitidas) ...')
                log_results.append('\n­ƒûÑ´©Å LOGS DO KERNEL (DMESG)')
                log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                log_results.append('Ôòæ ' + 'O que ├® isto?'.ljust(66) + ' Ôòæ')
                log_results.append('Ôòæ ' + 'Logs do n├║cleo do sistema (kernel) que mostram problemas de'.ljust(66) + ' Ôòæ')
                log_results.append('Ôòæ ' + 'hardware, permiss├Áes e acessos a recursos de baixo n├¡vel.'.ljust(66) + ' Ôòæ')
                log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                if kernel_issues_by_type:
                    log_results.append('\nÔÜá´©Å TIPOS DE PROBLEMAS NO KERNEL:')
                    log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                    for term, data in kernel_issues_by_type.items():
                        log_results.append(f'Ôòæ ÔÇó {data['description']} ({data['count']} ocorr├¬ncias)'.ljust(69) + 'Ôòæ')
                    log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                    log_results.append('\n­ƒæë O que isso significa para voc├¬?')
                    log_results.append('   Problemas no kernel podem causar travamentos, reinicializa├º├Áes')
                    log_results.append('   inesperadas ou funcionamento inst├ível do dispositivo.')
                if kernel_issues:
                    log_results.append('\nÔÜá´©Å Problemas identificados no kernel:')
                    log_results.append('----------------------------------------------------------------------')
                    log_results.append('\n'.join(kernel_issues))
                else:
                    log_results.append('\nÔ£à Nenhum problema cr├¡tico encontrado nos logs do kernel')
                    log_results.append('   Os componentes de baixo n├¡vel do sistema est├úo funcionando corretamente.')
                found_logs = True
        except Exception as e:
            log_results.append(f'\nÔÜá´©Å N├úo foi poss├¡vel ler logs do kernel: {str(e)}')
            log_results.append('   Por que isto acontece? Alguns dispositivos restringem o acesso')
            log_results.append('   aos logs do kernel por raz├Áes de seguran├ºa.')
        crash_count = 0
        anr_count = 0
        error_count = 0
        crash_apps = set()
        anr_apps = set()
        try:
            result = self._run_adb_command([self.adb_path, 'shell', 'dumpsys dropbox --print'])
            if result and len(result.strip()) > 10:
                crash_events = []
                anr_events = []
                other_events = []
                for line in result.split('\n'):
                    if 'CRASH' in line:
                        crash_events.append(line)
                        crash_count += 1
                        app_match = re.search('data_app_crash/([^/]+)', line)
                        if app_match:
                            crash_apps.add(app_match.group(1))
                    elif 'ANR' in line:
                        anr_events.append(line)
                        anr_count += 1
                        app_match = re.search('data_app_anr/([^/]+)', line)
                        if app_match:
                            anr_apps.add(app_match.group(1))
                    elif 'ERROR' in line or 'EXCEPTION' in line:
                        other_events.append(line)
                        error_count += 1
                log_results.append('\n­ƒô▒ EVENTOS DO SISTEMA (DROPBOX)')
                log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                log_results.append('Ôòæ ' + 'O que ├® isto?'.ljust(66) + ' Ôòæ')
                log_results.append('Ôòæ ' + 'Logs de eventos cr├¡ticos como crashes, aplicativos que n├úo'.ljust(66) + ' Ôòæ')
                log_results.append('Ôòæ ' + 'respondem (ANRs) e outros erros significativos do sistema.'.ljust(66) + ' Ôòæ')
                log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                if crash_events:
                    log_results.append('\n­ƒÆÑ CRASHES DETECTADOS:')
                    log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                    log_results.append('Ôòæ ' + 'O que s├úo crashes?'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'Crashes ocorrem quando um aplicativo para de funcionar'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'abruptamente devido a um erro grave no c├│digo.'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'Impacto: Perda de dados n├úo salvos e interrup├º├úo do uso.'.ljust(66) + ' Ôòæ')
                    log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                    log_results.append('\n'.join(crash_events[:10]))
                    if len(crash_events) > 10:
                        log_results.append(f'... (mais {len(crash_events) - 10} eventos omitidos) ...')
                if anr_events:
                    log_results.append('\nÔÅ▒´©Å ANRs (Application Not Responding):')
                    log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                    log_results.append('Ôòæ ' + 'O que s├úo ANRs?'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + "Ocorrem quando um aplicativo 'congela' e n├úo responde ├ás".ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'intera├º├Áes do usu├írio por mais de 5 segundos.'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'Impacto: Frustra├º├úo do usu├írio e perda de produtividade.'.ljust(66) + ' Ôòæ')
                    log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                    log_results.append('\n'.join(anr_events[:10]))
                    if len(anr_events) > 10:
                        log_results.append(f'... (mais {len(anr_events) - 10} eventos omitidos) ...')
                if other_events:
                    log_results.append('\nÔÜá´©Å OUTROS ERROS:')
                    log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                    log_results.append('Ôòæ ' + 'O que s├úo esses erros?'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'Problemas n├úo categorizados que afetam o funcionamento do'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'sistema ou aplicativos de forma irregular.'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'Impacto: Comportamentos inesperados ou falhas diversas.'.ljust(66) + ' Ôòæ')
                    log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                    log_results.append('\n'.join(other_events[:10]))
                    if len(other_events) > 10:
                        log_results.append(f'... (mais {len(other_events) - 10} eventos omitidos) ...')
                if not crash_events and not anr_events and not other_events:
                    log_results.append('Ô£à Nenhum evento cr├¡tico encontrado nos logs do sistema')
                    log_results.append('   Isto ├® um ├│timo sinal! Significa que o sistema est├í operando')
                    log_results.append('   corretamente sem falhas graves recentes.')
                found_logs = True
        except Exception as e:
            log_results.append(f'\nÔÜá´©Å N├úo foi poss├¡vel ler eventos do sistema: {str(e)}')
            log_results.append('   Por que isto acontece? O dispositivo pode ter restri├º├Áes de acesso')
            log_results.append('   aos logs do sistema ou problemas de comunica├º├úo.')
        battery_dict = {}
        try:
            battery_info = self._run_adb_command([self.adb_path, 'shell', 'dumpsys battery'])
            if battery_info:
                log_results.append('\n­ƒöï INFORMA├ç├òES DA BATERIA')
                log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                log_results.append('Ôòæ ' + 'O que ├® isto?'.ljust(66) + ' Ôòæ')
                log_results.append('Ôòæ ' + 'Dados t├®cnicos sobre o estado atual da bateria e como est├í'.ljust(66) + ' Ôòæ')
                log_results.append('Ôòæ ' + 'sendo utilizada pelo dispositivo.'.ljust(66) + ' Ôòæ')
                log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                for line in battery_info.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        battery_dict[key.strip()] = value.strip()
                if battery_dict:
                    power_source = 'AC' if battery_dict.get('AC powered') == 'true' else 'USB' if battery_dict.get('USB powered') == 'true' else 'Bateria'
                    health_map = {'1': 'Desconhecido', '2': 'Boa', '3': 'Superaquecida', '4': 'Danificada', '5': 'Sobretens├úo', '6': 'Falha', '7': 'Fria'}
                    health_code = battery_dict.get('health', '1')
                    health = health_map.get(health_code, 'Desconhecido')
                    log_results.append('')
                    log_results.append('ÔöîÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÉ')
                    log_results.append(f'Ôöé ­ƒöî Fonte de energia: {power_source.ljust(48)}Ôöé')
                    log_results.append('Ôöé  Ô×£ Indica se o dispositivo est├í usando energia da bateria   Ôöé')
                    log_results.append('Ôöé    ou est├í conectado ├á energia.                             Ôöé')
                    log_results.append('Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ')
                    log_results.append(f'Ôöé ­ƒôè N├¡vel: {battery_dict.get('level', 'N/A')}%'.ljust(67) + 'Ôöé')
                    log_results.append('Ôöé  Ô×£ A porcentagem atual de carga da bateria.                 Ôöé')
                    log_results.append('Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ')
                    log_results.append(f'Ôöé ÔØñ´©Å Sa├║de: {health} (C├│digo: {health_code})'.ljust(67) + 'Ôöé')
                    log_results.append('Ôöé  Ô×£ Condi├º├úo geral da bateria e sua capacidade de manter     Ôöé')
                    log_results.append('Ôöé    carga.                                                   Ôöé')
                    try:
                        try:
                            temp = float(battery_dict.get('temperature', '0')) / 10
                            log_results.append('Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ')
                            log_results.append(f'Ôöé ­ƒîí´©Å Temperatura: {temp:.1f}┬░C'.ljust(67) + 'Ôöé')
                            log_results.append('Ôöé  Ô×£ Temperatura atual da bateria. Valores acima de 40┬░C s├úo   Ôöé')
                            log_results.append('Ôöé    preocupantes.                                             Ôöé')
                        except Exception as e:
                            log_results.append(f'\nÔÜá´©Å N├úo foi poss├¡vel ler informa├º├Áes da bateria: {str(e)}')
                            log_results.append('   Por que isto acontece? Pode haver restri├º├Áes de permiss├úo para')
                            log_results.append('   acessar as informa├º├Áes da bateria ou problemas de comunica├º├úo.')
                    except:
                        log_results.append('Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ')
                        log_results.append(f'Ôöé ­ƒîí´©Å Temperatura: {battery_dict.get('temperature', 'N/A')}'.ljust(67) + 'Ôöé')
                        log_results.append('Ôöé  Ô×£ Temperatura atual da bateria em unidades do sistema.      Ôöé')
            try:
                voltage = float(battery_dict.get('voltage', '0')) / 1000
                log_results.append('Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ')
                log_results.append(f'Ôöé ÔÜí Voltagem: {voltage:.2f}V'.ljust(67) + 'Ôöé')
                log_results.append('Ôöé  Ô×£ Tens├úo atual da bateria. Valores abaixo do normal podem   Ôöé')
                log_results.append('Ôöé    indicar problemas.                                        Ôöé')
            except Exception as e:
                log_results.append(f'\nÔÜá´©Å N├úo foi poss├¡vel ler informa├º├Áes da bateria: {str(e)}')
                log_results.append('   Por que isto acontece? Pode haver restri├º├Áes de permiss├úo para')
                log_results.append('   acessar as informa├º├Áes da bateria ou problemas de comunica├º├úo.')
            else:
                log_results.append('Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ')
                log_results.append(f'Ôöé ­ƒö¼ Tecnologia: {battery_dict.get('technology', 'N/A')}'.ljust(67) + 'Ôöé')
                log_results.append('Ôöé  Ô×£ O tipo de qu├¡mica utilizada na bateria (Li-Ion, Li-Poly).    Ôöé')
                log_results.append('ÔööÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÿ')
                found_logs = True
        except Exception as e:
            return f'Erro ao verificar eventos do sistema:\n{str(e)}\n\nVerifique se:\n1. O dispositivo est├í respondendo\n2. A conex├úo USB est├í est├ível\n3. A depura├º├úo USB continua ativada'
        return '\n'.join(log_results)
    def panic_android(self, parent_window=None):
        if not self.check_device():
            return 'Nenhum dispositivo detectado. Conecte o dispositivo e tente novamente.'
        progress = QProgressDialog('Gerando Bugreport...', None, 0, 100, parent_window)
        progress.setWindowModality(Qt.WindowModal)
        progress.setAutoClose(True)
        progress.setValue(0)
        try:
            progress.setLabelText('Coletando informa├º├Áes do dispositivo...')
            device_info = self.check_device_info()
            progress.setValue(10)
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            default_filename = f'bugreport_{timestamp}.zip'
            save_path, _ = QFileDialog.getSaveFileName(parent_window, 'Salvar Bugreport', default_filename, 'Arquivos ZIP (*.zip)')
            if not save_path:
                return 'Opera├º├úo cancelada pelo usu├írio.'
            progress.setLabelText('Gerando bugreport completo...\nIsso pode levar alguns minutos.')
            progress.setValue(30)
            self._run_adb_command([self.adb_path, 'bugreport', save_path])
            progress.setValue(90)
            if os.path.exists(save_path):
                progress.setValue(100)
                return f'Bugreport gerado com sucesso!\n\nArquivo salvo em:\n{save_path}\n\nEste arquivo cont├®m informa├º├Áes detalhadas do sistema\nque podem ajudar no diagn├│stico de problemas.'
            raise Exception('Falha ao gerar o arquivo de bugreport')
        except Exception as e:
            return f'Erro durante a gera├º├úo do bugreport: {str(e)}'
    def filter_logcat(self, filter_type='all', keywords=None):
        try:
            buffer_arg = {'all': '', 'system': '-b system', 'main': '-b main', 'crash': '-b crash', 'radio': '-b radio', 'events': '-b events'}.get(filter_type, '')
            cmd = [self.adb_path, 'logcat', '-d']
            if buffer_arg:
                cmd.extend(buffer_arg.split())
            output = self._run_adb_command(cmd)
            if keywords:
                filtered_lines = []
                for line in output.split('\n'):
                    if any((keyword.lower() in line.lower() for keyword in keywords)):
                        filtered_lines.append(line)
                return '\n'.join(filtered_lines)
            return output
        except Exception as e:
            raise Exception(f'Erro ao filtrar logs: {str(e)}')
    def analyze_system_errors(self):
        try:
            system_logs = self.filter_logcat('system')
            crash_logs = self.filter_logcat('crash')
            error_patterns = {'ANR': 'ANR in (\\S+)', 'FATAL EXCEPTION': 'FATAL EXCEPTION: .*?(?=\\n)', 'System.err': 'System.err: .*?(?=\\n)', 'SIGSEGV': 'SIGSEGV.*?(?=\\n)', 'OutOfMemoryError': 'OutOfMemoryError.*?(?=\\n)'}
            results = {'anrs': [], 'crashes': [], 'system_errors': [], 'summary': {'total_anrs': 0, 'total_crashes': 0, 'total_errors': 0}}
            for line in system_logs.split('\n'):
                if 'ANR in' in line:
                    match = re.search(error_patterns['ANR'], line)
                    if match:
                        results['anrs'].append({'package': match.group(1), 'timestamp': line.split()[0:2], 'full_log': line})
                        results['summary']['total_anrs'] += 1
                if any((err in line for err in ('FATAL EXCEPTION', 'System.err', 'SIGSEGV'))):
                    results['system_errors'].append(line)
                    results['summary']['total_errors'] += 1
            for line in crash_logs.split('\n'):
                if any((pattern in line for pattern in error_patterns.values())):
                    results['crashes'].append(line)
                    results['summary']['total_crashes'] += 1
            return self.format_error_analysis(results)
        except Exception as e:
            raise Exception(f'Erro ao analisar erros do sistema: {str(e)}')
    def format_error_analysis(self, results):
        output = []
        output.append('=== An├ílise de Erros do Sistema ===')
        output.append('\nResumo:')
        output.append(f'ÔÇó Total de ANRs: {results['summary']['total_anrs']}')
        output.append(f'ÔÇó Total de Crashes: {results['summary']['total_crashes']}')
        output.append(f'ÔÇó Total de Erros de Sistema: {results['summary']['total_errors']}')
        if results['anrs']:
            output.append('\n=== ANRs (Application Not Responding) ===')
            for anr in results['anrs']:
                output.append(f'\nAplicativo: {anr['package']}')
                output.append(f'Timestamp: {' '.join(anr['timestamp'])}')
        if results['crashes']:
            output.append('\n=== Crashes ===')
            for crash in results['crashes'][:10]:
                output.append(f'\nÔÇó {crash}')
        if results['system_errors']:
            output.append('\n=== Erros de Sistema ===')
            for error in results['system_errors'][:10]:
                output.append(f'\nÔÇó {error}')
        if not any([results['anrs'], results['crashes'], results['system_errors']]):
            output.append('\nNenhum erro cr├¡tico encontrado nos logs analisados.')
        return '\n'.join(output)
    def unlock_bootloader(self, parent_window=None):
        warning = 'ATEN├ç├âO!\n\nO desbloqueio do bootloader ir├í:\n1. Apagar TODOS os dados do dispositivo\n2. Pode invalidar a garantia\n3. ├ë um processo irrevers├¡vel\n\nCertifique-se de:\n1. Ter feito backup de todos os dados\n2. O dispositivo estar com a bateria carregada\n3. Ter habilitado o desbloqueio OEM nas configura├º├Áes\n\nDeseja continuar?'
        reply = QMessageBox.warning(parent_window, 'Desbloquear Bootloader', warning, QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No:
            return 'Opera├º├úo cancelada pelo usu├írio.'
        progress = QProgressDialog('Desbloqueando bootloader...', None, 0, 100, parent_window)
        progress.setWindowModality(Qt.WindowModal)
        progress.setAutoClose(True)
        progress.setValue(0)
        try:
            progress.setLabelText('Verificando estado do dispositivo...')
            if not self.check_fastboot_device():
                return 'Dispositivo n├úo est├í em modo fastboot.\n1. Ative o modo desenvolvedor\n2. Habilite o desbloqueio OEM\n3. Reinicie em modo fastboot'
            progress.setValue(20)
            progress.setLabelText('Verificando status do bootloader...')
            bootloader_status = self._run_fastboot_command([self.fastboot_path, 'getvar', 'unlocked'])
            progress.setValue(40)
            if 'unlocked: yes' in bootloader_status.lower():
                return 'Bootloader j├í est├í desbloqueado!'
            progress.setLabelText('Executando comando de desbloqueio...')
            self._run_fastboot_command([self.fastboot_path, 'flashing', 'unlock'])
            progress.setValue(60)
            progress.setLabelText('Aguardando confirma├º├úo no dispositivo...\nUse as teclas de volume e power para confirmar')
            time.sleep(5)
            progress.setValue(80)
            progress.setLabelText('Verificando resultado...')
            bootloader_status = self._run_fastboot_command([self.fastboot_path, 'getvar', 'unlocked'])
            progress.setValue(100)
            if 'unlocked: yes' in bootloader_status.lower():
                return 'Bootloader desbloqueado com sucesso!\nO dispositivo ser├í reiniciado e todos os dados ser├úo apagados.'
        except Exception as e:
            return f'Erro ao desbloquear bootloader: {str(e)}'
        return 'N├úo foi poss├¡vel confirmar o desbloqueio.\nVerifique se:\n1. O desbloqueio foi confirmado no dispositivo\n2. O dispositivo suporta desbloqueio\n3. O desbloqueio OEM est├í habilitado'
    def fix_permissions(self):
        try:
            if not self.check_device():
                return 'Nenhum dispositivo detectado'
            permissions = ['android.permission.READ_EXTERNAL_STORAGE', 'android.permission.WRITE_EXTERNAL_STORAGE', 'android.permission.ACCESS_MEDIA_LOCATION', 'android.permission.MANAGE_EXTERNAL_STORAGE', 'android.permission.PACKAGE_USAGE_STATS', 'android.permission.SYSTEM_ALERT_WINDOW', 'android.permission.WRITE_SECURE_SETTINGS']
            results = []
            for perm in permissions:
                pass
            try:
                result = self._run_adb_command([self.adb_path, 'shell', 'pm', 'grant', 'com.android.systemui', perm])
                results.append(f'Permiss├úo {perm}: OK')
            except:
                results.append(f'Permiss├úo {perm}: Falhou')
            else:
                self._run_adb_command([self.adb_path, 'shell', 'pm', 'reset-permissions'])
                results.append('Reset geral de permiss├Áes: OK')
                self._run_adb_command([self.adb_path, 'shell', 'chmod -R 777 /data/local/tmp'])
                results.append('Permiss├Áes de arquivos tempor├írios: OK')
        except Exception as e:
            raise Exception(f'Erro ao corrigir permiss├Áes: {str(e)}')
        return '\n'.join(results)
    def _run_adb_command_with_progress(self, command):
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, cwd=os.path.dirname(self.adb_path) if self.adb_path else None, startupinfo=self.startupinfo, creationflags=self.creation_flags)
            return process
        except Exception as e:
            raise Exception(f'Erro ao executar comando: {str(e)}')
    def kill_process(self, package_name):
        try:
            if not self.check_device():
                return 'Nenhum dispositivo detectado'
            commands = [f'am force-stop {package_name}', f'killall {package_name}', f'kill $(pidof {package_name})']
            for cmd in commands:
                pass
            try:
                self._run_adb_command([self.adb_path, 'shell', cmd])
            except:
                pass
            else:
                ps_output = self._run_adb_command([self.adb_path, 'shell', 'ps | grep', package_name])
                if package_name in ps_output:
                    return f'N├úo foi poss├¡vel matar o processo {package_name}'
        except Exception as e:
            return f'Erro ao matar processo: {str(e)}'
        return f'Processo {package_name} finalizado com sucesso'
    def list_processes(self):
        try:
            if not self.check_device():
                return 'Nenhum dispositivo detectado'
            ps_output = self._run_adb_command([self.adb_path, 'shell', 'ps -A'])
            processes = []
            for line in ps_output.split('\n')[1:]:
                parts = line.split()
                if len(parts) >= 8:
                    processes.append({'pid': parts[1], 'user': parts[0], 'name': parts[-1], 'cpu': parts[2], 'mem': parts[3]})
            processes.sort(key=(lambda x: float(x['cpu'])), reverse=True)
            output = ['=== Processos em Execu├º├úo ===\n']
            output.append('PID\tCPU%\tMEM\tUSU├üRIO\tPROCESSO')
            output.append('--------------------------------------------------')
            for proc in processes[:20]:
                output.append(f'{proc['pid']}\t{proc['cpu']}%\t{proc['mem']}\t{proc['user']}\t{proc['name']}')
            return '\n'.join(output)
        except Exception as e:
            return f'Erro ao listar processos: {str(e)}'
    def start_log_capture(self, log_file=None):
        if self.logcat_process is not None:
            return 'Captura de logs j├í est├í em andamento'
        if not self.check_device():
            return 'Nenhum dispositivo detectado'
        try:
            if log_file is None:
                log_dir = os.path.join(tempfile.gettempdir(), 'adb_logs')
                os.makedirs(log_dir, exist_ok=True)
                log_file = os.path.join(log_dir, f'logcat_{time.strftime('%Y%m%d_%H%M%S')}.txt')
            self._run_adb_command([self.adb_path, 'logcat', '-c'])
            def capture_logs():
                with open(log_file, 'w', encoding='utf-8') as f:
                    process = subprocess.Popen([self.adb_path, 'logcat'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, cwd=os.path.dirname(self.adb_path), startupinfo=self.startupinfo, creationflags=self.creation_flags)
                    self.logcat_process = process
                    while self.running:
                        line = process.stdout.readline()
                        if line:
                            f.write(line)
                            f.flush()
                            self.log_queue.put(line)
                    process.terminate()
                    self.logcat_process = None
            self.running = True
            self.log_thread = threading.Thread(target=capture_logs)
            self.log_thread.daemon = True
            self.log_thread.start()
            return f'Captura de logs iniciada. Arquivo: {log_file}'
        except Exception as e:
            self.running = False
            self.logcat_process = None
            return f'Erro ao iniciar captura de logs: {str(e)}'
    def stop_log_capture(self):
        if self.logcat_process is None:
            return 'Nenhuma captura de logs em andamento'
        try:
            self.running = False
            if self.log_thread:
                self.log_thread.join(timeout=5)
            if self.logcat_process:
                self.logcat_process.terminate()
                self.logcat_process = None
            return 'Captura de logs finalizada'
        except Exception as e:
            return f'Erro ao parar captura de logs: {str(e)}'
    def get_latest_logs(self, max_lines=100):
        try:
            logs = []
            while not self.log_queue.empty():
                logs.append(self.log_queue.get_nowait())
            return ''.join(logs)
        except:
            return ''
    def get_device_info(self):
        device_info = {}
        try:
            if not self.is_device_connected():
                return 'Nenhum dispositivo conectado'
            model_output = self.execute_adb_command('shell getprop ro.product.model').strip()
            brand_output = self.execute_adb_command('shell getprop ro.product.brand').strip()
            if not model_output or not brand_output:
                return 'N├úo foi poss├¡vel obter informa├º├Áes b├ísicas do dispositivo'
            device_info['model'] = model_output
            device_info['brand'] = brand_output
            android_version = self.execute_adb_command('shell getprop ro.build.version.release').strip()
            device_info['android'] = android_version or 'Desconhecido'
            cpu_info = self.execute_adb_command('shell cat /proc/cpuinfo')
            cpu_model_match = re.search('Hardware\\s+:\\s+(.*)', cpu_info)
            if cpu_model_match:
                device_info['cpu'] = cpu_model_match.group(1).strip()
            else:
                device_info['cpu'] = 'Desconhecido'
            mem_info = self.execute_adb_command('shell cat /proc/meminfo')
            total_mem_match = re.search('MemTotal\\s+:\\s+(\\d+)', mem_info)
            if total_mem_match:
                total_mem_kb = int(total_mem_match.group(1))
                total_mem_mb = total_mem_kb / 1024
                device_info['memory'] = f'{total_mem_mb:.0f} MB'
            else:
                device_info['memory'] = 'Desconhecido'
            battery_info = self.execute_adb_command('shell dumpsys battery')
            battery_level_match = re.search('level: (\\d+)', battery_info)
            if battery_level_match:
                device_info['battery'] = f'{battery_level_match.group(1)}%'
                return device_info
            device_info['battery'] = 'Desconhecido'
            return device_info
        except Exception as e:
            self.logger.error(f'Erro ao obter informa├º├Áes do dispositivo: {str(e)}')
            return f'Erro ao obter informa├º├Áes do dispositivo: {str(e)}'
    def check_system_events(self):
        try:
            if not self.check_device():
                return 'Nenhum dispositivo detectado'
            log_results = []
            found_logs = False
            log_results.append('======================================================================')
            log_results.append('­ƒô▒ RELAT├ôRIO DE DIAGN├ôSTICO DO SISTEMA'.center(70))
            log_results.append('======================================================================')
            log_results.append('\nEste relat├│rio analisa logs e eventos do sistema Android para identificar problemas.')
            log_results.append('Cada se├º├úo cont├®m explica├º├Áes detalhadas para ajudar na interpreta├º├úo dos resultados.')
            log_results.append('----------------------------------------------------------------------\n')
            error_descriptions = {'permission': 'Problemas de permiss├úo - O sistema negou acesso a um recurso', 'crash': 'Crash de aplicativo - Um aplicativo fechou inesperadamente', 'anr': 'ANR (App Not Responding) - Um aplicativo parou de responder', 'failed': 'Falha em opera├º├úo - Uma a├º├úo solicitada n├úo p├┤de ser conclu├¡da', 'exception': 'Exce├º├úo n├úo tratada - Erro de programa├º├úo n├úo capturado', 'out of memory': 'Mem├│ria insuficiente - O dispositivo est├í com pouca RAM dispon├¡vel', 'battery': 'Problema de bateria - H├í um problema com a carga ou estado da bateria', 'temperature': 'Problema de temperatura - O dispositivo est├í muito quente ou frio', 'deadlock': 'Deadlock - Processos travados esperando um pelo outro', 'watchdog': 'Watchdog timeout - Um processo demorou muito para responder', 'fatal': 'Erro fatal - Problema grave no sistema ou aplicativo', 'denied': 'Acesso negado - Uma opera├º├úo foi bloqueada por seguran├ºa'}
            try:
                result = self._run_adb_command([self.adb_path, 'shell', 'logcat -d -b system'])
                if result and len(result.strip()) > 10:
                    important_lines = []
                    error_count = 0
                    warning_count = 0
                    error_types = {}
                    for line in result.split('\n'):
                        if 'E/' not in line and 'error' not in line.lower():
                            if 'exception' in line.lower():
                                important_lines.append(line)
                                error_count += 1
                                for error_key, description in error_descriptions.items():
                                    if error_key not in line.lower():
                                        continue
                                    if error_key not in error_types:
                                        error_types[error_key] = {'count': 1, 'description': description}
                                    else:
                                        error_types[error_key]['count'] += 1
                            elif 'W/' in line or 'warning' in line.lower():
                                important_lines.append(line)
                                warning_count += 1
                    if len(important_lines) > 30:
                        important_lines = important_lines[:30]
                        important_lines.append('... (mais linhas omitidas) ...')
                    log_results.append('\n­ƒôè RESUMO DE LOGS DO SISTEMA')
                    log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                    log_results.append('Ôòæ ' + 'O que ├® isto?'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'Logs do sistema Android que mostram erros e avisos dos aplicativos'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'e componentes do sistema operacional.'.ljust(66) + ' Ôòæ')
                    log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                    log_results.append(f'ÔØî Erros encontrados: {error_count}')
                    log_results.append(f'ÔÜá´©Å Avisos encontrados: {warning_count}')
                    if error_types:
                        log_results.append('\n­ƒöì TIPOS DE ERROS DETECTADOS:')
                        log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                        for error_key, data in error_types.items():
                            log_results.append(f'Ôòæ ÔÇó {data['description']} ({data['count']} ocorr├¬ncias)'.ljust(69) + 'Ôòæ')
                        log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                    if important_lines:
                        log_results.append('\n­ƒöì EVENTOS IMPORTANTES DO SISTEMA')
                        log_results.append('----------------------------------------------------------------------')
                        log_results.append('­ƒæë O que significam estes logs?')
                        log_results.append('   E/ = Erro | W/ = Aviso | I/ = Informa├º├úo')
                        log_results.append('   Os c├│digos ap├│s a barra (/) indicam o componente que gerou o log.')
                        log_results.append('----------------------------------------------------------------------')
                        log_results.append('\n'.join(important_lines))
                    else:
                        log_results.append('\nÔ£à Nenhum evento cr├¡tico encontrado nos logs do sistema')
                        log_results.append('   Isto ├® um bom sinal! O sistema est├í funcionando normalmente.')
                    found_logs = True
            except Exception as e:
                log_results.append(f'\nÔÜá´©Å N├úo foi poss├¡vel ler logs do sistema: {str(e)}')
                log_results.append('   Por que isto acontece? O dispositivo pode ter restri├º├Áes de acesso')
                log_results.append('   aos logs ou a depura├º├úo USB pode estar com problemas.')
            else:
                kernel_issues_by_type = {}
        except Exception as e:
            return f'Erro ao verificar eventos do sistema:\n{str(e)}\n\nVerifique se:\n1. O dispositivo est├í respondendo\n2. A conex├úo USB est├í est├ível\n3. A depura├º├úo USB continua ativada'
        try:
            result = self._run_adb_command([self.adb_path, 'shell', 'dmesg'])
            if result and len(result.strip()) > 10:
                kernel_issues = []
                kernel_terms = {'error': 'Erro geral no kernel', 'fail': 'Falha em uma opera├º├úo', 'denied': 'Permiss├úo negada pelo sistema', 'cannot': 'Opera├º├úo imposs├¡vel', 'panic': 'Kernel Panic - erro muito grave', 'emerg': 'Emerg├¬ncia no sistema', 'alert': 'Alerta de funcionamento', 'critical': 'Problema cr├¡tico', 'oom_kill': 'Out of Memory Kill - Processo eliminado por falta de mem├│ria', 'segfault': 'Segmentation Fault - Acesso inv├ílido ├á mem├│ria', 'i/o error': 'Erro de entrada/sa├¡da', 'blocked for': 'Processo bloqueado por muito tempo'}
                for line in result.split('\n'):
                    lower_line = line.lower()
                    for term, description in kernel_terms.items():
                        if not term in lower_line:
                            continue
                        kernel_issues.append(line)
                        if term not in kernel_issues_by_type:
                            kernel_issues_by_type[term] = {'count': 1, 'description': description}
                        else:
                            kernel_issues_by_type[term]['count'] += 1
                        break
                if len(kernel_issues) > 20:
                    kernel_issues = kernel_issues[:20]
                    kernel_issues.append('... (mais linhas omitidas) ...')
                log_results.append('\n­ƒûÑ´©Å LOGS DO KERNEL (DMESG)')
                log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                log_results.append('Ôòæ ' + 'O que ├® isto?'.ljust(66) + ' Ôòæ')
                log_results.append('Ôòæ ' + 'Logs do n├║cleo do sistema (kernel) que mostram problemas de'.ljust(66) + ' Ôòæ')
                log_results.append('Ôòæ ' + 'hardware, permiss├Áes e acessos a recursos de baixo n├¡vel.'.ljust(66) + ' Ôòæ')
                log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                if kernel_issues_by_type:
                    log_results.append('\nÔÜá´©Å TIPOS DE PROBLEMAS NO KERNEL:')
                    log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                    for term, data in kernel_issues_by_type.items():
                        log_results.append(f'Ôòæ ÔÇó {data['description']} ({data['count']} ocorr├¬ncias)'.ljust(69) + 'Ôòæ')
                    log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                    log_results.append('\n­ƒæë O que isso significa para voc├¬?')
                    log_results.append('   Problemas no kernel podem causar travamentos, reinicializa├º├Áes')
                    log_results.append('   inesperadas ou funcionamento inst├ível do dispositivo.')
                if kernel_issues:
                    log_results.append('\nÔÜá´©Å Problemas identificados no kernel:')
                    log_results.append('----------------------------------------------------------------------')
                    log_results.append('\n'.join(kernel_issues))
                else:
                    log_results.append('\nÔ£à Nenhum problema cr├¡tico encontrado nos logs do kernel')
                    log_results.append('   Os componentes de baixo n├¡vel do sistema est├úo funcionando corretamente.')
                found_logs = True
        except Exception as e:
            log_results.append(f'\nÔÜá´©Å N├úo foi poss├¡vel ler logs do kernel: {str(e)}')
            log_results.append('   Por que isto acontece? Alguns dispositivos restringem o acesso')
            log_results.append('   aos logs do kernel por raz├Áes de seguran├ºa.')
        crash_count = 0
        anr_count = 0
        error_count = 0
        crash_apps = set()
        anr_apps = set()
        try:
            result = self._run_adb_command([self.adb_path, 'shell', 'dumpsys dropbox --print'])
            if result and len(result.strip()) > 10:
                crash_events = []
                anr_events = []
                other_events = []
                for line in result.split('\n'):
                    if 'CRASH' in line:
                        crash_events.append(line)
                        crash_count += 1
                        app_match = re.search('data_app_crash/([^/]+)', line)
                        if app_match:
                            crash_apps.add(app_match.group(1))
                    elif 'ANR' in line:
                        anr_events.append(line)
                        anr_count += 1
                        app_match = re.search('data_app_anr/([^/]+)', line)
                        if app_match:
                            anr_apps.add(app_match.group(1))
                    elif 'ERROR' in line or 'EXCEPTION' in line:
                        other_events.append(line)
                        error_count += 1
                log_results.append('\n­ƒô▒ EVENTOS DO SISTEMA (DROPBOX)')
                log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                log_results.append('Ôòæ ' + 'O que ├® isto?'.ljust(66) + ' Ôòæ')
                log_results.append('Ôòæ ' + 'Logs de eventos cr├¡ticos como crashes, aplicativos que n├úo'.ljust(66) + ' Ôòæ')
                log_results.append('Ôòæ ' + 'respondem (ANRs) e outros erros significativos do sistema.'.ljust(66) + ' Ôòæ')
                log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                if crash_events:
                    log_results.append('\n­ƒÆÑ CRASHES DETECTADOS:')
                    log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                    log_results.append('Ôòæ ' + 'O que s├úo crashes?'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'Crashes ocorrem quando um aplicativo para de funcionar'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'abruptamente devido a um erro grave no c├│digo.'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'Impacto: Perda de dados n├úo salvos e interrup├º├úo do uso.'.ljust(66) + ' Ôòæ')
                    log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                    log_results.append('\n'.join(crash_events[:10]))
                    if len(crash_events) > 10:
                        log_results.append(f'... (mais {len(crash_events) - 10} eventos omitidos) ...')
                if anr_events:
                    log_results.append('\nÔÅ▒´©Å ANRs (Application Not Responding):')
                    log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                    log_results.append('Ôòæ ' + 'O que s├úo ANRs?'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + "Ocorrem quando um aplicativo 'congela' e n├úo responde ├ás".ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'intera├º├Áes do usu├írio por mais de 5 segundos.'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'Impacto: Frustra├º├úo do usu├írio e perda de produtividade.'.ljust(66) + ' Ôòæ')
                    log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                    log_results.append('\n'.join(anr_events[:10]))
                    if len(anr_events) > 10:
                        log_results.append(f'... (mais {len(anr_events) - 10} eventos omitidos) ...')
                if other_events:
                    log_results.append('\nÔÜá´©Å OUTROS ERROS:')
                    log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                    log_results.append('Ôòæ ' + 'O que s├úo esses erros?'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'Problemas n├úo categorizados que afetam o funcionamento do'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'sistema ou aplicativos de forma irregular.'.ljust(66) + ' Ôòæ')
                    log_results.append('Ôòæ ' + 'Impacto: Comportamentos inesperados ou falhas diversas.'.ljust(66) + ' Ôòæ')
                    log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                    log_results.append('\n'.join(other_events[:10]))
                    if len(other_events) > 10:
                        log_results.append(f'... (mais {len(other_events) - 10} eventos omitidos) ...')
                if not crash_events and not anr_events and not other_events:
                    log_results.append('Ô£à Nenhum evento cr├¡tico encontrado nos logs do sistema')
                    log_results.append('   Isto ├® um ├│timo sinal! Significa que o sistema est├í operando')
                    log_results.append('   corretamente sem falhas graves recentes.')
                found_logs = True
        except Exception as e:
            log_results.append(f'\nÔÜá´©Å N├úo foi poss├¡vel ler eventos do sistema: {str(e)}')
            log_results.append('   Por que isto acontece? O dispositivo pode ter restri├º├Áes de acesso')
            log_results.append('   aos logs do sistema ou problemas de comunica├º├úo.')
        battery_dict = {}
        try:
            battery_info = self._run_adb_command([self.adb_path, 'shell', 'dumpsys battery'])
            if battery_info:
                log_results.append('\n­ƒöï INFORMA├ç├òES DA BATERIA')
                log_results.append('ÔòöÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòù')
                log_results.append('Ôòæ ' + 'O que ├® isto?'.ljust(66) + ' Ôòæ')
                log_results.append('Ôòæ ' + 'Dados t├®cnicos sobre o estado atual da bateria e como est├í'.ljust(66) + ' Ôòæ')
                log_results.append('Ôòæ ' + 'sendo utilizada pelo dispositivo.'.ljust(66) + ' Ôòæ')
                log_results.append('ÔòÜÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòØ')
                for line in battery_info.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        battery_dict[key.strip()] = value.strip()
                if battery_dict:
                    power_source = 'AC' if battery_dict.get('AC powered') == 'true' else 'USB' if battery_dict.get('USB powered') == 'true' else 'Bateria'
                    health_map = {'1': 'Desconhecido', '2': 'Boa', '3': 'Superaquecida', '4': 'Danificada', '5': 'Sobretens├úo', '6': 'Falha', '7': 'Fria'}
                    health_code = battery_dict.get('health', '1')
                    health = health_map.get(health_code, 'Desconhecido')
                    log_results.append('')
                    log_results.append('ÔöîÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÉ')
                    log_results.append(f'Ôöé ­ƒöî Fonte de energia: {power_source.ljust(48)}Ôöé')
                    log_results.append('Ôöé  Ô×£ Indica se o dispositivo est├í usando energia da bateria   Ôöé')
                    log_results.append('Ôöé    ou est├í conectado ├á energia.                             Ôöé')
                    log_results.append('Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ')
                    log_results.append(f'Ôöé ­ƒôè N├¡vel: {battery_dict.get('level', 'N/A')}%'.ljust(67) + 'Ôöé')
                    log_results.append('Ôöé  Ô×£ A porcentagem atual de carga da bateria.                 Ôöé')
                    log_results.append('Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ')
                    log_results.append(f'Ôöé ÔØñ´©Å Sa├║de: {health} (C├│digo: {health_code})'.ljust(67) + 'Ôöé')
                    log_results.append('Ôöé  Ô×£ Condi├º├úo geral da bateria e sua capacidade de manter     Ôöé')
                    log_results.append('Ôöé    carga.                                                   Ôöé')
                    try:
                        try:
                            temp = float(battery_dict.get('temperature', '0')) / 10
                            log_results.append('Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ')
                            log_results.append(f'Ôöé ­ƒîí´©Å Temperatura: {temp:.1f}┬░C'.ljust(67) + 'Ôöé')
                            log_results.append('Ôöé  Ô×£ Temperatura atual da bateria. Valores acima de 40┬░C s├úo   Ôöé')
                            log_results.append('Ôöé    preocupantes.                                             Ôöé')
                        except Exception as e:
                            log_results.append(f'\nÔÜá´©Å N├úo foi poss├¡vel ler informa├º├Áes da bateria: {str(e)}')
                            log_results.append('   Por que isto acontece? Pode haver restri├º├Áes de permiss├úo para')
                            log_results.append('   acessar as informa├º├Áes da bateria ou problemas de comunica├º├úo.')
                    except:
                        log_results.append('Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ')
                        log_results.append(f'Ôöé ­ƒîí´©Å Temperatura: {battery_dict.get('temperature', 'N/A')}'.ljust(67) + 'Ôöé')
                        log_results.append('Ôöé  Ô×£ Temperatura atual da bateria em unidades do sistema.      Ôöé')
            try:
                voltage = float(battery_dict.get('voltage', '0')) / 1000
                log_results.append('Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ')
                log_results.append(f'Ôöé ÔÜí Voltagem: {voltage:.2f}V'.ljust(67) + 'Ôöé')
                log_results.append('Ôöé  Ô×£ Tens├úo atual da bateria. Valores abaixo do normal podem   Ôöé')
                log_results.append('Ôöé    indicar problemas.                                        Ôöé')
            except Exception as e:
                log_results.append(f'\nÔÜá´©Å N├úo foi poss├¡vel ler informa├º├Áes da bateria: {str(e)}')
                log_results.append('   Por que isto acontece? Pode haver restri├º├Áes de permiss├úo para')
                log_results.append('   acessar as informa├º├Áes da bateria ou problemas de comunica├º├úo.')
            else:
                log_results.append('Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ')
                log_results.append(f'Ôöé ­ƒö¼ Tecnologia: {battery_dict.get('technology', 'N/A')}'.ljust(67) + 'Ôöé')
                log_results.append('Ôöé  Ô×£ O tipo de qu├¡mica utilizada na bateria (Li-Ion, Li-Poly).    Ôöé')
                log_results.append('ÔööÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÿ')
                found_logs = True
        except Exception as e:
            return f'Erro ao verificar eventos do sistema:\n{str(e)}\n\nVerifique se:\n1. O dispositivo est├í respondendo\n2. A conex├úo USB est├í est├ível\n3. A depura├º├úo USB continua ativada'
        return '\n'.join(log_results)
    def panic_android(self, parent_window=None):
        if not self.check_device():
            return 'Nenhum dispositivo detectado. Conecte o dispositivo e tente novamente.'
        progress = QProgressDialog('Gerando Bugreport...', None, 0, 100, parent_window)
        progress.setWindowModality(Qt.WindowModal)
        progress.setAutoClose(True)
        progress.setValue(0)
        try:
            progress.setLabelText('Coletando informa├º├Áes do dispositivo...')
            device_info = self.check_device_info()
            progress.setValue(10)
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            default_filename = f'bugreport_{timestamp}.zip'
            save_path, _ = QFileDialog.getSaveFileName(parent_window, 'Salvar Bugreport', default_filename, 'Arquivos ZIP (*.zip)')
            if not save_path:
                return 'Opera├º├úo cancelada pelo usu├írio.'
            progress.setLabelText('Gerando bugreport completo...\nIsso pode levar alguns minutos.')
            progress.setValue(30)
            self._run_adb_command([self.adb_path, 'bugreport', save_path])
            progress.setValue(90)
            if os.path.exists(save_path):
                progress.setValue(100)
                return f'Bugreport gerado com sucesso!\n\nArquivo salvo em:\n{save_path}\n\nEste arquivo cont├®m informa├º├Áes detalhadas do sistema\nque podem ajudar no diagn├│stico de problemas.'
            raise Exception('Falha ao gerar o arquivo de bugreport')
        except Exception as e:
            return f'Erro durante a gera├º├úo do bugreport: {str(e)}'
    def filter_logcat(self, filter_type='all', keywords=None):
        try:
            buffer_arg = {'all': '', 'system': '-b system', 'main': '-b main', 'crash': '-b crash', 'radio': '-b radio', 'events': '-b events'}.get(filter_type, '')
            cmd = [self.adb_path, 'logcat', '-d']
            if buffer_arg:
                cmd.extend(buffer_arg.split())
            output = self._run_adb_command(cmd)
            if keywords:
                filtered_lines = []
                for line in output.split('\n'):
                    if any((keyword.lower() in line.lower() for keyword in keywords)):
                        filtered_lines.append(line)
                return '\n'.join(filtered_lines)
            return output
        except Exception as e:
            raise Exception(f'Erro ao filtrar logs: {str(e)}')
    def analyze_system_errors(self):
        try:
            system_logs = self.filter_logcat('system')
            crash_logs = self.filter_logcat('crash')
            error_patterns = {'ANR': 'ANR in (\\S+)', 'FATAL EXCEPTION': 'FATAL EXCEPTION: .*?(?=\\n)', 'System.err': 'System.err: .*?(?=\\n)', 'SIGSEGV': 'SIGSEGV.*?(?=\\n)', 'OutOfMemoryError': 'OutOfMemoryError.*?(?=\\n)'}
            results = {'anrs': [], 'crashes': [], 'system_errors': [], 'summary': {'total_anrs': 0, 'total_crashes': 0, 'total_errors': 0}}
            for line in system_logs.split('\n'):
                if 'ANR in' in line:
                    match = re.search(error_patterns['ANR'], line)
                    if match:
                        results['anrs'].append({'package': match.group(1), 'timestamp': line.split()[0:2], 'full_log': line})
                        results['summary']['total_anrs'] += 1
                if any((err in line for err in ('FATAL EXCEPTION', 'System.err', 'SIGSEGV'))):
                    results['system_errors'].append(line)
                    results['summary']['total_errors'] += 1
            for line in crash_logs.split('\n'):
                if any((pattern in line for pattern in error_patterns.values())):
                    results['crashes'].append(line)
                    results['summary']['total_crashes'] += 1
            return self.format_error_analysis(results)
        except Exception as e:
            raise Exception(f'Erro ao analisar erros do sistema: {str(e)}')
    def format_error_analysis(self, results):
        output = []
        output.append('=== An├ílise de Erros do Sistema ===')
        output.append('\nResumo:')
        output.append(f'ÔÇó Total de ANRs: {results['summary']['total_anrs']}')
        output.append(f'ÔÇó Total de Crashes: {results['summary']['total_crashes']}')
