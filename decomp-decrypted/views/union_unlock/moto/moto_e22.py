from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from .moto_e22_mods.brom_e22 import BromE22Widget, CoresUnion
class MotoE22Widget(QWidget):
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
        self.stacked.setStyleSheet(f'background-color: {CoresUnion.BACKGROUND};')
        self.brom_widget = BromE22Widget()
        self.stacked.addWidget(self.brom_widget)
        layout.addWidget(self.stacked)
        self.abrir_brom()
    def _estilo_ativo(self):
        return f'\n            QPushButton {{\n                background-color: {CoresUnion.PRIMARY};\n                color: {CoresUnion.TEXT_WHITE};\n                border: none;\n                border-radius: 16px;\n            }}\n        '
    def _estilo_inativo(self):
        return f'\n            QPushButton {{\n                background-color: {CoresUnion.BACKGROUND_DARK};\n                color: {CoresUnion.TEXT};\n                border: 1px solid {CoresUnion.BORDER};\n                border-radius: 16px;\n            }}\n            QPushButton:hover {{\n                background-color: {CoresUnion.BORDER};\n            }}\n        '
    def abrir_brom(self):
        self.stacked.setCurrentWidget(self.brom_widget)
        self.btn_brom.setStyleSheet(self._estilo_ativo())
