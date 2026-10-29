'''
SAMSUNG QR CODE VIEWER
=====================
M├│dulo respons├ível por buscar e exibir QR Codes da tabela conteudos_dinamicos.
Este m├│dulo:
- Conecta ao MySQL usando as mesmas credenciais do sistema
- Busca o registro com t├¡tulo "qrcode"
- Exibe thumbnail_blob, arquivo_blob e descri├º├úo em uma janela compacta
- Segue os padr├Áes de seguran├ºa e estabilidade RESTORECELL
Autor: TECH UNION SOLUTIONS
Data: 2025-10-11
'''
import pymysql
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QWidget, QFrame)
from PyQt5.QtCore import (Qt, QByteArray, QThread, pyqtSignal)
from PyQt5.QtGui import QPixmap
import traceback
from app.utils._app_cfg import db_config
MYSQL_CONFIG = db_config(ssl={'ca': None}, ssl_verify_cert=False, cursorclass=pymysql.cursors.DictCursor)
class QRCodeLoaderThread(QThread):
    '''
    Thread para carregar dados do QR Code do MySQL de forma ass├¡ncrona.
    Evita travar a interface durante o carregamento.
    '''
    data_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    def run(self):
        '''Executa a busca no MySQL em background'''
        try:
            conn = pymysql.connect(**MYSQL_CONFIG)
            cursor = conn.cursor()
            query = '\n                SELECT \n                    id,\n                    titulo,\n                    descricao,\n                    thumbnail_blob,\n                    arquivo_blob,\n                    ativo\n                FROM conteudos_dinamicos\n                WHERE LOWER(titulo) LIKE %s\n                ORDER BY id ASC\n            '
            cursor.execute(query, ('%qrcode%',))
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            print(f'[QRCodeLoader] Busca executada: {len(results) if results else 0} registros encontrados')
            if results and len(results) > 0:
                ativos = [r for r in results if r.get('ativo') == 1]
                if ativos:
                    self.data_loaded.emit(ativos)
                    return
                self.error_occurred.emit('API_OFFLINE')
                return
        except Exception as e:
            error_msg = f'Erro ao carregar QR Code: {str(e)}'
            self.error_occurred.emit(error_msg)
            print(f'[QRCodeLoader] {error_msg}')
            print(traceback.format_exc())
        self.error_occurred.emit('Nenhum QR Code encontrado na tabela conteudos_dinamicos')
class QRCodeViewerDialog(QDialog):
    '''
    Janela compacta para exibir QR Codes.
    Exibe:
    - Thumbnail (miniatura)
    - Arquivo principal (imagem completa)
    - Descri├º├úo
    - Navega├º├úo entre m├║ltiplos QR Codes
    '''
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('­ƒô▒ QR Code Generator [8-16]')
        self.setModal(True)
        self.setMinimumSize(600, 500)
        self.resize(700, 600)
        self.loader_thread = None
        self.qrcode_list = []
        self.current_index = 0
        self.current_image_index = 0
        self.setup_ui()
        self.load_qrcode_data()
    def setup_ui(self):
        '''Configura a interface da janela'''
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        title_label = QLabel('­ƒô▒ QR Code Generator [8-16]')
        title_label.setStyleSheet('\n            QLabel {\n                font-size: 18px;\n                font-weight: bold;\n                color: #2c3e50;\n                padding: 10px;\n                background-color: #ecf0f1;\n                border-radius: 8px;\n            }\n        ')
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        nav_frame = QFrame()
        nav_frame.setStyleSheet('\n            QFrame {\n                background-color: #ffffff;\n                border-radius: 6px;\n                border: 2px solid #3498db;\n            }\n        ')
        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(10, 5, 10, 5)
        nav_layout.setSpacing(10)
        nav_frame.setLayout(nav_layout)
        self.btn_prev = QPushButton('ÔùÇ')
        self.btn_prev.setFixedSize(40, 40)
        self.btn_prev.setStyleSheet('\n            QPushButton {\n                background-color: #3498db;\n                color: white;\n                font-weight: bold;\n                font-size: 16px;\n                border-radius: 20px;\n                border: none;\n            }\n            QPushButton:hover {\n                background-color: #2980b9;\n            }\n            QPushButton:pressed {\n                background-color: #21618c;\n            }\n            QPushButton:disabled {\n                background-color: #bdc3c7;\n                color: #7f8c8d;\n            }\n        ')
        self.btn_prev.clicked.connect(self.show_previous)
        self.btn_prev.setEnabled(False)
        nav_layout.addWidget(self.btn_prev)
        self.nav_label = QLabel('QR Code 1 de 1')
        self.nav_label.setAlignment(Qt.AlignCenter)
        self.nav_label.setStyleSheet('\n            QLabel {\n                font-size: 14px;\n                font-weight: bold;\n                color: #2c3e50;\n                padding: 5px 15px;\n            }\n        ')
        nav_layout.addWidget(self.nav_label, 1)
        self.btn_next = QPushButton('ÔûÂ')
        self.btn_next.setFixedSize(40, 40)
        self.btn_next.setStyleSheet('\n            QPushButton {\n                background-color: #3498db;\n                color: white;\n                font-weight: bold;\n                font-size: 16px;\n                border-radius: 20px;\n                border: none;\n            }\n            QPushButton:hover {\n                background-color: #2980b9;\n            }\n            QPushButton:pressed {\n                background-color: #21618c;\n            }\n            QPushButton:disabled {\n                background-color: #bdc3c7;\n                color: #7f8c8d;\n            }\n        ')
        self.btn_next.clicked.connect(self.show_next)
        self.btn_next.setEnabled(False)
        nav_layout.addWidget(self.btn_next)
        self.nav_frame = nav_frame
        self.nav_frame.hide()
        layout.addWidget(nav_frame)
        image_nav_frame = QFrame()
        image_nav_frame.setStyleSheet('\n            QFrame {\n                background-color: #f8f9fa;\n                border-radius: 6px;\n                border: 2px solid #6c757d;\n            }\n        ')
        image_nav_layout = QHBoxLayout()
        image_nav_layout.setContentsMargins(10, 5, 10, 5)
        image_nav_layout.setSpacing(10)
        image_nav_frame.setLayout(image_nav_layout)
        self.btn_img_prev = QPushButton('ÔùÇ')
        self.btn_img_prev.setFixedSize(40, 40)
        self.btn_img_prev.setStyleSheet('\n            QPushButton {\n                background-color: #6c757d;\n                color: white;\n                font-weight: bold;\n                font-size: 16px;\n                border-radius: 20px;\n                border: none;\n            }\n            QPushButton:hover {\n                background-color: #5a6268;\n            }\n            QPushButton:pressed {\n                background-color: #4e555b;\n            }\n            QPushButton:disabled {\n                background-color: #bdc3c7;\n                color: #7f8c8d;\n            }\n        ')
        self.btn_img_prev.clicked.connect(self.show_previous_image)
        self.btn_img_prev.setEnabled(False)
        image_nav_layout.addWidget(self.btn_img_prev)
        self.image_nav_label = QLabel('Miniatura')
        self.image_nav_label.setAlignment(Qt.AlignCenter)
        self.image_nav_label.setStyleSheet('\n            QLabel {\n                font-size: 13px;\n                font-weight: bold;\n                color: #495057;\n                padding: 5px 15px;\n            }\n        ')
        image_nav_layout.addWidget(self.image_nav_label, 1)
        self.btn_img_next = QPushButton('ÔûÂ')
        self.btn_img_next.setFixedSize(40, 40)
        self.btn_img_next.setStyleSheet('\n            QPushButton {\n                background-color: #6c757d;\n                color: white;\n                font-weight: bold;\n                font-size: 16px;\n                border-radius: 20px;\n                border: none;\n            }\n            QPushButton:hover {\n                background-color: #5a6268;\n            }\n            QPushButton:pressed {\n                background-color: #4e555b;\n            }\n            QPushButton:disabled {\n                background-color: #bdc3c7;\n                color: #7f8c8d;\n            }\n        ')
        self.btn_img_next.clicked.connect(self.show_next_image)
        self.btn_img_next.setEnabled(True)
        image_nav_layout.addWidget(self.btn_img_next)
        self.image_nav_frame = image_nav_frame
        self.image_nav_frame.hide()
        layout.addWidget(image_nav_frame)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet('\n            QScrollArea {\n                border: none;\n                background-color: white;\n            }\n        ')
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(15)
        self.content_widget.setLayout(self.content_layout)
        self.loading_label = QLabel('ÔÅ│ Carregando QR Code do servidor...')
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet('\n            QLabel {\n                font-size: 14px;\n                color: #7f8c8d;\n                padding: 20px;\n            }\n        ')
        self.content_layout.addWidget(self.loading_label)
        scroll_area.setWidget(self.content_widget)
        layout.addWidget(scroll_area)
        close_btn = QPushButton('Ô£û Fechar')
        close_btn.setStyleSheet('\n            QPushButton {\n                background-color: #e74c3c;\n                color: white;\n                font-weight: bold;\n                padding: 10px 20px;\n                border-radius: 6px;\n                border: none;\n                font-size: 13px;\n            }\n            QPushButton:hover {\n                background-color: #c0392b;\n            }\n            QPushButton:pressed {\n                background-color: #a93226;\n            }\n        ')
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        self.setLayout(layout)
    def load_qrcode_data(self):
        '''Inicia o carregamento dos dados do QR Code'''
        self.loader_thread = QRCodeLoaderThread()
        self.loader_thread.data_loaded.connect(self.display_qrcode_data)
        self.loader_thread.error_occurred.connect(self.display_error)
        self.loader_thread.start()
    def display_qrcode_data(self, data_list):
        '''
Exibe os dados dos QR Codes na interface
Args:
    data_list (list): Lista de registros de QR Codes
'''
        self.loading_label.deleteLater()
        self.qrcode_list = data_list
        self.current_index = 0
        self.current_image_index = 0
        if len(self.qrcode_list) > 1:
            self.nav_frame.show()
            self.update_navigation()
        self.image_nav_frame.show()
        self.update_image_navigation()
        self.refresh_display()
    def show_previous(self):
        '''Mostra o QR Code anterior'''
        if self.current_index > 0:
            self.current_index -= 1
            self.current_image_index = 0
            self.update_navigation()
            self.update_image_navigation()
            self.refresh_display()
    def show_next(self):
        '''Mostra o pr├│ximo QR Code'''
        if self.current_index < len(self.qrcode_list) - 1:
            self.current_index += 1
            self.current_image_index = 0
            self.update_navigation()
            self.update_image_navigation()
            self.refresh_display()
    def update_navigation(self):
        '''Atualiza o estado dos bot├Áes de navega├º├úo e o label contador'''
        total = len(self.qrcode_list)
        current = self.current_index + 1
        self.nav_label.setText(f'QR Code {current} de {total}')
        self.btn_prev.setEnabled(self.current_index > 0)
        self.btn_next.setEnabled(self.current_index < total - 1)
    def show_previous_image(self):
        '''Mostra a imagem anterior (volta para thumbnail)'''
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.update_image_navigation()
            self.refresh_display()
    def show_next_image(self):
        '''Mostra a pr├│xima imagem (vai para arquivo)'''
        if self.current_image_index < 1:
            self.current_image_index += 1
            self.update_image_navigation()
            self.refresh_display()
    def update_image_navigation(self):
        '''Atualiza o estado dos bot├Áes de navega├º├úo de imagens'''
        if self.current_image_index == 0:
            self.image_nav_label.setText('­ƒû╝´©Å Miniatura')
        else:
            self.image_nav_label.setText('­ƒôÀ Imagem Completa')
        self.btn_img_prev.setEnabled(self.current_image_index > 0)
        self.btn_img_next.setEnabled(self.current_image_index < 1)
    def refresh_display(self):
        '''Atualiza o display com o QR Code atual'''
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if not widget:
                continue
            if widget != self.loading_label:
                widget.deleteLater()
        data = self.qrcode_list[self.current_index]
        if data.get('descricao'):
            desc_label = QLabel(data['descricao'])
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet('\n                QLabel {\n                    font-size: 13px;\n                    color: #34495e;\n                    padding: 10px;\n                    background-color: #ecf0f1;\n                    border-radius: 6px;\n                    border-left: 4px solid #3498db;\n                }\n            ')
            self.content_layout.addWidget(desc_label)
        blob_data = None
        if self.current_image_index == 0:
            blob_data = data.get('thumbnail_blob')
        else:
            blob_data = data.get('arquivo_blob')
        if blob_data and len(blob_data) > 100:
            image_widget = self.create_single_image(blob_data)
            self.content_layout.addWidget(image_widget)
        else:
            no_image_label = QLabel('ÔØî Imagem n├úo dispon├¡vel')
            no_image_label.setAlignment(Qt.AlignCenter)
            no_image_label.setStyleSheet('\n                QLabel {\n                    font-size: 14px;\n                    color: #e74c3c;\n                    padding: 40px;\n                    background-color: #fadbd8;\n                    border-radius: 8px;\n                    border: 2px dashed #e74c3c;\n                }\n            ')
            self.content_layout.addWidget(no_image_label)
        self.content_layout.addStretch()
    def create_single_image(self, blob_data):
        '''
Cria widget para exibir UMA imagem BLOB (sem t├¡tulo, tamanho maior)
Args:
    blob_data (bytes): Dados bin├írios da imagem
Returns:
    QLabel: Widget com a imagem
'''
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setStyleSheet('\n            QLabel {\n                background-color: #f8f9fa;\n                border-radius: 8px;\n                border: 2px solid #dee2e6;\n                padding: 20px;\n            }\n        ')
        try:
            pixmap = QPixmap()
            byte_array = QByteArray(blob_data)
            if pixmap.loadFromData(byte_array):
                if pixmap.width() > 500 or pixmap.height() > 500:
                    pixmap = pixmap.scaled(500, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                image_label.setPixmap(pixmap)
                return image_label
        except Exception as e:
            image_label.setText(f'ÔØî Erro: {str(e)}')
            image_label.setStyleSheet('\n                QLabel {\n                    color: #e74c3c;\n                    padding: 40px;\n                    background-color: #fadbd8;\n                    border-radius: 8px;\n                    border: 2px dashed #e74c3c;\n                }\n            ')
            print(f'[QRCodeViewer] Erro ao exibir imagem: {e}')
            print(traceback.format_exc())
            return image_label
        try:
            image_label.setText('ÔØî Erro ao carregar imagem')
            image_label.setStyleSheet('\n                    QLabel {\n                        color: #e74c3c;\n                        padding: 40px;\n                        background-color: #fadbd8;\n                        border-radius: 8px;\n                        border: 2px dashed #e74c3c;\n                    }\n                ')
        except Exception as e:
            image_label.setText(f'ÔØî Erro: {str(e)}')
            image_label.setStyleSheet('\n                QLabel {\n                    color: #e74c3c;\n                    padding: 40px;\n                    background-color: #fadbd8;\n                    border-radius: 8px;\n                    border: 2px dashed #e74c3c;\n                }\n            ')
            print(f'[QRCodeViewer] Erro ao exibir imagem: {e}')
            print(traceback.format_exc())
        return image_label
    def create_image_container(self, title, blob_data, max_width=250, max_height=250):
        '''
Cria um container para exibir uma imagem BLOB
Args:
    title (str): T├¡tulo do container
    blob_data (bytes): Dados bin├írios da imagem
    max_width (int): Largura m├íxima da imagem
    max_height (int): Altura m├íxima da imagem
Returns:
    QFrame: Container com a imagem
'''
        container = QFrame()
        container.setStyleSheet('\n            QFrame {\n                background-color: white;\n                border-radius: 6px;\n                border: 2px solid #dee2e6;\n            }\n        ')
        container_layout = QVBoxLayout()
        container_layout.setSpacing(10)
        container.setLayout(container_layout)
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet('\n            QLabel {\n                font-size: 12px;\n                font-weight: bold;\n                color: #495057;\n                padding: 5px;\n                background-color: #e9ecef;\n                border-radius: 4px;\n            }\n        ')
        container_layout.addWidget(title_label)
        try:
            pixmap = QPixmap()
            byte_array = QByteArray(blob_data)
            if pixmap.loadFromData(byte_array):
                if pixmap.width() > max_width or pixmap.height() > max_height:
                    pixmap = pixmap.scaled(max_width, max_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                image_label = QLabel()
                image_label.setPixmap(pixmap)
                image_label.setAlignment(Qt.AlignCenter)
                image_label.setStyleSheet('padding: 10px;')
                container_layout.addWidget(image_label)
                return container
        except Exception as e:
            error_label = QLabel(f'ÔØî Erro: {str(e)}')
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet('color: #e74c3c; padding: 20px;')
            container_layout.addWidget(error_label)
            print(f'[QRCodeViewer] Erro ao exibir imagem: {e}')
            print(traceback.format_exc())
            return container
        try:
            error_label = QLabel('ÔØî Erro ao carregar imagem')
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet('color: #e74c3c; padding: 20px;')
            container_layout.addWidget(error_label)
        except Exception as e:
            error_label = QLabel(f'ÔØî Erro: {str(e)}')
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet('color: #e74c3c; padding: 20px;')
            container_layout.addWidget(error_label)
            print(f'[QRCodeViewer] Erro ao exibir imagem: {e}')
            print(traceback.format_exc())
        return container
    def display_error(self, error_message):
        '''
Exibe mensagem de erro
Args:
    error_message (str): Mensagem de erro
'''
        if error_message == 'API_OFFLINE':
            self.loading_label.setText('ÔÜá´©Å API TEMPORARIAMENTE FORA DO AR\n\nOs QR Codes est├úo temporariamente indispon├¡veis.\n\n­ƒô× Entre em contato com o suporte t├®cnico ou aguarde.\n\nSuporte: RESTORECELL SOLU├ç├òES TECNOL├ôGICA')
            self.loading_label.setStyleSheet('\n                QLabel {\n                    font-size: 14px;\n                    font-weight: bold;\n                    color: #856404;\n                    padding: 30px;\n                    background-color: #fff3cd;\n                    border-radius: 8px;\n                    border-left: 5px solid #ffc107;\n                }\n            ')
            return
        self.loading_label.setText(f'ÔØî {error_message}')
        self.loading_label.setStyleSheet('\n                QLabel {\n                    font-size: 13px;\n                    color: #e74c3c;\n                    padding: 20px;\n                    background-color: #fadbd8;\n                    border-radius: 6px;\n                    border-left: 4px solid #e74c3c;\n                }\n            ')
def show_qrcode_viewer(parent=None):
    '''
Fun├º├úo auxiliar para abrir o visualizador de QR Code
Args:
    parent: Widget pai (opcional)
'''
    dialog = QRCodeViewerDialog(parent)
    dialog.exec_()
