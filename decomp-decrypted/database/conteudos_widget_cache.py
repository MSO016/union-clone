from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea, QProgressBar)
from PyQt5.QtCore import (Qt, QTimer, QThread, pyqtSignal)
from PyQt5.QtGui import (QPixmap, QIcon, QFont)
import webbrowser
import os
from cache_manager import ConteudosCacheManager
class SyncThread(QThread):
    sync_finished = pyqtSignal(bool)
    sync_progress = pyqtSignal(str)
    def __init__(self, cache_manager):
        super().__init__()
        self.cache_manager = cache_manager
    def run(self):
        try:
            self.sync_progress.emit('Sincronizando...')
            sucesso = self.cache_manager.sincronizar_com_mysql()
            self.sync_finished.emit(sucesso)
            return
        except Exception as e:
            self.sync_progress.emit(f'Erro: {str(e)}')
            self.sync_finished.emit(False)
class ConteudosDinamicosWidgetCache(QWidget):
    def __init__(self, user_type='todos', user_id=None, parent=None):
        super().__init__(parent)
        self.user_type = user_type
        self.user_id = user_id
        self.cache_manager = ConteudosCacheManager()
        self.sync_thread = None
        self.setup_ui()
        self.carregar_conteudos()
        self.timer = QTimer()
        self.timer.timeout.connect(self.atualizar_cache_automatico)
        self.timer.start(300000)
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.cache_manager.limpar_cache_expirado)
        self.cleanup_timer.start(600000)
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        self.header_frame = self.criar_header()
        layout.addWidget(self.header_frame)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet('\n            QScrollArea {\n                border: none;\n                background-color: transparent;\n            }\n            QScrollBar:vertical {\n                background: #f0f0f0;\n                width: 8px;\n                border-radius: 4px;\n            }\n            QScrollBar::handle:vertical {\n                background: #c0c0c0;\n                border-radius: 4px;\n            }\n        ')
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(10)
        self.scroll_area.setWidget(self.content_widget)
        layout.addWidget(self.scroll_area)
    def criar_header(self):
        frame = QFrame()
        frame.setStyleSheet('\n            QFrame {\n                background-color: #f8f9fa;\n                border-radius: 6px;\n                padding: 8px;\n                border: 1px solid #dee2e6;\n            }\n        ')
        frame.setMaximumHeight(60)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 5, 10, 5)
        titulo = QLabel('­ƒô▒ Conte├║dos Din├ómicos')
        titulo.setStyleSheet('font-weight: bold; font-size: 14px; color: #2c3e50;')
        layout.addWidget(titulo)
        layout.addStretch()
        self.status_label = QLabel('­ƒöä Carregando...')
        self.status_label.setStyleSheet('font-size: 11px; color: #6c757d;')
        layout.addWidget(self.status_label)
        self.sync_btn = QPushButton('­ƒöä')
        self.sync_btn.setStyleSheet('\n            QPushButton {\n                background-color: #17a2b8;\n                color: white;\n                border: none;\n                padding: 4px 8px;\n                border-radius: 3px;\n                font-size: 12px;\n            }\n            QPushButton:hover {\n                background-color: #138496;\n            }\n            QPushButton:disabled {\n                background-color: #6c757d;\n            }\n        ')
        self.sync_btn.clicked.connect(self.sincronizar_manual)
        self.sync_btn.setToolTip('Sincronizar agora')
        layout.addWidget(self.sync_btn)
        return frame
    def atualizar_status_cache(self):
        try:
            metricas = self.cache_manager.get_metricas_cache()
            if metricas.get('modo_offline', False):
                status = '­ƒôí Offline'
                cor = '#dc3545'
            else:
                status = '­ƒîÉ Online'
                cor = '#28a745'
            total = metricas.get('total_conteudos', 0)
            pendentes = metricas.get('interacoes_pendentes', 0)
            texto = f'{status} ÔÇó {total} conte├║dos'
            if pendentes > 0:
                texto += f' ÔÇó {pendentes} pendentes'
            self.status_label.setText(texto)
            self.status_label.setStyleSheet(f'font-size: 11px; color: {cor};')
            return
        except Exception as e:
            self.status_label.setText('ÔØî Erro no cache')
            self.status_label.setStyleSheet('font-size: 11px; color: #dc3545;')
    def sincronizar_manual(self):
        if self.sync_thread and self.sync_thread.isRunning():
            return
        self.sync_btn.setEnabled(False)
        self.sync_btn.setText('ÔÅ│')
        self.sync_thread = SyncThread(self.cache_manager)
        self.sync_thread.sync_finished.connect(self.on_sync_finished)
        self.sync_thread.start()
    def on_sync_finished(self, sucesso):
        self.sync_btn.setEnabled(True)
        self.sync_btn.setText('­ƒöä')
        if sucesso:
            self.carregar_conteudos()
        self.atualizar_status_cache()
    def atualizar_cache_automatico(self):
        if not self.sync_thread or not self.sync_thread.isRunning():
            self.carregar_conteudos()
    def carregar_conteudos(self):
        try:
            self.limpar_conteudos()
            conteudos = self.cache_manager.get_conteudos_para_usuario(self.user_type)
            self._registrar_visualizacao_tela()
            self._exibir_conteudos_por_tipo(conteudos)
            self.atualizar_status_cache()
            return
        except Exception as e:
            self._exibir_erro(f'Erro ao carregar conte├║dos: {str(e)}')
    def _registrar_visualizacao_tela(self):
        pass
    def _exibir_conteudos_por_tipo(self, conteudos):
        if self.user_type in ('premium', 'admin') and conteudos['assistentes']:
            self.adicionar_secao_assistentes(conteudos['assistentes'])
        if self.user_type == 'basico' and conteudos['promocoes']:
            self.adicionar_secao_promocoes(conteudos['promocoes'])
        if conteudos['tutoriais']:
            self.adicionar_secao_tutoriais(conteudos['tutoriais'])
        if conteudos['noticias']:
            self.adicionar_secao_noticias(conteudos['noticias'])
        if conteudos['dicas']:
            self.adicionar_secao_dicas(conteudos['dicas'])
        if not any(conteudos.values()):
            self._exibir_sem_conteudos()
    def _exibir_sem_conteudos(self):
        frame = QFrame()
        frame.setStyleSheet('\n            QFrame {\n                background-color: #f8f9fa;\n                border-radius: 6px;\n                padding: 20px;\n                border: 1px solid #dee2e6;\n            }\n        ')
        layout = QVBoxLayout(frame)
        emoji = QLabel('­ƒô▒')
        emoji.setAlignment(Qt.AlignCenter)
        emoji.setStyleSheet('font-size: 32px; margin-bottom: 10px;')
        layout.addWidget(emoji)
        texto = QLabel('Nenhum conte├║do dispon├¡vel no momento')
        texto.setAlignment(Qt.AlignCenter)
        texto.setStyleSheet('color: #6c757d; font-size: 14px;')
        layout.addWidget(texto)
        self.content_layout.addWidget(frame)
    def _exibir_erro(self, mensagem):
        frame = QFrame()
        frame.setStyleSheet('\n            QFrame {\n                background-color: #f8d7da;\n                border-radius: 6px;\n                padding: 15px;\n                border: 1px solid #f5c6cb;\n            }\n        ')
        layout = QVBoxLayout(frame)
        erro_label = QLabel(f'ÔØî {mensagem}')
        erro_label.setStyleSheet('color: #721c24; font-size: 13px;')
        erro_label.setWordWrap(True)
        layout.addWidget(erro_label)
        self.content_layout.addWidget(frame)
    def limpar_conteudos(self):
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    def adicionar_secao_assistentes(self, assistentes):
        secao = self.criar_secao('­ƒñû Assistentes IA Premium', '#3498db')
        for assistente in assistentes[:2]:
            card = self.criar_card_assistente(assistente)
            secao.layout().addWidget(card)
        self.content_layout.addWidget(secao)
    def adicionar_secao_promocoes(self, promocoes):
        secao = self.criar_secao('Ô¡É Ofertas Especiais', '#f39c12')
        for promocao in promocoes[:1]:
            card = self.criar_card_promocao(promocao)
            secao.layout().addWidget(card)
        self.content_layout.addWidget(secao)
    def adicionar_secao_tutoriais(self, tutoriais):
        secao = self.criar_secao('­ƒôÜ Tutoriais', '#2ecc71')
        for tutorial in tutoriais[:2]:
            card = self.criar_card_simples(tutorial, '­ƒôÜ', '#2ecc71', 'Ver Tutorial')
            secao.layout().addWidget(card)
        self.content_layout.addWidget(secao)
    def adicionar_secao_noticias(self, noticias):
        secao = self.criar_secao('­ƒô░ Novidades', '#9b59b6')
        for noticia in noticias[:2]:
            card = self.criar_card_simples(noticia, '­ƒô░', '#9b59b6', 'Ler Mais')
            secao.layout().addWidget(card)
        self.content_layout.addWidget(secao)
    def adicionar_secao_dicas(self, dicas):
        secao = self.criar_secao('­ƒÆí Dicas T├®cnicas', '#e67e22')
        for dica in dicas[:2]:
            card = self.criar_card_simples(dica, '­ƒÆí', '#e67e22', 'Ver Dica')
            secao.layout().addWidget(card)
        self.content_layout.addWidget(secao)
    def criar_secao(self, titulo, cor):
        frame = QFrame()
        frame.setStyleSheet(f'\n            QFrame {{\n                background-color: white;\n                border-radius: 8px;\n                border-left: 4px solid {cor};\n                padding: 12px;\n                margin: 3px;\n            }}\n        ')
        layout = QVBoxLayout(frame)
        layout.setSpacing(8)
        titulo_label = QLabel(titulo)
        titulo_label.setStyleSheet(f'\n            font-size: 15px;\n            font-weight: bold;\n            color: {cor};\n            padding: 3px 0px;\n        ')
        layout.addWidget(titulo_label)
        return frame
    def criar_card_assistente(self, assistente):
        card = QFrame()
        card.setStyleSheet('\n            QFrame {\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, \n                           stop:0 #3498db, stop:1 #2980b9);\n                border-radius: 8px;\n                padding: 15px;\n                color: white;\n            }\n        ')
        layout = QHBoxLayout(card)
        icon_label = QLabel('­ƒñû')
        icon_label.setStyleSheet('font-size: 28px; padding-right: 15px;')
        layout.addWidget(icon_label)
        content_layout = QVBoxLayout()
        titulo = QLabel(assistente['titulo'])
        titulo.setStyleSheet('font-weight: bold; font-size: 16px; color: white;')
        content_layout.addWidget(titulo)
        descricao = QLabel(assistente['descricao'])
        descricao.setStyleSheet('color: white; font-size: 13px; margin-top: 5px;')
        descricao.setWordWrap(True)
        content_layout.addWidget(descricao)
        layout.addLayout(content_layout, 1)
        btn = QPushButton('USAR IA')
        btn.setStyleSheet('\n            QPushButton {\n                background-color: white;\n                color: #3498db;\n                border: none;\n                padding: 10px 20px;\n                border-radius: 5px;\n                font-weight: bold;\n                font-size: 13px;\n            }\n            QPushButton:hover {\n                background-color: #ecf0f1;\n            }\n        ')
        btn.clicked.connect((lambda: self.abrir_assistente(assistente)))
        layout.addWidget(btn)
        return card
    def criar_card_promocao(self, promocao):
        card = QFrame()
        card.setStyleSheet('\n            QFrame {\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, \n                           stop:0 #f39c12, stop:1 #e67e22);\n                border-radius: 8px;\n                padding: 15px;\n                color: white;\n            }\n        ')
        layout = QHBoxLayout(card)
        content_layout = QVBoxLayout()
        titulo = QLabel(promocao['titulo'])
        titulo.setStyleSheet('font-weight: bold; font-size: 16px; color: white;')
        content_layout.addWidget(titulo)
        descricao = QLabel(promocao['descricao'])
        descricao.setStyleSheet('color: white; font-size: 13px; margin-top: 5px;')
        descricao.setWordWrap(True)
        content_layout.addWidget(descricao)
        layout.addLayout(content_layout, 1)
        btn = QPushButton('FAZER UPGRADE')
        btn.setStyleSheet('\n            QPushButton {\n                background-color: white;\n                color: #f39c12;\n                border: none;\n                padding: 10px 15px;\n                border-radius: 5px;\n                font-weight: bold;\n                font-size: 13px;\n            }\n            QPushButton:hover {\n                background-color: #ecf0f1;\n            }\n        ')
        btn.clicked.connect((lambda: self.abrir_promocao(promocao)))
        layout.addWidget(btn)
        return card
    def criar_card_simples(self, conteudo, emoji, cor, texto_botao):
        card = QFrame()
        card.setStyleSheet('\n            QFrame {\n                background-color: #f8f9fa;\n                border-radius: 6px;\n                padding: 12px;\n                border: 1px solid #dee2e6;\n            }\n            QFrame:hover {\n                background-color: #e9ecef;\n            }\n        ')
        layout = QHBoxLayout(card)
        icon_label = QLabel(emoji)
        icon_label.setStyleSheet('font-size: 22px; padding-right: 12px;')
        layout.addWidget(icon_label)
        content_layout = QVBoxLayout()
        titulo = QLabel(conteudo['titulo'])
        titulo.setStyleSheet('font-weight: bold; font-size: 14px; color: #2c3e50;')
        content_layout.addWidget(titulo)
        if conteudo.get('descricao'):
            desc_texto = conteudo['descricao']
            if len(desc_texto) > 80:
                desc_texto = desc_texto[:80] + '...'
            descricao = QLabel(desc_texto)
            descricao.setStyleSheet('color: #6c757d; font-size: 12px; margin-top: 3px;')
            descricao.setWordWrap(True)
            content_layout.addWidget(descricao)
        layout.addLayout(content_layout, 1)
        btn = QPushButton(texto_botao)
        btn.setStyleSheet(f'\n            QPushButton {{\n                background-color: {cor};\n                color: white;\n                border: none;\n                padding: 6px 12px;\n                border-radius: 4px;\n                font-size: 12px;\n                font-weight: bold;\n            }}\n            QPushButton:hover {{\n                opacity: 0.9;\n            }}\n        ')
        btn.clicked.connect((lambda: self.abrir_conteudo(conteudo)))
        layout.addWidget(btn)
        return card
    def abrir_assistente(self, assistente):
        self.cache_manager.registrar_interacao(assistente['id'], 'click', self.user_id)
        if assistente.get('link'):
            webbrowser.open(assistente['link'])
    def abrir_promocao(self, promocao):
        self.cache_manager.registrar_interacao(promocao['id'], 'click', self.user_id)
        print(f'Abrindo promo├º├úo: {promocao['titulo']}')
    def abrir_conteudo(self, conteudo):
        self.cache_manager.registrar_interacao(conteudo['id'], 'click', self.user_id)
        if conteudo.get('link'):
            if conteudo['link'].startswith('http'):
                webbrowser.open(conteudo['link'])
                return
            print(f'Navegando para: {conteudo['link']}')
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    widget = ConteudosDinamicosWidgetCache(user_type='premium', user_id=123)
    widget.setWindowTitle('Teste - Conte├║dos Din├ómicos Cache')
    widget.resize(400, 600)
    widget.show()
    sys.exit(app.exec_())
