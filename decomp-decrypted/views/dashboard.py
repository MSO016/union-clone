from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QWidget, QScrollArea)
from PyQt5.QtCore import Qt
from app.utils.window_protection import protect_window_from_capture_extended
from app.utils.screen_protection_config import pode_gravar_tela
from app.utils.backup_manager import BackupManager
import sqlite3
from datetime import datetime, timedelta
class DashboardDialog(QDialog):
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.is_admin = parent.is_admin if hasattr(parent, 'is_admin') else False
        self.setWindowTitle('Dashboard')
        self.setModal(True)
        self.setMinimumSize(1000, 700)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setSizeGripEnabled(True)
        if not self.pode_gravar_tela():
            protect_window_from_capture_extended(self, True)
        self.setup_ui()
        self.carregar_dados()
    def pode_gravar_tela(self):
        if self.is_admin:
            return True
        if hasattr(self.parent(), 'user_domain') and self.parent().user_domain:
            return pode_gravar_tela(self.is_admin, self.parent().user_domain)
        return False
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        titulo = QLabel('Dashboard')
        titulo.setStyleSheet('font-size: 18px; font-weight: bold; margin: 10px;')
        layout.addWidget(titulo)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        stats_gerais = QLabel('Estat├¡sticas Gerais')
        stats_gerais.setStyleSheet('font-size: 16px; font-weight: bold;')
        scroll_layout.addWidget(stats_gerais)
        cards_layout = QHBoxLayout()
        self.os_abertas = self.criar_card('OS em Aberto', '0', '#f0ad4e')
        cards_layout.addWidget(self.os_abertas)
        self.os_concluidas = self.criar_card('OS Conclu├¡das (30 dias)', '0', '#5cb85c')
        cards_layout.addWidget(self.os_concluidas)
        self.taxa_sucesso = self.criar_card('Taxa de Sucesso', '0%', '#5bc0de')
        cards_layout.addWidget(self.taxa_sucesso)
        self.tempo_medio = self.criar_card('Tempo M├®dio de Reparo', '0d', '#337ab7')
        cards_layout.addWidget(self.tempo_medio)
        scroll_layout.addLayout(cards_layout)
        prob_label = QLabel('Dispositivos com Maior ├ìndice de Falha')
        prob_label.setStyleSheet('font-size: 16px; font-weight: bold; margin-top: 20px;')
        scroll_layout.addWidget(prob_label)
        self.prob_table = QTableWidget()
        self.prob_table.setColumnCount(5)
        self.prob_table.setHorizontalHeaderLabels(['Tipo', 'Marca', 'Modelo', 'Total OS', 'Taxa de Falha'])
        self.prob_table.horizontalHeader().setStretchLastSection(True)
        scroll_layout.addWidget(self.prob_table)
        rec_label = QLabel('Problemas Mais Recorrentes')
        rec_label.setStyleSheet('font-size: 16px; font-weight: bold; margin-top: 20px;')
        scroll_layout.addWidget(rec_label)
        self.rec_table = QTableWidget()
        self.rec_table.setColumnCount(2)
        self.rec_table.setHorizontalHeaderLabels(['Problema', 'Quantidade'])
        self.rec_table.horizontalHeader().setStretchLastSection(True)
        scroll_layout.addWidget(self.rec_table)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        backup_layout = QHBoxLayout()
        btn_criar_backup = QPushButton('­ƒôª Criar Backup')
        btn_criar_backup.setStyleSheet('\n            QPushButton {\n                background-color: #2980b9;\n                color: white;\n                border: none;\n                padding: 8px 15px;\n                border-radius: 3px;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background-color: #3498db;\n            }\n        ')
        btn_criar_backup.clicked.connect(self.criar_backup)
        backup_layout.addWidget(btn_criar_backup)
        btn_restaurar_backup = QPushButton('­ƒôÑ Restaurar Backup')
        btn_restaurar_backup.setStyleSheet('\n            QPushButton {\n                background-color: #27ae60;\n                color: white;\n                border: none;\n                padding: 8px 15px;\n                border-radius: 3px;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background-color: #2ecc71;\n            }\n        ')
        btn_restaurar_backup.clicked.connect(self.restaurar_backup)
        backup_layout.addWidget(btn_restaurar_backup)
        btn_verificar = QPushButton('­ƒöì Verificar Integridade')
        btn_verificar.setStyleSheet('\n            QPushButton {\n                background-color: #f39c12;\n                color: white;\n                border: none;\n                padding: 8px 15px;\n                border-radius: 3px;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background-color: #e67e22;\n            }\n        ')
        btn_verificar.clicked.connect(self.verificar_integridade)
        backup_layout.addWidget(btn_verificar)
        backup_layout.addStretch()
        layout.addLayout(backup_layout)
        btn_fechar = QPushButton('Fechar')
        btn_fechar.setStyleSheet('\n            QPushButton {\n                background-color: #d9534f;\n                color: white;\n                border: none;\n                padding: 5px 15px;\n                border-radius: 3px;\n            }\n            QPushButton:hover {\n                background-color: #c9302c;\n            }\n        ')
        btn_fechar.clicked.connect(self.reject)
        layout.addWidget(btn_fechar)
    def criar_card(self, titulo, valor, cor):
        card = QLabel()
        card.setStyleSheet(f'\n            QLabel {{\n                background-color: {cor};\n                color: white;\n                padding: 15px;\n                border-radius: 5px;\n                min-width: 200px;\n            }}\n        ')
        card.setText(f'<b>{titulo}</b><br><h2>{valor}</h2>')
        return card
    def carregar_dados(self):
        try:
            conn = sqlite3.connect('app/database/service_orders.db')
            cursor = conn.cursor()
            cursor.execute("\n                SELECT COUNT(*) FROM service_orders\n                WHERE status = 'em_reparo'\n                AND user_id = ?\n            ", (self.user_id,))
            total_abertas = cursor.fetchone()[0]
            self.os_abertas.setText(f'<b>OS em Aberto</b><br><h2>{total_abertas}</h2>')
            from datetime import date
            data_limite = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            cursor.execute("\n                SELECT COUNT(*) FROM service_orders\n                WHERE status IN ('concluido_sucesso', 'concluido_sem_solucao')\n                AND date(completion_date) >= ?\n                AND user_id = ?\n            ", (data_limite, self.user_id))
            total_concluidas = cursor.fetchone()[0]
            self.os_concluidas.setText(f'<b>OS Conclu├¡das (30 dias)</b><br><h2>{total_concluidas}</h2>')
            cursor.execute("\n                SELECT \n                    COUNT(*) as total,\n                    SUM(CASE WHEN status = 'concluido_sucesso' THEN 1 ELSE 0 END) as sucesso\n                FROM service_orders\n                WHERE status IN ('concluido_sucesso', 'concluido_sem_solucao')\n                AND user_id = ?\n            ", (self.user_id,))
            total, sucesso = cursor.fetchone()
            taxa = sucesso / total * 100 if total > 0 else 0
            self.taxa_sucesso.setText(f'<b>Taxa de Sucesso</b><br><h2>{taxa:.1f}%</h2>')
            cursor.execute("\n                SELECT AVG(julianday(completion_date) - julianday(entry_date))\n                FROM service_orders\n                WHERE status IN ('concluido_sucesso', 'concluido_sem_solucao')\n                AND user_id = ?\n            ", (self.user_id,))
            tempo_medio = cursor.fetchone()[0] or 0
            self.tempo_medio.setText(f'<b>Tempo M├®dio de Reparo</b><br><h2>{tempo_medio:.1f}d</h2>')
            cursor.execute("\n                SELECT \n                    device_type,\n                    brand,\n                    model,\n                    COUNT(*) as total,\n                    SUM(CASE WHEN status = 'concluido_sem_solucao' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as taxa_falha\n                FROM service_orders\n                WHERE user_id = ?\n                GROUP BY device_type, brand, model\n                HAVING COUNT(*) >= 3\n                ORDER BY taxa_falha DESC\n                LIMIT 10\n            ", (self.user_id,))
            self.prob_table.setRowCount(0)
            for row, (tipo, marca, modelo, total, taxa) in enumerate(cursor.fetchall()):
                self.prob_table.insertRow(row)
                self.prob_table.setItem(row, 0, QTableWidgetItem(tipo))
                self.prob_table.setItem(row, 1, QTableWidgetItem(marca))
                self.prob_table.setItem(row, 2, QTableWidgetItem(modelo))
                self.prob_table.setItem(row, 3, QTableWidgetItem(str(total)))
                self.prob_table.setItem(row, 4, QTableWidgetItem(f'{taxa:.1f}%'))
            cursor.execute('\n                SELECT reported_issue, COUNT(*) as total\n                FROM service_orders\n                WHERE user_id = ?\n                GROUP BY reported_issue\n                ORDER BY total DESC\n                LIMIT 10\n            ', (self.user_id,))
            self.rec_table.setRowCount(0)
            for row, (problema, total) in enumerate(cursor.fetchall()):
                self.rec_table.insertRow(row)
                self.rec_table.setItem(row, 0, QTableWidgetItem(problema))
                self.rec_table.setItem(row, 1, QTableWidgetItem(str(total)))
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao carregar dados: {str(e)}')
        if conn:
            conn.close()
    def refresh_dados(self):
        self.carregar_dados()
    def criar_backup(self):
        BackupManager.criar_backup(self)
    def restaurar_backup(self):
        if BackupManager.restaurar_backup(self):
            self.carregar_dados()
    def verificar_integridade(self):
        BackupManager.verificar_integridade(self)
