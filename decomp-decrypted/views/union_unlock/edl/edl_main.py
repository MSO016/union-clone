import sys
import os
import threading
from time import monotonic
from PyQt5.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem, QStackedWidget, QFrame, QLineEdit, QLabel, QTabWidget, QComboBox, QPushButton, QProgressBar, QGraphicsOpacityEffect)
from PyQt5.QtCore import (Qt, pyqtSignal, pyqtSlot, QThread, QTimer, QSize, QPropertyAnimation)
from PyQt5.QtGui import (QFont, QPixmap, QKeySequence)
try:
    from app.views.union_unlock.edl import config
    from app.views.union_unlock.edl.edl_ativo import EdlAtivoWidget
    from app.views.union_unlock.edl.auto import EdlAutoWidget
    from app.views.union_unlock.edl.manual import EdlManualWidget
    from app.views.union_unlock.edl.partitions import PartitionManagerWidget
except ImportError:
    import config
    from edl_ativo import EdlAtivoWidget
    from auto import EdlAutoWidget
    from manual import EdlManualWidget
    from partitions import PartitionManagerWidget
def _log(msg: str):
    print(f'[EDL_MAIN] {msg}', flush=True)
IMG_DIR = config.IMG_DIR
TOOLS_DIR = str(config.TOOLS_DIR)
class _Cores:
    BG = '#f5f5f5'
    BG_WHITE = '#ffffff'
    PRIMARY = '#1428A0'
    XIAOMI = '#ff6700'
    OPPO = '#1a9c2d'
    VIVO = '#415fff'
    REALME = '#ffc800'
    HONOR = '#00a4a6'
    HUAWEI = '#cf0a2c'
    TEXT = '#2c3e50'
    MUTED = '#7f8c8d'
    WHITE = '#ffffff'
    BORDER = '#bdc3c7'
    SUCCESS = '#27ae60'
_BRAND_COLORS = {'Samsung': _Cores.PRIMARY, 'Xiaomi': _Cores.XIAOMI, 'Oppo': _Cores.OPPO, 'Vivo': _Cores.VIVO, 'Realme': _Cores.REALME, 'Honor': _Cores.HONOR, 'Huawei': _Cores.HUAWEI}
_DEFAULT_BRAND_COLOR = '#607d8b'
class _OverlayVerificacao(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Widget)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setStyleSheet('background-color: rgba(245, 245, 245, 230);')
        self.hide()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        try:
            from app.views.union_unlock.edl.config import LOGO_PATH
        except ImportError:
            from config import LOGO_PATH
        self._lbl_logo = QLabel(self)
        self._lbl_logo.setAlignment(Qt.AlignCenter)
        if os.path.exists(LOGO_PATH):
            pix = QPixmap(LOGO_PATH).scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self._lbl_logo.setPixmap(pix)
        layout.addWidget(self._lbl_logo)
        self._lbl_txt = QLabel('Verificando...', self)
        self._lbl_txt.setAlignment(Qt.AlignCenter)
        self._lbl_txt.setFont(QFont('Segoe UI', 13))
        self._lbl_txt.setStyleSheet('color: #2c3e50; margin-top: 10px;')
        layout.addWidget(self._lbl_txt)
        self._bar = QProgressBar(self)
        self._bar.setFixedSize(220, 14)
        self._bar.setRange(0, 0)
        self._bar.setTextVisible(False)
        self._bar.setStyleSheet('QProgressBar { border: 1px solid #bdc3c7; border-radius: 7px; background-color: #ffffff; } QProgressBar::chunk { background-color: #1428A0; border-radius: 6px; }')
        layout.addWidget(self._bar, alignment=Qt.AlignCenter)
    def mostrar(self, texto='Verificando...'):
        self._lbl_txt.setText(texto)
        self._bar.setRange(0, 0)
        if self.parent():
            self.setGeometry(self.parent().rect())
        self.raise_()
        self.show()
    def concluir(self, texto='Pronto', ms_fechar=1200):
        self._lbl_txt.setText(texto)
        self._bar.setRange(0, 1)
        self._bar.setValue(1)
        QTimer.singleShot(ms_fechar, self.hide)
class _MarcaWidget(QWidget):
    _sinal_modelos = pyqtSignal(list)
    redirecionar_particoes = pyqtSignal(dict)
    def __init__(self, marca, cor, parent=None):
        super().__init__(parent)
        self._marca = marca
        self._cor = cor
        self._carregado = False
        self._sinal_modelos.connect(self._popular_modelos)
        self.setStyleSheet(f'background-color: {_Cores.BG};')
        self._setup_ui()
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        left = QFrame()
        left.setFixedWidth(300)
        left.setStyleSheet(f'background-color: {_Cores.BG_WHITE}; border-right: 1px solid {_Cores.BORDER};')
        ll = QVBoxLayout(left)
        ll.setContentsMargins(10, 15, 10, 15)
        ll.setSpacing(10)
        self.busca = QLineEdit()
        self.busca.setPlaceholderText('Buscar')
        self.busca.setFixedHeight(35)
        self.busca.setFont(QFont('Segoe UI', 11))
        self.busca.setStyleSheet(f'\n            QLineEdit {{\n                background-color: {_Cores.BG};\n                border: 1px solid {_Cores.BORDER};\n                border-radius: 17px; padding: 0 15px;\n                color: {_Cores.TEXT};\n            }}\n            QLineEdit:focus {{ border: 2px solid {self._cor}; }}\n        ')
        self.busca.textChanged.connect(self._filtrar)
        ll.addWidget(self.busca)
        self.lista = QListWidget()
        self.lista.setFont(QFont('Segoe UI', 11))
        self.lista.setStyleSheet(f'\n            QListWidget {{ background-color: {_Cores.BG_WHITE}; border: none; }}\n            QListWidget::item {{\n                color: {_Cores.TEXT}; padding: 10px 12px;\n                border-radius: 8px; margin: 2px 0;\n            }}\n            QListWidget::item:hover {{ background-color: {_Cores.BG}; }}\n            QListWidget::item:selected {{\n                background-color: {self._cor}; color: {_Cores.WHITE};\n            }}\n        ')
        self.lista.currentItemChanged.connect(self._on_select)
        ll.addWidget(self.lista)
        layout.addWidget(left)
        self.stacked = QStackedWidget()
        self.stacked.setStyleSheet(f'background-color: {_Cores.BG};')
        self._lbl_status = QLabel('Selecione um modelo')
        self._lbl_status.setAlignment(Qt.AlignCenter)
        self._lbl_status.setFont(QFont('Segoe UI', 14))
        self._lbl_status.setStyleSheet(f'color: {_Cores.MUTED};')
        self.stacked.addWidget(self._lbl_status)
        layout.addWidget(self.stacked, stretch=1)
        self._widgets = {}
    def showEvent(self, event):
        super().showEvent(event)
        if not self._carregado:
            self._carregado = True
            threading.Thread(target=self._carregar, daemon=True).start()
    def _carregar(self):
        try:
            from app.views.union_unlock.edl.edl_sync import get_sync
        except ImportError:
            from edl_sync import get_sync
        sync = get_sync()
        modelos = sync.listar_marca(self._marca)
        _log(f'{self._marca}: {len(modelos)} modelos no cache')
        if modelos:
            self._sinal_modelos.emit(modelos)
    def _popular_modelos(self, modelos):
        novos = 0
        for m in modelos:
            chave = f'_srv_{m['srv_id']}'
            if chave in self._widgets:
                continue
            item = QListWidgetItem(m['modelo'])
            item.setData(Qt.UserRole, chave)
            self.lista.addItem(item)
            widget = EdlAtivoWidget(m, self._marca, IMG_DIR, TOOLS_DIR, parent=self)
            widget.redirecionar_particoes.connect(self.redirecionar_particoes)
            self.stacked.addWidget(widget)
            self._widgets[chave] = widget
            novos += 1
        _log(f'{self._marca}: {novos} modelos carregados ({self.lista.count()} total)')
        if self.lista.count() > 0:
            if self.lista.currentRow() < 0:
                self.lista.setCurrentRow(0)
    def recarregar(self):
        self.lista.clear()
        for w in self._widgets.values():
            self.stacked.removeWidget(w)
            w.deleteLater()
        self._widgets.clear()
        self._carregado = False
        threading.Thread(target=self._carregar, daemon=True).start()
    def _filtrar(self, texto):
        texto = texto.lower()
        for i in range(self.lista.count()):
            item = self.lista.item(i)
            item.setHidden(texto not in item.text().lower())
    def _on_select(self, current, previous):
        if current:
            chave = current.data(Qt.UserRole)
            if chave in self._widgets:
                self.stacked.setCurrentWidget(self._widgets[chave])
class EdlMainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f'background-color: {_Cores.BG};')
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        header = QWidget()
        header.setFixedHeight(48)
        header.setStyleSheet(f'background-color: {_Cores.PRIMARY};')
        hl = QHBoxLayout(header)
        hl.setContentsMargins(16, 0, 16, 0)
        titulo = QLabel('TECH UNION SOLUTIONS QCOM (USE COM MODERA├ç├âO)')
        titulo.setFont(QFont('Segoe UI', 14, QFont.Bold))
        titulo.setStyleSheet(f'color: {_Cores.WHITE};')
        hl.addWidget(titulo)
        hl.addStretch()
        self._lbl_porta_ico = QLabel('ÔùÅ')
        self._lbl_porta_ico.setFixedWidth(18)
        self._lbl_porta_ico.setStyleSheet('color: #ff4444; font-size: 16px; font-weight: bold;')
        self._lbl_porta_ico.setToolTip('Nenhum dispositivo EDL conectado')
        hl.addWidget(self._lbl_porta_ico)
        self._combo_porta = QComboBox()
        self._combo_porta.setFixedWidth(240)
        self._combo_porta.setFixedHeight(28)
        self._combo_porta.setStyleSheet("QComboBox { background-color: #0e1a6e; color: #ffffff; border: 1px solid #4a5abf; border-radius: 5px; padding: 2px 10px; font-size: 11px; font-family: 'Segoe UI'; font-weight: bold; } QComboBox::drop-down { border: none; } QComboBox QAbstractItemView { background-color: #1a1a3e; color: #ffffff; selection-background-color: #3355cc; }")
        self._combo_porta.addItem('Aguardando dispositivo EDL...')
        hl.addWidget(self._combo_porta)
        self._btn_refresh_porta = QPushButton('Ôƒ│')
        self._btn_refresh_porta.setFixedSize(28, 28)
        self._btn_refresh_porta.setCursor(Qt.PointingHandCursor)
        self._btn_refresh_porta.setToolTip('Verificar portas COM')
        self._btn_refresh_porta.setStyleSheet('QPushButton { background-color: #0e1a6e; color: #ffffff; border: 1px solid #4a5abf; border-radius: 5px; font-size: 14px; font-weight: bold; } QPushButton:hover { background-color: #3355cc; }')
        self._btn_refresh_porta.clicked.connect(self._atualizar_portas)
        hl.addWidget(self._btn_refresh_porta)
        main_layout.addWidget(header)
        self._scan_timer = QTimer(self)
        self._scan_timer.setInterval(3000)
        self._scan_timer.timeout.connect(self._atualizar_portas)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"\n            QTabBar::tab {{\n                min-width: 90px; padding: 8px 18px;\n                font-size: 12px; font-family: 'Segoe UI'; font-weight: bold;\n            }}\n            QTabBar::tab:selected {{\n                color: {_Cores.PRIMARY};\n                border-bottom: 3px solid {_Cores.PRIMARY};\n            }}\n        ")
        self._tabs_marca = {}
        self._auto_widget = EdlAutoWidget()
        self._auto_widget.redirecionar_particoes.connect(self._ir_para_particoes)
        self.tabs.addTab(self._auto_widget, 'Auto')
        self._manual_widget = EdlManualWidget()
        self.tabs.addTab(self._manual_widget, 'Manual')
        self._partition_widget = PartitionManagerWidget()
        self.tabs.addTab(self._partition_widget, 'Parti├º├Áes')
        self._criar_abas_marcas()
        main_layout.addWidget(self.tabs)
        self._overlay = _OverlayVerificacao(self)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_overlay'):
            if self._overlay.isVisible():
                self._overlay.setGeometry(self.rect())
    def showEvent(self, event):
        super().showEvent(event)
        self._scan_timer.start()
        if not hasattr(self, '_inicializado'):
            self._inicializado = True
            QTimer.singleShot(300, self._sync_silencioso)
            QTimer.singleShot(500, self._atualizar_portas)
    def hideEvent(self, event):
        super().hideEvent(event)
        self._scan_timer.stop()
    def _sync_silencioso(self):
        self._overlay.mostrar('Verificando...')
        def _run():
            try:
                from app.views.union_unlock.edl.edl_sync import get_sync
            except ImportError:
                from edl_sync import get_sync
            sync = get_sync()
            precisa = sync.pode_sincronizar()
            if precisa:
                _log('Verificacao QCOM iniciando...')
                ok = sync.sincronizar()
                _log(f'Verificacao QCOM {'OK' if ok else 'sem conexao'}')
            from PyQt5.QtCore import QMetaObject, Qt as _Qt
            QMetaObject.invokeMethod(self, '_recarregar_marcas', _Qt.QueuedConnection)
            QMetaObject.invokeMethod(self, '_finalizar_overlay', _Qt.QueuedConnection)
        threading.Thread(target=_run, daemon=True).start()
    @pyqtSlot()
    def _finalizar_overlay(self):
        self._overlay.concluir('Pronto', 1200)
    def _atualizar_portas(self):
        porta_atual = self._combo_porta.currentData()
        self._combo_porta.clear()
        encontrou = False
        idx_restore = -1
        try:
            from serial.tools import list_ports
            for p in list_ports.comports():
                hwid = (p.hwid or '').lower()
                desc = (p.description or '').lower()
                if '05c6' in hwid:
                    if '9008' not in hwid:
                        if '9008' in desc and ('qdloader' in desc or 'qualcomm' in desc):
                            self._combo_porta.addItem(f'{p.device} ÔÇö QDLoader 9008', p.device)
                            if p.device == porta_atual:
                                idx_restore = self._combo_porta.count() - 1
                            encontrou = True
        except Exception:
            pass
        if encontrou:
            self._lbl_porta_ico.setStyleSheet('color: #00ff88; font-size: 16px; font-weight: bold;')
            self._lbl_porta_ico.setToolTip('Dispositivo EDL detectado')
            if idx_restore >= 0:
                self._combo_porta.setCurrentIndex(idx_restore)
                return
            return
        self._combo_porta.addItem('Aguardando dispositivo EDL...')
        self._lbl_porta_ico.setStyleSheet('color: #ff4444; font-size: 16px; font-weight: bold;')
        self._lbl_porta_ico.setToolTip('Nenhum dispositivo EDL conectado')
    def porta_selecionada(self):
        data = self._combo_porta.currentData()
        if data:
            return data
    def sincronizar(self):
        def _run():
            try:
                from app.views.union_unlock.edl.edl_sync import get_sync
            except ImportError:
                from edl_sync import get_sync
            sync = get_sync()
            ok = sync.sincronizar()
            _log(f'Verificacao QCOM manual {'OK' if ok else 'sem conexao'}')
            if ok:
                sync.sincronizar_loaders_auto()
                from PyQt5.QtCore import QMetaObject, Qt as _Qt
                QMetaObject.invokeMethod(self, '_recarregar_marcas', _Qt.QueuedConnection)
        threading.Thread(target=_run, daemon=True).start()
    def _criar_abas_marcas(self):
        try:
            from app.views.union_unlock.edl.edl_sync import get_sync
        except ImportError:
            from edl_sync import get_sync
        sync = get_sync()
        marcas_db = sync.listar_marcas_disponiveis()
        if not marcas_db:
            marcas_db = list(_BRAND_COLORS.keys())
        for marca in marcas_db:
            if marca in self._tabs_marca:
                continue
            cor = _BRAND_COLORS.get(marca, _DEFAULT_BRAND_COLOR)
            widget = _MarcaWidget(marca, cor)
            widget.redirecionar_particoes.connect(self._ir_para_particoes)
            self.tabs.addTab(widget, marca)
            self._tabs_marca[marca] = widget
            _log(f'Aba criada: {marca}')
    @pyqtSlot()
    def _recarregar_marcas(self):
        self._criar_abas_marcas()
        try:
            from app.views.union_unlock.edl.edl_sync import get_sync
        except ImportError:
            from edl_sync import get_sync
        sync = get_sync()
        marcas_com_modelos = set(sync.listar_marcas_disponiveis())
        for marca in list(self._tabs_marca.keys()):
            if marcas_com_modelos and marca not in marcas_com_modelos:
                widget = self._tabs_marca.pop(marca)
                idx = self.tabs.indexOf(widget)
                if idx >= 0:
                    self.tabs.removeTab(idx)
                widget.deleteLater()
                _log(f'Aba removida (sem modelos): {marca}')
            else:
                self._tabs_marca[marca].recarregar()
        if hasattr(self, '_partition_widget'):
            marca_tab = getattr(self._partition_widget, '_marca_tab', None)
            if marca_tab:
                if hasattr(marca_tab, 'recarregar_marcas'):
                    marca_tab.recarregar_marcas()
    def _ir_para_particoes(self, dados: dict):
        _log(f'Redirecionando para Parti├º├Áes: {dados.get('modelo', '?')}')
        idx = self.tabs.indexOf(self._partition_widget)
        if idx >= 0:
            self.tabs.setCurrentIndex(idx)
            auth_type = dados.get('auth_type')
            loader_path = dados.get('loader_path')
            device_info = dados.get('device_info', {})
            memoria = device_info.get('memoria_auto') or dados.get('memoria', 'emmc')
            if auth_type:
                self._partition_widget.pre_configurar_auth(auth_type)
            if loader_path:
                self._partition_widget.carregar_loader_e_iniciar(loader_path, memoria, auth_type)
    def pre_configurar_auth(self, auth_type: str):
        self._partition_widget.pre_configurar_auth(auth_type)
