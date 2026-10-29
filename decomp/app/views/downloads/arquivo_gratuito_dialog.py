'''
RESTORECELL - Di├ílogo de Arquivo Gratuito
Janela para exibir detalhes de arquivos gratuitos com download direto
Autor: Engenheiro Senior RESTORECELL
Data: Janeiro 2025
'''
import logging
import webbrowser
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QFrame, QMessageBox, QScrollArea, QWidget)
from PyQt5.QtCore import (Qt, pyqtSignal, QSize)
from PyQt5.QtGui import (QFont, QPixmap, QIcon)
from app.utils.path_manager import PathManager
class ArquivoGratuitoDialog(QDialog):
    '''Di├ílogo para exibir detalhes de arquivos gratuitos'''
    download_iniciado = pyqtSignal()
    def __init__(self, arquivo_info: dict, parent=None):
        super().__init__(parent)
        self.arquivo_info = arquivo_info
        self.logger = logging.getLogger(__name__)
        self.setWindowTitle('Arquivo Gratuito - Union Solutions')
        self.setModal(True)
        self.resize(600, 500)
        self._setup_ui()
        self._aplicar_estilos()
        self._popular_dados()
    def _setup_ui(self):
        '''Configura a interface do usu├írio'''
        layout_principal = QVBoxLayout()
        layout_principal.setSpacing(15)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        self._criar_header(layout_principal)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameStyle(QFrame.NoFrame)
        conteudo_widget = QWidget()
        conteudo_layout = QVBoxLayout(conteudo_widget)
        self._criar_info_basica(conteudo_layout)
        self._criar_secao_solucao(conteudo_layout)
        self._criar_secao_descricao(conteudo_layout)
        scroll_area.setWidget(conteudo_widget)
        layout_principal.addWidget(scroll_area)
        self._criar_botoes_acao(layout_principal)
        self.setLayout(layout_principal)
    def _criar_header(self, parent_layout):
        '''Cria o cabe├ºalho da janela'''
        header_frame = QFrame()
        header_frame.setObjectName('headerFrame')
        header_frame.setFixedHeight(80)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 15, 20, 15)
        icon_label = QLabel()
        icon_label.setFixedSize(50, 50)
        icon_label.setStyleSheet('\n            QLabel {\n                background-color: white;\n                border-radius: 25px;\n                border: 3px solid #27ae60;\n            }\n        ')
        svg_download = PathManager.get_resource_path('icons_svg/cloud-arrow-down.svg')
        if svg_download:
            icon_label.setPixmap(QIcon(svg_download).pixmap(QSize(28, 28)))
        icon_label.setAlignment(Qt.AlignCenter)
        texto_layout = QVBoxLayout()
        titulo_label = QLabel('Arquivo Gratuito')
        titulo_label.setObjectName('tituloHeader')
        titulo_label.setFont(QFont('Arial', 18, QFont.Bold))
        subtitulo_label = QLabel('Download dispon├¡vel imediatamente')
        subtitulo_label.setObjectName('subtituloHeader')
        subtitulo_label.setFont(QFont('Arial', 12))
        texto_layout.addWidget(titulo_label)
        texto_layout.addWidget(subtitulo_label)
        texto_layout.addStretch()
        header_layout.addWidget(icon_label)
        header_layout.addLayout(texto_layout)
        header_layout.addStretch()
        parent_layout.addWidget(header_frame)
    def _criar_info_basica(self, parent_layout):
        '''Cria se├º├úo com informa├º├Áes b├ísicas'''
        info_frame = QFrame()
        info_frame.setObjectName('infoFrame')
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(15, 15, 15, 15)
        titulo_label = QLabel()
        titulo_label.setObjectName('tituloArquivo')
        titulo_label.setFont(QFont('Arial', 14, QFont.Bold))
        titulo_label.setWordWrap(True)
        info_layout.addWidget(titulo_label)
        self.titulo_label = titulo_label
        marca_label = QLabel()
        marca_label.setObjectName('marcaModelo')
        marca_label.setFont(QFont('Arial', 12))
        info_layout.addWidget(marca_label)
        self.marca_label = marca_label
        categoria_label = QLabel()
        categoria_label.setObjectName('categoria')
        categoria_label.setFont(QFont('Arial', 11))
        info_layout.addWidget(categoria_label)
        self.categoria_label = categoria_label
        parent_layout.addWidget(info_frame)
    def _criar_secao_solucao(self, parent_layout):
        '''Cria se├º├úo de solu├º├úo'''
        solucao_frame = QFrame()
        solucao_frame.setObjectName('secaoFrame')
        solucao_layout = QVBoxLayout(solucao_frame)
        solucao_layout.setContentsMargins(15, 15, 15, 15)
        titulo_secao = QLabel('Solucao')
        titulo_secao.setObjectName('tituloSecao')
        titulo_secao.setFont(QFont('Arial', 13, QFont.Bold))
        solucao_layout.addWidget(titulo_secao)
        solucao_text = QTextEdit()
        solucao_text.setObjectName('solucaoText')
        solucao_text.setReadOnly(True)
        solucao_text.setMaximumHeight(100)
        solucao_text.setFont(QFont('Arial', 11))
        solucao_layout.addWidget(solucao_text)
        self.solucao_text = solucao_text
        parent_layout.addWidget(solucao_frame)
    def _criar_secao_descricao(self, parent_layout):
        '''Cria se├º├úo de descri├º├úo'''
        descricao_frame = QFrame()
        descricao_frame.setObjectName('secaoFrame')
        descricao_layout = QVBoxLayout(descricao_frame)
        descricao_layout.setContentsMargins(15, 15, 15, 15)
        titulo_secao = QLabel('Descricao')
        titulo_secao.setObjectName('tituloSecao')
        titulo_secao.setFont(QFont('Arial', 13, QFont.Bold))
        descricao_layout.addWidget(titulo_secao)
        descricao_text = QTextEdit()
        descricao_text.setObjectName('descricaoText')
        descricao_text.setReadOnly(True)
        descricao_text.setMaximumHeight(120)
        descricao_text.setFont(QFont('Arial', 11))
        descricao_layout.addWidget(descricao_text)
        self.descricao_text = descricao_text
        parent_layout.addWidget(descricao_frame)
    def _criar_botoes_acao(self, parent_layout):
        '''Cria bot├Áes de a├º├úo'''
        botoes_frame = QFrame()
        botoes_layout = QHBoxLayout(botoes_frame)
        botoes_layout.setContentsMargins(0, 15, 0, 0)
        btn_cancelar = QPushButton('Cancelar')
        btn_cancelar.setObjectName('btnCancelar')
        btn_cancelar.setMinimumSize(100, 38)
        btn_cancelar.setMaximumHeight(42)
        btn_cancelar.clicked.connect(self.reject)
        btn_download = QPushButton('Download Gratuito')
        btn_download.setObjectName('btnDownload')
        btn_download.setMinimumSize(170, 38)
        btn_download.setMaximumHeight(42)
        btn_download.setFont(QFont('Arial', 11, QFont.Bold))
        btn_download.clicked.connect(self._fazer_download)
        self.btn_download = btn_download
        botoes_layout.addStretch()
        botoes_layout.addWidget(btn_cancelar)
        botoes_layout.addWidget(btn_download)
        parent_layout.addWidget(botoes_frame)
    def _popular_dados(self):
        '''Popula os campos com dados do arquivo'''
        try:
            titulo = self.arquivo_info.get('titulo', 'T├¡tulo n├úo dispon├¡vel')
            self.titulo_label.setText(titulo)
            marca = self.arquivo_info.get('marca', 'N/A')
            modelo = self.arquivo_info.get('modelo', 'N/A')
            self.marca_label.setText(f'{marca} {modelo}')
            categoria = self.arquivo_info.get('categoria', 'N/A')
            self.categoria_label.setText(f'Categoria: {categoria}')
            solucao = self.arquivo_info.get('solucao', 'Solu├º├úo n├úo informada')
            self.solucao_text.setPlainText(solucao)
            descricao = self.arquivo_info.get('descricao', 'Descri├º├úo n├úo dispon├¡vel')
            self.descricao_text.setPlainText(descricao)
            return
        except Exception as e:
            self.logger.error(f'Erro ao popular dados: {str(e)}')
    def _fazer_download(self):
        '''Processa o download do arquivo'''
        try:
            link_download = self.arquivo_info.get('link_download')
            if not link_download:
                QMessageBox.warning(self, 'Erro', 'Link de download n├úo dispon├¡vel.\n\nVerifique se o arquivo ainda est├í ativo.')
                return
            resposta = QMessageBox.question(self, 'Confirmar Download', f'Iniciar download do arquivo?\n\n{self.arquivo_info.get('titulo', '')}\nO arquivo sera aberto no seu navegador', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if resposta == QMessageBox.Yes:
                webbrowser.open(link_download)
                self.download_iniciado.emit()
                QMessageBox.information(self, 'Download Iniciado', 'Download iniciado no seu navegador!\n\nO arquivo sera baixado automaticamente.')
                self.accept()
                return
        except Exception as e:
            self.logger.error(f'Erro no download: {str(e)}')
            QMessageBox.critical(self, 'Erro', f'Erro ao processar download:\n\n{str(e)}')
    def _aplicar_estilos(self):
        '''Aplica estilos CSS ├á janela'''
        self.setStyleSheet('\n            QDialog {\n                background-color: #f8f9fa;\n            }\n            \n            QFrame#headerFrame {\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, \n                    stop:0 #27ae60, stop:1 #2ecc71);\n                border-radius: 10px;\n            }\n            \n            QLabel#tituloHeader {\n                color: white;\n                font-weight: bold;\n            }\n            \n            QLabel#subtituloHeader {\n                color: #ecf0f1;\n            }\n            \n            QFrame#infoFrame, QFrame#secaoFrame {\n                background-color: white;\n                border: 1px solid #ddd;\n                border-radius: 8px;\n            }\n            \n            QLabel#tituloArquivo {\n                color: #2c3e50;\n                padding: 5px 0;\n            }\n            \n            QLabel#marcaModelo {\n                color: #27ae60;\n                font-weight: bold;\n            }\n            \n            QLabel#categoria {\n                color: #7f8c8d;\n            }\n            \n            QLabel#tituloSecao {\n                color: #2c3e50;\n                padding: 5px 0;\n                border-bottom: 2px solid #27ae60;\n                margin-bottom: 10px;\n            }\n            \n            QTextEdit#solucaoText, QTextEdit#descricaoText {\n                background-color: #f8f9fa;\n                border: 1px solid #ddd;\n                border-radius: 5px;\n                padding: 8px;\n                font-family: Arial;\n            }\n            \n            QPushButton#btnDownload {\n                background-color: #27ae60;\n                color: white;\n                border: none;\n                border-radius: 20px;\n                font-weight: bold;\n            }\n            \n            QPushButton#btnDownload:hover {\n                background-color: #229954;\n            }\n            \n            QPushButton#btnDownload:pressed {\n                background-color: #1e8449;\n            }\n            \n            QPushButton#btnCancelar {\n                background-color: #95a5a6;\n                color: white;\n                border: none;\n                border-radius: 20px;\n            }\n            \n            QPushButton#btnCancelar:hover {\n                background-color: #7f8c8d;\n            }\n            \n            QScrollArea {\n                border: none;\n                background-color: transparent;\n            }\n        ')
