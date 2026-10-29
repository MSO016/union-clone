from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QDateEdit, QScrollArea, QWidget, QFrame, QHeaderView)
from PyQt5.QtCore import (Qt, QDate, QEvent)
from PyQt5.QtGui import QFont
import sqlite3
class DailyReportDialog(QDialog):
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle('Relat├│rio Di├írio')
        self.setModal(True)
        self.setMinimumSize(1000, 700)
        self.showMaximized()
        self.setup_ui()
        self.carregar_relatorio()
    def keyPressEvent(self, event):
        '''CORRE├ç├âO CR├ìTICA: Bloqueia Enter/Return no QDialog inteiro'''
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            return
        super().keyPressEvent(event)
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
        titulo = QLabel('­ƒôè Relat├│rio Di├írio')
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
        self.criar_secao_filtros(layout)
        self.criar_secao_estatisticas(layout)
        self.criar_secao_detalhes(layout)
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
    def criar_secao_filtros(self, layout):
        '''Cria se├º├úo de filtros'''
        secao_frame = QFrame()
        secao_frame.setStyleSheet('\n            QFrame {\n                background-color: #ffffff;\n                border: 1px solid #e0e0e0;\n                border-radius: 8px;\n                padding: 20px;\n            }\n        ')
        secao_layout = QVBoxLayout(secao_frame)
        titulo_secao = QLabel('­ƒôà Data do Relat├│rio')
        titulo_secao.setStyleSheet('\n            QLabel {\n                font-size: 16px;\n                font-weight: bold;\n                color: #2c3e50;\n                margin-bottom: 15px;\n                padding-bottom: 10px;\n                border-bottom: 2px solid #3498db;\n            }\n        ')
        secao_layout.addWidget(titulo_secao)
        data_layout = QHBoxLayout()
        data_label = QLabel('­ƒôå Selecionar Data:')
        data_label.setStyleSheet('font-weight: bold; color: #34495e;')
        self.data_edit = QDateEdit()
        self.data_edit.setDate(QDate.currentDate())
        self.data_edit.setCalendarPopup(True)
        self.data_edit.dateChanged.connect(self.carregar_relatorio)
        self.data_edit.setStyleSheet('\n            QDateEdit {\n                border: 1px solid #bdc3c7;\n                border-radius: 4px;\n                padding: 6px;\n                min-width: 150px;\n                background-color: #f8f9fa;\n                color: #2c3e50;\n            }\n            QDateEdit:focus {\n                border: 2px solid #3498db;\n                background-color: #ffffff;\n            }\n        ')
        data_layout.addWidget(data_label)
        data_layout.addWidget(self.data_edit)
        data_layout.addStretch()
        secao_layout.addLayout(data_layout)
        layout.addWidget(secao_frame)
    def criar_secao_estatisticas(self, layout):
        '''Cria se├º├úo de estat├¡sticas'''
        secao_frame = QFrame()
        secao_frame.setStyleSheet('\n            QFrame {\n                background-color: #ffffff;\n                border: 1px solid #e0e0e0;\n                border-radius: 8px;\n                padding: 20px;\n            }\n        ')
        secao_layout = QVBoxLayout(secao_frame)
        titulo_secao = QLabel('­ƒôê Estat├¡sticas do Dia')
        titulo_secao.setStyleSheet('\n            QLabel {\n                font-size: 16px;\n                font-weight: bold;\n                color: #2c3e50;\n                margin-bottom: 15px;\n                padding-bottom: 10px;\n                border-bottom: 2px solid #e67e22;\n            }\n        ')
        secao_layout.addWidget(titulo_secao)
        stats_layout = QHBoxLayout()
        self.os_abertas = QLabel('­ƒôØ OS Abertas: 0')
        self.os_abertas.setStyleSheet('\n            QLabel {\n                padding: 12px;\n                background-color: #f39c12;\n                color: white;\n                border-radius: 6px;\n                font-weight: bold;\n                text-align: center;\n            }\n        ')
        stats_layout.addWidget(self.os_abertas)
        self.os_sucesso = QLabel('Ô£à Conclu├¡das com Sucesso: 0')
        self.os_sucesso.setStyleSheet('\n            QLabel {\n                padding: 12px;\n                background-color: #27ae60;\n                color: white;\n                border-radius: 6px;\n                font-weight: bold;\n                text-align: center;\n            }\n        ')
        stats_layout.addWidget(self.os_sucesso)
        self.os_sem_solucao = QLabel('ÔØî Conclu├¡das sem Solu├º├úo: 0')
        self.os_sem_solucao.setStyleSheet('\n            QLabel {\n                padding: 12px;\n                background-color: #e74c3c;\n                color: white;\n                border-radius: 6px;\n                font-weight: bold;\n                text-align: center;\n            }\n        ')
        stats_layout.addWidget(self.os_sem_solucao)
        self.faturamento_total = QLabel('­ƒÆ░ Faturamento: R$ 0,00')
        self.faturamento_total.setStyleSheet('\n            QLabel {\n                padding: 12px;\n                background-color: #16a085;\n                color: white;\n                border-radius: 6px;\n                font-weight: bold;\n                text-align: center;\n            }\n        ')
        stats_layout.addWidget(self.faturamento_total)
        secao_layout.addLayout(stats_layout)
        layout.addWidget(secao_frame)
    def criar_secao_detalhes(self, layout):
        '''Cria se├º├úo de detalhes da tabela'''
        secao_frame = QFrame()
        secao_frame.setStyleSheet('\n            QFrame {\n                background-color: #ffffff;\n                border: 1px solid #e0e0e0;\n                border-radius: 8px;\n                padding: 20px;\n            }\n        ')
        secao_layout = QVBoxLayout(secao_frame)
        titulo_secao = QLabel('­ƒôï Detalhes das Ordens de Servi├ºo')
        titulo_secao.setStyleSheet('\n            QLabel {\n                font-size: 16px;\n                font-weight: bold;\n                color: #2c3e50;\n                margin-bottom: 15px;\n                padding-bottom: 10px;\n                border-bottom: 2px solid #27ae60;\n            }\n        ')
        secao_layout.addWidget(titulo_secao)
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(8)
        self.tabela.setHorizontalHeaderLabels(['OS #', 'Cliente', 'Dispositivo', 'Problema', 'Status', 'Valor', 'Entrada', 'Conclus├úo'])
        self.tabela.horizontalHeader().setStretchLastSection(False)
        header = self.tabela.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.tabela.setStyleSheet('\n            QTableWidget {\n                border: 1px solid #bdc3c7;\n                border-radius: 4px;\n                background-color: #ffffff !important;\n                gridline-color: #ecf0f1;\n                color: #2c3e50 !important;\n            }\n            QTableWidget::item {\n                padding: 8px;\n                border-bottom: 1px solid #ecf0f1;\n                background-color: #ffffff !important;\n                color: #2c3e50 !important;\n                min-height: 25px;\n                border-right: 1px solid #ecf0f1;\n            }\n            QTableWidget::item:selected {\n                background-color: #3498db !important;\n                color: #ffffff !important;\n            }\n            QTableWidget::item:hover {\n                background-color: #f8f9fa !important;\n                color: #2c3e50 !important;\n            }\n            QHeaderView::section {\n                background-color: #f8f9fa !important;\n                border: 1px solid #bdc3c7;\n                padding: 8px;\n                font-weight: bold;\n                color: #2c3e50 !important;\n            }\n        ')
        secao_layout.addWidget(self.tabela)
        layout.addWidget(secao_frame)
    def carregar_relatorio(self):
        try:
            conn = sqlite3.connect('app/database/service_orders.db')
            cursor = conn.cursor()
            data_selecionada = self.data_edit.date().toString('yyyy-MM-dd')
            print(f'DEBUG: Carregando relat├│rio para data: {data_selecionada}')
            cursor.execute('\n                SELECT COUNT(*) FROM service_orders\n                WHERE date(entry_date) = ?\n                AND user_id = ?\n            ', (data_selecionada, self.user_id))
            total_abertas = cursor.fetchone()[0]
            self.os_abertas.setText(f'OS Abertas: {total_abertas}')
            print(f'DEBUG: OS abertas na data {data_selecionada}: {total_abertas}')
            cursor.execute("\n                SELECT COUNT(*) FROM service_orders\n                WHERE date(completion_date) = ?\n                AND status = 'concluido_sucesso'\n                AND user_id = ?\n            ", (data_selecionada, self.user_id))
            os_sucesso = cursor.fetchone()[0]
            self.os_sucesso.setText(f'Conclu├¡das com Sucesso: {os_sucesso}')
            print(f'DEBUG: OS conclu├¡das com sucesso na data {data_selecionada}: {os_sucesso}')
            cursor.execute("\n                SELECT COUNT(*) FROM service_orders\n                WHERE date(completion_date) = ?\n                AND status = 'concluido_sem_solucao'\n                AND user_id = ?\n            ", (data_selecionada, self.user_id))
            total_sem_solucao = cursor.fetchone()[0]
            self.os_sem_solucao.setText(f'Conclu├¡das sem Solu├º├úo: {total_sem_solucao}')
            print(f'DEBUG: OS conclu├¡das sem solu├º├úo na data {data_selecionada}: {total_sem_solucao}')
            cursor.execute('\n                SELECT id, status, completion_date, date(completion_date) as data_apenas \n                FROM service_orders \n                WHERE user_id = ? \n                AND completion_date IS NOT NULL\n                ORDER BY completion_date DESC\n            ', (self.user_id,))
            debug_os = cursor.fetchall()
            print(f'DEBUG: Total de OS com completion_date: {len(debug_os)}')
            for os_debug in debug_os:
                print(f'DEBUG: OS {os_debug[0]}, Status: {os_debug[1]}, Data completa: {os_debug[2]}, Data apenas: {os_debug[3]}')
            cursor.execute("\n                SELECT COALESCE(SUM(service_value), 0.0) \n                FROM service_orders\n                WHERE date(completion_date) = ?\n                AND status IN ('concluido_sucesso', 'concluido_sem_solucao')\n                AND user_id = ?\n            ", (data_selecionada, self.user_id))
            faturamento = cursor.fetchone()[0]
            faturamento_formatado = f'R$ {faturamento:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
            self.faturamento_total.setText(f'­ƒÆ░ Faturamento: {faturamento_formatado}')
            print(f'DEBUG: Faturamento total do dia: R$ {faturamento:.2f}')
            cursor.execute('\n                SELECT so.id, c.name, so.device_type, so.brand, so.model, \n                       so.reported_issue, so.status, so.service_value, \n                       so.entry_date, so.completion_date\n                FROM service_orders so\n                JOIN clients c ON so.client_id = c.id\n                WHERE (date(so.entry_date) = ? OR date(so.completion_date) = ?)\n                AND so.user_id = ?\n                ORDER BY so.entry_date DESC\n            ', (data_selecionada, data_selecionada, self.user_id))
            resultados = cursor.fetchall()
            print(f'DEBUG: OS encontradas para tabela: {len(resultados)}')
            self.tabela.setRowCount(0)
            for row, (os_id, cliente, device_type, brand, model, reported_issue, status, service_value, entrada, conclusao) in enumerate(resultados):
                self.tabela.insertRow(row)
                status_display = {'em_reparo': 'Em Reparo', 'concluido_sucesso': 'Conclu├¡do com Sucesso', 'concluido_sem_solucao': 'Conclu├¡do sem Solu├º├úo'}.get(status, status)
                dispositivo = f'{brand} {model}'
                if device_type:
                    dispositivo += f' ({device_type})'
                if service_value and service_value > 0:
                    valor_formatado = f'R$ {service_value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
                else:
                    valor_formatado = '-'
                self.tabela.setItem(row, 0, QTableWidgetItem(str(os_id) if os_id else 'N/A'))
                self.tabela.setItem(row, 1, QTableWidgetItem(cliente if cliente else 'Cliente n├úo encontrado'))
                self.tabela.setItem(row, 2, QTableWidgetItem(dispositivo if dispositivo.strip() else 'N├úo informado'))
                self.tabela.setItem(row, 3, QTableWidgetItem(reported_issue if reported_issue else 'N├úo informado'))
                self.tabela.setItem(row, 4, QTableWidgetItem(status_display))
                self.tabela.setItem(row, 5, QTableWidgetItem(valor_formatado))
                self.tabela.setItem(row, 6, QTableWidgetItem(entrada if entrada else 'N/A'))
                conclusao_display = conclusao if conclusao else 'Em andamento'
                self.tabela.setItem(row, 7, QTableWidgetItem(conclusao_display))
                print(f'DEBUG: Adicionada ├á tabela - OS {os_id}, Cliente: {cliente}, Status: {status_display}, Valor: {valor_formatado}')
                continue
        except Exception as e:
            print(f'DEBUG: Erro no relat├│rio di├írio: {str(e)}')
            QMessageBox.critical(self, 'Erro', f'Erro ao carregar relat├│rio: {str(e)}')
        if conn:
            conn.close()
