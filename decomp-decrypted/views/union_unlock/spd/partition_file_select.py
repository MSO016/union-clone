import os
import json
import logging
from PyQt5.QtWidgets import (QFileDialog, QTableWidgetItem, QMessageBox)
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt
logger = logging.getLogger(__name__)
FILE_COL = 5
_PLACEHOLDER = 'Clique duplo para selecionar'
_PLACEHOLDER_COLOR = '#95a5a6'
_FILE_SELECTED_COLOR = '#2471a3'
_last_used_dir = ''
def create_file_cell():
    item = QTableWidgetItem(_PLACEHOLDER)
    item.setForeground(QColor(_PLACEHOLDER_COLOR))
    item.setFont(QFont('Segoe UI', 9))
    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
    item.setData(Qt.UserRole, '')
    return item
def on_cell_double_click(table, row, column, default_dir_fn, parent=None):
    global _last_used_dir
    if column != FILE_COL:
        return
    name_item = table.item(row, 1)
    if not name_item:
        return
    part_name = name_item.text()
    default_dir = _last_used_dir or ''
    if not default_dir:
        try:
            default_dir = default_dir_fn() if callable(default_dir_fn) else ''
        except Exception:
            pass
    fp, _ = QFileDialog.getOpenFileName(parent, f'Selecionar arquivo para {part_name}', default_dir, 'Binarios (*.bin *.img);;Todos (*.*)')
    item = table.item(row, FILE_COL)
    if not item:
        item = create_file_cell()
        table.setItem(row, FILE_COL, item)
    if not fp:
        item.setText(_PLACEHOLDER)
        item.setForeground(QColor(_PLACEHOLDER_COLOR))
        item.setToolTip('')
        item.setData(Qt.UserRole, '')
        return
    _last_used_dir = os.path.dirname(fp)
    item.setText(os.path.basename(fp))
    item.setForeground(QColor(_FILE_SELECTED_COLOR))
    item.setFont(QFont('Segoe UI', 9, QFont.Bold))
    item.setToolTip(fp)
    item.setData(Qt.UserRole, fp)
    cb = table.item(row, 0)
    if cb:
        cb.setCheckState(Qt.Checked)
def load_backup_map(table, default_dir_fn, parent=None):
    global _last_used_dir
    default_dir = ''
    try:
        default_dir = default_dir_fn() if callable(default_dir_fn) else ''
    except Exception:
        pass
    fp, _ = QFileDialog.getOpenFileName(parent, 'Selecionar Mapa de Backup', default_dir, 'Union Backup Map (union_backup_map.json);;JSON (*.json)')
    if not fp:
        return 0
    try:
        with open(fp, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        logger.error('Erro ao ler mapa de backup: %s', e)
        QMessageBox.critical(parent, 'Erro', 'Arquivo invalido. Selecione um mapa de backup gerado pelo sistema.')
        return -1
    parts = data.get('partitions', [])
    if not parts:
        QMessageBox.information(parent, 'Vazio', 'Nenhuma particao encontrada no mapa.')
        return 0
    base_dir = os.path.dirname(fp)
    _last_used_dir = base_dir
    name_to_row = {}
    for row in range(table.rowCount()):
        name_item = table.item(row, 1)
        if name_item:
            name_to_row[name_item.text()] = row
    loaded = 0
    missing = []
    for p in parts:
        pname = p.get('name', '')
        fname = p.get('filename', '')
        if not pname or not fname:
            continue
        full_path = os.path.join(base_dir, fname)
        row = name_to_row.get(pname)
        if row is None:
            continue
        if not os.path.isfile(full_path):
            missing.append(pname)
            continue
        item = table.item(row, FILE_COL)
        if not item:
            item = create_file_cell()
            table.setItem(row, FILE_COL, item)
        item.setText(fname)
        item.setForeground(QColor(_FILE_SELECTED_COLOR))
        item.setFont(QFont('Segoe UI', 9, QFont.Bold))
        item.setToolTip(full_path)
        item.setData(Qt.UserRole, full_path)
        cb = table.item(row, 0)
        if cb:
            cb.setCheckState(Qt.Checked)
        loaded += 1
        continue
    if missing:
        logger.warning('Arquivos ausentes no mapa: %s', ', '.join(missing[:20]))
    if loaded > 0 and missing:
        QMessageBox.warning(parent, 'Carregamento Parcial', f'{loaded} arquivo(s) carregado(s).\n\n{len(missing)} arquivo(s) nao encontrado(s):\n  - ' + '\n  - '.join(missing[:10]) + ('...' if len(missing) > 10 else ''))
        return loaded
    if loaded > 0:
        QMessageBox.information(parent, 'Mapa Carregado', f'{loaded} arquivo(s) carregado(s) com sucesso.')
        return loaded
    QMessageBox.warning(parent, 'Nenhum Carregado', 'Nenhum arquivo correspondente foi encontrado.')
    return loaded
def get_file_assignments(table):
    assignments = []
    for row in range(table.rowCount()):
        item = table.item(row, FILE_COL)
        if item:
            fp = item.data(Qt.UserRole)
            if fp:
                name_item = table.item(row, 1)
                if name_item:
                    assignments.append((name_item.text(), str(fp)))
    return assignments
def clear_all_files(table):
    for row in range(table.rowCount()):
        item = table.item(row, FILE_COL)
        if not item:
            continue
        if item.data(Qt.UserRole):
            item.setText(_PLACEHOLDER)
            item.setForeground(QColor(_PLACEHOLDER_COLOR))
            item.setFont(QFont('Segoe UI', 9))
            item.setToolTip('')
            item.setData(Qt.UserRole, '')
