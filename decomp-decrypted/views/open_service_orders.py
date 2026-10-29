from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QWidget, QFileDialog)
from PyQt5.QtCore import Qt
import sqlite3
from .close_service_order import CloseServiceOrderDialog
from .edit_service_order import EditServiceOrderDialog
import os
class OpenServiceOrdersDialog(QDialog):
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.is_admin = parent.is_admin if hasattr(parent, 'is_admin') else False
        self.setWindowTitle('Ordens de Servi├ºo em Aberto')
        self.setModal(True)
        self.setMinimumSize(800, 600)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setSizeGripEnabled(True)
        self.setup_ui()
        self.carregar_os()
        self.showMaximized()
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        titulo = QLabel('Ordens de Servi├ºo em Aberto')
        titulo.setStyleSheet('font-size: 18px; font-weight: bold; margin: 10px;')
        layout.addWidget(titulo)
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(9)
        self.tabela.setHorizontalHeaderLabels(['OS #', 'Cliente', 'Dispositivo', 'Marca/Modelo', 'Problema', 'Valor', 'Data Entrada', 'Status', 'A├º├Áes'])
        self.tabela.setStyleSheet('\n            QTableWidget {\n                gridline-color: #ecf0f1;\n                background-color: white;\n                border: 1px solid #bdc3c7;\n                border-radius: 6px;\n                selection-background-color: #3498db;\n                color: #2c3e50;\n            }\n            QTableWidget::item {\n                padding: 12px 8px;\n                border-bottom: 1px solid #ecf0f1;\n                color: #2c3e50;\n                background-color: white;\n            }\n            QTableWidget::item:selected {\n                background-color: #3498db;\n                color: white;\n            }\n            QTableWidget::item:alternate {\n                background-color: #f8f9fa;\n                color: #2c3e50;\n            }\n            QHeaderView::section {\n                background-color: #34495e;\n                color: white;\n                padding: 12px 8px;\n                border: none;\n                font-weight: bold;\n                font-size: 13px;\n            }\n        ')
        self.tabela.horizontalHeader().setStretchLastSection(True)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.tabela)
        btn_voltar = QPushButton('ÔåÉ Voltar')
        btn_voltar.setStyleSheet('\n            QPushButton {\n                background-color: #6c757d;\n                color: white;\n                border: none;\n                padding: 12px 25px;\n                border-radius: 5px;\n                font-weight: bold;\n                font-size: 14px;\n            }\n            QPushButton:hover {\n                background-color: #5a6268;\n            }\n        ')
        btn_voltar.clicked.connect(self.reject)
        layout.addWidget(btn_voltar)
    def carregar_os(self):
        try:
            conn = sqlite3.connect('app/database/service_orders.db')
            cursor = conn.cursor()
            cursor.execute("\n                SELECT so.id, c.name, so.device_type,\n                       so.brand, so.model, so.reported_issue,\n                       so.service_value, so.entry_date, so.status\n                FROM service_orders so\n                JOIN clients c ON so.client_id = c.id\n                WHERE so.status = 'em_reparo'\n                AND so.user_id = ?\n                ORDER BY so.entry_date DESC\n            ", (self.user_id,))
            self.tabela.setRowCount(0)
            for row, (os_id, cliente, tipo, marca, modelo, problema, service_value, entrada, status) in enumerate(cursor.fetchall()):
                self.tabela.insertRow(row)
                self.tabela.setItem(row, 0, QTableWidgetItem(str(os_id)))
                self.tabela.setItem(row, 1, QTableWidgetItem(cliente))
                self.tabela.setItem(row, 2, QTableWidgetItem(tipo))
                self.tabela.setItem(row, 3, QTableWidgetItem(f'{marca} / {modelo}'))
                self.tabela.setItem(row, 4, QTableWidgetItem(problema))
                if service_value and service_value > 0:
                    valor_formatado = f'R$ {service_value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
                else:
                    valor_formatado = '-'
                self.tabela.setItem(row, 5, QTableWidgetItem(valor_formatado))
                self.tabela.setItem(row, 6, QTableWidgetItem(entrada))
                self.tabela.setItem(row, 7, QTableWidgetItem('Em Reparo'))
                acoes_widget = QWidget()
                acoes_layout = QHBoxLayout()
                acoes_layout.setContentsMargins(5, 5, 5, 5)
                acoes_layout.setSpacing(5)
                editar_btn = QPushButton('Editar')
                editar_btn.setStyleSheet('\n                    QPushButton {\n                        background-color: #f39c12;\n                        color: white;\n                        border: none;\n                        padding: 20px 15px;\n                        border-radius: 5px;\n                        font-weight: bold;\n                        font-size: 12px;\n                        min-width: 110px;\n                    }\n                    QPushButton:hover {\n                        background-color: #e67e22;\n                    }\n                    QPushButton:pressed {\n                        background-color: #d35400;\n                    }\n                ')
                editar_btn.clicked.connect((lambda checked, os_id=os_id: self.editar_os(os_id)))
                pdf_a4_btn = QPushButton('­ƒôä A4')
                pdf_a4_btn.setStyleSheet('\n                    QPushButton {\n                        background-color: #5bc0de;\n                        color: white;\n                        border: none;\n                        padding: 20px 15px;\n                        border-radius: 5px;\n                        font-weight: bold;\n                        font-size: 12px;\n                        min-width: 110px;\n                    }\n                    QPushButton:hover {\n                        background-color: #46b8da;\n                    }\n                ')
                pdf_a4_btn.clicked.connect((lambda checked, os_id=os_id: self.gerar_pdf_a4(os_id)))
                pdf_a4_btn.setToolTip('Gerar PDF A4 padr├úo')
                pdf_thermal_btn = QPushButton('­ƒû¿´©Å 80mm')
                pdf_thermal_btn.setStyleSheet('\n                    QPushButton {\n                        background-color: #17a2b8;\n                        color: white;\n                        border: none;\n                        padding: 20px 15px;\n                        border-radius: 5px;\n                        font-weight: bold;\n                        font-size: 12px;\n                        min-width: 110px;\n                    }\n                    QPushButton:hover {\n                        background-color: #138496;\n                    }\n                ')
                pdf_thermal_btn.clicked.connect((lambda checked, os_id=os_id: self.gerar_pdf_termico(os_id)))
                pdf_thermal_btn.setToolTip('Gerar PDF para impressora t├®rmica 80mm')
                encerrar_btn = QPushButton('Encerrar')
                encerrar_btn.setStyleSheet('\n                    QPushButton {\n                        background-color: #27ae60;\n                        color: white;\n                        border: none;\n                        padding: 20px 15px;\n                        border-radius: 5px;\n                        font-weight: bold;\n                        font-size: 12px;\n                        min-width: 110px;\n                    }\n                    QPushButton:hover {\n                        background-color: #229954;\n                    }\n                ')
                encerrar_btn.clicked.connect((lambda checked, os_id=os_id: self.encerrar_os(os_id)))
                excluir_btn = QPushButton('Excluir')
                excluir_btn.setStyleSheet('\n                    QPushButton {\n                        background-color: #e74c3c;\n                        color: white;\n                        border: none;\n                        padding: 20px 15px;\n                        border-radius: 5px;\n                        font-weight: bold;\n                        font-size: 12px;\n                        min-width: 110px;\n                    }\n                    QPushButton:hover {\n                        background-color: #c0392b;\n                    }\n                ')
                excluir_btn.clicked.connect((lambda checked, os_id=os_id: self.excluir_os(os_id)))
                acoes_layout.addWidget(editar_btn)
                acoes_layout.addWidget(pdf_a4_btn)
                acoes_layout.addWidget(pdf_thermal_btn)
                acoes_layout.addWidget(encerrar_btn)
                acoes_layout.addWidget(excluir_btn)
                acoes_widget.setLayout(acoes_layout)
                self.tabela.setCellWidget(row, 8, acoes_widget)
                continue
            for row in range(self.tabela.rowCount()):
                self.tabela.setRowHeight(row, 65)
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao carregar ordens de servi├ºo: {str(e)}')
        if conn:
            conn.close()
    def editar_os(self, os_id):
        dialog = EditServiceOrderDialog(os_id, self.user_id, self)
        if dialog.exec_() == QDialog.Accepted:
            self.carregar_os()
            self.accept()
    def encerrar_os(self, os_id):
        dialog = CloseServiceOrderDialog(os_id, self.user_id, self)
        if dialog.exec_() == QDialog.Accepted:
            self.carregar_os()
            self.accept()
    def excluir_os(self, os_id):
        conn = None
        try:
            resposta = QMessageBox.question(self, 'Confirma├º├úo', 'Tem certeza que deseja excluir esta ordem de servi├ºo?', QMessageBox.Yes | QMessageBox.No)
            if resposta == QMessageBox.Yes:
                conn = sqlite3.connect('app/database/service_orders.db')
                cursor = conn.cursor()
                cursor.execute('\n                    SELECT photo_path FROM service_order_photos\n                    WHERE service_order_id = ?\n                ', (os_id,))
                for (photo_path,) in cursor.fetchall():
                    if os.path.exists(photo_path):
                        os.remove(photo_path)
                cursor.execute('\n                    DELETE FROM service_order_photos\n                    WHERE service_order_id = ?\n                ', (os_id,))
                cursor.execute('\n                    DELETE FROM service_orders\n                    WHERE id = ? AND user_id = ?\n                ', (os_id, self.user_id))
                conn.commit()
                QMessageBox.information(self, 'Sucesso', 'Ordem de servi├ºo exclu├¡da com sucesso!')
                self.carregar_os()
                self.accept()
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao excluir OS: {str(e)}')
        if conn:
            conn.close()
    def gerar_pdf_a4(self, os_id):
        try:
            from app.utils.service_order_pdf import ServiceOrderPDF
            from datetime import datetime
            import subprocess
            import sys
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            default_name = f'OS_{os_id}_{timestamp}.pdf'
            pdf_path, _ = QFileDialog.getSaveFileName(self, 'Salvar PDF A4', default_name, 'Arquivos PDF (*.pdf)')
            if not pdf_path:
                return
            if not pdf_path.lower().endswith('.pdf'):
                pdf_path += '.pdf'
            pdf_generator = ServiceOrderPDF(os_id, self.user_id)
            pdf_generator.generate_pdf(pdf_path, include_photo=False)
            reply = QMessageBox.question(self, 'PDF Gerado! ­ƒôä', f'PDF A4 salvo em:\n{pdf_path}\n\nDeseja abrir?', QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    if sys.platform == 'win32':
                        os.startfile(pdf_path)
                        return
                    if sys.platform == 'darwin':
                        subprocess.call(['open', pdf_path])
                        return
                    subprocess.call(['xdg-open', pdf_path])
                except Exception as e:
                    print(f'Erro ao abrir PDF: {e}')
                return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao gerar PDF A4:\n{str(e)}')
    def gerar_pdf_termico(self, os_id):
        try:
            from app.utils.service_order_thermal_pdf import ServiceOrderThermalPDF
            from datetime import datetime
            import subprocess
            import sys
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            default_name = f'OS_{os_id}_thermal_{timestamp}.pdf'
            pdf_path, _ = QFileDialog.getSaveFileName(self, 'Salvar PDF T├®rmico 80mm', default_name, 'Arquivos PDF (*.pdf)')
            if not pdf_path:
                return
            if not pdf_path.lower().endswith('.pdf'):
                pdf_path += '.pdf'
            thermal_generator = ServiceOrderThermalPDF(os_id, self.user_id)
            if thermal_generator.generate_pdf(pdf_path):
                reply = QMessageBox.question(self, 'PDF T├®rmico Gerado! ­ƒû¿´©Å', f'PDF t├®rmico 80mm salvo em:\n{pdf_path}\n\nVoc├¬ pode:\nÔÇó Imprimir em impressora t├®rmica\nÔÇó Enviar por WhatsApp/Email\nÔÇó Imprimir no celular\n\nDeseja abrir?', QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    pass
            try:
                if sys.platform == 'win32':
                    os.startfile(pdf_path)
                    return
                if sys.platform == 'darwin':
                    subprocess.call(['open', pdf_path])
                    return
                subprocess.call(['xdg-open', pdf_path])
            except Exception as e:
                print(f'Erro ao abrir PDF: {e}')
            else:
                return
        except ImportError:
            QMessageBox.critical(self, 'Erro', 'M├│dulo de PDF t├®rmico n├úo encontrado.\n\nArquivo: app/utils/service_order_thermal_pdf.py')
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao gerar PDF t├®rmico:\n{str(e)}')
