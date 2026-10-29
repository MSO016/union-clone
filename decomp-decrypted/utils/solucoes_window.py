from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sqlite3
import os
import tempfile
import subprocess
from app.utils.database_manager import DatabaseManager
from app.utils.translation_manager import TranslationManager
class ImagemDialog(QDialog):
    def __init__(self, imagem_blob, parent=None):
        super().__init__(parent)
        self.translation_manager = TranslationManager.get_instance()
        self.setWindowTitle(self.translation_manager.get_text('image_preview'))
        self.setModal(True)
        layout = QVBoxLayout(self)
        label = QLabel()
        pixmap = QPixmap()
        pixmap.loadFromData(imagem_blob)
        screen = QApplication.primaryScreen().size()
        scaled_pixmap = pixmap.scaled(min(screen.width() * 0.8, pixmap.width()), min(screen.height() * 0.8, pixmap.height()), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label.setPixmap(scaled_pixmap)
        layout.addWidget(label)
        btn_fechar = QPushButton(self.translation_manager.get_text('close'))
        btn_fechar.clicked.connect(self.close)
        layout.addWidget(btn_fechar, alignment=Qt.AlignCenter)
class SolucoesWindow(QMainWindow):
    def __init__(self, marca, parent=None):
        super().__init__(parent)
        self.marca = marca
        self.parent = parent
        self.db = DatabaseManager()
        self.translation_manager = TranslationManager.get_instance()
        self.translation_manager.language_changed.connect(self.refresh_interface)
        self.setup_ui()
        self.carregar_solucoes()
    def setup_ui(self):
        self.setWindowTitle(self.translation_manager.get_text('solutions_title').format(self.marca))
        self.setMinimumSize(1000, 600)
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        header = QHBoxLayout()
        btn_voltar = QPushButton(self.translation_manager.get_text('back'))
        btn_voltar.setStyleSheet('\n            QPushButton {\n                background-color: #2196F3;\n                color: white;\n                border: none;\n                padding: 8px 15px;\n                border-radius: 4px;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background-color: #1976D2;\n            }\n        ')
        btn_voltar.clicked.connect(self.voltar)
        header.addWidget(btn_voltar)
        nav_label = QLabel(self.translation_manager.get_text('solutions_breadcrumb').format(self.marca))
        nav_label.setStyleSheet('color: #2196F3; font-size: 14px;')
        header.addWidget(nav_label)
        header.addStretch()
        layout.addLayout(header)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.translation_manager.get_text('search_model'))
        self.search_input.setStyleSheet('\n            QLineEdit {\n                padding: 10px;\n                border: 1px solid #ddd;\n                border-radius: 5px;\n                margin: 10px 0;\n                font-size: 14px;\n            }\n        ')
        self.search_input.textChanged.connect(self.filtrar_solucoes)
        layout.addWidget(self.search_input)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.grid_layout = QGridLayout(scroll_content)
        self.grid_layout.setSpacing(20)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
    def filtrar_solucoes(self, texto):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("\n                SELECT id, modelo, descricao, observacoes, diagrama_blob, imagem_blob \n                FROM solucoes \n                WHERE marca = ? \n                AND status = 'ativo'\n                AND (\n                    lower(modelo) LIKE ? OR \n                    lower(descricao) LIKE ?\n                )\n                ORDER BY modelo\n            ", (self.marca, f'%{texto.lower()}%', f'%{texto.lower()}%'))
            solucoes = cursor.fetchall()
            for i in reversed(range(self.grid_layout.count())):
                widget = self.grid_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
            row = col = 0
            for solucao in solucoes:
                card = self.criar_card_solucao(solucao)
                self.grid_layout.addWidget(card, row, col)
                col += 1
                if col > 2:
                    col = 0
                    row += 1
            conn.close()
            return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', str(e))
    def carregar_solucoes(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("\n                SELECT id, modelo, descricao, observacoes, diagrama_blob, imagem_blob \n                FROM solucoes \n                WHERE marca = ? AND status = 'ativo'\n                ORDER BY modelo\n            ", (self.marca,))
            solucoes = cursor.fetchall()
            row = col = 0
            for solucao in solucoes:
                card = self.criar_card_solucao(solucao)
                self.grid_layout.addWidget(card, row, col)
                col += 1
                if col > 2:
                    col = 0
                    row += 1
            conn.close()
            return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', str(e))
    def criar_card_solucao(self, solucao):
        id, modelo, descricao, observacoes, diagrama_blob, imagem_blob = solucao
        card = QFrame()
        card.setStyleSheet('\n            QFrame {\n                background: white;\n                border-radius: 10px;\n                padding: 15px;\n                border: 2px solid #eee;\n            }\n            QFrame:hover {\n                border-color: #2196F3;\n            }\n        ')
        layout = QVBoxLayout(card)
        titulo = QLabel(modelo)
        titulo.setStyleSheet('font-size: 18px; font-weight: bold; color: #2C3E50;')
        titulo.setWordWrap(True)
        layout.addWidget(titulo)
        if descricao:
            desc = QLabel(str(descricao))
            desc.setStyleSheet('color: #7F8C8D;')
            desc.setWordWrap(True)
            layout.addWidget(desc)
        if imagem_blob:
            imagem = QLabel()
            pixmap = QPixmap()
            pixmap.loadFromData(imagem_blob)
            scaled = pixmap.scaled(300, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            imagem.setPixmap(scaled)
            imagem.setAlignment(Qt.AlignCenter)
            layout.addWidget(imagem)
        btn = QPushButton(self.translation_manager.get_text('view_details'))
        btn.setStyleSheet('\n            QPushButton {\n                background-color: #2196F3;\n                color: white;\n                border: none;\n                padding: 8px;\n                border-radius: 4px;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background-color: #1976D2;\n            }\n        ')
        btn.clicked.connect((lambda: self.ver_detalhes(id)))
        layout.addWidget(btn)
        return card
    def voltar(self):
        if self.parent:
            self.parent.show()
        self.close()
    def ver_detalhes(self, id):
        try:
            solucao = self.db.get_solution_by_id(id)
            if solucao:
                modelo, descricao, observacoes, diagrama_blob, imagem_blob = solucao
                dialog = QDialog(self)
                dialog.setWindowTitle(modelo)
                dialog.setMinimumSize(800, 600)
                layout = QVBoxLayout(dialog)
                titulo = QLabel(modelo)
                titulo.setStyleSheet('font-size: 24px; font-weight: bold;')
                layout.addWidget(titulo)
                if descricao:
                    desc_label = QLabel(f'Descri├º├úo: {descricao}')
                    desc_label.setWordWrap(True)
                    layout.addWidget(desc_label)
                if observacoes:
                    obs_label = QLabel(f'Observa├º├Áes: {observacoes}')
                    obs_label.setWordWrap(True)
                    layout.addWidget(obs_label)
                if imagem_blob:
                    img_label = QLabel()
                    pixmap = QPixmap()
                    pixmap.loadFromData(imagem_blob)
                    scaled = pixmap.scaled(600, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    img_label.setPixmap(scaled)
                    img_label.setAlignment(Qt.AlignCenter)
                    layout.addWidget(img_label)
                btn_fechar = QPushButton(self.translation_manager.get_text('close'))
                btn_fechar.clicked.connect(dialog.close)
                layout.addWidget(btn_fechar)
                dialog.exec_()
                return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao carregar detalhes: {str(e)}')
    def refresh_interface(self):
        self.setWindowTitle(self.translation_manager.get_text('solutions_title').format(self.marca))
        self.search_input.setPlaceholderText(self.translation_manager.get_text('search_model'))
        for btn in self.findChildren(QPushButton):
            if 'voltar' not in btn.text().lower():
                if 'back' in btn.text().lower() or 'volver' in btn.text().lower():
                    btn.setText(self.translation_manager.get_text('back'))
                    continue
            if 'ver detalhe' not in btn.text().lower():
                if 'view detail' in btn.text().lower() or 'ver detalle' in btn.text().lower():
                    btn.setText(self.translation_manager.get_text('view_details'))
                    continue
            if 'fechar' not in btn.text().lower() and 'close' not in btn.text().lower() and 'cerrar' not in btn.text().lower():
                continue
            btn.setText(self.translation_manager.get_text('close'))
            continue
