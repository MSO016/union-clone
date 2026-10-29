from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame, QPushButton, QGraphicsDropShadowEffect, QGridLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import (QPixmap, QDesktopServices, QIcon, QColor)
from PyQt5.QtCore import QUrl
import os
PARCEIROS = [{'nome': 'RESTORECELL Solu├º├Áes tecnol├│gicas', 'descricao': 'Reparos de smartphones e treinamentos de manuten├º├úo de smartphones!', 'endereco': 'Av. Godofredo Maciel, 1178, 2┬║ piso - Sala C Parangaba, Fortaleza', 'telefone': '(85)98963-4058', 'instagram': '@restorecell10', 'logo': 'restorecell.png'}, {'nome': 'RAMONCELL', 'descricao': 'Assistencia t├®cnica e treinamentos', 'endereco': 'Rua E,185 canindezinho', 'telefone': '(85)986534210', 'instagram': '@ramoncell7', 'logo': 'ramon.jpg'}, {'nome': 'VIPCELL', 'descricao': 'Reparos em smartphones e treinamentos presencial', 'endereco': 'Avenida santo amaro - Villa Kennedy, Caruaru-PE', 'telefone': '(81)992024197', 'instagram': '@vipcell_numero1', 'logo': 'vipcell.jpg'}, {'nome': 'Bionic Tech - Solu├º├Áes Apple', 'descricao': 'Especialista em placas de iPhones e Android', 'endereco': 'Avenida Barreto de Menezes - Dentro do Mercado das Mangueiras - Prazeres, Jaboat├úo dos Guararapes - PE, 54315-000', 'telefone': '(81)99754-2545', 'instagram': '@bionictech.apple', 'logo': 'bionic.jpg'}, {'nome': 'IBRAFIX', 'descricao': 'Especialista em reparos e solu├º├Áes t├®cnicas', 'endereco': 'Rua E, 185 canidezinho Fortaleza Cear├í', 'telefone': '(85)99670-9072', 'instagram': '@carlos_ibrafix', 'logo': 'ibrafix.jpg'}, {'nome': 'JT assist├¬ncia tech', 'descricao': 'Assist├¬ncia T├®cnica Em Smartphone e Inform├ítica.', 'endereco': 'Rua palm├ícia 656 jardim Guanabara', 'telefone': '+55 85994111533', 'instagram': '@j.t.assistencia_tecnica', 'logo': 'jt.jpg'}, {'nome': 'JOTACELL', 'descricao': 'Assist├¬ncia t├®cnica especializada em smartphones', 'endereco': 'Algod├Áes - BA, CEP: 48832-000', 'telefone': '(75)98705-0924', 'instagram': '@jotacellservices', 'logo': 'jotacell.jpg'}, {'nome': 'DAPLE', 'descricao': 'Suporte remoto e assist├¬ncia t├®cnica especializada', 'endereco': 'Rua terceira avenida 77, bairro centro, Balne├írio Cambori├║ - SC', 'telefone': '(47)99978-8974', 'instagram': '@daple.remoto', 'logo': 'daple.jpg'}, {'nome': 'MAICONCELL', 'descricao': 'Assist├¬ncia t├®cnica especializada em smartphones', 'endereco': 'Av Jo├úo De Lauro cidade Jardim 1789', 'telefone': '(77)99825-3602', 'instagram': '@maiconcell_', 'logo': 'maiconcell.jpg'}, {'nome': 'WILLIAN SERVER BR', 'descricao': 'Assist├¬ncia T├®cnica Em Smartphone e Inform├ítica.', 'endereco': 'Cear├í - Brasil', 'telefone': '+55 88 99802-2869', 'instagram': '@willian.server.br', 'logo': 'willian.jpg'}, {'nome': 'M.F ASSIST├èNCIA T├ëCNICA', 'descricao': 'Assist├¬ncia t├®cnica especializada em smartphones', 'endereco': 'Av Denizar Trevizani 1861 Aeroporto 3, Franca - SP', 'telefone': '(16)99108-9731', 'instagram': '@mfassistencia.tec', 'logo': 'mf.jpg'}, {'nome': 'METACELMASTER', 'descricao': 'Especializado em software de smartphone', 'endereco': 'Belo Horizonte - MG', 'telefone': '(37)99386-6972', 'instagram': '@metacelmaster', 'logo': 'meta.jpg'}, {'nome': 'MARTECH Cursos de Software EAD', 'descricao': 'Cursos de software EAD', 'endereco': 'Bras├¡lia - DF', 'telefone': '(61)98564-3981', 'instagram': '@martech.cursos.software', 'logo': 'martech.jpg'}, {'nome': 'DR.IPHONE', 'descricao': 'Treinamentos especializados e especialista em IPHONES!', 'endereco': 'Av. Washington Soares, 4567 - Edson Queiroz, Fortaleza', 'telefone': '(85)988026475', 'instagram': '@dr.iphonefortaleza', 'logo': 'driphone.png'}, {'nome': 'VictorCell Ferramentas', 'descricao': 'Especialista em ferramentas para t├®cnicos.', 'endereco': 'F5 Box 1283 - 1282 - 1246, Beco da Poeira, Av. Imperador, 546 - Centro, Fortaleza - CE', 'telefone': '(88)99647-6113', 'instagram': '@victor_ferramentas', 'logo': 'victorcell.png'}, {'nome': 'MR CELULAR', 'descricao': 'Assist├¬ncia t├®cnica especializada em smartphone', 'endereco': 'Av. M├írio Homem de Melo, 2216, box 4, Mecejana - Boa Vista-RR', 'telefone': '(95)99128-9284', 'instagram': '@mr_celular__', 'logo': 'marcosmodera.jpeg'}]
class ParceirosWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
    def setup_ui(self):
        self.setWindowTitle('Parceiros')
        self.setMinimumSize(1200, 800)
        icon = QIcon('app/resources/icon.png')
        self.setWindowIcon(icon)
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        header = QHBoxLayout()
        btn_voltar = QPushButton('ÔåÉ Voltar')
        btn_voltar.setStyleSheet('\n            QPushButton {\n                background-color: #2196F3;\n                color: white;\n                border: none;\n                padding: 10px 20px;\n                border-radius: 5px;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background-color: #1976D2;\n            }\n        ')
        btn_voltar.clicked.connect(self.voltar)
        header.addWidget(btn_voltar)
        title = QLabel('Nossos Parceiros')
        title.setStyleSheet('\n            font-size: 28px;\n            font-weight: bold;\n            color: #1976D2;\n            margin: 0 20px;\n        ')
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('\n            QScrollArea {\n                border: none;\n                background: transparent;\n            }\n        ')
        content = QWidget()
        content_layout = QGridLayout(content)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(10, 10, 10, 10)
        row = col = 0
        for parceiro in PARCEIROS:
            card = self.criar_card_parceiro(parceiro)
            content_layout.addWidget(card, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1
        scroll.setWidget(content)
        layout.addWidget(scroll)
    def criar_card_parceiro(self, parceiro):
        card = QFrame()
        card.setStyleSheet('\n            QFrame {\n                background: white;\n                border-radius: 8px;\n                padding: 10px;\n                border: 1px solid rgba(0, 0, 0, 0.1);\n            }\n            QFrame:hover {\n                border: 1px solid #2196F3;\n            }\n        ')
        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        logo_container = QLabel()
        logo_container.setFixedSize(200, 120)
        logo_container.setStyleSheet('\n            QLabel {\n                background: white;\n                qproperty-alignment: AlignCenter;\n            }\n        ')
        logo_path = os.path.join('app/resources/parceiros', parceiro['logo'])
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaled(200, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_container.setPixmap(scaled_pixmap)
            logo_container.setAlignment(Qt.AlignCenter)
        logo_frame = QFrame()
        logo_frame.setStyleSheet('background: white;')
        logo_layout = QHBoxLayout(logo_frame)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.addWidget(logo_container, alignment=Qt.AlignCenter)
        layout.addWidget(logo_frame)
        nome = QLabel(parceiro['nome'])
        nome.setStyleSheet('\n            font-size: 16px;\n            font-weight: bold;\n            color: #333333;\n        ')
        nome.setWordWrap(True)
        nome.setAlignment(Qt.AlignCenter)
        layout.addWidget(nome)
        descricao = QLabel(parceiro['descricao'])
        descricao.setStyleSheet('color: #555555;')
        descricao.setWordWrap(True)
        descricao.setAlignment(Qt.AlignCenter)
        layout.addWidget(descricao)
        endereco = QLabel(parceiro['endereco'])
        endereco.setStyleSheet('color: #666666;')
        endereco.setWordWrap(True)
        endereco.setAlignment(Qt.AlignCenter)
        layout.addWidget(endereco)
        contato = QLabel(f'Contato: {parceiro['telefone']}')
        contato.setAlignment(Qt.AlignCenter)
        layout.addWidget(contato)
        instagram = QPushButton(parceiro['instagram'])
        instagram.setCursor(Qt.PointingHandCursor)
        instagram.setStyleSheet('\n            QPushButton {\n                color: #1da1f2;\n                border: 1px solid #1da1f2;\n                border-radius: 5px;\n                padding: 5px 10px;\n                background-color: white;\n            }\n            QPushButton:hover {\n                background-color: #1da1f2;\n                color: white;\n            }\n        ')
        instagram.clicked.connect((lambda: QDesktopServices.openUrl(QUrl(f'https://instagram.com/{parceiro['instagram'].replace('@', '')}'))))
        layout.addWidget(instagram, alignment=Qt.AlignCenter)
        return card
    def voltar(self):
        '''Close partners window and show parent'''
        self.close()
        if self.parent:
            self.parent.show()
