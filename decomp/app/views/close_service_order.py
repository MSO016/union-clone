from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox, QComboBox, QFileDialog, QScrollArea, QWidget, QLineEdit, QFrame)
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QPixmap
import sqlite3
from datetime import datetime
import shutil
import os
class CloseServiceOrderDialog(QDialog):
    def __init__(self, os_id, user_id, parent=None):
        super().__init__(parent)
        self.os_id = os_id
        self.user_id = user_id
        self.conn = None
        self.is_admin = parent.is_admin if hasattr(parent, 'is_admin') else False
        self.setWindowTitle('Encerrar Ordem de Servi├ºo')
        self.setModal(True)
        self.setMinimumSize(900, 700)
        self.showMaximized()
        self.foto_path = None
        self.setup_ui()
        self.carregar_dados_os()
    def keyPressEvent(self, event):
        '''PROTE├ç├âO CR├ìTICA: Bloqueia Enter/Return para evitar fechamento acidental'''
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            return
        super().keyPressEvent(event)
    def closeEvent(self, event):
        '''Sobrescreve o evento de fechamento para garantir que a conex├úo seja fechada'''
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
        event.accept()
    def setup_ui(self):
        '''Configura interface seguindo padr├úo das outras telas'''
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
        titulo = QLabel('­ƒöº Encerrar Ordem de Servi├ºo')
        titulo.setStyleSheet('\n            QLabel {\n                font-size: 18px;\n                font-weight: bold;\n                color: #2c3e50;\n                margin-left: 20px;\n            }\n        ')
        header_layout.addWidget(titulo)
        header_layout.addStretch()
        main_layout.addWidget(header_frame)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        self.criar_secao_status_valor(layout)
        self.criar_secao_solucao_passos(layout)
        self.criar_secao_observacoes(layout)
        self.criar_secao_foto(layout)
        self.criar_botoes_acao(layout)
        scroll.setWidget(main_widget)
        main_layout.addWidget(scroll)
    def criar_secao_status_valor(self, layout):
        '''Se├º├úo: Status e Valor do Servi├ºo'''
        secao_frame = QFrame()
        secao_frame.setStyleSheet('\n            QFrame {\n                background-color: #ffffff;\n                border: 1px solid #e0e0e0;\n                border-radius: 8px;\n                padding: 20px;\n            }\n        ')
        secao_layout = QVBoxLayout(secao_frame)
        titulo_secao = QLabel('­ƒÅÀ´©Å Status e Valor do Servi├ºo')
        titulo_secao.setStyleSheet('\n            QLabel {\n                font-size: 16px;\n                font-weight: bold;\n                color: #2c3e50;\n                margin-bottom: 15px;\n                padding-bottom: 10px;\n                border-bottom: 2px solid #3498db;\n            }\n        ')
        secao_layout.addWidget(titulo_secao)
        status_layout = QHBoxLayout()
        status_label = QLabel('­ƒôï Status Final:')
        status_label.setStyleSheet('font-weight: bold; color: #34495e;')
        self.status_combo = QComboBox()
        self.status_combo.addItems(['Conclu├¡do com Sucesso', 'Conclu├¡do sem Solu├º├úo'])
        self.status_combo.setStyleSheet('\n            QComboBox {\n                border: 1px solid #bdc3c7;\n                border-radius: 4px;\n                padding: 6px;\n                min-width: 200px;\n                background-color: #f8f9fa;\n                color: #2c3e50;\n            }\n            QComboBox:focus {\n                border: 2px solid #3498db;\n                background-color: #ffffff;\n            }\n        ')
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_combo)
        status_layout.addStretch()
        secao_layout.addLayout(status_layout)
        valor_layout = QHBoxLayout()
        valor_label = QLabel('­ƒÆ░ Valor do Servi├ºo (R$):')
        valor_label.setStyleSheet('font-weight: bold; color: #34495e;')
        self.valor_input = QLineEdit()
        self.valor_input.setPlaceholderText('0,00')
        self.valor_input.setMaxLength(10)
        self.valor_input.textChanged.connect(self.validar_valor)
        self.valor_input.setStyleSheet('\n            QLineEdit {\n                border: 1px solid #bdc3c7;\n                border-radius: 4px;\n                padding: 6px;\n                min-width: 150px;\n                background-color: #f8f9fa;\n                color: #2c3e50;\n            }\n            QLineEdit:focus {\n                border: 2px solid #3498db;\n                background-color: #ffffff;\n            }\n        ')
        valor_layout.addWidget(valor_label)
        valor_layout.addWidget(self.valor_input)
        valor_layout.addStretch()
        secao_layout.addLayout(valor_layout)
        layout.addWidget(secao_frame)
    def criar_secao_solucao_passos(self, layout):
        '''Se├º├úo: Solu├º├úo e Passos Realizados'''
        secao_frame = QFrame()
        secao_frame.setStyleSheet('\n            QFrame {\n                background-color: #ffffff;\n                border: 1px solid #e0e0e0;\n                border-radius: 8px;\n                padding: 20px;\n            }\n        ')
        secao_layout = QVBoxLayout(secao_frame)
        titulo_secao = QLabel('­ƒöº Solu├º├úo e Passos Realizados')
        titulo_secao.setStyleSheet('\n            QLabel {\n                font-size: 16px;\n                font-weight: bold;\n                color: #2c3e50;\n                margin-bottom: 15px;\n                padding-bottom: 10px;\n                border-bottom: 2px solid #27ae60;\n            }\n        ')
        secao_layout.addWidget(titulo_secao)
        solucao_label = QLabel('Ô£à Solu├º├úo Aplicada:')
        solucao_label.setStyleSheet('font-weight: bold; color: #34495e; margin-top: 5px;')
        self.solucao_text = QTextEdit()
        self.solucao_text.setPlaceholderText('Descreva detalhadamente a solu├º├úo aplicada...')
        self.solucao_text.setTabChangesFocus(True)
        self.solucao_text.setMinimumHeight(80)
        self.solucao_text.setStyleSheet('\n            QTextEdit {\n                border: 1px solid #bdc3c7;\n                border-radius: 4px;\n                padding: 8px;\n                background-color: #f8f9fa;\n                color: #2c3e50;\n            }\n            QTextEdit:focus {\n                border: 2px solid #27ae60;\n                background-color: #ffffff;\n            }\n        ')
        secao_layout.addWidget(solucao_label)
        secao_layout.addWidget(self.solucao_text)
        passos_label = QLabel('­ƒôï Passos Realizados:')
        passos_label.setStyleSheet('font-weight: bold; color: #34495e; margin-top: 10px;')
        self.passos_text = QTextEdit()
        self.passos_text.setPlaceholderText('Liste detalhadamente todos os passos realizados durante o reparo...')
        self.passos_text.setTabChangesFocus(True)
        self.passos_text.setMinimumHeight(80)
        self.passos_text.setStyleSheet('\n            QTextEdit {\n                border: 1px solid #bdc3c7;\n                border-radius: 4px;\n                padding: 8px;\n                background-color: #f8f9fa;\n                color: #2c3e50;\n            }\n            QTextEdit:focus {\n                border: 2px solid #27ae60;\n                background-color: #ffffff;\n            }\n        ')
        secao_layout.addWidget(passos_label)
        secao_layout.addWidget(self.passos_text)
        layout.addWidget(secao_frame)
    def criar_secao_observacoes(self, layout):
        '''Se├º├úo: Observa├º├Áes e Motivo de Falha'''
        secao_frame = QFrame()
        secao_frame.setStyleSheet('\n            QFrame {\n                background-color: #ffffff;\n                border: 1px solid #e0e0e0;\n                border-radius: 8px;\n                padding: 20px;\n            }\n        ')
        secao_layout = QVBoxLayout(secao_frame)
        titulo_secao = QLabel('­ƒôØ Observa├º├Áes e Motivo de Falha')
        titulo_secao.setStyleSheet('\n            QLabel {\n                font-size: 16px;\n                font-weight: bold;\n                color: #2c3e50;\n                margin-bottom: 15px;\n                padding-bottom: 10px;\n                border-bottom: 2px solid #e67e22;\n            }\n        ')
        secao_layout.addWidget(titulo_secao)
        falha_label = QLabel('ÔØî Motivo da Falha (se aplic├ível):')
        falha_label.setStyleSheet('font-weight: bold; color: #34495e; margin-top: 5px;')
        self.falha_text = QTextEdit()
        self.falha_text.setPlaceholderText('Se n├úo foi poss├¡vel resolver, explique detalhadamente o motivo...')
        self.falha_text.setTabChangesFocus(True)
        self.falha_text.setMinimumHeight(80)
        self.falha_text.setStyleSheet('\n            QTextEdit {\n                border: 1px solid #bdc3c7;\n                border-radius: 4px;\n                padding: 8px;\n                background-color: #f8f9fa;\n                color: #2c3e50;\n            }\n            QTextEdit:focus {\n                border: 2px solid #e67e22;\n                background-color: #ffffff;\n            }\n        ')
        secao_layout.addWidget(falha_label)
        secao_layout.addWidget(self.falha_text)
        obs_label = QLabel('­ƒôÄ Observa├º├Áes T├®cnicas:')
        obs_label.setStyleSheet('font-weight: bold; color: #34495e; margin-top: 10px;')
        self.obs_text = QTextEdit()
        self.obs_text.setPlaceholderText('Observa├º├Áes adicionais, dicas t├®cnicas, recomenda├º├Áes...')
        self.obs_text.setTabChangesFocus(True)
        self.obs_text.setMinimumHeight(80)
        self.obs_text.setStyleSheet('\n            QTextEdit {\n                border: 1px solid #bdc3c7;\n                border-radius: 4px;\n                padding: 8px;\n                background-color: #f8f9fa;\n                color: #2c3e50;\n            }\n            QTextEdit:focus {\n                border: 2px solid #e67e22;\n                background-color: #ffffff;\n            }\n        ')
        secao_layout.addWidget(obs_label)
        secao_layout.addWidget(self.obs_text)
        layout.addWidget(secao_frame)
    def criar_secao_foto(self, layout):
        '''Se├º├úo: Foto do Servi├ºo'''
        secao_frame = QFrame()
        secao_frame.setStyleSheet('\n            QFrame {\n                background-color: #ffffff;\n                border: 1px solid #e0e0e0;\n                border-radius: 8px;\n                padding: 20px;\n            }\n        ')
        secao_layout = QVBoxLayout(secao_frame)
        titulo_secao = QLabel('­ƒô© Foto do Servi├ºo')
        titulo_secao.setStyleSheet('\n            QLabel {\n                font-size: 16px;\n                font-weight: bold;\n                color: #2c3e50;\n                margin-bottom: 15px;\n                padding-bottom: 10px;\n                border-bottom: 2px solid #9b59b6;\n            }\n        ')
        secao_layout.addWidget(titulo_secao)
        foto_layout = QHBoxLayout()
        self.foto_label = QLabel('­ƒôÀ Foto de conclus├úo do servi├ºo:')
        self.foto_label.setStyleSheet('font-weight: bold; color: #34495e;')
        self.foto_preview = QLabel()
        self.foto_preview.setFixedSize(200, 150)
        self.foto_preview.setStyleSheet('\n            QLabel {\n                border: 2px dashed #bdc3c7;\n                border-radius: 4px;\n                background-color: #f8f9fa;\n            }\n        ')
        self.foto_preview.setScaledContents(True)
        foto_buttons_layout = QVBoxLayout()
        self.foto_btn = QPushButton('­ƒôü Selecionar Foto')
        self.foto_btn.clicked.connect(self.selecionar_foto)
        self.foto_btn.setStyleSheet('\n            QPushButton {\n                background-color: #3498db;\n                color: white;\n                border: none;\n                padding: 8px 15px;\n                border-radius: 4px;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background-color: #2980b9;\n            }\n        ')
        foto_buttons_layout.addWidget(self.foto_btn)
        self.remover_foto_btn = QPushButton('­ƒùæ´©Å Remover Foto')
        self.remover_foto_btn.setStyleSheet('\n            QPushButton {\n                background-color: #e74c3c;\n                color: white;\n                border: none;\n                padding: 8px 15px;\n                border-radius: 4px;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background-color: #c0392b;\n            }\n        ')
        self.remover_foto_btn.clicked.connect(self.remover_foto)
        self.remover_foto_btn.setVisible(False)
        foto_buttons_layout.addWidget(self.remover_foto_btn)
        foto_layout.addWidget(self.foto_label)
        foto_layout.addWidget(self.foto_preview)
        foto_layout.addLayout(foto_buttons_layout)
        secao_layout.addLayout(foto_layout)
        layout.addWidget(secao_frame)
    def criar_botoes_acao(self, layout):
        '''Bot├Áes de a├º├úo finais'''
        layout.addSpacing(20)
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        salvar_btn = QPushButton('Ô£à Encerrar O.S.')
        salvar_btn.setStyleSheet('\n            QPushButton {\n                background-color: #27ae60;\n                color: white;\n                border: none;\n                padding: 12px 25px;\n                border-radius: 6px;\n                font-weight: bold;\n                font-size: 14px;\n            }\n            QPushButton:hover {\n                background-color: #229954;\n            }\n        ')
        salvar_btn.clicked.connect(self.encerrar_os)
        cancelar_btn = QPushButton('ÔØî Cancelar')
        cancelar_btn.setStyleSheet('\n            QPushButton {\n                background-color: #e74c3c;\n                color: white;\n                border: none;\n                padding: 12px 25px;\n                border-radius: 6px;\n                font-weight: bold;\n                font-size: 14px;\n            }\n            QPushButton:hover {\n                background-color: #c0392b;\n            }\n        ')
        cancelar_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(salvar_btn)
        buttons_layout.addSpacing(10)
        buttons_layout.addWidget(cancelar_btn)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
    def validar_valor(self, texto):
        '''Valida├º├úo para campo de valor monet├írio'''
        import re
        texto_limpo = re.sub('[^\\d,.]', '', texto)
        texto_limpo = texto_limpo.replace('.', ',')
        partes = texto_limpo.split(',')
        if len(partes) > 2:
            texto_limpo = partes[0] + ',' + ''.join(partes[1:])
        if len(partes) == 2 and len(partes[1]) > 2:
            texto_limpo = partes[0] + ',' + partes[1][:2]
        if texto != texto_limpo:
            self.valor_input.setText(texto_limpo)
    def carregar_dados_os(self):
        try:
            if self.conn:
                self.conn.close()
            self.conn = sqlite3.connect('app/database/service_orders.db')
            cursor = self.conn.cursor()
            cursor.execute('\n                SELECT solution, steps_taken, failure_reason, technician_notes, service_value\n                FROM service_orders WHERE id = ?\n            ', (self.os_id,))
            dados = cursor.fetchone()
            if dados:
                self.solucao_text.setText(dados[0] or '')
                self.passos_text.setText(dados[1] or '')
                self.falha_text.setText(dados[2] or '')
                self.obs_text.setText(dados[3] or '')
                if dados[4]:
                    valor_formatado = f'{float(dados[4]):.2f}'.replace('.', ',')
                    self.valor_input.setText(valor_formatado)
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao carregar dados: {str(e)}')
            self.reject()
        if self.conn:
            self.conn.close()
            self.conn = None
    def selecionar_foto(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Selecionar Foto', '', 'Imagens (*.png *.jpg *.jpeg)')
        if file_name:
            photos_dir = os.path.join('app', 'photos', 'service_orders')
            os.makedirs(photos_dir, exist_ok=True)
            new_filename = f'os_{self.os_id}_completion_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg'
            new_path = os.path.join(photos_dir, new_filename)
            shutil.copy2(file_name, new_path)
            self.foto_path = new_path
            pixmap = QPixmap(file_name)
            self.foto_preview.setPixmap(pixmap.scaled(200, 150, Qt.KeepAspectRatio))
            self.remover_foto_btn.setVisible(True)
    def remover_foto(self):
        '''Remove a foto selecionada'''
        if self.foto_path and os.path.exists(self.foto_path):
            try:
                os.remove(self.foto_path)
            except Exception as e:
                print(f'Erro ao remover arquivo de foto: {str(e)}')
        self.foto_path = None
        self.foto_preview.clear()
        self.foto_preview.setText('')
        self.remover_foto_btn.setVisible(False)
    def encerrar_os(self):
        try:
            if self.conn:
                self.conn.close()
            self.conn = sqlite3.connect('app/database/service_orders.db')
            cursor = self.conn.cursor()
            status = 'concluido_sucesso' if self.status_combo.currentText() == 'Conclu├¡do com Sucesso' else 'concluido_sem_solucao'
            solucao = self.solucao_text.toPlainText().strip()
            passos = self.passos_text.toPlainText().strip()
            falha = self.falha_text.toPlainText().strip()
            obs = self.obs_text.toPlainText().strip()
            valor_texto = self.valor_input.text().strip().replace(',', '.')
            try:
                valor = float(valor_texto) if valor_texto else 0.0
            except ValueError:
                valor = 0.0
            else:
                if status == 'concluido_sucesso' and not solucao:
                    QMessageBox.warning(self, 'Erro', 'Para concluir com sucesso, descreva a solu├º├úo aplicada!')
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao encerrar O.S.: {str(e)}')
            if self.conn:
                self.conn.rollback()
        try:
            if not passos:
                QMessageBox.warning(self, 'Erro', 'Descreva os passos realizados!')
                if self.conn:
                    self.conn.close()
                    self.conn = None
                    return
                return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao encerrar O.S.: {str(e)}')
            if self.conn:
                self.conn.rollback()
        try:
            if status == 'concluido_sem_solucao' and not falha:
                QMessageBox.warning(self, 'Erro', 'Para concluir sem solu├º├úo, explique o motivo da falha!')
                if self.conn:
                    self.conn.close()
                    self.conn = None
                    return
                return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao encerrar O.S.: {str(e)}')
            if self.conn:
                self.conn.rollback()
        try:
            data_conclusao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f'DEBUG: Salvando completion_date como: {data_conclusao}')
            cursor.execute('\n                UPDATE service_orders \n                SET status = ?,\n                    solution = ?,\n                    steps_taken = ?,\n                    failure_reason = ?,\n                    technician_notes = ?,\n                    completion_date = ?,\n                    completion_photo = ?,\n                    service_value = ?\n                WHERE id = ?\n            ', (status, solucao, passos, falha, obs, data_conclusao, self.foto_path, valor, self.os_id))
            if status == 'concluido_sucesso':
                cursor.execute('\n                    SELECT device_type, brand, model, reported_issue\n                    FROM service_orders WHERE id = ?\n                ', (self.os_id,))
                os_data = cursor.fetchone()
                if os_data:
                    cursor.execute('\n                        INSERT INTO knowledge_base (\n                            device_type, brand, model, issue_description,\n                            solution, steps_taken, success_rate, user_id\n                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)\n                    ', (os_data[0], os_data[1], os_data[2], os_data[3], solucao, passos, 100, self.user_id))
            self.conn.commit()
            QMessageBox.information(self, 'Sucesso', 'Ordem de Servi├ºo encerrada com sucesso!')
            reply = QMessageBox.question(self, 'Gerar PDF da OS', 'Ordem de Servi├ºo encerrada!\n\nDeseja gerar o PDF agora?\n\nÔÇó SIM: Escolher formato (A4 ou T├®rmico 80mm)\nÔÇó N├âO: Apenas salvar (pode gerar depois)', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                formato_msg = QMessageBox()
                formato_msg.setIcon(QMessageBox.Question)
                formato_msg.setWindowTitle('Escolher Formato do PDF')
                formato_msg.setText('Escolha o formato do PDF:\n\n­ƒôä PDF A4: Impress├úo padr├úo, completo\n­ƒû¿´©Å PDF 80mm: Impressora t├®rmica, compacto')
                btn_a4 = formato_msg.addButton('­ƒôä PDF A4', QMessageBox.AcceptRole)
                btn_thermal = formato_msg.addButton('­ƒû¿´©Å PDF 80mm', QMessageBox.ActionRole)
                formato_msg.addButton('Cancelar', QMessageBox.RejectRole)
                formato_msg.exec_()
                if formato_msg.clickedButton() == btn_a4:
                    self.gerar_pdf_a4()
                elif formato_msg.clickedButton() == btn_thermal:
                    self.gerar_pdf_termico()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao encerrar O.S.: {str(e)}')
            if self.conn:
                self.conn.rollback()
        if self.conn:
            self.conn.close()
            self.conn = None
    def gerar_pdf_a4(self):
        '''
        Gera PDF A4 padr├úo da OS encerrada
        '''
        try:
            from app.utils.service_order_pdf import ServiceOrderPDF
            import subprocess
            import sys
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            default_name = f'OS_{self.os_id}_{timestamp}.pdf'
            pdf_path, _ = QFileDialog.getSaveFileName(self, 'Salvar PDF A4', default_name, 'Arquivos PDF (*.pdf)')
            if not pdf_path:
                return
            if not pdf_path.lower().endswith('.pdf'):
                pdf_path += '.pdf'
            include_photo = False
            if self.foto_path and os.path.exists(self.foto_path):
                reply = QMessageBox.question(self, 'Incluir Foto?', 'Esta OS possui uma foto de encerramento.\n\nDeseja incluir a foto no PDF?\n\nÔÇó SIM: PDF mais completo (pode gerar 2 p├íginas)\nÔÇó N├âO: PDF mais compacto (apenas texto)', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                include_photo = reply == QMessageBox.Yes
            pdf_generator = ServiceOrderPDF(self.os_id, self.user_id)
            pdf_generator.generate_pdf(pdf_path, include_photo)
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
    def gerar_pdf_termico(self):
        '''
        ­ƒåò NOVO: Gera PDF T├®rmico 80mm da OS encerrada
        '''
        try:
            from app.utils.service_order_thermal_pdf import ServiceOrderThermalPDF
            import subprocess
            import sys
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            default_name = f'OS_{self.os_id}_thermal_{timestamp}.pdf'
            pdf_path, _ = QFileDialog.getSaveFileName(self, 'Salvar PDF T├®rmico 80mm', default_name, 'Arquivos PDF (*.pdf)')
            if not pdf_path:
                return
            if not pdf_path.lower().endswith('.pdf'):
                pdf_path += '.pdf'
            thermal_generator = ServiceOrderThermalPDF(self.os_id, self.user_id)
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
