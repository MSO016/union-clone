from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QMenuBar, QMenu, QAction, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QStatusBar, QLineEdit, QComboBox, QMessageBox, QScrollArea, QInputDialog)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QColor
from app.utils.path_manager import PathManager
from app.views.client_form import ClientForm
from app.views.service_order_form import ServiceOrderForm
from app.views.open_service_orders import OpenServiceOrdersDialog
from app.views.list_clients import ListClientsDialog
from app.views.service_order_history import ServiceOrderHistoryDialog
from app.views.knowledge_base_search import KnowledgeBaseSearchDialog
from app.views.add_knowledge import AddKnowledgeDialog
from app.views.daily_report import DailyReportDialog
from app.views.monthly_report import MonthlyReportDialog
from app.views.close_service_order import CloseServiceOrderDialog
from app.views.company_settings import CompanySettingsDialog
from app.utils.translation_manager import TranslationManager
from app.utils.backup_manager import BackupManager
import sqlite3
import os
from datetime import datetime, date
import re
class ServiceOrderWindow(QMainWindow):
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle(TranslationManager.get_instance().get_text('system_title'))
        self.setMinimumSize(1200, 700)
        self.todas_os = []
        self.conn = None
        self.is_admin = parent.is_admin if hasattr(parent, 'is_admin') else False
        self.translation_manager = TranslationManager.get_instance()
        self.setup_ui()
        self.carregar_dashboard()
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.carregar_dashboard)
        self.refresh_timer.start(30000)
        self.ultima_atualizacao = None
    def closeEvent(self, event):
        if hasattr(self, 'refresh_timer') and self.refresh_timer.isActive():
            self.refresh_timer.stop()
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
        event.accept()
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.criar_sidebar(main_layout)
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)
        main_layout.addWidget(content_widget)
        header_layout = QHBoxLayout()
        titulo = QLabel(self.translation_manager.get_text('dashboard_title'))
        titulo.setStyleSheet('\n            font-size: 28px; \n            font-weight: bold; \n            color: #2c3e50;\n            margin: 0px;\n        ')
        header_layout.addWidget(titulo)
        header_layout.addStretch()
        botoes_principais = QHBoxLayout()
        botoes_principais.setSpacing(10)
        self.btn_nova_os = QPushButton('Nova OS')
        self.btn_nova_os.setStyleSheet('\n            QPushButton {\n                background-color: #e74c3c;\n                color: white;\n                border: none;\n                padding: 10px 15px;\n                border-radius: 6px;\n                font-size: 13px;\n                font-weight: bold;\n                min-width: 120px;\n            }\n            QPushButton:hover {\n                background-color: #c0392b;\n            }\n            QPushButton:pressed {\n                background-color: #a93226;\n            }\n        ')
        self.btn_nova_os.setCursor(Qt.PointingHandCursor)
        self.btn_nova_os.clicked.connect(self.nova_os)
        botoes_principais.addWidget(self.btn_nova_os)
        self.btn_atualizar = QPushButton('Atualizar')
        self.btn_atualizar.setStyleSheet('\n            QPushButton {\n                background-color: #17a2b8;\n                color: white;\n                border: none;\n                padding: 10px 15px;\n                border-radius: 6px;\n                font-size: 13px;\n                font-weight: bold;\n                min-width: 100px;\n            }\n            QPushButton:hover {\n                background-color: #138496;\n            }\n            QPushButton:pressed {\n                background-color: #117a8b;\n            }\n        ')
        self.btn_atualizar.setCursor(Qt.PointingHandCursor)
        self.btn_atualizar.clicked.connect(self.refresh_manual)
        botoes_principais.addWidget(self.btn_atualizar)
        header_layout.addLayout(botoes_principais)
        layout.addLayout(header_layout)
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)
        self.os_abertas = self.criar_card_melhorado(self.translation_manager.get_text('open_orders'), '0', '#e74c3c')
        cards_layout.addWidget(self.os_abertas)
        self.os_concluidas = self.criar_card_melhorado(self.translation_manager.get_text('completed_today'), '0', '#27ae60')
        cards_layout.addWidget(self.os_concluidas)
        self.total_clientes = self.criar_card_melhorado(self.translation_manager.get_text('total_clients'), '0', '#3498db')
        cards_layout.addWidget(self.total_clientes)
        layout.addLayout(cards_layout)
        filtros_frame = QWidget()
        filtros_frame.setStyleSheet('\n            QWidget {\n                background-color: #f8f9fa;\n                border-radius: 8px;\n                padding: 15px;\n            }\n        ')
        filtros_layout = QHBoxLayout(filtros_frame)
        filtros_label = QLabel('Filtros:')
        filtros_label.setStyleSheet('\n            font-size: 16px;\n            font-weight: bold;\n            color: #2c3e50;\n            margin-right: 20px;\n        ')
        filtros_layout.addWidget(filtros_label)
        status_label = QLabel('Status:')
        status_label.setStyleSheet('font-weight: bold; color: #34495e;')
        self.status_combo = QComboBox()
        self.status_combo.setStyleSheet('\n            QComboBox {\n                padding: 8px 12px;\n                border: 2px solid #bdc3c7;\n                border-radius: 4px;\n                background-color: white;\n                min-width: 150px;\n                color: #2c3e50;\n                font-weight: bold;\n            }\n            QComboBox:focus {\n                border-color: #3498db;\n            }\n            QComboBox:hover {\n                border-color: #3498db;\n                background-color: #f8f9fa;\n            }\n        ')
        self.status_combo.addItems([self.translation_manager.get_text('all'), self.translation_manager.get_text('in_repair'), self.translation_manager.get_text('closed_success'), self.translation_manager.get_text('closed_no_solution')])
        self.status_combo.currentTextChanged.connect(self.filtrar_os)
        filtros_layout.addWidget(status_label)
        filtros_layout.addWidget(self.status_combo)
        filtros_layout.addWidget(QLabel('   '))
        busca_label = QLabel('Buscar:')
        busca_label.setStyleSheet('font-weight: bold; color: #34495e;')
        self.busca_input = QLineEdit()
        self.busca_input.setPlaceholderText(self.translation_manager.get_text('search_placeholder'))
        self.busca_input.setStyleSheet('\n            QLineEdit {\n                padding: 8px 12px;\n                border: 2px solid #bdc3c7;\n                border-radius: 4px;\n                background-color: white;\n                min-width: 250px;\n                color: #2c3e50;\n                font-weight: bold;\n            }\n            QLineEdit:focus {\n                border-color: #3498db;\n                background-color: #f8f9fa;\n            }\n            QLineEdit:hover {\n                border-color: #3498db;\n            }\n        ')
        self.busca_input.textChanged.connect(self.filtrar_os)
        filtros_layout.addWidget(busca_label)
        filtros_layout.addWidget(self.busca_input)
        filtros_layout.addStretch()
        layout.addWidget(filtros_frame)
        tabela_titulo = QLabel('Ordens de Servi├ºo Recentes')
        tabela_titulo.setStyleSheet('\n            font-size: 18px;\n            font-weight: bold;\n            color: #2c3e50;\n            margin-top: 10px;\n            margin-bottom: 10px;\n        ')
        layout.addWidget(tabela_titulo)
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(6)
        self.tabela.setHorizontalHeaderLabels(['N┬║ OS', 'Cliente', 'Dispositivo', 'Status', 'Data', 'A├º├Áes'])
        self.tabela.setStyleSheet('\n            QTableWidget {\n                gridline-color: #ecf0f1;\n                background-color: white;\n                border: 1px solid #bdc3c7;\n                border-radius: 6px;\n                selection-background-color: #3498db;\n                color: #2c3e50;\n            }\n            QHeaderView::section {\n                background-color: #34495e;\n                color: white;\n                padding: 12px;\n                border: none;\n                font-weight: bold;\n                font-size: 13px;\n            }\n            QTableWidget::item {\n                padding: 12px;\n                border: none;\n                font-size: 13px;\n            }\n            QTableWidget::item:selected {\n                background-color: #3498db;\n                color: white;\n            }\n            QTableWidget::item:hover {\n                background-color: #ecf0f1;\n            }\n        ')
        self.tabela.horizontalHeader().setStretchLastSection(True)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.itemSelectionChanged.connect(self.atualizar_cores_botoes)
        self.tabela.setColumnWidth(0, 80)
        self.tabela.setColumnWidth(1, 200)
        self.tabela.setColumnWidth(2, 250)
        self.tabela.setColumnWidth(3, 150)
        self.tabela.setColumnWidth(4, 120)
        layout.addWidget(self.tabela)
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet('\n            QStatusBar {\n                background-color: #34495e;\n                color: white;\n                padding: 5px;\n                border-top: 1px solid #2c3e50;\n            }\n            QStatusBar::item {\n                border: none;\n            }\n        ')
        self.setStatusBar(self.status_bar)
        menu_bar = self.menuBar()
        clientes_menu = menu_bar.addMenu(self.translation_manager.get_text('clients'))
        listar_clientes_action = clientes_menu.addAction(self.translation_manager.get_text('client_list'))
        listar_clientes_action.triggered.connect(self.abrir_lista_clientes)
        novo_cliente_action = clientes_menu.addAction(self.translation_manager.get_text('new_client'))
        novo_cliente_action.triggered.connect(self.novo_cliente)
        os_menu = menu_bar.addMenu(self.translation_manager.get_text('service_orders'))
        nova_os_action = os_menu.addAction(self.translation_manager.get_text('new_order'))
        nova_os_action.triggered.connect(self.nova_os)
        os_abertas_action = os_menu.addAction(self.translation_manager.get_text('open_orders'))
        os_abertas_action.triggered.connect(self.abrir_os_abertas)
        historico_action = os_menu.addAction(self.translation_manager.get_text('history'))
        historico_action.triggered.connect(self.abrir_historico)
        bc_menu = menu_bar.addMenu(self.translation_manager.get_text('knowledge_base'))
        pesquisar_bc_action = bc_menu.addAction(self.translation_manager.get_text('search_solutions'))
        pesquisar_bc_action.triggered.connect(self.pesquisar_solucoes)
        nova_solucao_action = bc_menu.addAction(self.translation_manager.get_text('new_solution'))
        nova_solucao_action.triggered.connect(self.nova_solucao)
        relatorios_menu = menu_bar.addMenu(self.translation_manager.get_text('reports'))
        relatorio_diario_action = relatorios_menu.addAction(self.translation_manager.get_text('daily_report'))
        relatorio_diario_action.triggered.connect(self.relatorio_diario)
        relatorio_mensal_action = relatorios_menu.addAction(self.translation_manager.get_text('monthly_report'))
        relatorio_mensal_action.triggered.connect(self.relatorio_mensal)
        config_menu = menu_bar.addMenu(self.translation_manager.get_text('settings'))
        company_settings_action = config_menu.addAction(self.translation_manager.get_text('company_settings'))
        company_settings_action.triggered.connect(self.abrir_config_empresa)
        backup_menu = menu_bar.addMenu('Backup')
        criar_backup_action = backup_menu.addAction('Criar Backup')
        criar_backup_action.triggered.connect(self.criar_backup)
        restaurar_backup_action = backup_menu.addAction('Restaurar Backup')
        restaurar_backup_action.triggered.connect(self.restaurar_backup)
        backup_menu.addSeparator()
        verificar_integridade_action = backup_menu.addAction('Verificar Integridade')
        verificar_integridade_action.triggered.connect(self.verificar_integridade)
        backup_menu.addSeparator()
        zerar_os_action = backup_menu.addAction('Zerar Sistema de OS')
        zerar_os_action.triggered.connect(self.zerar_sistema_os)
    def criar_sidebar(self, main_layout):
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        screen_height = screen.height()
        if screen_height <= 768:
            sidebar_width = 250
            compact_mode = True
        elif screen_height <= 900:
            sidebar_width = 270
            compact_mode = True
        else:
            sidebar_width = 280
            compact_mode = False
        sidebar_container = QWidget()
        sidebar_container.setFixedWidth(sidebar_width)
        sidebar_container.setStyleSheet('\n            QWidget {\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,\n                    stop:0 #2c3e50, stop:1 #34495e);\n                border-right: 3px solid #3498db;\n            }\n        ')
        container_layout = QVBoxLayout(sidebar_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet('\n            QScrollArea {\n                border: none;\n                background: transparent;\n            }\n            QScrollBar:vertical {\n                border: none;\n                background: rgba(52, 73, 94, 0.3);\n                width: 12px;\n                border-radius: 6px;\n                margin: 2px;\n            }\n            QScrollBar::handle:vertical {\n                background: #3498db;\n                border-radius: 6px;\n                min-height: 20px;\n            }\n            QScrollBar::handle:vertical:hover {\n                background: #2980b9;\n            }\n            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {\n                border: none;\n                background: none;\n                height: 0px;\n            }\n            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {\n                background: none;\n            }\n        ')
        sidebar = QWidget()
        sidebar.setStyleSheet('background: transparent;')
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 25, 20, 25)
        sidebar_layout.setSpacing(12)
        titulo_sidebar = QLabel('TECH UNION')
        titulo_sidebar.setStyleSheet('\n            QLabel {\n                font-size: 16px;\n                font-weight: bold;\n                color: white;\n                background-color: rgba(52, 152, 219, 0.2);\n                padding: 10px;\n                border-radius: 6px;\n                border: 2px solid #3498db;\n                text-align: center;\n            }\n        ')
        titulo_sidebar.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(titulo_sidebar)
        secao_os = QLabel('ORDENS DE SERVI├çO')
        secao_os.setStyleSheet('\n            QLabel {\n                font-size: 12px;\n                font-weight: bold;\n                color: #ecf0f1;\n                padding: 6px 0px;\n                border-bottom: 2px solid #3498db;\n                margin-top: 8px;\n                margin-bottom: 6px;\n            }\n        ')
        sidebar_layout.addWidget(secao_os)
        btn_sidebar_nova_os = self.criar_botao_sidebar('Nova Ordem de Servi├ºo', '#e74c3c', self.nova_os)
        sidebar_layout.addWidget(btn_sidebar_nova_os)
        btn_sidebar_os_abertas = self.criar_botao_sidebar('OS Abertas', '#f39c12', self.abrir_os_abertas)
        sidebar_layout.addWidget(btn_sidebar_os_abertas)
        btn_sidebar_historico = self.criar_botao_sidebar('Hist├│rico de OS', '#9b59b6', self.abrir_historico)
        sidebar_layout.addWidget(btn_sidebar_historico)
        secao_clientes = QLabel('CLIENTES')
        secao_clientes.setStyleSheet('\n            QLabel {\n                font-size: 12px;\n                font-weight: bold;\n                color: #ecf0f1;\n                padding: 6px 0px;\n                border-bottom: 2px solid #3498db;\n                margin-bottom: 6px;\n                margin-top: 10px;\n            }\n        ')
        sidebar_layout.addWidget(secao_clientes)
        btn_sidebar_novo_cliente = self.criar_botao_sidebar('Novo Cliente', '#3498db', self.novo_cliente)
        sidebar_layout.addWidget(btn_sidebar_novo_cliente)
        btn_sidebar_lista_clientes = self.criar_botao_sidebar('Lista de Clientes', '#2ecc71', self.abrir_lista_clientes)
        sidebar_layout.addWidget(btn_sidebar_lista_clientes)
        secao_bc = QLabel('BASE DE CONHECIMENTO')
        secao_bc.setStyleSheet('\n            QLabel {\n                font-size: 12px;\n                font-weight: bold;\n                color: #ecf0f1;\n                padding: 6px 0px;\n                border-bottom: 2px solid #3498db;\n                margin-bottom: 6px;\n                margin-top: 10px;\n            }\n        ')
        sidebar_layout.addWidget(secao_bc)
        btn_sidebar_pesquisar = self.criar_botao_sidebar('Pesquisar Solu├º├Áes', '#16a085', self.pesquisar_solucoes)
        sidebar_layout.addWidget(btn_sidebar_pesquisar)
        btn_sidebar_nova_solucao = self.criar_botao_sidebar('Nova Solu├º├úo', '#27ae60', self.nova_solucao)
        sidebar_layout.addWidget(btn_sidebar_nova_solucao)
        secao_relatorios = QLabel('RELAT├ôRIOS')
        secao_relatorios.setStyleSheet('\n            QLabel {\n                font-size: 12px;\n                font-weight: bold;\n                color: #ecf0f1;\n                padding: 6px 0px;\n                border-bottom: 2px solid #3498db;\n                margin-bottom: 6px;\n                margin-top: 10px;\n            }\n        ')
        sidebar_layout.addWidget(secao_relatorios)
        btn_sidebar_diario = self.criar_botao_sidebar('Relat├│rio Di├írio', '#e67e22', self.relatorio_diario)
        sidebar_layout.addWidget(btn_sidebar_diario)
        btn_sidebar_mensal = self.criar_botao_sidebar('Relat├│rio Mensal', '#d35400', self.relatorio_mensal)
        sidebar_layout.addWidget(btn_sidebar_mensal)
        secao_sistema = QLabel('SISTEMA')
        secao_sistema.setStyleSheet('\n            QLabel {\n                font-size: 12px;\n                font-weight: bold;\n                color: #ecf0f1;\n                padding: 6px 0px;\n                border-bottom: 2px solid #3498db;\n                margin-bottom: 6px;\n                margin-top: 10px;\n            }\n        ')
        sidebar_layout.addWidget(secao_sistema)
        btn_sidebar_config = self.criar_botao_sidebar('Configura├º├Áes', '#95a5a6', self.abrir_config_empresa)
        sidebar_layout.addWidget(btn_sidebar_config)
        btn_sidebar_backup = self.criar_botao_sidebar('Criar Backup', '#7f8c8d', self.criar_backup)
        sidebar_layout.addWidget(btn_sidebar_backup)
        btn_sidebar_atualizar = self.criar_botao_sidebar('Atualizar Dados', '#17a2b8', self.refresh_manual, destaque=True)
        sidebar_layout.addWidget(btn_sidebar_atualizar)
        sidebar_layout.addStretch()
        debug_info = QLabel(f'{screen.width()}x{screen_height} | {'Compacto' if compact_mode else 'Normal'}')
        debug_info.setStyleSheet('\n            QLabel {\n                font-size: 10px;\n                color: #7f8c8d;\n                padding: 4px;\n                text-align: center;\n                background: rgba(0, 0, 0, 0.1);\n                border-radius: 4px;\n                margin-top: 8px;\n            }\n        ')
        debug_info.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(debug_info)
        scroll_area.setWidget(sidebar)
        container_layout.addWidget(scroll_area)
        main_layout.addWidget(sidebar_container)
    def criar_botao_sidebar(self, texto, cor, funcao, destaque=False):
        botao = QPushButton(texto)
        if destaque:
            estilo = f'\n                QPushButton {{\n                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,\n                        stop:0 {cor}, stop:1 #1abc9c);\n                    color: white;\n                    border: none;\n                    padding: 10px 12px;\n                    border-radius: 8px;\n                    font-size: 12px;\n                    font-weight: bold;\n                    text-align: left;\n                    border: 2px solid transparent;\n                }}\n                QPushButton:hover {{\n                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,\n                        stop:0 #1abc9c, stop:1 {cor});\n                    border: 2px solid white;\n                }}\n                QPushButton:pressed {{\n                    background-color: #138496;\n                }}\n            '
        else:
            estilo = f'\n                QPushButton {{\n                    background-color: {cor};\n                    color: white;\n                    border: none;\n                    padding: 10px 12px;\n                    border-radius: 6px;\n                    font-size: 12px;\n                    font-weight: bold;\n                    text-align: left;\n                    border: 2px solid transparent;\n                }}\n                QPushButton:hover {{\n                    background-color: rgba(255, 255, 255, 0.1);\n                    border: 2px solid {cor};\n                }}\n                QPushButton:pressed {{\n                    background-color: rgba(0, 0, 0, 0.2);\n                }}\n            '
        botao.setStyleSheet(estilo)
        botao.setCursor(Qt.PointingHandCursor)
        botao.clicked.connect(funcao)
        return botao
    def criar_card(self, titulo, valor, cor):
        card = QLabel()
        card.setStyleSheet(f'\n            QLabel {{\n                background-color: {cor};\n                color: white;\n                padding: 20px;\n                border-radius: 5px;\n                min-width: 250px;\n                max-width: 250px;\n                min-height: 100px;\n                max-height: 100px;\n                font-size: 14px;\n            }}\n        ')
        card.setAlignment(Qt.AlignCenter)
        card.setText(f'{titulo}<br><br><h1>{valor}</h1>')
        return card
    def criar_card_melhorado(self, titulo, valor, cor, emoji=''):
        card = QLabel()
        card.setStyleSheet(f'\n            QLabel {{\n                background-color: {cor};\n                color: white;\n                padding: 20px;\n                border-radius: 5px;\n                min-width: 250px;\n                max-width: 250px;\n                min-height: 100px;\n                max-height: 100px;\n                font-size: 14px;\n            }}\n        ')
        card.setAlignment(Qt.AlignCenter)
        prefixo = f'{emoji} ' if str(emoji or '').strip() else ''
        card.setText(f'{prefixo}{titulo}<br><br><h1>{valor}</h1>')
        return card
    def carregar_dashboard(self):
        try:
            if self.conn:
                pass
            try:
                self.conn.close()
            except:
                pass
            else:
                self.conn = None
                self.conn = sqlite3.connect('app/database/service_orders.db')
                cursor = self.conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='service_orders'")
                if not cursor.fetchone():
                    print('DEBUG: Tabela service_orders n├úo encontrada!')
                    QMessageBox.warning(self, 'Erro', 'Tabela de ordens de servi├ºo n├úo encontrada!')
        except sqlite3.Error as e:
            print(f'DEBUG: Erro SQL: {str(e)}')
            QMessageBox.warning(self, 'Erro de Banco de Dados', f'Erro ao carregar dados: {str(e)}')
            self.todas_os = []
            self.filtrar_os()
        except Exception as e:
            print(f'DEBUG: Erro geral: {str(e)}')
            QMessageBox.warning(self, 'Erro', f'Erro inesperado ao carregar dados: {str(e)}')
            self.todas_os = []
            self.filtrar_os()
        try:
            cursor.execute("\n                SELECT COUNT(*) FROM service_orders \n                WHERE status = 'em_reparo' AND user_id = ?\n            ", (self.user_id,))
            os_abertas = cursor.fetchone()[0]
            self.os_abertas.setText(f'{self.translation_manager.get_text('open_orders')}<br><br><h1>{os_abertas}</h1>')
            data_hoje = date.today().strftime('%Y-%m-%d')
            print(f'DEBUG: Buscando OS conclu├¡das na data: {data_hoje}')
            cursor.execute("\n                SELECT COUNT(*) FROM service_orders \n                WHERE status IN ('concluido_sucesso', 'concluido_sem_solucao')\n                AND date(completion_date) = ?\n                AND user_id = ?\n            ", (data_hoje, self.user_id))
            os_hoje = cursor.fetchone()[0]
            print(f'DEBUG: OS conclu├¡das hoje encontradas: {os_hoje}')
            self.os_concluidas.setText(f'{self.translation_manager.get_text('completed_today')}<br><br><h1>{os_hoje}</h1>')
            cursor.execute("\n                SELECT completion_date, status, date(completion_date) as data_apenas FROM service_orders \n                WHERE status IN ('concluido_sucesso', 'concluido_sem_solucao')\n                AND user_id = ?\n                ORDER BY completion_date DESC\n                LIMIT 10\n            ", (self.user_id,))
            debug_os = cursor.fetchall()
            print(f'DEBUG: OS conclu├¡das encontradas: {len(debug_os)}')
            for os_debug in debug_os:
                print(f'DEBUG: Data conclus├úo completa: {os_debug[0]}, Status: {os_debug[1]}, Data apenas: {os_debug[2]}')
            data_atual = datetime.now()
            print(f'DEBUG: Data/hora atual do sistema: {data_atual}')
            print(f'DEBUG: Data atual formatada: {data_atual.strftime('%Y-%m-%d')}')
            print(f'DEBUG: Hora atual formatada: {data_atual.strftime('%H:%M:%S')}')
            cursor.execute('\n                SELECT COUNT(*) FROM clients \n                WHERE user_id = ?\n            ', (self.user_id,))
            total_clientes = cursor.fetchone()[0]
            self.total_clientes.setText(f'{self.translation_manager.get_text('total_clients')}<br><br><h1>{total_clientes}</h1>')
            cursor.execute('\n                SELECT so.id, c.name, so.brand, so.model, so.status, so.entry_date,\n                       so.device_type, so.reported_issue\n                FROM service_orders so\n                JOIN clients c ON so.client_id = c.id\n                WHERE so.user_id = ?\n                ORDER BY so.entry_date DESC\n                LIMIT 50\n            ', (self.user_id,))
            self.todas_os = cursor.fetchall()
            print(f'DEBUG: Carregadas {len(self.todas_os)} ordens de servi├ºo para o usu├írio {self.user_id}')
            if not self.todas_os:
                cursor.execute('SELECT COUNT(*) FROM service_orders')
                total_os = cursor.fetchone()[0]
                print(f'DEBUG: Total de OS no banco: {total_os}')
                cursor.execute('SELECT COUNT(*) FROM service_orders WHERE user_id = ?', (self.user_id,))
                os_usuario = cursor.fetchone()[0]
                print(f'DEBUG: OS do usu├írio {self.user_id}: {os_usuario}')
                if total_os > 0 and os_usuario == 0:
                    self.status_bar.showMessage(f'Nenhuma ordem de servi├ºo encontrada para o usu├írio {self.user_id}')
                elif total_os == 0:
                    self.status_bar.showMessage('Nenhuma ordem de servi├ºo cadastrada no sistema')
            self.filtrar_os()
        except sqlite3.Error as e:
            print(f'DEBUG: Erro SQL: {str(e)}')
            QMessageBox.warning(self, 'Erro de Banco de Dados', f'Erro ao carregar dados: {str(e)}')
            self.todas_os = []
            self.filtrar_os()
        except Exception as e:
            print(f'DEBUG: Erro geral: {str(e)}')
            QMessageBox.warning(self, 'Erro', f'Erro inesperado ao carregar dados: {str(e)}')
            self.todas_os = []
            self.filtrar_os()
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
            self.conn = None
        self.ultima_atualizacao = datetime.now()
        hora_formatada = self.ultima_atualizacao.strftime('%H:%M:%S')
        self.status_bar.showMessage(f'Dashboard atualizado ├ás {hora_formatada}')
    def _texto_status_filtro(self, texto=None):
        if texto is None:
            try:
                texto = self.status_combo.currentText()
            except Exception:
                return ''
        status_clean = str(texto or '')
        for emoji in ('­ƒöº', 'Ô£à', 'ÔØî', '­ƒôè'):
            status_clean = status_clean.replace(emoji, '')
        try:
            status_clean = re.sub('\\s*\\(\\d+\\)', '', status_clean).strip()
        except Exception:
            status_clean = status_clean.strip()
        return status_clean
        return status_clean
    def filtrar_os(self):
        status = self.status_combo.currentText()
        texto = self.busca_input.text().lower()
        filtrados = []
        for os in self.todas_os:
            status_clean = self._texto_status_filtro(status)
            texto_todas = self.translation_manager.get_text('all')
            if status_clean and status_clean != texto_todas:
                status_map = {self.translation_manager.get_text('in_repair'): 'em_reparo', self.translation_manager.get_text('closed_success'): 'concluido_sucesso', self.translation_manager.get_text('closed_no_solution'): 'concluido_sem_solucao'}
                if status_clean in status_map and os[4] != status_map[status_clean]:
                    continue
            if texto:
                cliente_nome = str(os[1]) if len(os) > 1 else ''
                marca = str(os[2]) if len(os) > 2 else ''
                modelo = str(os[3]) if len(os) > 3 else ''
                problema = str(os[7]) if len(os) > 7 else ''
                modelo_completo = f'{marca} {modelo}'.lower()
                if texto not in cliente_nome.lower() and texto not in modelo_completo and texto not in problema.lower():
                    continue
            filtrados.append(os)
            continue
        self.atualizar_contadores_status()
        self.atualizar_tabela(filtrados)
    def atualizar_contadores_status(self):
        if not self.todas_os:
            return
        contadores = {'em_reparo': 0, 'concluido_sucesso': 0, 'concluido_sem_solucao': 0}
        for os in self.todas_os:
            status = os[4]
            if status in contadores:
                contadores[status] += 1
        current_selection = self.status_combo.currentText()
        self.status_combo.blockSignals(True)
        self.status_combo.clear()
        self.status_combo.addItems([f'{self.translation_manager.get_text('all')} ({len(self.todas_os)})', f'{self.translation_manager.get_text('in_repair')} ({contadores['em_reparo']})', f'{self.translation_manager.get_text('closed_success')} ({contadores['concluido_sucesso']})', f'{self.translation_manager.get_text('closed_no_solution')} ({contadores['concluido_sem_solucao']})'])
        for i in range(self.status_combo.count()):
            item_text = self.status_combo.itemText(i)
            if not any((base_text in current_selection for base_text in (self.translation_manager.get_text('all'), self.translation_manager.get_text('in_repair'), self.translation_manager.get_text('closed_success'), self.translation_manager.get_text('closed_no_solution')) if base_text in item_text)):
                continue
            self.status_combo.setCurrentIndex(i)
            break
        else:
            self.status_combo.setCurrentIndex(0)
        self.status_combo.blockSignals(False)
    def atualizar_tabela(self, dados):
        self.tabela.setRowCount(0)
        for row, os_data in enumerate(dados):
            if len(os_data) >= 8:
                os_id, cliente, marca, modelo, status, data, tipo, problema = os_data
            else:
                os_id = os_data[0] if len(os_data) > 0 else ''
                cliente = os_data[1] if len(os_data) > 1 else ''
                marca = os_data[2] if len(os_data) > 2 else ''
                modelo = os_data[3] if len(os_data) > 3 else ''
                status = os_data[4] if len(os_data) > 4 else ''
                data = os_data[5] if len(os_data) > 5 else ''
                tipo = os_data[6] if len(os_data) > 6 else ''
                problema = os_data[7] if len(os_data) > 7 else ''
            self.tabela.insertRow(row)
            status_display = {'em_reparo': self.translation_manager.get_text('in_repair'), 'concluido_sucesso': self.translation_manager.get_text('closed_success'), 'concluido_sem_solucao': self.translation_manager.get_text('closed_no_solution')}.get(status, status)
            status_colors = {'em_reparo': '#f39c12', 'concluido_sucesso': '#27ae60', 'concluido_sem_solucao': '#e74c3c'}
            os_item = QTableWidgetItem(str(os_id))
            os_item.setTextAlignment(Qt.AlignCenter)
            os_item.setForeground(QColor('#2c3e50'))
            self.tabela.setItem(row, 0, os_item)
            cliente_item = QTableWidgetItem(cliente)
            cliente_item.setForeground(QColor('#2c3e50'))
            self.tabela.setItem(row, 1, cliente_item)
            if tipo and tipo.strip():
                modelo_display = f'{marca} {modelo}\n{tipo}'
            else:
                modelo_display = f'{marca} {modelo}'
            dispositivo_item = QTableWidgetItem(modelo_display)
            dispositivo_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            dispositivo_item.setForeground(QColor('#2c3e50'))
            self.tabela.setItem(row, 2, dispositivo_item)
            status_item = QTableWidgetItem(status_display)
            status_item.setTextAlignment(Qt.AlignCenter)
            if status in status_colors:
                status_item.setBackground(QColor(status_colors[status]))
                status_item.setForeground(QColor('#1a1a1a'))
                font = status_item.font()
                font.setBold(True)
                status_item.setFont(font)
            else:
                status_item.setForeground(QColor('#2c3e50'))
            self.tabela.setItem(row, 3, status_item)
            try:
                data_obj = datetime.strptime(data, '%Y-%m-%d %H:%M:%S')
                data_formatada = data_obj.strftime('%d/%m/%Y\n%H:%M')
            except:
                data_formatada = data
            data_item = QTableWidgetItem(data_formatada)
            data_item.setTextAlignment(Qt.AlignCenter)
            data_item.setForeground(QColor('#2c3e50'))
            self.tabela.setItem(row, 4, data_item)
            btn_widget = QWidget()
            btn_widget.setMinimumHeight(40)
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(8, 8, 8, 8)
            btn_layout.setSpacing(5)
            if status == 'em_reparo':
                encerrar_btn = QPushButton('Encerrar')
                encerrar_btn.setStyleSheet('\n                    QPushButton {\n                        background-color: #27ae60;\n                        color: white;\n                        border: none;\n                        padding: 6px 12px;\n                        border-radius: 4px;\n                        font-size: 12px;\n                        font-weight: bold;\n                        min-width: 80px;\n                    }\n                    QPushButton:hover {\n                        background-color: #229954;\n                    }\n                    QPushButton:pressed {\n                        background-color: #1e8449;\n                    }\n                ')
                encerrar_btn.setCursor(Qt.PointingHandCursor)
                encerrar_btn.clicked.connect((lambda checked, os_id=os_id: self.encerrar_os(os_id)))
                btn_layout.addWidget(encerrar_btn)
            ver_btn = QPushButton('Ver')
            ver_btn.setStyleSheet('\n                QPushButton {\n                    background-color: #3498db;\n                    color: white;\n                    border: none;\n                    padding: 6px 12px;\n                    border-radius: 4px;\n                    font-size: 12px;\n                    font-weight: bold;\n                    min-width: 70px;\n                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);\n                }\n                QPushButton:hover {\n                    background-color: #2980b9;\n                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);\n                }\n                QPushButton:pressed {\n                    background-color: #21618c;\n                    box-shadow: 0 1px 2px rgba(0,0,0,0.1);\n                }\n            ')
            ver_btn.setCursor(Qt.PointingHandCursor)
            ver_btn.clicked.connect((lambda checked, os_id=os_id: self.ver_detalhes_os(os_id)))
            btn_layout.addWidget(ver_btn)
            self.tabela.setCellWidget(row, 5, btn_widget)
            continue
        self.tabela.resizeRowsToContents()
        for row in range(self.tabela.rowCount()):
            if self.tabela.rowHeight(row) < 60:
                self.tabela.setRowHeight(row, 60)
        total_exibidas = len(dados)
        total_geral = len(self.todas_os)
        if total_exibidas == total_geral:
            status_msg = f'Exibindo {total_exibidas} ordem(s) de servi├ºo'
        else:
            status_msg = f'Exibindo {total_exibidas} de {total_geral} ordem(s) de servi├ºo'
        filtros_ativos = []
        if self._texto_status_filtro() != self.translation_manager.get_text('all'):
            filtros_ativos.append('Status')
        if self.busca_input.text().strip():
            filtros_ativos.append('Busca')
        if filtros_ativos:
            status_msg += f' | Filtros: {', '.join(filtros_ativos)}'
        self.status_bar.showMessage(status_msg)
        self.atualizar_cores_botoes()
    def atualizar_cores_botoes(self):
        try:
            linhas_selecionadas = set()
            for item in self.tabela.selectedItems():
                linhas_selecionadas.add(item.row())
            for row in range(self.tabela.rowCount()):
                widget = self.tabela.cellWidget(row, 5)
                if widget:
                    ver_btn = None
                    for child in widget.findChildren(QPushButton):
                        if not 'Ver' in child.text():
                            continue
                        ver_btn = child
                        break
                    if not ver_btn:
                        continue
                    if row in linhas_selecionadas:
                        ver_btn.setStyleSheet('\n                                QPushButton {\n                                    background-color: #f39c12;\n                                    color: white;\n                                    border: none;\n                                    padding: 6px 12px;\n                                    border-radius: 4px;\n                                    font-size: 12px;\n                                    font-weight: bold;\n                                    min-width: 70px;\n                                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);\n                                }\n                                QPushButton:hover {\n                                    background-color: #e67e22;\n                                    box-shadow: 0 3px 6px rgba(0,0,0,0.3);\n                                }\n                                QPushButton:pressed {\n                                    background-color: #d35400;\n                                    box-shadow: 0 1px 2px rgba(0,0,0,0.2);\n                                }\n                            ')
                    else:
                        ver_btn.setStyleSheet('\n                                QPushButton {\n                                    background-color: #3498db;\n                                    color: white;\n                                    border: none;\n                                    padding: 6px 12px;\n                                    border-radius: 4px;\n                                    font-size: 12px;\n                                    font-weight: bold;\n                                    min-width: 70px;\n                                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);\n                                }\n                                QPushButton:hover {\n                                    background-color: #2980b9;\n                                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);\n                                }\n                                QPushButton:pressed {\n                                    background-color: #21618c;\n                                    box-shadow: 0 1px 2px rgba(0,0,0,0.1);\n                                }\n                            ')
            return
        except Exception as e:
            print(f'Erro ao atualizar cores dos bot├Áes: {str(e)}')
    def abrir_lista_clientes(self):
        dialog = ListClientsDialog(self.user_id, self)
        if dialog.exec_() == ListClientsDialog.Accepted:
            self.carregar_dashboard()
    def novo_cliente(self):
        dialog = ClientForm(self.user_id, self)
        if dialog.exec_() == ClientForm.Accepted:
            self.carregar_dashboard()
    def nova_os(self):
        dialog = ServiceOrderForm(self.user_id, self)
        if dialog.exec_() == ServiceOrderForm.Accepted:
            self.carregar_dashboard()
    def abrir_os_abertas(self):
        dialog = OpenServiceOrdersDialog(self.user_id, self)
        if dialog.exec_() == OpenServiceOrdersDialog.Accepted:
            self.carregar_dashboard()
    def abrir_historico(self):
        dialog = ServiceOrderHistoryDialog(self.user_id, self)
        if dialog.exec_() == ServiceOrderHistoryDialog.Accepted:
            self.carregar_dashboard()
    def pesquisar_solucoes(self):
        dialog = KnowledgeBaseSearchDialog(self.user_id, self)
        if dialog.exec_() == KnowledgeBaseSearchDialog.Accepted:
            self.carregar_dashboard()
    def nova_solucao(self):
        dialog = AddKnowledgeDialog(self.user_id, self)
        if dialog.exec_() == AddKnowledgeDialog.Accepted:
            self.carregar_dashboard()
    def relatorio_diario(self):
        dialog = DailyReportDialog(self.user_id, self)
        if dialog.exec_() == DailyReportDialog.Accepted:
            self.carregar_dashboard()
    def relatorio_mensal(self):
        dialog = MonthlyReportDialog(self.user_id, self)
        if dialog.exec_() == MonthlyReportDialog.Accepted:
            self.carregar_dashboard()
    def encerrar_os(self, os_id):
        dialog = CloseServiceOrderDialog(os_id, self.user_id, self)
        if dialog.exec_() == CloseServiceOrderDialog.Accepted:
            self.carregar_dashboard()
    def ver_detalhes_os(self, os_id):
        from app.views.service_order_details import ServiceOrderDetailsDialog
        dialog = ServiceOrderDetailsDialog(os_id, self)
        if dialog.exec_() == ServiceOrderDetailsDialog.Accepted:
            self.carregar_dashboard()
    def abrir_config_empresa(self):
        dialog = CompanySettingsDialog(self.user_id, self)
        if dialog.exec_() == CompanySettingsDialog.Accepted:
            self.carregar_dashboard()
    def refresh_manual(self):
        self.status_bar.showMessage('Atualizando dashboard...')
        self.carregar_dashboard()
    def criar_backup(self):
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
            self.conn = None
        if BackupManager.criar_backup(self):
            self.carregar_dashboard()
    def restaurar_backup(self):
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
            self.conn = None
        if BackupManager.restaurar_backup(self):
            self.carregar_dashboard()
    def verificar_integridade(self):
        BackupManager.verificar_integridade(self)
    def _resolver_caminho_banco(self):
        db_path = 'app/database/service_orders.db'
        if not os.path.exists(db_path):
            db_path = PathManager.get_database_path('service_orders.db')
        return db_path
    def zerar_sistema_os(self):
        aviso = QMessageBox(self)
        aviso.setIcon(QMessageBox.Warning)
        aviso.setWindowTitle('Zerar Sistema de Ordens de Servi├ºo')
        aviso.setText('Esta a├º├úo ├® IRREVERS├ìVEL.')
        aviso.setInformativeText('Ser├úo apagados TODOS os seguintes dados:\nÔÇó Ordens de Servi├ºo\nÔÇó Fotos das OS (registros no banco)\nÔÇó Clientes\nÔÇó Base de conhecimento\n\nOs dados da sua empresa (nome, CNPJ, logo) ser├úo PRESERVADOS.\nUm backup de seguran├ºa ser├í criado automaticamente antes de apagar.\n\nDeseja continuar?')
        aviso.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        aviso.setDefaultButton(QMessageBox.No)
        if aviso.exec_() != QMessageBox.Yes:
            return
        texto, ok = QInputDialog.getText(self, 'Confirma├º├úo Final', 'Para confirmar, digite a palavra CONFIRMAR (em mai├║sculas):')
        if not ok or texto.strip() != 'CONFIRMAR':
            QMessageBox.information(self, 'Opera├º├úo Cancelada', 'Nenhum dado foi apagado.')
            return
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = None
        db_path = self._resolver_caminho_banco()
        if not os.path.exists(db_path):
            QMessageBox.critical(self, 'Erro', 'Banco de dados n├úo encontrado. Opera├º├úo cancelada.')
            self.carregar_dashboard()
            return
        backup_path = BackupManager.criar_backup_automatico(db_path=db_path, prefixo='backup_pre_reset_os')
        if not backup_path:
            QMessageBox.critical(self, 'Opera├º├úo Abortada', 'N├úo foi poss├¡vel criar o backup de seguran├ºa.\nPor seguran├ºa, NENHUM dado foi apagado.\n\nTente novamente ou contate o suporte.')
            self.carregar_dashboard()
            return
        conn = None
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM service_order_photos')
            cursor.execute('DELETE FROM service_orders')
            cursor.execute('DELETE FROM clients')
            cursor.execute('DELETE FROM knowledge_base')
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'")
            if cursor.fetchone():
                cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('service_orders','service_order_photos','clients','knowledge_base')")
            conn.commit()
        except Exception as exc:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            print(f'[service_order_window] zerar_sistema_os: {type(exc).__name__}')
            QMessageBox.critical(self, 'Erro', f'N├úo foi poss├¡vel zerar o sistema de OS.\nA opera├º├úo foi revertida e nada foi perdido.\n\nSeu backup de seguran├ºa est├í salvo em:\n{backup_path}')
            self.carregar_dashboard()
            try:
                pass
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass
        if conn:
            try:
                conn.close()
            except Exception:
                pass
        try:
            c2 = sqlite3.connect(db_path)
            c2.execute('VACUUM')
            c2.close()
        except Exception:
            pass
        self.carregar_dashboard()
        QMessageBox.information(self, 'Conclu├¡do', f'Sistema de Ordens de Servi├ºo zerado com sucesso!\n\nBackup de seguran├ºa salvo em:\n{backup_path}')
