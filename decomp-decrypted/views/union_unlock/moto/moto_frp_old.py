from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from .moto_frp_old_mods.frp_old import FrpOldWidget, CoresUnion
class MotoFrpOldWidget(QWidget):
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
        self.btn_factory = QPushButton('Factory Mode')
        self.btn_factory.setFixedSize(130, 36)
        self.btn_factory.setCursor(Qt.PointingHandCursor)
        self.btn_factory.setFont(QFont('Segoe UI', 11))
        self.btn_factory.clicked.connect(self.abrir_factory)
        mode_layout.addWidget(self.btn_factory)
        mode_layout.addStretch()
        layout.addWidget(self.frame_mode)
        self.stacked = QStackedWidget()
        self.factory_widget = FrpOldWidget()
        self.stacked.addWidget(self.factory_widget)
        layout.addWidget(self.stacked)
        self.abrir_factory()
    def abrir_factory(self):
        self.stacked.setCurrentWidget(self.factory_widget)
        self.btn_factory.setStyleSheet(f'QPushButton {{ background-color: {CoresUnion.PRIMARY}; color: white; border: none; border-radius: 16px; }}')
