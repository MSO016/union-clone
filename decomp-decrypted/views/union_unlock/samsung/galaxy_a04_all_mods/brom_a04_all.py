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
def log_terminal(msg: str):
    print(msg, flush=True)
    return msg
class BromSamsungWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    def __init__(self, mtk_path: str, script_path: str, modelo: str):
        super().__init__()
        self.mtk_path = mtk_path
        self.script_path = script_path
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
            if not os.path.exists(self.script_path):
                self._log('ÔØî ERRO: Script n├úo encontrado!')
                self._log(f'   Caminho: {self.script_path}')
                self.finished_signal.emit(False, 'Script n├úo encontrado')
                self.status_signal.emit('error')
                return
            self._log('=======================================================')
            self._log('  TECH UNION SOLUTIONS - FRP SAMSUNG BROM')
            self._log(f'  Modelo: {self.modelo}')
            self._log('=======================================================')
            self._log('')
            self._log('Ô£à mtk.exe ......: Encontrado')
            self._log(f'Ô£à Script .......: {os.path.basename(self.script_path)}')
            self._log('')
            self._log('­ƒô▒ FASE 1: Aguardando dispositivo para formata├º├úo...')
            self._log('   Conecte o celular em modo BROM:')
            self._log('   1. Desligue o aparelho')
            self._log('   2. Segure Volume + e Volume -')
            self._log('   3. Conecte o cabo USB')
            self._log('')
            self._log('-------------------------------------------------------')
            self.status_signal.emit('waiting')
            self.progress_signal.emit(10)
            comando_mtk = [self.mtk_path, 'e', 'persistent']
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            processo = subprocess.Popen(comando_mtk, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=os.path.dirname(self.mtk_path), creationflags=creationflags)
            device_connected = False
            erase_success = False
            while True:
                if self._cancelado:
                    processo.terminate()
                    self._log('')
                    self._log('Ôøö Processo cancelado pelo usu├írio')
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
                        frases_conexao = ['device detected :)', 'handshake complete', 'da matched', 'sending da', 'uploading da', 'upload da', 'is in brom mode', 'is in brom-mode', 'successfully uploaded', 'boot to succeeded', 'dram setup passed', 'emi data succeeded']
                        if any((frase in linha_lower for frase in frases_conexao)):
                            device_connected = True
                            self.status_signal.emit('connected')
                            self.progress_signal.emit(30)
                            self._log('')
                            self._log('Ô£à Dispositivo detectado e conectado!')
                            self._log('')
                    if 'erasing' in linha_lower or 'successfully' in linha_lower:
                        erase_success = True
                        self.progress_signal.emit(50)
                    if any((err in linha_lower for err in ('no valid da loader found', 'no da_loader config set up', 'error on getting preloader', 'da selection failed', 'daa_sig_verify_failed'))):
                        erase_success = False
            retcode_mtk = processo.wait()
            if retcode_mtk != 0 or not erase_success:
                if not erase_success:
                    if retcode_mtk == 0:
                        self.status_signal.emit('error')
                        self._log('')
                        self._log('ÔØî Processo n├úo conseguiu formatar a parti├º├úo')
                        self._log('   Verifique se o DA Loader ├® compat├¡vel com o dispositivo.')
                        self.finished_signal.emit(False, 'Falha na formata├º├úo - DA Loader incompat├¡vel')
                        return
                self.status_signal.emit('error')
                self._log('')
                self._log(f'ÔØî Falha na formata├º├úo (c├│digo: {retcode_mtk})')
                self.finished_signal.emit(False, 'Erro na formata├º├úo persistent')
                return
            if not device_connected:
                self.status_signal.emit('connected')
                self.progress_signal.emit(50)
            self._log('')
            self._log('=======================================================')
            self._log('­ƒô▒ FASE 2: Executando script do modelo...')
            self._log('=======================================================')
            self._log('')
            self.progress_signal.emit(60)
            comando_script = [self.script_path]
            processo_script = subprocess.Popen(comando_script, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=os.path.dirname(self.script_path), creationflags=creationflags)
            while True:
                if self._cancelado:
                    processo_script.terminate()
                    self._log('Ôøö Processo cancelado')
                    self.finished_signal.emit(False, 'Cancelado')
                    self.status_signal.emit('error')
                    return
                linha = processo_script.stdout.readline()
                if not linha and processo_script.poll() is not None:
                    break
                if linha:
                    self._log(linha.rstrip())
            self.progress_signal.emit(90)
            retcode_script = processo_script.wait()
            if retcode_script == 0:
                self.progress_signal.emit(100)
                self.status_signal.emit('success')
                self._log('')
                self._log('=======================================================')
                self._log('  Ô£à PROCESSO FINALIZADO COM SUCESSO!')
                self._log('=======================================================')
                self._log('')
                self._log('­ƒô▒ FRP removido com sucesso!')
                self._log('ÔÅ│ O dispositivo vai reiniciar automaticamente')
                self._log('­ƒÆí Configure normalmente ap├│s reiniciar!')
                self._log('')
                self._log('=======================================================')
                self._log('  TECH UNION SOLUTIONS - Valeu, t├®cnico! ­ƒÆ¬­ƒçº­ƒçÀ')
                self._log('=======================================================')
                self.finished_signal.emit(True, 'FRP removido com sucesso!')
                return
            self.status_signal.emit('error')
            self._log('')
            self._log(f'ÔØî Script finalizou com erro (c├│digo: {retcode_script})')
            self.finished_signal.emit(False, f'Erro no script (c├│digo: {retcode_script})')
            return
        except Exception as e:
            self.status_signal.emit('error')
            self._log(f'ÔØî Exce├º├úo: {str(e)}')
            self.finished_signal.emit(False, str(e))
    def cancelar(self):
        self._cancelado = True
class BromA04AllWidget(QWidget):
    MODELO = 'Galaxy A04'
    VARIANTE = 'A045 | Todas as variantes'
    SUPORTE = 'Bin├írio E (A045F) | Bin├írio F (A045M)'
    SCRIPT = 'galaxy_a04.exe'
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
    def _get_script_path(self) -> str:
        try:
            from app.utils.path_manager import PathManager
            tools = PathManager.get_unlock_tools_dir()
            if tools:
                p = os.path.normpath(os.path.join(os.path.dirname(tools), 'samsung', 'scripts', self.SCRIPT))
                if os.path.isfile(p):
                    return p
        except Exception:
            pass
        return os.path.join(os.path.dirname(self.script_dir), 'scripts', self.SCRIPT)
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
        self.btn_frp.setStyleSheet(f'\n            QPushButton {{\n                background-color: {CoresUnion.PRIMARY};\n                color: {CoresUnion.TEXT_WHITE};\n                border: none;\n                border-radius: 20px;\n            }}\n            QPushButton:hover {{\n                background-color: {CoresUnion.PRIMARY_HOVER};\n            }}\n            QPushButton:disabled {{\n                background-color: {CoresUnion.BORDER};\n            }}\n        ')
        self.btn_frp.clicked.connect(self.remove_frp)
        left_layout.addWidget(self.btn_frp)
        left_layout.addSpacing(10)
        self.btn_parar = QPushButton('Parar')
        self.btn_parar.setFixedSize(100, 35)
        self.btn_parar.setCursor(Qt.PointingHandCursor)
        self.btn_parar.setFont(QFont('Segoe UI', 11))
        self.btn_parar.setStyleSheet(f'\n            QPushButton {{\n                background-color: {CoresUnion.BACKGROUND_DARK};\n                color: {CoresUnion.TEXT};\n                border: 1px solid {CoresUnion.BORDER};\n                border-radius: 17px;\n            }}\n            QPushButton:hover {{\n                background-color: {CoresUnion.BORDER};\n            }}\n        ')
        self.btn_parar.clicked.connect(self.parar)
        left_layout.addWidget(self.btn_parar)
        self.barra_progresso = QProgressBar()
        self.barra_progresso.setFixedSize(250, 18)
        self.barra_progresso.setValue(0)
        self.barra_progresso.setTextVisible(False)
        self.barra_progresso.setStyleSheet(f'\n            QProgressBar {{\n                border: 1px solid {CoresUnion.BORDER};\n                border-radius: 9px;\n                background-color: {CoresUnion.BACKGROUND_WHITE};\n            }}\n            QProgressBar::chunk {{\n                background-color: {CoresUnion.PRIMARY};\n                border-radius: 8px;\n            }}\n        ')
        left_layout.addWidget(self.barra_progresso)
        left_layout.addStretch()
        self.label_aviso = QLabel('ÔÜá´©Å Se SEC Ctrl = 0 em modo Download, eFuse queimado!\n    O modo BROM provavelmente n├úo funcionar├í.\n­ƒÆí Execute como Administrador.')
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
        self.phone_container.setStyleSheet(f'\n            QFrame {{\n                background-color: {CoresUnion.BACKGROUND_DARK};\n                border-radius: 125px;\n                border: 2px solid {CoresUnion.BORDER};\n            }}\n        ')
        phone_layout = QVBoxLayout(self.phone_container)
        phone_layout.setAlignment(Qt.AlignCenter)
        self.phone_image = QLabel()
        self.phone_image.setFixedSize(140, 140)
        self.phone_image.setAlignment(Qt.AlignCenter)
        self.phone_image.setScaledContents(False)
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
        container_styles = {'notfound': f'background-color: {CoresUnion.BACKGROUND_DARK}; border-radius: 125px; border: 2px solid {CoresUnion.BORDER};', 'loading': f'background-color: {CoresUnion.BACKGROUND_DARK}; border-radius: 125px; border: 2px solid {CoresUnion.PRIMARY};', 'connected': f'background-color: {CoresUnion.BACKGROUND_DARK}; border-radius: 125px; border: 2px solid {CoresUnion.PRIMARY};', 'success': f'background-color: {CoresUnion.SUCCESS}; border-radius: 125px; border: 2px solid {CoresUnion.SUCCESS};', 'error': f'background-color: {CoresUnion.ERROR}; border-radius: 125px; border: 2px solid {CoresUnion.ERROR};'}
        self.phone_container.setStyleSheet(container_styles.get(status, container_styles['notfound']))
        img_path = self._get_img_path(images.get(status, 'phone_notfound.png'))
        if os.path.exists(img_path):
            pixmap = QPixmap(img_path)
            scaled = pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.phone_image.setPixmap(scaled)
            if status == 'loading':
                self.original_pixmap = scaled
                return
            return
        self.phone_image.setText('­ƒô▒')
        self.phone_image.setStyleSheet(f'font-size: 50px; color: {CoresUnion.TEXT};')
    def _rotate_phone(self, angle: int):
        if self.original_pixmap:
            transform = QTransform().rotate(angle)
            rotated = self.original_pixmap.transformed(transform, Qt.SmoothTransformation)
            xoffset = (rotated.width() - self.original_pixmap.width()) // 2
            yoffset = (rotated.height() - self.original_pixmap.height()) // 2
            cropped = rotated.copy(xoffset, yoffset, self.original_pixmap.width(), self.original_pixmap.height())
            self.phone_image.setPixmap(cropped)
    def _start_spinner(self):
        self._set_phone_image('loading')
        self.spinner_anim.start()
    def _stop_spinner(self):
        self.spinner_anim.stop()
    def remove_frp(self):
        if self.em_execucao:
            QMessageBox.warning(self, 'Aviso', 'Um processo j├í est├í em execu├º├úo.')
            return
        mtk_path = os.path.join(self._get_tools_path(), 'mtk.exe')
        script_path = self._get_script_path()
        if not os.path.exists(mtk_path):
            QMessageBox.critical(self, 'Erro', 'Componente n├úo encontrado!\n\nReinstale o programa ou entre em contato com o suporte.')
            return
        if not os.path.exists(script_path):
            QMessageBox.critical(self, 'Erro', 'Componente n├úo encontrado!\n\nReinstale o programa ou entre em contato com o suporte.')
            return
        reply = QMessageBox.question(self, 'Confirmar', f'Iniciar remo├º├úo de FRP do {self.MODELO}?\n\nInstru├º├Áes:\n1. Conecte o aparelho desligado\n2. Assim que aparecer o logo, segure o bot├úo Power\n   por 4 segundos\n\nContinuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        self.em_execucao = True
        self.label_status.setText('Aguardando dispositivo...')
        self.label_status.setStyleSheet(f'color: {CoresUnion.TEXT_MUTED};')
        self.label_phone_status.setText('Conecte o celular em modo BROM')
        self._start_spinner()
        self.barra_progresso.setValue(5)
        self.worker = BromSamsungWorker(mtk_path, script_path, self.MODELO)
        self.worker.progress_signal.connect(self.barra_progresso.setValue)
        self.worker.status_signal.connect(self._on_status)
        self.worker.finished_signal.connect(self._on_finished)
        self.btn_frp.setEnabled(False)
        self.worker.start()
    def _on_status(self, status: str):
        if status == 'waiting':
            self.label_status.setText('Aguardando dispositivo...')
            self.label_status.setStyleSheet(f'color: {CoresUnion.TEXT_MUTED};')
            self.label_phone_status.setText('Conecte o celular em modo BROM')
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
            self.label_phone_status.setText('FRP removido! Ô£à')
            return
        if status == 'error':
            self._stop_spinner()
            self._set_phone_image('error')
            self.label_status.setText('Erro no processo')
            self.label_status.setStyleSheet(f'color: {CoresUnion.ERROR};')
            self.label_phone_status.setText('Verifique e tente novamente')
    def _on_finished(self, sucesso: bool, mensagem: str):
        self.em_execucao = False
        self.btn_frp.setEnabled(True)
        self._stop_spinner()
        if sucesso:
            self._set_phone_image('success')
            self.barra_progresso.setValue(100)
            QMessageBox.information(self, 'Sucesso', mensagem)
    def parar(self):
        if self.em_execucao:
            self.label_status.setText('Parando processo...')
            if self.worker:
                self.worker.cancelar()
            if sys.platform == 'win32':
                try:
                    subprocess.run(['taskkill', '/F', '/IM', 'mtk.exe'], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    subprocess.run(['taskkill', '/F', '/IM', self.SCRIPT], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                except:
                    pass
            self.em_execucao = False
            self.btn_frp.setEnabled(True)
            self.label_status.setText('Processo interrompido')
            self.label_status.setStyleSheet(f'color: {CoresUnion.WARNING};')
            self.label_phone_status.setText('')
            self._stop_spinner()
            self._set_phone_image('notfound')
            self.barra_progresso.setValue(0)
