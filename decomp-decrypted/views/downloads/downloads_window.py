import webbrowser
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QFrame, QScrollArea, QLineEdit, QMessageBox, QProgressBar, QApplication, QSizePolicy, QDialog, QTextEdit)
from PyQt5.QtCore import (Qt, QTimer, QThread, pyqtSignal, QSize)
from PyQt5.QtGui import (QFont, QPixmap, QIcon, QCursor, QPainter, QColor)
from app.utils.path_manager import PathManager
from app.utils.arquivos_manager import ArquivosManager
from app.database.downloads_cache import DownloadsCache
import logging
import re
class DownloadsWindow(QMainWindow):
    def __init__(self, email_login: str, parent=None):
        super().__init__(parent)
        self.email_login = email_login
        self.parent_window = parent
        self.logger = logging.getLogger(__name__)
        self.arquivos_manager = ArquivosManager()
        self.cache = DownloadsCache()
        self.marcas_disponiveis = []
        self.arquivos_recentes = []
        self.arquivos_populares = []
        if not self._verificar_acesso_usuario():
            self.logger.error(f'Acesso negado ao m├│dulo de downloads para: {self.email_login}')
            self._setup_ui_acesso_negado()
            return
        self._setup_ui()
        self._aplicar_estilos()
        self._carregar_dados_iniciais()
    def _verificar_acesso_usuario(self):
        try:
            if not self.email_login or not self.email_login.strip():
                self.logger.warning('Tentativa de acesso sem email v├ílido')
                return False
            if not self.arquivos_manager.verificar_dados_usuario(self.email_login):
                self.logger.warning(f'Usu├írio n├úo encontrado no sistema: {self.email_login}')
                return False
            if not re.match('^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$', self.email_login):
                self.logger.warning(f'Formato de email inv├ílido: {self.email_login}')
                return False
            self.logger.info(f'Acesso autorizado ├á ├írea de downloads: {self.email_login}')
            return True
        except Exception as e:
            self.logger.error(f'Erro ao verificar acesso do usu├írio {self.email_login}: {str(e)}')
            return False
    def _setup_ui(self):
        self.setWindowTitle('TECH UNION SOLUTIONS ARQUIVOS')
        self.setMinimumSize(900, 650)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        self._criar_header(main_layout)
        self._criar_area_conteudo(main_layout)
    def _criar_header(self, parent_layout):
        header_widget = QFrame()
        header_widget.setObjectName('headerFrame')
        header_widget.setMinimumHeight(60)
        header_widget.setMaximumHeight(85)
        header_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(15, 10, 15, 10)
        header_layout.setSpacing(15)
        btn_voltar = QPushButton('ÔåÉ Voltar')
        btn_voltar.setObjectName('btnVoltar')
        btn_voltar.setMinimumSize(80, 40)
        btn_voltar.setMaximumSize(120, 60)
        btn_voltar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        btn_voltar.setCursor(Qt.PointingHandCursor)
        btn_voltar.clicked.connect(self._voltar_tela_principal)
        header_layout.addWidget(btn_voltar)
        titulo_label = QLabel('TECH UNION SOLUTIONS ARQUIVOS')
        titulo_label.setObjectName('tituloHeader')
        titulo_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        titulo_label.setWordWrap(True)
        titulo_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        header_layout.addWidget(titulo_label, 1)
        self._criar_barra_creditos(header_layout)
        header_layout.addStretch()
        parent_layout.addWidget(header_widget)
    def _criar_barra_creditos(self, parent_layout):
        try:
            creditos_widget = QWidget()
            creditos_widget.setObjectName('creditosWidget')
            creditos_widget.setFixedHeight(45)
            creditos_widget.setMinimumWidth(200)
            creditos_layout = QHBoxLayout(creditos_widget)
            creditos_layout.setContentsMargins(15, 8, 15, 8)
            creditos_layout.setSpacing(8)
            icon_creditos = QLabel('R$')
            icon_creditos.setStyleSheet('font-size: 14px; font-weight: bold; color: white;')
            creditos_layout.addWidget(icon_creditos)
            self.saldo_label = QLabel('Carregando...')
            self.saldo_label.setObjectName('saldoLabel')
            self.saldo_label.setAlignment(Qt.AlignCenter)
            creditos_layout.addWidget(self.saldo_label)
            btn_recarregar = QPushButton('+')
            btn_recarregar.setObjectName('btnRecarregarCreditos')
            btn_recarregar.setFixedSize(35, 35)
            btn_recarregar.setToolTip('Adicionar creditos')
            btn_recarregar.clicked.connect(self._mostrar_popup_creditos)
            creditos_layout.addWidget(btn_recarregar)
            parent_layout.addWidget(creditos_widget)
            self._atualizar_saldo_creditos()
            return
        except Exception as e:
            self.logger.error(f'Erro ao criar barra de cr├®ditos: {str(e)}')
    def _atualizar_saldo_creditos(self):
        try:
            saldo = self.arquivos_manager.obter_saldo_creditos(self.email_login)
            if saldo >= 50.0:
                cor = '#27AE60'
                status = 'ALTO'
            elif saldo >= 20.0:
                cor = '#F39C12'
                status = 'M├ëDIO'
            else:
                cor = '#E74C3C'
                status = 'BAIXO'
            texto = f'R$ {saldo:.2f}'
            self.saldo_label.setText(texto)
            self.saldo_label.setStyleSheet(f'\n                QLabel#saldoLabel {{\n                    color: {cor};\n                    font-weight: bold;\n                    font-size: 14px;\n                    padding: 5px 10px;\n                    border-radius: 15px;\n                    background-color: rgba(255, 255, 255, 0.1);\n                    border: 2px solid {cor};\n                }}\n            ')
            self.saldo_label.setToolTip(f'Saldo: R$ {saldo:.2f}\nStatus: {status}')
            self._notificar_header_saldo()
            return
        except Exception as e:
            self.logger.error(f'Erro ao atualizar saldo de cr├®ditos: {str(e)}')
            self.saldo_label.setText('Erro')
            self.saldo_label.setStyleSheet('\n                QLabel#saldoLabel {\n                    color: #E74C3C;\n                    font-weight: bold;\n                    font-size: 14px;\n                }\n            ')
    def _notificar_header_saldo(self):
        try:
            parent = getattr(self, 'parent_window', None)
            if parent is not None:
                if hasattr(parent, 'atualizar_header_saldo'):
                    parent.atualizar_header_saldo()
                    return
                return
        except Exception as e:
            self.logger.error(f'Falha ao atualizar saldo no header: {type(e).__name__}')
    def _mostrar_popup_creditos(self):
        try:
            from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame)
            from PyQt5.QtCore import Qt
            from PyQt5.QtGui import QFont, QPixmap
            import webbrowser
            import urllib.parse
            dialog = QDialog(self)
            dialog.setWindowTitle('Adicionar Creditos')
            dialog.setFixedSize(450, 320)
            dialog.setModal(True)
            dialog.setStyleSheet('\n                QDialog {\n                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                        stop: 0 #1e3c72, stop: 1 #2a5298);\n                    border-radius: 10px;\n                }\n                QLabel {\n                    color: white;\n                }\n                QPushButton {\n                    border: none;\n                    border-radius: 8px;\n                    font-weight: bold;\n                    padding: 12px 20px;\n                    font-size: 14px;\n                }\n                QPushButton:hover {\n                    transform: translateY(-2px);\n                    box-shadow: 0 4px 8px rgba(0,0,0,0.3);\n                }\n                QPushButton:pressed {\n                    transform: translateY(0px);\n                }\n            ')
            layout = QVBoxLayout(dialog)
            layout.setSpacing(20)
            layout.setContentsMargins(25, 25, 25, 25)
            header_layout = QHBoxLayout()
            icon_label = QLabel()
            icon_label.setAlignment(Qt.AlignCenter)
            svg_creditos = PathManager.get_resource_path('icons_svg/lightning-charge.svg')
            if svg_creditos:
                pixmap_c = self._svg_colorido(svg_creditos, 48, '#FFD700')
                if not pixmap_c.isNull():
                    icon_label.setPixmap(pixmap_c)
            icon_label.setStyleSheet('\n                QLabel {\n                    padding: 10px;\n                    background: rgba(255, 255, 255, 0.1);\n                    border-radius: 25px;\n                    min-width: 80px;\n                    max-width: 80px;\n                    min-height: 80px;\n                    max-height: 80px;\n                }\n            ')
            header_layout.addWidget(icon_label)
            title_label = QLabel('Seja o Primeiro!')
            title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            title_label.setStyleSheet('\n                QLabel {\n                    font-size: 24px;\n                    font-weight: bold;\n                    color: #FFD700;\n                    margin-left: 15px;\n                }\n            ')
            header_layout.addWidget(title_label)
            layout.addLayout(header_layout)
            texto_persuasivo = QLabel('\n<b>Saia na frente da concorrencia!</b>\n<br><br>\nArquivos premium as vezes tem <b>limite de downloads</b> - quem tem creditos acessa primeiro e garante sua copia!\n<br><br>\nNao perca tempo esperando na fila - mantenha creditos e tenha acesso instantaneo aos melhores arquivos!\n<br><br>\n<b>Tecnicos inteligentes sempre estao preparados!</b>\n            ')
            texto_persuasivo.setWordWrap(True)
            texto_persuasivo.setAlignment(Qt.AlignLeft)
            texto_persuasivo.setStyleSheet('\n                QLabel {\n                    font-size: 13px;\n                    line-height: 1.4;\n                    padding: 15px;\n                    background: rgba(255, 255, 255, 0.1);\n                    border-radius: 8px;\n                    border-left: 4px solid #FFD700;\n                }\n            ')
            layout.addWidget(texto_persuasivo)
            buttons_layout = QHBoxLayout()
            buttons_layout.setSpacing(15)
            btn_credito = QPushButton('Por Credito')
            btn_credito.setStyleSheet('\n                QPushButton {\n                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                        stop: 0 #27ae60, stop: 1 #2ecc71);\n                    color: white;\n                    font-size: 16px;\n                    font-weight: bold;\n                    min-width: 150px;\n                }\n                QPushButton:hover {\n                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                        stop: 0 #2ecc71, stop: 1 #58d68d);\n                }\n                QPushButton:pressed {\n                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                        stop: 0 #229954, stop: 1 #27ae60);\n                }\n            ')
            def abrir_whatsapp():
                try:
                    numero = '5585997507465'
                    mensagem = 'Ol├í! Quero por cr├®dito'
                    mensagem_encoded = urllib.parse.quote(mensagem, safe='')
                    url = f'https://wa.me/{numero}?text={mensagem_encoded}'
                    webbrowser.open(url)
                    dialog.accept()
                    return
                except Exception as e:
                    self.logger.error(f'Erro ao abrir WhatsApp: {str(e)}')
            btn_credito.clicked.connect(abrir_whatsapp)
            buttons_layout.addWidget(btn_credito)
            btn_cancelar = QPushButton('Agora Nao')
            btn_cancelar.setStyleSheet('\n                QPushButton {\n                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                        stop: 0 #95a5a6, stop: 1 #7f8c8d);\n                    color: white;\n                    font-size: 14px;\n                    min-width: 120px;\n                }\n                QPushButton:hover {\n                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                        stop: 0 #bdc3c7, stop: 1 #95a5a6);\n                }\n                QPushButton:pressed {\n                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                        stop: 0 #7f8c8d, stop: 1 #6c7b7d);\n                }\n            ')
            btn_cancelar.clicked.connect(dialog.reject)
            buttons_layout.addWidget(btn_cancelar)
            layout.addLayout(buttons_layout)
            self._atualizar_saldo_creditos()
            dialog.exec_()
            return
        except Exception as e:
            self.logger.error(f'Erro ao mostrar popup de cr├®ditos: {str(e)}')
            self._atualizar_saldo_creditos()
    def _criar_area_conteudo(self, parent_layout):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setSpacing(25)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self._criar_faixa_arquivos_recentes()
        self._criar_faixa_arquivos_populares()
        self._criar_secao_marcas()
        self._criar_loading_indicator()
        scroll_area.setWidget(content_widget)
        parent_layout.addWidget(scroll_area)
    def _criar_faixa_arquivos_recentes(self):
        try:
            faixa_recentes = QFrame()
            faixa_recentes.setObjectName('faixaRecentes')
            faixa_recentes.setFixedHeight(50)
            faixa_recentes.setStyleSheet('\n                QFrame#faixaRecentes {\n                    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,\n                        stop: 0 rgba(52, 152, 219, 0.9),\n                        stop: 0.5 rgba(52, 152, 219, 1.0),\n                        stop: 1 rgba(41, 128, 185, 0.9));\n                    border-radius: 8px;\n                    margin: 5px 0;\n                    box-shadow: 0 2px 8px rgba(52, 152, 219, 0.3);\n                }\n            ')
            faixa_layout = QHBoxLayout(faixa_recentes)
            faixa_layout.setContentsMargins(10, 5, 15, 5)
            faixa_layout.setSpacing(15)
            icon_label = QLabel()
            svg_recentes = PathManager.get_resource_path('icons_svg/cloud-arrow-down.svg')
            if svg_recentes:
                pixmap_r = self._svg_colorido(svg_recentes, 18, '#ffffff')
                if not pixmap_r.isNull():
                    icon_label.setPixmap(pixmap_r)
            icon_label.setStyleSheet('padding-right: 8px;')
            faixa_layout.addWidget(icon_label)
            titulo_label = QLabel('Arquivos Recentes:')
            titulo_label.setStyleSheet('\n                font-size: 14px;\n                font-weight: bold;\n                color: white;\n                padding-right: 10px;\n                min-width: 120px;\n                max-width: 150px;\n                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);\n            ')
            faixa_layout.addWidget(titulo_label, 0)
            self.recentes_label = QLabel()
            self.recentes_label.setStyleSheet("\n                padding: 5px 10px;\n                font-family: 'Segoe UI', Arial;\n                font-weight: bold;\n                font-size: 13px;\n                color: white;\n                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);\n                min-width: 200px;\n                background: transparent;\n            ")
            self.recentes_label.setWordWrap(False)
            self.recentes_label.setFixedHeight(30)
            self.recentes_label.setAlignment(Qt.AlignVCenter)
            faixa_layout.addWidget(self.recentes_label, 1)
            btn_ver_recentes = QPushButton('Ver Recentes')
            btn_ver_recentes.setObjectName('btnVerRecentes')
            btn_ver_recentes.setCursor(Qt.PointingHandCursor)
            btn_ver_recentes.setSizePolicy(btn_ver_recentes.sizePolicy().horizontalPolicy(), btn_ver_recentes.sizePolicy().verticalPolicy())
            btn_ver_recentes.clicked.connect(self._mostrar_todos_recentes)
            faixa_layout.addWidget(btn_ver_recentes, 0)
            self.content_layout.addWidget(faixa_recentes)
            faixa_recentes.show()
            return
        except Exception as e:
            self.logger.error(f'Erro ao criar faixa de recentes: {str(e)}')
    def _criar_faixa_arquivos_populares(self):
        try:
            faixa_populares = QFrame()
            faixa_populares.setObjectName('faixaPopulares')
            faixa_populares.setFixedHeight(50)
            faixa_populares.setStyleSheet('\n                QFrame#faixaPopulares {\n                    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,\n                        stop: 0 rgba(231, 76, 60, 0.9),\n                        stop: 0.5 rgba(231, 76, 60, 1.0),\n                        stop: 1 rgba(192, 57, 43, 0.9));\n                    border-radius: 8px;\n                    margin: 5px 0;\n                    box-shadow: 0 2px 8px rgba(231, 76, 60, 0.3);\n                }\n            ')
            faixa_layout = QHBoxLayout(faixa_populares)
            faixa_layout.setContentsMargins(10, 5, 15, 5)
            faixa_layout.setSpacing(15)
            icon_label = QLabel()
            svg_populares = PathManager.get_resource_path('icons_svg/lightning-charge.svg')
            if svg_populares:
                pixmap_p = self._svg_colorido(svg_populares, 18, '#ffffff')
                if not pixmap_p.isNull():
                    icon_label.setPixmap(pixmap_p)
            icon_label.setStyleSheet('padding-right: 8px;')
            faixa_layout.addWidget(icon_label)
            titulo_label = QLabel('Arquivos Populares:')
            titulo_label.setStyleSheet('\n                font-size: 14px;\n                font-weight: bold;\n                color: white;\n                padding-right: 10px;\n                min-width: 120px;\n                max-width: 150px;\n                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);\n            ')
            faixa_layout.addWidget(titulo_label, 0)
            self.populares_label = QLabel()
            self.populares_label.setStyleSheet("\n                padding: 5px 10px;\n                font-family: 'Segoe UI', Arial;\n                font-weight: bold;\n                font-size: 13px;\n                color: white;\n                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);\n                min-width: 200px;\n                background: transparent;\n            ")
            self.populares_label.setWordWrap(False)
            self.populares_label.setFixedHeight(30)
            self.populares_label.setAlignment(Qt.AlignVCenter)
            faixa_layout.addWidget(self.populares_label, 1)
            btn_ver_populares = QPushButton('Ver Populares')
            btn_ver_populares.setObjectName('btnVerPopulares')
            btn_ver_populares.setCursor(Qt.PointingHandCursor)
            btn_ver_populares.setSizePolicy(btn_ver_populares.sizePolicy().horizontalPolicy(), btn_ver_populares.sizePolicy().verticalPolicy())
            btn_ver_populares.clicked.connect(self._mostrar_todos_populares)
            faixa_layout.addWidget(btn_ver_populares, 0)
            self.content_layout.addWidget(faixa_populares)
            faixa_populares.show()
            QApplication.processEvents()
            return
        except Exception as e:
            self.logger.error(f'Erro ao criar faixa de populares: {str(e)}')
    def _criar_secao_populares(self):
        titulo = QLabel('Arquivos Principais')
        titulo.setObjectName('tituloSecao')
        titulo.setFont(QFont('Arial', 16, QFont.Bold))
        self.content_layout.addWidget(titulo)
        scroll_populares = QScrollArea()
        scroll_populares.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_populares.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_populares.setFixedHeight(220)
        scroll_populares.setWidgetResizable(True)
        scroll_populares.setObjectName('scrollPopulares')
        self.populares_frame = QWidget()
        self.populares_frame.setObjectName('popularesFrame')
        self.populares_layout = QHBoxLayout(self.populares_frame)
        self.populares_layout.setSpacing(20)
        self.populares_layout.setContentsMargins(15, 15, 15, 15)
        scroll_populares.setWidget(self.populares_frame)
        self.content_layout.addWidget(scroll_populares)
    def _criar_secao_marcas(self):
        titulo = QLabel('Marcas Disponiveis')
        titulo.setObjectName('tituloSecao')
        titulo.setFont(QFont('Arial', 16, QFont.Bold))
        self.content_layout.addWidget(titulo)
        self.marcas_frame = QFrame()
        self.marcas_frame.setObjectName('marcasFrame')
        self.marcas_layout = QGridLayout(self.marcas_frame)
        self.marcas_layout.setSpacing(20)
        self.content_layout.addWidget(self.marcas_frame)
    def _criar_loading_indicator(self):
        self.loading_frame = QFrame()
        self.loading_frame.setObjectName('loadingFrame')
        self.loading_frame.setFixedHeight(100)
        self.loading_frame.hide()
        loading_layout = QVBoxLayout(self.loading_frame)
        loading_layout.setAlignment(Qt.AlignCenter)
        loading_label = QLabel('Carregando arquivos...')
        loading_label.setFont(QFont('Arial', 14))
        loading_label.setAlignment(Qt.AlignCenter)
        loading_layout.addWidget(loading_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(8)
        loading_layout.addWidget(self.progress_bar)
        self.content_layout.addWidget(self.loading_frame)
    def _carregar_dados_iniciais(self):
        self._mostrar_loading(True)
        try:
            self._forcar_atualizacao_cache()
            self._carregar_marcas()
            self._carregar_arquivos_recentes()
            self._carregar_arquivos_populares()
            self._atualizar_faixa_recentes()
            self._atualizar_faixa_populares()
        except Exception as e:
            self.logger.error(f'Erro carregar dados: {str(e)}')
            QMessageBox.critical(self, 'Erro', 'Erro ao carregar dados. Tente novamente.')
        finally:
            self._mostrar_loading(False)
            QTimer.singleShot(800, self._iniciar_animacao_faixas)
    def _carregar_marcas(self):
        try:
            self.logger.info('Carregando TODAS as marcas do servidor de arquivos')
            marcas_cache = self.cache.obter_marcas_cache()
            if marcas_cache and len(marcas_cache) > 0:
                self.marcas_disponiveis = marcas_cache
                self.logger.info(f'{len(self.marcas_disponiveis)} marcas carregadas do cache')
                self._popular_grid_marcas()
                QTimer.singleShot(2000, self._verificar_atualizacoes_incrementais)
                return
            self.logger.info('Cache vazio, buscando marcas do servidor...')
            self._buscar_marcas_mysql_completo()
            return
        except Exception as e:
            self.logger.error(f'Erro ao carregar marcas: {str(e)}')
            self._carregar_marcas_fallback()
    def _verificar_atualizacoes_incrementais(self):
        try:
            self.logger.info('Verificando atualizacoes incrementais...')
            marcas_mysql = self.arquivos_manager.obter_marcas_disponiveis()
            if marcas_mysql and len(marcas_mysql) > len(self.marcas_disponiveis):
                self.logger.info(f'Encontradas {len(marcas_mysql)} marcas (tinha {len(self.marcas_disponiveis)})')
                self.marcas_disponiveis = marcas_mysql
                self._popular_grid_marcas()
                self.cache.salvar_marcas_cache(marcas_mysql)
                self.logger.info(f'Cache atualizado incrementalmente com {len(marcas_mysql)} marcas')
                return
            self.logger.info(f'Marcas ja atualizadas: {len(self.marcas_disponiveis)} marcas')
            return
        except Exception as e:
            self.logger.error(f'Erro na verifica├º├úo incremental: {str(e)}')
    def _buscar_marcas_mysql_completo(self):
        try:
            self.logger.info('Buscando marcas do servidor...')
            marcas_mysql = self.arquivos_manager.obter_marcas_disponiveis()
            if marcas_mysql and len(marcas_mysql) > 0:
                self.marcas_disponiveis = marcas_mysql
                self._popular_grid_marcas()
                self.cache.salvar_marcas_cache(marcas_mysql)
                self.logger.info(f'{len(marcas_mysql)} marcas carregadas e salvas no cache')
                return
            self.logger.warning('Nenhuma marca encontrada no servidor')
            self._carregar_marcas_fallback()
            return
        except Exception as e:
            self.logger.error(f'Erro ao buscar marcas: {str(e)}')
            self._carregar_marcas_fallback()
    def _carregar_marcas_fallback(self):
        self.logger.info('Usando marcas de fallback para garantir funcionalidade')
        self.marcas_disponiveis = [{'marca': 'Samsung', 'categorias': ['Firmware', 'Tool', 'Driver']}, {'marca': 'Motorola', 'categorias': ['Firmware', 'Tool', 'Driver']}, {'marca': 'Xiaomi', 'categorias': ['Firmware', 'Tool', 'Driver']}, {'marca': 'Apple', 'categorias': ['Firmware', 'Tool', 'Driver']}]
        self._popular_grid_marcas()
    def _carregar_arquivos_recentes(self):
        self.arquivos_recentes = self.arquivos_manager.obter_arquivos_recentes(5)
    def _carregar_arquivos_populares(self):
        self.arquivos_populares = self.arquivos_manager.obter_arquivos_populares(5)
    def _popular_grid_marcas(self):
        self._limpar_layout(self.marcas_layout)
        if not self.marcas_disponiveis:
            sem_marcas = QLabel('Nenhuma marca disponivel no momento')
            sem_marcas.setAlignment(Qt.AlignCenter)
            sem_marcas.setStyleSheet('color: #666; font-size: 14px; padding: 40px;')
            self.marcas_layout.addWidget(sem_marcas, 0, 0, 1, 4)
            return
        row = col = 0
        for marca_info in self.marcas_disponiveis:
            card = self._criar_card_marca(marca_info)
            self.marcas_layout.addWidget(card, row, col)
            col += 1
            if col >= 4:
                col = 0
                row += 1
    def _svg_colorido(self, svg_path, size, color):
        try:
            icon = QIcon(svg_path)
            pixmap = icon.pixmap(QSize(size, size))
            if not pixmap.isNull():
                painter = QPainter(pixmap)
                painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
                painter.fillRect(pixmap.rect(), QColor(color))
                painter.end()
            return pixmap
        except Exception:
            return QPixmap()
    def _criar_card_marca(self, marca_info):
        card = QFrame()
        card.setObjectName('cardMarca')
        card.setFixedSize(280, 170)
        card.setCursor(QCursor(Qt.PointingHandCursor))
        card.enterEvent = lambda event: self._on_card_hover_enter(card)
        card.leaveEvent = lambda event: self._on_card_hover_leave(card)
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignCenter)
        svg_path = PathManager.get_resource_path('icons_svg/folder2-open.svg')
        if svg_path:
            pixmap = self._svg_colorido(svg_path, 44, '#3498db')
            if not pixmap.isNull():
                icon_label.setPixmap(pixmap)
        icon_label.setStyleSheet('margin-bottom: 5px;')
        layout.addWidget(icon_label)
        nome_label = QLabel(marca_info['marca'])
        nome_label.setObjectName('nomeMarca')
        nome_label.setAlignment(Qt.AlignCenter)
        nome_label.setWordWrap(True)
        nome_label.setFont(QFont('Arial', 14, QFont.Bold))
        layout.addWidget(nome_label)
        card.mousePressEvent = lambda e: self._abrir_categorias(marca_info['marca'])
        return card
    def _on_card_hover_enter(self, card):
        card.setStyleSheet('\n            QFrame#cardMarca {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #ffffff, stop: 1 #f8f9fa);\n                border: 2px solid #3498db;\n                border-radius: 12px;\n                margin: 3px;\n                padding: 12px;\n                box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);\n            }\n            QLabel#nomeMarca {\n                color: #2980b9;\n                font-weight: bold;\n            }\n        ')
    def _on_card_hover_leave(self, card):
        card.setStyleSheet('\n            QFrame#cardMarca {\n                background-color: white;\n                border: 2px solid #ecf0f1;\n                border-radius: 12px;\n                margin: 3px;\n                padding: 12px;\n            }\n            QLabel#nomeMarca {\n                color: #2c3e50;\n                font-weight: bold;\n            }\n        ')
    def _atualizar_faixa_recentes(self):
        if not hasattr(self, 'recentes_label'):
            return
        if not self.arquivos_recentes:
            self.recentes_label.setText('Nenhum arquivo recente disponivel no momento')
            self.texto_recentes_completo = 'Nenhum arquivo recente disponivel no momento'
            return
        arquivos_texto = []
        for arquivo in self.arquivos_recentes[:5]:
            titulo = arquivo.get('titulo', 'Arquivo')
            marca = arquivo.get('marca', 'N/A')
            modelo = arquivo.get('modelo', arquivo.get('versao', ''))
            categoria = arquivo.get('categoria', '')
            texto_arquivo = f'{titulo} - {marca}'
            if modelo:
                texto_arquivo += f' {modelo}'
            if categoria:
                texto_arquivo += f' ({categoria})'
            arquivos_texto.append(texto_arquivo)
        self.texto_recentes_completo = ' | '.join(arquivos_texto)
        self.texto_recentes_completo = '          ' + self.texto_recentes_completo + '          '
        self.recentes_label.setText(self.texto_recentes_completo)
    def _atualizar_faixa_populares(self):
        if not hasattr(self, 'populares_label'):
            return
        if not self.arquivos_populares:
            self.populares_label.setText('Nenhum arquivo popular disponivel no momento')
            self.texto_populares_completo = 'Nenhum arquivo popular disponivel no momento'
            return
        arquivos_texto = []
        for arquivo in self.arquivos_populares[:5]:
            titulo = arquivo.get('titulo', 'Arquivo')
            marca = arquivo.get('marca', 'N/A')
            modelo = arquivo.get('modelo', arquivo.get('versao', ''))
            categoria = arquivo.get('categoria', '')
            visualizacoes = arquivo.get('quantidade_downloads', 0)
            texto_arquivo = f'{titulo} - {marca}'
            if modelo:
                texto_arquivo += f' {modelo}'
            if categoria:
                texto_arquivo += f' ({categoria})'
            texto_arquivo += f' [{visualizacoes} downloads]'
            arquivos_texto.append(texto_arquivo)
        self.texto_populares_completo = ' | '.join(arquivos_texto)
        self.texto_populares_completo = '          ' + self.texto_populares_completo + '          '
        self.populares_label.setText(self.texto_populares_completo)
    def _criar_card_arquivo_pequeno(self, arquivo):
        card = QFrame()
        card.setObjectName('cardArquivoPequeno')
        card.setFixedSize(250, 180)
        card.setCursor(QCursor(Qt.PointingHandCursor))
        layout = QVBoxLayout(card)
        layout.setSpacing(6)
        layout.setContentsMargins(12, 12, 12, 12)
        tipo_icon = 'Gratis' if arquivo.get('tipo_arquivo') == 'gratuito' else 'Pago'
        icon_label = QLabel(tipo_icon)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet('font-size: 11px; margin-bottom: 3px; font-weight: bold; color: #27ae60;' if arquivo.get('tipo_arquivo') == 'gratuito' else 'font-size: 11px; margin-bottom: 3px; font-weight: bold; color: #e67e22;')
        layout.addWidget(icon_label)
        titulo = arquivo.get('titulo', 'Arquivo')
        if len(titulo) > 20:
            titulo = titulo[:18] + '...'
        titulo_label = QLabel(titulo)
        titulo_label.setAlignment(Qt.AlignCenter)
        titulo_label.setWordWrap(True)
        titulo_label.setFont(QFont('Arial', 10, QFont.Bold))
        titulo_label.setStyleSheet('color: #2c3e50; margin-bottom: 2px;')
        layout.addWidget(titulo_label)
        marca = arquivo.get('marca', 'N/A')
        marca_label = QLabel(f'{marca}')
        marca_label.setAlignment(Qt.AlignCenter)
        marca_label.setStyleSheet('color: #34495e; font-size: 9px; font-weight: 600;')
        layout.addWidget(marca_label)
        modelo = arquivo.get('modelo', arquivo.get('versao', 'N/A'))
        if modelo and modelo != 'N/A':
            modelo_label = QLabel(f'{modelo}')
            modelo_label.setAlignment(Qt.AlignCenter)
            modelo_label.setStyleSheet('color: #7f8c8d; font-size: 8px; font-weight: 500;')
            layout.addWidget(modelo_label)
        categoria = arquivo.get('categoria', '')
        if categoria:
            categoria_label = QLabel(f'{categoria}')
            categoria_label.setAlignment(Qt.AlignCenter)
            categoria_label.setStyleSheet('color: #95a5a6; font-size: 8px;')
            layout.addWidget(categoria_label)
        downloads_count = arquivo.get('quantidade_downloads', 0)
        downloads_label = QLabel(f'{downloads_count} downloads')
        downloads_label.setAlignment(Qt.AlignCenter)
        downloads_label.setStyleSheet('color: #bdc3c7; font-size: 8px; margin-top: 1px;')
        layout.addWidget(downloads_label)
        card.mousePressEvent = lambda e: self._processar_click_arquivo(arquivo)
        return card
    def _abrir_categorias(self, marca):
        try:
            from app.views.downloads.categorias_window import CategoriasWindow
            self.categorias_window = CategoriasWindow(marca, self.email_login, self)
            self.categorias_window.setWindowFlags(Qt.Window)
            self.categorias_window.showMaximized()
            return
        except Exception as e:
            self.logger.error(f'Erro abrir categorias: {str(e)}')
            QMessageBox.critical(self, 'Erro', 'N├úo foi poss├¡vel abrir as categorias. Tente novamente.')
    def _processar_click_arquivo(self, arquivo):
        try:
            janela_atual = getattr(self, 'detalhe_window', None)
            if janela_atual is not None and janela_atual.isVisible():
                janela_atual.activateWindow()
                janela_atual.raise_()
                return
            arquivo_completo = self.arquivos_manager.obter_detalhes_arquivo(arquivo['id'])
            if not arquivo_completo:
                QMessageBox.warning(self, 'Aviso', 'Arquivo n├úo encontrado ou indispon├¡vel.')
                return
            from app.views.downloads.detalhe_arquivo_window import DetalheArquivoWindow
            self.detalhe_window = DetalheArquivoWindow(arquivo_completo, self.email_login, self)
            self.detalhe_window.setWindowFlags(Qt.Window)
            self.detalhe_window.show()
            return
        except Exception as e:
            self.logger.error(f'Erro ao abrir detalhes do arquivo: {str(e)}')
            QMessageBox.critical(self, 'Erro', 'N├úo foi poss├¡vel abrir os detalhes do arquivo. Tente novamente.')
    def _abrir_arquivo_gratuito(self, arquivo):
        try:
            from app.views.downloads.arquivo_gratuito_dialog import ArquivoGratuitoDialog
            detalhes = self.arquivos_manager.obter_detalhes_arquivo(arquivo['id'])
            if not detalhes:
                QMessageBox.warning(self, 'Erro', 'N├úo foi poss├¡vel carregar detalhes do arquivo.')
                return
            dialog = ArquivoGratuitoDialog(detalhes, self)
            dialog.download_iniciado.connect((lambda: self.logger.info(f'Download iniciado: {arquivo['titulo']}')))
            dialog.exec_()
            return
        except Exception as e:
            self.logger.error(f'Erro ao abrir arquivo gratuito: {str(e)}')
            QMessageBox.critical(self, 'Erro', 'N├úo foi poss├¡vel abrir o arquivo. Tente novamente.')
    def _fazer_download_gratuito(self, arquivo_id):
        try:
            link = self.arquivos_manager.obter_link_download_gratuito(arquivo_id)
            if link:
                webbrowser.open(link)
                QMessageBox.information(self, 'Download Iniciado', 'O download foi iniciado no seu navegador!')
                return
            QMessageBox.warning(self, 'Erro', 'Link de download n├úo dispon├¡vel.')
            return
        except Exception as e:
            self.logger.error(f'Erro download gratuito: {str(e)}')
            QMessageBox.critical(self, 'Erro', 'Erro ao processar download.')
    def _abrir_detalhes_arquivo(self, arquivo):
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle(f'Detalhes: {arquivo.get('nome_arquivo', 'Arquivo Desconhecido')}')
            dialog.setFixedSize(500, 450)
            dialog.setStyleSheet("\n                QDialog {\n                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                        stop: 0 #f8f9fa, stop: 1 #e9ecef);\n                    border-radius: 10px;\n                }\n                QLabel {\n                    color: #2c3e50;\n                    font-family: 'Segoe UI', Arial;\n                }\n                QPushButton {\n                    font-family: 'Segoe UI', Arial;\n                    font-weight: bold;\n                    border-radius: 6px;\n                    padding: 8px 16px;\n                }\n                QPushButton#btnBaixar {\n                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                        stop: 0 #27ae60, stop: 1 #219a52);\n                    color: white;\n                    border: none;\n                }\n                QPushButton#btnBaixar:hover {\n                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                        stop: 0 #2ecc71, stop: 1 #27ae60);\n                }\n                QPushButton#btnFechar {\n                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                        stop: 0 #e74c3c, stop: 1 #c0392b);\n                    color: white;\n                    border: none;\n                }\n                QPushButton#btnFechar:hover {\n                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                        stop: 0 #ec7063, stop: 1 #e74c3c);\n                }\n                QTextEdit {\n                    background: white;\n                    border: 1px solid #bdc3c7;\n                    border-radius: 6px;\n                    padding: 8px;\n                    font-size: 12px;\n                }\n            ")
            layout = QVBoxLayout(dialog)
            layout.setSpacing(15)
            layout.setContentsMargins(20, 20, 20, 20)
            titulo = QLabel(f'{arquivo.get('nome_arquivo', 'Arquivo Desconhecido')}')
            titulo.setStyleSheet('font-size: 16px; font-weight: bold; color: #2980b9; margin-bottom: 10px;')
            layout.addWidget(titulo)
            info_frame = QFrame()
            info_layout = QVBoxLayout(info_frame)
            marca_label = QLabel(f'Marca: {arquivo.get('marca', 'N/A')}')
            marca_label.setStyleSheet('font-size: 13px; margin: 3px 0;')
            info_layout.addWidget(marca_label)
            categoria_label = QLabel(f'Categoria: {arquivo.get('categoria', 'N/A')}')
            categoria_label.setStyleSheet('font-size: 13px; margin: 3px 0;')
            info_layout.addWidget(categoria_label)
            tipo = 'Gratuito' if arquivo.get('tipo_arquivo') == 'gratuito' else 'Premium'
            tipo_label = QLabel(f'Tipo: {tipo}')
            tipo_label.setStyleSheet('font-size: 13px; margin: 3px 0;')
            info_layout.addWidget(tipo_label)
            tamanho = arquivo.get('tamanho_arquivo', 'N/A')
            if tamanho and tamanho != 'N/A':
                if isinstance(tamanho, (int, float)) and tamanho > 0:
                    if tamanho >= 1073741824:
                        tamanho_str = f'{tamanho / 1073741824:.1f} GB'
                    elif tamanho >= 1048576:
                        tamanho_str = f'{tamanho / 1048576:.1f} MB'
                    elif tamanho >= 1024:
                        tamanho_str = f'{tamanho / 1024:.1f} KB'
                    else:
                        tamanho_str = f'{tamanho} bytes'
                else:
                    tamanho_str = str(tamanho)
            else:
                tamanho_str = 'N/A'
            tamanho_label = QLabel(f'Tamanho: {tamanho_str}')
            tamanho_label.setStyleSheet('font-size: 13px; margin: 3px 0;')
            info_layout.addWidget(tamanho_label)
            downloads = arquivo.get('total_downloads', 0)
            downloads_label = QLabel(f'Downloads: {downloads:,}')
            downloads_label.setStyleSheet('font-size: 13px; margin: 3px 0;')
            info_layout.addWidget(downloads_label)
            layout.addWidget(info_frame)
            desc_label = QLabel('Descricao:')
            desc_label.setStyleSheet('font-size: 14px; font-weight: bold; margin-top: 10px;')
            layout.addWidget(desc_label)
            desc_text = QTextEdit()
            desc_text.setPlainText(arquivo.get('descricao', 'Nenhuma descri├º├úo dispon├¡vel.'))
            desc_text.setMaximumHeight(80)
            desc_text.setReadOnly(True)
            layout.addWidget(desc_text)
            botoes_layout = QHBoxLayout()
            botoes_layout.setSpacing(10)
            btn_baixar = QPushButton('Baixar Arquivo')
            btn_baixar.setObjectName('btnBaixar')
            btn_baixar.clicked.connect((lambda: self._confirmar_download_arquivo(arquivo, dialog)))
            botoes_layout.addWidget(btn_baixar)
            btn_fechar = QPushButton('Fechar')
            btn_fechar.setObjectName('btnFechar')
            btn_fechar.clicked.connect(dialog.close)
            botoes_layout.addWidget(btn_fechar)
            layout.addLayout(botoes_layout)
            dialog.exec_()
            return
        except Exception as e:
            self.logger.error(f'Erro ao mostrar detalhes do arquivo: {str(e)}')
            QMessageBox.warning(self, 'Erro', 'N├úo foi poss├¡vel carregar os detalhes do arquivo. Tente novamente.')
    def _confirmar_download_arquivo(self, arquivo, dialog):
        dialog.close()
        self._processar_click_arquivo(arquivo)
    def _mostrar_loading(self, mostrar: bool):
        if mostrar:
            self.loading_frame.show()
            return
        self.loading_frame.hide()
    def _limpar_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    def _aplicar_estilos(self):
        self.setStyleSheet("\n            QMainWindow {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #f4f6f9, stop: 1 #e8eef7);\n                font-family: 'Segoe UI', 'SF Pro Display', Arial, sans-serif;\n            }\n            \n            QFrame#headerFrame {\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, \n                    stop:0 #2c3e50, stop:0.5 #3498db, stop:1 #2980b9);\n                border-radius: 10px;\n                margin: 5px;\n                padding: 8px;\n                border: 1px solid rgba(0, 0, 0, 0.1);\n                box-shadow: 0 3px 10px rgba(44, 62, 80, 0.2);\n            }\n            \n            QLabel#tituloHeader {\n                color: white;\n                font-weight: bold;\n                font-size: 20px;  /* Tamanho maior j├í que n├úo compete com busca */\n                text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);\n                letter-spacing: 0.8px;\n                padding: 8px 15px;\n                min-height: 30px;\n                max-height: 50px;\n            }\n            \n            QPushButton#btnVoltar {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 rgba(255, 255, 255, 0.95), stop: 1 rgba(255, 255, 255, 0.8));\n                color: #2c3e50;\n                border: 2px solid rgba(255, 255, 255, 0.9);\n                border-radius: 18px;  /* Raio menor para bot├úo menor */\n                font-weight: bold;\n                font-size: 13px;  /* Fonte menor para responsividade */\n                text-shadow: none;\n                box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);\n                letter-spacing: 0.3px;\n                padding: 6px 12px;  /* Padding responsivo */\n            }\n            \n            QPushButton#btnVoltar:hover {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #ffffff, stop: 1 #f8f9fa);\n                border-color: #ffffff;\n                transform: translateY(-1px);  /* Movimento menor */\n                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);\n            }\n            \n            QPushButton#btnVoltar:pressed {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #ecf0f1, stop: 1 #bdc3c7);\n                transform: translateY(0px);\n                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);\n            }\n            \n\n            \n            QLabel#tituloSecao {\n                color: #2c3e50;\n                margin: 15px 0;\n                padding: 8px 0;\n                border-bottom: 3px solid #3498db;\n                font-size: 20px;\n                font-weight: bold;\n                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);\n            }\n            \n            QFrame#cardMarca {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #ffffff, stop: 1 #f8f9fa);\n                border: 2px solid #e9ecef;\n                border-radius: 15px;\n                margin: 8px;\n                padding: 18px;\n                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);\n            }\n            \n            QFrame#cardMarca:hover {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #f8f9fa, stop: 1 #e3f2fd);\n                border-color: #3498db;\n                transform: translateY(-2px);\n                box-shadow: 0 6px 16px rgba(52, 152, 219, 0.2);\n            }\n            \n            QLabel#nomeMarca {\n                color: #2c3e50;\n                font-weight: bold;\n                font-size: 16px;\n                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);\n            }\n            \n            /* Faixas animadas - cores inspiradas no main_window */\n            QFrame#faixaRecentesFrame {\n                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,\n                    stop: 0 #3498db, stop: 1 #2980b9);\n                border-radius: 8px;\n                margin: 8px 0px;\n                padding: 12px;\n                min-height: 50px;\n                max-height: 50px;\n                box-shadow: 0 3px 8px rgba(52, 152, 219, 0.3);\n            }\n            \n            QFrame#faixaPopularesFrame {\n                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,\n                    stop: 0 #e74c3c, stop: 1 #c0392b);\n                border-radius: 8px;\n                margin: 8px 0px;\n                padding: 12px;\n                min-height: 50px;\n                max-height: 50px;\n                box-shadow: 0 3px 8px rgba(231, 76, 60, 0.3);\n            }\n            \n            QFrame#cardArquivoPequeno {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #ffffff, stop: 1 #f8f9fa);\n                border: 2px solid #e9ecef;\n                border-radius: 15px;\n                margin: 8px;\n                padding: 12px;\n                min-width: 250px;\n                max-width: 250px;\n                min-height: 180px;\n                max-height: 180px;\n                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);\n            }\n            \n            QFrame#cardArquivoPequeno:hover {\n                border-color: #3498db;\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #f8f9fa, stop: 1 #e3f2fd);\n                transform: scale(1.05) translateY(-3px);\n                box-shadow: 0 8px 20px rgba(52, 152, 219, 0.25);\n            }\n            \n            QScrollArea {\n                border: none;\n                background-color: transparent;\n            }\n            \n            QScrollArea#scrollRecentes, QScrollArea#scrollPopulares {\n                border: 2px solid #e9ecef;\n                border-radius: 12px;\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #ffffff, stop: 1 #fdfdfe);\n                margin: 8px 0;\n                box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);\n            }\n            \n            QScrollArea QScrollBar:horizontal {\n                height: 14px;\n                background-color: #ecf0f1;\n                border-radius: 7px;\n                margin: 3px;\n            }\n            \n            QScrollArea QScrollBar::handle:horizontal {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #bdc3c7, stop: 1 #95a5a6);\n                border-radius: 7px;\n                min-width: 25px;\n            }\n            \n            QScrollArea QScrollBar::handle:horizontal:hover {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #95a5a6, stop: 1 #7f8c8d);\n            }\n            \n            QScrollArea QScrollBar:vertical {\n                width: 14px;\n                background-color: #ecf0f1;\n                border-radius: 7px;\n                margin: 3px;\n            }\n            \n            QScrollArea QScrollBar::handle:vertical {\n                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,\n                    stop: 0 #bdc3c7, stop: 1 #95a5a6);\n                border-radius: 7px;\n                min-height: 25px;\n            }\n            \n            QScrollArea QScrollBar::handle:vertical:hover {\n                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,\n                    stop: 0 #95a5a6, stop: 1 #7f8c8d);\n            }\n            \n            QWidget#recentesFrame, QWidget#popularesFrame {\n                background-color: transparent;\n                border-radius: 12px;\n                padding: 15px;\n                min-height: 200px;\n            }\n            \n            QFrame#loadingFrame {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #f8f9fa, stop: 1 #e9ecef);\n                border: 1px solid #dee2e6;\n                border-radius: 12px;\n                margin: 15px 0px;\n                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);\n            }\n            \n            QProgressBar {\n                border: 1px solid #dee2e6;\n                border-radius: 6px;\n                background-color: #e9ecef;\n                text-align: center;\n                font-weight: bold;\n                font-size: 12px;\n                box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);\n            }\n            \n            QProgressBar::chunk {\n                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,\n                    stop: 0 #3498db, stop: 1 #2980b9);\n                border-radius: 6px;\n                box-shadow: 0 1px 3px rgba(52, 152, 219, 0.3);\n            }\n        ")
    def _forcar_atualizacao_cache(self):
        pass
    def _iniciar_animacao_faixas(self):
        self.scroll_timer = QTimer()
        self.scroll_timer.timeout.connect(self._animar_faixas)
        self.scroll_timer.start(150)
    def _animar_faixas(self):
        if hasattr(self, 'texto_recentes_completo') and self.texto_recentes_completo:
            if not hasattr(self, 'scroll_position_recentes'):
                self.scroll_position_recentes = 0
            self.scroll_position_recentes += 1
            if self.scroll_position_recentes >= len(self.texto_recentes_completo):
                self.scroll_position_recentes = 0
            texto_rotacionado = self.texto_recentes_completo[self.scroll_position_recentes:] + self.texto_recentes_completo[:self.scroll_position_recentes]
            self.recentes_label.setText(texto_rotacionado)
        if hasattr(self, 'texto_populares_completo'):
            if self.texto_populares_completo:
                if not hasattr(self, 'scroll_position_populares'):
                    self.scroll_position_populares = 0
                self.scroll_position_populares += 1
                if self.scroll_position_populares >= len(self.texto_populares_completo):
                    self.scroll_position_populares = 0
                texto_rotacionado = self.texto_populares_completo[self.scroll_position_populares:] + self.texto_populares_completo[:self.scroll_position_populares]
                self.populares_label.setText(texto_rotacionado)
    def _mostrar_todos_recentes(self):
        from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QLabel)
        dialog = QDialog(self)
        dialog.setWindowTitle('Arquivos Recentes - Tech Union Downloads')
        dialog.setMinimumSize(700, 500)
        dialog.setStyleSheet('\n            QDialog {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #f8f9fa, stop: 1 #e9ecef);\n            }\n            QLabel#tituloDialog {\n                font-size: 18px;\n                font-weight: bold;\n                color: white;\n                padding: 15px;\n                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,\n                    stop: 0 #3498db, stop: 1 #2980b9);\n                border-radius: 8px;\n                margin-bottom: 10px;\n                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);\n            }\n            QListWidget {\n                border: 2px solid #dee2e6;\n                border-radius: 8px;\n                background-color: white;\n                font-size: 14px;\n                padding: 5px;\n            }\n            QListWidget::item {\n                padding: 12px;\n                border-bottom: 1px solid #e9ecef;\n                background-color: white;\n                border-radius: 4px;\n                margin: 2px;\n            }\n            QListWidget::item:hover {\n                background-color: #e3f2fd;\n                transform: translateY(-1px);\n                box-shadow: 0 2px 8px rgba(52, 152, 219, 0.2);\n            }\n            QListWidget::item:selected {\n                background-color: #2196f3;\n                color: white;\n                box-shadow: 0 3px 10px rgba(33, 150, 243, 0.3);\n            }\n            QPushButton {\n                padding: 10px 20px;\n                border-radius: 6px;\n                font-weight: bold;\n                font-size: 14px;\n                border: none;\n            }\n            QPushButton#btnBaixar {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #2ecc71, stop: 1 #27ae60);\n                color: white;\n            }\n            QPushButton#btnBaixar:hover {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #58d68d, stop: 1 #2ecc71);\n                transform: translateY(-2px);\n            }\n            QPushButton#btnFechar {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #95a5a6, stop: 1 #7f8c8d);\n                color: white;\n            }\n            QPushButton#btnFechar:hover {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #bdc3c7, stop: 1 #95a5a6);\n            }\n        ')
        layout = QVBoxLayout(dialog)
        titulo = QLabel('Arquivos Recentes do Servidor')
        titulo.setObjectName('tituloDialog')
        layout.addWidget(titulo)
        lista = QListWidget()
        if self.arquivos_recentes:
            for arquivo in self.arquivos_recentes:
                titulo_arquivo = arquivo.get('titulo', 'Arquivo')
                marca = arquivo.get('marca', 'N/A')
                modelo = arquivo.get('modelo', arquivo.get('versao', ''))
                categoria = arquivo.get('categoria', '')
                downloads = arquivo.get('quantidade_downloads', 0)
                tipo = 'Premium' if arquivo.get('tipo_arquivo') == 'pago' else 'Gratuito'
                texto_item = f'{titulo_arquivo}\n'
                texto_item += f'   {marca} {modelo}\n'
                if categoria:
                    texto_item += f'   Categoria: {categoria}\n'
                texto_item += f'   {downloads} downloads | {tipo}'
                item = QListWidgetItem(texto_item)
                item.setData(Qt.UserRole, arquivo)
                lista.addItem(item)
        else:
            item = QListWidgetItem('Nenhum arquivo recente disponivel no momento')
            lista.addItem(item)
        layout.addWidget(lista)
        botoes_layout = QHBoxLayout()
        if self.arquivos_recentes:
            btn_detalhes = QPushButton('Ver Detalhes')
            btn_detalhes.setObjectName('btnBaixar')
            btn_detalhes.clicked.connect((lambda: self._ver_detalhes_arquivo_dialog(lista, dialog)))
            botoes_layout.addWidget(btn_detalhes)
        btn_fechar = QPushButton('Fechar')
        btn_fechar.setObjectName('btnFechar')
        btn_fechar.clicked.connect(dialog.close)
        botoes_layout.addWidget(btn_fechar)
        layout.addLayout(botoes_layout)
        dialog.exec_()
    def _mostrar_todos_populares(self):
        from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QLabel)
        dialog = QDialog(self)
        dialog.setWindowTitle('Arquivos Populares - Tech Union Downloads')
        dialog.setMinimumSize(700, 500)
        dialog.setStyleSheet('\n            QDialog {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #f8f9fa, stop: 1 #e9ecef);\n            }\n            QLabel#tituloDialog {\n                font-size: 18px;\n                font-weight: bold;\n                color: white;\n                padding: 15px;\n                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,\n                    stop: 0 #e74c3c, stop: 1 #c0392b);\n                border-radius: 8px;\n                margin-bottom: 10px;\n                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);\n            }\n            QListWidget {\n                border: 2px solid #dee2e6;\n                border-radius: 8px;\n                background-color: white;\n                font-size: 14px;\n                padding: 5px;\n            }\n            QListWidget::item {\n                padding: 12px;\n                border-bottom: 1px solid #e9ecef;\n                background-color: white;\n                border-radius: 4px;\n                margin: 2px;\n            }\n            QListWidget::item:hover {\n                background-color: #ffebee;\n                transform: translateY(-1px);\n                box-shadow: 0 2px 8px rgba(231, 76, 60, 0.2);\n            }\n            QListWidget::item:selected {\n                background-color: #f44336;\n                color: white;\n                box-shadow: 0 3px 10px rgba(244, 67, 54, 0.3);\n            }\n            QPushButton {\n                padding: 10px 20px;\n                border-radius: 6px;\n                font-weight: bold;\n                font-size: 14px;\n                border: none;\n            }\n            QPushButton#btnBaixar {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #2ecc71, stop: 1 #27ae60);\n                color: white;\n            }\n            QPushButton#btnBaixar:hover {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #58d68d, stop: 1 #2ecc71);\n                transform: translateY(-2px);\n            }\n            QPushButton#btnFechar {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #95a5a6, stop: 1 #7f8c8d);\n                color: white;\n            }\n            QPushButton#btnFechar:hover {\n                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n                    stop: 0 #bdc3c7, stop: 1 #95a5a6);\n            }\n        ')
        layout = QVBoxLayout(dialog)
        titulo = QLabel('Arquivos Populares do Servidor')
        titulo.setObjectName('tituloDialog')
        layout.addWidget(titulo)
        lista = QListWidget()
        if self.arquivos_populares:
            for arquivo in self.arquivos_populares:
                titulo_arquivo = arquivo.get('titulo', 'Arquivo')
                marca = arquivo.get('marca', 'N/A')
                modelo = arquivo.get('modelo', arquivo.get('versao', ''))
                categoria = arquivo.get('categoria', '')
                downloads = arquivo.get('quantidade_downloads', 0)
                tipo = 'Premium' if arquivo.get('tipo_arquivo') == 'pago' else 'Gratuito'
                texto_item = f'{titulo_arquivo}\n'
                texto_item += f'   {marca} {modelo}\n'
                if categoria:
                    texto_item += f'   Categoria: {categoria}\n'
                texto_item += f'   {downloads} downloads | {tipo} | Popular'
                item = QListWidgetItem(texto_item)
                item.setData(Qt.UserRole, arquivo)
                lista.addItem(item)
        else:
            item = QListWidgetItem('Nenhum arquivo popular disponivel no momento')
            lista.addItem(item)
        layout.addWidget(lista)
        botoes_layout = QHBoxLayout()
        if self.arquivos_populares:
            btn_detalhes = QPushButton('Ver Detalhes')
            btn_detalhes.setObjectName('btnBaixar')
            btn_detalhes.clicked.connect((lambda: self._ver_detalhes_arquivo_dialog(lista, dialog)))
            botoes_layout.addWidget(btn_detalhes)
        btn_fechar = QPushButton('Fechar')
        btn_fechar.setObjectName('btnFechar')
        btn_fechar.clicked.connect(dialog.close)
        botoes_layout.addWidget(btn_fechar)
        layout.addLayout(botoes_layout)
        dialog.exec_()
    def _ver_detalhes_arquivo_dialog(self, lista, dialog):
        item_atual = lista.currentItem()
        if not item_atual:
            QMessageBox.warning(dialog, 'Aviso', 'Selecione um arquivo para ver os detalhes.')
            return
        arquivo = item_atual.data(Qt.UserRole)
        if not arquivo:
            return
        dialog.close()
        self._abrir_detalhes_arquivo(arquivo)
    def _voltar_tela_principal(self):
        try:
            if hasattr(self, 'scroll_timer') and self.scroll_timer.isActive():
                self.scroll_timer.stop()
            self.close()
            if self.parent_window:
                self.parent_window.show()
                self.parent_window.raise_()
                self.parent_window.activateWindow()
                return
        except Exception as e:
            self.logger.error(f'Erro ao voltar para tela principal: {str(e)}')
            self.close()
    def closeEvent(self, event):
        resposta = QMessageBox.question(self, 'Fechar Downloads', 'Deseja fechar a ├írea de downloads?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resposta == QMessageBox.Yes:
            event.accept()
            return
        event.ignore()
    def _mostrar_notificacao_compra(self, arquivo_titulo: str):
        try:
            notificacao = QWidget(self)
            notificacao.setObjectName('notificacaoCompra')
            notificacao.setFixedSize(350, 80)
            parent_rect = self.geometry()
            x = parent_rect.width() - 370
            y = 20
            notificacao.move(x, y)
            layout = QHBoxLayout(notificacao)
            layout.setContentsMargins(15, 10, 15, 10)
            layout.setSpacing(10)
            icon_label = QLabel()
            svg_check = PathManager.get_resource_path('icons_svg/check2-all.svg')
            if svg_check:
                pixmap_ok = self._svg_colorido(svg_check, 24, '#27AE60')
                if not pixmap_ok.isNull():
                    icon_label.setPixmap(pixmap_ok)
            layout.addWidget(icon_label)
            texto_layout = QVBoxLayout()
            titulo_notif = QLabel('Compra Realizada!')
            titulo_notif.setStyleSheet('\n                font-weight: bold;\n                font-size: 14px;\n                color: #27AE60;\n                margin: 0;\n            ')
            texto_layout.addWidget(titulo_notif)
            arquivo_notif = QLabel(f'{arquivo_titulo[:30]}...')
            arquivo_notif.setStyleSheet('\n                font-size: 12px;\n                color: #2C3E50;\n                margin: 0;\n            ')
            texto_layout.addWidget(arquivo_notif)
            layout.addLayout(texto_layout)
            btn_fechar = QPushButton('Ô£û')
            btn_fechar.setFixedSize(25, 25)
            btn_fechar.setStyleSheet('\n                QPushButton {\n                    background: transparent;\n                    border: none;\n                    color: #7F8C8D;\n                    font-weight: bold;\n                }\n                QPushButton:hover {\n                    color: #E74C3C;\n                }\n            ')
            btn_fechar.clicked.connect(notificacao.close)
            layout.addWidget(btn_fechar)
            notificacao.setStyleSheet('\n                QWidget#notificacaoCompra {\n                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                        stop:0 #D5EFDE, stop:1 #B8E6C1);\n                    border: 2px solid #27AE60;\n                    border-radius: 10px;\n                    box-shadow: 0 4px 15px rgba(39, 174, 96, 0.3);\n                }\n            ')
            notificacao.show()
            notificacao.raise_()
            QTimer.singleShot(5000, notificacao.close)
            notificacao.setWindowOpacity(0.0)
            self.notif_animation = QTimer()
            self.notif_opacity = 0.0
            def fade_in():
                self.notif_opacity += 0.1
                notificacao.setWindowOpacity(self.notif_opacity)
                if self.notif_opacity >= 1.0:
                    self.notif_animation.stop()
            self.notif_animation.timeout.connect(fade_in)
            self.notif_animation.start(50)
            return
        except Exception as e:
            self.logger.error(f'Erro ao mostrar notifica├º├úo: {str(e)}')
            self.logger.info(f'Compra realizada: {arquivo_titulo}')
    def _setup_ui_acesso_negado(self):
        self.setWindowTitle('ACESSO NEGADO - TECH UNION SOLUTIONS')
        self.setFixedSize(500, 300)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setAlignment(Qt.AlignCenter)
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignCenter)
        svg_shield = PathManager.get_resource_path('icons_svg/shield-lock.svg')
        if svg_shield:
            pixmap_err = self._svg_colorido(svg_shield, 64, '#E74C3C')
            if not pixmap_err.isNull():
                icon_label.setPixmap(pixmap_err)
            icon_label.setStyleSheet('margin-bottom: 20px;')
        else:
            icon_label.setText('X')
            icon_label.setStyleSheet('font-size: 64px; margin-bottom: 20px; color: #E74C3C; font-weight: bold;')
        main_layout.addWidget(icon_label)
        titulo_label = QLabel('ACESSO NEGADO')
        titulo_label.setAlignment(Qt.AlignCenter)
        titulo_label.setStyleSheet('\n            font-size: 18px;\n            font-weight: bold;\n            color: #E74C3C;\n            margin-bottom: 10px;\n        ')
        main_layout.addWidget(titulo_label)
        mensagem_label = QLabel('Voc├¬ n├úo tem permiss├úo para acessar\no m├│dulo de downloads.')
        mensagem_label.setAlignment(Qt.AlignCenter)
        mensagem_label.setWordWrap(True)
        mensagem_label.setStyleSheet('\n            font-size: 14px;\n            color: #666;\n            margin-bottom: 20px;\n        ')
        main_layout.addWidget(mensagem_label)
        btn_fechar = QPushButton('Fechar')
        btn_fechar.setFixedSize(120, 40)
        btn_fechar.setStyleSheet('\n            QPushButton {\n                background-color: #E74C3C;\n                color: white;\n                border: none;\n                border-radius: 8px;\n                font-size: 14px;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background-color: #C0392B;\n            }\n        ')
        btn_fechar.clicked.connect(self.close)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_fechar)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)
