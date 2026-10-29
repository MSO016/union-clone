from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QStackedWidget, QLineEdit, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from .redmi_a3 import RedmiA3Widget
from .redmi_a1 import RedmiA1Widget
from .redmi_a1_plus import RedmiA1PlusWidget
from .redmi_a2 import RedmiA2Widget
from .redmi_9 import Redmi9Widget
from .redmi_9c import Redmi9CWidget
from .redmi_10a import Redmi10AWidget
from .redmi_9a import Redmi9AWidget
from .redmi_10_2022 import Redmi102022Widget
from .redmi_12c import Redmi12CWidget
from .redmi_13c import Redmi13CWidget
from .redmi_14c import Redmi14CWidget
from .redmi_15c import Redmi15CWidget
from .redmi_note_12s import RedmiNote12SWidget
from .redmi_note8pro_begonia import RedmiNote8ProBegoniaWidget
from .redmi_note9_merlin import RedmiNote9MerlinWidget
from .redmi_12_fire import Redmi12FireWidget
from .poco_m3_pro import PocoM3ProWidget
from .redmi_note10_5g import RedmiNote105GWidget
from .poco_c55 import PocoC55Widget
from .poco_c50 import PocoC50Widget
from .redmi_note11s import RedmiNote11SWidget
from .redmi_note10s import RedmiNote10SWidget
from .poco_m4_pro_4g import PocoM4Pro4GWidget
from .poco_m4_pro_5g import PocoM4Pro5GWidget
from .xiaomi_fastboot_frp import XiaomiFastbootFrpWidget
class CoresUnion:
    BACKGROUND = '#f5f5f5'
    BACKGROUND_DARK = '#e8e8e8'
    BACKGROUND_WHITE = '#ffffff'
    PRIMARY = '#ff6700'
    PRIMARY_HOVER = '#e55d00'
    PRIMARY_LIGHT = '#ff8533'
    SUCCESS = '#27ae60'
    ERROR = '#e74c3c'
    WARNING = '#f39c12'
    TEXT = '#2c3e50'
    TEXT_MUTED = '#7f8c8d'
    TEXT_WHITE = '#ffffff'
    BORDER = '#bdc3c7'
class XiaomiWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f'background-color: {CoresUnion.BACKGROUND};')
        self.modelos = [('­ƒöô FRP Fastboot (BL Unlock)', 'xiaomi_fastboot_frp'), ('Redmi A1', 'redmi_a1'), ('Redmi A1+', 'redmi_a1_plus'), ('Redmi A2', 'redmi_a2'), ('Redmi A3', 'redmi_a3'), ('Redmi 9', 'redmi_9'), ('Redmi 9A', 'redmi_9a'), ('Redmi 9C', 'redmi_9c'), ('Redmi 10A', 'redmi_10a'), ('Redmi 10 2022', 'redmi_10_2022'), ('Redmi 12C', 'redmi_12c'), ('Redmi 13C', 'redmi_13c'), ('Redmi 14C', 'redmi_14c'), ('Redmi 15C', 'redmi_15c'), ('Redmi Note 8 Pro', 'redmi_note8pro_begonia'), ('Redmi Note 9', 'redmi_note9_merlin'), ('Redmi Note 10 5G', 'redmi_note10_5g'), ('Redmi Note 10S', 'redmi_note10s'), ('Redmi Note 11S', 'redmi_note11s'), ('Redmi Note 12S', 'redmi_note_12s'), ('Redmi 12', 'redmi_12_fire'), ('Poco M3 Pro 5G', 'poco_m3_pro'), ('Poco M4 Pro 4G', 'poco_m4_pro_4g'), ('Poco M4 Pro 5G', 'poco_m4_pro_5g'), ('Poco C50', 'poco_c50'), ('Poco C55', 'poco_c55')]
        self.setup_ui()
        self.carregar_modelos()
        if self.lista_modelos.count() > 0:
            self.lista_modelos.setCurrentRow(0)
    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        left_panel = QFrame()
        left_panel.setFixedWidth(330)
        left_panel.setStyleSheet(f'background-color: {CoresUnion.BACKGROUND};')
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(5)
        self.busca = QLineEdit()
        self.busca.setPlaceholderText('­ƒöì Buscar')
        self.busca.setFixedHeight(35)
        self.busca.setStyleSheet(f'\n            QLineEdit {{\n                background-color: {CoresUnion.BACKGROUND_WHITE};\n                border: 1px solid {CoresUnion.BORDER};\n                border-radius: 17px;\n                padding: 5px 15px;\n                font-size: 12px;\n            }}\n            QLineEdit:focus {{\n                border: 2px solid {CoresUnion.PRIMARY};\n            }}\n        ')
        self.busca.textChanged.connect(self.filtrar_modelos)
        left_layout.addWidget(self.busca)
        self.lista_modelos = QListWidget()
        self.lista_modelos.setStyleSheet(f'\n            QListWidget {{\n                background-color: {CoresUnion.BACKGROUND_DARK};\n                border: none;\n                border-radius: 10px;\n                padding: 5px;\n            }}\n            QListWidget::item {{\n                background-color: transparent;\n                color: {CoresUnion.TEXT};\n                padding: 10px;\n                border-radius: 8px;\n                margin: 2px;\n            }}\n            QListWidget::item:selected {{\n                background-color: {CoresUnion.PRIMARY};\n                color: white;\n            }}\n            QListWidget::item:hover:!selected {{\n                background-color: {CoresUnion.BORDER};\n            }}\n        ')
        self.lista_modelos.currentRowChanged.connect(self.modelo_selecionado)
        left_layout.addWidget(self.lista_modelos)
        main_layout.addWidget(left_panel)
        right_panel = QFrame()
        right_panel.setStyleSheet(f'background-color: {CoresUnion.BACKGROUND};')
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        self.stacked = QStackedWidget()
        self.modelo_widgets = {'xiaomi_fastboot_frp': XiaomiFastbootFrpWidget(), 'redmi_a1': RedmiA1Widget(), 'redmi_a1_plus': RedmiA1PlusWidget(), 'redmi_a2': RedmiA2Widget(), 'redmi_a3': RedmiA3Widget(), 'redmi_9': Redmi9Widget(), 'redmi_9a': Redmi9AWidget(), 'redmi_9c': Redmi9CWidget(), 'redmi_10a': Redmi10AWidget(), 'redmi_10_2022': Redmi102022Widget(), 'redmi_12c': Redmi12CWidget(), 'redmi_13c': Redmi13CWidget(), 'redmi_14c': Redmi14CWidget(), 'redmi_15c': Redmi15CWidget(), 'redmi_note8pro_begonia': RedmiNote8ProBegoniaWidget(), 'redmi_note9_merlin': RedmiNote9MerlinWidget(), 'redmi_note10_5g': RedmiNote105GWidget(), 'redmi_note10s': RedmiNote10SWidget(), 'redmi_note11s': RedmiNote11SWidget(), 'redmi_note_12s': RedmiNote12SWidget(), 'redmi_12_fire': Redmi12FireWidget(), 'poco_m3_pro': PocoM3ProWidget(), 'poco_m4_pro_4g': PocoM4Pro4GWidget(), 'poco_m4_pro_5g': PocoM4Pro5GWidget(), 'poco_c50': PocoC50Widget(), 'poco_c55': PocoC55Widget()}
        for modelo_id, widget in self.modelo_widgets.items():
            self.stacked.addWidget(widget)
        right_layout.addWidget(self.stacked)
        main_layout.addWidget(right_panel, stretch=1)
    def carregar_modelos(self):
        for nome, modelo_id in self.modelos:
            item = QListWidgetItem(nome)
            item.setData(Qt.UserRole, modelo_id)
            self.lista_modelos.addItem(item)
    def filtrar_modelos(self, texto):
        texto = texto.lower()
        for i in range(self.lista_modelos.count()):
            item = self.lista_modelos.item(i)
            item.setHidden(texto not in item.text().lower())
    def modelo_selecionado(self, index):
        if index >= 0:
            item = self.lista_modelos.item(index)
            modelo_id = item.data(Qt.UserRole)
            if modelo_id in self.modelo_widgets:
                widget = self.modelo_widgets[modelo_id]
                self.stacked.setCurrentWidget(widget)
    def showEvent(self, event):
        super().showEvent(event)
        self._aplicar_wordwrap_titulos()
    def _aplicar_wordwrap_titulos(self):
        for lbl in self.stacked.findChildren(QLabel):
            if not lbl.font().pointSize() >= 18:
                continue
            if lbl.font().bold():
                lbl.setWordWrap(True)
