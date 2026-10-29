'''Gerenciador de visualizacao ao vivo ÔÇö processo isolado.'''
import os
import sys
import time
import shutil
import tempfile
import logging
import atexit
_log = logging.getLogger(__name__)
_instance = None
def get_scrcpy_manager():
    '''Retorna instancia singleton.'''
    global _instance
    if _instance is None:
        _instance = _ScrcpyManager()
    return _instance
class _ScrcpyManager:
    '''Controla ciclo de vida do processo de visualizacao.'''
    def __init__(self):
        self._proc = None
        self._temp_dir = None
        self._last_ts = 0
        self._on_stop_cb = None
        atexit.register(self.parar)
    def esta_ativo(self):
        '''Retorna True se processo ativo.'''
        try:
            if self._proc is None:
                return False
            from PyQt5.QtCore import QProcess
            return self._proc.state() != QProcess.NotRunning
        except Exception:
            return False
    _TIMEOUT_GLOBAL = 120
    def iniciar(self, parent=None, progress_callback=None, on_stop=None):
        '''Inicia visualizacao. Retorna (sucesso, msg_generica).'''
        from app.utils._lsv_cfg import _CD
        agora = time.monotonic()
        if agora - self._last_ts < _CD:
            return (False, '')
        self._last_ts = agora
        if self.esta_ativo():
            return (True, '')
        self._on_stop_cb = on_stop
        _deadline = time.monotonic() + self._TIMEOUT_GLOBAL
        try:
            adb_path = self._resolver_adb()
            if not self._verificar_device(adb_path):
                return (False, 'Nenhum dispositivo conectado. Conecte via USB.')
            if time.monotonic() > _deadline:
                return (False, 'Opera├º├úo expirou. Tente novamente.')
            exe_path = self._resolver_exe(progress_callback)
            if not exe_path:
                return (False, 'Recurso indispon├¡vel. Verifique conex├úo.')
            if time.monotonic() > _deadline:
                return (False, 'Opera├º├úo expirou. Tente novamente.')
            args = self._montar_args()
            from PyQt5.QtCore import QProcess
            self._proc = QProcess(parent)
            self._proc.setWorkingDirectory(os.path.dirname(exe_path))
            from PyQt5.QtCore import QProcessEnvironment
            env = QProcessEnvironment.systemEnvironment()
            from app.utils._lsv_cfg import _srv_path
            srv = _srv_path(self._temp_dir) if self._temp_dir else None
            if srv:
                env.insert('SCRCPY_SERVER_PATH', srv)
            if adb_path:
                env.insert('ADB', adb_path)
                adb_dir = os.path.dirname(adb_path)
                current = env.value('PATH', '')
                if adb_dir not in current:
                    env.insert('PATH', adb_dir + os.pathsep + current)
            self._proc.setProcessEnvironment(env)
            self._proc.finished.connect(self._on_finished)
            self._proc.start(exe_path, args)
            if not self._proc.waitForStarted(5000):
                return (False, 'N├úo foi poss├¡vel iniciar o recurso.')
            time.sleep(0.5)
            if not self.esta_ativo():
                return (False, 'O recurso encerrou inesperadamente.')
        except Exception:
            return (False, 'Erro interno. Tente novamente.')
        return (True, '')
    def parar(self):
        '''Encerra processo se ativo.'''
        try:
            if self._proc is not None:
                from PyQt5.QtCore import QProcess
                if self._proc.state() != QProcess.NotRunning:
                    self._proc.kill()
                    self._proc.waitForFinished(2000)
                self._proc = None
                return
        except Exception:
            self._proc = None
    def _on_finished(self):
        '''Callback quando processo termina.'''
        self._proc = None
        if self._on_stop_cb:
            try:
                self._on_stop_cb()
                return
            except Exception:
                pass
    def _verificar_device(self, adb_path):
        '''Verifica se ha device ADB conectado.'''
        import subprocess
        _bin = adb_path
        if not _bin:
            _bin = shutil.which('adb')
        if not _bin or not os.path.isfile(_bin):
            return False
        _flags = 134217728 if sys.platform == 'win32' else 0
        try:
            r = subprocess.run([_bin, 'devices'], capture_output=True, text=True, timeout=5, creationflags=_flags)
            for line in r.stdout.strip().split('\n')[1:]:
                if '\tdevice' in line:
                    return True
        except Exception:
            return False
        try:
            return False
        except Exception:
            return False
    def _resolver_exe(self, progress_callback=None):
        '''Resolve recurso principal.'''
        from app.utils._lsv_cfg import (_ZIP, _PK, _EXE, _HASH, _TEMP_PREFIX)
        try:
            from app.utils._res_loader import obter_ferramenta
        except Exception:
            return
        arq = obter_ferramenta(_ZIP, sha256_esperado=_HASH, progress_callback=progress_callback)
        if not arq:
            return
        self._limpar_temp_anterior()
        try:
            from pyzipper import AESZipFile
        except ImportError:
            return
        try:
            self._temp_dir = tempfile.mkdtemp(prefix=_TEMP_PREFIX)
            with AESZipFile(arq, 'r') as zf:
                zf.setpassword(_PK)
                zf.extractall(self._temp_dir)
            target = os.path.join(self._temp_dir, _EXE)
            if os.path.isfile(target):
                return target
        except Exception:
            return
    def _resolver_adb(self):
        '''Resolve dependencia de ponte sem disparar extracoes.'''
        try:
            from app.utils.adb_manager import ADBManager
            m = ADBManager()
            if m.adb_path and os.path.isfile(m.adb_path):
                return m.adb_path
        except Exception:
            pass
        w = shutil.which('adb')
        if w and os.path.isfile(w):
            return w
        _common = [os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Android', 'Sdk', 'platform-tools', 'adb.exe'), 'C:\\platform-tools\\adb.exe']
        for p in _common:
            if not p:
                continue
            if not os.path.isfile(p):
                continue
            return p
    def _montar_args(self):
        '''Prepara parametros de execucao.'''
        from app.utils._lsv_cfg import _ARGS
        return list(_ARGS)
    def _limpar_temp_anterior(self):
        '''Sanitiza sessao anterior.'''
        from app.utils._lsv_cfg import _TEMP_PREFIX
        if self._temp_dir and os.path.isdir(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir, ignore_errors=True)
            except Exception:
                pass
            self._temp_dir = None
        try:
            base = tempfile.gettempdir()
            for e in os.listdir(base):
                if not e.startswith(_TEMP_PREFIX):
                    continue
                if os.path.isdir(os.path.join(base, e)):
                    try:
                        try:
                            shutil.rmtree(os.path.join(base, e), ignore_errors=True)
                        except Exception:
                            continue
                    except Exception:
                        return
        except Exception:
            return
