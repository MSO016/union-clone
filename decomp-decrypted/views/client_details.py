from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox, QScrollArea, QWidget, QFrame, QGridLayout, QTableWidget, QTableWidgetItem)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import (QFont, QColor, QBrush)
import sqlite3
from datetime import datetime
class ClientDetailsDialog(QDialog):
    def __init__(self, client_id, user_id, parent=None):
        super().__init__(parent)
        self.client_id = client_id
        self.user_id = user_id
        self.is_admin = parent.is_admin if hasattr(parent, 'is_admin') else False
        self.setWindowTitle('Detalhes do Cliente')
        self.setModal(True)
        self.setMinimumSize(1000, 700)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setSizeGripEnabled(True)
        self.showMaximized()
        self.setup_ui()
        self.carregar_detalhes()
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)
        header_layout = QHBoxLayout()
        voltar_btn = QPushButton('ÔåÉ Voltar')
        voltar_btn.setStyleSheet('\n            QPushButton {\n                background-color: #6c757d;\n                color: white;\n                border: none;\n                padding: 12px 25px;\n                border-radius: 5px;\n                font-weight: bold;\n                font-size: 14px;\n            }\n            QPushButton:hover {\n                background-color: #5a6268;\n            }\n        ')
        voltar_btn.clicked.connect(self.reject)
        header_layout.addWidget(voltar_btn)
        titulo = QLabel('Detalhes do Cliente')
        titulo.setStyleSheet('font-size: 24px; font-weight: bold; color: #2c3e50; margin-left: 20px;')
        header_layout.addWidget(titulo)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { border: none; }')
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        self.cliente_frame = self.criar_secao_info('Informa├º├Áes do Cliente')
        content_layout.addWidget(self.cliente_frame)
        self.historico_frame = self.criar_secao_historico()
        content_layout.addWidget(self.historico_frame)
        self.stats_frame = self.criar_secao_estatisticas()
        content_layout.addWidget(self.stats_frame)
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        self.criar_botoes_acao(layout)
    def criar_secao_info(self, titulo):
        frame = QFrame()
        frame.setStyleSheet('\n            QFrame {\n                background-color: white;\n                border: 1px solid #ddd;\n                border-radius: 8px;\n                padding: 20px;\n            }\n        ')
        layout = QVBoxLayout(frame)
        titulo_label = QLabel(titulo)
        titulo_label.setStyleSheet('font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 15px;')
        layout.addWidget(titulo_label)
        self.info_container = QGridLayout()
        layout.addLayout(self.info_container)
        return frame
    def criar_secao_historico(self):
        frame = QFrame()
        frame.setStyleSheet('\n            QFrame {\n                background-color: white;\n                border: 1px solid #ddd;\n                border-radius: 8px;\n                padding: 20px;\n            }\n        ')
        layout = QVBoxLayout(frame)
        titulo_label = QLabel('Hist├│rico de Ordens de Servi├ºo')
        titulo_label.setStyleSheet('font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 15px;')
        layout.addWidget(titulo_label)
        self.historico_table = QTableWidget()
        self.historico_table.setColumnCount(6)
        self.historico_table.setHorizontalHeaderLabels(['OS #', 'Dispositivo', 'Problema', 'Status', 'Data Entrada', 'Data Conclus├úo'])
        self.historico_table.horizontalHeader().setStretchLastSection(True)
        self.historico_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.historico_table.setAlternatingRowColors(False)
        self.historico_table.setStyleSheet('\n            QTableWidget {\n                gridline-color: #ecf0f1;\n                background-color: white;\n                selection-background-color: #e8f4fd;\n                selection-color: #2c3e50;\n            }\n            QTableWidget::item {\n                padding: 8px;\n                border-bottom: 1px solid #ecf0f1;\n                color: #2c3e50;\n            }\n            QHeaderView::section {\n                background-color: #34495e;\n                color: white;\n                padding: 10px;\n                border: none;\n                font-weight: bold;\n            }\n        ')
        layout.addWidget(self.historico_table)
        return frame
    def criar_secao_estatisticas(self):
        frame = QFrame()
        frame.setStyleSheet('\n            QFrame {\n                background-color: white;\n                border: 1px solid #ddd;\n                border-radius: 8px;\n                padding: 20px;\n            }\n        ')
        layout = QVBoxLayout(frame)
        titulo_label = QLabel('Estat├¡sticas do Cliente')
        titulo_label.setStyleSheet('font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 15px;')
        layout.addWidget(titulo_label)
        self.stats_container = QHBoxLayout()
        layout.addLayout(self.stats_container)
        return frame
    def criar_botoes_acao(self, layout):
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        nova_os_btn = QPushButton('NOVA OS PARA ESTE CLIENTE')
        nova_os_btn.setStyleSheet('\n            QPushButton {\n                background-color: #e74c3c;\n                color: white;\n                border: none;\n                padding: 12px 25px;\n                border-radius: 5px;\n                font-weight: bold;\n                font-size: 14px;\n            }\n            QPushButton:hover {\n                background-color: #c0392b;\n            }\n        ')
        nova_os_btn.clicked.connect(self.nova_os_cliente)
        buttons_layout.addWidget(nova_os_btn)
        editar_btn = QPushButton('EDITAR CLIENTE')
        editar_btn.setStyleSheet('\n            QPushButton {\n                background-color: #3498db;\n                color: white;\n                border: none;\n                padding: 12px 25px;\n                border-radius: 5px;\n                font-weight: bold;\n                font-size: 14px;\n            }\n            QPushButton:hover {\n                background-color: #2980b9;\n            }\n        ')
        editar_btn.clicked.connect(self.editar_cliente)
        buttons_layout.addWidget(editar_btn)
        buttons_layout.addStretch()
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
    def carregar_detalhes(self):
        try:
            conn = sqlite3.connect('app/database/service_orders.db')
            cursor = conn.cursor()
            self.verificar_e_adicionar_colunas(cursor)
            cursor.execute('PRAGMA table_info(clients)')
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao carregar detalhes: {str(e)}')
        try:
            colunas_existentes = [coluna[1] for coluna in cursor.fetchall()]
            if 'tipo_cliente' in colunas_existentes and 'observacoes' in colunas_existentes:
                cursor.execute('\n                    SELECT id, name, phone, email, address, tipo_cliente, observacoes\n                    FROM clients \n                    WHERE id = ? AND user_id = ?\n                ', (self.client_id, self.user_id))
            else:
                cursor.execute('\n                    SELECT id, name, phone, email, address\n                    FROM clients \n                    WHERE id = ? AND user_id = ?\n                ', (self.client_id, self.user_id))
            cliente_info = cursor.fetchone()
            if not cliente_info:
                QMessageBox.warning(self, 'Erro', 'Cliente n├úo encontrado.')
                self.reject()
                if conn:
                    conn.close()
                    return
                return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao carregar detalhes: {str(e)}')
        try:
            if len(cliente_info) == 5:
                cliente_info = cliente_info + ('pessoa_fisica', '')
            self.preencher_info_cliente(cliente_info)
            self.carregar_historico_os(cursor)
            self.carregar_estatisticas(cursor)
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao carregar detalhes: {str(e)}')
        if conn:
            conn.close()
    def preencher_info_cliente(self, cliente_info):
        id_cliente, nome, telefone, email, endereco, tipo_cliente, observacoes = cliente_info
        while self.info_container.count():
            child = self.info_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        tipo_display = '­ƒæñ Pessoa F├¡sica' if (tipo_cliente or 'pessoa_fisica') == 'pessoa_fisica' else '­ƒÅó Lojista'
        infos = [('ID do Cliente:', str(id_cliente)), ('Nome Completo:', nome or 'N├úo informado'), ('Telefone:', telefone or 'N├úo informado'), ('E-mail:', email or 'N├úo informado'), ('Endere├ºo:', endereco or 'N├úo informado'), ('Tipo de Cliente:', tipo_display), ('Observa├º├Áes:', observacoes or 'Nenhuma observa├º├úo registrada')]
        for i, (label, valor) in enumerate(infos):
            label_widget = QLabel(label)
            label_widget.setStyleSheet('\n                QLabel {\n                    font-weight: bold;\n                    color: #34495e;\n                    font-size: 14px;\n                    padding: 5px 0;\n                }\n            ')
            valor_widget = QLabel(valor)
            valor_widget.setStyleSheet('\n                QLabel {\n                    color: #2c3e50;\n                    font-size: 14px;\n                    padding: 5px 10px;\n                    background-color: #f8f9fa;\n                    border: 1px solid #e9ecef;\n                    border-radius: 4px;\n                    margin-bottom: 10px;\n                }\n            ')
            valor_widget.setWordWrap(True)
            self.info_container.addWidget(label_widget, i, 0)
            self.info_container.addWidget(valor_widget, i, 1)
        self.info_container.setColumnStretch(0, 0)
        self.info_container.setColumnStretch(1, 1)
    def carregar_historico_os(self, cursor):
        try:
            cursor.execute('\n                SELECT id, device_type, brand, model, reported_issue, \n                       status, entry_date, completion_date\n                FROM service_orders \n                WHERE client_id = ? AND user_id = ?\n                ORDER BY entry_date DESC\n            ', (self.client_id, self.user_id))
            historico = cursor.fetchall()
            self.historico_table.setRowCount(0)
            for row, (os_id, device_type, brand, model, reported_issue, status, entry_date, completion_date) in enumerate(historico):
                self.historico_table.insertRow(row)
                dispositivo = f'{device_type or 'N/A'}'
                if brand:
                    dispositivo += f' - {brand}'
                if model:
                    dispositivo += f' {model}'
                data_entrada = self.formatar_data(entry_date)
                data_conclusao = self.formatar_data(completion_date) if completion_date else 'Em andamento'
                os_item = QTableWidgetItem(f'OS #{os_id}')
                dispositivo_item = QTableWidgetItem(dispositivo)
                problema_item = QTableWidgetItem(reported_issue or 'N├úo informado')
                status_item = QTableWidgetItem(self.traduzir_status(status))
                entrada_item = QTableWidgetItem(data_entrada)
                conclusao_item = QTableWidgetItem(data_conclusao)
                self.historico_table.setItem(row, 0, os_item)
                self.historico_table.setItem(row, 1, dispositivo_item)
                self.historico_table.setItem(row, 2, problema_item)
                self.historico_table.setItem(row, 3, status_item)
                self.historico_table.setItem(row, 4, entrada_item)
                self.historico_table.setItem(row, 5, conclusao_item)
                cor_fundo = QColor('white') if row % 2 == 0 else QColor('#f8f9fa')
                for item in os_item, dispositivo_item, problema_item, entrada_item, conclusao_item:
                    item.setBackground(cor_fundo)
                    item.setForeground(QColor('#2c3e50'))
                self.aplicar_cor_status(status_item, status)
                self.historico_table.setRowHeight(row, 45)
                continue
            self.historico_table.resizeColumnsToContents()
            self.historico_table.update()
            self.historico_table.repaint()
            return
        except Exception as e:
            QMessageBox.warning(self, 'Aviso', f'Erro ao carregar hist├│rico: {str(e)}')
    def carregar_estatisticas(self, cursor):
        try:
            while self.stats_container.count():
                child = self.stats_container.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            stats = [('Total de OS', 'SELECT COUNT(*) FROM service_orders WHERE client_id = ?'), ('OS Conclu├¡das', "SELECT COUNT(*) FROM service_orders WHERE client_id = ? AND status LIKE 'concluido%'"), ('OS Abertas', "SELECT COUNT(*) FROM service_orders WHERE client_id = ? AND status = 'aberto'"), ('OS em Reparo', "SELECT COUNT(*) FROM service_orders WHERE client_id = ? AND status IN ('em_andamento', 'em_reparo')")]
            for titulo, query in stats:
                cursor.execute(query, (self.client_id,))
                valor = cursor.fetchone()[0]
                card = self.criar_card_estatistica(titulo, str(valor))
                self.stats_container.addWidget(card)
            self.stats_container.addStretch()
            return
        except Exception as e:
            QMessageBox.warning(self, 'Aviso', f'Erro ao carregar estat├¡sticas: {str(e)}')
    def criar_card_estatistica(self, titulo, valor):
        card = QFrame()
        card.setStyleSheet('\n            QFrame {\n                background-color: #3498db;\n                border-radius: 8px;\n                padding: 15px;\n                margin: 5px;\n                min-width: 150px;\n                max-width: 200px;\n            }\n        ')
        layout = QVBoxLayout(card)
        layout.setSpacing(5)
        valor_label = QLabel(valor)
        valor_label.setStyleSheet('\n            QLabel {\n                color: white;\n                font-size: 28px;\n                font-weight: bold;\n                text-align: center;\n            }\n        ')
        valor_label.setAlignment(Qt.AlignCenter)
        titulo_label = QLabel(titulo)
        titulo_label.setStyleSheet('\n            QLabel {\n                color: white;\n                font-size: 12px;\n                text-align: center;\n            }\n        ')
        titulo_label.setAlignment(Qt.AlignCenter)
        titulo_label.setWordWrap(True)
        layout.addWidget(valor_label)
        layout.addWidget(titulo_label)
        return card
    def formatar_data(self, data_str):
        if not data_str:
            return 'N/A'
        try:
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y'):
                try:
                    dt = datetime.strptime(data_str, fmt)
                except ValueError:
                    continue
                return dt.strftime('%d/%m/%Y %H:%M')
        except:
            return 'N/A'
        try:
            return str(data_str)
        except:
            return 'N/A'
    def traduzir_status(self, status):
        traducoes = {'aberto': 'Aberto', 'em_andamento': 'Em Andamento', 'em_reparo': 'Em Reparo', 'concluido_sucesso': 'Conclu├¡do com Sucesso', 'concluido_sem_solucao': 'Conclu├¡do sem Solu├º├úo', 'cancelado': 'Cancelado'}
        if status:
            return traducoes.get(status, status.replace('_', ' ').title())
        return None(None, 'N/A')
    def aplicar_cor_status(self, item, status):
        cores = {'aberto': '#e74c3c', 'em_andamento': '#f39c12', 'em_reparo': '#3498db', 'concluido_sucesso': '#27ae60', 'concluido_sem_solucao': '#e67e22', 'cancelado': '#95a5a6'}
        item.setTextAlignment(Qt.AlignCenter)
        font = item.font()
        font.setBold(True)
        item.setFont(font)
        if status in cores:
            cor_fundo = QColor(cores[status])
            cor_texto = QColor('white')
            item.setBackground(QBrush(cor_fundo))
            item.setForeground(QBrush(cor_texto))
            return
        cor_fundo = QColor('#ecf0f1')
        cor_texto = QColor('#2c3e50')
        item.setBackground(QBrush(cor_fundo))
        item.setForeground(QBrush(cor_texto))
    def nova_os_cliente(self):
        try:
            from app.views.service_order_form import ServiceOrderForm
            dialog = ServiceOrderForm(self.user_id, self)
            if hasattr(dialog, 'cliente_combo'):
                for i in range(dialog.cliente_combo.count()):
                    if not dialog.cliente_combo.itemData(i) == self.client_id:
                        continue
                    dialog.cliente_combo.setCurrentIndex(i)
                    break
            if dialog.exec_() == QDialog.Accepted:
                self.carregar_detalhes()
                QMessageBox.information(self, 'Sucesso', 'Nova ordem de servi├ºo criada com sucesso!')
                return
        except ImportError:
            QMessageBox.warning(self, 'Erro', 'M├│dulo de cria├º├úo de OS n├úo encontrado.')
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao abrir formul├írio de OS: {str(e)}')
    def editar_cliente(self):
        try:
            from app.views.edit_client import EditClientDialog
            dialog = EditClientDialog(self.client_id, self.user_id, self)
            if dialog.exec_() == QDialog.Accepted:
                self.carregar_detalhes()
                QMessageBox.information(self, 'Sucesso', 'Cliente editado com sucesso!')
                return
        except ImportError:
            QMessageBox.warning(self, 'Erro', 'M├│dulo de edi├º├úo de cliente n├úo encontrado.')
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao abrir formul├írio de edi├º├úo: {str(e)}')
# WARNING: Decompyle incomplete
