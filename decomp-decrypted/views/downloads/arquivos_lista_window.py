from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QFrame, QScrollArea, QMessageBox, QSizePolicy)
from PyQt5.QtCore import (Qt, QTimer, QSize)
from PyQt5.QtGui import (QFont, QPixmap, QIcon, QCursor, QResizeEvent)
from app.utils.arquivos_manager import ArquivosManager
from app.database.downloads_cache import DownloadsCache
import logging
class ArquivosListaWindow(QMainWindow):
    def __init__(self, marca: str, categoria: str, email_login: str, parent=None):
        super().__init__(parent)
        self.marca = marca
        self.categoria = categoria
        self.email_login = email_login
        self.parent_window = parent
        self.logger = logging.getLogger(__name__)
        self.arquivos_manager = ArquivosManager()
        self.cache = DownloadsCache()
        self.arquivos_disponiveis = []
        self.itens_por_pagina = 15
        self.pagina_atual = 1
        self.total_paginas = 1
        self.arquivos_filtrados = []
        self._setup_ui()
        self._aplicar_estilos()
        self._carregar_arquivos()
        self._current_width = self.width()
        self._setup_responsive_behavior()
    def _setup_ui(self):
        self.setWindowTitle(f'{self.marca} - {self.categoria}')
        self.setMinimumSize(800, 600)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        self._criar_header(main_layout)
        self._criar_area_conteudo(main_layout)
        self._criar_botao_voltar(main_layout)
    def _criar_header(self, parent_layout):
        header_widget = QFrame()
        header_widget.setObjectName('headerFrame')
        header_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(15, 15, 15, 15)
        header_layout.setSpacing(10)
        self._criar_linha_titulo(header_layout)
        self._criar_barra_filtros(header_layout)
        parent_layout.addWidget(header_widget)
    def _criar_linha_titulo(self, parent_layout):
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setSpacing(8)
        nav_label = QLabel(f'Downloads > {self.marca} > {self.categoria}')
        nav_label.setObjectName('navLabel')
        nav_label.setFont(QFont('Arial', 11))
        nav_label.setWordWrap(True)
        top_layout.addWidget(nav_label)
        titulo_label = QLabel(f'Arquivos - {self.categoria}')
        titulo_label.setObjectName('tituloHeader')
        titulo_label.setFont(QFont('Arial', 16, QFont.Bold))
        titulo_label.setWordWrap(True)
        titulo_label.setAlignment(Qt.AlignCenter)
        top_layout.addWidget(titulo_label)
        parent_layout.addWidget(top_widget)
    def _criar_barra_filtros(self, parent_layout):
        from PyQt5.QtWidgets import QLineEdit, QComboBox
        filtros_widget = QWidget()
        filtros_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_filtros_layout = QVBoxLayout(filtros_widget)
        main_filtros_layout.setSpacing(10)
        main_filtros_layout.setContentsMargins(0, 0, 0, 0)
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)
        search_frame = QFrame()
        search_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        search_inner_layout = QHBoxLayout(search_frame)
        search_inner_layout.setContentsMargins(0, 0, 0, 0)
        search_inner_layout.setSpacing(5)
        search_icon = QLabel('')
        search_icon.setFont(QFont('Arial', 12))
        search_inner_layout.addWidget(search_icon)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Pesquisar arquivos...')
        self.search_input.setObjectName('searchInput')
        self.search_input.setFixedHeight(32)
        self.search_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.search_input.textChanged.connect(self._on_search_changed)
        search_inner_layout.addWidget(self.search_input)
        search_layout.addWidget(search_frame)
        main_filtros_layout.addLayout(search_layout)
        filtros_layout = QHBoxLayout()
        filtros_layout.setSpacing(10)
        order_container = QWidget()
        order_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        order_layout = QHBoxLayout(order_container)
        order_layout.setContentsMargins(0, 0, 0, 0)
        order_layout.setSpacing(5)
        order_label = QLabel('')
        order_label.setFont(QFont('Arial', 10))
        order_layout.addWidget(order_label)
        self.order_combo = QComboBox()
        self.order_combo.setObjectName('orderCombo')
        self.order_combo.setFixedHeight(32)
        self.order_combo.setMinimumWidth(120)
        self.order_combo.addItems(['Mais Recentes', 'Mais Populares', 'A-Z (Nome)', 'Menor Pre├ºo', 'Maior Pre├ºo'])
        self.order_combo.currentTextChanged.connect(self._on_order_changed)
        order_layout.addWidget(self.order_combo)
        filtros_layout.addWidget(order_container)
        type_container = QWidget()
        type_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        type_layout = QHBoxLayout(type_container)
        type_layout.setContentsMargins(0, 0, 0, 0)
        type_layout.setSpacing(5)
        type_label = QLabel('')
        type_label.setFont(QFont('Arial', 10))
        type_layout.addWidget(type_label)
        self.type_combo = QComboBox()
        self.type_combo.setObjectName('typeCombo')
        self.type_combo.setFixedHeight(32)
        self.type_combo.setMinimumWidth(100)
        self.type_combo.addItems(['Todos', 'Gratuitos', 'Pagos'])
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        type_layout.addWidget(self.type_combo)
        filtros_layout.addWidget(type_container)
        filtros_layout.addStretch()
        self.results_label = QLabel('0 arquivos')
        self.results_label.setObjectName('resultsLabel')
        self.results_label.setFont(QFont('Arial', 10))
        self.results_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        filtros_layout.addWidget(self.results_label)
        main_filtros_layout.addLayout(filtros_layout)
        parent_layout.addWidget(filtros_widget)
        self.arquivos_originais = []
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._aplicar_filtros)
    def _setup_responsive_behavior(self):
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self._ajustar_layout_responsivo)
    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        if hasattr(self, 'resize_timer'):
            self.resize_timer.stop()
            self.resize_timer.start(150)
    def _ajustar_layout_responsivo(self):
        current_width = self.width()
        if current_width < 900:
            self._aplicar_layout_compacto()
        elif current_width < 1200:
            self._aplicar_layout_medio()
        else:
            self._aplicar_layout_expandido()
        self._current_width = current_width
    def _aplicar_layout_compacto(self):
        if hasattr(self, 'search_input'):
            self.search_input.setMinimumWidth(150)
            self.search_input.setPlaceholderText('Pesquisar...')
        if hasattr(self, 'order_combo'):
            self.order_combo.setMinimumWidth(90)
        if hasattr(self, 'type_combo'):
            self.type_combo.setMinimumWidth(80)
    def _aplicar_layout_medio(self):
        if hasattr(self, 'search_input'):
            self.search_input.setMinimumWidth(200)
            self.search_input.setPlaceholderText('Pesquisar arquivos...')
        if hasattr(self, 'order_combo'):
            self.order_combo.setMinimumWidth(120)
        if hasattr(self, 'type_combo'):
            self.type_combo.setMinimumWidth(100)
    def _aplicar_layout_expandido(self):
        if hasattr(self, 'search_input'):
            self.search_input.setMinimumWidth(300)
            self.search_input.setPlaceholderText('Pesquisar arquivos dispon├¡veis...')
        if hasattr(self, 'order_combo'):
            self.order_combo.setMinimumWidth(150)
        if hasattr(self, 'type_combo'):
            self.type_combo.setMinimumWidth(120)
    def _criar_area_conteudo(self, parent_layout):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setSpacing(15)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.arquivos_frame = QFrame()
        self.arquivos_frame.setObjectName('arquivosFrame')
        self.arquivos_layout = QVBoxLayout(self.arquivos_frame)
        self.arquivos_layout.setSpacing(15)
        self.content_layout.addWidget(self.arquivos_frame)
        self.content_layout.addStretch()
        scroll_area.setWidget(content_widget)
        parent_layout.addWidget(scroll_area)
        self._criar_controles_paginacao(parent_layout)
    def _criar_controles_paginacao(self, parent_layout):
        paginacao_frame = QFrame()
        paginacao_frame.setObjectName('paginacaoFrame')
        paginacao_layout = QHBoxLayout(paginacao_frame)
        paginacao_layout.setContentsMargins(15, 10, 15, 10)
        paginacao_layout.setSpacing(10)
        self.btn_primeira = QPushButton('Primeira')
        self.btn_primeira.setObjectName('btnPaginacao')
        self.btn_primeira.clicked.connect((lambda: self._ir_para_pagina(1)))
        self.btn_anterior = QPushButton('Anterior')
        self.btn_anterior.setObjectName('btnPaginacao')
        self.btn_anterior.clicked.connect(self._pagina_anterior)
        self.label_pagina = QLabel('P├ígina 1 de 1')
        self.label_pagina.setObjectName('labelPagina')
        self.label_pagina.setAlignment(Qt.AlignCenter)
        self.label_pagina.setFont(QFont('Arial', 12, QFont.Bold))
        self.btn_proxima = QPushButton('Proxima')
        self.btn_proxima.setObjectName('btnPaginacao')
        self.btn_proxima.clicked.connect(self._proxima_pagina)
        self.btn_ultima = QPushButton('Ultima')
        self.btn_ultima.setObjectName('btnPaginacao')
        self.btn_ultima.clicked.connect((lambda: self._ir_para_pagina(self.total_paginas)))
        paginacao_layout.addWidget(self.btn_primeira)
        paginacao_layout.addWidget(self.btn_anterior)
        paginacao_layout.addStretch()
        paginacao_layout.addWidget(self.label_pagina)
        paginacao_layout.addStretch()
        paginacao_layout.addWidget(self.btn_proxima)
        paginacao_layout.addWidget(self.btn_ultima)
        parent_layout.addWidget(paginacao_frame)
    def _criar_botao_voltar(self, parent_layout):
        btn_voltar = QPushButton('ÔåÉ Voltar')
        btn_voltar.setObjectName('btnVoltar')
        btn_voltar.clicked.connect(self.close)
        btn_voltar.setStyleSheet('\n            QPushButton {\n                background: #e74c3c;\n                color: white;\n                border: none;\n                border-radius: 8px;\n                font-weight: bold;\n                font-size: 14px;\n                padding: 10px 20px;\n            }\n            QPushButton:hover {\n                background: #c0392b;\n            }\n        ')
        parent_layout.addWidget(btn_voltar)
    def _carregar_arquivos(self):
        try:
            cache_key = f'arquivos_{self.marca}_{self.categoria}'
            arquivos_cache = self.cache.obter_arquivos_cache(self.marca, self.categoria)
            if arquivos_cache:
                self.arquivos_originais = arquivos_cache
                self.arquivos_disponiveis = arquivos_cache
                self._popular_lista_arquivos()
                QTimer.singleShot(100, self._atualizar_arquivos_mysql)
                return
            self._atualizar_arquivos_mysql()
            return
        except Exception as e:
            self.logger.error(f'Erro carregar arquivos: {str(e)}')
            QMessageBox.warning(self, 'Erro', 'Erro ao carregar arquivos.')
    def _atualizar_arquivos_mysql(self):
        try:
            arquivos = self.arquivos_manager.obter_arquivos_por_categoria(self.marca, self.categoria, limit=100)
            if arquivos is None:
                self._mostrar_erro_conexao()
                return
            if len(arquivos) == 0:
                self._mostrar_sem_arquivos()
                return
            self.arquivos_originais = arquivos
            self.arquivos_disponiveis = arquivos
            self._popular_lista_arquivos()
        except ConnectionError as e:
            self.logger.error(f'Erro de conexao com servidor: {str(e)}')
            self._mostrar_erro_conexao()
        except Exception as e:
            self.logger.error(f'Erro ao processar arquivos: {str(e)}')
            self._mostrar_sem_arquivos()
        try:
            self.cache.salvar_arquivos_cache(self.marca, self.categoria, arquivos)
            return
        except Exception as cache_error:
            self.logger.warning(f'Falha ao salvar cache (n├úo cr├¡tico): {str(cache_error)}')
    def _popular_lista_arquivos(self):
        self._limpar_layout(self.arquivos_layout)
        if not self.arquivos_disponiveis:
            self._mostrar_sem_arquivos()
            self._atualizar_controles_paginacao()
            return
        self.arquivos_filtrados = self.arquivos_disponiveis.copy()
        self._calcular_paginacao()
        inicio = (self.pagina_atual - 1) * self.itens_por_pagina
        fim = inicio + self.itens_por_pagina
        arquivos_pagina = self.arquivos_filtrados[inicio:fim]
        self._atualizar_contador_resultados(len(self.arquivos_filtrados))
        for arquivo_info in arquivos_pagina:
            card = self._criar_card_arquivo(arquivo_info)
            self.arquivos_layout.addWidget(card)
        self._atualizar_controles_paginacao()
    def _calcular_paginacao(self):
        total_itens = len(self.arquivos_filtrados)
        self.total_paginas = max(1, (total_itens + self.itens_por_pagina - 1) // self.itens_por_pagina)
        if self.pagina_atual > self.total_paginas:
            self.pagina_atual = 1
    def _atualizar_controles_paginacao(self):
        self.label_pagina.setText(f'P├ígina {self.pagina_atual} de {self.total_paginas}')
        tem_arquivos = len(self.arquivos_filtrados) > 0
        self.btn_primeira.setEnabled(tem_arquivos and self.pagina_atual > 1)
        self.btn_anterior.setEnabled(tem_arquivos and self.pagina_atual > 1)
        self.btn_proxima.setEnabled(tem_arquivos and self.pagina_atual < self.total_paginas)
        self.btn_ultima.setEnabled(tem_arquivos and self.pagina_atual < self.total_paginas)
    def _ir_para_pagina(self, numero_pagina):
        if 1 <= numero_pagina <= self.total_paginas:
            self.pagina_atual = numero_pagina
            self._atualizar_lista_paginada()
    def _pagina_anterior(self):
        if self.pagina_atual > 1:
            self.pagina_atual -= 1
            self._atualizar_lista_paginada()
    def _proxima_pagina(self):
        if self.pagina_atual < self.total_paginas:
            self.pagina_atual += 1
            self._atualizar_lista_paginada()
    def _criar_card_arquivo(self, arquivo_info):
        card = QFrame()
        card.setObjectName('cardArquivo')
        card.setFixedHeight(120)
        card.setCursor(QCursor(Qt.PointingHandCursor))
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(20)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        titulo_label = QLabel(arquivo_info['titulo'])
        titulo_label.setObjectName('tituloArquivo')
        titulo_label.setFont(QFont('Arial', 14, QFont.Bold))
        titulo_label.setWordWrap(True)
        info_layout.addWidget(titulo_label)
        if arquivo_info.get('descricao'):
            desc_label = QLabel(arquivo_info['descricao'][:100] + '...' if len(arquivo_info['descricao']) > 100 else arquivo_info['descricao'])
            desc_label.setObjectName('descricaoArquivo')
            desc_label.setFont(QFont('Arial', 10))
            desc_label.setWordWrap(True)
            info_layout.addWidget(desc_label)
        extras_layout = QHBoxLayout()
        extras_layout.setSpacing(15)
        if arquivo_info.get('tamanho_arquivo'):
            tamanho_label = QLabel(f'{arquivo_info['tamanho_arquivo']}')
            tamanho_label.setObjectName('extraInfo')
            tamanho_label.setFont(QFont('Arial', 9))
            extras_layout.addWidget(tamanho_label)
        downloads = arquivo_info.get('quantidade_downloads', 0)
        download_label = QLabel(f'{downloads} downloads')
        download_label.setObjectName('extraInfo')
        download_label.setFont(QFont('Arial', 9))
        extras_layout.addWidget(download_label)
        extras_layout.addStretch()
        info_layout.addLayout(extras_layout)
        layout.addLayout(info_layout)
        layout.addStretch()
        acao_layout = QVBoxLayout()
        acao_layout.setSpacing(10)
        acao_layout.setAlignment(Qt.AlignCenter)
        tipo_arquivo = arquivo_info.get('tipo_arquivo', 'pago')
        if tipo_arquivo == 'gratuito':
            preco_label = QLabel('GRATUITO')
            preco_label.setObjectName('precoGratuito')
            preco_label.setFont(QFont('Arial', 12, QFont.Bold))
        else:
            preco = float(arquivo_info.get('preco', 0))
            preco_label = QLabel(f'R$ {preco:.2f}')
            preco_label.setObjectName('precoPago')
            preco_label.setFont(QFont('Arial', 12, QFont.Bold))
        preco_label.setAlignment(Qt.AlignCenter)
        acao_layout.addWidget(preco_label)
        if tipo_arquivo == 'gratuito':
            btn_acao = QPushButton('Download')
            btn_acao.setObjectName('btnDownload')
        else:
            status_arquivo = self._verificar_status_arquivo_usuario(arquivo_info.get('id'))
            if status_arquivo == 'liberado':
                btn_acao = QPushButton('Pago')
                btn_acao.setObjectName('btnPago')
            elif status_arquivo == 'pendente':
                btn_acao = QPushButton('Pendente')
                btn_acao.setObjectName('btnPendente')
            else:
                btn_acao = QPushButton('Comprar')
                btn_acao.setObjectName('btnComprar')
        btn_acao.setMinimumSize(90, 35)
        btn_acao.setMaximumHeight(35)
        btn_acao.clicked.connect((lambda: self._processar_click_arquivo(arquivo_info)))
        acao_layout.addWidget(btn_acao)
        layout.addLayout(acao_layout)
        return card
    def _on_search_changed(self):
        self.search_timer.stop()
        self.search_timer.start(500)
    def _on_order_changed(self):
        self._aplicar_filtros()
    def _on_type_changed(self):
        self._aplicar_filtros()
    def _aplicar_filtros(self):
        try:
            if not self.arquivos_originais:
                return
            arquivos_filtrados = self.arquivos_originais.copy()
            termo_pesquisa = self.search_input.text().strip().lower()
            if termo_pesquisa:
                arquivos_filtrados = [arquivo for arquivo in arquivos_filtrados if termo_pesquisa in arquivo.get('titulo', '').lower() if termo_pesquisa in arquivo.get('descricao', '').lower() if termo_pesquisa in arquivo.get('marca', '').lower() if termo_pesquisa in arquivo.get('categoria', '').lower()]
        except Exception as e:
            self.logger.error(f'Erro ao aplicar filtros: {str(e)}')
        tipo_selecionado = self.type_combo.currentText()
        if tipo_selecionado != 'Todos':
            if tipo_selecionado == 'Gratuitos':
                try:
                    arquivos_filtrados = [a for a in arquivos_filtrados if a.get('tipo_arquivo') == 'gratuito']
                    if tipo_selecionado == 'Pagos':
                        arquivos_filtrados = [a for a in arquivos_filtrados if a.get('tipo_arquivo') == 'pago']
                except Exception as e:
                    self.logger.error(f'Erro ao aplicar filtros: {str(e)}')
        ordem_selecionada = self.order_combo.currentText()
        if ordem_selecionada == 'Mais Recentes':
            arquivos_filtrados.sort(key=(lambda x: x.get('data_criacao', '')), reverse=True)
        elif ordem_selecionada == 'Mais Populares':
            arquivos_filtrados.sort(key=(lambda x: x.get('quantidade_downloads', 0)), reverse=True)
        elif ordem_selecionada == 'A-Z (Nome)':
            arquivos_filtrados.sort(key=(lambda x: x.get('titulo', '').lower()))
        elif ordem_selecionada == 'Menor Pre├ºo':
            arquivos_filtrados.sort(key=(lambda x: float(x.get('preco', 0))))
        elif ordem_selecionada == 'Maior Pre├ºo':
            arquivos_filtrados.sort(key=(lambda x: float(x.get('preco', 0))), reverse=True)
        self.arquivos_filtrados = arquivos_filtrados
        self.pagina_atual = 1
        self._calcular_paginacao()
        self._atualizar_lista_paginada()
    def _atualizar_lista_paginada(self):
        self._limpar_layout(self.arquivos_layout)
        if not self.arquivos_filtrados:
            self._mostrar_sem_arquivos()
            self._atualizar_controles_paginacao()
            return
        inicio = (self.pagina_atual - 1) * self.itens_por_pagina
        fim = inicio + self.itens_por_pagina
        arquivos_pagina = self.arquivos_filtrados[inicio:fim]
        self._atualizar_contador_resultados(len(self.arquivos_filtrados))
        for arquivo_info in arquivos_pagina:
            card = self._criar_card_arquivo(arquivo_info)
            self.arquivos_layout.addWidget(card)
        self._atualizar_controles_paginacao()
    def _atualizar_contador_resultados(self, total: int):
        if hasattr(self, 'results_label'):
            if total == 1:
                self.results_label.setText('1 arquivo')
                return
            self.results_label.setText(f'{total} arquivos')
    def _verificar_status_arquivo_usuario(self, arquivo_id: int) -> str:
        try:
            if not arquivo_id:
                return 'nao_comprado'
            liberacao = self.arquivos_manager.verificar_liberacao_usuario(self.email_login, arquivo_id)
            if liberacao:
                return 'liberado'
            compra_pendente = self.arquivos_manager.verificar_compra_pendente(self.email_login, arquivo_id)
            if compra_pendente:
                return 'pendente'
        except Exception as e:
            self.logger.error(f'Erro ao verificar status arquivo {arquivo_id}: {str(e)}')
        return 'nao_comprado'
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
            self.logger.error(f'Erro abrir detalhes: {str(e)}')
            QMessageBox.critical(self, 'Erro', f'Erro ao abrir detalhes: {str(e)}')
    def _mostrar_sem_arquivos(self):
        msg_frame = QFrame()
        msg_frame.setObjectName('semArquivosFrame')
        msg_layout = QVBoxLayout(msg_frame)
        msg_layout.setAlignment(Qt.AlignCenter)
        texto_label = QLabel(f'Nenhum arquivo encontrado em {self.categoria}')
        texto_label.setFont(QFont('Arial', 14))
        texto_label.setAlignment(Qt.AlignCenter)
        msg_layout.addWidget(texto_label)
        self.arquivos_layout.addWidget(msg_frame)
    def _mostrar_erro_conexao(self):
        msg_frame = QFrame()
        msg_frame.setObjectName('erroConexaoFrame')
        msg_layout = QVBoxLayout(msg_frame)
        msg_layout.setAlignment(Qt.AlignCenter)
        texto_label = QLabel('Erro ao conectar com servidor')
        texto_label.setFont(QFont('Arial', 14))
        texto_label.setAlignment(Qt.AlignCenter)
        msg_layout.addWidget(texto_label)
        self.arquivos_layout.addWidget(msg_frame)
    def _limpar_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    def _aplicar_estilos(self):
        self.setStyleSheet('\n            /* Header Responsivo */\n            #headerFrame {\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,\n                    stop:0 #2c3e50, stop:1 #3498db);\n                border-radius: 10px;\n                padding: 10px;\n            }\n            \n            #navLabel {\n                color: #ecf0f1;\n                font-weight: bold;\n                padding: 2px;\n            }\n            \n            #tituloHeader {\n                color: white;\n                font-weight: bold;\n                padding: 5px;\n                text-align: center;\n            }\n            \n            /* Cards de arquivo responsivos */\n            #cardArquivo {\n                background: white;\n                border: 2px solid #bdc3c7;\n                border-radius: 12px;\n                margin: 3px;\n                padding: 10px;\n                min-height: 120px;\n            }\n            \n            #cardArquivo:hover {\n                border-color: #3498db;\n                background: #f8f9fa;\n                transform: translateY(-2px);\n            }\n            \n            #tituloArquivo {\n                color: #2c3e50;\n                font-weight: bold;\n                font-size: 13px;\n                margin-bottom: 5px;\n            }\n            \n            #descricaoArquivo {\n                color: #7f8c8d;\n                font-size: 11px;\n                line-height: 1.3;\n            }\n            \n            #extraInfo {\n                color: #95a5a6;\n                font-size: 10px;\n            }\n            \n            #precoGratuito {\n                color: #27ae60;\n                font-weight: bold;\n                font-size: 12px;\n            }\n            \n            #precoPago {\n                color: #e67e22;\n                font-weight: bold;\n                font-size: 12px;\n            }\n            \n            /* Bot├Áes responsivos */\n            #btnDownload, #btnComprar, #btnPago, #btnPendente {\n                border: none;\n                border-radius: 6px;\n                font-weight: bold;\n                font-size: 11px;\n                padding: 8px 12px;\n                min-width: 80px;\n                min-height: 28px;\n            }\n            \n            #btnDownload {\n                background: #27ae60;\n                color: white;\n            }\n            \n            #btnDownload:hover {\n                background: #229954;\n            }\n            \n            #btnComprar {\n                background: #e67e22;\n                color: white;\n            }\n            \n            #btnComprar:hover {\n                background: #d35400;\n            }\n            \n            #btnPago {\n                background: #27ae60;\n                color: white;\n            }\n            \n            #btnPago:hover {\n                background: #229954;\n            }\n            \n            #btnPendente {\n                background: #f39c12;\n                color: white;\n            }\n            \n            #btnPendente:hover {\n                background: #e67e22;\n            }\n            \n            /* Filtros e pesquisa responsivos */\n            #searchInput {\n                background: white;\n                border: 2px solid #bdc3c7;\n                border-radius: 8px;\n                padding: 6px 10px;\n                font-size: 13px;\n                min-width: 200px;\n            }\n            \n            #searchInput:focus {\n                border-color: #3498db;\n                outline: none;\n            }\n            \n            #orderCombo, #typeCombo {\n                background: white;\n                border: 2px solid #bdc3c7;\n                border-radius: 6px;\n                padding: 6px 12px;\n                font-size: 12px;\n                min-width: 100px;\n                color: #2c3e50;\n                font-weight: 500;\n            }\n            \n            #orderCombo:focus, #typeCombo:focus {\n                border-color: #3498db;\n                outline: none;\n            }\n            \n            #orderCombo:hover, #typeCombo:hover {\n                border-color: #7f8c8d;\n                background: #f8f9fa;\n            }\n            \n            #orderCombo::drop-down, #typeCombo::drop-down {\n                width: 25px;\n                border: none;\n                background: transparent;\n                subcontrol-origin: padding;\n                subcontrol-position: top right;\n            }\n            \n            #orderCombo::down-arrow, #typeCombo::down-arrow {\n                image: none;\n                border-left: 5px solid transparent;\n                border-right: 5px solid transparent;\n                border-top: 5px solid #34495e;\n                width: 0px;\n                height: 0px;\n                margin-right: 5px;\n            }\n            \n            #orderCombo::down-arrow:hover, #typeCombo::down-arrow:hover {\n                border-top-color: #3498db;\n            }\n            \n            #orderCombo QAbstractItemView, #typeCombo QAbstractItemView {\n                background: white;\n                border: 2px solid #bdc3c7;\n                border-radius: 6px;\n                color: #2c3e50;\n                font-size: 12px;\n                padding: 5px;\n                selection-background-color: #3498db;\n                selection-color: white;\n            }\n            \n            #orderCombo QAbstractItemView::item, #typeCombo QAbstractItemView::item {\n                padding: 8px 12px;\n                border: none;\n            }\n            \n            #orderCombo QAbstractItemView::item:hover, #typeCombo QAbstractItemView::item:hover {\n                background: #ecf0f1;\n                color: #2c3e50;\n            }\n            \n            #orderCombo QAbstractItemView::item:selected, #typeCombo QAbstractItemView::item:selected {\n                background: #3498db;\n                color: white;\n            }\n            \n            #filterLabel {\n                color: #34495e;\n                font-weight: bold;\n                font-size: 10px;\n            }\n            \n            #resultsLabel {\n                color: #2c3e50;\n                font-weight: bold;\n                font-size: 13px;\n                padding: 5px;\n                background: rgba(255, 255, 255, 0.9);\n                border-radius: 6px;\n                border: 1px solid #bdc3c7;\n            }\n            \n            /* Bot├úo voltar */\n            #btnVoltar {\n                background: #e74c3c;\n                color: white;\n                border: none;\n                border-radius: 8px;\n                font-weight: bold;\n                font-size: 14px;\n                padding: 10px 20px;\n                min-width: 100px;\n            }\n            \n            #btnVoltar:hover {\n                background: #c0392b;\n            }\n            \n            /* Controles de Pagina├º├úo */\n            #paginacaoFrame {\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,\n                    stop:0 #f8f9fa, stop:1 #ecf0f1);\n                border: 1px solid #bdc3c7;\n                border-radius: 8px;\n                margin: 5px 0;\n            }\n            \n            #btnPaginacao {\n                background: #3498db;\n                color: white;\n                border: none;\n                border-radius: 6px;\n                font-weight: bold;\n                font-size: 12px;\n                padding: 8px 15px;\n                min-width: 90px;\n                min-height: 35px;\n            }\n            \n            #btnPaginacao:hover:enabled {\n                background: #2980b9;\n                transform: translateY(-1px);\n            }\n            \n            #btnPaginacao:disabled {\n                background: #bdc3c7;\n                color: #7f8c8d;\n            }\n            \n            #labelPagina {\n                color: #2c3e50;\n                font-weight: bold;\n                font-size: 14px;\n                background: white;\n                border: 1px solid #bdc3c7;\n                border-radius: 6px;\n                padding: 8px 20px;\n                min-width: 120px;\n            }\n            \n            /* Mensagens */\n            #semArquivosFrame, #erroConexaoFrame {\n                background: #f8f9fa;\n                border: 2px dashed #bdc3c7;\n                border-radius: 12px;\n                padding: 20px;\n                margin: 10px;\n            }\n            \n            /* Scrollbar personalizada */\n            QScrollArea {\n                border: none;\n                background: transparent;\n            }\n            \n            QScrollBar:vertical {\n                background: #f1f2f6;\n                width: 12px;\n                border-radius: 6px;\n            }\n            \n            QScrollBar::handle:vertical {\n                background: #3498db;\n                border-radius: 6px;\n                min-height: 20px;\n            }\n            \n            QScrollBar::handle:vertical:hover {\n                background: #2980b9;\n            }\n            \n            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {\n                border: none;\n                background: none;\n            }\n        ')
    def closeEvent(self, event):
        try:
            if hasattr(self, 'cache'):
                pass
        except Exception as e:
            self.logger.error(f'Erro ao fechar arquivos: {str(e)}')
        event.accept()
