'''Ref: administrativo/documentacao/2026-08-30_exy_engine.md'''
import logging
import subprocess
import threading
import time
from pathlib import Path
from typing import (Callable, Optional, Tuple)
from app.views.union_unlock.exy.engine import _cfg
_log = logging.getLogger(__name__)
LogCb = Optional[Callable[[str], None]]
def _emit(cb: LogCb, msg: str):
    if cb:
        cb(msg)
class ExynosEngine:
    '''Ref: administrativo/documentacao/2026-08-30_exy_engine.md'''
    def __init__(self):
        self._process = None
        self._cancel_event = threading.Event()
        self._lock = threading.Lock()
    @property
    def cli_available(self) -> bool:
        return _cfg.CLI_EXE_PATH.is_file()
    @property
    def cli_path(self) -> Path:
        return _cfg.CLI_EXE_PATH
    def cancel(self):
        '''Ref: administrativo/documentacao/2026-08-30_exy_engine.md'''
        self._cancel_event.set()
        with self._lock:
            if self._process and self._process.poll() is None:
                try:
                    self._process.terminate()
                    return
                except Exception:
                    pass
    def _reset(self):
        self._cancel_event.clear()
        self._process = None
    def boot_ramdisk(self, port: str, preset_json_path: str, log_cb: LogCb=None, timeout: int=None) -> Tuple[bool, str, int]:
        '''Ref: administrativo/documentacao/2026-08-30_exy_engine.md'''
        self._reset()
        if not self.cli_available:
            msg = 'Ferramentas Exynos indisponiveis'
            _emit(log_cb, msg)
            return False, msg, -1
        if not port:
            return (False, 'Dispositivo nao detectado', -1)
        if not Path(preset_json_path).is_file():
            return (False, 'Configuracao do processador nao encontrada', -1)
        timeout = timeout or _cfg.BOOT_TIMEOUT_S
        _pw = _cfg.CLI_PASSWORD
        cli_path = _cfg.CLI_EXE_PATH
        engine_dir = _cfg.ENGINE_DIR
        import os as _os
        _env = _os.environ.copy()
        _env['_EXY_K'] = _pw.decode('utf-8') if isinstance(_pw, bytes) else str(_pw)
        cmd = [str(cli_path), port, preset_json_path, _env['_EXY_K']]
        _emit(log_cb, 'Enviando ramdisk ao dispositivo...')
        _emit(log_cb, 'Configurando parametros de boot...')
        try:
            with self._lock:
                self._process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=str(engine_dir), env=_env, creationflags=subprocess.CREATE_NO_WINDOW)
        except OSError as av_err:
            if getattr(av_err, 'winerror', 0) == 225:
                _emit(log_cb, 'Protecao do sistema interferiu ÔÇö tentando alternativa...')
                _cfg.ENGINE_DIR = _cfg._resolve_engine_dir()
                _cfg.CLI_EXE_PATH = _cfg.ENGINE_DIR / _cfg.CLI_EXE
                engine_dir = _cfg.ENGINE_DIR
                cli_path = _cfg.CLI_EXE_PATH
                if not cli_path.is_file():
                    pass
        start = time.monotonic()
        while True:
            if self._cancel_event.is_set():
                self._kill_process()
                self._cleanup()
                return (False, 'Operacao cancelada', 5)
        exit_code = self._process.returncode
        exit_msg = _cfg.EXIT_CODES.get(exit_code, 'Resultado inesperado')
        if exit_code == 0:
            _emit(log_cb, f'Concluido com sucesso ({int(time.monotonic() - start)}s)')
            self._cleanup()
            return True, exit_msg, exit_code
        _emit(log_cb, f'Falha: {exit_msg}')
        self._cleanup()
        return False, exit_msg, exit_code
    def _kill_process(self):
        with self._lock:
            if self._process and self._process.poll() is None:
                try:
                    self._process.terminate()
                    self._process.wait(timeout=5)
                    return
                except subprocess.TimeoutExpired:
                    try:
                        self._process.kill()
                        self._process.wait(timeout=3)
                    except Exception:
                        pass
    def _cleanup(self):
        with self._lock:
            if self._process:
                try:
                    if self._process.stdout:
                        self._process.stdout.close()
                except Exception:
                    pass
                self._process = None
