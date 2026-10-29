from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QGroupBox, QGridLayout, QSplitter, QApplication, QListWidget, QListWidgetItem, QMenu, QMessageBox, QFrame, QScrollArea, QFileDialog, QInputDialog, QDialog, QLineEdit, QTabWidget, QCheckBox, QProgressBar, QTreeWidget, QTreeWidgetItem, QHeaderView, QRadioButton, QButtonGroup, QSizePolicy)
from PyQt5.QtCore import (Qt, QTimer, QUrl, QThread, pyqtSignal)
from PyQt5.QtGui import (QIcon, QCursor, QDesktopServices, QFont, QPixmap, QColor)
from app.utils.adb_manager import ADBManager
from app.utils.tools_android import AndroidTools
from app.utils.path_manager import PathManager
import os
import time
import threading
import logging
import xml.etree.ElementTree as ET
try:
    from app.views.union_unlock.flash.motorola.motorola_flash_gui import MotorolaFlashToolWidget
    MOTOROLA_FLASH_AVAILABLE = True
except ImportError:
    MOTOROLA_FLASH_AVAILABLE = False
class UnlockDialog(QDialog):
    def __init__(self, tools, parent=None):
        super().__init__(parent)
        self.tools = tools
        self.setup_ui()
    def setup_ui(self):
        self.setWindowTitle('Desbloqueio do Bootloader Motorola')
        self.setMinimumWidth(600)
        layout = QVBoxLayout(self)
        instructions = QLabel("Processo de Desbloqueio do Bootloader:\n\n1. Clique em 'Obter C├│digo' para gerar o c├│digo ├║nico do dispositivo\n2. Copie o c├│digo e acesse o site oficial da Motorola\n3. Cole o c├│digo no site e solicite o desbloqueio\n4. Voc├¬ receber├í um email com o token de desbloqueio\n5. Cole o token recebido abaixo e clique em 'Desbloquear'\n")
        instructions.setStyleSheet('font-size: 12px; margin: 10px;')
        layout.addWidget(instructions)
        device_frame = QFrame()
        device_frame.setStyleSheet('\n            QFrame {\n                background-color: #f5f5f5;\n                border-radius: 5px;\n                padding: 10px;\n            }\n        ')
        device_layout = QVBoxLayout(device_frame)
        self.device_code = QLineEdit()
        self.device_code.setReadOnly(True)
        self.device_code.setPlaceholderText('O c├│digo do dispositivo aparecer├í aqui...')
        self.device_code.setStyleSheet('\n            QLineEdit {\n                padding: 8px;\n                font-family: monospace;\n                font-size: 14px;\n                background: white;\n                border: 1px solid #ddd;\n                border-radius: 4px;\n            }\n        ')
        device_layout.addWidget(self.device_code)
        device_buttons = QHBoxLayout()
        get_code_btn = QPushButton('Obter C├│digo')
        get_code_btn.clicked.connect(self.get_device_code)
        device_buttons.addWidget(get_code_btn)
        copy_code_btn = QPushButton('Copiar C├│digo')
        copy_code_btn.clicked.connect((lambda: self.copy_to_clipboard(self.device_code.text())))
        device_buttons.addWidget(copy_code_btn)
        open_site_btn = QPushButton('Abrir Site Motorola')
        open_site_btn.clicked.connect(self.open_unlock_portal)
        device_buttons.addWidget(open_site_btn)
        device_layout.addLayout(device_buttons)
        layout.addWidget(device_frame)
        unlock_frame = QFrame()
        unlock_frame.setStyleSheet('\n            QFrame {\n                background-color: #f5f5f5;\n                border-radius: 5px;\n                padding: 10px;\n                margin-top: 10px;\n            }\n        ')
        unlock_layout = QVBoxLayout(unlock_frame)
        self.unlock_token = QLineEdit()
        self.unlock_token.setPlaceholderText('Cole aqui o token recebido por email...')
        self.unlock_token.setStyleSheet('\n            QLineEdit {\n                padding: 8px;\n                font-family: monospace;\n                font-size: 14px;\n                background: white;\n                border: 1px solid #ddd;\n                border-radius: 4px;\n            }\n        ')
        unlock_layout.addWidget(self.unlock_token)
        unlock_btn = QPushButton('Desbloquear Bootloader')
        unlock_btn.clicked.connect(self.unlock_bootloader)
        unlock_layout.addWidget(unlock_btn)
        layout.addWidget(unlock_frame)
    def get_device_code(self):
        '''Obt├®m o c├│digo ├║nico do dispositivo'''
        try:
            if not self.tools.adb.check_fastboot_device():
                QMessageBox.warning(self, 'Modo Fastboot Necess├írio', 'O dispositivo precisa estar em modo fastboot!\n\n1. Desligue o dispositivo\n2. Pressione Vol- + Power at├® entrar em fastboot')
                return
            result = self.tools.get_unlock_data()
            if 'Ô£à' in result:
                code = result.split(':')[-1].strip()
                self.device_code.setText(code)
                QMessageBox.information(self, 'C├│digo Obtido', 'C├│digo obtido com sucesso!\n1. Copie o c├│digo\n2. Acesse o site da Motorola\n3. Aguarde o email com o token')
                return
            QMessageBox.warning(self, 'Erro', result)
            return
        except Exception as e:
            import logging
            logging.getLogger(__name__).error('UnlockDialog erro ao obter codigo: %s', e)
            QMessageBox.critical(self, 'Erro', 'Falha na operacao. Verifique a conexao com o dispositivo.')
    def copy_to_clipboard(self, text):
        '''Copia texto para a ├írea de transfer├¬ncia'''
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            QMessageBox.information(self, 'Copiado', 'C├│digo copiado para a ├írea de transfer├¬ncia!')
            return
        QMessageBox.warning(self, 'Erro', 'Obtenha o c├│digo do dispositivo primeiro!')
    def open_unlock_portal(self):
        '''Abre o site oficial de unlock da Motorola'''
        url = 'https://en-us.support.motorola.com/app/standalone/bootloader/unlock-your-device-c'
        QDesktopServices.openUrl(QUrl(url))
    def unlock_bootloader(self):
        '''Executa o desbloqueio com o token fornecido'''
        token = self.unlock_token.text().strip()
        if not token:
            QMessageBox.warning(self, 'Token Necess├írio', 'Por favor, insira o token recebido por email!')
            return
        try:
            if not self.tools.adb.check_fastboot_device():
                QMessageBox.warning(self, 'Modo Fastboot Necess├írio', 'O dispositivo precisa estar em modo fastboot!')
                return
            reply = QMessageBox.warning(self, 'ATEN├ç├âO', 'O desbloqueio do bootloader ir├í:\n\n1. APAGAR TODOS OS DADOS do dispositivo\n2. Pode invalidar a garantia\n3. ├ë um processo irrevers├¡vel\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                result = self.tools.unlock_bootloader(token)
                if 'Ô£à' in result:
                    QMessageBox.information(self, 'Sucesso', 'Bootloader desbloqueado com sucesso!\nO dispositivo ser├í reiniciado.')
                    self.accept()
                    return
                QMessageBox.warning(self, 'Erro', result)
                return
        except Exception as e:
            import logging
            logging.getLogger(__name__).error('UnlockDialog erro ao desbloquear: %s', e)
            QMessageBox.critical(self, 'Erro', 'Falha no desbloqueio. Verifique a conexao com o dispositivo.')
class FlashRomDialog(QDialog):
    '''
    [LEGACY - DESATIVADO]
    Dialog avan├ºado para flash de ROM com an├ílise de parti├º├Áes
    Substitu├¡do pelo m├│dulo: app/views/union_unlock/flash/motorola/
    '''
    def __init__(self, tools, parent=None):
        super().__init__(parent)
        self.tools = tools
        self.adb = tools.adb
        self.device_has_ab = False
        self.xml_data = None
        self.selected_partitions = []
        self.flash_type = 'wipe'
        self._showing = False
        self.setup_ui()
    def setup_ui(self):
        '''Configura a interface do dialog'''
        self.setWindowTitle('­ƒöÑ Flash ROM - Motorola')
        self.setModal(True)
        self.setWindowState(Qt.WindowMaximized)
        self.resize(1920, 1080)
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(6, 6, 6, 6)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        header_layout.setContentsMargins(0, 0, 0, 0)
        back_btn = QPushButton('ÔåÉ Voltar')
        back_btn.setStyleSheet('\n            QPushButton {\n                background-color: #34495e;\n                color: white;\n                font-weight: bold;\n                padding: 6px 16px;\n                border-radius: 4px;\n                min-width: 80px;\n                border: none;\n                font-size: 11px;\n                max-height: 24px;\n                min-height: 24px;\n            }\n            QPushButton:hover {\n                background-color: #2c3e50;\n                transform: translateY(-1px);\n            }\n            QPushButton:pressed {\n                background-color: #1a252f;\n            }\n        ')
        back_btn.clicked.connect(self.reject)
        header_layout.addWidget(back_btn)
        title = QLabel('­ƒöÑ Flash ROM - Motorola')
        title.setStyleSheet('\n            QLabel {\n                font-size: 14px; \n                font-weight: bold; \n                color: #2c3e50; \n                margin: 0px;\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,\n                    stop:0 rgba(52,152,219,0.06), stop:1 rgba(155,89,182,0.06));\n                border-radius: 4px;\n                padding: 2px 12px;\n                border: 1px solid rgba(52,152,219,0.15);\n                max-height: 24px;\n                min-height: 24px;\n            }\n        ')
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        risk_warning = QLabel('ÔÜá´©Å FUNCIONALIDADE TESTADA EM DESENVOLVIMENTO: O flash ROM pode apresentar riscos. Testado em diversos Motorola com sucesso, mas recomendamos backup completo. Uso por sua conta e risco. N├úo nos responsabilizamos por eventuais danos.')
        risk_warning.setStyleSheet('\n            QLabel {\n                color: #d32f2f;\n                font-weight: bold;\n                font-size: 10px;\n                padding: 3px 8px;\n                background: rgba(211, 47, 47, 0.08);\n                border: 1px solid rgba(211, 47, 47, 0.3);\n                border-radius: 3px;\n                margin: 1px;\n                max-height: 20px;\n                min-height: 20px;\n            }\n        ')
        risk_warning.setWordWrap(False)
        risk_warning.setAlignment(Qt.AlignCenter)
        layout.addWidget(risk_warning)
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        left_frame = QFrame()
        left_frame.setStyleSheet('\n            QFrame {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #f8f9fa, stop:1 #e9ecef);\n                border-radius: 10px;\n                border: 1px solid #dee2e6;\n            }\n        ')
        left_layout = QVBoxLayout(left_frame)
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(15, 15, 15, 15)
        flash_group = QGroupBox()
        flash_group.setStyleSheet('\n            QGroupBox {\n                font-weight: bold;\n                font-size: 14px;\n                color: #2c3e50;\n                border: 2px solid #3498db;\n                border-radius: 8px;\n                margin-top: 10px;\n                padding-top: 10px;\n                background-color: white;\n            }\n            QGroupBox::title {\n                subcontrol-origin: margin;\n                left: 15px;\n                padding: 0 10px 0 10px;\n                background-color: white;\n                color: #3498db;\n            }\n        ')
        flash_group.setTitle('­ƒöº Tipo de Flash')
        flash_layout = QVBoxLayout(flash_group)
        flash_layout.setSpacing(8)
        flash_layout.setContentsMargins(12, 15, 12, 12)
        self.flash_button_group = QButtonGroup(self)
        self.wipe_radio = QRadioButton('­ƒöÑ Flash com WIPE (flashfile.xml)')
        self.wipe_radio.setStyleSheet('\n            QRadioButton {\n                font-size: 13px;\n                color: #2c3e50;\n                spacing: 8px;\n                padding: 5px;\n            }\n            QRadioButton::indicator {\n                width: 18px;\n                height: 18px;\n            }\n            QRadioButton::indicator:checked {\n                image: none;\n                background-color: #e74c3c;\n                border: 3px solid white;\n                border-radius: 9px;\n                outline: 2px solid #e74c3c;\n            }\n            QRadioButton::indicator:unchecked {\n                background-color: white;\n                border: 2px solid #bdc3c7;\n                border-radius: 9px;\n            }\n        ')
        self.wipe_radio.setToolTip('ÔÜá´©Å Apaga TODOS os dados (factory reset) - Recomendado para problemas graves')
        self.wipe_radio.setChecked(True)
        self.flash_button_group.addButton(self.wipe_radio)
        flash_layout.addWidget(self.wipe_radio)
        self.no_wipe_radio = QRadioButton('­ƒÆ¥ Flash sem WIPE (servicefile.xml)')
        self.no_wipe_radio.setStyleSheet('\n            QRadioButton {\n                font-size: 13px;\n                color: #2c3e50;\n                spacing: 8px;\n                padding: 5px;\n            }\n            QRadioButton::indicator {\n                width: 18px;\n                height: 18px;\n            }\n            QRadioButton::indicator:checked {\n                image: none;\n                background-color: #27ae60;\n                border: 3px solid white;\n                border-radius: 9px;\n                outline: 2px solid #27ae60;\n            }\n            QRadioButton::indicator:unchecked {\n                background-color: white;\n                border: 2px solid #bdc3c7;\n                border-radius: 9px;\n            }\n        ')
        self.no_wipe_radio.setToolTip('­ƒÆí Mant├®m dados do usu├írio - Para atualiza├º├Áes ou corre├º├Áes leves')
        self.flash_button_group.addButton(self.no_wipe_radio)
        flash_layout.addWidget(self.no_wipe_radio)
        self.wipe_radio.toggled.connect((lambda: setattr(self, 'flash_type', 'wipe')))
        self.no_wipe_radio.toggled.connect((lambda: setattr(self, 'flash_type', 'no-wipe')))
        left_layout.addWidget(flash_group)
        file_group = QGroupBox()
        file_group.setStyleSheet('\n            QGroupBox {\n                font-weight: bold;\n                font-size: 14px;\n                color: #2c3e50;\n                border: 2px solid #9b59b6;\n                border-radius: 8px;\n                margin-top: 10px;\n                padding-top: 10px;\n                background-color: white;\n            }\n            QGroupBox::title {\n                subcontrol-origin: margin;\n                left: 15px;\n                padding: 0 10px 0 10px;\n                background-color: white;\n                color: #9b59b6;\n            }\n        ')
        file_group.setTitle('­ƒôü Arquivo de Firmware')
        file_layout = QVBoxLayout(file_group)
        file_layout.setSpacing(8)
        file_layout.setContentsMargins(12, 15, 12, 12)
        self.file_label = QLabel('­ƒôä Nenhum arquivo selecionado')
        self.file_label.setStyleSheet('\n            QLabel {\n                color: #7f8c8d; \n                font-style: italic;\n                font-size: 12px;\n                padding: 8px;\n                background-color: #f8f9fa;\n                border-radius: 4px;\n                border: 1px dashed #bdc3c7;\n            }\n        ')
        file_layout.addWidget(self.file_label)
        file_buttons = QHBoxLayout()
        file_buttons.setSpacing(8)
        self.select_xml_btn = QPushButton('­ƒôï XML')
        self.select_xml_btn.setStyleSheet('\n            QPushButton {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #3498db, stop:1 #2980b9);\n                color: white;\n                font-weight: bold;\n                padding: 8px 12px;\n                border-radius: 6px;\n                border: none;\n                font-size: 11px;\n            }\n            QPushButton:hover {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #5dade2, stop:1 #3498db);\n            }\n            QPushButton:pressed {\n                background: #2471a3;\n            }\n        ')
        self.select_xml_btn.setToolTip('­ƒôï Selecione flashfile.xml ou servicefile.xml')
        self.select_xml_btn.clicked.connect(self.select_xml_file)
        file_buttons.addWidget(self.select_xml_btn)
        self.select_firmware_btn = QPushButton('­ƒôé Pasta')
        self.select_firmware_btn.setStyleSheet('\n            QPushButton {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #9b59b6, stop:1 #8e44ad);\n                color: white;\n                font-weight: bold;\n                padding: 8px 12px;\n                border-radius: 6px;\n                border: none;\n                font-size: 11px;\n            }\n            QPushButton:hover {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #bb8fce, stop:1 #9b59b6);\n            }\n            QPushButton:pressed {\n                background: #6c3483;\n            }\n        ')
        self.select_firmware_btn.setToolTip('­ƒôé Selecione a pasta com todos os arquivos da firmware')
        self.select_firmware_btn.clicked.connect(self.select_firmware_folder)
        file_buttons.addWidget(self.select_firmware_btn)
        file_layout.addLayout(file_buttons)
        left_layout.addWidget(file_group)
        device_group = QGroupBox()
        device_group.setStyleSheet('\n            QGroupBox {\n                font-weight: bold;\n                font-size: 14px;\n                color: #2c3e50;\n                border: 2px solid #16a085;\n                border-radius: 8px;\n                margin-top: 10px;\n                padding-top: 10px;\n                background-color: white;\n            }\n            QGroupBox::title {\n                subcontrol-origin: margin;\n                left: 15px;\n                padding: 0 10px 0 10px;\n                background-color: white;\n                color: #16a085;\n            }\n        ')
        device_group.setTitle('­ƒô▒ Status do Dispositivo')
        device_layout = QVBoxLayout(device_group)
        device_layout.setSpacing(8)
        device_layout.setContentsMargins(12, 15, 12, 12)
        self.device_status = QLabel('­ƒöì Verificando...')
        self.device_status.setStyleSheet('\n            QLabel {\n                font-weight: bold;\n                font-size: 13px;\n                color: #34495e;\n                padding: 10px;\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,\n                    stop:0 #ecf0f1, stop:1 #bdc3c7);\n                border-radius: 6px;\n                border: 1px solid #95a5a6;\n            }\n        ')
        device_layout.addWidget(self.device_status)
        self.check_device_btn = QPushButton('­ƒöì Verificar Dispositivo')
        self.check_device_btn.setStyleSheet('\n            QPushButton {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #16a085, stop:1 #138d75);\n                color: white;\n                font-weight: bold;\n                padding: 10px 15px;\n                border-radius: 6px;\n                border: none;\n                font-size: 12px;\n            }\n            QPushButton:hover {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #48c9b0, stop:1 #16a085);\n            }\n            QPushButton:pressed {\n                background: #117a65;\n            }\n        ')
        self.check_device_btn.clicked.connect(self.check_device_status)
        device_layout.addWidget(self.check_device_btn)
        left_layout.addWidget(device_group)
        action_buttons = QHBoxLayout()
        action_buttons.setSpacing(8)
        action_buttons.setContentsMargins(0, 8, 0, 0)
        self.flash_btn = QPushButton('­ƒÜÇ INICIAR FLASH')
        self.flash_btn.setStyleSheet('\n            QPushButton {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #e74c3c, stop:1 #c0392b);\n                color: white;\n                font-weight: bold;\n                font-size: 12px;\n                padding: 8px 15px;\n                border-radius: 6px;\n                border: none;\n                min-height: 32px;\n            }\n            QPushButton:hover {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #ec7063, stop:1 #e74c3c);\n                transform: translateY(-2px);\n            }\n            QPushButton:pressed {\n                background: #a93226;\n                transform: translateY(0px);\n            }\n            QPushButton:disabled {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #bdc3c7, stop:1 #95a5a6);\n                color: #7f8c8d;\n            }\n        ')
        self.flash_btn.setEnabled(False)
        self.flash_btn.clicked.connect(self.start_flash)
        action_buttons.addWidget(self.flash_btn)
        close_btn = QPushButton('ÔØî Fechar')
        close_btn.setStyleSheet('\n            QPushButton {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #95a5a6, stop:1 #7f8c8d);\n                color: white;\n                font-weight: bold;\n                font-size: 11px;\n                padding: 8px 12px;\n                border-radius: 6px;\n                border: none;\n                min-height: 32px;\n            }\n            QPushButton:hover {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #aab7b8, stop:1 #95a5a6);\n            }\n            QPushButton:pressed {\n                background: #566573;\n            }\n        ')
        close_btn.clicked.connect(self.reject)
        action_buttons.addWidget(close_btn)
        left_layout.addLayout(action_buttons)
        left_layout.addStretch()
        splitter.addWidget(left_frame)
        right_frame = QFrame()
        right_frame.setStyleSheet('\n            QFrame {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #ffffff, stop:1 #f8f9fa);\n                border-radius: 10px;\n                border: 1px solid #dee2e6;\n            }\n        ')
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(10, 10, 10, 10)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet('\n            QTabWidget::pane {\n                border: 2px solid #3498db;\n                border-radius: 8px;\n                background-color: white;\n                margin-top: 5px;\n            }\n            QTabWidget::tab-bar {\n                alignment: center;\n            }\n            QTabBar::tab {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #ecf0f1, stop:1 #bdc3c7);\n                color: #2c3e50;\n                padding: 10px 20px;\n                margin-right: 2px;\n                border-radius: 6px 6px 0 0;\n                font-weight: bold;\n                font-size: 12px;\n            }\n            QTabBar::tab:selected {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #3498db, stop:1 #2980b9);\n                color: white;\n            }\n            QTabBar::tab:hover {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #85c1e9, stop:1 #5dade2);\n                color: white;\n            }\n        ')
        partitions_widget = QWidget()
        partitions_layout = QVBoxLayout(partitions_widget)
        partitions_header = QLabel('­ƒùé´©Å Parti├º├Áes a serem flasheadas:')
        partitions_header.setStyleSheet('font-weight: bold; margin-bottom: 5px;')
        partitions_layout.addWidget(partitions_header)
        self.selection_counter = QLabel('­ƒôè 0 parti├º├Áes selecionadas')
        self.selection_counter.setStyleSheet('\n            QLabel {\n                color: #7f8c8d;\n                font-size: 11px;\n                font-style: italic;\n                padding: 2px 5px;\n                background-color: rgba(52,152,219,0.1);\n                border-radius: 3px;\n                margin-bottom: 3px;\n            }\n        ')
        partitions_layout.addWidget(self.selection_counter)
        self.partitions_tree = QTreeWidget()
        self.partitions_tree.setHeaderLabels(['Parti├º├úo', 'Arquivo', 'Tamanho', 'A├º├úo'])
        self.partitions_tree.header().setStretchLastSection(False)
        self.partitions_tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.partitions_tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.partitions_tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.partitions_tree.header().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.partitions_tree.itemChanged.connect(self.on_partition_selection_changed)
        partitions_layout.addWidget(self.partitions_tree)
        partition_controls = QHBoxLayout()
        partition_controls.setSpacing(8)
        self.select_all_btn = QPushButton('Ô£à Todas')
        self.select_all_btn.setStyleSheet('\n            QPushButton {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #27ae60, stop:1 #229954);\n                color: white;\n                font-weight: bold;\n                padding: 6px 12px;\n                border-radius: 4px;\n                border: none;\n                font-size: 10px;\n            }\n            QPushButton:hover {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #58d68d, stop:1 #27ae60);\n            }\n        ')
        self.select_all_btn.clicked.connect(self.select_all_partitions)
        partition_controls.addWidget(self.select_all_btn)
        self.select_essential_btn = QPushButton('ÔÜí Essenciais')
        self.select_essential_btn.setStyleSheet('\n            QPushButton {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #f39c12, stop:1 #e67e22);\n                color: white;\n                font-weight: bold;\n                padding: 6px 12px;\n                border-radius: 4px;\n                border: none;\n                font-size: 10px;\n            }\n            QPushButton:hover {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #f8c471, stop:1 #f39c12);\n            }\n        ')
        self.select_essential_btn.clicked.connect(self.select_essential_partitions)
        self.select_essential_btn.setToolTip('Seleciona apenas parti├º├Áes cr├¡ticas (boot, system, recovery)')
        partition_controls.addWidget(self.select_essential_btn)
        self.deselect_all_btn = QPushButton('ÔØî Nenhuma')
        self.deselect_all_btn.setStyleSheet('\n            QPushButton {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #e74c3c, stop:1 #c0392b);\n                color: white;\n                font-weight: bold;\n                padding: 6px 12px;\n                border-radius: 4px;\n                border: none;\n                font-size: 10px;\n            }\n            QPushButton:hover {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #ec7063, stop:1 #e74c3c);\n            }\n        ')
        self.deselect_all_btn.clicked.connect(self.deselect_all_partitions)
        partition_controls.addWidget(self.deselect_all_btn)
        partitions_layout.addLayout(partition_controls)
        self.tabs.addTab(partitions_widget, '­ƒôï Parti├º├Áes')
        progress_widget = QWidget()
        progress_layout = QVBoxLayout(progress_widget)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet('\n            QProgressBar {\n                border: 2px solid #3498db;\n                border-radius: 8px;\n                text-align: center;\n                font-weight: bold;\n                font-size: 12px;\n                color: black;\n                background-color: #ecf0f1;\n                min-height: 25px;\n            }\n            QProgressBar::chunk {\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,\n                    stop:0 #e74c3c, stop:0.5 #f39c12, stop:1 #27ae60);\n                border-radius: 6px;\n                margin: 1px;\n            }\n        ')
        self.progress_bar.setFormat('­ƒöÑ Processando: %p% conclu├¡do')
        progress_layout.addWidget(self.progress_bar)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("\n            QTextEdit {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #1e1e1e, stop:1 #2c3e50);\n                color: #00ff00;\n                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;\n                font-size: 12px;\n                font-weight: 500;\n                border-radius: 8px;\n                border: 2px solid #34495e;\n                padding: 10px;\n                selection-background-color: #3498db;\n            }\n            QScrollBar:vertical {\n                background-color: #34495e;\n                width: 12px;\n                border-radius: 6px;\n            }\n            QScrollBar::handle:vertical {\n                background-color: #5dade2;\n                border-radius: 6px;\n                min-height: 20px;\n            }\n            QScrollBar::handle:vertical:hover {\n                background-color: #85c1e9;\n            }\n        ")
        self.log_text.setHtml("\n            <div style='color: #3498db; font-weight: bold; margin-bottom: 8px; text-align: center;'>\n                ­ƒöÑ ÔòÉÔòÉÔòÉ UNION FLASH SYSTEM v1.3 ÔòÉÔòÉÔòÉ\n            </div>\n            <div style='color: #f39c12; font-size: 11px; margin-bottom: 5px;'>\n                Ô£¿ Sistema Flash Profissional para Motorola\n            </div>\n            <div style='color: #95a5a6; font-size: 10px;'>\n                ­ƒôï Status: Aguardando sele├º├úo de firmware...<br/>\n                ­ƒÆí Dica: Selecione um arquivo XML ou pasta firmware para come├ºar\n            </div>\n            <div style='color: #2ecc71; font-size: 10px; margin-top: 8px;'>\n                ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ\n            </div>\n        ")
        progress_layout.addWidget(self.log_text)
        self.tabs.addTab(progress_widget, '­ƒôè Progresso')
        right_layout.addWidget(self.tabs)
        splitter.addWidget(right_frame)
        splitter.setSizes([450, 1050])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        footer = QLabel('­ƒÆí UNION v1.3 - Sistema Flash Profissional')
        footer.setStyleSheet('\n            QLabel {\n                color: #7f8c8d;\n                font-size: 10px;\n                padding: 1px 4px;\n                text-align: center;\n                background-color: rgba(0,0,0,0.02);\n                border-radius: 1px;\n                margin-top: 1px;\n                max-height: 16px;\n                min-height: 16px;\n            }\n        ')
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)
    def showEvent(self, event):
        '''Chamado quando a janela ├® mostrada'''
        super().showEvent(event)
        self.setWindowState(Qt.WindowMaximized)
        self.showMaximized()
        if not self._showing:
            self._showing = True
            self.log_text.append('============================================================')
            self.log_text.append('­ƒöÑ Sistema Flash Profissional para Motorola')
            self.log_text.append('­ƒôï Status: Aguardando sele├º├úo de firmware...')
            self.log_text.append('­ƒÆí Dica: Selecione um arquivo XML ou pasta firmware para come├ºar')
            self.log_text.append('============================================================')
            self.log_text.append('')
            self.log_text.append('­ƒøí´©Å SISTEMA DE PROTE├ç├âO A/B ATIVADO:')
            self.log_text.append('Ô£à Detec├º├úo autom├ítica de slots A/B')
            self.log_text.append('Ô£à Flash no slot INATIVO (mant├®m backup seguro)')
            self.log_text.append('Ô£à Remo├º├úo autom├ítica de parti├º├Áes duplicadas')
            self.log_text.append('Ô£à Copy Partitions para componentes cr├¡ticos')
            self.log_text.append('Ô£à Ativa├º├úo segura do novo slot')
            self.log_text.append('Ô£à Prote├º├úo contra downgrade de bootloader/modem')
            self.log_text.append('')
            self.log_text.append('­ƒôÜ BASEADO NAS MELHORES PR├üTICAS:')
            self.log_text.append('ÔÇó Android AOSP A/B Update Documentation')
            self.log_text.append('ÔÇó Motorola-specific slot management')
            self.log_text.append('ÔÇó Copy Partitions (anti-brick protection)')
            self.log_text.append('ÔÇó Fastboot slot control commands')
            self.log_text.append('')
    def select_xml_file(self):
        '''Seleciona arquivo XML (flashfile.xml ou servicefile.xml)'''
        file_filter = 'XML Files (*.xml);;All Files (*)'
        file_path, _ = QFileDialog.getOpenFileName(self, 'Selecionar arquivo XML', '', file_filter)
        if file_path:
            self.parse_xml_file(file_path)
    def select_firmware_folder(self):
        '''Seleciona pasta da firmware'''
        folder_path = QFileDialog.getExistingDirectory(self, 'Selecionar pasta da firmware')
        if folder_path:
            xml_files = []
            for file in os.listdir(folder_path):
                if file.endswith('.xml') and ('flashfile' in file.lower() or 'servicefile' in file.lower()):
                    xml_files.append(os.path.join(folder_path, file))
            if xml_files:
                if len(xml_files) == 1:
                    self.parse_xml_file(xml_files[0])
                    return
                items = [os.path.basename(f) for f in xml_files]
                from PyQt5.QtWidgets import QInputDialog
                item, ok = QInputDialog.getItem(self, 'Selecionar XML', 'Escolha o arquivo XML:', items, 0, False)
                if ok:
                    if item:
                        selected_xml = xml_files[items.index(item)]
                        self.parse_xml_file(selected_xml)
                        return
                    return
                return
            QMessageBox.warning(self, 'Aviso', 'Nenhum arquivo XML encontrado na pasta selecionada!')
    def parse_xml_file(self, xml_path):
        '''Parse do arquivo XML com abordagem SIMPLIFICADA baseada nos scripts BAT funcionais'''
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            partitions = []
            xml_folder = os.path.dirname(xml_path)
            filename_elements = root.findall('.//*[@filename]')
            erase_elements = root.findall('.//erase')
            essential_partitions = ['bootloader', 'boot', 'recovery', 'system', 'modem', 'logo', 'gpt', 'persist', 'fsg', 'dsp', 'aboot', 'rpm', 'tz', 'sbl1', 'hyp', 'pmic', 'keymaster', 'cmnlib', 'cmnlib64', 'lksecapp', 'vendor']
            for elem in filename_elements:
                partition_info = {'name': '', 'file': '', 'action': 'flash', 'essential': False, 'selected': True, 'size': 'N/A'}
                partition_info['file'] = elem.attrib.get('filename', '')
                if 'partition' in elem.attrib:
                    partition_info['name'] = elem.attrib['partition']
                elif 'var' in elem.attrib:
                    var_name = elem.attrib['var']
                    if 'partition-' in var_name:
                        partition_info['name'] = var_name.replace('partition-', '')
                    else:
                        partition_info['name'] = var_name
                if not partition_info['name']:
                    if partition_info['file']:
                        if 'sparsechunk' in partition_info['file'].lower():
                            if '.img_sparsechunk.' in partition_info['file']:
                                base_name = partition_info['file'].split('.img_sparsechunk.')[0]
                            elif '_sparsechunk.' in partition_info['file']:
                                base_name = partition_info['file'].split('_sparsechunk.')[0]
                            else:
                                base_name = partition_info['file'].replace('.img', '').replace('.bin', '').replace('.mbn', '')
                            partition_info['name'] = base_name
                        else:
                            name_from_file = partition_info['file']
                            for ext in ('.img', '.bin', '.mbn'):
                                if not name_from_file.endswith(ext):
                                    continue
                                name_from_file = name_from_file[:-len(ext)]
                                break
                            partition_info['name'] = name_from_file
                partition_info['essential'] = any((essential in partition_info['name'].lower() for essential in essential_partitions))
            try:
                file_path = os.path.join(xml_folder, partition_info['file'])
                if os.path.exists(file_path):
                    size_bytes = os.path.getsize(file_path)
                    partition_info['size'] = self.format_size(size_bytes)
            except Exception:
                partition_info['size'] = 'N/A'
            else:
                if not partition_info['name']:
                    pass
                if not partition_info['file']:
                    pass
                partitions.append(partition_info)
                for elem in erase_elements:
                    partition_info = {'name': elem.attrib.get('partition', ''), 'file': '', 'action': 'erase', 'essential': False, 'selected': True, 'size': 'N/A'}
                    if partition_info['name']:
                        partition_info['essential'] = any((essential in partition_info['name'].lower() for essential in essential_partitions))
                        partitions.append(partition_info)
                if not partitions:
                    partitions = self.alternative_xml_parsing(root)
                if not partitions:
                    raise Exception('Nenhuma parti├º├úo encontrada no XML')
                flash_count = sum((1 for p in partitions if p['action'] == 'flash'))
                erase_count = sum((1 for p in partitions if p['action'] == 'erase'))
                if flash_count > 0:
                    self.log_text.append(f'­ƒô▓ {flash_count} parti├º├Áes para flash encontradas')
                if erase_count > 0:
                    self.log_text.append(f'­ƒùæ´©Å {erase_count} parti├º├Áes para erase encontradas')
                firmware_folder = os.path.dirname(xml_path)
                self.log_text.append(f'­ƒôü Pasta detectada: {firmware_folder}')
                if firmware_folder and os.path.exists(firmware_folder):
                    pass
        except Exception as e:
            self.log_text.append(f'ÔØî Erro ao analisar XML: {str(e)}')
            return False
        self.xml_data = {'file_path': xml_path, 'folder': firmware_folder, 'partitions': partitions}
        self.populate_partitions_tree()
        self.check_device_status()
        self.file_label.setText(f'­ƒôä {os.path.basename(xml_path)} ({len(partitions)} parti├º├Áes)')
        self.file_label.setStyleSheet('\n                QLabel {\n                    color: #27ae60; \n                    font-weight: bold;\n                    font-size: 12px;\n                    padding: 8px;\n                    background-color: #f8f9fa;\n                    border-radius: 4px;\n                    border: 1px solid #27ae60;\n                }\n            ')
        success_msg = f'Ô£à XML analisado com sucesso! {len(partitions)} parti├º├Áes encontradas.'
        self.log_text.append(success_msg)
        self.validate_flash_conditions()
        return True
    def validate_flash_conditions(self):
        '''Valida se todas as condi├º├Áes para flash est├úo atendidas'''
        try:
            if not self.xml_data or not self.xml_data.get('partitions'):
                self.flash_btn.setEnabled(False)
                return False
            selected_partitions = self.get_selected_partitions()
            if not selected_partitions:
                self.flash_btn.setEnabled(False)
                return False
            self.flash_btn.setEnabled(True)
            self.log_text.append(f'Ô£à Sistema pronto para flash! {len(selected_partitions)} parti├º├Áes selecionadas')
            return True
        except Exception as e:
            self.flash_btn.setEnabled(False)
            return False
    def extract_partition_info(self, elem, xml_folder=None):
        '''Extrai informa├º├Áes de parti├º├úo de um elemento XML - MANT├ëM SPARSECHUNKS SEPARADOS'''
        try:
            partition_info = {'name': '', 'file': '', 'action': '', 'essential': False, 'selected': True, 'size': 'N/A', 'is_sparsechunk': False, 'base_partition': '', 'unique_id': ''}
            if 'partition' in elem.attrib:
                partition_info['name'] = elem.attrib['partition']
            elif 'var' in elem.attrib and 'partition' in elem.attrib['var']:
                partition_info['name'] = elem.attrib['var'].replace('partition-', '')
            if 'filename' in elem.attrib:
                partition_info['file'] = elem.attrib['filename']
            elif 'file' in elem.attrib:
                partition_info['file'] = elem.attrib['file']
            if elem.tag == 'erase':
                partition_info['action'] = 'erase'
            elif elem.tag == 'flash' or 'flash' in elem.attrib.get('operation', ''):
                partition_info['action'] = 'flash'
            else:
                partition_info['action'] = elem.tag
            if partition_info['file'] and 'sparsechunk' in partition_info['file'].lower():
                partition_info['is_sparsechunk'] = True
                partition_info['unique_id'] = f'{partition_info['name']}_{partition_info['file']}'
                if '.img_sparsechunk' in partition_info['file']:
                    base_name = partition_info['file'].split('.img_sparsechunk')[0]
                elif '_sparsechunk' in partition_info['file']:
                    base_name = partition_info['file'].split('_sparsechunk')[0]
                else:
                    base_name = partition_info['file'].replace('.img', '')
                partition_info['base_partition'] = base_name
            else:
                partition_info['unique_id'] = f'{partition_info['name']}_{partition_info['action']}'
            essential_partitions = ['bootloader', 'boot', 'recovery', 'system', 'modem', 'logo', 'gpt', 'persist', 'fsg', 'dsp', 'aboot', 'rpm', 'tz', 'sbl1', 'hyp', 'pmic', 'keymaster', 'cmnlib', 'cmnlib64', 'lksecapp', 'vendor']
            partition_info['essential'] = any((essential in partition_info['name'].lower() for essential in essential_partitions))
            if partition_info['file'] and xml_folder:
                pass
            try:
                file_path = os.path.join(xml_folder, partition_info['file'])
                if os.path.exists(file_path):
                    size_bytes = os.path.getsize(file_path)
                    partition_info['size'] = self.format_size(size_bytes)
            except Exception:
                pass
            else:
                if partition_info['name']:
                    return partition_info
        except Exception as e:
            return
    def alternative_xml_parsing(self, root):
        '''Parsing alternativo para XMLs com estrutura diferente'''
        partitions = []
        try:
            text_content = ET.tostring(root, encoding='unicode')
            import re
            flash_pattern = 'fastboot\\s+flash\\s+(\\w+)\\s+([^\\s]+)'
            flash_matches = re.findall(flash_pattern, text_content, re.IGNORECASE)
            essential_partitions = ['bootloader', 'boot', 'recovery', 'system', 'modem', 'logo', 'gpt', 'persist', 'fsg', 'dsp', 'aboot', 'rpm', 'tz', 'sbl1', 'hyp', 'pmic', 'keymaster', 'cmnlib', 'cmnlib64', 'lksecapp', 'vendor']
            for partition, filename in flash_matches:
                is_essential = any((essential in partition.lower() for essential in essential_partitions))
                partitions.append({'name': partition, 'file': filename, 'action': 'flash', 'essential': is_essential, 'selected': True, 'size': 'N/A'})
            erase_pattern = 'fastboot\\s+erase\\s+(\\w+)'
            erase_matches = re.findall(erase_pattern, text_content, re.IGNORECASE)
            for partition in erase_matches:
                partitions.append({'name': partition, 'file': '', 'action': 'erase', 'essential': False, 'selected': True, 'size': 'N/A'})
        except Exception as e:
            self.log_text.append(f'ÔÜá´©Å Erro no parsing alternativo: {str(e)}')
        return partitions
    def format_size(self, size_bytes):
        '''Formata tamanho em bytes para formato leg├¡vel'''
        for unit in ('B', 'KB', 'MB', 'GB'):
            if size_bytes < 1024.0:
                return f'{size_bytes:.1f} {unit}'
            size_bytes /= 1024.0
        return f'{size_bytes:.1f} TB'
    def populate_partitions_tree(self):
        '''Popula a ├írvore de parti├º├Áes'''
        self.partitions_tree.clear()
        if not self.xml_data or not self.xml_data['partitions']:
            return
        groups = {}
        for partition in self.xml_data['partitions']:
            action = partition['action']
            if action not in groups:
                groups[action] = []
            groups[action].append(partition)
        for action, partitions in groups.items():
            group_item = QTreeWidgetItem([f'­ƒôü {action.upper()}', '', '', ''])
            group_item.setExpanded(True)
            for partition in partitions:
                partition_item = QTreeWidgetItem([partition['name'], partition['file'], partition['size'], partition['action']])
                partition_item.setFlags(partition_item.flags() | Qt.ItemIsUserCheckable)
                partition_item.setCheckState(0, Qt.Checked if partition['selected'] else Qt.Unchecked)
                if partition['essential']:
                    partition_item.setToolTip(0, 'Parti├º├úo essencial para o funcionamento do sistema')
                group_item.addChild(partition_item)
                self.update_partition_visual(partition_item)
            self.partitions_tree.addTopLevelItem(group_item)
            continue
        self.update_selection_counter()
        self.validate_flash_conditions()
    def select_all_partitions(self):
        '''Seleciona todas as parti├º├Áes'''
        if not self.xml_data or not self.xml_data.get('partitions'):
            QMessageBox.warning(self, 'Aviso', 'Carregue um arquivo XML primeiro!')
            return
        self.set_all_partitions_checked(True)
        self.update_selection_counter()
        self.validate_flash_conditions()
        self.log_text.append('Ô£à Todas as parti├º├Áes foram selecionadas')
    def select_essential_partitions(self):
        '''Seleciona apenas parti├º├Áes essenciais'''
        if not self.xml_data or not self.xml_data.get('partitions'):
            QMessageBox.warning(self, 'Aviso', 'Carregue um arquivo XML primeiro!')
            return
        essential_partitions = ['bootloader', 'boot', 'recovery', 'system', 'modem', 'logo', 'gpt', 'persist', 'fsg', 'dsp', 'aboot', 'rpm', 'tz', 'sbl1', 'hyp', 'pmic', 'keymaster', 'cmnlib', 'cmnlib64', 'lksecapp', 'vendor']
        selected_count = 0
        for i in range(self.partitions_tree.topLevelItemCount()):
            group_item = self.partitions_tree.topLevelItem(i)
            for j in range(group_item.childCount()):
                partition_item = group_item.child(j)
                partition_name = partition_item.text(0).lower()
                is_essential_hardcoded = any((essential in partition_name for essential in essential_partitions))
                is_essential_xml = any((partition.get('essential', False) for partition in self.xml_data['partitions'] if partition['name'].lower() != partition_name))
                is_essential = is_essential_hardcoded or is_essential_xml
                if is_essential:
                    partition_item.setCheckState(0, Qt.Checked)
                    selected_count += 1
                else:
                    partition_item.setCheckState(0, Qt.Unchecked)
                self.update_partition_visual(partition_item)
            continue
        self.update_selection_counter()
        self.validate_flash_conditions()
        self.log_text.append(f'ÔÜí {selected_count} parti├º├Áes essenciais selecionadas')
        selected_names = []
        for i in range(self.partitions_tree.topLevelItemCount()):
            group_item = self.partitions_tree.topLevelItem(i)
            for j in range(group_item.childCount()):
                partition_item = group_item.child(j)
                if partition_item.checkState(0) == Qt.Checked:
                    selected_names.append(partition_item.text(0))
        self.log_text.append(f'­ƒôï Parti├º├Áes: {', '.join(selected_names[:10])}')
        if len(selected_names) > 10:
            self.log_text.append(f'­ƒôï ...e mais {len(selected_names) - 10} parti├º├Áes')
    def deselect_all_partitions(self):
        '''Desmarca todas as parti├º├Áes'''
        if not self.xml_data or not self.xml_data.get('partitions'):
            QMessageBox.warning(self, 'Aviso', 'Carregue um arquivo XML primeiro!')
            return
        self.set_all_partitions_checked(False)
        self.update_selection_counter()
        self.validate_flash_conditions()
        self.log_text.append('ÔØî Todas as parti├º├Áes foram desmarcadas')
    def set_all_partitions_checked(self, checked):
        '''Define estado de sele├º├úo de todas as parti├º├Áes'''
        if self.partitions_tree.topLevelItemCount() == 0:
            return
        state = Qt.Checked if checked else Qt.Unchecked
        for i in range(self.partitions_tree.topLevelItemCount()):
            group_item = self.partitions_tree.topLevelItem(i)
            for j in range(group_item.childCount()):
                partition_item = group_item.child(j)
                partition_item.setCheckState(0, state)
                self.update_partition_visual(partition_item)
    def update_selection_counter(self):
        '''Atualiza contador de parti├º├Áes selecionadas'''
        if not hasattr(self, 'selection_counter'):
            return
        selected_count = 0
        total_count = 0
        for i in range(self.partitions_tree.topLevelItemCount()):
            group_item = self.partitions_tree.topLevelItem(i)
            for j in range(group_item.childCount()):
                partition_item = group_item.child(j)
                total_count += 1
                if partition_item.checkState(0) == Qt.Checked:
                    selected_count += 1
        if selected_count == 0:
            text = '­ƒôè Nenhuma parti├º├úo selecionada'
            color = '#e74c3c'
        elif selected_count == total_count:
            text = f'­ƒôè Todas as {total_count} parti├º├Áes selecionadas'
            color = '#27ae60'
        else:
            text = f'­ƒôè {selected_count} de {total_count} parti├º├Áes selecionadas'
            color = '#f39c12'
        self.selection_counter.setText(text)
        self.selection_counter.setStyleSheet(f'\n            QLabel {{\n                color: {color};\n                font-size: 11px;\n                font-weight: bold;\n                padding: 2px 5px;\n                background-color: rgba(52,152,219,0.1);\n                border-radius: 3px;\n                margin-bottom: 3px;\n            }}\n                 ')
    def on_partition_selection_changed(self, item, column):
        '''Callback chamado quando sele├º├úo de parti├º├úo muda'''
        if column == 0:
            self.update_partition_visual(item)
            self.update_selection_counter()
            self.validate_flash_conditions()
    def update_partition_visual(self, item):
        '''Atualiza visual da parti├º├úo baseado no estado de sele├º├úo'''
        if not item or item.parent() is None:
            return
        partition_name = item.text(0)
        is_checked = item.checkState(0) == Qt.Checked
        essential_partitions = ['bootloader', 'boot', 'recovery', 'system', 'modem', 'logo', 'gpt']
        is_essential = False
        if self.xml_data and self.xml_data.get('partitions'):
            for partition in self.xml_data['partitions']:
                if partition['name'] != partition_name:
                    continue
                if not partition.get('essential', False):
                    continue
                is_essential = True
                break
        if not is_essential:
            is_essential = partition_name.lower() in essential_partitions
        if is_essential:
            if is_checked:
                item.setBackground(0, QColor(255, 193, 7, 200))
                item.setBackground(1, QColor(255, 193, 7, 100))
                item.setBackground(2, QColor(255, 193, 7, 80))
                item.setBackground(3, QColor(255, 193, 7, 80))
                font = item.font(0)
                font.setBold(True)
                item.setFont(0, font)
            else:
                item.setBackground(0, QColor(255, 235, 59, 120))
                item.setBackground(1, QColor(255, 255, 255, 0))
                item.setBackground(2, QColor(255, 255, 255, 0))
                item.setBackground(3, QColor(255, 255, 255, 0))
                font = item.font(0)
                font.setBold(False)
                item.setFont(0, font)
        elif is_checked:
            item.setBackground(0, QColor(33, 150, 243, 180))
            item.setBackground(1, QColor(33, 150, 243, 100))
            item.setBackground(2, QColor(33, 150, 243, 80))
            item.setBackground(3, QColor(33, 150, 243, 80))
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)
        else:
            item.setBackground(0, QColor(255, 255, 255, 0))
            item.setBackground(1, QColor(255, 255, 255, 0))
            item.setBackground(2, QColor(255, 255, 255, 0))
            item.setBackground(3, QColor(255, 255, 255, 0))
            font = item.font(0)
            font.setBold(False)
            item.setFont(0, font)
        if is_checked:
            item.setForeground(0, QColor(255, 255, 255))
            return
        item.setForeground(0, QColor(0, 0, 0))
    def check_device_status(self):
        '''Verifica status do dispositivo de forma simplificada'''
        try:
            if self.adb.check_fastboot_device():
                self.device_status.setText('Ô£à Dispositivo em modo Fastboot')
                self.device_status.setStyleSheet('color: #27ae60; font-weight: bold;')
            try:
                device_info = self.adb.execute_fastboot_command('getvar product')
                if device_info and ':' in device_info:
                    model = device_info.split(':')[-1].strip()
                    self.log_text.append(f'­ƒô▒ Dispositivo: {model}')
                else:
                    self.log_text.append('­ƒô▒ Dispositivo Motorola detectado')
            except Exception:
                self.log_text.append('­ƒô▒ Dispositivo Motorola em fastboot')
                self.device_has_ab = False
            else:
                try:
                    try:
                        try:
                            current_slot = self.adb.execute_fastboot_command('getvar current-slot')
                            if 'current-slot:' in current_slot and current_slot.split(':')[-1].strip():
                                self.device_has_ab = True
                                active_slot = current_slot.split(':')[-1].strip()
                                self.log_text.append(f'­ƒöä Dispositivo A/B detectado (slot ativo: {active_slot})')
                                return
                            self.device_has_ab = False
                            self.log_text.append('­ƒöº Dispositivo tradicional (n├úo-A/B)')
                        except Exception:
                            self.device_has_ab = False
                            self.log_text.append('­ƒöº Dispositivo tradicional (n├úo-A/B)')
                    except Exception:
                        self.log_text.append('­ƒô▒ Dispositivo Motorola em fastboot')
                        self.device_has_ab = False
                except Exception as e:
                    self.device_status.setText(f'ÔØî Erro ao verificar: {str(e)}')
                    self.device_status.setStyleSheet('color: #e74c3c; font-weight: bold;')
                return
        except Exception as e:
            self.device_status.setText(f'ÔØî Erro ao verificar: {str(e)}')
            self.device_status.setStyleSheet('color: #e74c3c; font-weight: bold;')
    def get_selected_partitions(self):
        '''Retorna lista de parti├º├Áes selecionadas - CORRE├ç├âO CR├ìTICA DE SPARSECHUNK'''
        selected = []
        for i in range(self.partitions_tree.topLevelItemCount()):
            group_item = self.partitions_tree.topLevelItem(i)
            for j in range(group_item.childCount()):
                partition_item = group_item.child(j)
                if partition_item.checkState(0) == Qt.Checked:
                    partition_name = partition_item.text(0)
                    partition_file = partition_item.text(1)
                    for partition in self.xml_data['partitions']:
                        if partition['name'] != partition_name:
                            continue
                        if not partition['file'] == partition_file:
                            continue
                        selected.append(partition)
                        break
        return selected
    def start_flash(self):
        '''Inicia o processo de flash'''
        try:
            self.log_text.append('­ƒöì Executando verifica├º├Áes pr├®-flash...')
            if not self.adb.check_fastboot_device():
                QMessageBox.warning(self, 'Erro', 'Dispositivo precisa estar em modo Fastboot!')
                return
            connectivity_ok = False
            test_commands = ['getvar product', 'getvar serialno', 'devices']
            for cmd in test_commands:
                pass
            try:
                test_response = self.adb.execute_fastboot_command(cmd)
                if test_response is not None:
                    self.log_text.append(f'Ô£à Teste de conectividade aprovado ({cmd})')
                    connectivity_ok = True
            except Exception as e:
                self.log_text.append(f'ÔÜá´©Å Comando {cmd} falhou: {str(e)}')
            else:
                if not connectivity_ok:
                    QMessageBox.critical(self, 'Erro de Conectividade', 'Dispositivo n├úo responde a nenhum comando fastboot:\n\nVerifique:\nÔÇó Drivers USB Motorola instalados\nÔÇó Cabo USB de qualidade funcionando\nÔÇó Dispositivo realmente em modo Fastboot\nÔÇó Porta USB diferente (preferencialmente USB 2.0)\nÔÇó Feche outros programas que possam usar o dispositivo')
                    return
                if not self.xml_data:
                    QMessageBox.warning(self, 'Erro', 'Selecione um arquivo XML primeiro!')
                    return
                selected_partitions = self.get_selected_partitions()
                if not selected_partitions:
                    QMessageBox.warning(self, 'Erro', 'Selecione pelo menos uma parti├º├úo para flash!')
                    return
                missing_files = []
                for partition in selected_partitions:
                    if partition['action'] != 'flash':
                        continue
                    if partition['file']:
                        file_path = os.path.join(self.xml_data['folder'], partition['file'])
                        if os.path.exists(file_path):
                            continue
                        missing_files.append(partition['file'])
                if missing_files:
                    QMessageBox.critical(self, 'Arquivos N├úo Encontrados', 'Os seguintes arquivos n├úo foram encontrados:\n\n' + '\n'.join(missing_files[:5]) + (f'\n... e mais {len(missing_files) - 5}' if len(missing_files) > 5 else '') + f'\n\nPasta: {self.xml_data['folder']}')
                    return
                self.log_text.append('Ô£à Todas as verifica├º├Áes aprovadas')
                msg = f'Deseja iniciar o flash de {len(selected_partitions)} parti├º├Áes?\n\n'
                msg += f'Tipo: {'COM WIPE' if self.flash_type == 'wipe' else 'SEM WIPE'}\n'
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao iniciar flash:\n{str(e)}')
        try:
            msg += f'Parti├º├Áes: {', '.join([p['name'] for p in selected_partitions[:5]])}'
            if len(selected_partitions) > 5:
                msg += f'e mais {len(selected_partitions) - 5}...'
            reply = QMessageBox.question(self, 'Confirmar Flash', msg, QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
            self.flash_thread = FlashThread(self.adb, self.xml_data, selected_partitions, self.flash_type)
            self.flash_thread.progress_signal.connect(self.update_progress)
            self.flash_thread.log_signal.connect(self.log_text.append)
            self.flash_thread.finished_signal.connect(self.flash_finished)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.flash_btn.setEnabled(False)
            self.tabs.setCurrentIndex(1)
            self.log_text.append('­ƒöÑ Iniciando processo de flash...')
            self.flash_thread.start()
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao iniciar flash:\n{str(e)}')
    def update_progress(self, value):
        '''Atualiza barra de progresso'''
        self.progress_bar.setValue(value)
    def flash_finished(self, success, message):
        '''Callback quando flash termina'''
        self.progress_bar.setVisible(False)
        self.flash_btn.setEnabled(True)
        if success:
            self.log_text.append('Ô£à Flash conclu├¡do com sucesso!')
            QMessageBox.information(self, 'Sucesso', message)
            return
        self.log_text.append(f'ÔØî Flash falhou: {message}')
        QMessageBox.critical(self, 'Erro', f'Flash falhou:\n{message}')
class FlashThread(QThread):
    '''Thread para executar flash em background'''
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    def __init__(self, adb, xml_data, partitions, flash_type):
        super().__init__()
        self.adb = adb
        self.xml_data = xml_data
        self.partitions = partitions
        self.flash_type = flash_type
    def run(self):
        '''Executa flash simplificado baseado na l├│gica dos scripts BAT universais'''
        try:
            total_steps = len(self.partitions)
            current_step = 0
            self.log_signal.emit(f'­ƒÜÇ Iniciando flash de {total_steps} parti├º├Áes...')
            device_supports_ab = False
            try:
                current_slot = self.adb.execute_fastboot_command('getvar current-slot')
                if 'current-slot:' in current_slot and current_slot.split(':')[-1].strip():
                    device_supports_ab = True
            except Exception:
                device_supports_ab = False
            else:
                try:
                    self.adb.execute_fastboot_command('getvar max-sparse-size')
                    self.adb.execute_fastboot_command('oem fb_mode_set')
                except Exception:
                    pass
                for partition in self.partitions:
                    pass
        except Exception as e:
            self.finished_signal.emit(False, str(e))
        self.progress_signal.emit(95)
        final_commands = [['oem', 'fb_mode_clear'], ['reboot']]
        self.log_signal.emit('­ƒöä Executando comandos finais...')
        for cmd in final_commands:
            try:
                try:
                    if cmd[0] == 'reboot':
                        self.log_signal.emit('­ƒöä Reiniciando dispositivo...')
                    result = self.adb.execute_fastboot_command(' '.join(cmd))
                    if result:
                        self.log_signal.emit(f'Ô£à {result}')
                except Exception as e:
                    self.log_signal.emit(f'ÔÜá´©Å {str(e)}')
                    continue
            except Exception as e:
                self.finished_signal.emit(False, str(e))
        self.progress_signal.emit(100)
        self.log_signal.emit('Ô£à Flash conclu├¡do com sucesso!')
        self.finished_signal.emit(True, 'Flash conclu├¡do com sucesso!')
class ToolsAndroid(QWidget):
    update_status_signal = pyqtSignal(str, str)
    append_log_signal = pyqtSignal(str)
    def __init__(self, parent=None, adb_manager=None):
        super().__init__(parent)
        self.update_status_signal.connect(self.update_device_status)
        self.append_log_signal.connect(self._append_log)
        self.logger = logging.getLogger(__name__)
        self.adb = adb_manager or ADBManager()
        self.tools = AndroidTools(adb_manager=self.adb)
        self.checking_device = False
        self._updating_info = False
        self._checking_in_progress = False
        self._showing = False
        self.last_check_time = 0
        self._svg_path = PathManager.get_resource_path('icons_svg')
        self.setup_styles()
        self.setup_ui()
    def setup_styles(self):
        '''Define os estilos da interface'''
        self.button_style = '\n            QPushButton {\n                padding: 6px 10px;\n                font-size: 8pt;\n                min-height: 32px;\n                background-color: #2196F3;\n                color: white;\n                border-radius: 6px;\n                font-weight: 600;\n                border: none;\n                text-align: left;\n                padding-left: 12px;\n            }\n            QPushButton:hover {\n                background-color: #0D47A1;\n            }\n            QPushButton:pressed {\n                background-color: #1428A0;\n            }\n            QPushButton:disabled {\n                background-color: #bdc3c7;\n                color: #7f8c8d;\n            }\n        '
    def setup_ui(self):
        '''Configura a interface do usu├írio'''
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet('\n            QTabWidget::pane {\n                border: 1px solid #e0e0e0;\n                background: #ffffff;\n                border-radius: 4px;\n            }\n            QTabWidget::tab-bar {\n                alignment: left;\n            }\n            QTabBar::tab {\n                background: #1428A0;\n                border: 1px solid #0D47A1;\n                padding: 6px 16px;\n                margin-right: 2px;\n                border-top-left-radius: 4px;\n                border-top-right-radius: 4px;\n                font-weight: bold;\n                min-width: 70px;\n                font-size: 8pt;\n                color: #bcd0ea;\n            }\n            QTabBar::tab:selected {\n                background: #2196F3;\n                border-color: #2196F3;\n                color: white;\n            }\n            QTabBar::tab:hover {\n                background: #0D47A1;\n                color: white;\n            }\n        ')
        standard_tab = QWidget()
        self.setup_standard_tab(standard_tab)
        self.tab_widget.addTab(standard_tab, 'Padr├úo')
        if MOTOROLA_FLASH_AVAILABLE:
            self.flash_tab = MotorolaFlashToolWidget()
            self.tab_widget.addTab(self.flash_tab, 'Flash')
        main_layout.addWidget(self.tab_widget)
    def _make_card_label_adaptive(self, label):
        '''Torna uma QLabel do card de status responsiva a resolu├º├úo/zoom.
- `setWordWrap(True)`: reflui o texto (horizontal) em vez de cortar quando
  o painel encolhe.
- Pol├¡tica vertical `Minimum`: o `sizeHint` vira o piso de altura, ent├úo a
  label NUNCA ├® comprimida abaixo da altura natural -> elimina a
  sobreposi├º├úo de texto observada em DPI 125%/150%.
- `setHeightForWidth(True)`: garante que, ao quebrar em mais linhas, o
  layout reserve a altura correta.
'''
        label.setWordWrap(True)
        policy = label.sizePolicy()
        policy.setHorizontalPolicy(QSizePolicy.Expanding)
        policy.setVerticalPolicy(QSizePolicy.Minimum)
        policy.setHeightForWidth(True)
        label.setSizePolicy(policy)
    def setup_standard_tab(self, tab_widget):
        '''Configura a aba padr├úo com funcionalidades atuais'''
        main_layout = QHBoxLayout(tab_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        left_panel = QFrame()
        left_panel.setStyleSheet('\n            QFrame {\n                background-color: #ffffff;\n                border-radius: 8px;\n                border: 1px solid #e0e0e0;\n            }\n        ')
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(15)
        status_frame = QFrame()
        status_frame.setStyleSheet('\n            QFrame {\n                background-color: #1428A0;\n                border-radius: 6px;\n                padding: 8px;\n                border: 1px solid #0D47A1;\n            }\n            QLabel {\n                color: #ffffff;\n                margin-bottom: 1px;\n                font-size: 8pt;\n            }\n        ')
        status_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        status_layout = QVBoxLayout(status_frame)
        status_layout.setSpacing(4)
        status_layout.setContentsMargins(4, 4, 4, 4)
        self.device_info = QLabel("Clique em 'Verificar Dispositivo' para iniciar")
        self.device_info.setStyleSheet('font-weight: bold; font-size: 10pt; color: #ecf0f1; margin-bottom: 4px;')
        self._make_card_label_adaptive(self.device_info)
        status_layout.addWidget(self.device_info)
        divider1 = QFrame()
        divider1.setFrameShape(QFrame.HLine)
        divider1.setStyleSheet('background-color: rgba(255,255,255,0.2); max-height: 1px;')
        status_layout.addWidget(divider1)
        device_section = QFrame()
        device_section.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        device_layout = QVBoxLayout(device_section)
        device_layout.setContentsMargins(0, 0, 0, 0)
        device_layout.setSpacing(2)
        self.model_info = QLabel('Modelo: Aguardando...')
        self.model_info.setStyleSheet('color: #bdc3c7; font-weight: 500; font-size: 8pt;')
        self._make_card_label_adaptive(self.model_info)
        device_layout.addWidget(self.model_info)
        self.hardware_info = QLabel('CPU: Aguardando...')
        self.hardware_info.setStyleSheet('color: #bdc3c7; font-weight: 500; font-size: 8pt;')
        self._make_card_label_adaptive(self.hardware_info)
        device_layout.addWidget(self.hardware_info)
        status_layout.addWidget(device_section)
        divider2 = QFrame()
        divider2.setFrameShape(QFrame.HLine)
        divider2.setStyleSheet('background-color: rgba(255,255,255,0.2); max-height: 1px;')
        status_layout.addWidget(divider2)
        security_section = QFrame()
        security_section.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        security_layout = QVBoxLayout(security_section)
        security_layout.setContentsMargins(0, 0, 0, 0)
        security_layout.setSpacing(2)
        security_label = QLabel('SEGURAN├çA')
        security_label.setStyleSheet('color: rgba(255,255,255,0.7); font-size: 7pt; font-weight: bold; margin-bottom: 1px;')
        security_layout.addWidget(security_label)
        security_row = QFrame()
        security_row_layout = QHBoxLayout(security_row)
        security_row_layout.setContentsMargins(0, 0, 0, 0)
        security_row_layout.setSpacing(8)
        self.bootloader_status = QLabel('Bootloader: N/A')
        self.bootloader_status.setStyleSheet('color: #bdc3c7; font-size: 8pt;')
        self._make_card_label_adaptive(self.bootloader_status)
        security_row_layout.addWidget(self.bootloader_status, 1)
        self.frp_status = QLabel('FRP: N/A')
        self.frp_status.setStyleSheet('color: #bdc3c7; font-size: 8pt;')
        self._make_card_label_adaptive(self.frp_status)
        security_row_layout.addWidget(self.frp_status, 1)
        security_layout.addWidget(security_row)
        status_layout.addWidget(security_section)
        divider3 = QFrame()
        divider3.setFrameShape(QFrame.HLine)
        divider3.setStyleSheet('background-color: rgba(255,255,255,0.2); max-height: 1px;')
        status_layout.addWidget(divider3)
        self.slot_info = QLabel('Slots: Aguardando...')
        self.slot_info.setStyleSheet('color: #bdc3c7; font-weight: 500; font-size: 8pt;')
        self._make_card_label_adaptive(self.slot_info)
        status_layout.addWidget(self.slot_info)
        left_layout.addWidget(status_frame)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('\n            QScrollArea { border: none; background: transparent; }\n            QScrollBar:vertical {\n                background: #f0f0f0;\n                width: 8px;\n                border-radius: 4px;\n            }\n            QScrollBar::handle:vertical {\n                background: #bdc3c7;\n                border-radius: 4px;\n                min-height: 20px;\n            }\n            QScrollBar::handle:vertical:hover {\n                background: #2196F3;\n            }\n            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {\n                height: 0px;\n            }\n        ')
        scroll_content = QWidget()
        scroll_content.setStyleSheet('background: #ffffff;')
        buttons_layout = QVBoxLayout(scroll_content)
        buttons_layout.setSpacing(8)
        buttons_layout.setContentsMargins(4, 4, 4, 4)
        _btn_icons = {'Verificar Dispositivo': 'question-circle.svg', 'Status Bootloader': 'shield-lock.svg', 'Desbloquear Bootloader': 'shield-check.svg', 'Download Firmware': 'cloud-arrow-down.svg', 'Remover MDM': 'shield-shaded.svg', 'Fix Comm Server': 'tools.svg', 'Reboot Fastboot': 'arrow-clockwise.svg', 'FRP Models MTKs/SPD': 'phone-flip.svg'}
        buttons = [('Verificar Dispositivo', self.check_device, 'Detecta o dispositivo (Fastboot/ADB) e mostra informa├º├Áes detalhadas'), ('Status Bootloader', self.check_bootloader_status, 'Verifica status do bootloader (requer Fastboot)'), ('Desbloquear Bootloader', self.show_unlock_dialog, 'Processo completo de desbloqueio do bootloader'), ('Download Firmware', self.download_firmware, 'Download de firmware oficial Motorola'), ('Remover MDM', self.remove_mdm, 'Remove MDM do dispositivo'), ('Fix Comm Server', self.fix_comm_server, 'Corrige erro de Comm Server em dispositivos sem servi├ºos por falha CQA ou software'), ('Reboot Fastboot', self.fastboot_reboot, 'Reinicia em modo fastboot'), ('FRP Models MTKs/SPD', self.show_frp_motorola_mtk, 'BETA - Remo├º├úo de FRP via BROM/SPD Mode para Motorola e Xiaomi'), ('premium:ID:5', self.execute_premium_motorola_id_5, 'Servi├ºo Premium - T├¡tulo din├ómico do banco (ID 5)', False)]
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(6)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setColumnStretch(2, 1)
        dev_notice = QLabel('Algumas funcionalidades estao em fase de testes. Sempre faca backup antes de procedimentos criticos.')
        dev_notice.setStyleSheet('\n            QLabel {\n                color: #e67e22;\n                font-size: 7pt;\n                padding: 6px 10px;\n                background-color: #fff8e1;\n                border: 1px solid #ffcc02;\n                border-radius: 4px;\n            }\n        ')
        dev_notice.setWordWrap(True)
        dev_notice.setAlignment(Qt.AlignCenter)
        buttons_layout.addWidget(dev_notice)
        from app.utils.premium_services_manager import get_premium_services_manager
        premium_manager = get_premium_services_manager()
        row = 0
        col = 0
        for btn_data in buttons:
            if len(btn_data) == 3:
                btn_text, btn_func, tooltip = btn_data
            else:
                btn_text, btn_func, tooltip, _ = btn_data
            is_premium_button = btn_text.startswith('premium:')
            is_dev_button = btn_text.startswith('ÔÜá´©Å')
            if is_premium_button:
                servico_identificador = btn_text.replace('premium:', '')
                btn = premium_manager.criar_botao_premium_com_indicador(servico_identificador, btn_func, parent=self)
                btn.setToolTip(tooltip)
                btn.setStyleSheet('\n                    QPushButton {\n                        padding: 6px 10px;\n                        font-size: 8pt;\n                        font-weight: bold;\n                        min-height: 32px;\n                        background-color: #c0392b;\n                        color: white;\n                        border-radius: 6px;\n                        border: 1px solid #e74c3c;\n                        text-align: left;\n                        padding-left: 12px;\n                    }\n                    QPushButton:hover {\n                        background-color: #e74c3c;\n                        border: 1px solid #ec7063;\n                    }\n                    QPushButton:pressed {\n                        background-color: #922b21;\n                        border: 1px solid #922b21;\n                    }\n                    QPushButton:disabled {\n                        background-color: #bdc3c7;\n                        color: #7f8c8d;\n                        border: 1px solid #bdc3c7;\n                    }\n                ')
                if not hasattr(self, 'premium_buttons'):
                    self.premium_buttons = []
                self.premium_buttons.append((btn, servico_identificador))
            elif is_dev_button:
                btn = QPushButton(btn_text)
                btn.clicked.connect(btn_func)
                btn.setToolTip(tooltip)
                btn.setStyleSheet('\n                    QPushButton {\n                        padding: 6px 10px;\n                        font-size: 8pt;\n                        font-weight: bold;\n                        min-height: 32px;\n                        background-color: #f39c12;\n                        color: #1e1e1e;\n                        border-radius: 6px;\n                        border: 1px solid #f1c40f;\n                        text-align: left;\n                        padding-left: 12px;\n                    }\n                    QPushButton:hover {\n                        background-color: #f1c40f;\n                        border: 1px solid #f9e547;\n                    }\n                    QPushButton:pressed {\n                        background-color: #d68910;\n                        border: 1px solid #d68910;\n                    }\n                    QPushButton:disabled {\n                        background-color: #bdc3c7;\n                        color: #7f8c8d;\n                        border: 1px solid #bdc3c7;\n                    }\n                ')
            else:
                btn = QPushButton(btn_text)
                btn.setStyleSheet(self.button_style)
                btn.clicked.connect(btn_func)
                btn.setToolTip(tooltip)
            icon_file = _btn_icons.get(btn_text)
            if icon_file and self._svg_path:
                icon_full = os.path.join(self._svg_path, icon_file)
                if os.path.isfile(icon_full):
                    btn.setIcon(QIcon(icon_full))
            grid_layout.addWidget(btn, row, col)
            col += 1
            if not col > 2:
                continue
            col = 0
            row += 1
            continue
        buttons_layout.addWidget(grid_widget)
        buttons_layout.addStretch()
        scroll.setWidget(scroll_content)
        left_layout.addWidget(scroll)
        main_layout.addWidget(left_panel, 3)
        terminal_frame = QFrame()
        terminal_frame.setStyleSheet('\n            QFrame {\n                background-color: #1e1e1e;\n                border-radius: 8px;\n                padding: 10px;\n            }\n        ')
        terminal_layout = QVBoxLayout(terminal_frame)
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("\n            QTextEdit {\n                background-color: #1e1e1e;\n                color: white;\n                border: none;\n                font-family: 'Consolas', monospace;\n                font-size: 9pt;\n            }\n        ")
        terminal_layout.addWidget(self.log_area)
        self._show_welcome_message()
        main_layout.addWidget(terminal_frame, 2)
    def update_device_info(self):
        '''Atualiza informa├º├Áes do dispositivo periodicamente de forma segura'''
        if hasattr(self, '_updating_info') and self._updating_info:
            return
        self._updating_info = True
        try:
            def update_in_thread():
                try:
                    is_connected = False
                    try:
                        is_connected = self.adb.check_device()
                    except Exception as e:
                        self.logger.error('Erro ao verificar conex├úo:: %s', e)
                        QTimer.singleShot(0, (lambda: self.log_area.append('[!] Erro ao verificar conex├úo: Verifique o dispositivo.')))
                        try:
                            pass
                        except Exception as e:
                            self.logger.error('Erro ao atualizar informa├º├Áes:: %s', e)
                            QTimer.singleShot(0, (lambda: self.log_area.append('[!] Erro ao atualizar informa├º├Áes: Verifique o dispositivo.')))
                        self._updating_info = False
                        return
                    else:
                        if is_connected:
                            def update_ui_connected():
                                self.device_info.setText('Dispositivo Motorola conectado')
                                self.bootloader_status.setText(self.tools.check_bootloader_status())
                                self.mdm_status.setText('MDM: Verificando...')
                                self.comm_status.setText('Comm Server: OK')
                            QTimer.singleShot(0, update_ui_connected)
                except Exception as e:
                    self.logger.error('Erro ao atualizar informa├º├Áes:: %s', e)
                    QTimer.singleShot(0, (lambda: self.log_area.append('[!] Erro ao atualizar informa├º├Áes: Verifique o dispositivo.')))
                    try:
                        is_connected = False
                        if is_connected:
                            def update_ui_connected():
                                self.device_info.setText('Dispositivo Motorola conectado')
                                self.bootloader_status.setText(self.tools.check_bootloader_status())
                                self.mdm_status.setText('MDM: Verificando...')
                                self.comm_status.setText('Comm Server: OK')
                            QTimer.singleShot(0, update_ui_connected)
                        else:
                            def update_ui_disconnected():
                                self.device_info.setText('Dispositivo n├úo detectado')
                                self.bootloader_status.setText('Bootloader: N/A')
                                self.mdm_status.setText('MDM: N/A')
                                self.comm_status.setText('Comm Server: N/A')
                            QTimer.singleShot(0, update_ui_disconnected)
                    except Exception as e:
                        self.logger.error('Erro ao atualizar informa├º├Áes:: %s', e)
                        QTimer.singleShot(0, (lambda: self.log_area.append('[!] Erro ao atualizar informa├º├Áes: Verifique o dispositivo.')))
                    finally:
                        self._updating_info = False
                self._updating_info = False
            threading.Thread(target=update_in_thread, daemon=True).start()
            return
        except Exception as e:
            self._updating_info = False
            self.logger.error('Erro ao atualizar informa├º├Áes:: %s', e)
            self.log_area.append('[ERRO] Erro ao atualizar informa├º├Áes: Verifique o dispositivo.')
    def check_device(self):
        '''Verifica se ├® um dispositivo Motorola e atualiza a interface de forma segura'''
        if hasattr(self, '_checking_in_progress') and self._checking_in_progress:
            return
        self._checking_in_progress = True
        self.last_check_time = time.time()
        try:
            self.device_info.setText('Verificando dispositivo...')
            self.model_info.setText('Modelo: Verificando...')
            self.hardware_info.setText('Hardware: Verificando...')
            self.bootloader_status.setText('Bootloader: Verificando...')
            self.frp_status.setText('FRP: Verificando...')
            self.slot_info.setText('Slots: Verificando...')
            def check_in_thread():
                try:
                    is_fastboot = False
                    is_adb = False
                    device_info_result = ''
                    self.logger.debug('Verificando dispositivo fastboot...')
                    try:
                        is_fastboot = self.adb.check_fastboot_device()
                        self.logger.debug(f'Fastboot detectado: {is_fastboot}')
                    except Exception as e:
                        self.logger.debug('Erro ao verificar fastboot: %s', e)
                    else:
                        if not is_fastboot:
                            self.logger.debug('Verificando dispositivo ADB...')
                except Exception as e:
                    self.logger.debug('Erro geral na verifica├º├úo: %s', e)
                    self.logger.error('Erro ao verificar dispositivo:: %s', e)
                    self.append_log_signal.emit('[ERRO] Erro ao verificar dispositivo: Verifique a conexao.')
                    self.update_status_signal.emit('', 'none')
                if is_fastboot:
                    self.logger.debug('Obtendo informa├º├Áes do fastboot...')
                elif is_adb:
                    self.logger.debug('Modo ADB detectado...')
                    self.append_log_signal.emit('[OK] Dispositivo Motorola em modo ADB detectado')
                    try:
                        try:
                            device_info_result = self.tools.check_device_info()
                            self.logger.debug(f'Informa├º├Áes obtidas: {len(device_info_result) if device_info_result else 0} caracteres')
                            self.update_status_signal.emit(device_info_result, 'fastboot')
                            self.append_log_signal.emit('[OK] Dispositivo Motorola em modo fastboot detectado')
                            if device_info_result:
                                self.append_log_signal.emit(device_info_result)
                        except Exception as e:
                            self.logger.debug('Erro ao obter info ADB: %s', e)
                            self.update_status_signal.emit('', 'adb')
                            try:
                                adb_info = self._get_adb_device_info()
                                if adb_info:
                                    self.update_status_signal.emit(adb_info, 'adb')
                                    self.append_log_signal.emit(adb_info)
                                else:
                                    self.update_status_signal.emit('', 'adb')
                            except Exception as e:
                                self.logger.debug('Erro ao obter informa├º├Áes fastboot: %s', e)
                                self.update_status_signal.emit('', 'fastboot')
                                self.append_log_signal.emit('[OK] Dispositivo em fastboot (erro ao obter detalhes)')
                            finally:
                                self._checking_in_progress = False
                    except Exception as e:
                        self.logger.debug('Erro geral na verifica├º├úo: %s', e)
                        self.logger.error('Erro ao verificar dispositivo:: %s', e)
                        self.append_log_signal.emit('[ERRO] Erro ao verificar dispositivo: Verifique a conexao.')
                        self.update_status_signal.emit('', 'none')
                    finally:
                        self._checking_in_progress = False
                    self.append_log_signal.emit('[i] Para informacoes de bootloader/FRP, reinicie em modo fastboot')
                else:
                    try:
                        self.logger.debug('Nenhum dispositivo detectado')
                        self.update_status_signal.emit('', 'none')
                        self.append_log_signal.emit('[!] Nenhum dispositivo Motorola detectado')
                        self.append_log_signal.emit('[i] Conecte um dispositivo em modo fastboot ou ADB')
                    except Exception as e:
                        self.logger.debug('Erro geral na verifica├º├úo: %s', e)
                        self.logger.error('Erro ao verificar dispositivo:: %s', e)
                        self.append_log_signal.emit('[ERRO] Erro ao verificar dispositivo: Verifique a conexao.')
                        self.update_status_signal.emit('', 'none')
                    finally:
                        self._checking_in_progress = False
            threading.Thread(target=check_in_thread, daemon=True).start()
            return
        except Exception as e:
            self._checking_in_progress = False
            self.device_info.setText('Erro ao verificar dispositivo')
            self.logger.error('Erro:: %s', e)
            self.log_area.append('[ERRO] Erro: Verifique o dispositivo.')
    def _get_adb_device_info(self):
        '''Obt├®m informa├º├Áes detalhadas do dispositivo em modo ADB'''
        try:
            info = []
            info.append(' === INFORMA├ç├òES DO DISPOSITIVO (ADB) ===')
            props = [('ro.product.model', 'Modelo'), ('ro.product.brand', 'Marca'), ('ro.product.device', 'Device'), ('ro.serialno', 'Serial'), ('ro.build.version.release', 'Android'), ('ro.build.version.sdk', 'SDK'), ('ro.build.version.security_patch', 'Patch Seguran├ºa'), ('ro.product.cpu.abi', 'Arquitetura'), ('ro.board.platform', 'Chipset'), ('ro.build.id', 'Build ID'), ('ro.build.display.id', 'Build Display'), ('ro.build.fingerprint', 'Fingerprint'), ('gsm.sim.state', 'Estado SIM'), ('gsm.operator.alpha', 'Operadora')]
            for prop, label in props:
                pass
            try:
                value = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'getprop', prop]).strip()
                if value:
                    if value not in ('', 'unknown', 'null'):
                        info.append(f' {label}: {value}')
            except Exception:
                pass
        except Exception as e:
            self.logger.debug('Erro ao obter info ADB: %s', e)
        try:
            imei_cmd = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'service', 'call', 'iphonesubinfo', '1']).strip()
            if imei_cmd and 'Parcel' in imei_cmd:
                import re
                matches = re.findall("'([0-9.]+)'", imei_cmd)
                if matches:
                    imei = ''.join(matches).replace('.', '')
                    if len(imei) >= 14:
                        info.append(f'IMEI: {imei[:15]}')
        except Exception:
            pass
        try:
            battery = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'dumpsys', 'battery']).strip()
            if battery:
                for line in battery.split('\n'):
                    if not 'level:' in line.lower():
                        continue
                    level = line.split(':')[-1].strip()
                    info.append(f'Bateria: {level}%')
                    break
        except Exception:
            pass
        try:
            try:
                storage = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'df', '/data']).strip()
                if storage:
                    lines = storage.split('\n')
                    if len(lines) > 1:
                        parts = lines[1].split()
                        if len(parts) >= 4:
                            try:
                                try:
                                    try:
                                        total_kb = int(parts[1].replace('K', '').replace('M', '000').replace('G', '000000'))
                                        total_gb = total_kb / 1048576
                                        info.append(f'Armazenamento: ~{total_gb:.0f}GB')
                                    except:
                                        pass
                                except Exception:
                                    pass
                            except Exception as e:
                                self.logger.debug('Erro ao obter info ADB: %s', e)
            except Exception:
                pass
        except Exception as e:
            self.logger.debug('Erro ao obter info ADB: %s', e)
        else:
            try:
                try:
                    try:
                        total_kb = int(parts[1].replace('K', '').replace('M', '000').replace('G', '000000'))
                        total_gb = total_kb / 1048576
                        info.append(f'Armazenamento: ~{total_gb:.0f}GB')
                    except:
                        pass
                except Exception:
                    pass
            except Exception as e:
                self.logger.debug('Erro ao obter info ADB: %s', e)
        if len(info) > 1:
            return '\n'.join(info)
    def update_device_status(self, device_info_text, mode):
        '''Atualiza o status do dispositivo na interface'''
        try:
            if mode == 'fastboot' and device_info_text and 'Ô£à' in device_info_text:
                lines = device_info_text.split('\n')
                info_data = {}
                for line in lines:
                    line = line.strip()
                    if not line or not line.startswith('Ô£à'):
                        continue
                    line = line.replace('Ô£à ', '')
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip().lower()
                        value = value.strip()
                        info_data[key] = value
                model = info_data.get('modelo', 'N├úo detectado')
                hardware = 'N├úo detectado'
                if 'cpu' in info_data:
                    hardware = info_data['cpu']
                elif 'ram' in info_data:
                    hardware = info_data['ram']
                elif 'emmc' in info_data:
                    hardware = f'Storage: {info_data['emmc']}'
                bootloader_raw = info_data.get('securestate', 'N/A')
                if 'locked' in bootloader_raw.lower():
                    bootloader_text = 'Bloqueado'
                    bootloader_color = '#e74c3c'
                elif 'unlocked' in bootloader_raw.lower():
                    bootloader_text = 'Desbloqueado'
                    bootloader_color = '#27ae60'
                else:
                    bootloader_text = 'Desconhecido'
                    bootloader_color = '#f39c12'
                frp_raw = info_data.get('frp state', 'N/A').lower()
                if 'no protection' in frp_raw or frp_raw == '0':
                    frp_text = 'SEM FRP'
                    frp_color = '#27ae60'
                elif 'protected' in frp_raw or frp_raw == '1':
                    frp_text = 'COM FRP'
                    frp_color = '#e74c3c'
                else:
                    frp_text = 'Desconhecido'
                    frp_color = '#f39c12'
                current_slot = info_data.get('current slot', 'N/A')
                slot_count = info_data.get('slot count', '')
                if current_slot != 'N/A':
                    slots_text = f'Slot {current_slot.upper()} ativo'
                    if slot_count:
                        slots_text += f' ({slot_count} slots)'
                else:
                    slots_text = 'N/A'
                self.device_info.setText('Dispositivo Motorola (Fastboot)')
                self.device_info.setStyleSheet('font-weight: bold; font-size: 10pt; color: #27ae60;')
                self.model_info.setText(f'Modelo: {model}')
                self.model_info.setStyleSheet('color: #ecf0f1; font-weight: 500; font-size: 8pt;')
                self.hardware_info.setText(f'CPU: {hardware}')
                self.hardware_info.setStyleSheet('color: #ecf0f1; font-weight: 500; font-size: 8pt;')
                self.bootloader_status.setText(f'Bootloader: {bootloader_text}')
                self.bootloader_status.setStyleSheet(f'color: {bootloader_color}; font-size: 8pt;')
                self.frp_status.setText(f'FRP: {frp_text}')
                self.frp_status.setStyleSheet(f'color: {frp_color}; font-size: 8pt;')
                self.slot_info.setText(f'Slots: {slots_text}')
                self.slot_info.setStyleSheet('color: #ecf0f1; font-weight: 500; font-size: 8pt;')
                return
            if mode == 'adb':
                pass
            try:
                info_data = {}
                if device_info_text and 'Ô£à' in device_info_text:
                    for line in device_info_text.split('\n'):
                        line = line.strip()
                        if not line.startswith('Ô£à'):
                            continue
                        if ':' in line:
                            line = line.replace('Ô£à ', '')
                            key, value = line.split(':', 1)
                            info_data[key.strip().lower()] = value.strip()
                model_info = info_data.get('modelo', 'Detectado')
                android_version = info_data.get('android', 'N/A')
                chipset = info_data.get('chipset', '')
                bateria = info_data.get('bateria', '')
                self.device_info.setText('Dispositivo Motorola (ADB)')
                self.device_info.setStyleSheet('font-weight: bold; font-size: 10pt; color: #27ae60;')
                self.model_info.setText(f'Modelo: {model_info}')
                self.model_info.setStyleSheet('color: #ecf0f1; font-weight: 500; font-size: 8pt;')
                hw_text = f'Android {android_version}'
                if chipset:
                    hw_text += f' | {chipset}'
                self.hardware_info.setText(f' {hw_text}')
                self.hardware_info.setStyleSheet('color: #ecf0f1; font-weight: 500; font-size: 8pt;')
                self.bootloader_status.setText('Bootloader: Requer Fastboot')
                self.bootloader_status.setStyleSheet('color: #f39c12; font-size: 8pt;')
                self.frp_status.setText('FRP: Requer Fastboot')
                self.frp_status.setStyleSheet('color: #f39c12; font-size: 8pt;')
                if bateria:
                    self.slot_info.setText(f'Bateria: {bateria}')
                else:
                    self.slot_info.setText('Slots: Requer Fastboot')
                self.slot_info.setStyleSheet('color: #ecf0f1; font-weight: 500; font-size: 8pt;')
            except Exception as e:
                self.logger.debug('Erro ao processar info ADB: %s', e)
                self.device_info.setText('Dispositivo Motorola (ADB)')
                self.device_info.setStyleSheet('font-weight: bold; font-size: 10pt; color: #f39c12;')
                self.model_info.setText('Modelo: Modo ADB ativo')
                self.model_info.setStyleSheet('color: #ecf0f1; font-weight: 500; font-size: 8pt;')
                self.hardware_info.setText('CPU: Use fastboot para detalhes')
                self.hardware_info.setStyleSheet('color: #f39c12; font-weight: 500; font-size: 8pt;')
                self.bootloader_status.setText('Bootloader: N/A')
                self.bootloader_status.setStyleSheet('color: #7f8c8d; font-size: 8pt;')
                self.frp_status.setText('FRP: N/A')
                self.frp_status.setStyleSheet('color: #7f8c8d; font-size: 8pt;')
                self.slot_info.setText('Slots: N/A (modo ADB)')
                self.slot_info.setStyleSheet('color: #7f8c8d; font-weight: 500; font-size: 8pt;')
            else:
                return
        except Exception as e:
            self.logger.debug('Erro ao atualizar status: %s', e)
            self.device_info.setText('Erro ao verificar dispositivo')
            self.device_info.setStyleSheet('font-weight: bold; font-size: 10pt; color: #e67e22;')
            self.model_info.setText('Modelo: Tente novamente')
            self.model_info.setStyleSheet('color: #7f8c8d; font-weight: 500; font-size: 8pt;')
            self.hardware_info.setText('CPU: Tente novamente')
            self.hardware_info.setStyleSheet('color: #7f8c8d; font-weight: 500; font-size: 8pt;')
            self.bootloader_status.setText('Bootloader: Erro')
            self.bootloader_status.setStyleSheet('color: #7f8c8d; font-size: 8pt;')
            self.frp_status.setText('FRP: Erro')
            self.frp_status.setStyleSheet('color: #7f8c8d; font-size: 8pt;')
            self.slot_info.setText('Slots: Tente novamente')
            self.slot_info.setStyleSheet('color: #7f8c8d; font-weight: 500; font-size: 8pt;')
    def _append_log(self, message):
        '''Slot thread-safe para adicionar mensagem ao log'''
        try:
            if hasattr(self, 'log_area'):
                if self.log_area:
                    self.log_area.append(message)
                    return
                return
        except Exception as e:
            self.logger.debug('Erro ao adicionar log: %s', e)
    def check_bootloader_status(self):
        '''Verifica status do bootloader'''
        result = self.tools.check_bootloader_status()
        self.log_area.append(result)
    def show_unlock_dialog(self):
        '''Mostra o di├ílogo de desbloqueio do bootloader'''
        dialog = UnlockDialog(self.tools, self)
        dialog.exec_()
    def fastboot_reboot(self):
        '''Reinicia o dispositivo via fastboot'''
        try:
            if not self.adb.check_fastboot_device():
                self.log_area.append('[!] Dispositivo precisa estar em modo fastboot!')
                return
            self.adb.execute_fastboot_command('reboot')
            self.log_area.append('[OK] Dispositivo reiniciando...')
            return
        except Exception as e:
            self.logger.error('Erro ao reiniciar:: %s', e)
            self.log_area.append('[ERRO] Erro ao reiniciar: Verifique o dispositivo.')
    def remove_mdm(self):
        '''Remove MDM do dispositivo'''
        try:
            if not self.adb.check_device():
                self.log_area.append('[!] Dispositivo precisa estar em modo normal (ADB)!')
                return
            reply = QMessageBox.warning(self, 'Remover MDM', 'Esta opera├º├úo ir├í remover o MDM do dispositivo.\nAlguns apps do sistema podem parar de funcionar.\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                result = self.tools.fix_mdm()
                self.log_area.append(result)
                return
        except Exception as e:
            self.logger.error('Erro ao remover MDM:: %s', e)
            self.log_area.append('[ERRO] Erro ao remover MDM: Verifique o dispositivo.')
    def fix_comm_server(self):
        '''Corrige Comm Server'''
        try:
            if not self.adb.check_fastboot_device():
                self.log_area.append('Dispositivo precisa estar em modo fastboot!')
                return
            reply = QMessageBox.warning(self, 'Fix Comm Server', "Esta opera├º├úo ├® indicada para dispositivos que apresentam:\n\nÔÇó Erro de 'Comm Server' ou servi├ºos indispon├¡veis\nÔÇó Falhas relacionadas ao CQA (Certified Quality Auditor)\nÔÇó Problemas de software ap├│s atualiza├º├Áes\n\nO processo ir├í:\n1. Apagar todos os dados\n2. Corrigir o erro de Comm Server\n3. Reiniciar o dispositivo\n\nDeseja continuar?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                result = self.tools.fix_comm_server()
                self.log_area.append(result)
                return
        except Exception as e:
            self.logger.error('Erro ao corrigir Comm Server:: %s', e)
            self.log_area.append('[ERRO] Erro ao corrigir Comm Server: Verifique o dispositivo.')
    def download_firmware(self):
        '''Abre o reposit├│rio de firmware da Motorola'''
        try:
            url = 'https://mirrors.lolinet.com/firmware/lenomola/'
            QDesktopServices.openUrl(QUrl(url))
            self.log_area.append('[i] Abrindo repositorio de firmware Motorola...')
            self.log_area.append('[i] Dica: Procure pelo modelo do seu dispositivo e baixe a versao mais recente.')
            return
        except Exception as e:
            self.logger.error('Erro ao abrir reposit├│rio:: %s', e)
            self.log_area.append('[ERRO] Erro ao abrir reposit├│rio: Verifique o dispositivo.')
    def execute_premium_motorola_id_5(self):
        '''
        Executa servi├ºo premium ID 5 (Motorola).
        Servi├ºo premium - Requer cr├®ditos
        Busca por ID 5 no banco (t├¡tulo din├ómico)
        '''
        try:
            from app.utils.premium_services_manager import get_premium_services_manager
            user_id = 1
            if hasattr(self.parent, 'user_id'):
                user_id = self.parent.user_id
            premium_manager = get_premium_services_manager()
            servico = premium_manager.buscar_servico_premium_por_id(5)
            if servico:
                titulo_servico = servico.get('titulo', 'Servi├ºo Premium')
            else:
                titulo_servico = 'Servi├ºo Premium'
            sucesso = premium_manager.abrir_servico_premium(titulo=titulo_servico, user_id=user_id, parent=self)
            if sucesso:
                self.log_area.append(f'Servi├ºo {titulo_servico} acessado')
                self.log_area.append('[OK] Servico premium aberto no navegador')
                return
            self.log_area.append(f'Acesso ao servi├ºo {titulo_servico} cancelado ou indispon├¡vel')
            return
        except Exception as e:
            self.log_area.append('Erro ao acessar servi├ºo premium')
            self.log_area.append('[!] Servico temporariamente indisponivel')
            QMessageBox.warning(self, 'Servi├ºo Indispon├¡vel', 'O servi├ºo est├í temporariamente indispon├¡vel.\n\nPor favor, tente novamente mais tarde.\n\nSuporte: (85) 99750-7465')
    def _show_welcome_message(self):
        '''Exibe mensagem de boas-vindas com termo de responsabilidade'''
        welcome_msg = '\n===============================================================================\n  TECH UNION SOLUTIONS - Tools Android\n  Ferramentas Profissionais para Tecnicos\n===============================================================================\n\nBem-vindo ao modulo de ferramentas Android.\nSelecione uma aba acima para acessar os recursos disponiveis.\n\n  IMPORTANTE:\n\n   - Este sistema foi desenvolvido para profissionais e estudos tecnicos.\n   - Recomendamos conhecimento previo antes de executar qualquer procedimento.\n   - Sempre faca backup dos dados antes de qualquer intervencao.\n\n  Sobre Desbloqueios e Remocao de Protecoes:\n\n   - Utilize apenas em dispositivos de sua propriedade legitima.\n   - Para fins de estudo, testes e aprendizado tecnico.\n   - Respeite sempre a propriedade e privacidade de terceiros.\n\n  Responsabilidades:\n\n   - Voce e responsavel pelo uso correto das ferramentas.\n   - A TECH UNION disponibiliza as ferramentas para fins profissionais.\n   - Use seu conhecimento tecnico com etica e responsabilidade.\n   - Em caso de duvidas, consulte nossa equipe de suporte.\n\n===============================================================================\n  Conecte seu dispositivo e selecione a operacao desejada.\n===============================================================================\n\n'
        self.log_area.setPlainText(welcome_msg)
    def showEvent(self, event):
        '''Quando a aba ├® mostrada, inicia o timer de maneira controlada'''
        super().showEvent(event)
        if hasattr(self, '_showing') and self._showing:
            return
        self._showing = True
        QTimer.singleShot(1000, self.clear_showing_flag)
    def clear_showing_flag(self):
        '''Limpa a flag de exibi├º├úo'''
        self._showing = False
    def delayed_check(self):
        '''Executa verifica├º├úo do dispositivo com atraso para n├úo travar a UI'''
        if not self.isVisible():
            return
        try:
            self.checking_device = True
            self.check_device()
        except Exception as e:
            self.logger.error('Erro ao verificar dispositivo:: %s', e)
            self.log_area.append('[ERRO] Erro ao verificar dispositivo: Verifique o dispositivo.')
        finally:
            self.checking_device = False
    def hideEvent(self, event):
        '''Quando a aba ├® escondida, para o timer e limpa recursos'''
        super().hideEvent(event)
        self.checking_device = False
        if hasattr(self, '_showing'):
            self._showing = False
    def show_frp_motorola_mtk(self):
        '''Abre a interface de FRP Models MTKs/SPD (BROM Mode)'''
        try:
            self.log_area.append('[i] Abrindo FRP Models MTKs/SPD (BROM Mode)...')
            from PyQt5.QtWidgets import QDialog, QVBoxLayout
            from PyQt5.QtGui import QIcon
            import os
            import sys
            union_unlock_path = os.path.join(os.path.dirname(__file__), 'union_unlock')
            if union_unlock_path not in sys.path:
                sys.path.insert(0, union_unlock_path)
            from moto.motorola import MotorolaWidget
            dialog = QDialog(self)
            dialog.setWindowTitle('FRP Models MTKs/SPD - TECH UNION')
            dialog.setMinimumSize(900, 550)
            from PyQt5.QtWidgets import QApplication
            screen = QApplication.primaryScreen()
            if screen:
                sg = screen.availableGeometry()
                w = min(1320, int(sg.width() * 0.85))
                h = min(820, int(sg.height() * 0.85))
                dialog.resize(w, h)
            else:
                dialog.resize(1100, 700)
            dialog.setModal(False)
            icon_path = os.path.join(union_unlock_path, 'img', 'logo_32.png')
            if os.path.exists(icon_path):
                dialog.setWindowIcon(QIcon(icon_path))
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(0, 0, 0, 0)
            motorola_widget = MotorolaWidget()
            layout.addWidget(motorola_widget)
            self._motorola_dialog = dialog
            dialog.show()
            self.log_area.append('[OK] Interface FRP Models MTKs/SPD aberta!')
            return
        except Exception as e:
            self.log_area.append('Erro ao abrir FRP Motorola. Tente novamente.')
            self.log_area.append('Se persistir, contate o suporte tecnico.')
            import logging
            logging.getLogger(__name__).error('show_frp_motorola_mtk falhou: %s', type(e).__name__)
