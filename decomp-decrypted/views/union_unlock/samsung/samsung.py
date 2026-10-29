import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QListWidget, QListWidgetItem, QStackedWidget, QFrame, QApplication, QMainWindow)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from .galaxy_a02_all import GalaxyA02AllWidget
from .galaxy_a03s_all import GalaxyA03sAllWidget
from .galaxy_a04_all import GalaxyA04AllWidget
from .galaxy_a04e_all import GalaxyA04eAllWidget
from .galaxy_a05_all import GalaxyA05AllWidget
from .galaxy_a06_all import GalaxyA06AllWidget
from .galaxy_a10s_all import GalaxyA10sAllWidget
from .galaxy_a32_all import GalaxyA32AllWidget
from .galaxy_a055m_b13_mods import BromA055mB13Widget
from .galaxy_a01core_a013m import GalaxyA01CoreA013MWidget
from .galaxy_a02s_a025m import GalaxyA02sA025mWidget
from .galaxy_a05s_a057g_u7 import GalaxyA05sA057gU7Widget
from .galaxy_a05s_a057m import GalaxyA05sA057mWidget
from .galaxy_a05s_a057m_ub import GalaxyA05sA057mUBWidget
from .galaxy_a20s_a207f import GalaxyA20sA207fWidget
from .galaxy_a20s_a207m import GalaxyA20sA207mWidget
from .galaxy_a23_a235f_ua import GalaxyA23A235fUAWidget
from .galaxy_all_android_16 import GalaxyAllAndroid16Widget
from .galaxy_a23_a235n_u9 import GalaxyA23A235nU9Widget
from .galaxy_s20fe_g780g import GalaxyS20feG780gWidget
from .galaxy_taba_t295 import GalaxyTabAT295Widget
from .galaxy_s20fe5g_g781b_ug import GalaxyS20FE5GG781bUGWidget
from .galaxy_a23_a236m_ub import GalaxyA23A236mUBWidget
from .galaxy_a22_5g_a226br import GalaxyA22_5G_A226BRWidget
from .galaxy_a12_a125m import GalaxyA12A125mWidget
from .galaxy_a04_all_mods.brom_a04_all import CoresUnion
class SamsungWidget(QWidget):
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
        self.busqueda.setPlaceholderText('Buscar')
        self.busqueda.setFixedHeight(35)
        self.busqueda.setFont(QFont('Segoe UI', 11))
        self.busqueda.setStyleSheet(f'\n            QLineEdit {{\n                background-color: {CoresUnion.BACKGROUND};\n                border: 1px solid {CoresUnion.BORDER};\n                border-radius: 17px;\n                padding: 0 15px;\n                color: {CoresUnion.TEXT};\n            }}\n            QLineEdit:focus {{\n                border: 2px solid {CoresUnion.PRIMARY};\n            }}\n        ')
        self.busqueda.textChanged.connect(self.filtrar_modelo)
        left_layout.addWidget(self.busqueda)
        self.lista_modelos = QListWidget()
        self.lista_modelos.setFont(QFont('Segoe UI', 11))
        self.lista_modelos.setStyleSheet(f'\n            QListWidget {{\n                background-color: {CoresUnion.BACKGROUND_WHITE};\n                border: none;\n            }}\n            QListWidget::item {{\n                color: {CoresUnion.TEXT};\n                padding: 10px 12px;\n                border-radius: 8px;\n                margin: 2px 0;\n            }}\n            QListWidget::item:hover {{\n                background-color: {CoresUnion.BACKGROUND};\n            }}\n            QListWidget::item:selected {{\n                background-color: {CoresUnion.PRIMARY};\n                color: {CoresUnion.TEXT_WHITE};\n            }}\n        ')
        self.modelos = [('Galaxy Android 16 (Todos)', 'galaxy_all_android_16'), ('Galaxy A01 Core A013M', 'galaxy_a01core_a013m'), ('Galaxy A02 Todos', 'galaxy_a02_all'), ('Galaxy A02s A025M U9', 'galaxy_a02s_a025m'), ('Galaxy A03s Todos', 'galaxy_a03s_all'), ('Galaxy A04 Todos', 'galaxy_a04_all'), ('Galaxy A04e Todos', 'galaxy_a04e_all'), ('Galaxy A05 Todos', 'galaxy_a05_all'), ('[TP] Galaxy A05 A055M B13', 'galaxy_a055m_b13'), ('Galaxy A05s A057G U7', 'galaxy_a05s_a057g_u7'), ('Galaxy A05s A057M UA', 'galaxy_a05s_a057m'), ('Galaxy A05s A057M UB', 'galaxy_a05s_a057m_ub'), ('Galaxy A06 Todos', 'galaxy_a06_all'), ('Galaxy A10s Todos', 'galaxy_a10s_all'), ('Galaxy A12 A125M', 'galaxy_a12_a125m'), ('Galaxy A20s A207F U5', 'galaxy_a20s_a207f'), ('Galaxy A20s A207M U4', 'galaxy_a20s_a207m'), ('[TESTE] Galaxy A22 5G A226BR', 'galaxy_a22_5g_a226br'), ('Galaxy A23 A235F UA', 'galaxy_a23_a235f_ua'), ('Galaxy A23 A236M UB', 'galaxy_a23_a236m_ub'), ('Galaxy A23 A235N U9', 'galaxy_a23_a235n_u9'), ('Galaxy A32 Todos', 'galaxy_a32_all'), ('Galaxy S20 FE G780G', 'galaxy_s20fe_g780g'), ('Galaxy S20 FE 5G G781B UG', 'galaxy_s20fe5g_g781b_ug'), ('Galaxy Tab A 8.0 T295', 'galaxy_taba_t295')]
        for nome, id_modelo in self.modelos:
            item = QListWidgetItem(nome)
            item.setData(Qt.UserRole, id_modelo)
            self.lista_modelos.addItem(item)
        self.lista_modelos.currentItemChanged.connect(self._on_modelo_selected)
        left_layout.addWidget(self.lista_modelos)
        layout.addWidget(self.left_panel)
        self.right_panel = QStackedWidget()
        self.right_panel.setStyleSheet(f'background-color: {CoresUnion.BACKGROUND};')
        self.modelo_widgets = {'galaxy_a02_all': GalaxyA02AllWidget(), 'galaxy_a03s_all': GalaxyA03sAllWidget(), 'galaxy_a04_all': GalaxyA04AllWidget(), 'galaxy_a04e_all': GalaxyA04eAllWidget(), 'galaxy_a05_all': GalaxyA05AllWidget(), 'galaxy_a06_all': GalaxyA06AllWidget(), 'galaxy_a10s_all': GalaxyA10sAllWidget(), 'galaxy_a32_all': GalaxyA32AllWidget(), 'galaxy_a055m_b13': BromA055mB13Widget(), 'galaxy_a01core_a013m': GalaxyA01CoreA013MWidget(), 'galaxy_a02s_a025m': GalaxyA02sA025mWidget(), 'galaxy_a05s_a057g_u7': GalaxyA05sA057gU7Widget(), 'galaxy_a05s_a057m': GalaxyA05sA057mWidget(), 'galaxy_a05s_a057m_ub': GalaxyA05sA057mUBWidget(), 'galaxy_a20s_a207f': GalaxyA20sA207fWidget(), 'galaxy_a20s_a207m': GalaxyA20sA207mWidget(), 'galaxy_all_android_16': GalaxyAllAndroid16Widget(), 'galaxy_a23_a235f_ua': GalaxyA23A235fUAWidget(), 'galaxy_a23_a235n_u9': GalaxyA23A235nU9Widget(), 'galaxy_s20fe_g780g': GalaxyS20feG780gWidget(), 'galaxy_taba_t295': GalaxyTabAT295Widget(), 'galaxy_s20fe5g_g781b_ug': GalaxyS20FE5GG781bUGWidget(), 'galaxy_a23_a236m_ub': GalaxyA23A236mUBWidget(), 'galaxy_a22_5g_a226br': GalaxyA22_5G_A226BRWidget(), 'galaxy_a12_a125m': GalaxyA12A125mWidget()}
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
class SamsungUnlockWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Samsung Unlock - TECH UNION')
        self.setMinimumSize(900, 550)
        screen = QApplication.primaryScreen()
        if screen:
            sg = screen.availableGeometry()
            self.resize(min(1320, int(sg.width() * 0.85)), min(820, int(sg.height() * 0.85)))
        else:
            self.resize(1100, 700)
        self.setCentralWidget(SamsungWidget())
def abrir_samsung_unlock(parent=None) -> SamsungUnlockWindow:
    window = SamsungUnlockWindow(parent)
    window.show()
    return window
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = SamsungUnlockWindow()
    window.show()
    sys.exit(app.exec_())
