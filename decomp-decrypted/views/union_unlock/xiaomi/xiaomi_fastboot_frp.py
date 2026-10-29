from PyQt5.QtWidgets import QWidget, QVBoxLayout
from .xiaomi_fastboot_frp_mods.fastboot_frp import FastbootFrpWidget
class XiaomiFastbootFrpWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.fastboot_widget = FastbootFrpWidget()
        layout.addWidget(self.fastboot_widget)
