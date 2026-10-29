from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit, QMessageBox, QComboBox, QFileDialog, QScrollArea, QWidget, QFrame, QCompleter)
from PyQt5.QtCore import Qt, QStringListModel
from PyQt5.QtGui import QFont
import sqlite3
import os
import shutil
from datetime import datetime
from .device_completer import DeviceCompleter
class EditServiceOrderDialog(QDialog):
    def __init__(self, os_id, user_id, parent=None):
        super().__init__(parent)
        self.os_id = os_id
        self.user_id = user_id
        self.fotos_adicionadas = []
        self.fotos_removidas = []
        self.device_completer = DeviceCompleter(user_id)
        self.is_admin = parent.is_admin if hasattr(parent, 'is_admin') else False
        self.setWindowTitle('Editar Ordem de Servi├ºo')
        self.setModal(True)
        self.setMinimumSize(1000, 700)
        self.showMaximized()
        self.setup_ui()
        self.carregar_os()
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
        titulo = QLabel('Editar Ordem de Servi├ºo')
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
    def carregar_os(self):
        try:
            conn = sqlite3.connect('app/database/service_orders.db')
            cursor = conn.cursor()
            cursor.execute('\n                SELECT id, name, phone FROM clients\n                WHERE user_id = ?\n                ORDER BY name\n            ', (self.user_id,))
            self.todos_clientes = cursor.fetchall()
            self.clientes = {}
            for client_id, name, phone in self.todos_clientes:
                display_name = f'{name} - {phone}' if phone else name
                self.clientes[display_name] = client_id
                self.cliente_combo.addItem(display_name)
            if not getattr(self, '_combo_connected', False):
                self.cliente_combo.currentTextChanged.connect(self._on_combo_changed)
                self._combo_connected = True
            self._atualizar_feedback_busca('normal', f'{len(self.todos_clientes)} clientes dispon├¡veis')
            self.setup_autocomplete()
            cursor.execute('\n                SELECT client_id, device_type, brand, model,\n                       reported_issue, diagnosis\n                FROM service_orders\n                WHERE id = ? AND user_id = ?\n            ', (self.os_id, self.user_id))
            os = cursor.fetchone()
            if os:
                for display_name, client_id in self.clientes.items():
                    if not client_id == os[0]:
                        continue
                    self.cliente_combo.setCurrentText(display_name)
                    if hasattr(self, 'busca_cliente_input'):
                        nome_cliente = display_name.split(' - ')[0] if ' - ' in display_name else display_name
                        self.busca_cliente_input.setText(nome_cliente)
                        self._atualizar_feedback_busca('sucesso', f'Ô£ô {nome_cliente} selecionado')
                    break
                self.tipo_combo.setCurrentText(os[1])
                self.marca_input.setText(os[2])
                self.modelo_input.setText(os[3])
                self.problema_text.setText(os[4])
                self.diagnostico_text.setText(os[5] or '')
                cursor.execute('\n                    SELECT id, photo_path FROM service_order_photos\n                    WHERE service_order_id = ?\n                ', (self.os_id,))
                for photo_id, photo_path in cursor.fetchall():
                    self.adicionar_foto_existente(photo_id, photo_path)
                self.device_completer.setup_completers(self.marca_input, self.modelo_input, self.tipo_combo.currentText())
                self.tipo_combo.currentTextChanged.connect(self.atualizar_estatisticas)
                self.marca_input.textChanged.connect(self.atualizar_estatisticas)
                self.modelo_input.textChanged.connect(self.atualizar_estatisticas)
                self.atualizar_estatisticas()
            else:
                QMessageBox.critical(self, 'Erro', 'Ordem de servi├ºo n├úo encontrada!')
                self.reject()
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao carregar OS: {str(e)}')
        finally:
            if conn:
                conn.close()
    def adicionar_foto_existente(self, photo_id, photo_path):
        foto_layout = QHBoxLayout()
        foto_label = QLabel(os.path.basename(photo_path))
        foto_layout.addWidget(foto_label)
        btn_remover = QPushButton('Remover')
        btn_remover.setStyleSheet('\n            QPushButton {\n                background-color: #d9534f;\n                color: white;\n                border: none;\n                padding: 3px 10px;\n                border-radius: 3px;\n            }\n            QPushButton:hover {\n                background-color: #c9302c;\n            }\n        ')
        btn_remover.clicked.connect((lambda: self.remover_foto(photo_id, foto_layout)))
        foto_layout.addWidget(btn_remover)
        self.fotos_layout.addLayout(foto_layout)
    def adicionar_foto(self):
        arquivo, _ = QFileDialog.getOpenFileName(self, 'Selecionar Foto', '', 'Imagens (*.png *.jpg *.jpeg)')
        if arquivo:
            foto_layout = QHBoxLayout()
            foto_label = QLabel(os.path.basename(arquivo))
            foto_layout.addWidget(foto_label)
            btn_remover = QPushButton('Remover')
            btn_remover.setStyleSheet('\n                QPushButton {\n                    background-color: #d9534f;\n                    color: white;\n                    border: none;\n                    padding: 3px 10px;\n                    border-radius: 3px;\n                }\n                QPushButton:hover {\n                    background-color: #c9302c;\n                }\n            ')
            btn_remover.clicked.connect((lambda: self.remover_foto_nova(arquivo, foto_layout)))
            foto_layout.addWidget(btn_remover)
            self.fotos_layout.addLayout(foto_layout)
            self.fotos_adicionadas.append(arquivo)
    def remover_foto(self, photo_id, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.fotos_removidas.append(photo_id)
    def remover_foto_nova(self, arquivo, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.fotos_adicionadas.remove(arquivo)
    def salvar_os(self):
        cliente_selecionado = None
        if self.cliente_combo.currentText() and self.cliente_combo.currentText() in self.clientes:
            cliente_selecionado = self.clientes[self.cliente_combo.currentText()]
        elif hasattr(self, 'cliente_map') and self.busca_cliente_input.text().strip():
            texto_busca = self.busca_cliente_input.text().strip()
            for display_text, data in self.cliente_map.items():
                if texto_busca != display_text and texto_busca not in display_text:
                    if not data['nome'].lower() == texto_busca.lower():
                        continue
                cliente_selecionado = data['id']
                if display_text not in self.clientes:
                    self.clientes[display_text] = data['id']
                self.cliente_combo.setCurrentText(display_text)
                break
        if cliente_selecionado is None:
            QMessageBox.warning(self, 'Erro', 'Selecione um cliente v├ílido!')
            return
        if not self.marca_input.text().strip():
            QMessageBox.warning(self, 'Erro', 'Informe a marca do dispositivo!')
            return
        if not self.modelo_input.text().strip():
            QMessageBox.warning(self, 'Erro', 'Informe o modelo do dispositivo!')
            return
        if not self.problema_text.toPlainText().strip():
            QMessageBox.warning(self, 'Erro', 'Descreva o problema relatado!')
            return
        try:
            conn = sqlite3.connect('app/database/service_orders.db')
            cursor = conn.cursor()
            cursor.execute('\n                UPDATE service_orders\n                SET client_id = ?, device_type = ?, brand = ?,\n                    model = ?, reported_issue = ?, diagnosis = ?\n                WHERE id = ? AND user_id = ?\n            ', (cliente_selecionado, self.tipo_combo.currentText(), self.marca_input.text().strip(), self.modelo_input.text().strip(), self.problema_text.toPlainText().strip(), self.diagnostico_text.toPlainText().strip(), self.os_id, self.user_id))
            for photo_id in self.fotos_removidas:
                cursor.execute('\n                    SELECT photo_path FROM service_order_photos\n                    WHERE id = ?\n                ', (photo_id,))
                photo_path = cursor.fetchone()[0]
                if os.path.exists(photo_path):
                    os.remove(photo_path)
                cursor.execute('\n                    DELETE FROM service_order_photos\n                    WHERE id = ?\n                ', (photo_id,))
            for arquivo in self.fotos_adicionadas:
                os.makedirs('app/data/fotos', exist_ok=True)
                nome_arquivo = f'{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.path.basename(arquivo)}'
                destino = os.path.join('app/data/fotos', nome_arquivo)
                shutil.copy2(arquivo, destino)
                cursor.execute('\n                    INSERT INTO service_order_photos (service_order_id, photo_path)\n                    VALUES (?, ?)\n                ', (self.os_id, destino))
            conn.commit()
            QMessageBox.information(self, 'Sucesso', 'Ordem de servi├ºo atualizada com sucesso!')
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao atualizar OS: {str(e)}')
        if conn:
            conn.close()
    def excluir_os(self):
        conn = None
        try:
            resposta = QMessageBox.question(self, 'Confirma├º├úo', 'Tem certeza que deseja excluir esta ordem de servi├ºo?', QMessageBox.Yes | QMessageBox.No)
            if resposta == QMessageBox.Yes:
                conn = sqlite3.connect('app/database/service_orders.db')
                cursor = conn.cursor()
                cursor.execute('\n                    SELECT photo_path FROM service_order_photos\n                    WHERE service_order_id = ?\n                ', (self.os_id,))
                for (photo_path,) in cursor.fetchall():
                    if os.path.exists(photo_path):
                        os.remove(photo_path)
                cursor.execute('\n                    DELETE FROM service_order_photos\n                    WHERE service_order_id = ?\n                ', (self.os_id,))
                cursor.execute('\n                    DELETE FROM service_orders\n                    WHERE id = ? AND user_id = ?\n                ', (self.os_id, self.user_id))
                conn.commit()
                QMessageBox.information(self, 'Sucesso', 'Ordem de servi├ºo exclu├¡da com sucesso!')
                self.accept()
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao excluir OS: {str(e)}')
        if conn:
            conn.close()
    def atualizar_estatisticas(self):
        '''Atualiza as estat├¡sticas do dispositivo'''
        stats = self.device_completer.get_device_stats(marca=self.marca_input.text().strip(), modelo=self.modelo_input.text().strip(), tipo_dispositivo=self.tipo_combo.currentText())
        if stats:
            html = f'\n                <b>Estat├¡sticas do Dispositivo:</b><br>\n                Total de OS: {stats['total']}<br>\n                Conclu├¡das com Sucesso: {stats['sucesso']} ({stats['taxa_sucesso']:.1f}%)<br>\n                Sem Solu├º├úo: {stats['sem_solucao']} ({stats['taxa_falha']:.1f}%)<br>\n            '
            self.stats_label.setText(html)
            return
        self.stats_label.setText('Nenhuma estat├¡stica dispon├¡vel para este dispositivo.')
    def criar_secao_cliente(self, layout):
        '''Cria se├º├úo de sele├º├úo de cliente com busca melhorada (ATUALIZADO)'''
        secao_frame = QFrame()
        secao_frame.setStyleSheet('\n            QFrame {\n                background-color: #f8f9fa;\n                border: 1px solid #dee2e6;\n                border-radius: 8px;\n                padding: 15px;\n            }\n        ')
        secao_layout = QVBoxLayout(secao_frame)
        titulo = QLabel('­ƒæñ Sele├º├úo de Cliente')
        titulo.setStyleSheet('\n            QLabel {\n                font-size: 16px;\n                font-weight: bold;\n                color: #2c3e50;\n                margin-bottom: 10px;\n            }\n        ')
        secao_layout.addWidget(titulo)
        cliente_layout = QHBoxLayout()
        cliente_label = QLabel('Cliente:')
        cliente_label.setMinimumWidth(80)
        cliente_label.setStyleSheet('font-weight: bold; color: #495057;')
        self.busca_cliente_input = QLineEdit()
        self.busca_cliente_input.setPlaceholderText('Digite para buscar cliente...')
        self.busca_cliente_input.setMinimumHeight(35)
        self.busca_cliente_input.setStyleSheet('\n            QLineEdit {\n                border: 1px solid #ced4da;\n                border-radius: 4px;\n                padding: 8px;\n                font-size: 14px;\n                background-color: white;\n            }\n            QLineEdit:focus {\n                border-color: #007bff;\n            }\n        ')
        self.busca_cliente_input.textChanged.connect(self.filtrar_clientes)
        self.setup_autocomplete()
        self._combo_connected = False
        self.cliente_combo = QComboBox()
        self.cliente_combo.setMinimumWidth(300)
        self.cliente_combo.setMinimumHeight(35)
        self.cliente_combo.setStyleSheet('\n            QComboBox {\n                border: 1px solid #ced4da;\n                border-radius: 4px;\n                padding: 8px;\n                font-size: 14px;\n                background-color: white;\n                color: #2c3e50;\n            }\n            QComboBox:focus {\n                border-color: #007bff;\n            }\n            QComboBox QAbstractItemView {\n                background-color: white;\n                border: 1px solid #ced4da;\n                selection-background-color: #007bff;\n                selection-color: white;\n                color: #2c3e50;\n            }\n        ')
        cliente_layout.addWidget(cliente_label)
        cliente_layout.addWidget(self.busca_cliente_input)
        cliente_layout.addWidget(self.cliente_combo)
        cliente_layout.addStretch()
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
        titulo = QLabel('­ƒô▒ Informa├º├Áes do Dispositivo')
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
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet('\n            QLabel {\n                background-color: #e3f2fd;\n                padding: 10px;\n                border-radius: 5px;\n                border: 1px solid #bbdefb;\n                margin-top: 10px;\n                color: #1565c0;\n            }\n        ')
        secao_layout.addWidget(self.stats_label)
        layout.addWidget(secao_frame)
    def criar_secao_diagnostico(self, layout):
        '''Cria se├º├úo com diagn├│stico e fotos'''
        secao_frame = QFrame()
        secao_frame.setStyleSheet('\n            QFrame {\n                background-color: #f8f9fa;\n                border: 1px solid #dee2e6;\n                border-radius: 8px;\n                padding: 15px;\n            }\n        ')
        secao_layout = QVBoxLayout(secao_frame)
        titulo = QLabel('­ƒöº Diagn├│stico e Documenta├º├úo')
        titulo.setStyleSheet('\n            QLabel {\n                font-size: 16px;\n                font-weight: bold;\n                color: #2c3e50;\n                margin-bottom: 10px;\n            }\n        ')
        secao_layout.addWidget(titulo)
        problema_label = QLabel('Problema Relatado:')
        problema_label.setStyleSheet('font-weight: bold; color: #495057;')
        self.problema_text = QTextEdit()
        self.problema_text.setTabChangesFocus(True)
        self.problema_text.setMaximumHeight(100)
        self.problema_text.setStyleSheet('\n            QTextEdit {\n                border: 1px solid #ced4da;\n                border-radius: 4px;\n                padding: 8px;\n                font-size: 14px;\n                background-color: white;\n            }\n            QTextEdit:focus {\n                border-color: #007bff;\n            }\n        ')
        secao_layout.addWidget(problema_label)
        secao_layout.addWidget(self.problema_text)
        diagnostico_label = QLabel('Diagn├│stico:')
        diagnostico_label.setStyleSheet('font-weight: bold; color: #495057; margin-top: 10px;')
        self.diagnostico_text = QTextEdit()
        self.diagnostico_text.setTabChangesFocus(True)
        self.diagnostico_text.setMaximumHeight(100)
        self.diagnostico_text.setStyleSheet('\n            QTextEdit {\n                border: 1px solid #ced4da;\n                border-radius: 4px;\n                padding: 8px;\n                font-size: 14px;\n                background-color: white;\n            }\n            QTextEdit:focus {\n                border-color: #007bff;\n            }\n        ')
        secao_layout.addWidget(diagnostico_label)
        secao_layout.addWidget(self.diagnostico_text)
        fotos_label = QLabel('­ƒôÀ Fotos:')
        fotos_label.setStyleSheet('font-weight: bold; color: #495057; margin-top: 10px;')
        secao_layout.addWidget(fotos_label)
        self.fotos_layout = QVBoxLayout()
        secao_layout.addLayout(self.fotos_layout)
        add_foto_layout = QHBoxLayout()
        add_foto_btn = QPushButton('+ Adicionar Foto')
        add_foto_btn.setStyleSheet('\n            QPushButton {\n                background-color: #007bff;\n                color: white;\n                border: none;\n                padding: 8px 16px;\n                border-radius: 4px;\n                font-weight: bold;\n                font-size: 14px;\n                min-width: 140px;\n            }\n            QPushButton:hover {\n                background-color: #0056b3;\n            }\n        ')
        add_foto_btn.clicked.connect(self.adicionar_foto)
        add_foto_layout.addWidget(add_foto_btn)
        add_foto_layout.addStretch()
        secao_layout.addLayout(add_foto_layout)
        layout.addWidget(secao_frame)
    def criar_botoes_acao(self, layout):
        '''Cria bot├Áes de a├º├úo padronizados (espec├¡ficos do edit)'''
        layout.addSpacing(10)
        buttons_layout = QHBoxLayout()
        salvar_btn = QPushButton('­ƒÆ¥ Salvar Altera├º├Áes')
        salvar_btn.setStyleSheet('\n            QPushButton {\n                background-color: #28a745;\n                color: white;\n                border: none;\n                padding: 12px 25px;\n                border-radius: 5px;\n                font-weight: bold;\n                font-size: 16px;\n                min-width: 180px;\n            }\n            QPushButton:hover {\n                background-color: #218838;\n            }\n        ')
        salvar_btn.clicked.connect(self.salvar_os)
        excluir_btn = QPushButton('­ƒùæ´©Å Excluir OS')
        excluir_btn.setStyleSheet('\n            QPushButton {\n                background-color: #dc3545;\n                color: white;\n                border: none;\n                padding: 12px 25px;\n                border-radius: 5px;\n                font-weight: bold;\n                font-size: 16px;\n                min-width: 120px;\n            }\n            QPushButton:hover {\n                background-color: #c82333;\n            }\n        ')
        excluir_btn.clicked.connect(self.excluir_os)
        cancelar_btn = QPushButton('ÔØî Cancelar')
        cancelar_btn.setStyleSheet('\n            QPushButton {\n                background-color: #6c757d;\n                color: white;\n                border: none;\n                padding: 12px 25px;\n                border-radius: 5px;\n                font-weight: bold;\n                font-size: 16px;\n                min-width: 120px;\n            }\n            QPushButton:hover {\n                background-color: #545b62;\n            }\n        ')
        cancelar_btn.clicked.connect(self.reject)
        buttons_layout.addStretch()
        buttons_layout.addWidget(salvar_btn)
        buttons_layout.addWidget(excluir_btn)
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
        self.clientes.clear()
        if not texto_busca:
            for id, nome, telefone in self.todos_clientes:
                display_name = f'{nome} - {telefone}' if telefone else nome
                self.clientes[display_name] = id
                self.cliente_combo.addItem(display_name)
            self.busca_cliente_input.setPlaceholderText('Digite para buscar cliente...')
            self._atualizar_feedback_busca('normal', f'{len(self.todos_clientes)} clientes dispon├¡veis')
        else:
            clientes_filtrados = []
            for id, nome, telefone in self.todos_clientes:
                if texto_busca_lower in nome.lower() or telefone and texto_busca_lower in telefone.lower():
                    display_name = f'{nome} - {telefone}' if telefone else nome
                    clientes_filtrados.append((id, nome, telefone))
                    self.clientes[display_name] = id
                    self.cliente_combo.addItem(display_name)
            if len(clientes_filtrados) == 1:
                self.cliente_combo.setCurrentIndex(0)
                self._atualizar_feedback_busca('sucesso', f'Ô£ô {clientes_filtrados[0][1]} selecionado')
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
        if self.cliente_combo.currentText():
            if not getattr(self, '_updating_from_search', False):
                texto_combo = self.cliente_combo.currentText()
                if ' - ' in texto_combo:
                    nome_cliente = texto_combo.split(' - ')[0]
                    self._updating_from_combo = True
                    self.busca_cliente_input.setText(nome_cliente)
                    self._atualizar_feedback_busca('sucesso', f'Ô£ô {nome_cliente} selecionado')
                    if hasattr(self, 'cliente_map') and texto_combo in self.cliente_map:
                        self.mostrar_detalhes_cliente(self.cliente_map[texto_combo])
                    self._updating_from_combo = False
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
            self._atualizar_feedback_busca('sucesso', f'Ô£ô {cliente_data['nome']} selecionado')
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
                detalhes = f'­ƒô▒ {telefone or 'N├úo informado'}'
                if email:
                    detalhes += f' | Ô£ë´©Å {email}'
                if endereco:
                    detalhes += f' | ­ƒôì {endereco}'
                self.cliente_detalhes_label.setText(f'Ô£à Cliente: {nome}\n{detalhes}')
                self.cliente_detalhes_frame.setVisible(True)
        except Exception as e:
            print(f'Erro ao carregar detalhes do cliente: {e}')
        if conn:
            conn.close()
    def ocultar_detalhes_cliente(self):
        '''Oculta ├írea de detalhes do cliente (NOVA FUNCIONALIDADE)'''
        self.cliente_detalhes_frame.setVisible(False)
