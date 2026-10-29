from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QFrame, QGridLayout, QMenuBar, QAction, QMessageBox)
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QIcon, QPixmap
from app.views.login_window import LoginWindow
from app.utils.translation_manager import TranslationManager
from app.views.language_selector import LanguageSelectorDialog
from app.utils.window_protection import protect_window_from_capture_extended
import sqlite3
import os
class MainWindow(QMainWindow):
    def __init__(self, user_id=None, is_admin=False):
        super().__init__()
        if user_id is None:
            self.close()
            self.login = LoginWindow()
            self.login.show()
            return
        self.user_id = user_id
        self.is_admin = is_admin
        self.translation_manager = TranslationManager.get_instance()
        self.create_ui_structure()
        self.update_ui_texts()
        self.conectar_banco()
        if not self.pode_gravar_tela():
            protect_window_from_capture_extended(self, True)
    def pode_gravar_tela(self):
        from app.utils.screen_protection_config import pode_gravar_tela as config_pode_gravar
        return config_pode_gravar(is_admin=self.is_admin, user_domain=getattr(self, 'user_domain', None))
    def conectar_banco(self):
        try:
            from ..utils.path_manager import PathManager
            self.db_path = PathManager.get_database_path('base.db')
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao conectar ao banco: {str(e)}')
    def create_ui_structure(self):
        self.setMinimumSize(1200, 800)
        central = QWidget()
        self.setCentralWidget(central)
        central.setStyleSheet('\n            QWidget {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #f8f9fa, stop:1 #ffffff);\n            }\n        ')
        self.main_layout = QVBoxLayout(central)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(25)
        self.create_header()
        self.create_search_bar()
        self.create_grid_layout()
        self.create_menu_bar()
        if self.is_admin:
            self.create_admin_label()
    def update_ui_texts(self):
        self.setWindowTitle(self.translation_manager.get_text('system_title'))
        for widget in self.findChildren(QLabel):
            if widget.text() == 'UNION TECHNICAL':
                continue
            if 'slogan' in widget.styleSheet():
                widget.setText(self.translation_manager.get_text('slogan'))
        for btn in self.findChildren(QPushButton):
            if '­ƒîÉ' in btn.text():
                btn.setText(f'­ƒîÉ {self.translation_manager.current_language_name}')
            elif 'Ver Solu├º├Áes' in btn.text():
                btn.setText(self.translation_manager.get_text('see_solutions'))
        self.search_box.setPlaceholderText(self.translation_manager.get_text('search_placeholder'))
        self.menuBar().clear()
        self.create_menu_bar()
    def create_header(self):
        header = QFrame()
        header.setStyleSheet('\n            QFrame {\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,\n                    stop:0 #1976D2, stop:1 #64B5F6);\n                border-radius: 15px;\n                padding: 10px;\n                max-height: 120px;\n            }\n        ')
        header_layout = QHBoxLayout(header)
        title_container = QVBoxLayout()
        logo_label = QLabel()
        logo_pixmap = QPixmap('app/resources/logos/logo.png').scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(logo_pixmap)
        header_layout.addWidget(logo_label)
        titulo = QLabel('UNION TECHNICAL')
        titulo.setStyleSheet('\n            font-size: 28px;\n            font-weight: bold;\n            color: white;\n            margin-left: 15px;\n        ')
        title_container.addWidget(titulo)
        slogan = QLabel(self.translation_manager.get_text('slogan'))
        slogan.setStyleSheet('\n            font-size: 14px;\n            color: rgba(255, 255, 255, 0.9);\n            margin-left: 15px;\n        ')
        title_container.addWidget(slogan)
        header_layout.addLayout(title_container)
        header_layout.addStretch()
        language_btn = QPushButton(f'­ƒîÉ {self.translation_manager.current_language_name}')
        language_btn.setStyleSheet('\n            QPushButton {\n                background: rgba(255, 255, 255, 0.2);\n                border: none;\n                border-radius: 15px;\n                padding: 8px 15px;\n                color: white;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background: rgba(255, 255, 255, 0.3);\n            }\n        ')
        language_btn.clicked.connect(self.change_language)
        header_layout.addWidget(language_btn)
        user_info = QFrame()
        user_info.setStyleSheet('\n            QFrame {\n                background: rgba(255, 255, 255, 0.2);\n                border-radius: 20px;\n                padding: 10px 20px;\n            }\n        ')
        user_layout = QHBoxLayout(user_info)
        user_layout.setContentsMargins(0, 0, 0, 0)
        user_label = QLabel(f'­ƒæñ {self.get_username()}')
        user_label.setStyleSheet('color: white; font-weight: bold;')
        user_layout.addWidget(user_label)
        header_layout.addWidget(user_info)
        self.main_layout.addWidget(header)
    def create_search_bar(self):
        search_frame = QFrame()
        search_frame.setStyleSheet('\n            QFrame {\n                background: white;\n                border-radius: 25px;\n                padding: 5px 20px;\n                border: 1px solid #e0e0e0;\n            }\n        ')
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(10, 0, 10, 0)
        search_icon = QLabel('­ƒöì')
        search_layout.addWidget(search_icon)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(self.translation_manager.get_text('search_placeholder'))
        self.search_box.setStyleSheet('\n            QLineEdit {\n                border: none;\n                padding: 10px;\n                font-size: 14px;\n                background: transparent;\n            }\n            QLineEdit:focus {\n                outline: none;\n            }\n        ')
        search_layout.addWidget(self.search_box)
        self.main_layout.addWidget(search_frame)
    def create_grid_layout(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('\n            QScrollArea {\n                border: none;\n                background: transparent;\n            }\n            QScrollBar:vertical {\n                border: none;\n                background: #f0f0f0;\n                width: 10px;\n                border-radius: 5px;\n            }\n            QScrollBar::handle:vertical {\n                background: #c0c0c0;\n                border-radius: 5px;\n            }\n            QScrollBar::handle:vertical:hover {\n                background: #a0a0a0;\n            }\n        ')
        scroll_content = QWidget()
        self.grid_layout = QGridLayout(scroll_content)
        self.grid_layout.setSpacing(25)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        marcas = [('APPLE', 'apple.png'), ('XIAOMI', 'xiaomi.png'), ('ANDROID\nCOMANDOS', 'android.png'), ('SAMSUNG', 'samsung.png'), ('REALME', 'realme.png'), ('MOTOROLA', 'motorola.png'), ('OPPO', 'oppo.png'), ('INFINIX', 'infinix.png'), ('CPU', 'cpu.png'), ('ESTUDO', 'estudo.png'), ('VIVO', 'vivo.png'), ('HUAWEI', 'huawei.png'), ('SOFTWARE', 'software.png'), ('TEST POINTS', 'testpoint.png')]
        row = col = 0
        for marca, icone in marcas:
            card = self.criar_card_marca(marca, icone)
            self.grid_layout.addWidget(card, row, col)
            col += 1
            if col > 3:
                col = 0
                row += 1
        scroll.setWidget(scroll_content)
        self.main_layout.addWidget(scroll)
        self.search_box.textChanged.connect(self.buscar_solucoes)
    def create_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu(self.translation_manager.get_text('menu_file'))
        language_action = file_menu.addAction(self.translation_manager.get_text('change_language'))
        language_action.triggered.connect(self.change_language)
        file_menu.addSeparator()
        exit_action = file_menu.addAction(self.translation_manager.get_text('exit'))
        exit_action.triggered.connect(self.close)
        menu_android = menu_bar.addMenu('Android')
        diagnostico_acao = QAction('Diagn├│stico ADB', self)
        diagnostico_acao.triggered.connect(self.abrir_diagnostico)
        menu_android.addAction(diagnostico_acao)
        menu_parceiros = menu_bar.addMenu('Parceiros')
        ver_parceiros_acao = QAction('Ver Parceiros', self)
        ver_parceiros_acao.triggered.connect(self.abrir_parceiros)
        menu_parceiros.addAction(ver_parceiros_acao)
        menu_opcoes = menu_bar.addMenu('Op├º├Áes')
        sobre_acao = QAction('Sobre o Sistema', self)
        sobre_acao.triggered.connect(self.mostrar_sobre)
        menu_opcoes.addAction(sobre_acao)
        quantidade_acao = QAction('Quantidade de Solu├º├Áes', self)
        quantidade_acao.triggered.connect(self.mostrar_quantidade_solucoes)
        menu_opcoes.addAction(quantidade_acao)
        fechar_acao = QAction('Fechar', self)
        fechar_acao.triggered.connect(self.close)
        menu_opcoes.addAction(fechar_acao)
    def create_admin_label(self):
        admin_label = QLabel('­ƒöº Modo Administrador')
        admin_label.setStyleSheet('\n            QLabel {\n                color: #1976D2;\n                font-weight: bold;\n                padding: 8px 15px;\n                border: 2px solid #1976D2;\n                border-radius: 15px;\n                background: rgba(25, 118, 210, 0.1);\n            }\n        ')
        admin_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(admin_label)
    def criar_card_marca(self, marca, icone_nome):
        card = QFrame()
        card.setFixedSize(250, 300)
        card.setStyleSheet('\n            QFrame {\n                background: white;\n                border-radius: 10px;\n                padding: 15px;\n                border: 2px solid #eee;\n            }\n            QFrame:hover {\n                border: 2px solid #2196F3;\n                background-color: #f5f5f5;\n            }\n        ')
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)
        logo_container = QLabel()
        logo_container.setFixedSize(150, 150)
        logo_container.setAlignment(Qt.AlignCenter)
        logo_path = os.path.join('app/resources/logos', icone_nome)
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_container.setPixmap(scaled_pixmap)
        layout.addWidget(logo_container)
        nome = QLabel(marca)
        nome.setStyleSheet('\n            font-size: 18px;\n            font-weight: bold;\n            color: #2C3E50;\n            margin: 10px 0;\n        ')
        nome.setAlignment(Qt.AlignCenter)
        layout.addWidget(nome)
        btn = QPushButton('Ver Solu├º├Áes')
        btn.setStyleSheet('\n            QPushButton {\n                background-color: #2196F3;\n                color: white;\n                border: none;\n                padding: 10px 20px;\n                border-radius: 5px;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background-color: #1976D2;\n            }\n        ')
        btn.clicked.connect((lambda: self.abrir_solucoes(marca)))
        layout.addWidget(btn)
        return card
    def buscar_solucoes(self, texto):
        try:
            if not texto:
                for row in range(self.grid_layout.rowCount()):
                    for col in range(self.grid_layout.columnCount()):
                        item = self.grid_layout.itemAtPosition(row, col)
                        if item:
                            item.widget().setVisible(True)
                return
            texto = texto.lower()
            for row in range(self.grid_layout.rowCount()):
                for col in range(self.grid_layout.columnCount()):
                    item = self.grid_layout.itemAtPosition(row, col)
                    if item:
                        widget = item.widget()
                        marca = widget.findChild(QLabel).text().lower()
                        widget.setVisible(texto in marca)
            return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro na busca: {str(e)}')
    def mostrar_sobre(self):
        QMessageBox.about(self, 'Sobre o Sistema', 'TECHNICIANS UNION - Solu├º├Áes para Smartphones\nVers├úo 1.0\nDesenvolvido por TECHNICIANS UNION')
    def mostrar_quantidade_solucoes(self):
        try:
            cursor = self.cursor
            cursor.execute("SELECT COUNT(*) FROM solucoes WHERE status='ativo'")
            total = cursor.fetchone()[0]
            QMessageBox.information(self, 'Quantidade de Solu├º├Áes', f'Total de solu├ºes dispon├¡veis: {total}')
            return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao consultar quantidade: {str(e)}')
    def abrir_solucoes(self, marca):
        try:
            from app.views.solucoes_view import SolucoesWindow
            self.solucoes_window = SolucoesWindow(marca, self)
            self.solucoes_window.setWindowFlags(Qt.Window)
            self.solucoes_window.setWindowModality(Qt.NonModal)
            self.solucoes_window.setMinimumSize(1200, 800)
            self.solucoes_window.resize(1200, 800)
            if not self.pode_gravar_tela():
                protect_window_from_capture_extended(self.solucoes_window, True)
            screen = QCoreApplication.instance().desktop().screenGeometry()
            window_size = self.solucoes_window.frameGeometry()
            x = (screen.width() - window_size.width()) // 2
            y = (screen.height() - window_size.height()) // 2
            self.solucoes_window.move(x, y)
            self.solucoes_window.show()
            return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao abrir solu├º├Áes: {str(e)}')
    def abrir_diagnostico(self):
        try:
            from app.views.diagnostico_android import DiagnosticoAndroid
            self.diagnostico_window = DiagnosticoAndroid(self)
            if not self.pode_gravar_tela():
                protect_window_from_capture_extended(self.diagnostico_window, True)
            screen = QCoreApplication.instance().desktop().screenGeometry()
            window_size = self.diagnostico_window.frameGeometry()
            x = (screen.width() - window_size.width()) // 2
            y = (screen.height() - window_size.height()) // 2
            self.diagnostico_window.move(x, y)
            self.diagnostico_window.show()
            return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao abrir diagn├│stico: {str(e)}')
    def abrir_parceiros(self):
        try:
            from app.views.parceiros_view import ParceirosWindow
            self.parceiros_window = ParceirosWindow(self)
            protect_window_from_capture_extended(self.parceiros_window, True)
            screen = QCoreApplication.instance().desktop().screenGeometry()
            window_size = self.parceiros_window.frameGeometry()
            x = (screen.width() - window_size.width()) // 2
            y = (screen.height() - window_size.height()) // 2
            self.parceiros_window.move(x, y)
            self.hide()
            self.parceiros_window.show()
            return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao abrir parceiros: {str(e)}')
    def change_language(self):
        dialog = LanguageSelectorDialog(self)
        if dialog.exec_() == LanguageSelectorDialog.Accepted:
            self.refresh_interface()
    def refresh_interface(self):
        self.update_ui_texts()
