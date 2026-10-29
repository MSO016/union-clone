from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QMessageBox, QScrollArea, QWidget, QFrame, QComboBox, QTextEdit)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import sqlite3
class EditClientDialog(QDialog):
    def __init__(self, client_id, user_id, parent=None):
        super().__init__(parent)
        self.client_id = client_id
        self.user_id = user_id
        self.setWindowTitle('Editar Cliente')
        self.setModal(True)
        self.setMinimumSize(1000, 700)
        self.showMaximized()
        self.setup_ui()
        self.carregar_cliente()
    def setup_ui(self):
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
        titulo = QLabel('Editar Cliente')
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
        self.nome_input.setStyleSheet('\n            QLineEdit {\n                border: 1px solid #ced4da;\n                border-radius: 4px;\n                padding: 8px;\n                font-size: 14px;\n            }\n            QLineEdit:focus {\n                border-color: #007bff;\n            }\n        ')
        nome_layout.addWidget(nome_label)
        nome_layout.addWidget(self.nome_input)
        secao_layout.addLayout(nome_layout)
        layout.addWidget(secao_frame)
    def criar_secao_contato(self, layout):
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
        self.endereco_input.setStyleSheet('\n            QLineEdit {\n                border: 1px solid #ced4da;\n                border-radius: 4px;\n                padding: 8px;\n                font-size: 14px;\n            }\n            QLineEdit:focus {\n                border-color: #007bff;\n            }\n        ')
        endereco_layout.addWidget(endereco_label)
        endereco_layout.addWidget(self.endereco_input)
        secao_layout.addLayout(endereco_layout)
        layout.addWidget(secao_frame)
    def criar_secao_classificacao(self, layout):
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
        self.observacoes_text.setStyleSheet('\n            QTextEdit {\n                border: 1px solid #ced4da;\n                border-radius: 4px;\n                padding: 8px;\n                font-size: 14px;\n                background-color: white;\n            }\n            QTextEdit:focus {\n                border-color: #007bff;\n            }\n        ')
        secao_layout.addWidget(self.observacoes_text)
        layout.addWidget(secao_frame)
    def criar_botoes_acao(self, layout):
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        salvar_btn = QPushButton('­ƒÆ¥ Salvar Altera├º├Áes')
        salvar_btn.setMinimumHeight(45)
        salvar_btn.setMinimumWidth(150)
        salvar_btn.setStyleSheet('\n            QPushButton {\n                background-color: #28a745;\n                color: white;\n                border: none;\n                padding: 12px 25px;\n                border-radius: 6px;\n                font-size: 15px;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background-color: #218838;\n            }\n        ')
        salvar_btn.clicked.connect(self.salvar_cliente)
        excluir_btn = QPushButton('­ƒùæ´©Å Excluir Cliente')
        excluir_btn.setMinimumHeight(45)
        excluir_btn.setMinimumWidth(150)
        excluir_btn.setStyleSheet('\n            QPushButton {\n                background-color: #dc3545;\n                color: white;\n                border: none;\n                padding: 12px 25px;\n                border-radius: 6px;\n                font-size: 15px;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background-color: #c82333;\n            }\n        ')
        excluir_btn.clicked.connect(self.excluir_cliente)
        cancelar_btn = QPushButton('ÔØî Cancelar')
        cancelar_btn.setMinimumHeight(45)
        cancelar_btn.setMinimumWidth(150)
        cancelar_btn.setStyleSheet('\n            QPushButton {\n                background-color: #6c757d;\n                color: white;\n                border: none;\n                padding: 12px 25px;\n                border-radius: 6px;\n                font-size: 15px;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background-color: #545b62;\n            }\n        ')
        cancelar_btn.clicked.connect(self.reject)
        buttons_layout.addStretch()
        buttons_layout.addWidget(salvar_btn)
        buttons_layout.addWidget(excluir_btn)
        buttons_layout.addWidget(cancelar_btn)
        layout.addLayout(buttons_layout)
    def verificar_e_adicionar_colunas(self, cursor):
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
    def carregar_cliente(self):
        try:
            conn = sqlite3.connect('app/database/service_orders.db')
            cursor = conn.cursor()
            self.verificar_e_adicionar_colunas(cursor)
            cursor.execute('PRAGMA table_info(clients)')
        except Exception as e:
            QMessageBox.critical(self, 'ÔØî Erro', f'Erro ao carregar cliente:\n{str(e)}')
        try:
            colunas_existentes = [coluna[1] for coluna in cursor.fetchall()]
            if 'tipo_cliente' in colunas_existentes and 'observacoes' in colunas_existentes:
                cursor.execute('\n                    SELECT name, phone, email, address, tipo_cliente, observacoes\n                    FROM clients\n                    WHERE id = ? AND user_id = ?\n                ', (self.client_id, self.user_id))
            else:
                cursor.execute('\n                    SELECT name, phone, email, address\n                    FROM clients\n                    WHERE id = ? AND user_id = ?\n                ', (self.client_id, self.user_id))
            cliente = cursor.fetchone()
            if cliente:
                self.nome_input.setText(cliente[0] or '')
                self.telefone_input.setText(cliente[1] or '')
                self.email_input.setText(cliente[2] or '')
                self.endereco_input.setText(cliente[3] or '')
                if len(cliente) >= 6:
                    tipo_cliente_db = cliente[4] or 'pessoa_fisica'
                    tipo_display = 'Pessoa F├¡sica' if tipo_cliente_db == 'pessoa_fisica' else 'Lojista'
                    self.tipo_combo.setCurrentText(tipo_display)
                    self.observacoes_text.setPlainText(cliente[5] or '')
                else:
                    self.tipo_combo.setCurrentText('Pessoa F├¡sica')
                    self.observacoes_text.setPlainText('')
            else:
                QMessageBox.critical(self, 'ÔØî Erro', 'Cliente n├úo encontrado!')
                self.reject()
        except Exception as e:
            QMessageBox.critical(self, 'ÔØî Erro', f'Erro ao carregar cliente:\n{str(e)}')
        finally:
            if conn:
                conn.close()
    def salvar_cliente(self):
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
            cursor.execute('PRAGMA table_info(clients)')
        except Exception as e:
            QMessageBox.critical(self, 'ÔØî Erro', f'Erro ao atualizar cliente no banco:\n\n{str(e)}')
        try:
            colunas_existentes = [coluna[1] for coluna in cursor.fetchall()]
            if 'tipo_cliente' in colunas_existentes and 'observacoes' in colunas_existentes:
                cursor.execute('\n                    UPDATE clients\n                    SET name = ?, phone = ?, email = ?, address = ?, tipo_cliente = ?, observacoes = ?\n                    WHERE id = ? AND user_id = ?\n                ', (nome, telefone, email, endereco, tipo_cliente, observacoes, self.client_id, self.user_id))
            else:
                cursor.execute('\n                    UPDATE clients\n                    SET name = ?, phone = ?, email = ?, address = ?\n                    WHERE id = ? AND user_id = ?\n                ', (nome, telefone, email, endereco, self.client_id, self.user_id))
            conn.commit()
            QMessageBox.information(self, 'Ô£à Sucesso', f'Cliente atualizado com sucesso!\n\n­ƒôØ Nome: {nome}\n­ƒô× Telefone: {telefone}\n­ƒÅÀ´©Å Tipo: {tipo_cliente_display}')
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, 'ÔØî Erro', f'Erro ao atualizar cliente no banco:\n\n{str(e)}')
        if conn:
            conn.close()
    def excluir_cliente(self):
        try:
            conn = sqlite3.connect('app/database/service_orders.db')
            cursor = conn.cursor()
            cursor.execute('\n                SELECT COUNT(*) FROM service_orders\n                WHERE client_id = ? AND user_id = ?\n            ', (self.client_id, self.user_id))
            total_os = cursor.fetchone()[0]
            if total_os > 0:
                QMessageBox.warning(self, 'Aviso', 'N├úo ├® poss├¡vel excluir o cliente pois existem ordens de servi├ºo vinculadas!')
                if conn:
                    conn.close()
                    return
                return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao excluir cliente: {str(e)}')
        try:
            resposta = QMessageBox.question(self, 'Confirma├º├úo', 'Tem certeza que deseja excluir este cliente?', QMessageBox.Yes | QMessageBox.No)
            if resposta == QMessageBox.Yes:
                cursor.execute('\n                    DELETE FROM clients\n                    WHERE id = ? AND user_id = ?\n                ', (self.client_id, self.user_id))
                conn.commit()
                QMessageBox.information(self, 'Sucesso', 'Cliente exclu├¡do com sucesso!')
                self.accept()
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao excluir cliente: {str(e)}')
        if conn:
            conn.close()
