from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QScrollArea, QWidget, QFrame, QComboBox, QTextEdit)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import sqlite3
class ClientForm(QDialog):
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle('Cadastro de Cliente')
        self.setModal(True)
        self.setMinimumSize(1000, 700)
        self.showMaximized()
        self.setup_ui()
    def setup_ui(self):
        '''Configura a interface seguindo o padr├úo das outras telas'''
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        header_frame = QFrame()
        header_frame.setStyleSheet('\n            QFrame {\n                background-color: #f8f9fa;\n                border-bottom: 1px solid #dee2e6;\n                padding: 10px;\n            }\n        ')
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 10, 20, 10)
        voltar_btn = QPushButton('ÔåÉ Voltar')
        voltar_btn.setStyleSheet('\n            QPushButton {\n                background-color: #6c757d;\n                color: white;\n                border: none;\n                padding: 8px 16px;\n                border-radius: 4px;\n                font-weight: bold;\n                font-size: 14px;\n            }\n            QPushButton:hover {\n                background-color: #545b62;\n            }\n        ')
        voltar_btn.clicked.connect(self.reject)
        header_layout.addWidget(voltar_btn)
        titulo = QLabel('Cadastro de Cliente')
        titulo.setStyleSheet('\n            QLabel {\n                font-size: 18px;\n                font-weight: bold;\n                color: #2c3e50;\n                margin-left: 20px;\n            }\n        ')
        header_layout.addWidget(titulo)
        header_layout.addStretch()
        main_layout.addWidget(header_frame)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        self.criar_secao_info_basicas(layout)
        self.criar_secao_contato(layout)
        self.criar_secao_classificacao(layout)
        self.criar_botoes_acao(layout)
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
    def criar_secao_info_basicas(self, layout):
        '''Cria se├º├úo com informa├º├Áes b├ísicas do cliente'''
        secao_frame = QFrame()
        secao_frame.setStyleSheet('\n            QFrame {\n                background-color: white;\n                border: 1px solid #dee2e6;\n                border-radius: 8px;\n                padding: 15px;\n            }\n        ')
        secao_layout = QVBoxLayout(secao_frame)
        titulo = QLabel('­ƒôï Informa├º├Áes B├ísicas')
        titulo.setStyleSheet('\n            QLabel {\n                font-size: 16px;\n                font-weight: bold;\n                color: #2c3e50;\n                margin-bottom: 10px;\n            }\n        ')
        secao_layout.addWidget(titulo)
        nome_layout = QHBoxLayout()
        nome_label = QLabel('Nome Completo: *')
        nome_label.setMinimumWidth(120)
        nome_label.setStyleSheet('font-weight: bold; color: #495057;')
        self.nome_input = QLineEdit()
        self.nome_input.setMinimumHeight(35)
        self.nome_input.setPlaceholderText('Digite o nome completo do cliente')
        self.nome_input.setStyleSheet('\n            QLineEdit {\n                border: 1px solid #ced4da;\n                border-radius: 4px;\n                padding: 8px;\n                font-size: 14px;\n            }\n            QLineEdit:focus {\n                border-color: #007bff;\n            }\n        ')
        nome_layout.addWidget(nome_label)
        nome_layout.addWidget(self.nome_input)
        secao_layout.addLayout(nome_layout)
        layout.addWidget(secao_frame)
    def criar_secao_contato(self, layout):
        '''Cria se├º├úo com informa├º├Áes de contato'''
        secao_frame = QFrame()
        secao_frame.setStyleSheet('\n            QFrame {\n                background-color: white;\n                border: 1px solid #dee2e6;\n                border-radius: 8px;\n                padding: 15px;\n            }\n        ')
        secao_layout = QVBoxLayout(secao_frame)
        titulo = QLabel('­ƒô× Informa├º├Áes de Contato')
        titulo.setStyleSheet('\n            QLabel {\n                font-size: 16px;\n                font-weight: bold;\n                color: #2c3e50;\n                margin-bottom: 10px;\n            }\n        ')
        secao_layout.addWidget(titulo)
        telefone_layout = QHBoxLayout()
        telefone_label = QLabel('Telefone: *')
        telefone_label.setMinimumWidth(120)
        telefone_label.setStyleSheet('font-weight: bold; color: #495057;')
        self.telefone_input = QLineEdit()
        self.telefone_input.setMinimumHeight(35)
        self.telefone_input.setPlaceholderText('(00) 00000-0000')
        self.telefone_input.setStyleSheet('\n            QLineEdit {\n                border: 1px solid #ced4da;\n                border-radius: 4px;\n                padding: 8px;\n                font-size: 14px;\n            }\n            QLineEdit:focus {\n                border-color: #007bff;\n            }\n        ')
        telefone_layout.addWidget(telefone_label)
        telefone_layout.addWidget(self.telefone_input)
        secao_layout.addLayout(telefone_layout)
        email_layout = QHBoxLayout()
        email_label = QLabel('E-mail:')
        email_label.setMinimumWidth(120)
        email_label.setStyleSheet('font-weight: bold; color: #495057;')
        self.email_input = QLineEdit()
        self.email_input.setMinimumHeight(35)
        self.email_input.setPlaceholderText('cliente@email.com')
        self.email_input.setStyleSheet('\n            QLineEdit {\n                border: 1px solid #ced4da;\n                border-radius: 4px;\n                padding: 8px;\n                font-size: 14px;\n            }\n            QLineEdit:focus {\n                border-color: #007bff;\n            }\n        ')
        email_layout.addWidget(email_label)
        email_layout.addWidget(self.email_input)
        secao_layout.addLayout(email_layout)
        endereco_layout = QHBoxLayout()
        endereco_label = QLabel('Endere├ºo:')
        endereco_label.setMinimumWidth(120)
        endereco_label.setStyleSheet('font-weight: bold; color: #495057;')
        self.endereco_input = QLineEdit()
        self.endereco_input.setMinimumHeight(35)
        self.endereco_input.setPlaceholderText('Rua, n├║mero, bairro, cidade')
        self.endereco_input.setStyleSheet('\n            QLineEdit {\n                border: 1px solid #ced4da;\n                border-radius: 4px;\n                padding: 8px;\n                font-size: 14px;\n            }\n            QLineEdit:focus {\n                border-color: #007bff;\n            }\n        ')
        endereco_layout.addWidget(endereco_label)
        endereco_layout.addWidget(self.endereco_input)
        secao_layout.addLayout(endereco_layout)
        layout.addWidget(secao_frame)
    def criar_secao_classificacao(self, layout):
        '''Cria se├º├úo com classifica├º├úo e observa├º├Áes (NOVOS CAMPOS)'''
        secao_frame = QFrame()
        secao_frame.setStyleSheet('\n            QFrame {\n                background-color: #f8f9fa;\n                border: 1px solid #dee2e6;\n                border-radius: 8px;\n                padding: 15px;\n            }\n        ')
        secao_layout = QVBoxLayout(secao_frame)
        titulo = QLabel('­ƒÅÀ´©Å Classifica├º├úo e Observa├º├Áes')
        titulo.setStyleSheet('\n            QLabel {\n                font-size: 16px;\n                font-weight: bold;\n                color: #2c3e50;\n                margin-bottom: 10px;\n            }\n        ')
        secao_layout.addWidget(titulo)
        tipo_layout = QHBoxLayout()
        tipo_label = QLabel('Tipo de Cliente:')
        tipo_label.setMinimumWidth(120)
        tipo_label.setStyleSheet('font-weight: bold; color: #495057;')
        self.tipo_combo = QComboBox()
        self.tipo_combo.addItems(['Pessoa F├¡sica', 'Lojista'])
        self.tipo_combo.setCurrentText('Pessoa F├¡sica')
        self.tipo_combo.setMinimumHeight(35)
        self.tipo_combo.setStyleSheet('\n            QComboBox {\n                border: 1px solid #ced4da;\n                border-radius: 4px;\n                padding: 8px;\n                font-size: 14px;\n                background-color: white;\n                color: #2c3e50;\n                selection-background-color: #007bff;\n            }\n            QComboBox:focus {\n                border-color: #007bff;\n                background-color: white;\n            }\n            QComboBox:on {\n                background-color: white;\n                border-color: #007bff;\n            }\n            QComboBox QAbstractItemView {\n                background-color: white;\n                border: 1px solid #ced4da;\n                selection-background-color: #007bff;\n                selection-color: white;\n                color: #2c3e50;\n                outline: none;\n            }\n            QComboBox QAbstractItemView::item {\n                padding: 8px;\n                background-color: white;\n                color: #2c3e50;\n                border: none;\n            }\n            QComboBox QAbstractItemView::item:selected {\n                background-color: #007bff;\n                color: white;\n            }\n            QComboBox QAbstractItemView::item:hover {\n                background-color: #e3f2fd;\n                color: #2c3e50;\n            }\n        ')
        tipo_layout.addWidget(tipo_label)
        tipo_layout.addWidget(self.tipo_combo)
        tipo_layout.addStretch()
        secao_layout.addLayout(tipo_layout)
        obs_label = QLabel('Observa├º├Áes:')
        obs_label.setStyleSheet('font-weight: bold; color: #495057; margin-top: 10px;')
        secao_layout.addWidget(obs_label)
        self.observacoes_text = QTextEdit()
        self.observacoes_text.setMaximumHeight(100)
        self.observacoes_text.setPlaceholderText('Informa├º├Áes adicionais sobre o cliente (hist├│rico, prefer├¬ncias, etc.)')
        self.observacoes_text.setStyleSheet('\n            QTextEdit {\n                border: 1px solid #ced4da;\n                border-radius: 4px;\n                padding: 8px;\n                font-size: 14px;\n                background-color: white;\n            }\n            QTextEdit:focus {\n                border-color: #007bff;\n            }\n        ')
        secao_layout.addWidget(self.observacoes_text)
        layout.addWidget(secao_frame)
    def criar_botoes_acao(self, layout):
        '''Cria bot├Áes de a├º├úo padronizados'''
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        salvar_btn = QPushButton('­ƒÆ¥ Salvar Cliente')
        salvar_btn.setMinimumHeight(45)
        salvar_btn.setMinimumWidth(150)
        salvar_btn.setStyleSheet('\n            QPushButton {\n                background-color: #28a745;\n                color: white;\n                border: none;\n                padding: 12px 25px;\n                border-radius: 6px;\n                font-size: 15px;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background-color: #218838;\n            }\n            QPushButton:pressed {\n                background-color: #1e7e34;\n            }\n        ')
        salvar_btn.clicked.connect(self.salvar_cliente)
        cancelar_btn = QPushButton('ÔØî Cancelar')
        cancelar_btn.setMinimumHeight(45)
        cancelar_btn.setMinimumWidth(150)
        cancelar_btn.setStyleSheet('\n            QPushButton {\n                background-color: #6c757d;\n                color: white;\n                border: none;\n                padding: 12px 25px;\n                border-radius: 6px;\n                font-size: 15px;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background-color: #545b62;\n            }\n            QPushButton:pressed {\n                background-color: #495057;\n            }\n        ')
        cancelar_btn.clicked.connect(self.reject)
        buttons_layout.addStretch()
        buttons_layout.addWidget(salvar_btn)
        buttons_layout.addWidget(cancelar_btn)
        layout.addLayout(buttons_layout)
    def verificar_e_adicionar_colunas(self, cursor):
        '''Verifica se as novas colunas existem e as adiciona se necess├írio'''
        try:
            cursor.execute('PRAGMA table_info(clients)')
        except Exception as e:
            print(f'ÔÜá´©Å Erro ao verificar/adicionar colunas: {e}')
        try:
            colunas_existentes = [coluna[1] for coluna in cursor.fetchall()]
            if 'tipo_cliente' not in colunas_existentes:
                cursor.execute('ALTER TABLE clients ADD COLUMN tipo_cliente TEXT DEFAULT "pessoa_fisica"')
                print("Ô£à Coluna 'tipo_cliente' adicionada com sucesso")
            if 'observacoes' not in colunas_existentes:
                cursor.execute('ALTER TABLE clients ADD COLUMN observacoes TEXT DEFAULT ""')
                print("Ô£à Coluna 'observacoes' adicionada com sucesso")
                return
            return
        except Exception as e:
            print(f'ÔÜá´©Å Erro ao verificar/adicionar colunas: {e}')
    def salvar_cliente(self):
        '''Salva o cliente no banco com valida├º├Áes robustas e migra├º├úo autom├ítica'''
        nome = self.nome_input.text().strip()
        telefone = self.telefone_input.text().strip()
        email = self.email_input.text().strip()
        endereco = self.endereco_input.text().strip()
        tipo_cliente_display = self.tipo_combo.currentText()
        tipo_cliente = 'pessoa_fisica' if tipo_cliente_display == 'Pessoa F├¡sica' else 'lojista'
        observacoes = self.observacoes_text.toPlainText().strip()
        if not nome:
            QMessageBox.warning(self, 'ÔØî Erro', 'O nome do cliente ├® obrigat├│rio!')
            self.nome_input.setFocus()
            return
        if not telefone:
            QMessageBox.warning(self, 'ÔØî Erro', 'O telefone do cliente ├® obrigat├│rio!')
            self.telefone_input.setFocus()
            return
        if email and '@' not in email:
            QMessageBox.warning(self, 'ÔØî Erro', 'Email inv├ílido! Deve conter o s├¡mbolo @')
            self.email_input.setFocus()
            return
        try:
            conn = sqlite3.connect('app/database/service_orders.db')
            cursor = conn.cursor()
            self.verificar_e_adicionar_colunas(cursor)
            cursor.execute('\n                SELECT id FROM clients \n                WHERE name = ? AND phone = ? AND user_id = ?\n            ', (nome, telefone, self.user_id))
            if cursor.fetchone():
                QMessageBox.warning(self, 'ÔÜá´©Å Cliente J├í Existe', f"J├í existe um cliente com o nome '{nome}' e telefone '{telefone}'.\n\nVerifique se n├úo ├® um cliente duplicado.")
                if conn:
                    conn.close()
                    return
                return
        except Exception as e:
            QMessageBox.critical(self, 'ÔØî Erro', f'Erro ao salvar cliente no banco de dados:\n\n{str(e)}')
        try:
            cursor.execute('PRAGMA table_info(clients)')
        except Exception as e:
            QMessageBox.critical(self, 'ÔØî Erro', f'Erro ao salvar cliente no banco de dados:\n\n{str(e)}')
        try:
            colunas_existentes = [coluna[1] for coluna in cursor.fetchall()]
            if 'tipo_cliente' in colunas_existentes and 'observacoes' in colunas_existentes:
                cursor.execute('\n                    INSERT INTO clients (name, phone, email, address, tipo_cliente, observacoes, user_id)\n                    VALUES (?, ?, ?, ?, ?, ?, ?)\n                ', (nome, telefone, email, endereco, tipo_cliente, observacoes, self.user_id))
            else:
                cursor.execute('\n                    INSERT INTO clients (name, phone, email, address, user_id)\n                    VALUES (?, ?, ?, ?, ?)\n                ', (nome, telefone, email, endereco, self.user_id))
            conn.commit()
            QMessageBox.information(self, 'Ô£à Sucesso', f'Cliente cadastrado com sucesso!\n\n­ƒôØ Nome: {nome}\n­ƒô× Telefone: {telefone}\n­ƒÅÀ´©Å Tipo: {tipo_cliente_display}')
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, 'ÔØî Erro', f'Erro ao salvar cliente no banco de dados:\n\n{str(e)}')
        if conn:
            conn.close()
