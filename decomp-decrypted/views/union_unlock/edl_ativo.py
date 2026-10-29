import logging
import os
import sys
import subprocess
import tempfile
from typing import Dict
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QFrame, QMessageBox, QDialog, QScrollArea)
from PyQt5.QtCore import (QThread, pyqtSignal, Qt, QVariantAnimation)
from PyQt5.QtGui import (QFont, QPixmap, QTransform)
_logger = logging.getLogger(__name__)
def _log(msg: str):
    _logger.debug(msg)
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
def _secure_tmpfile(suffix: str='.bin') -> tuple:
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
def _base_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))
def _img_path(filename: str) -> str:
    return os.path.join(_base_dir(), 'img', filename)
def _tool_path(filename: str) -> str:
    try:
        from app.utils.path_manager import PathManager
        p = PathManager.get_unlock_tool(filename)
        if p and os.path.isfile(p):
            return p
    except Exception:
        pass
    return os.path.join(_base_dir(), 'tools', filename)
_PALETA = {'samsung': {'PRIMARY': '#1428A0', 'PRIMARY_HOVER': '#0D1B69', 'SUCCESS': '#27ae60', 'ERROR': '#e74c3c', 'WARNING': '#f39c12', 'TEXT': '#2c3e50', 'TEXT_MUTED': '#7f8c8d', 'TEXT_WHITE': '#ffffff', 'BORDER': '#bdc3c7', 'BACKGROUND': '#f5f5f5', 'BACKGROUND_DARK': '#e8e8e8', 'BACKGROUND_WHITE': '#ffffff'}, 'xiaomi': {'PRIMARY': '#ff6700', 'PRIMARY_HOVER': '#e55d00', 'SUCCESS': '#27ae60', 'ERROR': '#e74c3c', 'WARNING': '#f39c12', 'TEXT': '#2c3e50', 'TEXT_MUTED': '#7f8c8d', 'TEXT_WHITE': '#ffffff', 'BORDER': '#bdc3c7', 'BACKGROUND': '#f5f5f5', 'BACKGROUND_DARK': '#e8e8e8', 'BACKGROUND_WHITE': '#ffffff'}}
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
                self.status_signal.emit('error')
                self.finished_signal.emit(False, motivo or 'Falha na opera├º├úo')
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
                self.finished_signal.emit(False, 'Execute como Administrador!\n\nClique com bot├úo direito no programa\ne selecione "Executar como administrador"')
        except Exception:
            self.status_signal.emit('error')
            self.finished_signal.emit(False, 'Erro inesperado.\n\nEntre em contato com o suporte.')
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
            self.log_signal.emit(f'\n{'============================================================'}')
            self.log_signal.emit('  Executando remo├º├úo de FRP...')
            self.log_signal.emit(f'{'============================================================'}')
            cmd = [self._exe, '-m', self._mem, '-l', self._ldr, 'resetfrp']
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=os.path.dirname(self._exe), creationflags=flags)
            conectou = False
            erro = None
            for line in iter(proc.stdout.readline, ''):
                if self._stop:
                    proc.terminate()
                    self.finished_signal.emit(False, 'Cancelado')
                    return
                linha = line.rstrip()
                self.log_signal.emit(linha)
                ll = linha.lower()
                if 'automatic port detection failed' in ll:
                    erro = 'no_device'
                elif 'failed to send loader' in ll:
                    erro = 'loader_failed'
                if not conectou:
                    for kw in ('sahara', 'firehose', 'connected', 'sending loader', 'auto-detected port', 'device detected'):
                        if not kw in ll:
                            continue
                        conectou = True
                        self.status_signal.emit('connected')
                        self.progress_signal.emit(50)
                        break
                if 'rebooting' not in ll:
                    if 'done' not in ll:
                        continue
                    if 'frp' not in ll:
                        continue
                self.progress_signal.emit(90)
                continue
            proc.wait()
            if erro == 'no_device':
                self.status_signal.emit('error')
                self.finished_signal.emit(False, 'Dispositivo n├úo detectado!\n\nConecte o aparelho em modo EDL antes de iniciar.')
                return
            if erro == 'loader_failed':
                self.status_signal.emit('error')
                self.finished_signal.emit(False, 'Falha ao enviar loader.\n\nReconecte o dispositivo em modo EDL.')
                return
            if not conectou:
                self.status_signal.emit('error')
                self.finished_signal.emit(False, 'Dispositivo n├úo conectado!\n\nEntre em modo EDL antes de iniciar.')
                return
            self.progress_signal.emit(100)
            self.status_signal.emit('success')
            self.finished_signal.emit(True, 'FRP removido com sucesso!\n\nO aparelho ir├í reiniciar.')
            return
        except OSError as e:
            self.status_signal.emit('error')
            if hasattr(e, 'winerror') and e.winerror == 740:
                self.finished_signal.emit(False, 'Execute como Administrador!')
        except Exception:
            self.status_signal.emit('error')
            self.finished_signal.emit(False, 'Erro inesperado.\n\nEntre em contato com o suporte.')
class _FrpSamsungWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    def __init__(self, loader_path: str, memoria: str, particoes=None):
        super().__init__()
        self._loader = loader_path
        self._mem = memoria
        self._particoes = particoes or ['persistent']
        self._cancelado = False
    def cancelar(self):
        self._cancelado = True
        if sys.platform == 'win32':
            for exe in ('QSaharaServer.exe', 'fh_loader.exe'):
                try:
                    subprocess.run(['taskkill', '/F', '/IM', exe], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                except Exception:
                    continue
    def run(self):
        try:
            from app.views.union_unlock.edl.frp_samsung import executar_frp_samsung
            self.status_signal.emit('connected')
            ok, msg, _data = executar_frp_samsung(loader_path=self._loader, memoria=self._mem, particoes_alvo=self._particoes, log_cb=self._emit_log, progress_cb=self.progress_signal.emit)
            if self._cancelado:
                self.status_signal.emit('error')
                self.finished_signal.emit(False, 'Cancelado pelo usu├írio.')
                return
            self.status_signal.emit('success' if ok else 'error')
            self.finished_signal.emit(ok, 'FRP removido com sucesso!\n\nO aparelho ir├í reiniciar.' if ok else msg)
            return
        except Exception:
            self.status_signal.emit('error')
            self.finished_signal.emit(False, 'Erro inesperado.\n\nReconecte o dispositivo e tente novamente.')
    def _emit_log(self, msg: str):
        self.log_signal.emit(msg)
class EdlAtivoWidget(QWidget):
    redirecionar_qcom = pyqtSignal(dict)
    def __init__(self, dados: Dict, marca: str, parent=None):
        super().__init__(parent)
        self._dados = dados
        self._marca = marca.lower()
        self._worker = None
        self._em_exec = False
        self._ldr_tmp = None
        self.setup_ui()
        self._init_animation()
    def _c(self, chave: str) -> str:
        return _cor(self._marca, chave)
    def setup_ui(self):
        dados = self._dados
        ops = dados.get('operacoes', {})
        self.setStyleSheet(f'background-color: {self._c('BACKGROUND')};')
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(50)
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.setSpacing(8)
        ll.setAlignment(Qt.AlignTop)
        lbl_modelo = QLabel(dados.get('modelo', ''))
        lbl_modelo.setFont(QFont('Segoe UI', 24, QFont.Bold))
        lbl_modelo.setStyleSheet(f'color: {self._c('TEXT')};')
        lbl_modelo.setWordWrap(True)
        ll.addWidget(lbl_modelo)
        ll.addSpacing(60)
        lbl_suporte = QLabel('Suporte: Qualcomm EDL')
        lbl_suporte.setFont(QFont('Segoe UI', 13))
        lbl_suporte.setStyleSheet(f'color: {self._c('TEXT_MUTED')};')
        ll.addWidget(lbl_suporte)
        lbl_modo = QLabel('Modo: EDL (Qualcomm)')
        lbl_modo.setFont(QFont('Segoe UI', 11))
        lbl_modo.setStyleSheet(f'color: {self._c('PRIMARY')};')
        ll.addWidget(lbl_modo)
        ll.addSpacing(25)
        self._botoes = {}
        for chave, op in ops.items():
            label = op.get('label', chave.title())
            btn = QPushButton(label)
            btn.setFixedSize(150, 40)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFont(QFont('Segoe UI', 12, QFont.Bold))
            btn.setStyleSheet(f'\n                QPushButton {{ background-color: {self._c('PRIMARY')}; color: {self._c('TEXT_WHITE')};\n                    border: none; border-radius: 20px; }}\n                QPushButton:hover {{ background-color: {self._c('PRIMARY_HOVER')}; }}\n                QPushButton:disabled {{ background-color: {self._c('BORDER')}; }}\n            ')
            btn.clicked.connect((lambda checked, k=chave: self._executar(k)))
            ll.addWidget(btn)
            self._botoes[chave] = btn
            continue
        ll.addSpacing(10)
        self.btn_parar = QPushButton('Parar')
        self.btn_parar.setFixedSize(100, 35)
        self.btn_parar.setCursor(Qt.PointingHandCursor)
        self.btn_parar.setFont(QFont('Segoe UI', 11))
        self.btn_parar.setStyleSheet(f'\n            QPushButton {{ background-color: {self._c('BACKGROUND_DARK')}; color: {self._c('TEXT')};\n                border: 1px solid {self._c('BORDER')}; border-radius: 17px; }}\n            QPushButton:hover {{ background-color: {self._c('BORDER')}; }}\n        ')
        self.btn_parar.clicked.connect(self._parar)
        ll.addWidget(self.btn_parar)
        self.barra = QProgressBar()
        self.barra.setFixedSize(250, 18)
        self.barra.setValue(0)
        self.barra.setTextVisible(False)
        self.barra.setStyleSheet(f'\n            QProgressBar {{ border: 1px solid {self._c('BORDER')}; border-radius: 9px;\n                background-color: {self._c('BACKGROUND_WHITE')}; }}\n            QProgressBar::chunk {{ background-color: {self._c('PRIMARY')}; border-radius: 8px; }}\n        ')
        ll.addWidget(self.barra)
        self.btn_tp = QPushButton('­ƒôì Test Point')
        self.btn_tp.setFixedSize(130, 30)
        self.btn_tp.setCursor(Qt.PointingHandCursor)
        self.btn_tp.setFont(QFont('Segoe UI', 10, QFont.Bold))
        self.btn_tp.setStyleSheet(f'\n            QPushButton {{ background-color: {self._c('WARNING')};\n                color: #ffffff; border: none; border-radius: 15px; }}\n            QPushButton:hover {{ background-color: #d35400; }}\n        ')
        self.btn_tp.clicked.connect(self._mostrar_testpoint)
        self.btn_tp.setVisible(bool(dados.get('tem_testpoint')))
        ll.addWidget(self.btn_tp)
        ll.addStretch()
        self.lbl_aviso = QLabel('ÔÜá´©Å IMPORTANTE: Conecte o aparelho em modo EDL\n   ANTES de clicar em Remover FRP!\n­ƒöº Driver: Qualcomm Serial')
        self.lbl_aviso.setFont(QFont('Segoe UI', 9))
        self.lbl_aviso.setStyleSheet(f'color: {self._c('PRIMARY')}; padding: 5px;')
        self.lbl_aviso.setWordWrap(True)
        ll.addWidget(self.lbl_aviso)
        ll.addSpacing(4)
        if self._marca == 'samsung':
            nota = 'Ô£à Sucesso: Fa├ºa hard reset (Vol+ e Power) para concluir.\nÔØî Falha: Bin├írio incompat├¡vel. Verifique a vers├úo\n    do firmware antes de tentar novamente.'
        else:
            nota = 'Ô£à Sucesso: Fa├ºa hard reset (Vol+ e Power) para concluir.\nÔØî Falha: Verifique se o modelo exige autentica├º├úo\n    (auth) ou se a vers├úo de seguran├ºa n├úo ├® suportada.'
        lbl_nota = QLabel(nota)
        lbl_nota.setFont(QFont('Segoe UI', 8))
        lbl_nota.setStyleSheet(f'color: {self._c('TEXT_MUTED')}; padding: 2px 5px;')
        lbl_nota.setWordWrap(True)
        ll.addWidget(lbl_nota)
        ll.addSpacing(6)
        self.lbl_status = QLabel('Pronto para iniciar')
        self.lbl_status.setFont(QFont('Segoe UI', 12))
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
        rl.addWidget(self.lbl_phone)
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
        path = _img_path(images.get(status, 'phone_notfound.png'))
        if os.path.exists(path):
            pix = QPixmap(path).scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.phone_image.setPixmap(pix)
            if status == 'loading':
                self.original_pixmap = pix
                return
            return
        self.phone_image.setText('­ƒô▒')
        self.phone_image.setStyleSheet(f'font-size:50px;color:{self._c('TEXT')};')
    def _rotate_phone(self, angle):
        if self.original_pixmap:
            rot = self.original_pixmap.transformed(QTransform().rotate(angle), Qt.SmoothTransformation)
            dx = (rot.width() - self.original_pixmap.width()) // 2
            dy = (rot.height() - self.original_pixmap.height()) // 2
            self.phone_image.setPixmap(rot.copy(dx, dy, self.original_pixmap.width(), self.original_pixmap.height()))
    def _mostrar_testpoint(self):
        try:
            from app.views.union_unlock.edl.edl_sync import get_sync
            img_bytes = get_sync().download_testpoint(self._dados['srv_id'])
        except Exception:
            img_bytes = None
        if not img_bytes:
            QMessageBox.information(self, 'Test Point', 'Imagem de Test Point n├úo dispon├¡vel para este modelo.')
            return
        pix = QPixmap()
        if not pix.loadFromData(img_bytes):
            QMessageBox.warning(self, 'Test Point', 'N├úo foi poss├¡vel carregar a imagem.')
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(f'Test Point ÔÇö {self._dados.get('modelo', '')}')
        dlg.resize(640, 520)
        lay = QVBoxLayout(dlg)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        lbl_img = QLabel()
        lbl_img.setPixmap(pix)
        lbl_img.setAlignment(Qt.AlignCenter)
        scroll.setWidget(lbl_img)
        lay.addWidget(scroll, stretch=1)
        btn_fechar = QPushButton('Fechar')
        btn_fechar.setFixedSize(100, 32)
        btn_fechar.setCursor(Qt.PointingHandCursor)
        btn_fechar.clicked.connect(dlg.close)
        lay.addWidget(btn_fechar, alignment=Qt.AlignCenter)
        dlg.exec_()
    def _executar(self, chave):
        if self._em_exec:
            return
        ops = self._dados.get('operacoes', {})
        op = ops.get(chave)
        if not op:
            return
        modelo = self._dados.get('modelo', '')
        requer_auth = self._dados.get('requer_auth')
        ferramenta = op.get('ferramenta', 'edl-ng')
        sequencia = op.get('sequencia', [])
        reset_apos = op.get('reset_apos', True)
        memoria = self._dados.get('memoria', 'emmc')
        mem_label = 'eMMC' if memoria == 'emmc' else 'UFS'
        is_samsung = requer_auth == 'samsung'
        if requer_auth and not is_samsung and ferramenta == 'edl-ng':
            _log(f'{modelo} requer auth ({requer_auth}) ÔÇö redirecionando para QCOM EDL')
            reply = QMessageBox.information(self, 'Verificacao Adicional', f'O modelo {modelo} requer uma etapa adicional.\n\nA operacao sera realizada pelo modulo QCOM EDL,\nque suporta autenticacao e gerenciamento de particoes.\n\nDeseja ir para o modulo QCOM EDL agora?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                self._navegar_para_qcom_edl(requer_auth)
            return
        _log(f'Iniciando {op.get('label', chave.upper())} ÔÇö {modelo}')
        if not is_samsung:
            if ferramenta == 'frp_edl':
                exe = _tool_path('FRP_EDL.exe')
            elif ferramenta == 'emmcdl':
                exe = _tool_path('emmcdl.exe')
            else:
                exe = _tool_path('edl-ng.exe')
            if not os.path.exists(exe):
                _log('Componente nao encontrado')
                QMessageBox.critical(self, 'Erro', 'Componente n├úo encontrado!\n\nReinstale o programa ou entre em contato com o suporte.')
                return
        from app.views.union_unlock.edl.edl_sync import get_sync
        loader_bytes = get_sync().download_loader(self._dados['srv_id'])
        if not loader_bytes:
            _log('Loader nao disponivel')
            QMessageBox.critical(self, 'Erro', 'Loader n├úo dispon├¡vel.\n\nAtualize o sistema ou verifique sua conex├úo.')
            return
        _log(f'Loader pronto: {len(loader_bytes)} bytes')
        try:
            ext = _detectar_formato_loader(loader_bytes)
            fd, tmp = _secure_tmpfile(suffix=f'.{ext}')
            with os.fdopen(fd, 'wb') as f:
                f.write(loader_bytes)
            self._ldr_tmp = tmp
        except Exception:
            try:
                if 'tmp' in locals() and os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass
            QMessageBox.critical(self, 'Erro', 'Erro ao preparar componente.\n\nEntre em contato com o suporte.')
            return
        label = op.get('label', chave.title())
        reply = QMessageBox.question(self, 'Confirmar', f'Iniciar {label} para {modelo}?\n\n­ƒô▒ COMO ENTRAR EM MODO EDL:\n\n­ƒöº Test Point (recomendado):\n   ÔÇó Abra o aparelho e localize o ponto EDL\n   ÔÇó Fa├ºa curto no Test Point e conecte o cabo USB\n\n­ƒöî Cabo ou Adaptador EDL:\n   ÔÇó Conecte ao aparelho desligado\n\nEm alguns modelos, combina├º├Áes de bot├Áes\npodem ativar o modo EDL.\n\nO aparelho est├í em modo EDL?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            self._limpar_tmp()
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
        if is_samsung:
            worker = _FrpSamsungWorker(self._ldr_tmp, memoria)
            worker.log_signal.connect(self._on_samsung_log)
        elif ferramenta == 'frp_edl':
            worker = _FrpEdlWorker(exe, self._ldr_tmp, memoria)
            worker.log_signal.connect(self._on_log)
        else:
            worker = _EdlNgWorker(exe, self._ldr_tmp, memoria, sequencia, reset_apos)
            worker.log_signal.connect(self._on_log)
        worker.progress_signal.connect(self.barra.setValue)
        worker.status_signal.connect(self._on_status)
        worker.finished_signal.connect(self._on_finished)
        self._worker = worker
        worker.start()
    def _on_log(self, linha):
        _log(linha)
    def _on_samsung_log(self, msg: str):
        txt = msg.strip()
        if not txt or txt.startswith('=') or txt.startswith('-'):
            return
        lower = txt.lower()
        if 'enviando programador' in lower or 'carregando' in lower:
            self.lbl_status.setText('Carregando loader...')
            self.lbl_phone.setText('Enviando...')
        elif 'configurando' in lower or 'memoria' in lower:
            self.lbl_status.setText('Configurando dispositivo...')
            self.lbl_phone.setText('Configurando...')
        elif 'lendo mapa' in lower or 'particoes' in lower:
            self.lbl_status.setText('Lendo parti├º├Áes...')
            self.lbl_phone.setText('Lendo parti├º├Áes...')
        elif 'zerando' in lower or 'program' in lower:
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
            self.lbl_status.setText('FRP removido!')
            self.lbl_status.setStyleSheet(f'color: {self._c('SUCCESS')};')
            return
        self.lbl_status.setStyleSheet(f'color: {self._c('WARNING')};')
    def _on_status(self, estado):
        if estado == 'waiting':
            _log('Aguardando dispositivo em modo EDL...')
            self.lbl_status.setText('Aguardando dispositivo...')
            return
        if estado == 'connected':
            _log('Dispositivo conectado!')
            self._set_phone_image('loading')
            self.lbl_status.setText('Dispositivo conectado!')
            self.lbl_status.setStyleSheet(f'color: {self._c('PRIMARY')};')
            self.lbl_phone.setText('Conectando...')
            return
        if estado == 'processing':
            _log('Processando operacao...')
            self.lbl_status.setText('Processando...')
            self.lbl_phone.setText('Removendo FRP...')
            return
        if estado == 'success':
            _log('============================================================')
            _log('  OPERACAO CONCLUIDA COM SUCESSO!')
            _log('============================================================')
            self.spinner_anim.stop()
            self._set_phone_image('success')
            self.lbl_status.setText('Finalizado com sucesso!')
            self.lbl_status.setStyleSheet(f'color: {self._c('SUCCESS')};')
            self.lbl_phone.setText('FRP removido! Ô£à')
            return
        if estado == 'error':
            _log('ERRO na operacao')
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
        _log(f'FALHA ÔÇö {modelo}')
        self._set_phone_image('error')
        self.lbl_phone.setText('Falha no processo')
        self.barra.setValue(0)
        QMessageBox.critical(self, 'Erro', msg)
    def _parar(self):
        if self._em_exec and self._worker:
            self._worker.cancelar()
        if sys.platform == 'win32':
            for exe_name in ('edl-ng.exe', 'FRP_EDL.exe', 'emmcdl.exe', 'QSaharaServer.exe', 'fh_loader.exe'):
                try:
                    subprocess.run(['taskkill', '/F', '/IM', exe_name], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                except Exception:
                    continue
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
    def _navegar_para_qcom_edl(self, auth_type: str):
        w = self.window()
        tab_widget = getattr(w, 'tab_widget', None)
        edl_widget = getattr(w, '_edl_qcom_widget', None)
        if tab_widget and edl_widget:
            idx = tab_widget.indexOf(edl_widget)
            if idx >= 0:
                tab_widget.setCurrentIndex(idx)
                edl_widget.pre_configurar_auth(auth_type)
                _log(f'Navegou para aba QCOM EDL (auth={auth_type})')
                return
        parent_dlg = self.window()
        if hasattr(parent_dlg, 'close'):
            parent_dlg.close()
        _log('QCOM EDL nao encontrado na janela principal ÔÇö feche este dialog e use a aba QCOM EDL')
    def _limpar_tmp(self):
        if self._ldr_tmp and os.path.exists(self._ldr_tmp):
            try:
                os.remove(self._ldr_tmp)
            except Exception:
                pass
        self._ldr_tmp = None
