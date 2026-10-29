'''Ref: administrativo/documentacao/19-07-2026-ANALISE-MTK-BOOT-META/'''
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QSplitter, QSizePolicy, QMessageBox, QScrollArea, QFileDialog)
from PyQt5.QtCore import (Qt, QThread, QTimer, pyqtSignal)
from PyQt5.QtGui import QFont, QCursor
from app.views.union_unlock.hxd.gui.tema import (gerar_qss_botao, gerar_qss_botao_outline, BG, BG_WHITE, PRIMARY, BORDER, TEXT, TEXT_MUTED, GREEN, RED, WHITE)
from app.views.union_unlock.hxd.gui.log_seguro import LogSeguro
_DISCLAIMER = 'AVISO LEGAL: Esta ferramenta e destinada a tecnicos qualificados. O uso incorreto pode causar danos irreversiveis ao dispositivo. TECH UNION SOLUTIONS nao se responsabiliza por uso indevido.'
_LEGALIDADE = 'Dica: Use somente em aparelhos proprios ou com autorizacao do proprietario. Solicite nota fiscal ou termo de responsabilidade ao cliente.'
_ACCENT = '#d32f2f'
class _WorkerThread(QThread):
    '''Worker thread para operacoes em background.'''
    log = pyqtSignal(str)
    resultado = pyqtSignal(bool, str, dict)
    def __init__(self, engine, operacao, porta='', engine_2026=None, save_dir=''):
        super().__init__()
        self._engine = engine
        self._operacao = operacao
        self._porta = porta
        self._engine_2026 = engine_2026
        self._save_dir = save_dir
    def cancelar(self):
        '''Cancela operacao via engine (seguro).'''
        try:
            self._engine.cancel()
        except Exception:
            pass
        if self._engine_2026:
            try:
                self._engine_2026.cancel()
                return
            except Exception:
                pass
    def run(self):
        def _cb(msg):
            self.log.emit(msg)
        try:
            if self._operacao == 'boot_meta':
                ok, msg, port = self._engine.boot_meta(log_cb=_cb)
                self.resultado.emit(ok, msg, {'porta': port})
                return
            if self._operacao == 'read_info':
                info = self._engine.read_info(self._porta, log_cb=_cb)
                self.resultado.emit(bool(info), 'Leitura concluida', info)
                return
            if self._operacao == 'diagnostics':
                diag = self._engine.diagnostics(self._porta, log_cb=_cb)
                self.resultado.emit(bool(diag), 'Diagnostico concluido', diag)
                return
            if self._operacao == 'hw_diagnostics':
                diag = self._engine.hw_diagnostics(self._porta, log_cb=_cb)
                ok = bool(diag and diag.get('tests'))
                resumo = diag.get('resumo', {})
                msg = 'Diagnostico: %d OK | %d Falha | %d Info' % (resumo.get('pass', 0), resumo.get('fail', 0), resumo.get('info', 0)) if resumo else 'Diagnostico concluido'
                self.resultado.emit(ok, msg, diag)
                return
            if self._operacao == 'erase_frp':
                ok, msg = self._engine.erase_frp(self._porta, log_cb=_cb)
                self.resultado.emit(ok, msg, {})
                return
            if self._operacao == 'factory_reset':
                ok, msg = self._engine.factory_reset(self._porta, log_cb=_cb)
                self.resultado.emit(ok, msg, {})
                return
            if self._operacao == 'frp_erase_new':
                ok, msg = self._engine.frp_erase_new(self._porta, log_cb=_cb)
                self.resultado.emit(ok, msg, {})
                return
            if self._operacao == 'factory_reset_new':
                ok, msg = self._engine.factory_reset_new(self._porta, log_cb=_cb)
                self.resultado.emit(ok, msg, {})
                return
            if self._operacao == 'remove_payjoy':
                ok, msg = self._engine.remove_payjoy(self._porta, log_cb=_cb)
                self.resultado.emit(ok, msg, {})
                return
            if self._operacao == 'reboot':
                ok, msg = self._engine.reboot(self._porta, log_cb=_cb)
                self.resultado.emit(ok, msg, {})
                return
            if self._operacao == 'factory_reset_2026':
                if not self._engine_2026:
                    self.resultado.emit(False, 'Modulo 2026 indisponivel', {})
                    return
                ok, msg = self._engine_2026.factory_reset_2026(self._porta, log_cb=_cb)
                self.resultado.emit(ok, msg, {})
                return
            if self._operacao == 'remove_payjoy_2026':
                if not self._engine_2026:
                    self.resultado.emit(False, 'Modulo 2026 indisponivel', {})
                    return
                ok, msg = self._engine_2026.remove_payjoy_2026(self._porta, log_cb=_cb, save_dir=self._save_dir)
                self.resultado.emit(ok, msg, {})
                return
        except Exception:
            self.resultado.emit(False, 'Falha na operacao', {})
class MitWidget(QWidget):
    '''Tela Meta Mode Tools ÔÇö sub-aba independente com terminal proprio.'''
    _BOOT_TIMEOUT_S = 120
    def __init__(self, parent=None):
        super().__init__(parent)
        self._engine = None
        self._engine_2026 = None
        self._worker = None
        self._em_execucao = False
        self._porta_meta = ''
        self._elapsed = 0
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_tick)
        self._setup_ui()
        self._init_engine()
        self._exibir_boas_vindas()
    def _init_engine(self):
        '''Inicializa engine com fallback defensivo.'''
        try:
            from .mit_engine import MitEngine
            eng = MitEngine()
            if eng.available:
                self._engine = eng
            else:
                self._log.erro('Modulo nao disponivel')
                self._desabilitar_todos()
        except Exception:
            self._engine = None
            self._log.erro('Modulo nao disponivel')
            self._desabilitar_todos()
        try:
            from .mit_engine_2026 import MitEngine2026
            eng2 = MitEngine2026()
            if eng2.available:
                self._engine_2026 = eng2
                return
        except Exception:
            self._engine_2026 = None
    def _desabilitar_todos(self):
        '''Desabilita todos os botoes.'''
        for btn in self._btn_boot, self._btn_read, self._btn_diag, self._btn_hw_diag, self._btn_frp, self._btn_factory, self._btn_frp_new, self._btn_factory_new, self._btn_pyj, self._btn_factory_2026, self._btn_pyj_2026, self._btn_reboot, self._btn_cancel:
            btn.setEnabled(False)
    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        titulo = QLabel('META MODE TOOLS')
        titulo.setFont(QFont('Segoe UI', 13, QFont.Bold))
        titulo.setStyleSheet(f'color: {_ACCENT!s}; background: {BG_WHITE!s}; padding: 10px 16px; border-bottom: 1px solid {BORDER!s};')
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
        inner.setStyleSheet('background-color: %s;' % BG_WHITE)
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(8)
        g1, g1_lay = self._group('CONECTAR DISPOSITIVO ÔÇö Passo 1')
        g1_lay.addWidget(self._hint('Conecte desligado via USB e clique em Conectar.'))
        self._btn_boot = self._botao_sm('CONECTAR', gerar_qss_botao())
        self._btn_boot.clicked.connect(self._on_boot)
        g1_lay.addWidget(self._btn_boot)
        lay.addWidget(g1)
        g2, g2_lay = self._group('INFORMACOES ÔÇö Passo 2')
        row2 = QHBoxLayout()
        row2.setSpacing(4)
        self._btn_read = self._botao_sm('LER INFO', gerar_qss_botao())
        self._btn_read.clicked.connect(self._on_read)
        row2.addWidget(self._btn_read)
        self._btn_diag = self._botao_sm('DIAGNOSTICO', gerar_qss_botao_outline())
        self._btn_diag.clicked.connect(self._on_diag)
        row2.addWidget(self._btn_diag)
        g2_lay.addLayout(row2)
        self._btn_hw_diag = self._botao_sm('DIAGNOSTICO HARDWARE', gerar_qss_botao_outline())
        self._btn_hw_diag.clicked.connect(self._on_hw_diag)
        g2_lay.addWidget(self._btn_hw_diag)
        lay.addWidget(g2)
        g3, g3_lay = self._group('OPERACOES ÔÇö Passo 3')
        row3a = QHBoxLayout()
        row3a.setSpacing(4)
        self._btn_frp = self._botao_sm('FRP', gerar_qss_botao())
        self._btn_frp.clicked.connect(self._on_frp)
        row3a.addWidget(self._btn_frp)
        self._btn_factory = self._botao_sm('RESET FABRICA', gerar_qss_botao_outline())
        self._btn_factory.clicked.connect(self._on_factory)
        row3a.addWidget(self._btn_factory)
        g3_lay.addLayout(row3a)
        row3b = QHBoxLayout()
        row3b.setSpacing(4)
        self._btn_frp_new = self._botao_sm('FRP NEW', gerar_qss_botao())
        self._btn_frp_new.clicked.connect(self._on_frp_new)
        row3b.addWidget(self._btn_frp_new)
        self._btn_factory_new = self._botao_sm('FACTORY NEW', gerar_qss_botao_outline())
        self._btn_factory_new.clicked.connect(self._on_factory_new)
        row3b.addWidget(self._btn_factory_new)
        g3_lay.addLayout(row3b)
        self._btn_pyj = self._botao_sm('PYJ (2026)', gerar_qss_botao_outline())
        self._btn_pyj.clicked.connect(self._on_pyj)
        g3_lay.addWidget(self._btn_pyj)
        lay.addWidget(g3)
        g4, g4_lay = self._group('NEW SEC 08/2026')
        hint_2026 = QLabel('Conexao automatica ÔÇö nao requer CONECTAR  |  Testado no Smart 20')
        hint_2026.setStyleSheet('color: #888; font-size: 10px; padding: 0 4px;')
        g4_lay.addWidget(hint_2026)
        row4 = QHBoxLayout()
        row4.setSpacing(4)
        self._btn_factory_2026 = self._botao_sm('FACTORY 08/2026', gerar_qss_botao())
        self._btn_factory_2026.clicked.connect(self._on_factory_2026)
        row4.addWidget(self._btn_factory_2026)
        self._btn_pyj_2026 = self._botao_sm('PYJ 07/2026', gerar_qss_botao_outline())
        self._btn_pyj_2026.clicked.connect(self._on_pyj_2026)
        row4.addWidget(self._btn_pyj_2026)
        g4_lay.addLayout(row4)
        lay.addWidget(g4)
        g5, g5_lay = self._group('CONTROLE')
        row5 = QHBoxLayout()
        row5.setSpacing(4)
        self._btn_reboot = self._botao_sm('REINICIAR', gerar_qss_botao_outline())
        self._btn_reboot.clicked.connect(self._on_reboot)
        row5.addWidget(self._btn_reboot)
        self._btn_cancel = QPushButton('CANCELAR')
        self._btn_cancel.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_cancel.setMinimumHeight(32)
        self._btn_cancel.setMaximumHeight(34)
        self._btn_cancel.setEnabled(False)
        self._btn_cancel.setStyleSheet('QPushButton { background: %s; color: white; border-radius: 4px; font-weight: bold; }QPushButton:disabled { background: #bdc3c7; color: #7f8c8d; }QPushButton:hover { background: #c62828; }' % RED)
        self._btn_cancel.clicked.connect(self._on_cancel)
        row5.addWidget(self._btn_cancel)
        g5_lay.addLayout(row5)
        lay.addWidget(g5)
        self._lbl_status = QLabel('Pronto.')
        self._lbl_status.setStyleSheet('color: %s; padding: 4px 0;' % TEXT_MUTED)
        lay.addWidget(self._lbl_status)
        lay.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(inner)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f'QScrollArea {{ background-color: {BG_WHITE!s}; border: none; }}QScrollBar:vertical {{ width: 6px; background: transparent; }}QScrollBar::handle:vertical {{ background: {BORDER!s}; border-radius: 3px; }}QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}')
        return scroll
    def _botao_sm(self, text, qss):
        '''Cria botao compacto (32px).'''
        btn = QPushButton(text)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.setMinimumHeight(32)
        btn.setMaximumHeight(34)
        btn.setStyleSheet(qss)
        return btn
    def _group(self, title):
        '''Cria grupo visual compacto.'''
        f = QFrame()
        f.setStyleSheet(f'QFrame {{ background-color: {BG!s}; border: 1px solid {BORDER!s}; border-radius: 6px; }}')
        outer = QVBoxLayout(f)
        outer.setContentsMargins(10, 8, 10, 8)
        outer.setSpacing(4)
        t = QLabel(title)
        t.setFont(QFont('Segoe UI', 8, QFont.Bold))
        t.setStyleSheet('color: %s; border: none; background: transparent;' % PRIMARY)
        outer.addWidget(t)
        return f, outer
    def _hint(self, text):
        '''Cria label de dica compacta.'''
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setFont(QFont('Segoe UI', 8))
        lbl.setStyleSheet('color: %s; border: none; background: transparent;' % TEXT_MUTED)
        return lbl
    def _criar_terminal(self) -> QWidget:
        '''Cria area de terminal (logs).'''
        frame = QFrame()
        frame.setStyleSheet('background-color: #1a1a2e; border-left: 1px solid %s;' % BORDER)
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(6)
        hdr = QHBoxLayout()
        lbl = QLabel('LOGS')
        lbl.setFont(QFont('Segoe UI', 10, QFont.Bold))
        lbl.setStyleSheet('color: %s;' % WHITE)
        hdr.addWidget(lbl)
        hdr.addStretch()
        btn_limpar = QPushButton('Limpar')
        btn_limpar.setCursor(QCursor(Qt.PointingHandCursor))
        btn_limpar.setFixedHeight(26)
        btn_limpar.setStyleSheet('QPushButton { background: #2c3e50; color: %s; border: none; border-radius: 4px; padding: 2px 10px; }QPushButton:hover { background: #34495e; }' % WHITE)
        btn_limpar.clicked.connect(self._limpar_log)
        hdr.addWidget(btn_limpar)
        lay.addLayout(hdr)
        self._log = LogSeguro()
        self._log.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        lay.addWidget(self._log, stretch=1)
        return frame
    def _exibir_boas_vindas(self):
        self._log.info('Tech Union Solutions ÔÇö Meta Mode Tools')
        self._log.aviso(_DISCLAIMER)
        self._log.aviso(_LEGALIDADE)
        self._log.separador()
        self._log.info('Pronto.')
    def _limpar_log(self):
        self._log.limpar()
        self._exibir_boas_vindas()
    def _set_busy(self, busy):
        self._em_execucao = busy
        for btn in self._btn_boot, self._btn_read, self._btn_diag, self._btn_hw_diag, self._btn_frp, self._btn_factory, self._btn_frp_new, self._btn_factory_new, self._btn_pyj, self._btn_factory_2026, self._btn_pyj_2026, self._btn_reboot:
            btn.setEnabled(not busy)
        self._btn_cancel.setEnabled(busy)
        if busy:
            self._elapsed = 0
            self._timer.start()
            self._lbl_status.setText('Processando... (0s)')
            return
        self._timer.stop()
        self._lbl_status.setText('Pronto.')
    def _on_tick(self):
        '''Atualiza contador a cada segundo.'''
        self._elapsed += 1
        self._lbl_status.setText('Processando... (%ds)' % self._elapsed)
        if self._elapsed >= self._BOOT_TIMEOUT_S:
            if self._em_execucao:
                self._log.aviso('Tempo limite atingido (%ds). Cancele ou reconecte o dispositivo.' % self._elapsed)
                self._timer.stop()
    def _on_cancel(self):
        '''Cancela operacao em andamento de forma segura.'''
        if not self._em_execucao or not self._worker:
            return
        self._log.aviso('Cancelando operacao...')
        self._btn_cancel.setEnabled(False)
        self._worker.cancelar()
        if self._worker.isRunning():
            finished = self._worker.wait(5000)
            if not finished:
                self._log.aviso('For├ºando encerramento...')
                self._worker.terminate()
                self._worker.wait(2000)
        self._set_busy(False)
        self._log.info('Operacao cancelada.')
    def _on_worker_log(self, msg):
        if ': ' in msg:
            parts = msg.split(': ', 1)
            key = parts[0].strip()
            val = parts[1].strip()
            if key and val:
                self._log.prop(key, val)
                return
        self._log.info(msg)
    def _start_worker(self, operacao, save_dir=''):
        if self._em_execucao or not self._engine:
            return
        self._set_busy(True)
        self._worker = _WorkerThread(self._engine, operacao, self._porta_meta, engine_2026=self._engine_2026, save_dir=save_dir)
        self._worker.log.connect(self._on_worker_log)
        self._worker.resultado.connect(self._on_resultado)
        self._worker.start()
    def _on_resultado(self, ok, msg, info):
        elapsed = self._elapsed
        self._set_busy(False)
        if info.get('porta'):
            self._porta_meta = info['porta']
        if ok:
            if elapsed > 0:
                self._log.sucesso('%s (%ds)' % (msg, elapsed))
            else:
                self._log.sucesso(msg)
            self._lbl_status.setText(msg)
            return
        self._log.erro(msg)
        self._lbl_status.setText(msg)
        if msg:
            if 'dispositivo' in msg.lower() or 'disponivel' in msg.lower() or 'driver' in msg.lower():
                QMessageBox.warning(self, 'Aviso', msg)
    def _on_boot(self):
        self._log.info('Conectando ao dispositivo...')
        self._start_worker('boot_meta')
    def _on_read(self):
        if not self._porta_meta:
            QMessageBox.warning(self, 'Aviso', 'Conecte o dispositivo primeiro.')
            return
        self._log.info('Lendo informacoes...')
        self._start_worker('read_info')
    def _on_diag(self):
        if not self._porta_meta:
            QMessageBox.warning(self, 'Aviso', 'Conecte o dispositivo primeiro.')
            return
        self._log.info('Diagnosticando hardware...')
        self._start_worker('diagnostics')
    def _on_hw_diag(self):
        if not self._porta_meta:
            QMessageBox.warning(self, 'Aviso', 'Conecte o dispositivo primeiro.')
            return
        self._log.separador()
        self._log.info('Iniciando diagnostico completo de hardware...')
        self._start_worker('hw_diagnostics')
    def _on_frp(self):
        if not self._porta_meta:
            QMessageBox.warning(self, 'Aviso', 'Conecte o dispositivo primeiro.')
            return
        resp = QMessageBox.warning(self, 'Confirmar operacao', 'ATENCAO: Esta operacao ira remover a protecao.\n\nUse somente em aparelhos proprios ou com\nautorizacao do proprietario.\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resp != QMessageBox.Yes:
            return
        self._log.info('Processando...')
        self._start_worker('erase_frp')
    def _on_factory(self):
        if not self._porta_meta:
            QMessageBox.warning(self, 'Aviso', 'Conecte o dispositivo primeiro.')
            return
        resp = QMessageBox.warning(self, 'Confirmar operacao', 'ATENCAO: Esta operacao apaga TODOS os dados!\n\nO dispositivo sera reiniciado automaticamente.\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resp != QMessageBox.Yes:
            return
        self._log.info('Executando reset...')
        self._start_worker('factory_reset')
    def _on_frp_new(self):
        if not self._porta_meta:
            QMessageBox.warning(self, 'Aviso', 'Conecte o dispositivo primeiro.')
            return
        resp = QMessageBox.warning(self, 'Termo de responsabilidade', 'Ao prosseguir, voce declara que:\n\n- O aparelho e de sua propriedade ou possui\n  autorizacao expressa do proprietario.\n- Assume total responsabilidade pelo uso.\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resp != QMessageBox.Yes:
            return
        self._log.info('Processando...')
        self._start_worker('frp_erase_new')
    def _on_factory_new(self):
        if not self._porta_meta:
            QMessageBox.warning(self, 'Aviso', 'Conecte o dispositivo primeiro.')
            return
        resp = QMessageBox.warning(self, 'Termo de responsabilidade', 'Ao prosseguir, voce declara que:\n\n- O aparelho e de sua propriedade ou possui\n  autorizacao expressa do proprietario.\n- Esta ciente que TODOS os dados serao apagados.\n- Assume total responsabilidade pelo uso.\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resp != QMessageBox.Yes:
            return
        self._log.info('Executando reset...')
        self._start_worker('factory_reset_new')
    def _on_pyj(self):
        if not self._porta_meta:
            QMessageBox.warning(self, 'Aviso', 'Conecte o dispositivo primeiro.')
            return
        resp = QMessageBox.warning(self, 'Termo de responsabilidade ÔÇö EXPERIMENTAL', 'ATENCAO: Esta funcionalidade e EXPERIMENTAL.\n\nTestada ate o momento em:\n  - Infinix X6532 (MT6768)\n  - TECNO KL5 (MT6768)\n\nRISCOS:\n  - Pode causar danos irreversiveis (brick).\n  - Pode nao funcionar em outros modelos.\n  - Escrita incorreta na particao pode\n    comprometer o dispositivo.\n\nAo prosseguir, voce declara que:\n  - O aparelho e de sua propriedade ou possui\n    autorizacao expressa do proprietario.\n  - Assume TOTAL responsabilidade pelo uso.\n  - Esta ciente dos riscos acima.\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resp != QMessageBox.Yes:
            return
        self._log.info('Processando operacao experimental...')
        self._start_worker('remove_payjoy')
    def _on_factory_2026(self):
        if not self._engine_2026:
            QMessageBox.warning(self, 'Aviso', 'Modulo 2026 nao disponivel.')
            return
        resp = QMessageBox.warning(self, 'Termo de responsabilidade', 'Ao prosseguir, voce declara que:\n\n- O aparelho e de sua propriedade ou possui\n  autorizacao expressa do proprietario.\n- Esta ciente que TODOS os dados serao apagados.\n- Assume total responsabilidade pelo uso.\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resp != QMessageBox.Yes:
            return
        self._engine._close_serial()
        self._log.info('Executando reset 2026...')
        self._start_worker('factory_reset_2026')
    def _on_pyj_2026(self):
        if not self._engine_2026:
            QMessageBox.warning(self, 'Aviso', 'Modulo 2026 nao disponivel.')
            return
        resp = QMessageBox.warning(self, 'Termo de responsabilidade', 'ATENCAO: Operacao avancada.\n\nAo prosseguir, voce declara que:\n  - O aparelho e de sua propriedade ou possui\n    autorizacao expressa do proprietario.\n  - Assume TOTAL responsabilidade pelo uso.\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resp != QMessageBox.Yes:
            return
        import os
        default_dir = os.path.join(os.path.expanduser('~'), 'Documents')
        save_dir = QFileDialog.getExistingDirectory(self, 'Escolha onde salvar a particao', default_dir)
        if not save_dir:
            return
        self._engine._close_serial()
        self._log.info('Processando operacao 2026...')
        self._start_worker('remove_payjoy_2026', save_dir=save_dir)
    def _on_reboot(self):
        if not self._porta_meta:
            QMessageBox.warning(self, 'Aviso', 'Conecte o dispositivo primeiro.')
            return
        self._log.info('Reiniciando...')
        self._start_worker('reboot')
    def closeEvent(self, event):
        self._timer.stop()
        if self._worker and self._worker.isRunning():
            self._worker.cancelar()
            self._worker.wait(3000)
            if self._worker.isRunning():
                self._worker.terminate()
        if self._engine:
            try:
                self._engine.cancel()
            except Exception:
                pass
        if self._engine_2026:
            try:
                self._engine_2026.cancel()
            except Exception:
                pass
        super().closeEvent(event)
