import os
import sys
import subprocess
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QFrame, QMessageBox)
from PyQt5.QtCore import (Qt, QThread, pyqtSignal)
from PyQt5.QtGui import QFont
from ..brom_base import CoresUnion
class FastbootFrpWorker(QThread):
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    def __init__(self, fastboot_path: str, include_userdata: bool=False):
        super().__init__()
        self.fastboot_path = fastboot_path
        self.include_userdata = include_userdata
        self._cancelado = False
    def _log(self, msg: str):
        print(f'[FASTBOOT] {msg}', flush=True)
        self.log_signal.emit(msg)
    def _run_fastboot(self, args: list) -> tuple:
        cmd = [self.fastboot_path] + args
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
            output = result.stdout + result.stderr
            return result.returncode == 0, output.strip()
        except subprocess.TimeoutExpired:
            return (False, 'Timeout - dispositivo n├úo respondeu')
        except Exception as e:
            return False, str(e)
    def run(self):
        try:
            self._log('==================================================')
            self._log('  TECH UNION SOLUTIONS - FRP FASTBOOT')
            self._log('  ÔÜá´©Å BOOTLOADER DESBLOQUEADO OBRIGAT├ôRIO')
            self._log('==================================================')
            self._log('')
            if not os.path.exists(self.fastboot_path):
                self._log('ÔØî fastboot.exe n├úo encontrado!')
                self.finished_signal.emit(False, 'fastboot.exe n├úo encontrado!')
                return
            self._log('Ô£à fastboot.exe encontrado')
            self.progress_signal.emit(10)
            self._log('')
            self._log('­ƒô▒ Verificando dispositivo em modo Fastboot...')
            self.status_signal.emit('checking')
            success, output = self._run_fastboot(['devices'])
            self._log(f'   {output}')
            if not output or 'fastboot' not in output.lower():
                self._log('')
                self._log('ÔØî Nenhum dispositivo em modo Fastboot!')
                self._log('   1. Desligue o aparelho')
                self._log('   2. Segure Volume - e Power')
                self._log('   3. Conecte o cabo USB')
                self.finished_signal.emit(False, 'Nenhum dispositivo em modo Fastboot!\n\n­ƒô▒ Como entrar em Fastboot:\n1. Desligue o aparelho\n2. Segure Volume - e Power\n3. Conecte o cabo USB')
                return
            self._log('Ô£à Dispositivo detectado!')
            self.status_signal.emit('connected')
            self.progress_signal.emit(30)
            self._log('')
            self._log('­ƒöº Apagando parti├º├úo FRP...')
            self.status_signal.emit('erasing_frp')
            success, output = self._run_fastboot(['erase', 'frp'])
            self._log(f'   {output}')
            if not success:
                if 'FAILED' in output.upper():
                    self._log('ÔØî Falha ao apagar FRP!')
                    self._log('   Verifique se o bootloader est├í desbloqueado.')
                    self.finished_signal.emit(False, 'Falha ao apagar FRP!\n\nÔÜá´©Å O bootloader est├í desbloqueado?\nEste m├®todo s├│ funciona com bootloader desbloqueado.')
                    return
            self._log('Ô£à FRP apagado!')
            self.progress_signal.emit(60)
            if self.include_userdata:
                self._log('')
                self._log('­ƒöº Apagando parti├º├úo userdata (Factory Reset)...')
                self.status_signal.emit('erasing_userdata')
                success, output = self._run_fastboot(['erase', 'userdata'])
                self._log(f'   {output}')
                if success or 'Erasing' in output:
                    self._log('Ô£à Userdata apagado!')
                else:
                    self._log('ÔÜá´©Å Aviso: userdata pode n├úo ter sido apagado completamente')
                self.progress_signal.emit(80)
            self._log('')
            self._log('­ƒöä Reiniciando dispositivo...')
            self.status_signal.emit('rebooting')
            success, output = self._run_fastboot(['reboot'])
            self._log(f'   {output}')
            self.progress_signal.emit(100)
            self.status_signal.emit('success')
            self._log('')
            self._log('==================================================')
            self._log('  Ô£à FRP REMOVIDO COM SUCESSO!')
            self._log('==================================================')
            self._log('')
            self._log('­ƒô▒ O dispositivo est├í reiniciando...')
            self._log('­ƒÆí Configure normalmente ap├│s reiniciar!')
            msg = 'FRP removido com sucesso!\n\nO dispositivo est├í reiniciando.'
            if self.include_userdata:
                msg += '\n\nÔÜá´©Å Factory Reset aplicado - todos os dados foram apagados.'
            self.finished_signal.emit(True, msg)
            return
        except Exception as e:
            self._log(f'ÔØî Erro: {str(e)}')
            self.finished_signal.emit(False, str(e))
    def cancelar(self):
        self._cancelado = True
class FastbootFrpWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.em_execucao = False
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.setup_ui()
    def _get_fastboot_path(self) -> str:
        try:
            from app.utils.path_manager import PathManager
            p = PathManager.get_unlock_tool('fastboot.exe')
            if p and os.path.isfile(p):
                return p
        except Exception:
            pass
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(base, 'tools', 'fastboot.exe')
    def setup_ui(self):
        self.setStyleSheet(f'background-color: {CoresUnion.BACKGROUND};')
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(15)
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(5)
        title = QLabel('Xiaomi | FRP Fastboot')
        title.setFont(QFont('Segoe UI', 24, QFont.Bold))
        title.setStyleSheet(f'color: {CoresUnion.TEXT};')
        header_layout.addWidget(title)
        subtitle = QLabel('Todos os modelos com Bootloader Desbloqueado')
        subtitle.setFont(QFont('Segoe UI', 12))
        subtitle.setStyleSheet(f'color: {CoresUnion.TEXT_MUTED};')
        header_layout.addWidget(subtitle)
        main_layout.addWidget(header)
        aviso_frame = QFrame()
        aviso_frame.setStyleSheet(f'\n            QFrame {{\n                background-color: #FFF3E0;\n                border: 2px solid {CoresUnion.WARNING};\n                border-radius: 10px;\n                padding: 15px;\n            }}\n        ')
        aviso_layout = QVBoxLayout(aviso_frame)
        aviso_layout.setSpacing(8)
        aviso_title = QLabel('ÔÜá´©Å REQUISITO OBRIGAT├ôRIO')
        aviso_title.setFont(QFont('Segoe UI', 14, QFont.Bold))
        aviso_title.setStyleSheet(f'color: {CoresUnion.WARNING}; background: transparent;')
        aviso_layout.addWidget(aviso_title)
        aviso_text = QLabel('Este m├®todo SOMENTE funciona em dispositivos com BOOTLOADER DESBLOQUEADO.\n\nComo saber se o bootloader est├í desbloqueado?\nAo ligar o aparelho, se aparecer um cadeado ABERTO na parte superior\nda tela, significa que o bootloader est├í desbloqueado.\n\nSe o bootloader estiver bloqueado, use outro m├®todo (BROM, EDL, etc.)')
        aviso_text.setFont(QFont('Segoe UI', 10))
        aviso_text.setStyleSheet(f'color: {CoresUnion.TEXT}; background: transparent;')
        aviso_text.setWordWrap(True)
        aviso_layout.addWidget(aviso_text)
        main_layout.addWidget(aviso_frame)
        instrucoes = QLabel("­ƒô▒ Como entrar em modo Fastboot:\n   1. Desligue o aparelho completamente\n   2. Segure Volume - (menos) e Power juntos\n   3. Conecte o cabo USB quando aparecer 'FASTBOOT'")
        instrucoes.setFont(QFont('Segoe UI', 11))
        instrucoes.setStyleSheet(f'color: {CoresUnion.TEXT_MUTED}; padding: 10px;')
        main_layout.addWidget(instrucoes)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        self.btn_frp = QPushButton('Remover FRP')
        self.btn_frp.setMinimumHeight(45)
        self.btn_frp.setMaximumWidth(200)
        self.btn_frp.setCursor(Qt.PointingHandCursor)
        self.btn_frp.setFont(QFont('Segoe UI', 11, QFont.Bold))
        self.btn_frp.setStyleSheet(f'\n            QPushButton {{\n                background-color: {CoresUnion.PRIMARY};\n                color: white;\n                border: none;\n                border-radius: 22px;\n                padding: 10px 25px;\n            }}\n            QPushButton:hover {{ background-color: {CoresUnion.PRIMARY_HOVER}; }}\n            QPushButton:disabled {{ background-color: {CoresUnion.BORDER}; }}\n        ')
        self.btn_frp.clicked.connect((lambda: self.executar(False)))
        btn_layout.addWidget(self.btn_frp)
        self.btn_factory = QPushButton('FRP + Factory Reset')
        self.btn_factory.setMinimumHeight(45)
        self.btn_factory.setMaximumWidth(220)
        self.btn_factory.setCursor(Qt.PointingHandCursor)
        self.btn_factory.setFont(QFont('Segoe UI', 11, QFont.Bold))
        self.btn_factory.setStyleSheet(f'\n            QPushButton {{\n                background-color: {CoresUnion.ERROR};\n                color: white;\n                border: none;\n                border-radius: 22px;\n                padding: 10px 25px;\n            }}\n            QPushButton:hover {{ background-color: #c0392b; }}\n            QPushButton:disabled {{ background-color: {CoresUnion.BORDER}; }}\n        ')
        self.btn_factory.clicked.connect((lambda: self.executar(True)))
        btn_layout.addWidget(self.btn_factory)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(15)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f'\n            QProgressBar {{\n                border: 1px solid {CoresUnion.BORDER};\n                border-radius: 7px;\n                background-color: {CoresUnion.BACKGROUND_WHITE};\n            }}\n            QProgressBar::chunk {{\n                background-color: {CoresUnion.PRIMARY};\n                border-radius: 6px;\n            }}\n        ')
        main_layout.addWidget(self.progress_bar)
        self.label_status = QLabel('Pronto para iniciar')
        self.label_status.setFont(QFont('Segoe UI', 12))
        self.label_status.setStyleSheet(f'color: {CoresUnion.TEXT_MUTED};')
        main_layout.addWidget(self.label_status)
        main_layout.addStretch()
    def executar(self, include_userdata: bool):
        if self.em_execucao:
            return
        fastboot_path = self._get_fastboot_path()
        if not os.path.exists(fastboot_path):
            QMessageBox.critical(self, 'Erro', 'fastboot.exe n├úo encontrado!')
            return
        if include_userdata:
            msg = 'ÔÜá´©Å ATEN├ç├âO: FACTORY RESET\n\nIsso ir├í:\nÔÇó Remover o bloqueio FRP\nÔÇó APAGAR TODOS OS DADOS do dispositivo\n\nÔÜá´©Å REQUISITO: Bootloader Desbloqueado\n\nContinuar?'
        else:
            msg = 'Remover FRP do dispositivo?\n\nÔÜá´©Å REQUISITO: Bootloader Desbloqueado\n\n­ƒô▒ Certifique-se que o dispositivo est├í em modo Fastboot.\n\nContinuar?'
        reply = QMessageBox.question(self, 'Confirmar', msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        self.em_execucao = True
        self.btn_frp.setEnabled(False)
        self.btn_factory.setEnabled(False)
        self.progress_bar.setValue(0)
        self.label_status.setText('Iniciando...')
        self.label_status.setStyleSheet(f'color: {CoresUnion.PRIMARY};')
        self.worker = FastbootFrpWorker(fastboot_path, include_userdata)
        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.status_signal.connect(self._on_status)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()
    def _on_status(self, status: str):
        status_msgs = {'checking': 'Verificando dispositivo...', 'connected': 'Dispositivo conectado!', 'erasing_frp': 'Apagando FRP...', 'erasing_userdata': 'Apagando dados (Factory Reset)...', 'rebooting': 'Reiniciando dispositivo...', 'success': 'Conclu├¡do com sucesso!'}
        self.label_status.setText(status_msgs.get(status, status))
        if status == 'success':
            self.label_status.setStyleSheet(f'color: {CoresUnion.SUCCESS};')
            return
        if status == 'connected':
            self.label_status.setStyleSheet(f'color: {CoresUnion.PRIMARY};')
    def _on_finished(self, sucesso: bool, msg: str):
        self.em_execucao = False
        self.btn_frp.setEnabled(True)
        self.btn_factory.setEnabled(True)
        if sucesso:
            self.label_status.setText('Ô£à FRP removido com sucesso!')
            self.label_status.setStyleSheet(f'color: {CoresUnion.SUCCESS};')
            self.progress_bar.setValue(100)
            QMessageBox.information(self, 'Sucesso', msg)
            return
        self.label_status.setText('ÔØî Erro')
        self.label_status.setStyleSheet(f'color: {CoresUnion.ERROR};')
        self.progress_bar.setValue(0)
        QMessageBox.critical(self, 'Erro', msg)
