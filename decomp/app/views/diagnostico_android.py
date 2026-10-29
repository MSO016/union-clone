from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QMessageBox, QGroupBox, QGridLayout, QSizePolicy, QSplitter, QApplication, QScrollArea, QDialog, QTabWidget, QListWidget, QListWidgetItem, QFileDialog, QProgressDialog)
from PyQt5.QtCore import (Qt, QTimer, QThread, pyqtSignal, pyqtSlot)
from PyQt5.QtGui import QIcon, QFont
from app.utils.adb_manager import ADBManager
from app.views.tools_android import ToolsAndroid
from app.views.xiaomi_tools import XiaomiTools
from app.views.adware_tools import AdwareTools
from app.views.adb_app_manager_view import ADBAppManagerView
from app.views.adb_system_monitor_view import ADBSystemMonitorView
from app.views.diag_formatters import (format_device_info, format_storage_info, format_cpu_info)
from app.views.diag_parser_v2 import (parse_battery, parse_signal, parse_sensors, parse_touch, parse_storage, parse_memory, parse_thermal, parse_cpu, parse_identity, parse_camera, parse_wifi, parse_usb, parse_partitions, parse_system_events, parse_network, parse_audio)
from app.views.diag_formatters_v2 import (wrap_output, _LINE, format_battery as fmt_battery_v2, format_signal as fmt_signal_v2, format_sensors as fmt_sensors_v2, format_touch as fmt_touch_v2, format_storage as fmt_storage_v2, format_memory as fmt_memory_v2, format_thermal as fmt_thermal_v2, format_cpu as fmt_cpu_v2, format_identity as fmt_identity_v2, format_camera as fmt_camera_v2, format_wifi as fmt_wifi_v2, format_usb as fmt_usb_v2, format_partitions as fmt_partitions_v2, format_system_events as fmt_system_events_v2, format_network as fmt_network_v2, format_audio as fmt_audio_v2)
from app.views.samsung_tools import SamsungTools
from app.utils.translation_manager import TranslationManager
import re
import os
import logging
import traceback
import time
import threading
import subprocess
try:
    from app.views.ui.diag_theme import (qss_group_box, qss_btn_primary, qss_btn_diagnostic, qss_btn_success, qss_btn_danger, qss_status_label, qss_log_area, qss_scroll_area, qss_battery_label, qss_error_dialog, qss_msg_box_info, STATUS_CONNECTED_BG, STATUS_DISCONNECTED_BG, LOG_ERROR_COLOR, LOG_WARN_COLOR, WHITE, TEXT, PRIMARY, UNION_ACCENT, GREEN)
    _TEMA_DISPONIVEL = True
except ImportError:
    _TEMA_DISPONIVEL = False
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('DiagnosticoAndroid')
for _lib in ('botocore', 'boto3', 's3transfer', 'urllib3'):
    logging.getLogger(_lib).setLevel(logging.CRITICAL)
class CommandThread(QThread):
    '''Thread separada para executar comandos'''
    command_finished = pyqtSignal(str)
    command_started = pyqtSignal()
    command_error = pyqtSignal(str)
    progress_update = pyqtSignal(str)
    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.start_time = None
        self._is_running = True
    def run(self):
        try:
            self.start_time = time.time()
            logger.debug(f'Iniciando comando: {self.function.__name__}')
            self.command_started.emit()
            result = self.function(*self.args, **self.kwargs)
            if self._is_running:
                execution_time = time.time() - self.start_time
                logger.debug(f'Comando {self.function.__name__} completado em {execution_time:.2f} segundos')
                self.command_finished.emit(result if isinstance(result, str) else str(result))
                return
        except Exception as e:
            if self._is_running:
                logger.error(f'Erro no comando {self.function.__name__}: {str(e)}')
                logger.error(f'Traceback: {traceback.format_exc()}')
                self.command_error.emit(str(e))
    def stop(self):
        '''Para a execu├º├úo da thread'''
        self._is_running = False
class DiagnosticoAndroid(QMainWindow):
    def __init__(self, parent=None, adb_manager=None):
        super().__init__(parent)
        self.adb = adb_manager or ADBManager()
        self.translation_manager = TranslationManager.get_instance()
        self.log_timer = QTimer()
        self.log_timer.timeout.connect(self.update_logs)
        self.log_timer.setInterval(100)
        self.command_thread = None
        self.active_command = None
        self.command_lock = threading.Lock()
        self.user_email = None
        if parent and hasattr(parent, 'user_email'):
            self.user_email = parent.user_email
        self.device_check_timer = QTimer()
        self.device_check_timer.timeout.connect(self.check_device_status)
        self.device_check_timer.setInterval(5000)
        logger.debug('Iniciando DiagnosticoAndroid')
        self.group_style = qss_group_box() if _TEMA_DISPONIVEL else '\n            QGroupBox {\n                font-size: 12px;\n                font-weight: bold;\n                padding: 8px;\n                margin-top: 3px;\n                border: 1px solid #E0E0E0;\n                border-radius: 3px;\n                background-color: #FFFFFF;\n            }\n            QGroupBox::title {\n                subcontrol-origin: margin;\n                left: 7px;\n                padding: 0 3px;\n                color: #1976D2;\n            }\n        '
        _LEGACY_TABS_QSS = '\n            QTabWidget::pane {\n                border: 1px solid #cccccc;\n                background: white;\n                padding: 5px;\n            }\n            QTabWidget::tab-bar {\n                alignment: left;\n            }\n            QTabBar::tab {\n                background: #555555;\n                border: 2px solid #333333;\n                padding: 8px 12px;\n                margin-right: 3px;\n                border-top-left-radius: 6px;\n                border-top-right-radius: 6px;\n                font-weight: bold;\n                min-width: 100px;\n                font-size: 13px;\n                color: white;\n            }\n            QTabBar::tab:selected {\n                border-bottom-color: white;\n                margin-top: -2px;\n                padding-top: 10px;\n            }\n            QTabBar::tab:!selected {\n                background-color: #9E9E9E;\n                color: white;\n            }\n            QTabBar::tab:hover:!selected {\n                background: #757575;\n            }\n        '
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName('abas_ferramentas')
        if self.tab_widget.tabBar() is not None:
            self.tab_widget.tabBar().setObjectName('tabs_ferramentas')
        self._tools_tabs_modern_active = False
        try:
            from app.views.ui.tools_tabs_theme import apply_tools_tabs_theme as _apply_tt_theme, is_modern_enabled as _is_tt_modern
            if _is_tt_modern() and _apply_tt_theme(self.tab_widget):
                self._tools_tabs_modern_active = True
            else:
                self.tab_widget.setStyleSheet(_LEGACY_TABS_QSS)
        except Exception as _tt_err:
            logger.warning('Tema moderno das abas Ferramentas indisponivel; usando legado: %s', type(_tt_err).__name__)
            self.tab_widget.setStyleSheet(_LEGACY_TABS_QSS)
        _bar = self.tab_widget.tabBar()
        if _bar is not None:
            _bar.setUsesScrollButtons(True)
            _bar.setExpanding(False)
            _bar.setElideMode(Qt.ElideNone)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        self.button_style = qss_btn_primary() if _TEMA_DISPONIVEL else '\n            QPushButton {\n                padding: 8px;\n                font-size: 12px;\n                min-width: 160px;\n                min-height: 40px;\n                background-color: #2196F3;\n                color: white;\n                border-radius: 4px;\n                font-weight: bold;\n                border: none;\n            }\n            QPushButton:hover {\n                background-color: #1976D2;\n            }\n            QPushButton:pressed {\n                background-color: #1565C0;\n            }\n            QPushButton:disabled {\n                background-color: #B0BEC5;\n            }\n        '
        self.diagnostic_button_style = qss_btn_diagnostic() if _TEMA_DISPONIVEL else '\n            QPushButton {\n                padding: 7px 6px;\n                font-size: 13px;\n                min-width: 120px;\n                max-width: 180px;\n                min-height: 38px;\n                max-height: 38px;\n                background-color: #2196F3;\n                color: white;\n                border-radius: 4px;\n                font-weight: bold;\n                border: none;\n            }\n            QPushButton:hover {\n                background-color: #1976D2;\n            }\n            QPushButton:pressed {\n                background-color: #1565C0;\n            }\n            QPushButton:disabled {\n                background-color: #B0BEC5;\n            }\n        '
        self.icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'icons'))
        self.svg_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources', 'icons_svg'))
        self.start_capture_btn = QPushButton(' Iniciar Captura')
        self.start_capture_btn.setIcon(QIcon(os.path.join(self.icon_path, 'play.png')))
        self.stop_capture_btn = QPushButton(' Parar Captura')
        self.stop_capture_btn.setIcon(QIcon(os.path.join(self.icon_path, 'stop.png')))
        self.clear_logs_btn = QPushButton(' Limpar Logs')
        self.clear_logs_btn.setIcon(QIcon(os.path.join(self.icon_path, 'clear.png')))
        self.power_status = QLabel('-')
        self.battery_level = QLabel('-')
        self.battery_health = QLabel('-')
        self.battery_cycles = QLabel('-')
        self.battery_temp = QLabel('-')
        self.battery_voltage = QLabel('-')
        self.battery_tech = QLabel('-')
        from app.utils.unlock_tools_manager import get_unlock_tools_manager
        self._unlock_tools_mgr = get_unlock_tools_manager()
        self._unlock_tools_mgr.extrair_com_progresso(self)
        self.setup_ui()
        self.create_menu()
    def handle_adb_error(self, error_msg):
        '''Funcao centralizada para tratamento de erros ADB'''
        logger.error(f'Erro ADB: {error_msg}')
        original_error = str(error_msg)
        error_msg_lower = original_error.lower()
        if original_error.strip().startswith('ÔØî'):
            friendly_message = original_error
        else:
            error_map = {'device not found': "Nenhum dispositivo detectado.\n\nClique primeiro em 'Verificar Conexao ADB' para\nconectar seu dispositivo antes de usar os diagnosticos.", 'unauthorized': "Dispositivo nao autorizado.\n\nNo celular, aceite a solicitacao de depuracao USB\ne clique novamente em 'Verificar Conexao ADB'.", 'offline': 'Dispositivo offline.\n\nReconecte o cabo USB e tente novamente.', 'no devices/emulators': "Nenhum dispositivo detectado.\n\nConecte o aparelho via USB e clique em\n'Verificar Conexao ADB'.", 'caminho': "Nenhum dispositivo conectado.\n\nAntes de usar os diagnosticos, conecte o\naparelho e clique em 'Verificar Conexao ADB'.", 'adb n├úo encontrado': 'ADB nao encontrado no sistema.\n\nVerifique se o platform-tools esta instalado.', 'failed to access device': 'Falha ao acessar dispositivo.', 'insufficient permissions': 'Permissoes insuficientes no dispositivo.', 'adb server': 'Erro no servidor ADB. Tente reconectar.', 'timeout': 'Tempo limite excedido. Tente novamente.'}
            friendly_message = "Nenhum dispositivo conectado.\n\nConecte o aparelho via USB e clique em\n'Verificar Conexao ADB' antes de usar os diagnosticos."
            for key, message in error_map.items():
                if not key in error_msg_lower:
                    continue
                friendly_message = message
                break
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Warning)
        error_dialog.setWindowTitle('Atencao')
        error_dialog.setText(friendly_message)
        error_dialog.setStyleSheet(qss_error_dialog() if _TEMA_DISPONIVEL else '\n            QMessageBox {\n                background-color: #f8f9fa;\n                min-width: 400px;\n            }\n            QLabel {\n                color: #333;\n                font-size: 12px;\n                padding: 10px;\n            }\n            QPushButton {\n                padding: 8px 16px;\n                background-color: #dc3545;\n                color: white;\n                border: none;\n                border-radius: 4px;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background-color: #c82333;\n            }\n        ')
        error_dialog.exec_()
    def check_device_connection(self):
        '''Verifica conex├úo do dispositivo antes de executar comandos'''
        try:
            if not self.adb.check_device():
                raise Exception('device not found')
            return True
        except Exception as e:
            self.handle_adb_error(e)
            return False
    def safe_execute(self, func):
        '''Wrapper para executar fun├º├Áes com verifica├º├úo de conex├úo'''
        if self.check_device_connection():
            try:
                return func()
            except Exception as e:
                self.handle_adb_error(e)
    def setup_ui(self):
        '''Configura a interface do usu├írio'''
        self.setWindowTitle('Diagn├│stico Android')
        screen = QApplication.primaryScreen().geometry()
        width = min(int(screen.width() * 0.85), 1600)
        height = min(int(screen.height() * 0.85), 1000)
        self.resize(width, height)
        self.setCentralWidget(self.tab_widget)
        diagnostico_widget = QWidget()
        diagnostico_layout = QHBoxLayout(diagnostico_widget)
        self.diag_layout = diagnostico_layout
        main_scroll = QScrollArea()
        self.diag_main_scroll = main_scroll
        main_scroll.setWidgetResizable(True)
        main_scroll.setFrameShape(QScrollArea.NoFrame)
        main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_scroll.setStyleSheet(qss_scroll_area() if _TEMA_DISPONIVEL else '\n            QScrollArea {\n                background: transparent;\n                border: none;\n            }\n            QScrollArea > QWidget > QWidget {\n                background: transparent;\n            }\n            QScrollBar:vertical {\n                border: none;\n                background: #f0f0f0;\n                width: 12px;\n                border-radius: 6px;\n            }\n            QScrollBar::handle:vertical {\n                background: #c0c0c0;\n                min-height: 20px;\n                border-radius: 6px;\n                margin: 2px;\n            }\n            QScrollBar::handle:vertical:hover {\n                background: #a0a0a0;\n            }\n            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {\n                height: 0px;\n            }\n            QScrollBar:horizontal {\n                border: none;\n                background: #f0f0f0;\n                height: 10px;\n                border-radius: 5px;\n            }\n            QScrollBar::handle:horizontal {\n                background: #c0c0c0;\n                min-width: 20px;\n                border-radius: 5px;\n                margin: 2px;\n            }\n            QScrollBar::handle:horizontal:hover {\n                background: #a0a0a0;\n            }\n            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {\n                width: 0px;\n            }\n        ')
        left_container = QWidget()
        self.diag_left_container = left_container
        left_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        left_container.setMinimumWidth(520)
        left_layout = QVBoxLayout(left_container)
        left_layout.setSpacing(10)
        status_group = QGroupBox('Status ADB')
        status_group.setStyleSheet(self.group_style)
        status_group_layout = QVBoxLayout()
        status_group_layout.setSpacing(5)
        self.status_label = QLabel('Aguardando verificacao de conexao...')
        self.status_label.setStyleSheet(qss_status_label(False) if _TEMA_DISPONIVEL else '\n            QLabel {\n                padding: 5px 10px;\n                border-radius: 4px;\n                background: #f44336;\n                color: white;\n                font-weight: bold;\n                font-size: 12px;\n            }\n        ')
        status_group_layout.addWidget(self.status_label)
        btn_verificar = QPushButton('Verificar Conex├úo ADB')
        btn_verificar.clicked.connect(self.check_connection)
        btn_verificar.setStyleSheet(self.button_style)
        status_group_layout.addWidget(btn_verificar)
        status_group.setLayout(status_group_layout)
        left_layout.addWidget(status_group)
        self.battery_group = QGroupBox('Informa├º├Áes da Bateria')
        self.battery_group.setStyleSheet(self.group_style)
        battery_layout = QVBoxLayout()
        battery_layout.setSpacing(5)
        battery_scroll = QScrollArea()
        battery_scroll.setWidgetResizable(True)
        battery_scroll.setFrameShape(QScrollArea.NoFrame)
        battery_scroll.setStyleSheet('\n            QScrollArea {\n                background: transparent;\n                border: none;\n            }\n            QScrollArea > QWidget > QWidget {\n                background: transparent;\n            }\n        ')
        battery_widget = QWidget()
        battery_info_layout = QVBoxLayout(battery_widget)
        battery_info_layout.setSpacing(5)
        battery_info_layout.setContentsMargins(0, 0, 0, 0)
        battery_grid = QGridLayout()
        battery_grid.setSpacing(5)
        battery_grid.setColumnStretch(1, 1)
        battery_label_style = qss_battery_label() if _TEMA_DISPONIVEL else '\n            QLabel {\n                font-size: 12px;\n                padding: 5px 10px;\n                background-color: #F5F5F5;\n                border-radius: 4px;\n            }\n            QLabel[labelType="title"] {\n                font-weight: bold;\n                color: #1976D2;\n                background-color: transparent;\n                padding: 5px 2px;\n            }\n            QLabel[labelType="value"] {\n                background-color: #F5F5F5;\n                font-weight: bold;\n                color: #212121;\n            }\n        '
        info_pairs = [('Fonte de Energia:', self.power_status), ('N├¡vel:', self.battery_level), ('Sa├║de:', self.battery_health), ('Ciclos:', self.battery_cycles), ('Temperatura:', self.battery_temp), ('Voltagem:', self.battery_voltage), ('Tecnologia:', self.battery_tech)]
        for row, (title, value_label) in enumerate(info_pairs):
            title_label = QLabel(title)
            title_label.setProperty('labelType', 'title')
            title_label.setStyleSheet(battery_label_style)
            title_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            value_label.setProperty('labelType', 'value')
            value_label.setStyleSheet(battery_label_style)
            value_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            battery_grid.addWidget(title_label, row, 0)
            battery_grid.addWidget(value_label, row, 1)
        battery_info_layout.addLayout(battery_grid)
        battery_scroll.setWidget(battery_widget)
        battery_layout.addWidget(battery_scroll)
        battery_button_container = QWidget()
        battery_button_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        battery_buttons = QHBoxLayout(battery_button_container)
        battery_buttons.setSpacing(10)
        battery_buttons.setContentsMargins(0, 5, 0, 0)
        btn_battery = QPushButton('Atualizar Info Bateria')
        btn_battery.clicked.connect(self.update_battery_info)
        btn_battery.setStyleSheet(self.button_style)
        btn_battery.setFixedWidth(150)
        btn_reset_stats = QPushButton('Resetar Estat├¡sticas')
        btn_reset_stats.clicked.connect(self.reset_battery_stats)
        btn_reset_stats.setStyleSheet(self.button_style)
        btn_reset_stats.setFixedWidth(150)
        btn_print_battery = QPushButton('Imprimir Relatorio')
        btn_print_battery.clicked.connect(self.print_battery_report)
        btn_print_battery.setStyleSheet(qss_btn_success() if _TEMA_DISPONIVEL else '\n            QPushButton {\n                padding: 8px;\n                font-size: 12px;\n                min-width: 140px;\n                min-height: 40px;\n                background-color: #27ae60;\n                color: white;\n                border-radius: 4px;\n                font-weight: bold;\n                border: none;\n            }\n            QPushButton:hover {\n                background-color: #229954;\n            }\n            QPushButton:pressed {\n                background-color: #1e8449;\n            }\n        ')
        btn_print_battery.setFixedWidth(150)
        battery_buttons.addStretch()
        battery_buttons.addWidget(btn_battery)
        battery_buttons.addWidget(btn_reset_stats)
        battery_buttons.addWidget(btn_print_battery)
        battery_buttons.addStretch()
        battery_layout.addWidget(battery_button_container)
        self.battery_group.setLayout(battery_layout)
        self.battery_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        left_layout.addWidget(self.battery_group)
        diag_group = QGroupBox('Diagn├│sticos')
        self.diag_group_diagnosticos = diag_group
        diag_group.setStyleSheet(self.group_style)
        diag_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        diag_layout = QGridLayout()
        diag_layout.setSpacing(5)
        diag_layout.setContentsMargins(8, 8, 8, 8)
        diagnostic_buttons = [('Info do Dispositivo', self.check_device_info, 'phone-flip.svg'), ('Armazenamento', self.check_storage, 'hdd.svg'), ('Info CPU', self.check_cpu, 'cpu.svg'), ('Info Mem├│ria', self.check_memory, 'arrow-clockwise.svg'), ('Eventos Sistema', self.check_system_events, 'graph-up.svg'), ('Verificar RFFE', self.check_rffe, 'reception-4.svg'), ('Testar USB', self.test_usb, 'pci-card-network.svg'), ('Info T├®rmica', self.check_thermal, 'thermometer-half.svg'), ('An├ílise de WiFi', self.check_wifi, 'wifi.svg'), ('An├ílise de Rede', self.check_network, 'globe.svg'), ('Sensores Verificar', self.check_sensors, 'robot.svg'), ('Panic Android', self.execute_panic_android, 'card-checklist.svg'), ('Mapa Parti├º├Áes', self.check_partition_map, 'folder-check.svg'), ('Tira Virus', self.detect_adware, 'shield-shaded.svg'), ('Info Touch', self.check_touch_info, 'keyboard.svg'), ('Info C├ómera', self.check_camera_info, 'camera.svg'), ('Diag. ├üudio', self.check_audio_diag, 'volume-up-fill.svg')]
        self.diag_grid_buttons = []
        cols = 3
        for i, (text, slot, svg_name) in enumerate(diagnostic_buttons):
            btn = self.create_diagnostic_button(text, slot, svg_name=svg_name)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            row = i // cols
            col = i % cols
            diag_layout.addWidget(btn, row, col)
            self.diag_grid_buttons.append(btn)
        diag_layout.setColumnStretch(0, 1)
        diag_layout.setColumnStretch(1, 1)
        diag_layout.setColumnStretch(2, 1)
        diag_group.setLayout(diag_layout)
        left_layout.addWidget(diag_group)
        system_group = QGroupBox('Controles de Sistema')
        system_group.setStyleSheet(self.group_style)
        system_layout = QHBoxLayout()
        system_layout.setSpacing(10)
        system_layout.setContentsMargins(5, 5, 5, 5)
        system_button_container = QWidget()
        system_button_layout = QHBoxLayout(system_button_container)
        system_button_layout.setSpacing(10)
        system_buttons = [('Reiniciar Sistema', self.reboot_to_system), ('Modo Recovery', self.reboot_to_recovery), ('Modo Fastboot', self.reboot_to_fastboot)]
        for text, slot in system_buttons:
            btn = self.create_button(text, slot)
            btn.setMinimumWidth(150)
            btn.setMaximumWidth(200)
            system_button_layout.addWidget(btn)
        system_button_layout.insertStretch(0)
        system_button_layout.addStretch()
        system_layout.addWidget(system_button_container)
        system_group.setLayout(system_layout)
        left_layout.addWidget(system_group, alignment=Qt.AlignCenter)
        left_layout.addStretch()
        main_scroll.setWidget(left_container)
        diagnostico_layout.addWidget(main_scroll)
        right_container = QWidget()
        self.diag_right_container = right_container
        right_container.setMinimumWidth(300)
        right_container.setMaximumWidth(800)
        right_layout = QVBoxLayout(right_container)
        right_layout.setSpacing(10)
        log_group = QGroupBox('Logs do Sistema')
        log_group.setStyleSheet(self.group_style)
        log_layout = QVBoxLayout()
        log_layout.setSpacing(5)
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet(qss_log_area() if _TEMA_DISPONIVEL else "\n            QTextEdit {\n                font-family: 'Consolas', 'Courier New', monospace;\n                font-size: 15px;\n                background-color: #2b2b2b;\n                color: #a9b7c6;\n                border: none;\n                border-radius: 3px;\n                padding: 8px;\n                min-height: 400px;\n            }\n            QScrollBar:vertical {\n                border: none;\n                background: #2b2b2b;\n                width: 10px;\n                margin: 0px;\n            }\n            QScrollBar::handle:vertical {\n                background: #404040;\n                min-height: 20px;\n                border-radius: 5px;\n            }\n            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {\n                height: 0px;\n            }\n        ")
        log_layout.addWidget(self.log_area)
        log_buttons = QHBoxLayout()
        log_buttons.setSpacing(5)
        self.start_capture_btn = QPushButton(' Iniciar Captura')
        self.start_capture_btn.setIcon(QIcon(os.path.join(self.icon_path, 'play.png')))
        self.start_capture_btn.clicked.connect(self.start_logging)
        self.start_capture_btn.setStyleSheet(self.button_style)
        self.start_capture_btn.setFixedWidth(150)
        self.stop_capture_btn = QPushButton(' Parar Captura')
        self.stop_capture_btn.setIcon(QIcon(os.path.join(self.icon_path, 'stop.png')))
        self.stop_capture_btn.clicked.connect(self.stop_logging)
        self.stop_capture_btn.setStyleSheet(self.button_style)
        self.stop_capture_btn.setFixedWidth(150)
        self.stop_capture_btn.setEnabled(False)
        self.clear_logs_btn = QPushButton(' Limpar Logs')
        self.clear_logs_btn.setIcon(QIcon(os.path.join(self.icon_path, 'clear.png')))
        self.clear_logs_btn.clicked.connect(self.clear_logs)
        self.clear_logs_btn.setStyleSheet(self.button_style)
        self.clear_logs_btn.setFixedWidth(150)
        self.print_log_btn = QPushButton(' Imprimir Log')
        self.print_log_btn.clicked.connect(self.print_current_log)
        self.print_log_btn.setStyleSheet(qss_btn_success(min_width=120) if _TEMA_DISPONIVEL else '\n            QPushButton {\n                padding: 8px;\n                font-size: 12px;\n                min-width: 120px;\n                min-height: 40px;\n                background-color: #27ae60;\n                color: white;\n                border-radius: 4px;\n                font-weight: bold;\n                border: none;\n            }\n            QPushButton:hover {\n                background-color: #229954;\n            }\n            QPushButton:pressed {\n                background-color: #1e8449;\n            }\n        ')
        self.print_log_btn.setFixedWidth(130)
        log_buttons.addWidget(self.start_capture_btn)
        log_buttons.addWidget(self.stop_capture_btn)
        log_buttons.addWidget(self.clear_logs_btn)
        log_buttons.addWidget(self.print_log_btn)
        log_buttons.addStretch()
        log_layout.addLayout(log_buttons)
        log_group.setLayout(log_layout)
        right_layout.addWidget(log_group)
        splitter = QSplitter()
        self.diag_splitter = splitter
        splitter.addWidget(right_container)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        diagnostico_layout.addWidget(splitter)
        diagnostico_tab_index = self.tab_widget.addTab(diagnostico_widget, 'Diagnostico')
        tools_widget = ToolsAndroid(self, adb_manager=self.adb)
        motorola_tab_index = self.tab_widget.addTab(tools_widget, 'Motorola')
        xiaomi_widget = XiaomiTools(self, adb_manager=self.adb)
        xiaomi_tab_index = self.tab_widget.addTab(xiaomi_widget, 'Xiaomi')
        samsung_tab_index = None
        try:
            samsung_widget = SamsungTools(self, adb_manager=self.adb)
            samsung_tab_index = self.tab_widget.addTab(samsung_widget, 'Samsung')
        except Exception as e:
            logger.warning('Aba Samsung nao carregada: %s', type(e).__name__)
        try:
            from app.views.union_unlock.edl.edl_main import EdlMainWidget
            edl_widget = EdlMainWidget(self)
            self._edl_qcom_widget = edl_widget
            edl_tab_index = self.tab_widget.addTab(edl_widget, 'QCOM EDL')
        except Exception as e:
            self._edl_qcom_widget = None
            edl_tab_index = None
            logger.warning('QCOM EDL nao carregado: %s', type(e).__name__)
        spd_tab_index = None
        try:
            from app.views.union_unlock.spd.spd_main import SPDToolsWidget
            spd_widget = SPDToolsWidget(self)
            self._spd_widget = spd_widget
            spd_tab_index = self.tab_widget.addTab(spd_widget, 'SPD')
        except Exception as e:
            self._spd_widget = None
            logger.warning('SPD nao carregado: %s', type(e).__name__)
        adware_widget = AdwareTools(self, adb_manager=self.adb)
        adware_tab_index = self.tab_widget.addTab(adware_widget, 'Tira Virus')
        hxd_tab_index = None
        _pai = self.parent() if callable(getattr(self, 'parent', None)) else None
        _hxd_permitido = hasattr(_pai, 'is_premium_user') and bool(_pai.is_premium_user) or hasattr(_pai, 'is_admin') and bool(_pai.is_admin)
        if _hxd_permitido:
            try:
                from app.views.union_unlock.hxd.gui.main_widget import HxdMainWidget
                hxd_widget = HxdMainWidget(self)
                self._hxd_widget = hxd_widget
                hxd_tab_index = self.tab_widget.addTab(hxd_widget, 'Tools')
            except Exception as e:
                self._hxd_widget = None
                logger.warning('HXD Editor nao carregado: %s', e)
        else:
            self._hxd_widget = None
        exy_tab_index = None
        _exy_permitido = hasattr(_pai, 'is_premium_user') and bool(_pai.is_premium_user) or hasattr(_pai, 'is_admin') and bool(_pai.is_admin)
        if _exy_permitido:
            try:
                from app.views.union_unlock.exy.gui.main_widget import ExyMainWidget
                exy_widget = ExyMainWidget(self)
                self._exy_widget = exy_widget
                exy_tab_index = self.tab_widget.addTab(exy_widget, 'Exynos')
            except Exception as e:
                self._exy_widget = None
                logger.warning('Exynos nao carregado: %s', e)
        else:
            self._exy_widget = None
        app_manager_widget = ADBAppManagerView(self, adb_manager=self.adb)
        app_manager_tab_index = self.tab_widget.addTab(app_manager_widget, 'Apps')
        system_monitor_widget = ADBSystemMonitorView(self, adb_manager=self.adb)
        system_monitor_tab_index = self.tab_widget.addTab(system_monitor_widget, 'Monitor')
        self.personalizar_aba(diagnostico_tab_index, '#1565C0', '#0D47A1', 'Diagnostico')
        self.personalizar_aba(motorola_tab_index, '#2E7D32', '#1B5E20', 'Motorola')
        self.personalizar_aba(xiaomi_tab_index, '#C62828', '#B71C1C', 'Xiaomi')
        if samsung_tab_index is not None:
            self.personalizar_aba(samsung_tab_index, '#6A4C93', '#4A148C', 'Samsung')
        if edl_tab_index is not None:
            self.personalizar_aba(edl_tab_index, '#D84315', '#BF360C', 'QCOM EDL')
        if spd_tab_index is not None:
            self.personalizar_aba(spd_tab_index, '#2471A3', '#1B4F72', 'SPD')
        self.personalizar_aba(adware_tab_index, '#0097A7', '#006064', 'Tira Virus')
        if hxd_tab_index is not None:
            self.personalizar_aba(hxd_tab_index, '#1428A0', '#0D1B69', 'Tools')
        if exy_tab_index is not None:
            self.personalizar_aba(exy_tab_index, '#E65100', '#BF360C', 'Exynos')
        self.personalizar_aba(app_manager_tab_index, '#FF6F00', '#E65100', 'Apps')
        self.personalizar_aba(system_monitor_tab_index, '#7B1FA2', '#4A148C', 'Monitor')
        self.tab_widget.setCurrentIndex(diagnostico_tab_index)
        self.on_tab_changed(diagnostico_tab_index)
        self._show_welcome_message()
        self._apply_diag_layout_responsive_fix()
    def personalizar_aba(self, index, cor_fundo, cor_borda, texto=None):
        '''
Personaliza a apar├¬ncia de uma aba espec├¡fica com cores e estilos customizados.
Modo MODERNO (default): apenas atualiza o texto se fornecido ÔÇö o
QSS escopado em tools_tabs_theme.py j├í cuida da apar├¬ncia uniforme.
A fun├º├úo ├® mantida apenas para compatibilidade com os chamadores
existentes (setup inicial e on_tab_changed).
Modo LEGADO (UI_TOOLS_TABS_MODERN=0 ou fallback): comportamento
original com cores por aba.
Args:
    index: ├ìndice da aba a ser personalizada
    cor_fundo: Cor de fundo da aba em formato hex (#RRGGBB)
    cor_borda: Cor da borda da aba em formato hex (#RRGGBB)
    texto: Texto da aba (opcional, mant├®m o atual se None)
'''
        tab_bar = self.tab_widget.tabBar()
        if texto:
            tab_bar.setTabText(index, texto)
        if getattr(self, '_tools_tabs_modern_active', False):
            return
        estilo_aba = f'\n            QTabBar::tab:!selected:#{tab_bar.objectName()}{{\n                background-color: {cor_fundo}90; /* 90% de opacidade para melhor visibilidade */\n                border: 2px solid {cor_borda}90; /* 90% de opacidade */\n                color: #222222;\n                font-weight: bold;\n            }}\n            QTabBar::tab:selected:#{tab_bar.objectName()} {{\n                background-color: {cor_fundo}; \n                border: 2px solid {cor_borda};\n                border-bottom-color: white;\n                color: white;\n            }}\n        '
        widget = self.tab_widget.widget(index)
        if widget:
            prop_name = f'aba_estilo_{index}'
            widget.setProperty(prop_name, estilo_aba)
        tab_bar.setTabTextColor(index, Qt.black if index != self.tab_widget.currentIndex() else Qt.white)
        if index == self.tab_widget.currentIndex():
            tab_bar.setStyleSheet(f'\n                QTabBar::tab:selected {{\n                    background-color: {cor_fundo};\n                    color: white;\n                    border: 2px solid {cor_borda};\n                    border-bottom-color: white;\n                }}\n                QTabBar::tab:!selected {{\n                    background-color: #5A5A5A;\n                    color: white;\n                    border: 2px solid #444444;\n                }}\n            ')
    @staticmethod
    def _resolve_diag_layout_profile(dpi_scale):
        '''
        Retorna um perfil de larguras adaptativo conforme a escala de DPI.
        Tabela calibrada para o conte├║do real da aba Diagn├│stico (3 colunas
        de bot├Áes na esquerda + painel de logs com 4 bot├Áes na direita).
        Faixas (escala_logical = logical_dpi / 96):
        - <1.15 (at├® 114%):       valores generosos (DPI normal).
        - 1.15-1.37 (115-137%):   intermedi├írio (HiDPI suave).
        - 1.38-1.52 (138-152%):   compacto (HiDPI 150%).
        - >=1.53 (160%+):         ultra-compacto (HiDPI alto, 175% t├¡pico).
        Soma left+right na faixa mais extrema = 740px, deixando ÔëÑ200px de
        folga em telas de 960px l├│gicos (1680├ù1050 @ 175%).
        '''
        try:
            scale = float(dpi_scale) if dpi_scale else 1.0
        except (TypeError, ValueError):
            scale = 1.0
        scale = max(1.0, scale)
        if scale >= 1.53:
            return {'tier': 'ultra_compact', 'left_min': 420, 'right_min': 380, 'initial_sizes': [620, 440], 'btn_widths': (100, 100, 95, 95), 'log_min_h': 180, 'grid_btn_min': 110, 'grid_btn_max': 160}
        if scale >= 1.38:
            return {'tier': 'compact', 'left_min': 460, 'right_min': 420, 'initial_sizes': [680, 500], 'btn_widths': (110, 110, 100, 100), 'log_min_h': 200, 'grid_btn_min': 120, 'grid_btn_max': 170}
        if scale >= 1.15:
            return {'tier': 'intermediate', 'left_min': 490, 'right_min': 460, 'initial_sizes': [740, 560], 'btn_widths': (115, 115, 105, 105), 'log_min_h': 200, 'grid_btn_min': 130, 'grid_btn_max': 180}
        return {'tier': 'normal', 'left_min': 520, 'right_min': 480, 'initial_sizes': [820, 600], 'btn_widths': (120, 120, 110, 110), 'log_min_h': 200, 'grid_btn_min': 140, 'grid_btn_max': 200}
    def _apply_diag_layout_responsive_fix(self):
        '''
Aplica ajustes responsivos p├│s-constru├º├úo do layout da aba Diagn├│stico.
Corrige (de forma idempotente, defensiva e adaptativa por DPI):
- Splitter degenerado (que tinha apenas 1 filho).
- MaximumWidth artificial no painel direito.
- MinimumWidth excessivo no painel esquerdo.
- Bot├Áes de log com largura fixa que transbordam em telas estreitas.
- min-height excessivo na ├írea de log.
- **Adapta valores ao DPI** para evitar overflow em escala 175%
  (Windows HiDPI), preservando UX em DPI normal.
Controlado por env var UI_DIAG_LAYOUT_FIX (default "1"). Em qualquer
falha interna, faz log e mant├®m o layout original (zero impacto).
'''
        try:
            btn.setMinimumWidth(min_w)
            btn.setMaximumWidth(QWIDGETSIZE_MAX)
            btn.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
            diag_btns = getattr(self, 'diag_grid_buttons', None) or []
            if diag_btns:
                grid_min = profile.get('grid_btn_min', 120)
                grid_max = profile.get('grid_btn_max', 180)
                for btn in diag_btns:
                    pass
            try:
                btn.setMinimumWidth(grid_min)
                btn.setMaximumWidth(grid_max)
                btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            except Exception:
                pass
            else:
                logger.info('Layout responsivo aplicado com sucesso.')
        except Exception as e:
            logger.warning('Layout fix nao aplicado (mantendo legado): %s', type(e).__name__)
    def _show_welcome_message(self):
        '''Mensagem inicial do ambiente de diagnostico ADB.'''
        self.log_area.clear()
        _W = 'ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ'
        _S = 'ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ'
        lines = [_W, '  TECH UNION SOLUTIONS', '  Diagnostico Android via ADB', _W, '', '  Este ambiente coleta dados do dispositivo', '  conectado via USB (modo depuracao ADB).', '', '  Os resultados ajudam a identificar:', '    - Estado do hardware (touch, audio, camera)', '    - Saude da bateria e temperatura', '    - Rede, sensores e armazenamento', '    - Eventos criticos do sistema', '', _S, '  Como usar:', _S, '  1. Conecte o dispositivo via cabo USB', '  2. Ative a Depuracao USB no dispositivo', "  3. Clique em 'Verificar Conexao ADB' acima", '  4. Execute os diagnosticos desejados', '', _S, '  Dicas para melhores resultados:', _S, '  - Mantenha a tela do dispositivo ligada', '  - Use cabo original (evite hubs USB)', '  - Aceite a autorizacao de depuracao no device', '  - Combine mais de um diagnostico para cruzar', '    dados e confirmar hipoteses', '', _S, '  Observacoes importantes:', _S, '  - Resultados podem variar entre fabricantes', '  - Dados refletem o estado no momento da coleta', '  - Em caso de duvida, repita o teste', '  - Seu feedback melhora a ferramenta', '', _W, '  Responsabilidades:', '', '  Voce e responsavel pelo uso correto das', '  ferramentas. A TECH UNION disponibiliza', '  os recursos para fins profissionais.', '  Use seu conhecimento tecnico com etica', '  e responsabilidade.', _W, '', '  Feito de tecnicos para tecnicos.', '']
        self.log_area.append('\n'.join(lines))
    def create_button(self, text, slot, icon_name=None):
        btn = QPushButton(f' {text}' if icon_name else text)
        if icon_name:
            btn.setIcon(QIcon(os.path.join(self.icon_path, f'{icon_name}.png')))
        btn.setStyleSheet(self.button_style)
        btn.clicked.connect(slot)
        return btn
    def create_diagnostic_button(self, text, slot, icon_name=None, svg_name=None):
        '''Cria bot├Áes espec├¡ficos para diagn├│stico com ├¡cone SVG.'''
        btn = QPushButton(f' {text}')
        if svg_name and hasattr(self, 'svg_path'):
            svg_full = os.path.join(self.svg_path, svg_name)
            if os.path.isfile(svg_full):
                btn.setIcon(QIcon(svg_full))
        elif icon_name:
            btn.setIcon(QIcon(os.path.join(self.icon_path, f'{icon_name}.png')))
        btn.setStyleSheet(self.diagnostic_button_style)
        btn.clicked.connect(slot)
        tooltip_map = {'Info do Dispositivo': 'Exibe informa├º├Áes detalhadas sobre o dispositivo Android conectado', 'Armazenamento': 'Analisa o uso de armazenamento e detecta problemas de espa├ºo', 'Info CPU': 'Mostra informa├º├Áes do processador e detecta problemas de performance', 'Info Mem├│ria': 'Verifica uso de RAM e detecta vazamentos de mem├│ria', 'Eventos Sistema': 'Analisa eventos do sistema para identificar erros', 'Verificar RFFE': 'Testa conectividade de rede e sinal m├│vel', 'Testar USB': 'Diagn├│stica problemas de conex├úo USB', 'Info T├®rmica': 'Monitora temperatura e detecta superaquecimento', 'An├ílise de WiFi': 'Analisa conectividade WiFi e problemas de rede', 'An├ílise de Rede': 'Diagn├│stica problemas gerais de conectividade', 'Sensores Verificar': 'Testa funcionamento dos sensores do dispositivo', 'Panic Android': 'Gera relat├│rio completo de diagn├│stico (bugreport)', 'Mapa Parti├º├Áes': 'Lista todas as parti├º├Áes do dispositivo', 'Tira Virus': 'Detecta e remove aplicativos maliciosos e adware'}
        if text in tooltip_map:
            btn.setToolTip(tooltip_map[text])
        return btn
    def check_connection(self):
        '''Verifica conexao ADB com kill/start server para tentativa limpa'''
        try:
            if self.adb.adb_path:
                try:
                    self.adb._run_adb_command([self.adb.adb_path, 'kill-server'], timeout=5)
                except Exception:
                    pass
            try:
                self.adb._run_adb_command([self.adb.adb_path, 'start-server'], timeout=10)
            except Exception:
                pass
            else:
                if self.adb.check_device():
                    self.update_status_label(True)
                    self.log_area.clear()
                    self.log_area.append('\n  Dispositivo conectado com sucesso!\n  Diagnosticos prontos para uso.\n')
                    return
                self.update_status_label(False)
                self.log_area.clear()
                self.log_area.append('\n  Nenhum dispositivo detectado.\n\n  Verifique:\n  - Cabo USB conectado\n  - Depuracao USB ativada no celular\n  - Aceite a autorizacao na tela do aparelho\n')
        except Exception as e:
            logger.error(f'Erro ao verificar conexao: {e}')
            self.update_status_label(False)
            self.handle_adb_error(str(e))
    def parse_battery_info(self, info_str):
        '''Converte a sa├¡da do dumpsys battery em um dicion├írio'''
        info_dict = {}
        for line in info_str.split('\n'):
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                info_dict[key.strip()] = value.strip()
        return info_dict
    def update_battery_info(self):
        '''Atualiza informa├º├Áes da bateria com verifica├º├úo'''
        def _update():
            if not self.adb.adb_path:
                logger.warning('ADB n├úo inicializado ao atualizar bateria')
                return
            try:
                result = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'dumpsys battery'])
                info = self.parse_battery_info(result)
                if info:
                    self.power_status.setText(info.get('AC powered', 'USB') if info.get('AC powered', 'false') == 'true' else 'USB' if info.get('USB powered', 'false') == 'true' else 'Bateria')
                    self.battery_level.setText(f'{info.get('level', '-')}%')
                    health_code = info.get('health', '1')
                    self.battery_health.setText(f'{self.get_health_status(health_code)}')
                    temp_val = float(info.get('temperature', '0')) / 10
                    if temp_val > 45:
                        self.battery_temp.setText(f'{temp_val:.1f}┬░C (ALTA)')
                    elif temp_val < 5:
                        self.battery_temp.setText(f'{temp_val:.1f}┬░C (BAIXA)')
                    else:
                        self.battery_temp.setText(f'{temp_val:.1f}┬░C')
                    volt_raw = int(info.get('voltage', '0'))
                    volt_v = volt_raw / 1000
                    if volt_raw < 3300:
                        self.battery_voltage.setText(f'{volt_v:.2f}V (Critica)')
                    elif volt_raw < 3700:
                        self.battery_voltage.setText(f'{volt_v:.2f}V (Baixa)')
                    elif volt_raw > 4400:
                        self.battery_voltage.setText(f'{volt_v:.2f}V (Alta)')
                    else:
                        self.battery_voltage.setText(f'{volt_v:.2f}V')
                    self.battery_tech.setText(info.get('technology', '-'))
                    self._update_battery_cycles()
                    return
            except Exception as e:
                logger.error(f'Erro ao atualizar info bateria: {str(e)}')
        self.safe_execute(_update)
    def _update_battery_cycles(self):
        '''Atualiza campo de ciclos de carga da bateria'''
        try:
            dump = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'dumpsys battery'])
            cycles = None
            for line in dump.split('\n'):
                if 'mSavedBatteryUsage' in line:
                    try:
                        try:
                            raw_usage = int(line.split(':')[1].strip())
                            cycles = raw_usage // 100
                        except (ValueError, IndexError):
                            continue
                    except Exception:
                        self.battery_cycles.setText('Indisponivel')
        except Exception:
            self.battery_cycles.setText('Indisponivel')
        if cycles is not None:
            if cycles < 100:
                self.battery_cycles.setText(f'{cycles} (Nova)')
                return
        self.battery_cycles.setText('Indisponivel')
        try:
            if cycles < 300:
                self.battery_cycles.setText(f'{cycles} (Uso moderado)')
                return
            if cycles < 500:
                self.battery_cycles.setText(f'{cycles} (Uso intenso)')
                return
            self.battery_cycles.setText(f'{cycles} (Desgaste elevado)')
            return
        except Exception:
            self.battery_cycles.setText('Indisponivel')
    def reset_battery_stats(self):
        '''Reseta estat├¡sticas da bateria'''
        try:
            reply = QMessageBox.question(self, 'Confirmar Reset', 'Deseja resetar as estat├¡sticas da bateria?\nIsso ir├í limpar o hist├│rico de uso.', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.adb._run_adb_command([self.adb.adb_path, 'shell', 'dumpsys batterystats --reset'])
                QMessageBox.information(self, 'Sucesso', 'Estat├¡sticas da bateria resetadas com sucesso!')
                return
        except Exception as e:
            self.show_error('Erro ao Resetar Estat├¡sticas', e)
    def print_current_log(self):
        '''Imprime o conteudo atual do log'''
        try:
            from app.utils.report_printer import ReportPrinter
            log_content = self.log_area.toPlainText()
            if not log_content or not log_content.strip():
                QMessageBox.warning(self, 'Aviso', 'Nao ha log para imprimir.\nCapture logs primeiro.')
                return
            printer = ReportPrinter(user_email=self.user_email)
            printer.print_log(log_content, title='Log do Dispositivo', parent=self)
            return
        except Exception as e:
            logger.error(f'Erro ao imprimir log: {e}')
            QMessageBox.critical(self, 'Erro', f'Erro ao imprimir:\n{str(e)}')
    def print_battery_report(self):
        '''Imprime relatorio de bateria'''
        try:
            from app.utils.report_printer import ReportPrinter
            battery_info = {}
            if hasattr(self, 'power_status') and self.power_status.text():
                battery_info['Fonte de Energia'] = self.power_status.text()
            if hasattr(self, 'battery_level') and self.battery_level.text():
                battery_info['Nivel'] = self.battery_level.text()
            if hasattr(self, 'battery_health') and self.battery_health.text():
                battery_info['Saude'] = self.battery_health.text()
            if hasattr(self, 'battery_temp') and self.battery_temp.text():
                battery_info['Temperatura'] = self.battery_temp.text()
            if hasattr(self, 'battery_voltage') and self.battery_voltage.text():
                battery_info['Voltagem'] = self.battery_voltage.text()
            if hasattr(self, 'battery_tech') and self.battery_tech.text():
                battery_info['Tecnologia'] = self.battery_tech.text()
        except Exception as e:
            logger.error(f'Erro ao imprimir relatorio de bateria: {e}')
            QMessageBox.critical(self, 'Erro', f'Erro ao imprimir:\n{str(e)}')
        try:
            dados_validos = {k: v for k, v in battery_info.items() if v if v.strip() if v != '-'}
            if not dados_validos:
                QMessageBox.warning(self, 'Aviso', "Nao ha dados de bateria.\nClique em 'Atualizar Info Bateria' primeiro.")
                return
            device_info = {}
            if hasattr(self, 'device_model_label') and self.device_model_label.text():
                device_info['Modelo'] = self.device_model_label.text()
            if hasattr(self, 'device_serial_label') and self.device_serial_label.text():
                device_info['Serial'] = self.device_serial_label.text()
            printer = ReportPrinter(user_email=self.user_email)
            printer.print_battery_report(dados_validos, device_info=device_info if device_info else None, parent=self)
            return
        except Exception as e:
            logger.error(f'Erro ao imprimir relatorio de bateria: {e}')
            QMessageBox.critical(self, 'Erro', f'Erro ao imprimir:\n{str(e)}')
    def execute_command(self, function, *args, **kwargs):
        '''Executa um comando em uma thread separada com monitoramento'''
        try:
            if not self.adb.adb_path:
                self.handle_adb_error('device not found')
                return
        except Exception as e:
            logger.error(f'Erro ao executar comando: {str(e)}')
            logger.error(f'Traceback: {traceback.format_exc()}')
            self.handle_adb_error(str(e))
        try:
            if not self.adb.check_device():
                self.handle_adb_error('device not found')
                return
        except Exception:
            self.handle_adb_error('device not found')
        try:
            if not self.command_lock.acquire(blocking=False):
                logger.warning('Comando em execucao, ignorando nova solicitacao')
                return
        except Exception as e:
            logger.error(f'Erro ao executar comando: {str(e)}')
            logger.error(f'Traceback: {traceback.format_exc()}')
            self.handle_adb_error(str(e))
        try:
            logger.debug(f'Preparando para executar comando: {function.__name__}')
            if function.__name__ == 'detect_malicious_apps':
                logger.debug('Detectando execu├º├úo de detec├º├úo de adware - executando na thread principal')
                self.active_command = function.__name__
                self.on_command_started()
                try:
                    try:
                        result = function(*args, **kwargs)
                        self.on_command_finished(result if isinstance(result, str) else str(result))
                    except Exception as e:
                        logger.error(f'Erro na detec├º├úo de adware: {str(e)}')
                        self.on_command_error(str(e))
                finally:
                    pass
                try:
                    self.command_lock.release()
                except Exception as e:
                    logger.error(f'Erro ao executar comando: {str(e)}')
                    logger.error(f'Traceback: {traceback.format_exc()}')
                    self.handle_adb_error(str(e))
                return
            if self.command_thread and self.command_thread.isRunning():
                logger.warning('Cancelando comando anterior')
                self.command_thread.stop()
                self.command_thread.wait()
                self.command_thread.disconnect()
                self.command_thread = None
            self.command_thread = CommandThread(function, *args, **kwargs)
            self.active_command = function.__name__
            self.command_thread.command_started.connect(self.on_command_started)
            self.command_thread.command_finished.connect(self.on_command_finished)
            self.command_thread.command_error.connect(self.on_command_error)
            logger.debug('Iniciando thread do comando')
            self.command_thread.start()
        finally:
            try:
                self.command_lock.release()
            except Exception as e:
                logger.error(f'Erro ao executar comando: {str(e)}')
                logger.error(f'Traceback: {traceback.format_exc()}')
                self.handle_adb_error(str(e))
    def on_command_started(self):
        '''Manipula o inicio do comando'''
        logger.debug(f'Comando iniciado: {self.active_command}')
        self.disable_buttons(True)
        self._cmd_start_time = __import__('time').time()
        self.log_area.clear()
        self.log_area.append('\n  Processando...\n')
    def on_command_finished(self, result):
        '''Manipula a conclusao do comando'''
        try:
            logger.debug(f'Comando finalizado: {self.active_command}')
            import time as _time
            elapsed_ms = None
            if hasattr(self, '_cmd_start_time') and self._cmd_start_time:
                elapsed_ms = int((_time.time() - self._cmd_start_time) * 1000)
                self._cmd_start_time = None
            if self.active_command == 'check_device_info' and isinstance(result, str):
                try:
                    import ast
                    device_info = {}
                    if result.strip().startswith('{') and result.strip().endswith('}'):
                        pass
                    try:
                        device_info = ast.literal_eval(result)
                    except (ValueError, SyntaxError):
                        device_info = {}
                    else:
                        if device_info:
                            parsed = parse_identity({'model': device_info.get('model', ''), 'brand': device_info.get('brand', ''), 'android': device_info.get('android', ''), 'security': device_info.get('security', ''), 'device': device_info.get('device', ''), 'hardware': device_info.get('hardware', ''), 'platform': device_info.get('chipset', device_info.get('board', '')), 'flash_locked': device_info.get('flash_locked', '1'), 'bootstate': device_info.get('bootstate', 'green'), 'build_id': device_info.get('build_id', ''), 'kernel': device_info.get('kernel', ''), 'baseband': device_info.get('baseband', '')})
                            self.log_area.clear()
                            self.log_area.append(fmt_identity_v2(parsed))
                except Exception:
                    self.log_area.append(result)
            elif self.active_command == 'check_storage_info' and isinstance(result, str):
                try:
                    dev_checks = {}
                    try:
                        mmcblk = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'ls /dev/block/mmcblk0 2>/dev/null && echo YES || echo NO']).strip()
                        sda = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'ls /dev/block/sda 2>/dev/null && echo YES || echo NO']).strip()
                        dev_checks['has_mmcblk0'] = 'YES' in mmcblk
                        dev_checks['has_sda'] = 'YES' in sda
                    except Exception:
                        pass
                    else:
                        parsed = parse_storage(result, dev_checks)
                        self.log_area.clear()
                        self.log_area.append(fmt_storage_v2(parsed))
                except Exception:
                    self.log_area.append(result)
            elif self.active_command == 'check_cpu_info' and isinstance(result, str):
                try:
                    max_freq = None
                    platform = None
                    try:
                        max_freq = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq 2>/dev/null']).strip()
                        platform = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'getprop', 'ro.board.platform']).strip()
                    except Exception:
                        pass
                    else:
                        parsed = parse_cpu(result, max_freq=max_freq, platform=platform)
                        self.log_area.clear()
                        self.log_area.append(fmt_cpu_v2(parsed))
                except Exception:
                    self.log_area.append(result)
            elif self.active_command == 'check_memory_info' and isinstance(result, str):
                try:
                    parsed = parse_memory(result)
                    self.log_area.clear()
                    self.log_area.append(fmt_memory_v2(parsed))
                except Exception:
                    self.log_area.append(result)
                else:
                    self.log_area.append(fmt_memory_v2(parsed))
                    if self.active_command == 'check_sensors' and isinstance(result, str):
                        try:
                            parsed = parse_sensors(result)
                            self.log_area.clear()
                            self.log_area.append(fmt_sensors_v2(parsed))
                        except Exception:
                            self.log_area.append(result)
                        else:
                            self.log_area.append(fmt_sensors_v2(parsed))
                            if self.active_command == '_check_thermal_cmd' and isinstance(result, str):
                                try:
                                    parsed = parse_thermal(result)
                                    self.log_area.clear()
                                    self.log_area.append(fmt_thermal_v2(parsed))
                                except Exception:
                                    self.log_area.append(result)
                                else:
                                    self.log_area.append(fmt_thermal_v2(parsed))
                                    if self.active_command == 'check_partition_map' and isinstance(result, str):
                                        try:
                                            parsed = parse_partitions(result)
                                            self.log_area.clear()
                                            self.log_area.append(fmt_partitions_v2(parsed))
                                        except Exception:
                                            self.log_area.append(result)
                                        else:
                                            self.log_area.append(fmt_partitions_v2(parsed))
                                            if self.active_command == '_check_network_cmd' and isinstance(result, str):
                                                try:
                                                    connectivity_raw = result
                                                    pkg_map = {}
                                                    if '===PKG_SEPARATOR===' in result:
                                                        parts = result.split('===PKG_SEPARATOR===')
                                                        connectivity_raw = parts[0].strip()
                                                        pkg_raw = parts[1].strip() if len(parts) > 1 else ''
                                                        for line in pkg_raw.splitlines():
                                                            m = re.match('package:(\\S+)\\s+uid:(\\d+)', line)
                                                            if m:
                                                                pkg_map[int(m.group(2))] = m.group(1)
                                                    parsed = parse_network(connectivity_raw)
                                                    if parsed.get('blocked_uids'):
                                                        resolved = []
                                                        for uid in parsed['blocked_uids']:
                                                            name = pkg_map.get(uid, f'uid:{uid}')
                                                            resolved.append(name)
                                                        parsed['blocked_names'] = resolved
                                                    self.log_area.clear()
                                                    self.log_area.append(fmt_network_v2(parsed))
                                                except Exception:
                                                    self.log_area.append(result)
                                                else:
                                                    self.log_area.append(fmt_network_v2(parsed))
                                                    if self.active_command == '_check_system_events_cmd' and isinstance(result, str):
                                                        try:
                                                            logcat = ''
                                                            uptime = ''
                                                            if '__LOGCAT__' in result and '__UPTIME__' in result:
                                                                parts = result.split('__UPTIME__')
                                                                logcat = parts[0].replace('__LOGCAT__', '').strip()
                                                                uptime = parts[1].strip() if len(parts) > 1 else ''
                                                            else:
                                                                logcat = result
                                                            parsed = parse_system_events(logcat, uptime)
                                                            self.log_area.clear()
                                                            self.log_area.append(fmt_system_events_v2(parsed))
                                                        except Exception:
                                                            self.log_area.append(result)
                                                        else:
                                                            self.log_area.append(fmt_system_events_v2(parsed))
                                                            if self.active_command == 'check_wifi' and isinstance(result, str):
                                                                try:
                                                                    parsed = parse_wifi(result)
                                                                    self.log_area.clear()
                                                                    self.log_area.append(fmt_wifi_v2(parsed))
                                                                except Exception:
                                                                    self.log_area.append(result)
                                                                else:
                                                                    self.log_area.append(fmt_wifi_v2(parsed))
                                                                    if self.active_command == '_check_usb_cmd' and isinstance(result, str):
                                                                        try:
                                                                            parsed = parse_usb(result)
                                                                            self.log_area.clear()
                                                                            self.log_area.append(fmt_usb_v2(parsed))
                                                                        except Exception:
                                                                            self.log_area.append(result)
                                                                        else:
                                                                            self.log_area.append(fmt_usb_v2(parsed))
                                                                            if self.active_command == '_check_rffe_cmd' and isinstance(result, str):
                                                                                try:
                                                                                    operator = None
                                                                                    net_type = None
                                                                                    sim_state = None
                                                                                    try:
                                                                                        operator = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'getprop', 'gsm.sim.operator.alpha']).strip()
                                                                                        net_type = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'getprop', 'gsm.network.type']).strip()
                                                                                        sim_state = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'getprop', 'gsm.sim.state']).strip()
                                                                                    except Exception:
                                                                                        pass
                                                                                    else:
                                                                                        sig_lines = '\n'.join((l for l in result.split('\n') if 'mSignalStrength' in l))
                                                                                        if sig_lines:
                                                                                            parsed = parse_signal(sig_lines, operator, net_type, sim_state=sim_state)
                                                                                            self.log_area.clear()
                                                                                            self.log_area.append(fmt_signal_v2(parsed))
                                                                                except Exception:
                                                                                    self.log_area.append(result)
                                                                            elif self.active_command == '_check_touch_cmd' and isinstance(result, str):
                                                                                pass
                                                                            elif self.active_command == '_check_camera_cmd' and isinstance(result, str):
                                                                                try:
                                                                                    parsed = parse_camera(result)
                                                                                    self.log_area.clear()
                                                                                    self.log_area.append(fmt_camera_v2(parsed))
                                                                                except Exception:
                                                                                    self.log_area.append(result)
                                                                            elif self.active_command == '_check_audio_cmd' and isinstance(result, str):
                                                                                try:
                                                                                    audio_raw = result
                                                                                    policy_raw = ''
                                                                                    if '===AUDIO_POLICY===' in result:
                                                                                        parts = result.split('===AUDIO_POLICY===')
                                                                                        audio_raw = parts[0].strip()
                                                                                        policy_raw = parts[1].strip() if len(parts) > 1 else ''
                                                                                    parsed = parse_audio(audio_raw, policy_raw)
                                                                                    self.log_area.clear()
                                                                                    self.log_area.append(fmt_audio_v2(parsed))
                                                                                except Exception:
                                                                                    self.log_area.append(result)
                                                                            else:
                                                                                self.log_area.append(result)
        except Exception as e:
            logger.error(f'Erro ao finalizar comando: {str(e)}')
            self.log_area.append(result)
        _OP_NAMES = {'check_device_info': 'Info do Dispositivo', 'check_storage_info': 'Armazenamento', 'check_cpu_info': 'Processador', 'check_memory_info': 'Memoria RAM', 'check_sensors': 'Sensores', '_check_thermal_cmd': 'Temperatura', '_check_rffe_cmd': 'Sinal Celular (RFFE)', 'check_partition_map': 'Mapa de Particoes', '_check_network_cmd': 'Analise de Rede', '_check_system_events_cmd': 'Eventos do Sistema', 'check_wifi': 'Analise Wi-Fi', '_check_usb_cmd': 'Teste USB', '_check_touch_cmd': 'Info Touch', '_check_camera_cmd': 'Info Camera', '_check_audio_cmd': 'Diagnostico Audio'}
        op_name = _OP_NAMES.get(self.active_command)
        current_text = self.log_area.toPlainText().strip()
        if current_text and _LINE[0] in current_text:
            self.log_area.clear()
            self.log_area.append(wrap_output(current_text, elapsed_ms, operation=op_name))
        self.enable_buttons()
        self.active_command = None
        if self.command_thread:
            self.command_thread.disconnect()
            self.command_thread = None
        try:
            try:
                self.adb.finalize_adb_operation()
            except Exception:
                return
        except Exception as e:
            logger.error(f'Erro ao finalizar comando: {str(e)}')
            self.log_area.append(result)
    def on_command_error(self, error):
        '''Manipula erros do comando'''
        try:
            logger.error(f'Erro no comando {self.active_command}: {error}')
            self.handle_adb_error(error)
            self.enable_buttons()
            self.active_command = None
            if self.command_thread:
                self.command_thread.disconnect()
                self.command_thread = None
                return
        except Exception as e:
            logger.error(f'Erro ao tratar erro do comando: {str(e)}')
    def enable_buttons(self, keep_verify=False):
        '''Habilita todos os bot├Áes'''
        logger.debug('Habilitando bot├Áes')
        try:
            for btn in self.findChildren(QPushButton):
                if keep_verify:
                    if 'Verificar' in btn.text():
                        continue
                btn.setEnabled(True)
                btn.setCursor(Qt.ArrowCursor)
            return
        except Exception as e:
            logger.error(f'Erro ao habilitar bot├Áes: {str(e)}')
    def disable_buttons(self, keep_verify=False):
        '''Desabilita bot├Áes durante execu├º├úo'''
        logger.debug('Desabilitando bot├Áes')
        try:
            for btn in self.findChildren(QPushButton):
                if keep_verify:
                    if 'Verificar' in btn.text():
                        continue
                btn.setEnabled(False)
                btn.setCursor(Qt.BusyCursor)
            return
        except Exception as e:
            logger.error(f'Erro ao desabilitar bot├Áes: {str(e)}')
    def check_device_info(self):
        '''Mostra informa├º├Áes do dispositivo de forma ass├¡ncrona'''
        logger.debug('Iniciando verifica├º├úo de informa├º├Áes do dispositivo')
        self.execute_command(self.adb.check_device_info)
    def check_storage(self):
        '''Verifica armazenamento de forma ass├¡ncrona'''
        logger.debug('Iniciando verifica├º├úo de armazenamento')
        self.execute_command(self.adb.check_storage_info)
    def check_partition_map(self):
        '''Lista mapa de parti├º├Áes do dispositivo via ADB'''
        logger.debug('Iniciando mapeamento de parti├º├Áes')
        self.execute_command(self.adb.check_partition_map)
    def check_cpu(self):
        '''Verifica CPU de forma ass├¡ncrona'''
        logger.debug('Iniciando verifica├º├úo de CPU')
        self.execute_command(self.adb.check_cpu_info)
    def check_memory(self):
        '''Verifica mem├│ria de forma ass├¡ncrona'''
        logger.debug('Iniciando verifica├º├úo de mem├│ria')
        self.execute_command(self.adb.check_memory_info)
    def check_wifi(self):
        '''Verifica informa├º├Áes do WiFi de forma ass├¡ncrona'''
        logger.debug('Iniciando verifica├º├úo de WiFi')
        self.execute_command(self.adb.check_wifi)
    def check_network(self):
        '''Verifica informacoes de rede de forma assincrona'''
        def _check_network_cmd():
            connectivity = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'dumpsys connectivity'])
            packages = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'pm list packages -U'])
            return f'{connectivity}\n===PKG_SEPARATOR===\n{packages}'
        self.execute_command(_check_network_cmd)
    def check_sensors(self):
        '''Verifica sensores de forma ass├¡ncrona'''
        logger.debug('Iniciando verifica├º├úo de sensores')
        self.execute_command(self.adb.check_sensors)
    def check_rffe(self):
        '''Verifica sinal celular de forma assincrona.'''
        def _check_rffe_cmd():
            return self.adb._run_adb_command([self.adb.adb_path, 'shell', 'dumpsys telephony.registry'])
        self.execute_command(_check_rffe_cmd)
    def test_usb(self):
        '''Verifica informacoes USB de forma assincrona'''
        def _check_usb_cmd():
            return self.adb._run_adb_command([self.adb.adb_path, 'shell', 'dumpsys usb'])
        self.execute_command(_check_usb_cmd)
    def check_thermal(self):
        '''Verifica informa├º├Áes t├®rmicas de forma ass├¡ncrona'''
        def _check_thermal_cmd():
            return self.adb._run_adb_command([self.adb.adb_path, 'shell', 'dumpsys thermalservice'])
        self.execute_command(_check_thermal_cmd)
    def check_touch_info(self):
        '''Diagnostico do digitalizador e subsistema de input'''
        def _check_touch_cmd():
            getevent = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'getevent -p'])
            features = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'pm list features'])
            return f'{getevent}\n===FEATURES===\n{features}'
        self.execute_command(_check_touch_cmd)
    def check_camera_info(self):
        '''Diagnostico de cameras detectadas pelo sistema'''
        def _check_camera_cmd():
            return self.adb._run_adb_command([self.adb.adb_path, 'shell', 'dumpsys media.camera'])
        self.execute_command(_check_camera_cmd)
    def check_audio_diag(self):
        '''Diagnostico completo do subsistema de audio'''
        def _check_audio_cmd():
            audio = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'dumpsys audio'])
            policy = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'dumpsys media.audio_policy'])
            return f'{audio}\n===AUDIO_POLICY===\n{policy}'
        self.execute_command(_check_audio_cmd)
    def check_system_events(self):
        '''Verifica eventos do sistema de forma assincrona'''
        def _check_system_events_cmd():
            logcat = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'logcat -d -t 100 *:E'])
            uptime = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'uptime'])
            return f'__LOGCAT__\n{logcat}\n__UPTIME__\n{uptime}'
        self.execute_command(_check_system_events_cmd)
    def execute_panic_android(self):
        '''Executa panic android de forma ass├¡ncrona com feedback visual melhorado'''
        if not self.adb.is_device_connected():
            QMessageBox.warning(self, self.translation_manager.get_text('device_not_found'), f'{self.translation_manager.get_text('no_android_detected_short')}\n\n{self.translation_manager.get_text('please_check')}\n{self.translation_manager.get_text('check_usb_connection')}\n{self.translation_manager.get_text('check_usb_debugging')}\n{self.translation_manager.get_text('try_reconnect')}')
            return
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        default_filename = f'bugreport_{timestamp}.zip'
        save_path, _ = QFileDialog.getSaveFileName(self, 'Salvar Bugreport', default_filename, 'Arquivos ZIP (*.zip)')
        if not save_path:
            self.on_command_finished('Opera├º├úo cancelada pelo usu├írio.')
            return
        self.progress = QProgressDialog(self)
        self.progress.setWindowTitle('Gerando Bugreport')
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.setAutoClose(True)
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.progress.setMinimumWidth(400)
        self.progress.setValue(0)
        info_messages = ['O bugreport ├® uma ferramenta essencial para diagn├│stico...', 'Ele cont├®m logs do sistema, informa├º├Áes de hardware e software...', 'Ajuda a identificar problemas de desempenho e estabilidade...', '├Ütil para desenvolvedores e suporte t├®cnico...', 'Inclui hist├│rico de crashes e ANRs (App Not Responding)...', 'Cont├®m informa├º├Áes sobre uso de bateria e recursos...', 'Ajuda a identificar apps problem├íticos...', 'Fornece dados sobre o estado da rede e conectividade...']
        self.msg_timer = QTimer(self)
        current_msg_index = 0
        def update_message():
            nonlocal current_msg_index
            self.progress.setLabelText(f'Gerando bugreport...\n\n{info_messages[current_msg_index]}')
            current_msg_index = (current_msg_index + 1) % len(info_messages)
        self.msg_timer.timeout.connect(update_message)
        self.msg_timer.start(3000)
        class BugreportThread(QThread):
            progress_update = pyqtSignal(int)
            finished = pyqtSignal(str)
            error = pyqtSignal(str)
            def __init__(self, adb, save_path):
                super().__init__()
                self.adb = adb
                self.save_path = save_path
                self._is_running = True
            def run(self):
                try:
                    process = subprocess.Popen([self.adb.adb_path, 'bugreport', self.save_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, startupinfo=self.adb.startupinfo, creationflags=self.adb.creation_flags)
                    if process.poll() is None:
                        while self._is_running:
                            output = process.stderr.readline()
                            if 'BEGIN:' in output:
                                self.progress_update.emit(30)
                            elif 'PROGRESS:' in output:
                                pass
                    try:
                        percent = int(output.split(':')[1].strip())
                        self.progress_update.emit(30 + int(percent * 0.6))
                    except:
                        pass
                    else:
                        if process.poll() is None:
                            if self._is_running:
                                pass
                        if not self._is_running:
                            process.terminate()
                            return
                        if os.path.exists(self.save_path):
                            self.progress_update.emit(100)
                            self.finished.emit(f'Bugreport gerado com sucesso!\n\nArquivo salvo em:\n{self.save_path}\n\nEste arquivo cont├®m informa├º├Áes detalhadas do sistema\nque podem ajudar no diagn├│stico de problemas.')
                            return
                        raise Exception('Falha ao gerar o arquivo de bugreport')
                except Exception as e:
                    self.error.emit(f'Erro durante a gera├º├úo do bugreport: {str(e)}')
            def stop(self):
                self._is_running = False
        self.bugreport_thread = BugreportThread(self.adb, save_path)
        self.bugreport_thread.progress_update.connect(self.progress.setValue)
        self.bugreport_thread.finished.connect(self._on_bugreport_finished)
        self.bugreport_thread.error.connect(self._on_bugreport_error)
        self.progress.canceled.connect(self.bugreport_thread.stop)
        self.bugreport_thread.start()
    def _on_bugreport_finished(self, result):
        '''Callback quando o bugreport ├® conclu├¡do com sucesso'''
        self.msg_timer.stop()
        self.progress.close()
        self.on_command_finished(result)
    def _on_bugreport_error(self, error):
        '''Callback quando ocorre um erro no bugreport'''
        self.msg_timer.stop()
        self.progress.close()
        self.on_command_error(error)
    def reboot_to_system(self):
        '''Reinicia para o sistema de forma ass├¡ncrona'''
        self.execute_command(self.adb.reboot_to_system)
    def reboot_to_recovery(self):
        '''Reinicia para recovery de forma ass├¡ncrona'''
        self.execute_command(self.adb.reboot_to_recovery)
    def reboot_to_fastboot(self):
        '''Reinicia para fastboot de forma ass├¡ncrona'''
        self.execute_command(self.adb.reboot_to_fastboot)
    def start_logging(self):
        '''Inicia a captura de logs'''
        try:
            if self.check_device_connection():
                self.log_area.clear()
                self.log_area.append('=== Iniciando captura de logs ===\n')
                self.adb.start_log_capture()
                self.start_capture_btn.setEnabled(False)
                self.stop_capture_btn.setEnabled(True)
                self.log_timer.start()
                return
        except Exception as e:
            self.show_error('Erro ao Iniciar Logs', str(e))
    def stop_logging(self):
        '''Para a captura de logs'''
        try:
            self.log_timer.stop()
            self.adb.stop_log_capture()
            self.start_capture_btn.setEnabled(True)
            self.stop_capture_btn.setEnabled(False)
            self.log_area.append('\n=== Captura de logs interrompida ===')
            return
        except Exception as e:
            self.show_error('Erro ao Parar Logs', str(e))
    def clear_logs(self):
        '''Limpa a ├írea de logs'''
        self.log_area.clear()
    def update_status_label(self, connected=False):
        '''Atualiza o label de status com cores'''
        if connected:
            self.status_label.setText('Status: Conectado')
            self.status_label.setStyleSheet(qss_status_label(True) if _TEMA_DISPONIVEL else '\n                QLabel {\n                    padding: 10px;\n                    border-radius: 5px;\n                    background: #4CAF50;\n                    color: white;\n                    font-weight: bold;\n                }\n            ')
            return
        self.status_label.setText('Status: N├úo conectado')
        self.status_label.setStyleSheet(qss_status_label(False) if _TEMA_DISPONIVEL else '\n                QLabel {\n                    padding: 10px;\n                    border-radius: 5px;\n                    background: #f44336;\n                    color: white;\n                    font-weight: bold;\n                }\n            ')
    def update_logs(self):
        '''Atualiza os logs em tempo real'''
        try:
            logs = self.adb.get_latest_logs()
            if logs:
                if isinstance(logs, str):
                    logs = logs.splitlines()
                for line in logs:
                    if line.strip():
                        l = line.rstrip()
                        if ' E ' not in l and ' E/' not in l:
                            if 'error' in l.lower() or 'fail' in l.lower():
                                self.log_area.append(f'<span style="color:#ff5555;font-weight:bold;">{l}</span>')
                            elif ' W ' not in l:
                                if ' W/' in l or 'warn' in l.lower():
                                    self.log_area.append(f'<span style="color:#ffcc00;font-weight:bold;">{l}</span>')
                                else:
                                    self.log_area.append(l)
                self.log_area.verticalScrollBar().setValue(self.log_area.verticalScrollBar().maximum())
                return
        except Exception as e:
            self.log_timer.stop()
            self.show_error('Erro ao Atualizar Logs', str(e))
    def get_health_status(self, health_code):
        '''Retorna status da saude da bateria ÔÇö limpo e conciso'''
        health_map = {'1': 'Desconhecido', '2': 'Boa', '3': 'Superaquecida', '4': 'Danificada', '5': 'Sobretens├úo', '6': 'Falha n├úo especificada', '7': 'Muito fria'}
        try:
            battery_info = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'dumpsys battery'])
            asoc = None
            current_capacity = None
            for line in battery_info.split('\n'):
                if 'mSavedBatteryAsoc' in line:
                    pass
            try:
                asoc = int(line.split(':')[1].strip())
            except (ValueError, IndexError):
                pass
        except Exception:
            return health_map.get(health_code, 'Desconhecido')
        health_status = health_map.get(health_code, 'Desconhecido')
        if asoc is not None:
            if asoc >= 85:
                cap_label = f'Capacidade: {asoc}%'
            elif asoc >= 60:
                cap_label = f'Capacidade: {asoc}% (degradada)'
                if health_status == 'Boa':
                    health_status = 'Degradada'
            else:
                cap_label = f'Capacidade: {asoc}% (critica)'
                if health_status == 'Boa':
                    health_status = 'Critica'
            if current_capacity:
                return f'{health_status} ÔÇö {cap_label} | {current_capacity:.0f} mAh'
            return f'{health_status} ÔÇö {cap_label}'
        try:
            if current_capacity:
                return f'{health_status} ÔÇö {current_capacity:.0f} mAh'
        except Exception:
            return health_map.get(health_code, 'Desconhecido')
        return health_status
    def analyze_voltage(self, voltage, capacity):
        '''Analisa os n├¡veis de voltagem da bateria'''
        if voltage < 3300:
            return f'ALERTA: Voltagem criticamente baixa ({voltage}mV)'
        if voltage < 3700:
            return f'Voltagem baixa ({voltage}mV)'
        if voltage > 4400:
            return f'ALERTA: Voltagem muito alta ({voltage}mV)'
        if voltage > 4350:
            return f'Voltagem ligeiramente alta ({voltage}mV)'
        return f'Voltagem normal ({voltage}mV)'
    def analyze_cycles(self, cycles):
        '''Analisa o n├║mero de ciclos de carga'''
        if cycles < 100:
            return f'Bateria nova ({cycles} ciclos)'
        if cycles < 300:
            return f'Uso moderado ({cycles} ciclos)'
        if cycles < 500:
            return f'Uso intenso ({cycles} ciclos)'
        return f'ALERTA: Muitos ciclos de carga ({cycles} ciclos)'
    def get_battery_recommendations(self, asoc=None, temp=None, voltage=None, cycles=None, health_status=None):
        '''Gera recomenda├º├Áes baseadas na an├ílise da bateria'''
        recommendations = []
        if asoc is not None and asoc < 75:
            recommendations.append('Recomenda├º├úo: Considere uma troca de bateria')
        if temp is not None:
            if temp > 40:
                recommendations.append('Recomenda├º├úo: Evite usar o dispositivo enquanto carrega')
                recommendations.append('Recomenda├º├úo: Evite exposi├º├úo ao sol ou calor excessivo')
            elif temp < 10:
                recommendations.append('Recomenda├º├úo: Evite usar o dispositivo em temperaturas muito baixas')
        if cycles is not None and cycles > 500:
            recommendations.append('Recomenda├º├úo: Bateria pr├│xima do fim da vida ├║til')
        if health_status and 'Cr├¡tica' in health_status:
            recommendations.append('IMPORTANTE: Fa├ºa backup dos seus dados e procure assist├¬ncia t├®cnica')
        return recommendations
    def show_error(self, title, error):
        '''Fun├º├úo melhorada para mostrar erros'''
        error_msg = str(error)
        friendly_messages = {'device not found': 'Dispositivo n├úo encontrado.\n\nVerifique:\n- Conex├úo do cabo USB\n- Depura├º├úo USB ativada\n- Driver do dispositivo instalado', 'unauthorized': 'Dispositivo n├úo autorizado.\n\nPor favor:\n- Aceite a solicita├º├úo de depura├º├úo USB no dispositivo\n- Reconecte o cabo USB', 'offline': 'Dispositivo offline.\n\nTente:\n- Reconectar o cabo USB\n- Reiniciar o dispositivo\n- Verificar a conex├úo USB', 'permission denied': 'Permiss├úo negada.\n\nExecute o programa como administrador', 'waiting for device': 'Aguardando dispositivo.\n\nVerifique se o dispositivo est├í:\n- Conectado via USB\n- Em modo fastboot', 'cannot load': 'Erro ao carregar ADB/Fastboot.\n\nVerifique:\n- Instala├º├úo do Android Platform Tools\n- Vari├íveis de ambiente'}
        for key, message in friendly_messages.items():
            if not key in error_msg.lower():
                continue
            error_msg = message
            break
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(error_msg)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.setStyleSheet(qss_msg_box_info() if _TEMA_DISPONIVEL else '\n            QMessageBox {\n                background-color: #f0f0f0;\n            }\n            QLabel {\n                min-width: 300px;\n                color: #333;\n            }\n            QPushButton {\n                padding: 5px 15px;\n                background-color: #2196F3;\n                color: white;\n                border: none;\n                border-radius: 3px;\n            }\n            QPushButton:hover {\n                background-color: #1976D2;\n            }\n        ')
        msg_box.exec_()
        self.log_area.append(f'\nÔØî ERRO: {error_msg}')
    def check_device_status(self):
        '''Verifica se h├í dispositivo conectado e atualiza o status periodicamente'''
        if getattr(self, '_checking_status', False):
            return
        self._checking_status = True
        try:
            if self.adb.is_adb_blocked_by_windows():
                if hasattr(self, 'device_check_timer') and self.device_check_timer.isActive():
                    self.device_check_timer.stop()
                    logger.warning('Ôøö Timer de verifica├º├úo parado - ADB bloqueado pelo Windows')
                if not getattr(self, '_adb_block_msg_shown', False):
                    self._adb_block_msg_shown = True
                    self.update_status_label(False)
                    msg = self.adb.get_adb_blocked_message()
                    self.log_area.append(f'\nÔÜá´©Å ATEN├ç├âO:\n{msg}')
                    QMessageBox.warning(self, 'ADB Bloqueado', msg)
                self._checking_status = False
                return
            if not self.command_thread or not self.command_thread.isRunning():
                if not self.adb.adb_path:
                    logger.debug('ADB n├úo dispon├¡vel para verifica├º├úo de status')
                    self.update_status_label(False)
                    self._checking_status = False
                    return
            else:
                try:
                    device_connected = self.adb.check_device()
                    self.update_status_label(device_connected)
                    if device_connected:
                        self.update_battery_info()
                except Exception as e:
                    logger.warning(f'Erro na verifica├º├úo de dispositivo: {str(e)}. Tentando limpar cache ADB.')
                    try:
                        self.adb.clear_adb_cache()
                        device_connected = self.adb.check_device()
                        self.update_status_label(device_connected)
                    except Exception as e2:
                        logger.error(f'Erro persistente ap├│s limpar cache: {str(e2)}')
                        self.update_status_label(False)
                finally:
                    self._checking_status = False
        except Exception as e:
            logger.debug(f'Erro ao verificar status do dispositivo: {str(e)}')
            self.update_status_label(False)
    def closeEvent(self, event):
        '''Limpa recursos ao fechar a janela'''
        logger.info('Fechando DiagnosticoAndroid e liberando recursos')
        try:
            if self.device_check_timer.isActive():
                self.device_check_timer.stop()
            if self.log_timer.isActive():
                self.log_timer.stop()
            if self.command_thread and self.command_thread.isRunning():
                logger.debug('Parando thread de comando em execu├º├úo')
                self.command_thread.stop()
                self.command_thread.wait(1000)
            if self.adb and self.adb.log_capture_running:
                logger.debug('Parando captura de logs')
                self.adb.stop_log_capture()
            if self.adb:
                logger.debug('Limpando processos ADB')
            try:
                self.adb.cleanup_processes()
            except Exception as e:
                logger.error(f'Erro ao limpar processos ADB: {str(e)}')
            else:
                try:
                    try:
                        from app.utils.scrcpy_manager import get_scrcpy_manager
                        get_scrcpy_manager().parar()
                    except Exception:
                        pass
                except Exception as e:
                    logger.error(f'Erro ao fechar DiagnosticoAndroid: {str(e)}')
                    logger.error(traceback.format_exc())
                    super().closeEvent(event)
                if hasattr(self, '_unlock_tools_mgr') and self._unlock_tools_mgr:
                    self._unlock_tools_mgr.limpar()
                super().closeEvent(event)
        except Exception as e:
            logger.error(f'Erro ao fechar DiagnosticoAndroid: {str(e)}')
            logger.error(traceback.format_exc())
            super().closeEvent(event)
    def on_tab_changed(self, index):
        '''Manipula a mudan├ºa de aba com melhor gest├úo de erros e reinicializa├º├úo'''
        logger.debug(f'Mudando para aba ├¡ndice {index}')
        try:
            if getattr(self, '_checking_status', False):
                logger.debug('Verifica├º├úo de status em andamento, adiando mudan├ºa de aba')
                QTimer.singleShot(100, (lambda: self.on_tab_changed(index)))
                QTimer.singleShot(100, self.clear_tab_changing_flag)
                return
            if getattr(self, '_tab_changing', False):
                logger.debug('Opera├º├úo de mudan├ºa de aba j├í em andamento')
                QTimer.singleShot(100, self.clear_tab_changing_flag)
                return
            self._tab_changing = True
            tab_widget = self.tab_widget.widget(index)
            tab_text = self.tab_widget.tabText(index)
            logger.debug(f'Aba selecionada: {tab_text}')
            aba_cores = {'Diagnostico': {'bg': '#1565C0', 'border': '#0D47A1'}, 'Motorola': {'bg': '#2E7D32', 'border': '#1B5E20'}, 'Xiaomi': {'bg': '#C62828', 'border': '#B71C1C'}, 'Samsung': {'bg': '#6A4C93', 'border': '#4A148C'}, 'QCOM EDL': {'bg': '#D84315', 'border': '#BF360C'}, 'Tira Virus': {'bg': '#0097A7', 'border': '#006064'}, 'Tools': {'bg': '#1428A0', 'border': '#0D1B69'}, 'Apps': {'bg': '#FF6F00', 'border': '#E65100'}, 'Monitor': {'bg': '#7B1FA2', 'border': '#4A148C'}}
            for texto, cores in aba_cores.items():
                if not texto in tab_text:
                    continue
                self.personalizar_aba(index, cores['bg'], cores['border'])
                break
        except Exception as e:
            logger.error(f'Erro na mudan├ºa de aba: {str(e)}')
        finally:
            QTimer.singleShot(100, self.clear_tab_changing_flag)
    def clear_tab_changing_flag(self):
        '''Limpa a flag de mudan├ºa de aba'''
        self._tab_changing = False
    def create_menu(self):
        '''Cria o menu da janela de diagn├│stico'''
        menu_bar = self.menuBar()
        view_menu = menu_bar.addMenu('Exibir')
        self.toggle_fullscreen_action = view_menu.addAction('Alternar Tela Cheia')
        self.toggle_fullscreen_action.setShortcut('F11')
        self.toggle_fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addSeparator()
        reset_size_action = view_menu.addAction('Redefinir Tamanho')
        reset_size_action.triggered.connect(self.reset_window_size)
        manual_menu = menu_bar.addMenu('Manual')
        manual_adb_action = manual_menu.addAction('ADB Habilitacao')
        manual_adb_action.triggered.connect(self.show_manual_adb)
        device_menu = menu_bar.addMenu('Dispositivo')
        select_device_action = device_menu.addAction('Selecionar Dispositivo ADB')
        select_device_action.setShortcut('Ctrl+D')
        select_device_action.setToolTip('Escolha qual dispositivo usar quando h├í v├írios conectados')
        select_device_action.triggered.connect(self.show_device_selector)
        usb_menu = menu_bar.addMenu('Conexao USB')
        usb_deps_action = usb_menu.addAction('Dependencias USB (UsbDk / WinFsp)')
        usb_deps_action.setToolTip('Verifica e instala bibliotecas necess├írias para comunica├º├úo USB')
        usb_deps_action.triggered.connect(self._abrir_dependencias_usb)
        usb_menu.addSeparator()
        usb_devmgmt_action = usb_menu.addAction('Gerenciador de Dispositivos')
        usb_devmgmt_action.setToolTip('Abre o Gerenciador de Dispositivos do Windows')
        usb_devmgmt_action.triggered.connect(self._abrir_gerenciador_dispositivos)
        tools_menu = menu_bar.addMenu('Ajustes')
        reset_adb_action = tools_menu.addAction('Reiniciar Conexao ADB')
        reset_adb_action.setShortcut('Ctrl+R')
        reset_adb_action.triggered.connect(self.reset_adb_action)
        tools_menu.addSeparator()
        fix_defender_action = tools_menu.addAction('Corrigir Bloqueio do Windows')
        fix_defender_action.setToolTip('Corrige problemas do Windows Defender bloqueando o ADB')
        fix_defender_action.triggered.connect(self.fix_windows_defender_action)
        reinstall_action = tools_menu.addAction('Reinstalar Platform-Tools')
        reinstall_action.setToolTip('Baixa uma nova vers├úo do ADB direto do Google')
        reinstall_action.triggered.connect(self.reinstall_platform_tools_action)
        tools_menu.addSeparator()
        sync_unlock_action = tools_menu.addAction('Sincronizar Modelos')
        sync_unlock_action.setToolTip('Atualiza lista de modelos dispon├¡veis')
        sync_unlock_action.setShortcut('Ctrl+Shift+U')
        sync_unlock_action.triggered.connect(self._sync_modelos_unlock)
        tools_menu.addSeparator()
        driver_menu = tools_menu.addMenu('Assinatura de Drivers')
        check_driver_action = driver_menu.addAction('Verificar Status')
        check_driver_action.setToolTip('Verifica status da verifica├º├úo de assinatura de drivers')
        check_driver_action.triggered.connect(self.check_driver_signature_status)
        driver_menu.addSeparator()
        enable_unsigned_action = driver_menu.addAction('Habilitar Drivers Nao Assinados')
        enable_unsigned_action.setToolTip('Permite instala├º├úo de drivers MTK, Qualcomm, etc.')
        enable_unsigned_action.triggered.connect(self.enable_unsigned_drivers)
        disable_unsigned_action = driver_menu.addAction('Restaurar Protecao de Drivers')
        disable_unsigned_action.setToolTip('Reativa verifica├º├úo de assinatura de drivers')
        disable_unsigned_action.triggered.connect(self.disable_unsigned_drivers)
        stream_menu = menu_bar.addMenu('Live Stream')
        self._stream_start_action = stream_menu.addAction('Iniciar Espelhamento')
        self._stream_start_action.setShortcut('Ctrl+L')
        self._stream_start_action.triggered.connect(self._toggle_live_stream)
        stream_menu.addSeparator()
        self._stream_stop_action = stream_menu.addAction('Encerrar Espelhamento')
        self._stream_stop_action.triggered.connect(self._parar_live_stream)
        self._stream_stop_action.setEnabled(False)
        help_menu = menu_bar.addMenu('Ajuda')
        about_action = help_menu.addAction('Sobre')
        about_action.triggered.connect(self.show_about)
        help_menu.addSeparator()
        close_action = help_menu.addAction('Fechar')
        close_action.setShortcut('Ctrl+Q')
        close_action.triggered.connect(self.close)
    def _toggle_live_stream(self):
        '''Inicia ou traz foco para o espelhamento.'''
        try:
            from app.utils.scrcpy_manager import get_scrcpy_manager
            mgr = get_scrcpy_manager()
            if mgr.esta_ativo():
                return
            from PyQt5.QtWidgets import QProgressDialog, QApplication
            from PyQt5.QtCore import Qt
            dlg = QProgressDialog('Iniciando espelhamento...', None, 0, 0, self)
            dlg.setWindowTitle('Live Stream')
            dlg.setWindowModality(Qt.WindowModal)
            dlg.setMinimumDuration(0)
            dlg.setMinimumWidth(280)
            dlg.show()
            QApplication.processEvents()
            def _prog(pct, msg):
                try:
                    dlg.setMaximum(100)
                    dlg.setValue(min(pct, 99))
                    dlg.setLabelText(msg if msg else 'Baixando recursos...')
                    QApplication.processEvents()
                    return
                except Exception:
                    return
            def _on_stream_stop():
                try:
                    self._stream_start_action.setEnabled(True)
                    self._stream_stop_action.setEnabled(False)
                    return
                except Exception:
                    return
            ok, msg = mgr.iniciar(parent=self, progress_callback=_prog, on_stop=_on_stream_stop)
            dlg.close()
            if ok:
                self._stream_start_action.setEnabled(False)
                self._stream_stop_action.setEnabled(True)
                return
            if msg:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(self, 'Live Stream', msg)
                return
        except Exception:
            pass
    def _parar_live_stream(self):
        '''Encerra espelhamento se ativo.'''
        try:
            from app.utils.scrcpy_manager import get_scrcpy_manager
            mgr = get_scrcpy_manager()
            mgr.parar()
        except Exception:
            pass
        try:
            self._stream_start_action.setEnabled(True)
            self._stream_stop_action.setEnabled(False)
        except Exception:
            return
    def _abrir_dependencias_usb(self):
        '''Abre a janela de gerenciamento de depend├¬ncias USB.'''
        try:
            from app.utils.usb_requirements_manager import abrir_janela_dependencias_usb
            abrir_janela_dependencias_usb(parent=self)
            return
        except Exception:
            try:
                QMessageBox.warning(self, 'Conex├úo USB', 'N├úo foi poss├¡vel abrir a janela de depend├¬ncias USB.')
                return
            except Exception:
                pass
    def _abrir_gerenciador_dispositivos(self):
        '''Atalho para o Gerenciador de Dispositivos do Windows.'''
        try:
            from app.utils.usb_requirements_manager import abrir_gerenciador_dispositivos_seguro
            abrir_gerenciador_dispositivos_seguro(parent=self)
            return
        except Exception:
            try:
                QMessageBox.warning(self, 'Gerenciador de Dispositivos', 'N├úo foi poss├¡vel abrir o Gerenciador de Dispositivos.')
                return
            except Exception:
                pass
    def _sync_modelos_unlock(self):
        '''Sincroniza modelos din├ómicos do servidor ÔÇö Ctrl+Shift+U'''
        import time as _time
        cooldown = getattr(self, '_sync_cooldown', 0)
        if _time.monotonic() < cooldown:
            ultimo_ok = getattr(self, '_sync_ultimo_ok', True)
            if ultimo_ok:
                QMessageBox.information(self, 'Sincroniza├º├úo', 'Seus modelos j├í est├úo atualizados!')
                return
            QMessageBox.information(self, 'Sincroniza├º├úo', 'N├úo foi poss├¡vel verificar atualiza├º├Áes.\n\nVerifique sua conex├úo e tente novamente em instantes.')
            return
        progress = QProgressDialog('Verificando atualiza├º├Áes...', None, 0, 0, self)
        progress.setWindowTitle('Sincroniza├º├úo')
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setCancelButton(None)
        progress.show()
        QApplication.processEvents()
        def _do_sync():
            ok = False
            try:
                from app.views.union_unlock.edl.edl_sync import get_sync
                sync = get_sync()
                ok = sync.sincronizar()
                if ok:
                    sync.sincronizar_loaders_auto()
            except Exception:
                ok = False
            try:
                edl_w = getattr(self, '_edl_qcom_widget', None)
                if edl_w and hasattr(edl_w, '_recarregar_marcas'):
                    from PyQt5.QtCore import QMetaObject, Qt as _Qt
                    QMetaObject.invokeMethod(edl_w, '_recarregar_marcas', _Qt.QueuedConnection)
            except Exception:
                pass
            try:
                from app.views.union_unlock.spd.spd_sync import get_sync as _spd_get_sync
                _spd_sync = _spd_get_sync()
                spd_ok = _spd_sync.sincronizar()
                if not spd_ok:
                    ok = False
                spd_w = getattr(self, '_spd_widget', None)
                if spd_w and hasattr(spd_w, '_recarregar_marcas'):
                    from PyQt5.QtCore import QMetaObject, Qt as _Qt
                    QMetaObject.invokeMethod(spd_w, '_recarregar_marcas', _Qt.QueuedConnection)
            except Exception:
                pass
            try:
                hxd_w = getattr(self, '_hxd_widget', None)
                if hxd_w:
                    frp = getattr(hxd_w, '_frp_frame', None)
                    if frp and hasattr(frp, '_engine') and frp._engine:
                        frp._engine.sync(force=True)
                        from PyQt5.QtCore import QMetaObject, Qt as _Qt
                        QMetaObject.invokeMethod(frp, '_popular_modelos', _Qt.QueuedConnection)
            except Exception:
                pass
            try:
                exy_w = getattr(self, '_exy_widget', None)
                if exy_w and hasattr(exy_w, '_preset_mgr'):
                    from app.views.union_unlock.exy.engine.exynos_sync import get_sync as _exy_get_sync
                    _exy_sync = _exy_get_sync()
                    _exy_sync.sincronizar()
                    exy_w._preset_mgr.clear_cache()
                    from PyQt5.QtCore import QMetaObject, Qt as _Qt
                    QMetaObject.invokeMethod(exy_w, '_carregar_chipsets', _Qt.QueuedConnection)
            except Exception:
                pass
            self._sync_ultimo_ok = ok
            self._sync_resultado_msg = ok
            from PyQt5.QtCore import QMetaObject, Qt as _Qt
            QMetaObject.invokeMethod(progress, 'close', _Qt.QueuedConnection)
            QMetaObject.invokeMethod(self, '_mostrar_resultado_sync', _Qt.QueuedConnection)
        self._sync_cooldown = _time.monotonic() + 120
        threading.Thread(target=_do_sync, daemon=True).start()
    @pyqtSlot()
    def _mostrar_resultado_sync(self):
        ok = getattr(self, '_sync_resultado_msg', False)
        if ok:
            QMessageBox.information(self, 'Sincroniza├º├úo', 'Modelos atualizados com sucesso!')
            return
        QMessageBox.warning(self, 'Sincroniza├º├úo', 'N├úo foi poss├¡vel sincronizar.\nVerifique sua conex├úo e tente novamente.')
    def reset_adb_action(self):
        '''
        Reinicia completamente a conex├úo ADB
        Resolve problemas de conex├úo, travamentos e erros
        '''
        reply = QMessageBox.question(self, '­ƒöä Reiniciar Conex├úo ADB', 'Esta a├º├úo ir├í reiniciar completamente a conex├úo com dispositivos Android.\n\nÔ£à Resolve problemas de:\n  ÔÇó Dispositivos n├úo detectados\n  ÔÇó Conex├úo travada ou lenta\n  ÔÇó Erros de comunica├º├úo\n  ÔÇó M├║ltiplos dispositivos conflitando\n\nO processo leva alguns segundos.\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.No:
            return
        from PyQt5.QtWidgets import QProgressDialog
        progress = QProgressDialog('Reiniciando conex├úo ADB...\n\nAguarde...', None, 0, 100, self)
        progress.setWindowTitle('Reset ADB')
        progress.setWindowModality(Qt.WindowModal)
        progress.setAutoClose(False)
        progress.setValue(0)
        progress.show()
        QApplication.processEvents()
        try:
            progress.setLabelText('­ƒöä Preparando reset...')
            progress.setValue(20)
            QApplication.processEvents()
            progress.setLabelText('­ƒöä Reiniciando conex├úo ADB...')
            progress.setValue(40)
            QApplication.processEvents()
            resultado = self.adb.reset_adb_complete()
            progress.setLabelText('Ô£à Verificando conex├úo...')
            progress.setValue(80)
            QApplication.processEvents()
            time.sleep(0.5)
            device_ok = False
            try:
                device_ok = self.adb.check_device()
            except:
                pass
            else:
                progress.setValue(100)
                progress.close()
                if device_ok:
                    QMessageBox.information(self, 'Ô£à Conex├úo Restabelecida', 'A conex├úo ADB foi reiniciada com sucesso!\n\nÔ£à Dispositivo detectado e pronto para usar.\n\nVoc├¬ j├í pode continuar trabalhando normalmente.')
                    return
                if self.adb.adb_path:
                    QMessageBox.information(self, 'Ô£à Conex├úo Reiniciada', 'A conex├úo ADB foi reiniciada com sucesso!\n\nÔä╣´©Å Nenhum dispositivo Android detectado no momento.\n\n­ƒô▒ Para conectar um dispositivo:\n  1. Conecte via cabo USB\n  2. Ative a Depura├º├úo USB\n  3. Autorize o computador no dispositivo')
                    return
                QMessageBox.warning(self, 'ÔÜá´©Å Aten├º├úo', 'A conex├úo foi reiniciada, por├®m n├úo foi poss├¡vel\nestabelecer comunica├º├úo com dispositivos Android.\n\n­ƒÆí Solu├º├Áes:\n  1. Verifique se o cabo USB est├í bem conectado\n  2. Tente uma porta USB diferente\n  3. Reinicie o aplicativo\n  4. Reinicie o computador se necess├írio\n\n­ƒô× Se o problema persistir, contate o suporte.')
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, 'ÔØî Erro ao Reiniciar', 'N├úo foi poss├¡vel reiniciar a conex├úo ADB.\n\n­ƒÆí Solu├º├Áes:\n  1. Feche e abra o aplicativo novamente\n  2. Reinicie o computador\n  3. Verifique se h├í atualiza├º├Áes do sistema\n\n­ƒô× Se o problema persistir, contate o suporte.')
    def show_device_selector(self):
        '''
        Seletor de dispositivo ADB ÔÇö 15/04/2026
        Resolve: IoTs/water coolers no PC do cliente que conflitam com o ADB.
        '''
        try:
            devices = self.adb.get_connected_devices()
        except Exception as e:
            logger.error(f'Erro ao listar dispositivos: {e}')
            QMessageBox.warning(self, 'ÔÜá´©Å Erro', 'N├úo foi poss├¡vel listar os dispositivos conectados.\n\nVerifique se o ADB est├í funcionando corretamente.')
        if not devices:
            QMessageBox.information(self, '­ƒô▒ Nenhum Dispositivo', 'Nenhum dispositivo Android conectado foi encontrado.\n\n­ƒôî Verifique:\n  1. Cabo USB conectado\n  2. Depura├º├úo USB ativada\n  3. Dispositivo autorizado')
            return
        if len(devices) == 1:
            serial = devices[0]['serial']
            model = devices[0]['model']
            self.adb.set_selected_device(serial)
            QMessageBox.information(self, 'Dispositivo Selecionado', f'Apenas 1 dispositivo conectado:\n\n{model}\nSerial: {serial}\n\nDispositivo selecionado automaticamente.')
            return
        dialog = QDialog(self)
        dialog.setWindowTitle('Selecionar Dispositivo ADB')
        dialog.setMinimumWidth(420)
        dialog.setMinimumHeight(300)
        layout = QVBoxLayout(dialog)
        info_label = QLabel(f'Foram encontrados {len(devices)} dispositivos conectados.\nSelecione qual dispositivo deseja usar:')
        info_label.setWordWrap(True)
        info_label.setStyleSheet('font-size: 13px; padding: 8px;')
        layout.addWidget(info_label)
        list_widget = QListWidget()
        list_widget.setStyleSheet('\n            QListWidget {\n                font-size: 13px;\n                padding: 4px;\n            }\n            QListWidget::item {\n                padding: 10px;\n                border-bottom: 1px solid #333;\n            }\n            QListWidget::item:selected {\n                background-color: #0078D4;\n                color: white;\n            }\n        ')
        current_serial = self.adb.selected_serial
        selected_index = 0
        for i, dev in enumerate(devices):
            display = f'­ƒô▒ {dev['model']}   ÔÇö   Serial: {dev['serial']}'
            item = QListWidgetItem(display)
            item.setData(Qt.UserRole, dev['serial'])
            list_widget.addItem(item)
            if dev['serial'] == current_serial:
                selected_index = i
        list_widget.setCurrentRow(selected_index)
        layout.addWidget(list_widget)
        auto_label = QLabel('­ƒÆí Dica: Se nenhum dispositivo for selecionado,\no sistema usar├í o primeiro da lista automaticamente.')
        auto_label.setStyleSheet('font-size: 11px; color: #888; padding: 4px;')
        layout.addWidget(auto_label)
        btn_layout = QHBoxLayout()
        btn_auto = QPushButton('Modo Automatico')
        btn_auto.setStyleSheet('\n            QPushButton {\n                background-color: #555;\n                color: white;\n                border: none;\n                padding: 8px 16px;\n                border-radius: 4px;\n                font-size: 12px;\n            }\n            QPushButton:hover { background-color: #666; }\n        ')
        btn_select = QPushButton('Usar Este Dispositivo')
        btn_select.setStyleSheet('\n            QPushButton {\n                background-color: #0078D4;\n                color: white;\n                border: none;\n                padding: 8px 16px;\n                border-radius: 4px;\n                font-size: 12px;\n                font-weight: bold;\n            }\n            QPushButton:hover { background-color: #1a88e0; }\n        ')
        def _on_auto():
            self.adb.set_selected_device(None)
            dialog.accept()
            QMessageBox.information(self, '­ƒöä Modo Autom├ítico', 'Sele├º├úo de dispositivo removida.\n\nO sistema usar├í o primeiro dispositivo detectado automaticamente.')
        def _on_select():
            current = list_widget.currentItem()
            if not current:
                return
            serial = current.data(Qt.UserRole)
            model = current.text().split('ÔÇö')[0].replace('­ƒô▒', '').strip()
            self.adb.set_selected_device(serial)
            dialog.accept()
            QMessageBox.information(self, 'Ô£à Dispositivo Selecionado', f'Dispositivo selecionado com sucesso!\n\n­ƒô▒ {model}\nSerial: {serial}\n\nTodos os comandos ADB ser├úo direcionados para este dispositivo.')
        btn_auto.clicked.connect(_on_auto)
        btn_select.clicked.connect(_on_select)
        list_widget.itemDoubleClicked.connect((lambda: _on_select()))
        btn_layout.addWidget(btn_auto)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_select)
        layout.addLayout(btn_layout)
        dialog.exec_()
    def fix_windows_defender_action(self):
        '''
        Corrige problemas do Windows Defender bloqueando o ADB.
        Adiciona exce├º├Áes e remove Exploit Protection.
        '''
        try:
            from app.utils.correcao_wdef import show_correction_dialog
            show_correction_dialog(self)
            return
        except Exception as e:
            logger.error(f'Erro ao abrir corre├º├úo do Windows Defender: {e}')
            QMessageBox.critical(self, 'Erro', f'N├úo foi poss├¡vel abrir a ferramenta de corre├º├úo.\n\nErro: {str(e)}')
    def reinstall_platform_tools_action(self):
        '''
        Reinstala o platform-tools baixando do Google.
        '''
        try:
            from app.utils.correcao_wdef import show_reinstall_dialog
            show_reinstall_dialog(self)
            return
        except Exception as e:
            logger.error(f'Erro ao abrir reinstala├º├úo: {e}')
            QMessageBox.critical(self, 'Erro', f'N├úo foi poss├¡vel abrir a ferramenta de reinstala├º├úo.\n\nErro: {str(e)}')
    def check_driver_signature_status(self):
        '''Verifica status dos drivers'''
        try:
            from app.utils.window_protection import DriverSignatureManager
            status = DriverSignatureManager.check_status()
            if status['error']:
                QMessageBox.warning(self, 'Aviso', f'Nao foi possivel verificar: {status['error']}')
                return
            linhas = ['STATUS DOS DRIVERS:\n']
            if status['testsigning']:
                linhas.append('[OK] Modo de teste: Ativado')
            else:
                linhas.append('[--] Modo de teste: Desativado')
            if status['nointegritychecks'] or status['integrity_checks_disabled']:
                linhas.append('[OK] Drivers especiais: Permitidos')
            else:
                linhas.append('[--] Drivers especiais: Bloqueados')
            linhas.append('\n')
            if status['testsigning'] or status['nointegritychecks']:
                linhas.append('Seu PC esta pronto para drivers especiais.')
            else:
                linhas.append("Drivers especiais podem nao funcionar.\nUse 'Habilitar Drivers' no menu Ajustes.")
            QMessageBox.information(self, 'Status dos Drivers', '\n'.join(linhas))
            return
        except Exception as e:
            logger.error(f'Erro ao verificar drivers: {e}')
            QMessageBox.warning(self, 'Erro', 'Nao foi possivel verificar.')
    def enable_unsigned_drivers(self):
        '''Habilita drivers especiais para ferramentas tecnicas'''
        try:
            from app.utils.window_protection import DriverSignatureManager
            if not DriverSignatureManager.is_admin():
                QMessageBox.warning(self, 'Aviso', "Abra o programa como Administrador.\n\nClique com botao direito no icone\ne escolha 'Executar como administrador'.")
                return
            reply = QMessageBox.question(self, 'Habilitar Drivers', 'Permite instalar drivers especiais.\n\nUsado para:\n- Drivers de aparelhos em modo download\n- Drivers de boxes profissionais\n- Drivers de ferramentas tecnicas\n\nSera necessario reiniciar o PC.\n\nContinuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
            success1, msg1 = DriverSignatureManager.enable_test_signing()
            success2, msg2 = DriverSignatureManager.disable_integrity_checks()
            if success1 or success2:
                restart_reply = QMessageBox.question(self, 'Configurado', 'Drivers especiais habilitados!\n\nReinicie o PC para aplicar.\n\nReiniciar agora?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if restart_reply == QMessageBox.Yes:
                    import subprocess
                    subprocess.run(['shutdown', '/r', '/t', '10', '/c', 'TECH UNION: Reiniciando...'], shell=True)
                    QMessageBox.information(self, 'Reiniciando', 'O PC vai reiniciar em 10 segundos.\n\nSalve seus trabalhos!')
                    return
                return
            erro_simples = 'Nao foi possivel configurar.\n\n'
            if 'secure boot' in msg1.lower() or 'secure boot' in msg2.lower():
                erro_simples += 'Desative o Secure Boot no BIOS e tente novamente.'
            else:
                erro_simples += 'Tente executar como Administrador.'
            QMessageBox.warning(self, 'Aviso', erro_simples)
            return
        except Exception as e:
            logger.error(f'Erro ao habilitar drivers: {e}')
            QMessageBox.warning(self, 'Erro', 'Falha ao configurar drivers.')
    def disable_unsigned_drivers(self):
        '''Restaura configuracao padrao dos drivers'''
        try:
            from app.utils.window_protection import DriverSignatureManager
            if not DriverSignatureManager.is_admin():
                QMessageBox.warning(self, 'Aviso', "Abra o programa como Administrador.\n\nClique com botao direito no icone\ne escolha 'Executar como administrador'.")
                return
            reply = QMessageBox.question(self, 'Restaurar Drivers', 'Volta a configuracao padrao do Windows.\n\nAlguns drivers especiais podem parar de funcionar.\n\nContinuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
            success1, msg1 = DriverSignatureManager.disable_test_signing()
            success2, msg2 = DriverSignatureManager.enable_integrity_checks()
            if success1 or success2:
                QMessageBox.information(self, 'Restaurado', 'Configuracao padrao restaurada!\n\nReinicie o PC para aplicar.')
                return
            QMessageBox.warning(self, 'Aviso', 'Algumas opcoes ja estavam na configuracao padrao.')
            return
        except Exception as e:
            logger.error(f'Erro ao restaurar drivers: {e}')
            QMessageBox.warning(self, 'Erro', 'Falha ao restaurar configuracao.')
    def toggle_fullscreen(self):
        '''Alterna entre tela cheia e janela normal'''
        if self.isMaximized():
            self.showNormal()
            self.center_window()
            self.toggle_fullscreen_action.setText('Maximizar Janela')
            self.statusBar().showMessage('Janela redimensionada para o modo normal', 2000)
            return
        self.showMaximized()
        self.toggle_fullscreen_action.setText('Reduzir Janela')
        self.statusBar().showMessage('Janela maximizada - Pressione F11 para alternar', 2000)
    def center_window(self):
        '''Centraliza a janela na tela'''
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)
    def reset_window_size(self):
        '''Redefine o tamanho da janela para o padr├úo'''
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        width = min(int(screen.width() * 0.85), 1600)
        height = min(int(screen.height() * 0.85), 1000)
        self.showNormal()
        self.resize(width, height)
        self.center_window()
        self.statusBar().showMessage('Tamanho da janela redefinido', 2000)
    def show_about(self):
        '''Mostra informa├º├Áes sobre o diagn├│stico android'''
        from PyQt5.QtWidgets import QMessageBox
        about_text = "\n        <h3 style='color: #2196F3;'>Diagn├│stico Android UNION</h3>\n        <p><b>Vers├úo:</b> 1.3.4</p>\n        <p><b>Descri├º├úo:</b> Ferramenta avan├ºada para diagn├│stico de dispositivos Android</p>\n        \n        <h4 style='color: #1976D2;'>Funcionalidades:</h4>\n        <ul>\n            <li>­ƒô▒ Informa├º├Áes detalhadas do dispositivo</li>\n            <li>­ƒÆ¥ An├ílise de armazenamento</li>\n            <li>ÔÜí Diagn├│stico de CPU e mem├│ria</li>\n            <li>­ƒöï Monitoramento de bateria</li>\n            <li>­ƒôÂ An├ílise de conectividade</li>\n            <li>­ƒøí´©Å Detec├º├úo de adware e v├¡rus</li>\n        </ul>\n        \n        <p style='color: #666; font-size: 11px;'>\n        Tech Union Solutions ┬® 2024<br>\n        Todos os direitos reservados\n        </p>\n        "
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.about(self, 'Sobre - Diagn├│stico Android', about_text)
    def show_manual_adb(self):
        '''Mostra o manual completo de habilita├º├úo ADB'''
        self._show_manual_adb_simple()
    def _show_manual_adb_simple(self):
        '''Vers├úo simplificada do manual ADB usando QDialog'''
        from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTabWidget, QTextEdit, QPushButton, QHBoxLayout)
        from PyQt5.QtCore import Qt
        dialog = QDialog(self)
        dialog.setWindowTitle('Manual ADB - RESTORECELL')
        dialog.setModal(True)
        dialog.resize(900, 700)
        layout = QVBoxLayout(dialog)
        tab_widget = QTabWidget()
        codes_tab = QTextEdit()
        codes_tab.setReadOnly(True)
        codes_tab.setHtml(self._get_codes_content())
        tab_widget.addTab(codes_tab, 'Codigos por Fabricante')
        emergency_tab = QTextEdit()
        emergency_tab.setReadOnly(True)
        emergency_tab.setHtml(self._get_emergency_content())
        tab_widget.addTab(emergency_tab, 'Emergencia/FRP')
        setup_tab = QTextEdit()
        setup_tab.setReadOnly(True)
        setup_tab.setHtml(self._get_setup_content())
        tab_widget.addTab(setup_tab, 'Configuracao PC')
        trouble_tab = QTextEdit()
        trouble_tab.setReadOnly(True)
        trouble_tab.setHtml(self._get_troubleshooting_content())
        tab_widget.addTab(trouble_tab, 'Problemas Comuns')
        layout.addWidget(tab_widget)
        button_layout = QHBoxLayout()
        close_button = QPushButton('Fechar')
        close_button.clicked.connect(dialog.close)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        dialog.exec_()
    def _get_codes_content(self):
        '''Retorna o conte├║do HTML dos c├│digos por fabricante'''
        return '\n        <h2 style=\'color: #2196F3; text-align: center;\'>­ƒöº C├│digos para Ativar ADB por Fabricante</h2>\n        \n        <h3 style=\'color: #1976D2;\'>­ƒô▒ SAMSUNG (Principal)</h3>\n        <table border=\'1\' cellpadding=\'8\' style=\'border-collapse: collapse; width: 100%;\'>\n            <tr style=\'background: #E3F2FD;\'>\n                <th>C├│digo</th><th>Fun├º├úo</th><th>Como Usar</th>\n            </tr>\n            <tr>\n                <td><code>*#0808#</code></td>\n                <td>USB Settings</td>\n                <td>Chamada emerg├¬ncia ÔåÆ Selecionar "DM+ACM+ADB" ÔåÆ Reboot</td>\n            </tr>\n            <tr>\n                <td><code>*#0*#</code></td>\n                <td>Menu de teste</td>\n                <td>Emerg├¬ncia ÔåÆ Acessar configura├º├Áes</td>\n            </tr>\n            <tr>\n                <td><code>(+30012012732+</code></td>\n                <td>Calculator Mode</td>\n                <td>Calculadora ÔåÆ Digite ÔåÆ <code>*#0808#</code></td>\n            </tr>\n        </table>\n        \n        <h3 style=\'color: #1976D2;\'>­ƒô▒ HUAWEI/HONOR</h3>\n        <ul>\n            <li><strong>*#*#2846579#*#*</strong> - ProjectMenu ÔåÆ Background Settings ÔåÆ USB Ports</li>\n            <li><strong>*#*#14789632#*#*</strong> - ProjectMenu alternativo</li>\n        </ul>\n        \n        <h3 style=\'color: #1976D2;\'>­ƒô▒ XIAOMI/REDMI</h3>\n        <ul>\n            <li><strong>*#*#6484#*#*</strong> - CIT Mode ÔåÆ Connectivity ÔåÆ USB ÔåÆ Enable ADB</li>\n            <li><strong>*#*#64663#*#*</strong> - Hardware Test ÔåÆ USB Debug</li>\n        </ul>\n        \n        <h3 style=\'color: #1976D2;\'>­ƒô▒ LG</h3>\n        <ul>\n            <li><strong>*#546368#*[3 ├║ltimos d├¡gitos]#</strong> - Hidden Menu ÔåÆ USB Settings</li>\n            <li><strong>277634#*#</strong> - Port Check Test</li>\n        </ul>\n        <p><em>Exemplos: V20: *#546368#*997# | G6: *#546368#*870# | V30: *#546368#*930#</em></p>\n        \n        <h3 style=\'color: #1976D2;\'>­ƒô▒ MOTOROLA</h3>\n        <ul>\n            <li><strong>*#*#2486#*#*</strong> - CQATest ÔåÆ Settings ÔåÆ ADB Debug</li>\n        </ul>\n        \n        <h3 style=\'color: #1976D2;\'>­ƒô▒ SONY</h3>\n        <ul>\n            <li><strong>*#*#7378423#*#*</strong> - Service Menu ÔåÆ Settings ÔåÆ USB Debug</li>\n        </ul>\n        \n        <h3 style=\'color: #1976D2;\'>­ƒô▒ OUTROS FABRICANTES</h3>\n        <ul>\n            <li><strong>OPPO/REALME:</strong> *#899# ou *#*#899#*#*</li>\n            <li><strong>VIVO:</strong> *#*#225#*#*</li>\n            <li><strong>ONEPLUS:</strong> *#800# ou *#*#800#*#*</li>\n        </ul>\n        \n        <div style=\'background: #FFF3E0; padding: 10px; margin-top: 20px; border-left: 4px solid #FF9800;\'>\n            <h4 style=\'color: #E65100; margin-top: 0;\'>ÔÜá´©Å IMPORTANTE:</h4>\n            <p>ÔÇó Sempre teste <code>*#06#</code> primeiro para verificar se c├│digos funcionam<br>\n            ÔÇó Aguarde 5-10 segundos ap├│s digitar c├│digos<br>\n            ÔÇó Alguns c├│digos precisam reinicializa├º├úo do aparelho</p>\n        </div>\n        '
    def _get_emergency_content(self):
        '''Retorna o conte├║do HTML dos m├®todos de emerg├¬ncia'''
        return '\n        <h2 style=\'color: #F44336; text-align: center;\'>­ƒåÿ M├®todos de Emerg├¬ncia (FRP/Tela Bloqueada)</h2>\n        \n        <h3 style=\'color: #D32F2F;\'>­ƒÜ¿ Cen├írio 1: Tela de Ativa├º├úo FRP</h3>\n        <ol>\n            <li>Tela do Google ÔåÆ "Chamada de emerg├¬ncia"</li>\n            <li>Digite o c├│digo do fabricante</li>\n            <li>Configure ADB conforme orienta├º├úo</li>\n            <li>Use ferramentas FRP (Z3X, Octopus, etc.)</li>\n        </ol>\n        \n        <h3 style=\'color: #D32F2F;\'>­ƒô▒ SAMSUNG - M├®todo Emerg├¬ncia</h3>\n        <div style=\'background: #FFEBEE; padding: 15px; border-radius: 5px;\'>\n            <p><strong>M├ëTODO A (Emerg├¬ncia):</strong></p>\n            <ol>\n                <li>Tela de ativa├º├úo ÔåÆ "Chamada de emerg├¬ncia"</li>\n                <li>Digite: <code>*#0808#</code></li>\n                <li>Selecione: "DM + ACM + ADB"</li>\n                <li>Toque em "Reboot"</li>\n            </ol>\n            \n            <p><strong>M├ëTODO B (Calculator):</strong></p>\n            <ol>\n                <li>Abra Calculadora</li>\n                <li>Digite: <code>(+30012012732+</code></li>\n                <li>Na tela que abrir, digite: <code>*#0808#</code></li>\n                <li>Selecione: "DM + ACM + ADB"</li>\n            </ol>\n        </div>\n        \n        <h3 style=\'color: #D32F2F;\'>­ƒô▒ XIAOMI - Qualquer Tela</h3>\n        <div style=\'background: #E8F5E8; padding: 15px; border-radius: 5px;\'>\n            <ol>\n                <li>Aparelho ligado em qualquer tela</li>\n                <li>Digite: <code>*#*#6484#*#*</code></li>\n                <li>Tela CIT aparece automaticamente</li>\n                <li>Procure: "Connectivity" ÔåÆ "USB"</li>\n                <li>Ative: "Enable ADB"</li>\n            </ol>\n        </div>\n        \n        <h3 style=\'color: #D32F2F;\'>­ƒô▒ LG - Download Mode</h3>\n        <div style=\'background: #FFF3E0; padding: 15px; border-radius: 5px;\'>\n            <ol>\n                <li>Aparelho no Download Mode</li>\n                <li>Na tela de emerg├¬ncia, digite: <code>277634#*#</code></li>\n                <li>Selecione: "Port Check Test"</li>\n                <li>Ative: "Enable"</li>\n                <li>Conecte USB</li>\n            </ol>\n        </div>\n        \n        <h3 style=\'color: #D32F2F;\'>­ƒöä M├®todos Alternativos</h3>\n        <p><strong>Via Bootloader/Fastboot:</strong></p>\n        <ul>\n            <li>Combina├º├úo: Volume Down + Power (maioria)</li>\n            <li>Comando: <code>adb reboot bootloader</code></li>\n            <li>Comando: <code>adb reboot fastboot</code></li>\n        </ul>\n        \n        <p><strong>Via Recovery:</strong></p>\n        <ul>\n            <li>Combina├º├úo: Volume Up + Power</li>\n            <li>Procurar: "ADB Sideload" ou "Reboot to bootloader"</li>\n        </ul>\n        \n        <div style=\'background: #FFCDD2; padding: 10px; margin-top: 20px; border-left: 4px solid #F44336;\'>\n            <h4 style=\'color: #C62828; margin-top: 0;\'>ÔÜá´©Å ATEN├ç├âO:</h4>\n            <p>ÔÇó Sempre informe riscos ao cliente<br>\n            ÔÇó Fa├ºa backup antes de qualquer procedimento<br>\n            ÔÇó Documente o que funcionou para cada modelo</p>\n        </div>\n        '
    def _get_setup_content(self):
        '''Retorna o conte├║do HTML da configura├º├úo da m├íquina'''
        return '\n        <h2 style=\'color: #4CAF50; text-align: center;\'>­ƒÆ╗ Configura├º├úo da M├íquina</h2>\n        \n        <h3 style=\'color: #388E3C;\'>­ƒôÑ Downloads Necess├írios</h3>\n        <div style=\'background: #E8F5E8; padding: 15px; border-radius: 5px;\'>\n            <p><strong>1. ADB/Fastboot Minimal (Recomendado):</strong></p>\n            <ul>\n                <li>Download: <code>https://developer.android.com/studio/releases/platform-tools</code></li>\n                <li>Tamanho: ~10MB</li>\n                <li>Inclui: adb.exe, fastboot.exe, drivers b├ísicos</li>\n            </ul>\n            \n            <p><strong>2. Drivers USB Universais:</strong></p>\n            <ul>\n                <li>Universal ADB Driver: <code>https://adb.clockworkmod.com/</code></li>\n                <li>Samsung USB Driver: Samsung.com/developers</li>\n                <li>LG Bridge: Para aparelhos LG</li>\n            </ul>\n        </div>\n        \n        <h3 style=\'color: #388E3C;\'>ÔÜÖ´©Å Instala├º├úo Windows</h3>\n        <div style=\'background: #E3F2FD; padding: 15px; border-radius: 5px;\'>\n            <p><strong>M├®todo Simples:</strong></p>\n            <ol>\n                <li>Download platform-tools.zip</li>\n                <li>Extrair para: <code>C:\\adb\\</code></li>\n                <li>Adicionar <code>C:\\adb\\</code> ao PATH do Windows</li>\n                <li>Teste: Abrir CMD ÔåÆ digite "adb"</li>\n            </ol>\n            \n            <p><strong>Configurar PATH (Windows 10/11):</strong></p>\n            <ol>\n                <li>Tecla Windows + R ÔåÆ digite "sysdm.cpl"</li>\n                <li>Aba "Avan├ºado" ÔåÆ "Vari├íveis de Ambiente"</li>\n                <li>Em "Path" ÔåÆ "Editar" ÔåÆ "Novo"</li>\n                <li>Adicionar: <code>C:\\adb\\</code></li>\n                <li>OK ÔåÆ OK ÔåÆ OK</li>\n                <li>Reiniciar CMD/PowerShell</li>\n            </ol>\n        </div>\n        \n        <h3 style=\'color: #388E3C;\'>­ƒöî Configura├º├úo Drivers</h3>\n        <div style=\'background: #FFF3E0; padding: 15px; border-radius: 5px;\'>\n            <p><strong>Driver Universal (Windows):</strong></p>\n            <ol>\n                <li>Baixar: universal_adb_driver.zip</li>\n                <li>Extrair pasta</li>\n                <li>Conectar aparelho com ADB ativo</li>\n                <li>Gerenciador de Dispositivos ÔåÆ Dispositivo desconhecido</li>\n                <li>Clique direito ÔåÆ "Atualizar driver"</li>\n                <li>Selecionar pasta extra├¡da</li>\n            </ol>\n        </div>\n        \n        <h3 style=\'color: #388E3C;\'>Ô£à Teste de Funcionamento</h3>\n        <div style=\'background: #FFEBEE; padding: 15px; border-radius: 5px;\'>\n            <p><strong>Comandos de Teste:</strong></p>\n            <pre style=\'background: #333; color: #fff; padding: 10px; border-radius: 3px;\'>\n# Verificar se ADB est├í instalado\nadb version\n\n# Listar dispositivos conectados\nadb devices\n\n# Resultado esperado:\nList of devices attached\nABC123XYZ    device\n            </pre>\n        </div>\n        \n        <h3 style=\'color: #388E3C;\'>­ƒÅó Setup da Bancada</h3>\n        <ul>\n            <li>PC fixo com ADB instalado</li>\n            <li>Cabos USB de qualidade (originais)</li>\n            <li>Hub USB 3.0 (para m├║ltiplos aparelhos)</li>\n            <li>Pasta com drivers principais</li>\n            <li>Backup dos manuais ADB impressos</li>\n        </ul>\n        \n        <div style=\'background: #E8F5E8; padding: 10px; margin-top: 20px; border-left: 4px solid #4CAF50;\'>\n            <h4 style=\'color: #2E7D32; margin-top: 0;\'>­ƒÆí DICA:</h4>\n            <p>Mantenha uma estrutura organizada:<br>\n            <code>C:\\TecnicoADB\\</code><br>\n            Ôö£ÔöÇÔöÇ adb\\ (platform-tools)<br>\n            Ôö£ÔöÇÔöÇ drivers\\ (drivers USB)<br>\n            Ôö£ÔöÇÔöÇ tools\\ (Z3X, Octopus, etc.)<br>\n            ÔööÔöÇÔöÇ manuais\\ (documenta├º├úo)</p>\n        </div>\n        '
    def _get_troubleshooting_content(self):
        '''Retorna o conte├║do HTML do troubleshooting'''
        return '\n        <h2 style=\'color: #FF9800; text-align: center;\'>­ƒøá´©Å Problemas Comuns e Solu├º├Áes</h2>\n        \n        <h3 style=\'color: #F57C00;\'>ÔØî "Device Unauthorized"</h3>\n        <div style=\'background: #FFF3E0; padding: 15px; border-radius: 5px; margin-bottom: 15px;\'>\n            <p><strong>CAUSA:</strong> N├úo autorizou depura├º├úo USB</p>\n            <p><strong>SOLU├ç├âO:</strong></p>\n            <ol>\n                <li>No celular ÔåÆ Aceitar depura├º├úo USB</li>\n                <li>Comando: <code>adb kill-server && adb start-server</code></li>\n                <li>Reconectar cabo USB</li>\n                <li>Marcar "Sempre permitir deste computador"</li>\n            </ol>\n        </div>\n        \n        <h3 style=\'color: #F57C00;\'>ÔØî "No Devices Found"</h3>\n        <div style=\'background: #FFEBEE; padding: 15px; border-radius: 5px; margin-bottom: 15px;\'>\n            <p><strong>CAUSA:</strong> Driver ou cabo</p>\n            <p><strong>SOLU├ç├âO:</strong></p>\n            <ol>\n                <li>Verificar cabo USB (trocar se necess├írio)</li>\n                <li>Trocar porta USB</li>\n                <li>Instalar/atualizar driver</li>\n                <li>Reiniciar adb: <code>adb kill-server && adb start-server</code></li>\n            </ol>\n        </div>\n        \n        <h3 style=\'color: #F57C00;\'>ÔØî "adb n├úo ├® reconhecido como comando"</h3>\n        <div style=\'background: #E3F2FD; padding: 15px; border-radius: 5px; margin-bottom: 15px;\'>\n            <p><strong>CAUSA:</strong> PATH n├úo configurado</p>\n            <p><strong>SOLU├ç├âO:</strong></p>\n            <ol>\n                <li>Verificar se adb.exe est├í na pasta</li>\n                <li>Reconfigurar PATH do Windows</li>\n                <li>Reiniciar CMD/PowerShell</li>\n                <li>Testar novamente</li>\n            </ol>\n        </div>\n        \n        <h3 style=\'color: #F57C00;\'>ÔØî "Permission Denied"</h3>\n        <div style=\'background: #E8F5E8; padding: 15px; border-radius: 5px; margin-bottom: 15px;\'>\n            <p><strong>CAUSA:</strong> USB Debug n├úo ativo</p>\n            <p><strong>SOLU├ç├âO:</strong></p>\n            <ol>\n                <li>Verificar se USB Debug est├í ativo</li>\n                <li>Revogar autoriza├º├Áes USB</li>\n                <li>Reconnectar e aceitar novamente</li>\n            </ol>\n        </div>\n        \n        <h3 style=\'color: #F57C00;\'>­ƒöº Comandos ├Üteis</h3>\n        <div style=\'background: #F5F5F5; padding: 15px; border-radius: 5px;\'>\n            <pre style=\'background: #333; color: #fff; padding: 10px; border-radius: 3px;\'>\n# Reiniciar servidor ADB\nadb kill-server && adb start-server\n\n# Verificar dispositivos com detalhes\nadb devices -l\n\n# Entrar no shell do aparelho\nadb shell\n\n# Informa├º├Áes do sistema\nadb shell getprop ro.product.model\nadb shell getprop ro.build.version.release\n\n# Reboot para diferentes modos\nadb reboot\nadb reboot recovery\nadb reboot bootloader\n            </pre>\n        </div>\n        \n        <h3 style=\'color: #F57C00;\'>­ƒôï Checklist R├ípido</h3>\n        <div style=\'background: #E8F5E8; padding: 15px; border-radius: 5px;\'>\n            <p><strong>Antes de come├ºar:</strong></p>\n            <ul>\n                <li>Ôÿæ´©Å ADB instalado e no PATH</li>\n                <li>Ôÿæ´©Å Drivers instalados</li>\n                <li>Ôÿæ´©Å Cabo USB de qualidade</li>\n                <li>Ôÿæ´©Å Teste <code>*#06#</code> primeiro</li>\n            </ul>\n            \n            <p><strong>Durante o processo:</strong></p>\n            <ul>\n                <li>Ôÿæ´©Å Aguarde 5-10 segundos ap├│s c├│digos</li>\n                <li>Ôÿæ´©Å Teste <code>adb devices</code> ap├│s tentativas</li>\n                <li>Ôÿæ´©Å Documente o que funcionou</li>\n            </ul>\n        </div>\n        \n        <div style=\'background: #FFCDD2; padding: 10px; margin-top: 20px; border-left: 4px solid #F44336;\'>\n            <h4 style=\'color: #C62828; margin-top: 0;\'>­ƒÄ» LEMBRE-SE:</h4>\n            <p>ÔÇó 90% dos problemas s├úo cabo USB ou driver<br>\n            ÔÇó Sempre teste em aparelho pr├│prio primeiro<br>\n            ÔÇó Mantenha backup dos procedimentos que funcionaram<br>\n            ÔÇó Em caso de d├║vida, consulte f├│runs t├®cnicos especializados</p>\n        </div>\n        '
    def detect_adware(self):
        '''Redirecionado para a aba de Detector de Adware'''
        for i in range(self.tab_widget.count()):
            if not 'Tira Virus' in self.tab_widget.tabText(i):
                continue
            self.tab_widget.setCurrentIndex(i)
            break
        QMessageBox.information(self, 'Tira Virus', "A funcionalidade de deteccao de virus foi movida para a aba 'Tira Virus'.\n\nVoc├¬ foi redirecionado para a nova interface.")
    def parse_radio_status(self, raw_output):
        import re
        def get_signal_strength(level, rsrp=None):
            if level >= 4:
                bars = '­ƒôÂ­ƒôÂ­ƒôÂ­ƒôÂ­ƒôÂ Sinal excelente'
            elif level == 3:
                bars = '­ƒôÂ­ƒôÂ­ƒôÂ Sinal bom'
            elif level == 2:
                bars = '­ƒôÂ­ƒôÂ Sinal regular'
            elif level == 1:
                bars = '­ƒôÂ Sinal fraco'
            else:
                bars = 'Sem sinal'
            if rsrp is not None and rsrp != '0':
                bars = f'{rsrp} dBm ({bars})'
            return bars
        def get_network_type(tech_code_or_name):
            network_types = {'0': 'Desconhecido', '1': 'GPRS', '2': 'EDGE', '3': 'UMTS', '4': 'CDMA', '5': 'EVDO_0', '6': 'EVDO_A', '7': '1xRTT', '8': 'HSDPA', '9': 'HSUPA', '10': 'HSPA', '11': 'iDEN', '12': 'EVDO_B', '13': 'LTE', '14': 'eHRPD', '15': 'HSPA+', '16': 'GSM', '17': 'TD-SCDMA', '18': 'IWLAN', '19': 'LTE_CA', '20': '5G_NR'}
            if isinstance(tech_code_or_name, str):
                for v in network_types.values():
                    if v in tech_code_or_name:
                        return v
            return network_types.get(str(tech_code_or_name), tech_code_or_name or 'Desconhecido')
        def parse_service_state(service_state_str):
            info = {}
            if 'mServiceState=' in service_state_str:
                voice_op = re.search('mVoiceOperatorAlphaLong=([^,\\n]+)', service_state_str)
                data_op = re.search('mDataOperatorAlphaLong=([^,\\n]+)', service_state_str)
                op = voice_op.group(1) if voice_op else data_op.group(1) if data_op else None
                info['operadora'] = op if op and op != 'null' else 'Desconhecida'
                voice_state = re.search('mVoiceRegState=(\\d+)\\(([^)]+)\\)', service_state_str)
                data_state = re.search('mDataRegState=(\\d+)\\(([^)]+)\\)', service_state_str)
                info['voice_state'] = voice_state.group(2) if voice_state else 'UNKNOWN'
                info['data_state'] = data_state.group(2) if data_state else 'UNKNOWN'
                voice_tech = re.search('getRilVoiceRadioTechnology=(\\d+)\\(([^)]+)\\)', service_state_str)
                data_tech = re.search('getRilDataRadioTechnology=(\\d+)\\(([^)]+)\\)', service_state_str)
                info['voice_tech'] = voice_tech.group(2) if voice_tech else 'Unknown'
                info['data_tech'] = data_tech.group(2) if data_tech else 'Unknown'
                info['tech_code'] = data_tech.group(1) if data_tech else '0'
                info['roaming'] = 'mRoaming=true' in service_state_str
                info['data_enabled'] = 'mDataEnabled=true' in service_state_str
                mcc = re.search('mMcc=(\\d+)', service_state_str)
                mnc = re.search('mMnc=(\\d+)', service_state_str)
                info['mcc'] = mcc.group(1) if mcc else None
                info['mnc'] = mnc.group(1) if mnc else None
                lte_block = re.search('CellIdentityLte:\\{([^}]*)\\}', service_state_str)
                if lte_block:
                    lte_content = lte_block.group(1)
                    band = re.search('mBandwidth=(\\d+)', lte_content)
                    if band:
                        bw = band.group(1)
                        if bw not in ('0', '2147483647'):
                            try:
                                bw_int = int(bw)
                                info['bandwidth'] = f'{bw_int // 1000 if bw_int > 1000 else bw_int} MHz'
                            except:
                                info['bandwidth'] = f'{bw}'
                        else:
                            info['bandwidth'] = None
                    rsrp2 = re.search('rsrp=(-?\\d+)', lte_content)
                    if rsrp2:
                        info['rsrp'] = rsrp2.group(1)
                if 'bandwidth' not in info:
                    band = re.search('mBandwidth=(\\d+)', service_state_str)
                    if band:
                        bw = band.group(1)
                        if bw not in ('0', '2147483647'):
                            try:
                                bw_int = int(bw)
                                info['bandwidth'] = f'{bw_int // 1000 if bw_int > 1000 else bw_int} MHz'
                            except:
                                info['bandwidth'] = f'{bw} MHz'
                        else:
                            info['bandwidth'] = None
                if 'rsrp' not in info:
                    rsrp = re.search('rsrp=(-?\\d+)', service_state_str)
                    if rsrp:
                        info['rsrp'] = rsrp.group(1)
            return info
        def global_signal_and_band(raw_output):
            rsrp = None
            rsrp_matches = re.findall('rsrp=(-?\\d+)', raw_output)
            if rsrp_matches:
                rsrp = min([int(x) for x in rsrp_matches if x not in ('0', '2147483647')], default=None)
                if rsrp is not None:
                    rsrp = str(rsrp)
            level = None
            level_matches = re.findall('level=(\\d+)', raw_output)
            if level_matches:
                level = max([int(x) for x in level_matches])
            bandwidth = None
            cellbands = re.findall('mCellBandwidths=\\[([\\d, ]+)\\]', raw_output)
            if cellbands:
                bands = [int(x) for x in re.split('[ ,]+', cellbands[0]) if x if x not in ('0', '2147483647')]
                if bands:
                    bw = max(bands)
                    bandwidth = f'{bw // 1000 if bw > 1000 else bw} MHz'
            return level, rsrp, bandwidth
        result = []
        found_active = False
        service_states = re.finditer('mServiceState=\\{([^}]*)\\}', raw_output)
        for i, state_match in enumerate(service_states):
            service_state_str = state_match.group(0)
            info = parse_service_state(service_state_str)
            status = f'\n­ƒô▒ Chip {i + 1} ({info.get('operadora', 'Desconhecida')}):\n'
            if info.get('voice_state') == 'IN_SERVICE' or info.get('data_state') == 'IN_SERVICE':
                found_active = True
                status += 'Ô£à Status: Conectado\n'
                rede = get_network_type(info.get('data_tech') or info.get('voice_tech'))
                status += f'­ƒôí Rede: {rede}\n'
                signal = re.search('level=(\\d+)', service_state_str)
                signal_level = int(signal.group(1)) if signal else None
                rsrp = info.get('rsrp')
                bw = info.get('bandwidth')
                if signal_level is None or rsrp is None or not bw:
                    g_level, g_rsrp, g_bw = global_signal_and_band(raw_output)
                    if signal_level is None and g_level is not None:
                        signal_level = g_level
                    if rsrp is None and g_rsrp is not None:
                        rsrp = g_rsrp
                    if not bw and g_bw:
                        bw = g_bw
                status += f'­ƒôÂ Sinal: {get_signal_strength(signal_level or 0, rsrp)}\n'
                if info.get('roaming'):
                    status += '­ƒîÉ Roaming: Ativo\n'
                if info.get('data_enabled'):
                    status += '­ƒô▒ Dados m├│veis: Ativos\n'
                if info.get('mcc') and info.get('mnc'):
                    status += f'­ƒôí MCC/MNC: {info['mcc']}/{info['mnc']}\n'
                status += f'­ƒôè Largura de banda: {bw if bw else 'Indispon├¡vel'}\n'
            else:
                status += 'ÔÜá´©Å Status: Sem servi├ºo\n'
                rede = get_network_type(info.get('data_tech') or info.get('voice_tech'))
                status += f'­ƒôí ├Ültima rede conhecida: {rede}\n'
                status += '­ƒôÂ ├Ültimo sinal: Sem sinal\n'
            result.append(status)
            continue
        try:
            available_networks = self.adb._run_adb_command([self.adb.adb_path, 'shell', 'service call phone 5 i32 0'])
            result.append('\n­ƒôí Redes dispon├¡veis:')
            networks = re.findall('"(.*?)"', available_networks)
            if networks:
                for network in networks:
                    if network.strip():
                        result.append(f'   ÔÇó {network}')
            else:
                result.append('   Nenhuma rede encontrada')
        except Exception as e:
            result.append('   Nenhuma rede encontrada')
        try:
            test_servers = [('Google', '8.8.8.8'), ('Cloudflare', '1.1.1.1'), ('Operadora', '8.8.4.4')]
            result.append('\n­ƒîÉ Teste de conectividade:')
            for name, server in test_servers:
                ping_result = self.adb._run_adb_command([self.adb.adb_path, 'shell', f'ping -c 1 -W 1 {server}'])
                if '1 received' in ping_result:
                    result.append(f'   Ô£à {name}: Conectado')
                else:
                    result.append(f'   ÔØî {name}: Sem conex├úo')
        except Exception as e:
            pass
        try:
            tech_info = self.adb._run_adb_command([self.adb.adb_path, 'shell', "dumpsys telephony.registry | grep -E 'mServiceState|mDataConnectionState|mDataConnectionNetworkType'"])
            if tech_info:
                result.append('\n­ƒöº Diagn├│stico T├®cnico:')
                for line in tech_info.split('\n'):
                    if any((x in line for x in ('IN_SERVICE', 'LTE', 'mcc', 'mnc', 'bandwidth', 'mDataConnectionState', 'rsrp'))):
                        line = re.sub('mBandwidth=2147483647', 'mBandwidth=Indispon├¡vel', line)
                        line = re.sub('mBandwidth=(\\d{4,6})', (lambda m: f'mBandwidth={int(m.group(1)) // 1000} MHz'), line)
                        result.append(f'   ÔÇó {line.strip()}')
        except Exception as e:
            pass
        if not found_active:
            result.append('\nÔÜá´©Å Nenhum chip SIM detectado ou ativo.')
            result.append('Recomenda├º├Áes:')
            result.append('1. Verifique se o chip est├í corretamente inserido')
            result.append('2. Tente reiniciar o dispositivo')
            result.append('3. Verifique se o chip est├í ativo com sua operadora')
            result.append('4. Teste o chip em outro dispositivo')
        return '\n'.join(result)
