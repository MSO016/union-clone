'''
TECH UNION SOLUTIONS ÔÇö Honor FRP Widget
Tela completa com terminal proprio ÔÇö sub-aba do Tools (HXD).
Signals/QThread para nao travar a UI. Logs sanitizados.
'''
import webbrowser
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QLineEdit, QSplitter, QSizePolicy, QMessageBox, QApplication, QScrollArea)
from PyQt5.QtCore import (Qt, QThread, pyqtSignal)
from PyQt5.QtGui import QFont, QCursor
from app.views.union_unlock.hxd.gui.tema import (gerar_qss_botao, gerar_qss_botao_outline, BG, BG_WHITE, PRIMARY, BORDER, TEXT, TEXT_MUTED, GREEN, RED, WHITE)
from app.views.union_unlock.hxd.gui.log_seguro import LogSeguro
_DISCLAIMER = 'AVISO LEGAL: Esta ferramenta e destinada a tecnicos qualificados. O uso incorreto pode causar danos irreversiveis ao dispositivo. TECH UNION SOLUTIONS nao se responsabiliza por uso indevido.'
_LEGALIDADE = 'Dica: Use somente em aparelhos proprios ou com autorizacao do proprietario. Solicite nota fiscal ou termo de responsabilidade ao cliente. Qualquer uso indevido e de inteira responsabilidade do operador.'
_KEY_HINT = 'Copie a serial e gere a chave no Tech Union Services.'
_KEY_URL = 'https://techunionservices.com/service/honor-frp-key-ww-via-sn-maximo-24-hrs-usuarios-union'
_KEY_URL_LABEL = 'Gerar chave ÔåÆ techunionservices.com/honor-frp'
_HONOR_RED = '#d32f2f'
class _HonorThread(QThread):
    log = pyqtSignal(str)
    resultado = pyqtSignal(bool, str, dict)
    def __init__(self, engine, operacao, chave=''):
        super().__init__()
        self._engine = engine
        self._operacao = operacao
        self._chave = chave
    def run(self):
        def _cb(msg):
            self.log.emit(msg)
        try:
            if self._operacao == 'read_info':
                info = self._engine.read_info(log_cb=_cb)
                if info.get('conectado') or info.get('serial'):
                    self.resultado.emit(True, 'Leitura concluida', info)
                    return
                self.resultado.emit(False, 'Nenhum dispositivo detectado', info)
                return
            if self._operacao == 'unlock':
                ok, msg = self._engine.executar_unlock(self._chave, log_cb=_cb)
                self.resultado.emit(ok, msg, {})
                return
            if self._operacao == 'reboot':
                ok, msg = self._engine.reboot(log_cb=_cb)
                self.resultado.emit(ok, msg, {})
                return
        except Exception:
            self.resultado.emit(False, 'Falha na operacao', {})
class HonorFrpWidget(QWidget):
    '''Tela Honor FRP ÔÇö sub-aba independente com terminal proprio.'''
    def __init__(self, parent=None):
        super().__init__(parent)
        self._engine = None
        self._worker = None
        self._em_execucao = False
        self._serial = ''
        self._setup_ui()
        self._init_engine()
        self._exibir_boas_vindas()
    def _init_engine(self):
        try:
            from .honor_frp_engine import HonorFrpEngine
            self._engine = HonorFrpEngine()
            return
        except Exception:
            self._engine = None
            self._btn_read.setEnabled(False)
            self._btn_unlock.setEnabled(False)
            self._btn_reboot.setEnabled(False)
            self._log.erro('Modulo indisponivel')
    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        titulo = QLabel('HONOR FRP UNLOCK')
        titulo.setFont(QFont('Segoe UI', 13, QFont.Bold))
        titulo.setStyleSheet(f'color: {_HONOR_RED}; background: {BG_WHITE}; padding: 10px 16px; border-bottom: 1px solid {BORDER};')
        root.addWidget(titulo)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._criar_controles())
        splitter.addWidget(self._criar_terminal())
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        root.addWidget(splitter, stretch=1)
    def _criar_controles(self) -> QWidget:
        inner = QWidget()
        inner.setStyleSheet(f'background-color: {BG_WHITE};')
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(8)
        g1, g1_lay = self._group('PASSO 1: LER SERIAL DO DISPOSITIVO')
        g1_lay.addWidget(self._hint('Coloque o dispositivo HONOR em modo Fastboot e clique em Read Info.'))
        self._btn_read = QPushButton('Read Info ÔÇö Ler Serial')
        self._btn_read.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_read.setMinimumHeight(32)
        self._btn_read.setStyleSheet(gerar_qss_botao())
        self._btn_read.clicked.connect(self._on_read)
        g1_lay.addWidget(self._btn_read)
        lay.addWidget(g1)
        g2, g2_lay = self._group('PASSO 2: COPIAR SERIAL E GERAR CHAVE')
        g2_lay.addWidget(self._hint(_KEY_HINT))
        row = QHBoxLayout()
        row.setSpacing(4)
        self._serial_edit = QLineEdit()
        self._serial_edit.setReadOnly(True)
        self._serial_edit.setPlaceholderText('Serial sera exibida aqui')
        self._serial_edit.setFont(QFont('Consolas', 10, QFont.Bold))
        self._serial_edit.setMinimumHeight(30)
        self._serial_edit.setStyleSheet(f'QLineEdit {{ border: 1px solid {BORDER}; border-radius: 4px; padding: 3px 6px; background: {BG}; color: {TEXT}; }}')
        row.addWidget(self._serial_edit, stretch=1)
        self._btn_copy = QPushButton('COPIAR')
        self._btn_copy.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_copy.setMinimumHeight(30)
        self._btn_copy.setStyleSheet(gerar_qss_botao_outline())
        self._btn_copy.clicked.connect(self._on_copy)
        row.addWidget(self._btn_copy)
        g2_lay.addLayout(row)
        self._btn_gerar_chave = QPushButton('GERAR CHAVE NO SITE')
        self._btn_gerar_chave.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_gerar_chave.setMinimumHeight(34)
        self._btn_gerar_chave.setToolTip(_KEY_URL_LABEL)
        self._btn_gerar_chave.setStyleSheet(f"\n            QPushButton {{\n                background-color: {GREEN};\n                color: {WHITE};\n                border: none;\n                border-radius: 6px;\n                padding: 6px 12px;\n                font-family: 'Segoe UI', sans-serif;\n                font-size: 11px;\n                font-weight: bold;\n            }}\n            QPushButton:hover {{\n                background-color: #219a52;\n            }}\n            QPushButton:pressed {{\n                background-color: #1e8449;\n            }}\n        ")
        self._btn_gerar_chave.clicked.connect(self._abrir_link_chave)
        g2_lay.addWidget(self._btn_gerar_chave)
        g2_lay.addWidget(self._hint(_KEY_URL_LABEL))
        lay.addWidget(g2)
        g3, g3_lay = self._group('PASSO 3: DESBLOQUEAR FRP')
        g3_lay.addWidget(self._hint('Cole a chave gerada e clique em FRP Unlock.'))
        row3 = QHBoxLayout()
        row3.setSpacing(4)
        self._chave_edit = QLineEdit()
        self._chave_edit.setPlaceholderText('Cole a chave FRP aqui')
        self._chave_edit.setMinimumHeight(30)
        self._chave_edit.setEchoMode(QLineEdit.Password)
        self._chave_edit.setStyleSheet(f'QLineEdit {{ border: 1px solid {BORDER}; border-radius: 4px; padding: 3px 6px; background: {BG_WHITE}; color: {TEXT}; }}')
        row3.addWidget(self._chave_edit, stretch=1)
        self._btn_unlock = QPushButton('FRP UNLOCK')
        self._btn_unlock.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_unlock.setMinimumHeight(30)
        self._btn_unlock.setStyleSheet(gerar_qss_botao())
        self._btn_unlock.clicked.connect(self._on_unlock)
        row3.addWidget(self._btn_unlock)
        g3_lay.addLayout(row3)
        lay.addWidget(g3)
        g4, g4_lay = self._group('PASSO 4: REINICIAR (OPCIONAL)')
        self._btn_reboot = QPushButton('Reboot Device')
        self._btn_reboot.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_reboot.setMinimumHeight(32)
        self._btn_reboot.setStyleSheet(gerar_qss_botao_outline())
        self._btn_reboot.clicked.connect(self._on_reboot)
        g4_lay.addWidget(self._btn_reboot)
        lay.addWidget(g4)
        self._lbl_status = QLabel('Pronto.')
        self._lbl_status.setStyleSheet(f'color: {TEXT_MUTED};')
        lay.addWidget(self._lbl_status)
        lay.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(inner)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f'QScrollArea {{ background: {BG_WHITE}; border: none; }}QScrollBar:vertical {{ background: {BG}; width: 8px; }}QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 4px; min-height: 30px; }}QScrollBar::handle:vertical:hover {{ background: {PRIMARY}; }}QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}')
        return scroll
    def _group(self, title: str):
        f = QFrame()
        f.setStyleSheet(f'\n            QFrame {{\n                background-color: {BG};\n                border: 1px solid {BORDER};\n                border-radius: 6px;\n            }}\n        ')
        outer = QVBoxLayout(f)
        outer.setContentsMargins(10, 8, 10, 8)
        outer.setSpacing(4)
        t = QLabel(title)
        t.setFont(QFont('Segoe UI', 9, QFont.Bold))
        t.setStyleSheet(f'color: {PRIMARY}; border: none; background: transparent;')
        outer.addWidget(t)
        return f, outer
    def _hint(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setFont(QFont('Segoe UI', 9))
        lbl.setStyleSheet(f'color: {TEXT_MUTED}; border: none; background: transparent;')
        return lbl
    def _criar_terminal(self) -> QWidget:
        frame = QFrame()
        frame.setStyleSheet(f'background-color: #1a1a2e; border-left: 1px solid {BORDER};')
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(6)
        hdr = QHBoxLayout()
        lbl = QLabel('LOGS')
        lbl.setFont(QFont('Segoe UI', 10, QFont.Bold))
        lbl.setStyleSheet(f'color: {WHITE};')
        hdr.addWidget(lbl)
        hdr.addStretch()
        btn_limpar = QPushButton('Limpar')
        btn_limpar.setCursor(QCursor(Qt.PointingHandCursor))
        btn_limpar.setFixedHeight(26)
        btn_limpar.setStyleSheet(f'QPushButton {{ background: #2c3e50; color: {WHITE}; border: none; border-radius: 4px; padding: 2px 10px; }}QPushButton:hover {{ background: #34495e; }}')
        btn_limpar.clicked.connect(self._limpar_log)
        hdr.addWidget(btn_limpar)
        lay.addLayout(hdr)
        self._log = LogSeguro()
        self._log.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        lay.addWidget(self._log, stretch=1)
        return frame
    def _exibir_boas_vindas(self):
        self._log.info('Tech Union Services ÔÇö Honor FRP Unlock')
        self._log.aviso(_DISCLAIMER)
        self._log.aviso(_LEGALIDADE)
        self._log.info(_KEY_HINT)
        self._log.info(f'Pedido da chave: {_KEY_URL_LABEL}')
        self._log.separador()
        self._log.info('Pronto.')
    def _abrir_link_chave(self, _url: str=''):
        '''Abre a pagina de pedido da chave no navegador.'''
        try:
            webbrowser.open(_KEY_URL)
            self._log.info('[HONOR FRP] Abrindo pagina de pedido da chave...')
            return
        except Exception:
            self._log.aviso('[HONOR FRP] Nao foi possivel abrir o navegador ÔÇö acesse techunionservices.com/honor-frp')
    def _limpar_log(self):
        self._log.limpar()
        self._exibir_boas_vindas()
    def _set_busy(self, busy: bool):
        self._em_execucao = busy
        self._btn_read.setEnabled(not busy)
        self._btn_unlock.setEnabled(not busy)
        self._btn_reboot.setEnabled(not busy)
        self._btn_copy.setEnabled(not busy)
        if busy:
            self._lbl_status.setText('Processando...')
            return
        None('Pronto.')
    def _on_worker_log(self, msg: str):
        self._log.info(f'[HONOR FRP] {msg}')
    def _start_worker(self, operacao: str, chave: str=''):
        if self._em_execucao or not self._engine:
            return
        self._set_busy(True)
        self._worker = _HonorThread(self._engine, operacao, chave)
        self._worker.log.connect(self._on_worker_log)
        self._worker.resultado.connect(self._on_resultado)
        self._worker.start()
    def _on_resultado(self, ok: bool, msg: str, info: dict):
        self._set_busy(False)
        if info.get('serial'):
            self._serial = info['serial']
            self._serial_edit.setText(self._serial)
        if ok:
            self._log.sucesso(f'[HONOR FRP] {msg}')
            self._lbl_status.setText(msg)
            return
        self._log.erro(f'[HONOR FRP] {msg}')
        self._lbl_status.setText(msg)
        if msg:
            if 'dispositivo' in msg.lower():
                QMessageBox.warning(self, 'Aviso', msg)
    def _on_read(self):
        self._log.info('[HONOR FRP] Lendo informacoes...')
        self._start_worker('read_info')
    def _on_copy(self):
        serial = self._serial_edit.text().strip()
        if not serial:
            QMessageBox.warning(self, 'Aviso', 'Nenhuma serial disponivel para copiar')
            return
        QApplication.clipboard().setText(serial)
        self._log.sucesso('[HONOR FRP] Serial copiada')
        QMessageBox.information(self, 'Sucesso', 'Serial copiada para area de transferencia')
    def _on_unlock(self):
        chave = self._chave_edit.text().strip()
        if not chave or chave.lower().startswith('cole a chave'):
            QMessageBox.warning(self, 'Aviso', 'Cole a chave FRP gerada no servidor Tech Union Services.')
            return
        resp = QMessageBox.warning(self, 'Confirmar FRP Unlock', 'ATENCAO: Esta operacao ira remover a protecao FRP (Honor).\n\nO dispositivo DEVE estar em modo FASTBOOT.\nUse somente chave do Tech Union Services.\n\nAo confirmar, voce assume total responsabilidade pela\noperacao. Certifique-se de ter autorizacao do proprietario.\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resp != QMessageBox.Yes:
            return
        self._log.info('[HONOR FRP] Iniciando operacao...')
        self._start_worker('unlock', chave)
    def _on_reboot(self):
        self._log.info('[HONOR FRP] Reiniciando...')
        self._start_worker('reboot')
    def closeEvent(self, event):
        if self._worker and self._worker.isRunning():
            self._worker.wait(3000)
        super().closeEvent(event)
# WARNING: Decompyle incomplete
