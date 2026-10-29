'''
TECH UNION SOLUTIONS - Pel├¡culas Compat├¡veis
Segue o padr├úo ParceirosWindow: QMainWindow simples, sem QThread.
'''
from pathlib import Path
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTableWidget, QTableWidgetItem, QPushButton, QLabel, QFrame, QApplication, QShortcut, QHeaderView, QAbstractItemView)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import (QColor, QIcon, QKeySequence, QFont)
from app.views.peliculas.peliculas_cache import PeliculasCache
class PeliculasWindow(QMainWindow):
    '''
    Janela de pel├¡culas compat├¡veis.
    Padr├úo id├¬ntico ao ParceirosWindow: QMainWindow + parent + setup_ui no construtor.
    Sincroniza├º├úo feita via QTimer.singleShot (sem QThread).
    '''
    DEBOUNCE_MS = 300
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_ref = parent
        self.cache = None
        self.current_results = []
        self.cache_dir = str(Path(__file__).parent / 'cache_local')
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)
        self._setup_ui()
        self._setup_shortcuts()
        QTimer.singleShot(200, self._inicializar_cache)
    def _setup_ui(self):
        self.setWindowTitle('Tech Union - Pel├¡culas Compat├¡veis')
        self.setMinimumSize(700, 550)
        screen = QApplication.primaryScreen()
        if screen:
            sg = screen.availableGeometry()
            w = int(sg.width() * 0.65)
            h = int(sg.height() * 0.75)
            self.resize(w, h)
            self.move(sg.x() + (sg.width() - w) // 2, sg.y() + (sg.height() - h) // 2)
        else:
            self.resize(1000, 700)
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        header = QFrame()
        header.setStyleSheet('\n            QFrame {\n                background-color: #FFFFFF;\n                border-bottom: 1px solid #dadce0;\n            }\n        ')
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)
        lbl_title = QLabel('Pel├¡culas Compat├¡veis')
        lbl_title.setStyleSheet('font-size: 18px; font-weight: 600; color: #1a73e8;')
        header_layout.addWidget(lbl_title)
        header_layout.addStretch()
        self.lbl_model_count = QLabel('')
        self.lbl_model_count.setStyleSheet('\n            font-size: 13px; font-weight: 500; color: #1a73e8;\n            padding: 4px 12px; background-color: #e8f0fe; border-radius: 12px;\n        ')
        self.lbl_model_count.setVisible(False)
        header_layout.addWidget(self.lbl_model_count)
        main_layout.addWidget(header)
        content = QWidget()
        content.setStyleSheet('background-color: #FFFFFF;')
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 16, 20, 12)
        content_layout.setSpacing(12)
        self.loading_widget = QWidget()
        loading_layout = QVBoxLayout(self.loading_widget)
        loading_layout.setAlignment(Qt.AlignCenter)
        loading_layout.setSpacing(16)
        self.lbl_loading = QLabel('Carregando...')
        self.lbl_loading.setAlignment(Qt.AlignCenter)
        self.lbl_loading.setStyleSheet('font-size: 18px; font-weight: 600; color: #1a73e8;')
        loading_layout.addWidget(self.lbl_loading)
        self.lbl_loading_detail = QLabel('Verificando dados locais...')
        self.lbl_loading_detail.setAlignment(Qt.AlignCenter)
        self.lbl_loading_detail.setStyleSheet('font-size: 13px; color: #666666;')
        loading_layout.addWidget(self.lbl_loading_detail)
        content_layout.addWidget(self.loading_widget)
        self.search_widget = QWidget()
        self.search_widget.setVisible(False)
        search_layout = QVBoxLayout(self.search_widget)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(8)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Busca por nome completo, parcial ou c├│digo do modelo')
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setStyleSheet('\n            QLineEdit {\n                padding: 10px 14px; font-size: 14px;\n                border: 2px solid #dadce0; border-radius: 8px;\n                background-color: #FFFFFF;\n            }\n            QLineEdit:focus { border-color: #1a73e8; }\n        ')
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_input)
        results_row = QHBoxLayout()
        self.lbl_result_count = QLabel('Digite um modelo para buscar')
        self.lbl_result_count.setStyleSheet('font-size: 13px; font-weight: 500; color: #333333; padding: 4px 0;')
        results_row.addWidget(self.lbl_result_count)
        results_row.addStretch()
        self.btn_copy = QPushButton('Copiar Lista')
        self.btn_copy.setStyleSheet('\n            QPushButton {\n                padding: 10px 24px; font-size: 14px; font-weight: 500;\n                border-radius: 6px; border: none;\n                background-color: #28a745; color: white;\n            }\n            QPushButton:hover { background-color: #218838; }\n        ')
        self.btn_copy.setVisible(False)
        self.btn_copy.setCursor(Qt.PointingHandCursor)
        self.btn_copy.clicked.connect(self._on_copy_click)
        results_row.addWidget(self.btn_copy)
        search_layout.addLayout(results_row)
        self.table_results = QTableWidget()
        self.table_results.setColumnCount(2)
        self.table_results.setHorizontalHeaderLabels(['MODELO DO APARELHO', 'PEL├ìCULAS COMPAT├ìVEIS'])
        self.table_results.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_results.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_results.horizontalHeader().setStyleSheet('\n            QHeaderView::section {\n                background-color: #1a73e8; color: white;\n                font-weight: bold; font-size: 13px;\n                padding: 8px 12px; border: none;\n            }\n        ')
        self.table_results.verticalHeader().setVisible(False)
        self.table_results.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_results.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_results.setAlternatingRowColors(True)
        self.table_results.setWordWrap(True)
        self.table_results.setStyleSheet('\n            QTableWidget {\n                border: 1px solid #dadce0; border-radius: 4px;\n                background-color: #FFFFFF; font-size: 13px;\n                gridline-color: #e0e0e0;\n            }\n            QTableWidget::item {\n                padding: 8px 12px;\n            }\n            QTableWidget::item:selected {\n                background-color: #e8f0fe; color: #333333;\n            }\n        ')
        search_layout.addWidget(self.table_results, 1)
        content_layout.addWidget(self.search_widget)
        main_layout.addWidget(content, 1)
        self.lbl_status = QLabel('Inicializando...')
        self.lbl_status.setStyleSheet('\n            background-color: #f8f9fa; border-top: 1px solid #dadce0;\n            color: #666666; font-size: 12px; padding: 6px 12px;\n        ')
        main_layout.addWidget(self.lbl_status)
    def _inicializar_cache(self):
        '''Inicializa e sincroniza cache. Roda no thread principal via QTimer.'''
        try:
            self.lbl_loading.setText('Verificando dados...')
            QApplication.processEvents()
            self.cache = PeliculasCache(cache_dir=self.cache_dir)
            self.cache.inicializar()
            stats = self.cache.get_estatisticas()
            needs_sync = stats['total_modelos'] == 0 or not stats['cache_valido']
            if needs_sync:
                self.lbl_loading.setText('Sincronizando...')
                self.lbl_loading_detail.setText('Baixando dados do servidor...')
                QApplication.processEvents()
                sucesso, msg = self.cache.sincronizar(force=True)
                if sucesso:
                    stats = self.cache.get_estatisticas()
                    self.lbl_status.setText(f'Pronto ÔÇö {stats['total_modelos']} modelos dispon├¡veis')
                    self.lbl_status.setStyleSheet('background-color: #f8f9fa; border-top: 1px solid #dadce0; color: #28a745; font-size: 12px; padding: 6px 12px;')
                else:
                    self.lbl_status.setText(f'Pronto ÔÇö {stats['total_modelos']} modelos dispon├¡veis')
            else:
                self.lbl_status.setText(f'Pronto ÔÇö {stats['total_modelos']} modelos dispon├¡veis')
            if stats['total_modelos'] > 0:
                self.lbl_model_count.setText(f'{stats['total_modelos']} modelos')
                self.lbl_model_count.setVisible(True)
                self.loading_widget.setVisible(False)
                self.search_widget.setVisible(True)
                self.search_input.setFocus()
                return
            self.lbl_loading.setText('Sem dados')
            self.lbl_loading_detail.setText('N├úo foi poss├¡vel carregar os dados.\nVerifique sua conex├úo.')
            return
        except Exception as e:
            self.lbl_loading.setText('Erro')
            self.lbl_loading_detail.setText('N├úo foi poss├¡vel conectar ├á base de dados.\nTente novamente mais tarde.')
            self.lbl_status.setText('Erro ao carregar dados')
            print(f'[PeliculasWindow] Erro na inicializa├º├úo: {e}')
    def _on_search_changed(self, text):
        self.search_timer.stop()
        if len(text.strip()) >= 2:
            self.search_timer.start(self.DEBOUNCE_MS)
            return
        self._clear_results()
    def _perform_search(self):
        if not self.cache:
            return
        termo = self.search_input.text().strip()
        if len(termo) < 2:
            self._clear_results()
            return
        resultados = self.cache.buscar(termo)
        self.current_results = resultados
        self._display_results(resultados, termo)
    def _separar_resultados(self, resultados, termo):
        '''Agrupa por grupo_id e separa modelos buscados dos compat├¡veis.'''
        termo_upper = termo.upper().strip()
        por_grupo = {}
        for r in resultados:
            gid = r.get('grupo_id')
            if gid not in por_grupo:
                por_grupo[gid] = {'buscados': [], 'compativeis': []}
            nome = r.get('modelo', '').upper()
            codigo = (r.get('codigo', '') or '').upper()
            if termo_upper in nome or termo_upper in codigo:
                por_grupo[gid]['buscados'].append(r)
            else:
                por_grupo[gid]['compativeis'].append(r)
        linhas = []
        for gid, grupo in por_grupo.items():
            buscados = grupo['buscados']
            compativeis = grupo['compativeis']
            if not buscados:
                buscados = [compativeis.pop(0)] if compativeis else []
            todos_do_grupo = buscados + compativeis
            for b in buscados:
                outros = [m for m in todos_do_grupo if m is not b]
                linhas.append((b, outros))
        return linhas
    def _display_results(self, resultados, termo):
        self.table_results.setRowCount(0)
        if not resultados:
            self.lbl_result_count.setText(f'Nenhum modelo encontrado para "{termo}"')
            self.btn_copy.setVisible(False)
            return
        linhas = self._separar_resultados(resultados, termo)
        self.table_results.setRowCount(len(linhas))
        bold_font = QFont()
        bold_font.setBold(True)
        for row, (modelo_buscado, compativeis) in enumerate(linhas):
            item_modelo = QTableWidgetItem(modelo_buscado['modelo'])
            item_modelo.setFont(bold_font)
            self.table_results.setItem(row, 0, item_modelo)
            nomes_compat = ' / '.join((c['modelo'] for c in compativeis))
            if not nomes_compat:
                nomes_compat = '(sem compat├¡veis adicionais)'
            item_compat = QTableWidgetItem(nomes_compat)
            self.table_results.setItem(row, 1, item_compat)
        self.table_results.resizeRowsToContents()
        total = len(linhas)
        self.lbl_result_count.setText(f'{total} resultado{'s' if total != 1 else ''} encontrado{'s' if total != 1 else ''}')
        self.btn_copy.setVisible(True)
    def _clear_results(self):
        self.table_results.setRowCount(0)
        self.current_results = []
        self.lbl_result_count.setText('Digite um modelo para buscar')
        self.btn_copy.setVisible(False)
    def _on_copy_click(self):
        if not self.current_results:
            return
        termo = self.search_input.text().strip()
        linhas_dados = self._separar_resultados(self.current_results, termo)
        linhas = ['Pel├¡culas Compat├¡veis', '----------------------------------------']
        for modelo_buscado, compativeis in linhas_dados:
            nomes = ' / '.join((c['modelo'] for c in compativeis)) if compativeis else '(sem compat├¡veis)'
            linhas.append(f'{modelo_buscado['modelo']}  ÔåÆ  {nomes}')
        linhas.append('----------------------------------------')
        linhas.append('Tech Union Solutions')
        QApplication.clipboard().setText('\n'.join(linhas))
        self.btn_copy.setText('Copiado!')
        QTimer.singleShot(2000, (lambda: self.btn_copy.setText('Copiar Lista')))
    def _setup_shortcuts(self):
        '''Atalho Ctrl+Shift+F5 para for├ºar sincroniza├º├úo (uso interno TI)'''
        shortcut = QShortcut(QKeySequence('Ctrl+Shift+F5'), self)
        shortcut.activated.connect(self._force_sync)
    def _force_sync(self):
        '''Sincroniza├º├úo for├ºada do cache ÔÇö uso exclusivo TI (Ctrl+Shift+F5)'''
        if not self.cache:
            self.lbl_status.setText('Cache n├úo inicializado')
            return
        self.lbl_status.setText('Sincronizando com servidor...')
        QApplication.processEvents()
        try:
            self.cache._last_sync = None
            sucesso, msg = self.cache.sincronizar(force=True)
            stats = self.cache.get_estatisticas()
            total = stats.get('total_modelos', 0)
            if sucesso:
                self.lbl_status.setText(f'Atualizado ÔÇö {total} modelos dispon├¡veis')
                self.lbl_model_count.setText(f'{total} modelos')
                return
            self.lbl_status.setText(f'Falha: {msg} ÔÇö {total} modelos dispon├¡veis')
            return
        except Exception as e:
            self.lbl_status.setText('Erro na sincroniza├º├úo. Tente novamente.')
            print(f'[PeliculasWindow] Erro na sincroniza├º├úo: {e}')
