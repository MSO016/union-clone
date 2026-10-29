from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QMessageBox, QScrollArea, QWidget, QFrame, QFileDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from app.utils.service_order_pdf import ServiceOrderPDF
import sqlite3
import os
import sys
from datetime import datetime
class ServiceOrderDetailsDialog(QDialog):
    def __init__(self, os_id, parent=None):
        super().__init__(parent)
        self.os_id = os_id
        self.user_id = parent.user_id if hasattr(parent, 'user_id') else None
        self.is_admin = parent.is_admin if hasattr(parent, 'is_admin') else False
        self.setWindowTitle('Detalhes da Ordem de Servi├ºo')
        self.setModal(True)
        self.setMinimumSize(800, 600)
        self.setup_ui()
        self.carregar_detalhes()
    def setup_ui(self):
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { border: none; }')
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)
        titulo = QLabel(f'Ordem de Servi├ºo #{self.os_id}')
        titulo.setStyleSheet('font-size: 18px; font-weight: bold; margin: 10px;')
        content_layout.addWidget(titulo)
        cliente_frame = self.criar_secao('Informa├º├Áes do Cliente')
        self.cliente_info = QLabel()
        cliente_frame.layout().addWidget(self.cliente_info)
        content_layout.addWidget(cliente_frame)
        dispositivo_frame = self.criar_secao('Informa├º├Áes do Dispositivo')
        self.dispositivo_info = QLabel()
        dispositivo_frame.layout().addWidget(self.dispositivo_info)
        content_layout.addWidget(dispositivo_frame)
        problema_frame = self.criar_secao('Problema e Diagn├│stico')
        self.problema_info = QLabel()
        problema_frame.layout().addWidget(self.problema_info)
        content_layout.addWidget(problema_frame)
        financeiro_frame = self.criar_secao('Informa├º├Áes Financeiras')
        self.financeiro_info = QLabel()
        self.financeiro_info.setTextFormat(Qt.RichText)
        self.financeiro_info.setWordWrap(True)
        financeiro_frame.layout().addWidget(self.financeiro_info)
        content_layout.addWidget(financeiro_frame)
        solucao_frame = self.criar_secao('Solu├º├úo e Passos Realizados')
        self.solucao_info = QLabel()
        solucao_frame.layout().addWidget(self.solucao_info)
        content_layout.addWidget(solucao_frame)
        fotos_frame = self.criar_secao('Fotos')
        self.fotos_layout = QHBoxLayout()
        fotos_frame.layout().addLayout(self.fotos_layout)
        content_layout.addWidget(fotos_frame)
        buttons_layout = QHBoxLayout()
        self.reabrir_btn = QPushButton('Reabrir OS (Garantia)')
        self.reabrir_btn.setStyleSheet('\n            QPushButton {\n                background-color: #f0ad4e;\n                color: white;\n                border: none;\n                padding: 5px 15px;\n                border-radius: 3px;\n            }\n            QPushButton:hover {\n                background-color: #ec971f;\n            }\n        ')
        self.reabrir_btn.clicked.connect(self.reabrir_os)
        self.reabrir_btn.setVisible(False)
        buttons_layout.addWidget(self.reabrir_btn)
        imprimir_btn = QPushButton('­ƒôä PDF A4')
        imprimir_btn.setStyleSheet('\n            QPushButton {\n                background-color: #5bc0de;\n                color: white;\n                border: none;\n                padding: 5px 15px;\n                border-radius: 3px;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background-color: #46b8da;\n            }\n        ')
        imprimir_btn.clicked.connect(self.imprimir_os)
        buttons_layout.addWidget(imprimir_btn)
        imprimir_thermal_btn = QPushButton('­ƒû¿´©Å PDF 80mm')
        imprimir_thermal_btn.setStyleSheet('\n            QPushButton {\n                background-color: #17a2b8;\n                color: white;\n                border: none;\n                padding: 5px 15px;\n                border-radius: 3px;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background-color: #138496;\n            }\n        ')
        imprimir_thermal_btn.clicked.connect(self.imprimir_os_termico)
        buttons_layout.addWidget(imprimir_thermal_btn)
        fechar_btn = QPushButton('Fechar')
        fechar_btn.setStyleSheet('\n            QPushButton {\n                background-color: #d9534f;\n                color: white;\n                border: none;\n                padding: 5px 15px;\n                border-radius: 3px;\n            }\n            QPushButton:hover {\n                background-color: #c9302c;\n            }\n        ')
        fechar_btn.clicked.connect(self.close)
        buttons_layout.addWidget(fechar_btn)
        content_layout.addLayout(buttons_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)
    def criar_secao(self, titulo):
        frame = QFrame()
        frame.setStyleSheet('\n            QFrame {\n                background-color: white;\n                border: 1px solid #ddd;\n                border-radius: 5px;\n                padding: 10px;\n            }\n        ')
        layout = QVBoxLayout(frame)
        titulo_label = QLabel(titulo)
        titulo_label.setStyleSheet('\n            font-size: 14px;\n            font-weight: bold;\n            color: #2c3e50;\n            margin-bottom: 5px;\n        ')
        layout.addWidget(titulo_label)
        return frame
    def carregar_detalhes(self):
        try:
            conn = sqlite3.connect('app/database/service_orders.db')
            cursor = conn.cursor()
            cursor.execute('\n                SELECT c.name, c.phone, c.email, c.address,\n                       so.device_type, so.brand, so.model, so.serial_number,\n                       so.reported_issue, so.initial_diagnosis,\n                       so.status, so.solution, so.steps_taken,\n                       so.failure_reason, so.entry_date, so.completion_date,\n                       so.technician_notes, so.service_value, so.completion_photo\n                FROM service_orders so\n                JOIN clients c ON so.client_id = c.id\n                WHERE so.id = ?\n            ', (self.os_id,))
            dados = cursor.fetchone()
            if dados:
                self.cliente_info.setText(f'\n                    <b>Nome:</b> {dados[0]}<br>\n                    <b>Telefone:</b> {dados[1] or '-'}<br>\n                    <b>Email:</b> {dados[2] or '-'}<br>\n                    <b>Endere├ºo:</b> {dados[3] or '-'}\n                ')
                self.dispositivo_info.setText(f'\n                    <b>Tipo:</b> {dados[4]}<br>\n                    <b>Marca:</b> {dados[5]}<br>\n                    <b>Modelo:</b> {dados[6]}<br>\n                    <b>N├║mero de S├®rie:</b> {dados[7] or '-'}\n                ')
                status_display = {'em_reparo': 'Em Reparo', 'concluido_sucesso': 'Conclu├¡do com Sucesso', 'concluido_sem_solucao': 'Conclu├¡do sem Solu├º├úo'}.get(dados[10], dados[10])
                self.problema_info.setText(f'\n                    <b>Status:</b> {status_display}<br>\n                    <b>Problema Relatado:</b><br>\n                    {dados[8]}<br><br>\n                    <b>Diagn├│stico Inicial:</b><br>\n                    {dados[9] or '-'}\n                ')
            try:
                if dados[17] and float(dados[17]) > 0:
                    valor_formatado = f'R$ {float(dados[17]):.2f}'.replace('.', ',')
                    financeiro_text = f'\n                            <div style="background-color: #e8f5e8; padding: 10px; border-radius: 5px; border: 1px solid #4CAF50;">\n                                <b style="color: #2E7D32; font-size: 16px;">­ƒÆ░ Valor do Servi├ºo:</b> \n                                <span style="color: #1B5E20; font-size: 18px; font-weight: bold;">{valor_formatado}</span>\n                            </div>\n                        '
            except (ValueError, TypeError):
                financeiro_text = '\n                        <div style="background-color: #fff3cd; padding: 10px; border-radius: 5px; border: 1px solid #ffc107;">\n                            <b style="color: #856404;">­ƒÆ░ Valor do Servi├ºo:</b> \n                            <span style="color: #856404;">N├úo informado</span>\n                        </div>\n                    '
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao carregar detalhes: {str(e)}')
        if conn:
            conn.close()
    def reabrir_os(self):
        conn = None
        try:
            resposta = QMessageBox.question(self, 'Reabrir OS', 'Deseja reabrir esta OS para garantia?\nIsso criar├í uma nova OS vinculada a esta.', QMessageBox.Yes | QMessageBox.No)
            if resposta == QMessageBox.Yes:
                conn = sqlite3.connect('app/database/service_orders.db')
                cursor = conn.cursor()
                cursor.execute('\n                    SELECT client_id, device_type, brand, model,\n                           reported_issue, initial_diagnosis, user_id\n                    FROM service_orders\n                    WHERE id = ?\n                ', (self.os_id,))
                dados = cursor.fetchone()
                if dados:
                    cursor.execute("\n                        INSERT INTO service_orders (\n                            client_id, device_type, brand, model,\n                            reported_issue, initial_diagnosis, status,\n                            entry_date, user_id\n                        ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'), ?)\n                    ", (dados[0], dados[1], dados[2], dados[3], dados[4], f'GARANTIA - OS ORIGINAL #{self.os_id}\n{dados[5] or ''}', 'em_reparo', dados[6]))
                    nova_os_id = cursor.lastrowid
                    conn.commit()
                    QMessageBox.information(self, 'Sucesso', f'OS reaberta com sucesso!\nNova OS criada com ID: {nova_os_id}')
                    self.accept()
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao reabrir OS: {str(e)}')
        if conn:
            conn.close()
    def imprimir_os(self):
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nome_sugerido = f'OS_{self.os_id}_{timestamp}.pdf'
            pdf_path, _ = QFileDialog.getSaveFileName(self, 'Salvar PDF da Ordem de Servi├ºo', nome_sugerido, 'Arquivos PDF (*.pdf);;Todos os arquivos (*)')
            if not pdf_path:
                return
            if not pdf_path.lower().endswith('.pdf'):
                pdf_path += '.pdf'
            if os.path.exists(pdf_path):
                pass
            try:
                with open(pdf_path, 'r+b') as test_file:
                    pass
            except (PermissionError, IOError):
                base_name = pdf_path[:-4]
                counter = 1
                while os.path.exists(f'{base_name}_{counter}.pdf'):
                    try:
                        with open(f'{base_name}_{counter}.pdf', 'r+b') as test_file:
                            pass
                    except (PermissionError, IOError):
                        counter += 1
                        if counter > 10:
                            raise Exception('Muitos arquivos em uso. Tente fechar alguns PDFs.')
                    if not None:
                        pass
                    try:
                        pass
                    except (PermissionError, IOError):
                        counter += 1
                        if counter > 10:
                            raise Exception('Muitos arquivos em uso. Tente fechar alguns PDFs.')
                    break
                pdf_path = f'{base_name}_{counter}.pdf'
                QMessageBox.information(self, 'Arquivo Renomeado', f'O arquivo original estava em uso.\nSalvando como: {os.path.basename(pdf_path)}')
            else:
                include_photo = False
                conn = sqlite3.connect('app/database/service_orders.db')
                cursor = conn.cursor()
                cursor.execute('SELECT completion_photo FROM service_orders WHERE id = ?', (self.os_id,))
                result = cursor.fetchone()
                conn.close()
                if result and result[0] and os.path.exists(result[0]):
                    reply = QMessageBox.question(self, 'Incluir Foto no PDF?', 'Esta OS possui uma foto de encerramento.\n\nDeseja incluir a foto no PDF?\n\nÔÇó SIM: PDF mais completo (pode gerar 2 p├íginas)\nÔÇó N├âO: PDF mais compacto (apenas texto)', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                    include_photo = reply == QMessageBox.Yes
                pdf_generator = ServiceOrderPDF(self.os_id, self.user_id)
                pdf_generator.generate_pdf(pdf_path, include_photo)
                reply = QMessageBox.question(self, 'PDF Gerado com Sucesso! Ô£à', f'PDF da Ordem de Servi├ºo foi salvo em:\n{pdf_path}\n\nDeseja abrir o arquivo?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    pass
        except PermissionError as e:
            QMessageBox.critical(self, 'Erro de Permiss├úo', f'N├úo foi poss├¡vel salvar o PDF no local escolhido.\n\nDetalhes: {str(e)}\n\nTente:\nÔÇó Escolher outro local\nÔÇó Fechar PDFs abertos\nÔÇó Executar como administrador')
        except Exception as e:
            QMessageBox.critical(self, 'Erro ao Gerar PDF', 'Ocorreu um erro ao gerar o PDF.\n\nTente novamente ou escolha outro local para salvar.')
    def imprimir_os_termico(self):
        try:
            from app.utils.service_order_thermal_pdf import ServiceOrderThermalPDF
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nome_sugerido = f'OS_{self.os_id}_thermal_{timestamp}.pdf'
            pdf_path, _ = QFileDialog.getSaveFileName(self, 'Salvar PDF T├®rmico 80mm', nome_sugerido, 'Arquivos PDF (*.pdf);;Todos os arquivos (*)')
            if not pdf_path:
                return
            if not pdf_path.lower().endswith('.pdf'):
                pdf_path += '.pdf'
            thermal_generator = ServiceOrderThermalPDF(self.os_id, self.user_id)
            if thermal_generator.generate_pdf(pdf_path):
                reply = QMessageBox.question(self, 'PDF T├®rmico Gerado! ­ƒû¿´©Å', f'PDF t├®rmico 80mm foi salvo em:\n{pdf_path}\n\nVoc├¬ pode:\nÔÇó Imprimir em impressora t├®rmica local\nÔÇó Enviar por WhatsApp/Email\nÔÇó Imprimir no celular via Bluetooth\n\nDeseja abrir o arquivo?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    pass
            try:
                if sys.platform == 'win32':
                    os.startfile(pdf_path)
                    return
                if sys.platform == 'darwin':
                    import subprocess
                    subprocess.call(['open', pdf_path])
                    return
                import subprocess
                subprocess.call(['xdg-open', pdf_path])
            except Exception as e:
                print(f'Erro ao abrir PDF: {e}')
            else:
                return
        except ImportError:
            QMessageBox.critical(self, 'Erro', 'M├│dulo de PDF t├®rmico n├úo encontrado.\n\nArquivo necess├írio: app/utils/service_order_thermal_pdf.py')
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao gerar PDF t├®rmico:\n\n{str(e)}')
# WARNING: Decompyle incomplete
