import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QComboBox, QPushButton, QSizePolicy, QMessageBox, QCompleter)
from PyQt5.QtCore import (Qt, QThread, QSize, pyqtSignal)
from PyQt5.QtGui import (QFont, QCursor, QFontMetrics, QIcon)
from .tema import (gerar_qss_botao, gerar_qss_botao_outline, BG, BG_WHITE, PRIMARY, UNION_BLUE, UNION_ACCENT, UNION_LIGHT, BORDER, TEXT, TEXT_MUTED, TEXT_LABEL, GREEN, RED, WHITE, HEADER_BG)
def _aplicar_icone_btn(btn, svg_relativo, tamanho=16):
    try:
        from app.utils.path_manager import PathManager
        caminho = PathManager.get_resource_path(svg_relativo)
        if caminho:
            if os.path.isfile(caminho):
                btn.setIcon(QIcon(caminho))
                btn.setIconSize(QSize(tamanho, tamanho))
                return
            return
    except Exception:
        pass
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
class _SyncThread(QThread):
    finished = pyqtSignal(bool, str)
    def __init__(self, engine, force=False):
        super().__init__()
        self._engine = engine
        self._force = force
    def run(self):
        try:
            ok, msg = self._engine.sync(force=self._force)
            self.finished.emit(ok, msg)
            return
        except Exception:
            self.finished.emit(False, 'Falha na conexao')
class _FrpThread(QThread):
    log = pyqtSignal(str)
    resultado = pyqtSignal(bool, str, dict)
    def __init__(self, engine, codename, serial_len=10, operacao='read_info'):
        super().__init__()
        self._engine = engine
        self._codename = codename
        self._serial_len = serial_len
        self._operacao = operacao
        self._cancelled = False
    def cancelar(self):
        self._cancelled = True
    def is_cancelled(self) -> bool:
        return self._cancelled
    def run(self):
        def _cb(msg):
            self.log.emit(msg)
        try:
            if self._operacao == 'read_info':
                info = self._engine.read_info(log_cb=_cb)
                if info.get('codename') or info.get('serial'):
                    self.resultado.emit(True, 'Leitura concluida', info)
                    return
                self.resultado.emit(False, 'Nenhum dispositivo detectado', info)
                return
            if self._operacao == 'frp_remove':
                ok, msg = self._engine.executar_frp(self._codename, serial_len=self._serial_len, log_cb=_cb, cancel_check=self.is_cancelled)
                self.resultado.emit(ok, msg, {})
                return
        except Exception:
            self.resultado.emit(False, 'Falha na operacao', {})
class MotoFrpFrame(QWidget):
    log_signal = pyqtSignal(str)
    def __init__(self, parent=None, log_callback=None):
        super().__init__(parent)
        self._log_cb = log_callback
        self._engine = None
        self._worker = None
        self._sync_worker = None
        self._modelos_data = []
        self._em_execucao = False
        self._android_detectado = 0
        self._setup_ui()
        self._init_engine()
    def _log(self, msg: str):
        if self._log_cb:
            self._log_cb(msg)
    def _cleanup_worker(self):
        if self._worker and self._worker.isRunning():
            self._worker.cancelar()
            self._worker.wait(5000)
        self._worker = None
    def closeEvent(self, event):
        self._cleanup_worker()
        super().closeEvent(event)
    def _init_engine(self):
        try:
            from ..core.engines.moto_frp_engine import MotoFrpEngine
            self._engine = MotoFrpEngine()
            self._fazer_sync(force=False)
            return
        except Exception:
            self._lbl_sync_status.setText('')
            self._btn_read.setEnabled(False)
            self._btn_frp.setEnabled(False)
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        sel_frame = QFrame()
        sel_frame.setStyleSheet(f'\n            QFrame {{\n                background-color: {BG};\n                border: 1px solid {BORDER};\n                border-radius: 8px;\n                padding: 4px;\n            }}\n        ')
        sel_layout = QVBoxLayout(sel_frame)
        sel_layout.setContentsMargins(10, 6, 10, 6)
        sel_layout.setSpacing(4)
        self._lbl_sync_status = QLabel('')
        self._lbl_sync_status.setFont(QFont('Segoe UI', 9))
        self._lbl_sync_status.setStyleSheet(f'color: {TEXT_MUTED};')
        self._lbl_sync_status.setAlignment(Qt.AlignRight)
        sel_layout.addWidget(self._lbl_sync_status)
        _lbl_font = QFont('Segoe UI', 10)
        _lbl_w = QFontMetrics(_lbl_font).horizontalAdvance('Modelo:') + 12
        row_modelo = QHBoxLayout()
        row_modelo.setSpacing(8)
        lbl_modelo = QLabel('Modelo:')
        lbl_modelo.setFont(_lbl_font)
        lbl_modelo.setStyleSheet(f'color: {TEXT_LABEL}; border: none; background: transparent;')
        lbl_modelo.setFixedWidth(_lbl_w)
        row_modelo.addWidget(lbl_modelo)
        self._combo_modelo = QComboBox()
        self._combo_modelo.setEditable(True)
        self._combo_modelo.setInsertPolicy(QComboBox.NoInsert)
        self._combo_modelo.setMinimumHeight(28)
        self._combo_modelo.setCursor(QCursor(Qt.PointingHandCursor))
        self._combo_modelo.setStyleSheet(self._qss_combo())
        self._combo_modelo.addItem('ÔÇö selecione ÔÇö')
        self._combo_modelo.lineEdit().setPlaceholderText('Buscar modelo...')
        self._combo_modelo.completer().setCompletionMode(QCompleter.PopupCompletion)
        self._combo_modelo.completer().setFilterMode(Qt.MatchContains)
        self._combo_modelo.currentIndexChanged.connect(self._on_modelo_changed)
        row_modelo.addWidget(self._combo_modelo, 1)
        sel_layout.addLayout(row_modelo)
        info_frame = QFrame()
        info_frame.setStyleSheet(f'\n            QFrame {{\n                background-color: {BG_WHITE};\n                border: 1px solid {BORDER};\n                border-radius: 6px;\n                padding: 4px;\n            }}\n        ')
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(8, 4, 8, 4)
        info_layout.setSpacing(1)
        self._lbl_modelo_info = QLabel('Codename: ÔÇö')
        self._lbl_modelo_info.setFont(QFont('Segoe UI', 9))
        self._lbl_modelo_info.setStyleSheet(f'color: {TEXT}; border: none; background: transparent;')
        self._lbl_modelo_info.setWordWrap(True)
        info_layout.addWidget(self._lbl_modelo_info)
        self._lbl_serial = QLabel('Serial: ÔÇö')
        self._lbl_serial.setFont(QFont('Segoe UI', 9))
        self._lbl_serial.setStyleSheet(f'color: {TEXT}; border: none; background: transparent;')
        self._lbl_serial.setWordWrap(True)
        info_layout.addWidget(self._lbl_serial)
        self._lbl_frp_status = QLabel('FRP: ÔÇö')
        self._lbl_frp_status.setFont(QFont('Segoe UI', 9, QFont.Bold))
        self._lbl_frp_status.setStyleSheet(f'color: {PRIMARY}; border: none; background: transparent;')
        self._lbl_frp_status.setWordWrap(True)
        info_layout.addWidget(self._lbl_frp_status)
        self._lbl_secure = QLabel('Secure: ÔÇö')
        self._lbl_secure.setFont(QFont('Segoe UI', 9))
        self._lbl_secure.setStyleSheet(f'color: {TEXT}; border: none; background: transparent;')
        self._lbl_secure.setWordWrap(True)
        info_layout.addWidget(self._lbl_secure)
        sel_layout.addWidget(info_frame)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        self._btn_read = QPushButton('Read Info')
        self._btn_read.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_read.setStyleSheet(gerar_qss_botao_outline())
        self._btn_read.setMinimumHeight(30)
        self._btn_read.setEnabled(False)
        _aplicar_icone_btn(self._btn_read, 'icons_svg/card-checklist.svg')
        self._btn_read.clicked.connect(self._on_read_info)
        btn_layout.addWidget(self._btn_read)
        self._btn_frp = QPushButton('FRP Unlock')
        self._btn_frp.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_frp.setStyleSheet(gerar_qss_botao())
        self._btn_frp.setMinimumHeight(30)
        self._btn_frp.setEnabled(False)
        _aplicar_icone_btn(self._btn_frp, 'icons_svg/shield-lock.svg')
        self._btn_frp.clicked.connect(self._on_frp_remove)
        btn_layout.addWidget(self._btn_frp)
        self._btn_cancel = QPushButton('Cancelar')
        self._btn_cancel.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_cancel.setStyleSheet(f"\n            QPushButton {{\n                background-color: transparent;\n                color: {RED};\n                border: 1px solid {RED};\n                border-radius: 6px;\n                padding: 6px 12px;\n                font-family: 'Segoe UI';\n                font-size: 11px;\n                font-weight: 600;\n            }}\n            QPushButton:hover {{\n                background-color: {RED};\n                color: {WHITE};\n            }}\n            QPushButton:disabled {{\n                border-color: {BORDER};\n                color: {TEXT_MUTED};\n            }}\n        ")
        self._btn_cancel.setMinimumHeight(30)
        self._btn_cancel.setEnabled(False)
        self._btn_cancel.setVisible(False)
        self._btn_cancel.clicked.connect(self._on_cancel)
        btn_layout.addWidget(self._btn_cancel)
        sel_layout.addLayout(btn_layout)
        layout.addWidget(sel_frame)
    def _qss_combo(self) -> str:
        return ''.join(['\n            QComboBox {\n                background-color: ', f'{BG_WHITE}', ';\n                color: ', f'{TEXT}', ';\n                border: 1px solid ', f'{BORDER}', ";\n                border-radius: 6px;\n                padding: 4px 8px;\n                font-size: 12px;\n                font-family: 'Segoe UI';\n                min-height: 22px;\n            }\n            QComboBox:hover {\n                border-color: ", f'{UNION_BLUE}', ';\n            }\n            QComboBox:disabled {\n                border-color: ', f'{BORDER}', ';\n                color: ', f'{TEXT_MUTED}', ';\n                background-color: ', f'{BG}', ';\n            }\n            QComboBox::drop-down {\n                border: none; width: 28px; padding-right: 6px;\n            }\n            QComboBox QAbstractItemView {\n                background-color: ', f'{BG_WHITE}', ';\n                color: ', f'{TEXT}', ';\n                selection-background-color: ', f'{UNION_BLUE}', ';\n                selection-color: ', f'{WHITE}', ';\n                border: 1px solid ', f'{BORDER}', ';\n                padding: 4px;\n                outline: none;\n            }\n            QComboBox QAbstractItemView::item {\n                min-height: 26px; padding: 3px 8px;\n            }\n            QComboBox QAbstractItemView::item:hover {\n                background-color: ', f'{UNION_LIGHT}', ';\n                color: ', f'{TEXT}', ';\n            }\n            QComboBox QLineEdit {\n                background: transparent;\n                border: none;\n                color: ', f'{TEXT}', ';\n                font-size: 12px;\n                padding: 0;\n            }\n            ', f'{_SETA_QSS}', '\n        '])
    def _fazer_sync(self, force=False):
        if not self._engine:
            return
        self._sync_worker = _SyncThread(self._engine, force)
        self._sync_worker.finished.connect(self._on_sync_done)
        self._sync_worker.start()
    def _on_sync_done(self, ok: bool, msg: str):
        if ok:
            self._lbl_sync_status.setText('Ô£ô Pronto')
            self._lbl_sync_status.setStyleSheet(f'color: {GREEN};')
        else:
            self._lbl_sync_status.setText('Ô£ô Pronto')
            self._lbl_sync_status.setStyleSheet(f'color: {TEXT_MUTED};')
        self._popular_modelos()
        self._btn_read.setEnabled(True)
    def force_sync(self):
        self._fazer_sync(force=True)
    def _popular_modelos(self):
        if not self._engine:
            return
        self._combo_modelo.blockSignals(True)
        self._combo_modelo.clear()
        self._modelos_data = []
        self._btn_frp.setEnabled(False)
        self._reset_info()
        self._modelos_data = self._engine.listar_modelos('Motorola')
        if self._modelos_data:
            self._combo_modelo.addItem('ÔÇö selecione ÔÇö')
            for m in self._modelos_data:
                label = f'{m['modelo']} ({m['codename']})'
                if m.get('status') == 'em_teste':
                    label += ' [teste]'
                self._combo_modelo.addItem(label)
        else:
            self._combo_modelo.addItem('ÔÇö nenhum modelo ÔÇö')
        self._combo_modelo.blockSignals(False)
    def _on_modelo_changed(self, idx: int):
        if idx <= 0 or idx > len(self._modelos_data):
            self._btn_frp.setEnabled(False)
            self._reset_info()
            return
        md = self._modelos_data[idx - 1]
        self._lbl_modelo_info.setText(f'Codename: {md['codename']}')
        self._lbl_serial.setText('Serial: ÔÇö')
        self._lbl_frp_status.setText('FRP: Aguardando leitura')
        self._lbl_frp_status.setStyleSheet(f'color: {PRIMARY}; border: none; background: transparent;')
        self._lbl_secure.setText('Secure: ÔÇö')
        self._btn_frp.setEnabled(True)
    def _reset_info(self):
        self._lbl_modelo_info.setText('Codename: ÔÇö')
        self._lbl_serial.setText('Serial: ÔÇö')
        self._lbl_frp_status.setText('FRP: ÔÇö')
        self._lbl_frp_status.setStyleSheet(f'color: {PRIMARY}; border: none; background: transparent;')
        self._android_detectado = 0
        self._lbl_secure.setText('Secure: ÔÇö')
    def _modelo_selecionado(self) -> dict:
        idx = self._combo_modelo.currentIndex()
        if idx <= 0 or idx > len(self._modelos_data):
            return {}
        return self._modelos_data[idx - 1]
    def _on_read_info(self):
        if not self._engine:
            return
        md = self._modelo_selecionado()
        self._set_busy(True)
        self._log('[MOTOROLA FRP] Lendo informacoes...')
        self._worker = _FrpThread(self._engine, md.get('codename', '') if md else '', serial_len=md.get('serial_len', 10) if md else 10, operacao='read_info')
        self._worker.log.connect(self._on_worker_log)
        self._worker.resultado.connect(self._on_read_done)
        self._worker.start()
    def _auto_select_by_codename(self, codename: str):
        if not codename or not self._modelos_data:
            return
        cn_low = codename.lower()
        best_idx = -1
        for i, m in enumerate(self._modelos_data):
            mc = m.get('codename', '').lower()
            if mc == cn_low:
                best_idx = i
                break
            if mc.startswith(cn_low + '-') or mc.startswith(cn_low + '_'):
                if best_idx < 0:
                    best_idx = i
        if best_idx >= 0:
            self._combo_modelo.blockSignals(True)
            self._combo_modelo.setCurrentIndex(best_idx + 1)
            self._combo_modelo.blockSignals(False)
            self._btn_frp.setEnabled(True)
    def _on_read_done(self, ok: bool, msg: str, info: dict):
        self._set_busy(False)
        if ok and info.get('codename'):
            cn = info.get('codename', 'ÔÇö')
            serial = info.get('serial', 'ÔÇö')
            frp = info.get('frp_state', 'ÔÇö')
            secure = info.get('secure', 'ÔÇö')
            sku = info.get('sku', '')
            android = info.get('android', '')
            if android and android.isdigit():
                self._android_detectado = int(android)
            else:
                self._android_detectado = 0
            self._auto_select_by_codename(cn)
            if not android:
                md_sel = self._modelo_selecionado()
                if md_sel and md_sel.get('android_version'):
                    android = f'~{md_sel['android_version']}'
            modelo_txt = f'Codename: {cn}'
            if sku:
                modelo_txt = f'{sku} ({cn})'
            self._lbl_modelo_info.setText(modelo_txt)
            serial_txt = f'Serial: {serial}'
            if android:
                serial_txt += f'  |  Android {android}'
            self._lbl_serial.setText(serial_txt)
            self._lbl_secure.setText(f'Secure: {secure}')
            if 'protected' in frp.lower():
                self._lbl_frp_status.setText(f'FRP: PROTEGIDO ({frp})')
                self._lbl_frp_status.setStyleSheet(f'color: {RED}; border: none; background: transparent; font-weight: bold;')
                return
            if 'no protection' in frp.lower():
                self._lbl_frp_status.setText('FRP: LIVRE Ô£ô')
                self._lbl_frp_status.setStyleSheet(f'color: {GREEN}; border: none; background: transparent; font-weight: bold;')
                return
            self._lbl_frp_status.setText(f'FRP: {frp}')
            self._lbl_frp_status.setStyleSheet(f'color: {PRIMARY}; border: none; background: transparent;')
            return
        self._lbl_frp_status.setText(f'FRP: {msg}')
        self._lbl_frp_status.setStyleSheet(f'color: {RED}; border: none; background: transparent;')
    def _on_frp_remove(self):
        if self._em_execucao:
            return
        md = self._modelo_selecionado()
        if not md:
            return
        lote_cn = ''
        av_lote = md.get('android_version') or 0
        if self._engine:
            lote_cn = self._engine._sync.get_lote_codename(md['codename'])
        is_secondary = lote_cn and md['codename'].lower() != lote_cn.lower()
        msg_aviso = f'ATEN├ç├âO: Esta opera├º├úo ir├í remover a prote├º├úo FRP.\n\nModelo: {md['modelo']}\nCodename: {md['codename']}\n'
        if av_lote:
            msg_aviso += f'Testado em: Android {av_lote}\n'
        if self._android_detectado and av_lote:
            if self._android_detectado < av_lote:
                msg_aviso += f'\nÔøö RISCO ALTO: Dispositivo com Android {self._android_detectado}\nEsta operacao REQUER Android {av_lote}.\nRISCO DE DANO PERMANENTE ao dispositivo!\nAtualize o software antes de continuar.\n'
            elif self._android_detectado > av_lote:
                msg_aviso += f'Dispositivo: Android {self._android_detectado}\n'
        msg_aviso += '\nO dispositivo DEVE estar em modo FASTBOOT.\nN├âO desconecte o cabo USB durante a opera├º├úo.\n\n'
        if is_secondary:
            msg_aviso += 'ÔÜá AVISO: O aparelho pode ligar com tela preta.\nSe isso ocorrer, pressione Vol- at├® entrar em fastboot.\nVerifique pelo Gerenciador de Dispositivos se apareceu\ne passe o software para restaurar o sistema.\n\n'
        msg_aviso += 'Ao confirmar, voce assume total responsabilidade pela\noperacao. Certifique-se de ter autorizacao do proprietario.\n\nDeseja continuar?'
        resposta = QMessageBox.warning(self, 'Confirmar FRP Unlock', msg_aviso, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resposta != QMessageBox.Yes:
            return
        self._set_busy(True, show_cancel=True)
        self._log(f'[MOTOROLA FRP] Iniciando operacao: {md['modelo']}')
        if self._engine and not self._engine._synced:
            self._engine.sync(force=True)
        self._worker = _FrpThread(self._engine, md['codename'], serial_len=md.get('serial_len', 10), operacao='frp_remove')
        self._worker.log.connect(self._on_worker_log)
        self._worker.resultado.connect(self._on_frp_done)
        self._worker.start()
    def _on_frp_done(self, ok: bool, msg: str, info: dict):
        self._set_busy(False, show_cancel=False)
        if 'cancelada' in msg.lower() or 'cancelado' in msg.lower():
            self._lbl_frp_status.setText('FRP: Cancelado')
            self._lbl_frp_status.setStyleSheet(f'color: {TEXT_MUTED}; border: none; background: transparent; font-weight: bold;')
            self._log('[MOTOROLA FRP] Operacao cancelada')
            return
        if ok:
            self._lbl_frp_status.setText('FRP: LIVRE Ô£ô')
            self._lbl_frp_status.setStyleSheet(f'color: {GREEN}; border: none; background: transparent; font-weight: bold;')
            self._log('[MOTOROLA FRP] Ô£ô Operacao concluida')
            if 'modelo secundario' in msg.lower():
                QMessageBox.information(self, 'FRP Removido', 'FRP removido com sucesso!\n\nO aparelho pode ligar com tela preta.\nSe isso ocorrer, pressione Vol- at├® entrar em fastboot.\nVerifique pelo Gerenciador de Dispositivos se apareceu\ne passe o software para restaurar o sistema.')
                return
            QMessageBox.information(self, 'Sucesso', 'FRP removido com sucesso!')
            return
        self._lbl_frp_status.setText('FRP: FALHA')
        self._lbl_frp_status.setStyleSheet(f'color: {RED}; border: none; background: transparent; font-weight: bold;')
        self._log(f'[MOTOROLA FRP] Ô£ù {msg}')
        QMessageBox.warning(self, 'Erro', f'Falha na operacao.\n{msg}')
    def _on_worker_log(self, msg: str):
        self._log(f'[MOTOROLA FRP] {msg}')
    def _on_cancel(self):
        if not self._em_execucao:
            return
        if self._worker:
            if self._worker.isRunning():
                self._worker.cancelar()
                self._btn_cancel.setEnabled(False)
                self._btn_cancel.setText('Cancelando...')
                self._log('[MOTOROLA FRP] Cancelamento solicitado ÔÇö aguarde a finalizacao segura')
    def _set_busy(self, busy: bool, show_cancel: bool=False):
        self._em_execucao = busy
        self._btn_read.setEnabled(not busy)
        if not busy:
            md = self._modelo_selecionado()
            self._btn_frp.setEnabled(bool(md))
            self._btn_cancel.setVisible(False)
            self._btn_cancel.setEnabled(False)
            self._btn_cancel.setText('Cancelar')
        else:
            self._btn_frp.setEnabled(False)
            if show_cancel:
                self._btn_cancel.setVisible(True)
                self._btn_cancel.setEnabled(True)
        self._combo_modelo.setEnabled(not busy)
