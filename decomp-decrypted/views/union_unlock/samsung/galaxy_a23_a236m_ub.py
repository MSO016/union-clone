from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QStackedWidget)
from .galaxy_a23_a236m_ub_mods import EdlA23A236mUBWidget
class GalaxyA23A236mUBWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        self.edl_widget = EdlA23A236mUBWidget()
        self.stack.addWidget(self.edl_widget)
        layout.addWidget(self.stack)
