import webbrowser
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QFrame, QScrollArea, QMessageBox, QTextEdit, QSizePolicy, QInputDialog, QLineEdit, QApplication)
from PyQt5.QtCore import (Qt, QTimer, QThread, pyqtSignal)
from PyQt5.QtGui import (QFont, QPixmap, QIcon, QCursor)
from app.utils.arquivos_manager import ArquivosManager
from app.utils.webhook_client import WebhookClient
import logging
class DetalheArquivoWindow(QMainWindow):
    def __init__(self, arquivo_info: dict, email_login: str, parent=None):
        super().__init__(parent)
        self.arquivo_info = arquivo_info
        self.email_login = email_login
        self.parent_window = parent
        self.logger = logging.getLogger(__name__)
        self.arquivos_manager = ArquivosManager()
        self.webhook_client = WebhookClient()
        self._setup_ui()
        self._aplicar_estilos()
        self._popular_detalhes()
        self._verificar_status_compra_inicial()
    def _setup_ui(self):
        titulo = self.arquivo_info.get('titulo', 'Arquivo')
        self.setWindowTitle(f'{titulo}')
        self.setMinimumSize(900, 700)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        self._criar_header(main_layout)
        self._criar_area_conteudo(main_layout)
        self._criar_area_acoes(main_layout)
    def _criar_header(self, parent_layout):
        header_widget = QFrame()
        header_widget.setObjectName('headerFrame')
        header_widget.setMinimumHeight(60)
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(15, 10, 15, 10)
        header_layout.setSpacing(8)
        top_layout = QHBoxLayout()
        marca = self.arquivo_info.get('marca', '')
        modelo = self.arquivo_info.get('modelo', '')
        categoria = self.arquivo_info.get('categoria', '')
        nav_texto = f'Downloads > {marca}'
        if modelo and modelo.strip():
            nav_texto += f' > {modelo}'
        nav_texto += f' > {categoria} > Detalhes'
        nav_label = QLabel(nav_texto)
        nav_label.setObjectName('navLabel')
        nav_label.setFont(QFont('Arial', 11))
        nav_label.setWordWrap(True)
        top_layout.addWidget(nav_label)
        top_layout.addStretch()
        header_layout.addLayout(top_layout)
        parent_layout.addWidget(header_widget)
    def _criar_area_conteudo(self, parent_layout):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setSpacing(20)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        scroll_area.setWidget(content_widget)
        parent_layout.addWidget(scroll_area)
    def _criar_area_acoes(self, parent_layout):
        acoes_frame = QFrame()
        acoes_frame.setObjectName('acoesFrame')
        acoes_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        main_layout = QVBoxLayout(acoes_frame)
        main_layout.setContentsMargins(25, 20, 25, 25)
        main_layout.setSpacing(15)
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        btn_voltar = QPushButton('Voltar')
        btn_voltar.setObjectName('btnVoltar')
        btn_voltar.setFixedSize(120, 40)
        btn_voltar.clicked.connect(self.close)
        header_layout.addWidget(btn_voltar)
        header_layout.addStretch()
        main_layout.addWidget(header_container)
        botoes_container = QWidget()
        botoes_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        botoes_layout = QHBoxLayout(botoes_container)
        botoes_layout.setContentsMargins(0, 10, 0, 0)
        botoes_layout.addStretch()
        self._criar_botoes_acao(botoes_layout)
        botoes_layout.addStretch()
        main_layout.addWidget(botoes_container)
        parent_layout.addWidget(acoes_frame)
    def _criar_botoes_acao(self, parent_layout):
        tipo_arquivo = self.arquivo_info.get('tipo_arquivo', 'pago')
        arquivo_id = self.arquivo_info.get('id')
        if tipo_arquivo == 'gratuito':
            btn_download = QPushButton('Download Gratuito')
            btn_download.setObjectName('btnDownloadGratuito')
            btn_download.setMinimumSize(180, 45)
            btn_download.setMaximumHeight(50)
            btn_download.clicked.connect(self._fazer_download_gratuito)
            parent_layout.addWidget(btn_download)
            return
        preco = float(self.arquivo_info.get('preco', 0))
        liberacao = self.arquivos_manager.verificar_liberacao_usuario(self.email_login, arquivo_id)
        if liberacao:
            btn_download = QPushButton('Download Liberado')
            btn_download.setObjectName('btnDownloadLiberado')
            btn_download.setMinimumSize(180, 45)
            btn_download.setMaximumHeight(50)
            btn_download.clicked.connect(self._fazer_download_liberado)
            parent_layout.addWidget(btn_download)
            return
        compra_pendente = self.arquivos_manager.verificar_compra_pendente(self.email_login, arquivo_id)
        if compra_pendente:
            codigo_compra = str(compra_pendente['codigo_compra'])
            status_container = QWidget()
            status_container.setMaximumWidth(520)
            status_layout = QVBoxLayout(status_container)
            status_layout.setSpacing(8)
            status_layout.setContentsMargins(10, 5, 10, 5)
            status_label = QLabel('COMPRA PENDENTE')
            status_label.setObjectName('statusPendente')
            status_label.setFont(QFont('Arial', 14, QFont.Bold))
            status_label.setAlignment(Qt.AlignCenter)
            status_layout.addWidget(status_label)
            info_label = QLabel(f'C├│digo: {codigo_compra}')
            info_label.setObjectName('infoPendente')
            info_label.setFont(QFont('Arial', 11))
            info_label.setAlignment(Qt.AlignCenter)
            info_label.setWordWrap(True)
            info_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            status_layout.addWidget(info_label)
            btn_copiar = QPushButton('Copiar C├│digo')
            btn_copiar.setObjectName('btnCopiarCodigo')
            btn_copiar.setFixedHeight(38)
            btn_copiar.setCursor(QCursor(Qt.PointingHandCursor))
            btn_copiar.clicked.connect((lambda _checked=False, c=codigo_compra, b=btn_copiar: self._copiar_codigo(c, b)))
            status_layout.addWidget(btn_copiar, alignment=Qt.AlignCenter)
            parent_layout.addWidget(status_container)
            return
        self._criar_sistema_compras_inteligente(parent_layout, preco)
    def _criar_sistema_compras_inteligente(self, parent_layout, preco):
        saldo_creditos = self.arquivos_manager.obter_saldo_creditos(self.email_login)
        container = QWidget()
        container.setMaximumWidth(650)
        layout = QHBoxLayout(container)
        layout.setSpacing(20)
        layout.setContentsMargins(10, 5, 10, 5)
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setSpacing(8)
        info_layout.setContentsMargins(0, 0, 0, 0)
        preco_label = QLabel(f'R$ {preco:.2f}')
        preco_label.setObjectName('precoDetalhes')
        preco_label.setFont(QFont('Arial', 16, QFont.Bold))
        preco_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(preco_label)
        creditos_info = QLabel(f'Saldo: R$ {saldo_creditos:.2f}')
        creditos_info.setObjectName('creditosInfo')
        creditos_info.setFont(QFont('Arial', 12))
        creditos_info.setAlignment(Qt.AlignCenter)
        if saldo_creditos >= preco:
            creditos_info.setStyleSheet('color: #27AE60; font-weight: bold;')
        else:
            creditos_info.setStyleSheet('color: #E74C3C; font-weight: bold;')
        info_layout.addWidget(creditos_info)
        layout.addWidget(info_widget)
        botoes_widget = QWidget()
        botoes_layout = QHBoxLayout(botoes_widget)
        botoes_layout.setSpacing(12)
        botoes_layout.setContentsMargins(0, 0, 0, 0)
        if saldo_creditos >= preco:
            btn_creditos = QPushButton('Comprar\ncom Cr├®ditos')
            btn_creditos.setObjectName('btnComprarCreditos')
            btn_creditos.setMinimumSize(130, 50)
            btn_creditos.setMaximumSize(180, 60)
            btn_creditos.clicked.connect(self._comprar_com_creditos)
            botoes_layout.addWidget(btn_creditos)
            divisor = QLabel('|')
            divisor.setFont(QFont('Arial', 20, QFont.Bold))
            divisor.setStyleSheet('color: #BDC3C7;')
            divisor.setAlignment(Qt.AlignCenter)
            botoes_layout.addWidget(divisor)
        btn_whatsapp = QPushButton('Comprar\nvia WhatsApp')
        btn_whatsapp.setObjectName('btnComprarWhatsApp')
        btn_whatsapp.setMinimumSize(130, 50)
        btn_whatsapp.setMaximumSize(180, 60)
        btn_whatsapp.clicked.connect(self._iniciar_compra)
        botoes_layout.addWidget(btn_whatsapp)
        layout.addWidget(botoes_widget)
        if saldo_creditos < preco:
            diferenca = preco - saldo_creditos
            msg_widget = QWidget()
            msg_layout = QVBoxLayout(msg_widget)
            msg_layout.setContentsMargins(0, 0, 0, 0)
            msg_saldo = QLabel(f'Faltam R$ {diferenca:.2f}\npara compra instant├ónea')
            msg_saldo.setObjectName('msgSaldoInsuficiente')
            msg_saldo.setFont(QFont('Arial', 10))
            msg_saldo.setAlignment(Qt.AlignCenter)
            msg_saldo.setStyleSheet('color: #F39C12; font-style: italic;')
            msg_saldo.setWordWrap(True)
            msg_layout.addWidget(msg_saldo)
            layout.addWidget(msg_widget)
        parent_layout.addWidget(container)
    def _popular_detalhes(self):
        titulo_frame = self._criar_secao_titulo()
        self.content_layout.addWidget(titulo_frame)
        info_frame = self._criar_secao_informacoes()
        self.content_layout.addWidget(info_frame)
        solucao_frame = self._criar_secao_solucao()
        self.content_layout.addWidget(solucao_frame)
        desc_frame = self._criar_secao_descricao()
        self.content_layout.addWidget(desc_frame)
        stats_frame = self._criar_secao_estatisticas()
        self.content_layout.addWidget(stats_frame)
        self.content_layout.addStretch()
    def _criar_secao_titulo(self):
        frame = QFrame()
        frame.setObjectName('tituloFrame')
        layout = QVBoxLayout(frame)
        layout.setSpacing(10)
        titulo_label = QLabel(self.arquivo_info.get('titulo', 'Sem t├¡tulo'))
        titulo_label.setObjectName('tituloArquivo')
        titulo_label.setFont(QFont('Arial', 20, QFont.Bold))
        titulo_label.setWordWrap(True)
        titulo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo_label)
        marca = self.arquivo_info.get('marca', '')
        modelo = self.arquivo_info.get('modelo', '')
        categoria = self.arquivo_info.get('categoria', '')
        subtitulo_texto = f'{marca}'
        if modelo and modelo.strip():
            subtitulo_texto += f' ÔÇó {modelo}'
        subtitulo_texto += f' ÔÇó {categoria}'
        subtitulo_label = QLabel(subtitulo_texto)
        subtitulo_label.setObjectName('subtituloArquivo')
        subtitulo_label.setFont(QFont('Arial', 14))
        subtitulo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitulo_label)
        return frame
    def _criar_secao_informacoes(self):
        frame = QFrame()
        frame.setObjectName('infoFrame')
        layout = QVBoxLayout(frame)
        layout.setSpacing(15)
        titulo_secao = QLabel('Informa├º├Áes Detalhadas')
        titulo_secao.setObjectName('tituloSecao')
        titulo_secao.setFont(QFont('Arial', 16, QFont.Bold))
        layout.addWidget(titulo_secao)
        info_grid = QGridLayout()
        info_grid.setSpacing(12)
        info_grid.setColumnStretch(1, 1)
        linha = 0
        tipo = self.arquivo_info.get('tipo_arquivo', 'pago')
        tipo_texto = 'GRATUITO' if tipo == 'gratuito' else 'PAGO'
        self._adicionar_info_grid(info_grid, linha, 'Tipo:', tipo_texto)
        linha += 1
        if tipo == 'pago' and self.arquivo_info.get('preco'):
            preco = float(self.arquivo_info['preco'])
            self._adicionar_info_grid(info_grid, linha, 'Pre├ºo:', f'R$ {preco:.2f}')
            linha += 1
        if self.arquivo_info.get('tamanho_arquivo'):
            self._adicionar_info_grid(info_grid, linha, 'Tamanho:', f' {self.arquivo_info['tamanho_arquivo']}')
            linha += 1
        if self.arquivo_info.get('data_criacao'):
            data = str(self.arquivo_info['data_criacao'])[:10]
            data_formatada = data.replace('-', '/')
            self._adicionar_info_grid(info_grid, linha, 'Publicado:', f'{data_formatada}')
            linha += 1
        if self.arquivo_info.get('data_modificacao'):
            data_mod = str(self.arquivo_info['data_modificacao'])[:10]
            data_mod_formatada = data_mod.replace('-', '/')
            self._adicionar_info_grid(info_grid, linha, 'Atualizado:', f'{data_mod_formatada}')
            linha += 1
        downloads = self.arquivo_info.get('quantidade_downloads', 0)
        self._adicionar_info_grid(info_grid, linha, 'Downloads:', f'{downloads} vezes')
        linha += 1
        if self.arquivo_info.get('avaliacao_media'):
            avaliacao = float(self.arquivo_info['avaliacao_media'])
            estrelas = ''
            self._adicionar_info_grid(info_grid, linha, 'Avalia├º├úo:', f'{estrelas} ({avaliacao:.1f}/5.0)')
            linha += 1
        if self.arquivo_info.get('versao'):
            self._adicionar_info_grid(info_grid, linha, 'Vers├úo:', f'{self.arquivo_info['versao']}')
            linha += 1
        if self.arquivo_info.get('verificado'):
            status_verificacao = 'Verificado' if self.arquivo_info['verificado'] else 'N├úo verificado'
            self._adicionar_info_grid(info_grid, linha, 'Status:', status_verificacao)
            linha += 1
        if self.arquivo_info.get('whatsapp_contato'):
            whatsapp = self.arquivo_info['whatsapp_contato']
            self._adicionar_info_grid(info_grid, linha, 'Suporte:', f'{whatsapp}')
            linha += 1
        layout.addLayout(info_grid)
        return frame
    def _adicionar_info_grid(self, grid, linha, label, valor):
        label_widget = QLabel(label)
        label_widget.setObjectName('labelInfo')
        label_widget.setFont(QFont('Arial', 12, QFont.Bold))
        valor_widget = QLabel(valor)
        valor_widget.setObjectName('valorInfo')
        valor_widget.setFont(QFont('Arial', 12))
        grid.addWidget(label_widget, linha, 0)
        grid.addWidget(valor_widget, linha, 1)
    def _criar_secao_solucao(self):
        frame = QFrame()
        frame.setObjectName('solucaoFrame')
        layout = QVBoxLayout(frame)
        layout.setSpacing(15)
        titulo_secao = QLabel('Solu├º├úo T├®cnica')
        titulo_secao.setObjectName('tituloSecao')
        titulo_secao.setFont(QFont('Arial', 16, QFont.Bold))
        layout.addWidget(titulo_secao)
        solucao_texto = self.arquivo_info.get('solucao', '').strip()
        if solucao_texto:
            solucao_text = QTextEdit()
            solucao_text.setObjectName('solucaoTexto')
            solucao_text.setPlainText(solucao_texto)
            solucao_text.setReadOnly(True)
            solucao_text.setMaximumHeight(120)
            solucao_text.setMinimumHeight(80)
            layout.addWidget(solucao_text)
            return frame
        sem_solucao_frame = QFrame()
        sem_solucao_frame.setObjectName('semSolucaoFrame')
        sem_solucao_layout = QVBoxLayout(sem_solucao_frame)
        sem_solucao_layout.setAlignment(Qt.AlignCenter)
        sem_solucao_layout.setSpacing(8)
        icon_label = QLabel('')
        icon_label.setFont(QFont('Arial', 24))
        icon_label.setAlignment(Qt.AlignCenter)
        sem_solucao_layout.addWidget(icon_label)
        msg_label = QLabel('Solu├º├úo t├®cnica n├úo informada')
        msg_label.setObjectName('msgSemSolucao')
        msg_label.setFont(QFont('Arial', 12))
        msg_label.setAlignment(Qt.AlignCenter)
        sem_solucao_layout.addWidget(msg_label)
        layout.addWidget(sem_solucao_frame)
        return frame
    def _criar_secao_descricao(self):
        frame = QFrame()
        frame.setObjectName('descFrame')
        layout = QVBoxLayout(frame)
        layout.setSpacing(15)
        titulo_secao = QLabel('Descri├º├úo Detalhada')
        titulo_secao.setObjectName('tituloSecao')
        titulo_secao.setFont(QFont('Arial', 16, QFont.Bold))
        layout.addWidget(titulo_secao)
        descricao_texto = self.arquivo_info.get('descricao', '').strip()
        if descricao_texto:
            desc_text = QTextEdit()
            desc_text.setObjectName('descricaoTexto')
            desc_text.setPlainText(descricao_texto)
            desc_text.setReadOnly(True)
            desc_text.setMaximumHeight(150)
            desc_text.setMinimumHeight(100)
            layout.addWidget(desc_text)
            return frame
        sem_desc_frame = QFrame()
        sem_desc_frame.setObjectName('semDescFrame')
        sem_desc_layout = QVBoxLayout(sem_desc_frame)
        sem_desc_layout.setAlignment(Qt.AlignCenter)
        sem_desc_layout.setSpacing(8)
        icon_label = QLabel('')
        icon_label.setFont(QFont('Arial', 24))
        icon_label.setAlignment(Qt.AlignCenter)
        sem_desc_layout.addWidget(icon_label)
        msg_label = QLabel('Descri├º├úo detalhada n├úo informada')
        msg_label.setObjectName('msgSemDesc')
        msg_label.setFont(QFont('Arial', 12))
        msg_label.setAlignment(Qt.AlignCenter)
        sem_desc_layout.addWidget(msg_label)
        layout.addWidget(sem_desc_frame)
        return frame
    def _criar_secao_estatisticas(self):
        frame = QFrame()
        frame.setObjectName('statsFrame')
        layout = QVBoxLayout(frame)
        layout.setSpacing(15)
        titulo_secao = QLabel('Estat├¡sticas')
        titulo_secao.setObjectName('tituloSecao')
        titulo_secao.setFont(QFont('Arial', 16, QFont.Bold))
        layout.addWidget(titulo_secao)
        stats_grid = QHBoxLayout()
        stats_grid.setSpacing(30)
        downloads = self.arquivo_info.get('quantidade_downloads', 0)
        download_card = self._criar_stat_card('', str(downloads), 'Downloads')
        stats_grid.addWidget(download_card)
        tipo = self.arquivo_info.get('tipo_arquivo', 'pago')
        tipo_icon = '' if tipo == 'gratuito' else ''
        tipo_card = self._criar_stat_card(tipo_icon, tipo.upper(), 'Tipo')
        stats_grid.addWidget(tipo_card)
        if tipo == 'pago':
            preco = float(self.arquivo_info.get('preco', 0))
            preco_card = self._criar_stat_card('', f'R$ {preco:.2f}', 'Pre├ºo')
            stats_grid.addWidget(preco_card)
        stats_grid.addStretch()
        layout.addLayout(stats_grid)
        return frame
    def _criar_stat_card(self, icon, valor, label):
        card = QFrame()
        card.setObjectName('statCard')
        card.setFixedSize(120, 80)
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(5)
        icon_label = QLabel(icon)
        icon_label.setFont(QFont('Arial', 20))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        valor_label = QLabel(valor)
        valor_label.setObjectName('statValor')
        valor_label.setFont(QFont('Arial', 12, QFont.Bold))
        valor_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(valor_label)
        label_widget = QLabel(label)
        label_widget.setObjectName('statLabel')
        label_widget.setFont(QFont('Arial', 9))
        label_widget.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_widget)
        return card
    def _fazer_download_gratuito(self):
        try:
            arquivo_id = self.arquivo_info.get('id')
            if not arquivo_id:
                QMessageBox.warning(self, 'Erro', 'ID do arquivo n├úo encontrado.')
                return
            link_download = self.arquivos_manager.obter_link_download_gratuito(arquivo_id)
            if link_download:
                webbrowser.open(link_download)
                QMessageBox.information(self, 'Download Iniciado', 'Download gratuito iniciado no seu navegador!')
                self.close()
                return
            QMessageBox.warning(self, 'Erro', 'Link de download n├úo dispon├¡vel.\n\nVerifique se o arquivo ainda est├í ativo.')
            return
        except Exception as e:
            self.logger.error(f'Erro download gratuito: {str(e)}')
            QMessageBox.critical(self, 'Erro', f'Erro ao processar download: {str(e)}')
    def _iniciar_compra(self):
        try:
            arquivo_id = self.arquivo_info.get('id')
            if not arquivo_id:
                QMessageBox.warning(self, 'Erro', 'ID do arquivo n├úo encontrado.')
                return
            compra_pendente = self.arquivos_manager.verificar_compra_pendente(self.email_login, arquivo_id)
            if compra_pendente:
                QMessageBox.information(self, 'Compra Pendente', f'Voc├¬ j├í tem uma compra pendente para este arquivo!\n\nC├│digo: {compra_pendente['codigo_compra']}\nData: {str(compra_pendente['data_compra'])[:19]}\n\nAguarde a libera├º├úo ou entre em contato conosco.')
                return
            liberacao = self.arquivos_manager.verificar_liberacao_usuario(self.email_login, arquivo_id)
            if liberacao:
                QMessageBox.information(self, 'Arquivo Liberado', f"Este arquivo j├í foi liberado para voc├¬!\n\nC├│digo: {liberacao['codigo_compra']}\n\nClique em 'Download' para baixar.")
                self._atualizar_botoes_liberado()
                return
            whatsapp_contato = self.arquivo_info.get('whatsapp_contato', '')
            if not whatsapp_contato or whatsapp_contato.strip() == '':
                QMessageBox.warning(self, 'WhatsApp N├úo Cadastrado', f'Este arquivo n├úo possui WhatsApp de contato cadastrado!\n\n{self.arquivo_info.get('titulo', '')}\nR$ {float(self.arquivo_info.get('preco', 0)):.2f}\n\nEntre em contato com o suporte para mais informa├º├Áes.')
                return
            resposta = QMessageBox.question(self, 'Confirmar Compra', f'Deseja comprar este arquivo?\n\n{self.arquivo_info.get('titulo', '')}\nR$ {float(self.arquivo_info.get('preco', 0)):.2f}\nWhatsApp: {whatsapp_contato}\n\nAp├│s confirmar, voc├¬ ser├í direcionado para o WhatsApp para finalizar a compra.', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if resposta != QMessageBox.Yes:
                return
            telefone_perfil = ''
            try:
                _udata = self.arquivos_manager.obter_dados_usuario_webhook(self.email_login)
                if _udata:
                    _tel = _udata.get('telefone', '')
                    if _tel and _tel not in ('N├úo informado', 'N/A'):
                        telefone_perfil = _tel
            except Exception:
                pass
            else:
                whatsapp_comprador, ok = QInputDialog.getText(self, 'WhatsApp para contato', 'Informe seu WhatsApp (com DDD) para receber a libera├º├úo:', QLineEdit.Normal, telefone_perfil)
                if not ok:
                    return
                whatsapp_comprador = ''.join((c for c in whatsapp_comprador if c.isdigit()))[:15]
                if len(whatsapp_comprador) < 10:
                    QMessageBox.warning(self, 'WhatsApp Inv├ílido', 'Informe um n├║mero v├ílido com DDD (m├¡nimo 10 d├¡gitos).\nExemplo: 11999998888')
                    return
                self.logger.info(f'Iniciando processo de compra - Arquivo: {arquivo_id}, Usuario: {self.email_login}')
                compra_data = self.arquivos_manager.registrar_compra(self.email_login, arquivo_id)
                if not compra_data:
                    QMessageBox.critical(self, 'Erro na Compra', 'N├úo foi poss├¡vel registrar a compra!\n\nPoss├¡veis causas:\nÔÇó Arquivo n├úo encontrado\nÔÇó Arquivo n├úo ├® pago\nÔÇó Erro na conex├úo com banco\n\nVerifique os logs para mais detalhes.')
                    return
                self.logger.info(f'Compra registrada com sucesso: {compra_data['codigo_compra']}')
                usuario_data = self.arquivos_manager.obter_dados_usuario_webhook(self.email_login)
                _usuario_fallback = {'email': self.email_login, 'nome': 'Usu├írio', 'telefone': 'N/A'}
                _usuario_final = usuario_data or _usuario_fallback
                _usuario_final['whatsapp_comprador'] = whatsapp_comprador
                webhook_data = {'compra_id': compra_data['compra_id'], 'codigo_compra': compra_data['codigo_compra'], 'valor_pago': compra_data['valor_pago'], 'arquivo': compra_data['arquivo'], 'usuario': _usuario_final}
        except Exception as e:
            self.logger.error(f'Erro cr├¡tico na compra: {str(e)}')
            import traceback
            self.logger.error(f'Traceback: {traceback.format_exc()}')
            QMessageBox.critical(self, 'Erro Cr├¡tico', f'Erro inesperado ao processar compra:\n\n{str(e)}\n\nContate o suporte t├®cnico.')
        try:
            self.logger.info('Enviando notifica├º├úo de compra...')
            resultado_notificacao = self.webhook_client.enviar_compra_arquivo(webhook_data)
            notificacao_sucesso = resultado_notificacao.get('status') == 'sucesso'
            self.logger.info(f'Resultado notifica├º├úo: {resultado_notificacao}')
        except Exception as notificacao_error:
            self.logger.error(f'Erro na notifica├º├úo: {str(notificacao_error)}')
            notificacao_sucesso = False
        try:
            usuario_data = self.arquivos_manager.obter_dados_usuario_webhook(self.email_login)
            nome_usuario = usuario_data.get('nome', 'Cliente') if usuario_data else 'Cliente'
            titulo_arquivo = self.arquivo_info.get('titulo', '')
            marca_arquivo = self.arquivo_info.get('marca', '')
            modelo_arquivo = self.arquivo_info.get('modelo', '')
            preco_arquivo = float(self.arquivo_info.get('preco', 0))
            mensagem = f'­ƒøÆ *NOVA COMPRA REGISTRADA*\n\n­ƒæñ Cliente: {nome_usuario}\n­ƒôº Email: {self.email_login}\n­ƒôï C├│digo: {compra_data['codigo_compra']}\n\n­ƒô▒ *Arquivo:*\n­ƒôä {titulo_arquivo}\n­ƒÅÀ´©Å {marca_arquivo} {modelo_arquivo}\n­ƒÆ░ Valor: R$ {preco_arquivo:.2f}\n\nÔ£à Status: PENDENTE\nÔÅ░ Aguardando libera├º├úo'
            import urllib.parse
            mensagem_encoded = urllib.parse.quote(mensagem)
            whatsapp_limpo = ''.join(filter(str.isdigit, whatsapp_contato))
            whatsapp_url = f'https://wa.me/{whatsapp_limpo}?text={mensagem_encoded}'
            self.logger.info(f'Link WhatsApp gerado: {whatsapp_url}')
        except Exception as whatsapp_error:
            self.logger.error(f'Erro ao gerar link WhatsApp: {str(whatsapp_error)}')
            whatsapp_url = None
        status_notificacao = 'Notifica├º├úo enviada' if notificacao_sucesso else 'Notifica├º├úo com problema'
        codigo_compra = str(compra_data['codigo_compra'])
        ja_copiou = False
        while True:
            box = QMessageBox(self)
            box.setWindowTitle('Compra Registrada com Sucesso')
            box.setIcon(QMessageBox.Information)
            prefixo_copia = 'C├│digo copiado para a ├írea de transfer├¬ncia!\n\n' if ja_copiou else ''
            box.setText(f'{prefixo_copia}COMPRA REGISTRADA NO SISTEMA!\n\nC├│digo: {codigo_compra}\nValor: R$ {compra_data['valor_pago']:.2f}\nWhatsApp: {whatsapp_contato}\nStatus: {status_notificacao}\n\nStatus: PENDENTE\nAguarde a libera├º├úo pelo administrador\n\nDeseja abrir o WhatsApp agora para finalizar a compra?')
            btn_sim = box.addButton('Abrir WhatsApp', QMessageBox.YesRole)
            btn_copiar = box.addButton('Copiar C├│digo', QMessageBox.ActionRole)
            btn_nao = box.addButton('Agora n├úo', QMessageBox.NoRole)
            box.setDefaultButton(btn_sim)
            box.exec_()
            clicado = box.clickedButton()
            if clicado is not btn_copiar:
                break
            self._copiar_codigo(codigo_compra)
            ja_copiou = True
        resposta_whatsapp = QMessageBox.Yes if clicado is btn_sim else QMessageBox.No
        if resposta_whatsapp == QMessageBox.Yes and whatsapp_url:
            try:
                try:
                    import webbrowser
                    webbrowser.open(whatsapp_url)
                    self.logger.info('WhatsApp aberto com sucesso')
                    QMessageBox.information(self, 'WhatsApp Aberto', f'WhatsApp aberto com dados da compra!\n\nEnvie a mensagem para finalizar sua compra.\nC├│digo: {compra_data['codigo_compra']}')
                except Exception as browser_error:
                    self.logger.error(f'Erro ao abrir WhatsApp: {str(browser_error)}')
                    QMessageBox.warning(self, 'Erro ao Abrir WhatsApp', f'N├úo foi poss├¡vel abrir o WhatsApp automaticamente.\n\nEntre em contato manualmente:\nWhatsApp: {whatsapp_contato}\nC├│digo: {compra_data['codigo_compra']}')
            except Exception as e:
                self.logger.error(f'Erro cr├¡tico na compra: {str(e)}')
                import traceback
                self.logger.error(f'Traceback: {traceback.format_exc()}')
                QMessageBox.critical(self, 'Erro Cr├¡tico', f'Erro inesperado ao processar compra:\n\n{str(e)}\n\nContate o suporte t├®cnico.')
        elif resposta_whatsapp == QMessageBox.Yes and not whatsapp_url:
            QMessageBox.warning(self, 'Erro no Link WhatsApp', f'Erro ao gerar link do WhatsApp.\n\nEntre em contato manualmente:\nWhatsApp: {whatsapp_contato}\nC├│digo: {compra_data['codigo_compra']}')
        self.close()
    def _fazer_download_liberado(self):
        try:
            arquivo_id = self.arquivo_info.get('id')
            if not arquivo_id:
                QMessageBox.warning(self, 'Erro', 'ID do arquivo n├úo encontrado.')
                return
            liberacao = self.arquivos_manager.verificar_liberacao_usuario(self.email_login, arquivo_id)
            if not liberacao:
                QMessageBox.warning(self, 'Erro', 'Arquivo n├úo est├í liberado para download.\n\nVerifique se a compra foi aprovada.')
                return
            link_download = liberacao.get('link_download')
            if not link_download:
                QMessageBox.warning(self, 'Erro', 'Link de download n├úo encontrado.\n\nEntre em contato com o suporte.')
                return
            import webbrowser
            webbrowser.open(link_download)
            self.arquivos_manager._incrementar_downloads(arquivo_id)
            QMessageBox.information(self, 'Download Iniciado', f'Download iniciado no navegador!\n\n{liberacao['titulo']}\nC├│digo: {liberacao['codigo_compra']}')
            return
        except Exception as e:
            self.logger.error(f'Erro download liberado: {str(e)}')
            QMessageBox.critical(self, 'Erro', f'Erro ao fazer download: {str(e)}')
    def _atualizar_botoes_liberado(self):
        try:
            acoes_frame = None
            for i in range(self.centralWidget().layout().count()):
                item = self.centralWidget().layout().itemAt(i)
                if not item:
                    continue
                if not item.widget():
                    continue
                if not item.widget().objectName() == 'acoesFrame':
                    continue
                acoes_frame = item.widget()
                break
            if not acoes_frame:
                self.logger.warning('Frame de a├º├Áes n├úo encontrado')
                return
            botoes_container = None
            main_layout = acoes_frame.layout()
            if main_layout and main_layout.count() >= 2:
                botoes_item = main_layout.itemAt(1)
                if botoes_item and botoes_item.widget():
                    botoes_container = botoes_item.widget()
            if not botoes_container:
                self.logger.warning('Container de bot├Áes n├úo encontrado')
                return
            botoes_layout = botoes_container.layout()
            if botoes_layout:
                while botoes_layout.count():
                    item = botoes_layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
                botoes_layout.addStretch()
                btn_download = QPushButton('Download Liberado')
                btn_download.setObjectName('btnDownloadLiberado')
                btn_download.setMinimumSize(180, 45)
                btn_download.setMaximumHeight(50)
                btn_download.clicked.connect(self._fazer_download_liberado)
                botoes_layout.addWidget(btn_download)
                botoes_layout.addStretch()
            self.logger.info('Bot├Áes atualizados para arquivo liberado')
            return
        except Exception as e:
            self.logger.error(f'Erro ao atualizar bot├Áes liberado: {str(e)}')
            self._recriar_area_acoes_liberada()
    def _recriar_area_acoes_liberada(self):
        try:
            self.logger.info('Executando fallback: recria├º├úo completa da ├írea de a├º├Áes')
            for i in reversed(range(self.centralWidget().layout().count())):
                item = self.centralWidget().layout().itemAt(i)
                if not item:
                    continue
                if not item.widget():
                    continue
                if not item.widget().objectName() == 'acoesFrame':
                    continue
                widget = item.widget()
                self.centralWidget().layout().removeWidget(widget)
                widget.setParent(None)
                widget.deleteLater()
                break
            from PyQt5.QtCore import QCoreApplication
            QCoreApplication.processEvents()
            acoes_frame = QFrame()
            acoes_frame.setObjectName('acoesFrame')
            acoes_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
            main_layout = QVBoxLayout(acoes_frame)
            main_layout.setContentsMargins(25, 20, 25, 25)
            main_layout.setSpacing(15)
            header_container = QWidget()
            header_layout = QHBoxLayout(header_container)
            header_layout.setContentsMargins(0, 0, 0, 0)
            btn_voltar = QPushButton('Voltar')
            btn_voltar.setObjectName('btnVoltar')
            btn_voltar.setFixedSize(120, 40)
            btn_voltar.clicked.connect(self.close)
            header_layout.addWidget(btn_voltar)
            header_layout.addStretch()
            main_layout.addWidget(header_container)
            botoes_container = QWidget()
            botoes_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
            botoes_layout = QHBoxLayout(botoes_container)
            botoes_layout.setContentsMargins(0, 10, 0, 0)
            botoes_layout.addStretch()
            btn_download = QPushButton('Download Liberado')
            btn_download.setObjectName('btnDownloadLiberado')
            btn_download.setMinimumSize(180, 45)
            btn_download.setMaximumHeight(50)
            btn_download.clicked.connect(self._fazer_download_liberado)
            botoes_layout.addWidget(btn_download)
            botoes_layout.addStretch()
            main_layout.addWidget(botoes_container)
            self.centralWidget().layout().addWidget(acoes_frame)
            self.logger.info('├ürea de a├º├Áes recriada com sucesso via fallback')
            return
        except Exception as e:
            self.logger.error(f'Erro cr├¡tico no fallback de recria├º├úo: {str(e)}')
    def _copiar_codigo(self, codigo, botao=None):
        try:
            QApplication.clipboard().setText(str(codigo))
            if botao is not None:
                texto_original = botao.text()
                botao.setText('Copiado!')
                botao.setEnabled(False)
                QTimer.singleShot(2000, (lambda: None))
                return
        except Exception as e:
            self.logger.error(f'Erro ao copiar c├│digo: {str(e)}')
            QMessageBox.information(self, 'C├│digo da compra', f'Copie o c├│digo manualmente:\n\n{codigo}')
    def _aplicar_estilos(self):
        self.setStyleSheet('\n            /* Header */\n            #headerFrame {\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,\n                    stop:0 #2c3e50, stop:1 #3498db);\n                border-radius: 10px;\n            }\n            \n            #navLabel {\n                color: #ecf0f1;\n                font-weight: bold;\n            }\n            \n            /* Se├º├Áes */\n            #tituloFrame {\n                background: #f8f9fa;\n                border: 2px solid #e9ecef;\n                border-radius: 12px;\n                padding: 20px;\n            }\n            \n            #infoFrame, #descFrame, #solucaoFrame, #statsFrame {\n                background: white;\n                border: 2px solid #e9ecef;\n                border-radius: 12px;\n                padding: 20px;\n            }\n            \n            #tituloArquivo {\n                color: #2c3e50;\n                font-weight: bold;\n            }\n            \n            #subtituloArquivo {\n                color: #7f8c8d;\n            }\n            \n            #tituloSecao {\n                color: #2c3e50;\n                font-weight: bold;\n                border-bottom: 2px solid #3498db;\n                padding-bottom: 5px;\n            }\n            \n            #labelInfo {\n                color: #34495e;\n                font-weight: bold;\n            }\n            \n            #valorInfo {\n                color: #2c3e50;\n            }\n            \n            #solucaoTexto, #descricaoTexto {\n                background: #f8f9fa;\n                border: 1px solid #dee2e6;\n                border-radius: 6px;\n                font-family: Arial;\n                font-size: 12px;\n                padding: 10px;\n            }\n            \n            /* Mensagens para campos vazios */\n            #semSolucaoFrame, #semDescFrame {\n                background: #f8f9fa;\n                border: 2px dashed #dee2e6;\n                border-radius: 8px;\n                padding: 30px;\n                margin: 10px 0;\n            }\n            \n            #msgSemSolucao, #msgSemDesc {\n                color: #6c757d;\n                font-style: italic;\n            }\n            \n            /* Cards de estat├¡stica */\n            #statCard {\n                background: #f8f9fa;\n                border: 2px solid #dee2e6;\n                border-radius: 8px;\n            }\n            \n            #statValor {\n                color: #2c3e50;\n                font-weight: bold;\n            }\n            \n            #statLabel {\n                color: #6c757d;\n            }\n            \n            /* Frame de a├º├Áes com layout compacto */\n            QFrame#acoesFrame {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 rgba(255, 255, 255, 0.98),\n                    stop:1 rgba(248, 249, 250, 0.98));\n                border-top: 1px solid #DEE2E6;\n                border-radius: 0 0 12px 12px;\n                padding: 8px;\n                min-height: 100px;\n            }\n\n            /* Bot├úo voltar compacto */\n            QPushButton#btnVoltar {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #ADB5BD, stop:1 #6C757D);\n                color: white;\n                border: none;\n                border-radius: 6px;\n                font-weight: bold;\n                font-size: 11px;\n                padding: 6px 10px;\n            }\n            QPushButton#btnVoltar:hover {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #CED4DA, stop:1 #ADB5BD);\n            }\n\n            /* Labels de pre├ºo compactos */\n            QLabel#precoDetalhes {\n                color: #2C3E50;\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 rgba(52, 152, 219, 0.1),\n                    stop:1 rgba(41, 128, 185, 0.05));\n                border: 1px solid #3498DB;\n                border-radius: 8px;\n                padding: 8px 15px;\n                margin: 3px;\n            }\n\n            /* Informa├º├Áes de cr├®ditos compactas */\n            QLabel#creditosInfo {\n                padding: 6px 12px;\n                border-radius: 6px;\n                background: rgba(255, 255, 255, 0.8);\n                border: 1px solid rgba(189, 195, 199, 0.3);\n                margin: 2px;\n                font-weight: bold;\n            }\n\n            /* Bot├Áes principais compactos */\n            QPushButton#btnComprarCreditos, QPushButton#btnComprarWhatsApp {\n                border: none;\n                border-radius: 10px;\n                font-weight: bold;\n                font-size: 12px;\n                padding: 8px;\n                text-align: center;\n            }\n\n            /* Bot├úo cr├®ditos estilo especial */\n            QPushButton#btnComprarCreditos {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #FF6B6B, stop:1 #EE5A52);\n                color: white;\n                border: 2px solid #FFD93D;\n                box-shadow: 0 2px 6px rgba(255, 107, 107, 0.25);\n            }\n            QPushButton#btnComprarCreditos:hover {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #FF7979, stop:1 #FF6B6B);\n                transform: translateY(-1px);\n                box-shadow: 0 3px 10px rgba(255, 107, 107, 0.4);\n            }\n            QPushButton#btnComprarCreditos:pressed {\n                transform: translateY(0px);\n                box-shadow: 0 1px 4px rgba(255, 107, 107, 0.3);\n            }\n\n            /* Bot├úo WhatsApp estilo especial */\n            QPushButton#btnComprarWhatsApp {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #25D366, stop:1 #1DA851);\n                color: white;\n                border: 1px solid #34E87A;\n                box-shadow: 0 2px 6px rgba(37, 211, 102, 0.25);\n            }\n            QPushButton#btnComprarWhatsApp:hover {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #34E87A, stop:1 #25D366);\n                transform: translateY(-1px);\n                box-shadow: 0 3px 10px rgba(37, 211, 102, 0.4);\n            }\n            QPushButton#btnComprarWhatsApp:pressed {\n                transform: translateY(0px);\n                box-shadow: 0 1px 4px rgba(37, 211, 102, 0.3);\n            }\n\n            /* Bot├Áes de download compactos */\n            QPushButton#btnDownloadGratuito, QPushButton#btnDownloadLiberado {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #28A745, stop:1 #218838);\n                color: white;\n                border: none;\n                border-radius: 10px;\n                font-weight: bold;\n                font-size: 13px;\n                padding: 10px 15px;\n                border: 1px solid #34CE57;\n            }\n            QPushButton#btnDownloadGratuito:hover, QPushButton#btnDownloadLiberado:hover {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #34CE57, stop:1 #28A745);\n                transform: translateY(-1px);\n                box-shadow: 0 3px 8px rgba(40, 167, 69, 0.3);\n            }\n\n            /* Status pendente compacto */\n            QLabel#statusPendente {\n                color: #F39C12;\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 rgba(243, 156, 18, 0.12),\n                    stop:1 rgba(243, 156, 18, 0.04));\n                border: 1px solid #F39C12;\n                border-radius: 8px;\n                padding: 12px;\n                margin: 5px;\n            }\n\n            QLabel#infoPendente {\n                color: #7F8C8D;\n                font-style: italic;\n                padding: 4px;\n                background: rgba(255, 255, 255, 0.7);\n                border-radius: 6px;\n                margin: 3px;\n            }\n\n            /* Bot├úo copiar c├│digo do pedido pendente */\n            QPushButton#btnCopiarCodigo {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #3498DB, stop:1 #2980B9);\n                color: white;\n                border: none;\n                border-radius: 8px;\n                font-weight: bold;\n                font-size: 12px;\n                padding: 8px 18px;\n            }\n            QPushButton#btnCopiarCodigo:hover {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #5DADE2, stop:1 #3498DB);\n            }\n            QPushButton#btnCopiarCodigo:disabled {\n                background: #27AE60;\n                color: white;\n            }\n\n            /* Mensagem de saldo insuficiente compacta */\n            QLabel#msgSaldoInsuficiente {\n                padding: 6px 10px;\n                border-radius: 6px;\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 rgba(243, 156, 18, 0.1),\n                    stop:1 rgba(243, 156, 18, 0.03));\n                border: 1px solid rgba(243, 156, 18, 0.3);\n                margin: 5px;\n                font-weight: 500;\n                max-width: 120px;\n            }\n\n            /* Scrollbar vertical vis├¡vel (antes ficava quase invis├¡vel no tema claro) */\n            QScrollArea {\n                background: transparent;\n                border: none;\n            }\n            QScrollBar:vertical {\n                background: #eceff1;\n                width: 12px;\n                margin: 2px;\n                border-radius: 6px;\n            }\n            QScrollBar::handle:vertical {\n                background: #95a5a6;\n                min-height: 30px;\n                border-radius: 6px;\n            }\n            QScrollBar::handle:vertical:hover {\n                background: #7f8c8d;\n            }\n            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {\n                height: 0px;\n            }\n            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {\n                background: transparent;\n            }\n        ')
    def closeEvent(self, event):
        event.accept()
    def _verificar_status_compra_inicial(self):
        try:
            arquivo_id = self.arquivo_info.get('id')
            tipo_arquivo = self.arquivo_info.get('tipo_arquivo', 'pago')
            if not arquivo_id or tipo_arquivo == 'gratuito':
                return
            liberacao = self.arquivos_manager.verificar_liberacao_usuario(self.email_login, arquivo_id)
            if liberacao:
                self._atualizar_botoes_liberado()
                return
        except Exception as e:
            self.logger.error(f'Erro ao verificar status de compra: {str(e)}')
    def _comprar_com_creditos(self):
        try:
            arquivo_id = self.arquivo_info.get('id')
            if not arquivo_id:
                QMessageBox.warning(self, 'Erro', 'ID do arquivo n├úo encontrado.')
                return
            preco = float(self.arquivo_info.get('preco', 0))
            titulo = self.arquivo_info.get('titulo', 'Arquivo')
            resposta = QMessageBox.question(self, 'Confirmar Compra com Cr├®ditos', f'COMPRA INSTANT├éNEA COM CR├ëDITOS\n\nArquivo: {titulo}\nValor: R$ {preco:.2f}\n\nO arquivo ser├í liberado IMEDIATAMENTE ap├│s a confirma├º├úo.\nOs cr├®ditos ser├úo debitados do seu saldo.\n\nConfirmar compra?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if resposta != QMessageBox.Yes:
                return
            self.logger.info(f'Iniciando compra com cr├®ditos - Arquivo: {arquivo_id}, Usuario: {self.email_login}')
            resultado = self.arquivos_manager.registrar_compra_com_creditos(self.email_login, arquivo_id)
            if not resultado:
                QMessageBox.critical(self, 'Erro na Compra', 'Erro inesperado ao processar compra com cr├®ditos!\n\nPoss├¡veis causas:\nÔÇó Falha na conex├úo com banco\nÔÇó Arquivo n├úo encontrado\nÔÇó Erro interno do sistema\n\nSeus cr├®ditos foram preservados.\nContate o suporte se o problema persistir.')
                return
            if resultado.get('status') == 'saldo_insuficiente':
                saldo_atual = resultado['saldo_atual']
                diferenca = resultado['diferenca']
                QMessageBox.warning(self, 'Saldo Insuficiente', f"SALDO INSUFICIENTE PARA COMPRA\n\nValor do arquivo: R$ {preco:.2f}\nSeu saldo atual: R$ {saldo_atual:.2f}\nDiferen├ºa: R$ {diferenca:.2f}\n\nAdicione cr├®ditos ├á sua conta ou\nuse a op├º├úo 'Comprar via WhatsApp' para finalizar a compra.")
                return
            if resultado.get('status') == 'compra_realizada':
                codigo_compra = resultado['codigo_compra']
                saldo_anterior = resultado['saldo_anterior']
                saldo_atual = resultado['saldo_atual']
                QMessageBox.information(self, 'Compra Realizada com Sucesso!', f'COMPRA PROCESSADA COM CR├ëDITOS!\n\nArquivo: {titulo}\nC├│digo: {codigo_compra}\nValor pago: R$ {preco:.2f}\n\nSALDO ATUALIZADO:\nAnterior: R$ {saldo_anterior:.2f}\nAtual: R$ {saldo_atual:.2f}\n\nStatus: LIBERADO\nVoc├¬ j├í pode fazer o download!')
                self._atualizar_interface_apos_compra()
                self.logger.info(f'Compra com cr├®ditos finalizada com sucesso: {codigo_compra}')
                return
        except Exception as e:
            self.logger.error(f'Erro cr├¡tico na compra com cr├®ditos: {str(e)}')
            import traceback
            self.logger.error(f'Traceback: {traceback.format_exc()}')
            QMessageBox.critical(self, 'Erro Cr├¡tico', f'Erro inesperado ao processar compra:\n\n{str(e)}\n\nSeus cr├®ditos foram preservados.\nContate o suporte t├®cnico.')
    def _atualizar_interface_apos_compra(self):
        try:
            self._atualizar_botoes_liberado()
            try:
                if hasattr(self.parent_window, '_atualizar_saldo_creditos'):
                    self.parent_window._atualizar_saldo_creditos()
            except Exception as parent_error:
                self.logger.warning(f'N├úo foi poss├¡vel atualizar saldo na tela principal: {parent_error}')
            try:
                if hasattr(self.parent_window, '_mostrar_notificacao_compra'):
                    arquivo_titulo = self.arquivo_info.get('titulo', 'Arquivo')
                    self.parent_window._mostrar_notificacao_compra(arquivo_titulo)
            except Exception as notif_error:
                self.logger.warning(f'N├úo foi poss├¡vel mostrar notifica├º├úo: {notif_error}')
            else:
                self.logger.info('Interface atualizada ap├│s compra com cr├®ditos')
        except Exception as e:
            self.logger.error(f'Erro ao atualizar interface: {str(e)}')
