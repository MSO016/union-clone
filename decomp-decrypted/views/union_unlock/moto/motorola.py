import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QListWidget, QListWidgetItem, QStackedWidget, QFrame, QApplication, QMainWindow)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from .moto_e6s import MotoE6sWidget
from .moto_e7 import MotoE7Widget
from .moto_e7_power import MotoE7PowerWidget
from .moto_e22 import MotoE22Widget
from .moto_e22i import MotoE22iWidget
from .moto_g05 import MotoG05Widget
from .moto_g06 import BromG06Widget
from .moto_g15 import MotoG15Widget
from .moto_g17 import BromG17Widget
from .moto_g22 import MotoG22Widget
from .mdm_spd_mtk import MdmSpdMtkWidget
from .moto_frp_old import MotoFrpOldWidget
from .moto_e22_mods.brom_e22 import CoresUnion
class MotorolaWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f'background-color: {CoresUnion.BACKGROUND};')
        self.setup_ui()
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.left_panel = QFrame()
        self.left_panel.setFixedWidth(330)
        self.left_panel.setStyleSheet(f'background-color: {CoresUnion.BACKGROUND_WHITE}; border-right: 1px solid {CoresUnion.BORDER};')
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(10, 15, 10, 15)
        left_layout.setSpacing(10)
        self.busqueda = QLineEdit()
        self.busqueda.setPlaceholderText('­ƒöì Buscar')
        self.busqueda.setFixedHeight(35)
        self.busqueda.setFont(QFont('Segoe UI', 11))
        self.busqueda.setStyleSheet(f'\n            QLineEdit {{\n                background-color: {CoresUnion.BACKGROUND};\n                border: 1px solid {CoresUnion.BORDER};\n                border-radius: 17px;\n                padding: 0 15px;\n                color: {CoresUnion.TEXT};\n            }}\n            QLineEdit:focus {{\n                border: 2px solid {CoresUnion.PRIMARY};\n            }}\n        ')
        self.busqueda.textChanged.connect(self.filtrar_modelo)
        left_layout.addWidget(self.busqueda)
        self.lista_modelos = QListWidget()
        self.lista_modelos.setFont(QFont('Segoe UI', 12))
        self.lista_modelos.setStyleSheet(f'\n            QListWidget {{\n                background-color: {CoresUnion.BACKGROUND_WHITE};\n                border: none;\n            }}\n            QListWidget::item {{\n                color: {CoresUnion.TEXT};\n                padding: 12px 15px;\n                border-radius: 8px;\n                margin: 2px 0;\n            }}\n            QListWidget::item:hover {{\n                background-color: {CoresUnion.BACKGROUND};\n            }}\n            QListWidget::item:selected {{\n                background-color: {CoresUnion.PRIMARY};\n                color: {CoresUnion.TEXT_WHITE};\n            }}\n        ')
        self.modelos = [('Moto E6s (XT2053)', 'moto_e6s'), ('Moto E7', 'moto_e7'), ('Moto E7 Power', 'moto_e7_power'), ('Moto E22', 'moto_e22'), ('Moto E22i', 'moto_e22i'), ('Moto G05', 'moto_g05'), ('Moto G06', 'moto_g06'), ('Moto G15', 'moto_g15'), ('Moto G17', 'moto_g17'), ('Moto G22', 'moto_g22'), ('MDM SPD/MTK', 'mdm_spd_mtk'), ('Moto Antigos', 'moto_frp_old')]
        for nome, id_modelo in self.modelos:
            item = QListWidgetItem(nome)
            item.setData(Qt.UserRole, id_modelo)
            self.lista_modelos.addItem(item)
        self.lista_modelos.currentItemChanged.connect(self._on_modelo_selected)
        left_layout.addWidget(self.lista_modelos)
        layout.addWidget(self.left_panel)
        self.right_panel = QStackedWidget()
        self.right_panel.setStyleSheet(f'background-color: {CoresUnion.BACKGROUND};')
        self.modelo_widgets = {'moto_e6s': MotoE6sWidget(), 'moto_e7': MotoE7Widget(), 'moto_e7_power': MotoE7PowerWidget(), 'moto_e22': MotoE22Widget(), 'moto_e22i': MotoE22iWidget(), 'moto_g05': MotoG05Widget(), 'moto_g06': BromG06Widget(), 'moto_g15': MotoG15Widget(), 'moto_g17': BromG17Widget(), 'moto_g22': MotoG22Widget(), 'mdm_spd_mtk': MdmSpdMtkWidget(), 'moto_frp_old': MotoFrpOldWidget()}
        for widget in self.modelo_widgets.values():
            self.right_panel.addWidget(widget)
        layout.addWidget(self.right_panel)
        self.lista_modelos.setCurrentRow(0)
    def filtrar_modelo(self, texto: str):
        texto = texto.lower()
        for i in range(self.lista_modelos.count()):
            item = self.lista_modelos.item(i)
            item.setHidden(texto not in item.text().lower())
    def _on_modelo_selected(self, current, previous):
        if current:
            id_modelo = current.data(Qt.UserRole)
            if id_modelo in self.modelo_widgets:
                self.right_panel.setCurrentWidget(self.modelo_widgets[id_modelo])
    def showEvent(self, event):
        super().showEvent(event)
        self._aplicar_wordwrap_titulos()
    def _aplicar_wordwrap_titulos(self):
        for lbl in self.right_panel.findChildren(QLabel):
            if not lbl.font().pointSize() >= 18:
                continue
            if lbl.font().bold():
                lbl.setWordWrap(True)
class MotorolaUnlockWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('­ƒöº Motorola Unlock - TECH UNION')
        self.setMinimumSize(900, 550)
        screen = QApplication.primaryScreen()
        if screen:
            sg = screen.availableGeometry()
            self.resize(min(1320, int(sg.width() * 0.85)), min(820, int(sg.height() * 0.85)))
        else:
            self.resize(1100, 700)
        self.setCentralWidget(MotorolaWidget())
def abrir_motorola_unlock(parent=None) -> MotorolaUnlockWindow:
    window = MotorolaUnlockWindow(parent)
    window.show()
    return window
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MotorolaUnlockWindow()
    window.show()
    sys.exit(app.exec_())
