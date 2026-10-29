import os
import re
import sys
import time
import logging
import subprocess
import threading
from typing import (List, Optional, Callable, NamedTuple)
from pathlib import Path
log = logging.getLogger(__name__)
if sys.platform == 'win32':
    _CREATION_FLAGS = subprocess.CREATE_NO_WINDOW
    _STARTUPINFO = subprocess.STARTUPINFO()
    _STARTUPINFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    _STARTUPINFO.wShowWindow = subprocess.SW_HIDE
else:
    _CREATION_FLAGS = 0
    _STARTUPINFO = None
class SPDPartition(NamedTuple):
    index: int
    name: str
    size_bytes: int
    size_str: str
_PART_RE = re.compile('(\\d+)\\s+(\\S+)\\s+(\\d+(?:\\.\\d+)?)(KB|MB|GB)\\s*$')
_SIZE_UNITS = {'KB': 1024, 'MB': 1048576, 'GB': 1073741824}
_BSL_VER_RE = re.compile('BSL_REP_VER:\\s*"([^"\\\\]+)')
_PROGRESS_RE = re.compile('(\\d+(?:\\.\\d+)?)\\s*%\\s*Speed\\s*:\\s*(\\d+(?:\\.\\d+)?)\\s*Mb/s', re.IGNORECASE)
_CONNECT_PHASE_WEIGHTS = {'CHECK_BAUD bootrom': 10, 'EXEC FDL1': 20, 'CHECK_BAUD FDL1': 15, 'CHANGE_BAUD FDL1': 10, 'EXEC FDL2': 30, 'DISABLE_TRANSCODE': 10, 'Reading Partition List': 5}
_PROTOCOL_NOISE_PREFIXES = ('send: type = 0x', 'recv: type = 0x', 'send (', 'recv (', '[=', '[ ', 'CurTime:', 'CurPort:', 'Waiting for dl_diag')
def _is_protocol_noise(line: str) -> bool:
    stripped = line.lstrip()
    for prefix in _PROTOCOL_NOISE_PREFIXES:
        if stripped.startswith(prefix):
            return True
    return False
def _parse_partition_line(line: str) -> Optional[SPDPartition]:
    m = _PART_RE.search(line)
    if not m:
        return
    idx = int(m.group(1))
    name = m.group(2)
    size_val = float(m.group(3))
    unit = m.group(4)
    size_bytes = int(size_val * _SIZE_UNITS.get(unit, 1))
    size_str = f'{int(size_val)}{unit}' if size_val == int(size_val) else f'{size_val}{unit}'
    return SPDPartition(index=idx, name=name, size_bytes=size_bytes, size_str=size_str)
def find_spd_dump(search_dirs: List[str]) -> str:
    for d in search_dirs:
        if not d or not os.path.isdir(d):
            continue
        candidate = os.path.join(d, 'spd_dump.exe')
        if not os.path.isfile(candidate):
            continue
        return candidate
    return ''
class SPDDumpProcess:
    def __init__(self, spd_dump_path: str, fdl1_path: str, fdl2_path: str, fdl1_addr: int, fdl2_addr: int, exec_addr: int=0, cwd: str='', log_cb: Optional[Callable[[str, str], None]]=None, use_kick: bool=False, verbose: int=1):
        self._exe = spd_dump_path
        self._fdl1 = fdl1_path
        self._fdl2 = fdl2_path
        self._fdl1_addr = fdl1_addr
        self._fdl2_addr = fdl2_addr
        self._exec_addr = exec_addr
        self._cwd = cwd or os.path.dirname(fdl1_path)
        self._log_cb = log_cb
        self._use_kick = use_kick
        self._verbose = verbose
        self._process = None
        self._reader_thread = None
        self._ready = threading.Event()
        self._output_lines = []
        self._partitions = []
        self._lock = threading.Lock()
        self._cmd_lock = threading.Lock()
        self._fatal_error = ''
        self._bsl_versions = []
        self._erase_done_event = threading.Event()
        self._write_done_event = threading.Event()
        self._read_done_event = threading.Event()
        self._last_op_ok = False
        self._connect_progress = 0
        self._connect_phases_seen = set()
        self.on_ready = None
        self.on_partitions = None
        self.on_exit = None
        self.on_connect_progress = None
        self.on_op_progress = None
    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None
    @property
    def is_ready(self) -> bool:
        return self._ready.is_set()
    @property
    def has_fatal_error(self) -> bool:
        return bool(self._fatal_error)
    @property
    def fatal_error(self) -> str:
        return self._fatal_error
    @property
    def partitions(self) -> List[SPDPartition]:
        with self._lock:
            return list(self._partitions)
    @property
    def bsl_version(self) -> str:
        with self._lock:
            return self._bsl_versions[-1] if self._bsl_versions else ''
    @property
    def bsl_versions(self) -> List[str]:
        with self._lock:
            return list(self._bsl_versions)
    @property
    def bsl_stage(self) -> str:
        with self._lock:
            for v in self._bsl_versions:
                if v.startswith('SPRD3'):
                    return 'SPRD3'
                if not v.startswith('SPRD4'):
                    continue
                return 'SPRD4'
        return ''
    def _log(self, msg: str, level: str='INFO'):
        log.log(getattr(logging, level.upper(), logging.INFO), f'[bin_spd] {msg}')
        if self._log_cb:
            try:
                self._log_cb(msg, level)
                return
            except Exception:
                pass
    def start(self, wait_seconds: int=300) -> bool:
        if self.is_running:
            self._log('Processo ja esta rodando', 'WARN')
            return True
        if not os.path.isfile(self._exe):
            log.error(f'[bin_spd] Executavel nao encontrado: {self._exe}')
            return False
        cmd = [self._exe, '--wait', str(wait_seconds)]
        if self._verbose:
            cmd += ['--verbose', str(self._verbose)]
        if self._use_kick:
            cmd += ['--kick']
        if self._exec_addr:
            cmd += ['exec_addr', f'0x{self._exec_addr:x}']
        cmd += ['fdl', self._fdl1, f'0x{self._fdl1_addr:X}', 'fdl', self._fdl2, f'0x{self._fdl2_addr:X}', 'exec']
        log.debug(f'[bin_spd] CWD: {self._cwd}')
        log.debug(f'[bin_spd] CMD: {' '.join(cmd)}')
        popen_kwargs = dict(stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1, cwd=self._cwd)
        if _CREATION_FLAGS:
            popen_kwargs['creationflags'] = _CREATION_FLAGS
        if _STARTUPINFO is not None:
            popen_kwargs['startupinfo'] = _STARTUPINFO
        try:
            self._process = subprocess.Popen(cmd, **popen_kwargs)
        except PermissionError:
            log.error(f'[bin_spd] Permissao negada: {self._exe}')
            self._log('Execucao bloqueada. Verifique o antivirus ou as permissoes do sistema.', 'ERROR')
            return False
        except (ValueError, TypeError) as e:
            log.warning('[bin_spd] Popen rejeitou creationflags/startupinfo (%s). Fallback para Popen sem janela oculta ÔÇö janela CMD pode aparecer neste ambiente.', e)
            popen_kwargs.pop('creationflags', None)
            popen_kwargs.pop('startupinfo', None)
            try:
                self._process = subprocess.Popen(cmd, **popen_kwargs)
            except OSError as e2:
                log.error(f'[bin_spd] Erro ao iniciar (fallback): {e2}')
                self._log('Erro ao iniciar o processo de comunicacao.', 'ERROR')
                e = None
                del e
                return False
        self._ready.clear()
        self._output_lines.clear()
        self._partitions.clear()
        self._connect_progress = 0
        self._connect_phases_seen = set()
        with self._lock:
            self._bsl_versions.clear()
        self._fatal_error = ''
        self._reader_thread = threading.Thread(target=self._read_output, daemon=True, name='spd_dump_reader')
        self._reader_thread.start()
        self._log('Processo iniciado ÔÇö aguardando dispositivo...', 'DEBUG')
        return True
    def wait_ready(self, timeout: float=120) -> bool:
        return self._ready.wait(timeout=timeout)
    def send_command(self, command: str) -> bool:
        if not self.is_running:
            self._log('Processo nao esta ativo', 'ERROR')
            return False
        try:
            with self._cmd_lock:
                log.debug(f'[bin_spd] -> {command}')
                self._process.stdin.write(command + '\n')
                self._process.stdin.flush()
        except (BrokenPipeError, OSError) as e:
            log.error(f'[bin_spd] Erro ao enviar comando: {e}')
            self._log('Erro na comunicacao com o dispositivo', 'ERROR')
            return False
        return True
    def list_partitions(self) -> bool:
        return self.send_command('p')
    def read_partition(self, name: str, output_path: str='', size_bytes: int=0, timeout: float=300.0) -> bool:
        self._read_done_event.clear()
        self._last_op_ok = False
        if output_path and size_bytes > 0:
            quoted = self._quote_path_for_spd(output_path)
            if not self.send_command(f'read_part {name} 0 {size_bytes} {quoted}'):
                return False
        elif output_path:
            import os as _os
            out_dir = _os.path.dirname(output_path)
            if out_dir:
                self.send_command(f'path {out_dir}')
            if not self.send_command(f'r {name}'):
                return False
        elif not self.send_command(f'r {name}'):
            return False
        if not self._read_done_event.wait(timeout=timeout):
            self._log('Timeout aguardando conclusao da leitura', 'ERROR')
            return False
        return self._last_op_ok
    @staticmethod
    def _quote_path_for_spd(path: str) -> str:
        try:
            if not path:
                return path
            if len(path) >= 2:
                if path[0] == '"' and path[-1] == '"' or path[0] == "'" and path[-1] == "'":
                    return path
            if '"' in path:
                return path
            return f'"{path}"'
        except Exception:
            return path
    def write_partition(self, name: str, file_path: str, timeout: float=180.0) -> bool:
        self._write_done_event.clear()
        self._last_op_ok = False
        quoted = self._quote_path_for_spd(file_path)
        if not self.send_command(f'w {name} {quoted}'):
            return False
        if not self._write_done_event.wait(timeout=timeout):
            self._log('Timeout aguardando confirmacao da gravacao', 'ERROR')
            return False
        return self._last_op_ok
    def write_force(self, name: str, file_path: str, timeout: float=180.0) -> bool:
        self._write_done_event.clear()
        self._last_op_ok = False
        quoted = self._quote_path_for_spd(file_path)
        if not self.send_command(f'w_force {name} {quoted}'):
            return False
        if not self._write_done_event.wait(timeout=timeout):
            self._log('Timeout aguardando confirmacao da gravacao', 'ERROR')
            return False
        return self._last_op_ok
    def erase_partition(self, name: str, timeout: float=120.0) -> bool:
        self._erase_done_event.clear()
        self._last_op_ok = False
        if not self.send_command(f'e {name}'):
            return False
        if not self._erase_done_event.wait(timeout=timeout):
            self._log('Timeout aguardando conclusao da operacao', 'ERROR')
            return False
        return self._last_op_ok
    def disable_avb(self) -> bool:
        return self.send_command('dis_avb')
    def skip_confirm(self, enabled: bool=True) -> bool:
        if enabled:
            return self.send_command(f'skip_confirm {1}')
        return None(f'{None}{0}')
    def reset_device(self) -> bool:
        return self.send_command('reset')
    def reboot_recovery(self) -> bool:
        return self.send_command('reboot-recovery')
    def reboot_fastboot(self) -> bool:
        return self.send_command('reboot-fastboot')
    def poweroff_device(self) -> bool:
        return self.send_command('poweroff')
    def set_save_path(self, path: str) -> bool:
        return self.send_command(f'path {path}')
    def set_blk_size(self, size: int=65535) -> bool:
        size = max(512, min(int(size), 65535))
        return self.send_command(f'blk_size {size}')
    def stop(self, timeout: float=5.0):
        if not self._process:
            return
        if self._process.poll() is None:
            try:
                self._process.terminate()
                self._process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                try:
                    self._process.kill()
                    self._process.wait(timeout=2)
                except Exception:
                    pass
        self._process = None
        self._ready.clear()
        self._log('Processo encerrado', 'DEBUG')
    _FATAL_PATTERNS = [('wrong command or wrong mode', 'Nao foi possivel conectar. Possivel erro nas conexoes fisicas ou versao de seguranca do dispositivo nao compativel. Verifique cabo, Test Point e tente novamente.'), ('usb_send failed', 'Conexao USB instavel. Solucoes (em ordem):\n  1. Use uma porta USB TRASEIRA (portas frontais tem cabos longos e sao suscetiveis a ruido).\n  2. Troque por um cabo USB curto e blindado.\n  3. Evite hubs USB ÔÇö conecte direto na placa-mae.\n  4. Se persistir, teste em USB 2.0 (mais estavel que 3.0).'), ('LIBUSB_ERROR_TIMEOUT', 'Timeout USB. O device parou de responder. Verifique cabo/porta e tente uma porta USB TRASEIRA (2.0).'), ('open(ttyUSB) failed', 'Porta de comunicacao nao encontrada. Verifique os drivers.'), ('find port failed', 'Dispositivo nao detectado. Verifique o cabo e o Test Point.'), ('timeout reached', 'Tempo limite atingido. Reconecte o dispositivo.'), ('ver expected', 'Dispositivo nao respondeu. Verifique se esta em Modo SPD.')]
    def _read_output(self):
        proc = self._process
        if proc is None:
            log.warning('[bin_spd] _read_output iniciado sem subprocess')
            return
        fdl2_detected = False
        collecting_parts = False
        try:
            for line in iter(proc.stdout.readline, ''):
                line = line.strip()
                if not line:
                    continue
                if _is_protocol_noise(line):
                    if line.lstrip().startswith(('[=', '[ ')):
                        m_prog = _PROGRESS_RE.search(line)
                        if m_prog and self.on_op_progress:
                            pass
            try:
                pct = int(float(m_prog.group(1)))
                spd_val = float(m_prog.group(2))
                self.on_op_progress(max(0, min(100, pct)), spd_val)
            except Exception:
                pass
            else:
                log.debug('[bin_spd] %s', line)
                if proc.poll() is not None:
                    pass
        except Exception as e:
            log.error(f'[bin_spd] Erro na leitura do output: {e}')
        try:
            pass
        except Exception as e:
            log.error(f'[bin_spd] Erro na leitura do output: {e}')
        try:
            exit_code = proc.returncode if proc.poll() is not None else -1
        except Exception:
            exit_code = -1
        log.debug(f'[bin_spd] Processo encerrado (exit_code={exit_code})')
        self._log('Processo encerrado', 'DEBUG')
        self._ready.set()
        if self.on_exit:
            try:
                self.on_exit(exit_code)
            except Exception:
                pass
# WARNING: Decompyle incomplete
