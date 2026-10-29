import os
import sys
import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QProgressBar, QLabel, QMessageBox, QMainWindow)
from PyQt5.QtCore import (Qt, QUrl, QSize, pyqtSignal)
from PyQt5.QtGui import (QIcon, QFont, QPixmap, QPainter, QColor)
try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False
    QWebEngineView = None
    QWebEnginePage = None
logger = logging.getLogger(__name__)
def _aplicar_icone_btn(btn, svg_relativo, tamanho=16, cor='#FFFFFF'):
    try:
        from PyQt5.QtSvg import QSvgRenderer
        from app.utils.path_manager import PathManager
        caminho = PathManager.get_resource_path(svg_relativo)
        if not caminho or not os.path.isfile(caminho):
            return
        renderer = QSvgRenderer(caminho)
        pixmap = QPixmap(tamanho, tamanho)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        renderer.render(painter)
        if cor:
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.fillRect(pixmap.rect(), QColor(cor))
        painter.end()
        btn.setIcon(QIcon(pixmap))
        btn.setIconSize(QSize(tamanho, tamanho))
        return
    except Exception:
        return
def is_webengine_available():
    return WEBENGINE_AVAILABLE
class WebViewWidget(QMainWindow):
    url_changed = pyqtSignal(str)
    page_loaded = pyqtSignal(bool)
    def __init__(self, url='https://www.google.com', title='Navegador TECH UNION', show_controls=True, show_url_bar=True, allow_external=False, parent=None):
        super().__init__(parent)
        if not WEBENGINE_AVAILABLE:
            QMessageBox.critical(self, 'M├│dulo N├úo Instalado', 'O navegador interno requer o m├│dulo PyQtWebEngine.\n\nPara instalar, execute:\npip install PyQtWebEngine\n\nAp├│s a instala├º├úo, reinicie o aplicativo.')
            logger.error('PyQtWebEngine n├úo est├í instalado')
            self.close()
            return
        self.logger = logging.getLogger(__name__)
        self.initial_url = url
        self.allow_external = allow_external
        self.show_controls = show_controls
        self.show_url_bar = show_url_bar
        self.setWindowTitle(title)
        from PyQt5.QtWidgets import QDesktopWidget
        screen = QDesktopWidget().screenGeometry()
        width = int(screen.width() * 0.8)
        height = int(screen.height() * 0.85)
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        self.setGeometry(x, y, width, height)
        self.setMinimumSize(800, 600)
        self.setup_ui()
        if url:
            self.navigate_to_url(url)
        self.logger.info(f'Navegador interno criado: {url}')
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        if self.show_controls:
            controls_bar = QWidget()
            controls_bar.setFixedHeight(45)
            controls_bar.setStyleSheet('\n                QWidget {\n                    background-color: #2c3e50;\n                    padding: 4px 8px;\n                }\n                QPushButton {\n                    background-color: #34495e;\n                    color: white;\n                    border: none;\n                    padding: 6px 12px;\n                    border-radius: 3px;\n                    font-weight: bold;\n                    font-size: 11px;\n                    min-width: 70px;\n                    max-height: 32px;\n                }\n                QPushButton:hover {\n                    background-color: #3d566e;\n                }\n                QPushButton:pressed {\n                    background-color: #2980b9;\n                }\n                QPushButton:disabled {\n                    background-color: #7f8c8d;\n                    color: #bdc3c7;\n                }\n            ')
            controls_layout = QHBoxLayout(controls_bar)
            controls_layout.setSpacing(4)
            controls_layout.setContentsMargins(4, 4, 4, 4)
            self.back_btn = QPushButton('Voltar')
            self.back_btn.setToolTip('Voltar para p├ígina anterior')
            self.back_btn.clicked.connect(self.go_back)
            controls_layout.addWidget(self.back_btn)
            self.forward_btn = QPushButton('Avan├ºar')
            self.forward_btn.setToolTip('Avan├ºar para pr├│xima p├ígina')
            self.forward_btn.clicked.connect(self.go_forward)
            controls_layout.addWidget(self.forward_btn)
            self.reload_btn = QPushButton('Recarregar')
            self.reload_btn.setToolTip('Recarregar p├ígina atual')
            _aplicar_icone_btn(self.reload_btn, 'icons_svg/arrow-clockwise.svg')
            self.reload_btn.clicked.connect(self.reload_page)
            controls_layout.addWidget(self.reload_btn)
            self.home_btn = QPushButton('In├¡cio')
            self.home_btn.setToolTip('Voltar para p├ígina inicial')
            self.home_btn.clicked.connect(self.go_home)
            controls_layout.addWidget(self.home_btn)
            controls_layout.addStretch()
            self.external_btn = QPushButton('Abrir Externo')
            self.external_btn.setToolTip('Abrir no navegador padr├úo do sistema\n\nAlgumas fun├º├Áes funcionam melhor no navegador externo:\n- Visualiza├º├úo e impress├úo de PDF\n- Abrir pastas do sistema\n- Download de arquivos')
            self.external_btn.setStyleSheet('\n                QPushButton {\n                    background-color: #2980b9;\n                    color: white;\n                    border: none;\n                    padding: 6px 12px;\n                    border-radius: 3px;\n                    font-weight: bold;\n                    font-size: 11px;\n                    min-width: 90px;\n                    max-height: 32px;\n                }\n                QPushButton:hover {\n                    background-color: #3498db;\n                }\n                QPushButton:pressed {\n                    background-color: #1a5276;\n                }\n            ')
            _aplicar_icone_btn(self.external_btn, 'icons_svg/globe.svg')
            self.external_btn.clicked.connect(self.open_external)
            controls_layout.addWidget(self.external_btn)
            self.close_btn = QPushButton('Fechar')
            self.close_btn.setToolTip('Fechar navegador')
            self.close_btn.clicked.connect(self.close)
            controls_layout.addWidget(self.close_btn)
            main_layout.addWidget(controls_bar)
        if self.show_url_bar:
            url_bar_widget = QWidget()
            url_bar_widget.setFixedHeight(38)
            url_bar_widget.setStyleSheet('\n                QWidget {\n                    background-color: #ecf0f1;\n                    padding: 3px 8px;\n                }\n                QLineEdit {\n                    background-color: white;\n                    border: 1px solid #bdc3c7;\n                    border-radius: 3px;\n                    padding: 6px;\n                    font-size: 12px;\n                }\n                QLineEdit:focus {\n                    border-color: #3498db;\n                }\n            ')
            url_bar_layout = QHBoxLayout(url_bar_widget)
            url_bar_layout.setSpacing(4)
            url_bar_layout.setContentsMargins(4, 3, 4, 3)
            url_label = QLabel('URL')
            url_label.setStyleSheet('font-size: 11px; font-weight: bold; color: #2c3e50;')
            url_bar_layout.addWidget(url_label)
            self.url_bar = QLineEdit()
            self.url_bar.setPlaceholderText('Digite a URL e pressione Enter...')
            self.url_bar.returnPressed.connect(self.on_url_enter)
            url_bar_layout.addWidget(self.url_bar)
            go_btn = QPushButton('IR')
            go_btn.setFixedSize(50, 28)
            go_btn.setStyleSheet('\n                QPushButton {\n                    background-color: #27ae60;\n                    color: white;\n                    border: none;\n                    padding: 4px 8px;\n                    border-radius: 3px;\n                    font-weight: bold;\n                    font-size: 11px;\n                }\n                QPushButton:hover {\n                    background-color: #2ecc71;\n                }\n                QPushButton:pressed {\n                    background-color: #229954;\n                }\n            ')
            go_btn.clicked.connect(self.on_url_enter)
            url_bar_layout.addWidget(go_btn)
            main_layout.addWidget(url_bar_widget)
        info_bar = QWidget()
        info_bar.setFixedHeight(55)
        info_bar.setStyleSheet('\n            QWidget {\n                background-color: #e67e22;\n                border-bottom: 3px solid #d35400;\n            }\n            QLabel#info_main {\n                color: white;\n                font-size: 14px;\n                font-weight: bold;\n                background-color: transparent;\n            }\n            QLabel#info_sub {\n                color: #ffeaa7;\n                font-size: 11px;\n                background-color: transparent;\n            }\n            QPushButton {\n                background-color: #27ae60;\n                color: white;\n                border: 2px solid #1e8449;\n                padding: 8px 20px;\n                border-radius: 5px;\n                font-size: 13px;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background-color: #2ecc71;\n                border-color: #27ae60;\n            }\n        ')
        info_layout = QHBoxLayout(info_bar)
        info_layout.setContentsMargins(15, 8, 15, 8)
        info_layout.setSpacing(12)
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        info_main = QLabel('PARA MELHOR EXPERI├èNCIA, USE O NAVEGADOR EXTERNO')
        info_main.setObjectName('info_main')
        text_layout.addWidget(info_main)
        info_sub = QLabel('PDF, impress├úo, download de arquivos e outras fun├º├Áes funcionam 100% no navegador externo')
        info_sub.setObjectName('info_sub')
        text_layout.addWidget(info_sub)
        info_layout.addLayout(text_layout)
        info_layout.addStretch()
        open_external_btn = QPushButton('ABRIR NO NAVEGADOR')
        _aplicar_icone_btn(open_external_btn, 'icons_svg/globe.svg')
        open_external_btn.clicked.connect(self.open_external)
        info_layout.addWidget(open_external_btn)
        main_layout.addWidget(info_bar)
        self.info_bar = info_bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setStyleSheet('\n            QProgressBar {\n                border: none;\n                background-color: #ecf0f1;\n                text-align: center;\n            }\n            QProgressBar::chunk {\n                background-color: #3498db;\n            }\n        ')
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)
        self.browser = QWebEngineView()
        self.browser.loadProgress.connect(self.on_load_progress)
        self.browser.loadFinished.connect(self.on_load_finished)
        self.browser.loadStarted.connect(self.on_load_started)
        self.browser.urlChanged.connect(self.on_url_changed)
        main_layout.addWidget(self.browser)
        self.status_label = QLabel('Pronto')
        self.status_label.setFixedHeight(24)
        self.status_label.setStyleSheet('\n            QLabel {\n                background-color: #2c3e50;\n                color: white;\n                padding: 3px 8px;\n                font-size: 10px;\n            }\n        ')
        main_layout.addWidget(self.status_label)
    def navigate_to_url(self, url):
        try:
            if not url.startswith(('http://', 'https://', 'file://')):
                url = 'https://' + url
            self.browser.setUrl(QUrl(url))
            self.logger.info(f'Navegando para: {url}')
            return
        except Exception as e:
            self.logger.error(f'Erro ao navegar para URL: {str(e)}')
            self.status_label.setText('Erro ao carregar p├ígina')
    def on_url_enter(self):
        if hasattr(self, 'url_bar'):
            url = self.url_bar.text().strip()
            if url:
                self.navigate_to_url(url)
    def go_back(self):
        if self.browser.history().canGoBack():
            self.browser.back()
            self.logger.debug('Voltando para p├ígina anterior')
    def go_forward(self):
        if self.browser.history().canGoForward():
            self.browser.forward()
            self.logger.debug('Avan├ºando para pr├│xima p├ígina')
    def reload_page(self):
        self.browser.reload()
        self.logger.debug('Recarregando p├ígina')
    def go_home(self):
        self.navigate_to_url(self.initial_url)
        self.logger.debug(f'Voltando para home: {self.initial_url}')
    def open_external(self):
        try:
            from PyQt5.QtGui import QDesktopServices
            current_url = self.browser.url().toString()
            QDesktopServices.openUrl(QUrl(current_url))
            self.logger.info(f'Abrindo externamente: {current_url}')
            self.status_label.setText('Abrindo no navegador externo...')
            return
        except Exception as e:
            self.logger.error(f'Erro ao abrir navegador externo: {str(e)}')
            QMessageBox.warning(self, 'Erro', 'N├úo foi poss├¡vel abrir o navegador externo.')
    def on_load_progress(self, progress):
        self.progress_bar.setValue(progress)
        self.status_label.setText(f'Carregando... {progress}%')
    def on_load_started(self):
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.status_label.setText('Carregando p├ígina...')
        if self.show_controls:
            self.back_btn.setEnabled(False)
            self.forward_btn.setEnabled(False)
    def on_load_finished(self, success):
        self.progress_bar.hide()
        if success:
            self.status_label.setText('P├ígina carregada com sucesso')
            self.logger.info(f'P├ígina carregada: {self.browser.url().toString()}')
        else:
            self.status_label.setText('Erro ao carregar p├ígina')
            self.logger.error(f'Erro ao carregar: {self.browser.url().toString()}')
        if self.show_controls:
            self.back_btn.setEnabled(self.browser.history().canGoBack())
            self.forward_btn.setEnabled(self.browser.history().canGoForward())
        self.page_loaded.emit(success)
    def on_url_changed(self, url):
        url_str = url.toString()
        if hasattr(self, 'url_bar'):
            self.url_bar.setText(url_str)
        self.logger.debug(f'URL alterada: {url_str}')
        self.url_changed.emit(url_str)
    def get_current_url(self):
        return self.browser.url().toString()
    def get_page_title(self):
        return self.browser.page().title()
    def closeEvent(self, event):
        self.logger.info('Navegador interno fechado')
        event.accept()
class WebViewManager:
    _instance = None
    _web_views = {}
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WebViewManager, cls).__new__(cls)
        return cls._instance
    def abrir_url(self, url, title='Navegador TECH UNION', **kwargs):
        if url in self._web_views and self._web_views[url].isVisible():
            self._web_views[url].activateWindow()
            self._web_views[url].raise_()
            return self._web_views[url]
        web_view = WebViewWidget(url=url, title=title, **kwargs)
        web_view.show()
        self._web_views[url] = web_view
        return web_view
    def fechar_todas(self):
        for web_view in self._web_views.values():
            if web_view.isVisible():
                web_view.close()
        self._web_views.clear()
def get_web_view_manager():
    return WebViewManager()
