import sys
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QComboBox, QLineEdit, QProgressBar, QTextEdit, QSplitter, QGroupBox, QCheckBox, QMessageBox, QInputDialog, QHeaderView, QAbstractItemView, QMenu, QAction, QDialog, QDialogButtonBox, QFrame, QFileDialog)
from PyQt5.QtCore import (Qt, QThread, pyqtSignal, QTimer, QSize, QDateTime)
from PyQt5.QtGui import (QIcon, QFont, QPixmap, QColor, QPalette)
from app.utils.adb_app_manager import (ADBAppManager, AppType, AppInfo)
from app.utils.translation_manager import TranslationManager
from app.utils.path_manager import PathManager
from app.utils._pkg_defs import _STATIC_PROTECTED
import logging
logger = logging.getLogger(__name__)
class AppManagerThread(QThread):
    progress_update = pyqtSignal(str)
    operation_complete = pyqtSignal(str, bool)
    apps_loaded = pyqtSignal(list)
    smart_cache_result = pyqtSignal(str, bool, dict)
    def __init__(self, app_manager, operation, *args):
        super().__init__()
        self.app_manager = app_manager
        self.operation = operation
        self.args = args
    def run(self):
        try:
            if self.operation == 'list_apps':
                app_type, include_details = self.args
                self.progress_update.emit(f'Listando aplicativos ({app_type.value})...')
                apps = self.app_manager.list_packages(app_type, include_details)
                self.apps_loaded.emit(apps)
                return
            if self.operation == 'list_mdm_apps':
                include_details = self.args[0]
                self.progress_update.emit('Detectando aplicativos MDM...')
                apps = self.app_manager.list_mdm_packages(include_details)
                self.apps_loaded.emit(apps)
                return
            if self.operation == 'force_stop':
                package_name = self.args[0]
                self.progress_update.emit(f'Parando {package_name}...')
                result = self.app_manager.force_stop_app(package_name)
                message = f'App {package_name} {'parado' if result else 'falhou'}'
                self.operation_complete.emit(message, result)
                return
            if self.operation == 'clear_cache':
                package_name = self.args[0]
                self.progress_update.emit(f'Limpando cache de {package_name}...')
                result, message = self.app_manager.clear_app_cache(package_name)
                self.operation_complete.emit(message, result)
                return
            if self.operation == 'smart_clear_cache':
                package_name = self.args[0]
                self.progress_update.emit(f'Analisando e limpando {package_name}...')
                success, message, details = self.app_manager.smart_clear_app_cache(package_name)
                self.smart_cache_result.emit(message, success, details)
                return
            if self.operation == 'batch_clear_cache':
                package_names = self.args[0]
                total = len(package_names)
                for i, package_name in enumerate(package_names):
                    self.progress_update.emit(f'Limpando cache {i + 1}/{total}: {package_name}')
                    self.app_manager.clear_app_cache(package_name)
                self.operation_complete.emit(f'Cache limpo para {total} aplicativos', True)
                return
            if self.operation == 'smart_batch_clear_cache':
                package_names = self.args[0]
                total = len(package_names)
                browser_count = 0
                success_count = 0
                for i, package_name in enumerate(package_names):
                    self.progress_update.emit(f'Processando {i + 1}/{total}: {package_name}')
                    success, message, details = self.app_manager.smart_clear_app_cache(package_name)
                    if success:
                        success_count += 1
                    if details.get('type', '').startswith('browser'):
                        browser_count += 1
                batch_message = f'Processados {total} apps: {success_count} sucessos'
                if browser_count > 0:
                    batch_message += f'\n´©Å {browser_count} navegador(es) com limita├º├Áes'
                self.operation_complete.emit(batch_message, True)
                return
            if self.operation == 'uninstall':
                package_name = self.args[0]
                self.progress_update.emit(f'Desinstalando {package_name}...')
                result = self.app_manager.uninstall_app(package_name)
                message = f'App {package_name} {'desinstalado' if result else 'falhou na desinstala├º├úo'}'
                self.operation_complete.emit(message, result)
                return
            if self.operation == 'batch_uninstall':
                package_names = self.args[0]
                total = len(package_names)
                success_count = 0
                for i, package_name in enumerate(package_names):
                    self.progress_update.emit(f'Desinstalando {i + 1}/{total}: {package_name}')
                    result = self.app_manager.uninstall_app(package_name)
                    if result:
                        success_count += 1
                self.operation_complete.emit(f'Desinstala├º├úo conclu├¡da: {success_count}/{total} sucessos', True)
                return
            if self.operation == 'install_apk':
                apk_path = self.args[0]
                self.progress_update.emit('Instalando aplicativo...')
                success, message = self.app_manager.install_apk_from_file(apk_path)
                self.operation_complete.emit(message, success)
                return
            if self.operation == 'install_existing':
                package_name = self.args[0]
                self.progress_update.emit('Restaurando aplicativo...')
                success, message = self.app_manager.install_existing_package(package_name)
                self.operation_complete.emit(message, success)
                return
            if self.operation == 'recover_launcher':
                package_name = self.args[0]
                self.progress_update.emit('Restaurando launcher...')
                success, message = self.app_manager.install_existing_package(package_name)
                if success:
                    pass
            try:
                self.app_manager._execute_adb_command(['shell', 'cmd', 'role', 'add-role-holder', 'android.app.role.HOME', package_name], timeout=15)
            except Exception:
                pass
            else:
                self.operation_complete.emit(message, success)
                return
        except Exception as e:
            self.operation_complete.emit('Ocorreu um erro inesperado. Tente novamente.', False)
class ADBAppManagerView(QWidget):
    def __init__(self, parent=None, adb_manager=None):
        super().__init__(parent)
        self.adb_manager = adb_manager
        self.app_manager = ADBAppManager(adb_manager) if adb_manager else None
        self.translation_manager = TranslationManager.get_instance()
        self.current_apps = []
        self.selected_apps = []
        self.setup_ui()
        self.setup_connections()
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_apps)
        self._show_initial_message()
    def setup_ui(self):
        layout = QVBoxLayout(self)
        beta_warning = self.create_beta_warning()
        layout.addWidget(beta_warning)
        header_layout = self.create_header()
        layout.addLayout(header_layout)
        main_splitter = QSplitter(Qt.Horizontal)
        apps_widget = self.create_apps_widget()
        main_splitter.addWidget(apps_widget)
        info_widget = self.create_info_widget()
        main_splitter.addWidget(info_widget)
        main_splitter.setSizes([700, 300])
        layout.addWidget(main_splitter)
        self.create_status_bar(layout)
        self.apply_styles()
    def create_beta_warning(self):
        warning_frame = QFrame()
        warning_frame.setFrameStyle(QFrame.StyledPanel)
        warning_frame.setMaximumHeight(40)
        warning_frame.setStyleSheet('\n            QFrame {\n                background-color: #dc3545;\n                border: 1px solid #c82333;\n                border-radius: 4px;\n                margin: 2px;\n                padding: 3px;\n                max-height: 40px;\n            }\n        ')
        layout = QHBoxLayout(warning_frame)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)
        icon_label = QLabel('[!]')
        icon_label.setFont(QFont('Arial', 14))
        icon_label.setStyleSheet('color: white; background: transparent; border: none;')
        layout.addWidget(icon_label)
        text_label = QLabel('ATEN├ç├âO: Ferramenta em desenvolvimento - Use com responsabilidade')
        text_label.setFont(QFont('Arial', 11, QFont.Bold))
        text_label.setStyleSheet('color: white; background: transparent; border: none; font-weight: bold;')
        text_label.setWordWrap(True)
        layout.addWidget(text_label, 1)
        info_label = QLabel('ÔÇó Testado parcialmente')
        info_label.setFont(QFont('Arial', 9, QFont.Bold))
        info_label.setStyleSheet('color: #f8f9fa; background: transparent; border: none; font-weight: bold;')
        layout.addWidget(info_label)
        close_btn = QPushButton('├ù')
        close_btn.setFixedSize(16, 16)
        close_btn.setStyleSheet('\n            QPushButton {\n                background: transparent;\n                border: none;\n                color: white;\n                font-size: 12px;\n                border-radius: 8px;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background: #c82333;\n            }\n        ')
        close_btn.clicked.connect(warning_frame.hide)
        layout.addWidget(close_btn)
        return warning_frame
    def create_header(self):
        layout = QHBoxLayout()
        filter_group = QGroupBox('Filtros')
        filter_layout = QHBoxLayout(filter_group)
        self.app_type_combo = QComboBox()
        self.app_type_combo.addItems(['Todos', 'Usu├írio', 'Sistema', 'Desabilitados', 'Habilitados', 'MDM Detectados', 'Removidos'])
        filter_layout.addWidget(QLabel('Tipo:'))
        filter_layout.addWidget(self.app_type_combo)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText('Buscar aplicativo...')
        filter_layout.addWidget(QLabel('Buscar:'))
        filter_layout.addWidget(self.search_edit)
        self.details_checkbox = QCheckBox('Carregar detalhes')
        filter_layout.addWidget(self.details_checkbox)
        layout.addWidget(filter_group)
        action_group = QGroupBox('A├º├Áes')
        action_layout = QHBoxLayout(action_group)
        self.refresh_btn = QPushButton('Buscar')
        self.stop_selected_btn = QPushButton('Parar Selecionados')
        self.clear_cache_btn = QPushButton('Limpar Cache')
        self.uninstall_btn = QPushButton('Desinstalar')
        self.batch_clear_btn = QPushButton('Limpeza em Lote')
        try:
            icons_path = PathManager.get_resource_path('icons_svg')
            _icon_map = {self.refresh_btn: 'arrow-clockwise.svg', self.stop_selected_btn: 'power.svg', self.clear_cache_btn: 'hdd.svg', self.uninstall_btn: 'shield-shaded.svg', self.batch_clear_btn: 'check2-all.svg'}
            for btn, svg_name in _icon_map.items():
                import os
                svg_path = os.path.join(icons_path, svg_name)
                if os.path.exists(svg_path):
                    btn.setIcon(QIcon(svg_path))
                    btn.setIconSize(QSize(16, 16))
        except Exception:
            pass
        self.uninstall_btn.setStyleSheet('\n            QPushButton { background-color: #e53935; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px; border: none; font-size: 9pt; }\n            QPushButton:hover { background-color: #c62828; }\n            QPushButton:pressed { background-color: #b71c1c; }\n            QPushButton:disabled { background-color: #BDBDBD; color: #757575; }\n        ')
        action_layout.addWidget(self.refresh_btn)
        action_layout.addWidget(self.stop_selected_btn)
        action_layout.addWidget(self.clear_cache_btn)
        action_layout.addWidget(self.uninstall_btn)
        action_layout.addWidget(self.batch_clear_btn)
        self.install_apk_btn = QPushButton('Instalar APK')
        self.install_apk_btn.setStyleSheet('\n            QPushButton { background-color: #17a2b8; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px; border: none; font-size: 9pt; }\n            QPushButton:hover { background-color: #138496; }\n            QPushButton:pressed { background-color: #117a8b; }\n            QPushButton:disabled { background-color: #BDBDBD; color: #757575; }\n        ')
        action_layout.addWidget(self.install_apk_btn)
        separator = QLabel('|')
        separator.setStyleSheet('color: #CCCCCC; font-size: 16px; padding: 0 5px;')
        action_layout.addWidget(separator)
        self.advanced_actions_combo = QComboBox()
        self.advanced_actions_combo.addItems(['Selecione uma acao...', 'Congelar App', 'Descongelar App', 'Desabilitar App', 'Habilitar App', 'Restaurar App', 'Recuperar Launcher'])
        self.advanced_actions_combo.setMinimumWidth(180)
        action_layout.addWidget(self.advanced_actions_combo)
        self.apply_advanced_btn = QPushButton('Aplicar')
        self.apply_advanced_btn.setStyleSheet('\n            QPushButton {\n                background-color: #28a745;\n                color: white;\n                font-weight: bold;\n                padding: 8px 15px;\n            }\n            QPushButton:hover {\n                background-color: #218838;\n            }\n            QPushButton:pressed {\n                background-color: #1e7e34;\n            }\n            QPushButton:disabled {\n                background-color: #CCCCCC;\n                color: #666666;\n            }\n        ')
        action_layout.addWidget(self.apply_advanced_btn)
        layout.addWidget(action_group)
        return layout
    def create_apps_widget(self):
        widget = QGroupBox('Aplicativos Instalados')
        layout = QVBoxLayout(widget)
        self.apps_table = QTableWidget()
        self.apps_table.setColumnCount(2)
        self.apps_table.setHorizontalHeaderLabels(['', 'Application Name'])
        self.apps_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.apps_table.setAlternatingRowColors(True)
        self.apps_table.horizontalHeader().setStretchLastSection(True)
        self.apps_table.setContextMenuPolicy(Qt.CustomContextMenu)
        header = self.apps_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.apps_table.setIconSize(QSize(28, 28))
        table_font = self.apps_table.font()
        table_font.setPointSize(table_font.pointSize() + 2)
        self.apps_table.setFont(table_font)
        layout.addWidget(self.apps_table)
        return widget
    def create_info_widget(self):
        widget = QGroupBox('Informa├º├Áes')
        layout = QVBoxLayout(widget)
        self.system_info_label = QLabel('Sistema: Carregando...')
        layout.addWidget(self.system_info_label)
        stats_group = QGroupBox('Estat├¡sticas')
        stats_layout = QGridLayout(stats_group)
        self.total_apps_label = QLabel('Total: 0')
        self.system_apps_label = QLabel('Sistema: 0')
        self.user_apps_label = QLabel('Usu├írio: 0')
        self.selected_apps_label = QLabel('Selecionados: 0')
        stats_layout.addWidget(self.total_apps_label, 0, 0)
        stats_layout.addWidget(self.system_apps_label, 0, 1)
        stats_layout.addWidget(self.user_apps_label, 1, 0)
        stats_layout.addWidget(self.selected_apps_label, 1, 1)
        layout.addWidget(stats_group)
        log_group = QGroupBox('Log de Opera├º├Áes')
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        clear_log_btn = QPushButton('Limpar Log')
        clear_log_btn.clicked.connect(self.log_text.clear)
        log_layout.addWidget(clear_log_btn)
        layout.addWidget(log_group)
        return widget
    def create_status_bar(self, layout):
        status_layout = QHBoxLayout()
        self.status_label = QLabel('Pronto')
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.progress_bar)
        layout.addLayout(status_layout)
    def _show_initial_message(self):
        self.add_log('Gerenciador de Apps pronto!')
        self.add_log("Clique em 'Buscar' para carregar os aplicativos.")
        self.add_log('Isso evita lentidao no carregamento do sistema.')
        self.status_label.setText('Pronto - Clique em Buscar para carregar apps')
    def setup_connections(self):
        self.refresh_btn.clicked.connect(self.refresh_apps)
        self.stop_selected_btn.clicked.connect(self.stop_selected_apps)
        self.clear_cache_btn.clicked.connect(self.clear_cache_selected_smart)
        self.uninstall_btn.clicked.connect(self.uninstall_selected)
        self.batch_clear_btn.clicked.connect(self.batch_clear_cache_smart)
        self.install_apk_btn.clicked.connect(self.do_install_apk)
        self.apply_advanced_btn.clicked.connect(self.apply_advanced_action)
        self.app_type_combo.currentTextChanged.connect(self.filter_apps)
        self.search_edit.textChanged.connect(self.filter_apps)
        self.apps_table.itemChanged.connect(self.on_item_changed)
        self.apps_table.customContextMenuRequested.connect(self.show_context_menu)
    def apply_styles(self):
        self.setStyleSheet('\n            QGroupBox {\n                font-weight: bold;\n                border: 1px solid #e0e0e0;\n                border-radius: 4px;\n                margin: 4px;\n                padding-top: 10px;\n            }\n            QGroupBox::title {\n                subcontrol-origin: margin;\n                left: 10px;\n                padding: 0 5px 0 5px;\n            }\n            QPushButton {\n                padding: 6px 12px;\n                border: none;\n                border-radius: 4px;\n                background-color: #2196F3;\n                color: white;\n                font-weight: bold;\n                font-size: 9pt;\n            }\n            QPushButton:hover {\n                background-color: #1976D2;\n            }\n            QPushButton:pressed {\n                background-color: #0D47A1;\n            }\n            QPushButton:disabled {\n                background-color: #BDBDBD;\n                color: #757575;\n            }\n            QTableWidget {\n                gridline-color: #e0e0e0;\n                selection-background-color: #1976D2;\n            }\n            QTableWidget::item {\n                padding: 5px;\n            }\n                ')
    def _check_device_connection(self):
        if not self.adb_manager:
            QMessageBox.critical(self, self.translation_manager.get_text('adb_not_available_title'), f'{self.translation_manager.get_text('adb_not_available_message')}<br><br>{self.translation_manager.get_text('adb_not_found_details')}')
            return False
        try:
            device_connected = self.adb_manager.check_device()
            if not device_connected:
                message = ''.join(['<b>', f'{self.translation_manager.get_text('android_not_detected')}', '</b><br><br><b>', f'{self.translation_manager.get_text('android_follow_steps')}', '</b><br><br><b>', f'{self.translation_manager.get_text('android_step1_title')}', '</b><br>', f'{self.translation_manager.get_text('android_step1_connect')}', '<br>', f'{self.translation_manager.get_text('android_step1_cable')}', '<br><br><b>', f'{self.translation_manager.get_text('android_step2_title')}', '</b><br>ÔÇó <i>', f'{self.translation_manager.get_text('android_step2_goto')}', '</i><br>', f'{self.translation_manager.get_text('android_step2_tap')}', '<br>', f'{self.translation_manager.get_text('android_step2_appear')}', '<br><br><b>', f'{self.translation_manager.get_text('android_step3_title')}', '</b><br>ÔÇó <i>', f'{self.translation_manager.get_text('android_step3_goto')}', '</i><br>', f'{self.translation_manager.get_text('android_step3_enable')}', '<br>', f'{self.translation_manager.get_text('android_step3_install')}', '<br><br><b>', f'{self.translation_manager.get_text('android_step4_title')}', '</b><br>', f'{self.translation_manager.get_text('android_step4_message')}', '<br>', f'{self.translation_manager.get_text('android_step4_check')}', '<br>', f'{self.translation_manager.get_text('android_step4_allow')}', '<br><br><b>', f'{self.translation_manager.get_text('android_try_again')}', '</b><br><br><b>', f'{self.translation_manager.get_text('android_tip_title')}', '</b><br>', f'{self.translation_manager.get_text('android_tip_drivers')}', '<br>', f'{self.translation_manager.get_text('android_tip_reinstall')}', '<br>', f'{self.translation_manager.get_text('android_tip_cable')}'])
                QMessageBox.warning(self, self.translation_manager.get_text('android_not_connected_title'), message)
                return False
        except Exception as e:
            QMessageBox.critical(self, self.translation_manager.get_text('connection_error_title'), f' <b>{self.translation_manager.get_text('connection_error_title')}:</b><br><br><i>{str(e)}</i><br><br>{self.translation_manager.get_text('connection_error_verify')}<br>{self.translation_manager.get_text('connection_check_usb')}<br>{self.translation_manager.get_text('connection_check_debugging')}<br>{self.translation_manager.get_text('connection_check_authorization')}<br>{self.translation_manager.get_text('connection_check_drivers')}<br><br><b>{self.translation_manager.get_text('connection_tip_technicians')}</b>')
            return False
        return True
    def load_apps(self):
        if not self.app_manager:
            self.add_log('Erro: ADB Manager n├úo dispon├¡vel')
            return
        if not self._check_device_connection():
            return
        app_type = self.get_selected_app_type()
        include_details = self.details_checkbox.isChecked()
        self.show_progress('Carregando aplicativos...')
        if app_type == 'MDM':
            self.thread = AppManagerThread(self.app_manager, 'list_mdm_apps', include_details)
            self.thread.progress_update.connect(self.show_progress)
            self.thread.apps_loaded.connect(self.on_apps_loaded)
            self.thread.start()
            return
        if app_type == 'REMOVED':
            self.thread = AppManagerThread(self.app_manager, 'list_removed')
            self.thread.progress_update.connect(self.show_progress)
            self.thread.apps_loaded.connect(self.on_apps_loaded)
            self.thread.start()
            return
        self.thread = AppManagerThread(self.app_manager, 'list_apps', app_type, include_details)
        self.thread.progress_update.connect(self.show_progress)
        self.thread.apps_loaded.connect(self.on_apps_loaded)
        self.thread.start()
    def get_selected_app_type(self):
        combo_text = self.app_type_combo.currentText()
        type_map = {'Todos': AppType.ALL, 'Usu├írio': AppType.USER, 'Sistema': AppType.SYSTEM, 'Desabilitados': AppType.DISABLED, 'Habilitados': AppType.ENABLED, 'MDM Detectados': 'MDM', 'Removidos': 'REMOVED'}
        return type_map.get(combo_text, AppType.ALL)
    def on_apps_loaded(self, apps):
        self.current_apps = apps
        self.populate_apps_table()
        self.update_stats()
        self.hide_progress()
        self.add_log(f'Carregados {len(apps)} aplicativos')
        if self.app_manager:
            if hasattr(self.app_manager, 'adb_manager'):
                self.app_manager.adb_manager.finalize_adb_operation()
    def populate_apps_table(self):
        self.apps_table.setRowCount(len(self.current_apps))
        for row, app in enumerate(self.current_apps):
            checkbox = QCheckBox()
            checkbox.stateChanged.connect(self.update_selected_apps)
            self.apps_table.setCellWidget(row, 0, checkbox)
            app_name_item = QTableWidgetItem(app.package_name)
            app_name_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            icon_path = 'app/assets/icons/android.png'
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                app_name_item.setIcon(icon)
            if hasattr(app, 'is_suspended') and app.is_suspended:
                app_name_item.setBackground(QColor(240, 248, 255))
            elif not app.is_enabled:
                app_name_item.setBackground(QColor(250, 250, 250))
            self.apps_table.setItem(row, 1, app_name_item)
            continue
    def update_stats(self):
        total = len(self.current_apps)
        system = sum((1 for app in self.current_apps if app.is_system))
        user = total - system
        selected = len(self.selected_apps)
        self.total_apps_label.setText(f'Total: {total}')
        self.system_apps_label.setText(f'Sistema: {system}')
        self.user_apps_label.setText(f'Usu├írio: {user}')
        self.selected_apps_label.setText(f'Selecionados: {selected}')
        if self.app_manager:
            try:
                android_version = self.app_manager._get_android_version()
                self.system_info_label.setText(f'Sistema: {android_version.value[1]}')
                return
            except Exception:
                self.system_info_label.setText('Sistema: Erro ao detectar')
    def filter_apps(self):
        search_text = self.search_edit.text().lower()
        for row in range(self.apps_table.rowCount()):
            package_name = self.apps_table.item(row, 1).text().lower()
            show_row = search_text in package_name or not search_text
            self.apps_table.setRowHidden(row, not show_row)
    def refresh_apps(self):
        self.load_apps()
    def stop_selected_apps(self):
        if not self._check_device_connection():
            return
        selected_packages = self.get_selected_packages()
        if not selected_packages:
            QMessageBox.warning(self, 'Aviso', 'Nenhum aplicativo selecionado')
            return
        reply = QMessageBox.question(self, 'Confirmar', f'Parar {len(selected_packages)} aplicativo(s) selecionado(s)?', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.execute_batch_operation('force_stop', selected_packages)
    def clear_cache_selected_smart(self):
        if not self._check_device_connection():
            return
        selected_packages = self.get_selected_packages()
        if not selected_packages:
            QMessageBox.warning(self, 'Aviso', 'Nenhum aplicativo selecionado')
            return
        if len(selected_packages) == 1:
            package_name = selected_packages[0]
            self.show_progress(f'Analisando {package_name}...')
            self.thread = AppManagerThread(self.app_manager, 'smart_clear_cache', package_name)
            self.thread.progress_update.connect(self.show_progress)
            self.thread.smart_cache_result.connect(self.on_smart_cache_result)
            self.thread.start()
            return
        reply = QMessageBox.question(self, 'Confirmar Limpeza em Lote', f'Processar limpeza de cache para {len(selected_packages)} aplicativo(s)?\n\n Navegadores ter├úo tratamento especial com feedback detalhado.', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.execute_smart_batch_operation('smart_batch_clear_cache', selected_packages)
    def batch_clear_cache_smart(self):
        if not self._check_device_connection():
            return
        dialog = BatchClearDialog(self, self.app_manager)
        if dialog.exec_() == QDialog.Accepted:
            packages = dialog.get_selected_packages()
            if packages:
                existing_packages = []
                for pkg in packages:
                    if self.app_manager._package_exists(pkg):
                        existing_packages.append(pkg)
                if existing_packages:
                    reply = QMessageBox.question(self, '´©Å Confirmar Limpeza em Lote', f' **Executar limpeza em {len(existing_packages)} aplicativo(s)?**\n\n **Apps selecionados:**\n' + '\n'.join((f'ÔÇó {pkg.split('.')[-1]}' for pkg in existing_packages[:8])) + (f'\n... e mais {len(existing_packages) - 8}' if len(existing_packages) > 8 else '') + '\n\n Navegadores ter├úo tratamento especial com feedback detalhado.', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                    if reply == QMessageBox.Yes:
                        self.execute_smart_batch_operation('smart_batch_clear_cache', existing_packages)
                        return
                    return
                QMessageBox.information(self, 'Informa├º├úo', 'Nenhum dos aplicativos selecionados foi encontrado no dispositivo.')
                return
            QMessageBox.information(self, 'Nenhuma Categoria Selecionada', ' **Por favor, selecione ao menos uma categoria:**\n\n Cache de navegadores\n Cache de redes sociais\n Cache de jogos\n\n **Dica:** Para aplicativos espec├¡ficos, use a sele├º├úo individual na lista principal.')
    def uninstall_selected(self):
        if not self._check_device_connection():
            return
        selected_packages = self.get_selected_packages()
        if not selected_packages:
            QMessageBox.warning(self, 'Aviso', 'Nenhum aplicativo selecionado')
            return
        reply = QMessageBox.warning(self, '´©Å ATEN├ç├âO - DESINSTALAR APLICATIVOS', f'Voc├¬ est├í prestes a DESINSTALAR {len(selected_packages)} aplicativo(s)!\n\n´©Å ESTA A├ç├âO ├ë IRREVERS├ìVEL!\n\nAplicativos selecionados:\n' + '\n'.join((f'ÔÇó {pkg}' for pkg in selected_packages[:5])) + (f'\n... e mais {len(selected_packages) - 5}' if len(selected_packages) > 5 else '') + '\n\n´©Å APLICATIVOS DE SISTEMA podem causar problemas no dispositivo!\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.execute_batch_operation('uninstall', selected_packages)
    def execute_batch_operation(self, operation, packages):
        self.show_progress(f'Executando {operation} em {len(packages)} apps...')
        if operation == 'force_stop':
            for package in packages:
                self.thread = AppManagerThread(self.app_manager, 'force_stop', package)
                self.thread.operation_complete.connect(self.on_operation_complete)
                self.thread.start()
            return
        if operation == 'clear_cache':
            self.thread = AppManagerThread(self.app_manager, 'batch_clear_cache', packages)
            self.thread.progress_update.connect(self.show_progress)
            self.thread.operation_complete.connect(self.on_operation_complete)
            self.thread.start()
            return
        if operation == 'uninstall':
            self.thread = AppManagerThread(self.app_manager, 'batch_uninstall', packages)
            self.thread.progress_update.connect(self.show_progress)
            self.thread.operation_complete.connect(self.on_operation_complete)
            self.thread.start()
    def execute_smart_batch_operation(self, operation, packages):
        self.show_progress(f'Processando {len(packages)} aplicativos...')
        self.thread = AppManagerThread(self.app_manager, operation, packages)
        self.thread.progress_update.connect(self.show_progress)
        self.thread.operation_complete.connect(self.on_operation_complete)
        self.thread.start()
    def on_operation_complete(self, message, success):
        self.add_log(message)
        if success:
            self.refresh_apps()
        elif self.app_manager and hasattr(self.app_manager, 'adb_manager'):
            self.app_manager.adb_manager.finalize_adb_operation()
        self.hide_progress()
    def on_smart_cache_result(self, message, success, details):
        self.hide_progress()
        self.add_log(message)
        self.show_smart_cache_dialog(message, success, details)
        if success:
            if self._should_refresh_after_cache_operation(details):
                self.refresh_apps()
    def _should_refresh_after_cache_operation(self, details):
        operation_type = details.get('type', 'unknown')
        refresh_types = {'regular_app_success', 'browser_partial_success', 'browser_system_optimization'}
        return operation_type in refresh_types
    def show_smart_cache_dialog(self, message, success, details):
        dialog_type = details.get('type', 'unknown')
        user_message = details.get('message', message)
        if dialog_type == 'browser_partial_success':
            self.show_browser_partial_success_dialog(details)
            return
        if dialog_type == 'browser_system_optimization':
            self.show_browser_optimization_dialog(details)
            return
        if dialog_type == 'browser_limitation':
            self.show_browser_limitation_dialog(details)
            return
        if dialog_type == 'regular_app_success':
            self.show_regular_app_success_dialog(details)
            return
        if dialog_type == 'legacy_limitation':
            self.show_legacy_limitation_dialog(details)
            return
        if dialog_type == 'error':
            QMessageBox.critical(self, 'Erro', user_message)
            return
        if success:
            QMessageBox.information(self, 'Sucesso', user_message)
            return
        QMessageBox.warning(self, 'Aviso', user_message)
    def show_browser_partial_success_dialog(self, details):
        browser_name = details.get('browser_name', 'Navegador')
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(f' {browser_name} - Limpeza Processada')
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText(details.get('message', ''))
        msg_box.addButton(' Entendi', QMessageBox.AcceptRole)
        msg_box.addButton(' Como limpar manualmente?', QMessageBox.HelpRole)
        result = msg_box.exec_()
        if result == 1:
            self.show_manual_browser_cleanup_help(browser_name)
    def show_browser_optimization_dialog(self, details):
        browser_name = details.get('browser_name', 'Navegador')
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(f' Sistema Otimizado para {browser_name}')
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText(details.get('message', ''))
        msg_box.addButton(' Entendi', QMessageBox.AcceptRole)
        msg_box.addButton(' Limpar navegador manualmente', QMessageBox.HelpRole)
        result = msg_box.exec_()
        if result == 1:
            self.show_manual_browser_cleanup_help(browser_name)
    def show_browser_limitation_dialog(self, details):
        browser_name = details.get('browser_name', 'Navegador')
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(f' {browser_name} - Cache Protegido')
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setText(details.get('message', ''))
        msg_box.addButton(' Limpar manualmente', QMessageBox.AcceptRole)
        if details.get('radical_option_available', False):
            msg_box.addButton('´©Å Limpar TUDO (perde dados)', QMessageBox.DestructiveRole)
        msg_box.addButton(' Cancelar', QMessageBox.RejectRole)
        result = msg_box.exec_()
        if result == 0:
            self.show_manual_browser_cleanup_help(browser_name)
            return
        if result == 1:
            if details.get('radical_option_available', False):
                self.offer_radical_cleanup(details.get('app_name', browser_name))
    def show_regular_app_success_dialog(self, details):
        app_name = details.get('app_name', 'Aplicativo')
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(f' {app_name} - Cache Limpo!')
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText(details.get('message', ''))
        msg_box.addButton(' Perfeito!', QMessageBox.AcceptRole)
        msg_box.exec_()
    def show_legacy_limitation_dialog(self, details):
        app_name = details.get('app_name', 'Aplicativo')
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(f' {app_name} - Limita├º├úo do Android')
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setText(details.get('message', ''))
        msg_box.addButton(' Limpar manualmente', QMessageBox.AcceptRole)
        if details.get('full_clear_available', False):
            msg_box.addButton('´©Å Limpar TUDO', QMessageBox.DestructiveRole)
        msg_box.addButton(' Cancelar', QMessageBox.RejectRole)
        result = msg_box.exec_()
        if result == 0:
            self.show_manual_app_cleanup_help(app_name)
            return
        if result == 1:
            if details.get('full_clear_available', False):
                self.offer_radical_cleanup(app_name)
    def show_manual_browser_cleanup_help(self, browser_name):
        help_messages = {'Google Chrome': '1. Abrir Chrome\n2. Menu (Ôï«) > Configura├º├Áes\n3. Privacidade e seguran├ºa\n4. Limpar dados de navega├º├úo\n5. Selecionar: Cache, Cookies\n6. Limpar dados', 'Mozilla Firefox': '1. Abrir Firefox\n2. Menu (Ôëí) > Configura├º├Áes\n3. Privacidade e seguran├ºa\n4. Limpar dados\n5. Selecionar: Cache\n6. Limpar', 'Samsung Internet': '1. Abrir Samsung Internet\n2. Menu (Ôëí) > Configura├º├Áes\n3. Dados de navega├º├úo\n4. Excluir dados de navega├º├úo\n5. Selecionar itens\n6. Excluir', 'Opera': '1. Abrir Opera\n2. Menu > Configura├º├Áes\n3. Privacidade e seguran├ºa\n4. Limpar dados de navega├º├úo\n5. Selecionar cache\n6. Limpar dados'}
        instructions = help_messages.get(browser_name, "1. Abrir o navegador\n2. Procurar Menu ou Configura├º├Áes\n3. Buscar 'Privacidade' ou 'Dados'\n4. Limpar cache e cookies")
        QMessageBox.information(self, f' Como limpar {browser_name} manualmente', f' **INSTRU├ç├òES PASSO A PASSO:**\n\n{instructions}\n\n **DICA:** Isso limpa 100% do cache!\n\n´©Å **AVISO:** Pode solicitar login novamente em sites.')
    def show_manual_app_cleanup_help(self, app_name):
        QMessageBox.information(self, f' Como limpar {app_name} manualmente', f' **INSTRU├ç├òES:**\n\n1. Abrir: **Configura├º├Áes** do Android\n2. Ir em: **Apps** ou **Aplicativos**\n3. Procurar: **{app_name}**\n4. Tocar em: **Armazenamento**\n5. Tocar em: **Limpar Cache**\n\n **RESULTADO:** Cache ser├í limpo 100%!\n\n **SEGURO:** N├úo remove dados do usu├írio.')
    def offer_radical_cleanup(self, app_name):
        reply = QMessageBox.critical(self, f'´©Å ATEN├ç├âO - Limpar TODOS os dados de {app_name}', f' **ESTA A├ç├âO ├ë IRREVERS├ìVEL!**\n\n **O QUE SER├ü REMOVIDO:**\nÔÇó Cache e arquivos tempor├írios\nÔÇó Configura├º├Áes e prefer├¬ncias\nÔÇó Contas e senhas salvas\nÔÇó Hist├│rico e dados do usu├írio\n\n **DEPOIS DA LIMPEZA:**\nÔÇó {app_name} voltar├í ao estado inicial\nÔÇó Ser├í necess├írio configurar tudo novamente\n\n **Deseja continuar mesmo assim?**', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.perform_radical_cleanup(app_name)
    def perform_radical_cleanup(self, app_name):
        try:
            package_name = None
            for app in self.current_apps:
                if app.app_name != app_name:
                    if not app.package_name.split('.')[-1].title() == app_name:
                        continue
                package_name = app.package_name
                break
            if package_name:
                result, message = self.app_manager.clear_all_data(package_name)
                if result:
                    QMessageBox.information(self, ' Limpeza Completa Realizada', f' **{app_name} foi completamente limpo!**\n\n Todos os dados foram removidos\n Cache foi limpo 100%\n App voltou ao estado inicial\n\n **Pr├│ximos passos:**\nÔÇó Reconfigurar o app conforme necess├írio\nÔÇó Fazer login novamente se aplic├ível')
                    self.refresh_apps()
                    return
                QMessageBox.warning(self, ' Erro na Limpeza', f'N├úo foi poss├¡vel limpar todos os dados de {app_name}:\n\n{message}')
                return
            QMessageBox.warning(self, 'Erro', f'N├úo foi poss├¡vel encontrar o pacote para {app_name}')
            return
        except Exception as e:
            QMessageBox.critical(self, 'Erro Inesperado', f'Erro ao tentar limpar {app_name}:\n\n{str(e)}')
    def show_context_menu(self, position):
        if self.apps_table.itemAt(position):
            menu = QMenu()
            force_stop_action = QAction('Parar App', self)
            clear_cache_action = QAction('Limpar Cache', self)
            clear_data_action = QAction('Limpar Dados', self)
            freeze_action = QAction('Congelar App', self)
            unfreeze_action = QAction('Descongelar App', self)
            enable_action = QAction('Habilitar App', self)
            uninstall_action = QAction('Desinstalar', self)
            app_info_action = QAction('Informacoes', self)
            open_settings_action = QAction('Configuracoes', self)
            menu.addAction(force_stop_action)
            menu.addAction(clear_cache_action)
            menu.addAction(clear_data_action)
            menu.addSeparator()
            menu.addAction(freeze_action)
            menu.addAction(unfreeze_action)
            menu.addAction(enable_action)
            menu.addSeparator()
            menu.addAction(uninstall_action)
            menu.addSeparator()
            menu.addAction(app_info_action)
            menu.addAction(open_settings_action)
            force_stop_action.triggered.connect(self.context_force_stop)
            clear_cache_action.triggered.connect(self.context_clear_cache)
            clear_data_action.triggered.connect(self.context_clear_data)
            uninstall_action.triggered.connect(self.context_uninstall)
            app_info_action.triggered.connect(self.context_app_info)
            open_settings_action.triggered.connect(self.context_open_settings)
            freeze_action.triggered.connect(self.context_freeze_app)
            unfreeze_action.triggered.connect(self.context_unfreeze_app)
            enable_action.triggered.connect(self.context_enable_app)
            menu.exec_(self.apps_table.mapToGlobal(position))
    def context_force_stop(self):
        if not self._check_device_connection():
            return
        current_row = self.apps_table.currentRow()
        if current_row >= 0:
            package_name = self.apps_table.item(current_row, 1).text()
            self.thread = AppManagerThread(self.app_manager, 'force_stop', package_name)
            self.thread.operation_complete.connect(self.on_operation_complete)
            self.thread.start()
    def context_clear_cache(self):
        if not self._check_device_connection():
            return
        current_row = self.apps_table.currentRow()
        if current_row >= 0:
            package_name = self.apps_table.item(current_row, 1).text()
            self.show_progress(f'Analisando {package_name}...')
            self.thread = AppManagerThread(self.app_manager, 'smart_clear_cache', package_name)
            self.thread.progress_update.connect(self.show_progress)
            self.thread.smart_cache_result.connect(self.on_smart_cache_result)
            self.thread.start()
    def context_clear_data(self):
        if not self._check_device_connection():
            return
        current_row = self.apps_table.currentRow()
        if current_row >= 0:
            package_name = self.apps_table.item(current_row, 1).text()
            reply = QMessageBox.warning(self, 'Aten├º├úo', f'Limpar TODOS os dados do {package_name}?\n\nIsso ir├í apagar configura├º├Áes, contas e dados do usu├írio!', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                result, message = self.app_manager.clear_all_data(package_name)
                self.add_log(message)
                if result:
                    self.refresh_apps()
    def context_uninstall(self):
        if not self._check_device_connection():
            return
        current_row = self.apps_table.currentRow()
        if current_row >= 0:
            package_name = self.apps_table.item(current_row, 1).text()
            reply = QMessageBox.critical(self, '´©Å ATEN├ç├âO - DESINSTALAR APLICATIVO', f'Voc├¬ est├í prestes a DESINSTALAR:\n\n {package_name}\n\n´©Å ESTA A├ç├âO ├ë IRREVERS├ìVEL!\n\n´©Å Se for app de SISTEMA pode causar problemas!\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.thread = AppManagerThread(self.app_manager, 'uninstall', package_name)
                self.thread.operation_complete.connect(self.on_operation_complete)
                self.thread.start()
    def context_app_info(self):
        if not self._check_device_connection():
            return
        current_row = self.apps_table.currentRow()
        if current_row >= 0:
            package_name = self.apps_table.item(current_row, 1).text()
            app_info = self.app_manager.get_app_info(package_name)
            if app_info:
                info_dialog = AppInfoDialog(app_info, self)
                info_dialog.exec_()
    def context_open_settings(self):
        if not self._check_device_connection():
            return
        current_row = self.apps_table.currentRow()
        if current_row >= 0:
            package_name = self.apps_table.item(current_row, 1).text()
            success = self.app_manager.open_app_settings(package_name)
            if success:
                self.add_log(f'Configura├º├Áes abertas para {package_name}')
                return
            self.add_log(f'Erro ao abrir configura├º├Áes de {package_name}')
    def context_freeze_app(self):
        if not self._check_device_connection():
            return
        current_row = self.apps_table.currentRow()
        if current_row >= 0:
            package_name = self.apps_table.item(current_row, 1).text()
            reply = QMessageBox.question(self, '´©Å Congelar Aplicativo', f'Deseja CONGELAR o aplicativo?\n\n {package_name}\n\n´©Å O QUE ACONTECE:\nÔÇó App ficar├í invis├¡vel na lista de apps\nÔÇó N├úo poder├í ser executado\nÔÇó N├úo receber├í notifica├º├Áes\nÔÇó Pode ser descongelado depois\n\n IDEAL PARA: Bloatware e apps de sistema indesejados\n\n Android 9+ suportado', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.show_progress(f'Congelando {package_name}...')
                success, message = self.app_manager.freeze_app(package_name)
                self.hide_progress()
                self.add_log(message)
                if success:
                    QMessageBox.information(self, ' App Congelado', f' **Sucesso!**\n\n {package_name} foi congelado\n\n App n├úo aparecer├í mais na lista\n N├úo poder├í ser executado\n Economia de recursos\n\n Para descongelar: Menu de contexto > Descongelar')
                    self.refresh_apps()
                    return
                QMessageBox.warning(self, ' Erro ao Congelar', f'N├úo foi poss├¡vel congelar o aplicativo:\n\n{message}\n\n´©Å Poss├¡veis causas:\nÔÇó Android < 9 (n├úo suportado)\nÔÇó App protegido pelo sistema\nÔÇó Permiss├Áes insuficientes')
    def context_unfreeze_app(self):
        if not self._check_device_connection():
            return
        current_row = self.apps_table.currentRow()
        if current_row >= 0:
            package_name = self.apps_table.item(current_row, 1).text()
            reply = QMessageBox.question(self, ' Descongelar Aplicativo', f'Deseja DESCONGELAR o aplicativo?\n\n {package_name}\n\n´©Å O QUE ACONTECE:\nÔÇó App voltar├í a aparecer na lista\nÔÇó Poder├í ser executado normalmente\nÔÇó Receber├í notifica├º├Áes novamente\n\n Continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                self.show_progress(f'Descongelando {package_name}...')
                success, message = self.app_manager.unfreeze_app(package_name)
                self.hide_progress()
                self.add_log(message)
                if success:
                    QMessageBox.information(self, ' App Descongelado', f' **Sucesso!**\n\n {package_name} foi descongelado\n\n App voltou a aparecer\n Pode ser usado normalmente\n Notifica├º├Áes restauradas')
                    self.refresh_apps()
                    return
                QMessageBox.warning(self, ' Erro ao Descongelar', f'N├úo foi poss├¡vel descongelar o aplicativo:\n\n{message}\n\nPoss├¡veis causas:\nÔÇó App protegido pelo sistema\nÔÇó Permiss├Áes insuficientes')
    def context_enable_app(self):
        if not self._check_device_connection():
            return
        current_row = self.apps_table.currentRow()
        if current_row >= 0:
            package_name = self.apps_table.item(current_row, 1).text()
            reply = QMessageBox.question(self, ' Habilitar Aplicativo', f'Deseja HABILITAR o aplicativo?\n\n {package_name}\n\n´©Å O QUE ACONTECE:\nÔÇó App voltar├í a funcionar\nÔÇó Poder├í ser executado\nÔÇó Receber├í atualiza├º├Áes\n\n Continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                self.show_progress(f'Habilitando {package_name}...')
                success, message = self.app_manager.enable_app(package_name)
                self.hide_progress()
                self.add_log(message)
                if success:
                    QMessageBox.information(self, ' App Habilitado', f' **Sucesso!**\n\n {package_name} foi habilitado\n\n App voltou a funcionar\n Pode ser usado normalmente\n Atualiza├º├Áes restauradas')
                    self.refresh_apps()
                    return
                QMessageBox.warning(self, ' Erro ao Habilitar', f'N├úo foi poss├¡vel habilitar o aplicativo:\n\n{message}\n\nPoss├¡veis causas:\nÔÇó App foi removido (use Restaurar App)\nÔÇó App protegido pelo sistema\nÔÇó Permiss├Áes insuficientes')
    def context_disable_app(self):
        if not self._check_device_connection():
            return
        current_row = self.apps_table.currentRow()
        if current_row >= 0:
            package_name = self.apps_table.item(current_row, 1).text()
            reply = QMessageBox.question(self, ' Desabilitar Aplicativo', f'Deseja DESABILITAR o aplicativo?\n\n {package_name}\n\n´©Å O QUE ACONTECE:\nÔÇó App n├úo poder├í ser executado\nÔÇó Ficar├í vis├¡vel mas inativo\nÔÇó Pode ser reabilitado depois\n\n´©Å ATEN├ç├âO: Desabilitar apps de sistema pode causar problemas!\n\n Continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.show_progress(f'Desabilitando {package_name}...')
                success, message = self.app_manager.disable_app(package_name)
                self.hide_progress()
                self.add_log(message)
                if success:
                    QMessageBox.information(self, ' App Desabilitado', f' **Sucesso!**\n\n {package_name} foi desabilitado\n\n App n├úo poder├í ser executado\n Pode ser reabilitado quando quiser')
                    self.refresh_apps()
                    return
                QMessageBox.warning(self, ' Erro ao Desabilitar', f'N├úo foi poss├¡vel desabilitar o aplicativo:\n\n{message}\n\nPoss├¡veis causas:\nÔÇó App essencial do sistema\nÔÇó Permiss├Áes insuficientes')
    def apply_advanced_action(self):
        action = self.advanced_actions_combo.currentText()
        if action == 'Selecione uma acao...':
            QMessageBox.information(self, 'Selecione uma Acao', 'Por favor, selecione uma acao no menu antes de clicar em Aplicar.')
            return
        if action == 'Recuperar Launcher':
            self.do_recover_launcher()
            self.advanced_actions_combo.setCurrentIndex(0)
            return
        current_row = self.apps_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, 'Nenhum App Selecionado', 'Por favor, selecione um aplicativo na tabela antes de aplicar esta acao.')
            return
        if action == 'Congelar App':
            self.context_freeze_app()
        elif action == 'Descongelar App':
            self.context_unfreeze_app()
        elif action == 'Desabilitar App':
            self.context_disable_app()
        elif action == 'Habilitar App':
            self.context_enable_app()
        elif action == 'Restaurar App':
            self.do_restore_app()
        self.advanced_actions_combo.setCurrentIndex(0)
    def do_install_apk(self):
        if not self._check_device_connection():
            return
        try:
            docs_path = os.path.expanduser('~/Documents')
            if not os.path.isdir(docs_path):
                docs_path = os.path.expanduser('~')
        except Exception:
            docs_path = ''
        apk_path, _ = QFileDialog.getOpenFileName(self, 'Selecionar Aplicativo', docs_path, 'Aplicativos (*.apk)')
        if not apk_path:
            return
        apk_name = os.path.basename(apk_path)
        reply = QMessageBox.question(self, 'Confirmar Instalacao', f'Deseja instalar o aplicativo?\n\n{apk_name}', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.show_progress('Instalando aplicativo...')
            self.thread = AppManagerThread(self.app_manager, 'install_apk', apk_path)
            self.thread.progress_update.connect(self.show_progress)
            self.thread.operation_complete.connect(self.on_operation_complete)
            self.thread.start()
    def do_recover_launcher(self):
        if not self._check_device_connection():
            return
        try:
            self.show_progress('Verificando launcher do dispositivo...')
            output = self.app_manager._execute_adb_command(['shell', 'cmd', 'package', 'query-activities', '--brief', '-c', 'android.intent.category.HOME', '-a', 'android.intent.action.MAIN'], timeout=15)
            real_launchers = []
            if output:
                for line in output.strip().split('\n'):
                    line = line.strip()
                    if '/' not in line:
                        continue
                    if 'FallbackHome' not in line:
                        pkg = line.split('/')[0]
                        if not pkg:
                            continue
                        if pkg != 'android':
                            real_launchers.append(pkg)
            if real_launchers:
                self.hide_progress()
                QMessageBox.information(self, 'Launcher Funcionando', f'O launcher do dispositivo esta funcionando normalmente.\n\nLauncher ativo: {real_launchers[0]}\n\nSe o aparelho estiver sem tela inicial, reinicie o dispositivo.')
                return
            direct_boot = False
            try:
                lock_output = self.app_manager._execute_adb_command(['shell', 'dumpsys', 'lock_settings'], timeout=10)
                if lock_output:
                    for lock_line in lock_output.split('\n'):
                        if 'CredentialType' not in lock_line:
                            continue
                        if 'NONE' in lock_line.upper():
                            continue
                        if not 'None' not in lock_line:
                            continue
                        direct_boot = True
            except Exception:
                logger.debug('Nao foi possivel verificar estado de bloqueio do dispositivo')
        except Exception as e:
            logger.error('Erro ao recuperar launcher: %s', e)
            self.hide_progress()
            QMessageBox.warning(self, 'Erro', 'Nao foi possivel verificar o launcher. Verifique a conexao e tente novamente.')
        self.show_progress('Buscando launchers removidos e desabilitados...')
        removed = self.app_manager.list_removed_packages()
        try:
            disabled = self.app_manager.list_disabled_packages()
        except Exception:
            disabled = []
        try:
            launcher_names = {p for p in _STATIC_PROTECTED if 'launcher' in p.lower() if 'home' in p.lower() if 'trebuchet' in p.lower()}
        except Exception as e:
            logger.error('Erro ao recuperar launcher: %s', e)
            self.hide_progress()
            QMessageBox.warning(self, 'Erro', 'Nao foi possivel verificar o launcher. Verifique a conexao e tente novamente.')
        try:
            found_launchers = [p for p in removed if p in launcher_names]
        except Exception as e:
            logger.error('Erro ao recuperar launcher: %s', e)
            self.hide_progress()
            QMessageBox.warning(self, 'Erro', 'Nao foi possivel verificar o launcher. Verifique a conexao e tente novamente.')
        try:
            found_disabled = [p for p in disabled if p in launcher_names if p not in found_launchers]
            all_found = found_launchers + found_disabled
            self.hide_progress()
            if direct_boot:
                QMessageBox.warning(self, 'Dispositivo Bloqueado', 'O dispositivo possui bloqueio de tela (PIN, padrao ou senha).\n\nO launcher nao pode iniciar enquanto o bloqueio estiver ativo.\n\nPeca a senha ao cliente, desbloqueie o aparelho e tente novamente.')
                return
            if not all_found:
                QMessageBox.warning(self, 'Nenhum Launcher Encontrado', "Nao foi possivel encontrar um launcher removido ou desabilitado no dispositivo.\n\nVoce pode usar o botao 'Instalar APK' para instalar um launcher manualmente.")
                return
            if len(all_found) == 1:
                chosen = all_found[0]
            else:
                from PyQt5.QtWidgets import QInputDialog
                chosen, ok = QInputDialog.getItem(self, 'Selecionar Launcher', 'Foram encontrados launchers removidos/desabilitados.\nSelecione qual deseja restaurar:', all_found, 0, False)
                if not ok:
                    return
            reply = QMessageBox.question(self, 'Confirmar Restauracao', f'Deseja restaurar o launcher?\n\n{chosen}\n\nApos a restauracao, pode ser necessario reiniciar o aparelho.', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.show_progress('Restaurando launcher...')
                self.thread = AppManagerThread(self.app_manager, 'recover_launcher', chosen)
                self.thread.progress_update.connect(self.show_progress)
                self.thread.operation_complete.connect(self._on_launcher_recovered)
                self.thread.start()
                return
        except Exception as e:
            logger.error('Erro ao recuperar launcher: %s', e)
            self.hide_progress()
            QMessageBox.warning(self, 'Erro', 'Nao foi possivel verificar o launcher. Verifique a conexao e tente novamente.')
    def _on_launcher_recovered(self, message, success):
        self.hide_progress()
        self.add_log(message)
        if success:
            reply = QMessageBox.question(self, 'Launcher Restaurado', f'{message}\n\nDeseja reiniciar o dispositivo agora?\n(Recomendado para aplicar a mudanca)', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    self.app_manager._execute_adb_command(['reboot'], timeout=10)
                    self.add_log('Dispositivo reiniciando...')
                except Exception:
                    QMessageBox.information(self, 'Aviso', 'Nao foi possivel reiniciar automaticamente. Reinicie o aparelho manualmente.')
                return
            return
        QMessageBox.warning(self, 'Aviso', message)
    def do_restore_app(self):
        if not self._check_device_connection():
            return
        current_row = self.apps_table.currentRow()
        if current_row < 0:
            return
        package_name = self.apps_table.item(current_row, 1).text()
        reply = QMessageBox.question(self, 'Confirmar Restauracao', f'Deseja restaurar o aplicativo?\n\n{package_name}\n\nO aplicativo sera reinstalado para o usuario atual.', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.show_progress('Restaurando aplicativo...')
            self.thread = AppManagerThread(self.app_manager, 'install_existing', package_name)
            self.thread.progress_update.connect(self.show_progress)
            self.thread.operation_complete.connect(self.on_operation_complete)
            self.thread.start()
    def on_item_changed(self, item):
        self.update_selected_apps()
    def update_selected_apps(self):
        self.selected_apps = self.get_selected_packages()
        self.update_stats()
    def show_progress(self, message):
        self.status_label.setText(message)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
    def hide_progress(self):
        self.status_label.setText('Pronto')
        self.progress_bar.setVisible(False)
    def add_log(self, message):
        timestamp = QDateTime.currentDateTime().toString('hh:mm:ss')
        self.log_text.append(f'[{timestamp}] {message}')
    def get_selected_packages(self):
        selected = []
        for row in range(self.apps_table.rowCount()):
            checkbox = self.apps_table.cellWidget(row, 0)
            if not checkbox:
                continue
            if checkbox.isChecked():
                package_name = self.apps_table.item(row, 1).text()
                selected.append(package_name)
        return selected
class BatchClearDialog(QDialog):
    def __init__(self, parent=None, app_manager=None):
        super().__init__(parent)
        self.app_manager = app_manager
        self.setWindowTitle('Limpeza em Lote')
        self.setModal(True)
        self.resize(450, 350)
        layout = QVBoxLayout(self)
        options_group = QGroupBox('Op├º├Áes de Limpeza')
        options_layout = QVBoxLayout(options_group)
        self._check_available_apps()
        self.user_apps_cb = QCheckBox('Aplicativos do usuario (use selecao individual)')
        self.user_apps_cb.setChecked(False)
        self.user_apps_cb.setEnabled(False)
        self.browser_cache_cb = QCheckBox(f' Cache de navegadores ({self.browser_count} encontrados)')
        self.social_cache_cb = QCheckBox(f' Cache de redes sociais ({self.social_count} encontrados)')
        self.games_cache_cb = QCheckBox(f' Cache de jogos ({self.games_count} encontrados)')
        self.browser_cache_cb.setEnabled(self.browser_count > 0)
        self.social_cache_cb.setEnabled(self.social_count > 0)
        self.games_cache_cb.setEnabled(self.games_count > 0)
        options_layout.addWidget(self.user_apps_cb)
        options_layout.addWidget(self.browser_cache_cb)
        options_layout.addWidget(self.social_cache_cb)
        options_layout.addWidget(self.games_cache_cb)
        if self.browser_count + self.social_count + self.games_count == 0:
            no_apps_label = QLabel('´©Å Nenhum aplicativo das categorias padr├úo encontrado.\n Use a sele├º├úo individual na tela principal.')
            no_apps_label.setStyleSheet('color: #ff6b35; font-weight: bold; padding: 10px;')
            options_layout.addWidget(no_apps_label)
        layout.addWidget(options_group)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    def _check_available_apps(self):
        self.browser_count = 0
        self.social_count = 0
        self.games_count = 0
        self.available_browsers = []
        self.available_social = []
        self.available_games = []
        if not self.app_manager:
            return
        try:
            browser_packages = ['com.android.chrome', 'com.android.browser', 'org.mozilla.firefox']
            social_packages = ['com.whatsapp', 'com.facebook.katana', 'com.instagram.android']
            games_packages = ['com.king.candycrushsaga', 'com.supercell.clashofclans']
            for pkg in browser_packages:
                if self.app_manager._package_exists(pkg):
                    self.browser_count += 1
                    self.available_browsers.append(pkg)
            for pkg in social_packages:
                if self.app_manager._package_exists(pkg):
                    self.social_count += 1
                    self.available_social.append(pkg)
            for pkg in games_packages:
                if self.app_manager._package_exists(pkg):
                    self.games_count += 1
                    self.available_games.append(pkg)
            return
        except Exception:
            return
    def get_selected_packages(self):
        packages = []
        if self.browser_cache_cb.isChecked() and self.browser_cache_cb.isEnabled():
            packages.extend(self.available_browsers)
        if self.social_cache_cb.isChecked() and self.social_cache_cb.isEnabled():
            packages.extend(self.available_social)
        if self.games_cache_cb.isChecked() and self.games_cache_cb.isEnabled():
            packages.extend(self.available_games)
        return packages
class AppInfoDialog(QDialog):
    def __init__(self, app_info, parent=None):
        super().__init__(parent)
        self.app_info = app_info
        self.setWindowTitle(f'Informa├º├Áes - {app_info.package_name}')
        self.setModal(True)
        self.resize(500, 400)
        layout = QVBoxLayout(self)
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_html = f'\n        <h3>{app_info.app_name or app_info.package_name}</h3>\n        <p><b>Pacote:</b> {app_info.package_name}</p>\n        <p><b>Vers├úo:</b> {app_info.version or 'N/A'}</p>\n        <p><b>Tipo:</b> {'Sistema' if app_info.is_system else 'Usu├írio'}</p>\n        <p><b>Status:</b> {'Habilitado' if app_info.is_enabled else 'Desabilitado'}</p>\n        '
        info_text.setHtml(info_html)
        layout.addWidget(info_text)
        close_btn = QPushButton('Fechar')
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
