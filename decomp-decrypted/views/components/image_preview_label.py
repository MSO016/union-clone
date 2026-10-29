from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt
class ImagePreviewLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMinimumSize(200, 200)
        self.setMaximumSize(200, 200)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet('\n            QLabel {\n                background-color: #f5f6fa;\n                border: 2px dashed #dcdde1;\n                border-radius: 5px;\n            }\n        ')
        self.setText('Sem imagem')
    def setPixmap(self, pixmap):
        if pixmap:
            scaled = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            super().setPixmap(scaled)
            return
        self.clear()
        self.setText('Sem imagem')
