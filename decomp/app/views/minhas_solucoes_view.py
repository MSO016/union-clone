from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, QScrollArea, QSplitter, QFrame, QTextEdit, QMessageBox, QApplication, QFileDialog, QHeaderView, QDialog, QMenuBar, QAction)
from PyQt5.QtCore import (Qt, QByteArray, QBuffer)
from PyQt5.QtGui import QPixmap, QImage
from ..utils.user_solutions_manager import UserSolutionsManager
from .components.image_preview_label import ImagePreviewLabel
from .dialogs.view_solution_dialog import ViewSolutionDialog, ImageViewerDialog
from ..utils.translation_manager import TranslationManager
from app.utils.window_protection import protect_window_from_capture_extended
from app.utils.screen_protection_config import pode_gravar_tela
from app.utils.marcas_sistema import get_marcas_para_dropdown
from app.utils.compartilhamento_seguro import CompartilhamentoSeguro
from app.views.perfil_window import PerfilWindow
from app.utils.backup_manager import BackupManager
import fitz
import os
import re
import logging
class MinhasSolucoesWindow(QMainWindow):
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.user_id = user_id
        self.parent_window = parent
        self.solutions_manager = UserSolutionsManager(user_id)
        self.translation_manager = TranslationManager.get_instance()
        self.is_admin = parent.is_admin if hasattr(parent, 'is_admin') else False
        self.translation_manager.language_changed.connect(self.refresh_interface)
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowSystemMenuHint | Qt.WindowCloseButtonHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        screen = QApplication.primaryScreen().availableGeometry()
        self.setMinimumSize(int(screen.width() * 0.7), int(screen.height() * 0.8))
        self.resize(int(screen.width() * 0.8), int(screen.height() * 0.8))
        self.setWindowTitle('TECH UNION - ' + self.translation_manager.get_text('my_solutions'))
        if not self.pode_gravar_tela():
            protect_window_from_capture_extended(self, True)
        self.init_components()
        self.setup_ui()
        self.setup_menu_bar()
        self.load_solutions()
        self.center_window()
    def pode_gravar_tela(self):
        '''Verifica se o usu├írio pode gravar a tela baseado no dom├¡nio ou se ├® admin'''
        if self.is_admin:
            return True
        if hasattr(self.parent_window, 'user_domain') and self.parent_window.user_domain:
            return pode_gravar_tela(self.is_admin, self.parent_window.user_domain)
        return False
    def center_window(self):
        '''Centraliza a janela na tela'''
        screen = QApplication.primaryScreen().availableGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)
    def setup_menu_bar(self):
        '''Configura a barra de menu com op├º├Áes de backup'''
        menubar = self.menuBar()
        backup_menu = menubar.addMenu('Backup')
        backup_action = QAction('Criar Backup Manual', self)
        backup_action.setStatusTip('Cria um backup das suas solu├º├Áes')
        backup_action.triggered.connect(self.criar_backup_manual)
        backup_menu.addAction(backup_action)
        restore_action = QAction('Restaurar Backup', self)
        restore_action.setStatusTip('Restaura solu├º├Áes de um arquivo de backup')
        restore_action.triggered.connect(self.restaurar_backup_manual)
        backup_menu.addAction(restore_action)
        backup_menu.addSeparator()
        about_backup_action = QAction('Sobre o Backup', self)
        about_backup_action.setStatusTip('Informa├º├Áes sobre o sistema de backup')
        about_backup_action.triggered.connect(self.mostrar_info_backup)
        backup_menu.addAction(about_backup_action)
        menubar.setStyleSheet('\n            QMenuBar {\n                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,\n                    stop: 0 #2c3e50, stop: 0.5 #34495e, stop: 1 #FF6B35);\n                color: white;\n                border: none;\n                padding: 4px;\n                font-weight: bold;\n                font-size: 14px;\n            }\n            QMenuBar::item {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #FF6B35, stop: 1 #F7931E);\n                color: white;\n                padding: 8px 12px;\n                margin: 2px;\n                border-radius: 6px;\n                border: 2px solid #FFF;\n                font-weight: bold;\n                font-size: 14px;\n                box-shadow: 0 2px 4px rgba(0,0,0,0.3);\n            }\n            QMenuBar::item:selected {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #F7931E, stop: 1 #FF6B35);\n                color: white;\n                border: 2px solid #FFD700;\n                transform: scale(1.05);\n            }\n            QMenuBar::item:pressed {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #E67E22, stop: 1 #D35400);\n                color: white;\n                border: 2px solid #FFD700;\n            }\n            QMenu {\n                background-color: white;\n                border: 2px solid #F7931E;\n                border-radius: 6px;\n                padding: 6px;\n            }\n            QMenu::item {\n                background-color: transparent;\n                padding: 8px 20px;\n                margin: 2px;\n                border-radius: 4px;\n                color: #2c3e50;\n                font-weight: bold;\n            }\n            QMenu::item:selected {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #FF6B35, stop: 1 #F7931E);\n                color: white;\n            }\n            QMenu::separator {\n                height: 2px;\n                background-color: #F7931E;\n                margin: 4px 10px;\n            }\n        ')
    def criar_backup_manual(self):
        '''Cria backup manual das solu├º├Áes usando BackupManager'''
        try:
            if hasattr(self, 'solutions_manager') and hasattr(self.solutions_manager, 'conn'):
                pass
            try:
                if self.solutions_manager.conn:
                    self.solutions_manager.conn.close()
                    self.solutions_manager.conn = None
            except:
                pass
            else:
                sucesso = BackupManager.criar_backup_solucoes(self)
                if sucesso:
                    self.logger.info('Backup das solu├º├Áes criado com sucesso')
        except Exception as e:
            self._mostrar_erro_seguro('Erro no Backup', 'N├úo foi poss├¡vel criar o backup das solu├º├Áes', str(e))
    def restaurar_backup_manual(self):
        '''Restaura backup manual das solu├º├Áes usando BackupManager'''
        try:
            from app.utils.path_manager import PathManager
            db_path = PathManager.get_data_path()
            solucoes_db = os.path.join(db_path, 'user_solutions_1.db')
            try:
                test_file = os.path.join(db_path, 'test_permissions.tmp')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
            except PermissionError:
                reply = QMessageBox.question(self, 'Permiss├úo Necess├íria - TECH UNION', 'Detectamos que pode haver problemas de permiss├úo.\n\nPara garantir que a restaura├º├úo funcione corretamente:\n\nRECOMENDA├ç├âO:\n1. Feche este aplicativo\n2. Clique direito no ├¡cone do TECH UNION \n3. Escolha "Executar como administrador"\n4. Tente restaurar novamente\n\nOu voc├¬ pode tentar continuar (pode falhar):\n\nContinuar mesmo assim?\n                    '.strip(), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply != QMessageBox.Yes:
                    pass
            else:
                if hasattr(self, 'solutions_manager'):
                    pass
        except Exception as e:
            self._mostrar_erro_seguro('Erro na Restaura├º├úo', 'N├úo foi poss├¡vel restaurar o backup das solu├º├Áes', str(e))
        sucesso = BackupManager.restaurar_backup_solucoes(self)
        if sucesso:
            self.load_solutions()
            self.logger.info('Backup das solu├º├Áes restaurado com sucesso')
    def mostrar_info_backup(self):
        '''Mostra informa├º├Áes sobre o sistema de backup'''
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            admin_info = 'Executando como Administrador' if is_admin else 'Usu├írio Normal'
        except:
            admin_info = ''
        QMessageBox.information(self, 'Sistema de Backup - TECH UNION', f'\nSISTEMA DE BACKUP DAS SOLU├ç├òES\n\nO que ├® backupado:\nÔÇó Todas as suas solu├º├Áes t├®cnicas\nÔÇó Imagens e diagramas salvos\nÔÇó Descri├º├Áes e observa├º├Áes\nÔÇó Status de compartilhamento\n\nSeguran├ºa:\nÔÇó Dados ficam no seu computador\nÔÇó Arquivo ZIP compactado\nÔÇó Backup autom├ítico antes da restaura├º├úo\nÔÇó Valida├º├úo de integridade\n\nComo usar:\nÔÇó Backup Manual: Salva suas solu├º├Áes em arquivo ZIP\nÔÇó Restaurar: Carrega solu├º├Áes de um arquivo ZIP\nÔÇó Recomenda├º├úo: Fa├ºa backup antes de reinstalar o sistema\n\nProblemas de Permiss├úo?\nÔÇó Execute como Administrador (clique direito no ├¡cone)\nÔÇó Isso resolve 99% dos problemas de permiss├úo\nÔÇó Sistema tentar├í v├írias abordagens automaticamente\n\n{admin_info}\n\nDica: Guarde os backups em local seguro (nuvem, HD externo)\n            '.strip())
    def init_components(self):
        '''Inicializa todos os componentes da interface'''
        screen = QApplication.primaryScreen().availableGeometry()
        button_font_size = max(10, min(13, int(screen.width() / 160)))
        input_font_size = max(9, min(12, int(screen.width() / 160)))
        self.solutions_table = QTableWidget()
        self.solutions_table.setColumnCount(4)
        self.solutions_table.setHorizontalHeaderLabels(['ID', self.translation_manager.get_text('brand'), self.translation_manager.get_text('model'), self.translation_manager.get_text('description')])
        self.solutions_table.setColumnHidden(0, True)
        self.solutions_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.solutions_table.setSelectionMode(QTableWidget.SingleSelection)
        self.solutions_table.setShowGrid(False)
        self.solutions_table.setAlternatingRowColors(True)
        self.solutions_table.verticalHeader().setVisible(False)
        self.solutions_table.horizontalHeader().setStretchLastSection(True)
        self.solutions_table.setStyleSheet('\n            QTableWidget {\n                background-color: white;\n                alternate-background-color: #f8f9fa;\n                border: none;\n                gridline-color: #e9ecef;\n                border-radius: 8px;\n            }\n            QTableWidget::item {\n                padding: 12px;\n                border-bottom: 1px solid #e9ecef;\n                color: #2c3e50;\n                font-size: 12px;\n            }\n            QTableWidget::item:selected {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #FF6B35, stop: 1 #F7931E);\n                color: white;\n                font-weight: bold;\n            }\n            QTableWidget::item:hover {\n                background-color: #fff3e0;\n            }\n            QHeaderView::section {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #2c3e50, stop: 1 #34495e);\n                color: white;\n                padding: 12px;\n                border: none;\n                font-weight: bold;\n                font-size: 12px;\n            }\n            QHeaderView::section:hover {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #FF6B35, stop: 1 #F7931E);\n            }\n        ')
        header = self.solutions_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self.solutions_table.setColumnWidth(2, 200)
        self.solutions_table.verticalHeader().setDefaultSectionSize(40)
        self.solutions_table.itemSelectionChanged.connect(self.on_selection_changed)
        self.brand_combo = QComboBox()
        self.brand_combo.addItem(self.translation_manager.get_text('all'))
        self.brand_combo.addItems(get_marcas_para_dropdown())
        self.brand_combo.currentTextChanged.connect(self.filter_solutions)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.translation_manager.get_text('search_placeholder'))
        self.search_input.textChanged.connect(self.filter_solutions)
        self.view_btn = QPushButton(self.translation_manager.get_text('view'))
        self.edit_btn = QPushButton(self.translation_manager.get_text('edit'))
        self.delete_btn = QPushButton(self.translation_manager.get_text('delete'))
        self.new_btn = QPushButton(self.translation_manager.get_text('new_solution'))
        self.share_btn = QPushButton('Compartilhar')
        self.view_btn.clicked.connect(self.show_solution_details)
        self.edit_btn.clicked.connect(self.edit_solution)
        self.delete_btn.clicked.connect(self.delete_solution)
        self.new_btn.clicked.connect(self.new_solution)
        self.share_btn.clicked.connect(self.compartilhar_solucao)
        for btn in self.view_btn, self.edit_btn, self.delete_btn, self.new_btn:
            btn.setMinimumHeight(max(35, min(45, int(screen.height() / 25))))
            btn.setCursor(Qt.PointingHandCursor)
            font = btn.font()
            font.setPointSize(button_font_size)
            font.setBold(True)
            btn.setFont(font)
            btn.setStyleSheet('\n                QPushButton {\n                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                        stop: 0 #34495e, stop: 1 #2c3e50);\n                    color: white;\n                    border: none;\n                    padding: 8px 16px;\n                    border-radius: 6px;\n                    font-weight: bold;\n                }\n                QPushButton:hover {\n                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                        stop: 0 #FF6B35, stop: 1 #F7931E);\n                    transform: translateY(-1px);\n                }\n                QPushButton:pressed {\n                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                        stop: 0 #e74c3c, stop: 1 #c0392b);\n                }\n                QPushButton:disabled {\n                    background-color: #bdc3c7;\n                    color: #7f8c8d;\n                }\n            ')
        self.share_btn.setMinimumHeight(max(35, min(45, int(screen.height() / 25))))
        self.share_btn.setCursor(Qt.PointingHandCursor)
        font = self.share_btn.font()
        font.setPointSize(button_font_size)
        font.setBold(True)
        self.share_btn.setFont(font)
        self.share_btn.setStyleSheet('\n            QPushButton {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #FF6B35, stop: 1 #F7931E);\n                color: white;\n                border: none;\n                padding: 10px 25px;\n                border-radius: 8px;\n                font-weight: bold;\n                font-size: 13px;\n            }\n            QPushButton:hover {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #FF5722, stop: 1 #FF9800);\n                transform: translateY(-2px);\n                box-shadow: 0 4px 8px rgba(255, 107, 53, 0.3);\n            }\n            QPushButton:pressed {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #E64A19, stop: 1 #F57C00);\n                transform: translateY(0px);\n            }\n            QPushButton:disabled {\n                background-color: #B0BEC5;\n                color: #7f8c8d;\n            }\n        ')
        self.view_btn.setEnabled(False)
        self.edit_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.share_btn.setEnabled(False)
        self.marca_input = QComboBox()
        self.marca_input.addItems(get_marcas_para_dropdown())
        self.modelo_input = QLineEdit()
        self.descricao_input = QTextEdit()
        self.observacoes_input = QTextEdit()
        text_edit_height = max(120, int(screen.height() / 6))
        self.descricao_input.setMinimumHeight(text_edit_height)
        self.observacoes_input.setMinimumHeight(text_edit_height)
        for input_field in self.modelo_input, self.descricao_input, self.observacoes_input:
            font = input_field.font()
            font.setPointSize(input_font_size)
            input_field.setFont(font)
        marca_font = self.marca_input.font()
        marca_font.setPointSize(input_font_size)
        self.marca_input.setFont(marca_font)
        self.marca_input.setStyleSheet('\n            QComboBox {\n                padding: 8px 12px;\n                border: 2px solid #F7931E;\n                border-radius: 6px;\n                background: white;\n                min-width: 200px;\n                color: #2c3e50;\n                font-weight: bold;\n                font-size: 12px;\n            }\n            QComboBox:focus {\n                border: 2px solid #FF6B35;\n            }\n            QComboBox::drop-down {\n                border: none;\n                padding-right: 20px;\n            }\n            QComboBox::down-arrow {\n                width: 12px;\n                height: 12px;\n                margin-right: 5px;\n            }\n            QComboBox QAbstractItemView {\n                border: 2px solid #F7931E;\n                background: white;\n                selection-background-color: #FF6B35;\n                selection-color: white;\n                font-weight: bold;\n            }\n        ')
        self.imagem_containers = []
        self.diagrama_containers = []
        self.setup_media_containers()
        self.view_btn.setEnabled(False)
        self.edit_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.setup_field_styles()
        self.brand_combo = QComboBox()
        self.brand_combo.setStyleSheet('\n            QComboBox {\n                padding: 8px 12px;\n                border: 2px solid #F7931E;\n                border-radius: 6px;\n                background: white;\n                min-width: 200px;\n                color: #2c3e50;\n                font-weight: bold;\n                font-size: 12px;\n            }\n            QComboBox:focus {\n                border: 2px solid #FF6B35;\n            }\n            QComboBox::drop-down {\n                border: none;\n                padding-right: 20px;\n            }\n            QComboBox::down-arrow {\n                width: 12px;\n                height: 12px;\n                margin-right: 5px;\n            }\n            QComboBox QAbstractItemView {\n                border: 2px solid #F7931E;\n                background: white;\n                selection-background-color: #FF6B35;\n                selection-color: white;\n                font-weight: bold;\n            }\n        ')
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.translation_manager.get_text('search_placeholder'))
        self.search_input.setStyleSheet('\n            QLineEdit {\n                padding: 10px 15px;\n                border: 2px solid #F7931E;\n                border-radius: 6px;\n                font-size: 14px;\n                background-color: white;\n                min-height: 35px;\n                color: #2c3e50;\n                font-weight: bold;\n            }\n            QLineEdit:focus {\n                border-color: #FF6B35;\n                background-color: #fefefe;\n            }\n            QLineEdit::placeholder {\n                color: #95a5a6;\n                font-weight: normal;\n            }\n        ')
        self.solutions_table.setStyleSheet('\n            QTableWidget {\n                background-color: white;\n                alternate-background-color: #f8f9fa;\n                border: none;\n                gridline-color: #dcdde1;\n            }\n            QTableWidget::item {\n                padding: 8px;\n                border-bottom: 1px solid #dcdde1;\n            }\n            QTableWidget::item:selected {\n                background-color: #2196F3;\n                color: white;\n            }\n            QHeaderView::section {\n                background-color: #2c3e50;\n                color: white;\n                padding: 10px;\n                border: none;\n                font-weight: bold;\n            }\n        ')
        header = self.solutions_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self.solutions_table.setColumnWidth(2, 200)
        self.solutions_table.setAlternatingRowColors(True)
        self.solutions_table.verticalHeader().setDefaultSectionSize(40)
    def setup_ui(self):
        '''Configura a interface do usu├írio'''
        screen = QApplication.primaryScreen().availableGeometry()
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(8)
        header_frame = QFrame()
        header_frame.setMaximumHeight(60)
        header_frame.setStyleSheet('\n            QFrame {\n                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,\n                    stop: 0 #2c3e50, stop: 0.4 #34495e, stop: 0.7 #FF6B35, stop: 1 #F7931E);\n                border-radius: 12px;\n                border: 3px solid #F7931E;\n                margin: 2px;\n            }\n        ')
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(8, 3, 8, 3)
        btn_voltar = QPushButton(self.translation_manager.get_text('back'))
        btn_voltar.setStyleSheet('\n            QPushButton {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #F7931E, stop: 1 #FF6B35);\n                color: white;\n                border: none;\n                padding: 8px 20px;\n                border-radius: 6px;\n                font-weight: bold;\n                font-size: 12px;\n                max-width: 120px;\n            }\n            QPushButton:hover {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #FF5722, stop: 1 #FF9800);\n                transform: translateY(-1px);\n            }\n        ')
        btn_voltar.clicked.connect(self.voltar)
        title_label = QLabel(self.translation_manager.get_text('my_solutions'))
        title_label.setStyleSheet('\n            QLabel {\n                color: white;\n                font-weight: bold;\n                font-size: 20px;\n                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);\n                padding: 5px;\n            }\n        ')
        self.stats_label = QLabel('Carregando estatisticas...')
        self.stats_label.setStyleSheet('\n            QLabel {\n                color: white;\n                font-weight: bold;\n                font-size: 14px;\n                background: rgba(247, 147, 30, 0.2);\n                padding: 5px 10px;\n                border-radius: 6px;\n                border: 1px solid #F7931E;\n            }\n        ')
        self.admin_label = self._criar_label_admin()
        if self.admin_label:
            self.admin_label.setStyleSheet('\n                QLabel {\n                    color: white;\n                    font-weight: bold;\n                    font-size: 12px;\n                    background: rgba(76, 175, 80, 0.8);\n                    padding: 4px 8px;\n                    border-radius: 4px;\n                    border: 1px solid #4CAF50;\n                }\n            ')
        header_layout.addWidget(btn_voltar)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        if self.admin_label:
            header_layout.addWidget(self.admin_label)
        header_layout.addWidget(self.stats_label)
        main_layout.addWidget(header_frame)
        splitter = QSplitter(Qt.Horizontal)
        left_panel = QWidget()
        left_panel.setMinimumWidth(int(screen.width() * 0.5))
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 5, 0)
        search_frame = QFrame()
        search_frame.setStyleSheet('\n            QFrame {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #ffffff, stop: 0.3 #f8f9fa, stop: 1 #ecf0f1);\n                border-radius: 12px;\n                border: 3px solid #F7931E;\n                padding: 10px;\n                margin: 2px;\n            }\n        ')
        search_layout = QVBoxLayout(search_frame)
        search_layout.setContentsMargins(8, 3, 8, 3)
        line1_layout = QHBoxLayout()
        brand_label = QLabel(self.translation_manager.get_text('brand') + ':')
        brand_label.setStyleSheet('\n            font-weight: bold;\n            color: #2c3e50;\n            font-size: 13px;\n        ')
        self.search_input.setStyleSheet('\n            QLineEdit {\n                padding: 10px 15px;\n                border: 2px solid #F7931E;\n                border-radius: 8px;\n                background: white;\n                color: #2c3e50;\n                font-size: 12px;\n                min-width: 200px;\n            }\n            QLineEdit:focus {\n                border: 3px solid #FF6B35;\n                background-color: #fefefe;\n            }\n        ')
        search_label = QLabel('Pesquisar:')
        search_label.setStyleSheet('\n            font-weight: bold;\n            color: #2c3e50;\n            font-size: 13px;\n        ')
        line1_layout.addWidget(brand_label)
        line1_layout.addWidget(self.brand_combo)
        line1_layout.addSpacing(15)
        line1_layout.addWidget(search_label)
        line1_layout.addWidget(self.search_input)
        line2_layout = QHBoxLayout()
        status_label = QLabel('Filtrar:')
        status_label.setStyleSheet('\n            font-weight: bold;\n            color: #2c3e50;\n            font-size: 13px;\n        ')
        self.status_filter = QComboBox()
        self.status_filter.addItems(['Todas', 'Compartilhadas', 'Aprovadas', 'Apenas Locais'])
        self.status_filter.currentTextChanged.connect(self.filter_solutions)
        self.status_filter.setStyleSheet('\n            QComboBox {\n                padding: 8px 12px;\n                border: 2px solid #F7931E;\n                border-radius: 8px;\n                background: white;\n                color: #2c3e50;\n                font-size: 12px;\n                min-width: 160px;\n                font-weight: bold;\n            }\n            QComboBox:focus {\n                border: 3px solid #FF6B35;\n            }\n            QComboBox::drop-down {\n                border: none;\n                padding-right: 15px;\n            }\n            QComboBox::down-arrow {\n                width: 12px;\n                height: 12px;\n                margin-right: 5px;\n            }\n            QComboBox QAbstractItemView {\n                border: 2px solid #F7931E;\n                background: white;\n                selection-background-color: #FF6B35;\n                selection-color: white;\n                font-weight: bold;\n            }\n        ')
        line2_layout.addWidget(status_label)
        line2_layout.addWidget(self.status_filter)
        line2_layout.addStretch()
        search_layout.addLayout(line1_layout)
        search_layout.addLayout(line2_layout)
        left_layout.addWidget(search_frame)
        table_scroll = QScrollArea()
        table_scroll.setWidgetResizable(True)
        table_scroll.setStyleSheet('border: none;')
        table_scroll.setWidget(self.solutions_table)
        left_layout.addWidget(table_scroll)
        right_panel = QWidget()
        right_panel.setMaximumWidth(int(screen.width() * 0.35))
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 0, 0, 0)
        details_scroll = QScrollArea()
        details_scroll.setWidgetResizable(True)
        details_scroll.setStyleSheet('\n            QScrollArea {\n                border: none;\n                background-color: transparent;\n            }\n        ')
        details_content = QWidget()
        details_content_layout = QVBoxLayout(details_content)
        action_layout = QHBoxLayout()
        action_layout.addWidget(self.view_btn)
        action_layout.addWidget(self.edit_btn)
        action_layout.addWidget(self.delete_btn)
        action_layout.addWidget(self.share_btn)
        action_layout.addWidget(self.new_btn)
        details_content_layout.addLayout(action_layout)
        details_layout = QVBoxLayout()
        for label_text, widget in (self.translation_manager.get_text('brand') + ':', self.marca_input), (self.translation_manager.get_text('model') + ':', self.modelo_input), (self.translation_manager.get_text('description') + ':', self.descricao_input), (self.translation_manager.get_text('observations') + ':', self.observacoes_input):
            label = QLabel(label_text)
            label.setStyleSheet('font-weight: bold;')
            details_layout.addWidget(label)
            details_layout.addWidget(widget)
        details_content_layout.addLayout(details_layout)
        media_layout = QVBoxLayout()
        imagens_layout = QHBoxLayout()
        for container in self.imagem_containers:
            imagens_layout.addWidget(container)
        media_layout.addLayout(imagens_layout)
        diagramas_layout = QHBoxLayout()
        for container in self.diagrama_containers:
            diagramas_layout.addWidget(container)
        media_layout.addLayout(diagramas_layout)
        details_content_layout.addLayout(media_layout)
        details_scroll.setWidget(details_content)
        right_layout.addWidget(details_scroll)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        total_width = int(screen.width() * 0.8)
        splitter.setSizes([int(total_width * 0.65), int(total_width * 0.35)])
        main_layout.addWidget(splitter)
        self.connect_signals()
    def voltar(self):
        '''Volta para a tela principal'''
        if self.parent_window:
            self.parent_window.show()
        self.close()
    def _criar_label_admin(self):
        '''Cria label indicando se est├í rodando como administrador'''
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if is_admin:
                return QLabel('Admin')
        except Exception:
            pass
    def setup_media_containers(self):
        '''Configura os containers de m├¡dia (3 imagens + 3 diagramas)'''
        screen = QApplication.primaryScreen().availableGeometry()
        preview_size = max(100, min(120, int(screen.width() / 16)))
        label_font_size = max(9, min(11, int(screen.width() / 160)))
        self.imagem_previews = []
        self.btn_imagens = []
        for i in range(3):
            container = QFrame()
            container.setStyleSheet('\n                QFrame {\n                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                        stop: 0 #ffffff, stop: 1 #f8f9fa);\n                    border-radius: 8px;\n                    padding: 6px;\n                    margin: 2px;\n                    border: 2px solid #e9ecef;\n                }\n                QFrame:hover {\n                    border: 2px solid #F7931E;\n                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                        stop: 0 #fefefe, stop: 1 #fff3e0);\n                }\n            ')
            layout = QVBoxLayout(container)
            layout.setContentsMargins(2, 2, 2, 2)
            layout.setSpacing(3)
            label = QLabel(f'{self.translation_manager.get_text('image')} {i + 1}:')
            font = label.font()
            font.setPointSize(label_font_size)
            font.setBold(True)
            label.setFont(font)
            label.setStyleSheet('color: #2c3e50;')
            preview = ImagePreviewLabel()
            preview.setFixedSize(preview_size, preview_size)
            self.imagem_previews.append(preview)
            btn = QPushButton(self.translation_manager.get_text('select_image'))
            btn.setFont(font)
            btn.clicked.connect((lambda checked, idx=i: self.select_image(idx)))
            self.btn_imagens.append(btn)
            layout.addWidget(label)
            layout.addWidget(preview)
            layout.addWidget(btn)
            self.imagem_containers.append(container)
            continue
        self.diagrama_previews = []
        self.btn_diagramas = []
        for i in range(3):
            container = QFrame()
            container.setStyleSheet('\n                QFrame {\n                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                        stop: 0 #ffffff, stop: 1 #f8f9fa);\n                    border-radius: 8px;\n                    padding: 6px;\n                    margin: 2px;\n                    border: 2px solid #e9ecef;\n                }\n                QFrame:hover {\n                    border: 2px solid #F7931E;\n                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                        stop: 0 #fefefe, stop: 1 #fff3e0);\n                }\n            ')
            layout = QVBoxLayout(container)
            layout.setContentsMargins(2, 2, 2, 2)
            layout.setSpacing(3)
            label = QLabel(f'{self.translation_manager.get_text('diagram')} {i + 1}:')
            font = label.font()
            font.setPointSize(label_font_size)
            font.setBold(True)
            label.setFont(font)
            label.setStyleSheet('color: #2c3e50;')
            preview = ImagePreviewLabel()
            preview.setFixedSize(preview_size, preview_size)
            self.diagrama_previews.append(preview)
            btn = QPushButton(self.translation_manager.get_text('select_diagram'))
            btn.setFont(font)
            btn.clicked.connect((lambda checked, idx=i: self.select_diagram(idx)))
            self.btn_diagramas.append(btn)
            layout.addWidget(label)
            layout.addWidget(preview)
            layout.addWidget(btn)
            self.diagrama_containers.append(container)
            continue
    def setup_field_styles(self):
        '''Configura os estilos dos campos de entrada'''
        screen = QApplication.primaryScreen().availableGeometry()
        field_height = max(30, min(40, int(screen.height() / 27)))
        text_edit_height = max(80, min(120, int(screen.height() / 7)))
        self.marca_input.setEnabled(False)
        for input_field in (self.modelo_input,):
            input_field.setStyleSheet('\n                QLineEdit {\n                    padding: 10px 12px;\n                    border: 2px solid #e9ecef;\n                    border-radius: 8px;\n                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                        stop: 0 #ffffff, stop: 1 #f8f9fa);\n                    min-height: %dpx;\n                    color: #2c3e50;\n                    font-size: 12px;\n                }\n                QLineEdit:focus {\n                    border: 2px solid #F7931E;\n                    background: white;\n                }\n            ' % field_height)
            input_field.setReadOnly(True)
        for text_edit in self.descricao_input, self.observacoes_input:
            text_edit.setStyleSheet('\n                QTextEdit {\n                    padding: 10px;\n                    border: 2px solid #e9ecef;\n                    border-radius: 8px;\n                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                        stop: 0 #ffffff, stop: 1 #f8f9fa);\n                    min-height: %dpx;\n                    color: #2c3e50;\n                    font-size: 12px;\n                }\n                QTextEdit:focus {\n                    border: 2px solid #F7931E;\n                    background: white;\n                }\n            ' % text_edit_height)
            text_edit.setReadOnly(True)
            text_edit.setMinimumHeight(text_edit_height)
    def ensure_marca_dropdown_populated(self):
        '''Garante que o dropdown de marcas esteja sempre populado e funcional'''
        try:
            current_count = self.marca_input.count()
            self.logger.debug(f'Dropdown atual tem {current_count} op├º├Áes')
            from app.utils.marcas_sistema import get_marcas_para_dropdown
            marcas = get_marcas_para_dropdown()
            self.marca_input.clear()
            self.marca_input.addItems(marcas)
            self.logger.debug(f'Dropdown re-populado com {len(marcas)} marcas')
            self.marca_input.setEnabled(True)
            self.marca_input.setVisible(True)
            self.marca_input.repaint()
            self.marca_input.update()
            self.logger.debug(f'Dropdown estado final: {self.marca_input.count()} op├º├Áes')
            return
        except Exception as e:
            self.logger.error(f'Erro ao garantir popula├º├úo do dropdown: {e}')
            try:
                from app.utils.marcas_sistema import get_marcas_para_dropdown
                self.marca_input.clear()
                self.marca_input.addItems(get_marcas_para_dropdown())
                self.marca_input.setEnabled(True)
                self.marca_input.setVisible(True)
                self.logger.debug('Fallback: Dropdown restaurado')
            except Exception as fallback_error:
                self.logger.error(f'Fallback dropdown falhou: {fallback_error}')
                e = None
                del e
                return
    def connect_signals(self):
        '''Conecta todos os sinais dos componentes'''
        self.search_input.textChanged.connect(self.filter_solutions)
        self.brand_combo.currentTextChanged.connect(self.filter_solutions)
        self.status_filter.currentTextChanged.connect(self.filter_solutions)
        self.solutions_table.itemSelectionChanged.connect(self.show_solution_details)
        self.new_btn.clicked.connect(self.new_solution)
        self.edit_btn.clicked.connect(self.edit_solution)
        self.delete_btn.clicked.connect(self.delete_solution)
        self.view_btn.clicked.connect(self.view_solution)
    def _sanitizar_entrada_busca(self, texto):
        '''Sanitiza entrada de busca removendo caracteres potencialmente perigosos'''
        if not texto:
            return ''
        texto_limpo = re.sub('[<>"\\\';\\\\%_]', '', str(texto).strip())
        if len(texto_limpo) > 100:
            texto_limpo = texto_limpo[:100]
        return texto_limpo
    def _mostrar_erro_seguro(self, titulo, mensagem_usuario, erro_tecnico=''):
        '''Mostra erro padronizado sem expor detalhes t├®cnicos'''
        try:
            if erro_tecnico:
                self.logger.error(f'{titulo}: {erro_tecnico}')
            QMessageBox.warning(self, titulo, mensagem_usuario)
            return
        except Exception:
            QMessageBox.warning(self, 'Aviso', 'Ocorreu um problema inesperado.')
    def filter_solutions(self):
        '''Filtra as solu├º├Áes com base no texto de pesquisa, marca selecionada e status de forma segura'''
        search_text = self._sanitizar_entrada_busca(self.search_input.text())
        selected_brand = self.brand_combo.currentText()
        selected_status = self.status_filter.currentText()
        try:
            for row in range(self.solutions_table.rowCount()):
                should_show = True
                marca = self.solutions_table.item(row, 1).text()
                modelo = str(self.solutions_table.item(row, 2).text()).lower()
                descricao = str(self.solutions_table.item(row, 3).text()).lower()
                if search_text:
                    text_match = search_text in marca.lower() or search_text in modelo or search_text in descricao
                    should_show = should_show and text_match
                if selected_brand != self.translation_manager.get_text('all') and selected_brand != 'ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ':
                    marca_clean = marca.replace('[S] ', '')
                    brand_match = marca_clean == selected_brand
                    should_show = should_show and brand_match
                if selected_status == 'Compartilhadas':
                    status_match = marca.startswith('[S]')
                    should_show = should_show and status_match
                elif selected_status == 'Aprovadas':
                    status_match = marca.startswith('[S]')
                    should_show = should_show and status_match
                elif selected_status == 'Apenas Locais':
                    status_match = not marca.startswith('[S]')
                    should_show = should_show and status_match
                self.solutions_table.setRowHidden(row, not should_show)
                continue
            return
        except Exception as e:
            self._mostrar_erro_seguro('Erro de Filtro', 'N├úo foi poss├¡vel aplicar o filtro.', str(e))
    def load_solutions(self):
        '''Carrega as solu├º├Áes do banco de dados'''
        try:
            self.solutions_table.setRowCount(0)
            solutions = self.solutions_manager.get_solutions()
            user_brands = set()
            all_brands = set([self.translation_manager.get_text('all')])
            for solution in solutions:
                row = self.solutions_table.rowCount()
                self.solutions_table.insertRow(row)
                if isinstance(solution, tuple):
                    solution_dict = {'id': solution[0], 'id_usuario': solution[1] if len(solution) > 1 else self.user_id, 'marca': solution[2] if len(solution) > 2 else solution[1], 'modelo': solution[3] if len(solution) > 3 else solution[2], 'descricao': solution[4] if len(solution) > 4 else solution[3], 'observacoes': solution[5] if len(solution) > 5 else solution[4] if len(solution) > 4 else '', 'status': solution[6] if len(solution) > 6 else solution[5] if len(solution) > 5 else 'ativo', 'data_criacao': solution[7] if len(solution) > 7 else solution[6] if len(solution) > 6 else '', 'imagem_blob': solution[8] if len(solution) > 8 else solution[7] if len(solution) > 7 else None, 'diagrama_blob': solution[9] if len(solution) > 9 else solution[8] if len(solution) > 8 else None, 'imagem_1_blob': solution[10] if len(solution) > 10 else solution[9] if len(solution) > 9 else None, 'imagem_2_blob': solution[11] if len(solution) > 11 else solution[10] if len(solution) > 10 else None, 'diagrama_2_blob': solution[12] if len(solution) > 12 else solution[11] if len(solution) > 11 else None, 'permite_compartilhamento': solution[13] if len(solution) > 13 else solution[12] if len(solution) > 12 else 1, 'compartilhada': solution[14] if len(solution) > 14 else 0, 'data_compartilhamento': solution[15] if len(solution) > 15 else None}
                else:
                    solution_dict = solution
                if solution_dict['marca']:
                    user_brands.add(solution_dict['marca'])
                    all_brands.add(solution_dict['marca'])
                descricao = solution_dict['descricao']
                if solution_dict.get('diagrama_blob'):
                    pass
            try:
                fitz.open(stream=solution_dict['diagrama_blob'], filetype='pdf')
                descricao += ' [PDF]'
            except:
                descricao += ' [Imagem]'
            else:
                marca_display = solution_dict['marca']
                if solution_dict.get('compartilhada'):
                    marca_display = f'[S] {marca_display}'
                items = [QTableWidgetItem(str(solution_dict['id'])), QTableWidgetItem(marca_display), QTableWidgetItem(solution_dict['modelo']), QTableWidgetItem(descricao)]
                for col, item in enumerate(items):
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    self.solutions_table.setItem(row, col, item)
                current_brand = self.brand_combo.currentText()
                self.brand_combo.clear()
                user_brands_list = sorted(user_brands)
        except Exception as e:
            QMessageBox.critical(self, self.translation_manager.get_text('error_loading'), 'Ocorreu um erro ao carregar as solu├º├Áes. Tente novamente.')
        try:
            system_brands = [marca for marca in get_marcas_para_dropdown() if marca not in user_brands]
            final_brands = [self.translation_manager.get_text('all')]
            if user_brands_list:
                final_brands.extend(user_brands_list)
                if system_brands:
                    final_brands.append('ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ')
                    final_brands.extend(system_brands)
            else:
                final_brands.extend(system_brands)
            self.brand_combo.addItems(final_brands)
            index = self.brand_combo.findText(current_brand)
            if index >= 0:
                self.brand_combo.setCurrentIndex(index)
            self.solutions_table.resizeColumnsToContents()
            header = self.solutions_table.horizontalHeader()
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.Interactive)
            header.setSectionResizeMode(3, QHeaderView.Stretch)
            self.solutions_table.setColumnWidth(2, 200)
            self.update_statistics()
        except Exception as e:
            QMessageBox.critical(self, self.translation_manager.get_text('error_loading'), 'Ocorreu um erro ao carregar as solu├º├Áes. Tente novamente.')
    def show_solution_details(self):
        '''Exibe os detalhes da solu├º├úo selecionada'''
        try:
            selected_rows = self.solutions_table.selectedItems()
            if not selected_rows:
                self.clear_details()
                return
            row = self.solutions_table.currentRow()
            solution_id = int(self.solutions_table.item(row, 0).text())
            solution = self.solutions_manager.get_solution_by_id(solution_id)
            if not solution:
                self.clear_details()
                return
            if isinstance(solution, tuple):
                solution_dict = {'id': solution[0], 'id_usuario': solution[1] if len(solution) > 1 else self.user_id, 'marca': solution[2] if len(solution) > 2 else solution[1], 'modelo': solution[3] if len(solution) > 3 else solution[2], 'descricao': solution[4] if len(solution) > 4 else solution[3], 'observacoes': solution[5] if len(solution) > 5 else solution[4] if len(solution) > 4 else '', 'status': solution[6] if len(solution) > 6 else solution[5] if len(solution) > 5 else 'ativo', 'data_criacao': solution[7] if len(solution) > 7 else solution[6] if len(solution) > 6 else '', 'imagem_blob': solution[8] if len(solution) > 8 else solution[7] if len(solution) > 7 else None, 'diagrama_blob': solution[9] if len(solution) > 9 else solution[8] if len(solution) > 8 else None, 'imagem_1_blob': solution[10] if len(solution) > 10 else solution[9] if len(solution) > 9 else None, 'imagem_2_blob': solution[11] if len(solution) > 11 else solution[10] if len(solution) > 10 else None, 'diagrama_2_blob': solution[12] if len(solution) > 12 else solution[11] if len(solution) > 11 else None, 'permite_compartilhamento': solution[13] if len(solution) > 13 else solution[12] if len(solution) > 12 else 1, 'compartilhada': solution[14] if len(solution) > 14 else 0, 'data_compartilhamento': solution[15] if len(solution) > 15 else None}
            else:
                solution_dict = solution
            self.marca_input.setCurrentText(solution_dict.get('marca', ''))
            self.modelo_input.setText(solution_dict.get('modelo', ''))
            self.descricao_input.setText(solution_dict.get('descricao', ''))
            self.observacoes_input.setText(solution_dict.get('observacoes', ''))
            imagem_fields = ['imagem_blob', 'imagem_1_blob', 'imagem_2_blob']
            for i, field in enumerate(imagem_fields):
                if solution_dict.get(field):
                    pixmap = QPixmap()
                    pixmap.loadFromData(solution_dict[field])
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(self.imagem_previews[i].size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        self.imagem_previews[i].setPixmap(scaled_pixmap)
                    else:
                        self.imagem_previews[i].clear()
                else:
                    self.imagem_previews[i].clear()
            diagrama_fields = ['diagrama_blob', 'diagrama_2_blob']
            for i, field in enumerate(diagrama_fields):
                if i < len(self.diagrama_previews) and solution_dict.get(field):
                    pixmap = QPixmap()
                    pixmap.loadFromData(solution_dict[field])
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(self.diagrama_previews[i].size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        self.diagrama_previews[i].setPixmap(scaled_pixmap)
                        continue
                    self.diagrama_previews[i].clear()
                    continue
                if not i < len(self.diagrama_previews):
                    continue
                self.diagrama_previews[i].clear()
                continue
            if len(self.diagrama_previews) > 2:
                self.diagrama_previews[2].clear()
            self.view_btn.setEnabled(True)
            self.edit_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
            if solution_dict.get('compartilhada'):
                self.share_btn.setText('Compartilhada')
                self.share_btn.setEnabled(False)
                self.share_btn.setToolTip('Esta solu├º├úo j├í foi compartilhada')
                return
            self.share_btn.setText('Compartilhar')
            self.share_btn.setEnabled(True)
            self.share_btn.setToolTip('Compartilhar esta solu├º├úo com a comunidade')
            return
        except Exception as e:
            QMessageBox.warning(self, self.translation_manager.get_text('error_showing_details'), 'Ocorreu um erro ao exibir os detalhes da solu├º├úo. Tente novamente.')
            self.logger.error(f'Erro ao exibir detalhes da solu├º├úo: {str(e)}')
    def clear_details(self):
        '''Limpa os campos de detalhes'''
        self.ensure_marca_dropdown_populated()
        self.marca_input.setCurrentIndex(0)
        self.modelo_input.clear()
        self.descricao_input.clear()
        self.observacoes_input.clear()
        for preview in self.imagem_previews:
            preview.clear()
        for preview in self.diagrama_previews:
            preview.clear()
        self.view_btn.setEnabled(False)
        self.edit_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.share_btn.setEnabled(False)
    def select_image(self, index=0):
        '''Seleciona uma imagem para a solu├º├úo'''
        file_name, _ = QFileDialog.getOpenFileName(self, f'{self.translation_manager.get_text('select_image')} {index + 1}', '', self.translation_manager.get_text('image_files') + ' (*.png *.jpg *.jpeg *.bmp);;' + self.translation_manager.get_text('all_files') + ' (*)')
        if file_name:
            original_pixmap = QPixmap(file_name)
            if not original_pixmap.isNull():
                if not hasattr(self, 'original_images'):
                    self.original_images = [None, None, None]
                self.original_images[index] = original_pixmap
                preview_pixmap = original_pixmap.scaled(self.imagem_previews[index].size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.imagem_previews[index].setPixmap(preview_pixmap)
                width = original_pixmap.width()
                height = original_pixmap.height()
                self.logger.debug(f'Imagem {index + 1}: {width}x{height}')
    def select_diagram(self, index=0):
        '''Seleciona um diagrama para a solu├º├úo'''
        file_name, _ = QFileDialog.getOpenFileName(self, f'{self.translation_manager.get_text('select_diagram')} {index + 1}', '', self.translation_manager.get_text('diagram_files') + ' (*.pdf *.png *.jpg *.jpeg);;' + self.translation_manager.get_text('all_files') + ' (*)')
        if file_name:
            if file_name.lower().endswith('.pdf'):
                try:
                    with open(file_name, 'rb') as pdf_file:
                        pdf_data = pdf_file.read()
                    if not hasattr(self, 'original_diagrams_data'):
                        self.original_diagrams_data = [None, None, None]
                    if not hasattr(self, 'is_diagrams_pdf'):
                        self.is_diagrams_pdf = [False, False, False]
                    self.original_diagrams_data[index] = pdf_data
                    self.is_diagrams_pdf[index] = True
                    pdf_document = fitz.open(file_name)
                    first_page = pdf_document[0]
                    zoom = 2
                    mat = fitz.Matrix(zoom, zoom)
                    pix = first_page.get_pixmap(matrix=mat)
                    img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
                    preview_pixmap = QPixmap.fromImage(img)
                    scaled_preview = preview_pixmap.scaled(self.diagrama_previews[index].size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.diagrama_previews[index].setPixmap(scaled_preview)
                    pdf_document.close()
                except Exception as e:
                    QMessageBox.warning(self, self.translation_manager.get_text('error_loading_pdf'), 'Ocorreu um erro ao carregar o PDF. Tente novamente.')
                return
            original_pixmap = QPixmap(file_name)
            if not original_pixmap.isNull():
                if not hasattr(self, 'original_diagrams'):
                    self.original_diagrams = [None, None, None]
                if not hasattr(self, 'is_diagrams_pdf'):
                    self.is_diagrams_pdf = [False, False, False]
                self.original_diagrams[index] = original_pixmap
                self.is_diagrams_pdf[index] = False
                preview_pixmap = original_pixmap.scaled(self.diagrama_previews[index].size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.diagrama_previews[index].setPixmap(preview_pixmap)
                width = original_pixmap.width()
                height = original_pixmap.height()
                self.logger.debug(f'Diagrama {index + 1}: {width}x{height}')
    def view_solution(self):
        '''Abre o di├ílogo de visualiza├º├úo da solu├º├úo'''
        try:
            row = self.solutions_table.currentRow()
            solution_id = int(self.solutions_table.item(row, 0).text())
            solution = self.solutions_manager.get_solution_by_id(solution_id)
            def is_pdf(data):
                if not data:
                    return False
                try:
                    return data.startswith(b'%PDF')
                except:
                    return False
            imagem_data = solution.get('imagem_blob')
            diagrama_data = solution.get('diagrama_blob')
            imagem_is_pdf = is_pdf(imagem_data) if imagem_data else False
            diagrama_is_pdf = is_pdf(diagrama_data) if diagrama_data else False
            if imagem_data and diagrama_data:
                dialog = QDialog(self)
                dialog.setWindowTitle('Escolher Visualiza├º├úo')
                layout = QVBoxLayout(dialog)
                if imagem_is_pdf:
                    btn_imagem = QPushButton('Visualizar PDF da Imagem')
                    btn_imagem.clicked.connect((lambda: self.open_pdf(imagem_data, 'imagem')))
                    layout.addWidget(btn_imagem)
                else:
                    btn_imagem = QPushButton('Visualizar Imagem')
                    btn_imagem.clicked.connect((lambda: self.show_image_dialog(imagem_data)))
                    layout.addWidget(btn_imagem)
                if diagrama_is_pdf:
                    btn_diagrama = QPushButton('Visualizar PDF do Diagrama')
                    btn_diagrama.clicked.connect((lambda: self.open_pdf(diagrama_data, 'diagrama')))
                    layout.addWidget(btn_diagrama)
                else:
                    btn_diagrama = QPushButton('Visualizar Diagrama')
                    btn_diagrama.clicked.connect((lambda: self.show_image_dialog(diagrama_data)))
                    layout.addWidget(btn_diagrama)
                btn_close = QPushButton('Fechar')
                btn_close.clicked.connect(dialog.close)
                layout.addWidget(btn_close)
                for btn in dialog.findChildren(QPushButton):
                    btn.setMinimumWidth(200)
                    btn.setMinimumHeight(40)
                    btn.setStyleSheet('\n                        QPushButton {\n                            background-color: #2196F3;\n                            color: white;\n                            border: none;\n                            padding: 8px;\n                            border-radius: 4px;\n                            font-size: 12px;\n                        }\n                        QPushButton:hover {\n                            background-color: #1976D2;\n                        }\n                    ')
                dialog.exec_()
                return
            if imagem_data:
                if imagem_is_pdf:
                    self.open_pdf(imagem_data, 'imagem')
                    return
                self.show_image_dialog(imagem_data)
                return
            if diagrama_data:
                if diagrama_is_pdf:
                    self.open_pdf(diagrama_data, 'diagrama')
                    return
                self.show_image_dialog(diagrama_data)
                return
        except Exception as e:
            QMessageBox.warning(self, self.translation_manager.get_text('error_viewing'), 'Ocorreu um erro ao abrir a visualiza├º├úo. Tente novamente.')
    def open_pdf(self, pdf_data, prefix):
        '''Abre um PDF no visualizador padr├úo do Windows com valida├º├úo de seguran├ºa'''
        try:
            import tempfile
            import os
            if not self._validar_arquivo_seguro(pdf_data, 'pdf'):
                return
            temp_dir = os.path.join(tempfile.gettempdir(), 'union_solutions')
            os.makedirs(temp_dir, exist_ok=True)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', prefix=f'{prefix}_', dir=temp_dir)
            temp_file.write(pdf_data)
            temp_file.close()
            os.startfile(temp_file.name)
            return
        except Exception as e:
            self._mostrar_erro_seguro('Erro ao Abrir Arquivo', 'N├úo foi poss├¡vel abrir o arquivo PDF.', str(e))
    def show_image_dialog(self, image_data):
        '''Mostra uma imagem no visualizador interno'''
        try:
            if not self._validar_arquivo_seguro(image_data, 'imagem'):
                return
            dialog = ImageViewerDialog('Visualizar Imagem', image_data=image_data, parent=self)
            dialog.exec_()
            return
        except Exception as e:
            self._mostrar_erro_seguro('Erro ao Visualizar', 'N├úo foi poss├¡vel abrir a imagem selecionada.', str(e))
    def new_solution(self):
        '''Prepara a interface para criar uma nova solu├º├úo'''
        self.ensure_marca_dropdown_populated()
        self.marca_input.setCurrentIndex(0)
        self.modelo_input.clear()
        self.descricao_input.clear()
        self.observacoes_input.clear()
        for preview in self.imagem_previews:
            preview.clear()
        for preview in self.diagrama_previews:
            preview.clear()
        if hasattr(self, 'original_images'):
            self.original_images = [None, None, None]
        if hasattr(self, 'original_diagrams'):
            self.original_diagrams = [None, None, None]
        if hasattr(self, 'original_diagrams_data'):
            self.original_diagrams_data = [None, None, None]
        if hasattr(self, 'is_diagrams_pdf'):
            self.is_diagrams_pdf = [False, False, False]
        self.ensure_marca_dropdown_populated()
        self.marca_input.setEnabled(True)
        self.modelo_input.setReadOnly(False)
        self.descricao_input.setReadOnly(False)
        self.observacoes_input.setReadOnly(False)
        self.new_btn.setText(self.translation_manager.get_text('save'))
        self.new_btn.clicked.disconnect()
        self.new_btn.clicked.connect(self.save_new_solution)
        self.edit_btn.setText(self.translation_manager.get_text('cancel'))
        self.edit_btn.clicked.disconnect()
        self.edit_btn.clicked.connect(self.cancel_new_solution)
        self.view_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        for btn in self.btn_imagens:
            btn.setEnabled(True)
        for btn in self.btn_diagramas:
            btn.setEnabled(True)
    def save_new_solution(self):
        '''Salva a nova solu├º├úo'''
        try:
            marca = self._sanitizar_texto_entrada(self.marca_input.currentText().strip())
            modelo = self._sanitizar_texto_entrada(self.modelo_input.text().strip())
            descricao = self._sanitizar_texto_entrada(self.descricao_input.toPlainText().strip())
            observacoes = self._sanitizar_texto_entrada(self.observacoes_input.toPlainText().strip())
            if not all([marca, modelo, descricao]):
                QMessageBox.warning(self, self.translation_manager.get_text('required_fields'), self.translation_manager.get_text('please_fill_required_fields'))
                return
            imagem_blobs = [None, None, None]
            if hasattr(self, 'original_images'):
                for i, img in enumerate(self.original_images):
                    if img:
                        ba = QByteArray()
                        buffer = QBuffer(ba)
                        buffer.open(QBuffer.WriteOnly)
                        img.save(buffer, 'PNG', quality=100)
                        imagem_blobs[i] = ba.data()
            diagrama_blobs = [None, None, None]
            if hasattr(self, 'is_diagrams_pdf') and len(self.is_diagrams_pdf) > 0 and self.is_diagrams_pdf[0]:
                if hasattr(self, 'original_diagrams_data') and self.original_diagrams_data[0]:
                    diagrama_blobs[0] = self.original_diagrams_data[0]
            elif hasattr(self, 'original_diagrams') and len(self.original_diagrams) > 0 and self.original_diagrams[0]:
                ba = QByteArray()
                buffer = QBuffer(ba)
                buffer.open(QBuffer.WriteOnly)
                self.original_diagrams[0].save(buffer, 'PNG', quality=100)
                diagrama_blobs[0] = ba.data()
            if hasattr(self, 'is_diagrams_pdf') and len(self.is_diagrams_pdf) > 1 and self.is_diagrams_pdf[1]:
                if hasattr(self, 'original_diagrams_data') and len(self.original_diagrams_data) > 1 and self.original_diagrams_data[1]:
                    diagrama_blobs[1] = self.original_diagrams_data[1]
            elif hasattr(self, 'original_diagrams') and len(self.original_diagrams) > 1 and self.original_diagrams[1]:
                ba = QByteArray()
                buffer = QBuffer(ba)
                buffer.open(QBuffer.WriteOnly)
                self.original_diagrams[1].save(buffer, 'PNG', quality=100)
                diagrama_blobs[1] = ba.data()
            self.solutions_manager.add_solution(marca=marca, modelo=modelo, descricao=descricao, observacoes=observacoes, imagem_blob=imagem_blobs[0], diagrama_blob=diagrama_blobs[0], imagem_1_blob=imagem_blobs[1], imagem_2_blob=imagem_blobs[2], diagrama_2_blob=diagrama_blobs[1])
            self.restore_interface()
            self.load_solutions()
            QMessageBox.information(self, self.translation_manager.get_text('success'), self.translation_manager.get_text('solution_added_successfully'))
            return
        except Exception as e:
            self._mostrar_erro_seguro(self.translation_manager.get_text('error_saving'), 'N├úo foi poss├¡vel salvar a solu├º├úo. Verifique os dados e tente novamente.', str(e))
    def cancel_new_solution(self):
        '''Cancela a cria├º├úo de uma nova solu├º├úo'''
        self.restore_interface()
    def restore_interface(self):
        '''Restaura a interface ao estado normal'''
        self.clear_details()
        self.marca_input.setEnabled(False)
        self.modelo_input.setReadOnly(True)
        self.descricao_input.setReadOnly(True)
        self.observacoes_input.setReadOnly(True)
        self.new_btn.setText(self.translation_manager.get_text('new_solution'))
        self.new_btn.clicked.disconnect()
        self.new_btn.clicked.connect(self.new_solution)
        self.edit_btn.setText(self.translation_manager.get_text('edit'))
        self.edit_btn.clicked.disconnect()
        self.edit_btn.clicked.connect(self.edit_solution)
        for btn in self.btn_imagens:
            btn.setEnabled(False)
        for btn in self.btn_diagramas:
            btn.setEnabled(False)
    def edit_solution(self):
        '''Prepara a interface para editar a solu├º├úo atual'''
        QMessageBox.information(self, 'Edi├º├úo de Solu├º├úo - TECH UNION', '\nEsta edi├º├úo ser├í salva localmente no seu dispositivo\n\nBenef├¡cios:\nÔÇó Altera├º├úo r├ípida e segura\nÔÇó Seus dados ficam protegidos\nÔÇó Dispon├¡vel mesmo offline\n\nInforma├º├Áes importantes:\nÔÇó Esta edi├º├úo n├úo afeta solu├º├Áes j├í compartilhadas\nÔÇó Para altera├º├Áes em solu├º├Áes compartilhadas, entre em contato com o suporte\nÔÇó Use "Compartilhar" para enviar novas vers├Áes ├á comunidade\n\nD├║vidas? Entre em contato com nosso suporte t├®cnico\n            '.strip())
        self.ensure_marca_dropdown_populated()
        self.marca_input.setEnabled(True)
        self.modelo_input.setReadOnly(False)
        self.descricao_input.setReadOnly(False)
        self.observacoes_input.setReadOnly(False)
        self.edit_btn.setText(self.translation_manager.get_text('save'))
        self.edit_btn.clicked.disconnect()
        self.edit_btn.clicked.connect(self.save_edit_solution)
        self.new_btn.setText(self.translation_manager.get_text('cancel'))
        self.new_btn.clicked.disconnect()
        self.new_btn.clicked.connect(self.cancel_edit_solution)
        self.view_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        for btn in self.btn_imagens:
            btn.setEnabled(True)
        for btn in self.btn_diagramas:
            btn.setEnabled(True)
    def save_edit_solution(self):
        '''Salva as altera├º├Áes na solu├º├úo'''
        try:
            marca = self._sanitizar_texto_entrada(self.marca_input.currentText().strip())
            modelo = self._sanitizar_texto_entrada(self.modelo_input.text().strip())
            descricao = self._sanitizar_texto_entrada(self.descricao_input.toPlainText().strip())
            observacoes = self._sanitizar_texto_entrada(self.observacoes_input.toPlainText().strip())
            if not all([marca, modelo, descricao]):
                QMessageBox.warning(self, self.translation_manager.get_text('required_fields'), self.translation_manager.get_text('please_fill_required_fields'))
                return
            row = self.solutions_table.currentRow()
            solution_id = int(self.solutions_table.item(row, 0).text())
            imagem_blobs = [None, None, None]
            for i, preview in enumerate(self.imagem_previews):
                pixmap = preview.pixmap()
                if not pixmap:
                    continue
                if pixmap.isNull():
                    continue
                ba = QByteArray()
                buffer = QBuffer(ba)
                buffer.open(QBuffer.WriteOnly)
                pixmap.save(buffer, 'PNG', quality=100)
                imagem_blobs[i] = ba.data()
            diagrama_blobs = [None, None, None]
            for i, preview in enumerate(self.diagrama_previews[:2]):
                pixmap = preview.pixmap()
                if not pixmap:
                    continue
                if pixmap.isNull():
                    continue
                ba = QByteArray()
                buffer = QBuffer(ba)
                buffer.open(QBuffer.WriteOnly)
                pixmap.save(buffer, 'PNG', quality=100)
                diagrama_blobs[i] = ba.data()
            self.solutions_manager.update_solution(id=solution_id, marca=marca, modelo=modelo, descricao=descricao, observacoes=observacoes, imagem_blob=imagem_blobs[0], diagrama_blob=diagrama_blobs[0], imagem_1_blob=imagem_blobs[1], imagem_2_blob=imagem_blobs[2], diagrama_2_blob=diagrama_blobs[1])
            self.restore_interface()
            self.load_solutions()
            QMessageBox.information(self, self.translation_manager.get_text('success'), self.translation_manager.get_text('solution_updated_successfully'))
            return
        except Exception as e:
            self._mostrar_erro_seguro(self.translation_manager.get_text('error_updating'), 'N├úo foi poss├¡vel atualizar a solu├º├úo. Verifique os dados e tente novamente.', str(e))
    def cancel_edit_solution(self):
        '''Cancela a edi├º├úo da solu├º├úo atual'''
        self.restore_interface()
        self.show_solution_details()
    def delete_solution(self):
        '''Exclui a solu├º├úo selecionada'''
        try:
            if not self.solutions_table.selectedItems():
                QMessageBox.warning(self, self.translation_manager.get_text('select_solution'), self.translation_manager.get_text('please_select_solution'))
                return
            row = self.solutions_table.currentRow()
            id_item = self.solutions_table.item(row, 0)
            if not id_item:
                QMessageBox.warning(self, self.translation_manager.get_text('error'), self.translation_manager.get_text('could_not_identify_solution'))
                return
            solution_id = int(id_item.text())
            msgBox = QMessageBox(self)
            msgBox.setWindowTitle(self.translation_manager.get_text('confirm_deletion'))
            msgBox.setText(self.translation_manager.get_text('are_you_sure_delete_solution'))
            msgBox.setIcon(QMessageBox.Question)
            btn_sim = msgBox.addButton('Sim', QMessageBox.YesRole)
            btn_nao = msgBox.addButton('N├úo', QMessageBox.NoRole)
            msgBox.setDefaultButton(btn_nao)
            msgBox.exec_()
            clicked_button = msgBox.clickedButton()
            if clicked_button == btn_sim:
                self.solutions_manager.delete_solution(solution_id)
                self.clear_details()
                self.load_solutions()
                QMessageBox.information(self, self.translation_manager.get_text('success'), self.translation_manager.get_text('solution_deleted_successfully'))
                return
        except Exception as e:
            self._mostrar_erro_seguro(self.translation_manager.get_text('error_deleting'), 'N├úo foi poss├¡vel excluir a solu├º├úo. Tente novamente mais tarde.', str(e))
    def on_selection_changed(self):
        '''Atualiza o estado dos bot├Áes baseado na sele├º├úo da tabela'''
        has_selection = len(self.solutions_table.selectedItems()) > 0
        self.view_btn.setEnabled(has_selection)
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        self.share_btn.setEnabled(has_selection)
    def refresh_interface(self):
        '''Atualiza a interface com o novo idioma'''
        self.setWindowTitle('TECH UNION - ' + self.translation_manager.get_text('my_solutions'))
        self.solutions_table.setHorizontalHeaderLabels(['ID', self.translation_manager.get_text('brand'), self.translation_manager.get_text('model'), self.translation_manager.get_text('description')])
        self.search_input.setPlaceholderText(self.translation_manager.get_text('search_by_brand_model'))
        self.view_btn.setText(self.translation_manager.get_text('view'))
        self.edit_btn.setText(self.translation_manager.get_text('edit'))
        self.delete_btn.setText(self.translation_manager.get_text('delete'))
        self.new_btn.setText(self.translation_manager.get_text('new_solution'))
        for btn in self.findChildren(QPushButton):
            if 'voltar' in btn.text().lower() or 'back' in btn.text().lower() or 'volver' in btn.text().lower():
                btn.setText(self.translation_manager.get_text('back'))
        for label in self.findChildren(QLabel):
            if 'brand:' in label.text().lower():
                label.setText(self.translation_manager.get_text('brand') + ':')
                continue
            if 'model:' in label.text().lower():
                label.setText(self.translation_manager.get_text('model') + ':')
                continue
            if 'description:' in label.text().lower():
                label.setText(self.translation_manager.get_text('description') + ':')
                continue
            if 'observations:' in label.text().lower():
                label.setText(self.translation_manager.get_text('observations') + ':')
                continue
            if 'image:' in label.text().lower():
                label.setText(self.translation_manager.get_text('image') + ':')
                continue
            if 'diagram:' not in label.text().lower():
                continue
            label.setText(self.translation_manager.get_text('diagram') + ':')
            continue
        if hasattr(self, 'btn_imagens'):
            for i, btn in enumerate(self.btn_imagens):
                btn.setText(self.translation_manager.get_text('select_image'))
        if hasattr(self, 'btn_diagramas'):
            for i, btn in enumerate(self.btn_diagramas):
                btn.setText(self.translation_manager.get_text('select_diagram'))
        current_index = self.brand_combo.currentIndex()
        self.brand_combo.clear()
        self.brand_combo.addItem(self.translation_manager.get_text('all'))
        self.brand_combo.setCurrentIndex(current_index)
    def compartilhar_solucao(self):
        '''Compartilha a solu├º├úo selecionada com a comunidade'''
        try:
            if not self.solutions_table.selectedItems():
                QMessageBox.warning(self, 'Sele├º├úo Necess├íria', 'Por favor, selecione uma solu├º├úo para compartilhar.')
                return
            row = self.solutions_table.currentRow()
            solution_id = int(self.solutions_table.item(row, 0).text())
            solution = self.solutions_manager.get_solution_by_id(solution_id)
            if not solution:
                QMessageBox.warning(self, 'Erro', 'N├úo foi poss├¡vel obter os dados da solu├º├úo.')
                return
            if isinstance(solution, tuple):
                solution_dict = {'id': solution[0], 'marca': solution[1], 'modelo': solution[2], 'descricao': solution[3], 'observacoes': solution[4] if len(solution) > 4 else '', 'status': solution[5] if len(solution) > 5 else 'ativo', 'data_criacao': solution[6] if len(solution) > 6 else '', 'imagem_blob': solution[7] if len(solution) > 7 else None, 'diagrama_blob': solution[8] if len(solution) > 8 else None, 'imagem_1_blob': solution[9] if len(solution) > 9 else None, 'imagem_2_blob': solution[10] if len(solution) > 10 else None, 'diagrama_2_blob': solution[11] if len(solution) > 11 else None, 'permite_compartilhamento': solution[12] if len(solution) > 12 else 1}
            else:
                solution_dict = solution
            if not solution_dict.get('permite_compartilhamento', 1):
                QMessageBox.warning(self, 'Compartilhamento Negado', 'Esta solu├º├úo n├úo permite compartilhamento.')
                return
            user_email = getattr(self.parent_window, 'user_email', None) if self.parent_window else None
            compartilhamento = CompartilhamentoSeguro(self.user_id, user_email)
            pode_compartilhar, compartilhamentos_hoje = compartilhamento.verificar_limite_compartilhamentos()
            tem_instagram, info_instagram = compartilhamento.verificar_instagram_cadastrado()
            if not tem_instagram:
                abrir_perfil, cancelar = compartilhamento.mostrar_dialogo_instagram(self, info_instagram)
                if abrir_perfil:
                    user_email = getattr(self.parent_window, 'user_email', None) if self.parent_window else None
                    if user_email:
                        pass
            try:
                perfil_window = PerfilWindow(user_email, self)
                result = perfil_window.exec_()
                compartilhamento.limpar_cache_instagram()
                tem_instagram_novo, info_instagram_novo = compartilhamento.verificar_instagram_cadastrado()
                if tem_instagram_novo:
                    QMessageBox.information(self, 'Instagram Cadastrado - TECH UNION', f'Perfeito! Instagram @{info_instagram_novo} cadastrado com sucesso!\n\nAgora voc├¬ pode compartilhar suas solu├º├Áes.')
                    self.compartilhar_solucao()
                    return
                QMessageBox.information(self, 'Instagram N├úo Cadastrado - TECH UNION', 'Para compartilhar suas solu├º├Áes, voc├¬ precisa cadastrar seu Instagram no perfil.\n\nVoc├¬ pode tentar novamente a qualquer momento!')
            except Exception as e:
                self.logger.error(f'Erro ao abrir tela de perfil: {str(e)}')
                QMessageBox.warning(self, 'Erro', 'N├úo foi poss├¡vel abrir a tela de perfil. Tente novamente.')
            else:
                return
        except Exception as e:
            self._mostrar_erro_seguro('Erro no Compartilhamento', 'N├úo foi poss├¡vel compartilhar a solu├º├úo. Tente novamente mais tarde.', str(e))
    def update_statistics(self):
        '''Atualiza as estat├¡sticas na interface'''
        try:
            total_compartilhadas = self.solutions_manager.contar_solucoes_compartilhadas()
            self.stats_label.setText(f'Compartilhadas: {total_compartilhadas}')
            return
        except Exception as e:
            self.logger.error(f'Erro ao atualizar estat├¡sticas: {str(e)}')
            self.stats_label.setText('Estatisticas indisponiveis')
    def _validar_arquivo_seguro(self, dados_arquivo, tipo_esperado):
        '''
        VALIDA├ç├âO DE SEGURAN├çA - Verifica se arquivo ├® seguro antes de processar
        Mant├®m funcionalidade original, apenas adiciona prote├º├úo
        '''
        try:
            tamanho_mb = len(dados_arquivo) / 1048576
            limite_mb = 100
            if tamanho_mb > limite_mb:
                self._mostrar_erro_seguro('Arquivo Muito Grande', f'O arquivo ├® muito grande ({tamanho_mb:.1f}MB). Limite: {limite_mb}MB.', 'Arquivo excede limite de tamanho')
                return False
            if tipo_esperado == 'pdf':
                if not dados_arquivo.startswith(b'%PDF'):
                    self._mostrar_erro_seguro('Arquivo Inv├ílido', 'O arquivo selecionado n├úo ├® um PDF v├ílido.', 'Cabe├ºalho PDF inv├ílido')
                    return False
                assinaturas_suspeitas = [b'<script', b'javascript:', b'eval(']
                for assinatura in assinaturas_suspeitas:
                    if not assinatura.lower() in dados_arquivo.lower():
                        continue
                    self._mostrar_erro_seguro('Arquivo Suspeito', 'O arquivo PDF cont├®m conte├║do suspeito e n├úo pode ser aberto.', f'Assinatura suspeita encontrada: {assinatura}')
                    return False
                return True
            if tipo_esperado in ('imagem', 'image'):
                cabecalhos_validos = [b'\xff\xd8\xff', b'\x89PNG\r\n\x1a\n', b'GIF87a', b'GIF89a', b'BM']
                if not any((dados_arquivo.startswith(cabecalho) for cabecalho in cabecalhos_validos)):
                    self._mostrar_erro_seguro('Formato N├úo Suportado', 'O arquivo selecionado n├úo ├® uma imagem v├ílida.', 'Cabe├ºalho de imagem inv├ílido')
                    return False
        except Exception as e:
            self._mostrar_erro_seguro('Erro de Valida├º├úo', 'N├úo foi poss├¡vel validar o arquivo selecionado.', str(e))
            return False
        return True
    def _sanitizar_texto_entrada(self, texto):
        '''
        SANITIZA├ç├âO DE ENTRADA (Corre├º├úo #2 - Prioridade M├®dia)
        Remove caracteres perigosos mantendo funcionalidade
        '''
        import re
        if not texto:
            return ''
        texto_limpo = re.sub('[<>"\\\'\\\\;]', '', texto)
        palavras_perigosas = ['<script', 'javascript:', 'eval(', 'exec(', 'system(']
        for palavra in palavras_perigosas:
            texto_limpo = texto_limpo.replace(palavra.lower(), '')
            texto_limpo = texto_limpo.replace(palavra.upper(), '')
        return texto_limpo.strip()
    def _mostrar_erro_seguro(self, titulo, mensagem_usuario, erro_tecnico):
        '''
        TRATAMENTO DE ERRO SEGURO (Corre├º├úo #3 - Prioridade M├®dia)
        Mostra erro amig├ível para usu├írio, registra detalhes t├®cnicos no log
        '''
        try:
            if hasattr(self, 'logger'):
                self.logger.error(f'Erro t├®cnico: {erro_tecnico}')
            QMessageBox.warning(self, titulo, mensagem_usuario)
            return
        except Exception as fallback_error:
            QMessageBox.warning(self, 'Erro', 'Ocorreu um erro inesperado.')
            if hasattr(self, 'logger'):
                self.logger.error(f'Fallback erro seguro: {fallback_error}')
