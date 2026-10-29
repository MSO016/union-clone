from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QStackedWidget)
from .galaxy_taba_t295_mods import EdlTabAT295Widget
class GalaxyTabAT295Widget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        self.edl_widget = EdlTabAT295Widget()
        self.stack.addWidget(self.edl_widget)
        layout.addWidget(self.stack)
