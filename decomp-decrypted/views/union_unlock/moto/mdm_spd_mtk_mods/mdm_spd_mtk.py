import os
import sys
import subprocess
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QFrame, QMessageBox)
from PyQt5.QtCore import (Qt, QThread, pyqtSignal, QVariantAnimation)
from PyQt5.QtGui import (QFont, QPixmap, QTransform)
from ..moto_e22_mods.brom_e22 import CoresUnion
class FastbootWorker(QThread):
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    def __init__(self, fastboot_path: str, empty_file_path: str, parent=None):
        super().__init__(parent)
        self.fastboot_path = fastboot_path
        self.empty_file_path = empty_file_path
        self.cancelado = False
    def cancelar(self):
        self.cancelado = True
    def _run_fastboot(self, args: list, timeout: int=30) -> tuple:
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            result = subprocess.run([self.fastboot_path] + args, capture_output=True, text=True, timeout=timeout, creationflags=creationflags)
            output = result.stdout + result.stderr
            return result.returncode == 0, output
        except subprocess.TimeoutExpired:
            return (False, 'Timeout - dispositivo n├úo respondeu')
        except Exception as e:
            return False, str(e)
    def run(self):
        try:
            self.log_signal.emit('==================================================')
            self.log_signal.emit('­ƒöº MDM SPD/MTK - WIPE DATA RESET')
            self.log_signal.emit('==================================================')
            self.log_signal.emit('')
            self.log_signal.emit('­ƒô▒ Verificando dispositivo em modo Fastboot...')
            self.status_signal.emit('waiting')
            self.progress_signal.emit(10)
            for i in range(30):
                if self.cancelado:
                    self.finished_signal.emit(False, 'Cancelado pelo usu├írio')
                    return
                sucesso, output = self._run_fastboot(['devices'], timeout=5)
                if sucesso and output.strip() and 'fastboot' in output.lower():
                    self.log_signal.emit('Ô£à Dispositivo detectado em modo Fastboot!')
                    self.status_signal.emit('connected')
                    self.progress_signal.emit(30)
                    break
                self.msleep(1000)
            else:
                self.log_signal.emit('ÔØî Nenhum dispositivo encontrado em modo Fastboot')
                self.status_signal.emit('error')
                self.finished_signal.emit(False, 'Dispositivo n├úo encontrado!\n\nVerifique:\n1. Aparelho em modo Fastboot\n2. Drivers instalados\n3. Cabo USB funcionando')
                return
            if self.cancelado:
                self.finished_signal.emit(False, 'Cancelado pelo usu├írio')
                return
            self.log_signal.emit('')
            self.log_signal.emit('­ƒöä Limpando userdata (Wipe Data)...')
            self.progress_signal.emit(40)
            sucesso, output = self._run_fastboot(['flash', 'userdata', self.empty_file_path], timeout=60)
            if sucesso or 'finished' in output.lower() or 'okay' in output.lower():
                self.log_signal.emit('Ô£à Userdata limpo com sucesso!')
            else:
                self.log_signal.emit(f'ÔÜá´©Å Userdata: {output.strip()}')
            self.progress_signal.emit(50)
            if self.cancelado:
                self.finished_signal.emit(False, 'Cancelado pelo usu├írio')
                return
            self.log_signal.emit('')
            self.log_signal.emit('­ƒöä Limpando cache...')
            self.progress_signal.emit(60)
            sucesso, output = self._run_fastboot(['flash', 'cache', self.empty_file_path], timeout=60)
            if sucesso or 'finished' in output.lower() or 'okay' in output.lower():
                self.log_signal.emit('Ô£à Cache limpo com sucesso!')
            else:
                self.log_signal.emit(f'ÔÜá´©Å Cache: {output.strip()}')
            self.progress_signal.emit(70)
            if self.cancelado:
                self.finished_signal.emit(False, 'Cancelado pelo usu├írio')
                return
            self.log_signal.emit('')
            self.log_signal.emit('­ƒöä Reiniciando dispositivo...')
            sucesso, output = self._run_fastboot(['reboot'], timeout=30)
            self.progress_signal.emit(100)
            self.log_signal.emit('')
            self.log_signal.emit('==================================================')
            self.log_signal.emit('  Ô£à PROCESSO FINALIZADO!')
            self.log_signal.emit('==================================================')
            self.log_signal.emit('')
            self.log_signal.emit('­ƒô▒ Wipe Data realizado com sucesso!')
            self.log_signal.emit('ÔÅ│ Aguarde o aparelho reiniciar')
            self.log_signal.emit('­ƒÆí Configure normalmente ap├│s reiniciar!')
            self.log_signal.emit('')
            self.log_signal.emit('ÔÜá´©Å NOTA: Este m├®todo N├âO remove FRP!')
            self.log_signal.emit('   Use apenas para Factory Reset.')
            self.log_signal.emit('')
            self.log_signal.emit('==================================================')
            self.log_signal.emit('  TECH UNION SOLUTIONS ­ƒÆ¬­ƒçº­ƒçÀ')
            self.log_signal.emit('==================================================')
            self.status_signal.emit('success')
            self.finished_signal.emit(True, 'Ô£à Wipe Data realizado com sucesso!\n\nO aparelho vai reiniciar.\nConfigure normalmente!\n\nÔÜá´©Å NOTA: Este m├®todo N├âO remove FRP!')
            return
        except Exception as e:
            self.log_signal.emit(f'ÔØî Erro: {str(e)}')
            self.status_signal.emit('error')
            self.finished_signal.emit(False, f'Erro: {str(e)}')
class MdmSpdMtkWidget(QWidget):
    MODELO = 'MDM SPD/MTK'
    VARIANTE = 'Motorola SPD/MTK Antigos'
    ANDROID = 'Apenas Factory Reset (N├âO remove FRP)'
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
        self.label_teste = QLabel('­ƒº¬ EM TESTE')
        self.label_teste.setFont(QFont('Segoe UI', 10, QFont.Bold))
        self.label_teste.setStyleSheet(f'\n            background-color: {CoresUnion.WARNING};\n            color: white;\n            padding: 4px 12px;\n            border-radius: 10px;\n        ')
        self.label_teste.setFixedWidth(100)
        self.label_teste.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.label_teste)
        left_layout.addSpacing(10)
        self.label_modelo = QLabel(f'Motorola {self.MODELO}')
        self.label_modelo.setFont(QFont('Segoe UI', 24, QFont.Bold))
        self.label_modelo.setStyleSheet(f'color: {CoresUnion.TEXT};')
        left_layout.addWidget(self.label_modelo)
        self.label_variante = QLabel(self.VARIANTE)
        self.label_variante.setFont(QFont('Segoe UI', 14))
        self.label_variante.setStyleSheet(f'color: {CoresUnion.TEXT_MUTED};')
        left_layout.addWidget(self.label_variante)
        left_layout.addSpacing(30)
        self.label_version = QLabel(f'Suporte: {self.ANDROID}')
        self.label_version.setFont(QFont('Segoe UI', 13))
        self.label_version.setStyleSheet(f'color: {CoresUnion.TEXT_MUTED};')
        left_layout.addWidget(self.label_version)
        left_layout.addSpacing(25)
        self.btn_wipe = QPushButton('Wipe Data Reset')
        self.btn_wipe.setFixedSize(170, 40)
        self.btn_wipe.setCursor(Qt.PointingHandCursor)
        self.btn_wipe.setFont(QFont('Segoe UI', 12, QFont.Bold))
        self.btn_wipe.setStyleSheet(f'\n            QPushButton {{ background-color: {CoresUnion.PRIMARY}; color: {CoresUnion.TEXT_WHITE}; border: none; border-radius: 20px; }}\n            QPushButton:hover {{ background-color: {CoresUnion.PRIMARY_HOVER}; }}\n            QPushButton:disabled {{ background-color: {CoresUnion.BORDER}; }}\n        ')
        self.btn_wipe.clicked.connect(self.executar_wipe)
        left_layout.addWidget(self.btn_wipe)
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
        self.label_aviso = QLabel('­ƒº¬ M├│dulo em fase de testes.\n\nÔÜá´©Å ATEN├ç├âO:\nÔÇó Funciona APENAS em aparelhos ANTIGOS\nÔÇó Alguns modelos N├âO s├úo suportados\nÔÇó N├âO remove FRP (apenas Factory Reset)\nÔÇó Requer modo Fastboot\nÔÇó Execute como Administrador')
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
    def executar_wipe(self, usar_fastboot2: bool=False):
        if self.em_execucao:
            return
        tools_path = self._get_tools_path()
        if usar_fastboot2:
            fastboot_path = os.path.join(tools_path, 'fastboot2.exe')
            if not os.path.exists(fastboot_path):
                fastboot_path = os.path.join(tools_path, 'fastboot.exe')
        else:
            fastboot_path = os.path.join(tools_path, 'fastboot.exe')
        empty_file_path = os.path.join(tools_path, '0')
        if not os.path.exists(fastboot_path):
            QMessageBox.critical(self, 'Erro', 'Componente n├úo encontrado!\n\nReinstale o programa ou entre em contato com o suporte.')
            return
        if not os.path.exists(empty_file_path):
            QMessageBox.critical(self, 'Erro', 'Componente n├úo encontrado!\n\nReinstale o programa ou entre em contato com o suporte.')
            return
        reply = QMessageBox.question(self, 'ÔÜá´©Å Aten├º├úo - MDM SPD/MTK', '­ƒº¬ M├ôDULO EM TESTE\n\nÔÜá´©Å IMPORTANTE:\nÔÇó Este m├®todo funciona APENAS em aparelhos ANTIGOS\nÔÇó Motorola com chipset SPD ou MTK antigo\nÔÇó Alguns modelos N├âO s├úo suportados!\nÔÇó N├âO remove FRP (apenas Factory Reset)\n\n­ƒôï Instru├º├Áes:\n1. Desligue o aparelho\n2. Segure Volume - e Power\n3. Entre em modo Fastboot\n4. Conecte o cabo USB\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        self.em_execucao = True
        self.label_status.setText('Aguardando dispositivo em Fastboot...')
        self.label_status.setStyleSheet(f'color: {CoresUnion.TEXT_MUTED};')
        self.label_phone_status.setText('Conecte em modo Fastboot')
        self._start_spinner()
        self.barra_progresso.setValue(5)
        self.worker = FastbootWorker(fastboot_path, empty_file_path)
        self.worker.progress_signal.connect(self.barra_progresso.setValue)
        self.worker.status_signal.connect(self._on_status)
        self.worker.log_signal.connect(self._on_log)
        self.worker.finished_signal.connect(self._on_finished)
        self.btn_wipe.setEnabled(False)
        self.worker.start()
    def _on_log(self, msg: str):
        print(msg)
    def _on_status(self, status: str):
        if status == 'waiting':
            self.label_status.setText('Aguardando dispositivo...')
            self.label_status.setStyleSheet(f'color: {CoresUnion.TEXT_MUTED};')
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
            self.label_phone_status.setText('Wipe Data conclu├¡do! Ô£à')
            return
        if status == 'error':
            self._stop_spinner()
            self._set_phone_image('error')
            self.label_status.setText('Erro no processo')
            self.label_status.setStyleSheet(f'color: {CoresUnion.ERROR};')
            self.label_phone_status.setText('Verifique e tente novamente')
    def _on_finished(self, sucesso: bool, msg: str):
        self.em_execucao = False
        self.btn_wipe.setEnabled(True)
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
                    subprocess.run(['taskkill', '/F', '/IM', 'fastboot.exe'], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                except:
                    pass
            self.em_execucao = False
            self.btn_wipe.setEnabled(True)
            self._stop_spinner()
            self._set_phone_image('notfound')
            self.label_status.setText('Processo interrompido')
            self.label_status.setStyleSheet(f'color: {CoresUnion.WARNING};')
            self.label_phone_status.setText('')
            self.barra_progresso.setValue(0)
