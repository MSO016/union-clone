'''
TECH UNION SOLUTIONS - JANELA DE VISUALIZA├ç├âO DE PERFIL
=======================================================
Janela para visualizar o perfil do usu├írio em modo somente leitura.
Exibe todas as informa├º├Áes do perfil de forma organizada e elegante.
Autor: Sistema UNION V1.3
Data: Janeiro 2025
'''
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton, QMessageBox, QProgressDialog, QGroupBox, QScrollArea, QWidget, QFrame, QSpacerItem, QSizePolicy, QTextEdit, QDesktopWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import (QFont, QPixmap, QIcon)
import pymysql
import logging
from datetime import datetime
import base64
from app.utils._app_cfg import db_config
MYSQL_CONFIG = db_config(ssl={'ca': None}, ssl_verify_cert=False)
logger = logging.getLogger(__name__)
class VisualizarPerfilWindow(QDialog):
    def __init__(self, user_email, parent=None):
        super().__init__(parent)
        self.user_email = user_email
        self.user_id = None
        self.perfil_data = None
        self.setWindowTitle('Meu Perfil - TECH UNION SOLUTIONS')
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self._setup_window_size()
        self.setup_ui()
        self.carregar_dados()
    def _setup_window_size(self):
        '''Configura tamanho da janela baseado na ├írea dispon├¡vel da tela (desconta taskbar)'''
        desktop = QDesktopWidget()
        available = desktop.availableGeometry()
        avail_w = available.width()
        avail_h = available.height()
        self.compact_mode = avail_h <= 900
        window_w = min(650, avail_w - 100)
        window_h = min(700, avail_h - 80)
        self.setMinimumSize(500, 400)
        self.setMaximumSize(avail_w - 40, avail_h - 40)
        self.resize(window_w, window_h)
        if self.parent():
            pg = self.parent().geometry()
            x = pg.x() + (pg.width() - window_w) // 2
            y = pg.y() + (pg.height() - window_h) // 2
            self.move(max(0, x), max(0, y))
            return
        x = (avail_w - window_w) // 2 + available.x()
        y = (avail_h - window_h) // 2 + available.y()
        self.move(max(0, x), max(0, y))
    def setup_ui(self):
        '''Configura a interface da janela'''
        layout = QVBoxLayout(self)
        sp = 10 if self.compact_mode else 15
        mg = 12 if self.compact_mode else 20
        layout.setSpacing(sp)
        layout.setContentsMargins(mg, mg, mg, mg)
        header_frame = QFrame()
        h_pad = '10px' if self.compact_mode else '15px'
        header_frame.setStyleSheet(f'\n            QFrame {{\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,\n                    stop:0 #1565C0, stop:1 #1976D2);\n                border-radius: 8px;\n                padding: {h_pad};\n                margin-bottom: {'5px' if self.compact_mode else '10px'};\n            }}\n        ')
        header_layout = QVBoxLayout(header_frame)
        header_layout.setSpacing(4)
        t_size = '20px' if self.compact_mode else '24px'
        title = QLabel('MEU PERFIL')
        title.setStyleSheet(f'\n            color: white;\n            font-size: {t_size};\n            font-weight: bold;\n            text-align: center;\n        ')
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)
        if not self.compact_mode:
            subtitle = QLabel('Visualiza├º├úo das suas informa├º├Áes pessoais e profissionais')
            subtitle.setStyleSheet('\n                color: #ecf0f1;\n                font-size: 14px;\n                text-align: center;\n            ')
            subtitle.setAlignment(Qt.AlignCenter)
            header_layout.addWidget(subtitle)
        layout.addWidget(header_frame)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('\n            QScrollArea {\n                border: none;\n                background-color: transparent;\n            }\n        ')
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        foto_group = QGroupBox('Foto de Perfil')
        foto_group.setStyleSheet(self.get_group_style())
        foto_layout = QHBoxLayout(foto_group)
        foto_layout.setAlignment(Qt.AlignCenter)
        foto_size = 100 if self.compact_mode else 150
        self.foto_label = QLabel()
        self.foto_label.setFixedSize(foto_size, foto_size)
        self.foto_label.setStyleSheet(f'\n            QLabel {{\n                border: 3px solid #bdc3c7;\n                border-radius: {foto_size // 2}px;\n                background-color: #ecf0f1;\n                color: #7f8c8d;\n                font-size: 16px;\n                font-weight: bold;\n                text-align: center;\n            }}\n        ')
        self.foto_label.setText('Foto')
        self.foto_label.setAlignment(Qt.AlignCenter)
        foto_layout.addWidget(self.foto_label)
        content_layout.addWidget(foto_group)
        basic_group = QGroupBox('Informa├º├Áes B├ísicas')
        basic_group.setStyleSheet(self.get_group_style())
        basic_layout = QFormLayout(basic_group)
        basic_layout.setSpacing(8 if self.compact_mode else 15)
        self.email_label = QLabel(self.user_email)
        self.email_label.setStyleSheet(self.get_info_style())
        basic_layout.addRow('Email:', self.email_label)
        self.creditos_label = QLabel('R$ 0,00')
        self.creditos_label.setStyleSheet('\n            QLabel {\n                background-color: #27ae60;\n                border: none;\n                border-radius: 4px;\n                padding: 4px 10px;\n                font-size: 12px;\n                font-weight: bold;\n                color: white;\n            }\n        ')
        self.creditos_label.setAlignment(Qt.AlignLeft)
        basic_layout.addRow('Saldo de Cr├®ditos:', self.creditos_label)
        self.nome_label = QLabel('N├úo informado')
        self.nome_label.setStyleSheet(self.get_info_style())
        basic_layout.addRow('Nome:', self.nome_label)
        self.nivel_label = QLabel('NOVATO')
        self.nivel_label.setStyleSheet('\n            QLabel {\n                background-color: #7f8c8d;\n                border: none;\n                border-radius: 4px;\n                padding: 4px 10px;\n                font-size: 12px;\n                font-weight: bold;\n                color: white;\n            }\n        ')
        self.nivel_label.setAlignment(Qt.AlignLeft)
        basic_layout.addRow('N├¡vel:', self.nivel_label)
        self.data_nascimento_label = QLabel('N├úo informado')
        self.data_nascimento_label.setStyleSheet(self.get_info_style())
        basic_layout.addRow('Data de Nascimento:', self.data_nascimento_label)
        content_layout.addWidget(basic_group)
        contact_group = QGroupBox('Informa├º├Áes de Contato')
        contact_group.setStyleSheet(self.get_group_style())
        contact_layout = QFormLayout(contact_group)
        contact_layout.setSpacing(8 if self.compact_mode else 15)
        self.telefone_label = QLabel('N├úo informado')
        self.telefone_label.setStyleSheet(self.get_info_style())
        contact_layout.addRow('Telefone:', self.telefone_label)
        self.localizacao_label = QLabel('N├úo informado')
        self.localizacao_label.setStyleSheet(self.get_info_style())
        contact_layout.addRow('Localiza├º├úo:', self.localizacao_label)
        self.website_label = QLabel('N├úo informado')
        self.website_label.setStyleSheet(self.get_info_style())
        contact_layout.addRow('Website:', self.website_label)
        content_layout.addWidget(contact_group)
        social_group = QGroupBox('Redes Sociais')
        social_group.setStyleSheet(self.get_group_style())
        social_layout = QFormLayout(social_group)
        social_layout.setSpacing(8 if self.compact_mode else 15)
        self.linkedin_label = QLabel('N├úo informado')
        self.linkedin_label.setStyleSheet(self.get_info_style())
        social_layout.addRow('LinkedIn:', self.linkedin_label)
        self.instagram_label = QLabel('N├úo informado')
        self.instagram_label.setStyleSheet(self.get_info_style())
        social_layout.addRow('Instagram:', self.instagram_label)
        self.github_label = QLabel('N├úo informado')
        self.github_label.setStyleSheet(self.get_info_style())
        social_layout.addRow('GitHub:', self.github_label)
        self.twitter_label = QLabel('N├úo informado')
        self.twitter_label.setStyleSheet(self.get_info_style())
        social_layout.addRow('X (Twitter):', self.twitter_label)
        content_layout.addWidget(social_group)
        privacy_group = QGroupBox('Configura├º├Áes de Privacidade')
        privacy_group.setStyleSheet(self.get_group_style())
        privacy_layout = QFormLayout(privacy_group)
        privacy_layout.setSpacing(8 if self.compact_mode else 15)
        self.visibilidade_label = QLabel('P├║blico')
        self.visibilidade_label.setStyleSheet(self.get_info_style())
        privacy_layout.addRow('Visibilidade:', self.visibilidade_label)
        self.notificacoes_email_label = QLabel('Ativado')
        self.notificacoes_email_label.setStyleSheet(self.get_info_style())
        privacy_layout.addRow('Notifica├º├Áes Email:', self.notificacoes_email_label)
        self.notificacoes_push_label = QLabel('Ativado')
        self.notificacoes_push_label.setStyleSheet(self.get_info_style())
        privacy_layout.addRow('Notifica├º├Áes Push:', self.notificacoes_push_label)
        content_layout.addWidget(privacy_group)
        bio_group = QGroupBox('Sobre Voc├¬')
        bio_group.setStyleSheet(self.get_group_style())
        bio_layout = QVBoxLayout(bio_group)
        self.bio_text = QTextEdit()
        self.bio_text.setPlainText('Nenhuma informa├º├úo adicionada ainda.')
        self.bio_text.setReadOnly(True)
        self.bio_text.setMaximumHeight(100 if self.compact_mode else 150)
        self.bio_text.setStyleSheet('\n            QTextEdit {\n                border: 2px solid #bdc3c7;\n                border-radius: 5px;\n                padding: 10px;\n                font-size: 13px;\n                background-color: #f8f9fa;\n                color: #2c3e50;\n                font-family: Arial, sans-serif;\n            }\n        ')
        bio_layout.addWidget(self.bio_text)
        content_layout.addWidget(bio_group)
        content_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        self.btn_editar = QPushButton('Editar Perfil')
        self.btn_editar.setStyleSheet('\n            QPushButton {\n                background-color: #2196F3;\n                color: white;\n                border: none;\n                padding: 6px 12px;\n                border-radius: 4px;\n                font-size: 12px;\n                font-weight: 600;\n            }\n            QPushButton:hover {\n                background-color: #1976D2;\n            }\n            QPushButton:pressed {\n                background-color: #0D47A1;\n            }\n        ')
        self.btn_editar.clicked.connect(self.editar_perfil)
        buttons_layout.addWidget(self.btn_editar)
        self.btn_atualizar_saldo = QPushButton('Atualizar Saldo')
        self.btn_atualizar_saldo.setStyleSheet('\n            QPushButton {\n                background-color: #27ae60;\n                color: white;\n                border: none;\n                padding: 6px 12px;\n                border-radius: 4px;\n                font-size: 12px;\n                font-weight: 600;\n            }\n            QPushButton:hover {\n                background-color: #219a52;\n            }\n            QPushButton:pressed {\n                background-color: #1e8449;\n            }\n        ')
        self.btn_atualizar_saldo.clicked.connect(self.atualizar_saldo)
        buttons_layout.addWidget(self.btn_atualizar_saldo)
        buttons_layout.addStretch()
        self.btn_fechar = QPushButton('Fechar')
        self.btn_fechar.setStyleSheet('\n            QPushButton {\n                background-color: #424242;\n                color: white;\n                border: none;\n                padding: 6px 12px;\n                border-radius: 4px;\n                font-size: 12px;\n                font-weight: 600;\n            }\n            QPushButton:hover {\n                background-color: #616161;\n            }\n            QPushButton:pressed {\n                background-color: #212121;\n            }\n        ')
        self.btn_fechar.clicked.connect(self.accept)
        buttons_layout.addWidget(self.btn_fechar)
        layout.addLayout(buttons_layout)
    def get_group_style(self):
        '''Retorna o estilo padr├úo para grupos'''
        fs = '13px' if self.compact_mode else '14px'
        mt = '6px' if self.compact_mode else '10px'
        pt = '6px' if self.compact_mode else '10px'
        return f'\n            QGroupBox {{\n                font-weight: bold;\n                font-size: {fs};\n                color: #2c3e50;\n                border: 2px solid #bdc3c7;\n                border-radius: 8px;\n                margin-top: {mt};\n                padding-top: {pt};\n            }}\n            QGroupBox::title {{\n                subcontrol-origin: margin;\n                left: 10px;\n                padding: 0 5px 0 5px;\n            }}\n        '
    def get_info_style(self):
        '''Retorna o estilo para labels de informa├º├úo'''
        pad = '5px' if self.compact_mode else '8px'
        fs = '12px' if self.compact_mode else '13px'
        return f'\n            QLabel {{\n                background-color: #f8f9fa;\n                border: 1px solid #dee2e6;\n                border-radius: 4px;\n                padding: {pad};\n                font-size: {fs};\n                color: #495057;\n                font-weight: normal;\n            }}\n        '
    def conectar_mysql(self):
        '''Conecta ao banco MySQL'''
        try:
            return pymysql.connect(**MYSQL_CONFIG, **{'cursorclass': pymysql.cursors.DictCursor, 'autocommit': False})
        except Exception as e:
            logger.error(f'Erro ao conectar ao MySQL: {str(e)}')
    def carregar_dados(self):
        '''Carrega os dados do usu├írio do banco MySQL'''
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
                self.creditos_label.setText(f'R$ {saldo_creditos:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))
                self._configurar_nivel_usuario(nivel_usuario)
                cursor.execute('\n                    SELECT nome, telefone, localizacao, website, linkedin, \n                           instagram, github, twitter, bio, data_nascimento,\n                           visibilidade, notificacoes_email, notificacoes_push,\n                           foto_perfil\n                    FROM perfil \n                    WHERE id_usuario = %s\n                ', (self.user_id,))
                perfil = cursor.fetchone()
                progress.setValue(80)
                if perfil:
                    self.perfil_data = perfil
                    self.preencher_dados(perfil)
                else:
                    self.mostrar_perfil_vazio()
            else:
                self.mostrar_perfil_vazio()
            progress.setValue(100)
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f'Erro ao carregar dados: {str(e)}')
            self._mostrar_erro_seguro('Erro ao Carregar Perfil', 'N├úo foi poss├¡vel carregar os dados do perfil.\n\nVerifique sua conex├úo com a internet.')
            self.mostrar_perfil_vazio()
        finally:
            progress.close()
    def _mostrar_erro_seguro(self, titulo, mensagem_usuario):
        '''Mostra erro seguro sem expor detalhes t├®cnicos (fun├º├úo nova - baseada em relat├│rio)'''
        try:
            QMessageBox.warning(self, titulo, mensagem_usuario)
            return
        except Exception:
            return
    def preencher_dados(self, perfil):
        '''Preenche os campos com os dados do perfil'''
        if perfil['nome']:
            self.nome_label.setText(perfil['nome'])
        if perfil['data_nascimento']:
            data_formatada = perfil['data_nascimento'].strftime('%d/%m/%Y')
            self.data_nascimento_label.setText(data_formatada)
        if perfil['telefone']:
            self.telefone_label.setText(perfil['telefone'])
        if perfil['localizacao']:
            self.localizacao_label.setText(perfil['localizacao'])
        if perfil['website']:
            self.website_label.setText(perfil['website'])
        if perfil['linkedin']:
            self.linkedin_label.setText(perfil['linkedin'])
        if perfil['instagram']:
            self.instagram_label.setText(perfil['instagram'])
        if perfil['github']:
            self.github_label.setText(perfil['github'])
        if perfil['twitter']:
            self.twitter_label.setText(perfil['twitter'])
        if perfil['bio']:
            self.bio_text.setPlainText(perfil['bio'])
        if perfil['visibilidade']:
            visibilidade_map = {'publico': 'P├║blico', 'privado': 'Privado', 'amigos': 'Apenas Amigos'}
            self.visibilidade_label.setText(visibilidade_map.get(perfil['visibilidade'], 'P├║blico'))
        self.notificacoes_email_label.setText('Ativado' if perfil['notificacoes_email'] else 'Desativado')
        self.notificacoes_push_label.setText('Ativado' if perfil['notificacoes_push'] else 'Desativado')
        if perfil['foto_perfil']:
            try:
                foto_data = base64.b64decode(perfil['foto_perfil'])
                pixmap = QPixmap()
                pixmap.loadFromData(foto_data)
                if not pixmap.isNull():
                    foto_sz = 100 if self.compact_mode else 150
                    circular_pixmap = QPixmap(foto_sz, foto_sz)
                    circular_pixmap.fill(Qt.transparent)
                    from PyQt5.QtGui import QPainter, QPainterPath
                    painter = QPainter(circular_pixmap)
                    painter.setRenderHint(QPainter.Antialiasing)
                    path = QPainterPath()
                    path.addEllipse(0, 0, foto_sz, foto_sz)
                    painter.setClipPath(path)
                    scaled_pixmap = pixmap.scaled(foto_sz, foto_sz, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    x = (foto_sz - scaled_pixmap.width()) // 2
                    y = (foto_sz - scaled_pixmap.height()) // 2
                    painter.drawPixmap(x, y, scaled_pixmap)
                    painter.end()
                    self.foto_label.setPixmap(circular_pixmap)
                    return
            except Exception as e:
                logger.error(f'Erro ao carregar foto: {str(e)}')
    def mostrar_perfil_vazio(self):
        '''Mostra mensagem quando n├úo h├í dados de perfil'''
        self.bio_text.setPlainText("Seu perfil ainda n├úo foi criado.\n\nClique em 'Editar Perfil' para adicionar suas informa├º├Áes e come├ºar a interagir com outros usu├írios do sistema UNION!")
        self.btn_editar.setStyleSheet('\n            QPushButton {\n                background-color: #c0392b;\n                color: white;\n                border: none;\n                padding: 6px 12px;\n                border-radius: 4px;\n                font-size: 12px;\n                font-weight: 600;\n            }\n            QPushButton:hover {\n                background-color: #e74c3c;\n            }\n            QPushButton:pressed {\n                background-color: #a93226;\n            }\n        ')
    def atualizar_saldo(self):
        '''Atualiza o saldo de cr├®ditos do usu├írio'''
        if not self.user_id:
            QMessageBox.information(self, 'Aviso', 'N├úo foi poss├¡vel identificar o usu├írio.')
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
                self.creditos_label.setText(f'R$ {saldo_creditos:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))
                from PyQt5.QtCore import QTimer
                original_style = self.creditos_label.styleSheet()
                success_style = original_style.replace('#27ae60', '#2ecc71').replace('#2980b9', '#27ae60')
                self.creditos_label.setStyleSheet(success_style)
                QTimer.singleShot(1000, (lambda: self.creditos_label.setStyleSheet(original_style)))
                logger.info(f'Saldo atualizado para R$ {saldo_creditos:,.2f}')
                QMessageBox.information(self, 'Sucesso', f'Saldo atualizado.\n\nSaldo atual: R$ {saldo_creditos:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))
            try:
                parent = self.parent()
                if parent is not None and hasattr(parent, 'atualizar_header_saldo'):
                    parent.atualizar_header_saldo()
            except Exception as e_hdr:
                logger.error(f'Falha ao atualizar saldo no header: {type(e_hdr).__name__}')
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
    def _configurar_nivel_usuario(self, nivel):
        '''Configura a exibi├º├úo do n├¡vel do usu├írio (fun├º├úo nova - segura)'''
        try:
            niveis_config = {0: {'nome': 'BANIDO', 'cor_start': '#e74c3c', 'cor_end': '#c0392b'}, 1: {'nome': 'NOVATO', 'cor_start': '#7f8c8d', 'cor_end': '#95a5a6'}, 2: {'nome': 'MEMBRO', 'cor_start': '#3498db', 'cor_end': '#2980b9'}, 3: {'nome': 'EXPERT', 'cor_start': '#9b59b6', 'cor_end': '#8e44ad'}, 4: {'nome': 'MODERADOR', 'cor_start': '#f39c12', 'cor_end': '#e67e22'}, 5: {'nome': 'ADMIN', 'cor_start': '#27ae60', 'cor_end': '#2ecc71'}}
            config = niveis_config.get(nivel, niveis_config[1])
            self.nivel_label.setText(config['nome'])
            estilo_nivel = f'\n                QLabel {{\n                    background-color: {config['cor_start']};\n                    border: none;\n                    border-radius: 4px;\n                    padding: 4px 10px;\n                    font-size: 12px;\n                    font-weight: bold;\n                    color: white;\n                }}\n            '
            self.nivel_label.setStyleSheet(estilo_nivel)
            logger.info(f'N├¡vel do usu├írio configurado: {config['nome']}')
            return
        except Exception as e:
            self.nivel_label.setText('NOVATO')
            logger.error(f'Erro ao configurar n├¡vel: {str(e)}')
    def editar_perfil(self):
        '''Abre a janela de edi├º├úo de perfil'''
        try:
            from app.views.perfil_window import PerfilWindow
            self.accept()
            perfil_window = PerfilWindow(self.user_email, self.parent())
            perfil_window.exec_()
            return
        except Exception as e:
            logger.error('Erro ao abrir editor de perfil: %s', type(e).__name__)
            QMessageBox.warning(self, 'Erro', 'N├úo foi poss├¡vel abrir o editor de perfil.\n\nTente novamente. Se o problema continuar, use o menu Usuario > Editar Meu Perfil.')
