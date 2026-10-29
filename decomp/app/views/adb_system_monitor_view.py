'''
Interface PyQt5 para monitoramento de sistema via ADB
Monitor de CPU/RAM em tempo real usando comando top
Desenvolvido seguindo as diretrizes RESTORECELL
'''
import sys
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QProgressBar, QTextEdit, QSplitter, QGroupBox, QSlider, QSpinBox, QCheckBox, QComboBox, QTabWidget, QHeaderView, QAbstractItemView, QFileDialog, QMessageBox, QFrame, QDialog, QApplication, QListWidget, QListWidgetItem)
from PyQt5.QtCore import (Qt, QThread, pyqtSignal, QTimer, QDateTime)
from PyQt5.QtGui import (QFont, QColor, QPalette, QPixmap, QPainter, QPen)
from collections import deque
import json
import logging
import re
from datetime import datetime
from app.utils.adb_system_monitor import ADBSystemMonitor, AlertLevel
from app.utils.adb_app_manager import ADBAppManager
from app.utils.translation_manager import TranslationManager
logger = logging.getLogger(__name__)
class MonitorThread(QThread):
    '''Thread para monitoramento em tempo real'''
    data_updated = pyqtSignal(dict, list)
    alert_triggered = pyqtSignal(dict)
    def __init__(self, system_monitor):
        super().__init__()
        self.system_monitor = system_monitor
        self.running = False
    def run(self):
        '''Executa o loop de monitoramento'''
        def monitor_callback(system_info, processes):
            if system_info:
                if processes:
                    system_dict = system_info.__dict__ if hasattr(system_info, '__dict__') else system_info
                    process_list = [p.__dict__ if hasattr(p, '__dict__') else p for p in processes]
                    self.data_updated.emit(system_dict, process_list)
        def alert_callback(alert):
            alert_dict = alert.__dict__ if hasattr(alert, '__dict__') else alert
            self.alert_triggered.emit(alert_dict)
        try:
            self.system_monitor.add_alert_callback(alert_callback)
            success = self.system_monitor.start_monitoring(monitor_callback)
            if not success:
                logger.error('Falha ao iniciar monitoramento do sistema')
            try:
                self.system_monitor.stop_monitoring()
            except Exception as e:
                logger.error(f'Erro ao parar monitoramento: {str(e)}')
            else:
                return
        except Exception as e:
            logger.error(f'Erro no MonitorThread: {str(e)}')
        try:
            self.system_monitor.stop_monitoring()
        except Exception as e:
            logger.error(f'Erro ao parar monitoramento: {str(e)}')
    def stop(self):
        '''Para o monitoramento'''
        self.running = False
        self.quit()
class ADBSystemMonitorView(QWidget):
    '''Interface principal do monitor de sistema'''
    def __init__(self, parent=None, adb_manager=None):
        super().__init__(parent)
        self.adb_manager = adb_manager
        self.system_monitor = ADBSystemMonitor(adb_manager) if adb_manager else None
        self.translation_manager = TranslationManager.get_instance()
        self.monitor_thread = None
        self.is_monitoring = False
        self.last_alert_processes = {}
        self.alert_cooldown = 10
        self.setup_ui()
        self.setup_connections()
        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self.update_ui)
        self.ui_timer.start(3000)
        self.device_check_timer = QTimer()
        self.device_check_timer.timeout.connect(self.check_device_status)
        self.update_counter = 0
    def setup_ui(self):
        '''Configura a interface do usu├írio'''
        layout = QVBoxLayout(self)
        beta_warning = self.create_beta_warning()
        layout.addWidget(beta_warning)
        controls = self.create_controls()
        layout.addWidget(controls)
        tabs = QTabWidget()
        processes_tab = self.create_processes_tab()
        tabs.addTab(processes_tab, 'Processos')
        alerts_tab = self.create_alerts_tab()
        tabs.addTab(alerts_tab, 'Alertas')
        settings_tab = self.create_settings_tab()
        tabs.addTab(settings_tab, 'Configuracoes')
        layout.addWidget(tabs)
        self.create_status_bar(layout)
        self.apply_styles()
    def create_beta_warning(self):
        '''Cria aviso com fundo vermelho e texto em negrito'''
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
        text_label = QLabel('ATEN├ç├âO: Monitor em desenvolvimento - Use com responsabilidade')
        text_label.setFont(QFont('Arial', 11, QFont.Bold))
        text_label.setStyleSheet('color: white; background: transparent; border: none; font-weight: bold;')
        text_label.setWordWrap(True)
        layout.addWidget(text_label, 1)
        info_label = QLabel('ÔÇó Dados podem variar')
        info_label.setFont(QFont('Arial', 9, QFont.Bold))
        info_label.setStyleSheet('color: #f8f9fa; background: transparent; border: none; font-weight: bold;')
        layout.addWidget(info_label)
        close_btn = QPushButton('├ù')
        close_btn.setFixedSize(16, 16)
        close_btn.setStyleSheet('\n            QPushButton {\n                background: transparent;\n                border: none;\n                color: white;\n                font-size: 12px;\n                border-radius: 8px;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background: #c82333;\n            }\n        ')
        close_btn.clicked.connect(warning_frame.hide)
        layout.addWidget(close_btn)
        return warning_frame
    def create_controls(self):
        '''Cria controles principais'''
        group = QGroupBox('Controles de Monitoramento')
        layout = QHBoxLayout(group)
        self.start_btn = QPushButton('Iniciar Monitoramento')
        self.stop_btn = QPushButton('Parar Monitoramento')
        self.stop_btn.setEnabled(False)
        self.export_btn = QPushButton('Exportar Dados')
        self.clear_btn = QPushButton('Limpar Historico')
        self.diagnostic_btn = QPushButton('Diagnostico do Sistema')
        self.diagnostic_btn.setToolTip('Executa diagn├│stico completo do dispositivo Android')
        self.diagnostic_btn.clicked.connect(self.run_system_diagnostic)
        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)
        layout.addWidget(self.diagnostic_btn)
        layout.addWidget(self.export_btn)
        layout.addWidget(self.clear_btn)
        layout.addStretch()
        self.status_indicator = QLabel('[OFF] Parado')
        self.status_indicator.setStyleSheet('font-weight: bold; color: #e53935; font-size: 9pt;')
        layout.addWidget(self.status_indicator)
        return group
    def create_processes_tab(self):
        '''Cria tab de processos melhorada com informa├º├Áes do sistema'''
        widget = QWidget()
        layout = QVBoxLayout(widget)
        system_info_group = QGroupBox('Informacoes do Sistema')
        system_layout = QGridLayout(system_info_group)
        cpu_frame = QFrame()
        cpu_frame.setFrameStyle(QFrame.StyledPanel)
        cpu_layout = QVBoxLayout(cpu_frame)
        cpu_title = QLabel('CPU')
        cpu_title.setFont(QFont('Arial', 10, QFont.Bold))
        cpu_layout.addWidget(cpu_title)
        self.cpu_usage_label = QLabel('Uso: 0%')
        self.cpu_details_label = QLabel('User: 0% | System: 0% | Idle: 0%')
        cpu_layout.addWidget(self.cpu_usage_label)
        cpu_layout.addWidget(self.cpu_details_label)
        ram_frame = QFrame()
        ram_frame.setFrameStyle(QFrame.StyledPanel)
        ram_layout = QVBoxLayout(ram_frame)
        ram_title = QLabel('RAM')
        ram_title.setFont(QFont('Arial', 10, QFont.Bold))
        ram_layout.addWidget(ram_title)
        self.ram_usage_label = QLabel('Uso: 0 MB / 0 MB (0%)')
        self.ram_details_label = QLabel('Livre: 0 MB | Buffers: 0 MB')
        ram_layout.addWidget(self.ram_usage_label)
        ram_layout.addWidget(self.ram_details_label)
        proc_frame = QFrame()
        proc_frame.setFrameStyle(QFrame.StyledPanel)
        proc_layout = QVBoxLayout(proc_frame)
        proc_title = QLabel('Processos')
        proc_title.setFont(QFont('Arial', 10, QFont.Bold))
        proc_layout.addWidget(proc_title)
        self.process_summary_label = QLabel('Total: 0 | Executando: 0')
        self.process_details_label = QLabel('Dormindo: 0 | Parados: 0 | Zumbis: 0')
        proc_layout.addWidget(self.process_summary_label)
        proc_layout.addWidget(self.process_details_label)
        load_frame = QFrame()
        load_frame.setFrameStyle(QFrame.StyledPanel)
        load_layout = QVBoxLayout(load_frame)
        load_title = QLabel('Carga do Sistema')
        load_title.setFont(QFont('Arial', 10, QFont.Bold))
        load_layout.addWidget(load_title)
        self.load_average_label = QLabel('1min: 0.00 | 5min: 0.00 | 15min: 0.00')
        self.uptime_label = QLabel('Uptime: Desconhecido')
        load_layout.addWidget(self.load_average_label)
        load_layout.addWidget(self.uptime_label)
        system_layout.addWidget(cpu_frame, 0, 0)
        system_layout.addWidget(ram_frame, 0, 1)
        system_layout.addWidget(proc_frame, 1, 0)
        system_layout.addWidget(load_frame, 1, 1)
        layout.addWidget(system_info_group)
        controls_group = QGroupBox('Controles de Processos')
        controls_layout = QHBoxLayout(controls_group)
        filter_layout = QHBoxLayout()
        self.process_refresh_btn = QPushButton('Atualizar')
        self.process_refresh_btn.setToolTip('Atualiza a lista de processos')
        filter_layout.addWidget(QLabel('Ordenar por:'))
        self.process_sort_combo = QComboBox()
        self.process_sort_combo.addItems(['CPU', 'Mem├│ria', 'PID', 'Nome'])
        self.process_sort_combo.setToolTip('Ordena processos por crit├®rio')
        filter_layout.addWidget(self.process_sort_combo)
        filter_layout.addWidget(self.process_refresh_btn)
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        filter_layout.addWidget(separator)
        self.mdm_filter_check = QCheckBox('Apenas MDM')
        self.mdm_filter_check.setToolTip('Mostra apenas processos de gerenciamento m├│vel')
        self.mdm_filter_check.stateChanged.connect(self.filter_mdm_processes)
        filter_layout.addWidget(self.mdm_filter_check)
        self.system_filter_check = QCheckBox('Apenas Sistema')
        self.system_filter_check.setToolTip('Mostra apenas processos do sistema')
        self.system_filter_check.stateChanged.connect(self.filter_system_processes)
        filter_layout.addWidget(self.system_filter_check)
        self.high_cpu_filter_check = QCheckBox('Alto CPU')
        self.high_cpu_filter_check.setToolTip('Mostra apenas processos com alto uso de CPU')
        self.high_cpu_filter_check.stateChanged.connect(self.filter_high_cpu_processes)
        filter_layout.addWidget(self.high_cpu_filter_check)
        controls_layout.addLayout(filter_layout)
        controls_layout.addStretch()
        action_layout = QHBoxLayout()
        self.kill_process_btn = QPushButton('Finalizar Processo')
        self.kill_process_btn.setToolTip('Finaliza o processo selecionado (kill)')
        self.kill_process_btn.setEnabled(False)
        self.kill_process_btn.clicked.connect(self.kill_selected_process)
        self.kill_process_btn.setStyleSheet('\n            QPushButton { background-color: #e53935; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px; border: none; font-size: 9pt; }\n            QPushButton:hover { background-color: #c62828; }\n            QPushButton:pressed { background-color: #b71c1c; }\n            QPushButton:disabled { background-color: #BDBDBD; color: #757575; }\n        ')
        self.force_kill_btn = QPushButton('Forcar Finalizacao')
        self.force_kill_btn.setToolTip('Forca finalizacao do processo (kill -9)')
        self.force_kill_btn.setEnabled(False)
        self.force_kill_btn.clicked.connect(self.force_kill_selected_process)
        self.force_kill_btn.setStyleSheet('\n            QPushButton { background-color: #b71c1c; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px; border: none; font-size: 9pt; }\n            QPushButton:hover { background-color: #880e0e; }\n            QPushButton:pressed { background-color: #6d0b0b; }\n            QPushButton:disabled { background-color: #BDBDBD; color: #757575; }\n        ')
        self.process_details_btn = QPushButton('Detalhes')
        self.process_details_btn.setToolTip('Mostra detalhes do processo selecionado')
        self.process_details_btn.setEnabled(False)
        self.process_details_btn.clicked.connect(self.show_process_details)
        action_layout.addWidget(self.kill_process_btn)
        action_layout.addWidget(self.force_kill_btn)
        action_layout.addWidget(self.process_details_btn)
        controls_layout.addLayout(action_layout)
        layout.addWidget(controls_group)
        processes_group = QGroupBox('Lista de Processos')
        processes_layout = QVBoxLayout(processes_group)
        self.processes_table = QTableWidget()
        self.processes_table.setColumnCount(8)
        self.processes_table.setHorizontalHeaderLabels(['PID', 'Nome do Processo', 'CPU %', 'RAM %', 'RAM (MB)', 'Usu├írio', 'Estado', 'Prioridade'])
        self.processes_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.processes_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.processes_table.setAlternatingRowColors(True)
        self.processes_table.setSortingEnabled(True)
        self.processes_table.horizontalHeader().setStretchLastSection(True)
        self.processes_table.verticalHeader().setVisible(False)
        self.processes_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.processes_table.selectionModel().selectionChanged.connect(self.on_process_selection_changed)
        self.processes_table.horizontalHeaderItem(0).setToolTip('ID do Processo')
        self.processes_table.horizontalHeaderItem(1).setToolTip('Nome do aplicativo/servi├ºo')
        self.processes_table.horizontalHeaderItem(2).setToolTip('Uso de CPU em porcentagem')
        self.processes_table.horizontalHeaderItem(3).setToolTip('Uso de RAM em porcentagem')
        self.processes_table.horizontalHeaderItem(4).setToolTip('RAM usada em megabytes')
        self.processes_table.horizontalHeaderItem(5).setToolTip('Usu├írio que executa o processo')
        self.processes_table.horizontalHeaderItem(6).setToolTip('Estado atual do processo')
        self.processes_table.horizontalHeaderItem(7).setToolTip('Prioridade do processo')
        processes_layout.addWidget(self.processes_table)
        states_info = QLabel('Estados: S=Dormindo, R=Executando, Z=Zumbi, T=Parado, D=Aguardando I/O')
        states_info.setFont(QFont('Arial', 8))
        states_info.setStyleSheet('color: #666; padding: 5px;')
        processes_layout.addWidget(states_info)
        layout.addWidget(processes_group)
        return widget
    def create_alerts_tab(self):
        '''Cria tab de alertas com funcionalidade de clique'''
        widget = QWidget()
        layout = QVBoxLayout(widget)
        info_label = QLabel('<b>Dica:</b> Clique em um alerta para ver detalhes do processo')
        info_label.setStyleSheet('QLabel { background-color: #e3f2fd; padding: 8px; border-radius: 4px; color: #1976d2; }')
        layout.addWidget(info_label)
        self.alerts_list = QListWidget()
        self.alerts_list.setStyleSheet("\n            QListWidget {\n                background-color: #fafafa;\n                border: 1px solid #ddd;\n                border-radius: 4px;\n                font-family: 'Consolas', 'Courier New', monospace;\n                font-size: 10px;\n            }\n            QListWidget::item {\n                padding: 8px;\n                border-bottom: 1px solid #eee;\n                margin: 2px;\n                border-radius: 3px;\n            }\n            QListWidget::item:hover {\n                background-color: #e3f2fd;\n                border: 1px solid #2196f3;\n            }\n            QListWidget::item:selected {\n                background-color: #1976d2;\n                color: white;\n            }\n        ")
        self.alerts_list.itemDoubleClicked.connect(self.on_alert_clicked)
        layout.addWidget(self.alerts_list)
        self.current_alerts = []
        controls_layout = QHBoxLayout()
        self.view_process_btn = QPushButton('Ver Processo')
        self.view_process_btn.setEnabled(False)
        self.view_process_btn.clicked.connect(self.view_alert_process)
        self.clear_alerts_btn = QPushButton('Limpar Alertas')
        self.export_alerts_btn = QPushButton('Exportar Alertas')
        controls_layout.addWidget(self.view_process_btn)
        controls_layout.addStretch()
        controls_layout.addWidget(self.clear_alerts_btn)
        controls_layout.addWidget(self.export_alerts_btn)
        layout.addLayout(controls_layout)
        self.alerts_list.itemSelectionChanged.connect(self.on_alert_selection_changed)
        return widget
    def create_settings_tab(self):
        '''Cria tab de configura├º├Áes'''
        widget = QWidget()
        layout = QVBoxLayout(widget)
        alert_group = QGroupBox('Configura├º├Áes de Alerta')
        alert_layout = QGridLayout(alert_group)
        alert_layout.addWidget(QLabel('CPU Alto (%):'), 0, 0)
        self.cpu_high_spin = QSpinBox()
        self.cpu_high_spin.setRange(1, 100)
        self.cpu_high_spin.setValue(80)
        alert_layout.addWidget(self.cpu_high_spin, 0, 1)
        alert_layout.addWidget(QLabel('CPU Cr├¡tico (%):'), 1, 0)
        self.cpu_critical_spin = QSpinBox()
        self.cpu_critical_spin.setRange(1, 100)
        self.cpu_critical_spin.setValue(95)
        alert_layout.addWidget(self.cpu_critical_spin, 1, 1)
        alert_layout.addWidget(QLabel('RAM Alto (%):'), 0, 2)
        self.memory_high_spin = QSpinBox()
        self.memory_high_spin.setRange(1, 100)
        self.memory_high_spin.setValue(80)
        alert_layout.addWidget(self.memory_high_spin, 0, 3)
        alert_layout.addWidget(QLabel('RAM Cr├¡tico (%):'), 1, 2)
        self.memory_critical_spin = QSpinBox()
        self.memory_critical_spin.setRange(1, 100)
        self.memory_critical_spin.setValue(95)
        alert_layout.addWidget(self.memory_critical_spin, 1, 3)
        apply_btn = QPushButton('Aplicar Configura├º├Áes')
        apply_btn.clicked.connect(self.apply_alert_settings)
        alert_layout.addWidget(apply_btn, 2, 0, 1, 4)
        layout.addWidget(alert_group)
        monitor_group = QGroupBox('Configura├º├Áes de Monitoramento')
        monitor_layout = QGridLayout(monitor_group)
        monitor_layout.addWidget(QLabel('Intervalo (seg):'), 0, 0)
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 60)
        self.interval_spin.setValue(2)
        monitor_layout.addWidget(self.interval_spin, 0, 1)
        monitor_layout.addWidget(QLabel('Hist├│rico m├íximo:'), 1, 0)
        self.history_spin = QSpinBox()
        self.history_spin.setRange(50, 1000)
        self.history_spin.setValue(300)
        monitor_layout.addWidget(self.history_spin, 1, 1)
        layout.addWidget(monitor_group)
        layout.addStretch()
        return widget
    def create_status_bar(self, layout):
        '''Cria barra de status'''
        status_layout = QHBoxLayout()
        self.status_label = QLabel('Pronto')
        self.last_update_label = QLabel('├Ültima atualiza├º├úo: N/A')
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.last_update_label)
        layout.addLayout(status_layout)
    def setup_connections(self):
        '''Configura conex├Áes de sinais'''
        self.start_btn.clicked.connect(self.start_monitoring)
        self.stop_btn.clicked.connect(self.stop_monitoring)
        self.export_btn.clicked.connect(self.export_data)
        self.clear_btn.clicked.connect(self.clear_history)
        self.process_refresh_btn.clicked.connect(self.refresh_processes)
        self.process_sort_combo.currentTextChanged.connect(self.refresh_processes)
        self.clear_alerts_btn.clicked.connect(self.clear_alerts)
        self.export_alerts_btn.clicked.connect(self.export_alerts)
    def apply_styles(self):
        '''Aplica estilos CSS'''
        self.setStyleSheet('\n            QGroupBox {\n                font-weight: bold;\n                border: 1px solid #e0e0e0;\n                border-radius: 4px;\n                margin: 4px;\n                padding-top: 10px;\n            }\n            QGroupBox::title {\n                subcontrol-origin: margin;\n                left: 10px;\n                padding: 0 5px 0 5px;\n            }\n            QPushButton {\n                padding: 6px 12px;\n                border: none;\n                border-radius: 4px;\n                background-color: #2196F3;\n                color: white;\n                font-weight: bold;\n                font-size: 9pt;\n            }\n            QPushButton:hover {\n                background-color: #1976D2;\n            }\n            QPushButton:pressed {\n                background-color: #0D47A1;\n            }\n            QPushButton:disabled {\n                background-color: #BDBDBD;\n                color: #757575;\n            }\n            QProgressBar {\n                border: 1px solid #e0e0e0;\n                border-radius: 3px;\n                text-align: center;\n                font-weight: bold;\n            }\n            QProgressBar::chunk {\n                background-color: #4CAF50;\n                border-radius: 2px;\n            }\n        ')
    def start_monitoring(self):
        '''Inicia o monitoramento'''
        if not self.system_monitor:
            QMessageBox.warning(self, 'Erro', 'Monitor de sistema n├úo dispon├¡vel')
            return
        if not self._check_device_connection():
            return
        if self.is_monitoring:
            return
        try:
            self.system_monitor.update_interval = self.interval_spin.value()
            self.monitor_thread = MonitorThread(self.system_monitor)
            self.monitor_thread.data_updated.connect(self.on_data_updated)
            self.monitor_thread.alert_triggered.connect(self.on_alert_triggered)
            self.monitor_thread.start()
            self.is_monitoring = True
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_indicator.setText('[ON] Monitorando')
            self.status_indicator.setStyleSheet('font-weight: bold; color: #2e7d32; font-size: 9pt;')
            self.add_log('Monitoramento iniciado')
            return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao iniciar monitoramento: {str(e)}')
    def stop_monitoring(self):
        '''Para o monitoramento'''
        if not self.is_monitoring:
            return
        try:
            if self.monitor_thread:
                self.monitor_thread.stop()
                self.monitor_thread.wait(5000)
            self.is_monitoring = False
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_indicator.setText('[OFF] Parado')
            self.status_indicator.setStyleSheet('font-weight: bold; color: #e53935; font-size: 9pt;')
            self.add_log('Monitoramento parado')
            return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao parar monitoramento: {str(e)}')
    def on_process_selection_changed(self):
        '''Callback quando sele├º├úo da tabela muda'''
        selected_rows = self.processes_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        self.kill_process_btn.setEnabled(has_selection)
        self.force_kill_btn.setEnabled(has_selection)
        self.process_details_btn.setEnabled(has_selection)
    def get_selected_process_info(self):
        '''Obt├®m informa├º├Áes do processo selecionado'''
        selected_rows = self.processes_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        pid_item = self.processes_table.item(row, 0)
        name_item = self.processes_table.item(row, 1)
        if pid_item and name_item:
            return {'pid': pid_item.text(), 'name': name_item.text().replace('[MDM] ', ''), 'row': row}
    def kill_selected_process(self):
        '''Finaliza o processo selecionado'''
        if not self._check_device_connection():
            return
        process_info = self.get_selected_process_info()
        if not process_info:
            return
        reply = QMessageBox.question(self, 'Confirmar Finalizacao', f'Deseja finalizar o processo:\n\nPID: {process_info['pid']}\nNome: {process_info['name']}\n\nATENCAO: Esta acao pode causar instabilidade no sistema.', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            success, method_used = self._try_multiple_kill_methods(process_info)
            if success:
                QMessageBox.information(self, 'Processo Finalizado', f'<b>Processo finalizado com sucesso!</b><br><br><b>Processo:</b> {process_info['name']}<br><b>PID:</b> {process_info['pid']}<br><b>Metodo usado:</b> {method_used}<br><br><b>Resultado:</b><br>ÔÇó O processo foi encerrado<br>ÔÇó Recursos de sistema liberados<br>ÔÇó Sistema ajustado automaticamente<br><br><b>Dica:</b> A lista sera atualizada automaticamente')
                self.refresh_processes()
    def _try_multiple_kill_methods(self, process_info):
        '''
Tenta m├║ltiplos m├®todos para finalizar um processo
Returns:
    tuple: (success: bool, method_used: str)
'''
        methods = [{'name': 'AM Force-Stop', 'description': 'Finaliza├º├úo via Android Manager', 'function': self._try_am_force_stop}, {'name': 'Kill Normal', 'description': 'Kill padr├úo (SIGTERM)', 'function': self._try_normal_kill}, {'name': 'PKill por Nome', 'description': 'Kill por nome do processo', 'function': self._try_pkill_by_name}, {'name': 'App Disable', 'description': 'Desabilitar aplicativo', 'function': self._try_disable_app}]
        for method in methods:
            try:
                success = method['function'](process_info)
                if success:
                    return True, method['name']
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f'M├®todo {method['name']} falhou: {str(e)}')
                continue
        self._show_all_methods_failed_error(process_info)
        return (False, 'Todos os m├®todos falharam')
    def _try_am_force_stop(self, process_info):
        '''Tenta finalizar usando am force-stop'''
        process_name = process_info['name']
        clean_name = self._extract_clean_package_name(process_name)
        if clean_name and '.' in clean_name and len(clean_name.split('.')) >= 2:
            try:
                self.adb_manager.execute_adb_command(f'shell am force-stop {clean_name}')
            except Exception:
                return False
            return True
        return False
    def _try_normal_kill(self, process_info):
        '''Tenta kill normal'''
        try:
            self.adb_manager.execute_adb_command(f'shell kill {process_info['pid']}')
            return True
        except Exception as e:
            if 'Operation not permitted' in str(e):
                return False
            raise
    def _try_pkill_by_name(self, process_info):
        '''Tenta pkill por nome'''
        try:
            process_name = process_info['name']
            clean_name = self._extract_clean_package_name(process_name)
            if clean_name:
                self.adb_manager.execute_adb_command(f'shell pkill -f {clean_name}')
                return True
        except Exception:
            pass
        return False
    def _try_disable_app(self, process_info):
        '''Tenta desabilitar o app (apenas para packages)'''
        process_name = process_info['name']
        clean_name = self._extract_clean_package_name(process_name)
        if clean_name and '.' in clean_name and len(clean_name.split('.')) >= 2:
            try:
                self.adb_manager.execute_adb_command(f'shell pm disable-user --user 0 {clean_name}')
            except Exception:
                return False
            return True
        return False
    def _extract_clean_package_name(self, process_name):
        '''
Extrai o nome limpo do package, removendo ├¡cones e par├¬nteses
Args:
    process_name: Nome do processo com prefixo (ex: "TikTok (com.zhiliaoapp.musically)")
Returns:
    str: Nome limpo do package (ex: "com.zhiliaoapp.musically")
'''
        try:
            clean_name = process_name
            icons_to_remove = ['[MDM] ', '[SYS] ', '[CPU] ', '[APP] ']
            for icon in icons_to_remove:
                clean_name = clean_name.replace(icon, '').strip()
            if '(' in clean_name and ')' in clean_name:
                start = clean_name.find('(')
                end = clean_name.find(')')
                if start < end:
                    package_name = clean_name[start + 1:end].strip()
                    if '.' in package_name and len(package_name.split('.')) >= 2:
                        return package_name
            clean_name = clean_name.strip()
            if '.' in clean_name and len(clean_name.split('.')) >= 2:
                if ' ' in clean_name:
                    potential_package = clean_name.split(' ')[0]
                    if '.' in potential_package:
                        return potential_package
                return clean_name
        except Exception:
            pass
    def _show_all_methods_failed_error(self, process_info):
        '''Mostra erro quando todos os m├®todos falham'''
        is_mdm = self.is_mdm_process(process_info['name'])
        if is_mdm:
            QMessageBox.critical(self, 'Processo MDM Protegido', f"<b>Este processo MDM n├úo pode ser finalizado!</b><br><br><b>Processo:</b> {process_info['name']}<br><b>PID:</b> {process_info['pid']}<br><br><b>Sistema MDM Detectado:</b><br>ÔÇó Este ├® um processo de gerenciamento m├│vel<br>ÔÇó Protegido por pol├¡ticas de seguran├ºa rigorosas<br>ÔÇó Projetado para resistir a tentativas de remo├º├úo<br><br><b>Status da Operacao:</b><br>ÔÇó M├║ltiplos m├®todos de finaliza├º├úo foram tentados<br>ÔÇó Todos os m├®todos dispon├¡veis falharam<br>ÔÇó O processo possui prote├º├Áes especiais<br><br><b>Opcoes Avancadas:</b><br>ÔÇó Use 'For├ºar Finaliza├º├úo' (pode funcionar em alguns casos)<br>ÔÇó Remover via configura├º├Áes do dispositivo<br>ÔÇó Factory Reset (├║ltimo recurso)<br>ÔÇó Contate administrador do MDM")
            return
        QMessageBox.warning(self, 'Processo Altamente Protegido', f"<b>N├úo foi poss├¡vel finalizar este processo:</b><br><br><b>Processo:</b> {process_info['name']}<br><b>PID:</b> {process_info['pid']}<br><br><b>Diagnostico:</b><br>ÔÇó Processo protegido pelo sistema Android<br>ÔÇó Pode ser cr├¡tico para funcionamento do sistema<br>ÔÇó Pol├¡ticas de seguran├ºa impedem finaliza├º├úo<br><br><b>Status da Operacao:</b><br>ÔÇó M├║ltiplos m├®todos de finaliza├º├úo foram tentados<br>ÔÇó Todos os m├®todos dispon├¡veis falharam<br>ÔÇó O processo possui prote├º├Áes especiais<br><br><b>Proximos Passos:</b><br>ÔÇó Tente 'For├ºar Finaliza├º├úo' (Kill -9)<br>ÔÇó Verifique se ├® realmente necess├írio finalizar<br>ÔÇó Considere se ├® processo do sistema essencial")
    def force_kill_selected_process(self):
        '''For├ºa finaliza├º├úo do processo selecionado'''
        if not self._check_device_connection():
            return
        process_info = self.get_selected_process_info()
        if not process_info:
            return
        reply = QMessageBox.question(self, 'Confirmar Finalizacao Forcada', f'Deseja FORCAR a finalizacao do processo:\n\nPID: {process_info['pid']}\nNome: {process_info['name']}\n\nATENCAO: Esta acao e irreversivel e pode causar perda de dados!\nUse apenas se o processo nao responder ao kill normal.', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            success, method_used = self._try_force_kill_methods(process_info)
            if success:
                QMessageBox.information(self, 'Force Kill Executado', f'<b>Processo for├ºadamente finalizado!</b><br><br><b>Processo:</b> {process_info['name']}<br><b>PID:</b> {process_info['pid']}<br><b>Metodo usado:</b> {method_used}<br><br><b>ATENCAO:</b><br>ÔÇó Finaliza├º├úo imediata sem cleanup<br>ÔÇó Dados n├úo salvos podem ter sido perdidos<br>ÔÇó Recursos foram liberados for├ºadamente<br><br><b>Status:</b><br>ÔÇó Processo terminado instantaneamente<br>ÔÇó Opera├º├úo irrevers├¡vel executada<br>ÔÇó Sistema pode ter se reorganizado<br><br><b>Dica:</b> Use apenas quando necessario')
                self.refresh_processes()
    def _try_force_kill_methods(self, process_info):
        '''
Tenta m├®todos force kill mais agressivos
Returns:
    tuple: (success: bool, method_used: str)
'''
        methods = [{'name': 'Kill -9 (SIGKILL)', 'description': 'Sinal SIGKILL imediato', 'function': self._try_kill_sigkill}, {'name': 'AM Force-Stop + Kill', 'description': 'Force-stop + kill combinados', 'function': self._try_am_force_stop_and_kill}, {'name': 'PKill Agressivo', 'description': 'PKill com sinal KILL', 'function': self._try_pkill_sigkill}, {'name': 'App Disable For├ºado', 'description': 'Desabilitar app permanentemente', 'function': self._try_force_disable_app}]
        for method in methods:
            try:
                success = method['function'](process_info)
                if success:
                    return True, method['name']
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f'M├®todo force {method['name']} falhou: {str(e)}')
                continue
        self._show_force_kill_failed_error(process_info)
        return (False, 'Todos os m├®todos force kill falharam')
    def _try_kill_sigkill(self, process_info):
        '''Tenta kill -9 tradicional'''
        try:
            self.adb_manager.execute_adb_command(f'shell kill -9 {process_info['pid']}')
            return True
        except Exception as e:
            if 'Operation not permitted' in str(e):
                return False
            raise
    def _try_am_force_stop_and_kill(self, process_info):
        '''Combina am force-stop com kill'''
        process_name = process_info['name']
        clean_name = self._extract_clean_package_name(process_name)
        if clean_name and '.' in clean_name and len(clean_name.split('.')) >= 2:
            try:
                self.adb_manager.execute_adb_command(f'shell am force-stop {clean_name}')
                self.adb_manager.execute_adb_command(f'shell kill -9 {process_info['pid']}')
            except Exception:
                return False
            return True
        return False
    def _try_pkill_sigkill(self, process_info):
        '''Tenta pkill com SIGKILL'''
        try:
            process_name = process_info['name']
            clean_name = self._extract_clean_package_name(process_name)
            if clean_name:
                self.adb_manager.execute_adb_command(f'shell pkill -9 -f {clean_name}')
                return True
        except Exception:
            pass
        return False
    def _try_force_disable_app(self, process_info):
        '''For├ºa desabilita├º├úo do app'''
        process_name = process_info['name']
        clean_name = self._extract_clean_package_name(process_name)
        if clean_name and '.' in clean_name and len(clean_name.split('.')) >= 2:
            try:
                self.adb_manager.execute_adb_command(f'shell pm disable {clean_name}')
            except Exception:
                return False
            return True
        return False
    def _show_force_kill_failed_error(self, process_info):
        '''Mostra erro quando todos os m├®todos force kill falham'''
        is_mdm = self.is_mdm_process(process_info['name'])
        if is_mdm:
            QMessageBox.critical(self, 'MDM Impossivel de Remover', f'<b>Este processo MDM ├® IMORTAL!</b><br><br><b>Processo:</b> {process_info['name']}<br><b>PID:</b> {process_info['pid']}<br><br><b>Protecao Maxima Detectada:</b><br>ÔÇó Processo protegido por kernel<br>ÔÇó SELinux/AppArmor impedindo acesso<br>ÔÇó Pol├¡ticas MDM de n├¡vel root<br>ÔÇó Auto-restaura├º├úo ativa<br><br><b>Status da Operacao Force Kill:</b><br>ÔÇó M├®todos de finaliza├º├úo for├ºada foram executados<br>ÔÇó Todos os m├®todos agressivos falharam<br>ÔÇó O processo ├® altamente protegido<br><br><b>Unicas Opcoes Restantes:</b><br>ÔÇó Root + modifica├º├úo de sistema<br>ÔÇó Factory Reset completo<br>ÔÇó Contato com administrador MDM<br>ÔÇó Flashing de firmware customizado')
            return
        QMessageBox.critical(self, 'Force Kill Impossivel', f'<b>Nem mesmo SIGKILL funcionou!</b><br><br><b>Processo:</b> {process_info['name']}<br><b>PID:</b> {process_info['pid']}<br><br><b>Analise Critica:</b><br>ÔÇó Processo em estado kernel imut├ível<br>ÔÇó Prote├º├úo de sistema de n├¡vel mais baixo<br>ÔÇó Pode ser thread cr├¡tica do Android<br>ÔÇó Auto-restaura├º├úo instant├ónea ativa<br><br><b>Status da Operacao Force Kill:</b><br>ÔÇó M├®todos de finaliza├º├úo for├ºada foram executados<br>ÔÇó Todos os m├®todos agressivos falharam<br>ÔÇó O processo ├® extremamente protegido<br><br><b>CONCLUSAO TECNICA:</b><br>Este processo N├âO DEVE ser finalizado!<br>├ë essencial para estabilidade do sistema.')
    def show_process_details(self):
        '''Mostra detalhes do processo selecionado com m├®todo corrigido'''
        if not self._check_device_connection():
            return
        process_info = self.get_selected_process_info()
        if not process_info:
            QMessageBox.information(self, 'Informa├º├úo', 'Selecione um processo na tabela')
            return
        try:
            pid = process_info['pid']
            if self.system_monitor:
                details = self.system_monitor.get_process_details(pid)
                if details is None:
                    QMessageBox.warning(self, 'Processo n├úo encontrado', f'O processo PID {pid} n├úo existe mais no sistema.')
                    return
                formatted_details = self.system_monitor.format_process_details_for_display(details)
            else:
                details_parts = []
            try:
                status_output = self.adb_manager.execute_adb_command(['shell', 'cat', f'/proc/{pid}/status'])
                details_parts.append(f'Status do Processo:\n{status_output}\n')
            except:
                details_parts.append('Status: N├úo dispon├¡vel\n')
            else:
                try:
                    cmdline_output = self.adb_manager.execute_adb_command(['shell', 'cat', f'/proc/{pid}/cmdline'])
                    cmdline_clean = cmdline_output.replace('\x00', ' ').strip()
                    details_parts.append(f'Linha de Comando: {cmdline_clean}\n')
                except:
                    details_parts.append('Linha de Comando: N├úo dispon├¡vel\n')
                try:
                    try:
                        maps_output = self.adb_manager.execute_adb_command(['shell', 'head', '-10', f'/proc/{pid}/maps'])
                        details_parts.append(f'Mapeamento de Mem├│ria (primeiras 10 linhas):\n{maps_output}')
                    except:
                        details_parts.append('Mapeamento de Mem├│ria: N├úo dispon├¡vel\n')
                except Exception as e:
                    QMessageBox.critical(self, 'Erro', f'Erro ao obter detalhes do processo:\n{str(e)}')
                formatted_details = '\n'.join(details_parts)
                dialog = QDialog(self)
                dialog.setWindowTitle(f'Detalhes do Processo - {process_info['name']} (PID: {pid})')
                dialog.setModal(True)
                dialog.resize(900, 700)
                layout = QVBoxLayout(dialog)
                header_layout = QHBoxLayout()
                info_label = QLabel(f'Processo: <b>{process_info['name']}</b> | PID: <b>{pid}</b> | CPU: <b>{process_info.get('cpu_percent', 0):.1f}%</b> | RAM: <b>{process_info.get('memory_mb', 0):.1f} MB</b>')
                info_label.setStyleSheet('QLabel { background-color: #f0f0f0; padding: 8px; border-radius: 4px; }')
                header_layout.addWidget(info_label)
                layout.addLayout(header_layout)
                text_edit = QTextEdit()
                text_edit.setPlainText(formatted_details)
                text_edit.setReadOnly(True)
                text_edit.setFont(QFont('Courier New', 9))
                text_edit.setStyleSheet('\n                QTextEdit {\n                    background-color: #fafafa;\n                    border: 1px solid #ddd;\n                    border-radius: 4px;\n                    padding: 8px;\n                }\n            ')
                layout.addWidget(text_edit)
                button_layout = QHBoxLayout()
                copy_btn = QPushButton('Copiar Detalhes')
                copy_btn.setStyleSheet('\n                QPushButton {\n                    background-color: #4CAF50;\n                    color: white;\n                    border: none;\n                    padding: 8px 16px;\n                    border-radius: 4px;\n                    font-weight: bold;\n                }\n                QPushButton:hover {\n                    background-color: #45a049;\n                }\n            ')
                copy_btn.clicked.connect((lambda: QApplication.clipboard().setText(text_edit.toPlainText())))
                refresh_btn = QPushButton('Atualizar')
                refresh_btn.setStyleSheet('\n                QPushButton {\n                    background-color: #2196F3;\n                    color: white;\n                    border: none;\n                    padding: 8px 16px;\n                    border-radius: 4px;\n                    font-weight: bold;\n                }\n                QPushButton:hover {\n                    background-color: #1976D2;\n                }\n            ')
                refresh_btn.clicked.connect((lambda: self._refresh_process_details(pid, text_edit, info_label)))
                close_btn = QPushButton('Fechar')
                close_btn.setStyleSheet('\n                QPushButton {\n                    background-color: #757575;\n                    color: white;\n                    border: none;\n                    padding: 8px 16px;\n                    border-radius: 4px;\n                    font-weight: bold;\n                }\n                QPushButton:hover {\n                    background-color: #616161;\n                }\n            ')
                close_btn.clicked.connect(dialog.accept)
                button_layout.addWidget(copy_btn)
                button_layout.addWidget(refresh_btn)
                button_layout.addStretch()
                button_layout.addWidget(close_btn)
                layout.addLayout(button_layout)
                dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao obter detalhes do processo:\n{str(e)}')
    def _refresh_process_details(self, pid, text_edit, info_label):
        '''Atualiza os detalhes do processo no dialog'''
        try:
            if self.system_monitor:
                details = self.system_monitor.get_process_details(pid)
                if details is None:
                    text_edit.setPlainText(f'Processo PID {pid} nao existe mais no sistema')
                    info_label.setText(f'Processo: <b>Finalizado</b> | PID: <b>{pid}</b>')
                    return
                formatted_details = self.system_monitor.format_process_details_for_display(details)
                text_edit.setPlainText(formatted_details)
                if 'additional_info' in details:
                    if 'name' in details['additional_info']:
                        process_name = details['additional_info']['name']
                        info_label.setText(f'Processo: <b>{process_name}</b> | PID: <b>{pid}</b> | Status: <b>{details['status']}</b>')
                        return
                    return
                return
        except Exception as e:
            text_edit.setPlainText('Erro ao atualizar detalhes')
    def filter_mdm_processes(self):
        '''Filtra processos MDM baseado no checkbox'''
        if hasattr(self, 'current_processes'):
            self.update_processes_table(self.current_processes)
    def filter_mdm_processes_data(self, processes):
        '''Filtra apenas processos MDM'''
        mdm_processes = []
        for process in processes:
            if self.is_mdm_process(process.get('name', '')):
                mdm_processes.append(process)
        return mdm_processes
    def is_mdm_process(self, process_name):
        '''Verifica se um processo ├® relacionado ao MDM'''
        process_lower = process_name.lower()
        mdm_patterns = ['payjoy', 'paks', 'sysdll', 'mdm', 'deviceowner', 'managedprovisioning', 'knox', 'airwatch', 'mobileiron', 'intune', 'xenmobile', 'maas360', 'mobicontrol', 'absolute', 'lookout', 'symantec', 'kaspersky', 'vmware', 'blackberry', 'checkpoint', 'zenprise', 'citrix', 'parallels', 'teamviewer', 'logmein', 'bomgar', 'miradore', 'hexnode', 'scalefusion', '42gears', 'manageengine', 'sophos', 'spiceworks', 'comodo', 'trend', 'eset', 'avast', 'avg', 'bitdefender', 'norton', 'mcafee', 'paloalto']
        return any((pattern in process_lower for pattern in mdm_patterns))
    def on_alert_triggered(self, alert):
        '''Callback quando alerta ├® disparado - vers├úo otimizada para lista'''
        try:
            timestamp = QDateTime.currentDateTime().toString('hh:mm:ss')
            current_time = QDateTime.currentDateTime().toSecsSinceEpoch()
            level_icon = '[!]'
            level_color = 'orange'
            if isinstance(alert, dict):
                alert_level = alert.get('level')
                message = alert.get('message', 'Alerta desconhecido')
                process_info = alert.get('process_info')
                process_name = None
                if 'Processo' in message:
                    pass
            try:
                process_name = message.split('Processo ')[1].split(' ')[0]
            except IndexError:
                pass
            else:
                if process_name:
                    last_alert_time = getattr(self, 'last_alert_processes', {}).get(process_name, 0)
                    alert_cooldown = getattr(self, 'alert_cooldown', 10)
                    if current_time - last_alert_time < alert_cooldown:
                        return
                    if not hasattr(self, 'last_alert_processes'):
                        self.last_alert_processes = {}
                    self.last_alert_processes[process_name] = current_time
                if hasattr(alert_level, 'value') and isinstance(alert_level.value, tuple):
                    level_icon = alert_level.value[1]
                    level_color = alert_level.value[0] if len(alert_level.value) > 2 else 'orange'
                elif isinstance(alert_level, str):
                    level_icon = alert_level
                if process_info:
                    message += f' (PID: {process_info.pid})'
                message = str(alert)
                item_text = f'[{timestamp}] {level_icon} {message}'
                if hasattr(self, 'alerts_list'):
                    self.alerts_list.addItem(item_text)
                    if self.alerts_list.count() > 100:
                        self.alerts_list.takeItem(0)
                    self.alerts_list.scrollToBottom()
                    if not hasattr(self, 'current_alerts'):
                        self.current_alerts = []
                    self.current_alerts.append(alert)
                    if len(self.current_alerts) > 100:
                        self.current_alerts = self.current_alerts[-100:]
                print(f'ALERTA: [{timestamp}] {level_icon} {message}')
        except Exception as e:
            error_msg = f'Erro ao processar alerta: {str(e)}'
            print(error_msg)
            if hasattr(self, 'alerts_list'):
                self.alerts_list.addItem(f'[{QDateTime.currentDateTime().toString('hh:mm:ss')}] {error_msg}')
    def refresh_processes(self):
        '''Atualiza lista de processos'''
        if not self._check_device_connection():
            return
        if self.system_monitor:
            try:
                sort_by = self.process_sort_combo.currentText().lower()
                processes = self.system_monitor.get_processes(limit=20, sort_by=sort_by)
            except Exception as e:
                QMessageBox.warning(self, 'Erro', f'Erro ao atualizar processos: {str(e)}')
            try:
                self.update_processes_table([p.__dict__ for p in processes])
                return
                return
            except Exception as e:
                QMessageBox.warning(self, 'Erro', f'Erro ao atualizar processos: {str(e)}')
    def apply_alert_settings(self):
        '''Aplica configura├º├Áes de alerta'''
        if self.system_monitor:
            try:
                self.system_monitor.set_alert_threshold('cpu_high', self.cpu_high_spin.value())
                self.system_monitor.set_alert_threshold('cpu_critical', self.cpu_critical_spin.value())
                self.system_monitor.set_alert_threshold('memory_high', self.memory_high_spin.value())
                self.system_monitor.set_alert_threshold('memory_critical', self.memory_critical_spin.value())
                QMessageBox.information(self, 'Sucesso', 'Configura├º├Áes aplicadas com sucesso!')
            except Exception as e:
                QMessageBox.critical(self, 'Erro', f'Erro ao aplicar configura├º├Áes: {str(e)}')
    def export_data(self):
        '''Exporta dados de monitoramento'''
        if not self.system_monitor:
            QMessageBox.warning(self, 'Erro', 'Monitor n├úo dispon├¡vel')
            return
        try:
            filename, _ = QFileDialog.getSaveFileName(self, 'Exportar Dados', 'system_monitor_data.json', 'JSON Files (*.json);;CSV Files (*.csv)')
            if filename:
                if filename.endswith('.json'):
                    success = self.system_monitor.export_report(filename, 'json')
                else:
                    success = self.system_monitor.export_report(filename, 'csv')
                if success:
                    QMessageBox.information(self, 'Sucesso', f'Dados exportados para {filename}')
                    return
                QMessageBox.warning(self, 'Erro', 'Falha ao exportar dados')
                return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao exportar: {str(e)}')
    def clear_history(self):
        '''Limpa hist├│rico de monitoramento'''
        reply = QMessageBox.question(self, 'Confirmar', 'Limpar todo o hist├│rico de monitoramento?', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.system_monitor:
                self.system_monitor.clear_history()
            self.add_log('Hist├│rico limpo')
    def clear_alerts(self):
        '''Limpa log de alertas'''
        self.alerts_list.clear()
        self.current_alerts = []
        self.view_process_btn.setEnabled(False)
    def export_alerts(self):
        '''Exporta alertas da lista'''
        try:
            filename, _ = QFileDialog.getSaveFileName(self, 'Exportar Alertas', 'alerts.txt', 'Text Files (*.txt)')
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    if hasattr(self, 'alerts_list'):
                        for i in range(self.alerts_list.count()):
                            item = self.alerts_list.item(i)
                            f.write(item.text() + '\n')
                    else:
                        f.write('Nenhum alerta dispon├¡vel\n')
                        QMessageBox.information(self, 'Sucesso', f'Alertas exportados para {filename}')
                return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao exportar alertas: {str(e)}')
    def update_ui(self):
        '''Atualiza interface periodicamente (otimizado)'''
        try:
            if self.is_monitoring:
                self.status_label.setText(f'Monitorando... (Updates: {self.update_counter})')
                return
            self.status_label.setText("Parado - Clique em 'Iniciar' para monitorar")
            return
        except Exception as e:
            self.status_label.setText(f'Erro na interface: {str(e)}')
            logger.error(f'Erro em update_ui: {str(e)}')
    def add_log(self, message):
        '''Adiciona mensagem ao log'''
        if hasattr(self, 'log_output'):
            timestamp = datetime.now().strftime('%H:%M:%S')
            self.log_output.append(f'[{timestamp}] {message}')
            if self.log_output.document().blockCount() > 1000:
                cursor = self.log_output.textCursor()
                cursor.movePosition(cursor.Start)
                cursor.movePosition(cursor.Down, cursor.KeepAnchor, 100)
                cursor.removeSelectedText()
    def _check_device_connection(self):
        '''
Verifica se h├í dispositivo conectado e mostra instru├º├Áes se necess├írio
Returns:
    bool: True se dispositivo conectado, False caso contr├írio
'''
        if not self.adb_manager:
            QMessageBox.critical(self, self.translation_manager.get_text('adb_not_available_title'), f'{self.translation_manager.get_text('adb_not_available_message')}<br><br>{self.translation_manager.get_text('adb_not_found_details')}')
            return False
        try:
            device_connected = self.adb_manager.check_device()
            if not device_connected:
                message = ''.join(['<b>', f'{self.translation_manager.get_text('android_not_detected')}', '</b><br><br><b>', f'{self.translation_manager.get_text('android_follow_steps_system')}', '</b><br><br><b>', f'{self.translation_manager.get_text('android_step1_title')}', '</b><br>', f'{self.translation_manager.get_text('android_step1_connect')}', '<br>', f'{self.translation_manager.get_text('android_step1_cable')}', '<br><br><b>', f'{self.translation_manager.get_text('android_step2_title')}', '</b><br>ÔÇó <i>', f'{self.translation_manager.get_text('android_step2_goto')}', '</i><br>', f'{self.translation_manager.get_text('android_step2_tap')}', '<br>', f'{self.translation_manager.get_text('android_step2_appear')}', '<br><br><b>', f'{self.translation_manager.get_text('android_step3_title')}', '</b><br>ÔÇó <i>', f'{self.translation_manager.get_text('android_step3_goto')}', '</i><br>', f'{self.translation_manager.get_text('android_step3_enable')}', '<br>', f'{self.translation_manager.get_text('android_step3_install')}', '<br><br><b>', f'{self.translation_manager.get_text('android_step4_title')}', '</b><br>', f'{self.translation_manager.get_text('android_step4_message')}', '<br>', f'{self.translation_manager.get_text('android_step4_check')}', '<br>', f'{self.translation_manager.get_text('android_step4_allow')}', '<br><br><b>', f'{self.translation_manager.get_text('android_try_again')}', '</b><br><br><b>', f'{self.translation_manager.get_text('android_tip_reconnect')}', '</b>'])
                QMessageBox.warning(self, self.translation_manager.get_text('android_not_connected_title'), message)
                return False
        except Exception as e:
            QMessageBox.critical(self, self.translation_manager.get_text('connection_error_title'), f'<b>{self.translation_manager.get_text('connection_error_title')}:</b><br><br><i>{str(e)}</i><br><br>{self.translation_manager.get_text('connection_error_verify')}<br>{self.translation_manager.get_text('connection_check_usb')}<br>{self.translation_manager.get_text('connection_check_debugging')}<br>{self.translation_manager.get_text('connection_check_authorization')}<br>{self.translation_manager.get_text('connection_check_drivers')}')
            return False
        return True
    def check_device_status(self):
        '''
        Verifica se h├í dispositivos conectados e atualiza o estado da interface
        '''
        if not self.adb_manager:
            self.diagnostic_btn.setEnabled(False)
            self.diagnostic_btn.setText('Diagnostico (ADB nao disponivel)')
            self.diagnostic_btn.setStyleSheet('color: gray;')
            return
        try:
            device_connected = self.adb_manager.check_device()
            if device_connected:
                self.diagnostic_btn.setEnabled(True)
                self.diagnostic_btn.setText('Diagnostico do Sistema')
                self.diagnostic_btn.setStyleSheet('color: black;')
                self.diagnostic_btn.setToolTip('Executa diagn├│stico completo do dispositivo Android')
                return
            self.diagnostic_btn.setEnabled(False)
            self.diagnostic_btn.setText('Diagnostico (Dispositivo nao conectado)')
            self.diagnostic_btn.setStyleSheet('color: gray;')
            self.diagnostic_btn.setToolTip('Conecte um dispositivo Android via USB para usar o diagn├│stico')
            return
        except Exception as e:
            self.diagnostic_btn.setEnabled(False)
            self.diagnostic_btn.setText('Diagnostico (Erro de conexao)')
            self.diagnostic_btn.setStyleSheet('color: red;')
            self.diagnostic_btn.setToolTip(f'Erro ao verificar dispositivo: {str(e)}')
    def run_system_diagnostic(self):
        '''
        Executa diagn├│stico completo do sistema Android
        Vers├úo melhorada com verifica├º├úo de dispositivos conectados
        '''
        if not self.system_monitor:
            QMessageBox.warning(self, 'Erro', 'Sistema de monitoramento n├úo inicializado')
            return
        if not self._check_device_connection():
            return
        try:
            progress_dialog = QDialog(self)
            progress_dialog.setWindowTitle('Executando Diagn├│stico')
            progress_dialog.setModal(True)
            progress_dialog.resize(300, 100)
            progress_layout = QVBoxLayout(progress_dialog)
            progress_label = QLabel('Analisando sistema Android...')
            progress_layout.addWidget(progress_label)
            progress_dialog.show()
            QApplication.processEvents()
            diagnostic = self.system_monitor.get_system_diagnostic()
            progress_dialog.close()
            results_dialog = QDialog(self)
            results_dialog.setWindowTitle('Diagnostico do Sistema Android')
            results_dialog.setModal(True)
            results_dialog.resize(900, 700)
            layout = QVBoxLayout(results_dialog)
            device_group = QGroupBox('Informacoes do Dispositivo')
            device_layout = QVBoxLayout(device_group)
            device_info = diagnostic.get('device_info', {})
            device_text = f'\nModelo: {device_info.get('model', 'N/A')}\nFabricante: {device_info.get('manufacturer', 'N/A')}\nAndroid: {device_info.get('android_version', 'N/A')} (API {device_info.get('api_level', 'N/A')})\n            '.strip()
            device_label = QLabel(device_text)
            device_label.setFont(QFont('Courier New', 9))
            device_layout.addWidget(device_label)
            layout.addWidget(device_group)
            performance_group = QGroupBox('Performance')
            performance_layout = QVBoxLayout(performance_group)
            performance = diagnostic.get('performance', {})
            performance_text = f'\nCPU: {performance.get('cpu_usage', 0):.1f}%\nRAM: {performance.get('memory_usage', 0):.1f}%\nLoad Average: {performance.get('load_average', (0, 0, 0))}\nProcessos: {performance.get('processes_total', 0)} (Zumbis: {performance.get('processes_zombie', 0)})\n            '.strip()
            performance_label = QLabel(performance_text)
            performance_label.setFont(QFont('Courier New', 9))
            performance_layout.addWidget(performance_label)
            layout.addWidget(performance_group)
            storage = diagnostic.get('storage', {})
            if storage:
                storage_group = QGroupBox('Armazenamento')
                storage_layout = QVBoxLayout(storage_group)
                storage_text = f'\nTotal: {storage.get('total_gb', 0)} GB\nUsado: {storage.get('used_gb', 0)} GB ({storage.get('used_percent', 0):.1f}%)\nDispon├¡vel: {storage.get('available_gb', 0)} GB\n                '.strip()
                storage_label = QLabel(storage_text)
                storage_label.setFont(QFont('Courier New', 9))
                storage_layout.addWidget(storage_label)
                layout.addWidget(storage_group)
            battery = diagnostic.get('battery', {})
            if battery:
                battery_group = QGroupBox('Bateria')
                battery_layout = QVBoxLayout(battery_group)
                battery_text = f'\nN├¡vel: {battery.get('level', 'N/A')}%\nTemperatura: {battery.get('temperature', 'N/A')}┬░C\n                '.strip()
                battery_label = QLabel(battery_text)
                battery_label.setFont(QFont('Courier New', 9))
                battery_layout.addWidget(battery_label)
                layout.addWidget(battery_group)
            issues = diagnostic.get('issues', [])
            if issues:
                issues_group = QGroupBox('Problemas Detectados')
                issues_layout = QVBoxLayout(issues_group)
                issues_text = QTextEdit()
                issues_text.setPlainText('\n'.join([f'ÔÇó {issue}' for issue in issues]))
                issues_text.setReadOnly(True)
                issues_text.setMaximumHeight(150)
                issues_text.setStyleSheet('background-color: #ffebee; color: #c62828;')
                issues_layout.addWidget(issues_text)
                layout.addWidget(issues_group)
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao executar diagn├│stico:\n{str(e)}')
        recommendations = diagnostic.get('recommendations', [])
        if recommendations:
            rec_group = QGroupBox('Recomendacoes')
            rec_layout = QVBoxLayout(rec_group)
            rec_text = QTextEdit()
        button_layout = QHBoxLayout()
        copy_btn = QPushButton('Copiar Relatorio')
        copy_btn.clicked.connect((lambda: self.copy_diagnostic_report(diagnostic)))
        save_btn = QPushButton('Salvar Relatorio')
        save_btn.clicked.connect((lambda: self.save_diagnostic_report(diagnostic)))
        close_btn = QPushButton('Fechar')
        close_btn.clicked.connect(results_dialog.accept)
        button_layout.addWidget(copy_btn)
        button_layout.addWidget(save_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        results_dialog.exec_()
    def copy_diagnostic_report(self, diagnostic):
        '''Copia relat├│rio de diagn├│stico para a ├írea de transfer├¬ncia'''
        try:
            report_text = self.format_diagnostic_report(diagnostic)
            QApplication.clipboard().setText(report_text)
            QMessageBox.information(self, 'Sucesso', 'Relat├│rio copiado para a ├írea de transfer├¬ncia!')
            return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao copiar relat├│rio:\n{str(e)}')
    def save_diagnostic_report(self, diagnostic):
        '''Salva relat├│rio de diagn├│stico em arquivo'''
        try:
            filename, _ = QFileDialog.getSaveFileName(self, 'Salvar Relat├│rio de Diagn├│stico', f'diagnostic_report_{diagnostic.get('timestamp', '').replace(':', '-')}.txt', 'Arquivos de Texto (*.txt);;Todos os Arquivos (*)')
            if filename:
                report_text = self.format_diagnostic_report(diagnostic)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report_text)
                    QMessageBox.information(self, 'Sucesso', f'Relat├│rio salvo em:\n{filename}')
                return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao salvar relat├│rio:\n{str(e)}')
    def format_diagnostic_report(self, diagnostic):
        '''Formata relat├│rio de diagn├│stico para texto'''
        lines = []
        lines.append('============================================================')
        lines.append('RELAT├ôRIO DE DIAGN├ôSTICO DO SISTEMA ANDROID')
        lines.append('============================================================')
        lines.append(f'Data/Hora: {diagnostic.get('timestamp', 'N/A')}')
        lines.append('')
        device_info = diagnostic.get('device_info', {})
        lines.append('INFORMA├ç├òES DO DISPOSITIVO:')
        lines.append(f'  Modelo: {device_info.get('model', 'N/A')}')
        lines.append(f'  Fabricante: {device_info.get('manufacturer', 'N/A')}')
        lines.append(f'  Android: {device_info.get('android_version', 'N/A')} (API {device_info.get('api_level', 'N/A')})')
        lines.append('')
        performance = diagnostic.get('performance', {})
        lines.append('PERFORMANCE:')
        lines.append(f'  CPU: {performance.get('cpu_usage', 0):.1f}%')
        lines.append(f'  RAM: {performance.get('memory_usage', 0):.1f}%')
        lines.append(f'  Load Average: {performance.get('load_average', (0, 0, 0))}')
        lines.append(f'  Processos: {performance.get('processes_total', 0)} (Zumbis: {performance.get('processes_zombie', 0)})')
        lines.append('')
        storage = diagnostic.get('storage', {})
        if storage:
            lines.append('ARMAZENAMENTO:')
            lines.append(f'  Total: {storage.get('total_gb', 0)} GB')
            lines.append(f'  Usado: {storage.get('used_gb', 0)} GB ({storage.get('used_percent', 0):.1f}%)')
            lines.append(f'  Dispon├¡vel: {storage.get('available_gb', 0)} GB')
            lines.append('')
        battery = diagnostic.get('battery', {})
        if battery:
            lines.append('BATERIA:')
            lines.append(f'  N├¡vel: {battery.get('level', 'N/A')}%')
            lines.append(f'  Temperatura: {battery.get('temperature', 'N/A')}┬░C')
            lines.append('')
        issues = diagnostic.get('issues', [])
        if issues:
            lines.append('PROBLEMAS DETECTADOS:')
            for issue in issues:
                lines.append(f'  ÔÇó {issue}')
            lines.append('')
        recommendations = diagnostic.get('recommendations', [])
        if recommendations:
            lines.append('RECOMENDA├ç├òES:')
            for rec in recommendations:
                lines.append(f'  ÔÇó {rec}')
            lines.append('')
        lines.append('============================================================')
        lines.append('Relat├│rio gerado pelo TECH UNION SOLUTIONS')
        lines.append('============================================================')
        return '\n'.join(lines)
    def closeEvent(self, event):
        '''Evento de fechamento'''
        if self.is_monitoring:
            self.stop_monitoring()
        if hasattr(self, 'ui_timer') and self.ui_timer.isActive():
            self.ui_timer.stop()
        if hasattr(self, 'device_check_timer') and self.device_check_timer.isActive():
            self.device_check_timer.stop()
        event.accept()
    def filter_system_processes(self):
        '''Filtra processos do sistema'''
        if hasattr(self, 'current_processes'):
            self.update_processes_table(self.current_processes)
    def filter_high_cpu_processes(self):
        '''Filtra processos com alto uso de CPU'''
        if hasattr(self, 'current_processes'):
            self.update_processes_table(self.current_processes)
    def filter_system_processes_data(self, processes):
        '''Filtra apenas processos do sistema'''
        system_processes = []
        for process in processes:
            user = process.get('user', '').lower()
            name = process.get('name', '').lower()
            if user in ('system', 'root') or name.startswith('system') or name.startswith('kernel') or name.startswith('android'):
                system_processes.append(process)
        return system_processes
    def filter_high_cpu_processes_data(self, processes):
        '''Filtra apenas processos com alto uso de CPU'''
        high_cpu_processes = []
        for process in processes:
            cpu_percent = float(process.get('cpu_percent', 0))
            if cpu_percent >= 5.0:
                high_cpu_processes.append(process)
        return high_cpu_processes
    def update_system_info_display(self, system_info):
        '''Atualiza display das informa├º├Áes do sistema'''
        try:
            if not system_info:
                return
            cpu_usage = system_info.get('cpu_usage', {})
            cpu_total = cpu_usage.get('total_used', 0)
            cpu_user = cpu_usage.get('user', 0)
            cpu_system = cpu_usage.get('system', 0)
            cpu_idle = cpu_usage.get('idle', 0)
            self.cpu_usage_label.setText(f'Uso: {cpu_total:.1f}%')
            self.cpu_details_label.setText(f'User: {cpu_user:.1f}% | System: {cpu_system:.1f}% | Idle: {cpu_idle:.1f}%')
            memory_usage = system_info.get('memory_usage', {})
            total_mb = memory_usage.get('total', 0) / 1024
            used_mb = memory_usage.get('used', 0) / 1024
            free_mb = memory_usage.get('free', 0) / 1024
            buffers_mb = memory_usage.get('buffers', 0) / 1024
            used_percent = memory_usage.get('used_percent', 0)
            self.ram_usage_label.setText(f'Uso: {used_mb:.0f} MB / {total_mb:.0f} MB ({used_percent:.1f}%)')
            self.ram_details_label.setText(f'Livre: {free_mb:.0f} MB | Buffers: {buffers_mb:.0f} MB')
            total_proc = system_info.get('processes_total', 0)
            running_proc = system_info.get('processes_running', 0)
            sleeping_proc = system_info.get('processes_sleeping', 0)
            stopped_proc = system_info.get('processes_stopped', 0)
            zombie_proc = system_info.get('processes_zombie', 0)
            self.process_summary_label.setText(f'Total: {total_proc} | Executando: {running_proc}')
            self.process_details_label.setText(f'Dormindo: {sleeping_proc} | Parados: {stopped_proc} | Zumbis: {zombie_proc}')
            load_avg = system_info.get('load_average', (0, 0, 0))
            uptime = system_info.get('uptime', 'Desconhecido')
            self.load_average_label.setText(f'1min: {load_avg[0]:.2f} | 5min: {load_avg[1]:.2f} | 15min: {load_avg[2]:.2f}')
            self.uptime_label.setText(f'Uptime: {uptime}')
            return
        except Exception as e:
            logger.error(f'Erro ao atualizar informa├º├Áes do sistema: {str(e)}')
    def update_processes_table(self, processes):
        '''Atualiza tabela de processos - vers├úo melhorada'''
        try:
            if not processes:
                return
            self.current_processes = processes
            filtered_processes = processes
            if hasattr(self, 'mdm_filter_check') and self.mdm_filter_check.isChecked():
                filtered_processes = self.filter_mdm_processes_data(filtered_processes)
            if hasattr(self, 'system_filter_check') and self.system_filter_check.isChecked():
                filtered_processes = self.filter_system_processes_data(filtered_processes)
            if hasattr(self, 'high_cpu_filter_check') and self.high_cpu_filter_check.isChecked():
                filtered_processes = self.filter_high_cpu_processes_data(filtered_processes)
            headers = ['PID', 'Nome do Processo', 'CPU %', 'RAM %', 'RAM (MB)', 'Usu├írio', 'Estado', 'Prioridade']
            if self.processes_table.columnCount() != len(headers):
                self.processes_table.setColumnCount(len(headers))
                self.processes_table.setHorizontalHeaderLabels(headers)
            current_row_count = self.processes_table.rowCount()
            needed_rows = len(filtered_processes)
            if needed_rows > current_row_count:
                for i in range(current_row_count, needed_rows):
                    self.processes_table.insertRow(i)
            elif needed_rows < current_row_count:
                for i in range(current_row_count - 1, needed_rows - 1, -1):
                    self.processes_table.removeRow(i)
            for row, process in enumerate(filtered_processes):
                pass
            try:
                original_name = str(process.get('name', 'N/A'))
                pid = process.get('pid', 0)
                if self.system_monitor:
                    enhanced_name = self.system_monitor.get_enhanced_process_name(original_name, pid)
                    process_name = enhanced_name
                elif self.is_mdm_process(original_name):
                    process_name = f'[MDM] {original_name}'
                elif process.get('user', '').lower() in ('system', 'root'):
                    process_name = f'[SYS] {original_name}'
                elif float(process.get('cpu_percent', 0)) > 10:
                    process_name = f'[CPU] {original_name}'
                else:
                    process_name = original_name
                ram_mb = float(process.get('memory_kb', 0)) / 1024
                state = str(process.get('state', 'N/A'))
                priority = process.get('priority', 0)
                self._update_table_item(row, 0, str(process.get('pid', 0)))
                self._update_table_item(row, 1, process_name)
                self._update_table_item(row, 2, f'{float(process.get('cpu_percent', 0)):.1f}%')
                self._update_table_item(row, 3, f'{float(process.get('memory_percent', 0)):.1f}%')
                self._update_table_item(row, 4, f'{ram_mb:.1f} MB')
                self._update_table_item(row, 5, str(process.get('user', 'N/A')))
                self._update_table_item(row, 6, state)
                self._update_table_item(row, 7, str(priority))
                state_item = self.processes_table.item(row, 6)
                if state_item:
                    if state == 'R':
                        state_item.setBackground(QColor(144, 238, 144))
                    elif state == 'Z':
                        state_item.setBackground(QColor(255, 182, 193))
                    elif state == 'T':
                        state_item.setBackground(QColor(255, 255, 224))
                cpu_item = self.processes_table.item(row, 2)
                if cpu_item:
                    if float(process.get('cpu_percent', 0)) > 20:
                        cpu_item.setBackground(QColor(255, 218, 185))
            except Exception as row_error:
                logger.warning(f'Erro ao processar linha {row}: {row_error}')
            else:
                if not hasattr(self, '_columns_resized'):
                    self.processes_table.resizeColumnsToContents()
                    self._columns_resized = True
        except Exception as e:
            logger.error(f'Erro ao atualizar tabela de processos: {str(e)}')
    def _update_table_item(self, row, column, text):
        '''Atualiza item da tabela de forma otimizada'''
        try:
            item = self.processes_table.item(row, column)
            if item is None:
                item = QTableWidgetItem(text)
                self.processes_table.setItem(row, column, item)
                return
            if item.text() != text:
                item.setText(text)
                return
        except Exception as e:
            item = QTableWidgetItem(text)
            self.processes_table.setItem(row, column, item)
    def on_data_updated(self, system_info, processes):
        '''Callback quando dados s├úo atualizados - vers├úo melhorada'''
        try:
            self.update_counter += 1
            self.current_processes = processes if processes else []
            if system_info:
                self.update_system_info_display(system_info)
            if processes:
                process_dicts = []
                for process in processes:
                    if hasattr(process, '__dict__'):
                        process_dicts.append(process.__dict__)
                    else:
                        process_dicts.append(process)
                self.update_processes_table(process_dicts)
            self.last_update = QDateTime.currentDateTime()
            self.last_update_label.setText(f'├Ültima atualiza├º├úo: {self.last_update.toString('hh:mm:ss')}')
            return
        except Exception as e:
            logger.error(f'Erro em on_data_updated: {str(e)}')
            self.status_label.setText(f'Erro na atualiza├º├úo: {str(e)}')
    def setup_connections(self):
        '''Configura conex├Áes de sinais'''
        self.start_btn.clicked.connect(self.start_monitoring)
        self.stop_btn.clicked.connect(self.stop_monitoring)
        self.export_btn.clicked.connect(self.export_data)
        self.clear_btn.clicked.connect(self.clear_history)
        self.process_refresh_btn.clicked.connect(self.refresh_processes)
        self.process_sort_combo.currentTextChanged.connect(self.refresh_processes)
        self.clear_alerts_btn.clicked.connect(self.clear_alerts)
        self.export_alerts_btn.clicked.connect(self.export_alerts)
    def on_alert_clicked(self, item):
        '''Callback quando um alerta ├® duplo-clicado'''
        try:
            alert_text = item.text()
            clean_text = re.sub('<[^>]*>', '', alert_text)
            pid_match = re.search('PID:\\s*(\\d+)', clean_text)
            if pid_match:
                pid = int(pid_match.group(1))
                self.show_process_details_by_pid(pid)
                return
            process_match = re.search('Processo\\s+([^\\s\\(]+)', clean_text)
            if process_match:
                process_name = process_match.group(1)
                self.show_process_details_by_name(process_name)
                return
            QMessageBox.information(self, 'Informa├º├úo', 'Este alerta n├úo cont├®m informa├º├Áes de processo espec├¡fico')
            return
        except Exception as e:
            QMessageBox.warning(self, 'Erro', f'Erro ao processar clique no alerta: {str(e)}')
    def view_alert_process(self):
        '''Mostra detalhes do processo selecionado no alerta'''
        selected_items = self.alerts_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, 'Informa├º├úo', 'Selecione um alerta na lista')
            return
        alert_text = selected_items[0].text()
        clean_text = re.sub('<[^>]*>', '', alert_text)
        pid_match = re.search('PID:\\s*(\\d+)', clean_text)
        if pid_match:
            pid = int(pid_match.group(1))
            self.show_process_details_by_pid(pid)
            return
        process_match = re.search('Processo\\s+([^\\s\\(]+)', clean_text)
        if process_match:
            process_name = process_match.group(1)
            self.show_process_details_by_name(process_name)
            return
        QMessageBox.warning(self, 'Erro', 'N├úo foi poss├¡vel extrair informa├º├Áes do processo do alerta selecionado')
    def show_process_details_by_name(self, process_name):
        '''Mostra detalhes de um processo espec├¡fico por nome'''
        try:
            process_info = None
            if hasattr(self, 'current_processes') and self.current_processes:
                for process in self.current_processes:
                    if not process.name == process_name:
                        continue
                    process_info = process
                    break
            if process_info:
                self.show_process_details_by_pid(process_info.pid)
                return
            QMessageBox.information(self, 'Processo n├úo encontrado', f"O processo '{process_name}' n├úo foi encontrado na lista atual de processos.\n\nIsso pode acontecer se o processo foi finalizado ou se a lista ainda n├úo foi atualizada.")
            return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao buscar processo por nome:\n{str(e)}')
    def show_process_details_by_pid(self, pid):
        '''Mostra detalhes de um processo espec├¡fico por PID'''
        try:
            if self.system_monitor:
                details = self.system_monitor.get_process_details(pid)
                if details is None:
                    QMessageBox.warning(self, 'Processo n├úo encontrado', f'O processo PID {pid} n├úo existe mais no sistema.')
                    return
                formatted_details = self.system_monitor.format_process_details_for_display(details)
            else:
                formatted_details = f'Sistema de monitoramento n├úo dispon├¡vel para PID {pid}'
            dialog = QDialog(self)
            dialog.setWindowTitle(f'Detalhes do Processo - PID: {pid}')
            dialog.setModal(True)
            dialog.resize(900, 700)
            layout = QVBoxLayout(dialog)
            header_layout = QHBoxLayout()
            info_label = QLabel(f'Processo PID: <b>{pid}</b>')
            info_label.setStyleSheet('QLabel { background-color: #f0f0f0; padding: 8px; border-radius: 4px; }')
            header_layout.addWidget(info_label)
            layout.addLayout(header_layout)
            text_edit = QTextEdit()
            text_edit.setPlainText(formatted_details)
            text_edit.setReadOnly(True)
            text_edit.setFont(QFont('Courier New', 9))
            text_edit.setStyleSheet('\n                QTextEdit {\n                    background-color: #fafafa;\n                    border: 1px solid #ddd;\n                    border-radius: 4px;\n                    padding: 8px;\n                }\n            ')
            layout.addWidget(text_edit)
            button_layout = QHBoxLayout()
            copy_btn = QPushButton('Copiar Detalhes')
            copy_btn.setStyleSheet('\n                QPushButton {\n                    background-color: #4CAF50;\n                    color: white;\n                    border: none;\n                    padding: 8px 16px;\n                    border-radius: 4px;\n                    font-weight: bold;\n                }\n                QPushButton:hover {\n                    background-color: #45a049;\n                }\n            ')
            copy_btn.clicked.connect((lambda: QApplication.clipboard().setText(text_edit.toPlainText())))
            close_btn = QPushButton('Fechar')
            close_btn.setStyleSheet('\n                QPushButton {\n                    background-color: #757575;\n                    color: white;\n                    border: none;\n                    padding: 8px 16px;\n                    border-radius: 4px;\n                    font-weight: bold;\n                }\n                QPushButton:hover {\n                    background-color: #616161;\n                }\n            ')
            close_btn.clicked.connect(dialog.accept)
            button_layout.addWidget(copy_btn)
            button_layout.addStretch()
            button_layout.addWidget(close_btn)
            layout.addLayout(button_layout)
            dialog.exec_()
            return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao obter detalhes do processo:\n{str(e)}')
    def on_alert_selection_changed(self):
        '''Callback quando a sele├º├úo da lista de alertas muda'''
        if hasattr(self, 'alerts_list'):
            if hasattr(self, 'view_process_btn'):
                selected_items = self.alerts_list.selectedItems()
                self.view_process_btn.setEnabled(len(selected_items) > 0)
    def on_alert_triggered(self, alert):
        '''Callback quando alerta ├® disparado (com sistema anti-spam)'''
        try:
            timestamp = QDateTime.currentDateTime().toString('hh:mm:ss')
            current_time = QDateTime.currentDateTime().toSecsSinceEpoch()
            level_icon = '[!]'
            level_color = 'orange'
            if isinstance(alert, dict):
                alert_level = alert.get('level')
                message = alert.get('message', 'Alerta desconhecido')
                process_name = None
                if 'Processo' in message:
                    pass
            try:
                process_name = message.split('Processo ')[1].split(' ')[0]
            except IndexError:
                pass
            else:
                if process_name:
                    last_alert_time = self.last_alert_processes.get(process_name, 0)
                    if current_time - last_alert_time < self.alert_cooldown:
                        return
                    self.last_alert_processes[process_name] = current_time
                if hasattr(alert_level, 'value') and isinstance(alert_level.value, tuple):
                    level_icon = alert_level.value[1]
                    level_color = alert_level.value[0] if len(alert_level.value) > 2 else 'orange'
                else:
                    if isinstance(alert_level, str):
                        level_icon = alert_level
                    message = str(alert)
                if hasattr(self, 'alerts_list'):
                    alert_item = QListWidgetItem(f'[{timestamp}] {level_icon} {message}')
                    color_map = {'high': QColor(255, 0, 0), 'medium': QColor(255, 165, 0), 'low': QColor(0, 128, 0), 'critical': QColor(128, 0, 128)}
                    item_color = color_map.get(level_color, QColor(255, 165, 0))
                    alert_item.setForeground(item_color)
                    self.alerts_list.addItem(alert_item)
                    scrollbar = self.alerts_list.verticalScrollBar()
                    scrollbar.setValue(scrollbar.maximum())
                print(f'ALERTA: [{timestamp}] {level_icon} {message}')
        except Exception as e:
            error_msg = f'Erro ao processar alerta: {str(e)}'
            print(error_msg)
            if hasattr(self, 'alerts_list'):
                self.alerts_list.addItem(f'[{QDateTime.currentDateTime().toString('hh:mm:ss')}] {error_msg}')
