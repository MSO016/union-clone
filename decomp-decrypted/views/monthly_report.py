from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QComboBox, QScrollArea, QWidget, QFrame)
from PyQt5.QtCore import (Qt, QDate, QEvent)
from PyQt5.QtGui import QFont
import sqlite3
import calendar
class MonthlyReportDialog(QDialog):
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle('Relat├│rio Mensal')
        self.setModal(True)
        self.setMinimumSize(1000, 700)
        self.showMaximized()
        self.setup_ui()
        self.carregar_relatorio()
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            return
        super().keyPressEvent(event)
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
        titulo = QLabel('­ƒôè Relat├│rio Mensal')
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
        secao_frame = QFrame()
        secao_frame.setStyleSheet('\n            QFrame {\n                background-color: #ffffff;\n                border: 1px solid #e0e0e0;\n                border-radius: 8px;\n                padding: 20px;\n            }\n        ')
        secao_layout = QVBoxLayout(secao_frame)
        titulo_secao = QLabel('­ƒôà Per├¡odo do Relat├│rio')
        titulo_secao.setStyleSheet('\n            QLabel {\n                font-size: 16px;\n                font-weight: bold;\n                color: #2c3e50;\n                margin-bottom: 15px;\n                padding-bottom: 10px;\n                border-bottom: 2px solid #3498db;\n            }\n        ')
        secao_layout.addWidget(titulo_secao)
        data_layout = QHBoxLayout()
        mes_label = QLabel('­ƒôà M├¬s:')
        mes_label.setStyleSheet('font-weight: bold; color: #34495e;')
        self.mes_combo = QComboBox()
        self.mes_combo.setFocusPolicy(Qt.StrongFocus)
        self.mes_combo.installEventFilter(self)
        meses = ['Janeiro', 'Fevereiro', 'Mar├ºo', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        self.mes_combo.addItems(meses)
        self.mes_combo.setCurrentIndex(QDate.currentDate().month() - 1)
        self.mes_combo.currentIndexChanged.connect(self.carregar_relatorio)
        self.mes_combo.setStyleSheet('\n            QComboBox {\n                border: 1px solid #bdc3c7;\n                border-radius: 4px;\n                padding: 6px;\n                min-width: 120px;\n                background-color: #f8f9fa;\n                color: #2c3e50;\n            }\n            QComboBox:focus {\n                border: 2px solid #3498db;\n                background-color: #ffffff;\n            }\n            QComboBox::drop-down {\n                border: none;\n                width: 20px;\n            }\n            QComboBox::down-arrow {\n                image: none;\n                border-left: 5px solid transparent;\n                border-right: 5px solid transparent;\n                border-top: 5px solid #7f8c8d;\n                width: 0;\n                height: 0;\n            }\n            QComboBox QAbstractItemView {\n                background-color: #ffffff;\n                border: 1px solid #bdc3c7;\n                selection-background-color: #3498db;\n                selection-color: #ffffff;\n                color: #2c3e50;\n                padding: 4px;\n            }\n            QComboBox QAbstractItemView::item {\n                min-height: 25px;\n                padding: 4px;\n                background-color: #ffffff;\n                color: #2c3e50;\n            }\n            QComboBox QAbstractItemView::item:selected {\n                background-color: #3498db;\n                color: #ffffff;\n            }\n            QComboBox QAbstractItemView::item:hover {\n                background-color: #ecf0f1;\n                color: #2c3e50;\n            }\n        ')
        data_layout.addWidget(mes_label)
        data_layout.addWidget(self.mes_combo)
        ano_label = QLabel('­ƒôå Ano:')
        ano_label.setStyleSheet('font-weight: bold; color: #34495e; margin-left: 20px;')
        self.ano_combo = QComboBox()
        self.ano_combo.setFocusPolicy(Qt.StrongFocus)
        self.ano_combo.installEventFilter(self)
        ano_atual = QDate.currentDate().year()
        anos = [str(ano) for ano in range(ano_atual - 2, ano_atual + 1)]
        self.ano_combo.addItems(anos)
        self.ano_combo.setCurrentText(str(ano_atual))
        self.ano_combo.currentIndexChanged.connect(self.carregar_relatorio)
        self.ano_combo.setStyleSheet('\n            QComboBox {\n                border: 1px solid #bdc3c7;\n                border-radius: 4px;\n                padding: 6px;\n                min-width: 100px;\n                background-color: #f8f9fa;\n                color: #2c3e50;\n            }\n            QComboBox:focus {\n                border: 2px solid #3498db;\n                background-color: #ffffff;\n            }\n            QComboBox::drop-down {\n                border: none;\n                width: 20px;\n            }\n            QComboBox::down-arrow {\n                image: none;\n                border-left: 5px solid transparent;\n                border-right: 5px solid transparent;\n                border-top: 5px solid #7f8c8d;\n                width: 0;\n                height: 0;\n            }\n            QComboBox QAbstractItemView {\n                background-color: #ffffff;\n                border: 1px solid #bdc3c7;\n                selection-background-color: #3498db;\n                selection-color: #ffffff;\n                color: #2c3e50;\n                padding: 4px;\n            }\n            QComboBox QAbstractItemView::item {\n                min-height: 25px;\n                padding: 4px;\n                background-color: #ffffff;\n                color: #2c3e50;\n            }\n            QComboBox QAbstractItemView::item:selected {\n                background-color: #3498db;\n                color: #ffffff;\n            }\n            QComboBox QAbstractItemView::item:hover {\n                background-color: #ecf0f1;\n                color: #2c3e50;\n            }\n        ')
        data_layout.addWidget(ano_label)
        data_layout.addWidget(self.ano_combo)
        data_layout.addStretch()
        secao_layout.addLayout(data_layout)
        layout.addWidget(secao_frame)
    def eventFilter(self, obj, event):
        if (obj == self.mes_combo or obj == self.ano_combo) and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                return True
        return super().eventFilter(obj, event)
    def criar_secao_estatisticas(self, layout):
        secao_frame = QFrame()
        secao_frame.setStyleSheet('\n            QFrame {\n                background-color: #ffffff;\n                border: 1px solid #e0e0e0;\n                border-radius: 8px;\n                padding: 20px;\n            }\n        ')
        secao_layout = QVBoxLayout(secao_frame)
        titulo_secao = QLabel('­ƒôê Estat├¡sticas do Per├¡odo')
        titulo_secao.setStyleSheet('\n            QLabel {\n                font-size: 16px;\n                font-weight: bold;\n                color: #2c3e50;\n                margin-bottom: 15px;\n                padding-bottom: 10px;\n                border-bottom: 2px solid #e67e22;\n            }\n        ')
        secao_layout.addWidget(titulo_secao)
        stats_layout = QHBoxLayout()
        self.total_os = QLabel('­ƒôè Total de OS: 0')
        self.total_os.setStyleSheet('\n            QLabel {\n                padding: 12px;\n                background-color: #3498db;\n                color: white;\n                border-radius: 6px;\n                font-weight: bold;\n                text-align: center;\n            }\n        ')
        stats_layout.addWidget(self.total_os)
        self.os_sucesso = QLabel('Ô£à Conclu├¡das com Sucesso: 0')
        self.os_sucesso.setStyleSheet('\n            QLabel {\n                padding: 12px;\n                background-color: #27ae60;\n                color: white;\n                border-radius: 6px;\n                font-weight: bold;\n                text-align: center;\n            }\n        ')
        stats_layout.addWidget(self.os_sucesso)
        self.os_sem_solucao = QLabel('ÔØî Conclu├¡das sem Solu├º├úo: 0')
        self.os_sem_solucao.setStyleSheet('\n            QLabel {\n                padding: 12px;\n                background-color: #e74c3c;\n                color: white;\n                border-radius: 6px;\n                font-weight: bold;\n                text-align: center;\n            }\n        ')
        stats_layout.addWidget(self.os_sem_solucao)
        self.os_em_reparo = QLabel('­ƒöº Em Reparo: 0')
        self.os_em_reparo.setStyleSheet('\n            QLabel {\n                padding: 12px;\n                background-color: #f39c12;\n                color: white;\n                border-radius: 6px;\n                font-weight: bold;\n                text-align: center;\n            }\n        ')
        stats_layout.addWidget(self.os_em_reparo)
        self.taxa_sucesso = QLabel('­ƒôê Taxa de Sucesso: 0%')
        self.taxa_sucesso.setStyleSheet('\n            QLabel {\n                padding: 12px;\n                background-color: #9b59b6;\n                color: white;\n                border-radius: 6px;\n                font-weight: bold;\n                text-align: center;\n            }\n        ')
        stats_layout.addWidget(self.taxa_sucesso)
        self.faturamento_total = QLabel('­ƒÆ░ Faturamento: R$ 0,00')
        self.faturamento_total.setStyleSheet('\n            QLabel {\n                padding: 12px;\n                background-color: #16a085;\n                color: white;\n                border-radius: 6px;\n                font-weight: bold;\n                text-align: center;\n            }\n        ')
        stats_layout.addWidget(self.faturamento_total)
        secao_layout.addLayout(stats_layout)
        layout.addWidget(secao_frame)
    def criar_secao_detalhes(self, layout):
        secao_frame = QFrame()
        secao_frame.setStyleSheet('\n            QFrame {\n                background-color: #ffffff;\n                border: 1px solid #e0e0e0;\n                border-radius: 8px;\n                padding: 20px;\n            }\n        ')
        secao_layout = QVBoxLayout(secao_frame)
        titulo_secao = QLabel('­ƒôï Detalhes das Ordens de Servi├ºo')
        titulo_secao.setStyleSheet('\n            QLabel {\n                font-size: 16px;\n                font-weight: bold;\n                color: #2c3e50;\n                margin-bottom: 15px;\n                padding-bottom: 10px;\n                border-bottom: 2px solid #27ae60;\n            }\n        ')
        secao_layout.addWidget(titulo_secao)
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(9)
        self.tabela.setHorizontalHeaderLabels(['OS #', 'Cliente', 'Dispositivo', 'Problema', 'Status', 'Valor', 'Entrada', 'Conclus├úo', 'Tempo de Reparo'])
        self.tabela.horizontalHeader().setStretchLastSection(False)
        from PyQt5.QtWidgets import QHeaderView
        header = self.tabela.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        self.tabela.setStyleSheet('\n            QTableWidget {\n                border: 1px solid #bdc3c7;\n                border-radius: 4px;\n                background-color: #ffffff !important;\n                gridline-color: #ecf0f1;\n                color: #2c3e50 !important;\n            }\n            QTableWidget::item {\n                padding: 8px;\n                border-bottom: 1px solid #ecf0f1;\n                background-color: #ffffff !important;\n                color: #2c3e50 !important;\n                min-height: 25px;\n                border-right: 1px solid #ecf0f1;\n            }\n            QTableWidget::item:selected {\n                background-color: #3498db !important;\n                color: #ffffff !important;\n            }\n            QTableWidget::item:hover {\n                background-color: #f8f9fa !important;\n                color: #2c3e50 !important;\n            }\n            QHeaderView::section {\n                background-color: #f8f9fa !important;\n                border: 1px solid #bdc3c7;\n                padding: 8px;\n                font-weight: bold;\n                color: #2c3e50 !important;\n            }\n        ')
        secao_layout.addWidget(self.tabela)
        layout.addWidget(secao_frame)
    def carregar_relatorio(self):
        try:
            conn = sqlite3.connect('app/database/service_orders.db')
            cursor = conn.cursor()
            mes = self.mes_combo.currentIndex() + 1
            ano = int(self.ano_combo.currentText())
            ultimo_dia = calendar.monthrange(ano, mes)[1]
            data_inicio = f'{ano}-{mes:02d}-01'
            data_fim = f'{ano}-{mes:02d}-{ultimo_dia}'
            cursor.execute('\n                SELECT COUNT(DISTINCT so.id) FROM service_orders so\n                WHERE (date(so.entry_date) BETWEEN ? AND ? \n                       OR date(so.completion_date) BETWEEN ? AND ?)\n                AND so.user_id = ?\n            ', (data_inicio, data_fim, data_inicio, data_fim, self.user_id))
            total = cursor.fetchone()[0]
            self.total_os.setText(f'Total de OS: {total}')
            cursor.execute('\n                SELECT COUNT(*) FROM service_orders\n                WHERE date(completion_date) BETWEEN ? AND ?\n                AND user_id = ?\n            ', (data_inicio, data_fim, self.user_id))
            os_concluidas = cursor.fetchone()[0]
            cursor.execute("\n                SELECT COUNT(*) FROM service_orders\n                WHERE date(completion_date) BETWEEN ? AND ?\n                AND status = 'concluido_sucesso'\n                AND user_id = ?\n            ", (data_inicio, data_fim, self.user_id))
            os_sucesso = cursor.fetchone()[0]
            self.os_sucesso.setText(f'Conclu├¡das com Sucesso: {os_sucesso}')
            cursor.execute("\n                SELECT COUNT(*) FROM service_orders\n                WHERE date(completion_date) BETWEEN ? AND ?\n                AND status = 'concluido_sem_solucao'\n                AND user_id = ?\n            ", (data_inicio, data_fim, self.user_id))
            total_sem_solucao = cursor.fetchone()[0]
            self.os_sem_solucao.setText(f'Conclu├¡das sem Solu├º├úo: {total_sem_solucao}')
            cursor.execute("\n                SELECT COUNT(*) FROM service_orders\n                WHERE date(entry_date) BETWEEN ? AND ?\n                AND status = 'em_reparo'\n                AND user_id = ?\n            ", (data_inicio, data_fim, self.user_id))
            os_em_reparo = cursor.fetchone()[0]
            self.os_em_reparo.setText(f'Em Reparo: {os_em_reparo}')
            total_concluidas = os_sucesso + total_sem_solucao
            taxa = os_sucesso / total_concluidas * 100 if total_concluidas > 0 else 0
            self.taxa_sucesso.setText(f'Taxa de Sucesso: {taxa:.1f}%')
            cursor.execute("\n                SELECT COALESCE(SUM(service_value), 0.0) \n                FROM service_orders\n                WHERE date(completion_date) BETWEEN ? AND ?\n                AND status IN ('concluido_sucesso', 'concluido_sem_solucao')\n                AND user_id = ?\n            ", (data_inicio, data_fim, self.user_id))
            faturamento = cursor.fetchone()[0]
            faturamento_formatado = f'R$ {faturamento:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
            self.faturamento_total.setText(f'­ƒÆ░ Faturamento: {faturamento_formatado}')
            cursor.execute("\n                SELECT so.id, c.name, so.device_type, so.reported_issue, so.status,\n                       so.service_value, so.entry_date, so.completion_date,\n                       CASE \n                           WHEN so.completion_date IS NOT NULL THEN\n                               julianday(so.completion_date) - julianday(so.entry_date)\n                           ELSE\n                               julianday('now') - julianday(so.entry_date)\n                       END as repair_time\n                FROM service_orders so\n                LEFT JOIN clients c ON so.client_id = c.id\n                WHERE (date(so.entry_date) BETWEEN ? AND ? \n                       OR date(so.completion_date) BETWEEN ? AND ?)\n                AND so.user_id = ?\n                ORDER BY \n                    CASE WHEN so.completion_date IS NOT NULL THEN so.completion_date ELSE so.entry_date END DESC\n            ", (data_inicio, data_fim, data_inicio, data_fim, self.user_id))
            resultados_tabela = cursor.fetchall()
            self.tabela.setRowCount(0)
            for row, (os_id, cliente, tipo, problema, status, service_value, entrada, conclusao, tempo) in enumerate(resultados_tabela):
                self.tabela.insertRow(row)
                status_display = {'em_reparo': 'Em Reparo', 'concluido_sucesso': 'Conclu├¡do com Sucesso', 'concluido_sem_solucao': 'Conclu├¡do sem Solu├º├úo'}.get(status, status)
                if service_value and service_value > 0:
                    valor_formatado = f'R$ {service_value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
                else:
                    valor_formatado = '-'
                if tempo and tempo > 0:
                    dias = int(tempo)
                    horas = int((tempo - dias) * 24)
                    if status == 'em_reparo':
                        tempo_display = f'{dias}d {horas}h (em andamento)'
                    else:
                        tempo_display = f'{dias}d {horas}h'
                else:
                    tempo_display = 'Em andamento'
                self.tabela.setItem(row, 0, QTableWidgetItem(str(os_id) if os_id else 'N/A'))
                self.tabela.setItem(row, 1, QTableWidgetItem(cliente if cliente else 'Cliente n├úo encontrado'))
                self.tabela.setItem(row, 2, QTableWidgetItem(tipo if tipo else 'N├úo informado'))
                self.tabela.setItem(row, 3, QTableWidgetItem(problema if problema else 'N├úo informado'))
                self.tabela.setItem(row, 4, QTableWidgetItem(status_display))
                self.tabela.setItem(row, 5, QTableWidgetItem(valor_formatado))
                self.tabela.setItem(row, 6, QTableWidgetItem(entrada if entrada else 'N/A'))
                conclusao_display = conclusao if conclusao else 'Em andamento'
                self.tabela.setItem(row, 7, QTableWidgetItem(conclusao_display))
                self.tabela.setItem(row, 8, QTableWidgetItem(tempo_display))
                continue
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao carregar relat├│rio: {str(e)}')
        if conn:
            conn.close()
