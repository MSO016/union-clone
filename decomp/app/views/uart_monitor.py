from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QLabel, QTextEdit, QFrame, QTabWidget, QGridLayout, QMessageBox, QCheckBox, QLineEdit, QSpinBox, QScrollArea, QDialog, QApplication, QSizePolicy)
from PyQt5.QtCore import (Qt, QTimer, QSize, pyqtSignal)
from PyQt5.QtGui import (QTextCursor, QColor, QIcon)
import serial
import serial.tools.list_ports
import threading
import time
import re
from datetime import datetime
import os
from app.utils.translation_manager import TranslationManager
try:
    from app.utils.path_manager import PathManager
    _HAS_PATH_MANAGER = True
except ImportError:
    _HAS_PATH_MANAGER = False
def _uart_svg_icon(name):
    '''Retorna QIcon do SVG de forma defensiva (fallback: icone vazio).'''
    try:
        if _HAS_PATH_MANAGER:
            path = PathManager.get_resource_path('icons_svg/%s' % name)
            if path and os.path.isfile(path):
                return QIcon(path)
    except Exception:
        pass
    return QIcon()
try:
    from app.views._uart_parser import (create_empty_state, update_health_state, classify_line, update_health_state_auto, classify_line_auto)
    from app.views._uart_health_widget import UartHealthPanel
    _HAS_NEW_PARSER = True
except ImportError:
    _HAS_NEW_PARSER = False
os.environ['QT_LOGGING_RULES'] = 'qt.qpa.fonts.warning=false'
_SVG_SETA_DOWN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources', 'icons_svg', 'seta_down.svg').replace('\\', '/')
_UART_COLORS = {'primary_dark': '#0D47A1', 'primary': '#2196F3', 'bg_main': '#f7f9fc', 'bg_card': '#ffffff', 'text_dark': '#3a4a63', 'border': '#c5d6ec', 'border_light': '#e8eef5', 'success': '#4CAF50', 'error': '#E53935', 'warning': '#FF9800', 'info': '#2196F3'}
_UART_DPI_PROFILES = {'normal': {'window_w': 1200, 'window_h': 800, 'min_w': 950, 'min_h': 600, 'btn_min_w': 105, 'btn_min_h': 34, 'btn_font': 11, 'title_font': 13, 'body_font': 11, 'small_font': 10, 'combo_min_w': 120, 'spacing': 10, 'margin': 10, 'left_stretch': 65, 'right_stretch': 35}, 'intermediate': {'window_w': 1050, 'window_h': 700, 'min_w': 850, 'min_h': 540, 'btn_min_w': 90, 'btn_min_h': 30, 'btn_font': 10, 'title_font': 12, 'body_font': 10, 'small_font': 9, 'combo_min_w': 105, 'spacing': 8, 'margin': 8, 'left_stretch': 62, 'right_stretch': 38}, 'compact': {'window_w': 900, 'window_h': 600, 'min_w': 750, 'min_h': 480, 'btn_min_w': 78, 'btn_min_h': 28, 'btn_font': 10, 'title_font': 11, 'body_font': 10, 'small_font': 9, 'combo_min_w': 90, 'spacing': 6, 'margin': 6, 'left_stretch': 58, 'right_stretch': 42}, 'ultra_compact': {'window_w': 780, 'window_h': 520, 'min_w': 650, 'min_h': 420, 'btn_min_w': 68, 'btn_min_h': 26, 'btn_font': 9, 'title_font': 10, 'body_font': 9, 'small_font': 8, 'combo_min_w': 78, 'spacing': 5, 'margin': 5, 'left_stretch': 55, 'right_stretch': 45}}
class UARTMonitor(QMainWindow):
    signal_log = pyqtSignal(str, str)
    signal_error = pyqtSignal(str, str, str)
    signal_status = pyqtSignal(str)
    signal_stats = pyqtSignal(int, int)
    signal_filter_count = pyqtSignal(str, str, int)
    signal_health = pyqtSignal(object)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.translation_manager = TranslationManager.get_instance()
        self.setWindowTitle(self.translation_manager.get_text('uart_monitor_title'))
        self._profile = self._resolve_dpi_profile()
        p = self._profile
        self.resize(p['window_w'], p['window_h'])
        self.setMinimumSize(p['min_w'], p['min_h'])
        self.serial_port = None
        self.is_connected = False
        self.rx_count = 0
        self.tx_count = 0
        self._detect_cancel = False
        self._detect_thread = None
        self._hw_health = {'PLL': {'status': 'ÔÇö', 'detail': ''}, 'PMIC': {'status': 'ÔÇö', 'detail': ''}, 'UFS': {'status': 'ÔÇö', 'detail': ''}, 'GPIO': {'status': 'ÔÇö', 'detail': ''}, 'WDT': {'status': 'ÔÇö', 'detail': ''}, 'SPMI': {'status': 'ÔÇö', 'detail': ''}, 'RTC': {'status': 'ÔÇö', 'detail': ''}, 'Boot': {'status': 'ÔÇö', 'detail': ''}}
        self._hw_labels = {}
        self._boot_cycle_count = 0
        self._last_boot_stage = ''
        if _HAS_NEW_PARSER:
            self._parsed_state = create_empty_state()
        self.message_patterns = {'Inicializacao': {'PLL / Clock': {'pattern': '(?:Pll init|#T#PLL|pll_init|clock_init|PLL=)', 'color': '#4caf50', 'type': 'success', 'description': 'Clock do processador (PLL)', 'repair_steps': ['PLL init Done = clock do processador OK', 'Se ausente: problema no cristal oscilador', 'Verifique soldas do cristal (XTAL)', 'Teste continuidade nos pinos do cristal']}, 'PMIC / Power': {'pattern': '(?:\\[PWRAP\\].*(?:pass|Done|Found|Calibration)|pmic_detect|PMIC_RST_KEY|POWER ON)', 'color': '#4caf50', 'type': 'success', 'description': 'Comunicacao com PMIC (gerenciamento de energia)', 'repair_steps': ['PWRAP pass = comunicacao SPI com PMIC OK', 'Se ausente: PMIC danificado ou sem alimentacao', 'Verifique soldas e tensoes do PMIC', 'Teste VBAT e VIO no PMIC']}, 'Memoria': {'pattern': '(?:mtcmos Done|initializing heap|Memory base|DDR|do_ddr_training)', 'color': '#4caf50', 'type': 'success', 'description': 'Subsistema de memoria (RAM/mtcmos)', 'repair_steps': ['mtcmos Done = dominio de energia da memoria OK', 'Se ausente: possivel falha na RAM ou alimentacao', 'Verifique soldas da RAM (reballing)', 'Teste tensoes VDRAM e VDDQ']}, 'GPIO': {'pattern': '(?:#T#GPIO|gpio_set|kpd_gpio)', 'color': '#4caf50', 'type': 'success', 'description': 'Portas GPIO do processador', 'repair_steps': ['GPIO init = pinos de I/O do SoC OK', 'Se ausente: possivel problema no SoC', 'Verifique alimentacao do SoC', 'GPIO controla botoes, sensores, etc']}, 'Boot Stage': {'pattern': '(?:ll init start|BL31.*Initializing|welcome to lk|initializing kernel|BL31_BASE|Booting from)', 'color': '#4caf50', 'type': 'success', 'description': 'Estagio do boot (Preloader > LK > Kernel)', 'repair_steps': ['Cada estagio indica progresso do boot', 'Preloader: ll init start (primeiro estagio)', 'LK: welcome to lk (segundo estagio)', 'Se parou aqui: problema no estagio seguinte']}}, 'Diagnostico': {'Reset / Motivo': {'pattern': '(?:\\[RGU\\].*(?:rst from|STA from|parse g_rgu_status|NONRST_REG))', 'color': '#2196f3', 'type': 'info', 'description': 'Motivo do reset e estado do watchdog', 'repair_steps': ['rst from mostra o que causou o reset', 'STA=0x0 = boot limpo (normal)', 'STA diferente de 0 = reset por falha', 'NONRST_REG guarda flags entre resets']}, 'Watchdog': {'pattern': '(?:\\[RGU\\].*(?:MODE|LENGTH|INTERVAL|SWSYSRST|wdt_mode|wdt_pre_init|LATCH_CTL|DEBUG_CTL)|#T#WDT)', 'color': '#2196f3', 'type': 'info', 'description': 'Configuracao do watchdog timer', 'repair_steps': ['WDT protege contra travamentos', 'MODE e LENGTH definem o timeout', 'Se WDT reseta repetidamente: travamento no boot', 'Pode indicar problema de software ou hardware']}, 'ATF / TrustZone': {'pattern': '(?:\\[ATF\\].*(?:log_enable|BOOT_REASON|version|BL31:|Preparing for EL3)|====> GZ|MTEE|mTEE_SDK)', 'color': '#2196f3', 'type': 'info', 'description': 'ARM Trusted Firmware e TrustZone', 'repair_steps': ['ATF/BL31 = firmware seguro do processador', 'BOOT_REASON mostra tipo de boot', 'GZ = GeeniZone (hypervisor MediaTek)', 'Se ausente: possivel problema na eMMC/UFS']}, 'Bandgap / Analog': {'pattern': '(?:bandgap filter|0x1000C600)', 'color': '#2196f3', 'type': 'info', 'description': 'Calibracao do circuito analogico (bandgap)', 'repair_steps': ['Bandgap = referencia de tensao interna do SoC', 'Valores diferentes do esperado = problema analogico', 'Geralmente indica SoC danificado', 'Comparar valores com aparelho funcional']}}, 'Falhas': {'Erros Reais': {'pattern': '(?i)(?:(?:^|[\\s\\[])(?:error|fail(?:ed|ure)?|fault|panic|abort)\\b(?!.*(?:_flag\\b|_addr\\b|_size\\b|_log\\b)))', 'color': '#f44336', 'type': 'error', 'description': 'Erros reais detectados no boot', 'repair_steps': ['Analise a linha completa do erro', 'Identifique qual subsistema falhou', 'Verifique componentes relacionados', 'Compare com log de aparelho funcional']}, 'I2C / Barramento': {'pattern': '(?i)(?:i2c.*(?:error|fail|timeout|nack)|spi.*(?:error|fail|timeout))', 'color': '#ff5722', 'type': 'error', 'description': 'Falha de comunicacao I2C/SPI', 'repair_steps': ['I2C/SPI = barramentos de comunicacao', 'Falha aqui indica componente sem resposta', 'Verifique soldas do componente no barramento', 'Teste pullups e continuidade das trilhas']}, 'PMIC Falha': {'pattern': '(?i)(?:pmic.*(?:error|fail|fault|over.*temp|under.*volt)|PWRAP.*(?:error|fail|timeout))', 'color': '#d32f2f', 'type': 'error', 'description': 'Falha critica no PMIC', 'repair_steps': ['PMIC com falha = sem energia para o aparelho', 'Verifique VBAT, VSYS e alimentacao principal', 'Teste com fonte de bancada (limite corrente)', 'Possivel necessidade de troca do PMIC']}}, 'Avisos': {'Warnings': {'pattern': '(?i)(?:(?:^|[\\s\\[])(?:warning|WARN|caution)\\b|not match|format all)', 'color': '#ff9800', 'type': 'warning', 'description': 'Avisos do sistema (nem sempre sao problemas)', 'repair_steps': ['Avisos podem ser comportamento normal', '"not match, format all" = primeira vez ligando (normal)', 'Monitore se o boot continua apos o aviso', 'Warning repetido pode indicar problema']}, 'Retry / Timeout': {'pattern': '(?i)(?:(?:^|[\\s\\[])(?:retry|timeout|timed out)\\b)', 'color': '#ff9800', 'type': 'warning', 'description': 'Tentativas e timeouts', 'repair_steps': ['Retry = sistema tentando novamente', 'Timeout = componente nao respondeu a tempo', 'Poucos retries = normal, muitos = problema', 'Timeout repetido = componente possivelmente danificado']}}}
        self.category_colors = {'Inicializacao': '#4caf50', 'Diagnostico': '#2196f3', 'Falhas': '#f44336', 'Avisos': '#ff9800'}
        self.category_bg_colors = {'Inicializacao': '#e8f5e9', 'Diagnostico': '#e3f2fd', 'Falhas': '#ffebee', 'Avisos': '#fff3e0'}
        self.message_counts = {}
        for category in self.message_patterns:
            self.message_counts[category] = {}
            for name in self.message_patterns[category]:
                self.message_counts[category][name] = 0
        self.message_checks = {}
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_statistics)
        self.stats_timer.start(1000)
        self.setup_ui()
        self.signal_log.connect(self.update_log)
        self.signal_error.connect(self.handle_error)
        self.signal_status.connect(self.update_status)
        self.signal_stats.connect((lambda rx, tx: None))
        self.signal_filter_count.connect(self.update_filter_count)
        self.read_thread = None
        self.command_history = []
        self._port_refresh_timer = QTimer()
        self._port_refresh_timer.timeout.connect(self._auto_refresh_ports)
        self._port_refresh_timer.start(3000)
        self._health_needs_update = False
        if _HAS_NEW_PARSER:
            self._health_timer = QTimer()
            self._health_timer.setInterval(150)
            self._health_timer.timeout.connect(self._poll_health_update)
            QTimer.singleShot(100, self._init_health_pending)
        self.show_welcome_message()
    @staticmethod
    def _resolve_dpi_profile():
        '''Detecta DPI do sistema e retorna profile adequado.'''
        try:
            screen = QApplication.primaryScreen()
            if screen:
                dpi_scale = screen.logicalDotsPerInch() / 96.0
            else:
                dpi_scale = 1.0
        except Exception:
            dpi_scale = 1.0
        if dpi_scale < 1.15:
            return _UART_DPI_PROFILES['normal']
        if dpi_scale < 1.38:
            return _UART_DPI_PROFILES['intermediate']
        if dpi_scale < 1.53:
            return _UART_DPI_PROFILES['compact']
        return _UART_DPI_PROFILES['ultra_compact']
    def show_welcome_message(self):
        '''Exibe mensagem de boas-vindas concisa'''
        welcome_msg = 'UART Monitor ÔÇö TECH UNION SOLUTIONS\nÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ\nBaudrate por processador:\n  MediaTek (MTK):       921600\n  Qualcomm (Snapdragon): 115200\n  Exynos / SPD:         teste automatico\n\nUso: Selecione porta > Auto Detectar > Conectar\nDica: desconecte e reconecte o cabo USB para disparar o boot.'
        self.signal_log.emit(welcome_msg, 'success')
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        p = self._profile
        layout = QHBoxLayout(central_widget)
        layout.setSpacing(p['spacing'])
        layout.setContentsMargins(p['margin'], p['margin'], p['margin'], p['margin'])
        left_panel = QVBoxLayout()
        left_panel.setSpacing(p['spacing'])
        conn_frame = self.setup_connection_frame()
        left_panel.addWidget(conn_frame, stretch=0)
        log_frame = QFrame()
        log_frame.setStyleSheet(f'\n            QFrame {{\n                background-color: {_UART_COLORS['bg_card']};\n                border: 1px solid {_UART_COLORS['border_light']};\n                border-radius: 6px;\n                padding: {p['spacing']}px;\n            }}\n        ')
        log_layout = QVBoxLayout(log_frame)
        log_layout.setContentsMargins(6, 4, 6, 4)
        log_title = QLabel(self.translation_manager.get_text('log_messages_title'))
        log_title.setStyleSheet(f'\n            font-size: {p['title_font']}px;\n            font-weight: bold;\n            color: {_UART_COLORS['primary_dark']};\n            padding: 3px;\n        ')
        log_layout.addWidget(log_title)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.log_text.setStyleSheet(f'\n            QTextEdit {{\n                background-color: #0a0a0a;\n                color: #00ff41;\n                border: 1px solid {_UART_COLORS['border']};\n                border-radius: 4px;\n                font-family: "Cascadia Code", "Consolas", "Courier New", monospace;\n                font-size: {p['body_font']}px;\n                padding: 8px;\n            }}\n        ')
        log_layout.addWidget(self.log_text)
        left_panel.addWidget(log_frame, stretch=1)
        if not _HAS_NEW_PARSER:
            self._health_frame = self._setup_health_panel()
            left_panel.addWidget(self._health_frame, stretch=0)
        layout.addLayout(left_panel, stretch=p['left_stretch'])
        right_panel = QVBoxLayout()
        if _HAS_NEW_PARSER:
            self._health_widget = UartHealthPanel(profile=p)
            right_panel.addWidget(self._health_widget, stretch=1)
        self._filters_frame_hidden = self.setup_filters()
        try:
            self._filters_frame_hidden.setVisible(False)
        except Exception:
            pass
        stats_frame = self.setup_stats_frame()
        right_panel.addWidget(stats_frame, stretch=0)
        layout.addLayout(right_panel, stretch=p['right_stretch'])
        C = _UART_COLORS
        self.setStyleSheet(''.join(['\n            QMainWindow, QWidget {\n                background-color: ', f'{C['bg_main']}', ';\n                color: ', f'{C['text_dark']}', ';\n            }\n            QFrame {\n                background-color: ', f'{C['bg_card']}', ';\n                border: 1px solid ', f'{C['border_light']}', ';\n                border-radius: 6px;\n                padding: ', f'{p['spacing']}', 'px;\n            }\n            QLabel {\n                color: ', f'{C['text_dark']}', ';\n                padding: 2px;\n                border: none;\n                background: transparent;\n            }\n            QPushButton {\n                padding: 6px ', f'{p['spacing']}', 'px;\n                font-size: ', f'{p['btn_font']}', 'px;\n                min-width: ', f'{p['btn_min_w']}', 'px;\n                min-height: ', f'{p['btn_min_h']}', 'px;\n                background-color: ', f'{C['primary']}', ';\n                color: white;\n                border-radius: 5px;\n                font-weight: 600;\n                border: none;\n                font-family: "Segoe UI", sans-serif;\n            }\n            QPushButton:hover {\n                background-color: ', f'{C['primary_dark']}', ';\n            }\n            QPushButton:pressed {\n                background-color: #0A3A8A;\n            }\n            QPushButton:disabled {\n                background-color: #B0BEC5;\n                color: #78909C;\n            }\n            QComboBox {\n                background-color: ', f'{C['bg_card']}', ';\n                color: ', f'{C['text_dark']}', ';\n                border: 1px solid ', f'{C['border']}', ';\n                border-radius: 5px;\n                padding: 4px 24px 4px 8px;\n                min-width: ', f'{p['combo_min_w']}', 'px;\n                font-size: ', f'{p['body_font']}', 'px;\n                font-family: "Segoe UI", sans-serif;\n            }\n            QComboBox:hover {\n                border-color: ', f'{C['primary']}', ';\n            }\n            QComboBox::drop-down {\n                subcontrol-origin: padding;\n                subcontrol-position: top right;\n                width: 22px;\n                border-left: 1px solid ', f'{C['border_light']}', ';\n                border-top-right-radius: 5px;\n                border-bottom-right-radius: 5px;\n                background-color: ', f'{C['bg_main']}', ';\n            }\n            QComboBox::drop-down:hover {\n                background-color: #d5dbdb;\n            }\n            QComboBox::down-arrow {\n                image: url(', f'{_SVG_SETA_DOWN}', ');\n                width: 10px;\n                height: 10px;\n            }\n        ']))
    def update_ports(self):
        '''Atualiza a lista de portas disponiveis com descricao e VID:PID.'''
        current_text = self.port_combo.currentText()
        current_device = current_text.split(' ÔÇö')[0].strip() if ' ÔÇö' in current_text else current_text
        ports_info = serial.tools.list_ports.comports()
        new_items = []
        for p in ports_info:
            desc = p.description or p.device
            vid_str = f' (VID:{p.vid:04X})' if p.vid else ''
            new_items.append(f'{p.device} ÔÇö {desc}{vid_str}')
        existing = [self.port_combo.itemText(i) for i in range(self.port_combo.count())]
        if new_items == existing:
            return
        self.port_combo.clear()
        self.port_combo.addItems(new_items)
        if current_device:
            for i, item in enumerate(new_items):
                if not item.startswith(current_device):
                    continue
                self.port_combo.setCurrentIndex(i)
                return
    def _auto_refresh_ports(self):
        '''Atualiza lista de portas COM silenciosamente (nao mexe se conectado).'''
        if self.is_connected:
            return
        if self._detect_thread and self._detect_thread.is_alive():
            return
        self.update_ports()
    def toggle_connection(self):
        '''Conecta/Desconecta da porta serial'''
        if not self.is_connected:
            try:
                port_text = self.port_combo.currentText()
                port = port_text.split(' ÔÇö')[0].strip() if ' ÔÇö' in port_text else port_text
                baud = int(self.baud_combo.currentText())
                if not port:
                    QMessageBox.warning(self, self.translation_manager.get_text('error_port_not_selected_title'), "Por favor, selecione uma porta COM v├ílida.\n\nSe nenhuma porta estiver dispon├¡vel:\n1. Verifique se o dispositivo est├í conectado\n2. Tente reconectar o cabo USB\n3. Use o bot├úo 'Atualizar' para buscar portas")
                    return
            except Exception:
                QMessageBox.critical(self, self.translation_manager.get_text('error_generic_title'), 'Falha ao iniciar o monitoramento.\n\nVerifique a porta serial selecionada, reconecte o cabo\ne tente novamente.')
            try:
                self._safe_close_port()
                self.serial_port = serial.Serial(port=port, baudrate=baud, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=0.1)
            except serial.SerialException as se:
                error_msg = str(se).lower()
                if 'permission' in error_msg or 'access' in error_msg:
                    QMessageBox.critical(self, self.translation_manager.get_text('error_port_in_use_title'), f'A porta {port} est├í em uso por outro programa.\n\n' + 'Poss├¡veis solu├º├Áes:\n' + '1. Feche outros programas que possam estar usando a porta\n' + '2. Verifique se h├í outro monitor serial aberto\n' + '3. Tente desconectar e reconectar o dispositivo\n' + '4. Reinicie o computador se o problema persistir')
                elif 'not found' in error_msg or 'n├úo existe' in error_msg:
                    QMessageBox.critical(self, self.translation_manager.get_text('error_port_not_found_title'), f'A porta {port} n├úo foi encontrada no sistema.\n\n' + 'Poss├¡veis solu├º├Áes:\n' + '1. Verifique se o dispositivo est├í conectado\n' + '2. Tente outra porta USB\n' + '3. Reinstale os drivers do dispositivo\n' + "4. Use o bot├úo 'Atualizar' para buscar portas dispon├¡veis")
                else:
                    QMessageBox.critical(self, self.translation_manager.get_text('error_connection_title'), f'N├úo foi poss├¡vel conectar ├á porta {port}.\n\n' + f'Erro: {str(se)}\n\n' + 'Sugest├Áes:\n' + '1. Verifique as configura├º├Áes da porta\n' + '2. Tente outro cabo USB\n' + '3. Verifique se o dispositivo est├í funcionando')
            self.is_connected = True
            self.connect_btn.setText(self.translation_manager.get_text('btn_disconnect'))
            self.signal_status.emit(self.translation_manager.get_text('status_connected').format(port=port, baud=baud))
            if _HAS_NEW_PARSER:
                self._parsed_state = create_empty_state()
                self._health_needs_update = False
                try:
                    try:
                        self._health_widget.mark_all_running()
                        self._health_timer.start()
                    except Exception:
                        pass
                except Exception:
                    QMessageBox.critical(self, self.translation_manager.get_text('error_generic_title'), 'Falha ao iniciar o monitoramento.\n\nVerifique a porta serial selecionada, reconecte o cabo\ne tente novamente.')
            self.read_thread = threading.Thread(target=self.read_serial, daemon=True)
            self.read_thread.start()
            return
        self.disconnect()
    def _safe_close_port(self):
        '''Fecha porta serial de forma segura, tratando handle invalido no Windows.'''
        try:
            if self.serial_port:
                if self.serial_port.is_open:
                    self.serial_port.close()
                self.serial_port = None
        except (serial.SerialException, OSError):
            self.serial_port = None
        time.sleep(0.15)
    def disconnect(self):
        '''Desconecta da porta serial com cleanup seguro.'''
        self.is_connected = False
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=2.0)
        self.read_thread = None
        self._safe_close_port()
        self.connect_btn.setText(self.translation_manager.get_text('btn_connect'))
        self.signal_status.emit(self.translation_manager.get_text('status_disconnected'))
        if _HAS_NEW_PARSER:
            try:
                self._health_timer.stop()
                self._health_needs_update = False
                self._health_widget.show_pending_tests()
                return
            except Exception:
                pass
    def auto_detect_baud(self):
        '''Auto detecta o baud rate correto ÔÇö executa em thread separada para nao congelar UI'''
        if self.is_connected:
            QMessageBox.warning(self, self.translation_manager.get_text('error_generic_title'), 'Desconecte primeiro antes de detectar o baudrate.')
            return
        if not self.port_combo.currentText():
            QMessageBox.warning(self, self.translation_manager.get_text('error_generic_title'), 'Selecione uma porta primeiro!')
            return
        self.connect_btn.setEnabled(False)
        detect_btn = self.sender()
        if detect_btn:
            detect_btn.setEnabled(False)
        self._detect_cancel = False
        self._stop_detect_btn.setVisible(True)
        self.status_label.setText('Detectando baud rate...')
        self.signal_log.emit('Iniciando deteccao automatica de baudrate...\n>> Desconecte e reconecte o cabo USB do aparelho para disparar o boot <<', 'info')
        port = self.port_combo.currentText()
        port = port.split(' ÔÇö')[0].strip() if ' ÔÇö' in port else port
        self._detect_thread = threading.Thread(target=self._auto_detect_worker, args=(port, detect_btn), daemon=True)
        self._detect_thread.start()
    def _stop_detection(self):
        '''Cancela a deteccao em andamento e faz cleanup imediato na UI'''
        if self._detect_cancel:
            return
        self._detect_cancel = True
        self._stop_detect_btn.setVisible(False)
        self.connect_btn.setEnabled(True)
        for btn in self.findChildren(QPushButton):
            btn.setEnabled(True)
        self.signal_log.emit('Deteccao cancelada pelo usuario.', 'warning')
        self.status_label.setText('Desconectado')
    def _score_baud_data(self, data):
        '''Analisa qualidade dos dados recebidos para determinar se o baud esta correto.'''
        import math
        from collections import Counter
        if not data:
            return {'score': 0, 'printable_pct': 0, 'entropy': 0, 'has_newlines': False, 'utf8_valid': False, 'null_pct': 0}
        total = len(data)
        counter = Counter(data)
        printable = sum((1 for b in data if b <= 32 if 32 <= 126 or b in (9, 10, 13)))
        printable_pct = printable / total * 100
        has_newlines = b'\n' in data or b'\r' in data
        null_pct = counter.get(0, 0) / total * 100
        ff_pct = counter.get(255, 0) / total * 100
        text_cluster = sum((counter.get(b, 0) for b in range(32, 127))) / total * 100
        entropy = 0
        for count in counter.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)
        norm_entropy = entropy / 8 * 100
        utf8_valid = False
        try:
            data.decode('utf-8')
            utf8_valid = True
        except UnicodeDecodeError:
            pass
        score = printable_pct
        if printable_pct > 65:
            score += text_cluster * 0.2
        if has_newlines and printable_pct > 60:
            score += 10
        if utf8_valid and printable_pct > 55:
            score += 8
        if total > 100 and printable_pct > 60:
            score += min(10, total / 200)
        if null_pct > 30:
            score -= 40
        if ff_pct > 30:
            score -= 30
        if norm_entropy > 75:
            score -= 15
        score = max(0, min(100, score))
        return {'score': score, 'printable_pct': printable_pct, 'entropy': norm_entropy, 'has_newlines': has_newlines, 'utf8_valid': utf8_valid, 'null_pct': null_pct}
    def _wait_for_boot_burst(self, ser, timeout_s=15.0):
        '''Aguarda o dispositivo comecar a transmitir e captura o burst completo.
        O boot de smartphones e disparado pelo cabo USB ou botao power.
        Esta funcao faz polling agressivo (3ms) esperando o primeiro byte chegar,
        e depois captura tudo ate o dispositivo parar de enviar.
        Retorna os bytes capturados ou b"" se timeout.
        '''
        data = b''
        deadline = time.perf_counter() + timeout_s
        while time.perf_counter() < deadline:
            if self._detect_cancel:
                return b''
            try:
                waiting = ser.in_waiting
            except (serial.SerialException, OSError):
                return b''
            if waiting > 0:
                data += ser.read(min(waiting, 4096))
                break
            time.sleep(0.003)
        if not data:
            return b''
        idle_cycles = 0
        capture_deadline = time.perf_counter() + 2.0
        while time.perf_counter() < capture_deadline:
            if self._detect_cancel:
                return data
            try:
                waiting = ser.in_waiting
            except (serial.SerialException, OSError):
                return data
            if waiting > 0:
                data += ser.read(min(waiting, 4096))
                idle_cycles = 0
            else:
                idle_cycles += 1
                if idle_cycles > 40:
                    return data
                time.sleep(0.003)
        return data
    def _auto_detect_worker(self, port, detect_btn):
        '''Detecta baudrate sincronizado com o boot do dispositivo.
        Para cada baudrate candidato:
        1. Configura o baud e aguarda o tecnico reconectar o cabo USB
        2. Quando o dispositivo liga e transmite, captura o burst
        3. Analisa a qualidade dos dados
        4. Se confianca alta, aceita. Se nao, pede novo replug no proximo baud.
        '''
        priority_bauds = [921600, 115200, 460800, 230400, 57600, 9600, 38400, 19200, 1382400]
        results = []
        ser = None
        try:
            ser = serial.Serial(port=port, baudrate=priority_bauds[0], timeout=0.05)
            ser.reset_input_buffer()
            if ser.in_waiting > 0:
                prebuf = ser.read(min(ser.in_waiting, 4096))
                time.sleep(0.05)
                extra = b''
                idle = 0
                cap_end = time.perf_counter() + 1.5
                while time.perf_counter() < cap_end:
                    if self._detect_cancel:
                        break
            try:
                w = ser.in_waiting
            except (serial.SerialException, OSError):
                pass
            else:
                if w > 0:
                    extra += ser.read(min(w, 4096))
                    idle = 0
                else:
                    idle += 1
                    if idle > 30:
                        pass
                    else:
                        time.sleep(0.003)
                if time.perf_counter() < cap_end:
                    pass
                all_data = prebuf + extra
                if len(all_data) > 10:
                    first_baud = priority_bauds[0]
                    self.signal_log.emit(f'Transmissao ativa detectada! ({len(all_data)} bytes a {first_baud})', 'info')
                    score_info = self._score_baud_data(all_data)
                    score_info['baudrate'] = first_baud
                    score_info['bytes'] = len(all_data)
                    results.append(score_info)
                    nl_str = 'sim' if score_info['has_newlines'] else 'nao'
                    self.signal_log.emit(f'  {first_baud}: {len(all_data)}B, score={score_info['score']:.0f}/100 ({score_info['printable_pct']:.0f}% legivel, newlines={nl_str})', 'normal')
                    if score_info['score'] > 75:
                        self.signal_log.emit(f'  >> Baud {first_baud} confirmado!', 'success')
                        ser.close()
                        ser = None
                        self._finish_detection(results, detect_btn)
        except serial.SerialException:
            self.signal_log.emit('Nao foi possivel acessar a porta selecionada. Verifique o cabo USB, drivers e se outro programa esta usando a porta.', 'error')
            self.signal_status.emit('Falha na comunicacao')
            QTimer.singleShot(0, (lambda: self._on_detect_failed(detect_btn)))
        except Exception:
            self.signal_log.emit('Ocorreu uma falha interna ao iniciar a deteccao. Reconecte o cabo e tente novamente.', 'error')
            self.signal_status.emit('Falha interna')
            QTimer.singleShot(0, (lambda: self._on_detect_failed(detect_btn)))
        for i, baud in enumerate(priority_bauds):
            if self._detect_cancel:
                break
            ser.baudrate = baud
            ser.reset_input_buffer()
            self.signal_status.emit(f'Aguardando boot em {baud} baud...')
            self.signal_log.emit(f'\n[{i + 1}/{len(priority_bauds)}] Testando {baud} baud ÔÇö desconecte e reconecte o cabo USB agora...', 'info')
            data = self._wait_for_boot_burst(ser, timeout_s=12.0)
            if self._detect_cancel:
                break
            if not data:
                self.signal_log.emit(f'  {baud}: nenhum dado (timeout)', 'normal')
                continue
            score_info = self._score_baud_data(data)
            score_info['baudrate'] = baud
            score_info['bytes'] = len(data)
            results.append(score_info)
            nl_str = 'sim' if score_info['has_newlines'] else 'nao'
            self.signal_log.emit(f'  {baud}: {len(data)}B, score={score_info['score']:.0f}/100 ({score_info['printable_pct']:.0f}% legivel, newlines={nl_str})', 'normal')
            if score_info['score'] > 75 and len(data) > 20:
                self.signal_log.emit(f'  >> Baud {baud} confirmado!', 'success')
                break
            if not score_info['score'] > 30:
                continue
            self.signal_log.emit('  Dados recebidos mas confianca media. Testando proximo baud...', 'warning')
            self.signal_log.emit('>> Desconecte e reconecte o cabo USB novamente <<', 'warning')
            continue
        if ser:
            ser.close()
            ser = None
        self._finish_detection(results, detect_btn)
        if ser:
            try:
                ser.close()
            except Exception:
                return
    def _finish_detection(self, results, detect_btn):
        '''Finaliza a deteccao e mostra resultado ao tecnico.'''
        if self._detect_cancel:
            return
        results.sort(key=(lambda x: x['score']), reverse=True)
        best = results[0] if results else None
        if best and best['score'] > 30:
            detected = best['baudrate']
            confidence = best['score']
            if len(results) > 1:
                self.signal_log.emit('Ranking:', 'info')
                for r in results[:3]:
                    marker = ' <<' if r['baudrate'] == detected else ''
                    self.signal_log.emit(f'  {r['baudrate']}: score={r['score']:.0f}, {r['bytes']}B{marker}', 'normal')
            self.signal_log.emit(f'Baud detectado: {detected} (confianca: {confidence:.0f}/100)', 'success')
            self.signal_status.emit(f'Detectado: {detected} baud')
            conf = confidence
            QTimer.singleShot(0, (lambda: self._on_detect_complete(detected, detect_btn, conf)))
            return
        if results:
            self.signal_log.emit('Nenhum baud com confianca alta. Candidatos:', 'warning')
            for r in results[:3]:
                self.signal_log.emit(f'  {r['baudrate']}: score={r['score']:.0f}, {r['bytes']}B', 'normal')
        else:
            self.signal_log.emit('Nenhum dado recebido.\nVerifique: cabo USB-TTL conectado? GND comum? Aparelho ligado?', 'error')
        self.signal_status.emit('Deteccao falhou')
        QTimer.singleShot(0, (lambda: self._on_detect_failed(detect_btn)))
    def _on_detect_complete(self, detected_baud, detect_btn, confidence=0):
        '''Callback na UI thread apos deteccao com sucesso.
        Se confianca >= 85: auto-conecta e libera o tecnico para o diagnostico.
        Se confianca < 85: seta o baud e deixa o tecnico decidir.
        '''
        self._stop_detect_btn.setVisible(False)
        self.connect_btn.setEnabled(True)
        if detect_btn:
            detect_btn.setEnabled(True)
        self.baud_combo.setCurrentText(str(detected_baud))
        if confidence >= 85:
            self.signal_log.emit(f'\nBaudrate {detected_baud} confirmado! Conectando automaticamente...', 'success')
            self.toggle_connection()
            self.signal_log.emit('Pronto para diagnostico! Os dados UART estao sendo recebidos.', 'success')
            return
        self.signal_log.emit(f"\nBaudrate {detected_baud} configurado (confianca media).\nClique em 'Conectar' para testar.\nSe os dados nao fizerem sentido, rode a deteccao novamente.", 'info')
    def _on_detect_failed(self, detect_btn):
        '''Callback na UI thread apos deteccao falhar ÔÇö libera UI imediatamente.'''
        self._stop_detect_btn.setVisible(False)
        self.connect_btn.setEnabled(True)
        if detect_btn:
            detect_btn.setEnabled(True)
        self.signal_log.emit("\nDeteccao nao encontrou baudrate com confianca.\nTente novamente desconectando e reconectando o cabo USB.\nSe persistir, use 'Testar Baudrates' para teste manual.", 'warning')
    def show_baud_test_assistant(self):
        '''Mostra assistente para testar baudrates manualmente'''
        from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QTextEdit, QPushButton, QLabel, QProgressBar)
        dialog = QDialog(self)
        dialog.setWindowTitle('Assistente de Teste de Baudrates')
        dialog.setMinimumSize(700, 500)
        dialog.setStyleSheet('\n            QDialog {\n                background-color: #f0f0f0;\n            }\n            QLabel {\n                font-weight: bold;\n                color: #333;\n            }\n            QListWidget {\n                background: white;\n                border: 1px solid #ddd;\n                border-radius: 4px;\n            }\n            QTextEdit {\n                background: white;\n                border: 1px solid #ddd;\n                border-radius: 4px;\n                font-family: monospace;\n            }\n        ')
        layout = QVBoxLayout(dialog)
        instructions = QLabel("Como usar o Assistente:\n1. Selecione um baudrate da lista abaixo\n2. Clique em 'Testar' para conectar temporariamente\n3. Observe os dados recebidos na area inferior\n4. Se os dados estiverem legiveis, use 'Aplicar' para definir o baudrate")
        instructions.setWordWrap(True)
        instructions.setStyleSheet('\n            background-color: #E8F5E9;\n            border: 2px solid #4CAF50;\n            border-radius: 8px;\n            padding: 10px;\n            margin: 5px;\n        ')
        layout.addWidget(instructions)
        baud_list = QListWidget()
        recommended_bauds = [('921600 - MediaTek', 921600), ('460800 - MediaTek', 460800), ('230400 - Qualcomm', 230400), ('115200 - Universal', 115200), ('57600', 57600), ('38400', 38400), ('19200', 19200), ('9600', 9600), ('1382400', 1382400)]
        for label, baud in recommended_bauds:
            baud_list.addItem(f'{label}')
        layout.addWidget(baud_list)
        data_label = QLabel('Dados Recebidos:')
        layout.addWidget(data_label)
        data_area = QTextEdit()
        data_area.setMaximumHeight(150)
        data_area.setPlaceholderText('Os dados recebidos aparecer├úo aqui...')
        layout.addWidget(data_area)
        button_layout = QHBoxLayout()
        test_btn = QPushButton('Testar Selecionado')
        apply_btn = QPushButton('Aplicar e Conectar')
        close_btn = QPushButton('Fechar')
        button_layout.addWidget(test_btn)
        button_layout.addWidget(apply_btn)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        current_test_baud = None
        test_serial = None
        def test_selected_baud():
            nonlocal test_serial, current_test_baud
            if baud_list.currentRow() < 0:
                QMessageBox.warning(dialog, 'Erro', 'Selecione um baudrate primeiro!')
                return
            try:
                data_area.clear()
                data_area.append(f'Testando {selected_baud} baud por 3 segundos...')
                test_serial = serial.Serial(port, selected_baud, timeout=0.1)
                current_test_baud = selected_baud
                start_time = time.time()
                received_data = b''
                while time.time() - start_time < 3:
                    if test_serial.in_waiting:
                        data = test_serial.read(test_serial.in_waiting)
                        received_data += data
                try:
                    text = data.decode('utf-8', errors='replace')
                    clean_text = ''.join((c for c in text if c.isprintable() or c in '\n\r'))
                    if clean_text.strip():
                        data_area.append(clean_text.strip())
                except:
                    pass
                else:
                    time.sleep(0.1)
                    if time.time() - start_time < 3:
                        pass
                    if received_data:
                        printable_chars = sum((1 for byte in received_data if byte <= 32 if 32 <= 126 or byte in (10, 13)))
                        printable_ratio = printable_chars / len(received_data)
                        data_area.append(f'\nAnalise: {len(received_data)} bytes, {printable_ratio:.1%} legivel')
                        if printable_ratio > 0.7:
                            data_area.append('Dados parecem legiveis - baudrate provavelmente correto!')
            except Exception:
                data_area.append('Nao foi possivel testar. Reconecte o cabo e tente novamente.')
                try:
                    data_area.clear()
                    data_area.append(f'Testando {selected_baud} baud por 3 segundos...')
                    test_serial = serial.Serial(port, selected_baud, timeout=0.1)
                    current_test_baud = selected_baud
                    start_time = time.time()
                    received_data = b''
                    while time.time() - start_time < 3:
                        if test_serial.in_waiting:
                            data = test_serial.read(test_serial.in_waiting)
                            received_data += data
                        time.sleep(0.1)
                    if received_data:
                        printable_chars = sum((1 for byte in received_data if byte <= 32 if 32 <= 126 or byte in (10, 13)))
                        printable_ratio = printable_chars / len(received_data)
                        data_area.append(f'\nAnalise: {len(received_data)} bytes, {printable_ratio:.1%} legivel')
                        if printable_ratio > 0.7:
                            data_area.append('Dados parecem legiveis - baudrate provavelmente correto!')
                        elif printable_ratio > 0.3:
                            data_area.append('Alguns dados legiveis - pode estar correto')
                        else:
                            data_area.append('Dados ilegiveis - tente outro baudrate')
                    else:
                        data_area.append('Nenhum dado recebido - verifique conexao ou tente outro baudrate')
                except Exception:
                    data_area.append('Nao foi possivel testar. Reconecte o cabo e tente novamente.')
                finally:
                    if test_serial:
                        if test_serial.is_open:
                            test_serial.close()
            if test_serial:
                if test_serial.is_open:
                    test_serial.close()
        def apply_and_connect():
            if current_test_baud:
                self.baud_combo.setCurrentText(str(current_test_baud))
                dialog.accept()
                if not self.is_connected:
                    self.toggle_connection()
                    return
                return
            QMessageBox.warning(dialog, 'Erro', 'Teste um baudrate primeiro!')
        def close_dialog():
            if test_serial and test_serial.is_open:
                test_serial.close()
            dialog.reject()
        test_btn.clicked.connect(test_selected_baud)
        apply_btn.clicked.connect(apply_and_connect)
        close_btn.clicked.connect(close_dialog)
        dialog.exec_()
    def read_serial(self):
        '''Thread de leitura da porta serial'''
        buffer = ''
        while self.is_connected:
            try:
                if self.serial_port and self.serial_port.is_open and self.serial_port.in_waiting:
                    data = self.serial_port.read(self.serial_port.in_waiting)
                    self.rx_count += len(data)
                try:
                    text = data.decode('utf-8', errors='replace')
                    text = ''.join((c for c in text if c.isprintable() or c in '\n\r\t'))
                    buffer += text
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        if line:
                            self.process_line(line)
                except Exception:
                    pass
                else:
                    time.sleep(0.01)
            except (serial.SerialException, OSError):
                if self.is_connected:
                    self.is_connected = False
                    self.signal_status.emit('Porta desconectada ÔÇö verifique o cabo USB')
                self._safe_close_port()
            except Exception:
                if not self.is_connected:
                    pass
    def _init_health_pending(self):
        '''Mostra testes pendentes no health panel (chamado via QTimer da main thread).'''
        try:
            if hasattr(self, '_health_widget'):
                if self._health_widget:
                    self._health_widget.show_pending_tests()
                    return
                return
        except Exception:
            pass
    def _poll_health_update(self):
        '''Timer na main thread ÔÇö verifica se o parser detectou algo novo.'''
        if not self._health_needs_update:
            return
        self._health_needs_update = False
        try:
            if hasattr(self, '_health_widget'):
                if self._health_widget:
                    self._health_widget.update_from_state(self._parsed_state)
                    return
                return
        except Exception:
            pass
    def process_line(self, line):
        '''Processa uma linha do log ÔÇö atualiza health e anota terminal.'''
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        if _HAS_NEW_PARSER:
            try:
                _baud = self._get_current_baud_safe()
                if update_health_state_auto(self._parsed_state, line, baud_rate=_baud):
                    self._health_needs_update = True
            except Exception:
                pass
        else:
            self._check_hw_health(line)
        classified = None
        if _HAS_NEW_PARSER:
            try:
                _platform = self._parsed_state.get('_internal', {}).get('platform_confirmed')
                classified = classify_line_auto(line, platform=_platform)
            except Exception:
                classified = None
        if classified:
            marker = classified.get('marker', '')
            severity = classified.get('severity', 'info')
            category = classified.get('category', '')
            self._bump_internal_count(category, marker)
            msg = f'[{timestamp}] [{marker}] {line}'
            _sev_to_type = {'ok': 'success', 'error': 'error', 'warn': 'warning', 'info': 'info'}
            self.signal_log.emit(msg, _sev_to_type.get(severity, 'normal'))
            return
        self.signal_log.emit(f'[{timestamp}] {line}', 'normal')
    def _bump_internal_count(self, category, marker):
        '''Incrementa contador interno para uso em reprocessamento/estatisticas.'''
        try:
            if not hasattr(self, '_smart_counts'):
                self._smart_counts = {}
            key = f'{category}::{marker}'
            self._smart_counts[key] = self._smart_counts.get(key, 0) + 1
            return
        except Exception:
            return
    def send_command(self):
        '''Envia comando pela porta serial'''
        if not self.is_connected:
            QMessageBox.warning(self, 'Erro', 'Nao conectado a porta serial.')
            return
        try:
            command = self.cmd_input.currentText().strip()
            if not command:
                QMessageBox.warning(self, 'Erro', 'Digite um comando primeiro.')
                return
        except Exception:
            self.signal_error.emit('System', '', 'Falha ao enviar comando.')
            QMessageBox.critical(self, 'Erro', 'Nao foi possivel enviar o comando.\nVerifique a conexao e tente novamente.')
        try:
            existing_items = [self.cmd_input.itemText(i) for i in range(self.cmd_input.count())]
            if command not in existing_items:
                self.cmd_input.addItem(command)
            data = f'{command}\r\n'.encode('utf-8', errors='replace')
            self.serial_port.write(data)
            self.tx_count += len(data)
            self.cmd_input.setCurrentText('')
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            self.signal_log.emit(f'[{timestamp}] Enviado: {command}', 'command')
            return
        except Exception:
            self.signal_error.emit('System', '', 'Falha ao enviar comando.')
            QMessageBox.critical(self, 'Erro', 'Nao foi possivel enviar o comando.\nVerifique a conexao e tente novamente.')
    _LOG_COLORS = {'error': '#ff5555', 'warning': '#ffb86c', 'success': '#50fa7b', 'info': '#8be9fd', 'command': '#bd93f9', 'normal': '#e0e0e0', 'timestamp': '#6272a4', 'subsystem': '#ff79c6'}
    _SUBSYSTEM_RE = re.compile('(\\[(?:RGU|PWRAP|ATF|DOE_ENV|PMIC)\\]|====> GZ|INFO:|NOTICE:|WARNING:)')
    def update_log(self, message, msg_type):
        '''Atualiza a area de log com coloracao por segmento.'''
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        ts_match = re.match('(\\[\\d{2}:\\d{2}:\\d{2}\\.\\d+\\])\\s*(.*)', message)
        if ts_match and msg_type == 'normal':
            ts_part = ts_match.group(1) + ' '
            body = ts_match.group(2)
            fmt_ts = cursor.charFormat()
            fmt_ts.setForeground(QColor(self._LOG_COLORS['timestamp']))
            cursor.insertText(ts_part, fmt_ts)
            sub_match = self._SUBSYSTEM_RE.search(body)
            if sub_match:
                pre = body[:sub_match.start()]
                tag = sub_match.group(0)
                post = body[sub_match.end():]
                fmt_body = cursor.charFormat()
                fmt_body.setForeground(QColor(self._LOG_COLORS['normal']))
                if pre:
                    cursor.insertText(pre, fmt_body)
                fmt_sub = cursor.charFormat()
                fmt_sub.setForeground(QColor(self._LOG_COLORS['subsystem']))
                cursor.insertText(tag, fmt_sub)
                cursor.insertText(post + '\n', fmt_body)
            else:
                fmt_body = cursor.charFormat()
                fmt_body.setForeground(QColor(self._LOG_COLORS['normal']))
                cursor.insertText(body + '\n', fmt_body)
        else:
            color_key = msg_type if msg_type in self._LOG_COLORS else 'normal'
            fmt = cursor.charFormat()
            fmt.setForeground(QColor(self._LOG_COLORS[color_key]))
            cursor.insertText(message + '\n', fmt)
        self.log_text.setTextCursor(cursor)
        self.log_text.ensureCursorVisible()
        if self.log_text.document().lineCount() > 10000:
            trim_cursor = self.log_text.textCursor()
            trim_cursor.movePosition(QTextCursor.Start)
            for _ in range(2000):
                trim_cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor)
            trim_cursor.removeSelectedText()
    def handle_error(self, category, name, message):
        '''Manipula erros. Nunca expoe detalhes tecnicos ao tecnico de bancada.'''
        if not category or not name:
            msg_low = (message or '').lower()
            if any((k in msg_low for k in ('oserror', 'clearcommerror', 'identificador', 'permission denied', 'access is denied', 'access denied', 'access negado', 'serialexception', 'device not configured', 'no such file', 'winerror', 'errno'))):
                safe_msg = 'Perda de comunicacao com a porta serial. Reconecte o cabo USB e verifique se outro programa nao esta usando a porta.'
            elif any((k in msg_low for k in ('exception', 'traceback', 'attributeerror', 'typeerror', 'valueerror', 'keyerror', 'importerror', 'modulenotfound'))):
                safe_msg = 'Falha interna de comunicacao. Reconecte o dispositivo e tente novamente.'
            elif any((k in msg_low for k in ('timeout', 'timed out'))):
                safe_msg = 'O aparelho nao respondeu no tempo esperado. Reconecte e tente novamente.'
            else:
                safe_msg = 'Ocorreu um problema na comunicacao. Reconecte o cabo e tente novamente.'
            self.signal_log.emit(f'[Sistema] {safe_msg}', 'warning')
            return
        if category not in self.message_counts:
            self.message_counts[category] = {}
        if name not in self.message_counts[category]:
            self.message_counts[category][name] = 0
        self.message_counts[category][name] += 1
        count = self.message_counts[category][name]
        self.update_filter_count(category, name, count)
    def update_status(self, status):
        '''Atualiza o status da conex├úo'''
        C = _UART_COLORS
        p = self._profile
        self.status_label.setText(status)
        if 'Conectado' in status or 'Connected' in status:
            self.status_label.setStyleSheet(f'color: {C['success']}; font-weight: 600; font-size: {p['small_font']}px;')
            return
        self.status_label.setStyleSheet(f'color: {C['error']}; font-weight: 600; font-size: {p['small_font']}px;')
    def update_statistics(self):
        '''Atualiza estat├¡sticas de RX/TX'''
        if self.is_connected:
            if self.serial_port:
                self.rx_label.setText(f'RX: {self.format_bytes(self.rx_count)}')
                self.tx_label.setText(f'TX: {self.format_bytes(self.tx_count)}')
                for category in self.message_patterns:
                    total = sum(self.message_counts[category].values())
                    for child in self.findChildren(QLabel):
                        if child.text().startswith(f'{category}:'):
                            child.setText(f'{category}: {total}')
    def format_bytes(self, bytes):
        '''Formata bytes para formato leg├¡vel'''
        for unit in ('B', 'KB', 'MB', 'GB'):
            if bytes < 1024:
                return f'{bytes:.1f} {unit}'
            bytes /= 1024
        return f'{bytes:.1f} TB'
    def clear_category_counts(self):
        '''Limpa os contadores de uma categoria'''
        category = self.sender().property('category')
        if category in self.message_counts:
            for name in self.message_counts[category]:
                self.message_counts[category][name] = 0
                self.update_filter_count(category, name, 0)
    def update_filter_count(self, category, name, count):
        '''Atualiza o contador de um filtro especifico via objectName unico.'''
        obj_name = f'cnt_{category}_{name}'
        lbl = self.findChild(QLabel, obj_name)
        if not lbl:
            return
        C = _UART_COLORS
        p = self._profile
        font_sz = max(9, p.get('small_font', 10) - 1)
        lbl.setText(str(count))
        if count == 0:
            bg, fg, border = C['bg_main'], C['text_dark'], C['border_light']
        elif count > 10:
            bg, fg, border = C['error'], '#ffffff', C['error']
        elif count > 5:
            bg, fg, border = C['warning'], '#ffffff', C['warning']
        else:
            bg, fg, border = '#e3f2fd', C['primary_dark'], C['primary_dark']
        lbl.setStyleSheet(f'\n            QLabel {{\n                background-color: {bg};\n                color: {fg};\n                border: 1px solid {border};\n                border-radius: 8px;\n                font-size: {font_sz}px;\n                font-weight: bold;\n                padding: 1px 4px;\n            }}\n        ')
    def show_repair_steps(self, category, name):
        '''Mostra uma janela com os passos de reparo para o erro selecionado'''
        pattern_info = self.message_patterns[category][name]
        dialog = QDialog(self)
        dialog.setWindowTitle(f'Detalhes: {name}')
        dialog.setModal(True)
        dialog.resize(500, 400)
        layout = QVBoxLayout(dialog)
        title = QLabel(name)
        title.setStyleSheet(f'\n            font-size: 16px;\n            font-weight: bold;\n            color: {self.category_colors[category]};\n            padding: 10px;\n            background-color: {self.category_bg_colors[category]};\n            border-radius: 5px;\n            margin-bottom: 10px;\n        ')
        layout.addWidget(title)
        desc = QLabel(f'Descri├º├úo: {pattern_info['description']}')
        desc.setStyleSheet('font-size: 12px; padding: 5px; margin-bottom: 10px;')
        desc.setWordWrap(True)
        layout.addWidget(desc)
        count = self.message_counts[category][name]
        count_label = QLabel(f'Ocorr├¬ncias detectadas: {count}')
        if pattern_info.get('type') == 'error':
            count_label.setStyleSheet('font-weight: bold; color: #E53935;')
        elif pattern_info.get('type') == 'warning':
            count_label.setStyleSheet('font-weight: bold; color: #F57C00;')
        else:
            count_label.setStyleSheet('font-weight: bold; color: #1976D2;')
        layout.addWidget(count_label)
        msg_type = pattern_info.get('type', 'info').upper()
        type_colors = {'ERROR': '#f44336', 'WARNING': '#ff9800', 'INFO': '#2196f3', 'SUCCESS': '#4caf50'}
        type_label = QLabel(f'Tipo: {msg_type}')
        type_label.setStyleSheet(f'font-weight: bold; color: {type_colors.get(msg_type, '#666')};')
        layout.addWidget(type_label)
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        steps_label = QLabel('Informacoes e Passos:')
        steps_label.setStyleSheet('font-weight: bold; font-size: 14px; margin-top: 10px;')
        layout.addWidget(steps_label)
        steps_text = QTextEdit()
        steps_content = ''
        for i, step in enumerate(pattern_info['repair_steps'], 1):
            steps_content += f'{i}. {step}\n\n'
        steps_text.setPlainText(steps_content.strip())
        steps_text.setReadOnly(True)
        steps_text.setStyleSheet('\n            QTextEdit {\n                background-color: #f8f9fa;\n                border: 1px solid #dee2e6;\n                border-radius: 5px;\n                padding: 10px;\n                font-size: 12px;\n                line-height: 1.4;\n            }\n        ')
        layout.addWidget(steps_text)
        close_btn = QPushButton('Fechar')
        close_btn.clicked.connect(dialog.accept)
        close_btn.setStyleSheet('\n            QPushButton {\n                background-color: #1976D2;\n                color: white;\n                border: none;\n                padding: 8px 16px;\n                border-radius: 4px;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background-color: #1565C0;\n            }\n        ')
        layout.addWidget(close_btn)
        dialog.exec_()
    def closeEvent(self, event):
        '''Manipula fechamento da janela com cleanup completo.'''
        if hasattr(self, '_port_refresh_timer'):
            self._port_refresh_timer.stop()
        if hasattr(self, 'stats_timer'):
            self.stats_timer.stop()
        self._detect_cancel = True
        self.disconnect()
        event.accept()
    def setup_filters(self):
        '''Configura o painel de filtros ÔÇö tema UNION BLUE, compacto e responsivo.'''
        p = self._profile
        C = _UART_COLORS
        filters_frame = QFrame()
        filters_frame.setObjectName('uart_filters_panel')
        filters_frame.setStyleSheet(f'\n            QFrame#uart_filters_panel {{\n                background-color: {C['bg_card']};\n                border: 1px solid {C['border_light']};\n                border-radius: 6px;\n            }}\n        ')
        filters_layout = QVBoxLayout(filters_frame)
        filters_layout.setSpacing(4)
        filters_layout.setContentsMargins(6, 6, 6, 6)
        header_row = QHBoxLayout()
        title = QLabel('Filtros')
        title.setStyleSheet(f'\n            font-size: {p['title_font']}px;\n            font-weight: bold;\n            color: {C['primary_dark']};\n            border: none; background: transparent; padding: 2px;\n        ')
        header_row.addWidget(title)
        header_row.addStretch()
        _qbtn = f'\n            QPushButton {{\n                border: 1px solid {C['border']};\n                padding: 4px 10px;\n                border-radius: 4px;\n                font-size: {p['small_font']}px;\n                font-weight: 600;\n                background-color: #e8eef5;\n                color: {C['text_dark']};\n            }}\n            QPushButton:hover {{ background-color: #d0dff0; border-color: {C['primary']}; }}\n            QPushButton:pressed {{ background-color: #bbdefb; }}\n        '
        show_all_btn = QPushButton('Todos')
        show_all_btn.setStyleSheet(_qbtn)
        show_all_btn.clicked.connect(self.uncheck_all_filters)
        header_row.addWidget(show_all_btn)
        errors_only_btn = QPushButton('Falhas')
        errors_only_btn.setStyleSheet(f'\n            QPushButton {{\n                border: 1px solid {C['error']};\n                padding: 4px 10px;\n                border-radius: 4px;\n                font-size: {p['small_font']}px;\n                font-weight: 600;\n                background-color: #fce4ec;\n                color: {C['error']};\n            }}\n            QPushButton:hover {{ background-color: #ffcdd2; }}\n            QPushButton:pressed {{ background-color: {C['error']}; color: white; }}\n        ')
        errors_only_btn.clicked.connect(self.show_errors_only)
        header_row.addWidget(errors_only_btn)
        reprocess_btn = QPushButton('Reprocessar')
        reprocess_btn.setStyleSheet(f'\n            QPushButton {{\n                border: 1px solid {C['primary_dark']};\n                padding: 4px 10px;\n                border-radius: 4px;\n                font-size: {p['small_font']}px;\n                font-weight: 600;\n                background-color: #e3f2fd;\n                color: {C['primary_dark']};\n            }}\n            QPushButton:hover {{ background-color: #bbdefb; }}\n            QPushButton:pressed {{ background-color: {C['primary']}; color: white; }}\n        ')
        reprocess_btn.setToolTip(self.translation_manager.get_text('tooltip_reprocess'))
        reprocess_btn.clicked.connect(self.reprocess_existing_logs)
        header_row.addWidget(reprocess_btn)
        filters_layout.addLayout(header_row)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f'\n            QScrollArea {{ border: none; background: transparent; }}\n            QScrollBar:vertical {{\n                background: {C['bg_main']}; width: 5px; border-radius: 2px;\n            }}\n            QScrollBar::handle:vertical {{\n                background: {C['border']}; border-radius: 2px; min-height: 20px;\n            }}\n            QScrollBar::handle:vertical:hover {{ background: {C['primary']}; }}\n            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}\n        ')
        scroll_content = QWidget()
        scroll_content.setStyleSheet('background: transparent;')
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(6)
        scroll_layout.setContentsMargins(2, 2, 2, 2)
        _cat_colors_border = {'Inicializacao': '#27ae60', 'Diagnostico': C['primary'], 'Falhas': C['error'], 'Avisos': C['warning']}
        category_order = ['Falhas', 'Avisos', 'Inicializacao', 'Diagnostico']
        for category in category_order:
            if category not in self.message_patterns:
                continue
            patterns = self.message_patterns[category]
            border_c = _cat_colors_border.get(category, C['border'])
            cat_frame = QFrame()
            cat_frame.setStyleSheet(f'\n                QFrame {{\n                    background-color: {C['bg_card']};\n                    border: 1px solid {C['border_light']};\n                    border-left: 3px solid {border_c};\n                    border-radius: 4px;\n                    padding: 0;\n                }}\n            ')
            cat_lay = QVBoxLayout(cat_frame)
            cat_lay.setContentsMargins(8, 4, 6, 4)
            cat_lay.setSpacing(2)
            cat_title = QLabel(category)
            cat_title.setStyleSheet(f'\n                font-weight: bold; font-size: {p['small_font']}px;\n                color: {border_c}; border: none; background: transparent;\n                padding: 1px 0;\n            ')
            cat_lay.addWidget(cat_title)
            self.message_checks[category] = {}
            for name in patterns:
                row_lay = QHBoxLayout()
                row_lay.setContentsMargins(0, 0, 0, 0)
                row_lay.setSpacing(4)
                check = QCheckBox(name)
                check.setChecked(False)
                check.setStyleSheet(f'\n                    QCheckBox {{\n                        padding: 1px; font-size: {p['small_font']}px;\n                        color: {C['text_dark']}; border: none; background: transparent;\n                    }}\n                    QCheckBox::indicator {{\n                        width: 14px; height: 14px;\n                        border: 1px solid {C['border']};\n                        border-radius: 3px; background: white;\n                    }}\n                    QCheckBox::indicator:checked {{\n                        background: {C['primary']};\n                        border-color: {C['primary_dark']};\n                    }}\n                    QCheckBox:hover {{ color: {C['primary']}; }}\n                ')
                self.message_checks[category][name] = check
                row_lay.addWidget(check, stretch=1)
                count_label = QLabel('0')
                count_label.setObjectName(f'cnt_{category}_{name}')
                count_label.setFixedWidth(32)
                count_label.setAlignment(Qt.AlignCenter)
                count_label.setStyleSheet(f'\n                    QLabel {{\n                        background-color: {C['bg_main']};\n                        color: {C['text_dark']};\n                        border: 1px solid {C['border_light']};\n                        border-radius: 8px;\n                        font-size: {p['small_font'] - 1}px;\n                        font-weight: bold;\n                        padding: 1px 4px;\n                    }}\n                ')
                row_lay.addWidget(count_label)
                details_btn = QPushButton('?')
                details_btn.setFixedSize(20, 20)
                details_btn.setStyleSheet(f'\n                    QPushButton {{\n                        background: transparent; border: 1px solid {C['border_light']};\n                        border-radius: 10px; font-size: 10px; font-weight: bold;\n                        color: {C['primary']};\n                    }}\n                    QPushButton:hover {{\n                        background: #e3f2fd; border-color: {C['primary']};\n                    }}\n                ')
                details_btn.clicked.connect((lambda checked, c=category, n=name: self.show_repair_steps(c, n)))
                row_lay.addWidget(details_btn)
                cat_lay.addLayout(row_lay)
                continue
            scroll_layout.addWidget(cat_frame)
            continue
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        filters_layout.addWidget(scroll)
        return filters_frame
    def setup_connection_frame(self):
        '''Configura o frame de conex├úo'''
        p = self._profile
        C = _UART_COLORS
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(p['spacing'])
        processor_tips = QLabel(self.translation_manager.get_text('processor_tips'))
        processor_tips.setStyleSheet(f'\n            QLabel {{\n                background-color: #e8f4fd;\n                border: 1px solid {C['border']};\n                border-left: 3px solid {C['primary']};\n                border-radius: 4px;\n                padding: 8px;\n                font-size: {p['small_font']}px;\n                color: {C['primary_dark']};\n                font-weight: 500;\n            }}\n        ')
        processor_tips.setWordWrap(True)
        layout.addWidget(processor_tips)
        config_frame = QFrame()
        config_layout = QHBoxLayout(config_frame)
        settings = QHBoxLayout()
        port_layout = QVBoxLayout()
        port_label = QLabel(self.translation_manager.get_text('label_com_port'))
        port_label.setStyleSheet(f'font-weight: 600; color: {C['text_dark']}; font-size: {p['body_font']}px;')
        self.port_combo = QComboBox()
        self.port_combo.setToolTip(self.translation_manager.get_text('tooltip_port_combo'))
        self.update_ports()
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_combo)
        baud_layout = QVBoxLayout()
        baud_label = QLabel(self.translation_manager.get_text('label_baud_rate'))
        baud_label.setStyleSheet(f'font-weight: 600; color: {C['text_dark']}; font-size: {p['body_font']}px;')
        self.baud_combo = QComboBox()
        baudrates = ['1382400', '921600', '460800', '256000', '230400', '128000', '115200', '76800', '57600', '43000', '38400', '19200', '14400', '9600', '4800', '2400', '1200']
        self.baud_combo.addItems(baudrates)
        self.baud_combo.setCurrentText('921600')
        self.baud_combo.setToolTip('Selecione o baud rate:\nÔÇó 921600/460800: MediaTek comum\nÔÇó 115200/230400: Qualcomm comum\nÔÇó 57600/38400: Dispositivos antigos\nÔÇó 1M-6M: Dispositivos de alta velocidade\nÔÇó Outros: Dispositivos espec├¡ficos')
        baud_layout.addWidget(baud_label)
        baud_layout.addWidget(self.baud_combo)
        settings.addLayout(port_layout)
        settings.addLayout(baud_layout)
        config_layout.addLayout(settings)
        layout.addWidget(config_frame)
        buttons_frame = QFrame()
        buttons_frame.setObjectName('uart_action_bar')
        buttons_frame.setStyleSheet(f'\n            QFrame#uart_action_bar {{\n                background-color: {C['bg_card']};\n                border: 1px solid {C['border_light']};\n                border-radius: 6px;\n                padding: {max(4, p['spacing'] - 2)}px;\n            }}\n        ')
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setSpacing(max(6, p['spacing'] - 2))
        buttons_layout.setContentsMargins(6, 4, 6, 4)
        _action_btn_style = f'\n            QPushButton {{\n                background-color: {C['primary']};\n                color: white;\n                border: none;\n                border-radius: 6px;\n                padding: 8px 14px;\n                font-size: {p['btn_font']}px;\n                font-weight: 600;\n                font-family: "Segoe UI", sans-serif;\n                min-height: {p['btn_min_h']}px;\n                text-align: center;\n            }}\n            QPushButton:hover {{\n                background-color: {C['primary_dark']};\n            }}\n            QPushButton:pressed {{\n                background-color: #0A3A8A;\n            }}\n            QPushButton:disabled {{\n                background-color: #B0BEC5;\n                color: #ECEFF1;\n            }}\n        '
        _icon_size = QSize(max(14, p['btn_font']), max(14, p['btn_font']))
        self.connect_btn = QPushButton(self.translation_manager.get_text('btn_connect'))
        self.connect_btn.setToolTip(self.translation_manager.get_text('tooltip_connect'))
        self.connect_btn.setStyleSheet(_action_btn_style)
        self.connect_btn.setIcon(_uart_svg_icon('terminal.svg'))
        self.connect_btn.setIconSize(_icon_size)
        self.connect_btn.setCursor(Qt.PointingHandCursor)
        self.connect_btn.clicked.connect(self.toggle_connection)
        refresh_btn = QPushButton(self.translation_manager.get_text('btn_refresh_ports'))
        refresh_btn.setToolTip(self.translation_manager.get_text('tooltip_refresh'))
        refresh_btn.setStyleSheet(_action_btn_style)
        refresh_btn.setIcon(_uart_svg_icon('cloud-arrow-down.svg'))
        refresh_btn.setIconSize(_icon_size)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.update_ports)
        detect_btn = QPushButton(self.translation_manager.get_text('btn_auto_detect'))
        detect_btn.setToolTip(self.translation_manager.get_text('tooltip_auto_detect'))
        detect_btn.setStyleSheet(_action_btn_style)
        detect_btn.setIcon(_uart_svg_icon('cpu.svg'))
        detect_btn.setIconSize(_icon_size)
        detect_btn.setCursor(Qt.PointingHandCursor)
        detect_btn.clicked.connect(self.auto_detect_baud)
        test_bauds_btn = QPushButton(self.translation_manager.get_text('btn_test_baudrates'))
        test_bauds_btn.setToolTip(self.translation_manager.get_text('tooltip_test_baudrates'))
        test_bauds_btn.setStyleSheet(_action_btn_style)
        test_bauds_btn.setIcon(_uart_svg_icon('tools.svg'))
        test_bauds_btn.setIconSize(_icon_size)
        test_bauds_btn.setCursor(Qt.PointingHandCursor)
        test_bauds_btn.clicked.connect(self.show_baud_test_assistant)
        for _btn in self.connect_btn, refresh_btn, detect_btn, test_bauds_btn:
            _btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        buttons_layout.addWidget(self.connect_btn)
        buttons_layout.addWidget(refresh_btn)
        buttons_layout.addWidget(detect_btn)
        buttons_layout.addWidget(test_bauds_btn)
        self._stop_detect_btn = QPushButton('Parar')
        self._stop_detect_btn.setStyleSheet(f'\n            QPushButton {{\n                background-color: {C['error']};\n                color: white;\n                border: none;\n                border-radius: 5px;\n                font-weight: 600;\n                min-width: {p['btn_min_w']}px;\n                min-height: {p['btn_min_h']}px;\n                font-size: {p['btn_font']}px;\n            }}\n            QPushButton:hover {{ background-color: #C62828; }}\n        ')
        self._stop_detect_btn.setVisible(False)
        self._stop_detect_btn.clicked.connect(self._stop_detection)
        buttons_layout.addWidget(self._stop_detect_btn)
        layout.addWidget(buttons_frame)
        return frame
    def _setup_health_panel(self):
        '''Painel de saude do hardware ÔÇö mostra subsistemas OK/FALHA em tempo real.'''
        p = self._profile
        C = _UART_COLORS
        frame = QFrame()
        frame.setStyleSheet(f'\n            QFrame {{\n                background-color: {C['bg_card']};\n                border: 1px solid {C['border_light']};\n                border-radius: 6px;\n            }}\n        ')
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)
        title = QLabel('Saude do Hardware')
        title.setStyleSheet(f'\n            font-size: {p['title_font']}px;\n            font-weight: bold;\n            color: {C['primary_dark']};\n            padding: 2px;\n        ')
        layout.addWidget(title)
        grid = QGridLayout()
        grid.setSpacing(2)
        icons = {'PLL': 'CLK', 'PMIC': 'PWR', 'UFS': 'STOR', 'GPIO': 'I/O', 'WDT': 'WDT', 'SPMI': 'BUS', 'RTC': 'RTC', 'Boot': 'BOOT'}
        status_style = f'font-size: {p['small_font']}px; padding: 1px 4px; border-radius: 3px;'
        for i, key in enumerate(self._hw_health):
            row, col = divmod(i, 4)
            tag = QLabel(icons.get(key, key))
            tag.setStyleSheet(f'\n                font-size: {p['small_font']}px;\n                font-weight: bold;\n                color: {C['text_dark']};\n                padding: 1px;\n            ')
            tag.setFixedWidth(32)
            val = QLabel('ÔÇö')
            val.setStyleSheet(status_style + 'color: #999; background-color: #f5f5f5;')
            val.setToolTip(f'{key}: aguardando dados...')
            val.setFixedWidth(32)
            val.setAlignment(Qt.AlignCenter)
            self._hw_labels[key] = val
            grid.addWidget(tag, row, col * 2)
            grid.addWidget(val, row, col * 2 + 1)
        layout.addLayout(grid)
        return frame
    def _get_current_baud_safe(self):
        '''Retorna baud rate atual como int, ou None se indisponivel.'''
        try:
            return int(self.baud_combo.currentText())
        except (ValueError, AttributeError, RuntimeError):
            return
    def _check_hw_health(self, line):
        '''Verifica subsistemas no log e atualiza painel de saude.'''
        updated = False
        if 'LASTPC' in line:
            self._boot_cycle_count += 1
            if self._boot_cycle_count >= 2:
                self._hw_health['Boot'] = {'status': 'ERR', 'detail': f'BOOTLOOP detectado ({self._boot_cycle_count} ciclos)'}
                updated = True
        if self._hw_health['PLL']['status'] == 'ÔÇö':
            if 'Pll init Done' in line or '#T#PLL=' in line:
                self._hw_health['PLL'] = {'status': 'OK', 'detail': 'PLL inicializado'}
                updated = True
        if self._hw_health['PMIC']['status'] != 'ERR':
            if '[PWRAP] Read Test pass' in line or '[PWRAP] Write Test pass' in line:
                self._hw_health['PMIC'] = {'status': 'OK', 'detail': 'PWRAP Read/Write pass'}
                updated = True
            elif '[SPMI] [CALI PASS]' in line and self._hw_health['PMIC']['status'] == 'ÔÇö':
                self._hw_health['PMIC'] = {'status': 'OK', 'detail': 'SPMI calibracao pass'}
                updated = True
            elif 'PWRAP' in line:
                if 'fail' in line.lower() or 'error' in line.lower():
                    self._hw_health['PMIC'] = {'status': 'ERR', 'detail': line.strip()[:60]}
                    updated = True
        if self._hw_health['UFS']['status'] == 'ÔÇö':
            if '[UFS]' in line or 'ufs_aio' in line:
                self._hw_health['UFS'] = {'status': 'PL', 'detail': 'UFS inicializando...'}
                self._last_boot_stage = 'UFS_INIT'
                updated = True
        elif self._hw_health['UFS']['status'] == 'PL':
            if 'LASTPC' in line:
                self._hw_health['UFS'] = {'status': 'ERR', 'detail': 'Crash apos UFS init ÔÇö storage danificado'}
                updated = True
            elif 'ufs_aio_pre_link' in line or 'UFS init done' in line:
                self._hw_health['UFS'] = {'status': 'OK', 'detail': 'UFS link estabelecido'}
                updated = True
            elif '[eMMC]' in line or 'emmc' in line.lower():
                self._hw_health['UFS'] = {'status': 'OK', 'detail': 'eMMC detectado'}
                updated = True
        if self._hw_health['GPIO']['status'] == 'ÔÇö' and '#T#GPIO=' in line:
            self._hw_health['GPIO'] = {'status': 'OK', 'detail': 'GPIO inicializado'}
            updated = True
        if self._hw_health['WDT']['status'] == 'ÔÇö':
            if '#T#WDT' in line:
                self._hw_health['WDT'] = {'status': 'OK', 'detail': 'Watchdog configurado'}
                updated = True
            elif 'ap_watchdog' in line.lower() or 'wdt_status' in line.lower():
                m = re.search('wdt\\s+status\\s+(0x[0-9a-fA-F]+)', line, re.IGNORECASE)
                if m and m.group(1) != '0x0':
                    self._hw_health['WDT'] = {'status': 'ERR', 'detail': f'WDT reset detectado: {m.group(1)}'}
                    updated = True
        if self._hw_health['SPMI']['status'] == 'ÔÇö':
            if '[SPMI] [CALI PASS]' in line:
                self._hw_health['SPMI'] = {'status': 'OK', 'detail': 'SPMI calibracao OK'}
                updated = True
            elif '#T#SPMI=' in line:
                self._hw_health['SPMI'] = {'status': 'OK', 'detail': 'SPMI inicializado'}
                updated = True
            elif '[SPMI]' in line and 'fail' in line.lower():
                self._hw_health['SPMI'] = {'status': 'ERR', 'detail': line.strip()[:60]}
                updated = True
        if 'rtc cbusy time out' in line.lower() or 'rtc timeout' in line.lower():
            self._hw_health['RTC'] = {'status': 'ERR', 'detail': 'RTC timeout ÔÇö cristal/bateria'}
            updated = True
        elif self._hw_health['RTC']['status'] == 'ÔÇö':
            m = re.search('Current RTC time:\\[(\\d{4}/\\d+/\\d+)', line)
            if m:
                year = int(m.group(1).split('/')[0])
                if year < 2020:
                    self._hw_health['RTC'] = {'status': 'ERR', 'detail': f'Data invalida: {m.group(1)}'}
                else:
                    self._hw_health['RTC'] = {'status': 'OK', 'detail': f'RTC: {m.group(1)}'}
                updated = True
        if self._hw_health['Boot']['status'] not in ('OK', 'ERR'):
            if 'welcome to lk' in line.lower():
                self._hw_health['Boot'] = {'status': 'OK', 'detail': 'LK (Little Kernel) alcancado'}
                updated = True
            elif 'initializing kernel' in line.lower():
                self._hw_health['Boot'] = {'status': 'OK', 'detail': 'Kernel inicializando'}
                updated = True
            elif 'll init start' in line and self._hw_health['Boot']['status'] == 'ÔÇö':
                self._hw_health['Boot'] = {'status': 'PL', 'detail': 'Preloader iniciado'}
                updated = True
        if updated:
            QTimer.singleShot(0, self._refresh_health_ui)
    def _refresh_health_ui(self):
        '''Atualiza labels do painel de saude na UI thread.'''
        for key, info in self._hw_health.items():
            lbl = self._hw_labels.get(key)
            if lbl:
                st = info['status']
                if st == 'OK':
                    lbl.setText('OK')
                    lbl.setStyleSheet('font-size: 10px; padding: 1px 4px; border-radius: 3px; font-weight: bold; color: white; background-color: #4caf50;')
                elif st == 'ERR':
                    lbl.setText('ERR')
                    lbl.setStyleSheet('font-size: 10px; padding: 1px 4px; border-radius: 3px; font-weight: bold; color: white; background-color: #f44336;')
                elif st == 'PL':
                    lbl.setText('PL')
                    lbl.setStyleSheet('font-size: 10px; padding: 1px 4px; border-radius: 3px; font-weight: bold; color: white; background-color: #2196f3;')
                else:
                    lbl.setText('ÔÇö')
                    lbl.setStyleSheet('font-size: 10px; padding: 1px 4px; border-radius: 3px; color: #999; background-color: #f5f5f5;')
                lbl.setToolTip(f'{key}: {info['detail']}' if info['detail'] else key)
    def setup_command_frame(self):
        '''Configura o frame de comando'''
        p = self._profile
        C = _UART_COLORS
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(p['spacing'])
        cmd_title = QLabel(self.translation_manager.get_text('send_commands_title'))
        cmd_title.setStyleSheet(f'\n            font-size: {p['title_font']}px;\n            font-weight: bold;\n            color: {C['primary_dark']};\n            padding: 3px;\n        ')
        layout.addWidget(cmd_title)
        cmd_tips = QLabel("Comandos comuns: help, AT, reset, reboot, version, status\nPressione Enter ou clique 'Enviar' para executar")
        cmd_tips.setStyleSheet(f'\n            background-color: #fef9e7;\n            border: 1px solid #f0d78c;\n            border-left: 3px solid {C['warning']};\n            border-radius: 4px;\n            padding: 6px 8px;\n            font-size: {p['small_font']}px;\n            color: #7d5a00;\n        ')
        cmd_tips.setWordWrap(True)
        layout.addWidget(cmd_tips)
        input_layout = QHBoxLayout()
        self.cmd_input = QComboBox()
        self.cmd_input.setEditable(True)
        self.cmd_input.setPlaceholderText('Digite um comando...')
        self.cmd_input.setToolTip('Digite um comando ou selecione do hist├│rico')
        common_commands = ['help', 'AT', 'version', 'status', 'reset', 'reboot', '?', 'info', 'debug', 'bootmode']
        self.cmd_input.addItems(common_commands)
        self.cmd_input.setCurrentText('')
        self.cmd_input.lineEdit().returnPressed.connect(self.send_command)
        input_layout.addWidget(self.cmd_input)
        send_btn = QPushButton(self.translation_manager.get_text('btn_send'))
        send_btn.setToolTip(self.translation_manager.get_text('tooltip_send_command'))
        send_btn.clicked.connect(self.send_command)
        input_layout.addWidget(send_btn)
        clear_history_btn = QPushButton('Limpar')
        clear_history_btn.setFixedSize(70, 32)
        clear_history_btn.setToolTip('Limpar historico de comandos')
        clear_history_btn.clicked.connect(self.clear_command_history)
        input_layout.addWidget(clear_history_btn)
        layout.addLayout(input_layout)
        return frame
    def clear_command_history(self):
        '''Limpa o hist├│rico de comandos'''
        reply = QMessageBox.question(self, 'Limpar Historico', 'Deseja limpar o historico de comandos?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            current_text = self.cmd_input.currentText()
            self.cmd_input.clear()
            common_commands = ['help', 'AT', 'version', 'status', 'reset', 'reboot', '?', 'info', 'debug', 'bootmode']
            self.cmd_input.addItems(common_commands)
            self.cmd_input.setCurrentText(current_text)
            self.signal_log.emit('Historico de comandos limpo.', 'success')
    def setup_stats_frame(self):
        '''Configura o frame de estatisticas ÔÇö tema UNION BLUE, compacto.'''
        p = self._profile
        C = _UART_COLORS
        frame = QFrame()
        frame.setObjectName('uart_stats_panel')
        frame.setStyleSheet(f'\n            QFrame#uart_stats_panel {{\n                background-color: {C['bg_card']};\n                border: 1px solid {C['border_light']};\n                border-radius: 6px;\n            }}\n        ')
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)
        header = QHBoxLayout()
        title = QLabel('Monitor')
        title.setStyleSheet(f'\n            font-size: {p['body_font']}px; font-weight: bold;\n            color: {C['primary_dark']}; border: none; background: transparent;\n        ')
        header.addWidget(title)
        header.addStretch()
        self.status_label = QLabel('Desconectado')
        self.status_label.setStyleSheet(f'\n            color: {C['error']}; font-weight: 600;\n            font-size: {p['small_font']}px;\n            border: none; background: transparent;\n        ')
        header.addWidget(self.status_label)
        layout.addLayout(header)
        rx_tx_row = QHBoxLayout()
        rx_tx_row.setSpacing(8)
        self.rx_label = QLabel('RX: 0 B')
        self.rx_label.setStyleSheet(f'\n            font-weight: 600; font-size: {p['small_font']}px;\n            color: #27ae60; border: none; background: transparent;\n        ')
        rx_tx_row.addWidget(self.rx_label)
        self.tx_label = QLabel('TX: 0 B')
        self.tx_label.setStyleSheet(f'\n            font-weight: 600; font-size: {p['small_font']}px;\n            color: {C['primary']}; border: none; background: transparent;\n        ')
        rx_tx_row.addWidget(self.tx_label)
        rx_tx_row.addStretch()
        layout.addLayout(rx_tx_row)
        clear_btn = QPushButton('Limpar Logs')
        clear_btn.setStyleSheet(f'\n            QPushButton {{\n                background-color: #e8eef5;\n                color: {C['text_dark']};\n                padding: 5px;\n                font-size: {p['small_font']}px;\n                border: 1px solid {C['border']};\n                border-radius: 4px;\n                font-weight: 600;\n                margin-top: 4px;\n            }}\n            QPushButton:hover {{\n                background-color: #ffcdd2;\n                border-color: {C['error']};\n                color: {C['error']};\n            }}\n            QPushButton:pressed {{\n                background-color: {C['error']};\n                color: white;\n            }}\n        ')
        clear_btn.clicked.connect(self.clear_all_logs)
        layout.addWidget(clear_btn)
        return frame
    def clear_all_logs(self):
        '''Limpa todos os logs e contadores'''
        reply = QMessageBox.question(self, 'Limpar Logs', 'Todos os logs e contadores serao resetados.\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.log_text.clear()
            self.rx_count = 0
            self.tx_count = 0
            self.rx_label.setText('RX: 0.0 B')
            self.tx_label.setText('TX: 0.0 B')
            for category in self.message_counts:
                for name in self.message_counts[category]:
                    self.message_counts[category][name] = 0
                    self.update_filter_count(category, name, 0)
            for key in self._hw_health:
                self._hw_health[key] = {'status': 'ÔÇö', 'detail': ''}
            self._boot_cycle_count = 0
            self._last_boot_stage = ''
            if _HAS_NEW_PARSER:
                self._parsed_state = create_empty_state()
                try:
                    self._health_widget.clear()
                except Exception:
                    pass
            else:
                self._refresh_health_ui()
            self.signal_log.emit('Logs limpos.', 'info')
    def uncheck_all_filters(self):
        '''Desmarca todos os filtros para mostrar tudo'''
        for category in self.message_checks:
            for name in self.message_checks[category]:
                self.message_checks[category][name].setChecked(False)
    def show_errors_only(self):
        '''Mostra apenas falhas e avisos'''
        self.uncheck_all_filters()
        for cat in ('Falhas', 'Avisos'):
            if cat in self.message_checks:
                for name in self.message_checks[cat]:
                    self.message_checks[cat][name].setChecked(True)
    def show_hardware_only(self):
        '''Mostra inicializacao e diagnostico de hardware'''
        self.uncheck_all_filters()
        for cat in ('Inicializacao', 'Diagnostico'):
            if cat in self.message_checks:
                for name in self.message_checks[cat]:
                    self.message_checks[cat][name].setChecked(True)
    def reprocess_existing_logs(self):
        '''Reprocessa logs existentes com filtros atuais'''
        log_content = self.log_text.toPlainText()
        if not log_content.strip():
            QMessageBox.information(self, 'Ôä╣´©Å Sem dados', 'N├úo h├í logs para reprocessar.\nConecte primeiro e capture alguns dados.')
            return
        reply = QMessageBox.question(self, 'Reprocessar Logs', 'Isso ir├í reprocessar todos os logs existentes com os filtros atuais.\n\nImportante:\nÔÇó O log ser├í limpo e reprocessado\nÔÇó Apenas linhas que fazem match com filtros ativos aparecer├úo\nÔÇó Se nenhum filtro estiver ativo, todas as linhas aparecer├úo\n\nContinuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.No:
            return
        original_lines = []
        for line in log_content.split('\n'):
            if not line.strip():
                continue
            if '] ' in line:
                parts = line.split('] ', 1)
                if len(parts) > 1:
                    msg = parts[1]
                    if '] ' in msg:
                        category_parts = msg.split('] ', 1)
                        if len(category_parts) > 1:
                            original_lines.append(category_parts[1])
                        else:
                            original_lines.append(msg)
                    else:
                        original_lines.append(msg)
                else:
                    original_lines.append(line)
            else:
                original_lines.append(line)
        if not original_lines:
            QMessageBox.warning(self, 'Erro', 'N├úo foi poss├¡vel extrair mensagens dos logs existentes.')
            return
        self.log_text.clear()
        for category in self.message_counts:
            for name in self.message_counts[category]:
                self.message_counts[category][name] = 0
                self.update_filter_count(category, name, 0)
        if _HAS_NEW_PARSER:
            self._parsed_state = create_empty_state()
            try:
                self._health_widget.clear()
            except Exception:
                pass
        self.signal_log.emit('Reprocessando logs existentes...', 'info')
        self.signal_log.emit('Encontradas %d mensagens para reprocessar' % len(original_lines), 'info')
        processed_count = 0
        matched_count = 0
        for i, line in enumerate(original_lines):
            if line.strip():
                matched = self.reprocess_single_line(line.strip())
                if matched:
                    matched_count += 1
                processed_count += 1
        self.signal_log.emit(f'Reprocessamento concluido. {matched_count}/{processed_count} mensagens correspondem aos filtros ativos.', 'success')
        if matched_count == 0:
            if self.has_active_filters():
                self.signal_log.emit("Dica: Nenhuma mensagem corresponde aos filtros ativos. Tente desmarcar filtros ou usar 'Ver Tudo' para ver todas as mensagens.", 'info')
    def reprocess_single_line(self, line):
        '''Processa uma ├║nica linha durante o reprocessamento'''
        matched = False
        if _HAS_NEW_PARSER:
            try:
                _baud = self._get_current_baud_safe()
                if update_health_state_auto(self._parsed_state, line, baud_rate=_baud):
                    self._health_widget.update_from_state(self._parsed_state)
            except Exception:
                pass
        active_filters = self.has_active_filters()
        if not active_filters:
            msg = f'[REPROCESSADO] {line}'
            self.signal_log.emit(msg, 'normal')
            return True
        for category, patterns in self.message_patterns.items():
            for name, pattern_info in patterns.items():
                if not self.message_checks[category][name].isChecked():
                    continue
                if not re.search(pattern_info['pattern'], line, re.IGNORECASE):
                    continue
                matched = True
                self.message_counts[category][name] += 1
                count = self.message_counts[category][name]
                self.signal_filter_count.emit(category, name, count)
                msg = f'[REPROCESSADO] [{category}] {name}: {line}'
                msg_type = pattern_info.get('type', 'info')
                self.signal_log.emit(msg, msg_type)
                return True
        if not matched:
            if active_filters:
                msg = f'[REPROCESSADO] {line}'
                self.signal_log.emit(msg, 'normal')
                return True
        return False
    def has_active_filters(self):
        '''Verifica se h├í filtros ativos'''
        for category in self.message_checks:
            if any((check.isChecked() for check in self.message_checks[category].values())):
                return True
        return False
