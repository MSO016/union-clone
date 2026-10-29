from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QScrollArea, QWidget, QFrame, QGroupBox, QApplication)
from PyQt5.QtCore import (Qt, QSize, QByteArray, QBuffer)
from PyQt5.QtGui import QPixmap, QImage
from app.utils.window_protection import protect_window_from_capture_extended
import fitz
import io
class ImageViewer(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 800)
        self.setAlignment(Qt.AlignCenter)
        self._pixmap = None
        self.scale_factor = 1.0
    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        self._update_pixmap()
    def _update_pixmap(self):
        if self._pixmap:
            available_size = self.size()
            scaled_size = self._pixmap.size()
            if scaled_size.width() <= available_size.width() and scaled_size.height() <= available_size.height():
                scaled_pixmap = self._pixmap
            else:
                scaled_pixmap = self._pixmap.scaled(available_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            if self.scale_factor != 1.0:
                scaled_pixmap = self._pixmap.scaled(self._pixmap.size() * self.scale_factor, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            super().setPixmap(scaled_pixmap)
    def zoom_in(self):
        self.scale_factor *= 1.25
        self._update_pixmap()
    def zoom_out(self):
        self.scale_factor *= 0.8
        self._update_pixmap()
    def reset_zoom(self):
        self.scale_factor = 1.0
        self._update_pixmap()
class ImageViewerDialog(QDialog):
    def __init__(self, title, image_data=None, pdf_data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        screen = parent.screen().availableGeometry()
        self.resize(int(screen.width() * 0.9), int(screen.height() * 0.9))
        layout = QVBoxLayout(self)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignCenter)
        self.image_viewer = ImageViewer()
        container_layout.addWidget(self.image_viewer)
        scroll_area.setWidget(container)
        if image_data:
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            self.image_viewer.setPixmap(pixmap)
        elif pdf_data:
            try:
                doc = fitz.open(stream=pdf_data, filetype='pdf')
                page = doc[0]
                zoom = 4
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(img)
                self.image_viewer.setPixmap(pixmap)
                doc.close()
            except Exception as e:
                print(f'Erro ao carregar PDF: {str(e)}')
        button_layout = QHBoxLayout()
        btn_zoom_in = QPushButton('Aumentar (+)')
        btn_zoom_out = QPushButton('Diminuir (-)')
        btn_reset = QPushButton('Resetar Zoom')
        btn_close = QPushButton('Fechar')
        for btn in btn_zoom_in, btn_zoom_out, btn_reset, btn_close:
            btn.setMinimumWidth(120)
            btn.setMinimumHeight(40)
            button_layout.addWidget(btn)
        btn_zoom_in.clicked.connect(self.image_viewer.zoom_in)
        btn_zoom_out.clicked.connect(self.image_viewer.zoom_out)
        btn_reset.clicked.connect(self.image_viewer.reset_zoom)
        btn_close.clicked.connect(self.close)
        layout.addWidget(scroll_area)
        layout.addLayout(button_layout)
        self.setStyleSheet('\n            QDialog {\n                background-color: #f0f0f0;\n            }\n            QPushButton {\n                background-color: #2196F3;\n                color: white;\n                border: none;\n                padding: 10px;\n                border-radius: 4px;\n                min-width: 120px;\n                font-size: 12px;\n            }\n            QPushButton:hover {\n                background-color: #1976D2;\n            }\n            QScrollArea {\n                border: 1px solid #ddd;\n                background-color: white;\n            }\n        ')
class ViewSolutionDialog(QDialog):
    def __init__(self, solution_id, parent=None):
        super().__init__(parent)
        self.solution_id = solution_id
        self.solutions_manager = parent.solutions_manager
        self.solution = self.solutions_manager.get_solution_by_id(solution_id)
        self.is_admin = parent.is_admin if hasattr(parent, 'is_admin') else False
        self.setWindowTitle('Visualizar Solu├º├úo')
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        screen = QApplication.primaryScreen().availableGeometry()
        self.setMinimumSize(int(screen.width() * 0.7), int(screen.height() * 0.7))
        if not self.is_admin:
            protect_window_from_capture_extended(self, True)
        self.setup_ui()
        self.load_solution()
    def setup_ui(self):
        '''Configura a interface do di├ílogo'''
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        for label_text, value in ('Marca:', self.solution.get('marca', '')), ('Modelo:', self.solution.get('modelo', '')), ('Descri├º├úo:', self.solution.get('descricao', '')), ('Observa├º├Áes:', self.solution.get('observacoes', '')):
            label = QLabel(label_text)
            label.setStyleSheet('font-weight: bold;')
            text = QLabel(value)
            text.setWordWrap(True)
            text.setTextInteractionFlags(Qt.TextSelectableByMouse)
            main_layout.addWidget(label)
            main_layout.addWidget(text)
            main_layout.addSpacing(10)
        media_container = QWidget()
        media_layout = QHBoxLayout(media_container)
        if self.solution.get('imagem_blob'):
            imagem_group = QGroupBox('Imagem')
            imagem_layout = QVBoxLayout(imagem_group)
            self.imagem_label = QLabel()
            self.imagem_label.setAlignment(Qt.AlignCenter)
            imagem_scroll = QScrollArea()
            imagem_scroll.setWidget(self.imagem_label)
            imagem_scroll.setWidgetResizable(True)
            zoom_layout = QHBoxLayout()
            zoom_in_btn = QPushButton('Aumentar (+)')
            zoom_out_btn = QPushButton('Diminuir (-)')
            reset_zoom_btn = QPushButton('Resetar Zoom')
            zoom_layout.addWidget(zoom_in_btn)
            zoom_layout.addWidget(zoom_out_btn)
            zoom_layout.addWidget(reset_zoom_btn)
            imagem_layout.addLayout(zoom_layout)
            imagem_layout.addWidget(imagem_scroll)
            media_layout.addWidget(imagem_group)
            self.zoom_factor = 1.0
            zoom_in_btn.clicked.connect((lambda: self.zoom_image(1.2)))
            zoom_out_btn.clicked.connect((lambda: self.zoom_image(0.8)))
            reset_zoom_btn.clicked.connect(self.reset_zoom)
        if self.solution.get('diagrama_blob'):
            diagrama_group = QGroupBox('Diagrama')
            diagrama_layout = QVBoxLayout(diagrama_group)
            self.diagrama_label = QLabel()
            self.diagrama_label.setAlignment(Qt.AlignCenter)
            diagrama_scroll = QScrollArea()
            diagrama_scroll.setWidget(self.diagrama_label)
            diagrama_scroll.setWidgetResizable(True)
            zoom_layout = QHBoxLayout()
            zoom_in_btn = QPushButton('Aumentar (+)')
            zoom_out_btn = QPushButton('Diminuir (-)')
            reset_zoom_btn = QPushButton('Resetar Zoom')
            zoom_layout.addWidget(zoom_in_btn)
            zoom_layout.addWidget(zoom_out_btn)
            zoom_layout.addWidget(reset_zoom_btn)
            diagrama_layout.addLayout(zoom_layout)
            diagrama_layout.addWidget(diagrama_scroll)
            media_layout.addWidget(diagrama_group)
            self.zoom_factor_diagrama = 1.0
            zoom_in_btn.clicked.connect((lambda: self.zoom_diagram(1.2)))
            zoom_out_btn.clicked.connect((lambda: self.zoom_diagram(0.8)))
            reset_zoom_btn.clicked.connect(self.reset_zoom_diagram)
        main_layout.addWidget(media_container)
        btn_fechar = QPushButton('Fechar')
        btn_fechar.clicked.connect(self.close)
        main_layout.addWidget(btn_fechar)
        scroll.setWidget(main_widget)
        layout.addWidget(scroll)
    def load_solution(self):
        '''Carrega os dados da solu├º├úo'''
        if self.solution.get('imagem_blob'):
            pixmap = QPixmap()
            pixmap.loadFromData(self.solution['imagem_blob'])
            if not pixmap.isNull():
                self.original_image = pixmap
                self.imagem_label.setPixmap(pixmap)
        if self.solution.get('diagrama_blob'):
            try:
                pdf_document = fitz.open(stream=self.solution['diagrama_blob'], filetype='pdf')
                first_page = pdf_document[0]
                zoom = 2
                mat = fitz.Matrix(zoom, zoom)
                pix = first_page.get_pixmap(matrix=mat)
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(img)
                self.original_diagram = pixmap
                self.diagrama_label.setPixmap(pixmap)
                self.is_diagram_pdf = True
                self.pdf_document = pdf_document
            except:
                pixmap = QPixmap()
                pixmap.loadFromData(self.solution['diagrama_blob'])
                if not pixmap.isNull():
                    self.original_diagram = pixmap
                    self.diagrama_label.setPixmap(pixmap)
                    self.is_diagram_pdf = False
    def zoom_image(self, factor):
        '''Aplica zoom na imagem'''
        if hasattr(self, 'original_image'):
            self.zoom_factor *= factor
            scaled_pixmap = self.original_image.scaled(int(self.original_image.width() * self.zoom_factor), int(self.original_image.height() * self.zoom_factor), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.imagem_label.setPixmap(scaled_pixmap)
    def reset_zoom(self):
        '''Reseta o zoom da imagem'''
        if hasattr(self, 'original_image'):
            self.zoom_factor = 1.0
            self.imagem_label.setPixmap(self.original_image)
    def zoom_diagram(self, factor):
        '''Aplica zoom no diagrama'''
        if hasattr(self, 'original_diagram'):
            self.zoom_factor_diagrama *= factor
            if hasattr(self, 'is_diagram_pdf') and self.is_diagram_pdf:
                first_page = self.pdf_document[0]
                zoom = 2 * self.zoom_factor_diagrama
                mat = fitz.Matrix(zoom, zoom)
                pix = first_page.get_pixmap(matrix=mat)
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(img)
            else:
                pixmap = self.original_diagram.scaled(int(self.original_diagram.width() * self.zoom_factor_diagrama), int(self.original_diagram.height() * self.zoom_factor_diagrama), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.diagrama_label.setPixmap(pixmap)
    def reset_zoom_diagram(self):
        '''Reseta o zoom do diagrama'''
        if hasattr(self, 'original_diagram'):
            self.zoom_factor_diagrama = 1.0
            if hasattr(self, 'is_diagram_pdf') and self.is_diagram_pdf:
                first_page = self.pdf_document[0]
                zoom = 2
                mat = fitz.Matrix(zoom, zoom)
                pix = first_page.get_pixmap(matrix=mat)
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(img)
            else:
                pixmap = self.original_diagram
            self.diagrama_label.setPixmap(pixmap)
    def closeEvent(self, event):
        '''Evento chamado quando o di├ílogo ├® fechado'''
        if hasattr(self, 'pdf_document'):
            self.pdf_document.close()
        super().closeEvent(event)
