from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QMessageBox, QProgressDialog, QGroupBox, QScrollArea, QWidget, QFrame, QSpacerItem, QSizePolicy, QFileDialog, QComboBox, QDateEdit, QCheckBox, QApplication, QDesktopWidget)
from PyQt5.QtCore import (Qt, QTimer, QDate)
from PyQt5.QtGui import (QFont, QPixmap, QIcon)
import pymysql
import logging
from datetime import datetime
import base64
import os
from app.utils._app_cfg import db_config
MYSQL_CONFIG = db_config(ssl={'ca': None}, ssl_verify_cert=False)
logger = logging.getLogger(__name__)
class PerfilWindow(QDialog):
    def __init__(self, user_email, parent=None):
        super().__init__(parent)
        self.user_email = user_email
        self.user_id = None
        self.perfil_existe = False
        self.foto_perfil_data = None
        self.setWindowTitle('Meu Perfil - TECH UNION SOLUTIONS')
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setup_window_size()
        self.setup_ui()
        self.carregar_dados()
    def setup_window_size(self):
        desktop = QDesktopWidget()
        available = desktop.availableGeometry()
        avail_w = available.width()
        avail_h = available.height()
        if avail_h <= 680:
            window_width = min(620, avail_w - 80)
            window_height = min(avail_h - 60, 620)
            self.compact_mode = True
        elif avail_h <= 850:
            window_width = min(680, avail_w - 100)
            window_height = min(avail_h - 80, 700)
            self.compact_mode = True
        else:
            window_width = min(700, avail_w - 100)
            window_height = min(800, avail_h - 80)
            self.compact_mode = False
        self.setMinimumSize(500, 400)
        self.setMaximumSize(avail_w - 40, avail_h - 40)
        self.resize(window_width, window_height)
        if hasattr(self, 'parent') and self.parent():
            parent_geo = self.parent().geometry()
            x = parent_geo.x() + (parent_geo.width() - window_width) // 2
            y = parent_geo.y() + (parent_geo.height() - window_height) // 2
            self.move(max(0, x), max(0, y))
        else:
            x = (avail_w - window_width) // 2 + available.x()
            y = (avail_h - window_height) // 2 + available.y()
            self.move(max(0, x), max(0, y))
        logger.info(f'Janela configurada para area disponivel {avail_w}x{avail_h}: {window_width}x{window_height}')
    def setup_ui(self):
        layout = QVBoxLayout(self)
        if self.compact_mode:
            layout.setSpacing(10)
            layout.setContentsMargins(15, 15, 15, 15)
        else:
            layout.setSpacing(15)
            layout.setContentsMargins(20, 20, 20, 20)
        header_frame = QFrame()
        header_frame.setStyleSheet(f'\n            QFrame {{\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,\n                    stop:0 #1565C0, stop:1 #1976D2);\n                border-radius: 8px;\n                padding: {'10px' if self.compact_mode else '15px'};\n                margin-bottom: {'5px' if self.compact_mode else '10px'};\n            }}\n        ')
        header_layout = QVBoxLayout(header_frame)
        header_layout.setSpacing(5)
        title = QLabel('MEU PERFIL')
        title_size = '20px' if self.compact_mode else '24px'
        title.setStyleSheet(f'\n            color: white;\n            font-size: {title_size};\n            font-weight: bold;\n            text-align: center;\n        ')
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)
        if not self.compact_mode:
            subtitle = QLabel('Gerencie suas informa├º├Áes pessoais e profissionais')
            subtitle.setStyleSheet('\n                color: #ecf0f1;\n                font-size: 14px;\n                text-align: center;\n            ')
            subtitle.setAlignment(Qt.AlignCenter)
            header_layout.addWidget(subtitle)
        layout.addWidget(header_frame)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet('\n            QScrollArea {\n                border: none;\n                background-color: transparent;\n            }\n            QScrollBar:vertical {\n                background: #f1f1f1;\n                width: 12px;\n                border-radius: 6px;\n            }\n            QScrollBar::handle:vertical {\n                background: #3498db;\n                border-radius: 6px;\n                min-height: 20px;\n            }\n            QScrollBar::handle:vertical:hover {\n                background: #2980b9;\n            }\n        ')
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_spacing = 12 if self.compact_mode else 20
        form_layout.setSpacing(form_spacing)
        foto_group = QGroupBox('Foto de Perfil')
        foto_group.setStyleSheet(self.get_group_style())
        foto_layout = QHBoxLayout(foto_group)
        foto_size = 100 if self.compact_mode else 120
        self.foto_label = QLabel()
        self.foto_label.setFixedSize(foto_size, foto_size)
        self.foto_label.setStyleSheet(f'\n            QLabel {{\n                border: 2px solid #bdc3c7;\n                border-radius: {foto_size // 2}px;\n                background-color: #ecf0f1;\n                color: #7f8c8d;\n                font-size: 16px;\n                font-weight: bold;\n                text-align: center;\n            }}\n        ')
        self.foto_label.setText('Foto')
        self.foto_label.setAlignment(Qt.AlignCenter)
        foto_layout.addWidget(self.foto_label)
        foto_buttons_layout = QVBoxLayout()
        self.btn_escolher_foto = QPushButton('Escolher Foto')
        self.btn_escolher_foto.setStyleSheet(self.get_button_style('#3498db'))
        self.btn_escolher_foto.clicked.connect(self.escolher_foto)
        foto_buttons_layout.addWidget(self.btn_escolher_foto)
        self.btn_remover_foto = QPushButton('Remover Foto')
        self.btn_remover_foto.setStyleSheet(self.get_button_style('#e74c3c'))
        self.btn_remover_foto.clicked.connect(self.remover_foto)
        foto_buttons_layout.addWidget(self.btn_remover_foto)
        foto_buttons_layout.addStretch()
        foto_layout.addLayout(foto_buttons_layout)
        form_layout.addWidget(foto_group)
        basic_group = QGroupBox('Informa├º├Áes B├ísicas')
        basic_group.setStyleSheet(self.get_group_style())
        basic_layout = QFormLayout(basic_group)
        basic_layout.setSpacing(8 if self.compact_mode else 10)
        self.email_field = QLineEdit(self.user_email)
        self.email_field.setReadOnly(True)
        self.email_field.setStyleSheet('\n            QLineEdit {\n                background-color: #ecf0f1;\n                border: 1px solid #bdc3c7;\n                border-radius: 5px;\n                padding: 6px;\n                font-size: 12px;\n            }\n        ')
        basic_layout.addRow('Email:', self.email_field)
        self.creditos_field = QLineEdit('R$ 0,00')
        self.creditos_field.setReadOnly(True)
        self.creditos_field.setStyleSheet('\n            QLineEdit {\n                background-color: #27ae60;\n                border: none;\n                border-radius: 4px;\n                padding: 4px 8px;\n                font-size: 12px;\n                font-weight: bold;\n                color: white;\n            }\n        ')
        self.creditos_field.setToolTip('Cr├®ditos s├úo usados para comprar servi├ºos no sistema.\nPara adicionar cr├®ditos, entre em contato com o administrador.')
        basic_layout.addRow('Saldo de Cr├®ditos:', self.creditos_field)
        if not self.compact_mode:
            creditos_info = QLabel('Cr├®ditos s├úo gerenciados pelo administrador do sistema')
            creditos_info.setStyleSheet('\n                color: #7f8c8d; \n                font-size: 11px; \n                font-style: italic; \n                margin-left: 10px;\n                margin-bottom: 8px;\n            ')
            basic_layout.addRow('', creditos_info)
        self.nome_field = QLineEdit()
        self.nome_field.setPlaceholderText('Digite seu nome completo')
        self.nome_field.setStyleSheet(self.get_field_style())
        basic_layout.addRow('Nome:', self.nome_field)
        self.nivel_field = QLineEdit('NOVATO')
        self.nivel_field.setReadOnly(True)
        self.nivel_field.setStyleSheet('\n            QLineEdit {\n                background-color: #7f8c8d;\n                border: none;\n                border-radius: 4px;\n                padding: 4px 8px;\n                font-size: 12px;\n                font-weight: bold;\n                color: white;\n            }\n        ')
        self.nivel_field.setToolTip('Seu n├¡vel ├® determinado pela sua participa├º├úo e contribui├º├Áes.\nGerenciado pelo administrador do sistema.')
        basic_layout.addRow('N├¡vel:', self.nivel_field)
        self.data_nascimento_field = QDateEdit()
        self.data_nascimento_field.setDate(QDate(1990, 1, 1))
        self.data_nascimento_field.setCalendarPopup(True)
        self.data_nascimento_field.setStyleSheet(self.get_field_style())
        basic_layout.addRow('Data de Nascimento:', self.data_nascimento_field)
        form_layout.addWidget(basic_group)
        contact_group = QGroupBox('Informa├º├Áes de Contato')
        contact_group.setStyleSheet(self.get_group_style())
        contact_layout = QFormLayout(contact_group)
        contact_layout.setSpacing(8 if self.compact_mode else 10)
        self.telefone_field = QLineEdit()
        self.telefone_field.setPlaceholderText('(85) 99999-9999')
        self.telefone_field.setStyleSheet(self.get_field_style())
        contact_layout.addRow('Telefone:', self.telefone_field)
        self.localizacao_field = QLineEdit()
        self.localizacao_field.setPlaceholderText('Cidade, Estado, Pa├¡s')
        self.localizacao_field.setStyleSheet(self.get_field_style())
        contact_layout.addRow('Localiza├º├úo:', self.localizacao_field)
        self.website_field = QLineEdit()
        self.website_field.setPlaceholderText('https://seusite.com')
        self.website_field.setStyleSheet(self.get_field_style())
        contact_layout.addRow('Website:', self.website_field)
        form_layout.addWidget(contact_group)
        social_group = QGroupBox('Redes Sociais')
        social_group.setStyleSheet(self.get_group_style())
        social_layout = QFormLayout(social_group)
        social_layout.setSpacing(8 if self.compact_mode else 10)
        self.linkedin_field = QLineEdit()
        self.linkedin_field.setPlaceholderText('https://linkedin.com/in/seuperfil')
        self.linkedin_field.setStyleSheet(self.get_field_style())
        social_layout.addRow('LinkedIn:', self.linkedin_field)
        self.instagram_field = QLineEdit()
        self.instagram_field.setPlaceholderText('@seuinstagram')
        self.instagram_field.setStyleSheet(self.get_field_style())
        social_layout.addRow('Instagram:', self.instagram_field)
        self.github_field = QLineEdit()
        self.github_field.setPlaceholderText('https://github.com/seuusuario')
        self.github_field.setStyleSheet(self.get_field_style())
        social_layout.addRow('GitHub:', self.github_field)
        self.twitter_field = QLineEdit()
        self.twitter_field.setPlaceholderText('@seuX')
        self.twitter_field.setStyleSheet(self.get_field_style())
        social_layout.addRow('X (Twitter):', self.twitter_field)
        form_layout.addWidget(social_group)
        privacy_group = QGroupBox('Configura├º├Áes de Privacidade')
        privacy_group.setStyleSheet(self.get_group_style())
        privacy_layout = QFormLayout(privacy_group)
        privacy_layout.setSpacing(8 if self.compact_mode else 10)
        self.visibilidade_combo = QComboBox()
        self.visibilidade_combo.addItems(['publico', 'privado', 'amigos'])
        self.visibilidade_combo.setStyleSheet(self.get_field_style())
        privacy_layout.addRow('Visibilidade:', self.visibilidade_combo)
        self.notificacoes_email_check = QCheckBox('Receber notifica├º├Áes por email')
        self.notificacoes_email_check.setChecked(True)
        self.notificacoes_email_check.setStyleSheet(self.get_checkbox_style())
        privacy_layout.addRow('Email:', self.notificacoes_email_check)
        self.notificacoes_push_check = QCheckBox('Receber notifica├º├Áes push')
        self.notificacoes_push_check.setChecked(True)
        self.notificacoes_push_check.setStyleSheet(self.get_checkbox_style())
        privacy_layout.addRow('Push:', self.notificacoes_push_check)
        form_layout.addWidget(privacy_group)
        bio_group = QGroupBox('Sobre Voc├¬')
        bio_group.setStyleSheet(self.get_group_style())
        bio_layout = QVBoxLayout(bio_group)
        if not self.compact_mode:
            bio_label = QLabel('Conte sobre sua experi├¬ncia profissional, especialidades t├®cnicas, projetos, etc.')
            bio_label.setStyleSheet('color: #7f8c8d; font-size: 12px; margin-bottom: 5px;')
            bio_layout.addWidget(bio_label)
        self.bio_field = QTextEdit()
        bio_placeholder = 'Exemplo: T├®cnico em eletr├┤nica, especialista em smartphones...' if self.compact_mode else 'Exemplo:\n\nÔÇó T├®cnico em eletr├┤nica com 5 anos de experi├¬ncia\nÔÇó Especialista em reparo de smartphones Samsung e iPhone\nÔÇó Conhecimento avan├ºado em soldagem BGA\nÔÇó Experi├¬ncia com diagn├│stico de placas-m├úe\nÔÇó Forma├º├úo em Engenharia El├®trica\n\nCompartilhe suas habilidades e experi├¬ncias para ajudar outros t├®cnicos!'
        self.bio_field.setPlaceholderText(bio_placeholder)
        min_height = 100 if self.compact_mode else 150
        max_height = 130 if self.compact_mode else 200
        self.bio_field.setMinimumHeight(min_height)
        self.bio_field.setMaximumHeight(max_height)
        font_size = '12px' if self.compact_mode else '13px'
        padding = '6px' if self.compact_mode else '8px'
        self.bio_field.setStyleSheet(f'\n            QTextEdit {{\n                border: 2px solid #bdc3c7;\n                border-radius: 5px;\n                padding: {padding};\n                font-size: {font_size};\n                background-color: white;\n                font-family: Arial, sans-serif;\n            }}\n            QTextEdit:focus {{\n                border-color: #3498db;\n            }}\n        ')
        bio_layout.addWidget(self.bio_field)
        self.char_counter = QLabel('0 / 1000 caracteres')
        counter_size = '10px' if self.compact_mode else '11px'
        self.char_counter.setStyleSheet(f'color: #7f8c8d; font-size: {counter_size};')
        self.char_counter.setAlignment(Qt.AlignRight)
        self.bio_field.textChanged.connect(self.update_char_counter)
        bio_layout.addWidget(self.char_counter)
        form_layout.addWidget(bio_group)
        spacer_height = 10 if self.compact_mode else 20
        form_layout.addItem(QSpacerItem(20, spacer_height, QSizePolicy.Minimum, QSizePolicy.Expanding))
        scroll.setWidget(form_widget)
        layout.addWidget(scroll)
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        self.btn_cancelar = QPushButton('Cancelar')
        self.btn_cancelar.setStyleSheet('\n            QPushButton {\n                background-color: #424242;\n                color: white;\n                border: none;\n                padding: 6px 12px;\n                border-radius: 4px;\n                font-size: 12px;\n                font-weight: 600;\n            }\n            QPushButton:hover {\n                background-color: #616161;\n            }\n            QPushButton:pressed {\n                background-color: #212121;\n            }\n        ')
        self.btn_cancelar.clicked.connect(self.reject)
        buttons_layout.addWidget(self.btn_cancelar)
        buttons_layout.addStretch()
        self.btn_atualizar = QPushButton('Atualizar')
        self.btn_atualizar.setStyleSheet('\n            QPushButton {\n                background-color: #2196F3;\n                color: white;\n                border: none;\n                padding: 6px 12px;\n                border-radius: 4px;\n                font-size: 12px;\n                font-weight: 600;\n            }\n            QPushButton:hover {\n                background-color: #1976D2;\n            }\n            QPushButton:pressed {\n                background-color: #0D47A1;\n            }\n        ')
        self.btn_atualizar.setToolTip('Atualizar saldo de cr├®ditos')
        self.btn_atualizar.clicked.connect(self.atualizar_saldo)
        buttons_layout.addWidget(self.btn_atualizar)
        self.btn_salvar = QPushButton('Salvar Perfil')
        self.btn_salvar.setStyleSheet('\n            QPushButton {\n                background-color: #27ae60;\n                color: white;\n                border: none;\n                padding: 6px 12px;\n                border-radius: 4px;\n                font-size: 12px;\n                font-weight: 600;\n            }\n            QPushButton:hover {\n                background-color: #219a52;\n            }\n            QPushButton:pressed {\n                background-color: #1e8449;\n            }\n        ')
        self.btn_salvar.clicked.connect(self.salvar_perfil)
        buttons_layout.addWidget(self.btn_salvar)
        layout.addLayout(buttons_layout)
    def get_group_style(self):
        font_size = '13px' if self.compact_mode else '14px'
        margin_top = '8px' if self.compact_mode else '10px'
        padding_top = '8px' if self.compact_mode else '10px'
        return f'\n            QGroupBox {{\n                font-weight: bold;\n                font-size: {font_size};\n                color: #2c3e50;\n                border: 2px solid #bdc3c7;\n                border-radius: 8px;\n                margin-top: {margin_top};\n                padding-top: {padding_top};\n            }}\n            QGroupBox::title {{\n                subcontrol-origin: margin;\n                left: 10px;\n                padding: 0 5px 0 5px;\n            }}\n        '
    def get_field_style(self):
        padding = '6px' if self.compact_mode else '8px'
        font_size = '12px' if self.compact_mode else '13px'
        return f'\n            QLineEdit, QDateEdit, QComboBox {{\n                border: 2px solid #bdc3c7;\n                border-radius: 5px;\n                padding: {padding};\n                font-size: {font_size};\n                background-color: white;\n                color: #2c3e50;\n            }}\n            QLineEdit:focus, QDateEdit:focus, QComboBox:focus {{\n                border-color: #3498db;\n            }}\n            QComboBox::drop-down {{\n                border: none;\n                background-color: #3498db;\n                border-radius: 3px;\n                width: 20px;\n            }}\n            QComboBox::down-arrow {{\n                image: none;\n                border: 2px solid white;\n                border-top: none;\n                border-right: none;\n                width: 6px;\n                height: 6px;\n                margin: 2px;\n                transform: rotate(-45deg);\n            }}\n            QComboBox QAbstractItemView {{\n                background-color: white;\n                border: 2px solid #bdc3c7;\n                border-radius: 5px;\n                selection-background-color: #3498db;\n                selection-color: white;\n            }}\n        '
    def get_button_style(self, color):
        return f'\n            QPushButton {{\n                background-color: {color};\n                color: white;\n                border: none;\n                padding: 6px 12px;\n                border-radius: 4px;\n                font-size: 12px;\n                font-weight: 600;\n            }}\n            QPushButton:hover {{\n                background-color: {color}dd;\n            }}\n            QPushButton:pressed {{\n                background-color: {color}aa;\n            }}\n        '
    def get_checkbox_style(self):
        font_size = '12px' if self.compact_mode else '13px'
        return f'\n            QCheckBox {{\n                font-size: {font_size};\n                color: #2c3e50;\n                spacing: 8px;\n            }}\n            QCheckBox::indicator {{\n                width: 18px;\n                height: 18px;\n                border-radius: 3px;\n                border: 2px solid #bdc3c7;\n                background-color: white;\n            }}\n            QCheckBox::indicator:checked {{\n                background-color: #3498db;\n                border-color: #3498db;\n                image: none;\n            }}\n            QCheckBox::indicator:checked:after {{\n                content: "Ô£ô";\n                color: white;\n                font-weight: bold;\n                font-size: 12px;\n            }}\n            QCheckBox:hover {{\n                color: #3498db;\n            }}\n        '
    def update_char_counter(self):
        text = self.bio_field.toPlainText()
        char_count = len(text)
        self.char_counter.setText(f'{char_count} / 1000 caracteres')
        if char_count > 1000:
            cursor = self.bio_field.textCursor()
            cursor.deletePreviousChar()
    def _validar_imagem_segura(self, file_path):
        try:
            import os
            if os.path.getsize(file_path) > 10485760:
                return (False, 'Imagem muito grande. M├íximo 10MB permitido.')
            extensoes_permitidas = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
            _, ext = os.path.splitext(file_path.lower())
            if ext not in extensoes_permitidas:
                return (False, 'Formato de imagem n├úo permitido.')
            with open(file_path, 'rb') as f:
                header = f.read(16)
                valid_headers = [b'\x89PNG\r\n\x1a\n', b'\xff\xd8\xff', b'GIF87a', b'GIF89a', b'BM']
                if not any((header.startswith(h) for h in valid_headers)):
                    return (False, 'Arquivo n├úo ├® uma imagem v├ílida.')
        except Exception as e:
            logger.error(f'Erro na valida├º├úo de imagem: {str(e)}')
            return (False, 'Erro ao validar a imagem.')
        return (True, 'Imagem v├ílida')
    def escolher_foto(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, 'Escolher Foto de Perfil', '', 'Imagens (*.png *.jpg *.jpeg *.gif *.bmp);;Todos os arquivos (*)')
        if file_path:
            try:
                is_valid, message = self._validar_imagem_segura(file_path)
                if not is_valid:
                    self._mostrar_erro_seguro('Imagem Inv├ílida', message)
                    return
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    foto_size = 100 if self.compact_mode else 120
                    scaled_pixmap = pixmap.scaled(foto_size, foto_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    circular_pixmap = QPixmap(foto_size, foto_size)
                    circular_pixmap.fill(Qt.transparent)
                    from PyQt5.QtGui import QPainter, QPainterPath
                    painter = QPainter(circular_pixmap)
                    painter.setRenderHint(QPainter.Antialiasing)
                    path = QPainterPath()
                    path.addEllipse(0, 0, foto_size, foto_size)
                    painter.setClipPath(path)
                    x = (foto_size - scaled_pixmap.width()) // 2
                    y = (foto_size - scaled_pixmap.height()) // 2
                    painter.drawPixmap(x, y, scaled_pixmap)
                    painter.end()
                    self.foto_label.setPixmap(circular_pixmap)
                    with open(file_path, 'rb') as f:
                        self.foto_perfil_data = base64.b64encode(f.read()).decode('utf-8')
                    QMessageBox.information(self, 'Sucesso', 'Foto carregada com sucesso!')
                    return
                self._mostrar_erro_seguro('Erro na Imagem', 'N├úo foi poss├¡vel carregar a imagem selecionada.')
            except Exception as e:
                logger.error(f'Erro ao carregar foto: {str(e)}')
                self._mostrar_erro_seguro('Erro ao Carregar Foto', 'Erro ao processar a imagem selecionada.')
    def remover_foto(self):
        self.foto_label.setPixmap(QPixmap())
        self.foto_label.setText('Foto')
        self.foto_perfil_data = None
        QMessageBox.information(self, 'Sucesso', 'Foto removida com sucesso!')
    def _configurar_nivel_usuario(self, nivel):
        try:
            niveis_config = {0: {'nome': 'BANIDO', 'cor_start': '#e74c3c', 'cor_end': '#c0392b'}, 1: {'nome': 'NOVATO', 'cor_start': '#7f8c8d', 'cor_end': '#95a5a6'}, 2: {'nome': 'MEMBRO', 'cor_start': '#3498db', 'cor_end': '#2980b9'}, 3: {'nome': 'EXPERT', 'cor_start': '#9b59b6', 'cor_end': '#8e44ad'}, 4: {'nome': 'MODERADOR', 'cor_start': '#f39c12', 'cor_end': '#e67e22'}, 5: {'nome': 'ADMIN', 'cor_start': '#27ae60', 'cor_end': '#2ecc71'}}
            config = niveis_config.get(nivel, niveis_config[1])
            self.nivel_field.setText(config['nome'])
            estilo_nivel = f'\n                QLineEdit {{\n                    background-color: {config['cor_start']};\n                    border: none;\n                    border-radius: 4px;\n                    padding: 4px 8px;\n                    font-size: 12px;\n                    font-weight: bold;\n                    color: white;\n                }}\n            '
            self.nivel_field.setStyleSheet(estilo_nivel)
            logger.info(f'N├¡vel do usu├írio configurado: {config['nome']}')
            return
        except Exception as e:
            self.nivel_field.setText('NOVATO')
            logger.error(f'Erro ao configurar n├¡vel: {str(e)}')
    def atualizar_saldo(self):
        if not self.user_id:
            QMessageBox.information(self, 'Aviso', 'Salve o perfil primeiro para atualizar o saldo.')
            return
        try:
            progress = QProgressDialog('Atualizando saldo...', None, 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.setValue(20)
            conn = self.conectar_mysql()
            if not conn:
                QMessageBox.warning(self, 'Erro', 'N├úo foi poss├¡vel conectar ao banco de dados.')
                if 'progress' in locals():
                    progress.close()
                    return
                return
        except Exception as e:
            logger.error(f'Erro ao atualizar saldo: {str(e)}')
            self._mostrar_erro_seguro('Erro ao Atualizar Saldo', 'N├úo foi poss├¡vel atualizar o saldo no momento.\n\nTente novamente em alguns minutos.')
        try:
            cursor = conn.cursor()
            progress.setValue(50)
            cursor.execute('SELECT saldo_creditos FROM usuarios WHERE id_usuario = %s', (self.user_id,))
            resultado = cursor.fetchone()
            progress.setValue(80)
            if resultado:
                saldo_creditos = float(resultado.get('saldo_creditos', 0.0))
                self.creditos_field.setText(f'R$ {saldo_creditos:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))
                original_style = self.creditos_field.styleSheet()
                success_style = original_style.replace('#27ae60', '#2ecc71').replace('#2ecc71', '#27ae60')
                self.creditos_field.setStyleSheet(success_style)
                QTimer.singleShot(1000, (lambda: self.creditos_field.setStyleSheet(original_style)))
                logger.info(f'Saldo atualizado para R$ {saldo_creditos:,.2f}')
                QMessageBox.information(self, 'Sucesso', f'Saldo atualizado.\n\nSaldo atual: R$ {saldo_creditos:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))
            else:
                QMessageBox.information(self, 'Aviso', 'Usu├írio n├úo encontrado no sistema.')
            progress.setValue(100)
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f'Erro ao atualizar saldo: {str(e)}')
            self._mostrar_erro_seguro('Erro ao Atualizar Saldo', 'N├úo foi poss├¡vel atualizar o saldo no momento.\n\nTente novamente em alguns minutos.')
        if 'progress' in locals():
            progress.close()
    def conectar_mysql(self):
        try:
            return pymysql.connect(**MYSQL_CONFIG, **{'cursorclass': pymysql.cursors.DictCursor, 'autocommit': False})
        except Exception as e:
            logger.error(f'Erro ao conectar ao MySQL: {str(e)}')
    def carregar_dados(self):
        progress = QProgressDialog('Carregando dados do perfil...', None, 0, 100, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setValue(10)
        try:
            conn = self.conectar_mysql()
            if not conn:
                QMessageBox.warning(self, 'Erro', 'N├úo foi poss├¡vel conectar ao banco de dados.\n\nVerifique sua conex├úo com a internet.')
                progress.close()
                return
            cursor = conn.cursor()
            progress.setValue(30)
            cursor.execute('SELECT id_usuario, saldo_creditos, nivel_usuario FROM usuarios WHERE email = %s', (self.user_email,))
            usuario = cursor.fetchone()
            progress.setValue(50)
            if usuario:
                self.user_id = usuario['id_usuario']
                saldo_creditos = float(usuario.get('saldo_creditos', 0.0))
                nivel_usuario = int(usuario.get('nivel_usuario', 1))
                self.creditos_field.setText(f'R$ {saldo_creditos:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))
                self._configurar_nivel_usuario(nivel_usuario)
                cursor.execute('\n                    SELECT nome, telefone, localizacao, website, linkedin, \n                           instagram, github, twitter, bio, data_nascimento,\n                           visibilidade, notificacoes_email, notificacoes_push,\n                           foto_perfil\n                    FROM perfil \n                    WHERE id_usuario = %s\n                ', (self.user_id,))
                perfil = cursor.fetchone()
                progress.setValue(80)
                if perfil:
                    self.perfil_existe = True
                    self.preencher_campos(perfil)
                else:
                    logger.info('Perfil n├úo existe - ser├í criado ao salvar')
            else:
                logger.info('Usu├írio n├úo existe - ser├í criado ao salvar')
            progress.setValue(100)
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f'Erro ao carregar dados: {str(e)}')
            self._mostrar_erro_seguro('Erro ao Carregar Dados', 'N├úo foi poss├¡vel carregar alguns dados do perfil.\n\nVoc├¬ pode continuar e tentar salvar novamente.')
        finally:
            progress.close()
    def preencher_campos(self, perfil):
        if perfil['nome']:
            self.nome_field.setText(perfil['nome'])
        if perfil['telefone']:
            self.telefone_field.setText(perfil['telefone'])
        if perfil['localizacao']:
            self.localizacao_field.setText(perfil['localizacao'])
        if perfil['website']:
            self.website_field.setText(perfil['website'])
        if perfil['linkedin']:
            self.linkedin_field.setText(perfil['linkedin'])
        if perfil['instagram']:
            self.instagram_field.setText(perfil['instagram'])
        if perfil['github']:
            self.github_field.setText(perfil['github'])
        if perfil['twitter']:
            self.twitter_field.setText(perfil['twitter'])
        if perfil['bio']:
            self.bio_field.setPlainText(perfil['bio'])
        if perfil['data_nascimento']:
            self.data_nascimento_field.setDate(perfil['data_nascimento'])
        if perfil['visibilidade']:
            index = self.visibilidade_combo.findText(perfil['visibilidade'])
            if index >= 0:
                self.visibilidade_combo.setCurrentIndex(index)
        self.notificacoes_email_check.setChecked(bool(perfil['notificacoes_email']))
        self.notificacoes_push_check.setChecked(bool(perfil['notificacoes_push']))
        if perfil['foto_perfil']:
            try:
                foto_data = base64.b64decode(perfil['foto_perfil'])
                pixmap = QPixmap()
                pixmap.loadFromData(foto_data)
                if not pixmap.isNull():
                    foto_size = 100 if self.compact_mode else 120
                    scaled_pixmap = pixmap.scaled(foto_size, foto_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.foto_label.setPixmap(scaled_pixmap)
                    self.foto_perfil_data = perfil['foto_perfil']
                    return
            except Exception as e:
                logger.error(f'Erro ao carregar foto: {str(e)}')
    def _sanitizar_entrada_usuario(self, texto):
        try:
            if not texto:
                return
            import re
            texto_limpo = re.sub('[<>"\\\'\\\\;\\x00-\\x1f\\x7f-\\x9f]', '', str(texto))
            texto_limpo = re.sub('<[^>]*>', '', texto_limpo)
            texto_limpo = re.sub('(javascript:|data:|vbscript:|onload|onerror)', '', texto_limpo, flags=re.IGNORECASE)
            texto_limpo = texto_limpo[:500] if len(texto_limpo) > 500 else texto_limpo
        except Exception as e:
            logger.error(f'Erro na sanitiza├º├úo: {str(e)}')
        return texto_limpo.strip() or None
    def _validar_url_segura(self, url):
        try:
            if not url or not url.strip():
                return
            import re
            url = url.strip()
            if not re.match('^https?://', url, re.IGNORECASE):
                url = 'https://' + url
            url_pattern = '^https?://[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*(/.*)?$'
            if not re.match(url_pattern, url):
                return
            url = re.sub('[<>"\\\'\\\\;\\x00-\\x1f\\x7f-\\x9f]', '', url)
            if len(url) > 255:
                return
            return url
        except Exception as e:
            logger.error(f'Erro na valida├º├úo de URL: {str(e)}')
    def salvar_perfil(self):
        nome_bruto = self.nome_field.text().strip()
        nome = self._sanitizar_entrada_usuario(nome_bruto)
        if not nome:
            QMessageBox.warning(self, 'Aviso', 'O campo Nome ├® obrigat├│rio e deve conter apenas caracteres v├ílidos!')
            self.nome_field.setFocus()
            return
        progress = QProgressDialog('Salvando perfil...', None, 0, 100, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setValue(10)
        try:
            conn = self.conectar_mysql()
            if not conn:
                QMessageBox.critical(self, 'Erro', 'N├úo foi poss├¡vel conectar ao banco de dados.')
                progress.close()
                return
            cursor = conn.cursor()
            progress.setValue(30)
            if not self.user_id:
                cursor.execute('SELECT id_usuario FROM usuarios WHERE email = %s', (self.user_email,))
                usuario = cursor.fetchone()
                if not usuario:
                    import uuid
                    import time
                    licenca_unica = f'UNION-{int(time.time())}-{str(uuid.uuid4())[:8].upper()}'
                    cursor.execute("\n                        INSERT INTO usuarios (email, licenca, nome_usuario, data_registro, status)\n                        VALUES (%s, %s, %s, NOW(), 'ativo')\n                    ", (self.user_email, licenca_unica, nome))
                    self.user_id = cursor.lastrowid
                    logger.info(f'Usu├írio criado com ID: {self.user_id}, Licen├ºa: {licenca_unica}')
                else:
                    self.user_id = usuario['id_usuario']
            progress.setValue(60)
            dados_perfil = {'nome': nome, 'telefone': self._sanitizar_entrada_usuario(self.telefone_field.text()), 'localizacao': self._sanitizar_entrada_usuario(self.localizacao_field.text()), 'website': self._validar_url_segura(self.website_field.text()), 'linkedin': self._validar_url_segura(self.linkedin_field.text()), 'instagram': self._sanitizar_entrada_usuario(self.instagram_field.text()), 'github': self._validar_url_segura(self.github_field.text()), 'twitter': self._sanitizar_entrada_usuario(self.twitter_field.text()), 'bio': self._sanitizar_entrada_usuario(self.bio_field.toPlainText()), 'data_nascimento': self.data_nascimento_field.date().toPyDate(), 'visibilidade': self._sanitizar_entrada_usuario(self.visibilidade_combo.currentText()) or 'publico', 'notificacoes_email': bool(self.notificacoes_email_check.isChecked()), 'notificacoes_push': bool(self.notificacoes_push_check.isChecked()), 'foto_perfil': self.foto_perfil_data}
            if self.perfil_existe:
                cursor.execute('\n                    UPDATE perfil SET \n                        nome = %s, telefone = %s, localizacao = %s, website = %s,\n                        linkedin = %s, instagram = %s, github = %s, twitter = %s, bio = %s,\n                        data_nascimento = %s, visibilidade = %s, notificacoes_email = %s,\n                        notificacoes_push = %s, foto_perfil = %s, updated_at = NOW()\n                    WHERE id_usuario = %s\n                ', (*dados_perfil.values(), self.user_id))
                logger.info('Perfil atualizado')
            else:
                cursor.execute('\n                    INSERT INTO perfil (id_usuario, nome, telefone, localizacao, website,\n                                      linkedin, instagram, github, twitter, bio, data_nascimento,\n                                      visibilidade, notificacoes_email, notificacoes_push,\n                                      foto_perfil, created_at, updated_at)\n                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())\n                ', (self.user_id, *dados_perfil.values()))
                self.perfil_existe = True
                logger.info('Perfil criado')
            progress.setValue(90)
            conn.commit()
            progress.setValue(100)
            cursor.close()
            conn.close()
            QMessageBox.information(self, 'Sucesso', 'Perfil salvo com sucesso.\n\nSuas informa├º├Áes foram atualizadas no sistema.\nAgora voc├¬ est├í pronto para interagir com outros usu├írios!')
            self.accept()
        except Exception as e:
            logger.error(f'Erro ao salvar perfil: {str(e)}')
            self._mostrar_erro_seguro('Erro ao Salvar Perfil', 'N├úo foi poss├¡vel salvar o perfil no momento.\n\nVerifique sua conex├úo com a internet e tente novamente.')
        finally:
            progress.close()
    def _mostrar_erro_seguro(self, titulo, mensagem_usuario):
        try:
            QMessageBox.critical(self, titulo, mensagem_usuario)
            return
        except Exception:
            return
