'''Ref: administrativo/documentacao/29-07-2026-FILE-MANAGER-DIAGMODE/'''
import os
import sys
import time
from datetime import datetime
from typing import Optional
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QSplitter, QSizePolicy, QMessageBox, QFileDialog, QScrollArea, QHeaderView, QTreeWidget, QTreeWidgetItem, QMenu, QInputDialog, QLineEdit, QDialog, QFormLayout, QPlainTextEdit, QComboBox, QApplication, QProgressDialog)
from PyQt5.QtCore import (Qt, QThread, pyqtSignal)
from PyQt5.QtGui import (QFont, QCursor, QColor, QIcon)
from PyQt5.QtCore import QSize as _QSize
from app.views.union_unlock.hxd.gui.tema import (gerar_qss_botao, gerar_qss_botao_outline, BG, BG_WHITE, BG_DARK, PRIMARY, PRIMARY_HOVER, UNION_BLUE, UNION_ACCENT, UNION_LIGHT, BORDER, TEXT, TEXT_MUTED, TEXT_LABEL, GREEN, GREEN_DARK, RED, RED_BG, YELLOW, ORANGE, WHITE, HEADER_BG)
from app.views.union_unlock.hxd.gui.log_seguro import LogSeguro
from app.views.union_unlock.hxd.core.backup_manager import BackupManager
from .fmgr_engine import FmgrEngine, EntryInfo
from ._fmgr_core import (detect_filesystem, FS_NAMES, FS_EXT4, FS_NVRAM, FS_RAW, FS_EROFS, format_size, octal_permissions)
_VERSAO = 'v1.0'
_OBJ_NAME = 'fmgr_widget'
class _WorkerThread(QThread):
    log_emitido = pyqtSignal(str, str)
    finalizado = pyqtSignal(bool, str, object)
    def __init__(self, engine, op, **kwargs):
        super().__init__()
        self._engine = engine
        self._op = op
        self._kw = kwargs
    def run(self):
        def _cb(msg):
            self.log_emitido.emit('info', msg)
        try:
            if self._op == 'open':
                ok, msg = self._engine.open_image(self._kw['path'])
                self.finalizado.emit(ok, msg, None)
                return
            if self._op == 'write':
                ok, msg = self._engine.write_file(self._kw['dest'], self._kw['data'], _cb)
                self.finalizado.emit(ok, msg, None)
                return
            if self._op == 'delete':
                ok, msg = self._engine.delete(self._kw['path'], self._kw.get('is_dir', False), _cb)
                self.finalizado.emit(ok, msg, None)
                return
            if self._op == 'mkdir':
                ok, msg = self._engine.mkdir(self._kw['path'], _cb)
                self.finalizado.emit(ok, msg, None)
                return
            if self._op == 'rename':
                ok, msg = self._engine.rename(self._kw['old'], self._kw['new'], _cb)
                self.finalizado.emit(ok, msg, None)
                return
            if self._op == 'export':
                ok, msg = self._engine.export_file(self._kw['src'], self._kw['dest'], _cb)
                self.finalizado.emit(ok, msg, None)
                return
            if self._op == 'import':
                ok, msg = self._engine.import_file(self._kw['src'], self._kw['dest'], _cb)
                self.finalizado.emit(ok, msg, None)
                return
            if self._op == 'chmod':
                ok, msg = self._engine.chmod(self._kw['path'], self._kw['mode'], _cb)
                self.finalizado.emit(ok, msg, None)
                return
            if self._op == 'chown':
                ok, msg = self._engine.chown(self._kw['path'], self._kw['uid'], self._kw['gid'], _cb)
                self.finalizado.emit(ok, msg, None)
                return
            if self._op == 'audit':
                result = self._engine.audit()
                self.finalizado.emit(True, 'Audit concluido', result)
                return
            self.finalizado.emit(False, 'Operacao nao suportada.', None)
            return
        except Exception:
            self.finalizado.emit(False, 'Falha inesperada. Reinstale o sistema.', None)
class _HexViewDialog(QDialog):
    def __init__(self, title, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f'Hex View ÔÇö {title}')
        self.resize(750, 520)
        self.setStyleSheet(f'background: {BG}; color: {TEXT};')
        lay = QVBoxLayout(self)
        lbl = QLabel(f'Arquivo: {title} ({format_size(len(data))})')
        lbl.setFont(QFont('Segoe UI', 11, QFont.Bold))
        lbl.setStyleSheet(f'color: {PRIMARY}; padding: 4px;')
        lay.addWidget(lbl)
        txt = QPlainTextEdit()
        txt.setReadOnly(True)
        txt.setFont(QFont('Consolas', 10))
        txt.setStyleSheet('QPlainTextEdit { background: #1e1e1e; color: #43a047; border: 1px solid #2a2a2a; border-radius: 4px; padding: 8px; }')
        lines = []
        for offset in range(0, min(len(data), 16384), 16):
            chunk = data[offset:offset + 16]
            hex_part = ' '.join((f'{b:02X}' for b in chunk))
            ascii_part = ''.join(('.' for b in chunk if not b <= 32 if not 32 < 127))
            lines.append(f'{offset:08X}  {hex_part:<48}  {ascii_part}')
        if len(data) > 16384:
            lines.append(f'\n... truncado ({format_size(len(data))} total)')
        txt.setPlainText('\n'.join(lines))
        lay.addWidget(txt)
class _TextViewDialog(QDialog):
    def __init__(self, title, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f'Text View ÔÇö {title}')
        self.resize(700, 500)
        self.setStyleSheet(f'background: {BG}; color: {TEXT};')
        lay = QVBoxLayout(self)
        lbl = QLabel(f'Arquivo: {title}')
        lbl.setFont(QFont('Segoe UI', 11, QFont.Bold))
        lbl.setStyleSheet(f'color: {PRIMARY}; padding: 4px;')
        lay.addWidget(lbl)
        txt = QPlainTextEdit()
        txt.setReadOnly(True)
        txt.setFont(QFont('Consolas', 10))
        txt.setStyleSheet('QPlainTextEdit { background: #1e1e1e; color: #ffffff; border: 1px solid #2a2a2a; border-radius: 4px; padding: 8px; }')
        try:
            content = data.decode('utf-8', errors='replace')
        except Exception:
            content = repr(data[:4096])
        txt.setPlainText(content[:100000])
        lay.addWidget(txt)
class _ChangePermDialog(QDialog):
    '''Dialog de permissoes ÔÇö igual a referencia (checkboxes rwx + UID/GID).'''
    def __init__(self, entry: EntryInfo, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f'Change Permission ÔÇö {entry.name}')
        self.resize(460, 420)
        self.setStyleSheet(f'\n            QDialog {{ background: {BG_WHITE}; color: {TEXT}; }}\n            QLabel {{ background: transparent; }}\n            QCheckBox {{ spacing: 6px; font-size: 12px; }}\n            QCheckBox::indicator {{ width: 18px; height: 18px; }}\n            QCheckBox::indicator:checked {{\n                background: {UNION_ACCENT}; border: 1px solid {UNION_BLUE};\n                border-radius: 3px;\n            }}\n            QCheckBox::indicator:unchecked {{\n                background: {BG}; border: 1px solid {BORDER};\n                border-radius: 3px;\n            }}\n        ')
        self._entry = entry
        self._result_mode = None
        self._result_uid = None
        self._result_gid = None
        self._build()
    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)
        mode = self._entry.mode
        info_frame = QFrame()
        info_frame.setStyleSheet(f'\n            QFrame {{ background: {BG}; border: 1px solid {BORDER};\n                      border-radius: 6px; padding: 10px; }}\n        ')
        info_lay = QVBoxLayout(info_frame)
        info_lay.setSpacing(4)
        for label, value in ('File Name', self._entry.name), ('File Type', 'directory' if self._entry.is_dir else 'file'), ('File Size', self._entry.size_str), ('File Mode', self._entry.permissions), ('Owner', f'uid={self._entry.uid}  gid={self._entry.gid}'):
            row = QHBoxLayout()
            lbl = QLabel(f'{label} :')
            lbl.setFont(QFont('Consolas', 10, QFont.Bold))
            lbl.setFixedWidth(100)
            lbl.setStyleSheet(f'color: {TEXT_LABEL};')
            val = QLabel(str(value))
            val.setFont(QFont('Consolas', 10))
            val.setStyleSheet(f'color: {TEXT};')
            row.addWidget(lbl)
            row.addWidget(val, stretch=1)
            info_lay.addLayout(row)
        lay.addWidget(info_frame)
        from PyQt5.QtWidgets import QGridLayout
        grid_frame = QFrame()
        grid_frame.setStyleSheet(f'\n            QFrame {{ background: {BG_WHITE}; border: 1px solid {BORDER};\n                      border-radius: 6px; padding: 12px; }}\n        ')
        grid = QGridLayout(grid_frame)
        grid.setSpacing(10)
        headers = ['', 'Read', 'Write', 'Execute']
        for i, h in enumerate(headers):
            lbl = QLabel(h)
            lbl.setFont(QFont('Segoe UI', 11, QFont.Bold))
            lbl.setStyleSheet(f'color: {PRIMARY};')
            lbl.setAlignment(Qt.AlignCenter)
            grid.addWidget(lbl, 0, i)
        self._checks = {}
        rows = [('Owner', 6), ('Group', 3), ('Others', 0)]
        for row_idx, (label, shift) in enumerate(rows, 1):
            lbl = QLabel(label)
            lbl.setFont(QFont('Segoe UI', 11, QFont.Bold))
            lbl.setStyleSheet(f'color: {TEXT};')
            grid.addWidget(lbl, row_idx, 0)
            for col_idx, (perm_name, bit_offset) in enumerate([('r', 2), ('w', 1), ('x', 0)], 1):
                from PyQt5.QtWidgets import QCheckBox
                cb = QCheckBox()
                bit = shift + bit_offset
                cb.setChecked(bool(mode & 1 << bit))
                self._checks[label, perm_name] = cb, bit
                grid.addWidget(cb, row_idx, col_idx, Qt.AlignCenter)
        lay.addWidget(grid_frame)
        uid_gid_frame = QFrame()
        uid_gid_frame.setStyleSheet(f'\n            QFrame {{ background: {BG}; border: 1px solid {BORDER};\n                      border-radius: 6px; padding: 10px; }}\n        ')
        ug_lay = QHBoxLayout(uid_gid_frame)
        ug_lay.setSpacing(16)
        from PyQt5.QtWidgets import QSpinBox
        lbl_uid = QLabel('UID:')
        lbl_uid.setFont(QFont('Segoe UI', 11, QFont.Bold))
        lbl_uid.setStyleSheet(f'color: {TEXT_LABEL};')
        self._spin_uid = QSpinBox()
        self._spin_uid.setRange(0, 65535)
        self._spin_uid.setValue(self._entry.uid)
        self._spin_uid.setFont(QFont('Consolas', 11))
        self._spin_uid.setMinimumHeight(32)
        self._spin_uid.setStyleSheet(f'\n            QSpinBox {{\n                background: {BG_WHITE}; color: {TEXT};\n                border: 1px solid {BORDER}; border-radius: 4px;\n                padding: 4px 8px;\n            }}\n            QSpinBox:focus {{ border-color: {UNION_ACCENT}; }}\n        ')
        lbl_gid = QLabel('GID:')
        lbl_gid.setFont(QFont('Segoe UI', 11, QFont.Bold))
        lbl_gid.setStyleSheet(f'color: {TEXT_LABEL};')
        self._spin_gid = QSpinBox()
        self._spin_gid.setRange(0, 65535)
        self._spin_gid.setValue(self._entry.gid)
        self._spin_gid.setFont(QFont('Consolas', 11))
        self._spin_gid.setMinimumHeight(32)
        self._spin_gid.setStyleSheet(self._spin_uid.styleSheet())
        ug_lay.addWidget(lbl_uid)
        ug_lay.addWidget(self._spin_uid, stretch=1)
        ug_lay.addWidget(lbl_gid)
        ug_lay.addWidget(self._spin_gid, stretch=1)
        lay.addWidget(uid_gid_frame)
        btn_lay = QHBoxLayout()
        btn_lay.setSpacing(8)
        btn_lay.addStretch()
        btn_cancel = QPushButton('Cancel')
        btn_cancel.setCursor(QCursor(Qt.PointingHandCursor))
        btn_cancel.setStyleSheet(gerar_qss_botao_outline())
        btn_cancel.setMinimumHeight(34)
        btn_cancel.clicked.connect(self.reject)
        btn_lay.addWidget(btn_cancel)
        btn_save = QPushButton('Save')
        btn_save.setCursor(QCursor(Qt.PointingHandCursor))
        btn_save.setStyleSheet(gerar_qss_botao())
        btn_save.setMinimumHeight(34)
        btn_save.clicked.connect(self._on_save)
        btn_lay.addWidget(btn_save)
        lay.addLayout(btn_lay)
    def _on_save(self):
        new_mode = 0
        for (_, _), (cb, bit) in self._checks.items():
            if cb.isChecked():
                new_mode |= 1 << bit
        file_type_bits = self._entry.mode & 61440
        self._result_mode = file_type_bits | new_mode
        self._result_uid = self._spin_uid.value()
        self._result_gid = self._spin_gid.value()
        self.accept()
    @property
    def new_mode(self) -> Optional[int]:
        return self._result_mode
    @property
    def new_uid(self) -> Optional[int]:
        return self._result_uid
    @property
    def new_gid(self) -> Optional[int]:
        return self._result_gid
class _EditTextDialog(QDialog):
    '''Dialog para editar conteudo de arquivo texto e salvar de volta.'''
    def __init__(self, name, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f'Editar Texto ÔÇö {name}')
        self.resize(720, 520)
        self.setStyleSheet(f'background: {BG}; color: {TEXT};')
        self._saved = False
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(8)
        header_lay = QHBoxLayout()
        lbl = QLabel(f'Editando: {name} ({format_size(len(data))})')
        lbl.setFont(QFont('Segoe UI', 11, QFont.Bold))
        lbl.setStyleSheet(f'color: {PRIMARY};')
        header_lay.addWidget(lbl)
        header_lay.addStretch()
        lay.addLayout(header_lay)
        self._editor = QPlainTextEdit()
        self._editor.setFont(QFont('Consolas', 11))
        self._editor.setStyleSheet(f'QPlainTextEdit {{ background: {BG_WHITE}; color: {TEXT}; border: 1px solid {BORDER}; border-radius: 4px; padding: 8px; }}')
        try:
            self._editor.setPlainText(data.decode('utf-8', errors='replace'))
        except Exception:
            self._editor.setPlainText('')
        lay.addWidget(self._editor, stretch=1)
        btn_lay = QHBoxLayout()
        btn_lay.addStretch()
        btn_cancel = QPushButton('Cancelar')
        btn_cancel.setCursor(QCursor(Qt.PointingHandCursor))
        btn_cancel.setStyleSheet(gerar_qss_botao_outline())
        btn_cancel.setMinimumHeight(34)
        btn_cancel.clicked.connect(self.reject)
        btn_lay.addWidget(btn_cancel)
        btn_save = QPushButton('Salvar')
        btn_save.setCursor(QCursor(Qt.PointingHandCursor))
        btn_save.setStyleSheet(gerar_qss_botao(GREEN))
        btn_save.setMinimumHeight(34)
        btn_save.clicked.connect(self._on_save)
        btn_lay.addWidget(btn_save)
        lay.addLayout(btn_lay)
    def _on_save(self):
        self._saved = True
        self.accept()
    @property
    def was_saved(self) -> bool:
        return self._saved
    @property
    def new_data(self) -> bytes:
        return self._editor.toPlainText().encode('utf-8')
class _EditHexDialog(QDialog):
    '''Hex editor com 3 colunas: Offset (ro) | Hex (editavel) | ASCII (preview live).'''
    _MAX_EDIT = 2097152
    def __init__(self, name, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f'Hex Edit ÔÇö {name}')
        self.resize(820, 560)
        self.setStyleSheet(f'background: {BG}; color: {TEXT};')
        self._saved = False
        self._original = data
        self._updating = False
        truncado = len(data) > self._MAX_EDIT
        self._edit_data = data[:self._MAX_EDIT] if truncado else data
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(6)
        lbl = QLabel(f'Arquivo: {name} ({format_size(len(data))})')
        lbl.setFont(QFont('Segoe UI', 11, QFont.Bold))
        lbl.setStyleSheet(f'color: {PRIMARY}; padding: 4px;')
        lay.addWidget(lbl)
        if truncado:
            aviso = QLabel(f'Arquivo grande ÔÇö editando primeiros {format_size(self._MAX_EDIT)}. O restante sera preservado.')
            aviso.setFont(QFont('Segoe UI', 10))
            aviso.setStyleSheet(f'color: {YELLOW}; padding: 4px;')
            aviso.setWordWrap(True)
            lay.addWidget(aviso)
        hint = QLabel('Edite os bytes hex (coluna central). O ASCII atualiza automaticamente.')
        hint.setFont(QFont('Segoe UI', 9))
        hint.setStyleSheet(f'color: {TEXT_MUTED}; padding: 2px;')
        hint.setWordWrap(True)
        lay.addWidget(hint)
        self._search_matches = []
        self._search_idx = -1
        self._build_search_bar(lay)
        col_hdr = QHBoxLayout()
        col_hdr.setSpacing(0)
        _fnt_hdr = QFont('Consolas', 9, QFont.Bold)
        for txt, w in (('OFFSET', 82), ('HEX', 0), ('ASCII', 152)):
            l = QLabel(txt)
            l.setFont(_fnt_hdr)
            l.setStyleSheet(f'color: {TEXT_MUTED}; padding-left: 4px;')
            if w:
                l.setFixedWidth(w)
                col_hdr.addWidget(l)
            else:
                col_hdr.addWidget(l, stretch=1)
        lay.addLayout(col_hdr)
        editor_frame = QFrame()
        editor_frame.setStyleSheet('QFrame { background: #1e1e1e; border: 1px solid #2a2a2a; border-radius: 4px; }')
        ef_lay = QHBoxLayout(editor_frame)
        ef_lay.setContentsMargins(4, 4, 4, 4)
        ef_lay.setSpacing(6)
        _fnt = QFont('Consolas', 10)
        _base_qss = 'QPlainTextEdit {{ background: transparent; border: none; color: {clr}; padding: 2px; }}'
        self._off_view = QPlainTextEdit()
        self._off_view.setReadOnly(True)
        self._off_view.setFont(_fnt)
        self._off_view.setStyleSheet(_base_qss.format(clr='#888888'))
        self._off_view.setFixedWidth(78)
        self._off_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._off_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._off_view.setLineWrapMode(QPlainTextEdit.NoWrap)
        ef_lay.addWidget(self._off_view)
        sep1 = QFrame()
        sep1.setFixedWidth(1)
        sep1.setStyleSheet('background: #333;')
        ef_lay.addWidget(sep1)
        self._hex_edit = QPlainTextEdit()
        self._hex_edit.setFont(_fnt)
        self._hex_edit.setStyleSheet(_base_qss.format(clr='#43a047'))
        self._hex_edit.setLineWrapMode(QPlainTextEdit.NoWrap)
        ef_lay.addWidget(self._hex_edit, stretch=1)
        sep2 = QFrame()
        sep2.setFixedWidth(1)
        sep2.setStyleSheet('background: #333;')
        ef_lay.addWidget(sep2)
        self._asc_view = QPlainTextEdit()
        self._asc_view.setReadOnly(True)
        self._asc_view.setFont(_fnt)
        self._asc_view.setStyleSheet(_base_qss.format(clr='#8bc34a'))
        self._asc_view.setFixedWidth(148)
        self._asc_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._asc_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._asc_view.setLineWrapMode(QPlainTextEdit.NoWrap)
        ef_lay.addWidget(self._asc_view)
        lay.addWidget(editor_frame, stretch=1)
        self._populate(self._edit_data)
        self._hex_edit.textChanged.connect(self._on_hex_changed)
        self._scroll_syncing = False
        self._hex_edit.verticalScrollBar().valueChanged.connect(self._sync_scroll_from_hex)
        self._asc_view.verticalScrollBar().valueChanged.connect(self._sync_scroll_from_asc)
        self._off_view.verticalScrollBar().valueChanged.connect(self._sync_scroll_from_off)
        self._syncing = False
        self._hex_edit.cursorPositionChanged.connect(self._sync_hex_to_ascii)
        self._asc_view.cursorPositionChanged.connect(self._sync_ascii_to_hex)
        self._lbl_err = QLabel('')
        self._lbl_err.setFont(QFont('Segoe UI', 10))
        self._lbl_err.setStyleSheet(f'color: {RED};')
        self._lbl_err.setWordWrap(True)
        lay.addWidget(self._lbl_err)
        btn_lay = QHBoxLayout()
        btn_lay.addStretch()
        btn_cancel = QPushButton('Cancelar')
        btn_cancel.setCursor(QCursor(Qt.PointingHandCursor))
        btn_cancel.setStyleSheet(gerar_qss_botao_outline())
        btn_cancel.setMinimumHeight(34)
        btn_cancel.clicked.connect(self.reject)
        btn_lay.addWidget(btn_cancel)
        btn_save = QPushButton('Salvar')
        btn_save.setCursor(QCursor(Qt.PointingHandCursor))
        btn_save.setStyleSheet(gerar_qss_botao(GREEN))
        btn_save.setMinimumHeight(34)
        btn_save.clicked.connect(self._on_save)
        btn_lay.addWidget(btn_save)
        lay.addLayout(btn_lay)
    def _populate(self, data: bytes):
        self._updating = True
        offsets, hex_lines, ascii_lines = [], [], []
        for off in range(0, len(data), 16):
            chunk = data[off:off + 16]
            offsets.append(f'{off:08X}')
            hex_lines.append(' '.join((f'{b:02X}' for b in chunk)))
            ascii_lines.append(''.join(('.' for b in chunk if not b <= 32 if not 32 < 127)))
        self._off_view.setPlainText('\n'.join(offsets))
        self._hex_edit.setPlainText('\n'.join(hex_lines))
        self._asc_view.setPlainText('\n'.join(ascii_lines))
        self._updating = False
    def _on_hex_changed(self):
        if self._updating:
            return
        self._updating = True
        parsed = self._try_parse_silent()
        if parsed is not None:
            ascii_lines, offsets = [], []
            for off in range(0, len(parsed), 16):
                chunk = parsed[off:off + 16]
                offsets.append(f'{off:08X}')
                ascii_lines.append(''.join(('.' for b in chunk if not b <= 32 if not 32 < 127)))
            self._asc_view.setPlainText('\n'.join(ascii_lines))
            self._off_view.setPlainText('\n'.join(offsets))
            self._lbl_err.setText('')
        self._updating = False
    def _try_parse_silent(self) -> Optional[bytes]:
        parts = []
        for line in self._hex_edit.toPlainText().splitlines():
            clean = ''.join(line.strip().split())
            if not clean:
                continue
            if len(clean) % 2 != 0:
                return
            try:
                parts.append(bytes.fromhex(clean))
            except ValueError:
                return
        if parts:
            return b''.join(parts)
        return b''
    def _on_save(self):
        parsed = self._try_parse_silent()
        if parsed is None:
            self._lbl_err.setText('Hex invalido. Use apenas 0-9 e A-F, 2 digitos por byte.')
            return
        self._lbl_err.setText('')
        self._saved = True
        self.accept()
    @property
    def was_saved(self) -> bool:
        return self._saved
    @property
    def new_data(self) -> bytes:
        parsed = self._try_parse_silent()
        if parsed is None:
            return self._original
        if len(self._original) > self._MAX_EDIT:
            return parsed + self._original[self._MAX_EDIT:]
        return parsed
    def _sync_scroll_from_hex(self, val):
        '''Hex scrollou ÔåÆ sincroniza offset e ASCII.'''
        if self._scroll_syncing:
            return
        self._scroll_syncing = True
        try:
            self._off_view.verticalScrollBar().setValue(val)
            self._asc_view.verticalScrollBar().setValue(val)
        finally:
            self._scroll_syncing = False
    def _sync_scroll_from_asc(self, val):
        '''ASCII scrollou ÔåÆ sincroniza hex e offset.'''
        if self._scroll_syncing:
            return
        self._scroll_syncing = True
        try:
            self._hex_edit.verticalScrollBar().setValue(val)
            self._off_view.verticalScrollBar().setValue(val)
        finally:
            self._scroll_syncing = False
    def _sync_scroll_from_off(self, val):
        '''Offset scrollou ÔåÆ sincroniza hex e ASCII.'''
        if self._scroll_syncing:
            return
        self._scroll_syncing = True
        try:
            self._hex_edit.verticalScrollBar().setValue(val)
            self._asc_view.verticalScrollBar().setValue(val)
        finally:
            self._scroll_syncing = False
    def _sync_hex_to_ascii(self):
        '''Quando o cursor move no hex, destaca o ASCII correspondente.'''
        if self._syncing or self._updating:
            return
        self._syncing = True
        try:
            cursor = self._hex_edit.textCursor()
            block = cursor.block()
            if not block.isValid():
                self._syncing = False
                return
        finally:
            self._syncing = False
        try:
            line = block.blockNumber()
            col = cursor.positionInBlock()
            byte_idx = col // 3
            if byte_idx > 15:
                byte_idx = 15
            sel_text = cursor.selectedText()
            if sel_text:
                n_bytes = max(1, (len(sel_text.replace(' ', '')) + 1) // 2)
            else:
                n_bytes = 1
            asc_block = self._asc_view.document().findBlockByLineNumber(line)
            if not asc_block.isValid():
                self._syncing = False
                return
        finally:
            self._syncing = False
        try:
            asc_cursor = self._asc_view.textCursor()
            target_pos = asc_block.position() + min(byte_idx, asc_block.length() - 1)
            asc_cursor.setPosition(target_pos)
            asc_cursor.movePosition(asc_cursor.Right, asc_cursor.KeepAnchor, n_bytes)
            self._asc_view.setTextCursor(asc_cursor)
        finally:
            self._syncing = False
    def _sync_ascii_to_hex(self):
        '''Quando o cursor move no ASCII, destaca o hex correspondente.'''
        if self._syncing or self._updating:
            return
        self._syncing = True
        try:
            cursor = self._asc_view.textCursor()
            block = cursor.block()
            if not block.isValid():
                self._syncing = False
                return
        finally:
            self._syncing = False
        try:
            line = block.blockNumber()
            byte_idx = cursor.positionInBlock()
            if byte_idx > 15:
                byte_idx = 15
            sel_len = len(cursor.selectedText()) if cursor.hasSelection() else 1
            n_bytes = max(1, sel_len)
            hex_block = self._hex_edit.document().findBlockByLineNumber(line)
            if not hex_block.isValid():
                self._syncing = False
                return
        finally:
            self._syncing = False
        try:
            hex_cursor = self._hex_edit.textCursor()
            target_pos = hex_block.position() + byte_idx * 3
            hex_cursor.setPosition(target_pos)
            hex_n_chars = n_bytes * 3 - 1 if n_bytes > 1 else 2
            hex_cursor.movePosition(hex_cursor.Right, hex_cursor.KeepAnchor, hex_n_chars)
            self._hex_edit.setTextCursor(hex_cursor)
        finally:
            self._syncing = False
    @staticmethod
    def _aplicar_svg_btn(btn, svg_relativo, tamanho=16):
        '''Aplica SVG via PathManager. Fallback: botao sem icone.'''
        try:
            from app.utils.path_manager import PathManager
            caminho = PathManager.get_resource_path(svg_relativo)
            if caminho:
                if os.path.isfile(caminho):
                    btn.setIcon(QIcon(caminho))
                    btn.setIconSize(_QSize(tamanho, tamanho))
                    return
                return
        except Exception:
            pass
    def _build_search_bar(self, parent_layout):
        '''Constroi barra de busca/substituicao colapsavel.'''
        self._search_frame = QFrame()
        self._search_frame.setStyleSheet(f'QFrame {{ background: {BG_DARK}; border: 1px solid {BORDER}; border-radius: 4px; }}')
        sf_lay = QVBoxLayout(self._search_frame)
        sf_lay.setContentsMargins(8, 6, 8, 6)
        sf_lay.setSpacing(4)
        _fnt_sm = QFont('Segoe UI', 9)
        _fnt_input = QFont('Consolas', 10)
        _input_qss = f'QLineEdit {{ background: #1e1e1e; color: {WHITE}; border: 1px solid {BORDER}; border-radius: 3px; padding: 4px 6px; font-family: Consolas; font-size: 10pt; }}QLineEdit:focus {{ border-color: {UNION_ACCENT}; }}'
        _combo_qss = f'QComboBox {{ background: #1e1e1e; color: {WHITE}; border: 1px solid {BORDER}; border-radius: 3px; padding: 3px 6px; font-size: 9pt; min-width: 70px; }}QComboBox QAbstractItemView {{ background: #1e1e1e; color: {WHITE}; selection-background-color: {UNION_BLUE}; }}'
        row1 = QHBoxLayout()
        row1.setSpacing(4)
        lbl_b = QLabel('Buscar:')
        lbl_b.setFont(_fnt_sm)
        lbl_b.setStyleSheet(f'color: {TEXT_LABEL}; border: none;')
        lbl_b.setFixedWidth(62)
        row1.addWidget(lbl_b)
        self._search_input = QLineEdit()
        self._search_input.setFont(_fnt_input)
        self._search_input.setStyleSheet(_input_qss)
        self._search_input.setPlaceholderText('texto ou bytes hex...')
        self._search_input.returnPressed.connect(self._do_search_next)
        row1.addWidget(self._search_input, stretch=1)
        self._search_mode = QComboBox()
        self._search_mode.addItems(['ASCII', 'HEX'])
        self._search_mode.setStyleSheet(_combo_qss)
        self._search_mode.setFixedWidth(78)
        row1.addWidget(self._search_mode)
        _btn_qss_sm = f'QPushButton {{ background: {UNION_BLUE}; color: {WHITE}; border: none; border-radius: 3px; padding: 4px 10px; font-size: 9pt; }}QPushButton:hover {{ background: {PRIMARY_HOVER}; }}QPushButton:disabled {{ background: #444; color: #888; }}'
        _btn_nav_qss = f'QPushButton {{ background: transparent; color: {WHITE}; border: 1px solid {BORDER}; border-radius: 3px; }}QPushButton:hover {{ background: {UNION_BLUE}; border-color: {UNION_ACCENT}; }}QPushButton:disabled {{ background: #333; color: #666; }}'
        btn_prev = QPushButton()
        btn_prev.setToolTip('Anterior')
        btn_prev.setCursor(QCursor(Qt.PointingHandCursor))
        btn_prev.setStyleSheet(_btn_nav_qss)
        btn_prev.setFixedSize(30, 28)
        btn_prev.clicked.connect(self._do_search_prev)
        self._aplicar_svg_btn(btn_prev, 'icons_svg/caret-up-square.svg', 14)
        row1.addWidget(btn_prev)
        btn_next = QPushButton()
        btn_next.setToolTip('Proximo')
        btn_next.setCursor(QCursor(Qt.PointingHandCursor))
        btn_next.setStyleSheet(_btn_nav_qss)
        btn_next.setFixedSize(30, 28)
        btn_next.clicked.connect(self._do_search_next)
        self._aplicar_svg_btn(btn_next, 'icons_svg/caret-down-square.svg', 14)
        row1.addWidget(btn_next)
        sf_lay.addLayout(row1)
        row2 = QHBoxLayout()
        row2.setSpacing(4)
        lbl_r = QLabel('Substituir:')
        lbl_r.setFont(_fnt_sm)
        lbl_r.setStyleSheet(f'color: {TEXT_LABEL}; border: none;')
        lbl_r.setFixedWidth(62)
        row2.addWidget(lbl_r)
        self._replace_input = QLineEdit()
        self._replace_input.setFont(_fnt_input)
        self._replace_input.setStyleSheet(_input_qss)
        self._replace_input.setPlaceholderText('novo valor (mesmo modo)...')
        row2.addWidget(self._replace_input, stretch=1)
        btn_rep = QPushButton('Substituir')
        btn_rep.setCursor(QCursor(Qt.PointingHandCursor))
        btn_rep.setStyleSheet(_btn_qss_sm)
        btn_rep.setFixedHeight(28)
        btn_rep.clicked.connect(self._do_replace_one)
        row2.addWidget(btn_rep)
        btn_rep_all = QPushButton('Subst. Tudo')
        btn_rep_all.setCursor(QCursor(Qt.PointingHandCursor))
        btn_rep_all.setStyleSheet(f'QPushButton {{ background: {ORANGE}; color: {WHITE}; border: none; border-radius: 3px; padding: 4px 10px; font-size: 9pt; }}QPushButton:hover {{ background: {RED}; }}')
        btn_rep_all.setFixedHeight(28)
        btn_rep_all.clicked.connect(self._do_replace_all)
        row2.addWidget(btn_rep_all)
        sf_lay.addLayout(row2)
        self._search_status = QLabel('')
        self._search_status.setFont(QFont('Segoe UI', 9))
        self._search_status.setStyleSheet(f'color: {TEXT_MUTED}; border: none; padding: 0 2px;')
        sf_lay.addWidget(self._search_status)
        parent_layout.addWidget(self._search_frame)
    def _parse_search_term(self, text: str) -> Optional[bytes]:
        '''Converte o termo de busca em bytes conforme o modo selecionado.'''
        if not text:
            return
        try:
            if self._search_mode.currentText() == 'ASCII':
                return text.encode('utf-8')
            clean = ''.join(text.strip().split())
            if len(clean) % 2 != 0:
                return
            return bytes.fromhex(clean)
        except (ValueError, UnicodeEncodeError):
            return
    def _get_current_bytes(self) -> Optional[bytes]:
        '''Retorna os bytes atuais do editor (parseados do hex).'''
        return self._try_parse_silent()
    def _find_all(self, needle: bytes, haystack: bytes) -> list:
        '''Encontra todas as posicoes de needle em haystack.'''
        if not needle:
            return []
        positions = []
        start = 0
        limit = 50000
        while len(positions) < limit:
            pos = haystack.find(needle, start)
            if pos < 0:
                break
            positions.append(pos)
            start = pos + 1
        return positions
    def _do_search_next(self):
        '''Busca proximo ÔÇö encontra e navega para a proxima ocorrencia.'''
        term = self._parse_search_term(self._search_input.text())
        if term is None:
            mode = self._search_mode.currentText()
            if mode == 'HEX':
                self._search_status.setText('Hex invalido. Use pares: A0 FF 01')
            else:
                self._search_status.setText('Termo de busca vazio.')
            self._search_status.setStyleSheet(f'color: {RED}; border: none; padding: 0 2px;')
            return
        data = self._get_current_bytes()
        if data is None:
            self._search_status.setText('Dados hex invalidos no editor.')
            self._search_status.setStyleSheet(f'color: {RED}; border: none; padding: 0 2px;')
            return
        self._search_matches = self._find_all(term, data)
        if not self._search_matches:
            self._search_status.setText('Nenhuma ocorrencia encontrada.')
            self._search_status.setStyleSheet(f'color: {YELLOW}; border: none; padding: 0 2px;')
            self._search_idx = -1
            return
        if self._search_idx < 0 or self._search_idx >= len(self._search_matches) - 1:
            self._search_idx = 0
        else:
            self._search_idx += 1
        self._navigate_to_match(term)
    def _do_search_prev(self):
        '''Busca anterior ÔÇö navega para a ocorrencia anterior.'''
        term = self._parse_search_term(self._search_input.text())
        if term is None:
            return
        data = self._get_current_bytes()
        if data is None:
            return
        self._search_matches = self._find_all(term, data)
        if not self._search_matches:
            self._search_status.setText('Nenhuma ocorrencia encontrada.')
            self._search_status.setStyleSheet(f'color: {YELLOW}; border: none; padding: 0 2px;')
            self._search_idx = -1
            return
        if self._search_idx <= 0:
            self._search_idx = len(self._search_matches) - 1
        else:
            self._search_idx -= 1
        self._navigate_to_match(term)
    def _navigate_to_match(self, needle: bytes):
        '''Navega o editor hex ate a ocorrencia atual e destaca hex + ASCII.'''
        if self._search_idx < 0 or self._search_idx >= len(self._search_matches):
            return
        pos = self._search_matches[self._search_idx]
        total = len(self._search_matches)
        offset_hex = f'0x{pos:X}'
        self._search_status.setText(f'Ocorrencia {self._search_idx + 1} de {total} (offset {offset_hex})')
        self._search_status.setStyleSheet(f'color: {GREEN}; border: none; padding: 0 2px;')
        line_num = pos // 16
        col_in_line = pos % 16
        n_bytes = len(needle)
        self._syncing = True
        try:
            hex_block = self._hex_edit.document().findBlockByLineNumber(line_num)
            if not hex_block.isValid():
                self._syncing = False
                return
        finally:
            self._syncing = False
        try:
            hex_cursor = self._hex_edit.textCursor()
            hex_char_pos = hex_block.position() + col_in_line * 3
            hex_cursor.setPosition(hex_char_pos)
            hex_n_chars = n_bytes * 3 - 1
            hex_cursor.movePosition(hex_cursor.Right, hex_cursor.KeepAnchor, hex_n_chars)
            self._hex_edit.setTextCursor(hex_cursor)
            self._hex_edit.centerCursor()
            asc_block = self._asc_view.document().findBlockByLineNumber(line_num)
            if asc_block.isValid():
                asc_cursor = self._asc_view.textCursor()
                asc_char_pos = asc_block.position() + col_in_line
                asc_cursor.setPosition(asc_char_pos)
                asc_cursor.movePosition(asc_cursor.Right, asc_cursor.KeepAnchor, n_bytes)
                self._asc_view.setTextCursor(asc_cursor)
        finally:
            self._syncing = False
        self._hex_edit.setFocus()
    def _do_replace_one(self):
        '''Substitui a ocorrencia atual.'''
        search_bytes = self._parse_search_term(self._search_input.text())
        replace_bytes = self._parse_search_term(self._replace_input.text())
        if search_bytes is None:
            self._search_status.setText('Termo de busca invalido.')
            self._search_status.setStyleSheet(f'color: {RED}; border: none; padding: 0 2px;')
            return
        if replace_bytes is None:
            self._search_status.setText('Termo de substituicao invalido.')
            self._search_status.setStyleSheet(f'color: {RED}; border: none; padding: 0 2px;')
            return
        data = self._get_current_bytes()
        if data is None:
            self._search_status.setText('Dados hex invalidos no editor.')
            self._search_status.setStyleSheet(f'color: {RED}; border: none; padding: 0 2px;')
            return
        if self._search_idx < 0 or not self._search_matches:
            self._search_matches = self._find_all(search_bytes, data)
            if not self._search_matches:
                self._search_status.setText('Nenhuma ocorrencia para substituir.')
                self._search_status.setStyleSheet(f'color: {YELLOW}; border: none; padding: 0 2px;')
                return
            self._search_idx = 0
        pos = self._search_matches[self._search_idx]
        new_data = data[:pos] + replace_bytes + data[pos + len(search_bytes):]
        self._edit_data = new_data
        self._populate(new_data)
        self._search_matches = self._find_all(search_bytes, new_data)
        if self._search_idx >= len(self._search_matches):
            self._search_idx = max(0, len(self._search_matches) - 1)
        remaining = len(self._search_matches)
        self._search_status.setText(f'Substituido em offset 0x{pos:X}. {remaining} ocorrencia(s) restante(s).')
        self._search_status.setStyleSheet(f'color: {GREEN}; border: none; padding: 0 2px;')
        if self._search_matches:
            self._navigate_to_match(search_bytes)
    def _do_replace_all(self):
        '''Substitui todas as ocorrencias.'''
        search_bytes = self._parse_search_term(self._search_input.text())
        replace_bytes = self._parse_search_term(self._replace_input.text())
        if search_bytes is None:
            self._search_status.setText('Termo de busca invalido.')
            self._search_status.setStyleSheet(f'color: {RED}; border: none; padding: 0 2px;')
            return
        if replace_bytes is None:
            self._search_status.setText('Termo de substituicao invalido.')
            self._search_status.setStyleSheet(f'color: {RED}; border: none; padding: 0 2px;')
            return
        data = self._get_current_bytes()
        if data is None:
            self._search_status.setText('Dados hex invalidos no editor.')
            self._search_status.setStyleSheet(f'color: {RED}; border: none; padding: 0 2px;')
            return
        matches = self._find_all(search_bytes, data)
        if not matches:
            self._search_status.setText('Nenhuma ocorrencia para substituir.')
            self._search_status.setStyleSheet(f'color: {YELLOW}; border: none; padding: 0 2px;')
            return
        count = len(matches)
        new_data = data.replace(search_bytes, replace_bytes)
        self._edit_data = new_data
        self._populate(new_data)
        self._search_matches = []
        self._search_idx = -1
        self._search_status.setText(f'{count} ocorrencia(s) substituida(s).')
        self._search_status.setStyleSheet(f'color: {GREEN}; border: none; padding: 0 2px;')
class _PropertiesDialog(QDialog):
    def __init__(self, entry: EntryInfo, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f'Propriedades ÔÇö {entry.name}')
        self.resize(420, 340)
        self.setStyleSheet(f'\n            QDialog {{ background: {BG_WHITE}; color: {TEXT}; }}\n            QLabel {{ background: transparent; }}\n        ')
        lay = QFormLayout(self)
        lay.setSpacing(10)
        lay.setContentsMargins(16, 16, 16, 16)
        title = QLabel(f'Propriedades de: {entry.name}')
        title.setFont(QFont('Segoe UI', 12, QFont.Bold))
        title.setStyleSheet(f'color: {PRIMARY}; padding-bottom: 8px;')
        lay.addRow(title)
        def _add(label, value):
            lbl = QLabel(f'{label}:')
            lbl.setFont(QFont('Segoe UI', 10, QFont.Bold))
            lbl.setStyleSheet(f'color: {TEXT_LABEL};')
            val = QLabel(str(value))
            val.setFont(QFont('Consolas', 10))
            val.setStyleSheet(f'color: {TEXT};')
            val.setTextInteractionFlags(Qt.TextSelectableByMouse)
            lay.addRow(lbl, val)
        _add('Nome', entry.name)
        _add('Caminho', entry.path)
        _add('Tipo', 'Pasta' if entry.is_dir else 'Arquivo')
        _add('Tamanho', entry.size_str)
        _add('Permissoes', entry.permissions)
        _add('UID / GID', f'{entry.uid} / {entry.gid}')
        _add('Inode', str(entry.inode))
        _add('Modificado', entry.mtime_str)
        _add('Modo (octal)', octal_permissions(entry.mode))
class FmgrWidget(QWidget):
    '''File Manager Widget ÔÇö padrao visual UNION.'''
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName(_OBJ_NAME)
        self._engine = FmgrEngine()
        self._backup_mgr = BackupManager()
        self._img_path = None
        self._backup_feito = False
        self._worker = None
        self._current_path = '/'
        self._clipboard_path = None
        self._clipboard_op = None
        self._inicializar_ui()
        self._exibir_boas_vindas()
    def _inicializar_ui(self):
        s = f'#{_OBJ_NAME}'
        self.setStyleSheet(''.join(['\n            ', f'{s}', ' {\n                background-color: ', f'{BG}', ';\n                color: ', f'{TEXT}', ";\n                font-family: 'Segoe UI', 'Calibri', sans-serif;\n                font-size: 13px;\n            }\n            ", f'{s}', ' QLabel {\n                color: ', f'{TEXT}', ';\n                background: transparent;\n            }\n            ', f'{s}', ' QScrollArea {\n                border: none;\n                background: transparent;\n            }\n            ', f'{s}', ' QScrollBar:vertical {\n                background: ', f'{BG_DARK}', '; width: 10px; border-radius: 5px;\n            }\n            ', f'{s}', ' QScrollBar::handle:vertical {\n                background: ', f'{UNION_ACCENT}', '; border-radius: 5px; min-height: 30px;\n            }\n            ', f'{s}', ' QScrollBar::handle:vertical:hover {\n                background: ', f'{UNION_BLUE}', ';\n            }\n            ', f'{s}', ' QScrollBar::add-line:vertical, ', f'{s}', ' QScrollBar::sub-line:vertical {\n                height: 0px;\n            }\n            ', f'{s}', ' QScrollBar:horizontal {\n                background: ', f'{BG_DARK}', '; height: 10px; border-radius: 5px;\n            }\n            ', f'{s}', ' QScrollBar::handle:horizontal {\n                background: ', f'{UNION_ACCENT}', '; border-radius: 5px; min-width: 30px;\n            }\n            ', f'{s}', ' QScrollBar::handle:horizontal:hover {\n                background: ', f'{UNION_BLUE}', ';\n            }\n            ', f'{s}', ' QScrollBar::add-line:horizontal, ', f'{s}', ' QScrollBar::sub-line:horizontal {\n                width: 0px;\n            }\n            ', f'{s}', ' QSplitter::handle {\n                background: ', f'{BORDER}', '; width: 1px;\n            }\n        ']))
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)
        layout_principal.addWidget(self._criar_corpo(), stretch=1)
    def _criar_corpo(self) -> QSplitter:
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._criar_painel_esquerdo())
        splitter.addWidget(self._criar_painel_direito())
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        return splitter
    def _criar_painel_esquerdo(self) -> QWidget:
        container = QWidget()
        container.setStyleSheet(f'background-color: {BG_WHITE};')
        container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        toolbar = QFrame()
        toolbar.setStyleSheet(f'\n            QFrame {{ background-color: {BG_WHITE}; border-bottom: 1px solid {BORDER}; }}\n        ')
        tb_lay = QHBoxLayout(toolbar)
        tb_lay.setContentsMargins(12, 8, 12, 8)
        tb_lay.setSpacing(8)
        self._btn_open = QPushButton('Abrir Imagem')
        self._btn_open.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_open.setStyleSheet(gerar_qss_botao())
        self._btn_open.setMinimumHeight(34)
        self._btn_open.clicked.connect(self._on_open)
        tb_lay.addWidget(self._btn_open)
        self._btn_back = QPushButton('Voltar')
        self._btn_back.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_back.setStyleSheet(gerar_qss_botao_outline())
        self._btn_back.setMinimumHeight(34)
        self._btn_back.setEnabled(False)
        self._btn_back.clicked.connect(self._on_back)
        tb_lay.addWidget(self._btn_back)
        self._btn_refresh = QPushButton('Atualizar')
        self._btn_refresh.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_refresh.setStyleSheet(gerar_qss_botao_outline())
        self._btn_refresh.setMinimumHeight(34)
        self._btn_refresh.clicked.connect(self._on_refresh)
        tb_lay.addWidget(self._btn_refresh)
        tb_lay.addStretch()
        self._lbl_path = QLabel('/')
        self._lbl_path.setFont(QFont('Consolas', 11, QFont.Bold))
        self._lbl_path.setStyleSheet(f'color: {PRIMARY};')
        tb_lay.addWidget(self._lbl_path)
        layout.addWidget(toolbar)
        info_frame = QFrame()
        info_frame.setStyleSheet(f'\n            QFrame {{\n                background-color: {BG};\n                border-bottom: 1px solid {BORDER};\n                padding: 6px 12px;\n            }}\n        ')
        info_lay = QHBoxLayout(info_frame)
        info_lay.setContentsMargins(12, 4, 12, 4)
        info_lay.setSpacing(16)
        self._lbl_fs = QLabel('Nenhuma imagem aberta')
        self._lbl_fs.setFont(QFont('Segoe UI', 10))
        self._lbl_fs.setStyleSheet(f'color: {TEXT_MUTED};')
        info_lay.addWidget(self._lbl_fs)
        self._lbl_vol_info = QLabel('')
        self._lbl_vol_info.setFont(QFont('Segoe UI', 10))
        self._lbl_vol_info.setStyleSheet(f'color: {TEXT_LABEL};')
        info_lay.addWidget(self._lbl_vol_info)
        info_lay.addStretch()
        self._lbl_status = QLabel('Pronto')
        self._lbl_status.setFont(QFont('Segoe UI', 10))
        self._lbl_status.setStyleSheet(f'color: {TEXT_MUTED};')
        info_lay.addWidget(self._lbl_status)
        layout.addWidget(info_frame)
        dev_frame = QFrame()
        dev_frame.setStyleSheet(f'\n            QFrame {{\n                background-color: {UNION_LIGHT};\n                border-bottom: 1px solid {BORDER};\n                padding: 3px 12px;\n            }}\n        ')
        dev_lay = QHBoxLayout(dev_frame)
        dev_lay.setContentsMargins(12, 2, 12, 2)
        lbl_dev = QLabel('Area em desenvolvimento ÔÇö pode haver erros. Seu feedback e importante para melhorarmos esta ferramenta.')
        lbl_dev.setFont(QFont('Segoe UI', 9))
        lbl_dev.setStyleSheet(f'color: {UNION_BLUE};')
        lbl_dev.setWordWrap(True)
        dev_lay.addWidget(lbl_dev)
        layout.addWidget(dev_frame)
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(['Nome', 'Tamanho', 'Permissoes', 'Modificado'])
        self._tree.setRootIsDecorated(False)
        self._tree.setAlternatingRowColors(True)
        self._tree.setSortingEnabled(True)
        self._tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_context_menu)
        self._tree.itemDoubleClicked.connect(self._on_double_click)
        self._tree.setStyleSheet(f"\n            QTreeWidget {{\n                background: {BG_WHITE};\n                color: {TEXT};\n                border: none;\n                font-family: 'Consolas', 'Courier New', monospace;\n                font-size: 12px;\n                alternate-background-color: {BG};\n            }}\n            QTreeWidget::item {{\n                padding: 3px 0;\n                min-height: 22px;\n            }}\n            QTreeWidget::item:selected {{\n                background: {UNION_LIGHT};\n                color: {PRIMARY};\n            }}\n            QTreeWidget::item:hover {{\n                background: {BG};\n            }}\n            QHeaderView::section {{\n                background: {BG_WHITE};\n                color: {TEXT_MUTED};\n                border: none;\n                border-bottom: 2px solid {BORDER};\n                padding: 6px 8px;\n                font-family: 'Segoe UI';\n                font-weight: bold;\n                font-size: 10px;\n                text-transform: uppercase;\n            }}\n        ")
        hdr = self._tree.header()
        hdr.setStretchLastSection(True)
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        for i in (1, 2, 3):
            hdr.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        layout.addWidget(self._tree, stretch=1)
        return container
    def _criar_painel_direito(self) -> QWidget:
        container = QWidget()
        container.setStyleSheet(f'background-color: {BG};')
        container.setMinimumWidth(300)
        container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 16, 16, 16)
        layout.setSpacing(8)
        lbl_titulo = QLabel('Logs do Sistema')
        lbl_titulo.setFont(QFont('Segoe UI', 12, QFont.Bold))
        lbl_titulo.setStyleSheet(f'color: {TEXT}; padding-bottom: 4px;')
        layout.addWidget(lbl_titulo)
        self._log = LogSeguro(self)
        layout.addWidget(self._log, stretch=1)
        layout_btns = QHBoxLayout()
        layout_btns.setSpacing(8)
        btn_limpar = QPushButton('Limpar Log')
        btn_limpar.setCursor(QCursor(Qt.PointingHandCursor))
        btn_limpar.setStyleSheet(gerar_qss_botao_outline())
        btn_limpar.clicked.connect(self._limpar_log)
        layout_btns.addWidget(btn_limpar)
        btn_audit = QPushButton('Audit')
        btn_audit.setCursor(QCursor(Qt.PointingHandCursor))
        btn_audit.setStyleSheet(gerar_qss_botao_outline())
        btn_audit.clicked.connect(self._on_audit)
        layout_btns.addWidget(btn_audit)
        btn_info = QPushButton('Info')
        btn_info.setCursor(QCursor(Qt.PointingHandCursor))
        btn_info.setStyleSheet(gerar_qss_botao_outline())
        btn_info.clicked.connect(self._on_info)
        layout_btns.addWidget(btn_info)
        layout_btns.addStretch()
        layout.addLayout(layout_btns)
        return container
    def _on_context_menu_readonly(self, pos):
        '''Menu de contexto para modos NVRAM/RAW.'''
        item = self._tree.itemAt(pos)
        if not item:
            return
        user_data = item.data(0, Qt.UserRole)
        if not user_data:
            return
        menu = QMenu(self)
        menu.setStyleSheet(f"\n            QMenu {{\n                background: {BG_WHITE}; color: {TEXT};\n                border: 1px solid {BORDER};\n                font-family: 'Segoe UI'; font-size: 12px; padding: 4px;\n            }}\n            QMenu::item {{\n                padding: 6px 28px 6px 12px; border-radius: 3px;\n            }}\n            QMenu::item:selected {{\n                background: {UNION_LIGHT}; color: {PRIMARY};\n            }}\n            QMenu::separator {{\n                height: 1px; background: {BORDER}; margin: 4px 8px;\n            }}\n        ")
        if hasattr(user_data, 'data_off'):
            act_hex = menu.addAction('Visualizar Hex')
            act_export = menu.addAction('Exportar NV Item')
            act_props = menu.addAction('Propriedades')
            action = menu.exec_(self._tree.mapToGlobal(pos))
            if action == act_hex:
                self._on_nvram_item_dblclick(user_data)
                return
            if action == act_export:
                self._do_export_nv_item(user_data)
                return
            if action == act_props:
                self._do_nv_item_props(user_data)
                return
            return
        if user_data == 'raw_hex':
            raw = self._engine.raw_data
            if not raw:
                return
            name = os.path.basename(self._engine.img_path)
            editavel = not self._engine.is_readonly
            if editavel:
                act_edit = menu.addAction('Editar Hex')
                act_view = menu.addAction('Visualizar Hex')
                menu.addSeparator()
                act_export = menu.addAction('Exportar')
                action = menu.exec_(self._tree.mapToGlobal(pos))
                if action == act_edit:
                    self._do_edit_raw_hex(name, raw)
                    return
                if action == act_view:
                    dlg = _HexViewDialog(name, raw, self)
                    dlg.exec_()
                    return
                if action == act_export:
                    self._do_export_raw()
                    return
                return
            act_hex = menu.addAction('Visualizar Hex')
            menu.addSeparator()
            act_export = menu.addAction('Exportar')
            action = menu.exec_(self._tree.mapToGlobal(pos))
            if action == act_hex:
                dlg = _HexViewDialog(name, raw, self)
                dlg.exec_()
                return
            if action == act_export:
                self._do_export_raw()
    def _do_export_nv_item(self, nv_item):
        '''Exporta dados de um NV item para arquivo local.'''
        parser = self._engine.nvram_parser
        if not parser:
            return
        data = parser.read_nv_data(nv_item)
        if not data:
            self._log.aviso('Dados nao disponiveis.')
            return
        dest, _ = QFileDialog.getSaveFileName(self, 'Exportar NV Item', nv_item.name, 'Binario (*.bin);;Todos (*)')
        if not dest:
            return
        try:
            with open(dest, 'wb') as f:
                f.write(data)
            self._log.sucesso(f'Exportado: {nv_item.name} ({format_size(len(data))})')
        except Exception:
            self._log.erro('Falha ao exportar.')
    def _do_nv_item_props(self, nv_item):
        '''Exibe propriedades de um NV item.'''
        self._log.separador()
        self._log.prop('Nome', nv_item.name)
        self._log.prop('Categoria', nv_item.category)
        self._log.prop('Tamanho', format_size(nv_item.data_size))
        if 'nvdata/' in nv_item.path:
            self._log.prop('Caminho NV', nv_item.path.split('nvdata/')[-1])
            return
        None(None, nv_item.name)
    def _on_context_menu(self, pos):
        if self._engine.is_nvram or self._engine.is_raw:
            self._on_context_menu_readonly(pos)
            return
        if self._engine.raw_data is not None:
            self._on_context_menu_readonly(pos)
            return
        item = self._tree.itemAt(pos)
        menu = QMenu(self)
        menu.setStyleSheet(f"\n            QMenu {{\n                background: {BG_WHITE}; color: {TEXT};\n                border: 1px solid {BORDER};\n                font-family: 'Segoe UI'; font-size: 12px; padding: 4px;\n            }}\n            QMenu::item {{\n                padding: 6px 28px 6px 12px; border-radius: 3px;\n            }}\n            QMenu::item:selected {{\n                background: {UNION_LIGHT}; color: {PRIMARY};\n            }}\n            QMenu::separator {{\n                height: 1px; background: {BORDER}; margin: 4px 8px;\n            }}\n        ")
        if item:
            entry = item.data(0, Qt.UserRole)
            if entry:
                act_export = menu.addAction('Export')
                menu.addSeparator()
                act_cut = menu.addAction('Cut')
                act_copy = menu.addAction('Copy')
                act_paste = menu.addAction('Paste')
                act_paste.setEnabled(self._clipboard_path is not None)
                menu.addSeparator()
                act_rename = menu.addAction('Rename')
                act_delete = menu.addAction('Delete')
                menu.addSeparator()
                act_newfolder = menu.addAction('New Folder')
                act_newtext = menu.addAction('New Text File')
                menu.addSeparator()
                act_hex = menu.addAction('Visualizar Hex')
                act_text = menu.addAction('Visualizar Texto')
                act_edit_text = None
                act_edit_hex = None
                if not entry.is_dir:
                    menu.addSeparator()
                    act_edit_text = menu.addAction('Editar (Texto)')
                    act_edit_hex = menu.addAction('Editar (Hex)')
                menu.addSeparator()
                act_chmod = menu.addAction('Change Permission')
                act_props = menu.addAction('Properties')
                action = menu.exec_(self._tree.mapToGlobal(pos))
                if action == act_export:
                    self._do_export(entry)
                    return
                if action == act_cut:
                    self._do_cut(entry)
                    return
                if action == act_copy:
                    self._do_copy(entry)
                    return
                if action == act_paste:
                    self._do_paste()
                    return
                if action == act_rename:
                    self._do_rename(entry)
                    return
                if action == act_delete:
                    self._do_delete(entry)
                    return
                if action == act_newfolder:
                    self._do_new_folder()
                    return
                if action == act_newtext:
                    self._do_new_text_file()
                    return
                if action == act_hex:
                    self._do_open_hex(entry)
                    return
                if action == act_text:
                    self._do_open_text(entry)
                    return
                if action == act_edit_text and act_edit_text:
                    self._do_edit_text(entry)
                    return
                if action == act_edit_hex and act_edit_hex:
                    self._do_edit_hex(entry)
                    return
                if action == act_chmod:
                    self._do_change_permission(entry)
                    return
                if action == act_props:
                    self._do_properties(entry)
                    return
                return
            return
        act_paste = menu.addAction('Paste')
        act_paste.setEnabled(self._clipboard_path is not None)
        menu.addSeparator()
        act_newfolder = menu.addAction('New Folder')
        act_newtext = menu.addAction('New Text File')
        menu.addSeparator()
        act_import = menu.addAction('Import File')
        action = menu.exec_(self._tree.mapToGlobal(pos))
        if action == act_paste:
            self._do_paste()
            return
        if action == act_newfolder:
            self._do_new_folder()
            return
        if action == act_newtext:
            self._do_new_text_file()
            return
        if action == act_import:
            self._do_import()
    def _on_open(self):
        from pathlib import Path
        docs = str(Path.home() / 'Documents')
        if not os.path.isdir(docs):
            docs = str(Path.home())
        path, _ = QFileDialog.getOpenFileName(self, 'Abrir Imagem de Particao', docs, 'Imagens de Particao (*.img *.bin *.raw *.nvram);;Todos (*)')
        if not path:
            return
        self._img_path = path
        self._backup_feito = False
        self._log.separador()
        self._log.info(f'Abrindo: {os.path.basename(path)}')
        self._set_busy(True)
        self._worker = _WorkerThread(self._engine, 'open', path=path)
        self._worker.log_emitido.connect(self._on_log)
        self._worker.finalizado.connect(self._on_open_done)
        self._worker.start()
    def _on_open_done(self, ok, msg, _):
        self._set_busy(False)
        if ok:
            self._log.sucesso(msg)
            if self._engine.is_nvram:
                self._exibir_nvram()
                return
            if self._engine.is_raw:
                self._exibir_raw()
                return
            info = self._engine.volume_info()
            if info:
                self._lbl_fs.setText(f'Particao ÔÇö {info.get('last_mounted', '')}')
                self._lbl_vol_info.setText(f'{info.get('total', '?')} total | {info.get('free', '?')} livre')
                for k, v in info.items():
                    self._log.prop(k, v)
            self._current_path = '/'
            self._refresh_tree()
            self._atualizar_status('Imagem carregada')
            self._diagnosticar_capacidades()
            return
        self._log.erro(msg)
    def _exibir_nvram(self):
        '''Exibe NVRAM parseada na tree e log.'''
        parser = self._engine.nvram_parser
        self._tree.clear()
        self._btn_back.setEnabled(False)
        self._lbl_path.setText('/ NVRAM MediaTek')
        fs_name = self._engine.fs_type_name
        self._lbl_fs.setText(f'Formato: {fs_name} (somente leitura)')
        self._lbl_vol_info.setText(f'{format_size(self._engine.nvram_parser.size)}')
        self._log.separador()
        self._log.info(f'Formato detectado: {fs_name}')
        self._log.sucesso('Leitura: disponivel')
        self._log.aviso('Escrita: indisponivel (somente leitura)')
        if parser is None:
            self._log.aviso('Indice nao parseado ÔÇö exibindo como hex')
            self._exibir_raw()
            return
        summary = parser.summary()
        for k, v in summary.items():
            if k.startswith('cat_'):
                self._log.prop(k.replace('cat_', '').upper(), f'{v} items')
            else:
                self._log.prop(k.replace('_', ' ').title(), v)
        imeis = parser.imeis
        if imeis:
            self._log.separador()
            for r in imeis:
                self._log.sucesso(f'{r.label}: {r.full}')
            if parser.key_used:
                self._log.info(f'Chave: {parser.key_used}')
            if parser.ldi_count > len(imeis):
                self._log.info(f'{parser.ldi_count - len(imeis)} copias de backup encontradas (ignoradas)')
        elif parser.ldi_count > 0:
            self._log.separador()
            if not parser.has_crypto:
                self._log.aviso('Decodificacao indisponivel ÔÇö instale o componente de criptografia para visualizar IMEI.')
            else:
                self._log.aviso('Nao foi possivel decodificar IMEI. A chave pode ser diferente para este modelo.')
        self._log.separador()
        cats = parser.items_by_category()
        cat_order = ['IMEI', 'WIFI', 'BT', 'SERIAL', 'SEGURANCA', 'CONFIG', 'CALIBRACAO', 'OUTROS']
        cat_icons = {'IMEI': '­ƒô▒', 'WIFI': '­ƒôí', 'BT': '­ƒôí', 'SERIAL': '­ƒöì', 'SEGURANCA': '­ƒöÆ', 'CONFIG': 'ÔÜÖ´©Å', 'CALIBRACAO': '­ƒöº', 'OUTROS': '­ƒôä'}
        cat_display_names = {'IMEI': 'ARQUIVOS IMEI'}
        if imeis:
            qtd = len(imeis)
            titulo_imei = 'IMEI DECODIFICADO (Dual SIM)' if qtd >= 2 else 'IMEI DECODIFICADO (Single SIM)'
            imei_parent = QTreeWidgetItem([f'­ƒô▒ {titulo_imei}', '', '', ''])
            imei_parent.setForeground(0, QColor(GREEN))
            imei_parent.setFont(0, QFont('Segoe UI', 11, QFont.Bold))
            self._tree.addTopLevelItem(imei_parent)
            for r in imeis:
                child = QTreeWidgetItem([f'    {r.label}: {r.full}', f'check: {r.check_digit}', '', ''])
                child.setForeground(0, QColor(GREEN))
                self._tree.addTopLevelItem(child)
            sep = QTreeWidgetItem(['', '', '', ''])
            self._tree.addTopLevelItem(sep)
        for cat in cat_order:
            items = cats.get(cat, [])
            if not items:
                continue
            icon = cat_icons.get(cat, '­ƒôä')
            display_name = cat_display_names.get(cat, cat)
            parent = QTreeWidgetItem([f'{icon} {display_name} ({len(items)} arquivos)', '', '', ''])
            parent.setForeground(0, QColor(UNION_BLUE))
            parent.setFont(0, QFont('Segoe UI', 10, QFont.Bold))
            self._tree.addTopLevelItem(parent)
            for nv in items:
                entry_item = QTreeWidgetItem([f'    {nv.name}', format_size(nv.data_size), '', ''])
                entry_item.setData(0, Qt.UserRole, nv)
                self._tree.addTopLevelItem(entry_item)
            continue
        status_parts = [f'{len(parser.items)} NV items']
        if imeis:
            status_parts.append(f'{'SIM1' if len(imeis) == 1 else 'SIM1+SIM2'} detectado')
        self._atualizar_status(' | '.join(status_parts))
    def _exibir_raw(self):
        '''Exibe arquivo RAW no tree como hex view.'''
        self._tree.clear()
        self._btn_back.setEnabled(False)
        fs_name = self._engine.fs_type_name
        raw_data = self._engine.raw_data
        size = len(raw_data) if raw_data else 0
        editavel = not self._engine.is_readonly
        self._lbl_path.setText('/ Raw View')
        if editavel:
            self._lbl_fs.setText(f'Formato: {fs_name} (leitura/escrita)')
        else:
            self._lbl_fs.setText(f'Formato: {fs_name} (somente leitura)')
        self._lbl_vol_info.setText(format_size(size))
        self._log.separador()
        self._log.info(f'Formato detectado: {fs_name}')
        self._log.info(f'Tamanho: {format_size(size)}')
        self._log.sucesso('Leitura: disponivel')
        if editavel:
            self._log.sucesso('Escrita: disponivel (edicao hex)')
        else:
            self._log.aviso('Escrita: indisponivel (somente leitura)')
        self._log.separador()
        if editavel:
            self._log.info('Clique duas vezes para abrir o editor hex. Faca backup antes de editar.')
        else:
            self._log.info('Clique duas vezes para abrir o visualizador hex.')
        item = QTreeWidgetItem([f'­ƒôä {os.path.basename(self._engine.img_path)}', format_size(size), '', ''])
        item.setData(0, Qt.UserRole, 'raw_hex')
        item.setForeground(0, QColor(UNION_BLUE))
        self._tree.addTopLevelItem(item)
        self._atualizar_status(f'Raw ÔÇö {format_size(size)}')
    def _do_edit_raw_hex(self, name: str, data: bytes):
        '''Abre editor hex para arquivo RAW editavel (FRP, misc, etc).'''
        dlg = _EditHexDialog(name, data, self)
        if dlg.exec_() == QDialog.Accepted:
            if dlg.was_saved:
                if not self._garantir_backup():
                    return
                new_data = dlg.new_data
                self._log.info('Salvando alteracoes...')
                ok, msg = self._engine.write_raw_data(new_data)
                if ok:
                    self._log.sucesso('Alteracoes salvas com sucesso.')
                    self._exibir_raw()
                    return
                self._log.erro(msg)
    def _do_export_raw(self):
        '''Exporta arquivo RAW para disco local.'''
        raw = self._engine.raw_data
        if not raw:
            return
        name = os.path.basename(self._engine.img_path)
        dest, _ = QFileDialog.getSaveFileName(self, 'Exportar', name, 'Binario (*.bin);;Todos (*)')
        if not dest:
            return
        try:
            with open(dest, 'wb') as f:
                f.write(raw)
            self._log.sucesso(f'Exportado: {name} ({format_size(len(raw))})')
        except Exception:
            self._log.erro('Falha ao exportar.')
    def _on_nvram_item_dblclick(self, nv_item):
        '''Abre visualizador hex para NV item selecionado.'''
        parser = self._engine.nvram_parser
        if not parser:
            return
        data = parser.read_nv_data(nv_item)
        if data:
            dlg = _HexViewDialog(nv_item.name, data, self)
            dlg.exec_()
            return
        self._log.aviso('Dados nao disponiveis para este item.')
    def _on_back(self):
        if self._engine.is_nvram or self._engine.is_raw:
            return
        if self._current_path == '/':
            return
        self._current_path = self._current_path.rsplit('/', 2)[0] or '/'
        self._refresh_tree()
    def _on_refresh(self):
        if not self._engine.is_open:
            return
        if self._engine.is_nvram:
            self._exibir_nvram()
            return
        if self._engine.is_raw:
            self._exibir_raw()
            return
        self._refresh_tree()
    def _on_double_click(self, item, col):
        user_data = item.data(0, Qt.UserRole)
        if user_data is None:
            return
        if user_data == 'raw_hex':
            raw = self._engine.raw_data
            if raw:
                name = os.path.basename(self._engine.img_path)
                if not self._engine.is_readonly:
                    self._do_edit_raw_hex(name, raw)
                    return
                dlg = _HexViewDialog(name, raw, self)
                dlg.exec_()
            return
        if hasattr(user_data, 'data_off'):
            self._on_nvram_item_dblclick(user_data)
            return
        entry = user_data
        if entry.is_dir:
            self._current_path = entry.path
            self._refresh_tree()
            return
        data = self._engine.read_file(entry.path)
        if not data:
            self._log.erro(f'Falha ao ler: {entry.name}')
            return
        is_text = True
        try:
            sample = data[:4096]
            sample.decode('utf-8')
            null_ratio = sample.count(0) / max(len(sample), 1)
            if null_ratio > 0.1:
                is_text = False
        except UnicodeDecodeError:
            is_text = False
        if is_text:
            dlg = _TextViewDialog(entry.name, data, self)
        else:
            dlg = _HexViewDialog(entry.name, data, self)
        dlg.exec_()
    def _refresh_tree(self):
        self._tree.clear()
        self._lbl_path.setText(self._current_path)
        self._btn_back.setEnabled(self._current_path != '/')
        entries = self._engine.list_dir(self._current_path)
        dirs = sorted([e for e in entries if e.is_dir], key=(lambda x: x.name.lower()))
        files = sorted([e for e in entries if not e.is_dir], key=(lambda x: x.name.lower()))
        for entry in dirs + files:
            icon = '­ƒôü ' if entry.is_dir else '­ƒôä '
            item = QTreeWidgetItem([f'{icon}{entry.name}', entry.size_str if not entry.is_dir else '', entry.permissions, entry.mtime_str])
            item.setData(0, Qt.UserRole, entry)
            if entry.is_dir:
                item.setForeground(0, QColor(UNION_BLUE))
            self._tree.addTopLevelItem(item)
        self._lbl_status.setText(f'{len(dirs)} pastas, {len(files)} arquivos')
    def _do_export(self, entry: EntryInfo):
        if entry.is_dir:
            dest = QFileDialog.getExistingDirectory(self, 'Exportar para')
            if not dest:
                return
            dest = os.path.join(dest, entry.name)
        else:
            dest, _ = QFileDialog.getSaveFileName(self, 'Exportar', entry.name)
            if not dest:
                return
        self._run_op('export', src=entry.path, dest=dest)
    def _do_cut(self, entry: EntryInfo):
        self._clipboard_path = entry.path
        self._clipboard_op = 'cut'
        self._log.info(f'Recortado: {entry.name}')
    def _do_copy(self, entry: EntryInfo):
        self._clipboard_path = entry.path
        self._clipboard_op = 'copy'
        self._log.info(f'Copiado: {entry.name}')
    def _do_paste(self):
        if not self._clipboard_path:
            return
        if not self._garantir_backup():
            return
        src = self._clipboard_path
        name = src.rsplit('/', 1)[-1]
        dest = self._current_path.rstrip('/') + '/' + name
        data = self._engine.read_file(src)
        if not data:
            self._log.erro('Falha ao ler arquivo da area de transferencia.')
            return
        self._run_op('write', dest=dest, data=data)
        if self._clipboard_op == 'cut':
            self._clipboard_path = None
            self._clipboard_op = None
    def _do_rename(self, entry: EntryInfo):
        new_name, ok = QInputDialog.getText(self, 'Renomear', 'Novo nome:', text=entry.name)
        if not ok or not new_name or new_name == entry.name:
            return
        new_name = self._sanitizar_nome(new_name)
        if not new_name:
            self._log.aviso('Nome invalido.')
            return
        if not self._garantir_backup():
            return
        parent = entry.path.rsplit('/', 1)[0] or '/'
        new_path = parent.rstrip('/') + '/' + new_name
        self._run_op('rename', old=entry.path, new=new_path)
    def _do_delete(self, entry: EntryInfo):
        tipo = 'pasta' if entry.is_dir else 'arquivo'
        r = QMessageBox.warning(self, 'Confirmar Exclusao', f"Deletar {tipo} '{entry.name}'?\n\nEsta acao e irreversivel.", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if r != QMessageBox.Yes:
            return
        if not self._garantir_backup():
            return
        self._run_op('delete', path=entry.path, is_dir=entry.is_dir)
    @staticmethod
    def _sanitizar_nome(name: str) -> str:
        '''Remove caracteres perigosos de nomes de arquivo/pasta.'''
        proibidos = ['..', '/', '\\', '\x00', '|', '<', '>', '"', '?', '*']
        sanitizado = name.strip()
        for c in proibidos:
            sanitizado = sanitizado.replace(c, '')
        return sanitizado[:255]
    def _do_new_folder(self):
        name, ok = QInputDialog.getText(self, 'Nova Pasta', 'Nome da pasta:')
        if not ok or not name:
            return
        name = self._sanitizar_nome(name)
        if not name:
            self._log.aviso('Nome invalido.')
            return
        if not self._garantir_backup():
            return
        path = self._current_path.rstrip('/') + '/' + name
        self._run_op('mkdir', path=path)
    def _do_new_text_file(self):
        name, ok = QInputDialog.getText(self, 'Novo Arquivo de Texto', 'Nome:', text='novo_arquivo.txt')
        if not ok or not name:
            return
        name = self._sanitizar_nome(name)
        if not name:
            self._log.aviso('Nome invalido.')
            return
        if not self._garantir_backup():
            return
        path = self._current_path.rstrip('/') + '/' + name
        content = f'Criado por TECH UNION SOLUTIONS\n{datetime.now().isoformat()}\n'
        self._run_op('write', dest=path, data=content.encode('utf-8'))
    def _do_open_hex(self, entry: EntryInfo):
        if entry.is_dir:
            self._log.aviso('Nao e possivel abrir pasta como hex')
            return
        data = self._engine.read_file(entry.path)
        if data:
            dlg = _HexViewDialog(entry.name, data, self)
            dlg.exec_()
            return
        self._log.erro(f'Falha ao ler: {entry.name}')
    def _do_open_text(self, entry: EntryInfo):
        if entry.is_dir:
            self._log.aviso('Nao e possivel abrir pasta como texto')
            return
        data = self._engine.read_file(entry.path)
        if data:
            dlg = _TextViewDialog(entry.name, data, self)
            dlg.exec_()
            return
        self._log.erro(f'Falha ao ler: {entry.name}')
    def _do_edit_text(self, entry: EntryInfo):
        if entry.is_dir:
            self._log.aviso('Nao e possivel editar pasta')
            return
        data = self._engine.read_file(entry.path)
        if not data:
            self._log.erro(f'Falha ao ler: {entry.name}')
            return
        dlg = _EditTextDialog(entry.name, data, self)
        if dlg.exec_() == QDialog.Accepted:
            if dlg.was_saved:
                if not self._garantir_backup():
                    return
                self._log.info(f'Salvando alteracoes em {entry.name}...')
                self._run_op('write', dest=entry.path, data=dlg.new_data)
    def _do_edit_hex(self, entry: EntryInfo):
        if entry.is_dir:
            self._log.aviso('Nao e possivel editar pasta')
            return
        data = self._engine.read_file(entry.path)
        if not data:
            self._log.erro(f'Falha ao ler: {entry.name}')
            return
        dlg = _EditHexDialog(entry.name, data, self)
        if dlg.exec_() == QDialog.Accepted:
            if dlg.was_saved:
                if not self._garantir_backup():
                    return
                self._log.info(f'Salvando alteracoes em {entry.name}...')
                self._run_op('write', dest=entry.path, data=dlg.new_data)
    def _do_change_permission(self, entry: EntryInfo):
        full = self._engine.get_info(entry.path) or entry
        dlg = _ChangePermDialog(full, self)
        if dlg.exec_() != QDialog.Accepted:
            return
        if not self._garantir_backup():
            return
        new_mode = dlg.new_mode
        new_uid = dlg.new_uid
        new_gid = dlg.new_gid
        mode_changed = new_mode is not None and new_mode != full.mode
        owner_changed = new_uid != full.uid or new_gid != full.gid
        if mode_changed:
            self._log.info(f'Alterando permissoes: {octal_permissions(new_mode)}')
            self._set_busy(True)
            self._worker = _WorkerThread(self._engine, 'chmod', path=entry.path, mode=new_mode)
            self._worker.log_emitido.connect(self._on_log)
            if owner_changed:
                def _on_chmod_done(ok, msg, _):
                    if ok:
                        self._log.sucesso('Permissoes alteradas')
                        self._log.info(f'Alterando proprietario: uid={new_uid} gid={new_gid}')
                        self._worker = _WorkerThread(self._engine, 'chown', path=entry.path, uid=new_uid, gid=new_gid)
                        self._worker.log_emitido.connect(self._on_log)
                        self._worker.finalizado.connect(self._on_op_done)
                        self._worker.start()
                        return
                    self._set_busy(False)
                    self._log.erro(msg)
                self._worker.finalizado.connect(_on_chmod_done)
            else:
                self._worker.finalizado.connect(self._on_op_done)
            self._worker.start()
            return
        if owner_changed:
            self._log.info(f'Alterando proprietario: uid={new_uid} gid={new_gid}')
            self._run_op('chown', path=entry.path, uid=new_uid, gid=new_gid)
            return
        self._log.info('Nenhuma alteracao detectada')
    def _do_properties(self, entry: EntryInfo):
        full = self._engine.get_info(entry.path)
        dlg = _PropertiesDialog(full or entry, self)
        dlg.exec_()
    def _do_import(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Importar Arquivo')
        if not path:
            return
        if not self._garantir_backup():
            return
        name = os.path.basename(path)
        dest = self._current_path.rstrip('/') + '/' + name
        self._run_op('import', src=path, dest=dest)
    def _on_audit(self):
        if not self._engine.is_open:
            self._log.aviso('Abra uma imagem primeiro')
            return
        self._log.separador()
        self._log.info('Executando auditoria do filesystem...')
        self._set_busy(True)
        self._worker = _WorkerThread(self._engine, 'audit')
        self._worker.log_emitido.connect(self._on_log)
        self._worker.finalizado.connect(self._on_audit_done)
        self._worker.start()
    def _on_audit_done(self, ok, msg, result):
        self._set_busy(False)
        if ok and isinstance(result, dict):
            for k, v in result.items():
                self._log.prop(str(k), str(v))
            if result.get('clean'):
                self._log.sucesso('Filesystem LIMPO ÔÇö sem anomalias')
                return
            self._log.aviso('Anomalias detectadas!')
            return
        self._log.erro(msg)
    def _on_info(self):
        if not self._engine.is_open:
            self._log.aviso('Abra uma imagem primeiro')
            return
        self._log.separador()
        info = self._engine.partition_info()
        if info:
            for k, v in info.items():
                self._log.prop(str(k), str(v))
            return
        self._log.erro('Falha ao obter info')
    def _diagnosticar_capacidades(self):
        '''Verifica DLL e WinFsp e informa o usuario sobre leitura/escrita.'''
        from ._fmgr_core import (resolve_bin, find_winfsp_bin, BIN_EXT4_DLL, BIN_EXT4_EXE)
        self._log.separador()
        self._log.sucesso('Leitura: disponivel')
        dll_ok = os.path.isfile(resolve_bin(BIN_EXT4_DLL))
        exe_ok = os.path.isfile(resolve_bin(BIN_EXT4_EXE))
        winfsp_ok = bool(find_winfsp_bin())
        if dll_ok:
            self._log.sucesso('Escrita (principal): disponivel')
        else:
            self._log.aviso('Escrita (principal): indisponivel ÔÇö acesse Configuracoes > Dependencias para instalar.')
        if exe_ok and winfsp_ok:
            self._log.sucesso('Escrita (alternativo): disponivel')
        elif exe_ok and not winfsp_ok:
            self._log.aviso('Escrita (alternativo): requer componente auxiliar ÔÇö acesse Configuracoes > Dependencias para instalar.')
        else:
            self._log.aviso('Escrita (alternativo): indisponivel ÔÇö acesse Configuracoes > Dependencias para instalar.')
        if not dll_ok and (not exe_ok or not winfsp_ok):
            self._log.aviso('Modo somente leitura ativo. Operacoes de escrita nao funcionarao ate as dependencias serem instaladas.')
        self._log.separador()
    def _run_op(self, op, **kwargs):
        if op not in ('open', 'export', 'audit') and not self._engine.is_open:
            self._log.aviso('Abra uma imagem primeiro.')
            return
        self._set_busy(True)
        self._worker = _WorkerThread(self._engine, op, **kwargs)
        self._worker.log_emitido.connect(self._on_log)
        self._worker.finalizado.connect(self._on_op_done)
        self._worker.start()
    def _on_op_done(self, ok, msg, _):
        self._set_busy(False)
        if ok:
            self._log.sucesso(msg)
            self._refresh_tree()
            return
        self._log.erro(msg)
    def _on_log(self, tipo, msg):
        if tipo == 'info':
            self._log.info(msg)
            return
        if tipo == 'ok':
            self._log.sucesso(msg)
            return
        if tipo == 'erro':
            self._log.erro(msg)
            return
        if tipo == 'aviso':
            self._log.aviso(msg)
    def _set_busy(self, busy):
        self._btn_open.setEnabled(not busy)
        self._btn_refresh.setEnabled(not busy)
        if busy:
            self._atualizar_status('Processando...')
            return
        self._atualizar_status('Pronto')
    def _limpar_log(self):
        self._log.limpar()
        self._log.info('Log limpo.')
    def _garantir_backup(self) -> bool:
        '''Tenta backup automatico antes da primeira escrita.
        NAO bloqueia a operacao se falhar ÔÇö apenas avisa.'''
        if self._backup_feito:
            return True
        if not self._img_path or not os.path.isfile(self._img_path):
            return True
        if not self._backup_mgr.pronto:
            self._log.aviso('Backup nao disponivel ÔÇö continue com cuidado.')
            self._backup_feito = True
            return True
        try:
            tamanho = os.path.getsize(self._img_path)
        except Exception:
            tamanho = 0
        progress = None
        if tamanho > 52428800:
            progress = QProgressDialog('Criando backup de seguranca...', None, 0, 0, self)
            progress.setWindowTitle('Backup')
            progress.setMinimumDuration(0)
            progress.setCancelButton(None)
            progress.setStyleSheet(f"\n                QProgressDialog {{\n                    background: {BG_WHITE}; color: {TEXT};\n                    font-family: 'Segoe UI'; font-size: 12px;\n                }}\n            ")
            progress.show()
            QApplication.processEvents()
        nome_bk = self._backup_mgr.criar_backup(self._img_path, 'techunion_file')
        if progress:
            progress.close()
        if nome_bk:
            self._backup_feito = True
            self._log.sucesso(f'Backup criado: {nome_bk}')
            return True
        self._log.aviso('Nao foi possivel criar backup ÔÇö continue com cuidado.')
        self._backup_feito = True
        return True
    def _atualizar_status(self, texto):
        self._lbl_status.setText(texto)
    def _exibir_boas_vindas(self):
        self._log.separador()
        self._log.info(f'TECH UNION SOLUTIONS ÔÇö Android File Manager {_VERSAO} Navegue, edite e gerencie arquivos em imagens de particao.')
        self._log.aviso('ATENCAO: Modificar um pequeno arquivo dentro de uma particao pode causar impactos significativos no funcionamento do dispositivo. Sempre verifique o que esta fazendo e faca backup antes de qualquer alteracao.')
        self._log.separador()
        self._log.aviso('Dica: Use somente em aparelhos proprios ou com autorizacao do proprietario. Solicite nota fiscal ou termo de responsabilidade ao cliente. Qualquer uso indevido e de inteira responsabilidade do operador.')
        self._log.separador()
        self._log.info('Pronto para operacao.')
    def closeEvent(self, event):
        if self._worker and self._worker.isRunning():
            self._worker.wait(2000)
        self._engine.close()
        super().closeEvent(event)
def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    w = FmgrWidget()
    w.setWindowTitle('TECH UNION ÔÇö Android File Manager')
    w.resize(1000, 700)
    w.show()
    sys.exit(app.exec_())
if __name__ == '__main__':
    main()
# WARNING: Decompyle incomplete
