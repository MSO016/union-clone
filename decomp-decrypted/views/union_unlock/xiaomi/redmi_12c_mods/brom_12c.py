import os
import sys
import subprocess
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QFrame, QMessageBox)
from PyQt5.QtCore import (QThread, pyqtSignal, Qt, QVariantAnimation)
from PyQt5.QtGui import (QFont, QPixmap, QTransform)
class CoresUnion:
    BACKGROUND = '#f5f5f5'
    BACKGROUND_DARK = '#e8e8e8'
    BACKGROUND_WHITE = '#ffffff'
    PRIMARY = '#ff6700'
    PRIMARY_HOVER = '#e55d00'
    SUCCESS = '#27ae60'
    ERROR = '#e74c3c'
    WARNING = '#f39c12'
    TEXT = '#2c3e50'
    TEXT_MUTED = '#7f8c8d'
    TEXT_WHITE = '#ffffff'
    BORDER = '#bdc3c7'
class Brom12CWorker(QThread):
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
                self._log('Erro: mtk.exe nao encontrado!')
                self.finished_signal.emit(False, 'mtk.exe nao encontrado')
                self.status_signal.emit('error')
                return
            self._log('=======================================================')
            self._log('  TECH UNION SOLUTIONS - FRP XIAOMI BROM')
            self._log('  Modelo: ' + self.modelo)
            self._log('=======================================================')
            self._log('')
            self._log('mtk.exe ......: Encontrado')
            if self.loader_path and os.path.exists(self.loader_path):
                self._log('Loader .......: ' + os.path.basename(self.loader_path))
                comando = [self.mtk_path, 'e', 'frp,persist,userdata', '--loader', self.loader_path]
            else:
                self._log('Erro: Loader nao encontrado!')
                self._log('Caminho: ' + str(self.loader_path))
                self.finished_signal.emit(False, 'Loader nao encontrado')
                self.status_signal.emit('error')
                return
            self._log('')
            self._log('Aguardando dispositivo...')
            self._log('   Conecte o celular em modo BROM:')
            self._log('   1. Desligue o aparelho')
            self._log('   2. Segure Volume + e Volume -')
            self._log('   3. Conecte o cabo USB')
            self._log('')
            self._log('-------------------------------------------------------')
            self.status_signal.emit('waiting')
            self.progress_signal.emit(10)
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            processo = subprocess.Popen(comando, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=False, cwd=os.path.dirname(self.mtk_path), creationflags=creationflags)
            device_connected = False
            erase_started = False
            erro_detectado = False
            sucesso_format = False
            if self._cancelado:
                processo.terminate()
                self._log('Processo cancelado pelo usuario')
                self.finished_signal.emit(False, 'Cancelado')
                self.status_signal.emit('error')
                return
            linha_bytes = processo.stdout.readline()
            if not linha_bytes and processo.poll() is not None:
                pass
            elif linha_bytes:
                pass
            try:
                linha = linha_bytes.decode('utf-8', errors='replace').rstrip()
            except:
                linha = linha_bytes.decode('latin-1', errors='replace').rstrip()
            else:
                self._log(linha)
                linha_lower = linha.lower()
                if not device_connected:
                    if 'waiting' not in linha_lower:
                        frases_conexao = ['device detected :)', 'handshake complete', 'da matched', 'sending da', 'uploading da', 'upload da', 'is in brom mode', 'successfully uploaded', 'boot to succeeded', 'dram setup passed']
                        if any((frase in linha_lower for frase in frases_conexao)):
                            device_connected = True
                            self.status_signal.emit('connected')
                            self.progress_signal.emit(40)
                            self._log('\nDispositivo detectado e conectado!\n')
                if device_connected and not erase_started:
                    if 'erasing' in linha_lower or 'formatting' in linha_lower:
                        erase_started = True
                        self.progress_signal.emit(70)
                if 'formatted sector' in linha_lower or 'erased sector' in linha_lower:
                    sucesso_format = True
                    self.progress_signal.emit(95)
                if 'daa_sig_verify_failed' in linha_lower:
                    erro_detectado = 'auth'
                elif any((err in linha_lower for err in ('no valid da loader found', 'no da_loader config set up', 'error on getting preloader', 'da selection failed'))):
                    erro_detectado = 'da_loader'
                retcode = processo.wait()
                if not sucesso_format or erro_detectado:
                    if retcode == 0 and not erro_detectado:
                        pass
                self.progress_signal.emit(100)
                self.status_signal.emit('success')
                self._log('\n=======================================================')
                self._log('  PROCESSO FINALIZADO COM SUCESSO!')
                self._log('=======================================================')
                self._log('\nFRP removido com sucesso!')
                self._log('O dispositivo vai reiniciar automaticamente')
                self._log('Configure normalmente apos reiniciar!')
                self._log('\n=======================================================')
                self._log('  TECH UNION SOLUTIONS')
                self._log('=======================================================')
                self.finished_signal.emit(True, 'Processo conclu├¡do!\n\nÔÜá´©Å IMPORTANTE: Verifique se o FRP foi realmente removido.\n\nCaso ainda apare├ºa a tela de conta Google,\ntente novamente ou use o m├®todo Test Point.')
                return
        except Exception as e:
            self.status_signal.emit('error')
            self._log('Excecao: ' + str(e))
            self.finished_signal.emit(False, str(e))
    def cancelar(self):
        self._cancelado = True
class Brom12CWidget(QWidget):
    MODELO = 'Redmi 12C'
    VARIANTE = 'MT6768/MT6769 (Helio G85)'
    ANDROID = 'Ate Android 14'
    LOADER = 'Redmi_9_MT6768.bin'
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
        try:
            from app.utils.path_manager import PathManager
            tools = PathManager.get_unlock_tools_dir()
            if tools:
                p = os.path.normpath(os.path.join(os.path.dirname(tools), 'xiaomi', 'DA', self.LOADER))
                if os.path.isfile(p):
                    return p
        except Exception:
            pass
        base = os.path.dirname(os.path.abspath(__file__))
        return os.path.normpath(os.path.join(base, '..', 'DA', self.LOADER))
    def setup_ui(self):
        self.setStyleSheet('background-color: ' + CoresUnion.BACKGROUND + ';')
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(50)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        left_layout.setAlignment(Qt.AlignTop)
        self.label_modelo = QLabel('Xiaomi ' + self.MODELO)
        self.label_modelo.setFont(QFont('Segoe UI', 24, QFont.Bold))
        self.label_modelo.setStyleSheet('color: ' + CoresUnion.TEXT + ';')
        left_layout.addWidget(self.label_modelo)
        self.label_variante = QLabel(self.VARIANTE)
        self.label_variante.setFont(QFont('Segoe UI', 14))
        self.label_variante.setStyleSheet('color: ' + CoresUnion.TEXT_MUTED + ';')
        left_layout.addWidget(self.label_variante)
        left_layout.addSpacing(60)
        self.label_version = QLabel('Suporte: ' + self.ANDROID)
        self.label_version.setFont(QFont('Segoe UI', 13))
        self.label_version.setStyleSheet('color: ' + CoresUnion.TEXT_MUTED + ';')
        left_layout.addWidget(self.label_version)
        left_layout.addSpacing(25)
        self.btn_frp = QPushButton('Remover FRP')
        self.btn_frp.setFixedSize(150, 40)
        self.btn_frp.setCursor(Qt.PointingHandCursor)
        self.btn_frp.setFont(QFont('Segoe UI', 12, QFont.Bold))
        self.btn_frp.setStyleSheet('QPushButton { background-color: ' + CoresUnion.PRIMARY + '; color: ' + CoresUnion.TEXT_WHITE + '; border: none; border-radius: 20px; } QPushButton:hover { background-color: ' + CoresUnion.PRIMARY_HOVER + '; } QPushButton:disabled { background-color: ' + CoresUnion.BORDER + '; }')
        self.btn_frp.clicked.connect(self.remove_frp)
        left_layout.addWidget(self.btn_frp)
        left_layout.addSpacing(10)
        self.btn_parar = QPushButton('Parar')
        self.btn_parar.setFixedSize(100, 35)
        self.btn_parar.setCursor(Qt.PointingHandCursor)
        self.btn_parar.setFont(QFont('Segoe UI', 11))
        self.btn_parar.setStyleSheet('QPushButton { background-color: ' + CoresUnion.BACKGROUND_DARK + '; color: ' + CoresUnion.TEXT + '; border: 1px solid ' + CoresUnion.BORDER + '; border-radius: 17px; } QPushButton:hover { background-color: ' + CoresUnion.BORDER + '; }')
        self.btn_parar.clicked.connect(self.parar)
        left_layout.addWidget(self.btn_parar)
        self.barra_progresso = QProgressBar()
        self.barra_progresso.setFixedSize(250, 18)
        self.barra_progresso.setValue(0)
        self.barra_progresso.setTextVisible(False)
        self.barra_progresso.setStyleSheet('QProgressBar { border: 1px solid ' + CoresUnion.BORDER + '; border-radius: 9px; background-color: ' + CoresUnion.BACKGROUND_WHITE + '; } QProgressBar::chunk { background-color: ' + CoresUnion.PRIMARY + '; border-radius: 8px; }')
        left_layout.addWidget(self.barra_progresso)
        left_layout.addStretch()
        self.label_aviso = QLabel('Execute como Administrador.')
        self.label_aviso.setFont(QFont('Segoe UI', 9))
        self.label_aviso.setStyleSheet('color: ' + CoresUnion.TEXT_MUTED + '; padding: 5px;')
        self.label_aviso.setWordWrap(True)
        left_layout.addWidget(self.label_aviso)
        left_layout.addSpacing(10)
        self.label_status = QLabel('Pronto para iniciar')
        self.label_status.setFont(QFont('Segoe UI', 12))
        self.label_status.setStyleSheet('color: ' + CoresUnion.TEXT_MUTED + ';')
        left_layout.addWidget(self.label_status)
        main_layout.addWidget(left_widget, stretch=1)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setAlignment(Qt.AlignCenter)
        self.phone_container = QFrame()
        self.phone_container.setFixedSize(250, 250)
        self.phone_container.setStyleSheet('background-color: ' + CoresUnion.BACKGROUND_DARK + '; border-radius: 125px; border: 2px solid ' + CoresUnion.BORDER + ';')
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
        self.label_phone_status.setStyleSheet('color: ' + CoresUnion.TEXT_MUTED + '; margin-top: 15px;')
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
        styles = {'notfound': 'background-color: ' + CoresUnion.BACKGROUND_DARK + '; border-radius: 125px; border: 2px solid ' + CoresUnion.BORDER + ';', 'loading': 'background-color: ' + CoresUnion.BACKGROUND_DARK + '; border-radius: 125px; border: 2px solid ' + CoresUnion.PRIMARY + ';', 'connected': 'background-color: ' + CoresUnion.BACKGROUND_DARK + '; border-radius: 125px; border: 2px solid ' + CoresUnion.PRIMARY + ';', 'success': 'background-color: ' + CoresUnion.SUCCESS + '; border-radius: 125px; border: 2px solid ' + CoresUnion.SUCCESS + ';', 'error': 'background-color: ' + CoresUnion.ERROR + '; border-radius: 125px; border: 2px solid ' + CoresUnion.ERROR + ';'}
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
        loader_path = self._get_loader_path()
        if not os.path.exists(mtk_path):
            QMessageBox.critical(self, 'Erro', 'Componente n├úo encontrado!\n\nReinstale o programa ou entre em contato com o suporte.')
            return
        if not os.path.exists(loader_path):
            QMessageBox.critical(self, 'Erro', 'Componente n├úo encontrado!\n\nReinstale o programa ou entre em contato com o suporte.')
            return
        reply = QMessageBox.question(self, 'Confirmar', 'Iniciar remocao de FRP do ' + self.MODELO + '?\n\nMODO BROM\n\n1. Desligue o aparelho completamente\n2. Segure Volume + e Volume -\n3. Conecte o cabo USB\n\nContinuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        self.em_execucao = True
        self.label_status.setText('Aguardando dispositivo...')
        self.label_status.setStyleSheet('color: ' + CoresUnion.TEXT_MUTED + ';')
        self.label_phone_status.setText('Conecte o celular em modo BROM')
        self._start_spinner()
        self.barra_progresso.setValue(5)
        self.worker = Brom12CWorker(mtk_path, loader_path, self.MODELO)
        self.worker.progress_signal.connect(self.barra_progresso.setValue)
        self.worker.status_signal.connect(self._on_status)
        self.worker.log_signal.connect(self._on_log)
        self.worker.finished_signal.connect(self._on_finished)
        self.btn_frp.setEnabled(False)
        self.worker.start()
    def _on_log(self, msg: str):
        pass
    def _on_status(self, status: str):
        if status == 'waiting':
            self.label_status.setText('Aguardando dispositivo...')
            self.label_status.setStyleSheet('color: ' + CoresUnion.TEXT_MUTED + ';')
            return
        if status == 'connected':
            self._stop_spinner()
            self._set_phone_image('connected')
            self.label_status.setText('Dispositivo conectado!')
            self.label_status.setStyleSheet('color: ' + CoresUnion.PRIMARY + ';')
            self.label_phone_status.setText('Processando...')
            return
        if status == 'success':
            self._stop_spinner()
            self._set_phone_image('success')
            self.label_status.setText('Finalizado com sucesso!')
            self.label_status.setStyleSheet('color: ' + CoresUnion.SUCCESS + ';')
            self.label_phone_status.setText('FRP removido!')
            return
        if status == 'error':
            self._stop_spinner()
            self._set_phone_image('error')
            self.label_status.setText('Erro no processo')
            self.label_status.setStyleSheet('color: ' + CoresUnion.ERROR + ';')
            self.label_phone_status.setText('Verifique e tente novamente')
    def _on_finished(self, sucesso: bool, msg: str):
        self.em_execucao = False
        self.btn_frp.setEnabled(True)
        self._stop_spinner()
        if sucesso:
            self._set_phone_image('success')
            self.barra_progresso.setValue(100)
            QMessageBox.information(self, 'Sucesso', msg)
            return
        self._set_phone_image('error')
        QMessageBox.warning(self, 'Aviso', msg)
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
            self.label_status.setStyleSheet('color: ' + CoresUnion.WARNING + ';')
            self.label_phone_status.setText('')
            self.barra_progresso.setValue(0)
