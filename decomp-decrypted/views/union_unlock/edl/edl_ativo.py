import logging
import os
import sys
import subprocess
import tempfile
from typing import (Dict, List, Optional)
_logger = logging.getLogger('edl_ativo')
def _log(msg: str):
    _logger.debug(msg)
def _secure_tmpfile(suffix: str='.tmp') -> tuple:
    try:
        if sys.platform == 'win32':
            base = os.environ.get('LOCALAPPDATA', tempfile.gettempdir())
        else:
            base = tempfile.gettempdir()
        edl_dir = os.path.join(base, '.union_edl', '_ldr')
        os.makedirs(edl_dir, exist_ok=True)
        if sys.platform == 'win32':
            import ctypes
            parent = os.path.dirname(edl_dir)
            attrs = ctypes.windll.kernel32.GetFileAttributesW(parent)
            if attrs == -1 or not attrs & 2:
                ctypes.windll.kernel32.SetFileAttributesW(parent, 8198)
        return tempfile.mkstemp(suffix=suffix, dir=edl_dir)
    except Exception:
        return tempfile.mkstemp(suffix=suffix)
def _matar_processos_edl():
    if sys.platform != 'win32':
        return
    for exe_name in ('edl-ng.exe', 'FRP_EDL.exe', 'emmcdl.exe', 'fh_loader.exe', 'QSaharaServer.exe'):
        try:
            result = subprocess.run(['taskkill', '/F', '/IM', exe_name], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=5)
            if result.returncode == 0:
                _log(f'Processo {exe_name} encerrado')
        except Exception:
            continue
def _detectar_formato_loader(dados: bytes) -> str:
    if not dados or len(dados) < 4:
        return 'bin'
    if dados[:3] == b'\x7fEL' and dados[3:4] in (b'F', b'E'):
        return 'elf'
    if len(dados) >= 8:
        header_type = int.from_bytes(dados[:4], 'little')
        if header_type in (5, 7):
            return 'mbn'
    if len(dados) >= 40 and dados[36:40] == b'\x7fELF':
        return 'mbn'
    return 'bin'
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QFrame, QMessageBox, QDialog, QScrollArea, QProgressDialog)
from PyQt5.QtCore import (QThread, pyqtSignal, Qt, QVariantAnimation, QTimer)
import time
from PyQt5.QtGui import (QFont, QPixmap, QTransform)
try:
    from app.views.union_unlock.edl.edl_auth_config import (AuthSelectorWidget, is_oppo_vip, is_oppo_vip2, extrair_vip_chipset)
    _AUTH_SELECTOR_OK = True
except ImportError:
    try:
        from edl_auth_config import (AuthSelectorWidget, is_oppo_vip, is_oppo_vip2, extrair_vip_chipset)
        _AUTH_SELECTOR_OK = True
    except ImportError:
        _AUTH_SELECTOR_OK = False
        is_oppo_vip = lambda x: bool(x) and x.startswith('oppo_vip') and not x.startswith('oppo_vip2')
        is_oppo_vip2 = lambda x: bool(x) and x.startswith('oppo_vip2')
        extrair_vip_chipset = lambda x: None
try:
    from app.views.union_unlock.edl.frp_xiaomi_auth import executar_frp_auth
    _FRP_AUTH_OK = True
except ImportError:
    try:
        from frp_xiaomi_auth import executar_frp_auth
        _FRP_AUTH_OK = True
    except ImportError:
        _FRP_AUTH_OK = False
try:
    from app.views.union_unlock.edl.frp_samsung import executar_frp_samsung
    _FRP_SAMSUNG_OK = True
except ImportError:
    try:
        from frp_samsung import executar_frp_samsung
        _FRP_SAMSUNG_OK = True
    except ImportError:
        _FRP_SAMSUNG_OK = False
try:
    from app.views.union_unlock.edl.frp_oppo_vip import executar_frp_vip
    _FRP_VIP_OK = True
except ImportError:
    try:
        from frp_oppo_vip import executar_frp_vip
        _FRP_VIP_OK = True
    except ImportError:
        _FRP_VIP_OK = False
try:
    from app.views.union_unlock.edl._qcom_io import executar_frp_serial
    _FRP_VIP2_OK = True
except ImportError:
    try:
        from _qcom_io import executar_frp_serial
        _FRP_VIP2_OK = True
    except ImportError:
        _FRP_VIP2_OK = False
try:
    from app.views.union_unlock.edl.micloud_edl import executar_micloud_edl
    _MICLOUD_EDL_OK = True
except ImportError:
    try:
        from micloud_edl import executar_micloud_edl
        _MICLOUD_EDL_OK = True
    except ImportError:
        _MICLOUD_EDL_OK = False
def _is_micloud_op(chave: str, op: dict) -> bool:
    ck = chave.lower()
    cl = op.get('label', '').lower()
    return 'mi_cloud' in ck or 'micloud' in ck or 'mi cloud' in cl or 'mi account' in cl or 'reset_mi' in ck
_PALETA = {'samsung': {'PRIMARY': '#1428A0', 'PRIMARY_HOVER': '#0D1B69', 'SUCCESS': '#27ae60', 'ERROR': '#e74c3c', 'WARNING': '#f39c12', 'TEXT': '#2c3e50', 'TEXT_MUTED': '#7f8c8d', 'TEXT_WHITE': '#ffffff', 'BORDER': '#bdc3c7', 'BACKGROUND': '#f5f5f5', 'BACKGROUND_DARK': '#e8e8e8', 'BACKGROUND_WHITE': '#ffffff'}, 'xiaomi': {'PRIMARY': '#ff6700', 'PRIMARY_HOVER': '#e55d00', 'SUCCESS': '#27ae60', 'ERROR': '#e74c3c', 'WARNING': '#f39c12', 'TEXT': '#2c3e50', 'TEXT_MUTED': '#7f8c8d', 'TEXT_WHITE': '#ffffff', 'BORDER': '#bdc3c7', 'BACKGROUND': '#f5f5f5', 'BACKGROUND_DARK': '#e8e8e8', 'BACKGROUND_WHITE': '#ffffff'}, 'oppo': {'PRIMARY': '#1a9c2d', 'PRIMARY_HOVER': '#158024', 'SUCCESS': '#27ae60', 'ERROR': '#e74c3c', 'WARNING': '#f39c12', 'TEXT': '#2c3e50', 'TEXT_MUTED': '#7f8c8d', 'TEXT_WHITE': '#ffffff', 'BORDER': '#bdc3c7', 'BACKGROUND': '#f5f5f5', 'BACKGROUND_DARK': '#e8e8e8', 'BACKGROUND_WHITE': '#ffffff'}, 'vivo': {'PRIMARY': '#415fff', 'PRIMARY_HOVER': '#2e4de6', 'SUCCESS': '#27ae60', 'ERROR': '#e74c3c', 'WARNING': '#f39c12', 'TEXT': '#2c3e50', 'TEXT_MUTED': '#7f8c8d', 'TEXT_WHITE': '#ffffff', 'BORDER': '#bdc3c7', 'BACKGROUND': '#f5f5f5', 'BACKGROUND_DARK': '#e8e8e8', 'BACKGROUND_WHITE': '#ffffff'}, 'realme': {'PRIMARY': '#ffc800', 'PRIMARY_HOVER': '#e6b400', 'SUCCESS': '#27ae60', 'ERROR': '#e74c3c', 'WARNING': '#f39c12', 'TEXT': '#2c3e50', 'TEXT_MUTED': '#7f8c8d', 'TEXT_WHITE': '#2c3e50', 'BORDER': '#bdc3c7', 'BACKGROUND': '#f5f5f5', 'BACKGROUND_DARK': '#e8e8e8', 'BACKGROUND_WHITE': '#ffffff'}}
_PALETA_DEFAULT = _PALETA['samsung']
def _cor(marca: str, chave: str) -> str:
    return _PALETA.get(marca.lower(), _PALETA_DEFAULT).get(chave, '#000000')
class _EdlNgWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    def __init__(self, edl_path, loader_path, memoria, sequencia, reset_apos):
        super().__init__()
        self._edl = edl_path
        self._loader = loader_path
        self._mem = 'Sdcc' if memoria == 'emmc' else 'Ufs'
        self._seq = sequencia
        self._reset = reset_apos
        self._stop = False
    def cancelar(self):
        self._stop = True
    def _exec(self, args):
        cmd = [self._edl, '--loader', self._loader, '--memory', self._mem] + args
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=os.path.dirname(self._edl), creationflags=flags)
        ok = False
        no_dev = False
        for line in iter(proc.stdout.readline, ''):
            if self._stop:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=3)
                return (False, 'Cancelado pelo usu├írio')
            linha = line.rstrip()
            self.log_signal.emit(linha)
            ll = linha.lower()
            if 'found device' in ll:
                self.status_signal.emit('connected')
                self.progress_signal.emit(40)
            if 'loader uploaded' in ll and 'started successfully' in ll:
                self.status_signal.emit('processing')
                self.progress_signal.emit(50)
            if 'successfully erased' in ll:
                ok = True
                self.progress_signal.emit(80)
            elif 'power command' in ll and 'sent successfully' in ll:
                ok = True
            if 'no qualcomm edl devices found' not in ll:
                continue
            no_dev = True
            continue
        proc.wait()
        if no_dev:
            return (False, 'Dispositivo n├úo encontrado!\n\nConecte o aparelho em modo EDL antes de iniciar.')
        return ok or proc.returncode == 0, ''
    def run(self):
        try:
            for f in self._edl, self._loader:
                if os.path.exists(f):
                    continue
                self.status_signal.emit('error')
                self.finished_signal.emit(False, 'Componente n├úo encontrado!\n\nReinstale o programa ou entre em contato com o suporte.')
                return
            self.status_signal.emit('waiting')
            self.progress_signal.emit(10)
            total = len(self._seq)
            for i, cmd_str in enumerate(self._seq, 1):
                if self._stop:
                    self.finished_signal.emit(False, 'Cancelado')
                    return
                self.log_signal.emit(f'\n{'============================================================'}')
                self.log_signal.emit(f'  ETAPA {i}/{total}: {cmd_str}')
                self.log_signal.emit(f'{'============================================================'}')
                self.progress_signal.emit(10 + int(70 * i / (total + 1)))
                ok, motivo = self._exec(cmd_str.split())
                if ok:
                    self.log_signal.emit(f'  ETAPA {i} concluida com sucesso!')
                    continue
                self.log_signal.emit(f'  ETAPA {i} FALHOU')
                self.log_signal.emit('ERRO na operacao')
                self.status_signal.emit('error')
                self.finished_signal.emit(False, motivo or 'Falha na opera├º├úo.\n\nReconecte o dispositivo em modo EDL e tente novamente.')
                return
            if self._reset and not self._stop:
                self.log_signal.emit(f'\n{'============================================================'}')
                self.log_signal.emit('  Reiniciando dispositivo...')
                self.log_signal.emit(f'{'============================================================'}')
                self._exec(['reset'])
            self.progress_signal.emit(100)
            self.status_signal.emit('success')
            self.finished_signal.emit(True, 'FRP removido com sucesso!\n\nO aparelho ir├í reiniciar.')
            return
        except OSError as e:
            self.status_signal.emit('error')
            if hasattr(e, 'winerror') and e.winerror == 740:
                self.finished_signal.emit(False, 'Execute como Administrador!\n\nClique com bot├úo direito no programa\ne selecione "Executar como administrador".')
        except Exception as e:
            _log(f'Erro inesperado na operacao: {e}')
            self.status_signal.emit('error')
            self.finished_signal.emit(False, 'Erro inesperado na execu├º├úo.\n\nReconecte o dispositivo e tente novamente.')
class _FrpEdlWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    def __init__(self, frp_edl, loader, memoria):
        super().__init__()
        self._exe = frp_edl
        self._ldr = loader
        self._mem = 'ufs' if memoria == 'ufs' else 'emmc'
        self._stop = False
    def cancelar(self):
        self._stop = True
    def run(self):
        try:
            for f in self._exe, self._ldr:
                if os.path.exists(f):
                    continue
                self.status_signal.emit('error')
                self.finished_signal.emit(False, 'Componente n├úo encontrado!\n\nReinstale o programa ou entre em contato com o suporte.')
                return
            self.status_signal.emit('waiting')
            self.progress_signal.emit(10)
            cmd = [self._exe, '-m', self._mem, '-l', self._ldr, 'resetfrp']
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=os.path.dirname(self._exe), creationflags=flags)
            conectou = False
            erro = None
            for line in iter(proc.stdout.readline, ''):
                if self._stop:
                    proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)
            else:
                self.finished_signal.emit(False, 'Cancelado')
                return
        except OSError as e:
            self.status_signal.emit('error')
            if hasattr(e, 'winerror') and e.winerror == 740:
                self.finished_signal.emit(False, 'Execute como Administrador!\n\nClique com bot├úo direito no programa\ne selecione "Executar como administrador".')
        except Exception as e:
            _log(f'Erro inesperado no FRP_EDL: {e}')
            self.status_signal.emit('error')
            self.finished_signal.emit(False, 'Erro inesperado na execu├º├úo.\n\nReconecte o dispositivo e tente novamente.')
class _FrpXiaomiAuthWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str, dict)
    def __init__(self, loader_path: str, memoria: str, particoes, auth_manufacturer: str='xiaomi'):
        super().__init__()
        self._loader = loader_path
        self._mem = memoria
        self._particoes = particoes
        self._auth = auth_manufacturer
        self._cancelado = False
    def cancelar(self):
        self._cancelado = True
        _matar_processos_edl()
    def run(self):
        try:
            self.status_signal.emit('connected')
            ok, msg, data = executar_frp_auth(loader_path=self._loader, memoria=self._mem, particoes_alvo=self._particoes, log_cb=self._emit, progress_cb=self.progress_signal.emit, auth_manufacturer=self._auth)
            if self._cancelado:
                self.status_signal.emit('error')
                self.finished_signal.emit(False, 'Cancelado pelo usuario.', {})
                return
            self.status_signal.emit('success' if ok else 'error')
            self.finished_signal.emit(ok, msg, data)
            return
        except Exception as e:
            _log(f'Erro _FrpXiaomiAuthWorker: {e}')
            self.status_signal.emit('error')
            self.finished_signal.emit(False, 'Erro inesperado.\n\nReconecte o dispositivo e tente novamente.', {})
    def _emit(self, msg: str):
        _log(msg)
        self.log_signal.emit(msg)
class _FrpSamsungWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str, dict)
    def __init__(self, loader_path: str, memoria: str, particoes=None):
        super().__init__()
        self._loader = loader_path
        self._mem = memoria
        self._particoes = particoes or ['persistent']
        self._cancelado = False
    def cancelar(self):
        self._cancelado = True
        _matar_processos_edl()
    def run(self):
        try:
            self.status_signal.emit('connected')
            ok, msg, data = executar_frp_samsung(loader_path=self._loader, memoria=self._mem, particoes_alvo=self._particoes, log_cb=self._emit, progress_cb=self.progress_signal.emit)
            if self._cancelado:
                self.status_signal.emit('error')
                self.finished_signal.emit(False, 'Cancelado pelo usuario.', {})
                return
            self.status_signal.emit('success' if ok else 'error')
            self.finished_signal.emit(ok, msg, data)
            return
        except Exception as e:
            _log(f'Erro _FrpSamsungWorker: {e}')
            self.status_signal.emit('error')
            self.finished_signal.emit(False, 'Erro inesperado.\n\nReconecte o dispositivo e tente novamente.', {})
    def _emit(self, msg: str):
        _log(msg)
        self.log_signal.emit(msg)
class _FrpVipWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str, dict)
    def __init__(self, loader_path: str, memoria: str, particoes: list, digest_data: bytes, sign_data: bytes):
        super().__init__()
        self._loader = loader_path
        self._mem = memoria
        self._particoes = particoes
        self._digest = digest_data
        self._sign = sign_data
        self._cancelado = False
    def cancelar(self):
        self._cancelado = True
        _matar_processos_edl()
    def run(self):
        try:
            self.status_signal.emit('connected')
            ok, msg, data = executar_frp_vip(loader_path=self._loader, memoria=self._mem, digest_data=self._digest, sign_data=self._sign, particoes_alvo=self._particoes, log_cb=self._emit, progress_cb=self.progress_signal.emit)
            if self._cancelado:
                self.status_signal.emit('error')
                self.finished_signal.emit(False, 'Cancelado pelo usuario.', {})
                return
            self.status_signal.emit('success' if ok else 'error')
            self.finished_signal.emit(ok, msg, data)
            return
        except Exception as e:
            _log(f'Erro _FrpVipWorker: {e}')
            self.status_signal.emit('error')
            self.finished_signal.emit(False, 'Erro inesperado.\n\nReconecte o dispositivo e tente novamente.', {})
    def _emit(self, msg: str):
        _log(msg)
        self.log_signal.emit(msg)
class _FrpVip2Worker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str, dict)
    def __init__(self, port: str, loader_path: str, qsahara_path: str, memoria: str, digest_data: bytes, sign_data: bytes):
        super().__init__()
        self._port = port
        self._loader = loader_path
        self._qsahara = qsahara_path
        self._mem = memoria
        self._digest = digest_data
        self._sign = sign_data
        self._cancelado = False
    def cancelar(self):
        self._cancelado = True
    def run(self):
        try:
            self.status_signal.emit('connected')
            ok, msg, data = executar_frp_serial(port=self._port, loader_path=self._loader, qsahara_path=self._qsahara, memory=self._mem, digest=self._digest, sign=self._sign, log_cb=self._emit, progress_cb=self.progress_signal.emit)
            if self._cancelado:
                self.status_signal.emit('error')
                self.finished_signal.emit(False, 'Cancelado pelo usuario.', {})
                return
            self.status_signal.emit('success' if ok else 'error')
            self.finished_signal.emit(ok, msg, data)
            return
        except Exception as e:
            _log(f'Erro _FrpVip2Worker: {e}')
            self.status_signal.emit('error')
            self.finished_signal.emit(False, 'Erro inesperado.\n\nReconecte o dispositivo e tente novamente.', {})
    def _emit(self, msg: str):
        _log(msg)
        self.log_signal.emit(msg)
class _MiCloudEdlWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str, dict)
    def __init__(self, loader_path: str, memoria: str, auth_manufacturer: str='xiaomi'):
        super().__init__()
        self._loader = loader_path
        self._mem = memoria
        self._auth = auth_manufacturer
        self._cancelado = False
    def cancelar(self):
        self._cancelado = True
        _matar_processos_edl()
    def run(self):
        try:
            self.status_signal.emit('connected')
            ok, msg, data = executar_micloud_edl(loader_path=self._loader, memoria=self._mem, log_cb=self._emit, progress_cb=self.progress_signal.emit, auth_manufacturer=self._auth)
            if self._cancelado:
                self.status_signal.emit('error')
                self.finished_signal.emit(False, 'Cancelado pelo usuario.', {})
                return
            self.status_signal.emit('success' if ok else 'error')
            self.finished_signal.emit(ok, msg, data)
            return
        except Exception as e:
            _log(f'Erro _MiCloudEdlWorker: {e}')
            self.status_signal.emit('error')
            self.finished_signal.emit(False, 'Erro inesperado.\n\nReconecte o dispositivo e tente novamente.', {})
    def _emit(self, msg: str):
        _log(msg)
        self.log_signal.emit(msg)
class EdlAtivoWidget(QWidget):
    redirecionar_particoes = pyqtSignal(dict)
    def __init__(self, dados: Dict, marca: str, img_dir: str, tools_dir: str, parent=None):
        super().__init__(parent)
        self._dados = dados
        self._marca = marca.lower()
        self._img_dir = img_dir
        self._tools_dir = tools_dir
        self._worker = None
        self._frp_auth_worker = None
        self._em_exec = False
        self._ldr_tmp = None
        self.setup_ui()
        self._init_animation()
    def _c(self, chave: str) -> str:
        return _cor(self._marca, chave)
    def _img(self, nome: str) -> str:
        return os.path.join(self._img_dir, nome)
    def _tool(self, nome: str) -> str:
        return os.path.join(self._tools_dir, nome)
    def _garantir_sync_fresco(self) -> None:
        try:
            from app.views.union_unlock.edl.edl_sync import get_sync
        except ImportError:
            try:
                from edl_sync import get_sync
            except ImportError:
                return
        try:
            sync = get_sync()
            if sync.pode_sincronizar():
                _log('Sync preventivo pre-FRP...')
                sync.sincronizar()
                return
        except Exception:
            return
    @staticmethod
    def _scan_porta_edl():
        try:
            from serial.tools import list_ports
            for p in list_ports.comports():
                hwid = (p.hwid or '').lower()
                desc = (p.description or '').lower()
                if '05c6' in hwid:
                    if '9008' not in hwid:
                        if '9008' not in desc:
                            continue
                        if 'qdloader' in desc or 'qualcomm' in desc:
                            return p.device
            return
        except Exception:
            return
    def _aguardar_dispositivo_edl(self, timeout_s: int=120) -> bool:
        modelo = self._dados.get('modelo', '')
        dlg = QProgressDialog(f'Preparando operacao para {modelo}...', 'Cancelar', 0, 100, self)
        dlg.setWindowTitle('Verificacao EDL')
        dlg.setMinimumWidth(380)
        dlg.setWindowModality(Qt.WindowModal)
        dlg.setAutoClose(False)
        dlg.setAutoReset(False)
        dlg.setMinimumDuration(0)
        cancelado = False
        def _check_cancel():
            nonlocal cancelado
            from PyQt5.QtWidgets import QApplication
            QApplication.processEvents()
            if dlg.wasCanceled():
                cancelado = True
            return cancelado
        dlg.setLabelText('Verificando dados do modelo...')
        dlg.setValue(10)
        if _check_cancel():
            dlg.close()
            return False
        self._garantir_sync_fresco()
        dlg.setLabelText('Aguardando dispositivo EDL...\n\nConecte o aparelho em modo EDL (Test Point ou Botoes)')
        dlg.setValue(30)
        porta = self._scan_porta_edl()
        if not porta:
            t0 = time.monotonic()
            while time.monotonic() - t0 < timeout_s:
                if _check_cancel():
                    dlg.close()
                    return False
                porta = self._scan_porta_edl()
                if porta:
                    break
                pct = 30 + int(40 * (time.monotonic() - t0) / timeout_s)
                dlg.setValue(min(pct, 69))
                from PyQt5.QtWidgets import QApplication
                QApplication.processEvents()
                time.sleep(1.5)
        if not porta:
            dlg.close()
            QMessageBox.warning(self, 'Tempo esgotado', 'Dispositivo nao detectado.\n\nVerifique se o aparelho esta em modo EDL e tente novamente.')
            return False
        _log(f'Dispositivo EDL detectado: {porta}')
        dlg.setLabelText('Dispositivo conectado!\n\nPreparando operacao...')
        dlg.setValue(70)
        if _check_cancel():
            dlg.close()
            return False
        try:
            from app.views.union_unlock.edl.edl_sync import get_sync
        except ImportError:
            from edl_sync import get_sync
        try:
            loader_bytes = get_sync().download_loader(self._dados['srv_id'])
        except Exception as _dl_err:
            _log(f'download_loader falhou: {_dl_err}')
            loader_bytes = None
        if not loader_bytes:
            dlg.close()
            QMessageBox.critical(self, 'Erro', 'Dados nao disponiveis para este modelo.\n\nAtualize o sistema ou verifique sua conexao.')
            return False
        dlg.setValue(85)
        if _check_cancel():
            dlg.close()
            return False
        try:
            fd, tmp = _secure_tmpfile(suffix='.tmp')
            with os.fdopen(fd, 'wb') as f:
                f.write(loader_bytes)
            self._ldr_tmp = tmp
        except Exception:
            dlg.close()
            QMessageBox.critical(self, 'Erro', 'Erro ao preparar componente.\n\nVerifique espaco em disco e tente novamente.')
            return False
        dlg.setValue(100)
        dlg.close()
        return True
    def setup_ui(self):
        dados = self._dados
        ops = dados.get('operacoes', {})
        self.setStyleSheet(f'background-color: {self._c('BACKGROUND')};')
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 15)
        main_layout.setSpacing(25)
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 10, 0, 0)
        ll.setSpacing(6)
        ll.setAlignment(Qt.AlignTop)
        lbl_modelo = QLabel(dados.get('modelo', ''))
        lbl_modelo.setFont(QFont('Segoe UI', 18, QFont.Bold))
        lbl_modelo.setStyleSheet(f'color: {self._c('TEXT')};')
        lbl_modelo.setWordWrap(True)
        ll.addWidget(lbl_modelo)
        ll.addSpacing(12)
        lbl_suporte = QLabel('Suporte: Qualcomm EDL')
        lbl_suporte.setFont(QFont('Segoe UI', 11))
        lbl_suporte.setStyleSheet(f'color: {self._c('TEXT_MUTED')};')
        ll.addWidget(lbl_suporte)
        lbl_modo = QLabel('Modo: EDL (Qualcomm)')
        lbl_modo.setFont(QFont('Segoe UI', 10))
        lbl_modo.setStyleSheet(f'color: {self._c('PRIMARY')};')
        ll.addWidget(lbl_modo)
        ll.addSpacing(12)
        self._botoes = {}
        for chave, op in ops.items():
            label = op.get('label', chave.title())
            btn = QPushButton(label)
            btn.setFixedHeight(40)
            btn.setMinimumWidth(140)
            btn.setMaximumWidth(200)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFont(QFont('Segoe UI', 12, QFont.Bold))
            btn.setStyleSheet(f'\n                QPushButton {{ background-color: {self._c('PRIMARY')}; color: {self._c('TEXT_WHITE')};\n                    border: none; border-radius: 20px; }}\n                QPushButton:hover {{ background-color: {self._c('PRIMARY_HOVER')}; }}\n                QPushButton:disabled {{ background-color: {self._c('BORDER')}; }}\n            ')
            btn.clicked.connect((lambda checked, k=chave: self._executar(k)))
            ll.addWidget(btn)
            self._botoes[chave] = btn
            continue
        ll.addSpacing(10)
        if _AUTH_SELECTOR_OK:
            self._auth_selector = AuthSelectorWidget()
            ll.addWidget(self._auth_selector)
        else:
            self._auth_selector = None
        ll.addSpacing(10)
        self.btn_parar = QPushButton('Parar')
        self.btn_parar.setFixedSize(100, 35)
        self.btn_parar.setCursor(Qt.PointingHandCursor)
        self.btn_parar.setFont(QFont('Segoe UI', 11))
        self.btn_parar.setStyleSheet(f'\n            QPushButton {{ background-color: {self._c('BACKGROUND_DARK')}; color: {self._c('TEXT')};\n                border: 1px solid {self._c('BORDER')}; border-radius: 17px; }}\n            QPushButton:hover {{ background-color: {self._c('BORDER')}; }}\n        ')
        self.btn_parar.clicked.connect(self._parar)
        ll.addWidget(self.btn_parar)
        self.barra = QProgressBar()
        self.barra.setMaximumWidth(300)
        self.barra.setFixedHeight(18)
        self.barra.setValue(0)
        self.barra.setTextVisible(False)
        self.barra.setStyleSheet(f'\n            QProgressBar {{ border: 1px solid {self._c('BORDER')}; border-radius: 9px;\n                background-color: {self._c('BACKGROUND_WHITE')}; }}\n            QProgressBar::chunk {{ background-color: {self._c('PRIMARY')}; border-radius: 8px; }}\n        ')
        ll.addWidget(self.barra)
        ll.addSpacing(8)
        self.btn_tp = QPushButton('­ƒôì Test Point', self)
        self.btn_tp.setFixedSize(130, 30)
        self.btn_tp.setCursor(Qt.PointingHandCursor)
        self.btn_tp.setFont(QFont('Segoe UI', 9, QFont.Bold))
        self.btn_tp.setToolTip('Ver imagem do Test Point deste modelo')
        self.btn_tp.setStyleSheet(f'\n            QPushButton {{ background-color: {self._c('WARNING')};\n                color: #ffffff; border: none; border-radius: 6px; }}\n            QPushButton:hover {{ background-color: #e67e22; }}\n        ')
        self.btn_tp.clicked.connect(self._mostrar_testpoint)
        ll.addWidget(self.btn_tp)
        self.btn_tp.setVisible(dados.get('tem_testpoint', False))
        ll.addStretch()
        self.lbl_aviso = QLabel('ÔÜá´©Å Conecte em EDL ANTES de clicar | Driver: Qualcomm Serial')
        self.lbl_aviso.setFont(QFont('Segoe UI', 8))
        self.lbl_aviso.setStyleSheet(f'color: {self._c('PRIMARY')}; padding: 2px;')
        self.lbl_aviso.setWordWrap(True)
        ll.addWidget(self.lbl_aviso)
        ll.addSpacing(4)
        self.lbl_status = QLabel('Pronto para iniciar')
        self.lbl_status.setFont(QFont('Segoe UI', 11))
        self.lbl_status.setStyleSheet(f'color: {self._c('TEXT_MUTED')};')
        ll.addWidget(self.lbl_status)
        main_layout.addWidget(left, stretch=1)
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setAlignment(Qt.AlignCenter)
        self.phone_container = QFrame()
        self.phone_container.setFixedSize(250, 250)
        self.phone_container.setStyleSheet(f'background-color: {self._c('BACKGROUND_DARK')}; border-radius: 125px; border: 2px solid {self._c('BORDER')};')
        fl = QVBoxLayout(self.phone_container)
        fl.setAlignment(Qt.AlignCenter)
        self.phone_image = QLabel()
        self.phone_image.setFixedSize(140, 140)
        self.phone_image.setAlignment(Qt.AlignCenter)
        fl.addWidget(self.phone_image)
        rl.addWidget(self.phone_container)
        self.lbl_phone = QLabel('')
        self.lbl_phone.setAlignment(Qt.AlignCenter)
        self.lbl_phone.setFont(QFont('Segoe UI', 11))
        self.lbl_phone.setStyleSheet(f'color: {self._c('TEXT_MUTED')}; margin-top: 15px;')
        self.lbl_phone.setWordWrap(True)
        rl.addWidget(self.lbl_phone)
        self._lbl_watermark = None
        main_layout.addWidget(right, stretch=1)
        self._set_phone_image('notfound')
    def _init_animation(self):
        self.spinner_anim = QVariantAnimation()
        self.spinner_anim.setDuration(3000)
        self.spinner_anim.setStartValue(0)
        self.spinner_anim.setEndValue(360)
        self.spinner_anim.setLoopCount(-1)
        self.spinner_anim.valueChanged.connect(self._rotate_phone)
        self.original_pixmap = None
    def _set_phone_image(self, status):
        images = {'notfound': 'phone_notfound.png', 'loading': 'phone_loading.png', 'connected': 'phone_connected.png', 'success': 'phone_success.png', 'error': 'phone_error.png'}
        styles = {'notfound': f'background-color:{self._c('BACKGROUND_DARK')};border-radius:125px;border:2px solid {self._c('BORDER')};', 'loading': f'background-color:{self._c('BACKGROUND_DARK')};border-radius:125px;border:2px solid {self._c('PRIMARY')};', 'connected': f'background-color:{self._c('BACKGROUND_DARK')};border-radius:125px;border:2px solid {self._c('PRIMARY')};', 'success': f'background-color:{self._c('SUCCESS')};border-radius:125px;border:2px solid {self._c('SUCCESS')};', 'error': f'background-color:{self._c('ERROR')};border-radius:125px;border:2px solid {self._c('ERROR')};'}
        self.phone_container.setStyleSheet(styles.get(status, styles['notfound']))
        path = self._img(images.get(status, 'phone_notfound.png'))
        if os.path.exists(path):
            img_sz = 120
            pix = QPixmap(path).scaled(img_sz, img_sz, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.phone_image.setPixmap(pix)
            if status == 'loading':
                self.original_pixmap = pix
                return
            return
        self.phone_image.setText('­ƒô▒')
        self.phone_image.setStyleSheet(f'font-size:40px;color:{self._c('TEXT')};')
    def _rotate_phone(self, angle):
        if self.original_pixmap:
            rot = self.original_pixmap.transformed(QTransform().rotate(angle), Qt.SmoothTransformation)
            dx = (rot.width() - self.original_pixmap.width()) // 2
            dy = (rot.height() - self.original_pixmap.height()) // 2
            self.phone_image.setPixmap(rot.copy(dx, dy, self.original_pixmap.width(), self.original_pixmap.height()))
    def _mostrar_testpoint(self):
        modelo = self._dados.get('modelo', '')
        srv_id = self._dados.get('srv_id')
        if not srv_id:
            return
        try:
            from app.views.union_unlock.edl.edl_sync import get_sync
        except ImportError:
            from edl_sync import get_sync
        img_bytes = get_sync().download_testpoint(srv_id)
        if not img_bytes:
            QMessageBox.information(self, 'Test Point', f'Imagem de Test Point n├úo dispon├¡vel para {modelo}.\n\nVerifique sua conex├úo ou tente novamente.')
            return
        pix = QPixmap()
        if not pix.loadFromData(img_bytes):
            QMessageBox.warning(self, 'Test Point', 'N├úo foi poss├¡vel carregar a imagem.')
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(f'Test Point ÔÇö {modelo}')
        dlg.setMinimumSize(420, 350)
        dlg.resize(min(pix.width() + 40, 900), min(pix.height() + 80, 700))
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(8)
        titulo = QLabel(f'Test Point ÔÇö {modelo}')
        titulo.setFont(QFont('Segoe UI', 13, QFont.Bold))
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet(f'color: {self._c('TEXT')};')
        lay.addWidget(titulo)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { border: none; }')
        lbl_img = QLabel()
        lbl_img.setAlignment(Qt.AlignCenter)
        max_w = min(pix.width(), 850)
        max_h = min(pix.height(), 600)
        scaled = pix.scaled(max_w, max_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        lbl_img.setPixmap(scaled)
        scroll.setWidget(lbl_img)
        lay.addWidget(scroll, stretch=1)
        btn_fechar = QPushButton('Fechar')
        btn_fechar.setFixedSize(100, 32)
        btn_fechar.setCursor(Qt.PointingHandCursor)
        btn_fechar.setFont(QFont('Segoe UI', 10))
        btn_fechar.setStyleSheet(f'\n            QPushButton {{ background-color: {self._c('BACKGROUND_DARK')};\n                color: {self._c('TEXT')}; border: 1px solid {self._c('BORDER')};\n                border-radius: 6px; }}\n            QPushButton:hover {{ background-color: {self._c('BORDER')}; }}\n        ')
        btn_fechar.clicked.connect(dlg.accept)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(btn_fechar)
        btn_row.addStretch()
        lay.addLayout(btn_row)
        dlg.setStyleSheet(f'QDialog {{ background-color: {self._c('BACKGROUND')}; }}')
        dlg.exec_()
    def _executar(self, chave):
        if self._em_exec:
            return
        ops = self._dados.get('operacoes', {})
        op = ops.get(chave)
        if not op:
            return
        try:
            from app.views.union_unlock.edl.firehose_ops import detectar_boxes_ativas
        except ImportError:
            from firehose_ops import detectar_boxes_ativas
        boxes = detectar_boxes_ativas()
        if boxes:
            lista = ', '.join(boxes)
            resp = QMessageBox.warning(self, 'Conflito de Porta', f'Programas que podem bloquear a porta EDL:\n\n  {lista}\n\nFeche-os para garantir o acesso ao dispositivo.\nDeseja tentar mesmo assim?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if resp == QMessageBox.No:
                return
        modelo = self._dados.get('modelo', '')
        if _MICLOUD_EDL_OK and _is_micloud_op(chave, op):
            self._executar_micloud_edl(chave)
            return
        requer_auth = self._dados.get('requer_auth')
        if self._auth_selector and self._auth_selector.is_forced():
            requer_auth = self._auth_selector.get_auth_type()
        if requer_auth:
            if _FRP_AUTH_OK and requer_auth in ('xiaomi',):
                _log(f'{modelo} requer auth ({requer_auth}) ÔÇö usando FRP Auth direto')
                self._executar_frp_auth(chave, requer_auth)
                return
            if _FRP_SAMSUNG_OK and requer_auth == 'samsung':
                _log(f'{modelo} requer auth ({requer_auth}) ÔÇö usando FRP Samsung direto')
                self._executar_frp_samsung(chave)
                return
            if _FRP_VIP2_OK and is_oppo_vip2(requer_auth):
                _log(f'{modelo} requer auth VIP2')
                self._executar_frp_vip2(chave)
                return
            if _FRP_VIP_OK and is_oppo_vip(requer_auth):
                _log(f'{modelo} requer auth ({requer_auth}) ÔÇö usando FRP VIP (patch)')
                self._executar_frp_vip(chave)
                return
            _log(f'{modelo} requer auth ({requer_auth}) ÔÇö redirecionando para Parti├º├Áes')
            reply = QMessageBox.information(self, 'Verificacao Adicional', f'O modelo {modelo} requer uma etapa adicional de verificacao.\n\nA operacao sera realizada pela aba "Particoes", onde voce podera:\n  ÔÇó Visualizar todas as particoes do dispositivo\n  ÔÇó Selecionar exatamente quais particoes apagar\n  ÔÇó Executar com seguranca total\n\nDeseja ir para a aba Particoes agora?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                self.redirecionar_particoes.emit({**self._dados, 'auth_type': requer_auth, 'loader_path': self._ldr_tmp or ''})
            return
        ferramenta = op.get('ferramenta', 'edl-ng')
        sequencia = op.get('sequencia', [])
        reset_apos = op.get('reset_apos', True)
        memoria = self._dados.get('memoria', 'emmc')
        _log(f'Iniciando {chave} para {modelo} | ferramenta={ferramenta} mem={memoria}')
        if _FRP_AUTH_OK and ferramenta == 'edl-ng':
            particoes_seq = []
            for s in sequencia:
                partes = s.split()
                if len(partes) >= 2:
                    particoes_seq.append(partes[-1])
            _log(f'{modelo} usando fh_loader patch (mais efetivo que edl-ng)')
            self._executar_frp_fhloader(chave, particoes_seq or ['frp'])
            return
        if ferramenta == 'frp_edl':
            exe = self._tool('FRP_EDL.exe')
        elif ferramenta == 'emmcdl':
            exe = self._tool('emmcdl.exe')
        else:
            exe = self._tool('edl-ng.exe')
        if not os.path.exists(exe):
            QMessageBox.critical(self, 'Erro', 'Componente nao encontrado!\n\nReinstale o programa ou entre em contato com o suporte.')
            return
        if not self._aguardar_dispositivo_edl():
            return
        self._em_exec = True
        for b in self._botoes.values():
            b.setEnabled(False)
        self.lbl_status.setText('Aguardando dispositivo...')
        self.lbl_status.setStyleSheet(f'color: {self._c('TEXT_MUTED')};')
        self.lbl_phone.setText('Conecte o celular em modo EDL')
        self.barra.setValue(5)
        self._set_phone_image('loading')
        self.spinner_anim.start()
        if ferramenta == 'frp_edl':
            worker = _FrpEdlWorker(exe, self._ldr_tmp, memoria)
        else:
            worker = _EdlNgWorker(exe, self._ldr_tmp, memoria, sequencia, reset_apos)
        worker.log_signal.connect((lambda msg: _log(msg)))
        worker.progress_signal.connect(self.barra.setValue)
        worker.status_signal.connect(self._on_status)
        worker.finished_signal.connect(self._on_finished)
        self._worker = worker
        worker.start()
    def _executar_frp_fhloader(self, chave: str, particoes: list):
        memoria = self._dados.get('memoria', 'emmc')
        if not self._aguardar_dispositivo_edl():
            return
        self._em_exec = True
        for b in self._botoes.values():
            b.setEnabled(False)
        self.lbl_status.setText('Conectando ao dispositivo...')
        self.lbl_status.setStyleSheet(f'color: {self._c('WARNING')};')
        self.lbl_phone.setText('Conecte o celular em modo EDL')
        self.barra.setValue(5)
        self._set_phone_image('loading')
        self.spinner_anim.start()
        _log(f'fh_loader patch: particoes={particoes}')
        worker = _FrpXiaomiAuthWorker(self._ldr_tmp, memoria, particoes, '')
        worker.log_signal.connect(self._on_frp_auth_log)
        worker.progress_signal.connect(self.barra.setValue)
        worker.status_signal.connect(self._on_status)
        worker.finished_signal.connect(self._on_frp_auth_finished)
        self._frp_auth_worker = worker
        self._worker = worker
        worker.start()
    def _executar_frp_auth(self, chave: str, auth_tipo: str):
        op = self._dados.get('operacoes', {}).get(chave, {})
        modelo = self._dados.get('modelo', '')
        memoria = self._dados.get('memoria', 'emmc')
        if not self._aguardar_dispositivo_edl():
            return
        particoes = ['frp']
        factory = QMessageBox.question(self, 'Apagar dados do usuario?', 'Deseja tambem realizar o Factory Reset?\n\nIsso apagara todos os dados do usuario (fotos, apps, contas).\nRecomendado quando o aparelho esta com conta Google.\n\nApagar USERDATA?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if factory == QMessageBox.Yes:
            particoes.append('userdata')
            _log('Usuario optou por apagar userdata (Factory Reset)')
        else:
            _log('Usuario optou por apagar somente FRP')
        self._em_exec = True
        self._frp_auth_worker = None
        for b in self._botoes.values():
            b.setEnabled(False)
        self.lbl_status.setText('Conectando ao dispositivo...')
        self.lbl_status.setStyleSheet(f'color: {self._c('WARNING')};')
        self.lbl_phone.setText('Conecte o celular em modo EDL')
        self.barra.setValue(5)
        self._set_phone_image('loading')
        self.spinner_anim.start()
        worker = _FrpXiaomiAuthWorker(self._ldr_tmp, memoria, particoes, auth_tipo)
        worker.log_signal.connect(self._on_frp_auth_log)
        worker.progress_signal.connect(self.barra.setValue)
        worker.status_signal.connect(self._on_status)
        worker.finished_signal.connect(self._on_frp_auth_finished)
        self._frp_auth_worker = worker
        self._worker = worker
        worker.start()
    def _on_frp_auth_log(self, msg: str):
        txt = msg.strip()
        if not txt or txt.startswith('=') or txt.startswith('-'):
            return
        _STATUS_KEYWORDS = ('Conectando', 'Porta EDL', 'Enviando programador', 'Autenticando', 'Configurando', 'Memoria', 'LUNs', 'Chip mem', 'Capacidade', 'Lendo mapa', 'Total:', 'Localizando', 'Encontrada', 'Apagando', 'apagada com sucesso', 'Reiniciando', 'FRP REMOVIDO', 'Tempo total')
        if any((kw in txt for kw in _STATUS_KEYWORDS)):
            self.lbl_status.setText(txt.lstrip())
            self.lbl_status.setStyleSheet(f'color: {self._c('WARNING')};')
            if 'Enviando programador' in txt:
                self.lbl_phone.setText('Enviando...')
                return
            if 'Autenticando' in txt:
                self.lbl_phone.setText('Autenticando...')
                return
            if 'Lendo mapa' in txt:
                self.lbl_phone.setText('Lendo particoes...')
                return
            if 'Apagando FRP' in txt:
                self.lbl_phone.setText('Apagando FRP...')
                return
            if 'Apagando USERDATA' in txt:
                self.lbl_phone.setText('Factory Reset...')
                return
            if 'Reiniciando' in txt:
                self.lbl_phone.setText('Reiniciando...')
    def _on_frp_auth_finished(self, ok: bool, msg: str, device_data: dict):
        self._em_exec = False
        self.spinner_anim.stop()
        for b in self._botoes.values():
            b.setEnabled(True)
        modelo = self._dados.get('modelo', '')
        if ok:
            _log(f'FRP_AUTH SUCESSO ÔÇö {modelo}')
            self._set_phone_image('success')
            self.barra.setValue(100)
            self.lbl_status.setText('FRP removido com sucesso!')
            self.lbl_status.setStyleSheet(f'color: {self._c('SUCCESS')};')
            self.lbl_phone.setText('Sucesso!')
            info_parts = []
            if device_data.get('mem_type'):
                label = device_data.get('storage_label', device_data['mem_type'])
                info_parts.append(f'Memoria: {label}')
            if device_data.get('capacidade_gb'):
                info_parts.append(f'Capacidade: ~{device_data['capacidade_gb']} GB')
            if device_data.get('particoes_apagadas'):
                info_parts.append('FRP removido')
            if device_data.get('tempo_total'):
                info_parts.append(f'Tempo: {device_data['tempo_total']}')
            info_text = '\n'.join(info_parts) if info_parts else ''
            QMessageBox.information(self, 'Sucesso', f'FRP removido com sucesso!\n\n{info_text}\n\nO aparelho vai reiniciar.\nConfigure normalmente.')
        else:
            _log(f'FRP_AUTH FALHA ÔÇö {modelo}: {msg}')
            self._set_phone_image('error')
            self.lbl_phone.setText('Falha no processo')
            self.barra.setValue(0)
            reply = QMessageBox.question(self, 'Falha na Operacao', 'A operacao de FRP falhou.\n\nDeseja tentar pela aba Particoes?\n(Permite selecionar particoes manualmente)', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                requer_auth = self._dados.get('requer_auth', 'xiaomi')
                self.redirecionar_particoes.emit({**self._dados, 'auth_type': requer_auth, 'loader_path': self._ldr_tmp or ''})
        self._limpar_tmp()
    def _executar_frp_samsung(self, chave: str):
        modelo = self._dados.get('modelo', '')
        memoria = self._dados.get('memoria', 'emmc')
        if not self._aguardar_dispositivo_edl():
            return
        particoes = ['persistent']
        self._em_exec = True
        for b in self._botoes.values():
            b.setEnabled(False)
        self.lbl_status.setText('Conectando ao dispositivo Samsung...')
        self.lbl_status.setStyleSheet(f'color: {self._c('WARNING')};')
        self.lbl_phone.setText('Conecte o celular em modo EDL')
        self.barra.setValue(5)
        self._set_phone_image('loading')
        self.spinner_anim.start()
        worker = _FrpSamsungWorker(self._ldr_tmp, memoria, particoes)
        worker.log_signal.connect(self._on_samsung_log)
        worker.progress_signal.connect(self.barra.setValue)
        worker.status_signal.connect(self._on_status)
        worker.finished_signal.connect(self._on_frp_auth_finished)
        self._worker = worker
        worker.start()
    def _on_samsung_log(self, msg: str):
        txt = msg.strip()
        if not txt or txt.startswith('=') or txt.startswith('-'):
            return
        lower = txt.lower()
        if 'enviando programador' in lower:
            self.lbl_status.setText('Carregando loader...')
            self.lbl_phone.setText('Enviando...')
        elif 'configurando' in lower:
            self.lbl_status.setText('Configurando dispositivo...')
            self.lbl_phone.setText('Configurando...')
        elif 'lendo mapa' in lower or 'particoes' in lower:
            self.lbl_status.setText('Lendo parti├º├Áes...')
            self.lbl_phone.setText('Lendo particoes...')
        elif 'zerando' in lower:
            self.lbl_status.setText('Removendo FRP...')
            self.lbl_phone.setText('Removendo FRP...')
        elif 'modo alternativo' in lower:
            self.lbl_status.setText('Removendo FRP (modo alternativo)...')
            self.lbl_phone.setText('Removendo FRP...')
        elif '% concluido' in lower:
            self.lbl_status.setText(f'Removendo FRP... {txt}')
        elif 'reiniciando' in lower:
            self.lbl_status.setText('Reiniciando dispositivo...')
            self.lbl_phone.setText('Reiniciando...')
        elif 'sucesso' in lower or 'removido' in lower:
            self.lbl_status.setText('FRP Samsung removido!')
            self.lbl_status.setStyleSheet(f'color: {self._c('SUCCESS')};')
            return
        self.lbl_status.setStyleSheet(f'color: {self._c('WARNING')};')
    def _carregar_vip_data(self, chipset: Optional[str]=None, vip_auth_id: Optional[int]=None):
        where = 'WHERE ativo=1'
        params_sqlite = ()
        params_mysql = ()
        if vip_auth_id is not None:
            where = 'WHERE id=?'
            params_sqlite = (vip_auth_id,)
            params_mysql = (vip_auth_id,)
        elif chipset:
            where += ' AND chipset=?'
            params_sqlite = (chipset,)
            params_mysql = (chipset,)
        query_sqlite = f'SELECT digest, sign_data FROM edl_auth_vip {where} LIMIT 1'
        query_mysql = query_sqlite.replace('?', '%s')
        try:
            import sqlite3
            _vip_db = None
            try:
                from app.utils.path_manager import PathManager
                tools = PathManager.get_unlock_tools_dir()
                if tools:
                    _candidate = os.path.normpath(os.path.join(os.path.dirname(tools), 'edl', 'edl_qcom.db'))
                    if os.path.isfile(_candidate):
                        _vip_db = _candidate
            except Exception:
                pass
            else:
                if not _vip_db:
                    _vip_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'edl_qcom.db')
                if os.path.exists(_vip_db):
                    conn = sqlite3.connect(_vip_db)
                    cur = conn.cursor()
        except Exception as e:
            _log(f'Cache VIP local nao disponivel: {e}')
        try:
            import pymysql
            from app.utils._app_cfg import db_config
            cfg = db_config(connect_timeout=10, read_timeout=15)
            conn = pymysql.connect(**cfg)
            cur = conn.cursor()
            cur.execute(query_mysql, params_mysql)
            row = cur.fetchone()
            conn.close()
            if row and row[0] and row[1]:
                _log(f'VIP data do MySQL ({len(row[0])}B + {len(row[1])}B){' chipset=' + chipset if chipset else ''}')
                return row[0], row[1]
        except Exception as e:
            _log(f'MySQL VIP nao disponivel: {e}')
        return (None, None)
    def _executar_frp_vip(self, chave: str):
        modelo = self._dados.get('modelo', '')
        memoria = self._dados.get('memoria', 'emmc')
        requer_auth = self._dados.get('requer_auth', '')
        _chipset = extrair_vip_chipset(requer_auth)
        _vip_id = self._dados.get('vip_auth_id')
        vip_digest, vip_sign = self._carregar_vip_data(chipset=_chipset, vip_auth_id=_vip_id)
        if not vip_digest or not vip_sign:
            QMessageBox.critical(self, 'Erro', 'Dados de autenticacao nao encontrados.\n\nVerifique o painel administrativo ou atualize o sistema.')
            return
        if not self._aguardar_dispositivo_edl():
            return
        op = self._dados.get('operacoes', {}).get(chave, {})
        particoes = []
        for s in op.get('sequencia', ['erase-part frp']):
            partes = s.split()
            if len(partes) >= 2:
                particoes.append(partes[-1])
        if not particoes:
            particoes = ['frp']
        self._em_exec = True
        for b in self._botoes.values():
            b.setEnabled(False)
        self.lbl_status.setText('Autenticando dispositivo...')
        self.lbl_status.setStyleSheet(f'color: {self._c('WARNING')};')
        self.lbl_phone.setText('Conecte o celular em modo EDL')
        self.barra.setValue(5)
        self._set_phone_image('loading')
        self.spinner_anim.start()
        worker = _FrpVipWorker(self._ldr_tmp, memoria, particoes, vip_digest, vip_sign)
        worker.log_signal.connect(self._on_vip_log)
        worker.progress_signal.connect(self.barra.setValue)
        worker.status_signal.connect(self._on_status)
        worker.finished_signal.connect(self._on_frp_auth_finished)
        self._worker = worker
        worker.start()
    def _executar_frp_vip2(self, chave: str):
        modelo = self._dados.get('modelo', '')
        memoria = self._dados.get('memoria', 'emmc')
        requer_auth = self._dados.get('requer_auth', '')
        _chipset = extrair_vip_chipset(requer_auth)
        _vip_id = self._dados.get('vip_auth_id')
        vip_digest, vip_sign = self._carregar_vip_data(chipset=_chipset, vip_auth_id=_vip_id)
        if not vip_digest or not vip_sign:
            QMessageBox.critical(self, 'Erro', 'Dados de autenticacao nao encontrados.\n\nVerifique o painel administrativo ou atualize o sistema.')
            return
        if not self._aguardar_dispositivo_edl():
            return
        try:
            from app.views.union_unlock.edl.config import QSAHARA
        except ImportError:
            from config import QSAHARA
        qsahara_path = str(QSAHARA)
        porta = self._scan_porta_edl()
        if not porta:
            self._limpar_tmp()
            QMessageBox.critical(self, 'Erro', 'Dispositivo desconectado durante a preparacao.\n\nReconecte em modo EDL e tente novamente.')
            return
        self._em_exec = True
        for b in self._botoes.values():
            b.setEnabled(False)
        self.lbl_status.setText('Autenticando dispositivo...')
        self.lbl_status.setStyleSheet(f'color: {self._c('WARNING')};')
        self.lbl_phone.setText('Conecte o celular em modo EDL')
        self.barra.setValue(5)
        self._set_phone_image('loading')
        self.spinner_anim.start()
        worker = _FrpVip2Worker(porta, self._ldr_tmp, qsahara_path, memoria, vip_digest, vip_sign)
        worker.log_signal.connect(self._on_vip_log)
        worker.progress_signal.connect(self.barra.setValue)
        worker.status_signal.connect(self._on_status)
        worker.finished_signal.connect(self._on_frp_auth_finished)
        self._worker = worker
        worker.start()
    def _on_vip_log(self, msg: str):
        txt = msg.strip()
        if not txt or txt.startswith('=') or txt.startswith('-'):
            return
        lower = txt.lower()
        if 'enviando programador' in lower:
            self.lbl_status.setText('Carregando loader...')
            self.lbl_phone.setText('Enviando...')
        elif 'autenticando vip' in lower:
            self.lbl_status.setText('Autenticando VIP...')
            self.lbl_phone.setText('Autenticando...')
        elif 'vip auth concluido' in lower:
            self.lbl_status.setText('VIP Auth OK!')
            self.lbl_phone.setText('Autenticado!')
        elif 'configurando' in lower:
            self.lbl_status.setText('Configurando dispositivo...')
            self.lbl_phone.setText('Configurando...')
        elif 'lendo mapa' in lower or 'particoes' in lower:
            self.lbl_status.setText('Lendo particoes...')
            self.lbl_phone.setText('Lendo particoes...')
        elif 'zerando' in lower:
            self.lbl_status.setText('Removendo FRP...')
            self.lbl_phone.setText('Removendo FRP...')
        elif 'reiniciando' in lower:
            self.lbl_status.setText('Reiniciando dispositivo...')
            self.lbl_phone.setText('Reiniciando...')
        elif 'sucesso' in lower or 'removido' in lower:
            self.lbl_status.setText('FRP removido com sucesso!')
            self.lbl_status.setStyleSheet(f'color: {self._c('SUCCESS')};')
            return
        self.lbl_status.setStyleSheet(f'color: {self._c('WARNING')};')
    def _executar_micloud_edl(self, chave: str):
        modelo = self._dados.get('modelo', '')
        memoria = self._dados.get('memoria', 'emmc')
        resp = QMessageBox.warning(self, 'Reset Mi Cloud', f'Voce vai remover o bloqueio Mi Cloud de {modelo}.\n\nUm backup de seguranca sera salvo na pasta Documentos.\n\nUse APENAS se o aparelho esta bloqueado por Mi Account.\nEm caso de duvida, NAO prossiga.\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resp != QMessageBox.Yes:
            return
        if not self._aguardar_dispositivo_edl():
            return
        self._em_exec = True
        for b in self._botoes.values():
            b.setEnabled(False)
        self.lbl_status.setText('Iniciando Mi Cloud reset...')
        self.lbl_status.setStyleSheet(f'color: {self._c('WARNING')};')
        self.lbl_phone.setText('Conecte o celular em modo EDL')
        self.barra.setValue(5)
        self._set_phone_image('loading')
        self.spinner_anim.start()
        worker = _MiCloudEdlWorker(self._ldr_tmp, memoria, 'xiaomi')
        worker.log_signal.connect(self._on_micloud_log)
        worker.progress_signal.connect(self.barra.setValue)
        worker.status_signal.connect(self._on_status)
        worker.finished_signal.connect(self._on_micloud_finished)
        self._worker = worker
        worker.start()
    def _on_micloud_log(self, msg: str):
        txt = msg.strip()
        if not txt or txt.startswith('=') or txt.startswith('-'):
            return
        lower = txt.lower()
        if 'conectando' in lower:
            self.lbl_status.setText('Conectando ao dispositivo...')
            self.lbl_phone.setText('Conectando...')
        elif 'enviando programador' in lower:
            self.lbl_status.setText('Carregando componentes...')
            self.lbl_phone.setText('Carregando...')
        elif 'verificando dispositivo' in lower:
            self.lbl_status.setText('Verificando dispositivo...')
            self.lbl_phone.setText('Verificando...')
        elif 'analisando' in lower:
            self.lbl_status.setText('Analisando dispositivo...')
            self.lbl_phone.setText('Analisando...')
        elif 'lendo informacoes' in lower:
            self.lbl_status.setText('Lendo informacoes do aparelho...')
            self.lbl_phone.setText('Analisando...')
        elif 'preparando' in lower:
            self.lbl_status.setText('Preparando dispositivo...')
            self.lbl_phone.setText('Preparando...')
        elif 'processando' in lower or 'minutos' in lower:
            self.lbl_status.setText('Processando... aguarde')
            self.lbl_phone.setText('Processando...')
        elif 'criando backup' in lower:
            self.lbl_status.setText('Criando backup de seguranca...')
            self.lbl_phone.setText('Backup...')
        elif 'finalizando' in lower:
            self.lbl_status.setText('Finalizando operacao...')
            self.lbl_phone.setText('Finalizando...')
        elif 'aplicando' in lower or 'nao desconecte' in lower:
            self.lbl_status.setText('Aplicando... NAO desconecte o cabo!')
            self.lbl_phone.setText('Aplicando...')
        elif 'reiniciando' in lower:
            self.lbl_status.setText('Reiniciando dispositivo...')
            self.lbl_phone.setText('Reiniciando...')
        else:
            if 'concluida com sucesso' in lower or 'removido com sucesso' in lower:
                self.lbl_status.setText('Operacao concluida com sucesso!')
                self.lbl_status.setStyleSheet(f'color: {self._c('SUCCESS')};')
                self.lbl_phone.setText('Sucesso!')
                return
            return
        self.lbl_status.setStyleSheet(f'color: {self._c('WARNING')};')
    def _on_micloud_finished(self, ok: bool, msg: str, device_data: dict):
        self._em_exec = False
        self.spinner_anim.stop()
        for b in self._botoes.values():
            b.setEnabled(True)
        modelo = self._dados.get('modelo', '')
        if ok:
            _log(f'MICLOUD_EDL SUCESSO ÔÇö {modelo}')
            self._set_phone_image('success')
            self.barra.setValue(100)
            self.lbl_status.setText('Mi Cloud removido com sucesso!')
            self.lbl_status.setStyleSheet(f'color: {self._c('SUCCESS')};')
            self.lbl_phone.setText('Sucesso! Ô£à')
            info_parts = []
            if device_data.get('backup_path'):
                info_parts.append('Backup salvo na pasta Documentos')
            if device_data.get('tempo_total'):
                info_parts.append(f'Tempo: {device_data['tempo_total']}s')
            info_text = '\n'.join(info_parts)
            QMessageBox.information(self, 'Sucesso', f'Mi Cloud removido com sucesso!\n\n{info_text}\n\nO aparelho vai reiniciar.\nConfigure normalmente.')
        else:
            _log(f'MICLOUD_EDL FALHA ÔÇö {modelo}: {msg}')
            self._set_phone_image('error')
            self.lbl_phone.setText('Falha no processo')
            self.barra.setValue(0)
            self.lbl_status.setText('Falha na operacao')
            self.lbl_status.setStyleSheet(f'color: {self._c('ERROR')};')
            safe_msg = 'Nao foi possivel concluir a operacao.\n\nReconecte o aparelho em modo EDL e tente novamente.\nSe o problema persistir, o modelo pode nao ser compativel.'
            if 'nao encontrad' in msg.lower():
                safe_msg = 'Nao foi possivel concluir a operacao.\n\nEste modelo pode nao ser compativel\ncom esta funcionalidade.'
            QMessageBox.critical(self, 'Falha', safe_msg)
        self._limpar_tmp()
    def _on_status(self, estado):
        if estado == 'waiting':
            self.lbl_status.setText('Aguardando dispositivo...')
            return
        if estado == 'connected':
            self._set_phone_image('loading')
            self.lbl_status.setText('Dispositivo conectado!')
            self.lbl_status.setStyleSheet(f'color: {self._c('PRIMARY')};')
            self.lbl_phone.setText('Conectando...')
            return
        if estado == 'processing':
            self.lbl_status.setText('Processando...')
            self.lbl_phone.setText('Removendo FRP...')
            return
        if estado == 'success':
            self.spinner_anim.stop()
            self._set_phone_image('success')
            self.lbl_status.setText('Finalizado com sucesso!')
            self.lbl_status.setStyleSheet(f'color: {self._c('SUCCESS')};')
            self.lbl_phone.setText('FRP removido! Ô£à')
            return
        if estado == 'error':
            self.spinner_anim.stop()
            self._set_phone_image('error')
            self.lbl_status.setText('Erro no processo')
            self.lbl_status.setStyleSheet(f'color: {self._c('ERROR')};')
    def _on_finished(self, sucesso, msg):
        self._em_exec = False
        self.spinner_anim.stop()
        self._limpar_tmp()
        for b in self._botoes.values():
            b.setEnabled(True)
        modelo = self._dados.get('modelo', '')
        if sucesso:
            _log(f'SUCESSO ÔÇö {modelo}')
            self._set_phone_image('success')
            self.barra.setValue(100)
            QMessageBox.information(self, 'Sucesso', msg)
            return
        _log(f'FALHA ÔÇö {modelo}: {msg}')
        self._set_phone_image('error')
        self.lbl_phone.setText('Falha no processo')
        self.barra.setValue(0)
        QMessageBox.critical(self, 'Erro', 'Opera├º├úo falhou.\n\nReconecte o dispositivo em modo EDL e tente novamente.\nSe o problema persistir, o dispositivo pode n├úo suportar esta opera├º├úo.')
    def _parar(self):
        try:
            if self._em_exec and self._worker and hasattr(self._worker, 'cancelar'):
                self._worker.cancelar()
            if hasattr(self, '_frp_auth_worker') and self._frp_auth_worker and hasattr(self._frp_auth_worker, 'cancelar'):
                self._frp_auth_worker.cancelar()
            _matar_processos_edl()
        finally:
            self.spinner_anim.stop()
            self._em_exec = False
            self._limpar_tmp()
            for b in self._botoes.values():
                b.setEnabled(True)
        self._set_phone_image('notfound')
        self.barra.setValue(0)
        self.lbl_status.setText('Processo interrompido')
        self.lbl_status.setStyleSheet(f'color: {self._c('WARNING')};')
        self.lbl_phone.setText('')
    def _limpar_tmp(self):
        if self._ldr_tmp and os.path.exists(self._ldr_tmp):
            try:
                os.remove(self._ldr_tmp)
            except Exception:
                pass
        self._ldr_tmp = None
# WARNING: Decompyle incomplete
