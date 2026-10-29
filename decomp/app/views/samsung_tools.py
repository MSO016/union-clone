'''
Interface de ferramentas Samsung
Desenvolvido seguindo as diretrizes RESTORECELL
Esta view segue os padr├Áes visuais e estruturais das outras abas do sistema UNION.
'''
import logging
import subprocess
import threading
import time
import serial.tools.list_ports
import traceback
import sys
import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QGroupBox, QComboBox, QMessageBox, QProgressDialog, QGridLayout, QSizePolicy, QFrame, QScrollArea, QTabWidget, QApplication)
from PyQt5.QtCore import (Qt, QTimer, pyqtSignal, QThread)
from PyQt5.QtGui import (QFont, QTextCursor, QIcon)
from app.utils.path_manager import PathManager
from app.utils.samsung_manager import SamsungManager
from app.utils.samsung_advanced import SamsungAdvancedTools
from app.utils.samsung_qrcode_viewer import show_qrcode_viewer
from app.views.union_unlock.flash.samsung.samsung_flash_gui import SamsungFlashToolWidget
logger = logging.getLogger(__name__)
DEBUG_SAMSUNG = False
def debug_log(msg):
    '''Log de debug detalhado'''
    if DEBUG_SAMSUNG:
        print(f'[SAMSUNG DEBUG] {msg}')
        logger.debug(f'[SAMSUNG DEBUG] {msg}')
class CommandThread(QThread):
    '''Thread para executar comandos de forma ass├¡ncrona'''
    command_finished = pyqtSignal(str)
    command_started = pyqtSignal()
    command_error = pyqtSignal(str)
    progress_update = pyqtSignal(str)
    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self._is_running = True
    def run(self):
        try:
            self.command_started.emit()
            result = self.function(*self.args, **self.kwargs)
            if self._is_running:
                self.command_finished.emit(str(result))
                return
        except Exception as e:
            if self._is_running:
                logger.error(f'Erro no comando: {str(e)}')
                self.command_error.emit(str(e))
    def stop(self):
        self._is_running = False
class SamsungTools(QWidget):
    '''Interface principal das ferramentas Samsung'''
    _log_lines_request = pyqtSignal(list)
    _progress_value_request = pyqtSignal(int)
    _progress_label_request = pyqtSignal(str)
    _progress_close_request = pyqtSignal()
    def __init__(self, parent=None, adb_manager=None):
        debug_log('SamsungTools.__init__ - In├¡cio')
        try:
            super().__init__(parent)
            debug_log('SamsungTools.__init__ - super().__init__ OK')
            self.parent = parent
            self.adb_manager = adb_manager
            debug_log('SamsungTools.__init__ - adb_manager atribu├¡do')
            self.samsung_manager = SamsungManager(adb_manager)
            debug_log('SamsungTools.__init__ - SamsungManager criado')
            self.samsung_advanced = SamsungAdvancedTools(self.samsung_manager, self.adb_manager)
            debug_log('SamsungTools.__init__ - SamsungAdvancedTools criado')
            self.command_thread = None
            self._is_updating_ports = False
            debug_log('SamsungTools.__init__ - Vari├íveis inicializadas')
            self._log_lines_request.connect(self._exibir_linhas_no_log_ativo)
            debug_log('SamsungTools.__init__ - _log_lines_request conectado')
            self._current_progress_dialog = None
            self._progress_value_request.connect(self._on_progress_value_request)
            self._progress_label_request.connect(self._on_progress_label_request)
            self._progress_close_request.connect(self._on_progress_close_request)
            debug_log('SamsungTools.__init__ - slots de progress conectados')
            self.setup_ui()
            debug_log('SamsungTools.__init__ - setup_ui() conclu├¡do')
            return
        except Exception as e:
            debug_log(f'SamsungTools.__init__ - ERRO: {str(e)}')
            debug_log(f'SamsungTools.__init__ - Traceback: {traceback.format_exc()}')
            raise
    def setup_ui(self):
        '''Configura a interface do usu├írio'''
        debug_log('setup_ui - In├¡cio')
        try:
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(5, 5, 5, 5)
            main_layout.setSpacing(5)
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            debug_log('setup_ui - Layout principal criado')
            self.tab_widget = QTabWidget()
            self.tab_widget.setStyleSheet('\n                QTabWidget::pane {\n                    border: 1px solid #cccccc;\n                    background: white;\n                    padding: 2px;\n                }\n                QTabWidget::tab-bar {\n                    alignment: left;\n                }\n                QTabBar::tab {\n                    background: #555555;\n                    border: 2px solid #333333;\n                    padding: 6px 12px;\n                    margin-right: 2px;\n                    border-top-left-radius: 4px;\n                    border-top-right-radius: 4px;\n                    font-weight: bold;\n                    min-width: 80px;\n                    font-size: 12px;\n                    color: white;\n                }\n                QTabBar::tab:selected {\n                    background: #1976D2;\n                    border-color: #1976D2;\n                    color: white;\n                }\n                QTabBar::tab:hover {\n                    background: #666666;\n                }\n            ')
            standard_tab = QWidget()
            self.setup_standard_tab(standard_tab)
            self.tab_widget.addTab(standard_tab, 'Padrao')
            advanced_tab = QWidget()
            self.setup_advanced_tab(advanced_tab)
            self.tab_widget.addTab(advanced_tab, 'Advanced')
            self.flash_tab = SamsungFlashToolWidget()
            self.tab_widget.addTab(self.flash_tab, 'Flash')
            main_layout.addWidget(self.tab_widget)
            self.apply_styles()
            debug_log('setup_ui - Estilos aplicados')
            debug_log('setup_ui - Agendando setup_connections em 500ms')
            QTimer.singleShot(500, self.setup_connections)
            debug_log('setup_ui - Conclu├¡do com sucesso (log removido para otimiza├º├úo)')
            return
        except Exception as e:
            debug_log(f'setup_ui - ERRO: {str(e)}')
            debug_log(f'setup_ui - Traceback: {traceback.format_exc()}')
            raise
    def setup_standard_tab(self, tab_widget):
        '''Configura a aba padr├úo com funcionalidades atuais (padr├úo das outras abas)'''
        main_layout = QVBoxLayout(tab_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        content_layout = QHBoxLayout()
        left_scroll_area = QScrollArea()
        left_scroll_area.setWidgetResizable(True)
        left_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        left_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_scroll_area.setStyleSheet('\n            QScrollArea {\n                border: none;\n                background-color: transparent;\n            }\n            QScrollBar:vertical {\n                background-color: #ecf0f1;\n                width: 12px;\n                border-radius: 6px;\n                margin: 0px;\n            }\n            QScrollBar::handle:vertical {\n                background-color: #95a5a6;\n                border-radius: 6px;\n                min-height: 20px;\n            }\n            QScrollBar::handle:vertical:hover {\n                background-color: #7f8c8d;\n            }\n            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {\n                border: none;\n                background: none;\n            }\n        ')
        left_panel = QFrame()
        left_panel.setStyleSheet('\n            QFrame {\n                background-color: #f8f9fa;\n                border-radius: 8px;\n                border: 1px solid #dee2e6;\n            }\n        ')
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(10)
        serial_group = self.create_serial_group()
        left_layout.addWidget(serial_group)
        info_group = self.create_info_group()
        left_layout.addWidget(info_group)
        tools_group = self.create_tools_group()
        left_layout.addWidget(tools_group)
        left_layout.addStretch()
        left_scroll_area.setWidget(left_panel)
        content_layout.addWidget(left_scroll_area)
        right_panel = QFrame()
        right_panel.setStyleSheet('\n            QFrame {\n                background-color: #f8f9fa;\n                border-radius: 8px;\n                border: 1px solid #dee2e6;\n            }\n        ')
        right_layout = QVBoxLayout(right_panel)
        terminal_title = QLabel('Terminal Samsung')
        terminal_title.setStyleSheet('\n            font-weight: bold;\n            font-size: 13px;\n            color: #495057;\n            padding: 5px;\n            background-color: #e9ecef;\n            border-radius: 4px;\n        ')
        right_layout.addWidget(terminal_title)
        self.standard_log = QTextEdit()
        self.standard_log.setReadOnly(True)
        self.standard_log.setStyleSheet("\n            QTextEdit {\n                font-family: 'Consolas', 'Courier New', monospace;\n                font-size: 13px;\n                background-color: #2b2b2b;\n                color: #a9b7c6;\n                border: 1px solid #495057;\n                border-radius: 4px;\n                padding: 6px;\n            }\n        ")
        right_layout.addWidget(self.standard_log)
        self._show_welcome_message()
        clear_standard_btn = QPushButton('Limpar Terminal')
        clear_standard_btn.setStyleSheet('\n            QPushButton {\n                background-color: #424242;\n                color: white;\n                border: none;\n                border-radius: 4px;\n                padding: 6px 12px;\n                font-weight: bold;\n                font-size: 10px;\n            }\n            QPushButton:hover {\n                background-color: #616161;\n            }\n        ')
        clear_standard_btn.clicked.connect(self.clear_standard_log)
        clear_standard_btn.setMaximumWidth(120)
        right_layout.addWidget(clear_standard_btn, alignment=Qt.AlignRight)
        content_layout.addWidget(right_panel)
        main_layout.addLayout(content_layout)
    def setup_advanced_tab(self, tab_widget):
        '''Configura a aba Advanced com funcionalidades avan├ºadas'''
        main_layout = QVBoxLayout(tab_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        warning_frame = QFrame()
        warning_frame.setStyleSheet('\n            QFrame {\n                background-color: #fff3cd;\n                border: 2px solid #ffc107;\n                border-radius: 8px;\n                padding: 10px;\n            }\n        ')
        warning_layout = QVBoxLayout(warning_frame)
        warning_title = QLabel('FUNCIONALIDADES AVANCADAS SAMSUNG')
        warning_title.setStyleSheet('\n            font-weight: bold;\n            font-size: 14px;\n            color: #856404;\n            margin-bottom: 5px;\n        ')
        warning_layout.addWidget(warning_title)
        warning_text = QLabel('\n        ATENCAO - Leia antes de usar:\n        - Nao nos responsabilizamos por brick ou danos - Use com conhecimento previo\n        - Desbloqueios: APENAS em dispositivos proprios ou com comprovacao de propriedade\n        - Processador e Patch de Seguranca sao CRITICOS - Verifique sempre antes de executar\n        - Variantes de modelo: Foque no chipset, nao apenas no nome do modelo\n        - Drivers e ADB atualizados sao essenciais para evitar falhas\n        - Ferramentas testadas e validadas - Novos modelos adicionados constantemente\n        ')
        warning_text.setStyleSheet('\n            color: #856404;\n            font-size: 12px;\n            line-height: 1.4;\n        ')
        warning_layout.addWidget(warning_text)
        main_layout.addWidget(warning_frame)
        content_layout = QHBoxLayout()
        left_scroll_area = QScrollArea()
        left_scroll_area.setWidgetResizable(True)
        left_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        left_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_scroll_area.setStyleSheet('\n            QScrollArea {\n                border: none;\n                background-color: transparent;\n            }\n            QScrollBar:vertical {\n                background-color: #ecf0f1;\n                width: 12px;\n                border-radius: 6px;\n                margin: 0px;\n            }\n            QScrollBar::handle:vertical {\n                background-color: #95a5a6;\n                border-radius: 6px;\n                min-height: 20px;\n            }\n            QScrollBar::handle:vertical:hover {\n                background-color: #7f8c8d;\n            }\n            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {\n                border: none;\n                background: none;\n            }\n        ')
        left_panel = QFrame()
        left_panel.setStyleSheet('\n            QFrame {\n                background-color: #f8f9fa;\n                border-radius: 8px;\n                border: 1px solid #dee2e6;\n            }\n        ')
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(10)
        conn_group = QGroupBox('Conexao Samsung Advanced')
        conn_group.setStyleSheet('\n            QGroupBox {\n                font-weight: bold;\n                font-size: 12px;\n                color: #495057;\n                border: 2px solid #007bff;\n                border-radius: 8px;\n                margin-top: 10px;\n                padding-top: 10px;\n            }\n            QGroupBox::title {\n                subcontrol-origin: margin;\n                left: 10px;\n                padding: 0 5px 0 5px;\n                background-color: #f8f9fa;\n            }\n        ')
        conn_layout = QVBoxLayout(conn_group)
        self.advanced_status = QLabel('Aguardando conexao Samsung...')
        self.advanced_status.setStyleSheet('\n            font-weight: bold;\n            font-size: 11px;\n            color: #dc3545;\n            padding: 5px;\n            background-color: #f8d7da;\n            border-radius: 4px;\n            border: 1px solid #f5c6cb;\n        ')
        conn_layout.addWidget(self.advanced_status)
        self.advanced_connect_btn = QPushButton('Detectar e Conectar Samsung')
        self.advanced_connect_btn.setStyleSheet('\n            QPushButton {\n                background-color: #28a745;\n                color: white;\n                border: none;\n                padding: 8px 16px;\n                border-radius: 6px;\n                font-weight: bold;\n                font-size: 11px;\n            }\n            QPushButton:hover {\n                background-color: #218838;\n            }\n            QPushButton:pressed {\n                background-color: #1e7e34;\n            }\n        ')
        self.advanced_connect_btn.clicked.connect(self.advanced_detect_and_connect)
        conn_layout.addWidget(self.advanced_connect_btn)
        left_layout.addWidget(conn_group)
        functions_group = QGroupBox('Funcoes Avancadas')
        functions_group.setStyleSheet('\n            QGroupBox {\n                font-weight: bold;\n                font-size: 12px;\n                color: #495057;\n                border: 2px solid #6c757d;\n                border-radius: 8px;\n                margin-top: 10px;\n                padding-top: 10px;\n            }\n            QGroupBox::title {\n                subcontrol-origin: margin;\n                left: 10px;\n                padding: 0 5px 0 5px;\n                background-color: #f8f9fa;\n            }\n        ')
        functions_layout = QGridLayout(functions_group)
        functions_layout.setSpacing(6)
        _adv_row = 0
        _adv_col = 0
        advanced_buttons = [('Info Download', self.execute_dvif_info, 'Informacoes detalhadas do dispositivo Samsung', True), ('FRP Android 9-10', self.execute_frp_android_9_10, 'FRP Bypass para Samsung Android 9-10 Exynos', False), ('FRP ADB', self.execute_frp_adb_only, 'FRP Bypass apenas com comandos ADB (dispositivo autorizado)', True), ('FRP ADB Debug', self.execute_frp_adb_debug, 'FRP via adb root + push (APENAS ROM eng/userdebug)', True), ('FRP ADB Debug (UNION)', self.execute_frp_recovery_union, 'FRP via metodo UNION - forca autorizacao + limpeza automatica', True), ('QR Code Generator [8-16]', self.show_qrcode_viewer, 'Visualiza QR Codes para desbloqueio Samsung', True), ('FRP Android 11+', self.execute_frp_android_11_plus, 'FRP para Android 11+ (metodo validado) - Samsung Exynos', False), ('FRP Android 16', self.execute_frp_android_16, 'FRP Android 16 (Patch Nov 2024) - Dispositivo LIGADO na tela FRP', True), ('FRP MODELS', self.show_frp_samsung_models, 'FRP por modelo especifico - Samsung EDL/BROM/MTP', True), ('premium:ID:2', self.execute_frp_work_id_android_14, 'Servico Premium - FRP por ID/IMEI ate Android 14', True), ('Analise Avancada', self.perform_advanced_analysis, 'Analise completa do dispositivo Samsung', False)]
        self.advanced_function_buttons = []
        _adv_icons = {'Info Download': 'card-checklist.svg', 'FRP Android 9-10': 'shield-lock.svg', 'FRP ADB': 'terminal.svg', 'FRP ADB Debug': 'terminal.svg', 'FRP ADB Debug (UNION)': 'shield-fill-check.svg', 'QR Code Generator [8-16]': 'upc-scan.svg', 'FRP Android 11+': 'shield-lock.svg', 'FRP Android 16': 'shield-lock.svg', 'FRP MODELS': 'phone-flip.svg', 'Analise Avancada': 'clipboard2-pulse.svg'}
        adv_icons_dir = PathManager.get_resource_path('icons_svg')
        from app.utils.premium_services_manager import get_premium_services_manager
        premium_manager = get_premium_services_manager()
        for text, callback, tooltip, always_enabled in advanced_buttons:
            is_premium_button = text.startswith('premium:')
            if is_premium_button:
                servico_identificador = text.replace('premium:', '')
                btn = premium_manager.criar_botao_premium_com_indicador(servico_identificador, callback, parent=self)
                btn.setToolTip(tooltip)
                if not hasattr(self, 'premium_buttons'):
                    self.premium_buttons = []
                self.premium_buttons.append((btn, servico_identificador))
            else:
                btn = QPushButton(text)
                btn.setToolTip(tooltip)
                btn.clicked.connect(callback)
                svg_file = _adv_icons.get(text)
                if svg_file and adv_icons_dir:
                    import os
                    icon_path = os.path.join(adv_icons_dir, svg_file)
                    if os.path.isfile(icon_path):
                        btn.setIcon(QIcon(icon_path))
                if not always_enabled:
                    btn.setEnabled(False)
                    self.advanced_function_buttons.append(btn)
            if not is_premium_button:
                if 'FRP Android 11+' in text:
                    btn.setStyleSheet('\n                        QPushButton {\n                            background-color: #e74c3c;\n                            color: white;\n                            font-weight: bold;\n                            padding: 8px 16px;\n                            border-radius: 6px;\n                            border: 2px solid #c0392b;\n                            font-size: 12px;\n                        }\n                        QPushButton:hover {\n                            background-color: #c0392b;\n                            border-color: #a93226;\n                        }\n                        QPushButton:pressed {\n                            background-color: #a93226;\n                            border-color: #922b21;\n                        }\n                    ')
                elif 'FRP Android 16' in text:
                    btn.setStyleSheet('\n                        QPushButton {\n                            background-color: #9b59b6;\n                            color: white;\n                            font-weight: bold;\n                            padding: 8px 16px;\n                            border-radius: 6px;\n                            border: 2px solid #8e44ad;\n                            font-size: 12px;\n                        }\n                        QPushButton:hover {\n                            background-color: #8e44ad;\n                            border-color: #7d3c98;\n                        }\n                        QPushButton:pressed {\n                            background-color: #7d3c98;\n                            border-color: #6c3483;\n                        }\n                    ')
                else:
                    btn.setStyleSheet('\n                        QPushButton {\n                            background-color: #007bff;\n                            color: white;\n                            font-weight: bold;\n                            padding: 8px 16px;\n                            border-radius: 6px;\n                            border: none;\n                            font-size: 12px;\n                        }\n                        QPushButton:hover {\n                            background-color: #0056b3;\n                        }\n                        QPushButton:pressed {\n                            background-color: #004085;\n                        }\n                    ')
            functions_layout.addWidget(btn, _adv_row, _adv_col)
            _adv_col += 1
            if not _adv_col >= 3:
                continue
            _adv_col = 0
            _adv_row += 1
            continue
        left_layout.addWidget(functions_group)
        left_layout.addStretch()
        left_scroll_area.setWidget(left_panel)
        content_layout.addWidget(left_scroll_area)
        right_panel = QFrame()
        right_panel.setStyleSheet('\n            QFrame {\n                background-color: #f8f9fa;\n                border-radius: 8px;\n                border: 1px solid #dee2e6;\n            }\n        ')
        right_layout = QVBoxLayout(right_panel)
        log_title = QLabel('Log de Funcoes Avancadas')
        log_title.setStyleSheet('\n            font-weight: bold;\n            font-size: 13px;\n            color: #495057;\n            padding: 5px;\n            background-color: #e9ecef;\n            border-radius: 4px;\n        ')
        right_layout.addWidget(log_title)
        self.advanced_log = QTextEdit()
        self.advanced_log.setReadOnly(True)
        self.advanced_log.setStyleSheet("\n            QTextEdit {\n                font-family: 'Consolas', 'Courier New', monospace;\n                font-size: 13px;\n                background-color: #2b2b2b;\n                color: #a9b7c6;\n                border: 1px solid #495057;\n                border-radius: 4px;\n                padding: 6px;\n            }\n        ")
        self.advanced_log_message('­ƒÜÇ Log de fun├º├Áes avan├ºadas Samsung iniciado...')
        self.advanced_log_message('ÔÜá´©Å Use estas funcionalidades com responsabilidade!')
        right_layout.addWidget(self.advanced_log)
        clear_advanced_btn = QPushButton('Limpar Terminal')
        clear_advanced_btn.setStyleSheet('\n            QPushButton {\n                background-color: #424242;\n                color: white;\n                border: none;\n                border-radius: 4px;\n                padding: 6px 12px;\n                font-weight: bold;\n                font-size: 10px;\n            }\n            QPushButton:hover {\n                background-color: #616161;\n            }\n        ')
        clear_advanced_btn.clicked.connect(self.clear_advanced_log)
        clear_advanced_btn.setMaximumWidth(120)
        right_layout.addWidget(clear_advanced_btn, alignment=Qt.AlignRight)
        content_layout.addWidget(right_panel)
        main_layout.addLayout(content_layout)
    def create_serial_group(self):
        '''Cria grupo de conex├úo serial'''
        debug_log('create_serial_group - In├¡cio')
        try:
            group = QGroupBox('Conexao Serial')
            layout = QVBoxLayout()
            port_layout = QHBoxLayout()
            port_label = QLabel('Porta:')
            debug_log('create_serial_group - Criando QComboBox...')
            self.port_combo = QComboBox()
            self.port_combo.setMinimumWidth(200)
            debug_log('create_serial_group - QComboBox criado')
            self.refresh_ports_btn = QPushButton('Atualizar')
            self.refresh_ports_btn.clicked.connect(self.update_port_list)
            _serial_icons_dir = PathManager.get_resource_path('icons_svg')
            if _serial_icons_dir:
                import os
                _refresh_icon = os.path.join(_serial_icons_dir, 'arrow-clockwise.svg')
                if os.path.isfile(_refresh_icon):
                    self.refresh_ports_btn.setIcon(QIcon(_refresh_icon))
            debug_log('create_serial_group - Bot├úo refresh criado')
            self.connect_btn = QPushButton('Forcar')
            self.connect_btn.setToolTip('Forca conexao manual na porta selecionada (fallback)')
            self.connect_btn.clicked.connect(self.toggle_connection)
            if _serial_icons_dir:
                _conn_icon = os.path.join(_serial_icons_dir, 'broadcast-pin.svg')
                if os.path.isfile(_conn_icon):
                    self.connect_btn.setIcon(QIcon(_conn_icon))
            debug_log('create_serial_group - Bot├úo conectar criado')
            port_layout.addWidget(port_label)
            port_layout.addWidget(self.port_combo)
            port_layout.addWidget(self.refresh_ports_btn)
            port_layout.addWidget(self.connect_btn)
            port_layout.addStretch()
            layout.addLayout(port_layout)
            self.connection_status = QLabel('Desconectado')
            self.connection_status.setVisible(False)
            group.setLayout(layout)
            debug_log('create_serial_group - Conclu├¡do com sucesso')
            return group
        except Exception as e:
            debug_log(f'create_serial_group - ERRO: {str(e)}')
            debug_log(f'create_serial_group - Traceback: {traceback.format_exc()}')
            raise
    def create_info_group(self):
        '''Cria grupo de informa├º├Áes do dispositivo'''
        group = QGroupBox('Informacoes do Dispositivo')
        layout = QVBoxLayout()
        self.get_info_btn = QPushButton('Obter Informacoes')
        self.get_info_btn.clicked.connect(self.get_device_info)
        self.get_info_btn.setEnabled(True)
        _info_icons_dir = PathManager.get_resource_path('icons_svg')
        if _info_icons_dir:
            import os
            _info_icon = os.path.join(_info_icons_dir, 'card-checklist.svg')
            if os.path.isfile(_info_icon):
                self.get_info_btn.setIcon(QIcon(_info_icon))
        layout.addWidget(self.get_info_btn)
        group.setLayout(layout)
        return group
    def create_tools_group(self):
        '''Cria grupo de ferramentas Samsung'''
        group = QGroupBox('Ferramentas Samsung')
        layout = QGridLayout()
        layout.setSpacing(10)
        frp_info = QLabel("Para funcionalidades FRP, acesse a aba 'Advanced'")
        frp_info.setStyleSheet('\n            QLabel {\n                color: #0969da;\n                font-weight: bold;\n                padding: 8px;\n                background-color: #dbeafe;\n                border: 1px solid #60a5fa;\n                border-radius: 4px;\n                margin-bottom: 10px;\n            }\n        ')
        layout.addWidget(frp_info, 0, 0, 1, 3)
        tools = [('Factory Reset', self.factory_reset_device, 'Apaga TODOS os dados do dispositivo - IRREVERSIVEL!', False), ('Reiniciar Dispositivo', self.reboot_device, 'Reinicializacao forcada do dispositivo', False), ('Modo Download', self.reboot_download, 'Reinicia em modo Download', False), ('Verificar IMEI', self.check_imei, 'Verifica o IMEI do dispositivo', False), ('Turbo Clean', self.remove_bloatware, 'Otimizacao ADB - remove apps pre-instalados para liberar espaco. Requer USB Debugging ativo.', True), ('Testar Comunicacao', self.show_development_message, 'Funcao em desenvolvimento - Testa comunicacao com o dispositivo', False)]
        _btn_icons = {'Factory Reset': 'shield-lock.svg', 'Reiniciar Dispositivo': 'arrow-clockwise.svg', 'Modo Download': 'cloud-arrow-down.svg', 'Verificar IMEI': 'upc-scan.svg', 'Turbo Clean': 'virus2.svg', 'Testar Comunicacao': 'broadcast-pin.svg'}
        icons_dir = PathManager.get_resource_path('icons_svg')
        row = 1
        col = 0
        for text, callback, tooltip, adb_only in tools:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            btn.setToolTip(tooltip)
            btn.setEnabled(True)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setMinimumHeight(50)
            svg_file = _btn_icons.get(text)
            if svg_file and icons_dir:
                import os
                icon_path = os.path.join(icons_dir, svg_file)
                if os.path.isfile(icon_path):
                    btn.setIcon(QIcon(icon_path))
            btn.callback = callback
            btn.adb_only = bool(adb_only)
            layout.addWidget(btn, row, col)
            col += 1
            if not col >= 3:
                continue
            col = 0
            row += 1
            continue
        group.setLayout(layout)
        self.tools_group = group
        return group
    def apply_styles(self):
        '''Aplica estilos consistentes com o sistema'''
        self.setStyleSheet('\n            QGroupBox {\n                font-size: 12px;\n                font-weight: bold;\n                padding: 8px;\n                margin-top: 3px;\n                border: 1px solid #E0E0E0;\n                border-radius: 3px;\n                background-color: #FFFFFF;\n            }\n            QGroupBox::title {\n                subcontrol-origin: margin;\n                left: 7px;\n                padding: 0 3px;\n                color: #1976D2;\n            }\n            QPushButton {\n                padding: 8px;\n                font-size: 12px;\n                background-color: #2196F3;\n                color: white;\n                border-radius: 4px;\n                font-weight: bold;\n                border: none;\n            }\n            QPushButton:hover {\n                background-color: #1976D2;\n            }\n            QPushButton:pressed {\n                background-color: #1565C0;\n            }\n            QPushButton:disabled {\n                background-color: #B0BEC5;\n            }\n            /* CORRE├ç├âO: Estilo espec├¡fico para QMessageBox - evita heran├ºa de cor branca */\n            QMessageBox {\n                background-color: #ffffff;\n            }\n            QMessageBox QLabel {\n                color: #2c3e50;\n            }\n            QMessageBox QPushButton {\n                background-color: #e8e8e8;\n                color: #2c3e50;\n                border: 1px solid #bdc3c7;\n                border-radius: 5px;\n                padding: 6px 20px;\n                min-width: 70px;\n            }\n            QMessageBox QPushButton:hover {\n                background-color: #d0d0d0;\n            }\n        ')
    def setup_connections(self):
        '''Configura conex├Áes de sinais'''
        debug_log('setup_connections - In├¡cio')
        try:
            debug_log('setup_connections - Agendando update_port_list em 100ms')
            QTimer.singleShot(100, self.update_port_list)
            debug_log('setup_connections - Timer agendado com sucesso')
            return
        except Exception as e:
            debug_log(f'setup_connections - ERRO: {str(e)}')
            debug_log(f'setup_connections - Traceback: {traceback.format_exc()}')
    def update_port_list(self):
        '''Atualiza lista de portas seriais dispon├¡veis'''
        debug_log('update_port_list - In├¡cio')
        if self._is_updating_ports:
            debug_log('update_port_list - J├í est├í atualizando, retornando')
            return
        self._is_updating_ports = True
        debug_log('update_port_list - Flag _is_updating_ports = True')
        try:
            current_port = None
            if self.port_combo.count() > 0:
                current_port = self.port_combo.currentData()
                debug_log(f'update_port_list - Porta atual: {current_port}')
            debug_log('update_port_list - Listando portas COM...')
            ports = list(serial.tools.list_ports.comports())
            debug_log(f'update_port_list - {len(ports)} portas encontradas')
            self.port_combo.clear()
            debug_log('update_port_list - Combo limpo')
            if ports:
                samsung_ports = []
                other_ports = []
                for port in ports:
                    port_text = f'{port.device} - {port.description}'
                    debug_log(f'update_port_list - Processando: {port_text}')
                    if 'samsung' in port.description.lower() or 'mobile' in port.description.lower():
                        samsung_ports.append((port_text, port.device))
                        debug_log(f'update_port_list - Porta Samsung detectada: {port.device}')
                    else:
                        other_ports.append((port_text, port.device))
                for text, device in samsung_ports:
                    self.port_combo.addItem(text, device)
                    debug_log(f'update_port_list - Adicionada porta Samsung: {text}')
                for text, device in other_ports:
                    self.port_combo.addItem(text, device)
                if current_port:
                    index = self.port_combo.findData(current_port)
                    if index >= 0:
                        self.port_combo.setCurrentIndex(index)
                        debug_log(f'update_port_list - Porta anterior restaurada: {current_port}')
                        self._is_updating_ports = False
                        debug_log('update_port_list - Flag _is_updating_ports = False')
                        return
                if samsung_ports:
                    self.port_combo.setCurrentIndex(0)
                    debug_log('update_port_list - Primeira porta Samsung selecionada')
            else:
                self.port_combo.addItem('Nenhuma porta detectada')
                debug_log('update_port_list - Nenhuma porta detectada')
            debug_log('update_port_list - Atualiza├º├úo conclu├¡da com sucesso')
        except Exception as e:
            debug_log(f'update_port_list - ERRO: {str(e)}')
            debug_log(f'update_port_list - Traceback: {traceback.format_exc()}')
            logger.error(f'Erro ao listar portas: {str(e)}')
            self.port_combo.clear()
            self.port_combo.addItem('Erro ao listar portas')
        finally:
            self._is_updating_ports = False
            debug_log('update_port_list - Flag _is_updating_ports = False')
    def toggle_connection(self):
        '''Alterna conex├úo serial'''
        if self.samsung_manager.is_connected:
            self.disconnect_serial()
            return
        self.connect_serial()
    def connect_serial(self):
        '''Conecta ├á porta serial selecionada'''
        debug_log('connect_serial - In├¡cio')
        port_data = self.port_combo.currentData()
        if not port_data:
            self.log('ÔØî Nenhuma porta v├ílida selecionada')
            return
        self.log(f'­ƒöî Conectando a {port_data}...')
        self.connect_btn.setEnabled(False)
        self.refresh_ports_btn.setEnabled(False)
        def _do_connect():
            debug_log(f'_do_connect - Tentando conectar a {port_data}')
            try:
                debug_log('_do_connect - Tentando velocidade alta...')
                if self.samsung_manager.connect_serial(port_data, 115200):
                    debug_log('_do_connect - Conex├úo bem-sucedida em velocidade alta')
                    return (True, 115200)
                debug_log('_do_connect - Tentando velocidade baixa...')
                if self.samsung_manager.connect_serial(port_data, 9600):
                    debug_log('_do_connect - Conex├úo bem-sucedida em velocidade baixa')
                    return (True, 9600)
                debug_log('_do_connect - Falha na conex├úo')
                return (False, 'N├úo foi poss├¡vel estabelecer comunica├º├úo')
            except Exception as e:
                debug_log(f'_do_connect - ERRO: {str(e)}')
                debug_log(f'_do_connect - Traceback: {traceback.format_exc()}')
                return False, str(e)
        debug_log('connect_serial - Iniciando thread de conex├úo')
        self.execute_command(_do_connect)
    def disconnect_serial(self):
        '''Desconecta da porta serial'''
        self.samsung_manager.disconnect_serial()
        self.connection_status.setText('Desconectado')
        self.connection_status.setStyleSheet('\n            QLabel {\n                padding: 5px 10px;\n                border-radius: 4px;\n                background: #f44336;\n                color: white;\n                font-weight: bold;\n            }\n        ')
        self.connect_btn.setText('Forcar')
        self.enable_tools(False)
        self.log('­ƒöî Desconectado')
    def enable_tools(self, enabled=True):
        '''Habilita/desabilita ferramentas da aba Padrao.
        CORRECAO 12-08-2026: Com conexao sob demanda, botoes permanecem
        habilitados por padrao. Aceita enabled=False apenas para lock
        temporario durante execucao de comando (evita cliques duplos).
        Ao finalizar comando, on_command_finished chama enable_tools(True).
        '''
        state = True if enabled else False
        self.get_info_btn.setEnabled(state)
        for btn in self.tools_group.findChildren(QPushButton):
            if hasattr(btn, 'callback'):
                btn.setEnabled(state)
    def log(self, message):
        '''Adiciona mensagem ao log (inteligente por aba ativa)'''
        try:
            current_tab = self.tab_widget.currentIndex()
            if current_tab == 0:
                self.standard_log_message(f'­ƒôï {message}')
                return
            self.advanced_log_message(f'­ƒôï {message}')
            return
        except:
            self.advanced_log_message(f'­ƒôï {message}')
    def _is_main_thread(self):
        '''Retorna True quando o codigo executa na thread principal do QApplication.'''
        try:
            app = QApplication.instance()
            if app is None:
                return True
            return QThread.currentThread() == app.thread()
        except Exception:
            return True
    def advanced_log_message(self, message):
        '''Adiciona mensagem ao log avancado.
        Guard automatico: se for chamado de thread secundaria, redireciona
        via signal _log_lines_request (queued connection -> main thread)
        para evitar warning "Cannot queue arguments of type 'QTextCursor'".
        '''
        if not self._is_main_thread():
            self._log_lines_request.emit([message])
            return
        timestamp = time.strftime('%H:%M:%S')
        self.advanced_log.append(f'[{timestamp}] {message}')
    def standard_log_message(self, message):
        '''Adiciona mensagem ao terminal da aba padrao.
        Guard automatico: se for chamado de thread secundaria, redireciona
        via signal _log_lines_request (queued connection -> main thread)
        para evitar warning "Cannot queue arguments of type 'QTextCursor'".
        '''
        if not self._is_main_thread():
            self._log_lines_request.emit([message])
            return
        timestamp = time.strftime('%H:%M:%S')
        cursor = self.standard_log.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.standard_log.setTextCursor(cursor)
        self.standard_log.insertPlainText(f'[{timestamp}] {message}\n')
        cursor.movePosition(QTextCursor.End)
        self.standard_log.setTextCursor(cursor)
    def _exibir_linhas_no_log_ativo(self, linhas):
        '''Exibe uma lista de linhas no log da aba ativa (sempre na main thread).
ATIVADO via signal _log_lines_request (declarado na classe e
conectado no __init__). A partir de threads secundarias, use:
    self._log_lines_request.emit([linha1, linha2, ...])
Qt enfileira automaticamente para a main thread (queued connection)
porque o widget vive nela ÔÇö sem necessidade de QTimer.singleShot.
OTIMIZACAO 23-05-2026 v3: para listas grandes (>3 linhas), faz uma
unica operacao de insercao em vez de loop com setTextCursor por linha.
Loops longos com cursor manipulation podem congelar a UI por 100-500ms
em listas de 30-60 linhas (caso do "Obter Informacoes" Samsung).
'''
        if not linhas:
            return
        try:
            current_tab = self.tab_widget.currentIndex()
        except Exception:
            current_tab = 1
        timestamp = time.strftime('%H:%M:%S')
        bloco = '\n'.join((f'[{timestamp}] {linha}' for linha in linhas))
        if current_tab == 0:
            cursor = self.standard_log.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.standard_log.setTextCursor(cursor)
            self.standard_log.insertPlainText(bloco + '\n')
            cursor.movePosition(QTextCursor.End)
            self.standard_log.setTextCursor(cursor)
            return
        self.advanced_log.append(bloco)
    def _on_progress_value_request(self, value):
        '''Atualiza setValue do QProgressDialog atual (main thread).'''
        pd = self._current_progress_dialog
        if pd is None:
            return
        try:
            pd.setValue(int(value))
            return
        except RuntimeError:
            self._current_progress_dialog = None
        except Exception:
            return
    def _on_progress_label_request(self, text):
        '''Atualiza setLabelText do QProgressDialog atual (main thread).'''
        pd = self._current_progress_dialog
        if pd is None:
            return
        try:
            pd.setLabelText(str(text))
            return
        except RuntimeError:
            self._current_progress_dialog = None
        except Exception:
            return
    def _on_progress_close_request(self):
        '''Fecha o QProgressDialog atual (main thread) e limpa referencia.'''
        pd = self._current_progress_dialog
        if pd is None:
            return
        try:
            pd.close()
        except RuntimeError:
            pass
        except Exception:
            pass
        finally:
            self._current_progress_dialog = None
    def clear_standard_log(self):
        '''Limpa o terminal da aba padr├úo'''
        self.standard_log.clear()
        self.standard_log_message('­ƒùæ´©Å Terminal limpo')
    def clear_advanced_log(self):
        '''Limpa o terminal da aba advanced'''
        self.advanced_log.clear()
        self.advanced_log_message('­ƒùæ´©Å Terminal limpo')
    def _execute_with_auto_connect(self, operation_func, operation_name='Operacao'):
        '''Detecta porta, conecta, executa e desconecta automaticamente.
        Fallback: se samsung_manager ja esta conectado (manual), usa conexao existente.
        Se auto-detect falhar, orienta o tecnico a conectar manualmente.
        '''
        if self.samsung_manager.is_connected:
            self.log(f'Executando {operation_name}...')
            self.execute_command(operation_func)
            return
        if hasattr(self, 'samsung_advanced') and self.samsung_advanced.serial_port and self.samsung_advanced.serial_port.is_open:
            self.log('ÔÜá´©Å Porta em uso pela aba Advanced. Aguarde ou desconecte la.')
            return
        self.log('­ƒöì Detectando dispositivo Samsung...')
        def _auto_connect_and_run():
            ports = self.samsung_manager.find_samsung_ports()
            samsung_ports = [p for p in ports if p.get('is_samsung')]
            if not samsung_ports:
                return '__AUTO_CONNECT_FAIL__'
            port = samsung_ports[0]['port']
            if not (self.samsung_manager.connect_serial(port, 115200) or self.samsung_manager.connect_serial(port, 9600)):
                return '__AUTO_CONNECT_FAIL__'
            try:
                result = operation_func()
            finally:
                self.samsung_manager.disconnect_serial()
            return result
        self.execute_command(_auto_connect_and_run)
    def execute_command(self, function, *args, **kwargs):
        '''Executa comando em thread separada'''
        if self.command_thread and self.command_thread.isRunning():
            self.log('ÔÜá´©Å Comando j├í em execu├º├úo')
            return
        self.command_thread = CommandThread(function, *args, **kwargs)
        self.command_thread.command_started.connect(self.on_command_started)
        self.command_thread.command_finished.connect(self.on_command_finished)
        self.command_thread.command_error.connect(self.on_command_error)
        self.command_thread.start()
    def on_command_started(self):
        '''Quando comando inicia'''
        self.enable_tools(False)
        self.connect_btn.setEnabled(False)
    def on_command_finished(self, result):
        '''Quando comando termina com resultado'''
        debug_log(f'on_command_finished - result type: {type(result)}, result: {result}')
        if isinstance(result, str) and result.startswith('(') and result.endswith(')'):
            try:
                import ast
                parsed_result = ast.literal_eval(result)
                if isinstance(parsed_result, tuple) and len(parsed_result) == 2:
                    success, data = parsed_result
                    if success:
                        baudrate = data
                        self.connection_status.setText('Conectado')
                        self.connection_status.setStyleSheet('\n                            QLabel {\n                                padding: 5px 10px;\n                                border-radius: 4px;\n                                background: #4CAF50;\n                                color: white;\n                                font-weight: bold;\n                            }\n                        ')
                        self.connect_btn.setText('Liberar')
                        self.enable_tools(True)
                        self.log('Ô£à Conectado com sucesso')
                        self.log('Ô£à Comunica├º├úo estabelecida com o dispositivo')
                        def _unlock_modem():
                            self.samsung_manager.ensure_modem_unlocked()
                            return 'Ô£à Modem desbloqueado'
                        QTimer.singleShot(100, (lambda: self.execute_command(_unlock_modem)))
                    else:
                        error_msg = data if isinstance(data, str) else 'Falha na conex├úo'
                        self.log(f'ÔØî {error_msg}')
                        self.enable_tools(False)
                else:
                    self.log(result)
            except:
                self.log(result)
        elif isinstance(result, str) and result == '__AUTO_CONNECT_FAIL__':
            self.log('ÔÜá´©Å Nenhum dispositivo Samsung detectado automaticamente.')
            self.log('­ƒÆí Conecte o aparelho via USB e tente novamente,')
            self.log("   ou use o botao 'Conectar' acima para conexao manual.")
        else:
            self.log(result)
        self.enable_tools(True)
        self.connect_btn.setEnabled(True)
        self.refresh_ports_btn.setEnabled(True)
        debug_log('on_command_finished - Controles reabilitados')
        try:
            if self.adb_manager:
                def _finalize_adb_bg():
                    try:
                        self.adb_manager.finalize_adb_operation()
                        return
                    except Exception:
                        return
                threading.Thread(target=_finalize_adb_bg, name='adb-finalize-bg', daemon=True).start()
        except Exception:
            pass
        try:
            ct = self.command_thread
            if ct is not None:
                if ct.isRunning():
                    ct.wait(2000)
                ct.deleteLater()
                self.command_thread = None
                return
        except Exception:
            self.command_thread = None
    def on_command_error(self, error):
        '''Quando comando tem erro'''
        debug_log(f'on_command_error - {error}')
        self.log(f'ÔØî Erro: {error}')
        self.enable_tools(self.samsung_manager.is_connected)
        self.connect_btn.setEnabled(True)
        self.refresh_ports_btn.setEnabled(True)
        try:
            ct = self.command_thread
            if ct is not None:
                if ct.isRunning():
                    ct.wait(2000)
                ct.deleteLater()
                self.command_thread = None
                return
        except Exception:
            self.command_thread = None
    def get_device_info(self):
        '''Obt├®m informa├º├Áes do dispositivo e exibe no terminal'''
        self.log('­ƒô▒ Iniciando coleta de informa├º├Áes do dispositivo...')
        def _get_info():
            def progress_callback(msg):
                self._log_lines_request.emit([f'ÔÅ│ {msg}'])
            info = self.samsung_manager.get_device_info(progress_callback)
            if info:
                formatted = []
                labels = [('model', '­ƒô▒ Modelo'), ('android', '­ƒñû Android'), ('android_version', '­ƒñû Vers├úo Sistema'), ('baseband', '­ƒôí Baseband'), ('imei', '­ƒöó IMEI'), ('serialno', '­ƒöñ Serial'), ('product_code', '­ƒôª C├│digo Produto'), ('country_code', '­ƒîÅ Pa├¡s'), ('csc', '­ƒîì CSC/Regi├úo'), ('lock_status', '­ƒöÆ Status Bloqueio'), ('unique_number', '­ƒöÉ N├║mero ├Ünico'), ('connection_type', '­ƒöù Protocolo'), ('sdp_status', 'ÔÜÖ´©Å Status SDP'), ('hardware_version', '­ƒöº Vers├úo Hardware'), ('manufacturer', '­ƒÅ¡ Fabricante'), ('revision', '­ƒôï Revis├úo'), ('build', '­ƒö¿ Build'), ('kernel', '­ƒÆ╗ Kernel'), ('imsi', '­ƒô▓ IMSI'), ('carrier', '­ƒôÂ Operadora'), ('portmode', '­ƒöî Modo Porta')]
                formatted.append('ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ')
                for key, label in labels:
                    if key not in info:
                        continue
                    value = info[key]
                    if not value or value == 'N/A':
                        value = 'N├úo dispon├¡vel'
                    if key == 'imei' and len(str(value)) == 15:
                        value = ' '.join([value[i:i + 4] for i in range(0, 15, 4)])
                    if value == 'N├úo dispon├¡vel' and key not in ('model', 'imei', 'serialno', 'baseband', 'android_version'):
                        continue
                    if key == 'serialno' and value == 'Protegido pelo dispositivo':
                        formatted.append(f'{label}: ­ƒöÆ {value}')
                        continue
                    if key == 'connection_type' and value:
                        clean_value = value.replace('AT,', '').replace('AT', '').strip()
                        if clean_value.startswith(','):
                            clean_value = clean_value[1:].strip()
                        if not clean_value:
                            clean_value = 'USB/MTP'
                        formatted.append(f'{label}: {clean_value}')
                        continue
                    if key == 'lock_status' and value:
                        lock_icon = '­ƒöô' if value == 'NONE' else '­ƒöÆ'
                        formatted.append(f'{label}: {lock_icon} {value}')
                        continue
                    if key == 'android_version' and value and value != 'N├úo dispon├¡vel':
                        formatted.append(f'{label}: Ô£¿ {value}')
                        continue
                    formatted.append(f'{label}: {value}')
                    continue
                formatted.append('ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ')
                formatted_output = []
                formatted_output.append('==================================================')
                formatted_output.append('[COM+ADB] read INFO Scanning for device... COM')
                formatted_output.append('Reading Info... OK')
                formatted_output.append('')
                if info.get('model'):
                    formatted_output.append(f'Model Number : {info['model']}')
                if info.get('android') or info.get('baseband'):
                    formatted_output.append('Firmware ver:')
                    if info.get('baseband'):
                        baseband = info['baseband']
                        formatted_output.append(f'  BL : {baseband}')
                        formatted_output.append(f'  AP : {baseband}')
                        formatted_output.append(f'  CP : {baseband}')
                        formatted_output.append(f'  CSC : {baseband}')
                if info.get('android_version'):
                    formatted_output.append(f'Android Version : Ô£¿ {info['android_version']} (EXCLUSIVO UNION)')
                if info.get('country_code'):
                    formatted_output.append(f'Country Code : {info['country_code']}')
                elif info.get('csc'):
                    formatted_output.append(f'CSC/Region : {info['csc']}')
                if info.get('serialno'):
                    if info['serialno'] == 'Protegido pelo dispositivo':
                        formatted_output.append(f'Serial Number : ­ƒöÆ {info['serialno']}')
                    else:
                        formatted_output.append(f'Serial Number : {info['serialno']}')
                if info.get('imei'):
                    formatted_output.append(f'IMEI : {info['imei']}')
                if info.get('unique_number'):
                    formatted_output.append(f'Unique Number : {info['unique_number']}')
                if info.get('lock_status'):
                    lock_status = info['lock_status']
                    if lock_status == 'NONE':
                        formatted_output.append(f'LOCK : {lock_status} ­ƒöô')
                    else:
                        formatted_output.append(f'LOCK : {lock_status} ­ƒöÆ')
                extras = []
                if info.get('connection_type'):
                    clean_conn = info['connection_type'].replace('AT,', '').replace('AT', '').strip()
                    if clean_conn.startswith(','):
                        clean_conn = clean_conn[1:].strip()
                    if clean_conn:
                        extras.append(f'Connection : {clean_conn}')
                if info.get('sdp_status'):
                    extras.append(f'SDP Status : {info['sdp_status']}')
                if extras:
                    formatted_output.append('')
                    formatted_output.append('INFORMA├ç├òES EXTRAS (EXCLUSIVO UNION):')
                    formatted_output.extend(extras)
                formatted_output.append('')
                formatted_output.append('TOOL UNION v1.3 (MELHORADO)')
                formatted_output.append('==================================================')
                linhas_a_exibir = ['­ƒôï INFORMA├ç├òES DO DISPOSITIVO SAMSUNG'] + list(formatted_output)
                self._log_lines_request.emit(linhas_a_exibir)
                return 'Ô£à Informa├º├Áes obtidas e exibidas no terminal!'
            return 'ÔØî N├úo foi poss├¡vel obter informa├º├Áes do dispositivo'
        self.log('ÔÅ│ AGUARDE - Coletando informa├º├Áes do dispositivo...')
        self.log('ÔÜá´©Å N├âO DESCONECTE O DISPOSITIVO DURANTE O PROCESSO')
        self._execute_with_auto_connect(_get_info, 'Obter Informacoes')
    def frp_unlock_unified(self):
        '''FRP Unlock unificado com sele├º├úo de m├®todo'''
        method_index = self.frp_combo.currentIndex()
        if method_index == 0:
            QMessageBox.warning(self, 'Aviso', 'Por favor, selecione um m├®todo FRP antes de continuar.')
            return
        reply = QMessageBox.warning(self, 'Aviso Importante - Fun├º├úo Experimental', 'ÔÜá´©Å ATEN├ç├âO: Esta fun├º├úo N├âO est├í 100% funcional!\n\nEsta ferramenta est├í em DESENVOLVIMENTO e pode:\nÔÇó Falhar na opera├º├úo\nÔÇó Causar travamentos\nÔÇó N├úo funcionar como esperado\n\nUse por sua CONTA E RISCO!\n\nDeseja continuar mesmo assim?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        if method_index == 1:
            self.frp_unlock_pre_2022()
            return
        if method_index == 2:
            self.frp_unlock_2022()
            return
        if method_index == 3:
            self.frp_unlock_2024()
    def frp_unlock_pre_2022(self):
        '''FRP Unlock para dispositivos pre-2022'''
        reply = QMessageBox.question(self, 'Confirmar FRP Unlock', 'Esta opera├º├úo tentar├í desbloquear o FRP do dispositivo.\n\nAVISO: Use apenas em dispositivos que voc├¬ possui!\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.log('­ƒöô Iniciando FRP Unlock Pre-2022...')
            self.execute_command(self.samsung_manager.frp_unlock_pre_2022)
    def frp_unlock_2022(self):
        '''FRP Unlock para dispositivos 2022'''
        reply = QMessageBox.question(self, 'Confirmar FRP Unlock', 'Esta opera├º├úo tentar├í desbloquear o FRP do dispositivo.\n\nCompat├¡vel com patches Aug-Dec 2022.\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.log('­ƒöô Iniciando FRP Unlock 2022...')
            self.execute_command(self.samsung_manager.frp_unlock_2022)
    def frp_unlock_2024(self):
        '''FRP Unlock para dispositivos 2024'''
        reply = QMessageBox.question(self, 'Confirmar FRP Unlock', 'Esta opera├º├úo tentar├í desbloquear o FRP do dispositivo.\n\nCompat├¡vel com dispositivos 2024.\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.log('­ƒöô Iniciando FRP Unlock 2024...')
            self.execute_command(self.samsung_manager.frp_unlock_2024)
    def open_wifitest(self):
        '''Abre menu WIFITEST'''
        self.log('­ƒôí Abrindo menu WIFITEST...')
        def _open_wifitest():
            if self.samsung_manager.open_wifitest_menu():
                return 'Ô£à Menu WIFITEST aberto com sucesso!'
            return 'ÔØî Falha ao abrir menu WIFITEST'
        self.execute_command(_open_wifitest)
    def reboot_device(self):
        '''Reinicia o dispositivo'''
        reply = QMessageBox.question(self, 'Confirmar Reinicializa├º├úo', 'Deseja reiniciar o dispositivo?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            def _reboot():
                if self.samsung_manager.reboot_device('normal'):
                    return 'Comando de reinicializa├º├úo enviado com sucesso!\nO dispositivo deve reiniciar agora.'
                return 'Falha ao enviar comando de reinicializa├º├úo'
            self._execute_with_auto_connect(_reboot, 'Reiniciar Dispositivo')
    def reboot_download(self):
        '''Reinicia em modo download'''
        reply = QMessageBox.question(self, 'Confirmar Modo Download', 'Deseja reiniciar o dispositivo em modo Download?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            def _reboot_download():
                if self.samsung_manager.reboot_device('download'):
                    return 'Comando de Download Mode enviado com sucesso!\nO dispositivo deve reiniciar em modo Download agora.'
                return 'Falha ao enviar comando de Download Mode'
            self._execute_with_auto_connect(_reboot_download, 'Modo Download')
    def check_imei(self):
        '''Verifica IMEI do dispositivo'''
        def _check_imei():
            imei = self.samsung_manager.check_imei()
            if imei:
                return f'Ô£à IMEI: {imei}'
            return 'ÔØî N├úo foi poss├¡vel obter o IMEI'
        self._execute_with_auto_connect(_check_imei, 'Verificar IMEI')
    def factory_reset_device(self):
        '''
        Executa factory reset no dispositivo Samsung
        IMPLEMENTA├ç├âO CIR├ÜRGICA com m├║ltiplas confirma├º├Áes de seguran├ºa
        seguindo as diretrizes RESTORECELL para opera├º├Áes cr├¡ticas
        '''
        first_reply = QMessageBox.critical(self, 'ATEN├ç├âO - OPERA├ç├âO CR├ìTICA E IRREVERS├ìVEL', '<div style="text-align: center;"><h2 style="color: #d32f2f;">FACTORY RESET</h2><p style="font-size: 14px;"><b>Esta opera├º├úo ir├í APAGAR COMPLETAMENTE todos os dados do dispositivo!</b></p><br><p style="color: #d32f2f; font-size: 13px;"><b>DADOS QUE SER├âO PERDIDOS PERMANENTEMENTE:</b></p><p>ÔÇó Todas as fotos, v├¡deos e documentos</p><p>ÔÇó Aplicativos instalados e suas configura├º├Áes</p><p>ÔÇó Contatos, mensagens e hist├│rico de chamadas</p><p>ÔÇó Configura├º├Áes do sistema e contas</p><p>ÔÇó Senhas salvas e dados de aplicativos</p><br><p style="color: #d32f2f; font-size: 14px;"><b>ESTA OPERA├ç├âO N├âO PODE SER DESFEITA!</b></p><br><p>Tem CERTEZA ABSOLUTA que deseja continuar?</p></div>', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if first_reply != QMessageBox.Yes:
            self.log('Factory Reset cancelado pelo usu├írio (1┬¬ confirma├º├úo)')
            return
        second_reply = QMessageBox.warning(self, 'CONFIRMA├ç├âO DE RESPONSABILIDADE', '<div style="text-align: center;"><h3 style="color: #f57c00;">CONFIRMA├ç├âO FINAL</h3><br><p><b>Voc├¬ confirma que:</b></p><p>ÔÇó ├ë o propriet├írio leg├¡timo deste dispositivo</p><p>ÔÇó Tem autoriza├º├úo para realizar esta opera├º├úo</p><p>ÔÇó Fez backup de todos os dados importantes</p><p>ÔÇó Entende que a opera├º├úo ├® IRREVERS├ìVEL</p><br><p style="color: #d32f2f;"><b>O TECH UNION SOLUTIONS n├úo se responsabiliza por:</b></p><p>ÔÇó Perda de dados n├úo salvos em backup</p><p>ÔÇó Problemas decorrentes do factory reset</p><p>ÔÇó Uso indevido desta ferramenta</p><br><p style="font-size: 14px;"><b>Confirma a execu├º├úo do Factory Reset?</b></p></div>', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if second_reply != QMessageBox.Yes:
            self.log('Factory Reset cancelado pelo usu├írio (2┬¬ confirma├º├úo)')
            return
        third_reply = QMessageBox.question(self, 'CONFIRMA├ç├âO T├ëCNICA FINAL', '<div style="text-align: center;"><h3 style="color: #1976d2;">EXECU├ç├âO T├ëCNICA</h3><br><p><b>Opera├º├úo:</b> Factory Reset via Comunica├º├úo Serial</p><p><b>Protocolo:</b> Comandos Propriet├írios Samsung</p><p><b>Efeito:</b> Formata├º├úo Completa Imediata</p><br><p style="color: #d32f2f; font-size: 13px;"><b>├ÜLTIMA OPORTUNIDADE PARA CANCELAR</b></p><br><p>Ap├│s clicar "Sim", os comandos ser├úo enviados IMEDIATAMENTE</p><p>e o dispositivo iniciar├í o processo de formata├º├úo.</p><br><p><b>Executar Factory Reset AGORA?</b></p></div>', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if third_reply != QMessageBox.Yes:
            self.log('Factory Reset cancelado pelo usu├írio (3┬¬ confirma├º├úo)')
            return
        self.log('INICIANDO FACTORY RESET - OPERA├ç├âO CR├ìTICA CONFIRMADA')
        self.log('ATEN├ç├âO: Todos os dados do dispositivo ser├úo APAGADOS!')
        self.log('Executando comandos propriet├írios Samsung...')
        def _factory_reset():
            '''Execu├º├úo do factory reset em thread separada'''
            try:
                success, message = self.samsung_manager.factory_reset_device()
                if success:
                    self.log('============================================================')
                    self.log('FACTORY RESET EXECUTADO COM SUCESSO!')
                    self.log('============================================================')
                    return message
                self.log('============================================================')
                self.log('FACTORY RESET FALHOU!')
                self.log('============================================================')
                return message
            except Exception as e:
                error_msg = f'ERRO CR├ìTICO durante Factory Reset: {str(e)}'
                logger.error(error_msg)
                return error_msg
        self._execute_with_auto_connect(_factory_reset, 'Factory Reset')
    def execute_dvif_info(self):
        '''Executa comando propriet├írio para obter informa├º├Áes do dispositivo'''
        try:
            self.advanced_log_message('­ƒöÑ Iniciando Info Download - Obtendo informa├º├Áes do dispositivo...')
            def _execute_dvif():
                return self.samsung_advanced.execute_dvif_command()
            def _on_dvif_finished(result):
                try:
                    if result['success']:
                        self.advanced_log_message('Ô£à Info Download executado com sucesso!')
                        data = result['data']
                        self.advanced_log_message('==================================================')
                        self.advanced_log_message('­ƒôï INFORMA├ç├òES DO DISPOSITIVO SAMSUNG')
                        self.advanced_log_message('==================================================')
                        if 'model' in data:
                            self.advanced_log_message(f'­ƒô▒ Modelo: {data['model']}')
                        if 'vendor' in data:
                            self.advanced_log_message(f'­ƒÅ¡ Fabricante: {data['vendor']}')
                        if 'capa' in data:
                            self.advanced_log_message(f'­ƒÆ¥ Capacidade: {data['capa']}GB')
                        if 'sales' in data:
                            self.advanced_log_message(f'­ƒîì Regi├úo/CSC: {data['sales']}')
                        if 'ver' in data:
                            self.advanced_log_message(f'­ƒôï Vers├úo Firmware: {data['ver']}')
                        if 'un' in data:
                            self.advanced_log_message(f'­ƒöÉ N├║mero ├Ünico: {data['un']}')
                        if 'fwver' in data:
                            self.advanced_log_message(f'­ƒöº Vers├úo FW: {data['fwver']}')
                        if 'product' in data:
                            self.advanced_log_message(f'­ƒôª C├│digo Produto: {data['product']}')
                        if 'did' in data:
                            self.advanced_log_message(f'­ƒåö Device ID: {data['did']}')
                        if 'tmu_temp' in data:
                            self.advanced_log_message(f'­ƒîí´©Å Temperatura: {data['tmu_temp']}┬░C')
                        self.advanced_log_message('==================================================')
                        technical_fields = [k for k in data.keys() if k not in ('protocol', 'method', 'raw_response', 'timestamp')]
                        self.advanced_log_message(f'Ô£à Total de informa├º├Áes obtidas: {len(technical_fields)}')
                        self.advanced_log_message('==================================================')
                        self.log('­ƒÄë Info Download Samsung executado com sucesso!')
                        return
                except Exception as e:
                    self.advanced_log_message(f'ÔØî Erro inesperado: {str(e)}')
                    self.log('ÔØî Erro Info Download - falha na execu├º├úo')
                self.advanced_log_message(f'ÔØî Erro Info Download: {result['error']}')
                self.log('ÔØî Info Download falhou - verifique conex├úo Samsung')
            def _on_dvif_error(error):
                self.advanced_log_message(f'ÔØî Erro Info Download: {str(error)}')
                self.log('ÔØî Info Download falhou - erro de comunica├º├úo')
            if self.command_thread and self.command_thread.isRunning():
                self.advanced_log_message('ÔÜá´©Å Comando j├í em execu├º├úo')
                return
            self.command_thread = CommandThread(_execute_dvif)
            self.command_thread.command_started.connect((lambda: self.advanced_log_message('­ƒöä Executando Info Download...')))
            self.command_thread.command_finished.connect((lambda result_str: self._safe_handle_dvif_result(result_str, _on_dvif_finished)))
            self.command_thread.command_error.connect(_on_dvif_error)
            self.command_thread.start()
            return
        except Exception as e:
            self.advanced_log_message(f'ÔØî Erro ao executar Info Download: {str(e)}')
    def execute_frp_android_9_10(self):
        '''Executa FRP Bypass para Android 9-10'''
        try:
            reply = QMessageBox.warning(self, '­ƒöô FRP Android 9-10', '­ƒÜ¿ ATEN├ç├âO: FRP Bypass Android 9-10\n\nM├®todo testado em Samsung Android 9-10 com processadores Exynos.\n\nREQUISITOS:\nÔÇó Dispositivo deve estar no menu *#0*#\nÔÇó Cabo USB conectado\nÔÇó Drivers Samsung instalados\n\nÔÜá´©Å Use apenas em dispositivos pr├│prios!\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply != QMessageBox.Yes:
                self.advanced_log_message('ÔØî FRP Android 9-10 cancelado pelo usu├írio')
                return
            self.advanced_log_message('­ƒöô Iniciando FRP Bypass Android 9-10...')
            def _execute_frp():
                return self.samsung_advanced.execute_frp_android_9_10()
            def _on_frp_finished(result):
                try:
                    if result.get('requires_usb_reconnection', False):
                        self.advanced_log_message('­ƒÜ¿ INTERVEN├ç├âO NECESS├üRIA - Acesso negado detectado!')
                        reply = QMessageBox.question(self, '­ƒöä Interven├º├úo Necess├íria - FRP Android 9-10', result['reconnection_message'], QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                        if reply == QMessageBox.Yes:
                            self.advanced_log_message('Ô£à Usu├írio confirmou interven├º├úo - continuando com ADB...')
                            def _continue_with_adb():
                                return self.samsung_advanced.continue_frp_with_adb(result)
                            def _on_adb_finished(adb_result):
                                if adb_result['success']:
                                    self.advanced_log_message('­ƒÄë FRP BYPASS ANDROID 9-10 CONCLU├ìDO!')
                                    self.advanced_log_message('Ô£à ADB foi ativado e comandos executados')
                                    self.advanced_log_message('­ƒô▒ Dispositivo deve estar desbloqueado')
                                    self.log('­ƒÄë FRP Android 9-10 executado com sucesso!')
                                    return
                                self.advanced_log_message('ÔØî Processo ADB falhou - Verifique se o dispositivo est├í autorizado')
                                self.log('ÔØî Processo ADB falhou - Verifique se o dispositivo est├í autorizado')
                            def _on_adb_error(error):
                                self.advanced_log_message('ÔØî Erro no processo ADB - Verifique conex├úo USB')
                                self.log('ÔØî Erro no processo ADB - Verifique conex├úo USB')
                            if self.command_thread and self.command_thread.isRunning():
                                self.advanced_log_message('ÔÜá´©Å Aguarde o processo anterior finalizar...')
                                return
                            self.command_thread = CommandThread(_continue_with_adb)
                            self.command_thread.command_finished.connect((lambda result_str: _on_adb_finished(eval(result_str))))
                            self.command_thread.command_error.connect(_on_adb_error)
                            self.command_thread.start()
                            return
                        self.advanced_log_message('ÔØî Usu├írio cancelou interven├º├úo - FRP interrompido')
                        self.log('ÔØî FRP Android 9-10 cancelado pelo usu├írio')
                        return
                    if result['success']:
                        self.advanced_log_message('­ƒÄë FRP BYPASS ANDROID 9-10 CONCLU├ìDO!')
                        self.advanced_log_message('Ô£à ADB foi ativado e comandos executados')
                        self.advanced_log_message('­ƒô▒ Dispositivo deve estar desbloqueado')
                        for cmd_result in result['commands_executed']:
                            status = 'Ô£à' if cmd_result['success'] else 'ÔØî'
                            self.advanced_log_message(f'{status} {cmd_result['description']}')
                        self.log('­ƒÄë FRP Android 9-10 executado com sucesso!')
                        return
                    self.advanced_log_message(f'ÔØî FRP falhou: {result['error']}')
                    if result['commands_executed']:
                        self.advanced_log_message('­ƒôï Comandos executados:')
                        for cmd_result in result['commands_executed']:
                            status = 'Ô£à' if cmd_result['success'] else 'ÔØî'
                            self.advanced_log_message(f'  {status} {cmd_result['description']}')
                    if not result['adb_activated']:
                        self.advanced_log_message('­ƒÆí Dica: Certifique-se que o dispositivo est├í no menu *#0*#')
                    self.log(f'ÔØî FRP Android 9-10 falhou: {result['error']}')
                    return
                except Exception as e:
                    self.advanced_log_message(f'ÔØî Erro inesperado: {str(e)}')
                    self.log(f'ÔØî Erro FRP Android 9-10: {str(e)}')
            def _on_frp_error(error):
                self.advanced_log_message(f'ÔØî Erro FRP Android 9-10: {str(error)}')
                self.log(f'ÔØî Erro FRP Android 9-10: {str(error)}')
            if self.command_thread and self.command_thread.isRunning():
                self.advanced_log_message('ÔÜá´©Å Comando j├í em execu├º├úo')
                return
            self.command_thread = CommandThread(_execute_frp)
            self.command_thread.command_started.connect((lambda: self.advanced_log_message('­ƒöä Iniciando FRP...')))
            self.command_thread.command_finished.connect((lambda result_str: self._safe_handle_frp_result(result_str, _on_frp_finished)))
            self.command_thread.command_error.connect(_on_frp_error)
            self.command_thread.start()
            return
        except Exception as e:
            self.advanced_log_message('ÔØî Erro ao executar FRP - Verifique conex├úo')
    def execute_frp_android_11_plus(self):
        '''Executa FRP Bypass para Android 11+ (m├®todo validado 2023)'''
        try:
            reply = QMessageBox.warning(self, '­ƒöÑ FRP Android 11+', '­ƒÜ¿ ATEN├ç├âO: FRP Bypass Android 11+ (M├®todo Validado 2023)\n\n­ƒôï M├ëTODO TESTADO E VALIDADO:\nÔÇó Samsung Android 11-12 com processadores Exynos\nÔÇó Baseado no validador que funcionou (SM-A205G)\nÔÇó Pode funcionar em outros modelos Samsung similares\n\n­ƒôï REQUISITOS:\nÔÇó Dispositivo deve estar no menu *#0*#\nÔÇó Cabo USB conectado\nÔÇó Drivers Samsung instalados\n\nÔÜá´©Å IMPORTANTE:\nÔÇó Use apenas em dispositivos pr├│prios!\nÔÇó Processo pode requerer interven├º├úo (desconectar/reconectar USB)\nÔÇó Aguarde instru├º├Áes na tela se necess├írio\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply != QMessageBox.Yes:
                self.advanced_log_message('ÔØî FRP Android 11+ cancelado pelo usu├írio')
                return
            self.advanced_log_message('­ƒöÑ Iniciando FRP Bypass Android 11+ (m├®todo validado)...')
            def _execute_frp_11_plus():
                return self.samsung_advanced.execute_frp_android_11_plus()
            def _on_frp_11_plus_finished(result):
                try:
                    if result.get('requires_usb_reconnection', False):
                        self.advanced_log_message('­ƒÜ¿ INTERVEN├ç├âO NECESS├üRIA - Conex├úo caiu (comportamento normal)!')
                        reply = QMessageBox.question(self, '­ƒöä Interven├º├úo Necess├íria - FRP Android 11+', result['reconnection_message'], QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                        if reply == QMessageBox.Yes:
                            self.advanced_log_message('Ô£à Usu├írio confirmou interven├º├úo - continuando com ADB...')
                            def _continue_with_adb_11_plus():
                                return self.samsung_advanced.continue_frp_android_11_plus_with_adb(result)
                            def _on_adb_11_plus_finished(adb_result):
                                if adb_result['success']:
                                    self.advanced_log_message('­ƒÄë FRP BYPASS ANDROID 11+ CONCLU├ìDO!')
                                    self.advanced_log_message('Ô£à ADB foi ativado e comandos Android 11+ executados')
                                    self.advanced_log_message('­ƒô▒ Dispositivo deve estar desbloqueado')
                                    self.log('­ƒÄë FRP Android 11+ executado com sucesso!')
                                    return
                                self.advanced_log_message('ÔØî Processo ADB Android 11+ falhou - Verifique se o dispositivo est├í autorizado')
                                self.log('ÔØî Processo ADB Android 11+ falhou - Verifique se o dispositivo est├í autorizado')
                            def _on_adb_11_plus_error(error):
                                self.advanced_log_message('ÔØî Erro no processo ADB Android 11+ - Verifique conex├úo USB')
                                self.log('ÔØî Erro no processo ADB Android 11+ - Verifique conex├úo USB')
                            if self.command_thread and self.command_thread.isRunning():
                                self.advanced_log_message('ÔÜá´©Å Aguarde o processo anterior finalizar...')
                                return
                            self.command_thread = CommandThread(_continue_with_adb_11_plus)
                            self.command_thread.command_finished.connect((lambda result_str: self._safe_handle_frp_result(result_str, _on_adb_11_plus_finished)))
                            self.command_thread.command_error.connect(_on_adb_11_plus_error)
                            self.command_thread.start()
                            return
                        self.advanced_log_message('ÔØî Usu├írio cancelou interven├º├úo - FRP Android 11+ interrompido')
                        self.log('ÔØî FRP Android 11+ cancelado pelo usu├írio')
                        return
                    if result['success']:
                        self.advanced_log_message('­ƒÄë FRP BYPASS ANDROID 11+ CONCLU├ìDO!')
                        self.advanced_log_message('Ô£à ADB foi ativado e comandos Android 11+ executados')
                        self.advanced_log_message('­ƒô▒ Dispositivo deve estar desbloqueado')
                        for cmd_result in result['commands_executed']:
                            status = 'Ô£à' if cmd_result['success'] else 'ÔØî'
                            self.advanced_log_message(f'{status} {cmd_result['description']}')
                        self.log('­ƒÄë FRP Android 11+ executado com sucesso!')
                        return
                    self.advanced_log_message(f'ÔØî FRP Android 11+ falhou: {result['error']}')
                    if result['commands_executed']:
                        self.advanced_log_message('­ƒôï Comandos executados:')
                        for cmd_result in result['commands_executed']:
                            status = 'Ô£à' if cmd_result['success'] else 'ÔØî'
                            self.advanced_log_message(f'  {status} {cmd_result['description']}')
                    if not result['adb_activated']:
                        self.advanced_log_message('­ƒÆí Dica: Certifique-se que o dispositivo est├í no menu *#0*#')
                    self.log(f'ÔØî FRP Android 11+ falhou: {result['error']}')
                    return
                except Exception as e:
                    self.advanced_log_message(f'ÔØî Erro inesperado: {str(e)}')
                    self.log(f'ÔØî Erro FRP Android 11+: {str(e)}')
            def _on_frp_11_plus_error(error):
                self.advanced_log_message(f'ÔØî Erro FRP Android 11+: {str(error)}')
                self.log(f'ÔØî Erro FRP Android 11+: {str(error)}')
            if self.command_thread and self.command_thread.isRunning():
                self.advanced_log_message('ÔÜá´©Å Comando j├í em execu├º├úo')
                return
            self.command_thread = CommandThread(_execute_frp_11_plus)
            self.command_thread.command_started.connect((lambda: self.advanced_log_message('­ƒöä Iniciando FRP Android 11+...')))
            self.command_thread.command_finished.connect((lambda result_str: self._safe_handle_frp_result(result_str, _on_frp_11_plus_finished)))
            self.command_thread.command_error.connect(_on_frp_11_plus_error)
            self.command_thread.start()
            return
        except Exception as e:
            self.advanced_log_message('ÔØî Erro ao executar FRP Android 11+ - Verifique conex├úo')
    def execute_frp_adb_only(self):
        '''
        Executa FRP Bypass apenas com comandos ADB (dispositivo j├í autorizado)
        CORRE├ç├âO CIR├ÜRGICA: Removida verifica├º├úo redundante - check_adb_status j├í faz isso
        com tratamento de estados intermedi├írios (connecting, unauthorized, etc.)
        '''
        try:
            reply = QMessageBox.warning(self, 'ÔÜí FRP ADB', '­ƒÜ¿ ATEN├ç├âO: FRP Bypass via ADB\n\nEste m├®todo executa APENAS os comandos ADB finais.\n\n­ƒôï REQUISITOS ESSENCIAIS:\nÔÇó Dispositivo com USB Debugging ATIVO e AUTORIZADO\nÔÇó ADB instalado corretamente no sistema\nÔÇó TECH UNION instalado corretamente\nÔÇó Cabo USB original conectado\n\nÔÜÖ´©Å COMPATIBILIDADE:\nÔÇó Funciona com a maioria dos dispositivos Samsung\nÔÇó Alguns dispositivos podem n├úo ser compat├¡veis\nÔÇó Certifique-se que autorizou a depura├º├úo USB no dispositivo\n\n­ƒÆí DICA IMPORTANTE:\nSe o m├®todo falhar, tente os m├®todos FRP espec├¡ficos\npara sua vers├úo do Android (9-10 ou 11+).\n\n­ƒÜÇ Nossa equipe trabalha TODOS OS DIAS para melhorar\na compatibilidade e efici├¬ncia das ferramentas!\n\nÔÜá´©Å Use apenas em dispositivos pr├│prios ou autorizados!\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply != QMessageBox.Yes:
                self.advanced_log_message('ÔØî FRP ADB cancelado pelo usu├írio')
                return
            self.advanced_log_message('ÔÜí Iniciando FRP Bypass via ADB...')
            def _execute_adb_frp():
                return self.samsung_advanced.execute_adb_frp_bypass()
            def _on_adb_frp_finished(result):
                try:
                    if result['success']:
                        self.advanced_log_message('­ƒÄë FRP BYPASS ADB CONCLU├ìDO!')
                        self.advanced_log_message('Ô£à Comandos ADB executados com sucesso')
                        self.advanced_log_message('­ƒô▒ Dispositivo deve estar desbloqueado')
                        for cmd_result in result.get('adb_commands_executed', []):
                            status = 'Ô£à' if cmd_result['success'] else 'ÔØî'
                            self.advanced_log_message(f'{status} {cmd_result['description']}')
                        self.log('­ƒÄë FRP ADB executado com sucesso!')
                        return
                    self.advanced_log_message('ÔØî FRP ADB falhou - Verifique se o dispositivo est├í autorizado')
                    self.log('ÔØî FRP ADB falhou - Verifique autoriza├º├úo ADB')
                    return
                except Exception as e:
                    self.advanced_log_message('ÔØî Erro inesperado no FRP ADB')
            def _on_adb_frp_error(error):
                self.advanced_log_message('ÔØî Erro no FRP ADB - Verifique conex├úo USB')
                self.log('ÔØî Erro no FRP ADB - Verifique conex├úo USB')
            if self.command_thread and self.command_thread.isRunning():
                self.advanced_log_message('ÔÜá´©Å Comando j├í em execu├º├úo')
                return
            self.command_thread = CommandThread(_execute_adb_frp)
            self.command_thread.command_started.connect((lambda: self.advanced_log_message('­ƒöä Executando comandos ADB...')))
            self.command_thread.command_finished.connect((lambda result_str: self._safe_handle_frp_result(result_str, _on_adb_frp_finished)))
            self.command_thread.command_error.connect(_on_adb_frp_error)
            self.command_thread.start()
            return
        except Exception as e:
            self.advanced_log_message('ÔØî Erro ao executar FRP ADB - Verifique configura├º├úo')
    def execute_frp_adb_debug(self):
        '''FRP Debug via adb root + push zeros ÔÇö APENAS ROM eng/userdebug'''
        try:
            reply = QMessageBox.warning(self, 'ÔÜí FRP ADB Debug', 'ATENCAO: FRP Debug via ADB Root\n\nEste metodo funciona APENAS em ROM engineering ou userdebug.\nEm ROM de producao (user), o processo sera abortado automaticamente.\n\nREQUISITOS:\n- Dispositivo com ROM eng/userdebug\n- USB Debugging ativo e autorizado\n- Cabo USB original conectado\n\nO QUE SERA FEITO:\n1. adb root (elevar daemon)\n2. Localizar particao FRP\n3. Sobrescrever particao com zeros\n4. Reiniciar dispositivo\n\nUse apenas em dispositivos proprios ou autorizados!\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply != QMessageBox.Yes:
                self.advanced_log_message('[-] FRP ADB Debug cancelado pelo usuario')
                return
            self.advanced_log_message('[-] Iniciando FRP ADB Debug...')
            def _execute():
                return self.samsung_advanced.execute_adb_frp_debug_bypass()
            def _on_finished(result):
                try:
                    if result['success']:
                        self.advanced_log_message('[-] FRP DEBUG CONCLUIDO!')
                        self.advanced_log_message('[-] UNION fazendo a magica...')
                        self.advanced_log_message('[-] Dispositivo reiniciando ÔÇö FRP limpo.')
                        self.log('FRP ADB Debug concluido com sucesso')
                        return
                    erro = result.get('error', 'Erro desconhecido')
                    self.advanced_log_message(f'[-] Falha: {erro}')
                    self.log(f'FRP ADB Debug falhou: {erro}')
                    return
                except Exception:
                    self.advanced_log_message('[-] Erro ao processar resultado')
            def _on_error(error):
                self.advanced_log_message('[-] Erro no FRP ADB Debug - Verifique conexao USB')
                self.log('Erro no FRP ADB Debug')
            if self.command_thread and self.command_thread.isRunning():
                self.advanced_log_message('[-] Comando ja em execucao, aguarde.')
                return
            self.command_thread = CommandThread(_execute)
            self.command_thread.command_started.connect((lambda: self.advanced_log_message('[-] Executando FRP Debug...')))
            self.command_thread.command_finished.connect((lambda result_str: self._safe_handle_frp_result(result_str, _on_finished)))
            self.command_thread.command_error.connect(_on_error)
            self.command_thread.start()
            return
        except Exception as e:
            self.advanced_log_message('[-] Erro ao iniciar FRP ADB Debug')
    def execute_frp_recovery_union(self):
        '''FRP ADB Debug (UNION) ÔÇö metodo otimizado com forca de autorizacao + limpeza'''
        try:
            reply = QMessageBox.warning(self, 'ÔÜí FRP ADB Debug (UNION)', 'ATENCAO: FRP ADB Debug (UNION)\n\nMetodo UNION ÔÇö forca autorizacao e limpa FRP automaticamente.\nFunciona em dispositivos com ROM debug ou engineering.\n\nREQUISITOS:\n- Dispositivo com ROM debug ou engineering\n- USB Debugging ativo\n- Cabo USB original conectado\n\nO QUE SERA FEITO:\n1. Verificar e forcar conexao do dispositivo\n2. Elevar permissoes\n3. Localizar e limpar area protegida\n4. Reiniciar dispositivo\n\nUse apenas em dispositivos proprios ou autorizados!\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply != QMessageBox.Yes:
                self.advanced_log_message('[-] FRP ADB Debug (UNION) cancelado pelo usuario')
                return
            self.advanced_log_message('[-] Iniciando FRP ADB Debug (UNION)...')
            def log_callback(msg):
                self.advanced_log_message(msg)
            def _execute():
                return self.samsung_advanced.execute_frp_recovery_union(log_callback=log_callback)
            def _on_finished(result):
                try:
                    if result['success']:
                        self.log('FRP ADB Debug (UNION) concluido com sucesso')
                        return
                    erro = result.get('error', 'Erro desconhecido')
                    self.log(f'FRP ADB Debug (UNION) falhou: {erro}')
                    return
                except Exception:
                    return
            def _on_error(error):
                self.advanced_log_message('[-] Erro ÔÇö Verifique conexao USB e tente novamente')
                self.log('Erro no FRP ADB Debug (UNION)')
            if self.command_thread and self.command_thread.isRunning():
                self.advanced_log_message('[-] Comando ja em execucao, aguarde.')
                return
            self.command_thread = CommandThread(_execute)
            self.command_thread.command_started.connect((lambda: self.advanced_log_message('[-] Executando FRP ADB Debug (UNION)...')))
            self.command_thread.command_finished.connect((lambda result_str: self._safe_handle_frp_result(result_str, _on_finished)))
            self.command_thread.command_error.connect(_on_error)
            self.command_thread.start()
            return
        except Exception:
            self.advanced_log_message('[-] Erro ao iniciar. Tente novamente.')
    def perform_advanced_analysis(self):
        '''Executa an├ílise avan├ºada do dispositivo'''
        try:
            self.advanced_log_message('­ƒöì Iniciando an├ílise avan├ºada...')
            def _execute_analysis():
                result = {'success': False, 'data': {}}
                try:
                    self.advanced_log_message('­ƒôè Analisando portas Samsung...')
                    ports = self.samsung_advanced.find_samsung_ports()
                    if ports:
                        self.advanced_log_message(f'Ô£à {len(ports)} porta(s) Samsung encontrada(s):')
                        for port in ports:
                            self.advanced_log_message(f'  ­ƒôì {port['port']} - {port['type']} ({port['description']})')
                    else:
                        self.advanced_log_message('ÔØî Nenhuma porta Samsung encontrada')
                    self.advanced_log_message('­ƒöì Verificando status ADB...')
                    adb_active = self.samsung_advanced.check_adb_status()
                    if adb_active:
                        self.advanced_log_message('Ô£à ADB ativo e funcional')
                    else:
                        self.advanced_log_message('ÔØî ADB n├úo detectado ou inativo')
                except Exception as e:
                    self.advanced_log_message(f'ÔØî Erro na an├ílise: {str(e)}')
                    result['error'] = str(e)
                    return result
                try:
                    modem_ports = [p for p in ports if p['type'] in ('modem', 'modem_desc')]
                    if modem_ports:
                        self.advanced_log_message('­ƒô▒ Testando comando propriet├írio...')
                        info_result = self.samsung_advanced.execute_dvif_command()
                        if info_result['success']:
                            self.advanced_log_message('Ô£à Comando propriet├írio funcional - dispositivo compat├¡vel')
                            if 'model' in info_result['data']:
                                self.advanced_log_message(f'­ƒô▒ Modelo detectado: {info_result['data']['model']}')
                        else:
                            self.advanced_log_message('ÔÜá´©Å Comando propriet├írio n├úo respondeu - pode n├úo ser compat├¡vel')
                    self.advanced_log_message('Ô£à An├ílise avan├ºada conclu├¡da!')
                    result['success'] = True
                except Exception as e:
                    self.advanced_log_message(f'ÔØî Erro na an├ílise: {str(e)}')
                    result['error'] = str(e)
                return result
            def _on_analysis_error(error):
                self.advanced_log_message(f'ÔØî Erro ao executar an├ílise: {str(error)}')
            self.execute_command(_execute_analysis)
            return
        except Exception as e:
            self.advanced_log_message(f'ÔØî Erro ao executar an├ílise: {str(e)}')
    def show_frp_android_11_coming_soon(self):
        '''Mostra mensagem para FRP Android 11+'''
        QMessageBox.information(self, '­ƒÜº FRP Android 11+', '­ƒöÑ FUNCIONALIDADE EM DESENVOLVIMENTO!\n\n­ƒÜÇ Nossa equipe est├í trabalhando no m├®todo FRP para Android 11+:\n   ÔÇó Compatibilidade com One UI 3.0+\n   ÔÇó Bypass para dispositivos mais recentes\n   ÔÇó M├®todos adaptativos por vers├úo\n\nÔÜí RECURSOS PLANEJADOS:\n   ÔÇó Detec├º├úo autom├ítica da vers├úo Android\n   ÔÇó M├║ltiplos m├®todos de bypass\n   ÔÇó Suporte para Knox mais recente\n\n­ƒÄ» LAN├çAMENTO: Em breve!\n\n­ƒÆí Por enquanto, use o m├®todo Android 9-10 se compat├¡vel.')
        self.advanced_log_message('­ƒÜº FRP Android 11+ - Fun├º├úo em desenvolvimento')
    def show_qrcode_viewer(self):
        '''Abre o visualizador de QR Code'''
        try:
            self.advanced_log_message('­ƒô▓ Abrindo QR Code Generator [8-16]...')
            show_qrcode_viewer(self)
            self.advanced_log_message('Ô£à Visualizador de QR Code aberto com sucesso')
            return
        except Exception as e:
            error_msg = f'ÔØî Erro ao abrir QR Code Viewer: {str(e)}'
            self.advanced_log_message(error_msg)
            QMessageBox.critical(self, 'Erro', f'N├úo foi poss├¡vel abrir o visualizador de QR Code.\n\n{str(e)}')
            logger.error(f'[QRCodeViewer] {error_msg}')
            logger.error(traceback.format_exc())
    def show_frp_samsung_models(self):
        '''Abre a interface de FRP Samsung por modelo (EDL/BROM/MTP)'''
        try:
            self.advanced_log_message('­ƒöô Abrindo FRP Samsung Models...')
            from PyQt5.QtWidgets import QDialog, QVBoxLayout
            from PyQt5.QtGui import QIcon
            import os
            import sys
            union_unlock_path = os.path.join(os.path.dirname(__file__), 'union_unlock')
            if union_unlock_path not in sys.path:
                sys.path.insert(0, union_unlock_path)
            from samsung.samsung import SamsungWidget
            dialog = QDialog(self)
            dialog.setWindowTitle('FRP Samsung Models - TECH UNION')
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
            samsung_widget = SamsungWidget()
            layout.addWidget(samsung_widget)
            self._samsung_models_dialog = dialog
            dialog.show()
            self.advanced_log_message('Ô£à Interface FRP Samsung Models aberta!')
            return
        except Exception as e:
            error_msg = f'ÔØî Erro ao abrir FRP Samsung Models: {str(e)}'
            self.advanced_log_message(error_msg)
            logger.error(f'[FRPSamsungModels] {error_msg}')
            import traceback
            logger.error(traceback.format_exc())
            QMessageBox.critical(self, 'Erro', f'N├úo foi poss├¡vel abrir FRP Samsung Models.\n\n{str(e)}')
    def execute_frp_android_16(self):
        '''
        Executa FRP Bypass para Android 16
        Oferece duas op├º├Áes:
        1. DEFINITIVO - M├®todo validado completo (batch + exploit)
        2. BYPASS P/ HARDLOCKS - M├®todo alternativo (para casos espec├¡ficos)
        '''
        try:
            from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QDialogButtonBox)
            dialog = QDialog(self)
            dialog.setWindowTitle('FRP Android 16 - Selecione o Metodo')
            dialog.setMinimumWidth(450)
            dialog.setStyleSheet('\n                QDialog {\n                    background-color: #1a1a2e;\n                }\n                QLabel {\n                    color: #ffffff;\n                    font-size: 12px;\n                }\n                QPushButton {\n                    min-height: 50px;\n                    font-size: 13px;\n                    font-weight: bold;\n                    border-radius: 8px;\n                    padding: 10px 20px;\n                }\n            ')
            layout = QVBoxLayout(dialog)
            layout.setSpacing(15)
            layout.setContentsMargins(20, 20, 20, 20)
            title_label = QLabel('FRP ANDROID 16 - TECH UNION SOLUTIONS')
            title_label.setStyleSheet('font-size: 16px; font-weight: bold; color: #ff6b35;')
            title_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(title_label)
            desc_label = QLabel('Selecione o metodo mais adequado para seu dispositivo:')
            desc_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(desc_label)
            beta_label = QLabel('VERSAO BETA | Pode nao funcionar em todos os patchs de seguranca\nTestado e validado - Nossa equipe trabalha para voce!')
            beta_label.setStyleSheet('\n                QLabel {\n                    background-color: rgba(255, 193, 7, 0.2);\n                    border: 1px solid #ffc107;\n                    border-radius: 5px;\n                    padding: 8px;\n                    color: #ffc107;\n                    font-size: 11px;\n                    font-weight: bold;\n                }\n            ')
            beta_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(beta_label)
            btn_definitivo = QPushButton('DEFINITIVO\n(Metodo Validado - Taxa 95%)')
            btn_definitivo.setStyleSheet('\n                QPushButton {\n                    background-color: #28a745;\n                    color: white;\n                    border: 2px solid #1e7e34;\n                }\n                QPushButton:hover {\n                    background-color: #218838;\n                }\n            ')
            btn_definitivo.setToolTip('M├®todo completo validado em 14/12/2025\nÔÇó Usa exploits em batch (rajada)\nÔÇó Factory Reset autom├ítico\nÔÇó N├úo requer ADB ap├│s reset\nÔÇó Recomendado para maioria dos casos')
            layout.addWidget(btn_definitivo)
            btn_bypass = QPushButton('BYPASS P/ HARDLOCKS\n(Metodo Alternativo - Taxa 80%)')
            btn_bypass.setStyleSheet('\n                QPushButton {\n                    background-color: #fd7e14;\n                    color: white;\n                    border: 2px solid #e06b12;\n                }\n                QPushButton:hover {\n                    background-color: #e56a0c;\n                }\n            ')
            btn_bypass.setToolTip('M├®todo alternativo para casos espec├¡ficos\nÔÇó Para dispositivos com prote├º├úo adicional\nÔÇó Pode requerer m├║ltiplas tentativas\nÔÇó Use se o m├®todo definitivo falhar')
            layout.addWidget(btn_bypass)
            btn_cancel = QPushButton('Cancelar')
            btn_cancel.setStyleSheet('\n                QPushButton {\n                    background-color: #6c757d;\n                    color: white;\n                    min-height: 35px;\n                }\n                QPushButton:hover {\n                    background-color: #5a6268;\n                }\n            ')
            layout.addWidget(btn_cancel)
            info_label = QLabel('\nREQUISITOS OBRIGATORIOS:\n- Dispositivo LIGADO na tela do FRP\n- Cabo USB original conectado\n- Drivers Samsung instalados (Samsung USB Driver)\n- Conexao com internet estavel')
            info_label.setStyleSheet('font-size: 11px; color: #aaaaaa;')
            layout.addWidget(info_label)
            choice = {'method': None}
            def on_definitivo():
                choice['method'] = 'definitivo'
                dialog.accept()
            def on_bypass():
                choice['method'] = 'bypass'
                dialog.accept()
            def on_cancel():
                choice['method'] = None
                dialog.reject()
            btn_definitivo.clicked.connect(on_definitivo)
            btn_bypass.clicked.connect(on_bypass)
            btn_cancel.clicked.connect(on_cancel)
            result = dialog.exec_()
            if choice['method'] == 'definitivo':
                self._execute_frp_android_16_definitivo()
                return
            if choice['method'] == 'bypass':
                self._execute_frp_android_16_bypass()
                return
            self.advanced_log_message('ÔØî FRP Android 16 cancelado pelo usu├írio')
            return
        except Exception as e:
            self.advanced_log_message(f'ÔØî Erro ao executar FRP Android 16: {str(e)}')
    def _execute_frp_android_16_definitivo(self):
        '''
        Executa o M├ëTODO DEFINITIVO validado em 14/12/2025
        Este m├®todo:
        - Usa batch (rajada) para envio de comandos
        - Inclui exploit completo
        - Factory Reset autom├ítico
        - N├âO requer ADB ap├│s reset
        '''
        try:
            self.advanced_log_message('­ƒöÑ Iniciando M├ëTODO DEFINITIVO...')
            self.advanced_log_message('­ƒôï M├®todo validado TECH UNION SOLUTIONS')
            self.advanced_log_message('ÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöü')
            from app.utils.samsung_android16_frp import SamsungAndroid16FRP
            frp_handler = SamsungAndroid16FRP()
            def log_callback(msg):
                self.advanced_log_message(msg)
            frp_handler.set_log_callback(log_callback)
            def _execute_definitivo():
                return frp_handler.execute()
            def _on_definitivo_finished(result):
                try:
                    if result.get('success'):
                        self.advanced_log_message('')
                        self.advanced_log_message('Ô£à PROCESSO FINALIZADO!')
                        self.advanced_log_message('ÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöü')
                        self.advanced_log_message('­ƒô▒ O dispositivo vai reiniciar')
                        self.advanced_log_message('ÔÅ│ Aguarde o boot (~2-3 minutos)')
                        self.advanced_log_message('­ƒÆí N├úo funcionou? Tente novamente!')
                        self.log('Ô£à FRP Android 16 - Processo finalizado!')
                        QMessageBox.information(self, 'Ô£à PROCESSO FINALIZADO!', 'Ô£à PROCESSO FINALIZADO COM SUCESSO!\nÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöü\n\n­ƒô▒ O dispositivo est├í reiniciando...\n\nÔÅ│ Aguarde o boot completo (~2-3 minutos)\n\n­ƒÆí Configure normalmente ap├│s reiniciar!\n\nÔÜá´©Å N├úo funcionou? Tente novamente ou\n   use outro m├®todo.\n\n­ƒöÑ TECH UNION SOLUTIONS - Valeu, t├®cnico! ­ƒÆ¬')
                        return
                    error_msg = result.get('error', 'Erro desconhecido')
                    phase = result.get('phase', '')
                    self.advanced_log_message(f'ÔØî M├®todo Definitivo falhou: {error_msg}')
                    self.advanced_log_message(f'­ƒôï Fase: {phase}')
                    self.log('ÔØî FRP Android 16 - M├®todo Definitivo falhou')
                    reply = QMessageBox.question(self, 'ÔÜá´©Å M├®todo Definitivo Falhou', f'ÔØî O m├®todo definitivo n├úo funcionou\n\n­ƒôï Fase: {phase}\nÔÜá´©Å Erro: {error_msg}\n\nDeseja tentar o M├ëTODO BYPASS?\n(Para dispositivos com prote├º├úo adicional)', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                    if reply == QMessageBox.Yes:
                        self._execute_frp_android_16_bypass()
                        return
                except Exception as e:
                    self.advanced_log_message(f'ÔØî Erro inesperado: {str(e)}')
            def _on_definitivo_error(error):
                self.advanced_log_message(f'ÔØî Erro: {str(error)}')
                self.log('ÔØî FRP Android 16 - Erro no m├®todo definitivo')
            if self.command_thread and self.command_thread.isRunning():
                self.advanced_log_message('ÔÜá´©Å Aguarde o processo anterior...')
                return
            self.command_thread = CommandThread(_execute_definitivo)
            self.command_thread.command_started.connect((lambda: self.advanced_log_message('­ƒöä Executando exploits...')))
            self.command_thread.command_finished.connect((lambda result_str: self._safe_handle_frp_result(result_str, _on_definitivo_finished)))
            self.command_thread.command_error.connect(_on_definitivo_error)
            self.command_thread.start()
            return
        except ImportError as e:
            self.advanced_log_message(f'ÔØî M├│dulo n├úo encontrado: {e}')
            self.advanced_log_message('­ƒÆí Verifique a instala├º├úo do sistema')
        except Exception as e:
            self.advanced_log_message(f'ÔØî Erro ao executar m├®todo definitivo: {str(e)}')
    def _execute_frp_android_16_bypass(self):
        '''
        Executa o M├ëTODO BYPASS para Hardlocks
        Este ├® o m├®todo alternativo para dispositivos com prote├º├úo adicional
        Usa a implementa├º├úo existente em samsung_advanced.py
        '''
        try:
            self.advanced_log_message('ÔÜí Iniciando M├ëTODO BYPASS...')
            self.advanced_log_message('­ƒôï Para dispositivos com prote├º├úo adicional')
            self.advanced_log_message('ÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöü')
            def log_callback(msg):
                self.advanced_log_message(msg)
            def _execute_bypass():
                return self.samsung_advanced.execute_frp_android_16(log_callback=log_callback)
            def _on_bypass_finished(result):
                try:
                    if result.get('success'):
                        self.advanced_log_message('­ƒÄë BYPASS CONCLU├ìDO COM SUCESSO!')
                        self.log('­ƒÄë FRP Android 16 - Bypass conclu├¡do!')
                        QMessageBox.information(self, 'Ô£à Sucesso', '­ƒÄë FRP BYPASS CONCLU├ìDO!\n\nO dispositivo foi desbloqueado.\n\n­ƒô▒ Configure o dispositivo normalmente.')
                        return
                    if result.get('requires_factory_reset'):
                        self.advanced_log_message('ÔÜá´©Å Requer Factory Reset adicional')
                        reply = QMessageBox.question(self, '­ƒöä Factory Reset Necess├írio', 'ÔÜá´©Å O BYPASS requer formata├º├úo adicional\n\nEste processo ir├í:\n   1. FORMATAR o dispositivo\n   2. Reiniciar automaticamente\n   3. FRP ser├í removido ap├│s boot\n\nÔÜá´©Å ATEN├ç├âO: Dados ser├úo apagados!\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                        if reply == QMessageBox.Yes:
                            self._execute_frp_android_16_method2()
                            return
                        return
                    error_msg = result.get('error', 'Erro desconhecido')
                    self.advanced_log_message(f'ÔØî Bypass falhou: {error_msg}')
                    self.log('ÔØî FRP Android 16 - Bypass falhou')
                    return
                except Exception as e:
                    self.advanced_log_message(f'ÔØî Erro inesperado: {str(e)}')
            def _on_bypass_error(error):
                self.advanced_log_message(f'ÔØî Erro no bypass: {str(error)}')
                self.log('ÔØî FRP Android 16 - Erro no bypass')
            if self.command_thread and self.command_thread.isRunning():
                self.advanced_log_message('ÔÜá´©Å Aguarde o processo anterior...')
                return
            self.command_thread = CommandThread(_execute_bypass)
            self.command_thread.command_started.connect((lambda: self.advanced_log_message('­ƒöä Processando bypass...')))
            self.command_thread.command_finished.connect((lambda result_str: self._safe_handle_frp_result(result_str, _on_bypass_finished)))
            self.command_thread.command_error.connect(_on_bypass_error)
            self.command_thread.start()
            return
        except Exception as e:
            self.advanced_log_message(f'ÔØî Erro ao executar bypass: {str(e)}')
    def _execute_frp_android_16_method2(self):
        '''Executa M├®todo 2 do FRP Android 16 (Factory Reset + reconex├úo)'''
        try:
            self.advanced_log_message('­ƒöä Preparando formata├º├úo...')
            def log_callback(msg):
                self.advanced_log_message(msg)
            def _execute_method2():
                return self.samsung_advanced.execute_frp_android_16_method2(log_callback=log_callback)
            def _on_method2_finished(result):
                if result.get('requires_reconnection'):
                    self.advanced_log_message('­ƒöä Dispositivo formatado - aguardando rein├¡cio...')
                    reply = QMessageBox.information(self, '­ƒöî Reconex├úo Necess├íria', '­ƒöä DISPOSITIVO FORMATADO\nÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöü\n\n­ƒô▒ O dispositivo est├í reiniciando...\n\n­ƒôï PROCEDIMENTO:\n   1. Aguarde o dispositivo ligar completamente\n   2. Entre novamente em normal mode\n   3. Reconecte o cabo USB\n   4. Clique OK quando estiver pronto\n\nÔÅ│ Aguarde pelo menos 60 segundos...', QMessageBox.Ok)
                    reply2 = QMessageBox.question(self, '­ƒöä Continuar Processo', 'O dispositivo est├í conectado e em modo Download?\n\nClique SIM para continuar o processo FRP.', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                    if reply2 == QMessageBox.Yes:
                        self.advanced_log_message('­ƒöä Continuando processo ap├│s reconex├úo...')
                        self.execute_frp_android_16()
                        return
                    self.advanced_log_message('ÔØî Processo cancelado pelo usu├írio')
                    return
                self.advanced_log_message(f'ÔØî Erro: {result.get('error', 'Falha desconhecida')}')
            def _on_method2_error(error):
                self.advanced_log_message(f'ÔØî Erro no M├®todo 2: {str(error)}')
            if self.command_thread and self.command_thread.isRunning():
                self.advanced_log_message('ÔÜá´©Å Aguarde o processo anterior...')
                return
            self.command_thread = CommandThread(_execute_method2)
            self.command_thread.command_finished.connect((lambda result_str: self._safe_handle_frp_result(result_str, _on_method2_finished)))
            self.command_thread.command_error.connect(_on_method2_error)
            self.command_thread.start()
            return
        except Exception as e:
            self.advanced_log_message(f'ÔØî Erro no M├®todo 2: {str(e)}')
    def execute_frp_work_id_android_14(self):
        '''
        Executa servi├ºo premium FRP WORK ID ANDROID 14.
        Servi├ºo remoto por ID/IMEI - Requer cr├®ditos
        Busca por ID 2 no banco (t├¡tulo din├ómico)
        '''
        try:
            from app.utils.premium_services_manager import get_premium_services_manager
            user_id = 1
            if hasattr(self.parent, 'user_id'):
                user_id = self.parent.user_id
            premium_manager = get_premium_services_manager()
            servico = premium_manager.buscar_servico_premium_por_id(2)
            if servico:
                titulo_servico = servico.get('titulo', 'FRP HARD LOCK')
            else:
                titulo_servico = 'FRP HARD LOCK'
            sucesso = premium_manager.abrir_servico_premium(titulo=titulo_servico, user_id=user_id, parent=self)
            if sucesso:
                self.advanced_log_message('Ô£à Servi├ºo FRP WORK ID ANDROID 14 acessado')
                self.log('­ƒîÉ Servi├ºo premium aberto no navegador')
                return
            self.advanced_log_message('ÔÜá´©Å Acesso ao servi├ºo FRP WORK ID cancelado ou indispon├¡vel')
            return
        except Exception as e:
            self.advanced_log_message('ÔÜá´©Å Erro ao acessar servi├ºo premium')
            self.log('ÔÜá´©Å Servi├ºo temporariamente indispon├¡vel')
            QMessageBox.warning(self, 'Servi├ºo Indispon├¡vel', 'O servi├ºo est├í temporariamente indispon├¡vel.\n\nPor favor, tente novamente mais tarde.\n\n­ƒô× Suporte: (85) 99750-7465')
    def advanced_detect_and_connect(self):
        '''Detecta e conecta Samsung - IGUAL AO VALIDADOR QUE FUNCIONOU'''
        try:
            self.advanced_log_message('­ƒöì Detectando dispositivos Samsung...')
            self.advanced_status.setText('Detectando...')
            self.advanced_status.setStyleSheet('\n                font-weight: bold;\n                font-size: 11px;\n                color: #856404;\n                padding: 5px;\n                background-color: #fff3cd;\n                border-radius: 4px;\n                border: 1px solid #ffeaa7;\n            ')
            def _detect_and_connect():
                result = {'success': False, 'port': None, 'error': ''}
                try:
                    ports = self.samsung_advanced.find_samsung_ports()
                    if not ports:
                        result['error'] = 'Nenhuma porta Samsung encontrada'
                        return result
                    best_port = ports[0]['port']
                    self.advanced_log_message(f'­ƒô▒ Tentando conectar: {best_port}')
                    if self.samsung_advanced.connect_to_port(best_port):
                        if self.samsung_advanced.test_at_communication():
                            result['success'] = True
                            result['port'] = best_port
                            self.advanced_log_message(f'Ô£à Conectado com sucesso: {best_port}')
                            return result
                        result['error'] = f'Falha na comunica├º├úo AT com {best_port}'
                        return result
                except Exception as e:
                    result['error'] = f'Erro na detec├º├úo: {str(e)}'
                    return result
                try:
                    result['error'] = f'Falha na conex├úo com {best_port}'
                except Exception as e:
                    result['error'] = f'Erro na detec├º├úo: {str(e)}'
                return result
            def _on_connect_finished(result):
                try:
                    if result['success']:
                        self.advanced_status.setText(f'Conectado: {result['port']}')
                        self.advanced_status.setStyleSheet('\n                            font-weight: bold;\n                            font-size: 11px;\n                            color: #155724;\n                            padding: 5px;\n                            background-color: #d4edda;\n                            border-radius: 4px;\n                            border: 1px solid #c3e6cb;\n                        ')
                        for btn in self.advanced_function_buttons:
                            btn.setEnabled(True)
                        self.advanced_log_message('­ƒÄë Conex├úo Advanced estabelecida!')
                        self.advanced_log_message('Ô£à Bot├Áes FRP habilitados')
                        self.advanced_connect_btn.setText('Desconectar')
                        self.advanced_connect_btn.setStyleSheet('\n                            QPushButton {\n                                background-color: #dc3545;\n                                color: white;\n                                border: none;\n                                padding: 8px 16px;\n                                border-radius: 6px;\n                                font-weight: bold;\n                                font-size: 11px;\n                            }\n                            QPushButton:hover {\n                                background-color: #c82333;\n                            }\n                            QPushButton:pressed {\n                                background-color: #bd2130;\n                            }\n                        ')
                        self.advanced_connect_btn.clicked.disconnect()
                        self.advanced_connect_btn.clicked.connect(self.advanced_disconnect)
                        return
                    self.advanced_status.setText(f'Falha: {result['error']}')
                    self.advanced_status.setStyleSheet('\n                            font-weight: bold;\n                            font-size: 11px;\n                            color: #721c24;\n                            padding: 5px;\n                            background-color: #f8d7da;\n                            border-radius: 4px;\n                            border: 1px solid #f5c6cb;\n                        ')
                    self.advanced_log_message(f'ÔØî Falha na conex├úo: {result['error']}')
                    return
                except Exception as e:
                    self.advanced_log_message(f'ÔØî Erro no callback: {str(e)}')
            def _on_connect_error(error):
                self.advanced_status.setText('Erro na deteccao')
                self.advanced_log_message(f'ÔØî Erro na detec├º├úo: {str(error)}')
            if self.command_thread and self.command_thread.isRunning():
                self.advanced_log_message('ÔÜá´©Å Comando j├í em execu├º├úo')
                return
            self.command_thread = CommandThread(_detect_and_connect)
            self.command_thread.command_started.connect((lambda: self.advanced_log_message('­ƒöä Iniciando detec├º├úo...')))
            self.command_thread.command_finished.connect((lambda result_str: self._safe_handle_connect_result(result_str, _on_connect_finished)))
            self.command_thread.command_error.connect(_on_connect_error)
            self.command_thread.start()
            return
        except Exception as e:
            self.advanced_log_message(f'ÔØî Erro ao detectar Samsung: {str(e)}')
    def advanced_disconnect(self):
        '''Desconecta Samsung Advanced'''
        try:
            self.advanced_log_message('­ƒöî Desconectando...')
            if self.samsung_advanced.serial_port and self.samsung_advanced.serial_port.is_open:
                self.samsung_advanced.serial_port.close()
            self.advanced_status.setText('Desconectado')
            self.advanced_status.setStyleSheet('\n                font-weight: bold;\n                font-size: 11px;\n                color: #dc3545;\n                padding: 5px;\n                background-color: #f8d7da;\n                border-radius: 4px;\n                border: 1px solid #f5c6cb;\n            ')
            for btn in self.advanced_function_buttons:
                btn.setEnabled(False)
            self.advanced_connect_btn.setText('Detectar e Conectar Samsung')
            self.advanced_connect_btn.setStyleSheet('\n                QPushButton {\n                    background-color: #28a745;\n                    color: white;\n                    border: none;\n                    padding: 8px 16px;\n                    border-radius: 6px;\n                    font-weight: bold;\n                    font-size: 11px;\n                }\n                QPushButton:hover {\n                    background-color: #218838;\n                }\n                QPushButton:pressed {\n                    background-color: #1e7e34;\n                }\n            ')
            self.advanced_connect_btn.clicked.disconnect()
            self.advanced_connect_btn.clicked.connect(self.advanced_detect_and_connect)
            self.advanced_log_message('Ô£à Desconectado com sucesso')
            return
        except Exception as e:
            self.advanced_log_message(f'ÔØî Erro ao desconectar: {str(e)}')
    def _safe_handle_connect_result(self, result_str: str, callback_func):
        '''Trata resultado de conex├úo de forma segura - EVITA CRASHES'''
        try:
            if isinstance(result_str, str):
                clean_str = result_str.strip()
                if clean_str.startswith('{') and clean_str.endswith('}'):
                    result = eval(clean_str)
                else:
                    result = {'success': False, 'error': f'Resultado inv├ílido: {clean_str[:100]}'}
            else:
                result = result_str
            callback_func(result)
            return
        except Exception as e:
            self.advanced_log_message(f'ÔØî Erro processando resultado de conex├úo: {str(e)}')
            error_result = {'success': False, 'error': f'Erro no callback: {str(e)}'}
            callback_func(error_result)
    def _safe_handle_frp_result(self, result_str: str, callback_func):
        '''Trata resultado de FRP de forma segura - EVITA CRASHES'''
        try:
            if isinstance(result_str, str):
                clean_str = result_str.strip()
                if clean_str.startswith('{') and clean_str.endswith('}'):
                    result = eval(clean_str)
                else:
                    result = {'success': False, 'error': f'Resultado inv├ílido: {clean_str[:100]}'}
            else:
                result = result_str
            callback_func(result)
            return
        except Exception as e:
            self.advanced_log_message(f'ÔØî Erro processando resultado de FRP: {str(e)}')
            error_result = {'success': False, 'error': f'Erro no callback: {str(e)}'}
            callback_func(error_result)
    def _safe_handle_dvif_result(self, result_str: str, callback_func):
        '''Trata resultado de DVIF de forma segura - EVITA CRASHES'''
        try:
            if isinstance(result_str, str):
                clean_str = result_str.strip()
                if clean_str.startswith('{') and clean_str.endswith('}'):
                    result = eval(clean_str)
                else:
                    result = {'success': False, 'error': f'Resultado inv├ílido: {clean_str[:100]}'}
            else:
                result = result_str
            callback_func(result)
            return
        except Exception as e:
            self.advanced_log_message(f'ÔØî Erro processando resultado de DVIF: {str(e)}')
            error_result = {'success': False, 'error': f'Erro no callback: {str(e)}'}
            callback_func(error_result)
    def _diagnosticar_adb_speed_clean(self):
        """Classifica o estado do ADB antes de iniciar Speed Clean.
CORRECAO CIRURGICA 25-05-2026: substituiu o guard fraco que so testava
`if not self.adb_manager`. Agora usa get_device_states_detailed() (ja
existente em app/utils/adb_manager.py) para diferenciar 4 cenarios e
permitir mensagens especificas para o usuario, reduzindo chamadas de
suporte. Em caso de falha total, faz fallback para is_device_connected()
garantindo que o caminho feliz nao seja impactado.
Retorna tupla (codigo: str, mensagem_html: str). Codigos:
    'ok'           -> device autorizado e operacional, pode prosseguir
    'sem_manager'  -> objeto adb_manager nao disponivel
    'sem_device'   -> nenhum device USB detectado
    'unauthorized' -> device conectado mas usuario nao autorizou
    'offline'      -> device em estado offline (driver/cabo)
    'desconhecido' -> estado retornado nao mapeado (recovery, sideload, etc.)
"""
        if not self.adb_manager:
            return ('sem_manager', '<div style="text-align: center;"><h3>ÔØî ADB indisponivel</h3><br><p>O modulo ADB nao esta disponivel neste sistema.</p><p>Reinicie o aplicativo ou contate o suporte.</p></div>')
        estados = []
        try:
            estados = self.adb_manager.get_device_states_detailed() or []
        except Exception:
            estados = []
        if estados:
            states_norm = [str(d.get('state', '')).strip().lower() for d in estados]
            if 'device' in states_norm:
                return ('ok', '')
            if 'unauthorized' in states_norm:
                return ('unauthorized', '<div style="text-align: center;"><h3>­ƒöÉ Autorize a depuracao USB no celular</h3><br><p>O dispositivo foi detectado, mas <b>aguarda autorizacao</b>.</p><br><p><b>No celular Samsung:</b></p><p>1. Olhe a tela do aparelho</p><p>2. Aparece um popup <b>"Permitir depuracao USB?"</b></p><p>3. Marque <b>"Sempre permitir deste computador"</b></p><p>4. Toque em <b>"Permitir"</b></p><br><p>Depois clique novamente em Speed Clean.</p></div>')
            if 'offline' in states_norm or 'no permissions' in states_norm:
                return ('offline', '<div style="text-align: center;"><h3>ÔÜá´©Å Dispositivo offline</h3><br><p>O ADB detectou o celular mas a conexao esta instavel.</p><br><p><b>Tente:</b></p><p>ÔÇó Desconectar e reconectar o cabo USB</p><p>ÔÇó Trocar de porta USB no PC</p><p>ÔÇó Trocar o cabo USB (alguns sao apenas de carga)</p><p>ÔÇó Reinstalar drivers ADB Samsung no PC</p></div>')
            return 'desconhecido', f'<div style="text-align: center;"><h3>ÔÜá´©Å Estado nao suportado</h3><br><p>Estado(s) detectado(s): <b>{', '.join(states_norm)}</b></p><br><p>Coloque o celular em modo normal (nao recovery/fastboot)</p><p>e tente novamente.</p></div>'
        device_ok = False
        try:
            device_ok = bool(self.adb_manager.is_device_connected())
        except Exception:
            device_ok = False
        if device_ok:
            return ('ok', '')
        return ('sem_device', '<div style="text-align: center;"><h3>­ƒô▒ Conecte um Android via USB</h3><br><p>Esta funcao usa <b>ADB</b> (nao a porta COM serial).</p><br><p><b>Verifique no celular:</b></p><p>ÔÇó Cabo USB conectado e funcional</p><p>ÔÇó <b>USB Debugging</b> habilitado em Opcoes de Desenvolvedor</p><p>ÔÇó Drivers ADB Samsung instalados no PC</p></div>')
    def remove_bloatware(self):
        '''Remove bloatware Samsung/Operadoras via ADB.
        CORRECAO CIRURGICA 25-05-2026: agora valida ADB com diagnostico
        detalhado (sem_device, unauthorized, offline) usando o helper
        _diagnosticar_adb_speed_clean. Antes, validava apenas existencia
        do objeto adb_manager e tentava remover 30 pacotes mesmo sem
        device, gerando ~150s de UI travada ("Nao respondendo").
        '''
        codigo, mensagem_html = self._diagnosticar_adb_speed_clean()
        if codigo != 'ok':
            QMessageBox.warning(self, 'Speed Clean ÔÇö Conexao ADB', mensagem_html)
            return
        reply = QMessageBox.question(self, 'Limpar Apps Desnecess├írios', '<div style="text-align: center;"><h3>­ƒº╣ LIMPAR APPS DESNECESS├üRIOS</h3><br><p>Esta opera├º├úo remover├í aplicativos pr├®-instalados que voc├¬ n├úo usa:</p><br><p><b>ÔÇó Samsung:</b> Bixby, Samsung Free, Game Tools, etc.</p><p><b>ÔÇó Facebook:</b> Apps pr├®-instalados</p><p><b>ÔÇó Microsoft:</b> Office (alguns modelos)</p><p><b>ÔÇó Google:</b> Apps opcionais (Duo, Play Movies, etc.)</p><p><b>ÔÇó Operadoras BR:</b> Claro, Vivo, TIM, Oi</p><br><p>­ƒôï <b>IMPORTANTE:</b></p><p>ÔÇó Apps ser├úo desinstalados apenas para o usu├írio atual</p><p>ÔÇó Podem ser restaurados com factory reset</p><p>ÔÇó Processo seguro e revers├¡vel</p><p>ÔÇó Ô£à Libera espa├ºo e deixa o celular mais r├ípido</p><br><p>Deseja continuar?</p></div>', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.log('­ƒº╣ Iniciando limpeza de apps desnecess├írios...')
            progress = QProgressDialog('Preparando limpeza...', 'Cancelar', 0, 100, self)
            progress.setWindowTitle('Limpando Apps Desnecess├írios')
            progress.setWindowModality(Qt.WindowModal)
            progress.setAutoClose(True)
            progress.setMinimumDuration(0)
            progress.show()
            self._current_progress_dialog = progress
            _emit_state = {'value': -1, 'label': '', 'ts': 0.0}
            _RATE_LIMIT_S = 0.1
            def _remove_bloatware():
                '''Executa remocao com feedback via signals cross-thread.
                IMPORTANTE: este escopo roda na CommandThread (QThread).
                NAO chamar metodos de QProgressDialog diretamente ÔÇö emitir
                os signals self._progress_*_request (auto-marshall para
                main thread via Qt.QueuedConnection).
                '''
                def update_progress(current, total, package):
                    '''Callback executado na QThread ÔÇö apenas emite signals.'''
                    try:
                        if total and total > 0:
                            v = int(current / total * 100)
                            if v < 0:
                                v = 0
                            elif v > 100:
                                v = 100
                        else:
                            v = 0
                        package_name = package.split('.')[-1] if '.' in package else package
                        label_text = f'Processando: {package_name}'
                        now = time.monotonic()
                        if v != _emit_state['value']:
                            if v >= 100 or now - _emit_state['ts'] >= _RATE_LIMIT_S:
                                self._progress_value_request.emit(v)
                                _emit_state['value'] = v
                                _emit_state['ts'] = now
                        if package_name != _emit_state['label']:
                            self._progress_label_request.emit(label_text)
                            _emit_state['label'] = package_name
                            return
                    except Exception:
                        pass
                results = self.samsung_manager.remove_bloatware(update_progress)
                try:
                    if _emit_state['value'] != 100:
                        self._progress_value_request.emit(100)
                except Exception:
                    pass
                try:
                    self._progress_close_request.emit()
                except Exception:
                    pass
                summary = 'Ô£à LIMPEZA CONCLU├ìDA!\n\n'
                summary += '­ƒôè Estat├¡sticas:\n'
                summary += f'  Ô£à Removidos: {len(results['success'])}\n'
                summary += f'  ÔØî Falharam: {len(results['failed'])}\n'
                summary += f'  Ôèÿ N├úo encontrados: {len(results['not_found'])}\n\n'
                if len(results['success']) > 0:
                    summary += '­ƒÄë Celular mais limpo e r├ípido!'
                    return summary
                if len(results['not_found']) == len(results['success']) + len(results['failed']) + len(results['not_found']):
                    summary += 'Ôä╣´©Å Celular j├í est├í limpo (apps n├úo encontrados)'
                    return summary
                summary += 'ÔÜá´©Å Alguns apps n├úo puderam ser removidos'
                return summary
            self.execute_command(_remove_bloatware)
    def test_communication(self):
        '''Testa comunica├º├úo com o dispositivo'''
        self.log('­ƒº¬ Testando comunica├º├úo com o dispositivo...')
        def _test_communication():
            results = self.samsung_manager.test_at_commands()
            output = 'Ô£à Resultados dos testes de comunica├º├úo:\n\n'
            for desc, response in results.items():
                if len(response) > 50:
                    response = response[:50] + '...'
                output += f'{desc}: {response}\n'
            return output
        self.execute_command(_test_communication)
    def show_development_message(self):
        '''Mostra mensagem de fun├º├úo em desenvolvimento'''
        QMessageBox.information(self, '­ƒöº Fun├º├úo em Desenvolvimento', "<div style='text-align: center;'><h3>ÔÜá´©Å FUN├ç├âO EM DESENVOLVIMENTO ÔÜá´©Å</h3><p><b>A equipe do TECH UNION SOLUTIONS est├í trabalhando</b></p><p><b>com m├íximo cuidado e precis├úo cir├║rgica no</b></p><p><b>desenvolvimento desta funcionalidade.</b></p><br><p>­ƒö¼ <i>Nossos t├®cnicos e desenvolvedores est├úo realizando testes rigorosos</i></p><p>­ƒøí´©Å <i>para garantir total seguran├ºa e estabilidade</i></p><p>ÔÜí <i>antes de disponibilizar para uso em produ├º├úo.</i></p><br><p><b>­ƒÜÇ Em breve esta ferramenta estar├í dispon├¡vel!</b></p><p><font color='#2196F3'><b>Obrigado pela sua paci├¬ncia e confian├ºa.</b></font></p></div>")
    def _show_welcome_message(self):
        '''Exibe mensagem de boas-vindas com termo de responsabilidade'''
        welcome_msg = '\n===============================================================================\n  TECH UNION SOLUTIONS - Tools Samsung\n  Ferramentas Profissionais para Tecnicos\n===============================================================================\n\nBem-vindo ao modulo de ferramentas Samsung.\nSelecione uma aba acima para acessar os recursos disponiveis.\n\n  IMPORTANTE:\n\n   - Este sistema foi desenvolvido para profissionais e estudos tecnicos.\n   - Recomendamos conhecimento previo antes de executar qualquer procedimento.\n   - Sempre faca backup dos dados antes de qualquer intervencao.\n\n  Sobre Desbloqueios e Remocao de Protecoes:\n\n   - Utilize apenas em dispositivos de sua propriedade legitima.\n   - Para fins de estudo, testes e aprendizado tecnico.\n   - Respeite sempre a propriedade e privacidade de terceiros.\n\n  Responsabilidades:\n\n   - Voce e responsavel pelo uso correto das ferramentas.\n   - A TECH UNION disponibiliza as ferramentas para fins profissionais.\n   - Use seu conhecimento tecnico com etica e responsabilidade.\n   - Em caso de duvidas, consulte nossa equipe de suporte.\n\n===============================================================================\n  Conecte seu dispositivo e selecione a operacao desejada.\n===============================================================================\n\n'
        self.standard_log_message(welcome_msg)
