import os
import sys
import subprocess
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QFrame, QMessageBox)
from PyQt5.QtCore import (QThread, pyqtSignal, Qt, QVariantAnimation)
from PyQt5.QtGui import (QFont, QPixmap, QTransform)
from ..galaxy_a04_all_mods.brom_a04_all import CoresUnion
class EdlA23A236mUBWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    def __init__(self, edl_path: str, loader_path: str, modelo: str):
        super().__init__()
        self.edl_path = edl_path
        self.loader_path = loader_path
        self.modelo = modelo
        self._cancelado = False
    def cancelar(self):
        self._cancelado = True
    def _run_command(self, args: list, description: str) -> tuple:
        cmd = [self.edl_path, '--loader', self.loader_path, '--memory', 'Ufs'] + args
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=os.path.dirname(self.edl_path), creationflags=creationflags)
            output_lines = []
            success = False
            no_device = False
            timeout_error = False
            while True:
                if self._cancelado:
                    process.terminate()
                    return (False, 'Cancelado pelo usuario')
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    linha = line.rstrip()
                    output_lines.append(linha)
                    linha_lower = linha.lower()
                    if 'found device' in linha_lower:
                        self.status_signal.emit('connected')
                        self.progress_signal.emit(40)
                    if 'successfully erased' in linha_lower:
                        success = True
                        self.progress_signal.emit(80)
                    elif 'power command' in linha_lower and 'sent successfully' in linha_lower:
                        success = True
                    elif 'loader uploaded' in linha_lower:
                        self.progress_signal.emit(30)
                    if 'no qualcomm edl devices found' in linha_lower:
                        no_device = True
                    elif 'timeout' in linha_lower:
                        timeout_error = True
            process.wait()
            if no_device:
                return (False, 'Dispositivo nao encontrado!\n\nConecte o aparelho em modo EDL antes de iniciar.')
            if timeout_error and not success:
                return (False, 'Erro de comunicacao USB!\n\nReconecte o dispositivo em modo EDL e tente novamente.')
            if success:
                return (True, 'FRP removido com sucesso!')
        except Exception:
            return (False, 'Erro inesperado.\n\nReinstale o programa ou entre\nem contato com o suporte.')
        return (False, 'Falha na comunica├º├úo com o dispositivo.\n\nVerifique a conex├úo USB e tente novamente.')
    def run(self):
        try:
            if not (os.path.exists(self.edl_path) and os.path.exists(self.loader_path)):
                self.finished_signal.emit(False, 'Componente n├úo encontrado!\n\nReinstale o programa ou entre\nem contato com o suporte.')
                self.status_signal.emit('error')
                return
            self.status_signal.emit('waiting')
            self.progress_signal.emit(10)
            sucesso, mensagem = self._run_command(['erase-part', 'persistent'], 'Apagando FRP')
            if self._cancelado:
                self.finished_signal.emit(False, 'Cancelado')
                return
            if not sucesso:
                self.finished_signal.emit(False, mensagem)
                self.status_signal.emit('error')
                return
            self.progress_signal.emit(90)
            self._run_command(['reset'], 'Reiniciando')
            self.progress_signal.emit(100)
            self.status_signal.emit('success')
            self.finished_signal.emit(True, 'FRP removido com sucesso!\n\nO aparelho ir├í reiniciar automaticamente.')
            return
        except OSError as e:
            self.status_signal.emit('error')
            if hasattr(e, 'winerror') and e.winerror == 740:
                self.finished_signal.emit(False, "Execute como Administrador!\n\nClique com bot├úo direito no programa\ne selecione 'Executar como administrador'.")
        except Exception:
            self.finished_signal.emit(False, 'Erro inesperado.\n\nReinstale o programa ou entre\nem contato com o suporte.')
            self.status_signal.emit('error')
class EdlA23A236mUBWidget(QWidget):
    MODELO = 'Galaxy A23'
    VARIANTE = 'A236M UB'
    SUPORTE = 'Android 12-14'
    CHIPSET = 'Snapdragon 680 (SM6225)'
    LOADER = 'a236m_ub_prog_ufs_firehose_sm6150.elf'
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
    def _get_edl_path(self) -> str:
        try:
            from app.utils.path_manager import PathManager
            p = PathManager.get_unlock_tool('edl-ng.exe')
            if p and os.path.isfile(p):
                return p
        except Exception:
            pass
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(base, 'tools', 'edl-ng.exe')
    def _get_loader_path(self) -> str:
        try:
            from app.utils.path_manager import PathManager
            tools = PathManager.get_unlock_tools_dir()
            if tools:
                p = os.path.normpath(os.path.join(os.path.dirname(tools), 'samsung', 'loaders', self.LOADER))
                if os.path.isfile(p):
                    return p
        except Exception:
            pass
        return os.path.join(os.path.dirname(self.script_dir), 'loaders', self.LOADER)
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
        left_layout.addSpacing(10)
        self.label_modelo = QLabel(f'Samsung {self.MODELO}')
        self.label_modelo.setFont(QFont('Segoe UI', 24, QFont.Bold))
        self.label_modelo.setStyleSheet(f'color: {CoresUnion.TEXT};')
        left_layout.addWidget(self.label_modelo)
        self.label_variante = QLabel(self.VARIANTE)
        self.label_variante.setFont(QFont('Segoe UI', 14))
        self.label_variante.setStyleSheet(f'color: {CoresUnion.TEXT_MUTED};')
        left_layout.addWidget(self.label_variante)
        left_layout.addSpacing(30)
        self.label_chipset = QLabel(f'Chipset: {self.CHIPSET}')
        self.label_chipset.setFont(QFont('Segoe UI', 11))
        self.label_chipset.setStyleSheet(f'color: {CoresUnion.TEXT_MUTED};')
        left_layout.addWidget(self.label_chipset)
        self.label_storage = QLabel('Storage: UFS')
        self.label_storage.setFont(QFont('Segoe UI', 11))
        self.label_storage.setStyleSheet(f'color: {CoresUnion.TEXT_MUTED};')
        left_layout.addWidget(self.label_storage)
        self.label_version = QLabel(f'Suporte: {self.SUPORTE}')
        self.label_version.setFont(QFont('Segoe UI', 11))
        self.label_version.setStyleSheet(f'color: {CoresUnion.TEXT_MUTED};')
        left_layout.addWidget(self.label_version)
        self.label_metodo = QLabel('Modo: EDL (Qualcomm)')
        self.label_metodo.setFont(QFont('Segoe UI', 11))
        self.label_metodo.setStyleSheet(f'color: {CoresUnion.PRIMARY};')
        left_layout.addWidget(self.label_metodo)
        left_layout.addSpacing(25)
        self.btn_frp = QPushButton('Remover FRP')
        self.btn_frp.setFixedSize(160, 45)
        self.btn_frp.setCursor(Qt.PointingHandCursor)
        self.btn_frp.setFont(QFont('Segoe UI', 12, QFont.Bold))
        self.btn_frp.setStyleSheet(f'\n            QPushButton {{ \n                background-color: {CoresUnion.PRIMARY}; \n                color: {CoresUnion.TEXT_WHITE}; \n                border: none; \n                border-radius: 22px; \n            }} \n            QPushButton:hover {{ \n                background-color: {CoresUnion.PRIMARY_HOVER}; \n            }} \n            QPushButton:disabled {{ \n                background-color: {CoresUnion.BORDER}; \n            }}\n        ')
        self.btn_frp.clicked.connect(self.remove_frp)
        left_layout.addWidget(self.btn_frp)
        left_layout.addSpacing(10)
        self.btn_parar = QPushButton('Parar')
        self.btn_parar.setFixedSize(100, 35)
        self.btn_parar.setCursor(Qt.PointingHandCursor)
        self.btn_parar.setFont(QFont('Segoe UI', 11))
        self.btn_parar.setStyleSheet(f'\n            QPushButton {{ \n                background-color: {CoresUnion.BACKGROUND_DARK}; \n                color: {CoresUnion.TEXT}; \n                border: 1px solid {CoresUnion.BORDER}; \n                border-radius: 17px; \n            }} \n            QPushButton:hover {{ \n                background-color: {CoresUnion.BORDER}; \n            }}\n        ')
        self.btn_parar.clicked.connect(self.parar)
        left_layout.addWidget(self.btn_parar)
        self.barra_progresso = QProgressBar()
        self.barra_progresso.setFixedSize(260, 18)
        self.barra_progresso.setValue(0)
        self.barra_progresso.setTextVisible(False)
        self.barra_progresso.setStyleSheet(f'\n            QProgressBar {{ \n                border: 1px solid {CoresUnion.BORDER}; \n                border-radius: 9px; \n                background-color: {CoresUnion.BACKGROUND_WHITE}; \n            }} \n            QProgressBar::chunk {{ \n                background-color: {CoresUnion.PRIMARY}; \n                border-radius: 8px; \n            }}\n        ')
        left_layout.addWidget(self.barra_progresso)
        left_layout.addStretch()
        self.label_aviso = QLabel('IMPORTANTE: Conecte o aparelho em modo EDL\n   ANTES de clicar em Remover FRP!\nDriver: Qualcomm Serial\nMetodo: Test Point ou Combinacao de Teclas\nVol- + Inserir cabo USB')
        self.label_aviso.setFont(QFont('Segoe UI', 9))
        self.label_aviso.setStyleSheet(f'color: {CoresUnion.PRIMARY}; padding: 5px;')
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
        self.phone_container.setStyleSheet(f'\n            background-color: {CoresUnion.BACKGROUND_DARK}; \n            border-radius: 125px; \n            border: 2px solid {CoresUnion.BORDER};\n        ')
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
                return
            return
        self.phone_image.setText('­ƒô▒')
        self.phone_image.setStyleSheet(f'font-size: 50px; color: {CoresUnion.TEXT};')
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
        edl_path = os.path.normpath(self._get_edl_path())
        loader_path = self._get_loader_path()
        if not (os.path.exists(edl_path) and os.path.exists(loader_path)):
            QMessageBox.critical(self, 'Erro', 'Componente n├úo encontrado!\n\nReinstale o programa ou entre\nem contato com o suporte.')
            return
        reply = QMessageBox.question(self, 'Confirmar', f'Iniciar remocao de FRP do {self.MODELO} {self.VARIANTE}?\n\nIMPORTANTE: O aparelho JA deve estar conectado\nem modo EDL (porta 9008) ANTES de continuar!\n\nCOMO ENTRAR EM MODO EDL:\n\nOpcao 1 - Combinacao de Teclas:\n  - Desligue o aparelho\n  - Segure Vol- e conecte o cabo USB\n\nOpcao 2 - Test Point:\n  - Abra o aparelho\n  - Localize o ponto EDL na placa\n  - Faca curto no Test Point\n  - Conecte o cabo USB\n\nO aparelho esta em modo EDL?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        self.em_execucao = True
        self.label_status.setText('Aguardando dispositivo...')
        self.label_phone_status.setText('Conecte o celular em modo EDL')
        self._start_spinner()
        self.barra_progresso.setValue(5)
        self.worker = EdlA23A236mUBWorker(edl_path, loader_path, self.MODELO)
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
            return
        self._set_phone_image('error')
        self.label_phone_status.setText('Falha no processo')
        self.barra_progresso.setValue(0)
        QMessageBox.critical(self, 'Erro', msg)
    def parar(self):
        if self.em_execucao:
            if self.worker:
                self.worker.cancelar()
            if sys.platform == 'win32':
                try:
                    subprocess.run(['taskkill', '/F', '/IM', 'edl-ng.exe'], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
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
