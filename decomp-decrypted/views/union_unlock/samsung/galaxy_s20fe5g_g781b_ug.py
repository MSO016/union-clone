from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QStackedWidget)
from .galaxy_s20fe5g_g781b_ug_mods import EdlS20FE5GG781bUGWidget
class GalaxyS20FE5GG781bUGWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        self.edl_widget = EdlS20FE5GG781bUGWidget()
        self.stack.addWidget(self.edl_widget)
        layout.addWidget(self.stack)
