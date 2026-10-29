from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit, QMessageBox, QComboBox, QSpinBox, QScrollArea, QWidget, QFileDialog, QListWidget, QInputDialog, QApplication)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
import sqlite3
from datetime import datetime
import os
import shutil
class AddKnowledgeDialog(QDialog):
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle('Adicionar ├á Base de Conhecimento')
        self.setModal(True)
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        if screen_width <= 1366:
            width_ratio = 0.7
            height_ratio = 0.8
        elif screen_width <= 1920:
            width_ratio = 0.6
            height_ratio = 0.75
        else:
            width_ratio = 0.5
            height_ratio = 0.7
        dialog_width = int(screen_width * width_ratio)
        dialog_height = int(screen_height * height_ratio)
        self.setMinimumSize(600, 700)
        self.resize(dialog_width, dialog_height)
        self.move((screen_width - dialog_width) // 2, (screen_height - dialog_height) // 2)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)
        self.setSizeGripEnabled(True)
        self.anexos = []
        self.setup_ui()
        self.showMaximized()
    def setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        titulo = QLabel('Nova Solu├º├úo')
        titulo.setStyleSheet('font-size: 18px; font-weight: bold; margin: 10px;')
        layout.addWidget(titulo)
        tipo_layout = QHBoxLayout()
        tipo_label = QLabel('Tipo:')
        self.tipo_combo = QComboBox()
        self.tipo_combo.addItems(['Notebook', 'Smartphone', 'Desktop', 'Tablet', 'Impressora', 'Outro'])
        tipo_layout.addWidget(tipo_label)
        tipo_layout.addWidget(self.tipo_combo)
        layout.addLayout(tipo_layout)
        marca_layout = QHBoxLayout()
        marca_label = QLabel('Marca:')
        self.marca_input = QLineEdit()
        marca_layout.addWidget(marca_label)
        marca_layout.addWidget(self.marca_input)
        layout.addLayout(marca_layout)
        modelo_layout = QHBoxLayout()
        modelo_label = QLabel('Modelo:')
        self.modelo_input = QLineEdit()
        modelo_layout.addWidget(modelo_label)
        modelo_layout.addWidget(self.modelo_input)
        layout.addLayout(modelo_layout)
        problema_label = QLabel('Descri├º├úo do Problema:')
        self.problema_text = QTextEdit()
        self.problema_text.setMaximumHeight(100)
        layout.addWidget(problema_label)
        layout.addWidget(self.problema_text)
        solucao_label = QLabel('Solu├º├úo:')
        self.solucao_text = QTextEdit()
        self.solucao_text.setMaximumHeight(150)
        layout.addWidget(solucao_label)
        layout.addWidget(self.solucao_text)
        passos_label = QLabel('Passos para Solu├º├úo:')
        self.passos_text = QTextEdit()
        self.passos_text.setMaximumHeight(150)
        layout.addWidget(passos_label)
        layout.addWidget(self.passos_text)
        taxa_layout = QHBoxLayout()
        taxa_label = QLabel('Taxa de Sucesso (%):')
        self.taxa_spin = QSpinBox()
        self.taxa_spin.setRange(0, 100)
        self.taxa_spin.setValue(100)
        taxa_layout.addWidget(taxa_label)
        taxa_layout.addWidget(self.taxa_spin)
        layout.addLayout(taxa_layout)
        anexos_label = QLabel('Anexos:')
        layout.addWidget(anexos_label)
        anexos_layout = QHBoxLayout()
        self.anexos_list = QListWidget()
        anexos_layout.addWidget(self.anexos_list)
        botoes_anexo = QVBoxLayout()
        add_foto_btn = QPushButton('Adicionar Foto')
        add_foto_btn.clicked.connect((lambda: self.adicionar_anexo('foto')))
        botoes_anexo.addWidget(add_foto_btn)
        add_pdf_btn = QPushButton('Adicionar PDF')
        add_pdf_btn.clicked.connect((lambda: self.adicionar_anexo('pdf')))
        botoes_anexo.addWidget(add_pdf_btn)
        add_doc_btn = QPushButton('Adicionar Documento')
        add_doc_btn.clicked.connect((lambda: self.adicionar_anexo('doc')))
        botoes_anexo.addWidget(add_doc_btn)
        remover_btn = QPushButton('Remover Anexo')
        remover_btn.clicked.connect(self.remover_anexo)
        botoes_anexo.addWidget(remover_btn)
        anexos_layout.addLayout(botoes_anexo)
        layout.addLayout(anexos_layout)
        buttons_layout = QHBoxLayout()
        salvar_btn = QPushButton('Salvar')
        salvar_btn.setStyleSheet('\n            QPushButton {\n                background-color: #27ae60;\n                color: white;\n                border: none;\n                padding: 8px 15px;\n                border-radius: 5px;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background-color: #229954;\n            }\n        ')
        salvar_btn.clicked.connect(self.salvar_solucao)
        cancelar_btn = QPushButton('Cancelar')
        cancelar_btn.setStyleSheet('\n            QPushButton {\n                background-color: #e74c3c;\n                color: white;\n                border: none;\n                padding: 8px 15px;\n                border-radius: 5px;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background-color: #c0392b;\n            }\n        ')
        cancelar_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(salvar_btn)
        buttons_layout.addWidget(cancelar_btn)
        layout.addLayout(buttons_layout)
        scroll.setWidget(main_widget)
        dialog_layout = QVBoxLayout(self)
        dialog_layout.addWidget(scroll)
    def adicionar_anexo(self, tipo):
        filtros = {'foto': 'Imagens (*.png *.jpg *.jpeg)', 'pdf': 'PDF (*.pdf)', 'doc': 'Documentos (*.doc *.docx *.txt *.rtf)'}
        file_name, _ = QFileDialog.getOpenFileName(self, f'Selecionar {tipo.upper()}', '', filtros[tipo])
        if file_name:
            descricao, ok = QInputDialog.getText(self, 'Descri├º├úo do Anexo', 'Digite uma breve descri├º├úo do anexo:')
            if ok:
                if descricao:
                    anexos_dir = os.path.join('app', 'attachments', 'knowledge_base')
                    os.makedirs(anexos_dir, exist_ok=True)
                    ext = os.path.splitext(file_name)[1]
                    new_filename = f'kb_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}'
                    new_path = os.path.join(anexos_dir, new_filename)
                    shutil.copy2(file_name, new_path)
                    self.anexos.append({'path': new_path, 'type': tipo, 'description': descricao})
                    self.anexos_list.addItem(f'{descricao} ({tipo.upper()})')
    def remover_anexo(self):
        current_row = self.anexos_list.currentRow()
        if current_row >= 0:
            anexo = self.anexos[current_row]
            if os.path.exists(anexo['path']):
                os.remove(anexo['path'])
            self.anexos.pop(current_row)
            self.anexos_list.takeItem(current_row)
    def salvar_solucao(self):
        if not self.marca_input.text().strip():
            QMessageBox.warning(self, 'Erro', 'Preencha a marca do dispositivo!')
            return
        if not self.modelo_input.text().strip():
            QMessageBox.warning(self, 'Erro', 'Preencha o modelo do dispositivo!')
            return
        if not self.problema_text.toPlainText().strip():
            QMessageBox.warning(self, 'Erro', 'Descreva o problema!')
            return
        if not self.solucao_text.toPlainText().strip():
            QMessageBox.warning(self, 'Erro', 'Descreva a solu├º├úo!')
            return
        if not self.passos_text.toPlainText().strip():
            QMessageBox.warning(self, 'Erro', 'Liste os passos para a solu├º├úo!')
            return
        try:
            conn = sqlite3.connect('app/database/service_orders.db')
            cursor = conn.cursor()
            cursor.execute("\n                INSERT INTO knowledge_base (\n                    device_type, brand, model,\n                    issue_description, solution,\n                    steps_taken, success_rate,\n                    user_id, created_at\n                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))\n            ", (self.tipo_combo.currentText(), self.marca_input.text().strip(), self.modelo_input.text().strip(), self.problema_text.toPlainText().strip(), self.solucao_text.toPlainText().strip(), self.passos_text.toPlainText().strip(), self.taxa_spin.value(), self.user_id))
            kb_id = cursor.lastrowid
            for anexo in self.anexos:
                cursor.execute('\n                    INSERT INTO knowledge_base_attachments (\n                        knowledge_base_id, file_path,\n                        file_type, description\n                    ) VALUES (?, ?, ?, ?)\n                ', (kb_id, anexo['path'], anexo['type'], anexo['description']))
            conn.commit()
            QMessageBox.information(self, 'Sucesso', 'Solu├º├úo adicionada com sucesso!')
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao salvar solu├º├úo: {str(e)}')
        if conn:
            conn.close()
