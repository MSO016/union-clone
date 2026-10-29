import logging
import os
import threading
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QLabel, QPushButton, QSplitter, QSizePolicy, QMessageBox, QScrollArea, QComboBox)
from PyQt5.QtCore import (Qt, QThread, QTimer, pyqtSignal, pyqtSlot, QSize)
from PyQt5.QtGui import (QFont, QCursor, QIcon)
from app.views.union_unlock.exy.gui.tema import (gerar_qss_botao, gerar_qss_botao_outline, gerar_qss_principal, BG, BG_WHITE, PRIMARY, BORDER, TEXT, TEXT_MUTED, GREEN, RED, WHITE, ACCENT, _OBJ_NAME)
try:
    from app.views.union_unlock.hxd.gui.log_seguro import LogSeguro
except ImportError:
    LogSeguro = None
from app.views.union_unlock.exy.engine.preset_manager import PresetManager
from app.views.union_unlock.exy.engine.exynos_engine import ExynosEngine
from app.views.union_unlock.exy.engine import (device_detector, adb_ops, _cfg, exynos_tools_loader)
_log = logging.getLogger(__name__)
def _resolve_seta_svg() -> str:
    try:
        _svg = None
        try:
            from app.utils.path_manager import PathManager
            _candidate = PathManager.get_resource_path(os.path.join('icons_svg', 'seta_down.svg'))
            if _candidate and os.path.isfile(_candidate):
                _svg = os.path.normpath(_candidate).replace('\\', '/')
        except Exception:
            pass
        else:
            if not _svg:
                _base = os.path.dirname(os.path.abspath(__file__))
                _svg = os.path.normpath(os.path.join(_base, '..', '..', '..', '..', 'resources', 'icons_svg', 'seta_down.svg')).replace('\\', '/')
            if os.path.isfile(_svg):
                pass
    except Exception:
        pass
    return ''
_SETA_QSS = _resolve_seta_svg()
_DISCLAIMER = 'AVISO LEGAL: Esta ferramenta e destinada a tecnicos qualificados. O uso incorreto pode causar danos irreversiveis ao dispositivo. TECH UNION SOLUTIONS nao se responsabiliza por uso indevido.'
_LEGALIDADE = 'Dica: Use somente em aparelhos proprios ou com autorizacao do proprietario. Solicite nota fiscal ou termo de responsabilidade ao cliente.'
class _WorkerThread(QThread):
    log = pyqtSignal(str)
    resultado = pyqtSignal(bool, str, dict)
    def __init__(self, operacao, engine, preset_mgr, port='', chipset='', cancel_event=None):
        super().__init__()
        self._op = operacao
        self._engine = engine
        self._preset_mgr = preset_mgr
        self._port = port
        self._chipset = chipset
        self._cancel = cancel_event
    def cancelar(self):
        if self._cancel:
            self._cancel.set()
        if self._engine:
            self._engine.cancel()
    def _fresh_detect_port(self, _cb) -> str:
        _cb('Buscando dispositivo em Download Mode...')
        dev = device_detector.detect_samsung_modem(log_cb=_cb)
        if not dev or not dev.com_port:
            self.resultado.emit(False, 'Dispositivo nao encontrado em Download Mode.\nVerifique USB e tente novamente.', {})
            return ''
        try:
            dvif = device_detector.read_device_info_odin(dev.com_port, log_cb=_cb)
            if dvif.get('MODEL'):
                _cb(f'Dispositivo: {dvif['MODEL']}')
        except Exception:
            _log.debug('DVIF pre-cli falhou ÔÇö continuando', exc_info=True)
        return dev.com_port
        return dev.com_port
    def run(self):
        def _cb(msg):
            self.log.emit(msg)
        try:
            if self._op == 'detect':
                dev = device_detector.auto_detect(log_cb=_cb)
                if dev:
                    self.resultado.emit(True, dev.display_name, {'port': dev.com_port, 'model': dev.model, 'mode': dev.mode})
                    return
                self.resultado.emit(False, 'Nenhum dispositivo detectado', {})
                return
            if self._op == 'reboot_download':
                old_port = self._port
                ok = device_detector.reboot_to_download(old_port, log_cb=_cb)
                if not ok:
                    self.resultado.emit(False, 'Falha ao enviar comando de reboot', {})
                    return
                dev = device_detector.wait_download_mode(timeout_s=30, log_cb=_cb, cancel_event=self._cancel, old_port=old_port)
                if dev:
                    self.resultado.emit(True, 'Dispositivo em Download Mode', {'port': dev.com_port, 'mode': 'download', 'model': dev.model})
                    return
                self.resultado.emit(False, 'Dispositivo nao reapareceu ÔÇö verifique USB e clique DETECTAR', {})
                return
            if self._op == 'enable_adb':
                port = self._fresh_detect_port(_cb)
                if not port:
                    return
                adb_ops.sync_adb_key(engine_dir=str(_cfg.ENGINE_DIR), log_cb=_cb)
                json_path = self._preset_mgr.get_json_path(self._chipset)
                if not json_path:
                    self.resultado.emit(False, 'Configuracao do processador nao encontrada.\nVerifique a conexao de internet.', {})
                    return
                ok, msg, code = self._engine.boot_ramdisk(port, json_path, log_cb=_cb)
                self._preset_mgr.limpar_preset_temporario(self._chipset)
                self.resultado.emit(ok, msg, {'exit_code': code, 'port': port, 'mode': 'download'})
                return
            if self._op == 'adb_frp':
                port = self._fresh_detect_port(_cb)
                if not port:
                    return
                adb_ops.sync_adb_key(engine_dir=str(_cfg.ENGINE_DIR), log_cb=_cb)
                json_path = self._preset_mgr.get_json_path(self._chipset)
                if not json_path:
                    self.resultado.emit(False, 'Configuracao do processador nao encontrada.\nVerifique a conexao de internet.', {})
                    return
                _cb('Iniciando exploit. Isso pode levar alguns minutos...')
                _cb('Preparando ramdisk personalizado...')
                ok, msg, code = self._engine.boot_ramdisk(port, json_path, log_cb=_cb)
                self._preset_mgr.limpar_preset_temporario(self._chipset)
                if not ok:
                    self.resultado.emit(False, f'Falha na preparacao: {msg}', {'exit_code': code})
                    return
                if self._cancel and self._cancel.is_set():
                    self.resultado.emit(False, 'Cancelado', {})
                    return
                _cb('Aguardando dispositivo reiniciar...')
                if not adb_ops.wait_for_device(timeout=120, log_cb=_cb, cancel_event=self._cancel, initial_delay=8.0):
                    self.resultado.emit(False, "Dispositivo nao respondeu.\nToque 'Permitir depuracao USB' se aparecer no aparelho.", {})
                    return
                adb_ops.read_adb_device_info(log_cb=_cb)
                _cb('Limpando dados de protecao...')
                ok, msg = adb_ops.push_frp(log_cb=_cb, cancel_event=self._cancel)
                self.resultado.emit(ok, msg, {})
                return
            if self._op == 'remove_frp_adb':
                _cb('Verificando ADB...')
                if not adb_ops.wait_for_device(timeout=30, log_cb=_cb, cancel_event=self._cancel):
                    self.resultado.emit(False, 'Nenhum dispositivo ADB', {})
                    return
                ok, msg = adb_ops.push_frp(log_cb=_cb, cancel_event=self._cancel)
                self.resultado.emit(ok, msg, {})
                return
        except Exception as exc:
            _log.error('WorkerThread erro: %s', exc, exc_info=True)
            self.resultado.emit(False, 'Ocorreu um erro inesperado.\nVerifique a conexao USB e tente novamente.', {})
class ExyMainWidget(QWidget):
    _BOOT_TIMEOUT_S = 300
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName(_OBJ_NAME)
        self._preset_mgr = PresetManager()
        self._engine = None
        self._worker = None
        self._em_execucao = False
        self._device_port = ''
        self._device_mode = ''
        self._elapsed = 0
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_tick)
        self._setup_ui()
        self._inicializar_ambiente()
        self._exibir_boas_vindas()
    def _setup_ui(self):
        self.setStyleSheet(gerar_qss_principal())
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        titulo = QLabel('SAMSUNG EXYNOS FRP (TESTE)')
        titulo.setFont(QFont('Segoe UI', 13, QFont.Bold))
        titulo.setStyleSheet(f'color: {ACCENT!s}; background: {BG_WHITE!s}; padding: 10px 16px; border-bottom: 1px solid {BORDER!s};')
        root.addWidget(titulo)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._criar_controles())
        splitter.addWidget(self._criar_terminal())
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        root.addWidget(splitter, stretch=1)
    def _svg_icon(self, name: str) -> QIcon:
        try:
            from app.utils.path_manager import PathManager
            icons = PathManager.get_resource_path('icons_svg')
            if icons:
                p = os.path.join(icons, name)
                if os.path.isfile(p):
                    return QIcon(p)
        except Exception:
            pass
        return QIcon()
    def _criar_controles(self) -> QWidget:
        inner = QWidget()
        inner.setStyleSheet('background-color: %s;' % BG_WHITE)
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(8)
        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        g1, g1_lay = self._group('PROCESSADOR')
        g1_lay.addWidget(self._hint('Selecione o chipset Exynos'))
        self._combo_chipset = QComboBox()
        self._combo_chipset.setMinimumHeight(32)
        _combo_qss = f'QComboBox {{ background: {BG!s}; color: {TEXT!s}; border: 1px solid {BORDER!s}; border-radius: 4px; padding: 4px 24px 4px 8px; font-size: 12px; }}QComboBox::drop-down {{ border: none; width: 24px; }}QComboBox QAbstractItemView {{ background: {BG_WHITE!s}; color: {TEXT!s}; selection-background-color: {PRIMARY!s}; }}'
        if _SETA_QSS:
            _combo_qss += _SETA_QSS
        self._combo_chipset.setStyleSheet(_combo_qss)
        g1_lay.addWidget(self._combo_chipset)
        top_row.addWidget(g1, stretch=1)
        g2, g2_lay = self._group('DISPOSITIVO')
        self._lbl_device = QLabel('Nenhum dispositivo')
        self._lbl_device.setFont(QFont('Segoe UI', 9))
        self._lbl_device.setStyleSheet('color: %s; border: none; background: transparent;' % TEXT)
        g2_lay.addWidget(self._lbl_device)
        self._btn_detect = self._botao_sm('DETECTAR', gerar_qss_botao())
        self._btn_detect.setIcon(self._svg_icon('usb-plug.svg'))
        self._btn_detect.setIconSize(QSize(16, 16))
        self._btn_detect.clicked.connect(self._on_detect)
        g2_lay.addWidget(self._btn_detect)
        top_row.addWidget(g2, stretch=1)
        lay.addLayout(top_row)
        g3, g3_lay = self._group('OPERACOES')
        grid = QGridLayout()
        grid.setSpacing(4)
        self._btn_reboot_dl = self._botao_sm('Reboot Download', gerar_qss_botao_outline())
        self._btn_reboot_dl.setIcon(self._svg_icon('power.svg'))
        self._btn_reboot_dl.setIconSize(QSize(14, 14))
        self._btn_reboot_dl.clicked.connect(self._on_reboot_download)
        grid.addWidget(self._btn_reboot_dl, 0, 0)
        self._btn_enable_adb = self._botao_sm('Enable ADB', gerar_qss_botao())
        self._btn_enable_adb.setIcon(self._svg_icon('lightning-charge.svg'))
        self._btn_enable_adb.setIconSize(QSize(14, 14))
        self._btn_enable_adb.clicked.connect(self._on_enable_adb)
        grid.addWidget(self._btn_enable_adb, 0, 1)
        self._btn_adb_frp = self._botao_sm('ADB + FRP One-Click', gerar_qss_botao())
        self._btn_adb_frp.setIcon(self._svg_icon('shield-fill-check.svg'))
        self._btn_adb_frp.setIconSize(QSize(14, 14))
        self._btn_adb_frp.clicked.connect(self._on_adb_frp)
        grid.addWidget(self._btn_adb_frp, 1, 0)
        self._btn_remove_frp = self._botao_sm('Remover FRP (ADB)', gerar_qss_botao_outline())
        self._btn_remove_frp.setIcon(self._svg_icon('shield-lock.svg'))
        self._btn_remove_frp.setIconSize(QSize(14, 14))
        self._btn_remove_frp.clicked.connect(self._on_remove_frp_adb)
        grid.addWidget(self._btn_remove_frp, 1, 1)
        g3_lay.addLayout(grid)
        lay.addWidget(g3)
        g4, g4_lay = self._group('CONTROLE')
        row = QHBoxLayout()
        row.setSpacing(4)
        self._btn_cancel = QPushButton('CANCELAR')
        self._btn_cancel.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_cancel.setMinimumHeight(32)
        self._btn_cancel.setMaximumHeight(34)
        self._btn_cancel.setEnabled(False)
        self._btn_cancel.setStyleSheet('QPushButton { background: %s; color: white; border-radius: 4px; font-weight: bold; }QPushButton:disabled { background: #bdc3c7; color: #7f8c8d; }QPushButton:hover { background: #c62828; }' % RED)
        self._btn_cancel.clicked.connect(self._on_cancel)
        row.addWidget(self._btn_cancel)
        self._btn_reboot = self._botao_sm('REINICIAR', gerar_qss_botao_outline())
        self._btn_reboot.setIcon(self._svg_icon('arrow-clockwise.svg'))
        self._btn_reboot.setIconSize(QSize(14, 14))
        self._btn_reboot.clicked.connect(self._on_reboot)
        row.addWidget(self._btn_reboot)
        g4_lay.addLayout(row)
        lay.addWidget(g4)
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
        btn = QPushButton(text)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.setMinimumHeight(32)
        btn.setMaximumHeight(34)
        btn.setStyleSheet(qss)
        return btn
    def _group(self, title):
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
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setFont(QFont('Segoe UI', 8))
        lbl.setStyleSheet('color: %s; border: none; background: transparent;' % TEXT_MUTED)
        return lbl
    def _criar_terminal(self) -> QWidget:
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
        if LogSeguro is not None:
            self._log_widget = LogSeguro()
        else:
            from PyQt5.QtWidgets import QTextEdit
            self._log_widget = QTextEdit()
            self._log_widget.setReadOnly(True)
        self._log_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        lay.addWidget(self._log_widget, stretch=1)
        return frame
    def _log_info(self, msg: str):
        if hasattr(self._log_widget, 'info'):
            self._log_widget.info(msg)
            return
        self._log_widget.append(msg)
    def _log_erro(self, msg: str):
        if hasattr(self._log_widget, 'erro'):
            self._log_widget.erro(msg)
            return
        self._log_widget.append(f'[ERRO] {msg}')
    def _log_sucesso(self, msg: str):
        if hasattr(self._log_widget, 'sucesso'):
            self._log_widget.sucesso(msg)
            return
        self._log_widget.append(f'[OK] {msg}')
    def _log_aviso(self, msg: str):
        if hasattr(self._log_widget, 'aviso'):
            self._log_widget.aviso(msg)
            return
        self._log_widget.append(f'[AVISO] {msg}')
    def _log_prop(self, key: str, val: str):
        if hasattr(self._log_widget, 'prop'):
            self._log_widget.prop(key, val)
            return
        self._log_widget.append(f'  {key}: {val}')
    def _log_separador(self):
        if hasattr(self._log_widget, 'separador'):
            self._log_widget.separador()
            return
        self._log_widget.append('ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ')
    def _log_limpar(self):
        if hasattr(self._log_widget, 'limpar'):
            self._log_widget.limpar()
            return
        self._log_widget.clear()
    _DOWNLOAD_MSG_MAP = {'Baixando recursos...': None, 'Verificando ferramentas Exynos...': 'Verificando componentes...', 'Antivirus detectado ÔÇö extraindo em pasta segura...': 'Ajustando ambiente...', 'Solicitando exclusao de antivirus...': 'Configurando protecoes...'}
    def _progress_cb(self, pct: int, msg: str):
        if msg.startswith('Extraindo'):
            mapped = f'Processando dados... ({pct}%)' if pct > 0 else 'Processando dados...'
            if getattr(self, '_last_extract_pct', -1) == pct:
                return
            self._last_extract_pct = pct
            self._log_info(mapped)
            return
        mapped = self._DOWNLOAD_MSG_MAP.get(msg, msg)
        if mapped is None:
            if pct <= 10:
                mapped = 'Sincronizando srv1...'
            elif pct <= 50:
                mapped = 'Sincronizando srv2...'
            elif pct <= 80:
                mapped = 'Processando dados...'
            else:
                mapped = 'Finalizando...'
            if getattr(self, '_last_sync_msg', '') == mapped:
                return
            self._last_sync_msg = mapped
        self._log_info(mapped)
    def _inicializar_ambiente(self):
        if not exynos_tools_loader.cli_disponivel():
            self._log_info('Preparando ambiente...')
            self._last_sync_msg = ''
            ok = exynos_tools_loader.garantir_tools(progress_callback=self._progress_cb)
            if not ok and not exynos_tools_loader.cli_disponivel():
                self._log_erro('O antivirus pode ter bloqueado componentes necessarios.\nTente executar o aplicativo como Administrador.\nSe o problema persistir, adicione uma exclusao no seu antivirus\npara a pasta do aplicativo.')
        _cfg.ENGINE_DIR = _cfg._resolve_engine_dir()
        _cfg.CLI_EXE_PATH = _cfg.ENGINE_DIR / _cfg.CLI_EXE
        self._engine = ExynosEngine()
        self._preset_mgr.sincronizar()
        self._carregar_chipsets()
    @pyqtSlot()
    def _carregar_chipsets(self):
        chipsets = self._preset_mgr.list_chipsets()
        self._combo_chipset.clear()
        if chipsets:
            for cs in chipsets:
                preset = self._preset_mgr.load_preset(cs)
                label = preset.display_name if preset else cs
                self._combo_chipset.addItem(label, cs)
            return
        self._combo_chipset.addItem('Nenhum processador disponivel', '')
    def _exibir_boas_vindas(self):
        self._log_info('Tech Union Solutions ÔÇö Samsung Exynos FRP')
        self._log_aviso(_DISCLAIMER)
        self._log_aviso(_LEGALIDADE)
        self._log_separador()
        cli_ok = self._engine.cli_available if self._engine else False
        n_processadores = self._combo_chipset.count()
        sync_ok = self._preset_mgr.usando_sync
        if cli_ok:
            self._log_prop('Status', 'Pronto para uso')
        else:
            self._log_prop('Status', 'Indisponivel')
        self._log_prop('CPUs suportadas', f'{n_processadores} ({'servidor on' if sync_ok else 'offline'})')
        if not cli_ok:
            self._log_erro('Reinstale o aplicativo ou verifique seu antivirus\npara comecar a usar esta ferramenta.')
        self._log_separador()
        self._log_info('Pronto. Selecione o processador e detecte o dispositivo.')
    def _limpar_log(self):
        self._log_limpar()
        self._exibir_boas_vindas()
    def _get_chipset(self) -> str:
        return self._combo_chipset.currentData() or ''
    def _operation_buttons(self):
        return self._btn_detect, self._btn_reboot_dl, self._btn_enable_adb, self._btn_adb_frp, self._btn_remove_frp, self._btn_reboot
    def _set_busy(self, busy):
        self._em_execucao = busy
        for btn in self._operation_buttons():
            btn.setEnabled(not busy)
        self._combo_chipset.setEnabled(not busy)
        self._btn_cancel.setEnabled(busy)
        if busy:
            self._elapsed = 0
            self._timer.start()
            self._lbl_status.setText('Processando... (0s)')
            return
        self._timer.stop()
        self._lbl_status.setText('Pronto.')
    def _on_tick(self):
        self._elapsed += 1
        self._lbl_status.setText('Processando... (%ds)' % self._elapsed)
        if self._elapsed >= self._BOOT_TIMEOUT_S:
            if self._em_execucao:
                self._log_aviso('Tempo limite atingido (%ds). Cancele ou reconecte o dispositivo.' % self._elapsed)
                self._timer.stop()
    def _on_cancel(self):
        if not self._em_execucao or not self._worker:
            return
        self._log_aviso('Cancelando operacao...')
        self._btn_cancel.setEnabled(False)
        self._worker.cancelar()
        if self._worker.isRunning():
            finished = self._worker.wait(5000)
            if not finished:
                self._log_aviso('Forcando encerramento...')
                self._worker.terminate()
                self._worker.wait(2000)
        self._set_busy(False)
        self._log_info('Operacao cancelada.')
    _CLI_MSG_FILTER = {'Waiting enabling adb': 'Habilitando acesso ao dispositivo...', 'result: true': 'Dispositivo respondeu com sucesso', 'result: false': 'Dispositivo nao respondeu'}
    _LOG_BLOCK_TERMS = ('frp.bin', 'at+', '.exe', '.dll', '.json', '.zip', '.db', 'com port', 'win32', 'winerror', 'adbkey', 'ramdisks', '/dev/block', 'blockdev', 'getprop', 'adb push', 'adb shell', 'exynos', 'bridge', 'exynosbridgehost')
    @staticmethod
    def _has_path(text: str) -> bool:
        import re
        return bool(re.search('[A-Z]:\\\\|/dev/|%[A-Z]+%|\\\\\\\\[a-zA-Z]', text))
    def _on_worker_log(self, msg):
        low = msg.strip().lower()
        for pattern, replacement in self._CLI_MSG_FILTER.items():
            if low.startswith(pattern.lower()):
                self._log_info(replacement)
                return
        if any((t in low for t in self._LOG_BLOCK_TERMS)):
            _log.debug('Filtrado: %s', msg)
            return
        if self._has_path(msg):
            _log.debug('Filtrado (path): %s', msg)
            return
        if ': ' in msg:
            parts = msg.split(': ', 1)
            key = parts[0].strip()
            val = parts[1].strip()
            if key and val:
                self._log_prop(key, val)
                return
        self._log_info(msg)
    def _start_worker(self, operacao):
        if self._em_execucao:
            return
        cancel_ev = threading.Event()
        self._set_busy(True)
        self._worker = _WorkerThread(operacao=operacao, engine=self._engine, preset_mgr=self._preset_mgr, port=self._device_port, chipset=self._get_chipset(), cancel_event=cancel_ev)
        self._worker.log.connect(self._on_worker_log)
        self._worker.resultado.connect(self._on_resultado)
        self._worker.start()
    @staticmethod
    def _fmt_elapsed(s: int) -> str:
        if s < 60:
            return f'{s} segundo(s)'
        m, r = divmod(s, 60)
        return f'{m} minuto(s) {r} segundo(s)'
    def _on_resultado(self, ok, msg, info):
        elapsed = self._elapsed
        self._set_busy(False)
        if info.get('port'):
            self._device_port = info['port']
        if info.get('mode'):
            self._device_mode = info['mode']
        if info.get('model') or info.get('port'):
            mode_map = {'normal': 'NORMAL', 'download': 'DOWNLOAD', 'adb': 'ADB', 'modem': 'MODEM'}
            mode_label = mode_map.get(self._device_mode, self._device_mode.upper())
            model = info.get('model', '')
            parts = [model] if model else []
            parts.append(f'[{mode_label}]')
            self._lbl_device.setText(' '.join(parts))
        if ok:
            self._log_sucesso(msg)
            if elapsed > 0:
                self._log_info(f'Tempo de execucao {self._fmt_elapsed(elapsed)}')
            self._log_separador()
            self._log_info('Executado por TECH UNION SOLUTIONS v1.3.4')
            self._lbl_status.setText(msg)
            return
        self._log_erro(msg)
        self._lbl_status.setText(msg)
        if msg:
            if 'dispositivo' in msg.lower() or 'nao encontrad' in msg.lower():
                QMessageBox.warning(self, 'Aviso', msg)
    def _require_port(self) -> bool:
        if not self._device_port:
            QMessageBox.warning(self, 'Aviso', 'Detecte o dispositivo primeiro.')
            return False
        return True
    def _require_chipset(self) -> bool:
        cs = self._get_chipset()
        if not cs:
            QMessageBox.warning(self, 'Aviso', 'Selecione um processador Exynos.')
            return False
        return True
    def _confirmar_operacao(self, titulo, mensagem) -> bool:
        resp = QMessageBox.warning(self, titulo, mensagem, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        return resp == QMessageBox.Yes
    def _on_detect(self):
        self._log_info('Buscando dispositivo em download mode...')
        self._start_worker('detect')
    def _on_reboot_download(self):
        if not self._require_port():
            return
        if self._device_mode == 'download':
            QMessageBox.information(self, 'Informacao', "O dispositivo JA esta em Download Mode.\n\nUse 'ENABLE ADB' ou 'ADB + FRP ONE-CLICK'.")
            return
        self._log_separador()
        self._log_info('Desligando dispositivo...')
        self._log_info('Conectando em Download Mode...')
        self._start_worker('reboot_download')
    def _on_enable_adb(self):
        if not (self._require_port() and self._require_chipset()):
            return
        if not self._engine or not self._engine.cli_available:
            QMessageBox.warning(self, 'Erro', 'Ferramentas Exynos indisponiveis.\nVerifique sua conexao de internet e reinicie o aplicativo.')
            return
        if self._device_mode == 'normal':
            resp = QMessageBox.warning(self, 'Aviso', "O dispositivo parece estar em modo NORMAL.\n\nPara esta operacao, o dispositivo precisa estar em\nDOWNLOAD MODE (Odin Mode).\n\nUse 'REBOOT TO DOWNLOAD' primeiro, ou coloque o\ndispositivo manualmente em Download Mode.\n\nDeseja tentar mesmo assim?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if resp != QMessageBox.Yes:
                return
        self._log_separador()
        self._log_info('Iniciando exploit...')
        self._start_worker('enable_adb')
    def _on_adb_frp(self):
        if not (self._require_port() and self._require_chipset()):
            return
        if not self._engine or not self._engine.cli_available:
            QMessageBox.warning(self, 'Erro', 'Ferramentas Exynos indisponiveis.')
            return
        if self._device_mode == 'normal':
            QMessageBox.warning(self, 'Aviso', "O dispositivo esta em modo NORMAL.\nUse 'REBOOT TO DOWNLOAD' primeiro.")
            return
        if not self._confirmar_operacao('Confirmar operacao', 'ATENCAO: Esta operacao ira:\n  1. Enviar ramdisk personalizado\n  2. Configurar acesso ao dispositivo\n  3. Remover protecao automaticamente\n\nUse somente em aparelhos proprios ou com\nautorizacao do proprietario.\n\nDeseja continuar?'):
            return
        self._log_separador()
        self._log_info('Iniciando Reset FRP (Exynos Download Mode)')
        self._start_worker('adb_frp')
    def _on_remove_frp_adb(self):
        if not self._confirmar_operacao('Termo de responsabilidade', 'ATENCAO: Remove FRP via ADB direto.\n\nO dispositivo deve estar com ADB habilitado.\n\nAo prosseguir, voce declara que:\n- O aparelho e de sua propriedade ou possui\n  autorizacao expressa do proprietario.\n- Assume total responsabilidade pelo uso.\n\nDeseja continuar?'):
            return
        self._log_separador()
        self._log_info('Iniciando remocao de protecao...')
        self._start_worker('remove_frp_adb')
    def _on_reboot(self):
        self._log_info('Reiniciando dispositivo...')
        adb_ops.reboot_device(log_cb=(lambda m: self._log_info(m)))
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
        super().closeEvent(event)
