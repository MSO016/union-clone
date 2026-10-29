'''
RESTORECELL - Janela de Categorias por Marca
Lista categorias dispon├¡veis para uma marca especifica
'''
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QFrame, QScrollArea, QMessageBox)
from PyQt5.QtCore import (Qt, QTimer, QThread, pyqtSignal)
from PyQt5.QtGui import (QFont, QPixmap, QIcon, QCursor)
from app.utils.arquivos_manager import ArquivosManager
from app.database.downloads_cache import DownloadsCache
import logging
class CategoriasWindow(QMainWindow):
    '''
    Janela que exibe categorias dispon├¡veis para uma marca espec├¡fica
    '''
    def __init__(self, marca: str, email_login: str, parent=None):
        super().__init__(parent)
        self.marca = marca
        self.email_login = email_login
        self.parent_window = parent
        self.logger = logging.getLogger(__name__)
        self.arquivos_manager = ArquivosManager()
        self.cache = DownloadsCache()
        self.categorias_disponiveis = []
        self._setup_ui()
        self._aplicar_estilos()
        self._carregar_categorias()
    def _setup_ui(self):
        '''Configura interface principal'''
        self.setWindowTitle(f'{self.marca} - Categorias')
        self.setMinimumSize(1000, 700)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        self._criar_header(main_layout)
        self._criar_area_conteudo(main_layout)
        self._criar_botao_voltar(main_layout)
    def _criar_header(self, parent_layout):
        '''Cria header com t├¡tulo e navega├º├úo'''
        header_widget = QFrame()
        header_widget.setObjectName('headerFrame')
        header_widget.setFixedHeight(80)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(15, 15, 15, 15)
        nav_label = QLabel(f'Downloads > {self.marca}')
        nav_label.setObjectName('navLabel')
        nav_label.setFont(QFont('Arial', 14))
        header_layout.addWidget(nav_label)
        header_layout.addStretch()
        titulo_label = QLabel(f'Categorias - {self.marca}')
        titulo_label.setObjectName('tituloHeader')
        titulo_label.setFont(QFont('Arial', 20, QFont.Bold))
        header_layout.addWidget(titulo_label)
        parent_layout.addWidget(header_widget)
    def _criar_area_conteudo(self, parent_layout):
        '''Cria ├írea de conte├║do com scroll'''
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setSpacing(20)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.categorias_frame = QFrame()
        self.categorias_frame.setObjectName('categoriasFrame')
        self.categorias_layout = QGridLayout(self.categorias_frame)
        self.categorias_layout.setSpacing(20)
        self.content_layout.addWidget(self.categorias_frame)
        self.content_layout.addStretch()
        scroll_area.setWidget(content_widget)
        parent_layout.addWidget(scroll_area)
    def _criar_botao_voltar(self, parent_layout):
        '''Cria bot├úo para voltar'''
        botao_frame = QFrame()
        botao_layout = QHBoxLayout(botao_frame)
        btn_voltar = QPushButton('Voltar')
        btn_voltar.setObjectName('btnVoltar')
        btn_voltar.setFixedSize(120, 40)
        btn_voltar.clicked.connect(self.close)
        botao_layout.addWidget(btn_voltar)
        botao_layout.addStretch()
        parent_layout.addWidget(botao_frame)
    def _carregar_categorias(self):
        '''Carrega categorias da marca do cache e MySQL'''
        try:
            cache_key = f'categorias_{self.marca}'
            categorias_cache = self.cache.obter_categorias_cache(self.marca)
            if categorias_cache:
                self.categorias_disponiveis = categorias_cache
                self._popular_grid_categorias()
                QTimer.singleShot(100, self._atualizar_categorias_mysql)
                return
            self._atualizar_categorias_mysql()
            return
        except Exception as e:
            self.logger.error(f'Erro carregar categorias: {str(e)}')
            QMessageBox.warning(self, 'Erro', 'Erro ao carregar categorias.')
    def _atualizar_categorias_mysql(self):
        '''Atualiza categorias do MySQL'''
        try:
            categorias = self.arquivos_manager.obter_categorias_por_marca(self.marca)
            if categorias is None:
                self._mostrar_erro_conexao()
                return
            if len(categorias) == 0:
                self._mostrar_sem_categorias()
                return
            self.categorias_disponiveis = categorias
            self._popular_grid_categorias()
            self.cache.salvar_categorias_cache(self.marca, categorias)
            return
        except ConnectionError as e:
            self.logger.error(f'Erro de conexao com servidor: {str(e)}')
            self._mostrar_erro_conexao()
        except Exception as e:
            self.logger.error(f'Erro ao processar categorias: {str(e)}')
            self._mostrar_sem_categorias()
    def _popular_grid_categorias(self):
        '''Popula grid com categorias dispon├¡veis'''
        self._limpar_layout(self.categorias_layout)
        if not self.categorias_disponiveis:
            self._mostrar_sem_categorias()
            return
        linha, coluna = 0, 0
        max_colunas = 3
        for categoria_info in self.categorias_disponiveis:
            card = self._criar_card_categoria(categoria_info)
            self.categorias_layout.addWidget(card, linha, coluna)
            coluna += 1
            if coluna >= max_colunas:
                coluna = 0
                linha += 1
    def _criar_card_categoria(self, categoria_info):
        '''Cria card para uma categoria'''
        card = QFrame()
        card.setObjectName('cardCategoria')
        card.setFixedSize(280, 120)
        card.setCursor(QCursor(Qt.PointingHandCursor))
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)
        nome_label = QLabel(categoria_info['categoria'])
        nome_label.setObjectName('nomeCategoria')
        nome_label.setFont(QFont('Arial', 14, QFont.Bold))
        nome_label.setAlignment(Qt.AlignCenter)
        nome_label.setWordWrap(True)
        layout.addWidget(nome_label)
        total = categoria_info.get('total_arquivos', 0)
        contador_label = QLabel(f'{total} arquivo{'s' if total != 1 else ''}')
        contador_label.setObjectName('contadorArquivos')
        contador_label.setFont(QFont('Arial', 11))
        contador_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(contador_label)
        categoria_nome = categoria_info['categoria']
        card.mousePressEvent = lambda event, cat=categoria_nome: self._abrir_arquivos(cat)
        return card
    def _abrir_arquivos(self, categoria):
        '''Abre janela de arquivos para categoria espec├¡fica'''
        try:
            from app.views.downloads.arquivos_lista_window import ArquivosListaWindow
            self.arquivos_window = ArquivosListaWindow(self.marca, categoria, self.email_login, self)
            self.arquivos_window.setWindowFlags(Qt.Window)
            self.arquivos_window.showMaximized()
            return
        except Exception as e:
            self.logger.error(f'Erro abrir arquivos: {str(e)}')
            QMessageBox.critical(self, 'Erro', f'Erro ao abrir arquivos: {str(e)}')
    def _mostrar_sem_categorias(self):
        '''Mostra mensagem quando n├úo h├í categorias'''
        msg_frame = QFrame()
        msg_frame.setObjectName('semCategoriasFrame')
        msg_layout = QVBoxLayout(msg_frame)
        msg_layout.setAlignment(Qt.AlignCenter)
        texto_label = QLabel(f'Nenhuma categoria encontrada para {self.marca}')
        texto_label.setFont(QFont('Arial', 14))
        texto_label.setAlignment(Qt.AlignCenter)
        msg_layout.addWidget(texto_label)
        self.categorias_layout.addWidget(msg_frame, 0, 0, 1, 3)
    def _mostrar_erro_conexao(self):
        '''Mostra mensagem de erro de conex├úo'''
        msg_frame = QFrame()
        msg_frame.setObjectName('erroConexaoFrame')
        msg_layout = QVBoxLayout(msg_frame)
        msg_layout.setAlignment(Qt.AlignCenter)
        texto_label = QLabel('Erro ao conectar com servidor')
        texto_label.setFont(QFont('Arial', 14))
        texto_label.setAlignment(Qt.AlignCenter)
        msg_layout.addWidget(texto_label)
        self.categorias_layout.addWidget(msg_frame, 0, 0, 1, 3)
    def _limpar_layout(self, layout):
        '''Limpa todos os widgets de um layout'''
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    def _aplicar_estilos(self):
        '''Aplica estilos CSS ├á interface'''
        self.setStyleSheet('\n            /* Header */\n            #headerFrame {\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,\n                    stop:0 #2c3e50, stop:1 #3498db);\n                border-radius: 10px;\n            }\n            \n            #navLabel {\n                color: #ecf0f1;\n                font-weight: bold;\n            }\n            \n            #tituloHeader {\n                color: white;\n                font-weight: bold;\n            }\n            \n            /* Cards de categoria */\n            #cardCategoria {\n                background: white;\n                border: 2px solid #bdc3c7;\n                border-radius: 12px;\n                padding: 15px;\n            }\n            \n            #cardCategoria:hover {\n                border-color: #3498db;\n                background: #f8f9fa;\n            }\n            \n            #nomeCategoria {\n                color: #2c3e50;\n                font-weight: bold;\n            }\n            \n            #contadorArquivos {\n                color: #7f8c8d;\n            }\n            \n            /* Bot├úo voltar */\n            #btnVoltar {\n                background: #e74c3c;\n                color: white;\n                border: none;\n                border-radius: 8px;\n                font-weight: bold;\n                font-size: 14px;\n            }\n            \n            #btnVoltar:hover {\n                background: #c0392b;\n            }\n            \n            /* Mensagens */\n            #semCategoriasFrame, #erroConexaoFrame {\n                background: #f8f9fa;\n                border: 2px dashed #bdc3c7;\n                border-radius: 12px;\n                padding: 40px;\n            }\n        ')
    def closeEvent(self, event):
        '''Evento de fechamento da janela'''
        try:
            if hasattr(self, 'cache'):
                pass
        except Exception as e:
            self.logger.error(f'Erro ao fechar categorias: {str(e)}')
        event.accept()
