from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QLineEdit, QComboBox, QTextEdit, QScrollArea, QWidget, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
import sqlite3
import os
class KnowledgeBaseSearchDialog(QDialog):
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle('Base de Conhecimento')
        self.setModal(True)
        self.setMinimumSize(1000, 600)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)
        self.setup_ui()
        self.carregar_solucoes()
    def setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        titulo = QLabel('Base de Conhecimento - Pesquisa')
        titulo.setStyleSheet('font-size: 18px; font-weight: bold; margin: 10px;')
        layout.addWidget(titulo)
        filtros_layout = QHBoxLayout()
        self.tipo_combo = QComboBox()
        self.tipo_combo.addItems(['Todos', 'Notebook', 'Smartphone', 'Desktop', 'Tablet', 'Impressora', 'Outro'])
        self.tipo_combo.currentTextChanged.connect(self.filtrar_solucoes)
        filtros_layout.addWidget(QLabel('Tipo:'))
        filtros_layout.addWidget(self.tipo_combo)
        self.busca_input = QLineEdit()
        self.busca_input.setPlaceholderText('Buscar por marca, modelo ou problema...')
        self.busca_input.textChanged.connect(self.filtrar_solucoes)
        filtros_layout.addWidget(self.busca_input)
        layout.addLayout(filtros_layout)
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(6)
        self.tabela.setHorizontalHeaderLabels(['ID', 'Dispositivo', 'Marca/Modelo', 'Problema', 'Taxa de Sucesso', 'Data'])
        self.tabela.horizontalHeader().setStretchLastSection(True)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.doubleClicked.connect(self.ver_detalhes)
        layout.addWidget(self.tabela)
        detalhes_label = QLabel('Detalhes da Solu├º├úo')
        detalhes_label.setStyleSheet('font-weight: bold;')
        layout.addWidget(detalhes_label)
        self.detalhes_text = QTextEdit()
        self.detalhes_text.setReadOnly(True)
        self.detalhes_text.setMaximumHeight(200)
        layout.addWidget(self.detalhes_text)
        buttons_layout = QHBoxLayout()
        ver_btn = QPushButton('Ver Solu├º├úo')
        ver_btn.setStyleSheet('\n            QPushButton {\n                background-color: #5bc0de;\n                color: white;\n                border: none;\n                padding: 5px 15px;\n                border-radius: 3px;\n            }\n            QPushButton:hover {\n                background-color: #46b8da;\n            }\n        ')
        ver_btn.clicked.connect(self.ver_detalhes)
        buttons_layout.addWidget(ver_btn)
        fechar_btn = QPushButton('Fechar')
        fechar_btn.setStyleSheet('\n            QPushButton {\n                background-color: #d9534f;\n                color: white;\n                border: none;\n                padding: 5px 15px;\n                border-radius: 3px;\n            }\n            QPushButton:hover {\n                background-color: #c9302c;\n            }\n        ')
        fechar_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(fechar_btn)
        layout.addLayout(buttons_layout)
        scroll.setWidget(main_widget)
        dialog_layout = QVBoxLayout(self)
        dialog_layout.addWidget(scroll)
    def carregar_solucoes(self):
        try:
            conn = sqlite3.connect('app/database/service_orders.db')
            cursor = conn.cursor()
            cursor.execute('\n                SELECT id, device_type, brand, model,\n                       issue_description, success_rate, created_at\n                FROM knowledge_base\n                WHERE user_id = ?\n                ORDER BY created_at DESC\n            ', (self.user_id,))
            self.todas_solucoes = cursor.fetchall()
            self.atualizar_tabela(self.todas_solucoes)
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao carregar solu├º├Áes: {str(e)}')
        if conn:
            conn.close()
    def atualizar_tabela(self, dados):
        self.tabela.setRowCount(0)
        for row, (id, tipo, marca, modelo, problema, taxa, data) in enumerate(dados):
            self.tabela.insertRow(row)
            self.tabela.setItem(row, 0, QTableWidgetItem(str(id)))
            self.tabela.setItem(row, 1, QTableWidgetItem(tipo))
            self.tabela.setItem(row, 2, QTableWidgetItem(f'{marca} / {modelo}'))
            self.tabela.setItem(row, 3, QTableWidgetItem(problema))
            self.tabela.setItem(row, 4, QTableWidgetItem(f'{taxa}%'))
            self.tabela.setItem(row, 5, QTableWidgetItem(data))
            continue
    def filtrar_solucoes(self):
        tipo = self.tipo_combo.currentText()
        texto = self.busca_input.text().lower()
        filtradas = []
        for solucao in self.todas_solucoes:
            if tipo != 'Todos':
                if solucao[1] == tipo and (not texto or texto in str(solucao[2]).lower() or texto in str(solucao[3]).lower() or texto in str(solucao[4]).lower()):
                    filtradas.append(solucao)
        self.atualizar_tabela(filtradas)
    def ver_detalhes(self, item=None):
        conn = None
        try:
            if not item or isinstance(item, bool):
                selected_items = self.tabela.selectedItems()
                if not selected_items:
                    QMessageBox.warning(self, 'Aviso', 'Selecione uma solu├º├úo para ver os detalhes!')
                    if conn:
                        conn.close()
                        return
                    return
                row = selected_items[0].row()
            else:
                row = item.row()
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao carregar detalhes: {str(e)}')
        kb_id = int(self.tabela.item(row, 0).text())
        conn = sqlite3.connect('app/database/service_orders.db')
        cursor = conn.cursor()
        cursor.execute('\n                SELECT device_type, brand, model, issue_description,\n                       solution, steps_taken, success_rate, created_at\n                FROM knowledge_base \n                WHERE id = ?\n            ', (kb_id,))
        dados = cursor.fetchone()
        if dados:
            detalhes = QDialog(self)
            detalhes.setWindowTitle('Detalhes da Solu├º├úo')
            detalhes.setModal(True)
            detalhes.setMinimumWidth(800)
            detalhes.setMinimumHeight(600)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            main_widget = QWidget()
            layout = QVBoxLayout(main_widget)
            layout.addWidget(QLabel(f'<b>Dispositivo:</b> {dados[0]}'))
            layout.addWidget(QLabel(f'<b>Marca/Modelo:</b> {dados[1]} {dados[2]}'))
            layout.addWidget(QLabel(f'<b>Problema:</b> {dados[3]}'))
            layout.addWidget(QLabel(f'<b>Taxa de Sucesso:</b> {dados[6]}%'))
            layout.addWidget(QLabel(f'<b>Data:</b> {dados[7]}'))
            layout.addWidget(QLabel('<b>Solu├º├úo:</b>'))
            solucao_text = QTextEdit()
            solucao_text.setPlainText(dados[4])
            solucao_text.setReadOnly(True)
            layout.addWidget(solucao_text)
            layout.addWidget(QLabel('<b>Passos Realizados:</b>'))
            passos_text = QTextEdit()
            passos_text.setPlainText(dados[5])
            passos_text.setReadOnly(True)
            layout.addWidget(passos_text)
            layout.addWidget(QLabel('<b>Anexos:</b>'))
            anexos_list = QListWidget()
            layout.addWidget(anexos_list)
            cursor.execute('\n                    SELECT file_path, file_type, description\n                    FROM knowledge_base_attachments\n                    WHERE knowledge_base_id = ?\n                ', (kb_id,))
            anexos = cursor.fetchall()
            for anexo in anexos:
                item = QListWidgetItem(f'{anexo[2]} ({anexo[1].upper()})')
                item.setData(Qt.UserRole, anexo[0])
                anexos_list.addItem(item)
            if anexos:
                abrir_btn = QPushButton('Abrir Anexo Selecionado')
                abrir_btn.clicked.connect((lambda: self.abrir_anexo(anexos_list.currentItem())))
                layout.addWidget(abrir_btn)
            scroll.setWidget(main_widget)
            detalhes_layout = QVBoxLayout(detalhes)
            detalhes_layout.addWidget(scroll)
            detalhes.exec_()
        if conn:
            conn.close()
    def abrir_anexo(self, item):
        if item:
            file_path = item.data(Qt.UserRole)
            if os.path.exists(file_path):
                os.startfile(file_path)
                return
            QMessageBox.warning(self, 'Erro', 'Arquivo n├úo encontrado!')
