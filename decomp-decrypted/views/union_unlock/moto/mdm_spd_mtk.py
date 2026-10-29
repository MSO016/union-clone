from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from .mdm_spd_mtk_mods.mdm_spd_mtk import MdmSpdMtkWidget as MdmWidget, CoresUnion
class MdmSpdMtkWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f'background-color: {CoresUnion.BACKGROUND};')
        self.setup_ui()
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.frame_mode = QFrame()
        self.frame_mode.setFixedHeight(50)
        self.frame_mode.setStyleSheet(f'background-color: {CoresUnion.BACKGROUND};')
        mode_layout = QHBoxLayout(self.frame_mode)
        mode_layout.setContentsMargins(20, 10, 20, 10)
        mode_layout.setSpacing(10)
        mode_layout.setAlignment(Qt.AlignLeft)
        self.btn_fastboot = QPushButton('Fastboot Mode')
        self.btn_fastboot.setFixedSize(130, 36)
        self.btn_fastboot.setCursor(Qt.PointingHandCursor)
        self.btn_fastboot.setFont(QFont('Segoe UI', 11))
        self.btn_fastboot.clicked.connect(self.abrir_fastboot)
        mode_layout.addWidget(self.btn_fastboot)
        mode_layout.addStretch()
        layout.addWidget(self.frame_mode)
        self.stacked = QStackedWidget()
        self.mdm_widget = MdmWidget()
        self.stacked.addWidget(self.mdm_widget)
        layout.addWidget(self.stacked)
        self.abrir_fastboot()
    def abrir_fastboot(self):
        self.stacked.setCurrentWidget(self.mdm_widget)
        self.btn_fastboot.setStyleSheet(f'QPushButton {{ background-color: {CoresUnion.PRIMARY}; color: white; border: none; border-radius: 16px; }}')
