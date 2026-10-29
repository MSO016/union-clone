import os
import sys
import subprocess
import shutil
import tempfile
import threading
from pathlib import Path
from typing import Optional, Tuple
from app.utils._app_cfg import REFS
_MTK_ZIP_NAME = 'mtk_tools.zip'
_MTK_EXE_NAME = 'MTK_TOOLS_V1.3.4.exe'
_MTK_ZIP_KEY = REFS.PK_Z
_TEMP_PREFIX = '_pyt_'
class MTKZipExtractor:
    def __init__(self):
        self.cache_dir = None
        self.extracted_exe = None
        self._limpar_sessoes_anteriores()
    def _limpar_sessoes_anteriores(self):
        try:
            if sys.platform == 'win32':
                base = os.environ.get('LOCALAPPDATA', tempfile.gettempdir())
            else:
                base = tempfile.gettempdir()
            old_cache = Path(base) / '.union_cache' / 'mtk'
            if old_cache.exists():
                shutil.rmtree(old_cache, ignore_errors=True)
            old_root = Path(base) / '.union_cache'
            if old_root.exists():
                try:
                    try:
                        if not any(old_root.iterdir()):
                            old_root.rmdir()
                    except Exception:
                        pass
                except Exception:
                    pass
        except Exception:
            pass
        else:
            try:
                try:
                    if not any(old_root.iterdir()):
                        old_root.rmdir()
                except Exception:
                    pass
            except Exception:
                pass
        try:
            temp_base = Path(tempfile.gettempdir())
            for d in temp_base.iterdir():
                if not d.is_dir():
                    continue
                if d.name.startswith(_TEMP_PREFIX):
                    shutil.rmtree(d, ignore_errors=True)
        except Exception:
            return
    def _find_zip_path(self) -> Optional[str]:
        try:
            from app.utils._res_loader import _cache_dir
            cached = os.path.join(_cache_dir(), _MTK_ZIP_NAME)
            if os.path.isfile(cached):
                return cached
        except Exception:
            pass
        try:
            from app.utils.path_manager import PathManager
            pm_file = PathManager.get_mtk_file(_MTK_ZIP_NAME)
            if pm_file:
                return pm_file
        except Exception:
            pass
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
            paths = [os.path.join(base_path, '_internal', 'app', 'views', 'mtk', _MTK_ZIP_NAME), os.path.join(base_path, 'app', 'views', 'mtk', _MTK_ZIP_NAME)]
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            app_dir = os.path.dirname(current_dir)
            paths = [os.path.join(app_dir, 'views', 'mtk', _MTK_ZIP_NAME)]
        for path in paths:
            if not os.path.exists(path):
                continue
            return path
    def zip_existe(self) -> bool:
        return self._find_zip_path() is not None
    def cache_valido(self) -> bool:
        return False
    def extrair(self, progress_callback=None) -> Tuple[bool, str]:
        try:
            import pyzipper
        except ImportError:
            return (False, 'err_module')
        zip_path = self._find_zip_path()
        if not zip_path:
            return (False, 'err_resource')
        try:
            if progress_callback:
                progress_callback(10, 'Preparando recursos...')
            self.cache_dir = Path(tempfile.mkdtemp(prefix=_TEMP_PREFIX))
            exe_dest = self.cache_dir / _MTK_EXE_NAME
            if progress_callback:
                progress_callback(20, 'Carregando m├│dulo...')
            with pyzipper.AESZipFile(zip_path, 'r') as zf:
                zf.setpassword(_MTK_ZIP_KEY)
                if progress_callback:
                    progress_callback(40, 'Verificando integridade...')
                zf.extract(_MTK_EXE_NAME, str(self.cache_dir))
            if progress_callback:
                progress_callback(80, 'Finalizando...')
            if exe_dest.exists() and exe_dest.stat().st_size > 50000000:
                self.extracted_exe = str(exe_dest)
                if progress_callback:
                    progress_callback(100, 'Pronto!')
                return True, str(exe_dest)
        except pyzipper.BadZipFile:
            return (False, 'err_corrupt')
        except RuntimeError:
            return (False, 'err_decrypt')
        except Exception:
            return (False, 'err_system')
        return (False, 'err_extract')
    def limpar_cache(self):
        try:
            if self.cache_dir and self.cache_dir.exists():
                shutil.rmtree(self.cache_dir, ignore_errors=True)
        except Exception:
            pass
        self.cache_dir = None
        self.extracted_exe = None
    def get_exe_path(self) -> Optional[str]:
        return self.extracted_exe
class MTKManager:
    def __init__(self):
        self.mtk_process = None
        self.zip_extractor = MTKZipExtractor()
        self._monitor_thread = None
        self.mtk_path = self._determinar_caminho_mtk()
    def _determinar_caminho_mtk(self) -> str:
        if self.zip_extractor.cache_valido():
            exe_cache = self.zip_extractor.get_exe_path()
            if exe_cache and os.path.exists(exe_cache):
                return exe_cache
        if self.zip_extractor.zip_existe():
            return 'ZIP_MODE'
        try:
            from app.utils.path_manager import PathManager
            pm_exe = PathManager.get_mtk_file(_MTK_EXE_NAME)
            if pm_exe:
                return pm_exe
            for ext in ('mtk_gui.pyc', 'mtk_gui.py'):
                pm_script = PathManager.get_mtk_file(ext)
                if not pm_script:
                    continue
                return pm_script
        except Exception:
            pass
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
            exe_paths = [os.path.join(base_path, '_internal', 'app', 'views', 'mtk', _MTK_EXE_NAME), os.path.join(base_path, 'app', 'views', 'mtk', _MTK_EXE_NAME)]
            for exe_path in exe_paths:
                if not os.path.exists(exe_path):
                    continue
                return exe_path
            possible_paths = [os.path.join(base_path, '_internal', 'app', 'views', 'mtk', 'mtk_gui.pyc'), os.path.join(base_path, '_internal', 'app', 'views', 'mtk', 'mtk_gui.py'), os.path.join(base_path, 'app', 'views', 'mtk', 'mtk_gui.pyc'), os.path.join(base_path, 'app', 'views', 'mtk', 'mtk_gui.py')]
            for path in possible_paths:
                if not os.path.exists(path):
                    continue
                return path
            return possible_paths[0]
        current_dir = os.path.dirname(os.path.abspath(__file__))
        app_dir = os.path.dirname(current_dir)
        exe_dev = os.path.join(app_dir, 'views', 'mtk', _MTK_EXE_NAME)
        if os.path.exists(exe_dev):
            return exe_dev
        return os.path.join(app_dir, 'views', 'mtk', 'mtk_gui.py')
    def requer_extracao(self) -> bool:
        return self.mtk_path == 'ZIP_MODE'
    def extrair_zip(self, progress_callback=None) -> Tuple[bool, str]:
        sucesso, resultado = self.zip_extractor.extrair(progress_callback)
        if sucesso:
            self.mtk_path = resultado
            return (True, 'Ô£à Ferramenta preparada com sucesso!')
        mensagens = {'err_module': 'ÔÜá´©Å N├úo foi poss├¡vel iniciar a ferramenta.\n\n­ƒÆí Solu├º├úo:\nÔÇó Reinstale o TECH UNION SOLUTIONS\nÔÇó Contate o suporte: (85) 99750-7465', 'err_resource': 'ÔÜá´©Å Recurso n├úo encontrado.\n\n­ƒÆí Solu├º├úo:\nÔÇó Verifique se o antiv├¡rus n├úo removeu arquivos\nÔÇó Reinstale o TECH UNION SOLUTIONS', 'err_extract': 'ÔÜá´©Å Falha ao preparar ferramenta.\n\n­ƒÆí Solu├º├úo:\nÔÇó Verifique espa├ºo em disco\nÔÇó Verifique permiss├Áes do sistema\nÔÇó Reinstale o programa se persistir', 'err_corrupt': 'ÔÜá´©Å Arquivo de recursos corrompido.\n\n­ƒÆí Solu├º├úo:\nÔÇó Verifique seu antiv├¡rus\nÔÇó Reinstale o TECH UNION SOLUTIONS', 'err_decrypt': 'ÔÜá´©Å Falha na verifica├º├úo de seguran├ºa.\n\n­ƒÆí Solu├º├úo:\nÔÇó Reinstale o TECH UNION SOLUTIONS\nÔÇó Contate o suporte se persistir', 'err_system': 'ÔÜá´©Å Erro do sistema operacional.\n\n­ƒÆí Solu├º├úo:\nÔÇó Reinicie o computador\nÔÇó Execute como Administrador\nÔÇó Verifique seu antiv├¡rus'}
        return False, mensagens.get(resultado, mensagens['err_system'])
    def verificar_disponibilidade(self) -> Tuple[bool, str]:
        if self.mtk_path == 'ZIP_MODE':
            if self.zip_extractor.zip_existe():
                return (True, 'Ô£à Ferramenta pronta para uso')
            return (False, 'NEEDS_DOWNLOAD')
        if not os.path.exists(self.mtk_path):
            return (False, 'NEEDS_DOWNLOAD')
        is_exe = self.mtk_path.endswith('.exe')
        is_pyc = self.mtk_path.endswith('.pyc')
        is_py = self.mtk_path.endswith('.py')
        if not is_exe and not is_py and not is_pyc:
            return (False, 'ÔÜá´©Å Arquivo de ferramenta inv├ílido.\n\n­ƒÆí Solu├º├úo:\nÔÇó Reinstale o TECH UNION SOLUTIONS')
        if is_exe:
            return (True, 'Ô£à Ferramenta pronta para uso')
        if not sys.executable:
            return (False, 'ÔÜá´©Å Ambiente n├úo configurado.\n\n­ƒÆí Solu├º├úo:\nÔÇó Contate o suporte t├®cnico')
        return (True, 'Ô£à Ferramenta pronta para uso')
    def esta_rodando(self) -> bool:
        if self.mtk_process is None:
            return False
        return self.mtk_process.poll() is None
    def abrir(self) -> Tuple[bool, str]:
        try:
            if self.requer_extracao():
                return (False, 'NEEDS_EXTRACT')
            disponivel, mensagem = self.verificar_disponibilidade()
            if not disponivel:
                return False, mensagem
            if self.esta_rodando():
                return (True, 'Ferramenta j├í est├í em execu├º├úo')
            is_exe = self.mtk_path.endswith('.exe')
            if is_exe:
                comando = [self.mtk_path]
            else:
                python_executable = sys.executable
                if getattr(sys, 'frozen', False):
                    system_python = shutil.which('python') or shutil.which('python3')
                    if system_python:
                        python_executable = system_python
                    else:
                        possible_paths = ['C:\\Python39\\python.exe', 'C:\\Python310\\python.exe', 'C:\\Python311\\python.exe', 'C:\\Python312\\python.exe', 'C:\\Python313\\python.exe']
                        for path in possible_paths:
                            if not os.path.exists(path):
                                continue
                            python_executable = path
                        else:
                            return (False, 'ÔÜá´©Å Ambiente n├úo configurado corretamente.\n\n­ƒÆí Solu├º├úo:\nÔÇó Contate o suporte: (85) 99750-7465')
                comando = [python_executable, self.mtk_path]
            env = os.environ.copy()
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
                qt_plugin_path = os.path.join(base_path, 'PyQt5', 'Qt5', 'plugins')
                if os.path.exists(qt_plugin_path):
                    env['QT_PLUGIN_PATH'] = qt_plugin_path
                    env['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(qt_plugin_path, 'platforms')
            if sys.platform == 'win32':
                pythonw_path = None
                if not is_exe:
                    python_dir = os.path.dirname(comando[0])
                    pythonw_candidate = os.path.join(python_dir, 'pythonw.exe')
                    if os.path.exists(pythonw_candidate):
                        pythonw_path = pythonw_candidate
                        comando[0] = pythonw_path
                if pythonw_path or is_exe:
                    self.mtk_process = subprocess.Popen(comando, cwd=os.path.dirname(self.mtk_path), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = 0
                    self.mtk_process = subprocess.Popen(comando, startupinfo=startupinfo, cwd=os.path.dirname(self.mtk_path), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                self.mtk_process = subprocess.Popen(comando, cwd=os.path.dirname(self.mtk_path), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, start_new_session=True)
            self._monitor_thread = threading.Thread(target=self._monitorar_processo, daemon=True)
            self._monitor_thread.start()
            return (True, 'Ô£à Ferramenta iniciada com sucesso!')
        except FileNotFoundError:
            return (False, 'ÔÜá´©Å N├úo foi poss├¡vel iniciar a ferramenta.\n\n­ƒÆí Solu├º├úo:\nÔÇó Verifique seu antiv├¡rus\nÔÇó Reinstale o TECH UNION SOLUTIONS')
        except PermissionError:
            return (False, 'ÔÜá´©Å Permiss├úo negada.\n\n­ƒÆí Solu├º├úo:\nÔÇó Execute como Administrador\nÔÇó Verifique seu antiv├¡rus')
        except Exception:
            return (False, 'ÔÜá´©Å Erro ao iniciar ferramenta.\n\n­ƒÆí Solu├º├úo:\nÔÇó Reinicie o computador\nÔÇó Tente novamente\nÔÇó Contate o suporte se persistir')
    def _monitorar_processo(self):
        try:
            if self.mtk_process:
                self.mtk_process.wait()
        except Exception:
            pass
        self.mtk_process = None
        self.zip_extractor.limpar_cache()
        self.mtk_path = self._determinar_caminho_mtk()
    def fechar(self) -> bool:
        if not self.esta_rodando():
            return True
        try:
            self.mtk_process.terminate()
            self.mtk_process.wait(timeout=5)
            self.mtk_process = None
            self.zip_extractor.limpar_cache()
            self.mtk_path = self._determinar_caminho_mtk()
            return True
        except Exception:
            return False
    def limpar_cache(self):
        self.zip_extractor.limpar_cache()
        self.mtk_path = self._determinar_caminho_mtk()
    def obter_status(self) -> str:
        disponivel, _ = self.verificar_disponibilidade()
        if not disponivel:
            return 'ÔØî Ferramenta indispon├¡vel'
        if self.esta_rodando():
            return 'Ô£à Ferramenta em execu├º├úo'
        return 'ÔÅ©´©Å Ferramenta pronta para uso'
_mtk_manager_instance: Optional[MTKManager] = None
def get_mtk_manager() -> MTKManager:
    global _mtk_manager_instance
    if _mtk_manager_instance is None:
        _mtk_manager_instance = MTKManager()
    return _mtk_manager_instance
def limpar_cache_mtk():
    if _mtk_manager_instance:
        _mtk_manager_instance.limpar_cache()
