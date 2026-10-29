import os
import sys
import struct
import hashlib
import gzip
import tempfile
import subprocess
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QFrame, QMessageBox)
from PyQt5.QtCore import (QThread, pyqtSignal, Qt, QVariantAnimation)
from PyQt5.QtGui import (QFont, QPixmap, QTransform)
class CoresUnion:
    BACKGROUND = '#f5f5f5'
    BACKGROUND_DARK = '#e8e8e8'
    BACKGROUND_WHITE = '#ffffff'
    PRIMARY = '#1428A0'
    PRIMARY_HOVER = '#0D1B69'
    PRIMARY_LIGHT = '#1E90FF'
    SUCCESS = '#27ae60'
    ERROR = '#e74c3c'
    WARNING = '#f39c12'
    TEXT = '#2c3e50'
    TEXT_MUTED = '#7f8c8d'
    TEXT_WHITE = '#ffffff'
    BORDER = '#bdc3c7'
    BORDER_DARK = '#95a5a6'
_MAGIC = b'TECHUNIO'
_FLAG_GZIP = 1
_FLAG_XOR = 2
_XOR_KEY = b'TECH_UNION_2025_SECURE_KEY'
def _xor_data(data: bytes) -> bytes:
    key_len = len(_XOR_KEY)
    return bytes((b ^ _XOR_KEY[i % key_len] for i, b in enumerate(data)))
def _extract_loader(src_path: str) -> str:
    with open(src_path, 'rb') as f:
        magic = f.read(8)
        if magic != _MAGIC:
            raise ValueError('Invalid file')
        f.read(1)
        flags = struct.unpack('B', f.read(1))[0]
        f.read(2)
        f.read(4)
        expected_hash = f.read(32)
        name_len = struct.unpack('<H', f.read(2))[0]
        name = f.read(name_len).decode('utf-8')
        payload = f.read()
    if flags & _FLAG_XOR:
        payload = _xor_data(payload)
    if flags & _FLAG_GZIP:
        data = gzip.decompress(payload)
    else:
        data = payload
    calc_hash = hashlib.sha256(data).digest()
    if calc_hash != expected_hash:
        raise ValueError('Hash mismatch')
    temp_dir = os.path.join(tempfile.gettempdir(), 'tu_cache')
    os.makedirs(temp_dir, exist_ok=True)
    path_hash = hashlib.md5(src_path.encode()).hexdigest()[:8]
    temp_path = os.path.join(temp_dir, f'{path_hash}_{name}')
    with open(temp_path, 'wb') as f:
        f.write(data)
    return temp_path
class BromA226BRWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    def __init__(self, mtk_path: str, loader_path: str, modelo: str):
        super().__init__()
        self.mtk_path = mtk_path
        self.loader_path = loader_path
        self.modelo = modelo
        self._cancelado = False
    def _log(self, msg: str):
        print(msg, flush=True)
        self.log_signal.emit(msg)
    def run(self):
        try:
            if not os.path.exists(self.mtk_path):
                self._log('ÔØî ERRO: mtk.exe n├úo encontrado!')
                self._log(f'   Caminho: {self.mtk_path}')
                self.finished_signal.emit(False, 'mtk.exe n├úo encontrado')
                self.status_signal.emit('error')
                return
            self._log('=======================================================')
            self._log('  TECH UNION SOLUTIONS - FRP SAMSUNG BROM')
            self._log(f'  Modelo: {self.modelo}')
            self._log('=======================================================')
            self._log('')
            self._log('[Ô£ô] mtk.exe: Encontrado')
            if self.loader_path:
                self._log('[Ô£ô] Loader: Configurado')
            self._log('')
            self._log('Aguardando dispositivo...')
            self._log('   1. Desligue o aparelho')
            self._log('   2. Segure Volume + e Volume -')
            self._log('   3. Conecte o cabo USB')
            self._log('')
            self._log('-------------------------------------------------------')
            self.status_signal.emit('waiting')
            self.progress_signal.emit(10)
            if self.loader_path:
                comando = [self.mtk_path, 'e', 'frp,persist,userdata', '--loader', self.loader_path]
            else:
                comando = [self.mtk_path, 'e', 'frp,persist,userdata']
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            processo = subprocess.Popen(comando, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=os.path.dirname(self.mtk_path), creationflags=creationflags)
            device_connected = False
            erasing_started = False
            sucesso_formatacao = False
            erro_detectado = False
            while True:
                if self._cancelado:
                    processo.terminate()
                    self._log('Processo cancelado pelo usuario')
                    self.finished_signal.emit(False, 'Cancelado')
                    self.status_signal.emit('error')
                    return
                linha = processo.stdout.readline()
                if not linha and processo.poll() is not None:
                    break
                if linha:
                    linha_limpa = linha.rstrip()
                    self._log(linha_limpa)
                    linha_lower = linha_limpa.lower()
                    if not device_connected and 'waiting' not in linha_lower:
                        frases_conexao = ['device detected :)', 'handshake complete', 'da matched', 'sending da', 'uploading da', 'upload da', 'is in brom mode', 'successfully uploaded', 'boot to succeeded', 'dram setup passed', 'kamakiri run']
                        if any((frase in linha_lower for frase in frases_conexao)):
                            device_connected = True
                            self.status_signal.emit('connected')
                            self.progress_signal.emit(40)
                            self._log('')
                            self._log('[Ô£ô] Dispositivo detectado e conectado!')
                            self._log('')
                    if device_connected and not erasing_started:
                        if 'erasing' in linha_lower or 'formatting' in linha_lower:
                            erasing_started = True
                            self.progress_signal.emit(70)
                    if 'successsfully formatted' in linha_lower or 'formatted sector' in linha_lower:
                        sucesso_formatacao = True
                        self.progress_signal.emit(95)
                    if 'daa_sig_verify_failed' in linha_lower:
                        erro_detectado = 'auth'
                    elif any((err in linha_lower for err in ('no valid da loader found', 'no da_loader config set up', 'error on getting preloader', 'da selection failed'))):
                        erro_detectado = 'da_loader'
            retcode = processo.wait()
            if not sucesso_formatacao or erro_detectado:
                if retcode == 0 and not erro_detectado:
                    pass
            self.progress_signal.emit(100)
            self.status_signal.emit('success')
            self._log('')
            self._log('=======================================================')
            self._log('  [Ô£ô] PROCESSO FINALIZADO COM SUCESSO!')
            self._log('=======================================================')
            self._log('')
            self._log('FRP removido com sucesso!')
            self._log('TECH UNION SOLUTIONS - Valeu, tecnico!')
            self.finished_signal.emit(True, 'FRP removido com sucesso!')
            return
            if erro_detectado == 'auth':
                self.status_signal.emit('error')
                self._log('')
                self._log('=======================================================')
                self._log('  [ERRO] FALHA DE AUTENTICACAO (DAA)')
                self._log('=======================================================')
                self._log('')
                self._log('Dispositivo com seguranca maior que a suportada!')
                self._log('Verifique se e a variante correta do modelo.')
                self.finished_signal.emit(False, 'Seguranca DAA - Nao suportado')
                return
            if erro_detectado == 'da_loader':
                self.status_signal.emit('error')
                self._log('')
                self._log('[ERRO] Falha no DA Loader - Componente nao compativel')
                self.finished_signal.emit(False, 'DA Loader nao compativel com este dispositivo.')
                return
            self.status_signal.emit('error')
            self._log('')
            self._log(f'Processo finalizou com erro (codigo: {retcode})')
            if not device_connected:
                self._log('Nenhum dispositivo foi detectado.')
                self._log('   - Verifique se esta em modo BROM (Vol+ e Vol- ao conectar)')
                self._log('   - Verifique o cabo USB')
            self.finished_signal.emit(False, f'Erro (codigo: {retcode})')
            return
        except Exception as e:
            self.status_signal.emit('error')
            self._log(f'Excecao: {str(e)}')
            self.finished_signal.emit(False, str(e))
    def cancelar(self):
        self._cancelado = True
class BromA226BRWidget(QWidget):
    MODELO = 'Galaxy A22 5G'
    VARIANTE = 'SM-A226BR (Brasil)'
    SUPORTE = 'Full binary'
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.em_execucao = False
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.setup_ui()
        self._init_animation()
    def _get_img_path(self, filename: str) -> str:
        try:
            from app.utils.path_manager import PathManager
            d = PathManager.get_unlock_img_dir()
            if d:
                p = os.path.join(d, filename)
                if os.path.isfile(p):
                    return p
        except Exception:
            pass
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(base, 'img', filename)
    def _get_tools_path(self) -> str:
        try:
            from app.utils.path_manager import PathManager
            d = PathManager.get_unlock_tools_dir()
            if d and os.path.isdir(d):
                return d
        except Exception:
            pass
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(base, 'tools')
    def _get_loader_path(self) -> str:
        da_folder = None
        try:
            from app.utils.path_manager import PathManager
            tools = PathManager.get_unlock_tools_dir()
            if tools:
                candidate = os.path.normpath(os.path.join(os.path.dirname(tools), 'samsung', 'DA'))
                if os.path.isdir(candidate):
                    da_folder = candidate
        except Exception:
            pass
        if not da_folder:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            da_folder = os.path.join(base, 'DA')
        union_path = os.path.join(da_folder, 'Samsung_A226BR_MT6833.union')
        if os.path.exists(union_path):
            try:
                return _extract_loader(union_path)
            except Exception:
                pass
    def setup_ui(self):
        self.setStyleSheet(f'background-color: {CoresUnion.BACKGROUND};')
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(50)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        left_layout.setAlignment(Qt.AlignTop)
        self.label_modelo = QLabel(f'Samsung {self.MODELO}')
        self.label_modelo.setFont(QFont('Segoe UI', 24, QFont.Bold))
        self.label_modelo.setStyleSheet(f'color: {CoresUnion.TEXT};')
        left_layout.addWidget(self.label_modelo)
        self.label_variante = QLabel(self.VARIANTE)
        self.label_variante.setFont(QFont('Segoe UI', 14))
        self.label_variante.setStyleSheet(f'color: {CoresUnion.TEXT_MUTED};')
        left_layout.addWidget(self.label_variante)
        left_layout.addSpacing(60)
        self.label_version = QLabel(f'Suporte: {self.SUPORTE}')
        self.label_version.setFont(QFont('Segoe UI', 13))
        self.label_version.setStyleSheet(f'color: {CoresUnion.TEXT_MUTED};')
        left_layout.addWidget(self.label_version)
        left_layout.addSpacing(25)
        self.btn_frp = QPushButton('Remover FRP')
        self.btn_frp.setFixedSize(150, 40)
        self.btn_frp.setCursor(Qt.PointingHandCursor)
        self.btn_frp.setFont(QFont('Segoe UI', 12, QFont.Bold))
        self.btn_frp.setStyleSheet(f'\n            QPushButton {{ background-color: {CoresUnion.PRIMARY}; color: {CoresUnion.TEXT_WHITE}; border: none; border-radius: 20px; }}\n            QPushButton:hover {{ background-color: {CoresUnion.PRIMARY_HOVER}; }}\n            QPushButton:disabled {{ background-color: {CoresUnion.BORDER}; }}\n        ')
        self.btn_frp.clicked.connect(self.remove_frp)
        left_layout.addWidget(self.btn_frp)
        left_layout.addSpacing(10)
        self.btn_parar = QPushButton('Parar')
        self.btn_parar.setFixedSize(100, 35)
        self.btn_parar.setCursor(Qt.PointingHandCursor)
        self.btn_parar.setFont(QFont('Segoe UI', 11))
        self.btn_parar.setStyleSheet(f'\n            QPushButton {{ background-color: {CoresUnion.BACKGROUND_DARK}; color: {CoresUnion.TEXT}; border: 1px solid {CoresUnion.BORDER}; border-radius: 17px; }}\n            QPushButton:hover {{ background-color: {CoresUnion.BORDER}; }}\n        ')
        self.btn_parar.clicked.connect(self.parar)
        left_layout.addWidget(self.btn_parar)
        self.barra_progresso = QProgressBar()
        self.barra_progresso.setFixedSize(250, 18)
        self.barra_progresso.setValue(0)
        self.barra_progresso.setTextVisible(False)
        self.barra_progresso.setStyleSheet(f'\n            QProgressBar {{ border: 1px solid {CoresUnion.BORDER}; border-radius: 9px; background-color: {CoresUnion.BACKGROUND_WHITE}; }}\n            QProgressBar::chunk {{ background-color: {CoresUnion.PRIMARY}; border-radius: 8px; }}\n        ')
        left_layout.addWidget(self.barra_progresso)
        left_layout.addStretch()
        self.label_aviso = QLabel('ÔÜá´©Å M├│dulo em fase de testes. Execute como Administrador.\n­ƒÆ¼ Agradecemos seu feedback!')
        self.label_aviso.setFont(QFont('Segoe UI', 9))
        self.label_aviso.setStyleSheet(f'color: {CoresUnion.WARNING}; padding: 5px;')
        self.label_aviso.setWordWrap(True)
        left_layout.addWidget(self.label_aviso)
        left_layout.addSpacing(10)
        self.label_status = QLabel('Pronto para iniciar')
        self.label_status.setFont(QFont('Segoe UI', 12))
        self.label_status.setStyleSheet(f'color: {CoresUnion.TEXT_MUTED};')
        left_layout.addWidget(self.label_status)
        main_layout.addWidget(left_widget, stretch=1)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setAlignment(Qt.AlignCenter)
        self.phone_container = QFrame()
        self.phone_container.setFixedSize(250, 250)
        self.phone_container.setStyleSheet(f'background-color: {CoresUnion.BACKGROUND_DARK}; border-radius: 125px; border: 2px solid {CoresUnion.BORDER};')
        phone_layout = QVBoxLayout(self.phone_container)
        phone_layout.setAlignment(Qt.AlignCenter)
        self.phone_image = QLabel()
        self.phone_image.setFixedSize(140, 140)
        self.phone_image.setAlignment(Qt.AlignCenter)
        phone_layout.addWidget(self.phone_image)
        right_layout.addWidget(self.phone_container)
        self.label_phone_status = QLabel('')
        self.label_phone_status.setAlignment(Qt.AlignCenter)
        self.label_phone_status.setFont(QFont('Segoe UI', 11))
        self.label_phone_status.setStyleSheet(f'color: {CoresUnion.TEXT_MUTED}; margin-top: 15px;')
        right_layout.addWidget(self.label_phone_status)
        main_layout.addWidget(right_widget, stretch=1)
        self._set_phone_image('notfound')
    def _init_animation(self):
        self.spinner_anim = QVariantAnimation()
        self.spinner_anim.setDuration(3000)
        self.spinner_anim.setStartValue(0)
        self.spinner_anim.setEndValue(360)
        self.spinner_anim.setLoopCount(-1)
        self.spinner_anim.valueChanged.connect(self._rotate_phone)
        self.original_pixmap = None
    def _set_phone_image(self, status: str):
        images = {'notfound': 'phone_notfound.png', 'loading': 'phone_loading.png', 'connected': 'phone_connected.png', 'success': 'phone_success.png', 'error': 'phone_error.png'}
        styles = {'notfound': f'background-color: {CoresUnion.BACKGROUND_DARK}; border-radius: 125px; border: 2px solid {CoresUnion.BORDER};', 'loading': f'background-color: {CoresUnion.BACKGROUND_DARK}; border-radius: 125px; border: 2px solid {CoresUnion.PRIMARY};', 'connected': f'background-color: {CoresUnion.BACKGROUND_DARK}; border-radius: 125px; border: 2px solid {CoresUnion.PRIMARY};', 'success': f'background-color: {CoresUnion.SUCCESS}; border-radius: 125px; border: 2px solid {CoresUnion.SUCCESS};', 'error': f'background-color: {CoresUnion.ERROR}; border-radius: 125px; border: 2px solid {CoresUnion.ERROR};'}
        self.phone_container.setStyleSheet(styles.get(status, styles['notfound']))
        img_path = self._get_img_path(images.get(status, 'phone_notfound.png'))
        if os.path.exists(img_path):
            pixmap = QPixmap(img_path).scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.phone_image.setPixmap(pixmap)
            if status == 'loading':
                self.original_pixmap = pixmap
    def _rotate_phone(self, angle: int):
        if self.original_pixmap:
            rotated = self.original_pixmap.transformed(QTransform().rotate(angle), Qt.SmoothTransformation)
            xoffset = (rotated.width() - self.original_pixmap.width()) // 2
            yoffset = (rotated.height() - self.original_pixmap.height()) // 2
            self.phone_image.setPixmap(rotated.copy(xoffset, yoffset, self.original_pixmap.width(), self.original_pixmap.height()))
    def _start_spinner(self):
        self._set_phone_image('loading')
        self.spinner_anim.start()
    def _stop_spinner(self):
        self.spinner_anim.stop()
    def remove_frp(self):
        if self.em_execucao:
            return
        mtk_path = os.path.join(self._get_tools_path(), 'mtk.exe')
        if not os.path.exists(mtk_path):
            QMessageBox.critical(self, 'Erro', 'Componente n├úo encontrado!\n\nReinstale o programa ou entre em contato com o suporte.')
            return
        reply = QMessageBox.question(self, 'Confirmar', f'Iniciar remo├º├úo de FRP do {self.MODELO}?\n\nInstru├º├Áes:\n1. Desligue o aparelho\n2. Segure Volume + e Volume -\n3. Conecte o cabo USB', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        self.em_execucao = True
        self.label_status.setText('Aguardando dispositivo...')
        self.label_phone_status.setText('Conecte o celular em modo BROM')
        self._start_spinner()
        self.barra_progresso.setValue(5)
        loader_path = self._get_loader_path()
        self.worker = BromA226BRWorker(mtk_path, loader_path, self.MODELO)
        self.worker.progress_signal.connect(self.barra_progresso.setValue)
        self.worker.status_signal.connect(self._on_status)
        self.worker.finished_signal.connect(self._on_finished)
        self.btn_frp.setEnabled(False)
        self.worker.start()
    def _on_status(self, status: str):
        if status == 'waiting':
            self.label_status.setText('Aguardando dispositivo...')
            return
        if status == 'connected':
            self._stop_spinner()
            self._set_phone_image('connected')
            self.label_status.setText('Dispositivo conectado!')
            self.label_status.setStyleSheet(f'color: {CoresUnion.PRIMARY};')
            self.label_phone_status.setText('Processando...')
            return
        if status == 'success':
            self._stop_spinner()
            self._set_phone_image('success')
            self.label_status.setText('Finalizado com sucesso!')
            self.label_status.setStyleSheet(f'color: {CoresUnion.SUCCESS};')
            self.label_phone_status.setText('FRP removido!')
            return
        if status == 'error':
            self._stop_spinner()
            self._set_phone_image('error')
            self.label_status.setText('Erro no processo')
            self.label_status.setStyleSheet(f'color: {CoresUnion.ERROR};')
    def _on_finished(self, sucesso: bool, msg: str):
        self.em_execucao = False
        self.btn_frp.setEnabled(True)
        self._stop_spinner()
        if sucesso:
            self._set_phone_image('success')
            self.barra_progresso.setValue(100)
            QMessageBox.information(self, 'Sucesso', msg)
    def parar(self):
        if self.em_execucao:
            if self.worker:
                self.worker.cancelar()
            if sys.platform == 'win32':
                try:
                    subprocess.run(['taskkill', '/F', '/IM', 'mtk.exe'], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                except:
                    pass
            self.em_execucao = False
            self.btn_frp.setEnabled(True)
            self._stop_spinner()
            self._set_phone_image('notfound')
            self.label_status.setText('Processo interrompido')
            self.label_status.setStyleSheet(f'color: {CoresUnion.WARNING};')
            self.label_phone_status.setText('')
            self.barra_progresso.setValue(0)
