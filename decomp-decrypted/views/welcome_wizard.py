from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QProgressBar, QStackedWidget, QWidget, QFrame, QMessageBox, QDesktopWidget, QTextEdit, QSizePolicy, QSpacerItem, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import (QFont, QPixmap, QIcon)
import pymysql
import logging
import re
import uuid
import time
from datetime import datetime
from app.utils.translation_manager import TranslationManager
from app.utils._app_cfg import db_config
MYSQL_CONFIG = db_config(ssl={'ca': None}, ssl_verify_cert=False)
logger = logging.getLogger(__name__)
class WelcomeWizard(QDialog):
    wizard_completed = pyqtSignal()
    def __init__(self, user_email, parent=None):
        super().__init__(parent)
        self.user_email = user_email
        self.user_id = None
        self.current_step = 0
        self.total_steps = 4
        self.translation_manager = TranslationManager.get_instance()
        self.dynamic_widgets = {}
        self.setWindowTitle(self.translation_manager.get_text('welcome_wizard_title'))
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.setModal(True)
        self.setup_window_size()
        self.setup_ui()
        self.carregar_user_id()
        logger.info(f'WelcomeWizard iniciado para usu├írio: {self.user_email}')
    def setup_window_size(self):
        desktop = QDesktopWidget()
        screen_rect = desktop.availableGeometry()
        screen_width = screen_rect.width()
        screen_height = screen_rect.height()
        if screen_height <= 768:
            window_width = min(500, screen_width - 80)
            window_height = min(550, screen_height - 100)
            self.compact_mode = True
            self.ultra_compact = True
            self.font_size_title = 16
            self.font_size_text = 10
            self.spacing = 8
            self.button_height = 45
            logger.info(f'Modo ULTRA COMPACTO ativado ({screen_width}x{screen_height})')
        elif screen_height <= 900:
            window_width = min(600, screen_width - 100)
            window_height = min(600, screen_height - 90)
            self.compact_mode = True
            self.ultra_compact = False
            self.font_size_title = 18
            self.font_size_text = 11
            self.spacing = 10
            self.button_height = 50
            logger.info(f'Modo COMPACTO ativado ({screen_width}x{screen_height})')
        elif screen_height <= 1080:
            window_width = 650
            window_height = 650
            self.compact_mode = False
            self.ultra_compact = False
            self.font_size_title = 20
            self.font_size_text = 12
            self.spacing = 12
            self.button_height = 55
            logger.info(f'Modo M├ëDIO ativado ({screen_width}x{screen_height})')
        else:
            window_width = 700
            window_height = 700
            self.compact_mode = False
            self.ultra_compact = False
            self.font_size_title = 22
            self.font_size_text = 13
            self.spacing = 15
            self.button_height = 60
            logger.info(f'Modo PADR├âO ativado ({screen_width}x{screen_height})')
        self.setMinimumSize(480, 500)
        self.setMaximumSize(min(800, screen_width - 50), min(900, screen_height - 50))
        self.resize(window_width, window_height)
        x = screen_rect.x() + (screen_rect.width() - window_width) // 2
        y = screen_rect.y() + (screen_rect.height() - window_height) // 2
        self.move(max(screen_rect.x(), x), max(screen_rect.y(), y))
        logger.info(f'Ô£à Janela: {window_width}x{window_height} | Tela: {screen_width}x{screen_height} | Posi├º├úo: ({x}, {y})')
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(self.spacing)
        layout.setContentsMargins(20, 20, 20, 20)
        header_frame = QFrame()
        header_frame.setStyleSheet('\n            QFrame {\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, \n                    stop:0 #2c3e50, stop:1 #3498db);\n                border-radius: 8px;\n                padding: 15px;\n            }\n        ')
        header_layout = QVBoxLayout(header_frame)
        header_layout.setSpacing(5)
        title_label = QLabel(self.translation_manager.get_text('welcome_wizard_title'))
        title_label.setStyleSheet(f'\n            color: white;\n            font-size: {self.font_size_title}px;\n            font-weight: bold;\n        ')
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label)
        self.dynamic_widgets['header_title'] = title_label
        layout.addWidget(header_frame)
        progress_frame = QFrame()
        progress_frame.setStyleSheet('\n            QFrame {\n                background-color: #f8f9fa;\n                border-radius: 5px;\n                padding: 10px;\n            }\n        ')
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setSpacing(5)
        self.progress_label = QLabel(self.translation_manager.get_text('welcome_step_progress').format(1, self.total_steps))
        self.progress_label.setStyleSheet(f'\n            color: #2c3e50;\n            font-size: {self.font_size_text}px;\n            font-weight: 600;\n        ')
        self.progress_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.progress_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(self.total_steps)
        self.progress_bar.setValue(1)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet('\n            QProgressBar {\n                border: 2px solid #bdc3c7;\n                border-radius: 5px;\n                background-color: #ecf0f1;\n                height: 20px;\n            }\n            QProgressBar::chunk {\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, \n                    stop:0 #3498db, stop:1 #2980b9);\n                border-radius: 3px;\n            }\n        ')
        progress_layout.addWidget(self.progress_bar)
        layout.addWidget(progress_frame)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet('\n            QScrollArea {\n                background-color: white;\n                border: 2px solid #ecf0f1;\n                border-radius: 8px;\n            }\n        ')
        self.pages = QStackedWidget()
        self.pages.setStyleSheet('\n            QStackedWidget {\n                background-color: white;\n                padding: 10px;\n            }\n        ')
        self.pages.addWidget(self.create_step0_language())
        self.pages.addWidget(self.create_step1_welcome())
        self.pages.addWidget(self.create_step2_profile_data())
        self.pages.addWidget(self.create_step3_confirmation())
        scroll_area.setWidget(self.pages)
        layout.addWidget(scroll_area)
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        self.btn_previous = QPushButton(self.translation_manager.get_text('welcome_btn_previous'))
        self.btn_previous.setEnabled(False)
        self.btn_previous.setStyleSheet(self.get_button_style('#95a5a6'))
        self.btn_previous.clicked.connect(self.previous_step)
        buttons_layout.addWidget(self.btn_previous)
        buttons_layout.addStretch()
        self.btn_next = QPushButton(self.translation_manager.get_text('welcome_btn_next'))
        self.btn_next.setStyleSheet(self.get_button_style('#27ae60'))
        self.btn_next.clicked.connect(self.next_step)
        buttons_layout.addWidget(self.btn_next)
        layout.addLayout(buttons_layout)
    def get_button_style(self, color):
        font_size = 12 if self.compact_mode else 14
        padding = '10px 20px' if self.compact_mode else '12px 24px'
        return f'\n            QPushButton {{\n                background-color: {color};\n                color: white;\n                border: none;\n                border-radius: 6px;\n                padding: {padding};\n                font-size: {font_size}px;\n                font-weight: bold;\n                min-width: 100px;\n            }}\n            QPushButton:hover {{\n                background-color: {color}dd;\n            }}\n            QPushButton:pressed {{\n                background-color: {color}aa;\n            }}\n            QPushButton:disabled {{\n                background-color: #bdc3c7;\n                color: #7f8c8d;\n            }}\n        '
    def create_step0_language(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(self.spacing)
        layout.setContentsMargins(20, 20, 20, 20)
        title = QLabel('Select Your Language / Selecione seu Idioma / Seleccione su Idioma')
        title.setStyleSheet(f'\n            color: #2c3e50;\n            font-size: {self.font_size_title - 2}px;\n            font-weight: bold;\n        ')
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        layout.addWidget(title)
        layout.addSpacing(20)
        buttons_container = QWidget()
        buttons_layout = QVBoxLayout(buttons_container)
        buttons_layout.setSpacing(15)
        buttons_layout.setContentsMargins(40, 0, 40, 0)
        idioma_atual = self.translation_manager.get_current_language()
        btn_pt = QPushButton('Portugu├¬s (Brasil)')
        btn_pt.setStyleSheet(self._get_language_button_style(selected=idioma_atual == 'pt'))
        btn_pt.clicked.connect((lambda: self._selecionar_idioma('pt', btn_pt)))
        btn_pt.setMinimumHeight(self.button_height)
        btn_pt.setCursor(Qt.PointingHandCursor)
        buttons_layout.addWidget(btn_pt)
        btn_en = QPushButton('English (USA)')
        btn_en.setStyleSheet(self._get_language_button_style(selected=idioma_atual == 'en'))
        btn_en.clicked.connect((lambda: self._selecionar_idioma('en', btn_en)))
        btn_en.setMinimumHeight(self.button_height)
        btn_en.setCursor(Qt.PointingHandCursor)
        buttons_layout.addWidget(btn_en)
        btn_es = QPushButton('Espa├▒ol')
        btn_es.setStyleSheet(self._get_language_button_style(selected=idioma_atual == 'es'))
        btn_es.clicked.connect((lambda: self._selecionar_idioma('es', btn_es)))
        btn_es.setMinimumHeight(self.button_height)
        btn_es.setCursor(Qt.PointingHandCursor)
        buttons_layout.addWidget(btn_es)
        self.language_buttons = {'pt': btn_pt, 'en': btn_en, 'es': btn_es}
        layout.addWidget(buttons_container)
        layout.addStretch()
        help_text = QLabel('Choose your preferred language to continue\nEscolha seu idioma preferido para continuar\nElija su idioma preferido para continuar')
        help_text.setStyleSheet(f'\n            color: #7f8c8d;\n            font-size: {self.font_size_text - 2}px;\n            font-style: italic;\n        ')
        help_text.setAlignment(Qt.AlignCenter)
        help_text.setWordWrap(True)
        layout.addWidget(help_text)
        return page
    def _get_language_button_style(self, selected=False):
        font_size = 14 if self.compact_mode else 16
        if selected:
            return f'\n                QPushButton {{\n                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, \n                        stop:0 #27ae60, stop:1 #2ecc71);\n                    color: white;\n                    border: 3px solid #229954;\n                    border-radius: 8px;\n                    padding: 15px;\n                    font-size: {font_size}px;\n                    font-weight: bold;\n                    text-align: left;\n                }}\n                QPushButton:hover {{\n                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, \n                        stop:0 #229954, stop:1 #27ae60);\n                    border: 3px solid #1e8449;\n                }}\n            '
        return f'\n                QPushButton {{\n                    background-color: #f8f9fa;\n                    color: #2c3e50;\n                    border: 2px solid #dee2e6;\n                    border-radius: 8px;\n                    padding: 15px;\n                    font-size: {font_size}px;\n                    font-weight: 600;\n                    text-align: left;\n                }}\n                QPushButton:hover {{\n                    background-color: #e9ecef;\n                    border: 2px solid #adb5bd;\n                }}\n                QPushButton:pressed {{\n                    background-color: #dee2e6;\n                }}\n            '
    def _selecionar_idioma(self, codigo_idioma, botao_clicado):
        idiomas_validos = ['pt', 'en', 'es']
        if codigo_idioma not in idiomas_validos:
            logger.warning(f'Idioma inv├ílido: {codigo_idioma}')
            return
        self.translation_manager.set_language(codigo_idioma)
        logger.info(f'Idioma alterado para: {codigo_idioma}')
        for codigo, botao in self.language_buttons.items():
            botao.setStyleSheet(self._get_language_button_style(selected=codigo == codigo_idioma))
        self._atualizar_textos_interface()
    def _atualizar_textos_interface(self):
        self.setWindowTitle(self.translation_manager.get_text('welcome_wizard_title'))
        if 'header_title' in self.dynamic_widgets:
            self.dynamic_widgets['header_title'].setText(self.translation_manager.get_text('welcome_wizard_title'))
        self.btn_previous.setText(self.translation_manager.get_text('welcome_btn_previous'))
        if self.current_step == self.total_steps - 1:
            self.btn_next.setText(self.translation_manager.get_text('welcome_btn_finish'))
        else:
            self.btn_next.setText(self.translation_manager.get_text('welcome_btn_next'))
        self.progress_label.setText(self.translation_manager.get_text('welcome_step_progress').format(self.current_step + 1, self.total_steps))
        if 'step1_title' in self.dynamic_widgets:
            self.dynamic_widgets['step1_title'].setText(self.translation_manager.get_text('welcome_step1_title'))
        if 'step1_message' in self.dynamic_widgets:
            self.dynamic_widgets['step1_message'].setText(self.translation_manager.get_text('welcome_step1_message'))
        if 'step2_title' in self.dynamic_widgets:
            self.dynamic_widgets['step2_title'].setText(self.translation_manager.get_text('welcome_step2_title'))
        if 'step2_message' in self.dynamic_widgets:
            self.dynamic_widgets['step2_message'].setText(self.translation_manager.get_text('welcome_step2_message'))
        if 'nome_label' in self.dynamic_widgets:
            self.dynamic_widgets['nome_label'].setText(self.translation_manager.get_text('welcome_name_label') + ' *')
        if 'telefone_label' in self.dynamic_widgets:
            self.dynamic_widgets['telefone_label'].setText(self.translation_manager.get_text('welcome_phone_label'))
        if 'localizacao_label' in self.dynamic_widgets:
            self.dynamic_widgets['localizacao_label'].setText(self.translation_manager.get_text('welcome_location_label'))
        if 'nome_field' in self.dynamic_widgets:
            self.dynamic_widgets['nome_field'].setPlaceholderText(self.translation_manager.get_text('welcome_name_placeholder'))
        if 'telefone_field' in self.dynamic_widgets:
            self.dynamic_widgets['telefone_field'].setPlaceholderText(self.translation_manager.get_text('welcome_phone_placeholder'))
        if 'localizacao_field' in self.dynamic_widgets:
            self.dynamic_widgets['localizacao_field'].setPlaceholderText(self.translation_manager.get_text('welcome_location_placeholder'))
        if 'step3_title' in self.dynamic_widgets:
            self.dynamic_widgets['step3_title'].setText(self.translation_manager.get_text('welcome_step3_title'))
        if 'step3_message' in self.dynamic_widgets:
            self.dynamic_widgets['step3_message'].setText(self.translation_manager.get_text('welcome_step3_message'))
        logger.info('Textos da interface atualizados para o idioma selecionado')
    def create_step1_welcome(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(self.spacing)
        layout.setContentsMargins(20, 20, 20, 20)
        title = QLabel(self.translation_manager.get_text('welcome_step1_title'))
        title.setStyleSheet(f'\n            color: #2c3e50;\n            font-size: {self.font_size_title}px;\n            font-weight: bold;\n        ')
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        self.dynamic_widgets['step1_title'] = title
        layout.addSpacing(10)
        message = QLabel(self.translation_manager.get_text('welcome_step1_message'))
        message.setStyleSheet(f'\n            color: #34495e;\n            font-size: {self.font_size_text}px;\n            line-height: 1.6;\n        ')
        message.setWordWrap(True)
        message.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        layout.addWidget(message)
        self.dynamic_widgets['step1_message'] = message
        layout.addStretch()
        return page
    def create_step2_profile_data(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(self.spacing)
        layout.setContentsMargins(20, 20, 20, 20)
        title = QLabel(self.translation_manager.get_text('welcome_step2_title'))
        title.setStyleSheet(f'\n            color: #2c3e50;\n            font-size: {self.font_size_title}px;\n            font-weight: bold;\n        ')
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        self.dynamic_widgets['step2_title'] = title
        message = QLabel(self.translation_manager.get_text('welcome_step2_message'))
        message.setStyleSheet(f'\n            color: #7f8c8d;\n            font-size: {max(11, self.font_size_text - 1)}px;\n        ')
        message.setWordWrap(True)
        message.setAlignment(Qt.AlignCenter)
        layout.addWidget(message)
        self.dynamic_widgets['step2_message'] = message
        layout.addSpacing(15)
        nome_label = QLabel(self.translation_manager.get_text('welcome_name_label') + ' *')
        nome_label.setStyleSheet(f'\n            color: #2c3e50;\n            font-size: {self.font_size_text}px;\n            font-weight: bold;\n        ')
        layout.addWidget(nome_label)
        self.dynamic_widgets['nome_label'] = nome_label
        self.nome_field = QLineEdit()
        self.nome_field.setPlaceholderText(self.translation_manager.get_text('welcome_name_placeholder'))
        self.nome_field.setStyleSheet(self.get_field_style())
        layout.addWidget(self.nome_field)
        self.dynamic_widgets['nome_field'] = self.nome_field
        layout.addSpacing(10)
        telefone_label = QLabel(self.translation_manager.get_text('welcome_phone_label'))
        telefone_label.setStyleSheet(f'\n            color: #2c3e50;\n            font-size: {self.font_size_text}px;\n            font-weight: bold;\n        ')
        layout.addWidget(telefone_label)
        self.dynamic_widgets['telefone_label'] = telefone_label
        self.telefone_field = QLineEdit()
        self.telefone_field.setPlaceholderText(self.translation_manager.get_text('welcome_phone_placeholder'))
        self.telefone_field.setStyleSheet(self.get_field_style())
        layout.addWidget(self.telefone_field)
        self.dynamic_widgets['telefone_field'] = self.telefone_field
        layout.addSpacing(10)
        localizacao_label = QLabel(self.translation_manager.get_text('welcome_location_label'))
        localizacao_label.setStyleSheet(f'\n            color: #2c3e50;\n            font-size: {self.font_size_text}px;\n            font-weight: bold;\n        ')
        layout.addWidget(localizacao_label)
        self.dynamic_widgets['localizacao_label'] = localizacao_label
        self.localizacao_field = QLineEdit()
        self.localizacao_field.setPlaceholderText(self.translation_manager.get_text('welcome_location_placeholder'))
        self.localizacao_field.setStyleSheet(self.get_field_style())
        layout.addWidget(self.localizacao_field)
        self.dynamic_widgets['localizacao_field'] = self.localizacao_field
        nota = QLabel('* ' + self.translation_manager.get_text('required_fields'))
        nota.setStyleSheet(f'\n            color: #e74c3c;\n            font-size: {max(10, self.font_size_text - 2)}px;\n            font-style: italic;\n        ')
        layout.addWidget(nota)
        layout.addStretch()
        return page
    def get_field_style(self):
        padding = '8px' if self.compact_mode else '10px'
        font_size = 12 if self.compact_mode else 13
        return f'\n            QLineEdit {{\n                border: 2px solid #bdc3c7;\n                border-radius: 5px;\n                padding: {padding};\n                font-size: {font_size}px;\n                background-color: white;\n                color: #2c3e50;\n            }}\n            QLineEdit:focus {{\n                border-color: #3498db;\n            }}\n        '
    def create_step3_confirmation(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(self.spacing)
        layout.setContentsMargins(20, 20, 20, 20)
        title = QLabel(self.translation_manager.get_text('welcome_step3_title'))
        title.setStyleSheet(f'\n            color: #27ae60;\n            font-size: {self.font_size_title}px;\n            font-weight: bold;\n        ')
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        self.dynamic_widgets['step3_title'] = title
        message = QLabel(self.translation_manager.get_text('welcome_step3_message'))
        message.setStyleSheet(f'\n            color: #34495e;\n            font-size: {self.font_size_text}px;\n            line-height: 1.6;\n        ')
        message.setWordWrap(True)
        message.setAlignment(Qt.AlignCenter)
        layout.addWidget(message)
        self.dynamic_widgets['step3_message'] = message
        layout.addStretch()
        return page
    def carregar_user_id(self):
        try:
            conn = self.conectar_mysql()
            if not conn:
                logger.error('Falha ao conectar ao MySQL no carregar_user_id')
                return
            cursor = conn.cursor()
            cursor.execute('SELECT id_usuario FROM usuarios WHERE email = %s', (self.user_email,))
            usuario = cursor.fetchone()
            if usuario:
                self.user_id = usuario['id_usuario']
                logger.info(f'User ID carregado: {self.user_id}')
            else:
                logger.warning(f'Usu├írio n├úo encontrado no MySQL: {self.user_email}')
            cursor.close()
            conn.close()
            return
        except Exception as e:
            logger.error(f'Erro ao carregar user_id: {str(e)}')
    def conectar_mysql(self):
        try:
            return pymysql.connect(**MYSQL_CONFIG, **{'cursorclass': pymysql.cursors.DictCursor, 'autocommit': False})
        except Exception as e:
            logger.error(f'Erro ao conectar ao MySQL: {str(e)}')
    def previous_step(self):
        if self.current_step > 0:
            self.current_step -= 1
            self.pages.setCurrentIndex(self.current_step)
            self.update_progress()
            if self.current_step == 0:
                self.btn_previous.setEnabled(False)
            self.btn_next.setText(self.translation_manager.get_text('welcome_btn_next'))
            self.btn_next.setStyleSheet(self.get_button_style('#27ae60'))
            logger.info(f'Voltou para etapa {self.current_step + 1}')
    def next_step(self):
        if self.current_step == 2:
            if not self.validar_dados():
                return
            if not self.salvar_perfil():
                return
        if self.current_step == 3:
            logger.info('Wizard conclu├¡do com sucesso')
            self.wizard_completed.emit()
            self.accept()
            return
        if self.current_step < self.total_steps - 1:
            self.current_step += 1
            self.pages.setCurrentIndex(self.current_step)
            self.update_progress()
            self.btn_previous.setEnabled(True)
            if self.current_step == self.total_steps - 1:
                self.btn_next.setText(self.translation_manager.get_text('welcome_btn_finish'))
                self.btn_next.setStyleSheet(self.get_button_style('#3498db'))
            logger.info(f'Avan├ºou para etapa {self.current_step + 1}')
    def update_progress(self):
        self.progress_bar.setValue(self.current_step + 1)
        self.progress_label.setText(self.translation_manager.get_text('welcome_step_progress').format(self.current_step + 1, self.total_steps))
    def validar_dados(self):
        nome_bruto = self.nome_field.text().strip()
        nome = self._sanitizar_entrada_usuario(nome_bruto)
        if not nome or len(nome) < 3:
            QMessageBox.warning(self, self.translation_manager.get_text('warning_title'), self.translation_manager.get_text('welcome_validation_name_required'))
            self.nome_field.setFocus()
            logger.warning('Valida├º├úo falhou: Nome inv├ílido ou muito curto')
            return False
        logger.info('Valida├º├úo de dados passou com sucesso')
        return True
    def _sanitizar_entrada_usuario(self, texto):
        try:
            if not texto:
                return
            texto_limpo = re.sub('[<>"\\\'\\\\;\\x00-\\x1f\\x7f-\\x9f]', '', str(texto))
            texto_limpo = re.sub('<[^>]*>', '', texto_limpo)
            texto_limpo = re.sub('(javascript:|data:|vbscript:|onload|onerror)', '', texto_limpo, flags=re.IGNORECASE)
            texto_limpo = texto_limpo[:500] if len(texto_limpo) > 500 else texto_limpo
        except Exception as e:
            logger.error(f'Erro na sanitiza├º├úo: {str(e)}')
        return texto_limpo.strip() or None
    def salvar_perfil(self):
        try:
            conn = self.conectar_mysql()
            if not conn:
                self._mostrar_erro_seguro(self.translation_manager.get_text('error'), self.translation_manager.get_text('welcome_error_save'))
                return False
            cursor = conn.cursor()
            nome = self._sanitizar_entrada_usuario(self.nome_field.text())
            telefone = self._sanitizar_entrada_usuario(self.telefone_field.text())
            localizacao = self._sanitizar_entrada_usuario(self.localizacao_field.text())
            if not self.user_id:
                cursor.execute('SELECT id_usuario FROM usuarios WHERE email = %s', (self.user_email,))
                usuario = cursor.fetchone()
                if not usuario:
                    licenca_unica = f'UNION-{int(time.time())}-{str(uuid.uuid4())[:8].upper()}'
                    cursor.execute("\n                        INSERT INTO usuarios (email, licenca, nome_usuario, data_registro, status)\n                        VALUES (%s, %s, %s, NOW(), 'ativo')\n                    ", (self.user_email, licenca_unica, nome))
                    self.user_id = cursor.lastrowid
                    logger.info(f'Usu├írio criado: ID={self.user_id}')
                else:
                    self.user_id = usuario['id_usuario']
                    cursor.execute('\n                        UPDATE usuarios SET nome_usuario = %s WHERE id_usuario = %s\n                    ', (nome, self.user_id))
                    logger.info(f'Usu├írio atualizado: ID={self.user_id}')
            cursor.execute('\n                SELECT id_usuario FROM perfil WHERE id_usuario = %s\n            ', (self.user_id,))
            perfil_existe = cursor.fetchone()
            if perfil_existe:
                cursor.execute('\n                    UPDATE perfil SET \n                        nome = %s, telefone = %s, localizacao = %s, updated_at = NOW()\n                    WHERE id_usuario = %s\n                ', (nome, telefone, localizacao, self.user_id))
                logger.info('Perfil atualizado')
            else:
                cursor.execute("\n                    INSERT INTO perfil (id_usuario, nome, telefone, localizacao, \n                                      visibilidade, notificacoes_email, notificacoes_push,\n                                      created_at, updated_at)\n                    VALUES (%s, %s, %s, %s, 'publico', 1, 1, NOW(), NOW())\n                ", (self.user_id, nome, telefone, localizacao))
                logger.info('Perfil criado')
            conn.commit()
            cursor.close()
            conn.close()
            logger.info('Perfil salvo com sucesso no MySQL')
            return True
        except Exception as e:
            logger.error(f'Erro ao salvar perfil: {str(e)}')
            if conn:
                conn.rollback()
            self._mostrar_erro_seguro(self.translation_manager.get_text('error'), self.translation_manager.get_text('welcome_error_save'))
            return False
    def _mostrar_erro_seguro(self, titulo, mensagem_usuario):
        try:
            QMessageBox.critical(self, titulo, mensagem_usuario)
            return
        except Exception:
            logger.error('Falha cr├¡tica ao exibir mensagem de erro')
