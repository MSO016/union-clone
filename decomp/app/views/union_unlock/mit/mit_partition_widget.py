'''Ref: administrativo/documentacao/29-07-2026-ANALISE-MTK-BOOT-META - V2/'''
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QSplitter, QSizePolicy, QMessageBox, QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QProgressBar, QFileDialog, QCheckBox)
from PyQt5.QtCore import (Qt, QThread, QTimer, pyqtSignal)
from PyQt5.QtGui import (QFont, QCursor, QColor)
from app.views.union_unlock.hxd.gui.tema import (gerar_qss_botao, gerar_qss_botao_outline, BG, BG_WHITE, PRIMARY, BORDER, TEXT, TEXT_MUTED, GREEN, RED, WHITE)
from app.views.union_unlock.hxd.gui.log_seguro import LogSeguro
from . import _mit_partition_core as _pcore
_ACCENT = '#1428A0'
_AVISO_LENTIDAO = 'IMPORTANTE: Operacoes de leitura/escrita sao LENTAS.\n  Backup 512 KB ~ 2 min | 1 MB ~ 4 min | Particoes grandes = horas\n  NAO desconecte o cabo. Tenha paciencia.'
_DISCLAIMER = 'AVISO LEGAL: Esta ferramenta e destinada a tecnicos qualificados. O uso incorreto pode causar danos irreversiveis ao dispositivo. TECH UNION SOLUTIONS nao se responsabiliza por uso indevido.'
def _default_save_dir():
    '''Retorna diretorio padrao de salvamento (Documentos do usuario).'''
    try:
        from app.utils.path_manager import PathManager
        d = PathManager.get_user_documents_dir('union_backups')
        if d:
            return d
    except Exception:
        pass
    import os
    return os.path.join(os.path.expanduser('~'), 'Documents')
class _WorkerThread(QThread):
    '''Worker para operacoes em background.'''
    log = pyqtSignal(str)
    progress = pyqtSignal(int)
    resultado = pyqtSignal(bool, str, object)
    def __init__(self, engine, operacao, **kwargs):
        super().__init__()
        self._engine = engine
        self._operacao = operacao
        self._kwargs = kwargs
    def cancelar(self):
        try:
            self._engine.cancel()
            return
        except Exception:
            return
    def run(self):
        def _log(msg):
            self.log.emit(msg)
        def _prog(val):
            self.progress.emit(val)
        try:
            if self._operacao == 'connect':
                ok, msg, parts = self._engine.connect_and_list(log_cb=_log)
                self.resultado.emit(ok, msg, parts)
                return
            if self._operacao == 'read':
                ok, msg = self._engine.partition_read(self._kwargs['part'], self._kwargs['filepath'], log_cb=_log, progress_cb=_prog)
                self.resultado.emit(ok, msg, None)
                return
            if self._operacao == 'write':
                ok, msg = self._engine.partition_write(self._kwargs['part'], self._kwargs['filepath'], log_cb=_log, progress_cb=_prog)
                self.resultado.emit(ok, msg, None)
                return
            if self._operacao == 'erase':
                ok, msg = self._engine.partition_erase(self._kwargs['part'], log_cb=_log, progress_cb=_prog)
                self.resultado.emit(ok, msg, None)
                return
            if self._operacao == 'reboot':
                ok, msg = self._engine.reboot(log_cb=_log)
                self.resultado.emit(ok, msg, None)
                return
        except Exception:
            self.resultado.emit(False, 'Falha na operacao.', None)
class MitPartitionWidget(QWidget):
    '''Gerenciador de particoes META ÔÇö sub-aba HXD.'''
    def __init__(self, parent=None):
        super().__init__(parent)
        self._engine = None
        self._worker = None
        self._em_execucao = False
        self._partitions = []
        self._elapsed = 0
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_tick)
        self._setup_ui()
        self._init_engine()
        self._exibir_boas_vindas()
    def _init_engine(self):
        try:
            from .mit_partition_engine import MitPartitionEngine
            eng = MitPartitionEngine()
            if eng.available:
                self._engine = eng
                return
            self._log.erro('Modulo nao disponivel.')
            self._desabilitar_todos()
            return
        except Exception:
            self._engine = None
            self._log.erro('Modulo nao disponivel.')
            self._desabilitar_todos()
    def _desabilitar_todos(self):
        for btn in self._btn_connect, self._btn_read, self._btn_write, self._btn_erase, self._btn_reboot, self._btn_cancel:
            btn.setEnabled(False)
    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        titulo = QLabel('META PARTITION (teste)')
        titulo.setFont(QFont('Segoe UI', 13, QFont.Bold))
        titulo.setStyleSheet(f'color: {PRIMARY!s}; background: {BG_WHITE!s}; padding: 10px 16px; border-bottom: 1px solid {BORDER!s};')
        root.addWidget(titulo)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._criar_painel_esquerdo())
        splitter.addWidget(self._criar_painel_direito())
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        root.addWidget(splitter, stretch=1)
    def _criar_painel_esquerdo(self) -> QWidget:
        '''Painel esquerdo: info + tabela + barra de botoes embaixo.'''
        container = QWidget()
        container.setStyleSheet('background-color: %s;' % BG_WHITE)
        lay = QVBoxLayout(container)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(6)
        self._info_frame = QFrame()
        self._info_frame.setVisible(False)
        self._info_frame.setStyleSheet('QFrame { background: #eaf2f8; border: 1px solid #85c1e9; border-radius: 6px; }')
        self._info_frame.setMaximumHeight(50)
        info_lay = QHBoxLayout(self._info_frame)
        info_lay.setContentsMargins(10, 4, 10, 4)
        self._lbl_device_info = QLabel('')
        self._lbl_device_info.setFont(QFont('Segoe UI', 9))
        self._lbl_device_info.setStyleSheet('color: #2c3e50; border: none;')
        info_lay.addWidget(self._lbl_device_info)
        self._lbl_part_count = QLabel('')
        self._lbl_part_count.setFont(QFont('Segoe UI', 9, QFont.Bold))
        self._lbl_part_count.setStyleSheet('color: %s; border: none;' % PRIMARY)
        info_lay.addWidget(self._lbl_part_count)
        info_lay.addStretch()
        lay.addWidget(self._info_frame)
        sel_bar = QHBoxLayout()
        sel_bar.setSpacing(6)
        btn_sel_all = QPushButton('Todos')
        btn_sel_all.setFixedHeight(22)
        btn_sel_all.setStyleSheet(self._btn_sm_css())
        btn_sel_all.clicked.connect(self._sel_all)
        sel_bar.addWidget(btn_sel_all)
        btn_unsel = QPushButton('Nenhum')
        btn_unsel.setFixedHeight(22)
        btn_unsel.setStyleSheet(self._btn_sm_css())
        btn_unsel.clicked.connect(self._unsel_all)
        sel_bar.addWidget(btn_unsel)
        self._lbl_sel_count = QLabel('')
        self._lbl_sel_count.setStyleSheet('color: %s; font-size: 10px;' % PRIMARY)
        sel_bar.addWidget(self._lbl_sel_count)
        sel_bar.addStretch()
        lay.addLayout(sel_bar)
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(['', 'Nome', 'Inicio (LBA)', 'Tamanho', 'Nota'])
        h = self._table.horizontalHeader()
        h.setFont(QFont('Segoe UI', 9, QFont.Bold))
        self._table.setColumnWidth(0, 30)
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.setColumnWidth(2, 90)
        self._table.setColumnWidth(3, 80)
        self._table.setColumnWidth(4, 60)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet(f'QTableWidget {{ background: white; border: 1px solid {BORDER!s}; font-size: 11px; gridline-color: #ecf0f1; }}QTableWidget::item:selected {{ background: {PRIMARY!s}; color: white; }}QHeaderView::section {{ background: #ecf0f1; font-weight: bold; font-size: 10px; border: 1px solid {BORDER!s}; padding: 3px; }}')
        self._table.cellChanged.connect(self._on_cell_changed)
        lay.addWidget(self._table, stretch=1)
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setFixedHeight(14)
        self._progress.setStyleSheet('QProgressBar { border: 1px solid #aaa; border-radius: 3px; background: #e0e0e0; text-align: center; font-size: 9px; }QProgressBar::chunk { background: %s; border-radius: 3px; }' % PRIMARY)
        lay.addWidget(self._progress)
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(6)
        self._btn_connect = self._botao('CONECTAR', PRIMARY)
        self._btn_connect.clicked.connect(self._on_connect)
        btn_bar.addWidget(self._btn_connect)
        self._btn_read = self._botao('BACKUP', GREEN)
        self._btn_read.clicked.connect(self._on_read)
        self._btn_read.setEnabled(False)
        btn_bar.addWidget(self._btn_read)
        self._btn_write = self._botao('GRAVAR', '#f39c12')
        self._btn_write.clicked.connect(self._on_write)
        self._btn_write.setEnabled(False)
        btn_bar.addWidget(self._btn_write)
        self._btn_erase = self._botao('APAGAR', RED)
        self._btn_erase.clicked.connect(self._on_erase)
        self._btn_erase.setEnabled(False)
        btn_bar.addWidget(self._btn_erase)
        self._btn_reboot = self._botao('REINICIAR', '#8e44ad')
        self._btn_reboot.clicked.connect(self._on_reboot)
        self._btn_reboot.setEnabled(False)
        btn_bar.addWidget(self._btn_reboot)
        self._btn_cancel = self._botao('CANCELAR', '#7f8c8d')
        self._btn_cancel.clicked.connect(self._on_cancel)
        self._btn_cancel.setEnabled(False)
        btn_bar.addWidget(self._btn_cancel)
        lay.addLayout(btn_bar)
        self._lbl_status = QLabel('Pronto.')
        self._lbl_status.setStyleSheet('color: %s; font-size: 10px; padding: 2px;' % TEXT_MUTED)
        lay.addWidget(self._lbl_status)
        return container
    def _criar_painel_direito(self) -> QWidget:
        '''Painel direito: terminal de log.'''
        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self._log = LogSeguro(parent=container)
        lay.addWidget(self._log)
        return container
    def _botao(self, text, color):
        btn = QPushButton(text)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.setMinimumHeight(32)
        btn.setFont(QFont('Segoe UI', 9, QFont.Bold))
        btn.setStyleSheet('QPushButton { background: %s; color: white; border-radius: 4px; padding: 4px 10px; }QPushButton:hover { opacity: 0.8; }QPushButton:disabled { background: #bdc3c7; color: #7f8c8d; }' % color)
        return btn
    def _btn_sm_css(self):
        return 'QPushButton { background: #95a5a6; color: white; border-radius: 3px; font-size: 9px; padding: 2px 8px; }QPushButton:hover { background: #7f8c8d; }'
    def _exibir_boas_vindas(self):
        self._log.info('Tech Union Solutions ÔÇö Meta Partition')
        self._log.aviso(_DISCLAIMER)
        self._log.separador()
        self._log.info('Pronto.')
    def _on_connect(self):
        if not self._engine:
            return
        self._log.separador()
        self._log.info('Conectando ao dispositivo...')
        self._log.aviso(_AVISO_LENTIDAO)
        self._iniciar_operacao('connect')
    def _on_read(self):
        parts = self._get_checked_partitions()
        if not parts:
            part = self._get_selected_partition()
            if part:
                parts = [part]
        if not parts:
            QMessageBox.warning(self, 'Aviso', 'Selecione ao menos uma particao.')
            return
        if len(parts) == 1:
            filepath, _ = QFileDialog.getSaveFileName(self, "Salvar backup de '%s'" % parts[0]['name'], self._default_filepath(parts[0]['name']), 'Binary (*.bin);;Todos (*)')
            if not filepath:
                return
            self._log.info('Backup: %s' % parts[0]['name'])
            self._iniciar_operacao('read', part=parts[0], filepath=filepath)
            return
        folder = QFileDialog.getExistingDirectory(self, 'Pasta para salvar backups', _default_save_dir())
        if not folder:
            return
        self._log.info('Backup de %d particoes...' % len(parts))
        self._iniciar_backup_multiplo(parts, folder)
    def _on_write(self):
        part = self._get_selected_partition()
        if not part:
            QMessageBox.warning(self, 'Aviso', 'Selecione uma particao.')
            return
        if _pcore.is_blacklisted(part['name']):
            reply = QMessageBox.critical(self, 'OPERACAO DE ALTO RISCO', "A particao '%s' e CRITICA.\n\nGravar dados incorretos pode causar BRICK IRREVERSIVEL.\n\nVoce assume TOTAL responsabilidade por esta acao.\n\nDeseja realmente continuar?" % part['name'], QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
        elif _pcore.is_warned(part['name']):
            reply = QMessageBox.warning(self, 'Termo de responsabilidade', "A particao '%s' e importante para o funcionamento.\n\nRecomendamos fazer backup ANTES de gravar.\n\nDeseja continuar?" % part['name'], QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
        else:
            reply = QMessageBox.question(self, 'Confirmar gravacao', "Gravar arquivo na particao '%s'?\nDados atuais serao sobrescritos." % part['name'], QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
        filepath, _ = QFileDialog.getOpenFileName(self, "Arquivo para gravar em '%s'" % part['name'], _default_save_dir(), 'Binary (*.bin);;Todos (*)')
        if not filepath:
            return
        self._log.info('Gravando: %s' % part['name'])
        self._iniciar_operacao('write', part=part, filepath=filepath)
    def _on_erase(self):
        part = self._get_selected_partition()
        if not part:
            QMessageBox.warning(self, 'Aviso', 'Selecione uma particao.')
            return
        if _pcore.is_blacklisted(part['name']):
            reply = QMessageBox.critical(self, 'OPERACAO DE ALTO RISCO', "A particao '%s' e CRITICA.\n\nZerar esta particao pode causar BRICK IRREVERSIVEL.\nO dispositivo pode NUNCA MAIS ligar.\n\nVoce assume TOTAL responsabilidade.\n\nDeseja realmente continuar?" % part['name'], QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
        elif _pcore.is_warned(part['name']):
            reply = QMessageBox.warning(self, 'Termo de responsabilidade', "Zerar '%s' pode impedir o boot normal.\n\nRecomendamos fazer backup ANTES.\n\nDeseja continuar?" % part['name'], QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
        else:
            reply = QMessageBox.question(self, 'Confirmar', "Zerar completamente '%s'?\nTodos os dados serao perdidos." % part['name'], QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
        self._log.info('Zerando: %s' % part['name'])
        self._iniciar_operacao('erase', part=part)
    def _on_reboot(self):
        reply = QMessageBox.question(self, 'Reiniciar', 'Reiniciar o dispositivo?\nA sessao sera encerrada.', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        self._log.info('Reiniciando...')
        self._iniciar_operacao('reboot')
    def _on_cancel(self):
        if self._worker:
            self._worker.cancelar()
            self._log.aviso('Cancelando operacao...')
            self._btn_cancel.setEnabled(False)
    def _sel_all(self):
        self._table.blockSignals(True)
        for row in range(self._table.rowCount()):
            item = self._table.item(row, 0)
            if item:
                item.setCheckState(Qt.Checked)
        self._table.blockSignals(False)
        self._update_sel_count()
    def _unsel_all(self):
        self._table.blockSignals(True)
        for row in range(self._table.rowCount()):
            item = self._table.item(row, 0)
            if item:
                item.setCheckState(Qt.Unchecked)
        self._table.blockSignals(False)
        self._update_sel_count()
    def _on_cell_changed(self, row, col):
        if col == 0:
            self._update_sel_count()
    def _update_sel_count(self):
        total = 0
        for row in range(self._table.rowCount()):
            item = self._table.item(row, 0)
            if not item:
                continue
            if item.checkState() == Qt.Checked:
                total += 1
        rows = self._table.rowCount()
        if rows > 0:
            self._lbl_sel_count.setText('%d de %d' % (total, rows))
    def _get_checked_partitions(self):
        checked = []
        for row in range(self._table.rowCount()):
            item = self._table.item(row, 0)
            if not item:
                continue
            if item.checkState() != Qt.Checked:
                continue
            if row < len(self._partitions):
                checked.append(self._partitions[row])
        return checked
    def _get_selected_partition(self):
        row = self._table.currentRow()
        if row < 0 or row >= len(self._partitions):
            return
        return self._partitions[row]
    def _iniciar_operacao(self, operacao, **kwargs):
        self._set_busy(True)
        self._progress.setValue(0)
        self._elapsed = 0
        self._timer.start()
        self._worker = _WorkerThread(self._engine, operacao, **kwargs)
        self._worker.log.connect(self._on_worker_log)
        self._worker.progress.connect(self._progress.setValue)
        self._worker.resultado.connect(self._on_resultado)
        self._worker.start()
    def _iniciar_backup_multiplo(self, parts, folder):
        '''Backup sequencial de multiplas particoes.'''
        import os
        self._backup_queue = list(parts)
        self._backup_folder = folder
        self._backup_sucesso = 0
        self._backup_total = len(parts)
        self._next_backup()
    def _next_backup(self):
        if not self._backup_queue:
            self._log.sucesso('Backup concluido: %d/%d' % (self._backup_sucesso, self._backup_total))
            self._set_busy(False)
            if self._engine and self._engine.session_active:
                self._set_ops_enabled(True)
            return
        import os
        part = self._backup_queue.pop(0)
        filepath = os.path.join(self._backup_folder, '%s.bin' % part['name'])
        self._log.info('[%d/%d] %s...' % (self._backup_total - len(self._backup_queue), self._backup_total, part['name']))
        self._set_busy(True)
        self._progress.setValue(0)
        self._elapsed = 0
        self._timer.start()
        self._worker = _WorkerThread(self._engine, 'read', part=part, filepath=filepath)
        self._worker.log.connect(self._on_worker_log)
        self._worker.progress.connect(self._progress.setValue)
        self._worker.resultado.connect(self._on_backup_multi_result)
        self._worker.start()
    def _on_backup_multi_result(self, ok, msg, data):
        self._timer.stop()
        if ok:
            self._backup_sucesso += 1
        else:
            self._log.erro(msg)
        self._worker = None
        self._next_backup()
    def _on_worker_log(self, msg):
        if ':\\' in msg or '/' in msg and 'dev/block' not in msg:
            import os
            msg = os.path.basename(msg) if '\\' in msg else msg
        if ':' in msg and not msg.startswith(' ') and not msg.startswith('['):
            parts = msg.split(':', 1)
            self._log.prop(parts[0], parts[1].strip())
            return
        self._log.info(msg)
    def _on_resultado(self, ok, msg, data):
        self._timer.stop()
        self._set_busy(False)
        if ok:
            self._log.sucesso('%s (%ds)' % (msg, self._elapsed))
            self._lbl_status.setText('OK (%ds)' % self._elapsed)
            self._lbl_status.setStyleSheet('color: %s;' % GREEN)
            if data and isinstance(data, list):
                self._partitions = data
                self._populate_table(data)
                self._info_frame.setVisible(True)
                info = getattr(self._engine, 'device_info', {})
                info_text = ''
                if info.get('brand') or info.get('model'):
                    info_text = f'{info.get('brand', '')!s} {info.get('model', '')!s}'
                    if info.get('android'):
                        info_text += ' (Android %s)' % info['android']
                self._lbl_device_info.setText(info_text.strip())
                self._lbl_part_count.setText('%d particoes' % len(data))
        else:
            self._log.erro(msg)
            self._lbl_status.setText('Falha')
            self._lbl_status.setStyleSheet('color: %s;' % RED)
        if self._engine and self._engine.session_active:
            self._set_ops_enabled(True)
        self._worker = None
    def _on_tick(self):
        self._elapsed += 1
        self._lbl_status.setText('Executando... (%ds)' % self._elapsed)
    def _set_busy(self, busy):
        self._em_execucao = busy
        self._btn_connect.setEnabled(not busy)
        self._btn_cancel.setEnabled(busy)
        if busy:
            self._btn_read.setEnabled(False)
            self._btn_write.setEnabled(False)
            self._btn_erase.setEnabled(False)
            self._btn_reboot.setEnabled(False)
    def _set_ops_enabled(self, enabled):
        self._btn_read.setEnabled(enabled)
        self._btn_write.setEnabled(enabled)
        self._btn_erase.setEnabled(enabled)
        self._btn_reboot.setEnabled(enabled)
    def _populate_table(self, partitions):
        self._table.blockSignals(True)
        self._table.setRowCount(len(partitions))
        for row, p in enumerate(partitions):
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            chk.setCheckState(Qt.Unchecked)
            self._table.setItem(row, 0, chk)
            item_name = QTableWidgetItem(p['name'])
            item_name.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self._table.setItem(row, 1, item_name)
            item_lba = QTableWidgetItem(str(p['start_lba']))
            item_lba.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self._table.setItem(row, 2, item_lba)
            item_size = QTableWidgetItem(_pcore.format_size(p['size_mb']))
            item_size.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self._table.setItem(row, 3, item_size)
            nota, is_critical = _pcore.get_note(p['name'])
            item_nota = QTableWidgetItem(nota)
            item_nota.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            if is_critical:
                item_nota.setForeground(QColor(RED))
            self._table.setItem(row, 4, item_nota)
            continue
        self._table.blockSignals(False)
        self._update_sel_count()
    def _default_filepath(self, name):
        import os
        return os.path.join(_default_save_dir(), '%s.bin' % name)
    def closeEvent(self, event):
        self._timer.stop()
        if self._worker and self._worker.isRunning():
            self._worker.cancelar()
            self._worker.quit()
            if not self._worker.wait(3000):
                self._worker.terminate()
        if self._engine:
            try:
                self._engine.disconnect()
            except Exception:
                pass
        event.accept()
