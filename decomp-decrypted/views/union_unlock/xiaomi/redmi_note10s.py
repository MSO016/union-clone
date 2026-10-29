from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from .redmi_note10s_mods.brom_note10s import BromNote10SWidget
from .brom_base import CoresUnion
class RedmiNote10SWidget(QWidget):
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
        self.btn_brom.setFixedSize(110, 36)
        self.btn_brom.setCursor(Qt.PointingHandCursor)
        self.btn_brom.setFont(QFont('Segoe UI', 11))
        self.btn_brom.clicked.connect(self.abrir_brom)
        mode_layout.addWidget(self.btn_brom)
        mode_layout.addStretch()
        layout.addWidget(self.frame_mode)
        self.stacked = QStackedWidget()
        self.brom_widget = BromNote10SWidget()
        self.stacked.addWidget(self.brom_widget)
        layout.addWidget(self.stacked)
        self.abrir_brom()
    def abrir_brom(self):
        self.stacked.setCurrentWidget(self.brom_widget)
        self.btn_brom.setStyleSheet(f'QPushButton {{ background-color: {CoresUnion.PRIMARY}; color: white; border: none; border-radius: 18px; }}')
