from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QSplitter, QSizePolicy, QMessageBox, QScrollArea, QTextEdit)
from PyQt5.QtCore import (Qt, QThread, QTimer, pyqtSignal)
from PyQt5.QtGui import (QFont, QCursor, QColor)
from .dmiti_engine import DmitiEngine
_ACCENT = '#00897B'
_BG = '#f5f5f5'
_BG_WHITE = '#ffffff'
_BORDER = '#bdc3c7'
_TEXT = '#2c3e50'
_TEXT_MUTED = '#7f8c8d'
_GREEN = '#27ae60'
_RED = '#e53935'
_DISCLAIMER = 'AVISO: Ferramenta para tecnicos qualificados. Uso incorreto pode causar danos irreversiveis. TECH UNION SOLUTIONS nao se responsabiliza por uso indevido.'
_LEGALIDADE = 'Use somente em aparelhos proprios ou com autorizacao do proprietario. Solicite nota fiscal ou termo de responsabilidade ao cliente.'
class _LogWidget(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont('Consolas', 9))
        self.setStyleSheet('QTextEdit { background: #1a1a2e; color: #d7e6f5; border: none; padding: 8px; }')
    def info(self, msg: str):
        self.append(f'<span style="color:#ffffff">{msg}</span>')
    def sucesso(self, msg: str):
        self.append(f'<span style="color:#43a047">{msg}</span>')
    def erro(self, msg: str):
        self.append(f'<span style="color:#e53935">{msg}</span>')
    def aviso(self, msg: str):
        self.append(f'<span style="color:#f39c12">{msg}</span>')
    def prop(self, chave: str, valor: str):
        self.append(f'<span style="color:#7a8a9a">{chave}:</span> <span style="color:#4fc3f7">{valor}</span>')
    def separador(self):
        self.append('<span style="color:#7a8a9a">ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ</span>')
class _WorkerThread(QThread):
    log = pyqtSignal(str)
    resultado = pyqtSignal(bool, str, dict)
    def __init__(self, engine, operacao: str, porta: str=''):
        super().__init__()
        self._engine = engine
        self._operacao = operacao
        self._porta = porta
    def cancelar(self):
        try:
            self._engine.cancel()
            return
        except Exception:
            return
    def run(self):
        def _cb(msg):
            self.log.emit(msg)
        try:
            if self._operacao == 'boot_diag':
                ok, msg, port = self._engine.boot_diag(log_cb=_cb)
                self.resultado.emit(ok, msg, {'porta': port})
                return
            if self._operacao == 'read_info':
                info = self._engine.read_info(self._porta, log_cb=_cb)
                self.resultado.emit(bool(info), 'Leitura concluida', info)
                return
            if self._operacao == 'read_info_completo':
                info = self._engine.read_info_completo(log_cb=_cb)
                self.resultado.emit(bool(info), 'Leitura concluida', info)
                return
            if self._operacao == 'factory_reset':
                ok, msg = self._engine.factory_reset(self._porta, log_cb=_cb)
                self.resultado.emit(ok, msg, {})
                return
            if self._operacao == 'factory_reset_completo':
                ok, msg = self._engine.factory_reset_completo(log_cb=_cb)
                self.resultado.emit(ok, msg, {})
                return
            if self._operacao == 'remove_pyj':
                ok, msg = self._engine.remove_pyj(self._porta, log_cb=_cb)
                self.resultado.emit(ok, msg, {})
                return
            if self._operacao == 'remove_pyj_completo':
                ok, msg = self._engine.remove_pyj_completo(log_cb=_cb)
                self.resultado.emit(ok, msg, {})
                return
            if self._operacao == 'enable_adb':
                ok, msg = self._engine.enable_adb(self._porta, log_cb=_cb)
                self.resultado.emit(ok, msg, {})
                return
            if self._operacao == 'enable_adb_completo':
                ok, msg = self._engine.enable_adb_completo(log_cb=_cb)
                self.resultado.emit(ok, msg, {})
                return
            if self._operacao == 'reboot':
                ok, msg = self._engine.reboot(self._porta, log_cb=_cb)
                self.resultado.emit(ok, msg, {})
                return
            if self._operacao == 'reboot_completo':
                ok, msg = self._engine.reboot_completo(log_cb=_cb)
                self.resultado.emit(ok, msg, {})
                return
            if self._operacao == 'frp_remove_completo':
                ok, msg = self._engine.frp_remove_completo(log_cb=_cb)
                self.resultado.emit(ok, msg, {})
                return
            if self._operacao == 'sec_plugin_completo':
                ok, msg = self._engine.sec_plugin_completo(log_cb=_cb)
                self.resultado.emit(ok, msg, {})
                return
        except Exception as e:
            self.resultado.emit(False, 'Ocorreu um erro inesperado. Tente novamente.', {})
class DmitiWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._engine = None
        self._worker = None
        self._em_execucao = False
        self._porta_diag = ''
        self._elapsed = 0
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_tick)
        self._setup_ui()
        self._init_engine()
        self._exibir_boas_vindas()
    def _init_engine(self):
        try:
            self._engine = DmitiEngine()
            if not self._engine.available:
                self._log.erro('pyserial nao disponivel')
                self._desabilitar_todos()
                return
        except Exception as e:
            self._engine = None
            self._log.erro(f'Engine indisponivel: {e}')
            self._desabilitar_todos()
    def _desabilitar_todos(self):
        for btn in self._btn_read, self._btn_factory, self._btn_frp, self._btn_sec, self._btn_pyj, self._btn_adb, self._btn_reboot, self._btn_cancel:
            btn.setEnabled(False)
    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        titulo = QLabel('DIAG MODE ÔÇö ITEL / TECNO / INFINIX')
        titulo.setFont(QFont('Segoe UI', 13, QFont.Bold))
        titulo.setStyleSheet(f'color: {_ACCENT}; background: {_BG_WHITE}; padding: 10px 16px; border-bottom: 1px solid {_BORDER};')
        root.addWidget(titulo)
        subtitulo = QLabel('(em teste ÔÇö use por sua conta e risco, feedbacks sao bem-vindos)')
        subtitulo.setFont(QFont('Segoe UI', 9))
        subtitulo.setStyleSheet(f'color: {_TEXT_MUTED}; background: {_BG_WHITE}; padding: 0px 16px 6px 16px;')
        root.addWidget(subtitulo)
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
        inner.setStyleSheet(f'background-color: {_BG_WHITE};')
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)
        lay.addWidget(self._hint('Desligue o aparelho, aguarde 10 segundos\ne plugue o cabo USB. Selecione a operacao.'))
        g1, g1_lay = self._group('INFORMACOES')
        self._btn_read = self._botao('LER INFO')
        self._btn_read.clicked.connect(self._on_read)
        g1_lay.addWidget(self._btn_read)
        lay.addWidget(g1)
        g2, g2_lay = self._group('OPERACOES')
        self._btn_factory = self._botao('RESET DE FABRICA')
        self._btn_factory.clicked.connect(self._on_factory)
        g2_lay.addWidget(self._btn_factory)
        self._btn_frp = self._botao('REMOVER FRP')
        self._btn_frp.clicked.connect(self._on_frp)
        g2_lay.addWidget(self._btn_frp)
        self._btn_sec = self._botao('SEC PLUGIN')
        self._btn_sec.clicked.connect(self._on_sec_plugin)
        self._btn_sec.setVisible(False)
        g2_lay.addWidget(self._btn_sec)
        g2_lay.addWidget(self._hint('Testado: Smart 10, KL4.\nOutros modelos SPD tambem podem ser compativeis.'))
        self._btn_adb = self._botao('ATIVAR ADB')
        self._btn_adb.clicked.connect(self._on_adb)
        g2_lay.addWidget(self._btn_adb)
        self._btn_reboot = self._botao('REINICIAR')
        self._btn_reboot.clicked.connect(self._on_reboot)
        g2_lay.addWidget(self._btn_reboot)
        lay.addWidget(g2)
        g3, g3_lay = self._group('REMOVER PYJ')
        g3_lay.addWidget(self._hint('Chipsets UNISOC (Infinix, Tecno, Itel).\nTestado: Smart 10, KL4.\nO aparelho NAO pode ter FRP ativo.\nApos concluir, ative o ADB e use o Anti Relock.'))
        self._btn_pyj = self._botao('PYJ')
        self._btn_pyj.clicked.connect(self._on_pyj)
        g3_lay.addWidget(self._btn_pyj)
        lay.addWidget(g3)
        status_row = QHBoxLayout()
        self._lbl_status = QLabel('Pronto.')
        self._lbl_status.setStyleSheet(f'color: {_TEXT_MUTED};')
        status_row.addWidget(self._lbl_status)
        self._btn_cancel = QPushButton('CANCELAR')
        self._btn_cancel.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_cancel.setMaximumWidth(100)
        self._btn_cancel.setMinimumHeight(28)
        self._btn_cancel.setEnabled(False)
        self._btn_cancel.setStyleSheet(f'QPushButton {{ background: {_RED}; color: white; border-radius: 4px; padding: 4px 10px; font-weight: bold; }}QPushButton:disabled {{ background: #bdc3c7; color: #7f8c8d; }}')
        self._btn_cancel.clicked.connect(self._on_cancel)
        status_row.addWidget(self._btn_cancel)
        lay.addLayout(status_row)
        lay.addStretch()
        self._btn_boot = QPushButton()
        self._btn_boot.setVisible(False)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(inner)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        return scroll
    def _criar_terminal(self) -> QWidget:
        frame = QFrame()
        frame.setStyleSheet('background: #1a1a2e; border-radius: 4px;')
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(4)
        hdr = QHBoxLayout()
        lbl = QLabel('LOG')
        lbl.setFont(QFont('Consolas', 9, QFont.Bold))
        lbl.setStyleSheet('color: #7a8a9a;')
        hdr.addWidget(lbl)
        hdr.addStretch()
        btn_limpar = QPushButton('Limpar')
        btn_limpar.setMaximumWidth(60)
        btn_limpar.setStyleSheet('QPushButton { background: #2c3e50; color: white; border-radius: 3px; padding: 2px 8px; font-size: 11px; }QPushButton:hover { background: #34495e; }')
        btn_limpar.clicked.connect(self._on_limpar_log)
        hdr.addWidget(btn_limpar)
        lay.addLayout(hdr)
        self._log = _LogWidget(frame)
        lay.addWidget(self._log, stretch=1)
        return frame
    def _group(self, titulo: str):
        frame = QFrame()
        frame.setStyleSheet(f'QFrame {{ border: 1px solid {_BORDER}; border-radius: 6px; background: {_BG}; }}')
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(8)
        lbl = QLabel(titulo)
        lbl.setFont(QFont('Segoe UI', 9, QFont.Bold))
        lbl.setStyleSheet(f'color: {_TEXT}; border: none;')
        lay.addWidget(lbl)
        return frame, lay
    def _hint(self, texto: str) -> QLabel:
        lbl = QLabel(texto)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(f'color: {_TEXT_MUTED}; font-size: 11px; border: none;')
        return lbl
    def _botao(self, texto: str) -> QPushButton:
        btn = QPushButton(texto)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.setMinimumHeight(34)
        btn.setStyleSheet(f'QPushButton {{ background: {_ACCENT}; color: white; border-radius: 4px; padding: 6px 12px; font-weight: bold; }}QPushButton:hover {{ background: #00695C; }}QPushButton:disabled {{ background: #bdc3c7; color: #7f8c8d; }}')
        return btn
    def _exibir_boas_vindas(self):
        self._log.info('Tech Union Solutions ÔÇö Diag Mode Tools')
        self._log.info('Suporte: Itel, Tecno, Infinix (UNISOC/Spreadtrum)')
        self._log.aviso(_DISCLAIMER)
        self._log.aviso(_LEGALIDADE)
        self._log.separador()
        self._log.info('Aguardando comando...')
    def _on_boot(self):
        if self._em_execucao:
            return
        self._porta_diag = ''
        self._start_worker('boot_diag')
    def _on_read(self):
        self._start_worker('read_info_completo')
    def _on_factory(self):
        resp = QMessageBox.warning(self, 'Confirmar', 'ATENCAO: Apaga TODOS os dados!\n\nO aparelho deve estar DESLIGADO.\nConecte via USB ao clicar em Sim.\n\nUse somente com autorizacao do proprietario.\n\nContinuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resp != QMessageBox.Yes:
            return
        self._start_worker('factory_reset_completo')
    def _on_adb(self):
        resp = QMessageBox.warning(self, 'Confirmar', 'Ativar ADB via DiagMode.\nEfeito apos reiniciar o dispositivo.\n\nO aparelho deve estar DESLIGADO.\nConecte via USB ao clicar em Sim.\n\nContinuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resp != QMessageBox.Yes:
            return
        self._start_worker('enable_adb_completo')
    def _on_pyj(self):
        resp = QMessageBox.warning(self, 'Termo de responsabilidade ÔÇö PYJ', 'ATENCAO: Operacao de remocao PayJoy.\n\nIMPORTANTE:\n  - O aparelho NAO pode ter FRP (conta Google).\n  - O aparelho deve estar DESLIGADO antes de conectar.\n  - A operacao leva de 2 a 5 minutos.\n  - NAO desconecte durante o processo.\n\nTestado em:\n  - Tecno KL4 (UNISOC)\n  - Smart 10 (UNISOC)\n\nOutros modelos SPD (Infinix, Tecno, Itel)\ntambem podem ser compativeis.\n\nRISCOS:\n  - Pode causar brick.\n  - Escrita incorreta pode comprometer o device.\n\nAo prosseguir:\n  - Aparelho proprio ou com autorizacao.\n  - Assume TOTAL responsabilidade.\n\nContinuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resp != QMessageBox.Yes:
            return
        self._start_worker('remove_pyj_completo')
    def _on_frp(self):
        resp = QMessageBox.warning(self, 'Confirmar ÔÇö Remocao FRP', 'ATENCAO: Operacao de remocao de conta Google (FRP).\n\nO QUE SERA FEITO:\n  - Leitura automatica da estrutura do dispositivo\n  - Localizacao dinamica da area de protecao\n  - Limpeza completa da area + Reset de fabrica\n\nREQUISITOS:\n  - Aparelho DESLIGADO antes de conectar\n  - NAO desconecte durante o processo\n  - Operacao leva de 3 a 5 minutos\n\nTESTADO EM:\n  - Smart 10 (UNISOC)\n  - KL4 (UNISOC)\n  Outros modelos SPD (Infinix, Tecno, Itel)\n  tambem podem ser compativeis.\n\nRISCOS:\n  - WiFi/BT MAC sera regenerado\n  - DRM keys serao perdidos\n  - Uso indevido pode danificar o aparelho\n\nUse somente em aparelhos proprios ou com\nautorizacao do proprietario.\n\nContinuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resp != QMessageBox.Yes:
            return
        self._start_worker('frp_remove_completo')
    def _on_sec_plugin(self):
        resp = QMessageBox.warning(self, 'Confirmar ÔÇö SEC PLUGIN', 'ATENCAO: Limpeza de dados de rastreamento.\n\nO QUE SERA FEITO:\n  - Leitura da estrutura do dispositivo\n  - Deteccao de dados de rastreamento\n  - Limpeza cirurgica dos setores afetados\n\nREQUISITOS:\n  - Aparelho DESLIGADO antes de conectar\n  - NAO desconecte durante o processo\n\nTESTADO EM:\n  - Smart 10 (UNISOC)\n  - KL4 (UNISOC)\n  Outros modelos SPD tambem podem ser compativeis.\n\nUse somente em aparelhos proprios ou com\nautorizacao do proprietario.\n\nContinuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resp != QMessageBox.Yes:
            return
        self._start_worker('sec_plugin_completo')
    def _on_reboot(self):
        self._start_worker('reboot_completo')
    def _on_cancel(self):
        if self._worker:
            if self._worker.isRunning():
                self._worker.cancelar()
                self._log.aviso('Cancelando...')
                self._btn_cancel.setEnabled(False)
    def _on_limpar_log(self):
        self._log.clear()
        self._exibir_boas_vindas()
    def _start_worker(self, operacao: str):
        if self._em_execucao or not self._engine:
            return
        self._set_busy(True)
        self._log.separador()
        self._log.info(f'>>> {operacao.upper().replace('_', ' ')}')
        self._worker = _WorkerThread(self._engine, operacao, self._porta_diag)
        self._worker.log.connect(self._on_worker_log)
        self._worker.resultado.connect(self._on_resultado)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()
    def _set_busy(self, busy: bool):
        self._em_execucao = busy
        for btn in self._btn_read, self._btn_factory, self._btn_frp, self._btn_sec, self._btn_pyj, self._btn_adb, self._btn_reboot:
            btn.setEnabled(not busy)
        self._btn_cancel.setEnabled(busy)
        if busy:
            self._elapsed = 0
            self._timer.start()
            self._lbl_status.setStyleSheet(f'color: {_ACCENT};')
            self._lbl_status.setText('Executando...')
            return
        self._timer.stop()
        self._lbl_status.setStyleSheet(f'color: {_TEXT_MUTED};')
        self._lbl_status.setText('Pronto.')
    def _on_worker_log(self, msg: str):
        if ': ' in msg and not msg.startswith('[') and not msg.startswith(' '):
            parts = msg.split(': ', 1)
            if len(parts) == 2 and len(parts[0]) < 25:
                self._log.prop(parts[0], parts[1])
                return
        self._log.info(msg)
    def _on_resultado(self, ok: bool, msg: str, dados: dict):
        if ok:
            self._log.sucesso(msg)
            if 'porta' in dados and dados['porta']:
                self._porta_diag = dados['porta']
            if dados:
                if 'porta' not in dados:
                    self._log.separador()
                    for k, v in dados.items():
                        self._log.prop(k, v)
                    return
                return
            return
        self._log.erro(msg)
    def _on_finished(self):
        self._set_busy(False)
    def _on_tick(self):
        self._elapsed += 1
        self._lbl_status.setText(f'Executando... ({self._elapsed}s)')
    def closeEvent(self, event):
        self._timer.stop()
        if self._worker and self._worker.isRunning():
            self._worker.cancelar()
            self._worker.wait(5000)
            if self._worker.isRunning():
                self._worker.terminate()
        if self._engine:
            try:
                self._engine.cancel()
            except Exception:
                pass
        super().closeEvent(event)
