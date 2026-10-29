from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from .poco_c50_mods.brom_poco_c50 import BromPocoC50Widget
from .brom_base import CoresUnion
class PocoC50Widget(QWidget):
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
        self.btn_brom = QPushButton('BROM Mode')
        self.btn_brom.setFixedSize(120, 36)
        self.btn_brom.setCursor(Qt.PointingHandCursor)
        self.btn_brom.setFont(QFont('Segoe UI', 11))
        self.btn_brom.setStyleSheet(f'QPushButton {{ background-color: {CoresUnion.PRIMARY}; color: white; border: none; border-radius: 16px; }}')
        mode_layout.addWidget(self.btn_brom)
        mode_layout.addStretch()
        layout.addWidget(self.frame_mode)
        self.stacked = QStackedWidget()
        self.brom_widget = BromPocoC50Widget()
        self.stacked.addWidget(self.brom_widget)
        layout.addWidget(self.stacked)
