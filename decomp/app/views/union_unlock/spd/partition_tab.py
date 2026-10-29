'''
Aba de Particoes ÔÇö widget PyQt5 modular.
Ver: alan/documentacao/16-08-2026-ARQUITETURA-SPD-INTERNA/01_MAPA_REFERENCIAS_INTERNAS.md
'''
import os
import json
import threading
import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QProgressBar, QMessageBox, QFileDialog, QComboBox, QCheckBox, QLineEdit, QProgressDialog)
from PyQt5.QtCore import (Qt, QTimer, pyqtSignal, QStandardPaths)
from PyQt5.QtGui import QFont, QColor
logger = logging.getLogger(__name__)
ENABLE_NATIVE_ENGINE = False
PARTITION_OPS_AVAILABLE = False
try:
    from app.views.union_unlock.spd.partition_ops import SPDPartitionManager
    from app.views.union_unlock.spd.model_data import ModelConfig
    PARTITION_OPS_AVAILABLE = True
except ImportError:
    try:
        from app.views.union_unlock.spd.partition_ops import SPDPartitionManager
        from app.views.union_unlock.spd.model_data import ModelConfig
        PARTITION_OPS_AVAILABLE = True
    except ImportError:
        pass
class PartitionTab(QWidget):
    '''
    Widget modular para gerenciamento de particoes SPD.
    Protocolo 100% nativo Python ÔÇö sem spd_dump.exe.
    Seletor proprio de Marca/Modelo segmentado.
    '''
    _sig_partitions_ready = pyqtSignal(list)
    _sig_fill_table = pyqtSignal(list)
    _sig_connect_fail = pyqtSignal(str)
    _sig_connected = pyqtSignal()
    _sig_spd_list_partitions = pyqtSignal()
    _sig_device_reset = pyqtSignal()
    _sig_device_post_action = pyqtSignal(str)
    _sig_op_done = pyqtSignal(bool, str, str, str)
    _sig_pause_port_scan = pyqtSignal(bool)
    _sig_connect_progress = pyqtSignal(int, str)
    _sig_op_progress = pyqtSignal(int, float)
    def __init__(self, get_model_config_fn=None, log_signal=None, parent=None):
        super().__init__(parent)
        self._get_config_ext = get_model_config_fn
        self._log_signal = log_signal
        self._part_mgr = None
        self._spd_parts = None
        self._connect_thread = None
        self._is_busy = False
        self._selected_config = None
        self._connect_dlg = None
        self._sig_partitions_ready.connect(self._on_spd_dump_done)
        self._sig_fill_table.connect(self._fill_table)
        self._sig_connect_fail.connect(self._on_connect_fail)
        self._sig_connected.connect(self._on_connected)
        self._sig_spd_list_partitions.connect(self._do_spd_list)
        self._sig_device_reset.connect(self._on_device_reset)
        self._sig_device_post_action.connect(self._on_device_post_action)
        self._sig_op_done.connect(self._on_op_done)
        self._sig_connect_progress.connect(self._on_connect_progress_ui)
        self._sig_op_progress.connect(self._on_op_progress_ui)
        self._build_ui()
        self._load_devices()
    def _build_ui(self):
        vlay = QVBoxLayout(self)
        vlay.setContentsMargins(6, 6, 6, 6)
        vlay.setSpacing(6)
        sel_bar = QWidget()
        hlay_sel = QHBoxLayout(sel_bar)
        hlay_sel.setContentsMargins(0, 0, 0, 0)
        hlay_sel.setSpacing(8)
        lbl_marca = QLabel('Marca:')
        lbl_marca.setFont(QFont('Segoe UI', 9, QFont.Bold))
        hlay_sel.addWidget(lbl_marca)
        self.combo_brand = QComboBox()
        self.combo_brand.setFixedWidth(160)
        self.combo_brand.setStyleSheet(self._combo_style())
        self.combo_brand.currentIndexChanged.connect(self._on_brand_changed)
        hlay_sel.addWidget(self.combo_brand)
        lbl_modelo = QLabel('Modelo:')
        lbl_modelo.setFont(QFont('Segoe UI', 9, QFont.Bold))
        hlay_sel.addWidget(lbl_modelo)
        self.combo_model = QComboBox()
        self.combo_model.setFixedWidth(220)
        self.combo_model.setStyleSheet(self._combo_style())
        self.combo_model.currentIndexChanged.connect(self._on_model_changed)
        hlay_sel.addWidget(self.combo_model)
        self.lbl_model_info = QLabel('')
        self.lbl_model_info.setFont(QFont('Segoe UI', 8))
        self.lbl_model_info.setStyleSheet('color: #7f8c8d;')
        hlay_sel.addWidget(self.lbl_model_info)
        hlay_sel.addSpacing(16)
        self.lbl_auth = QLabel('Auth:')
        self.lbl_auth.setFont(QFont('Segoe UI', 9, QFont.Bold))
        hlay_sel.addWidget(self.lbl_auth)
        self.combo_auth = QComboBox()
        self.combo_auth.setFixedWidth(130)
        self.combo_auth.setStyleSheet(self._combo_style())
        self.combo_auth.addItem('Auth-1', 'spd_dump')
        self.combo_auth.addItem('Auth-2', 'native')
        self.combo_auth.setCurrentIndex(0)
        self.combo_auth.setToolTip('Auth-1: Protocolo assistido\nAuth-2: Protocolo nativo')
        hlay_sel.addWidget(self.combo_auth)
        if not ENABLE_NATIVE_ENGINE:
            self.lbl_auth.hide()
            self.combo_auth.hide()
        hlay_sel.addSpacing(12)
        self.chk_advanced = QCheckBox('Autorizacao Avancada')
        self.chk_advanced.setFont(QFont('Segoe UI', 8))
        self.chk_advanced.setChecked(True)
        self.chk_advanced.setToolTip('Habilita autorizacao avancada para dispositivos protegidos')
        self.chk_advanced.setStyleSheet('\n            QCheckBox { color: #2c3e50; spacing: 4px; }\n            QCheckBox::indicator { width: 14px; height: 14px; }\n            QCheckBox::indicator:checked { background-color: #2471a3; border: 1px solid #1a5276; border-radius: 2px; }\n            QCheckBox::indicator:unchecked { background-color: #FFFFFF; border: 1px solid #bdc3c7; border-radius: 2px; }\n        ')
        hlay_sel.addWidget(self.chk_advanced)
        self.chk_force = QCheckBox('Force')
        self.chk_force.setFont(QFont('Segoe UI', 8))
        self.chk_force.setChecked(False)
        self.chk_force.setToolTip("Force: usa modo --kick do spd_dump (boot_diag -> cali_diag -> dl_diag).\nAtive se o device nao conectar normalmente ou em portas USB instaveis.\nEquivalente ao 'Force Mode' de box tools populares.")
        self.chk_force.setStyleSheet('\n            QCheckBox { color: #2c3e50; spacing: 4px; }\n            QCheckBox::indicator { width: 14px; height: 14px; }\n            QCheckBox::indicator:checked { background-color: #c0392b; border: 1px solid #922b21; border-radius: 2px; }\n            QCheckBox::indicator:unchecked { background-color: #FFFFFF; border: 1px solid #bdc3c7; border-radius: 2px; }\n        ')
        hlay_sel.addWidget(self.chk_force)
        hlay_sel.addStretch()
        sel_bar.setFixedHeight(32)
        vlay.addWidget(sel_bar)
        info_bar = QWidget()
        hlay_info = QHBoxLayout(info_bar)
        hlay_info.setContentsMargins(0, 0, 0, 0)
        hlay_info.setSpacing(8)
        self.lbl_status = QLabel('Selecione marca e modelo acima')
        self.lbl_status.setFont(QFont('Segoe UI', 9))
        hlay_info.addWidget(self.lbl_status)
        hlay_info.addStretch()
        self.btn_connect = QPushButton('Conectar SPD')
        self.btn_connect.setFixedSize(120, 28)
        self.btn_connect.setStyleSheet(self._btn_style('#2471a3'))
        self.btn_connect.clicked.connect(self._on_connect)
        hlay_info.addWidget(self.btn_connect)
        self.btn_list = QPushButton('Listar Particoes')
        self.btn_list.setFixedSize(120, 28)
        self.btn_list.setStyleSheet(self._btn_style('#2471a3'))
        self.btn_list.setEnabled(False)
        self.btn_list.clicked.connect(self._on_list)
        hlay_info.addWidget(self.btn_list)
        self.btn_cancel = QPushButton('CANCELAR')
        self.btn_cancel.setFixedSize(90, 28)
        self.btn_cancel.setStyleSheet(self._btn_style('#e74c3c'))
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._on_cancel)
        hlay_info.addWidget(self.btn_cancel)
        info_bar.setFixedHeight(36)
        vlay.addWidget(info_bar)
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(['', 'Nome', 'Tamanho', 'Tipo', 'Status', 'Arquivo'])
        h = self.table.horizontalHeader()
        h.setFont(QFont('Segoe UI', 9, QFont.Bold))
        self.table.setColumnWidth(0, 30)
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 70)
        self.table.setColumnWidth(4, 80)
        self.table.setColumnWidth(5, 200)
        h.setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        try:
            self.table.itemChanged.connect(self._on_table_item_changed)
        except Exception:
            pass
        try:
            self.table.cellDoubleClicked.connect(self._on_file_double_click)
        except Exception:
            pass
        self.table.setStyleSheet('\n            QTableWidget { background-color: #FFFFFF; border: 1px solid #bdc3c7;\n                           font-size: 11px; gridline-color: #bdc3c7; }\n            QTableWidget::item:selected { background-color: #4A90D9; color: #FFFFFF; }\n            QHeaderView::section { background-color: #E8E8E8; font-weight: bold;\n                                   font-size: 10px; border: 1px solid #bdc3c7; padding: 3px; }\n        ')
        vlay.addWidget(self.table)
        search_row = QWidget()
        hlay_search = QHBoxLayout(search_row)
        hlay_search.setContentsMargins(0, 0, 0, 0)
        hlay_search.setSpacing(6)
        lbl_search = QLabel('Buscar:')
        lbl_search.setFont(QFont('Segoe UI', 9))
        hlay_search.addWidget(lbl_search)
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText('Digite o nome da particao (ex: persist, userdata, boot)')
        self.txt_search.setClearButtonEnabled(True)
        self.txt_search.setFixedHeight(24)
        self.txt_search.setStyleSheet('\n            QLineEdit {\n                background-color: white;\n                border: 1px solid #bdc3c7;\n                border-radius: 3px;\n                padding: 2px 8px;\n                font-size: 11px;\n                color: #2c3e50;\n            }\n            QLineEdit:focus {\n                border-color: #2471a3;\n            }\n        ')
        self.txt_search.textChanged.connect(self._on_search_partition)
        hlay_search.addWidget(self.txt_search, 1)
        search_row.setFixedHeight(28)
        vlay.addWidget(search_row)
        sel_row = QWidget()
        hlay_sr = QHBoxLayout(sel_row)
        hlay_sr.setContentsMargins(0, 0, 0, 0)
        hlay_sr.setSpacing(6)
        btn_sel_all = QPushButton('Selecionar Tudo')
        btn_sel_all.setFixedHeight(22)
        btn_sel_all.setStyleSheet(self._btn_style_sm())
        btn_sel_all.clicked.connect(self._on_sel_all)
        hlay_sr.addWidget(btn_sel_all)
        btn_unsel = QPushButton('Desmarcar Tudo')
        btn_unsel.setFixedHeight(22)
        btn_unsel.setStyleSheet(self._btn_style_sm())
        btn_unsel.clicked.connect(self._on_unsel_all)
        hlay_sr.addWidget(btn_unsel)
        self.lbl_count = QLabel('')
        self.lbl_count.setFont(QFont('Segoe UI', 9))
        self.lbl_count.setStyleSheet('color: #4A90D9; font-weight: bold;')
        hlay_sr.addWidget(self.lbl_count)
        hlay_sr.addStretch()
        sel_row.setFixedHeight(28)
        vlay.addWidget(sel_row)
        ops_row = QWidget()
        hlay_ops = QHBoxLayout(ops_row)
        hlay_ops.setContentsMargins(0, 0, 0, 0)
        hlay_ops.setSpacing(6)
        self.btn_backup = QPushButton('Backup')
        self.btn_backup.setFixedSize(100, 32)
        self.btn_backup.setStyleSheet(self._btn_style('#2471a3'))
        self.btn_backup.setEnabled(False)
        self.btn_backup.clicked.connect(self._on_backup)
        hlay_ops.addWidget(self.btn_backup)
        self.btn_write = QPushButton('Gravar')
        self.btn_write.setFixedSize(100, 32)
        self.btn_write.setStyleSheet(self._btn_style('#f39c12'))
        self.btn_write.setEnabled(False)
        self.btn_write.clicked.connect(self._on_write)
        hlay_ops.addWidget(self.btn_write)
        self.btn_erase = QPushButton('Apagar')
        self.btn_erase.setFixedSize(100, 32)
        self.btn_erase.setStyleSheet(self._btn_style('#e74c3c'))
        self.btn_erase.setEnabled(False)
        self.btn_erase.clicked.connect(self._on_erase)
        hlay_ops.addWidget(self.btn_erase)
        self.btn_load = QPushButton('Carregar')
        self.btn_load.setFixedSize(100, 32)
        self.btn_load.setStyleSheet(self._btn_style('#8e44ad'))
        self.btn_load.setEnabled(False)
        self.btn_load.clicked.connect(self._on_load_map)
        hlay_ops.addWidget(self.btn_load)
        self.btn_reset = QPushButton('Reset')
        self.btn_reset.setFixedSize(80, 32)
        self.btn_reset.setStyleSheet(self._btn_style_sm())
        self.btn_reset.setEnabled(False)
        self.btn_reset.clicked.connect(self._on_reset)
        hlay_ops.addWidget(self.btn_reset)
        self.btn_reboot_recovery = QPushButton('Recovery')
        self.btn_reboot_recovery.setFixedSize(90, 32)
        self.btn_reboot_recovery.setStyleSheet(self._btn_style_sm())
        self.btn_reboot_recovery.setEnabled(False)
        self.btn_reboot_recovery.clicked.connect(self._on_reboot_recovery)
        hlay_ops.addWidget(self.btn_reboot_recovery)
        self.btn_reboot_fastboot = QPushButton('Fastboot')
        self.btn_reboot_fastboot.setFixedSize(90, 32)
        self.btn_reboot_fastboot.setStyleSheet(self._btn_style_sm())
        self.btn_reboot_fastboot.setEnabled(False)
        self.btn_reboot_fastboot.clicked.connect(self._on_reboot_fastboot)
        hlay_ops.addWidget(self.btn_reboot_fastboot)
        self.btn_poweroff = QPushButton('Desligar')
        self.btn_poweroff.setFixedSize(90, 32)
        self.btn_poweroff.setStyleSheet(self._btn_style_sm())
        self.btn_poweroff.setEnabled(False)
        self.btn_poweroff.clicked.connect(self._on_poweroff)
        hlay_ops.addWidget(self.btn_poweroff)
        hlay_ops.addStretch()
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFixedSize(150, 18)
        self.progress.setTextVisible(True)
        self.progress.setFormat('%p%')
        self.progress.setStyleSheet('\n            QProgressBar { border: 1px solid #AAAAAA; border-radius: 3px;\n                           background-color: #E0E0E0; text-align: center; font-size: 10px; }\n            QProgressBar::chunk { background-color: #4A90D9; border-radius: 3px; }\n        ')
        hlay_ops.addWidget(self.progress)
        ops_row.setFixedHeight(40)
        vlay.addWidget(ops_row)
    def _load_devices(self):
        '''Popula a lista de dispositivos a partir do servidor.
        Fluxo: sincroniza metadados sob demanda e popula os combos.
        Se nao ha conectividade nem cache, exibe placeholder discreto.
        '''
        self._sync_models = {}
        self._sync_temp_paths = None
        loaded = self._load_from_mysql()
        if loaded > 0:
            return
        if not PARTITION_OPS_AVAILABLE:
            self.combo_brand.addItem('-- modulo indisponivel --')
            return
        self.combo_brand.blockSignals(True)
        self.combo_brand.clear()
        self.combo_brand.addItem('-- sem conexao com servidor --')
        self.combo_brand.blockSignals(False)
    def _load_from_mysql(self) -> int:
        '''Carrega modelos do servidor via camada de sync. Retorna quantidade.'''
        try:
            from app.views.union_unlock.spd.spd_sync import get_sync
            from app.views.union_unlock.spd.model_data import ModelConfig
        except ImportError:
            try:
                from app.views.union_unlock.spd.spd_sync import get_sync
                from app.views.union_unlock.spd.model_data import ModelConfig
            except ImportError:
                return 0
        try:
            sync = get_sync()
            if sync.pode_sincronizar():
                sync.sincronizar()
            marcas = sync.listar_marcas()
            if not marcas:
                return 0
            self.combo_brand.blockSignals(True)
            self.combo_brand.clear()
            self.combo_brand.addItem('-- Selecione --')
            total = 0
            for marca in sorted(marcas):
                modelos = sync.listar_modelos_por_marca(marca)
                brand_key = marca.upper()
                configs = []
                for m in modelos:
                    ops = sync.get_operacoes(m['srv_id'])
                    op_names = [val.get('label', key) for key, val in ops.items()]
                    config = ModelConfig(brand=brand_key, model=m['modelo'], chipset=m.get('chipset') or '', fdl1_addr=int(m['fdl1_addr'], 16) if m.get('fdl1_addr') else 0, fdl2_addr=int(m['fdl2_addr'], 16) if m.get('fdl2_addr') else 0, exec_addr=int(m['exec_addr'], 16) if m.get('exec_addr') else None, fdl1_file='fdl1-dl.bin', fdl2_file='fdl2-dl.bin', operations=op_names, data_dir='')
                    config._srv_id = m['srv_id']
                    config._ops_json = ops
                    config._memoria = m.get('memoria', 'emmc')
                    configs.append(config)
                    total += 1
                continue
                if not configs:
                    continue
                self._sync_models[brand_key] = configs
                self.combo_brand.addItem(brand_key)
                continue
        except Exception as e:
            logger.warning('PartitionTab: falha ao carregar do servidor: %s', type(e).__name__)
            return 0
        self.combo_brand.blockSignals(False)
        logger.info('PartitionTab: %d modelos carregados do servidor', total)
        return total
    def _on_brand_changed(self, idx):
        self.combo_model.blockSignals(True)
        self.combo_model.clear()
        self.combo_model.addItem('-- Selecione --')
        if idx <= 0:
            self.combo_model.blockSignals(False)
            self._selected_config = None
            self.lbl_model_info.setText('')
            return
        brand = self.combo_brand.currentText()
        if self._sync_models and brand.upper() in self._sync_models:
            configs = self._sync_models[brand.upper()]
            for m in configs:
                display = m.model
                if m.chipset:
                    display += f' ({m.chipset})'
                self.combo_model.addItem(display, m)
        self.combo_model.blockSignals(False)
        self._selected_config = None
        self.lbl_model_info.setText('')
    def _on_model_changed(self, idx):
        if idx <= 0:
            self._selected_config = None
            self.lbl_model_info.setText('')
            return
        config = self.combo_model.itemData(idx)
        if config:
            self._selected_config = config
            srv_id = getattr(config, '_srv_id', None)
            status_text = 'Compativel' if srv_id else 'Dados indisponiveis'
            self.lbl_model_info.setText(status_text)
            self.lbl_status.setText(f'{config.brand} {config.model} selecionado ÔÇö pronto')
            self.lbl_status.setStyleSheet('color: #2471a3;')
    def select_model_by_config(self, config) -> None:
        '''
        Pre-seleciona marca e modelo nos combos a partir de um ModelConfig externo.
        Chamado pela aba principal ao clicar em PARTITIONS.
        '''
        if not config:
            return
        if not self._sync_models:
            return
        brand = getattr(config, 'brand', '').upper()
        model = getattr(config, 'model', '')
        for i in range(self.combo_brand.count()):
            if not self.combo_brand.itemText(i).upper() == brand:
                continue
            self.combo_brand.setCurrentIndex(i)
            break
        else:
            return
        from PyQt5.QtCore import QTimer
        def _select_model():
            for j in range(self.combo_model.count()):
                item_config = self.combo_model.itemData(j)
                if not item_config:
                    continue
                if getattr(item_config, 'model', '') == model:
                    self.combo_model.setCurrentIndex(j)
                    return
        QTimer.singleShot(50, _select_model)
    def _get_active_config(self):
        '''Retorna config do seletor local ou fallback da aba principal.'''
        if self._selected_config:
            return self._selected_config
        if self._get_config_ext:
            return self._get_config_ext()
    def _get_auth_mode(self) -> str:
        """Retorna 'native' ou 'spd_dump'. Por enquanto so spd_dump ativo na UI."""
        if not ENABLE_NATIVE_ENGINE:
            return 'spd_dump'
        return self.combo_auth.currentData() or 'spd_dump'
    def _on_connect(self):
        config = self._get_active_config()
        if not config:
            QMessageBox.warning(self, 'Selecao', 'Selecione uma Marca e Modelo nos combos acima.')
            return
        auth_mode = self._get_auth_mode()
        srv_id = getattr(config, '_srv_id', None)
        if not ENABLE_NATIVE_ENGINE or auth_mode == 'spd_dump' or srv_id:
            if ENABLE_NATIVE_ENGINE and srv_id and auth_mode == 'native':
                QMessageBox.information(self, 'Autenticacao', 'Este modelo requer o protocolo assistido.\nSelecione Auth-1 no seletor de autenticacao.')
                return
            self._on_connect_spd_dump(config)
            return
        if not PARTITION_OPS_AVAILABLE:
            QMessageBox.information(self, 'Indisponivel', 'Modulo partition_ops nao disponivel.')
            return
        model_dir = getattr(config, 'data_dir', None) or ''
        brand = getattr(config, 'brand', '')
        model_name = getattr(config, 'model', '')
        fdl1_file = getattr(config, 'fdl1_file', 'fdl1-sign.bin')
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        data_base = os.path.join(base, 'src', 'Data')
        txt_path = os.path.join(data_base, 'Models', brand.upper(), f'{model_name.upper()}.txt')
        if not model_dir:
            model_dir = os.path.join(data_base, 'Models', brand.upper(), model_name.upper())
        if not os.path.isfile(os.path.join(model_dir, fdl1_file)):
            sub = os.path.join(data_base, 'Models', brand.upper(), model_name.upper())
            if os.path.isfile(os.path.join(sub, fdl1_file)):
                model_dir = sub
                logger.info(f'FDL encontrado em subdir: {sub}')
        if not os.path.exists(txt_path):
            logger.error(f'Modelo nao encontrado: {txt_path}')
            QMessageBox.warning(self, 'Erro', 'Dados do modelo nao encontrados.\nVerifique a instalacao ou sincronize novamente.')
            return
        self._set_busy(True, 'Conectando...')
        self.btn_connect.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        if self._part_mgr:
            try:
                self._part_mgr.disconnect()
            except Exception:
                pass
        def do_connect():
            try:
                self._part_mgr = SPDPartitionManager.from_model_config(model_txt_path=txt_path, model_dir=model_dir, log_cb=self._emit_log, progress_cb=(lambda v: None))
                ok = self._part_mgr.connect(wait_timeout=60)
                if ok:
                    self._sig_connected.emit()
                    return
                self._sig_connect_fail.emit('Timeout ou erro ao conectar')
                return
            except Exception as e:
                self._sig_connect_fail.emit(str(e))
        self._connect_thread = threading.Thread(target=do_connect, daemon=True)
        self._connect_thread.start()
    def _on_connect_spd_dump(self, config):
        '''Conecta usando o componente externo de comunicacao.
        Recupera dados sob demanda do cache local (sincronizado com servidor)
        ou usa arquivos previamente disponibilizados no data_dir do modelo.
        '''
        import os as _os
        from app.views.union_unlock.spd.bin_spd import SPDDumpProcess
        from app.views.union_unlock.spd.config import SPD_DUMP_PATH
        brand = getattr(config, 'brand', '')
        model_name = getattr(config, 'model', '')
        fdl1_addr = getattr(config, 'fdl1_addr', 0)
        fdl2_addr = getattr(config, 'fdl2_addr', 0)
        exec_addr = getattr(config, 'exec_addr', None)
        if not self.chk_advanced.isChecked():
            exec_addr = None
        if not fdl1_addr or not fdl2_addr:
            QMessageBox.warning(self, 'Configuracao', f'Configuracao incompleta para {brand} {model_name}.\nVerifique o modelo no painel administrativo.')
            return
        spd_exe = SPD_DUMP_PATH
        if not spd_exe or not _os.path.isfile(spd_exe):
            QMessageBox.warning(self, 'Conexao', 'Componente de comunicacao nao encontrado.\n\nVerifique a instalacao do aplicativo.')
            return
        srv_id = getattr(config, '_srv_id', None)
        model_dir = getattr(config, 'data_dir', None) or ''
        self._sync_temp_paths = None
        if srv_id and (not model_dir or not _os.path.isdir(model_dir)):
            try:
                try:
                    from app.views.union_unlock.spd.spd_sync import get_sync
                except ImportError:
                    from app.views.union_unlock.spd.spd_sync import get_sync
            except Exception as e:
                logger.error(f'Erro ao preparar dados: {e}')
                QMessageBox.warning(self, 'Erro', 'Erro ao preparar dados do modelo.\nVerifique a conexao e tente novamente.')
            sync = get_sync()
            paths = sync.extrair_fdls_temp(srv_id)
            if not paths:
                QMessageBox.warning(self, 'Dados', f'Falha ao preparar dados para {model_name}.\nVerifique a conexao com o servidor.')
                return
            try:
                self._sync_temp_paths = paths
                fdl1_path = paths['fdl1']
                fdl2_path = paths['fdl2']
                model_dir = paths['dir']
            except Exception as e:
                logger.error(f'Erro ao preparar dados: {e}')
                QMessageBox.warning(self, 'Erro', 'Erro ao preparar dados do modelo.\nVerifique a conexao e tente novamente.')
        else:
            if not model_dir:
                data_base = _os.path.join(base, 'src', 'Data')
                model_dir = _os.path.join(data_base, 'Models', brand.upper(), model_name.upper())
            fdl1_path, fdl2_path = self._resolve_fdl_files(config, model_dir)
            if not fdl1_path or not fdl2_path:
                return
        self._sig_pause_port_scan.emit(True)
        self._set_busy(True, 'Conectando ao dispositivo...')
        self._show_connect_dialog(f'{brand} {model_name}'.strip())
        self.btn_connect.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        def on_ready():
            self._sig_spd_list_partitions.emit()
        def on_partitions(parts):
            try:
                from app.views.union_unlock.spd.partition import PartitionInfo
            except ImportError:
                from app.views.union_unlock.spd.partition import PartitionInfo
            pi_list = [PartitionInfo(name=p.name, size_bytes=p.size_bytes) for p in parts]
            self._sig_partitions_ready.emit(pi_list)
        temp_paths_ref = self._sync_temp_paths
        def on_exit(code):
            self._sig_pause_port_scan.emit(False)
            if temp_paths_ref:
                try:
                    try:
                        from app.views.union_unlock.spd.spd_sync import SpdSync
                    except ImportError:
                        from app.views.union_unlock.spd.spd_sync import SpdSync
                except Exception:
                    pass
                SpdSync.limpar_fdls_temp(temp_paths_ref)
            if not proc.partitions:
                error_msg = getattr(proc, 'fatal_error', '') or 'Nao foi possivel conectar. Possivel erro nas conexoes fisicas ou versao de seguranca incompativel. Verifique cabo, Test Point e tente novamente.'
                self._sig_connect_fail.emit(error_msg)
        force_kick = False
        try:
            force_kick = bool(self.chk_force.isChecked())
        except Exception:
            pass
        if force_kick:
            logger.info('[partition_tab] Force ativado ÔÇö spd_dump com --kick')
        proc = SPDDumpProcess(spd_dump_path=spd_exe, fdl1_path=fdl1_path, fdl2_path=fdl2_path, fdl1_addr=fdl1_addr, fdl2_addr=fdl2_addr, exec_addr=exec_addr or 0, cwd=model_dir, log_cb=self._emit_log, use_kick=force_kick)
        proc.on_ready = on_ready
        proc.on_partitions = on_partitions
        proc.on_exit = on_exit
        proc.on_connect_progress = lambda pct, phase: self._sig_connect_progress.emit(pct, phase)
        proc.on_op_progress = lambda pct, speed_mb: self._sig_op_progress.emit(pct, speed_mb)
        self._spd_proc = proc
        self.progress.setValue(0)
        if not proc.start(wait_seconds=300):
            self._sig_pause_port_scan.emit(False)
            self._on_connect_fail('Falha ao iniciar conexao. Verifique os drivers e o dispositivo.')
            return
        self._watchdog = QTimer(self)
        self._watchdog.setInterval(2000)
        self._watchdog.timeout.connect(self._check_spd_process)
        self._watchdog.start()
    def _check_spd_process(self):
        '''Watchdog ÔÇö verifica se o processo morreu ou reportou erro fatal.'''
        wd = getattr(self, '_watchdog', None)
        proc = getattr(self, '_spd_proc', None)
        if not proc:
            if wd:
                wd.stop()
            return
        if proc.partitions:
            if wd:
                wd.stop()
            return
        should_fail = False
        if not proc.is_running:
            should_fail = True
        if proc.has_fatal_error and not proc.partitions:
            should_fail = True
        if should_fail:
            if self._is_busy:
                if wd:
                    wd.stop()
                error_msg = proc.fatal_error or 'Nao foi possivel conectar. Possivel erro nas conexoes fisicas ou versao de seguranca incompativel. Verifique cabo, Test Point e tente novamente.'
                if proc.is_running:
                    proc.stop()
                self._on_connect_fail(error_msg)
                self._sig_pause_port_scan.emit(False)
    def _resolve_fdl_files(self, config, model_dir: str):
        '''
        Resolve caminhos dos FDLs, preferindo -dl sobre -sign.
        Ref: unlock_autopatch_9230.bat ÔÇö usa fdl1-dl.bin e fdl2-dl.bin
        Esses sao os FDLs de download que suportam comandos de particao.
        '''
        import os as _os
        fdl1_file = getattr(config, 'fdl1_file', 'fdl1-sign.bin')
        fdl2_file = getattr(config, 'fdl2_file', 'fdl2-sign.bin')
        fdl1_dl = _os.path.join(model_dir, 'fdl1-dl.bin')
        fdl2_dl = _os.path.join(model_dir, 'fdl2-dl.bin')
        if _os.path.isfile(fdl1_dl):
            fdl1_path = fdl1_dl
        else:
            fdl1_path = _os.path.join(model_dir, fdl1_file)
        if _os.path.isfile(fdl2_dl):
            fdl2_path = fdl2_dl
        else:
            fdl2_path = _os.path.join(model_dir, fdl2_file)
        if not _os.path.isfile(fdl1_path):
            logger.error(f'Arquivo nao encontrado: {fdl1_path}')
            QMessageBox.warning(self, 'Dados', 'Arquivo de comunicacao primario nao encontrado.\nVerifique a instalacao do modelo.')
            return (None, None)
        if not _os.path.isfile(fdl2_path):
            logger.error(f'Arquivo nao encontrado: {fdl2_path}')
            QMessageBox.warning(self, 'Dados', 'Arquivo de comunicacao secundario nao encontrado.\nVerifique a instalacao do modelo.')
            return (None, None)
        return fdl1_path, fdl2_path
    def _do_spd_list(self):
        """Slot (main thread) ÔÇö envia 'p' ao spd_dump apos FDL2 ativo."""
        proc = getattr(self, '_spd_proc', None)
        if proc:
            if proc.is_running:
                QTimer.singleShot(500, proc.list_partitions)
    def _on_spd_dump_done(self, parts):
        '''Slot (main thread) ÔÇö popula tabela com particoes do spd_dump.'''
        wd = getattr(self, '_watchdog', None)
        if wd:
            wd.stop()
        self._close_connect_dialog()
        self._spd_parts = parts
        self._set_busy(False)
        try:
            self.progress.setValue(100)
        except Exception:
            pass
        stage_suffix = ''
        try:
            proc = getattr(self, '_spd_proc', None)
            if proc is not None:
                stage = getattr(proc, 'bsl_stage', '') or ''
                if stage:
                    stage_suffix = f' ┬À {stage}'
        except Exception:
            pass
        self.lbl_status.setText(f'Conectado{stage_suffix} ÔÇö {len(parts)} particoes')
        self.lbl_status.setStyleSheet('color: #27ae60; font-weight: bold;')
        self.btn_connect.setText('Reconectar')
        self.btn_connect.setEnabled(True)
        self.btn_list.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.btn_reset.setEnabled(True)
        self._set_extra_actions_enabled(True)
        self._fill_table(parts)
    def _send_spd_cmd(self, command: str):
        '''Envia comando ao processo spd_dump interativo.'''
        proc = getattr(self, '_spd_proc', None)
        if not proc or not proc.is_running:
            self._emit_log('Processo de comunicacao nao esta ativo', 'ERROR')
            return False
        return proc.send_command(command)
    def _kill_spd_process(self):
        '''Encerra o processo spd_dump interativo.'''
        proc = getattr(self, '_spd_proc', None)
        if proc:
            proc.stop()
        self._spd_proc = None
        self._sig_pause_port_scan.emit(False)
    def _on_cancel(self):
        '''Cancela operacao em andamento (conexao ou particionamento).'''
        wd = getattr(self, '_watchdog', None)
        if wd:
            wd.stop()
        self._close_connect_dialog()
        self._kill_spd_process()
        if self._part_mgr:
            self._part_mgr.cancel()
            try:
                self._part_mgr.disconnect()
            except Exception:
                pass
        self._set_busy(False)
        self.lbl_status.setText('Operacao cancelada')
        self.lbl_status.setStyleSheet('color: #e74c3c;')
        self.btn_connect.setEnabled(True)
        self.btn_connect.setText('Conectar SPD')
        self.btn_cancel.setEnabled(False)
        self.btn_list.setEnabled(False)
        self.btn_reset.setEnabled(False)
        self._set_extra_actions_enabled(False)
        self._set_op_btns(False)
        self.progress.setValue(0)
    def _on_connected(self):
        self._set_busy(False)
        self.lbl_status.setText('Conectado ÔÇö dispositivo pronto')
        self.lbl_status.setStyleSheet('color: #27ae60; font-weight: bold;')
        self.btn_connect.setText('Reconectar')
        self.btn_connect.setEnabled(True)
        self.btn_list.setEnabled(True)
        self.btn_reset.setEnabled(True)
        self._set_extra_actions_enabled(True)
        self.btn_cancel.setEnabled(False)
    def _on_connect_progress_ui(self, pct: int, phase: str):
        '''Slot (main thread) ÔÇö atualiza QProgressBar durante conexao.
        Chamado via signal a partir do callback on_connect_progress do
        SPDDumpProcess. Mostra fase legivel (traduzida do marker do
        spd_dump) para o tecnico acompanhar o boot em tempo real.
        '''
        try:
            self.progress.setValue(pct)
        except Exception:
            pass
        phase_pt = {'CHECK_BAUD bootrom': 'BROM detectado', 'SEND': 'Enviando FDL1...', 'EXEC FDL1': 'Executando FDL1...', 'CHECK_BAUD FDL1': 'FDL1 respondendo', 'CHANGE_BAUD FDL1': 'Ajustando velocidade', 'SEND ': 'Enviando FDL2...', 'EXEC FDL2': 'Executando FDL2...', 'DISABLE_TRANSCODE': 'HDLC negociado', 'Reading Partition List': 'Lendo tabela de particoes...'}.get(phase, phase)
        try:
            self.lbl_status.setText(f'{phase_pt} ({pct}%)')
            self.lbl_status.setStyleSheet('color: #2471a3; font-weight: bold;')
        except Exception:
            pass
        dlg = getattr(self, '_connect_dlg', None)
        if dlg is not None:
            try:
                dlg.setValue(pct)
                dlg.setLabelText(f'{phase_pt} ({pct}%)')
                return
            except Exception:
                pass
    def _on_op_progress_ui(self, pct: int, speed_mb: float):
        '''Slot (main thread) ÔÇö atualiza QProgressBar durante r/w/erase.
        Chamado via signal a partir do on_op_progress do SPDDumpProcess.
        Mostra velocidade em MB/s no rotulo para o tecnico ter feedback
        real de I/O (evita duvida "esta rodando ou travou?").
        '''
        try:
            self.progress.setValue(pct)
        except Exception:
            pass
        try:
            batch_lbl = getattr(self, '_batch_current_label', '')
            if batch_lbl:
                self.lbl_status.setText(f'{batch_lbl} ÔÇö {pct}% ┬À {speed_mb:.1f} MB/s')
                return
            base = self.lbl_status.text().split(' ÔÇö ')[0]
            self.lbl_status.setText(f'{base} ÔÇö {pct}% ┬À {speed_mb:.1f} MB/s')
        except Exception:
            return
    def _show_connect_dialog(self, model_name: str=''):
        '''Cria e exibe o QProgressDialog da conexao.
Comportamento de seguranca:
- Sempre fecha um dialog anterior antes de criar novo (evita
  leak em reconexao).
- Qualquer excecao na criacao e engolida silenciosamente: nesse
  caso `self._connect_dlg` permanece None e a UI segue apenas
  com a QProgressBar embutida (nunca trava, nunca vaza estado).
- `dlg.canceled` conecta a `_on_cancel` (helper ja existente),
  reaproveitando 100% do fluxo de cancelamento (kill do proc,
  stop do watchdog, reset da UI).
'''
        self._close_connect_dialog()
        try:
            label = f'Conectando a {model_name}...' if model_name else 'Conectando ao dispositivo...'
            dlg = QProgressDialog(label, 'Cancelar', 0, 100, self)
            dlg.setWindowTitle('Conexao SPD')
            dlg.setMinimumWidth(380)
            dlg.setWindowModality(Qt.WindowModal)
            dlg.setAutoClose(False)
            dlg.setAutoReset(False)
            dlg.setMinimumDuration(0)
            dlg.setValue(0)
            try:
                dlg.canceled.connect(self._on_cancel)
            except Exception:
                pass
            else:
                self._connect_dlg = dlg
        except Exception as e:
            logger.debug(f'[partition_tab] _show_connect_dialog: {e}')
            self._connect_dlg = None
        try:
            try:
                dlg.show()
            except Exception:
                return
        except Exception as e:
            logger.debug(f'[partition_tab] _show_connect_dialog: {e}')
            self._connect_dlg = None
    def _close_connect_dialog(self):
        '''Fecha o dialog de conexao se existir; idempotente.
CRITICO ÔÇö desconectar o signal `canceled` ANTES de `close()`:
no Qt5, `QProgressDialog.close()` chama `closeEvent` -> `reject`
-> `cancel()` -> emite `canceled`. Como `dlg.canceled` esta
conectado a `_on_cancel` (que mata o subprocesso spd_dump e
zera `self._spd_proc`), fechar o dialog programaticamente ao
final de uma conexao BEM-SUCEDIDA disparava o cancelamento
indevido ÔÇö a UI mostrava "Conectado ÔÇö N particoes" mas o
proc ja tinha sido morto, e o proximo Backup/Reset caia em
"Nenhum backend conectado" (bug reproduzido em 25/08/2026).
Ref: comportamento nativo de QDialog::closeEvent + override
de QProgressDialog::reject documentado no Qt.
Comportamento de seguranca:
- Desconexao envolvida em try/except: se o signal ja estava
  desconectado por outro motivo, ignora silenciosamente.
- `close()` envolvido em try/except: se widget ja destruido,
  engole a excecao.
- Sempre reseta `self._connect_dlg = None` ao final para nao
  vazar referencia obsoleta.
'''
        dlg = getattr(self, '_connect_dlg', None)
        if dlg is None:
            return
        try:
            dlg.canceled.disconnect(self._on_cancel)
        except Exception:
            pass
        try:
            dlg.close()
        except Exception:
            pass
        self._connect_dlg = None
    def _on_connect_fail(self, msg: str):
        self._close_connect_dialog()
        self._set_busy(False)
        display = msg if len(msg) <= 90 else msg[:87] + '...'
        self.lbl_status.setText(display)
        self.lbl_status.setStyleSheet('color: #e74c3c; font-weight: bold; font-size: 9pt;')
        self.btn_connect.setEnabled(True)
        self.btn_connect.setText('Conectar SPD')
        self.btn_cancel.setEnabled(False)
    def _on_list(self):
        if not self._part_mgr:
            return
        self._set_busy(True, 'Listando particoes...')
        self.btn_list.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        def do_list():
            parts = self._part_mgr.list_partitions()
            self._sig_fill_table.emit(parts)
        threading.Thread(target=do_list, daemon=True).start()
    def _fill_table(self, parts):
        safety_colors = {'safe': '#27ae60', 'caution': '#f39c12', 'critical': '#e74c3c', 'unknown': '#7f8c8d'}
        safety_labels = {'safe': 'Seguro', 'caution': 'Cuidado', 'critical': 'CRITICO', 'unknown': '--'}
        self.table.setRowCount(len(parts))
        self.table.blockSignals(True)
        try:
            for row, p in enumerate(parts):
                cb = QTableWidgetItem()
                cb.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                cb.setCheckState(Qt.Unchecked)
                self.table.setItem(row, 0, cb)
                ni = QTableWidgetItem(p.name)
                ni.setFont(QFont('Consolas', 10))
                if p.safety == 'critical':
                    ni.setForeground(QColor('#e74c3c'))
                self.table.setItem(row, 1, ni)
                si = QTableWidgetItem(p.size_str)
                si.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(row, 2, si)
                ti = QTableWidgetItem(p.type)
                ti.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 3, ti)
                sti = QTableWidgetItem(safety_labels.get(p.safety, '--'))
                sti.setTextAlignment(Qt.AlignCenter)
                sti.setForeground(QColor(safety_colors.get(p.safety, '#7f8c8d')))
                sti.setFont(QFont('Segoe UI', 9, QFont.Bold))
                self.table.setItem(row, 4, sti)
                try:
                    from app.views.union_unlock.spd.partition_file_select import create_file_cell
                    self.table.setItem(row, 5, create_file_cell())
                except Exception:
                    pass
                continue
        finally:
            self.table.blockSignals(False)
        has = len(parts) > 0
        self._set_op_btns(has)
        self.btn_list.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self._set_busy(False)
        self.lbl_status.setText(f'{len(parts)} particoes carregadas')
        self.lbl_status.setStyleSheet('color: #27ae60; font-weight: bold;')
        self._update_count()
    def _on_search_partition(self, text: str):
        '''Filtra linhas visiveis da tabela pelo nome da particao.'''
        q = (text or '').strip().lower()
        visible_count = 0
        for i in range(self.table.rowCount()):
            item_nome = self.table.item(i, 1)
            nome = (item_nome.text() if item_nome else '').lower()
            match = not q or q in nome
            self.table.setRowHidden(i, not match)
            if match:
                visible_count += 1
        try:
            rows = self.table.rowCount()
            if q:
                self.lbl_count.setText(f'{visible_count} de {rows} filtrada(s)')
                return
            self._update_count()
            return
        except Exception:
            return
    def _on_sel_all(self):
        for i in range(self.table.rowCount()):
            cb = self.table.item(i, 0)
            if cb:
                cb.setCheckState(Qt.Checked)
        self._update_count()
    def _on_unsel_all(self):
        for i in range(self.table.rowCount()):
            cb = self.table.item(i, 0)
            if cb:
                cb.setCheckState(Qt.Unchecked)
        self._update_count()
    def _on_table_item_changed(self, item):
        '''Handler global de mudanca em items da tabela.
        Objetivo cirurgico: manter o contador "X de N selecionada(s)"
        sincronizado com o checkbox individual (coluna 0). Ignora
        mudancas em outras colunas para nao gastar CPU a toa.
        Robusto contra `item is None` e contra excecoes vindas do
        `_update_count` (nunca deve derrubar a UI por causa de um
        contador visual).
        '''
        try:
            if item is None or item.column() != 0:
                return
            self._update_count()
            return
        except Exception:
            return
    def _update_count(self):
        total = sum((1 for i in range(self.table.rowCount()) if self.table.item(i, 0) or self.table.item(i, 0).checkState() == Qt.Checked))
        rows = self.table.rowCount()
        if rows > 0:
            self.lbl_count.setText(f'{total} de {rows} selecionada(s)')
            return
        None('')
    def _get_selected(self):
        '''Retorna a PRIMEIRA particao selecionada (compat).
        Para operacoes batch (multi-check), use `_get_all_selected()`.
        Se nada marcado, cai no cursor da tabela (row selecionada).
        '''
        selected = self._get_all_selected()
        if selected:
            return selected[0]
        parts = self._get_parts_ref()
        if not parts:
            return
        r = self.table.currentRow()
        if 0 <= r:
            if r < len(parts):
                return parts[r]
    def _get_parts_ref(self):
        '''Retorna a lista atual de particoes (spd_dump OU partition_mgr).'''
        if self._part_mgr:
            return self._part_mgr.partitions
        return getattr(self, '_spd_parts', None) or []
    def _get_all_selected(self) -> list:
        '''Retorna TODAS as particoes com checkbox marcado.
        Fonte de verdade: apenas checkboxes da coluna 0. Filtra por
        indices validos contra a lista de particoes (defensivo contra
        race entre repopulacao e query). Preserva a ordem da tabela
        para a operacao batch executar top-to-bottom (previsivel).
        '''
        parts = self._get_parts_ref()
        if not parts:
            return []
        out = []
        for i in range(self.table.rowCount()):
            cb = self.table.item(i, 0)
            if not cb:
                continue
            if cb.checkState() != Qt.Checked:
                continue
            if i < len(parts):
                out.append(parts[i])
        return out
    def _get_part_size(self, name: str) -> int:
        '''Retorna tamanho em bytes da particao pelo nome.'''
        parts = getattr(self, '_spd_parts', None) or []
        for p in parts:
            if p.name != name:
                continue
            return p.size_bytes or 0
        return 0
    def _on_file_double_click(self, row, column):
        try:
            from app.views.union_unlock.spd.partition_file_select import on_cell_double_click
            on_cell_double_click(self.table, row, column, self._get_default_docs_dir, parent=self)
            return
        except Exception as e:
            logger.error('Erro ao selecionar arquivo: %s', e)
    def _on_load_map(self):
        try:
            from app.views.union_unlock.spd.partition_file_select import load_backup_map
            loaded = load_backup_map(self.table, self._get_default_docs_dir, parent=self)
            if loaded:
                if loaded > 0:
                    self._update_count()
                    return
                return
        except Exception as e:
            logger.error('Erro ao carregar mapa: %s', e)
            QMessageBox.critical(self, 'Erro', 'Nao foi possivel carregar o mapa. Tente novamente.')
    def _on_backup(self):
        '''Backup de uma OU MULTIPLAS particoes selecionadas.
Fluxo:
  - 0 marcadas -> usa a linha do cursor (compat com uso rapido).
  - 1 marcada  -> QFileDialog para escolher nome/caminho.
  - N marcadas -> QFileDialog para escolher PASTA destino;
                  cada particao vira <pasta>/backup_<nome>.bin.
Execucao sequencial (fila) ÔÇö uma por vez. Justificativa:
`spd_dump.exe` interativo aceita um READ_START por vez; enfileirar
respeita o fluxo natural do binario e evita corromper o pipe
stdin/stdout. Similar ao que ferramentas EDL/Qualcomm fazem.
'''
        selected = self._get_all_selected()
        if not selected:
            single = self._get_selected()
            if not single:
                QMessageBox.information(self, 'Selecao', 'Selecione uma ou mais particoes.')
                return
            selected = [single]
        base_dir = self._get_default_docs_dir()
        if len(selected) == 1:
            p = selected[0]
            display = self._get_display_label(p.name)
            default_name = f'backup_{display.replace(' ', '_').lower()}.bin'
            save_path, _ = QFileDialog.getSaveFileName(self, f'Salvar Backup ÔÇö {display}', os.path.join(base_dir, default_name), 'Binarios (*.bin *.img);;Todos (*.*)')
            if not save_path:
                return
            try:
                self.__class__._last_save_dir = os.path.dirname(save_path)
            except Exception:
                pass
            self._run_op('read', p.name, save_path)
            return
        dest_dir = QFileDialog.getExistingDirectory(self, f'Pasta destino ÔÇö Backup de {len(selected)} particoes', base_dir)
        if not dest_dir:
            return
        try:
            self.__class__._last_save_dir = dest_dir
        except Exception:
            pass
        queue = []
        for p in selected:
            fname = f'backup_{p.name.replace(' ', '_').lower()}.bin'
            queue.append(('read', p.name, os.path.join(dest_dir, fname)))
        self._run_batch(queue)
    @classmethod
    def _get_default_docs_dir(cls) -> str:
        '''Resolve pasta padrao de salvamento.
Ordem: (1) ultima pasta usada nesta sessao,
       (2) Documentos do usuario resolvido via QStandardPaths
           (funciona em qualquer localidade ÔÇö pt-BR, en-US, etc.),
       (3) fallback %USERPROFILE%/Documents (retrocompat Windows).
'''
        last = getattr(cls, '_last_save_dir', None)
        if last and os.path.isdir(last):
            return last
        try:
            docs = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
            if docs and os.path.isdir(docs):
                return docs
        except Exception:
            pass
        fallback = os.path.join(os.path.expanduser('~'), 'Documents')
        return fallback
    def _on_write(self):
        assignments = []
        try:
            from app.views.union_unlock.spd.partition_file_select import get_file_assignments
            assignments = get_file_assignments(self.table)
        except Exception:
            pass
        if assignments:
            parts_ref = self._get_parts_ref()
            safety_map = {}
            if parts_ref:
                safety_map = {p.name: p.safety for p in parts_ref}
            criticas = [n for n, _ in assignments if safety_map.get(n) == 'critical']
            lines = []
            for name, fp in assignments:
                display = self._get_display_label(name)
                fname = os.path.basename(fp)
                tag = '  ** CRITICA **' if name in criticas else ''
                lines.append(f'  {display}  <-  {fname}{tag}')
            if len(lines) > 15:
                visible = lines[:15]
                msg = f'Gravar {len(assignments)} particao(oes)?\n\n' + '\n'.join(visible) + f'\n  ... e mais {len(lines) - 15} particao(oes)'
            else:
                msg = f'Gravar {len(assignments)} particao(oes)?\n\n' + '\n'.join(lines)
            if criticas:
                msg += '\n\nATENCAO: Particoes criticas incluidas. Gravar incorretamente pode causar danos ao dispositivo.'
            msg += '\n\nEsta operacao e IRREVERSIVEL!'
            confirm = QMessageBox.question(self, 'Confirmar Gravacao em Lote', msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if confirm != QMessageBox.Yes:
                return
            logger.info('Write batch: %s', ', '.join((f'{n}={os.path.basename(f)}' for n, f in assignments)))
            queue = [('write', n, f) for n, f in assignments]
            self._run_batch(queue)
            return
        p = self._get_selected()
        if not p:
            QMessageBox.information(self, 'Selecao', 'Selecione uma particao ou use clique duplo na coluna Arquivo para escolher os arquivos a gravar.')
            return
        display = self._get_display_label(p.name)
        if p.safety == 'critical':
            QMessageBox.critical(self, 'BLOQUEADO', f'{display} e uma area CRITICA.\nGravar nela pode causar BRICK.\nOperacao bloqueada por seguranca.')
            return
        fp, _ = QFileDialog.getOpenFileName(self, f'Selecionar Imagem ÔÇö {display}', self._get_default_docs_dir(), 'Binarios (*.bin *.img);;Todos (*.*)')
        if not fp:
            return
        try:
            self.__class__._last_save_dir = os.path.dirname(fp)
        except Exception:
            pass
        confirm = QMessageBox.question(self, 'Confirmar Gravacao', f"Gravar '{os.path.basename(fp)}' em {display}?\nEsta operacao e irreversivel!", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if confirm != QMessageBox.Yes:
            return
        self._run_op('write', p.name, fp)
    def _on_erase(self):
        '''Erase de uma OU MULTIPLAS particoes selecionadas.
        Seguranca reforcada no batch: se QUALQUER particao for critica,
        bloqueia a operacao inteira com lista das partes envolvidas.
        '''
        selected = self._get_all_selected()
        if not selected:
            single = self._get_selected()
            if not single:
                QMessageBox.information(self, 'Selecao', 'Selecione uma ou mais particoes.')
                return
            selected = [single]
        criticas = [p.name for p in selected if p.safety == 'critical']
        if criticas:
            QMessageBox.critical(self, 'BLOQUEADO', 'As seguintes particoes sao CRITICAS e nao podem ser apagadas:\n\n  - ' + '\n  - '.join(criticas) + '\n\nDesmarque essas particoes e tente novamente.')
            return
        if len(selected) == 1:
            display = self._get_display_label(selected[0].name)
            confirm = QMessageBox.question(self, 'Confirmar Limpeza', f'Apagar {display}?\nEsta operacao e irreversivel!', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if confirm != QMessageBox.Yes:
                return
            self._run_op('erase', selected[0].name)
            return
        nomes = '\n  - '.join((p.name for p in selected))
        confirm = QMessageBox.question(self, 'Confirmar Limpeza em Lote', f'Apagar {len(selected)} particoes?\n\n  - {nomes}\n\nEsta operacao e IRREVERSIVEL para cada uma.', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if confirm != QMessageBox.Yes:
            return
        queue = [('erase', p.name, '') for p in selected]
        self._run_batch(queue)
    def _on_reset(self):
        confirm = QMessageBox.question(self, 'Reiniciar', 'Reiniciar o dispositivo?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if confirm != QMessageBox.Yes:
            return
        proc = getattr(self, '_spd_proc', None)
        if proc and proc.is_running:
            self.lbl_status.setText('Reiniciando dispositivo...')
            self.lbl_status.setStyleSheet('color: #7f8c8d;')
            self._set_op_btns(False)
            self.btn_cancel.setEnabled(False)
            self.btn_reset.setEnabled(False)
            self._set_extra_actions_enabled(False)
            def do_spd_reset():
                try:
                    proc.reset_device()
                    import time as _time
                    _time.sleep(2.0)
                except Exception as e:
                    logger.debug(f'[partition_tab] reset_device: {e}')
                try:
                    self._kill_spd_process()
                except Exception:
                    pass
                self._sig_device_reset.emit()
            threading.Thread(target=do_spd_reset, daemon=True).start()
            return
        if not self._part_mgr:
            return
        def do_reset():
            self._part_mgr.reset()
            self._sig_device_reset.emit()
        threading.Thread(target=do_reset, daemon=True).start()
    def _on_device_reset(self):
        '''Slot (main thread) ÔÇö UI apos reset do dispositivo.'''
        self.lbl_status.setText('Dispositivo reiniciado')
        self.lbl_status.setStyleSheet('color: #7f8c8d;')
        self._set_op_btns(False)
        self.btn_cancel.setEnabled(False)
    def _run_exit_download_action(self, dialog_title: str, dialog_msg: str, spd_command_fn, busy_msg: str, done_msg: str):
        '''Executa uma acao que faz o device sair do Modo SPD.
Args:
    dialog_title/dialog_msg: texto da confirmacao QMessageBox.
    spd_command_fn: callable que envia o comando ao spd_dump
        (ex.: proc.poweroff_device).
    busy_msg: texto do label durante a acao.
    done_msg: texto do label apos concluir (emitido via signal).
Comportamento de seguranca:
- Se proc estiver ausente/parado, apenas informa via label
  (nao lanca excecao, nao trava UI).
- Qualquer excecao no envio do comando e logada em debug
  e ainda assim tenta encerrar o processo (finally).
- Sinal de conclusao usa _sig_device_post_action isolado ÔÇö
  nao interfere no fluxo do Reset existente.
'''
        confirm = QMessageBox.question(self, dialog_title, dialog_msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if confirm != QMessageBox.Yes:
            return
        proc = getattr(self, '_spd_proc', None)
        if not proc or not proc.is_running:
            self.lbl_status.setText('Dispositivo nao esta conectado')
            self.lbl_status.setStyleSheet('color: #e67e22;')
            return
        self.lbl_status.setText(busy_msg)
        self.lbl_status.setStyleSheet('color: #7f8c8d;')
        self._set_op_btns(False)
        self.btn_cancel.setEnabled(False)
        self.btn_reset.setEnabled(False)
        self._set_extra_actions_enabled(False)
        def _worker():
            try:
                spd_command_fn()
                import time as _time
                _time.sleep(2.0)
            except Exception as e:
                logger.debug(f'[partition_tab] exit-download action: {e}')
            try:
                self._kill_spd_process()
            except Exception:
                pass
            self._sig_device_post_action.emit(done_msg)
        threading.Thread(target=_worker, daemon=True).start()
    def _on_reboot_recovery(self):
        proc = getattr(self, '_spd_proc', None)
        if not proc:
            return
        self._run_exit_download_action('Reiniciar em Recovery', 'Reiniciar o dispositivo no modo Recovery?', proc.reboot_recovery, 'Reiniciando em Recovery...', 'Dispositivo reiniciado em Recovery')
    def _on_reboot_fastboot(self):
        proc = getattr(self, '_spd_proc', None)
        if not proc:
            return
        self._run_exit_download_action('Reiniciar em Fastboot', 'Reiniciar o dispositivo no modo Fastboot?', proc.reboot_fastboot, 'Reiniciando em Fastboot...', 'Dispositivo reiniciado em Fastboot')
    def _on_poweroff(self):
        proc = getattr(self, '_spd_proc', None)
        if not proc:
            return
        self._run_exit_download_action('Desligar dispositivo', 'Desligar o dispositivo?\n\nObs.: o desligamento efetivo ocorre ao desconectar o cabo.', proc.poweroff_device, 'Desligando dispositivo...', 'Dispositivo desligado (desconecte o cabo)')
    def _on_device_post_action(self, msg: str):
        '''Slot (main thread) ÔÇö UI apos acao de saida do Modo SPD.
        Reproduz o cleanup do _on_device_reset mas com a mensagem
        parametrizada. Nao substitui _on_device_reset ÔÇö coexiste.
        '''
        self.lbl_status.setText(msg)
        self.lbl_status.setStyleSheet('color: #7f8c8d;')
        self._set_op_btns(False)
        self.btn_cancel.setEnabled(False)
    def _get_display_label(self, name: str) -> str:
        """Retorna o nome REAL da particao (ex: 'miscdata', 'boot_a').
Motivos:
- Backups precisam do nome real para o tecnico saber o que restaurar
  depois (ex: 'backup_miscdata.bin' vs 'backup_area3.bin').
- `spd_dump.exe` loga sempre o nome real; se a UI mostrar 'Area N'
  o tecnico nao consegue correlacionar com o log e nao entende qual
  particao esta sendo lida/gravada/apagada.
- A rotulacao generica 'Area N' era usada em versoes antigas para
  reduzir a chance de o tecnico apagar/gravar a particao errada,
  mas ja temos:
     1. Confirmacao de CRITICA em write/erase (_CRITICAL_PARTS).
     2. Combo com nome real + tamanho na tabela.
     3. Validacao dupla no read (_run_read_op) antes de salvar.
Fallback: se por algum motivo o nome vier vazio (nao deveria), volta
para 'Particao selecionada' ÔÇö nunca expoe indice interno.
"""
        real = (name or '').strip()
        if not real:
            return 'Particao selecionada'
        return real
    def _run_op(self, op: str, name: str, file_path: str=''):
        self._set_op_btns(False)
        self.btn_cancel.setEnabled(True)
        self.progress.setValue(0)
        display = self._get_display_label(name)
        op_labels = {'read': 'Lendo', 'write': 'Gravando', 'erase': 'Apagando'}
        self._set_busy(True, f'{op_labels.get(op, op.capitalize())} {display}...')
        proc = getattr(self, '_spd_proc', None)
        use_spd = proc and proc.is_running and not self._part_mgr
        def do_op():
            if use_spd:
                ok, msg = self._run_op_spd(op, name, file_path)
            elif self._part_mgr:
                if op == 'read':
                    ok, msg = self._part_mgr.read_partition(name, file_path)
                elif op == 'write':
                    ok, msg = self._part_mgr.write_partition(name, file_path)
                elif op == 'erase':
                    ok, msg = self._part_mgr.erase_partition(name)
                else:
                    ok, msg = False, 'Operacao desconhecida'
            else:
                ok, msg = False, 'Nenhum backend conectado'
            self._sig_op_done.emit(ok, msg, op, name)
        threading.Thread(target=do_op, daemon=True).start()
    def _run_batch(self, queue: list):
        '''Executa uma FILA de operacoes sequencialmente numa unica thread.
Args:
    queue: lista de tuplas (op, name, file_path). Ex:
        [("read", "boot_a", "C:/tmp/boot_a.bin"),
         ("erase", "userdata", "")]
Justificativa da execucao sequencial:
- `spd_dump.exe` aceita UM comando de r/w/erase por vez (o binario
  bloqueia stdin ate o comando anterior emitir DONE ou FAIL).
- Paralelizar quebraria o pipe e corromperia state.
- Feedback visual: uma barra + rotulo mostrando "X de N".
Em caso de falha numa particao, a fila CONTINUA para as proximas
(fail-soft ÔÇö igual EDL/Qualcomm). No fim, um resumo mostra
quais foram OK e quais falharam.
'''
        if not queue:
            return
        self._batch_queue = list(queue)
        self._batch_total = len(queue)
        self._batch_results = []
        self._set_op_btns(False)
        self.btn_cancel.setEnabled(True)
        self.progress.setValue(0)
        proc = getattr(self, '_spd_proc', None)
        use_spd = proc and proc.is_running and not self._part_mgr
        def worker():
            for idx, (op, name, file_path) in enumerate(self._batch_queue, 1):
                display = self._get_display_label(name)
                op_lbl = {'read': 'Lendo', 'write': 'Gravando', 'erase': 'Apagando'}.get(op, op.capitalize())
                self._batch_status_update(f'[{idx}/{self._batch_total}] {op_lbl} {display}...')
                if use_spd:
                    ok, msg = self._run_op_spd(op, name, file_path)
                elif self._part_mgr:
                    if op == 'read':
                        ok, msg = self._part_mgr.read_partition(name, file_path)
                    elif op == 'write':
                        ok, msg = self._part_mgr.write_partition(name, file_path)
                    elif op == 'erase':
                        ok, msg = self._part_mgr.erase_partition(name)
                    else:
                        ok, msg = False, 'Operacao desconhecida'
                else:
                    ok, msg = False, 'Nenhum backend conectado'
                self._batch_results.append((op, name, ok, msg))
                if self.btn_cancel.isEnabled():
                    continue
                break
            ok_count = sum((1 for _, _, k, _ in self._batch_results if k))
            total = len(self._batch_queue)
            success = ok_count == total
            if success:
                summary = f'Todas as {total} operacoes concluidas'
            else:
                falhas = [n for _, n, k, _ in self._batch_results if not k]
                summary = f'{ok_count}/{total} OK. Falhas: ' + ', '.join(falhas[:5]) + ('...' if len(falhas) > 5 else '')
            if any((op == 'read' for op, _, _, _ in self._batch_results)):
                try:
                    import json as _json
                    import hashlib as _hashlib
                    from datetime import datetime as _dt
                except Exception:
                    logger.warning('Falha ao gerar union_backup_map.json', exc_info=True)
                try:
                    reads_ok = [(bq[1], bq[2]) for bq, br in zip(self._batch_queue, self._batch_results) if bq[0] == 'read' if br[2]]
                    if reads_ok:
                        parts_info = []
                        for bname, bfp in reads_ok:
                            if not bfp:
                                continue
                            if os.path.isfile(bfp):
                                try:
                                    fsize = os.path.getsize(bfp)
                                    with open(bfp, 'rb') as fh:
                                        md5 = _hashlib.md5(fh.read()).hexdigest()
                                except Exception:
                                    fsize = 0
                                    md5 = ''
                                parts_info.append({'name': bname, 'filename': os.path.basename(bfp), 'size_bytes': fsize, 'md5': md5})
                        if parts_info:
                            map_dir = os.path.dirname(reads_ok[0][1])
                            map_path = os.path.join(map_dir, 'union_backup_map.json')
                            existing = []
                            try:
                                if os.path.isfile(map_path):
                                    with open(map_path, 'r', encoding='utf-8') as fin:
                                        old = _json.load(fin)
                                    existing = old.get('partitions', [])
                            except Exception:
                                existing = []
                            merged = {p['name']: p for p in existing}
                            for p in parts_info:
                                merged[p['name']] = p
                            map_data = {'tool': 'TECH UNION SOLUTIONS', 'version': '1.3', 'timestamp': _dt.now().isoformat(), 'partitions': list(merged.values())}
                            tmp_path = map_path + '.tmp'
                            with open(tmp_path, 'w', encoding='utf-8') as fout:
                                _json.dump(map_data, fout, indent=2, ensure_ascii=False)
                            os.replace(tmp_path, map_path)
                except Exception:
                    logger.warning('Falha ao gerar union_backup_map.json', exc_info=True)
            self._sig_op_done.emit(success, summary, 'batch', '')
            self._batch_current_label = ''
        threading.Thread(target=worker, daemon=True).start()
    def _batch_status_update(self, msg: str):
        '''Atualiza lbl_status de forma segura via QTimer (main thread).'''
        self._batch_current_label = msg
        try:
            QTimer.singleShot(0, (lambda: self.lbl_status.setText(msg)))
            QTimer.singleShot(0, (lambda: self.lbl_status.setStyleSheet('color: #f39c12; font-weight: bold;')))
            return
        except Exception:
            return
    def _run_op_spd(self, op: str, name: str, file_path: str=''):
        '''Executa opera├º├úo via SPDDumpProcess (Auth-1).'''
        proc = self._spd_proc
        if not proc or not proc.is_running:
            return (False, 'Conexao nao esta ativa')
        try:
            if op == 'read':
                sz = self._get_part_size(name)
                if sz <= 0:
                    sz = 2097152
                    logger.warning("Tamanho de '%s' desconhecido, usando fallback %d", name, sz)
                ok = proc.read_partition(name, file_path, size_bytes=sz)
                if ok and file_path:
                    actual = os.path.getsize(file_path) if os.path.isfile(file_path) else 0
                    if actual == 0:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                        return (False, 'Backup vazio ÔÇö dispositivo pode ter desconectado. Reconecte e tente novamente.')
                    if sz > 0 and actual < sz:
                        diff = sz - actual
                        if diff == 512 and ok:
                            logger.info("Backup NV ajustado: %d/%d bytes para '%s' (header 512b omitido pelo binario)", actual, sz, name)
            try:
                logger.warning("Backup parcial: %d/%d bytes para '%s'", actual, sz, name)
            except OSError:
                pass
            else:
                return
        except Exception as e:
            logger.error(f"Erro op '{op}' em '{name}': {e}")
            return (False, 'Erro na operacao')
        return (False, 'Operacao desconhecida')
    def _on_op_done(self, ok: bool, msg: str, op: str, name: str):
        self._set_op_btns(True)
        self.btn_cancel.setEnabled(False)
        self._set_busy(False)
        self.progress.setValue(100 if ok else 0)
        if op == 'batch':
            self.lbl_status.setText(msg)
            self.lbl_status.setStyleSheet('color: #27ae60; font-weight: bold;' if ok else 'color: #e74c3c; font-weight: bold;')
            results = getattr(self, '_batch_results', None)
            if results:
                if not ok:
                    falhas = [(n, m) for _, n, k, m in results if not k]
                    detalhe = '\n'.join((f'  - {n}: {m[:60]}' for n, m in falhas[:20]))
                    QMessageBox.warning(self, 'Operacao em Lote', f'{msg}\n\nFalhas detalhadas:\n{detalhe}')
                elif ok:
                    try:
                        QMessageBox.information(self, 'Operacao em Lote', f'Operacao concluida com sucesso!\n\n{msg}')
                    except Exception:
                        pass
            try:
                from app.views.union_unlock.spd.partition_file_select import clear_all_files
                clear_all_files(self.table)
            except Exception:
                pass
            return
        display = self._get_display_label(name)
        op_labels = {'read': 'Leitura', 'write': 'Gravacao', 'erase': 'Limpeza'}
        op_lbl = op_labels.get(op, op.capitalize())
        if ok:
            self.lbl_status.setText(f'{op_lbl} de {display} ÔÇö OK')
            self.lbl_status.setStyleSheet('color: #27ae60; font-weight: bold;')
            try:
                QMessageBox.information(self, 'Sucesso', f'{op_lbl} concluida com sucesso!\n\nParticao: {display}')
            except Exception:
                pass
            return
        self.lbl_status.setText(f'Falha: {msg[:80]}')
        self.lbl_status.setStyleSheet('color: #e74c3c;')
    def _set_busy(self, busy: bool, msg: str=''):
        self._is_busy = busy
        if busy:
            if msg:
                self.lbl_status.setText(msg)
                self.lbl_status.setStyleSheet('color: #f39c12;')
    def _set_op_btns(self, enabled: bool):
        self.btn_backup.setEnabled(enabled)
        self.btn_write.setEnabled(enabled)
        self.btn_erase.setEnabled(enabled)
        try:
            self.btn_load.setEnabled(enabled)
            return
        except Exception:
            return
    def _set_extra_actions_enabled(self, enabled: bool):
        '''Habilita/desabilita as acoes extras de saida do Modo SPD.
        Agrupa os 3 botoes adicionais (Recovery/Fastboot/Desligar) para
        acompanhar o mesmo ciclo de vida do `btn_reset` ÔÇö sempre juntos
        com ele. Fallback defensivo: se algum atributo nao existir
        (ex.: build parcial), ignora sem quebrar a UI.
        '''
        for name in ('btn_reboot_recovery', 'btn_reboot_fastboot', 'btn_poweroff'):
            btn = getattr(self, name, None)
            if btn is not None:
                try:
                    btn.setEnabled(enabled)
                except Exception:
                    continue
    def _emit_log(self, msg: str, level: str):
        """Filtro de log ÔÇö WHITELIST estrita para nao vazar dados tecnicos.
        Regra: nunca propaga output cru do componente externo. Apenas
        eventos de UX conhecidos sao traduzidos para mensagens amigaveis.
        Mensagens do proprio wrapper (level='ERROR'/'OK') so passam se
        nao contem paths, enderecos ou tokens sensiveis.
        """
        if not self._log_signal:
            return
        lo = msg.lower()
        if 'check_baud' in lo and 'bootrom' in lo:
            self._log_signal.emit('[PART] Connecting with device... Ok', 'success')
            return
        if 'exec fdl2' in lo or 'enable_write_raw_data' in lo:
            self._log_signal.emit('[PART] Initializing device... Ok', 'success')
            return
        if 'erase part done' in lo:
            self._log_signal.emit('[PART] Erase Ok', 'success')
            return
        if 'write part done' in lo:
            self._log_signal.emit('[PART] Write Ok', 'success')
            return
        if any((t in msg for t in ('\\', '/', '0x', 'CMD:', 'CWD:', 'send:', 'recv:', 'type =', 'size =', 'FDL', 'fdl', 'baud', 'BAUD', 'partition_1', 'pgpt', '.bin', '.img', '.xml', 'user_partition', 'slot '))):
            return
        if level not in ('OK', 'ERROR', 'INFO'):
            return
        tipo = 'success' if level == 'OK' else 'error' if level == 'ERROR' else 'info'
        try:
            self._log_signal.emit(f'[PART] {msg}', tipo)
            return
        except Exception:
            return
    def cleanup(self):
        '''Libera todos os recursos ativos.
Chamada pelo parent (spd_main) e tambem por closeEvent/hideEvent
para garantir que NADA fique orfao. Ordem defensiva:
  1. Kill do spd_dump.exe (senao vira zumbi consumindo COM/USB).
  2. Disconnect do partition_mgr nativo (Auth-2).
  3. Limpeza de FDLs temporarios extraidos.
Cada passo em try/except isolado para nao interromper os outros.
'''
        try:
            proc = getattr(self, '_spd_proc', None)
            if proc is not None:
                pass
            try:
                proc.stop(timeout=3)
            except Exception as e:
                logger.debug(f'[partition_tab.cleanup] stop proc: {e}')
            else:
                self._spd_proc = None
        except Exception as e:
            logger.debug(f'[partition_tab.cleanup] proc cleanup: {e}')
        wd = getattr(self, '_watchdog', None)
        if wd:
            try:
                wd.stop()
            except Exception:
                pass
        if self._part_mgr:
            try:
                self._part_mgr.disconnect()
            except Exception:
                pass
            self._part_mgr = None
        temp_paths = getattr(self, '_sync_temp_paths', None)
        if temp_paths:
            try:
                try:
                    from app.views.union_unlock.spd.spd_sync import SpdSync
                except ImportError:
                    from app.views.union_unlock.spd.spd_sync import SpdSync
            except Exception:
                pass
            SpdSync.limpar_fdls_temp(temp_paths)
            self._sync_temp_paths = None
    def closeEvent(self, event):
        '''Garante cleanup ao fechar widget/janela.
        Sem isso, spd_dump.exe fica zumbi ocupando a porta COM ate
        matar processo manualmente no Gerenciador de Tarefas.
        '''
        try:
            self.cleanup()
        except Exception:
            pass
        super().closeEvent(event)
    def hideEvent(self, event):
        '''Cleanup ao esconder aba (troca para outra aba/modulo).
        Politica: SE NAO estiver conectado ativamente com particoes ja
        listadas E o tecnico trocar de aba, mata o processo pendente
        (evita spd_dump.exe rodando em background aguardando conexao
        que nao vai mais acontecer, consumindo CPU e prendendo o COM).
        Se estiver operando (backup/write em andamento), NAO mata ÔÇö
        deixa a operacao terminar em background.
        '''
        try:
            proc = getattr(self, '_spd_proc', None)
            if proc is not None and not self._is_busy and not getattr(self, '_spd_parts', None):
                pass
            try:
                proc.stop(timeout=2)
            except Exception:
                pass
            else:
                self._spd_proc = None
                self._sig_pause_port_scan.emit(False)
        except Exception as e:
            logger.debug(f'[partition_tab.hideEvent] {e}')
        super().hideEvent(event)
    @staticmethod
    def _btn_style(color: str) -> str:
        return f'\n            QPushButton {{\n                background-color: {color}; color: #FFFFFF;\n                border: none; border-radius: 5px;\n                font-weight: bold; font-size: 10px;\n                padding: 4px 10px;\n            }}\n            QPushButton:hover {{ background-color: {color}dd; }}\n            QPushButton:disabled {{ background-color: #bdc3c7; }}\n        '
    @staticmethod
    def _btn_style_sm() -> str:
        return '\n            QPushButton {\n                background-color: #FFFFFF; color: #2c3e50;\n                border: 1px solid #bdc3c7; border-radius: 3px;\n                padding: 2px 8px; font-size: 9px;\n            }\n            QPushButton:hover { background-color: #E8E8E8; }\n        '
    @staticmethod
    def _combo_style() -> str:
        try:
            from app.views.union_unlock.spd.config import SVG_SETA_DOWN
            svg = SVG_SETA_DOWN.replace('\\', '/')
        except Exception:
            svg = ''
        arrow_rule = f'QComboBox::down-arrow {{ image: url("{svg}"); width: 10px; height: 10px; }}' if svg else ''
        return f'\n            QComboBox {{\n                border: 1px solid #bdc3c7; border-radius: 4px;\n                padding: 4px 24px 4px 8px; font-size: 11px;\n                background-color: white;\n                color: #2c3e50;\n            }}\n            QComboBox:focus {{ border-color: #2471a3; }}\n            QComboBox::drop-down {{\n                subcontrol-origin: padding; subcontrol-position: top right;\n                border-left: 1px solid #bdc3c7;\n                border-top-right-radius: 4px;\n                border-bottom-right-radius: 4px;\n                width: 22px; background-color: #ecf0f1;\n            }}\n            QComboBox::drop-down:hover {{ background-color: #d5dbdb; }}\n            {arrow_rule}\n            QComboBox QAbstractItemView {{\n                background-color: white;\n                border: 1px solid #bdc3c7;\n                outline: none;\n                padding: 2px;\n                color: #2c3e50;\n            }}\n            QComboBox QAbstractItemView::item {{\n                min-height: 22px;\n                padding: 4px 8px;\n                color: #2c3e50;\n                background-color: white;\n            }}\n            QComboBox QAbstractItemView::item:hover {{\n                background-color: #d6e4f0;\n                color: #2c3e50;\n            }}\n            QComboBox QAbstractItemView::item:selected {{\n                background-color: #d6e4f0;\n                color: #2c3e50;\n            }}\n        '
# WARNING: Decompyle incomplete
