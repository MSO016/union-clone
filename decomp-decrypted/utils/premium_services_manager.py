import pymysql
import webbrowser
from typing import (Optional, Dict, List)
from PyQt5.QtWidgets import (QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton, QTextEdit, QHBoxLayout, QScrollArea, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from app.utils._app_cfg import db_config
try:
    from app.utils.web_view_widget import (WebViewWidget, is_webengine_available, get_web_view_manager)
    NAVEGADOR_INTERNO_DISPONIVEL = True
except ImportError:
    NAVEGADOR_INTERNO_DISPONIVEL = False
    WebViewWidget = None
    is_webengine_available = lambda: False
    get_web_view_manager = lambda: None
class PremiumServicesManager:
    _DB_CONFIG = db_config(cursorclass=pymysql.cursors.DictCursor)
    def __init__(self):
        self._cache = {}
        self._cache_timeout = 300
    def _conectar_db(self) -> Optional[pymysql.Connection]:
        try:
            conn = pymysql.connect(**self._DB_CONFIG, **{'ssl': {'ca': None}, 'ssl_verify_cert': False})
            return conn
        except Exception as e:
            print('ÔÜá´©Å Servi├ºo temporariamente indispon├¡vel')
    def buscar_servico_premium(self, titulo: str) -> Optional[Dict]:
        cache_key = f'premium_{titulo}'
        if cache_key in self._cache:
            print(f"Ô£à Servi├ºo '{titulo}' carregado do cache")
            return self._cache[cache_key]
        conn = self._conectar_db()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute('\n                SELECT \n                    id, titulo, tipo, link, descricao, ativo,\n                    data_criacao, data_modificacao\n                FROM conteudos_dinamicos \n                WHERE titulo = %s\n                LIMIT 1\n            ', (titulo,))
            resultado = cursor.fetchone()
            if resultado:
                self._cache[cache_key] = resultado
                status_ativo = resultado.get('ativo')
                print(f"Ô£à Servi├ºo '{titulo}' encontrado - Status: {status_ativo} (tipo: {type(status_ativo).__name__})")
            else:
                print(f"ÔÜá´©Å Servi├ºo '{titulo}' n├úo encontrado no banco de dados")
            cursor.close()
            conn.close()
            return resultado
        except Exception as e:
            print('ÔÜá´©Å Erro ao consultar servi├ºo')
            if conn:
                conn.close()
    def buscar_servico_premium_por_id(self, id_servico: int) -> Optional[Dict]:
        cache_key = f'premium_id_{id_servico}'
        if cache_key in self._cache:
            print(f'Ô£à Servi├ºo ID {id_servico} carregado do cache')
            return self._cache[cache_key]
        conn = self._conectar_db()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute('\n                SELECT \n                    id, titulo, tipo, link, descricao, ativo,\n                    data_criacao, data_modificacao\n                FROM conteudos_dinamicos \n                WHERE id = %s\n                LIMIT 1\n            ', (id_servico,))
            resultado = cursor.fetchone()
            if resultado:
                self._cache[cache_key] = resultado
                status_ativo = resultado.get('ativo')
                titulo_encontrado = resultado.get('titulo', 'N/A')
                print(f"Ô£à Servi├ºo ID {id_servico} encontrado - T├¡tulo: '{titulo_encontrado}' - Status: {status_ativo}")
            else:
                print(f'ÔÜá´©Å Servi├ºo ID {id_servico} n├úo encontrado no banco de dados')
            cursor.close()
            conn.close()
            return resultado
        except Exception as e:
            print('ÔÜá´©Å Erro ao consultar servi├ºo por ID')
            if conn:
                conn.close()
    def criar_botao_premium_com_indicador(self, identificador: str, callback, parent=None, cor_personalizada=None) -> QPushButton:
        servico = None
        titulo_final = identificador
        if identificador.startswith('ID:'):
            try:
                id_servico = int(identificador.replace('ID:', '').strip())
                servico = self.buscar_servico_premium_por_id(id_servico)
                if servico:
                    titulo_final = servico.get('titulo', identificador)
                    print(f"Ô£à Bot├úo criado com t├¡tulo din├ómico do banco: '{titulo_final}'")
            except ValueError:
                print(f'ÔÜá´©Å ID inv├ílido: {identificador}')
        else:
            servico = self.buscar_servico_premium(identificador)
            titulo_final = identificador
        if servico:
            ativo_value = servico.get('ativo')
            esta_ativo = ativo_value in (1, '1', True, 'true', 'True', 'TRUE')
            print(f'­ƒöì Debug ativo: valor={ativo_value}, tipo={type(ativo_value).__name__}, resultado={esta_ativo}')
            if servico.get('titulo'):
                titulo_final = servico.get('titulo')
        else:
            esta_ativo = False
            print(f"ÔÜá´©Å Servi├ºo '{identificador}' n├úo encontrado - marcando como inativo")
        indicador = '­ƒƒó' if esta_ativo else '­ƒö┤'
        btn_text = f'{indicador} {titulo_final}'
        btn = QPushButton(btn_text)
        btn.setProperty('servico_titulo', titulo_final)
        btn.setProperty('servico_ativo', esta_ativo)
        if esta_ativo:
            btn.setToolTip('Ô£à Servi├ºo ativo e dispon├¡vel\nClique para mais informa├º├Áes')
        else:
            btn.setToolTip('­ƒö┤ Servi├ºo temporariamente indispon├¡vel')
        btn.clicked.connect(callback)
        if cor_personalizada == 'laranja':
            cor_principal_1 = '#ff6f00'
            cor_principal_2 = '#ff8f00'
            cor_hover_1 = '#e65100'
            cor_hover_2 = '#ff6f00'
            cor_pressed = '#bf360c'
            cor_borda = '#e65100'
        else:
            cor_principal_1 = '#8e44ad'
            cor_principal_2 = '#9b59b6'
            cor_hover_1 = '#7d3c98'
            cor_hover_2 = '#8e44ad'
            cor_pressed = '#6c3483'
            cor_borda = '#7d3c98'
        if esta_ativo:
            btn.setStyleSheet(f'\n                QPushButton {{\n                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, \n                                stop:0 {cor_principal_1}, stop:1 {cor_principal_2});\n                    color: white;\n                    font-weight: bold;\n                    padding: 8px 16px;\n                    border-radius: 6px;\n                    border: 2px solid {cor_borda};\n                    font-size: 12px;\n                }}\n                QPushButton:hover {{\n                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, \n                                stop:0 {cor_hover_1}, stop:1 {cor_hover_2});\n                    border-color: {cor_pressed};\n                }}\n                QPushButton:pressed {{\n                    background-color: {cor_pressed};\n                    border-color: {cor_pressed};\n                }}\n            ')
            return btn
        btn.setStyleSheet('\n                QPushButton {\n                    background-color: #95a5a6;\n                    color: #ecf0f1;\n                    font-weight: bold;\n                    padding: 8px 16px;\n                    border-radius: 6px;\n                    border: 2px solid #7f8c8d;\n                    font-size: 12px;\n                }\n                QPushButton:hover {\n                    background-color: #7f8c8d;\n                    border-color: #707b7c;\n                }\n            ')
        return btn
    def exibir_dialogo_descricao(self, titulo_servico: str, descricao: str, parent=None) -> bool:
        dialog = QDialog(parent)
        dialog.setWindowTitle(f'­ƒôï {titulo_servico} - Informa├º├Áes Importantes')
        dialog.setMinimumWidth(600)
        dialog.setMaximumWidth(700)
        dialog.setMinimumHeight(400)
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        title_label = QLabel(f'­ƒôï {titulo_servico.upper()}')
        title_label.setStyleSheet('\n            QLabel {\n                font-size: 18px;\n                font-weight: bold;\n                color: #2c3e50;\n                padding: 15px;\n                background-color: #f8f9fa;\n                border-radius: 8px;\n                border-left: 5px solid #8e44ad;\n            }\n        ')
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        warning_label = QLabel('ÔÜá´©Å IMPORTANTE: Leia com aten├º├úo antes de prosseguir!')
        warning_label.setStyleSheet('\n            QLabel {\n                font-size: 14px;\n                font-weight: bold;\n                color: #e67e22;\n                padding: 10px;\n                background-color: #fff3cd;\n                border-radius: 5px;\n                border: 1px solid #ffc107;\n            }\n        ')
        warning_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(warning_label)
        desc_area = QTextEdit()
        desc_area.setReadOnly(True)
        desc_area.setPlainText(descricao)
        desc_area.setStyleSheet('\n            QTextEdit {\n                font-size: 13px;\n                padding: 15px;\n                background-color: white;\n                border: 2px solid #dee2e6;\n                border-radius: 8px;\n                line-height: 1.6;\n            }\n        ')
        font = QFont('Segoe UI', 11)
        desc_area.setFont(font)
        layout.addWidget(desc_area)
        credit_label = QLabel('­ƒÆ░ ATEN├ç├âO: Este servi├ºo requer cr├®ditos no Tech Union Services')
        credit_label.setStyleSheet('\n            QLabel {\n                font-size: 13px;\n                font-weight: bold;\n                color: #8e44ad;\n                padding: 12px;\n                background-color: #f4ecf7;\n                border-radius: 5px;\n                border: 2px solid #8e44ad;\n            }\n        ')
        credit_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(credit_label)
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        btn_cancelar = QPushButton('ÔØî N├úo Li / Cancelar')
        btn_cancelar.setStyleSheet('\n            QPushButton {\n                background-color: #95a5a6;\n                color: white;\n                padding: 12px 24px;\n                border-radius: 6px;\n                font-weight: bold;\n                font-size: 13px;\n                border: none;\n            }\n            QPushButton:hover {\n                background-color: #7f8c8d;\n            }\n        ')
        btn_cancelar.clicked.connect(dialog.reject)
        buttons_layout.addWidget(btn_cancelar)
        btn_confirmar = QPushButton('Ô£à Li e Entendi - Prosseguir')
        btn_confirmar.setStyleSheet('\n            QPushButton {\n                background-color: #27ae60;\n                color: white;\n                padding: 12px 24px;\n                border-radius: 6px;\n                font-weight: bold;\n                font-size: 13px;\n                border: none;\n            }\n            QPushButton:hover {\n                background-color: #229954;\n            }\n            QPushButton:pressed {\n                background-color: #1e8449;\n            }\n        ')
        btn_confirmar.clicked.connect(dialog.accept)
        buttons_layout.addWidget(btn_confirmar)
        layout.addLayout(buttons_layout)
        result = dialog.exec_()
        return result == QDialog.Accepted
    def exibir_aviso_creditos(self, titulo_servico: str, parent=None) -> str:
        dialog = QMessageBox(parent)
        dialog.setWindowTitle(f'­ƒÆ░ {titulo_servico} - Servi├ºo Premium')
        dialog.setIcon(QMessageBox.Information)
        texto_html = f"\n        <h3 style='color: #8e44ad;'>­ƒÆÄ Servi├ºo Premium com Cr├®ditos</h3>\n        <p><b>{titulo_servico}</b> ├® um servi├ºo profissional exclusivo que requer cr├®ditos.</p>\n        \n        <div style='background-color: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #8e44ad;'>\n            <p><b>­ƒÜÇ Por que usar este servi├ºo?</b></p>\n            <ul>\n                <li>Ô£à Solu├º├úo profissional executada remotamente por ID/IMEI</li>\n                <li>ÔÜí Processo r├ípido, seguro e com garantia</li>\n                <li>­ƒöÆ Suporte t├®cnico especializado inclu├¡do</li>\n                <li>­ƒÆ░ Voc├¬ pode adquirir cr├®ditos durante o processo</li>\n            </ul>\n        </div>\n        \n        <div style='background-color: #e8f5e9; padding: 12px; border-radius: 5px; border-left: 4px solid #27ae60; margin-top: 15px;'>\n            <p style='color: #27ae60; margin: 0; font-weight: bold;'>\n                ­ƒÆí FACILIDADE TOTAL: N├úo se preocupe! Voc├¬ pode inserir cr├®ditos durante o processo de compra na plataforma.\n            </p>\n        </div>\n        \n        <p style='margin-top: 15px; font-size: 13px; color: #7f8c8d;'>\n            ­ƒîÉ <b>Tech Union Services</b> - techunionservices.com | ­ƒô× (85) 99750-7465\n        </p>\n        "
        dialog.setText(texto_html)
        dialog.setTextFormat(Qt.RichText)
        btn_prosseguir = dialog.addButton('Ô£à Continuar para o Servi├ºo', QMessageBox.YesRole)
        btn_cancelar = dialog.addButton('ÔØî Cancelar', QMessageBox.RejectRole)
        dialog.exec_()
        clicked_button = dialog.clickedButton()
        if clicked_button == btn_prosseguir:
            return 'prosseguir'
        return 'cancelar'
    def abrir_servico_premium(self, titulo: str, user_id: int, parent=None) -> bool:
        try:
            print(f'­ƒöì Consultando servi├ºo: {titulo}')
            servico = self.buscar_servico_premium(titulo)
            if not servico:
                QMessageBox.warning(parent, 'Servi├ºo Indispon├¡vel', f"O servi├ºo '{titulo}' n├úo est├í dispon├¡vel no momento.\n\nPor favor, tente novamente mais tarde.")
                return False
            ativo_value = servico.get('ativo')
            esta_ativo = ativo_value in (1, '1', True, 'true', 'True', 'TRUE')
            print(f'­ƒöì Verifica├º├úo ativo: valor={ativo_value}, tipo={type(ativo_value).__name__}, ativo={esta_ativo}')
            if not esta_ativo:
                QMessageBox.information(parent, '­ƒö┤ Servi├ºo Temporariamente Indispon├¡vel', f"O servi├ºo '{titulo}' est├í temporariamente indispon├¡vel.\n\nÔÅ░ Poss├¡veis motivos:\nÔÇó Manuten├º├úo programada\nÔÇó Atualiza├º├úo de sistemas\nÔÇó Instabilidade moment├ónea\n\nPor favor, aguarde e tente novamente em alguns minutos.\n\n­ƒô× Suporte: (85) 99750-7465")
                return False
            if not servico.get('link'):
                QMessageBox.warning(parent, 'Configura├º├úo Incompleta', f"O servi├ºo '{titulo}' est├í com configura├º├úo incompleta.\n\nEntre em contato com o suporte t├®cnico.")
                return False
            descricao = servico.get('descricao', 'Descri├º├úo n├úo dispon├¡vel')
            if not self.exibir_dialogo_descricao(titulo, descricao, parent):
                print(f'ÔÜá´©Å Usu├írio n├úo confirmou leitura de {titulo}')
                return False
            resultado_creditos = self.exibir_aviso_creditos(titulo, parent)
            if resultado_creditos == 'cancelar':
                print(f'ÔÜá´©Å Usu├írio cancelou servi├ºo {titulo}')
                return False
        except Exception as e:
            print('ÔÜá´©Å Erro ao processar servi├ºo premium')
            QMessageBox.critical(parent, 'Erro Inesperado', 'Ocorreu um erro ao processar sua solicita├º├úo.\n\nPor favor, tente novamente ou entre em contato com o suporte.')
            return False
        try:
            self.registrar_uso(servico['id'], user_id, 'click')
            navegador_aberto = False
            if NAVEGADOR_INTERNO_DISPONIVEL and is_webengine_available():
                print(f'­ƒîÉ Abrindo {titulo} no navegador interno...')
            try:
                web_manager = get_web_view_manager()
                web_view = web_manager.abrir_url(url=servico['link'], title=f'­ƒÆ│ {titulo} - Tech Union Services', show_controls=True, show_url_bar=False, allow_external=True, parent=parent)
                navegador_aberto = True
                print(f'Ô£à Navegador interno aberto com sucesso para {titulo}')
                QMessageBox.information(parent, f'­ƒîÉ {titulo}', 'Ô£à O servi├ºo foi aberto no navegador interno.\n\n­ƒôï Siga as instru├º├Áes na p├ígina para completar o processo.\n\n­ƒÆí Dica: Tenha em m├úos o IMEI/ID do dispositivo.\n\n­ƒô× Suporte: RESTORECELL SOLU├ç├òES TECNOL├ôGICA')
            except Exception as e:
                QMessageBox.critical(parent, 'Erro ao Abrir Servi├ºo', f'N├úo foi poss├¡vel abrir automaticamente.\n\n­ƒôï Copie e cole este link no seu navegador:\n\n{servico['link']}\n\n­ƒô× Suporte: (85) 99750-7465')
                try:
                    try:
                        return False
                    except Exception as e_interno:
                        print(f'ÔÜá´©Å Erro no navegador interno: {str(e_interno)}')
                        print('­ƒô▒ Tentando fallback para navegador externo...')
                        navegador_aberto = False
                except Exception as e:
                    print('ÔÜá´©Å Erro ao processar servi├ºo premium')
                    QMessageBox.critical(parent, 'Erro Inesperado', 'Ocorreu um erro ao processar sua solicita├º├úo.\n\nPor favor, tente novamente ou entre em contato com o suporte.')
                    return False
            else:
                if not navegador_aberto:
                    webbrowser.open(servico['link'])
                    print(f'Ô£à Servi├ºo {titulo} aberto no navegador externo')
                QMessageBox.information(parent, f'­ƒîÉ {titulo}', f'Ô£à O servi├ºo foi aberto no seu navegador padr├úo.\n\n­ƒöù Link: {servico['link']}\n\n­ƒôï Siga as instru├º├Áes na p├ígina para completar o processo.\n\n­ƒÆí Dica: Tenha em m├úos o IMEI/ID do dispositivo.\n\n­ƒô× Suporte: RESTORECELL SOLU├ç├òES TECNOL├ôGICA')
        except Exception as e:
            QMessageBox.critical(parent, 'Erro ao Abrir Servi├ºo', f'N├úo foi poss├¡vel abrir automaticamente.\n\n­ƒôï Copie e cole este link no seu navegador:\n\n{servico['link']}\n\n­ƒô× Suporte: (85) 99750-7465')
            try:
                return False
            except Exception as e:
                print('ÔÜá´©Å Erro ao processar servi├ºo premium')
                QMessageBox.critical(parent, 'Erro Inesperado', 'Ocorreu um erro ao processar sua solicita├º├úo.\n\nPor favor, tente novamente ou entre em contato com o suporte.')
                return False
        return True
    def registrar_uso(self, id_servico: int, id_usuario: int, tipo_interacao: str='click'):
        conn = self._conectar_db()
        if not conn:
            print('ÔÜá´©Å Analytics temporariamente indispon├¡vel')
            return
        try:
            cursor = conn.cursor()
            cursor.execute('\n                INSERT INTO conteudos_interacoes \n                (id_conteudo, id_usuario, tipo_interacao, data_interacao)\n                VALUES (%s, %s, %s, NOW())\n            ', (id_servico, id_usuario, tipo_interacao))
            conn.commit()
            cursor.close()
            conn.close()
            print(f'Ô£à Uso registrado: {tipo_interacao}')
            return
        except Exception as e:
            print('ÔÜá´©Å Analytics indispon├¡vel')
            if conn:
                conn.close()
    def atualizar_status_botao(self, botao: QPushButton, titulo: str):
        try:
            cache_key = f'premium_{titulo}'
            if cache_key in self._cache:
                del self._cache[cache_key]
            servico = self.buscar_servico_premium(titulo)
            if servico:
                ativo_value = servico.get('ativo')
                esta_ativo = ativo_value in (1, '1', True, 'true', 'True', 'TRUE')
            else:
                esta_ativo = False
            indicador = '­ƒƒó' if esta_ativo else '­ƒö┤'
            botao.setText(f'{indicador} {titulo}')
            botao.setProperty('servico_ativo', esta_ativo)
            if esta_ativo:
                botao.setToolTip('Ô£à Servi├ºo ativo e dispon├¡vel\nClique para mais informa├º├Áes')
            else:
                botao.setToolTip('­ƒö┤ Servi├ºo temporariamente indispon├¡vel')
            print(f"Ô£à Status do bot├úo '{titulo}' atualizado: {'Ativo' if esta_ativo else 'Inativo'}")
            return
        except Exception as e:
            print('ÔÜá´©Å Erro ao atualizar status do bot├úo')
    def limpar_cache(self):
        self._cache.clear()
        print('­ƒöä Cache de servi├ºos premium limpo')
_manager_instance = None
def get_premium_services_manager() -> PremiumServicesManager:
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = PremiumServicesManager()
    return _manager_instance
