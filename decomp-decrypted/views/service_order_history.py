from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QLineEdit, QComboBox, QWidget, QFileDialog)
from PyQt5.QtCore import Qt
import sqlite3
from .edit_service_order import EditServiceOrderDialog
class ServiceOrderHistoryDialog(QDialog):
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.is_admin = parent.is_admin if hasattr(parent, 'is_admin') else False
        self.setWindowTitle('Hist├│rico de Ordens de Servi├ºo')
        self.setModal(True)
        self.setMinimumSize(1000, 600)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setSizeGripEnabled(True)
        self.setup_ui()
        self.carregar_historico()
        self.showMaximized()
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        titulo = QLabel('Hist├│rico de Ordens de Servi├ºo')
        titulo.setStyleSheet('font-size: 18px; font-weight: bold; margin: 10px;')
        layout.addWidget(titulo)
        filtros_layout = QHBoxLayout()
        status_label = QLabel('Status:')
        self.status_combo = QComboBox()
        self.status_combo.addItems(['Todos', 'Em Reparo', 'Conclu├¡do com Sucesso', 'Conclu├¡do sem Solu├º├úo'])
        self.status_combo.currentTextChanged.connect(self.filtrar_historico)
        filtros_layout.addWidget(status_label)
        filtros_layout.addWidget(self.status_combo)
        self.busca_input = QLineEdit()
        self.busca_input.setPlaceholderText('Buscar por cliente, dispositivo ou problema...')
        self.busca_input.textChanged.connect(self.filtrar_historico)
        filtros_layout.addWidget(self.busca_input)
        layout.addLayout(filtros_layout)
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(10)
        self.tabela.setHorizontalHeaderLabels(['OS #', 'Cliente', 'Dispositivo', 'Marca/Modelo', 'Problema', 'Status', 'Valor', 'Data Entrada', 'Data Conclus├úo', 'A├º├Áes'])
        self.tabela.setStyleSheet('\n            QTableWidget {\n                gridline-color: #ecf0f1;\n                background-color: white;\n                border: 1px solid #bdc3c7;\n                border-radius: 6px;\n                selection-background-color: #3498db;\n                color: #2c3e50;\n            }\n            QTableWidget::item {\n                padding: 12px 8px;\n                border-bottom: 1px solid #ecf0f1;\n                color: #2c3e50;\n                background-color: white;\n            }\n            QTableWidget::item:selected {\n                background-color: #3498db;\n                color: white;\n            }\n            QTableWidget::item:alternate {\n                background-color: #f8f9fa;\n                color: #2c3e50;\n            }\n            QHeaderView::section {\n                background-color: #34495e;\n                color: white;\n                padding: 12px 8px;\n                border: none;\n                font-weight: bold;\n                font-size: 13px;\n            }\n        ')
        self.tabela.horizontalHeader().setStretchLastSection(True)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.doubleClicked.connect(self.ver_detalhes)
        self.tabela.itemSelectionChanged.connect(self.atualizar_cores_botoes)
        layout.addWidget(self.tabela)
        btn_voltar = QPushButton('ÔåÉ Voltar')
        btn_voltar.setStyleSheet('\n            QPushButton {\n                background-color: #6c757d;\n                color: white;\n                border: none;\n                padding: 12px 25px;\n                border-radius: 5px;\n                font-weight: bold;\n                font-size: 14px;\n            }\n            QPushButton:hover {\n                background-color: #5a6268;\n            }\n        ')
        btn_voltar.clicked.connect(self.reject)
        layout.addWidget(btn_voltar)
    def carregar_historico(self):
        try:
            conn = sqlite3.connect('app/database/service_orders.db')
            cursor = conn.cursor()
            cursor.execute('\n                SELECT so.id, c.name, so.device_type,\n                       so.brand, so.model, so.reported_issue,\n                       so.status, so.service_value, so.entry_date, so.completion_date\n                FROM service_orders so\n                JOIN clients c ON so.client_id = c.id\n                WHERE so.user_id = ?\n                ORDER BY so.entry_date DESC\n            ', (self.user_id,))
            self.todas_os = cursor.fetchall()
            self.atualizar_tabela(self.todas_os)
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao carregar hist├│rico: {str(e)}')
        if conn:
            conn.close()
    def atualizar_tabela(self, dados):
        self.tabela.setRowCount(0)
        for row, (os_id, cliente, tipo, marca, modelo, problema, status, service_value, entrada, conclusao) in enumerate(dados):
            self.tabela.insertRow(row)
            status_display = {'em_reparo': 'Em Reparo', 'concluido_sucesso': 'Conclu├¡do com Sucesso', 'concluido_sem_solucao': 'Conclu├¡do sem Solu├º├úo'}.get(status, status)
            if service_value and service_value > 0:
                valor_formatado = f'R$ {service_value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
            else:
                valor_formatado = '-'
            self.tabela.setItem(row, 0, QTableWidgetItem(str(os_id)))
            self.tabela.setItem(row, 1, QTableWidgetItem(cliente))
            self.tabela.setItem(row, 2, QTableWidgetItem(tipo))
            self.tabela.setItem(row, 3, QTableWidgetItem(f'{marca} / {modelo}'))
            self.tabela.setItem(row, 4, QTableWidgetItem(problema))
            self.tabela.setItem(row, 5, QTableWidgetItem(status_display))
            self.tabela.setItem(row, 6, QTableWidgetItem(valor_formatado))
            self.tabela.setItem(row, 7, QTableWidgetItem(entrada))
            self.tabela.setItem(row, 8, QTableWidgetItem(conclusao or ''))
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(5, 5, 5, 5)
            btn_layout.setSpacing(5)
            visualizar_btn = QPushButton('Visualizar')
            visualizar_btn.setStyleSheet('\n                QPushButton {\n                    background-color: #27ae60;\n                    color: white;\n                    border: none;\n                    padding: 20px 15px;\n                    border-radius: 5px;\n                    font-weight: bold;\n                    font-size: 12px;\n                    min-width: 110px;\n                }\n                QPushButton:hover {\n                    background-color: #229954;\n                }\n            ')
            visualizar_btn.clicked.connect((lambda checked, os_id=os_id: self.visualizar_os(os_id)))
            btn_layout.addWidget(visualizar_btn)
            if status == 'em_reparo':
                editar_btn = QPushButton('Editar')
                editar_btn.setStyleSheet('\n                    QPushButton {\n                        background-color: #3498db;\n                        color: white;\n                        border: none;\n                        padding: 20px 15px;\n                        border-radius: 5px;\n                        font-weight: bold;\n                        font-size: 12px;\n                        min-width: 110px;\n                    }\n                    QPushButton:hover {\n                        background-color: #2980b9;\n                    }\n                ')
                editar_btn.clicked.connect((lambda checked, os_id=os_id: self.editar_os(os_id)))
                btn_layout.addWidget(editar_btn)
            pdf_a4_btn = QPushButton('A4')
            pdf_a4_btn.setStyleSheet('\n                QPushButton {\n                    background-color: #5bc0de;\n                    color: white;\n                    border: none;\n                    padding: 20px 15px;\n                    border-radius: 5px;\n                    font-weight: bold;\n                    font-size: 12px;\n                    min-width: 110px;\n                }\n                QPushButton:hover {\n                    background-color: #46b8da;\n                }\n            ')
            pdf_a4_btn.clicked.connect((lambda checked, os_id=os_id: self.gerar_pdf_a4(os_id)))
            pdf_a4_btn.setToolTip('Gerar PDF A4 padr├úo')
            btn_layout.addWidget(pdf_a4_btn)
            pdf_thermal_btn = QPushButton('80mm')
            pdf_thermal_btn.setStyleSheet('\n                QPushButton {\n                    background-color: #17a2b8;\n                    color: white;\n                    border: none;\n                    padding: 20px 15px;\n                    border-radius: 5px;\n                    font-weight: bold;\n                    font-size: 12px;\n                    min-width: 110px;\n                }\n                QPushButton:hover {\n                    background-color: #138496;\n                }\n            ')
            pdf_thermal_btn.clicked.connect((lambda checked, os_id=os_id: self.gerar_pdf_termico(os_id)))
            pdf_thermal_btn.setToolTip('Gerar PDF para impressora t├®rmica 80mm')
            btn_layout.addWidget(pdf_thermal_btn)
            self.tabela.setCellWidget(row, 9, btn_widget)
            continue
        for row in range(self.tabela.rowCount()):
            self.tabela.setRowHeight(row, 65)
        self.atualizar_cores_botoes()
    def filtrar_historico(self):
        status = self.status_combo.currentText()
        texto = self.busca_input.text().lower()
        filtrados = []
        for os in self.todas_os:
            if status != 'Todos':
                status_map = {'Em Reparo': 'em_reparo', 'Conclu├¡do com Sucesso': 'concluido_sucesso', 'Conclu├¡do sem Solu├º├úo': 'concluido_sem_solucao'}
                if os[6] == status_map.get(status) and (not texto or texto in str(os[1]).lower() or texto in str(os[2]).lower() or texto in str(os[3]).lower() or texto in str(os[4]).lower() or texto in str(os[5]).lower()):
                    filtrados.append(os)
        self.atualizar_tabela(filtrados)
    def ver_detalhes(self):
        selecionado = self.tabela.selectedItems()
        if not selecionado:
            QMessageBox.warning(self, 'Aviso', 'Selecione uma O.S. para ver os detalhes!')
            return
        os_id = int(self.tabela.item(selecionado[0].row(), 0).text())
        from app.views.service_order_details import ServiceOrderDetailsDialog
        dialog = ServiceOrderDetailsDialog(os_id, self)
        dialog.exec_()
    def atualizar_cores_botoes(self):
        try:
            linhas_selecionadas = set()
            for item in self.tabela.selectedItems():
                linhas_selecionadas.add(item.row())
            for row in range(self.tabela.rowCount()):
                widget = self.tabela.cellWidget(row, 8)
                if widget:
                    visualizar_btn = None
                    editar_btn = None
                    for child in widget.findChildren(QPushButton):
                        if 'Visualizar' in child.text():
                            visualizar_btn = child
                        elif 'Editar' in child.text():
                            editar_btn = child
                    if visualizar_btn:
                        if row in linhas_selecionadas:
                            visualizar_btn.setStyleSheet('\n                                QPushButton {\n                                    background-color: #1e8449;\n                                    color: white;\n                                    border: none;\n                                    padding: 20px 15px;\n                                    border-radius: 5px;\n                                    font-weight: bold;\n                                    font-size: 12px;\n                                    min-width: 110px;\n                                }\n                                QPushButton:hover {\n                                    background-color: #196f3d;\n                                }\n                                QPushButton:pressed {\n                                    background-color: #145a32;\n                                }\n                            ')
                        else:
                            visualizar_btn.setStyleSheet('\n                                QPushButton {\n                                    background-color: #27ae60;\n                                    color: white;\n                                    border: none;\n                                    padding: 20px 15px;\n                                    border-radius: 5px;\n                                    font-weight: bold;\n                                    font-size: 12px;\n                                    min-width: 110px;\n                                }\n                                QPushButton:hover {\n                                    background-color: #229954;\n                                }\n                                QPushButton:pressed {\n                                    background-color: #1e8449;\n                                }\n                            ')
                    if not editar_btn:
                        continue
                    if row in linhas_selecionadas:
                        editar_btn.setStyleSheet('\n                                QPushButton {\n                                    background-color: #f39c12;\n                                    color: white;\n                                    border: none;\n                                    padding: 20px 15px;\n                                    border-radius: 5px;\n                                    font-weight: bold;\n                                    font-size: 12px;\n                                    min-width: 110px;\n                                }\n                                QPushButton:hover {\n                                    background-color: #e67e22;\n                                }\n                                QPushButton:pressed {\n                                    background-color: #d35400;\n                                }\n                            ')
                    else:
                        editar_btn.setStyleSheet('\n                                QPushButton {\n                                    background-color: #3498db;\n                                    color: white;\n                                    border: none;\n                                    padding: 20px 15px;\n                                    border-radius: 5px;\n                                    font-weight: bold;\n                                    font-size: 12px;\n                                    min-width: 110px;\n                                }\n                                QPushButton:hover {\n                                    background-color: #2980b9;\n                                }\n                                QPushButton:pressed {\n                                    background-color: #21618c;\n                                }\n                            ')
            return
        except Exception as e:
            print(f'Erro ao atualizar cores dos bot├Áes: {str(e)}')
    def visualizar_os(self, os_id):
        from app.views.service_order_details import ServiceOrderDetailsDialog
        dialog = ServiceOrderDetailsDialog(os_id, self)
        dialog.exec_()
    def editar_os(self, os_id):
        dialog = EditServiceOrderDialog(os_id, self.user_id, self)
        if dialog.exec_() == QDialog.Accepted:
            self.carregar_historico()
            self.filtrar_historico()
    def gerar_pdf_a4(self, os_id):
        try:
            from app.utils.service_order_pdf import ServiceOrderPDF
            from app.utils.path_manager import PathManager
            from datetime import datetime
            import subprocess
            import sys
            import os
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            pasta_pdfs = PathManager.get_user_documents_dir('UNION_OS/PDFs')
            default_name = os.path.join(pasta_pdfs, f'OS_{os_id}_{timestamp}.pdf')
            pdf_path, _ = QFileDialog.getSaveFileName(self, 'Salvar PDF A4', default_name, 'Arquivos PDF (*.pdf)')
            if not pdf_path:
                return
            if not pdf_path.lower().endswith('.pdf'):
                pdf_path += '.pdf'
            include_photo = False
            conn = sqlite3.connect('app/database/service_orders.db')
            cursor = conn.cursor()
            cursor.execute('SELECT completion_photo, status FROM service_orders WHERE id = ?', (os_id,))
            result = cursor.fetchone()
            conn.close()
            if result and result[0] and os.path.exists(result[0]) and result[1] in ('concluido_sucesso', 'concluido_sem_solucao'):
                reply = QMessageBox.question(self, 'Incluir Foto?', 'Esta OS possui uma foto de encerramento.\n\nDeseja incluir a foto no PDF?\n\nÔÇó SIM: PDF mais completo (pode gerar 2 p├íginas)\nÔÇó N├âO: PDF mais compacto (apenas texto)', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                include_photo = reply == QMessageBox.Yes
            pdf_generator = ServiceOrderPDF(os_id, self.user_id)
            pdf_generator.generate_pdf(pdf_path, include_photo)
            reply = QMessageBox.question(self, 'PDF Gerado!', f'PDF A4 salvo em:\n{pdf_path}\n\nDeseja abrir?', QMessageBox.Yes | QMessageBox.No)
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
            from app.utils.path_manager import PathManager
            from datetime import datetime
            import subprocess
            import sys
            import os
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            pasta_pdfs = PathManager.get_user_documents_dir('UNION_OS/PDFs')
            default_name = os.path.join(pasta_pdfs, f'OS_{os_id}_thermal_{timestamp}.pdf')
            pdf_path, _ = QFileDialog.getSaveFileName(self, 'Salvar PDF T├®rmico 80mm', default_name, 'Arquivos PDF (*.pdf)')
            if not pdf_path:
                return
            if not pdf_path.lower().endswith('.pdf'):
                pdf_path += '.pdf'
            thermal_generator = ServiceOrderThermalPDF(os_id, self.user_id)
            if thermal_generator.generate_pdf(pdf_path):
                reply = QMessageBox.question(self, 'PDF T├®rmico Gerado!', f'PDF t├®rmico 80mm salvo em:\n{pdf_path}\n\nVoc├¬ pode:\nÔÇó Imprimir em impressora t├®rmica\nÔÇó Enviar por WhatsApp/Email\nÔÇó Imprimir no celular\n\nDeseja abrir?', QMessageBox.Yes | QMessageBox.No)
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
