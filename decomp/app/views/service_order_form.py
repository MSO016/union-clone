from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QComboBox, QTextEdit, QFileDialog, QScrollArea, QWidget, QFrame, QCompleter)
from PyQt5.QtCore import Qt, QStringListModel
from PyQt5.QtGui import QFont
from app.utils.service_order_pdf import ServiceOrderPDF
import sqlite3
import os
from datetime import datetime
class ServiceOrderForm(QDialog):
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.is_admin = parent.is_admin if hasattr(parent, 'is_admin') else False
        self.setWindowTitle('Nova Ordem de Servi├ºo')
        self.setModal(True)
        self.setMinimumSize(1000, 700)
        self.showMaximized()
        self.fotos = []
        self.setup_ui()
        self.carregar_clientes()
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
        titulo = QLabel('Nova Ordem de Servi├ºo')
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
        self.criar_secao_cliente(layout)
        self.criar_secao_dispositivo(layout)
        self.criar_secao_diagnostico(layout)
        self.criar_botoes_acao(layout)
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
    def carregar_clientes(self):
        '''Carrega todos os clientes para busca e combo (ATUALIZADO)'''
        try:
            conn = sqlite3.connect('app/database/service_orders.db')
            cursor = conn.cursor()
            cursor.execute('\n                SELECT id, name, phone FROM clients\n                WHERE user_id = ?\n                ORDER BY name\n            ', (self.user_id,))
            self.todos_clientes = cursor.fetchall()
            self.cliente_combo.clear()
            for id, nome, telefone in self.todos_clientes:
                self.cliente_combo.addItem(f'{nome} - {telefone}', id)
            if not self._combo_connected:
                self.cliente_combo.currentTextChanged.connect(self._on_combo_changed)
                self._combo_connected = True
            self._atualizar_feedback_busca('normal', f'{len(self.todos_clientes)} clientes dispon├¡veis')
            self.setup_autocomplete()
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao carregar clientes: {str(e)}')
        if conn:
            conn.close()
    def setup_autocomplete(self):
        '''Configura autocomplete inteligente para o campo de busca (NOVA FUNCIONALIDADE)'''
        if not hasattr(self, 'todos_clientes') or not self.todos_clientes:
            return
        sugestoes = []
        self.cliente_map = {}
        for id, nome, telefone in self.todos_clientes:
            display = f'{nome} - {telefone}' if telefone else nome
            sugestoes.append(display)
            self.cliente_map[display] = {'id': id, 'nome': nome, 'telefone': telefone or 'N├úo informado'}
        self.completer = QCompleter(sugestoes, self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.activated.connect(self.on_autocomplete_selected)
        self.busca_cliente_input.setCompleter(self.completer)
    def on_autocomplete_selected(self, text):
        '''Chamado quando usu├írio seleciona item do autocomplete (NOVA FUNCIONALIDADE)'''
        if text in self.cliente_map:
            cliente_data = self.cliente_map[text]
            self._updating_from_search = True
            combo_encontrado = False
            for i in range(self.cliente_combo.count()):
                if not self.cliente_combo.itemText(i) == text:
                    continue
                self.cliente_combo.setCurrentIndex(i)
                combo_encontrado = True
                break
            if not combo_encontrado:
                self.cliente_combo.addItem(text, cliente_data['id'])
                self.cliente_combo.setCurrentIndex(self.cliente_combo.count() - 1)
            self.busca_cliente_input.setText(text)
            self.mostrar_detalhes_cliente(cliente_data)
            self._atualizar_feedback_busca('sucesso', f'{cliente_data['nome']} selecionado')
            self._updating_from_search = False
    def mostrar_detalhes_cliente(self, cliente_data):
        '''Mostra detalhes do cliente selecionado (NOVA FUNCIONALIDADE)'''
        try:
            conn = sqlite3.connect('app/database/service_orders.db')
            cursor = conn.cursor()
            cursor.execute('\n                SELECT name, phone, email, address FROM clients\n                WHERE id = ? AND user_id = ?\n            ', (cliente_data['id'], self.user_id))
            dados = cursor.fetchone()
            if dados:
                nome, telefone, email, endereco = dados
                detalhes = f'{telefone or 'N├úo informado'}'
                if email:
                    detalhes += f' | {email}'
                if endereco:
                    detalhes += f' | {endereco}'
                self.cliente_detalhes_label.setText(f'Cliente: {nome}\n{detalhes}')
                self.cliente_detalhes_frame.setVisible(True)
        except Exception as e:
            print(f'Erro ao carregar detalhes do cliente: {e}')
        if conn:
            conn.close()
    def ocultar_detalhes_cliente(self):
        '''Oculta ├írea de detalhes do cliente (NOVA FUNCIONALIDADE)'''
        self.cliente_detalhes_frame.setVisible(False)
    def novo_cliente(self):
        from app.views.client_form import ClientForm
        dialog = ClientForm(self.user_id, self)
        if dialog.exec_() == ClientForm.Accepted:
            self.busca_cliente_input.clear()
            self.carregar_clientes()
    def adicionar_fotos(self):
        fotos, _ = QFileDialog.getOpenFileNames(self, 'Selecionar Fotos', '', 'Imagens (*.png *.jpg *.jpeg)')
        if fotos:
            self.fotos.extend(fotos)
            self.fotos_label.setText(f'Fotos: {len(self.fotos)} selecionadas')
    def salvar_os(self):
        cliente_selecionado = None
        if self.cliente_combo.currentData() is not None:
            cliente_selecionado = self.cliente_combo.currentData()
        elif hasattr(self, 'cliente_map') and self.busca_cliente_input.text().strip():
            texto_busca = self.busca_cliente_input.text().strip()
            for display_text, data in self.cliente_map.items():
                if texto_busca != display_text and texto_busca not in display_text:
                    if not data['nome'].lower() == texto_busca.lower():
                        continue
                cliente_selecionado = data['id']
                for i in range(self.cliente_combo.count()):
                    if not self.cliente_combo.itemText(i) == display_text:
                        continue
                    self.cliente_combo.setCurrentIndex(i)
                    break
                break
        if cliente_selecionado is None:
            QMessageBox.warning(self, 'Erro', 'Selecione um cliente v├ílido!')
            return
        if not (self.marca_input.text().strip() and self.modelo_input.text().strip()):
            QMessageBox.warning(self, 'Erro', 'Marca e modelo s├úo obrigat├│rios!')
            return
        if not self.problema_text.toPlainText().strip():
            QMessageBox.warning(self, 'Erro', 'Descreva o problema relatado!')
            return
        try:
            conn = sqlite3.connect('app/database/service_orders.db')
            cursor = conn.cursor()
            valor_texto = self.valor_input.text().strip().replace(',', '.')
            try:
                valor = float(valor_texto) if valor_texto else None
            except ValueError:
                valor = None
            else:
                cursor.execute('\n                INSERT INTO service_orders (\n                    client_id, device_type, brand, model, serial_number,\n                    reported_issue, initial_diagnosis, status, service_value, user_id\n                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n            ', (cliente_selecionado, self.tipo_combo.currentText(), self.marca_input.text().strip(), self.modelo_input.text().strip(), self.serie_input.text().strip(), self.problema_text.toPlainText().strip(), self.diagnostico_text.toPlainText().strip(), 'em_reparo', valor, self.user_id))
                os_id = cursor.lastrowid
                if self.fotos:
                    fotos_dir = os.path.join('app', 'data', 'fotos', str(os_id))
                    os.makedirs(fotos_dir, exist_ok=True)
                    for i, foto_path in enumerate(self.fotos):
                        ext = os.path.splitext(foto_path)[1]
                        novo_nome = f'foto_{i + 1}{ext}'
                        novo_path = os.path.join(fotos_dir, novo_nome)
                        with open(foto_path, 'rb'):
                            pass
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao salvar OS: {str(e)}')
        conn.commit()
        reply = QMessageBox.question(self, 'Gerar PDF da OS', 'Ordem de Servi├ºo cadastrada com sucesso!\n\nDeseja gerar o PDF agora?\n\nÔÇó SIM: Escolher formato (A4 ou T├®rmico 80mm)\nÔÇó N├âO: Apenas salvar (pode gerar depois)', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            formato_msg = QMessageBox()
            formato_msg.setIcon(QMessageBox.Question)
            formato_msg.setWindowTitle('Escolher Formato do PDF')
            formato_msg.setText('Escolha o formato do PDF:\n\nPDF A4: Impress├úo padr├úo, completo\nPDF 80mm: Impressora t├®rmica, compacto')
            btn_a4 = formato_msg.addButton('PDF A4', QMessageBox.AcceptRole)
            btn_thermal = formato_msg.addButton('PDF 80mm', QMessageBox.ActionRole)
            formato_msg.addButton('Cancelar', QMessageBox.RejectRole)
            formato_msg.exec_()
            if formato_msg.clickedButton() == btn_a4:
                self.gerar_pdf_os(os_id)
            elif formato_msg.clickedButton() == btn_thermal:
                self.gerar_pdf_termico(os_id)
        QMessageBox.information(self, 'Sucesso', 'Ordem de Servi├ºo cadastrada com sucesso!')
        self.accept()
        if conn:
            conn.close()
    def gerar_pdf_os(self, os_id):
        '''Gera PDF A4 padr├úo da OS'''
        try:
            from datetime import datetime
            import time
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nome_sugerido = f'OS_{os_id}_{timestamp}.pdf'
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
                pdf_generator = ServiceOrderPDF(os_id, self.user_id)
                pdf_generator.generate_pdf(pdf_path, include_photo=False)
                reply = QMessageBox.question(self, 'PDF Gerado com Sucesso!', f'PDF da Ordem de Servi├ºo foi salvo em:\n{pdf_path}\n\nDeseja abrir o arquivo?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    pass
        except PermissionError as e:
            QMessageBox.critical(self, 'Erro de Permiss├úo', f'N├úo foi poss├¡vel salvar o PDF no local escolhido.\n\nDetalhes: {str(e)}\n\nTente:\nÔÇó Escolher outro local\nÔÇó Fechar PDFs abertos\nÔÇó Executar como administrador')
        except Exception as e:
            QMessageBox.critical(self, 'Erro ao Gerar PDF', 'Ocorreu um erro ao gerar o PDF.\n\nTente novamente ou escolha outro local para salvar.')
    def gerar_pdf_termico(self, os_id):
        '''
        ­ƒåò NOVO: Gera PDF T├®rmico 80mm
        Abordagem simplificada: igual ao PDF A4, mas formato 80mm
        '''
        try:
            from app.utils.service_order_thermal_pdf import ServiceOrderThermalPDF
            from datetime import datetime
            import subprocess
            import sys
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nome_sugerido = f'OS_{os_id}_thermal_{timestamp}.pdf'
            pdf_path, _ = QFileDialog.getSaveFileName(self, 'Salvar PDF T├®rmico 80mm', nome_sugerido, 'Arquivos PDF (*.pdf);;Todos os arquivos (*)')
            if not pdf_path:
                return
            if not pdf_path.lower().endswith('.pdf'):
                pdf_path += '.pdf'
            thermal_generator = ServiceOrderThermalPDF(os_id, self.user_id)
            if thermal_generator.generate_pdf(pdf_path):
                reply = QMessageBox.question(self, 'PDF T├®rmico Gerado!', f'PDF t├®rmico 80mm foi salvo em:\n{pdf_path}\n\nVoc├¬ pode:\nÔÇó Imprimir em impressora t├®rmica local\nÔÇó Enviar por WhatsApp/Email\nÔÇó Imprimir no celular via Bluetooth\n\nDeseja abrir o arquivo?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
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
            QMessageBox.critical(self, 'Erro', 'M├│dulo de PDF t├®rmico n├úo encontrado.\n\nArquivo necess├írio: app/utils/service_order_thermal_pdf.py')
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao gerar PDF t├®rmico:\n\n{str(e)}')
    def criar_secao_cliente(self, layout):
        '''Cria se├º├úo de sele├º├úo de cliente com busca melhorada'''
        secao_frame = QFrame()
        secao_frame.setStyleSheet('\n            QFrame {\n                background-color: #f8f9fa;\n                border: 1px solid #dee2e6;\n                border-radius: 8px;\n                padding: 15px;\n            }\n        ')
        secao_layout = QVBoxLayout(secao_frame)
        titulo = QLabel('Sele├º├úo de Cliente')
        titulo.setStyleSheet('\n            QLabel {\n                font-size: 16px;\n                font-weight: bold;\n                color: #2c3e50;\n                margin-bottom: 10px;\n            }\n        ')
        secao_layout.addWidget(titulo)
        cliente_layout = QHBoxLayout()
        cliente_label = QLabel('Cliente:')
        cliente_label.setMinimumWidth(80)
        cliente_label.setStyleSheet('font-weight: bold; color: #495057;')
        self.busca_cliente_input = QLineEdit()
        self.busca_cliente_input.setPlaceholderText('Digite o nome do cliente...')
        self.busca_cliente_input.setMinimumHeight(35)
        self.busca_cliente_input.setStyleSheet('\n            QLineEdit {\n                border: 1px solid #ced4da;\n                border-radius: 4px;\n                padding: 8px;\n                font-size: 14px;\n                background-color: white;\n            }\n            QLineEdit:focus {\n                border-color: #007bff;\n            }\n        ')
        self.busca_cliente_input.textChanged.connect(self.filtrar_clientes)
        self.setup_autocomplete()
        self._combo_connected = False
        self.cliente_combo = QComboBox()
        self.cliente_combo.setMinimumWidth(300)
        self.cliente_combo.setMinimumHeight(35)
        self.cliente_combo.setStyleSheet('\n            QComboBox {\n                border: 1px solid #ced4da;\n                border-radius: 4px;\n                padding: 8px;\n                font-size: 14px;\n                background-color: white;\n                color: #2c3e50;\n            }\n            QComboBox:focus {\n                border-color: #007bff;\n            }\n            QComboBox QAbstractItemView {\n                background-color: white;\n                border: 1px solid #ced4da;\n                selection-background-color: #007bff;\n                selection-color: white;\n                color: #2c3e50;\n            }\n        ')
        novo_cliente_btn = QPushButton('+ Novo Cliente')
        novo_cliente_btn.setStyleSheet('\n            QPushButton {\n                background-color: #28a745;\n                color: white;\n                border: none;\n                padding: 8px 16px;\n                border-radius: 4px;\n                font-weight: bold;\n                font-size: 14px;\n                min-width: 120px;\n            }\n            QPushButton:hover {\n                background-color: #218838;\n            }\n        ')
        novo_cliente_btn.clicked.connect(self.novo_cliente)
        cliente_layout.addWidget(cliente_label)
        cliente_layout.addWidget(self.busca_cliente_input)
        cliente_layout.addWidget(self.cliente_combo)
        cliente_layout.addWidget(novo_cliente_btn)
        secao_layout.addLayout(cliente_layout)
        self.cliente_detalhes_frame = QFrame()
        self.cliente_detalhes_frame.setStyleSheet('\n            QFrame {\n                background-color: #e8f5e8;\n                border: 1px solid #c3e6c3;\n                border-radius: 4px;\n                padding: 10px;\n                margin-top: 5px;\n            }\n        ')
        self.cliente_detalhes_frame.setVisible(False)
        detalhes_layout = QVBoxLayout(self.cliente_detalhes_frame)
        detalhes_layout.setContentsMargins(10, 5, 10, 5)
        self.cliente_detalhes_label = QLabel()
        self.cliente_detalhes_label.setStyleSheet('\n            QLabel {\n                color: #2d5a2d;\n                font-weight: bold;\n                background: transparent;\n                border: none;\n            }\n        ')
        detalhes_layout.addWidget(self.cliente_detalhes_label)
        secao_layout.addWidget(self.cliente_detalhes_frame)
        layout.addWidget(secao_frame)
    def criar_secao_dispositivo(self, layout):
        '''Cria se├º├úo com informa├º├Áes do dispositivo'''
        secao_frame = QFrame()
        secao_frame.setStyleSheet('\n            QFrame {\n                background-color: #f8f9fa;\n                border: 1px solid #dee2e6;\n                border-radius: 8px;\n                padding: 15px;\n            }\n        ')
        secao_layout = QVBoxLayout(secao_frame)
        titulo = QLabel('Informa├º├Áes do Dispositivo')
        titulo.setStyleSheet('\n            QLabel {\n                font-size: 16px;\n                font-weight: bold;\n                color: #2c3e50;\n                margin-bottom: 10px;\n            }\n        ')
        secao_layout.addWidget(titulo)
        tipo_layout = QHBoxLayout()
        tipo_label = QLabel('Tipo:')
        tipo_label.setMinimumWidth(80)
        tipo_label.setStyleSheet('font-weight: bold; color: #495057;')
        self.tipo_combo = QComboBox()
        self.tipo_combo.addItems(['Notebook', 'Smartphone', 'Desktop', 'Tablet', 'Impressora', 'Outro'])
        self.tipo_combo.setMinimumHeight(35)
        self.tipo_combo.setStyleSheet('\n            QComboBox {\n                border: 1px solid #ced4da;\n                border-radius: 4px;\n                padding: 8px;\n                font-size: 14px;\n                background-color: white;\n                color: #2c3e50;\n            }\n            QComboBox:focus {\n                border-color: #007bff;\n            }\n        ')
        tipo_layout.addWidget(tipo_label)
        tipo_layout.addWidget(self.tipo_combo)
        tipo_layout.addStretch()
        secao_layout.addLayout(tipo_layout)
        grid_layout = QHBoxLayout()
        marca_layout = QVBoxLayout()
        marca_label = QLabel('Marca:')
        marca_label.setStyleSheet('font-weight: bold; color: #495057; margin-top: 10px;')
        self.marca_input = QLineEdit()
        self.marca_input.setMinimumHeight(35)
        self.marca_input.setStyleSheet('\n            QLineEdit {\n                border: 1px solid #ced4da;\n                border-radius: 4px;\n                padding: 8px;\n                font-size: 14px;\n                background-color: white;\n            }\n            QLineEdit:focus {\n                border-color: #007bff;\n            }\n        ')
        marca_layout.addWidget(marca_label)
        marca_layout.addWidget(self.marca_input)
        modelo_layout = QVBoxLayout()
        modelo_label = QLabel('Modelo:')
        modelo_label.setStyleSheet('font-weight: bold; color: #495057; margin-top: 10px;')
        self.modelo_input = QLineEdit()
        self.modelo_input.setMinimumHeight(35)
        self.modelo_input.setStyleSheet('\n            QLineEdit {\n                border: 1px solid #ced4da;\n                border-radius: 4px;\n                padding: 8px;\n                font-size: 14px;\n                background-color: white;\n            }\n            QLineEdit:focus {\n                border-color: #007bff;\n            }\n        ')
        modelo_layout.addWidget(modelo_label)
        modelo_layout.addWidget(self.modelo_input)
        grid_layout.addLayout(marca_layout)
        grid_layout.addLayout(modelo_layout)
        secao_layout.addLayout(grid_layout)
        serie_layout = QVBoxLayout()
        serie_label = QLabel('N┬║ S├®rie (opcional):')
        serie_label.setStyleSheet('font-weight: bold; color: #495057; margin-top: 10px;')
        self.serie_input = QLineEdit()
        self.serie_input.setMinimumHeight(35)
        self.serie_input.setStyleSheet('\n            QLineEdit {\n                border: 1px solid #ced4da;\n                border-radius: 4px;\n                padding: 8px;\n                font-size: 14px;\n                background-color: white;\n            }\n            QLineEdit:focus {\n                border-color: #007bff;\n            }\n        ')
        serie_layout.addWidget(serie_label)
        serie_layout.addWidget(self.serie_input)
        secao_layout.addLayout(serie_layout)
        valor_layout = QVBoxLayout()
        valor_label = QLabel('Valor do Servi├ºo (opcional):')
        valor_label.setStyleSheet('font-weight: bold; color: #495057; margin-top: 10px;')
        self.valor_input = QLineEdit()
        self.valor_input.setPlaceholderText('Ex: 150,00 ou 150.50')
        self.valor_input.setMinimumHeight(35)
        self.valor_input.setStyleSheet('\n            QLineEdit {\n                border: 1px solid #ced4da;\n                border-radius: 4px;\n                padding: 8px;\n                font-size: 14px;\n                background-color: white;\n            }\n            QLineEdit:focus {\n                border-color: #28a745;\n                background-color: #f8fff9;\n            }\n        ')
        self.valor_input.textChanged.connect(self.validar_valor_tempo_real)
        valor_dica = QLabel('Deixe em branco se o valor ser├í definido ap├│s o diagn├│stico')
        valor_dica.setStyleSheet('\n            QLabel {\n                color: #6c757d;\n                font-size: 12px;\n                font-style: italic;\n                margin-top: 5px;\n            }\n        ')
        valor_layout.addWidget(valor_label)
        valor_layout.addWidget(self.valor_input)
        valor_layout.addWidget(valor_dica)
        secao_layout.addLayout(valor_layout)
        layout.addWidget(secao_frame)
    def criar_secao_diagnostico(self, layout):
        '''Cria se├º├úo com diagn├│stico e fotos'''
        secao_frame = QFrame()
        secao_frame.setStyleSheet('\n            QFrame {\n                background-color: #f8f9fa;\n                border: 1px solid #dee2e6;\n                border-radius: 8px;\n                padding: 15px;\n            }\n        ')
        secao_layout = QVBoxLayout(secao_frame)
        titulo = QLabel('Diagn├│stico e Documenta├º├úo')
        titulo.setStyleSheet('\n            QLabel {\n                font-size: 16px;\n                font-weight: bold;\n                color: #2c3e50;\n                margin-bottom: 10px;\n            }\n        ')
        secao_layout.addWidget(titulo)
        problema_label = QLabel('Problema Relatado:')
        problema_label.setStyleSheet('font-weight: bold; color: #495057;')
        self.problema_text = QTextEdit()
        self.problema_text.setPlaceholderText('Descreva detalhadamente o problema relatado pelo cliente...')
        self.problema_text.setTabChangesFocus(True)
        self.problema_text.setMaximumHeight(100)
        self.problema_text.setStyleSheet('\n            QTextEdit {\n                border: 1px solid #ced4da;\n                border-radius: 4px;\n                padding: 8px;\n                font-size: 14px;\n                background-color: white;\n            }\n            QTextEdit:focus {\n                border-color: #007bff;\n            }\n        ')
        secao_layout.addWidget(problema_label)
        secao_layout.addWidget(self.problema_text)
        diagnostico_label = QLabel('Diagn├│stico Inicial:')
        diagnostico_label.setStyleSheet('font-weight: bold; color: #495057; margin-top: 10px;')
        self.diagnostico_text = QTextEdit()
        self.diagnostico_text.setPlaceholderText('Diagn├│stico inicial do t├®cnico...')
        self.diagnostico_text.setTabChangesFocus(True)
        self.diagnostico_text.setMaximumHeight(100)
        self.diagnostico_text.setStyleSheet('\n            QTextEdit {\n                border: 1px solid #ced4da;\n                border-radius: 4px;\n                padding: 8px;\n                font-size: 14px;\n                background-color: white;\n            }\n            QTextEdit:focus {\n                border-color: #007bff;\n            }\n        ')
        secao_layout.addWidget(diagnostico_label)
        secao_layout.addWidget(self.diagnostico_text)
        fotos_layout = QHBoxLayout()
        self.fotos_label = QLabel('Fotos: 0 selecionadas')
        self.fotos_label.setStyleSheet('font-weight: bold; color: #495057; margin-top: 10px;')
        add_foto_btn = QPushButton('+ Adicionar Fotos')
        add_foto_btn.setStyleSheet('\n            QPushButton {\n                background-color: #007bff;\n                color: white;\n                border: none;\n                padding: 8px 16px;\n                border-radius: 4px;\n                font-weight: bold;\n                font-size: 14px;\n                min-width: 140px;\n            }\n            QPushButton:hover {\n                background-color: #0056b3;\n            }\n        ')
        add_foto_btn.clicked.connect(self.adicionar_fotos)
        fotos_layout.addWidget(self.fotos_label)
        fotos_layout.addStretch()
        fotos_layout.addWidget(add_foto_btn)
        secao_layout.addLayout(fotos_layout)
        layout.addWidget(secao_frame)
    def criar_botoes_acao(self, layout):
        '''Cria bot├Áes de a├º├úo padronizados'''
        layout.addSpacing(10)
        buttons_layout = QHBoxLayout()
        salvar_btn = QPushButton('Salvar Ordem de Servi├ºo')
        salvar_btn.setStyleSheet('\n            QPushButton {\n                background-color: #28a745;\n                color: white;\n                border: none;\n                padding: 12px 25px;\n                border-radius: 5px;\n                font-weight: bold;\n                font-size: 16px;\n                min-width: 200px;\n            }\n            QPushButton:hover {\n                background-color: #218838;\n            }\n        ')
        salvar_btn.clicked.connect(self.salvar_os)
        cancelar_btn = QPushButton('Cancelar')
        cancelar_btn.setStyleSheet('\n            QPushButton {\n                background-color: #6c757d;\n                color: white;\n                border: none;\n                padding: 12px 25px;\n                border-radius: 5px;\n                font-weight: bold;\n                font-size: 16px;\n                min-width: 120px;\n            }\n            QPushButton:hover {\n                background-color: #545b62;\n            }\n        ')
        cancelar_btn.clicked.connect(self.reject)
        buttons_layout.addStretch()
        buttons_layout.addWidget(salvar_btn)
        buttons_layout.addWidget(cancelar_btn)
        layout.addLayout(buttons_layout)
    def filtrar_clientes(self):
        '''Filtra clientes com UX melhorada - auto-sele├º├úo e feedback visual'''
        if not hasattr(self, 'todos_clientes') or getattr(self, '_updating_from_combo', False):
            return
        texto_busca = self.busca_cliente_input.text().strip()
        texto_busca_lower = texto_busca.lower()
        if hasattr(self, 'cliente_detalhes_frame'):
            self.ocultar_detalhes_cliente()
        self._updating_from_search = True
        if hasattr(self, '_combo_connected') and self._combo_connected:
            try:
                self.cliente_combo.currentTextChanged.disconnect()
            except TypeError:
                pass
        self.cliente_combo.clear()
        if not texto_busca:
            for id, nome, telefone in self.todos_clientes:
                self.cliente_combo.addItem(f'{nome} - {telefone}', id)
            self.busca_cliente_input.setPlaceholderText('Digite para buscar cliente...')
            self._atualizar_feedback_busca('normal', f'{len(self.todos_clientes)} clientes dispon├¡veis')
        else:
            clientes_filtrados = []
            for id, nome, telefone in self.todos_clientes:
                if texto_busca_lower in nome.lower() or texto_busca_lower in telefone.lower():
                    clientes_filtrados.append((id, nome, telefone))
                    self.cliente_combo.addItem(f'{nome} - {telefone}', id)
            if len(clientes_filtrados) == 1:
                self.cliente_combo.setCurrentIndex(0)
                self._atualizar_feedback_busca('sucesso', f'{clientes_filtrados[0][1]} selecionado')
            elif len(clientes_filtrados) > 1:
                self._atualizar_feedback_busca('multiplos', f'{len(clientes_filtrados)} clientes encontrados')
            else:
                self._atualizar_feedback_busca('vazio', 'Nenhum cliente encontrado')
        try:
            self.cliente_combo.currentTextChanged.connect(self._on_combo_changed)
            self._combo_connected = True
        except TypeError:
            pass
        self._updating_from_search = False
    def _atualizar_feedback_busca(self, tipo, mensagem):
        '''Atualiza feedback visual da busca sem CSS complexo'''
        if tipo == 'sucesso':
            self.busca_cliente_input.setPlaceholderText(mensagem)
            self.busca_cliente_input.setStyleSheet('\n                QLineEdit {\n                    border: 2px solid #28a745;\n                    border-radius: 4px;\n                    padding: 8px;\n                    font-size: 14px;\n                    background-color: #f8fff9;\n                }\n            ')
            return
        if tipo == 'multiplos':
            self.busca_cliente_input.setPlaceholderText(mensagem)
            self.busca_cliente_input.setStyleSheet('\n                QLineEdit {\n                    border: 2px solid #ffc107;\n                    border-radius: 4px;\n                    padding: 8px;\n                    font-size: 14px;\n                    background-color: #fffdf0;\n                }\n            ')
            return
        if tipo == 'vazio':
            self.busca_cliente_input.setPlaceholderText(mensagem)
            self.busca_cliente_input.setStyleSheet('\n                QLineEdit {\n                    border: 2px solid #dc3545;\n                    border-radius: 4px;\n                    padding: 8px;\n                    font-size: 14px;\n                    background-color: #fff5f5;\n                }\n            ')
            return
        self.busca_cliente_input.setPlaceholderText(mensagem)
        self.busca_cliente_input.setStyleSheet('\n                QLineEdit {\n                    border: 1px solid #ced4da;\n                    border-radius: 4px;\n                    padding: 8px;\n                    font-size: 14px;\n                    background-color: white;\n                }\n                QLineEdit:focus {\n                    border-color: #007bff;\n                }\n            ')
    def _on_combo_changed(self):
        '''Sincroniza campo de busca quando combo muda (UX MELHORADA)'''
        if self.cliente_combo.currentData():
            if not getattr(self, '_updating_from_search', False):
                texto_combo = self.cliente_combo.currentText()
                if ' - ' in texto_combo:
                    nome_cliente = texto_combo.split(' - ')[0]
                    self._updating_from_combo = True
                    self.busca_cliente_input.setText(nome_cliente)
                    self._atualizar_feedback_busca('sucesso', f'{nome_cliente} selecionado')
                    if hasattr(self, 'cliente_map') and texto_combo in self.cliente_map:
                        self.mostrar_detalhes_cliente(self.cliente_map[texto_combo])
                    self._updating_from_combo = False
    def validar_valor_tempo_real(self, texto):
        '''
        ­ƒåò NOVO: Valida├º├úo em tempo real do campo de valor
        Aceita: 150, 150.50, 150,50
        '''
        if not texto.strip():
            self.valor_input.setStyleSheet('\n                QLineEdit {\n                    border: 1px solid #ced4da;\n                    border-radius: 4px;\n                    padding: 8px;\n                    font-size: 14px;\n                    background-color: white;\n                }\n                QLineEdit:focus {\n                    border-color: #28a745;\n                    background-color: #f8fff9;\n                }\n            ')
            return
        texto_limpo = texto.strip().replace(',', '.')
        try:
            valor = float(texto_limpo)
            if valor < 0:
                self.valor_input.setStyleSheet('\n                    QLineEdit {\n                        border: 2px solid #dc3545;\n                        border-radius: 4px;\n                        padding: 8px;\n                        font-size: 14px;\n                        background-color: #fff5f5;\n                    }\n                ')
                return
            self.valor_input.setStyleSheet('\n                    QLineEdit {\n                        border: 2px solid #28a745;\n                        border-radius: 4px;\n                        padding: 8px;\n                        font-size: 14px;\n                        background-color: #f8fff9;\n                    }\n                ')
            return
        except ValueError:
            self.valor_input.setStyleSheet('\n                QLineEdit {\n                    border: 2px solid #dc3545;\n                    border-radius: 4px;\n                    padding: 8px;\n                    font-size: 14px;\n                    background-color: #fff5f5;\n                }\n            ')
# WARNING: Decompyle incomplete
