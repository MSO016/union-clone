from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QLineEdit, QWidget, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import sqlite3
from .edit_client import EditClientDialog
from .client_details import ClientDetailsDialog
class ListClientsDialog(QDialog):
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.is_admin = parent.is_admin if hasattr(parent, 'is_admin') else False
        self.setWindowTitle('Lista de Clientes')
        self.setModal(True)
        self.setMinimumSize(1000, 700)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setSizeGripEnabled(True)
        self.setup_ui()
        self.carregar_clientes()
        self.showMaximized()
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)
        header_layout = QHBoxLayout()
        voltar_btn = QPushButton('ÔåÉ Voltar')
        voltar_btn.setStyleSheet('\n            QPushButton {\n                background-color: #6c757d;\n                color: white;\n                border: none;\n                padding: 12px 25px;\n                border-radius: 5px;\n                font-weight: bold;\n                font-size: 14px;\n            }\n            QPushButton:hover {\n                background-color: #5a6268;\n            }\n            QPushButton:pressed {\n                background-color: #4e555b;\n            }\n        ')
        voltar_btn.clicked.connect(self.reject)
        header_layout.addWidget(voltar_btn)
        titulo = QLabel('Lista de Clientes')
        titulo.setStyleSheet('font-size: 24px; font-weight: bold; color: #2c3e50; margin-left: 20px;')
        header_layout.addWidget(titulo)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        busca_frame = QFrame()
        busca_frame.setStyleSheet('\n            QFrame {\n                background-color: white;\n                border: 1px solid #ddd;\n                border-radius: 8px;\n                padding: 10px;\n            }\n        ')
        busca_layout = QHBoxLayout(busca_frame)
        busca_layout.setContentsMargins(15, 10, 15, 10)
        busca_label = QLabel('­ƒöì Buscar:')
        busca_label.setStyleSheet('font-weight: bold; color: #2c3e50;')
        self.busca_input = QLineEdit()
        self.busca_input.setPlaceholderText('Digite nome, telefone ou email para filtrar...')
        self.busca_input.setStyleSheet('\n            QLineEdit {\n                border: 1px solid #ccc;\n                border-radius: 4px;\n                padding: 8px 12px;\n                font-size: 14px;\n                background-color: #f8f9fa;\n            }\n            QLineEdit:focus {\n                border-color: #3498db;\n                background-color: white;\n            }\n        ')
        self.busca_input.textChanged.connect(self.filtrar_clientes)
        self.busca_input.returnPressed.connect(self.filtrar_clientes)
        busca_layout.addWidget(busca_label)
        busca_layout.addWidget(self.busca_input)
        layout.addWidget(busca_frame)
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(6)
        self.tabela.setHorizontalHeaderLabels(['ID', 'Nome', 'Telefone', 'Email', 'OS', 'A├º├Áes'])
        self.tabela.horizontalHeader().setStretchLastSection(True)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setStyleSheet('\n            QTableWidget {\n                gridline-color: #ecf0f1;\n                background-color: white;\n                border: 1px solid #bdc3c7;\n                border-radius: 6px;\n                selection-background-color: #e8f4fd;\n                selection-color: #2c3e50;\n                color: #2c3e50;\n            }\n            QTableWidget::item {\n                padding: 12px 8px;\n                border-bottom: 1px solid #ecf0f1;\n                background-color: white;\n            }\n            QTableWidget::item:selected {\n                background-color: #e8f4fd;\n                color: #2c3e50;\n            }\n            QTableWidget::item:alternate {\n                background-color: #f8f9fa;\n            }\n            QTableWidget::item:alternate:selected {\n                background-color: #d6ebfd;\n                color: #2c3e50;\n            }\n            QHeaderView::section {\n                background-color: #34495e;\n                color: white;\n                padding: 12px 8px;\n                border: none;\n                font-weight: bold;\n                font-size: 13px;\n            }\n        ')
        layout.addWidget(self.tabela)
        buttons_frame = QFrame()
        buttons_frame.setStyleSheet('\n            QFrame {\n                background-color: #f8f9fa;\n                border-top: 1px solid #ddd;\n                border-radius: 0px 0px 8px 8px;\n                padding: 15px;\n            }\n        ')
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setSpacing(15)
        novo_btn = QPushButton('­ƒæñ Novo Cliente')
        novo_btn.setStyleSheet('\n            QPushButton {\n                background-color: #27ae60;\n                color: white;\n                border: none;\n                padding: 12px 25px;\n                border-radius: 5px;\n                font-weight: bold;\n                font-size: 14px;\n                min-width: 150px;\n            }\n            QPushButton:hover {\n                background-color: #229954;\n            }\n            QPushButton:pressed {\n                background-color: #1e8449;\n            }\n        ')
        novo_btn.clicked.connect(self.novo_cliente)
        buttons_layout.addWidget(novo_btn)
        buttons_layout.addStretch()
        layout.addWidget(buttons_frame)
        self.info_label = QLabel()
        self.info_label.setStyleSheet('\n            QLabel {\n                color: #6c757d;\n                font-size: 12px;\n                padding: 5px 10px;\n                background-color: #f8f9fa;\n                border-radius: 4px;\n            }\n        ')
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)
    def keyPressEvent(self, event):
        if (event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter) and self.busca_input.hasFocus():
            self.filtrar_clientes()
            return
        super().keyPressEvent(event)
    def carregar_clientes(self):
        try:
            conn = sqlite3.connect('app/database/service_orders.db')
            cursor = conn.cursor()
            cursor.execute('\n                SELECT c.id, c.name, c.phone, c.email, c.address,\n                       COUNT(so.id) as total_os\n                FROM clients c\n                LEFT JOIN service_orders so ON c.id = so.client_id\n                WHERE c.user_id = ?\n                GROUP BY c.id, c.name, c.phone, c.email, c.address\n                ORDER BY c.name\n            ', (self.user_id,))
            self.todos_clientes = cursor.fetchall()
            self.atualizar_tabela(self.todos_clientes)
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao carregar clientes: {str(e)}')
        if conn:
            conn.close()
    def atualizar_tabela(self, dados):
        self.tabela.setRowCount(0)
        for row, (id, nome, telefone, email, endereco, total_os) in enumerate(dados):
            self.tabela.insertRow(row)
            id_item = QTableWidgetItem(str(id))
            id_item.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(row, 0, id_item)
            self.tabela.setItem(row, 1, QTableWidgetItem(nome or ''))
            self.tabela.setItem(row, 2, QTableWidgetItem(telefone or ''))
            self.tabela.setItem(row, 3, QTableWidgetItem(email or ''))
            os_item = QTableWidgetItem(f'{total_os} OS')
            os_item.setTextAlignment(Qt.AlignCenter)
            if total_os > 0:
                os_item.setBackground(QColor('#e8f5e8'))
                os_item.setForeground(QColor('#27ae60'))
            else:
                os_item.setBackground(QColor('#f8f9fa'))
                os_item.setForeground(QColor('#6c757d'))
            self.tabela.setItem(row, 4, os_item)
            acoes_widget = QWidget()
            acoes_widget.setMinimumHeight(50)
            acoes_layout = QHBoxLayout(acoes_widget)
            acoes_layout.setContentsMargins(5, 5, 5, 5)
            acoes_layout.setSpacing(4)
            nova_os_btn = QPushButton('NOVA OS')
            nova_os_btn.setStyleSheet('\n                QPushButton {\n                    background-color: #e74c3c;\n                    color: white;\n                    border: none;\n                    padding: 6px 10px;\n                    border-radius: 4px;\n                    font-size: 10px;\n                    font-weight: bold;\n                    min-width: 65px;\n                    max-width: 85px;\n                }\n                QPushButton:hover {\n                    background-color: #c0392b;\n                }\n                QPushButton:pressed {\n                    background-color: #a93226;\n                }\n            ')
            nova_os_btn.setCursor(Qt.PointingHandCursor)
            nova_os_btn.clicked.connect((lambda checked, client_id=id: self.nova_os_cliente(client_id)))
            detalhes_btn = QPushButton('VER')
            detalhes_btn.setStyleSheet('\n                QPushButton {\n                    background-color: #3498db;\n                    color: white;\n                    border: none;\n                    padding: 6px 10px;\n                    border-radius: 4px;\n                    font-size: 10px;\n                    font-weight: bold;\n                    min-width: 65px;\n                    max-width: 85px;\n                }\n                QPushButton:hover {\n                    background-color: #2980b9;\n                }\n                QPushButton:pressed {\n                    background-color: #21618c;\n                }\n            ')
            detalhes_btn.setCursor(Qt.PointingHandCursor)
            detalhes_btn.clicked.connect((lambda checked, client_id=id: self.ver_detalhes_cliente(client_id)))
            editar_btn = QPushButton('EDITAR')
            editar_btn.setStyleSheet('\n                QPushButton {\n                    background-color: #f39c12;\n                    color: white;\n                    border: none;\n                    padding: 6px 10px;\n                    border-radius: 4px;\n                    font-size: 10px;\n                    font-weight: bold;\n                    min-width: 65px;\n                    max-width: 85px;\n                }\n                QPushButton:hover {\n                    background-color: #e67e22;\n                }\n                QPushButton:pressed {\n                    background-color: #d35400;\n                }\n            ')
            editar_btn.setCursor(Qt.PointingHandCursor)
            editar_btn.clicked.connect((lambda checked, client_id=id: self.editar_cliente(client_id)))
            excluir_btn = QPushButton('EXCLUIR')
            excluir_btn.setStyleSheet('\n                QPushButton {\n                    background-color: #95a5a6;\n                    color: white;\n                    border: none;\n                    padding: 6px 10px;\n                    border-radius: 4px;\n                    font-size: 10px;\n                    font-weight: bold;\n                    min-width: 65px;\n                    max-width: 85px;\n                }\n                QPushButton:hover {\n                    background-color: #7f8c8d;\n                }\n                QPushButton:pressed {\n                    background-color: #2c3e50;\n                }\n            ')
            excluir_btn.setCursor(Qt.PointingHandCursor)
            excluir_btn.clicked.connect((lambda checked, client_id=id: self.excluir_cliente(client_id)))
            acoes_layout.addWidget(nova_os_btn)
            acoes_layout.addWidget(detalhes_btn)
            acoes_layout.addWidget(editar_btn)
            acoes_layout.addWidget(excluir_btn)
            self.tabela.setCellWidget(row, 5, acoes_widget)
            continue
        for row in range(self.tabela.rowCount()):
            self.tabela.setRowHeight(row, 60)
        self.atualizar_info_contagem(len(dados))
    def atualizar_info_contagem(self, exibidos):
        total = len(self.todos_clientes) if hasattr(self, 'todos_clientes') else 0
        if exibidos == total:
            self.info_label.setText(f'­ƒôè Exibindo {total} cliente(s) ÔÇó Total de registros: {total}')
            return
        self.info_label.setText(f'­ƒôè Exibindo {exibidos} de {total} cliente(s) ÔÇó Filtro ativo')
    def filtrar_clientes(self):
        texto = self.busca_input.text().lower()
        if not texto:
            self.atualizar_tabela(self.todos_clientes)
            return
        filtrados = []
        for cliente in self.todos_clientes:
            nome = str(cliente[1] or '').lower()
            telefone = str(cliente[2] or '').lower()
            email = str(cliente[3] or '').lower()
            if texto in nome or texto in telefone or texto in email:
                filtrados.append(cliente)
        self.atualizar_tabela(filtrados)
    def novo_cliente(self):
        from app.views.client_form import ClientForm
        dialog = ClientForm(self.user_id, self)
        if dialog.exec_() == ClientForm.Accepted:
            self.carregar_clientes()
    def nova_os_cliente(self, client_id):
        try:
            from app.views.service_order_form import ServiceOrderForm
            dialog = ServiceOrderForm(self.user_id, self)
            if hasattr(dialog, 'cliente_combo'):
                for i in range(dialog.cliente_combo.count()):
                    if not dialog.cliente_combo.itemData(i) == client_id:
                        continue
                    dialog.cliente_combo.setCurrentIndex(i)
                    print(f'Ô£à Cliente ID {client_id} pr├®-selecionado no formul├írio de OS')
                else:
                    print(f'ÔÜá´©Å Cliente ID {client_id} n├úo encontrado no combo')
            if dialog.exec_() == QDialog.Accepted:
                self.carregar_clientes()
                return
        except ImportError:
            QMessageBox.warning(self, 'Aviso', 'M├│dulo de ordens de servi├ºo n├úo encontrado. Verifique se est├í dispon├¡vel.')
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao abrir formul├írio de OS: {str(e)}')
            print(f'ÔØî Erro detalhado: {str(e)}')
    def ver_detalhes_cliente(self, client_id):
        try:
            dialog = ClientDetailsDialog(client_id, self.user_id, self)
            dialog.exec_()
            return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao abrir detalhes do cliente: {str(e)}')
    def editar_cliente(self, client_id):
        dialog = EditClientDialog(client_id, self.user_id, self)
        if dialog.exec_() == QDialog.Accepted:
            self.carregar_clientes()
    def excluir_cliente(self, client_id):
        try:
            conn = sqlite3.connect('app/database/service_orders.db')
            cursor = conn.cursor()
            cursor.execute('\n                SELECT COUNT(*) FROM service_orders\n                WHERE client_id = ? AND user_id = ?\n            ', (client_id, self.user_id))
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
                cursor.execute('\n                    DELETE FROM clients\n                    WHERE id = ? AND user_id = ?\n                ', (client_id, self.user_id))
                conn.commit()
                QMessageBox.information(self, 'Sucesso', 'Cliente exclu├¡do com sucesso!')
                self.carregar_clientes()
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao excluir cliente: {str(e)}')
        if conn:
            conn.close()
