from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from .galaxy_all_android_16_mods.mtp_all_android_16 import MtpAllAndroid16Widget
from .galaxy_a04_all_mods.brom_a04_all import CoresUnion
class GalaxyAllAndroid16Widget(QWidget):
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
        self.btn_mtp = QPushButton('MTP Mode')
        self.btn_mtp.setFixedSize(110, 36)
        self.btn_mtp.setCursor(Qt.PointingHandCursor)
        self.btn_mtp.setFont(QFont('Segoe UI', 11))
        self.btn_mtp.setStyleSheet(f'QPushButton {{ background-color: {CoresUnion.PRIMARY}; color: white; border: none; border-radius: 16px; }}')
        mode_layout.addWidget(self.btn_mtp)
        mode_layout.addStretch()
        layout.addWidget(self.frame_mode)
        self.stacked = QStackedWidget()
        self.mtp_widget = MtpAllAndroid16Widget()
        self.stacked.addWidget(self.mtp_widget)
        layout.addWidget(self.stacked)
