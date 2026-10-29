from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QFrame, QMessageBox, QScrollArea, QGridLayout, QSplitter, QGroupBox, QTabWidget)
from PyQt5.QtCore import (Qt, QTimer, QThread, pyqtSignal, QElapsedTimer, QUrl)
from PyQt5.QtGui import (QFont, QIcon, QDesktopServices)
from app.utils.xiaomi_manager import XiaomiManager
from app.utils.adb_manager import ADBManager
import logging
import time
import os
import sys
import threading
import platform
from datetime import datetime, timedelta
import subprocess
logger = logging.getLogger(__name__)
class DeviceInfoThread(QThread):
    '''Thread separada para atualizar informa├º├Áes do dispositivo'''
    info_updated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    finished = pyqtSignal()
    def __init__(self, xiaomi_manager):
        super().__init__()
        self.xiaomi_manager = xiaomi_manager
        self.running = True
        self.timeout = 15
        self.logger = logging.getLogger(__name__)
    def run(self):
        start_time = time.time()
        result = {'connected': False, 'mode': 'none'}
        try:
            adb_connected = False
            try:
                adb_connected = self.xiaomi_manager.adb.is_device_connected()
            except Exception:
                pass
            else:
                if adb_connected:
                    result['connected'] = True
                    result['mode'] = 'adb'
                    is_xiaomi = self.xiaomi_manager.is_xiaomi_device()
                    result['is_xiaomi'] = is_xiaomi
                    if is_xiaomi:
                        result['miui_version'] = self.xiaomi_manager.get_miui_version()
                        result['battery'] = self.xiaomi_manager.get_battery_level()
        except Exception as e:
            self.logger.error(f'Erro ao obter informa├º├Áes do dispositivo: {str(e)}')
            result['error'] = str(e)
            self.info_updated.emit(result)
        try:
            fastboot_connected = False
            try:
                fastboot_connected = self.xiaomi_manager.is_fastboot_connected()
            except Exception:
                pass
            else:
                if fastboot_connected:
                    result['connected'] = True
                    result['mode'] = 'fastboot'
                    result['is_xiaomi'] = True
                    fb_info = self.xiaomi_manager.get_fastboot_device_info()
                    result['fastboot_vars'] = fb_info
                    result['fb_product'] = fb_info.get('product', fb_info.get('variant', ''))
                    result['fb_serial'] = fb_info.get('serialno', '')
                    result['fb_unlocked'] = fb_info.get('unlocked', '')
                    result['fb_anti'] = fb_info.get('anti', '')
                    result['fb_secure'] = fb_info.get('secure', '')
                    self.info_updated.emit(result)
                    elapsed = time.time() - start_time
                    self.logger.debug(f'Verifica├º├úo de dispositivo conclu├¡da em {elapsed:.2f}s')
                    return
                self.info_updated.emit(result)
        except Exception as e:
            self.logger.error(f'Erro ao obter informa├º├Áes do dispositivo: {str(e)}')
            result['error'] = str(e)
            self.info_updated.emit(result)
        elapsed = time.time() - start_time
        self.logger.debug(f'Verifica├º├úo de dispositivo conclu├¡da em {elapsed:.2f}s')
class CommandThread(QThread):
    '''Thread separada para executar comandos'''
    command_finished = pyqtSignal(bool, str)
    command_started = pyqtSignal()
    command_error = pyqtSignal(str)
    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.running = True
        self._timer = QElapsedTimer()
        self.logger = logging.getLogger(__name__)
    def run(self):
        try:
            self._timer.start()
            self.command_started.emit()
            result = self.function(*self.args, **self.kwargs)
            if self.running:
                execution_time = self._timer.elapsed() / 1000.0
                self.logger.debug(f'Comando {self.function.__name__} finalizado em {execution_time:.2f}s')
                self.command_finished.emit(True, result if isinstance(result, str) else 'Opera├º├úo conclu├¡da com sucesso')
                return
        except Exception as e:
            if self.running:
                self.logger.error(f'Erro no comando {self.function.__name__}: {str(e)}')
                self.command_finished.emit(False, str(e))
    def stop(self):
        '''Para a thread mesmo se estiver em execu├º├úo'''
        self.running = False
class XiaomiTools(QWidget):
    def __init__(self, parent=None, adb_manager=None):
        super().__init__(parent)
        self.parent = parent
        self.logger = logging.getLogger(__name__)
        self._checking_device = False
        self._refreshing_connection = False
        self.verification_count = 0
        self.adb_manager = adb_manager or ADBManager()
        self.xiaomi_manager = XiaomiManager(adb_manager=self.adb_manager)
        self.app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assets_dir = os.path.join(self.app_dir, 'assets')
        self.icons_dir = os.path.join(self.assets_dir, 'icons')
        self.setup_styles()
        self.setup_ui()
        self.last_check_time = time.time()
        self.check_count = 0
        self.max_checks = 3
        self.check_interval = 300
        self.device_info_cache = {}
        self.cache_valid_until = None
        self.cache_ttl = 300
        self.active_threads = []
        self.current_info_thread = None
        self.command_thread = None
        self.device_timer = QElapsedTimer()
        self.device_timer.start()
    def setup_styles(self):
        '''Define os estilos da interface'''
        self.button_style = '\n            QPushButton {\n                padding: 6px 10px;\n                font-size: 8pt;\n                min-height: 32px;\n                background-color: #2196F3;\n                color: white;\n                border-radius: 6px;\n                font-weight: 600;\n                border: none;\n                text-align: left;\n                padding-left: 12px;\n            }\n            QPushButton:hover {\n                background-color: #0D47A1;\n            }\n            QPushButton:pressed {\n                background-color: #1428A0;\n            }\n            QPushButton:disabled {\n                background-color: #bdc3c7;\n                color: #7f8c8d;\n            }\n        '
        self.warning_button_style = '\n            QPushButton {\n                padding: 6px 10px;\n                font-size: 8pt;\n                min-height: 32px;\n                background-color: #c0392b;\n                color: white;\n                border-radius: 6px;\n                font-weight: 600;\n                border: none;\n                text-align: left;\n                padding-left: 12px;\n            }\n            QPushButton:hover {\n                background-color: #e74c3c;\n            }\n            QPushButton:pressed {\n                background-color: #922b21;\n            }\n            QPushButton:disabled {\n                background-color: #bdc3c7;\n                color: #7f8c8d;\n            }\n        '
        self.placeholder_style = '\n            QLabel {\n                color: #7f8c8d;\n                font-size: 7pt;\n                padding-left: 5px;\n            }\n        '
    def setup_ui(self):
        '''Configura a interface do usu├írio'''
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet('\n            QTabWidget::pane {\n                border: 1px solid #e0e0e0;\n                background: #ffffff;\n                border-radius: 4px;\n            }\n            QTabWidget::tab-bar {\n                alignment: left;\n            }\n            QTabBar::tab {\n                background: #FF6900;\n                border: 1px solid #E55A00;\n                padding: 5px 12px;\n                margin-right: 2px;\n                border-top-left-radius: 4px;\n                border-top-right-radius: 4px;\n                font-weight: bold;\n                min-width: 50px;\n                font-size: 8pt;\n                color: rgba(255,255,255,0.8);\n            }\n            QTabBar::tab:selected {\n                background: #E55A00;\n                border-color: #CC4E00;\n                color: white;\n            }\n            QTabBar::tab:hover {\n                background: #E55A00;\n                color: white;\n            }\n        ')
        standard_tab = QWidget()
        self._setup_standard_tab(standard_tab)
        self.tab_widget.addTab(standard_tab, 'Tools')
        try:
            from app.views.union_unlock.flash.xiaomi.xiaomi_flash_gui import XiaomiFlashToolWidget
            self.flash_tab = XiaomiFlashToolWidget()
            self.tab_widget.addTab(self.flash_tab, 'Flash')
            self._xiaomi_flash_available = True
        except ImportError as e:
            self.logger.warning(f'Xiaomi Flash Tool n├úo dispon├¡vel: {e}')
            self._xiaomi_flash_available = False
        try:
            from app.views.union_unlock.sideload.xiaomi.xiaomi_sideload_gui import XiaomiSideloadWidget
            self.sideload_tab = XiaomiSideloadWidget()
            self.tab_widget.addTab(self.sideload_tab, 'Sideload')
            self._xiaomi_sideload_available = True
        except ImportError as e:
            self.logger.warning(f'Xiaomi Sideload Tool n├úo dispon├¡vel: {e}')
            self._xiaomi_sideload_available = False
        main_layout.addWidget(self.tab_widget)
    def _setup_standard_tab(self, tab_container):
        '''Configura a aba padr├úo com as ferramentas existentes'''
        tab_layout = QHBoxLayout(tab_container)
        tab_layout.setSpacing(10)
        tab_layout.setContentsMargins(10, 10, 10, 10)
        left_panel = QFrame()
        left_panel.setStyleSheet('\n            QFrame {\n                background-color: #ffffff;\n                border-radius: 8px;\n                border: 1px solid #e0e0e0;\n            }\n        ')
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(15)
        status_frame = QFrame()
        status_frame.setStyleSheet('\n            QFrame {\n                background-color: #FF6900;\n                border-radius: 6px;\n                padding: 8px;\n                border: 1px solid #E55A00;\n            }\n            QLabel {\n                color: #ffffff;\n                margin-bottom: 2px;\n                font-size: 9pt;\n                font-weight: bold;\n            }\n        ')
        status_layout = QVBoxLayout(status_frame)
        self.device_info = QLabel('Verificando dispositivo...')
        self.device_info.setStyleSheet('font-weight: bold; font-size: 11pt;')
        status_layout.addWidget(self.device_info)
        self.miui_version = QLabel('MIUI/HyperOS: Verificando...')
        status_layout.addWidget(self.miui_version)
        self.battery_level = QLabel('Bateria: --')
        status_layout.addWidget(self.battery_level)
        self.bootloader_status = QLabel('Status: --')
        status_layout.addWidget(self.bootloader_status)
        left_layout.addWidget(status_frame)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('\n            QScrollArea { border: none; background: transparent; }\n            QScrollBar:vertical {\n                background: #f0f0f0;\n                width: 8px;\n                border-radius: 4px;\n            }\n            QScrollBar::handle:vertical {\n                background: #bdc3c7;\n                border-radius: 4px;\n                min-height: 20px;\n            }\n            QScrollBar::handle:vertical:hover {\n                background: #FF6900;\n            }\n            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {\n                height: 0px;\n            }\n        ')
        scroll_content = QWidget()
        buttons_layout = QVBoxLayout(scroll_content)
        buttons_layout.setSpacing(10)
        from app.utils.path_manager import PathManager
        self._svg_path = PathManager.get_resource_path('icons_svg')
        _btn_icons = {'Verificar Dispositivo': 'question-circle.svg', 'Status Bootloader': 'shield-lock.svg', 'Identificacao Completa': 'card-checklist.svg', 'Preparar Unlock': 'shield-check.svg', 'Bypass Anti-rollback': 'shield-shaded.svg', 'FRP MODELS MTK/SPD': 'phone-flip.svg', 'Desativar DM-Verity': 'shield-fill-check.svg', 'Download Firmware': 'cloud-arrow-down.svg', 'Remover MiCloud': 'globe.svg', 'Remover Mi Account': 'shield-shaded.svg', 'Habilitar Temas': 'window.svg', 'Desativar Anuncios': 'shield-fill-check.svg', 'Desativar Otimizacoes': 'cpu.svg', 'Remover Updates OTA': 'arrow-clockwise.svg', 'Permissoes de Seguranca': 'shield-lock.svg', 'Otimizacao de Bateria': 'battery-charging.svg'}
        buttons = [('Verificar Dispositivo', self.check_device, 'Detecta dispositivo em ADB ou Fastboot', False), ('FRP MODELS MTK/SPD', self.show_frp_xiaomi_mtk, 'Remocao de FRP por modelo - MTK/SPD', False), ('Identificacao Completa', (lambda: self.log_area.append(self.xiaomi_manager.get_device_identifiers())), 'Serial, codename, baseband, build, seguranca', False), ('Preparar Unlock', self.prep_bootloader, 'Prepara dispositivo para desbloqueio', True), ('Bypass Anti-rollback', self.bypass_arb, 'Bypass da protecao anti-rollback', True), ('Desativar DM-Verity', self.disable_verity, 'Desativa verificacao DM-Verity', True), ('Download Firmware', self.download_firmware, 'Download de firmware oficial Xiaomi', False), ('Remover MiCloud', self.remove_micloud, 'Remove apenas servico Mi Cloud', False), ('Remover Mi Account', self.remove_mi_account, 'Remove conta Mi completa do dispositivo', True), ('premium:ID:3', self.execute_frp_xiaomi_remote, 'Servico Premium - FRP Xiaomi Remoto USB Android 13-15', False), ('premium:ID:4', self.execute_frp_xiaomi_id_4, 'Servico Premium Exclusivo Xiaomi - Requer creditos', False), ('Habilitar Temas', self.enable_themes, 'Permite instalacao de temas de terceiros', False), ('Desativar Anuncios', self.disable_ads, 'Remove anuncios do sistema MIUI/HyperOS', False), ('Desativar Otimizacoes', self.disable_optimization, 'Desativa otimizacoes do sistema', False), ('Remover Updates OTA', self.remove_ota_updates, 'Remove atualizacoes automaticas do sistema', True), ('Permissoes de Seguranca', self.grant_permissions, 'Concede permissoes de sistema', False), ('Otimizacao de Bateria', (lambda: self.disable_battery('com.miui.securitycenter')), 'Desativa otimizacao de bateria', False)]
        dev_notice = QLabel('Algumas funcionalidades estao em fase de testes. Sempre faca backup antes de procedimentos criticos.')
        dev_notice.setStyleSheet('\n            QLabel {\n                color: #e67e22;\n                font-size: 7pt;\n                padding: 6px 10px;\n                background-color: #fff8e1;\n                border: 1px solid #ffcc02;\n                border-radius: 4px;\n            }\n        ')
        dev_notice.setWordWrap(True)
        dev_notice.setAlignment(Qt.AlignCenter)
        buttons_layout.addWidget(dev_notice)
        from app.utils.premium_services_manager import get_premium_services_manager
        premium_manager = get_premium_services_manager()
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(6)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setColumnStretch(2, 1)
        row = 0
        col = 0
        for text, func, placeholder, is_warning in buttons:
            btn_container = QWidget()
            btn_layout = QVBoxLayout(btn_container)
            btn_layout.setSpacing(2)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            is_premium_button = text.startswith('premium:')
            if is_premium_button:
                servico_identificador = text.replace('premium:', '')
                btn = premium_manager.criar_botao_premium_com_indicador(servico_identificador, func, parent=self, cor_personalizada='laranja')
                btn.setToolTip(placeholder)
                if not hasattr(self, 'premium_buttons'):
                    self.premium_buttons = []
                self.premium_buttons.append((btn, servico_identificador))
            else:
                btn = QPushButton(text)
                btn.setStyleSheet(self.button_style)
                btn.clicked.connect(func)
                btn.setToolTip(placeholder)
            icon_file = _btn_icons.get(text)
            if icon_file and self._svg_path:
                icon_full = os.path.join(self._svg_path, icon_file)
                if os.path.isfile(icon_full):
                    btn.setIcon(QIcon(icon_full))
            btn_layout.addWidget(btn)
            placeholder_label = QLabel(placeholder)
            placeholder_label.setStyleSheet(self.placeholder_style)
            btn_layout.addWidget(placeholder_label)
            grid_layout.addWidget(btn_container, row, col)
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
        tab_layout.addWidget(left_panel, stretch=7)
        terminal_panel = QFrame()
        terminal_panel.setStyleSheet('\n            QFrame {\n                background-color: #1e1e1e;\n                border-radius: 8px;\n                padding: 10px;\n            }\n        ')
        terminal_layout = QVBoxLayout(terminal_panel)
        terminal_header = QLabel('Terminal de Logs')
        terminal_header.setStyleSheet('\n            color: white;\n            font-weight: bold;\n            font-size: 9pt;\n            padding: 5px;\n        ')
        terminal_layout.addWidget(terminal_header)
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("\n            QTextEdit {\n                background-color: #1e1e1e;\n                color: #ffffff;\n                font-family: 'Consolas', 'Courier New', monospace;\n                font-size: 9pt;\n                border: none;\n                border-radius: 5px;\n                padding: 8px;\n            }\n        ")
        terminal_layout.addWidget(self.log_area)
        self._show_welcome_message()
        tab_layout.addWidget(terminal_panel, stretch=3)
    def showEvent(self, event):
        '''Quando a aba ├® mostrada, inicia o timer'''
        super().showEvent(event)
        self.logger.debug('Aba Xiaomi mostrada, iniciando timer de atualiza├º├úo')
    def hideEvent(self, event):
        '''Quando a aba ├® escondida, para o timer'''
        super().hideEvent(event)
        self.logger.debug('Aba Xiaomi escondida, parando timer de atualiza├º├úo')
        if self.current_info_thread and self.current_info_thread.isRunning():
            self.logger.debug('Parando thread de informa├º├Áes ao esconder aba')
            self.current_info_thread.stop()
        if self.command_thread:
            if self.command_thread.isRunning():
                self.logger.debug('Parando thread de comandos ao esconder aba')
                self.command_thread.stop()
    def periodic_check(self):
        '''Verifica periodicamente o dispositivo, mas limita o n├║mero de verifica├º├Áes'''
        if hasattr(self, '_periodic_checking') and self._periodic_checking:
            self.logger.debug('Verifica├º├úo peri├│dica j├í em andamento, ignorando')
            return
        self._periodic_checking = True
        try:
            current_time = time.time()
            elapsed_time = current_time - self.device_timer.elapsed() / 1000.0
            if self.verification_count >= 3 and elapsed_time < 300:
                self.logger.debug('Limite de verifica├º├Áes atingido, ignorando verifica├º├úo peri├│dica')
                self._periodic_checking = False
                return
        finally:
            self._periodic_checking = False
        try:
            if self._checking_device:
                self.logger.debug('J├í verificando dispositivo, ignorando verifica├º├úo peri├│dica')
                self._periodic_checking = False
                return
        finally:
            self._periodic_checking = False
        try:
            if not self.last_check_time:
                self.last_check_time = current_time - 31
            if current_time - self.last_check_time < 30:
                self.logger.debug('Verifica├º├úo muito recente, ignorando verifica├º├úo peri├│dica')
                self._periodic_checking = False
                return
        finally:
            self._periodic_checking = False
        try:
            self.last_check_time = current_time
            if not self.device_timer.isValid() or self.device_timer.elapsed() > 300000:
                self.device_timer.start()
                self.verification_count = 0
            self.verification_count += 1
        finally:
            self._periodic_checking = False
    def check_device(self):
        '''Verifica o dispositivo com limita├º├úo de frequ├¬ncia'''
        if not self.isVisible():
            self.logger.debug('Tab n├úo est├í vis├¡vel, pulando verifica├º├úo')
            return
        if self.current_info_thread and self.current_info_thread.isRunning():
            self.logger.debug('J├í existe uma verifica├º├úo em andamento')
            return
        current_time = time.time()
        if self.cache_valid_until and current_time < self.cache_valid_until:
            self.logger.debug('Usando informa├º├Áes em cache')
            return
        if self.last_check_time:
            elapsed = current_time - self.last_check_time
            if elapsed < self.check_interval:
                if self.check_count >= self.max_checks:
                    self.logger.debug(f'Limite de verifica├º├Áes atingido ({self.max_checks} em {self.check_interval}s)')
                    return
            else:
                self.check_count = 0
        self.last_check_time = current_time
        self.check_count += 1
        self.device_info.setText('Verificando dispositivo...')
        self._checking_device = True
        self.current_info_thread = DeviceInfoThread(self.xiaomi_manager)
        self.current_info_thread.info_updated.connect(self.update_device_info)
        self.current_info_thread.error_occurred.connect(self.handle_device_error)
        self.current_info_thread.finished.connect(self.on_check_finished)
        self.active_threads.append(self.current_info_thread)
        self.current_info_thread.start()
    def on_check_finished(self):
        '''Chamado quando a verifica├º├úo termina'''
        self._checking_device = False
        self.logger.debug('Verifica├º├úo de dispositivo conclu├¡da')
    def update_device_info(self, info):
        '''Atualiza a UI com as informa├º├Áes do dispositivo'''
        try:
            self.device_info_cache = info
            self.cache_valid_until = time.time() + self.cache_ttl
            if not info.get('connected', False):
                self.device_info.setText('Nenhum dispositivo conectado (ADB/Fastboot)')
                self.miui_version.setText('MIUI/HyperOS: --')
                self.battery_level.setText('Bateria: --')
                self.bootloader_status.setText('Status: --')
                self.disable_buttons(keep_verify=True)
                return
            if 'error' in info:
                self.device_info.setText('Erro ao verificar dispositivo')
                self.logger.error(f'Erro de atualiza├º├úo: {info['error']}')
                self.disable_buttons(keep_verify=True)
                return
            mode = info.get('mode', 'adb')
            if mode == 'fastboot':
                product = info.get('fb_product', 'Desconhecido')
                serial = info.get('fb_serial', 'N/A')
                unlocked = info.get('fb_unlocked', '')
                anti = info.get('fb_anti', '')
                secure = info.get('fb_secure', '')
                self.device_info.setText(f'Dispositivo em FASTBOOT: {product}')
                self.miui_version.setText(f'Produto: {product}')
                self.battery_level.setText('Bateria: N/A (Fastboot)')
                if unlocked == 'yes':
                    self.bootloader_status.setText('Bootloader Desbloqueado')
                elif unlocked == 'no':
                    self.bootloader_status.setText('Bootloader Bloqueado')
                else:
                    self.bootloader_status.setText('Status: --')
                log_lines = ['ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ', '­ƒô▒ DISPOSITIVO DETECTADO EM MODO FASTBOOT', 'ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ', f'  Produto: {product}', f'  Serial: {serial}']
                if unlocked:
                    log_lines.append(f'  Bootloader: {'Desbloqueado' if unlocked == 'yes' else 'Bloqueado'}')
                if anti:
                    log_lines.append(f'  Anti-rollback (anti): {anti}')
                if secure:
                    log_lines.append(f'  Secure boot: {secure}')
                fb_vars = info.get('fastboot_vars', {})
                extra_keys = ['version-bootloader', 'version-baseband', 'partition-type:system', 'max-download-size', 'slot-count', 'current-slot', 'battery-voltage']
                for key in extra_keys:
                    if key in fb_vars:
                        log_lines.append(f'  {key}: {fb_vars[key]}')
                log_lines.append('ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ')
                log_lines.append('­ƒÆí Dispositivo est├í em modo Fastboot (brickado ou aguardando flash)')
                log_lines.append('')
                self.log_area.append('\n'.join(log_lines))
                self.enable_buttons()
                return
            if not info.get('is_xiaomi', False):
                self.device_info.setText('Dispositivo nao e Xiaomi')
                self.miui_version.setText('MIUI/HyperOS: --')
                self.battery_level.setText('Bateria: --')
                self.bootloader_status.setText('Status: --')
                self.disable_buttons(keep_verify=True)
                return
            miui_version = info.get('miui_version', '')
            if 'MIUI' in miui_version:
                formatted_version = miui_version
            elif 'HyperOS' in miui_version:
                formatted_version = miui_version
            elif 'V' in miui_version and len(miui_version.split('.')) >= 2:
                formatted_version = f'MIUI {miui_version}'
            elif 'xiaomi' in miui_version.lower() or 'redmi' in miui_version.lower():
                formatted_version = miui_version
            else:
                formatted_version = f'MIUI/HyperOS {miui_version}'
            self.miui_version.setText(f'{formatted_version}')
            battery = info.get('battery', '--')
            charging = '[Carregando]' if info.get('charging') == 'Carregando' else ''
            self.battery_level.setText(f'Bateria: {battery}% {charging}')
            security = info.get('bootloader', '')
            if 'Desbloqueado' in security:
                self.bootloader_status.setText('Bootloader Desbloqueado')
            else:
                self.bootloader_status.setText('Bootloader Bloqueado')
            self.device_info.setText('Dispositivo Xiaomi conectado (ADB)')
            self.enable_buttons()
            return
        except Exception as e:
            self.logger.error(f'Erro ao atualizar UI: {str(e)}')
            self.device_info.setText('Erro ao atualizar informacoes')
    def handle_device_error(self, error):
        '''Trata erros de atualiza├º├úo'''
        if error == 'device_not_found':
            self.device_info.setText('Dispositivo nao encontrado')
            self.miui_version.setText('MIUI/HyperOS: --')
            self.battery_level.setText('Bateria: --')
            self.bootloader_status.setText('Status: --')
            self.disable_buttons(keep_verify=True)
            return
        self.device_info.setText('Erro ao verificar dispositivo')
        self.logger.error(f'Erro de atualiza├º├úo: {error}')
        self.disable_buttons(keep_verify=True)
    def enable_buttons(self):
        '''Habilita todos os bot├Áes'''
        for btn in self.findChildren(QPushButton):
            btn.setEnabled(True)
            btn.setCursor(Qt.ArrowCursor)
    def disable_buttons(self, keep_verify=False):
        '''Desabilita todos os bot├Áes exceto Verificar'''
        for btn in self.findChildren(QPushButton):
            if keep_verify and 'Verificar Dispositivo' in btn.text():
                btn.setEnabled(True)
                btn.setCursor(Qt.ArrowCursor)
                continue
            btn.setEnabled(False)
            btn.setCursor(Qt.BusyCursor)
    def show_warning(self, title, message):
        '''Mostra aviso de opera├º├úo perigosa'''
        reply = QMessageBox.warning(self, title, f'{message}\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        return reply == QMessageBox.Yes
    def execute_command(self, function, *args, **kwargs):
        '''Executa um comando em uma thread separada'''
        if hasattr(self, '_executing_command') and self._executing_command:
            QMessageBox.warning(self, 'Opera├º├úo em Andamento', 'J├í existe uma opera├º├úo em andamento.\nPor favor, aguarde.')
            return
        self._executing_command = True
        try:
            if not self.device_info_cache.get('connected', False):
                QMessageBox.warning(self, 'Erro', 'Nenhum dispositivo conectado')
                QTimer.singleShot(500, (lambda: setattr(self, '_executing_command', False)))
                return
        finally:
            QTimer.singleShot(500, (lambda: setattr(self, '_executing_command', False)))
        try:
            if not self.device_info_cache.get('is_xiaomi', False):
                QMessageBox.warning(self, 'Erro', 'Apenas dispositivos Xiaomi s├úo suportados')
                QTimer.singleShot(500, (lambda: setattr(self, '_executing_command', False)))
                return
        finally:
            QTimer.singleShot(500, (lambda: setattr(self, '_executing_command', False)))
        try:
            self.device_info.setText('Executando operacao...')
            self.command_thread = CommandThread(function, *args, **kwargs)
            self.command_thread.command_started.connect((lambda: self.disable_buttons(True)))
            self.command_thread.command_finished.connect(self.on_command_finished)
            self.command_thread.command_error.connect(self.handle_command_error)
            self.active_threads.append(self.command_thread)
            self.command_thread.finished.connect((lambda: self.cleanup_thread(self.command_thread)))
            self.command_thread.start()
        finally:
            QTimer.singleShot(500, (lambda: setattr(self, '_executing_command', False)))
    def on_command_finished(self, success, result):
        '''Callback para quando um comando ├® conclu├¡do'''
        if success:
            self.log_area.append(result)
            self.enable_buttons()
            if not self._checking_device:
                QTimer.singleShot(1000, self.check_device)
        else:
            self.log_area.append(f'ÔØî Erro: {result}')
            self.enable_buttons()
        try:
            self.adb_manager.finalize_adb_operation()
            return
        except:
            return
    def handle_command_error(self, error):
        '''Trata erros de comandos'''
        self.log_area.append(f'ÔØî Erro: {error}')
        self.enable_buttons()
    def prep_bootloader(self):
        if self.show_warning('ÔÜá´©Å Aten├º├úo - Unlock Bootloader', 'Esta opera├º├úo ir├í:\n1. Apagar todos os dados do dispositivo\n2. Invalidar a garantia\n3. Reiniciar em modo fastboot\n\nCertifique-se de ter:\n- Feito backup de todos os dados\n- Mi Unlock Tool instalado no PC\n- Conta Xiaomi adicionada no dispositivo'):
            self.execute_command(self.xiaomi_manager.prepare_for_unlock)
    def enable_themes(self):
        self.execute_command(self.xiaomi_manager.enable_third_party_themes)
    def disable_ads(self):
        self.execute_command(self.xiaomi_manager.disable_miui_ads)
    def disable_optimization(self):
        self.execute_command(self.xiaomi_manager.disable_miui_optimization)
    def frp_mtk_xiaomi(self):
        '''
        Abre janela de FRP/MTK para dispositivos Xiaomi com chipset MediaTek.
        PROTE├ç├òES IMPLEMENTADAS:
        1. Singleton - Apenas uma janela por vez (evita duplicatas)
        2. Valida├º├úo de estado antes de abrir
        3. Exception handling robusto em todas as camadas
        4. Logs seguros - Sem exposi├º├úo de erros internos
        5. Mensagens amig├íveis - Sem termos t├®cnicos para usu├írio
        6. Aviso de responsabilidade - Usu├írio ciente dos riscos
        7. Confirma├º├úo de compatibilidade MTK
        SEGURAN├çA:
        - Ô£à Previne m├║ltiplas janelas abertas simultaneamente
        - Ô£à Valida├º├úo de importa├º├úo sem quebrar aplicativo
        - Ô£à Cleanup autom├ítico em caso de erro
        - Ô£à Thread-safe (gerenciador usa Singleton)
        - Ô£à N├úo exp├Áe paths/erros internos ao usu├írio
        - Ô£à Mensagens amig├íveis e persuasivas
        COMPORTAMENTO:
        1. Verifica se janela j├í est├í aberta (traz para frente se sim)
        2. Mostra aviso de responsabilidade (usu├írio deve aceitar)
        3. Importa GUI FRP com try/except robusto
        4. Abre janela em processo separado (n├úo trava aba Xiaomi)
        5. Log de todas as opera├º├Áes (sem expor erros t├®cnicos)
        '''
        try:
            self.log_area.append('============================================================')
            self.log_area.append('­ƒöº ABRINDO FERRAMENTA FRP/MTK XIAOMI')
            self.log_area.append('============================================================')
            try:
                from app.utils.frp_mtk_manager import get_frp_mtk_manager
                self.log_area.append('Ô£à M├│dulo FRP/MTK carregado com sucesso')
            except ImportError as e:
                self.logger.error(f'Erro ao importar FRP/MTK Manager: {type(e).__name__}')
                self.log_area.append('ÔØî Ferramenta FRP/MTK temporariamente indispon├¡vel')
                QMessageBox.warning(self, 'Ferramenta Indispon├¡vel', 'A ferramenta FRP/MTK esta em manutencao.\n\nO que fazer:\n- Reinicie o aplicativo e tente novamente\n- Entre em contato com o suporte se necessario\n\nSuporte: (85) 99750-7465')
            else:
                frp_manager = get_frp_mtk_manager()
                disponivel, mensagem = frp_manager.verificar_disponibilidade()
                if not disponivel:
                    QMessageBox.warning(self, 'ÔÜá´©Å FRP Xiaomi MTK Indispon├¡vel', mensagem)
                    self.log_area.append('ÔØî FRP MTK n├úo dispon├¡vel')
                    return
                if frp_manager.esta_rodando():
                    QMessageBox.information(self, 'FRP Xiaomi MTK', 'O FRP Xiaomi MTK ja esta em execucao!\n\nVerifique se a janela esta minimizada ou atras de outras janelas.\n\nCaso nao encontre a janela, feche o TECH UNION e abra novamente.')
                    self.log_area.append('Ô£à FRP MTK j├í est├í ativo')
                    return
                sucesso, mensagem_retorno = frp_manager.abrir(parent=self)
                if sucesso:
                    self.log_area.append('Ô£à FRP Xiaomi MTK iniciado com sucesso!')
                    self.log_area.append('')
                    self.log_area.append('­ƒôî INSTRU├ç├òES:')
                    self.log_area.append('   1. Aguarde a janela do FRP MTK carregar')
                    self.log_area.append('   2. Conecte o dispositivo Xiaomi MTK em modo BROM')
                    self.log_area.append('      (Aparelho desligado + Vol- + USB)')
                    self.log_area.append("   3. Clique em 'Conectar Dispositivo'")
                    self.log_area.append('   4. Aguarde leitura das parti├º├Áes')
                    self.log_area.append("   5. Clique em 'Apagar FRP' (backup autom├ítico)")
                    self.log_area.append('')
                    self.log_area.append('­ƒÆí A ferramenta ir├í abrir em alguns instantes...')
                    self.log_area.append('============================================================')
                    QMessageBox.information(self, 'FRP Xiaomi MTK', 'FRP Xiaomi MTK iniciado com sucesso!\n\nFerramenta especializada para Xiaomi MediaTek\n\nA interface do FRP ira abrir em alguns instantes.\nAguarde o carregamento completo da ferramenta.')
                    return
                QMessageBox.critical(self, 'Erro ao Abrir FRP MTK', mensagem_retorno)
                self.log_area.append('ÔØî Erro ao abrir FRP MTK')
        except Exception as e:
            self.logger.error(f'Erro cr├¡tico em frp_mtk_xiaomi: {type(e).__name__}')
            self.log_area.append('ÔØî Erro inesperado ao abrir FRP/MTK')
            QMessageBox.critical(self, 'Erro Inesperado', 'Ocorreu um erro inesperado.\n\nPor favor, reinicie o aplicativo e tente novamente.\n\nSe o problema persistir, contate o suporte t├®cnico.')
    def bypass_arb(self):
        if self.show_warning('ÔÜá´©Å Aten├º├úo - Anti-rollback', 'O bypass do Anti-rollback ├® uma opera├º├úo perigosa.\nPode causar brick se mal executada.\n\nCertifique-se de entender os riscos antes de prosseguir.'):
            self.execute_command(self.xiaomi_manager.bypass_anti_rollback)
    def fix_xiaomi_verity(self):
        '''Corrige o problema de dm-verity em dispositivos Xiaomi'''
        try:
            if not self.adb_manager.fastboot_path:
                self.log_area.append('­ƒöì Procurando Fastboot...')
                self.adb_manager.fastboot_path = self.adb_manager.find_fastboot_path()
            if not self.adb_manager.fastboot_path:
                self.log_area.append('ÔØî Fastboot n├úo encontrado, imposs├¡vel corrigir DM-Verity')
                self.log_area.append('­ƒÆí Verifique se o Fastboot esta instalado no sistema')
                return False
            self.logger.debug('Fastboot path: %s', self.adb_manager.fastboot_path)
            self.log_area.append('Ô£à Fastboot encontrado')
            si = None
            cf = 0
            if platform.system() == 'Windows':
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                si.wShowWindow = subprocess.SW_HIDE
                cf = subprocess.CREATE_NO_WINDOW
            result = subprocess.run([self.adb_manager.fastboot_path, 'devices'], capture_output=True, text=True, check=False, startupinfo=si, creationflags=cf, cwd=os.path.dirname(self.adb_manager.fastboot_path))
            if not result.stdout.strip():
                self.log_area.append('ÔØî Nenhum dispositivo em modo fastboot detectado')
                return False
            device_id = result.stdout.strip().split()[0]
            self.log_area.append(f'Ô£à Dispositivo fastboot detectado: {device_id}')
            self.log_area.append('­ƒöä Aplicando corre├º├úo DM-Verity...')
            subprocess.run([self.adb_manager.fastboot_path, 'oem', 'cdms', 'fix'], capture_output=True, text=True, check=False, startupinfo=si, creationflags=cf, cwd=os.path.dirname(self.adb_manager.fastboot_path))
            self.log_area.append('­ƒöä Reiniciando dispositivo...')
            subprocess.run([self.adb_manager.fastboot_path, 'reboot'], capture_output=True, text=True, check=False, startupinfo=si, creationflags=cf, cwd=os.path.dirname(self.adb_manager.fastboot_path))
            self.log_area.append('Ô£à Corre├º├úo aplicada com sucesso. Dispositivo reiniciando...')
            return True
        except Exception as e:
            self.logger.error(f'aplicar_correcao falhou: {e}')
            self.log_area.append('ÔØî Nao foi possivel aplicar a correcao. Tente novamente.')
            return False
    def disable_verity(self):
        '''Handler para o bot├úo de desativar DM-Verity'''
        if self.show_warning('ÔÜá´©Å Aten├º├úo - DM-Verity', 'Desativar o DM-Verity pode comprometer a seguran├ºa do dispositivo.\nO dispositivo precisa estar em modo fastboot.'):
            self.fix_xiaomi_verity()
    def grant_permissions(self):
        self.execute_command(self.xiaomi_manager.grant_security_permissions)
    def disable_battery(self, package):
        self.execute_command(self.xiaomi_manager.disable_battery_optimization, package)
    def remove_ota_updates(self):
        '''Remove o aplicativo de atualiza├º├Áes OTA para evitar updates autom├íticos'''
        if self.show_warning('ÔÜá´©Å ATEN├ç├âO - Remover Updates OTA', 'Esta opera├º├úo ir├í:\n1. Remover permanentemente o aplicativo de atualiza├º├Áes autom├íticas\n2. IMPEDIR que o sistema baixe e instale atualiza├º├Áes OTA\n3. Esta a├º├úo pode N├âO SER REVERS├ìVEL facilmente\n\nRISCOS IMPORTANTES:\nÔÇó Voc├¬ n├úo receber├í mais atualiza├º├Áes de seguran├ºa autom├íticas\nÔÇó Corre├º├Áes de bugs do sistema n├úo ser├úo aplicadas automaticamente\nÔÇó Para atualizar no futuro, ser├í necess├írio fazer flash manual\nÔÇó Em alguns casos, pode ser necess├írio resetar o dispositivo para reverter\n\nCertifique-se de entender completamente os riscos antes de prosseguir.\nEsta opera├º├úo ├® recomendada apenas para usu├írios avan├ºados.'):
            try:
                if not self.adb_manager.adb_path:
                    self.log_area.append('ÔØî Ferramenta de comunicacao nao encontrada. Reinstale o aplicativo ou contate o suporte.')
                    return
                si = None
                cf = 0
                if platform.system() == 'Windows':
                    si = subprocess.STARTUPINFO()
                    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    si.wShowWindow = subprocess.SW_HIDE
                    cf = subprocess.CREATE_NO_WINDOW
                result = subprocess.run([self.adb_manager.adb_path, 'devices'], capture_output=True, text=True, check=False, startupinfo=si, creationflags=cf, cwd=os.path.dirname(self.adb_manager.adb_path))
                lines = result.stdout.strip().split('\n')
                devices_connected = False
                for line in lines[1:]:
                    if not line.strip():
                        continue
                    if not '\tdevice' in line:
                        continue
                    devices_connected = True
                    break
                if not devices_connected:
                    self.log_area.append('ÔØî Nenhum dispositivo detectado. Verifique se:\n1. O dispositivo est├í conectado via USB\n2. A Depura├º├úo USB est├í ativada nas Op├º├Áes do Desenvolvedor\n3. O dispositivo est├í desbloqueado e autorizado\n4. Os drivers est├úo instalados corretamente')
                    return
                self.log_area.append('­ƒöä Removendo aplicativo de atualiza├º├Áes OTA...')
                result = subprocess.run([self.adb_manager.adb_path, 'shell', 'pm', 'uninstall', '-k', '--user', '0', 'com.android.updater'], capture_output=True, text=True, check=False, startupinfo=si, creationflags=cf, cwd=os.path.dirname(self.adb_manager.adb_path))
                if result.returncode == 0:
                    self.log_area.append('Ô£à Aplicativo de atualiza├º├Áes OTA removido com sucesso!')
                    self.log_area.append('\n­ƒôï INFORMA├ç├òES IMPORTANTES:')
                    self.log_area.append('ÔÇó As atualiza├º├Áes autom├íticas foram desativadas')
                    self.log_area.append('ÔÇó Voc├¬ n├úo receber├í mais notifica├º├Áes de atualiza├º├úo')
                    self.log_area.append('ÔÇó Para atualizar no futuro, use m├®todos manuais (fastboot/recovery)')
                    self.log_area.append('ÔÇó Para reverter, pode ser necess├írio um factory reset')
                    self.log_area.append('\n­ƒÆí Dica: Mantenha-se informado sobre atualiza├º├Áes de seguran├ºa!')
                    return
                error_output = result.stderr.strip() if result.stderr else 'Erro desconhecido'
                self.log_area.append(f'ÔØî Falha ao remover aplicativo de updates: {error_output}')
                self.log_area.append('Ôä╣´©Å Poss├¡veis causas:')
                self.log_area.append('ÔÇó O aplicativo j├í foi removido anteriormente')
                self.log_area.append('ÔÇó Permiss├Áes insuficientes')
                self.log_area.append('ÔÇó Aplicativo protegido pelo sistema')
            except Exception as e:
                self.logger.error(f'remove_ota_updates falhou: {e}')
                self.log_area.append('ÔØî Nao foi possivel remover atualizacoes. Verifique a conexao e tente novamente.')
    def closeEvent(self, event):
        '''Limpa recursos ao fechar a janela'''
        if self.current_info_thread:
            self.current_info_thread.stop()
        for thread in self.active_threads:
            if thread.isRunning():
                thread.running = False
                thread.wait(1000)
        super().closeEvent(event)
    def show_frp_xiaomi_mtk(self):
        '''Abre a interface de FRP Xiaomi MTK (BROM Mode)'''
        try:
            self.log_area.append('­ƒöô Abrindo FRP Xiaomi MTK (BROM Mode)...')
            from PyQt5.QtWidgets import QDialog, QVBoxLayout
            from PyQt5.QtGui import QIcon
            import os
            import sys
            union_unlock_path = os.path.join(os.path.dirname(__file__), 'union_unlock')
            if union_unlock_path not in sys.path:
                sys.path.insert(0, union_unlock_path)
            from xiaomi.xiaomi import XiaomiWidget
            dialog = QDialog(self)
            dialog.setWindowTitle('FRP Xiaomi - TECH UNION')
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
            xiaomi_widget = XiaomiWidget()
            layout.addWidget(xiaomi_widget)
            self._xiaomi_dialog = dialog
            dialog.show()
            self.log_area.append('Ô£à Interface FRP Xiaomi MTK aberta!')
            return
        except Exception as e:
            self.logger.error(f'abrir_frp_xiaomi falhou: {e}')
            self.log_area.append('ÔØî Nao foi possivel abrir FRP Xiaomi. Tente novamente.')
    def remove_micloud(self):
        '''Remove MiCloud do dispositivo'''
        if self.show_warning('ÔÜá´©Å Aten├º├úo - Remover MiCloud', 'Esta opera├º├úo ir├í remover a conta MiCloud.\nCertifique-se de ter feito backup dos dados.'):
            self.execute_command(self.xiaomi_manager.remove_micloud)
    def remove_mi_account(self):
        '''Remove conta Mi via ADB'''
        if self.show_warning('ÔÜá´©Å Aten├º├úo - Remover Mi Account', 'Esta opera├º├úo ir├í tentar remover a conta Mi do dispositivo.\nCertifique-se que:\n1. O dispositivo est├í conectado via USB\n2. A Depura├º├úo USB est├í ativada\n3. O dispositivo est├í desbloqueado'):
            try:
                if not self.adb_manager.adb_path:
                    self.log_area.append('ÔØî Ferramenta de comunicacao nao encontrada. Reinstale o aplicativo ou contate o suporte.')
                    return
                si = None
                cf = 0
                if platform.system() == 'Windows':
                    si = subprocess.STARTUPINFO()
                    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    si.wShowWindow = subprocess.SW_HIDE
                    cf = subprocess.CREATE_NO_WINDOW
                result = subprocess.run([self.adb_manager.adb_path, 'devices'], capture_output=True, text=True, check=False, startupinfo=si, creationflags=cf, cwd=os.path.dirname(self.adb_manager.adb_path))
                lines = result.stdout.strip().split('\n')
                devices_connected = False
                for line in lines[1:]:
                    if not line.strip():
                        continue
                    if not '\tdevice' in line:
                        continue
                    devices_connected = True
                    break
                if not devices_connected:
                    self.log_area.append('ÔØî Nenhum dispositivo detectado. Verifique se:\n1. O dispositivo est├í conectado via USB\n2. A Depura├º├úo USB est├í ativada nas Op├º├Áes do Desenvolvedor\n3. O dispositivo est├í desbloqueado e autorizado\n4. Os drivers est├úo instalados corretamente')
                    return
                brand_result = subprocess.run([self.adb_manager.adb_path, 'shell', 'getprop', 'ro.product.brand'], capture_output=True, text=True, check=False, startupinfo=si, creationflags=cf, cwd=os.path.dirname(self.adb_manager.adb_path))
                brand = brand_result.stdout.strip().lower()
                if 'xiaomi' not in brand and 'redmi' not in brand:
                    self.log_area.append('ÔØî Este m├®todo s├│ funciona em dispositivos Xiaomi/Redmi')
                    return
                self.log_area.append('­ƒöä Removendo conta Mi...')
                commands = [['shell', 'pm', 'uninstall', '-k', '--user', '0', 'com.xiaomi.finddevice'], ['shell', 'pm', 'uninstall', '-k', '--user', '0', 'com.miui.cloudservice'], ['shell', 'pm', 'uninstall', '-k', '--user', '0', 'com.miui.cloudbackup'], ['shell', 'settings', 'put', 'global', 'device_provisioned', '1'], ['shell', 'settings', 'put', 'secure', 'user_setup_complete', '1'], ['shell', 'content', 'insert', '--uri', 'content://settings/secure', '--bind', 'name:s:user_setup_complete', '--bind', 'value:s:1']]
                for cmd in commands:
                    pass
                try:
                    subprocess.run([self.adb_manager.adb_path] + cmd, capture_output=True, text=True, check=False, startupinfo=si, creationflags=cf, cwd=os.path.dirname(self.adb_manager.adb_path))
                except:
                    pass
                else:
                    self.log_area.append('\nÔ£à Processo conclu├¡do!\n')
                    self.log_area.append('OBSERVA├ç├òES IMPORTANTES:')
                    self.log_area.append('1. Reinicie o dispositivo')
                    self.log_area.append('2. Se a conta Mi ainda aparecer, repita o processo')
                    self.log_area.append('3. Em alguns modelos pode ser necess├írio um m├®todo alternativo')
                    self.log_area.append('4. Este m├®todo n├úo funciona em todos os modelos Xiaomi')
            except Exception as e:
                self.logger.error(f'remove_mi_account falhou: {e}')
                self.log_area.append('ÔØî Nao foi possivel remover a conta Mi. Verifique a conexao e tente novamente.')
    def cleanup_thread(self, thread):
        '''Remove um thread conclu├¡do da lista de threads ativos'''
        if thread in self.active_threads:
            self.active_threads.remove(thread)
    def checking_device(self):
        '''Retorna o estado de verifica├º├úo do dispositivo'''
        return self._checking_device
    def checking_device_set(self, value):
        '''Define o estado de verifica├º├úo do dispositivo'''
        self._checking_device = value
    checking_device = property(checking_device, checking_device_set)
    def refresh_adb_connection(self):
        '''Atualiza a conex├úo ADB de forma segura'''
        if hasattr(self, '_refreshing_connection') and self._refreshing_connection:
            self.logger.debug('Atualiza├º├úo de conex├úo j├í em andamento, ignorando chamada')
            return
        self._refreshing_connection = True
        self.logger.info('Atualizando conex├úo ADB na aba Xiaomi')
        try:
            try:
                self.adb_manager.clear_adb_cache()
            except Exception as e:
                self.logger.error(f'Erro ao limpar cache ADB: {str(e)}')
        except Exception as e:
            self.logger.error(f'Erro ao atualizar conex├úo ADB: {str(e)}')
            self._refreshing_connection = False
        QTimer.singleShot(1000, self._delayed_refresh_check)
    def _delayed_refresh_check(self):
        '''Executa a verifica├º├úo do dispositivo com atraso para n├úo bloquear a UI'''
        try:
            if not self.isVisible():
                self.logger.debug('Aba n├úo est├í mais vis├¡vel, cancelando atualiza├º├úo')
                self._refreshing_connection = False
                return
            is_device = False
            is_xiaomi = False
        except Exception as e:
            self.logger.error(f'Erro ao executar verifica├º├úo adiada: {str(e)}')
            self._refreshing_connection = False
        try:
            def check_in_thread():
                nonlocal is_device, is_xiaomi
                try:
                    is_device = self.adb_manager.check_device()
                    if is_device:
                        is_xiaomi = self.xiaomi_manager.is_xiaomi_device()
                except Exception as e:
                    self.logger.error(f'Erro na verifica├º├úo do dispositivo: {str(e)}')
                else:
                    QTimer.singleShot(0, (lambda: self.update_ui_status(is_device, is_xiaomi)))
                    QTimer.singleShot(100, (lambda: setattr(self, '_refreshing_connection', False)))
                finally:
                    QTimer.singleShot(0, (lambda: self.update_ui_status(is_device, is_xiaomi)))
                    QTimer.singleShot(100, (lambda: setattr(self, '_refreshing_connection', False)))
            threading.Thread(target=check_in_thread, daemon=True).start()
            return
        except Exception as e:
            self.logger.error(f'Erro ao verificar dispositivo: {str(e)}')
            self._refreshing_connection = False
    def update_ui_status(self, is_device, is_xiaomi):
        '''Atualiza a UI baseado no status do dispositivo'''
        try:
            if is_device and is_xiaomi:
                self.device_info.setText('Dispositivo Xiaomi conectado')
                self.enable_buttons()
                return
            if is_device and not is_xiaomi:
                self.device_info.setText('Dispositivo nao e Xiaomi')
                self.disable_buttons(keep_verify=True)
                return
            self.device_info.setText('Nenhum dispositivo conectado')
            self.disable_buttons(keep_verify=True)
            return
        except Exception as e:
            self.logger.error(f'Erro ao atualizar status da UI: {str(e)}')
    def download_firmware(self):
        '''Abre o reposit├│rio de firmware da Xiaomi'''
        try:
            url = 'https://mifirm.net/list/model'
            QDesktopServices.openUrl(QUrl(url))
            self.log_area.append('Ô£à Abrindo reposit├│rio de firmware Xiaomi...')
            self.log_area.append('Ôä╣´©Å Dicas para download:')
            self.log_area.append('1. Procure seu modelo na lista')
            self.log_area.append('2. Escolha a vers├úo correta para sua regi├úo (Global, EEA, etc)')
            self.log_area.append('3. Verifique a vers├úo do Android antes de baixar')
            self.log_area.append('4. Certifique-se de baixar a ROM completa e n├úo apenas atualiza├º├Áes')
            return
        except Exception as e:
            self.logger.error(f'abrir_repositorio falhou: {e}')
            self.log_area.append('ÔØî Nao foi possivel abrir o repositorio. Tente novamente.')
    def execute_frp_xiaomi_remote(self):
        '''
        Executa servi├ºo premium FRP XIAOMI REMOTE USB.
        Servi├ºo remoto USB - Requer cr├®ditos
        Android 13-15 MIUI/HyperOS
        Busca por ID 3 no banco (t├¡tulo din├ómico)
        '''
        try:
            from app.utils.premium_services_manager import get_premium_services_manager
            user_id = 1
            if hasattr(self.parent, 'user_id'):
                user_id = self.parent.user_id
            premium_manager = get_premium_services_manager()
            servico = premium_manager.buscar_servico_premium_por_id(3)
            if servico:
                titulo_servico = servico.get('titulo', 'FRP XIAOMI REMOTE USB')
            else:
                titulo_servico = 'FRP XIAOMI REMOTE USB'
            sucesso = premium_manager.abrir_servico_premium(titulo=titulo_servico, user_id=user_id, parent=self)
            if sucesso:
                self.log_area.append('Ô£à Servi├ºo FRP XIAOMI REMOTE USB acessado')
                self.log_area.append('­ƒîÉ Servi├ºo premium aberto no navegador')
                return
            self.log_area.append('ÔÜá´©Å Acesso ao servi├ºo FRP XIAOMI cancelado ou indispon├¡vel')
            return
        except Exception as e:
            self.log_area.append('ÔÜá´©Å Erro ao acessar servi├ºo premium')
            self.log_area.append('ÔÜá´©Å Servi├ºo temporariamente indispon├¡vel')
            QMessageBox.warning(self, 'Servico Indisponivel', 'O servico esta temporariamente indisponivel.\n\nPor favor, tente novamente mais tarde.\n\nSuporte: (85) 99750-7465')
    def execute_frp_xiaomi_id_4(self):
        '''
        Executa servi├ºo premium ID 4 (Xiaomi).
        Servi├ºo premium - Requer cr├®ditos
        Busca por ID 4 no banco (t├¡tulo din├ómico)
        '''
        try:
            from app.utils.premium_services_manager import get_premium_services_manager
            user_id = 1
            if hasattr(self.parent, 'user_id'):
                user_id = self.parent.user_id
            premium_manager = get_premium_services_manager()
            servico = premium_manager.buscar_servico_premium_por_id(4)
            if servico:
                titulo_servico = servico.get('titulo', 'Servi├ºo Premium')
            else:
                titulo_servico = 'Servi├ºo Premium'
            sucesso = premium_manager.abrir_servico_premium(titulo=titulo_servico, user_id=user_id, parent=self)
            if sucesso:
                self.log_area.append(f'Ô£à Servi├ºo {titulo_servico} acessado')
                self.log_area.append('­ƒîÉ Servi├ºo premium aberto no navegador')
                return
            self.log_area.append(f'ÔÜá´©Å Acesso ao servi├ºo {titulo_servico} cancelado ou indispon├¡vel')
            return
        except Exception as e:
            self.log_area.append('ÔÜá´©Å Erro ao acessar servi├ºo premium')
            self.log_area.append('ÔÜá´©Å Servi├ºo temporariamente indispon├¡vel')
            QMessageBox.warning(self, 'Servico Indisponivel', 'O servico esta temporariamente indisponivel.\n\nPor favor, tente novamente mais tarde.\n\nSuporte: (85) 99750-7465')
    def _show_welcome_message(self):
        '''Exibe mensagem de boas-vindas com termo de responsabilidade'''
        welcome_msg = '\n===============================================================================\n  TECH UNION SOLUTIONS - Tools Xiaomi\n  Ferramentas Profissionais para Tecnicos\n===============================================================================\n\nBem-vindo ao modulo de ferramentas Xiaomi.\nSelecione uma aba acima para acessar os recursos disponiveis.\n\n  IMPORTANTE:\n\n   - Este sistema foi desenvolvido para profissionais e estudos tecnicos.\n   - Recomendamos conhecimento previo antes de executar qualquer procedimento.\n   - Sempre faca backup dos dados antes de qualquer intervencao.\n\n  Sobre Desbloqueios e Remocao de Protecoes:\n\n   - Utilize apenas em dispositivos de sua propriedade legitima.\n   - Para fins de estudo, testes e aprendizado tecnico.\n   - Respeite sempre a propriedade e privacidade de terceiros.\n\n  Responsabilidades:\n\n   - Voce e responsavel pelo uso correto das ferramentas.\n   - A TECH UNION disponibiliza as ferramentas para fins profissionais.\n   - Use seu conhecimento tecnico com etica e responsabilidade.\n   - Em caso de duvidas, consulte nossa equipe de suporte.\n\n===============================================================================\n  Conecte seu dispositivo e selecione a operacao desejada.\n===============================================================================\n\n'
        self.log_area.append(welcome_msg)
